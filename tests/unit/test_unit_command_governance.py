"""
命令治理声明化（rate_limit= / deprecated=）单元测试

EPRFC-2026-001 方向七余项（2.9 提前交付）。测试滑动窗口限流（窗口计数、
静默丢弃与可选回复、user/session/global 三粒度、窗口过期、与 cooldown
共存、卸载清理）、废弃声明（自动回复、reject 拒绝执行、help 列表与单命令
帮助的废弃标记）、注册期校验矩阵。
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
    command_handler._rate_limits.clear()
    command_handler._usage_counts.clear()
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
    command_handler._rate_limits.clear()
    command_handler._usage_counts.clear()
    command_handler._max_name_tokens = 1
    command_handler.block = True
    adapter._onebot_handlers.clear()
    adapter._raw_handlers.clear()
    adapter._onebot_middlewares.clear()
    adapter._bots.clear()


def _msg(text, platform="onebot11", bot_id="bot_x", user_id="u1", group_id=None):
    data = {
        "id": f"id_{abs(hash((text, user_id, group_id)))}",
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
    from ErisPulse.Core.adapter import adapter

    with patch.object(config_module.config, "getConfig", return_value="/"):
        await adapter.emit(_msg(text, **kwargs))
        await asyncio.sleep(0.05)


class TestRateLimitRegistration:
    def test_valid_declaration_stored(self):
        @command_handler("rl_ok", rate_limit="5/minute", rate_limit_key="session", rate_limit_reply="太频繁")
        async def rl_ok(event):
            pass

        info = command_handler.commands["rl_ok"]
        assert info["rate_limit_spec"] == (5, 60.0)
        assert info["rate_limit_key"] == "session"
        assert info["rate_limit_reply"] == "太频繁"

    def test_short_units_accepted(self):
        @command_handler("rl_short", rate_limit="10/s")
        async def rl_short(event):
            pass

        assert command_handler.commands["rl_short"]["rate_limit_spec"] == (10, 1.0)

    def test_invalid_syntax_rejected(self):
        with pytest.raises(ValueError):

            @command_handler("rl_bad", rate_limit="5 per minute")
            async def rl_bad(event):
                pass

    def test_zero_count_rejected(self):
        with pytest.raises(ValueError):

            @command_handler("rl_zero", rate_limit="0/minute")
            async def rl_zero(event):
                pass

    def test_invalid_key_rejected(self):
        with pytest.raises(ValueError):

            @command_handler("rl_key", rate_limit="1/s", rate_limit_key="room")
            async def rl_key(event):
                pass

    def test_reply_without_limit_rejected(self):
        with pytest.raises(ValueError):

            @command_handler("rl_reply_only", rate_limit_reply="x")
            async def rl_reply_only(event):
                pass


class TestRateLimitDispatch:
    async def test_window_count_and_silent_drop(self):
        """窗口内第 N+1 次静默丢弃，命令保持认领"""
        calls = []

        @command_handler("rl_count", rate_limit="2/minute")
        async def rl_count(event):
            calls.append(1)

        await _dispatch("/rl_count")
        await _dispatch("/rl_count")
        await _dispatch("/rl_count")  # 第 3 次：超出窗口，静默丢弃
        assert len(calls) == 2

    async def test_reply_sent_on_hit(self):
        calls, replies = [], []

        @command_handler("rl_reply", rate_limit="1/minute", rate_limit_reply="慢一点")
        async def rl_reply(event):
            calls.append(1)

        with patch.object(
            command_handler, "_send_args_error", new=AsyncMock(side_effect=lambda e, t: replies.append(t))
        ):
            await _dispatch("/rl_reply")
            await _dispatch("/rl_reply")

        assert len(calls) == 1
        assert replies == ["慢一点"]

    async def test_user_key_isolation(self):
        calls = []

        @command_handler("rl_user", rate_limit="1/minute", rate_limit_key="user")
        async def rl_user(event):
            calls.append(event.get("user_id"))

        await _dispatch("/rl_user", user_id="u1")
        await _dispatch("/rl_user", user_id="u1")  # 同用户：命中
        await _dispatch("/rl_user", user_id="u2")  # 不同用户：独立窗口
        assert calls == ["u1", "u2"]

    async def test_session_key_isolation(self):
        calls = []

        @command_handler("rl_sess", rate_limit="1/minute", rate_limit_key="session")
        async def rl_sess(event):
            calls.append(event.get("user_id"))

        await _dispatch("/rl_sess", user_id="u1", group_id="g1")
        await _dispatch("/rl_sess", user_id="u2", group_id="g1")  # 同会话：命中
        await _dispatch("/rl_sess", user_id="u1", group_id="g2")  # 换会话：放行
        assert calls == ["u1", "u1"]

    async def test_window_expiry_restores(self):
        calls = []

        @command_handler("rl_short", rate_limit="1/0.3s")
        async def rl_short(event):
            calls.append(1)

        await _dispatch("/rl_short")
        await _dispatch("/rl_short")
        assert len(calls) == 1
        await asyncio.sleep(0.35)
        await _dispatch("/rl_short")
        assert len(calls) == 2

    async def test_cooldown_and_rate_limit_coexist(self):
        """同时声明：冷却先判（长窗口），限流后判（短窗口计数）"""
        calls = []

        @command_handler("rl_both", cooldown="1h", rate_limit="5/minute")
        async def rl_both(event):
            calls.append(1)

        await _dispatch("/rl_both")
        await _dispatch("/rl_both")  # 冷却命中（限流不计数）
        assert len(calls) == 1
        assert len(command_handler._rate_limits) == 1  # 仅一次放行计入窗口
        assert len(command_handler._rate_limits[list(command_handler._rate_limits)[0]]) == 1

    async def test_cleanup_on_unregister_by_owner(self):
        from ErisPulse.runtime.context import current_owner

        token = current_owner.set("some_module")
        try:

            @command_handler("rl_clean", rate_limit="2/minute")
            async def rl_clean(event):
                pass
        finally:
            current_owner.reset(token)

        await _dispatch("/rl_clean")
        assert command_handler._rate_limits

        command_handler.unregister_by_owner("some_module")
        assert command_handler._rate_limits == {}
        assert command_handler._cooldowns == {}


class TestDeprecated:
    async def test_notice_reply_then_executes(self):
        """默认：回复废弃文案后继续执行"""
        calls, replies = [], []

        @command_handler("dep_soft", deprecated="请用 /new")
        async def dep_soft(event):
            calls.append(1)

        with patch.object(
            command_handler, "_send_args_error", new=AsyncMock(side_effect=lambda e, t: replies.append(t))
        ):
            await _dispatch("/dep_soft")

        assert calls == [1]  # 仍执行
        assert replies == ["请用 /new"]  # 且先回复废弃文案

    async def test_reject_blocks_execution(self):
        calls, replies = [], []

        @command_handler("dep_hard", deprecated="请用 /new", deprecated_reject=True)
        async def dep_hard(event):
            calls.append(1)

        with patch.object(
            command_handler, "_send_args_error", new=AsyncMock(side_effect=lambda e, t: replies.append(t))
        ):
            await _dispatch("/dep_hard")

        assert calls == []  # 拒绝执行
        assert replies == ["请用 /new"]

    async def test_reject_fires_executed_hook_with_failure(self):
        from ErisPulse.Core.lifecycle import lifecycle

        executed = []
        lifecycle.register("command.executed", lambda data: executed.append(data))

        try:

            @command_handler("dep_hook", deprecated="x", deprecated_reject=True)
            async def dep_hook(event):
                pass

            await _dispatch("/dep_hook")
            await asyncio.sleep(0.1)
        finally:
            lifecycle.unregister("command.executed")

        assert executed and executed[-1]["success"] is False
        assert executed[-1]["error"] == "deprecated"

    def test_help_list_shows_mark(self):
        @command_handler("dep_list", deprecated="请用 /new", help="旧命令")
        async def dep_list(event):
            pass

        text = command_handler.help()
        assert "已废弃" in text
        assert "旧命令" in text

    def test_help_single_command_shows_notice(self):
        @command_handler("dep_one", deprecated="请用 /newcmd", help="旧功能")
        async def dep_one(event):
            pass

        text = command_handler.help("dep_one")
        assert "已废弃" in text
        assert "请用 /newcmd" in text

    def test_invalid_declarations_rejected(self):
        with pytest.raises(ValueError):

            @command_handler("dep_empty", deprecated="  ")
            async def dep_empty(event):
                pass

        with pytest.raises(ValueError):

            @command_handler("dep_reject_only", deprecated_reject=True)
            async def dep_reject_only(event):
                pass


class TestRateLimitTrace:
    async def test_rate_limit_drop_observed_in_trace(self):
        from ErisPulse.Core.Event.trace import start_dispatch_trace

        @command_handler("rl_trace", rate_limit="1/minute")
        async def rl_trace(event):
            pass

        from ErisPulse.Core.adapter import adapter

        with patch.object(config_module.config, "getConfig", return_value="/"):
            with start_dispatch_trace() as records:
                await adapter.emit(_msg("/rl_trace"))
                await asyncio.sleep(0.05)
                await adapter.emit(_msg("/rl_trace"))
                await asyncio.sleep(0.05)

        stages = [(r["stage"], r["verdict"]) for r in records]
        assert ("rate_limit", "dropped") in stages


class TestUsageLimit:
    """usage_limit= 自然周期配额"""

    @pytest.fixture(autouse=True)
    def fake_storage(self, monkeypatch):
        """以内存 dict 替换 storage KV（实际定义在 SQLStorageBase），隔离真实 DB 跨运行持久化"""
        from ErisPulse.Core.Bases.sql_base import SQLStorageBase

        stored: dict = {}

        async def fake_aget(self, key, default=None, **kwargs):
            return stored.get(key, default)

        async def fake_aset(self, key, value, **kwargs):
            stored[key] = value
            return True

        monkeypatch.setattr(SQLStorageBase, "aget", fake_aget)
        monkeypatch.setattr(SQLStorageBase, "aset", fake_aset)
        self._stored = stored
        yield

    def test_valid_declaration_stored(self):
        @command_handler("us_ok", usage_limit="3/day", usage_limit_key="user", usage_limit_reply="今日已用完")
        async def us_ok(event):
            pass

        info = command_handler.commands["us_ok"]
        assert info["usage_spec"] == (3, "day")
        assert info["usage_limit_key"] == "user"
        assert info["usage_limit_reply"] == "今日已用完"

    def test_invalid_declarations_rejected(self):
        with pytest.raises(ValueError):

            @command_handler("us_bad", usage_limit="3/week")
            async def us_bad(event):
                pass

        with pytest.raises(ValueError):

            @command_handler("us_key", usage_limit="1/day", usage_limit_key="room")
            async def us_key(event):
                pass

        with pytest.raises(ValueError):

            @command_handler("us_reply", usage_limit_reply="x")
            async def us_reply(event):
                pass

    def test_period_key_formats(self):
        day = command_handler.usage_period_key("day")
        hour = command_handler.usage_period_key("hour")
        minute = command_handler.usage_period_key("minute")
        assert len(day) == 10 and "T" not in day
        assert "T" in hour and len(hour) == 13
        assert len(minute) == 16

    async def test_quota_count_and_reply(self):
        calls, replies = [], []

        @command_handler("us_count", usage_limit="2/day", usage_limit_reply="今日次数已用完")
        async def us_count(event):
            calls.append(1)

        with patch.object(
            command_handler, "_send_args_error", new=AsyncMock(side_effect=lambda e, t: replies.append(t))
        ):
            await _dispatch("/us_count")
            await _dispatch("/us_count")
            await _dispatch("/us_count")  # 第 3 次：配额用尽

        assert len(calls) == 2
        assert replies == ["今日次数已用完"]

    async def test_user_isolation_and_memory_fallback(self, monkeypatch):
        """storage 异常时回退内存计数；用户间隔离"""
        calls = []

        @command_handler("us_iso", usage_limit="1/day")
        async def us_iso(event):
            calls.append(event.get("user_id"))

        await _dispatch("/us_iso", user_id="u1")
        await _dispatch("/us_iso", user_id="u1")  # 同用户：用尽
        await _dispatch("/us_iso", user_id="u2")  # 其他用户独立
        assert calls == ["u1", "u2"]

    async def test_persisted_count_survives_memory_reset(self, monkeypatch):
        """storage 计数高于内存时以其为准（模拟重启后内存清零）"""
        calls = []

        @command_handler("us_persist", usage_limit="2/day")
        async def us_persist(event):
            calls.append(1)

        stored = self._stored

        await _dispatch("/us_persist")
        await _dispatch("/us_persist")
        assert len(calls) == 2

        command_handler._usage_counts.clear()  # 模拟重启：内存清零
        await _dispatch("/us_persist")  # storage 计数=2 ≥ 上限：仍拒绝
        assert len(calls) == 2

    async def test_cleanup_on_unregister(self):
        from ErisPulse.runtime.context import current_owner

        token = current_owner.set("us_mod")
        try:

            @command_handler("us_clean", usage_limit="2/day")
            async def us_clean(event):
                pass
        finally:
            current_owner.reset(token)

        command_handler._usage_counts["us_clean\x00scope\x00period"] = 5
        command_handler.unregister_by_owner("us_mod")
        assert command_handler._usage_counts == {}
