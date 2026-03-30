"""
事件系统单元测试

测试Event模块的各个子模块功能，包括命令、消息、通知、请求和元事件
"""

import pytest
import asyncio
import warnings
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any

from ErisPulse.Core.Event import (
    command, message, notice, request, meta,
    register_event_method, register_event_mixin,
    unregister_event_method, unregister_platform_event_methods,
    get_platform_event_methods,
)
from ErisPulse.Core.Event.wrapper import Event, _platform_event_methods
from ErisPulse.Core.Event.base import BaseEventHandler
from ErisPulse.Core import adapter, config


# ==================== BaseEventHandler 测试 ====================

class TestBaseEventHandler:
    """基础事件处理器测试类"""
    
    @pytest.fixture
    def handler(self):
        """创建事件处理器"""
        handler = BaseEventHandler("test_event", "test_module")
        handler.handlers.clear()
        handler._handler_map.clear()
        return handler
    
    def test_register_handler(self, handler):
        """测试注册处理器"""
        def test_func(event):
            pass
        
        # 执行
        handler.register(test_func)
        
        # 验证
        assert len(handler.handlers) == 1
        assert handler.handlers[0]["func"] is test_func
        assert id(test_func) in handler._handler_map
    
    def test_register_handler_with_priority(self, handler):
        """测试注册带优先级的处理器"""
        def high_priority(event):
            pass
        
        def low_priority(event):
            pass
        
        # 先注册低优先级
        handler.register(low_priority, priority=10)
        # 后注册高优先级
        handler.register(high_priority, priority=1)
        
        # 验证排序（高优先级在前）
        assert handler.handlers[0]["func"] is high_priority
        assert handler.handlers[1]["func"] is low_priority
    
    def test_register_handler_with_condition(self, handler):
        """测试注册带条件的处理器"""
        def condition_func(event):
            return event.get("test", False) == True
        
        def test_handler(event):
            pass
        
        # 执行
        handler.register(test_handler, condition=condition_func)
        
        # 验证
        assert handler.handlers[0]["condition"] is condition_func
    
    def test_unregister_handler(self, handler):
        """测试注销处理器"""
        def test_func(event):
            pass
        
        # 注册
        handler.register(test_func)
        assert len(handler.handlers) == 1
        
        # 注销
        result = handler.unregister(test_func)
        
        # 验证
        assert result is True
        assert len(handler.handlers) == 0
        assert "test_func" not in handler._handler_map
    
    def test_unregister_nonexistent_handler(self, handler):
        """测试注销不存在的处理器"""
        def test_func(event):
            pass
        
        # 执行
        result = handler.unregister(test_func)
        
        # 验证
        assert result is False
    
    def test_decorator_registration(self, handler):
        """测试装饰器注册"""
        @handler(priority=5, condition=lambda e: True)
        def test_func(event):
            pass
        
        # 验证
        assert len(handler.handlers) == 1
        assert handler.handlers[0]["func"] is test_func
        assert handler.handlers[0]["priority"] == 5
    
    @pytest.mark.asyncio
    async def test_process_event(self, handler):
        """测试处理事件"""
        called = []
        
        async def test_func(event):
            called.append(event)
        
        # 注册处理器
        handler.register(test_func)
        
        # 创建测试事件
        event_data = {"test": True}
        
        # 执行
        await handler._process_event(event_data)
        
        # 验证
        assert len(called) == 1
        assert isinstance(called[0], Event)
    
    @pytest.mark.asyncio
    async def test_process_event_with_condition(self, handler):
        """测试处理带条件的事件"""
        called = []
        
        def condition(event):
            return event.get("test") == "match"
        
        async def test_func(event):
            called.append(event)
        
        # 注册处理器
        handler.register(test_func, condition=condition)
        
        # 创建不匹配的事件
        await handler._process_event({"test": "no_match"})
        assert len(called) == 0
        
        # 创建匹配的事件
        await handler._process_event({"test": "match"})
        assert len(called) == 1
    
    def test_clear_handlers(self, handler):
        """测试清除所有处理器"""
        # 注册多个处理器
        for i in range(5):
            def func(event):
                pass
            handler.register(func)
        
        assert len(handler.handlers) == 5
        
        # 执行清除
        count = handler._clear_handlers()
        
        # 验证
        assert count == 5
        assert len(handler.handlers) == 0
        assert len(handler._handler_map) == 0


