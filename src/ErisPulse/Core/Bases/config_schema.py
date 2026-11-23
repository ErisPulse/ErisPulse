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
7. 通过 field(metadata={"env": "MYMODULE_API_KEY"}) 声明环境变量绑定：
   优先级 环境变量 > config.toml > 声明默认值（Docker / CI 场景免改配置文件）
8. 使用 dataclass_to_toml_with_comments() 生成带注释的配置模板
9. 使用 dict_to_dataclass() 从 TOML 字典填充 dataclass（含环境变量覆盖）
10. 使用 validate_config() 校验配置实例
11. 使用 get_config_schema() 生成 WebUI JSON Schema（含 i18n 支持）
12. 容器类型 ``list[T]`` / ``dict[str, T]`` 的成员类型进入 schema 的 ``item``；
    dict_to_dataclass() 加载时按成员类型规范化（标量转换 / dataclass 实例化），
    validate_config() 校验成员类型与嵌套约束
{!--< /tips >!--}
"""

import builtins
import inspect
import json
import os
import re
import sys
from collections.abc import Mapping
from dataclasses import MISSING, dataclass, field, fields, is_dataclass
from functools import cache
from types import NoneType, UnionType
from typing import Any, ClassVar, Optional, Union, get_args, get_origin

from ..constants import CONFIG_TEMPLATE_NESTED_TABLE_MAX_DEPTH
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
        for ns in _annotation_namespaces(config_class):
            candidate = ns.get(name)
            if isinstance(candidate, type) and is_dataclass(candidate):
                resolved = candidate
                break
        t = resolved
    return t if (isinstance(t, type) and is_dataclass(t)) else None


def _annotation_namespaces(config_class: type) -> "list[Mapping]":
    """
    字符串注解的解析命名空间链

    顺序：类所在模块全局 → 沿 ``__qualname__`` 逐级外层的类命名空间 → 类自身
    （子配置类与 ConfigClass 同级声明在外层类中时，短名经由该链解析）。

    :param config_class: 配置 dataclass 类
    :return: 命名空间映射列表（按解析优先级排列）
    """
    namespaces: list[Mapping] = []
    module_name = getattr(config_class, "__module__", None)
    module = sys.modules.get(module_name) if isinstance(module_name, str) else None
    if module is not None:
        namespaces.append(vars(module))
        obj = module
        for part in getattr(config_class, "__qualname__", "").split(".")[:-1]:
            obj = vars(obj).get(part) if hasattr(obj, "__dict__") else None
            if obj is None:
                break
            namespaces.append(vars(obj))
    namespaces.append(vars(config_class))
    return namespaces


def _eval_hint(type_hint, config_class: type):
    """
    求值 PEP 563 字符串注解为类型对象（非字符串注解原样返回）

    内置仅开放基础类型构造（:data:`_HINT_EVAL_GLOBALS`），其余名字取字段
    声明处的命名空间链（:func:`_annotation_namespaces`）。

    :param type_hint: 类型注解（类型对象或字符串）
    :param config_class: 字段所属配置类（字符串注解解析用）
    :return: 类型对象；求值失败返回 None
    """
    if not isinstance(type_hint, str):
        return type_hint
    namespace = dict(_HINT_EVAL_GLOBALS)
    for ns in _annotation_namespaces(config_class):
        namespace.update({key: value for key, value in ns.items() if key != "__builtins__"})
    try:
        return eval(type_hint, namespace)
    except Exception:
        return None


def _field_hint(config_class: type, f):
    """
    字段类型注解的类型对象形态（字符串注解求值，失败时返回原字符串）

    :param config_class: 字段所属配置类
    :param f: dataclass Field 对象
    :return: 类型对象或原字符串注解
    """
    evaluated = _eval_hint(f.type, config_class)
    return f.type if evaluated is None else evaluated


def _is_dataclass_type(obj) -> bool:
    """obj 是否为 dataclass 类（非实例）"""
    return isinstance(obj, type) and is_dataclass(obj)


def _container_spec(type_hint, config_class: type) -> tuple[str, Any] | None:
    """
    解析容器类型注解的成员类型

    联合类型（含 ``Optional``）取首个非 ``None`` 分支，与
    :func:`python_type_category` 同序。返回值：数组为 ``("array", 元素类型)``，
    动态键表为 ``("table", 值类型)``；未带类型参数的裸容器成员类型为 ``None``。

    :param type_hint: 类型注解（类型对象或字符串）
    :param config_class: 字段所属配置类（字符串注解解析用）
    :return: ``(容器类别, 成员类型)``；非容器或注解无法求值返回 None
    """
    hint = _eval_hint(type_hint, config_class)
    if hint is None:
        return None
    origin = get_origin(hint)
    if origin in (Union, UnionType):
        args = [arg for arg in get_args(hint) if arg is not NoneType]
        return _container_spec(args[0], config_class) if args else None
    if origin is list or hint is list:
        args = get_args(hint)
        return ("array", args[0] if args else None)
    if origin is dict or hint is dict:
        args = get_args(hint)
        return ("table", args[1] if len(args) == 2 else None)
    return None


def _plain(value) -> Any:
    """
    值的纯数据形态（dataclass 实例递归转字典）

    :param value: 任意值
    :return: 仅含 dict / list / 标量的等价值
    """
    if is_dataclass(value) and not isinstance(value, type):
        return {
            f.name: _plain(getattr(value, f.name))
            for f in fields(value)
            if not f.name.startswith("_")
        }
    if isinstance(value, list):
        return [_plain(item) for item in value]
    if isinstance(value, dict):
        return {key: _plain(item) for key, item in value.items()}
    return value


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


# PEP 563 字符串注解求值的受限命名空间（仅类型构造所需的最小集合，不暴露任意内置）
_HINT_EVAL_GLOBALS: dict[str, Any] = {
    "__builtins__": {
        name: getattr(builtins, name)
        for name in ("int", "float", "bool", "str", "bytes", "list", "dict", "tuple", "set")
    },
    "Any": Any,
    "Optional": Optional,
    "Union": Union,
    "List": list,
    "Dict": dict,
}


def python_type_category(type_hint: Any) -> str:
    """
    识别 Python 类型注解的类别（声明式字段层的类型映射同源注册表）

    配置层（TOML 类型映射 :func:`_python_type_to_toml_type`）与 ORM 层
    （SQL 方言列类型映射，见 ``Core/Bases/model.py``）从同一类别派生各自的
    目标类型——一份识别逻辑，两侧消费。

    结构化判定（``typing.get_origin`` / ``issubclass``）：参数化泛型
    （``list[int]`` / ``dict[str, int]``）按容器类别识别；``Optional[X]`` 与
    ``X | None`` 取首个非 ``None`` 参数递归；PEP 563 字符串注解（``from
    __future__ import annotations`` 下的 ``__annotations__`` 形态）在受限
    命名空间内求值后同样处理；无法识别的注解回落 ``"str"``。

    :param type_hint: Python 类型注解（类型对象、typing 形态或字符串注解）
    :return: 类别名（"int" / "float" / "bool" / "list" / "dict" / "str"）

    {!--< tips >!--}
    1. 新增受支持的注解类别时，本函数与两个下游映射需同步扩展
    {!--< /tips >!--}
    """
    if isinstance(type_hint, str):
        try:
            type_hint = eval(type_hint, _HINT_EVAL_GLOBALS)
        except Exception:
            return "str"
    origin = get_origin(type_hint)
    if origin is not None:
        if origin is list:
            return "list"
        if origin is dict:
            return "dict"
        if origin in (Union, UnionType):
            args = [arg for arg in get_args(type_hint) if arg is not NoneType]
            if args:
                return python_type_category(args[0])
        return "str"
    if isinstance(type_hint, type):
        if issubclass(type_hint, bool):  # bool 是 int 子类，须先于 int 判定
            return "bool"
        if issubclass(type_hint, int):
            return "int"
        if issubclass(type_hint, float):
            return "float"
        if issubclass(type_hint, str):
            return "str"
        if issubclass(type_hint, list):
            return "list"
        if issubclass(type_hint, dict):
            return "dict"
    return "str"


def _python_type_to_toml_type(type_hint) -> str:
    """
    将 Python 类型注解转为 TOML 类型字符串

    {!--< internal-use >!--}
    {!--< /internal-use >!--}

    :param type_hint: Python 类型注解
    :return: TOML 类型名（integer/float/boolean/array/table/string）
    """
    return {
        "int": "integer",
        "float": "float",
        "bool": "boolean",
        "list": "array",
        "dict": "table",
        "str": "string",
    }[python_type_category(type_hint)]


# None 默认值的 TOML 占位表（键 = python_type_category 类别）
_TOML_NULL_PLACEHOLDERS = {
    "int": "0",
    "float": "0.0",
    "bool": "false",
    "str": '""',
    "list": "[]",
    "dict": "{}",
}


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


def dataclass_to_defaults_dict(config_class: type, _seen: tuple[type, ...] = ()) -> dict:
    """
    从 dataclass 类生成默认值字典

    ``example`` 字段不落盘，故默认值字典同样排除；
    嵌套 dataclass 字段递归展开为普通字典；容器默认值中的 dataclass 实例转为字典。

    :param config_class: dataclass 类
    :param _seen: 递归用：当前路径上已展开的 dataclass 类（自引用类型不重复展开）
    :return: 默认值字典（仅含 dict / list / 标量）
    """
    if config_class in _seen:
        return {}
    result = {}
    for f in fields(config_class):
        if f.name.startswith("_") or (f.metadata or {}).get("example", False):
            continue
        nested = _resolve_nested_dataclass(config_class, f)
        if nested is not None:
            result[f.name] = dataclass_to_defaults_dict(nested, _seen + (config_class,))
            continue
        if f.default is not MISSING:
            result[f.name] = f.default
        elif f.default_factory is not MISSING:
            result[f.name] = f.default_factory()
        else:
            result[f.name] = _type_default(f.type)
    return _plain(result)


def _toml_key(key) -> str:
    """
    键名的 TOML 字面形式（含 ``[A-Za-z0-9_-]`` 之外字符时加双引号）

    :param key: 键名
    :return: TOML 键字面量
    """
    text = str(key)
    return text if re.fullmatch(r"[A-Za-z0-9_-]+", text) else json.dumps(text)


def _toml_table_blocks(
    name: str,
    kind: str,
    item_type: type,
    value,
    include_example: bool,
    prefix: str,
    depth: int,
) -> "list[str]":
    """
    元素 / 值类型为 dataclass 的容器字段的 TOML 行

    有元素时每个元素输出一个 ``[[表数组]]``（数组）或 ``[表.键]``（动态键表）
    块；无元素或嵌套层数达上限时输出注释骨架。空值不落 ``键 = []``——静态
    数组与后续 ``[[键]]`` 追加互斥，落盘后用户无法再以表数组形式追加元素。

    :param name: 字段名
    :param kind: 容器类别（``"array"`` / ``"table"``）
    :param item_type: 元素 / 值的 dataclass 类
    :param value: 字段当前值（元素为字典或 dataclass 实例）
    :param include_example: 是否包含 ``example`` 字段
    :param prefix: 当前嵌套路径前缀
    :param depth: 当前嵌套表层数
    :return: 行列表（以空行结尾）
    """
    base = f"{prefix}{name}"
    items = []
    if kind == "array" and isinstance(value, (list, tuple)):
        items = [(f"[[{base}]]", f"{base}.", item) for item in value]
    elif kind == "table" and isinstance(value, dict):
        items = [
            (f"[{base}.{_toml_key(key)}]", f"{base}.{_toml_key(key)}.", item)
            for key, item in value.items()
        ]

    if depth >= CONFIG_TEMPLATE_NESTED_TABLE_MAX_DEPTH:
        header = f"[[{base}]]" if kind == "array" else f"[{base}.<key>]"
        return [f"# {header}", ""]
    if items:
        lines = []
        for header, item_prefix, item in items:
            lines.append(header)
            item_value = _plain(item)
            lines.append(
                dataclass_to_toml_with_comments(
                    item_type,
                    item_value if isinstance(item_value, dict) else None,
                    include_example=include_example,
                    _prefix=item_prefix,
                    _depth=depth + 1,
                )
            )
        return lines

    header = f"[[{base}]]" if kind == "array" else f"[{base}.<key>]"
    body = dataclass_to_toml_with_comments(
        item_type,
        None,
        include_example=include_example,
        _prefix=f"{base}.",
        _depth=depth + 1,
    )
    raw = [header, *body.rstrip("\n").split("\n")]
    return [f"# {line}" if line else "#" for line in raw] + [""]


def dataclass_to_toml_with_comments(
    config_class: type,
    existing_values: dict | None = None,
    include_example: bool = False,
    _prefix: str = "",
    _depth: int = 0,
) -> str:
    """
    将 dataclass class 转为带注释的 TOML 文本

    用于首次写入配置文件时生成可读的配置模板。
    description 若为 i18n 字典，则使用其 default/fallback 文本；
    未声明 description 时自动回退到类 docstring 中的字段说明。
    嵌套 dataclass 字段渲染为 ``[子表]`` 节（递归，注释同样保留）；
    元素 / 值类型为 dataclass 的容器（``list[T]`` / ``dict[str, T]``）渲染为
    ``[[表数组]]`` / ``[表.键]`` 块，无元素时输出注释骨架。

    :param config_class: dataclass 类
    :param existing_values: 已有的配置值（覆盖默认值）
    :param include_example: 是否包含 ``example`` 字段（默认排除，
        example 字段仅进 config.full.example，不写入 config.toml）
    :param _prefix: 递归用：当前嵌套路径前缀（如 ``"stalker_mode."``）
    :param _depth: 递归用：当前嵌套表层数（上限
        ``CONFIG_TEMPLATE_NESTED_TABLE_MAX_DEPTH``）
    :return: TOML 文本字符串
    """
    if existing_values is None:
        existing_values = {}

    # 两段式渲染：裸键（key = value）先行、表块（[子表] / [[表数组]]）殿后——
    # TOML 语义中表头之后的所有裸键归属该表，同级标量必须先于表头输出
    bare_lines: list[str] = []
    table_lines: list[str] = []
    docstrings = get_field_docstrings(config_class)

    for f in fields(config_class):
        meta = f.metadata or {}
        # 下划线前缀字段（如误声明为普通字段的 _schema_meta）不是用户配置项，
        # 不进入模板/schema/默认值等任何用户可见输出
        if f.name.startswith("_"):
            continue
        if not include_example and meta.get("example", False):
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

        # 字段头注释（描述 + 环境变量提示）随所属渲染段走：
        # 标量段入裸键区，容器/嵌套表段入表块区（TOML 表头语义）
        header_lines: list[str] = []
        if description:
            suffix = i18n.t("core.config.required_suffix") if required else ""
            header_lines.append(f"# {description}{suffix}")
        env_name = meta.get("env")
        if isinstance(env_name, str) and env_name:
            header_lines.append(f"# {i18n.t('core.config.env_hint', env=env_name)}")

        nested = _resolve_nested_dataclass(config_class, f)
        if nested is not None:
            if _depth >= CONFIG_TEMPLATE_NESTED_TABLE_MAX_DEPTH:
                table_lines.extend(header_lines)
                table_lines.append(f"# [{_prefix}{f.name}]")
                table_lines.append("")
                continue
            nested_existing = existing_values.get(f.name)
            body = dataclass_to_toml_with_comments(
                nested,
                nested_existing if isinstance(nested_existing, dict) else None,
                include_example=include_example,
                _prefix=f"{_prefix}{f.name}.",
                _depth=_depth + 1,
            )
            if body.strip():
                table_lines.extend(header_lines)
                table_lines.append(f"[{_prefix}{f.name}]")
                table_lines.append(body)
            continue

        # 元素 / 值类型为 dataclass 的容器：[[表数组]] / [表.键] 块
        container = _container_spec(f.type, config_class)
        if container is not None and _is_dataclass_type(container[1]):
            table_lines.extend(header_lines)
            table_lines.extend(
                _toml_table_blocks(
                    f.name,
                    container[0],
                    container[1],
                    value,
                    include_example,
                    _prefix,
                    _depth,
                )
            )
            continue

        bare_lines.extend(header_lines)

        # secret 字段不把真实值写入模板文件，避免配置文件泄露敏感信息
        effective_value = _plain(value)
        if is_secret and effective_value not in ("", None, [], {}):
            effective_value = ""
        if effective_value is None:
            # None 默认值的 TOML 渲染：TOML 无 null，按字段类别取占位——
            # 字符串/容器渲染空值（即未设置语义），标量注释占位（赋值后生效）
            category = python_type_category(_field_hint(config_class, f))
            placeholder = _TOML_NULL_PLACEHOLDERS[category]
            if category in ("int", "float", "bool"):
                bare_lines.append(f"# {f.name} = {placeholder}")
            else:
                bare_lines.append(f"{f.name} = {placeholder}")
        else:
            toml_value = _format_toml_value(effective_value)
            if required and effective_value in ("", 0, 0.0, False, [], {}):
                bare_lines.append(f"# {f.name} = {toml_value}")
            else:
                bare_lines.append(f"{f.name} = {toml_value}")

        bare_lines.append("")

    return "\n".join(bare_lines + table_lines)


def _env_override_value(f):
    """
    读取字段声明的环境变量覆盖值（``metadata: {"env": "NAME"}``）

    {!--< internal-use >!--}
    优先级：环境变量 > config.toml > 声明默认值。环境变量值为字符串，
    按字段注解转换——``int`` / ``float`` / ``bool`` 复用 :func:`_coerce_value`，
    ``list`` / ``dict`` 走 JSON 解析，``str`` 原样。转换失败（如整型字段
    收到非数字）时输出警告并回退（视为未覆盖）。

    :param f: dataclass Field 对象
    :return: 覆盖值；未声明 env / 环境变量不存在 / 转换失败时返回 MISSING
    """
    env_name = (f.metadata or {}).get("env")
    if not isinstance(env_name, str) or not env_name:
        return MISSING
    raw = os.environ.get(env_name)
    if raw is None or raw == "":
        return MISSING

    # 类型判定与模板/校验共用 python_type_category（结构化判定）：
    # 字符串子串匹配会把 Literal["list", ...] 等注解误判为 JSON 列
    category = python_type_category(f.type)
    logger = _get_config_logger()
    try:
        if category in ("list", "dict"):
            value = json.loads(raw)
            if not isinstance(value, (list, dict)):
                raise ValueError(raw[:50])
        else:
            value = _coerce_value(raw, f.type)
            # 转换后类型必须匹配注解（_coerce_value 失败时原样返回字符串）
            if category == "bool" and not isinstance(value, bool):
                raise ValueError(raw[:50])
            if category == "int" and (isinstance(value, bool) or not isinstance(value, int)):
                raise ValueError(raw[:50])
            if category == "float" and (isinstance(value, bool) or not isinstance(value, (int, float))):
                raise ValueError(raw[:50])
        return value
    except (ValueError, TypeError) as e:
        logger.warning(i18n.t("core.config.env_convert_failed", env=env_name, value=raw[:50], error=e))
        return MISSING


def _get_config_logger():
    """{!--< internal-use >!--} 延迟获取日志器（避免循环依赖）"""
    from ..logger import logger

    return logger


def _normalize_scalar(value, type_hint):
    """
    标量成员的类型规范化（str→int/float/bool）

    :param value: 原始值
    :param type_hint: 目标类型
    :return: 转换后的值（转换失败时返回原值）
    """
    if is_dataclass(type_hint) and isinstance(type_hint, type):
        return value
    if isinstance(value, str):
        return _coerce_value(value, type_hint)
    if value is None:
        return None
    hint = str(type_hint).lower()
    if "bool" in hint and isinstance(value, (int, float)):
        return bool(value)
    if "int" in hint and "bool" not in hint and isinstance(value, float) and value.is_integer():
        return int(value)
    if "float" in hint and isinstance(value, int) and not isinstance(value, bool):
        return float(value)
    return value


def _normalize_container_members(value, kind: str, member_hint, config_class: type):
    """
    容器成员的声明类型规范化

    数组元素 / 动态键表值按成员类型转换：标量做类型转换（含标量包装——
    面板布尔控件等输入 ``"true"`` 字符串时按注解还原），dataclass 成员实例化
    （非 dict 元素包装为首个字段，与 Dashboard 列表编辑器的标量行形态对齐）。
    字符串整体值为 JSON 容器文本时先解析。未带成员类型的容器原样返回。

    :param value: 容器值（list / dict；其他原样返回）
    :param kind: 容器类别（``"array"`` / ``"table"``）
    :param member_hint: 成员类型注解（None = 未声明）
    :param config_class: 字段所属配置类（字符串注解解析用）
    :return: 规范化后的值（dataclass 成员为实例）
    """
    if member_hint is None:
        return value
    hint = _eval_hint(member_hint, config_class)

    if isinstance(value, str):
        # 字符串整体值为 JSON 容器文本时先解析（面板 JSON 编辑态 / env 覆盖）
        try:
            parsed = json.loads(value)
        except (ValueError, TypeError):
            return value
        if not isinstance(parsed, (list, dict)):
            return value
        value = parsed
    if not isinstance(value, (list, dict)):
        return value

    if is_dataclass(hint) and isinstance(hint, type):
        if kind == "array":
            if not isinstance(value, list):
                return value
            items = []
            for item in value:
                if isinstance(item, dict):
                    items.append(dict_to_dataclass(hint, item))
                elif item is None:
                    continue
                else:
                    fields_list = [f for f in fields(hint) if not f.name.startswith("_")]
                    if fields_list:
                        items.append(dict_to_dataclass(hint, {fields_list[0].name: item}))
            return items
        if not isinstance(value, dict):
            return value
        return {
            key: dict_to_dataclass(hint, item) if isinstance(item, dict) else item
            for key, item in value.items()
        }

    if kind == "array":
        if not isinstance(value, list):
            return value
        return [_normalize_scalar(item, hint) for item in value]
    if not isinstance(value, dict):
        return value
    return {key: _normalize_scalar(item, hint) for key, item in value.items()}


def dict_to_dataclass(config_class: type, data: dict):
    """
    从 TOML dict 填充 dataclass 实例

    - 处理类型转换（str → int 等）
    - 忽略 dataclass 中不存在的字段
    - 使用 default/default_factory 填充缺失字段
    - 嵌套 dataclass 字段递归填充（dict → 嵌套实例）
    - 容器字段（``list[T]`` / ``dict[str, T]``）按成员类型规范化
      （标量转换 / dataclass 实例化 / JSON 字符串解析）
    - 环境变量覆盖（``metadata: {"env": "NAME"}``）：优先级 环境变量 > data > default

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

        # 环境变量覆盖优先于 data 与 default（声明一处、处处生效）
        env_value = _env_override_value(f)
        if env_value is not MISSING:
            kwargs[f.name] = env_value
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
            container = _container_spec(f.type, config_class)
            if container is not None:
                kwargs[f.name] = _normalize_container_members(
                    raw_value, container[0], container[1], config_class
                )
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


