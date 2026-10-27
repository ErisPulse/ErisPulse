"""
文件变更监控（PollingObserver）单元测试

补发 on_created / on_deleted 事件（mtime 轮询实现此前只回调 on_modified，
接口契约与行为不符）；on_moved 在轮询实现下明确不触发（移动 = 删除 + 创建）。
"""

import asyncio
import time

import pytest

from ErisPulse.runtime.file_watcher import FileSystemEventHandler, PollingObserver


class _Recorder(FileSystemEventHandler):
    def __init__(self):
        self.created, self.deleted, self.modified = [], [], []

    def on_created(self, event):
        self.created.append(event.src_path)

    def on_deleted(self, event):
        self.deleted.append(event.src_path)

    def on_modified(self, event):
        self.modified.append(event.src_path)


@pytest.mark.asyncio
async def test_created_and_deleted_events_fire(tmp_path):
    rec = _Recorder()
    observer = PollingObserver(interval=0.05)
    observer.schedule(rec, str(tmp_path), recursive=False)
    observer.start()
    try:
        target = tmp_path / "new_mod.py"
        target.write_text("x = 1\n", encoding="utf-8")
        await asyncio.sleep(0.2)
        assert any(p.endswith("new_mod.py") for p in rec.created)

        target.write_text("x = 2\n", encoding="utf-8")
        await asyncio.sleep(0.2)
        assert any(p.endswith("new_mod.py") for p in rec.modified)

        target.unlink()
        await asyncio.sleep(0.2)
        assert any(p.endswith("new_mod.py") for p in rec.deleted)
    finally:
        observer.stop()
        observer.join()


def test_non_py_files_ignored(tmp_path):
    rec = _Recorder()
    observer = PollingObserver(interval=0.05)
    observer.schedule(rec, str(tmp_path), recursive=False)
    observer.start()
    try:
        (tmp_path / "data.txt").write_text("x", encoding="utf-8")
        time.sleep(0.15)
        assert rec.created == []  # 仅监控 .py 文件
    finally:
        observer.stop()
        observer.join()


@pytest.mark.asyncio
async def test_relative_schedule_path_deletion_fires(tmp_path, monkeypatch):
    """相对路径调度的监控目录：删除事件必须触发

    键与删除前缀必须同坐标系（绝对化归一）——此前删除前缀为 resolve()
    绝对路径而 mtime 键保留调度原始路径，相对调度（默认 plugins / CLI 的
    "."）下 startswith 永不匹配，删除/改名插件静默失效。
    """
    monkeypatch.chdir(tmp_path)
    plugins = tmp_path / "plugins"
    plugins.mkdir()
    (plugins / "dice.py").write_text("x = 1\n", encoding="utf-8")

    rec = _Recorder()
    observer = PollingObserver(interval=0.05)
    observer.schedule(rec, "plugins", recursive=True)  # 相对路径调度
    observer.start()
    try:
        (plugins / "dice.py").unlink()
        await asyncio.sleep(0.25)
        assert any(p.endswith("dice.py") for p in rec.deleted), (
            "相对路径调度下删除事件未触发"
        )
    finally:
        observer.stop()
        observer.join()
