from __future__ import annotations

import queue
import threading
from pathlib import Path
from tkinter import messagebox

from ..config import load_catalog
from ..detection import detect_installed_apps
from ..downloader_worker import DownloadWorker
from ..installer import InstallEvent, InstallerWorker
from ..models import AppSpec
from .view import WinPyDeployView


class WinPyDeployController:
    def __init__(self, view: WinPyDeployView, event_q: "queue.Queue[InstallEvent]"):
        self.view = view
        self._event_q = event_q
        self._worker = InstallerWorker(event_q)
        self._worker_thread: threading.Thread | None = None
        self._dl_thread: threading.Thread | None = None
        self._catalog: tuple[AppSpec, ...] = ()
        self._spec_by_id: dict[str, AppSpec] = {}
        self._installed: dict[str, bool] = {}
        self._package_ok: dict[str, bool] = {}
        self._errors: dict[str, str] = {}
        self._selected: set[str] = set()

    def refresh_detection(self) -> None:
        self._catalog = load_catalog()
        self._spec_by_id = {a.app_id: a for a in self._catalog}
        self._installed = detect_installed_apps(self._catalog)
        self._package_ok = {a.app_id: ((not a.package_path or Path(a.package_path).exists()) and all(Path(f.path).exists() for f in getattr(a, "extra_files", ()))) for a in self._catalog}
        self._errors = {k: v for k, v in self._errors.items() if k in self._spec_by_id}
        self.view.rebuild_tree(self._catalog, self._installed, self._selected, self._package_ok, self._errors)
        self.view.log("检测完成。")

    def on_tree_select(self, _evt=None) -> None:
        self._selected = set(self.view.selection())

    def select_all_missing(self) -> None:
        missing = [a.app_id for a in self._catalog if not self._installed.get(a.app_id, False)]; self.view.set_selection(missing); self._selected = set(missing)

    def start_install(self) -> None:
        if self._worker_thread and self._worker_thread.is_alive(): messagebox.showinfo("提示", "正在安装中，请等待完成。"); return
        if self._dl_thread and self._dl_thread.is_alive(): messagebox.showinfo("提示", "正在下载中，请等待完成。"); return
        if not self._selected: messagebox.showinfo("提示", "请先选择要安装的软件（点击/框选）。"); return
        to_install = [s for i in self._selected if (s := self._spec_by_id.get(i)) and not self._installed.get(i, False)]
        if not to_install: messagebox.showinfo("提示", "选择的软件都已安装，无需执行。"); return
        self.view.log(f"准备安装 {len(to_install)} 个软件…"); self.view.set_busy(True)
        self._worker = InstallerWorker(self._event_q)
        self._worker_thread = threading.Thread(target=self._worker.install, args=(to_install,), daemon=True); self._worker_thread.start()

    def start_download(self) -> None:
        if self._dl_thread and self._dl_thread.is_alive(): messagebox.showinfo("提示", "正在下载中，请等待完成。"); return
        if self._worker_thread and self._worker_thread.is_alive(): messagebox.showinfo("提示", "正在安装中，请等待完成。"); return
        if not self._selected: messagebox.showinfo("提示", "请先选择要下载的软件（点击/框选）。"); return
        apps = [self._spec_by_id[i] for i in self._selected if i in self._spec_by_id]
        if not apps: messagebox.showinfo("提示", "没有可下载的条目。"); return
        self.view.log(f"准备下载 {len(apps)} 个软件的安装包…"); self.view.set_busy(True)
        dl = DownloadWorker(self._event_q)  # type: ignore[arg-type]
        self._dl_thread = threading.Thread(target=dl.download, args=(apps,), daemon=True); self._dl_thread.start()

    def handle_event(self, ev: InstallEvent) -> None:
        if ev.kind == "starting": self._errors.pop(ev.app_id, None); ev.message and self.view.log(ev.message)
        elif ev.kind == "downloaded":
            a = self._spec_by_id.get(ev.app_id)
            if a: self._package_ok[ev.app_id] = ((not a.package_path or Path(a.package_path).exists()) and all(Path(f.path).exists() for f in getattr(a, "extra_files", ())));
            self.view.rebuild_tree(self._catalog, self._installed, self._selected, self._package_ok, self._errors)
        elif ev.kind == "success":
            self._installed[ev.app_id] = True; self._errors.pop(ev.app_id, None)
            self.view.rebuild_tree(self._catalog, self._installed, self._selected, self._package_ok, self._errors)
        elif ev.kind == "skipped":
            app = self._spec_by_id.get(ev.app_id); app and self.view.log(f"已跳过：{app.name}")
        elif ev.kind == "failed" and ev.message:
            self._errors[ev.app_id] = ev.message; self.view.log(ev.message)
            self.view.rebuild_tree(self._catalog, self._installed, self._selected, self._package_ok, self._errors)
        elif ev.kind == "log" and ev.message: self.view.log(ev.message)
        elif ev.kind in {"download_all_done", "all_done"}:
            self.view.set_busy(False); self.view.log("下载任务已结束。" if ev.kind == "download_all_done" else "全部任务已结束。")
