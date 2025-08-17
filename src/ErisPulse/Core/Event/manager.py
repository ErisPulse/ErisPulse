"""
ErisPulse 事件管理器

提供全局事件管理功能，包括事件处理器创建、模块事件管理等
"""

from .. import logger
from .base import BaseEventHandler
from .exceptions import EventNotFoundException
from typing import Dict, List, Optional, Callable, Any
import asyncio

class EventManager:
    """
    事件管理器
    
    管理所有事件处理器，提供全局事件处理功能
    """
    
    def __init__(self):
        """
        初始化事件管理器
        """
        self.event_handlers: Dict[str, BaseEventHandler] = {}
        self.module_events: Dict[str, List[str]] = {}
        self.global_middlewares: List[Callable] = []
    
    def create_event_handler(self, event_type: str, module_name: str = None) -> BaseEventHandler:
        """
        创建事件处理器
        
        :param event_type: 事件类型
        :param module_name: 模块名称
        :return: 事件处理器实例
        """
        if event_type not in self.event_handlers:
            handler = BaseEventHandler(event_type, module_name)
            self.event_handlers[event_type] = handler
        return self.event_handlers[event_type]
    
    def get_event_handler(self, event_type: str) -> Optional[BaseEventHandler]:
        """
        获取事件处理器
        
        :param event_type: 事件类型
        :return: 事件处理器实例，如果不存在则返回None
        """
        return self.event_handlers.get(event_type)
    
    def register_module_event(self, module_name: str, event_type: str):
        """
        注册模块事件
        
        :param module_name: 模块名称
        :param event_type: 事件类型
        """
        if module_name not in self.module_events:
            self.module_events[module_name] = []
        if event_type not in self.module_events[module_name]:
            self.module_events[module_name].append(event_type)
    
    def middleware(self, func: Callable):
        """
        添加全局中间件
        
        :param func: 中间件函数
        :return: 中间件函数
        """
        self.global_middlewares.append(func)
        return func
    
    async def emit(self, event_type: str, event_data: Dict[str, Any]):
        """
        触发事件
        
        :param event_type: 事件类型
        :param event_data: 事件数据
        """
        # 执行全局中间件
        processed_data = event_data
        for middleware in self.global_middlewares:
            try:
                if asyncio.iscoroutinefunction(middleware):
                    processed_data = await middleware(processed_data)
                else:
                    processed_data = middleware(processed_data)
            except Exception as e:
                logger.error(f"全局中间件执行错误: {e}")
        
        # 触发事件处理器
        if event_type in self.event_handlers:
            handler = self.event_handlers[event_type]
            await handler._process_event(processed_data)
        
        # 触发通配符处理器
        if "*" in self.event_handlers:
            handler = self.event_handlers["*"]
            await handler._process_event(processed_data)
    
    def get_module_events(self, module_name: str) -> List[str]:
        """
        获取模块注册的事件
        
        :param module_name: 模块名称
        :return: 事件类型列表
        """
        return self.module_events.get(module_name, [])
    
    def cleanup_module_events(self, module_name: str):
        """
        清理模块事件
        
        :param module_name: 模块名称
        """
        if module_name in self.module_events:
            event_types = self.module_events[module_name]
            for event_type in event_types:
                if event_type in self.event_handlers:
                    # 移除该模块注册的处理器
                    handler = self.event_handlers[event_type]
                    handler.handlers = [
                        h for h in handler.handlers 
                        if h.get("module") != module_name
                    ]
            del self.module_events[module_name]

event_manager = EventManager()