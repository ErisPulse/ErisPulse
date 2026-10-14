"""
本地适配器插件单元测试

覆盖插件目录的适配器发现（discover_adapters）、模块/适配器扫描互斥、
AdapterLoader 的插件并入（本地优先）、热重载（代码变更 / 插件删除 /
未知名称）与 ``ep create adapter --local`` 生成物可发现性。
"""

import asyncio
import sys

import pytest

from ErisPulse.loaders.plugin_folder import PluginFolderLoader

ADAPTER_CORE = '''from ErisPulse import BaseAdapter


class MyAdapter(BaseAdapter):
    """测试适配器"""

    async def call_api(self, endpoint, **params):
        return {"retcode": 0}

    async def start(self):
        pass

    async def shutdown(self):
        pass

    class Send(BaseAdapter.Send):
        async def Raw_ob12(self, message, **kwargs):
            return {"retcode": 0}
'''

ADAPTER_CORE_MAIN = (
    "from ErisPulse import BaseAdapter\n"
    "\n"
    "\n"
    "class Main(BaseAdapter):\n"
    "    async def call_api(self, endpoint, **params):\n"
    "        return {'retcode': 0}\n"
    "\n"
    "    async def start(self):\n"
    "        pass\n"
    "\n"
    "    async def shutdown(self):\n"
    "        pass\n"
)

MODULE_CORE = "from ErisPulse.Core.Bases import BaseModule\n\n\nclass Main(BaseModule):\n    pass\n"


def _purge(names: list[str]) -> None:
    for name in names:
        sys.modules.pop(name, None)
        for mod_name in list(sys.modules):
            if mod_name.startswith(f"{name}."):
                sys.modules.pop(mod_name, None)


@pytest.fixture
def adapter_plugin_dir(tmp_path, monkeypatch):
    """构造 plugins/ 目录：my_adapter（包）+ single.py（单文件适配器）+ weather（模块插件）"""
    plugins = tmp_path / "plugins"
    (plugins / "my_adapter").mkdir(parents=True)
    (plugins / "my_adapter" / "__init__.py").write_text(
        "from .Core import MyAdapter\n", encoding="utf-8"
    )
    (plugins / "my_adapter" / "Core.py").write_text(ADAPTER_CORE, encoding="utf-8")
    (plugins / "single.py").write_text(ADAPTER_CORE, encoding="utf-8")
    (plugins / "weather").mkdir()
    (plugins / "weather" / "__init__.py").write_text(
        "from .Core import Main\n", encoding="utf-8"
    )
    (plugins / "weather" / "Core.py").write_text(MODULE_CORE, encoding="utf-8")

    monkeypatch.chdir(tmp_path)
    monkeypatch.syspath_prepend(str(tmp_path))
    _purge(["my_adapter", "single", "weather"])
    sys.path_importer_cache.clear()
    return plugins


def test_discover_adapters_finds_package_and_single_file(adapter_plugin_dir):
    """discover_adapters() 同时发现包形式与单文件适配器插件"""
    loader = PluginFolderLoader()
    results = loader.discover_adapters()

    assert set(results.keys()) == {"my_adapter", "single"}
    assert results["my_adapter"]["adapter_class"].__name__ == "MyAdapter"
    assert results["my_adapter"]["meta"]["source"] == "adapter_plugin_folder"
    assert results["my_adapter"]["meta"]["package"] is None
    assert results["my_adapter"]["meta"]["top_level"] == ["my_adapter"]


def test_module_scan_skips_adapter_plugins(adapter_plugin_dir):
    """模块扫描不收录适配器插件（静默跳过，不误报 no_module_class）"""
    loader = PluginFolderLoader()
    results = loader.discover()

    assert set(results.keys()) == {"weather"}


def test_adapter_scan_skips_module_plugins(adapter_plugin_dir):
    """适配器扫描不收录模块插件"""
    loader = PluginFolderLoader()
    results = loader.discover_adapters()

    assert "weather" not in results


