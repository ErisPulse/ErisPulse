"""
ErisPulse 全局异常处理系统

提供统一的异常捕获和格式化功能，支持同步和异步代码的异常处理。
在异常发生时自动生成友好的拼写纠错提示（"你是不是想写 xxx？"）。
"""

import asyncio
import sys
import time
import traceback
from pathlib import Path
from typing import Any

from ..Core.i18n import i18n
from .hints import (
    suggest_for_attribute_error,
    suggest_for_connection_error,
    suggest_for_coroutine_attribute,
    suggest_for_erispulse_client_error,
    suggest_for_event_loop_error,
    suggest_for_import_error,
    suggest_for_invalid_await,
    suggest_for_key_error,
    suggest_for_missing_argument,
    suggest_for_name_error,
    suggest_for_not_callable,
    suggest_for_recursion_error,
    suggest_for_timeout_error,
    suggest_for_websocket_disconnect,
)


def _t(key: str, **kwargs) -> str:
    """
    {!--< internal-use >!--}
    尝试用 i18n 翻译，失败时用英文 fallback
    """
    try:
        from ..Core.i18n import i18n

        return i18n.t(key, **kwargs)
    except Exception:
        _FALLBACKS = {
            "core.hints.did_you_mean": "Hint: Did you mean '{name}'?",
            "core.hints.import_did_you_mean": "Hint: Did you mean to import '{name}'?",
            "core.hints.key_did_you_mean": "Hint: Did you mean '{name}'?",
            "core.hints.name_did_you_mean": "Hint: Did you mean '{name}'?",
            "core.hints.no_suggestion": "Check the name for possible typos.",
            "core.hints.event_loop_closed": "Hint: The event loop was closed. Common causes: 1) calling async code after the loop was shut down; 2) reusing a closed loop; 3) calling sync code that internally closed the loop. Try restarting the process or check for asyncio.run() / loop.close() misuse.",
            "core.hints.no_event_loop": "Hint: There is no current event loop. Common causes: 1) calling async code outside an asyncio context; 2) the loop was not created. Use asyncio.run() or ensure a loop is running before awaiting.",
            "core.hints.asyncio_run_in_loop": "Hint: asyncio.run() cannot be called from a running event loop. Use 'await' on the coroutine directly, or schedule it as a task instead of nesting asyncio.run().",
            "core.hints.coroutine_never_awaited": "Hint: A coroutine was never awaited. You created a coroutine object but forgot to 'await' it. Add 'await' in front of the coroutine call.",
            "core.hints.invalid_await": "Hint: You awaited a non-coroutine object. Common causes: 1) the function is missing the 'async' keyword; 2) you awaited a plain return value instead of a coroutine; 3) you called a synchronous wrapper around an async function. Add 'async' to the function definition or remove the 'await'.",
            "core.hints.coroutine_attribute": "Hint: You accessed an attribute on a coroutine object. You likely forgot to 'await' the coroutine before accessing its result.",
            "core.hints.missing_argument": "Hint: A required positional argument is missing. Check the function signature and the number of arguments you passed.",
            "core.hints.not_callable": "Hint: This object is not callable. Common causes: 1) you assigned a non-function value to a name that shadows a function; 2) you forgot to instantiate a class (missing parentheses).",
            "core.hints.not_subscriptable": "Hint: This object is not subscriptable (cannot use []). It may be None or a non-sequence type; check whether the variable holds what you expect.",
            "core.hints.not_iterable": "Hint: This object is not iterable. Common causes: 1) it is None; 2) you expected a list/iterator but got a scalar. Verify the variable's type before iterating.",
            "core.hints.recursion_error": "Hint: Maximum recursion depth exceeded. Common causes: 1) the recursion has no base case; 2) an unexpected self-call exists. Check the recursion exit condition, or rewrite iteratively.",
            "core.hints.timeout_error": "Hint: Operation timed out. Common causes: 1) a network request did not finish in time; 2) the asyncio.wait_for timeout is too short; 3) the target service is slow or unreachable. Check connectivity and timeout settings.",
            "core.hints.connection_error": "Hint: Network connection failed. Common causes: 1) the target address/port is unreachable; 2) the service is not running; 3) a firewall is blocking. Check the target service status and connectivity.",
            "core.hints.connection_refused": "Hint: Connection refused. The target port may not be listening or the service is not running; confirm the target service is running.",
            "core.hints.connection_reset": "Hint: Connection reset by peer. Common causes: 1) the peer crashed or forcibly closed; 2) a middlebox dropped the connection. Retry or check the peer status.",
            "core.hints.client_connection_error": "Hint: Client connection failed (ErisPulse ClientConnectionError). Common causes: 1) DNS resolution failed; 2) target address unreachable; 3) connection refused. Check connectivity and the target address.",
            "core.hints.client_timeout_error": "Hint: Client request timed out (ErisPulse ClientTimeoutError). Common causes: 1) connection timeout; 2) server too slow; 3) timeout setting too short. Increase timeout or check the server status.",
            "core.hints.http_status_error": "Hint: Server returned an error status code (ErisPulse HTTPStatusError). Check request parameters and authentication.",
            "core.hints.http_client_error": "Hint: 4xx client error. Common causes: 1) bad request parameters; 2) unauthenticated or insufficient permissions; 3) resource not found. Check the request URL, parameters, and auth token.",
            "core.hints.http_server_error": "Hint: 5xx server error. This is a server-side issue. Common causes: 1) internal server exception; 2) server overloaded; 3) service unavailable. Retry later or contact the service provider.",
            "core.hints.websocket_abnormal_close": "Hint: WebSocket closed abnormally (non-1000/1001 close code). Common causes: 1) network drop; 2) server/client crash; 3) protocol error. Check the network and server logs.",
            "core.deprecated.kwarg": "The keyword argument '{old}' of {owner} is deprecated; use '{new}' or a positional argument instead. It will be removed in a future version.",
        }
        template = _FALLBACKS.get(key, key)
        try:
            return template.format(**kwargs)
        except Exception:
            return template


