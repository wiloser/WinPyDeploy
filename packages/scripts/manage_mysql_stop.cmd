@echo off
setlocal EnableExtensions
rem WinPyDeploy helper script (no registry writes)

taskkill /IM mysqld.exe /F >nul 2>nul
if errorlevel 1 (
  echo mysqld.exe not running
  exit /b 0
)

echo mysqld.exe stopped
exit /b 0
