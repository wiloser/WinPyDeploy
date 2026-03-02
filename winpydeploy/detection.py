from __future__ import annotations

import platform

from .models import AppSpec


def detect_installed_apps(apps: tuple[AppSpec, ...]) -> dict[str, bool]:
    system = platform.system().lower()
    if system != "windows":
        return {a.app_id: False for a in apps}
    return {a.app_id: False for a in apps}
