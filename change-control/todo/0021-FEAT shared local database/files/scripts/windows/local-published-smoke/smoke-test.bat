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

if exist "%SCRIPT_DIR%set-env.bat" (
    call "%SCRIPT_DIR%set-env.bat"
    if errorlevel 1 (
        set "EXIT_CODE=1"
        goto :cleanup
    )
)



set "LEDGER_CLIENT_URL=http://localhost:%LEDGER_CLIENT_PORT%/ledger"
set "LEDGER_SERVER_URL=http://localhost:%LEDGER_SERVER_PORT%"

echo Checking local published-image smoke-test stack
echo   Client: %LEDGER_CLIENT_URL%
echo   Server: %LEDGER_SERVER_URL%
echo.

echo on
docker compose ^
    --env-file "%ENV_FILE%" --env-file "%LOCAL_ENV_FILE%" ^
    -f "%COMPOSE_FILE%" ^
    ps
echo off

if errorlevel 1 (
    set "EXIT_CODE=%ERRORLEVEL%"
    goto :cleanup
)

echo.
echo Checking client health...
set "STATUS="
curl -sS -o nul -w "%%{http_code}" "%LEDGER_CLIENT_URL%/client-health" > "%TEMP%\ledger-client-health-status.txt"

if errorlevel 1 (
    echo ERROR: Could not connect to %LEDGER_CLIENT_URL%/client-health. >&2
    del "%TEMP%\ledger-client-health-status.txt" >nul 2>nul
    set "EXIT_CODE=1"
    goto :cleanup
)

set /p STATUS=<"%TEMP%\ledger-client-health-status.txt"
del "%TEMP%\ledger-client-health-status.txt" >nul 2>nul

if not "%STATUS%"=="200" (
    echo Expected HTTP 200 from %LEDGER_CLIENT_URL%/client-health, got %STATUS%
    set "EXIT_CODE=1"
    goto :cleanup
)
echo OK 200: %LEDGER_CLIENT_URL%/client-health






echo.
echo Checking unauthenticated /api/auth/me is rejected...
set "STATUS="
curl -sS -o nul -w "%%{http_code}" "%LEDGER_CLIENT_URL%/api/auth/me" > "%TEMP%\ledger-auth-me-status.txt"
if errorlevel 1 (
    echo ERROR: Could not connect to %LEDGER_CLIENT_URL%/api/auth/me. >&2
    del "%TEMP%\ledger-auth-me-status.txt" >nul 2>nul
    set "EXIT_CODE=1"
    goto :cleanup
)

set /p STATUS=<"%TEMP%\ledger-auth-me-status.txt"
del "%TEMP%\ledger-auth-me-status.txt" >nul 2>nul

if not "%STATUS%"=="401" (
    echo Expected HTTP 401 from %LEDGER_CLIENT_URL%/api/auth/me, got %STATUS%
    set "EXIT_CODE=1"
    goto :cleanup
)
echo OK 401: %LEDGER_CLIENT_URL%/api/auth/me






echo.
echo Checking server actuator health...
set "STATUS="
curl -sS -o nul -w "%%{http_code}" "%LEDGER_SERVER_URL%/actuator/health" > "%TEMP%\ledger-server-health-status.txt"
if errorlevel 1 (
    echo ERROR: Could not connect to %LEDGER_SERVER_URL%/actuator/health. >&2
    del "%TEMP%\ledger-server-health-status.txt" >nul 2>nul
    set "EXIT_CODE=1"
    goto :cleanup
)

set /p STATUS=<"%TEMP%\ledger-server-health-status.txt"
del "%TEMP%\ledger-server-health-status.txt" >nul 2>nul

if not "%STATUS%"=="200" (
    echo Expected HTTP 200 from %LEDGER_SERVER_URL%/actuator/health, got %STATUS%
    set "EXIT_CODE=1"
    goto :cleanup
)
echo OK 200: %LEDGER_SERVER_URL%/actuator/health






echo.
echo Checking client version metadata...
set "STATUS="
curl -sS "%LEDGER_CLIENT_URL%/version.json" > "%TEMP%\ledger-version.json"
if errorlevel 1 (
    echo version.json was missing or did not contain ledger-client metadata.
    type "%TEMP%\ledger-version.json"
    del "%TEMP%\ledger-version.json" >nul 2>nul
    set "EXIT_CODE=1"
    goto :cleanup
)

findstr /C:"\"component\":\"ledger-client\"" "%TEMP%\ledger-version.json" >nul
if errorlevel 1 (
    echo ERROR: version.json did not contain ledger-client metadata. >&2
    type "%TEMP%\ledger-version.json"
    del "%TEMP%\ledger-version.json" >nul 2>nul
    set "EXIT_CODE=1"
    goto :cleanup
)

del "%TEMP%\ledger-version.json" >nul 2>nul
echo OK version.json contains ledger-client metadata

echo.
echo Local published-image smoke test passed.


:cleanup
popd
endlocal & exit /b %EXIT_CODE%
