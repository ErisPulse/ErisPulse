"""
命令权限 ACL 与消息通配符单元测试

测试命令用户黑白名单（event.overrides.acl + 判定链，命令名支持
glob）、命令实现参数覆写（event.overrides.command，帮助渲染与可见性用户优先），
以及 message 装饰器 / wait_reply 的 pattern（glob）与 regex 过滤。
"""

import asyncio
import importlib
from unittest.mock import patch

import pytest

from ErisPulse.Core.Event import overrides as overrides_mod
from ErisPulse.Core.Event.command import command as command_handler
from ErisPulse.Core.Event.interaction import interaction
from ErisPulse.Core.Event.message import message as message_handler
from ErisPulse.Core.scope import scope as scope_manager
from ErisPulse.runtime.context import current_owner

# importlib.import_module 返回真实子模块（Core.config 包属性被 ConfigManager 单例遮蔽）
config_module = importlib.import_module("ErisPulse.Core.config")


@pytest.fixture(autouse=True)
def clean_state():
    from ErisPulse.Core.adapter import adapter
    from ErisPulse.Core.Event import _clear_all_handlers

    _clear_all_handlers()
    command_handler.commands.clear()
    command_handler.aliases.clear()
    command_handler.groups.clear()
    command_handler.permissions.clear()
    interaction.clear()
    overrides_mod._command.clear()
    overrides_mod.clear()
    scope_manager._data["platforms"].clear()
    scope_manager._data["bots"].clear()
    message_handler.handler.handlers.clear()
    message_handler.handler._handler_map.clear()
    adapter._onebot_handlers.clear()
    adapter._raw_handlers.clear()
    adapter._onebot_middlewares.clear()
    adapter._bots.clear()
    yield
    _clear_all_handlers()
    command_handler.commands.clear()
    command_handler.aliases.clear()
    command_handler.groups.clear()
    command_handler.permissions.clear()
    interaction.clear()
    overrides_mod._command.clear()
    overrides_mod.clear()
    scope_manager._data["platforms"].clear()
    scope_manager._data["bots"].clear()
    message_handler.handler.handlers.clear()
    message_handler.handler._handler_map.clear()
    adapter._onebot_handlers.clear()
    adapter._raw_handlers.clear()
    adapter._onebot_middlewares.clear()
    adapter._bots.clear()


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


