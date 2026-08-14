@echo off
setlocal

set "SCRIPT_DIR=%~dp0"
set "EXIT_CODE=0"

pushd "%SCRIPT_DIR%..\..\.." >nul 2>&1
if errorlevel 1 (
    echo ERROR: Could not locate the Diaries project root. >&2
    echo Script directory: "%SCRIPT_DIR%" >&2
    endlocal & exit /b 1
)
set "PROJECT_DIR=%CD%"

set "COMPOSE_FILE=%PROJECT_DIR%\compose.local-published-smoke.yaml"
if not exist "%COMPOSE_FILE%" (
    echo Compose file not found: "%COMPOSE_FILE%"
    set "EXIT_CODE=1"
    goto :cleanup
)

set "ENV_FILE=%PROJECT_DIR%\config\environments\local-published-smoke.env"
if not exist "%ENV_FILE%" (
    echo Environment file not found: "%ENV_FILE%"
    set "EXIT_CODE=1"
    goto :cleanup
)

call "%PROJECT_DIR%\scripts\windows\common\load-dotenv.bat"
if errorlevel 1 (
    set "EXIT_CODE=1"
    goto :cleanup
)

if exist "%SCRIPT_DIR%set-env.bat" (
    call "%SCRIPT_DIR%set-env.bat"
    if errorlevel 1 (
        set "EXIT_CODE=1"
        goto :cleanup
    )
)

rem -----------------------------------------------------------------
rem Resolve the effective image tags.
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
rem -----------------------------------------------------------------

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

echo Starting local published-image smoke-test stack
echo   Client image tag:    %EFFECTIVE_CLIENT_IMAGE_TAG%
echo   Responder image tag: %EFFECTIVE_RESPONDER_IMAGE_TAG%
echo.







docker compose ^
    --env-file "%ENV_FILE%" ^
    -f "%COMPOSE_FILE%" ^
    config --quiet
if errorlevel 1 (
    echo ERROR: Docker Compose configuration is invalid.
    set "EXIT_CODE=1"
    goto :cleanup
)




docker compose ^
    --env-file "%ENV_FILE%" ^
    -f "%COMPOSE_FILE%" ^
    pull

set "EXIT_CODE=%ERRORLEVEL%"



:cleanup
popd
endlocal & exit /b %EXIT_CODE%
