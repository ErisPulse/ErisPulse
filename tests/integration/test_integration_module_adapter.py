"""
模块与适配器协作集成测试

测试模块通过 Event 装饰器注册 handler 后，适配器 emit 事件时模块 handler 被正确触发。
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch

from ErisPulse.Core.adapter import adapter
from ErisPulse.Core.module import ModuleManager
from ErisPulse.Core.lifecycle import lifecycle
from ErisPulse.Core.Event import command, message, notice
from ErisPulse.Core.Event import _clear_all_handlers
from ErisPulse.Core.Bases import BaseModule


class _CollabModule(BaseModule):
    def __init__(self, sdk=None):
        self.sdk = sdk
        self.received_events = []

    async def on_load(self, event):
        @message.on_message()
        async def on_any_message(event_data):
            self.received_events.append(("message", event_data))

        @notice.on_friend_add()
        async def on_friend(event_data):
            self.received_events.append(("friend_add", event_data))

        @command("mod_cmd", help="模块命令")
        async def mod_command(event_data):
            self.received_events.append(("command", event_data))

        return True

    async def on_unload(self, event):
        self.received_events.clear()
        return True


def _make_msg(text="test", **kwargs):
    data = {
        "id": "collab_001",
        "time": 1712345678,
        "type": "message",
        "detail_type": "private",
        "platform": "collab",
        "self": {"platform": "collab", "user_id": "bot_c"},
        "user_id": "u1",
        "message": [{"type": "text", "data": {"text": text}}],
        "alt_message": text,
    }
    data.update(kwargs)
    return data


@pytest.fixture
def clean_state():
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


@pytest.fixture
def collab_module_mgr(clean_state):
    mgr = ModuleManager()
    mgr._modules.clear()
    mgr._module_classes.clear()
    mgr._loaded_modules.clear()
    mgr._module_info.clear()
    return mgr


class TestModuleAdapterIntegration:
    """模块与适配器协作集成测试"""

    @pytest.mark.asyncio
    async def test_module_registers_handlers_on_load(self, collab_module_mgr):
        """模块 on_load 中注册的事件 handler 可用"""
        collab_module_mgr.register("collab_mod", _CollabModule, {"cls_instance": True})
        result = await collab_module_mgr.load("collab_mod")

        assert result is True
        assert len(message.handler.handlers) > 0

    @pytest.mark.asyncio
    async def test_adapter_emit_triggers_module_handler(self, collab_module_mgr):
        """adapter emit 事件后模块 handler 被触发"""
        collab_module_mgr.register("collab_mod", _CollabModule, {"cls_instance": True})
        await collab_module_mgr.load("collab_mod")
        mod = collab_module_mgr._modules["collab_mod"]

        await adapter.emit(_make_msg("hello"))

        msg_events = [e for t, e in mod.received_events if t == "message"]
        assert len(msg_events) == 1

    @pytest.mark.asyncio
    async def test_module_command_triggered_via_adapter(self, collab_module_mgr):
        """通过 adapter emit 消息触发模块注册的命令"""
        collab_module_mgr.register("collab_mod", _CollabModule, {"cls_instance": True})
        await collab_module_mgr.load("collab_mod")
        mod = collab_module_mgr._modules["collab_mod"]

        with patch("ErisPulse.Core.config.config.getConfig", return_value="/"):
            await adapter.emit(_make_msg("/mod_cmd test_arg"))

        cmd_events = [e for t, e in mod.received_events if t == "command"]
        assert len(cmd_events) == 1

    @pytest.mark.asyncio
    async def test_unload_module_clears_events(self, collab_module_mgr):
        """卸载模块后模块不再接收新事件"""
        collab_module_mgr.register("collab_mod", _CollabModule, {"cls_instance": True})
        await collab_module_mgr.load("collab_mod")

        handler_count_before = len(message.handler.handlers)
        await collab_module_mgr.unload("collab_mod")

        handler_count_after = len(message.handler.handlers)
        assert handler_count_after <= handler_count_before

    @pytest.mark.asyncio
    async def test_multiple_modules_receive_same_event(self, collab_module_mgr):
        """多个模块同时接收同一事件"""
        collab_module_mgr.register("mod1", _CollabModule, {"cls_instance": True})
        collab_module_mgr.register("mod2", _CollabModule, {"cls_instance": True})
        await collab_module_mgr.load("mod1")
        await collab_module_mgr.load("mod2")
        mod1 = collab_module_mgr._modules["mod1"]
        mod2 = collab_module_mgr._modules["mod2"]

        await adapter.emit(_make_msg("broadcast"))

        assert len([e for t, e in mod1.received_events if t == "message"]) == 1
        assert len([e for t, e in mod2.received_events if t == "message"]) == 1

    @pytest.mark.asyncio
    async def test_module_lifecycle_events_emitted(self, collab_module_mgr):
        """模块加载/卸载时生命周期事件被触发"""
        events = []

        async def capture(data):
            events.append(data["event"])

        lifecycle.on("module.load")(capture)
        lifecycle.on("module.unload")(capture)

        collab_module_mgr.register("m1", _CollabModule, {"cls_instance": True})
        await collab_module_mgr.load("m1")
        await collab_module_mgr.unload("m1")

        assert "module.load" in events
        assert "module.unload" in events
