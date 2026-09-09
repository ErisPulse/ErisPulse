"""
ErisPulse 通用配置 Schema 模块

提供基于 dataclass 的配置定义，支持 TOML 注释生成和多语言 WebUI 表单元数据。

适用于适配器、模块、外部项目等任何需要声明式配置的场景。

{!--< tips >!--}
1. 使用 BaseConfig 作为单账户/全局配置基类（AdapterConfig 为其别名，保持兼容）
2. 使用 BotAccountConfig 作为多账户配置基类
3. 通过 field(metadata=...) 声明字段描述、控件类型等信息
4. description 支持 i18n 多语言：{"i18n": "key.path", "default": "默认文本"}
5. 未声明 description 时自动从类 docstring 提取字段说明兜底（:ivar: 或 Attributes: 风格）
6. 通过 field(metadata={"example": True}) 声明仅进 config.full.example 的示例字段（不自动落盘）
7. 使用 dataclass_to_toml_with_comments() 生成带注释的配置模板
8. 使用 dict_to_dataclass() 从 TOML 字典填充 dataclass
9. 使用 validate_config() 校验配置实例
10. 使用 get_config_schema() 生成 WebUI JSON Schema（含 i18n 支持）
{!--< /tips >!--}
"""

import inspect
import re
import sys
from collections.abc import Mapping
from dataclasses import MISSING, dataclass, field, fields, is_dataclass
from functools import cache
from typing import Any, ClassVar

from ..i18n import i18n

# ---------------------------------------------------------------------------
# 内部辅助函数
# ---------------------------------------------------------------------------

# reST 风格字段说明：:ivar name: desc / :cvar name: desc / :var name: desc
_RST_IVAR_RE = re.compile(r"^:(?:i|c)?var\s+(\w+)\s*[:：]\s*(.+)$")
# Google 风格字段说明行：name: desc（Attributes: 段内）
_GOOGLE_ATTR_RE = re.compile(r"^(\w+)\s*[:：]\s*(.+)$")


@cache
def get_field_docstrings(config_class: type) -> dict[str, str]:
    """
    从配置类 docstring 提取字段描述（description 兜底来源）

    支持两种常见风格（可混用，Google 段优先覆盖）：

    - reST::

        '''适配器配置

        :ivar token: API 访问令牌
        :ivar mode: 运行模式
        '''

    - Google::

        '''适配器配置

        Attributes:
            token: API 访问令牌
            mode: 运行模式
        '''

    :param config_class: 配置 dataclass 类
    :return: dict {字段名: 描述文本}
    """
    doc = inspect.getdoc(config_class)
    if not doc:
        return {}

    result: dict[str, str] = {}
    in_attributes = False
    for line in doc.splitlines():
        stripped = line.strip()

        rst_match = _RST_IVAR_RE.match(stripped)
        if rst_match:
            result[rst_match.group(1)] = rst_match.group(2).strip()
            in_attributes = False
            continue

        if stripped in ("Attributes:", "Attributes："):
            in_attributes = True
            continue

        if in_attributes:
            if not stripped:
                continue
            google_match = _GOOGLE_ATTR_RE.match(stripped)
            if google_match and (line.startswith((" ", "\t")) or not result):
                # 段内条目（缩进行）；反引号包裹的字段名剥除装饰
                name = google_match.group(1).strip("`")
                result[name] = google_match.group(2).strip()
            else:
                # 非条目内容 → Attributes 段结束
                in_attributes = False

    return result


def _resolve_description_text(meta: Mapping | None, fallback: str = "") -> str:
    """
    从 metadata 提取人类可读的描述文本

    用于 TOML 注释生成、校验错误信息等不需要多语言的场景。
    description 可以是:
      - 普通字符串: "账户备注名称"
      - i18n 字典:   {"i18n": "module.field.desc", "default": "账户备注名称"}

    未声明（或为空）时回退到 docstring 提取的字段说明。

    :param meta: field.metadata 字典
    :param fallback: description 缺失/为空时的兜底文本（docstring 描述）
    :return: 人类可读的描述字符串
    """
    if meta is not None:
        desc = meta.get("description", "")
        if isinstance(desc, dict):
            text = desc.get("default", desc.get("i18n", ""))
            return text or fallback
        if desc:
            return desc
    return fallback


