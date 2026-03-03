@echo off
setlocal EnableExtensions EnableDelayedExpansion
rem WinPyDeploy helper script: persist selected install dirs into USER PATH

set "ROOT=%WINPYDEPLOY_INSTALL_DIR%"
if not defined ROOT set "ROOT=C:\Program Files\softs"

set "FOUND="
for %%E in (python.exe pip.exe mysqld.exe mysql.exe redis-server.exe redis-cli.exe) do (
  for /f "delims=" %%F in ('where %%E 2^>nul') do (
    call :append_dir "%%~dpF"
  )
)

if not defined FOUND if exist "%ROOT%" (
  for %%E in (python.exe pip.exe mysqld.exe mysql.exe redis-server.exe redis-cli.exe) do (
    for /r "%ROOT%" %%F in (%%E) do (
      call :append_dir "%%~dpF"
    )
  )
)

if not defined FOUND (
  echo [path] no executable dirs found under "%ROOT%"
  exit /b 0
)

set "OLD="
for /f "skip=2 tokens=2,*" %%A in ('reg query "HKCU\Environment" /v Path 2^>nul') do (
  if /i "%%A"=="REG_EXPAND_SZ" set "OLD=%%B"
  if /i "%%A"=="REG_SZ" set "OLD=%%B"
)

if defined OLD (
  set "NEW=%OLD%"
) else (
  set "NEW="
)

for %%D in (!FOUND!) do (
  call :prepend_if_missing "%%~D"
)

if not defined NEW (
  echo [path] empty path, skip
  exit /b 0
)

reg add "HKCU\Environment" /v Path /t REG_EXPAND_SZ /d "!NEW!" /f >nul
if errorlevel 1 (
  echo [path] failed to persist USER PATH
  exit /b 1
)

echo [path] persisted to USER PATH
echo [path] added dirs:
for %%D in (!FOUND!) do echo   %%~D

echo [path] done
echo [path] 注意：请关闭并重新打开 CMD/PowerShell 后再验证命令。
echo [path] Redis 命令是 redis-server / redis-cli（不是 redis）。
exit /b 0

:append_dir
set "DIR=%~1"
if not defined DIR goto :eof
if not exist "%DIR%" goto :eof
if "%DIR:~-1%"=="\" set "DIR=%DIR:~0,-1%"
if not defined FOUND (
  set "FOUND=""%DIR%""
  goto :eof
)
echo ;!FOUND!; | findstr /i /c:";\"%DIR%\";" >nul
if not errorlevel 1 goto :eof
set "FOUND=!FOUND! "%DIR%""
goto :eof

:prepend_if_missing
set "P=%~1"
if not defined P goto :eof
if not exist "%P%" goto :eof
if not defined NEW (
  set "NEW=%P%"
  goto :eof
)
echo ;!NEW!; | findstr /i /c:";%P%;" >nul
if not errorlevel 1 goto :eof
set "NEW=%P%;!NEW!"
goto :eof
