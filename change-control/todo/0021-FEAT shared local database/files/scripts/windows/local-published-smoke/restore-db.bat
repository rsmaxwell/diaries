@echo off
setlocal

rem Restore the PostgreSQL database used by the local published-image
rem smoke-test environment.
rem
rem Usage:
rem   restore-db.bat backup-file.dump
rem
rem The backup must be a PostgreSQL custom-format dump created by
rem backup-db.bat.
rem
rem When only a filename is supplied, the script looks in:
rem   ledger\backups\local-published-smoke
rem
rem The restore uses pg_restore with --clean and --if-exists, replacing
rem database objects contained in the backup.

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

set "COMPOSE_FILE=%PROJECT_DIR%\compose.local-published-smoke.yaml"
set "ENV_FILE=%PROJECT_DIR%\config\environments\local-published-smoke.env"
set "BACKUP_DIR=%PROJECT_DIR%\backups\local-published-smoke"

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

rem First try the supplied value as an absolute or caller-relative path.
for %%I in ("%~1") do set "BACKUP_FILE=%%~fI"

if exist "%BACKUP_FILE%" goto :backup_file_resolved

rem If that was not found, try the standard backup directory used by
rem backup-db.bat.
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

rem Apply any optional local image-tag or mode overrides after loading the
rem baseline local-published-smoke environment.
if not exist "%SCRIPT_DIR%set-env.bat" goto :set_env_loaded

call "%SCRIPT_DIR%set-env.bat"
if errorlevel 1 (
    echo ERROR: Failed to load "%SCRIPT_DIR%set-env.bat". >&2
    set "EXIT_CODE=1"
    goto :cleanup
)

:set_env_loaded

if not defined LEDGER_DB_NAME set "LEDGER_DB_NAME=ledger"
if not defined LEDGER_DB_USERNAME set "LEDGER_DB_USERNAME=ledger"
if not defined LEDGER_DB_SERVICE set "LEDGER_DB_SERVICE=ledger-db"

docker compose ^
    --env-file "%ENV_FILE%" ^
    --env-file "%LOCAL_ENV_FILE%" ^
    -f "%COMPOSE_FILE%" ^
    config --quiet

if errorlevel 1 (
    echo ERROR: Docker Compose configuration is invalid. >&2
    set "EXIT_CODE=1"
    goto :cleanup
)

rem Verify that PostgreSQL is running and accepting connections.
docker compose ^
    --env-file "%ENV_FILE%" ^
    --env-file "%LOCAL_ENV_FILE%" ^
    -f "%COMPOSE_FILE%" ^
    exec -T "%LEDGER_DB_SERVICE%" ^
    pg_isready ^
        -U "%LEDGER_DB_USERNAME%" ^
        -d "%LEDGER_DB_NAME%" ^
    >nul 2>&1

if errorlevel 1 (
    echo ERROR: PostgreSQL service "%LEDGER_DB_SERVICE%" is not running or is not ready. >&2
    echo Start the local published-image smoke-test stack before restoring. >&2
    set "EXIT_CODE=1"
    goto :cleanup
)

echo.
echo WARNING: This will replace database objects in the target database.
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
echo Ensure that no users or scripts are changing Ledger data during restore.
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
echo Restoring the Ledger database...

docker compose ^
    --env-file "%ENV_FILE%" ^
    --env-file "%LOCAL_ENV_FILE%" ^
    -f "%COMPOSE_FILE%" ^
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
echo Restart the local published-image smoke-test stack so that the server
echo reconnects cleanly and reloads the restored data.

:cleanup
popd
endlocal & exit /b %EXIT_CODE%
