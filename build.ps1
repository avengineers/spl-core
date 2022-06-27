<#
.DESCRIPTION
    Wrapper for installing dependencies, running and testing the project

.Notes
On Windows, it may be required to enable this script by setting the execution
policy for the user. You can do this by issuing the following PowerShell command:

PS C:\> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

For more information on Execution Policies: 
https://go.microsoft.com/fwlink/?LinkID=135170
#>

[CmdletBinding(DefaultParameterSetName = 'Build')]
param(
    [Parameter(
        ParameterSetName = 'Build',
        Position = 0
    )]
    [switch]$build ## Select for building the software
    , [Parameter(ParameterSetName = 'Build')]
    [ValidateNotNullOrEmpty()]
    [string]$target = "" ## Target to be built
    , [Parameter(ParameterSetName = 'Build')]
    [string[]]$variants = "" ## Variants (projects) to be built ('all' for automatic build of all variants)
    , [Parameter(ParameterSetName = 'Build')]
    [string]$ninjaArgs = "" ## Additional build arguments for Ninja (e.g., "-d explain -d keepdepfile" for debugging purposes)
    , [Parameter(ParameterSetName = 'Build')]
    [switch]$clean ## Delete build directory
    , [Parameter(ParameterSetName = 'Build')]
    [switch]$reconfigure ## Delete CMake cache and reconfigure
    , [Parameter(
        Mandatory = $true,
        ParameterSetName = 'Import',
        Position = 0
    )]
    [switch]$import ## Select for importing legacy code from GNU Make repo
    , [Parameter(
        Mandatory = $true,
        ParameterSetName = 'Import'
    )]
    [ValidateNotNullOrEmpty()]
    [string]$source ## Location of GNU Make project containing a Makefile file
    , [Parameter(
        Mandatory = $true,
        ParameterSetName = 'Import'
    )]
    [ValidateNotNullOrEmpty()]
    [string]$variant ## Configuration name (<platform>/<subsystem>, e.g., spl/alpha)
    , [Parameter(ParameterSetName = 'Build')]
    [Parameter(ParameterSetName = 'Import')]
    [Parameter(ParameterSetName = 'Install')]
    [switch]$installMandatory ## install mandatory packages (e.g., CMake, Ninja, ...)
    , [Parameter(ParameterSetName = 'Build')]
    [Parameter(ParameterSetName = 'Import')]
    [Parameter(ParameterSetName = 'Install')]
    [switch]$installOptional ## install optional packages (e.g., VS Code)
)


$ErrorActionPreference = "Stop"

# Needed on Jenkins, somehow the env var PATH is not updated automatically
# after tool installations by scoop
Function ReloadEnvVars () {
    $Env:Path = [System.Environment]::GetEnvironmentVariable("Path", "User") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "Machine")
}

Function ScoopInstall ([string[]]$Packages) {
    Invoke-CommandLine -CommandLine "scoop install $Packages"
    ReloadEnvVars
}

Function Invoke-CommandLine {
    param (
        [string]$CommandLine,
        [bool]$StopAtError = $true,
        [bool]$Silent = $false
    )
    if (-Not $Silent) {
        Write-Host "Executing: $CommandLine"
    }
    Invoke-Expression $CommandLine
    if ($LASTEXITCODE -ne 0) {
        if ($StopAtError) {
            Write-Error "Command line call `"$CommandLine`" failed with exit code $LASTEXITCODE"
            exit 1
        }
        else {
            if (-Not $Silent) {
                Write-Host "Command line call `"$CommandLine`" failed with exit code $LASTEXITCODE, continuing ..."
            }
        }
    }
}

Push-Location $PSScriptRoot

# TODO: read proxy from a configuration file to make this script independent on network settings
# $ProxyHost = '<your host>'
# $Env:HTTP_PROXY = "http://$ProxyHost"
# $Env:HTTPS_PROXY = $Env:HTTP_PROXY
# $Env:NO_PROXY = "localhost, .other-domain.com"
# $WebProxy = New-Object System.Net.WebProxy($Env:HTTP_PROXY, $true, ($Env:NO_PROXY).split(','))
# [net.webrequest]::defaultwebproxy = $WebProxy
# [net.webrequest]::defaultwebproxy.credentials = [System.Net.CredentialCache]::DefaultNetworkCredentials

Write-Output "Running in ${pwd}"

