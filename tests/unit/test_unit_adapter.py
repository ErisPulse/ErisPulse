"""
适配器系统单元测试

测试适配器管理器和基础适配器类的功能
"""

import asyncio
from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock, Mock, PropertyMock, patch

import pytest

from ErisPulse.Core import router
from ErisPulse.Core.adapter import AdapterManager
from ErisPulse.Core.Bases import BaseAdapter, SendDSL
from ErisPulse.Core.config import config
from ErisPulse.Core.i18n import i18n
from ErisPulse.Core.lifecycle import lifecycle

# ==================== 适配器管理器测试 ====================


class TestAdapterManager:
    """适配器管理器测试类"""

    @pytest.fixture
    def manager(self):
        """创建适配器管理器实例"""
        manager = AdapterManager()
        # 清理初始状态
        manager._adapters.clear()
        manager._started_instances.clear()
        manager._adapter_info.clear()
        manager._onebot_handlers.clear()
        manager._raw_handlers.clear()
        manager._onebot_middlewares.clear()
        return manager

    @pytest.fixture
    def test_adapter_class(self):
        """创建测试适配器类"""

        class TestAdapter(BaseAdapter):
            def __init__(self, sdk=None):
                super().__init__()
                self.sdk = sdk
                self.started = False
                self.shutdown_called = False

            async def start(self):
                self.started = True

            async def shutdown(self):
                self.shutdown_called = True

            async def call_api(self, endpoint: str, **params):
                return {
                    "status": "ok",
                    "retcode": 0,
                    "data": {"test": True},
                    "message_id": "test_id",
                    "message": "",
                    "test_raw": params,
                }

        return TestAdapter

    # ==================== 注册测试 ====================

    def test_register_adapter_success(self, manager, test_adapter_class):
        """测试成功注册适配器"""
        # 执行
        result = manager.register(
            "test_platform", test_adapter_class, {"version": "1.0.0"}
        )

        # 验证
        assert result is True
        assert "test_platform" in manager._adapters
        assert isinstance(manager._adapters["test_platform"], test_adapter_class)
        assert "test_platform" in manager._adapter_info
        assert manager._adapter_info["test_platform"]["version"] == "1.0.0"

    def test_register_adapter_invalid_class(self, manager):
        """测试注册无效的适配器类"""

        class InvalidAdapter:
            pass

        # 执行和验证
        with pytest.raises(TypeError, match=i18n.t("core.adapter.must_inherit_base")):
            manager.register("invalid", InvalidAdapter)

    def test_register_adapter_duplicate(self, manager, test_adapter_class):
        """测试注册重复的适配器"""
        # 第一次注册
        manager.register("test_platform", test_adapter_class)

        # 第二次注册（覆盖，会记录 warning 日志）
        manager.register("test_platform", test_adapter_class)

        # 验证仍然只有一个实例（因为同一类会复用实例）
        assert (
            len(
                [
                    a
                    for a in manager._adapters.values()
                    if isinstance(a, test_adapter_class)
                ]
            )
            == 1
        )

    def test_register_adapter_multiple_platforms_same_class(
        self, manager, test_adapter_class
    ):
        """测试同一适配器类注册到多个平台"""
        # 注册到多个平台
        manager.register("platform1", test_adapter_class)
        manager.register("platform2", test_adapter_class)

        # 验证
        assert "platform1" in manager._adapters
        assert "platform2" in manager._adapters
        # 验证是同一个实例
        assert manager._adapters["platform1"] is manager._adapters["platform2"]

    def test_register_platform_attributes(self, manager, test_adapter_class):
        """测试平台属性注册"""
        manager.register("Test", test_adapter_class)

        # 验证属性可以通过不同大小写访问
        assert hasattr(manager, "test")
        assert hasattr(manager, "Test")
        assert hasattr(manager, "TEST")
        assert manager.test is manager._adapters["Test"]

    # ==================== 启动和关闭测试 ====================

    @pytest.mark.asyncio
    async def test_startup_all_adapters(self, manager, test_adapter_class):
        """测试启动所有适配器"""
        manager.register("platform1", test_adapter_class)
        manager.register("platform2", test_adapter_class)

        await manager.startup()

        assert len(manager._started_instances) == 0  # 异步，还未完成

    @pytest.mark.asyncio
    async def test_startup_specific_adapters(self, manager, test_adapter_class):
        """测试启动指定的适配器"""
        manager.register("platform1", test_adapter_class)
        manager.register("platform2", test_adapter_class)

        await manager.startup(["platform1"])

    @pytest.mark.asyncio
    async def test_startup_nonexistent_platform(self, manager):
        """测试启动不存在的平台"""
        await manager.startup(["nonexistent"])
        assert "nonexistent" not in manager._adapters

    @pytest.mark.asyncio
    async def test_shutdown_all_adapters(self, manager, test_adapter_class):
        """测试关闭所有适配器"""
        # 注册并启动适配器
        manager.register("platform1", test_adapter_class)
        adapter1 = manager._adapters["platform1"]
        adapter1.started = True

        manager.register("platform2", test_adapter_class)
        adapter2 = manager._adapters["platform2"]
        adapter2.started = True

        manager._started_instances.add(adapter1)

        # Mock router
        with patch.object(router, "stop"):
            # 执行
            await manager.shutdown()

            # 验证所有适配器已关闭（adapter1 和 adapter2 是同一个实例）
            assert adapter1.shutdown_called
            # 注意：由于同一类会复用实例，started_instances 只有一个实例
            assert len(manager._started_instances) == 0

    # ==================== 配置管理测试 ====================

    def test_adapter_exists(self, manager, test_adapter_class):
        """测试检查适配器是否存在"""
        # Mock config
        with patch.object(config, "getConfig", return_value={}):
            # 注册并检查
            manager.register("test_platform", test_adapter_class)

            # 验证
            assert manager.exists("test_platform") is True
            assert manager.exists("nonexistent") is False

    def test_adapter_is_enabled(self, manager):
        """测试检查适配器是否启用"""
        with patch.object(config, "getConfig") as mock_get, \
             patch.object(config, "setConfig") as mock_set:
            # 启用状态
            mock_get.return_value = True
            assert manager.is_enabled("test_platform") is True

            # 禁用状态
            mock_get.return_value = False
            assert manager.is_enabled("test_platform") is False

            # 未配置状态 - 默认启用并自动写入配置
            mock_get.return_value = None
            assert manager.is_enabled("test_platform") is True
            mock_set.assert_called_once()

    def test_adapter_enable(self, manager, test_adapter_class):
        """测试启用适配器"""
        # 先注册适配器
        manager.register("test_platform", test_adapter_class)

        with patch.object(config, "setConfig") as mock_set:
            # 执行
            result = manager.enable("test_platform")

            # 验证
            assert result is True
            mock_set.assert_called_once_with(
                "ErisPulse.adapters.status.test_platform", True
            )

    def test_adapter_disable(self, manager, test_adapter_class):
        """测试禁用适配器"""
        # 先注册适配器
        manager.register("test_platform", test_adapter_class)

        with patch.object(config, "setConfig") as mock_set:
            # 执行
            result = manager.disable("test_platform")

            # 验证
            assert result is True
            mock_set.assert_called_once_with(
                "ErisPulse.adapters.status.test_platform", False
            )

    def test_unregister_adapter(self, manager, test_adapter_class):
        """测试取消注册适配器"""
        # 注册适配器
        manager.register("Test", test_adapter_class)
        assert "Test" in manager._adapters

        # 执行取消注册
        result = manager.unregister("Test")

        # 验证
        assert result is True
        assert "Test" not in manager._adapters
        assert not hasattr(manager, "test")
        assert not hasattr(manager, "Test")

    # ==================== 工具方法测试 ====================

    def test_get_adapter(self, manager, test_adapter_class):
        """测试获取适配器实例"""
        manager.register("test_platform", test_adapter_class)

        # 执行
        adapter = manager.get("test_platform")

        # 验证
        assert adapter is not None
        assert isinstance(adapter, test_adapter_class)

    def test_get_adapter_case_insensitive(self, manager, test_adapter_class):
        """测试获取适配器（大小写不敏感）"""
        manager.register("TestPlatform", test_adapter_class)

        # 验证不同大小写都能获取
        assert manager.get("testplatform") is not None
        assert manager.get("TESTPLATFORM") is not None
        assert manager.get("TestPlatform") is not None

    def test_get_adapter_nonexistent(self, manager):
        """测试获取不存在的适配器"""
        adapter = manager.get("nonexistent")
        assert adapter is None

    def test_platforms_property(self, manager, test_adapter_class):
        """测试获取所有平台列表"""
        manager.register("platform1", test_adapter_class)
        manager.register("platform2", test_adapter_class)

        # 执行
        platforms = manager.platforms

        # 验证
        assert "platform1" in platforms
        assert "platform2" in platforms
        assert len(platforms) == 2

    def test_list_sends(self, manager, test_adapter_class):
        """测试列出支持的发送方法"""
        # 注册适配器
        manager.register("test_platform", test_adapter_class)

        # 执行
        methods = manager.list_sends("test_platform")

        # 验证 - 应该包含Example方法（从BaseAdapter.Send继承），但不包含基类方法
        assert "Example" in methods
        # 验证不包含基类方法
        assert "To" not in methods
        assert "Using" not in methods
        assert "Account" not in methods
        assert "At" not in methods
        assert "Reply" not in methods
        assert "AtAll" not in methods

    def test_list_sends_nonexistent_platform(self, manager):
        """测试列出不存在平台的方法"""
        # 执行和验证
        with pytest.raises(
            ValueError,
            match=i18n.t("core.adapter.platform_not_exist", platform="nonexistent"),
        ):
            manager.list_sends("nonexistent")

    def test_send_info(self, manager, test_adapter_class):
        """测试获取发送方法详情"""
        # 注册适配器
        manager.register("test_platform", test_adapter_class)

        # 执行
        info = manager.send_info("test_platform", "Example")

        # 验证基本信息
        assert info["name"] == "Example"
        assert "Awaitable" in info["return_type"]
        assert "Any" in info["return_type"]
        assert "示例消息发送方法" in info["docstring"]

        # 验证参数信息
        parameters = info["parameters"]
        assert len(parameters) == 1
        assert parameters[0]["name"] == "text"
        assert "str" in parameters[0]["type"]
        assert "str" in parameters[0]["annotation"]
        assert parameters[0]["default"] is None

    def test_send_info_nonexistent_platform(self, manager):
        """测试获取不存在平台的方法详情"""
        # 执行和验证
        with pytest.raises(
            ValueError,
            match=i18n.t("core.adapter.platform_not_exist", platform="nonexistent"),
        ):
            manager.send_info("nonexistent", "Example")

    def test_send_info_nonexistent_method(self, manager, test_adapter_class):
        """测试获取不存在方法的详情"""
        # 注册适配器
        manager.register("test_platform", test_adapter_class)

        # 执行和验证
        with pytest.raises(
            ValueError,
            match=i18n.t("core.adapter.method_not_exist", method="NonexistentMethod"),
        ):
            manager.send_info("test_platform", "NonexistentMethod")

    def test_contains_operator(self, manager, test_adapter_class):
        """测试包含操作符"""
        with patch.object(config, "getConfig", return_value=True):
            # 启用的适配器（先注册）
            with patch.object(config, "setConfig"):
                manager.register("enabled", test_adapter_class)
                assert "enabled" in manager

            # 禁用的适配器
            with patch.object(config, "getConfig", return_value=False):
                assert "disabled" not in manager

            # 不存在的适配器
            assert "nonexistent" not in manager

    # ==================== 事件处理测试 ====================

    def test_register_onebot_handler(self, manager):
        """测试注册OneBot12事件处理器"""
        handler_called = []

        @manager.on("message")
        async def handler(data):
            handler_called.append(data)

        # 验证处理器已注册
        assert "message" in manager._onebot_handlers
        assert len(manager._onebot_handlers["message"]) == 1

    def test_register_raw_handler(self, manager):
        """测试注册原生事件处理器"""
        handler_called = []

        @manager.on("test_event", raw=True, platform="test_platform")
        async def handler(data):
            handler_called.append(data)

        # 验证处理器已注册
        assert "test_event" in manager._raw_handlers
        assert len(manager._raw_handlers["test_event"]) == 1

    def test_register_middleware(self, manager):
        """测试注册中间件"""
        middleware_called = []

        @manager.middleware
        async def middleware(data):
            middleware_called.append(data)
            return data

        # 验证中间件已注册
        assert len(manager._onebot_middlewares) == 1
        assert middleware_called == []

    @pytest.mark.asyncio
    async def test_emit_onebot_event(self, manager):
        """测试提交OneBot12标准事件"""
        handler_called = []

        @manager.on("message")
        async def handler(data):
            handler_called.append(data)

        # 提交事件
        event_data = {
            "id": "test_123",
            "time": 1234567890,
            "type": "message",
            "detail_type": "private",
            "platform": "test",
            "self": {"platform": "test", "user_id": "bot_123"},
            "message": [{"type": "text", "data": {"text": "test"}}],
        }

        await manager.emit(event_data)
        await asyncio.sleep(0)

        # 验证处理器被调用
        assert len(handler_called) == 1
        assert handler_called[0] == event_data

    @pytest.mark.asyncio
    async def test_emit_raw_event(self, manager):
        """测试提交原生事件"""
        handler_called = []

        @manager.on("test_raw_event", raw=True, platform="test")
        async def handler(data):
            handler_called.append(data)

        # 提交事件
        event_data = {
            "id": "test_123",
            "time": 1234567890,
            "type": "message",
            "platform": "test",
            "self": {"platform": "test", "user_id": "bot_123"},
            "test_raw": {"raw_data": "test"},
            "test_raw_type": "test_raw_event",
        }

        await manager.emit(event_data)
        await asyncio.sleep(0)

        # 验证原生处理器被调用
        assert len(handler_called) == 1
        assert handler_called[0] == event_data["test_raw"]

    @pytest.mark.asyncio
    async def test_emit_with_middleware(self, manager):
        """测试事件经过中间件处理"""
        middleware_data = []
        handler_data = []

        @manager.middleware
        async def middleware(data):
            middleware_data.append(data)
            data["middleware_added"] = True
            return data

        @manager.on("message")
        async def handler(data):
            handler_data.append(data)

        # 提交事件
        event_data = {
            "id": "test_123",
            "type": "message",
            "platform": "test",
            "self": {"platform": "test", "user_id": "bot_123"},
            "message": [],
        }

        await manager.emit(event_data)
        await asyncio.sleep(0)

        # 验证中间件和处理器都被调用
        assert len(middleware_data) == 1
        assert len(handler_data) == 1
        assert handler_data[0]["middleware_added"] is True


