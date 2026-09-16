"""
配置环境变量映射（metadata: {"env": ...}）单元测试

测试声明式配置的环境变量绑定：优先级 env > toml > default、按字段注解
类型转换（str/int/float/bool/list/dict）、转换失败回退、嵌套 dataclass
字段覆盖、schema 与 TOML 模板的声明性输出（env 名提示、不写 env 值）、
以及未声明 env 字段的完全兼容。
"""

from dataclasses import dataclass, field

import pytest

from ErisPulse.Core.Bases.config_schema import (
    BaseConfig,
    dataclass_to_defaults_dict,
    dataclass_to_toml_with_comments,
    dict_to_dataclass,
    get_config_schema,
)


@dataclass
class EnvConfig(BaseConfig):
    api_key: str = field(
        default="",
        metadata={"description": "API 密钥", "env": "TEST_ENV_API_KEY"},
    )
    retries: int = field(default=3, metadata={"env": "TEST_ENV_RETRIES"})
    ratio: float = field(default=0.5, metadata={"env": "TEST_ENV_RATIO"})
    enabled: bool = field(default=False, metadata={"env": "TEST_ENV_ENABLED"})
    tags: list = field(default_factory=list, metadata={"env": "TEST_ENV_TAGS"})
    plain: str = ""  # 未声明 env：完全兼容


@dataclass
class EnvNested(BaseConfig):
    inner_key: str = field(default="", metadata={"env": "TEST_ENV_INNER_KEY"})


@dataclass
class EnvOuter(BaseConfig):
    nested: EnvNested = field(default_factory=EnvNested)


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    """清理测试涉及的全部环境变量"""
    for name in (
        "TEST_ENV_API_KEY",
        "TEST_ENV_RETRIES",
        "TEST_ENV_RATIO",
        "TEST_ENV_ENABLED",
        "TEST_ENV_TAGS",
        "TEST_ENV_INNER_KEY",
    ):
        monkeypatch.delenv(name, raising=False)
    yield


class TestEnvOverridePriority:
    """优先级：环境变量 > config.toml(data) > 声明默认值"""

    def test_env_overrides_default(self, monkeypatch):
        monkeypatch.setenv("TEST_ENV_API_KEY", "from-env")
        cfg = dict_to_dataclass(EnvConfig, {})
        assert cfg.api_key == "from-env"

    def test_env_overrides_toml(self, monkeypatch):
        monkeypatch.setenv("TEST_ENV_API_KEY", "from-env")
        cfg = dict_to_dataclass(EnvConfig, {"api_key": "from-toml"})
        assert cfg.api_key == "from-env"

    def test_toml_used_without_env(self):
        cfg = dict_to_dataclass(EnvConfig, {"api_key": "from-toml"})
        assert cfg.api_key == "from-toml"

    def test_default_without_env_and_toml(self):
        cfg = dict_to_dataclass(EnvConfig, {})
        assert cfg.api_key == "" and cfg.retries == 3 and cfg.plain == ""

    def test_undeclared_field_untouched(self, monkeypatch):
        """未声明 env 的字段完全不受影响（向后兼容）"""
        monkeypatch.setenv("TEST_ENV_API_KEY", "from-env")
        cfg = dict_to_dataclass(EnvConfig, {"plain": "keep"})
        assert cfg.plain == "keep"


class TestEnvTypeConversion:
    """环境变量字符串 → 字段注解类型转换"""

    def test_int(self, monkeypatch):
        monkeypatch.setenv("TEST_ENV_RETRIES", "7")
        assert dict_to_dataclass(EnvConfig, {}).retries == 7

    def test_float(self, monkeypatch):
        monkeypatch.setenv("TEST_ENV_RATIO", "0.75")
        assert dict_to_dataclass(EnvConfig, {}).ratio == 0.75

    @pytest.mark.parametrize("raw,expected", [("true", True), ("1", True), ("false", False), ("no", False)])
    def test_bool(self, monkeypatch, raw, expected):
        monkeypatch.setenv("TEST_ENV_ENABLED", raw)
        cfg = dict_to_dataclass(EnvConfig, {})
        assert cfg.enabled is expected

    def test_list_via_json(self, monkeypatch):
        monkeypatch.setenv("TEST_ENV_TAGS", '["a", "b"]')
        assert dict_to_dataclass(EnvConfig, {}).tags == ["a", "b"]

    def test_bool_not_confused_with_int(self, monkeypatch):
        """bool 字段收 "1" → True；int 字段收 "1" → 1（互不串扰）"""
        monkeypatch.setenv("TEST_ENV_ENABLED", "1")
        monkeypatch.setenv("TEST_ENV_RETRIES", "2")
        cfg = dict_to_dataclass(EnvConfig, {})
        assert cfg.enabled is True and cfg.retries == 2

    def test_invalid_value_falls_back(self, monkeypatch):
        """转换失败（int 字段收到非数字）→ 忽略覆盖回退 toml/default"""
        monkeypatch.setenv("TEST_ENV_RETRIES", "abc")
        cfg = dict_to_dataclass(EnvConfig, {"retries": 9})
        assert cfg.retries == 9

    def test_invalid_json_list_falls_back(self, monkeypatch):
        monkeypatch.setenv("TEST_ENV_TAGS", "not-json")
        cfg = dict_to_dataclass(EnvConfig, {})
        assert cfg.tags == []

    def test_empty_env_value_ignored(self, monkeypatch):
        """空字符串环境变量视为未设置"""
        monkeypatch.setenv("TEST_ENV_API_KEY", "")
        cfg = dict_to_dataclass(EnvConfig, {})
        assert cfg.api_key == ""


