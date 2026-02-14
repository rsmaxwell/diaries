@echo on
setLocal EnableDelayedExpansion

set BASEDIR=%~dp0

pushd %BASEDIR%
set DEV_SCRIPT_DIR=%CD%
popd

pushd %DEV_SCRIPT_DIR%\..
set SCRIPT_DIR=%CD%
popd

pushd %SCRIPT_DIR%\..
set SUBPROJECT_DIR=%CD%
popd

pushd %SCRIPT_DIR%\..
set PROJECT_DIR=%CD%
popd



cd %PROJECT_DIR%


set CLASSPATH="%SUBPROJECT_DIR%\bin\main
set CLASSPATH=%CLASSPATH%;%SUBPROJECT_DIR%\src\main\resources\META-INF
set CLASSPATH=%CLASSPATH%;%COMMON_SUBPROJECT_DIR%\bin\main
for /R %SUBPROJECT_DIR%\runtime %%a in (*.jar) do (
  set CLASSPATH=!CLASSPATH!;%%a
)
set CLASSPATH=%CLASSPATH%"

set HIBERNATE_LOGLEVEL=OFF
set LOGLEVEL=DEBUG

rem --- pretty-print classpath, one entry per line ---
set "CP=%CLASSPATH%"
set "CP=%CP:"=%"   rem remove the leading/trailing quotes

echo(
echo ==== CLASSPATH entries ====
for %%I in ("%CP:;=" "%") do echo %%~I
echo ===========================
echo(

java -classpath %CLASSPATH% com.rsmaxwell.diaries.responder.Responder ^
 --config %USERPROFILE%\.diaries\responder.json

