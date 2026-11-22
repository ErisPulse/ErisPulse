"""
runtime/frame_config 单元测试

覆盖环境变量覆盖（Docker/12-factor）、默认值补全与 set_erispulse_section 整节替换写入。
"""

import os
from unittest.mock import MagicMock, patch

import pytest

from ErisPulse.runtime.frame_config import (
    _apply_env_overrides,
    _coerce_env_value,
    get_config,
    set_erispulse_section,
    update_erispulse_config,
)


class TestEnvOverride:
    """环境变量覆盖测试"""

    @pytest.fixture(autouse=True)
    def _clean_env(self, monkeypatch):
        # 清理可能残留的 ERISPULSE_* 环境变量
        for k in list(os.environ):
            if k.startswith("ERISPULSE_"):
                monkeypatch.delenv(k, raising=False)
        yield

    def test_coerce_bool(self):
        assert _coerce_env_value(True, "false") is False
        assert _coerce_env_value(False, "true") is True
        assert _coerce_env_value(True, "0") is False
        assert _coerce_env_value(True, "yes") is True

    def test_coerce_int(self):
        assert _coerce_env_value(8080, "9999") == 9999
        assert isinstance(_coerce_env_value(8080, "9999"), int)

    def test_coerce_int_invalid_falls_back_to_str(self):
        assert _coerce_env_value(8080, "abc") == "abc"

    def test_coerce_float(self):
        assert _coerce_env_value(1.5, "2.5") == 2.5

    def test_coerce_list(self):
        assert _coerce_env_value(["a"], "x, y ,z") == ["x", "y", "z"]
        assert _coerce_env_value([], "") == []

    def test_coerce_str(self):
        assert _coerce_env_value("hello", "world") == "world"

    def test_apply_env_overrides_leaf(self, monkeypatch):
        monkeypatch.setenv("ERISPULSE_SERVER_PORT", "7777")
        cfg = {"server": {"port": 8080, "host": "0.0.0.0"}, "logger": {"level": "INFO"}}
        _apply_env_overrides(cfg, "ErisPulse")
        assert cfg["server"]["port"] == 7777
        assert cfg["server"]["host"] == "0.0.0.0"  # 未覆盖保持原值
        assert cfg["logger"]["level"] == "INFO"

    def test_apply_env_overrides_nested(self, monkeypatch):
        monkeypatch.setenv("ERISPULSE_LOGGER_LEVEL", "DEBUG")
        cfg = {"logger": {"level": "INFO"}}
        _apply_env_overrides(cfg, "ErisPulse")
        assert cfg["logger"]["level"] == "DEBUG"

    def test_get_config_env_override(self, monkeypatch):
        """端到端：get_config 返回的值受环境变量覆盖"""
        monkeypatch.setenv("ERISPULSE_SERVER_PORT", "12345")
        server_cfg = get_config("server")
        assert server_cfg["port"] == 12345


class TestSetErispulseSection:
    """set_erispulse_section 整节替换写入（2.8.0 新增 API）"""

    def test_path_joining_single_level(self):
        """单级路径拼接 CONFIG_ROOT_KEY 前缀后单键写入"""
        svc = MagicMock()
        svc.setConfig.return_value = True
        with patch(
            "ErisPulse.runtime.frame_config._get_config_service", return_value=svc
        ):
            ok = set_erispulse_section("master", {"users": {}})
        assert ok is True
        svc.setConfig.assert_called_once_with("ErisPulse.master", {"users": {}})

    def test_path_joining_multi_level(self):
        """多级路径整节写入，value 原样透传不深合并"""
        svc = MagicMock()
        acl = {"roll*": {"allow": ["onebot11:123"]}}
        with patch(
            "ErisPulse.runtime.frame_config._get_config_service", return_value=svc
        ):
            set_erispulse_section("scope.commands", acl)
        svc.setConfig.assert_called_once_with("ErisPulse.scope.commands", acl)

    def test_return_value_passthrough(self):
        """setConfig 失败（False）时返回值透传"""
        svc = MagicMock()
        svc.setConfig.return_value = False
        with patch(
            "ErisPulse.runtime.frame_config._get_config_service", return_value=svc
        ):
            assert set_erispulse_section("scope", {}) is False

    def test_section_replace_expresses_key_deletion(self):
        """整节替换可表达子键删除：写入不含旧子键的新节，旧子键即被移除"""
        svc = MagicMock()
        with patch(
            "ErisPulse.runtime.frame_config._get_config_service", return_value=svc
        ):
            # 原节有 deny，新节不含 deny → 整节覆盖后 deny 消失（unbind/解绑场景）
            set_erispulse_section(
                "scope.commands", {"roll": {"allow": ["a"]}}
            )
        _, value = svc.setConfig.call_args[0]
        assert "deny" not in value["roll"]

    def test_update_deep_merge_keeps_absent_keys(self):
        """对比：update_erispulse_config 深合并按叶子写入，未提及的子键不受影响"""
        svc = MagicMock()
        svc.getConfig.return_value = {
            "scope": {"commands": {"roll": {"allow": ["a"], "deny": ["b"]}}}
        }
        with patch(
            "ErisPulse.runtime.frame_config._get_config_service", return_value=svc
        ):
            update_erispulse_config(
                {"scope": {"commands": {"roll": {"allow": ["a2"]}}}}
            )
        paths = [c.args[0] for c in svc.setConfig.call_args_list]
        # 只有变化的叶子被写入；deny 未提及 → 无 deny 路径的写入（不会被删除）
        assert "ErisPulse.scope.commands.roll.allow" in paths
        assert "ErisPulse.scope.commands.roll.deny" not in paths

    def test_update_no_change_writes_nothing(self):
        """对比：update 对无变化的配置零写入"""
        svc = MagicMock()
        svc.getConfig.return_value = {"scope": {"commands": {"roll": {"allow": ["a"]}}}}
        with patch(
            "ErisPulse.runtime.frame_config._get_config_service", return_value=svc
        ):
            update_erispulse_config(
                {"scope": {"commands": {"roll": {"allow": ["a"]}}}}
            )
        scope_paths = [
            p
            for p in (c.args[0] for c in svc.setConfig.call_args_list)
            if p.startswith("ErisPulse.scope.commands")
        ]
        assert scope_paths == []


