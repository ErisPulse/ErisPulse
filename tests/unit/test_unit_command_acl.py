"""
命令权限 ACL 与消息通配符单元测试

测试命令用户黑白名单（控制面 scope.commands + 运行时 API + 判定链，命令名支持
glob），以及 message 装饰器 / wait_reply 的 pattern（glob）与 regex 过滤。
"""

import asyncio
from unittest.mock import patch

import pytest

from ErisPulse.Core.Event.command import command as command_handler
from ErisPulse.Core.Event.message import message as message_handler
from ErisPulse.Core.scope import scope as scope_manager
from ErisPulse.runtime.context import current_owner


@pytest.fixture(autouse=True)
def clean_state():
    from ErisPulse.Core.adapter import adapter
    from ErisPulse.Core.Event import _clear_all_handlers

    _clear_all_handlers()
    command_handler.commands.clear()
    command_handler.aliases.clear()
    command_handler.groups.clear()
    command_handler.permissions.clear()
    command_handler._waiting_replies.clear()
    scope_manager._bindings["commands"].clear()
    message_handler.handler.handlers.clear()
    message_handler.handler._handler_map.clear()
    adapter._onebot_handlers.clear()
    adapter._raw_handlers.clear()
    adapter._onebot_middlewares.clear()
    adapter._bots.clear()
    yield
    _clear_all_handlers()
    command_handler.commands.clear()
    command_handler.aliases.clear()
    command_handler.groups.clear()
    command_handler.permissions.clear()
    command_handler._waiting_replies.clear()
    scope_manager._bindings["commands"].clear()
    message_handler.handler.handlers.clear()
    message_handler.handler._handler_map.clear()
    adapter._onebot_handlers.clear()
    adapter._raw_handlers.clear()
    adapter._onebot_middlewares.clear()
    adapter._bots.clear()


def _msg(text, platform="onebot11", bot_id="bot_x", user_id="u1", group_id=None):
    data = {
        "id": f"id_{abs(hash(text))}",
        "time": 1712345678,
        "type": "message",
        "detail_type": "group" if group_id else "private",
        "platform": platform,
        "self": {"platform": platform, "user_id": bot_id},
        "user_id": user_id,
        "user_nickname": "User1",
        "message": [{"type": "text", "data": {"text": text}}],
        "alt_message": text,
    }
    if group_id:
        data["group_id"] = group_id
    return data


