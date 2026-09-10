"""
ErisPulse 生命周期管理模块

提供统一的钩子/事件管理和触发机制，支持点式结构事件监听与定向传播

{!--< tips >!--}
1. 使用 @lifecycle.on("event.name") 注册事件处理器
2. 使用 await lifecycle.emit("event.name", data) 触发事件
3. 使用 lifecycle.emit("event.name", data, to="Owner") 定向投递给指定 owner 注册的钩子
4. 使用 lifecycle.start_timer() / stop_timer() 进行计时
5. 旧版 submit_event() API 保持兼容
{!--< /tips >!--}
"""

import asyncio
import inspect
import time
from collections.abc import Callable
from typing import Any

from ..runtime.context import current_owner
from .constants import DEFAULT_EVENT_SOURCE, HANDLER_SLOW_THRESHOLD_SECS
from .i18n import i18n


class _NullLogger:
    """静默日志器，在 logger 模块尚未初始化时作为替代"""

    def trace(self, *args, **kwargs):
        pass

    def debug(self, *args, **kwargs):
        pass

    def info(self, *args, **kwargs):
        pass

    def warning(self, *args, **kwargs):
        pass

    def error(self, *args, **kwargs):
        pass

    def critical(self, *args, **kwargs):
        pass


def _get_logger():
    """延迟导入 logger，避免循环依赖（lifecycle → logger → config → lifecycle）"""
    try:
        from .logger import logger

        return logger
    except (ImportError, AttributeError):
        return _NullLogger()


