from __future__ import annotations

import platform
import queue
import tkinter as tk
from tkinter import ttk

try:
    from ..workers.installer import InstallEvent
    from .controller import WinPyDeployController
    from .view import WinPyDeployView
except ImportError as exc:  # pragma: no cover
    raise SystemExit(
        "请在项目根目录运行: `./.venv/bin/python main.py` 或 `./.venv/bin/python -m winpydeploy`"
    ) from exc


class WinPyDeployApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        style = ttk.Style(root)
        try:
            if platform.system().lower() == "windows":
                style.theme_use("vista")
            elif platform.system().lower() == "darwin":
                style.theme_use("aqua")
            else:
                style.theme_use("clam")
        except tk.TclError:
            pass
        try:
            bg = style.lookup("TFrame", "background") or root.cget("bg")
            for s in ("TFrame", "TLabelframe", "TLabelframe.Label", "TPanedwindow", "TSeparator"):
                style.configure(s, background=bg)
            for s in ("Sash", "Panedwindow", "TScrollbar"):
                style.configure(s, background=bg)
            style.configure("Toolbar.TButton", padding=(10, 6))
            style.configure("Treeview", rowheight=24)
            style.configure("Treeview.Heading", font=("TkDefaultFont", 12, "bold"))
            style.configure("Catalog.Treeview", rowheight=26)
            style.configure("Catalog.Treeview.Heading", font=("TkDefaultFont", 12, "bold"))
            style.configure("Status.Treeview", rowheight=20)
            style.configure("Status.Treeview.Heading", font=("TkDefaultFont", 11, "bold"))
        except Exception:
            pass
        self._event_q: "queue.Queue[InstallEvent]" = queue.Queue()
        self.view = WinPyDeployView(root)
        self.controller = WinPyDeployController(self.view, self._event_q)
        self.view.set_handlers(
            on_refresh=self.controller.refresh_detection,
            on_select_missing=self.controller.select_all_missing,
            on_settings=self.controller.open_settings,
            on_download=self.controller.start_download,
            on_install=self.controller.start_install,
            on_tree_select=self.controller.on_tree_select,
            on_cancel_task=self.controller.cancel_selected_task,
        )
        self.controller.refresh_detection()
        self.controller.start_service_polling(root)
        root.after(100, self._drain_events)

    def _drain_events(self) -> None:
        try:
            while True:
                self.controller.handle_event(self._event_q.get_nowait())
        except queue.Empty:
            pass
        finally:
            self.root.after(100, self._drain_events)


if __name__ == "__main__":
    raise SystemExit(
        "请在项目根目录运行: `./.venv/bin/python main.py` 或 `./.venv/bin/python -m winpydeploy`"
    )
