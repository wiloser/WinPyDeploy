@echo off
setlocal EnableExtensions EnableDelayedExpansion
rem WinPyDeploy helper script (no registry writes)
rem info-v3: prefer standard %BASE%\bin layout, fallback to recursive search

set "ROOT=%WINPYDEPLOY_INSTALL_DIR%"
if not defined ROOT set "ROOT=C:\Program Files\softs"
set "BASE=%ROOT%\MySQL"
set "BIN=%BASE%\bin"

if not exist "%BASE%" (
  echo MySQL not found: "%BASE%"
  exit /b 1
)

set "MYSQD="
if exist "%BIN%\mysqld.exe" set "MYSQD=%BIN%\mysqld.exe"
if not defined MYSQD for /r "%BASE%" %%F in (mysqld.exe) do if not defined MYSQD set "MYSQD=%%~fF"
set "EC=0"
if defined MYSQD (
  if exist "!MYSQD!" (
    "!MYSQD!" --version
    if errorlevel 1 set "EC=!ERRORLEVEL!"
    echo !MYSQD!
  ) else (
    echo mysqld.exe path invalid: "!MYSQD!"
    set "EC=1"
  )
) else (
  echo mysqld.exe not found under "%BASE%"
  set "EC=1"
)

set "MYSQL="
if exist "%BIN%\mysql.exe" set "MYSQL=%BIN%\mysql.exe"
if not defined MYSQL for /r "%BASE%" %%F in (mysql.exe) do if not defined MYSQL set "MYSQL=%%~fF"
if defined MYSQL (
  if exist "!MYSQL!" (
    "!MYSQL!" --version
    echo !MYSQL!
    rem client is optional; do not fail overall if it errors
  ) else (
    echo mysql.exe path invalid: "!MYSQL!"
  )
) else (
  echo mysql.exe not found under "%BASE%"
)

exit /b !EC!