class ExceptionHandler:
    @staticmethod
    def format_exception(
        exc_type: type[Exception], exc_value: Exception, exc_traceback: Any
    ) -> str:
        """
        格式化异常信息

        :param exc_type: 异常类型
        :param exc_value: 异常值
        :param exc_traceback: 追踪信息
        :return: 格式化后的异常信息
        """
        if exc_traceback is not None:
            tb_list = traceback.extract_tb(exc_traceback)
            if tb_list:
                last_frame = tb_list[-1]
                filename = Path(last_frame.filename).name
                line_number = last_frame.lineno
                function_name = last_frame.name
                return f"ERROR: {filename}:{function_name}:{line_number}: {exc_type.__name__}: {exc_value}"
        return f"ERROR: {exc_type.__name__}: {exc_value}"

    @staticmethod
    def format_async_exception(exception: Exception) -> str:
        """
        格式化异步异常信息

        :param exception: 异常对象
        :return: 格式化后的异常信息
        """
        if exception.__traceback__:
            tb_list = traceback.extract_tb(exception.__traceback__)
            if tb_list:
                last_frame = tb_list[-1]
                filename = Path(last_frame.filename).name
                line_number = last_frame.lineno
                function_name = last_frame.name
                return f"ERROR: {filename}:{function_name}:{line_number}: {type(exception).__name__}: {exception}"

        return f"ERROR: {type(exception).__name__}: {exception}"

    @staticmethod
    def generate_hints(
        exc_value: BaseException, exc_traceback: Any = None
    ) -> list[str]:
        """
        为异常生成友好的提示行

        根据异常类型智能推断：
        - BaseException 子类（CancelledError / KeyboardInterrupt）：关停/取消场景
        - AttributeError: 查找对象上最相似的属性，给出“你是不是想写 xxx”
        - ImportError / ModuleNotFoundError: 给出拼写建议
        - NameError / KeyError: 从上下文中找最相近的名称
        - TypeError: 多种子场景（await / 缺参 / 不可调用 / 不可下标）
        - RuntimeError: 事件循环相关多种场景
        - RecursionError / TimeoutError / ConnectionError: 常见运行期错误

        :param exc_value: 异常对象
        :param exc_traceback: traceback 对象（可选，用于上下文推断）
        :return: 提示行列表，无提示时为空列表
        """
        hints: list[str] = []

        # 注意：控制流异常（CancelledError / KeyboardInterrupt / SystemExit）
        # 已在 global_exception_handler / async_exception_handler 中提前处理，
        # 不会走到这里。以下仅处理真正的“错误”类异常。

        # ---------- Exception 级别 ----------
        if isinstance(exc_value, AttributeError):
            # 优先检测“对协程对象访问属性”（忘记 await）
            coro_hint = suggest_for_coroutine_attribute(exc_value, exc_traceback)
            if coro_hint:
                hints.append(_t(f"core.hints.{coro_hint}"))
            else:
                suggestion = suggest_for_attribute_error(exc_value, exc_traceback)
                if suggestion:
                    hints.append(_t("core.hints.did_you_mean", name=suggestion))

        elif isinstance(exc_value, ImportError):
            suggestion = suggest_for_import_error(exc_value)
            if suggestion:
                hints.append(_t("core.hints.import_did_you_mean", name=suggestion))

        elif isinstance(exc_value, KeyError):
            suggestion = suggest_for_key_error(exc_value, exc_traceback)
            if suggestion:
                hints.append(_t("core.hints.key_did_you_mean", name=suggestion))

        elif isinstance(exc_value, RecursionError):
            # 必须在 RuntimeError 之前检查（RecursionError 继承自 RuntimeError）
            hints.append(_t(f"core.hints.{suggest_for_recursion_error(exc_value)}"))

        elif isinstance(exc_value, RuntimeError):
            suggestion = suggest_for_event_loop_error(exc_value)
            if suggestion:
                hints.append(_t(f"core.hints.{suggestion}"))

        elif isinstance(exc_value, NameError):
            suggestion = suggest_for_name_error(exc_value, exc_traceback)
            if suggestion:
                hints.append(_t("core.hints.name_did_you_mean", name=suggestion))

        elif isinstance(exc_value, TypeError):
            # 依次尝试多个 TypeError 子场景，命中即止
            for type_suggester in (
                suggest_for_invalid_await,
                suggest_for_missing_argument,
                suggest_for_not_callable,
            ):
                suggestion = type_suggester(exc_value)
                if suggestion:
                    hints.append(_t(f"core.hints.{suggestion}"))
                    break

        elif isinstance(exc_value, TimeoutError):
            hints.append(_t(f"core.hints.{suggest_for_timeout_error(exc_value)}"))

        elif isinstance(exc_value, ConnectionError):
            hint = suggest_for_connection_error(exc_value)
            if hint:
                hints.append(_t(f"core.hints.{hint}"))

        else:
            # ErisPulse 自定义异常体系（ClientConnectionError / HTTPStatusError 等）
            # 放在最后，避免与原生异常分支冲突
            ws_hint = suggest_for_websocket_disconnect(exc_value)
            if ws_hint:
                # 正常关闭（code 1000/1001）不附加提示，属于生命周期事件
                if ws_hint != "websocket_normal_close":
                    hints.append(_t(f"core.hints.{ws_hint}"))
            else:
                ep_hint = suggest_for_erispulse_client_error(exc_value)
                if ep_hint:
                    hints.append(_t(f"core.hints.{ep_hint}"))

        return hints

    @staticmethod
    def format_exception_with_hints(
        exc_type: type[Exception],
        exc_value: Exception,
        exc_traceback: Any,
    ) -> str:
        """
        格式化异常信息并附带友好提示

        :param exc_type: 异常类型
        :param exc_value: 异常值
        :param exc_traceback: 追踪信息
        :return: 格式化后的异常信息（可能包含多行提示）
        """
        base = ExceptionHandler.format_exception(exc_type, exc_value, exc_traceback)
        hint_lines = ExceptionHandler.generate_hints(exc_value, exc_traceback)
        if hint_lines:
            return base + "\n" + "\n".join(hint_lines)
        return base


