"""
ErisPulse 适配器配置 Schema 模块

提供基于 dataclass 的配置定义，支持 TOML 注释生成和 WebUI 表单元数据。

{!--< tips >!--}
1. 使用 AdapterConfig 作为单账户/全局配置基类
2. 使用 BotAccountConfig 作为多账户配置基类
3. 通过 field(metadata=...) 声明字段描述、控件类型等信息
4. 使用 dataclass_to_toml_with_comments() 生成带注释的配置模板
5. 使用 dict_to_dataclass() 从 TOML 字典填充 dataclass
6. 使用 validate_config() 校验配置实例
{!--< /tips >!--}
"""

from dataclasses import MISSING, dataclass, field, fields


@dataclass
class I18nConfig:
    """
    国际化配置

    控制框架的显示语言和翻译行为
    """

    language: str = field(
        default="auto",
        metadata={
            "description": "显示语言 (auto=自动检测, zh-CN, zh-TW, en, ja, ru)",
            "required": False,
            "webui": {
                "widget": "select",
                "options": ["auto", "zh-CN", "zh-TW", "en", "ja", "ru"],
                "group": "basic",
                "order": 1,
            },
        },
    )
9

@dataclass
class AdapterConfig:
    """适配器全局配置基类（单账户/无账户适配器使用）"""

    pass


@dataclass
class BotAccountConfig:
    """Bot 账户配置基类（多账户适配器使用）"""

    enabled: bool = field(
        default=True,
        metadata={
            "description": "是否启用此账户",
            "required": False,
            "webui": {"widget": "switch", "group": "basic", "order": 999},
        },
    )
    name: str = field(
        default="",
        metadata={
            "description": "账户备注名称",
            "required": False,
            "webui": {"widget": "text", "group": "basic", "order": 998},
        },
    )


def dataclass_to_defaults_dict(config_class: type) -> dict:
    """
    从 dataclass 类生成默认值字典

    :param config_class: dataclass 类
    :return: 默认值字典
    """
    result = {}
    for f in fields(config_class):
        if f.default is not MISSING:
            result[f.name] = f.default
        elif f.default_factory is not MISSING:
            result[f.name] = f.default_factory()
        else:
            type_default = _type_default(f.type)
            result[f.name] = type_default
    return result


def _type_default(type_hint) -> object:
    """根据类型注解返回合理的默认值"""
    type_str = str(type_hint).lower()
    if "int" in type_str:
        return 0
    if "float" in type_str:
        return 0.0
    if "bool" in type_str:
        return False
    if "list" in type_str:
        return []
    if "dict" in type_str:
        return {}
    return ""


def _python_type_to_toml_type(type_hint) -> str:
    """将 Python 类型注解转为 TOML 类型字符串"""
    type_str = str(type_hint).lower()
    if "int" in type_str:
        return "integer"
    if "float" in type_str:
        return "float"
    if "bool" in type_str:
        return "boolean"
    if "list" in type_str:
        return "array"
    if "dict" in type_str:
        return "table"
    return "string"


def _format_toml_value(value) -> str:
    """将 Python 值格式化为 TOML 值字符串"""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        return str(value)
    if isinstance(value, str):
        return f'"{value}"'
    if isinstance(value, list):
        import json

        return json.dumps(value)
    if isinstance(value, dict):
        return "{}"
    return f'"{value}"'


def dataclass_to_toml_with_comments(
    config_class: type, existing_values: dict | None = None
) -> str:
    """
    将 dataclass class 转为带注释的 TOML 文本
    用于首次写入配置文件时生成可读的配置模板

    :param config_class: dataclass 类
    :param existing_values: 已有的配置值（覆盖默认值）
    :return: TOML 文本字符串
    """
    if existing_values is None:
        existing_values = {}

    lines = []

    for f in fields(config_class):
        value = existing_values.get(f.name)
        if value is None:
            if f.default is not MISSING:
                value = f.default
            elif f.default_factory is not MISSING:
                value = f.default_factory()
            else:
                value = _type_default(f.type)

        meta = f.metadata
        description = meta.get("description", "") if meta else ""
        required = meta.get("required", False) if meta else False

        if description:
            suffix = "（必填）" if required else ""
            lines.append(f"# {description}{suffix}")

        toml_value = _format_toml_value(value)

        if required and value in ("", 0, 0.0, False, None, [], {}):
            lines.append(f"# {f.name} = {toml_value}")
        else:
            lines.append(f"{f.name} = {toml_value}")

        lines.append("")

    return "\n".join(lines)


