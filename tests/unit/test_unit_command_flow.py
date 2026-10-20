"""
命令多轮流控语法糖（.got() 链）单元测试

覆盖：链式收集与参数注入、类型解析重试、超时终止、跨重启检查点续跑、
代理透明性（调用转发 / 属性转发 / unregister 解包）。
"""

import asyncio
import time

import pytest

from ErisPulse.Core.Event import CommandFlow
from ErisPulse.Core.Event.command import command
from ErisPulse.Core.Event.conversation import (
    Conversation,
    _conversation_resume_handlers,
)
from ErisPulse.Core.Event.wrapper import Event


def _make_event(text: str | None = None, user_id: str = "u1", **over) -> Event:
    data = {
        "platform": "test",
        "detail_type": "private",
        "user_id": user_id,
        "bot_id": "b1",
        "target_id": user_id,
        "time": time.time(),
        "message": [{"type": "text", "data": {"text": text or ""}}],
    }
    if text is not None:
        data["message_text"] = text
    data.update(over)
    return Event(data)


class _ScriptedWait:
    """脚本化 Event.wait_reply：按序列返回回复；序列耗尽时可阻塞模拟等待"""

    def __init__(self):
        self.script: list[str | None] = []
        self.prompts: list[str | None] = []
        self.block_when_empty = False
        self._block_event = asyncio.Event()

    def patch_into(self, monkeypatch):
        # 闭包普通函数挂类属性：描述符绑定后 self = 事件实例，闭包可达 sw
        sw = self

        async def fake_wait_reply(event_self, prompt=None, timeout=None, **kwargs):
            sw.prompts.append(prompt)
            if sw.script:
                text = sw.script.pop(0)
                return _make_event(text, user_id=event_self.get("user_id"))
            if sw.block_when_empty:
                await sw._block_event.wait()
            return None

        monkeypatch.setattr(Event, "wait_reply", fake_wait_reply)

    def unblock(self):
        self._block_event.set()


@pytest.fixture
def scripted(monkeypatch):
    sw = _ScriptedWait()
    sw.patch_into(monkeypatch)
    yield sw
    _conversation_resume_handlers.clear()
    sw.unblock()


