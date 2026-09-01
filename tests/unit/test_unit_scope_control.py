"""
统一控制面（scope）单元测试

覆盖五维：模块（三级绑定 + glob/re: 条目）、身份（四级绑定，原事件准入）、
命令（ACL + glob）、处理器（文本过滤）、覆盖（实现参数），
以及运行时增删、配置热更新、统计与拓扑。
"""

import asyncio
from unittest.mock import patch

import pytest

from ErisPulse.Core.scope import ScopeManager


def _make_mgr(bindings: dict, default_allow: bool = True) -> ScopeManager:
    """构造测试管理器（identity 绑定挂载到 identity 子树）"""
    mgr = ScopeManager()
    base = {
        "platforms": {},
        "bots": {},
        "sessions": {},
        "identity": {
            "adapters": {},
            "bots": {},
            "sessions": {},
            "users": {},
        },
        "commands": {},
        "handlers": {},
        "overrides": {},
    }
    base["identity"].update(bindings)
    mgr._bindings = base
    mgr._default_allow = default_allow
    return mgr


class TestIdentityCore:
    """身份维度核心功能（原事件准入迁移）"""

    def test_default_allow_all(self):
        """无绑定（默认）时所有事件放行"""
        mgr = _make_mgr({})
        assert mgr.is_identity_allowed("p") is True
        assert mgr.is_identity_allowed("p", "b1", "g1", "u1") is True

    def test_default_deny_strict_mode(self):
        """default_allow=False 时未配置绑定即拒绝"""
        mgr = _make_mgr({}, default_allow=False)
        assert mgr.is_identity_allowed("p", "b1", "g1", "u1") is False

    def test_adapter_deny(self):
        """适配器级 deny：该平台所有事件拒绝"""
        mgr = _make_mgr({"adapters": {"p": {"deny": True}}})
        assert mgr.is_identity_allowed("p", "b1", "g1", "u1") is False
        assert mgr.is_identity_allowed("p2") is True

    def test_bot_deny_overrides_adapter_allow(self):
        """Bot 级 deny 覆盖适配器级 allow"""
        mgr = _make_mgr(
            {"adapters": {"p": {"allow": True}}, "bots": {"p": {"b1": {"deny": True}}}}
        )
        assert mgr.is_identity_allowed("p", "b1") is False
        assert mgr.is_identity_allowed("p", "b2") is True

    def test_session_deny(self):
        """会话级 deny：该群所有事件拒绝"""
        mgr = _make_mgr({"sessions": {"p": {"g1": {"deny": True}}}})
        assert mgr.is_identity_allowed("p", "b1", "g1") is False
        assert mgr.is_identity_allowed("p", "b1", "g2") is True

    def test_user_deny(self):
        """用户级 deny：该用户所有事件拒绝"""
        mgr = _make_mgr({"users": {"p": {"u1": {"deny": True}}}})
        assert mgr.is_identity_allowed("p", "b1", "g1", "u1") is False
        assert mgr.is_identity_allowed("p", "b1", "g1", "u2") is True

    def test_user_allow_exception(self):
        """用户级 allow 做"例外放行"：上级 deny 但该用户放行"""
        mgr = _make_mgr(
            {
                "adapters": {"p": {"deny": True}},
                "users": {"p": {"u_admin": {"allow": True}}},
            }
        )
        assert mgr.is_identity_allowed("p", "b1", "g1", "u_admin") is True
        assert mgr.is_identity_allowed("p", "b1", "g1", "u_other") is False

    def test_specificity_order(self):
        """特异性解析：用户 > 会话 > Bot > 适配器，取第一个已配置的"""
        mgr = _make_mgr(
            {
                "adapters": {"p": {"deny": True}},
                "bots": {"p": {"b1": {"allow": True}}},
                "sessions": {"p": {"g1": {"deny": True}}},
                "users": {"p": {"u1": {"allow": True}}},
            }
        )
        # 用户级（最具体）
        assert mgr.is_identity_allowed("p", "b1", "g1", "u1") is True
        # 会话级
        assert mgr.is_identity_allowed("p", "b1", "g1", "u2") is False
        # Bot 级
        assert mgr.is_identity_allowed("p", "b1", "g2", "u2") is True
        # 适配器级
        assert mgr.is_identity_allowed("p", "b2", "g3", "u3") is False

    def test_deny_precedence_over_allow(self):
        """同一绑定内 deny 优先于 allow"""
        mgr = _make_mgr({"users": {"p": {"u1": {"allow": True, "deny": True}}}})
        assert mgr.is_identity_allowed("p", user_id="u1") is False

    def test_identity_glob_pattern_keys(self):
        """身份绑定键支持 glob（如 spam_*）"""
        mgr = _make_mgr({"users": {"p": {"spam_*": {"deny": True}}}})
        assert mgr.is_identity_allowed("p", user_id="spam_01") is False
        assert mgr.is_identity_allowed("p", user_id="normal") is True

    def test_identity_regex_pattern_keys(self):
        """身份绑定键支持 re: 正则"""
        mgr = _make_mgr({"users": {"p": {"re:^bot[0-9]+$": {"deny": True}}}})
        assert mgr.is_identity_allowed("p", user_id="bot123") is False
        assert mgr.is_identity_allowed("p", user_id="human") is True

    def test_bind_runtime(self):
        """bind_identity(persist=False) 仅运行时生效"""
        mgr = _make_mgr({})
        mgr.bind_identity("p", user_id="u1", deny=True, persist=False)
        assert mgr.is_identity_allowed("p", user_id="u1") is False
        assert mgr.is_identity_allowed("p", user_id="u2") is True

    def test_bind_adapter_level(self):
        """bind_identity 适配器级（无 bot/session/user）"""
        mgr = _make_mgr({})
        mgr.bind_identity("p", deny=True, persist=False)
        assert mgr.is_identity_allowed("p", "b1") is False

    def test_bind_session_level(self):
        """bind_identity 会话级"""
        mgr = _make_mgr({})
        mgr.bind_identity("p", session_id="g1", deny=True, persist=False)
        assert mgr.is_identity_allowed("p", "b1", "g1") is False
        assert mgr.is_identity_allowed("p", "b1", "g2") is True

    def test_bind_requires_policy(self):
        """bind_identity 未指定 allow/deny 时报错"""
        mgr = _make_mgr({})
        with pytest.raises(ValueError):
            mgr.bind_identity("p", persist=False)

    def test_unbind_runtime(self):
        """unbind_identity(persist=False) 移除绑定"""
        mgr = _make_mgr({"users": {"p": {"u1": {"deny": True}}}})
        assert mgr.unbind_identity("p", user_id="u1", persist=False) is True
        assert mgr.is_identity_allowed("p", user_id="u1") is True
        assert mgr.unbind_identity("p", user_id="u1", persist=False) is False

    def test_bind_persist_writes_config(self):
        """bind_identity(persist=True) 写入 scope.identity 配置"""
        mgr = _make_mgr({})
        written = {}

        def fake_update(new_config):
            written.update(new_config)

        with patch("ErisPulse.Core.scope.update_erispulse_config", side_effect=fake_update):
            mgr.bind_identity("p", user_id="u1", deny=True)
        assert written["scope"]["identity"]["users"]["p"]["u1"] == {"deny": True}

    def test_unbind_persist_writes_config(self):
        """unbind_identity(persist=True) 整节替换写入以支持删除绑定"""
        mgr = _make_mgr({"users": {"p": {"u1": {"deny": True}}}})
        written = {}

        def fake_set(path, value):
            written[path] = value

        with patch("ErisPulse.Core.scope.set_erispulse_section", side_effect=fake_set):
            assert mgr.unbind_identity("p", user_id="u1") is True
        assert "users" in written["scope.identity"]
        assert written["scope.identity"]["users"] == {}
        assert mgr.is_identity_allowed("p", user_id="u1") is True

    def test_config_hot_reload(self):
        """配置变更后身份绑定缓存重建"""
        mgr = _make_mgr({})
        with patch(
            "ErisPulse.runtime.get_config",
            return_value={"identity": {"users": {"p": {"u1": {"deny": True}}}}},
        ):
            mgr._on_config_updated({})
        assert mgr.is_identity_allowed("p", user_id="u1") is False
        assert mgr.is_identity_allowed("p", user_id="u2") is True

    def test_identity_stats(self):
        """get_stats 统计 identity_checks / identity_denied"""
        mgr = _make_mgr({"users": {"p": {"u1": {"deny": True}}}})
        mgr.reset_stats()
        mgr.is_identity_allowed("p", user_id="u1")
        mgr.is_identity_allowed("p", user_id="u2")
        stats = mgr.get_stats()
        assert stats["identity_checks"] == 2
        assert stats["identity_denied"] == 1


