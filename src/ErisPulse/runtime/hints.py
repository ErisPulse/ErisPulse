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

import asyncio
import difflib
import re
from collections.abc import Sequence
from typing import Any


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
) -> str | None:
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
) -> str | None:
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
    best: str | None = None
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


def parse_attr_error(exc: AttributeError) -> tuple[str | None, str | None]:
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


def get_object_from_traceback(tb: Any) -> object | None:
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
) -> str | None:
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
    obj: object | None = getattr(exc, "obj", None)
    if obj is None and tb is not None:
        obj = get_object_from_traceback(tb)

    if obj is None:
        return None

    # 收集对象的公共属性作为候选
    candidates = [a for a in dir(obj) if not a.startswith("_") and a != attr_name]
    if not candidates:
        return None

    return best_match(attr_name, candidates, cutoff=0.6)


# ImportError / ModuleNotFoundError 消息的正则模式
_IMPORT_NO_MODULE_PATTERN = re.compile(r"No module named ['\"]([^'\"]+)['\"]")
_IMPORT_CANNOT_IMPORT_PATTERN = re.compile(
    r"cannot import name ['\"]([^'\"]+)['\"]\s+from ['\"]([^'\"]+)['\"]"
)


def suggest_for_import_error(exc: ImportError) -> str | None:
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
            candidates = [a for a in dir(mod) if not a.startswith("_") and a != target]
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
                candidates = [a for a in dir(parent_mod) if not a.startswith("_")]
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


def suggest_for_key_error(exc: KeyError, tb: Any = None) -> str | None:
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
                for k in var_val:
                    if isinstance(k, str) and k != missing_key:
                        all_candidates.add(k)
        frame = frame.tb_next
        depth += 1

    if not all_candidates:
        return None

    return best_match(missing_key, list(all_candidates), cutoff=0.6)


def suggest_for_name_error(exc: NameError, tb: Any = None) -> str | None:
    """
    为 NameError 生成拼写建议

    名字拼写错误（如 ``my_modlue`` -> ``my_module``）是最高频的失误之一。
    从出错帧的局部变量、全局变量与内置名称中收集候选，给出最接近的匹配。

    :param exc: NameError 异常
    :param tb: traceback 对象（可选）
    :return: 建议的名称，无建议时返回 None
    """
    if not exc.args:
        return None
    missing_name = str(exc.args[0])
    if not missing_name or len(missing_name) < 2:
        return None

    # 收集候选：帧的局部 / 全局 / 内置名称
    candidates: set[str] = set()
    frames_checked = 0
    frame = tb
    # 先走 traceback 帧
    while frame and frames_checked < 5:
        f_locals = frame.tb_frame.f_locals
        f_globals = frame.tb_frame.f_globals
        for source in (f_locals, f_globals):
            for n in source:
                if isinstance(n, str) and not n.startswith("__") and n != missing_name:
                    candidates.add(n)
        # 内置名称（len/range/print 等）
        # __builtins__ 在主模块中是 module 对象，在子模块中是 dict
        builtins = f_globals.get("__builtins__")
        if isinstance(builtins, dict):
            for n in builtins:
                if isinstance(n, str) and not n.startswith("_") and n != missing_name:
                    candidates.add(n)
        elif hasattr(builtins, "__dict__"):
            for n in builtins.__dict__:
                if isinstance(n, str) and not n.startswith("_") and n != missing_name:
                    candidates.add(n)
        frame = frame.tb_next
        frames_checked += 1

    if not candidates:
        return None
    return best_match(missing_name, list(candidates), cutoff=0.6)


def suggest_for_coroutine_attribute(
    exc: AttributeError, tb: Any = None
) -> str | None:
    """
    检测“对协程对象访问属性”的常见错误（忘记 await）

    例如 ``sdk.my_module`` 返回未 await 的协程时，访问其属性会抛
    AttributeError。此函数返回一个标识符，由 exceptions.py 翻译为
    “你是不是忘记 await 了？”的提示。

    :param exc: AttributeError 异常
    :param tb: traceback 对象（可选）
    :return: 诊断提示标识符，不匹配时返回 None
    """
    obj: object | None = getattr(exc, "obj", None)
    if obj is None and tb is not None:
        obj = get_object_from_traceback(tb)
    if obj is not None and asyncio.iscoroutine(obj):
        return "coroutine_attribute"
    return None


def suggest_for_missing_argument(exc: TypeError) -> str | None:
    """
    为 TypeError: missing required positional argument 生成诊断提示

    检测调用时位置参数不足的常见错误（如调用 ``f(a)`` 但定义需要两个参数）。

    :param exc: TypeError 异常
    :return: 诊断提示标识符，不匹配时返回 None
    """
    msg = str(exc).lower()
    if "missing" in msg and "required positional argument" in msg:
        return "missing_argument"
    # 变体：“takes exactly N positional arguments but M were given”
    if "takes exactly" in msg and "positional argument" in msg:
        return "missing_argument"
    return None


def suggest_for_not_callable(exc: TypeError) -> str | None:
    """
    为 TypeError: object is not callable / not subscriptable / not iterable 生成诊断提示

    检测对不可调用 / 不可下标 / 不可迭代对象误用的常见错误，
    多数情况下是因为覆盖了同名变量或忘记加括号。

    :param exc: TypeError 异常
    :return: 诊断提示标识符，不匹配时返回 None
    """
    msg = str(exc).lower()
    if "is not callable" in msg:
        return "not_callable"
    if "is not subscriptable" in msg:
        return "not_subscriptable"
    if "is not iterable" in msg or "is not an iterator" in msg:
        return "not_iterable"
    return None


