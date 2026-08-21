"""
后台任务归属与取消单元测试

验证 runtime/tasks 的 owner 感知调度、按归属取消与全局兜底清理。
"""

import asyncio

import pytest

from ErisPulse.runtime.context import owner_scope
from ErisPulse.runtime.tasks import (
    cancel_all_background_tasks,
    cancel_owner_tasks,
    get_owner_tasks,
    spawn_background,
)


async def _forever():
    await asyncio.sleep(100)


class TestOwnerTracking:
    """任务归属追踪测试"""

    async def test_spawn_inside_owner_scope_tracked(self):
        """owner_scope 上下文内调度的任务自动归属"""
        with owner_scope("ModA"):
            task = spawn_background(_forever())
        try:
            assert any(not t.done() for t in get_owner_tasks("ModA"))
        finally:
            await cancel_owner_tasks("ModA")

    async def test_explicit_owner_param(self):
        """显式 owner 参数覆盖上下文归属"""
        with owner_scope("CtxOwner"):
            task = spawn_background(_forever(), owner="ExplicitOwner")
        try:
            assert get_owner_tasks("ExplicitOwner")
            assert not any(not t.done() for t in get_owner_tasks("CtxOwner"))
        finally:
            await cancel_owner_tasks("ExplicitOwner")

    async def test_no_owner_tracked_under_none(self):
        """无归属上下文的任务登记在 None 键下"""
        task = spawn_background(_forever())
        try:
            assert get_owner_tasks(None)
        finally:
            await cancel_owner_tasks(None)

    async def test_task_removed_from_index_after_done(self):
        """任务完成后自动从归属索引移除"""
        with owner_scope("ModDone"):
            task = spawn_background(asyncio.sleep(0.01))
        await asyncio.sleep(0.05)
        assert task.done()
        assert not get_owner_tasks("ModDone")


class TestCancelOwnerTasks:
    """按归属取消测试"""

    async def test_cancel_returns_count_and_cancels(self):
        """取消返回任务数且任务进入 cancelled 状态"""
        with owner_scope("ModCancel"):
            tasks = [spawn_background(_forever()) for _ in range(3)]
        cancelled = await cancel_owner_tasks("ModCancel")
        assert cancelled == 3
        await asyncio.sleep(0.05)
        assert all(t.cancelled() for t in tasks)
        assert not get_owner_tasks("ModCancel")

    async def test_cancel_unknown_owner_returns_zero(self):
        """取消不存在的归属者返回 0"""
        assert await cancel_owner_tasks("NoSuchOwner") == 0

    async def test_cancel_isolated_between_owners(self):
        """取消一个归属者不影响其它归属者的任务"""
        with owner_scope("Owner1"):
            t1 = spawn_background(_forever())
        with owner_scope("Owner2"):
            t2 = spawn_background(_forever())
        try:
            await cancel_owner_tasks("Owner1")
            await asyncio.sleep(0.05)
            assert t1.cancelled()
            assert not t2.done()
        finally:
            await cancel_owner_tasks("Owner2")

    async def test_completed_task_not_counted(self):
        """已完成的任务不计入取消数"""
        with owner_scope("ModFinished"):
            spawn_background(asyncio.sleep(0.01))
        await asyncio.sleep(0.05)
        assert await cancel_owner_tasks("ModFinished") == 0


class TestCancelAllBackgroundTasks:
    """全局兜底取消测试"""

    async def test_cancel_all_covers_none_owner(self):
        """全局取消覆盖无归属任务"""
        t = spawn_background(_forever())
        with owner_scope("ModAll"):
            t2 = spawn_background(_forever())
        cancelled = await cancel_all_background_tasks()
        try:
            assert cancelled >= 2
            await asyncio.sleep(0.05)
            assert t.cancelled()
            assert t2.cancelled()
        finally:
            # 幂等：再次调用返回 0
            assert await cancel_all_background_tasks() == 0


class TestGcWithWeakref:
    """取消后实例可回收（热重载泄漏场景）"""

    async def test_module_instance_released_after_cancel(self):
        """任务持有实例引用：取消后实例可被 GC"""
        import gc
        import weakref

        class Holder:
            async def run(self):
                await asyncio.sleep(100)

        def make_worker(h):
            # 工厂闭包：h 为参数绑定，外层重绑定不影响协程持有的引用
            async def worker():
                await h.run()

            return worker

        holder = Holder()
        ref = weakref.ref(holder)

        with owner_scope("LeakyModule"):
            spawn_background(make_worker(holder)())
        holder = None
        gc.collect()
        # 任务仍存活时实例被协程帧保活
        assert ref() is not None

        await cancel_owner_tasks("LeakyModule")
        await asyncio.sleep(0.05)
        gc.collect()
        assert ref() is None, "实例应在任务取消后被回收"
