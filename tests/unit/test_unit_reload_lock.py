"""
热重载互斥协调器（ReloadOpsCoordinator）单元测试

覆盖：并发 restart 串行 + dirty 合并补跑、重入直通、限时获取超时跳过、
锁被取消后可继续获取。
"""

import asyncio

import pytest

from ErisPulse.runtime.reload_ops import (
    ReloadOpsCoordinator,
    reload_ops,
    run_reload_exclusive,
)


@pytest.mark.unit
class TestReloadOpsCoordinator:
    """互斥与合并语义"""

    @pytest.mark.asyncio
    async def test_concurrent_sections_serialized(self):
        """两个并发互斥区不交叉执行"""
        coord = ReloadOpsCoordinator()
        events: list[str] = []

        async def worker(tag: str, delay: float):
            async with coord:
                events.append(f"enter-{tag}")
                await asyncio.sleep(delay)
                events.append(f"exit-{tag}")

        await asyncio.gather(worker("a", 0.05), worker("b", 0.0))
        # 串行：某个 worker 完整进出后另一个才进入
        assert events[0].startswith("enter-")
        assert events.index("enter-b") > events.index("exit-a") or events.index(
            "enter-a"
        ) > events.index("exit-b")

    @pytest.mark.asyncio
    async def test_restart_dirty_coalesce(self):
        """restart 进行中收到请求 → 合并为 dirty，完成后消费一次"""
        coord = ReloadOpsCoordinator()
        rounds: list[int] = []
        entered = asyncio.Event()

        async def restart_loop():
            async with coord:
                coord.begin_restart_section()
                entered.set()
                await asyncio.sleep(0)  # 让出控制权：等外部合并请求进入
                while True:
                    rounds.append(1)
                    if not coord.consume_restart_dirty():
                        break

        task = asyncio.ensure_future(restart_loop())
        await entered.wait()
        assert coord.mark_restart_pending() is True  # 合并
        assert coord.mark_restart_pending() is True  # 再次合并仍是同一次
        await asyncio.sleep(0.01)
        assert coord.mark_restart_pending() is False  # 已结束（锁释放）
        await task
        assert len(rounds) == 2  # 1 轮本体 + 1 轮补跑

    @pytest.mark.asyncio
    async def test_mark_pending_when_idle_returns_false(self):
        """无 restart 持锁时 mark_restart_pending 返回 False（调用方自行调度）"""
        coord = ReloadOpsCoordinator()
        assert coord.mark_restart_pending() is False

    @pytest.mark.asyncio
    async def test_reentrant_pass_through(self):
        """持锁任务内经 run_reload_exclusive 再入直接执行（不自杀锁）"""
        result: list[str] = []

        async def inner():
            result.append("inner")
            return "ok"

        async def outer():
            async with reload_ops:
                # 模拟 on_unload 钩子内再触发重载
                return await run_reload_exclusive(inner)

        assert await outer() == "ok"
        assert result == ["inner"]

    @pytest.mark.asyncio
    async def test_run_or_skip_timeout_skips(self):
        """锁被**其它任务**长期占用时 run_or_skip 超时跳过返回 None"""
        coord = ReloadOpsCoordinator()
        holder_entered = asyncio.Event()
        release = asyncio.Event()

        async def holder():
            async with coord:
                holder_entered.set()
                await release.wait()  # 长时间持锁

        holder_task = asyncio.ensure_future(holder())
        await holder_entered.wait()

        called: list[int] = []

        async def fn():
            called.append(1)
            return "ran"

        try:
            result = await coord.run_or_skip(
                fn,
                timeout=0.02,
                skip_log_key="core.module.dormancy_sweep_skipped",
                log_params={"name": "x"},
            )
            assert result is None
            assert called == []
        finally:
            release.set()
            await holder_task

    @pytest.mark.asyncio
    async def test_lock_released_after_cancelled_holder(self):
        """持锁任务被取消后锁可被后续获取"""
        coord = ReloadOpsCoordinator()

        async def holder():
            async with coord:
                await asyncio.sleep(10)

        task = asyncio.ensure_future(holder())
        await asyncio.sleep(0.01)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task

        acquired: list[int] = []

        async def follower():
            async with coord:
                acquired.append(1)

        await asyncio.wait_for(follower(), timeout=1.0)
        assert acquired == [1]

    @pytest.mark.asyncio
    async def test_module_level_singleton_is_coordinator(self):
        """模块级单例与类实例语义一致"""
        assert isinstance(reload_ops, ReloadOpsCoordinator)
        assert reload_ops.is_locked() is False


