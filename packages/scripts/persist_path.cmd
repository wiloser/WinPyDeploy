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

set "CAND="
if exist "%PY%" set "CAND=%CAND%;%PY%"
if exist "%PYS%" set "CAND=%CAND%;%PYS%"
if exist "%MY%" set "CAND=%CAND%;%MY%"
if exist "%RD%" set "CAND=%CAND%;%RD%"
if exist "%RDB%" set "CAND=%CAND%;%RDB%"

if "%CAND%"=="" (
  echo [path] no candidate dirs found under "%ROOT%"
  exit /b 0
)

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$ErrorActionPreference='Stop';" ^
  "$cand = @();" ^
  "foreach($p in @($env:PY,$env:PYS,$env:MY,$env:RD,$env:RDB)){ if($p -and (Test-Path -LiteralPath $p)){ $cand += $p } }" ^
  "if($cand.Count -eq 0){ Write-Host '[path] no candidate dirs found'; exit 0 }" ^
  "$old = [Environment]::GetEnvironmentVariable('Path','User');" ^
  "if(-not $old){ $old = '' }" ^
  "$parts = @();" ^
  "foreach($x in $old -split ';'){ if($x){ $parts += $x } }" ^
  "$seen = New-Object 'System.Collections.Generic.HashSet[string]' ([StringComparer]::OrdinalIgnoreCase);" ^
  "$out = New-Object System.Collections.Generic.List[string];" ^
  "foreach($x in $cand + $parts){ if(-not [string]::IsNullOrWhiteSpace($x)){ if($seen.Add($x)){ [void]$out.Add($x) } } }" ^
  "$newPath = ($out -join ';');" ^
  "[Environment]::SetEnvironmentVariable('Path',$newPath,'User');" ^
  "Write-Host ('[path] persisted to USER PATH, entries=' + $out.Count)"
if errorlevel 1 (
  echo [path] failed to persist USER PATH
  exit /b 1
)

echo [path] done
exit /b 0
