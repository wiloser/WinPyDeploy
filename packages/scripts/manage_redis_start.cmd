@echo off
setlocal EnableExtensions EnableDelayedExpansion
rem WinPyDeploy helper script (no registry writes)

set "ROOT=%WINPYDEPLOY_INSTALL_DIR%"
if not defined ROOT set "ROOT=C:\Program Files\softs"
set "BASE=%ROOT%\Redis"

set "SERVER="
if exist "%BASE%\redis-server.exe" set "SERVER=%BASE%\redis-server.exe"
if not defined SERVER if exist "%BASE%\bin\redis-server.exe" set "SERVER=%BASE%\bin\redis-server.exe"
if not defined SERVER for /r "%BASE%" %%F in (redis-server.exe) do if not defined SERVER set "SERVER=%%~fF"

if not defined SERVER (
  echo redis-server.exe not found under "%BASE%"
  exit /b 1
)

if not exist "!SERVER!" (
  echo redis-server.exe path invalid: "!SERVER!"
  exit /b 1
)

echo starting redis: "!SERVER!"
start "" /b "!SERVER!"
exit /b 0
