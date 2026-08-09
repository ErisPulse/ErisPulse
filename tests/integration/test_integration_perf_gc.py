"""
性能优化与资源回收集成测试

端到端验证本次性能优化引入的关键能力：
1. 事件处理器 Task 追踪与 shutdown 清理
2. 事件处理器并发背压（Semaphore）
3. 生命周期钩子 owner 追踪与模块卸载时自动清理
4. 适配器资源清理时联动清理生命周期钩子
5. wait_reply CancelledError 安全清理
6. 离线 Bot 自动过期回收
7. 限流存储过期清理
8. 主动 GC 后台任务启停
"""

import asyncio
import time
from unittest.mock import patch

import pytest

from ErisPulse.Core.adapter import adapter
from ErisPulse.Core.Event import _clear_all_handlers, message
from ErisPulse.Core.lifecycle import lifecycle
from ErisPulse.runtime.context import current_owner

# ==================== 辅助函数 ====================


def _make_msg(text="/hello", platform="perf_test", **kwargs):
    data = {
        "id": "perf_001",
        "time": 1712345678,
        "type": "message",
        "detail_type": "private",
        "platform": platform,
        "self": {"platform": platform, "user_id": "bot_perf"},
        "user_id": "u1",
        "user_nickname": "User1",
        "message": [{"type": "text", "data": {"text": text}}],
        "alt_message": text,
    }
    data.update(kwargs)
    return data


@pytest.fixture
def clean_state():
    """清理全局状态"""
    _clear_all_handlers()
    lifecycle._hooks.clear()
    lifecycle._timers.clear()
    adapter._onebot_handlers.clear()
    adapter._raw_handlers.clear()
    adapter._onebot_middlewares.clear()
    adapter._bots.clear()
    adapter._pending_handler_tasks.clear()
    adapter._handler_semaphore = None
    adapter._handler_max_concurrency = 0
    yield
    _clear_all_handlers()
    lifecycle._hooks.clear()
    lifecycle._timers.clear()
    adapter._onebot_handlers.clear()
    adapter._raw_handlers.clear()
    adapter._onebot_middlewares.clear()
    adapter._bots.clear()
    adapter._pending_handler_tasks.clear()
    adapter._handler_semaphore = None
    adapter._handler_max_concurrency = 0


# ==================== Task 追踪与 shutdown 清理 ====================


class TestHandlerTaskTrackingIntegration:
    """事件处理器 Task 追踪集成测试"""

    @pytest.mark.asyncio
    async def test_emit_creates_tracked_tasks(self, clean_state):
        """emit 后 handler Task 被追踪到 _pending_handler_tasks"""

        @adapter.on("message")
        async def handler(data):
            await asyncio.sleep(0.05)

        await adapter.emit(_make_msg("test"))
        await asyncio.sleep(0)  # 让 Task 创建

        assert len(adapter._pending_handler_tasks) > 0

        # 等待 handler 完成
        await asyncio.sleep(0.1)

        # Task 完成后自动从集合移除
        assert len(adapter._pending_handler_tasks) == 0

    @pytest.mark.asyncio
    async def test_multiple_handlers_all_tracked(self, clean_state):
        """多个 handler 各自创建被追踪的 Task"""

        @adapter.on("message")
        async def h1(data):
            await asyncio.sleep(0.05)

        @adapter.on("message")
        async def h2(data):
            await asyncio.sleep(0.05)

        await adapter.emit(_make_msg("test"))
        await asyncio.sleep(0)

        # 两个 handler 各一个 Task
        assert len(adapter._pending_handler_tasks) == 2

        await asyncio.sleep(0.15)
        assert len(adapter._pending_handler_tasks) == 0

    @pytest.mark.asyncio
    async def test_drain_cancels_inflight_tasks(self, clean_state):
        """shutdown drain 取消所有未完成的 handler Task"""

        @adapter.on("message")
        async def slow_handler(data):
            await asyncio.sleep(100)  # 永不自然结束

        await adapter.emit(_make_msg("test"))
        await asyncio.sleep(0)

        assert len(adapter._pending_handler_tasks) == 1

        # 模拟 shutdown drain
        await adapter._drain_pending_handler_tasks(timeout=2.0)

        assert len(adapter._pending_handler_tasks) == 0

    @pytest.mark.asyncio
    async def test_task_auto_removed_on_exception(self, clean_state):
        """handler 抛异常后 Task 仍自动从集合移除"""

        @adapter.on("message")
        async def bad_handler(data):
            raise ValueError("boom")

        await adapter.emit(_make_msg("test"))
        await asyncio.sleep(0.1)

        assert len(adapter._pending_handler_tasks) == 0


