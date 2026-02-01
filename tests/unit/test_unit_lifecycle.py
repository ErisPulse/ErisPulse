"""
生命周期管理单元测试

测试生命周期事件管理器的功能
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any

from ErisPulse.Core.lifecycle import LifecycleManager, lifecycle
from ErisPulse.Core.logger import logger


# ==================== LifecycleManager 测试 ====================

class TestLifecycleManager:
    """生命周期管理器测试类"""
    
    @pytest.fixture
    def manager(self):
        """创建生命周期管理器实例"""
        manager = LifecycleManager()
        manager._handlers.clear()
        manager._timers.clear()
        return manager
    
    # ==================== 事件注册测试 ====================
    
    def test_register_handler(self, manager):
        """测试注册事件处理器"""
        called = []
        
        def test_handler(event_data):
            called.append(event_data)
        
        # 执行
        manager.on("test_event")(test_handler)
        
        # 验证
        assert "test_event" in manager._handlers
        assert len(manager._handlers["test_event"]) == 1
    
    def test_register_multiple_handlers(self, manager):
        """测试注册多个处理器到同一事件"""
        called = []
        
        def handler1(event_data):
            called.append(1)
        
        def handler2(event_data):
            called.append(2)
        
        # 执行
        manager.on("test_event")(handler1)
        manager.on("test_event")(handler2)
        
        # 验证
        assert len(manager._handlers["test_event"]) == 2
    
    def test_register_invalid_event_name(self, manager):
        """测试注册无效的事件名"""
        # 空字符串
        with pytest.raises(ValueError, match="非空字符串"):
            manager.on("")
        
        # None
        with pytest.raises(ValueError, match="非空字符串"):
            manager.on(None)
    
    # ==================== 计时器测试 ====================
    
    def test_start_timer(self, manager):
        """测试开始计时"""
        import time
        
        # 执行
        manager.start_timer("test_timer")
        
        # 验证
        assert "test_timer" in manager._timers
        assert isinstance(manager._timers["test_timer"], float)
    
    def test_get_duration(self, manager):
        """测试获取持续时间"""
        import time
        
        # 开始计时
        manager.start_timer("test_timer")
        
        # 等待一小段时间
        time.sleep(0.1)
        
        # 执行
        duration = manager.get_duration("test_timer")
        
        # 验证
        assert duration >= 0.1
        assert duration < 0.2
    
    def test_stop_timer(self, manager):
        """测试停止计时"""
        import time
        
        # 开始计时
        manager.start_timer("test_timer")
        
        # 等待一小段时间
        time.sleep(0.1)
        
        # 停止计时
        duration = manager.stop_timer("test_timer")
        
        # 验证
        assert duration >= 0.1
        assert "test_timer" not in manager._timers
    
    def test_stop_nonexistent_timer(self, manager):
        """测试停止不存在的计时器"""
        # 执行
        duration = manager.stop_timer("nonexistent")
        
        # 验证（返回0）
        assert duration == 0.0
    
    def test_get_duration_nonexistent_timer(self, manager):
        """测试获取不存在的计时器持续时间"""
        # 执行
        duration = manager.get_duration("nonexistent")
        
        # 验证（返回0）
        assert duration == 0.0
    
    # ==================== 事件提交测试 ====================
    
    @pytest.mark.asyncio
    async def test_submit_event_success(self, manager):
        """测试成功提交事件"""
        called = []
        
        def handler(event_data):
            called.append(event_data)
        
        # 注册处理器
        manager.on("test_event")(handler)
        
        # 执行
        await manager.submit_event("test_event", data={"test": True})
        
        # 验证
        assert len(called) == 1
        assert called[0]["event"] == "test_event"
        assert called[0]["data"]["test"] is True
    
    @pytest.mark.asyncio
    async def test_submit_event_with_custom_fields(self, manager):
        """测试提交带自定义字段的事件"""
        called = []
        
        def handler(event_data):
            called.append(event_data)
        
        # 注册处理器
        manager.on("custom_event")(handler)
        
        # 执行
        await manager.submit_event(
            "custom_event",
            source="TestModule",
            msg="自定义消息",
            data={"key": "value"}
        )
        
        # 验证
        assert len(called) == 1
        assert called[0]["event"] == "custom_event"
        assert called[0]["source"] == "TestModule"
        assert called[0]["msg"] == "自定义消息"
        assert called[0]["data"]["key"] == "value"
        assert "timestamp" in called[0]
    
    @pytest.mark.asyncio
    async def test_submit_event_wildcard_handler(self, manager):
        """测试通配符处理器"""
        called = []
        
        def wildcard_handler(event_data):
            called.append(("wildcard", event_data))
        
        # 注册通配符处理器
        manager.on("*")(wildcard_handler)
        
        # 执行
        await manager.submit_event("any_event")
        
        # 验证
        assert len(called) == 1
        assert called[0][0] == "wildcard"
    
    @pytest.mark.asyncio
    async def test_submit_event_parent_handler(self, manager):
        """测试父级事件处理器（点式结构）"""
        called = []
        
        def parent_handler(event_data):
            called.append(("parent", event_data))
        
        def specific_handler(event_data):
            called.append(("specific", event_data))
        
        # 注册父级和特定处理器
        manager.on("module")(parent_handler)
        manager.on("module.init")(specific_handler)
        
        # 执行
        await manager.submit_event("module.init")
        
        # 验证（父级和特定都会被触发）
        assert len(called) == 2
        assert any(c[0] == "parent" for c in called)
        assert any(c[0] == "specific" for c in called)
    
    @pytest.mark.asyncio
    async def test_submit_event_multiple_handlers(self, manager):
        """测试事件触发多个处理器"""
        called = []
        
        def handler1(event_data):
            called.append(1)
        
        def handler2(event_data):
            called.append(2)
        
        def handler3(event_data):
            called.append(3)
        
        # 注册多个处理器
        manager.on("test_event")(handler1)
        manager.on("test_event")(handler2)
        manager.on("test_event")(handler3)
        
        # 执行
        await manager.submit_event("test_event")
        
        # 验证（所有处理器都被调用）
        assert len(called) == 3
        assert 1 in called
        assert 2 in called
        assert 3 in called
    
    @pytest.mark.asyncio
    async def test_submit_event_async_handler(self, manager):
        """测试异步事件处理器"""
        called = []
        
        async def async_handler(event_data):
            await asyncio.sleep(0.01)
            called.append("async")
        
        # 注册异步处理器
        manager.on("async_event")(async_handler)
        
        # 执行
        await manager.submit_event("async_event")
        
        # 验证
        assert len(called) == 1
        assert called[0] == "async"
    
    @pytest.mark.asyncio
    async def test_submit_event_sync_handler(self, manager):
        """测试同步事件处理器"""
        called = []
        
        def sync_handler(event_data):
            called.append("sync")
        
        # 注册同步处理器
        manager.on("sync_event")(sync_handler)
        
        # 执行
        await manager.submit_event("sync_event")
        
        # 验证
        assert len(called) == 1
        assert called[0] == "sync"
    
    # ==================== 事件验证测试 ====================
    
    @pytest.mark.asyncio
    async def test_validate_event_missing_required_field(self, manager):
        """测试验证缺少必填字段的事件"""
        # Mock logger
        with patch('ErisPulse.Core.lifecycle.logger') as mock_logger:
            # 执行（缺少event字段）
            await manager.submit_event(None, data={})
            
            # 验证错误被记录
            assert mock_logger.error.called
    
    @pytest.mark.asyncio
    async def test_submit_event_with_handler_error(self, manager):
        """测试处理器执行错误"""
        error_handler_called = []
        normal_handler_called = []
        
        def error_handler(event_data):
            error_handler_called.append(1)
            raise Exception("Test error")
        
        def normal_handler(event_data):
            normal_handler_called.append(2)
        
        # 注册处理器
        manager.on("test_event")(error_handler)
        manager.on("test_event")(normal_handler)
        
        # Mock logger
        with patch('ErisPulse.Core.lifecycle.logger') as mock_logger:
            # 执行
            await manager.submit_event("test_event")
            
            # 验证
            # 错误被记录
            assert mock_logger.error.called
            # 正常处理器仍然被调用
            assert len(normal_handler_called) == 1


# ==================== 全局生命周期实例测试 ====================

class TestGlobalLifecycle:
    """全局生命周期实例测试"""
    
    @pytest.fixture(autouse=True)
    def reset_global(self):
        """重置全局实例"""
        original_handlers = lifecycle._handlers.copy()
        lifecycle._handlers.clear()
        yield
        lifecycle._handlers.clear()
        lifecycle._handlers.update(original_handlers)
    
    def test_global_instance_exists(self):
        """测试全局实例存在"""
        assert lifecycle is not None
        assert isinstance(lifecycle, LifecycleManager)
    
    def test_standard_events_defined(self):
        """测试标准事件已定义"""
        assert "core" in lifecycle.STANDARD_EVENTS
        assert "module" in lifecycle.STANDARD_EVENTS
        assert "adapter" in lifecycle.STANDARD_EVENTS
        assert "server" in lifecycle.STANDARD_EVENTS


# ==================== 标准事件测试 ====================

class TestStandardEvents:
    """标准事件测试类"""
    
    @pytest.fixture
    def manager(self):
        """创建生命周期管理器实例"""
        manager = LifecycleManager()
        manager._handlers.clear()
        return manager
    
    @pytest.mark.asyncio
    async def test_core_init_events(self, manager):
        """测试核心初始化事件"""
        events = []
        
        @manager.on("core.init.start")
        async def on_start(data):
            events.append(("start", data))
        
        @manager.on("core.init.complete")
        async def on_complete(data):
            events.append(("complete", data))
        
        # 模拟核心初始化
        await manager.submit_event("core.init.start")
        await manager.submit_event("core.init.complete", data={"duration": 1.5, "success": True})
        
        # 验证
        assert len(events) == 2
        assert events[0][0] == "start"
        assert events[1][0] == "complete"
    
    @pytest.mark.asyncio
    async def test_module_events(self, manager):
        """测试模块生命周期事件"""
        events = []
        
        @manager.on("module.load")
        async def on_load(data):
            events.append(("load", data))
        
        @manager.on("module.init")
        async def on_init(data):
            events.append(("init", data))
        
        @manager.on("module.unload")
        async def on_unload(data):
            events.append(("unload", data))
        
        # 模拟模块生命周期
        await manager.submit_event("module.load", data={"module_name": "TestModule", "success": True})
        await manager.submit_event("module.init", data={"module_name": "TestModule", "success": True})
        await manager.submit_event("module.unload", data={"module_name": "TestModule", "success": True})
        
        # 验证
        assert len(events) == 3
        assert all(event[1]["data"]["module_name"] == "TestModule" for event in events)
    
    @pytest.mark.asyncio
    async def test_adapter_events(self, manager):
        """测试适配器生命周期事件"""
        events = []
        
        @manager.on("adapter.load")
        async def on_load(data):
            events.append(("load", data))
        
        @manager.on("adapter.start")
        async def on_start(data):
            events.append(("start", data))
        
        @manager.on("adapter.status.change")
        async def on_status_change(data):
            events.append(("status_change", data))
        
        @manager.on("adapter.stop")
        async def on_stop(data):
            events.append(("stop", data))
        
        @manager.on("adapter.stopped")
        async def on_stopped(data):
            events.append(("stopped", data))
        
        # 模拟适配器生命周期
        await manager.submit_event("adapter.load", data={"platform": "test_platform", "success": True})
        await manager.submit_event("adapter.start", data={"platforms": ["test_platform"]})
        await manager.submit_event("adapter.status.change", 
                              data={"platform": "test_platform", "status": "started"})
        await manager.submit_event("adapter.stop", data={})
        await manager.submit_event("adapter.stopped", data={})
        
        # 验证
        assert len(events) == 5
    
    @pytest.mark.asyncio
    async def test_server_events(self, manager):
        """测试服务器生命周期事件"""
        events = []
        
        @manager.on("server.start")
        async def on_start(data):
            events.append(("start", data))
        
        @manager.on("server.stop")
        async def on_stop(data):
            events.append(("stop", data))
        
        # 模拟服务器生命周期
        await manager.submit_event("server.start", 
                              data={"base_url": "http://localhost:8000", "host": "0.0.0.0", "port": 8000})
        await manager.submit_event("server.stop", data={})
        
        # 验证
        assert len(events) == 2
        assert events[0][1]["data"]["host"] == "0.0.0.0"
        assert events[0][1]["data"]["port"] == 8000
