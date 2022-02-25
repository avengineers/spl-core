@echo off

pushd %~dp0
call spl.bat --installOptional || exit /b 1
popd
pause