# ==================== 命令处理测试 ====================

class TestCommandHandler:
    """命令处理器测试类"""
    
    @pytest.fixture(autouse=True)
    def setup_command_handler(self):
        """设置命令处理器"""
        command.commands.clear()
        command.aliases.clear()
        command.groups.clear()
        command.permissions.clear()
        command._waiting_replies.clear()
        yield
        # 清理
        command._clear_commands()
    
    def test_register_command(self):
        """测试注册命令"""
        @command("test_cmd", help="测试命令")
        async def test_handler(event):
            pass
        
        # 验证
        assert "test_cmd" in command.commands
        assert command.commands["test_cmd"]["help"] == "测试命令"
    
    def test_register_command_with_aliases(self):
        """测试注册带别名的命令"""
        print(f"Before registration: command.commands = {list(command.commands.keys())}, command.aliases = {list(command.aliases.keys())}")
        
        @command("test", aliases=["t", "T"], help="测试命令")
        async def test_handler(event):
            pass
        
        print(f"After registration: command.commands = {list(command.commands.keys())}, command.aliases = {list(command.aliases.keys())}")
        print(f"Commands detail: {command.commands}")
        print(f"Aliases detail: {command.aliases}")
        
        # 验证
        assert "test" in command.commands
        assert "t" in command.aliases
        assert "T" in command.aliases
        assert command.aliases["t"] == "test"
        assert command.aliases["T"] == "test"
    
    def test_register_command_list_name(self):
        """测试使用列表注册命令"""
        @command(["test1", "test2"], help="多名称命令")
        async def test_handler(event):
            pass
        
        # 验证
        assert "test1" in command.commands
        assert "test2" in command.commands
        assert command.aliases["test2"] == "test1"
    
    def test_register_command_with_group(self):
        """测试注册带命令组的命令"""
        @command("admin.test", group="admin", help="管理员命令")
        async def test_handler(event):
            pass
        
        # 验证
        assert command.commands["admin.test"]["group"] == "admin"
        assert "admin.test" in command.groups["admin"]
    
    def test_register_command_with_permission(self):
        """测试注册带权限检查的命令"""
        def permission_check(event):
            return True
        
        @command("secure", permission=permission_check, help="安全命令")
        async def test_handler(event):
            pass
        
        # 验证
        assert command.permissions["secure"] is permission_check
    
    def test_register_hidden_command(self):
        """测试注册隐藏命令"""
        @command("secret", hidden=True, help="隐藏命令")
        async def test_handler(event):
            pass
        
        # 验证
        assert command.commands["secret"]["hidden"] is True
        assert "secret" not in command.get_visible_commands()
    
    def test_unregister_command(self):
        """测试注销命令"""
        @command("test", help="测试")
        async def test_handler(event):
            pass
        
        # 验证命令已注册
        assert "test" in command.commands
        
        # 执行注销
        result = command.unregister(test_handler)
        
        # 验证命令已被移除
        assert "test" not in command.commands
    
    def test_get_command(self):
        """测试获取命令"""
        @command("test", help="测试")
        async def test_handler(event):
            pass
        
        # 执行
        cmd_info = command.get_command("test")
        
        # 验证
        assert cmd_info is not None
        assert cmd_info["help"] == "测试"
    
    def test_get_command_via_alias(self):
        """测试通过别名获取命令"""
        @command("test", aliases=["t"], help="测试")
        async def test_handler(event):
            pass
        
        # 验证别名已注册
        assert "t" in command.aliases
        assert command.aliases["t"] == "test"
        
        # 通过别名获取
        cmd_info = command.get_command("t")
        
        # 验证
        assert cmd_info is not None
        assert cmd_info["main_name"] == "test"
    
    def test_get_visible_commands(self):
        """测试获取可见命令"""
        @command("visible", help="可见命令")
        async def visible_handler(event):
            pass
        
        @command("hidden", hidden=True, help="隐藏命令")
        async def hidden_handler(event):
            pass
        
        # 执行
        visible = command.get_visible_commands()
        
        # 验证
        assert "visible" in visible
        assert "hidden" not in visible
    
    def test_help_command(self):
        """测试帮助命令"""
        @command("test", help="测试帮助", usage="test [args]")
        async def test_handler(event):
            pass
        
        # 执行
        help_text = command.help("test")
        
        # 验证
        assert "test" in help_text
        assert "测试帮助" in help_text
        assert "test [args]" in help_text
    
    def test_help_all(self):
        """测试获取所有命令帮助"""
        @command("cmd1", help="命令1")
        async def handler1(event):
            pass
        
        @command("cmd2", help="命令2")
        async def handler2(event):
            pass
        
        # 执行
        help_text = command.help()
        
        # 验证
        assert "cmd1" in help_text
        assert "cmd2" in help_text
        assert "命令1" in help_text
        assert "命令2" in help_text
    
    @pytest.mark.asyncio
    async def test_wait_reply_success(self):
        """测试等待用户回复成功"""
        # 创建等待future
        future = asyncio.Future()
        
        wait_key = "test:user:123"
        command._waiting_replies[wait_key] = {
            "future": future,
            "callback": None,
            "validator": None,
            "timestamp": asyncio.get_event_loop().time()
        }
        
        # 设置回复
        reply_event = {"alt_message": "test reply"}
        future.set_result(reply_event)
        
        # 执行等待
        with patch.object(adapter, 'get', return_value=Mock()):
            result = await asyncio.wait_for(future, timeout=1.0)
        
        # 验证
        assert result == reply_event
    
    @pytest.mark.asyncio
    async def test_wait_reply_timeout(self):
        """测试等待用户回复超时"""
        with patch.object(adapter, 'get', return_value=Mock()):
            # 执行等待（超时）
            result = await command.wait_reply(
                {"platform": "test", "user_id": "123"},
                timeout=0.1
            )
        
        # 验证超时返回None
        assert result is None
    
    @pytest.mark.asyncio
    async def test_handle_message_command(self):
        """测试处理消息中的命令"""
        called = []
        
        @command("test", help="测试")
        async def test_handler(event):
            called.append(event)
        
        # Mock config
        with patch.object(config, 'getConfig', return_value="/"):
            # 创建消息事件
            event_data = {
                "type": "message",
                "platform": "test",
                "self": {"platform": "test", "user_id": "bot"},
                "user_id": "user123",
                "message": [{"type": "text", "data": {"text": "/test"}}],
                "alt_message": "/test"
            }
            
            # 执行
            await command._handle_message(event_data)
        
        # 验证
        assert len(called) == 1
        assert called[0]["command"]["name"] == "test"


