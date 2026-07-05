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


# ImportError / ModuleNotFoundError 消息的正则模式
_IMPORT_NO_MODULE_PATTERN = re.compile(
    r"No module named ['\"]([^'\"]+)['\"]"
)
_IMPORT_CANNOT_IMPORT_PATTERN = re.compile(
    r"cannot import name ['\"]([^'\"]+)['\"]\s+from ['\"]([^'\"]+)['\"]"
)


def suggest_for_import_error(exc: ImportError) -> Optional[str]:
    """
    为 ImportError / ModuleNotFoundError 生成拼写建议

    利用 Python 动态特性：解析模块路径，动态 import 父包并检查
    其实际包含的子模块/属性，给出最接近的匹配。

    支持两种场景:
    - ``import ErisPulse.Core.evnt`` -> 检查 ErisPulse.Core 下的子模块
    - ``from ErisPulse.Core import evnt`` -> 检查 ErisPulse.Core 的导出属性

    :param exc: ImportError 或 ModuleNotFoundError 异常
    :return: 建议的名称，无建议时返回 None
    """
    import importlib
    import sys

    msg = str(exc)

    # 场景 2: cannot import name 'xxx' from 'yyy'
    m = _IMPORT_CANNOT_IMPORT_PATTERN.search(msg)
    if m:
        target = m.group(1)
        source_mod = m.group(2)
        candidates: list[str] = []
        try:
            mod = sys.modules.get(source_mod) or importlib.import_module(source_mod)
            candidates = [
                a for a in dir(mod) if not a.startswith("_") and a != target
            ]
        except Exception:
            pass
        if candidates:
            return best_match_with_prefix(target, candidates, cutoff=0.5)
        return None

    # 场景 1: No module named 'xxx'
    mod_name = getattr(exc, "name", None)
    if not mod_name:
        m2 = _IMPORT_NO_MODULE_PATTERN.search(msg)
        if m2:
            mod_name = m2.group(1)

    if not mod_name or mod_name.startswith("."):
        return None

    parts = mod_name.split(".")
    target = parts[-1]
    candidates = []

    if len(parts) > 1:
        # 动态检查父包下实际存在的子模块
        parent_path = ".".join(parts[:-1])
        try:
            parent_mod = sys.modules.get(parent_path)
            if parent_mod is None:
                parent_mod = importlib.import_module(parent_path)

            if hasattr(parent_mod, "__path__"):
                import pkgutil

                for _, name, _ in pkgutil.iter_modules(parent_mod.__path__):
                    candidates.append(name)
            else:
                candidates = [
                    a for a in dir(parent_mod) if not a.startswith("_")
                ]
        except Exception:
            pass

    # 补充：同深度已加载模块
    for loaded in sys.modules:
        loaded_parts = loaded.split(".")
        if len(loaded_parts) == len(parts) and loaded_parts[-1] != target:
            candidates.append(loaded_parts[-1])

    if not candidates:
        return None

    return best_match_with_prefix(target, candidates, cutoff=0.5)


def suggest_for_key_error(exc: KeyError, tb: Any = None) -> Optional[str]:
    """
    为 KeyError 生成拼写建议

    利用 Python 动态特性：遍历 traceback 帧的局部变量，
    找到 dict-like 对象并在其 keys 中查找最相似的匹配。

    :param exc: KeyError 异常
    :param tb: traceback 对象
    :return: 建议的 key，无建议时返回 None
    """
    if not exc.args:
        return None

    missing_key = exc.args[0]
    if not isinstance(missing_key, str) or len(missing_key) < 2:
        return None

    if tb is None:
        return None

    # 遍历帧的局部变量，收集 dict-like 对象的字符串 key
    all_candidates: set[str] = set()
    frame = tb
    depth = 0
    while frame and depth < 5:
        for var_val in frame.tb_frame.f_locals.values():
            if isinstance(var_val, dict):
                for k in var_val.keys():
                    if isinstance(k, str) and k != missing_key:
                        all_candidates.add(k)
        frame = frame.tb_next
        depth += 1

    if not all_candidates:
        return None

    return best_match(missing_key, list(all_candidates), cutoff=0.6)


def suggest_for_event_loop_error(exc: RuntimeError) -> Optional[str]:
    """
    为 RuntimeError: Event loop is closed 生成诊断提示

    检测事件循环被意外关闭的常见原因，返回修复建议。
    与拼写建议类函数不同，这里返回的是一个标识符字符串，
    由 exceptions.py 通过 i18n 翻译为最终的多语言提示。

    :param exc: RuntimeError 异常
    :return: 诊断提示标识符，不匹配时返回 None
    """
    msg = str(exc)
    if "event loop is closed" not in msg.lower():
        return None
    return "event_loop_closed"


def suggest_for_invalid_await(exc: TypeError) -> Optional[str]:
    """
    为 TypeError: object X can't be used in 'await' expression 生成诊断提示

    检测对非协程对象使用 await 的常见原因。
    与拼写建议类函数不同，这里返回的是一个标识符字符串，
    由 exceptions.py 通过 i18n 翻译为最终的多语言提示。

    :param exc: TypeError 异常
    :return: 诊断提示标识符，不匹配时返回 None
    """
    msg = str(exc)
    if "can't be used in 'await' expression" not in msg.lower():
        return None
    return "invalid_await"


__all__ = [
    "suggest_similar",
    "best_match",
    "best_match_with_prefix",
    "parse_attr_error",
    "get_object_from_traceback",
    "suggest_for_attribute_error",
    "suggest_for_import_error",
    "suggest_for_key_error",
    "suggest_for_event_loop_error",
    "suggest_for_invalid_await",
]
