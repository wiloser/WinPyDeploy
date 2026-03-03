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

rem Flatten common zip layout: %DST%\python-3.x-embed-amd64\python.exe -> %DST%\python.exe
if not exist "%DST%\python.exe" (
  set "INNER="
  for /d %%D in ("%DST%\*") do (
    if exist "%%~fD\python.exe" if not defined INNER set "INNER=%%~fD"
  )
  if defined INNER (
    echo [python] flattening: "%INNER%" -> "%DST%"
    robocopy "%INNER%" "%DST%" /e /move >nul
    set "RC=%ERRORLEVEL%"
    if %RC% GEQ 8 (
      echo [python] flatten failed (robocopy=%RC%)
      exit /b %RC%
    )
    rmdir "%INNER%" 2>nul
  )
)

rem PATH is injected by WinPyDeploy runtime env; no registry writes here.
echo [python] done. (only unzip; PATH is injected)
exit /b 0
