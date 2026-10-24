"""
会话收件箱归因增强单元测试（#467/#468/#469/#470）

覆盖：
- sender / meta 查询透传（get / recent / get_by_trace，含缓冲行 read-your-writes）
- 旧表 meta 列迁移与后端不支持 ALTER 的静默降级
- meta JSON 损坏容错
- 入站 bot 回声识别三模式（self_echo = bot / skip / user）与非回显平台回归
- recent() 会话键过滤（含 None / "" 语义回归）
- 出站发送归属（send_ctx.module 的 owner / caller / 兜底路径与分发期 owner 注入）
"""

import asyncio
import importlib
import os
import tempfile
import uuid

import pytest

from ErisPulse.Core.Bases import BaseAdapter, SendDSL
from ErisPulse.Core.Event.wrapper import Event
from ErisPulse.Core.storage import StorageManager
from ErisPulse.Core.transcript import TRANSCRIPT_TABLE, transcript
from ErisPulse.runtime.context import current_caller, current_owner, get_current_owner, owner_scope

# importlib.import_module 返回真实子模块
# （Core.storage / Core.transcript 的包属性分别被 StorageManager / transcript 单例遮蔽）
_storage_module = importlib.import_module("ErisPulse.Core.storage")
_transcript_module = importlib.import_module("ErisPulse.Core.transcript")


@pytest.fixture
def temp_sm(monkeypatch):
    """用临时数据库替换全局 storage（transcript 为运行时导入）"""
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
        transcript._next_retention_at = transcript._RETENTION_INTERVAL
        transcript._buffer.clear()
        transcript._flusher_started = False
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


@pytest.fixture(autouse=True)
def default_self_echo(monkeypatch):
    """self_echo 配置缺省（回退默认 bot；各模式用例按需覆盖属性或配置）"""
    monkeypatch.setattr(transcript, "_config", dict)
    yield


def _evt(user_id="u1", group_id="g1", platform="onebot11", self_id="bot_x", **extra):
    """构造入站 message 事件（Event 包装）"""
    data = {
        "id": f"evt-{uuid.uuid4().hex[:8]}",
        "time": 1712345678,
        "type": "message",
        "detail_type": "group" if group_id else "private",
        "platform": platform,
        "user_id": user_id,
        "message": [{"type": "text", "data": {"text": "hi"}}],
        "alt_message": "hi",
    }
    if self_id is not None:
        data["self"] = {"platform": platform, "user_id": self_id}
    if group_id:
        data["group_id"] = group_id
    data.update(extra)
    return Event(data)


# ==================== #467：sender / meta 查询透传 ====================


