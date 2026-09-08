"""
Conversation 对话检查点单元测试

测试自动检查点（goto 自动保存）、target 维度存储键、旧格式迁移、
TTL 过期、重启自动恢复（register_resume_handler / try_auto_resume）
与终态自动清理。
"""

import asyncio
import importlib
import os
import tempfile
import time

import pytest

from ErisPulse.Core.Event.wrapper import Conversation, Event, _conversation_resume_handlers
from ErisPulse.Core.storage import StorageManager

# importlib.import_module 返回真实子模块（Core.storage 属性被 StorageManager 单例遮蔽）
_storage_module = importlib.import_module("ErisPulse.Core.storage")


@pytest.fixture
def temp_sm(monkeypatch):
    """用临时数据库替换全局 storage（Conversation 内部为运行时导入）"""
    StorageManager._instance = None
    with tempfile.NamedTemporaryFile(mode="w", suffix=".db", delete=False) as f:
        temp_path = f.name
    try:
        manager = StorageManager.__new__(StorageManager)
        manager.db_path = temp_path
        manager._init_db()
        manager._initialized = True
        monkeypatch.setattr(_storage_module, "storage", manager)
        yield manager
    finally:
        StorageManager._instance = None
        for ext in ["", "-wal", "-shm"]:
            fp = temp_path + ext
            if os.path.exists(fp):
                try:
                    os.remove(fp)
                except PermissionError:
                    pass


@pytest.fixture(autouse=True)
def clean_resume_handlers():
    from ErisPulse.Core.Event.interaction import interaction

    saved = list(_conversation_resume_handlers)
    _conversation_resume_handlers.clear()
    interaction.clear()  # resume 会话接管会留下租约，逐用例清理
    yield
    _conversation_resume_handlers.clear()
    _conversation_resume_handlers.extend(saved)
    interaction.clear()


def _evt(user_id="u1", group_id="g1", **extra):
    data = {
        "id": f"evt_{user_id}",
        "time": 1712345678,
        "type": "message",
        "detail_type": "group" if group_id else "private",
        "platform": "onebot11",
        "self": {"platform": "onebot11", "user_id": "bot_x"},
        "user_id": user_id,
        "message": [{"type": "text", "data": {"text": "hello"}}],
        "alt_message": "hello",
    }
    if group_id:
        data["group_id"] = group_id
    data.update(extra)
    return Event(data)


def _conv_with_branch(event, name="menu"):
    conv = event.conversation()
    conv._alive = True
    conv._current_branch = name

    @conv.branch(name)
    async def _branch(c, e): ...

    return conv


# ==================== 键构造 ====================


class TestCheckpointKey:
    def test_key_contains_target(self):
        key = Conversation._checkpoint_key(_evt())
        assert key == "conversation:onebot11:u1:g1"

    def test_key_private(self):
        assert Conversation._checkpoint_key(_evt(group_id=None)) == "conversation:onebot11:u1:u1"


# ==================== 自动检查点 ====================


