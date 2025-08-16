"""
ErisPulse 元事件处理模块

提供基于装饰器的元事件处理功能
"""

from .base import BaseEventHandler
from .manager import event_manager
from typing import Callable, Dict, Any

class MetaHandler:
    """
    元事件处理器
    
    提供元事件（如连接、断开连接、心跳等）的处理功能
    """
    
    def __init__(self):
        """
        初始化元事件处理器
        """
        self.handler = event_manager.create_event_handler("meta", "meta")
    
    def on_meta(self, priority: int = 0):
        """
        通用元事件装饰器
        
        :param priority: 处理器优先级
        :return: 装饰器函数
        """
        def decorator(func: Callable):
            self.handler.register(func, priority)
            return func
        return decorator
    
    def on_connect(self, priority: int = 0):
        """
        连接事件装饰器
        
        :param priority: 处理器优先级
        :return: 装饰器函数
        """
        def condition(event: Dict[str, Any]) -> bool:
            return event.get("detail_type") == "connect"
        
        def decorator(func: Callable):
            self.handler.register(func, priority, condition)
            return func
        return decorator
    
    def on_disconnect(self, priority: int = 0):
        """
        断开连接事件装饰器
        
        :param priority: 处理器优先级
        :return: 装饰器函数
        """
        def condition(event: Dict[str, Any]) -> bool:
            return event.get("detail_type") == "disconnect"
        
        def decorator(func: Callable):
            self.handler.register(func, priority, condition)
            return func
        return decorator
    
    def on_heartbeat(self, priority: int = 0):
        """
        心跳事件装饰器
        
        :param priority: 处理器优先级
        :return: 装饰器函数
        """
        def condition(event: Dict[str, Any]) -> bool:
            return event.get("detail_type") == "heartbeat"
        
        def decorator(func: Callable):
            self.handler.register(func, priority, condition)
            return func
        return decorator

# 创建全局元事件处理器实例
meta = MetaHandler()