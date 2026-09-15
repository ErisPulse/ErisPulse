"""
ErisPulse 异常诊断模块

从异常的 traceback 中提取「用户代码帧」摘要，过滤掉框架内部帧，
让开发者在默认日志级别下即可定位模块/适配器加载或初始化失败的具体位置，
无需手动重开 DEBUG 级别查看完整堆栈。

{!--< tips >!--}
1. extract_user_frame: 从异常对象提取结构化的用户代码帧信息
2. format_diagnostic_block: 生成可日志输出的多行诊断文本
3. log_diagnostic: 直接将诊断信息写入 logger（最常用）
{!--< /tips >!--}
"""

import linecache
import sys
import traceback
from pathlib import Path
from typing import Any

from .hints import best_match

_FRAMEWORK_ROOT: Path | None = None
_STDLIB_ROOT: Path | None = None


def _get_framework_root() -> Path:
    """
    获取 ErisPulse 包根目录，用于判定框架内部帧

    {!--< internal-use >!--}
    结果会被缓存，避免每次调用都查询 ``ErisPulse.__file__``
    {!--< /internal-use >!--}

    :return: Path ErisPulse 包目录（如 ``.../src/ErisPulse``）
    """
    global _FRAMEWORK_ROOT
    if _FRAMEWORK_ROOT is None:
        try:
            import ErisPulse

            _FRAMEWORK_ROOT = Path(ErisPulse.__file__).resolve().parent
        except Exception:
            _FRAMEWORK_ROOT = Path()
    return _FRAMEWORK_ROOT


def _is_framework_frame(filename: str) -> bool:
    """
    判断给定文件是否属于 ErisPulse 框架内部代码

    {!--< internal-use >!--}
    通过判断文件路径是否位于 ErisPulse 包目录下来识别框架帧。
    {!--< /internal-use >!--}

    :param filename: str 帧对应的文件路径
    :return: bool 是否为框架内部帧
    """
    try:
        root = _get_framework_root()
        if root == Path():
            return False
        fpath = Path(filename).resolve()
        return root in fpath.parents or fpath == root
    except Exception:
        return False


def _is_stdlib_frame(filename: str) -> bool:
    """
    判断给定文件是否属于 Python 标准库

    {!--< internal-use >!--}
    用于协程等待链采样时跳过 asyncio 等标准库帧（如 ``sleep``），直接
    定位业务代码的等待点。venv 环境下 ``sys.base_prefix`` 指向真实
    Python 安装目录，site-packages（第三方库）不在其中、不受影响。
    """
    global _STDLIB_ROOT
    try:
        if _STDLIB_ROOT is None:
            _STDLIB_ROOT = Path(sys.base_prefix).resolve()
        if Path() == _STDLIB_ROOT:
            return False
        return _STDLIB_ROOT in Path(filename).resolve().parents
    except Exception:
        return False


def _is_internal_frame(filename: str) -> bool:
    """
    判断给定文件是否为框架或标准库内部帧（非业务代码）

    {!--< internal-use >!--}
    框架帧与标准库帧统一视为非业务帧；协程等待链采样时两者都跳过。
    第三方库（site-packages）不在此列——卡在第三方库内部同样具有定位价值。
    """
    return _is_framework_frame(filename) or _is_stdlib_frame(filename)


def _short_filename(filename: str) -> str:
    """
    将绝对路径缩短为更易读的相对路径表示

    {!--< internal-use >!--}
    优先相对于当前工作目录；其次相对于 ErisPulse 包父目录；
    都不可行时退化为文件名。
    {!--< /internal-use >!--}

    :param filename: str 绝对文件路径
    :return: str 缩短后的路径（统一使用 ``/`` 分隔符）
    """
    try:
        p = Path(filename)
        cwd = Path.cwd()
        try:
            return str(p.relative_to(cwd)).replace("\\", "/")
        except ValueError:
            pass
        try:
            root = _get_framework_root()
            if root != Path():
                return str(p.relative_to(root.parent)).replace("\\", "/")
        except ValueError:
            pass
        return p.name
    except Exception:
        return filename


