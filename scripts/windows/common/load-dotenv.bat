@echo off

rem Load simple KEY=VALUE entries from an environment file.
rem This script intentionally does not use setlocal because the caller needs
rem the loaded variables.
rem
rem Usage:
rem   call load-dotenv.bat
rem   call load-dotenv.bat path\to\environment.env
rem
rem When no file is supplied, the top-level Diaries .env file is used.
rem A relative file path is first resolved relative to the caller's current
rem directory, and then relative to DIARIES_ROOT.

rem Derive the Diaries root from this script's location when not supplied.
rem This file is under: diaries\scripts\windows\common
if not defined DIARIES_ROOT (
    for %%I in ("%~dp0..\..\..") do set "DIARIES_ROOT=%%~fI"
)

if not exist "%DIARIES_ROOT%" (
    echo ERROR: Diaries root directory does not exist: "%DIARIES_ROOT%" >&2
    exit /b 1
)

if not "%~2"=="" (
    echo ERROR: load-dotenv.bat accepts at most one argument. >&2
    echo Usage: call load-dotenv.bat [environment-file] >&2
    exit /b 1
)

if "%~1"=="" goto :use_default_file

rem Resolve the supplied filename relative to the caller's current directory.
for %%I in ("%~1") do set "DOTENV_FILE=%%~fI"

if exist "%DOTENV_FILE%" goto :load_file

rem If it was a relative filename, try resolving it relative to DIARIES_ROOT.
for %%I in ("%DIARIES_ROOT%\%~1") do set "DOTENV_FILE=%%~fI"

goto :load_file

:use_default_file
set "DOTENV_FILE=%DIARIES_ROOT%\.env"

:load_file
if not exist "%DOTENV_FILE%" (
    echo ERROR: Environment file does not exist: "%DOTENV_FILE%" >&2
    exit /b 1
)

for /f "usebackq eol=# tokens=1,* delims==" %%A in ("%DOTENV_FILE%") do (
    if not "%%A"=="" set "%%A=%%B"
)

exit /b 0