class TestSenderMetaReadback:
    def test_get_returns_sender_meta_buffered(self, temp_sm):
        """缓冲行（未落盘）read-your-writes：get 立即可读 sender / meta"""
        evt = _evt()
        transcript.append(
            evt, "user", "你好", event_id="evt-1", sender="u123",
            meta={"nickname": "小王", "sub_type": "normal"},
        )
        rows = transcript.get(evt, 10)
        assert len(rows) == 1
        assert rows[0]["sender"] == "u123"
        assert rows[0]["event_id"] == "evt-1"
        assert rows[0]["meta"]["nickname"] == "小王"
        assert rows[0]["meta"]["sub_type"] == "normal"

    def test_get_returns_sender_meta_after_flush(self, temp_sm):
        """落盘行（DB 路径）：flush 后 get 仍返回 sender / meta"""
        evt = _evt()
        transcript.append(
            evt, "bot", "回复", event_id="evt-2", sender="bot_x",
            meta={"module": "ChatMod"},
        )
        assert transcript.flush() == 1
        rows = transcript.get(evt, 10)
        assert rows[0]["sender"] == "bot_x"
        assert rows[0]["meta"]["module"] == "ChatMod"

    def test_append_without_meta_defaults_empty(self, temp_sm):
        """未传 meta 时回退 {}（旧调用方兼容）"""
        transcript.append(_evt(), "user", "plain", sender="u1")
        rows = transcript.get("onebot11:group:g1", 10)
        assert rows[0]["sender"] == "u1"
        assert rows[0]["meta"] == {}

    def test_recent_includes_sender_meta(self, temp_sm):
        transcript.append("p:group:1", "user", "m1", sender="u1", meta={"nickname": "A"})
        transcript.append("p:group:2", "bot", "m2", sender="b1", meta={"module": "M"})
        transcript.flush()
        rows = transcript.recent(60)
        by_text = {r["text"]: r for r in rows}
        assert by_text["m1"]["sender"] == "u1"
        assert by_text["m1"]["meta"] == {"nickname": "A"}
        assert by_text["m2"]["meta"]["module"] == "M"

    def test_get_by_trace_includes_sender_meta(self, temp_sm):
        transcript.append(
            "p:group:1", "bot", "out", event_id="trace-9", sender="b1",
            meta={"module": "ChatMod"},
        )
        transcript.flush()
        rows = transcript.get_by_trace("trace-9")
        assert len(rows) == 1
        assert rows[0]["sender"] == "b1"
        assert rows[0]["meta"]["module"] == "ChatMod"

    @pytest.mark.asyncio
    async def test_event_history_includes_attribution(self, temp_sm):
        """event.history()（转发 get）返回归因字段"""
        evt = _evt()
        transcript.append(evt, "user", "问题", sender="u9", meta={"nickname": "提问者"})
        history = await evt.history(10)
        assert history[0]["sender"] == "u9"
        assert history[0]["meta"]["nickname"] == "提问者"

    def test_outbound_hook_records_module_meta(self, temp_sm):
        """message.sent 钩子记录携带 send_ctx 元数据与 module 归属"""
        asyncio.run(transcript._on_message_sent(
            {
                "platform": "onebot11", "method": "Text", "detail_type": "group",
                "target_id": "g1", "bot_id": "bot_x", "trace_id": "trace-1",
                "preview": "机器人回复", "module": "ChatMod",
            }
        ))
        rows = transcript.get("onebot11:group:g1", 10)
        assert rows[0]["role"] == "bot"
        assert rows[0]["meta"]["module"] == "ChatMod"
        assert rows[0]["meta"]["method"] == "Text"

    def test_outbound_hook_without_module_defaults_empty(self, temp_sm):
        """send_ctx 缺 module 键（第三方发射）时 meta.module 兜底空串"""
        asyncio.run(transcript._on_message_sent(
            {"platform": "p", "detail_type": "group", "target_id": "t",
             "preview": "hi", "trace_id": "trace-2"}
        ))
        rows = transcript.get("p:group:t", 10)
        assert rows[0]["meta"]["module"] == ""


# ==================== #467：旧表迁移与降级 ====================


