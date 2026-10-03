@echo off
setlocal
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0run-step8-diaries-final-regression.ps1" %*
exit /b %ERRORLEVEL%
