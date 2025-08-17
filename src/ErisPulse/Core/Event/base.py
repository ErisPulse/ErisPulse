"""
ErisPulse 事件处理基础模块

提供事件处理的核心功能，包括事件注册、处理和中间件支持
"""

from .. import adapter, logger
from typing import Callable, Any, Dict, List, Optional, Union
import asyncio

class BaseEventHandler:
    """
    基础事件处理器
    
    提供事件处理的基本功能，包括处理器注册、中间件支持等
    """
    
    def __init__(self, event_type: str, module_name: str = None):
        """
        初始化事件处理器
        
        :param event_type: 事件类型
        :param module_name: 模块名称
        """
        self.event_type = event_type
        self.module_name = module_name
        self.handlers: List[Dict] = []
        self.middlewares: List[Callable] = []
    
    def middleware(self, func: Callable) -> Callable:
        """
        添加中间件
        
        :param func: 中间件函数
        :return: 中间件函数
        """
        self.middlewares.append(func)
        return func
    
    def register(self, handler: Callable, priority: int = 0, condition: Callable = None):
        """
        注册事件处理器
        
        :param handler: 事件处理器函数
        :param priority: 处理器优先级，数值越小优先级越高
        :param condition: 处理器条件函数，返回True时才会执行处理器
        """
        handler_info = {
            "func": handler,
            "priority": priority,
            "condition": condition,
            "module": self.module_name
        }
        self.handlers.append(handler_info)
        # 按优先级排序
        self.handlers.sort(key=lambda x: x["priority"])
        
        # 注册到适配器
        if self.event_type:
            adapter.on(self.event_type)(self._process_event)
    
    def __call__(self, priority: int = 0, condition: Callable = None):
        """
        装饰器方式注册事件处理器
        
        :param priority: 处理器优先级
        :param condition: 处理器条件函数
        :return: 装饰器函数
        """
        def decorator(func: Callable):
            self.register(func, priority, condition)
            return func
        return decorator
    
    async def _process_event(self, event: Dict[str, Any]):
        """
        处理事件
        
        {!--< internal-use >!--}
        内部使用的方法，用于处理事件
        
        :param event: 事件数据
        """
        # 执行中间件
        processed_event = event
        for middleware in self.middlewares:
            try:
                if asyncio.iscoroutinefunction(middleware):
                    processed_event = await middleware(processed_event)
                else:
                    processed_event = middleware(processed_event)
            except Exception as e:
                logger.error(f"中间件执行错误: {e}")
        
        # 执行处理器
        for handler_info in self.handlers:
            condition = handler_info.get("condition")
            # 检查条件
            if condition and not condition(processed_event):
                continue
                
            handler = handler_info["func"]
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(processed_event)
                else:
                    handler(processed_event)
            except Exception as e:
                logger.error(f"事件处理器执行错误: {e}")
    
    def unregister(self, handler: Callable):
        """
        注销事件处理器
        
        :param handler: 要注销的事件处理器
        """
        self.handlers = [h for h in self.handlers if h["func"] != handler]