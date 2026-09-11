@echo off
setlocal EnableExtensions

rem ============================================================================
rem backup-db-to-binary.bat
rem
rem Back up the Diaries PostgreSQL database used by development-infrastructure mode in
rem PostgreSQL custom (binary) format.
rem
rem Usage:
rem
rem     backup-db-to-binary.bat [output-file]
rem
rem If output-file is relative, it is written beneath the standard
rem development-infrastructure backup directory used by the restore script.
rem An absolute path is used unchanged. If no output-file is supplied, a
rem timestamped filename is generated in the standard backup directory.
rem
rem The script:
rem   - locates the Diaries project root;
rem   - validates and loads the development-infrastructure environment files;
rem   - creates the mode-specific backup directory when necessary;
rem   - runs pg_dump inside the diaries-db container;
rem   - writes the dump onto the Windows host;
rem   - removes an incomplete or empty backup if the operation fails.
rem
rem Output directory:
rem
rem     data\database-backups\development-infrastructure
rem ============================================================================


rem ----------------------------------------------------------------------------
rem Initialise common script variables.
rem ----------------------------------------------------------------------------

set "SCRIPT_DIR=%~dp0"
set "EXIT_CODE=0"
set "BACKUP_FILE="


rem ----------------------------------------------------------------------------
rem Locate the Diaries project root.
rem
rem This script is located under:
rem
rem     diaries\scripts\windows\development-infrastructure
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
rem The committed development-infrastructure environment is loaded first and local.env
rem second, so machine-specific values in local.env override mode defaults.
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
rem Select the output file.
rem
rem A supplied relative filename is resolved beneath BACKUP_DIR so that, for
rem example, both of these commands refer to the same file:
rem
rem     backup-db-to-binary.bat rehearsal.dump
rem     restore-db-from-binary.bat data\database-backups\development-infrastructure\rehearsal.dump
rem
rem Drive-qualified, UNC and root-relative paths are treated as explicit.
rem Without an argument, generate an unambiguous timestamped output name.
rem ----------------------------------------------------------------------------

if not "%~1"=="" (
    set "BACKUP_FILE=%~1"
    call :resolve_backup_file
    if errorlevel 1 (
        set "EXIT_CODE=1"
        goto :cleanup
    )
) else (
    call :set_default_backup_file
    if errorlevel 1 (
        set "EXIT_CODE=1"
        goto :cleanup
    )
)

for %%I in ("%BACKUP_FILE%") do set "BACKUP_PARENT=%%~dpI"
if not exist "%BACKUP_PARENT%" (
    echo ERROR: Output directory not found: "%BACKUP_PARENT%" >&2
    set "EXIT_CODE=1"
    goto :cleanup
)


rem ----------------------------------------------------------------------------
rem Run pg_dump inside the PostgreSQL container.
rem
rem -T disables pseudo-TTY allocation so the custom-format binary stream can
rem be redirected safely to a file on the Windows host.
rem ----------------------------------------------------------------------------

echo Backing up the development-infrastructure database...
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
    echo Check that the development-infrastructure database container is running. >&2
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


rem ----------------------------------------------------------------------------
rem Resolve a caller-supplied output filename.
rem
rem A fully-qualified drive path, UNC path or root-relative path is explicit.
rem Every other path is relative to the standard backup directory. Ambiguous
rem drive-relative paths such as C:backup.dump are rejected.
rem ----------------------------------------------------------------------------

:resolve_backup_file
if "%BACKUP_FILE:~1,1%"==":" (
    if not "%BACKUP_FILE:~2,1%"=="\" if not "%BACKUP_FILE:~2,1%"=="/" (
        echo ERROR: Drive-relative output paths are not supported: "%BACKUP_FILE%" >&2
        exit /b 1
    )
)

if "%BACKUP_FILE:~0,1%"=="\" goto :resolve_explicit_backup_file
if "%BACKUP_FILE:~0,1%"=="/" goto :resolve_explicit_backup_file
if "%BACKUP_FILE:~1,2%"==":\" goto :resolve_explicit_backup_file
if "%BACKUP_FILE:~1,2%"==":/" goto :resolve_explicit_backup_file

for %%I in ("%BACKUP_DIR%\%BACKUP_FILE%") do set "BACKUP_FILE=%%~fI"
exit /b 0

:resolve_explicit_backup_file
    for %%I in ("%BACKUP_FILE%") do set "BACKUP_FILE=%%~fI"
exit /b 0


rem ----------------------------------------------------------------------------
rem Generate the default timestamped output name outside the caller's
rem parenthesised block so TIMESTAMP is expanded only after it has been set.
rem ----------------------------------------------------------------------------

:set_default_backup_file
set "TIMESTAMP="
for /f %%I in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd-HHmmss"') do set "TIMESTAMP=%%I"

if not defined TIMESTAMP (
    echo ERROR: Unable to generate backup timestamp. >&2
    exit /b 1
)

set "BACKUP_FILE=%BACKUP_DIR%\diaries-development-%TIMESTAMP%.dump"
exit /b 0
