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
