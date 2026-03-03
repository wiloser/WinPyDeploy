from __future__ import annotations

import tkinter as tk

from .core.paths import ensure_install_config
from .ui.app import WinPyDeployApp


def main() -> None:
    ensure_install_config()
    root = tk.Tk()
    WinPyDeployApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