def extract_user_frame(exc: BaseException, depth: int = 3) -> dict[str, Any]:
    """
    从异常 traceback 提取「用户代码帧」摘要

    过滤掉 ErisPulse 框架内部帧，保留最靠近错误发生点的 ``depth`` 个用户代码帧。
    用于在加载/初始化失败时快速定位用户代码中的出错位置。

    :param exc: BaseException 异常对象
    :param depth: int 最多保留的用户帧数量（从最深处开始计数）
    :return: dict 结构化诊断信息，包含:
        - ``frames``: 用户代码帧列表，每项含 ``file``/``lineno``/``func``/``source``
        - ``exc_type``: 异常类型名
        - ``exc_value``: 异常消息字符串
        - ``has_traceback``: 是否存在可用的 traceback

    :example:
    >>> try:
    ...     1 / 0
    ... except Exception as e:
    ...     info = extract_user_frame(e)
    ...     info["exc_type"]
    'ZeroDivisionError'
    """
    tb = getattr(exc, "__traceback__", None)
    exc_type = type(exc).__name__
    try:
        exc_value = str(exc)
    except Exception:
        exc_value = repr(exc)

    if tb is None:
        return {
            "frames": [],
            "exc_type": exc_type,
            "exc_value": exc_value,
            "has_traceback": False,
        }

    summaries = traceback.extract_tb(tb)
    user_summaries = [s for s in summaries if not _is_framework_frame(s.filename)]
    deepest = user_summaries[-depth:] if user_summaries else []

    frames: list[dict[str, Any]] = []
    for s in deepest:
        lineno = s.lineno or 0
        source: str | None = s.line
        if not source:
            try:
                source = linecache.getline(s.filename, lineno).strip() or None
            except Exception:
                source = None
        frames.append(
            {
                "file": _short_filename(s.filename),
                "lineno": lineno,
                "func": s.name or "<module>",
                "source": source,
            }
        )

    return {
        "frames": frames,
        "exc_type": exc_type,
        "exc_value": exc_value,
        "has_traceback": True,
    }


def _t(key: str, **kwargs: Any) -> str:
    """
    尝试用 i18n 翻译，失败时回退到英文兜底

    {!--< internal-use >!--}
    与 ``runtime.exceptions._t`` 相同的容错策略，确保 i18n 未就绪时
    诊断信息仍可输出。
    {!--< /internal-use >!--}

    :param key: str i18n 键
    :param kwargs: 占位符参数
    :return: str 翻译后的文本
    """
    try:
        from ..Core.i18n import i18n

        return i18n.t(key, **kwargs)
    except Exception:
        _FALLBACKS = {
            "core.diag.frame": "  → {file}:{lineno} in {func}",
            "core.diag.source": "      {source}",
            "core.diag.exc_line": "  → {exc_type}: {exc_value}",
            "core.diag.hint": (
                "  → Hint: raise the log level to DEBUG to see the full traceback."
            ),
            "core.diag.no_user_frame": (
                "  → (no user code frame found; this may be an internal framework error)"
            ),
            "core.diag.similar_hint": (
                "  → Hint: did you mean '{suggestion}'?"
            ),
        }
        template = _FALLBACKS.get(key, key)
        try:
            return template.format(**kwargs)
        except Exception:
            return template


def format_diagnostic_block(
    exc: BaseException,
    *,
    hint_key: str | None = None,
    hint_params: dict[str, Any] | None = None,
    candidates: list[str] | None = None,
    depth: int = 3,
) -> str:
    """
    生成可日志输出的多行诊断文本

    将 ``extract_user_frame`` 的结果格式化为带缩进引导符（``→``）的多行字符串，
    末尾附加查看完整堆栈的提示行。

    :param exc: BaseException 异常对象
    :param hint_key: str | None 自定义提示行的 i18n key（默认使用通用提示）
    :param hint_params: dict[str, Any] | None 提示行模板的填充参数
        （如 ``{"name": module_name}``，对应提示文案中的 ``{name}`` 占位符）
    :param candidates: list[str] | None 相似名称候选，用于附加「你是不是想写」提示
    :param depth: int 最多保留的用户帧数量
    :return: str 多行诊断文本；无可用信息时返回空字符串

    :example:
    >>> try:
    ...     import nonexistent_module
    ... except Exception as e:
    ...     print(format_diagnostic_block(e))
    """
    info = extract_user_frame(exc, depth=depth)
    lines: list[str] = []

    if not info["has_traceback"] or not info["frames"]:
        lines.append(_t("core.diag.no_user_frame"))
    else:
        for f in info["frames"]:
            lines.append(
                _t(
                    "core.diag.frame",
                    file=f["file"],
                    lineno=f["lineno"],
                    func=f["func"],
                )
            )
            if f["source"]:
                lines.append(_t("core.diag.source", source=f["source"]))
        lines.append(
            _t(
                "core.diag.exc_line",
                exc_type=info["exc_type"],
                exc_value=info["exc_value"],
            )
        )

    if candidates:
        suggestion = best_match(info["exc_value"], candidates, cutoff=0.5)
        if suggestion:
            lines.append(_t("core.diag.similar_hint", suggestion=suggestion))

    if hint_key is not None:
        try:
            from ..Core.i18n import i18n

            lines.append(i18n.t(hint_key, **(hint_params or {})))
        except Exception:
            lines.append(_t("core.diag.hint"))
    else:
        lines.append(_t("core.diag.hint"))

    return "\n".join(lines)


