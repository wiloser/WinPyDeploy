from __future__ import annotations

import time
import tkinter as tk
from tkinter import ttk

from ..models import AppSpec


class WinPyDeployView(ttk.Frame):
    COL_ID, COL_NAME, COL_STATUS, COL_NOTES = "id", "name", "status", "notes"

    def __init__(self, master: tk.Tk):
        super().__init__(master)
        master.title("WinPyDeploy - 软件安装管理(原型)"); master.minsize(920, 560)
        toolbar = ttk.Frame(self); toolbar.pack(side=tk.TOP, fill=tk.X, padx=10, pady=(10, 6))
        self.btn_refresh = ttk.Button(toolbar, text="刷新已安装状态")
        self.btn_select_missing = ttk.Button(toolbar, text="选择所有未安装")
        self.btn_clear = ttk.Button(toolbar, text="清空选择")
        self.btn_install = ttk.Button(toolbar, text="一键开始安装")
        self.btn_cancel = ttk.Button(toolbar, text="取消", state=tk.DISABLED)
        self.btn_refresh.pack(side=tk.LEFT)
        self.btn_select_missing.pack(side=tk.LEFT, padx=(8, 0))
        self.btn_clear.pack(side=tk.LEFT, padx=(8, 0))
        self.btn_install.pack(side=tk.LEFT, padx=(20, 0))
        self.btn_cancel.pack(side=tk.LEFT, padx=(8, 0))
        paned = ttk.Panedwindow(self, orient=tk.VERTICAL)
        paned.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        top, bottom = ttk.Frame(paned), ttk.Frame(paned); paned.add(top, weight=3); paned.add(bottom, weight=2)
        self.tree = ttk.Treeview(
            top,
            columns=(self.COL_ID, self.COL_NAME, self.COL_STATUS, self.COL_NOTES),
            show="headings",
            selectmode="extended",
        )
        for col, text, width in (
            (self.COL_ID, "ID", 120),
            (self.COL_NAME, "软件", 260),
            (self.COL_STATUS, "状态", 120),
            (self.COL_NOTES, "备注", 380),
        ):
            self.tree.heading(col, text=text); self.tree.column(col, width=width, anchor=tk.W)
        yscroll = ttk.Scrollbar(top, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=yscroll.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True); yscroll.pack(side=tk.RIGHT, fill=tk.Y)
        ttk.Label(bottom, text="日志").pack(side=tk.TOP, anchor=tk.W)
        self.log_text = tk.Text(bottom, height=10, wrap="word")
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        log_scroll = ttk.Scrollbar(bottom, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scroll.set); log_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.pack(fill=tk.BOTH, expand=True)

    def set_handlers(self, *, on_refresh, on_select_missing, on_clear, on_install, on_cancel, on_tree_select, on_tree_double_click) -> None:
        self.btn_refresh.configure(command=on_refresh)
        self.btn_select_missing.configure(command=on_select_missing)
        self.btn_clear.configure(command=on_clear)
        self.btn_install.configure(command=on_install)
        self.btn_cancel.configure(command=on_cancel)
        self.tree.bind("<<TreeviewSelect>>", on_tree_select)
        self.tree.bind("<Double-1>", on_tree_double_click)

    def log(self, line: str) -> None:
        ts = time.strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{ts}] {line}\n"); self.log_text.see(tk.END)

    def rebuild_tree(self, catalog: tuple[AppSpec, ...], installed: dict[str, bool], selected: set[str]) -> None:
        self.tree.delete(*self.tree.get_children())
        valid_ids = {a.app_id for a in catalog}
        for app in catalog:
            status = "已安装" if installed.get(app.app_id, False) else "未安装"
            self.tree.insert("", tk.END, iid=app.app_id, values=(app.app_id, app.name, status, app.notes))
        self.tree.selection_set([i for i in selected if i in valid_ids])

    def set_busy(self, busy: bool) -> None:
        s = tk.DISABLED if busy else tk.NORMAL
        self.btn_install.configure(state=s); self.btn_refresh.configure(state=s)
        self.btn_select_missing.configure(state=s); self.btn_clear.configure(state=s)
        self.btn_cancel.configure(state=tk.NORMAL if busy else tk.DISABLED)

    def selection(self) -> list[str]:
        return list(self.tree.selection())

    def set_selection(self, ids: list[str]) -> None:
        self.tree.selection_set(ids)

    def clear_selection(self) -> None:
        self.tree.selection_remove(self.tree.selection())