# ==================== SendDSL 测试 ====================


class TestSendDSL:
    """消息发送DSL测试类"""

    @pytest.fixture
    def base_adapter(self):
        """创建基础适配器"""

        class TestAdapter(BaseAdapter):
            async def start(self):
                pass

            async def shutdown(self):
                pass

            async def call_api(self, endpoint: str, **params):
                return {
                    "status": "ok",
                    "retcode": 0,
                    "data": {},
                    "message_id": "test_id",
                }

        return TestAdapter()

    def test_send_dsl_initialization(self, base_adapter):
        """测试SendDSL初始化"""
        send_dsl = SendDSL(base_adapter, "user", "123", None)

        assert send_dsl._adapter is base_adapter
        assert send_dsl._target_type == "user"
        assert send_dsl._target_id == "123"
        assert send_dsl._account_id is None

    def test_send_dsl_to_method(self, base_adapter):
        """测试To方法"""
        send_dsl = SendDSL(base_adapter)

        # 设置目标
        result = send_dsl.To("group", "456")

        assert result._target_type == "group"
        assert result._target_id == "456"
        assert result._target_to == "456"

    def test_send_dsl_to_single_arg(self, base_adapter):
        """测试To方法单参数"""
        send_dsl = SendDSL(base_adapter)

        # 只传ID
        result = send_dsl.To("789")

        assert result._target_to == "789"

    def test_send_dsl_using_method(self, base_adapter):
        """测试Using方法"""
        send_dsl = SendDSL(base_adapter)

        # 设置账号
        result = send_dsl.Using("account_123")

        assert result._account_id == "account_123"

    def test_send_dsl_chaining(self, base_adapter):
        """测试链式调用"""
        send_dsl = SendDSL(base_adapter)

        # 链式调用
        result = send_dsl.Using("account_1").To("user", "123")

        assert result._account_id == "account_1"
        assert result._target_type == "user"
        assert result._target_id == "123"


