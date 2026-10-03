@echo off
setlocal
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0apply-step4-windows-cleanup.ps1"
set "RC=%ERRORLEVEL%"
endlocal & exit /b %RC%