@pytest.mark.unit
class TestRestartDeferredMerge:
    """restart 请求落在普通 reload 持锁期间：deferred 登记 + 后续并入"""

    @pytest.mark.asyncio
    async def test_deferred_registered_then_merged(self):
        """非 restart 持锁：首个请求登记 deferred，后续请求并入（至多一轮）"""
        coord = ReloadOpsCoordinator()
        release = asyncio.Event()

        async def holder():
            async with coord:
                await release.wait()

        task = asyncio.ensure_future(holder())
        await asyncio.sleep(0.01)
        try:
            # 首个 restart：登记 deferred，调用方自行调度（排队等锁）
            assert coord.mark_restart_pending() is False
            assert coord._restart_deferred is True
            # 后续 restart：并入已排队的请求，不再额外调度
            assert coord.mark_restart_pending() is True
            assert coord.mark_restart_pending() is True
        finally:
            release.set()
            await task

        # 排队请求获得锁（或执行体退出）后登记清零，放行后续 restart
        coord._restart_deferred = True
        coord.clear_restart_deferred()
        # 锁空闲：新请求正常返回 False（需自行调度）
        assert coord.mark_restart_pending() is False

    @pytest.mark.asyncio
    async def test_dirty_merge_during_restart_holder_unchanged(self):
        """restart 持锁期间：请求仍走 dirty 合并（原语义不回归）"""
        coord = ReloadOpsCoordinator()
        release = asyncio.Event()

        async def restart_holder():
            async with coord:
                coord.begin_restart_section()
                await release.wait()

        task = asyncio.ensure_future(restart_holder())
        await asyncio.sleep(0.01)
        try:
            assert coord.mark_restart_pending() is True
            assert coord.consume_restart_dirty() is True
        finally:
            release.set()
            await task


@pytest.mark.unit
class TestUnloadPublicEntryMutex:
    """module/adapter unload() 公共入口纳入热重载互斥（限时等待 + 超时降级）"""

    @pytest.mark.asyncio
    async def test_unload_waits_until_lock_released(self):
        """重载持锁期间外部 unload 排队等待，锁释放后执行（不交叉）"""
        from ErisPulse.Core.module import ModuleManager

        release = asyncio.Event()

        async def reload_holder():
            async with reload_ops:
                await release.wait()

        holder = asyncio.ensure_future(reload_holder())
        await asyncio.sleep(0.01)
        manager = ModuleManager()
        try:
            task = asyncio.ensure_future(manager.unload("nothing_loaded"))
            await asyncio.sleep(0.05)
            # 持锁期间 unload 未完成（在等锁，不与重载交叉）
            assert not task.done()
            release.set()
            await holder
            assert await asyncio.wait_for(task, timeout=2.0) is True
        finally:
            release.set()
            await holder

    @pytest.mark.asyncio
    async def test_unload_reentrant_inside_reload_pipeline(self):
        """重载管线内部（同任务已持锁）调用 unload：重入直通不死锁"""
        from ErisPulse.Core.module import ModuleManager

        manager = ModuleManager()

        async def pipeline():
            async with reload_ops:
                return await manager.unload("nothing_loaded")

        assert await asyncio.wait_for(pipeline(), timeout=2.0) is True

    @pytest.mark.asyncio
    async def test_unload_degrades_after_timeout(self, monkeypatch, caplog):
        """持锁重载长时间卡死：限时等待超时后降级直接执行并留痕"""
        import importlib

        from ErisPulse.Core.module import ModuleManager

        # ErisPulse.Core 聚合导出把 module 名字绑定为管理器实例，
        # import ... as 拿到的是实例——经 sys.modules 取真身模块
        core_module_mod = importlib.import_module("ErisPulse.Core.module")
        monkeypatch.setattr(core_module_mod, "UNLOAD_LOCK_WAIT_TIMEOUT_SECS", 0.05)
        release = asyncio.Event()

        async def stuck_reload():
            async with reload_ops:
                await release.wait()

        holder = asyncio.ensure_future(stuck_reload())
        await asyncio.sleep(0.01)
        try:
            with caplog.at_level("WARNING"):
                manager = ModuleManager()
                assert await asyncio.wait_for(manager.unload("nothing_loaded"), timeout=2.0) is True
            assert any("unload_lock_timeout" in r.getMessage() or "降级" in r.getMessage() for r in caplog.records)
        finally:
            release.set()
            await holder

    @pytest.mark.asyncio
    async def test_adapter_unload_waits_for_lock(self):
        """adapter.unload 同样进入互斥：持锁期间排队"""
        from ErisPulse.Core.adapter import AdapterManager

        release = asyncio.Event()

        async def reload_holder():
            async with reload_ops:
                await release.wait()

        holder = asyncio.ensure_future(reload_holder())
        await asyncio.sleep(0.01)
        manager = AdapterManager()
        try:
            task = asyncio.ensure_future(manager.unload("ghost_platform"))
            await asyncio.sleep(0.05)
            assert not task.done()
            release.set()
            await holder
            # 未注册平台：等锁完成后正常走「未注册」分支返回 False
            assert await asyncio.wait_for(task, timeout=2.0) is False
        finally:
            release.set()
            await holder
