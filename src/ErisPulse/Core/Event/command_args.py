"""
ErisPulse 命令参数与选项解析模块

为 ``@command(args=..., options=...)`` 提供声明式参数解析：

- ``args=`` 声明位置参数：``<count:int>``（必填）、``[sides:int=6]``（可选含默认值）。
  类型支持 ``str`` / ``int`` / ``float`` / ``bool`` / ``literal``（枚举，``<mode:literal=fast|slow>``，
  可选形式默认取首个枚举值）/ ``duration``（如 ``90s``、``1h30m``，按秒折算为 float）/
  ``rest``（剩余全部文本，必须位于最后）
- ``options=`` 字典式声明选项：键为处理器参数名，值为旗标形式。``bool`` 注解的参数
  为布尔旗标（如 ``"-v/--verbose"``）；其余（缺省按 ``str``）为带值选项，支持
  ``--label hello`` 与 ``--label=hello`` 两种取值形式
- 解析顺序：选项先被识别剔除，剩余 token 再交给 ``args=`` 解析（``rest`` 覆盖剔除选项后的剩余文本）
- 声明在注册期解析并校验（语法错误 / 处理器签名不匹配直接抛 ValueError，fail-fast）；
  用户输入在分发期解析，失败抛出 :class:`CommandArgsError`（携带 i18n 键与插值参数），
  由命令分发层自动回复本地化错误提示

{!--< tips >!--}
1. 未声明 ``args=`` / ``options=`` 的命令行为完全不变（向后兼容）
2. 本模块为命令系统内部实现（``Core/Event/command.py`` 消费），不属公共 API
{!--< /tips >!--}
"""

import inspect
import re
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from ..constants import COMMAND_ARG_DURATION_UNITS, CONFIRM_NO_WORDS, CONFIRM_YES_WORDS
from ..i18n import i18n

# args= 声明条目：<...> 必填 / [...] 可选（默认值可含空格，故用正则整体提取条目）
_SPEC_ENTRY_RE = re.compile(r"<([^<>]+)>|\[([^\[\]]+)\]")
# duration 取值：1~n 段 "数值+单位"（大小写不敏感），如 90s / 1h30m / 1d
_DURATION_RE = re.compile(r"(\d+(?:\.\d+)?)([smhd])", re.IGNORECASE)
_DURATION_FULL_RE = re.compile(r"(?:\d+(?:\.\d+)?[smhd])+", re.IGNORECASE)
# 选项参数名须为合法 Python 标识符
_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
# 类数字 token（含负数 / 小数）：即使以 - 开头也视为取值而非选项
_NUMBER_LIKE_RE = re.compile(r"^-?\d+(?:\.\d+)?$")

# 位置参数支持的类型集合（rest 有专属位置规则，单独校验）
_POSITIONAL_TYPES = frozenset({"str", "int", "float", "bool", "literal", "duration", "rest"})
# 选项支持的注解类型集合（bool 为布尔旗标，其余为带值选项）
_OPTION_TYPES = frozenset({"str", "int", "float", "bool"})


@dataclass(frozen=True)
class PositionalArg:
    """args= 声明的单个位置参数（注册期解析产物）"""

    name: str
    type: str
    required: bool
    default: Any = None
    choices: tuple[str, ...] | None = None
    # 注册期声明的默认值原文（usage 展示用，如 "1d" / "6"）
    default_display: str = ""


@dataclass(frozen=True)
class OptionArg:
    """options= 声明的单个选项（注册期解析产物）"""

    name: str
    forms: tuple[str, ...]
    # "flag" 布尔旗标 / "value" 带值选项
    kind: str
    type: str
    default: Any = None


class CommandArgsError(Exception):
    """
    {!--< internal-use >!--}
    命令参数解析错误（用户输入侧）

    携带 i18n 键与插值参数，由命令分发层捕获后自动回复本地化错误提示；
    ``str(exception)`` 即本地化后的完整错误文本。
    """

    def __init__(self, key: str, **params: Any):
        self.key = key
        self.params = params
        super().__init__(i18n.t(key, **params))

    def __str__(self) -> str:
        return i18n.t(self.key, **self.params)


