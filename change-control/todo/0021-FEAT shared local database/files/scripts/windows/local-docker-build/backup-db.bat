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




rem Back up the PostgreSQL database used by the full Docker environment.
rem The backup is written to ledger\backups as a custom-format pg_dump file.

if not exist "backups" mkdir "backups"
if not exist "backups" mkdir "local-docker-build"

for /f %%I in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd-HHmmss"') do set "STAMP=%%I"

set "BACKUP_FILE=backups\local-docker-build\ledger-%STAMP%.dump"

echo Creating database backup:
echo   Service:  %LEDGER_DB_SERVICE%
echo   Database: %LEDGER_DB_NAME%
echo   User:     %LEDGER_DB_USERNAME%
echo   File:     %BACKUP_FILE%
echo.

@echo on
docker compose -f "%COMPOSE_FILE%" --env-file "%ENV_FILE%" --env-file "%LOCAL_ENV_FILE%" exec -T "%LEDGER_DB_SERVICE%" pg_dump -U "%LEDGER_DB_USERNAME%" -d "%LEDGER_DB_NAME%" -Fc > "%BACKUP_FILE%"
@echo off

set "EXIT_CODE=%ERRORLEVEL%"

if not "%EXIT_CODE%"=="0" (
    echo.
    echo Backup failed.
    if exist "%BACKUP_FILE%" del "%BACKUP_FILE%" >nul 2>nul
    goto :cleanup
)

echo.
echo Backup complete: %BACKUP_FILE%

:cleanup
popd
endlocal & exit /b %EXIT_CODE%
