"""存储操作失败默认抛出（StorageOperationError）契约测试"""

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
