@echo off
setlocal EnableExtensions

set "ZIP=%~dp0..\mysql-8.0.45-winx64.zip"
set "DST=C:\Program Files\softs\MySQL"

if not exist "%ZIP%" (
  echo [mysql] zip not found: "%ZIP%"
  exit /b 2
)

mkdir "%DST%" 2>nul

echo [mysql] extracting...
tar -xf "%ZIP%" -C "%DST%"
if errorlevel 1 exit /b %errorlevel%

set "BIN="
for /r "%DST%" %%F in (mysqld.exe) do if not defined BIN set "BIN=%%~dpF"
if not defined BIN set "BIN=%DST%\bin\"

call :prepend_path "%BIN%"

echo [mysql] done. (only unzip + PATH)
exit /b 0

:prepend_path
set "ADD=%~1"
set "ADD=%ADD:"=%"
set "OLD="
for /f "skip=2 tokens=2,*" %%A in ('reg query "HKLM\System\CurrentControlSet\Control\Session Manager\Environment" /v Path 2^>nul') do set "OLD=%%B"
if not defined OLD set "OLD="
set "OLD=%OLD:"=%"
set "NEW=%ADD%;%OLD%"
reg add "HKLM\System\CurrentControlSet\Control\Session Manager\Environment" /v Path /t REG_EXPAND_SZ /d "%NEW%" /f >nul 2>nul && exit /b 0
reg add "HKCU\Environment" /v Path /t REG_EXPAND_SZ /d "%NEW%" /f >nul 2>nul && exit /b 0
exit /b 0
