@echo off
setlocal

set "SCRIPT_DIR=%~dp0"
set "MOSQUITTO_IMAGE=eclipse-mosquitto:2"

pushd "%SCRIPT_DIR%" || exit /b 1

copy /Y "pwfile.source.txt" "pwfile.txt" >nul
if errorlevel 1 (
    echo Failed to copy pwfile.source.txt to pwfile.txt.
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
    echo Failed to generate pwfile.txt.
    popd
    exit /b %RC%
)

echo pwfile.txt generated successfully.

popd
exit /b 0
