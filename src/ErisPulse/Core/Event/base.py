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


def _try_merge_values(key: str, values: list) -> Any:
    """
    {!--< internal-use >!--}
    合并多个值，默认使用 last 策略

    :param key: 键名
    :param values: 值列表
    :return: 合并后的值
    """
    if len(values) == 1:
        return values[0]

    if key == "message":
        merged = []
        for v in values:
            if isinstance(v, list):
                merged.extend(v)
        return merged

    if key in ("alt_message", "text"):
        return " ".join(str(v) for v in values)

    return values[-1]


class _EventCopyTracker:
    """
    {!--< internal-use >!--}
    事件副本修改追踪器

    包装 Event 对象，追踪哪些 key 被修改。
    初始只持有原始事件引用，首次写入时创建副本。
    """

    __slots__ = ("_event", "_original_event", "_modified_keys")

    def __init__(self, original: Event):
        object.__setattr__(self, "_event", None)
        object.__setattr__(self, "_original_event", original)
        object.__setattr__(self, "_modified_keys", set())

    def _ensure_copy(self) -> Event:
        event = object.__getattribute__(self, "_event")
        if event is None:
            original = object.__getattribute__(self, "_original_event")
            object.__setattr__(self, "_event", Event(dict(original)))
            event = object.__getattribute__(self, "_event")
        return event

    def _get_from_copy_or_original(self, key: str) -> Any:
        event = object.__getattribute__(self, "_event")
        if event is not None:
            return event.get(key, _sentinel)
        return object.__getattribute__(self, "_original_event").get(key, _sentinel)

    def __getitem__(self, key: str) -> Any:
        event = object.__getattribute__(self, "_event")
        if event is not None:
            return event[key]
        return object.__getattribute__(self, "_original_event")[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self._modified_keys.add(key)
        self._ensure_copy()[key] = value

    def __contains__(self, key: str) -> bool:
        return key in object.__getattribute__(self, "_original_event")

    def get(self, key: str, default: Any = None) -> Any:
        event = object.__getattribute__(self, "_event")
        if event is not None:
            return event.get(key, default)
        return object.__getattribute__(self, "_original_event").get(key, default)

    def pop(self, key: str, *args) -> Any:
        self._modified_keys.add(key)
        return self._ensure_copy().pop(key, *args)

    def to_event(self) -> Event:
        event = object.__getattribute__(self, "_event")
        if event is None:
            return object.__getattribute__(self, "_original_event")
        return event

    def was_modified(self) -> bool:
        return bool(object.__getattribute__(self, "_modified_keys"))

    def modified_keys(self) -> set:
        return object.__getattribute__(self, "_modified_keys")

    def is_processed(self) -> bool:
        event = object.__getattribute__(self, "_event")
        if event is not None:
            return event.is_processed()
        return object.__getattribute__(self, "_original_event").is_processed()

    def mark_processed(self) -> None:
        self._modified_keys.add("_processed")
        self._ensure_copy().mark_processed()


async def _invoke_handler(handler_info: dict, tracker: _EventCopyTracker) -> _EventCopyTracker:
    """
    {!--< internal-use >!--}
    执行单个处理器，使用 Copy-On-Write 优化

    :param handler_info: 处理器信息字典
    :param tracker: 事件修改追踪器
    :return: 追踪器（可能被修改）
    """
    handler = handler_info["func"]
    try:
        if inspect.iscoroutinefunction(handler):
            await handler(tracker)
        else:
            handler(tracker)
    except Exception as e:
        logger.error(f"事件处理器执行错误: {e}")
    return tracker


def _merge_trackers(
    original: Event,
    snapshot: dict,
    trackers: list[_EventCopyTracker],
) -> None:
    """
    {!--< internal-use >!--}
    合并多个追踪器的修改

    :param original: 原始事件
    :param snapshot: 执行前快照
    :param trackers: 修改追踪器列表
    """
    modified_keys: dict[str, list[tuple[int, Any]]] = {}

    for idx, tracker in enumerate(trackers):
        if not tracker.was_modified():
            continue
        for key in tracker.modified_keys():
            new_val = tracker.get(key, _sentinel)
            old_val = snapshot.get(key, _sentinel)
            if new_val != old_val:
                modified_keys.setdefault(key, []).append((idx, new_val))

        for key in snapshot:
            if key not in tracker and key in modified_keys:
                if (idx, _sentinel) not in modified_keys[key]:
                    modified_keys[key].append((idx, _sentinel))

    for key, modifications in modified_keys.items():
        if len(modifications) > 1:
            src_indices = ", ".join(str(i) for i, _ in modifications)
            logger.warning(
                f"[Event] 同优先级处理器冲突: key='{key}', "
                f"涉及处理器索引 [{src_indices}], 使用最后修改值"
            )

        deleted = any(v is _sentinel for _, v in modifications)
        values = [v for _, v in modifications if v is not _sentinel]

        if deleted or not values:
            original.pop(key, None)
        else:
            original[key] = _try_merge_values(key, values)


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
        每个优先级组执行完毕后合并各处理器的变更，检测冲突。

        :param event: 事件数据
        """
        if not isinstance(event, Event):
            event = Event(event)

        if self.event_type == "message":
            if event.get("self", {}).get("user_id") == event.get("user_id"):
                event_config = get_event_config()
                ignore_self = event_config.get("message", {}).get("ignore_self", True)
                if ignore_self:
                    return

        for _priority, group_iter in groupby(self.handlers, key=lambda h: h["priority"]):
            group = list(group_iter)

            active = [
                h for h in group
                if not h.get("condition") or h["condition"](event)
            ]
            if not active:
                continue

            if len(active) == 1:
                tracker = _EventCopyTracker(event)
                await _invoke_handler(active[0], tracker)
                if tracker.was_modified():
                    result_event = tracker.to_event()
                    for key in result_event:
                        if result_event[key] != event.get(key, _sentinel):
                            event[key] = result_event[key]
                if event.is_processed():
                    break
                continue

            snapshot = dict(event)
            trackers = [_EventCopyTracker(event) for _ in active]

            results = await asyncio.gather(
                *(_invoke_handler(h, t) for h, t in zip(active, trackers))
            )

            _merge_trackers(event, snapshot, list(results))

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
