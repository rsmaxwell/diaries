@echo off
setlocal

rem Runtime verification for 0031 Step 4. Run from any directory on the Windows
rem development machine after config\environments\local.env has been updated.

set "SCRIPT_DIR=%~dp0"
pushd "%SCRIPT_DIR%..\..\.." >nul 2>&1
if errorlevel 1 (
    echo ERROR: Could not locate the Diaries project root. >&2
    endlocal & exit /b 1
)

set "PROJECT_DIR=%CD%"
set "PREPARE_CONFIG=%PROJECT_DIR%\scripts\windows\development-infrastructure\prepare-responder-config.bat"
set "GRADLE_WRAPPER=%PROJECT_DIR%\gradlew.bat"

call "%PREPARE_CONFIG%"
if errorlevel 1 goto :failed

if not exist "%DIARIES_EFFECTIVE_RESPONDER_CONFIG%" (
    echo ERROR: Effective responder configuration was not generated. >&2
    goto :failed
)

powershell -NoProfile -ExecutionPolicy Bypass -Command "$c = Get-Content -LiteralPath $env:DIARIES_EFFECTIVE_RESPONDER_CONFIG -Raw | ConvertFrom-Json; if ([string]$c.diaries.files -ne [string]$env:DIARIES_FILES_DIR) { throw 'Generated diaries.files does not match DIARIES_FILES_DIR.' }; Write-Host ('PASS: generated diaries.files = ' + $c.diaries.files)"
if errorlevel 1 goto :failed

call "%GRADLE_WRAPPER%" :diaries-responder:test --tests "com.rsmaxwell.diaries.responder.handlers.UploadStagingTest.publicUrlAndPersistedPathDoNotExposePhysicalFilesDirectory"
if errorlevel 1 goto :failed

echo.
echo PASS: 0031 Step 4 runtime verification completed.
popd
endlocal & exit /b 0

:failed
echo.
echo ERROR: 0031 Step 4 runtime verification failed. >&2
popd
endlocal & exit /b 1
