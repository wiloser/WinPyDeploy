import tkinter as tk
from tkinter import ttk

from winpydeploy.ui.app import WinPyDeployApp


def main() -> None:
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
