@echo off
setlocal
set "SCRIPT_DIR=%~dp0"
set "STEP6_DIR=%SCRIPT_DIR%.."
py "%SCRIPT_DIR%verify-step6-evidence.py" > "%STEP6_DIR%\VERIFICATION-OUTPUT.txt" 2>&1
set "RC=%ERRORLEVEL%"
type "%STEP6_DIR%\VERIFICATION-OUTPUT.txt"
exit /b %RC%