# ==================== BaseAdapter 测试 ====================


class TestBaseAdapter:
    """基础适配器测试类"""

    @pytest.fixture
    def concrete_adapter(self):
        """创建具体适配器"""

        class ConcreteAdapter(BaseAdapter):
            def __init__(self):
                super().__init__()
                self.initialized = False
                self.started = False
                self.shutdown_called = False

            async def start(self):
                self.started = True

            async def shutdown(self):
                self.shutdown_called = True

            async def call_api(self, endpoint: str, **params):
                return {
                    "status": "ok",
                    "retcode": 0,
                    "data": {"endpoint": endpoint},
                    "message_id": "test_id",
                }

        return ConcreteAdapter()

    def test_adapter_has_send_dsl(self, concrete_adapter):
        """测试适配器有Send DSL"""
        assert hasattr(concrete_adapter, "Send")
        assert isinstance(concrete_adapter.Send, SendDSL)

    def test_send_dsl_adapter_reference(self, concrete_adapter):
        """测试Send DSL引用适配器"""
        assert concrete_adapter.Send._adapter is concrete_adapter

    @pytest.mark.asyncio
    async def test_adapter_send_method(self, concrete_adapter):
        """测试send便捷方法"""
        task = concrete_adapter.send("user", "123", "test message", method="Example")

        # 验证返回的是Task
        import asyncio

        assert isinstance(task, asyncio.Task)

    def test_abstract_methods_not_implemented(self):
        """测试抽象方法未实现会抛出异常"""

        class IncompleteAdapter(BaseAdapter):
            pass

        # 使用 ABC，无法实例化未实现抽象方法的类
        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            IncompleteAdapter()

    # ==================== _resolve_account 测试 ====================

    def test_resolve_account_single_adapter_no_config_class(self):
        """未声明 AccountConfigClass 的单账户适配器返回 (None, None)"""

        class SingleAdapter(BaseAdapter):
            ConfigClass = None
            AccountConfigClass = None

            async def start(self):
                pass

            async def shutdown(self):
                pass

            async def call_api(self, endpoint: str, **params):
                return {"status": "ok"}

        adapter = SingleAdapter()
        name, cfg = adapter._resolve_account()
        assert name is None
        assert cfg is None

    def test_resolve_account_multi_adapter_returns_first_enabled(self):
        """多账户适配器返回第一个启用的账户"""
        from dataclasses import dataclass

        @dataclass
        class BotConfig:
            bot_id: str = ""
            enabled: bool = True
            token: str = ""

        class MultiAdapter(BaseAdapter):
            ConfigClass = None
            AccountConfigClass = BotConfig

            async def start(self):
                pass

            async def shutdown(self):
                pass

            async def call_api(self, endpoint: str, **params):
                return {"status": "ok"}

        adapter = MultiAdapter()
        # 模拟适配器加载后的账户数据
        adapter._accounts_data = {
            "default": BotConfig(bot_id="123", enabled=True, token="abc"),
            "disabled": BotConfig(bot_id="456", enabled=False, token="def"),
        }

        name, cfg = adapter._resolve_account()
        assert name == "default"
        assert cfg.bot_id == "123"

    def test_resolve_account_by_name(self):
        """按账户名解析账户"""
        from dataclasses import dataclass

        @dataclass
        class BotConfig:
            bot_id: str = ""
            enabled: bool = True
            token: str = ""

        class MultiAdapter(BaseAdapter):
            ConfigClass = None
            AccountConfigClass = BotConfig

            async def start(self):
                pass

            async def shutdown(self):
                pass

            async def call_api(self, endpoint: str, **params):
                return {"status": "ok"}

        adapter = MultiAdapter()
        adapter._accounts_data = {
            "default": BotConfig(bot_id="123", enabled=True, token="abc"),
            "second": BotConfig(bot_id="456", enabled=True, token="def"),
        }

        name, cfg = adapter._resolve_account("second")
        assert name == "second"
        assert cfg.bot_id == "456"

    def test_resolve_account_by_bot_id(self):
        """按 bot_id 字段解析账户"""
        from dataclasses import dataclass

        @dataclass
        class BotConfig:
            bot_id: str = ""
            enabled: bool = True
            token: str = ""

        class MultiAdapter(BaseAdapter):
            ConfigClass = None
            AccountConfigClass = BotConfig

            async def start(self):
                pass

            async def shutdown(self):
                pass

            async def call_api(self, endpoint: str, **params):
                return {"status": "ok"}

        adapter = MultiAdapter()
        adapter._accounts_data = {
            "default": BotConfig(bot_id="123", enabled=True, token="abc"),
            "second": BotConfig(bot_id="456", enabled=True, token="def"),
        }

        name, cfg = adapter._resolve_account("456")
        assert name == "second"
        assert cfg.token == "def"

    def test_resolve_account_not_found_raises(self):
        """未找到账户时抛出 ValueError"""
        from dataclasses import dataclass

        @dataclass
        class BotConfig:
            bot_id: str = ""
            enabled: bool = True
            token: str = ""

        class MultiAdapter(BaseAdapter):
            ConfigClass = None
            AccountConfigClass = BotConfig

            async def start(self):
                pass

            async def shutdown(self):
                pass

            async def call_api(self, endpoint: str, **params):
                return {"status": "ok"}

        adapter = MultiAdapter()
        adapter._accounts_data = {
            "default": BotConfig(bot_id="123", enabled=False, token="abc"),
        }

        with pytest.raises(ValueError, match="未找到可用账户"):
            adapter._resolve_account()

    def test_resolve_account_no_enabled_raises(self):
        """所有账户都禁用时抛出 ValueError"""
        from dataclasses import dataclass

        @dataclass
        class BotConfig:
            bot_id: str = ""
            enabled: bool = True
            token: str = ""

        class MultiAdapter(BaseAdapter):
            ConfigClass = None
            AccountConfigClass = BotConfig

            async def start(self):
                pass

            async def shutdown(self):
                pass

            async def call_api(self, endpoint: str, **params):
                return {"status": "ok"}

        adapter = MultiAdapter()
        adapter._accounts_data = {
            "default": BotConfig(bot_id="123", enabled=False, token="abc"),
            "second": BotConfig(bot_id="456", enabled=False, token="def"),
        }

        with pytest.raises(ValueError, match="未找到可用账户"):
            adapter._resolve_account()

    def test_resolve_account_adapter_override_accounts_data(self):
        """适配器覆写后直接设置 _accounts_data 的场景（向后兼容）"""
        from dataclasses import dataclass

        @dataclass
        class BotConfig:
            bot_id: str = ""
            enabled: bool = True
            token: str = ""

        class CustomAdapter(BaseAdapter):
            ConfigClass = None
            AccountConfigClass = BotConfig

            def __init__(self):
                super().__init__()
                # 模拟适配器覆写 _load_accounts 后填充自定义数据
                self._accounts_data = {
                    "custom": BotConfig(bot_id="custom_999", enabled=True, token="xyz"),
                }

            async def start(self):
                pass

            async def shutdown(self):
                pass

            async def call_api(self, endpoint: str, **params):
                return {"status": "ok"}

        adapter = CustomAdapter()
        name, cfg = adapter._resolve_account()
        assert name == "custom"
        assert cfg.bot_id == "custom_999"