class TestCommandACL:
    """命令权限 ACL（控制面 scope.commands，命令名支持 glob）"""

    @pytest.mark.asyncio
    async def test_deny_user_blocks(self):
        """deny 名单命中 → 拒绝执行并回复权限不足"""
        from ErisPulse.Core.adapter import adapter
        from ErisPulse.Core.Event import command

        received = []
        token = current_owner.set("ModuleA")
        try:

            @command("alpha")
            async def alpha(event):
                received.append("A")

        finally:
            current_owner.reset(token)

        @command("beta")
        async def beta(event):
            received.append("B")

        with patch("ErisPulse.Core.scope.set_erispulse_section"):
            command_handler.deny_user("beta", "onebot11", "u_bad")
        with patch("ErisPulse.Core.config.config.getConfig", return_value="/"):
            await adapter.emit(_msg("/beta", user_id="u_bad"))
            await asyncio.sleep(0.05)
            await adapter.emit(_msg("/beta", user_id="u_good"))
            await asyncio.sleep(0.05)

        assert received == ["B"]  # 仅 u_good 执行

    @pytest.mark.asyncio
    async def test_allow_list_restricts(self):
        """allow 名单非空 → 仅名单内用户可执行"""
        from ErisPulse.Core.adapter import adapter
        from ErisPulse.Core.Event import command

        received = []
        token = current_owner.set("ModuleA")
        try:

            @command("gamma")
            async def gamma(event):
                received.append(event.get("user_id"))

        finally:
            current_owner.reset(token)

        with patch("ErisPulse.Core.scope.set_erispulse_section"):
            command_handler.allow_user("gamma", "onebot11", "u_vip")
        with patch("ErisPulse.Core.config.config.getConfig", return_value="/"):
            await adapter.emit(_msg("/gamma", user_id="u_vip"))
            await asyncio.sleep(0.05)
            await adapter.emit(_msg("/gamma", user_id="u_normal"))
            await asyncio.sleep(0.05)

        assert received == ["u_vip"]

    @pytest.mark.asyncio
    async def test_deny_wins_over_allow(self):
        """同用户同时在 allow 与 deny 名单 → deny 优先"""
        from ErisPulse.Core.adapter import adapter
        from ErisPulse.Core.Event import command

        received = []
        token = current_owner.set("ModuleA")
        try:

            @command("delta")
            async def delta(event):
                received.append("D")

        finally:
            current_owner.reset(token)

        with patch("ErisPulse.Core.scope.set_erispulse_section"):
            command_handler.allow_user("delta", "onebot11", "u1")
            command_handler.deny_user("delta", "onebot11", "u1")
        with patch("ErisPulse.Core.config.config.getConfig", return_value="/"):
            await adapter.emit(_msg("/delta", user_id="u1"))
            await asyncio.sleep(0.05)

        assert received == []

    def test_glob_acl_matches_actual_command(self):
        """glob ACL 键匹配实际命令名"""
        with patch("ErisPulse.Core.scope.set_erispulse_section"):
            command_handler.deny_user("roll*", "onebot11", "u_bad")
        assert command_handler.get_acl("roll_dice") == {
            "allow": [],
            "deny": ["onebot11:u_bad"],
        }
        assert scope_manager.is_command_allowed("roll_dice", "onebot11", "u_bad") is False
        assert scope_manager.is_command_allowed("roll_dice", "onebot11", "u_ok") is True

    def test_exact_acl_over_glob(self):
        """精确 ACL 键优先于 glob 键"""
        scope_manager._bindings["commands"]["roll"] = {"deny": ["p:u2"]}
        scope_manager._bindings["commands"]["roll*"] = {"allow": ["p:u2"]}
        assert scope_manager.is_command_allowed("roll", "p", "u2") is False

    def test_get_acl_returns_lists(self):
        """get_acl 返回 allow/deny 列表"""
        scope_manager._bindings["commands"]["alpha"] = {
            "allow": ["onebot11:u1"],
            "deny": ["onebot11:u2"],
        }
        assert command_handler.get_acl("alpha") == {
            "allow": ["onebot11:u1"],
            "deny": ["onebot11:u2"],
        }

    def test_remove_acl(self):
        """remove_acl 清除 ACL 并持久化"""
        scope_manager._bindings["commands"]["alpha"] = {"deny": ["onebot11:u1"]}
        with patch("ErisPulse.Core.scope.set_erispulse_section") as fake:
            assert command_handler.remove_acl("alpha") is True
        assert scope_manager.get_acl("alpha") == {"allow": [], "deny": []}
        fake.assert_called_once()

    def test_allow_user_writes_scope_commands(self):
        """allow_user 写入 scope.commands"""
        with patch("ErisPulse.Core.scope.set_erispulse_section") as _:
            command_handler.allow_user("beta", "onebot11", "u1")
        assert scope_manager._bindings["commands"]["beta"]["allow"] == ["onebot11:u1"]

    def test_acl_loaded_from_scope_config(self):
        """配置热更新后 scope.commands 生效"""
        with patch(
            "ErisPulse.runtime.get_config",
            return_value={"commands": {"roll": {"deny": ["p:u"]}}},
        ):
            scope_manager._on_config_updated({})
        try:
            assert scope_manager.is_command_allowed("roll", "p", "u") is False
        finally:
            scope_manager._on_config_updated({})


