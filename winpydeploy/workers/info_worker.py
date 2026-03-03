from __future__ import annotations

import queue
import platform
import subprocess
import threading
from dataclasses import dataclass
from time import monotonic

from ..core.models import AppSpec


@dataclass(frozen=True)
class InfoEvent:
    kind: str
    app_id: str
    message: str = ""


class InfoWorker:
    def __init__(self, event_q: "queue.Queue[InfoEvent]"):
        self._q = event_q
        self._stop = threading.Event()
        self._proc: subprocess.Popen[str] | None = None

    def stop(self) -> None:
        self._stop.set()
        proc = self._proc
        if proc and proc.poll() is None:
            try:
                proc.terminate()
            except Exception:
                pass

    def fetch(self, app: AppSpec) -> None:
        if platform.system().lower() != "windows":
            self._q.put(InfoEvent("info_done", app.app_id, "(开发环境模拟)\n")); return
        out: list[str] = []
        for cmd in app.info_commands:
            if self._stop.is_set():
                self._q.put(InfoEvent("info_done", app.app_id, "cancelled")); return
            out.append(f"> {cmd}")
            try:
                self._proc = subprocess.Popen(
                    cmd,
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    errors="replace",
                )
                assert self._proc.stdout is not None
                # infoCommands should be quick; keep UI responsive even on false positives
                timeout_s = 10.0
                start = monotonic()
                chunks: list[str] = []
                while True:
                    if self._stop.is_set():
                        self.stop()
                        self._q.put(InfoEvent("info_done", app.app_id, "cancelled")); return
                    if (monotonic() - start) > timeout_s:
                        self.stop()
                        chunks.append(f"(timeout after {int(timeout_s)}s)")
                        break
                    line = self._proc.stdout.readline()
                    if line:
                        chunks.append(line.rstrip("\n"))
                        continue
                    if self._proc.poll() is not None:
                        break
                try:
                    rest = self._proc.stdout.read()
                    if rest:
                        chunks.append(rest.rstrip("\n"))
                except Exception:
                    pass
                s = "\n".join([c for c in chunks if c.strip()])
            except Exception as e:
                s = str(e)
            out.append(s.strip())
        text = "\n".join(x for x in out if x is not None).strip() + "\n"
        self._q.put(InfoEvent("info_done", app.app_id, text))
