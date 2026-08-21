@echo off
setlocal

set "EXIT_CODE=0"
set "SCRIPT_DIR=%~dp0"

rem This script is located under:
rem ledger\ledger-server\scripts\windows
rem Therefore, the Ledger project root is three directories above it.
pushd "%SCRIPT_DIR%..\..\.." >nul 2>&1
if errorlevel 1 (
    echo ERROR: Could not locate the Ledger project root. >&2
    echo Script directory: "%SCRIPT_DIR%" >&2
    set "EXIT_CODE=1"
    goto :cleanup
)
set "PROJECT_DIR=%CD%"

set "ENV_FILE=%PROJECT_DIR%\config\environments\development-infrastructure.env"
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

call "%PROJECT_DIR%\scripts\windows\common\load-dotenv.bat" "%ENV_FILE%"
if errorlevel 1 (
    set "EXIT_CODE=%ERRORLEVEL%"
    goto :cleanup
)

call "%PROJECT_DIR%\scripts\windows\common\load-dotenv.bat" "%LOCAL_ENV_FILE%"
if errorlevel 1 (
    set "EXIT_CODE=%ERRORLEVEL%"
    goto :cleanup
)




if "%LEDGER_DB_PORT%"=="" (
    echo ERROR: LEDGER_DB_PORT not set: >&2
    set "EXIT_CODE=1"
    goto :cleanup
)

if "%LEDGER_DB_NAME%"=="" (
    echo ERROR: LEDGER_DB_NAME not set: >&2
    set "EXIT_CODE=1"
    goto :cleanup
)




set "SPRING_PROFILES_ACTIVE=local"
set "LEDGER_DB_URL=jdbc:postgresql://localhost:%LEDGER_DB_PORT%/%LEDGER_DB_NAME%"





pushd "%PROJECT_DIR%\ledger-server"
@echo on
call gradlew.bat bootRun
@echo off

set "EXIT_CODE=%ERRORLEVEL%"
popd





set "EXIT_CODE=%ERRORLEVEL%"

popd
endlocal & exit /b %EXIT_CODE%
