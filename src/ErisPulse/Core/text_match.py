"""
ErisPulse 统一文本/条目匹配工具

为全系统（scope 控制面 / message 装饰器 / wait_reply / adapter.on / activate_on）
提供**同一套**匹配条目语法，避免各处各自实现、语义漂移：

- ``精确名``：如 ``"Chat"``、``"u_admin"`` —— 全值精确比较（大小写不敏感）
- ``glob``：含 ``*`` / ``?`` / ``[seq]`` 的条目，如 ``"Tool*"``、``"spam_*"`` ——
  glob 全值匹配（大小写不敏感）
- ``re:正则``：以 ``re:`` 前缀声明的正则条目，如 ``"re:^Danger.*"`` ——
  正则 ``search`` 匹配（默认大小写不敏感，可在正则内用 ``(?-i)`` 或 ``(?i)`` 控制）

约定：
- 默认**大小写不敏感**（对齐 scope 模块名匹配的既有语义）
- 纯精确条目走快路径（无正则/无 glob 开销）
- 正则条目编译结果带 LRU 缓存；非法正则静默降级为"不匹配"（不抛错）

{!--< tips >!--}
1. ``compile_entry_matcher(entry)`` 把单条目编译为 ``fn(text) -> bool``
2. ``compile_entry_list(entries)`` 把条目列表编译为"任一命中"匹配器
3. ``compile_text_matcher(pattern, regex)`` 给装饰器用（glob 与 regex 须都命中）
4. ``extract_text(event)`` 提取事件纯文本（``alt_message`` 优先）
{!--< /tips >!--}
"""

import fnmatch
import re
from collections.abc import Callable
from functools import lru_cache
from typing import Any

# 正则条目前缀
REGEX_PREFIX = "re:"

# 非法正则的全局降级标记（避免反复尝试编译）
_INVALID_REGEX = object()


@lru_cache(maxsize=1024)
def _compile_regex(pattern: str) -> re.Pattern | object:
    """
    {!--< internal-use >!--}
    编译正则（带 LRU 缓存）。非法正则返回哨兵对象，调用方视为"不匹配"。

    :param pattern: 正则源码
    :return: 编译后的 Pattern，或 ``_INVALID_REGEX``
    """
    try:
        return re.compile(pattern, re.IGNORECASE)
    except re.error:
        return _INVALID_REGEX


def is_entry_pattern(entry: str) -> bool:
    """
    判断条目是否包含模式语法（glob 或 re: 前缀）

    无模式字符的纯字符串走精确快路径。

    :param entry: 匹配条目
    :return: True 表示是 glob / 正则条目
    """
    return entry.startswith(REGEX_PREFIX) or any(c in entry for c in "*?[")


def compile_entry_matcher(entry: str) -> Callable[[str], bool]:
    """
    编译单个匹配条目为判定函数

    三种语法：

    - 精确名（无模式字符）→ 大小写不敏感全值比较
    - glob（含 ``*`` / ``?`` / ``[seq]``）→ 大小写不敏感 glob 全值匹配
    - ``re:...`` → 大小写不敏感正则 ``search``；非法正则恒不匹配

    :param entry: 匹配条目
    :return: ``fn(text: str) -> bool``
    """
    entry = str(entry)
    lower_entry = entry.lower()

    if entry.startswith(REGEX_PREFIX):
        regex_obj = _compile_regex(entry[len(REGEX_PREFIX):])
        if regex_obj is _INVALID_REGEX:
            return lambda _text: False
        return lambda text: regex_obj.search(text) is not None

    if is_entry_pattern(entry):
        return lambda text: fnmatch.fnmatchcase(text.lower(), lower_entry)

    # 精确快路径
    return lambda text: text.lower() == lower_entry


def compile_entry_list(entries: list[str] | None) -> Callable[[str], bool] | None:
    """
    编译条目列表为"任一命中即 True"的判定函数

    :param entries: 条目列表，None / 空返回 None（表示不限制）
    :return: ``fn(text: str) -> bool``，None 表示空列表
    """
    if not entries:
        return None
    if isinstance(entries, str):
        entries = [entries]
    matchers = [compile_entry_matcher(e) for e in entries]

    def matches(text: str) -> bool:
        return any(m(text) for m in matchers)

    return matches


def compile_text_matcher(
    pattern: str | None, regex: str | None
) -> Callable[[Any], bool] | None:
    """
    编译文本匹配条件函数（glob pattern 与 regex 须**都**命中才返回 True）

    供 message 装饰器 / wait_reply / adapter.on 使用：
    接收**事件对象**并内部提取文本，再按 pattern / regex 判定。

    - ``pattern``：glob 通配符（大小写不敏感全值匹配）
    - ``regex``：正则（大小写不敏感 ``search``）；注意此处为正则源码，**不加** ``re:`` 前缀
    - 两者同时给定 → AND；均未给定 → 返回 None（不限制）

    :param pattern: glob 通配符，None 表示不校验
    :param regex: 正则源码，None 表示不校验
    :return: 条件函数，均未给定时返回 None
    """
    if not pattern and not regex:
        return None

    glob_matcher = compile_entry_matcher(pattern) if pattern else None
    regex_obj = _compile_regex(regex) if regex else None
    invalid_regex = regex_obj is _INVALID_REGEX

    def condition(event: Any) -> bool:
        text = extract_text(event)
        if glob_matcher is not None and not glob_matcher(text):
            return False
        if regex is not None:
            if invalid_regex or regex_obj.search(text) is None:  # type: ignore[union-attr]
                return False
        return True

    return condition


def extract_text(event: Any) -> str:
    """
    提取事件对象的纯文本内容（供文本匹配使用）

    优先取 ``alt_message``（适配器提供的纯文本回退）；否则拼接 ``message``
    段中 ``type == "text"`` 的文本。提取失败返回空字符串。

    :param event: 事件数据（dict 或 Event 包装对象）
    :return: 消息纯文本
    """
    try:
        alt = event.get("alt_message")
        if isinstance(alt, str) and alt:
            return alt
        segments = event.get("message") or []
        parts = []
        for segment in segments:
            if isinstance(segment, dict) and segment.get("type") == "text":
                text = segment.get("data", {}).get("text")
                if isinstance(text, str):
                    parts.append(text)
        return "".join(parts)
    except Exception:
        return ""


def entry_matches(entry: str, text: str) -> bool:
    """
    单次便捷匹配（无需预编译）

    :param entry: 匹配条目（精确 / glob / ``re:`` 正则）
    :param text: 待匹配文本
    :return: 是否命中
    """
    return compile_entry_matcher(entry)(text)


__all__ = [
    "REGEX_PREFIX",
    "compile_entry_matcher",
    "compile_entry_list",
    "compile_text_matcher",
    "entry_matches",
    "extract_text",
    "is_entry_pattern",
]
