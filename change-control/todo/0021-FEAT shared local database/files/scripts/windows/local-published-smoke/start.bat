@echo off
setlocal

set "SCRIPT_DIR=%~dp0"

pushd "%SCRIPT_DIR%..\..\.." || exit /b 1
set "PROJECT_DIR=%CD%"
set "EXIT_CODE=0"


set "COMPOSE_FILE=%PROJECT_DIR%\compose.local-published-smoke.yaml"
if not exist "%COMPOSE_FILE%" (
    echo Compose file not found: "%COMPOSE_FILE%"
    set "EXIT_CODE=1"
    goto :cleanup
)

set "ENV_FILE=%PROJECT_DIR%\config\environments\local-published-smoke.env"
if not exist "%ENV_FILE%" (
    echo Environment file not found: "%ENV_FILE%"
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

if exist "%SCRIPT_DIR%set-env.bat" (
    call "%SCRIPT_DIR%set-env.bat"
    if errorlevel 1 (
        set "EXIT_CODE=1"
        goto :cleanup
    )
)

rem -----------------------------------------------------------------
rem Resolve the effective image tags.
rem
rem Precedence for the client:
rem   LEDGER_CLIENT_IMAGE_TAG
rem   LEDGER_IMAGE_TAG
rem   integration
rem
rem Precedence for the server:
rem   LEDGER_SERVER_IMAGE_TAG
rem   LEDGER_IMAGE_TAG
rem   integration
rem -----------------------------------------------------------------

if defined LEDGER_CLIENT_IMAGE_TAG (
    set "EFFECTIVE_CLIENT_IMAGE_TAG=%LEDGER_CLIENT_IMAGE_TAG%"
) else if defined LEDGER_IMAGE_TAG (
    set "EFFECTIVE_CLIENT_IMAGE_TAG=%LEDGER_IMAGE_TAG%"
) else (
    set "EFFECTIVE_CLIENT_IMAGE_TAG=integration"
)

if defined LEDGER_SERVER_IMAGE_TAG (
    set "EFFECTIVE_SERVER_IMAGE_TAG=%LEDGER_SERVER_IMAGE_TAG%"
) else if defined LEDGER_IMAGE_TAG (
    set "EFFECTIVE_SERVER_IMAGE_TAG=%LEDGER_IMAGE_TAG%"
) else (
    set "EFFECTIVE_SERVER_IMAGE_TAG=integration"
)

echo Starting local published-image smoke-test stack
echo   Client image: rsmaxwell/ledger-client:%EFFECTIVE_CLIENT_IMAGE_TAG%
echo   Server image: rsmaxwell/ledger-server:%EFFECTIVE_SERVER_IMAGE_TAG%
echo.

docker compose ^
    --env-file "%ENV_FILE%" --env-file "%LOCAL_ENV_FILE%" ^
    -f "%COMPOSE_FILE%" ^
    config --quiet
if errorlevel 1 (
    echo ERROR: Docker Compose configuration is invalid.
    set "EXIT_CODE=%ERRORLEVEL%"
    goto :cleanup
)

echo on
docker compose ^
    --env-file "%ENV_FILE%" --env-file "%LOCAL_ENV_FILE%" ^
    -f "%COMPOSE_FILE%" ^
    pull
echo off

if errorlevel 1 (
    set "EXIT_CODE=%ERRORLEVEL%"
    goto :cleanup
)

echo on
docker compose ^
    --env-file "%ENV_FILE%" --env-file "%LOCAL_ENV_FILE%" ^
    -f "%COMPOSE_FILE%" ^
    up -d --remove-orphans --wait --wait-timeout 120
@echo off

set "EXIT_CODE=%ERRORLEVEL%"
if not "%EXIT_CODE%"=="0" (
    echo ERROR: Failed to start the local published-image smoke-test stack. >&2
)


:cleanup
popd
endlocal & exit /b %EXIT_CODE%