def test_main_class_takes_priority(tmp_path, monkeypatch):
    """适配器类识别优先 Main 命名"""
    plugins = tmp_path / "plugins"
    pkg = plugins / "main_first"
    pkg.mkdir(parents=True)
    (pkg / "__init__.py").write_text(
        "from .Core import Main, MyAdapter\n", encoding="utf-8"
    )
    (pkg / "Core.py").write_text(
        ADAPTER_CORE + "\n\n" + ADAPTER_CORE_MAIN, encoding="utf-8"
    )

    monkeypatch.chdir(tmp_path)
    monkeypatch.syspath_prepend(str(tmp_path))
    _purge(["main_first"])
    sys.path_importer_cache.clear()

    results = PluginFolderLoader().discover_adapters()
    try:
        assert results["main_first"]["adapter_class"].__name__ == "Main"
    finally:
        _purge(["main_first"])


def test_foreign_reexport_rejected(tmp_path, monkeypatch):
    """外部包重导出的 BaseAdapter 子类不被识别为插件适配器"""
    plugins = tmp_path / "plugins"
    foreign = plugins / "foreign_adapter"
    foreign.mkdir(parents=True)
    (foreign / "__init__.py").write_text(
        "from .Impl import Foreign\n", encoding="utf-8"
    )
    (foreign / "Impl.py").write_text(ADAPTER_CORE.replace("MyAdapter", "Foreign"), encoding="utf-8")
    wrapper = plugins / "wrapper"
    wrapper.mkdir()
    (wrapper / "__init__.py").write_text(
        "from foreign_adapter import Foreign\n", encoding="utf-8"
    )

    monkeypatch.chdir(tmp_path)
    monkeypatch.syspath_prepend(str(tmp_path))
    _purge(["foreign_adapter", "wrapper"])
    sys.path_importer_cache.clear()

    results = PluginFolderLoader().discover_adapters()
    try:
        # foreign_adapter 自身（Impl 定义于其子模块）有效；wrapper 仅重导出外部类，无效
        assert set(results.keys()) == {"foreign_adapter"}
    finally:
        _purge(["foreign_adapter", "wrapper"])


def test_adapter_loader_merges_and_registers(adapter_plugin_dir):
    """AdapterLoader.load() 并入本地适配器并经 register_to_manager 注册"""
    from ErisPulse.Core.adapter import AdapterManager
    from ErisPulse.loaders.adapter import AdapterLoader

    async def run():
        manager = AdapterManager()
        loader = AdapterLoader()
        try:
            objs, enabled_list, _disabled_list = await loader.load(manager)
            assert "my_adapter" in objs
            assert "my_adapter" in enabled_list
            await loader.register_to_manager(enabled_list, objs, manager)
            assert manager.exists("my_adapter")
            info = manager._adapter_info["my_adapter"]
            assert info["meta"]["source"] == "adapter_plugin_folder"
            assert loader._local_adapters.keys() == {"my_adapter", "single"}

            instance = manager._adapters["my_adapter"]
            assert instance._platform == "my_adapter"
        finally:
            await manager.shutdown()

    asyncio.run(run())


def test_create_adapter_local_generates_discoverable_plugin(tmp_path, monkeypatch):
    """ep create adapter --local 生成物可被 discover_adapters() 发现且代码可编译"""
    monkeypatch.chdir(tmp_path)
    monkeypatch.syspath_prepend(str(tmp_path))
    _purge(["Dice"])

    from ErisPulse.CLI.commands.create import CreateCommand

    class Args:
        local = True
        name = "Dice"
        description = "dice adapter"
        author = ""
        email = ""
        homepage = ""
        output = "."
        force = False

    CreateCommand()._create_adapter(Args(), "Dice")

    plugins = tmp_path / "plugins"
    assert (plugins / "Dice" / "__init__.py").is_file()
    assert (plugins / "Dice" / "Core.py").is_file()
    assert (plugins / "Dice" / "Converter.py").is_file()
    assert not (plugins / "Dice" / "pyproject.toml").exists()

    # 生成代码合法（.format() 后 compile 验证）
    for fname in ("__init__.py", "Core.py", "Converter.py"):
        source = (plugins / "Dice" / fname).read_text(encoding="utf-8")
        compile(source, fname, "exec")

    results = PluginFolderLoader().discover_adapters()
    try:
        assert "Dice" in results
        assert results["Dice"]["meta"]["source"] == "adapter_plugin_folder"
    finally:
        _purge(["Dice"])

