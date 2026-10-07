@echo off
setlocal EnableExtensions

rem 0033-FEAT complete-dataset backup entry point for development-infrastructure.
rem Usage:
rem   backup-dataset.bat                         Capture, verify and promote one complete backup
rem   backup-dataset.bat preflight               Resolve/check the effective dataset without mutation
rem   backup-dataset.bat finalise YYYYMMDD-HHmmssZ  Finalise an existing Step-3 .partial capture

set "SCRIPT_DIR=%~dp0"
pushd "%SCRIPT_DIR%..\..\.." >nul 2>&1
if errorlevel 1 (
    echo ERROR: Could not locate the Diaries project root. >&2
    endlocal & exit /b 1
)
set "PROJECT_DIR=%CD%"
set "OPTIONS="
if /I "%~1"=="preflight" set "OPTIONS=-PreflightOnly"
if /I "%~1"=="finalise" (
    if "%~2"=="" goto :usage
    if not "%~3"=="" goto :usage
    set "OPTIONS=-FinaliseBackupId %~2"
)
if /I not "%~1"=="finalise" if not "%~1"=="" if /I not "%~1"=="preflight" goto :usage

powershell -NoProfile -ExecutionPolicy Bypass -File "%PROJECT_DIR%\scripts\windows\common\backup-dataset.ps1" ^
    -ModeName "development-infrastructure" ^
    -ProjectDir "%PROJECT_DIR%" ^
    %OPTIONS%
set "EXIT_CODE=%ERRORLEVEL%"
popd
endlocal & exit /b %EXIT_CODE%

:usage
echo Usage: backup-dataset.bat [preflight ^| finalise YYYYMMDD-HHmmssZ] >&2
popd
endlocal & exit /b 2
