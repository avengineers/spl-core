@echo off

pushd powershell\test\
REM ugly workaround to invoke tests twice, first time always fails.
powershell -Command "Invoke-Pester spl-functions.Tests.ps1 | Invoke-Pester spl-functions.Tests.ps1" || exit /b 1
popd

pushd cmake\test\common.cmake\
rd /s /q .cmaketest
cmake -B .cmaketest -G Ninja || exit /b 1
popd

pushd cmake\test\spl.cmake\
rd /s /q .cmaketest
cmake -B .cmaketest -G Ninja || exit /b 1
popd
