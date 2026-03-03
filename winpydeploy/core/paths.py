from __future__ import annotations

import json
import os
import platform
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


_INJECT_CACHE_ROOT: str | None = None
_INJECT_CACHE_DIRS: list[str] | None = None


def _compute_injected_dirs(install_root: str) -> list[str]:
    root = Path(install_root)
    dirs: list[str] = []

    def add_dir(p: Path) -> None:
        try:
            if p.exists() and p.is_dir():
                dirs.append(str(p))
        except Exception:
            return

    def add_parent_of_first_exe(base: Path, exe_names: tuple[str, ...]) -> None:
        try:
            if not base.exists() or not base.is_dir():
                return
        except Exception:
            return
        for exe in exe_names:
            try:
                for hit in base.rglob(exe):
                    add_dir(hit.parent)
                    return
            except Exception:
                continue

    # Python
    py = root / "Python312"
    if (py / "python.exe").exists():
        add_dir(py)
    else:
        add_parent_of_first_exe(py, ("python.exe",))
    if (py / "Scripts" / "pip.exe").exists():
        add_dir(py / "Scripts")

    # MySQL
    mysql = root / "MySQL"
    if (mysql / "bin").exists():
        add_dir(mysql / "bin")
    else:
        add_parent_of_first_exe(mysql, ("mysqld.exe", "mysql.exe"))

    # Redis
    redis = root / "Redis"
    add_dir(redis)
    if (redis / "bin").exists():
        add_dir(redis / "bin")
    add_parent_of_first_exe(redis, ("redis-server.exe", "redis-cli.exe"))

    # Stable order + remove duplicates (case-insensitive on Windows)
    out: list[str] = []
    seen: set[str] = set()
    for d in dirs:
        n = d.strip().lower()
        if n and n not in seen:
            out.append(d)
            seen.add(n)
    return out


def _build_injected_path(install_root: str, current_path: str) -> str:
    """Build a PATH with our known install locations prepended.

    This does NOT write registry; it only affects subprocess environments.
    """
    global _INJECT_CACHE_ROOT, _INJECT_CACHE_DIRS
    if _INJECT_CACHE_ROOT != install_root or _INJECT_CACHE_DIRS is None:
        _INJECT_CACHE_ROOT = install_root
        _INJECT_CACHE_DIRS = _compute_injected_dirs(install_root)

    candidates = _INJECT_CACHE_DIRS
    if not candidates:
        return current_path or ""

    existing = [x for x in (current_path or "").split(os.pathsep) if x]
    existing_norm = {x.strip().lower() for x in existing}
    injected: list[str] = []
    for c in candidates:
        n = c.strip().lower()
        if n and n not in existing_norm:
            injected.append(c)
            existing_norm.add(n)

    if not injected:
        return current_path or ""
    return os.pathsep.join(injected + existing)


def runtime_env() -> dict[str, str]:
    ins = install_dir()
    pkg = packages_dir()
    env = {
        "WINPYDEPLOY_PACKAGES_DIR": str(pkg),
        "WINPYDEPLOY_INSTALL_DIR": str(ins) if ins is not None else DEFAULT_INSTALL_DIR,
    }
    if platform.system().lower() == "windows":
        env["PATH"] = _build_injected_path(env["WINPYDEPLOY_INSTALL_DIR"], os.environ.get("PATH", ""))
    return env


def expand_with_runtime_env(text: str) -> str:
    env = {k.upper(): v for k, v in {**os.environ, **runtime_env()}.items()}

    def repl(m: re.Match[str]) -> str:
        key = m.group(1).upper()
        return env.get(key, m.group(0))

    return re.sub(r"%([^%]+)%", repl, text)


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


def _bundled_scripts_dir() -> Path | None:
    base = getattr(sys, "_MEIPASS", None)
    if not base:
        return None
    p = (Path(base) / "packages" / "scripts").resolve()
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

    scripts = packages_dir() / "scripts"
    scripts.mkdir(parents=True, exist_ok=True)

    # Sync all cmd scripts shipped with the app.
    # Priority: frozen/runtime (project_root) first, then PyInstaller bundle fallback.
    src_dirs: list[Path] = []
    pr = (project_root() / "packages" / "scripts").resolve()
    if pr.exists():
        src_dirs.append(pr)
    bsd = _bundled_scripts_dir()
    if bsd and bsd.exists():
        src_dirs.append(bsd)

    def should_overwrite(name: str, existing: bytes) -> bool:
        # Never clobber user-provided custom scripts (no WinPyDeploy markers)
        if b"WinPyDeploy" not in existing and b"PATH is injected" not in existing:
            return False

        if name.startswith("install_"):
            if b"WINPYDEPLOY_INSTALL_DIR" not in existing or b"PATH is injected" not in existing:
                return True
            # Require flattening logic for our zip installers
            if name in ("install_python.cmd", "install_mysql.cmd", "install_redis.cmd"):
                if not (b"robocopy" in existing and b"flattening" in existing):
                    return True
                # bump specific scripts when we strengthen flattening behavior
                if name in ("install_redis.cmd", "install_mysql.cmd", "install_python.cmd"):
                    return b"flatten-v5" not in existing
                return False
            return False

        if name.startswith("info_"):
            if b"WINPYDEPLOY_INSTALL_DIR" not in existing or b"WinPyDeploy helper script" not in existing:
                return True
            # Require quote sanitization lines (any one of them indicates new helper style)
            if b"%SERVER:\"=%" in existing or b"%MYSQD:\"=%" in existing or b"%PY:\"=%" in existing:
                return False
            return True

        if name.startswith("manage_"):
            if b"WinPyDeploy helper script" not in existing:
                return True
            # New manage scripts should prefer PATH lookup via `where`
            return b"where " not in existing

        # Default: keep existing
        return False

    for src_dir in src_dirs:
        for src in src_dir.glob("*.cmd"):
            dst = scripts / src.name
            if dst.exists():
                try:
                    existing = dst.read_bytes()
                    if not should_overwrite(src.name, existing):
                        continue
                except Exception:
                    continue
            try:
                shutil.copyfile(src, dst)
            except Exception:
                pass

    return path
