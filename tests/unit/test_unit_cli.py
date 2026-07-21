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
