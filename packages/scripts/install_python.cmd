@echo off
setlocal EnableExtensions

set "ZIP=%~dp0..\python-3.12.10-embed-amd64.zip"
set "ROOT=C:\Program Files\softs"
if defined WINPYDEPLOY_INSTALL_DIR set "ROOT=%WINPYDEPLOY_INSTALL_DIR%"
set "DST=%ROOT%\Python312"

if not exist "%ZIP%" (
  echo [python] zip not found: "%ZIP%"
  exit /b 2
)

mkdir "%DST%" 2>nul

echo [python] extracting...
tar -xf "%ZIP%" -C "%DST%"
if errorlevel 1 exit /b %errorlevel%

rem PATH is injected by WinPyDeploy runtime env; no registry writes here.
echo [python] done. (only unzip; PATH is injected)
exit /b 0
