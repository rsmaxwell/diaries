@echo off
setlocal

set "SCRIPT_DIR=%~dp0"

pushd "%SCRIPT_DIR%..\..\.." || exit /b 1
set "PROJECT_DIR=%CD%"
set "EXIT_CODE=0"

echo Local Docker-build stack status
echo Project directory: %PROJECT_DIR%
echo.

docker compose ps --all
set "EXIT_CODE=%ERRORLEVEL%"

popd
endlocal & exit /b %EXIT_CODE%
