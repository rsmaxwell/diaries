@echo off
setlocal

rem ============================================================================
rem build.bat
rem
rem Build the Diaries Docker images for the local-docker-build mode.
rem
rem The script:
rem   - locates the Diaries project root;
rem   - validates the mode-specific Compose and environment files;
rem   - loads the local-docker-build environment;
rem   - generates the Angular client build information;
rem   - validates the client version;
rem   - builds the Docker images using the mode-specific Compose definition.
rem ============================================================================


rem ----------------------------------------------------------------------------
rem Initialise common script variables.
rem
rem SCRIPT_DIR is the directory containing this script.
rem EXIT_CODE is returned to the calling process when the script finishes.
rem ----------------------------------------------------------------------------

set "SCRIPT_DIR=%~dp0"
set "EXIT_CODE=0"


rem ----------------------------------------------------------------------------
rem Locate the Diaries project root.
rem
rem This script is located under:
rem
rem     diaries\scripts\windows\local-docker-build
rem
rem Moving up three levels therefore gives us the Diaries project directory.
rem Exit immediately if that directory cannot be located. Since pushd has not
rem succeeded in that case, there is no corresponding popd to perform.
rem ----------------------------------------------------------------------------

pushd "%SCRIPT_DIR%..\..\.." >nul 2>&1
if errorlevel 1 (
    echo ERROR: Could not locate the Diaries project root. >&2
    echo Script directory: "%SCRIPT_DIR%" >&2
    endlocal & exit /b 1
)

set "PROJECT_DIR=%CD%"


rem ----------------------------------------------------------------------------
rem Define and validate the Compose file for local-docker-build mode.
rem ----------------------------------------------------------------------------

set "COMPOSE_FILE=%PROJECT_DIR%\compose.local-docker-build.yaml"

if not exist "%COMPOSE_FILE%" (
    echo ERROR: Compose file not found: "%COMPOSE_FILE%" >&2
    set "EXIT_CODE=1"
    goto :cleanup
)


rem ----------------------------------------------------------------------------
rem Define and validate the environment files for local-docker-build mode.
rem
rem ENV_FILE contains the committed mode-specific settings.
rem LOCAL_ENV_FILE contains machine-specific settings and overrides.
rem
rem The mode environment is applied first and local.env second, so values in
rem local.env take precedence over values in local-docker-build.env.
rem ----------------------------------------------------------------------------

set "ENV_FILE=%PROJECT_DIR%\config\environments\local-docker-build.env"
if not exist "%ENV_FILE%" (
    echo ERROR: Environment file not found: "%ENV_FILE%" >&2
    set "EXIT_CODE=1"
    goto :cleanup
)

set "LOCAL_ENV_FILE=%PROJECT_DIR%\config\environments\local.env"
if not exist "%LOCAL_ENV_FILE%" (
    echo ERROR: Local environment file not found: "%LOCAL_ENV_FILE%" >&2
    set "EXIT_CODE=1"
    goto :cleanup
)


rem ----------------------------------------------------------------------------
rem Load both environment files into the current batch process.
rem
rem Load the mode-specific environment first, followed by local.env so that
rem machine-specific values override the committed mode defaults.
rem ----------------------------------------------------------------------------

call "%PROJECT_DIR%\scripts\windows\common\load-dotenv.bat" "%ENV_FILE%"
if errorlevel 1 (
    echo ERROR: Could not load environment file: "%ENV_FILE%" >&2
    set "EXIT_CODE=1"
    goto :cleanup
)

call "%PROJECT_DIR%\scripts\windows\common\load-dotenv.bat" "%LOCAL_ENV_FILE%"
if errorlevel 1 (
    echo ERROR: Could not load local environment file: "%LOCAL_ENV_FILE%" >&2
    set "EXIT_CODE=1"
    goto :cleanup
)


rem ----------------------------------------------------------------------------
rem Generate the Angular client build information.
rem
rem The client build runs in its own directory. Pair this temporary pushd with
rem a nearby popd so that the common cleanup section remains responsible only
rem for restoring the original project-root pushd.
rem ----------------------------------------------------------------------------

pushd "%PROJECT_DIR%\diaries-client" >nul 2>&1
if errorlevel 1 (
    echo ERROR: Could not enter Diaries client directory. >&2
    set "EXIT_CODE=1"
    goto :cleanup
)

call npm run generate-build-info
set "EXIT_CODE=%ERRORLEVEL%"

popd

if not "%EXIT_CODE%"=="0" (
    echo ERROR: Failed to generate Diaries client build information. >&2
    goto :cleanup
)


rem ----------------------------------------------------------------------------
rem Read the client version from the build information that was just generated.
rem
rem generate-build-info.js is the authoritative source for the client version.
rem It writes that version to public\assets\build-info.json, but a child Node
rem process cannot set an environment variable in this parent batch process.
rem Therefore read the generated version back into DIARIES_CLIENT_VERSION.
rem ----------------------------------------------------------------------------

set "CLIENT_BUILD_INFO_FILE=%PROJECT_DIR%\diaries-client\public\assets\build-info.json"
set "DIARIES_CLIENT_VERSION="

if not exist "%CLIENT_BUILD_INFO_FILE%" (
    echo ERROR: Client build information file not found: "%CLIENT_BUILD_INFO_FILE%" >&2
    set "EXIT_CODE=1"
    goto :cleanup
)

for /f "usebackq delims=" %%I in (`
    powershell -NoProfile -Command ^
        "$info = Get-Content -Raw '%CLIENT_BUILD_INFO_FILE%' | ConvertFrom-Json; $info.version"
`) do set "DIARIES_CLIENT_VERSION=%%I"

if not defined DIARIES_CLIENT_VERSION (
    echo ERROR: Unable to determine the Diaries client version from: >&2
    echo "%CLIENT_BUILD_INFO_FILE%" >&2
    set "EXIT_CODE=1"
    goto :cleanup
)


rem ----------------------------------------------------------------------------
rem Build the Docker images.
rem
rem Both environment files are supplied to Docker Compose in the same order in
rem which they were loaded above. Values in local.env therefore override values
rem from local-docker-build.env.
rem
rem DIARIES_CLIENT_VERSION was read from the generated build-info.json and is
rem already present in this batch process, so it is also available to Compose.
rem
rem The Compose project name is deliberately not supplied here. It is defined
rem by the top-level "name:" property in compose.local-docker-build.yaml.
rem ----------------------------------------------------------------------------

echo Building Diaries client version %DIARIES_CLIENT_VERSION%
echo.

docker compose ^
    --env-file "%ENV_FILE%" ^
    --env-file "%LOCAL_ENV_FILE%" ^
    -f "%COMPOSE_FILE%" ^
    build

set "EXIT_CODE=%ERRORLEVEL%"

if not "%EXIT_CODE%"=="0" (
    echo.
    echo ERROR: Diaries Docker image build failed with exit code %EXIT_CODE%. >&2
    goto :cleanup
)


rem ----------------------------------------------------------------------------
rem Report successful completion.
rem ----------------------------------------------------------------------------

echo.
echo Diaries Docker images built successfully.


rem ----------------------------------------------------------------------------
rem Common cleanup and exit.
rem
rem The initial project-root pushd succeeded before any path can reach this
rem label, so it is safe to restore the caller's original working directory.
rem ----------------------------------------------------------------------------

:cleanup
popd
endlocal & exit /b %EXIT_CODE%