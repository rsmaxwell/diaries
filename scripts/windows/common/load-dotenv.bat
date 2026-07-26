@echo off

rem Load simple KEY=VALUE entries from the top-level .env file.
rem This intentionally does not use setlocal because the caller needs the values.

if "%PROJECT_DIR%"=="" (
    echo PROJECT_DIR is not set.
    exit /b 1
)

if exist "%PROJECT_DIR%\.env" (
    for /f "usebackq eol=# tokens=1,* delims==" %%A in ("%PROJECT_DIR%\.env") do (
        if not "%%A"=="" set "%%A=%%B"
    )
)

exit /b 0
