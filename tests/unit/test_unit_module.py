"""
模块系统单元测试

测试模块管理器和基础模块类的功能
"""

import asyncio
from unittest.mock import AsyncMock, Mock, patch

import pytest

from ErisPulse.Core.Bases import BaseModule
from ErisPulse.Core.config import config
from ErisPulse.Core.module import ModuleManager

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
        result = manager.register(
            "test_module", test_module_class, {"version": "1.0.0"}
        )

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
        assert (
            len([c for c in manager._module_classes.values() if c == test_module_class])
            == 1
        )

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
        with patch("ErisPulse.Core.module.logger") as mock_logger:
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
        with patch("ErisPulse.Core.module.logger") as mock_logger:
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
        with patch("ErisPulse.sdk", mock_sdk):
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

        # 执行 - 不传参数以卸载所有模块
        result = await manager.unload()

        # 验证
        assert result is True
        assert len(manager._loaded_modules) == 0
        assert "module1" not in manager._loaded_modules
        assert "module2" not in manager._loaded_modules

    @pytest.mark.asyncio
    async def test_unload_module_not_loaded(self, manager, test_module_class):
        """测试卸载未加载的模块"""
        # Mock logger
        with patch("ErisPulse.Core.module.logger") as mock_logger:
            # 执行
            result = await manager.unload("test_module")

            # 验证
            assert result is True
            mock_logger.warning.assert_called()

    # ==================== 配置管理测试 ====================

    def test_module_exists(self, manager, test_module_class):
        """测试检查模块是否存在（已注册）"""
        # 未注册的模块
        assert manager.exists("test_module") is False
        assert manager.exists("nonexistent") is False

        # 注册后存在
        manager.register("test_module", test_module_class)
        assert manager.exists("test_module") is True

    def test_module_is_enabled(self, manager):
        """测试检查模块是否启用"""
        with patch.object(config, "getConfig") as mock_get, \
             patch.object(config, "setConfig") as mock_set:
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

            # 未配置状态 - 默认启用并自动写入配置
            mock_get.return_value = None
            assert manager.is_enabled("test_module") is True
            mock_set.assert_called_once()

    def test_module_enable(self, manager, test_module_class):
        """测试启用模块"""
        manager.register("test_module", test_module_class)

        with patch.object(config, "setConfig") as mock_set:
            # Mock logger
            with patch("ErisPulse.Core.module.logger"):
                # 执行
                result = manager.enable("test_module")

                # 验证
                assert result is True
                mock_set.assert_called_once_with(
                    "ErisPulse.modules.status.test_module", True, immediate=True
                )

    def test_module_enable_nonexistent(self, manager):
        """测试启用未注册的模块"""
        with patch("ErisPulse.Core.module.logger"):
            result = manager.enable("nonexistent_module")
            assert result is False

    def test_module_disable(self, manager, test_module_class):
        """测试禁用模块"""
        # 先注册并加载模块
        manager.register("test_module", test_module_class)
        manager._modules["test_module"] = test_module_class()
        manager._loaded_modules.add("test_module")

        with patch.object(config, "setConfig") as mock_set:
            with patch("ErisPulse.Core.module.logger"):
                # 执行
                result = manager.disable("test_module")

                # 验证
                assert result is True
                mock_set.assert_called_once_with(
                    "ErisPulse.modules.status.test_module", False, immediate=True
                )
                assert "test_module" not in manager._loaded_modules
                assert "test_module" not in manager._modules

    def test_unregister_module(self, manager, test_module_class):
        """测试取消注册模块"""
        # 注册模块
        manager.register("test_module", test_module_class, {"version": "1.0"})
        assert "test_module" in manager._module_classes

        # 执行取消注册
        with patch("ErisPulse.Core.module.logger"):
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
        with patch.object(
            config, "getConfig", return_value={"module1": True, "module2": False}
        ):
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
        with patch("ErisPulse.Core.module.logger") as mock_logger:
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

        with patch.object(config, "getConfig") as mock_get:
            with patch.object(config, "setConfig"):
                # 启用的模块
                manager.register("enabled", EnabledModule)

                # 设置正确的 mock 返回值
                # exists("enabled") 调用 getConfig("ErisPulse.modules.status", {}) -> {"enabled": True}
                # is_enabled("enabled") 调用 getConfig("ErisPulse.modules.status.enabled") -> True
                def mock_get_enabled(key, default=None):
                    if key == "ErisPulse.modules.status":
                        return {"enabled": True}
                    if key == "ErisPulse.modules.status.enabled":
                        return True
                    return default

                mock_get.side_effect = mock_get_enabled
                assert "enabled" in manager

                # 禁用的模块
                manager.register("disabled", DisabledModule)

                def mock_get_disabled(key, default=None):
                    if key == "ErisPulse.modules.status":
                        return {"disabled": False}
                    if key == "ErisPulse.modules.status.disabled":
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
                return ModuleLoadStrategy(lazy_load=False, priority=100)

        strategy = EagerModule.get_load_strategy()
        assert strategy.lazy_load is False
        assert strategy.priority == 100

    @pytest.mark.asyncio
    async def test_on_load_abstractmethod(self):
        """测试on_load抽象方法"""

        class IncompleteModule(BaseModule):
            pass

        # 使用 ABC，无法实例化未实现抽象方法的类
        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            IncompleteModule()

    @pytest.mark.asyncio
    async def test_on_unload_abstractmethod(self):
        """测试on_unload抽象方法"""

        class IncompleteModule(BaseModule):
            async def on_load(self, event):
                return True

        # 使用 ABC，无法实例化未实现所有抽象方法的类
        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            IncompleteModule()


