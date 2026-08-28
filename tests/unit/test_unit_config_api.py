"""
CLI 配置向导单元测试

覆盖 config_wizard 的字段渲染（含来源标注）、账户管理、写入流程
（含放弃中止）、目标状态检查、`epsdk config` 命令路由与安装后
衔接逻辑。

Run via:

    pytest tests/unit/test_unit_config_api.py -v
"""

from dataclasses import dataclass, field
from types import SimpleNamespace
from unittest.mock import MagicMock, Mock

import pytest

from ErisPulse.Core.Bases import BaseConfig, BotAccountConfig

# ==================== 测试用配置声明 ====================


@dataclass
class FakeGlobalConfig(BaseConfig):
    token: str = field(default="", metadata={"required": True})
    mode: str = field(default="server")


@dataclass
class FakeAccountConfig(BotAccountConfig):
    bot_id: str = field(default="", metadata={"required": True})
    bot_token: str = field(default="", metadata={"required": True})


def _make_fake_config(store: dict | None = None) -> MagicMock:
    """构造 getConfig/setConfig 基于内存字典的伪配置管理器"""
    store = {} if store is None else store
    fake = MagicMock()

    def get_config(key, default=None):
        return store.get(key, default)

    fake.getConfig.side_effect = get_config
    fake.setConfig.side_effect = lambda key, value, immediate=False: store.__setitem__(key, value)
    fake.CONFIG_FILE = "config/config.toml"
    return fake


# ==================== config_wizard 工具函数测试 ====================


class TestWizardHelpers:
    """config_wizard 纯函数测试"""

    def test_normalize_dist_name(self):
        from ErisPulse.CLI.utils.config_wizard import _normalize_dist_name

        assert _normalize_dist_name("ErisPulse.Yunhu_Adapter") == "erispulse-yunhu-adapter"
        assert _normalize_dist_name("yunhu") == "yunhu"
        assert _normalize_dist_name(None) == ""

    def test_fill_fields_has_value_by_presence(self, monkeypatch):
        """fill_config_fields 按存储中是否包含该字段计算 has_value"""
        from ErisPulse.CLI.utils import config_wizard

        calls = {}

        def fake_prompt(name, field_schema, current, has_value=False):
            calls[name] = (current, has_value)
            return current

        monkeypatch.setattr(config_wizard, "_prompt_field", fake_prompt)
        values = config_wizard.fill_config_fields(FakeAccountConfig, {"bot_id": "1"})

        assert values["bot_id"] == "1"
        # bot_id 存在于存储 → 标注"当前"
        assert calls["bot_id"] == ("1", True)
        # bot_token 不在存储 → schema default 兜底并标注"默认"
        assert calls["bot_token"][1] is False

    def test_coerce_scalar(self):
        from ErisPulse.CLI.utils.config_wizard import _coerce_scalar

        assert _coerce_scalar("42", "integer") == 42
        assert _coerce_scalar("3.5", "float") == 3.5
        assert _coerce_scalar("yes", "boolean") is True
        assert _coerce_scalar("abc", "string") == "abc"
        with pytest.raises(ValueError):
            _coerce_scalar("x", "integer")

    def test_sort_fields_by_order(self):
        from ErisPulse.CLI.utils.config_wizard import _sort_fields

        fields = {
            "a": {"order": 2},
            "b": {"order": 1},
            "c": {},
        }
        result = [name for name, _ in _sort_fields(fields)]
        # b(order=1) → a(order=2) → c(无 order 垫底)
        assert result == ["b", "a", "c"]

    def test_plain_options_and_label(self):
        from ErisPulse.CLI.utils.config_wizard import _option_label, _plain_options

        options = ["server", {"label": "客户端", "value": "client"}]
        assert _plain_options(options) == ["server", "client"]
        assert _option_label(options[0]) == "server"
        assert _option_label(options[1]) == "客户端 (client)"


