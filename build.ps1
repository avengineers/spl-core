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

# Update/Reload current environment variable PATH with settings from registry
Function Initialize-EnvPath {
    # workaround for system-wide installations
    if ($Env:USER_PATH_FIRST) {
        $Env:Path = [System.Environment]::GetEnvironmentVariable("Path", "User") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "Machine")
    }
    else {
        $Env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
    }
}

function Test-RunningInCIorTestEnvironment {
    return [Boolean]($Env:JENKINS_URL -or $Env:PYTEST_CURRENT_TEST -or $Env:GITHUB_ACTIONS)
}

function Invoke-Bootstrap {
     # Download and unpack the bootstrap archive_url configured in bootstrap.json
    $bootstrapJson = Join-Path $PSScriptRoot 'bootstrap.json'
    if (Test-Path $bootstrapJson) {
        $bootstrapDir = Join-Path $PSScriptRoot '.bootstrap'
        if (-Not (Test-Path -Path $bootstrapDir)) {
            New-Item -ItemType Directory $bootstrapDir
        }
        $bootstrapConfig = Get-Content $bootstrapJson | ConvertFrom-Json
        $archiveFile = Join-Path $bootstrapDir 'bootstrap.zip'
        Invoke-WebRequest -Uri $bootstrapConfig.archive_url -OutFile $archiveFile
        Expand-Archive -Path $archiveFile -DestinationPath $bootstrapDir -Force
        . $bootstrapDir\bootstrap.ps1
    }
}

## start of script
# Always set the $InformationPreference variable to "Continue" globally, this way it gets printed on execution and continues execution afterwards.
$InformationPreference = "Continue"

# Stop on first error
$ErrorActionPreference = "Stop"

Push-Location $PSScriptRoot
Write-Output "Running in ${pwd}"

try {
    if ($install) {
        Invoke-Bootstrap
    }
    else {
        if (Test-RunningInCIorTestEnvironment -or $Env:USER_PATH_FIRST) {
            Initialize-EnvPath
        }
        # Execute all tests
        .\.venv\Scripts\poetry run pytest

        # Build documentation
        .\.venv\Scripts\poetry run sphinx-build docs out/docs/html
    }
}
finally {
    Pop-Location
    if (-Not (Test-RunningInCIorTestEnvironment)) {
        Read-Host -Prompt "Press Enter to continue ..."
    }
}
## end of script