class TestMetaMigration:
    def _make_old_table(self, manager):
        """构造 2.8 时代的旧表（有 sender 无 meta）并写入一行"""
        manager.CreateTable(
            TRANSCRIPT_TABLE,
            {
                "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
                "session_key": "TEXT NOT NULL",
                "event_id": "TEXT DEFAULT ''",
                "role": "TEXT NOT NULL",
                "sender": "TEXT DEFAULT ''",
                "text": "TEXT DEFAULT ''",
                "ts": "REAL NOT NULL",
            },
        )
        manager.Table(TRANSCRIPT_TABLE).Insert(
            {
                "session_key": "legacy:group:1",
                "event_id": "old-1",
                "role": "user",
                "sender": "legacy_user",
                "text": "旧数据",
                "ts": 1712345678.0,
            }
        ).Execute()

    def test_old_table_auto_adds_meta_column(self, temp_sm):
        """旧表（无 meta 列）在首次查询前自动补列，旧数据 meta 回退 {}"""
        self._make_old_table(temp_sm)
        rows = transcript.get("legacy:group:1", 10)
        assert len(rows) == 1
        assert rows[0]["sender"] == "legacy_user"
        assert rows[0]["meta"] == {}
        # 补列后新写入的 meta 可正常落盘读回
        transcript.append("legacy:group:1", "user", "新数据", meta={"nickname": "新"})
        transcript.flush()
        rows = transcript.get("legacy:group:1", 10)
        assert {r["text"]: r["meta"].get("nickname", "") for r in rows} == {
            "旧数据": "", "新数据": "新",
        }

    def test_alter_unsupported_degrades_silently(self, temp_sm, monkeypatch):
        """后端不支持 ALTER 时静默降级：查询不抛错（DB 行不可见，缓冲行仍可读）"""

        class _NoAlterProxy:
            """包装存储管理器：AlterTable 一律抛错（模拟不支持 ALTER 的后端）"""

            def __init__(self, inner):
                self._inner = inner

            def __getattr__(self, name):
                if name == "AlterTable":
                    def _no_alter(*_args, **_kwargs):
                        raise RuntimeError("ALTER not supported")

                    return _no_alter
                return getattr(self._inner, name)

        self._make_old_table(temp_sm)
        # 存储管理器 __setattr__ 会拦截实例属性写入，须经模块引用替换
        monkeypatch.setattr(_transcript_module, "storage", _NoAlterProxy(temp_sm))
        rows = transcript.get("legacy:group:1", 10)  # 不抛错
        assert rows == []
        transcript.append("legacy:group:1", "user", "降级期", sender="u1", meta={"k": "v"})
        rows = transcript.get("legacy:group:1", 10)
        assert [r["text"] for r in rows] == ["降级期"]
        assert rows[0]["meta"] == {"k": "v"}

    def test_corrupt_meta_json_returns_empty(self, temp_sm):
        """meta 列 JSON 损坏时返回 {} 不抛错"""
        transcript.append("p:group:1", "user", "好数据")
        transcript.flush()
        temp_sm.Table(TRANSCRIPT_TABLE).Insert(
            {
                "session_key": "p:group:1",
                "event_id": "corrupt-1",
                "role": "user",
                "sender": "u1",
                "text": "损坏行",
                "meta": "{not-json",
                "ts": 1712345679.0,
            }
        ).Execute()
        rows = transcript.get("p:group:1", 10)
        by_text = {r["text"]: r["meta"] for r in rows}
        assert by_text["好数据"] == {}
        assert by_text["损坏行"] == {}

    def test_non_dict_meta_input_ignored(self, temp_sm):
        """append 收到非 dict meta 时按空元数据处理"""
        transcript.append("p:group:1", "user", "bad", meta="not-a-dict")  # type: ignore[arg-type]
        rows = transcript.get("p:group:1", 10)
        assert rows[0]["meta"] == {}


# ==================== #470：入站 bot 回声识别 ====================


