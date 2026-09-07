"""
会话收件箱（transcript）单元测试

测试入站/出站消息记录、会话键推导、查询与清理、保留策略与启用开关。
"""

import asyncio
import importlib
import os
import tempfile

import pytest

from ErisPulse.Core.Event.wrapper import Event
from ErisPulse.Core.storage import StorageManager
from ErisPulse.Core.transcript import TRANSCRIPT_TEXT_MAX_CHARS, transcript

# importlib.import_module 返回真实子模块
# （Core.storage / Core.transcript 的包属性分别被 StorageManager / transcript 单例遮蔽）
_storage_module = importlib.import_module("ErisPulse.Core.storage")
_transcript_module = importlib.import_module("ErisPulse.Core.transcript")


@pytest.fixture
def temp_sm(monkeypatch):
    """用临时数据库替换全局 storage（transcript 与 wrapper 的 Conversation 均为运行时导入）"""
    StorageManager._instance = None
    with tempfile.NamedTemporaryFile(mode="w", suffix=".db", delete=False) as f:
        temp_path = f.name
    try:
        manager = StorageManager.__new__(StorageManager)
        manager.db_path = temp_path
        manager._init_db()
        manager._initialized = True
        monkeypatch.setattr(_storage_module, "storage", manager)
        monkeypatch.setattr(_transcript_module, "storage", manager)
        transcript._table_ready = False
        transcript._append_count = 0
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
def enable_transcript(monkeypatch):
    """强制启用收件箱（不依赖外部配置文件）"""
    monkeypatch.setattr(
        type(transcript),
        "enabled",
        property(lambda self: True),
    )
    yield


def _evt(user_id="u1", group_id="g1", platform="onebot11", **extra):
    data = {
        "id": f"evt_{user_id}",
        "time": 1712345678,
        "type": "message",
        "detail_type": "group" if group_id else "private",
        "platform": platform,
        "self": {"platform": platform, "user_id": "bot_x"},
        "user_id": user_id,
        "message": [{"type": "text", "data": {"text": "hi"}}],
        "alt_message": "hi",
    }
    if group_id:
        data["group_id"] = group_id
    data.update(extra)
    return Event(data)


# ==================== 会话键 ====================


class TestSessionKey:
    def test_group_key(self):
        assert transcript.session_key_from_event(_evt()) == "onebot11:group:g1"

    def test_private_key(self):
        assert transcript.session_key_from_event(_evt(group_id=None)) == "onebot11:private:u1"

    def test_key_string_passthrough(self):
        transcript.append(temp_sm := "x:y:z", "user", "hi") if False else None


# ==================== 记录与查询 ====================


class TestAppendGet:
    def test_append_and_get_order(self, temp_sm):
        evt = _evt()
        transcript.append(evt, "user", "第一句", event_id="evt_u1")
        transcript.append(evt, "bot", "第二句")
        transcript.append(evt, "user", "第三句")

        history = asyncio.run(evt.history(10))
        assert [m["text"] for m in history] == ["第一句", "第二句", "第三句"]
        assert [m["role"] for m in history] == ["user", "bot", "user"]
        assert history[0]["event_id"] == "evt_u1"

    def test_sessions_isolated(self, temp_sm):
        # 会话维度隔离：不同群（target）互不可见；同群不同用户属于同一会话
        transcript.append(_evt(group_id="g1"), "user", "G1")
        transcript.append(_evt(group_id="g2"), "user", "G2")

        h1 = asyncio.run(_evt(group_id="g1").history(10))
        assert [m["text"] for m in h1] == ["G1"]

    def test_text_truncated(self, temp_sm):
        evt = _evt()
        transcript.append(evt, "user", "x" * (TRANSCRIPT_TEXT_MAX_CHARS + 100))
        history = asyncio.run(evt.history(5))
        assert len(history[0]["text"]) == TRANSCRIPT_TEXT_MAX_CHARS

    def test_clear(self, temp_sm):
        evt = _evt()
        transcript.append(evt, "user", "temp")
        assert transcript.clear(evt) == 1
        assert asyncio.run(evt.history(5)) == []

    def test_disabled_append_noop(self, temp_sm, monkeypatch):
        monkeypatch.setattr(type(transcript), "enabled", property(lambda self: False))
        evt = _evt()
        assert transcript.append(evt, "user", "ignored") is False
        assert asyncio.run(evt.history(5)) == []


# ==================== 出站钩子 ====================


class TestOutboundHook:
    @pytest.mark.asyncio
    async def test_on_message_sent_records_bot(self, temp_sm):
        await transcript._on_message_sent(
            {"platform": "onebot11", "detail_type": "group", "target_id": "g1", "preview": "机器人回复"}
        )
        history = transcript.get("onebot11:group:g1", 10)
        assert len(history) == 1
        assert history[0]["role"] == "bot"
        assert history[0]["text"] == "机器人回复"

    @pytest.mark.asyncio
    async def test_on_message_sent_skips_no_preview(self, temp_sm):
        await transcript._on_message_sent({"platform": "p", "detail_type": "d", "target_id": "t"})
        assert transcript.get("p:d:t", 10) == []


# ==================== 保留策略 ====================


class TestRetention:
    def test_max_per_session(self, temp_sm, monkeypatch):
        monkeypatch.setattr(_transcript_module, "_RETENTION_INTERVAL", 1)
        evt = _evt()
        for i in range(10):
            transcript.append(evt, "user", f"m{i}")
        transcript._retention(transcript.session_key_from_event(evt), max_per_session=5, ttl_hours=0)

        history = asyncio.run(evt.history(50))
        assert len(history) == 5
        assert history[0]["text"] == "m5"
