@echo off
setlocal

rem ============================================================================
rem logs.bat
rem
rem Follow logs from the Diaries Docker Compose stack in local-docker-build mode.
rem
rem Usage:
rem
rem     logs.bat
rem     logs.bat <service> [<service> ...]
rem
rem Service names are Docker Compose service names, for example:
rem
rem     logs.bat diaries-responder
rem
rem Do not use container names such as diaries-local-responder.
rem ============================================================================


rem ----------------------------------------------------------------------------
rem Initialise common script variables.
rem ----------------------------------------------------------------------------

set "SCRIPT_DIR=%~dp0"
set "EXIT_CODE=0"


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
rem Define and validate the Compose file for local-docker-build mode.
rem ----------------------------------------------------------------------------

set "COMPOSE_FILE=%PROJECT_DIR%\compose.local-docker-build.yaml"

if not exist "%COMPOSE_FILE%" (
    echo ERROR: Compose file not found: "%COMPOSE_FILE%" >&2
    set "EXIT_CODE=1"
    goto :cleanup
)


rem ----------------------------------------------------------------------------
rem Define and validate the environment files for local-docker-build mode.
rem ----------------------------------------------------------------------------

set "ENV_FILE=%PROJECT_DIR%\config\environments\local-docker-build.env"
if not exist "%ENV_FILE%" (
    echo ERROR: Environment file not found: "%ENV_FILE%" >&2
    set "EXIT_CODE=1"
    goto :cleanup
)

set "LOCAL_ENV_FILE=%PROJECT_DIR%\config\environments\local.env"
if not exist "%LOCAL_ENV_FILE%" (
    echo ERROR: Local environment file not found: "%LOCAL_ENV_FILE%" >&2
    set "EXIT_CODE=1"
    goto :cleanup
)


rem ----------------------------------------------------------------------------
rem Load both environment files into the current batch process.
rem
rem Load local-docker-build.env first and local.env second so that machine-local
rem values override the committed mode defaults.
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


rem ----------------------------------------------------------------------------
rem Follow logs for the whole stack or for the requested Compose services.
rem
rem Both environment files are supplied to Compose in the same precedence order
rem as above. Any command-line arguments are treated as Compose service names.
rem ----------------------------------------------------------------------------

if "%~1"=="" (
    docker compose ^
        --env-file "%ENV_FILE%" ^
        --env-file "%LOCAL_ENV_FILE%" ^
        -f "%COMPOSE_FILE%" ^
        logs -f
) else (
    docker compose ^
        --env-file "%ENV_FILE%" ^
        --env-file "%LOCAL_ENV_FILE%" ^
        -f "%COMPOSE_FILE%" ^
        logs -f %*
)

set "EXIT_CODE=%ERRORLEVEL%"

if not "%EXIT_CODE%"=="0" (
    echo ERROR: Failed to read Diaries local-docker-build logs. >&2
    goto :cleanup
)


rem ----------------------------------------------------------------------------
rem Common cleanup and exit.
rem ----------------------------------------------------------------------------

:cleanup
popd
endlocal & exit /b %EXIT_CODE%
