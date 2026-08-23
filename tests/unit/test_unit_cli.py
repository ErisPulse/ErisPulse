"""
CLI system unit tests.

Covers command registration, alias resolution, argument parsing and command
routing. No network or filesystem side effects (execute is always mocked).

Run via:

    pytest tests/unit/test_unit_cli.py -v
    pytest tests/unit/test_unit_cli.py -k alias -v
    pytest -m unit -k cli
"""

import sys
from argparse import ArgumentParser

import pytest

from ErisPulse.CLI.base import Command
from ErisPulse.CLI.cli import CLI
from ErisPulse.CLI.registry import CommandRegistry

# ==================== Expected commands & aliases ====================

EXPECTED_COMMANDS = {
    "create": ["c", "new"],
    "init": [],
    "install": ["i", "add"],
    "uninstall": ["rm", "remove"],
    "upgrade": ["up"],
    "self-update": ["su", "update"],
    "list": ["l", "ls"],
    "list-remote": ["lsr"],
    "run": ["r"],
    "i18n": ["language", "lang"],
    "types": ["t", "stub"],
    "doctor": ["diag"],
}


# ==================== Fixtures ====================


@pytest.fixture
def clean_registry():
    """Provide an empty CommandRegistry singleton; restore afterwards."""
    reg = CommandRegistry()
    saved_commands = dict(reg._commands)
    saved_aliases = dict(reg._aliases)
    reg._commands.clear()
    reg._aliases.clear()
    yield reg
    reg._commands.clear()
    reg._aliases.clear()
    reg._commands.update(saved_commands)
    reg._aliases.update(saved_aliases)


@pytest.fixture
def fresh_cli(monkeypatch):
    """Provide a freshly discovered CLI instance (registry reset then rebuilt)."""
    import ErisPulse.CLI.cli as cli_mod

    monkeypatch.setattr(cli_mod, "print_banner", lambda: None)

    reg = CommandRegistry()
    reg._commands.clear()
    reg._aliases.clear()
    cli = CLI()
    yield cli
    reg._commands.clear()
    reg._aliases.clear()


# ==================== Helper test commands ====================


class _FooCommand(Command):
    """Test command."""

    name = "foo"
    description = "foo command"
    aliases = ["f", "foofoo"]

    def add_arguments(self, parser: ArgumentParser):
        parser.add_argument("--flag", action="store_true")

    def execute(self, args):
        return "foo"


class _BarCommand(Command):
    """Test command used for alias-collision scenarios."""

    name = "bar"
    description = "bar command"
    aliases = ["b"]

    def add_arguments(self, parser: ArgumentParser):
        pass

    def execute(self, args):
        return "bar"


# ==================== CommandRegistry unit tests ====================


class TestCommandRegistry:
    """CommandRegistry core logic."""

    def test_singleton(self):
        assert CommandRegistry() is CommandRegistry()

    def test_register_and_get(self, clean_registry):
        cmd = _FooCommand()
        clean_registry.register(cmd)
        assert clean_registry.get("foo") is cmd

    def test_get_by_alias(self, clean_registry):
        cmd = _FooCommand()
        clean_registry.register(cmd)
        assert clean_registry.get("f") is cmd
        assert clean_registry.get("foofoo") is cmd

    def test_get_unknown_returns_none(self, clean_registry):
        clean_registry.register(_FooCommand())
        assert clean_registry.get("nope") is None

    def test_resolve_canonical(self, clean_registry):
        clean_registry.register(_FooCommand())
        assert clean_registry.resolve("foo") == "foo"

    def test_resolve_alias(self, clean_registry):
        clean_registry.register(_FooCommand())
        assert clean_registry.resolve("f") == "foo"
        assert clean_registry.resolve("foofoo") == "foo"

    def test_resolve_unknown(self, clean_registry):
        clean_registry.register(_FooCommand())
        assert clean_registry.resolve("missing") is None

    def test_exists_supports_alias(self, clean_registry):
        clean_registry.register(_FooCommand())
        assert clean_registry.exists("foo")
        assert clean_registry.exists("f")
        assert not clean_registry.exists("missing")

    def test_list_aliases(self, clean_registry):
        clean_registry.register(_FooCommand())
        clean_registry.register(_BarCommand())
        aliases = clean_registry.list_aliases()
        assert aliases == {"f": "foo", "foofoo": "foo", "b": "bar"}

    def test_alias_collision_first_wins(self, clean_registry):
        clean_registry.register(_FooCommand())

        class _ConflictCommand(Command):
            name = "conflict"
            description = "conflict command"
            aliases = ["f"]  # collides with foo's "f"

            def add_arguments(self, parser):
                pass

            def execute(self, args):
                pass

        clean_registry.register(_ConflictCommand())
        assert clean_registry.resolve("f") == "foo"

    def test_register_duplicate_name_silently_skips(self, clean_registry):
        clean_registry.register(_FooCommand())
        second = _FooCommand()
        clean_registry.register(second)
        assert clean_registry.get("foo") is not second


