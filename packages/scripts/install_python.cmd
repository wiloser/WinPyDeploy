@echo off
setlocal EnableExtensions EnableDelayedExpansion

set "ZIP=%~dp0..\python-3.12.10-embed-amd64.zip"
set "DST=C:\Program Files\softs\Python312"

if not exist "%ZIP%" (
  echo [python] zip not found: "%ZIP%"
  exit /b 2
)

mkdir "%DST%" 2>nul

echo [python] extracting...
tar -xf "%ZIP%" -C "%DST%"
if errorlevel 1 exit /b %errorlevel%

call :prepend_path "%DST%"
call :prepend_path "%DST%\Scripts"

echo [python] done.
exit /b 0

:prepend_path
set "ADD=%~1"
for /f "tokens=2,*" %%A in ('reg query "HKLM\System\CurrentControlSet\Control\Session Manager\Environment" /v Path ^| find /i "Path"') do set "OLD=%%B"
if not defined OLD set "OLD="
set "NEW=%ADD%;%OLD%"
reg add "HKLM\System\CurrentControlSet\Control\Session Manager\Environment" /v Path /t REG_EXPAND_SZ /d "%NEW%" /f >nul
exit /b 0
