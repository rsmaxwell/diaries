@echo off
setlocal EnableExtensions

rem ============================================================================
rem restore-db-from-sql.bat
rem
rem Replace the development-infrastructure PostgreSQL database from a plain-text SQL
rem dump created by pg_dump --format=plain.
rem
rem Usage:
rem
rem     restore-db-from-sql.bat [sql-file]
rem
rem If sql-file is supplied, that exact file is restored and it may be located
rem anywhere on the Windows host. If no file is supplied, the newest standard
rem development-infrastructure .sql file is selected from:
rem
rem     data\database-backups\<effective-dataset>
rem
rem The existing database is dropped and recreated. The script asks for an
rem explicit RESTORE confirmation before making that destructive change.
rem ============================================================================


rem ----------------------------------------------------------------------------
rem Initialise common script variables.
rem ----------------------------------------------------------------------------

set "SCRIPT_DIR=%~dp0"
set "EXIT_CODE=0"
set "SQL_FILE="


rem ----------------------------------------------------------------------------
rem Locate the Diaries project root.
rem ----------------------------------------------------------------------------

pushd "%SCRIPT_DIR%..\..\.." >nul 2>&1
if errorlevel 1 (
    echo ERROR: Could not locate the Diaries project root. >&2
    echo Script directory: "%SCRIPT_DIR%" >&2
    endlocal & exit /b 1
)

set "PROJECT_DIR=%CD%"


rem ----------------------------------------------------------------------------
rem Define and validate the Compose and environment files.
rem ----------------------------------------------------------------------------

set "COMPOSE_FILE=%PROJECT_DIR%\compose.development-infrastructure.yaml"
set "ENV_FILE=%PROJECT_DIR%\config\environments\development-infrastructure.env"
set "LOCAL_ENV_FILE=%PROJECT_DIR%\config\environments\local.env"

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

if not exist "%LOCAL_ENV_FILE%" (
    echo ERROR: Local environment file not found: "%LOCAL_ENV_FILE%" >&2
    set "EXIT_CODE=1"
    goto :cleanup
)


rem ----------------------------------------------------------------------------
rem Load the committed mode environment first, followed by local.env.
rem ----------------------------------------------------------------------------

call "%PROJECT_DIR%\scripts\windows\common\load-dotenv.bat" "%ENV_FILE%"
if errorlevel 1 (
    echo ERROR: Could not load environment file: "%ENV_FILE%" >&2
    set "EXIT_CODE=1"
    goto :cleanup
)

call "%PROJECT_DIR%\scripts\windows\common\load-dotenv.bat" "%LOCAL_ENV_FILE%"
if errorlevel 1 (
    echo ERROR: Could not load local environment file: "%LOCAL_ENV_FILE%" >&2
    set "EXIT_CODE=1"
    goto :cleanup
)

if not defined DIARIES_DB_NAME set "DIARIES_DB_NAME=diaries"
if not defined DIARIES_DB_USERNAME set "DIARIES_DB_USERNAME=diaries"

rem ----------------------------------------------------------------------------
rem Validate and describe the effective durable dataset selected after local.env.
rem Step 7 deliberately keys backup locations from DIARIES_DB_DATA_DIR rather
rem than the launch-mode name so shared common data is backed up only as common.
rem ----------------------------------------------------------------------------

call "%PROJECT_DIR%\scripts\windows\common\validate-dataset-pair.bat" "development-infrastructure" "%ENV_FILE%" "%LOCAL_ENV_FILE%"
if errorlevel 1 (
    set "EXIT_CODE=1"
    goto :cleanup
)

set "DIARIES_DATASET_NAME="
set "DIARIES_EFFECTIVE_DB_DATA_DIR="
set "DIARIES_EFFECTIVE_FILES_ROOT="
set "DIARIES_DATASET_SHARING="

for /f "usebackq tokens=1,* delims==" %%A in (`powershell -NoProfile -ExecutionPolicy Bypass -File "%PROJECT_DIR%\scripts\windows\common\resolve-effective-dataset.ps1" -ModeName "development-infrastructure" -ProjectDir "%PROJECT_DIR%" -DatabaseDataDir "%DIARIES_DB_DATA_DIR%" -FilesDir "%DIARIES_FILES_DIR%"`) do set "%%A=%%B"
if errorlevel 1 (
    echo ERROR: Unable to resolve the effective durable dataset. >&2
    set "EXIT_CODE=1"
    goto :cleanup
)