# ==================== Discovery & alias integrity tests ====================


class TestCommandDiscovery:
    """CLI auto-discovery and builtin alias configuration."""

    def test_all_commands_discovered(self, fresh_cli):
        names = set(fresh_cli.registry.list_all())
        assert names == set(EXPECTED_COMMANDS.keys())

    def test_all_expected_aliases_present(self, fresh_cli):
        aliases = fresh_cli.registry.list_aliases()
        for canonical, alias_list in EXPECTED_COMMANDS.items():
            for alias in alias_list:
                assert aliases.get(alias) == canonical, (
                    "alias '%s' not mapped to '%s'" % (alias, canonical)
                )

    def test_no_alias_conflicts(self, fresh_cli):
        aliases = fresh_cli.registry.list_aliases()
        canonical_names = set(fresh_cli.registry.list_all())
        # aliases must not shadow canonical names
        assert not (set(aliases.keys()) & canonical_names)
        # every alias must be unique across commands
        all_aliases = []
        for cmd in fresh_cli.registry.get_all():
            all_aliases.extend(getattr(cmd, "aliases", []) or [])
        assert len(all_aliases) == len(set(all_aliases)), "duplicate aliases exist"

    def test_get_by_alias_returns_same_instance(self, fresh_cli):
        for canonical, alias_list in EXPECTED_COMMANDS.items():
            canonical_cmd = fresh_cli.registry.get(canonical)
            for alias in alias_list:
                assert fresh_cli.registry.get(alias) is canonical_cmd, (
                    "alias '%s' and '%s' differ in instance" % (alias, canonical)
                )

    def test_each_command_has_name_and_description(self, fresh_cli):
        for cmd in fresh_cli.registry.get_all():
            assert cmd.name, "%s missing name" % type(cmd).__name__
            assert cmd.description, "%s missing description" % type(cmd).__name__


# ==================== argparse parsing tests ====================


class TestArgparseParsing:
    """argparse subcommand & alias parsing."""

    @pytest.mark.parametrize(
        "alias",
        [a for aliases in EXPECTED_COMMANDS.values() for a in aliases],
        ids=lambda a: "alias-%s" % a,
    )
    def test_parser_accepts_alias(self, fresh_cli, alias):
        args, _ = fresh_cli.parser.parse_known_args([alias])
        assert args.command == alias
        assert fresh_cli.registry.resolve(alias) is not None

    @pytest.mark.parametrize("canonical", list(EXPECTED_COMMANDS.keys()))
    def test_parser_accepts_canonical(self, fresh_cli, canonical):
        args, _ = fresh_cli.parser.parse_known_args([canonical])
        assert args.command == canonical

    def test_install_alias_with_flag(self, fresh_cli):
        for alias in ["i", "add", "install"]:
            args, _ = fresh_cli.parser.parse_known_args([alias, "--no-uv"])
            assert args.command == alias
            assert args.no_uv is True

    def test_global_version_flag(self, fresh_cli):
        for flag in ["--version", "-V"]:
            args, _ = fresh_cli.parser.parse_known_args([flag])
            assert args.version is True

    def test_global_verbose_flag(self, fresh_cli):
        args, _ = fresh_cli.parser.parse_known_args(["-vv"])
        assert args.verbose == 2

    def test_unknown_flag_for_install_is_kept(self, fresh_cli):
        args, unknown = fresh_cli.parser.parse_known_args(
            ["install", "--some-pip-flag"]
        )
        assert "--some-pip-flag" in unknown


# ==================== Command routing tests (mocked execute) ====================


