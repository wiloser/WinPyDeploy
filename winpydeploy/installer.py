from __future__ import annotations

import queue
import platform
import subprocess
import threading
import time
from dataclasses import dataclass

from .models import AppSpec


@dataclass(frozen=True)
class InstallEvent:
    kind: str
    app_id: str
    message: str = ""


class InstallerWorker:
    def __init__(self, event_queue: "queue.Queue[InstallEvent]"):
        self._q = event_queue
        self._stop = threading.Event()
        self._proc: subprocess.Popen[str] | None = None

    def stop(self) -> None:
        self._stop.set()
        proc = self._proc
        if proc and proc.poll() is None:
            try:
                proc.terminate()
            except Exception:
                pass

    def _run_command(self, app: AppSpec, cmd: str) -> int:
        self._q.put(InstallEvent("log", app.app_id, f"  {cmd}"))
        if platform.system().lower() != "windows":
            time.sleep(0.25)
            return 0

        self._proc = subprocess.Popen(
            cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        assert self._proc.stdout is not None
        for line in self._proc.stdout:
            if self._stop.is_set():
                break
            line = line.rstrip("\n")
            if line:
                self._q.put(InstallEvent("log", app.app_id, line))
        return self._proc.wait()

    def install(self, apps: list[AppSpec]) -> None:
        for app in apps:
            if self._stop.is_set():
                self._q.put(InstallEvent("log", app.app_id, "已取消，跳过后续任务"))
                self._q.put(InstallEvent("skipped", app.app_id, "cancelled"))
                continue

            self._q.put(InstallEvent("starting", app.app_id, f"开始安装：{app.name}"))
            self._q.put(InstallEvent("log", app.app_id, "(开发环境模拟) 将执行命令："))
            if not app.install_commands:
                self._q.put(InstallEvent("log", app.app_id, "  (未配置 installCommands 或 packageFile)"))
            for cmd in app.install_commands:
                if self._stop.is_set():
                    break
                code = self._run_command(app, cmd)
                if self._stop.is_set():
                    break
                if code != 0:
                    self._q.put(InstallEvent("failed", app.app_id, f"安装失败（exit={code}），停止后续任务"))
                    self._stop.set()
                    break

            if self._stop.is_set():
                self._q.put(InstallEvent("skipped", app.app_id, "cancelled"))
            elif app.install_commands:
                self._q.put(InstallEvent("success", app.app_id, "ok"))
                self._q.put(InstallEvent("log", app.app_id, f"安装完成：{app.name}"))

        self._q.put(InstallEvent("all_done", "*", "done"))
