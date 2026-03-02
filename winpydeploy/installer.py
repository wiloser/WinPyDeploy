from __future__ import annotations

import queue
import threading
import time
from dataclasses import dataclass

from .models import AppSpec


@dataclass(frozen=True)
class InstallEvent:
    kind: str
    app_id: str
    message: str = ""


class InstallerWorker:
    def __init__(self, event_queue: "queue.Queue[InstallEvent]"):
        self._q = event_queue
        self._stop = threading.Event()

    def stop(self) -> None:
        self._stop.set()

    def install(self, apps: list[AppSpec]) -> None:
        for app in apps:
            if self._stop.is_set():
                self._q.put(InstallEvent("log", app.app_id, "已取消，跳过后续任务"))
                self._q.put(InstallEvent("skipped", app.app_id, "cancelled"))
                continue

            self._q.put(InstallEvent("starting", app.app_id, f"开始安装：{app.name}"))
            self._q.put(InstallEvent("log", app.app_id, "(开发环境模拟) 将执行命令："))
            for cmd in app.install_commands:
                self._q.put(InstallEvent("log", app.app_id, f"  {cmd}"))

            for i in range(1, 6):
                if self._stop.is_set():
                    break
                time.sleep(0.25)
                self._q.put(InstallEvent("progress", app.app_id, str(i * 20)))

            if self._stop.is_set():
                self._q.put(InstallEvent("skipped", app.app_id, "cancelled"))
            else:
                self._q.put(InstallEvent("success", app.app_id, "ok"))
                self._q.put(InstallEvent("log", app.app_id, f"安装完成：{app.name}"))

        self._q.put(InstallEvent("all_done", "*", "done"))
