@echo off
setlocal EnableExtensions EnableDelayedExpansion
rem WinPyDeploy helper script: persist selected install dirs into USER PATH

set "ROOT=%WINPYDEPLOY_INSTALL_DIR%"
if not defined ROOT set "ROOT=C:\Program Files\softs"

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$ErrorActionPreference='Stop';" ^
  "$root = $env:ROOT;" ^
  "if(-not (Test-Path -LiteralPath $root)){ Write-Host ('[path] install root not found: ' + $root); exit 0 }" ^
  "$targets = @('python.exe','pip.exe','mysqld.exe','mysql.exe','redis-server.exe','redis-cli.exe');" ^
  "$cand = New-Object System.Collections.Generic.List[string];" ^
  "foreach($t in $targets){" ^
  "  Get-ChildItem -LiteralPath $root -Recurse -File -Filter $t -ErrorAction SilentlyContinue | ForEach-Object {" ^
  "    $d = $_.DirectoryName; if($d){ [void]$cand.Add($d) }" ^
  "  }" ^
  "}" ^
  "if($cand.Count -eq 0){ Write-Host ('[path] no executable dirs found under ' + $root); exit 0 }" ^
  "$old = [Environment]::GetEnvironmentVariable('Path','User'); if(-not $old){ $old = '' }" ^
  "$parts = @(); foreach($x in $old -split ';'){ if($x){ $parts += $x } }" ^
  "$seen = New-Object 'System.Collections.Generic.HashSet[string]' ([StringComparer]::OrdinalIgnoreCase);" ^
  "$out = New-Object System.Collections.Generic.List[string];" ^
  "foreach($x in $cand + $parts){ if(-not [string]::IsNullOrWhiteSpace($x)){ if($seen.Add($x)){ [void]$out.Add($x) } } }" ^
  "$newPath = ($out -join ';');" ^
  "[Environment]::SetEnvironmentVariable('Path',$newPath,'User');" ^
  "Write-Host ('[path] persisted to USER PATH, entries=' + $out.Count);" ^
  "Write-Host '[path] added dirs:';" ^
  "foreach($d in ($cand | Select-Object -Unique)){ Write-Host ('  ' + $d) }"
if errorlevel 1 (
  echo [path] failed to persist USER PATH
  exit /b 1
)

echo [path] done
echo [path] 注意：请关闭并重新打开 CMD/PowerShell 后再验证命令。
echo [path] Redis 命令是 redis-server / redis-cli（不是 redis）。
exit /b 0
