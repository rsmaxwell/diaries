@echo off
setlocal

rem This script is located under:
rem   diaries\scripts\windows\development-infrastructure
rem
rem The Diaries project root is therefore two directories above this script.
set "SCRIPT_DIR=%~dp0"
set "PROJECT_DIR=%SCRIPT_DIR%..\.."

rem Change to the project root and replace PROJECT_DIR with its clean,
rem fully qualified path.
pushd "%PROJECT_DIR%" || (
    echo Failed to change working directory to "%PROJECT_DIR%".
    exit /b 1
)
set "PROJECT_DIR=%CD%"

rem Derive the compose file the project root.
set "COMPOSE_FILE=%PROJECT_DIR%\compose.development.yaml"

if not exist "%COMPOSE_FILE%" (
    echo Compose file not found: "%COMPOSE_FILE%"
    popd
    exit /b 1
)


rem Run Docker Compose from the project root and explicitly use the
rem development-infrastructure Compose definition.
@echo on
docker compose -f "%COMPOSE_FILE%" up -d diaries-db
@echo off

set "EXIT_CODE=%ERRORLEVEL%"
popd
endlocal & exit /b %EXIT_CODE%
