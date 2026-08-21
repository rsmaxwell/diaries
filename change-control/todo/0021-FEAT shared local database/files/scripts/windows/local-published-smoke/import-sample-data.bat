@echo off
setlocal

set "SCRIPT_DIR=%~dp0"

pushd "%SCRIPT_DIR%..\..\.." || exit /b 1
set "PROJECT_DIR=%CD%"
set "EXIT_CODE=0"



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




call "%PROJECT_DIR%\scripts\windows\common\load-dotenv.bat" "%ENV_FILE%"
if errorlevel 1 (
    set "EXIT_CODE=1"
    goto :cleanup
)

call "%PROJECT_DIR%\scripts\windows\common\load-dotenv.bat" "%LOCAL_ENV_FILE%"
if errorlevel 1 (
    set "EXIT_CODE=%ERRORLEVEL%"
    goto :cleanup
)

if exist "%SCRIPT_DIR%set-env.bat" (
    call "%SCRIPT_DIR%set-env.bat"
    if errorlevel 1 (
        set "EXIT_CODE=1"
        goto :cleanup
    )
)




if "%LEDGER_SERVER_URL%"=="" (
    if not "%LEDGER_SERVER_PORT%"=="" (
        set "LEDGER_SERVER_URL=http://localhost:%LEDGER_SERVER_PORT%"
    ) else (
        set "LEDGER_SERVER_URL=http://localhost:8080"
    )
)




call "%PROJECT_DIR%\ledger-server\scripts\windows\common\login.bat"

if errorlevel 1 (
        set "EXIT_CODE=1"
        goto :cleanup
)





set "TEST_SCRIPT=%PROJECT_DIR%\ledger-server\scripts\windows\common\import-sample-data.bat"
if not exist "%TEST_SCRIPT%" (
    echo ERROR: test script not found: >&2
    echo "%TEST_SCRIPT%" >&2
    set "EXIT_CODE=1"
    goto :cleanup
)


@echo on
call "%TEST_SCRIPT%"
@echo off
set "EXIT_CODE=%ERRORLEVEL%"

:cleanup
popd
endlocal & exit /b %EXIT_CODE%
