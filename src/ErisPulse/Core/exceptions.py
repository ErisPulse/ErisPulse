"""
ErisPulse 全局异常处理系统

提供统一的异常捕获和格式化功能，支持同步和异步代码的异常处理。
"""

import sys
import traceback
import asyncio
import os
from typing import Dict, Any, Type

class ExceptionHandler:
    @staticmethod
    def format_exception(exc_type: Type[Exception], exc_value: Exception, exc_traceback: Any) -> str:
        """
        :param exc_type: 异常类型
        :param exc_value: 异常值
        :param exc_traceback: 追踪信息
        :return: 格式化后的异常信息
        """
        tb_list = traceback.extract_tb(exc_traceback)
        if tb_list:
            last_frame = tb_list[-1]
            filename = os.path.basename(last_frame.filename)
            line_number = last_frame.lineno
            function_name = last_frame.name
            return f"ERROR: {filename}:{function_name}:{line_number}: {exc_type.__name__}: {exc_value}"
        else:
            return f"ERROR: {exc_type.__name__}: {exc_value}"
        
    @staticmethod
    def format_async_exception(exception: Exception) -> str:
        """
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

def global_exception_handler(exc_type: Type[Exception], exc_value: Exception, exc_traceback: Any) -> None:
    """
    全局异常处理器
    
    :param exc_type: 异常类型
    :param exc_value: 异常值
    :param exc_traceback: 追踪信息
    """
    try:
        from ErisPulse import logger
        err_logger = logger.error
    except ImportError:
        err_logger = sys.stderr.write

    formatted_error = ExceptionHandler.format_exception(exc_type, exc_value, exc_traceback)
    err_logger(formatted_error)

def async_exception_handler(loop: asyncio.AbstractEventLoop, context: Dict[str, Any]) -> None:
    """
    异步异常处理器
    
    :param loop: 事件循环
    :param context: 上下文字典
    """
    try:
        from ErisPulse import logger
        err_logger = logger.error
    except ImportError:
        err_logger = sys.stderr.write
    
    exception = context.get('exception')
    if exception:
        try:
            formatted_error = ExceptionHandler.format_async_exception(exception)
            err_logger(formatted_error + '\n')
        except Exception:
            err_logger(f"ERROR: 捕捉器发生错误，原始异常信息：\n\n{exception}\n\n" + traceback.format_exc())
    else:
        msg = context.get('message', '未知异步错误')
        err_logger(f"ERROR: 未处理的异步错误: {msg}\n")

def setup_async_loop(loop: asyncio.AbstractEventLoop = None) -> None:   # type: ignore || 原因: 在实现中，已经完成了对于本方法的类型检查
    """
    为指定的事件循环设置异常处理器
    
    :param loop: 事件循环实例，如果为None则使用当前事件循环
    """
    if loop is None:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.get_event_loop()
    
    if loop is not None:
        loop.set_exception_handler(async_exception_handler)
    else:
        raise RuntimeError("无法获取有效的事件循环")
    
    loop.set_exception_handler(async_exception_handler)

sys.excepthook = global_exception_handler
try:
    asyncio.get_event_loop().set_exception_handler(async_exception_handler)
except RuntimeError:
    pass