if not defined DIARIES_DATASET_NAME (
    echo ERROR: Effective dataset name was not resolved. >&2
    set "EXIT_CODE=1"
    goto :cleanup
)

set "BACKUP_DIR=%PROJECT_DIR%\data\database-backups\%DIARIES_DATASET_NAME%"



rem ----------------------------------------------------------------------------
rem Select the SQL file.
rem
rem IMPORTANT: An explicitly supplied path is handled first and does NOT depend
rem on the standard effective-dataset backup directory existing.
rem ----------------------------------------------------------------------------

if not "%~1"=="" (
    for %%I in ("%~1") do set "SQL_FILE=%%~fI"
) else (
    if not exist "%BACKUP_DIR%" (
        echo ERROR: Backup directory not found: "%BACKUP_DIR%" >&2
        set "EXIT_CODE=1"
        goto :cleanup
    )

    for /f "delims=" %%F in ('dir /b /a-d /o-d "%BACKUP_DIR%\diaries-%DIARIES_DATASET_NAME%-*.sql" 2^>nul') do (
        if not defined SQL_FILE set "SQL_FILE=%BACKUP_DIR%\%%F"
    )
)

if not defined SQL_FILE (
    echo ERROR: No database SQL backup files were found in: >&2
    echo "%BACKUP_DIR%" >&2
    set "EXIT_CODE=1"
    goto :cleanup
)


rem ----------------------------------------------------------------------------
rem Validate that the selected SQL file exists and is not empty.
rem ----------------------------------------------------------------------------

if not exist "%SQL_FILE%" (
    echo ERROR: Database SQL backup file not found: >&2
    echo "%SQL_FILE%" >&2
    set "EXIT_CODE=1"
    goto :cleanup
)

for %%F in ("%SQL_FILE%") do set "SQL_SIZE=%%~zF"
if "%SQL_SIZE%"=="0" (
    echo ERROR: Database SQL backup file is empty: >&2
    echo "%SQL_FILE%" >&2
    set "EXIT_CODE=1"
    goto :cleanup
)


rem ----------------------------------------------------------------------------
rem Perform a lightweight validation before touching the current database.
rem
rem A plain SQL dump produced by pg_dump contains the standard phrase below in
rem its header. This also catches the common mistake of supplying a custom
rem binary .dump file to the SQL restore script.
rem ----------------------------------------------------------------------------

findstr /c:"PostgreSQL database dump" "%SQL_FILE%" >nul
if errorlevel 1 (
    echo ERROR: The selected file does not appear to be a PostgreSQL plain SQL dump: >&2
    echo "%SQL_FILE%" >&2
    set "EXIT_CODE=1"
    goto :cleanup
)


rem ----------------------------------------------------------------------------
rem Check that the development-infrastructure PostgreSQL service is available.
rem ----------------------------------------------------------------------------

docker compose ^
    --env-file "%ENV_FILE%" ^
    --env-file "%LOCAL_ENV_FILE%" ^
    -f "%COMPOSE_FILE%" ^
    exec -T diaries-db pg_isready ^
        --username "%DIARIES_DB_USERNAME%" ^
        --dbname postgres >nul 2>&1

if errorlevel 1 (
    echo ERROR: The development-infrastructure database is not ready. >&2
    echo Start the stack before running this restore script. >&2
    set "EXIT_CODE=1"
    goto :cleanup
)


rem ----------------------------------------------------------------------------
rem Verify the optional Step-7 sidecar manifest before any destructive database
rem change. Legacy dumps without a manifest remain usable, but are clearly
rem identified as requiring manual Files-root verification.
powershell -NoProfile -ExecutionPolicy Bypass -File "%PROJECT_DIR%\scripts\windows\common\verify-db-backup-manifest.ps1" -BackupFile "%SQL_FILE%" -DatasetName "%DIARIES_DATASET_NAME%" -DatabaseDataDir "%DIARIES_EFFECTIVE_DB_DATA_DIR%" -FilesDir "%DIARIES_FILES_DIR%" -FilesRoot "%DIARIES_EFFECTIVE_FILES_ROOT%"
if errorlevel 1 (
    echo ERROR: Refusing database restore because the backup dataset identity does not match the current effective database + Files pair. >&2
    set "EXIT_CODE=1"
    goto :cleanup
)

