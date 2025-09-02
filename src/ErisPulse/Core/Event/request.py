"""
ErisPulse 请求处理模块

提供基于装饰器的请求事件处理功能

{!--< tips >!--}
1. 支持好友请求、群邀请等不同类型请求
2. 可以通过返回特定值来同意或拒绝请求
{!--< /tips >!--}
"""

from .base import BaseEventHandler
from typing import Callable, Dict, Any

class RequestHandler:
    """
    请求事件处理器
    
    提供请求事件处理功能
    """
    
    def __init__(self):
        self.handler = BaseEventHandler("request", "request")
    
    def on_request(self, priority: int = 0):
        """
        通用请求事件装饰器
        
        :param priority: 处理器优先级
        :return: 装饰器函数
        """
        def decorator(func: Callable):
            self.handler.register(func, priority)
            return func
        return decorator
    
    def remove_request_handler(self, handler: Callable) -> bool:
        """
        取消注册通用请求事件处理器
        
        :param handler: 要取消注册的处理器
        :return: 是否成功取消注册
        """
        return self.handler.unregister(handler)
    
    def on_friend_request(self, priority: int = 0):
        """
        好友请求事件装饰器
        
        :param priority: 处理器优先级
        :return: 装饰器函数
        """
        def condition(event: Dict[str, Any]) -> bool:
            return event.get("detail_type") == "friend"
        
        def decorator(func: Callable):
            self.handler.register(func, priority, condition)
            return func
        return decorator
    
    def remove_friend_request_handler(self, handler: Callable) -> bool:
        """
        取消注册好友请求事件处理器
        
        :param handler: 要取消注册的处理器
        :return: 是否成功取消注册
        """
        return self.handler.unregister(handler)
    
    def on_group_request(self, priority: int = 0):
        """
        群邀请请求事件装饰器
        
        :param priority: 处理器优先级
        :return: 装饰器函数
        """
        def condition(event: Dict[str, Any]) -> bool:
            return event.get("detail_type") == "group"
        
        def decorator(func: Callable):
            self.handler.register(func, priority, condition)
            return func
        return decorator
    
    def remove_group_request_handler(self, handler: Callable) -> bool:
        """
        取消注册群邀请请求事件处理器
        
        :param handler: 要取消注册的处理器
        :return: 是否成功取消注册
        """
        return self.handler.unregister(handler)
    
    def _clear_request_handlers(self):
        """
        {!--< internal-use >!--}
        清除所有已注册的请求处理器
        
        :return: 被清除的处理器数量
        """
        return self.handler._clear_handlers()
    
request = RequestHandler()