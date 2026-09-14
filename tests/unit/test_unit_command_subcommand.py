"""
命令子命令（空格分隔多 token 命令名）单元测试

测试命令匹配层的最长前缀匹配：父命令与子命令并存时优先命中子命令、
仅注册子命令时正常触发（历史版本中此类注册可入帮助列表但永远无法触发）、
多 token 别名、事件载荷携带命令全名、ACL/权限链对全名生效、
子命令未声明 permission 时沿父链继承最近声明权限的祖先，以及注销后的
token 数缓存重算与父命令回落。
"""

import asyncio
import importlib
from unittest.mock import patch

import pytest

from ErisPulse.Core.Event import overrides as overrides_mod
from ErisPulse.Core.Event.command import command as command_handler
from ErisPulse.Core.Event.interaction import interaction
from ErisPulse.runtime.context import current_owner

# importlib.import_module 返回真实子模块（Core.config 包属性被 ConfigManager 单例遮蔽）
config_module = importlib.import_module("ErisPulse.Core.config")
# 同理：Core.Event.command 包属性被 command 单例遮蔽，patch 时必须用真实模块对象
command_module = importlib.import_module("ErisPulse.Core.Event.command")


@pytest.fixture(autouse=True)
def clean_state():
    from ErisPulse.Core.adapter import adapter
    from ErisPulse.Core.Event import _clear_all_handlers
    from ErisPulse.Core.Event.message import message as message_handler

    _clear_all_handlers()
    command_handler.commands.clear()
    command_handler.aliases.clear()
    command_handler.groups.clear()
    command_handler.permissions.clear()
    command_handler._max_name_tokens = 1
    command_handler.block = True
    interaction.clear()
    overrides_mod._command.clear()
    overrides_mod.clear()
    adapter._onebot_handlers.clear()
    adapter._raw_handlers.clear()
    adapter._onebot_middlewares.clear()
    adapter._bots.clear()
    message_handler.handler.handlers.clear()
    message_handler.handler._handler_map.clear()
    yield
    _clear_all_handlers()
    command_handler.commands.clear()
    command_handler.aliases.clear()
    command_handler.groups.clear()
    command_handler.permissions.clear()
    command_handler._max_name_tokens = 1
    command_handler.block = True
    interaction.clear()
    overrides_mod._command.clear()
    overrides_mod.clear()
    adapter._onebot_handlers.clear()
    adapter._raw_handlers.clear()
    adapter._onebot_middlewares.clear()
    adapter._bots.clear()
    message_handler.handler.handlers.clear()
    message_handler.handler._handler_map.clear()


def _msg(text, platform="onebot11", bot_id="bot_x", user_id="u1", group_id=None):
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


async def _dispatch(text, **kwargs):
    """以 "/" 命令前缀分发消息事件并等待命令分发完成"""
    from ErisPulse.Core.adapter import adapter

    with patch.object(config_module.config, "getConfig", return_value="/"):
        await adapter.emit(_msg(text, **kwargs))
        await asyncio.sleep(0.05)


