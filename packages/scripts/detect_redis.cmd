@echo off
setlocal EnableExtensions
rem WinPyDeploy helper script (no registry writes)

set "ROOT=%WINPYDEPLOY_INSTALL_DIR%"
if not defined ROOT set "ROOT=C:\Program Files\softs"
set "BASE=%ROOT%\Redis"

if not exist "%BASE%" exit /b 1

set "FOUND="
for /r "%BASE%" %%F in (redis-server.exe) do if not defined FOUND set "FOUND=%%~fF"

if defined FOUND set "FOUND=%FOUND:"=%"

if defined FOUND exit /b 0
exit /b 1
