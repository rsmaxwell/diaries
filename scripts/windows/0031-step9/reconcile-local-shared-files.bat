@echo off
setlocal

rem 0031-FEAT Step 9: reconcile the one effective local database dataset
rem against the frozen pre-split shared Files tree. This is dry-run only.

set "SCRIPT_DIR=%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT_DIR%reconcile-local-shared-files.ps1" %*
set "EXIT_CODE=%ERRORLEVEL%"
endlocal & exit /b %EXIT_CODE%
