"""
ErisPulse 消息处理模块

提供基于装饰器的消息事件处理功能
"""

from .base import BaseEventHandler
from .manager import event_manager
from .. import adapter
from typing import Callable, Dict, Any
import asyncio

class MessageHandler:
    """
    消息处理器
    
    提供不同类型消息事件的处理功能
    """
    
    def __init__(self):
        """
        初始化消息处理器
        """
        self.handler = event_manager.create_event_handler("message", "message")
    
    def on_message(self, priority: int = 0):
        """
        消息事件装饰器
        
        :param priority: 处理器优先级
        :return: 装饰器函数
        """
        def decorator(func: Callable):
            self.handler.register(func, priority)
            return func
        return decorator
    
    def on_private_message(self, priority: int = 0):
        """
        私聊消息事件装饰器
        
        :param priority: 处理器优先级
        :return: 装饰器函数
        """
        def condition(event: Dict[str, Any]) -> bool:
            return event.get("detail_type") == "private"
        
        def decorator(func: Callable):
            self.handler.register(func, priority, condition)
            return func
        return decorator
    
    def on_group_message(self, priority: int = 0):
        """
        群聊消息事件装饰器
        
        :param priority: 处理器优先级
        :return: 装饰器函数
        """
        def condition(event: Dict[str, Any]) -> bool:
            return event.get("detail_type") == "group"
        
        def decorator(func: Callable):
            self.handler.register(func, priority, condition)
            return func
        return decorator
    
    def on_at_message(self, priority: int = 0):
        """
        @消息事件装饰器
        
        :param priority: 处理器优先级
        :return: 装饰器函数
        """
        def condition(event: Dict[str, Any]) -> bool:
            # 检查消息中是否有@机器人
            message_segments = event.get("message", [])
            self_id = event.get("self", {}).get("user_id")
            
            for segment in message_segments:
                if segment.get("type") == "mention" and segment.get("data", {}).get("user_id") == self_id:
                    return True
            return False
        
        def decorator(func: Callable):
            self.handler.register(func, priority, condition)
            return func
        return decorator

# 创建全局消息处理器实例
message = MessageHandler()