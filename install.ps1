param(
    [Parameter(
        Mandatory = $false
    )]
    [string]$version = "develop" ## use latest if no verison was given
    , [Parameter(
        Mandatory = $false
    )]
    [string]$repo_url = "https://github.com/avengineers/SPL.git"
    , [Parameter(
        Mandatory = $false
    )]
    [switch]$skipInstall
)

Write-Host "Clone/Update SPL version: $version from $repo_url"

if (-Not (Get-Command git -ErrorAction SilentlyContinue)) {
    throw "'git' executable not found, please install it."
}

if (Test-Path build/spl-core/$version) {
    Write-Host "SPL-core version already set to $version, no update."
} else {
    if (Test-Path build/spl-core/) {
        Remove-Item "build/spl-core" -Recurse -Force
    }
    
    git clone $repo_url --branch $version --depth 1 ./build/spl-core
    
    Push-Location build/spl-core
    Out-File -FilePath $version
    Pop-Location #build/spl-core
    
    if ($skipInstall) {
        Write-Host "Skipping installation of dependencies."
    } else {
        . .\build\spl-core\powershell\spl-variables.ps1
        . .\build\spl-core\powershell\spl-functions.ps1
    
        Push-Location build/spl-core
    
        if ($SPL_PROXY_HOST -and $SPL_PROXY_BYPASS_LIST) {
            Setup-Proxy -ProxyHost $SPL_PROXY_HOST -NoProxy $SPL_PROXY_BYPASS_LIST
        }
    
        Install-Basic-Tools
        $SPL_INSTALL_DEPENDENCY_JSON_FILE_CONTENT = Get-Content -Raw -Path "dependencies.json" | ConvertFrom-Json
        Install-Mandatory-Tools -JsonDependencies $SPL_INSTALL_DEPENDENCY_JSON_FILE_CONTENT
        Pop-Location #build/spl-core
    }
    
}