def _resolve_description_schema(meta: Mapping | None, fallback: str = "") -> str | dict:
    """
    从 metadata 提取 schema 可用的描述信息

    - 普通字符串原样返回（WebUI 直接展示）
    - i18n 字典原样返回（WebUI 根据 language 查找翻译）

    未声明（或为空）时回退到 docstring 提取的字段说明。

    :param meta: field.metadata 字典
    :param fallback: description 缺失/为空时的兜底文本（docstring 描述）
    :return: 字符串或 i18n 描述字典
    """
    if meta is not None:
        desc = meta.get("description", "")
        if isinstance(desc, dict):
            return desc
        if desc:
            return desc
    return fallback


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


def _resolve_nested_dataclass(config_class: type, f) -> type | None:
    """
    解析字段类型，若为嵌套 dataclass 则返回该类型，否则返回 None

    支持直接类型注解与字符串注解（延迟求值 / ``from __future__ import
    annotations``）；字符串注解从类所在模块全局与类属性（含嵌套类声明）按名解析。

    :param config_class: 外层配置 dataclass 类（或其实例的类）
    :param f: dataclass Field 对象
    :return: 嵌套 dataclass 类型，非嵌套字段返回 None

    {!--< internal-use >!--}
    {!--< /internal-use >!--}
    """
    t = f.type
    if isinstance(t, str):
        name = t.strip()
        resolved = None
        module_name = getattr(config_class, "__module__", None)
        module = sys.modules.get(module_name) if isinstance(module_name, str) else None

        # 解析命名空间链：类所在模块全局 → 沿 __qualname__ 逐级外层的类命名空间
        # （支持子配置类与 ConfigClass 同级声明在外层类中的写法）
        namespaces = []
        if module is not None:
            namespaces.append(vars(module))
            obj = module
            for part in getattr(config_class, "__qualname__", "").split(".")[:-1]:
                obj = vars(obj).get(part) if hasattr(obj, "__dict__") else None
                if obj is None:
                    break
                namespaces.append(vars(obj))
        namespaces.append(vars(config_class))

        for ns in namespaces:
            candidate = ns.get(name)
            if isinstance(candidate, type) and is_dataclass(candidate):
                resolved = candidate
                break
        t = resolved
    return t if (isinstance(t, type) and is_dataclass(t)) else None


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

    ``example`` 字段不落盘，故默认值字典同样排除；
    嵌套 dataclass 字段递归展开为普通字典。

    :param config_class: dataclass 类
    :return: 默认值字典
    """
    result = {}
    for f in fields(config_class):
        if f.name.startswith("_") or (f.metadata or {}).get("example", False):
            continue
        nested = _resolve_nested_dataclass(config_class, f)
        if nested is not None:
            result[f.name] = dataclass_to_defaults_dict(nested)
            continue
        if f.default is not MISSING:
            result[f.name] = f.default
        elif f.default_factory is not MISSING:
            result[f.name] = f.default_factory()
        else:
            type_default = _type_default(f.type)
            result[f.name] = type_default
    return result


def dataclass_to_toml_with_comments(
    config_class: type,
    existing_values: dict | None = None,
    include_example: bool = False,
    _prefix: str = "",
) -> str:
    """
    将 dataclass class 转为带注释的 TOML 文本

    用于首次写入配置文件时生成可读的配置模板。
    description 若为 i18n 字典，则使用其 default/fallback 文本；
    未声明 description 时自动回退到类 docstring 中的字段说明。
    嵌套 dataclass 字段渲染为 ``[子表]`` 节（递归，注释同样保留）。

    :param config_class: dataclass 类
    :param existing_values: 已有的配置值（覆盖默认值）
    :param include_example: 是否包含 ``example`` 字段（默认排除，
        example 字段仅进 config.full.example，不写入 config.toml）
    :param _prefix: 递归用：当前嵌套路径前缀（如 ``"stalker_mode."``）
    :return: TOML 文本字符串
    """
    if existing_values is None:
        existing_values = {}

    lines = []
    docstrings = get_field_docstrings(config_class)

    for f in fields(config_class):
        meta = f.metadata or {}
        # 下划线前缀字段（如误声明为普通字段的 _schema_meta）不是用户配置项，
        # 不进入模板/schema/默认值等任何用户可见输出
        if f.name.startswith("_"):
            continue
        if not include_example and meta.get("example", False):
            continue

        nested = _resolve_nested_dataclass(config_class, f)
        if nested is not None:
            nested_existing = existing_values.get(f.name)
            body = dataclass_to_toml_with_comments(
                nested,
                nested_existing if isinstance(nested_existing, dict) else None,
                include_example=include_example,
                _prefix=f"{_prefix}{f.name}.",
            )
            if body.strip():
                lines.append(f"[{_prefix}{f.name}]")
                lines.append(body)
            continue

        value = existing_values.get(f.name)
        if value is None:
            if f.default is not MISSING:
                value = f.default
            elif f.default_factory is not MISSING:
                value = f.default_factory()
            else:
                value = _type_default(f.type)

        is_secret = meta.get("secret", False)
        description = _resolve_description_text(meta, docstrings.get(f.name, ""))
        required = meta.get("required", False)

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
    - 嵌套 dataclass 字段递归填充（dict → 嵌套实例）

    :param config_class: dataclass 类
    :param data: 字典数据（通常来自 TOML 解析）
    :return: dataclass 实例
    """
    if data is None:
        data = {}

    kwargs = {}
    for f in fields(config_class):
        if f.name.startswith("_"):
            # 下划线前缀字段不是用户配置项，跳过（构造时走类默认值）
            continue

        nested = _resolve_nested_dataclass(config_class, f)
        if nested is not None:
            raw = data.get(f.name)
            kwargs[f.name] = dict_to_dataclass(
                nested, raw if isinstance(raw, dict) else {}
            )
            continue

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
        if f.name.startswith("_"):
            # 下划线前缀字段不是用户配置项，不参与校验
            continue
        nested = _resolve_nested_dataclass(type(instance), f)
        if nested is not None:
            # 嵌套 dataclass：递归校验，错误信息带路径前缀
            child = getattr(instance, f.name)
            if is_dataclass(child):
                errors.extend(
                    f"{f.name}: {sub_error}" for sub_error in validate_config(child)
                )
            continue
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


