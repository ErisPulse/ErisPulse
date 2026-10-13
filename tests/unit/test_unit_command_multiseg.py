"""
命令分发多段消息与健壮性修复单元测试（2.10.1）

覆盖：多 text 段参数不再丢失、mention 段夹层的命令解析、畸形段容错、
拒绝路径不再经 alt_message 整链重跑、wait_reply 不被命令触发消息重入消费、
select 同键多路聚合、条件函数异常隔离、最长前缀匹配、前导空白容忍、
mention user_id int/str 归一、get_text 段回退、converter mention 形态、
overrides 空文本语义、会话键 detail_type 区分。
"""

import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from ErisPulse.Core.Event import overrides as overrides_mod
from ErisPulse.Core.Event.command import command as command_handler
from ErisPulse.Core.Event.interaction import interaction
from ErisPulse.Core.Event.message import message as message_handler
from ErisPulse.Core.scope import scope as scope_manager
from ErisPulse.runtime.context import current_owner


@pytest.fixture(autouse=True)
def clean_state(_clean_event_command_state):
    """清理命令/事件系统状态（与 ACL 测试同口径）"""
    interaction.clear()
    overrides_mod._command.clear()
    overrides_mod.clear()
    scope_manager._data["platforms"].clear()
    scope_manager._data["bots"].clear()
    message_handler.handler.handlers.clear()
    message_handler.handler._handler_map.clear()
    yield
    interaction.clear()
    overrides_mod._command.clear()
    overrides_mod.clear()
    scope_manager._data["platforms"].clear()
    scope_manager._data["bots"].clear()
    message_handler.handler.handlers.clear()
    message_handler.handler._handler_map.clear()


def _evt(
    segments=None,
    alt_message=None,
    platform="onebot11",
    bot_id="bot_x",
    user_id="u1",
    group_id="g1",
):
    """构造消息事件；segments 缺省为单 text 段"""
    if segments is None:
        segments = [{"type": "text", "data": {"text": "/ping"}}]
    data = {
        "id": f"id_{abs(hash(str(segments)))}",
        "time": 1712345678,
        "type": "message",
        "detail_type": "group" if group_id else "private",
        "platform": platform,
        "self": {"platform": platform, "user_id": bot_id},
        "user_id": user_id,
        "message": segments,
    }
    if alt_message is not None:
        data["alt_message"] = alt_message
    if group_id:
        data["group_id"] = group_id
    return data


def _seg_text(text):
    return {"type": "text", "data": {"text": text}}


def _seg_mention(user_id):
    return {"type": "mention", "data": {"user_id": user_id}}


@pytest.mark.asyncio
async def test_multi_text_segment_args_not_lost():
    """平台把消息切成两个 text 段时，第二段参数不再丢失（2.10.1 修复）"""
    received = {}
    token = current_owner.set("MultiSegMod")
    try:

        @command_handler("kick")
        async def _kick(event):
            received["args"] = event.get_command_args()

        event = _evt(segments=[_seg_text("/kick"), _seg_text(" 吐槽怪 reason")], alt_message="")
        await command_handler._handle_message(event)
        assert received["args"] == ["吐槽怪", "reason"]
    finally:
        current_owner.reset(token)


@pytest.mark.asyncio
async def test_mention_middle_segment_command_parses():
    """/艾特 @xxx 123：mention 夹层不再导致整体丢失，text 参数照常解析"""
    received = {}
    token = current_owner.set("AtMod")
    try:

        @command_handler("艾特")
        async def _at(event):
            received["args"] = event.get_command_args()
            received["raw"] = event.get_command_raw()

        event = _evt(
            segments=[_seg_text("/艾特 "), _seg_mention("u2"), _seg_text(" 123")],
            alt_message="",
        )
        await command_handler._handle_message(event)
        # mention 段不进文本 args（段类型参数为后续版本能力），
        # 但命令命中且尾部 text 参数保留——不再"第二段整体丢失"
        assert received["args"] == ["123"]
        # raw 保留分段间距（" /艾特 " + " 123" 空格拼接），token 化不受影响
        assert "艾特" in received["raw"] and "123" in received["raw"]
    finally:
        current_owner.reset(token)


