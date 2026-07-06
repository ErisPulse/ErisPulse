"""
ErisPulse 通用配置 Schema 模块

提供基于 dataclass 的配置定义，支持 TOML 注释生成和多语言 WebUI 表单元数据。

适用于适配器、模块、外部项目等任何需要声明式配置的场景。

{!--< tips >!--}
1. 使用 BaseConfig 作为单账户/全局配置基类（AdapterConfig 为其别名，保持兼容）
2. 使用 BotAccountConfig 作为多账户配置基类
3. 通过 field(metadata=...) 声明字段描述、控件类型等信息
4. description 支持 i18n 多语言：{"i18n": "key.path", "default": "默认文本"}
5. 使用 dataclass_to_toml_with_comments() 生成带注释的配置模板
6. 使用 dict_to_dataclass() 从 TOML 字典填充 dataclass
7. 使用 validate_config() 校验配置实例
8. 使用 get_config_schema() 生成 WebUI JSON Schema（含 i18n 支持）
{!--< /tips >!--}
"""

from dataclasses import MISSING, dataclass, field, fields
from typing import Mapping


# ---------------------------------------------------------------------------
# 内部辅助函数
# ---------------------------------------------------------------------------

def _resolve_description_text(meta: Mapping | None) -> str:
    """
    从 metadata 提取人类可读的描述文本

    用于 TOML 注释生成、校验错误信息等不需要多语言的场景。
    description 可以是:
      - 普通字符串: "账户备注名称"
      - i18n 字典:   {"i18n": "module.field.desc", "default": "账户备注名称"}

    :param meta: field.metadata 字典
    :return: 人类可读的描述字符串
    """
    if meta is None:
        return ""
    desc = meta.get("description", "")
    if isinstance(desc, dict):
        return desc.get("default", desc.get("i18n", ""))
    return desc or ""


def _resolve_description_schema(meta: Mapping | None) -> str | dict:
    """
    从 metadata 提取 schema 可用的描述信息

    - 普通字符串原样返回（WebUI 直接展示）
    - i18n 字典原样返回（WebUI 根据 language 查找翻译）

    :param meta: field.metadata 字典
    :return: 字符串或 i18n 描述字典
    """
    if meta is None:
        return ""
    desc = meta.get("description", "")
    if isinstance(desc, dict):
        return desc
    return desc or ""


def _get_ui_meta(meta: Mapping | None) -> dict:
    """
    从 metadata 获取 UI 配置（兼容新旧键名）

    优先级: "ui"（新） > "webui"（旧，保留兼容）

    :param meta: field.metadata 字典
    :return: UI 元数据字典
    """
    if meta is None:
        return {}
    return meta.get("ui", meta.get("webui", {}))


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


def _get_field_default(f):
    """获取字段的默认值"""
    if f.default is not MISSING:
        return f.default
    if f.default_factory is not MISSING:
        return f.default_factory()
    return _type_default(f.type)


def _is_empty(value) -> bool:
    """判断值是否为空"""
    if value is None:
        return True
    if isinstance(value, str) and value.strip() == "":
        return True
    if isinstance(value, (list, dict)) and len(value) == 0:
        return True
    return False


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


# ---------------------------------------------------------------------------
# 配置基类
# ---------------------------------------------------------------------------


@dataclass
class BaseConfig:
    """通用配置基类

    适用于任何模块/项目的单账户或全局配置场景。
    继承此类即可获得 TOML 序列化、校验、WebUI Schema 等能力。

    使用示例::

        @dataclass
        class MyModuleConfig(BaseConfig):
            api_key: str = field(
                default="",
                metadata={
                    "description": {"i18n": "my_module.api_key", "default": "API 密钥"},
                    "required": True,
                    "secret": True,
                    "ui": {"widget": "password", "group": "connection", "order": 1},
                },
            )
    """

    pass


# 向后兼容别名：AdapterConfig → BaseConfig
AdapterConfig = BaseConfig


@dataclass
class BotAccountConfig:
    """多账户配置基类

    适用于需要管理多个账户的场景（如多 Bot）。
    继承此类自动获得 enabled/name 基础字段。

    使用示例::

        @dataclass
        class MyBotConfig(BotAccountConfig):
            bot_id: str = field(
                default="",
                metadata={
                    "description": {"i18n": "my_adapter.bot_id", "default": "Bot ID"},
                    "required": True,
                    "ui": {"widget": "text", "group": "basic", "order": 1},
                },
            )
    """

    enabled: bool = field(
        default=True,
        metadata={
            "description": {"i18n": "config.account.enabled", "default": "是否启用此账户"},
            "required": False,
            "ui": {"widget": "switch", "group": "basic", "order": 999},
        },
    )
    name: str = field(
        default="",
        metadata={
            "description": {"i18n": "config.account.name", "default": "账户备注名称"},
            "required": False,
            "ui": {"widget": "text", "group": "basic", "order": 998},
        },
    )



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
            "ui": {
                "widget": "select",
                "options": ["auto", "zh-CN", "zh-TW", "en", "ja", "ru"],
                "group": "basic",
                "order": 1,
            },
        },
    )


# ---------------------------------------------------------------------------
# 公共 API
# ---------------------------------------------------------------------------


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


def dataclass_to_toml_with_comments(
    config_class: type, existing_values: dict | None = None
) -> str:
    """
    将 dataclass class 转为带注释的 TOML 文本

    用于首次写入配置文件时生成可读的配置模板。
    description 若为 i18n 字典，则使用其 default/fallback 文本。

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
        description = _resolve_description_text(meta)
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


def validate_config(instance) -> list[str]:
    """
    校验 dataclass 实例

    - 检查 required 字段是否非空
    - 返回错误信息列表（空列表表示通过）
    - description 若为 i18n 字典，错误信息使用其 fallback/default 文本

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
            desc_text = _resolve_description_text(meta) or f.name
            errors.append(f"{f.name}（{desc_text}）不能为空")

    return errors


