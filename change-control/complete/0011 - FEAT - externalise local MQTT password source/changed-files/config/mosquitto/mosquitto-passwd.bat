@echo off
setlocal

set "SCRIPT_DIR=%~dp0"
set "SOURCE_FILE=%USERPROFILE%\.diaries\pwfile.source.txt"
set "MOSQUITTO_IMAGE=eclipse-mosquitto:2"

if not exist "%SOURCE_FILE%" (
    echo MQTT password source file not found: %SOURCE_FILE%
    exit /b 1
)

pushd "%SCRIPT_DIR%" || exit /b 1

copy /Y "%SOURCE_FILE%" "pwfile.txt" >nul
if errorlevel 1 (
    del /Q "pwfile.txt" >nul 2>&1
    echo Failed to copy the MQTT password source to pwfile.txt.
    popd
    exit /b 1
)

echo Converting pwfile.txt using %MOSQUITTO_IMAGE%...

docker run --rm ^
    -v "%CD%:/work" ^
    "%MOSQUITTO_IMAGE%" ^
    sh /work/generate-pwfile.sh

set "RC=%ERRORLEVEL%"

if not "%RC%"=="0" (
    del /Q "pwfile.txt" >nul 2>&1
    echo Failed to generate pwfile.txt.
    popd
    exit /b %RC%
)

echo pwfile.txt generated successfully.

popd
exit /b 0
