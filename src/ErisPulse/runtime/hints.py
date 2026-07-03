"""
ErisPulse 友好错误提示引擎

提供拼写检查、相似度匹配功能，帮助用户快速定位拼写错误。
被 CLI、全局异常钩子及核心模块的属性访问共同使用。

{!--< tips >!--}
1. suggest_similar: 返回多个相似候选词
2. best_match: 返回单个最佳匹配
3. parse_attr_error: 从 AttributeError 中提取信息
{!--< /tips >!--}
"""

import difflib
import re
from typing import Any, Optional, Sequence


def suggest_similar(
    name: str,
    candidates: Sequence[str],
    *,
    max_suggestions: int = 3,
    cutoff: float = 0.5,
) -> list[str]:
    """
    找出与给定名称最相似的候选词

    使用 difflib 进行模糊匹配，适用于拼写纠错场景（如 my_moudle -> my_module）。
    匹配时不区分大小写，但返回原始大小写的候选词。

    :param name: 用户输入的（可能有误的）名称
    :param candidates: 候选词列表
    :param max_suggestions: 最多返回的建议数量
    :param cutoff: 相似度阈值 (0.0 ~ 1.0)，低于此值的候选会被过滤
    :return: 按相似度从高到低排序的建议列表（保留原始大小写）
    """
    name_lower = name.lower()
    matcher = difflib.SequenceMatcher(None, name_lower)
    scored: list[tuple[float, str]] = []
    for candidate in candidates:
        matcher.set_seq2(candidate.lower())
        ratio = matcher.ratio()
        if ratio >= cutoff:
            scored.append((ratio, candidate))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [c for _, c in scored[:max_suggestions]]


def best_match(
    name: str,
    candidates: Sequence[str],
    *,
    cutoff: float = 0.6,
) -> Optional[str]:
    """
    返回单个最佳匹配建议

    :param name: 用户输入的名称
    :param candidates: 候选词列表
    :param cutoff: 相似度阈值（默认 0.6，确保只返回高置信度匹配）
    :return: 最佳匹配的候选词，无匹配时返回 None
    """
    matches = suggest_similar(name, candidates, max_suggestions=1, cutoff=cutoff)
    return matches[0] if matches else None


def best_match_with_prefix(
    name: str,
    candidates: Sequence[str],
    *,
    cutoff: float = 0.5,
    prefix_bonus: float = 0.85,
) -> Optional[str]:
    """
    带前缀加成的模糊匹配

    当输入是候选词的前缀时（如 ins -> install），给予更高的相似度分数。
    适用于命令行补全、拼写纠错等场景，确保前缀匹配优先于字符重排匹配。

    :param name: 用户输入的名称
    :param candidates: 候选词列表
    :param cutoff: 基础相似度阈值
    :param prefix_bonus: 前缀匹配的最低分数（默认 0.85）
    :return: 最佳匹配的候选词，无匹配时返回 None
    """
    name_lower = name.lower()
    matcher = difflib.SequenceMatcher(None, name_lower)
    best: Optional[str] = None
    best_score = cutoff

    for candidate in candidates:
        candidate_lower = candidate.lower()
        matcher.set_seq2(candidate_lower)
        ratio = matcher.ratio()
        # 前缀加成：输入是候选词的前缀时提升分数
        if candidate_lower.startswith(name_lower):
            ratio = max(ratio, prefix_bonus)
        if ratio > best_score:
            best_score = ratio
            best = candidate

    return best


# AttributeError 消息的正则模式
_ATTR_ERROR_PATTERNS = [
    # "'TypeName' object has no attribute 'attr'"
    re.compile(r"'(\w+)'\s+object has no attribute '([^']+)'"),
    # "module 'mod.name' has no attribute 'attr'"
    re.compile(r"module '([^']+)'\s+has no attribute '([^']+)'"),
]


def parse_attr_error(exc: AttributeError) -> tuple[Optional[str], Optional[str]]:
    """
    从 AttributeError 中提取对象类型名和属性名

    优先使用 Python 3.10+ 的 exc.name 属性，
    以及 exc.obj (3.12+) 推断类型名，
    否则从错误消息中正则解析。

    :param exc: AttributeError 异常实例
    :return: (type_name, attr_name)，无法提取时对应位置为 None
    """
    attr_name = getattr(exc, "name", None)

    # Python 3.12+: AttributeError.obj
    obj = getattr(exc, "obj", None)
    if obj is not None:
        type_name = type(obj).__name__
        return type_name, attr_name

    # Fallback: 正则解析错误消息
    msg = str(exc)
    for pattern in _ATTR_ERROR_PATTERNS:
        m = pattern.search(msg)
        if m:
            return m.group(1), m.group(2)

    return None, attr_name


def get_object_from_traceback(tb: Any) -> Optional[object]:
    """
    尝试从 traceback 的最后一帧中获取出错的对象（通常是 self）

    :param tb: traceback 对象
    :return: 出错的对象，无法获取时返回 None
    """
    if tb is None:
        return None
    # 跳转到最后一帧
    while tb.tb_next:
        tb = tb.tb_next
    frame = tb.tb_frame
    # 尝试从局部变量中找 self
    self_obj = frame.f_locals.get("self")
    if self_obj is not None:
        return self_obj
    return None


def suggest_for_attribute_error(
    exc: AttributeError,
    tb: Any = None,
) -> Optional[str]:
    """
    为 AttributeError 生成拼写建议

    尝试从异常对象或 traceback 中获取目标对象，
    在其公共属性中查找最相似的。

    :param exc: AttributeError 异常
    :param tb: traceback 对象（可选）
    :return: 建议的属性名，无建议时返回 None
    """
    _, attr_name = parse_attr_error(exc)
    if not attr_name:
        return None

    # 尝试获取目标对象
    obj: Optional[object] = getattr(exc, "obj", None)
    if obj is None and tb is not None:
        obj = get_object_from_traceback(tb)

    if obj is None:
        return None

    # 收集对象的公共属性作为候选
    candidates = [
        a for a in dir(obj) if not a.startswith("_") and a != attr_name
    ]
    if not candidates:
        return None

    return best_match(attr_name, candidates, cutoff=0.6)


__all__ = [
    "suggest_similar",
    "best_match",
    "best_match_with_prefix",
    "parse_attr_error",
    "get_object_from_traceback",
    "suggest_for_attribute_error",
]
