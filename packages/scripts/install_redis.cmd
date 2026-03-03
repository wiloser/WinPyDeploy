@echo off
setlocal EnableExtensions EnableDelayedExpansion

set "ZIP=%~dp0..\redis-windows-x64.zip"
set "ROOT=C:\Program Files\softs"
if defined WINPYDEPLOY_INSTALL_DIR set "ROOT=%WINPYDEPLOY_INSTALL_DIR%"
set "DST=%ROOT%\Redis"

if not exist "%ZIP%" (
  echo [redis] zip not found: "%ZIP%"
  exit /b 2
)

mkdir "%DST%" 2>nul

echo [redis] extracting...
tar -xf "%ZIP%" -C "%DST%"
if errorlevel 1 exit /b %errorlevel%

rem Flatten common zip layout: %DST%\Redis-8.x\redis-server.exe -> %DST%\redis-server.exe
if not exist "%DST%\redis-server.exe" (
  set "INNER="
  for /d %%D in ("%DST%\*") do (
    if exist "%%~fD\redis-server.exe" if not defined INNER set "INNER=%%~fD"
    if exist "%%~fD\bin\redis-server.exe" if not defined INNER set "INNER=%%~fD"
  )
  if defined INNER (
    echo [redis] flattening: "%INNER%" -> "%DST%"
    robocopy "%INNER%" "%DST%" /e /move >nul
    set "RC=!ERRORLEVEL!"
    if !RC! GEQ 8 (
      echo [redis] flatten failed (robocopy=%RC%)
      exit /b !RC!
    )
    rmdir "%INNER%" 2>nul
  )
)

rem PATH is injected by WinPyDeploy runtime env; no registry writes here.
echo [redis] done. (only unzip; PATH is injected)
exit /b 0
