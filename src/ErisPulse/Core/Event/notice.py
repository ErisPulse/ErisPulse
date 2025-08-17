"""
ErisPulse 通知处理模块

提供基于装饰器的通知事件处理功能
"""

from .base import BaseEventHandler
from .manager import event_manager
from typing import Callable, Dict, Any

class NoticeHandler:
    """
    通知处理器
    
    提供不同类型通知事件的处理功能
    """
    
    def __init__(self):
        """
        初始化通知处理器
        """
        self.handler = event_manager.create_event_handler("notice", "notice")
    
    def on_notice(self, priority: int = 0):
        """
        通用通知事件装饰器
        
        :param priority: 处理器优先级
        :return: 装饰器函数
        """
        def decorator(func: Callable):
            self.handler.register(func, priority)
            return func
        return decorator
    
    def on_friend_add(self, priority: int = 0):
        """
        好友添加通知事件装饰器
        
        :param priority: 处理器优先级
        :return: 装饰器函数
        """
        def condition(event: Dict[str, Any]) -> bool:
            return event.get("detail_type") == "friend_increase"
        
        def decorator(func: Callable):
            self.handler.register(func, priority, condition)
            return func
        return decorator
    
    def on_friend_remove(self, priority: int = 0):
        """
        好友删除通知事件装饰器
        
        :param priority: 处理器优先级
        :return: 装饰器函数
        """
        def condition(event: Dict[str, Any]) -> bool:
            return event.get("detail_type") == "friend_decrease"
        
        def decorator(func: Callable):
            self.handler.register(func, priority, condition)
            return func
        return decorator
    
    def on_group_increase(self, priority: int = 0):
        """
        群成员增加通知事件装饰器
        
        :param priority: 处理器优先级
        :return: 装饰器函数
        """
        def condition(event: Dict[str, Any]) -> bool:
            return event.get("detail_type") == "group_member_increase"
        
        def decorator(func: Callable):
            self.handler.register(func, priority, condition)
            return func
        return decorator
    
    def on_group_decrease(self, priority: int = 0):
        """
        群成员减少通知事件装饰器
        
        :param priority: 处理器优先级
        :return: 装饰器函数
        """
        def condition(event: Dict[str, Any]) -> bool:
            return event.get("detail_type") == "group_member_decrease"
        
        def decorator(func: Callable):
            self.handler.register(func, priority, condition)
            return func
        return decorator

notice = NoticeHandler()