# ==================== SendDSL Raw_ob12 测试 ====================


class TestSendDSLRawMethods:
    """SendDSL Raw_ob12 方法测试类"""

    @pytest.fixture
    def base_adapter(self):
        """创建基础适配器（未重写 Raw_ob12）"""

        class TestAdapter(BaseAdapter):
            async def start(self):
                pass

            async def shutdown(self):
                pass

            async def call_api(self, endpoint: str, **params):
                return {
                    "status": "ok",
                    "retcode": 0,
                    "data": {},
                    "message_id": "test_id",
                }

        return TestAdapter()

    @pytest.mark.asyncio
    async def test_raw_ob12_default_returns_error_response(self, base_adapter):
        """测试未重写 Raw_ob12 时返回标准错误响应"""
        send = SendDSL(base_adapter, "user", "123", None)
        result = await send.Raw_ob12([{"type": "text", "data": {"text": "hi"}}])
        assert result is not None
        assert result["status"] == "failed"
        assert result["retcode"] == 10002
        assert "Raw_ob12" in result["message"]
        assert result["data"] is None
        assert result["message_id"] == ""

    @pytest.mark.asyncio
    async def test_raw_ob12_default_logs_error(self, base_adapter):
        """测试未重写 Raw_ob12 时记录错误日志"""
        with patch("ErisPulse.Core.logger.logger") as mock_logger:
            send = SendDSL(base_adapter, "user", "123", None)
            await send.Raw_ob12([{"type": "text", "data": {"text": "hi"}}])
            mock_logger.error.assert_called_once()

    @pytest.mark.asyncio
    async def test_raw_ob12_with_overridden(self):
        """测试重写 Raw_ob12 后正常返回 Task 并可 await"""
        import asyncio

        class CustomAdapter(BaseAdapter):
            async def start(self):
                pass

            async def shutdown(self):
                pass

            async def call_api(self, endpoint: str, **params):
                return {"status": "ok", "retcode": 0, "data": {}, "message_id": "id"}

            class Send(BaseAdapter.Send):
                def Raw_ob12(self, message, **kwargs):
                    async def _do():
                        return await self._adapter.call_api("/send", message=message)

                    return asyncio.create_task(_do())

        adapter = CustomAdapter()
        send = adapter.Send.To("user", "123")
        result = await send.Raw_ob12([{"type": "text", "data": {"text": "hi"}}])
        assert result["status"] == "ok"

    @pytest.mark.asyncio
    async def test_raw_ob12_overridden_awaitable(self):
        """测试重写的 Raw_ob12 可以 await 并返回结果"""

        class CustomAdapter(BaseAdapter):
            async def start(self):
                pass

            async def shutdown(self):
                pass

            async def call_api(self, endpoint: str, **params):
                return {"status": "ok", "retcode": 0, "data": {}, "message_id": "id"}

            class Send(BaseAdapter.Send):
                def Raw_ob12(self, message, **kwargs):
                    import asyncio

                    async def _do():
                        return await self._adapter.call_api("/send", message=message)

                    return asyncio.create_task(_do())

        adapter = CustomAdapter()
        result = await adapter.Send.To("user", "123").Raw_ob12(
            [{"type": "text", "data": {"text": "hi"}}]
        )
        assert result["status"] == "ok"
        assert result["message_id"] == "id"

    @pytest.mark.asyncio
    async def test_raw_ob12_accepts_dict_input(self):
        """测试 Raw_ob12 接受单个 dict 输入"""

        class CustomAdapter(BaseAdapter):
            async def start(self):
                pass

            async def shutdown(self):
                pass

            async def call_api(self, endpoint: str, **params):
                return {"status": "ok", "retcode": 0, "data": {}, "message_id": "id"}

            class Send(BaseAdapter.Send):
                def Raw_ob12(self, message, **kwargs):
                    import asyncio

                    # 记录收到的 message 类型
                    self._received_type = type(message).__name__

                    async def _do():
                        return {}

                    return asyncio.create_task(_do())

        adapter = CustomAdapter()
        send = adapter.Send.To("user", "123")
        await send.Raw_ob12({"type": "text", "data": {"text": "hi"}})
        # 基类会将 dict 包装为 list
        assert hasattr(send, "_received_type")

    @pytest.mark.asyncio
    async def test_raw_ob12_with_message_builder(self):
        """测试 Raw_ob12 配合 MessageBuilder 使用"""
        import asyncio

        from ErisPulse.Core.Event.message_builder import MessageBuilder

        captured_segments = []

        class CustomAdapter(BaseAdapter):
            async def start(self):
                pass

            async def shutdown(self):
                pass

            async def call_api(self, endpoint: str, **params):
                return {"status": "ok", "retcode": 0, "data": {}, "message_id": "id"}

            class Send(BaseAdapter.Send):
                def Raw_ob12(self, message, **kwargs):
                    captured_segments.append(message)
                    import asyncio

                    async def _do():
                        return {}

                    return asyncio.create_task(_do())

        adapter = CustomAdapter()
        segments = MessageBuilder().text("Hi").mention("123").image("url").build()
        await adapter.Send.To("group", "456").Raw_ob12(segments)

        assert len(captured_segments) == 1
        assert len(captured_segments[0]) == 3
        assert captured_segments[0][0]["type"] == "text"
        assert captured_segments[0][1]["type"] == "mention"
        assert captured_segments[0][2]["type"] == "image"

    @pytest.mark.asyncio
    async def test_standard_methods_delegate_to_raw_ob12(self):
        """测试标准方法（Text/Image）委托给 Raw_ob12 时行为一致"""
        import asyncio

        calls = []

        class CustomAdapter(BaseAdapter):
            async def start(self):
                pass

            async def shutdown(self):
                pass

            async def call_api(self, endpoint: str, **params):
                return {"status": "ok", "retcode": 0, "data": {}, "message_id": "id"}

            class Send(BaseAdapter.Send):
                def Raw_ob12(self, message, **kwargs):
                    calls.append(message)
                    import asyncio

                    async def _do():
                        return {}

                    return asyncio.create_task(_do())

                def Text(self, text: str):
                    return self.Raw_ob12([{"type": "text", "data": {"text": text}}])

        adapter = CustomAdapter()
        # 通过 Text 方法发送
        await adapter.Send.To("user", "123").Text("Hello")
        # 直接调用 Raw_ob12
        await adapter.Send.To("user", "123").Raw_ob12(
            [{"type": "text", "data": {"text": "Hello"}}]
        )

        assert len(calls) == 2
        assert calls[0] == calls[1]


# ==================== Bot 状态追踪测试 ====================


