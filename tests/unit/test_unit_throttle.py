"""
处理器节流（throttle=）单元测试

EPRFC-2026-001 方向八（2.9 提前交付）。测试节流条件包装器：间隔内丢弃、
间隔过期放行、user/session/global 三粒度隔离、声明校验、与 detail_type /
pattern 条件共存，以及 on_message / on_private_message / on_group_message /
on_at_message 四个装饰器的接入。
"""

import asyncio
import importlib
from unittest.mock import patch

import pytest

from ErisPulse.Core.Event.message import message as message_handler

config_module = importlib.import_module("ErisPulse.Core.config")


@pytest.fixture(autouse=True)
def clean_state():
    from ErisPulse.Core.adapter import adapter
    from ErisPulse.Core.Event import _clear_all_handlers

    _clear_all_handlers()
    message_handler.handler.handlers.clear()
    message_handler.handler._handler_map.clear()
    adapter._onebot_handlers.clear()
    adapter._raw_handlers.clear()
    adapter._onebot_middlewares.clear()
    adapter._bots.clear()
    yield
    _clear_all_handlers()
    message_handler.handler.handlers.clear()
    message_handler.handler._handler_map.clear()
    adapter._onebot_handlers.clear()
    adapter._raw_handlers.clear()
    adapter._onebot_middlewares.clear()
    adapter._bots.clear()


def _msg(text, user_id="u1", group_id=None, mention_bot=False):
    data = {
        "id": f"id_{abs(hash((text, user_id, group_id, mention_bot)))}",
        "time": 1712345678,
        "type": "message",
        "detail_type": "group" if group_id else "private",
        "platform": "onebot11",
        "self": {"platform": "onebot11", "user_id": "bot_x"},
        "user_id": user_id,
        "message": [{"type": "text", "data": {"text": text}}],
        "alt_message": text,
    }
    if group_id:
        data["group_id"] = group_id
    if mention_bot:
        data["message"] = [
            {"type": "mention", "data": {"user_id": "bot_x"}},
            {"type": "text", "data": {"text": text}},
        ]
    return data


async def _dispatch(event):
    from ErisPulse.Core.adapter import adapter

    with patch.object(config_module.config, "getConfig", return_value="/"):
        await adapter.emit(event)
        await asyncio.sleep(0.05)


class TestThrottleDeclaration:
    def test_invalid_duration_rejected(self):
        with pytest.raises(ValueError):

            @message_handler.on_message(throttle="abc")
            async def h(event):
                pass

    def test_invalid_key_rejected(self):
        with pytest.raises(ValueError):

            @message_handler.on_message(throttle="1s", throttle_key="room")
            async def h2(event):
                pass


