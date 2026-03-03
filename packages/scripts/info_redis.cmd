@echo off
setlocal EnableExtensions
rem WinPyDeploy helper script (no registry writes)

set "ROOT=%WINPYDEPLOY_INSTALL_DIR%"
if not defined ROOT set "ROOT=C:\Program Files\softs"
set "BASE=%ROOT%\Redis"

if not exist "%BASE%" (
  echo Redis not found: "%BASE%"
  exit /b 1
)

set "SERVER="
for /r "%BASE%" %%F in (redis-server.exe) do if not defined SERVER set "SERVER=%%~fF"
if defined SERVER (
  echo %SERVER%
  "%SERVER%" --version
) else (
  echo redis-server.exe not found under "%BASE%"
)

set "CLI="
for /r "%BASE%" %%F in (redis-cli.exe) do if not defined CLI set "CLI=%%~fF"
if defined CLI (
  echo %CLI%
  "%CLI%" --version
) else (
  echo redis-cli.exe not found under "%BASE%"
)

if defined SERVER exit /b 0
exit /b 1
