@echo off
setlocal EnableExtensions

rem ============================================================================
rem backup-db-to-binary.bat
rem
rem Back up the Diaries PostgreSQL database used by local-docker-build mode in
rem PostgreSQL custom (binary) format.
rem
rem The script:
rem   - locates the Diaries project root;
rem   - validates and loads the local-docker-build environment files;
rem   - creates the mode-specific backup directory when necessary;
rem   - runs pg_dump inside the diaries-db container;
rem   - writes the dump onto the Windows host;
rem   - removes an incomplete or empty backup if the operation fails.
rem
rem Output directory:
rem
rem     data\database-backups\local-docker-build
rem ============================================================================


rem ----------------------------------------------------------------------------
rem Initialise common script variables.
rem ----------------------------------------------------------------------------

set "SCRIPT_DIR=%~dp0"
set "EXIT_CODE=0"


rem ----------------------------------------------------------------------------
rem Locate the Diaries project root.
rem
rem This script is located under:
rem
rem     diaries\scripts\windows\local-docker-build
rem
rem Moving up three levels therefore gives us the Diaries project directory.
rem Exit immediately if that directory cannot be located. Since pushd has not
rem succeeded in that case, there is no corresponding popd to perform.
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
rem
rem The committed local-docker-build environment is loaded first and local.env
rem second, so machine-specific values in local.env override mode defaults.
rem ----------------------------------------------------------------------------

set "COMPOSE_FILE=%PROJECT_DIR%\compose.local-docker-build.yaml"
set "ENV_FILE=%PROJECT_DIR%\config\environments\local-docker-build.env"
set "LOCAL_ENV_FILE=%PROJECT_DIR%\config\environments\local.env"
set "BACKUP_DIR=%PROJECT_DIR%\data\database-backups\local-docker-build"

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
rem Load the environment into this batch process.
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
rem Create the mode-specific backup directory if it does not already exist.
rem ----------------------------------------------------------------------------

if not exist "%BACKUP_DIR%" (
    mkdir "%BACKUP_DIR%"
    if errorlevel 1 (
        echo ERROR: Unable to create backup directory: "%BACKUP_DIR%" >&2
        set "EXIT_CODE=1"
        goto :cleanup
    )
)


rem ----------------------------------------------------------------------------
rem Generate an unambiguous, filesystem-safe local timestamp and output name.
rem ----------------------------------------------------------------------------

set "TIMESTAMP="
for /f %%I in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd-HHmmss"') do set "TIMESTAMP=%%I"

if not defined TIMESTAMP (
    echo ERROR: Unable to generate backup timestamp. >&2
    set "EXIT_CODE=1"
    goto :cleanup
)

set "BACKUP_FILE=%BACKUP_DIR%\diaries-local-docker-build-%TIMESTAMP%.dump"


rem ----------------------------------------------------------------------------
rem Run pg_dump inside the PostgreSQL container.
rem
rem -T disables pseudo-TTY allocation so the custom-format binary stream can
rem be redirected safely to a file on the Windows host.
rem ----------------------------------------------------------------------------

echo Backing up the local-docker-build database...
echo Database: %DIARIES_DB_NAME%
echo Output:   %BACKUP_FILE%
echo.

docker compose ^
    --env-file "%ENV_FILE%" ^
    --env-file "%LOCAL_ENV_FILE%" ^
    -f "%COMPOSE_FILE%" ^
    exec -T diaries-db pg_dump ^
        --format=custom ^
        --no-owner ^
        --no-privileges ^
        --username "%DIARIES_DB_USERNAME%" ^
        --dbname "%DIARIES_DB_NAME%" > "%BACKUP_FILE%"

set "EXIT_CODE=%ERRORLEVEL%"
if not "%EXIT_CODE%"=="0" (
    if exist "%BACKUP_FILE%" del /q "%BACKUP_FILE%"
    echo. >&2
    echo ERROR: Database backup failed with exit code %EXIT_CODE%. >&2
    echo Check that the local-docker-build database container is running. >&2
    goto :cleanup
)


rem ----------------------------------------------------------------------------
rem Reject an empty output file even if pg_dump returned success.
rem ----------------------------------------------------------------------------

for %%F in ("%BACKUP_FILE%") do set "BACKUP_SIZE=%%~zF"
if "%BACKUP_SIZE%"=="0" (
    del /q "%BACKUP_FILE%"
    echo. >&2
    echo ERROR: Database backup failed because the output file was empty. >&2
    set "EXIT_CODE=1"
    goto :cleanup
)


rem ----------------------------------------------------------------------------
rem Report successful completion.
rem ----------------------------------------------------------------------------

echo.
echo Database backup completed successfully:
echo %BACKUP_FILE%


rem ----------------------------------------------------------------------------
rem Common cleanup and exit.
rem ----------------------------------------------------------------------------

:cleanup
popd
endlocal & exit /b %EXIT_CODE%