class TestSelfEcho:
    @pytest.fixture
    def manager(self):
        from ErisPulse.Core.adapter import AdapterManager

        mgr = AdapterManager()
        mgr._adapters.clear()
        mgr._started_instances.clear()
        mgr._onebot_handlers.clear()
        mgr._raw_handlers.clear()
        mgr._onebot_middlewares.clear()
        return mgr

    def _emit_message(self, manager, *, user_id, self_id, **extra):
        """经 adapter.emit 走真实入站记录点"""
        data = {
            "id": f"evt-{uuid.uuid4().hex[:8]}",
            "time": 1712345678,
            "type": "message",
            "detail_type": "group",
            "platform": "onebot11",
            "user_id": user_id,
            "message": [{"type": "text", "data": {"text": "hi"}}],
            "alt_message": "hi",
            "group_id": "g1",
            "sub_type": "normal",
            "message_id": "mid-1",
        }
        if self_id is not None:
            data["self"] = {"platform": "onebot11", "user_id": self_id}
        data.update(extra)
        asyncio.run(manager.emit(data))

    def test_echo_recorded_as_bot_by_default(self, temp_sm, manager):
        """默认模式 bot：回声记 role=bot、sender=self_id、meta.self_echo=True"""
        self._emit_message(manager, user_id="bot_1", self_id="bot_1", user_name="机器人")
        rows = transcript.get("onebot11:group:g1", 10)
        assert len(rows) == 1
        assert rows[0]["role"] == "bot"
        assert rows[0]["sender"] == "bot_1"
        assert rows[0]["meta"]["self_echo"] is True
        assert rows[0]["meta"]["self_id"] == "bot_1"
        assert rows[0]["meta"]["nickname"] == "机器人"
        assert rows[0]["meta"]["sub_type"] == "normal"
        assert rows[0]["meta"]["message_id"] == "mid-1"

    def test_echo_skip_mode_not_recorded(self, temp_sm, manager, monkeypatch):
        monkeypatch.setattr(type(transcript), "self_echo", property(lambda self: "skip"))
        self._emit_message(manager, user_id="bot_1", self_id="bot_1")
        assert transcript.get("onebot11:group:g1", 10) == []
        assert len(transcript._buffer) == 0

    def test_echo_user_mode_legacy_behavior(self, temp_sm, manager, monkeypatch):
        monkeypatch.setattr(type(transcript), "self_echo", property(lambda self: "user"))
        self._emit_message(manager, user_id="bot_1", self_id="bot_1")
        rows = transcript.get("onebot11:group:g1", 10)
        assert len(rows) == 1
        assert rows[0]["role"] == "user"
        assert rows[0]["sender"] == "bot_1"
        assert "self_echo" not in rows[0]["meta"]

    def test_normal_user_message_unchanged(self, temp_sm, manager):
        """非回显平台回归：普通用户消息 role=user、无 self_echo 标记"""
        self._emit_message(manager, user_id="u9", self_id="bot_1", user_nickname="小王")
        rows = transcript.get("onebot11:group:g1", 10)
        assert len(rows) == 1
        assert rows[0]["role"] == "user"
        assert rows[0]["sender"] == "u9"
        assert rows[0]["meta"]["nickname"] == "小王"
        assert rows[0]["meta"]["self_id"] == "bot_1"
        assert "self_echo" not in rows[0]["meta"]

    def test_missing_self_field_zero_impact(self, temp_sm, manager):
        """self 字段缺失的适配器：零影响（不识别回声）"""
        self._emit_message(manager, user_id="u9", self_id=None)
        rows = transcript.get("onebot11:group:g1", 10)
        assert len(rows) == 1
        assert rows[0]["role"] == "user"
        assert rows[0]["meta"]["self_id"] == ""

    def test_self_echo_property_semantics(self, temp_sm, monkeypatch):
        """self_echo 属性：配置缺省/非法值回退默认 bot"""
        from ErisPulse.Core.constants import DEFAULT_TRANSCRIPT_SELF_ECHO

        monkeypatch.setattr(transcript, "_config", dict)
        assert transcript.self_echo == DEFAULT_TRANSCRIPT_SELF_ECHO == "bot"
        monkeypatch.setattr(transcript, "_config", lambda: {"self_echo": "skip"})
        assert transcript.self_echo == "skip"
        monkeypatch.setattr(transcript, "_config", lambda: {"self_echo": "bogus"})
        assert transcript.self_echo == "bot"
        monkeypatch.setattr(transcript, "_config", lambda: {"self_echo": "user"})
        assert transcript.self_echo == "user"


# ==================== #468：recent 会话过滤 ====================


