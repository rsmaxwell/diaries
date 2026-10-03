@echo off
setlocal
set "SCRIPT_DIR=%~dp0"
where pwsh >nul 2>&1
if %ERRORLEVEL%==0 (
    pwsh -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT_DIR%reconcile-common-pair.ps1" %*
) else (
    powershell -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT_DIR%reconcile-common-pair.ps1" %*
)
set "RC=%ERRORLEVEL%"
endlocal & exit /b %RC%
