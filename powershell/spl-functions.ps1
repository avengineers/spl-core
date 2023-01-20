# Needed on Jenkins, somehow the env var PATH is not updated automatically
# after tool installations by scoop
Function ReloadEnvVars () {
    $Env:Path = [System.Environment]::GetEnvironmentVariable("Path", "User") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "Machine")
}

# executes a command line call
Function Invoke-CommandLine {
    [Diagnostics.CodeAnalysis.SuppressMessageAttribute('PSAvoidUsingInvokeExpression', '', Justification='Usually this statement must be avoided (https://learn.microsoft.com/en-us/powershell/scripting/learn/deep-dives/avoid-using-invoke-expression?view=powershell-7.3), here it is OK as it does not execute unknown code. Refactoring might still be good.')]
    param (
        [string]$CommandLine,
        [bool]$StopAtError = $true,
        [bool]$Silent = $false
    )
    if (-Not $Silent) {
        Write-Information -Tags "Info:" -MessageData "Executing: $CommandLine"
    }

    try {
        Invoke-Expression $CommandLine
    } catch {
        Write-Error "The command invokation failed: $CommandLine"
    }

    if ($LASTEXITCODE -ne 0) {
        if ($StopAtError) {
            Write-Error "Command line call `"$CommandLine`" failed with exit code $LASTEXITCODE"
            exit 1
        }
        else {
            if (-Not $Silent) {
                Write-Information -Tags "Info:" -MessageData "Command line call `"$CommandLine`" failed with exit code $LASTEXITCODE, continuing ..."
            }
        }
    }
}

# will configure the proxy if proxy variables were set in settings.json
Function Initialize-Proxy([String] $ProxyHost, [String] $NoProxy) {
    $Env:HTTP_PROXY = "http://" + $ProxyHost.replace('http://', '')
    $Env:HTTPS_PROXY = $Env:HTTP_PROXY
    $Env:NO_PROXY = $NoProxy
    $webProxy = New-Object System.Net.WebProxy($Env:HTTP_PROXY, $true, ($Env:NO_PROXY).split(','))
    [net.webrequest]::defaultwebproxy = $webProxy
    [net.webrequest]::defaultwebproxy.credentials = [System.Net.CredentialCache]::DefaultNetworkCredentials
    Write-Information -Tags "Info:" -MessageData "Proxy set to: " + $Env:HTTP_PROXY
    Write-Information -Tags "Info:" -MessageData "No-Proxy set to: " + $Env:NO_PROXY
}

# installs scoop packages; can be a single package or multiple packages at once
Function ScoopInstall ([string[]]$Packages) {
    if ($Packages) {
        Invoke-CommandLine -CommandLine "scoop install $Packages"
        ReloadEnvVars
    }
}

# installs optional scoop packages; the user can decide to install or skip every package individually
Function ScoopInstallOptional ([string[]]$Packages) {
    foreach ($package in $Packages) {
        $message = "Do you want to install '$package'? (y/n)"
        [ValidateSet('y','n')]$Answer = Read-Host $message
        if ($Answer -eq 'y') {
            ScoopInstall($package)
        }
    }
}

# installs a given set of PIP packages (single or multiple)
Function PythonInstall ([string[]]$Packages, [string[]]$TrustedHosts) {
    if ($Packages) {
        $hosts = ""
        Foreach ($trustedHost in $TrustedHosts) {
            $hosts += " --trusted-host $trustedHost"
        }

        $pipInstaller = "python -m pip install $hosts"
        Invoke-CommandLine -CommandLine "$pipInstaller $Packages"
        ReloadEnvVars
        Invoke-CommandLine -CommandLine "$pipInstaller --upgrade pip"
        ReloadEnvVars
    }
}

# the function will take a location/path to a directory that contains powershell.ps1 files and run all of them
Function Invoke-Setup-Script([string] $Location) {
    if (Test-Path -Path $Location) {
        Get-ChildItem $Location | ForEach-Object {
            Write-Information("Run: " + $_.FullName)
            & $_.FullName
        }
    }
}

