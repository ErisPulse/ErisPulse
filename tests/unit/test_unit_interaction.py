"""
交互会话管理器单元测试

测试 InteractionManager 的三索引（key / owner / platform）、回复命中判定链
（pattern / regex / validator / 权限复查）、冲突取消、互斥租约，
以及 trace-id 与消息事务 ContextVar 的基础行为。
"""

import asyncio

import pytest

from ErisPulse.Core.Bases.errors import ErisPulseError, InteractionError
from ErisPulse.Core.Event.interaction import (
    InteractionCancelled,
    InteractionLease,
    SessionOccupiedError,
    interaction,
)
from ErisPulse.Core.scope import scope as scope_manager


@pytest.fixture(autouse=True)
def clean_interaction():
    interaction.clear()
    scope_manager._data["identity"] = {"adapters": {}, "bots": {}, "sessions": {}, "users": {}}
    scope_manager._data["platforms"] = {}
    scope_manager._data["bots"] = {}
    scope_manager._data["sessions"] = {}
    scope_manager._data["actions"] = {}
    scope_manager._invalidate_cache()
    yield
    interaction.clear()
    scope_manager._invalidate_cache()


def _evt(user_id="u1", platform="onebot11", group_id=None, **extra):
    data = {
        "id": f"evt_{user_id}",
        "time": 1712345678,
        "type": "message",
        "detail_type": "group" if group_id else "private",
        "platform": platform,
        "self": {"platform": platform, "user_id": "bot_x"},
        "user_id": user_id,
        "message": [{"type": "text", "data": {"text": "hello"}}],
        "alt_message": "hello",
    }
    if group_id:
        data["group_id"] = group_id
    data.update(extra)
    return data


# ==================== 会话键与注册 ====================


class TestMakeKey:
    def test_private_key(self):
        key = interaction.make_key(_evt())
        assert key == "onebot11:bot_x:u1:u1"

    def test_group_key(self):
        key = interaction.make_key(_evt(group_id="g9"))
        assert key == "onebot11:bot_x:u1:g9"


class TestRegisterResolve:
    @pytest.mark.asyncio
    async def test_resolve_hit(self):
        loop = asyncio.get_running_loop()
        future = loop.create_future()
        interaction.register(_evt(), future)

        reply = _evt(alt_message="回答")
        assert await interaction.resolve(reply) is True
        assert future.done() and future.result() is reply
        assert interaction.counts()["waits"] == 0

    @pytest.mark.asyncio
    async def test_resolve_miss_different_user(self):
        loop = asyncio.get_running_loop()
        future = loop.create_future()
        interaction.register(_evt(), future)

        assert await interaction.resolve(_evt(user_id="other")) is False
        assert not future.done()

    @pytest.mark.asyncio
    async def test_pattern_not_matched_keeps_waiting(self):
        loop = asyncio.get_running_loop()
        future = loop.create_future()
        interaction.register(_evt(), future, pattern="*数字*")

        assert await interaction.resolve(_evt(alt_message="随便说")) is False
        assert interaction.counts()["waits"] == 1
        assert not future.done()

        assert await interaction.resolve(_evt(alt_message="这是数字")) is True
        assert future.done()

    @pytest.mark.asyncio
    async def test_validator_failure_keeps_waiting(self):
        loop = asyncio.get_running_loop()
        future = loop.create_future()
        interaction.register(_evt(), future, validator=lambda e: e.get("alt_message") == "ok")

        assert await interaction.resolve(_evt(alt_message="bad")) is False
        assert interaction.counts()["waits"] == 1

    @pytest.mark.asyncio
    async def test_validator_exception_treated_as_failure(self):
        loop = asyncio.get_running_loop()
        future = loop.create_future()

        def _bad_validator(event):
            raise RuntimeError("boom")

        interaction.register(_evt(), future, validator=_bad_validator)
        assert await interaction.resolve(_evt()) is False
        assert interaction.counts()["waits"] == 1

    @pytest.mark.asyncio
    async def test_resolve_marks_processed(self):
        from ErisPulse.Core.Event.wrapper import Event

        loop = asyncio.get_running_loop()
        future = loop.create_future()
        interaction.register(_evt(), future)

        reply = Event(_evt())
        await interaction.resolve(reply)
        assert reply.get("_processed") is True


