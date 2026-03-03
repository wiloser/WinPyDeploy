@echo off
setlocal EnableExtensions EnableDelayedExpansion

set "ZIP=%~dp0..\mysql-8.0.45-winx64.zip"
set "ROOT=C:\Program Files\softs"
if defined WINPYDEPLOY_INSTALL_DIR set "ROOT=%WINPYDEPLOY_INSTALL_DIR%"
set "DST=%ROOT%\MySQL"

if not exist "%ZIP%" (
  echo [mysql] zip not found: "%ZIP%"
  exit /b 2
)

mkdir "%DST%" 2>nul

echo [mysql] extracting...
tar -xf "%ZIP%" -C "%DST%"
if errorlevel 1 exit /b %errorlevel%

rem Flatten common zip layout: %DST%\mysql-8.x\bin\... -> %DST%\bin\...
rem flatten-v2: supports deeper nested layouts by recursively locating mysqld.exe
if not exist "%DST%\bin\mysqld.exe" (
  set "INNER="
  for /d %%D in ("%DST%\*") do (
    if exist "%%~fD\bin\mysqld.exe" if not defined INNER set "INNER=%%~fD"
  )
  if not defined INNER (
    for /r "%DST%" %%F in (mysqld.exe) do (
      if not defined INNER (
        set "EXEDIR=%%~dpF"
        set "EXEDIR=!EXEDIR:~0,-1!"
        for %%P in ("!EXEDIR!") do set "EXENAME=%%~nxP"
        if /i "!EXENAME!"=="bin" (
          for %%U in ("!EXEDIR!\..") do set "INNER=%%~fU"
        ) else (
          set "INNER=!EXEDIR!"
        )
      )
    )
  )
  if defined INNER (
    echo [mysql] flattening: "%INNER%" -> "%DST%"
    robocopy "%INNER%" "%DST%" /e /move >nul
    set "RC=!ERRORLEVEL!"
    if !RC! GEQ 8 (
      echo [mysql] flatten failed (robocopy=%RC%)
      exit /b !RC!
    )
    rmdir "%INNER%" 2>nul
  )
)

rem PATH is injected by WinPyDeploy runtime env; no registry writes here.
echo [mysql] done. (only unzip; PATH is injected)
exit /b 0