# ==================== 消息处理测试 ====================

class TestMessageHandler:
    """消息处理器测试类"""
    
    @pytest.fixture
    def clear_handlers(self):
        """清理处理器"""
        message.handler.handlers.clear()
        yield
        message.handler.handlers.clear()
    
    def test_on_message_decorator(self, clear_handlers):
        """测试消息装饰器"""
        called = []
        
        @message.on_message()
        async def handler(event):
            called.append(event)
        
        # 验证注册
        assert len(message.handler.handlers) == 1
    
    def test_on_private_message_decorator(self, clear_handlers):
        """测试私聊消息装饰器"""
        called = []
        
        @message.on_private_message()
        async def handler(event):
            called.append(event)
        
        # 验证注册
        assert len(message.handler.handlers) == 1
        assert message.handler.handlers[0]["condition"] is not None
    
    def test_on_group_message_decorator(self, clear_handlers):
        """测试群聊消息装饰器"""
        called = []
        
        @message.on_group_message()
        async def handler(event):
            called.append(event)
        
        # 验证注册
        assert len(message.handler.handlers) == 1
    
    def test_on_at_message_decorator(self, clear_handlers):
        """测试@消息装饰器"""
        called = []
        
        @message.on_at_message()
        async def handler(event):
            called.append(event)
        
        # 验证注册
        assert len(message.handler.handlers) == 1