class TestBlockUser:
    """用户黑名单（便捷 API）"""

    def test_block_unblock_user(self):
        """block_user / unblock_user / is_user_blocked / get_blocked_users"""
        mgr = _make_mgr({})
        # patch 两个持久化入口，避免污染真实配置；内存态由 _apply_memory 保证
        with patch("ErisPulse.Core.scope.set_erispulse_section"), patch(
            "ErisPulse.Core.scope.update_erispulse_config"
        ):
            mgr.block_user("p", "u1")
        assert mgr.is_user_blocked("p", "u1") is True
        assert mgr.is_user_blocked("p", "u2") is False
        assert mgr.get_blocked_users() == {"p": ["u1"]}
        with patch("ErisPulse.Core.scope.set_erispulse_section"), patch(
            "ErisPulse.Core.scope.update_erispulse_config"
        ):
            assert mgr.unblock_user("p", "u1") is True
        assert mgr.is_user_blocked("p", "u1") is False
        assert mgr.unblock_user("p", "u1") is False

    def test_block_user_drops_events(self):
        """被拉黑用户的所有事件拒绝"""
        mgr = _make_mgr({})
        mgr.block_user("p", "u1", persist=False)
        assert mgr.is_identity_allowed("p", "b1", "g1", "u1") is False

    def test_block_only_deny_bindings_count(self):
        """get_blocked_users 只统计 deny 绑定"""
        mgr = _make_mgr({"users": {"p": {"u_allow": {"allow": True}}}})
        assert mgr.get_blocked_users() == {}