def get_config_schema(config_class: type) -> dict:
    """
    从 dataclass 生成 WebUI 可用的 JSON Schema

    包含字段名、类型、描述（支持 i18n）、控件类型、分组、排序等。
    description 若为 i18n 字典则原样透传，WebUI 根据语言键查找翻译。

    :param config_class: dataclass 类
    :return: schema 字典
    """
    schema_fields = {}
    groups = set()

    for f in fields(config_class):
        meta = f.metadata or {}
        ui_meta = _get_ui_meta(meta)

        field_schema = {
            "type": _python_type_to_toml_type(f.type),
            "description": _resolve_description_schema(meta),
            "required": meta.get("required", False),
            "secret": meta.get("secret", False),
            "default": _get_field_default(f),
        }

        if "widget" in ui_meta:
            field_schema["widget"] = ui_meta["widget"]
        if "group" in ui_meta:
            field_schema["group"] = ui_meta["group"]
            groups.add(ui_meta["group"])
        if "order" in ui_meta:
            field_schema["order"] = ui_meta["order"]
        if "options" in ui_meta:
            field_schema["options"] = ui_meta["options"]
        if "placeholder" in ui_meta:
            field_schema["placeholder"] = ui_meta["placeholder"]

        # 冗余扩展：透传 metadata 中的 "extra" 到 schema
        if "extra" in meta:
            field_schema["extra"] = meta["extra"]

        schema_fields[f.name] = field_schema

    return {
        "fields": schema_fields,
        "groups": sorted(groups),
        "account_based": issubclass(config_class, BotAccountConfig),
        # 冗余扩展：透传 config_class 级别的 meta（如果有）
        "meta": getattr(config_class, "_schema_meta", {}),
    }


def register_config_i18n(
    config_class: type,
    lang: str,
    translations: dict[str, str] | None = None,
    domain: str = "config",
) -> int:
    """
    将配置类的字段描述注册到 i18n 系统

    遍历 config_class 的所有字段，提取 description 中的 i18n 键，
    调用 i18n.register() 注册翻译。

    两种用法：
    1. 自动模式（translations=None）：将字段 description.default 作为 zh-CN 翻译注册
    2. 手动模式：提供 translations 字典（{i18n_key: translated_text}）

    使用示例::

        # 自动注册默认值作为中文翻译
        register_config_i18n(MyAdapterConfig, "zh-CN")

        # 手动注册英文翻译
        register_config_i18n(MyAdapterConfig, "en", {
            "my_adapter.endpoint": "API Endpoint",
            "my_adapter.token": "Platform Token",
        })

        # 多账户配置同理
        register_config_i18n(MyBotConfig, "zh-CN")
        register_config_i18n(MyBotConfig, "en", {
            "my_adapter.bot_id": "Bot ID",
            "my_adapter.bot_token": "Bot Token",
        })

    :param config_class: dataclass 配置类
    :param lang: 语言代码（如 "zh-CN", "en"）
    :param translations: 手动提供的翻译字典，None 则自动提取
    :param domain: i18n 域标识，默认 "config"
    :return: 注册的翻译条目数
    """
    from ErisPulse.Core.i18n import i18n

    count = 0
    for f in fields(config_class):
        meta = f.metadata or {}
        desc = meta.get("description", "")
        if not isinstance(desc, dict) or "i18n" not in desc:
            continue

        key = desc["i18n"]

        if translations is not None:
            # 手动模式：从提供的字典中查找
            text = translations.get(key)
            if text is not None:
                i18n.register(lang, {key: text}, domain=domain)
                count += 1
        else:
            # 自动模式：使用 description.default
            text = desc.get("default", "")
            if text:
                i18n.register(lang, {key: text}, domain=domain)
                count += 1

    return count


def resolve_config_schema(config_class: type, resolve_i18n: bool = True) -> dict:
    """
    获取配置 Schema，可选地将 i18n description 解析为当前语言的文本

    与 get_config_schema() 的区别：
    - 当 resolve_i18n=True 时，description 字段为解析后的字符串（适合直接展示）
    - 当 resolve_i18n=False 时，等同于 get_config_schema()（透传 i18n 字典）

    适合需要在服务端直接渲染描述文本的场景（如 Dashboard API 返回给不支持 i18n 的前端）。

    :param config_class: dataclass 配置类
    :param resolve_i18n: 是否将 i18n 描述解析为当前语言文本
    :return: schema 字典
    """
    schema = get_config_schema(config_class)

    if not resolve_i18n:
        return schema

    from ErisPulse.Core.i18n import i18n

    for field_name, field_schema in schema["fields"].items():
        desc = field_schema.get("description", "")
        if isinstance(desc, dict) and "i18n" in desc:
            key = desc["i18n"]
            default = desc.get("default", key)
            field_schema["description"] = i18n.t(key, default=default)

    return schema


# ---------------------------------------------------------------------------
# 导出
# ---------------------------------------------------------------------------

__all__ = [
    # 基类
    "BaseConfig",
    "AdapterConfig",  # ← BaseConfig 的别名
    "BotAccountConfig",
    "I18nConfig",
    # 工具函数
    "dataclass_to_toml_with_comments",
    "dataclass_to_defaults_dict",
    "dict_to_dataclass",
    "validate_config",
    "get_config_schema",
    "register_config_i18n",
    "resolve_config_schema",
]