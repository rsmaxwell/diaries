@echo off
setlocal

rem ============================================================================
rem pull.bat
rem
rem Pull the published Diaries images selected for local-published-smoke mode.
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
rem     diaries\scripts\windows\local-published-smoke
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
rem Define and validate the Compose file for local-published-smoke mode.
rem ----------------------------------------------------------------------------

set "COMPOSE_FILE=%PROJECT_DIR%\compose.local-published-smoke.yaml"

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
rem local.env take precedence over values in local-published-smoke.env.
rem ----------------------------------------------------------------------------

set "ENV_FILE=%PROJECT_DIR%\config\environments\local-published-smoke.env"

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
rem Apply optional local image-tag overrides.
rem
rem set-env.bat is intentionally separate from the two Compose environment
rem files. It is used only to select local published image tags without editing
rem committed configuration.
rem ----------------------------------------------------------------------------

if exist "%SCRIPT_DIR%set-env.bat" (
    call "%SCRIPT_DIR%set-env.bat"
    if errorlevel 1 (
        echo ERROR: Could not load local image-tag overrides. >&2
        set "EXIT_CODE=1"
        goto :cleanup
    )
)


rem ----------------------------------------------------------------------------
rem Resolve the effective published image tags.
rem
rem Precedence for the client:
rem   DIARIES_CLIENT_IMAGE_TAG
rem   DIARIES_IMAGE_TAG
rem   integration
rem
rem Precedence for the responder:
rem   DIARIES_RESPONDER_IMAGE_TAG
rem   DIARIES_IMAGE_TAG
rem   integration
rem ----------------------------------------------------------------------------

if defined DIARIES_CLIENT_IMAGE_TAG (
    set "EFFECTIVE_CLIENT_IMAGE_TAG=%DIARIES_CLIENT_IMAGE_TAG%"
) else if defined DIARIES_IMAGE_TAG (
    set "EFFECTIVE_CLIENT_IMAGE_TAG=%DIARIES_IMAGE_TAG%"
) else (
    set "EFFECTIVE_CLIENT_IMAGE_TAG=integration"
)

if defined DIARIES_RESPONDER_IMAGE_TAG (
    set "EFFECTIVE_RESPONDER_IMAGE_TAG=%DIARIES_RESPONDER_IMAGE_TAG%"
) else if defined DIARIES_IMAGE_TAG (
    set "EFFECTIVE_RESPONDER_IMAGE_TAG=%DIARIES_IMAGE_TAG%"
) else (
    set "EFFECTIVE_RESPONDER_IMAGE_TAG=integration"
)


rem ----------------------------------------------------------------------------
rem Report the published images that will be pulled.
rem ----------------------------------------------------------------------------

echo Pulling Diaries published images.
echo   Client image:    rsmaxwell/diaries-client:%EFFECTIVE_CLIENT_IMAGE_TAG%
echo   Responder image: rsmaxwell/diaries-responder:%EFFECTIVE_RESPONDER_IMAGE_TAG%
echo.


rem ----------------------------------------------------------------------------
rem Validate the resolved Docker Compose configuration.
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
rem Pull the selected images.
rem ----------------------------------------------------------------------------

docker compose ^
    -f "%COMPOSE_FILE%" ^
    --env-file "%ENV_FILE%" ^
    --env-file "%LOCAL_ENV_FILE%" ^
    pull

set "EXIT_CODE=%ERRORLEVEL%"

if not "%EXIT_CODE%"=="0" (
    echo ERROR: Failed to pull one or more Diaries images. >&2
    goto :cleanup
)

echo.
echo Diaries published images pulled successfully.

rem ----------------------------------------------------------------------------
rem Common cleanup and exit.
rem ----------------------------------------------------------------------------

:cleanup
popd
endlocal & exit /b %EXIT_CODE%
