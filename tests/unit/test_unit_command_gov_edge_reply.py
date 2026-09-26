"""
命令治理边沿回复单元测试

验证 ``cooldown_reply=`` / ``rate_limit_reply=`` / ``usage_limit_reply=`` 的
边沿触发语义：仅在状态翻转（进入新冷却窗口 / 限流窗口再次填满 / 进入新
自然周期）后的首次命中回复一次，同窗口 / 同周期的后续命中保持静默——
避免连击时治理回复本身刷屏；窗口重置 / 周期切换后重新可回复。
"""

import asyncio
import importlib
from unittest.mock import AsyncMock, patch

import pytest

from ErisPulse.Core.Event.command import command as command_handler
from ErisPulse.Core.Event import governance as governance_module

# importlib.import_module 返回真实子模块（Core.config 包属性被 ConfigManager 单例遮蔽）
config_module = importlib.import_module("ErisPulse.Core.config")

# 治理回复捕获：分发期 gate 的 send_reply 回调统一走 _send_args_error
_replies: "list[str]" = []


@pytest.fixture(autouse=True)
def clean_state():
    from ErisPulse.Core.adapter import adapter
    from ErisPulse.Core.Event import _clear_all_handlers

    def _clean():
        _clear_all_handlers()
        command_handler.commands.clear()
        command_handler.aliases.clear()
        command_handler.groups.clear()
        command_handler.permissions.clear()
        command_handler._cooldowns.clear()
        command_handler._rate_limits.clear()
        command_handler._usage_counts.clear()
        command_handler._gate._cooldown_replied.clear()
        command_handler._gate._rate_limit_replied.clear()
        command_handler._gate._usage_replied.clear()
        command_handler._max_name_tokens = 1
        command_handler.block = True
        adapter._onebot_handlers.clear()
        adapter._raw_handlers.clear()
        adapter._onebot_middlewares.clear()
        adapter._bots.clear()
        _replies.clear()

    _clean()
    yield
    _clean()


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

    with patch.object(config_module.config, "getConfig", return_value="/"), patch.object(
        command_handler,
        "_send_args_error",
        new=AsyncMock(side_effect=lambda e, t: _replies.append(t)),
    ):
        await adapter.emit(_msg(text, **kwargs))
        await asyncio.sleep(0.05)


class TestCooldownEdgeReply:
    """cooldown_reply=：每个冷却窗口至多回复一次"""

    async def test_reply_once_per_window(self):
        calls = []

        @command_handler("ed_cd", cooldown="0.5s", cooldown_reply="冷却中")
        async def ed_cd(event):
            calls.append(1)

        await _dispatch("/ed_cd")   # 窗口开启，执行
        await _dispatch("/ed_cd")   # 命中：首次回复
        await _dispatch("/ed_cd")   # 同窗口：静默
        assert len(calls) == 1
        assert _replies == ["冷却中"]

    async def test_new_window_replies_again(self):
        calls = []

        @command_handler("ed_cd2", cooldown="0.3s", cooldown_reply="冷却中")
        async def ed_cd2(event):
            calls.append(1)

        await _dispatch("/ed_cd2")
        await _dispatch("/ed_cd2")      # 窗口 1 命中：回复
        await asyncio.sleep(0.4)
        await _dispatch("/ed_cd2")      # 新窗口开启：执行
        await _dispatch("/ed_cd2")      # 窗口 2 命中：再次回复
        assert len(calls) == 2
        assert _replies == ["冷却中", "冷却中"]


class TestRateLimitEdgeReply:
    """rate_limit_reply=：窗口从"未满"再次变为"已满"的首次命中才回复"""

    async def test_reply_once_per_full_window(self):
        calls = []

        @command_handler("ed_rl", rate_limit="2/minute", rate_limit_reply="太频繁")
        async def ed_rl(event):
            calls.append(1)

        await _dispatch("/ed_rl")   # 放行 1
        await _dispatch("/ed_rl")   # 放行 2
        await _dispatch("/ed_rl")   # 窗口满：首次命中 → 回复
        await _dispatch("/ed_rl")   # 仍满：静默
        assert len(calls) == 2
        assert _replies == ["太频繁"]

    async def test_pass_clears_mark(self):
        calls = []

        @command_handler("ed_rl2", rate_limit="1/0.3s", rate_limit_reply="慢一点")
        async def ed_rl2(event):
            calls.append(1)

        await _dispatch("/ed_rl2")  # 放行
        await _dispatch("/ed_rl2")  # 窗口满：回复
        await asyncio.sleep(0.4)
        await _dispatch("/ed_rl2")  # 新窗口放行：清除标记
        await _dispatch("/ed_rl2")  # 再次填满：重新回复
        assert _replies == ["慢一点", "慢一点"]


class TestUsageLimitEdgeReply:
    """usage_limit_reply=：每个自然周期至多回复一次，周期切换重新可回复"""

    async def test_reply_once_per_period(self):
        import uuid

        calls = []
        # usage 计数按命令名经 storage KV 持久化：随机命令名保证跨运行干净
        #（今天跑过的残留计数不会把配额提前耗尽）
        name = f"ed_us_{uuid.uuid4().hex[:6]}"

        @command_handler(name, usage_limit="2/day", usage_limit_reply="今日已用完")
        async def ed_us(event):
            calls.append(1)

        await _dispatch(f"/{name}")   # 消耗 1
        await _dispatch(f"/{name}")   # 消耗 2
        await _dispatch(f"/{name}")   # 配额用尽：首次命中 → 回复
        await _dispatch(f"/{name}")   # 同周期：静默
        assert len(calls) == 2
        assert _replies == ["今日已用完"]

    async def test_period_switch_replies_again(self):
        import uuid

        calls = []
        # 按调用计数切换周期（勿用定长迭代器：任何额外调用都会耗尽抛 StopIteration）
        state = {"n": 0}

        def fake_period(unit, *a, **k):
            state["n"] += 1
            return "P1" if state["n"] <= 3 else "P2"

        name = f"ed_us2_{uuid.uuid4().hex[:6]}"

        @command_handler(name, usage_limit="1/day", usage_limit_reply="明天再来")
        async def ed_us2(event):
            calls.append(1)

        with patch.object(governance_module, "usage_period_key", side_effect=fake_period):
            await _dispatch(f"/{name}")  # P1 消耗 1
            await _dispatch(f"/{name}")  # P1 用尽：回复
            await _dispatch(f"/{name}")  # P1 静默
            await _dispatch(f"/{name}")  # P2 消耗 1（周期切换重置）
            await _dispatch(f"/{name}")  # P2 用尽：再次回复

        assert len(calls) == 2
        assert _replies == ["明天再来", "明天再来"]
