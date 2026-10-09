"""
连接注册表（连接池）单元测试

覆盖：登记/注销与索引、分组（连接侧 + 管理侧）、广播（过滤/排除/ids/
超时/失败明细）、跨模块关闭权限三态、close_owner、run_main_loop 跨线程桥、
spawn_later 归属定时器、spawn_thread 线程观测。
"""

import asyncio
import threading

import pytest

from ErisPulse.Core.Bases.errors import (
    ConnectionNotFoundError,
    ConnectionPermissionError,
)
from ErisPulse.Core.Bases.websocket import WebSocketConnectionBase, _ConnectionIdentity
from ErisPulse.Core.connections import BroadcastResult, ConnectionManager
from ErisPulse.runtime.context import owner_scope


class _FakeRaw:
    def __init__(self):
        self.sent: list = []
        self.closed = False

    async def send_json(self, data):
        self.sent.append(data)

    async def _close(self, code=1000, reason=None):
        self.closed = True


class _FakeConn(WebSocketConnectionBase):
    """测试用连接：鸭子类型实现连接池所需接口"""

    async def send_text(self, data):
        pass

    async def send_bytes(self, data):
        pass

    async def send_json(self, data, mode="text"):
        await self._ws.send_json(data)

    async def _close(self, code=1000, reason=None):
        await self._ws._close()


class _FakeSse(_ConnectionIdentity):
    """测试用 SSE 连接：send 即广播目标方法（共享身份混入，与真实 SseEmitter 一致）"""

    def __init__(self):
        super().__init__(kind="sse")
        self.sent: list = []
        self.closed = False

    async def send(self, data):
        self.sent.append(data)

    async def close(self, *, force=False):
        self.closed = True


@pytest.fixture()
def mgr():
    """全新 ConnectionManager（不污染全局单例）"""
    return ConnectionManager()


@pytest.fixture()
def clean_global():
    """每个用例后清空全局单例，防止跨用例污染"""
    from ErisPulse import connections as global_mgr

    yield global_mgr
    global_mgr.clear()


def _make_conn():
    return _FakeConn(_FakeRaw(), kind="server")


# ==================== 登记 / 注销 / 查询 ====================


class TestRegistry:
    def test_register_assigns_id_and_indexes(self, mgr):
        conn = _make_conn()
        cid = mgr.register(conn, namespace="ModA", kind="server", owner="ModA")
        assert cid == conn.id
        assert cid.startswith("ModA:")
        assert mgr.list(namespace="ModA") == [conn]
        assert mgr.list(owner="ModA") == [conn]
        assert len(mgr) == 1

    def test_unregister_removes_all_indexes(self, mgr):
        conn = _make_conn()
        mgr.register(conn, namespace="ModA", kind="server", owner="ModA")
        conn.join_group("room")
        assert mgr.unregister(conn) is True
        assert len(mgr) == 0
        assert conn.groups == frozenset()
        assert mgr.list(group="room") == []
        # 幂等
        assert mgr.unregister(conn) is False

    def test_get_not_found(self, mgr):
        with pytest.raises(ConnectionNotFoundError):
            mgr.get("ghost:00")

    def test_stats(self, mgr):
        a, b = _make_conn(), _make_conn()
        mgr.register(a, namespace="ModA", kind="server", owner="ModA")
        mgr.register(b, namespace="ModB", kind="client", owner="ModB")
        b.join_group("g1")
        stats = mgr.stats()
        assert stats["total"] == 2
        assert stats["by_kind"] == {"server": 1, "client": 1}
        assert stats["by_owner"]["ModA"] == 1
        assert stats["groups"] == {"g1": 1}

    def test_counts_for_ownership(self, mgr):
        conn = _make_conn()
        mgr.register(conn, namespace="ModA", kind="server", owner="ModA")
        assert mgr.counts() == {"connections": 1, "connection_groups": 0}
        conn.join_group("g")
        assert mgr.counts()["connection_groups"] == 1


# ==================== 分组 ====================


class TestGroups:
    def test_join_and_leave_via_conn(self, mgr):
        conn = _make_conn()
        mgr.register(conn, namespace="ModA", kind="server", owner="ModA")
        conn.join_group("room:1", "room:2")
        assert conn.groups == frozenset({"room:1", "room:2"})
        assert mgr.list(group="room:1") == [conn]
        conn.leave_group("room:1")
        assert conn.groups == frozenset({"room:2"})
        conn.leave_group()  # 全部退出
        assert conn.groups == frozenset()

    def test_assign_and_dismiss(self, mgr):
        conn = _make_conn()
        cid = mgr.register(conn, namespace="ModA", kind="server", owner="ModA")
        mgr.assign(cid, "tenant:a", "tenant:b")
        assert conn.groups == frozenset({"tenant:a", "tenant:b"})
        mgr.dismiss(cid, "tenant:a")
        assert conn.groups == frozenset({"tenant:b"})
        mgr.dismiss(cid)  # 不传参 = 全部退出
        assert conn.groups == frozenset()

    def test_assign_unknown_raises(self, mgr):
        with pytest.raises(ConnectionNotFoundError):
            mgr.assign("ghost:00", "g")

    def test_group_cleanup_on_unregister(self, mgr):
        conn = _make_conn()
        mgr.register(conn, namespace="ModA", kind="server", owner="ModA")
        conn.join_group("room")
        mgr.unregister(conn)
        assert mgr.list(group="room") == []


