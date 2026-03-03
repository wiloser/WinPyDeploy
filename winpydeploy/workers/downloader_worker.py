from __future__ import annotations

import concurrent.futures as cf
import queue
import threading
from dataclasses import dataclass
from pathlib import Path

from ..utils.downloader import ensure_package
from ..core.models import AppSpec


@dataclass(frozen=True)
class DownloadEvent:
    kind: str
    app_id: str
    message: str = ""


class DownloadWorker:
    def __init__(self, event_queue: "queue.Queue[DownloadEvent]"):
        self._q = event_queue
        self._stop = threading.Event()
        self._cancel: dict[str, threading.Event] = {}

        def emit(kind: str, app_id: str, message: str) -> None:
            self._q.put(DownloadEvent(kind, app_id, message))

        self._emit = emit

    def stop(self) -> None:
        self._stop.set()

    def cancel_app(self, app_id: str) -> None:
        (self._cancel.get(app_id) or self._cancel.setdefault(app_id, threading.Event())).set()

    def _stop_for(self, app_id: str) -> bool:
        return self._stop.is_set() or (self._cancel.get(app_id) and self._cancel[app_id].is_set())

    def _download_one(self, app: AppSpec) -> None:
        stop = lambda: self._stop_for(app.app_id)
        if stop(): self._emit("skipped", app.app_id, "cancelled"); return
        self._emit("starting", app.app_id, f"开始下载：{app.name}")
        if app.package_path and not ensure_package(app, self._emit, stop):
            self._emit("skipped" if stop() else "failed", app.app_id, "cancelled" if stop() else "下载失败")
            return
        for f in getattr(app, "extra_files", ()):
            if stop(): self._emit("skipped", app.app_id, "cancelled"); return
            if Path(f.path).exists():
                continue
            tmp = AppSpec(app_id=app.app_id, name=app.name, detect_keywords=(), install_commands=(), package_path=f.path, download_url=f.download_url, sha256=f.sha256)
            if not ensure_package(tmp, self._emit, stop):
                self._emit("skipped" if stop() else "failed", app.app_id, "cancelled" if stop() else "下载额外文件失败")
                return
        self._emit("downloaded", app.app_id, "ok")

    def download(self, apps: list[AppSpec]) -> None:
        for a in apps: self._cancel.setdefault(a.app_id, threading.Event())
        max_w = min(4, max(1, len(apps)))
        with cf.ThreadPoolExecutor(max_workers=max_w) as ex:
            futs = [ex.submit(self._download_one, a) for a in apps]
            for f in cf.as_completed(futs):
                try: f.result()
                except Exception as e: self._emit("log", "*", f"下载线程异常：{e}")
        self._emit("download_all_done", "*", "done")