# installs required tools that are needed to use scoop and python as installers
Function Install-Basic-Toolset() {
    if (-Not (Get-Command scoop -ErrorAction SilentlyContinue)) {
        if ((New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
            & $PSScriptRoot\install-scoop.ps1 -RunAsAdmin
        } else {
            & $PSScriptRoot\install-scoop.ps1
        }

        Invoke-CommandLine -CommandLine "scoop bucket rm main" -Silent $true -StopAtError $false
        Invoke-CommandLine -CommandLine "scoop bucket add main" -Silent $true
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

# install all tools that are mandatory for building the project
Function Install-Mandatory-Toolset([PSCustomObject]$JsonDependencies) {
    Foreach ($repo in $JsonDependencies.mandatory.scoop_repos) {
        $repo_and_name = $repo.Split("@")
        Invoke-CommandLine -CommandLine "scoop bucket add $($repo_and_name[0]) $($repo_and_name[1])" -StopAtError $false -Silent $true
        Invoke-CommandLine -CommandLine "scoop update"
    }

    ScoopInstall($JsonDependencies.mandatory.scoop)
    PythonInstall -Package $JsonDependencies.mandatory.python -TrustedHosts $JsonDependencies.mandatory.python_trusted_hosts
}

# install optional (GUI) tools that make life easier for developers
Function Install-Optional-Toolset([PSCustomObject]$JsonDependencies) {
    Invoke-CommandLine -CommandLine "scoop bucket add extras" -StopAtError $false
    Invoke-CommandLine -CommandLine "scoop update"
    ScoopInstallOptional($JsonDependencies.optional.scoop)
    PythonInstall -Package $jsonDependJsonDependenciesencies.optional.python
}

# start CMake with given targets
Function Invoke-CMake-Build([String] $Target, [String] $Variants, [String] $Filter, [String] $NinjaArgs, [bool] $Clean, [bool] $Reconfigure) {
    if ("selftests" -eq $Target) {
        $buildFolder = "build"
        # fresh and clean build
        if ($Clean) {
            if (Test-Path -Path $buildFolder) {
                Remove-Item $buildFolder -Force -Recurse
            }
        }

        # Run test cases to be found in folder test/
        # consider Filter if given
        $filterCmd = ''
        if ($Filter) {
            $filterCmd = "-k '$Filter'"
        }

        Invoke-CommandLine -CommandLine "python -m pipenv run python -m pytest test --capture=tee-sys --junitxml=test/output/test-report.xml -o junit_logging=all $filterCmd"
    }
    else {
        if ((-Not $Variants) -or ($Variants -eq 'all')) {
            $dirs = Get-Childitem -Include config.cmake -Path variants -Recurse | Resolve-Path -Relative
            $variantsList = @()
            Foreach ($dir in $dirs) {
                $variant = (get-item $dir).Directory.Parent.BaseName + "/" + (get-item $dir).Directory.BaseName
                $variantsList += $variant
            }
            $variantsSelected = @()
            if (-Not $Variants) {
                # variant selection if not specified
                Write-Information -ForegroundColor Black -BackgroundColor Yellow "no '--variant <variant>' was given, please select from list:"
                Foreach ($variant in $variantsList) {
                    Write-Information ("(" + [array]::IndexOf($variantsList, $variant) + ") " + $variant)
                }
                $variantsSelected += $variantsList[[int](Read-Host "Please enter selected variant number")]
                Write-Information -ForegroundColor Black -BackgroundColor Yellow "Selected variant is: $variantsSelected"
            }
            else {
                $variantsSelected = $variantsList
            }
        }
        else {
            $variantsSelected = $Variants.Replace('\', '/').Replace('./variant/', '').Replace('./variants/', '').Split(',')
        }

        Foreach ($variant in $variantsSelected) {
            $buildKit = "prod"
            if ($Target.Contains("unittests")) {
                $buildKit = "test"
            }
            $buildFolder = "build/$variant/$buildKit"
            # fresh and clean build
            if ($Clean) {
                if (Test-Path -Path $buildFolder) {
                    Remove-Item $buildFolder -Force -Recurse
                }
            }

            # delete CMake cache and reconfigure
            if ($Reconfigure) {
                if (Test-Path -Path "$buildFolder/CMakeCache.txt") {
                    Remove-Item "$buildFolder/CMakeCache.txt" -Force
                }
                if (Test-Path -Path "$buildFolder/CMakeFiles") {
                    Remove-Item "$buildFolder/CMakeFiles" -Force -Recurse
                }
            }

            # CMake configure and generate
            $variantDetails = $variant.Split('/')
            $platform = $variantDetails[0]
            $subsystem = $variantDetails[1]
            $additionalConfig = "-DBUILD_KIT=`"$buildKit`""
            if ($buildKit -eq "test") {
                $additionalConfig += " -DCMAKE_TOOLCHAIN_FILE=`"tools/toolchains/gcc/toolchain.cmake`""
            }
            Invoke-CommandLine -CommandLine "python -m pipenv run cmake -B '$buildFolder' -G Ninja -DFLAVOR=`"$platform`" -DSUBSYSTEM=`"$subsystem`" $additionalConfig"

            # CMake clean all dead artifacts. Required when running incremented builds to delete obsolete artifacts.
            Invoke-CommandLine -CommandLine "python -m pipenv run cmake --build '$buildFolder' --target $Target -- -t cleandead"
            # CMake build
            Invoke-CommandLine -CommandLine "python -m pipenv run cmake --build '$buildFolder' --target $Target -- $NinjaArgs"
        }
    }
}

# clones and runs the transformer to import new product variants
Function Invoke-Transformer([String] $Source, [String] $Variant, [bool] $Clean) {
    $transformerDir = "./build/import/transformer"
    New-Item -ItemType "directory" -Path $transformerDir -Force

    if (Test-Path -Path "$transformerDir/.git") {
        Remove-Item $transformerDir -Recurse -Force
    }

    git clone https://github.com/avengineers/SPLTransformer.git $transformerDir

    Invoke-CommandLine -CommandLine "$transformerDir\build.ps1 --source $Source --target $pwd --variant $Variant"
}