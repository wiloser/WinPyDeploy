@echo off
setlocal EnableExtensions EnableDelayedExpansion

set "ZIP=%~dp0..\python-3.12.10-embed-amd64.zip"
set "ROOT=C:\Program Files\softs"
if defined WINPYDEPLOY_INSTALL_DIR set "ROOT=%WINPYDEPLOY_INSTALL_DIR%"
set "DST=%ROOT%\Python312"

rem Preflight: ensure target dir is writable (Program Files often requires elevation)
mkdir "%DST%" 2>nul
(
  >"%DST%\.__writetest" echo ok
) 2>nul
if not exist "%DST%\.__writetest" (
  echo [python] ERROR: no write permission to "%DST%".
  echo [python] 请使用管理员权限运行，或在设置中把“集中安装目录”改到非 Program Files 目录（如 C:\softs）。
  exit /b 5
)
del /q "%DST%\.__writetest" 2>nul

if not exist "%ZIP%" (
  echo [python] zip not found: "%ZIP%"
  exit /b 2
)

echo [python] extracting...
tar -xf "%ZIP%" -C "%DST%"
if errorlevel 1 exit /b %errorlevel%

rem Flatten common zip layout: %DST%\python-3.x-embed-amd64\python.exe -> %DST%\python.exe
rem flatten-v4: copy-only flattening (no /move), with best-effort cleanup
if not exist "%DST%\python.exe" (
  set "INNER="
  for /d %%D in ("%DST%\*") do (
    if exist "%%~fD\python.exe" if not defined INNER set "INNER=%%~fD"
  )
  if not defined INNER (
    for /r "%DST%" %%F in (python.exe) do (
      if not defined INNER (
        set "EXEDIR=%%~dpF"
        set "EXEDIR=!EXEDIR:~0,-1!"
        set "INNER=!EXEDIR!"
      )
    )
  )
  if defined INNER (
    echo [python] flattening: "%INNER%" -> "%DST%"
    robocopy "%INNER%" "%DST%" /e /r:1 /w:1
    set "RC=!ERRORLEVEL!"
    if !RC! GEQ 8 (
      echo [python] flatten failed. robocopy=!RC!
      exit /b !RC!
    )
    if /i not "!INNER!"=="%DST%" rmdir /s /q "!INNER!" 2>nul
  )
)

rem PATH is injected by WinPyDeploy runtime env; no registry writes here.
echo [python] done. (only unzip; PATH is injected)
exit /b 0
