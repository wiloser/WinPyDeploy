@echo off
setlocal EnableExtensions
rem WinPyDeploy helper script (no registry writes)

set "ROOT=%WINPYDEPLOY_INSTALL_DIR%"
if not defined ROOT set "ROOT=C:\Program Files\softs"
set "BASE=%ROOT%\MySQL"

if not exist "%BASE%" (
  echo MySQL not found: "%BASE%"
  exit /b 1
)

set "MYSQD="
for /r "%BASE%" %%F in (mysqld.exe) do if not defined MYSQD set "MYSQD=%%~fF"
set "EC=0"
if defined MYSQD (
  set "MYSQD=%MYSQD:"=%"
  echo %MYSQD%
  if exist "%MYSQD%" (
    "%MYSQD%" --version
    if errorlevel 1 set "EC=%ERRORLEVEL%"
  ) else (
    echo mysqld.exe path invalid: "%MYSQD%"
    set "EC=1"
  )
) else (
  echo mysqld.exe not found under "%BASE%"
  set "EC=1"
)

set "MYSQL="
for /r "%BASE%" %%F in (mysql.exe) do if not defined MYSQL set "MYSQL=%%~fF"
if defined MYSQL (
  set "MYSQL=%MYSQL:"=%"
  echo %MYSQL%
  if exist "%MYSQL%" (
    "%MYSQL%" --version
    rem client is optional; do not fail overall if it errors
  ) else (
    echo mysql.exe path invalid: "%MYSQL%"
  )
) else (
  echo mysql.exe not found under "%BASE%"
)

exit /b %EC%