class TestCommandACL:
    """命令用户 ACL（event.overrides.acl，命令名支持 glob）"""

    @pytest.mark.asyncio
    async def test_deny_user_blocks(self):
        """deny 名单命中 → 拒绝执行并回复权限不足"""
        from ErisPulse.Core.adapter import adapter
        from ErisPulse.Core.Event import command

        received = []
        token = current_owner.set("ModuleA")
        try:

            @command("alpha")
            async def alpha(event):
                received.append("A")

        finally:
            current_owner.reset(token)

        @command("beta")
        async def beta(event):
            received.append("B")

        with patch("ErisPulse.Core.Event.overrides.set_erispulse_section"):
            overrides_mod.acl.set("beta", deny=["onebot11:u_bad"])
        with patch.object(config_module.config, "getConfig", return_value="/"):
            await adapter.emit(_msg("/beta", user_id="u_bad"))
            await asyncio.sleep(0.05)
            await adapter.emit(_msg("/beta", user_id="u_good"))
            await asyncio.sleep(0.05)

        assert received == ["B"]  # 仅 u_good 执行

    @pytest.mark.asyncio
    async def test_allow_list_restricts(self):
        """allow 名单非空 → 仅名单内用户可执行"""
        from ErisPulse.Core.adapter import adapter
        from ErisPulse.Core.Event import command

        received = []
        token = current_owner.set("ModuleA")
        try:

            @command("gamma")
            async def gamma(event):
                received.append(event.get("user_id"))

        finally:
            current_owner.reset(token)

        with patch("ErisPulse.Core.Event.overrides.set_erispulse_section"):
            overrides_mod.acl.set("gamma", allow=["onebot11:u_vip"])
        with patch.object(config_module.config, "getConfig", return_value="/"):
            await adapter.emit(_msg("/gamma", user_id="u_vip"))
            await asyncio.sleep(0.05)
            await adapter.emit(_msg("/gamma", user_id="u_normal"))
            await asyncio.sleep(0.05)

        assert received == ["u_vip"]

    @pytest.mark.asyncio
    async def test_deny_wins_over_allow(self):
        """同用户同时在 allow 与 deny 名单 → deny 优先"""
        from ErisPulse.Core.adapter import adapter
        from ErisPulse.Core.Event import command

        received = []
        token = current_owner.set("ModuleA")
        try:

            @command("delta")
            async def delta(event):
                received.append("D")

        finally:
            current_owner.reset(token)

        with patch("ErisPulse.Core.Event.overrides.set_erispulse_section"):
            overrides_mod.acl.set("delta", allow=["onebot11:u1"], deny=["onebot11:u1"])
        with patch.object(config_module.config, "getConfig", return_value="/"):
            await adapter.emit(_msg("/delta", user_id="u1"))
            await asyncio.sleep(0.05)

        assert received == []

    def test_glob_acl_matches_actual_command(self):
        """glob ACL 键匹配实际命令名"""
        with patch("ErisPulse.Core.Event.overrides.set_erispulse_section"):
            overrides_mod.acl.set("roll*", deny=["onebot11:u_bad"])
        assert overrides_mod.acl.get("roll_dice") == {
            "allow": [],
            "deny": ["onebot11:u_bad"],
        }
        assert overrides_mod.acl.is_allowed("roll_dice", "onebot11", "u_bad") is False
        assert overrides_mod.acl.is_allowed("roll_dice", "onebot11", "u_ok") is True

    def test_exact_acl_over_glob(self):
        """精确 ACL 键优先于 glob 键"""
        overrides_mod.acl.set("roll", deny=["p:u2"])
        overrides_mod.acl.set("roll*", allow=["p:u2"])
        assert overrides_mod.acl.is_allowed("roll", "p", "u2") is False

    def test_get_acl_returns_lists(self):
        """get_acl 返回 allow/deny 列表"""
        overrides_mod.acl.set("alpha", allow=["onebot11:u1"], deny=["onebot11:u2"])
        assert overrides_mod.acl.get("alpha") == {
            "allow": ["onebot11:u1"],
            "deny": ["onebot11:u2"],
        }

    def test_remove_acl(self):
        """remove_acl 清除 ACL 并持久化"""
        overrides_mod.acl.set("alpha", deny=["onebot11:u1"])
        with patch("ErisPulse.Core.Event.overrides.set_erispulse_section") as fake:
            assert overrides_mod.acl.delete("alpha") is True
        assert overrides_mod.acl.get("alpha") == {"allow": [], "deny": []}
        fake.assert_called_once()

    def test_allow_user_writes_control_commands(self):
        """acl.set 写入 event.overrides.acl"""
        with patch("ErisPulse.Core.Event.overrides.set_erispulse_section"):
            overrides_mod.acl.set("beta", allow=["onebot11:u1"])
        assert overrides_mod.acl.get("beta")["allow"] == ["onebot11:u1"]

    def test_acl_loaded_from_overrides_config(self):
        """配置热更新后 event.overrides.acl 与 acl_default_allow 生效"""
        with patch(
            "ErisPulse.runtime.get_event_config",
            return_value={"overrides": {"acl": {"roll": {"deny": ["p:u"]}}, "acl_default_allow": False}},
        ):
            overrides_mod._reload({})
        try:
            assert overrides_mod.acl.is_allowed("roll", "p", "u") is False
            assert overrides_mod.acl.is_allowed("other", "p", "u") is False  # 严格模式
            assert overrides_mod.acl.default_allow is False
        finally:
            overrides_mod._reload({})


