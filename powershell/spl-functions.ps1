# resets environment variables
Function Edit-Env {
    # workaround for GithubActions
    if ($Env:INVERT_PATH_VARIABLE -eq "true") {
        $Env:Path = [System.Environment]::GetEnvironmentVariable("Path", "User") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "Machine")
    }
    else {
        $Env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
    }
}

# executes a command line call and fails on first external error
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

# the function will take a location/path to a directory that contains powershell.ps1 files and run all of them
Function Invoke-Setup-Script([string] $Location) {
    if (Test-Path -Path $Location) {
        Get-ChildItem $Location | ForEach-Object {
            Write-Information -Tags "Info:" -MessageData ("Run: " + $_.FullName)
            . $_.FullName
        }
        Edit-Env
    }
}

# install all tools that are mandatory for building the project
Function Install-Toolset([String]$FilePath) {
    if (Test-Path -Path $FilePath) {
        Invoke-CommandLine -CommandLine "scoop import $FilePath"
        Edit-Env
    }
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
                Write-Information -Tags "Info:" -MessageData "no '--variant <variant>' was given, please select from list:"
                Foreach ($variant in $variantsList) {
                    Write-Information -Tags "Info:" -MessageData ("(" + [array]::IndexOf($variantsList, $variant) + ") " + $variant)
                }
                $variantsSelected += $variantsList[[int](Read-Host "Please enter selected variant number")]
                Write-Information -Tags "Info:" -MessageData "Selected variant is: $variantsSelected"
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