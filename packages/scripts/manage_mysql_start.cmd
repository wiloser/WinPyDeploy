@echo off
setlocal EnableExtensions EnableDelayedExpansion
rem WinPyDeploy helper script (no registry writes)

set "ROOT=%WINPYDEPLOY_INSTALL_DIR%"
if not defined ROOT set "ROOT=C:\Program Files\softs"
set "BASE=%ROOT%\MySQL"
set "BIN=%BASE%\bin"

set "MYSQD="
if exist "%BIN%\mysqld.exe" set "MYSQD=%BIN%\mysqld.exe"
if not defined MYSQD for /r "%BASE%" %%F in (mysqld.exe) do if not defined MYSQD set "MYSQD=%%~fF"

if not defined MYSQD (
  echo mysqld.exe not found under "%BASE%"
  exit /b 1
)

if not exist "!MYSQD!" (
  echo mysqld.exe path invalid: "!MYSQD!"
  exit /b 1
)

echo starting mysql: "!MYSQD!"
start "" /b "!MYSQD!"
exit /b 0