class TestRecentSessionFilter:
    def test_filter_returns_only_target_session(self, temp_sm):
        """多会话写入后按 session_key 过滤只返回该会话行（含 sender/meta）"""
        transcript.append("onebot11:group:1", "user", "A1", sender="u1", meta={"nickname": "A"})
        transcript.append("onebot11:group:2", "user", "B1", sender="u2")
        transcript.append("onebot11:group:1", "bot", "A2", sender="b1", meta={"module": "M"})
        transcript.flush()
        rows = transcript.recent(60, session_key="onebot11:group:1")
        assert [r["text"] for r in rows] == ["A1", "A2"]
        assert all(r["session_key"] == "onebot11:group:1" for r in rows)
        assert rows[0]["sender"] == "u1"
        assert rows[0]["meta"]["nickname"] == "A"
        assert rows[1]["meta"]["module"] == "M"

    def test_none_keeps_cross_session_semantics(self, temp_sm):
        """session_key=None 回归：跨会话全局查询（现状行为）"""
        transcript.append("onebot11:group:1", "user", "A1")
        transcript.append("onebot11:group:2", "user", "B1")
        transcript.flush()
        rows = transcript.recent(60)
        assert sorted(r["text"] for r in rows) == ["A1", "B1"]

    def test_empty_string_treated_as_no_filter(self, temp_sm):
        """session_key="" 容错：等价不过滤（docstring 契约）"""
        transcript.append("onebot11:group:1", "user", "A1")
        transcript.append("onebot11:group:2", "user", "B1")
        transcript.flush()
        rows = transcript.recent(60, session_key="")
        assert sorted(r["text"] for r in rows) == ["A1", "B1"]

    def test_filter_with_buffered_rows(self, temp_sm):
        """read-your-writes：仅入缓冲的行也按 session_key 过滤可读"""
        transcript.append("onebot11:group:1", "user", "buf-A")
        transcript.append("onebot11:group:2", "user", "buf-B")
        rows = transcript.recent(60, session_key="onebot11:group:1")
        assert [r["text"] for r in rows] == ["buf-A"]

    def test_filter_unknown_session_returns_empty(self, temp_sm):
        transcript.append("onebot11:group:1", "user", "A1")
        transcript.flush()
        assert transcript.recent(60, session_key="onebot11:group:999") == []


# ==================== #469：出站发送归属 ====================


def _make_send_adapter():
    """构建遵循标准适配器模式的测试适配器（Raw_ob12 + send_context）"""

    class _Adapter(BaseAdapter):
        _platform = "testplat"

        async def start(self):
            pass

        async def shutdown(self):
            pass

        async def call_api(self, endpoint: str, **params):
            return {
                "status": "ok",
                "retcode": 0,
                "data": {},
                "message_id": "mid_test",
                "message": "",
            }

    adapter = _Adapter()

    class _RealSend(SendDSL):
        def Raw_ob12(self, message, **kwargs):
            async def _do_send():
                segments = self._apply_modifiers(message)
                return await self._adapter.call_api(
                    endpoint="/send_message",
                    message=segments,
                    **self.send_context,
                    **kwargs,
                )

            return asyncio.ensure_future(_do_send())

    adapter.Send = _RealSend(adapter)
    return adapter


class TestSendCtxModule:
    @pytest.fixture(autouse=True)
    def clean_owner_context(self):
        """确保 ContextVar 与收件箱缓冲用例间无泄漏"""
        assert current_owner.get() is None
        assert current_caller.get() is None
        transcript._buffer.clear()
        yield
        transcript._buffer.clear()
        assert current_owner.get() is None
        assert current_caller.get() is None

    def _capture_sent_ctx(self):
        from ErisPulse.Core.lifecycle import lifecycle

        captured = []

        async def _on_sent(data):
            captured.append(data)

        lifecycle.on("message.sent")(_on_sent)
        return captured, _on_sent

    def _unregister(self, handler):
        from ErisPulse.Core.lifecycle import lifecycle

        handlers = lifecycle._hooks.get("message.sent", [])
        lifecycle._hooks["message.sent"] = [item for item in handlers if item[1] is not handler]

    @pytest.mark.asyncio
    async def test_module_from_current_owner(self):
        """模块经 module.call 执行期间（current_owner 已注入）：module=目标模块"""
        captured, handler = self._capture_sent_ctx()
        try:
            token = current_owner.set("QvQChat")
            try:
                await _make_send_adapter().Send.To("group", "g1").Text("hi")
            finally:
                current_owner.reset(token)
            for _ in range(100):
                if captured:
                    break
                await asyncio.sleep(0.02)
            assert captured and captured[0]["module"] == "QvQChat"
        finally:
            self._unregister(handler)

    @pytest.mark.asyncio
    async def test_module_falls_back_to_caller(self):
        """current_owner 缺失时回退 current_caller"""
        captured, handler = self._capture_sent_ctx()
        try:
            token = current_caller.set("CallerMod")
            try:
                await _make_send_adapter().Send.To("group", "g1").Text("hi")
            finally:
                current_caller.reset(token)
            for _ in range(100):
                if captured:
                    break
                await asyncio.sleep(0.02)
            assert captured and captured[0]["module"] == "CallerMod"
        finally:
            self._unregister(handler)

    @pytest.mark.asyncio
    async def test_module_empty_without_context(self):
        """无任何模块上下文（框架直发）：module="" 不抛错"""
        captured, handler = self._capture_sent_ctx()
        try:
            await _make_send_adapter().Send.To("group", "g1").Text("hi")
            for _ in range(100):
                if captured:
                    break
                await asyncio.sleep(0.02)
            assert captured and captured[0]["module"] == ""
        finally:
            self._unregister(handler)

    @pytest.mark.asyncio
    async def test_owner_priority_over_caller(self):
        """owner 优先于 caller（与 connections.py 既有回退顺序一致）"""
        captured, handler = self._capture_sent_ctx()
        try:
            owner_token = current_owner.set("Target")
            caller_token = current_caller.set("Caller")
            try:
                await _make_send_adapter().Send.To("group", "g1").Text("hi")
            finally:
                current_owner.reset(owner_token)
                current_caller.reset(caller_token)
            for _ in range(100):
                if captured:
                    break
                await asyncio.sleep(0.02)
            assert captured and captured[0]["module"] == "Target"
        finally:
            self._unregister(handler)


