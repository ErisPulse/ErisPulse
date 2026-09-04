"""
本地插件热重载监控（PluginReloadWatcher）单元测试

覆盖插件文件变更 → 插件名解析 → 重载回调触发的完整链路。
"""

import asyncio

from ErisPulse.runtime.plugin_reload import PluginReloadWatcher


def test_watcher_resolves_plugin_name(tmp_path, monkeypatch):
    """_handle_change 将文件路径解析为插件名（单文件 / 包形式）"""
    plugins = tmp_path / "plugins"
    (plugins / "weather" / "Core.py").parent.mkdir(parents=True)
    (plugins / "dice.py").write_text("x = 1", encoding="utf-8")

    monkeypatch.chdir(tmp_path)

    received = []

    async def on_reload(name):
        received.append(name)

    watcher = PluginReloadWatcher(on_reload)
    watcher._dirs = ["plugins"]

    async def run():
        # 单文件：plugins/dice.py → dice
        await watcher._handle_change(str(plugins / "dice.py"))
        # 包形式：plugins/weather/Core.py → weather
        await watcher._handle_change(str(plugins / "weather" / "Core.py"))
        # 包 __init__：plugins/weather/__init__.py → weather
        await watcher._handle_change(str(plugins / "weather" / "__init__.py"))

    asyncio.run(run())

    assert received == ["dice", "weather", "weather"], received


def test_watcher_start_stop_no_dirs(tmp_path, monkeypatch):
    """无插件目录时 start() 返回 False"""
    monkeypatch.chdir(tmp_path)

    async def on_reload(name):
        pass

    watcher = PluginReloadWatcher(on_reload)
    # 覆盖 _plugin_dirs 返回空
    watcher._plugin_dirs = list
    assert watcher.start() is False


def test_watcher_starts_and_stops(tmp_path, monkeypatch):
    """有插件目录时 start() 返回 True，stop() 后不再运行"""
    plugins = tmp_path / "plugins"
    plugins.mkdir()
    (plugins / "dice.py").write_text("x = 1", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    async def on_reload(name):
        pass

    watcher = PluginReloadWatcher(on_reload, interval=0.05)
    assert watcher.start() is True
    assert watcher.is_running is True
    watcher.stop()
    assert watcher.is_running is False


class TestSDKLoaderWiring:
    """SDK 与模块加载器的引用接线（热重载依赖 sdk._module_loader）"""

    def test_initializer_exposes_module_loader_to_sdk(self):
        """Initializer 创建的 ModuleLoader 必须注入 SDK，否则热重载永远不可用"""
        from ErisPulse import SDK

        sdk = SDK()
        assert sdk._module_loader is None

        initializer = sdk.Initializer(sdk)
        assert sdk._module_loader is not None
        assert sdk._module_loader is initializer._module_loader

    def test_reload_plugin_before_init_returns_false(self):
        """未初始化（无加载器）时 reload_plugin 优雅返回 False 而非抛错"""
        from ErisPulse import SDK

        sdk = SDK()
        assert asyncio.run(sdk.reload_plugin("dice")) is False

    def test_reload_plugin_passes_sdk_self(self):
        """reload_plugin 向加载器传递 SDK 实例自身（而非不存在的 _sdk 属性）"""
        from ErisPulse import SDK

        sdk = SDK()
        sdk.Initializer(sdk)

        captured = {}

        async def fake_reload(plugin_name, manager_instance, sdk_instance):
            captured["args"] = (plugin_name, manager_instance, sdk_instance)
            return True

        sdk._module_loader.reload_plugin = fake_reload
        assert asyncio.run(sdk.reload_plugin("dice")) is True
        name, manager, sdk_instance = captured["args"]
        assert name == "dice"
        assert manager is sdk.module
        assert sdk_instance is sdk