class TestBotStatusTracking:
    """Bot 状态追踪测试类"""

    @pytest.fixture
    def manager(self):
        """创建适配器管理器实例"""
        manager = AdapterManager()
        manager._adapters.clear()
        manager._started_instances.clear()
        manager._adapter_info.clear()
        manager._onebot_handlers.clear()
        manager._raw_handlers.clear()
        manager._onebot_middlewares.clear()
        manager._bots.clear()
        return manager

    @pytest.fixture
    def test_adapter_class(self):
        """创建测试适配器类"""

        class TestAdapter(BaseAdapter):
            def __init__(self, sdk=None):
                super().__init__()
                self.sdk = sdk

            async def start(self):
                pass

            async def shutdown(self):
                pass

            async def call_api(self, endpoint: str, **params):
                return {
                    "status": "ok",
                    "retcode": 0,
                    "data": {},
                    "message_id": "test_id",
                }

        return TestAdapter

    # ==================== meta connect 事件测试 ====================

    @pytest.mark.asyncio
    async def test_meta_connect_registers_bot(self, manager):
        """测试 meta connect 事件注册 Bot"""
        event = {
            "id": "1",
            "time": 1712345678,
            "type": "meta",
            "detail_type": "connect",
            "platform": "telegram",
            "self": {
                "platform": "telegram",
                "user_id": "123456",
                "user_name": "TestBot",
                "avatar": "https://example.com/avatar.jpg",
            },
        }

        with patch.object(lifecycle, "submit_event", new_callable=AsyncMock):
            await manager.emit(event)
            await asyncio.sleep(0)

        # 验证 Bot 已注册
        bot_info = manager.get_bot_info("telegram", "123456")
        assert bot_info is not None
        assert bot_info["status"] == "online"
        assert bot_info["info"]["user_name"] == "TestBot"
        assert bot_info["info"]["avatar"] == "https://example.com/avatar.jpg"

    @pytest.mark.asyncio
    async def test_meta_connect_triggers_lifecycle_event(self, manager):
        """测试 meta connect 触发 adapter.bot.online 生命周期事件"""
        event = {
            "id": "1",
            "time": 1712345678,
            "type": "meta",
            "detail_type": "connect",
            "platform": "telegram",
            "self": {"platform": "telegram", "user_id": "123456"},
        }

        with patch.object(
            lifecycle, "submit_event", new_callable=AsyncMock
        ) as mock_submit:
            await manager.emit(event)
            await asyncio.sleep(0)
            # 验证 adapter.bot.online 事件被提交
            mock_submit.assert_called_once()
            call_args = mock_submit.call_args
            assert call_args[0][0] == "adapter.bot.online"
            assert call_args[1]["data"]["bot_id"] == "123456"
            assert call_args[1]["data"]["platform"] == "telegram"
            assert call_args[1]["data"]["status"] == "online"

    @pytest.mark.asyncio
    async def test_meta_connect_first_time_vs_repeat(self, manager):
        """测试首次和重复 meta connect"""
        with patch.object(lifecycle, "submit_event", new_callable=AsyncMock):
            # 第一次 connect
            await manager.emit(
                {
                    "id": "1",
                    "time": 1,
                    "type": "meta",
                    "detail_type": "connect",
                    "platform": "tg",
                    "self": {"platform": "tg", "user_id": "bot1", "user_name": "Bot1"},
                }
            )
            await asyncio.sleep(0)
            # 第二次 connect（应该更新元信息而不是报错）
            await manager.emit(
                {
                    "id": "2",
                    "time": 2,
                    "type": "meta",
                    "detail_type": "connect",
                    "platform": "tg",
                    "self": {
                        "platform": "tg",
                        "user_id": "bot1",
                        "user_name": "Bot1Updated",
                    },
                }
            )
            await asyncio.sleep(0)

        bot_info = manager.get_bot_info("tg", "bot1")
        assert bot_info["status"] == "online"
        assert bot_info["info"]["user_name"] == "Bot1Updated"

    # ==================== meta heartbeat 事件测试 ====================

    @pytest.mark.asyncio
    async def test_meta_heartbeat_updates_active_time(self, manager):
        """测试 meta heartbeat 更新活跃时间"""
        import time

        # 先注册 Bot
        with patch.object(lifecycle, "submit_event", new_callable=AsyncMock):
            await manager.emit(
                {
                    "id": "1",
                    "time": 1,
                    "type": "meta",
                    "detail_type": "connect",
                    "platform": "tg",
                    "self": {"platform": "tg", "user_id": "bot1"},
                }
            )
            await asyncio.sleep(0)

        old_active = manager.get_bot_info("tg", "bot1")["last_active"]
        time.sleep(0.05)

        # 发送心跳
        await manager.emit(
            {
                "id": "2",
                "time": 2,
                "type": "meta",
                "detail_type": "heartbeat",
                "platform": "tg",
                "self": {"platform": "tg", "user_id": "bot1"},
            }
        )
        await asyncio.sleep(0)

        new_active = manager.get_bot_info("tg", "bot1")["last_active"]
        assert new_active > old_active

    @pytest.mark.asyncio
    async def test_meta_heartbeat_updates_metadata(self, manager):
        """测试 meta heartbeat 更新元信息"""
        with patch.object(lifecycle, "submit_event", new_callable=AsyncMock):
            await manager.emit(
                {
                    "id": "1",
                    "time": 1,
                    "type": "meta",
                    "detail_type": "connect",
                    "platform": "tg",
                    "self": {"platform": "tg", "user_id": "bot1", "user_name": "Bot1"},
                }
            )
            await asyncio.sleep(0)

        # 心跳中更新头像
        await manager.emit(
            {
                "id": "2",
                "time": 2,
                "type": "meta",
                "detail_type": "heartbeat",
                "platform": "tg",
                "self": {
                    "platform": "tg",
                    "user_id": "bot1",
                    "avatar": "https://new.avatar.jpg",
                },
            }
        )
        await asyncio.sleep(0)

        bot_info = manager.get_bot_info("tg", "bot1")
        assert bot_info["info"]["user_name"] == "Bot1"
        assert bot_info["info"]["avatar"] == "https://new.avatar.jpg"

    @pytest.mark.asyncio
    async def test_meta_heartbeat_unknown_bot_no_crash(self, manager):
        """测试 meta heartbeat 对未知 Bot 不崩溃"""
        await manager.emit(
            {
                "id": "1",
                "time": 1,
                "type": "meta",
                "detail_type": "heartbeat",
                "platform": "tg",
                "self": {"platform": "tg", "user_id": "unknown_bot"},
            }
        )
        await asyncio.sleep(0)
        # 不崩溃即可
        assert manager.get_bot_info("tg", "unknown_bot") is None

    # ==================== meta disconnect 事件测试 ====================

    @pytest.mark.asyncio
    async def test_meta_disconnect_marks_offline(self, manager):
        """测试 meta disconnect 标记 Bot 离线"""
        with patch.object(lifecycle, "submit_event", new_callable=AsyncMock):
            # 先上线
            await manager.emit(
                {
                    "id": "1",
                    "time": 1,
                    "type": "meta",
                    "detail_type": "connect",
                    "platform": "tg",
                    "self": {"platform": "tg", "user_id": "bot1"},
                }
            )
            await asyncio.sleep(0)

        assert manager.is_bot_online("tg", "bot1") is True

        # 断开连接
        with patch.object(lifecycle, "submit_event", new_callable=AsyncMock):
            await manager.emit(
                {
                    "id": "2",
                    "time": 2,
                    "type": "meta",
                    "detail_type": "disconnect",
                    "platform": "tg",
                    "self": {"platform": "tg", "user_id": "bot1"},
                }
            )
            await asyncio.sleep(0)

        assert manager.is_bot_online("tg", "bot1") is False
        bot_info = manager.get_bot_info("tg", "bot1")
        assert bot_info["status"] == "offline"

    @pytest.mark.asyncio
    async def test_meta_disconnect_unknown_bot(self, manager):
        """测试 meta disconnect 对未知 Bot 不崩溃"""
        with patch.object(lifecycle, "submit_event", new_callable=AsyncMock):
            await manager.emit(
                {
                    "id": "1",
                    "time": 1,
                    "type": "meta",
                    "detail_type": "disconnect",
                    "platform": "tg",
                    "self": {"platform": "tg", "user_id": "unknown_bot"},
                }
            )
            await asyncio.sleep(0)
        # 应该被注册但状态为 offline
        bot_info = manager.get_bot_info("tg", "unknown_bot")
        assert bot_info is not None
        assert bot_info["status"] == "offline"

    # ==================== 普通事件自动发现测试 ====================

    @pytest.mark.asyncio
    async def test_message_event_auto_discovers_bot(self, manager):
        """测试普通消息事件自动发现 Bot"""
        await manager.emit(
            {
                "id": "1",
                "time": 1,
                "type": "message",
                "detail_type": "group",
                "platform": "tg",
                "self": {"platform": "tg", "user_id": "bot1", "user_name": "AutoBot"},
                "message": [{"type": "text", "data": {"text": "hi"}}],
            }
        )
        await asyncio.sleep(0)

        bot_info = manager.get_bot_info("tg", "bot1")
        assert bot_info is not None
        assert bot_info["status"] == "online"
        assert bot_info["info"]["user_name"] == "AutoBot"

    @pytest.mark.asyncio
    async def test_notice_event_auto_discovers_bot(self, manager):
        """测试通知事件自动发现 Bot"""
        await manager.emit(
            {
                "id": "1",
                "time": 1,
                "type": "notice",
                "detail_type": "friend_add",
                "platform": "tg",
                "self": {"platform": "tg", "user_id": "bot1"},
                "user_id": "user1",
            }
        )
        await asyncio.sleep(0)

        assert manager.is_bot_online("tg", "bot1") is True

    @pytest.mark.asyncio
    async def test_event_without_self_no_crash(self, manager):
        """测试无 self 字段的事件不崩溃"""
        await manager.emit(
            {"id": "1", "time": 1, "type": "message", "platform": "tg", "message": []}
        )
        await asyncio.sleep(0)
        # 不崩溃即可
        assert len(manager._bots) == 0

    @pytest.mark.asyncio
    async def test_event_with_self_no_userid_no_crash(self, manager):
        """测试 self 字段无 user_id 的事件不崩溃"""
        await manager.emit(
            {
                "id": "1",
                "time": 1,
                "type": "message",
                "platform": "tg",
                "self": {"platform": "tg"},
            }
        )
        await asyncio.sleep(0)
        # 不崩溃即可
        assert len(manager._bots) == 0

    # ==================== self 字段元信息提取测试 ====================

    @pytest.mark.asyncio
    async def test_self_field_metadata_extraction(self, manager):
        """测试 self 字段扩展元信息提取"""
        with patch.object(lifecycle, "submit_event", new_callable=AsyncMock):
            await manager.emit(
                {
                    "id": "1",
                    "time": 1,
                    "type": "meta",
                    "detail_type": "connect",
                    "platform": "tg",
                    "self": {
                        "platform": "tg",
                        "user_id": "bot1",
                        "user_name": "MyBot",
                        "avatar": "https://avatar.jpg",
                        "account_id": "acc_001",
                    },
                }
            )
            await asyncio.sleep(0)

        bot_info = manager.get_bot_info("tg", "bot1")
        assert bot_info["info"]["user_name"] == "MyBot"
        assert bot_info["info"]["avatar"] == "https://avatar.jpg"
        assert bot_info["info"]["account_id"] == "acc_001"

    @pytest.mark.asyncio
    async def test_metadata_merge_on_repeated_events(self, manager):
        """测试重复事件时元信息合并"""
        with patch.object(lifecycle, "submit_event", new_callable=AsyncMock):
            # 第一次：只有 user_name
            await manager.emit(
                {
                    "id": "1",
                    "time": 1,
                    "type": "meta",
                    "detail_type": "connect",
                    "platform": "tg",
                    "self": {"platform": "tg", "user_id": "bot1", "user_name": "Bot1"},
                }
            )
            await asyncio.sleep(0)

            # 第二次：添加 avatar
            await manager.emit(
                {
                    "id": "2",
                    "time": 2,
                    "type": "message",
                    "platform": "tg",
                    "self": {
                        "platform": "tg",
                        "user_id": "bot1",
                        "avatar": "https://new.jpg",
                    },
                    "message": [],
                }
            )
            await asyncio.sleep(0)

        bot_info = manager.get_bot_info("tg", "bot1")
        assert bot_info["info"]["user_name"] == "Bot1"
        assert bot_info["info"]["avatar"] == "https://new.jpg"

    # ==================== 查询方法测试 ====================

    def test_get_bot_info_nonexistent(self, manager):
        """测试获取不存在的 Bot 信息"""
        assert manager.get_bot_info("tg", "bot1") is None

    def test_list_bots_all(self, manager):
        """测试列出所有 Bot"""
        manager._bots = {
            "tg": {"bot1": {"status": "online", "last_active": 1.0, "info": {}}},
            "dc": {"bot2": {"status": "offline", "last_active": 2.0, "info": {}}},
        }
        result = manager.list_bots()
        assert "tg" in result
        assert "dc" in result
        assert "bot1" in result["tg"]
        assert "bot2" in result["dc"]

    def test_list_bots_by_platform(self, manager):
        """测试列出指定平台的 Bot"""
        manager._bots = {
            "tg": {"bot1": {"status": "online", "last_active": 1.0, "info": {}}},
            "dc": {"bot2": {"status": "offline", "last_active": 2.0, "info": {}}},
        }
        result = manager.list_bots("tg")
        assert "tg" in result
        assert "dc" not in result

    def test_list_bots_empty_platform(self, manager):
        """测试列出不存在的平台"""
        result = manager.list_bots("nonexistent")
        assert result == {"nonexistent": {}}

    def test_is_bot_online(self, manager):
        """测试检查 Bot 是否在线"""
        manager._bots = {
            "tg": {
                "bot1": {"status": "online", "last_active": 1.0, "info": {}},
                "bot2": {"status": "offline", "last_active": 2.0, "info": {}},
            }
        }
        assert manager.is_bot_online("tg", "bot1") is True
        assert manager.is_bot_online("tg", "bot2") is False
        assert manager.is_bot_online("tg", "bot3") is False
        assert manager.is_bot_online("dc", "bot1") is False

    def test_get_status_summary(self, manager, test_adapter_class):
        """测试获取状态摘要"""
        manager.register("tg", test_adapter_class)
        manager._bots = {
            "tg": {
                "bot1": {
                    "status": "online",
                    "last_active": 1.0,
                    "info": {"user_name": "Bot1"},
                }
            }
        }
        summary = manager.get_status_summary()
        assert "adapters" in summary
        assert "tg" in summary["adapters"]
        assert summary["adapters"]["tg"]["status"] == "stopped"
        assert "bot1" in summary["adapters"]["tg"]["bots"]
        assert summary["adapters"]["tg"]["bots"]["bot1"]["status"] == "online"

    # ==================== shutdown 标记离线测试 ====================

    @pytest.mark.asyncio
    async def test_shutdown_marks_all_bots_offline(self, manager, test_adapter_class):
        """测试 shutdown 将所有 Bot 标记为离线"""
        manager.register("tg", test_adapter_class)

        # 模拟 Bot 上线
        manager._bots = {
            "tg": {
                "bot1": {"status": "online", "last_active": 1.0, "info": {}},
                "bot2": {"status": "online", "last_active": 2.0, "info": {}},
            }
        }

        with patch.object(router, "stop"):
            await manager.shutdown()

        # 验证所有 Bot 都离线
        assert manager.is_bot_online("tg", "bot1") is False
        assert manager.is_bot_online("tg", "bot2") is False

    # ==================== clear 清理测试 ====================

    def test_clear_clears_bot_state(self, manager):
        """测试 clear 清理 Bot 状态"""
        manager._bots = {
            "tg": {"bot1": {"status": "online", "last_active": 1.0, "info": {}}}
        }
        manager.clear()
        assert len(manager._bots) == 0

    # ==================== 多平台多 Bot 测试 ====================

    @pytest.mark.asyncio
    async def test_multiple_platforms_multiple_bots(self, manager):
        """测试多平台多 Bot 场景"""
        with patch.object(lifecycle, "submit_event", new_callable=AsyncMock):
            # Telegram Bot 上线
            await manager.emit(
                {
                    "id": "1",
                    "time": 1,
                    "type": "meta",
                    "detail_type": "connect",
                    "platform": "telegram",
                    "self": {
                        "platform": "telegram",
                        "user_id": "tg_bot1",
                        "user_name": "TGBot",
                    },
                }
            )
            await asyncio.sleep(0)
            # Discord Bot 上线
            await manager.emit(
                {
                    "id": "2",
                    "time": 2,
                    "type": "meta",
                    "detail_type": "connect",
                    "platform": "discord",
                    "self": {
                        "platform": "discord",
                        "user_id": "dc_bot1",
                        "user_name": "DCBot",
                    },
                }
            )
            await asyncio.sleep(0)

        # 验证两个平台的 Bot 都已注册
        assert manager.is_bot_online("telegram", "tg_bot1") is True
        assert manager.is_bot_online("discord", "dc_bot1") is True

        all_bots = manager.list_bots()
        assert "telegram" in all_bots
        assert "discord" in all_bots

        # Telegram Bot 离线
        with patch.object(lifecycle, "submit_event", new_callable=AsyncMock):
            await manager.emit(
                {
                    "id": "3",
                    "time": 3,
                    "type": "meta",
                    "detail_type": "disconnect",
                    "platform": "telegram",
                    "self": {"platform": "telegram", "user_id": "tg_bot1"},
                }
            )
            await asyncio.sleep(0)

        assert manager.is_bot_online("telegram", "tg_bot1") is False
        assert manager.is_bot_online("discord", "dc_bot1") is True


