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






rem Run the reusable server API test suite against the local development server.
rem Expected environment:
rem   - ledger-server local PostgreSQL container is running
rem   - ledger-server is running via scripts\windows\run-server.bat / gradle bootRun
rem   - no full-Docker ledger-server is also bound to localhost:8080

set "LEDGER_SERVER_URL=http://localhost:8080"
echo LEDGER_SERVER_URL = %LEDGER_SERVER_URL%

@echo on
call "%PROJECT_DIR%\ledger-server\scripts\windows\test\test.bat"
@echo off

set "EXIT_CODE=%ERRORLEVEL%"

popd
endlocal & exit /b %EXIT_CODE%
