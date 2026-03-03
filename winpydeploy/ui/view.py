from __future__ import annotations
import time
import tkinter as tk
from tkinter import ttk, font
from collections.abc import Callable
from ..core.models import AppSpec

class WinPyDeployView(ttk.Frame):
    COL_ID, COL_NAME, COL_STATUS, COL_VER, COL_NOTES = "id", "name", "status", "ver", "notes"
    PROC_COL_NAME, PROC_COL_STATE = "proc", "state"

    def _bind_mouse_wheel(self, widget: tk.Widget, *, y: bool = True, x: bool = False) -> None:
        def _on_wheel(ev: tk.Event) -> str:
            delta = 0
            if hasattr(ev, "delta") and ev.delta:
                delta = int(ev.delta)
            if ev.num == 4:
                delta = 120
            elif ev.num == 5:
                delta = -120
            if delta == 0:
                return "break"
            units = -1 if delta > 0 else 1
            if y and hasattr(widget, "yview_scroll"):
                widget.yview_scroll(units, "units")  # type: ignore[attr-defined]
                return "break"
            if x and hasattr(widget, "xview_scroll"):
                widget.xview_scroll(units, "units")  # type: ignore[attr-defined]
                return "break"
            return "break"

        if y:
            widget.bind("<MouseWheel>", _on_wheel)
            widget.bind("<Button-4>", _on_wheel)
            widget.bind("<Button-5>", _on_wheel)
        if x:
            widget.bind("<Shift-MouseWheel>", _on_wheel)

    def __init__(self, master: tk.Tk):
        super().__init__(master)
        master.title("WinPyDeploy - 软件安装管理(原型)"); master.minsize(920, 560)
        padx=pady=10; inner=6; gap=6
        self.grid_rowconfigure(1, weight=1); self.grid_columnconfigure(0, weight=1)

        def _mix_with_white(hex_color: str, ratio: float) -> str | None:
            try:
                s = (hex_color or "").strip()
                if not (s.startswith("#") and len(s) == 7):
                    return None
                r = int(s[1:3], 16)
                g = int(s[3:5], 16)
                b = int(s[5:7], 16)
                r2 = int(r + (255 - r) * ratio)
                g2 = int(g + (255 - g) * ratio)
                b2 = int(b + (255 - b) * ratio)
                return f"#{r2:02x}{g2:02x}{b2:02x}"
            except Exception:
                return None
        toolbar = ttk.Frame(self); toolbar.grid(row=0, column=0, sticky="ew", padx=padx, pady=(pady, gap))
        left, right = ttk.Frame(toolbar), ttk.Frame(toolbar); left.pack(side=tk.LEFT, fill=tk.X, expand=True); right.pack(side=tk.RIGHT)
        self.btn_refresh, self.btn_select_missing = (ttk.Button(left, text="刷新已安装状态", style="Toolbar.TButton"), ttk.Button(left, text="选择所有未安装", style="Toolbar.TButton"))
        self.btn_settings = ttk.Button(left, text="设置", style="Toolbar.TButton")
        self.btn_download, self.btn_install = (ttk.Button(right, text="下载缺失安装包", style="Toolbar.TButton"), ttk.Button(right, text="开始安装", style="Toolbar.TButton"))
        for w in (self.btn_refresh, self.btn_select_missing, self.btn_settings): w.pack(side=tk.LEFT, padx=(0, 8))
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=8, pady=2)
        for w in (self.btn_download, self.btn_install): w.pack(side=tk.LEFT, padx=(0, 8))
        paned = ttk.Panedwindow(self, orient=tk.VERTICAL); paned.grid(row=1, column=0, sticky="nsew", padx=padx, pady=(0, pady))
        top, bottom = ttk.Frame(paned), ttk.Frame(paned); paned.add(top, weight=3); paned.add(bottom, weight=2)
        top2 = ttk.Panedwindow(top, orient=tk.HORIZONTAL); top2.pack(fill=tk.BOTH, expand=True)
        treef, detf = ttk.Labelframe(top2, text="软件列表", padding=inner), ttk.Labelframe(top2, text="详细信息", padding=inner)
        top2.add(treef, weight=3); top2.add(detf, weight=2)
        treef.grid_rowconfigure(0, weight=1); treef.grid_columnconfigure(0, weight=1)
        self.tree = ttk.Treeview(
            treef,
            columns=(self.COL_ID, self.COL_NAME, self.COL_STATUS, self.COL_VER, self.COL_NOTES),
            show="headings",
            selectmode="extended",
            style="Catalog.Treeview",
        )
        for col, text, width in ((self.COL_ID, "ID", 120), (self.COL_NAME, "软件", 260), (self.COL_STATUS, "状态", 120), (self.COL_VER, "版本", 140), (self.COL_NOTES, "备注", 240)):
            self.tree.heading(col, text=text); self.tree.column(col, width=width, anchor=tk.W)
        for c in (self.COL_ID, self.COL_STATUS, self.COL_VER): self.tree.column(c, stretch=False)
        self.tree.column(self.COL_NAME, stretch=True); self.tree.column(self.COL_NOTES, stretch=True)
        self.tree.column(self.COL_STATUS, anchor=tk.CENTER)
        self.tree.column(self.COL_VER, anchor=tk.CENTER)
        self._bold = font.Font(**{**font.nametofont("TkDefaultFont").actual(), "weight": "bold"}); self.tree.tag_configure("missing", font=self._bold)

        # Zebra stripes (derived from theme background; avoids hard-coded colors)
        try:
            st = ttk.Style(master)
            base_bg = st.lookup("Treeview", "fieldbackground") or st.lookup("Treeview", "background")
            alt_bg = _mix_with_white(base_bg, 0.06) if base_bg else None
            if base_bg and base_bg.startswith("#"):
                self.tree.tag_configure("row_even", background=base_bg)
                if alt_bg:
                    self.tree.tag_configure("row_odd", background=alt_bg)
        except Exception:
            pass
        yscroll = ttk.Scrollbar(treef, orient=tk.VERTICAL, command=self.tree.yview); self.tree.configure(yscrollcommand=yscroll.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        self._bind_mouse_wheel(self.tree, y=True, x=False)
        detf.grid_rowconfigure(0, weight=1); detf.grid_rowconfigure(1, weight=0)
        detf.grid_columnconfigure(0, weight=1)
        self.details_text = tk.Text(detf, wrap="none", state=tk.DISABLED, font="TkFixedFont", bd=0, highlightthickness=0, padx=4, pady=2)
        det_v = ttk.Scrollbar(detf, orient=tk.VERTICAL, command=self.details_text.yview); det_h = ttk.Scrollbar(detf, orient=tk.HORIZONTAL, command=self.details_text.xview)
        self.details_text.configure(yscrollcommand=det_v.set, xscrollcommand=det_h.set); self.details_text.grid(row=0, column=0, sticky="nsew")
        self._bind_mouse_wheel(self.details_text, y=True, x=True)

        statusf = ttk.Labelframe(detf, text="运行状态", padding=(inner, inner - 2))
        statusf.grid(row=1, column=0, sticky="ew", pady=(gap, 0))
        statusf.grid_columnconfigure(0, weight=1)
        self.proc_note = ttk.Label(statusf, text="(选择软件后显示运行状态)")
        self.proc_note.grid(row=0, column=0, sticky="w")
        self.proc_tree = ttk.Treeview(
            statusf,
            columns=(self.PROC_COL_NAME, self.PROC_COL_STATE),
            show="headings",
            height=3,
            selectmode="none",
            style="Status.Treeview",
        )
        self.proc_tree.heading(self.PROC_COL_NAME, text="进程")
        self.proc_tree.heading(self.PROC_COL_STATE, text="状态")
        self.proc_tree.column(self.PROC_COL_NAME, width=210, anchor=tk.W, stretch=True)
        self.proc_tree.column(self.PROC_COL_STATE, width=90, anchor=tk.CENTER, stretch=False)
        self.proc_tree.grid(row=1, column=0, sticky="ew", pady=(4, 0))
        self._bind_mouse_wheel(self.proc_tree, y=True, x=False)
        actf = ttk.Frame(statusf)
        actf.grid(row=2, column=0, sticky="ew", pady=(6, 0))
        self.btn_proc_start = ttk.Button(actf, text="启动", style="Toolbar.TButton")
        self.btn_proc_stop = ttk.Button(actf, text="结束", style="Toolbar.TButton")
        self.btn_proc_start.pack(side=tk.LEFT)
        self.btn_proc_stop.pack(side=tk.LEFT, padx=(8, 0))
        sub = ttk.Panedwindow(bottom, orient=tk.HORIZONTAL); sub.pack(fill=tk.BOTH, expand=True)
        logf, taskf = ttk.Labelframe(sub, text="日志", padding=inner), ttk.Labelframe(sub, text="任务", padding=inner); sub.add(logf, weight=3); sub.add(taskf, weight=1)
        logf.grid_rowconfigure(0, weight=1); logf.grid_columnconfigure(0, weight=1)
        self.log_text = tk.Text(logf, wrap="none", font="TkFixedFont", bd=0, highlightthickness=0, padx=4, pady=2)
        log_v = ttk.Scrollbar(logf, orient=tk.VERTICAL, command=self.log_text.yview); log_h = ttk.Scrollbar(logf, orient=tk.HORIZONTAL, command=self.log_text.xview)
        self.log_text.configure(yscrollcommand=log_v.set, xscrollcommand=log_h.set); self.log_text.grid(row=0, column=0, sticky="nsew")
        self._bind_mouse_wheel(self.log_text, y=True, x=True)
        taskf.grid_rowconfigure(0, weight=1); taskf.grid_columnconfigure(0, weight=1)
        self.task_list = tk.Listbox(taskf, height=8, bd=0, highlightthickness=0)
        task_scroll = ttk.Scrollbar(taskf, orient=tk.VERTICAL, command=self.task_list.yview); self.task_list.configure(yscrollcommand=task_scroll.set)
        self.task_list.grid(row=0, column=0, sticky="nsew")
        self._bind_mouse_wheel(self.task_list, y=True, x=False)
        self.btn_cancel_task = ttk.Button(taskf, text="取消选中任务", style="Toolbar.TButton"); self.btn_cancel_task.grid(row=1, column=0, columnspan=1, sticky="ew", pady=(gap, 0))
        self._task_ids = []
        self._log_sink: Callable[[str], None] | None = None
        self.pack(fill=tk.BOTH, expand=True)

    def set_log_sink(self, sink: Callable[[str], None] | None) -> None:
        self._log_sink = sink

    def set_handlers(self, *, on_refresh, on_select_missing, on_settings, on_download, on_install, on_tree_select, on_cancel_task, on_proc_start, on_proc_stop) -> None:
        self.btn_refresh.configure(command=on_refresh); self.btn_select_missing.configure(command=on_select_missing)
        self.btn_settings.configure(command=on_settings)
        self.btn_download.configure(command=on_download); self.btn_install.configure(command=on_install)
        self.tree.bind("<<TreeviewSelect>>", on_tree_select)
        self.btn_cancel_task.configure(command=on_cancel_task)
        self.btn_proc_start.configure(command=on_proc_start)
        self.btn_proc_stop.configure(command=on_proc_stop)

    def log(self, line: str) -> None:
        ts = time.strftime("%H:%M:%S")
        msg = f"[{ts}] {line}"
        self.log_text.insert(tk.END, msg + "\n"); self.log_text.see(tk.END)
        if self._log_sink:
            self._log_sink(msg)

    def rebuild_tree(self, catalog: tuple[AppSpec, ...], installed: dict[str, bool], selected: set[str], package_ok: dict[str, bool], errors: dict[str, str], versions: dict[str, str]) -> None:
        self.tree.delete(*self.tree.get_children())
        valid_ids = {a.app_id for a in catalog}
        for idx, app in enumerate(catalog):
            is_installed = installed.get(app.app_id, False)
            ok = package_ok.get(app.app_id, True)
            status = "已安装" if is_installed else ("未安装" if ok else "未安装(缺包)")
            ver = (versions.get(app.app_id) or "").strip()
            err = (errors.get(app.app_id) or "").strip()
            notes = (err[:120] + "…") if len(err) > 120 else (err or app.notes)
            tags = []
            tags.append("missing" if not is_installed else "")
            tags.append("row_even" if (idx % 2 == 0) else "row_odd")
            tags = tuple(t for t in tags if t)
            self.tree.insert("", tk.END, iid=app.app_id, values=(app.app_id, app.name, status, ver, notes), tags=tags)
        self.tree.selection_set([i for i in selected if i in valid_ids])

    def set_details(self, text: str) -> None:
        self.details_text.configure(state=tk.NORMAL); self.details_text.delete("1.0", tk.END)
        self.details_text.insert(tk.END, text); self.details_text.see(tk.END); self.details_text.configure(state=tk.DISABLED)

    def set_running_status(self, *, items: list[tuple[str, str]] | None = None, note: str = "") -> None:
        if note:
            self.proc_note.configure(text=note)
        self.proc_tree.delete(*self.proc_tree.get_children())
        if not items:
            return
        for proc, state in items:
            self.proc_tree.insert("", tk.END, values=(proc, state))

    def set_proc_actions_enabled(self, enabled: bool) -> None:
        s = tk.NORMAL if enabled else tk.DISABLED
        self.btn_proc_start.configure(state=s)
        self.btn_proc_stop.configure(state=s)

    def set_tasks(self, items: list[tuple[str, str]]) -> None:
        self._task_ids = [i for i, _ in items]; self.task_list.delete(0, tk.END)
        for _, text in items: self.task_list.insert(tk.END, text)

    def selected_task_id(self) -> str:
        sel = self.task_list.curselection(); return self._task_ids[sel[0]] if sel and sel[0] < len(self._task_ids) else ""

    def set_busy(self, busy: bool) -> None:
        s = tk.DISABLED if busy else tk.NORMAL
        self.btn_install.configure(state=s); self.btn_download.configure(state=s)
        self.btn_refresh.configure(state=s); self.btn_select_missing.configure(state=s)

    def selection(self) -> list[str]:
        return list(self.tree.selection())

    def set_selection(self, ids: list[str]) -> None:
        self.tree.selection_set(ids)
