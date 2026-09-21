"""
命令冷却声明（cooldown= / cooldown_key= / cooldown_reply=）单元测试

EPRFC-2026-001 方向七（2.9.0 范围：cooldown）。测试注册期校验
（时长语法复用 args= duration 口径、粒度白名单、reply 须搭配 cooldown）、
分发期冷却判定（默认静默丢弃、可选回复文案、user/session/global 三粒度、
窗口过期恢复）、冷却计时时机（权限拒绝与参数错误不消耗冷却），
以及模块卸载（unregister / unregister_by_owner）自动清理冷却状态。
"""

import asyncio
import importlib
from unittest.mock import AsyncMock, patch

import pytest

from ErisPulse.Core.Event.command import command as command_handler

# importlib.import_module 返回真实子模块（Core.config 包属性被 ConfigManager 单例遮蔽）
config_module = importlib.import_module("ErisPulse.Core.config")


@pytest.fixture(autouse=True)
def clean_state():
    from ErisPulse.Core.adapter import adapter
    from ErisPulse.Core.Event import _clear_all_handlers

    _clear_all_handlers()
    command_handler.commands.clear()
    command_handler.aliases.clear()
    command_handler.groups.clear()
    command_handler.permissions.clear()
    command_handler._cooldowns.clear()
    command_handler._max_name_tokens = 1
    command_handler.block = True
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
    command_handler._cooldowns.clear()
    command_handler._max_name_tokens = 1
    command_handler.block = True
    adapter._onebot_handlers.clear()
    adapter._raw_handlers.clear()
    adapter._onebot_middlewares.clear()
    adapter._bots.clear()


