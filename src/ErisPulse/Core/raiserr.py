"""
ErisPulse 错误管理系统

提供错误类型注册、抛出和管理功能，集成全局异常处理。支持自定义错误类型、错误链追踪和全局异常捕获。

{!--< tips >!--}
1. 使用register注册自定义错误类型
2. 通过info获取错误信息
3. 自动捕获未处理异常
{!--< /tips >!--}
"""

import sys
import traceback
import asyncio
from typing import Dict, Any, Optional, Type, Callable, List, Set, Tuple, Union

class Error:
    """
    错误管理器
    
    提供错误类型注册和抛出功能
    
    {!--< tips >!--}
    1. 通过register方法注册自定义错误类型
    2. 通过动态属性访问抛出错误
    3. 通过info方法获取错误信息
    {!--< /tips >!--}
    """
    
    def __init__(self):
        self._types = {}

    def register(self, name: str, doc: str = "", base: Type[Exception] = Exception) -> Type[Exception]:
        """
        注册新的错误类型
        
        :param name: 错误类型名称
        :param doc: 错误描述文档
        :param base: 基础异常类
        :return: 注册的错误类
        
        :example:
        >>> # 注册简单错误
        >>> raiserr.register("SimpleError", "简单的错误类型")
        >>> # 注册自定义基类的错误
        >>> raiserr.register("AdvancedError", "高级错误", CustomBaseError)
        """
        if name not in self._types:
            err_cls = type(name, (base,), {"__doc__": doc})
            self._types[name] = err_cls
        return self._types[name]

    def __getattr__(self, name: str) -> Callable[..., None]:
        """
        动态获取错误抛出函数
        
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
        
        :param name: 错误类型名称(可选)
        :return: 错误信息字典
        
        :example:
        >>> # 获取特定错误信息
        >>> error_info = raiserr.info("SimpleError")
        >>> # 获取所有错误信息
        >>> all_errors = raiserr.info()
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

# 全局异常处理器
def global_exception_handler(exc_type: Type[Exception], exc_value: Exception, exc_traceback: Any) -> None:
    """
    {!--< internal-use >!--}
    全局异常处理器
    
    :param exc_type: 异常类型
    :param exc_value: 异常值
    :param exc_traceback: 追踪信息
    """
    error_message = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    raiserr.ExternalError(
        f"{exc_type.__name__}: {exc_value}\nTraceback:\n{error_message}"
    )
    
def async_exception_handler(loop: asyncio.AbstractEventLoop, context: Dict[str, Any]) -> None:
    """
    {!--< internal-use >!--}
    异步异常处理器
    
    :param loop: 事件循环
    :param context: 上下文字典
    """
    exception = context.get('exception')
    tb = ''.join(traceback.format_exception(type(exception), exception, exception.__traceback__))
    raiserr.ExternalError(
        f"{type(exception).__name__}: {exception}\nTraceback:\n{tb}"
    )

sys.excepthook = global_exception_handler
asyncio.get_event_loop().set_exception_handler(async_exception_handler)