# ==================== 模块与生命周期集成测试 ====================


class TestModuleLifecycleIntegration:
    """模块与生命周期集成测试"""

    @pytest.mark.asyncio
    async def test_module_load_submits_lifecycle_event(self):
        """测试模块加载提交生命周期事件"""
        # Mock lifecycle
        with patch("ErisPulse.Core.module.lifecycle") as mock_lifecycle:
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
            # load() 成功路径依次提交 "module.load" 与 "module.init"，
            # 断言其中确实包含 "module.load" 事件
            event_names = [c.args[0] for c in mock_lifecycle.submit_event.call_args_list]
            assert "module.load" in event_names

    @pytest.mark.asyncio
    async def test_module_unload_submits_lifecycle_event(self):
        """测试模块卸载提交生命周期事件"""
        # Mock lifecycle
        with patch("ErisPulse.Core.module.lifecycle") as mock_lifecycle:
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


# ==================== 模块依赖管理测试 ====================

class TestModuleDependencies:
    """模块依赖管理测试"""

    @pytest.fixture
    def loader(self):
        """创建模块加载器实例"""
        from ErisPulse.loaders.module import ModuleLoader
        return ModuleLoader()

    def _make_mock_module(self, name, depends=None, priority=0):
        """创建模拟模块对象"""
        mock_mod = Mock()
        mock_mod.moduleInfo = {
            "meta": {
                "name": name,
                "priority": priority,
                **({"depends": depends} if depends else {}),
            }
        }
        return mock_mod

    def test_validate_dependencies_all_satisfied(self, loader):
        """测试依赖全部满足"""
        modules = ["A", "B", "C"]
        module_objs = {
            "A": self._make_mock_module("A", depends=["B"]),
            "B": self._make_mock_module("B"),
            "C": self._make_mock_module("C"),
        }
        missing = loader._validate_dependencies(modules, module_objs)
        assert missing == {}

    def test_validate_dependencies_missing(self, loader):
        """测试存在缺失依赖"""
        modules = ["A", "B"]
        module_objs = {
            "A": self._make_mock_module("A", depends=["C"]),
            "B": self._make_mock_module("B"),
        }
        missing = loader._validate_dependencies(modules, module_objs)
        assert "A" in missing
        assert "C" in missing["A"]

    def test_validate_dependencies_no_depends(self, loader):
        """测试无依赖模块"""
        modules = ["A"]
        module_objs = {
            "A": self._make_mock_module("A"),
        }
        missing = loader._validate_dependencies(modules, module_objs)
        assert missing == {}

    def test_validate_dependencies_multiple_missing(self, loader):
        """测试多个缺失依赖"""
        modules = ["A"]
        module_objs = {
            "A": self._make_mock_module("A", depends=["B", "C"]),
        }
        missing = loader._validate_dependencies(modules, module_objs)
        assert len(missing["A"]) == 2

    def test_topological_sort_simple(self, loader):
        """测试简单拓扑排序"""
        modules = ["A", "B"]
        module_objs = {
            "A": self._make_mock_module("A", depends=["B"]),
            "B": self._make_mock_module("B"),
        }
        result = loader._topological_sort(modules, module_objs)
        assert result.index("B") < result.index("A")

    def test_topological_sort_chain(self, loader):
        """测试链式依赖排序"""
        modules = ["A", "B", "C"]
        module_objs = {
            "A": self._make_mock_module("A", depends=["B"]),
            "B": self._make_mock_module("B", depends=["C"]),
            "C": self._make_mock_module("C"),
        }
        result = loader._topological_sort(modules, module_objs)
        assert result.index("C") < result.index("B")
        assert result.index("B") < result.index("A")

    def test_topological_sort_no_deps(self, loader):
        """测试无依赖排序（按优先级）"""
        modules = ["A", "B", "C"]
        module_objs = {
            "A": self._make_mock_module("A", priority=1),
            "B": self._make_mock_module("B", priority=10),
            "C": self._make_mock_module("C", priority=5),
        }
        result = loader._topological_sort(modules, module_objs)
        assert result[0] == "B"  # priority=10 最高
        assert result[1] == "C"  # priority=5
        assert result[2] == "A"  # priority=1

    def test_topological_sort_priority_with_deps(self, loader):
        """测试带依赖的优先级排序"""
        modules = ["A", "B", "C", "D"]
        module_objs = {
            "A": self._make_mock_module("A", depends=["D"], priority=100),
            "B": self._make_mock_module("B", depends=["D"], priority=1),
            "C": self._make_mock_module("C", depends=["D"], priority=50),
            "D": self._make_mock_module("D"),
        }
        result = loader._topological_sort(modules, module_objs)
        assert result[0] == "D"
        assert result.index("A") < result.index("B")
        assert result.index("C") < result.index("B")

    def test_topological_sort_cycle_raises(self, loader):
        """测试循环依赖抛出异常"""
        modules = ["A", "B"]
        module_objs = {
            "A": self._make_mock_module("A", depends=["B"]),
            "B": self._make_mock_module("B", depends=["A"]),
        }
        with pytest.raises(RuntimeError, match="循环依赖"):
            loader._topological_sort(modules, module_objs)

    def test_topological_sort_diamond(self, loader):
        """测试菱形依赖"""
        #   D (top)
        #  / \
        # B   C
        #  \ /
        #   A (bottom)
        modules = ["A", "B", "C", "D"]
        module_objs = {
            "D": self._make_mock_module("D", depends=["B", "C"]),
            "B": self._make_mock_module("B", depends=["A"]),
            "C": self._make_mock_module("C", depends=["A"]),
            "A": self._make_mock_module("A"),
        }
        result = loader._topological_sort(modules, module_objs)
        assert result.index("A") < result.index("B")
        assert result.index("A") < result.index("C")
        assert result.index("B") < result.index("D")
        assert result.index("C") < result.index("D")


