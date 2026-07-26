@echo off

if "%~1"=="" (
    echo Usage: require-command.bat command-name
    exit /b 1
)

where "%~1" >nul 2>nul
if errorlevel 1 (
    echo Required command not found on PATH: %~1
    exit /b 1
)

exit /b 0
