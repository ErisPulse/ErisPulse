"""
ErisPulse 生命周期管理模块

提供统一的生命周期事件管理和触发机制

事件标准格式:
{
    "event": "事件名称",  # 必填
    "timestamp": float,  # 必填，Unix时间戳
    "data": dict,        # 可选，事件相关数据
    "source": str,       # 必填，事件来源
    "msg": str           # 可选，事件描述
}
"""

import asyncio
import time
from typing import Callable, List, Dict, Any
from .logger import logger

class LifecycleManager:
    """
    生命周期管理器
    
    管理SDK的生命周期事件，提供事件注册和触发功能
    支持点式结构事件监听，例如 module.init 可以被 module 监听到
    """
    
    # 预定义的标准事件列表
    STANDARD_EVENTS = {
        "core": ["init.start", "init.complete"],
        "module": ["load", "init", "unload"],
        "adapter": ["load", "start", "status.change", "stop", "stopped"],
        "server": ["start", "stop"]
    }
    
    def __init__(self):
        self._handlers: Dict[str, List[Callable]] = {}
        self._timers: Dict[str, float] = {}  # 用于存储计时器
        
    def _validate_event(self, event_data: Dict[str, Any]) -> bool:
        """
        验证事件数据格式
        
        :param event_data: 事件数据字典
        :return: 是否有效
        """
        if not isinstance(event_data, dict):
            logger.error("事件数据必须是字典")
            
        required_fields = ["event", "timestamp", "source"]
        for field in required_fields:
            if field not in event_data:
                logger.error(f"事件缺少必填字段: {field}")
                
        if not isinstance(event_data["event"], str):
            logger.error("event字段必须是字符串")
            
        if not isinstance(event_data["timestamp"], (int, float)):
            logger.error("timestamp字段必须是数字")
            
        if "data" in event_data and not isinstance(event_data["data"], dict):
            logger.error("data字段必须是字典")
            
        return True
        
    def on(self, event: str) -> Callable:
        """
        注册生命周期事件处理器
        
        :param event: 事件名称，支持点式结构如 module.init
        :return: 装饰器函数
        
        :raises ValueError: 当事件名无效时抛出
        """
        if not isinstance(event, str) or not event:
            raise ValueError("事件名称必须是非空字符串")
        def decorator(func: Callable) -> Callable:
            if event not in self._handlers:
                self._handlers[event] = []
            self._handlers[event].append(func)
            return func
        return decorator
        
    def start_timer(self, timer_id: str) -> None:
        """
        开始计时
        
        :param timer_id: 计时器ID
        """
        self._timers[timer_id] = time.time()
        
    def get_duration(self, timer_id: str) -> float:
        """
        获取指定计时器的持续时间
        
        :param timer_id: 计时器ID
        :return: 持续时间(秒)
        """
        if timer_id in self._timers:
            return time.time() - self._timers[timer_id]
        return 0.0
        
    def stop_timer(self, timer_id: str) -> float:
        """
        停止计时并返回持续时间
        
        :param timer_id: 计时器ID
        :return: 持续时间(秒)
        """
        duration = self.get_duration(timer_id)
        if timer_id in self._timers:
            del self._timers[timer_id]
        return duration
        
    async def submit_event(self, event_type: str, *, source: str = "ErisPulse", msg: str = "", data: dict = {}, timestamp = time.time()) -> None:
        """
        提交生命周期事件
        
        :param event: 事件名称
        :param event_data: 事件数据字典
        """
        # 构建完整事件数据
        event_data = {
            "event": event_type,
            "timestamp": timestamp,
            "data": data,
            "source": source,
            "msg": msg
        }
            
        # 验证事件格式
        self._validate_event(event_data)
        
        # 触发通配符处理器（如果存在）
        if "*" in self._handlers:
            await self._execute_handlers("*", event_data)
            
        # 触发完整事件名的处理器
        if event_type in self._handlers:
            await self._execute_handlers(event_type, event_data)
            
        # 触发父级事件名的处理器（点式结构）
        parts = event_type.split('.')
        for i in range(len(parts) - 1, 0, -1):
            parent_event = '.'.join(parts[:i])
            if parent_event in self._handlers:
                await self._execute_handlers(parent_event, event_data)
                
    async def _execute_handlers(self, event: str, event_data: Dict[str, Any]) -> None:
        """
        执行事件处理器
        
        :param event: 事件名称
        :param event_data: 事件数据
        """
        logger.debug(f"触发生命周期事件: {event}")
        for handler in self._handlers[event]:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event_data)
                else:
                    handler(event_data)
            except Exception as e:
                logger.error(f"生命周期事件处理器执行错误 {event}: {e}")

lifecycle = LifecycleManager()