@pytest.mark.asyncio
async def test_malformed_segments_no_crash():
    """畸形段（None / 纯字符串 message / data 非 dict）不击穿命令分发"""
    received = {}
    token = current_owner.set("RobustMod")
    try:

        @command_handler("ping")
        async def _ping(event):
            received["ok"] = True

        # message 为字符串（OB11 遗留习惯）
        evt = _evt(segments="/ping hello", alt_message="")
        await command_handler._handle_message(evt)
        assert received.get("ok") is True

        # 段列表混入非 dict 元素与 data 非 dict 段
        received.clear()
        evt = _evt(
            segments=[None, "junk", _seg_text("/ping"), {"type": "text", "data": "oops"}],
            alt_message="",
        )
        await command_handler._handle_message(evt)
        assert received.get("ok") is True

        # message 缺失
        evt = _evt(segments=None, alt_message="/ping")
        evt.pop("message", None)
        received.clear()
        await command_handler._handle_message(evt)
        assert received.get("ok") is True
    finally:
        current_owner.reset(token)


@pytest.mark.asyncio
async def test_denied_command_not_rerun_via_alt():
    """命中命令被拒绝后，alt_message 不再重跑整链（拒绝回复只发一次）"""

    deny_calls = []
    token = current_owner.set("DenyMod")
    try:

        @command_handler("secure")
        async def _secure(event):
            pass

        overrides_mod.acl.set("secure", deny=["onebot11:u1"])
        event = _evt(
            segments=[_seg_text("/secure x")],
            alt_message="@bot /secure x",  # 与首文本不同，旧实现会整链重跑
        )
        with patch.object(
            command_handler, "_send_permission_denied", new=AsyncMock(side_effect=lambda e: deny_calls.append(1))
        ):
            await command_handler._handle_message(event)
        assert len(deny_calls) == 1
    finally:
        current_owner.reset(token)


@pytest.mark.asyncio
async def test_wait_reply_not_consumed_by_command_trigger():
    """命令 handler 内新注册的 wait_reply 不被同一条触发消息消费（2.10.1 修复）"""
    token = current_owner.set("WaitMod")
    try:

        @command_handler("start")
        async def _start(event):
            future = asyncio.get_running_loop().create_future()
            interaction.register(event, future, pattern="*")

        event = _evt(segments=[_seg_text("/start")], alt_message="/start")
        await command_handler._handle_message(event)

        # 命令执行后等待仍在挂起（旧实现末尾二次 resolve 会立即消费掉）
        assert interaction.counts()["waits"] == 1

        # 下一条消息正常消费等待
        reply = _evt(segments=[_seg_text("好的")], alt_message="好的", user_id="u1")
        assert await interaction.resolve(reply) is True
    finally:
        current_owner.reset(token)


@pytest.mark.asyncio
async def test_select_same_user_multi_branch():
    """select 同 user 多路不再互相取消（2.10.1 聚合等待）"""
    from ErisPulse.Core.Event.wrapper import Event

    evt = Event(_evt())
    e1 = evt.expect(pattern="同意*", user="uA")
    e2 = evt.expect(pattern="拒绝*", user="uA")  # 同 user：旧实现必互踢

    async def delayed_reply():
        await asyncio.sleep(0.05)
        await interaction.resolve(_evt(user_id="uA", alt_message="拒绝吧"))

    task = asyncio.create_task(delayed_reply())
    which, reply = await evt.select(e1, e2, timeout=2)
    await task
    assert which == 1
    assert reply.get("alt_message") == "拒绝吧"
    assert interaction.counts()["waits"] == 0


@pytest.mark.asyncio
async def test_condition_exception_isolated():
    """条件函数崩溃只影响自身命中，同优先级组的其它处理器照常执行（2.10.1 修复）"""
    from ErisPulse.Core.Event.base import BaseEventHandler

    handler_box = BaseEventHandler("notice")
    ran = []

    def _boom_condition(event):
        raise RuntimeError("condition exploded")

    handler_box.register(lambda e: ran.append("bad"), priority=5, condition=_boom_condition)
    handler_box.register(lambda e: ran.append("good"), priority=5)

    event = {"id": "x", "type": "notice", "platform": "p1", "detail_type": "notice"}
    await handler_box._process_event(event)
    assert ran == ["good"]


@pytest.mark.asyncio
async def test_longest_prefix_match():
    """重叠前缀按最长匹配：/ab 组命令不再被 /a 抢占（2.10.1 修复）"""
    received = {}
    token = current_owner.set("PrefixMod")
    try:
        command_handler._prefixes = ["/a", "/ab"]

        @command_handler("cmd")
        async def _cmd(event):
            received["args"] = event.get_command_args()

        event = _evt(segments=[_seg_text("/ab cmd hello")], alt_message="")
        await command_handler._handle_message(event)
        assert received["args"] == ["hello"]
    finally:
        current_owner.reset(token)
        command_handler._prefixes = ["/"]


