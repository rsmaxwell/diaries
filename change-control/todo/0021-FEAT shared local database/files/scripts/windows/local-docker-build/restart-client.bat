@echo off
setlocal

set "EXIT_CODE=0"
set "SCRIPT_DIR=%~dp0"

rem This script is located under:
rem ledger\scripts\windows\local-docker-build
rem Therefore, the Ledger project root is three directories above it.
pushd "%SCRIPT_DIR%..\..\.." >nul 2>&1
if errorlevel 1 (
    echo ERROR: Could not locate the Ledger project root. >&2
    echo Script directory: "%SCRIPT_DIR%" >&2
    set "EXIT_CODE=1"
    goto :cleanup
)
set "PROJECT_DIR=%CD%"

set "COMPOSE_FILE=%PROJECT_DIR%\compose.local-docker-build.yaml"
if not exist "%COMPOSE_FILE%" (
    echo ERROR: Compose file not found: >&2
    echo "%COMPOSE_FILE%" >&2
    set "EXIT_CODE=1"
    goto :cleanup
)

set "ENV_FILE=%PROJECT_DIR%\config\environments\local-docker-build.env"
if not exist "%ENV_FILE%" (
    echo ERROR: Environment file not found: >&2
    echo "%ENV_FILE%" >&2
    set "EXIT_CODE=1"
    goto :cleanup
)

set "LOCAL_ENV_FILE=%PROJECT_DIR%\config\environments\local.env"
if not exist "%LOCAL_ENV_FILE%" (
    echo ERROR: Local environment file not found: >&2
    echo "%LOCAL_ENV_FILE%" >&2
    echo Copy config\environments\local.env.example to local.env and customise it. >&2
    set "EXIT_CODE=1"
    goto :cleanup
)





@echo on
docker compose -f "%COMPOSE_FILE%" --env-file "%ENV_FILE%" --env-file "%LOCAL_ENV_FILE%" restart ledger-client
@echo off

set "EXIT_CODE=%ERRORLEVEL%"

popd
endlocal & exit /b %EXIT_CODE%