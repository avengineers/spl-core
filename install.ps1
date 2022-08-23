if (-Not (Get-Command git -ErrorAction SilentlyContinue)) {
    throw "'git' executable not found, please install it."
}

Push-Location build
mkdir spl
Push-Location spl
git clone https://github.com/avengineers/SPL.git --branch develop --single-branch --depth 1 .
$SPL_INSTALL_DEPENDENCY_JSON_FILE = "dependencies.json"

. .\powershell\spl-functions.ps1
. .\powershell\spl-variables.ps1

if ($Env:HTTP_PROXY -and $Env:NO_PROXY) {
    Setup-Proxy -ProxyHost $Env:HTTP_PROXY -NoProxy $Env:NO_PROXY
}

Install-Basic-Tools
Install-Mandatory-Tools -JsonDependencies $SPL_INSTALL_DEPENDENCY_JSON_FILE
Pop-Location #spl
Pop-Location #build