class TestFrameworkDeclaration:
    """framework 节声明折叠（B1-2：唯一真相源 + 立即生效型调优键）"""

    EXPECTED_KEYS = {
        "enable_lazy_loading", "plugins_dir", "uninit_timeout", "strict_mode",
        "strict_mode_exceptions", "handler_max_concurrency", "handler_queue_max_pending",
        "proactive_gc_interval", "proactive_gc_generation", "proactive_gc_full_every",
        "proactive_gc_memory_growth_mb", "proactive_gc_idle_only", "proactive_gc_gen0_min",
        "offline_bot_expiry", "watch_ignore_dirs", "event_dedupe", "memory_tracing",
        "cross_account_policy", "session_accounts", "watch_include_plugin_dirs",
        "txn_begin_timeout", "txn_commit_timeout", "txn_slow_warn", "sync_warn_cooldown",
        "cross_receipt_window", "handler_slow_threshold",
    }

    def test_declaration_covers_full_key_set(self):
        """声明折叠键集合 == 手写字面量时代键集合（防漂移/防丢键）"""
        from ErisPulse.runtime.frame_config import DEFAULT_ERISPULSE_CONFIG
        from ErisPulse.runtime.frame_config_schema import framework_defaults

        folded = framework_defaults()
        assert set(folded) == self.EXPECTED_KEYS
        # 导入期占位空表 + 快照/ensure 路径补填
        assert DEFAULT_ERISPULSE_CONFIG["framework"] == {}

    def test_nested_section_folded(self):
        from ErisPulse.runtime.frame_config_schema import framework_defaults

        nested = framework_defaults()["strict_mode_exceptions"]
        assert nested == {"modules": [], "adapters": []}

    def test_tuning_defaults_come_from_constants(self):
        from ErisPulse.Core.constants import STORAGE_TXN_BEGIN_TIMEOUT_SECS
        from ErisPulse.runtime.frame_config_schema import framework_defaults

        assert framework_defaults()["txn_begin_timeout"] == STORAGE_TXN_BEGIN_TIMEOUT_SECS

    def test_get_framework_value_reads_user_config_over_defaults(self, monkeypatch, tmp_path):
        """用户配置 > 声明默认值；写后即时生效（合并快照失效链路）"""
        from ErisPulse.runtime.frame_config import get_framework_value

        assert get_framework_value("txn_slow_warn", 9.0) == 1.0
        from ErisPulse.Core.config import config

        config.setConfig("ErisPulse.framework.txn_slow_warn", 2.5)
        try:
            assert get_framework_value("txn_slow_warn", 9.0) == 2.5
        finally:
            config.setConfig("ErisPulse.framework.txn_slow_warn", 1.0)
        assert get_framework_value("txn_slow_warn", 9.0) == 1.0

    def test_storage_begin_timeout_uses_framework_value(self):
        """事务开启超时消费点经 get_framework_value 惰性读取（接线冒烟）"""
        import inspect

        from ErisPulse.Core.Bases.storage import _AsyncTransaction

        src = inspect.getsource(_AsyncTransaction.start)
        assert "get_framework_value" in src
        assert '"txn_begin_timeout"' in src
        assert "begin_timeout" in src
