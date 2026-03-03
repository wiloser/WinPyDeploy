from __future__ import annotations

import platform
import subprocess
import time
import os
import locale
from collections.abc import Callable
from pathlib import Path

from ..core.paths import expand_with_runtime_env, runtime_env


def _windows_cmd_encoding() -> str:
    env_enc = (os.environ.get("WINPYDEPLOY_CMD_ENCODING") or "").strip()
    if env_enc:
        return env_enc
    try:
        return locale.getpreferredencoding(False) or "gbk"
    except Exception:
        return "gbk"


class CommandRunner:
    def __init__(self, emit: Callable[[str, str, str], None]):
        self._emit = emit
        self._proc: subprocess.Popen[str] | None = None

    def terminate(self) -> None:
        proc = self._proc
        if proc and proc.poll() is None:
            try:
                proc.terminate()
            except Exception:
                pass

    def run(self, *, app_id: str, cmd: str, check_installer_path: bool = True) -> int:
        cmd = expand_with_runtime_env(cmd)
        self._emit("log", app_id, f"  {cmd}")
        if platform.system().lower() != "windows":
            time.sleep(0.25)
            return 0

        if check_installer_path:
            path = self._extract_installer_path(cmd)
            if path and not Path(path).exists():
                self._emit("log", app_id, f"安装包不存在：{path}")
                return 2

        popen_cmd: str | list[str] = cmd
        popen_shell = True

        # For .cmd/.bat script paths, force execution through `cmd /c call` so
        # batch `exit /b <code>` is propagated reliably.
        script_path = self._extract_installer_path(cmd)
        s = cmd.strip()
        if script_path and s == f'"{script_path}"' and Path(script_path).suffix.lower() in {".cmd", ".bat"}:
            popen_cmd = ["cmd.exe", "/d", "/c", "call", script_path]
            popen_shell = False

        self._proc = subprocess.Popen(
            popen_cmd,
            shell=popen_shell,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding=_windows_cmd_encoding(),
            errors="replace",
            bufsize=1,
            env={**os.environ, **runtime_env()},
        )
        assert self._proc.stdout is not None
        for line in self._proc.stdout:
            line = line.rstrip("\n")
            if line:
                self._emit("log", app_id, line)
        code = self._proc.wait()
        if code != 0:
            self._emit("log", app_id, f"命令退出码：{code}")
        return code

    @staticmethod
    def _extract_installer_path(cmd: str) -> str | None:
        s = cmd.strip()
        if s.startswith('"'):
            end = s.find('"', 1)
            return s[1:end] if end > 1 else None
        if s.lower().startswith("msiexec"):
            first = s.find('"')
            if first >= 0:
                second = s.find('"', first + 1)
                return s[first + 1 : second] if second > first else None
        return None
