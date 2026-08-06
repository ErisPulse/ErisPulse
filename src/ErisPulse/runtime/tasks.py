"""
后台任务管理工具

提供 fire-and-forget 模式的任务调度，避免被 GC 回收。

{!--< tips >!--}
1. ``spawn_background(coro)`` 调度一个不关心返回值的协程
2. 内部使用模块级集合保留 Task 引用，任务完成后自动清理
3. 避免出现 ``RUF006`` 所警告的“asyncio 任务悬挂被 GC”问题
{!--< /tips >!--}
"""

from __future__ import annotations

import asyncio
import threading
from collections.abc import Awaitable, Coroutine
from typing import Any, TypeVar

_T = TypeVar("_T")

# 模块级后台任务引用集合。Task 完成后会通过 done_callback 自动从集合中移除。
# 这样可保证 fire-and-forget 调度的任务在执行期间不会被 Python GC 回收。
_background_tasks: set[asyncio.Task[Any]] = set()

# 主事件循环注册表：由 ``sdk.run()`` / ``sdk.init()`` 在启动时注册。
# 后台线程（如 config watcher）在无事件循环时，可通过它把协程调度回主循环，
# 避免在临时事件循环中执行业务代码导致的 "Future attached to a different loop"。
_MAIN_LOOP: asyncio.AbstractEventLoop | None = None
_MAIN_LOOP_LOCK = threading.Lock()


def register_main_loop(loop: asyncio.AbstractEventLoop) -> None:
    """
    注册当前主事件循环

    供后台线程将协程调度回主循环使用（见 ``spawn_background``）。

    {!--< internal-use >!--}
    由 SDK 启动流程调用；重复注册会覆盖为最新循环。
    {!--< /internal-use >!--}

    :param loop: 正在运行的主事件循环
    """
    global _MAIN_LOOP
    with _MAIN_LOOP_LOCK:
        _MAIN_LOOP = loop


def _get_main_loop() -> asyncio.AbstractEventLoop | None:
    """
    线程安全地读取已注册的主事件循环

    {!--< internal-use >!--}
    仅供 ``spawn_background`` 等内部调度使用。
    {!--< /internal-use >!--}

    :return: 已注册的主事件循环，未注册时返回 None
    """
    with _MAIN_LOOP_LOCK:
        return _MAIN_LOOP


def spawn_background(coro: Awaitable[_T] | Coroutine[_T, Any, Any]) -> Any:
    """
    调度一个 fire-and-forget 后台任务

    优先在当前线程的事件循环中调度；如果当前线程没有运行中的事件循环
    （如配置监听后台线程），则优先调度回主事件循环（若已注册且正在运行），
    否则创建一个临时事件循环同步执行，确保协程在任何情况下都会被运行。

    内部将协程包装为 :class:`asyncio.Task`，并把引用保留到模块级集合中，
    直到任务结束自动清理。避免直接调用 ``loop.create_task`` / ``asyncio.ensure_future``
    后由于引用丢失被 GC 提前回收（``RUF006`` 警告对应的真实风险）。

    :param coro: 待执行的协程或可等待对象
    :return: 创建出的 :class:`asyncio.Task` / 调度回主循环的
             :class:`concurrent.futures.Future`，调用方可忽略返回值；
             在临时事件循环中同步执行时返回 ``None``
    :example:
    >>> spawn_background(some_async_work())
    """
    try:
        task = asyncio.ensure_future(coro)  # type: ignore[arg-type]
    except RuntimeError:
        # 当前线程没有运行中事件循环（如 config watcher 后台线程）。
        # 优先调度回主事件循环，确保业务代码在正确的循环上运行。
        main_loop = _get_main_loop()
        if main_loop is not None and main_loop.is_running():
            try:
                return asyncio.run_coroutine_threadsafe(coro, main_loop)
            except RuntimeError:
                pass
        # 兜底：创建一个临时事件循环同步执行，确保协程不会丢失。
        _loop = asyncio.new_event_loop()
        try:
            _loop.run_until_complete(coro)
        finally:
            _loop.close()
        return None

    # 把引用塞进模块级集合，并在完成时自动清理
    _background_tasks.add(task)
    task.add_done_callback(_background_tasks.discard)

    return task


__all__ = ["register_main_loop", "spawn_background"]
