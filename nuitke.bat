@echo off
setlocal enableextensions enabledelayedexpansion

rem Use UTF-8 codepage to avoid garbled output on modern Windows terminals.
chcp 65001 >nul
set PYTHONIOENCODING=utf-8

set "OUT=out"
set "APP=WinPyDeploy"
set "ARCH=%OUT%\archives"
set "REL=%OUT%\release"

if not exist "%OUT%" mkdir "%OUT%" >nul 2>nul
if not exist "%ARCH%" mkdir "%ARCH%" >nul 2>nul
if not exist "%REL%" mkdir "%REL%" >nul 2>nul

echo Build starting...

python -m pip install --upgrade nuitka

python -m nuitka --standalone --show-progress --plugin-enable=tk-inter --output-dir=out ^
	--assume-yes-for-downloads ^
	--remove-output ^
	--windows-console-mode=disable ^
	--file-reference-choice=runtime ^
	--lto=yes ^
	--include-data-file=packages\install_config.json=packages\install_config.json ^
	--include-data-file=packages\scripts\install_python.cmd=packages\scripts\install_python.cmd ^
	--include-data-file=packages\scripts\install_mysql.cmd=packages\scripts\install_mysql.cmd ^
	--include-data-file=packages\scripts\install_redis.cmd=packages\scripts\install_redis.cmd ^
	main.py

if errorlevel 1 (
	echo ERROR: Nuitka build failed.
	exit /b %errorlevel%
)

echo Normalizing output folder...

rem Archive existing output (prevents rename errors when output already exists)
if exist "%OUT%\%APP%" (
	for /f %%T in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd_HHmmss"') do set "TS=%%T"
	echo Archiving existing %OUT%\%APP% to %ARCH%\%APP%_!TS! ...
	move "%OUT%\%APP%" "%ARCH%\%APP%_!TS!" >nul
)

set "DIST="
if exist "%OUT%\%APP%.dist" set "DIST=%OUT%\%APP%.dist"
if not defined DIST if exist "%OUT%\main.dist" set "DIST=%OUT%\main.dist"
if not defined DIST (
	echo ERROR: dist folder not found under %OUT%.
	exit /b 2
)

move "%DIST%" "%OUT%\%APP%" >nul

rem Rename exe to a stable name
if exist "%OUT%\%APP%\main.exe" ren "%OUT%\%APP%\main.exe" "%APP%.exe" >nul

rem Create a zip archive of the new build (optional but handy for distribution)
for /f %%T in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd_HHmmss"') do set "TS=%%T"
powershell -NoProfile -Command "if(Test-Path '%OUT%\\%APP%'){Compress-Archive -Force -Path '%OUT%\\%APP%\\*' -DestinationPath '%REL%\\%APP%_!TS!.zip'}" >nul

rem Move expanded folder into archives (keeps workspace tidy; zip is the deliverable)
if exist "%OUT%\%APP%" move "%OUT%\%APP%" "%ARCH%\%APP%_!TS!" >nul

echo Done. Deliverable: %REL%\%APP%_!TS!.zip
echo Expanded folder archived to: %ARCH%\%APP%_!TS!

endlocal