# ==================== 并发背压 ====================


class TestHandlerBackpressureIntegration:
    """事件处理器并发背压集成测试"""

    @pytest.mark.asyncio
    async def test_concurrency_does_not_exceed_limit(self, clean_state):
        """并发 handler 数不超过 semaphore 限制"""
        # 设置很小的并发限制
        adapter._handler_max_concurrency = 3
        adapter._handler_semaphore = asyncio.Semaphore(3)

        current_concurrent = [0]
        max_concurrent = [0]

        @adapter.on("message")
        async def handler(data):
            current_concurrent[0] += 1
            max_concurrent[0] = max(max_concurrent[0], current_concurrent[0])
            await asyncio.sleep(0.05)
            current_concurrent[0] -= 1

        # 连续发送 20 条消息
        for i in range(20):
            await adapter.emit(_make_msg(f"msg_{i}"))

        await asyncio.sleep(0.5)

        assert max_concurrent[0] <= 3

    @pytest.mark.asyncio
    async def test_all_events_processed_under_backpressure(self, clean_state):
        """背压下所有事件最终都被处理"""
        adapter._handler_max_concurrency = 2
        adapter._handler_semaphore = asyncio.Semaphore(2)

        processed = []

        @adapter.on("message")
        async def handler(data):
            processed.append(data.get("alt_message"))
            await asyncio.sleep(0.01)

        # 发送 10 条消息
        for i in range(10):
            await adapter.emit(_make_msg(f"msg_{i}"))

        await asyncio.sleep(0.5)

        assert len(processed) == 10

    @pytest.mark.asyncio
    async def test_semaphore_lazy_init_from_config(self, clean_state):
        """信号量懒初始化，首次使用时创建"""
        adapter._handler_semaphore = None
        adapter._handler_max_concurrency = 0

        @adapter.on("message")
        async def handler(data):
            pass

        await adapter.emit(_make_msg("test"))
        await asyncio.sleep(0.1)

        # 信号量应被初始化
        assert adapter._handler_semaphore is not None
        assert adapter._handler_max_concurrency > 0


# ==================== 生命周期钩子 owner 追踪与清理 ====================


