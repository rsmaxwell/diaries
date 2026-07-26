@echo off

rem Override the published image tag for this mode.
rem This takes precedence over the top-level .env file.
set "DIARIES_IMAGE_TAG=integration"

exit /b 0
