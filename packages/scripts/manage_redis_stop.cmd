@echo off
setlocal EnableExtensions
rem WinPyDeploy helper script (no registry writes)

taskkill /IM redis-server.exe /F >nul 2>nul
if errorlevel 1 (
  echo redis-server.exe not running
  exit /b 0
)

echo redis-server.exe stopped
exit /b 0
