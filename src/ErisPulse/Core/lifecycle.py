"""
ErisPulse 生命周期管理模块

提供统一的钩子/事件管理和触发机制，支持点式结构事件监听

{!--< tips >!--}
1. 使用 @lifecycle.on("event.name") 注册事件处理器
2. 使用 await lifecycle.emit("event.name", data) 触发事件
3. 使用 lifecycle.start_timer() / stop_timer() 进行计时
4. 旧版 submit_event() API 保持兼容
{!--< /tips >!--}
"""

import asyncio
import inspect
import time
from typing import Any
from collections.abc import Callable
from .logger import logger


class LifecycleManager:
    """
    生命周期管理器

    统一的钩子/事件系统，支持：
    - 点式结构事件监听（如 module.init 可被 module 监听到）
    - 通配符监听（* 匹配所有事件）
    - 优先级排序
    - 同步/异步处理器
    - 计时器

    {!--< tips >!--}
    两种注册方式等价：
    >>> @lifecycle.on("module.load")
    ... async def on_load(data):
    ...     print(data)
    
    >>> lifecycle.register("module.load", on_load)
    
    两种触发方式等价：
    >>> await lifecycle.emit("module.load", {"module_name": "Test"})
    >>> await lifecycle.submit_event("module.load", data={"module_name": "Test"})
    {!--< /tips >!--}
    """

    # 预定义的标准事件列表
    STANDARD_EVENTS = {
        "core": ["init.start", "init.complete"],
        "module": ["load", "init", "unload"],
        "adapter": ["load", "start", "status.change", "stop", "stopped"],
        "server": ["start", "stop"],
    }

    def __init__(self):
        self._hooks: dict[str, list[tuple[int, Callable]]] = {}
        self._timers: dict[str, float] = {}

    # ==================== 注册 API ====================

    def on(self, event: str, *, priority: int = 0) -> Callable:
        """
        注册事件处理器（装饰器模式）

        :param event: str 事件名称，支持点式结构和通配符
        :param priority: int 优先级，数值越小越先执行 (默认: 0)
        :return: Callable 装饰器

        :raises ValueError: 当事件名无效时抛出

        :example:
        >>> @lifecycle.on("module.load")
        ... async def on_module_load(data):
        ...     print(f"模块加载: {data}")
        >>>
        >>> @lifecycle.on("adapter.*")
        ... def on_adapter_event(data):
        ...     pass
        """
        if not isinstance(event, str) or not event:
            raise ValueError("事件名称必须是非空字符串")

        def decorator(func: Callable) -> Callable:
            self._hooks.setdefault(event, []).append((priority, func))
            self._hooks[event].sort(key=lambda x: x[0])
            return func

        return decorator

    def register(self, event: str, handler: Callable, *, priority: int = 0):
        """
        注册事件处理器（函数调用模式）

        :param event: str 事件名称
        :param handler: Callable 处理函数
        :param priority: int 优先级 (默认: 0)

        :example:
        >>> lifecycle.register("config.set", my_handler, priority=10)
        """
        if not isinstance(event, str) or not event:
            raise ValueError("事件名称必须是非空字符串")
        self._hooks.setdefault(event, []).append((priority, handler))
        self._hooks[event].sort(key=lambda x: x[0])

    def off(self, event: str, handler: Callable = None):
        """
        取消注册事件处理器

        :param event: str 事件名称
        :param handler: Callable 指定取消的处理器，为 None 时取消该事件所有处理器

        :example:
        >>> lifecycle.off("config.set", my_handler)  # 取消指定处理器
        >>> lifecycle.off("config.set")               # 取消所有处理器
        """
        if handler is None:
            self._hooks.pop(event, None)
        else:
            handlers = self._hooks.get(event, [])
            self._hooks[event] = [(p, h) for p, h in handlers if h != handler]

    # ==================== 触发 API ====================

    async def emit(self, event: str, data: Any = None) -> Any:
        """
        触发事件（异步，精简版）

        按优先级执行匹配的处理器。处理器返回非 None 值时，
        该值将作为新的 data 传递给后续处理器。

        :param event: str 事件名称
        :param data: Any 事件数据
        :return: Any 经过所有处理器处理后的数据

        :example:
        >>> result = await lifecycle.emit("config.set", {"key": "test", "value": 42})
        """
        logger.debug(f"触发生命周期事件: {event}")

        # 通配符处理器
        if "*" in self._hooks:
            data = await self._execute_handlers("*", event, data)

        # 完整事件名处理器
        if event in self._hooks:
            data = await self._execute_handlers(event, event, data)

        # 父级事件处理器（点式结构）
        parts = event.split(".")
        for i in range(len(parts) - 1, 0, -1):
            parent_event = ".".join(parts[:i])
            if parent_event in self._hooks:
                data = await self._execute_handlers(parent_event, event, data)

        return data

    def emit_sync(self, event: str, data: Any = None) -> Any:
        """
        触发事件（同步，精简版）

        同步执行所有处理器。异步处理器会在当前事件循环中以 create_task 调度。
        注意：同步模式下异步处理器的返回值无法回传。

        :param event: str 事件名称
        :param data: Any 事件数据
        :return: Any 处理后的数据

        :example:
        >>> result = lifecycle.emit_sync("config.set", {"key": "test"})
        """
        logger.debug(f"触发生命周期事件: {event}")

        if "*" in self._hooks:
            data = self._execute_handlers_sync("*", event, data)

        if event in self._hooks:
            data = self._execute_handlers_sync(event, event, data)

        parts = event.split(".")
        for i in range(len(parts) - 1, 0, -1):
            parent_event = ".".join(parts[:i])
            if parent_event in self._hooks:
                data = self._execute_handlers_sync(parent_event, event, data)

        return data

    # ==================== 兼容 API ====================

    async def submit_event(
        self,
        event_type: str,
        *,
        source: str = "ErisPulse",
        msg: str = "",
        data: dict | None = None,
        timestamp: float | None = None,
    ) -> None:
        """
        提交生命周期事件（兼容旧版 API）

        构建标准事件格式后通过 emit 触发，处理器接收标准事件字典。

        :param event_type: str 事件名称
        :param source: str 事件来源(默认"ErisPulse")
        :param msg: str 事件描述
        :param data: dict 事件相关数据
        :param timestamp: float 时间戳(默认当前时间)

        :example:
        >>> await lifecycle.submit_event("module.load", data={"module_name": "Test"})
        """
        if event_type is None:
            logger.error("事件类型不能为None")
            return

        if not isinstance(event_type, str) or not event_type:
            logger.error(f"事件类型必须是非空字符串，收到: {event_type}")
            return

        if timestamp is None:
            timestamp = time.time()
        if data is None:
            data = {}

        event_data = {
            "event": event_type,
            "timestamp": timestamp,
            "data": data,
            "source": source,
            "msg": msg,
        }

        await self.emit(event_type, event_data)

    # ==================== 计时器 ====================

    def start_timer(self, timer_id: str) -> None:
        """
        开始计时

        :param timer_id: str 计时器ID
        """
        self._timers[timer_id] = time.time()

    def get_duration(self, timer_id: str) -> float:
        """
        获取指定计时器的持续时间

        :param timer_id: str 计时器ID
        :return: float 持续时间(秒)
        """
        if timer_id in self._timers:
            return time.time() - self._timers[timer_id]
        return 0.0

    def stop_timer(self, timer_id: str) -> float:
        """
        停止计时并返回持续时间

        :param timer_id: str 计时器ID
        :return: float 持续时间(秒)
        """
        duration = self.get_duration(timer_id)
        if timer_id in self._timers:
            del self._timers[timer_id]
        return duration

    # ==================== 内部方法 ====================

    async def _execute_handlers(
        self, hook_name: str, event: str, data: Any
    ) -> Any:
        """
        执行匹配的事件处理器（异步）

        :param hook_name: str 注册的钩子名
        :param event: str 实际事件名
        :param data: Any 事件数据
        :return: Any 处理后的数据
        """
        for _, handler in self._hooks[hook_name]:
            try:
                if inspect.iscoroutinefunction(handler):
                    result = await handler(data)
                else:
                    result = handler(data)
                if result is not None:
                    data = result
            except Exception as e:
                logger.error(f"生命周期事件处理器执行错误 {event}: {e}")
        return data

    def _execute_handlers_sync(
        self, hook_name: str, event: str, data: Any
    ) -> Any:
        """
        执行匹配的事件处理器（同步）

        :param hook_name: str 注册的钩子名
        :param event: str 实际事件名
        :param data: Any 事件数据
        :return: Any 处理后的数据
        """
        for _, handler in self._hooks[hook_name]:
            try:
                if inspect.iscoroutinefunction(handler):
                    try:
                        loop = asyncio.get_running_loop()
                        loop.create_task(handler(data))
                    except RuntimeError:
                        pass
                else:
                    result = handler(data)
                    if result is not None:
                        data = result
            except Exception as e:
                logger.error(f"生命周期事件处理器执行错误 {event}: {e}")
        return data

    # ==================== 工具方法 ====================

    def clear(self):
        """
        清除所有已注册的处理器和计时器

        :example:
        >>> lifecycle.clear()
        """
        self._hooks.clear()
        self._timers.clear()

    def list_hooks(self) -> dict[str, int]:
        """
        列出所有已注册的钩子及其处理器数量

        :return: dict 钩子名称到处理器数量的映射

        :example:
        >>> info = lifecycle.list_hooks()
        >>> # {"module.load": 2, "adapter.start": 1}
        """
        return {name: len(handlers) for name, handlers in self._hooks.items()}


lifecycle: LifecycleManager = LifecycleManager()

__all__ = ["LifecycleManager", "lifecycle"]
