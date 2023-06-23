param(
    [switch]$clean ## clean build, wipe out all build artifacts
    , [switch]$install ## install mandatory packages
)

Function Invoke-CommandLine {
    [Diagnostics.CodeAnalysis.SuppressMessageAttribute('PSAvoidUsingInvokeExpression', '', Justification = 'Usually this statement must be avoided (https://learn.microsoft.com/en-us/powershell/scripting/learn/deep-dives/avoid-using-invoke-expression?view=powershell-7.3), here it is OK as it does not execute unknown code.')]
    param (
        [Parameter(Mandatory = $true, Position = 0)]
        [string]$CommandLine,
        [Parameter(Mandatory = $false, Position = 1)]
        [bool]$StopAtError = $true,
        [Parameter(Mandatory = $false, Position = 2)]
        [bool]$Silent = $false
    )
    if (-Not $Silent) {
        Write-Output "Executing: $CommandLine"
    }
    $global:LASTEXITCODE = 0
    Invoke-Expression $CommandLine
    if ($global:LASTEXITCODE -ne 0) {
        if ($StopAtError) {
            Write-Error "Command line call `"$CommandLine`" failed with exit code $global:LASTEXITCODE"
        }
        else {
            if (-Not $Silent) {
                Write-Output "Command line call `"$CommandLine`" failed with exit code $global:LASTEXITCODE, continuing ..."
            }
        }
    }
}

Push-Location $PSScriptRoot
Write-Output "Running in ${pwd}"

if ($install) {
    if (-Not (Test-Path -Path '.bootstrap')) {
        New-Item -ItemType Directory '.bootstrap'
    }
    $bootstrapSource = 'https://raw.githubusercontent.com/avengineers/bootstrap/develop/bootstrap.ps1'
    Invoke-RestMethod $bootstrapSource -OutFile '.\.bootstrap\bootstrap.ps1'
    . .\.bootstrap\bootstrap.ps1
    Write-Output "For installation changes to take effect, please close and re-open your current shell."
}
else {
    # Unit Tests CMake
    Push-Location cmake\test\common.cmake\
    if (Test-Path .cmaketest) {
        Remove-Item .cmaketest -Recurse -Force
    }
    cmake -B .cmaketest -G Ninja
    if ($lastexitcode -ne 0) {
        throw ("common.cmake Tests: " + $errorMessage)
    }
    Pop-Location

    Push-Location cmake\test\spl.cmake\
    if (Test-Path .cmaketest) {
        Remove-Item .cmaketest -Recurse -Force
    }
    cmake -B .cmaketest -G Ninja
    if ($lastexitcode -ne 0) {
        throw ("spl.cmake Tests: " + $errorMessage)
    }
    Pop-Location

    # Unit Tests
    pipenv run pytest 
}

Pop-Location
