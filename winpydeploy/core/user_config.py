from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class UserConfig:
    packages_dir: str = ""
    install_dir: str = ""


def _config_dir() -> Path:
    if sys.platform.startswith("win"):
        base = os.environ.get("APPDATA") or str(Path.home() / "AppData" / "Roaming")
        return Path(base) / "WinPyDeploy"
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "WinPyDeploy"
    base = os.environ.get("XDG_CONFIG_HOME") or str(Path.home() / ".config")
    return Path(base) / "winpydeploy"


def config_path() -> Path:
    return _config_dir() / "user_config.json"


def load() -> UserConfig:
    p = config_path()
    try:
        d = json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}
        return UserConfig(
            packages_dir=str(d.get("packagesDir") or "").strip(),
            install_dir=str(d.get("installDir") or "").strip(),
        )
    except Exception:
        return UserConfig()


def save(cfg: UserConfig) -> None:
    p = config_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(
        json.dumps(
            {"packagesDir": cfg.packages_dir, "installDir": cfg.install_dir},
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
