# Read build environment definitions from VSCode config
Function Read-Environment-Variables() {
    $settingsJSON = Get-Content -Raw -Path .vscode/settings.json | ConvertFrom-Json

    if ($settingsJSON.'cmake.environment') {
        $settingsJSON.'cmake.environment' | Get-Member -MemberType NoteProperty | ForEach-Object {
            $key = $_.Name
            [Environment]::SetEnvironmentVariable($key, $settingsJSON.'cmake.environment'.$key)
        }
    }
}

Function Print-Missing-Variable([String] $variable) {
    Write-Error "$variable is/are not defined in settings.json"
}

### Env Vars ###
# Env variables must be defined in settings.json and shall print an error if missing
Read-Environment-Variables

$SPL_INSTALL_DEPENDENCY_JSON_FILE = Get-Content -Raw -Path $Env:SPL_INSTALL_DEPENDENCY_JSON_FILE | ConvertFrom-Json
if (-not $SPL_INSTALL_DEPENDENCY_JSON_FILE) {
    Print-Missing-Variable('SPL_INSTALL_DEPENDENCY_JSON_FILE')
    $SPL_INSTALL_DEPENDENCY_JSON_FILE = "dependencies.json"
}

$SPL_EXTENSIONS_SETUP_SCRIPTS_PATH = $Env:SPL_EXTENSION_ROOT_DIR + $Env:SPL_EXTENSION_SETUP_SCRIPT_SUBDIR
if (-not $SPL_EXTENSIONS_SETUP_SCRIPTS_PATH) {Print-Missing-Variable('SPL_EXTENSION_PATH and SPL_EXTENSION_SETUP_SCRIPT_SUBDIR')}

# TODO: read proxy from a configuration file to make this script independent on network settings
$SPL_PROXY_HOST = $Env:SPL_PROXY_HOST
$SPL_PROXY_BYPASS_LIST = $Env:SPL_PROXY_BYPASS_LIST
