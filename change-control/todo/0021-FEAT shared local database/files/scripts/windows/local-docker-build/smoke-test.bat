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

if "%LEDGER_CLIENT_PORT%"=="" set LEDGER_CLIENT_PORT=4200
if "%LEDGER_SERVER_PORT%"=="" set LEDGER_SERVER_PORT=8080




echo Checking Docker containers...
docker compose -f "%COMPOSE_FILE%" --env-file "%ENV_FILE%" --env-file "%LOCAL_ENV_FILE%" ps
if errorlevel 1 (
    set "EXIT_CODE=1"
    goto :cleanup
)

echo.
echo Checking client container through host port !LEDGER_CLIENT_PORT!...
curl -i "http://localhost:!LEDGER_CLIENT_PORT!/client-health"
if errorlevel 1 (
    set "EXIT_CODE=1"
    goto :cleanup
)

echo.
echo Checking server actuator health through host port !LEDGER_SERVER_PORT!...
curl -i "http://localhost:!LEDGER_SERVER_PORT!/actuator/health"
if errorlevel 1 (
    set "EXIT_CODE=1"
    goto :cleanup
)

echo.
echo Checking API proxy through client container...
for /f "usebackq delims=" %%T in (`powershell -NoProfile -Command "$u=$env:LEDGER_BOOTSTRAP_ADMIN_USERNAME; if (-not $u) { $u='admin' }; $p=$env:LEDGER_BOOTSTRAP_ADMIN_PASSWORD; if (-not $p) { $p='ledger-admin' }; $body=@{username=$u;password=$p} | ConvertTo-Json -Compress; try { (Invoke-RestMethod -Method Post -Uri ('http://localhost:' + $env:LEDGER_SERVER_PORT + '/api/auth/login') -ContentType 'application/json' -Body $body).accessToken } catch { Write-Error $_; exit 1 }"`) do set "LEDGER_ACCESS_TOKEN=%%T"
if "!LEDGER_ACCESS_TOKEN!"=="" (
    echo Login failed or did not return an access token.
    set "EXIT_CODE=1"
    goto :cleanup
)
curl -i "http://localhost:!LEDGER_CLIENT_PORT!/api/customers" -H "Authorization: Bearer !LEDGER_ACCESS_TOKEN!"
set "EXIT_CODE=%ERRORLEVEL%"

:cleanup
popd
endlocal & exit /b %EXIT_CODE%
