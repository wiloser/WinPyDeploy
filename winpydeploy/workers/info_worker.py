from __future__ import annotations

import queue
import platform
import subprocess
import threading
from dataclasses import dataclass

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

    def stop(self) -> None:
        self._stop.set()

    def fetch(self, app: AppSpec) -> None:
        if platform.system().lower() != "windows":
            self._q.put(InfoEvent("info_done", app.app_id, "(开发环境模拟)\n")); return
        out: list[str] = []
        for cmd in app.info_commands:
            if self._stop.is_set():
                self._q.put(InfoEvent("info_done", app.app_id, "cancelled")); return
            out.append(f"> {cmd}")
            try:
                r = subprocess.run(cmd, shell=True, capture_output=True, text=True, errors="replace", timeout=60)
                s = (r.stdout or "") + (r.stderr or "")
            except Exception as e:
                s = str(e)
            out.append(s.strip())
        text = "\n".join(x for x in out if x is not None).strip() + "\n"
        self._q.put(InfoEvent("info_done", app.app_id, text))
