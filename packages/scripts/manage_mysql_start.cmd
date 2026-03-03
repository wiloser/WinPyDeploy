@echo off
setlocal EnableExtensions EnableDelayedExpansion
rem WinPyDeploy helper script (no registry writes)

set "MYSQD="
for /f "delims=" %%F in ('where mysqld.exe 2^>nul') do if not defined MYSQD set "MYSQD=%%~fF"

set "ROOT=%WINPYDEPLOY_INSTALL_DIR%"
if not defined ROOT set "ROOT=C:\Program Files\softs"
set "BASE=%ROOT%\MySQL"
set "BIN=%BASE%\bin"

if not defined MYSQD if exist "%BIN%\mysqld.exe" set "MYSQD=%BIN%\mysqld.exe"
if not defined MYSQD if exist "C:\softs\MySQL\bin\mysqld.exe" set "MYSQD=C:\softs\MySQL\bin\mysqld.exe"
if not defined MYSQD if exist "C:\Program Files\softs\MySQL\bin\mysqld.exe" set "MYSQD=C:\Program Files\softs\MySQL\bin\mysqld.exe"
if not defined MYSQD if exist "%BASE%" for /r "%BASE%" %%F in (mysqld.exe) do if not defined MYSQD set "MYSQD=%%~fF"

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
