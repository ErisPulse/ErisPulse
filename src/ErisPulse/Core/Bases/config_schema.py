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

from collections.abc import Mapping
from dataclasses import MISSING, dataclass, field, fields
from typing import Any, ClassVar

from ..i18n import i18n

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
    """
    根据类型注解返回合理的默认值

    {!--< internal-use >!--}
    {!--< /internal-use >!--}

    :param type_hint: Python 类型注解
    :return: 对应类型的默认值（int→0, float→0.0, bool→False, list→[], dict→{}, str→""）
    """
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
    """
    将 Python 类型注解转为 TOML 类型字符串

    {!--< internal-use >!--}
    {!--< /internal-use >!--}

    :param type_hint: Python 类型注解
    :return: TOML 类型名（integer/float/boolean/array/table/string）
    """
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
    """
    将 Python 值格式化为 TOML 值字符串

    {!--< internal-use >!--}
    {!--< /internal-use >!--}

    :param value: Python 值（str/int/float/bool/list/dict 等）
    :return: TOML 格式的字符串
    """
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
    """
    获取 dataclass 字段的默认值

    {!--< internal-use >!--}
    {!--< /internal-use >!--}

    :param f: dataclass Field 对象
    :return: 字段的默认值（优先 default，其次 default_factory，最后根据类型推断）
    """
    if f.default is not MISSING:
        return f.default
    if f.default_factory is not MISSING:
        return f.default_factory()
    return _type_default(f.type)


def _is_empty(value) -> bool:
    """
    判断值是否为空（None / 空字符串 / 空列表 / 空字典）

    {!--< internal-use >!--}
    {!--< /internal-use >!--}

    :param value: 任意值
    :return: 是否为空
    """
    if value is None:
        return True
    if isinstance(value, str) and value.strip() == "":
        return True
    return bool(isinstance(value, (list, dict)) and len(value) == 0)


def _coerce_value(value, type_hint):
    """
    将值强制转换为目标类型（如 str→int、str→bool）

    {!--< internal-use >!--}
    {!--< /internal-use >!--}

    :param value: 原始值
    :param type_hint: 目标类型注解
    :return: 转换后的值（转换失败时返回原值）
    """
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

    # Schema 级别的扩展元数据（如 group_labels），由 get_config_schema 透传
    _schema_meta: ClassVar[dict] = {}


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
            "description": {"i18n": "core.config.i18n_language_description", "default": "显示语言 (auto=自动检测, zh-CN, zh-TW, en, ja, ru)"},
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
        is_secret = meta.get("secret", False) if meta else False
        description = _resolve_description_text(meta)
        required = meta.get("required", False) if meta else False

        if description:
            suffix = i18n.t("core.config.required_suffix") if required else ""
            lines.append(f"# {description}{suffix}")

        # secret 字段不把真实值写入模板文件，避免配置文件泄露敏感信息
        effective_value = (
            "" if (is_secret and value not in ("", None, [], {})) else value
        )
        toml_value = _format_toml_value(effective_value)

        if required and effective_value in ("", 0, 0.0, False, None, [], {}):
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


def _notify_instance_config_update(
    instance: Any,
    old_dict: dict | None,
    new_dict: dict | None,
    *,
    i18n_key: str,
    log_params: dict,
) -> None:
    """
    调用实例的 ``on_config_update`` 回调，传入类型安全的配置对象

    若实例声明了 ``ConfigClass``，则将字典通过 :func:`dict_to_dataclass`
    转换为 dataclass 实例；否则原样传入字典。回调中抛出的异常会被捕获
    并按指定的 i18n 键记录日志，不会向上传播。

    供 ``ModuleManager`` 与 ``AdapterManager`` 的配置热更新路由共用，
    避免在两处重复实现字典→dataclass 转换 + 异常兜底逻辑。

    {!--< internal-use >!--}
    {!--< /internal-use >!--}

    :param instance: 模块/适配器实例（需实现 ``on_config_update``）
    :param old_dict: 变更前的配置字典（可能为 None）
    :param new_dict: 变更后的配置字典（可能为 None）
    :param i18n_key: 回调异常日志的 i18n 键（如 ``core.module.config_update_failed``）
    :param log_params: 异常日志的额外格式化参数（如 ``{"name": "MyModule"}``）
    """
    config_class = getattr(instance, "ConfigClass", None)
    try:
        if config_class is not None:
            old_config = (
                dict_to_dataclass(config_class, old_dict) if old_dict else None
            )
            new_config = (
                dict_to_dataclass(config_class, new_dict) if new_dict else None
            )
        else:
            old_config = old_dict
            new_config = new_dict
        instance.on_config_update(old_config, new_config)
    except Exception as e:
        try:
            from ErisPulse.Core.logger import logger

            params = dict(log_params)
            params["error"] = e
            logger.error(i18n.t(i18n_key, **params))
        except Exception:
            pass