class TestCommandRouting:
    """alias -> canonical command -> execute full routing."""

    def test_alias_routes_to_correct_command(self, fresh_cli, monkeypatch):
        calls = []

        # execute is patched as an instance attribute, so it receives only
        # `args` (no implicit self binding).
        def fake_execute(args):
            calls.append(args.command)

        for cmd in fresh_cli.registry.get_all():
            monkeypatch.setattr(cmd, "execute", fake_execute)

        monkeypatch.setattr(sys, "argv", ["epsdk", "i"])
        fresh_cli.run()

        assert calls == ["i"]  # args.command keeps the alias the user typed

    @pytest.mark.parametrize(
        "alias,canonical",
        [(a, c) for c, aliases in EXPECTED_COMMANDS.items() for a in aliases],
    )
    def test_each_alias_routes(self, fresh_cli, monkeypatch, alias, canonical):
        target_cmd = fresh_cli.registry.get(canonical)
        called = {"flag": False}

        # Each command gets its own closure so we can detect which one ran.
        def make_fake(this_cmd):
            def fake_execute(args):
                if this_cmd is target_cmd:
                    called["flag"] = True

            return fake_execute

        for cmd in fresh_cli.registry.get_all():
            monkeypatch.setattr(cmd, "execute", make_fake(cmd))

        monkeypatch.setattr(sys, "argv", ["epsdk", alias])
        fresh_cli.run()

        assert called["flag"], "alias '%s' did not route to '%s'" % (alias, canonical)

    def test_version_flag_short_circuits(self, fresh_cli, monkeypatch):
        for cmd in fresh_cli.registry.get_all():
            monkeypatch.setattr(
                cmd, "execute", lambda *a: pytest.fail("should not run")
            )

        monkeypatch.setattr(sys, "argv", ["epsdk", "--version"])
        fresh_cli.run()  # passes if no exception

    def test_no_command_prints_help(self, fresh_cli, monkeypatch):
        for cmd in fresh_cli.registry.get_all():
            monkeypatch.setattr(
                cmd, "execute", lambda *a: pytest.fail("should not run")
            )

        printed = {"help": False}
        monkeypatch.setattr(
            fresh_cli.parser, "print_help", lambda *a: printed.__setitem__("help", True)
        )
        monkeypatch.setattr(sys, "argv", ["epsdk"])
        fresh_cli.run()
        assert printed["help"]


# ==================== Alias scheme as executable documentation ====================


class TestAliasScheme:
    """Pin the full alias scheme so any change is surfaced as a test failure."""

    def test_alias_table(self, fresh_cli):
        """
        Full alias reference (any change fails this test, alerting maintainers):

            create       -> c, new
            init         -> (none)
            install      -> i, add
            uninstall    -> rm, remove
            upgrade      -> up
            self-update  -> su, update
            list         -> l, ls
            list-remote  -> lsr
            run          -> r
            i18n         -> language, lang
            types        -> t, stub
            doctor       -> diag
        """
        actual = {
            cmd.name: sorted(getattr(cmd, "aliases", []) or [])
            for cmd in fresh_cli.registry.get_all()
        }
        expected = {
            canonical: sorted(aliases)
            for canonical, aliases in EXPECTED_COMMANDS.items()
        }
        assert actual == expected


# ==================== create 模板编译验证 ====================


class TestCreateTemplatesCompile:
    """验证 create 命令的代码模板渲染后可编译（回归 BUG-028）。

    AGENTS.md 第 8 条要求修改 create.py 模板后须运行 .format() + compile()
    验证。此处以测试形式常驻，防止模板再次产出无法 import 的代码。
    """

    @staticmethod
    def _text():
        from ErisPulse.CLI.utils.scaffold_text import ScaffoldText

        return ScaffoldText("en").all()

    def test_adapter_core_renders_and_compiles(self):
        from ErisPulse.CLI.commands import create as c

        code = c._ADAPTER_CORE.format(
            name="MyAdapter",
            converter_name="MyConverter",
            entry_key="myadapter",
            text=self._text(),
        )
        compile(code, "<adapter_core>", "exec")

    def test_module_core_renders_and_compiles(self):
        from ErisPulse.CLI.commands import create as c

        code = c._MODULE_CORE.format(name="MyModule", text=self._text())
        compile(code, "<module_core>", "exec")

    def test_module_core_sdk_injection_annotation(self):
        """模块模板：sdk 纯注入 + SDK 类型注解，无 import 兜底"""
        from ErisPulse.CLI.commands import create as c

        code = c._MODULE_CORE.format(name="MyModule", text=self._text())
        assert "def __init__(self, sdk: SDK = None):" in code
        assert "from ErisPulse import SDK" in code
        assert "from ErisPulse import sdk as _sdk" not in code
        assert "_sdk if sdk is None else sdk" not in code
        # 初始化日志不再调用无效的 .format(name=...)
        assert ').format(name="MyModule")' not in code

    def test_module_core_event_annotation_and_meta_i18n(self):
        """模块模板：事件回调带 Event 注解；meta description 用 i18n 字典"""
        from ErisPulse.CLI.commands import create as c

        code = c._MODULE_CORE.format(name="MyModule", text=self._text())
        assert "from ErisPulse.Core.Event import Event" in code
        # 事件回调全部注解为 Event
        assert "async def hello_command(event: Event):" in code
        assert "async def private_message_handler(event: Event):" in code
        assert "async def group_message_handler(event: Event):" in code
        assert "async def friend_add_handler(event: Event):" in code
        # 生命周期方法保持 dict
        assert "async def on_load(self, event: dict) -> bool:" in code
        # meta description 为 i18n 字典，且 I18nClass 注册了对应键
        assert '"i18n": "module.MyModule.meta.description"' in code
        assert 'key="module.MyModule.meta.description"' in code

    def test_adapter_converter_renders_and_compiles(self):
        from ErisPulse.CLI.commands import create as c

        code = c._ADAPTER_CONVERTER.format(
            name="MyAdapter",
            converter_name="MyConverter",
            entry_key="myadapter",
            text=self._text(),
        )
        compile(code, "<adapter_converter>", "exec")

    def test_adapter_core_imports_resolve(self):
        """适配器模板引用的 Core.Bases 符号必须真实存在。"""
        import ast

        from ErisPulse.CLI.commands import create as c
        from ErisPulse.Core import Bases

        code = c._ADAPTER_CORE.format(
            name="MyAdapter",
            converter_name="MyConverter",
            entry_key="myadapter",
            text=self._text(),
        )
        tree = ast.parse(code)
        imported = {
            alias.name
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
            and node.module == "ErisPulse.Core.Bases"
            for alias in node.names
        }
        for sym in imported:
            assert hasattr(Bases, sym), f"create 模板导入了不存在的符号: {sym}"
        # I18nKeys（复数）不存在于 Core.Bases，绝不能再次出现
        assert "I18nKeys" not in imported


