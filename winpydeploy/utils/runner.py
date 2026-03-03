from __future__ import annotations

import platform
import subprocess
import time
from collections.abc import Callable
from pathlib import Path


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
        self._emit("log", app_id, f"  {cmd}")
        if platform.system().lower() != "windows":
            time.sleep(0.25)
            return 0

        if check_installer_path:
            path = self._extract_installer_path(cmd)
            if path and not Path(path).exists():
                self._emit("log", app_id, f"安装包不存在：{path}")
                return 2

        self._proc = subprocess.Popen(
            cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            errors="replace",
            bufsize=1,
        )
        assert self._proc.stdout is not None
        for line in self._proc.stdout:
            line = line.rstrip("\n")
            if line:
                self._emit("log", app_id, line)
        return self._proc.wait()

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