def validate_field_constraints(
    label: str,
    value: Any,
    *,
    required: bool = False,
    choices: "list | tuple | None" = None,
    min_value: "int | float | None" = None,
    max_value: "int | float | None" = None,
    max_length: "int | None" = None,
) -> "list[str]":
    """
    字段约束校验共享引擎（声明式字段层的校验器同源实现）

    配置写入校验（:func:`validate_config` 的约束步骤）与 ORM 插入/更新
    校验（``Core/Bases/model.py``）共用同一判定语义：required 非空、
    枚举、数值范围、字符串长度。参数由各消费方从自己的声明形态解析
    （config 从 metadata/ui 元数据，ORM 从 Field 参数）。

    :param label: 字段标签（错误信息定位用，如字段名）
    :param value: 待校验的值
    :param required: 是否必填（非空）
    :param choices: 枚举选项（None 不校验）
    :param min_value: 数值下界（None 不校验）
    :param max_value: 数值上界（None 不校验）
    :param max_length: 字符串最大长度（None 不校验）
    :return: 本地化错误列表（空列表 = 通过）

    {!--< tips >!--}
    1. 空值（None/空串/空容器）跳过除 required 外的全部检查——与
       validate_config 的既有语义一致
    {!--< /tips >!--}
    """
    errors: list[str] = []

    is_empty = value is None or (isinstance(value, str) and not value.strip()) or (
        isinstance(value, (list, dict)) and len(value) == 0
    )
    if is_empty:
        if required:
            errors.append(i18n.t("core.config.field_required_empty", field=label, desc=label))
        return errors

    if choices:
        plain_opts = [o.get("value") if isinstance(o, dict) else o for o in choices]
        if value not in plain_opts:
            errors.append(i18n.t("core.config.field_option_invalid", field=label, value=value))

    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if min_value is not None and value < min_value:
            errors.append(i18n.t("core.config.field_below_min", field=label, value=value, min=min_value))
        if max_value is not None and value > max_value:
            errors.append(i18n.t("core.config.field_above_max", field=label, value=value, max=max_value))

    if max_length is not None and isinstance(value, str) and len(value) > max_length:
        errors.append(
            i18n.t("core.config.field_too_long", field=label, length=len(value), max=max_length)
        )

    return errors


