@echo off

pushd %~dp0
call spl.bat --installMandatory || exit /b 1
popd
pause