if ($installMandatory -or $installOptional) {
    if (-Not (Get-Command scoop -errorAction SilentlyContinue)) {
        # Initial Scoop installation
        iwr get.scoop.sh -outfile 'install.ps1'
        if ((New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
            & .\install.ps1 -RunAsAdmin
        } else {
            & .\install.ps1
        }
        ReloadEnvVars
    }

    # Necessary for 7zip installation, failed on Jenkins for unknown reason. See those issues:
    # https://github.com/ScoopInstaller/Scoop/issues/460
    # https://github.com/ScoopInstaller/Scoop/issues/4024
    ScoopInstall('lessmsi')
    Invoke-CommandLine -CommandLine "scoop config MSIEXTRACT_USE_LESSMSI $true"
    # Default installer tools, e.g., dark is required for python
    ScoopInstall('7zip', 'innounp', 'dark')
}

if ($installMandatory) {
    Invoke-CommandLine -CommandLine "scoop update"
    ScoopInstall(Get-Content 'install-mandatory.list')
    $PipInstaller = "python -m pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org"
    Invoke-CommandLine -CommandLine "$PipInstaller xmlrunner==1.7.7 autopep8==1.6.0 gcovr==5.1 pytest==7.1.2"
    ReloadEnvVars
    Invoke-CommandLine -CommandLine "$PipInstaller --upgrade pip"
    ReloadEnvVars
}
if ($installOptional) {
    Invoke-CommandLine -CommandLine "scoop bucket add extras" -StopAtError $false
    Invoke-CommandLine -CommandLine "scoop update"
    ScoopInstall(Get-Content 'install-optional.list')
}

if ($build) {
    # Read build environment definitions from VSCode config
    $settingsJSON = Get-Content -Raw -Path .vscode/settings.json | ConvertFrom-Json

    if ($settingsJSON.'cmake.environment') {
        $settingsJSON.'cmake.environment' | Get-Member -MemberType NoteProperty | ForEach-Object {
            $key = $_.Name
            [Environment]::SetEnvironmentVariable($key, $settingsJSON.'cmake.environment'.$key)
        }
    }

    if ("selftests" -eq $target) {
        $BuildFolder = "build"
        # fresh and clean build
        if ($clean) {
            if (Test-Path -Path $BuildFolder) {
                Remove-Item $BuildFolder -Force -Recurse
            }
        }

        # Run test cases to be found in folder test/
        Invoke-CommandLine -CommandLine "python -m pytest --capture=tee-sys --junitxml=test/output/test-report.xml -o junit_logging=all"
    }
    else {
        if ((-Not $variants) -or ($variants -eq 'all')) {
            $dirs = Get-Childitem -Include config.cmake -Path variants -Recurse | Resolve-Path -Relative
            $variantsList = @()
            Foreach ($dir in $dirs) {
                $variant = (get-item $dir).Directory.Parent.BaseName + "/" + (get-item $dir).Directory.BaseName
                $variantsList += $variant
            }
            $variantsSelected = @()
            if (-Not $variants) {
                # variant selection if not specified
                Write-Host -ForegroundColor Black -BackgroundColor Yellow "no '--variant <variant>' was given, please select from list:"
                Foreach ($variant in $variantsList) {
                    Write-Host ("(" + [array]::IndexOf($variantsList, $variant) + ") " + $variant)
                }
                $variantsSelected += $variantsList[[int](Read-Host "Please enter selected variant number")]
                Write-Host -ForegroundColor Black -BackgroundColor Yellow "Selected variant is: $variantsSelected"
            }
            else {
                $variantsSelected = $variantsList
            }
        }
        else {
            $variantsSelected = $variants.Replace('\', '/').Replace('./variant/', '').Replace('./variants/', '').Split(',')
        }

        Foreach ($variant in $variantsSelected) {
            $BuildKit = "prod"
            if ($target.Contains("unittests")) {
                $BuildKit = "test"
            }
            $BuildFolder = "build/$variant/$BuildKit"
            # fresh and clean build
            if ($clean) {
                if (Test-Path -Path $BuildFolder) {
                    Remove-Item $BuildFolder -Force -Recurse
                }
            }

            # delete CMake cache and reconfigure
            if ($reconfigure) {
                if (Test-Path -Path "$BuildFolder/CMakeCache.txt") {
                    Remove-Item "$BuildFolder/CMakeCache.txt" -Force
                }
                if (Test-Path -Path "$BuildFolder/CMakeFiles") {
                    Remove-Item "$BuildFolder/CMakeFiles" -Force -Recurse
                }
            }

            # CMake configure and generate
            $variantDetails = $variant.Split('/')
            $platform = $variantDetails[0]
            $subsystem = $variantDetails[1]
            $additionalConfig = "-DBUILD_KIT=`"$BuildKit`""
            if ($BuildKit -eq "test") {
                $additionalConfig += " -DCMAKE_TOOLCHAIN_FILE=`"tools/toolchains/gcc/toolchain.cmake`""
            }
            Invoke-CommandLine -CommandLine "cmake -B '$BuildFolder' -G Ninja -DFLAVOR=`"$platform`" -DSUBSYSTEM=`"$subsystem`" $additionalConfig"

            # CMake clean all dead artifacts. Required when running incremented builds to delete obsolete artifacts.
            Invoke-CommandLine -CommandLine "cmake --build '$BuildFolder' --target $target -- -t cleandead"
            # CMake build
            Invoke-CommandLine -CommandLine "cmake --build '$BuildFolder' --target $target -- $ninjaArgs"
        }
    }
}

if ($import) {
    $importWorkDir = 'build/import'
    
    if ($clean) {
        if (Test-Path -Path $importWorkDir) {
            Remove-Item $importWorkDir -Force -Recurse
        }
    }
    
    $transformerDir = "$importWorkDir/transformer"
    New-Item -ItemType "directory" -Path $transformerDir -Force
    
    Push-Location $transformerDir
    if (Test-Path -Path '.git') {
        git reset --hard HEAD
        git clean -fdx
        git pull
    }
    else {
        git clone https://github.com/avengineers/Make2SPL.git .
    }
    Invoke-CommandLine -CommandLine ".\build.ps1 --source $source --target $PSScriptRoot --variant $variant"
    Pop-Location
}

Pop-Location
