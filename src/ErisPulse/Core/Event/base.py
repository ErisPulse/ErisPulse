"""
ErisPulse 事件处理基础模块

提供事件处理的核心功能，包括事件注册和处理

{!--< tips >!--}
1. 所有事件处理都基于OneBot12标准事件格式
2. 通过适配器系统进行事件分发和接收
{!--< /tips >!--}
"""

import asyncio
import inspect
import time as _time
from collections.abc import Callable
from itertools import groupby
from typing import Any

from ...runtime import get_event_config
from ...runtime.context import current_owner, handler_waits
from .. import adapter, logger
from ..constants import (
    DEFAULT_HANDLER_PRIORITY,
    EVENT_TYPE_MESSAGE,
    HANDLER_SLOW_THRESHOLD_SECS,
    UNKNOWN_PLATFORM,
)
from ..i18n import i18n
from ..lifecycle import lifecycle
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
    _hname = getattr(
        handler, "__qualname__", getattr(handler, "__name__", str(handler))
    )
    _owner = handler_info.get("owner") or current_owner.get()

    # 切换到本 handler 的局部 wait 记录器。
    # 结束后把局部记录回填给外层 Task 级记录器（若有），便于统一判定 slow-log。
    _outer_waits = handler_waits.get()
    _local_waits: list[dict] = []
    _wait_token = handler_waits.set(_local_waits)

    _t = _time.monotonic()
    try:
        if inspect.iscoroutinefunction(handler):
            await handler(event)
        else:
            handler(event)
    except Exception as e:
        logger.error(i18n.t("core.event.handler_error", error=e))
        return
    finally:
        _elapsed = _time.monotonic() - _t
        handler_waits.reset(_wait_token)
        if isinstance(_outer_waits, list):
            _outer_waits.extend(_local_waits)

    _wait_total = sum(w.get("duration", 0.0) for w in _local_waits)
    _pure = max(0.0, _elapsed - _wait_total)

    # 归属信息（同时附加到日志，便于排查具体业务模块）
    _owner_tag = f" owner={_owner}" if _owner else " owner=<unknown>"

    if _local_waits:
        # 该 handler 调用过 wait_reply —— 在白名单内：
        # 真正的 CPU/IO 慢才需要 WARNING；纯等待用户回复一律降级到 DEBUG。
        _wait_keys = ",".join(w.get("wait_key", "") for w in _local_waits)
        if _pure > HANDLER_SLOW_THRESHOLD_SECS:
            logger.warning(
                i18n.t(
                    "core.event.slow_handler_wait",
                    handler=_hname, elapsed=f"{_elapsed:.4f}",
                    wait=f"{_wait_total:.4f}", pure=f"{_pure:.4f}",
                    waits=_wait_keys, owner=_owner_tag,
                )
            )
        else:
            logger.trace(
                i18n.t(
                    "core.event.trace_handler_wait",
                    handler=_hname, elapsed=f"{_elapsed:.4f}",
                    wait=f"{_wait_total:.4f}", pure=f"{_pure:.4f}",
                    owner=_owner_tag,
                )
            )
    else:
        if _elapsed > HANDLER_SLOW_THRESHOLD_SECS:
            logger.warning(
                i18n.t("core.event.slow_handler", handler=_hname, elapsed=f"{_elapsed:.4f}", owner=_owner_tag)
            )


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
        self,
        handler: Callable,
        priority: int = DEFAULT_HANDLER_PRIORITY,
        condition: Callable = None,
    ):
        """
        注册事件处理器

        :param handler: 事件处理器函数
        :param priority: 处理器优先级，数值越大优先级越高
        :param condition: 处理器条件函数，返回True时才会执行处理器
        """
        handler_info = {
            "func": handler,
            "priority": priority,
            "condition": condition,
            "module": self.module_name,
            "owner": current_owner.get(),
        }
        self.handlers.append(handler_info)
        self._handler_map[id(handler)] = handler_info
        self.handlers.sort(key=lambda x: x["priority"], reverse=True)

        if self.event_type and not self._linked_to_adapter_bus:
            adapter.on(self.event_type)(self._process_event)
            self._linked_to_adapter_bus = True
        logger.trace(
            i18n.t(
                "core.event.handler_registered",
                event_type=self.event_type,
                module=self.module_name,
                owner=current_owner.get() or "N/A",
            )
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

    def unregister_by_owner(self, owner: str) -> int:
        """
        {!--< internal-use >!--}
        按归属者精确移除事件处理器

        :param owner: 归属者（模块名）
        :return: 移除的处理器数量
        """
        before = len(self.handlers)
        self.handlers = [h for h in self.handlers if h.get("owner") != owner]
        self._handler_map = {id(h["func"]): h for h in self.handlers}
        removed = before - len(self.handlers)
        if removed > 0:
            logger.trace(
                i18n.t(
                    "core.event.handlers_cleaned",
                    count=removed,
                    event_type=self.event_type,
                    owner=owner,
                )
            )
        return removed

    def __call__(
        self, priority: int = DEFAULT_HANDLER_PRIORITY, condition: Callable = None
    ):
        """
        装饰器方式注册事件处理器

        :param priority: 处理器优先级，数值越大优先级越高
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

        # 事件链路追踪
        _trace_chain: list[dict] = []
        _trace_start = _time.monotonic()

        # 钩子: 事件预处理
        await lifecycle.emit(
            "event.pre_process",
            {
                "event_type": self.event_type,
                "platform": event.get("platform", UNKNOWN_PLATFORM),
                "detail_type": event.get("detail_type", "unknown"),
            },
        )

        # 忽略自己发送的消息
        if self.event_type == EVENT_TYPE_MESSAGE:
            if event.get("self", {}).get("user_id") == event.get("user_id"):
                event_config = get_event_config()
                ignore_self = event_config.get("message", {}).get("ignore_self", True)
                if ignore_self:
                    return

        for _priority, group_iter in groupby(
            self.handlers, key=lambda h: h["priority"]
        ):
            group = list(group_iter)

            # 过滤出满足条件的处理器
            active = [
                h for h in group if not h.get("condition") or h["condition"](event)
            ]
            if not active:
                continue

            # 单个处理器：直接传原事件（零拷贝）
            if len(active) == 1:
                _h0 = active[0]
                _h_name = getattr(_h0["func"], "__qualname__", getattr(_h0["func"], "__name__", str(_h0["func"])))
                _t0 = _time.monotonic()
                await _invoke_handler(_h0, event)
                _elapsed_0 = _time.monotonic() - _t0
                _trace_chain.append({
                    "handler": _h_name,
                    "priority": _priority,
                    "elapsed_ms": round(_elapsed_0 * 1000, 2),
                    "processed": event.is_processed(),
                })
                if event.is_processed():
                    break
                continue

            # 多个同优先级处理器：各自独立副本并行执行
            copies = [Event(dict(event)) for _ in active]
            _multi_t = _time.monotonic()
            await asyncio.gather(
                *(_invoke_handler(h, c) for h, c in zip(active, copies))
            )
            _multi_elapsed = _time.monotonic() - _multi_t

            # 记录多处理器链路（并行执行，统一计时）
            for h in active:
                _h_name = getattr(h["func"], "__qualname__", getattr(h["func"], "__name__", str(h["func"])))
                _trace_chain.append({
                    "handler": _h_name,
                    "priority": _priority,
                    "elapsed_ms": round(_multi_elapsed * 1000, 2),
                    "processed": False,
                })

            # 合并修改（后者覆盖前者）
            for copy in copies:
                for key, value in copy.items():
                    if value != event.get(key, _sentinel):
                        event[key] = value
                if copy.is_processed():
                    event.mark_processed()

            if event.is_processed():
                break

        # 输出事件链路追踪日志
        if _trace_chain:
            _total = _time.monotonic() - _trace_start
            _chain_str = " → ".join(
                f"{c['handler']}({c['elapsed_ms']}ms)"
                + ("[short-circuit]" if c["processed"] else "")
                for c in _trace_chain
            )
            logger.trace(
                i18n.t(
                    "core.event.trace_chain",
                    event_type=self.event_type,
                    platform=event.get("platform", "?"),
                    detail_type=event.get("detail_type", "?"),
                    chain=_chain_str,
                    total=f"{_total * 1000:.2f}",
                )
            )

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
