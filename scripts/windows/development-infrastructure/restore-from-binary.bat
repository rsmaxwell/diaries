@echo off
setlocal EnableExtensions

rem Locate the Diaries project directory from this script:
rem scripts\windows\development-infrastructure\restore-from-binary.bat
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

set "BACKUP_DIR=%PROJECT_DIR%\data\database-backups\development-infrastructure"
if not exist "%BACKUP_DIR%" (
    echo Backup directory not found: "%BACKUP_DIR%"
    set "EXIT_CODE=1"
    goto :cleanup
)

call "%PROJECT_DIR%\scripts\windows\common\load-dotenv.bat" "%ENV_FILE%"
if errorlevel 1 (
    set "EXIT_CODE=1"
    goto :cleanup
)

if not defined DIARIES_DB_NAME set "DIARIES_DB_NAME=diaries"
if not defined DIARIES_DB_USERNAME set "DIARIES_DB_USERNAME=diaries"



rem A dump file may be supplied as the first argument. Otherwise restore the
rem newest standard development backup from the normal backup directory.
if not "%~1"=="" (
    for %%I in ("%~1") do set "DUMP_FILE=%%~fI"
) else (
    for /f "delims=" %%F in ('dir /b /a-d /o-d "%BACKUP_DIR%\diaries-development-*.dump" 2^>nul') do (
        if not defined DUMP_FILE set "DUMP_FILE=%BACKUP_DIR%\%%F"
    )
)

if not defined DUMP_FILE (
    echo No database dump files were found in:
    echo %BACKUP_DIR%
    set "EXIT_CODE=1"
    goto :cleanup
)

if not exist "%DUMP_FILE%" (
    echo Database dump file not found:
    echo %DUMP_FILE%
    set "EXIT_CODE=1"
    goto :cleanup
)

for %%F in ("%DUMP_FILE%") do set "DUMP_SIZE=%%~zF"
if "%DUMP_SIZE%"=="0" (
    echo Database dump file is empty:
    echo %DUMP_FILE%
    set "EXIT_CODE=1"
    goto :cleanup
)

rem Check that the PostgreSQL service is available before validating or
rem replacing the database.
docker compose ^
    --env-file "%ENV_FILE%" ^
    -f "%COMPOSE_FILE%" ^
    exec -T diaries-db pg_isready ^
    --username "%DIARIES_DB_USERNAME%" ^
    --dbname postgres >nul 2>&1
if errorlevel 1 (
    echo The development-infrastructure database is not ready.
    echo Start it before running this restore script.
    set "EXIT_CODE=1"
    goto :cleanup
)

echo Validating database dump...
docker compose ^
    --env-file "%ENV_FILE%" ^
    -f "%COMPOSE_FILE%" ^
    exec -T diaries-db pg_restore --list < "%DUMP_FILE%" >nul
if errorlevel 1 (
    echo.
    echo The selected file is not a valid PostgreSQL custom-format dump:
    echo %DUMP_FILE%
    set "EXIT_CODE=1"
    goto :cleanup
)

echo.
echo WARNING: This will completely replace the development-infrastructure database.
echo.
echo Database: %DIARIES_DB_NAME%
echo Dump:     %DUMP_FILE%
echo.
echo Stop the locally running Diaries responder before continuing so that it
echo cannot reconnect while the database is being dropped and recreated.
echo.
set "CONFIRM="
set /p "CONFIRM=Type RESTORE to continue: "
if /i not "%CONFIRM%"=="RESTORE" (
    echo Restore cancelled.
    set "EXIT_CODE=1"
    goto :cleanup
)

echo.
echo Dropping the existing database...
docker compose ^
    --env-file "%ENV_FILE%" ^
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
    -f "%COMPOSE_FILE%" ^
    exec -T diaries-db createdb ^
    --username "%DIARIES_DB_USERNAME%" ^
    --owner "%DIARIES_DB_USERNAME%" ^
    "%DIARIES_DB_NAME%"
if errorlevel 1 (
    set "EXIT_CODE=%ERRORLEVEL%"
    goto :restore_failed
)

echo Restoring the database dump...
docker compose ^
    --env-file "%ENV_FILE%" ^
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

echo.
echo Database restore completed successfully.
echo Database: %DIARIES_DB_NAME%
echo Source:   %DUMP_FILE%
set "EXIT_CODE=0"
goto :cleanup

:restore_failed
echo.
echo Database restore failed with exit code %EXIT_CODE%.
echo The original database has already been removed and may now be empty or
echo only partially restored. Correct the problem and run this script again.


:cleanup
popd
endlocal & exit /b %EXIT_CODE%
