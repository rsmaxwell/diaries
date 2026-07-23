@echo off
setlocal

pushd "%~dp0..\.." || exit /b 1

docker compose down
set "RC=%ERRORLEVEL%"

popd
endlocal
exit /b %RC%