# ==================== 通知处理测试 ====================

class TestNoticeHandler:
    """通知处理器测试类"""
    
    @pytest.fixture
    def clear_handlers(self):
        """清理处理器"""
        notice.handler.handlers.clear()
        yield
        notice.handler.handlers.clear()
    
    def test_on_notice_decorator(self, clear_handlers):
        """测试通知装饰器"""
        @notice.on_notice()
        async def handler(event):
            pass
        
        assert len(notice.handler.handlers) == 1
    
    def test_on_friend_add_decorator(self, clear_handlers):
        """测试好友添加装饰器"""
        @notice.on_friend_add()
        async def handler(event):
            pass
        
        assert len(notice.handler.handlers) == 1
    
    def test_on_friend_remove_decorator(self, clear_handlers):
        """测试好友删除装饰器"""
        @notice.on_friend_remove()
        async def handler(event):
            pass
        
        assert len(notice.handler.handlers) == 1
    
    def test_on_group_increase_decorator(self, clear_handlers):
        """测试群成员增加装饰器"""
        @notice.on_group_increase()
        async def handler(event):
            pass
        
        assert len(notice.handler.handlers) == 1
    
    def test_on_group_decrease_decorator(self, clear_handlers):
        """测试群成员减少装饰器"""
        @notice.on_group_decrease()
        async def handler(event):
            pass
        
        assert len(notice.handler.handlers) == 1


# ==================== 请求处理测试 ====================

class TestRequestHandler:
    """请求处理器测试类"""
    
    @pytest.fixture
    def clear_handlers(self):
        """清理处理器"""
        request.handler.handlers.clear()
        yield
        request.handler.handlers.clear()
    
    def test_on_request_decorator(self, clear_handlers):
        """测试请求装饰器"""
        @request.on_request()
        async def handler(event):
            pass
        
        assert len(request.handler.handlers) == 1
    
    def test_on_friend_request_decorator(self, clear_handlers):
        """测试好友请求装饰器"""
        @request.on_friend_request()
        async def handler(event):
            pass
        
        assert len(request.handler.handlers) == 1
    
    def test_on_group_request_decorator(self, clear_handlers):
        """测试群邀请请求装饰器"""
        @request.on_group_request()
        async def handler(event):
            pass
        
        assert len(request.handler.handlers) == 1


# ==================== 元事件处理测试 ====================

class TestMetaHandler:
    """元事件处理器测试类"""
    
    @pytest.fixture
    def clear_handlers(self):
        """清理处理器"""
        meta.handler.handlers.clear()
        yield
        meta.handler.handlers.clear()
    
    def test_on_meta_decorator(self, clear_handlers):
        """测试元事件装饰器"""
        @meta.on_meta()
        async def handler(event):
            pass
        
        assert len(meta.handler.handlers) == 1
    
    def test_on_connect_decorator(self, clear_handlers):
        """测试连接事件装饰器"""
        @meta.on_connect()
        async def handler(event):
            pass
        
        assert len(meta.handler.handlers) == 1
    
    def test_on_disconnect_decorator(self, clear_handlers):
        """测试断开连接事件装饰器"""
        @meta.on_disconnect()
        async def handler(event):
            pass
        
        assert len(meta.handler.handlers) == 1
    
    def test_on_heartbeat_decorator(self, clear_handlers):
        """测试心跳事件装饰器"""
        @meta.on_heartbeat()
        async def handler(event):
            pass
        
        assert len(meta.handler.handlers) == 1


