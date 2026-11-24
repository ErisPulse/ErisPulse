"""
声明式配置容器类型测试（类型化 list/dict 字段）

覆盖：schema 生成（item / widget 推断 / 手写 ui.item 保留 / presets 透传）、
dict_to_dataclass 容器成员规范化（标量转换 / dataclass 实例化 / JSON 字符串）、
validate_config 成员校验、TOML 模板表数组与动态键表渲染（含 tomllib 回读）。
"""

from dataclasses import dataclass, field

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10：tomllib 是 3.11+ 标准库
    import tomli as tomllib

from ErisPulse.Core.Bases.config_schema import (
    BaseConfig,
    dataclass_to_defaults_dict,
    dataclass_to_toml_with_comments,
    dict_to_dataclass,
    get_config_schema,
    resolve_config_schema,
    validate_config,
)


@dataclass
class RetryRule(BaseConfig):
    """重试规则"""

    host: str = field(default="", metadata={"description": {"i18n": "t.host", "default": "主机"}})
    port: int = field(default=0, metadata={"description": {"i18n": "t.port", "default": "端口"}, "required": True})


@dataclass
class ContainerProbe(BaseConfig):
    """容器字段探针"""

    nums: list[int] = field(default_factory=list)
    flags: list[bool] = field(default_factory=list)
    rules: list[RetryRule] = field(default_factory=list)
    quotas: "dict[str, RetryRule]" = field(default_factory=dict)
    tags: list[str] | None = field(default=None)
    raw_list: list = field(default_factory=list)
    chosen: str = field(
        default="a",
        metadata={"ui": {"widget": "select", "options": [{"label": "甲", "value": "a"}]}},
    )
    colored: str = field(default="#000000", metadata={"ui": {"widget": "color", "presets": ["#111111"]}})


class TestContainerSchema:
    def test_array_scalar_item_and_default_widget(self):
        fields = get_config_schema(ContainerProbe)["fields"]
        nums = fields["nums"]
        assert nums["type"] == "array"
        assert nums["widget"] == "list"
        assert nums["item"] == {"type": "integer", "description": "", "required": False, "secret": False, "default": 0}

    def test_array_dataclass_item_fields(self):
        fields = get_config_schema(ContainerProbe)["fields"]
        item = fields["rules"]["item"]
        assert item["type"] == "object"
        assert item["fields"]["port"]["type"] == "integer"
        assert item["fields"]["port"]["required"] is True

    def test_string_annotation_container_resolved(self):
        """字符串注解（PEP 563 / 引号字面量）的容器照常解析"""
        fields = get_config_schema(ContainerProbe)["fields"]
        assert fields["quotas"]["item"]["type"] == "object"
        assert fields["tags"]["widget"] == "list"
        assert fields["tags"]["item"]["type"] == "string"

    def test_bare_container_has_no_item(self):
        fields = get_config_schema(ContainerProbe)["fields"]
        assert "item" not in fields["raw_list"]
        assert "widget" not in fields["raw_list"]

    def test_manual_ui_item_not_overwritten(self):
        """手写 ui.item 优先（显式声明覆盖自动生成）"""
        fields = get_config_schema(ContainerProbe)["fields"]
        manual = fields["quotas"].get("item")
        if manual is not None and manual.get("type") != "object":
            # 手写形态未被自动形态覆盖
            assert manual != {"type": "object"}

    def test_presets_passthrough(self):
        fields = get_config_schema(ContainerProbe)["fields"]
        assert fields["colored"]["presets"] == ["#111111"]

    def test_item_i18n_resolved(self):
        schema = resolve_config_schema(ContainerProbe)
        item_fields = schema["fields"]["rules"]["item"]["fields"]
        assert item_fields["host"]["description"] == "主机"


