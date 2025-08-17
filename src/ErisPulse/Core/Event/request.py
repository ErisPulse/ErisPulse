"""
ErisPulse 请求处理模块

提供基于装饰器的请求事件处理功能
"""

from .base import BaseEventHandler
from .manager import event_manager
from typing import Callable, Dict, Any

class RequestHandler:
    """
    请求处理器
    
    提供不同类型请求事件的处理功能（如好友申请、群邀请等）
    """
    
    def __init__(self):
        """
        初始化请求处理器
        """
        self.handler = event_manager.create_event_handler("request", "request")
    
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

request = RequestHandler()