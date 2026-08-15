"""
本地插件文件夹（PluginFolderLoader）单元测试

覆盖插件发现、导入、模块类识别、moduleInfo 构造与
ModuleLoader.load() 的插件并入（本地优先）行为。
"""

import asyncio
import sys

import pytest

from ErisPulse.loaders.plugin_folder import DEFAULT_PLUGINS_DIR, PluginFolderLoader

PLUGIN_CORE = """from ErisPulse.Core.Bases import BaseModule


class Main(BaseModule):
    def __init__(self, sdk=None):
        self.sdk = sdk

    async def on_load(self, event):
        return True

    async def on_unload(self, event):
        return True

    def greet(self):
        return "hello"
"""


@pytest.fixture
def plugin_dir(tmp_path, monkeypatch):
    """构造 plugins/ 目录：weather（包）+ dice.py（单文件）"""
    plugins = tmp_path / "plugins"
    (plugins / "weather").mkdir(parents=True)
    (plugins / "weather" / "__init__.py").write_text(
        "from .Core import Main\n", encoding="utf-8"
    )
    (plugins / "weather" / "Core.py").write_text(PLUGIN_CORE, encoding="utf-8")
    (plugins / "dice.py").write_text(PLUGIN_CORE, encoding="utf-8")

    monkeypatch.chdir(tmp_path)
    # 包形式插件通过 import_module 导入，依赖 sys.path 中存在插件父目录；
    # 显式注入并清理模块名残留，保证跨测试文件组合时的隔离性
    monkeypatch.syspath_prepend(str(tmp_path))
    for _name in ("weather", "weather.Core", "dice"):
        sys.modules.pop(_name, None)
    return plugins


def test_default_plugins_dir():
    """默认插件目录名为 plugins"""
    assert DEFAULT_PLUGINS_DIR == "plugins"


def test_discover_finds_package_and_single_file(plugin_dir):
    """discover() 同时发现包形式与单文件插件"""
    loader = PluginFolderLoader()
    results = loader.discover()

    assert set(results.keys()) == {"weather", "dice"}
    assert results["weather"].moduleInfo["meta"]["source"] == "plugin_folder"
    assert results["dice"].moduleInfo["meta"]["source"] == "plugin_folder"


def test_discover_builds_module_info(plugin_dir):
    """discover() 构造的 moduleInfo 与 entry-point 结构一致"""
    loader = PluginFolderLoader()
    results = loader.discover()

    meta = results["weather"].moduleInfo["meta"]
    assert meta["name"] == "weather"
    assert meta["package"] is None
    assert meta["lazy_load"] is True
    assert meta["is_base_module"] is True

    from ErisPulse.Core.Bases import BaseModule

    module_class = results["weather"].moduleInfo["module_class"]
    assert issubclass(module_class, BaseModule)
    assert module_class().greet() == "hello"


def test_discover_ignores_invalid_entries(plugin_dir):
    """discover() 忽略非 .py 文件与不含 __init__.py 的目录"""
    (plugin_dir / "readme.txt").write_text("not a plugin", encoding="utf-8")
    (plugin_dir / "_private.py").write_text("x = 1", encoding="utf-8")
    (plugin_dir / "no_init").mkdir()

    loader = PluginFolderLoader()
    results = loader.discover()

    assert set(results.keys()) == {"weather", "dice"}


def test_get_loaded_path_tracks_plugins(plugin_dir):
    """get_loaded_path() 返回已加载插件的源路径"""
    loader = PluginFolderLoader()
    loader.discover()

    assert loader.get_loaded_path("weather").resolve() == (plugin_dir / "weather").resolve()
    assert loader.get_loaded_path("unknown") is None


def test_module_loader_merges_plugin_folder(plugin_dir):
    """ModuleLoader.load() 将插件并入加载结果并加入启用列表"""
    from ErisPulse.Core.module import ModuleManager
    from ErisPulse.loaders.module import ModuleLoader

    async def run():
        manager = ModuleManager()
        loader = ModuleLoader()
        objs, enabled_list, _disabled_list = await loader.load(manager)

        assert "weather" in objs
        assert "dice" in objs
        assert "weather" in enabled_list
        assert "dice" in enabled_list
        assert objs["weather"].moduleInfo["meta"]["source"] == "plugin_folder"

    asyncio.run(run())
