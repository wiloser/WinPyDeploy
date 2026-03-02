# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path

block_cipher = None

root = Path(__file__).resolve().parent

# Bundle defaults; runtime will copy them into ./packages/ on first run
datas = [
    (str(root / "packages" / "install_config.json"), "packages"),
    (str(root / "packages" / "get-pip.py"), "packages"),
]


a = Analysis(
    [str(root / "winpydeploy" / "__main__.py")],
    pathex=[str(root)],
    binaries=[],
    datas=datas,
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="WinPyDeploy",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
)
