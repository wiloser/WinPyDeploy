$ErrorActionPreference = 'Stop'

python -m pip install --upgrade pip
python -m pip install pyinstaller

# Build from spec (bundles packages/install_config.json into the exe)
pyinstaller --noconfirm --clean WinPyDeploy.spec

Write-Host "Done. Output: dist/WinPyDeploy.exe"