# ==================== 模块启停热更新（设置关闭 = 卸载） ====================


class TestModuleStatusHotReload:
    """配置启停状态变更时应自动加载/卸载模块"""

    @pytest.fixture
    def manager(self):
        """创建模块管理器实例"""
        manager = ModuleManager()
        manager._modules.clear()
        manager._module_classes.clear()
        manager._loaded_modules.clear()
        manager._module_info.clear()
        manager._lazy_modules.clear()
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

    def test_disable_cleans_lazy_proxy(self, manager, test_module_class):
        """禁用未实例化的懒加载模块，应清理其代理而非早退"""
        manager.register("lazy_mod", test_module_class)
        manager.register_lazy("lazy_mod", Mock())
        with patch.object(config, "setConfig"):
            with patch("ErisPulse.Core.module.logger"):
                result = manager.disable("lazy_mod")
        assert result is True
        assert "lazy_mod" not in manager._lazy_modules

    def test_unload_cleans_lazy_proxy(self, manager, test_module_class):
        """卸载未实例化的懒加载模块，应清理其代理而非早退"""
        manager.register("lazy_mod", test_module_class)
        manager.register_lazy("lazy_mod", Mock())
        with patch("ErisPulse.Core.module.logger"):
            asyncio.run(manager.unload("lazy_mod"))
        assert "lazy_mod" not in manager._lazy_modules

    def test_unload_all_cleans_lazy_proxies(self, manager, test_module_class):
        """卸载全部模块应一并清理未初始化的懒加载代理"""
        manager.register("lazy_mod", test_module_class)
        manager.register_lazy("lazy_mod", Mock())
        with patch("ErisPulse.Core.module.logger"):
            asyncio.run(manager.unload())
        assert "lazy_mod" not in manager._lazy_modules


