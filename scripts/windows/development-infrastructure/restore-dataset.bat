@echo off
setlocal EnableExtensions

rem 0033-FEAT complete-dataset restore entry point for development-infrastructure.
rem 0033-FEAT Steps 5/6/7: preflight, prepare, controlled apply/rollback and postflight acceptance.
rem Usage:
rem   restore-dataset.bat preflight ^<backup-id-or-directory^>
rem   restore-dataset.bat prepare   ^<backup-id-or-directory^>
rem   restore-dataset.bat apply     ^<backup-id-or-directory^>
rem   restore-dataset.bat rollback  ^<backup-id-or-directory^>
rem   restore-dataset.bat postflight ^<backup-id-or-directory^>

set "SCRIPT_DIR=%~dp0"
pushd "%SCRIPT_DIR%..\..\.." >nul 2>&1
if errorlevel 1 (
    echo ERROR: Could not locate the Diaries project root. >&2
    endlocal & exit /b 1
)
set "PROJECT_DIR=%CD%"

if /I "%~1"=="preflight" (
    if "%~2"=="" goto :usage
    if not "%~3"=="" goto :usage
    set "OPTIONS=-PreflightOnly"
    goto :run
)
if /I "%~1"=="prepare" (
    if "%~2"=="" goto :usage
    if not "%~3"=="" goto :usage
    set "OPTIONS=-PrepareOnly"
    goto :run
)
if /I "%~1"=="apply" (
    if "%~2"=="" goto :usage
    if not "%~3"=="" goto :usage
    set "OPTIONS=-ApplyOnly"
    goto :run
)
if /I "%~1"=="rollback" (
    if "%~2"=="" goto :usage
    if not "%~3"=="" goto :usage
    set "OPTIONS=-RollbackOnly"
    goto :run
)
if /I "%~1"=="postflight" (
    if "%~2"=="" goto :usage
    if not "%~3"=="" goto :usage
    set "OPTIONS=-PostflightOnly"
    goto :run
)
goto :usage

:run
powershell -NoProfile -ExecutionPolicy Bypass -File "%PROJECT_DIR%\scripts\windows\common\restore-dataset.ps1" ^
    -ModeName "development-infrastructure" ^
    -ProjectDir "%PROJECT_DIR%" ^
    -BackupInput "%~2" ^
    %OPTIONS%
set "EXIT_CODE=%ERRORLEVEL%"
popd
endlocal & exit /b %EXIT_CODE%

:usage
echo Usage: restore-dataset.bat ^<preflight^|prepare^|apply^|rollback^|postflight^> ^<backup-id-or-directory^> >&2
popd
endlocal & exit /b 2
