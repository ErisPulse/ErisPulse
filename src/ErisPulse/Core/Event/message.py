"""
ErisPulse 消息处理模块

提供基于装饰器的消息事件处理功能

{!--< tips >!--}
1. 支持私聊、群聊消息分类处理
2. 支持@消息特殊处理
3. 支持自定义条件过滤
{!--< /tips >!--}
"""

from .base import BaseEventHandler
from typing import Callable, Dict, Any

class MessageHandler:
    """
    消息事件处理器
    
    提供不同类型消息事件的处理功能
    """
    
    def __init__(self):
        self.handler = BaseEventHandler("message", "message")
    
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
    
    def remove_message_handler(self, handler: Callable) -> bool:
        """
        取消注册消息事件处理器
        
        :param handler: 要取消注册的处理器
        :return: 是否成功取消注册
        """
        return self.handler.unregister(handler)
    
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
    
    def remove_private_message_handler(self, handler: Callable) -> bool:
        """
        取消注册私聊消息事件处理器
        
        :param handler: 要取消注册的处理器
        :return: 是否成功取消注册
        """
        return self.handler.unregister(handler)
    
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
    
    def remove_group_message_handler(self, handler: Callable) -> bool:
        """
        取消注册群聊消息事件处理器
        
        :param handler: 要取消注册的处理器
        :return: 是否成功取消注册
        """
        return self.handler.unregister(handler)
    
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
    
    def remove_at_message_handler(self, handler: Callable) -> bool:
        """
        取消注册@消息事件处理器
        
        :param handler: 要取消注册的处理器
        :return: 是否成功取消注册
        """
        return self.handler.unregister(handler)

    def _clear_message_handlers(self):
        """
        {!--< internal-use >!--}
        清除所有已注册的消息处理器
        
        :return: 被清除的处理器数量
        """
        return self.handler._clear_handlers()

message = MessageHandler()