"""
后台任务管理工具

提供 fire-and-forget 模式的任务调度，避免被 GC 回收，并支持按
资源归属者（模块名/适配器平台名）跟踪与取消任务。

{!--< tips >!--}
1. ``spawn_background(coro)`` 调度一个不关心返回值的协程
2. 任务自动归属到当前 ``owner_scope`` 上下文（模块/适配器），卸载时可由框架兜底取消
3. ``cancel_owner_tasks(owner)`` 取消并等待指定归属者的全部后台任务与定时器
4. ``cancel_all_background_tasks()`` 供 ``sdk.uninit()`` 兜底清理
5. ``install_owner_task_factory()``（随启动自动安装）：事件循环级任务工厂，
   owner 上下文内**任何** ``asyncio.create_task``（含第三方库）自动归属、卸载兜底取消
6. ``run_main_loop(coro)`` 从子线程安全投递到主循环并阻塞取结果；
   ``spawn_later(delay, coro_fn)`` 归属化的延迟调度（裸 ``loop.call_later`` 不归属）
7. ``spawn_thread(name, target)`` 归属化的线程启动（观测面；线程不可强杀，
   退出清理靠 ``on_cleanup`` 约定）
{!--< /tips >!--}
"""

from __future__ import annotations

import asyncio
import inspect
import threading
import weakref
from collections.abc import Awaitable, Callable, Coroutine
from typing import Any, TypeVar, cast

from ..Core.constants import DEFAULT_OWNER_CANCEL_TIMEOUT_SECS
from .context import current_owner

_T = TypeVar("_T")

# 模块级后台任务引用集合。Task 完成后会通过 done_callback 自动从集合中移除。
# 这样可保证 fire-and-forget 调度的任务在执行期间不会被 Python GC 回收。
_background_tasks: set[asyncio.Task[Any]] = set()

# 按资源归属者索引的后台任务表：
#   key   = owner（模块名/适配器平台名），None 表示无归属上下文的任务
#   value = 该 owner 名下所有未完成的后台任务（Task 或调度回主循环的 Future）
# 卸载模块/关闭适配器时按 owner 兜底取消，防止任务持有实例引用导致无法回收。
_owner_tasks: dict[str | None, set[Any]] = {}

# 按资源归属者索引的定时器句柄表（loop.call_later 产生的 TimerHandle 不经过
# task factory，是任务归属体系的盲区；spawn_later 经此登记后随卸载兜底取消）。
_owner_timers: dict[str | None, set[asyncio.TimerHandle]] = {}

