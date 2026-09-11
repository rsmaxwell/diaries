@echo off
setlocal EnableExtensions

rem ============================================================================
rem restore-db-from-binary.bat
rem
rem Replace the development-infrastructure PostgreSQL database from a PostgreSQL custom
rem format dump created by pg_dump --format=custom.
rem
rem Usage:
rem
rem     restore-db-from-binary.bat [dump-file]
rem
rem If dump-file is supplied, that exact file is restored and it may be located
rem anywhere on the Windows host. If no file is supplied, the newest standard
rem development-infrastructure .dump file is selected from:
rem
rem     data\database-backups\development-infrastructure
rem
rem The existing database is dropped and recreated. The script asks for an
rem explicit RESTORE confirmation before making that destructive change.
rem ============================================================================


rem ----------------------------------------------------------------------------
rem Initialise common script variables.
rem ----------------------------------------------------------------------------

set "SCRIPT_DIR=%~dp0"
set "EXIT_CODE=0"
set "DUMP_FILE="


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
set "BACKUP_DIR=%PROJECT_DIR%\data\database-backups\development-infrastructure"

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
rem Select the dump file.
rem
rem IMPORTANT: An explicitly supplied path is handled first and does NOT depend
rem on the standard development-infrastructure backup directory existing.
rem
rem Only when no argument is supplied do we require BACKUP_DIR and search it for
rem the newest standard backup.
rem ----------------------------------------------------------------------------

if not "%~1"=="" (
    for %%I in ("%~1") do set "DUMP_FILE=%%~fI"
) else (
    if not exist "%BACKUP_DIR%" (
        echo ERROR: Backup directory not found: "%BACKUP_DIR%" >&2
        set "EXIT_CODE=1"
        goto :cleanup
    )

    for /f "delims=" %%F in ('dir /b /a-d /o-d "%BACKUP_DIR%\diaries-development-*.dump" 2^>nul') do (
        if not defined DUMP_FILE set "DUMP_FILE=%BACKUP_DIR%\%%F"
    )
)

if not defined DUMP_FILE (
    echo ERROR: No database dump files were found in: >&2
    echo "%BACKUP_DIR%" >&2
    set "EXIT_CODE=1"
    goto :cleanup
)


rem ----------------------------------------------------------------------------
rem Validate that the selected dump file exists and is not empty.
rem ----------------------------------------------------------------------------

if not exist "%DUMP_FILE%" (
    echo ERROR: Database dump file not found: >&2
    echo "%DUMP_FILE%" >&2
    set "EXIT_CODE=1"
    goto :cleanup
)

for %%F in ("%DUMP_FILE%") do set "DUMP_SIZE=%%~zF"
if "%DUMP_SIZE%"=="0" (
    echo ERROR: Database dump file is empty: >&2
    echo "%DUMP_FILE%" >&2
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
rem Validate the custom-format dump before touching the existing database.
rem
rem pg_restore --list reads the supplied dump from standard input. Failure here
rem leaves the existing database unchanged.
rem ----------------------------------------------------------------------------

echo Validating database dump...

docker compose ^
    --env-file "%ENV_FILE%" ^
    --env-file "%LOCAL_ENV_FILE%" ^
    -f "%COMPOSE_FILE%" ^
    exec -T diaries-db pg_restore --list < "%DUMP_FILE%" >nul

if errorlevel 1 (
    echo. >&2
    echo ERROR: The selected file is not a valid PostgreSQL custom-format dump: >&2
    echo "%DUMP_FILE%" >&2
    set "EXIT_CODE=1"
    goto :cleanup
)


rem ----------------------------------------------------------------------------
rem Require explicit confirmation before dropping the current database.
rem ----------------------------------------------------------------------------

echo.
echo WARNING: This will completely replace the development-infrastructure database.
echo.
echo Database: %DIARIES_DB_NAME%
echo Dump:     %DUMP_FILE%
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
rem Restore the validated dump into the newly created database.
rem ----------------------------------------------------------------------------

echo Restoring the database dump...

docker compose ^
    --env-file "%ENV_FILE%" ^
    --env-file "%LOCAL_ENV_FILE%" ^
    -f "%COMPOSE_FILE%" ^
    exec -T diaries-db pg_restore ^
        --exit-on-error ^
        --no-owner ^
        --no-privileges ^
        --username "%DIARIES_DB_USERNAME%" ^
        --dbname "%DIARIES_DB_NAME%" < "%DUMP_FILE%"

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
echo Source:   %DUMP_FILE%
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
