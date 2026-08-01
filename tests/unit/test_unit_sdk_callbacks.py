"""
SDK 回调钩子单元测试

测试 sdk.init(before_init=, after_init=) 和 sdk.run(on_ready=) 的回调机制
"""

import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from ErisPulse import sdk


class TestInitCallbacks:
    """测试 sdk.init() 的 before_init / after_init 回调"""

    @pytest.fixture(autouse=True)
    def _reset_sdk(self):
        """每个测试前后重置 SDK 状态"""
        old_initialized = sdk._initialized
        sdk._initialized = False
        yield
        sdk._initialized = old_initialized

    @pytest.mark.asyncio
    async def test_before_init_sync_called(self):
        """同步 before_init 回调被调用"""
        called = []

        def before():
            called.append("before")

        with patch.object(sdk, "_prepare_environment", new=AsyncMock(return_value=True)):
            with patch.object(sdk, "Initializer") as MockInit:
                MockInit.return_value.init = AsyncMock(return_value=True)
                await sdk.init(before_init=before)

        assert called == ["before"]

    @pytest.mark.asyncio
    async def test_before_init_async_called(self):
        """异步 before_init 回调被 await"""
        called = []

        async def before():
            called.append("before")
            await asyncio.sleep(0)

        with patch.object(sdk, "_prepare_environment", new=AsyncMock(return_value=True)):
            with patch.object(sdk, "Initializer") as MockInit:
                MockInit.return_value.init = AsyncMock(return_value=True)
                await sdk.init(before_init=before)

        assert called == ["before"]

    @pytest.mark.asyncio
    async def test_after_init_called_on_success(self):
        """init 成功后 after_init 被调用"""
        called = []

        async def after():
            called.append("after")

        with patch.object(sdk, "_prepare_environment", new=AsyncMock(return_value=True)):
            with patch.object(sdk, "Initializer") as MockInit:
                MockInit.return_value.init = AsyncMock(return_value=True)
                await sdk.init(after_init=after)

        assert called == ["after"]

    @pytest.mark.asyncio
    async def test_after_init_not_called_on_failure(self):
        """init 失败时 after_init 不被调用"""
        called = []

        async def after():
            called.append("after")

        with patch.object(sdk, "_prepare_environment", new=AsyncMock(return_value=False)):
            await sdk.init(after_init=after)

        assert called == []

    @pytest.mark.asyncio
    async def test_callback_order(self):
        """回调顺序：before_init → 初始化 → after_init"""
        order = []

        def before():
            order.append("before_init")

        async def after():
            order.append("after_init")

        def mock_init_inner():
            order.append("init")
            return True

        with patch.object(sdk, "_prepare_environment", new=AsyncMock(return_value=True)):
            with patch.object(sdk, "Initializer") as MockInit:
                MockInit.return_value.init = AsyncMock(side_effect=mock_init_inner)
                await sdk.init(before_init=before, after_init=after)

        assert order == ["before_init", "init", "after_init"]

    @pytest.mark.asyncio
    async def test_before_init_error_does_not_crash(self):
        """before_init 抛异常不会中断 init"""
        def before():
            raise ValueError("boom")

        with patch.object(sdk, "_prepare_environment", new=AsyncMock(return_value=True)):
            with patch.object(sdk, "Initializer") as MockInit:
                MockInit.return_value.init = AsyncMock(return_value=True)
                result = await sdk.init(before_init=before)

        assert result is True

    @pytest.mark.asyncio
    async def test_after_init_error_does_not_crash(self):
        """after_init 抛异常不会影响 init 返回值"""
        async def after():
            raise ValueError("boom")

        with patch.object(sdk, "_prepare_environment", new=AsyncMock(return_value=True)):
            with patch.object(sdk, "Initializer") as MockInit:
                MockInit.return_value.init = AsyncMock(return_value=True)
                result = await sdk.init(after_init=after)

        assert result is True


class TestRunOnReady:
    """测试 sdk.run(on_ready=) 回调"""

    @pytest.fixture(autouse=True)
    def _reset_sdk(self):
        """每个测试前后重置 SDK 状态"""
        old_initialized = sdk._initialized
        sdk._initialized = False
        yield
        sdk._initialized = old_initialized

    @pytest.mark.asyncio
    async def test_on_ready_called_after_init(self):
        """on_ready 在 init 成功后被调用"""
        called = []

        async def ready():
            called.append("ready")

        with patch.object(sdk, "_prepare_environment", new=AsyncMock(return_value=True)):
            with patch.object(sdk, "Initializer") as MockInit:
                MockInit.return_value.init = AsyncMock(return_value=True)
                # keep_running=False 避免挂起
                await sdk.run(keep_running=False, on_ready=ready)

        assert called == ["ready"]

    @pytest.mark.asyncio
    async def test_on_ready_not_called_on_init_failure(self):
        """init 失败时 on_ready 不被调用"""
        called = []

        async def ready():
            called.append("ready")

        with patch.object(sdk, "_prepare_environment", new=AsyncMock(return_value=False)):
            await sdk.run(keep_running=False, on_ready=ready)

        assert called == []

    @pytest.mark.asyncio
    async def test_on_ready_sync(self):
        """同步 on_ready 回调"""
        called = []

        def ready():
            called.append("sync_ready")

        with patch.object(sdk, "_prepare_environment", new=AsyncMock(return_value=True)):
            with patch.object(sdk, "Initializer") as MockInit:
                MockInit.return_value.init = AsyncMock(return_value=True)
                await sdk.run(keep_running=False, on_ready=ready)

        assert called == ["sync_ready"]

    @pytest.mark.asyncio
    async def test_on_ready_error_does_not_crash(self):
        """on_ready 抛异常不会导致 run 崩溃"""
        async def ready():
            raise ValueError("boom")

        with patch.object(sdk, "_prepare_environment", new=AsyncMock(return_value=True)):
            with patch.object(sdk, "Initializer") as MockInit:
                MockInit.return_value.init = AsyncMock(return_value=True)
                # 不应该抛异常
                await sdk.run(keep_running=False, on_ready=ready)

    @pytest.mark.asyncio
    async def test_run_forwards_init_callbacks(self):
        """run() 转发 before_init / after_init 给 init()"""
        order = []

        def before():
            order.append("before")

        async def after():
            order.append("after")

        async def ready():
            order.append("ready")

        with patch.object(sdk, "_prepare_environment", new=AsyncMock(return_value=True)):
            with patch.object(sdk, "Initializer") as MockInit:
                MockInit.return_value.init = AsyncMock(return_value=True)
                await sdk.run(
                    keep_running=False,
                    before_init=before,
                    after_init=after,
                    on_ready=ready,
                )

        assert order == ["before", "after", "ready"]


class TestShutdown:
    """测试 sdk.shutdown() 优雅关闭机制"""

    def test_shutdown_before_run_is_noop(self):
        """run() 之前调用 shutdown() 不应报错（关闭事件尚未创建）"""
        old = sdk._shutdown_event
        try:
            sdk._shutdown_event = None
            sdk.shutdown()  # 无事件 → 静默无操作
        finally:
            sdk._shutdown_event = old

    def test_shutdown_sets_event(self):
        """shutdown() 设置关闭事件，使 run() 的挂起返回"""
        import asyncio as _asyncio

        old = sdk._shutdown_event
        try:
            sdk._shutdown_event = _asyncio.Event()
            assert not sdk._shutdown_event.is_set()
            sdk.shutdown()
            assert sdk._shutdown_event.is_set()
            # 重复调用安全
            sdk.shutdown()
            assert sdk._shutdown_event.is_set()
        finally:
            sdk._shutdown_event = old
