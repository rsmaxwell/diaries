@echo off

rem ============================================================================
rem prepare-responder-config.bat
rem
rem Prepare the effective responder configuration used by direct Windows
rem development. This file intentionally does not use setlocal because callers
rem consume the DIARIES_EFFECTIVE_* variables it sets.
rem
rem Environment precedence is the same as the development-infrastructure
rem Compose scripts:
rem
rem   1. config\environments\development-infrastructure.env
rem   2. config\environments\local.env
rem
rem The developer-owned responder JSON remains the base configuration. Only
rem diaries.files is overridden in the generated configuration.
rem ============================================================================

set "SCRIPT_DIR=%~dp0"
set "PREPARE_EXIT_CODE=0"

pushd "%SCRIPT_DIR%..\..\.." >nul 2>&1
if errorlevel 1 (
    echo ERROR: Could not locate the Diaries project root. >&2
    exit /b 1
)

set "PROJECT_DIR=%CD%"
set "ENV_FILE=%PROJECT_DIR%\config\environments\development-infrastructure.env"
set "LOCAL_ENV_FILE=%PROJECT_DIR%\config\environments\local.env"
set "LOAD_DOTENV=%PROJECT_DIR%\scripts\windows\common\load-dotenv.bat"
set "PREPARE_PS1=%PROJECT_DIR%\scripts\windows\development-infrastructure\prepare-responder-config.ps1"
set "DATASET_PAIR_GUARD=%PROJECT_DIR%\scripts\windows\common\validate-dataset-pair.bat"

if not exist "%ENV_FILE%" (
    echo ERROR: Environment file not found: "%ENV_FILE%" >&2
    set "PREPARE_EXIT_CODE=1"
    goto :cleanup
)

if not exist "%LOCAL_ENV_FILE%" (
    echo ERROR: Local environment file not found: "%LOCAL_ENV_FILE%" >&2
    echo Copy config\environments\local.env.example to local.env and customise it. >&2
    set "PREPARE_EXIT_CODE=1"
    goto :cleanup
)

if not exist "%LOAD_DOTENV%" (
    echo ERROR: Environment loader not found: "%LOAD_DOTENV%" >&2
    set "PREPARE_EXIT_CODE=1"
    goto :cleanup
)

if not exist "%PREPARE_PS1%" (
    echo ERROR: Responder configuration helper not found: "%PREPARE_PS1%" >&2
    set "PREPARE_EXIT_CODE=1"
    goto :cleanup
)

if not exist "%DATASET_PAIR_GUARD%" (
    echo ERROR: Dataset-pair validator not found: "%DATASET_PAIR_GUARD%" >&2
    set "PREPARE_EXIT_CODE=1"
    goto :cleanup
)

call "%DATASET_PAIR_GUARD%" "development-infrastructure" "%ENV_FILE%" "%LOCAL_ENV_FILE%"
if errorlevel 1 (
    set "PREPARE_EXIT_CODE=1"
    goto :cleanup
)

call "%LOAD_DOTENV%" "%ENV_FILE%"
if errorlevel 1 (
    set "PREPARE_EXIT_CODE=1"
    goto :cleanup
)

call "%LOAD_DOTENV%" "%LOCAL_ENV_FILE%"
if errorlevel 1 (
    set "PREPARE_EXIT_CODE=1"
    goto :cleanup
)

if not defined DIARIES_DB_DATA_DIR (
    echo ERROR: DIARIES_DB_DATA_DIR is not set after applying development-infrastructure.env and local.env. >&2
    set "PREPARE_EXIT_CODE=1"
    goto :cleanup
)

if not defined DIARIES_FILES_DIR (
    echo ERROR: DIARIES_FILES_DIR is not set after applying development-infrastructure.env and local.env. >&2
    set "PREPARE_EXIT_CODE=1"
    goto :cleanup
)

rem DIARIES_RESPONDER_CONFIG_FILE was historically the reconciliation script's
rem explicit config override. Preserve that compatibility by treating it as an
rem alternate developer-owned base. DIARIES_RESPONDER_BASE_CONFIG_FILE is the
rem clearer name for new usage and takes precedence when both are present.
set "BASE_CONFIG=%USERPROFILE%\.diaries\responder.json"
if defined DIARIES_RESPONDER_CONFIG_FILE set "BASE_CONFIG=%DIARIES_RESPONDER_CONFIG_FILE%"
if defined DIARIES_RESPONDER_BASE_CONFIG_FILE set "BASE_CONFIG=%DIARIES_RESPONDER_BASE_CONFIG_FILE%"

for %%I in ("%BASE_CONFIG%") do set "BASE_CONFIG=%%~fI"
if not exist "%BASE_CONFIG%" (
    echo ERROR: Developer responder configuration not found: "%BASE_CONFIG%" >&2
    set "PREPARE_EXIT_CODE=1"
    goto :cleanup
)

set "GENERATED_DIR=%PROJECT_DIR%\build\development-infrastructure"
set "GENERATED_CONFIG=%GENERATED_DIR%\responder.effective.json"
if not exist "%GENERATED_DIR%" mkdir "%GENERATED_DIR%" >nul 2>&1
if errorlevel 1 (
    echo ERROR: Could not create generated configuration directory: "%GENERATED_DIR%" >&2
    set "PREPARE_EXIT_CODE=1"
    goto :cleanup
)

set "DIARIES_EFFECTIVE_FILES_ROOT="
for /f "usebackq delims=" %%I in (`powershell -NoProfile -ExecutionPolicy Bypass -File "%PREPARE_PS1%" -BaseConfig "%BASE_CONFIG%" -OutputConfig "%GENERATED_CONFIG%" -FilesDir "%DIARIES_FILES_DIR%"`) do set "DIARIES_EFFECTIVE_FILES_ROOT=%%I"

if not defined DIARIES_EFFECTIVE_FILES_ROOT (
    echo ERROR: Effective responder configuration could not be generated. >&2
    set "PREPARE_EXIT_CODE=1"
    goto :cleanup
)

if not exist "%GENERATED_CONFIG%" (
    echo ERROR: Generated responder configuration not found: "%GENERATED_CONFIG%" >&2
    set "PREPARE_EXIT_CODE=1"
    goto :cleanup
)

for %%I in ("%DIARIES_DB_DATA_DIR%") do set "DIARIES_EFFECTIVE_DB_DATA_DIR=%%~fI"
set "DIARIES_EFFECTIVE_RESPONDER_CONFIG=%GENERATED_CONFIG%"

rem Deliberately print only non-secret dataset/storage diagnostics.
echo Effective development dataset:
echo   Database data: "%DIARIES_EFFECTIVE_DB_DATA_DIR%"
echo   Files root:    "%DIARIES_EFFECTIVE_FILES_ROOT%"
echo   Responder cfg: "%DIARIES_EFFECTIVE_RESPONDER_CONFIG%"

:cleanup
popd
exit /b %PREPARE_EXIT_CODE%