def _bool_value(raw: str, arg_name: str = "?") -> bool:
    """
    {!--< internal-use >!--}
    将用户输入 token 转换为布尔值

    复用交互式确认（``Event.confirm()``）维护的确认词表
    (:data:`~ErisPulse.Core.constants.CONFIRM_YES_WORDS` /
    :data:`~ErisPulse.Core.constants.CONFIRM_NO_WORDS`，zh/en/ja/ru），
    与交互确认同一判定口径、同一维护来源。

    :param raw: 用户输入的原始 token
    :param arg_name: 参数名（错误提示用，缺省为 "?"）
    :return: 转换后的布尔值
    :raises CommandArgsError: token 不在确认词表内
    """
    lowered = raw.strip().lower()
    if lowered in CONFIRM_YES_WORDS:
        return True
    if lowered in CONFIRM_NO_WORDS:
        return False
    raise CommandArgsError("core.command.args.invalid", arg=arg_name, type="bool", value=raw)


def _duration_value(raw: str) -> float:
    """
    {!--< internal-use >!--}
    将时长 token（如 ``90s``、``1h30m``）转换为秒数

    :param raw: 用户输入的原始 token
    :return: 折算后的秒数（float）
    :raises CommandArgsError: 格式不合法或包含未知单位
    """
    text = raw.strip()
    if not _DURATION_FULL_RE.fullmatch(text):
        raise CommandArgsError("core.command.args.invalid", arg="?", type="duration", value=raw)
    total = 0.0
    for value, unit in _DURATION_RE.findall(text):
        total += float(value) * COMMAND_ARG_DURATION_UNITS[unit.lower()]
    return total


def _convert_value(type_name: str, raw: str, arg_name: str, choices: tuple[str, ...] | None = None) -> Any:
    """
    {!--< internal-use >!--}
    按声明类型转换单个 token（分发期转换入口）

    :param type_name: 声明的类型名（str/int/float/bool/literal/duration）
    :param raw: 用户输入的原始 token
    :param arg_name: 参数名（错误提示用）
    :param choices: literal 类型的枚举值（其余类型为 None）
    :return: 转换后的值
    :raises CommandArgsError: 转换失败（携带本地化错误键）
    """
    try:
        if type_name == "int":
            return int(raw)
        if type_name == "float":
            return float(raw)
        if type_name == "bool":
            return _bool_value(raw, arg_name)
        if type_name == "duration":
            return _duration_value(raw)
        if type_name == "literal":
            if choices and raw in choices:
                return raw
            raise CommandArgsError(
                "core.command.args.invalid",
                arg=arg_name,
                type=f"literal({'|'.join(choices) if choices else ''})",
                value=raw,
            )
        return raw
    except ValueError as e:
        raise CommandArgsError("core.command.args.invalid", arg=arg_name, type=type_name, value=raw) from e


def _convert_default(type_name: str, raw: str, spec: str) -> Any:
    """
    {!--< internal-use >!--}
    注册期转换声明中的默认值（语法错误抛 ValueError fail-fast）

    :param type_name: 声明的类型名
    :param raw: 声明的默认值原文
    :param spec: 完整 args= 声明（错误提示用）
    :return: 转换后的默认值
    :raises ValueError: 默认值与声明类型不匹配
    """
    try:
        return _convert_value(type_name, raw, "?")
    except CommandArgsError as e:
        raise ValueError(i18n.t("core.command.args.bad_spec", spec=spec, reason=str(e))) from e


