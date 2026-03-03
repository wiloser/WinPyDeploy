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
if defined MYSQD (
  set "MYSQD=%MYSQD:"=%"
  echo %MYSQD%
  if exist "%MYSQD%" (
    "%MYSQD%" --version
  ) else (
    echo mysqld.exe path invalid: "%MYSQD%"
  )
) else (
  echo mysqld.exe not found under "%BASE%"
)

set "MYSQL="
for /r "%BASE%" %%F in (mysql.exe) do if not defined MYSQL set "MYSQL=%%~fF"
if defined MYSQL (
  set "MYSQL=%MYSQL:"=%"
  echo %MYSQL%
  if exist "%MYSQL%" (
    "%MYSQL%" --version
  ) else (
    echo mysql.exe path invalid: "%MYSQL%"
  )
) else (
  echo mysql.exe not found under "%BASE%"
)

if defined MYSQD exit /b 0
exit /b 1
