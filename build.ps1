<#
.SYNOPSIS
    Build wrapper for this project
.DESCRIPTION
    Build wrapper for CMake and Ninja
#>

[CmdletBinding(DefaultParameterSetName = 'Build')]
param(
    [string]$target = "" ## Target to be built
    , [string[]]$variants = "" ## Variants (projects) to be built ('all' for automatic build of all variants)
    , [string]$ninjaArgs = "" ## Additional build arguments for Ninja (e.g., "-d explain -d keepdepfile" for debugging purposes)
    , [switch]$clean ## Delete build directory
    , [switch]$reconfigure ## Delete CMake cache and reconfigure
    , [switch]$installMandatory ## install mandatory packages (e.g., CMake, Ninja, ...)
    , [switch]$installOptional ## install optional packages (e.g., VS Code)
)


$ErrorActionPreference = "Stop"

# Needed on Jenkins, somehow the env var PATH is not updated automatically
# after tool installations by scoop
Function ReloadEnvVars () {
    $Env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
}

Function ScoopInstall ([string[]]$Packages) {
    Invoke-CommandLine -CommandLine "scoop install $Packages"
    ReloadEnvVars
}

Function Invoke-CommandLine {
    param (
        [string]$CommandLine,
        [bool]$StopAtError = $true
    )
    Write-Host "Executing: $CommandLine"
    Invoke-Expression $CommandLine
    if ($LASTEXITCODE -ne 0) {
        if ($StopAtError) {
            Write-Error "Command line call `"$CommandLine`" failed with exit code $LASTEXITCODE"
            exit 1
        }
        else {
            Write-Host "Command line call `"$CommandLine`" failed with exit code $LASTEXITCODE, continuing ..."
        }
    }
}

Push-Location $PSScriptRoot

# Use default proxy
# $ProxyHost = '<your host>'
# $Env:HTTP_PROXY = "http://$ProxyHost"
# $Env:HTTPS_PROXY = $Env:HTTP_PROXY
# $Env:NO_PROXY = "localhost"
# $WebProxy = New-Object System.Net.WebProxy($Env:HTTP_PROXY, $true, ($Env:NO_PROXY).split(','))
# [net.webrequest]::defaultwebproxy = $WebProxy
# [net.webrequest]::defaultwebproxy.credentials = [System.Net.CredentialCache]::DefaultNetworkCredentials

if ($installMandatory -or $installOptional) {
    # Initial Scoop installation
    $ScoopInstaller = (New-Object System.Net.WebClient).DownloadString('https://get.scoop.sh')
    ReloadEnvVars
    if (-Not (Get-Command scoop -errorAction SilentlyContinue)) {
        Invoke-Expression $ScoopInstaller
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
    ScoopInstall(Get-Content 'install-mandatory.list')
    Invoke-CommandLine -CommandLine "python -m pip install --quiet --trusted-host pypi.org --trusted-host files.pythonhosted.org python-certifi-win32"
    Invoke-CommandLine -CommandLine "python -m pip install --quiet xmlrunner==1.7.7 autopep8==1.6.0 gcovr==5.0.0"
}
if ($installOptional) {
    Invoke-CommandLine -CommandLine "scoop bucket add extras"
    ScoopInstall(Get-Content 'install-optional.list')
}

if ($target) {
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
        Invoke-CommandLine -CommandLine "python -u test/run_all.py"
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
            $BuildFolder = "build/$variant"
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
            $additionalConfig = "-DBUILD_KIT=`"production`""
            if ($target.Contains("unittests")) {
                $additionalConfig = "-DBUILD_KIT=`"test`" -DCMAKE_TOOLCHAIN_FILE=`"tools/toolchains/gcc/toolchain.cmake`""
            }
            Invoke-CommandLine -CommandLine "cmake -B '$BuildFolder' -G Ninja -DFLAVOR=`"$platform`" -DSUBSYSTEM=`"$subsystem`" $additionalConfig"
        
            # CMake build
            Invoke-CommandLine -CommandLine "cmake --build '$BuildFolder' --target $target -- $ninjaArgs"
        }
    }    
}

Pop-Location
