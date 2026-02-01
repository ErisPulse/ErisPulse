"""
适配器系统单元测试

测试适配器管理器和基础适配器类的功能
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from typing import Dict, Any

from ErisPulse.Core.adapter import AdapterManager
from ErisPulse.Core.Bases import BaseAdapter, SendDSL
from ErisPulse.Core.config import config
from ErisPulse.Core.lifecycle import lifecycle
from ErisPulse.Core import router


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
                    "test_raw": params
                }
        
        return TestAdapter
    
    # ==================== 注册测试 ====================
    
    def test_register_adapter_success(self, manager, test_adapter_class):
        """测试成功注册适配器"""
        # 执行
        result = manager.register("test_platform", test_adapter_class, {"version": "1.0.0"})
        
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
        with pytest.raises(TypeError, match="必须继承自BaseAdapter"):
            manager.register("invalid", InvalidAdapter)
    
    def test_register_adapter_duplicate(self, manager, test_adapter_class):
        """测试注册重复的适配器"""
        # 第一次注册
        manager.register("test_platform", test_adapter_class)
        
        # 第二次注册（覆盖，会记录 warning 日志）
        manager.register("test_platform", test_adapter_class)
        
        # 验证仍然只有一个实例（因为同一类会复用实例）
        assert len([a for a in manager._adapters.values() if isinstance(a, test_adapter_class)]) == 1
    
    def test_register_adapter_multiple_platforms_same_class(self, manager, test_adapter_class):
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
        # 注册多个适配器
        manager.register("platform1", test_adapter_class)
        manager.register("platform2", test_adapter_class)
        
        # Mock router
        with patch.object(router, 'start') as mock_router_start:
            # 执行
            await manager.startup()
            
            # 验证路由器启动
            mock_router_start.assert_called_once()
            
            # 验证适配器已调度（异步启动）
            assert len(manager._started_instances) == 0  # 异步，还未完成
    
    @pytest.mark.asyncio
    async def test_startup_specific_adapters(self, manager, test_adapter_class):
        """测试启动指定的适配器"""
        # 注册多个适配器
        manager.register("platform1", test_adapter_class)
        manager.register("platform2", test_adapter_class)
        
        # Mock router
        with patch.object(router, 'start') as mock_router_start:
            # 执行
            await manager.startup(["platform1"])
            
            # 验证路由器启动
            mock_router_start.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_startup_nonexistent_platform(self, manager):
        """测试启动不存在的平台"""
        # 执行和验证
        with pytest.raises(ValueError, match="平台.*未注册"):
            await manager.startup(["nonexistent"])
    
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
        with patch.object(router, 'stop'):
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
        with patch.object(config, 'getConfig', return_value={}):
            # 注册并检查
            manager.register("test_platform", test_adapter_class)
            
            # 验证
            assert manager.exists("test_platform") is True
            assert manager.exists("nonexistent") is False
    
    def test_adapter_is_enabled(self, manager):
        """测试检查适配器是否启用"""
        with patch.object(config, 'getConfig') as mock_get:
            # 启用状态
            mock_get.return_value = True
            assert manager.is_enabled("test_platform") is True
            
            # 禁用状态
            mock_get.return_value = False
            assert manager.is_enabled("test_platform") is False
            
            # 未配置状态
            mock_get.return_value = None
            assert manager.is_enabled("test_platform") is False
    
    def test_adapter_enable(self, manager, test_adapter_class):
        """测试启用适配器"""
        # 先注册适配器
        manager.register("test_platform", test_adapter_class)
        
        with patch.object(config, 'setConfig') as mock_set:
            # 执行
            result = manager.enable("test_platform")
            
            # 验证
            assert result is True
            mock_set.assert_called_once_with("ErisPulse.adapters.status.test_platform", True)
    
    def test_adapter_disable(self, manager, test_adapter_class):
        """测试禁用适配器"""
        # 先注册适配器
        manager.register("test_platform", test_adapter_class)
        
        with patch.object(config, 'setConfig') as mock_set:
            # 执行
            result = manager.disable("test_platform")
            
            # 验证
            assert result is True
            mock_set.assert_called_once_with("ErisPulse.adapters.status.test_platform", False)
    
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
    
    def test_contains_operator(self, manager, test_adapter_class):
        """测试包含操作符"""
        with patch.object(config, 'getConfig', return_value=True):
            # 启用的适配器（先注册）
            with patch.object(config, 'setConfig'):
                manager.register("enabled", test_adapter_class)
                assert "enabled" in manager
            
            # 禁用的适配器
            with patch.object(config, 'getConfig', return_value=False):
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
            "message": [{"type": "text", "data": {"text": "test"}}]
        }
        
        await manager.emit(event_data)
        
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
            "test_raw_type": "test_raw_event"
        }
        
        await manager.emit(event_data)
        
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
            "message": []
        }
        
        await manager.emit(event_data)
        
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
                    "message_id": "test_id"
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
                    "message_id": "test_id"
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
        
        adapter = IncompleteAdapter()
        
        # 验证抽象方法抛出异常
        with pytest.raises(NotImplementedError):
            asyncio.run(adapter.start())
        
        with pytest.raises(NotImplementedError):
            asyncio.run(adapter.shutdown())
        
        with pytest.raises(NotImplementedError):
            asyncio.run(adapter.call_api("/test"))
