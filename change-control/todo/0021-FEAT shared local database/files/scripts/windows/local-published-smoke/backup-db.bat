@echo off
setlocal

rem Back up the PostgreSQL database used by the local published-image
rem smoke-test environment.
rem
rem The backup is written in PostgreSQL custom format under:
rem   ledger\backups\local-published-smoke

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
    set "EXIT_CODE=1"
    goto :cleanup
)

if not exist "%BACKUP_DIR%\" (
    mkdir "%BACKUP_DIR%" >nul 2>&1
    if errorlevel 1 (
        echo ERROR: Could not create backup directory: "%BACKUP_DIR%" >&2
        set "EXIT_CODE=1"
        goto :cleanup
    )
)

set "STAMP="

for /f %%I in (
    'powershell -NoProfile -Command "Get-Date -Format yyyyMMdd-HHmmss"'
) do set "STAMP=%%I"

if not defined STAMP (
    echo ERROR: Could not generate the backup timestamp. >&2
    set "EXIT_CODE=1"
    goto :cleanup
)

set "BACKUP_FILE=%BACKUP_DIR%\ledger-%STAMP%.dump"

echo Creating local published-smoke database backup:
echo   Compose file: "%COMPOSE_FILE%"
echo   Env file:     "%ENV_FILE%"
echo   Service:      %LEDGER_DB_SERVICE%
echo   Database:     %LEDGER_DB_NAME%
echo   User:         %LEDGER_DB_USERNAME%
echo   File:         "%BACKUP_FILE%"
echo.

docker compose ^
    --env-file "%ENV_FILE%" ^
    --env-file "%LOCAL_ENV_FILE%" ^
    -f "%COMPOSE_FILE%" ^
    exec -T "%LEDGER_DB_SERVICE%" ^
    pg_dump ^
        -U "%LEDGER_DB_USERNAME%" ^
        -d "%LEDGER_DB_NAME%" ^
        -Fc ^
    > "%BACKUP_FILE%"

set "EXIT_CODE=%ERRORLEVEL%"

if not "%EXIT_CODE%"=="0" (
    echo. >&2
    echo ERROR: Database backup failed. >&2

    if exist "%BACKUP_FILE%" (
        del "%BACKUP_FILE%" >nul 2>&1
    )

    goto :cleanup
)

if not exist "%BACKUP_FILE%" (
    echo ERROR: pg_dump reported success but no backup file was created. >&2
    set "EXIT_CODE=1"
    goto :cleanup
)

for %%I in ("%BACKUP_FILE%") do set "BACKUP_SIZE=%%~zI"

if "%BACKUP_SIZE%"=="0" (
    echo ERROR: pg_dump produced an empty backup file. >&2
    del "%BACKUP_FILE%" >nul 2>&1
    set "EXIT_CODE=1"
    goto :cleanup
)

echo.
echo Database backup complete:
echo   "%BACKUP_FILE%"
echo   Size: %BACKUP_SIZE% bytes

:cleanup
popd
endlocal & exit /b %EXIT_CODE%
