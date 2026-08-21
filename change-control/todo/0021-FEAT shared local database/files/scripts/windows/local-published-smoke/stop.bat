@echo off
setlocal

set "SCRIPT_DIR=%~dp0"

pushd "%SCRIPT_DIR%..\..\.." || exit /b 1
set "PROJECT_DIR=%CD%"
set "EXIT_CODE=0"


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

set "LOCAL_ENV_FILE=%PROJECT_DIR%\config\environments\local.env"
if not exist "%LOCAL_ENV_FILE%" (
    echo ERROR: Local environment file not found: >&2
    echo "%LOCAL_ENV_FILE%" >&2
    echo Copy config\environments\local.env.example to local.env and customise it. >&2
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






echo on
docker compose ^
    --env-file "%ENV_FILE%" --env-file "%LOCAL_ENV_FILE%" ^
    -f "%COMPOSE_FILE%" ^
    down
@echo off

set "EXIT_CODE=%ERRORLEVEL%"


:cleanup
popd
endlocal & exit /b %EXIT_CODE%
