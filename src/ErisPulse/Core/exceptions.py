# exceptions.py (新文件名)
"""
ErisPulse 全局异常处理系统

提供统一的异常捕获和格式化功能，支持同步和异步代码的异常处理。
"""

import sys
import traceback
import asyncio
from typing import Dict, Any, Type
from .logger import logger

class ExceptionHandler:
    """异常处理器类"""
    
    @staticmethod
    def format_exception(exc_type: Type[Exception], exc_value: Exception, exc_traceback: Any) -> str:
        """
        格式化异常信息
        
        :param exc_type: 异常类型
        :param exc_value: 异常值
        :param exc_traceback: 追踪信息
        :return: 格式化后的异常信息
        """
        RED = '\033[91m'
        YELLOW = '\033[93m'
        BLUE = '\033[94m'
        RESET = '\033[0m'
        
        error_title = f"{RED}{exc_type.__name__}{RESET}: {YELLOW}{exc_value}{RESET}"
        traceback_lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
        
        colored_traceback = []
        for line in traceback_lines:
            if "File " in line and ", line " in line:
                parts = line.split(', line ')
                colored_line = f"{BLUE}{parts[0]}{RESET}, line {parts[1]}"
                colored_traceback.append(colored_line)
            else:
                colored_traceback.append(f"{RED}{line}{RESET}")
        
        return f"""
{error_title}
{RED}Traceback:{RESET}
{''.join(colored_traceback)}"""

    @staticmethod
    def format_async_exception(exception: Exception) -> str:
        """
        格式化异步异常信息
        
        :param exception: 异常对象
        :return: 格式化后的异常信息
        """
        RED = '\033[91m'
        YELLOW = '\033[93m'
        BLUE = '\033[94m'
        RESET = '\033[0m'
        
        tb = ''.join(traceback.format_exception(type(exception), exception, exception.__traceback__))
        
        colored_tb = []
        for line in tb.split('\n'):
            if "File " in line and ", line " in line:
                parts = line.split(', line ')
                colored_line = f"{BLUE}{parts[0]}{RESET}, line {parts[1]}"
                colored_tb.append(colored_line)
            else:
                colored_tb.append(f"{RED}{line}{RESET}")
        
        return f"""{RED}{type(exception).__name__}{RESET}: {YELLOW}{exception}{RESET}
{RED}Traceback:{RESET}
{''.join(colored_tb)}"""

def global_exception_handler(exc_type: Type[Exception], exc_value: Exception, exc_traceback: Any) -> None:
    """
    全局异常处理器
    
    :param exc_type: 异常类型
    :param exc_value: 异常值
    :param exc_traceback: 追踪信息
    """
    try:
        formatted_error = ExceptionHandler.format_exception(exc_type, exc_value, exc_traceback)
        sys.stderr.write(formatted_error)
        # 同时记录到日志系统
        logger.error(f"未捕获异常: {exc_type.__name__}: {exc_value}")
    except Exception:
        # 防止异常处理过程中出现异常
        sys.stderr.write(f"Uncaught exception: {exc_type.__name__}: {exc_value}\n")

def async_exception_handler(loop: asyncio.AbstractEventLoop, context: Dict[str, Any]) -> None:
    """
    异步异常处理器
    
    :param loop: 事件循环
    :param context: 上下文字典
    """
    RED = '\033[91m'
    YELLOW = '\033[93m'
    RESET = '\033[0m'
    
    exception = context.get('exception')
    if exception:
        try:
            formatted_error = ExceptionHandler.format_async_exception(exception)
            sys.stderr.write(formatted_error)
            # 同时记录到日志系统
            logger.error(f"异步异常: {type(exception).__name__}: {exception}")
        except Exception:
            sys.stderr.write(f"{RED}Async Error{RESET}: {YELLOW}{exception}{RESET}\n")
    else:
        msg = context.get('message', 'Unknown async error')
        sys.stderr.write(f"{RED}Async Error{RESET}: {YELLOW}{msg}{RESET}\n")
        logger.error(f"异步错误: {msg}")

# 注册全局异常处理器
sys.excepthook = global_exception_handler
try:
    asyncio.get_event_loop().set_exception_handler(async_exception_handler)
except RuntimeError:
    # 如果还没有事件循环，则在创建时设置
    pass

# 提供一个函数用于在创建新事件循环时设置异常处理器
def setup_async_exception_handler(loop: asyncio.AbstractEventLoop = None) -> None:
    """
    设置异步异常处理器
    
    :param loop: 事件循环，如果为None则使用当前事件循环
    """
    if loop is None:
        loop = asyncio.get_event_loop()
    loop.set_exception_handler(async_exception_handler)