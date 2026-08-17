@echo off
setlocal EnableExtensions

rem ============================================================================
rem shell-prompt-database.bat
rem
rem Open an interactive shell inside the PostgreSQL container used by
rem local-docker-build mode.
rem
rem The script:
rem   - locates the Diaries project root;
rem   - validates and loads the mode and machine-local environment files;
rem   - validates the resolved Compose configuration;
rem   - opens an interactive shell in the running diaries-db service.
rem
rem Typical commands after entering the container include:
rem
rem     psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"
rem     ls -l /var/lib/postgresql/data
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
rem Define and validate the two environment files.
rem
rem ENV_FILE contains committed mode-specific defaults.
rem LOCAL_ENV_FILE contains machine-specific settings and overrides.
rem
rem The mode environment is applied first and local.env second, so values in
rem local.env take precedence over values in local-docker-build.env.
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
    echo Copy local.env.example to local.env and configure this machine. >&2
    set "EXIT_CODE=1"
    goto :cleanup
)


rem ----------------------------------------------------------------------------
rem Load both environment files into the current batch process.
rem
rem Load the mode-specific environment first, followed by local.env so that
rem machine-specific values override the committed mode defaults.
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
rem Validate the resolved Docker Compose configuration.
rem
rem Both environment files are supplied in the same order in which they were
rem loaded above. Values in local.env therefore override the committed mode
rem defaults.
rem ----------------------------------------------------------------------------

docker compose ^
    -f "%COMPOSE_FILE%" ^
    --env-file "%ENV_FILE%" ^
    --env-file "%LOCAL_ENV_FILE%" ^
    config --quiet

set "EXIT_CODE=%ERRORLEVEL%"

if not "%EXIT_CODE%"=="0" (
    echo ERROR: Docker Compose configuration validation failed. >&2
    goto :cleanup
)


rem ----------------------------------------------------------------------------
rem Open an interactive shell in the running PostgreSQL container.
rem ----------------------------------------------------------------------------

echo Opening shell in the Diaries local-docker-build PostgreSQL container...
echo Type "exit" to return to this command prompt.
echo.

docker compose ^
    -f "%COMPOSE_FILE%" ^
    --env-file "%ENV_FILE%" ^
    --env-file "%LOCAL_ENV_FILE%" ^
    exec diaries-db sh

set "EXIT_CODE=%ERRORLEVEL%"

if not "%EXIT_CODE%"=="0" (
    echo ERROR: Failed to open a shell in the PostgreSQL container. >&2
    goto :cleanup
)


rem ----------------------------------------------------------------------------
rem Common cleanup and exit.
rem ----------------------------------------------------------------------------

:cleanup
popd
endlocal & exit /b %EXIT_CODE%
