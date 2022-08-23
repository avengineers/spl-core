. .\install.ps1

Push-Location powershell\test\
# ugly workaround to invoke tests twice, first time always fails.
try {
    Invoke-Pester spl-functions.Tests.ps1
}
catch {
    Invoke-Pester spl-functions.Tests.ps1
}
Pop-Location

Push-Location cmake\test\common.cmake\
if (Test-Path .cmaketest) {
    Remove-Item .cmaketest -Recurse -Force
}
cmake -B .cmaketest -G Ninja
Pop-Location

Push-Location cmake\test\spl.cmake\
if (Test-Path .cmaketest) {
    Remove-Item .cmaketest -Recurse -Force
}
cmake -B .cmaketest -G Ninja
Pop-Location