def _schema_fields(config_class: type) -> dict:
    """
    递归生成配置类的字段 schema（嵌套 dataclass 字段以 ``fields`` 子树承载）

    :param config_class: dataclass 类
    :return: {字段名: 字段 schema} 字典

    {!--< internal-use >!--}
    {!--< /internal-use >!--}
    """
    schema_fields = {}
    docstrings = get_field_docstrings(config_class)

    for f in fields(config_class):
        if f.name.startswith("_"):
            # 下划线前缀字段不是用户配置项，不进入 schema
            continue
        meta = f.metadata or {}
        ui_meta = _get_ui_meta(meta)

        nested = _resolve_nested_dataclass(config_class, f)
        if nested is not None:
            # 嵌套 dataclass：递归生成子字段树（type=table，面板渲染为嵌套分组）
            field_schema = {
                "type": "table",
                "description": _resolve_description_schema(meta, docstrings.get(f.name, "")),
                "required": meta.get("required", False),
                "secret": meta.get("secret", False),
                "default": dataclass_to_defaults_dict(nested),
                "fields": _schema_fields(nested),
            }
            if meta.get("example", False):
                field_schema["example"] = True
            _apply_ui_meta(field_schema, ui_meta)
            schema_fields[f.name] = field_schema
            continue

        field_schema = {
            "type": _python_type_to_toml_type(f.type),
            "description": _resolve_description_schema(meta, docstrings.get(f.name, "")),
            "required": meta.get("required", False),
            "secret": meta.get("secret", False),
            "default": _get_field_default(f),
        }

        if meta.get("example", False):
            field_schema["example"] = True

        _apply_ui_meta(field_schema, ui_meta)

        # 冗余扩展：透传 metadata 中的 "extra" 到 schema
        if "extra" in meta:
            field_schema["extra"] = meta["extra"]

        schema_fields[f.name] = field_schema

    return schema_fields


