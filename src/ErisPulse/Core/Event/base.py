"""
ErisPulse 事件处理基础模块

提供事件处理的核心功能，包括事件注册和处理

{!--< tips >!--}
1. 所有事件处理都基于OneBot12标准事件格式
2. 通过适配器系统进行事件分发和接收
{!--< /tips >!--}
"""

from .. import adapter, logger
from typing import Callable, Any, Dict, List
import asyncio

class BaseEventHandler:
    """
    基础事件处理器
    
    提供事件处理的基本功能，包括处理器注册和注销
    """
    
    def __init__(self, event_type: str, module_name: str = None):
        """
        初始化事件处理器
        
        :param event_type: 事件类型
        :param module_name: 模块名称
        """
        self.event_type = event_type
        self.module_name = module_name
        self.handlers: List[Dict] = []
        self._handler_map = {}                      # 用于快速查找处理器
        self._adapter_handler_registered = False    # 是否已注册到适配器
    
    def register(self, handler: Callable, priority: int = 0, condition: Callable = None):
        """
        注册事件处理器
        
        :param handler: 事件处理器函数
        :param priority: 处理器优先级，数值越小优先级越高
        :param condition: 处理器条件函数，返回True时才会执行处理器
        """
        handler_info = {
            "func": handler,
            "priority": priority,
            "condition": condition,
            "module": self.module_name
        }
        self.handlers.append(handler_info)
        self._handler_map[id(handler)] = handler_info
        # 按优先级排序
        self.handlers.sort(key=lambda x: x["priority"])
        
        # 注册到适配器
        if self.event_type and not self._adapter_handler_registered:
            adapter.on(self.event_type)(self._process_event)
            self._adapter_handler_registered = True
        logger.debug(f"[Event] 已注册事件处理器: {self.event_type}, Called by: {self.module_name}")

    def unregister(self, handler: Callable) -> bool:
        """
        注销事件处理器
        
        :param handler: 要注销的事件处理器
        :return: 是否成功注销
        """
        handler_id = id(handler)
        if handler_id in self._handler_map:
            self.handlers = [h for h in self.handlers if h["func"] != handler]
            del self._handler_map[handler_id]
            return True
        return False
    
    def __call__(self, priority: int = 0, condition: Callable = None):
        """
        装饰器方式注册事件处理器
        
        :param priority: 处理器优先级
        :param condition: 处理器条件函数
        :return: 装饰器函数
        """
        def decorator(func: Callable):
            self.register(func, priority, condition)
            return func
        return decorator
    
    async def _process_event(self, event: Dict[str, Any]):
        """
        处理事件
        
        {!--< internal-use >!--}
        内部使用的方法，用于处理事件
        
        :param event: 事件数据
        """
        # 执行处理器
        for handler_info in self.handlers:
            condition = handler_info.get("condition")
            # 检查条件
            if condition and not condition(event):
                continue
                
            handler = handler_info["func"]
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    handler(event)
            except Exception as e:
                logger.error(f"事件处理器执行错误: {e}")

    def _clear_handlers(self):
        """
        {!--< internal-use >!--}
        清除所有已注册的事件处理器
        
        :return: 被清除的处理器数量
        """
        count = len(self.handlers)
        self.handlers.clear()
        self._handler_map.clear()
        return count