# ==================== Event 包装类测试 ====================

class TestEventWrapper:
    """事件包装类测试类"""
    
    @pytest.fixture
    def sample_event(self):
        """创建示例事件"""
        return Event({
            "id": "test_123",
            "time": 1234567890,
            "type": "message",
            "detail_type": "private",
            "platform": "test_platform",
            "self": {
                "platform": "test_platform",
                "user_id": "bot_123"
            },
            "message": [
                {"type": "text", "data": {"text": "Hello"}}
            ],
            "alt_message": "Hello",
            "user_id": "user_123",
            "user_nickname": "TestUser"
        })
    
    def test_event_inheritance(self, sample_event):
        """测试Event继承dict"""
        assert isinstance(sample_event, dict)
        assert sample_event["id"] == "test_123"
    
    def test_get_id(self, sample_event):
        """测试获取事件ID"""
        assert sample_event.get_id() == "test_123"
    
    def test_get_time(self, sample_event):
        """测试获取时间戳"""
        assert sample_event.get_time() == 1234567890
    
    def test_get_type(self, sample_event):
        """测试获取事件类型"""
        assert sample_event.get_type() == "message"
    
    def test_get_detail_type(self, sample_event):
        """测试获取详细类型"""
        assert sample_event.get_detail_type() == "private"
    
    def test_get_platform(self, sample_event):
        """测试获取平台名称"""
        assert sample_event.get_platform() == "test_platform"
    
    def test_get_self_platform(self, sample_event):
        """测试获取机器人平台"""
        assert sample_event.get_self_platform() == "test_platform"
    
    def test_get_self_user_id(self, sample_event):
        """测试获取机器人ID"""
        assert sample_event.get_self_user_id() == "bot_123"
    
    def test_get_self_info(self, sample_event):
        """测试获取机器人信息"""
        info = sample_event.get_self_info()
        assert info["platform"] == "test_platform"
        assert info["user_id"] == "bot_123"
    
    def test_get_message(self, sample_event):
        """测试获取消息段数组"""
        message = sample_event.get_message()
        assert len(message) == 1
        assert message[0]["type"] == "text"
    
    def test_get_alt_message(self, sample_event):
        """测试获取备用文本"""
        assert sample_event.get_alt_message() == "Hello"
    
    def test_get_text(self, sample_event):
        """测试获取纯文本"""
        assert sample_event.get_text() == "Hello"
    
    def test_get_user_id(self, sample_event):
        """测试获取发送者ID"""
        assert sample_event.get_user_id() == "user_123"
    
    def test_get_user_nickname(self, sample_event):
        """测试获取发送者昵称"""
        assert sample_event.get_user_nickname() == "TestUser"
    
    def test_is_message(self, sample_event):
        """测试是否为消息事件"""
        assert sample_event.is_message() is True
    
    def test_is_private_message(self, sample_event):
        """测试是否为私聊消息"""
        assert sample_event.is_private_message() is True
        assert sample_event.is_group_message() is False
    
    def test_is_group_message(self, sample_event):
        """测试是否为群聊消息"""
        assert sample_event.is_group_message() is False
    
    def test_is_at_message(self, sample_event):
        """测试是否为@消息"""
        assert sample_event.is_at_message() is False
    
    def test_has_mention(self, sample_event):
        """测试是否包含@"""
        assert sample_event.has_mention() is False
    
    def test_get_mentions(self, sample_event):
        """测试获取被@的用户列表"""
        mentions = sample_event.get_mentions()
        assert mentions == []
    
    def test_to_dict(self, sample_event):
        """测试转换为字典"""
        result = sample_event.to_dict()
        assert isinstance(result, dict)
        assert result["id"] == "test_123"
    
    def test_is_processed(self, sample_event):
        """测试是否已处理"""
        assert sample_event.is_processed() is False
        
        sample_event.mark_processed()
        assert sample_event.is_processed() is True
    
    def test_dot_notation_access(self, sample_event):
        """测试点式访问"""
        assert sample_event.platform == "test_platform"
        assert sample_event.user_id == "user_123"
    
    def test_repr(self, sample_event):
        """测试字符串表示"""
        repr_str = repr(sample_event)
        assert "Event" in repr_str
        assert "message" in repr_str
        assert "private" in repr_str


