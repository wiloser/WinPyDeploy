from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass(frozen=True)
class FileLogger:
    """Append-only line logger.

    Intentionally simple: one line in, one line appended.
    """

    path: Path

    @staticmethod
    def create(log_dir: Path, *, prefix: str = "winpydeploy") -> "FileLogger":
        log_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        return FileLogger(path=(log_dir / f"{prefix}_{ts}.log"))

    def append(self, line: str) -> None:
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("a", encoding="utf-8", errors="replace", newline="\n") as f:
                f.write(line.rstrip("\n") + "\n")
        except Exception:
            # Logging must never crash the UI.
            pass
