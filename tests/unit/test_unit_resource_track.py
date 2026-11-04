"""
合作式资源登记与 owner 绑定单元测试

验证 runtime/resource_track（track/untrack/release_owner_tracked）、
runtime/context.bind_owner 与跨事件循环任务取消的行为。
"""

import asyncio
import threading

import pytest

from ErisPulse.runtime.context import bind_owner, current_owner, owner_scope
from ErisPulse.runtime.resource_track import (
    get_owner_tracked,
    release_owner_tracked,
    track,
    untrack,
)
from ErisPulse.runtime.tasks import _track_owner_task, cancel_owner_tasks


class _SyncResource:
    """同步 release 的最小资源"""

    def __init__(self):
        self.released = 0

    def release(self):
        self.released += 1


class _AsyncResource:
    """异步 release 的资源"""

    def __init__(self):
        self.released = 0

    async def release(self):
        await asyncio.sleep(0)
        self.released += 1


class TestBindOwner:
    """bind_owner：谁创建谁运行"""

    async def test_sync_callable_restores_owner(self):
        """同步函数：调用期间 owner 为捕获值，返回后复位"""
        with owner_scope("Creator"):
            bound = bind_owner(lambda: current_owner.get())

        assert bound() == "Creator"
        # 调用点无 owner 上下文，不得泄漏
        assert current_owner.get() is None

    async def test_async_callable_keeps_owner_across_await(self):
        """异步函数：owner 跨 await 保持，且不污染调用方上下文"""

        async def worker():
            await asyncio.sleep(0)
            return current_owner.get()

        with owner_scope("Creator"):
            bound = bind_owner(worker)

        assert await bound() == "Creator"
        assert current_owner.get() is None

    async def test_explicit_owner_scope_wins_inside_call(self):
        """被调用方已有的 owner 上下文在调用结束后恢复"""
        with owner_scope("Creator"):
            bound = bind_owner(lambda: current_owner.get())

        with owner_scope("Caller"):
            assert bound() == "Creator"
            assert current_owner.get() == "Caller"


class TestResourceTrack:
    """合作式资源登记与释放"""

    def teardown_method(self):
        for owner in ("ModTrack", "OwnerA", "OwnerB"):
            release_owner_tracked_sync(owner)

    async def test_track_inside_owner_scope(self):
        """owner 上下文内登记 → 解析出 owner 并可查回"""
        resource = _SyncResource()
        with owner_scope("ModTrack"):
            owner = track(resource)

        assert owner == "ModTrack"
        assert get_owner_tracked("ModTrack") == [resource]

    async def test_release_owner_tracked_calls_sync_release(self):
        """release_owner_tracked 调用同步 release 并清空登记"""
        resource = _SyncResource()
        with owner_scope("ModTrack"):
            track(resource)

        count = await release_owner_tracked("ModTrack")

        assert count == 1
        assert resource.released == 1
        assert get_owner_tracked("ModTrack") == []

    async def test_release_owner_tracked_awaits_async_release(self):
        """release() 返回 awaitable 时释放链等待其完成"""
        resource = _AsyncResource()
        with owner_scope("ModTrack"):
            track(resource)

        count = await release_owner_tracked("ModTrack")

        assert count == 1
        assert resource.released == 1

    async def test_release_error_isolated(self):
        """单个资源释放失败不影响其余资源"""

        class _Broken:
            def release(self):
                raise RuntimeError("boom")

        good = _SyncResource()
        broken = _Broken()
        with owner_scope("ModTrack"):
            track(broken)
            track(good)

        count = await release_owner_tracked("ModTrack")

        assert count == 1
        assert good.released == 1

    async def test_untrack_removes_registration(self):
        """untrack 注销后不再随归属释放"""
        resource = _SyncResource()
        with owner_scope("OwnerA"):
            track(resource)

        removed = untrack(resource)

        assert removed == 1
        assert get_owner_tracked("OwnerA") == []
        assert resource.released == 0

    async def test_track_requires_owner(self):
        """无 owner 上下文且未显式传入 → ValueError"""
        with pytest.raises(ValueError):
            track(_SyncResource())

    async def test_track_requires_release_method(self):
        """资源未实现 release() → ValueError"""
        with owner_scope("OwnerA"):
            with pytest.raises(ValueError):
                track(object())

    async def test_explicit_owner_overrides_context(self):
        """显式 owner 参数优先于上下文"""
        resource = _SyncResource()
        with owner_scope("OwnerA"):
            owner = track(resource, owner="OwnerB")

        assert owner == "OwnerB"
        assert get_owner_tracked("OwnerB") == [resource]


def release_owner_tracked_sync(owner: str) -> None:
    """teardown 辅助：同步清理登记表（避免在同步 teardown 中 await）"""
    from ErisPulse.runtime import resource_track

    resource_track._owner_tracked.pop(owner, None)


class TestCrossLoopCancel:
    """跨事件循环任务取消：线程安全取消 + 不参与回收等待"""

    async def test_cross_loop_task_cancelled_without_runtime_error(self):
        """异环任务经 call_soon_threadsafe 取消，gather 不混入异环 Task"""
        loop = asyncio.new_event_loop()
        ready = threading.Event()
        future_holder = {}

        def _run():
            asyncio.set_event_loop(loop)
            ready.set()
            loop.run_forever()

        thread = threading.Thread(target=_run, daemon=True)
        thread.start()
        assert ready.wait(5)

        async def _forever():
            await asyncio.sleep(100)

        try:
            future = asyncio.run_coroutine_threadsafe(_forever(), loop)
            _track_owner_task("CrossLoopMod", future)

            cancelled = await cancel_owner_tasks("CrossLoopMod", timeout=1.0)

            assert cancelled == 1
            # 取消已投递：等待其生效，确认任务确实被取消而非残留
            for _ in range(50):
                if future.done():
                    break
                await asyncio.sleep(0.02)
            assert future.done()
            assert future.cancelled()
        finally:
            # 给取消留出在本循环内收尾的时间，再停循环（避免 pending task 警告）
            await asyncio.sleep(0.05)
            loop.call_soon_threadsafe(loop.stop)
            thread.join(timeout=5)
            loop.close()