class TestEnvNested:
    """嵌套 dataclass 字段的 env 覆盖（递归生效）"""

    def test_nested_env(self, monkeypatch):
        monkeypatch.setenv("TEST_ENV_INNER_KEY", "inner-env")
        cfg = dict_to_dataclass(EnvOuter, {})
        assert cfg.nested.inner_key == "inner-env"

    def test_nested_toml_lower_priority(self, monkeypatch):
        monkeypatch.setenv("TEST_ENV_INNER_KEY", "inner-env")
        cfg = dict_to_dataclass(EnvOuter, {"nested": {"inner_key": "inner-toml"}})
        assert cfg.nested.inner_key == "inner-env"


class TestDeclarativeOutputs:
    """声明性输出（schema / 模板 / defaults）中的 env 语义"""

    def test_schema_contains_env(self):
        schema = get_config_schema(EnvConfig)
        assert schema["fields"]["api_key"]["env"] == "TEST_ENV_API_KEY"
        assert "env" not in schema["fields"]["plain"]

    def test_toml_template_hints_env_without_value(self, monkeypatch):
        """模板仅提示环境变量名，不写入 env 实际值（防泄露）"""
        monkeypatch.setenv("TEST_ENV_API_KEY", "super-secret-value")
        text = dataclass_to_toml_with_comments(EnvConfig)
        assert "TEST_ENV_API_KEY" in text
        assert "super-secret-value" not in text

    def test_defaults_dict_pure_declaration(self, monkeypatch):
        """默认值字典为纯声明（不含 env 值），供模板生成使用"""
        monkeypatch.setenv("TEST_ENV_RETRIES", "99")
        assert dataclass_to_defaults_dict(EnvConfig)["retries"] == 3

    def test_validate_sees_env_values(self, monkeypatch):
        """校验消费点：env 覆盖后的实例值进入校验（required 字段被 env 满足）"""
        @dataclass
        class RequiredConfig(BaseConfig):
            token: str = field(default="", metadata={"env": "TEST_ENV_API_KEY", "required": True})

        from ErisPulse.Core.Bases.config_schema import validate_config

        # 未设置 env：required 校验失败
        errors = validate_config(dict_to_dataclass(RequiredConfig, {}))
        assert len(errors) == 1
        # 设置 env：覆盖后校验通过
        monkeypatch.setenv("TEST_ENV_API_KEY", "tok")
        assert validate_config(dict_to_dataclass(RequiredConfig, {})) == []

    def test_hot_reload_path_same_semantics(self, monkeypatch):
        """热更新走同一 dict_to_dataclass 管道：env 优先级一致"""
        monkeypatch.setenv("TEST_ENV_RETRIES", "5")
        first = dict_to_dataclass(EnvConfig, {})
        monkeypatch.setenv("TEST_ENV_RETRIES", "6")
        second = dict_to_dataclass(EnvConfig, {})
        assert (first.retries, second.retries) == (5, 6)


class TestDataclassDirectConstruction:
    """直接构造 dataclass 实例（不经 dict_to_dataclass）不受 env 影响——

    env 覆盖发生在框架配置管道（dict_to_dataclass）；直接实例化是纯声明行为。
    """

    def test_direct_init_ignores_env(self, monkeypatch):
        monkeypatch.setenv("TEST_ENV_RETRIES", "7")
        cfg = EnvConfig()
        assert cfg.retries == 3
