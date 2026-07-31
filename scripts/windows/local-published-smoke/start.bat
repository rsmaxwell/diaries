@echo off
setlocal

set "SCRIPT_DIR=%~dp0"

pushd "%SCRIPT_DIR%..\..\.." || exit /b 1
set "PROJECT_DIR=%CD%"
set "EXIT_CODE=0"

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
echo   Client image:    rsmaxwell/diaries-client:%EFFECTIVE_CLIENT_IMAGE_TAG%
echo   Responder image: rsmaxwell/diaries-responder:%EFFECTIVE_RESPONDER_IMAGE_TAG%
echo.



set "COMPOSE_PROJECT_NAME=diaries-local-published-smoke"
set "COMPOSE_FILE=%PROJECT_DIR%\compose.dockerhub.yaml"

if not exist "%COMPOSE_FILE%" (
    echo Compose file not found: "%COMPOSE_FILE%"
    set "EXIT_CODE=1"
    goto :cleanup
)

docker compose -f "%COMPOSE_FILE%" config --quiet
if errorlevel 1 (
    echo ERROR: Docker Compose configuration is invalid.
    set "EXIT_CODE=1"
    goto :cleanup
)

echo on
docker compose -f "%COMPOSE_FILE%" pull
@echo off

if errorlevel 1 (
    set "EXIT_CODE=1"
    goto :cleanup
)

echo on
docker compose ^
  -p "%COMPOSE_PROJECT_NAME%" ^
  -f "%COMPOSE_FILE%" ^
  up -d --remove-orphans --wait --wait-timeout 120
echo off

set "EXIT_CODE=%ERRORLEVEL%"

:cleanup
popd
endlocal & exit /b %EXIT_CODE%