def log_diagnostic(
    exc: BaseException,
    *,
    hint_key: str | None = None,
    hint_params: dict[str, Any] | None = None,
    candidates: list[str] | None = None,
    depth: int = 3,
    logger: Any = None,
) -> None:
    """
    将异常诊断信息写入日志

    最常用的入口：在 ``except`` 块中调用，自动提取用户代码帧并以
    ``ERROR`` 级别输出多行诊断信息。

    :param exc: BaseException 异常对象
    :param hint_key: str | None 自定义提示行的 i18n key
    :param hint_params: dict[str, Any] | None 提示行模板的填充参数
    :param candidates: list[str] | None 相似名称候选
    :param depth: int 最多保留的用户帧数量
    :param logger: Any 指定 logger 实例（默认使用 ``Core.logger.logger``）

    :example:
    >>> try:
    ...     risky_init()
    ... except Exception as e:
    ...     log_diagnostic(e)
    """
    if logger is None:
        try:
            from ..Core.logger import logger as _logger

            logger = _logger
        except (ImportError, AttributeError):
            return

    block = format_diagnostic_block(
        exc,
        hint_key=hint_key,
        hint_params=hint_params,
        candidates=candidates,
        depth=depth,
    )
    if block:
        logger.error(block)


def handler_source_loc(handler: Any) -> str:
    """
    生成事件处理器的定义位置标注（慢日志归因用）

    返回形如 ``" (module.path:123)"`` 的标注串，拼接在处理器名后，
    让 ``Main._handle_message`` 这类自定方法名能一眼定位到定义文件。
    对 ``functools.wraps`` 包装的处理器自动经 ``__wrapped__`` 下钻到原始
    函数取位置（包装函数的 ``__module__`` 被复制自原函数而 ``__code__``
    是框架内包装定义处，直接取会错配）；对绑定方法取底层函数。
    无源码信息（内置函数 / partial 等）时返回空串。

    :param handler: 事件处理器（函数 / 绑定方法 / wraps 包装函数）
    :return: 位置标注串（含前导空格；无源码信息时为空串）

    :example:
    >>> handler_source_loc(my_handler)
    ' (my_module.views:42)'
    """
    try:
        fn = getattr(handler, "__func__", handler)  # 绑定方法取底层函数
        fn = getattr(fn, "__wrapped__", fn)  # wraps 包装下钻到原始函数
        code = getattr(fn, "__code__", None)
        module = getattr(fn, "__module__", "") or ""
        if code is not None and module:
            return f" ({module}:{code.co_firstlineno})"
    except Exception:
        pass
    return ""


def _coro_await_frames(coro: Any, max_depth: int = 64) -> list:
    """
    沿协程 ``cr_await`` 等待链收集帧（从最外层到最深挂起点）

    {!--< internal-use >!--}
    ``Task.get_stack()`` 只返回协程根帧的 ``f_back`` 调用链——协程 ``await``
    另一个协程时不产生调用栈关系，内层帧拿不到；等待链须沿 ``cr_await``
    逐级下钻（即 asyncio 调试输出挂起位置的同一机制）。

    :param coro: 协程对象（Task 的根协程）
    :param max_depth: 最大下钻深度（防循环引用兜底）
    :return: 帧列表（frames[0] 最外层，末位为最深挂起帧）
    """
    frames: list = []
    seen: set[int] = set()
    current = coro
    while current is not None and max_depth > 0:
        key = id(current)
        if key in seen:
            break
        seen.add(key)
        max_depth -= 1
        frame = getattr(current, "cr_frame", None)
        if frame is not None:
            frames.append(frame)
        current = getattr(current, "cr_await", None)
    return frames


def deepest_user_frame(task: Any) -> str:
    """
    抓取运行中 Task 协程等待链最深的用户代码帧（慢执行定位）

    事件处理器执行超过阈值时，结束统计只能给出总耗时；本函数在执行中
    沿 Task 根协程的 ``cr_await`` 等待链下钻，返回最靠近挂起点（await 处）
    的非框架帧描述，直接定位业务代码的等待位置——无论等待的是 AI /
    HTTP 还是任何第三方库。Task 未在等待（CPU 密集 / 已结束 / 无用户帧）
    时返回空串。

    :param task: 运行中的 asyncio.Task
    :return: 形如 ``"my_module/client.py:88 in chat"`` 的描述串；无法采样时为空串

    :example:
    >>> deepest_user_frame(asyncio.current_task())
    'QvQChat/AIEngine/client.py:88 in chat'
    """
    try:
        frames = _coro_await_frames(task.get_coro())
    except Exception:
        return ""
    for frame in reversed(frames):
        code = frame.f_code
        try:
            if _is_internal_frame(code.co_filename):
                continue
            return f"{_short_filename(code.co_filename)}:{frame.f_lineno} in {code.co_name}"
        except Exception:
            continue  # 单帧格式化失败跳过，继续尝试更外层帧
    return ""


__all__ = [
    "deepest_user_frame",
    "extract_user_frame",
    "format_diagnostic_block",
    "handler_source_loc",
    "log_diagnostic",
]
