@echo off
echo 开始打包...
python -m nuitka --standalone --show-progress --plugin-enable=tk-inter --output-dir=out ^
	--include-data-file=packages\install_config.json=packages\install_config.json ^
	--include-data-file=packages\get-pip.py=packages\get-pip.py ^
	--include-data-file=packages\pip-26.0.1-py3-none-any.whl=packages\pip-26.0.1-py3-none-any.whl ^
	--include-data-file=packages\setuptools-82.0.0-py3-none-any.whl=packages\setuptools-82.0.0-py3-none-any.whl ^
	--include-data-file=packages\wheel-0.46.3-py3-none-any.whl=packages\wheel-0.46.3-py3-none-any.whl ^
	main.py

echo 重命名目录...
if exist out\WinPyDeploy.dist ren out\WinPyDeploy.dist WinPyDeploy
if exist out\main.dist ren out\main.dist WinPyDeploy

echo 打包完成！产物路径：out\WinPyDeploy
