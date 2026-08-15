@echo off
setlocal EnableExtensions

rem Locate the Diaries project directory from this script:
rem scripts\windows\development-infrastructure\backup-to-binary.bat
set "EXIT_CODE=0"

set "SCRIPT_DIR=%~dp0"
pushd "%SCRIPT_DIR%..\..\.." >nul 2>&1
if errorlevel 1 (
    echo ERROR: Could not locate the project directory. >&2
    endlocal & exit /b 1
)

set "PROJECT_DIR=%CD%"



rem These defaults match compose.development-infrastructure.yaml. Existing environment
rem variables take precedence when the development database is customised.
set "COMPOSE_FILE=%PROJECT_DIR%\compose.development-infrastructure.yaml"
if not exist "%COMPOSE_FILE%" (
    echo Compose file not found: "%COMPOSE_FILE%"
    set "EXIT_CODE=1"
    goto :cleanup
)

set "ENV_FILE=%PROJECT_DIR%\config\environments\development-infrastructure.env"
if not exist "%ENV_FILE%" (
    echo Environment file not found: "%ENV_FILE%"
    set "EXIT_CODE=1"
    goto :cleanup
)

set "LOCAL_ENV_FILE=%PROJECT_DIR%\config\environments\local.env"
if not exist "%LOCAL_ENV_FILE%" (
    echo Environment file not found: "%LOCAL_ENV_FILE%"
    set "EXIT_CODE=1"
    goto :cleanup
)

set "BACKUP_DIR=%PROJECT_DIR%\data\database-backups\development-infrastructure"
if not exist "%BACKUP_DIR%" (
    mkdir "%BACKUP_DIR%"
    if errorlevel 1 (
        echo Unable to create backup directory: "%BACKUP_DIR%"
        set "EXIT_CODE=1"
        goto :cleanup
    )
)

call "%PROJECT_DIR%\scripts\windows\common\load-dotenv.bat" "%ENV_FILE%"
if errorlevel 1 (
    set "EXIT_CODE=1"
    goto :cleanup
)

call "%PROJECT_DIR%\scripts\windows\common\load-dotenv.bat" "%LOCAL_ENV_FILE%"
if errorlevel 1 (
    set "EXIT_CODE=1"
    goto :cleanup
)

if not defined DIARIES_DB_NAME set "DIARIES_DB_NAME=diaries"
if not defined DIARIES_DB_USERNAME set "DIARIES_DB_USERNAME=diaries"




rem Use an unambiguous, filesystem-safe local timestamp.
set "TIMESTAMP="

for /f %%I in (
    'powershell -NoProfile -Command "Get-Date -Format yyyyMMdd-HHmmss"'
) do set "TIMESTAMP=%%I"

if not defined TIMESTAMP (
    echo ERROR: Could not generate backup timestamp. >&2
    set "EXIT_CODE=1"
    goto :cleanup
)

set "BACKUP_FILE=%BACKUP_DIR%\diaries-development-%TIMESTAMP%.dump"

echo Backing up the development-infrastructure database...
echo Database: %DIARIES_DB_NAME%
echo Output:   %BACKUP_FILE%
echo.

rem pg_dump runs inside the PostgreSQL container, while redirection writes the
rem custom-format binary dump onto the Windows host.
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
    echo.
    echo Database backup failed with exit code %EXIT_CODE%.
    echo Check that the development database container is running.
    set "EXIT_CODE=1"
    goto :cleanup
)

for %%F in ("%BACKUP_FILE%") do set "BACKUP_SIZE=%%~zF"
if "%BACKUP_SIZE%"=="0" (
    del /q "%BACKUP_FILE%"
    echo.
    echo Database backup failed because the output file was empty.
    set "EXIT_CODE=1"
    goto :cleanup
)

echo.
echo Database backup completed successfully:
echo %BACKUP_FILE%

:cleanup
popd
endlocal & exit /b %EXIT_CODE%