class TestPromptField:
    """_prompt_field 控件渲染测试（mock rich Prompt/Confirm）"""

    def test_boolean_field_uses_confirm(self, monkeypatch):
        from ErisPulse.CLI.utils import config_wizard

        ask = Mock(return_value=False)
        monkeypatch.setattr(config_wizard.Confirm, "ask", ask)
        result = config_wizard._prompt_field("enabled", {"type": "boolean", "required": False}, True)
        assert result is False
        ask.assert_called_once()
        # prompt 用字段名（"是否启用 enabled？"），避免与 label 描述重复
        assert "enabled" in ask.call_args[0][0]

    def test_boolean_field_source_label(self):
        """布尔字段 prompt 含来源标注，且无占位符残留"""
        from ErisPulse.CLI.utils.config_wizard import _source_label

        text = _source_label(True, "", "yes-text")
        assert "yes-text" in text
        assert "{value}" not in text

    def test_text_field_current_source(self):
        """已有配置值的文本字段"当前"标注含值且无占位符残留"""
        from ErisPulse.CLI.utils.config_wizard import _source_label

        text = _source_label(True, "https://x")
        assert "https://x" in text
        assert "{value}" not in text

    def test_text_field_default_source(self):
        """无已有值的文本字段"默认"标注含值且无占位符残留"""
        from ErisPulse.CLI.utils.config_wizard import _source_label

        text = _source_label(False, "server")
        assert "server" in text
        assert "{value}" not in text


class TestPickAccountName:
    """_pick_account_name 账户选择测试"""

    def test_empty_input_returns_none(self, monkeypatch):
        from ErisPulse.CLI.utils import config_wizard

        monkeypatch.setattr(config_wizard.Prompt, "ask", Mock(return_value=""))
        assert config_wizard._pick_account_name(["bot1", "bot2"]) is None

    def test_index_selects_account(self, monkeypatch):
        from ErisPulse.CLI.utils import config_wizard

        monkeypatch.setattr(config_wizard.Prompt, "ask", Mock(return_value="2"))
        assert config_wizard._pick_account_name(["bot1", "bot2"]) == "bot2"

    def test_invalid_index_reasks(self, monkeypatch):
        from ErisPulse.CLI.utils import config_wizard

        monkeypatch.setattr(config_wizard.Prompt, "ask", Mock(side_effect=["abc", "9", "1"]))
        assert config_wizard._pick_account_name(["bot1"]) == "bot1"

    def test_prompt_has_no_empty_default_parens(self, monkeypatch):
        from ErisPulse.CLI.utils import config_wizard

        ask = Mock(return_value="1")
        monkeypatch.setattr(config_wizard.Prompt, "ask", ask)
        config_wizard._pick_account_name(["bot1"])
        assert ask.call_args.kwargs.get("show_default") is False


class TestPromptAccountName:
    """_prompt_account_name 测试"""

    def test_empty_input_cancels(self, monkeypatch):
        """空输入视为取消新增，返回 None 而非循环报错"""
        from ErisPulse.CLI.utils import config_wizard

        ask = Mock(return_value="")
        monkeypatch.setattr(config_wizard.Prompt, "ask", ask)
        assert config_wizard._prompt_account_name({}) is None

    def test_valid_name(self, monkeypatch):
        from ErisPulse.CLI.utils import config_wizard

        monkeypatch.setattr(config_wizard.Prompt, "ask", Mock(return_value="bot1"))
        assert config_wizard._prompt_account_name({}) == "bot1"

    def test_duplicate_rejected(self, monkeypatch):
        from ErisPulse.CLI.utils import config_wizard

        monkeypatch.setattr(config_wizard.Prompt, "ask", Mock(side_effect=["bot1", "bot2"]))
        assert config_wizard._prompt_account_name({"bot1": {}}) == "bot2"

    def test_prompt_has_no_empty_default_parens(self, monkeypatch):
        from ErisPulse.CLI.utils import config_wizard

        ask = Mock(return_value="bot1")
        monkeypatch.setattr(config_wizard.Prompt, "ask", ask)
        config_wizard._prompt_account_name({})
        assert ask.call_args.kwargs.get("show_default") is False