class TestLongestPrefixMatch:
    """最长前缀匹配：子命令全名优先于父命令 + 剩余 token 作为参数"""

    @pytest.mark.asyncio
    async def test_parent_only_unchanged(self):
        """仅注册父命令 → 行为与历史版本一致（子命令 token 落入 args）"""
        calls = []

        @command_handler("admin")
        async def admin(event):
            calls.append((event.get_command_name(), event.get_command_args()))

        await _dispatch("/admin add x")
        assert calls == [("admin", ["add", "x"])]
        assert command_handler._max_name_tokens == 1

    @pytest.mark.asyncio
    async def test_child_wins_over_parent(self):
        """父子并存 → 优先命中子命令全名，剩余 token 作为参数"""
        calls = []

        @command_handler("admin")
        async def admin(event):
            calls.append((event.get_command_name(), event.get_command_args()))

        @command_handler("admin add")
        async def admin_add(event):
            calls.append((event.get_command_name(), event.get_command_args()))

        await _dispatch("/admin add x")
        assert calls == [("admin add", ["x"])]

        calls.clear()
        await _dispatch("/admin remove x")
        assert calls == [("admin", ["remove", "x"])]  # 未注册的子命令回落父命令

    @pytest.mark.asyncio
    async def test_child_only_now_triggers(self):
        """仅注册子命令（父命令不存在）→ 正常触发（历史版本永不匹配）"""
        calls = []

        @command_handler("admin add")
        async def admin_add(event):
            calls.append((event.get_command_name(), event.get_command_args()))

        assert command_handler._max_name_tokens == 2
        await _dispatch("/admin add x")
        assert calls == [("admin add", ["x"])]

    @pytest.mark.asyncio
    async def test_three_level_nesting(self):
        """三级嵌套命令名按最长匹配命中"""
        calls = []

        @command_handler("admin user ban")
        async def ban(event):
            calls.append((event.get_command_name(), event.get_command_args()))

        await _dispatch("/admin user ban u1 7d")
        assert calls == [("admin user ban", ["u1", "7d"])]

    @pytest.mark.asyncio
    async def test_case_insensitive_multi_token(self):
        """大小写不敏感模式 → 多 token 候选整体归一后匹配"""
        calls = []
        original = command_handler.case_sensitive
        command_handler.case_sensitive = False
        try:

            @command_handler("admin add")
            async def admin_add(event):
                calls.append(event.get_command_name())

            await _dispatch("/ADMIN ADD x")
            assert calls == ["admin add"]
        finally:
            command_handler.case_sensitive = original

    @pytest.mark.asyncio
    async def test_case_sensitive_mode_respects_exact_case(self):
        """大小写敏感模式 → 多 token 候选按原样精确匹配"""
        calls = []
        original = command_handler.case_sensitive
        command_handler.case_sensitive = True
        try:

            @command_handler("Admin Add")
            async def admin_add(event):
                calls.append(event.get_command_name())

            await _dispatch("/Admin Add x")
            assert calls == ["Admin Add"]

            calls.clear()
            await _dispatch("/admin add x")
            assert calls == []  # 小写形式不命中
        finally:
            command_handler.case_sensitive = original

    @pytest.mark.asyncio
    async def test_no_match_does_not_execute(self):
        """完全未注册的命令 → 不触发任何处理器"""
        calls = []

        @command_handler("admin add")
        async def admin_add(event):
            calls.append(event.get_command_name())

        await _dispatch("/admin remove x")
        assert calls == []

    @pytest.mark.asyncio
    async def test_single_token_alias_of_subcommand(self):
        """子命令的单 token 别名正常解析"""
        calls = []

        @command_handler("admin add", aliases=["aa"])
        async def admin_add(event):
            calls.append((event.get_command_name(), event.get_command_args()))

        await _dispatch("/aa x")
        assert calls == [("admin add", ["x"])]

    @pytest.mark.asyncio
    async def test_multi_token_alias(self):
        """多 token 别名参与最长前缀匹配"""
        calls = []

        @command_handler("admin add", aliases=["a add"])
        async def admin_add(event):
            calls.append((event.get_command_name(), event.get_command_args()))

        assert command_handler._max_name_tokens == 2
        await _dispatch("/a add x")
        assert calls == [("admin add", ["x"])]

    @pytest.mark.asyncio
    async def test_event_payload_carries_full_name(self):
        """事件命令信息（get_command_name / get_command_args / get_command_raw）携带全名语义"""
        payloads = []

        @command_handler("admin add")
        async def admin_add(event):
            payloads.append(
                {
                    "name": event.get_command_name(),
                    "args": event.get_command_args(),
                    "raw": event.get_command_raw(),
                    "is_command": event.is_command(),
                }
            )

        await _dispatch("/admin add x")
        assert payloads == [
            {"name": "admin add", "args": ["x"], "raw": "admin add x", "is_command": True}
        ]

    @pytest.mark.asyncio
    async def test_lifecycle_hook_receives_full_name(self):
        """command.matched / command.executed 钩子载荷携带命令全名"""
        from ErisPulse.Core.lifecycle import lifecycle

        matched, executed = [], []

        async def on_matched(data):
            matched.append(data["command"])

        async def on_executed(data):
            executed.append(data["command"])

        lifecycle.register("command.matched", on_matched)
        lifecycle.register("command.executed", on_executed)
        try:

            @command_handler("admin add")
            async def admin_add(event):
                pass

            await _dispatch("/admin add x")
            assert matched == ["admin add"]
            assert executed == ["admin add"]
        finally:
            lifecycle.unregister("command.matched", on_matched)
            lifecycle.unregister("command.executed", on_executed)