def _msg(text, platform="onebot11", bot_id="bot_x", user_id="u1", group_id=None):
    data = {
        "id": f"id_{abs(hash(text))}_{user_id}_{group_id}",
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


async def _dispatch(text, **kwargs):
    """以 "/" 命令前缀分发消息事件并等待命令分发完成"""
    from ErisPulse.Core.adapter import adapter

    with patch.object(config_module.config, "getConfig", return_value="/"):
        await adapter.emit(_msg(text, **kwargs))
        await asyncio.sleep(0.05)


class TestCooldownRegistration:
    """注册期解析与校验（fail-fast）"""

    def test_valid_declaration_stored(self):
        @command_handler("cd_ok", cooldown="1h30m", cooldown_key="session", cooldown_reply="稍后")
        async def cd_ok(event):
            pass

        info = command_handler.commands["cd_ok"]
        assert info["cooldown_seconds"] == 5400.0
        assert info["cooldown_key"] == "session"
        assert info["cooldown_reply"] == "稍后"

    def test_defaults(self):
        @command_handler("cd_def", cooldown="30s")
        async def cd_def(event):
            pass

        info = command_handler.commands["cd_def"]
        assert info["cooldown_seconds"] == 30.0
        assert info["cooldown_key"] == "user"
        assert info["cooldown_reply"] is None

    def test_invalid_duration_rejected(self):
        with pytest.raises(ValueError):

            @command_handler("cd_bad", cooldown="abc")
            async def cd_bad(event):
                pass

    def test_non_positive_duration_rejected(self):
        with pytest.raises(ValueError):

            @command_handler("cd_zero", cooldown="0s")
            async def cd_zero(event):
                pass

    def test_invalid_key_rejected(self):
        with pytest.raises(ValueError):

            @command_handler("cd_key", cooldown="1s", cooldown_key="room")
            async def cd_key(event):
                pass

    def test_reply_without_cooldown_rejected(self):
        with pytest.raises(ValueError):

            @command_handler("cd_reply_only", cooldown_reply="x")
            async def cd_reply_only(event):
                pass


class TestCooldownDispatch:
    """分发期冷却判定"""

    @pytest.mark.asyncio
    async def test_second_call_within_window_silent(self):
        """窗口内第二次调用：默认静默丢弃，处理器不执行"""
        calls = []

        @command_handler("cd_silent", cooldown="1h")
        async def cd_silent(event):
            calls.append(1)

        await _dispatch("/cd_silent")
        await _dispatch("/cd_silent")
        assert len(calls) == 1

    @pytest.mark.asyncio
    async def test_cooldown_reply_sent_on_hit(self):
        """窗口内命中：声明 cooldown_reply 时回复该文案"""
        calls, replies = [], []

        @command_handler("cd_reply", cooldown="1h", cooldown_reply="今天已签到")
        async def cd_reply(event):
            calls.append(1)

        with patch.object(
            command_handler, "_send_args_error", new=AsyncMock(side_effect=lambda e, t: replies.append(t))
        ):
            await _dispatch("/cd_reply")
            await _dispatch("/cd_reply")

        assert len(calls) == 1
        assert replies == ["今天已签到"]

    @pytest.mark.asyncio
    async def test_user_key_isolation(self):
        """user 粒度：不同用户互不影响"""
        calls = []

        @command_handler("cd_user", cooldown="1h", cooldown_key="user")
        async def cd_user(event):
            calls.append(event.get("user_id"))

        await _dispatch("/cd_user", user_id="u1")
        await _dispatch("/cd_user", user_id="u1")  # 同用户：命中冷却
        await _dispatch("/cd_user", user_id="u2")  # 不同用户：放行
        assert calls == ["u1", "u2"]

    @pytest.mark.asyncio
    async def test_session_key_isolation(self):
        """session 粒度：同会话共享冷却，跨会话互不影响"""
        calls = []

        @command_handler("cd_sess", cooldown="1h", cooldown_key="session")
        async def cd_sess(event):
            calls.append(event.get("user_id"))

        await _dispatch("/cd_sess", user_id="u1", group_id="g1")
        await _dispatch("/cd_sess", user_id="u2", group_id="g1")  # 同会话：命中
        await _dispatch("/cd_sess", user_id="u1", group_id="g2")  # 换会话：放行
        assert calls == ["u1", "u1"]

    @pytest.mark.asyncio
    async def test_global_key_shared(self):
        """global 粒度：所有用户所有会话共享冷却"""
        calls = []

        @command_handler("cd_glob", cooldown="1h", cooldown_key="global")
        async def cd_glob(event):
            calls.append(1)

        await _dispatch("/cd_glob", user_id="u1")
        await _dispatch("/cd_glob", user_id="u2", group_id="g9")
        assert calls == [1]

    @pytest.mark.asyncio
    async def test_window_expiry_restores(self):
        """窗口过期后恢复可用"""
        calls = []

        @command_handler("cd_short", cooldown="0.1s")
        async def cd_short(event):
            calls.append(1)

        await _dispatch("/cd_short")
        await _dispatch("/cd_short")
        assert len(calls) == 1
        await asyncio.sleep(0.2)
        await _dispatch("/cd_short")
        assert len(calls) == 2

    @pytest.mark.asyncio
    async def test_args_error_does_not_consume_cooldown(self):
        """参数解析失败不消耗冷却（计时在参数解析成功后才开始）"""
        calls = []

        @command_handler("cd_args", args="<n:int>", cooldown="1h")
        async def cd_args(event, n: int):
            calls.append(n)

        replies = []
        with patch.object(
            command_handler, "_send_args_error", new=AsyncMock(side_effect=lambda e, t: replies.append(t))
        ):
            await _dispatch("/cd_args abc")  # 参数错误：不进入冷却
            await _dispatch("/cd_args 5")  # 随后正常执行

        assert calls == [5]
        assert len(replies) == 1  # 仅参数错误的那次回复


class TestCooldownCleanup:
    """模块卸载自动清理冷却状态"""

    @pytest.mark.asyncio
    async def test_unregister_clears_cooldown_state(self):
        @command_handler("cd_clean", cooldown="1h")
        async def cd_clean(event):
            pass

        await _dispatch("/cd_clean")
        assert command_handler._cooldowns  # 已有冷却条目

        command_handler.unregister(cd_clean)
        assert command_handler._cooldowns == {}

    @pytest.mark.asyncio
    async def test_unregister_by_owner_clears_cooldown_state(self):
        from ErisPulse.runtime.context import current_owner

        token = current_owner.set("some_module")
        try:

            @command_handler("cd_owner", cooldown="1h")
            async def cd_owner(event):
                pass
        finally:
            current_owner.reset(token)

        await _dispatch("/cd_owner")
        assert command_handler._cooldowns

        command_handler.unregister_by_owner("some_module")
        assert command_handler._cooldowns == {}