class TestGetTargetStatus:
    """get_target_status 状态检查测试"""

    def test_none_declaration(self):
        from ErisPulse.CLI.utils.config_wizard import (
            STATUS_NONE,
            ConfigTarget,
            get_target_status,
        )

        target = ConfigTarget("adapter", "A", config_class=None, account_class=None)
        status, errors = get_target_status(target, _make_fake_config())
        assert status == STATUS_NONE
        assert errors == []

    def test_unconfigured_when_key_missing(self):
        from ErisPulse.CLI.utils.config_wizard import (
            STATUS_UNCONFIGURED,
            ConfigTarget,
            get_target_status,
        )

        target = ConfigTarget("adapter", "A", config_class=FakeGlobalConfig)
        status, _ = get_target_status(target, _make_fake_config())
        assert status == STATUS_UNCONFIGURED

    def test_ok_when_valid(self):
        from ErisPulse.CLI.utils.config_wizard import (
            STATUS_OK,
            ConfigTarget,
            get_target_status,
        )

        target = ConfigTarget(
            "adapter",
            "A",
            config_class=FakeGlobalConfig,
            account_class=FakeAccountConfig,
            config_key="A",
        )
        store = {
            "A": {"token": "t", "mode": "server"},
            "A.accounts": {"bot1": {"bot_id": "1", "bot_token": "t1", "enabled": True, "name": ""}},
        }
        status, errors = get_target_status(target, _make_fake_config(store))
        assert status == STATUS_OK
        assert errors == []

    def test_incomplete_when_required_missing(self):
        from ErisPulse.CLI.utils.config_wizard import (
            STATUS_INCOMPLETE,
            ConfigTarget,
            get_target_status,
        )

        target = ConfigTarget("module", "M", config_class=FakeGlobalConfig)
        store = {"M": {"token": "", "mode": "server"}}
        status, errors = get_target_status(target, _make_fake_config(store))
        assert status == STATUS_INCOMPLETE
        assert errors

    def test_incomplete_when_no_accounts(self):
        from ErisPulse.CLI.utils.config_wizard import (
            STATUS_INCOMPLETE,
            ConfigTarget,
            get_target_status,
        )

        target = ConfigTarget("adapter", "A", config_class=None, account_class=FakeAccountConfig)
        store = {"A.accounts": {}}
        status, _ = get_target_status(target, _make_fake_config(store))
        assert status == STATUS_INCOMPLETE


# ==================== 安装后衔接测试 ====================


class TestPostInstallConfigure:
    """post_install_configure 测试"""

    def test_empty_names_noop(self):
        from ErisPulse.CLI.utils import config_wizard

        # 不应触发任何发现
        config_wizard.post_install_configure([], interactive=True)

    def test_non_interactive_skips(self, monkeypatch):
        from ErisPulse.CLI.utils import config_wizard

        discover = Mock()
        monkeypatch.setattr(config_wizard, "load_config_targets", discover)
        config_wizard.post_install_configure(["pkg"], interactive=False)
        discover.assert_not_called()

    def test_matches_normalized_dist_names(self, monkeypatch):
        from ErisPulse.CLI.utils import config_wizard

        target = config_wizard.ConfigTarget(
            "adapter",
            "YunhuAdapter",
            config_class=FakeGlobalConfig,
            package="ErisPulse_Yunhu.Adapter",
        )
        monkeypatch.setattr(config_wizard, "load_config_targets", Mock(return_value=[target]))
        monkeypatch.setattr(config_wizard.Confirm, "ask", Mock(return_value=False))
        run_wizard = Mock()
        monkeypatch.setattr(config_wizard, "run_wizard", run_wizard)

        config_wizard.post_install_configure(["erispulse-yunhu.adapter"], interactive=True)

        # 匹配到目标但用户拒绝 → 不进入向导
        run_wizard.assert_not_called()

    def test_invokes_wizard_on_confirm(self, monkeypatch):
        from ErisPulse.CLI.utils import config_wizard

        target = config_wizard.ConfigTarget("module", "MyModule", config_class=FakeGlobalConfig, package="MyModule")
        monkeypatch.setattr(config_wizard, "load_config_targets", Mock(return_value=[target]))
        monkeypatch.setattr(config_wizard.Confirm, "ask", Mock(return_value=True))
        run_wizard = Mock(return_value=True)
        monkeypatch.setattr(config_wizard, "run_wizard", run_wizard)

        config_wizard.post_install_configure(["MyModule"], interactive=True)

        run_wizard.assert_called_once()
        assert run_wizard.call_args[0][0] is target

    def test_no_configurable_match_skips(self, monkeypatch):
        from ErisPulse.CLI.utils import config_wizard

        target = config_wizard.ConfigTarget("adapter", "A", config_class=None, account_class=None, package="pkg-a")
        confirm = Mock()
        monkeypatch.setattr(config_wizard, "load_config_targets", Mock(return_value=[target]))
        monkeypatch.setattr(config_wizard.Confirm, "ask", confirm)

        config_wizard.post_install_configure(["pkg-a"], interactive=True)
        confirm.assert_not_called()


