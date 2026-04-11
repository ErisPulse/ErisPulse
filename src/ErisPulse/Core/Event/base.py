"""
ErisPulse 事件处理基础模块

提供事件处理的核心功能，包括事件注册和处理

{!--< tips >!--}
1. 所有事件处理都基于OneBot12标准事件格式
2. 通过适配器系统进行事件分发和接收
{!--< /tips >!--}
"""

from .. import adapter, logger
from ...runtime import get_event_config
from typing import Any
from collections.abc import Callable
import asyncio
import inspect
from itertools import groupby
from .wrapper import Event


_sentinel = object()


async def _invoke_handler(handler_info: dict, event: Event) -> None:
    """
    {!--< internal-use >!--}
    执行单个事件处理器

    :param handler_info: 处理器信息字典
    :param event: 事件对象
    """
    handler = handler_info["func"]
    try:
        if inspect.iscoroutinefunction(handler):
            await handler(event)
        else:
            handler(event)
    except Exception as e:
        logger.error(f"事件处理器执行错误: {e}")

class BaseEventHandler:
    """
    基础事件处理器

    提供事件处理的基本功能，包括处理器注册和注销

    内部维护与适配器事件总线的连接状态（_linked_to_adapter_bus），
    确保 _process_event 在适配器总线被清空（如 shutdown/restart）后能重新挂载。
    """

    def __init__(self, event_type: str, module_name: str = None):
        """
        初始化事件处理器

        :param event_type: 事件类型
        :param module_name: 模块名称
        """
        self.event_type = event_type
        self.module_name = module_name
        self.handlers: list[dict] = []
        self._handler_map = {}  # 用于快速查找处理器

        # 是否已将 self._process_event 挂载到适配器事件总线（adapter._onebot_handlers）。
        #
        # 当 adapter.shutdown() 或 adapter.clear() 清空事件总线后，
        # 需要通过 _clear_handlers() 将此标记重置为 False，
        # 以便下次 register() 时重新调用 adapter.on() 挂载 _process_event。
        self._linked_to_adapter_bus: bool = False

    def register(
        self, handler: Callable, priority: int = 0, condition: Callable = None
    ):
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
            "module": self.module_name,
        }
        self.handlers.append(handler_info)
        self._handler_map[id(handler)] = handler_info
        # 按优先级排序
        self.handlers.sort(key=lambda x: x["priority"])

        # 注册到适配器
        if self.event_type and not self._linked_to_adapter_bus:
            adapter.on(self.event_type)(self._process_event)
            self._linked_to_adapter_bus = True
        logger.debug(
            f"[Event] 已注册事件处理器: {self.event_type}, Called by: {self.module_name}"
        )

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

    async def _process_event(self, event: dict[str, Any]):
        """
        处理事件

        {!--< internal-use >!--}
        同优先级处理器并行执行，不同优先级按顺序串行执行。
        同优先级处理器的修改冲突采用后者覆盖前者的策略。

        :param event: 事件数据
        """
        if not isinstance(event, Event):
            event = Event(event)

        # 忽略自己发送的消息
        if self.event_type == "message":
            if event.get("self", {}).get("user_id") == event.get("user_id"):
                event_config = get_event_config()
                ignore_self = event_config.get("message", {}).get("ignore_self", True)
                if ignore_self:
                    return

        for _priority, group_iter in groupby(self.handlers, key=lambda h: h["priority"]):
            group = list(group_iter)

            # 过滤出满足条件的处理器
            active = [
                h for h in group
                if not h.get("condition") or h["condition"](event)
            ]
            if not active:
                continue

            # 单个处理器：直接传原事件（零拷贝）
            if len(active) == 1:
                await _invoke_handler(active[0], event)
                if event.is_processed():
                    break
                continue

            # 多个同优先级处理器：各自独立副本并行执行
            copies = [Event(dict(event)) for _ in active]
            await asyncio.gather(
                *(_invoke_handler(h, c) for h, c in zip(active, copies))
            )

            # 合并修改（后者覆盖前者）
            for copy in copies:
                for key, value in copy.items():
                    if value != event.get(key, _sentinel):
                        event[key] = value
                if copy.is_processed():
                    event.mark_processed()

            if event.is_processed():
                break

    def _clear_handlers(self):
        """
        {!--< internal-use >!--}
        清除所有已注册的事件处理器，并断开与适配器事件总线的连接

        断开连接后，下次调用 register() 时会自动重新挂载 _process_event 到适配器总线，
        以适配 shutdown/restart 等场景下适配器总线被清空的情况。

        :return: 被清除的处理器数量
        """
        count = len(self.handlers)
        self.handlers.clear()
        self._handler_map.clear()
        self._linked_to_adapter_bus = False
        return count