# 按资源归属者索引的存活线程表（线程无法强杀，登记仅作观测与审计；
# 线程自然退出后经包装 target 自动移除）。
_owner_threads: dict[str | None, set[threading.Thread]] = {}

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
    install_owner_task_factory(loop)


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

    正在执行本取消逻辑的任务自身会被**排除**：``uninit()`` 的兜底取消
    由 ``_do_hard_restart`` 等任务驱动，若把当前任务也取消，Python 3.13
    的取消传播会沿其正在等待的 ``gather`` 结构回环（当前任务 -> gather
    -> 再取消当前任务），触发 ``RecursionError`` 且后续清理（如
    ``os._exit``）永远无法执行。

    :param owner: 资源归属者（模块名/适配器平台名）
    :param timeout: 等待任务回收的超时秒数，超时后不再阻塞
    :return: 发起取消的任务数
    """
    # 该归属者名下的未触发定时器一并取消（TimerHandle.cancel 幂等且立即生效）
    timers = _owner_timers.pop(owner, None)
    if timers:
        for handle in timers:
            try:
                handle.cancel()
            except Exception:
                pass
        timers.clear()

    tasks = _owner_tasks.pop(owner, None)
    if not tasks:
        return 0

    # 防自取消：排除当前正在执行取消逻辑的任务（见 docstring——
    # 取消自身会经 gather 取消传播形成递归环，RecursionError 后续清理全部中断）
    current = asyncio.current_task()
    pending: list[Any] = [
        t for t in tasks if not t.done() and t is not current
    ]
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
        except asyncio.TimeoutError:
            # 超时：任务已处于 cancelled 状态，最终会自行结束
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
    for owner in list(_owner_tasks.keys()) + list(_owner_timers.keys()):
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
    coro = cast('Coroutine[Any, Any, Any]', coro)

    # 从非主循环线程（如同步桥接线程 / config watcher）调度时，优先投递回
    # 主事件循环：桥接循环可能按次运行（run_until_complete 用完即停），
    # 其上排队的后台任务会被孤立而永不执行；业务协程也理应回到主循环。
    main_loop = _get_main_loop()
    if main_loop is not None and main_loop.is_running():
        try:
            current_loop = asyncio.get_running_loop()
        except RuntimeError:
            current_loop = None
        if current_loop is not None and current_loop is not main_loop:
            try:
                future = asyncio.run_coroutine_threadsafe(coro, main_loop)
                _track_owner_task(task_owner, future)
                return future
            except RuntimeError:
                pass

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
        # 业务协程若绑定了主循环资源（存储连接 / ContextVar 关联 Task），
        # 在异循环上执行可能报 "attached to a different loop"，留痕供排查
        from ..Core.i18n import i18n as _i18n
        from ..Core.logger import logger

        logger.warning(_i18n.t("runtime.tasks.temp_loop_fallback", owner=task_owner or "-"))
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


def run_main_loop(coro: Coroutine[Any, Any, _T], *, timeout: float | None = None) -> _T:
    """
    从子线程安全投递协程到主循环并阻塞等待结果

    跨线程投递的标准工具：在主循环内调用时直接报错（应 ``await``）；
    在其它线程（含其它事件循环的线程）调用时经
    ``asyncio.run_coroutine_threadsafe`` 投递回已注册的主循环并阻塞取结果。
    广播、推送、连接操作等凡从子线程触达主循环资源的场景都应基于它，
    不再手写 ``run_coroutine_threadsafe``。

    :param coro: 待执行的协程对象
    :param timeout: 阻塞等待结果的超时秒数；None 表示无限等待
    :return: 协程的返回值
    :raises RuntimeError: 在主循环内同步调用（应改为 await），
                         或超时未完成（:class:`TimeoutError`）

    :example:
    >>> # 在子线程里向某分组广播：
    >>> run_main_loop(connections.broadcast({"type": "ping"}, group="room:1"), timeout=5)
    """
    main_loop = _get_main_loop()
    try:
        current_loop: asyncio.AbstractEventLoop | None = asyncio.get_running_loop()
    except RuntimeError:
        current_loop = None

    if current_loop is not None and (main_loop is None or current_loop is main_loop):
        raise RuntimeError(
            "run_main_loop() 在主循环内同步调用；请直接 await 该协程，"
            "或改用 spawn_background() fire-and-forget"
        )

    if main_loop is not None and main_loop.is_running():
        future = asyncio.run_coroutine_threadsafe(coro, main_loop)
        return future.result(timeout)

    # 兜底：主循环尚未注册（过早调用）——临时事件循环同步执行，留痕供排查
    from ..Core.i18n import i18n as _i18n
    from ..Core.logger import logger

    logger.warning(_i18n.t("runtime.tasks.temp_loop_fallback", owner="run_main_loop"))
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


def _warn_coro_fn_failed(error: Exception) -> None:
    """{!--< internal-use >!--} spawn_later 触发回调失败留痕（不中断事件循环回调调度）"""
    try:
        from ..Core.i18n import i18n as _i18n
        from ..Core.logger import logger

        logger.warning(_i18n.t("runtime.tasks.spawn_later_failed", error=error))
    except Exception:
        pass


def spawn_later(
    delay: float,
    coro_fn: Callable[[], Awaitable[Any]],
    *args: Any,
    owner: str | None = None,
) -> asyncio.TimerHandle:
    """
    归属化的延迟调度（``loop.call_later`` 的 owner 感知包装）

    裸 ``loop.call_later`` 产生的 TimerHandle 不经过任务工厂，是归属权
    体系的盲区；本函数把句柄登记到 owner 名下，模块卸载时随
    ``cancel_owner_tasks`` 兜底取消，触发后经 ``spawn_background`` 调度
    协程（同样归属该 owner）。

    :param delay: 延迟秒数
    :param coro_fn: 返回可等待对象的工厂函数（在触发瞬间调用；
                    传协程工厂而非协程对象，可避免取消后 "never awaited" 警告）
    :param args: 传给 ``coro_fn`` 的位置参数
    :param owner: 显式指定资源归属者；缺省时从当前 owner 上下文捕获
    :return: :class:`asyncio.TimerHandle`（可提前 ``handle.cancel()``）

    :example:
    >>> spawn_later(30, lambda: cleanup_expired(), owner="MyModule")
    """
    task_owner = owner if owner is not None else current_owner.get()

    def _fire() -> None:
        try:
            try:
                result = coro_fn(*args)
            except Exception as e:
                _warn_coro_fn_failed(e)
                return
            if not inspect.isawaitable(result):
                # 工厂未返回可等待对象：留痕并忽略，避免 asyncio 回调栈噪声
                _warn_coro_fn_failed(TypeError("coro_fn did not return an awaitable"))
                return
            spawn_background(result, owner=task_owner)
        finally:
            timers = _owner_timers.get(task_owner)
            if timers is not None:
                timers.discard(handle)

    main_loop = _get_main_loop()
    try:
        loop: asyncio.AbstractEventLoop | None = asyncio.get_running_loop()
    except RuntimeError:
        loop = None
    if loop is None:
        loop = main_loop

    if loop is None:
        # 无可用事件循环：降级为线程型定时器（同样登记归属，cancel 语义一致）
        def _fire_threaded() -> None:
            try:
                result = coro_fn(*args)
                if inspect.isawaitable(result):
                    spawn_background(result, owner=task_owner)
                else:
                    _warn_coro_fn_failed(TypeError("coro_fn did not return an awaitable"))
            except Exception as e:
                _warn_coro_fn_failed(e)
            finally:
                timers = _owner_timers.get(task_owner)
                if timers is not None:
                    timers.discard(timer)

        timer = threading.Timer(delay, _fire_threaded)
        timer.daemon = True
        timers = _owner_timers.setdefault(task_owner, set())
        # 线程型兜底定时器鸭子类型兼容（有 .cancel()），登记进同一归属表
        timers.add(cast(asyncio.TimerHandle, timer))
        timer.start()
        return cast(asyncio.TimerHandle, timer)

    handle = loop.call_later(delay, _fire)
    timers = _owner_timers.setdefault(task_owner, set())
    timers.add(handle)
    return handle


def spawn_thread(
    name: str,
    target: Callable[..., Any],
    *args: Any,
    owner: str | None = None,
    daemon: bool = True,
) -> threading.Thread:
    """
    归属化的线程启动（观测面）

    线程无法被框架强制终止：登记使 ``ownership.counts()`` / 泄漏审计
    可见该归属者的存活线程，退出清理由业务在 ``on_cleanup`` 中自行约定
    （与框架内部 config-watcher / file-watcher 的兜底风格一致）。

    :param name: 线程名（自动加 ``erispulse:`` 前缀便于辨识）
    :param target: 线程入口函数
    :param args: 传给 ``target`` 的位置参数
    :param owner: 显式指定资源归属者；缺省时从当前 owner 上下文捕获
    :param daemon: 是否守护线程 (默认: True，随主进程退出)
    :return: 已启动的 :class:`threading.Thread`

    :example:
    >>> spawn_thread("poller", poll_loop, owner="MyAdapter")
    """
    task_owner = owner if owner is not None else current_owner.get()

    def _runner() -> None:
        try:
            target(*args)
        finally:
            threads = _owner_threads.get(task_owner)
            if threads is not None:
                threads.discard(thread)

    thread = threading.Thread(target=_runner, name=f"erispulse:{name}", daemon=daemon)
    threads = _owner_threads.setdefault(task_owner, set())
    threads.add(thread)
    thread.start()
    return thread


def get_owner_timers(owner: str | None) -> set[asyncio.TimerHandle]:
    """
    获取指定归属者名下未触发的定时器句柄集合

    :param owner: 资源归属者（模块名/适配器平台名）
    :return: 未触发句柄集合的浅拷贝
    """
    return set(_owner_timers.get(owner, ()))


def get_owner_threads(owner: str | None) -> set[threading.Thread]:
    """
    获取指定归属者名下存活的线程集合

    :param owner: 资源归属者（模块名/适配器平台名）
    :return: 存活线程集合的浅拷贝
    """
    return {t for t in _owner_threads.get(owner, ()) if t.is_alive()}


__all__ = [
    "cancel_all_background_tasks",
    "install_owner_task_factory",
    "cancel_owner_tasks",
    "get_owner_tasks",
    "get_owner_threads",
    "get_owner_timers",
    "register_main_loop",
    "run_main_loop",
    "spawn_background",
    "spawn_later",
    "spawn_thread",
]


# ==================== Owner 感知的 Task Factory ====================
#
# asyncio 官方扩展点（loop.set_task_factory）：事件循环上**任何**任务创建
# （含第三方库 aiohttp / APScheduler 等内部 create_task）都会经过这里。
# 创建瞬间读取 current_owner——owner_scope 上下文内的任务自动登记到归属表，
# 卸载时随 cancel_owner_tasks 兜底取消；无归属上下文（框架自身）的任务
# 不登记、行为与默认完全一致。

_FACTORY_INSTALLED_LOOPS: weakref.WeakSet[asyncio.AbstractEventLoop] = weakref.WeakSet()


def _owner_aware_task_factory(loop: asyncio.AbstractEventLoop, coro: Any, **kwargs: Any) -> asyncio.Task[Any]:
    """{!--< internal-use >!--} 任务创建钩子：归属上下文内的任务自动登记（供卸载兜底取消）

    ``**kwargs`` 必须保留并向 :class:`asyncio.Task` 透传：Python 3.13 起
    事件循环以 ``factory(loop, coro, **kwargs)`` 调用任务工厂（携带 context）。
    """
    task = asyncio.Task(coro, **kwargs)
    owner = current_owner.get()
    if owner is not None:
        _track_owner_task(owner, task)
    return task


def install_owner_task_factory(loop: asyncio.AbstractEventLoop) -> bool:
    """
    为事件循环安装 owner 感知的任务工厂（幂等）

    安装后，`owner_scope` 上下文内通过 `asyncio.create_task` / `ensure_future`
    创建的**所有**任务（包括第三方库内部创建的）自动登记到当前归属者名下，
    模块卸载 / 适配器关闭时随 `cancel_owner_tasks` 兜底取消。无归属上下文
    （owner=None）的任务不受影响。

    由 `register_main_loop` 在框架启动时自动调用。

    :param loop: 目标事件循环
    :return: 是否实际安装（重复调用返回 False）
    """
    if loop in _FACTORY_INSTALLED_LOOPS:
        return False
    # 协议标注（typeshed _TaskFactory）未覆盖 3.13 的 **kwargs 调用形态，
    # 运行时签名以 3.10–3.13 实际调用约定为准，此处断言绕开协议收窄
    loop.set_task_factory(cast(Any, _owner_aware_task_factory))
    _FACTORY_INSTALLED_LOOPS.add(loop)
    return True
