param(
    [switch]$clean ## clean build, wipe out all build artifacts
)

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
    # Download bootstrap scripts from external repository
    Invoke-RestMethod https://raw.githubusercontent.com/avengineers/bootstrap-installer/v1.5.0/install.ps1 | Invoke-Expression
    # Execute bootstrap script
    . .\.bootstrap\bootstrap.ps1
}


## start of script
# Always set the $InformationPreference variable to "Continue" globally, this way it gets printed on execution and continues execution afterwards.
$InformationPreference = "Continue"

# Stop on first error
$ErrorActionPreference = "Stop"

Push-Location $PSScriptRoot
Write-Output "Running in ${pwd}"

try {
    # bootstrap environment
    Invoke-Bootstrap

    Initialize-EnvPath

    # Run pypeline
    .\.venv\Scripts\pypeline run
}
finally {
    Pop-Location
    if (-Not (Test-RunningInCIorTestEnvironment)) {
        Read-Host -Prompt "Press Enter to continue ..."
    }
}
## end of script
