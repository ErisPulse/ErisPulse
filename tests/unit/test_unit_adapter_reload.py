"""
适配器代码级热重载单元测试

覆盖：PyPI 来源全链路（卸载 → 清缓存 → 重发现 → 注册 → 重新拉起）、
未知适配器拒绝、适配器被移除、注册失败回滚、身份核对、语法预检取消、
插件来源重载、管理器事件透传。
"""

import asyncio
import sys
import types

import pytest

from ErisPulse.Core.adapter import AdapterManager
from ErisPulse.Core.Event.conversation import _conversation_resume_handlers  # noqa: F401
from ErisPulse.Core.lifecycle import lifecycle
from ErisPulse.loaders.adapter import AdapterLoader


def _make_adapter_module(name: str, version: str = "1.0.0"):
    """在 sys.modules 中构造适配器模块桩（含 __version__ 与占位类）"""
    mod = types.ModuleType(name)
    mod.__version__ = version

    class _Stub:
        pass

    mod.Main = _Stub
    sys.modules[name] = mod
    return mod, _Stub


class FakeEntryPoint:
    """entry-point 桩：.load() 返回注入的类；dist=None（distless 场景）"""

    def __init__(self, cls):
        self._cls = cls
        self.name = "Plat"
        self.dist = None
        self.load_count = 0

    def load(self):
        self.load_count += 1
        return self._cls


class FakeFinder:
    def __init__(self, entry=None):
        self._entry = entry
        self.cache_cleared = False

    def clear_cache(self):
        self.cache_cleared = True

    def find_by_name(self, name):
        return self._entry

    def get_top_level_modules(self, package):
        return []


class FakePluginLoader:
    def __init__(self):
        self._loaded_adapter_paths: dict = {}
        self.discovered: dict = {}

    def get_loaded_adapter_path(self, name):
        return self._loaded_adapter_paths.get(name)

    def discover_adapters(self):
        return self.discovered


class FakeAdapterManager:
    """AdapterManager 测试桩：记录调用序列并模拟注册表行为"""

    def __init__(self):
        self.calls: list[tuple] = []
        self._adapters: dict = {}
        self._adapter_info: dict = {}
        self._started_instances: set = set()
        self._adapter_tasks: dict = {}
        self._bots: dict = {}
        self._enabled = True
        self._register_error: Exception | None = None

    def _collect_dependents(self, name):  # 兼容探针（适配器无级联，仅占位）
        return []

    async def unload(self, name):
        self.calls.append(("unload", name))
        self._adapters.pop(name, None)
        self._adapter_info.pop(name, None)
        self._bots.pop(name, None)
        self._adapter_tasks.pop(name, None)
        return True

    def register(self, name, cls, info):
        if self._register_error is not None:
            raise self._register_error
        self.calls.append(("register", name))
        self._adapter_info[name] = info
        self._adapters[name] = object()  # 替身实例
        return True

    def is_enabled(self, name):
        return self._enabled

    def _config_register(self, name):
        pass

    async def startup(self, platforms=None):
        self.calls.append(("startup", platforms))
        return True


def _make_loader(entry=None, plugin_loader=None) -> AdapterLoader:
    loader = AdapterLoader()
    loader._finder = FakeFinder(entry)
    if plugin_loader is not None:
        loader._plugin_loader = plugin_loader
    return loader