# ==================== 完整配置示例（config.full.example） ====================


class TestFullExampleConfig:
    """验证 init 生成的完整配置示例是合法 TOML 且覆盖框架关键配置"""

    @staticmethod
    def _example():
        import tomllib

        from ErisPulse.CLI.commands.init import InitCommand

        text = InitCommand._get_full_example_config()
        return text, tomllib.loads(text)

    def test_example_is_valid_toml(self):
        """生成的示例必须是可解析的 TOML"""
        _, data = self._example()
        assert "ErisPulse" in data

    def test_framework_section_covers_key_config(self):
        """framework 段包含懒加载/插件目录/超时/严格模式/并发/主动GC"""
        _, data = self._example()
        f = data["ErisPulse"]["framework"]
        for key in [
            "enable_lazy_loading",
            "plugins_dir",
            "uninit_timeout",
            "strict_mode",
            "strict_mode_exceptions",
            "handler_max_concurrency",
            "proactive_gc_interval",
            "offline_bot_expiry",
        ]:
            assert key in f, f"framework 配置缺少 {key}"
        assert f["strict_mode_exceptions"] == {"modules": [], "adapters": []}

    def test_uninit_timeout_documented(self):
        """uninit_timeout 出现在示例中（优雅收尾超时）"""
        text, data = self._example()
        assert "uninit_timeout" in text
        assert data["ErisPulse"]["framework"]["uninit_timeout"] == 30

    def test_no_invalid_toml_literals(self):
        """示例中不残留 TOML 非法字面量（如 null）"""
        text, _ = self._example()
        assert "= null" not in text

    def test_ssl_defaults_to_config_ssl_dir(self):
        """SSL 证书默认放 config/ssl/（相对路径跟随项目运行目录）"""
        _, data = self._example()
        server = data["ErisPulse"]["server"]
        assert server["ssl_certfile"] == "config/ssl/cert.pem"
        assert server["ssl_keyfile"] == "config/ssl/key.pem"


# ==================== 跨进程契约常量 ====================


