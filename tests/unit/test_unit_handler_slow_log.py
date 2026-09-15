"""
慢事件日志归因单元测试

测试处理器慢日志的指向正确性：框架桥接分发层（BaseEventHandler._process_event
挂载到适配器总线的绑定方法）的 Task 级慢告警降级为 TRACE——单个处理器的慢
已由内层 EventHandler 精确告警，桥接层再以框架函数名告警会指向错误位置
（日志显示 [BaseEventHandler._process_event]，用户无法定位）；
处理器慢日志携带定义位置标注（模块:行号），模块作者自定的方法名
（如 Main._handle_message）不再与框架内部函数混淆。
"""

import asyncio
import importlib
import logging
from unittest.mock import patch

import pytest

from ErisPulse.Core.Event.base import BaseEventHandler
from ErisPulse.runtime.diagnostics import deepest_user_frame, handler_source_loc

adapter_module = importlib.import_module("ErisPulse.Core.adapter")
base_module = importlib.import_module("ErisPulse.Core.Event.base")


def _msg(user_id="u1"):
    return {
        "id": f"id_{abs(hash(user_id))}",
        "time": 1712345678,
        "type": "message",
        "detail_type": "private",
        "platform": "test",
        "self": {"platform": "test", "user_id": "bot_x"},
        "user_id": user_id,
        "message": [{"type": "text", "data": {"text": "/slow"}}],
        "alt_message": "/slow",
    }


class TestHandlerSourceLoc:
    """handler_source_loc 位置标注生成"""

    def test_plain_function(self):
        def my_handler(event):
            return event

        loc = handler_source_loc(my_handler)
        assert loc.startswith(" (")
        assert "test_unit_handler_slow_log" in loc
        assert loc.rstrip().endswith(str(my_handler.__code__.co_firstlineno) + ")")

    def test_bound_method(self):
        class Fake:
            def handle(self, event):
                return event

        loc = handler_source_loc(Fake().handle)
        assert loc.startswith(" (")
        assert "test_unit_handler_slow_log" in loc

    def test_lambda(self):
        loc = handler_source_loc(lambda event: event)
        assert loc.startswith(" (")
        assert "test_unit_handler_slow_log" in loc

    def test_builtin_without_source(self):
        assert handler_source_loc(print) == ""


class TestDeepestUserFrame:
    """协程等待链采样：定位业务代码真正的等待点"""

    @pytest.mark.asyncio
    async def test_locates_inner_await_point(self):
        """挂起在 await 链上时返回最深业务帧（跳过框架与标准库帧）"""

        async def fake_ai_call():
            await asyncio.sleep(0.2)

        async def handler(event):
            await fake_ai_call()

        t = asyncio.create_task(handler({}))
        await asyncio.sleep(0.05)

        loc = deepest_user_frame(t)
        assert "fake_ai_call" in loc
        assert "test_unit_handler_slow_log" in loc

        await t

    @pytest.mark.asyncio
    async def test_done_task_returns_empty(self):
        """已结束的 Task → 空串"""

        async def quick():
            pass

        t = asyncio.create_task(quick())
        await t
        assert deepest_user_frame(t) == ""


class TestHandlerStillRunningWatchdog:
    """执行中看门狗：处理器超阈仍未完成时采样等待点"""

    @pytest.fixture
    def clean_bus(self):
        from ErisPulse.Core.adapter import adapter as adapter_manager

        adapter_manager._onebot_handlers.clear()
        adapter_manager._raw_handlers.clear()
        adapter_manager._onebot_middlewares.clear()
        adapter_manager._bots.clear()
        yield
        adapter_manager._onebot_handlers.clear()
        adapter_manager._raw_handlers.clear()
        adapter_manager._onebot_middlewares.clear()
        adapter_manager._bots.clear()

    @pytest.mark.asyncio
    async def test_watchdog_reports_current_await_point(self, clean_bus, caplog):
        """执行超阈 → 告警含入口位置 + 当前业务等待点（模拟等 AI 场景）"""
        from ErisPulse.Core.adapter import adapter as adapter_manager

        async def fake_ai_call():
            await asyncio.sleep(0.15)  # 模拟 AI 接口慢

        async def slow_biz_handler(event):
            await fake_ai_call()

        holder = BaseEventHandler("message")
        holder.register(slow_biz_handler)

        try:
            with patch.object(
                base_module, "HANDLER_SLOW_THRESHOLD_SECS", 0.02
            ), caplog.at_level(logging.WARNING):
                data = {
                    "id": "watchdog_1",
                    "time": 1,
                    "type": "message",
                    "detail_type": "private",
                    "platform": "test",
                    "self": {"platform": "test", "user_id": "bot_x"},
                    "user_id": "u1",
                    "message": [{"type": "text", "data": {"text": "hi"}}],
                    "alt_message": "hi",
                }
                await adapter_manager.emit(data)
                await asyncio.sleep(0.4)
        finally:
            holder.unregister(slow_biz_handler)

        msgs = [r.getMessage() for r in caplog.records if r.levelno >= logging.WARNING]
        # 看门狗（执行中）：入口 + 当前停在业务帧
        assert any("fake_ai_call" in m for m in msgs), f"看门狗应报告当前等待点: {msgs}"
        assert any("slow_biz_handler" in m for m in msgs)
        # 结束统计：总耗时
        assert any("took" in m and "slow_biz_handler" in m for m in msgs)

    @pytest.mark.asyncio
    async def test_watchdog_silent_when_handler_fast(self, clean_bus, caplog):
        """处理器在阈值内完成 → 不触发执行中告警"""
        from ErisPulse.Core.adapter import adapter as adapter_manager

        async def fast_handler(event):
            await asyncio.sleep(0.005)

        holder = BaseEventHandler("message")
        holder.register(fast_handler)

        try:
            with patch.object(
                base_module, "HANDLER_SLOW_THRESHOLD_SECS", 0.02
            ), caplog.at_level(logging.WARNING):
                data = {
                    "id": "watchdog_2",
                    "time": 1,
                    "type": "message",
                    "detail_type": "private",
                    "platform": "test",
                    "self": {"platform": "test", "user_id": "bot_x"},
                    "user_id": "u1",
                    "message": [{"type": "text", "data": {"text": "hi"}}],
                    "alt_message": "hi",
                }
                await adapter_manager.emit(data)
                await asyncio.sleep(0.1)
        finally:
            holder.unregister(fast_handler)

        msgs = [r.getMessage() for r in caplog.records if r.levelno >= logging.WARNING]
        # 执行中告警的判定特征：阈值数值出现在含 handler 名的同一条 WARNING 中
        # （结束统计不含 threshold 数值）
        assert not any(
            "fast_handler" in m and "0.02" in m for m in msgs
        ), f"快速处理器不应触发执行中告警: {msgs}"