class TestMessagePattern:
    """message 装饰器 pattern / regex 过滤"""

    @pytest.mark.asyncio
    async def test_on_message_pattern(self):
        """pattern 通配符：不匹配的消息不触发"""
        from ErisPulse.Core.adapter import adapter

        received = []
        token = current_owner.set("ModuleA")
        try:

            @message_handler.on_message(pattern="签到*")
            async def handler(event):
                received.append(event.get_text())

        finally:
            current_owner.reset(token)

        await adapter.emit(_msg("签到成功"))
        await asyncio.sleep(0.05)
        await adapter.emit(_msg("打卡失败"))
        await asyncio.sleep(0.05)

        assert received == ["签到成功"]

    @pytest.mark.asyncio
    async def test_on_message_regex(self):
        """regex：不匹配的消息不触发"""
        from ErisPulse.Core.adapter import adapter

        received = []
        token = current_owner.set("ModuleA")
        try:

            @message_handler.on_message(regex=r"\d+\s*元")
            async def handler(event):
                received.append(event.get_text())

        finally:
            current_owner.reset(token)

        await adapter.emit(_msg("优惠 5 元"))
        await asyncio.sleep(0.05)
        await adapter.emit(_msg("没有优惠"))
        await asyncio.sleep(0.05)

        assert received == ["优惠 5 元"]

    @pytest.mark.asyncio
    async def test_on_private_message_pattern(self):
        """on_private_message 同时满足 detail_type 与 pattern"""
        from ErisPulse.Core.adapter import adapter

        received = []
        token = current_owner.set("ModuleA")
        try:

            @message_handler.on_private_message(pattern="*密*")
            async def handler(event):
                received.append(event.get_text())

        finally:
            current_owner.reset(token)

        # 群聊命中 pattern 但 detail_type 不匹配
        await adapter.emit(_msg("机密信息", group_id="g1"))
        await asyncio.sleep(0.05)
        # 私聊命中 pattern
        await adapter.emit(_msg("机密信息"))
        await asyncio.sleep(0.05)

        assert received == ["机密信息"]

    @pytest.mark.asyncio
    async def test_pattern_and_regex_both_required(self):
        """pattern 与 regex 同时给定需同时满足"""
        from ErisPulse.Core.adapter import adapter

        received = []
        token = current_owner.set("ModuleA")
        try:

            @message_handler.on_message(pattern="*号", regex=r"^[0-9]+号$")
            async def handler(event):
                received.append(event.get_text())

        finally:
            current_owner.reset(token)

        await adapter.emit(_msg("123号"))
        await asyncio.sleep(0.05)
        await adapter.emit(_msg("abc号"))  # glob 命中但 regex 不命中
        await asyncio.sleep(0.05)

        assert received == ["123号"]


class TestWaitReplyPattern:
    """wait_reply 的 pattern / regex 过滤"""

    @pytest.mark.asyncio
    async def test_check_pending_reply_pattern(self):
        """_check_pending_reply 对 pattern 不匹配的回复继续等待"""
        from ErisPulse.Core.Event.wrapper import Event

        loop = asyncio.get_running_loop()
        future = loop.create_future()
        wait_event = _msg("初始消息", user_id="u1")
        interaction.register(wait_event, future, pattern="*abc*")
        wait_key = "onebot11:bot_x:u1:u1"

        # 不匹配的回复：不消费 future，仍保留等待条目
        await command_handler._check_pending_reply(Event(_msg("随便说点什么", user_id="u1")))
        assert wait_key in interaction._entries
        assert not future.done()

        # 匹配的回复：消费 future，清除等待条目
        await command_handler._check_pending_reply(
            Event(_msg("abc 在这里", user_id="u1"))
        )
        assert wait_key not in interaction._entries
        assert future.done()
        assert future.result().get("alt_message") == "abc 在这里"

    @pytest.mark.asyncio
    async def test_check_pending_reply_regex(self):
        """_check_pending_reply 对 regex 匹配的回复放行"""
        from ErisPulse.Core.Event.wrapper import Event

        loop = asyncio.get_running_loop()
        future = loop.create_future()
        wait_event = _msg("初始消息", user_id="u1")
        interaction.register(wait_event, future, regex=r"^\d+号$")
        wait_key = "onebot11:bot_x:u1:u1"

        await command_handler._check_pending_reply(Event(_msg("不是数字", user_id="u1")))
        assert wait_key in interaction._entries
        assert not future.done()

        await command_handler._check_pending_reply(Event(_msg("42号", user_id="u1")))
        assert wait_key not in interaction._entries
        assert future.done()