@pytest.mark.asyncio
async def test_leading_whitespace_tolerated():
    """前导空白容忍：mention 段后平台分段的 " /kick x" 可命中（2.10.1 修复）"""
    received = {}
    token = current_owner.set("WsMod")
    try:

        @command_handler("kick")
        async def _kick(event):
            received["ok"] = True

        event = _evt(segments=[_seg_text(" /kick x")], alt_message="")
        await command_handler._handle_message(event)
        assert received.get("ok") is True
    finally:
        current_owner.reset(token)


@pytest.mark.asyncio
async def test_must_at_bot_int_str_normalized():
    """must_at_bot：mention user_id 为平台原生 int、self.user_id 为 str 时仍命中（2.10.1 修复）"""
    received = {}
    token = current_owner.set("AtBotMod")
    original_must_at_bot = command_handler.must_at_bot
    command_handler.must_at_bot = True
    try:

        @command_handler("kick")
        async def _kick(event):
            received["ok"] = True

        event = _evt(
            segments=[
                _seg_mention(10001),  # int 形态
                _seg_text(" /kick x"),
            ],
            alt_message="",
            bot_id="10001",  # self.user_id 为 str
        )
        await command_handler._handle_message(event)
        assert received.get("ok") is True
    finally:
        command_handler.must_at_bot = original_must_at_bot
        current_owner.reset(token)


def test_get_text_segment_fallback():
    """无 alt_message 时 get_text 回退为 text 段拼接（2.10.1 修复）"""
    from ErisPulse.Core.Event.wrapper import Event

    event = Event(_evt(segments=[_seg_text("你好"), _seg_text("世界")], alt_message=None))
    # 回退口径与 text_match.extract_text 一致（text 段无分隔符拼接）
    assert event.get_text() == "你好世界"


def test_converter_at_produces_mention():
    """converter.at() 产出 OB12 规范 mention 段（2.10.1 修复，保留 at 别名）"""
    from ErisPulse.Core.Bases import BaseConverter

    conv = BaseConverter(platform="demo")
    assert conv.at("123") == {"type": "mention", "data": {"user_id": "123"}}
    assert conv.mention("123") == {"type": "mention", "data": {"user_id": "123"}}


def test_overrides_message_pattern_empty_text_no_match():
    """overrides pattern 条件：message 事件空文本不命中（不再绕过 pattern）"""
    overrides_mod.message.set("CondMod", pattern="签到*")
    cond = overrides_mod.condition_for("message", "CondMod")
    assert cond is not None
    image_only = {
        "type": "message",
        "detail_type": "group",
        "message": [{"type": "image", "data": {"file": "x.png"}}],
    }
    assert cond(image_only) is False
    # 命中 pattern 的文本事件照常放行；清理由 clean_state fixture 统一负责
    matched = {
        "type": "message",
        "detail_type": "group",
        "message": [{"type": "text", "data": {"text": "签到打卡"}}],
    }
    assert cond(matched) is True


def test_session_key_includes_detail_type():
    """会话级键并入 detail_type：user 与 group 同数值 id 不再互相命中（2.10.1 修复）"""
    base = {
        "platform": "p1",
        "self": {"user_id": "bot1"},
        "user_id": "77",
        "target_id": "888",
    }
    private_evt = {**base, "detail_type": "private"}
    group_evt = {**base, "detail_type": "group"}
    assert interaction.make_session_key(private_evt) != interaction.make_session_key(group_evt)


def test_builder_build_deepcopy_and_empty_args():
    """build() 深拷贝（改产物不污染 builder）；mention/reply 空参 fail-fast"""
    from ErisPulse.Core.Event.message_builder import MessageBuilder

    builder = MessageBuilder().text("hi")
    built = builder.build()
    built[0]["data"]["text"] = "mutated"
    assert builder.build()[0]["data"]["text"] == "hi"

    with pytest.raises(ValueError):
        MessageBuilder().mention("")
    with pytest.raises(ValueError):
        MessageBuilder().reply("")


@pytest.mark.asyncio
async def test_cmdpass_works_without_alt_message():
    """等待期间命令穿透：仅 message 段（无 alt_message）的事件也判定命令（2.10.1 修复）"""
    token = current_owner.set("CmdPassMod")
    try:

        @command_handler("cancel")
        async def _cancel(event):
            pass

        future = asyncio.get_running_loop().create_future()
        interaction.register(_evt(), future, pattern="*")

        # 已注册命令 → 穿透放行给命令分发器（等待不消费）
        cmd_event = _evt(segments=[_seg_text("/cancel")], alt_message=None, user_id="u1")
        assert await interaction.resolve(cmd_event) is False
        assert interaction.counts()["waits"] == 1

        # 普通文本照常命中等待
        plain = _evt(segments=[_seg_text("普通回复")], alt_message=None, user_id="u1")
        assert await interaction.resolve(plain) is True
    finally:
        current_owner.reset(token)
