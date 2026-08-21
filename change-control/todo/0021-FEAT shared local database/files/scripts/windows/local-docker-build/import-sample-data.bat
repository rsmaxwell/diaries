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

if "%LEDGER_SERVER_URL%"=="" (
    if not "%LEDGER_SERVER_PORT%"=="" (
        set "LEDGER_SERVER_URL=http://localhost:%LEDGER_SERVER_PORT%"
    ) else (
        set "LEDGER_SERVER_URL=http://localhost:8080"
    )
)

call "%PROJECT_DIR%\ledger-server\scripts\windows\common\login.bat"

if errorlevel 1 (
        set "EXIT_CODE=1"
        goto :cleanup
)



rem Import sample/demo data by calling the ledger-server REST API.
rem This uses normal business APIs rather than direct SQL.
rem Expected:
rem   - ledger-server is running

set "TEST_SCRIPT=%PROJECT_DIR%\ledger-server\scripts\windows\common\import-sample-data.bat"
if not exist "%TEST_SCRIPT%" (
    echo ERROR: test script not found: >&2
    echo "%TEST_SCRIPT%" >&2
    set "EXIT_CODE=1"
    goto :cleanup
)

@echo on
call "%TEST_SCRIPT%"
@echo off

set "EXIT_CODE=%ERRORLEVEL%"

:cleanup
popd
endlocal & exit /b %EXIT_CODE%
