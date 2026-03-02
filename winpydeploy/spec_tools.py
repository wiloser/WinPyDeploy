from __future__ import annotations

from pathlib import Path

from .models import ExtraFile
from .paths import packages_dir


def parse_extra_files(spec: dict, safe_path) -> tuple[ExtraFile, ...]:
    extra = spec.get("extraFiles") or spec.get("extra_files") or []
    if not isinstance(extra, list):
        return ()
    out: list[ExtraFile] = []
    for it in extra:
        if not isinstance(it, dict):
            continue
        f = str(it.get("file") or it.get("packageFile") or "").strip()
        if not f:
            continue
        out.append(
            ExtraFile(
                path=safe_path(f),
                download_url=str(it.get("downloadUrl") or it.get("download_url") or "").strip(),
                sha256=str(it.get("sha256") or "").strip(),
            )
        )
    return tuple(out)


def apply_pip_bootstrap(spec: dict, extra_files: tuple[ExtraFile, ...], post: list[str]) -> tuple[str, ...]:
    if not (spec.get("pipBootstrap") or spec.get("pip_bootstrap")):
        return tuple(post)
    if str(spec.get("installerType") or "").lower() != "zip":
        return tuple(post)

    target_dir = str(spec.get("targetDir") or spec.get("target_dir") or r"C:\\Python312").strip()
    get_pip = next((x.path for x in extra_files if Path(x.path).name.lower() == "get-pip.py"), "")
    if not get_pip:
        return tuple(post)

    pkg = str(packages_dir().resolve())
    pth = (
        "powershell -NoProfile -ExecutionPolicy Bypass -Command "
            f"\"$r='{target_dir}';$p=Join-Path $r 'python312._pth';"
            "New-Item -ItemType Directory -Force -Path (Join-Path $r 'Lib\\site-packages') | Out-Null;"
            "if(Test-Path $p){$bak=($p+'.bak');if(-not(Test-Path $bak)){Rename-Item -Force -Path $p -NewName (Split-Path $bak -Leaf)}}\""
    )
    gp = f'"{target_dir}\\python.exe" "{get_pip}" --no-index --find-links "{pkg}"'
    return tuple([pth, gp] + post)