# ==================== 广播 ====================


class TestBroadcast:
    async def test_broadcast_by_namespace(self, mgr):
        a, b = _make_conn(), _make_conn()
        mgr.register(a, namespace="ModA", kind="server", owner="ModA")
        mgr.register(b, namespace="ModB", kind="server", owner="ModB")
        result = await mgr.broadcast({"ping": 1}, namespace="ModA")
        assert isinstance(result, BroadcastResult)
        assert result.ok
        assert result.sent == [a.id]
        assert a._ws.sent == [{"ping": 1}]
        assert b._ws.sent == []

    async def test_broadcast_exclude(self, mgr):
        a, b = _make_conn(), _make_conn()
        mgr.register(a, namespace="ModA", kind="server", owner="ModA")
        mgr.register(b, namespace="ModA", kind="server", owner="ModA")
        result = await mgr.broadcast({"x": 1}, namespace="ModA", exclude={a.id})
        assert result.sent == [b.id]
        assert result.excluded == [a.id]
        assert result.total == 2

    async def test_broadcast_ids_with_missing(self, mgr):
        a = _make_conn()
        mgr.register(a, namespace="ModA", kind="server", owner="ModA")
        result = await mgr.broadcast({"x": 1}, ids=[a.id, "ghost:99"])
        assert result.sent == [a.id]
        assert "ghost:99" in result.failed
        assert result.total == 2

    async def test_broadcast_reports_send_failure(self, mgr):
        conn = _make_conn()
        mgr.register(conn, namespace="ModA", kind="server", owner="ModA")

        async def _boom(data):
            raise RuntimeError("broken pipe")

        conn.send_json = _boom
        result = await mgr.broadcast({"x": 1}, namespace="ModA")
        assert not result.ok
        assert conn.id in result.failed
        assert "broken pipe" in str(result.failed[conn.id])

    async def test_broadcast_raise_on_error(self, mgr):
        conn = _make_conn()
        mgr.register(conn, namespace="ModA", kind="server", owner="ModA")

        async def _boom(data):
            raise RuntimeError("broken pipe")

        conn.send_json = _boom
        with pytest.raises(RuntimeError):
            await mgr.broadcast({"x": 1}, namespace="ModA", raise_on_error=True)

    async def test_broadcast_timeout_per_target(self, mgr):
        slow, fast = _make_conn(), _make_conn()
        mgr.register(slow, namespace="ModA", kind="server", owner="ModA")
        mgr.register(fast, namespace="ModA", kind="server", owner="ModA")

        async def _stall(data):
            await asyncio.sleep(5)

        slow.send_json = _stall
        result = await mgr.broadcast({"x": 1}, namespace="ModA", timeout=0.05)
        assert result.sent == [fast.id]
        assert slow.id in result.failed

    async def test_broadcast_to_sse_uses_send(self, mgr):
        sse = _FakeSse()
        mgr.register(sse, namespace="Dash", kind="sse", owner="Dash")
        result = await mgr.broadcast({"msg": 1}, kind="sse")
        assert result.ok
        assert sse.sent == [{"msg": 1}]

    async def test_broadcast_empty_target(self, mgr):
        result = await mgr.broadcast({"x": 1}, namespace="Nobody")
        assert result.total == 0 and result.ok


# ==================== 关闭权限 / 回收 ====================


class TestClosePermission:
    async def test_cross_owner_close_denied(self, mgr):
        conn = _make_conn()
        mgr.register(conn, namespace="ModA", kind="server", owner="ModA")
        with owner_scope("ModB"):
            with pytest.raises(ConnectionPermissionError):
                await conn.close()
        assert not conn._ws.closed

    async def test_owner_close_allowed(self, mgr):
        conn = _make_conn()
        mgr.register(conn, namespace="ModA", kind="server", owner="ModA")
        with owner_scope("ModA"):
            await conn.close()
        assert conn._ws.closed

    async def test_empty_context_allowed(self, mgr):
        """上下文不可归因（框架内部路径/老代码）放行——0 破坏关键"""
        conn = _make_conn()
        mgr.register(conn, namespace="ModA", kind="server", owner="ModA")
        await conn.close()
        assert conn._ws.closed

    async def test_force_bypasses(self, mgr):
        conn = _make_conn()
        mgr.register(conn, namespace="ModA", kind="server", owner="ModA")
        with owner_scope("ModB"):
            await conn.close(force=True)
        assert conn._ws.closed

    async def test_manager_close_unregisters(self, mgr):
        conn = _make_conn()
        mgr.register(conn, namespace="ModA", kind="server", owner="ModA")
        with owner_scope("ModA"):
            await mgr.close(conn.id)
        assert len(mgr) == 0

    async def test_close_owner(self, mgr):
        a, b = _make_conn(), _make_conn()
        mgr.register(a, namespace="ModA", kind="server", owner="ModA")
        mgr.register(b, namespace="ModB", kind="server", owner="ModB")
        closed = await mgr.close_owner("ModA")
        assert closed == 1
        assert len(mgr) == 1
        assert a._ws.closed and not b._ws.closed
        assert await mgr.close_owner("Nobody") == 0


