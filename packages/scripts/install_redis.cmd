@echo off
setlocal EnableExtensions EnableDelayedExpansion

set "ZIP=%~dp0..\redis-windows-x64.zip"
set "ROOT=C:\Program Files\softs"
if defined WINPYDEPLOY_INSTALL_DIR set "ROOT=%WINPYDEPLOY_INSTALL_DIR%"
set "DST=%ROOT%\Redis"

rem Preflight: ensure target dir is writable (Program Files often requires elevation)
mkdir "%DST%" 2>nul
(
  >"%DST%\.__writetest" echo ok
) 2>nul
if not exist "%DST%\.__writetest" (
  echo [redis] ERROR: no write permission to "%DST%".
  echo [redis] 请使用管理员权限运行，或在设置中把“集中安装目录”改到非 Program Files 目录（如 C:\softs）。
  exit /b 5
)
del /q "%DST%\.__writetest" 2>nul

if not exist "%ZIP%" (
  echo [redis] zip not found: "%ZIP%"
  exit /b 2
)

echo [redis] extracting...
tar -xf "%ZIP%" -C "%DST%"
if errorlevel 1 exit /b %errorlevel%

rem Flatten common zip layout: %DST%\Redis-8.x\redis-server.exe -> %DST%\redis-server.exe
rem flatten-v3: supports deeper nested layouts; safer echo/exit behavior inside blocks
if not exist "%DST%\redis-server.exe" if not exist "%DST%\bin\redis-server.exe" (
  set "INNER="
  for /d %%D in ("%DST%\*") do (
    if exist "%%~fD\redis-server.exe" if not defined INNER set "INNER=%%~fD"
    if exist "%%~fD\bin\redis-server.exe" if not defined INNER set "INNER=%%~fD"
  )
  if not defined INNER (
    for /r "%DST%" %%F in (redis-server.exe) do (
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
    echo [redis] flattening: "%INNER%" -> "%DST%"
    robocopy "%INNER%" "%DST%" /e /move >nul
    set "RC=!ERRORLEVEL!"
    if !RC! GEQ 8 (
      echo [redis] flatten failed. robocopy=!RC!
      exit /b !RC!
    )
    rmdir "%INNER%" 2>nul
  )
)

rem PATH is injected by WinPyDeploy runtime env; no registry writes here.
echo [redis] done. (only unzip; PATH is injected)
exit /b 0
