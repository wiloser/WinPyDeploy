@echo off
setlocal EnableExtensions EnableDelayedExpansion
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
set "EC=0"
if defined SERVER (
  set "SERVER=%SERVER:"=%"
  if exist "%SERVER%" (
    set "VLINE="
    for /f "usebackq delims=" %%L in (`"%SERVER%" --version 2^>nul`) do if not defined VLINE set "VLINE=%%L"
    if defined VLINE (
      set "VER="
      for /f "tokens=2 delims==" %%V in ("!VLINE!") do if not defined VER set "VER=%%V"
      for /f "tokens=1 delims= " %%V in ("!VER!") do set "VER=%%V"
      if defined VER (
        echo Redis !VER!
      ) else (
        echo Redis
      )
      echo !VLINE!
    ) else (
      "%SERVER%" --version
      if errorlevel 1 set "EC=!ERRORLEVEL!"
    )
    echo %SERVER%
  ) else (
    echo redis-server.exe path invalid: "%SERVER%"
    set "EC=1"
  )
) else (
  echo redis-server.exe not found under "%BASE%"
  set "EC=1"
)

set "CLI="
for /r "%BASE%" %%F in (redis-cli.exe) do if not defined CLI set "CLI=%%~fF"
if defined CLI (
  set "CLI=%CLI:"=%"
  if exist "%CLI%" (
    "%CLI%" --version
    echo %CLI%
    rem cli is optional; do not fail overall if it errors
  ) else (
    echo redis-cli.exe path invalid: "%CLI%"
  )
) else (
  echo redis-cli.exe not found under "%BASE%"
)

exit /b !EC!