@pytest.mark.unit
class TestAdapterReload:
    """适配器代码级热重载"""

    def _prepare_world(self, pkg_old: str, pkg_new: str):
        old_mod, old_cls = _make_adapter_module(pkg_old)
        new_mod, new_cls = _make_adapter_module(pkg_new)

        old_info = {
            "meta": {"name": "Plat", "package": None, "top_level": [pkg_old], "version": "1.0.0"},
            "adapter_class": old_cls,
        }

        manager = FakeAdapterManager()
        manager._adapter_info["Plat"] = old_info
        instance = object()
        manager._adapters["Plat"] = instance
        manager._started_instances.add(instance)

        entry = FakeEntryPoint(new_cls)
        loader = _make_loader(entry)
        loader._last_adapter_objs["Plat"] = old_mod

        return loader, manager, old_mod, old_cls, new_cls, instance

    def test_reload_pypi_happy_path(self):
        """卸载 → 清缓存 → 重发现 → 注册 → 重新拉起；身份变化"""
        loader, manager, old_mod, old_cls, new_cls, instance = self._prepare_world(
            "fake_adp_old", "fake_adp_new"
        )

        try:
            ok = asyncio.run(loader.reload_adapter("Plat", manager, types.SimpleNamespace()))
            assert ok is True
            assert ("unload", "Plat") in manager.calls
            assert ("register", "Plat") in manager.calls
            assert ("startup", "Plat") in manager.calls  # 原运行态 → 重新拉起
            details = loader._last_adapter_reload_details
            assert details["identity_changed"] is True
            assert details["was_started"] is True
            assert details["version_new"] == "1.0.0"
            # 旧模块缓存已被清除
            assert "fake_adp_old" not in sys.modules
            assert loader._finder.cache_cleared is True
        finally:
            sys.modules.pop("fake_adp_old", None)
            sys.modules.pop("fake_adp_new", None)

    def test_reload_unknown_returns_false(self):
        loader = _make_loader()
        manager = FakeAdapterManager()
        assert asyncio.run(loader.reload_adapter("Ghost", manager, types.SimpleNamespace())) is False

    def test_removed_adapter_returns_true(self):
        loader, manager, *_ = self._prepare_world("fake_adp_gone", "fake_adp_gone2")
        loader._finder = FakeFinder(None)  # entry-point 消失

        ok = asyncio.run(loader.reload_adapter("Plat", manager, types.SimpleNamespace()))
        assert ok is True
        assert ("unload", "Plat") in manager.calls
        assert ("register", "Plat") not in manager.calls
        assert "Plat" not in loader._last_adapter_objs
        assert loader._last_adapter_reload_details["identity_changed"] is True

    def test_register_failure_rolls_back(self):
        loader, manager, old_mod, old_cls, new_cls, instance = self._prepare_world(
            "fake_adp_rb_old", "fake_adp_rb_new"
        )
        manager._register_error = RuntimeError("boom")

        try:
            ok = asyncio.run(loader.reload_adapter("Plat", manager, types.SimpleNamespace()))
            assert ok is False
            # 回滚：旧注册信息与旧实例恢复
            assert manager._adapter_info["Plat"]["adapter_class"] is old_cls
            assert manager._adapters["Plat"] is instance
            assert "fake_adp_rb_old" in sys.modules  # sys.modules 条目恢复
            assert loader._last_adapter_reload_details == {}
        finally:
            sys.modules.pop("fake_adp_rb_old", None)
            sys.modules.pop("fake_adp_rb_new", None)

    def test_identity_unchanged_warns(self):
        old_mod, old_cls = _make_adapter_module("fake_adp_same")
        old_info = {
            "meta": {"name": "Plat", "package": None, "top_level": ["fake_adp_same"]},
            "adapter_class": old_cls,
        }
        manager = FakeAdapterManager()
        manager._adapter_info["Plat"] = old_info
        instance = object()
        manager._adapters["Plat"] = instance
        manager._started_instances.add(instance)

        entry = FakeEntryPoint(old_cls)  # 重导入仍返回同类对象 → 身份未变化
        loader = _make_loader(entry)
        loader._last_adapter_objs["Plat"] = old_mod

        try:
            ok = asyncio.run(loader.reload_adapter("Plat", manager, types.SimpleNamespace()))
            assert ok is True
            assert loader._last_adapter_reload_details["identity_changed"] is False
        finally:
            sys.modules.pop("fake_adp_same", None)

    def test_precheck_failure_cancels_unload(self, tmp_path):
        bad = tmp_path / "broken_adp.py"
        bad.write_text("def broken(:\n", encoding="utf-8")

        old_mod, old_cls = _make_adapter_module("fake_adp_broken")
        old_mod.__file__ = str(bad)
        old_info = {
            "meta": {"name": "Plat", "package": None, "top_level": ["fake_adp_broken"]},
            "adapter_class": old_cls,
        }
        manager = FakeAdapterManager()
        manager._adapter_info["Plat"] = old_info

        loader = _make_loader(FakeEntryPoint(old_cls))
        loader._last_adapter_objs["Plat"] = old_mod

        try:
            ok = asyncio.run(loader.reload_adapter("Plat", manager, types.SimpleNamespace()))
            assert ok is False
            # 预检失败：未进入卸载流程
            assert ("unload", "Plat") not in manager.calls
        finally:
            sys.modules.pop("fake_adp_broken", None)

    def test_plugin_source_reload(self):
        old_mod, old_cls = _make_adapter_module("fake_adp_plugin")

        class FakePluginLoader:
            def __init__(self):
                self._loaded_adapter_paths = {"Plat": "/plugins/plat/Main.py"}
                self.discovered = {}

            def get_loaded_adapter_path(self, name):
                return self._loaded_adapter_paths.get(name)

            def discover_adapters(self):
                return self.discovered

        plugin = FakePluginLoader()
        new_cls = type("NewAdapter", (), {})
        new_mod = types.ModuleType("fake_adp_plugin_mod")
        plugin.discovered["Plat"] = {
            "name": "Plat",
            "meta": {
                "name": "Plat",
                "source": "adapter_plugin_folder",
                "top_level": ["Plat"],
            },
            "adapter_class": new_cls,
            "module_obj": new_mod,
        }

        manager = FakeAdapterManager()
        manager._adapter_info["Plat"] = {
            "meta": {"name": "Plat", "source": "adapter_plugin_folder"},
            "adapter_class": old_cls,
        }
        manager._adapters["Plat"] = object()

        loader = _make_loader(FakeEntryPoint(old_cls), plugin_loader=plugin)
        loader._last_adapter_objs["Plat"] = old_mod

        try:
            ok = asyncio.run(loader.reload_adapter("Plat", manager, types.SimpleNamespace()))
            assert ok is True
            assert loader._last_adapter_reload_details["source"] == "plugin"
            # 插件路径记录被清理后由 discover 重新登记
            assert "Plat" not in plugin._loaded_adapter_paths
        finally:
            sys.modules.pop("fake_adp_plugin", None)

    def test_disabled_adapter_not_started(self):
        loader, manager, *_ = self._prepare_world("fake_adp_dis_old", "fake_adp_dis_new")
        manager._enabled = False

        try:
            ok = asyncio.run(loader.reload_adapter("Plat", manager, types.SimpleNamespace()))
            assert ok is True
            assert ("register", "Plat") not in manager.calls
            assert ("startup", "Plat") not in manager.calls
            assert loader._last_adapter_reload_details["was_started"] is False
        finally:
            sys.modules.pop("fake_adp_dis_old", None)
            sys.modules.pop("fake_adp_dis_new", None)


