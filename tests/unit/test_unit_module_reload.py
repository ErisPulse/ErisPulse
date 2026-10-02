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
            async def reload_module(self, name, manager_instance, sdk_instance, *, full=False):
                captured["args"] = (name, manager_instance, sdk_instance)
                captured["full"] = full
                return True

        sdk = FakeSDK()
        sdk._module_loader = FakeLoader()
        mgr.set_sdk_ref(sdk)

        assert asyncio.run(mgr.reload("Weather")) is True
        name, manager_instance, sdk_instance = captured["args"]
        assert name == "Weather"
        assert manager_instance is mgr
        assert sdk_instance is sdk
        assert captured["full"] is False

    def test_no_loader_on_sdk_returns_false(self):
        from ErisPulse.Core.module import ModuleManager

        mgr = ModuleManager()
        mgr.set_sdk_ref(types.SimpleNamespace(_module_loader=None))
        assert asyncio.run(mgr.reload("Weather")) is False


@pytest.mark.unit
class TestFullReload:
    """full=True 全量重载：清理名单增强 + 依赖者重导代码"""

    def test_full_purges_top_level_from_module_object(self):
        """top_level 元数据缺失时，full=True 用旧模块对象顶层段兜底清理"""
        old_mod, _ = _make_module_in_sys("fake_meteor_pkg")
        new_mod, _ = _make_module_in_sys("fake_meteor_pkg")
        old_mod.moduleInfo = {"meta": {"name": "Meteor", "package": None}}

        # 元数据盲区：子模块仅存在于 import 缓存
        sub = types.ModuleType("fake_meteor_pkg.core")
        sys.modules["fake_meteor_pkg.core"] = sub

        loader = _make_loader(FakeEntryPoint(new_mod))
        loader._last_module_objs = {"Meteor": old_mod}
        manager = FakeManager()

        try:
            ok = asyncio.run(
                loader.reload_module("Meteor", manager, types.SimpleNamespace(), full=True)
            )
            assert ok is True
            # 盲区被兜底清理：子模块不再残留旧缓存
            assert "fake_meteor_pkg.core" not in sys.modules
            assert loader._finder.cache_cleared is True
        finally:
            sys.modules.pop("fake_meteor_pkg", None)
            sys.modules.pop("fake_meteor_pkg.core", None)

    def test_default_mode_keeps_cache_when_metadata_missing(self):
        """默认模式 + 元数据缺失：清理名单为空（假重载），现以显式告警提示"""
        old_mod, _ = _make_module_in_sys("fake_comet_pkg")
        new_mod, _ = _make_module_in_sys("fake_comet_pkg")
        old_mod.moduleInfo = {"meta": {"name": "Comet", "package": None}}

        sub = types.ModuleType("fake_comet_pkg.core")
        sys.modules["fake_comet_pkg.core"] = sub

        loader = _make_loader(FakeEntryPoint(new_mod))
        loader._last_module_objs = {"Comet": old_mod}
        manager = FakeManager()

        try:
            ok = asyncio.run(loader.reload_module("Comet", manager, types.SimpleNamespace()))
            assert ok is True
            # 默认模式不清理元数据外的缓存（保持既有语义，行为差异由 full=True 承担）
            assert "fake_comet_pkg.core" in sys.modules
        finally:
            sys.modules.pop("fake_comet_pkg", None)
            sys.modules.pop("fake_comet_pkg.core", None)

    def test_full_reloads_pypi_dependent_code(self):
        """full=True：PyPI 依赖者级联时同样重导代码（而非仅重新实例化）"""
        old_mod, _ = _make_module_in_sys("fake_root_pkg")
        new_mod, _ = _make_module_in_sys("fake_root_pkg")
        old_mod.moduleInfo = {
            "meta": {"name": "Root", "package": "erispulse-root", "top_level": ["fake_root_pkg"]}
        }

        dep_mod, _ = _make_module_in_sys("fake_dep_pkg")
        new_dep_mod, _ = _make_module_in_sys("fake_dep_pkg")
        dep_mod.moduleInfo = {
            "meta": {"name": "Helper", "package": "erispulse-dep", "top_level": ["fake_dep_pkg"]}
        }

        entry = FakeEntryPoint(new_mod)
        dep_entry = FakeEntryPoint(new_dep_mod)

        class DictFinder(FakeFinder):
            """按名字返回各自 entry-point 的桩"""

            def __init__(self):
                super().__init__(entry)
                self._entries = {"Root": entry, "Helper": dep_entry}

            def find_by_name(self, name):
                return self._entries.get(name)

        loader = _make_loader(finder=DictFinder())
        loader._last_module_objs = {"Root": old_mod, "Helper": dep_mod}

        manager = FakeManager()
        manager._module_info = {
            "Root": old_mod.moduleInfo,
            "Helper": dep_mod.moduleInfo,
        }
        manager._module_classes = {"Root": object, "Helper": object}

        def collect_dependents(name):
            return ["Helper"] if name == "Root" else []

        manager._collect_dependents = collect_dependents

        try:
            ok = asyncio.run(loader.reload_module("Root", manager, types.SimpleNamespace(), full=True))
            assert ok is True
            # 依赖者走完整重载：entry-point 重新导入 + 重新注册
            assert dep_entry.load_count == 1
            assert ("register", "Helper") in manager.calls
        finally:
            for name in ("fake_root_pkg", "fake_dep_pkg"):
                sys.modules.pop(name, None)

    def test_default_mode_dependent_skips_reimport(self):
        """默认模式：PyPI 依赖者仅重新实例化，不重导代码（既有语义）"""
        old_mod, _ = _make_module_in_sys("fake_root2_pkg")
        new_mod, _ = _make_module_in_sys("fake_root2_pkg")
        old_mod.moduleInfo = {
            "meta": {"name": "Root", "package": "erispulse-root", "top_level": ["fake_root2_pkg"]}
        }

        dep_mod, _ = _make_module_in_sys("fake_dep2_pkg")
        dep_mod.moduleInfo = {
            "meta": {"name": "Helper", "package": "erispulse-dep", "top_level": ["fake_dep2_pkg"]}
        }
        dep_entry = FakeEntryPoint(dep_mod)

        class DictFinder(FakeFinder):
            def __init__(self):
                super().__init__(FakeEntryPoint(new_mod))
                self._entries = {"Root": self._entry_point, "Helper": dep_entry}

            def find_by_name(self, name):
                return self._entries.get(name)

        loader = _make_loader(finder=DictFinder())
        loader._last_module_objs = {"Root": old_mod, "Helper": dep_mod}

        manager = FakeManager()
        manager._module_info = {"Root": old_mod.moduleInfo, "Helper": dep_mod.moduleInfo}
        manager._module_classes = {"Root": object, "Helper": object}
        manager._collect_dependents = lambda name: ["Helper"] if name == "Root" else []

        try:
            ok = asyncio.run(loader.reload_module("Root", manager, types.SimpleNamespace()))
            assert ok is True
            # 依赖者只 manager.load 重新实例化，entry-point 不重导
            assert dep_entry.load_count == 0
            assert ("load", "Helper") in manager.calls
        finally:
            for name in ("fake_root2_pkg", "fake_dep2_pkg"):
                sys.modules.pop(name, None)


