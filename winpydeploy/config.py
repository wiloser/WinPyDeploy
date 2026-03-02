from __future__ import annotations
import json
from pathlib import Path
from .models import AppSpec
from .paths import install_config_path, packages_dir
from .spec_tools import apply_pip_bootstrap, parse_extra_files

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
    if installer_type == "zip":
        target_dir = str(spec.get("targetDir") or spec.get("target_dir") or r"C:\\Python312").strip()
        ps = (
            "powershell -NoProfile -ExecutionPolicy Bypass -Command "
            f"\"$src='{path}';$dst='{target_dir}';"
            "Unblock-File -LiteralPath $src -ErrorAction SilentlyContinue;"
            "New-Item -ItemType Directory -Force -Path $dst | Out-Null;"
            "Expand-Archive -LiteralPath $src -DestinationPath $dst -Force\""
        )
        return [ps]
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

        detect = spec.get("detectCommands") or spec.get("detect_commands") or []
        detect_commands = tuple(str(c) for c in detect if str(c).strip())

        commands = spec.get("installCommands") or spec.get("install_commands")
        if not commands:
            commands = _commands_from_package(spec)
        if not commands:
            commands = []
        install_commands = tuple(str(c) for c in commands if str(c).strip())

        post = spec.get("postInstallCommands") or spec.get("post_install_commands") or []
        post_install_commands = [str(c) for c in post if str(c).strip()]

        package_path = ""
        package_file = spec.get("packageFile")
        if package_file:
            package_path = _safe_package_path(str(package_file))
        download_url = str(spec.get("downloadUrl") or spec.get("download_url") or "").strip()
        sha256 = str(spec.get("sha256") or "").strip()

        extra_files = parse_extra_files(spec, _safe_package_path)
        post_install_commands_t = apply_pip_bootstrap(spec, extra_files, post_install_commands)

        catalog.append(
            AppSpec(
                app_id=str(app_id),
                name=name,
                detect_keywords=detect_keywords,
                install_commands=install_commands,
                package_path=package_path,
                download_url=download_url,
                sha256=sha256,
                extra_files=extra_files,
                detect_commands=detect_commands,
                post_install_commands=post_install_commands_t,
                notes=notes,
            )
        )

    catalog.sort(key=lambda a: a.app_id)
    return tuple(catalog)
