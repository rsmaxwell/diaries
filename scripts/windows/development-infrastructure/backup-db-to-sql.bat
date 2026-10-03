@echo off
setlocal EnableExtensions

rem ============================================================================
rem backup-db-to-sql.bat
rem
rem Back up the Diaries PostgreSQL database used by development-infrastructure mode as
rem a plain-text SQL dump.
rem
rem Usage:
rem
rem     backup-db-to-sql.bat [output-file]
rem
rem If output-file is relative, it is written beneath the standard
rem development-infrastructure backup directory used by the restore script.
rem An absolute path is used unchanged. If no output-file is supplied, a
rem timestamped filename is generated in the standard backup directory.
rem
rem The script:
rem   - locates the Diaries project root;
rem   - validates and loads the development-infrastructure environment files;
rem   - creates the effective-dataset backup directory when necessary;
rem   - runs pg_dump inside the diaries-db container;
rem   - writes the SQL dump onto the Windows host;
rem   - removes an incomplete or empty backup if the operation fails.
rem
rem Output directory:
rem
rem     data\database-backups\<effective-dataset>
rem ============================================================================


rem ----------------------------------------------------------------------------
rem Initialise common script variables.
rem ----------------------------------------------------------------------------

set "SCRIPT_DIR=%~dp0"
set "EXIT_CODE=0"
set "BACKUP_FILE="


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
rem Create the effective-dataset backup directory if it does not already exist.
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
rem     backup-db-to-sql.bat rehearsal.sql
rem     restore-db-from-sql.bat data\database-backups\<effective-dataset>\rehearsal.sql
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
rem Run pg_dump inside the PostgreSQL container and redirect the plain-text SQL
rem stream to the Windows host.
rem ----------------------------------------------------------------------------

echo Operation: DATABASE-ONLY backup
echo Effective dataset: %DIARIES_DATASET_NAME%
echo Database data:    %DIARIES_EFFECTIVE_DB_DATA_DIR%
echo Files selector:   %DIARIES_FILES_DIR%
echo Files root:       %DIARIES_EFFECTIVE_FILES_ROOT%
echo Sharing:          %DIARIES_DATASET_SHARING%
echo Complete dataset: NO - mutable Files bytes are not included.
echo.

echo Backing up the development-infrastructure database as SQL...
echo Database: %DIARIES_DB_NAME%
echo Output:   %BACKUP_FILE%
echo.

docker compose ^
    --env-file "%ENV_FILE%" ^
    --env-file "%LOCAL_ENV_FILE%" ^
    -f "%COMPOSE_FILE%" ^
    exec -T diaries-db pg_dump ^
        --format=plain ^
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
rem Capture the catalogue count and write a sidecar dataset manifest.
rem The manifest makes the database-only nature explicit and records which
rem effective mutable Files root belongs with this database snapshot.
set "IMAGE_ROW_COUNT=unknown"
set "IMAGE_COUNT_FILE=%TEMP%\diaries-image-count-%RANDOM%-%RANDOM%.txt"
docker compose --env-file "%ENV_FILE%" --env-file "%LOCAL_ENV_FILE%" -f "%COMPOSE_FILE%" exec -T diaries-db psql -X -A -t --username "%DIARIES_DB_USERNAME%" --dbname "%DIARIES_DB_NAME%" -c "SELECT count(*) FROM public.image;" > "%IMAGE_COUNT_FILE%" 2>nul
if not errorlevel 1 (
    set /p "IMAGE_ROW_COUNT=" < "%IMAGE_COUNT_FILE%"
)
if exist "%IMAGE_COUNT_FILE%" del /q "%IMAGE_COUNT_FILE%"

set "MANIFEST_FILE="
for /f "usebackq delims=" %%I in (`powershell -NoProfile -ExecutionPolicy Bypass -File "%PROJECT_DIR%\scripts\windows\common\write-db-backup-manifest.ps1" -BackupFile "%BACKUP_FILE%" -BackupFormat "plain-sql" -ModeName "development-infrastructure" -DatasetName "%DIARIES_DATASET_NAME%" -DatabaseDataDir "%DIARIES_EFFECTIVE_DB_DATA_DIR%" -DatabaseName "%DIARIES_DB_NAME%" -FilesDir "%DIARIES_FILES_DIR%" -FilesRoot "%DIARIES_EFFECTIVE_FILES_ROOT%" -ProjectDir "%PROJECT_DIR%" -ImageRowCount "%IMAGE_ROW_COUNT%"`) do set "MANIFEST_FILE=%%I"
if not defined MANIFEST_FILE (
    echo ERROR: Database backup succeeded but its Step-7 dataset manifest could not be written. >&2
    set "EXIT_CODE=1"
    goto :cleanup
)


rem ----------------------------------------------------------------------------
rem Report successful completion.
rem ----------------------------------------------------------------------------

echo.
echo Database backup completed successfully:
echo %BACKUP_FILE%
echo Manifest: %MANIFEST_FILE%
echo NOTE: This is not a complete dataset backup; preserve matching Files separately.


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
rem drive-relative paths such as C:backup.sql are rejected.
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

set "BACKUP_FILE=%BACKUP_DIR%\diaries-%DIARIES_DATASET_NAME%-%TIMESTAMP%.sql"
exit /b 0