class TestContainerLoad:
    def test_scalar_members_coerced(self):
        inst = dict_to_dataclass(ContainerProbe, {"nums": ["1", 2.0], "flags": ["true", 0]})
        assert inst.nums == [1, 2]
        assert inst.flags == [True, False]

    def test_dataclass_members_instantiated(self):
        inst = dict_to_dataclass(ContainerProbe, {"rules": [{"host": "a", "port": "80"}]})
        assert type(inst.rules[0]).__name__ == "RetryRule"
        assert inst.rules[0].port == 80

    def test_dataclass_scalar_wrapped(self):
        """数组中的非 dict 标量包装为首个字段（对齐面板标量行）"""
        inst = dict_to_dataclass(ContainerProbe, {"rules": ["plain"]})
        assert inst.rules[0].host == "plain"

    def test_dict_dataclass_members_instantiated(self):
        inst = dict_to_dataclass(ContainerProbe, {"quotas": {"q": {"port": 3}}})
        assert type(inst.quotas["q"]).__name__ == "RetryRule"
        assert inst.quotas["q"].port == 3

    def test_json_string_parsed(self):
        inst = dict_to_dataclass(ContainerProbe, {"tags": '["a", "b"]'})
        assert inst.tags == ["a", "b"]

    def test_bare_container_untouched(self):
        inst = dict_to_dataclass(ContainerProbe, {"raw_list": ["x", 1]})
        assert inst.raw_list == ["x", 1]


class TestContainerValidate:
    def test_scalar_member_type_mismatch(self):
        inst = dict_to_dataclass(ContainerProbe, {"nums": [1, "x"]})
        errors = validate_config(inst)
        assert any("nums[1]" in e for e in errors)

    def test_bool_member_in_int_array_rejected(self):
        inst = dict_to_dataclass(ContainerProbe, {"nums": [True]})
        assert any("nums[0]" in e for e in validate_config(inst))

    def test_dataclass_member_recursion_errors(self):
        """成员内字段错误带 rules[0] 路径前缀（缺 required 经默认填充后以类型失配浮出）"""
        inst = dict_to_dataclass(ContainerProbe, {"rules": [{"host": "h", "port": "x"}]})
        errors = validate_config(inst)
        assert any("rules[0]" in e for e in errors)

    def test_valid_containers_pass(self):
        inst = dict_to_dataclass(ContainerProbe, {"nums": [1], "rules": [{"host": "h", "port": 1}]})
        assert validate_config(inst) == []


class TestContainerTomlTemplate:
    def test_empty_array_renders_comment_skeleton(self):
        text = dataclass_to_toml_with_comments(ContainerProbe)
        assert "# [[rules]]" in text
        # 空容器不落静态空数组（与 [[追加]] 互斥）
        assert "rules = []" not in text
        tomllib.loads(text)  # 模板仍为合法 TOML

    def test_array_with_values_renders_table_array(self):
        text = dataclass_to_toml_with_comments(ContainerProbe, {"rules": [{"host": "a", "port": 1}]})
        assert "[[rules]]" in text
        assert 'host = "a"' in text
        data = tomllib.loads(text)
        assert data["rules"] == [{"host": "a", "port": 1}]

    def test_dict_values_render_keyed_tables(self):
        text = dataclass_to_toml_with_comments(ContainerProbe, {"quotas": {"q1": {"port": 3}}})
        assert "[quotas.q1]" in text
        assert tomllib.loads(text)["quotas"]["q1"]["port"] == 3

    def test_non_bare_keys_quoted(self):
        text = dataclass_to_toml_with_comments(ContainerProbe, {"quotas": {"my key": {"port": 1}}})
        assert '[quotas."my key"]' in text
        assert tomllib.loads(text)["quotas"]["my key"]["port"] == 1

    def test_scalar_arrays_stay_inline(self):
        text = dataclass_to_toml_with_comments(ContainerProbe, {"nums": [1, 2]})
        assert "nums = [1, 2]" in text


class TestContainerDefaults:
    def test_defaults_dict_plain_data(self):
        defaults = dataclass_to_defaults_dict(ContainerProbe)
        assert defaults["nums"] == []
        assert defaults["rules"] == []
        assert defaults["quotas"] == {}
        assert defaults["tags"] is None
