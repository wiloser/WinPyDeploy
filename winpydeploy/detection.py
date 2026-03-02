from __future__ import annotations

import platform
import subprocess

from .models import AppSpec


def _run_check(cmd: str) -> bool:
    try:
        r = subprocess.run(
            cmd,
            shell=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=8,
        )
    except Exception:
        return False
    return r.returncode == 0


def detect_installed_apps(apps: tuple[AppSpec, ...]) -> dict[str, bool]:
    if platform.system().lower() != "windows":
        return {a.app_id: False for a in apps}

    result: dict[str, bool] = {}
    for app in apps:
        cmds = app.detect_commands
        if not cmds:
            result[app.app_id] = False
            continue
        result[app.app_id] = all(_run_check(c) for c in cmds)
    return result
