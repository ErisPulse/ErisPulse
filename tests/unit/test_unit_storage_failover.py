"""
存储后端连接失败快速失败与冷却重连单元测试

语义：mysql / postgres / sqlite 连接失败（建池重试耗尽）时框架照常启动、
存储操作快速失败（不再阻塞/崩溃）；冷却期（默认 30s）结束后自动重连试探，
数据库恢复即随之恢复。无 SQLite 回退。
"""

import time

import pytest

from ErisPulse.Core.Bases.errors import StorageUnreachableError
from ErisPulse.Core.storage import MySQLStorage, SQLiteStorage


async def _boom():
    raise RuntimeError("pool creation exhausted")


def _fresh(cls):
    """绕过 _SingletonMixin 缓存构造全新实例，吞掉初始化阶段的连接失败"""
    backend = object.__new__(cls)
    try:
        cls.__init__(backend)
    except StorageUnreachableError:
        pass
    return backend


@pytest.mark.asyncio
async def test_unreachable_construction_keeps_framework_alive(tmp_path, monkeypatch):
    """后端不可达时构造不抛出：框架照常启动，存储操作快速失败返回"""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(MySQLStorage, "_create_loop_resource", staticmethod(_boom))
    monkeypatch.setattr(MySQLStorage, "_RESOURCE_CREATE_BACKOFF_SECS", 0.01)

    backend = _fresh(MySQLStorage)

    assert not backend._is_ready()
    assert await backend.aset("k1", 1) is False
    assert await backend.aget("k1") is None


@pytest.mark.asyncio
async def test_runtime_loss_fails_fast_and_recovers(tmp_path, monkeypatch):
    """运行期数据库掉线：快速失败进入冷却；恢复后冷却结束自动重连成功"""

    class _FlakySQLite(SQLiteStorage):
        broken = False

        async def _create_loop_resource(self):
            if self.broken:
                raise RuntimeError("db down")
            return await super()._create_loop_resource()

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(_FlakySQLite, "_RESOURCE_FAIL_COOLDOWN_SECS", 0.05)
    backend = object.__new__(_FlakySQLite)
    _FlakySQLite.broken = False
    _FlakySQLite.__init__(backend)
    assert backend._is_ready()

    # 数据库掉线：操作快速失败（内部吞异常记日志），进入冷却
    _FlakySQLite.broken = True
    assert await backend.aset("k", "v") is False
    assert backend._resource_failed_until > time.monotonic()

    # 冷却期内：快速失败，不再阻塞重试
    t0 = time.monotonic()
    assert await backend.aget("k") is None
    assert time.monotonic() - t0 < 0.5

    # 数据库恢复 + 冷却结束：自动重连成功，冷却清零
    _FlakySQLite.broken = False
    time.sleep(0.06)
    assert await backend.aset("k", "v2") is True
    assert await backend.aget("k") == "v2"
    assert backend._resource_failed_until == 0.0
    await backend.aclose()


@pytest.mark.asyncio
async def test_mysql_runtime_loss_same_semantics(tmp_path, monkeypatch):
    """mysql 运行期掉线同语义：冷却结束自动重连试探（本机无 MySQL，试探仍失败属预期）"""
    attempts = {"n": 0}

    class _FlakyMySQL(MySQLStorage):
        async def _create_loop_resource(self):
            attempts["n"] += 1
            if self.broken:
                raise RuntimeError("db down")
            return await super()._create_loop_resource()

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(_FlakyMySQL, "_RESOURCE_CREATE_BACKOFF_SECS", 0.01)
    monkeypatch.setattr(_FlakyMySQL, "_RESOURCE_FAIL_COOLDOWN_SECS", 0.05)
    backend = object.__new__(_FlakyMySQL)
    _FlakyMySQL.broken = True
    try:
        _FlakyMySQL.__init__(backend)
    except StorageUnreachableError:
        pass
    # 模拟"曾正常就绪"状态（真实环境：先成功连接，之后数据库掉线）
    backend._finish_init()
    assert backend._is_ready()

    assert await backend.aset("k", "v") is False
    first_attempts = attempts["n"]

    # 冷却结束：自动重连试探（重新尝试建池并重新武装冷却）
    time.sleep(0.06)
    assert await backend.aset("k", "v") is False
    assert attempts["n"] == first_attempts + 3
    assert backend._resource_failed_until > time.monotonic()