def suggest_for_event_loop_error(exc: RuntimeError) -> str | None:
    """
    为 RuntimeError 中与事件循环相关的错误生成诊断提示

    覆盖常见场景：
    - 事件循环已被关闭（event loop is closed）
    - 没有当前事件循环（There is no current event loop）
    - 在已有事件循环中调用 asyncio.run()（cannot be called from a running event loop）

    与拼写建议类函数不同，这里返回的是一个标识符字符串，
    由 exceptions.py 通过 i18n 翻译为最终的多语言提示。

    :param exc: RuntimeError 异常
    :return: 诊断提示标识符，不匹配时返回 None
    """
    msg = str(exc).lower()
    if "event loop is closed" in msg:
        return "event_loop_closed"
    if "no current event loop" in msg or "there is no current event loop" in msg:
        return "no_event_loop"
    if "no running event loop" in msg:
        return "no_event_loop"
    if "asyncio.run()" in msg and "running event loop" in msg:
        return "asyncio_run_in_loop"
    if "coroutine" in msg and "was never awaited" in msg:
        return "coroutine_never_awaited"
    return None


def suggest_for_invalid_await(exc: TypeError) -> str | None:
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


def suggest_for_recursion_error(exc: RecursionError) -> str | None:
    """
    为 RecursionError 生成诊断提示

    检测无限递归 / 缺少递归终止条件的常见错误。

    :param exc: RecursionError 异常
    :return: 诊断提示标识符
    """
    return "recursion_error"


def suggest_for_timeout_error(exc: TimeoutError) -> str | None:
    """
    为 TimeoutError 生成诊断提示

    检测网络 / 异步操作超时的常见错误。

    :param exc: TimeoutError 异常
    :return: 诊断提示标识符
    """
    return "timeout_error"


def suggest_for_connection_error(exc: ConnectionError) -> str | None:
    """
    为 ConnectionError 及其子类生成诊断提示

    覆盖 ConnectionRefusedError / ConnectionResetError / ConnectionAbortedError，
    检测网络连接问题的常见原因。

    :param exc: ConnectionError 异常
    :return: 诊断提示标识符
    """
    if isinstance(exc, ConnectionRefusedError):
        return "connection_refused"
    if isinstance(exc, ConnectionResetError):
        return "connection_reset"
    return "connection_error"


def suggest_for_erispulse_client_error(exc: BaseException) -> str | None:
    """
    为 ErisPulse 自定义客户端异常生成诊断提示

    覆盖框架自身的 ClientConnectionError / ClientTimeoutError / HTTPStatusError，
    使用户看到这些异常时能获得与原生网络异常一致的友好提示。
    为避免循环导入，errors 模块在函数内部延迟导入。

    :param exc: 异常对象
    :return: 诊断提示标识符，不匹配时返回 None
    """
    try:
        from ..Core.Bases.errors import (
            ClientConnectionError,
            ClientTimeoutError,
            HTTPStatusError,
        )
    except ImportError:
        return None

    if isinstance(exc, ClientConnectionError):
        return "client_connection_error"
    if isinstance(exc, ClientTimeoutError):
        return "client_timeout_error"
    if isinstance(exc, HTTPStatusError):
        status = getattr(exc, "status", 0)
        if 400 <= status < 500:
            return "http_client_error"
        if 500 <= status < 600:
            return "http_server_error"
        return "http_status_error"
    return None


def suggest_for_websocket_disconnect(exc: BaseException) -> str | None:
    """
    检测 WebSocket 断开是否为正常关闭

    WebSocketDisconnect 的 code=1000（正常关闭）属于生命周期事件而非错误；
    其他 code（如 1006 异常断开）才需要关注。为避免循环导入，
    errors 模块在函数内部延迟导入。

    :param exc: 异常对象
    :return: 标识符（'websocket_normal_close' / 'websocket_abnormal_close'），不匹配返回 None
    """
    try:
        from ..Core.Bases.errors import WebSocketDisconnect
    except ImportError:
        return None

    if not isinstance(exc, WebSocketDisconnect):
        return None
    code = getattr(exc, "code", 1000)
    # 1000 (Normal Closure) / 1001 (Going Away) 是正常关闭
    if code in (1000, 1001):
        return "websocket_normal_close"
    return "websocket_abnormal_close"


__all__ = [
    "best_match",
    "best_match_with_prefix",
    "get_object_from_traceback",
    "parse_attr_error",
    "suggest_for_attribute_error",
    "suggest_for_connection_error",
    "suggest_for_coroutine_attribute",
    "suggest_for_erispulse_client_error",
    "suggest_for_event_loop_error",
    "suggest_for_import_error",
    "suggest_for_invalid_await",
    "suggest_for_key_error",
    "suggest_for_missing_argument",
    "suggest_for_name_error",
    "suggest_for_not_callable",
    "suggest_for_recursion_error",
    "suggest_for_timeout_error",
    "suggest_for_websocket_disconnect",
    "suggest_similar",
]
