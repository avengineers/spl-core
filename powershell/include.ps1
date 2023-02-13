# Always set the $InformationPreference variable to "Continue" globally, this way it gets printed on execution and continues execution afterwards.
$InformationPreference = "Continue"

# Stop on first PS error
$ErrorActionPreference = "Stop"

# Import the variables and functions script
. "$PSScriptRoot\spl-functions.ps1"