def _get_error_logger():
    """
    {!--< internal-use >!--}
    获取错误日志输出函数，优先使用框架 logger，失败时 fallback 到 stderr
    """
    try:
        from ..Core import logger

        return logger.error
    except (ImportError, AttributeError):
        return sys.stderr.write


# 事件循环关闭/异常退出时，asyncio 通过异常处理器上报的"清理噪音"消息。
# 这些源于强制关停时残留任务的销毁过程，不代表运行期错误，若按 ERROR 输出会在
# 退出时刷屏大量重复行（如 uvicorn 端口绑定失败 sys.exit(3) 后的级联关停）。
_ASYNC_SHUTDOWN_NOISE_MESSAGES: tuple[str, ...] = (
    "Task was destroyed but it is pending!",
)

# 折叠相同关停噪音的窗口（秒）。窗口内重复消息静默折叠，仅记录一次并附带累计次数。
_ASYNC_NOISE_FOLD_WINDOW_SECS: float = 2.0

# 噪音折叠状态: {消息 -> (累计次数, 首次时间戳)}
_async_noise_state: dict[str, tuple[int, float]] = {}


def _log_async_noise(message: str) -> None:
    """
    {!--< internal-use >!--}
    记录异步关停场景的低级别噪音日志（TRACE），无框架 logger 时静默丢弃

    这类消息仅在退出/关停时产生，降级为 TRACE 既避免刷屏，也保留排查线索
    （日志订阅器可显式订阅 TRACE 级别查看）。
    """
    try:
        from ..Core import logger

        logger.trace(message)
    except (ImportError, AttributeError):
        pass


