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




if not defined DIARIES_IMAGE_TAG set "DIARIES_IMAGE_TAG=integration"

echo Showing local published-image smoke-test stack status
echo   DIARIES_IMAGE_TAG=%DIARIES_IMAGE_TAG%
echo.



set "COMPOSE_FILE=%PROJECT_DIR%\compose.dockerhub.yaml"

if not exist "%COMPOSE_FILE%" (
    echo Compose file not found: "%COMPOSE_FILE%"
    set "EXIT_CODE=1"
    goto :cleanup
)




echo on
docker compose -f "%COMPOSE_FILE%" ps --all
echo off

set "EXIT_CODE=%ERRORLEVEL%"



:cleanup
popd
endlocal & exit /b %EXIT_CODE%