class TestThrottleBehavior:
    async def test_events_within_interval_dropped(self):
        calls = []

        @message_handler.on_message(throttle="1h")
        async def h(event):
            calls.append(1)

        await _dispatch(_msg("a"))
        await _dispatch(_msg("b"))  # 间隔内：丢弃
        assert calls == [1]

    async def test_interval_expiry_restores(self):
        calls = []

        @message_handler.on_message(throttle="0.3s")
        async def h(event):
            calls.append(1)

        await _dispatch(_msg("a"))
        await _dispatch(_msg("b"))
        assert calls == [1]
        await asyncio.sleep(0.35)
        await _dispatch(_msg("c"))
        assert calls == [1, 1]

    async def test_user_key_isolation(self):
        calls = []

        @message_handler.on_message(throttle="1h", throttle_key="user")
        async def h(event):
            calls.append(event.get("user_id"))

        await _dispatch(_msg("a", user_id="u1"))
        await _dispatch(_msg("b", user_id="u1"))  # 同用户：丢弃
        await _dispatch(_msg("c", user_id="u2"))  # 不同用户：放行
        assert calls == ["u1", "u2"]

    async def test_session_key_isolation(self):
        calls = []

        @message_handler.on_private_message(throttle="1h", throttle_key="session")
        async def h(event):
            calls.append(event.get("user_id"))

        await _dispatch(_msg("a", user_id="u1"))          # 私聊会话 u1
        await _dispatch(_msg("b", user_id="u2", group_id="g1"))  # 群会话（不匹配 private）
        await _dispatch(_msg("c", user_id="u3"))          # 另一私聊会话：放行
        assert calls == ["u1", "u3"]

    async def test_global_key_shared(self):
        calls = []

        @message_handler.on_message(throttle="1h", throttle_key="global")
        async def h(event):
            calls.append(1)

        await _dispatch(_msg("a", user_id="u1"))
        await _dispatch(_msg("b", user_id="u2", group_id="g9"))
        assert calls == [1]

    async def test_coexists_with_detail_type_and_pattern(self):
        """与既有条件组合：私聊 + pattern 匹配 + 节流共同生效"""
        calls = []

        @message_handler.on_private_message(pattern="cmd*", throttle="1h")
        async def h(event):
            calls.append(event.get("alt_message"))

        await _dispatch(_msg("cmd run"))    # 匹配 + 首次：放行
        await _dispatch(_msg("cmd again"))  # 匹配但节流：丢弃
        await _dispatch(_msg("other"))      # pattern 不匹配
        assert calls == ["cmd run"]

    async def test_group_and_at_decorators(self):
        group_calls, at_calls = [], []

        @message_handler.on_group_message(throttle="1h")
        async def g(event):
            group_calls.append(1)

        @message_handler.on_at_message(throttle="1h")
        async def a(event):
            at_calls.append(1)

        await _dispatch(_msg("hi", group_id="g1", mention_bot=True))
        await _dispatch(_msg("hi", group_id="g1", mention_bot=True))  # 双双节流
        assert group_calls == [1]
        assert at_calls == [1]

    async def test_unregister_stops_throttling(self):
        """注销后处理器不再触发（节流状态随闭包回收）"""
        calls = []

        @message_handler.on_message(throttle="1h")
        async def h(event):
            calls.append(1)

        await _dispatch(_msg("a"))
        message_handler.unregister(h)
        await _dispatch(_msg("b"))
        assert calls == [1]


class TestDebounce:
    """debounce= 防抖：窗口内同键事件只执行最后一条"""

    async def test_only_last_event_executes(self):
        calls = []

        @message_handler.on_message(debounce="0.5s")
        async def h(event):
            calls.append(event.get_alt_message())

        await _dispatch(_msg("first"))
        await _dispatch(_msg("second"))
        await _dispatch(_msg("third"))
        assert calls == []  # 窗口内：全部挂起，未执行
        await asyncio.sleep(0.7)
        assert calls == ["third"]  # 窗口耗尽：只执行最后一条

    async def test_window_expiry_executes_each(self):
        calls = []

        @message_handler.on_message(debounce="0.3s")
        async def h(event):
            calls.append(event.get_alt_message())

        await _dispatch(_msg("a"))
        await asyncio.sleep(0.45)
        await _dispatch(_msg("b"))
        await asyncio.sleep(0.45)
        assert calls == ["a", "b"]  # 无后续事件：各自到期执行

    async def test_user_key_isolation(self):
        calls = []

        @message_handler.on_message(debounce="0.5s", debounce_key="user")
        async def h(event):
            calls.append(event.get_user_id())

        await _dispatch(_msg("a", user_id="u1"))
        await _dispatch(_msg("b", user_id="u2"))  # 不同用户独立窗口
        await asyncio.sleep(0.7)
        assert sorted(calls) == ["u1", "u2"]

    async def test_debounce_throttle_mutually_exclusive(self):
        with pytest.raises(ValueError):

            @message_handler.on_message(throttle="1s", debounce="1s")
            async def h(event):
                pass

    async def test_invalid_duration_rejected(self):
        with pytest.raises(ValueError):

            @message_handler.on_message(debounce="abc")
            async def h2(event):
                pass

    async def test_invalid_key_rejected(self):
        with pytest.raises(ValueError):

            @message_handler.on_message(debounce="1s", debounce_key="room")
            async def h3(event):
                pass