class TestSubcommandPermission:
    """子命令权限继承：未声明 permission 时沿父链继承最近声明权限的祖先"""

    @pytest.mark.asyncio
    async def test_inherits_ancestor_permission_denied(self):
        """父命令声明拒绝型权限 → 子命令被同一权限保护"""
        calls = []

        def deny(event):
            return False

        @command_handler("admin", permission=deny)
        async def admin(event):
            calls.append("admin")

        @command_handler("admin add")
        async def admin_add(event):
            calls.append("admin add")

        await _dispatch("/admin add x")
        assert calls == []  # 继承的权限拒绝执行

    @pytest.mark.asyncio
    async def test_inherits_ancestor_permission_allowed(self):
        """父命令声明放行型权限 → 子命令正常执行"""
        calls = []

        def allow(event):
            return True

        @command_handler("admin", permission=allow)
        async def admin(event):
            calls.append("admin")

        @command_handler("admin add")
        async def admin_add(event):
            calls.append(event.get_command_name())

        await _dispatch("/admin add x")
        assert calls == ["admin add"]

    @pytest.mark.asyncio
    async def test_child_own_permission_overrides_inheritance(self):
        """子命令自身声明权限 → 覆盖继承"""
        calls = []

        def deny(event):
            return False

        def allow(event):
            return True

        @command_handler("admin", permission=deny)
        async def admin(event):
            calls.append("admin")

        @command_handler("admin add", permission=allow)
        async def admin_add(event):
            calls.append(event.get_command_name())

        await _dispatch("/admin add x")
        assert calls == ["admin add"]

    @pytest.mark.asyncio
    async def test_walkthrough_intermediate_ancestor(self):
        """中间祖先未声明权限 → 继续上溯到声明权限的祖先"""
        calls = []

        def deny(event):
            return False

        @command_handler("admin", permission=deny)
        async def admin(event):
            calls.append("admin")

        @command_handler("admin user")
        async def admin_user(event):
            calls.append("admin user")

        @command_handler("admin user ban")
        async def ban(event):
            calls.append("admin user ban")

        await _dispatch("/admin user ban u1")
        assert calls == []  # 跳过无权限的 admin user，继承 admin 的拒绝型权限

    @pytest.mark.asyncio
    async def test_no_ancestor_no_inheritance(self):
        """无任何已注册祖先 → 不继承，子命令无权限即放行（与历史行为一致）"""
        calls = []

        @command_handler("admin add")
        async def admin_add(event):
            calls.append(event.get_command_name())

        await _dispatch("/admin add x")
        assert calls == ["admin add"]

    @pytest.mark.asyncio
    async def test_ancestor_without_permission_is_transparent(self):
        """祖先已注册但未声明权限且更上层不存在 → 子命令放行"""
        calls = []

        @command_handler("admin")
        async def admin(event):
            calls.append("admin")

        @command_handler("admin add")
        async def admin_add(event):
            calls.append(event.get_command_name())

        await _dispatch("/admin add x")
        assert calls == ["admin add"]  # 命中子命令，父命令处理器不执行


class TestSubcommandACLAndScope:
    """子命令全名参与 ACL / master 检查"""

    @pytest.mark.asyncio
    async def test_acl_glob_matches_full_name(self):
        """ACL glob 规则对子命令全名生效"""
        from ErisPulse.Core.adapter import adapter

        calls = []
        token = current_owner.set("ModuleA")
        try:

            @command_handler("admin add")
            async def admin_add(event):
                calls.append(event.get_command_name())

        finally:
            current_owner.reset(token)

        with patch("ErisPulse.Core.Event.overrides.set_erispulse_section"):
            overrides_mod.acl.set("admin*", deny=["onebot11:u_bad"])
        with patch.object(config_module.config, "getConfig", return_value="/"):
            await adapter.emit(_msg("/admin add x", user_id="u_bad"))
            await asyncio.sleep(0.05)
            await adapter.emit(_msg("/admin add x", user_id="u_good"))
            await asyncio.sleep(0.05)

        assert calls == ["admin add"]  # 仅 u_good 执行

    @pytest.mark.asyncio
    async def test_master_flag_on_subcommand(self):
        """子命令声明 master=True → 非主人被拒绝"""
        calls = []

        @command_handler("admin add", master=True)
        async def admin_add(event):
            calls.append(event.get_command_name())

        await _dispatch("/admin add x")
        assert calls == []  # 测试环境中无主人身份，拒绝执行