class TestHelpAppliesOverrides:
    """帮助渲染读取覆写系统命令参数（event.overrides.command 的 hidden / help / usage）"""

    def _register(self, name, help_text="原始帮助"):
        token = current_owner.set("ModuleA")
        try:

            @command_handler(name, help=help_text)
            async def _cmd(event):
                pass

        finally:
            current_owner.reset(token)

    def test_hidden_override_hides_from_help(self):
        """覆盖 hidden=True 后命令从帮助列表隐藏（用户优先），移除覆盖后恢复"""
        self._register("alpha")

        assert "alpha" in command_handler.help(show_hidden=False)
        assert "alpha" in command_handler.get_visible_commands()

        with patch("ErisPulse.Core.Event.overrides.set_erispulse_section"):
            overrides_mod.command.set("ModuleA", "alpha", hidden=True)

        assert "alpha" not in command_handler.help(show_hidden=False)
        assert "alpha" not in command_handler.get_visible_commands()
        # show_hidden=True 仍可列出
        assert "alpha" in command_handler.help(show_hidden=True)

        with patch("ErisPulse.Core.Event.overrides.set_erispulse_section"):
            overrides_mod.command.delete("ModuleA", "alpha")
        assert "alpha" in command_handler.help(show_hidden=False)

    def test_hidden_override_help_text_visible_with_show_hidden(self):
        """隐藏后经 show_hidden=True 渲染时使用覆盖后的 help/usage"""
        self._register("alpha", help_text="原始帮助")

        with patch("ErisPulse.Core.Event.overrides.set_erispulse_section"):
            overrides_mod.command.set("ModuleA", "alpha", hidden=True, help="覆盖帮助")

        text = command_handler.help("alpha")
        assert "覆盖帮助" in text
        text_all = command_handler.help(show_hidden=True)
        assert "覆盖帮助" in text_all
        assert "原始帮助" not in text_all

    def test_no_owner_command_unaffected(self):
        """无 owner（框架级）命令不受覆盖影响，正常渲染"""
        @command_handler("beta", help="框架命令")
        async def beta(event):
            pass

        assert "框架命令" in command_handler.help(show_hidden=False)
        assert "beta" in command_handler.get_visible_commands()

    def test_unrelated_override_does_not_hide(self):
        """其它命令的覆盖不影响本命令可见性"""
        self._register("alpha")
        with patch("ErisPulse.Core.Event.overrides.set_erispulse_section"):
            overrides_mod.command.set("ModuleA", "other_cmd", hidden=True)
        assert "alpha" in command_handler.get_visible_commands()

    def test_override_command_level_wins_over_module_level(self):
        """命令级覆盖优先于模块级同名标量（与键序无关）"""
        self._register("alpha", help_text="原始帮助")
        overrides_mod._command["ModuleA"] = {
            "help": "模块级帮助",
            "alpha": {"help": "命令级帮助"},
        }
        assert command_handler.get_command("alpha")["help"] == "命令级帮助"

    def test_help_filters_by_scope_module_dimension(self):
        """传入事件上下文时，被作用域禁用模块的命令不再列出（会话感知帮助）"""
        self._register("alpha")

        scope_manager.set("platforms.onebot11", {"blocked": ["ModuleA"]}, persist=False)

        ev = _msg("/help", group_id="g1")
        # 会话感知：该平台上 ModuleA 被禁，命令不出现在帮助中
        assert "alpha" not in command_handler.help(event=ev)
        assert "alpha" not in command_handler.get_visible_commands(platform="onebot11", session_id="g1")
        # 不传上下文：保持原行为（全量可见命令）
        assert "alpha" in command_handler.help()

        scope_manager.delete("platforms.onebot11", persist=False)
        assert "alpha" in command_handler.help(event=ev)

    def test_help_command_name_filtered_by_scope(self):
        """会话感知下查询被禁模块的单条命令按未注册处理（静默语义）"""
        self._register("alpha")

        scope_manager.set("platforms.onebot11", {"blocked": ["ModuleA"]}, persist=False)

        ev = _msg("/help", group_id="g1")
        # 模块在该会话不可用 → 按未注册处理（not_found 文案，不含真实帮助内容）
        hidden_text = command_handler.help("alpha", event=ev)
        assert "alpha" in hidden_text
        assert "原始帮助" not in hidden_text
        # 上下文解除后正常显示
        scope_manager.delete("platforms.onebot11", persist=False)
        assert "原始帮助" in command_handler.help("alpha", event=ev)