class TestDispatchOwnerInjection:
    """事件处理器分发期间按注册期归属注入 current_owner（#469 方案 b）"""

    @pytest.fixture(autouse=True)
    def isolate_transcript_buffer(self):
        """emit 会触发入站自动记录：隔离共享收件箱缓冲，避免跨用例泄漏"""
        transcript._buffer.clear()
        yield
        transcript._buffer.clear()

    @pytest.fixture
    def manager(self):
        from ErisPulse.Core.adapter import AdapterManager

        mgr = AdapterManager()
        mgr._adapters.clear()
        mgr._started_instances.clear()
        mgr._onebot_handlers.clear()
        mgr._raw_handlers.clear()
        mgr._onebot_middlewares.clear()
        return mgr

    def _message_event(self):
        return {
            "id": f"evt-{uuid.uuid4().hex[:8]}",
            "time": 1712345678,
            "type": "message",
            "detail_type": "group",
            "platform": "onebot11",
            "self": {"platform": "onebot11", "user_id": "bot_1"},
            "user_id": "u1",
            "message": [{"type": "text", "data": {"text": "hi"}}],
            "alt_message": "hi",
            "group_id": "g1",
        }

    @pytest.mark.asyncio
    async def test_handler_runs_with_registered_owner(self, manager):
        """模块 B 注册的处理器内发送 / 读上下文 → 归属 B"""
        seen_owners = []

        with owner_scope("ChatMod"):
            @manager.on("message")
            async def handler(data):
                seen_owners.append(get_current_owner())

        await manager.emit(self._message_event())
        for _ in range(100):
            if seen_owners:
                break
            await asyncio.sleep(0.02)
        assert seen_owners == ["ChatMod"]

    @pytest.mark.asyncio
    async def test_handler_without_owner_keeps_outer_context(self, manager):
        """框架级处理器（注册期无 owner）：保持外层上下文不覆盖"""
        seen_owners = []

        @manager.on("message", scope_exempt=True)
        async def handler(data):
            seen_owners.append(get_current_owner())

        outer_token = current_owner.set("OuterCtx")
        try:
            await manager.emit(self._message_event())
            for _ in range(100):
                if seen_owners:
                    break
                await asyncio.sleep(0.02)
        finally:
            current_owner.reset(outer_token)
        assert seen_owners == ["OuterCtx"]

    @pytest.mark.asyncio
    async def test_outer_context_not_polluted(self, manager):
        """处理器 Task 内的 owner 注入不泄漏到分发方上下文"""

        with owner_scope("OwnerMod"):
            @manager.on("message")
            async def handler(data):
                pass

        await manager.emit(self._message_event())
        await asyncio.sleep(0.05)
        assert current_owner.get() is None