# ==================== run_wizard 集成测试 ====================


class TestRunWizard:
    """run_wizard 写入流程测试（mock 表单交互）"""

    def test_adapter_wizard_writes_config_and_accounts(self, monkeypatch):
        from ErisPulse.CLI.utils import config_wizard

        target = config_wizard.ConfigTarget(
            "adapter",
            "MyAdapter",
            config_class=FakeGlobalConfig,
            account_class=FakeAccountConfig,
            config_key="MyAdapter",
        )
        fake_config = _make_fake_config()

        monkeypatch.setattr(
            config_wizard,
            "fill_config_fields",
            Mock(return_value={"token": "t", "mode": "client"}),
        )
        monkeypatch.setattr(
            config_wizard,
            "_run_accounts_section",
            Mock(return_value={"bot1": {"bot_id": "1", "bot_token": "t1", "enabled": True, "name": "bot1"}}),
        )
        monkeypatch.setattr(config_wizard.Confirm, "ask", Mock(return_value=True))

        assert config_wizard.run_wizard(target, fake_config) is True

        assert fake_config.getConfig("MyAdapter")["token"] == "t"
        assert fake_config.getConfig("MyAdapter.accounts")["bot1"]["bot_token"] == "t1"
        assert fake_config.getConfig("ErisPulse.adapters.status.MyAdapter") is True

    def test_module_wizard_writes_config(self, monkeypatch):
        from ErisPulse.CLI.utils import config_wizard

        target = config_wizard.ConfigTarget("module", "MyModule", config_class=FakeGlobalConfig)
        fake_config = _make_fake_config()

        monkeypatch.setattr(
            config_wizard,
            "fill_config_fields",
            Mock(return_value={"token": "t", "mode": "server"}),
        )

        assert config_wizard.run_wizard(target, fake_config) is True
        assert fake_config.getConfig("MyModule")["token"] == "t"

    def test_no_declaration_returns_false(self):
        from ErisPulse.CLI.utils import config_wizard

        target = config_wizard.ConfigTarget("module", "M", config_class=None, account_class=None)
        assert config_wizard.run_wizard(target, _make_fake_config()) is False

    def test_validation_abandon_aborts_without_writing(self, monkeypatch):
        """校验失败且放弃重填：中止整个向导，不写入任何配置"""
        from ErisPulse.CLI.utils import config_wizard

        target = config_wizard.ConfigTarget("module", "MyModule", config_class=FakeGlobalConfig)
        fake_config = _make_fake_config()

        monkeypatch.setattr(config_wizard, "get_target_status", Mock(return_value=("unconfigured", [])))
        monkeypatch.setattr(
            config_wizard,
            "fill_config_fields",
            Mock(return_value={"token": "", "mode": "server"}),  # token 必填为空 → 校验失败
        )
        monkeypatch.setattr(config_wizard.Confirm, "ask", Mock(return_value=False))  # 放弃重填

        assert config_wizard.run_wizard(target, fake_config) is False
        fake_config.setConfig.assert_not_called()

    def test_ready_target_prints_hint_and_summary(self, monkeypatch):
        """已就绪目标：打印就绪提示；成功提示合并为一条（无逐键 saved_key）"""
        from ErisPulse.CLI.i18n import i18n as cli_i18n
        from ErisPulse.CLI.utils import config_wizard

        printed = []
        monkeypatch.setattr(
            config_wizard.console, "print", lambda *a, **k: printed.append(str(a[0]) if a else "")
        )
        monkeypatch.setattr(config_wizard, "get_target_status", Mock(return_value=("ok", [])))
        monkeypatch.setattr(
            config_wizard,
            "fill_config_fields",
            Mock(return_value={"token": "t", "mode": "client"}),
        )
        monkeypatch.setattr(config_wizard, "Confirm", MagicMock(ask=Mock(return_value=True)))

        target = config_wizard.ConfigTarget("module", "MyModule", config_class=FakeGlobalConfig)
        assert config_wizard.run_wizard(target, _make_fake_config()) is True

        combined = "\n".join(printed)
        # 就绪提示（语言无关：以翻译文本比对）
        assert cli_i18n.t("cli.config.ready_hint") in combined
        # 汇总键列表提示存在（而非逐键"已写入配置键"）
        assert cli_i18n.t("cli.config.saved_keys_header") in combined

    def test_wizard_syncs_core_i18n_language(self, monkeypatch):
        """run_wizard 开头的 core_i18n.set_language 以 persist=False 调用"""
        from ErisPulse.CLI.utils import config_wizard

        set_lang = Mock()
        monkeypatch.setattr(config_wizard._core_i18n, "set_language", set_lang)
        monkeypatch.setattr(config_wizard, "get_target_status", Mock(return_value=("unconfigured", [])))
        monkeypatch.setattr(
            config_wizard,
            "fill_config_fields",
            Mock(return_value={"token": "t", "mode": "client"}),
        )

        target = config_wizard.ConfigTarget("module", "MyModule", config_class=FakeGlobalConfig)
        config_wizard.run_wizard(target, _make_fake_config())
        set_lang.assert_called_once()
        assert set_lang.call_args.kwargs.get("persist") is False