@pytest.mark.unit
class TestReloadAll:
    """reload_all 全量重载所有模块"""

    def _build_world(self, pkg_a: str, pkg_b: str):
        """构造双模块世界：old 两个模块对象 + find_all 可发现的新 entry-points"""
        old_a, _ = _make_module_in_sys(pkg_a)
        old_b, _ = _make_module_in_sys(pkg_b)
        old_a.moduleInfo = {"meta": {"name": "Alpha", "package": None}}
        old_b.moduleInfo = {"meta": {"name": "Beta", "package": None, "depends": ["Alpha"]}}

        new_a, cls_a = _make_module_in_sys(pkg_a)
        new_b, cls_b = _make_module_in_sys(pkg_b)

        entry_a = FakeEntryPoint(new_a)
        entry_a.name = "Alpha"
        entry_b = FakeEntryPoint(new_b)
        entry_b.name = "Beta"

        class AllFinder(FakeFinder):
            def __init__(self):
                super().__init__(entry_a)
                self._entries = [entry_a, entry_b]
                self.last_error = None

            def find_all(self):
                return list(self._entries)

            def find_by_name(self, name):
                return {"Alpha": entry_a, "Beta": entry_b}.get(name)

        return old_a, old_b, new_a, new_b, AllFinder()

    def test_reload_all_pipeline(self, monkeypatch):
        """卸载全部 → 清缓存 → 重新发现注册 → 拓扑加载 → 重载前已加载模块重新激活"""
        pkg_a, pkg_b = "fake_all_pkg_a", "fake_all_pkg_b"
        old_a, old_b, new_a, new_b, finder = self._build_world(pkg_a, pkg_b)

        # 盲区模块对象（旧）：子模块残留 import 缓存，reload_all 应一并清理
        sub = types.ModuleType(f"{pkg_a}.core")
        sys.modules[sub.__name__] = sub

        loader = _make_loader(finder=finder)
        # 钉定懒加载策略（环境框架配置可能关闭全局懒加载，导致走 eager 路径）
        monkeypatch.setattr(loader, "_get_global_lazy_loading", lambda: True)

        class FakePluginLoader:
            _loaded_paths: dict = {}

            def discover(self):
                return {}

        loader._plugin_loader = FakePluginLoader()
        loader._last_module_objs = {"Alpha": old_a, "Beta": old_b}

        class AllManager:
            def __init__(self):
                self.calls: list[tuple] = []
                self._module_info: dict = {}
                self._module_classes: dict = {}
                self._modules: dict = {}
                self._module_services: dict = {}
                self._loaded_modules = {"Alpha", "Beta"}
                self._lazy_modules: dict = {}

            def _collect_dependents(self, name):
                return []

            async def unload(self, name, *, purge=False):
                self.calls.append(("unload", name, purge))
                self._loaded_modules.clear()
                return True

            def exists(self, name):
                return True

            def is_enabled(self, name):
                return True

            def _config_register(self, name):
                self.calls.append(("config_register", name))

            def register(self, name, cls, info):
                self.calls.append(("register", name))
                self._module_classes[name] = cls
                self._module_info[name] = info
                return True

            def register_lazy(self, name, proxy):
                self.calls.append(("register_lazy", name))
                self._lazy_modules[name] = proxy

            async def load(self, name):
                self.calls.append(("load", name))
                self._modules[name] = "instance"
                self._loaded_modules.add(name)
                return True

            def get(self, name):
                return self._modules.get(name)

        manager = AllManager()

        class WeakrefSdk:
            """LazyModule 持 SDK 弱引用，桩需支持 weakref（SimpleNamespace 不支持）"""

        sdk = WeakrefSdk()

        try:
            results = asyncio.run(loader.reload_all(manager, sdk))

            # 双模块全部成功，结果键为注册名
            assert results == {"Alpha": True, "Beta": True}
            # 全量卸载（purge 清注册存根）
            assert ("unload", None, True) in manager.calls
            # 元数据缺失的模块也经旧对象顶层段完成缓存清理
            assert f"{pkg_a}.core" not in sys.modules
            # 重新注册并按懒加载策略挂载（与冷启动管线一致）
            assert ("register", "Alpha") in manager.calls
            assert ("register", "Beta") in manager.calls
            assert ("register_lazy", "Alpha") in manager.calls
            assert ("register_lazy", "Beta") in manager.calls
            # 重载前处于已加载态的懒加载模块重新激活
            assert ("load", "Alpha") in manager.calls
            assert ("load", "Beta") in manager.calls
            # 发现快照被替换为新模块对象
            assert loader._last_module_objs["Alpha"] is new_a
            assert loader._last_module_objs["Beta"] is new_b
        finally:
            for name in (pkg_a, pkg_b, f"{pkg_a}.core"):
                sys.modules.pop(name, None)

    def test_reload_all_no_modules(self):
        """空快照：直接走发现管线，返回空结果不报错"""
        loader = _make_loader()

        class FakePluginLoader:
            _loaded_paths: dict = {}

            def discover(self):
                return {}

        loader._plugin_loader = FakePluginLoader()

        class EmptyManager:
            _loaded_modules: set = set()
            _lazy_modules: dict = {}

            def _collect_dependents(self, name):
                return []

            async def unload(self, name, *, purge=False):
                return True

            def exists(self, name):
                return True

            def is_enabled(self, name):
                return True

            def _config_register(self, name):
                pass

            def register(self, name, cls, info):
                return True

            def register_lazy(self, name, proxy):
                pass

            async def load(self, name):
                return True

            def get(self, name):
                return None

        results = asyncio.run(loader.reload_all(EmptyManager(), types.SimpleNamespace()))
        assert results == {}
