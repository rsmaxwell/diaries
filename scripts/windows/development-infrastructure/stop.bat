@echo off
setlocal

set "EXIT_CODE=0"
set "SCRIPT_DIR=%~dp0"

pushd "%SCRIPT_DIR%..\..\.." >nul 2>&1
if errorlevel 1 (
    echo ERROR: Could not locate the project directory. >&2
    echo Script directory: "%SCRIPT_DIR%" >&2
    endlocal & exit /b 1
)

set "PROJECT_DIR=%CD%"

set "COMPOSE_FILE=%PROJECT_DIR%\compose.development-infrastructure.yaml"
if not exist "%COMPOSE_FILE%" (
    echo ERROR: Compose file not found: "%COMPOSE_FILE%" >&2
    set "EXIT_CODE=1"
    goto :cleanup
)

set "ENV_FILE=%PROJECT_DIR%\config\environments\development-infrastructure.env"
if not exist "%ENV_FILE%" (
    echo ERROR: Environment file not found: "%ENV_FILE%" >&2
    set "EXIT_CODE=1"
    goto :cleanup
)

docker compose ^
    --env-file "%ENV_FILE%" ^
    -f "%COMPOSE_FILE%" ^
    down

set "EXIT_CODE=%ERRORLEVEL%"

:cleanup
popd
endlocal & exit /b %EXIT_CODE%
