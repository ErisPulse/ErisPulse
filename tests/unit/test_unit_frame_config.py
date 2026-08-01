"""
runtime/frame_config 单元测试

覆盖环境变量覆盖（Docker/12-factor）与默认值补全。
"""

import os

import pytest

from ErisPulse.runtime.frame_config import (
    _coerce_env_value,
    _apply_env_overrides,
    get_config,
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
