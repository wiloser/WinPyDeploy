from __future__ import annotations

import queue
import threading
from tkinter import messagebox

from ..config import load_catalog
from ..detection import detect_installed_apps
from ..installer import InstallEvent, InstallerWorker
from ..models import AppSpec
from .view import WinPyDeployView


class WinPyDeployController:
    def __init__(self, view: WinPyDeployView, event_q: "queue.Queue[InstallEvent]"):
        self.view = view
        self._event_q = event_q
        self._worker = InstallerWorker(event_q)
        self._worker_thread: threading.Thread | None = None
        self._catalog: tuple[AppSpec, ...] = ()
        self._spec_by_id: dict[str, AppSpec] = {}
        self._installed: dict[str, bool] = {}
        self._selected: set[str] = set()

    def refresh_detection(self) -> None:
        self._catalog = load_catalog()
        self._spec_by_id = {a.app_id: a for a in self._catalog}
        self._installed = detect_installed_apps(self._catalog)
        self.view.rebuild_tree(self._catalog, self._installed, self._selected)
        self.view.log("检测完成。")

    def on_tree_select(self, _evt=None) -> None:
        self._selected = set(self.view.selection())

    def select_all_missing(self) -> None:
        missing = [a.app_id for a in self._catalog if not self._installed.get(a.app_id, False)]
        self.view.set_selection(missing); self._selected = set(missing)

    def start_install(self) -> None:
        if self._worker_thread and self._worker_thread.is_alive():
            messagebox.showinfo("提示", "正在安装中，请等待完成。"); return
        if not self._selected:
            messagebox.showinfo("提示", "请先选择要安装的软件（点击/框选）。"); return

        to_install: list[AppSpec] = []
        for app_id in list(self._selected):
            spec = self._spec_by_id.get(app_id)
            if not spec:
                continue
            if self._installed.get(app_id, False):
                self.view.log(f"跳过已安装：{spec.name}")
            else:
                to_install.append(spec)
        if not to_install:
            messagebox.showinfo("提示", "选择的软件都已安装，无需执行。"); return

        self.view.log(f"准备安装 {len(to_install)} 个软件…")
        self.view.set_busy(True)
        self._worker = InstallerWorker(self._event_q)
        self._worker_thread = threading.Thread(target=self._worker.install, args=(to_install,), daemon=True)
        self._worker_thread.start()

    def handle_event(self, ev: InstallEvent) -> None:
        if ev.kind in {"starting", "log"} and ev.message:
            self.view.log(ev.message)
        elif ev.kind == "progress" and ev.message in {"20", "60", "100"}:
            app = self._spec_by_id.get(ev.app_id)
            if app:
                self.view.log(f"{app.name} ... {ev.message}%")
        elif ev.kind == "success":
            self._installed[ev.app_id] = True
            self.view.rebuild_tree(self._catalog, self._installed, self._selected)
        elif ev.kind == "skipped":
            app = self._spec_by_id.get(ev.app_id)
            if app:
                self.view.log(f"已跳过：{app.name}")
        elif ev.kind == "failed":
            if ev.message:
                self.view.log(ev.message)
        elif ev.kind == "all_done":
            self.view.set_busy(False); self.view.log("全部任务已结束。")