class TestCommandDimension:
    """命令维度（ACL）"""

    def test_is_command_allowed_no_acl(self):
        """未配置 ACL 遵循 default_allow"""
        mgr = _make_mgr({})
        assert mgr.is_command_allowed("roll", "p", "u1") is True
        mgr._default_allow = False
        assert mgr.is_command_allowed("roll", "p", "u1") is False

    def test_is_command_allowed_deny(self):
        """deny 命中拒绝"""
        mgr = _make_mgr({})
        mgr._bindings["commands"]["roll"] = {"deny": ["p:u1"]}
        assert mgr.is_command_allowed("roll", "p", "u1") is False
        assert mgr.is_command_allowed("roll", "p", "u2") is True

    def test_is_command_allowed_allow_list(self):
        """allow 白名单非空时仅名单内可执行"""
        mgr = _make_mgr({})
        mgr._bindings["commands"]["roll"] = {"allow": ["p:u1"]}
        assert mgr.is_command_allowed("roll", "p", "u1") is True
        assert mgr.is_command_allowed("roll", "p", "u2") is False

    def test_acl_glob_command_name(self):
        """命令名支持 glob 匹配 ACL"""
        mgr = _make_mgr({})
        mgr._bindings["commands"]["roll*"] = {"deny": ["p:u1"]}
        assert mgr.is_command_allowed("roll_dice", "p", "u1") is False
        assert mgr.is_command_allowed("roll_dice", "p", "u2") is True
        assert mgr.get_acl("roll_dice") == {"allow": [], "deny": ["p:u1"]}

    def test_acl_exact_over_pattern(self):
        """精确 ACL 键优先于 glob 键"""
        mgr = _make_mgr({})
        mgr._bindings["commands"]["roll"] = {"deny": ["p:u2"]}
        mgr._bindings["commands"]["roll*"] = {"allow": ["p:u2"]}
        # 精确键：u2 被 deny
        assert mgr.is_command_allowed("roll", "p", "u2") is False

    def test_allow_deny_user_mutate(self):
        """allow_user / deny_user 运行时增删（persist=False）"""
        mgr = _make_mgr({})
        mgr.allow_user("roll", "p", "u1", persist=False)
        assert mgr.get_acl("roll") == {"allow": ["p:u1"], "deny": []}
        mgr.deny_user("roll", "p", "u2", persist=False)
        assert mgr.get_acl("roll") == {"allow": ["p:u1"], "deny": ["p:u2"]}
        assert mgr.is_command_allowed("roll", "p", "u2") is False

    def test_remove_acl(self):
        """remove_acl 按 glob 清除 ACL"""
        mgr = _make_mgr({})
        mgr.allow_user("roll*", "p", "u1", persist=False)
        assert mgr.remove_acl("roll_dice", persist=False) is True
        assert mgr.get_acl("roll_dice") == {"allow": [], "deny": []}

    def test_acl_persist_writes_scope_commands(self):
        """allow_user(persist=True) 写入 scope.commands"""
        mgr = _make_mgr({})
        with patch("ErisPulse.Core.scope.set_erispulse_section") as fake:
            mgr.allow_user("roll", "p", "u1")
        fake.assert_called_once()
        assert mgr.get_acl("roll") == {"allow": ["p:u1"], "deny": []}


