"""
ErisPulse 生命周期管理模块

提供统一的生命周期事件管理和触发机制
"""

from typing import Callable, List, Dict
import asyncio
from .logger import logger

class LifecycleManager:
    """
    生命周期管理器
    
    管理SDK的生命周期事件，提供事件注册和触发功能
    """
    
    def __init__(self):
        self._handlers: Dict[str, List[Callable]] = {}
        
    def on(self, event: str) -> Callable:
        """
        注册生命周期事件处理器
        
        :param event: 事件名称
        :return: 装饰器函数
        """
        def decorator(func: Callable) -> Callable:
            if event not in self._handlers:
                self._handlers[event] = []
            self._handlers[event].append(func)
            return func
        return decorator
        
    async def emit(self, event: str, *args, **kwargs) -> None:
        """
        触发生命周期事件
        
        :param event: 事件名称
        :param args: 位置参数
        :param kwargs: 关键字参数
        """
        if event not in self._handlers:
            return
            
        logger.debug(f"触发生命周期事件: {event}")
        for handler in self._handlers[event]:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(*args, **kwargs)
                else:
                    handler(*args, **kwargs)
            except Exception as e:
                logger.error(f"生命周期事件处理器执行错误 {event}: {e}")

lifecycle = LifecycleManager()