def validate_config(instance) -> list[str]:
    """
    校验 dataclass 实例

    - 检查 ``required`` 字段是否非空
    - 检查字段值类型是否与声明一致（int/float/str/bool）
    - 检查 ``options`` 枚举约束（值是否在允许选项内）
    - 检查 ``min``/``max`` 数值范围约束

    返回错误信息列表（空列表表示通过）。description 若为 i18n 字典，
    错误信息使用其 fallback/default 文本。

    :param instance: dataclass 实例
    :return: 错误信息列表
    """
    errors = []

    # 字段声明类型名 → Python 类型 的简易映射（仅校验基本类型）
    _type_map = {"int": int, "float": float, "str": str, "bool": bool}

    for f in fields(instance):
        meta = f.metadata or {}
        value = getattr(instance, f.name)
        ui_meta = _get_ui_meta(meta) if meta else {}

        # 1. required 非空（需要 metadata 声明）
        if meta.get("required", False) and _is_empty(value):
            desc_text = _resolve_description_text(meta) or f.name
            errors.append(i18n.t("core.config.field_required_empty", field=f.name, desc=desc_text))
            continue  # 已为空，类型/范围检查无意义

        # 跳过空值后续检查
        if value in (None, "", [], {}):
            continue

        # 2. 类型检查
        type_name = (
            f.type if isinstance(f.type, str) else getattr(f.type, "__name__", "")
        )
        expected = _type_map.get(type_name)
        if expected is not None and not isinstance(value, expected):
            # bool 是 int 的子类：声明 int 但实际为 bool 视为类型不符
            errors.append(
                i18n.t("core.config.field_type_mismatch", field=f.name, expected=type_name, actual=type(value).__name__)
            )

        # 3. 枚举选项（options 可在 ui 子表或 metadata 顶层）
        options = ui_meta.get("options") or meta.get("options")
        if options:
            plain_opts = [
                o.get("value") if isinstance(o, dict) else o for o in options
            ]
            if value not in plain_opts:
                errors.append(i18n.t("core.config.field_option_invalid", field=f.name, value=value))

        # 4. 数值范围
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            min_val = ui_meta.get("min") if ui_meta else None
            max_val = ui_meta.get("max") if ui_meta else None
            if min_val is None:
                min_val = meta.get("min")
            if max_val is None:
                max_val = meta.get("max")
            if min_val is not None and value < min_val:
                errors.append(i18n.t("core.config.field_below_min", field=f.name, value=value, min=min_val))
            if max_val is not None and value > max_val:
                errors.append(i18n.t("core.config.field_above_max", field=f.name, value=value, max=max_val))

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
    1. 自动模式（translations=None）：将字段 description.default 注册到指定 lang
       （description.default 是语言无关的兜底文本，调用者自行决定注册到哪种语言）
    2. 手动模式：提供 translations 字典（{i18n_key: translated_text}）

    使用示例::

        # 将默认文本注册为中文翻译
        register_config_i18n(MyAdapterConfig, "zh-CN")

        # 将默认文本注册为英文翻译
        register_config_i18n(MyAdapterConfig, "en")

        # 手动提供英文翻译（覆盖默认文本）
        register_config_i18n(MyAdapterConfig, "en", {
            "my_adapter.endpoint": "API Endpoint",
            "my_adapter.token": "Platform Token",
        })

    :param config_class: dataclass 配置类
    :param lang: 语言代码（如 "zh-CN", "en"）
    :param translations: 手动提供的翻译字典，None 则自动提取
    :param domain: i18n 域标识，默认 "config"
    :return: 注册的翻译条目数
    """

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


def _resolve_i18n_text(value, i18n_mgr):
    """
    解析单个值的 i18n 文本

    接受纯字符串（原样返回）或 i18n 字典（解析为当前语言文本）。

    :param value: 原始值（str 或 {"i18n": ..., "default": ...}）
    :param i18n_mgr: I18nManager 实例
    :return: 解析后的字符串
    """
    if isinstance(value, dict) and "i18n" in value:
        key = value["i18n"]
        default = value.get("default", key)
        return i18n_mgr.t(key, default=default)
    return value


def resolve_config_schema(config_class: type, resolve_i18n: bool = True) -> dict:
    """
    获取配置 Schema，可选地将所有 i18n 文本字段解析为当前语言的文本

    与 get_config_schema() 的区别：
    - 当 resolve_i18n=True 时，所有用户可见文本字段（description、options label、
      placeholder、group_labels）为解析后的字符串（适合直接展示）
    - 当 resolve_i18n=False 时，等同于 get_config_schema()（透传 i18n 字典）

    支持的 i18n 字段（均采用 ``{"i18n": "key", "default": "文本"}`` 格式）：
    - ``description``: 字段描述
    - ``options[].label``: select 控件选项标签
    - ``placeholder``: 输入框占位符
    - ``group_labels``: 分组显示名（通过 ``_schema_meta["group_labels"]`` 声明）

    纯字符串值会被原样透传（向后兼容）。

    :param config_class: dataclass 配置类
    :param resolve_i18n: 是否将 i18n 文本解析为当前语言
    :return: schema 字典
    """
    schema = get_config_schema(config_class)

    if not resolve_i18n:
        return schema


    for field_schema in schema["fields"].values():
        # description
        field_schema["description"] = _resolve_i18n_text(
            field_schema.get("description", ""), i18n
        )

        # placeholder
        if "placeholder" in field_schema:
            field_schema["placeholder"] = _resolve_i18n_text(
                field_schema["placeholder"], i18n
            )

        # options[].label
        options = field_schema.get("options")
        if isinstance(options, list):
            resolved_options = []
            for opt in options:
                if isinstance(opt, dict) and "label" in opt:
                    resolved = dict(opt)
                    resolved["label"] = _resolve_i18n_text(opt["label"], i18n)
                    resolved_options.append(resolved)
                else:
                    resolved_options.append(opt)
            field_schema["options"] = resolved_options

    # group_labels: 通过 _schema_meta 声明的分组显示名
    meta = schema.get("meta", {})
    group_labels = meta.get("group_labels", {})
    if group_labels:
        schema["group_labels"] = {
            name: _resolve_i18n_text(label, i18n)
            for name, label in group_labels.items()
        }

    return schema


# ---------------------------------------------------------------------------
# Secret 脱敏
# ---------------------------------------------------------------------------

# secret 字段脱敏后的固定掩码
SECRET_REDACTED: str = "***"


def redact_secret(value: Any) -> Any:
    """
    脱敏标记为 ``secret`` 的配置值

    非空值统一替换为固定掩码 ``***``；空值（空串 / None / 空集合）原样返回，
    便于日志、模板生成等场景避免泄露敏感信息。

    :param value: 原始值
    :return: 脱敏后的值

    :example:
    >>> redact_secret("sk-xxxxxxxx")
    '***'
    >>> redact_secret("")
    ''
    """
    if value is None or value == "" or (isinstance(value, (list, dict)) and not value):
        return value
    return SECRET_REDACTED


# ---------------------------------------------------------------------------
# 导出
# ---------------------------------------------------------------------------

__all__ = [
    "SECRET_REDACTED",
    "AdapterConfig",
    "BaseConfig",
    "BotAccountConfig",
    "I18nConfig",
    "dataclass_to_defaults_dict",
    "dataclass_to_toml_with_comments",
    "dict_to_dataclass",
    "get_config_schema",
    "redact_secret",
    "register_config_i18n",
    "resolve_config_schema",
    "validate_config",
]