def _apply_ui_meta(field_schema: dict, ui_meta: dict) -> None:
    """{!--< internal-use >!--} 将 UI 元数据合并进字段 schema"""
    if "widget" in ui_meta:
        field_schema["widget"] = ui_meta["widget"]
    if "group" in ui_meta:
        field_schema["group"] = ui_meta["group"]
    if "order" in ui_meta:
        field_schema["order"] = ui_meta["order"]
    if "options" in ui_meta:
        field_schema["options"] = ui_meta["options"]
    if "placeholder" in ui_meta:
        field_schema["placeholder"] = ui_meta["placeholder"]


def get_config_schema(config_class: type) -> dict:
    """
    从 dataclass 生成 WebUI 可用的 JSON Schema

    包含字段名、类型、描述（支持 i18n）、控件类型、分组、排序等。
    description 若为 i18n 字典则原样透传，WebUI 根据语言键查找翻译；
    未声明 description 时自动回退到类 docstring 中的字段说明。
    ``example`` 字段在 schema 中带 ``"example": true`` 标记（供面板自行决定展示策略）。
    嵌套 dataclass 字段以 ``"type": "table"`` + ``"fields"`` 子树承载，
    面板可渲染为嵌套分组而非整棵平铺。

    :param config_class: dataclass 类
    :return: schema 字典
    """
    fields_dict = _schema_fields(config_class)
    # 顶层字段分组列表（嵌套子树自持分组，不外泄）
    groups = sorted(
        {fs["group"] for fs in fields_dict.values() if isinstance(fs, dict) and "group" in fs}
    )
    return {
        "fields": fields_dict,
        "groups": groups,
        "account_based": is_dataclass(config_class) and issubclass(config_class, BotAccountConfig),
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

    - 纯字符串原样返回
    - i18n 字典 ``{"i18n": "key", "default": "文本"}`` 解析为当前语言文本
    - 仅含 ``default`` 的字典 ``{"default": "文本"}``（语言无关文本，
      如动态生成的选项标签）解析为 default 文本

    :param value: 原始值（str 或 i18n 字典 / default 兜底字典）
    :param i18n_mgr: I18nManager 实例
    :return: 解析后的字符串
    """
    if isinstance(value, dict):
        if "i18n" in value:
            key = value["i18n"]
            default = value.get("default", key)
            return i18n_mgr.t(key, default=default)
        if "default" in value:
            return value["default"]
    return value


def _resolve_fields_i18n(fields_dict: dict) -> None:
    """{!--< internal-use >!--} 递归解析字段树中的 i18n 文本（含嵌套 dataclass 子树）"""
    for field_schema in fields_dict.values():
        if not isinstance(field_schema, dict):
            continue

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

        # 嵌套 dataclass 子树递归解析
        nested_fields = field_schema.get("fields")
        if isinstance(nested_fields, dict):
            _resolve_fields_i18n(nested_fields)


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

    嵌套 dataclass 字段子树同步解析。纯字符串值会被原样透传（向后兼容）。

    :param config_class: dataclass 配置类
    :param resolve_i18n: 是否将 i18n 文本解析为当前语言
    :return: schema 字典
    """
    schema = get_config_schema(config_class)

    if not resolve_i18n:
        return schema

    _resolve_fields_i18n(schema["fields"])

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
    "get_field_docstrings",
    "redact_secret",
    "register_config_i18n",
    "resolve_config_schema",
    "validate_config",
]
