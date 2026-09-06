"""
模块热重载（ModuleLoader.reload_module）单元测试

覆盖 PyPI 安装包来源与本地插件来源的统一重载流程：
卸载 → 清理注册与 sys.modules → 重新发现/导入 → 注册加载。
"""

import asyncio
import sys
import types

import pytest

from ErisPulse.Core.Bases.module import BaseModule
from ErisPulse.loaders import ModuleLoader


class FakeManager:
    """ModuleManager 测试桩：记录调用序列"""

    def __init__(self):
        self.calls: list[tuple] = []
        self._module_info: dict = {}
        self._module_classes: dict = {}

    def _collect_dependents(self, name):
        return []

    async def unload(self, name):
        self.calls.append(("unload", name))
        return True

    def unregister(self, name):
        self.calls.append(("unregister", name))
        return True

    def register(self, name, cls, info):
        self.calls.append(("register", name))
        return True

    async def load(self, name):
        self.calls.append(("load", name))
        return True

    def get(self, name):
        return "instance"


class FakeFinder:
    """ModuleFinder 测试桩：可控 entry-point 查询与缓存标记"""

    def __init__(self, entry_point=None):
        self._entry_point = entry_point
        self.cache_cleared = False

    def clear_cache(self):
        self.cache_cleared = True

    def find_by_name(self, name):
        return self._entry_point

    def get_top_level_modules(self, package):
        return []


def _make_module_in_sys(name: str, version: str = "1.0.0"):
    """向 sys.modules 注册一个携带 BaseModule 子类的真实模块对象"""
    mod = types.ModuleType(name)
    mod.__version__ = version

    class WeatherModule(BaseModule):
        pass

    # 类的 __module__ 必须指向合成模块名，否则 sys.modules[cls.__module__] 会命中测试模块
    WeatherModule.__module__ = name
    mod.WeatherModule = WeatherModule
    sys.modules[name] = mod
    return mod, WeatherModule


class FakeEntryPoint:
    name = "Weather"
    dist = None

    def __init__(self, module, attr="WeatherModule"):
        self._module = module
        self._attr = attr
        self.load_count = 0

    def load(self):
        # 模拟真实 import：重新导入会把模块对象重新挂回 sys.modules
        sys.modules[self._module.__name__] = self._module
        self.load_count += 1
        return getattr(self._module, self._attr)


def _make_loader(entry_point=None, finder=None):
    loader = ModuleLoader()
    loader._finder = finder or FakeFinder(entry_point)
    return loader


@pytest.mark.unit
class TestReloadPypiModule:
    """PyPI 安装包来源模块的热重载"""

    def test_full_flow(self, monkeypatch):
        """卸载 → 清 sys.modules → 重导入 → 注册 → 加载 → 挂载 sdk 属性"""
        old_mod, _ = _make_module_in_sys("fake_weather_pkg")
        new_mod, new_cls = _make_module_in_sys("fake_weather_pkg")

        # 旧快照：PyPI 来源（无 source 键），带 top_level 供 sys.modules 清理
        old_mod.moduleInfo = {
            "meta": {
                "name": "Weather",
                "package": "erispulse-weather",
                "top_level": ["fake_weather_pkg"],
            }
        }

        # 额外子模块：应随顶层包一并被清理
        sub = types.ModuleType("fake_weather_pkg.core")
        sys.modules["fake_weather_pkg.core"] = sub

        entry_point = FakeEntryPoint(new_mod)
        loader = _make_loader(entry_point)
        loader._last_module_objs = {"Weather": old_mod}

        manager = FakeManager()
        sdk = types.SimpleNamespace()
        sdk.Weather = "old-instance"

        try:
            ok = asyncio.run(loader.reload_module("Weather", manager, sdk))
        finally:
            sys.modules.pop("fake_weather_pkg", None)
            sys.modules.pop("fake_weather_pkg.core", None)

        assert ok is True
        # 完整调用链：unregister → register → load
        assert ("unregister", "Weather") in manager.calls
        assert ("register", "Weather") in manager.calls
        assert ("load", "Weather") in manager.calls
        # entry-point 重新导入
        assert entry_point.load_count == 1
        # 旧 sys.modules 条目被清理（purge 发生在重新导入前）
        assert "fake_weather_pkg.core" not in sys.modules
        # finder 缓存被清（突破 60 秒 entry-point 缓存）
        assert loader._finder.cache_cleared is True
        # 新实例挂载 sdk 属性，快照更新
        assert sdk.Weather == "instance"
        assert loader._last_module_objs["Weather"] is new_mod

    def test_uninstalled_module_returns_true(self):
        """entry-point 已消失（pip 卸载）：从快照移除并视为成功"""
        old_mod = types.ModuleType("fake_gone_pkg")

        class GoneModule(BaseModule):
            pass

        old_mod.GoneModule = GoneModule
        old_mod.moduleInfo = {
            "meta": {"name": "Gone", "package": "erispulse-gone", "top_level": ["fake_gone_pkg"]}
        }

        loader = _make_loader(finder=FakeFinder(None))  # 查不到 entry-point
        loader._last_module_objs = {"Gone": old_mod}

        manager = FakeManager()
        ok = asyncio.run(loader.reload_module("Gone", manager, types.SimpleNamespace()))

        assert ok is True
        assert ("unload", "Gone") in manager.calls
        assert "Gone" not in loader._last_module_objs

    def test_load_failure_returns_false(self):
        """重新导入成功但 manager.load 失败：返回 False"""
        mod, _ = _make_module_in_sys("fake_fail_pkg")
        mod.moduleInfo = {"meta": {"name": "Bad", "top_level": ["fake_fail_pkg"]}}

        loader = _make_loader(FakeEntryPoint(mod))
        loader._last_module_objs = {"Bad": mod}

        manager = FakeManager()

        async def fail_load(name):
            return False

        manager.load = fail_load

        try:
            ok = asyncio.run(loader.reload_module("Bad", manager, types.SimpleNamespace()))
        finally:
            sys.modules.pop("fake_fail_pkg", None)

        assert ok is False

    def test_unknown_module_returns_false(self):
        """模块不在加载快照中：直接返回 False，不触发卸载"""
        loader = ModuleLoader()
        manager = FakeManager()
        ok = asyncio.run(loader.reload_module("Ghost", manager, types.SimpleNamespace()))

        assert ok is False
        assert manager.calls == []


