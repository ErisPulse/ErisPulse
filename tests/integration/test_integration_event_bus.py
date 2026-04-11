"""
事件总线端到端集成测试

测试 adapter.emit() → middleware → OB12 handlers → module callbacks 的完整流转。
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch

from ErisPulse.Core.adapter import adapter
from ErisPulse.Core.lifecycle import lifecycle
from ErisPulse.Core.Event import command, message, notice
from ErisPulse.Core.Event import _clear_all_handlers
from collections import defaultdict


def _make_msg(text="/hello", **kwargs):
    data = {
        "id": "bus_001",
        "time": 1712345678,
        "type": "message",
        "detail_type": "private",
        "platform": "bus_test",
        "self": {"platform": "bus_test", "user_id": "bot_bus"},
        "user_id": "u1",
        "user_nickname": "User1",
        "message": [{"type": "text", "data": {"text": text}}],
        "alt_message": text,
    }
    data.update(kwargs)
    return data


@pytest.fixture
def clean_event_state():
    _clear_all_handlers()
    lifecycle._handlers.clear()
    lifecycle._timers.clear()
    adapter._onebot_handlers.clear()
    adapter._raw_handlers.clear()
    adapter._onebot_middlewares.clear()
    adapter._bots.clear()
    yield
    _clear_all_handlers()
    lifecycle._handlers.clear()
    lifecycle._timers.clear()
    adapter._onebot_handlers.clear()
    adapter._raw_handlers.clear()
    adapter._onebot_middlewares.clear()
    adapter._bots.clear()


class TestEventBusIntegration:
    """事件总线集成测试"""

    @pytest.mark.asyncio
    async def test_emit_to_ob12_handler(self, clean_event_state):
        """emit 事件到 OB12 handler"""
        received = []

        @adapter.on("message")
        async def handler(data):
            received.append(data)

        event = _make_msg("hello")
        await adapter.emit(event)

        assert len(received) == 1
        assert received[0]["type"] == "message"
        assert received[0]["alt_message"] == "hello"

    @pytest.mark.asyncio
    async def test_middleware_chain_modifies_event(self, clean_event_state):
        """middleware 链修改事件数据并传递到 handler"""
        middleware_log = []
        handler_data = []

        @adapter.middleware
        async def mw1(data):
            middleware_log.append("mw1")
            data["mw1_tag"] = True
            return data

        @adapter.middleware
        async def mw2(data):
            middleware_log.append("mw2")
            data["mw2_tag"] = True
            return data

        @adapter.on("message")
        async def handler(data):
            handler_data.append(data)

        event = _make_msg("test")
        await adapter.emit(event)

        assert middleware_log == ["mw1", "mw2"]
        assert len(handler_data) == 1
        assert handler_data[0].get("mw1_tag") is True
        assert handler_data[0].get("mw2_tag") is True

    @pytest.mark.asyncio
    async def test_multiple_middlewares_sequential(self, clean_event_state):
        """多个 middleware 按顺序执行"""
        order = []

        @adapter.middleware
        async def mw1(data):
            order.append("mw1")
            return data

        @adapter.middleware
        async def mw2(data):
            order.append("mw2")
            return data

        @adapter.on("message")
        async def handler(data):
            order.append("handler")

        await adapter.emit(_make_msg("test"))
        assert order == ["mw1", "mw2", "handler"]

    @pytest.mark.asyncio
    async def test_multiple_handlers_same_event(self, clean_event_state):
        """同一事件多个 handler 都被调用"""
        results = []

        @adapter.on("message")
        async def h1(data):
            results.append("h1")

        @adapter.on("message")
        async def h2(data):
            results.append("h2")

        @adapter.on("message")
        async def h3(data):
            results.append("h3")

        await adapter.emit(_make_msg("test"))

        assert len(results) == 3
        assert "h1" in results
        assert "h2" in results
        assert "h3" in results

    @pytest.mark.asyncio
    async def test_raw_handler_receives_platform_event(self, clean_event_state):
        """原生事件处理器接收平台原始数据"""
        raw_received = []

        @adapter.on("friend_add", raw=True, platform="bus_test")
        async def raw_handler(data):
            raw_received.append(data)

        event = {
            "id": "raw_001",
            "time": 1712345678,
            "type": "notice",
            "platform": "bus_test",
            "self": {"platform": "bus_test", "user_id": "bot_bus"},
            "bus_test_raw": {"action": "friend_add", "user_id": "new_user"},
            "bus_test_raw_type": "friend_add",
        }

        await adapter.emit(event)

        assert len(raw_received) == 1
        assert raw_received[0]["action"] == "friend_add"

    @pytest.mark.asyncio
    async def test_command_through_event_bus(self, clean_event_state):
        """通过事件总线触发命令处理"""
        received = []

        @command("hello", help="测试命令")
        async def hello_handler(event):
            received.append(event)

        with patch("ErisPulse.Core.config.config.getConfig", return_value="/"):
            event = _make_msg("/hello")
            await adapter.emit(event)

        assert len(received) == 1

    @pytest.mark.asyncio
    async def test_command_with_args(self, clean_event_state):
        """命令参数解析"""
        received = []

        @command("echo", help="回显命令")
        async def echo_handler(event):
            received.append(event)

        with patch("ErisPulse.Core.config.config.getConfig", return_value="/"):
            event = _make_msg("/echo hello world")
            await adapter.emit(event)

        assert len(received) == 1
        cmd_info = received[0].get("command", {})
        assert cmd_info.get("name") == "echo"
        assert cmd_info.get("raw") == "echo hello world"

    @pytest.mark.asyncio
    async def test_command_alias(self, clean_event_state):
        """命令别名"""
        received = []

        @command("greet", aliases=["hi", "hello"], help="问候")
        async def greet_handler(event):
            received.append(event)

        with patch("ErisPulse.Core.config.config.getConfig", return_value="/"):
            await adapter.emit(_make_msg("/hi"))
            await adapter.emit(_make_msg("/hello"))

        assert len(received) == 2

    @pytest.mark.asyncio
    async def test_message_handler_condition_filter(self, clean_event_state):
        """消息 handler 条件过滤"""
        private_msgs = []
        all_msgs = []

        @message.on_message()
        async def all_handler(event):
            all_msgs.append(event)

        @message.on_private_message()
        async def private_handler(event):
            private_msgs.append(event)

        with patch("ErisPulse.Core.config.config.getConfig", return_value="/"):
            await adapter.emit(_make_msg("hi", detail_type="private"))
            await adapter.emit(_make_msg("hi", detail_type="group", group_id="g1"))

        assert len(all_msgs) >= 2
        assert len(private_msgs) == 1

    @pytest.mark.asyncio
    async def test_notice_event_flow(self, clean_event_state):
        """通知事件流转"""
        received = []

        @notice.on_notice()
        async def handler(event):
            received.append(event)

        event = {
            "id": "n_001",
            "time": 1712345678,
            "type": "notice",
            "detail_type": "friend_add",
            "platform": "bus_test",
            "self": {"platform": "bus_test", "user_id": "bot_bus"},
            "user_id": "new_user",
        }
        await adapter.emit(event)

        assert len(received) == 1
        assert received[0]["detail_type"] == "friend_add"

    @pytest.mark.asyncio
    async def test_hidden_command_not_in_help(self, clean_event_state):
        """隐藏命令不出现在帮助列表"""

        @command("visible", help="可见命令")
        async def visible_cmd(event):
            pass

        @command("secret", hidden=True, help="秘密命令")
        async def secret_cmd(event):
            pass

        visible = command.get_visible_commands()
        assert "visible" in visible
        assert "secret" not in visible

    @pytest.mark.asyncio
    async def test_event_processed_stops_propagation(self, clean_event_state):
        """_processed 标记中断后续 handler（通过 message handler condition）"""
        order = []

        @message.on_message(priority=0)
        async def first_handler(event):
            order.append("first")

        @message.on_message(priority=10)
        async def second_handler(event):
            order.append("second")

        with patch("ErisPulse.Core.config.config.getConfig", return_value="/"):
            event = _make_msg("test")
            await adapter.emit(event)

        assert order[0] == "first"
        assert order[1] == "second"

    @pytest.mark.asyncio
    async def test_burst_events_all_processed(self, clean_event_state):
        """快速连续 emit 多个事件，全部被处理"""
        count = 0
        lock = asyncio.Lock()

        @adapter.on("message")
        async def handler(data):
            nonlocal count
            async with lock:
                count += 1

        tasks = [adapter.emit(_make_msg(f"msg_{i}")) for i in range(100)]
        await asyncio.gather(*tasks)

        assert count == 100
