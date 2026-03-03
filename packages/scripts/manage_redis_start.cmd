@echo off
setlocal EnableExtensions EnableDelayedExpansion
rem WinPyDeploy helper script (no registry writes)

set "SERVER="
for /f "delims=" %%F in ('where redis-server.exe 2^>nul') do if not defined SERVER set "SERVER=%%~fF"

set "ROOT=%WINPYDEPLOY_INSTALL_DIR%"
if not defined ROOT set "ROOT=C:\Program Files\softs"
set "BASE=%ROOT%\Redis"

if not defined SERVER if exist "%BASE%\redis-server.exe" set "SERVER=%BASE%\redis-server.exe"
if not defined SERVER if exist "%BASE%\bin\redis-server.exe" set "SERVER=%BASE%\bin\redis-server.exe"
if not defined SERVER if exist "C:\softs\Redis\redis-server.exe" set "SERVER=C:\softs\Redis\redis-server.exe"
if not defined SERVER if exist "C:\softs\Redis\bin\redis-server.exe" set "SERVER=C:\softs\Redis\bin\redis-server.exe"
if not defined SERVER if exist "C:\Program Files\softs\Redis\redis-server.exe" set "SERVER=C:\Program Files\softs\Redis\redis-server.exe"
if not defined SERVER if exist "C:\Program Files\softs\Redis\bin\redis-server.exe" set "SERVER=C:\Program Files\softs\Redis\bin\redis-server.exe"
if not defined SERVER if exist "%BASE%" for /r "%BASE%" %%F in (redis-server.exe) do if not defined SERVER set "SERVER=%%~fF"

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
