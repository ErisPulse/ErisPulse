"""
ErisPulse 通知处理模块

提供基于装饰器的通知事件处理功能

{!--< tips >!--}
1. 支持好友、群组等不同类型通知
2. 支持成员变动等细粒度事件
{!--< /tips >!--}
"""

from .base import BaseEventHandler
from typing import Callable, Dict, Any

class NoticeHandler:
    def __init__(self):
        self.handler = BaseEventHandler("notice", "notice")
    
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