from __future__ import annotations

import queue
import tkinter as tk

try:
    from ..installer import InstallEvent
    from .controller import WinPyDeployController
    from .view import WinPyDeployView
except ImportError as exc:  # pragma: no cover
    raise SystemExit(
        "请在项目根目录运行: `./.venv/bin/python main.py` 或 `./.venv/bin/python -m winpydeploy`"
    ) from exc


class WinPyDeployApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self._event_q: "queue.Queue[InstallEvent]" = queue.Queue()
        self.view = WinPyDeployView(root)
        self.controller = WinPyDeployController(self.view, self._event_q)
        self.view.set_handlers(
            on_refresh=self.controller.refresh_detection,
            on_select_missing=self.controller.select_all_missing,
            on_install=self.controller.start_install,
            on_tree_select=self.controller.on_tree_select,
        )
        self.controller.refresh_detection()
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