@pytest.mark.unit
class TestCommandFlow:
    """.got() 链：收集 / 注入 / 检查点"""

    async def test_happy_chain_collects_and_injects(self, scripted, monkeypatch):
        seen = {}

        @command("flow_weather")
        async def weather(event):
            seen["entry"] = True

        @weather.got("city", prompt="城市?")
        async def weather_city(event, city: str):
            seen["city"] = city

        @weather.got("days", prompt="几天?", type=int)
        async def weather_days(event, city: str, days: int):
            seen["days"] = (city, days)

        scripted.script = ["北京", "3"]
        await weather(_make_event("x"))
        await asyncio.sleep(0.1)

        assert seen.get("entry") is True
        assert seen.get("city") == "北京"
        assert seen.get("days") == ("北京", 3)
        # 提示按步骤顺序自动发送（重试提示缺省复用 prompt）
        assert scripted.prompts == ["城市?", "几天?"]
        # 流程完成：检查点清除
        from ErisPulse.Core.storage import storage

        key = Conversation._checkpoint_key(_make_event("x"))
        assert not storage.get(key)
        assert _conversation_resume_handlers, "装饰期应注册恢复工厂"

    async def test_type_retry_then_success(self, scripted):
        seen = {}

        @command("flow_retry")
        async def fr(event):
            pass

        @fr.got("n", prompt="数字?", type=int, max_retries=2)
        async def fr_got(event, n: int):
            seen["n"] = n

        scripted.script = ["abc", "3"]
        await fr(_make_event("x"))
        await asyncio.sleep(0.1)

        assert seen.get("n") == 3
        # 失败后重发过提示（3 次调用：初始 + 重试）
        assert len(scripted.prompts) == 2

    async def test_max_retries_exhausted_ends_flow(self, scripted):
        seen = {}

        @command("flow_dead")
        async def fd(event):
            pass

        @fd.got("n", prompt="数字?", type=int, max_retries=1)
        async def fd_got(event, n: int):
            seen["n"] = n

        scripted.script = ["a", "b"]
        await fd(_make_event("x"))
        await asyncio.sleep(0.1)

        assert "n" not in seen
        # 初始 + 1 次重试后放弃（不再第三次询问）
        assert len(scripted.prompts) == 2

    async def test_timeout_ends_flow_and_clears_checkpoint(self, scripted):
        from ErisPulse.Core.storage import storage

        @command("flow_slow")
        async def fs(event):
            pass

        @fs.got("x", prompt="?", type=int)
        async def fs_got(event, x: int):
            pass

        evt = _make_event("x", user_id="timeout-user")
        scripted.script = []  # 立即超时（wait_reply 返回 None）
        await fs(evt)
        await asyncio.sleep(0.1)

        key = Conversation._checkpoint_key(evt)
        assert not storage.get(key)

    async def test_restart_resume_continues_from_checkpoint(self, scripted, monkeypatch):
        seen = {}

        @command("flow_resume")
        async def fre(event):
            pass

        @fre.got("city", prompt="城市?")
        async def fre_city(event, city: str):
            seen["city"] = city

        @fre.got("days", prompt="几天?", type=int)
        async def fre_days(event, city: str, days: int):
            seen["days"] = (city, days)

        # 第一轮：只回答第一步；第二步阻塞模拟"等待中进程重启"
        scripted.script = ["北京"]
        scripted.block_when_empty = True
        task = asyncio.create_task(fre(_make_event("x", user_id="resume-user")))
        await asyncio.sleep(0.1)
        assert seen.get("city") == "北京"

        from ErisPulse.Core.storage import storage

        key = Conversation._checkpoint_key(_make_event("x", user_id="resume-user"))
        saved = storage.get(key)
        assert isinstance(saved, dict) and saved.get("alive") is True

        # 第二轮（模拟重启后的首条消息）：自动恢复并继续收集
        scripted.script = ["3"]
        resumed = await Conversation.try_auto_resume(
            _make_event("继续", user_id="resume-user")
        )
        assert resumed is True
        await asyncio.sleep(0.1)
        assert seen.get("days") == ("北京", 3)

        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

    async def test_command_args_seed_collected(self, scripted):
        seen = {}

        @command("flow_seed")
        async def fseed(event, n: int):
            pass

        @fseed.got("label", prompt="标签?")
        async def fseed_got(event, n: int, label: str):
            seen["args"] = (n, label)

        scripted.script = ["好的"]
        await fseed(_make_event("x"), n=5)
        await asyncio.sleep(0.1)

        assert seen.get("args") == (5, "好的")


@pytest.mark.unit
class TestFlowProxyTransparency:
    """代理透明性：调用转发 / 属性转发 / 重名拒绝 / unregister 解包"""

    async def test_no_steps_is_pure_passthrough(self, scripted):
        calls = []

        @command("flow_plain")
        async def plain(event):
            calls.append(1)
            return "ok"

        assert not isinstance(plain, CommandFlow) or plain._flow_steps == []
        assert await plain(_make_event("x")) == "ok"
        assert calls == [1]

    def test_duplicate_step_name_rejected(self):
        @command("flow_dup")
        async def fdup(event):
            pass

        @fdup.got("a", prompt="1")
        async def step_a(event, a):
            pass

        with pytest.raises(ValueError):
            fdup.got("a", prompt="2")(step_a)

    def test_attribute_forwarding(self):
        @command("flow_attr")
        async def fatt(event):
            pass

        fatt.custom_marker = 42
        assert fatt.__name__ == "fatt"
        assert fatt.custom_marker == 42

    def test_unregister_unwraps_flow_proxy(self):
        @command("flow_unreg")
        async def funreg(event):
            pass

        assert command.unregister(funreg) is True

    async def test_timeout_duration_string(self, scripted):
        seen = {}

        @command("flow_dur")
        async def fdur(event):
            pass

        @fdur.got("x", prompt="?", timeout="90s")
        async def fdur_got(event, x: str):
            seen["x"] = x

        scripted.script = ["v"]
        await fdur(_make_event("x"))
        await asyncio.sleep(0.1)
        assert seen.get("x") == "v"