class TestUnregisterAndCache:
    """注销后的 token 缓存重算与父命令回落"""

    @pytest.mark.asyncio
    async def test_unregister_child_falls_back_to_parent(self):
        """注销子命令 → /admin add 回落为父命令 + args，缓存重算"""
        calls = []

        @command_handler("admin")
        async def admin(event):
            calls.append((event.get_command_name(), event.get_command_args()))

        @command_handler("admin add")
        async def admin_add(event):
            calls.append(event.get_command_name())

        assert command_handler.unregister(admin_add) is True  # 命令映射移除成功即返回 True
        assert command_handler.get_command("admin add") is None
        assert command_handler._max_name_tokens == 1

        await _dispatch("/admin add x")
        assert calls == [("admin", ["add", "x"])]

    @pytest.mark.asyncio
    async def test_unregister_by_owner_removes_subcommands(self):
        """按归属者注销 → 子命令一并移除且缓存重算"""
        token = current_owner.set("ModuleA")
        try:

            @command_handler("admin add")
            async def admin_add(event):
                pass

        finally:
            current_owner.reset(token)

        assert command_handler._max_name_tokens == 2
        assert command_handler.unregister_by_owner("ModuleA") == 1
        assert command_handler._max_name_tokens == 1
        assert command_handler.get_command("admin add") is None

    def test_clear_commands_resets_cache(self):
        """全量清理 → token 缓存复位"""
        token = current_owner.set("ModuleA")
        try:

            @command_handler("admin add")
            async def admin_add(event):
                pass

        finally:
            current_owner.reset(token)

        assert command_handler._max_name_tokens == 2
        command_handler._clear_commands()
        assert command_handler._max_name_tokens == 1


class TestArgsOriginalCasing:
    """参数与 raw 载荷保留用户原始大小写，仅命令名匹配做归一"""

    @pytest.mark.asyncio
    async def test_case_insensitive_mode_preserves_args(self):
        """大小写不敏感模式 → 参数/原文保留原始大小写（历史版本会被整体小写）"""
        calls = []
        original = command_handler.case_sensitive
        command_handler.case_sensitive = False
        try:

            @command_handler("echo")
            async def echo(event):
                calls.append((event.get_command_args(), event.get_command_raw()))

            await _dispatch("/echo Hello WORLD MiXeD")
            assert calls == [(["Hello", "WORLD", "MiXeD"], "echo Hello WORLD MiXeD")]
        finally:
            command_handler.case_sensitive = original

    @pytest.mark.asyncio
    async def test_case_sensitive_mode_preserves_args(self):
        """大小写敏感模式 → 参数/原文保留原始大小写（行为不变）"""
        calls = []
        original = command_handler.case_sensitive
        command_handler.case_sensitive = True
        try:

            @command_handler("echo")
            async def echo(event):
                calls.append((event.get_command_args(), event.get_command_raw()))

            await _dispatch("/echo Hello WORLD")
            assert calls == [(["Hello", "WORLD"], "echo Hello WORLD")]
        finally:
            command_handler.case_sensitive = original

    @pytest.mark.asyncio
    async def test_case_insensitive_match_with_mixed_case_command(self):
        """大小写不敏感模式 → 命令名大小写随意、参数保留原文（子命令路径）"""
        calls = []
        original = command_handler.case_sensitive
        command_handler.case_sensitive = False
        try:

            @command_handler("admin add")
            async def admin_add(event):
                calls.append((event.get_command_name(), event.get_command_args()))

            await _dispatch("/ADMIN ADD Hello")
            assert calls == [("admin add", ["Hello"])]
        finally:
            command_handler.case_sensitive = original


class TestDuplicateRegistrationWarning:
    """跨模块重名注册告警；同 owner 重注册（懒激活占位流程）不告警"""

    def test_different_owner_warns_and_last_wins(self):
        with patch.object(command_module, "logger") as log_mock:
            token_a = current_owner.set("ModuleA")
            try:

                @command_handler("dup")
                async def dup_a(event):
                    pass

            finally:
                current_owner.reset(token_a)

            token_b = current_owner.set("ModuleB")
            try:

                @command_handler("dup")
                async def dup_b(event):
                    pass

            finally:
                current_owner.reset(token_b)

        assert log_mock.warning.called  # 输出重名覆盖告警
        assert command_handler.commands["dup"]["func"] is dup_b  # 后注册者生效

    def test_same_owner_reregister_no_warning(self):
        with patch.object(command_module, "logger") as log_mock:
            token = current_owner.set("ModuleA")
            try:

                @command_handler("dup2")
                async def dup2_a(event):
                    pass

                @command_handler("dup2")
                async def dup2_b(event):
                    pass

            finally:
                current_owner.reset(token)

        assert not log_mock.warning.called  # 同 owner 重注册（如懒激活占位替换）不告警
        assert command_handler.commands["dup2"]["func"] is dup2_b