# ==================== 事件处理器 Task 追踪与并发控制测试 ====================


class TestHandlerTaskTracking:
    """事件处理器 Task 追踪、并发背压和清理功能测试"""

    @pytest.fixture
    def manager(self):
        """创建适配器管理器实例"""
        manager = AdapterManager()
        manager._adapters.clear()
        manager._started_instances.clear()
        manager._adapter_info.clear()
        manager._onebot_handlers.clear()
        manager._raw_handlers.clear()
        manager._onebot_middlewares.clear()
        manager._pending_handler_tasks.clear()
        manager._bots.clear()
        manager._adapter_tasks.clear()
        manager._handler_semaphore = None
        manager._handler_max_concurrency = 0
        return manager

    @pytest.mark.asyncio
    async def test_dispatch_creates_tracked_task(self, manager):
        """测试分发处理器时 Task 被追踪到 _pending_handler_tasks"""

        async def handler(data):
            await asyncio.sleep(0.01)

        manager._dispatch_handler_task(handler, {"test": True})

        # Task 应被追踪
        assert len(manager._pending_handler_tasks) == 1

        # 等待 Task 完成
        await asyncio.sleep(0.1)

        # Task 完成后应自动从集合中移除
        assert len(manager._pending_handler_tasks) == 0

    @pytest.mark.asyncio
    async def test_handler_semaphore_limits_concurrency(self, manager):
        """测试信号量限制处理器并发数"""

        # 手动设置较小的并发限制
        manager._handler_max_concurrency = 2
        manager._handler_semaphore = asyncio.Semaphore(2)

        executing = []
        max_concurrent = [0]

        async def slow_handler(data):
            executing.append(1)
            max_concurrent[0] = max(max_concurrent[0], len(executing))
            await asyncio.sleep(0.05)
            executing.pop()

        # 启动 5 个处理器
        for i in range(5):
            manager._dispatch_handler_task(slow_handler, {"index": i})

        await asyncio.sleep(0.3)

        # 最大并发数不超过 2
        assert max_concurrent[0] <= 2

    @pytest.mark.asyncio
    async def test_drain_pending_handler_tasks(self, manager):
        """测试 drain 方法取消所有在途 Task"""

        async def long_handler(data):
            await asyncio.sleep(100)

        # 启动 3 个长时间运行的处理器
        for i in range(3):
            manager._dispatch_handler_task(long_handler, {"index": i})

        assert len(manager._pending_handler_tasks) == 3

        # 执行 drain
        await manager._drain_pending_handler_tasks(timeout=1.0)

        # 所有 Task 应被取消并清除
        assert len(manager._pending_handler_tasks) == 0

    def test_evict_offline_bots(self, manager):
        """测试清除过期的离线 Bot 记录"""
        import time

        # 添加在线和离线 Bot
        manager._bots = {
            "platform1": {
                "bot1": {
                    "status": "online",
                    "last_active": time.time(),
                    "info": {},
                },
                "bot2": {
                    "status": "offline",
                    "last_active": time.time() - 7200,  # 2小时前
                    "info": {},
                },
            }
        }

        # 清除 1 小时前的离线 Bot
        evicted = manager._evict_offline_bots(expiry_secs=3600)

        assert evicted == 1
        assert "bot2" not in manager._bots["platform1"]
        assert "bot1" in manager._bots["platform1"]

    def test_evict_offline_bots_disabled(self, manager):
        """测试 expiry_secs=0 时禁用清除"""
        import time

        manager._bots = {
            "p1": {
                "b1": {
                    "status": "offline",
                    "last_active": time.time() - 999999,
                    "info": {},
                }
            }
        }

        evicted = manager._evict_offline_bots(expiry_secs=0)
        assert evicted == 0
        assert "b1" in manager._bots["p1"]

    def test_evict_offline_bots_cleans_empty_platforms(self, manager):
        """测试清除后空的平台也会被移除"""
        import time

        manager._bots = {
            "p1": {
                "b1": {
                    "status": "offline",
                    "last_active": time.time() - 999999,
                    "info": {},
                }
            },
            "p2": {
                "b2": {
                    "status": "online",
                    "last_active": time.time(),
                    "info": {},
                }
            },
        }

        manager._evict_offline_bots(expiry_secs=1)

        # p1 的唯一 bot 被清除，p1 应被移除
        assert "p1" not in manager._bots
        assert "p2" in manager._bots


