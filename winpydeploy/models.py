from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AppSpec:
    app_id: str
    name: str
    detect_keywords: tuple[str, ...]
    install_commands: tuple[str, ...]
    notes: str = ""


CATALOG: tuple[AppSpec, ...] = (
    AppSpec(
        app_id="7zip",
        name="7-Zip",
        detect_keywords=("7-zip", "7zip"),
        install_commands=(
            r"winget install --id 7zip.7zip --silent --accept-package-agreements --accept-source-agreements",
        ),
        notes="解压缩工具",
    ),
    AppSpec(
        app_id="git",
        name="Git",
        detect_keywords=("git",),
        install_commands=(
            r"winget install --id Git.Git --silent --accept-package-agreements --accept-source-agreements",
        ),
        notes="版本控制",
    ),
    AppSpec(
        app_id="vscode",
        name="Visual Studio Code",
        detect_keywords=("visual studio code", "vscode"),
        install_commands=(
            r"winget install --id Microsoft.VisualStudioCode --silent --accept-package-agreements --accept-source-agreements",
        ),
        notes="编辑器",
    ),
)
