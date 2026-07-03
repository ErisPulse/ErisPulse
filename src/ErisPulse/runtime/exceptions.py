"""
ErisPulse 全局异常处理系统

提供统一的异常捕获和格式化功能，支持同步和异步代码的异常处理。
在异常发生时自动生成友好的拼写纠错提示（"你是不是想写 xxx？"）。
"""

import asyncio
import os
import sys
import traceback
from typing import Any, Dict, List, Optional, Type

from .hints import (
    suggest_for_attribute_error,
    suggest_for_import_error,
    suggest_for_key_error,
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
            "core.hints.no_suggestion": "Check the name for possible typos.",
        }
        template = _FALLBACKS.get(key, key)
        try:
            return template.format(**kwargs)
        except Exception:
            return template


class ExceptionHandler:
    @staticmethod
    def format_exception(
        exc_type: Type[Exception], exc_value: Exception, exc_traceback: Any
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
                filename = os.path.basename(last_frame.filename)
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
                filename = os.path.basename(last_frame.filename)
                line_number = last_frame.lineno
                function_name = last_frame.name
                return f"ERROR: {filename}:{function_name}:{line_number}: {type(exception).__name__}: {exception}"

        return f"ERROR: {type(exception).__name__}: {exception}"

    @staticmethod
    def generate_hints(
        exc_value: Exception, exc_traceback: Any = None
    ) -> List[str]:
        """
        为异常生成友好的提示行

        根据 异常类型智能推断：
        - AttributeError: 查找对象上最相似的属性，给出"你是不是想写 xxx"
        - ImportError / ModuleNotFoundError: 暂不深入分析，给出通用提示

        :param exc_value: 异常对象
        :param exc_traceback: traceback 对象（可选，用于 AttributeError 上下文推断）
        :return: 提示行列表，无提示时为空列表
        """
        hints: List[str] = []

        if isinstance(exc_value, AttributeError):
            suggestion = suggest_for_attribute_error(
                exc_value, exc_traceback
            )
            if suggestion:
                hints.append(_t("core.hints.did_you_mean", name=suggestion))

        elif isinstance(exc_value, ImportError):
            suggestion = suggest_for_import_error(exc_value)
            if suggestion:
                hints.append(
                    _t("core.hints.import_did_you_mean", name=suggestion)
                )

        elif isinstance(exc_value, KeyError):
            suggestion = suggest_for_key_error(exc_value, exc_traceback)
            if suggestion:
                hints.append(
                    _t("core.hints.key_did_you_mean", name=suggestion)
                )

        return hints

    @staticmethod
    def format_exception_with_hints(
        exc_type: Type[Exception],
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
        base = ExceptionHandler.format_exception(
            exc_type, exc_value, exc_traceback
        )
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


def global_exception_handler(
    exc_type: Type[Exception], exc_value: Exception, exc_traceback: Any
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
    loop: asyncio.AbstractEventLoop, context: Dict[str, Any]
) -> None:
    """
    异步异常处理器

    :param loop: 事件循环
    :param context: 上下文字典
    """
    err_logger = _get_error_logger()

    exception = context.get("exception")
    if exception:
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
    "global_exception_handler",
    "async_exception_handler",
    "setup_exception_handling",
]
