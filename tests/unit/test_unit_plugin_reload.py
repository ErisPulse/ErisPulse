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