# ==================== 冲突与取消 ====================


class TestConflictAndCancel:
    @pytest.mark.asyncio
    async def test_conflict_cancels_old_wait(self):
        loop = asyncio.get_running_loop()
        old = loop.create_future()
        new = loop.create_future()

        interaction.register(_evt(), old)
        interaction.register(_evt(), new)

        assert old.done() and not old.cancelled()
        exc = old.exception()
        assert isinstance(exc, InteractionCancelled)
        assert exc.reason == "conflict"
        assert await interaction.resolve(_evt()) is True
        assert new.done()

    @pytest.mark.asyncio
    async def test_cancel_by_owner(self):
        loop = asyncio.get_running_loop()
        future = loop.create_future()
        with_owner = _evt()
        interaction.register(with_owner, future, owner="ModuleA")

        assert interaction.cancel_by_owner("ModuleA") == 1
        assert future.done()
        assert future.exception().reason == "owner_unload"
        assert interaction.counts()["waits"] == 0

    @pytest.mark.asyncio
    async def test_cancel_by_owner_keeps_others(self):
        loop = asyncio.get_running_loop()
        fut_a = loop.create_future()
        fut_b = loop.create_future()
        interaction.register(_evt(), fut_a, owner="A")
        interaction.register(_evt(user_id="u2"), fut_b, owner="B")

        assert interaction.cancel_by_owner("A") == 1
        assert not fut_b.done()
        assert interaction.counts()["waits"] == 1

    @pytest.mark.asyncio
    async def test_cancel_by_platform(self):
        loop = asyncio.get_running_loop()
        future = loop.create_future()
        interaction.register(_evt(platform="qq"), future)

        assert interaction.cancel_by_platform("qq") == 1
        assert future.done() and future.exception().reason == "platform_stop"

    @pytest.mark.asyncio
    async def test_clear_cancels_all(self):
        loop = asyncio.get_running_loop()
        futures = [loop.create_future() for _ in range(3)]
        for i, f in enumerate(futures):
            interaction.register(_evt(user_id=f"u{i}"), f)

        assert interaction.clear() == 3
        assert interaction.counts() == {"waits": 0, "leases": 0, "timers": 0, "owners": {}}
        for f in futures:
            assert f.done() and f.exception().reason == "cleared"


# ==================== 权限复查 ====================


class TestPermissionRecheck:
    @pytest.mark.asyncio
    async def test_identity_revoked_terminates_wait(self):
        scope_manager._data["identity"]["users"] = {"onebot11": {"u1": {"deny": True}}}
        scope_manager._invalidate_cache() if hasattr(scope_manager, "_invalidate_cache") else None

        loop = asyncio.get_running_loop()
        future = loop.create_future()
        interaction.register(_evt(), future, owner="ModuleA")

        hit = await interaction.resolve(_evt())
        assert hit is False
        assert future.done()
        assert future.exception().reason == "revoked"
        assert interaction.counts()["waits"] == 0

    @pytest.mark.asyncio
    async def test_module_unbound_terminates_wait(self):
        scope_manager._data["platforms"] = {"onebot11": {"modules": ["Other*"], "merge": True}}
        if hasattr(scope_manager, "_invalidate_cache"):
            scope_manager._invalidate_cache()

        loop = asyncio.get_running_loop()
        future = loop.create_future()
        interaction.register(_evt(), future, owner="ModuleA")

        assert await interaction.resolve(_evt()) is False
        assert future.done() and future.exception().reason == "revoked"

    @pytest.mark.asyncio
    async def test_permission_ok_when_no_binding(self):
        loop = asyncio.get_running_loop()
        future = loop.create_future()
        interaction.register(_evt(), future, owner="ModuleA")

        assert await interaction.resolve(_evt()) is True
        assert future.done()


# ==================== 互斥租约 ====================


