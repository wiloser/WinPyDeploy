@echo off
setlocal EnableExtensions EnableDelayedExpansion
rem WinPyDeploy helper script: persist selected install dirs into USER PATH

set "ROOT=%WINPYDEPLOY_INSTALL_DIR%"
if not defined ROOT set "ROOT=C:\Program Files\softs"

set "PY=%ROOT%\Python312"
set "PYS=%ROOT%\Python312\Scripts"
set "MY=%ROOT%\MySQL\bin"
set "RD=%ROOT%\Redis"
set "RDB=%ROOT%\Redis\bin"

if not exist "%PY%\python.exe" set "PY="
if not exist "%PYS%\pip.exe" set "PYS="
if not exist "%MY%\mysql.exe" if not exist "%MY%\mysqld.exe" set "MY="
if not exist "%RD%\redis-server.exe" set "RD="
if not exist "%RDB%\redis-server.exe" set "RDB="

if not defined PY if exist "%ROOT%\Python312" (
  for /r "%ROOT%\Python312" %%F in (python.exe) do if not defined PY set "PY=%%~dpF"
  if defined PY if "!PY:~-1!"=="\" set "PY=!PY:~0,-1!"
)
if not defined PYS if exist "%ROOT%\Python312" (
  for /r "%ROOT%\Python312" %%F in (pip.exe) do if not defined PYS set "PYS=%%~dpF"
  if defined PYS if "!PYS:~-1!"=="\" set "PYS=!PYS:~0,-1!"
)
if not defined MY if exist "%ROOT%\MySQL" (
  for /r "%ROOT%\MySQL" %%F in (mysqld.exe) do if not defined MY set "MY=%%~dpF"
  if defined MY if "!MY:~-1!"=="\" set "MY=!MY:~0,-1!"
)
if not defined RD if exist "%ROOT%\Redis" (
  for /r "%ROOT%\Redis" %%F in (redis-server.exe) do if not defined RD set "RD=%%~dpF"
  if defined RD if "!RD:~-1!"=="\" set "RD=!RD:~0,-1!"
)
if not defined RDB if exist "%ROOT%\Redis" (
  for /r "%ROOT%\Redis" %%F in (redis-cli.exe) do if not defined RDB set "RDB=%%~dpF"
  if defined RDB if "!RDB:~-1!"=="\" set "RDB=!RDB:~0,-1!"
)

set "FOUND="
call :append_dir "%PY%"
call :append_dir "%PYS%"
call :append_dir "%MY%"
call :append_dir "%RD%"
call :append_dir "%RDB%"

if not defined FOUND (
  echo [path] no candidate dirs found under "%ROOT%"
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
  echo [path] failed to persist USER PATH (may exceed OS/path limits)
  exit /b 1
)

echo [path] persisted to USER PATH
echo [path] added dirs:
for %%D in (!FOUND!) do echo   %%~D

echo [path] done
echo [path] reopen CMD/PowerShell to pick up changes.
echo [path] Redis commands are redis-server / redis-cli (not redis).
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