class LifecycleManager:
    """
    生命周期管理器

    统一的钩子/事件系统，支持：
    - 点式结构事件监听（如 module.init 可被 module 监听到）
    - 通配符监听（* 匹配所有事件）
    - 定向传播（emit(..., to="Owner") 仅分发给该 owner 注册的处理器）
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
        "core": ["init.start", "init.stage", "init.complete", "uninit.complete"],
        "module": ["load", "init", "unload", "register", "reload"],
        "adapter": [
            "load",
            "start",
            "status.change",
            "stop",
            "stopped",
            "event.receive",
            "event.dispatched",
            "bot.online",
            "bot.offline",
        ],
        "server": [
            "start",
            "stop",
            "request",
            "response",
            "websocket.connect",
            "websocket.disconnect",
        ],
        "event": ["pre_process"],
        "message": ["sending", "sent"],
        "command": ["matched", "executed"],
        "config": ["set", "updated"],
        "storage": ["ready", "unreachable", "recovered"],
        "client": ["request.success", "request.failed", "ws.connect"],
        "i18n": ["language.changed"],
    }

    def __init__(self):
        # _hooks 存储 (priority, handler, owner) 三元组
        self._hooks: dict[str, list[tuple[int, Callable, str | None]]] = {}
        self._timers: dict[str, float] = {}

    # ==================== 注册 API ====================

    def on(self, event: str, *, priority: int = 0) -> Callable:
        """
        注册事件处理器（装饰器模式）

        :param event: str 事件名称，支持点式结构和通配符
        :param priority: int 优先级，数值越大越先执行 (默认: 0)
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
            raise ValueError(i18n.t("core.lifecycle.event_name_required"))

        def decorator(func: Callable) -> Callable:
            owner = current_owner.get()
            self._hooks.setdefault(event, []).append((priority, func, owner))
            self._hooks[event].sort(key=lambda x: x[0], reverse=True)
            return func

        return decorator

    def register(self, event: str, handler: Callable, *, priority: int = 0):
        """
        注册事件处理器（函数调用模式）

        :param event: str 事件名称
        :param handler: Callable 处理函数
        :param priority: int 优先级，数值越大越先执行 (默认: 0)

        :example:
        >>> lifecycle.register("config.set", my_handler, priority=10)
        """
        if not isinstance(event, str) or not event:
            raise ValueError(i18n.t("core.lifecycle.event_name_required"))
        owner = current_owner.get()
        self._hooks.setdefault(event, []).append((priority, handler, owner))
        self._hooks[event].sort(key=lambda x: x[0], reverse=True)

    def once(self, event: str, *, priority: int = 0) -> Callable:
        """
        注册一次性事件处理器（触发一次后自动注销）

        :param event: str 事件名称
        :param priority: int 优先级 (默认: 0)
        :return: Callable 装饰器

        :example:
        >>> @lifecycle.once("core.init.complete")
        ... async def on_first_ready(data):
        ...     print("首次就绪")
        """
        if not isinstance(event, str) or not event:
            raise ValueError(i18n.t("core.lifecycle.event_name_required"))

        def decorator(func: Callable) -> Callable:
            if inspect.iscoroutinefunction(func):
                async def wrapper(data):
                    try:
                        return await func(data)
                    finally:
                        self.unregister(event, wrapper)
            else:
                def wrapper(data):
                    try:
                        return func(data)
                    finally:
                        self.unregister(event, wrapper)

            self.register(event, wrapper, priority=priority)
            return func

        return decorator

    def has_handlers(self, event: str) -> bool:
        """
        检查指定事件是否已有注册的处理器（含通配符 ``*`` 与父级事件）

        可用于热路径短路：发射事件前先判断有无监听者，避免无谓的字典遍历与任务调度。

        :param event: str 事件名称
        :return: bool 存在任意匹配处理器时返回 True

        :example:
        >>> if lifecycle.has_handlers("message.sending"):
        ...     await lifecycle.emit("message.sending", data)
        """
        if not isinstance(event, str) or not event:
            return False
        if self._hooks.get("*"):
            return True
        if self._hooks.get(event):
            return True
        parts = event.split(".")
        for i in range(len(parts) - 1, 0, -1):
            parent = ".".join(parts[:i])
            if self._hooks.get(parent):
                return True
        return False

    def unregister(self, event: str, handler: Callable | None = None):
        """
        取消注册事件处理器

        :param event: str 事件名称
        :param handler: Callable 指定取消的处理器，为 None 时取消该事件所有处理器

        :example:
        >>> lifecycle.unregister("config.set", my_handler)  # 取消指定处理器
        >>> lifecycle.unregister("config.set")               # 取消所有处理器
        """
        if handler is None:
            self._hooks.pop(event, None)
        else:
            handlers = self._hooks.get(event, [])
            self._hooks[event] = [(p, h, o) for p, h, o in handlers if h != handler]

    def unregister_by_owner(self, owner: str) -> int:
        """
        取消指定 owner 注册的所有事件处理器

        用于模块/适配器卸载时自动清理其注册的钩子，避免闭包引用导致内存泄漏。

        :param owner: 模块或适配器名称
        :return: int 被移除的处理器数量

        :example:
        >>> lifecycle.unregister_by_owner("MyModule")
        """
        removed = 0
        for event in list(self._hooks.keys()):
            original_len = len(self._hooks[event])
            self._hooks[event] = [
                (p, h, o) for p, h, o in self._hooks[event] if o != owner
            ]
            removed += original_len - len(self._hooks[event])
            if not self._hooks[event]:
                del self._hooks[event]
        return removed

    def get_owner_counts(self) -> dict[str, int]:
        """
        统计各 owner 注册的生命周期钩子数量（便于拓扑树展示）

        :return: {owner: 钩子数量} 字典

        :example:
        >>> lifecycle.get_owner_counts()
        {"MyModule": 3, "onebot11": 2}
        """
        counts: dict[str, int] = {}
        for handlers in self._hooks.values():
            for (_priority, _handler, owner) in handlers:
                if owner:
                    counts[owner] = counts.get(owner, 0) + 1
        return counts

    # ==================== 触发 API ====================

    async def emit(self, event: str, data: Any = None, *, to: str | None = None) -> Any:
        """
        触发事件（异步）

        匹配的处理器**并行执行**（各自包装为协程经 ``gather`` 并发，互不阻塞，
        本调用等待全部完成）：慢处理器不拖累其余处理器与触发方，但 emit 返回时
        所有处理器已执行完毕（顺序敏感的消费者可安全在 emit 之后读状态）。
        处理器返回非 None 值时按注册（优先级）顺序回放链式替换 data——
        所有处理器收到的是同一份输入数据。

        指定 ``to`` 时进入定向传播：事件只分发给以该拥有者（owner）身份注册的
        处理器（模块在 on_load 内注册 / `owner_scope` 上下文注册的钩子），
        其它模块与通配符 `*` 处理器不感知；目标 owner 无已注册钩子时静默丢弃。

        :param event: str 事件名称
        :param data: Any 事件数据（dict 时自动附加 `_trace_id`）
        :param to: str 定向投递目标拥有者（模块名 / 适配器平台名），None 广播
        :return: Any 经过所有处理器处理后的数据
        :raises ValueError: ``to`` 为空字符串时

        :example:
        >>> result = await lifecycle.emit("config.set", {"key": "test", "value": 42})
        >>> # 定向投递给 Chat 模块注册的钩子
        >>> await lifecycle.emit("maintenance", {"action": "reload"}, to="Chat")
        """
        # 事件数据为 dict 时自动携带当前事件的链路追踪 ID（不覆盖已有值）
        if isinstance(data, dict) and "_trace_id" not in data:
            from ..runtime.context import current_trace_id

            _tid = current_trace_id.get()
            if _tid:
                data["_trace_id"] = _tid

        if to is not None:
            if not to:
                raise ValueError(i18n.t("core.lifecycle.to_required"))
            parts = event.split(".")
            # 定向分发：精确事件名 + 点式父级前缀（均按 owner 过滤，通配符不参与）
            keys = [event] + [".".join(parts[:i]) for i in range(len(parts) - 1, 0, -1)]
            for key in keys:
                handlers = self._hooks.get(key)
                if handlers and any(o == to for (_p, _h, o) in handlers):
                    data = await self._execute_handlers(key, event, data, owner_filter=to)
            return data

        # 统计匹配的处理器总数
        parts = event.split(".")
        total_count = len(self._hooks.get("*", [])) + len(self._hooks.get(event, []))
        for i in range(len(parts) - 1, 0, -1):
            total_count += len(self._hooks.get(".".join(parts[:i]), []))
        _get_logger().trace(i18n.t("core.lifecycle.emit_enter", event=event, count=total_count))

        # 通配符处理器
        if "*" in self._hooks:
            _get_logger().trace(i18n.t("core.lifecycle.emit_wildcard", event=event, count=len(self._hooks["*"])))
            data = await self._execute_handlers("*", event, data)

        # 完整事件名处理器
        if event in self._hooks:
            _get_logger().trace(i18n.t("core.lifecycle.emit_exact", event=event, count=len(self._hooks[event])))
            data = await self._execute_handlers(event, event, data)

        # 父级事件处理器（点式结构）
        for i in range(len(parts) - 1, 0, -1):
            parent_event = ".".join(parts[:i])
            if parent_event in self._hooks:
                _get_logger().trace(
                    i18n.t("core.lifecycle.emit_parent", parent=parent_event, event=event)
                )
                data = await self._execute_handlers(parent_event, event, data)

        return data

    def emit_sync(self, event: str, data: Any = None, *, to: str | None = None) -> Any:
        """
        触发事件（同步，精简版）

        同步执行所有处理器。异步处理器会在当前事件循环中以 create_task 调度。
        注意：同步模式下异步处理器的返回值无法回传。

        指定 ``to`` 时进入定向传播（语义同 :meth:`emit` 的定向模式）。

        :param event: str 事件名称
        :param data: Any 事件数据
        :param to: str 定向投递目标拥有者，None 广播
        :return: Any 处理后的数据
        :raises ValueError: ``to`` 为空字符串时

        :example:
        >>> result = lifecycle.emit_sync("config.set", {"key": "test"})
        """
        if to is not None:
            if not to:
                raise ValueError(i18n.t("core.lifecycle.to_required"))
            parts = event.split(".")
            keys = [event] + [".".join(parts[:i]) for i in range(len(parts) - 1, 0, -1)]
            for key in keys:
                handlers = self._hooks.get(key)
                if handlers and any(o == to for (_p, _h, o) in handlers):
                    data = self._execute_handlers_sync(key, event, data, owner_filter=to)
            return data

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

    def fire(self, event: str, data: Any = None, *, to: str | None = None) -> None:
        """
        触发事件（后台，扔桶即走）——观测类事件的零成本发射

        与 :meth:`emit` 的差异：处理器在后台任务中并行执行，**不等待完成、
        无返回值**，本调用在无监听者时零开销（``has_handlers`` 短路），
        有监听者时仅付出一次任务调度成本。适用于高频热路径与纯观测事件
        （如 ``server.request`` / ``storage.ready``）。

        .. warning::
            后台事件**不保证执行时机**：emit 返回 ≠ 处理器已执行；
            框架关停期间后台任务会被取消——关停序列（uninit）中的
            事件请改用 :meth:`emit`。顺序敏感的消费（如 ``config.set``
            驱动的作用域重建）同样必须用 :meth:`emit`。

        :param event: str 事件名称
        :param data: Any 事件数据（dict 时自动附加 `_trace_id`）
        :param to: str 定向投递目标拥有者，None 广播

        :example:
        >>> lifecycle.fire("server.request", {"method": "GET", "path": "/"})
        """
        if not self.has_handlers(event):
            return
        from ..runtime.tasks import spawn_background

        spawn_background(self.emit(event, data, to=to))

    # ==================== 兼容 API ====================

    async def submit_event(
        self,
        event_type: str,
        *,
        source: str = DEFAULT_EVENT_SOURCE,
        msg: str = "",
        data: dict | None = None,
        timestamp: float | None = None,
        to: str | None = None,
        background: bool = False,
    ) -> None:
        """
        提交生命周期事件（兼容旧版 API）

        构建标准事件格式后通过 emit 触发，处理器接收标准事件字典；
        ``background=True`` 时改走 :meth:`fire` 后台发射（不等待处理器，
        适用于进度展示类观测事件，如 ``core.init.stage``）。

        :param event_type: str 事件名称
        :param source: str 事件来源(默认"ErisPulse")
        :param msg: str 事件描述
        :param data: dict 事件相关数据
        :param timestamp: float 时间戳(默认当前时间)
        :param to: str 定向投递目标拥有者（语义同 :meth:`emit`），None 广播
        :param background: bool 后台发射不等待处理器（默认 False）

        :raises ValueError: ``to`` 为空字符串时

        :example:
        >>> await lifecycle.submit_event("module.load", data={"module_name": "Test"})
        >>> await lifecycle.submit_event("maintenance", data={"action": "reload"}, to="Chat")
        """
        if event_type is None:
            _get_logger().error(i18n.t("core.lifecycle.event_type_none"))
            return

        if not isinstance(event_type, str) or not event_type:
            _get_logger().error(
                i18n.t("core.lifecycle.event_type_empty", type=event_type)
            )
            return

        _get_logger().trace(i18n.t("core.lifecycle.submit_event_enter", event=event_type, source=source))

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

        if background:
            self.fire(event_type, event_data, to=to)
        else:
            await self.emit(event_type, event_data, to=to)

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
        self, hook_name: str, event: str, data: Any, owner_filter: str | None = None
    ) -> Any:
        """
        执行匹配事件的处理（异步，处理器并行）

        每个处理器包装为独立协程经 ``asyncio.gather`` 并行执行——慢处理器
        不再阻塞其余处理器与触发方，总耗时从"各处理器之和"降为"最慢一个"。
        处理器返回非 None 值时按注册（优先级）顺序回放链式替换 data：
        所有处理器收到的是**同一份输入**，回放顺序确定性可预期。

        :param hook_name: str 注册的钩子名
        :param event: str 实际事件名
        :param data: Any 事件数据
        :param owner_filter: str 仅执行该拥有者注册的处理器（定向传播，None 不限）
        :return: Any 处理器链处理结果
        """
        selected = [
            (priority, handler, h_owner)
            for priority, handler, h_owner in self._hooks[hook_name]
            if owner_filter is None or h_owner == owner_filter
        ]
        if not selected:
            return data

        async def _run_one(handler: Callable, priority: int) -> Any:
            hname = getattr(
                handler, "__qualname__", getattr(handler, "__name__", str(handler))
            )
            try:
                _get_logger().trace(
                    i18n.t("core.lifecycle.handler_exec", handler=hname, priority=priority, event=event)
                )
                _t = time.monotonic()
                if inspect.iscoroutinefunction(handler):
                    result = await handler(data)
                else:
                    result = handler(data)
                _elapsed = time.monotonic() - _t
                if _elapsed > HANDLER_SLOW_THRESHOLD_SECS:
                    _get_logger().warning(
                        f"[Lifecycle] Slow handler {hname} for event '{event}' took {_elapsed:.4f}s"
                    )
                return result
            except Exception as e:
                _get_logger().error(
                    i18n.t("core.lifecycle.handler_error", event=event, error=e)
                )
                return None

        results = await asyncio.gather(
            *(_run_one(handler, priority) for priority, handler, _ in selected)
        )
        for result in results:
            if result is not None:
                data = result
        return data

    def _execute_handlers_sync(
        self, hook_name: str, event: str, data: Any, owner_filter: str | None = None
    ) -> Any:
        """
        执行匹配的事件处理器（同步）

        :param hook_name: str 注册的钩子名
        :param event: str 实际事件名
        :param data: Any 事件数据
        :param owner_filter: str 仅执行该拥有者注册的处理器（定向传播，None 不限）
        :return: Any 处理后的数据
        """
        for _, handler, _owner in self._hooks[hook_name]:
            if owner_filter is not None and _owner != owner_filter:
                continue
            try:
                if inspect.iscoroutinefunction(handler):
                    from ..runtime.tasks import spawn_background

                    spawn_background(handler(data))
                else:
                    result = handler(data)
                    if result is not None:
                        data = result
            except Exception as e:
                _get_logger().error(
                    i18n.t("core.lifecycle.handler_error", event=event, error=e)
                )
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
