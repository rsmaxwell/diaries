@echo off
setlocal

rem Reset the PostgreSQL database used by development-infrastructure mode.
rem
rem All local modes may share DIARIES_DB_DATA_DIR through local.env. Therefore
rem this reset deletes the resolved bind-mounted PostgreSQL data directory, not
rem a Docker named volume. If local.env points all modes at the common directory,
rem this resets the database for all three local modes.

set "EXIT_CODE=0"
set "SCRIPT_DIR=%~dp0"

rem This script is located under:
rem diaries\scripts\windows\development-infrastructure
rem Therefore, the Diaries project root is three directories above it.
pushd "%SCRIPT_DIR%..\..\.." >nul 2>&1
if errorlevel 1 (
    echo ERROR: Could not locate the Diaries project root. >&2
    echo Script directory: "%SCRIPT_DIR%" >&2
    endlocal & exit /b 1
)
set "PROJECT_DIR=%CD%"

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
    echo Copy config\environments\local.env.example to local.env and customise it. >&2
    set "EXIT_CODE=1"
    goto :cleanup
)

call "%PROJECT_DIR%\scripts\windows\common\load-dotenv.bat" "%ENV_FILE%"
if errorlevel 1 (
    set "EXIT_CODE=%ERRORLEVEL%"
    goto :cleanup
)

call "%PROJECT_DIR%\scripts\windows\common\load-dotenv.bat" "%LOCAL_ENV_FILE%"
if errorlevel 1 (
    set "EXIT_CODE=%ERRORLEVEL%"
    goto :cleanup
)

if not defined DIARIES_DB_DATA_DIR (
    echo ERROR: DIARIES_DB_DATA_DIR is not set. >&2
    set "EXIT_CODE=1"
    goto :cleanup
)

for %%I in ("%DIARIES_DB_DATA_DIR%") do set "DB_DATA_DIR=%%~fI"

echo.
echo This will:
echo   1. Stop the development infrastructure.
echo   2. DELETE the PostgreSQL data directory:
echo      "%DB_DATA_DIR%"
echo   3. Start a new empty PostgreSQL database.
echo.
echo WARNING: If this is the shared common directory, the database used by all
echo          three local Diaries modes will be deleted.
echo.
set "ANSWER="
set /p "ANSWER=Type RESET to continue: "

if /I not "%ANSWER%"=="RESET" (
    echo Database reset cancelled.
    goto :cleanup
)

@echo on
docker compose ^
    -f "%COMPOSE_FILE%" ^
    --env-file "%ENV_FILE%" ^
    --env-file "%LOCAL_ENV_FILE%" ^
    down --remove-orphans
@echo off

if errorlevel 1 (
    set "EXIT_CODE=%ERRORLEVEL%"
    goto :cleanup
)

if exist "%DB_DATA_DIR%" (
    echo Deleting PostgreSQL data directory: "%DB_DATA_DIR%"
    rmdir /s /q "%DB_DATA_DIR%"
    if errorlevel 1 (
        echo ERROR: Failed to delete PostgreSQL data directory. >&2
        set "EXIT_CODE=1"
        goto :cleanup
    )
)

mkdir "%DB_DATA_DIR%" >nul 2>&1
if errorlevel 1 (
    echo ERROR: Failed to create PostgreSQL data directory: "%DB_DATA_DIR%" >&2
    set "EXIT_CODE=1"
    goto :cleanup
)

@echo on
docker compose ^
    -f "%COMPOSE_FILE%" ^
    --env-file "%ENV_FILE%" ^
    --env-file "%LOCAL_ENV_FILE%" ^
    up -d --wait --wait-timeout 120
@echo off

set "EXIT_CODE=%ERRORLEVEL%"
if not "%EXIT_CODE%"=="0" goto :cleanup

echo.
echo Diaries database reset successfully.

:cleanup
popd
endlocal & exit /b %EXIT_CODE%
