@echo off
setlocal EnableExtensions EnableDelayedExpansion
rem WinPyDeploy helper script (no registry writes)
rem manage-v2: auto-init datadir and verify mysqld startup

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

for %%P in ("!MYSQD!\..") do set "BIN=%%~fP"
for %%P in ("!BIN!\..") do set "BASE=%%~fP"
set "DATA=!BASE!\data"
set "PORT=3306"

rem If already running, treat as success.
tasklist /FI "IMAGENAME eq mysqld.exe" | find /I "mysqld.exe" >nul
if not errorlevel 1 (
  echo mysqld already running
  exit /b 0
)

rem First-run init for zip distribution.
if not exist "!DATA!\mysql" (
  echo initializing mysql data dir: "!DATA!"
  mkdir "!DATA!" 2>nul
  "!MYSQD!" --initialize-insecure --basedir="!BASE!" --datadir="!DATA!"
  if errorlevel 1 (
    echo mysql initialize failed
    exit /b 2
  )
)

echo starting mysql: "!MYSQD!"
start "" /min "!MYSQD!" --standalone --basedir="!BASE!" --datadir="!DATA!" --port=!PORT!

timeout /t 2 /nobreak >nul
tasklist /FI "IMAGENAME eq mysqld.exe" | find /I "mysqld.exe" >nul
if errorlevel 1 (
  echo mysql start failed (mysqld not running)
  exit /b 3
)

echo mysql started on port !PORT!
exit /b 0
