from __future__ import annotations

import queue
import platform
import threading
from dataclasses import dataclass

from .models import AppSpec
from .runner import CommandRunner


@dataclass(frozen=True)
class InstallEvent:
    kind: str
    app_id: str
    message: str = ""


class InstallerWorker:
    def __init__(self, event_queue: "queue.Queue[InstallEvent]"):
        self._q = event_queue
        self._stop = threading.Event()

        def emit(kind: str, app_id: str, message: str) -> None:
            self._q.put(InstallEvent(kind, app_id, message))

        self._runner = CommandRunner(emit)

    def stop(self) -> None:
        self._stop.set()
        self._runner.terminate()

    def install(self, apps: list[AppSpec]) -> None:
        is_windows = platform.system().lower() == "windows"
        for app in apps:
            if self._stop.is_set():
                self._q.put(InstallEvent("log", app.app_id, "已取消，跳过后续任务"))
                self._q.put(InstallEvent("skipped", app.app_id, "cancelled"))
                continue

            self._q.put(InstallEvent("starting", app.app_id, f"开始安装：{app.name}"))
            mode = "Windows 真执行" if is_windows else "开发环境模拟"
            self._q.put(InstallEvent("log", app.app_id, f"({mode}) 将执行命令："))
            if not app.install_commands:
                self._q.put(InstallEvent("failed", app.app_id, "未配置 installCommands 或 packageFile，无法安装"))
                self._stop.set()
                continue

            failed = False
            for cmd in app.install_commands:
                if self._stop.is_set():
                    break
                code = self._runner.run(app_id=app.app_id, cmd=cmd, check_installer_path=True)
                if self._stop.is_set():
                    break
                if code != 0:
                    self._q.put(InstallEvent("failed", app.app_id, f"安装失败（exit={code}），停止后续任务"))
                    failed = True
                    self._stop.set()
                    break

            if not failed and not self._stop.is_set() and app.post_install_commands:
                self._q.put(InstallEvent("log", app.app_id, "(postInstall) 运行后置命令："))
                for cmd in app.post_install_commands:
                    code = self._runner.run(app_id=app.app_id, cmd=cmd, check_installer_path=False)
                    if code != 0:
                        self._q.put(InstallEvent("failed", app.app_id, f"后置命令失败（exit={code}），停止后续任务"))
                        self._stop.set()
                        failed = True
                        break

            if not failed and not self._stop.is_set():
                self._q.put(InstallEvent("success", app.app_id, "ok"))
                self._q.put(InstallEvent("log", app.app_id, f"安装完成：{app.name}"))

        self._q.put(InstallEvent("all_done", "*", "done"))
