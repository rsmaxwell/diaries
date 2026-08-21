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

call "%PROJECT_DIR%\scripts\windows\common\load-dotenv.bat" "%ENV_FILE%"
if errorlevel 1 (
    set "EXIT_CODE=1"
    goto :cleanup
)

call "%PROJECT_DIR%\scripts\windows\common\load-dotenv.bat" "%LOCAL_ENV_FILE%"
if errorlevel 1 (
    set "EXIT_CODE=%ERRORLEVEL%"
    goto :cleanup
)

if "%LEDGER_DB_NAME%"=="" set "LEDGER_DB_NAME=ledger"
if "%LEDGER_DB_USERNAME%"=="" set "LEDGER_DB_USERNAME=ledger"
if "%LEDGER_DB_SERVICE%"=="" set "LEDGER_DB_SERVICE=ledger-db"

if "%LEDGER_SERVER_URL%"=="" (
    if not "%LEDGER_SERVER_PORT%"=="" (
        set "LEDGER_SERVER_URL=http://localhost:%LEDGER_SERVER_PORT%"
    ) else (
        set "LEDGER_SERVER_URL=http://localhost:8080"
    )
)



rem Run the ledger-server API test suite against the full Docker environment.
rem Expected environment:
rem   - top-level compose stack is running
rem   - ledger-server container is published on localhost:%LEDGER_SERVER_PORT%
rem   - the top-level reset-db.bat script resets the same DB used by this server

echo LEDGER_SERVER_URL = %LEDGER_SERVER_URL%

@echo on
call "ledger-server\scripts\windows\test\test.bat"
@echo off

set "EXIT_CODE=%ERRORLEVEL%"

popd
endlocal & exit /b %EXIT_CODE%