class TestCrossProcessContracts:
    """钉住跨模块/跨进程共享的契约常量，防止两侧各自漂移。"""

    def test_hard_restart_exit_code_is_shared(self):
        """硬重启退出码：sdk.py 与 CLI run.py 必须引用同一常量（BUG 历史 H1）"""
        from ErisPulse.CLI.commands.run import RunCommand
        from ErisPulse.Core.constants import HARD_RESTART_EXIT_CODE
        from ErisPulse.sdk import sdk

        assert HARD_RESTART_EXIT_CODE == 42
        # 两侧必须与同一个常量值相等，避免硬重启被误判为崩溃
        assert sdk.RESTART_EXIT_CODE == HARD_RESTART_EXIT_CODE
        assert RunCommand._RESTART_EXIT_CODE == HARD_RESTART_EXIT_CODE

    def test_entry_point_groups_are_shared(self):
        """入口点组名：CLI 与主库镜像必须一致（loader/finder/create/types 共用）"""
        from ErisPulse.CLI.constants import (
            ADAPTER_ENTRY_POINT_GROUP as CLI_ADAPTER,
            MODULE_ENTRY_POINT_GROUP as CLI_MODULE,
        )
        from ErisPulse.Core.constants import (
            ADAPTER_ENTRY_POINT_GROUP as CORE_ADAPTER,
            MODULE_ENTRY_POINT_GROUP as CORE_MODULE,
        )

        assert CLI_MODULE == CORE_MODULE == "erispulse.module"
        assert CLI_ADAPTER == CORE_ADAPTER == "erispulse.adapter"

    def test_env_supervised_is_shared(self):
        """监督者标记环境变量：CLI run 注入 与 SDK 检测必须一致"""
        from ErisPulse.CLI.constants import ENV_SUPERVISED as CLI_ENV
        from ErisPulse.Core.constants import ENV_SUPERVISED as CORE_ENV

        assert CLI_ENV == CORE_ENV == "ERISPULSE_SUPERVISED"


# ==================== 运行器子进程清理 ====================


class TestRunInternalChildCleanup:
    """`ep run` 运行器退出时必须终止子进程，避免孤儿进程残留并占用端口等资源"""

    def _fake_process(self, *, running: bool = True):
        from unittest.mock import Mock

        fake = Mock()
        # 第一次 wait 抛 KeyboardInterrupt（模拟 Ctrl+C 中断 process.wait()），
        # 第二次 wait 正常返回（finally 清理路径中的 process.wait(timeout=5)）
        fake.wait = Mock(side_effect=[KeyboardInterrupt(), None])
        fake.poll = Mock(return_value=None if running else 0)
        fake.terminate = Mock()
        fake.kill = Mock()
        return fake

    def test_child_terminated_on_keyboard_interrupt(self):
        from unittest.mock import patch

        from ErisPulse.CLI.commands.run import RunCommand

        fake = self._fake_process(running=True)
        with patch("subprocess.Popen", return_value=fake):
            RunCommand()._run_internal(False)

        # 运行器退出时必须终止仍在运行的子进程（防孤儿占用端口）
        fake.terminate.assert_called_once()
        # 正常 terminate 成功，不应走到强杀
        fake.kill.assert_not_called()

    def test_exited_child_not_terminated(self):
        from unittest.mock import patch

        from ErisPulse.CLI.commands.run import RunCommand

        fake = self._fake_process(running=False)
        with patch("subprocess.Popen", return_value=fake):
            RunCommand()._run_internal(False)

        # 子进程已退出，无需 terminate
        fake.terminate.assert_not_called()


class TestCreateModuleLocal:
    """create module --local 生成本地插件结构"""

    def test_local_module_layout(self, tmp_path, monkeypatch, capsys):
        """--local 生成 plugins/<name>/ 包结构，无 pyproject.toml"""
        monkeypatch.chdir(tmp_path)

        from ErisPulse.CLI.commands.create import CreateCommand

        class Args:
            local = True
            name = "Dice"
            description = "dice plugin"
            author = ""
            email = ""
            homepage = ""
            output = "."
            force = False

        CreateCommand()._create_module(Args(), "Dice")

        plugins = tmp_path / "plugins"
        assert (plugins / "Dice" / "__init__.py").is_file()
        assert (plugins / "Dice" / "Core.py").is_file()
        assert not (plugins / "Dice" / "pyproject.toml").exists()

        core = (plugins / "Dice" / "Core.py").read_text(encoding="utf-8")
        assert "class Main(BaseModule)" in core
        assert "get_meta() -> ModuleMeta" in core

    def test_local_module_discoverable(self, tmp_path, monkeypatch):
        """生成的本地插件可被 PluginFolderLoader 发现"""
        monkeypatch.chdir(tmp_path)
        # 包形式插件经 import_module 导入，需将插件父目录加入 sys.path
        monkeypatch.syspath_prepend(str(tmp_path))
        sys.modules.pop("Dice", None)

        from ErisPulse.CLI.commands.create import CreateCommand

        class Args:
            local = True
            name = "Dice"
            description = "dice plugin"
            author = ""
            email = ""
            homepage = ""
            output = "."
            force = False

        CreateCommand()._create_module(Args(), "Dice")

        from ErisPulse.loaders.plugin_folder import PluginFolderLoader

        results = PluginFolderLoader().discover()
        assert "Dice" in results
        meta = results["Dice"].moduleInfo["meta"]
        assert meta["source"] == "plugin_folder"
        assert meta["is_base_module"] is True
