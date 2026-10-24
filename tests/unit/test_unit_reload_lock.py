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
