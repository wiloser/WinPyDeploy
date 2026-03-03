@echo off
setlocal EnableExtensions

set "ZIP=%~dp0..\mysql-8.0.45-winx64.zip"
set "ROOT=C:\Program Files\softs"
if defined WINPYDEPLOY_INSTALL_DIR set "ROOT=%WINPYDEPLOY_INSTALL_DIR%"
set "DST=%ROOT%\MySQL"

if not exist "%ZIP%" (
  echo [mysql] zip not found: "%ZIP%"
  exit /b 2
)

mkdir "%DST%" 2>nul

echo [mysql] extracting...
tar -xf "%ZIP%" -C "%DST%"
if errorlevel 1 exit /b %errorlevel%

rem PATH is injected by WinPyDeploy runtime env; no registry writes here.
echo [mysql] done. (only unzip; PATH is injected)
exit /b 0