@pytest.mark.unit
class TestReloadPluginSource:
    """本地插件来源重载保持原有路径（重扫描插件目录）"""

    def test_plugin_source_uses_plugin_discovery(self, monkeypatch):
        """plugin_folder 来源走 _plugin_loader.discover，不走 entry-point"""
        old_mod = types.ModuleType("dice_plugin")

        class DiceModule(BaseModule):
            pass

        old_mod.DiceModule = DiceModule
        old_mod.moduleInfo = {
            "meta": {"name": "dice", "source": "plugin_folder", "top_level": []}
        }

        loader = _make_loader(FakeFinder(None))
        loader._last_module_objs = {"dice": old_mod}

        discover_calls = []

        class FakePluginLoader:
            _loaded_paths: dict = {}

            def discover(self):
                discover_calls.append(1)
                return {}

        loader._plugin_loader = FakePluginLoader()

        manager = FakeManager()
        ok = asyncio.run(loader.reload_module("dice", manager, types.SimpleNamespace()))

        # 插件目录已无该插件：视为删除移除，成功返回
        assert ok is True
        assert discover_calls == [1]
        assert loader._finder.cache_cleared is False
        assert "dice" not in loader._last_module_objs


@pytest.mark.unit
class TestManagerReloadPassthrough:
    """ModuleManager.reload 经 sdk._module_loader 透传"""

    def test_no_sdk_ref_returns_false(self):
        from ErisPulse.Core.module import ModuleManager

        mgr = ModuleManager()
        assert asyncio.run(mgr.reload("dice")) is False

    def test_delegates_to_loader_with_self(self):
        from ErisPulse.Core.module import ModuleManager

        mgr = ModuleManager()

        captured = {}

        class FakeSDK:
            pass

        class FakeLoader:
            async def reload_module(self, name, manager_instance, sdk_instance):
                captured["args"] = (name, manager_instance, sdk_instance)
                return True

        sdk = FakeSDK()
        sdk._module_loader = FakeLoader()
        mgr.set_sdk_ref(sdk)

        assert asyncio.run(mgr.reload("Weather")) is True
        name, manager_instance, sdk_instance = captured["args"]
        assert name == "Weather"
        assert manager_instance is mgr
        assert sdk_instance is sdk

    def test_no_loader_on_sdk_returns_false(self):
        from ErisPulse.Core.module import ModuleManager

        mgr = ModuleManager()
        mgr.set_sdk_ref(types.SimpleNamespace(_module_loader=None))
        assert asyncio.run(mgr.reload("Weather")) is False
