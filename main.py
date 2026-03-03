import tkinter as tk

from winpydeploy.ui.app import WinPyDeployApp
from winpydeploy.core.paths import ensure_install_config


def main() -> None:
    ensure_install_config()
    root = tk.Tk()
    WinPyDeployApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
