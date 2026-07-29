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
import traceback
from pathlib import Path
from typing import Any

from .hints import best_match

_FRAMEWORK_ROOT: Path | None = None


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
    candidates: list[str] | None = None,
    depth: int = 3,
) -> str:
    """
    生成可日志输出的多行诊断文本

    将 ``extract_user_frame`` 的结果格式化为带缩进引导符（``→``）的多行字符串，
    末尾附加查看完整堆栈的提示行。

    :param exc: BaseException 异常对象
    :param hint_key: str | None 自定义提示行的 i18n key（默认使用通用提示）
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

            lines.append(i18n.t(hint_key))
        except Exception:
            lines.append(_t("core.diag.hint"))
    else:
        lines.append(_t("core.diag.hint"))

    return "\n".join(lines)


def log_diagnostic(
    exc: BaseException,
    *,
    hint_key: str | None = None,
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
        exc, hint_key=hint_key, candidates=candidates, depth=depth
    )
    if block:
        logger.error(block)


__all__ = [
    "extract_user_frame",
    "format_diagnostic_block",
    "log_diagnostic",
]