class TestHandlerDimension:
    """处理器/文本维度"""

    def test_no_handler_config(self):
        """未配置 handlers 时处理器条件为 None"""
        mgr = _make_mgr({})
        assert mgr.handler_condition("MyModule") is None

    def test_handler_pattern_condition(self):
        """handler_condition 生成文本条件"""
        mgr = _make_mgr({})
        mgr._bindings["handlers"]["MyModule"] = {"pattern": "签到*"}
        cond = mgr.handler_condition("MyModule")
        assert cond({"alt_message": "签到成功"}) is True
        assert cond({"alt_message": "打卡"}) is False

    def test_handler_regex_condition(self):
        """handler regex 配置（剥离 re: 前缀）"""
        mgr = _make_mgr({})
        mgr._bindings["handlers"]["MyModule"] = {"regex": "re:^\\d+号$"}
        cond = mgr.handler_condition("MyModule")
        assert cond({"alt_message": "42号"}) is True
        assert cond({"alt_message": "abc号"}) is False

    def test_bind_unbind_handler(self):
        """bind_handler / unbind_handler"""
        mgr = _make_mgr({})
        with patch("ErisPulse.Core.scope.set_erispulse_section"):
            mgr.bind_handler("MyModule", pattern="签到*")
        assert mgr._bindings["handlers"]["MyModule"]["pattern"] == "签到*"
        with patch("ErisPulse.Core.scope.set_erispulse_section"):
            assert mgr.unbind_handler("MyModule") is True
        assert mgr.handler_condition("MyModule") is None
        assert mgr.unbind_handler("MyModule") is False


class TestOverrideDimension:
    """实现参数覆盖维度"""

    def test_get_override_empty(self):
        """未配置覆盖时返回空字典"""
        mgr = _make_mgr({})
        assert mgr.get_override("MyModule", "restart") == {}

    def test_get_override_command_level_wins(self):
        """命令级覆盖优先于模块级"""
        mgr = _make_mgr({})
        mgr._bindings["overrides"]["MyModule"] = {
            "hidden": True,
            "restart": {"master": True},
        }
        assert mgr.get_override("MyModule", "restart") == {
            "hidden": True,
            "master": True,
        }
        assert mgr.get_override("MyModule") == {"hidden": True}

    def test_apply_override(self):
        """apply_override 合并覆盖到默认参数"""
        mgr = _make_mgr({})
        mgr._bindings["overrides"]["MyModule"] = {"restart": {"master": True}}
        merged = mgr.apply_override(
            "MyModule", "restart", {"master": False, "hidden": False}
        )
        assert merged == {"master": True, "hidden": False}

    def test_override_mutate(self):
        """override / remove_override"""
        mgr = _make_mgr({})
        with patch("ErisPulse.Core.scope.set_erispulse_section"):
            mgr.override("MyModule", "restart", master=True, hidden=True)
        assert mgr.get_override("MyModule", "restart")["master"] is True
        with patch("ErisPulse.Core.scope.set_erispulse_section"):
            assert mgr.remove_override("MyModule", "restart") is True
        assert mgr.get_override("MyModule", "restart") == {}
        assert mgr.remove_override("MyModule", "restart") is False


class TestModuleDimensionPatterns:
    """模块维度的 glob / re: 条目"""

    def test_module_glob_whitelist(self):
        """modules 白名单支持 glob"""
        mgr = _make_mgr({})
        mgr._bindings["platforms"]["p"] = {"modules": ["Tool*"]}
        assert mgr.is_allowed("p", None, "ToolBox") is True
        assert mgr.is_allowed("p", None, "Chat") is False

    def test_module_regex_blocklist(self):
        """blocked 支持 re: 正则"""
        mgr = _make_mgr({})
        mgr._bindings["platforms"]["p"] = {"blocked": ["re:^danger"]}
        assert mgr.is_allowed("p", None, "DangerBot") is False
        assert mgr.is_allowed("p", None, "Chat") is True

    def test_module_case_insensitive(self):
        """模块名匹配大小写不敏感"""
        mgr = _make_mgr({})
        mgr._bindings["platforms"]["p"] = {"modules": ["chat"]}
        assert mgr.is_allowed("p", None, "CHAT") is True