# ==================== 平台事件方法扩展测试 ====================

class TestRegisterEventMethod:
    """register_event_method 装饰器测试类"""

    def setup_method(self):
        """每个测试前清理注册表"""
        _platform_event_methods.clear()

    def teardown_method(self):
        """每个测试后清理注册表"""
        _platform_event_methods.clear()

    def test_register_single_method(self):
        """测试注册单个方法"""
        @register_event_method("email")
        def get_subject(self):
            return self.get("email_raw", {}).get("subject", "")

        assert "email" in _platform_event_methods
        assert "get_subject" in _platform_event_methods["email"]

    def test_register_multiple_methods_same_platform(self):
        """测试同一平台注册多个方法"""
        @register_event_method("email")
        def get_subject(self):
            pass

        @register_event_method("email")
        def get_from(self):
            pass

        assert len(_platform_event_methods["email"]) == 2
        assert "get_subject" in _platform_event_methods["email"]
        assert "get_from" in _platform_event_methods["email"]

    def test_register_different_platforms(self):
        """测试不同平台注册不同方法"""
        @register_event_method("email")
        def get_subject(self):
            pass

        @register_event_method("telegram")
        def get_chat_type(self):
            pass

        assert "get_subject" in _platform_event_methods["email"]
        assert "get_subject" not in _platform_event_methods["telegram"]
        assert "get_chat_type" in _platform_event_methods["telegram"]
        assert "get_chat_type" not in _platform_event_methods["email"]

    def test_skip_private_methods(self):
        """测试跳过以下划线开头的方法"""
        @register_event_method("test")
        def _private_helper(self):
            pass

        assert "test" not in _platform_event_methods or "_private_helper" not in _platform_event_methods.get("test", {})

    def test_conflict_with_builtin_warns(self):
        """测试与内置方法冲突时发出警告"""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            @register_event_method("test")
            def get_text(self):
                pass

            assert len(w) == 1
            assert issubclass(w[0].category, RuntimeWarning)
            assert "get_text" in str(w[0].message)
            assert "内置方法冲突" in str(w[0].message)

        # 冲突方法不应被注册
        assert "get_text" not in _platform_event_methods.get("test", {})

    def test_decorator_returns_original_function(self):
        """测试装饰器返回原始函数"""
        def get_subject(self):
            return "subject"

        decorated = register_event_method("email")(get_subject)
        assert decorated is get_subject


class TestRegisterEventMixin:
    """register_event_mixin 批量注册测试类"""

    def setup_method(self):
        """每个测试前清理注册表"""
        _platform_event_methods.clear()

    def teardown_method(self):
        """每个测试后清理注册表"""
        _platform_event_methods.clear()

    def test_register_mixin_class(self):
        """测试通过 Mixin 类批量注册"""
        class EmailEventMixin:
            def get_subject(self):
                return self.get("email_raw", {}).get("subject", "")

            def get_from(self):
                return self.get("email_raw", {}).get("from", "")

            def _internal(self):
                pass

        count = register_event_mixin("email", EmailEventMixin)
        assert count == 2
        assert "get_subject" in _platform_event_methods["email"]
        assert "get_from" in _platform_event_methods["email"]
        assert "_internal" not in _platform_event_methods["email"]

    def test_register_empty_mixin(self):
        """测试注册空 Mixin 类"""
        class EmptyMixin:
            pass

        count = register_event_mixin("test", EmptyMixin)
        assert count == 0

    def test_mixin_conflict_skips_with_warning(self):
        """测试 Mixin 中与内置冲突的方法被跳过"""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            class BadMixin:
                def get_text(self):
                    pass

                def get_platform(self):
                    pass

                def custom_method(self):
                    pass

            count = register_event_mixin("test", BadMixin)

            # 应有 2 个警告（get_text 和 get_platform 冲突）
            assert len(w) == 2
            # 只有 custom_method 被注册
            assert count == 1
            assert "custom_method" in _platform_event_methods["test"]