# ==================== run_main_loop 跨线程桥 ====================


class TestRunMainLoop:
    async def test_thread_bridge_returns_result(self):
        from ErisPulse import run_main_loop
        from ErisPulse.runtime.tasks import register_main_loop

        register_main_loop(asyncio.get_running_loop())
        box = {}

        def worker():
            box["value"] = run_main_loop(asyncio.sleep(0.01, result=42), timeout=5)

        t = threading.Thread(target=worker)
        t.start()
        while t.is_alive():
            await asyncio.sleep(0.01)
        assert box["value"] == 42

    async def test_main_loop_sync_call_rejected(self):
        from ErisPulse import run_main_loop
        from ErisPulse.runtime.tasks import register_main_loop

        # 每个用例独立事件循环，需先注册当前 loop（模拟 sdk.run 启动注册）
        register_main_loop(asyncio.get_running_loop())
        coro = asyncio.sleep(0)
        with pytest.raises(RuntimeError, match="await"):
            run_main_loop(coro)
        coro.close()  # 拒绝路径不会消费协程，显式关闭避免 RuntimeWarning


# ==================== spawn_later / spawn_thread ====================


class TestSpawnLater:
    async def test_fires_and_schedules_owned(self):
        from ErisPulse import spawn_later

        done = []

        def factory():
            async def _go():
                done.append(1)

            return _go()

        spawn_later(0.01, factory, owner="LaterMod")
        await asyncio.sleep(0.08)
        assert done == [1]

    async def test_cancel_via_owner_tasks(self):
        from ErisPulse import spawn_later
        from ErisPulse.runtime import cancel_owner_tasks, get_owner_timers

        def factory():
            async def _go():
                pass

            return _go()

        spawn_later(60, factory, owner="TimerMod")
        assert len(get_owner_timers("TimerMod")) == 1
        await cancel_owner_tasks("TimerMod")
        assert get_owner_timers("TimerMod") == set()

    async def test_non_awaitable_factory_no_crash(self):
        from ErisPulse import spawn_later

        spawn_later(0.01, lambda: 123, owner="BadMod")
        await asyncio.sleep(0.05)  # 不应抛异常，仅留痕


class TestSpawnThread:
    def test_registers_and_cleans_on_exit(self):
        from ErisPulse import spawn_thread
        from ErisPulse.runtime.tasks import get_owner_threads

        th = spawn_thread("probe", lambda: None, owner="ThreadMod")
        th.join(timeout=2)
        assert get_owner_threads("ThreadMod") == set()

    def test_alive_thread_visible(self):
        from ErisPulse import spawn_thread
        from ErisPulse.runtime.tasks import get_owner_threads

        release = threading.Event()
        th = spawn_thread("sleeper", release.wait, owner="AliveMod")
        try:
            assert th in get_owner_threads("AliveMod")
        finally:
            release.set()
            th.join(timeout=2)
        assert get_owner_threads("AliveMod") == set()


# ==================== 全局单例与框架接线 ====================


class TestGlobalSingleton:
    async def test_global_register_and_unload_chain(self, clean_global):
        """module 卸载链的 close_owner 路径（模拟）"""
        conn = _make_conn()
        clean_global.register(conn, namespace="UnloadMod", kind="server", owner="UnloadMod")
        assert clean_global.stats()["total"] == 1
        assert await clean_global.close_owner("UnloadMod") == 1
        assert clean_global.stats()["total"] == 0

    def test_clear_by_kind(self, clean_global):
        server_conn, client_conn = _make_conn(), _make_conn()
        clean_global.register(server_conn, namespace="A", kind="server", owner="A")
        clean_global.register(client_conn, kind="client", owner="B")
        assert clean_global.clear(kind="server") == 1
        assert clean_global.stats()["by_kind"] == {"client": 1}

    async def test_ownership_counts_sees_connections(self, clean_global):
        from ErisPulse import ownership

        conn = _make_conn()
        clean_global.register(conn, namespace="CountedMod", kind="server", owner="CountedMod")
        try:
            assert ownership.counts("CountedMod").get("connections") == 1
        finally:
            clean_global.unregister(conn)

    async def test_ws_base_join_group_uses_manager(self, clean_global):
        conn = _make_conn()
        cid = clean_global.register(conn, namespace="GrpMod", kind="server", owner="GrpMod")
        conn.join_group("ws-room")
        assert clean_global.list(group="ws-room") == [conn]
        conn.leave_group("ws-room")
        assert clean_global.list(group="ws-room") == []
        assert conn.id == cid
