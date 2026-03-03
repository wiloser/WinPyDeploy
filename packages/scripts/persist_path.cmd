@echo off
setlocal EnableExtensions EnableDelayedExpansion
rem WinPyDeploy helper script: persist selected install dirs into USER PATH (CMD only)

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
if not exist "%RDB%\redis-server.exe" if not exist "%RDB%\redis-cli.exe" set "RDB="

if not defined PY if exist "%ROOT%\Python312" (
  for /r "%ROOT%\Python312" %%F in (python.exe) do if not defined PY set "PY=%%~dpF"
)
if not defined PYS if exist "%ROOT%\Python312" (
  for /r "%ROOT%\Python312" %%F in (pip.exe) do if not defined PYS set "PYS=%%~dpF"
)
if not defined MY if exist "%ROOT%\MySQL" (
  for /r "%ROOT%\MySQL" %%F in (mysqld.exe) do if not defined MY set "MY=%%~dpF"
)
if not defined RD if exist "%ROOT%\Redis" (
  for /r "%ROOT%\Redis" %%F in (redis-server.exe) do if not defined RD set "RD=%%~dpF"
)
if not defined RDB if exist "%ROOT%\Redis" (
  for /r "%ROOT%\Redis" %%F in (redis-cli.exe) do if not defined RDB set "RDB=%%~dpF"
)

for %%V in (PY PYS MY RD RDB) do (
  call :trim_trailing_bslash %%V
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

set "ADDED="
call :add_unique "%PY%"
call :add_unique "%PYS%"
call :add_unique "%MY%"
call :add_unique "%RD%"
call :add_unique "%RDB%"

if not defined ADDED (
  echo [path] no new dirs to add
  exit /b 0
)

reg add "HKCU\Environment" /v Path /t REG_EXPAND_SZ /d "!NEW!" /f >nul
if errorlevel 1 (
  echo [path] failed to persist USER PATH
  exit /b 1
)

echo [path] persisted to USER PATH
echo [path] added dirs:
for %%D in (!ADDED!) do echo   %%~D

echo [path] done
echo [path] reopen CMD/PowerShell to pick up changes.
echo [path] Redis commands are redis-server / redis-cli (not redis).
exit /b 0

:trim_trailing_bslash
set "N=%~1"
call set "VAL=%%%N%%%"
if not defined VAL goto :eof
if "%VAL:~-1%"=="\" set "VAL=%VAL:~0,-1%"
call set "%N%=%VAL%"
goto :eof

:add_unique
set "P=%~1"
if not defined P goto :eof
if not exist "%P%" goto :eof

set "EXISTS=0"
if defined NEW (
  for %%K in ("!NEW:;=" "!") do (
    if /i "%%~K"=="!P!" set "EXISTS=1"
  )
)
if "%EXISTS%"=="1" goto :eof

if defined NEW (
  set "NEW=%P%;!NEW!"
) else (
  set "NEW=%P%"
)

if defined ADDED (
  set "ADDED=!ADDED! "%P%""
) else (
  set "ADDED="%P%""
)

goto :eof
