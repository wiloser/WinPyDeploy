from __future__ import annotations
import queue, threading
from pathlib import Path
import re
from tkinter import messagebox, filedialog
import tkinter as tk
from tkinter import ttk
from ..core import user_config
from ..core.paths import DEFAULT_INSTALL_DIR, ensure_install_config, packages_dir, set_packages_dir, install_dir, set_install_dir, project_root
from ..core.config import load_catalog
from ..core.detection import detect_installed_apps
from ..workers.downloader_worker import DownloadWorker
from ..workers.info_worker import InfoWorker
from ..workers.installer import InstallEvent, InstallerWorker
from ..core.models import AppSpec
from .view import WinPyDeployView
class WinPyDeployController:
    def __init__(self, view: WinPyDeployView, event_q: "queue.Queue[InstallEvent]"):
        self.view, self._event_q = view, event_q
        self._worker = InstallerWorker(event_q); self._worker_thread: threading.Thread | None = None
        self._dl_thread: threading.Thread | None = None; self._dl: DownloadWorker | None = None
        self._catalog: tuple[AppSpec, ...] = (); self._spec_by_id: dict[str, AppSpec] = {}
        self._installed: dict[str, bool] = {}; self._package_ok: dict[str, bool] = {}; self._errors: dict[str, str] = {}
        self._versions: dict[str, str] = {}; self._selected: set[str] = set(); self._tasks: dict[str, str] = {}
        self._info_thread: threading.Thread | None = None; self._info: InfoWorker | None = None; self._info_app = ""

    def _task(self, tid: str, text: str | None) -> None:
        (self._tasks.__setitem__(tid, text) if text is not None else self._tasks.pop(tid, None)); self.view.set_tasks(list(self._tasks.items()))

    def cancel_selected_task(self) -> None:
        tid = self.view.selected_task_id()
        if not tid: messagebox.showinfo("提示", "请先在任务列表中选择一个任务。"); return
        kind, _, app_id = tid.partition(":"); (kind == "dl" and self._dl and self._dl.cancel_app(app_id))
        if kind == "ins": self._worker.cancel_app(app_id)
        if kind == "info" and self._info and self._info_app == app_id: self._info.stop()
        self.view.log(f"已请求取消：{tid}")

    def open_settings(self) -> None:
        if (self._worker_thread and self._worker_thread.is_alive()) or (self._dl_thread and self._dl_thread.is_alive()):
            messagebox.showinfo("提示", "下载/安装进行中，暂不支持修改设置。"); return
        parent = self.view.winfo_toplevel()
        win = tk.Toplevel(parent); win.title("设置"); win.resizable(False, False)
        frm = ttk.Frame(win, padding=10); frm.pack(fill=tk.BOTH, expand=True)
        frm.grid_columnconfigure(0, weight=1)
        ttk.Label(frm, text="资源目录(集中下载/脚本/配置)：").grid(row=0, column=0, sticky="w")
        pkg_var = tk.StringVar(value=str(packages_dir()))
        ttk.Entry(frm, textvariable=pkg_var, width=56).grid(row=1, column=0, sticky="ew", pady=(6, 0))
        def browse_pkg():
            d = filedialog.askdirectory(title="选择资源目录", initialdir=pkg_var.get() or str(Path.home()))
            d and pkg_var.set(d)
        ttk.Button(frm, text="浏览…", command=browse_pkg).grid(row=1, column=1, padx=(8, 0), pady=(6, 0))

        ttk.Label(frm, text="集中安装目录(可选，用于 zip 解压默认目标)：").grid(row=2, column=0, sticky="w", pady=(10, 0))
        inst_var = tk.StringVar(value=str(install_dir() or DEFAULT_INSTALL_DIR))
        ttk.Entry(frm, textvariable=inst_var, width=56).grid(row=3, column=0, sticky="ew", pady=(6, 0))
        def browse_inst():
            d = filedialog.askdirectory(title="选择集中安装目录", initialdir=inst_var.get() or str(Path.home()))
            d and inst_var.set(d)
        ttk.Button(frm, text="浏览…", command=browse_inst).grid(row=3, column=1, padx=(8, 0), pady=(6, 0))

        ttk.Label(frm, text="说明：安装目录为空时保持各软件原有配置/默认值。").grid(row=4, column=0, columnspan=2, sticky="w", pady=(6, 0))
        btns = ttk.Frame(frm); btns.grid(row=5, column=0, columnspan=2, sticky="e", pady=(12, 0))

        def reset_defaults():
            pkg_var.set(str(project_root() / "packages"))
            inst_var.set(DEFAULT_INSTALL_DIR)
        def save_and_close():
            p = pkg_var.get().strip()
            if not p: messagebox.showerror("错误", "资源目录不能为空。"); return
            pp = Path(p).expanduser()
            if not pp.is_absolute(): messagebox.showerror("错误", "资源目录请填写绝对路径。"); return

            ip = inst_var.get().strip()
            def is_abs_any(s: str) -> bool:
                return Path(s).is_absolute() or re.match(r"^[A-Za-z]:[\\/]", s) is not None

            ipp_raw = ip
            if ipp_raw and not is_abs_any(ipp_raw):
                messagebox.showerror("错误", "集中安装目录请填写绝对路径（或留空）。"); return
            try:
                pp.mkdir(parents=True, exist_ok=True)
                # On non-Windows systems a Windows drive path can't be created; just persist it.
                user_config.save(user_config.UserConfig(packages_dir=str(pp), install_dir=str(ipp_raw) if ipp_raw else ""))
                set_packages_dir(str(pp))
                set_install_dir(str(ipp_raw) if ipp_raw else "")
                ensure_install_config()
                self.refresh_detection()
                self.view.log(f"已更新资源目录：{pp}")
                self.view.log(f"已更新集中安装目录：{ipp_raw or '(空)'}")
                win.destroy()
            except Exception as exc:
                messagebox.showerror("错误", f"保存失败：{exc}")
        ttk.Button(btns, text="恢复默认", command=reset_defaults).pack(side=tk.LEFT)
        ttk.Button(btns, text="取消", command=win.destroy).pack(side=tk.RIGHT)
        ttk.Button(btns, text="保存", command=save_and_close).pack(side=tk.RIGHT, padx=(0, 8))
        win.transient(parent); win.grab_set(); win.wait_window(win)

    def refresh_detection(self) -> None:
        self._catalog = load_catalog(); self._spec_by_id = {a.app_id: a for a in self._catalog}; self._installed = detect_installed_apps(self._catalog)
        self._package_ok = {a.app_id: ((not a.package_path or Path(a.package_path).exists()) and all(Path(f.path).exists() for f in getattr(a, "extra_files", ()))) for a in self._catalog}
        self._errors = {k: v for k, v in self._errors.items() if k in self._spec_by_id}; self._versions = {k: v for k, v in self._versions.items() if k in self._spec_by_id}
        self.view.rebuild_tree(self._catalog, self._installed, self._selected, self._package_ok, self._errors, self._versions); self.view.set_tasks(list(self._tasks.items())); self.view.log("检测完成。")

    def on_tree_select(self, _evt=None) -> None:
        sel = self.view.selection(); self._selected = set(sel)
        if not sel: self.view.set_details(""); return
        app_id = sel[-1]; spec = self._spec_by_id.get(app_id)
        if not self._installed.get(app_id, False): self.view.set_details("未安装。\n"); return
        if not spec or not spec.info_commands: self.view.set_details("(未配置 infoCommands)\n"); return
        self.view.set_details("加载中…\n"); (self._info_thread and self._info_thread.is_alive() and self._info and self._info.stop())
        self._info = InfoWorker(self._event_q)  # type: ignore[arg-type]
        self._info_app = app_id; self._task(f"info:{app_id}", f"信息 {spec.name}"); self._info_thread = threading.Thread(target=self._info.fetch, args=(spec,), daemon=True); self._info_thread.start()

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
        self._dl = DownloadWorker(self._event_q)  # type: ignore[arg-type]
        self._dl_thread = threading.Thread(target=self._dl.download, args=(apps,), daemon=True); self._dl_thread.start()

    def handle_event(self, ev: InstallEvent) -> None:
        if ev.kind == "starting":
            self._errors.pop(ev.app_id, None); ev.message and self.view.log(ev.message); spec = self._spec_by_id.get(ev.app_id)
            spec and ev.message.startswith("开始下载") and self._task(f"dl:{ev.app_id}", f"下载 {spec.name}")
            spec and ev.message.startswith("开始安装") and self._task(f"ins:{ev.app_id}", f"安装 {spec.name}")
        elif ev.kind == "downloaded":
            a = self._spec_by_id.get(ev.app_id)
            if a: self._package_ok[ev.app_id] = ((not a.package_path or Path(a.package_path).exists()) and all(Path(f.path).exists() for f in getattr(a, "extra_files", ())));
            self._task(f"dl:{ev.app_id}", None); self.view.rebuild_tree(self._catalog, self._installed, self._selected, self._package_ok, self._errors, self._versions)
        elif ev.kind == "success":
            self._installed[ev.app_id] = True; self._errors.pop(ev.app_id, None); self._task(f"ins:{ev.app_id}", None)
            self.view.rebuild_tree(self._catalog, self._installed, self._selected, self._package_ok, self._errors, self._versions)
        elif ev.kind == "skipped":
            app = self._spec_by_id.get(ev.app_id); app and self.view.log(("已取消：" if ev.message == "cancelled" else "已跳过：") + app.name)
            self._task(f"dl:{ev.app_id}", None); self._task(f"ins:{ev.app_id}", None); self._task(f"info:{ev.app_id}", None)
        elif ev.kind == "failed" and ev.message:
            self._errors[ev.app_id] = ev.message; self.view.log(ev.message)
            self._task(f"dl:{ev.app_id}", None); self._task(f"ins:{ev.app_id}", None)
            self.view.rebuild_tree(self._catalog, self._installed, self._selected, self._package_ok, self._errors, self._versions)
        elif ev.kind == "log" and ev.message:
            m = ev.message.strip(); prefix = "下载进度："
            if ev.app_id != "*" and m.startswith(prefix) and "MB/" in m and m.endswith("MB"):
                try:
                    got_s, rest = m[len(prefix):].split("MB/", 1); total_s = rest[:-2]
                    got, total = int(got_s), int(total_s); pct = int(got * 100 / total) if total > 0 else 0
                    n = 10; f = max(0, min(n, int(pct * n / 100))); bar = f"[{'#'*f}{'-'*(n-f)}] {pct:3d}%"
                    spec = self._spec_by_id.get(ev.app_id)
                    spec and self._task(f"dl:{ev.app_id}", f"下载 {spec.name} {bar}")
                except Exception:
                    pass
            self.view.log(ev.message)
        elif ev.kind == "info_done":
            self.view.set_details(ev.message or "")
            first = next((ln.strip() for ln in (ev.message or "").splitlines() if ln.strip() and not ln.strip().startswith(">")), "")
            if first: self._versions[ev.app_id] = first[:60]
            self._task(f"info:{ev.app_id}", None); self.view.rebuild_tree(self._catalog, self._installed, self._selected, self._package_ok, self._errors, self._versions)
        elif ev.kind in {"download_all_done", "all_done"}:
            self.view.set_busy(False); self.view.log("下载任务已结束。" if ev.kind == "download_all_done" else "全部任务已结束。")
