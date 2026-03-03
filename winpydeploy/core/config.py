from __future__ import annotations
import json
from pathlib import Path
from .models import AppSpec
from .paths import ensure_install_config, install_config_path, packages_dir, install_dir
from ..utils.spec_tools import parse_extra_files

def _safe_package_path(package_file: str) -> str:
    base = packages_dir().resolve()
    candidate = (base / package_file).resolve()
    if base != candidate and base not in candidate.parents:
        raise ValueError(f"packageFile 不允许越出 packages/: {package_file}")
    return str(candidate)

def _commands_from_package(app_id: str, spec: dict) -> list[str]:
    package_file = spec.get("packageFile")
    if not package_file:
        return []
    installer_type = str(spec.get("installerType") or "exe").lower()
    silent_args = str(spec.get("silentArgs") or "").strip()
    path = _safe_package_path(str(package_file))
    if installer_type == "msi":
        return [f'msiexec /i "{path}" /qn']
    if installer_type == "zip":
        target_dir = str(spec.get("targetDir") or spec.get("target_dir") or "").strip()
        if not target_dir:
            root = install_dir()
            if root is not None:
                target_dir = str(root / app_id)
        if not target_dir:
            target_dir = r"C:\\Python312"
        return [f'mkdir "{target_dir}" 2>nul & tar -xf "{path}" -C "{target_dir}"']
    if installer_type == "exe":
        return [f'"{path}" {silent_args}'.rstrip()]
    return [f'"{path}" {silent_args}'.rstrip()]

def _commands_from_script(spec: dict) -> list[str]:
    script = str(spec.get("installScript") or spec.get("install_script") or "").strip()
    if not script:
        return []
    return [f'"{_safe_package_path(script)}"']

def load_catalog(config_path: Path | None = None) -> tuple[AppSpec, ...]:
    path = config_path or install_config_path()
    if not path.exists():
        ensure_install_config()
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

        expected = spec.get("expectedPaths") or spec.get("expected_paths") or []
        expected_paths = tuple(str(p).strip() for p in expected if str(p).strip())
        if not expected_paths and str(spec.get("installerType") or "").lower() == "zip":
            td = str(spec.get("targetDir") or spec.get("target_dir") or "").strip()
            if td:
                expected_paths = (td,)

        info = spec.get("infoCommands") or spec.get("info_commands") or []
        info_commands = tuple(str(c) for c in info if str(c).strip())

        commands = spec.get("installCommands") or spec.get("install_commands") or _commands_from_script(spec) or _commands_from_package(str(app_id), spec) or []
        install_commands = tuple(str(c) for c in commands if str(c).strip())

        post = spec.get("postInstallCommands") or spec.get("post_install_commands") or []
        post_install_commands = [str(c) for c in post if str(c).strip()]

        post_script = str(spec.get("postInstallScript") or spec.get("post_install_script") or "").strip()
        if post_script:
            post_install_commands.insert(0, f'"{_safe_package_path(post_script)}"')

        package_path = ""
        package_file = spec.get("packageFile")
        if package_file:
            package_path = _safe_package_path(str(package_file))
        download_url = str(spec.get("downloadUrl") or spec.get("download_url") or "").strip()
        sha256 = str(spec.get("sha256") or "").strip()

        extra_files = parse_extra_files(spec, _safe_package_path)

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
                expected_paths=expected_paths,
                info_commands=info_commands,
                post_install_commands=tuple(post_install_commands),
                notes=notes,
            )
        )

    catalog.sort(key=lambda a: a.app_id)
    return tuple(catalog)
