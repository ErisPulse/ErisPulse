"""
命令完整流程集成测试

测试从消息事件到命令解析、handler 执行、别名、权限、帮助文本、wait_reply 的完整流程。
"""

import pytest
import asyncio
from unittest.mock import patch, AsyncMock

from ErisPulse.Core.adapter import adapter
from ErisPulse.Core.Event import command
from ErisPulse.Core.Event import _clear_all_handlers


def _make_msg(text, **kwargs):
    data = {
        "id": "cmd_001",
        "time": 1712345678,
        "type": "message",
        "detail_type": "private",
        "platform": "cmd_test",
        "self": {"platform": "cmd_test", "user_id": "bot_cmd"},
        "user_id": "u1",
        "user_nickname": "User1",
        "message": [{"type": "text", "data": {"text": text}}],
        "alt_message": text,
    }
    data.update(kwargs)
    return data


@pytest.fixture
def clean_cmd():
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


class TestCommandFlowIntegration:
    """命令完整流程集成测试"""

    @pytest.mark.asyncio
    async def test_basic_command(self, clean_cmd):
        """基本命令执行"""
        received = []

        @command("hello", help="问候命令")
        async def hello(event):
            received.append(event)

        with patch("ErisPulse.Core.config.config.getConfig", return_value="/"):
            await adapter.emit(_make_msg("/hello"))

        assert len(received) == 1

    @pytest.mark.asyncio
    async def test_command_with_arguments(self, clean_cmd):
        """带参数的命令"""
        received = []

        @command("echo", help="回显")
        async def echo(event):
            received.append(event)

        with patch("ErisPulse.Core.config.config.getConfig", return_value="/"):
            await adapter.emit(_make_msg("/echo hello world 123"))

        assert len(received) == 1
        assert received[0].get("command", {}).get("name") == "echo"

    @pytest.mark.asyncio
    async def test_command_alias_execution(self, clean_cmd):
        """命令别名"""
        received = []

        @command("greet", aliases=["hi", "hey"], help="问候")
        async def greet(event):
            received.append(event)

        with patch("ErisPulse.Core.config.config.getConfig", return_value="/"):
            await adapter.emit(_make_msg("/hi"))
            await adapter.emit(_make_msg("/hey"))
            await adapter.emit(_make_msg("/greet"))

        assert len(received) == 3

    @pytest.mark.asyncio
    async def test_command_group(self, clean_cmd):
        """命令组"""
        received = []

        @command("admin.ban", group="admin", help="封禁用户")
        async def ban(event):
            received.append(event)

        assert "admin.ban" in command.groups.get("admin", [])
        assert command.groups["admin"] == ["admin.ban"]

    @pytest.mark.asyncio
    async def test_command_permission_check(self, clean_cmd):
        """命令权限检查"""
        received = []
        permission_result = True

        def perm_check(event):
            return permission_result

        @command("secure", permission=perm_check, help="安全命令")
        async def secure(event):
            received.append(event)

        with patch("ErisPulse.Core.config.config.getConfig", return_value="/"):
            await adapter.emit(_make_msg("/secure"))

        assert len(received) == 1

    @pytest.mark.asyncio
    async def test_command_permission_denied(self, clean_cmd):
        """命令权限拒绝"""
        received = []

        def perm_deny(event):
            return False

        @command("locked", permission=perm_deny, help="锁定命令")
        async def locked(event):
            received.append(event)

        with patch("ErisPulse.Core.config.config.getConfig", return_value="/"):
            await adapter.emit(_make_msg("/locked"))

        assert len(received) == 0

    @pytest.mark.asyncio
    async def test_command_help_text(self, clean_cmd):
        """命令帮助文本"""

        @command("test", help="测试帮助文本", usage="test [args]")
        async def test_cmd(event):
            pass

        help_text = command.help("test")
        assert "test" in help_text
        assert "测试帮助文本" in help_text
        assert "test [args]" in help_text

    @pytest.mark.asyncio
    async def test_all_commands_help(self, clean_cmd):
        """全部命令帮助"""

        @command("cmd1", help="命令1")
        async def c1(event):
            pass

        @command("cmd2", help="命令2", usage="cmd2 <arg>")
        async def c2(event):
            pass

        help_text = command.help()
        assert "cmd1" in help_text
        assert "cmd2" in help_text
        assert "命令1" in help_text
        assert "命令2" in help_text

    @pytest.mark.asyncio
    async def test_hidden_command_not_visible(self, clean_cmd):
        """隐藏命令不在可见列表中"""

        @command("visible", help="可见")
        async def v(event):
            pass

        @command("hidden", hidden=True, help="隐藏")
        async def h(event):
            pass

        visible = command.get_visible_commands()
        assert "visible" in visible
        assert "hidden" not in visible

    @pytest.mark.asyncio
    async def test_command_unregister(self, clean_cmd):
        """注销命令"""

        @command("temp", help="临时命令")
        async def temp_cmd(event):
            pass

        assert "temp" in command.commands
        command.unregister(temp_cmd)
        assert "temp" not in command.commands

    @pytest.mark.asyncio
    async def test_non_command_message_not_handled(self, clean_cmd):
        """非命令消息不触发命令 handler"""
        received = []

        @command("hello", help="问候")
        async def hello(event):
            received.append(event)

        with patch("ErisPulse.Core.config.config.getConfig", return_value="/"):
            await adapter.emit(_make_msg("just a normal message"))

        assert len(received) == 0

    @pytest.mark.asyncio
    async def test_wait_reply_timeout(self, clean_cmd):
        """wait_reply 超时返回 None"""
        with patch("ErisPulse.Core.adapter.adapter", new_callable=AsyncMock):
            result = await command.wait_reply(
                {"platform": "test", "user_id": "nonexist"},
                timeout=0.1,
            )
        assert result is None

    @pytest.mark.asyncio
    async def test_list_name_registration(self, clean_cmd):
        """列表形式注册多名称命令"""

        @command(["main", "alias1", "alias2"], help="多名称")
        async def multi(event):
            pass

        assert "main" in command.commands
        assert command.aliases.get("alias1") == "main"
        assert command.aliases.get("alias2") == "main"

    @pytest.mark.asyncio
    async def test_command_get_command(self, clean_cmd):
        """get_command 通过名称和别名获取"""

        @command("primary", aliases=["p"], help="主命令")
        async def primary(event):
            pass

        info = command.get_command("primary")
        assert info is not None
        assert info["help"] == "主命令"

        alias_info = command.get_command("p")
        assert alias_info is not None
        assert alias_info["main_name"] == "primary"