class TestMessagePattern:
    """message 装饰器 pattern / regex 过滤"""

    @pytest.mark.asyncio
    async def test_on_message_pattern(self):
        """pattern 通配符：不匹配的消息不触发"""
        from ErisPulse.Core.adapter import adapter

        received = []
        token = current_owner.set("ModuleA")
        try:

            @message_handler.on_message(pattern="签到*")
            async def handler(event):
                received.append(event.get_text())

        finally:
            current_owner.reset(token)

        await adapter.emit(_msg("签到成功"))
        await asyncio.sleep(0.05)
        await adapter.emit(_msg("打卡失败"))
        await asyncio.sleep(0.05)

        assert received == ["签到成功"]

    @pytest.mark.asyncio
    async def test_on_message_regex(self):
        """regex：不匹配的消息不触发"""
        from ErisPulse.Core.adapter import adapter

        received = []
        token = current_owner.set("ModuleA")
        try:

            @message_handler.on_message(regex=r"\d+\s*元")
            async def handler(event):
                received.append(event.get_text())

        finally:
            current_owner.reset(token)

        await adapter.emit(_msg("优惠 5 元"))
        await asyncio.sleep(0.05)
        await adapter.emit(_msg("没有优惠"))
        await asyncio.sleep(0.05)

        assert received == ["优惠 5 元"]

    @pytest.mark.asyncio
    async def test_on_private_message_pattern(self):
        """on_private_message 同时满足 detail_type 与 pattern"""
        from ErisPulse.Core.adapter import adapter

        received = []
        token = current_owner.set("ModuleA")
        try:

            @message_handler.on_private_message(pattern="*密*")
            async def handler(event):
                received.append(event.get_text())

        finally:
            current_owner.reset(token)

        # 群聊命中 pattern 但 detail_type 不匹配
        await adapter.emit(_msg("机密信息", group_id="g1"))
        await asyncio.sleep(0.05)
        # 私聊命中 pattern
        await adapter.emit(_msg("机密信息"))
        await asyncio.sleep(0.05)

        assert received == ["机密信息"]

    @pytest.mark.asyncio
    async def test_pattern_and_regex_both_required(self):
        """pattern 与 regex 同时给定需同时满足"""
        from ErisPulse.Core.adapter import adapter

        received = []
        token = current_owner.set("ModuleA")
        try:

            @message_handler.on_message(pattern="*号", regex=r"^[0-9]+号$")
            async def handler(event):
                received.append(event.get_text())

        finally:
            current_owner.reset(token)

        await adapter.emit(_msg("123号"))
        await asyncio.sleep(0.05)
        await adapter.emit(_msg("abc号"))  # glob 命中但 regex 不命中
        await asyncio.sleep(0.05)

        assert received == ["123号"]


class TestWaitReplyPattern:
    """wait_reply 的 pattern / regex 过滤"""

    @pytest.mark.asyncio
    async def test_check_pending_reply_pattern(self):
        """_check_pending_reply 对 pattern 不匹配的回复继续等待"""
        from ErisPulse.Core.Event.wrapper import Event

        loop = asyncio.get_running_loop()
        future = loop.create_future()
        wait_key = "onebot11:bot_x:u1:u1"
        command_handler._waiting_replies[wait_key] = {
            "future": future,
            "callback": None,
            "validator": None,
            "pattern": "*abc*",
            "regex": None,
            "timestamp": loop.time(),
        }

        # 不匹配的回复：不消费 future，仍保留等待条目
        await command_handler._check_pending_reply(Event(_msg("随便说点什么", user_id="u1")))
        assert wait_key in command_handler._waiting_replies
        assert not future.done()

        # 匹配的回复：消费 future，清除等待条目
        await command_handler._check_pending_reply(
            Event(_msg("abc 在这里", user_id="u1"))
        )
        assert wait_key not in command_handler._waiting_replies
        assert future.done()
        assert future.result().get("alt_message") == "abc 在这里"

    @pytest.mark.asyncio
    async def test_check_pending_reply_regex(self):
        """_check_pending_reply 对 regex 匹配的回复放行"""
        from ErisPulse.Core.Event.wrapper import Event

        loop = asyncio.get_running_loop()
        future = loop.create_future()
        wait_key = "onebot11:bot_x:u1:u1"
        command_handler._waiting_replies[wait_key] = {
            "future": future,
            "callback": None,
            "validator": None,
            "pattern": None,
            "regex": r"^\d+号$",
            "timestamp": loop.time(),
        }

        await command_handler._check_pending_reply(Event(_msg("不是数字", user_id="u1")))
        assert wait_key in command_handler._waiting_replies
        assert not future.done()

        await command_handler._check_pending_reply(Event(_msg("42号", user_id="u1")))
        assert wait_key not in command_handler._waiting_replies
        assert future.done()

