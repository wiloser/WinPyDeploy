from __future__ import annotations
import hashlib
import os
import tempfile
import time
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
        emit("log", app.app_id, f"安装包不存在：{target}"); return False

    emit("log", app.app_id, f"安装包缺失，开始下载：{app.download_url}")
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=target.name + ".", dir=str(target.parent))
    os.close(fd)
    tmp = Path(tmp_name)
    try:
        with tmp.open("wb") as f:
            if not _download(app, emit, stop, f):
                return False
        if app.sha256 and not _sha256_ok(tmp, app.sha256):
            emit("log", app.app_id, "SHA256 校验失败")
            return False
        if not _replace_retry(tmp, target, emit, app.app_id, stop):
            return False
        emit("log", app.app_id, f"下载完成：{target}")
        return True
    finally:
        try: tmp.exists() and tmp.unlink()
        except Exception: pass

def _sha256_ok(path: Path, expected: str) -> bool:
    exp = expected.strip().lower().replace(" ", "")
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest() == exp

def _replace_retry(src: Path, dst: Path, emit, app_id: str, stop) -> bool:
    for attempt in range(20):
        try:
            os.replace(src, dst)
            return True
        except PermissionError as exc:
            if stop():
                emit("log", app_id, "下载已取消")
                return False
            if attempt in (0, 5, 10, 19):
                emit("log", app_id, f"文件被占用，重试… ({exc})")
            time.sleep(0.2 if attempt < 5 else 0.5)
    emit("log", app_id, "写入安装包失败：文件被占用")
    return False

def _download(app: AppSpec, emit, stop, f) -> bool:
    return _download_requests(app, emit, stop, f) if requests else _download_urllib(app, emit, stop, f)

def _download_urllib(app: AppSpec, emit, stop, f) -> bool:
    with urlopen(app.download_url, timeout=30) as resp:
        total = int(resp.headers.get("Content-Length") or 0); got = 0
        while True:
            if stop():
                emit("log", app.app_id, "下载已取消"); return False
            chunk = resp.read(1024 * 256)
            if not chunk:
                break
            f.write(chunk); got += len(chunk)
            if total and got % (1024 * 1024) < len(chunk):
                emit("log", app.app_id, f"下载进度：{got // (1024 * 1024)}MB/{total // (1024 * 1024)}MB")
    return True

def _download_requests(app: AppSpec, emit, stop, f) -> bool:
    assert requests is not None
    with requests.get(app.download_url, stream=True, timeout=30) as r:
        r.raise_for_status(); total = int(r.headers.get("Content-Length") or 0); got = 0
        for chunk in r.iter_content(chunk_size=1024 * 256):
            if stop():
                emit("log", app.app_id, "下载已取消"); return False
            if not chunk:
                continue
            f.write(chunk); got += len(chunk)
            if total and got % (1024 * 1024) < len(chunk):
                emit("log", app.app_id, f"下载进度：{got // (1024 * 1024)}MB/{total // (1024 * 1024)}MB")
    return True
