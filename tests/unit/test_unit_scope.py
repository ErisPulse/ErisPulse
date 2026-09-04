"""
模块作用域系统单元测试

测试 ScopeManager 的绑定解析、is_allowed 判断、运行时增删，
以及事件处理器 / 命令分发链路上的作用域过滤。
"""

import asyncio
from unittest.mock import patch

import pytest

from ErisPulse.Core.scope import ScopeManager


class TestScopeManager:
    """ScopeManager 核心功能测试"""

    @staticmethod
    def _make_mgr(bindings: dict) -> ScopeManager:
        mgr = ScopeManager()
        mgr._bindings = bindings
        return mgr

    def test_default_allow_all(self):
        """无绑定（默认）时所有模块允许"""
        mgr = self._make_mgr({"platforms": {}, "bots": {}})
        assert mgr.is_allowed("onebot11", "123", "Chat") is True
        assert mgr.is_allowed("onebot11", None, "Chat") is True

    def test_empty_module_name_allowed(self):
        """模块名为空（框架层资源）始终放行"""
        mgr = self._make_mgr({"platforms": {}, "bots": {}})
        assert mgr.is_allowed("onebot11", "123", None) is True
        assert mgr.is_allowed("onebot11", "123", "") is True

    def test_bot_allowlist(self):
        """Bot 级白名单：仅列出的模块允许"""
        mgr = self._make_mgr(
            {
                "platforms": {},
                "bots": {"onebot11": {"123456": {"modules": ["Chat"], "blocked": []}}},
            }
        )
        assert mgr.is_allowed("onebot11", "123456", "Chat") is True
        assert mgr.is_allowed("onebot11", "123456", "Translate") is False

    def test_bot_blocklist(self):
        """Bot 级黑名单：列出的模块禁用"""
        mgr = self._make_mgr(
            {
                "platforms": {},
                "bots": {"onebot11": {"123456": {"modules": [], "blocked": ["Danger"]}}},
            }
        )
        assert mgr.is_allowed("onebot11", "123456", "Danger") is False
        assert mgr.is_allowed("onebot11", "123456", "Chat") is True

    def test_platform_fallback(self):
        """平台级绑定作用于该平台所有 Bot"""
        mgr = self._make_mgr(
            {
                "platforms": {"onebot11": {"modules": ["Chat"], "blocked": ["Danger"]}},
                "bots": {},
            }
        )
        assert mgr.is_allowed("onebot11", "100", "Chat") is True
        assert mgr.is_allowed("onebot11", "100", "Danger") is False
        assert mgr.is_allowed("onebot11", "200", "Translate") is False
        # 其它平台不受影响
        assert mgr.is_allowed("telegram", "100", "Translate") is True

    def test_bot_overrides_platform(self):
        """Bot 级绑定覆盖平台级绑定"""
        mgr = self._make_mgr(
            {
                "platforms": {"onebot11": {"modules": ["Chat"], "blocked": []}},
                "bots": {"onebot11": {"123456": {"modules": [], "blocked": ["Chat"]}}},
            }
        )
        # Bot 级黑名单 Chat → 即使平台级白名单包含 Chat 也被拒绝
        assert mgr.is_allowed("onebot11", "123456", "Chat") is False
        # 其它 Bot 仍遵循平台级绑定
        assert mgr.is_allowed("onebot11", "999", "Chat") is True

    def test_get_effective_binding(self):
        """get() 返回生效绑定（原始配置形态）"""
        mgr = self._make_mgr(
            {
                "platforms": {"onebot11": {"modules": ["Chat"], "blocked": []}},
                "bots": {"onebot11": {"123456": {"modules": ["Chat"], "blocked": []}}},
            }
        )
        assert mgr.get("onebot11", "123456") == {"modules": ["Chat"], "blocked": []}
        assert mgr.get("onebot11") == {"modules": ["Chat"], "blocked": []}
        assert mgr.get("telegram") is None

    def test_bind_runtime(self):
        """bind(persist=False) 仅运行时生效"""
        mgr = self._make_mgr({"platforms": {}, "bots": {}})
        mgr.bind_module("onebot11", "123456", modules=["Chat"], persist=False)
        assert mgr.is_allowed("onebot11", "123456", "Chat") is True
        assert mgr.is_allowed("onebot11", "123456", "Translate") is False

    def test_bind_platform_runtime(self):
        """bind 平台级（bot_id=None）运行时生效"""
        mgr = self._make_mgr({"platforms": {}, "bots": {}})
        mgr.bind_module("onebot11", blocked=["Danger"], persist=False)
        assert mgr.is_allowed("onebot11", "111", "Danger") is False
        assert mgr.is_allowed("onebot11", "111", "Chat") is True

    def test_unbind_runtime(self):
        """unbind(persist=False) 移除绑定"""
        mgr = self._make_mgr(
            {
                "platforms": {},
                "bots": {"onebot11": {"123456": {"modules": ["Chat"], "blocked": []}}},
            }
        )
        assert mgr.unbind_module("onebot11", "123456", persist=False) is True
        assert mgr.get("onebot11", "123456") is None
        assert mgr.is_allowed("onebot11", "123456", "Translate") is True
        # 再次移除返回 False
        assert mgr.unbind_module("onebot11", "123456", persist=False) is False

    def test_bind_persist_writes_config(self):
        """bind(persist=True) 写入配置并同步内存态（不依赖配置回读）"""
        mgr = self._make_mgr({"platforms": {}, "bots": {}})
        written = {}

        def fake_update(new_config):
            written.update(new_config)

        with patch("ErisPulse.Core.scope.update_erispulse_config", side_effect=fake_update):
            mgr.bind_module("onebot11", "123456", modules=["Chat"], blocked=["Danger"])
        assert written["scope"]["bots"]["onebot11"]["123456"] == {
            "modules": ["Chat"],
            "blocked": ["Danger"],
        }
        # 写入触发的 config.set 重载可能回读旧缓存，内存态必须已直接应用
        assert mgr.get("onebot11", "123456") == {
            "modules": ["Chat"],
            "blocked": ["Danger"],
        }

    def test_unbind_persist_writes_config(self):
        """unbind(persist=True) 整节替换写入以支持删除绑定"""
        mgr = self._make_mgr(
            {
                "platforms": {},
                "bots": {"onebot11": {"123456": {"modules": ["Chat"], "blocked": []}}},
            }
        )
        written = {}

        def fake_set(path, value):
            written[path] = value

        with patch("ErisPulse.Core.scope.set_erispulse_section", side_effect=fake_set):
            assert mgr.unbind_module("onebot11", "123456") is True
        assert written["scope.bots"] == {}
        assert mgr.get("onebot11", "123456") is None

    def test_list_bindings_and_clear(self):
        """list_bindings() 与 clear()"""
        mgr = self._make_mgr(
            {
                "platforms": {"onebot11": {"modules": ["Chat"], "blocked": []}},
                "bots": {"onebot11": {"123456": {"modules": [], "blocked": ["X"]}}},
            }
        )
        bindings = mgr.list_bindings()
        assert bindings["platforms"]["onebot11"]["modules"] == ["Chat"]
        mgr.clear()
        assert mgr.list_bindings() == {
            "platforms": {},
            "bots": {},
            "sessions": {},
            "identity": {"adapters": {}, "bots": {}, "sessions": {}, "users": {}},
            "commands": {},
            "handlers": {},
            "overrides": {},
            "actions": {},
        }

    def test_bot_id_from_event(self):
        """从事件提取 Bot 标识（account_id 优先，回退 user_id）"""
        mgr = self._make_mgr({"platforms": {}, "bots": {}})
        assert mgr.bot_id_from_event({"self": {"account_id": "a1", "user_id": "u1"}}) == "a1"
        assert mgr.bot_id_from_event({"self": {"user_id": "u1"}}) == "u1"
        assert mgr.bot_id_from_event({}) == ""
        assert mgr.bot_id_from_event({"self": {}}) == ""

    def test_config_hot_reload(self):
        """配置变更后绑定缓存重建"""
        mgr = self._make_mgr({"platforms": {}, "bots": {}})
        with patch("ErisPulse.runtime.get_config", return_value={"platforms": {"x": {"modules": ["A"]}}, "bots": {}}):
            mgr._on_config_updated({})
        assert mgr.is_allowed("x", "any", "A") is True
        assert mgr.is_allowed("x", "any", "B") is False


