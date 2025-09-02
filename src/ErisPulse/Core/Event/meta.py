"""
ErisPulse 元事件处理模块

提供基于装饰器的元事件处理功能

{!--< tips >!--}
1. 支持连接、断开连接等生命周期事件
2. 适用于系统状态监控和初始化操作
{!--< /tips >!--}
"""

from .base import BaseEventHandler
from typing import Callable, Dict, Any

class MetaHandler:
    """
    元事件处理器
    
    提供元事件处理功能，如连接、断开连接等
    """
    
    def __init__(self):
        self.handler = BaseEventHandler("meta", "meta")
    
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
    
    def remove_meta_handler(self, handler: Callable) -> bool:
        """
        取消注册通用元事件处理器
        
        :param handler: 要取消注册的处理器
        :return: 是否成功取消注册
        """
        return self.handler.unregister(handler)
    
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
    
    def remove_connect_handler(self, handler: Callable) -> bool:
        """
        取消注册连接事件处理器
        
        :param handler: 要取消注册的处理器
        :return: 是否成功取消注册
        """
        return self.handler.unregister(handler)
    
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
    
    def remove_disconnect_handler(self, handler: Callable) -> bool:
        """
        取消注册断开连接事件处理器
        
        :param handler: 要取消注册的处理器
        :return: 是否成功取消注册
        """
        return self.handler.unregister(handler)
    
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
    
    def remove_heartbeat_handler(self, handler: Callable) -> bool:
        """
        取消注册心跳事件处理器
        
        :param handler: 要取消注册的处理器
        :return: 是否成功取消注册
        """
        return self.handler.unregister(handler)
    
    def _clear_meta_handlers(self):
        """
        {!--< internal-use >!--}
        清除所有已注册的元事件处理器
        
        :return: 被清除的处理器数量
        """
        return self.handler._clear_handlers()

meta = MetaHandler()