class TestBridgeSlowLogDowngraded:
    """桥接分发层（_process_event 绑定方法）慢告警降级；直连处理器保持 WARNING"""

    @pytest.fixture
    def manager(self):
        manager = adapter_module.AdapterManager()
        manager._onebot_handlers.clear()
        manager._raw_handlers.clear()
        manager._onebot_middlewares.clear()
        return manager

    @staticmethod
    async def _run_slow_task(manager, func):
        with patch.object(adapter_module, "HANDLER_SLOW_THRESHOLD_SECS", 0.01):
            task = manager._dispatch_handler_task(func, _msg(), event_type="message", platform="test")
            if task is not None:
                await task
            await asyncio.sleep(0.05)

    @pytest.mark.asyncio
    async def test_bridge_slow_not_warned_with_framework_name(self, manager):
        """桥接分发慢 → 不再以 BaseEventHandler._process_event 名义发 WARNING，降级 TRACE"""
        bridge = BaseEventHandler("message")
        # 手动注入慢业务处理器（不调 register，避免挂到全局适配器总线）
        async def slow_inner(event):
            await asyncio.sleep(0.08)

        bridge.handlers.append({"func": slow_inner, "priority": 0, "condition": None, "owner": None, "scope_exempt": True})

        with patch.object(adapter_module, "logger") as log_mock:
            await self._run_slow_task(manager, bridge._process_event)

        for call in log_mock.warning.call_args_list:
            assert "BaseEventHandler._process_event" not in str(call)
        assert log_mock.trace.called, "桥接慢告警应降级为 TRACE 输出"
        assert any("0.01" in str(c) for c in log_mock.trace.call_args_list)

    @pytest.mark.asyncio
    async def test_direct_handler_slow_keeps_warning_with_loc(self, manager):
        """直接注册的处理器慢 → 仍为 WARNING，且处理器名带定义位置标注"""
        async def slow_direct_handler(event):
            await asyncio.sleep(0.08)

        with patch.object(adapter_module, "logger") as log_mock:
            await self._run_slow_task(manager, slow_direct_handler)

        warnings = [str(c) for c in log_mock.warning.call_args_list]
        assert any(
            "slow_direct_handler" in m and "test_unit_handler_slow_log" in m for m in warnings
        ), f"WARNING 应含处理器名与定义位置标注: {warnings}"


class TestFullChainSlowLogAttribution:
    """全链路：BaseEventHandler 挂载到适配器总线后的慢日志归因"""

    @pytest.fixture(autouse=True)
    def clean_bus(self):
        from ErisPulse.Core.adapter import adapter as adapter_manager

        adapter_manager._onebot_handlers.clear()
        adapter_manager._raw_handlers.clear()
        adapter_manager._onebot_middlewares.clear()
        adapter_manager._bots.clear()
        yield
        adapter_manager._onebot_handlers.clear()
        adapter_manager._raw_handlers.clear()
        adapter_manager._onebot_middlewares.clear()
        adapter_manager._bots.clear()

    @pytest.mark.asyncio
    async def test_warning_points_to_business_handler_not_bridge(self, caplog):
        """真实链路：WARNING 指向业务处理器（带位置），桥接层不出现框架函数名"""
        from ErisPulse.Core.adapter import adapter as adapter_manager

        seen = []
        handler_holder = BaseEventHandler("message")

        async def slow_biz_handler(event):
            await asyncio.sleep(0.08)
            seen.append(event.get("user_id"))

        handler_holder.register(slow_biz_handler)

        try:
            with patch.object(adapter_module, "HANDLER_SLOW_THRESHOLD_SECS", 0.01), patch.object(
                importlib.import_module("ErisPulse.Core.Event.base"), "HANDLER_SLOW_THRESHOLD_SECS", 0.01
            ), caplog.at_level(5):
                await adapter_manager.emit(_msg())
                await asyncio.sleep(0.3)
        finally:
            handler_holder.unregister(slow_biz_handler)

        assert seen == ["u1"]
        warnings = [r.getMessage() for r in caplog.records if r.levelno >= logging.WARNING]
        # 精确告警：指向业务处理器（带定义位置标注）
        assert any("slow_biz_handler" in m and "test_unit_handler_slow_log" in m for m in warnings)
        # 框架桥接函数名不再出现在 WARNING 中
        assert all("BaseEventHandler._process_event" not in m for m in warnings)