class TestLease:
    def test_acquire_and_release(self):
        lease = interaction.acquire(_evt(), owner="A")
        assert isinstance(lease, InteractionLease)
        assert interaction.get_owner_of(_evt()) == "A"

        assert interaction.release(lease.key, owner="B") is False
        assert lease.release() is True
        assert interaction.get_owner_of(_evt()) is None

    def test_acquire_denied_when_occupied(self):
        assert interaction.acquire(_evt(), owner="A") is not None
        assert interaction.acquire(_evt(), owner="B") is None
        assert interaction.get_owner_of(_evt()) == "A"

    def test_lease_denied_when_wait_pending(self):
        loop = asyncio.new_event_loop()
        try:
            future = loop.create_future()
            interaction.register(_evt(), future, owner="Waiter")

            assert interaction.acquire(_evt(), owner="A") is None
            assert interaction.get_owner_of(_evt()) == "Waiter"
        finally:
            loop.close()

    def test_lease_expiry_lazy(self):
        lease = interaction.acquire(_evt(), owner="A", ttl=-1.0)
        assert lease.expired is True
        assert interaction.get_owner_of(_evt()) is None
        # 过期后可重新获取
        assert interaction.acquire(_evt(), owner="B") is not None

    def test_lease_renew(self):
        lease = interaction.acquire(_evt(), owner="A", ttl=1.0)
        assert lease.renew(100.0) is True
        assert not lease.expired

    def test_hold_context_manager(self):
        with interaction.hold(_evt(), owner="A") as lease:
            assert interaction.get_owner_of(_evt()) == "A"
        assert interaction.get_owner_of(_evt()) is None

    def test_hold_raises_when_occupied(self):
        interaction.acquire(_evt(), owner="A")
        with pytest.raises(SessionOccupiedError):
            with interaction.hold(_evt(), owner="B"):
                pass
        assert interaction.get_owner_of(_evt()) == "A"


# ==================== 会话定时器 ====================


class TestReminders:
    @pytest.mark.asyncio
    async def test_fires_callback(self):
        fired = []

        async def action():
            fired.append("x")

        reminder = interaction.add_reminder(_evt(), 0.05, action)
        assert reminder is not None
        await asyncio.sleep(0.15)
        assert fired == ["x"]
        assert reminder.expired

    @pytest.mark.asyncio
    async def test_reply_cancels_remind(self):
        loop = asyncio.get_running_loop()
        future = loop.create_future()
        interaction.register(_evt(), future)
        fired = []
        reminder = interaction.add_reminder(_evt(), 5, lambda: fired.append(1), cancellable_by_reply=True)

        assert await interaction.resolve(_evt()) is True
        assert reminder.cancel() is False  # 已被回复自动取消
        await asyncio.sleep(0.05)
        assert fired == []
        assert interaction.counts()["timers"] == 0

    @pytest.mark.asyncio
    async def test_escalate_not_cancelled_by_reply(self):
        loop = asyncio.get_running_loop()
        future = loop.create_future()
        interaction.register(_evt(), future)
        fired = []
        reminder = interaction.add_reminder(_evt(), 0.05, lambda: fired.append(1), cancellable_by_reply=False)

        await interaction.resolve(_evt())  # 回复命中
        assert not reminder.expired  # escalate 不受影响
        await asyncio.sleep(0.15)
        assert fired == [1]

    @pytest.mark.asyncio
    async def test_manual_cancel(self):
        fired = []
        reminder = interaction.add_reminder(_evt(), 5, lambda: fired.append(1))
        assert reminder.cancel() is True
        await asyncio.sleep(0.05)
        assert fired == []

    @pytest.mark.asyncio
    async def test_session_limit(self):
        for _ in range(5):
            assert interaction.add_reminder(_evt(), 60, lambda: None) is not None
        # 第 6 个被拒
        assert interaction.add_reminder(_evt(), 60, lambda: None) is None

    @pytest.mark.asyncio
    async def test_cancel_by_owner(self):
        fired = []
        reminder = interaction.add_reminder(_evt(), 5, lambda: fired.append(1), owner="ModuleA")
        assert interaction.cancel_by_owner("ModuleA") == 1
        await asyncio.sleep(0.05)
        assert fired == []
        assert reminder.expired is True  # 已终结（被取消，未执行）
        assert reminder.cancel() is False  # 二次取消返回 False

    @pytest.mark.asyncio
    async def test_owner_attributed_on_fire(self):
        from ErisPulse.runtime.context import get_current_owner

        seen = {}

        async def action():
            seen["owner"] = get_current_owner()

        interaction.add_reminder(_evt(), 0.05, action, owner="ModuleA")
        await asyncio.sleep(0.15)
        assert seen["owner"] == "ModuleA"


