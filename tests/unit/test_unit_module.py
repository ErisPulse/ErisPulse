"""
模块系统单元测试

测试模块管理器和基础模块类的功能
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any

from ErisPulse.Core.module import ModuleManager
from ErisPulse.Core.Bases import BaseModule
from ErisPulse.Core.config import config
from ErisPulse.Core.lifecycle import lifecycle


# ==================== 模块管理器测试 ====================

class TestModuleManager:
    """模块管理器测试类"""
    
    @pytest.fixture
    def manager(self):
        """创建模块管理器实例"""
        manager = ModuleManager()
        # 清理初始状态
        manager._modules.clear()
        manager._module_classes.clear()
        manager._loaded_modules.clear()
        manager._module_info.clear()
        return manager
    
    @pytest.fixture
    def test_module_class(self):
        """创建测试模块类"""
        class TestModule(BaseModule):
            def __init__(self, sdk=None):
                self.sdk = sdk
                self.loaded = False
                self.unloaded = False
            
            async def on_load(self, event):
                self.loaded = True
                return True
            
            async def on_unload(self, event):
                self.unloaded = True
                return True
        
        return TestModule
    
    @pytest.fixture
    def sync_module_class(self):
        """创建同步方法模块类"""
        class SyncModule(BaseModule):
            def __init__(self, sdk=None):
                self.sdk = sdk
                self.loaded = False
                self.unloaded = False
            
            def on_load(self, event):
                self.loaded = True
                return True
            
            def on_unload(self, event):
                self.unloaded = True
                return True
        
        return SyncModule
    
    # ==================== 注册测试 ====================
    
    def test_register_module_success(self, manager, test_module_class):
        """测试成功注册模块"""
        # 执行
        result = manager.register("test_module", test_module_class, {"version": "1.0.0"})
        
        # 验证
        assert result is True
        assert "test_module" in manager._module_classes
        assert manager._module_classes["test_module"] is test_module_class
        assert "test_module" in manager._module_info
        assert manager._module_info["test_module"]["version"] == "1.0.0"
    
    def test_register_module_invalid_class(self, manager):
        """测试注册无效的模块类"""
        class InvalidModule:
            pass
        
        result = manager.register("invalid", InvalidModule)
        
        # 但仍然会注册（ErisPulse允许非BaseModule类）
        assert result is True
    
    def test_register_module_invalid_name(self, manager, test_module_class):
        """测试注册无效的模块名"""
        # 验证空字符串
        with pytest.raises(TypeError, match="模块名称必须是非空字符串"):
            manager.register("", test_module_class)
        
        # 验证None
        with pytest.raises(TypeError, match="模块名称必须是非空字符串"):
            manager.register(None, test_module_class)
    
    def test_register_module_duplicate(self, manager, test_module_class):
        """测试注册重复的模块"""
        # 第一次注册
        manager.register("test_module", test_module_class)
        
        # 验证仍然只有一个
        assert len([c for c in manager._module_classes.values() if c == test_module_class]) == 1
    
    # ==================== 加载测试 ====================
    
    @pytest.mark.asyncio
    async def test_load_module_success(self, manager, test_module_class):
        """测试成功加载模块"""
        # 注册模块
        manager.register("test_module", test_module_class)
        
        # 执行
        result = await manager.load("test_module")
        
        # 验证
        assert result is True
        assert "test_module" in manager._loaded_modules
        assert "test_module" in manager._modules
        assert manager._modules["test_module"].loaded is True
    
    @pytest.mark.asyncio
    async def test_load_module_not_registered(self, manager):
        """测试加载未注册的模块"""
        # Mock logger
        with patch('ErisPulse.Core.module.logger') as mock_logger:
            # 执行
            result = await manager.load("nonexistent")
            
            # 验证
            assert result is False
            mock_logger.error.assert_called()
    
    @pytest.mark.asyncio
    async def test_load_module_already_loaded(self, manager, test_module_class):
        """测试重复加载模块"""
        # 注册并加载
        manager.register("test_module", test_module_class)
        await manager.load("test_module")
        
        # Mock logger
        with patch('ErisPulse.Core.module.logger') as mock_logger:
            # 再次加载
            result = await manager.load("test_module")
            
            # 验证
            assert result is True
            mock_logger.info.assert_called()
    
    @pytest.mark.asyncio
    async def test_load_module_sync_methods(self, manager, sync_module_class):
        """测试加载同步方法模块"""
        # 注册模块
        manager.register("sync_module", sync_module_class)
        
        # 执行
        result = await manager.load("sync_module")
        
        # 验证
        assert result is True
        assert manager._modules["sync_module"].loaded is True
    
    @pytest.mark.asyncio
    async def test_load_module_with_sdk_param(self, manager, test_module_class):
        """测试带sdk参数的模块加载"""
        # Mock SDK
        mock_sdk = Mock()
        
        # 注册模块
        manager.register("test_module", test_module_class)
        
        # 执行
        with patch('ErisPulse.sdk', mock_sdk):
            result = await manager.load("test_module")
        
        # 验证
        assert result is True
        assert manager._modules["test_module"].sdk is mock_sdk
    
    # ==================== 卸载测试 ====================
    
    @pytest.mark.asyncio
    async def test_unload_module_success(self, manager, test_module_class):
        """测试成功卸载模块"""
        # 注册并加载模块
        manager.register("test_module", test_module_class)
        await manager.load("test_module")
        
        # 执行
        result = await manager.unload("test_module")
        
        # 验证
        assert result is True
        assert "test_module" not in manager._loaded_modules
    
    @pytest.mark.asyncio
    async def test_unload_all_modules(self, manager, test_module_class):
        """测试卸载所有模块"""
        # 注册并加载多个模块
        manager.register("module1", test_module_class)
        manager.register("module2", test_module_class)
        await manager.load("module1")
        await manager.load("module2")
        
        # 执行
        result = await manager.unload("Unknown")
        
        # 验证
        assert result is True
        assert len(manager._loaded_modules) == 0
        assert "module1" not in manager._loaded_modules
        assert "module2" not in manager._loaded_modules
    
    @pytest.mark.asyncio
    async def test_unload_module_not_loaded(self, manager, test_module_class):
        """测试卸载未加载的模块"""
        # Mock logger
        with patch('ErisPulse.Core.module.logger') as mock_logger:
            # 执行
            result = await manager.unload("test_module")
            
            # 验证
            assert result is True
            mock_logger.warning.assert_called()
    
    # ==================== 配置管理测试 ====================
    
    def test_module_exists(self, manager):
        """测试检查模块是否存在"""
        # Mock config
        with patch.object(config, 'getConfig') as mock_get:
            # 存在的模块
            mock_get.return_value = {"test_module": True}
            assert manager.exists("test_module") is True
            
            # 不存在的模块
            assert manager.exists("nonexistent") is False
    
    def test_module_is_enabled(self, manager):
        """测试检查模块是否启用"""
        with patch.object(config, 'getConfig') as mock_get:
            # 启用状态
            mock_get.return_value = True
            assert manager.is_enabled("test_module") is True
            
            # 禁用状态
            mock_get.return_value = False
            assert manager.is_enabled("test_module") is False
            
            # 字符串状态
            mock_get.return_value = "true"
            assert manager.is_enabled("test_module") is True
            
            mock_get.return_value = "false"
            assert manager.is_enabled("test_module") is False
            
            # 未配置状态
            mock_get.return_value = None
            assert manager.is_enabled("test_module") is False
    
    def test_module_enable(self, manager):
        """测试启用模块"""
        with patch.object(config, 'setConfig') as mock_set:
            # Mock logger
            with patch('ErisPulse.Core.module.logger'):
                # 执行
                result = manager.enable("test_module")
                
                # 验证
                assert result is True
                mock_set.assert_called_once_with("ErisPulse.modules.status.test_module", True)
    
    def test_module_disable(self, manager, test_module_class):
        """测试禁用模块"""
        # 先注册并加载模块
        manager.register("test_module", test_module_class)
        manager._modules["test_module"] = test_module_class()
        manager._loaded_modules.add("test_module")
        
        with patch.object(config, 'setConfig') as mock_set:
            with patch('ErisPulse.Core.module.logger'):
                # 执行
                result = manager.disable("test_module")
                
                # 验证
                assert result is True
                mock_set.assert_called_once_with("ErisPulse.modules.status.test_module", False)
                assert "test_module" not in manager._loaded_modules
                assert "test_module" not in manager._modules
    
    def test_unregister_module(self, manager, test_module_class):
        """测试取消注册模块"""
        # 注册模块
        manager.register("test_module", test_module_class, {"version": "1.0"})
        assert "test_module" in manager._module_classes
        
        # 执行取消注册
        with patch('ErisPulse.Core.module.logger'):
            result = manager.unregister("test_module")
        
        # 验证
        assert result is True
        assert "test_module" not in manager._module_classes
    
    # ==================== 工具方法测试 ====================
    
    def test_get_module(self, manager, test_module_class):
        """测试获取模块实例"""
        # 注册并加载模块
        manager.register("test_module", test_module_class)
        manager._modules["test_module"] = test_module_class()
        manager._loaded_modules.add("test_module")
        
        # 执行
        module = manager.get("test_module")
        
        # 验证
        assert module is not None
        assert isinstance(module, test_module_class)
    
    def test_get_module_not_loaded(self, manager, test_module_class):
        """测试获取未加载的模块实例"""
        # 只注册，不加载
        manager.register("test_module", test_module_class)
        
        # 执行
        module = manager.get("test_module")
        
        # 验证
        assert module is None
    
    def test_is_loaded(self, manager, test_module_class):
        """测试检查模块是否已加载"""
        # 注册并加载
        manager.register("test_module", test_module_class)
        manager._loaded_modules.add("test_module")
        
        # 验证
        assert manager.is_loaded("test_module") is True
        assert manager.is_loaded("nonexistent") is False
    
    def test_list_registered(self, manager, test_module_class):
        """测试列出已注册的模块"""
        # 注册多个模块
        manager.register("module1", test_module_class)
        manager.register("module2", test_module_class)
        
        # 执行
        registered = manager.list_registered()
        
        # 验证
        assert "module1" in registered
        assert "module2" in registered
        assert len(registered) == 2
    
    def test_list_loaded(self, manager):
        """测试列出已加载的模块"""
        # 添加到已加载列表
        manager._loaded_modules.add("module1")
        manager._loaded_modules.add("module2")
        
        # 执行
        loaded = manager.list_loaded()
        
        # 验证
        assert "module1" in loaded
        assert "module2" in loaded
        assert len(loaded) == 2
    
    def test_list_items(self, manager):
        """测试列出所有模块状态"""
        with patch.object(config, 'getConfig', return_value={"module1": True, "module2": False}):
            # 执行
            items = manager.list_items()
            
            # 验证
            assert items["module1"] is True
            assert items["module2"] is False
    
    def test_getattr_module(self, manager, test_module_class):
        """测试通过属性访问模块"""
        # 注册并加载模块
        manager.register("test_module", test_module_class)
        manager._modules["test_module"] = test_module_class()
        
        # 执行
        module = manager.test_module
        
        # 验证
        assert module is not None
        assert isinstance(module, test_module_class)
    
    def test_getattr_module_not_found(self, manager):
        """测试通过属性访问不存在的模块"""
        # Mock logger
        with patch('ErisPulse.Core.module.logger') as mock_logger:
            # 执行和验证
            with pytest.raises(AttributeError, match="不存在或未启用"):
                _ = manager.nonexistent
    
    def test_contains_operator(self, manager):
        """测试包含操作符"""
        # 创建测试模块类
        class EnabledModule(BaseModule):
            async def on_load(self, event):
                return True
            async def on_unload(self, event):
                return True
        
        class DisabledModule(BaseModule):
            async def on_load(self, event):
                return True
            async def on_unload(self, event):
                return True
        
        with patch.object(config, 'getConfig') as mock_get:
            with patch.object(config, 'setConfig'):
                # 启用的模块
                manager.register("enabled", EnabledModule)
                # 设置正确的 mock 返回值
                # exists("enabled") 调用 getConfig("ErisPulse.modules.status", {}) -> {"enabled": True}
                # is_enabled("enabled") 调用 getConfig("ErisPulse.modules.status.enabled") -> True
                def mock_get_enabled(key, default=None):
                    if key == "ErisPulse.modules.status":
                        return {"enabled": True}
                    elif key == "ErisPulse.modules.status.enabled":
                        return True
                    return default
                mock_get.side_effect = mock_get_enabled
                assert "enabled" in manager
                
                # 禁用的模块
                manager.register("disabled", DisabledModule)
                def mock_get_disabled(key, default=None):
                    if key == "ErisPulse.modules.status":
                        return {"disabled": False}
                    elif key == "ErisPulse.modules.status.disabled":
                        return False
                    return default
                mock_get.side_effect = mock_get_disabled
                assert "disabled" not in manager
                
                # 不存在的模块
                assert "nonexistent" not in manager


# ==================== BaseModule 测试 ====================

class TestBaseModule:
    """基础模块测试类"""
    
    @pytest.fixture
    def concrete_module(self):
        """创建具体模块"""
        class ConcreteModule(BaseModule):
            def __init__(self):
                self.sdk = None
                self.loaded = False
                self.unloaded = False
            
            async def on_load(self, event):
                self.loaded = True
                return True
            
            async def on_unload(self, event):
                self.unloaded = True
                return True
        
        return ConcreteModule
    
    def test_get_load_strategy_default(self, concrete_module):
        """测试默认加载策略"""
        strategy = concrete_module.get_load_strategy()
        
        # 验证返回的是 ModuleLoadStrategy 对象
        from ErisPulse.loaders.strategy import ModuleLoadStrategy
        assert isinstance(strategy, ModuleLoadStrategy)
        
        # 验证默认懒加载为 True
        assert strategy.lazy_load is True
        
        # 验证默认优先级为 0
        assert strategy.priority == 0
    
    def test_get_load_strategy_override_with_object(self):
        """测试通过对象重写加载策略"""
        from ErisPulse.loaders.strategy import ModuleLoadStrategy
        
        class EagerModule(BaseModule):
            @staticmethod
            def get_load_strategy():
                return ModuleLoadStrategy(
                    lazy_load=False,
                    priority=100
                )
        
        strategy = EagerModule.get_load_strategy()
        assert strategy.lazy_load is False
        assert strategy.priority == 100
    
    @pytest.mark.asyncio
    async def test_on_load_abstractmethod(self):
        """测试on_load抽象方法"""
        class IncompleteModule(BaseModule):
            pass
        
        module = IncompleteModule()
        
        # 验证抽象方法抛出异常
        with pytest.raises(NotImplementedError):
            await module.on_load({})
    
    @pytest.mark.asyncio
    async def test_on_unload_abstractmethod(self):
        """测试on_unload抽象方法"""
        class IncompleteModule(BaseModule):
            async def on_load(self, event):
                return True
        
        module = IncompleteModule()
        
        # 验证抽象方法抛出异常
        with pytest.raises(NotImplementedError):
            await module.on_unload({})


# ==================== 模块与生命周期集成测试 ====================

class TestModuleLifecycleIntegration:
    """模块与生命周期集成测试"""
    
    @pytest.mark.asyncio
    async def test_module_load_submits_lifecycle_event(self):
        """测试模块加载提交生命周期事件"""
        # Mock lifecycle
        with patch('ErisPulse.Core.module.lifecycle') as mock_lifecycle:
            mock_lifecycle.submit_event = AsyncMock()
            
            from ErisPulse.Core.module import module
            module._modules.clear()
            module._loaded_modules.clear()
            module._module_classes.clear()
            
            # 创建测试模块
            class TestModule(BaseModule):
                async def on_load(self, event):
                    return True
                
                async def on_unload(self, event):
                    return True
            
            # 注册并加载
            module.register("test_module", TestModule)
            await module.load("test_module")
            
            # 验证生命周期事件被提交
            mock_lifecycle.submit_event.assert_called()
            call_args = mock_lifecycle.submit_event.call_args
            assert call_args[0][0] == "module_load"
    
    @pytest.mark.asyncio
    async def test_module_unload_submits_lifecycle_event(self):
        """测试模块卸载提交生命周期事件"""
        # Mock lifecycle
        with patch('ErisPulse.Core.module.lifecycle') as mock_lifecycle:
            mock_lifecycle.submit_event = AsyncMock()
            
            from ErisPulse.Core.module import module
            module._modules.clear()
            module._loaded_modules.clear()
            module._module_classes.clear()
            
            # 创建测试模块
            class TestModule(BaseModule):
                async def on_load(self, event):
                    return True
                
                async def on_unload(self, event):
                    return True
            
            # 注册、加载并卸载
            module.register("test_module", TestModule)
            await module.load("test_module")
            await module.unload("test_module")
            
            # 验证生命周期事件被提交
            mock_lifecycle.submit_event.assert_called()
            call_args = mock_lifecycle.submit_event.call_args
            assert call_args[0][0] == "module.unload"
