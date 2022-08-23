param(
    [Parameter(
        Mandatory = $false,
        Position = 0
    )]
    [string]$version = "develop" ## use latest if no verison was given
)

if (-Not (Get-Command git -ErrorAction SilentlyContinue)) {
    throw "'git' executable not found, please install it."
}

git clone https://github.com/avengineers/SPL.git --branch $version --depth 1 ./build/spl
Push-Location build/spl

. .\powershell\spl-functions.ps1

if ($Env:HTTP_PROXY -and $Env:NO_PROXY) {
    Setup-Proxy -ProxyHost $Env:HTTP_PROXY -NoProxy $Env:NO_PROXY
}

Install-Basic-Tools
Install-Mandatory-Tools -JsonDependencies "dependencies.json"
Pop-Location #build/spl