class TestHelpGrouping:
    """/help 子命令在可见父命令下缩进展示"""

    def test_children_indented_under_parent(self):
        @command_handler("admin", help="管理")
        async def admin(event):
            pass

        @command_handler("admin add", help="添加")
        async def admin_add(event):
            pass

        @command_handler("admin user", help="用户管理")
        async def admin_user(event):
            pass

        @command_handler("admin user ban", help="封禁")
        async def ban(event):
            pass

        @command_handler("standalone", help="独立命令")
        async def standalone(event):
            pass

        prefix = command_handler.prefix[0] if isinstance(command_handler.prefix, list) else command_handler.prefix
        text = command_handler.help()
        lines = {
            line.strip().split(" - ")[0]: line
            for line in text.splitlines()
            if " - " in line
        }

        # 顶层条目：2 空格缩进（list_item 自带）
        assert lines[f"{prefix}admin"].startswith("  " + prefix)
        assert lines[f"{prefix}standalone"].startswith("  " + prefix)
        # 子命令缩进深度按可见祖先链递增（父 2 格 → 子 4 格 → 孙 6 格）
        assert lines[f"{prefix}admin add"].startswith("    " + prefix)
        assert lines[f"{prefix}admin user ban"].startswith("      " + prefix)
        # 父命令条目位于子命令之前
        assert text.index(f"{prefix}admin -") < text.index(f"{prefix}admin add")

    def test_orphan_subcommand_renders_flat(self):
        """父命令不可见（未注册）→ 子命令按顶层条目平铺展示"""

        @command_handler("orphan add", help="无父命令")
        async def orphan_add(event):
            pass

        text = command_handler.help()
        orphan_line = next(line for line in text.splitlines() if "orphan add" in line)
        assert orphan_line.startswith("  ")  # 顶层缩进
        assert not orphan_line.startswith("    ")  # 不按子命令缩进

    def test_child_registered_before_parent_still_nested(self):
        """子命令先于父命令注册 → 父命令仍显示在子命令之前"""

        @command_handler("admin add", help="添加")
        async def admin_add(event):
            pass

        @command_handler("admin", help="管理")
        async def admin(event):
            pass

        prefix = command_handler.prefix[0] if isinstance(command_handler.prefix, list) else command_handler.prefix
        text = command_handler.help()
        assert text.index(f"{prefix}admin -") < text.index(f"{prefix}admin add")  # 父先子后
        child_line = next(line for line in text.splitlines() if f"{prefix}admin add" in line)
        assert child_line.startswith("    ")  # 子命令缩进不变