class TestLifecycleOwnerCleanupIntegration:
    """生命周期钩子在模块/适配器卸载时自动清理的集成测试"""

    @pytest.mark.asyncio
    async def test_module_unload_cleans_lifecycle_hooks(self, clean_state):
        """模块卸载时自动清理该模块注册的生命周期钩子"""
        # 模拟模块加载上下文
        token = current_owner.set("TestModule")
        try:

            @lifecycle.on("custom.event")
            async def handler(data):
                pass

            @lifecycle.on("another.event")
            async def handler2(data):
                pass
        finally:
            current_owner.reset(token)

        # 验证钩子存在
        assert "custom.event" in lifecycle._hooks
        assert "another.event" in lifecycle._hooks

        # 模拟模块卸载时清理
        removed = lifecycle.unregister_by_owner("TestModule")

        assert removed == 2
        assert "custom.event" not in lifecycle._hooks
        assert "another.event" not in lifecycle._hooks

    @pytest.mark.asyncio
    async def test_framework_hooks_not_cleaned_by_module_unload(self, clean_state):
        """模块卸载不影响框架自身注册的钩子"""
        # 框架注册（无 owner）

        @lifecycle.on("core.event")
        async def core_handler(data):
            pass

        # 模块注册
        token = current_owner.set("MyModule")
        try:

            @lifecycle.on("module.event")
            async def mod_handler(data):
                pass
        finally:
            current_owner.reset(token)

        # 卸载模块
        removed = lifecycle.unregister_by_owner("MyModule")
        assert removed == 1

        # 框架钩子不受影响
        assert "core.event" in lifecycle._hooks
        assert len(lifecycle._hooks["core.event"]) == 1

    @pytest.mark.asyncio
    async def test_adapter_cleanup_cleans_lifecycle_hooks(self, clean_state):
        """适配器资源清理时联动清理生命周期钩子"""
        # 模拟适配器注册钩子
        token = current_owner.set("MyPlatform")
        try:

            @lifecycle.on("adapter.custom")
            async def handler(data):
                pass
        finally:
            current_owner.reset(token)

        assert "adapter.custom" in lifecycle._hooks

        # 调用适配器资源清理
        adapter._cleanup_adapter_resources("MyPlatform")

        # 钩子应被清理
        assert "adapter.custom" not in lifecycle._hooks

    @pytest.mark.asyncio
    async def test_hooks_still_fire_after_owner_tracking(self, clean_state):
        """owner 追踪不影响钩子正常触发"""
        results = []

        token = current_owner.set("TestMod")
        try:

            @lifecycle.on("test.fire")
            async def handler(data):
                results.append(data)
        finally:
            current_owner.reset(token)

        await lifecycle.emit("test.fire", {"key": "value"})

        assert len(results) == 1
        assert results[0]["key"] == "value"

    @pytest.mark.asyncio
    async def test_emit_sync_works_with_owner_tuples(self, clean_state):
        """emit_sync 正常工作（同步模式下处理三元组）"""
        results = []

        def sync_handler(data):
            results.append(data)

        lifecycle.register("sync.event", sync_handler)

        lifecycle.emit_sync("sync.event", {"test": True})

        assert len(results) == 1


# ==================== wait_reply CancelledError 安全清理 ====================


class TestWaitReplyCleanupIntegration:
    """wait_reply 在 Task 取消时的安全清理集成测试"""

    @pytest.mark.asyncio
    async def test_wait_reply_cleans_on_cancel(self, clean_state):
        """wait_reply 被 cancel 时 _waiting_replies 不残留"""
        from ErisPulse.Core.Event.command import command as cmd_handler

        wait_task = None

        @adapter.on("message")
        async def handler(data):
            nonlocal wait_task
            # 启动 wait_reply
            from ErisPulse.Core.Event.wrapper import Event

            event = Event(data)
            loop = asyncio.get_running_loop()
            wait_task = loop.create_task(cmd_handler.wait_reply(event, timeout=30))
            await asyncio.sleep(0.05)  # 等 wait_reply 注册

        await adapter.emit(_make_msg("test"))
        await asyncio.sleep(0.1)

        # wait_task 应已创建并在等待
        assert wait_task is not None
        assert not wait_task.done()

        # 取消 wait_reply Task
        wait_task.cancel()
        try:
            await wait_task
        except asyncio.CancelledError:
            pass

        # _waiting_replies 应被 finally 清理
        matching_keys = [k for k in cmd_handler._waiting_replies if "perf_test" in k]
        assert len(matching_keys) == 0


# ==================== 离线 Bot 自动过期回收 ====================