def _fold_async_noise(message: str) -> None:
    """
    {!--< internal-use >!--}
    折叠相同噪音消息：窗口内重复只输出一次，并附带被折叠的累计次数
    """
    key = message.strip()
    now = time.monotonic()
    count, first_seen = _async_noise_state.get(key, (0, now))
    if count > 0 and now - first_seen < _ASYNC_NOISE_FOLD_WINDOW_SECS:
        _async_noise_state[key] = (count + 1, first_seen)
        return
    _async_noise_state[key] = (1, now)
    suffix = i18n.t("core.exceptions.folded_suffix", count=count) if count else ""
    _log_async_noise(f"Async - {key}{suffix}")


def global_exception_handler(
    exc_type: type[Exception], exc_value: Exception, exc_traceback: Any
) -> None:
    """
    全局异常处理器

    :param exc_type: 异常类型
    :param exc_value: 异常值
    :param exc_traceback: 追踪信息
    """
    err_logger = _get_error_logger()

    formatted = ExceptionHandler.format_exception_with_hints(
        exc_type, exc_value, exc_traceback
    )
    err_logger(formatted)


def async_exception_handler(
    loop: asyncio.AbstractEventLoop, context: dict[str, Any]
) -> None:
    """
    异步异常处理器

    :param loop: 事件循环
    :param context: 上下文字典
    """
    err_logger = _get_error_logger()

    exception = context.get("exception")
    if exception:
        # SystemExit / KeyboardInterrupt 是主动退出/关停的控制流信号（如 uvicorn
        # 端口绑定失败时 sys.exit(3)），不是异步错误，按 TRACE 记录避免退出时刷屏。
        if isinstance(exception, (SystemExit, KeyboardInterrupt)):
            _log_async_noise(
                f"Async - control-flow {type(exception).__name__}: {exception!r}"
            )
            return
        try:
            base = ExceptionHandler.format_async_exception(exception)
            hint_lines = ExceptionHandler.generate_hints(
                exception, exception.__traceback__
            )
            if hint_lines:
                err_logger(base + "\n" + "\n".join(hint_lines) + "\n")
            else:
                err_logger(base + "\n")
        except Exception:
            err_logger(f"ERROR Raw:\n\n{exception}\n\n" + traceback.format_exc())
    else:
        msg = context.get("message", "Async - Unknown Error")
        # 事件循环关闭时残留任务被销毁是正常清理噪音，折叠降级为 TRACE，避免刷屏
        if any(marker in msg for marker in _ASYNC_SHUTDOWN_NOISE_MESSAGES):
            _fold_async_noise(msg)
            return
        err_logger(f"Async - Error: {msg}\n")


def setup_exception_handling() -> None:
    """
    设置全局异常处理系统

    包括同步异常和异步异常的处理钩子
    """
    # 设置同步异常钩子
    sys.excepthook = global_exception_handler

    # 尝试设置异步异常处理器
    try:
        loop = asyncio.get_running_loop()
        loop.set_exception_handler(async_exception_handler)
    except RuntimeError:
        # 没有运行中的事件循环，这在初始化时是正常的
        # 异步异常处理器会在事件循环启动后通过其他方式设置
        pass


__all__ = [
    "ExceptionHandler",
    "async_exception_handler",
    "global_exception_handler",
    "setup_exception_handling",
]