def _make_msg(text, platform="onebot11", bot_id="bot_x", user_id="u1", group_id=None):
    data = {
        "id": f"id_{abs(hash(text))}",
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


class TestScopeDispatch:
    """作用域在事件分发 / 命令分发链路中的过滤测试"""

    @pytest.fixture(autouse=True)
    def clean_handlers(self):
        from ErisPulse.Core.adapter import adapter
        from ErisPulse.Core.Event import _clear_all_handlers

        _clear_all_handlers()
        adapter._onebot_handlers.clear()
        adapter._raw_handlers.clear()
        adapter._onebot_middlewares.clear()
        adapter._bots.clear()
        yield
        _clear_all_handlers()
        adapter._onebot_handlers.clear()
        adapter._raw_handlers.clear()
        adapter._onebot_middlewares.clear()
        adapter._bots.clear()

    @staticmethod
    def _scoped_mgr():
        mgr = ScopeManager()
        mgr._bindings = {
            "platforms": {},
            "bots": {"onebot11": {"bot_x": {"modules": ["ModuleB"], "blocked": []}}},
        }
        return mgr

    @pytest.mark.asyncio
    async def test_message_handler_filtered_by_scope(self):
        """被作用域禁用的模块，其消息处理器不触发"""
        from ErisPulse.Core.Event import message
        from ErisPulse.runtime.context import current_owner

        mgr = self._scoped_mgr()
        received = []

        with patch("ErisPulse.Core.scope.scope", mgr):
            token = current_owner.set("ModuleA")
            try:

                @message.on_message()
                async def handler_a(event):
                    received.append("A")

            finally:
                current_owner.reset(token)

            token = current_owner.set("ModuleB")
            try:

                @message.on_message()
                async def handler_b(event):
                    received.append("B")

            finally:
                current_owner.reset(token)

            from ErisPulse.Core.adapter import adapter

            await adapter.emit(_make_msg("hi"))
            await asyncio.sleep(0.05)

        assert received == ["B"]

    @pytest.mark.asyncio
    async def test_command_filtered_by_scope(self):
        """被作用域禁用的模块，其命令静默忽略（不回复、不执行）"""
        from ErisPulse.Core.Event import command
        from ErisPulse.runtime.context import current_owner

        mgr = self._scoped_mgr()
        received = []

        with patch("ErisPulse.Core.scope.scope", mgr):
            token = current_owner.set("ModuleA")
            try:

                @command("alpha")
                async def alpha(event):
                    received.append("A")

            finally:
                current_owner.reset(token)

            token = current_owner.set("ModuleB")
            try:

                @command("beta")
                async def beta(event):
                    received.append("B")

            finally:
                current_owner.reset(token)

            from ErisPulse.Core.adapter import adapter

            with patch("ErisPulse.Core.config.config.getConfig", return_value="/"):
                await adapter.emit(_make_msg("/alpha"))
                await asyncio.sleep(0.05)
                await adapter.emit(_make_msg("/beta"))
                await asyncio.sleep(0.05)

        assert received == ["B"]

    @pytest.mark.asyncio
    async def test_allowed_bot_still_gets_handlers(self):
        """未绑定的 Bot 收到所有模块的处理器与命令"""
        from ErisPulse.Core.Event import command, message
        from ErisPulse.runtime.context import current_owner

        mgr = self._scoped_mgr()  # 仅 bot_x 有绑定
        received = []

        with patch("ErisPulse.Core.scope.scope", mgr):
            token = current_owner.set("ModuleA")
            try:

                @message.on_message()
                async def handler_a(event):
                    received.append("A")

                @command("alpha")
                async def alpha(event):
                    received.append("cmdA")

            finally:
                current_owner.reset(token)

            from ErisPulse.Core.adapter import adapter

            await adapter.emit(_make_msg("hi", bot_id="bot_y"))  # 未绑定的 Bot
            await asyncio.sleep(0.05)
            with patch("ErisPulse.Core.config.config.getConfig", return_value="/"):
                await adapter.emit(_make_msg("/alpha", bot_id="bot_y"))
                await asyncio.sleep(0.05)

        assert "A" in received
        assert "cmdA" in received


class TestScopeSessionLevel:
    """会话级作用域：三级解析 会话 > Bot > 平台"""

    @staticmethod
    def _make_mgr(bindings: dict) -> ScopeManager:
        mgr = ScopeManager()
        mgr._bindings = bindings
        return mgr

    def test_session_allowlist(self):
        """会话级白名单：仅列出的模块允许"""
        mgr = self._make_mgr(
            {
                "platforms": {},
                "bots": {},
                "sessions": {"onebot11": {"group_9": {"modules": ["Chat"], "blocked": []}}},
            }
        )
        assert mgr.is_allowed("onebot11", "123", "Chat", "group_9") is True
        assert mgr.is_allowed("onebot11", "123", "Translate", "group_9") is False

    def test_session_blocklist(self):
        """会话级黑名单"""
        mgr = self._make_mgr(
            {
                "platforms": {},
                "bots": {},
                "sessions": {"onebot11": {"group_9": {"modules": [], "blocked": ["Danger"]}}},
            }
        )
        assert mgr.is_allowed("onebot11", "123", "Danger", "group_9") is False
        assert mgr.is_allowed("onebot11", "123", "Chat", "group_9") is True

    def test_session_overrides_bot(self):
        """会话级覆盖 Bot 级"""
        mgr = self._make_mgr(
            {
                "platforms": {},
                "bots": {"onebot11": {"b1": {"modules": ["B"], "blocked": []}}},
                "sessions": {"onebot11": {"group_9": {"modules": ["C"], "blocked": []}}},
            }
        )
        # 会话级 allow=['C'] 覆盖 Bot 级 allow=['B']
        assert mgr.is_allowed("onebot11", "b1", "C", "group_9") is True
        assert mgr.is_allowed("onebot11", "b1", "B", "group_9") is False
        # 无会话时回退 Bot 级
        assert mgr.is_allowed("onebot11", "b1", "B") is True
        assert mgr.is_allowed("onebot11", "b1", "C") is False

    def test_bot_overrides_platform(self):
        """Bot 级覆盖平台级"""
        mgr = self._make_mgr(
            {
                "platforms": {"onebot11": {"modules": ["A"], "blocked": []}},
                "bots": {"onebot11": {"b1": {"modules": ["B"], "blocked": []}}},
                "sessions": {},
            }
        )
        assert mgr.is_allowed("onebot11", "b1", "B") is True
        assert mgr.is_allowed("onebot11", "b1", "A") is False
        assert mgr.is_allowed("onebot11", "b2", "A") is True

    def test_session_bind_runtime(self):
        """bind 会话级（persist=False）运行时生效"""
        mgr = self._make_mgr({"platforms": {}, "bots": {}, "sessions": {}})
        mgr.bind_module("onebot11", session_id="group_9", modules=["Chat"], persist=False)
        assert mgr.is_allowed("onebot11", "b1", "Chat", "group_9") is True
        assert mgr.is_allowed("onebot11", "b1", "X", "group_9") is False

    def test_session_unbind_runtime(self):
        """unbind 会话级绑定"""
        mgr = self._make_mgr(
            {
                "platforms": {},
                "bots": {},
                "sessions": {"onebot11": {"group_9": {"modules": ["Chat"], "blocked": []}}},
            }
        )
        assert mgr.unbind_module("onebot11", session_id="group_9", persist=False) is True
        assert mgr.get("onebot11", None, "group_9") is None
        assert mgr.unbind_module("onebot11", session_id="group_9", persist=False) is False

    def test_session_persist_writes_config(self):
        """bind 会话级（persist=True）写入配置"""
        mgr = self._make_mgr({"platforms": {}, "bots": {}, "sessions": {}})
        written = {}

        def fake_update(new_config):
            written.update(new_config)

        with patch("ErisPulse.Core.scope.update_erispulse_config", side_effect=fake_update):
            mgr.bind_module("onebot11", session_id="group_9", modules=["Chat"])
        assert written["scope"]["sessions"]["onebot11"]["group_9"] == {
            "modules": ["Chat"],
            "blocked": [],
        }

    def test_session_id_from_event(self):
        """从事件提取会话标识（group / private / channel）"""
        mgr = self._make_mgr({"platforms": {}, "bots": {}, "sessions": {}})
        assert mgr.session_id_from_event({"detail_type": "group", "group_id": "g9"}) == "g9"
        assert mgr.session_id_from_event({"detail_type": "private", "user_id": "u1"}) == "u1"
        assert mgr.session_id_from_event({"detail_type": "channel", "channel_id": "c1"}) == "c1"
        assert mgr.session_id_from_event({}) == ""

    def test_session_id_from_event_meta_no_inference(self):
        """meta 等无会话上下文事件：直接返回空，不触发会话类型推断

        回归：connect / disconnect / heartbeat 等事件天然不含 group_id /
        channel_id / user_id 等会话字段，旧实现会经 infer_receive_type
        兜底推断并输出 WARNING 噪音（每次分发 3 次）。
        """
        import ErisPulse.Core.Event.session_type as _st

        mgr = self._make_mgr({"platforms": {}, "bots": {}, "sessions": {}})
        meta_events = [
            {"type": "meta", "detail_type": "connect", "self": {"user_id": "b1"}},
            {"type": "meta", "detail_type": "disconnect", "self": {"user_id": "b1"}},
            {"type": "meta", "detail_type": "heartbeat", "self": {"user_id": "b1"}},
            {"type": "meta", "detail_type": "connect"},
        ]

        # 打桩推断函数：若被调用则抛错，确保无会话字段事件不触发推断
        original = _st.infer_receive_type

        def _raise_if_called(*_a, **_k):
            raise AssertionError("infer_receive_type 不应被调用")

        _st.infer_receive_type = _raise_if_called
        try:
            for event in meta_events:
                assert mgr.session_id_from_event(event) == ""
        finally:
            _st.infer_receive_type = original

    def test_session_id_from_event_priority(self):
        """提取优先级 group > channel > guild > thread > user"""
        mgr = self._make_mgr({"platforms": {}, "bots": {}, "sessions": {}})
        assert (
            mgr.session_id_from_event(
                {"group_id": "g1", "channel_id": "c1", "user_id": "u1"}
            )
            == "g1"
        )
        assert mgr.session_id_from_event({"user_id": "u1"}) == "u1"

    def test_session_topology(self):
        """get_topology() 包含 sessions 桶"""
        mgr = self._make_mgr(
            {
                "platforms": {},
                "bots": {},
                "sessions": {"onebot11": {"group_9": {"modules": ["Chat"], "blocked": []}}},
            }
        )
        topo = mgr.get_topology()
        assert topo["sessions"]["onebot11"]["group_9"]["modules"] == ["Chat"]


class TestScopeSessionDispatch:
    """会话级作用域在事件 / 命令分发中的过滤"""

    @pytest.fixture(autouse=True)
    def clean_handlers(self):
        from ErisPulse.Core.adapter import adapter
        from ErisPulse.Core.Event import _clear_all_handlers

        _clear_all_handlers()
        adapter._onebot_handlers.clear()
        adapter._raw_handlers.clear()
        adapter._onebot_middlewares.clear()
        adapter._bots.clear()
        yield
        _clear_all_handlers()
        adapter._onebot_handlers.clear()
        adapter._raw_handlers.clear()
        adapter._onebot_middlewares.clear()
        adapter._bots.clear()

    @staticmethod
    def _scoped_mgr():
        mgr = ScopeManager()
        mgr._bindings = {
            "platforms": {},
            "bots": {},
            # 仅在群 g1 允许 ModuleB
            "sessions": {"onebot11": {"g1": {"modules": ["ModuleB"], "blocked": []}}},
        }
        return mgr

    @pytest.mark.asyncio
    async def test_message_handler_filtered_by_session(self):
        """同 Bot 不同群：被会话禁用的模块不触发"""
        from ErisPulse.Core.Event import message
        from ErisPulse.runtime.context import current_owner

        mgr = self._scoped_mgr()
        received = []

        with patch("ErisPulse.Core.scope.scope", mgr):
            token = current_owner.set("ModuleA")
            try:

                @message.on_message()
                async def handler_a(event):
                    received.append("A")

            finally:
                current_owner.reset(token)

            from ErisPulse.Core.adapter import adapter

            # 群 g1：ModuleA 被会话级白名单排除 → 不触发
            await adapter.emit(_make_msg("hi", group_id="g1"))
            await asyncio.sleep(0.05)
            # 群 g2：无会话绑定 → 回退允许全部 → 触发
            await adapter.emit(_make_msg("hi", group_id="g2"))
            await asyncio.sleep(0.05)

        assert received == ["A"]  # 仅 g2 触发

    @pytest.mark.asyncio
    async def test_command_filtered_by_session(self):
        """同 Bot 不同群：被会话禁用的命令静默忽略"""
        from ErisPulse.Core.Event import command
        from ErisPulse.runtime.context import current_owner

        mgr = self._scoped_mgr()
        received = []

        with patch("ErisPulse.Core.scope.scope", mgr):
            token = current_owner.set("ModuleA")
            try:

                @command("alpha")
                async def alpha(event):
                    received.append("A")

            finally:
                current_owner.reset(token)

            from ErisPulse.Core.adapter import adapter

            with patch("ErisPulse.Core.config.config.getConfig", return_value="/"):
                await adapter.emit(_make_msg("/alpha", group_id="g1"))
                await asyncio.sleep(0.05)
                await adapter.emit(_make_msg("/alpha", group_id="g2"))
                await asyncio.sleep(0.05)

        assert received == ["A"]  # 仅 g2 触发

class TestScopeEnhancements:
    """scope 增强：大小写不敏感 / default_allow / merge / 统计"""

    @staticmethod
    def _make_mgr(bindings: dict, default_allow: bool = True) -> ScopeManager:
        mgr = ScopeManager()
        mgr._bindings = bindings
        mgr._default_allow = default_allow
        return mgr

    def test_case_insensitive_module_match(self):
        """模块名大小写不敏感"""
        mgr = self._make_mgr(
            {
                "platforms": {},
                "bots": {},
                "sessions": {"p": {"g1": {"modules": ["Chat"], "blocked": []}}},
            }
        )
        assert mgr.is_allowed("p", "b1", "chat", "g1") is True
        assert mgr.is_allowed("p", "b1", "CHAT", "g1") is True
        assert mgr.is_allowed("p", "b1", "Translate", "g1") is False

    def test_default_allow_false_implicit_deny(self):
        """default_allow=false 时无绑定即拒绝"""
        mgr = self._make_mgr({"platforms": {}, "bots": {}, "sessions": {}}, default_allow=False)
        assert mgr.is_allowed("p", "b1", "Chat") is False
        assert mgr.is_allowed("p", "b1", "Anything") is False
        # 有白名单则白名单内放行
        mgr._bindings["platforms"]["p"] = {"modules": ["Chat"], "blocked": []}
        mgr._invalidate_cache()
        assert mgr.is_allowed("p", "b1", "Chat") is True
        assert mgr.is_allowed("p", "b1", "Music") is False

    def test_bind_merge(self):
        """bind_module(merge=True) 合并而非替换"""
        mgr = self._make_mgr({"platforms": {}, "bots": {}, "sessions": {}})
        mgr.bind_module("p", "b1", modules=["Chat"], persist=False)
        mgr.bind_module("p", "b1", modules=["Music"], persist=False, merge=True)
        mgr.bind_module("p", "b1", blocked=["Danger"], persist=False, merge=True)
        assert mgr.get("p", "b1") == {"modules": ["Chat", "Music"], "blocked": ["Danger"]}
        # 未 merge 则替换
        mgr.bind_module("p", "b1", modules=["Only"], persist=False)
        assert mgr.get("p", "b1") == {"modules": ["Only"], "blocked": []}

    def test_stats_filtered_count(self):
        """get_stats 统计过滤次数"""
        mgr = self._make_mgr(
            {
                "platforms": {},
                "bots": {"p": {"b1": {"modules": ["Chat"], "blocked": []}}},
                "sessions": {},
            }
        )
        mgr.reset_stats()
        assert mgr.is_allowed("p", "b1", "Chat") is True
        assert mgr.is_allowed("p", "b1", "Music") is False
        assert mgr.is_allowed("p", "b1", "Music") is False  # 缓存命中
        stats = mgr.get_stats()
        assert stats["module_filtered"] == 1
        assert stats["module_calls"] == 3
        assert stats["cache_hits"] == 1

    def test_cache_invalidated_on_bind(self):
        """bind 后缓存失效，立即生效"""
        mgr = self._make_mgr({"platforms": {}, "bots": {}, "sessions": {}})
        assert mgr.is_allowed("p", "b1", "Chat") is True  # 缓存 True
        mgr.bind_module("p", "b1", modules=["Music"], persist=False)
        assert mgr.is_allowed("p", "b1", "Chat") is False  # 缓存已失效


class TestScopePatternEntries:
    """模块维度条目统一语法（精确 / glob / re: 正则）"""

    @staticmethod
    def _make_mgr(bindings: dict) -> ScopeManager:
        mgr = ScopeManager()
        mgr._bindings = bindings
        return mgr

    def test_glob_whitelist(self):
        """白名单条目支持 glob"""
        mgr = self._make_mgr(
            {"platforms": {"p": {"modules": ["Tool*", "Chat"], "blocked": []}}, "bots": {}, "sessions": {}}
        )
        assert mgr.is_allowed("p", "b1", "ToolBox") is True
        assert mgr.is_allowed("p", "b1", "toolbox") is True
        assert mgr.is_allowed("p", "b1", "Music") is False

    def test_glob_blocklist(self):
        """黑名单条目支持 glob"""
        mgr = self._make_mgr(
            {"platforms": {"p": {"modules": [], "blocked": ["spam*"]}}, "bots": {}, "sessions": {}}
        )
        assert mgr.is_allowed("p", "b1", "SpamBot") is False
        assert mgr.is_allowed("p", "b1", "Chat") is True

    def test_regex_entries(self):
        """条目支持 re: 正则（黑名单 + 白名单组合）"""
        mgr = self._make_mgr(
            {"platforms": {"p": {"modules": [], "blocked": ["re:^danger.*bot$"]}}, "bots": {}, "sessions": {}}
        )
        assert mgr.is_allowed("p", "b1", "DangerBot") is False
        assert mgr.is_allowed("p", "b1", "danger_robot") is False
        assert mgr.is_allowed("p", "b1", "SafeChat") is True
        # 白名单正则：未命中即拒绝
        mgr2 = self._make_mgr(
            {"platforms": {"p": {"modules": ["re:^tool"], "blocked": []}}, "bots": {}, "sessions": {}}
        )
        assert mgr2.is_allowed("p", "b1", "ToolBox") is True
        assert mgr2.is_allowed("p", "b1", "Chat") is False

    def test_bind_with_pattern_entries(self):
        """bind_module 运行时写入模式条目"""
        mgr = self._make_mgr({"platforms": {}, "bots": {}, "sessions": {}})
        mgr.bind_module("p", "b1", modules=["re:^chat"], blocked=["Danger*"], persist=False)
        assert mgr.is_allowed("p", "b1", "ChatPro") is True
        assert mgr.is_allowed("p", "b1", "DangerZone") is False

    def test_invalid_regex_entry_never_matches(self):
        """非法正则条目恒不匹配（静默降级）"""
        mgr = self._make_mgr(
            {"platforms": {"p": {"modules": ["re:[bad"], "blocked": []}}, "bots": {}, "sessions": {}}
        )
        assert mgr.is_allowed("p", "b1", "anything") is False
