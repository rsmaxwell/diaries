@echo off
setlocal

set "EXIT_CODE=0"
set "SCRIPT_DIR=%~dp0"

rem This script is located under:
rem diaries\scripts\windows\local-docker-build
rem Therefore, the Diaries project root is three directories above it.
pushd "%SCRIPT_DIR%..\..\.." >nul 2>&1
if errorlevel 1 (
    echo ERROR: Could not locate the Diaries project root. >&2
    echo Script directory: "%SCRIPT_DIR%" >&2
    endlocal & exit /b 1
)
set "PROJECT_DIR=%CD%"

set "COMPOSE_FILE=%PROJECT_DIR%\compose.local-docker-build.yaml"
if not exist "%COMPOSE_FILE%" (
    echo Compose file not found: "%COMPOSE_FILE%"
    set "EXIT_CODE=1"
    goto :cleanup
)

set "ENV_FILE=%PROJECT_DIR%\config\environments\local-docker-build.env"
if not exist "%ENV_FILE%" (
    echo Environment file not found: "%ENV_FILE%"
    set "EXIT_CODE=1"
    goto :cleanup
)






pushd "%PROJECT_DIR%\diaries-client" >nul 2>&1
if errorlevel 1 (
    echo ERROR: Could not enter Diaries client directory. >&2
    set "EXIT_CODE=1"
    goto :cleanup
)

call npm run generate-build-info
set "EXIT_CODE=%ERRORLEVEL%"

popd

if not "%EXIT_CODE%"=="0" (
    echo ERROR: Failed to generate client build information. >&2
    goto :cleanup
)



call "%PROJECT_DIR%\scripts\windows\common\load-dotenv.bat" "%ENV_FILE%"
if errorlevel 1 (
    echo ERROR: Could not load environment file. >&2
    set "EXIT_CODE=1"
    goto :cleanup
)

if not defined DIARIES_CLIENT_VERSION (
    echo Unable to determine Diaries client version.
    set "EXIT_CODE=1"
    goto :cleanup
)



echo Building Diaries client version %DIARIES_CLIENT_VERSION%
echo.

docker compose ^
    --env-file "%ENV_FILE%" ^
    -f "%COMPOSE_FILE%" ^
    build

set "EXIT_CODE=%ERRORLEVEL%"

:cleanup
popd
endlocal & exit /b %EXIT_CODE%