# ==================== SendDSL 标准发送方法测试 ====================


class TestSendDSLStandardMethods:
    """SendDSL 基类内置标准发送方法（Text/Image/Voice/Video/File）测试"""

    @pytest.fixture
    def adapter_with_raw_ob12(self):
        """创建一个只实现 Raw_ob12 的适配器，验证标准方法是否自动委托"""

        class _Send(BaseAdapter.Send):
            def Raw_ob12(self, message, **kwargs):
                async def _do():
                    segments = self._apply_modifiers(message)
                    return await self._adapter.call_api(
                        endpoint="/send_message",
                        message=segments,
                        **self.send_context,
                        **kwargs,
                    )
                return asyncio.ensure_future(_do())

        class _Adapter(BaseAdapter):
            Send = _Send

            async def start(self):
                pass

            async def shutdown(self):
                pass

            async def call_api(self, endpoint: str, **params):
                return {
                    "status": "ok",
                    "retcode": 0,
                    "data": {"endpoint": endpoint, "params": params},
                    "message_id": "mid_test",
                    "message": "",
                }

        return _Adapter()

    @pytest.mark.asyncio
    async def test_text_delegates_to_raw_ob12(self, adapter_with_raw_ob12):
        """Text 应自动委托给 Raw_ob12，无需子类实现"""
        result = await adapter_with_raw_ob12.Send.To("user", "123").Text("hello")
        assert result["status"] == "ok"
        # 验证消息段是 text 类型
        params = result["data"]["params"]
        message = params["message"]
        assert any(seg["type"] == "text" and seg["data"]["text"] == "hello" for seg in message)

    @pytest.mark.asyncio
    async def test_image_delegates_to_raw_ob12(self, adapter_with_raw_ob12):
        """Image 应自动委托给 Raw_ob12"""
        result = await adapter_with_raw_ob12.Send.To("user", "123").Image("http://example.com/img.png")
        assert result["status"] == "ok"
        message = result["data"]["params"]["message"]
        assert any(seg["type"] == "image" for seg in message)

    @pytest.mark.asyncio
    async def test_voice_delegates_to_raw_ob12(self, adapter_with_raw_ob12):
        """Voice 应自动委托给 Raw_ob12（OneBot12 audio 段）"""
        result = await adapter_with_raw_ob12.Send.To("user", "123").Voice("http://example.com/voice.mp3")
        assert result["status"] == "ok"
        message = result["data"]["params"]["message"]
        # OneBot12 标准中语音为 audio 类型
        assert any(seg["type"] == "audio" for seg in message)

    @pytest.mark.asyncio
    async def test_video_delegates_to_raw_ob12(self, adapter_with_raw_ob12):
        """Video 应自动委托给 Raw_ob12"""
        result = await adapter_with_raw_ob12.Send.To("user", "123").Video("http://example.com/video.mp4")
        assert result["status"] == "ok"
        message = result["data"]["params"]["message"]
        assert any(seg["type"] == "video" for seg in message)

    @pytest.mark.asyncio
    async def test_file_delegates_to_raw_ob12(self, adapter_with_raw_ob12):
        """File 应自动委托给 Raw_ob12"""
        result = await adapter_with_raw_ob12.Send.To("user", "123").File("http://example.com/doc.pdf")
        assert result["status"] == "ok"
        message = result["data"]["params"]["message"]
        assert any(seg["type"] == "file" for seg in message)

    @pytest.mark.asyncio
    async def test_file_with_filename(self, adapter_with_raw_ob12):
        """File 支持可选 filename 参数"""
        result = await adapter_with_raw_ob12.Send.To("user", "123").File("http://example.com/doc.pdf", filename="doc.pdf")
        assert result["status"] == "ok"
        message = result["data"]["params"]["message"]
        file_seg = next(seg for seg in message if seg["type"] == "file")
        assert file_seg["data"]["filename"] == "doc.pdf"

    @pytest.mark.asyncio
    async def test_text_with_modifiers(self, adapter_with_raw_ob12):
        """Text + At/Reply 修饰器应正确合并到消息段"""
        result = await (adapter_with_raw_ob12.Send
                        .To("group", "456")
                        .At("789")
                        .Reply("msg_123")
                        .Text("带修饰器的文本"))
        assert result["status"] == "ok"
        message = result["data"]["params"]["message"]
        types = [seg["type"] for seg in message]
        assert "mention" in types
        assert "reply" in types
        assert "text" in types

    def test_standard_methods_exist_on_base(self):
        """标准发送方法应存在于 SendDSL 基类上（供 IDE 补全）"""
        for method in ("Text", "Image", "Voice", "Video", "File", "Raw_ob12"):
            assert hasattr(SendDSL, method), f"SendDSL 应定义 {method} 方法"
            assert callable(getattr(SendDSL, method))