class TestOfflineBotEvictionIntegration:
    """离线 Bot 记录自动过期回收集成测试"""

    def test_evict_old_offline_bots(self, clean_state):
        """清除过期离线 Bot"""
        now = time.time()

        adapter._bots = {
            "platform1": {
                "bot_online": {
                    "status": "online",
                    "last_active": now,
                    "info": {},
                },
                "bot_recently_offline": {
                    "status": "offline",
                    "last_active": now - 100,
                    "info": {},
                },
                "bot_old_offline": {
                    "status": "offline",
                    "last_active": now - 7200,
                    "info": {},
                },
            },
            "platform2": {
                "bot2_old": {
                    "status": "offline",
                    "last_active": now - 99999,
                    "info": {},
                },
            },
        }

        evicted = adapter._evict_offline_bots(expiry_secs=3600)

        assert evicted == 2
        assert "bot_online" in adapter._bots["platform1"]
        assert "bot_recently_offline" in adapter._bots["platform1"]
        assert "bot_old_offline" not in adapter._bots["platform1"]
        assert "platform2" not in adapter._bots

    def test_evict_zero_disables(self, clean_state):
        """expiry_secs=0 禁用清除"""
        now = time.time()
        adapter._bots = {
            "p1": {
                "b1": {
                    "status": "offline",
                    "last_active": now - 999999,
                    "info": {},
                }
            }
        }
        assert adapter._evict_offline_bots(expiry_secs=0) == 0


# ==================== 限流存储过期清理 ====================


class TestRateLimitCleanupIntegration:
    """路由限流存储过期清理集成测试"""

    def test_cleanup_removes_expired_entries(self):
        """清除过期的限流记录"""
        from ErisPulse.Core.router import RouterManager

        router = RouterManager()
        now = time.monotonic()

        router._rate_limit_store = {
            "route:/api:get:1.2.3.4": [now - 120, now - 110],
            "route:/api:get:5.6.7.8": [now - 10],
        }

        removed = router._cleanup_expired_rate_limits()

        assert removed == 1
        assert "route:/api:get:5.6.7.8" in router._rate_limit_store
        assert "route:/api:get:1.2.3.4" not in router._rate_limit_store

    def test_cleanup_empty_store(self):
        """空存储清理返回 0"""
        from ErisPulse.Core.router import RouterManager

        router = RouterManager()
        router._rate_limit_store.clear()
        assert router._cleanup_expired_rate_limits() == 0


# ==================== 主动 GC 后台任务 ====================


