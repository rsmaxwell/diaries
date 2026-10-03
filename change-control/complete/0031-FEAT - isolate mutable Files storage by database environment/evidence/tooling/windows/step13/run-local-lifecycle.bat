@echo off
setlocal
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0run-local-lifecycle.ps1" %*
exit /b %errorlevel%
