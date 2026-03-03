@echo off
setlocal EnableExtensions EnableDelayedExpansion
rem WinPyDeploy helper script (no registry writes)

set "ROOT=%WINPYDEPLOY_INSTALL_DIR%"
if not defined ROOT set "ROOT=C:\Program Files\softs"
set "BASE=%ROOT%\Python312"

set "PY=%BASE%\python.exe"
if not exist "%PY%" (
  set "PY="
  if exist "%BASE%" (
    for /r "%BASE%" %%F in (python.exe) do if not defined PY set "PY=%%~fF"
  )
)

if not defined PY (
  echo Python not found under "%BASE%"
  exit /b 1
)

set "PY=%PY:"=%"
if not exist "%PY%" (
  echo python.exe path invalid: "%PY%"
  exit /b 1
)

"%PY%" --version
if errorlevel 1 exit /b %ERRORLEVEL%
echo %PY%

"%PY%" -m pip --version
if errorlevel 1 exit /b %ERRORLEVEL%

rem pip list can be slow/large; keep it best-effort (do not fail overall)
"%PY%" -m pip list --format=columns

exit /b 0