class TestContextAwareQueries:
    """命令查询 API 的统一上下文支持（event / 显式关键字，全部可选向后兼容）"""

    def _register(self, name, group=None, help_text="原始帮助"):
        token = current_owner.set("ModuleA")
        try:

            @command_handler(name, group=group, help=help_text)
            async def _cmd(event):
                pass

        finally:
            current_owner.reset(token)

    def _blocked(self):
        scope_manager.set("platforms.onebot11", {"blocked": ["ModuleA"]}, persist=False)

    def test_get_command_filters_by_event(self):
        """get_command 传入 event 时，该会话不可用模块的命令返回 None"""
        self._register("alpha")
        ev = _msg("/x", group_id="g1")

        assert command_handler.get_command("alpha") is not None
        self._blocked()
        assert command_handler.get_command("alpha", event=ev) is None
        # 不传上下文保持原行为
        assert command_handler.get_command("alpha") is not None
        # 显式关键字参数与 event 等价
        assert command_handler.get_command("alpha", platform="onebot11", session_id="g1") is None
        scope_manager.delete("platforms.onebot11", persist=False)
        assert command_handler.get_command("alpha", event=ev) is not None

    def test_get_command_returns_effective_info(self):
        """get_command 返回合并覆盖后的生效参数（运行时修改可见）"""
        self._register("alpha", help_text="原始帮助")

        raw = command_handler.get_command("alpha")
        assert raw["help"] == "原始帮助"

        overrides_mod.command.set("ModuleA", "alpha", help="覆盖帮助", master=True)

        effective = command_handler.get_command("alpha")
        assert effective["help"] == "覆盖帮助"
        assert effective["must_master"] is True

        with patch("ErisPulse.Core.Event.overrides.set_erispulse_section"):
            overrides_mod.command.delete("ModuleA", "alpha")
        assert command_handler.get_command("alpha")["help"] == "原始帮助"

    def test_get_commands_filters_by_event(self):
        """get_commands 传入上下文时过滤不可用模块的命令；不传时返回完整注册表"""
        self._register("alpha")
        ev = _msg("/x", group_id="g1")

        assert "alpha" in command_handler.get_commands()
        self._blocked()
        assert "alpha" not in command_handler.get_commands(event=ev)
        assert "alpha" in command_handler.get_commands()
        scope_manager.delete("platforms.onebot11", persist=False)

    def test_get_group_commands_filters_by_event(self):
        """get_group_commands 传入上下文时过滤不可用模块的命令"""
        self._register("alpha", group="g28")

        token = current_owner.set("OtherModule")
        try:

            @command_handler("beta", group="g28")
            async def beta(event):
                pass

        finally:
            current_owner.reset(token)

        ev = _msg("/x", group_id="g1")
        assert set(command_handler.get_group_commands("g28")) == {"alpha", "beta"}

        self._blocked()
        assert command_handler.get_group_commands("g28", event=ev) == ["beta"]
        scope_manager.delete("platforms.onebot11", persist=False)
        assert set(command_handler.get_group_commands("g28", event=ev)) == {"alpha", "beta"}

    def test_get_visible_commands_event_equivalent_to_kwargs(self):
        """get_visible_commands 的 event 与显式关键字参数等价"""
        self._register("alpha")
        ev = _msg("/x", group_id="g1")

        self._blocked()
        via_event = command_handler.get_visible_commands(event=ev)
        via_kwargs = command_handler.get_visible_commands(platform="onebot11", session_id="g1")
        assert "alpha" not in via_event
        assert via_event.keys() == via_kwargs.keys()
        scope_manager.delete("platforms.onebot11", persist=False)
        assert "alpha" in command_handler.get_visible_commands(event=ev)

