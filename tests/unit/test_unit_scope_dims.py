"""
作用域（scope）单元测试

覆盖三维：身份（四级绑定）、模块条目（glob / re: 正则）、出站动作（内联表细粒度），
以及运行时增删、配置热更新、统计、清空与事件分发入口丢弃。
命令 ACL 与实现参数覆写见 test_unit_command_acl.py；
实现参数覆盖见 test_unit_command_acl.py。
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
        "handlers": {},
        "actions": {},
    }
    base["identity"].update(bindings)
    mgr._data = base
    mgr._default_allow = default_allow
    mgr._invalidate_cache()
    return mgr


class TestIdentityCore:
    """身份维度核心功能"""

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
        mgr = _make_mgr({"adapters": {"p": {"allow": True}}, "bots": {"p": {"b1": {"deny": True}}}})
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
        mgr.set("identity.users.p.u1", {"deny": True}, persist=False)
        assert mgr.is_identity_allowed("p", user_id="u1") is False
        assert mgr.is_identity_allowed("p", user_id="u2") is True

    def test_bind_adapter_level(self):
        """bind_identity 适配器级（无 bot/session/user）"""
        mgr = _make_mgr({})
        mgr.set("identity.adapters.p", {"deny": True}, persist=False)
        assert mgr.is_identity_allowed("p", "b1") is False

    def test_bind_session_level(self):
        """bind_identity 会话级"""
        mgr = _make_mgr({})
        mgr.set("identity.sessions.p.g1", {"deny": True}, persist=False)
        assert mgr.is_identity_allowed("p", "b1", "g1") is False
        assert mgr.is_identity_allowed("p", "b1", "g2") is True

    def test_set_accepts_allow_or_deny(self):
        """覆写式 API：allow / deny 二选一直接写入"""
        mgr = _make_mgr({})
        mgr.set("identity.users.p.u1", {"allow": True}, persist=False)
        assert mgr.is_identity_allowed("p", user_id="u1") is True

    def test_unbind_runtime(self):
        """unbind_identity(persist=False) 移除绑定"""
        mgr = _make_mgr({"users": {"p": {"u1": {"deny": True}}}})
        assert mgr.delete("identity.users.p.u1", persist=False) is True
        assert mgr.is_identity_allowed("p", user_id="u1") is True
        assert mgr.delete("identity.users.p.u1", persist=False) is False

    def test_bind_persist_writes_config(self):
        """set(persist=True) 写入 scope.identity 配置"""
        mgr = _make_mgr({})
        written = {}

        def fake_update(new_config):
            written.update(new_config)

        with patch("ErisPulse.Core.scope.update_erispulse_config", side_effect=fake_update):
            mgr.set("identity.users.p.u1", {"deny": True})
        assert written["scope"]["identity"]["users"]["p"]["u1"] == {"deny": True}

    def test_unbind_persist_writes_config(self):
        """unbind_identity(persist=True) 整节替换写入以支持删除绑定"""
        mgr = _make_mgr({"users": {"p": {"u1": {"deny": True}}}})
        written = {}

        def fake_set(path, value):
            written[path] = value

        with patch("ErisPulse.Core.scope.set_erispulse_section", side_effect=fake_set):
            assert mgr.delete("identity.users.p.u1") is True
        # delete 以最近父节整节替换持久化（支持删除子键）
        assert written["scope.identity.users.p"] == {}
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
        stats = mgr.stats()
        assert stats["identity_checks"] == 2
        assert stats["identity_denied"] == 1


class TestBlockUser:
    """用户黑名单（便捷 API）"""

    def test_block_unblock_user(self):
        """block_user / unblock_user / is_user_blocked / get_blocked_users"""
        mgr = _make_mgr({})
        # patch 两个持久化入口，避免污染真实配置；内存态由 _apply_memory 保证
        with patch("ErisPulse.Core.scope.set_erispulse_section"), patch("ErisPulse.Core.scope.update_erispulse_config"):
            mgr.set("identity.users.p.u1", {"deny": True})
        assert mgr.is_identity_allowed("p", user_id="u1") is False
        assert mgr.is_identity_allowed("p", user_id="u2") is True
        assert mgr.get("identity.users.p") == {"u1": {"deny": True}}
        with patch("ErisPulse.Core.scope.set_erispulse_section"), patch("ErisPulse.Core.scope.update_erispulse_config"):
            assert mgr.delete("identity.users.p.u1") is True
        assert mgr.is_identity_allowed("p", user_id="u1") is True
        assert mgr.delete("identity.users.p.u1") is False

    def test_block_user_drops_events(self):
        """被拉黑用户的所有事件拒绝"""
        mgr = _make_mgr({})
        mgr.set("identity.users.p.u1", {"deny": True}, persist=False)
        assert mgr.is_identity_allowed("p", "b1", "g1", "u1") is False

    def test_block_only_deny_bindings_count(self):
        """allow 绑定不是拉黑：deny 才会拒绝"""
        mgr = _make_mgr({"users": {"p": {"u_allow": {"allow": True}}}})
        assert mgr.get("identity.users.p") == {"u_allow": {"allow": True}}
        assert mgr.is_identity_allowed("p", user_id="u_allow") is True


class TestActionsDimension:
    """出站维度（scope.actions，内联表细粒度规则）"""

    def _make_mgr_with_actions(self, actions: dict | None = None) -> ScopeManager:
        mgr = _make_mgr({})
        mgr._data["actions"] = dict(actions or {})
        mgr._invalidate_cache()
        return mgr

    def test_default_allow_when_unconfigured(self):
        """未配置任何限制时默认全放行"""
        mgr = self._make_mgr_with_actions()
        assert mgr.is_action_allowed("MyModule", "send") is True
        assert mgr.is_action_allowed("MyModule", "api") is True
        assert mgr.is_action_allowed("MyModule", "request") is True
        assert mgr.is_action_allowed("", "send") is True  # 空 owner 恒放行

    def test_deny_after_set_action_false(self):
        """set_action(False) 后拒绝该动作（等价 {deny: true}）"""
        mgr = self._make_mgr_with_actions()
        mgr.set("actions.MyModule.send", False, persist=False)
        assert mgr.is_action_allowed("MyModule", "send") is False
        assert mgr.is_action_allowed("MyModule", "api") is True  # 其它动作不受影响

    def test_actions_independent(self):
        """三个动作互不影响"""
        mgr = self._make_mgr_with_actions()
        mgr.set("actions.MyModule.api", False, persist=False)
        assert mgr.is_action_allowed("MyModule", "api") is False
        assert mgr.is_action_allowed("MyModule", "send") is True
        assert mgr.is_action_allowed("MyModule", "request") is True

    def test_other_module_unaffected(self):
        """限制只作用于指定模块"""
        mgr = self._make_mgr_with_actions()
        mgr.set("actions.ModuleA.send", False, persist=False)
        assert mgr.is_action_allowed("ModuleA", "send") is False
        assert mgr.is_action_allowed("ModuleB", "send") is True

    def test_unset_action_restores_allow(self):
        """unset_action 移除限制恢复默认允许"""
        mgr = self._make_mgr_with_actions()
        mgr.set("actions.MyModule.send", False, persist=False)
        assert mgr.delete("actions.MyModule.send", persist=False) is True
        assert mgr.is_action_allowed("MyModule", "send") is True
        assert mgr.delete("actions.MyModule.send", persist=False) is False

    def test_unset_action_all_for_owner(self):
        """unset_action(owner) 移除该模块全部动作限制"""
        mgr = self._make_mgr_with_actions()
        mgr.set("actions.MyModule.send", False, persist=False)
        mgr.set("actions.MyModule.api", False, persist=False)
        assert mgr.delete("actions.MyModule", persist=False) is True
        assert mgr.is_action_allowed("MyModule", "send") is True
        assert mgr.is_action_allowed("MyModule", "api") is True

    def test_invalid_action_raises(self):
        """未知动作抛 ValueError"""
        mgr = self._make_mgr_with_actions()
        # 未知动作键写入后无判定效果（_ACTION_NAMES 之外的键不参与判定）
        mgr.set("actions.MyModule.hack", False, persist=False)
        assert mgr.is_action_allowed("MyModule", "send") is True

    def test_invalid_rule_silently_ignored(self):
        """非法规则形态在判定层静默不匹配（覆写式 set 不做类型校验）"""
        mgr = self._make_mgr_with_actions()
        mgr.set("actions.MyModule.send", {"allow": 123}, persist=False)
        # allow 非 list → 规则非法 → 判定按无规则放行
        assert mgr.is_action_allowed("MyModule", "send") is True
        mgr.set("actions.MyModule.send", {"allow": "Text"}, persist=False)
        assert mgr.is_action_allowed("MyModule", "send", name="Text") is True

    def test_send_method_granular(self):
        """方法级细粒度：白名单 / 黑名单 / deny 优先"""
        mgr = self._make_mgr_with_actions({"Mod": {"send": {"allow": ["Text", "Image*"], "deny": ["File"]}}})
        assert mgr.is_action_allowed("Mod", "send") is False  # 无 name：白名单语义不放行
        assert mgr.is_action_allowed("Mod", "send", name="Text") is True
        assert mgr.is_action_allowed("Mod", "send", name="Image1") is True
        assert mgr.is_action_allowed("Mod", "send", name="File") is False

    def test_api_glob_rules(self):
        """api 动作条目支持 glob（查询放行 / 管理拒绝）"""
        mgr = self._make_mgr_with_actions({"Mod": {"api": {"allow": ["get_*"]}}})
        assert mgr.is_action_allowed("Mod", "api", name="get_group_info") is True
        assert mgr.is_action_allowed("Mod", "api", name="set_group_name") is False

    def test_get_action_rules(self):
        """get 读取三动作当前规则（bool 原样存储，判定层归一化）"""
        mgr = self._make_mgr_with_actions()
        mgr.set("actions.MyModule.send", False, persist=False)
        mgr.set("actions.MyModule.api", {"allow": ["get_*"]}, persist=False)
        rules = mgr.get("actions.MyModule")
        assert rules == {
            "send": False,
            "api": {"allow": ["get_*"]},
        }
        # 判定层归一化：bool False 等价全禁
        assert mgr.is_action_allowed("MyModule", "send") is False

    def test_stats_counted(self):
        """is_action_allowed 累计 action_checks/action_denied"""
        mgr = self._make_mgr_with_actions()
        mgr.set("actions.MyModule.send", False, persist=False)
        mgr.is_action_allowed("MyModule", "send")  # denied
        mgr.is_action_allowed("MyModule", "api")  # allowed
        assert mgr._stats["action_checks"] == 2
        assert mgr._stats["action_denied"] == 1

    def test_persist_writes_config(self):
        """set_action 持久化到 scope.actions 配置节（规范化规则）"""
        mgr = self._make_mgr_with_actions()
        with patch("ErisPulse.Core.scope.update_erispulse_config") as fake_update:
            mgr.set("actions.MyModule.send", False)
        fake_update.assert_called_once()
        written = fake_update.call_args[0][0]
        assert written["scope"]["actions"]["MyModule"]["send"] is False

    def test_action_cache_invalidated_on_set(self):
        """set_action 后判定缓存失效，立即生效"""
        mgr = self._make_mgr_with_actions()
        assert mgr.is_action_allowed("Mod", "send", name="Text") is True  # 缓存 True
        mgr.set("actions.Mod.send", False, persist=False)
        assert mgr.is_action_allowed("Mod", "send", name="Text") is False

    def test_actions_config_validation(self):
        """配置校验：非法规则 / 未知动作告警并忽略，合法保留"""
        mgr = _make_mgr({})
        with patch(
            "ErisPulse.runtime.get_config",
            return_value={"actions": {"M": {"send": {"allow": 123}, "hack": False, "api": False}}},
        ):
            mgr._on_config_updated({})
        assert mgr._data["actions"]["M"] == {"api": {"deny": True}}


class TestModuleDimensionPatterns:
    """模块维度的 glob / re: 条目"""

    def test_module_glob_whitelist(self):
        """modules 白名单支持 glob"""
        mgr = _make_mgr({})
        mgr._data["platforms"]["p"] = {"modules": ["Tool*"]}
        assert mgr.is_allowed("p", None, "ToolBox") is True
        assert mgr.is_allowed("p", None, "Chat") is False

    def test_module_regex_blocklist(self):
        """blocked 支持 re: 正则"""
        mgr = _make_mgr({})
        mgr._data["platforms"]["p"] = {"blocked": ["re:^danger"]}
        assert mgr.is_allowed("p", None, "DangerBot") is False
        assert mgr.is_allowed("p", None, "Chat") is True

    def test_module_case_insensitive(self):
        """模块名匹配大小写不敏感"""
        mgr = _make_mgr({})
        mgr._data["platforms"]["p"] = {"modules": ["chat"]}
        assert mgr.is_allowed("p", None, "CHAT") is True


class TestGeneral:
    """通用：统计 / 拓扑 / 清空"""

    def test_list_and_clear(self):
        """list_bindings() 与 clear()（作用域三维结构）"""
        mgr = _make_mgr({"users": {"p": {"u1": {"deny": True}}}})
        assert mgr.topology()["identity"]["users"]["p"]["u1"] == {"deny": True}
        mgr.clear()
        assert mgr.topology() == {
            "platforms": {},
            "bots": {},
            "sessions": {},
            "identity": {"adapters": {}, "bots": {}, "sessions": {}, "users": {}},
            "actions": {},
        }

    def test_topology_scope_dimensions(self):
        """get_topology() 返回作用域三维结构"""
        mgr = _make_mgr({})
        topo = mgr.topology()
        for key in ("platforms", "bots", "sessions", "identity", "handlers", "actions"):
            assert key in topo
        assert "commands" not in topo

    def test_reset_stats(self):
        """reset_stats 清零全部统计"""
        mgr = _make_mgr({})
        mgr.is_identity_allowed("p")
        mgr.reset_stats()
        assert all(v == 0 for v in mgr.stats().values())

    def test_stats_module_only(self):
        """get_stats 仅含作用域统计键"""
        mgr = _make_mgr({})
        stats = mgr.stats()
        for key in ("module_calls", "module_filtered", "identity_checks", "identity_denied", "action_checks", "action_denied", "cache_hits", "cache_misses"):
            assert key in stats
        assert "command_checks" not in stats


class TestScopeConfigValidation:
    """scope 配置格式校验：坏节忽略 + 告警，好节保留"""

    def test_bad_bucket_type_ignored(self):
        """platforms 配置非 dict 时告警并忽略，其余节保留"""
        mgr = ScopeManager()
        with patch(
            "ErisPulse.runtime.get_config",
            return_value={"platforms": "oops", "bots": {"p": {"b": {"modules": ["A"], "blocked": []}}}},
        ):
            mgr._on_config_updated({})
        assert mgr._data["platforms"] == {}
        assert mgr.is_allowed("p", "b", "A") is True

    def test_unknown_key_warned_once(self):
        """未知顶层键（拼写错误）告警且只告警一次，不影响其它配置"""
        mgr = ScopeManager()
        assert mgr.is_identity_allowed("p", user_id="u1") is True
        with patch(
            "ErisPulse.runtime.get_config",
            return_value={"alow": {"p": {}}, "platforms": {"p": {"modules": ["A"], "blocked": []}}},
        ):
            mgr._on_config_updated({})
            mgr._on_config_updated({})
        assert mgr.is_allowed("p", "b", "A") is True
        # 去重：同一路径只记录一次告警
        assert len([k for k in mgr._warned if "alow" in k]) == 1


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
        scope_singleton._data["identity"] = {
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
        scope_singleton._data["identity"] = {
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

        scope_singleton.set("identity.users.onebot11.u_bad", {"deny": True}, persist=False)
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

        scope_singleton.set("identity.sessions.onebot11.g_bad", {"deny": True}, persist=False)
        await adapter.emit(self._make_msg("hi", group_id="g_bad"))
        await asyncio.sleep(0.05)
        await adapter.emit(self._make_msg("hi", group_id="g_good"))
        await asyncio.sleep(0.05)

        assert received == ["A"]  # 仅 g_good 触发



class TestTypedDimensionAPI:
    """维度化参数方法（set/get/delete_module·identity·handler·action，IDE 友好签名）"""

    def test_module_set_get_delete(self):
        """模块维度：三层路径定位 + 判定联动"""
        mgr = _make_mgr({})
        mgr.set_module("p", bot_id="b1", modules=["Chat"], blocked=["Danger*"])
        assert mgr.get_module("p", bot_id="b1") == {"modules": ["Chat"], "blocked": ["Danger*"]}
        assert mgr.is_allowed("p", "b1", "Chat") is True
        assert mgr.is_allowed("p", "b1", "DangerBot") is False
        assert mgr.delete_module("p", bot_id="b1") is True
        assert mgr.get_module("p", bot_id="b1") is None
        assert mgr.is_allowed("p", "b1", "Chat") is True  # 恢复默认放行

    def test_module_merge_write_time_union(self):
        """set_module(merge=True) 与该级现有绑定逐条目并集"""
        mgr = _make_mgr({})
        mgr.set_module("p", modules=["Chat"], blocked=["A"])
        mgr.set_module("p", modules=["Music"], merge=True)
        mgr.set_module("p", blocked=["B"], merge=True)
        assert mgr.get_module("p") == {"modules": ["Chat", "Music"], "blocked": ["A", "B"]}
        # merge=False 整体替换
        mgr.set_module("p", modules=["Only"])
        assert mgr.get_module("p") == {"modules": ["Only"], "blocked": []}

    def test_identity_levels_and_validation(self):
        """身份维度：四级路径 + allow/deny 校验"""
        mgr = _make_mgr({})
        mgr.set_identity("p", user_id="u_bad", deny=True)
        assert mgr.get_identity("p", user_id="u_bad") == {"deny": True}
        assert mgr.is_identity_allowed("p", user_id="u_bad") is False
        mgr.set_identity("p", session_id="g1", allow=True)
        assert mgr.is_identity_allowed("p", session_id="g1") is True
        # deny 优先于 allow（同给时）
        mgr.set_identity("p", user_id="u1", allow=True, deny=True)
        assert mgr.get_identity("p", user_id="u1") == {"deny": True}
        # 均缺省报错
        with pytest.raises(ValueError):
            mgr.set_identity("p")
        assert mgr.delete_identity("p", user_id="u_bad") is True
        assert mgr.get_identity("p", user_id="u_bad") is None

    def test_action_replace_semantics(self):
        """出站维度：整体替换语义（不残留旧键）+ 全空删除"""
        mgr = _make_mgr({})
        mgr.set_action("Mod", "send", deny=True)
        assert mgr.get_action("Mod", "send") == {"deny": True}
        # 重设为白名单：deny=True 不残留
        mgr.set_action("Mod", "send", allow=["Text"])
        assert mgr.get_action("Mod", "send") == {"allow": ["Text"]}
        assert mgr.is_action_allowed("Mod", "send", name="Text") is True
        assert mgr.is_action_allowed("Mod", "send", name="File") is False
        # 字符串单条目简写
        mgr.set_action("Mod", "api", deny="set_*")
        assert mgr.get_action("Mod", "api") == {"deny": ["set_*"]}
        assert mgr.is_action_allowed("Mod", "api", name="set_name") is False
        # 全空参数 = 移除规则
        mgr.set_action("Mod", "send")
        assert mgr.get_action("Mod", "send") is None
        assert mgr.is_action_allowed("Mod", "send") is True
        # action=None 移除整模块
        mgr.set_action("Mod", "request", deny=True)
        assert mgr.delete_action("Mod") is True
        assert mgr.is_action_allowed("Mod", "request") is True

    def test_action_unknown_raises(self):
        """未知动作与空模块报错"""
        mgr = _make_mgr({})
        with pytest.raises(ValueError):
            mgr.set_action("Mod", "hack", deny=True)
        with pytest.raises(ValueError):
            mgr.set_action("", "send", deny=True)

    def test_typed_persist_writes_config(self):
        """参数化方法 persist=True 落盘到对应配置节"""
        mgr = _make_mgr({})
        written = {}

        def fake_update(new_config):
            written.update(new_config)

        with patch("ErisPulse.Core.scope.update_erispulse_config", side_effect=fake_update):
            mgr.set_module("p", modules=["Chat"])
            mgr.set_identity("p", user_id="u1", deny=True)
            mgr.set_action("Mod", "send", deny=True)
        tree = written["scope"]
        assert tree["platforms"]["p"] == {"modules": ["Chat"], "blocked": []}
        assert tree["identity"]["users"]["p"]["u1"] == {"deny": True}
        assert tree["actions"]["Mod"]["send"] == {"deny": True}
