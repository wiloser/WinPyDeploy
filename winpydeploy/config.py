from __future__ import annotations

import json
from pathlib import Path

from .models import AppSpec
from .paths import install_config_path, packages_dir


def _safe_package_path(package_file: str) -> str:
    base = packages_dir().resolve()
    candidate = (base / package_file).resolve()
    if base != candidate and base not in candidate.parents:
        raise ValueError(f"packageFile 不允许越出 packages/: {package_file}")
    return str(candidate)


def _commands_from_package(spec: dict) -> list[str]:
    package_file = spec.get("packageFile")
    if not package_file:
        return []
    installer_type = str(spec.get("installerType") or "exe").lower()
    silent_args = str(spec.get("silentArgs") or "").strip()
    path = _safe_package_path(str(package_file))
    if installer_type == "msi":
        return [f'msiexec /i "{path}" /qn']
    if installer_type == "exe":
        return [f'"{path}" {silent_args}'.rstrip()]
    return [f'"{path}" {silent_args}'.rstrip()]


def load_catalog(config_path: Path | None = None) -> tuple[AppSpec, ...]:
    path = config_path or install_config_path()
    data = json.loads(path.read_text(encoding="utf-8"))
    apps: dict[str, dict] = data.get("apps", {})

    catalog: list[AppSpec] = []
    for app_id, spec in apps.items():
        if str(app_id).startswith("_"):
            continue
        if not isinstance(spec, dict):
            continue
        name = str(spec.get("name") or app_id)
        notes = str(spec.get("notes") or "")

        keywords = spec.get("detectKeywords") or spec.get("detect_keywords") or []
        detect_keywords = tuple(str(k).lower() for k in keywords if str(k).strip())
        if not detect_keywords:
            detect_keywords = (name.lower(), app_id.lower())

        commands = spec.get("installCommands") or spec.get("install_commands")
        if not commands:
            commands = _commands_from_package(spec)
        if not commands:
            commands = []
        install_commands = tuple(str(c) for c in commands if str(c).strip())

        catalog.append(
            AppSpec(
                app_id=str(app_id),
                name=name,
                detect_keywords=detect_keywords,
                install_commands=install_commands,
                notes=notes,
            )
        )

    catalog.sort(key=lambda a: a.app_id)
    return tuple(catalog)
