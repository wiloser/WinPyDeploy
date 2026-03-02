from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AppSpec:
    app_id: str
    name: str
    detect_keywords: tuple[str, ...]
    install_commands: tuple[str, ...]
    notes: str = ""
