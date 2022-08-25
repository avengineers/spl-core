param(
    [Parameter(
        Mandatory = $false
    )]
    [string]$version = "develop" ## use latest if no verison was given
    , [Parameter(
        Mandatory = $false
    )]
    [string]$repo_url = "https://github.com/avengineers/SPL.git"
)

echo "Clone/Update SPL version: $version from $repo_url"

if (-Not (Get-Command git -ErrorAction SilentlyContinue)) {
    throw "'git' executable not found, please install it."
}

if (Test-Path build/spl-core/.git) {
    Remove-Item 'build/spl-core' -Recurse
}

git clone $repo_url --branch $version --depth 1 ./build/spl-core

Push-Location build/spl-core

Out-File -FilePath $version
. .\powershell\spl-functions.ps1

if ($Env:HTTP_PROXY -and $Env:NO_PROXY) {
    Setup-Proxy -ProxyHost $Env:HTTP_PROXY -NoProxy $Env:NO_PROXY
}

Install-Basic-Tools
$SPL_INSTALL_DEPENDENCY_JSON_FILE_CONTENT = Get-Content -Raw -Path "dependencies.json" | ConvertFrom-Json
Install-Mandatory-Tools -JsonDependencies $SPL_INSTALL_DEPENDENCY_JSON_FILE_CONTENT
Pop-Location #build/spl-core
