@echo off
setlocal

rem Capture non-destructive 0031 Step 11 runtime-path evidence for one local mode.
rem The requested mode must already be running. Production must remain frozen.
rem This wrapper validates the database/Files pair before the PowerShell evidence
rem collector is invoked.

set "MODE=%~1"
if not defined MODE goto :usage

if /I not "%~2"=="-ProductionWriteFreezeConfirmed" (
    echo ERROR: Step 11 requires explicit confirmation that the production responder write freeze remains active. >&2
    goto :usage
)

set "RESPONDER_LOG=%~3"

set "SCRIPT_DIR=%~dp0"
pushd "%SCRIPT_DIR%..\..\.." >nul 2>&1
if errorlevel 1 (
    echo ERROR: Could not locate the Diaries project root. >&2
    exit /b 1
)
set "PROJECT_DIR=%CD%"
set "ENV_FILE=%PROJECT_DIR%\config\environments\%MODE%.env"
set "LOCAL_ENV_FILE=%PROJECT_DIR%\config\environments\local.env"
set "PAIR_GUARD=%PROJECT_DIR%\scripts\windows\common\validate-dataset-pair.bat"
set "COLLECTOR=%PROJECT_DIR%\scripts\windows\0031-step11\capture-local-mode.ps1"

if not exist "%ENV_FILE%" (
    echo ERROR: Unknown mode or environment file not found: "%ENV_FILE%" >&2
    popd
    exit /b 2
)
if not exist "%LOCAL_ENV_FILE%" (
    echo ERROR: Local environment file not found: "%LOCAL_ENV_FILE%" >&2
    echo Copy config\environments\local.env.example to local.env and customise it. >&2
    popd
    exit /b 1
)

call "%PAIR_GUARD%" "%MODE%" "%ENV_FILE%" "%LOCAL_ENV_FILE%"
if errorlevel 1 (
    popd
    exit /b 1
)

if not defined RESPONDER_LOG (
    powershell -NoProfile -ExecutionPolicy Bypass -File "%COLLECTOR%" -Mode "%MODE%" -ProjectDir "%PROJECT_DIR%"
) else (
    powershell -NoProfile -ExecutionPolicy Bypass -File "%COLLECTOR%" -Mode "%MODE%" -ProjectDir "%PROJECT_DIR%" -ResponderLog "%RESPONDER_LOG%"
)
set "EXIT_CODE=%ERRORLEVEL%"

popd
endlocal & exit /b %EXIT_CODE%

:usage
echo Usage: capture-local-mode.bat MODE -ProductionWriteFreezeConfirmed [ResponderLog] >&2
echo Modes: development-infrastructure, local-docker-build, local-published-smoke >&2
endlocal & exit /b 2