class TestProactiveGCIntegration:
    """主动 GC 后台任务集成测试"""

    @pytest.mark.asyncio
    async def test_start_and_stop_gc_task(self):
        """GC 任务可启动和停止"""
        from ErisPulse.sdk import SDK

        sdk = SDK()

        sdk._start_proactive_gc()
        assert sdk._gc_task is not None
        assert not sdk._gc_task.done()

        sdk._stop_proactive_gc()
        assert sdk._gc_task is None

    def test_stop_gc_is_idempotent(self):
        """多次停止 GC 安全（即使从未启动）"""
        from ErisPulse.sdk import SDK

        sdk = SDK()
        sdk._stop_proactive_gc()
        sdk._stop_proactive_gc()
        assert sdk._gc_task is None

    @pytest.mark.asyncio
    async def test_gc_task_handles_cancel_gracefully(self):
        """GC 任务被取消时正常退出"""
        from ErisPulse.sdk import SDK

        sdk = SDK()

        with patch("ErisPulse.sdk.DEFAULT_PROACTIVE_GC_INTERVAL_SECS", 0.01):
            sdk._start_proactive_gc()
            await asyncio.sleep(0.05)

            sdk._stop_proactive_gc()
            assert sdk._gc_task is None

    @pytest.mark.asyncio
    async def test_gc_task_evicts_offline_bots(self):
        """GC 周期触发时清除离线 Bot"""
        now = time.time()
        adapter._bots = {
            "gc_test": {
                "old_bot": {
                    "status": "offline",
                    "last_active": now - 999999,
                    "info": {},
                }
            }
        }

        evicted = adapter._evict_offline_bots(expiry_secs=1)
        assert evicted == 1
        assert "gc_test" not in adapter._bots

        adapter._bots.clear()

    # ==================== 主动 GC 自适应策略 ====================

    def _make_gc_framework_config(self, **overrides) -> dict:
        """构造最小 framework 配置，供 _read_gc_config 读取"""
        cfg = {
            "proactive_gc_interval": 0.01,
            "proactive_gc_generation": 0,
            "proactive_gc_full_every": 0,
            "proactive_gc_memory_growth_mb": 32,
            "proactive_gc_idle_only": False,
            "proactive_gc_gen0_min": 500,
        }
        cfg.update(overrides)
        return cfg

    @pytest.mark.asyncio
    async def test_gc_loop_skips_collection_when_gen0_low(self):
        """gen0 垃圾量低于阈值时跳过 Python GC"""
        from ErisPulse.sdk import SDK

        sdk = SDK()
        fw = self._make_gc_framework_config()
        with patch("ErisPulse.runtime.get_framework_config", return_value=fw), patch(
            "gc.get_count", return_value=(0, 0, 0)
        ) as mock_count, patch("gc.collect", return_value=0) as mock_collect:
            sdk._start_proactive_gc()
            await asyncio.sleep(0.05)
            sdk._stop_proactive_gc()

            # 多次轮询 gen0 均极低，不应触发任何 Python GC 回收
            assert mock_count.call_count > 0
            mock_collect.assert_not_called()

    @pytest.mark.asyncio
    async def test_gc_loop_runs_collection_when_gen0_high(self):
        """gen0 垃圾量达到阈值时执行常规回收"""
        from ErisPulse.sdk import SDK

        sdk = SDK()
        fw = self._make_gc_framework_config(proactive_gc_gen0_min=500)
        with patch("ErisPulse.runtime.get_framework_config", return_value=fw), patch(
            "gc.get_count", return_value=(1000, 0, 0)
        ), patch("gc.collect", return_value=5) as mock_collect:
            sdk._start_proactive_gc()
            await asyncio.sleep(0.05)
            sdk._stop_proactive_gc()

            assert mock_collect.call_count > 0

    @pytest.mark.asyncio
    async def test_gc_loop_full_collection_skipped_when_memory_stable(self):
        """周期性全量回收受内存增长门限约束：内存稳定时跳过"""
        from ErisPulse.sdk import SDK

        sdk = SDK()
        fw = self._make_gc_framework_config(
            proactive_gc_full_every=1, proactive_gc_memory_growth_mb=32
        )
        traced_values = iter([100.0] * 20)
        with patch("ErisPulse.runtime.get_framework_config", return_value=fw), patch(
            "gc.get_count", return_value=(1000, 1000, 1000)
        ), patch("ErisPulse.runtime.memory.get_traced_mb", side_effect=lambda: next(traced_values)), patch(
            "ErisPulse.runtime.memory.get_rss_mb", return_value=None
        ), patch("gc.collect", return_value=0) as mock_collect:
            sdk._start_proactive_gc()
            await asyncio.sleep(0.06)
            sdk._stop_proactive_gc()

            # 仅首次全量建立基线时回收一次，后续均因内存无增长而跳过
            assert mock_collect.call_count == 1

    @pytest.mark.asyncio
    async def test_gc_loop_full_collection_runs_when_memory_grew(self):
        """周期性全量回收：内存增长达到门限时执行"""
        from ErisPulse.sdk import SDK

        sdk = SDK()
        fw = self._make_gc_framework_config(
            proactive_gc_full_every=1, proactive_gc_memory_growth_mb=32
        )
        traced_values = iter([100.0, 200.0] + [200.0] * 20)
        with patch("ErisPulse.runtime.get_framework_config", return_value=fw), patch(
            "gc.get_count", return_value=(1000, 1000, 1000)
        ), patch("ErisPulse.runtime.memory.get_traced_mb", side_effect=lambda: next(traced_values)), patch(
            "ErisPulse.runtime.memory.get_rss_mb", return_value=None
        ), patch("gc.collect", return_value=0) as mock_collect:
            sdk._start_proactive_gc()
            await asyncio.sleep(0.06)
            sdk._stop_proactive_gc()

            # 首轮建立基线 + 后续内存增长触发，回收至少两次
            assert mock_collect.call_count >= 2

    @pytest.mark.asyncio
    async def test_gc_loop_skips_python_gc_when_busy(self):
        """idle_only 开启且存在 pending handler 时跳过 Python GC"""
        from ErisPulse.sdk import SDK

        sdk = SDK()
        fw = self._make_gc_framework_config(proactive_gc_idle_only=True)
        try:
            with patch("ErisPulse.runtime.get_framework_config", return_value=fw), patch(
                "gc.get_count", return_value=(1000, 1000, 1000)
            ), patch("gc.collect", return_value=0) as mock_collect:
                # 模拟事件洪峰：存在未完成的 handler task
                adapter._pending_handler_tasks.add(object())
                sdk._start_proactive_gc()
                await asyncio.sleep(0.05)
                sdk._stop_proactive_gc()

                mock_collect.assert_not_called()
        finally:
            adapter._pending_handler_tasks.clear()


