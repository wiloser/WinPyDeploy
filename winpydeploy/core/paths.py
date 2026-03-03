from __future__ import annotations

import json
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

from . import user_config

DEFAULT_INSTALL_DIR = r"C:\\Program Files\\softs"


def _is_absolute_any(path: str) -> bool:
    p = Path(path)
    if p.is_absolute():
        return True
    return re.match(r"^[A-Za-z]:[\\/]", str(path)) is not None


def project_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[2]


def packages_dir() -> Path:
    global _PKG_OVERRIDE
    if _PKG_OVERRIDE is not None:
        return _PKG_OVERRIDE
    cfg = user_config.load()
    if cfg.packages_dir:
        p = Path(cfg.packages_dir).expanduser()
        if p.is_absolute():
            return p
    return project_root() / "packages"


_PKG_OVERRIDE: Path | None = None
_INSTALL_OVERRIDE: Path | None = None


def set_packages_dir(path: str) -> None:
    global _PKG_OVERRIDE
    _PKG_OVERRIDE = Path(path).expanduser() if path else None


def install_dir() -> Path | None:
    global _INSTALL_OVERRIDE
    if _INSTALL_OVERRIDE is not None:
        return _INSTALL_OVERRIDE
    cfg = user_config.load()
    if cfg.install_dir:
        raw = str(cfg.install_dir).strip()
        if _is_absolute_any(raw):
            return Path(raw).expanduser()
    # tool is Windows-first; provide a sensible default
    return Path(DEFAULT_INSTALL_DIR)


def set_install_dir(path: str) -> None:
    global _INSTALL_OVERRIDE
    _INSTALL_OVERRIDE = Path(path).expanduser() if path else None


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


def _bundled_packages_file(name: str) -> Path | None:
    base = getattr(sys, "_MEIPASS", None)
    if not base:
        return None
    p = (Path(base) / "packages" / name).resolve()
    return p if p.exists() else None


def ensure_install_config() -> Path:
    ensure_packages_dir()
    path = install_config_path()
    if not path.exists():
        bundled = _bundled_install_config()
        if bundled:
            shutil.copyfile(bundled, path)
            return path
        src = project_root() / "packages" / "install_config.json"
        if src.exists():
            shutil.copyfile(src, path)
            return path
        default_config = {
            "schemaVersion": 1,
            "createdAt": datetime.now(timezone.utc).isoformat(),
            "notes": "用于标识安装包与安装策略的元信息（可按需扩展字段）",
            "apps": {},
        }
        path.write_text(json.dumps(default_config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    scripts = packages_dir() / "scripts"; scripts.mkdir(parents=True, exist_ok=True)
    for name in ("install_python.cmd", "install_mysql.cmd", "install_redis.cmd"):
        dst = scripts / name
        if dst.exists():
            try:
                b = dst.read_bytes()
                # Legacy buggy pattern that can break REG ADD when PATH contains quotes.
                if b"| find /i \"Path\"" not in b and b"^| find /i \"Path\"" not in b:
                    continue
            except Exception:
                continue
        bundled = _bundled_packages_file(f"scripts/{name}")
        src = bundled or (project_root() / "packages" / "scripts" / name)
        if src.exists():
            shutil.copyfile(src, dst)

    return path