def parse_args_spec(spec: str, handler: Callable[..., Any] | None = None) -> list[PositionalArg]:
    """
    解析 ``args=`` 声明字符串（注册期调用，fail-fast）

    语法：``<name:type>`` 必填、``[name:type=default]`` 可选；``literal`` 类型的
    ``=`` 后为枚举表（``a|b|c``，可选形式默认取首个）；``rest`` 类型必须是最后一个条目；
    必填条目不得出现在可选条目之后（避免二义性匹配）。
    可选条目未声明默认值（``[name:type]``）时回填处理器签名同名参数的默认值，
    避免注入 ``None`` 静默覆盖处理器自身的默认值（签名亦无默认值时仍为 ``None``）。

    :param spec: 声明字符串，如 ``"<count:int> [sides:int=6] [mode:literal=fast|slow]"``
    :param handler: 命令处理器（可选；用于回填未声明默认值的可选条目）
    :return: 位置参数规格列表（按声明顺序）
    :raises ValueError: 声明语法无效（携带本地化错误信息）

    :example:
    >>> parse_args_spec("<count:int> [sides:int=6]")
    """
    entries: list[PositionalArg] = []
    consumed = 0
    for match in _SPEC_ENTRY_RE.finditer(spec):
        gap = spec[consumed : match.start()]
        if gap.strip():
            raise ValueError(i18n.t("core.command.args.bad_spec", spec=spec, reason=gap.strip()[:32]))
        consumed = match.end()
        required = match.group(1) is not None
        body = (match.group(1) if required else match.group(2)).strip()

        head, has_default, default_part = body.partition("=")
        head = head.strip()
        name, _, type_name = head.partition(":")
        name, type_name = name.strip(), type_name.strip().lower()
        if not type_name:
            type_name = "str"  # 缺省类型为 str
        if not _IDENTIFIER_RE.fullmatch(name):
            raise ValueError(i18n.t("core.command.args.bad_spec", spec=spec, reason=name[:32]))
        if type_name not in _POSITIONAL_TYPES:
            raise ValueError(i18n.t("core.command.args.bad_spec", spec=spec, reason=type_name[:32]))
        if required and has_default:
            raise ValueError(i18n.t("core.command.args.bad_spec", spec=spec, reason=f"<{name}>=..."))

        choices = None
        default = None
        default_display = default_part.strip()
        if type_name == "literal":
            if not has_default or not default_display:
                raise ValueError(i18n.t("core.command.args.bad_spec", spec=spec, reason=f"{name}:literal"))
            choices = tuple(c.strip() for c in default_part.split("|"))
            if not all(choices) or len(set(choices)) != len(choices):
                raise ValueError(i18n.t("core.command.args.bad_spec", spec=spec, reason=default_part.strip()[:32]))
            default = choices[0]
            default_display = "|".join(choices)
        elif has_default:
            default = _convert_default(type_name, default_display, spec)
        elif type_name == "rest":
            default = ""
        entries.append(
            PositionalArg(
                name=name,
                type=type_name,
                required=required,
                default=default,
                choices=choices,
                default_display=default_display,
            )
        )
    if spec.strip() and not entries:
        raise ValueError(i18n.t("core.command.args.bad_spec", spec=spec, reason=spec.strip()[:32]))

    # 顺序规则：rest 必须最后；可选条目之后不得再出现必填条目
    seen_optional = False
    for entry in entries:
        if entry.type == "rest":
            if entry is not entries[-1]:
                raise ValueError(i18n.t("core.command.args.bad_spec", spec=spec, reason=f"rest:{entry.name}"))
            continue
        if entry.required and seen_optional:
            raise ValueError(i18n.t("core.command.args.bad_spec", spec=spec, reason=entry.name))
        if not entry.required:
            seen_optional = True

    # 回填：可选条目未声明默认值时取处理器签名默认值，避免 None 覆盖处理器自身默认
    if handler is not None:
        sig_params = inspect.signature(handler).parameters
        backfilled: list[PositionalArg] = []
        for entry in entries:
            if entry.required or entry.default_display or entry.type == "rest":
                backfilled.append(entry)
                continue
            param = sig_params.get(entry.name)
            if param is not None and param.default is not inspect.Parameter.empty:
                entry = PositionalArg(
                    name=entry.name,
                    type=entry.type,
                    required=entry.required,
                    default=param.default,
                    choices=entry.choices,
                    default_display=str(param.default),
                )
            backfilled.append(entry)
        entries = backfilled
    return entries


def _annotation_type_key(param: inspect.Parameter | None) -> str | None:
    """
    {!--< internal-use >!--}
    解析处理器参数注解为类型键（兼容真实类型对象与字符串注解）

    :param param: 处理器参数（None 返回 None）
    :return: "str"/"int"/"float"/"bool"；未注解返回 None；不支持返回原始注解文本
    """
    if param is None:
        return None
    ann = param.annotation
    if ann is inspect.Parameter.empty:
        return None
    # 真实类型对象取 __name__，字符串注解（from __future__ import annotations）原样返回；
    # 不支持的注解返回原始文本，由调用方校验报错
    return ann if isinstance(ann, str) else getattr(ann, "__name__", str(ann))


