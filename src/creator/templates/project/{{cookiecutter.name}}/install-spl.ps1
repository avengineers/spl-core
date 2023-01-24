Push-Location "$PSScriptRoot"
Invoke-Expression "& { $(Invoke-RestMethod https://git.marquardt.de/projects/SWSDRM/repos/spl/raw/install.ps1) } v1.6.0 https://git.marquardt.de/scm/swsdrm/spl.git -skipInstall"
Pop-Location