# ==================== 端到端：事件洪流 + shutdown 安全清理 ====================


class TestEndToEndResourceLifecycle:
    """端到端资源生命周期集成测试"""

    @pytest.mark.asyncio
    async def test_burst_then_shutdown_no_leak(self, clean_state):
        """事件洪流后 shutdown 不泄漏 Task"""
        processed = []

        @adapter.on("message")
        async def handler(data):
            await asyncio.sleep(0.01)
            processed.append(data["id"])

        for i in range(50):
            await adapter.emit(_make_msg(f"msg_{i}"))

        await asyncio.sleep(0.05)

        await adapter._drain_pending_handler_tasks(timeout=3.0)

        assert len(adapter._pending_handler_tasks) == 0

    @pytest.mark.asyncio
    async def test_repeated_emit_drain_cycles(self, clean_state):
        """重复 emit → drain 循环不累积 Task"""

        @adapter.on("message")
        async def handler(data):
            await asyncio.sleep(0.02)

        for cycle in range(5):
            for i in range(10):
                await adapter.emit(_make_msg(f"c{cycle}_m{i}"))

            await asyncio.sleep(0.03)
            await adapter._drain_pending_handler_tasks(timeout=2.0)

            assert len(adapter._pending_handler_tasks) == 0

    @pytest.mark.asyncio
    async def test_full_cleanup_after_module_simulation(self, clean_state):
        """模拟模块完整生命周期：注册钩子 → 加载 → 卸载 → 资源全清"""
        token = current_owner.set("DisposableModule")
        try:
            module_handlers_called = []

            @lifecycle.on("custom.work")
            async def on_work(data):
                module_handlers_called.append(data)

            @adapter.on("message")
            async def on_message(data):
                module_handlers_called.append("msg:" + str(data.get("alt_message", "")))
        finally:
            current_owner.reset(token)

        await lifecycle.emit("custom.work", {"phase": "active"})
        await adapter.emit(_make_msg("hello"))
        await asyncio.sleep(0.1)

        assert len(module_handlers_called) >= 2

        lc_removed = lifecycle.unregister_by_owner("DisposableModule")
        assert lc_removed >= 1

        message.handler.unregister_by_owner("DisposableModule")

        pre_count = len(module_handlers_called)
        await lifecycle.emit("custom.work", {"phase": "after_unload"})
        await asyncio.sleep(0.05)
        assert len(module_handlers_called) == pre_count

    @pytest.mark.asyncio
    async def test_handler_semaphore_reset_on_clear(self, clean_state):
        """AdapterManager.clear() 重置信号量"""
        adapter._get_handler_semaphore()
        assert adapter._handler_semaphore is not None

        adapter.clear()

        assert adapter._handler_semaphore is None
        assert adapter._handler_max_concurrency == 0
        assert len(adapter._pending_handler_tasks) == 0
