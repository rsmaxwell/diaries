@echo off
setlocal

rem Restore the PostgreSQL development database from a custom-format dump.
rem
rem Usage:
rem   restore-db.bat backup-file.dump
rem
rem When only a filename is supplied, the script looks in:
rem   ledger\backups\development-infrastructure

if "%~1"=="" (
    echo ERROR: No backup file was supplied. >&2
    echo Usage: %~nx0 ^<backup-file.dump^> >&2
    exit /b 1
)

if not "%~2"=="" (
    echo ERROR: Too many arguments were supplied. >&2
    echo Usage: %~nx0 ^<backup-file.dump^> >&2
    exit /b 1
)

set "SCRIPT_DIR=%~dp0"

pushd "%SCRIPT_DIR%..\..\.." >nul 2>&1
if errorlevel 1 (
    echo ERROR: Could not locate the Ledger project directory. >&2
    exit /b 1
)

set "PROJECT_DIR=%CD%"
set "EXIT_CODE=0"

set "COMPOSE_FILE=%PROJECT_DIR%\compose.development-infrastructure.yaml"
set "ENV_FILE=%PROJECT_DIR%\config\environments\development-infrastructure.env"
set "BACKUP_DIR=%PROJECT_DIR%\backups\development-infrastructure"

if not exist "%COMPOSE_FILE%" (
    echo ERROR: Compose file not found: "%COMPOSE_FILE%" >&2
    set "EXIT_CODE=1"
    goto :cleanup
)

if not exist "%ENV_FILE%" (
    echo ERROR: Environment file not found: "%ENV_FILE%" >&2
    set "EXIT_CODE=1"
    goto :cleanup
)

set "LOCAL_ENV_FILE=%PROJECT_DIR%\config\environments\local.env"
if not exist "%LOCAL_ENV_FILE%" (
    echo ERROR: Local environment file not found: "%LOCAL_ENV_FILE%" >&2
    echo Copy config\environments\local.env.example to local.env and customise it. >&2
    set "EXIT_CODE=1"
    goto :cleanup
)

for %%I in ("%~1") do set "BACKUP_FILE=%%~fI"

if exist "%BACKUP_FILE%" goto :backup_file_resolved

for %%I in ("%BACKUP_DIR%\%~1") do set "BACKUP_FILE=%%~fI"

:backup_file_resolved

if not exist "%BACKUP_FILE%" (
    echo ERROR: Backup file not found. >&2
    echo Supplied value: "%~1" >&2
    echo Resolved path:  "%BACKUP_FILE%" >&2
    set "EXIT_CODE=1"
    goto :cleanup
)

for %%I in ("%BACKUP_FILE%") do set "BACKUP_SIZE=%%~zI"

if "%BACKUP_SIZE%"=="0" (
    echo ERROR: Backup file is empty: "%BACKUP_FILE%" >&2
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

if not defined LEDGER_DB_NAME set "LEDGER_DB_NAME=ledger"
if not defined LEDGER_DB_USERNAME set "LEDGER_DB_USERNAME=ledger"
if not defined LEDGER_DB_SERVICE set "LEDGER_DB_SERVICE=ledger-db"

docker compose ^
    -f "%COMPOSE_FILE%" ^
    --env-file "%ENV_FILE%" ^
    --env-file "%LOCAL_ENV_FILE%" ^
    config --quiet

if errorlevel 1 (
    echo ERROR: Docker Compose configuration is invalid. >&2
    set "EXIT_CODE=1"
    goto :cleanup
)

docker compose ^
    -f "%COMPOSE_FILE%" ^
    --env-file "%ENV_FILE%" ^
    --env-file "%LOCAL_ENV_FILE%" ^
    exec -T "%LEDGER_DB_SERVICE%" ^
    pg_isready ^
        -U "%LEDGER_DB_USERNAME%" ^
        -d "%LEDGER_DB_NAME%" ^
    >nul 2>&1

if errorlevel 1 (
    echo ERROR: PostgreSQL service "%LEDGER_DB_SERVICE%" is not running or is not ready. >&2
    echo Start the development infrastructure before restoring. >&2
    set "EXIT_CODE=1"
    goto :cleanup
)

echo.
echo WARNING: This will replace database objects in the development database.
echo.
echo IMPORTANT: Stop ledger-server before continuing so that it does not
echo access or modify the database while the restore is taking place.
echo.
echo Backup:
echo   File:     "%BACKUP_FILE%"
echo   Size:     %BACKUP_SIZE% bytes
echo.
echo Target:
echo   Compose:  "%COMPOSE_FILE%"
echo   Env file: "%ENV_FILE%"
echo   Service:  %LEDGER_DB_SERVICE%
echo   Database: %LEDGER_DB_NAME%
echo   User:     %LEDGER_DB_USERNAME%
echo.

set "ANSWER="
set /p "ANSWER=Type RESTORE to continue: "

if /I not "%ANSWER%"=="RESTORE" (
    echo.
    echo Restore cancelled.
    set "EXIT_CODE=0"
    goto :cleanup
)

echo.
echo Restoring the Ledger development database...

docker compose ^
    -f "%COMPOSE_FILE%" ^
    --env-file "%ENV_FILE%" ^
    --env-file "%LOCAL_ENV_FILE%" ^
    exec -T "%LEDGER_DB_SERVICE%" ^
    pg_restore ^
        -U "%LEDGER_DB_USERNAME%" ^
        -d "%LEDGER_DB_NAME%" ^
        --clean ^
        --if-exists ^
        --no-owner ^
        --no-privileges ^
        --exit-on-error ^
    < "%BACKUP_FILE%"

set "EXIT_CODE=%ERRORLEVEL%"

if not "%EXIT_CODE%"=="0" (
    echo. >&2
    echo ERROR: Database restore failed. >&2
    goto :cleanup
)

echo.
echo Database restore completed successfully.
echo.
echo Restart ledger-server so that it reconnects to the restored database.

:cleanup
popd
endlocal & exit /b %EXIT_CODE%
