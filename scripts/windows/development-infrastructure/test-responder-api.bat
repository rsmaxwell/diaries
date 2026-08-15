@echo off
setlocal EnableExtensions EnableDelayedExpansion

rem Test the Diaries responder HTTP interface used by the local Docker build.
rem
rem Unlike ledger-server, diaries-responder does not expose a conventional
rem REST API. Its HTTP server provides the static /diaries and /files contexts;
rem the application's RPC operations are carried over MQTT.

rem Locate the Diaries project directory from this script:
rem scripts\windows\development-infrastructure\test-responder-api.bat
set "EXIT_CODE=0"

set "SCRIPT_DIR=%~dp0"
pushd "%SCRIPT_DIR%..\..\.." >nul 2>&1
if errorlevel 1 (
    echo ERROR: Could not locate the project directory. >&2
    endlocal & exit /b 1
)

set "PROJECT_DIR=%CD%"

set "ENV_FILE=%PROJECT_DIR%\config\environments\development-infrastructure.env"
if not exist "%ENV_FILE%" (
    echo Environment file not found: "%ENV_FILE%"
    set "EXIT_CODE=1"
    goto :cleanup
)

set "LOCAL_ENV_FILE=%PROJECT_DIR%\config\environments\local.env"
if not exist "%LOCAL_ENV_FILE%" (
    echo Environment file not found: "%LOCAL_ENV_FILE%"
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
    set "EXIT_CODE=1"
    goto :cleanup
)

if not defined DIARIES_RESPONDER_PORT set "DIARIES_RESPONDER_PORT=8081"
set "RESPONDER_URL=http://localhost:%DIARIES_RESPONDER_PORT%"







where curl.exe >nul 2>&1
if errorlevel 1 (
    echo curl.exe was not found on PATH.
    set "EXIT_CODE=1"
    goto :cleanup
)

echo Testing Diaries responder HTTP interface at:
echo %RESPONDER_URL%
echo.

set "FAILURES=0"

rem The directories may be empty, so a GET of the context itself normally
rem returns 404. Receiving that response proves that the responder HTTP server
rem is reachable and that the expected context has been registered.
call :expect_status GET "%RESPONDER_URL%/diaries" 404 "diaries context"
call :expect_status GET "%RESPONDER_URL%/files" 404 "files context"

rem Static-file contexts accept only GET and HEAD. POST must be rejected with
rem HTTP 405 Method Not Allowed.
call :expect_status POST "%RESPONDER_URL%/diaries" 405 "diaries method handling"
call :expect_status POST "%RESPONDER_URL%/files" 405 "files method handling"

rem An unknown path should not be served by either static-file context.
call :expect_status GET "%RESPONDER_URL%/not-a-responder-path" 404 "unknown path handling"

echo.
if not "%FAILURES%"=="0" (
    echo Diaries responder HTTP test failed: %FAILURES% check^(s^) failed.
    echo Check that diaries-responder is running and listening on port %DIARIES_RESPONDER_PORT%.
    set "EXIT_CODE=1"
    goto :cleanup
)

echo Diaries responder HTTP test passed.
echo.
echo Note: business API operations use MQTT RPC and are not exercised by this
echo HTTP-only test.

set "EXIT_CODE=0"
goto :cleanup

:expect_status
set "METHOD=%~1"
set "URL=%~2"
set "EXPECTED=%~3"
set "DESCRIPTION=%~4"
set "STATUS="


for /f "usebackq delims=" %%S in (`
    curl.exe --silent --show-error --output nul --write-out "%%{http_code}" --request "%METHOD%" --max-time 10 "%URL%" 2^>nul
`) do set "STATUS=%%S"


if not defined STATUS set "STATUS=000"

if "%STATUS%"=="%EXPECTED%" (
    echo OK %EXPECTED%: %DESCRIPTION% - %METHOD% %URL%
) else (
    echo FAILED: %DESCRIPTION% - %METHOD% %URL%
    echo          expected HTTP %EXPECTED%, received HTTP %STATUS%
    set /a FAILURES+=1
)

exit /b 0




:cleanup
popd
endlocal & exit /b %EXIT_CODE%