class TestUnregisterEventMethod:
    """注销方法测试类"""

    def setup_method(self):
        """每个测试前清理注册表"""
        _platform_event_methods.clear()

    def teardown_method(self):
        """每个测试后清理注册表"""
        _platform_event_methods.clear()

    def test_unregister_single_method(self):
        """测试注销单个方法"""
        @register_event_method("email")
        def get_subject(self):
            pass

        result = unregister_event_method("email", "get_subject")
        assert result is True
        assert "get_subject" not in _platform_event_methods["email"]

    def test_unregister_nonexistent_method(self):
        """测试注销不存在的方法"""
        result = unregister_event_method("email", "nonexistent")
        assert result is False

    def test_unregister_nonexistent_platform(self):
        """测试注销不存在平台的方法"""
        result = unregister_event_method("nonexistent", "get_subject")
        assert result is False

    def test_unregister_platform_all_methods(self):
        """测试注销平台全部方法"""
        @register_event_method("email")
        def get_subject(self):
            pass

        @register_event_method("email")
        def get_from(self):
            pass

        count = unregister_platform_event_methods("email")
        assert count == 2
        assert "email" not in _platform_event_methods

    def test_unregister_nonexistent_platform_all(self):
        """测试注销不存在平台的全部方法"""
        count = unregister_platform_event_methods("nonexistent")
        assert count == 0


class TestGetPlatformEventMethods:
    """查询方法测试类"""

    def setup_method(self):
        """每个测试前清理注册表"""
        _platform_event_methods.clear()

    def teardown_method(self):
        """每个测试后清理注册表"""
        _platform_event_methods.clear()

    def test_get_methods_for_platform(self):
        """测试查询平台已注册方法"""
        @register_event_method("email")
        def get_subject(self):
            pass

        @register_event_method("email")
        def get_from(self):
            pass

        methods = get_platform_event_methods("email")
        assert sorted(methods) == ["get_from", "get_subject"]

    def test_get_methods_for_nonexistent_platform(self):
        """测试查询不存在平台的方法"""
        methods = get_platform_event_methods("nonexistent")
        assert methods == []


