from __future__ import annotations

import os
import platform
import subprocess
from pathlib import Path

from .models import AppSpec
from .paths import expand_with_runtime_env, runtime_env


def _run_check(cmd: str) -> bool:
    try:
        env = {**os.environ, **runtime_env()}
        cmd = expand_with_runtime_env(cmd)
        r = subprocess.run(
            cmd,
            shell=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=8,
            env=env,
        )
    except Exception:
        return False
    return r.returncode == 0


def detect_installed_apps(apps: tuple[AppSpec, ...]) -> dict[str, bool]:
    if platform.system().lower() != "windows":
        return {a.app_id: False for a in apps}

    result: dict[str, bool] = {}
    for app in apps:
        expected_ok = True
        if getattr(app, "expected_paths", ()):  # backward compat with older cached objects
            for raw in app.expected_paths:
                p = expand_with_runtime_env(raw)
                if not p:
                    continue
                if not Path(p).exists():
                    expected_ok = False
                    break

        cmds = app.detect_commands
        if cmds:
            result[app.app_id] = expected_ok and all(_run_check(c) for c in cmds)
        else:
            result[app.app_id] = expected_ok and bool(getattr(app, "expected_paths", ()))
    return result