def parse_options_spec(options: dict[str, Any], handler: Callable[..., Any]) -> dict[str, OptionArg]:
    """
    解析 ``options=`` 声明（注册期调用，fail-fast）

    键为处理器参数名，值为旗标形式字符串（多个别名以 ``/`` 分隔，如
    ``"-v/--verbose"``）。注解为 ``bool`` 的参数解析为布尔旗标；``str`` / ``int`` /
    ``float``（缺省视为 ``str``）为带值选项，默认值取处理器签名的参数默认值。

    :param options: 选项声明字典，如 ``{"verbose": "-v/--verbose", "label": "--label"}``
    :param handler: 命令处理器（读取注解、默认值并校验签名）
    :return: 选项规格字典（键为处理器参数名）
    :raises ValueError: 旗标形式不合法 / 注解不受支持 / 参数未在处理器签名中定义

    :example:
    >>> parse_options_spec({"verbose": "-v/--verbose"}, handler)
    """
    params = inspect.signature(handler).parameters
    has_var_kw = any(p.kind is inspect.Parameter.VAR_KEYWORD for p in params.values())
    handler_name = getattr(handler, "__name__", "?")

    result: dict[str, OptionArg] = {}
    for name, forms_str in options.items():
        name = str(name)
        forms = tuple(f.strip() for f in str(forms_str).split("/") if f.strip())
        if not _IDENTIFIER_RE.fullmatch(name) or not forms or any(not f.startswith("-") for f in forms):
            raise ValueError(i18n.t("core.command.args.bad_option_forms", name=name[:32], forms=str(forms_str)))
        param = params.get(name)
        if param is None and not has_var_kw:
            raise ValueError(i18n.t("core.command.args.param_mismatch", cmd=handler_name, names=name))

        type_key = _annotation_type_key(param) or "str"
        if type_key not in _OPTION_TYPES:
            raise ValueError(i18n.t("core.command.args.option_bad_type", name=name, ann=type_key))
        if type_key == "bool":
            default = param.default if param is not None and param.default is not inspect.Parameter.empty else False
            result[name] = OptionArg(name=name, forms=forms, kind="flag", type="bool", default=default)
        else:
            default = param.default if param is not None and param.default is not inspect.Parameter.empty else None
            result[name] = OptionArg(name=name, forms=forms, kind="value", type=type_key, default=default)
    return result


def _looks_like_option(token: str) -> bool:
    """
    {!--< internal-use >!--}
    判断 token 是否形如选项旗标（类数字 token 如负数不算）

    :param token: 待判断的 token
    :return: 是否形如选项（"-x"、"--xx"；"-1"、"-0.5"、"-" 均不算）
    """
    return len(token) > 1 and token.startswith("-") and not _NUMBER_LIKE_RE.fullmatch(token)


def _extract_options(tokens: list[str], options_spec: dict[str, OptionArg]) -> tuple[list[str], dict[str, Any]]:
    """
    {!--< internal-use >!--}
    从 token 列表中识别并剔除选项（分发期第一步）

    支持独立取值（``--label hello``）与内联取值（``--label=hello``）；布尔旗标
    可用内联形式显式赋值（``-v=false``）。未声明的形如选项的 token 视为未知选项。

    :param tokens: 命令名之后的原始 token 列表
    :param options_spec: 选项规格字典
    :return: (剔除选项后的剩余 token, 选项参数名 → 已转换值)
    :raises CommandArgsError: 未知选项 / 带值选项缺少取值 / 内联值转换失败
    """
    form_map: dict[str, OptionArg] = {}
    for opt in options_spec.values():
        for form in opt.forms:
            form_map[form] = opt

    kwargs: dict[str, Any] = {}
    remaining: list[str] = []
    index = 0
    while index < len(tokens):
        token = tokens[index]
        opt = form_map.get(token)
        inline_value = None
        if opt is None and "=" in token:
            head, _, inline_value = token.partition("=")
            opt = form_map.get(head)
        if opt is None:
            if _looks_like_option(token):
                raise CommandArgsError("core.command.args.unknown_option", option=token)
            remaining.append(token)
            index += 1
            continue

        if opt.kind == "flag":
            kwargs[opt.name] = _convert_value("bool", inline_value, opt.name) if inline_value is not None else True
            index += 1
            continue
        if inline_value is not None:
            value, step = inline_value, 1
        elif index + 1 < len(tokens) and tokens[index + 1] not in form_map:
            value, step = tokens[index + 1], 2
        else:
            raise CommandArgsError("core.command.args.missing_value", option=token)
        kwargs[opt.name] = _convert_value(opt.type, value, opt.name)
        index += step
    return remaining, kwargs