class TestClaimOnMatch:
    """命令命中即认领：拒绝路径不再漏给消息处理器（双重响应歧义消除）"""

    @staticmethod
    def _register_observer(received: list):
        from ErisPulse.Core.Event.message import message as message_handler

        @message_handler.on_message()
        async def observer(event):
            received.append(event.get("alt_message"))

        return observer

    @pytest.mark.asyncio
    async def test_permission_denied_no_double_response(self):
        """权限拒绝 → 命令不执行，消息处理器也不再收到命令文本"""
        calls, observed = [], []
        self._register_observer(observed)

        def deny(event):
            return False

        @command_handler("locked", permission=deny)
        async def locked(event):
            calls.append("locked")

        await _dispatch("/locked x")
        assert calls == []       # 命令被拒
        assert observed == []    # 命中即认领，不漏给消息处理器

    @pytest.mark.asyncio
    async def test_master_denied_no_double_response(self):
        """master 拒绝 → 同样认领阻断"""
        calls, observed = [], []
        self._register_observer(observed)

        @command_handler("secret", master=True)
        async def secret(event):
            calls.append("secret")

        await _dispatch("/secret")
        assert calls == []
        assert observed == []

    @pytest.mark.asyncio
    async def test_scope_denied_silent_but_claimed(self):
        """scope 拒绝 → 静默（不回复）但仍认领阻断"""
        from ErisPulse.Core.scope import scope as scope_manager

        calls, observed = [], []
        self._register_observer(observed)
        token = current_owner.set("ModuleA")
        try:

            @command_handler("scoped")
            async def scoped(event):
                calls.append("scoped")

        finally:
            current_owner.reset(token)

        scope_manager.set_module("onebot11", blocked=["ModuleA"], persist=False)
        try:
            await _dispatch("/scoped")
            assert calls == []       # 静默不执行
            assert observed == []    # 不漏给消息处理器
        finally:
            scope_manager.delete_module("onebot11", persist=False)

    @pytest.mark.asyncio
    async def test_block_false_lets_observers_see(self):
        """ErisPulse.event.command.block=false → 仅认领不阻断，观察者可见"""
        calls, observed = [], []
        self._register_observer(observed)
        command_handler.block = False
        try:

            def deny(event):
                return False

            @command_handler("locked", permission=deny)
            async def locked(event):
                calls.append("locked")

            await _dispatch("/locked x")
            assert calls == []               # 命令仍被拒
            assert observed == ["/locked x"]  # 观察者可见（仅认领）
        finally:
            command_handler.block = True

    @pytest.mark.asyncio
    async def test_unmatched_still_reaches_observers(self):
        """未命中任何命令 → 照旧漏给消息处理器（行为不变）"""
        observed = []
        self._register_observer(observed)

        @command_handler("known")
        async def known(event):
            pass

        await _dispatch("/unknown x")
        assert observed == ["/unknown x"]


class TestAliasPrecedence:
    """命令名优先于别名：消除别名静默劫持"""

    @pytest.mark.asyncio
    async def test_command_wins_over_alias(self):
        """命令 "b" 与别名 "b"→"a" 冲突 → 命令 b 生效，别名不注册"""
        calls = []

        @command_handler("b")
        async def b_cmd(event):
            calls.append("b")

        @command_handler("a", aliases=["b"])
        async def a_cmd(event):
            calls.append("a")

        assert "b" not in command_handler.aliases  # 别名未注册
        await _dispatch("/b")
        assert calls == ["b"]

    @pytest.mark.asyncio
    async def test_new_command_removes_stale_alias(self):
        """后注册的命令名遮蔽既有别名 → 死别名被移除，命令可达"""
        calls = []

        @command_handler("a", aliases=["x"])
        async def a_cmd(event):
            calls.append("a")

        assert command_handler.aliases.get("x") == "a"

        @command_handler("x")
        async def x_cmd(event):
            calls.append("x")

        assert "x" not in command_handler.aliases
        await _dispatch("/x")
        assert calls == ["x"]

    @pytest.mark.asyncio
    async def test_duplicate_alias_first_wins(self):
        """同名别名重复注册 → 保持先注册者生效"""
        calls = []

        @command_handler("a1", aliases=["s"])
        async def a1(event):
            calls.append("a1")

        @command_handler("a2", aliases=["s"])
        async def a2(event):
            calls.append("a2")

        assert command_handler.aliases.get("s") == "a1"
        await _dispatch("/s")
        assert calls == ["a1"]


class TestAliasConflictWarnings:
    """别名冲突三类注册均告警"""

    def test_alias_conflicts_command_warns(self):
        with patch.object(command_module, "logger") as log_mock:

            @command_handler("b")
            async def b_cmd(event):
                pass

            @command_handler("a", aliases=["b"])
            async def a_cmd(event):
                pass

        assert log_mock.warning.called

    def test_name_conflicts_alias_warns_and_removes(self):
        with patch.object(command_module, "logger") as log_mock:

            @command_handler("a", aliases=["x"])
            async def a_cmd(event):
                pass

            @command_handler("x")
            async def x_cmd(event):
                pass

        assert log_mock.warning.called
        assert "x" not in command_handler.aliases

    def test_alias_vs_alias_warns(self):
        with patch.object(command_module, "logger") as log_mock:

            @command_handler("a1", aliases=["s"])
            async def a1(event):
                pass

            @command_handler("a2", aliases=["s"])
            async def a2(event):
                pass

        assert log_mock.warning.called
        assert command_handler.aliases.get("s") == "a1"
