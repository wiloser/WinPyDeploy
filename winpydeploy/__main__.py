from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from .paths import ensure_install_config
from .ui.app import WinPyDeployApp


def main() -> None:
    ensure_install_config()
    root = tk.Tk()
    style = ttk.Style(root)
    try:
        style.theme_use("aqua")
    except tk.TclError:
        pass
    WinPyDeployApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