class TestSetLanguagePersist:
    """Core i18n.set_language 的 persist 参数行为测试"""

    def test_persist_true_by_default(self, monkeypatch):
        from ErisPulse.CLI.utils.config_wizard import _core_i18n

        persist = Mock()
        monkeypatch.setattr(_core_i18n, "_persist_global_language", persist)
        _core_i18n.set_language("en")
        persist.assert_called_once()

    def test_persist_false_skips_persist(self, monkeypatch):
        from ErisPulse.CLI.utils.config_wizard import _core_i18n

        persist = Mock()
        monkeypatch.setattr(_core_i18n, "_persist_global_language", persist)
        _core_i18n.set_language("en", persist=False)
        persist.assert_not_called()
        assert _core_i18n.get_language() == "en"


# ==================== ConfigCommand 测试 ====================


class TestConfigCommand:
    """epsdk config 命令测试"""

    @pytest.fixture
    def command(self):
        from ErisPulse.CLI.commands.config import ConfigCommand

        return ConfigCommand()

    def test_no_targets_prints_hint(self, command, monkeypatch):
        from ErisPulse.CLI.utils import config_wizard

        printed = []
        monkeypatch.setattr(config_wizard, "load_config_targets", Mock(return_value=[]))
        monkeypatch.setattr(
            "ErisPulse.CLI.commands.config.console",
            MagicMock(print=lambda *a, **k: printed.append(a)),
        )

        args = SimpleNamespace(name=None, list=False)
        command.execute(args)
        assert printed

    def test_named_target_runs_wizard(self, command, monkeypatch):
        from ErisPulse.CLI.utils import config_wizard

        target = config_wizard.ConfigTarget("adapter", "MyAdapter", config_class=FakeGlobalConfig)
        run_wizard = Mock(return_value=True)
        monkeypatch.setattr(config_wizard, "load_config_targets", Mock(return_value=[target]))
        monkeypatch.setattr(config_wizard, "run_wizard", run_wizard)

        args = SimpleNamespace(name="MyAdapter", list=False)
        command.execute(args)
        run_wizard.assert_called_once()

    def test_named_target_by_config_key(self, command, monkeypatch):
        from ErisPulse.CLI.utils import config_wizard

        target = config_wizard.ConfigTarget(
            "adapter", "yunhu", config_class=FakeGlobalConfig, config_key="YunhuAdapter"
        )
        run_wizard = Mock(return_value=True)
        monkeypatch.setattr(config_wizard, "load_config_targets", Mock(return_value=[target]))
        monkeypatch.setattr(config_wizard, "run_wizard", run_wizard)

        args = SimpleNamespace(name="YunhuAdapter", list=False)
        command.execute(args)
        run_wizard.assert_called_once()

    def test_named_target_not_found(self, command, monkeypatch):
        from ErisPulse.CLI.utils import config_wizard

        target = config_wizard.ConfigTarget("adapter", "MyAdapter", config_class=FakeGlobalConfig)
        run_wizard = Mock()
        monkeypatch.setattr(config_wizard, "load_config_targets", Mock(return_value=[target]))
        monkeypatch.setattr(config_wizard, "run_wizard", run_wizard)

        args = SimpleNamespace(name="ghost", list=False)
        command.execute(args)
        run_wizard.assert_not_called()

    def test_list_flag_skips_interactive(self, command, monkeypatch):
        from ErisPulse.CLI.utils import config_wizard

        target = config_wizard.ConfigTarget("module", "MyModule", config_class=FakeGlobalConfig)
        monkeypatch.setattr(config_wizard, "load_config_targets", Mock(return_value=[target]))
        monkeypatch.setattr(config_wizard, "is_interactive", Mock(return_value=True))
        select = Mock()
        monkeypatch.setattr("ErisPulse.CLI.commands.config.ConfigCommand._interactive_select", select)

        args = SimpleNamespace(name=None, list=True)
        command.execute(args)
        select.assert_not_called()

    def test_interactive_select_prompt_no_empty_default_parens(self, command, monkeypatch):
        """交互选择序号提示无空默认值括号（show_default=False）"""
        import ErisPulse.CLI.commands.config as config_mod
        from ErisPulse.CLI.utils import config_wizard

        target = config_wizard.ConfigTarget("adapter", "MyAdapter", config_class=FakeGlobalConfig)
        ask = Mock(return_value="")
        monkeypatch.setattr(config_mod.Prompt, "ask", ask)
        monkeypatch.setattr(config_wizard, "get_target_status", Mock(return_value=("ok", [])))
        monkeypatch.setattr(config_wizard, "run_wizard", Mock())

        command._interactive_select([target], _make_fake_config())
        assert ask.call_args.kwargs.get("show_default") is False

    def test_interactive_select_loops_after_wizard(self, command, monkeypatch):
        """向导结束后回到选择菜单，支持连续配置多个目标"""
        import ErisPulse.CLI.commands.config as config_mod
        from ErisPulse.CLI.utils import config_wizard

        target = config_wizard.ConfigTarget("adapter", "MyAdapter", config_class=FakeGlobalConfig)
        run_wizard = Mock(return_value=True)
        monkeypatch.setattr(config_wizard, "run_wizard", run_wizard)
        monkeypatch.setattr(config_wizard, "get_target_status", Mock(return_value=("ok", [])))
        # 第一次选择 1 号目标，向导结束后再次询问，空输入退出
        monkeypatch.setattr(config_mod.Prompt, "ask", Mock(side_effect=["1", ""]))

        command._interactive_select([target], _make_fake_config())
        run_wizard.assert_called_once()
        assert run_wizard.call_args[0][0] is target


class TestCliI18nKeys:
    """CLI 向导 i18n 占位符插值回归测试"""

    def test_value_source_interpolates(self):
        """value_current / value_default 占位符 {value} 正确插值"""
        from ErisPulse.CLI.i18n import i18n

        assert "abc" in i18n.t("cli.config.value_current", value="abc")
        assert "abc" in i18n.t("cli.config.value_default", value="abc")
        assert "{value}" not in i18n.t("cli.config.value_current", value="abc")

    def test_ready_hint_and_keys_header(self):
        """ready_hint / saved_keys_header 可直接渲染且无占位符残留"""
        from ErisPulse.CLI.i18n import i18n

        for key in ("cli.config.ready_hint", "cli.config.saved_keys_header"):
            text = i18n.t(key)
            assert not text.startswith("cli.config")

    def test_yn_yes_no(self):
        from ErisPulse.CLI.i18n import i18n

        assert i18n.t("cli.config.yn_yes")
        assert i18n.t("cli.config.yn_no")