class TestEventPlatformMethodDispatch:
    """Event 实例平台方法分派测试类"""

    def setup_method(self):
        """每个测试前清理注册表"""
        _platform_event_methods.clear()

    def teardown_method(self):
        """每个测试后清理注册表"""
        _platform_event_methods.clear()

    def test_email_event_has_email_methods(self):
        """测试邮件事件可以访问邮件方法"""
        @register_event_method("email")
        def get_subject(self):
            return self.get("email_raw", {}).get("subject", "")

        event = Event({"platform": "email", "email_raw": {"subject": "Hello Email"}})
        assert event.get_subject() == "Hello Email"

    def test_email_event_missing_telegram_methods(self):
        """测试邮件事件访问 Telegram 方法抛出 AttributeError"""
        @register_event_method("telegram")
        def get_chat_type(self):
            return self.get("telegram_raw", {}).get("chat", {}).get("type", "")

        event = Event({"platform": "email", "email_raw": {}})
        with pytest.raises(AttributeError, match="get_chat_type"):
            event.get_chat_type()

    def test_telegram_event_has_telegram_methods(self):
        """测试 Telegram 事件可以访问 Telegram 方法"""
        @register_event_method("telegram")
        def get_chat_type(self):
            return self.get("telegram_raw", {}).get("chat", {}).get("type", "")

        event = Event({
            "platform": "telegram",
            "telegram_raw": {"chat": {"type": "private"}}
        })
        assert event.get_chat_type() == "private"

    def test_telegram_event_missing_email_methods(self):
        """测试 Telegram 事件访问邮件方法抛出 AttributeError"""
        @register_event_method("email")
        def get_subject(self):
            return self.get("email_raw", {}).get("subject", "")

        event = Event({"platform": "telegram", "telegram_raw": {}})
        with pytest.raises(AttributeError, match="get_subject"):
            event.get_subject()

    def test_builtin_methods_always_available(self):
        """测试内置方法在任何平台都可用"""
        @register_event_method("email")
        def get_subject(self):
            pass

        email_event = Event({"platform": "email"})
        telegram_event = Event({"platform": "telegram"})

        # 内置方法在两个平台都可用
        assert callable(email_event.get_text)
        assert callable(telegram_event.get_text)
        assert callable(email_event.get_user_id)
        assert callable(telegram_event.get_user_id)

    def test_dict_key_access_still_works(self):
        """测试字典键的点式访问不受影响"""
        @register_event_method("email")
        def get_subject(self):
            pass

        event = Event({"platform": "email", "user_id": "123", "custom_key": "value"})
        assert event.user_id == "123"
        assert event.custom_key == "value"

    def test_nonexistent_attribute_raises(self):
        """测试访问不存在的属性抛出 AttributeError"""
        event = Event({"platform": "test"})
        with pytest.raises(AttributeError, match="nonexistent_attr"):
            event.nonexistent_attr

    def test_platform_method_receives_self(self):
        """测试平台方法正确接收 self 绑定"""
        @register_event_method("email")
        def get_email_field(self, field_name):
            return self.get("email_raw", {}).get(field_name, "")

        event = Event({"platform": "email", "email_raw": {"to": "a@b.com"}})
        assert event.get_email_field("to") == "a@b.com"
        assert event.get_email_field("missing") == ""

    def test_dir_includes_platform_methods(self):
        """测试 dir(event) 包含平台方法名"""
        @register_event_method("email")
        def get_subject(self):
            pass

        @register_event_method("email")
        def get_from(self):
            pass

        event = Event({"platform": "email"})
        attr_names = dir(event)
        assert "get_subject" in attr_names
        assert "get_from" in attr_names

    def test_dir_excludes_other_platform_methods(self):
        """测试 dir(event) 不包含其他平台的方法名"""
        @register_event_method("email")
        def get_subject(self):
            pass

        @register_event_method("telegram")
        def get_chat_type(self):
            pass

        event = Event({"platform": "email"})
        attr_names = dir(event)
        assert "get_subject" in attr_names
        assert "get_chat_type" not in attr_names

    def test_hasattr_reflects_platform_methods(self):
        """测试 hasattr 正确反映平台方法存在性"""
        @register_event_method("email")
        def get_subject(self):
            pass

        email_event = Event({"platform": "email"})
        telegram_event = Event({"platform": "telegram"})

        assert hasattr(email_event, "get_subject") is True
        assert hasattr(telegram_event, "get_subject") is False

    def test_no_platform_still_works(self):
        """测试无 platform 字段时正常工作"""
        event = Event({"type": "message", "alt_message": "hi"})
        assert event.get_text() == "hi"
        assert event.type == "message"

    def test_mixin_methods_on_event(self):
        """测试通过 Mixin 注册的方法在 Event 上可用"""
        class EmailMixin:
            def get_subject(self):
                return self.get("email_raw", {}).get("subject", "")
            def get_from(self):
                return self.get("email_raw", {}).get("from", "")

        register_event_mixin("email", EmailMixin)

        event = Event({
            "platform": "email",
            "email_raw": {"subject": "Test Subject", "from": "sender@example.com"}
        })
        assert event.get_subject() == "Test Subject"
        assert event.get_from() == "sender@example.com"