class TestModuleMeta:
    """模块介绍 meta 与命令总览（按模块组织的命令数据）"""

    @pytest.fixture(autouse=True)
    def clean(self):
        from ErisPulse.Core.adapter import adapter
        from ErisPulse.Core.Event import _clear_all_handlers

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

    @staticmethod
    def _make_mgr():
        return ModuleManager()

    def _register_with_commands(self, mgr):
        from ErisPulse.Core.Event import command
        from ErisPulse.runtime.context import owner_scope

        class Weather(BaseModule):
            async def on_load(self, event): return True
            async def on_unload(self, event): return True

            @staticmethod
            def get_meta():
                return {"name": "天气", "description": "查询城市天气", "group": "工具"}

        mgr.register("Weather", Weather)
        with owner_scope("Weather"):
            @command("weather", help="查询天气", group="工具")
            async def weather_cmd(event): pass
            @command("forecast", aliases=["fc"], help="天气预报")
            async def fc_cmd(event): pass

    def test_get_meta_from_class(self):
        """get_meta() 从类声明 + 自动补全命令"""
        mgr = self._make_mgr()
        self._register_with_commands(mgr)
        meta = mgr.get_meta("Weather")
        assert meta["description"] == "查询城市天气"
        assert meta["group"] == "工具"
        assert set(meta["commands"]) == {"weather", "forecast"}

    def test_get_meta_none_for_unregistered(self):
        """未注册模块返回 None"""
        mgr = self._make_mgr()
        assert mgr.get_meta("Nope") is None

    def test_get_meta_merges_register_info(self):
        """注册 info 与类 get_meta 合并（类优先）"""
        mgr = self._make_mgr()

        class M(BaseModule):
            async def on_load(self, event): return True
            async def on_unload(self, event): return True

            @staticmethod
            def get_meta():
                return {"description": "类描述"}

        mgr.register("M", M, {"author": "alice", "description": "info描述"})
        meta = mgr.get_meta("M")
        assert meta["author"] == "alice"
        assert meta["description"] == "类描述"  # 类声明优先

    def test_get_commands_overview(self):
        """命令总览：模块 meta + 命令（别名/分组/帮助）"""
        mgr = self._make_mgr()
        self._register_with_commands(mgr)
        overview = mgr.get_commands_overview()
        entry = overview["Weather"]
        assert entry["meta"]["description"] == "查询城市天气"
        by_name = {c["name"]: c for c in entry["commands"]}
        assert by_name["weather"]["group"] == "工具"
        assert by_name["forecast"]["aliases"] == ["fc"]
        assert by_name["weather"]["hidden"] is False

    def test_get_meta_i18n_resolved(self):
        """i18n 字典字段解析为当前语言文本（键经 I18nClass 注册）"""
        from ErisPulse.Core.Bases import BaseI18n, I18nKey

        mgr = self._make_mgr()

        class WeatherI18n(BaseI18n):
            meta_description: I18nKey = I18nKey(
                default="Weather lookup", zh_CN="查询城市天气", en="Weather lookup"
            )
            meta_group: I18nKey = I18nKey(default="Tools", zh_CN="工具", en="Tools")

        class Weather(BaseModule):
            async def on_load(self, event): return True
            async def on_unload(self, event): return True

            @staticmethod
            def get_meta():
                return {
                    "name": "天气",
                    "description": {"i18n": "Weather.meta_description", "default": "Weather lookup"},
                    "group": {"i18n": "Weather.meta_group", "default": "Tools"},
                }

        mgr.register("Weather", Weather)
        WeatherI18n.register(prefix="Weather.", domain="Weather")

        meta = mgr.get_meta("Weather")
        assert meta["description"] == "查询城市天气"
        assert meta["group"] == "工具"

    def test_get_meta_i18n_raw(self):
        """resolve_i18n=False 透传原始 i18n 字典"""
        mgr = self._make_mgr()

        class M(BaseModule):
            async def on_load(self, event): return True
            async def on_unload(self, event): return True

            @staticmethod
            def get_meta():
                return {"description": {"i18n": "M.desc", "default": "Fallback"}}

        mgr.register("M", M)
        meta = mgr.get_meta("M", resolve_i18n=False)
        assert meta["description"] == {"i18n": "M.desc", "default": "Fallback"}

    def test_module_meta_class(self):
        """get_meta() 返回 ModuleMeta 声明类（属性键入）"""
        from ErisPulse.Core.Bases import ModuleMeta

        meta = ModuleMeta(name="天气", description="查询城市天气", group="工具", tags=["天气"])
        d = meta.to_dict()
        assert d == {"name": "天气", "description": "查询城市天气", "group": "工具", "tags": ["天气"]}
        # None 字段被过滤
        assert "version" not in d and "author" not in d

    def test_get_meta_with_module_meta(self):
        """ModuleManager.get_meta() 解析 ModuleMeta 实例（to_dict 链路）"""
        from ErisPulse.Core.Bases import ModuleMeta

        mgr = self._make_mgr()

        class Weather(BaseModule):
            async def on_load(self, event): return True
            async def on_unload(self, event): return True

            @staticmethod
            def get_meta():
                return ModuleMeta(name="天气", description="查询城市天气", group="工具")

        mgr.register("Weather", Weather)
        meta = mgr.get_meta("Weather")
        assert meta["description"] == "查询城市天气"
        assert meta["group"] == "工具"
        assert meta["name"] == "天气"

    def test_get_meta_meta_class_with_register_info(self):
        """ModuleMeta 声明 > 注册 info（与 dict 语义一致）"""
        from ErisPulse.Core.Bases import ModuleMeta

        mgr = self._make_mgr()

        class M(BaseModule):
            async def on_load(self, event): return True
            async def on_unload(self, event): return True

            @staticmethod
            def get_meta():
                return ModuleMeta(description="类声明")

        mgr.register("M", M, {"author": "alice", "description": "info描述"})
        meta = mgr.get_meta("M")
        assert meta["author"] == "alice"
        assert meta["description"] == "类声明"