class TestAutoCheckpoint:
    @pytest.mark.asyncio
    async def test_goto_saves_checkpoint(self, temp_sm):
        evt = _evt()
        conv = _conv_with_branch(evt)
        conv.context["step"] = 2

        conv.goto("menu", evt)
        await asyncio.sleep(0.05)

        data = temp_sm.get(Conversation._checkpoint_key(evt))
        assert isinstance(data, dict)
        assert data["branch"] == "menu"
        assert data["context"] == {"step": 2}
        assert data["alive"] is True
        assert isinstance(data["saved_at"], float)

    @pytest.mark.asyncio
    async def test_resume_restores_state(self, temp_sm):
        evt = _evt()
        conv = _conv_with_branch(evt)
        conv.context["q"] = "答案"
        await conv.save()

        conv2 = _conv_with_branch(_evt())
        assert await conv2.resume() is True
        assert conv2.get_current_branch() == "menu"
        assert conv2.context == {"q": "答案"}
        assert conv2.is_active is True

    @pytest.mark.asyncio
    async def test_resume_acquires_session_lease(self, temp_sm):
        """恢复即接管：resume 成功后对话持有会话租约"""
        from ErisPulse.Core.Event.interaction import interaction
        from ErisPulse.runtime.context import current_owner

        evt = _evt()
        conv = _conv_with_branch(evt)
        await conv.save()

        conv2 = _conv_with_branch(_evt())
        token = current_owner.set("MyModule")
        try:
            assert await conv2.resume() is True
        finally:
            current_owner.reset(token)
        assert interaction.get_owner_of(_evt()) == "MyModule"  # 会话已被接管

    @pytest.mark.asyncio
    async def test_resume_abandoned_when_session_occupied(self, temp_sm):
        """会话被其他模块占用时放弃恢复"""
        from ErisPulse.Core.Event.interaction import interaction

        evt = _evt()
        conv = _conv_with_branch(evt)
        await conv.save()

        # 其他模块先占用会话
        assert interaction.acquire(_evt(), owner="Other") is not None

        conv2 = _conv_with_branch(_evt())
        assert await conv2.resume() is False

    @pytest.mark.asyncio
    async def test_resume_brings_recent_history(self, temp_sm):
        """恢复时从收件箱带回最近消息"""
        from ErisPulse.Core import transcript

        evt = _evt()
        transcript._table_ready = False
        transcript.append(evt, "user", "之前的消息", event_id="e1")

        conv = _conv_with_branch(evt)
        await conv.save()

        conv2 = _conv_with_branch(_evt())
        assert await conv2.resume() is True
        assert conv2.recent_history and conv2.recent_history[-1]["text"] == "之前的消息"

    @pytest.mark.asyncio
    async def test_target_isolation(self, temp_sm):
        conv_a = _conv_with_branch(_evt(group_id="g1"))
        conv_a.context["which"] = "g1"
        await conv_a.save()

        conv_b = _conv_with_branch(_evt(group_id="g2"))
        assert await conv_b.resume() is False

    @pytest.mark.asyncio
    async def test_legacy_key_migrated(self, temp_sm):
        evt = _evt(user_id="legacy")
        temp_sm.set("conversation:onebot11:legacy", {
            "branch": "menu",
            "context": {"old": True},
            "alive": True,
            "timeout": 60,
        })

        conv = _conv_with_branch(_evt(user_id="legacy"))
        assert await conv.resume() is True
        assert conv.context == {"old": True}
        # 旧键已删除，数据迁移至新键
        assert temp_sm.get("conversation:onebot11:legacy") is None
        assert temp_sm.get(Conversation._checkpoint_key(_evt(user_id="legacy"))) is not None

    @pytest.mark.asyncio
    async def test_expired_checkpoint_rejected(self, temp_sm):
        evt = _evt(user_id="stale")
        temp_sm.set(Conversation._checkpoint_key(evt), {
            "version": 2,
            "branch": "menu",
            "context": {},
            "alive": True,
            "timeout": 60,
            "saved_at": time.time() - 100000,
        })

        conv = _conv_with_branch(evt)
        assert await conv.resume() is False
        # 过期存档被清理
        assert temp_sm.get(Conversation._checkpoint_key(evt)) is None

    @pytest.mark.asyncio
    async def test_stop_clears_checkpoint(self, temp_sm):
        evt = _evt()
        conv = _conv_with_branch(evt)
        await conv.save()
        assert temp_sm.get(Conversation._checkpoint_key(evt)) is not None

        conv.stop()
        await asyncio.sleep(0.05)
        assert temp_sm.get(Conversation._checkpoint_key(evt)) is None

    @pytest.mark.asyncio
    async def test_wait_timeout_clears_checkpoint(self, temp_sm):
        evt = _evt()
        conv = _conv_with_branch(evt)
        await conv.save()

        # wait() 在非活跃对话上返回 None 不会触发清理；模拟活跃对话等待超时路径：
        # wait() 内部调 event.wait_reply —— 这里直接验证 collect/wait 失活清理逻辑
        conv._alive = True
        await conv._checkpoint(save=False)
        assert temp_sm.get(Conversation._checkpoint_key(evt)) is None


# ==================== 重启自动恢复 ====================


class TestAutoResume:
    @pytest.mark.asyncio
    async def test_no_handlers_is_noop(self, temp_sm):
        assert await Conversation.try_auto_resume(_evt()) is False

    @pytest.mark.asyncio
    async def test_auto_resume_consumes_and_gotos(self, temp_sm):
        evt = _evt()
        conv = _conv_with_branch(evt)
        conv.context["resumed_with"] = "ctx"
        await conv.save()

        built = {}

        @Conversation.register_resume_handler()
        def factory(e):
            c = _conv_with_branch(e)
            built["conv"] = c
            return c

        target = _evt()
        assert await Conversation.try_auto_resume(target) is True
        assert target.get("_processed") is True
        assert built["conv"].get_current_branch() == "menu"
        assert built["conv"].context == {"resumed_with": "ctx"}

    @pytest.mark.asyncio
    async def test_platform_filter(self, temp_sm):
        evt = _evt()
        conv = _conv_with_branch(evt)
        await conv.save()

        @Conversation.register_resume_handler(platform="telegram")
        def factory(e):
            return _conv_with_branch(e)

        assert await Conversation.try_auto_resume(_evt()) is False

    @pytest.mark.asyncio
    async def test_factory_none_is_skipped(self, temp_sm):
        evt = _evt()
        conv = _conv_with_branch(evt)
        await conv.save()

        @Conversation.register_resume_handler()
        def none_factory(e):
            return None

        assert await Conversation.try_auto_resume(_evt()) is False

    @pytest.mark.asyncio
    async def test_expired_checkpoint_not_resumed(self, temp_sm):
        evt = _evt(user_id="old")
        temp_sm.set(Conversation._checkpoint_key(_evt(user_id="old")), {
            "version": 2,
            "branch": "menu",
            "context": {},
            "alive": True,
            "timeout": 60,
            "saved_at": time.time() - 100000,
        })

        @Conversation.register_resume_handler()
        def factory(e):
            return _conv_with_branch(e)

        assert await Conversation.try_auto_resume(_evt(user_id="old")) is False