def dict_to_dataclass(config_class: type, data: dict):
    """
    从 TOML dict 填充 dataclass 实例

    - 处理类型转换（str → int 等）
    - 忽略 dataclass 中不存在的字段
    - 使用 default/default_factory 填充缺失字段

    :param config_class: dataclass 类
    :param data: 字典数据（通常来自 TOML 解析）
    :return: dataclass 实例
    """
    if data is None:
        data = {}

    kwargs = {}
    for f in fields(config_class):
        raw_value = data.get(f.name, MISSING)

        if raw_value is MISSING:
            if f.default is not MISSING:
                kwargs[f.name] = f.default
            elif f.default_factory is not MISSING:
                kwargs[f.name] = f.default_factory()
            else:
                kwargs[f.name] = _type_default(f.type)
        else:
            kwargs[f.name] = _coerce_value(raw_value, f.type)

    return config_class(**kwargs)


def _coerce_value(value, type_hint):
    """将值强制转换为目标类型"""
    if value is None:
        return value

    type_str = str(type_hint).lower()

    try:
        if "int" in type_str and not isinstance(value, bool):
            return int(value)
        if "float" in type_str and not isinstance(value, bool):
            return float(value)
        if "bool" in type_str:
            if isinstance(value, str):
                return value.lower() in ("true", "1", "yes", "on")
            return bool(value)
    except (ValueError, TypeError):
        return value

    return value


def validate_config(instance) -> list[str]:
    """
    校验 dataclass 实例

    - 检查 required 字段是否非空
    - 返回错误信息列表（空列表表示通过）

    :param instance: dataclass 实例
    :return: 错误信息列表
    """
    errors = []

    for f in fields(instance):
        meta = f.metadata
        if not meta:
            continue

        required = meta.get("required", False)
        if not required:
            continue

        value = getattr(instance, f.name)
        if _is_empty(value):
            description = meta.get("description", f.name)
            errors.append(f"{f.name}（{description}）不能为空")

    return errors


def _is_empty(value) -> bool:
    """判断值是否为空"""
    if value is None:
        return True
    if isinstance(value, str) and value.strip() == "":
        return True
    if isinstance(value, (list, dict)) and len(value) == 0:
        return True
    return False


def get_config_schema(config_class: type) -> dict:
    """
    从 dataclass 生成 WebUI 可用的 JSON Schema

    包含字段名、类型、描述、控件类型、分组、排序等

    :param config_class: dataclass 类
    :return: schema 字典
    """
    schema_fields = {}
    groups = set()

    for f in fields(config_class):
        meta = f.metadata or {}
        webui = meta.get("webui", {})

        field_schema = {
            "type": _python_type_to_toml_type(f.type),
            "description": meta.get("description", ""),
            "required": meta.get("required", False),
            "secret": meta.get("secret", False),
            "default": _get_field_default(f),
        }

        if "widget" in webui:
            field_schema["widget"] = webui["widget"]
        if "group" in webui:
            field_schema["group"] = webui["group"]
            groups.add(webui["group"])
        if "order" in webui:
            field_schema["order"] = webui["order"]
        if "options" in webui:
            field_schema["options"] = webui["options"]
        if "placeholder" in webui:
            field_schema["placeholder"] = webui["placeholder"]

        schema_fields[f.name] = field_schema

    return {
        "fields": schema_fields,
        "groups": sorted(groups),
        "account_based": issubclass(config_class, BotAccountConfig),
    }


def _get_field_default(f):
    """获取字段的默认值"""
    if f.default is not MISSING:
        return f.default
    if f.default_factory is not MISSING:
        return f.default_factory()
    return _type_default(f.type)


__all__ = [
    "AdapterConfig",
    "BotAccountConfig",
    "I18nConfig",
    "dataclass_to_toml_with_comments",
    "dataclass_to_defaults_dict",
    "dict_to_dataclass",
    "validate_config",
    "get_config_schema",
]
