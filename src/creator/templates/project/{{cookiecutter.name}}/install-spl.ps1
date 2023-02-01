Push-Location "$PSScriptRoot"
Invoke-Expression "& { $(Invoke-RestMethod https://raw.githubusercontent.com/avengineers/SPL/develop/install.ps1) } v1.6.0 -skipInstall"
Pop-Location
