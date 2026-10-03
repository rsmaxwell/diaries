@echo off
setlocal

rem Validate the 0031 durable-dataset invariant before a local mode starts.
rem
rem Usage:
rem   call validate-dataset-pair.bat MODE MODE_ENV LOCAL_ENV
rem
rem The PowerShell helper rejects one-sided local.env overrides and the known
rem invalid local/production or database/Files pairings from the frozen Step 2
rem configuration contract.

if "%~3"=="" (
    echo ERROR: validate-dataset-pair.bat requires MODE, MODE_ENV and LOCAL_ENV. >&2
    echo Usage: call validate-dataset-pair.bat MODE MODE_ENV LOCAL_ENV >&2
    exit /b 2
)

set "SCRIPT_DIR=%~dp0"
set "VALIDATOR=%SCRIPT_DIR%validate-dataset-pair.ps1"

if not exist "%VALIDATOR%" (
    echo ERROR: Dataset-pair validator not found: "%VALIDATOR%" >&2
    exit /b 1
)

powershell -NoProfile -ExecutionPolicy Bypass -File "%VALIDATOR%" ^
    -ModeName "%~1" ^
    -ModeEnvironmentFile "%~2" ^
    -LocalEnvironmentFile "%~3"

exit /b %ERRORLEVEL%