@pytest.mark.unit
class TestAdapterManagerReload:
    """AdapterManager.reload 事件透传"""

    def test_reload_delegates_and_emits_event(self):
        captured = {}

        class FakeSDK:
            pass

        class FakeLoader:
            async def reload_adapter(self, name, manager_instance, sdk_instance, *, full=True):
                captured["args"] = (name, manager_instance, sdk_instance)
                captured["full"] = full
                return True

        manager = AdapterManager()
        sdk = FakeSDK()
        sdk._adapter_loader = FakeLoader()
        manager._sdk = (sdk)

        def _capture(data):
            captured["event"] = dict(data)

        lifecycle.register("adapter.reload", _capture)
        try:
            assert asyncio.run(manager.reload("Plat")) is True
        finally:
            lifecycle.unregister("adapter.reload", _capture)

        name, manager_instance, sdk_instance = captured["args"]
        assert name == "Plat"
        assert manager_instance is manager
        assert sdk_instance is sdk
        assert captured["full"] is True
        event = captured.get("event") or {}
        assert event.get("adapter_name") == "Plat"
        assert event.get("success") is True
        assert "duration_ms" in event

    def test_reload_without_loader_returns_false(self):
        manager = AdapterManager()
        manager._sdk = (types.SimpleNamespace(_adapter_loader=None))
        assert asyncio.run(manager.reload("Plat")) is False
