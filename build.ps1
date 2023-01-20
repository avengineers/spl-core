$ErrorActionPreference = 'Stop'

. .\powershell\spl.ps1 -install -installMandatory

Push-Location powershell\test\
# TODO: ugly workaround to invoke tests twice, first time always fails.
try {
    Invoke-Pester spl-functions.Tests.ps1
}
catch {
    Invoke-Pester spl-functions.Tests.ps1
}

$unittest = $lastexitcode

Pop-Location

if ($unittest -ne 0) {
    throw ("Unit Test: " + $errorMessage)
}

Push-Location powershell\
powershell -Command "Invoke-ScriptAnalyzer -EnableExit -Recurse -Path ."
$linter = $lastexitcode
Pop-Location

if ($linter -ne 0) {
    throw ("Powershell Linter: " + $errorMessage)
}

# TODO: move these tests to python tests
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

pipenv run pytest 
