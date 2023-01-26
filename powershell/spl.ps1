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
        Mandatory = $true,
        ParameterSetName = 'Build',
        Position = 0
    )]
    [switch]$build ## Select for building the software
    , [Parameter(
        Mandatory = $true,
        ParameterSetName = 'Build'
    )]
    [ValidateNotNullOrEmpty()]
    [string]$target = "" ## Target to be built
    , [Parameter(ParameterSetName = 'Build')]
    [string]$filter = "" ## filter for selftests; define in pytest syntax: https://docs.pytest.org/en/6.2.x/usage.html; e.g. "PYRO_C or test/test_unittests.py"
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
    [switch]$import ## Select for importing legacy code from Dimensions repo
    , [Parameter(
        Mandatory = $true,
        ParameterSetName = 'Import'
    )]
    [ValidateNotNullOrEmpty()]
    [string]$source ## Location of Dimensions project containing an 'Impl' directory
    , [Parameter(
        Mandatory = $true,
        ParameterSetName = 'Import'
    )]
    [ValidateNotNullOrEmpty()]
    [string]$variant ## Configuration name (<platform>/<subsystem>, e.g., VW_PPE_Porsche_983/BMS_HV_PYRO)
    , [Parameter(
        Mandatory = $true,
        ParameterSetName = 'Install',
        Position = 0
    )]
    [switch]$install ## Select for installing the software
    , [Parameter(ParameterSetName = 'Build')]
    [Parameter(ParameterSetName = 'Install')]
    [switch]$installMandatory ## install mandatory packages (e.g., CMake, Ninja, ...)
    , [Parameter(ParameterSetName = 'Build')]
    [Parameter(ParameterSetName = 'Install')]
    [switch]$installOptional ## install optional packages (e.g., VS Code)
)

Write-Information -Tags "Info:" -MessageData "Running in ${pwd}"

# load spl scripts
. "$PSScriptRoot\include.ps1"

if ($install -or $build) {
    if ($installMandatory -or $installOptional) {
        $envProps = ConvertFrom-StringData (Get-Content '.env' -raw)
        $bootstrap = $envProps.'BOOTSTRAP'
        $extension_path = $envProps.'SPL_EXTENSIONS_SETUP_SCRIPTS_PATH'
        $install_spl_deps = $envProps.'SPL_INSTALL_DEPENDENCIES'

        (New-Object System.Net.WebClient).DownloadFile($bootstrap, ".\bootstrap.ps1")
        . .\bootstrap.ps1

        if ($installMandatory) {
            if ($install_spl_deps -eq 'true') {
                Write-Information -Tags "Info:" -MessageData "Install SPL core mandatory dependencies."
                Install-Toolset -FilePath "$PSScriptRoot\..\scoopfile.json"
            }

            if ($extension_path) {
                Invoke-Setup-Script -Location "$extension_path\mandatory"
            }
        }

        if ($installOptional) {
            if ($install_spl_deps -eq 'true') {
                Write-Information -Tags "Info:" -MessageData "Install SPL core optional dependencies."
                Install-Toolset -FilePath "$PSScriptRoot\..\scoopfile-optional.json"
                
            }

            if ($extension_path) {
                Invoke-Setup-Script -Location "$extension_path\optional"
            }
        }
    }
}

if ($build) {
    Invoke-CMake-Build -Target $target -Variants $variants -Filter $filter -NinjaArgs $ninjaArgs -Clean $clean -Reconfigure $reconfigure
}

if ($import) {
    Invoke-Transformer -Source $source -Variant $variant -Clean $clean
}
