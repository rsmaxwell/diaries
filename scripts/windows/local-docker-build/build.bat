@echo off
setlocal

set "SCRIPT_DIR=%~dp0"
pushd "%SCRIPT_DIR%..\..\.." || exit /b 1

set "PROJECT_DIR=%CD%"
set "EXIT_CODE=0"

set "COMPOSE_FILE="
set "COMPOSE_PROJECT_NAME="

pushd "%PROJECT_DIR%\diaries-client" || (
    set "EXIT_CODE=1"
    goto :cleanup
)

call npm run generate-build-info
if errorlevel 1 (
    popd
    set "EXIT_CODE=1"
    goto :cleanup
)

for /f "usebackq delims=" %%V in (`powershell -NoProfile -Command ^
    "(Get-Content 'public\assets\build-info.json' -Raw | ConvertFrom-Json).version"`) do (
    set "DIARIES_CLIENT_VERSION=%%V"
)

popd

if not defined DIARIES_CLIENT_VERSION (
    echo Unable to determine Diaries client version.
    set "EXIT_CODE=1"
    goto :cleanup
)

echo Building Diaries client version %DIARIES_CLIENT_VERSION%
echo.

docker compose ^
    -f "%PROJECT_DIR%\compose.yaml" ^
    build

set "EXIT_CODE=%ERRORLEVEL%"

:cleanup
popd
endlocal & exit /b %EXIT_CODE%