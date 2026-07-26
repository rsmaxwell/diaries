@echo off
setlocal EnableExtensions EnableDelayedExpansion

rem Test the Diaries responder HTTP interface used by the local Docker build.
rem
rem Unlike ledger-server, diaries-responder does not expose a conventional
rem REST API. Its HTTP server provides the static /diaries and /files contexts;
rem the application's RPC operations are carried over MQTT.

rem Locate the Diaries project directory from this script:
rem scripts\windows\development-infrastructure\test-responder-api.bat
set "SCRIPT_DIR=%~dp0"
pushd "%SCRIPT_DIR%..\..\.." >nul
if errorlevel 1 (
    echo Unable to locate the Diaries project directory.
    exit /b 1
)
set "PROJECT_DIR=%CD%"

rem Existing environment variables take precedence. This default matches the
rem responder port used by the Diaries development and local Docker modes.
if not defined DIARIES_RESPONDER_PORT set "DIARIES_RESPONDER_PORT=8081"
set "RESPONDER_URL=http://localhost:%DIARIES_RESPONDER_PORT%"

where curl.exe >nul 2>&1
if errorlevel 1 (
    echo curl.exe was not found on PATH.
    popd
    exit /b 1
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
    popd
    endlocal & exit /b 1
)

echo Diaries responder HTTP test passed.
echo.
echo Note: business API operations use MQTT RPC and are not exercised by this
echo HTTP-only test.

popd
endlocal & exit /b 0

:expect_status
set "METHOD=%~1"
set "URL=%~2"
set "EXPECTED=%~3"
set "DESCRIPTION=%~4"
set "STATUS="

for /f "usebackq delims=" %%S in (`curl.exe --silent --show-error --output nul --write-out "%%{http_code}" --request "%METHOD%" --max-time 10 "%URL%" 2^>nul`) do set "STATUS=%%S"

if not defined STATUS set "STATUS=000"

if "%STATUS%"=="%EXPECTED%" (
    echo OK %EXPECTED%: %DESCRIPTION% - %METHOD% %URL%
) else (
    echo FAILED: %DESCRIPTION% - %METHOD% %URL%
    echo          expected HTTP %EXPECTED%, received HTTP %STATUS%
    set /a FAILURES+=1
)
exit /b 0