echo.
echo Operation: DATABASE-ONLY restore
echo Effective dataset: %DIARIES_DATASET_NAME%
echo Database data:    %DIARIES_EFFECTIVE_DB_DATA_DIR%
echo Files selector:   %DIARIES_FILES_DIR%
echo Files root:       %DIARIES_EFFECTIVE_FILES_ROOT%
echo Complete restore: NO - mutable Files bytes will not be restored.
echo.


rem ----------------------------------------------------------------------------
rem Require explicit confirmation before dropping the current database.
rem ----------------------------------------------------------------------------

echo.
echo WARNING: This will completely replace the development-infrastructure database.
echo.
echo Database: %DIARIES_DB_NAME%
echo SQL file: %SQL_FILE%
echo.
echo Stop any responder that can access this database before continuing.
echo.

set "CONFIRM="
set /p "CONFIRM=Type RESTORE to continue: "
if /i not "%CONFIRM%"=="RESTORE" (
    echo Restore cancelled.
    set "EXIT_CODE=1"
    goto :cleanup
)


rem ----------------------------------------------------------------------------
rem Drop and recreate the target database.
rem ----------------------------------------------------------------------------

echo.
echo Dropping the existing database...

docker compose ^
    --env-file "%ENV_FILE%" ^
    --env-file "%LOCAL_ENV_FILE%" ^
    -f "%COMPOSE_FILE%" ^
    exec -T diaries-db dropdb ^
        --force ^
        --if-exists ^
        --username "%DIARIES_DB_USERNAME%" ^
        "%DIARIES_DB_NAME%"

if errorlevel 1 (
    set "EXIT_CODE=%ERRORLEVEL%"
    goto :restore_failed
)

echo Creating a new empty database...

docker compose ^
    --env-file "%ENV_FILE%" ^
    --env-file "%LOCAL_ENV_FILE%" ^
    -f "%COMPOSE_FILE%" ^
    exec -T diaries-db createdb ^
        --username "%DIARIES_DB_USERNAME%" ^
        --owner "%DIARIES_DB_USERNAME%" ^
        "%DIARIES_DB_NAME%"

if errorlevel 1 (
    set "EXIT_CODE=%ERRORLEVEL%"
    goto :restore_failed
)


rem ----------------------------------------------------------------------------
rem Restore the SQL dump. ON_ERROR_STOP makes psql return failure on the first
rem SQL error instead of continuing through a partially failed restore.
rem ----------------------------------------------------------------------------

echo Restoring the SQL backup...

docker compose ^
    --env-file "%ENV_FILE%" ^
    --env-file "%LOCAL_ENV_FILE%" ^
    -f "%COMPOSE_FILE%" ^
    exec -T diaries-db psql ^
        --set ON_ERROR_STOP=on ^
        --username "%DIARIES_DB_USERNAME%" ^
        --dbname "%DIARIES_DB_NAME%" < "%SQL_FILE%"

if errorlevel 1 (
    set "EXIT_CODE=%ERRORLEVEL%"
    goto :restore_failed
)


rem ----------------------------------------------------------------------------
rem Report successful completion.
rem ----------------------------------------------------------------------------

echo.
echo Database restore completed successfully.
echo Database: %DIARIES_DB_NAME%
echo Source:   %SQL_FILE%
set "EXIT_CODE=0"
goto :cleanup


rem ----------------------------------------------------------------------------
rem Report a failure after the destructive phase has begun.
rem ----------------------------------------------------------------------------

:restore_failed
echo. >&2
echo ERROR: Database restore failed with exit code %EXIT_CODE%. >&2
echo The original database has already been removed and may now be empty or >&2
echo only partially restored. Correct the problem and run this script again. >&2


rem ----------------------------------------------------------------------------
rem Common cleanup and exit.
rem ----------------------------------------------------------------------------

:cleanup
popd
endlocal & exit /b %EXIT_CODE%