class TestListSends:
    """list_sends 方法测试（验证标准方法与平台特有方法都能被列出）"""

    @pytest.fixture
    def manager(self):
        """创建适配器管理器实例"""
        manager = AdapterManager()
        manager._adapters.clear()
        manager._started_instances.clear()
        manager._adapter_info.clear()
        return manager

    def test_list_sends_includes_standard_methods(self, manager):
        """list_sends 应包含标准发送方法（Text/Image 等）"""

        class _Adapter(BaseAdapter):
            async def start(self):
                pass

            async def shutdown(self):
                pass

            async def call_api(self, endpoint: str, **params):
                return {"status": "ok", "retcode": 0, "data": {}}

        manager.register("testplat", _Adapter)
        methods = manager.list_sends("testplat")
        # 标准方法应被列出
        assert "Text" in methods
        assert "Image" in methods
        assert "Voice" in methods
        assert "Video" in methods
        assert "File" in methods
        assert "Raw_ob12" in methods

    def test_list_sends_includes_platform_methods(self, manager):
        """list_sends 应包含平台特有的发送方法"""

        class _Send(BaseAdapter.Send):
            def Sticker(self, sticker_id: str):
                return self.Raw_ob12([{"type": "sticker", "data": {"id": sticker_id}}])

        class _Adapter(BaseAdapter):
            Send = _Send

            async def start(self):
                pass

            async def shutdown(self):
                pass

            async def call_api(self, endpoint: str, **params):
                return {"status": "ok", "retcode": 0, "data": {}}

        manager.register("testplat", _Adapter)
        methods = manager.list_sends("testplat")
        # 平台特有方法应被列出
        assert "Sticker" in methods
        # 标准方法也应被列出
        assert "Text" in methods

    def test_list_sends_excludes_chain_modifiers(self, manager):
        """list_sends 应排除链式修饰方法（At/To/Hook 等）"""

        class _Adapter(BaseAdapter):
            async def start(self):
                pass

            async def shutdown(self):
                pass

            async def call_api(self, endpoint: str, **params):
                return {"status": "ok", "retcode": 0, "data": {}}

        manager.register("testplat", _Adapter)
        methods = manager.list_sends("testplat")
        # 链式修饰方法不应被列出
        for chain_method in ("At", "AtAll", "Reply", "To", "Using", "Account",
                             "Hook", "Retry", "Timeout", "Defer", "Build"):
            assert chain_method not in methods, f"链式方法 {chain_method} 不应被列为发送方法"


# ==================== 返回 self 的平台修饰方法测试 ====================
# 平台无需任何装饰器：只要方法返回 self（SendDSL 实例），
# _wrap_send_method 会自动识别并不对其触发发送包装/生命周期事件。


class TestSendDSLReturnSelfModifier:
    """返回 self 的平台修饰方法（无需装饰器）链式调用测试"""

    @pytest.fixture
    def adapter_with_self_modifier(self):
        """创建带返回-self 修饰方法与依赖修饰的发送方法的适配器"""

        class _Send(BaseAdapter.Send):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self._expire = None
                self._member = None

            def Raw_ob12(self, message, **kwargs):
                async def _do():
                    segments = self._apply_modifiers(message)
                    return await self._adapter.call_api(
                        endpoint="/send_message",
                        message=segments,
                        expire=self._expire,
                        member=self._member,
                        **self.send_context,
                        **kwargs,
                    )
                return asyncio.ensure_future(_do())

            # 平台修饰方法：仅返回 self，无需任何装饰器
            def Expire(self, seconds: int):
                self._expire = seconds
                return self

            def ForMember(self, user_id: str):
                self._member = user_id
                return self

            def Board(self, content: str, **kwargs):
                return self.Raw_ob12([{"type": "board", "data": {"text": content}}])

        class _Adapter(BaseAdapter):
            Send = _Send

            async def start(self):
                pass

            async def shutdown(self):
                pass

            async def call_api(self, endpoint: str, **params):
                return {
                    "status": "ok",
                    "retcode": 0,
                    "data": {"endpoint": endpoint, "params": params},
                    "message_id": "mid_test",
                    "message": "",
                }

        return _Adapter()

    @pytest.mark.asyncio
    async def test_return_self_modifier_preserves_chain(self, adapter_with_self_modifier):
        """返回 self 的方法应保持链式（同一实例），不触发发送副作用"""
        chain = adapter_with_self_modifier.Send.To("group", "g1")
        result = chain.Expire(3600)
        assert result is chain
        assert chain._expire == 3600

        result2 = chain.ForMember("u123")
        assert result2 is chain
        assert chain._member == "u123"

    @pytest.mark.asyncio
    async def test_send_method_reads_modifier_state(self, adapter_with_self_modifier):
        """发送方法（Board）应能读取返回-self 修饰方法设置的状态"""
        result = await (adapter_with_self_modifier.Send
                        .To("group", "g1")
                        .Expire(3600)
                        .ForMember("u9")
                        .Board("看板内容"))
        assert result["status"] == "ok"
        params = result["data"]["params"]
        assert params["expire"] == 3600
        assert params["member"] == "u9"
        assert any(seg["type"] == "board" for seg in params["message"])

    @pytest.mark.asyncio
    async def test_multiple_return_self_modifiers_chain(self, adapter_with_self_modifier):
        """多个返回-self 的修饰方法应可连续链式调用"""
        chain = (adapter_with_self_modifier.Send
                 .To("group", "g1")
                 .Expire(100)
                 .ForMember("abc"))
        result = await chain.Board("hi")
        assert result["status"] == "ok"
        params = result["data"]["params"]
        assert params["expire"] == 100
        assert params["member"] == "abc"