def _file_comment_suffix(section_key: "str | None", field_path: str) -> str:
    """
    取配置文件中字段行尾注释并格式化为错误消息后缀（"文件即文档"回读）

    声明式字段的 description 以注释落盘后，配置文件本身就是用户眼前的
    文档；校验失败时引用文件里的原文比 schema 元数据更贴近用户所见。
    按需无损解析配置文件，任何失败静默返回空串（注释是增强信息，
    不允许拖垮校验主流程）。

    :param section_key: str 配置节键（点分路径）；None 表示调用方未提供
        节上下文，跳过回读
    :param field_path: str 节内字段路径（点分，嵌套字段含祖先路径）
    :return: str 形如 ``" （配置文件注释：…）"`` 的后缀；无注释返回空串

    {!--< internal-use >!--}
    {!--< /internal-use >!--}
    """
    if not section_key:
        return ""
    try:
        from ..config import config as _config

        comment_text = _config.get_field_comment(section_key, field_path)
    except Exception:
        return ""
    if not comment_text:
        return ""
    return " " + i18n.t("core.config.file_comment_suffix", comment=comment_text)


def validate_config(instance, section_key: "str | None" = None) -> list[str]:
    """
    校验 dataclass 实例

    - 检查 ``required`` 字段是否非空
    - 检查字段值类型是否与声明一致（int/float/str/bool）
    - 检查 ``options`` 枚举约束（值是否在允许选项内）
    - 检查 ``min``/``max`` 数值范围约束

    返回错误信息列表（空列表表示通过）。description 若为 i18n 字典，
    错误信息使用其 fallback/default 文本。传入 ``section_key`` 时，
    配置文件中该字段的行尾注释（如有）会附在对应错误消息之后。

    :param instance: dataclass 实例
    :param section_key: str 实例对应的配置节键（点分路径，如
        ``"MyAdapter"``）；传入后启用文件注释回读（默认 None 不回读）
    :return: 错误信息列表
    """
    return _validate_config(instance, section_key, "")


