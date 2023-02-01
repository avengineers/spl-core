param(
    [switch]$clean
)

New-Item -ItemType Directory '.bootstrap' -Force
(New-Object System.Net.WebClient).DownloadFile("https://raw.githubusercontent.com/avengineers/bootstrap/develop/bootstrap.ps1", ".\.bootstrap\bootstrap.ps1")
. .\.bootstrap\bootstrap.ps1

# Unit Tests Powershell
Push-Location powershell\test\
Invoke-Pester spl-functions.Tests.ps1
$unittest = $lastexitcode
Pop-Location

if ($unittest -ne 0) {
    throw ("Unit Test: " + $errorMessage)
}

# Linter Powershell
Push-Location powershell\
powershell -Command "Invoke-ScriptAnalyzer -EnableExit -Recurse -Path ."
$linter = $lastexitcode
Pop-Location

if ($linter -ne 0) {
    throw ("Powershell Linter: " + $errorMessage)
}

# Unit Tests CMake
Push-Location cmake\test\common.cmake\
if (Test-Path .cmaketest) {
    Remove-Item .cmaketest -Recurse -Force
}
cmake -B .cmaketest -G Ninja
if ($lastexitcode -ne 0) {
    throw ("common.cmake Tests: " + $errorMessage)
}
Pop-Location

Push-Location cmake\test\spl.cmake\
if (Test-Path .cmaketest) {
    Remove-Item .cmaketest -Recurse -Force
}
cmake -B .cmaketest -G Ninja
if ($lastexitcode -ne 0) {
    throw ("spl.cmake Tests: " + $errorMessage)
}
Pop-Location

# Unit Tests
pipenv run pytest 
