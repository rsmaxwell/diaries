@echo off
setlocal

rem ============================================================================
rem report-effective-dataset.bat
rem
rem Print only non-secret diagnostics for the effective 0031 database + Files
rem selection after the caller has loaded the mode environment and local.env.
rem
rem Usage:
rem   call report-effective-dataset.bat MODE
rem ============================================================================

set "MODE_NAME=%~1"
if not defined MODE_NAME set "MODE_NAME=local"

if not defined DIARIES_DB_DATA_DIR (
    echo ERROR: DIARIES_DB_DATA_DIR is not set. >&2
    exit /b 1
)
if not defined DIARIES_FILES_DIR (
    echo ERROR: DIARIES_FILES_DIR is not set. >&2
    exit /b 1
)

for %%I in ("%DIARIES_DB_DATA_DIR%") do set "EFFECTIVE_DB_DATA_DIR=%%~fI"

echo Effective Diaries dataset selection [%MODE_NAME%]:
echo   Database data: "%EFFECTIVE_DB_DATA_DIR%"
echo   Files selector: "%DIARIES_FILES_DIR%"

if defined DIARIES_NAS_CONTENT_PATH (
    echo   Docker Files path: /data/files
    echo   NAS subpath: %DIARIES_NAS_CONTENT_PATH%/%DIARIES_FILES_DIR%
    echo   Diary subpath: %DIARIES_NAS_CONTENT_PATH%/diaries ^(read-only^)
)

echo.
exit /b 0
