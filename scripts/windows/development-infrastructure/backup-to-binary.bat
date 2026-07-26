@echo off
setlocal EnableExtensions

rem Locate the Diaries project directory from this script:
rem scripts\windows\development-infrastructure\backup-to-binary.bat
set "SCRIPT_DIR=%~dp0"
pushd "%SCRIPT_DIR%..\..\.." >nul
if errorlevel 1 (
    echo Unable to locate the Diaries project directory.
    exit /b 1
)
set "PROJECT_DIR=%CD%"

set "COMPOSE_FILE=%PROJECT_DIR%\compose.development.yaml"
set "BACKUP_DIR=%PROJECT_DIR%\data\database-backups\day-to-day-development"

rem These defaults match compose.development.yaml. Existing environment
rem variables take precedence when the development database is customised.
if not defined DIARIES_DB_NAME set "DIARIES_DB_NAME=diaries"
if not defined DIARIES_DB_USERNAME set "DIARIES_DB_USERNAME=diaries"

if not exist "%COMPOSE_FILE%" (
    echo Compose file not found: "%COMPOSE_FILE%"
    popd
    exit /b 1
)

if not exist "%BACKUP_DIR%" (
    mkdir "%BACKUP_DIR%"
    if errorlevel 1 (
        echo Unable to create backup directory: "%BACKUP_DIR%"
        popd
        exit /b 1
    )
)

rem Use an unambiguous, filesystem-safe local timestamp.
for /f %%I in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd-HHmmss"') do set "TIMESTAMP=%%I"
set "BACKUP_FILE=%BACKUP_DIR%\diaries-development-%TIMESTAMP%.dump"

echo Backing up the day-to-day-development database...
echo Database: %DIARIES_DB_NAME%
echo Output:   %BACKUP_FILE%
echo.

rem pg_dump runs inside the PostgreSQL container, while redirection writes the
rem custom-format binary dump onto the Windows host.
docker compose -f "%COMPOSE_FILE%" exec -T diaries-db pg_dump ^
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
    popd
    endlocal & exit /b %EXIT_CODE%
)

for %%F in ("%BACKUP_FILE%") do set "BACKUP_SIZE=%%~zF"
if "%BACKUP_SIZE%"=="0" (
    del /q "%BACKUP_FILE%"
    echo.
    echo Database backup failed because the output file was empty.
    popd
    endlocal & exit /b 1
)

echo.
echo Database backup completed successfully:
echo %BACKUP_FILE%

popd
endlocal & exit /b 0
