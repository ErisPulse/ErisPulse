"""
事件链路解耦（认领 vs 阻断）单元测试

验证 done / mark_processed 的认领与阻断解耦语义，以及 command 分发后的认领+阻断默认行为。
"""

import pytest

from ErisPulse.Core.Event.base import BaseEventHandler
from ErisPulse.Core.Event.wrapper import Event


def _make_event(**overrides):
    """构造基础消息事件"""
    data = {
        "type": "message",
        "platform": "test",
        "user_id": "u1",
        "self": {"user_id": "bot"},
    }
    data.update(overrides)
    return data


class TestPropagationDecoupling:
    """done(claim/stop) / mark_processed 解耦测试"""

    @pytest.fixture
    def handler(self):
        h = BaseEventHandler("message", "test_propagation")
        h.handlers.clear()
        h._handler_map.clear()
        yield h
        h._clear_handlers()

    @pytest.mark.asyncio
    async def test_mark_processed_default_blocks(self, handler):
        """mark_processed() 默认阻断传播（向后兼容）"""
        order = []

        async def high(event):
            order.append("high")
            event.mark_processed()

        async def low(event):
            order.append("low")

        handler.register(high, priority=10)
        handler.register(low, priority=1)

        await handler._process_event(_make_event())
        assert order == ["high"]

    @pytest.mark.asyncio
    async def test_mark_processed_no_block_continues(self, handler):
        """mark_processed(stop=False) 仅认领，低优先级继续执行"""
        order = []

        async def high(event):
            order.append("high")
            event.mark_processed(stop=False)

        async def low(event):
            order.append("low")

        handler.register(high, priority=10)
        handler.register(low, priority=1)

        await handler._process_event(_make_event())
        assert order == ["high", "low"]

    @pytest.mark.asyncio
    async def test_done_claim_false_blocks_only(self, handler):
        """done(claim=False) 仅阻断，不标记 _processed"""
        checks = {}

        async def high(event):
            event.done(claim=False)
            checks["processed"] = event.is_processed()
            checks["stopped"] = event.is_stopped()

        ran_low = []

        async def low(event):
            ran_low.append(True)

        handler.register(high, priority=10)
        handler.register(low, priority=1)

        await handler._process_event(_make_event())
        assert checks == {"processed": False, "stopped": True}
        assert ran_low == []

    @pytest.mark.asyncio
    async def test_parallel_propagation_merge(self, handler):
        """同优先级并行：任一 handler 阻断则合并后阻断低优先级"""
        ran_low = []

        async def handler_a(event):
            event.done(claim=False)

        async def handler_b(event):
            pass  # 不阻断

        async def low(event):
            ran_low.append(True)

        handler.register(handler_a, priority=10)
        handler.register(handler_b, priority=10)
        handler.register(low, priority=1)

        await handler._process_event(_make_event())
        assert ran_low == []

    @pytest.mark.asyncio
    async def test_no_propagation_all_priorities_run(self, handler):
        """无阻断时所有优先级都执行"""
        order = []

        async def high(event):
            order.append("high")

        async def low(event):
            order.append("low")

        handler.register(high, priority=10)
        handler.register(low, priority=1)

        await handler._process_event(_make_event())
        assert order == ["high", "low"]


class TestCommandDispatchClaim:
    """command 分发后的认领与阻断（无外部 block 配置，固定默认行为）"""

    @pytest.fixture(autouse=True)
    def setup_command(self):
        from ErisPulse.Core.Event import command

        command.commands.clear()
        command.aliases.clear()
        command.groups.clear()
        command.permissions.clear()
        command._waiting_replies.clear()
        # 确保解析参数可预测（不依赖外部配置加载）
        command.prefix = "/"
        command._prefixes = ["/"]
        command.case_sensitive = True
        command.allow_space_prefix = False
        command.must_at_bot = False
        yield
        command._clear_commands()

    @pytest.mark.asyncio
    async def test_command_matched_claims_and_blocks(self):
        """命令匹配后默认 mark_processed()（认领+阻断）"""
        from ErisPulse.Core.Event import command

        @command("testcmd")
        async def cmd(event):
            pass

        event = Event(
            _make_event(
                message=[{"type": "text", "data": {"text": "/testcmd"}}],
                alt_message="/testcmd",
            )
        )

        await command._handle_message(event)

        assert event.is_processed()
        assert event.is_stopped()


class TestDoneModes:
    """done(claim/stop) 参数组合测试"""

    def test_done_both(self):
        """done() 默认：认领 + 阻断"""
        evt = Event(_make_event())
        evt.done()
        assert evt.is_processed()
        assert evt.is_stopped()

    def test_done_stop_false_claim_only(self):
        """done(stop=False)：仅认领，不阻断"""
        evt = Event(_make_event())
        evt.done(stop=False)
        assert evt.is_processed()
        assert not evt.is_stopped()

    def test_done_claim_false_block_only(self):
        """done(claim=False)：仅阻断，不认领"""
        evt = Event(_make_event())
        evt.done(claim=False)
        assert not evt.is_processed()
        assert evt.is_stopped()

    def test_mark_processed_default(self):
        """mark_processed() 默认认领+阻断"""
        evt = Event(_make_event())
        evt.mark_processed()
        assert evt.is_processed()
        assert evt.is_stopped()

    def test_done_is_alias_of_mark_processed(self):
        """done 是 mark_processed 的别名，参数完全等价"""
        evt = Event(_make_event())
        evt.done(stop=False)
        assert evt.is_processed()
        assert not evt.is_stopped()

        evt2 = Event(_make_event())
        evt2.done(claim=False)
        assert not evt2.is_processed()
        assert evt2.is_stopped()

        evt3 = Event(_make_event())
        evt3.done()
        assert evt3.is_processed()
        assert evt3.is_stopped()

    def test_is_stopped_query(self):
        """is_stopped() 查询阻断状态，对应 done(stop=True)"""
        evt = Event(_make_event())
        assert not evt.is_stopped()

        evt.done()
        assert evt.is_stopped()

        evt2 = Event(_make_event())
        evt2.done(stop=False)
        assert not evt2.is_stopped()
        assert evt2.is_processed()