# ==================== 会话级等待与多路 select ====================


class TestSessionScope:
    @pytest.mark.asyncio
    async def test_any_member_can_reply(self):
        loop = asyncio.get_running_loop()
        future = loop.create_future()
        # 会话级等待（群 g1）：u1 发起，同群任何成员的回复均可命中
        interaction.register(_evt(group_id="g1"), future, session_scope=True)

        other = _evt(user_id="u2", group_id="g1", alt_message="我来答")
        assert await interaction.resolve(other) is True
        assert future.done() and future.result() is other

    @pytest.mark.asyncio
    async def test_session_and_user_keys_coexist(self):
        loop = asyncio.get_running_loop()
        user_fut = loop.create_future()
        session_fut = loop.create_future()
        interaction.register(_evt(group_id="g1"), user_fut, owner="A")
        interaction.register(_evt(group_id="g1"), session_fut, session_scope=True, owner="B")
        assert interaction.counts()["waits"] == 2

        # 群成员 u2 回复命中会话级等待；u1 的精确等待不受影响
        assert await interaction.resolve(_evt(user_id="u2", group_id="g1")) is True
        assert session_fut.done() and not user_fut.done()


class TestSelect:
    @pytest.mark.asyncio
    async def test_first_hit_wins(self):
        from ErisPulse.Core.Event.wrapper import Event

        evt = Event(_evt())
        e1 = evt.expect(pattern="同意*", user="uA")
        e2 = evt.expect(pattern="拒绝*", user="uB")

        async def delayed_reply():
            await asyncio.sleep(0.05)
            await interaction.resolve(_evt(user_id="uB", alt_message="拒绝吧"))

        task = asyncio.create_task(delayed_reply())
        which, reply = await evt.select(e1, e2, timeout=2)
        await task
        assert which == 1
        assert reply.get("alt_message") == "拒绝吧"
        assert interaction.counts()["waits"] == 0

    @pytest.mark.asyncio
    async def test_timeout_returns_none(self):
        from ErisPulse.Core.Event.wrapper import Event

        evt = Event(_evt())
        which, reply = await evt.select(evt.expect(pattern="*"), timeout=0.05)
        assert which is None and reply is None
        assert interaction.counts()["waits"] == 0

    @pytest.mark.asyncio
    async def test_empty_expectations_raises(self):
        from ErisPulse.Core.Event.wrapper import Event

        evt = Event(_evt())
        with pytest.raises(ValueError):
            await evt.select()


# ==================== 异常体系与 ContextVar ====================


class TestExceptionHierarchy:
    def test_interaction_cancelled_hierarchy(self):
        assert issubclass(InteractionCancelled, InteractionError)
        assert issubclass(InteractionError, ErisPulseError)

    def test_session_occupied_hierarchy(self):
        assert issubclass(SessionOccupiedError, InteractionError)


class TestContextVars:
    def test_trace_id_default_none(self):
        from ErisPulse.runtime.context import get_current_trace_id

        assert get_current_trace_id() is None

    def test_trace_id_set_and_reset(self):
        from ErisPulse.runtime.context import current_trace_id, get_current_trace_id

        token = current_trace_id.set("t-1")
        try:
            assert get_current_trace_id() == "t-1"
        finally:
            current_trace_id.reset(token)
        assert get_current_trace_id() is None

    def test_send_receipts_default_none(self):
        from ErisPulse.runtime.context import get_send_receipts

        assert get_send_receipts() is None

    def test_send_receipts_in_tx(self):
        from ErisPulse.Core.Event.wrapper import _MessageTx
        from ErisPulse.runtime.context import get_send_receipts

        async def main():
            async with _MessageTx():
                receipts = get_send_receipts()
                assert receipts == []
                receipts.append({"platform": "p", "bot_id": "b", "message_id": "m1", "trace_id": None})
            assert get_send_receipts() is None

        asyncio.run(main())

    def test_message_tx_rollback_skips_missing_platform(self):
        from ErisPulse.Core.Event.wrapper import _rollback_receipts

        receipts = [{"platform": "no_such_platform", "bot_id": "b", "message_id": "m", "trace_id": None}]
        asyncio.run(_rollback_receipts(receipts))
