from __future__ import annotations

import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path


def project_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[1]


def packages_dir() -> Path:
    return project_root() / "packages"


def ensure_packages_dir() -> Path:
    path = packages_dir()
    path.mkdir(parents=True, exist_ok=True)
    return path


def install_config_path() -> Path:
    return packages_dir() / "install_config.json"


def _bundled_install_config() -> Path | None:
    base = getattr(sys, "_MEIPASS", None)
    if not base:
        return None
    p = (Path(base) / "packages" / "install_config.json").resolve()
    return p if p.exists() else None


def ensure_install_config() -> Path:
    ensure_packages_dir()
    path = install_config_path()
    if not path.exists():
        bundled = _bundled_install_config()
        if bundled:
            shutil.copyfile(bundled, path)
            return path
        default_config = {
            "schemaVersion": 1,
            "createdAt": datetime.now(timezone.utc).isoformat(),
            "notes": "用于标识安装包与安装策略的元信息（可按需扩展字段）",
            "apps": {},
        }
        path.write_text(json.dumps(default_config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path
