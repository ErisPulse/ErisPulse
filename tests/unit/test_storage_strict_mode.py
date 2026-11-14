"""存储操作失败默认抛出（StorageOperationError）契约测试"""

import sqlite3

import pytest
import pytest_asyncio

from ErisPulse.Core import StorageOperationError, StorageUnreachableError


@pytest_asyncio.fixture
async def storage(tmp_path, monkeypatch):
    """隔离 SQLite 后端（临时目录）"""
    monkeypatch.setenv("ERISPULSE_STORAGE_BACKEND", "sqlite")
    monkeypatch.setenv("ERISPULSE_STORAGE_USE_GLOBAL_DB", "false")
    monkeypatch.setenv("ERISPULSE_STORAGE_SQLITE_PATH", str(tmp_path / "t.db"))
    from ErisPulse.Core.storage import storage

    storage.__init__()
    # 测试隔离：指向临时库并清空循环缓存（全局单例跨测试残留旧连接）
    storage.db_path = str(tmp_path / "t.db")
    storage._loop_resources.clear()
    yield storage
    try:
        await storage.close()
    except Exception:
        pass


@pytest.mark.asyncio
async def test_write_failure_raises_by_default(storage, monkeypatch):
    """写操作失败默认抛 StorageOperationError（不再静默 False）"""
    monkeypatch.setattr(
        storage, "_run_with_conn",
        lambda *a, **k: (_ for _ in ()).throw(RuntimeError("boom")),
    )
    with pytest.raises(StorageOperationError) as ei:
        await storage.aset("k", "v")
    assert ei.value.operation == "set"
    assert ei.value.key == "k"
    assert isinstance(ei.value.__cause__, RuntimeError)


@pytest.mark.asyncio
async def test_delete_and_clear_failures_raise(storage, monkeypatch):
    """delete / clear 同契约"""
    monkeypatch.setattr(
        storage, "_run_with_conn",
        lambda *a, **k: (_ for _ in ()).throw(RuntimeError("boom")),
    )
    with pytest.raises(StorageOperationError):
        await storage.adelete("k")
    with pytest.raises(StorageOperationError):
        await storage.aclear()


@pytest.mark.asyncio
async def test_normal_write_unaffected(storage):
    """正常读写不受影响"""
    assert await storage.aset("k", "v") is True
    assert await storage.aget("k") == "v"


@pytest.mark.asyncio
async def test_cooldown_fastfail_stays_false(storage, monkeypatch):
    """连接级不可达（冷却期 fast-fail）恒返回 False——规则 26 韧性语义不变"""
    monkeypatch.setattr(storage, "_is_ready", lambda: False)
    assert await storage.aset("k", "v") is False
    assert await storage.aget("k", "fallback") == "fallback"


def test_exception_hierarchy():
    """StorageOperationError 挂 StorageError 层级（与 Unreachable 平级）"""
    assert issubclass(StorageOperationError, StorageUnreachableError.__mro__[1])
    err = StorageOperationError("m", operation="set", key="k")
    assert err.operation == "set" and err.key == "k"


@pytest.mark.asyncio
async def test_broken_connection_invalidated_and_rebuilt(storage, monkeypatch):
    """连接级损坏 → 丢弃缓存资源 → 下次操作重建成功（规则 26 自动重连兑现）"""
    await storage.aset("k", "v")   # 建立循环缓存资源

    real_exec = type(storage)._exec_query_on

    async def broken_conn(self, kind, sql, params, conn):
        raise sqlite3.OperationalError("Cannot operate on a closed database")

    monkeypatch.setattr(type(storage), "_exec_query_on", broken_conn)
    with pytest.raises(StorageOperationError):
        await storage.aset("k2", "v")          # 连接损坏 → 失效 → 本操作抛
    monkeypatch.setattr(type(storage), "_exec_query_on", real_exec)
    assert len(storage._loop_resources) == 0   # 缓存已失效

    assert await storage.aset("k2", "v") is True    # 下次操作重建成功（自愈）
    assert await storage.aget("k2") == "v"


@pytest.mark.asyncio
async def test_write_lock_error_does_not_invalidate(storage, monkeypatch):
    """写锁竞争（database is locked）不失效资源——连接本身可用，丢弃会误伤"""
    await storage.aset("k", "v")

    real_exec = type(storage)._exec_query_on

    async def locked(self, kind, sql, params, conn):
        raise sqlite3.OperationalError("database is locked")

    monkeypatch.setattr(type(storage), "_exec_query_on", locked)
    with pytest.raises(StorageOperationError):
        await storage.aset("k2", "v")
    monkeypatch.setattr(type(storage), "_exec_query_on", real_exec)

    assert await storage.aset("k3", "v") is True   # 资源仍在，正常写
