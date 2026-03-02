from __future__ import annotations

import queue
import threading
from dataclasses import dataclass
from pathlib import Path

from .downloader import ensure_package
from .models import AppSpec


@dataclass(frozen=True)
class DownloadEvent:
    kind: str
    app_id: str
    message: str = ""


class DownloadWorker:
    def __init__(self, event_queue: "queue.Queue[DownloadEvent]"):
        self._q = event_queue
        self._stop = threading.Event()

        def emit(kind: str, app_id: str, message: str) -> None:
            self._q.put(DownloadEvent(kind, app_id, message))

        self._emit = emit

    def stop(self) -> None:
        self._stop.set()

    def download(self, apps: list[AppSpec]) -> None:
        for app in apps:
            if self._stop.is_set():
                self._emit("log", app.app_id, "已取消，跳过后续任务")
                self._emit("skipped", app.app_id, "cancelled")
                continue

            self._emit("starting", app.app_id, f"开始下载：{app.name}")
            if app.package_path and not ensure_package(app, self._emit, self._stop.is_set):
                self._emit("failed", app.app_id, "下载失败，停止后续任务")
                self._stop.set(); break

            for f in getattr(app, "extra_files", ()):
                if Path(f.path).exists():
                    continue
                tmp = AppSpec(app_id=app.app_id, name=app.name, detect_keywords=(), install_commands=(),
                             package_path=f.path, download_url=f.download_url, sha256=f.sha256)
                if not ensure_package(tmp, self._emit, self._stop.is_set):
                    self._emit("failed", app.app_id, "下载额外文件失败，停止后续任务")
                    self._stop.set(); break
            if self._stop.is_set():
                break

            self._emit("downloaded", app.app_id, "ok")

        self._emit("download_all_done", "*", "done")
