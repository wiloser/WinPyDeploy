from __future__ import annotations

import hashlib
import os
import tempfile
from collections.abc import Callable
from pathlib import Path
from urllib.request import urlopen

from .models import AppSpec

try:  # optional dependency
    import requests  # type: ignore
except Exception:  # pragma: no cover
    requests = None


def ensure_package(app: AppSpec, emit: Callable[[str, str, str], None], stop: Callable[[], bool]) -> bool:
    if not app.package_path:
        return True
    target = Path(app.package_path)
    if target.exists():
        return True
    if not app.download_url:
        emit("log", app.app_id, f"安装包不存在：{target}")
        return False

    emit("log", app.app_id, f"安装包缺失，开始下载：{app.download_url}")
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkstemp(prefix=target.name + ".", dir=str(target.parent))[1])
    try:
        with tmp.open("wb") as f:
            if requests:
                ok = _download_requests(app, emit, stop, f)
            else:
                ok = _download_urllib(app, emit, stop, f)
            if not ok:
                return False

        if app.sha256 and not _verify_sha256(tmp, app.sha256):
            emit("log", app.app_id, "SHA256 校验失败，已删除下载文件")
            return False

        os.replace(tmp, target)
        emit("log", app.app_id, f"下载完成：{target}")
        return True
    finally:
        try:
            if tmp.exists():
                tmp.unlink()
        except Exception:
            pass


def _verify_sha256(path: Path, expected: str) -> bool:
    exp = expected.strip().lower().replace(" ", "")
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest() == exp


def _download_urllib(app: AppSpec, emit, stop, f) -> bool:
    with urlopen(app.download_url, timeout=30) as resp:
        total = int(resp.headers.get("Content-Length") or 0)
        got = 0
        while True:
            if stop():
                emit("log", app.app_id, "下载已取消")
                return False
            chunk = resp.read(1024 * 256)
            if not chunk:
                break
            f.write(chunk)
            got += len(chunk)
            if total and got % (1024 * 1024) < len(chunk):
                emit("log", app.app_id, f"下载进度：{got // (1024 * 1024)}MB/{total // (1024 * 1024)}MB")
    return True


def _download_requests(app: AppSpec, emit, stop, f) -> bool:
    assert requests is not None
    with requests.get(app.download_url, stream=True, timeout=30) as r:
        r.raise_for_status()
        total = int(r.headers.get("Content-Length") or 0)
        got = 0
        for chunk in r.iter_content(chunk_size=1024 * 256):
            if stop():
                emit("log", app.app_id, "下载已取消")
                return False
            if not chunk:
                continue
            f.write(chunk)
            got += len(chunk)
            if total and got % (1024 * 1024) < len(chunk):
                emit("log", app.app_id, f"下载进度：{got // (1024 * 1024)}MB/{total // (1024 * 1024)}MB")
    return True
