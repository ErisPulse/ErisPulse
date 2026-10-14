"""
ep create pack 单元测试

覆盖本地插件 → 可发布项目的转换：包形式模块插件、单文件适配器插件、
pyproject entry-point 按类型生成、无插件/未知插件的错误路径。
"""

import sys

import pytest

MODULE_CORE = """from ErisPulse.Core.Bases import BaseModule


class Main(BaseModule):
    pass
"""

ADAPTER_SINGLE = """from ErisPulse import BaseAdapter


class MyAdapter(BaseAdapter):
    async def call_api(self, endpoint, **params):
        return {}

    async def start(self):
        pass

    async def shutdown(self):
        pass
"""


class Args:
    name = None
    description = "converted plugin"
    author = "tester"
    email = "t@e.st"
    homepage = "https://example.com"
    output = "."
    force = False


@pytest.fixture
def plugins_dir(tmp_path, monkeypatch):
    """构造 plugins/ 目录：dice（包形式模块）+ ping.py（单文件适配器）"""
    plugins = tmp_path / "plugins"
    (plugins / "dice").mkdir(parents=True)
    (plugins / "dice" / "__init__.py").write_text(
        "from .Core import Main\n", encoding="utf-8"
    )
    (plugins / "dice" / "Core.py").write_text(MODULE_CORE, encoding="utf-8")
    (plugins / "ping.py").write_text(ADAPTER_SINGLE, encoding="utf-8")

    monkeypatch.chdir(tmp_path)
    monkeypatch.syspath_prepend(str(tmp_path))
    for name in ("dice", "dice.Core", "ping"):
        sys.modules.pop(name, None)
    sys.path_importer_cache.clear()
    return plugins


def _patch_prompts(monkeypatch, project_name="Dice"):
    """跳过交互：项目名固定返回，元信息走 Args

    patch rich 的 Prompt.ask 而非 create 模块属性：CLI 命令发现机制在
    全量测试下可能与测试 import 的 create 模块副本不一致（reload 副本），
    而 rich 模块是跨副本共享单例
    """
    from rich.prompt import Prompt

    monkeypatch.setattr(
        Prompt, "ask", classmethod(lambda cls, *a, **kw: project_name)
    )


def test_pack_module_plugin_to_project(plugins_dir, monkeypatch):
    """包形式模块插件转换为标准项目（entry-point 指向 Main）"""
    args = Args()
    args.name = "dice"
    _patch_prompts(monkeypatch, project_name="Dice")

    from ErisPulse.CLI.commands.create import CreateCommand

    CreateCommand()._create_pack(args)

    project = plugins_dir.parent / "Dice"
    assert (project / "pyproject.toml").is_file()
    assert (project / "LICENSE").is_file()
    assert (project / "README.md").is_file()
    assert (project / "Dice" / "__init__.py").is_file()
    assert (project / "Dice" / "Core.py").is_file()

    pyproject = (project / "pyproject.toml").read_text(encoding="utf-8")
    assert '"erispulse.module"' in pyproject
    assert '"dice" = "Dice:Main"' in pyproject
    assert 'packages = ["Dice"]' in pyproject

    # 生成代码合法
    for rel in ("Dice/__init__.py", "Dice/Core.py"):
        compile((project / rel).read_text(encoding="utf-8"), rel, "exec")


def test_pack_single_file_adapter_plugin(plugins_dir, monkeypatch):
    """单文件适配器插件转换：生成 __init__ 导出与 adapter entry-point"""
    args = Args()
    args.name = "ping"
    _patch_prompts(monkeypatch, project_name="Ping")

    from ErisPulse.CLI.commands.create import CreateCommand

    CreateCommand()._create_pack(args)

    project = plugins_dir.parent / "Ping"
    init_src = (project / "Ping" / "__init__.py").read_text(encoding="utf-8")
    assert "from .ping import MyAdapter" in init_src
    assert (project / "Ping" / "ping.py").is_file()

    pyproject = (project / "pyproject.toml").read_text(encoding="utf-8")
    assert '"erispulse.adapter"' in pyproject
    assert '"ping" = "Ping:MyAdapter"' in pyproject


def test_pack_without_plugins_exits(plugins_dir, monkeypatch):
    """插件目录为空时报错退出"""
    import shutil

    shutil.rmtree(plugins_dir)

    from ErisPulse.CLI.commands.create import CreateCommand

    with pytest.raises(SystemExit) as exc_info:
        CreateCommand()._create_pack(Args())
    assert exc_info.value.code == 1


def test_pack_unknown_plugin_exits(plugins_dir, monkeypatch):
    """--name 未命中候选插件时报错退出"""
    args = Args()
    args.name = "no_such_plugin"

    from ErisPulse.CLI.commands.create import CreateCommand

    with pytest.raises(SystemExit) as exc_info:
        CreateCommand()._create_pack(args)
    assert exc_info.value.code == 1