def _bind_positionals(tokens: list[str], args_spec: list[PositionalArg]) -> dict[str, Any]:
    """
    {!--< internal-use >!--}
    按位置参数规格绑定剩余 token（分发期第二步）

    :param tokens: 剔除选项后的剩余 token
    :param args_spec: 位置参数规格列表
    :return: 参数名 → 已转换值
    :raises CommandArgsError: 缺少必填参数 / token 转换失败 / 参数过多
    """
    kwargs: dict[str, Any] = {}
    rest = args_spec[-1] if args_spec and args_spec[-1].type == "rest" else None
    body = args_spec[:-1] if rest else args_spec

    index = 0
    for entry in body:
        if index >= len(tokens):
            if entry.required:
                raise CommandArgsError("core.command.args.missing", arg=entry.name)
            kwargs[entry.name] = entry.default
            continue
        kwargs[entry.name] = _convert_value(entry.type, tokens[index], entry.name, entry.choices)
        index += 1

    if rest is not None:
        if index < len(tokens):
            kwargs[rest.name] = " ".join(tokens[index:])
        elif rest.required:
            raise CommandArgsError("core.command.args.missing", arg=rest.name)
        else:
            kwargs[rest.name] = rest.default
        index = len(tokens)

    if index < len(tokens):
        raise CommandArgsError("core.command.args.too_many", extra=" ".join(tokens[index:]))
    return kwargs


def bind_command_arguments(
    tokens: list[str],
    args_spec: list[PositionalArg] | None = None,
    options_spec: dict[str, OptionArg] | None = None,
) -> dict[str, Any]:
    """
    将命令 token 列表解析为处理器关键字参数（分发期调用）

    解析顺序：选项先被识别剔除，剩余 token 再交给 ``args=`` 解析（``rest`` 为
    剔除选项后的剩余文本）。仅在声明了 ``args=`` / ``options=`` 的命令上调用。

    :param tokens: 命令名之后的原始 token 列表
    :param args_spec: 位置参数规格（未声明为 None）
    :param options_spec: 选项规格（未声明为 None）
    :return: 处理器关键字参数（直接 ``handler(event, **kwargs)`` 注入）
    :raises CommandArgsError: 任一 token 无法按声明解析（捕获后自动回复本地化提示）

    :example:
    >>> bind_command_arguments(["3", "--label", "hi"], args_spec, options_spec)
    {"count": 3, "label": "hi", ...}
    """
    kwargs: dict[str, Any] = {}
    remaining = list(tokens)
    if options_spec:
        remaining, option_kwargs = _extract_options(remaining, options_spec)
        kwargs.update(option_kwargs)
    if args_spec:
        kwargs.update(_bind_positionals(remaining, args_spec))
    elif remaining:
        # 只声明了 options：剔除选项后的剩余 token 无法安置
        raise CommandArgsError("core.command.args.too_many", extra=" ".join(remaining))
    return kwargs


def format_usage(args_spec: list[PositionalArg] | None, options_spec: dict[str, OptionArg] | None) -> str:
    """
    依据参数/选项规格生成 usage 尾串（未提供 usage= 时自动展示与错误提示附带）

    形态：位置参数 ``<count>`` / ``[sides=6]`` / ``<mode:a|b|c>`` / ``<text...>``；
    选项 ``[-v, --verbose]`` / ``[--label TEXT]``。

    :param args_spec: 位置参数规格（未声明为 None）
    :param options_spec: 选项规格（未声明为 None）
    :return: usage 尾串（无任何声明时为空字符串）

    :example:
    >>> format_usage(args_spec, options_spec)
    "<count> [sides=6] [-v, --verbose] [--label TEXT]"
    """
    parts: list[str] = []
    for entry in args_spec or []:
        if entry.type == "rest":
            parts.append(f"<{entry.name}...>" if entry.required else f"[{entry.name}...]")
        elif entry.type == "literal":
            shown = f"{entry.name}:{'|'.join(entry.choices or ())}"
            parts.append(f"<{shown}>" if entry.required else f"[{shown}]")
        elif entry.required:
            parts.append(f"<{entry.name}>")
        else:
            parts.append(f"[{entry.name}={entry.default_display}]")
    for opt in (options_spec or {}).values():
        if opt.kind == "flag":
            parts.append("[" + ", ".join(opt.forms) + "]")
        else:
            parts.append(f"[{opt.forms[-1]} {opt.type.upper()}]")
    return " ".join(parts)


def parse_duration(text: str) -> float:
    """
    将时长声明（如 ``"90s"``、``"1h30m"``、``"1d"``）转换为秒数

    语法与 ``args=`` 声明的 ``duration`` 类型一致：1~n 段"数值+单位"
    （单位 s / m / h / d，大小写不敏感）。供命令治理声明（``cooldown=``）
    等场景在注册期复用同一解析口径。

    :param text: 时长声明字符串
    :return: 折算后的秒数（float）
    :raises ValueError: 格式不合法、包含未知单位或折算值非正
    """
    try:
        seconds = _duration_value(text)
    except CommandArgsError as e:
        raise ValueError(str(e)) from e
    if seconds <= 0:
        raise ValueError(f"duration must be positive, got {text!r}")
    return seconds