def _validate_config(instance, section_key: "str | None", prefix: str) -> list[str]:
    """
    :meth:`validate_config` 的递归实现

    :param instance: dataclass 实例
    :param section_key: str 配置节键（透传，用于文件注释回读）
    :param prefix: str 嵌套字段的路径前缀（如 ``"Nested."``）

    {!--< internal-use >!--}
    {!--< /internal-use >!--}
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
                    f"{f.name}: {sub_error}"
                    for sub_error in _validate_config(child, section_key, f"{prefix}{f.name}.")
                )
            continue
        meta = f.metadata or {}
        value = getattr(instance, f.name)
        ui_meta = _get_ui_meta(meta) if meta else {}
        comment_suffix = _file_comment_suffix(section_key, f"{prefix}{f.name}")

        # 容器字段（list[T] / dict[str, T]）：成员类型与 dataclass 成员约束
        container = _container_spec(f.type, type(instance))
        if container is not None:
            kind, member_hint = container
            if isinstance(value, (list, dict)) and member_hint is not None:
                member_evaluated = _eval_hint(member_hint, type(instance))
                if member_evaluated is None:
                    continue
                if _is_dataclass_type(member_evaluated):
                    members = (
                        list(enumerate(value))
                        if kind == "array" and isinstance(value, list)
                        else list(value.items())
                        if isinstance(value, dict)
                        else []
                    )
                    for key, item in members:
                        label = f"{f.name}[{key}]" if kind == "array" else f"{f.name}.{key}"
                        if isinstance(item, member_evaluated):
                            errors.extend(
                                f"{label}: {sub_error}"
                                for sub_error in _validate_config(
                                    item, section_key, f"{prefix}{label}."
                                )
                            )
                        elif isinstance(item, dict):
                            errors.extend(
                                f"{label}: {sub_error}"
                                for sub_error in _validate_config(
                                    dict_to_dataclass(member_evaluated, item),
                                    section_key,
                                    f"{prefix}{label}.",
                                )
                            )
                        else:
                            errors.append(
                                i18n.t(
                                    "core.config.field_type_mismatch",
                                    field=label,
                                    expected=member_evaluated.__name__,
                                    actual=type(item).__name__,
                                )
                                + comment_suffix
                            )
                else:
                    member_name = getattr(member_evaluated, "__name__", str(member_evaluated))
                    expected = _type_map.get(member_name.lower().strip("'"))
                    if expected is not None and kind == "array" and isinstance(value, list):
                        for idx, item in enumerate(value):
                            ok = isinstance(item, expected) and not (
                                expected is int and isinstance(item, bool)
                            )
                            if not ok:
                                errors.append(
                                    i18n.t(
                                        "core.config.field_type_mismatch",
                                        field=f"{f.name}[{idx}]",
                                        expected=member_name,
                                        actual=type(item).__name__,
                                    )
                                    + comment_suffix
                                )
            continue
        meta = f.metadata or {}
        value = getattr(instance, f.name)
        ui_meta = _get_ui_meta(meta) if meta else {}
        comment_suffix = _file_comment_suffix(section_key, f"{prefix}{f.name}")

        # 1. required 非空（需要 metadata 声明）
        if meta.get("required", False) and _is_empty(value):
            desc_text = _resolve_description_text(meta) or f.name
            errors.append(
                i18n.t("core.config.field_required_empty", field=f.name, desc=desc_text) + comment_suffix
            )
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
                + comment_suffix
            )

        # 3. 枚举选项（options 可在 ui 子表或 metadata 顶层）
        options = ui_meta.get("options") or meta.get("options")
        if options:
            plain_opts = [
                o.get("value") if isinstance(o, dict) else o for o in options
            ]
            if value not in plain_opts:
                errors.append(
                    i18n.t("core.config.field_option_invalid", field=f.name, value=value)
                    + comment_suffix
                )

        # 4. 数值范围
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            min_val = ui_meta.get("min") if ui_meta else None
            max_val = ui_meta.get("max") if ui_meta else None
            if min_val is None:
                min_val = meta.get("min")
            if max_val is None:
                max_val = meta.get("max")
            if min_val is not None and value < min_val:
                errors.append(
                    i18n.t("core.config.field_below_min", field=f.name, value=value, min=min_val)
                    + comment_suffix
                )
            if max_val is not None and value > max_val:
                errors.append(
                    i18n.t("core.config.field_above_max", field=f.name, value=value, max=max_val)
                    + comment_suffix
                )

    return errors


def _item_schema(member_hint, config_class: type) -> dict | None:
    """
    容器成员的 schema 形态（Dashboard list 控件的 ``item`` 契约）

    dataclass 成员 → ``{"type": "object", "fields": {...}}``（行内多字段对象行）；
    标量成员 → 该标量的单字段 schema（标量行）；无成员类型声明返回 None。

    :param member_hint: 成员类型注解（可为 None）
    :param config_class: 字段所属配置类（字符串注解解析用）
    :return: 成员 schema 字典；无成员类型返回 None
    """
    hint = _eval_hint(member_hint, config_class) if member_hint is not None else None
    if hint is None:
        return None
    if _is_dataclass_type(hint):
        return {"type": "object", "fields": _schema_fields(hint)}
    # 标量成员：单字段形态（复用字段 schema 的构造路径）
    fake_field = _ItemField(hint)
    return _scalar_schema_fields(fake_field, fake_field.metadata or {})


class _ItemField:
    """list 控件标量成员的伪 Field（schema 渲染用）"""

    def __init__(self, type_hint):
        self.name = "item"
        self.type = type_hint
        self.metadata = {}
        self.default = MISSING
        self.default_factory = MISSING


def _scalar_schema_fields(f, meta: Mapping) -> dict:
    """
    单字段的非嵌套 schema 构造（:func:`_schema_fields` 的标量分支复用体）

    :param f: dataclass Field 对象
    :param meta: 字段 metadata
    :return: 字段 schema 字典
    """
    field_schema = {
        "type": _python_type_to_toml_type(f.type),
        "description": _resolve_description_schema(meta, ""),
        "required": meta.get("required", False),
        "secret": meta.get("secret", False),
        "default": _get_field_default(f),
    }
    _apply_ui_meta(field_schema, _get_ui_meta(meta))
    return field_schema


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
            "type": _python_type_to_toml_type(_field_hint(config_class, f)),
            "description": _resolve_description_schema(meta, docstrings.get(f.name, "")),
            "required": meta.get("required", False),
            "secret": meta.get("secret", False),
            "default": _get_field_default(f),
        }

        if meta.get("example", False):
            field_schema["example"] = True

        # 环境变量绑定声明（面板可据此提示"支持环境变量覆盖"）
        env_name = meta.get("env")
        if isinstance(env_name, str) and env_name:
            field_schema["env"] = env_name

        # 类型化容器：成员类型进入 item（Dashboard list 控件的行内 schema）；
        # 未显式声明 widget 的数组缺省 list 控件（行内按 item schema 渲染）
        container = _container_spec(f.type, config_class)
        if container is not None:
            item_schema = _item_schema(container[1], config_class)
            if item_schema is not None and "item" not in ui_meta:
                field_schema["item"] = item_schema
            if (
                container[0] == "array"
                and item_schema is not None
                and not ui_meta.get("widget")
            ):
                field_schema["widget"] = "list"

        _apply_ui_meta(field_schema, ui_meta)

        # 冗余扩展：透传 metadata 中的 "extra" 到 schema
        if "extra" in meta:
            field_schema["extra"] = meta["extra"]

        schema_fields[f.name] = field_schema

    return schema_fields


def _apply_ui_meta(field_schema: dict, ui_meta: dict) -> None:
    """{!--< internal-use >!--} 将 UI 元数据合并进字段 schema

    键集合以框架规范《配置与 UI 元数据》为准
    （docs/zh-CN/developer-guide/configuration.md）：widget / group / order /
    options / placeholder / min / max / step / rows / presets / show_if /
    disabled_if / value_type / item。框架原样透传，语义（控件行为、值形态、
    条件算子、兼容性契约）由规范定义，消费方（Dashboard 等）实现。
    """
    _UI_META_PASSTHROUGH_KEYS = (
        "widget",
        "group",
        "order",
        "options",
        "placeholder",
        # 满血组件系统扩展键
        "min",
        "max",
        "step",
        "rows",
        "presets",
        "show_if",
        "disabled_if",
        "value_type",
        "item",
    )
    for key in _UI_META_PASSTHROUGH_KEYS:
        if key in ui_meta:
            field_schema[key] = ui_meta[key]


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

        # 容器成员子树（list 控件行内 schema）递归解析
        item_schema = field_schema.get("item")
        if isinstance(item_schema, dict):
            item_fields = item_schema.get("fields")
            if isinstance(item_fields, dict):
                _resolve_fields_i18n(item_fields)
            else:
                item_schema["description"] = _resolve_i18n_text(
                    item_schema.get("description", ""), i18n
                )
                if "placeholder" in item_schema:
                    item_schema["placeholder"] = _resolve_i18n_text(
                        item_schema["placeholder"], i18n
                    )
                item_options = item_schema.get("options")
                if isinstance(item_options, list):
                    item_schema["options"] = [
                        dict(o, label=_resolve_i18n_text(o["label"], i18n))
                        if isinstance(o, dict) and "label" in o
                        else o
                        for o in item_options
                    ]

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