class TestGeneral:
    """通用：统计 / 拓扑 / 清空"""

    def test_list_and_clear(self):
        """list_bindings() 与 clear()（五维结构）"""
        mgr = _make_mgr({"users": {"p": {"u1": {"deny": True}}}})
        assert (
            mgr.list_bindings()["identity"]["users"]["p"]["u1"] == {"deny": True}
        )
        mgr.clear()
        assert mgr.list_bindings() == {
            "platforms": {},
            "bots": {},
            "sessions": {},
            "identity": {"adapters": {}, "bots": {}, "sessions": {}, "users": {}},
            "commands": {},
            "handlers": {},
            "overrides": {},
        }

    def test_topology_five_dimensions(self):
        """get_topology() 返回五维结构"""
        mgr = _make_mgr({})
        topo = mgr.get_topology()
        for key in ("platforms", "bots", "sessions", "identity", "commands", "handlers", "overrides"):
            assert key in topo

    def test_command_stats(self):
        """get_stats 统计 command_checks / command_denied"""
        mgr = _make_mgr({})
        mgr._bindings["commands"]["roll"] = {"deny": ["p:u1"]}
        mgr.reset_stats()
        mgr.is_command_allowed("roll", "p", "u1")
        mgr.is_command_allowed("roll", "p", "u2")
        stats = mgr.get_stats()
        assert stats["command_checks"] == 2
        assert stats["command_denied"] == 1

    def test_reset_stats(self):
        """reset_stats 清零全部统计"""
        mgr = _make_mgr({})
        mgr.is_identity_allowed("p")
        mgr.reset_stats()
        assert all(v == 0 for v in mgr.get_stats().values())


class TestScopeDispatch:
    """身份维度在事件分发入口的丢弃测试"""

    @pytest.fixture(autouse=True)
    def clean_handlers(self):
        from ErisPulse.Core.adapter import adapter
        from ErisPulse.Core.Event import _clear_all_handlers
        from ErisPulse.Core.scope import scope as scope_singleton

        _clear_all_handlers()
        adapter._onebot_handlers.clear()
        adapter._raw_handlers.clear()
        adapter._onebot_middlewares.clear()
        adapter._bots.clear()
        scope_singleton._bindings["identity"] = {
            "adapters": {},
            "bots": {},
            "sessions": {},
            "users": {},
        }
        scope_singleton._invalidate_cache()
        yield
        _clear_all_handlers()
        adapter._onebot_handlers.clear()
        adapter._raw_handlers.clear()
        adapter._onebot_middlewares.clear()
        adapter._bots.clear()
        scope_singleton._bindings["identity"] = {
            "adapters": {},
            "bots": {},
            "sessions": {},
            "users": {},
        }
        scope_singleton._invalidate_cache()

    @staticmethod
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

    @pytest.mark.asyncio
    async def test_blocked_user_event_fully_dropped(self):
        """被拉黑用户的消息完全不触发任何处理器"""
        from ErisPulse.Core.Event import message
        from ErisPulse.Core.scope import scope as scope_singleton
        from ErisPulse.runtime.context import current_owner

        received = []
        token = current_owner.set("ModuleA")
        try:

            @message.on_message()
            async def handler(event):
                received.append("A")

        finally:
            current_owner.reset(token)

        from ErisPulse.Core.adapter import adapter

        scope_singleton.block_user("onebot11", "u_bad", persist=False)
        # adapter 入口与 base 兜底都从 ErisPulse.Core.scope 取单例
        await adapter.emit(self._make_msg("hi", user_id="u_bad"))
        await asyncio.sleep(0.05)
        await adapter.emit(self._make_msg("hi", user_id="u_good"))
        await asyncio.sleep(0.05)

        assert received == ["A"]  # u_bad 被丢弃，u_good 正常触发

    @pytest.mark.asyncio
    async def test_session_denied_event_dropped(self):
        """被准入拒绝的群消息不触发处理器"""
        from ErisPulse.Core.Event import message
        from ErisPulse.Core.scope import scope as scope_singleton
        from ErisPulse.runtime.context import current_owner

        received = []
        token = current_owner.set("ModuleA")
        try:

            @message.on_message()
            async def handler(event):
                received.append("A")

        finally:
            current_owner.reset(token)

        from ErisPulse.Core.adapter import adapter

        scope_singleton.bind_identity(
            "onebot11", session_id="g_bad", deny=True, persist=False
        )
        await adapter.emit(self._make_msg("hi", group_id="g_bad"))
        await asyncio.sleep(0.05)
        await adapter.emit(self._make_msg("hi", group_id="g_good"))
        await asyncio.sleep(0.05)

        assert received == ["A"]  # 仅 g_good 触发
