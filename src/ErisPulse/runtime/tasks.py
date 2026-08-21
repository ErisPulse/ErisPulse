"""
后台任务管理工具

提供 fire-and-forget 模式的任务调度，避免被 GC 回收，并支持按
资源归属者（模块名/适配器平台名）跟踪与取消任务。

{!--< tips >!--}
1. ``spawn_background(coro)`` 调度一个不关心返回值的协程
2. 任务自动归属到当前 ``owner_scope`` 上下文（模块/适配器），卸载时可由框架兜底取消
3. ``cancel_owner_tasks(owner)`` 取消并等待指定归属者的全部后台任务
4. ``cancel_all_background_tasks()`` 供 ``sdk.uninit()`` 兜底清理
{!--< /tips >!--}
"""

from __future__ import annotations

import asyncio
import threading
from collections.abc import Awaitable, Coroutine
from typing import Any, TypeVar

from .context import current_owner
from ..Core.constants import DEFAULT_OWNER_CANCEL_TIMEOUT_SECS

_T = TypeVar("_T")

# 模块级后台任务引用集合。Task 完成后会通过 done_callback 自动从集合中移除。
# 这样可保证 fire-and-forget 调度的任务在执行期间不会被 Python GC 回收。
_background_tasks: set[asyncio.Task[Any]] = set()

# 按资源归属者索引的后台任务表：
#   key   = owner（模块名/适配器平台名），None 表示无归属上下文的任务
#   value = 该 owner 名下所有未完成的后台任务（Task 或调度回主循环的 Future）
# 卸载模块/关闭适配器时按 owner 兜底取消，防止任务持有实例引用导致无法回收。
_owner_tasks: dict[str | None, set[Any]] = {}

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


def _track_owner_task(owner: str | None, task: Any) -> None:
    """
    将任务登记到归属者索引

    {!--< internal-use >!--}
    {!--< /internal-use >!--}

    :param owner: 资源归属者（模块名/适配器平台名），None 表示无归属
    :param task: 已调度的 Task 或 Future
    """
    tasks = _owner_tasks.get(owner)
    if tasks is None:
        tasks = _owner_tasks[owner] = set()
    tasks.add(task)
    try:
        task.add_done_callback(tasks.discard)
    except Exception:
        # concurrent.futures.Future 支持 add_done_callback；防御异常实现
        tasks.discard(task)


def get_owner_tasks(owner: str | None) -> set[Any]:
    """
    获取指定归属者名下未完成的后台任务集合

    用于调试与泄漏可见性：模块/适配器卸载后若仍有存活任务，
    可通过此接口检查（正常情况下框架已在卸载时兜底取消）。

    :param owner: 资源归属者（模块名/适配器平台名），None 表示无归属任务
    :return: 未完成任务集合的浅拷贝
    """
    return set(_owner_tasks.get(owner, ()))


async def cancel_owner_tasks(owner: str | None, *, timeout: float = DEFAULT_OWNER_CANCEL_TIMEOUT_SECS) -> int:
    """
    取消并等待指定归属者的全部后台任务

    模块卸载 / 适配器关闭时由框架调用，兜底清理模块在 ``on_unload``
    中未自行取消的任务，防止任务持有实例引用导致模块无法被回收
    （热重载泄漏的常见根因）。

    :param owner: 资源归属者（模块名/适配器平台名）
    :param timeout: 等待任务回收的超时秒数，超时后不再阻塞
    :return: 发起取消的任务数
    """
    tasks = _owner_tasks.pop(owner, None)
    if not tasks:
        return 0

    pending: list[Any] = [t for t in tasks if not t.done()]
    cancelled = 0
    for task in pending:
        try:
            task.cancel()
            cancelled += 1
        except Exception:
            pass

    if pending:
        try:
            await asyncio.wait_for(
                asyncio.gather(*pending, return_exceptions=True),
                timeout=timeout,
            )
        except (asyncio.TimeoutError, Exception):
            # 超时或等待异常：任务已处于 cancelled 状态，最终会自行结束
            pass
    return cancelled


async def cancel_all_background_tasks(*, timeout: float = DEFAULT_OWNER_CANCEL_TIMEOUT_SECS) -> int:
    """
    取消并等待全部后台任务

    供 ``sdk.uninit()`` 在清理阶段兜底调用，确保框架退出时没有
    悬挂的 fire-and-forget 任务（如 message.sending 钩子、异步
    生命周期处理器调度等）。

    :param timeout: 等待任务回收的超时秒数
    :return: 发起取消的任务数
    """
    total = 0
    # 无归属上下文（None 键）的任务同样会被遍历清理
    for owner in list(_owner_tasks.keys()):
        total += await cancel_owner_tasks(owner, timeout=timeout)
    return total


def spawn_background(coro: Awaitable[_T] | Coroutine[_T, Any, Any], *, owner: str | None = None) -> Any:
    """
    调度一个 fire-and-forget 后台任务

    优先在当前线程的事件循环中调度；如果当前线程没有运行中的事件循环
    （如配置监听后台线程），则优先调度回主事件循环（若已注册且正在运行），
    否则创建一个临时事件循环同步执行，确保协程在任何情况下都会被运行。

    任务会自动归属到当前 ``owner_scope`` 上下文（模块名/适配器平台名），
    卸载/关闭时框架按归属兜底取消；也可通过 ``owner`` 参数显式指定。

    内部将协程包装为 :class:`asyncio.Task`，并把引用保留到模块级集合中，
    直到任务结束自动清理。避免直接调用 ``loop.create_task`` / ``asyncio.ensure_future``
    后由于引用丢失被 GC 提前回收（``RUF006`` 警告对应的真实风险）。

    :param coro: 待执行的协程或可等待对象
    :param owner: 显式指定资源归属者；缺省时从当前 owner 上下文捕获
    :return: 创建出的 :class:`asyncio.Task` / 调度回主循环的
             :class:`concurrent.futures.Future`，调用方可忽略返回值；
             在临时事件循环中同步执行时返回 ``None``
    :example:
    >>> spawn_background(some_async_work())
    """
    task_owner = owner if owner is not None else current_owner.get()

    try:
        task = asyncio.ensure_future(coro)  # type: ignore[arg-type]
    except RuntimeError:
        # 当前线程没有运行中事件循环（如 config watcher 后台线程）。
        # 优先调度回主事件循环，确保业务代码在正确的循环上运行。
        main_loop = _get_main_loop()
        if main_loop is not None and main_loop.is_running():
            try:
                future = asyncio.run_coroutine_threadsafe(coro, main_loop)
                _track_owner_task(task_owner, future)
                return future
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
    _track_owner_task(task_owner, task)

    return task


__all__ = [
    "cancel_all_background_tasks",
    "cancel_owner_tasks",
    "get_owner_tasks",
    "register_main_loop",
    "spawn_background",
]
