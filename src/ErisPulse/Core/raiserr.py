"""
ErisPulse 错误管理系统

提供全局异常捕获功能。不再推荐使用自定义错误注册功能。

{!--< tips >!--}
1. 请使用Python原生异常抛出方法
2. 系统会自动捕获并格式化所有未处理异常
3. 注册功能已标记为弃用，将在未来版本移除
{!--< /tips >!--}
"""

import sys
import traceback
import asyncio
from typing import Dict, Any, Optional, Type, Callable, List, Set, Tuple, Union

class Error:
    """
    错误管理器
    
    {!--< deprecated >!--} 请使用Python原生异常抛出方法 | 2025-07-18
    
    {!--< tips >!--}
    1. 注册功能将在未来版本移除
    2. 请直接使用raise Exception("message")方式抛出异常
    {!--< /tips >!--}
    """
    
    def __init__(self):
        self._types = {}

    def register(self, name: str, doc: str = "", base: Type[Exception] = Exception) -> Type[Exception]:
        """
        注册新的错误类型
        
        {!--< deprecated >!--} 请使用Python原生异常抛出方法 | 2025-07-18
        
        :param name: 错误类型名称
        :param doc: 错误描述文档
        :param base: 基础异常类
        :return: 注册的错误类
        """
        if name not in self._types:
            err_cls = type(name, (base,), {"__doc__": doc})
            self._types[name] = err_cls
        return self._types[name]

    def __getattr__(self, name: str) -> Callable[..., None]:
        """
        动态获取错误抛出函数
        
        {!--< deprecated >!--} 请使用Python原生异常抛出方法 | 2025-07-18
        
        :param name: 错误类型名称
        :return: 错误抛出函数
        
        :raises AttributeError: 当错误类型未注册时抛出
        """
        def raiser(msg: str, exit: bool = False) -> None:
            """
            错误抛出函数
            
            :param msg: 错误消息
            :param exit: 是否退出程序
            """
            from .logger import logger
            err_cls = self._types.get(name) or self.register(name)
            exc = err_cls(msg)

            red = '\033[91m'
            reset = '\033[0m'

            logger.error(f"{red}{name}: {msg} | {err_cls.__doc__}{reset}")
            logger.error(f"{red}{ ''.join(traceback.format_stack()) }{reset}")

            if exit:
                raise exc
        return raiser

    def info(self, name: Optional[str] = None) -> Dict[str, Any]:
        """
        获取错误信息
        
        {!--< deprecated >!--} 此功能将在未来版本移除 | 2025-07-18
        
        :param name: 错误类型名称(可选)
        :return: 错误信息字典
        """
        result = {}
        for err_name, err_cls in self._types.items():
            result[err_name] = {
                "type": err_name,
                "doc": getattr(err_cls, "__doc__", ""),
                "class": err_cls,
            }
        if name is None:
            return result
        err_cls = self._types.get(name)
        if not err_cls:
            return {
                "type": None,
                "doc": None,
                "class": None,
            }
        return {
            "type": name,
            "doc": getattr(err_cls, "__doc__", ""),
            "class": err_cls,
        }


raiserr = Error()

def global_exception_handler(exc_type: Type[Exception], exc_value: Exception, exc_traceback: Any) -> None:
    """
    全局异常处理器
    
    :param exc_type: 异常类型
    :param exc_value: 异常值
    :param exc_traceback: 追踪信息
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
    
    full_error = f"""
{error_title}
{RED}Traceback:{RESET}
{colored_traceback}"""
    
    sys.stderr.write(full_error)

def async_exception_handler(loop: asyncio.AbstractEventLoop, context: Dict[str, Any]) -> None:
    """
    异步异常处理器
    
    :param loop: 事件循环
    :param context: 上下文字典
    """
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    
    exception = context.get('exception')
    if exception:
        tb = ''.join(traceback.format_exception(type(exception), exception, exception.__traceback__))
        
        colored_tb = []
        for line in tb.split('\n'):
            if "File " in line and ", line " in line:
                parts = line.split(', line ')
                colored_line = f"{BLUE}{parts[0]}{RESET}, line {parts[1]}"
                colored_tb.append(colored_line)
            else:
                colored_tb.append(f"{RED}{line}{RESET}")
        
        error_msg = f"""{RED}{type(exception).__name__}{RESET}: {YELLOW}{exception}{RESET}
{RED}Traceback:{RESET}
{colored_tb}"""
        sys.stderr.write(error_msg)
    else:
        msg = context.get('message', 'Unknown async error')
        sys.stderr.write(f"{RED}Async Error{RESET}: {YELLOW}{msg}{RESET}")

sys.excepthook = global_exception_handler
asyncio.get_event_loop().set_exception_handler(async_exception_handler)