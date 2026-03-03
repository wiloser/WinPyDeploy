@echo off
setlocal enableextensions

echo 开始打包...

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

echo 重命名目录...
if exist out\WinPyDeploy.dist ren out\WinPyDeploy.dist WinPyDeploy
if exist out\main.dist ren out\main.dist WinPyDeploy

echo 打包完成！产物路径：out\WinPyDeploy

endlocal
