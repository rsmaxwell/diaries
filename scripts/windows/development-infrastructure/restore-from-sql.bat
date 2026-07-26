@echo off
setlocal EnableExtensions

rem Locate the Diaries project directory from this script:
rem scripts\windows\development-infrastructure\restore-from-sql.bat
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
    echo Backup directory not found: "%BACKUP_DIR%"
    popd
    exit /b 1
)

rem An SQL file may be supplied as the first argument. Otherwise restore the
rem newest standard development SQL backup from the normal backup directory.
if not "%~1"=="" (
    for %%I in ("%~1") do set "SQL_FILE=%%~fI"
) else (
    for /f "delims=" %%F in ('dir /b /a-d /o-d "%BACKUP_DIR%\diaries-development-*.sql" 2^>nul') do (
        if not defined SQL_FILE set "SQL_FILE=%BACKUP_DIR%\%%F"
    )
)

if not defined SQL_FILE (
    echo No database SQL backup files were found in:
    echo %BACKUP_DIR%
    popd
    exit /b 1
)

if not exist "%SQL_FILE%" (
    echo Database SQL backup file not found:
    echo %SQL_FILE%
    popd
    exit /b 1
)

for %%F in ("%SQL_FILE%") do set "SQL_SIZE=%%~zF"
if "%SQL_SIZE%"=="0" (
    echo Database SQL backup file is empty:
    echo %SQL_FILE%
    popd
    exit /b 1
)

rem A plain-text dump created by pg_dump contains this standard header. This
rem catches common mistakes, such as selecting a custom-format .dump file.
findstr /c:"PostgreSQL database dump" "%SQL_FILE%" >nul
if errorlevel 1 (
    echo The selected file does not appear to be a PostgreSQL plain SQL dump:
    echo %SQL_FILE%
    popd
    exit /b 1
)

rem Check that the PostgreSQL service is available before replacing the
rem database.
docker compose -f "%COMPOSE_FILE%" exec -T diaries-db pg_isready ^
    --username "%DIARIES_DB_USERNAME%" ^
    --dbname postgres >nul 2>&1
if errorlevel 1 (
    echo The day-to-day-development database is not ready.
    echo Start it before running this restore script.
    popd
    exit /b 1
)

echo.
echo WARNING: This will completely replace the day-to-day-development database.
echo.
echo Database: %DIARIES_DB_NAME%
echo SQL file: %SQL_FILE%
echo.
echo Stop the locally running Diaries responder before continuing so that it
echo cannot reconnect while the database is being dropped and recreated.
echo.
set "CONFIRM="
set /p "CONFIRM=Type RESTORE to continue: "
if /i not "%CONFIRM%"=="RESTORE" (
    echo Restore cancelled.
    popd
    exit /b 1
)

echo.
echo Dropping the existing database...
docker compose -f "%COMPOSE_FILE%" exec -T diaries-db dropdb ^
    --force ^
    --if-exists ^
    --username "%DIARIES_DB_USERNAME%" ^
    "%DIARIES_DB_NAME%"
if errorlevel 1 goto :restore_failed

echo Creating a new empty database...
docker compose -f "%COMPOSE_FILE%" exec -T diaries-db createdb ^
    --username "%DIARIES_DB_USERNAME%" ^
    --owner "%DIARIES_DB_USERNAME%" ^
    "%DIARIES_DB_NAME%"
if errorlevel 1 goto :restore_failed

echo Restoring the SQL backup...
docker compose -f "%COMPOSE_FILE%" exec -T diaries-db psql ^
    --set ON_ERROR_STOP=on ^
    --username "%DIARIES_DB_USERNAME%" ^
    --dbname "%DIARIES_DB_NAME%" < "%SQL_FILE%"
if errorlevel 1 goto :restore_failed

echo.
echo Database restore completed successfully.
echo Database: %DIARIES_DB_NAME%
echo Source:   %SQL_FILE%
popd
endlocal & exit /b 0

:restore_failed
set "EXIT_CODE=%ERRORLEVEL%"
echo.
echo Database restore failed with exit code %EXIT_CODE%.
echo The original database has already been removed and may now be empty or
echo only partially restored. Correct the problem and run this script again.
popd
endlocal & exit /b %EXIT_CODE%
