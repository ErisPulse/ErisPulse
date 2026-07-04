"""
Event 包装类增强测试

测试我们新增的 Event 方法：
- get_target_id / get_session_id
- supports / available_methods
- reply(at_sender=True, quote=True)
- register_event_method("*") 通配符
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from ErisPulse.Core.Event.wrapper import (
    Event,
    register_event_method,
    unregister_event_method,
)


def make_event(**kwargs):
    defaults = {
        "id": "evt_001",
        "time": 1700000000,
        "type": "message",
        "detail_type": "private",
        "platform": "test",
        "self": {"platform": "test", "user_id": "bot"},
        "message_id": "msg_001",
        "message": [{"type": "text", "data": {"text": "hello"}}],
        "alt_message": "hello",
        "user_id": "user_123",
    }
    defaults.update(kwargs)
    return Event(defaults)


def sec(title):
    print(f"\n{'=' * 50}")
    print(f"  {title}")
    print(f"{'=' * 50}")


def ok(msg=""):
    print(f"  ✓ {msg}")


# ==================== get_target_id ====================

def test_get_target_id():
    """各事件类型的统一目标 ID"""
    sec("get_target_id")

    # 私聊 → user_id
    e = make_event(detail_type="private", user_id="u1")
    assert e.get_target_id() == "u1"; ok("private → u1")

    # 群聊 → group_id
    e = make_event(detail_type="group", user_id="u2", group_id="g123")
    assert e.get_target_id() == "g123"; ok("group → g123")

    # 频道 → channel_id
    e = make_event(detail_type="channel", channel_id="ch_x", user_id="u3")
    assert e.get_target_id() == "ch_x"; ok("channel → ch_x")

    # guild → guild_id
    e = make_event(detail_type="guild", guild_id="guild_1", user_id="u4")
    assert e.get_target_id() == "guild_1"; ok("guild → guild_1")

    # 没有特殊 type 时退回 user_id
    e = make_event(detail_type="unknown", user_id="u5")
    assert e.get_target_id() == "u5"; ok("fallback → u5")

    print()


# ==================== get_session_id ====================

def test_get_session_id():
    """会话唯一标识"""
    sec("get_session_id")

    e = make_event(platform="qq", detail_type="group", group_id="123")
    sid = e.get_session_id()
    assert sid == "qq:group:123"
    ok(f"group: {sid}")

    e = make_event(platform="telegram", detail_type="private", user_id="456")
    sid = e.get_session_id()
    assert sid == "telegram:private:456"
    ok(f"private: {sid}")

    print()


# ==================== supports / available_methods ====================

def test_supports_and_available():
    """平台能力查询"""
    sec("supports / available_methods")

    e = make_event()

    # supports 返回 bool
    result = e.supports("Text")
    assert isinstance(result, bool); ok(f"supports('Text') → {result}")

    result = e.supports("NonExistentMethod_XYZ")
    assert result is False; ok(f"supports('不存在的方法') → False")

    # available_methods 返回列表
    methods = e.available_methods()
    assert isinstance(methods, list); ok(f"available_methods() 返回列表，长度 {len(methods)}")

    print()


# ==================== reply at_sender / quote ====================

def test_reply_params():
    """reply() 新参数"""
    sec("reply 新参数 at_sender / quote")

    e = make_event()

    # 先检查方法签名包含新参数
    import inspect
    sig = inspect.signature(e.reply)
    params = list(sig.parameters.keys())
    assert "at_sender" in params; ok("at_sender 参数存在")
    assert "quote" in params; ok("quote 参数存在")
    assert "at_users" in params; ok("at_users 参数保留")
    assert "reply_to" in params; ok("reply_to 参数保留")
    assert "at_all" in params; ok("at_all 参数保留")

    print()


# ==================== 通配符扩展 ====================

def test_wildcard_extension():
    """register_event_method('*') 跨平台生效"""
    sec("register_event_method 通配符 '*'")

    @register_event_method("*")
    async def cross_platform_greet(self):
        return f"hello from {self.get_platform()}"

    # QQ 平台也能用
    e1 = make_event(platform="qq")
    result = asyncio.run(e1.cross_platform_greet())
    assert "qq" in result; ok(f"QQ 平台: {result}")

    # Telegram 平台也能用
    e2 = make_event(platform="telegram")
    result = asyncio.run(e2.cross_platform_greet())
    assert "telegram" in result; ok(f"Telegram 平台: {result}")

    # dir() 包含
    assert "cross_platform_greet" in dir(e1); ok("dir() 包含通配符方法")

    # 注销
    unregister_event_method("*", "cross_platform_greet")
    assert "cross_platform_greet" not in dir(e1); ok("注销后 dir() 不再包含")

    print()


# ==================== 内置优先于通配符 ====================

def test_wildcard_not_override_builtin():
    """通配符不覆盖内置方法（get_text 仍然返回原始文本）"""
    sec("通配符不覆盖内置方法")

    @register_event_method("*")
    def fake_get_text(self):
        return "FAKE"

    e = make_event()
    # 直接调用应返回内置结果（__getattribute__ 优先）
    assert e.get_text() == "hello"; ok("内置方法优先，返回 'hello'")

    unregister_event_method("*", "fake_get_text")
    print()


if __name__ == "__main__":
    test_get_target_id()
    test_get_session_id()
    test_supports_and_available()
    test_reply_params()
    test_wildcard_extension()
    test_wildcard_not_override_builtin()
    print(f"{'=' * 50}")
    print("  全部测试通过 ✓")
    print(f"{'=' * 50}")
