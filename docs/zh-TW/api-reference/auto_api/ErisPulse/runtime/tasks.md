# `ErisPulse.runtime.tasks` 模块

---

## 模块概述


后台任务管理工具

提供 fire-and-forget 模式的任务调度，避免被 GC 回收，并支持按
资源归属者（模块名/适配器平台名）跟踪与取消任务。

> **提示**
> 1. ``spawn_background(coro)`` 调度一个不关心返回值的协程
> 2. 任务自动归属到当前 ``owner_scope`` 上下文（模块/适配器），卸载时可由框架兜底取消
> 3. ``cancel_owner_tasks(owner)`` 取消并等待指定归属者的全部后台任务与定时器
> 4. ``cancel_all_background_tasks()`` 供 ``sdk.uninit()`` 兜底清理
> 5. ``install_owner_task_factory()``（随启动自动安装）：事件循环级任务工厂，
> owner 上下文内**任何** ``asyncio.create_task``（含第三方库）自动归属、卸载兜底取消
> 6. ``run_main_loop(coro)`` 从子线程安全投递到主循环并阻塞取结果；
> ``spawn_later(delay, coro_fn)`` 归属化的延迟调度（裸 ``loop.call_later`` 不归属）
> 7. ``spawn_thread(name, target)`` 归属化的线程启动（观测面；线程不可强杀，
> 退出清理靠 ``on_cleanup`` 约定）

---

## 函数列表


### `register_main_loop(loop: asyncio.AbstractEventLoop) -> None`

注册当前主事件循环

供后台线程将协程调度回主循环使用（见 ``spawn_background``）。

**内部方法**
由 SDK 启动流程调用；重复注册会覆盖为最新循环。

- **loop**: 正在运行的主事件循环

---


### `_get_main_loop() -> asyncio.AbstractEventLoop | None`

线程安全地读取已注册的主事件循环

**内部方法**
仅供 ``spawn_background`` 等内部调度使用。

**返回值**: 已注册的主事件循环，未注册时返回 None

---


### `_track_owner_task(owner: str | None, task: Any) -> None`

将任务登记到归属者索引

**内部方法**

- **owner**: 资源归属者（模块名/适配器平台名），None 表示无归属
- **task**: 已调度的 Task 或 Future

---


### `get_owner_tasks(owner: str | None) -> set[Any]`

获取指定归属者名下未完成的后台任务集合

用于调试与泄漏可见性：模块/适配器卸载后若仍有存活任务，
可通过此接口检查（正常情况下框架已在卸载时兜底取消）。

- **owner**: 资源归属者（模块名/适配器平台名），None 表示无归属任务

**返回值**: 未完成任务集合的浅拷贝

---


### `async cancel_owner_tasks(owner: str | None, *, timeout: float = DEFAULT_OWNER_CANCEL_TIMEOUT_SECS) -> int`

取消并等待指定归属者的全部后台任务

模块卸载 / 适配器关闭时由框架调用，兜底清理模块在 ``on_unload``
中未自行取消的任务，防止任务持有实例引用导致模块无法被回收
（热重载泄漏的常见根因）。

正在执行本取消逻辑的任务自身会被**排除**：``uninit()`` 的兜底取消
由 ``_do_hard_restart`` 等任务驱动，若把当前任务也取消，Python 3.13
的取消传播会沿其正在等待的 ``gather`` 结构回环（当前任务 -> gather
-> 再取消当前任务），触发 ``RecursionError`` 且后续清理（如
``os._exit``）永远无法执行。

- **owner**: 资源归属者（模块名/适配器平台名）
- **timeout**: 等待任务回收的超时秒数，超时后不再阻塞

**返回值**: 发起取消的任务数

---


### `async cancel_all_background_tasks(*, timeout: float = DEFAULT_OWNER_CANCEL_TIMEOUT_SECS) -> int`

取消并等待全部后台任务

供 ``sdk.uninit()`` 在清理阶段兜底调用，确保框架退出时没有
悬挂的 fire-and-forget 任务（如 message.sending 钩子、异步
生命周期处理器调度等）。

- **timeout**: 等待任务回收的超时秒数

**返回值**: 发起取消的任务数

---


### `spawn_background(coro: Awaitable[_T] | Coroutine[_T, Any, Any], *, owner: str | None = None) -> Any`

调度一个 fire-and-forget 后台任务

优先在当前线程的事件循环中调度；如果当前线程没有运行中的事件循环
（如配置监听后台线程），则优先调度回主事件循环（若已注册且正在运行），
否则创建一个临时事件循环同步执行，确保协程在任何情况下都会被运行。

任务会自动归属到当前 ``owner_scope`` 上下文（模块名/适配器平台名），
卸载/关闭时框架按归属兜底取消；也可通过 ``owner`` 参数显式指定。

内部将协程包装为 :class:`asyncio.Task`，并把引用保留到模块级集合中，
直到任务结束自动清理。避免直接调用 ``loop.create_task`` / ``asyncio.ensure_future``
后由于引用丢失被 GC 提前回收（``RUF006`` 警告对应的真实风险）。

- **coro**: 待执行的协程或可等待对象
- **owner**: 显式指定资源归属者；缺省时从当前 owner 上下文捕获

**返回值**: 创建出的 :class:`asyncio.Task` / 调度回主循环的

         :class:`concurrent.futures.Future`，调用方可忽略返回值；
         在临时事件循环中同步执行时返回 ``None``
**示例**:

```python
spawn_background(some_async_work())
```

---


### `run_main_loop(coro: Coroutine[Any, Any, _T], *, timeout: float | None = None) -> _T`

从子线程安全投递协程到主循环并阻塞等待结果

跨线程投递的标准工具：在主循环内调用时直接报错（应 ``await``）；
在其它线程（含其它事件循环的线程）调用时经
``asyncio.run_coroutine_threadsafe`` 投递回已注册的主循环并阻塞取结果。
广播、推送、连接操作等凡从子线程触达主循环资源的场景都应基于它，
不再手写 ``run_coroutine_threadsafe``。

- **coro**: 待执行的协程对象
- **timeout**: 阻塞等待结果的超时秒数；None 表示无限等待

**返回值**: 协程的返回值

**异常**: `RuntimeError` - 在主循环内同步调用（应改为 await），

                     或超时未完成（:class:`TimeoutError`）

**示例**:

```python
# 在子线程里向某分组广播：
run_main_loop(connections.broadcast({"type": "ping"}, group="room:1"), timeout=5)
```

---


### `_warn_coro_fn_failed(error: Exception) -> None`

**内部方法** spawn_later 触发回调失败留痕（不中断事件循环回调调度）

---


### `spawn_later(delay: float, coro_fn: Callable[[], Awaitable[Any]], *args: Any, owner: str | None = None) -> asyncio.TimerHandle`

归属化的延迟调度（``loop.call_later`` 的 owner 感知包装）

裸 ``loop.call_later`` 产生的 TimerHandle 不经过任务工厂，是归属权
体系的盲区；本函数把句柄登记到 owner 名下，模块卸载时随
``cancel_owner_tasks`` 兜底取消，触发后经 ``spawn_background`` 调度
协程（同样归属该 owner）。

- **delay**: 延迟秒数
- **coro_fn**: 返回可等待对象的工厂函数（在触发瞬间调用；

                传协程工厂而非协程对象，可避免取消后 "never awaited" 警告）
- **args**: 传给 ``coro_fn`` 的位置参数
- **owner**: 显式指定资源归属者；缺省时从当前 owner 上下文捕获

**返回值**: :class:`asyncio.TimerHandle`（可提前 ``handle.cancel()``）

**示例**:

```python
spawn_later(30, lambda: cleanup_expired(), owner="MyModule")
```

---


### `spawn_thread(name: str, target: Callable[..., Any], *args: Any, owner: str | None = None, daemon: bool = True) -> threading.Thread`

归属化的线程启动（观测面）

线程无法被框架强制终止：登记使 ``ownership.counts()`` / 泄漏审计
可见该归属者的存活线程，退出清理由业务在 ``on_cleanup`` 中自行约定
（与框架内部 config-watcher / file-watcher 的兜底风格一致）。

- **name**: 线程名（自动加 ``erispulse:`` 前缀便于辨识）
- **target**: 线程入口函数
- **args**: 传给 ``target`` 的位置参数
- **owner**: 显式指定资源归属者；缺省时从当前 owner 上下文捕获
- **daemon**: 是否守护线程 (默认: True，随主进程退出)

**返回值**: 已启动的 :class:`threading.Thread`

**示例**:

```python
spawn_thread("poller", poll_loop, owner="MyAdapter")
```

---


### `get_owner_timers(owner: str | None) -> set[asyncio.TimerHandle]`

获取指定归属者名下未触发的定时器句柄集合

- **owner**: 资源归属者（模块名/适配器平台名）

**返回值**: 未触发句柄集合的浅拷贝

---


### `get_owner_threads(owner: str | None) -> set[threading.Thread]`

获取指定归属者名下存活的线程集合

- **owner**: 资源归属者（模块名/适配器平台名）

**返回值**: 存活线程集合的浅拷贝

---


### `_owner_aware_task_factory(loop: asyncio.AbstractEventLoop, coro: Any, **kwargs: Any) -> asyncio.Task[Any]`

**内部方法** 任务创建钩子：归属上下文内的任务自动登记（供卸载兜底取消）

``**kwargs`` 必须保留并向 :class:`asyncio.Task` 透传：Python 3.13 起
事件循环以 ``factory(loop, coro, **kwargs)`` 调用任务工厂（携带 context）。

---


### `install_owner_task_factory(loop: asyncio.AbstractEventLoop) -> bool`

为事件循环安装 owner 感知的任务工厂（幂等）

安装后，`owner_scope` 上下文内通过 `asyncio.create_task` / `ensure_future`
创建的**所有**任务（包括第三方库内部创建的）自动登记到当前归属者名下，
模块卸载 / 适配器关闭时随 `cancel_owner_tasks` 兜底取消。无归属上下文
（owner=None）的任务不受影响。

由 `register_main_loop` 在框架启动时自动调用。

- **loop**: 目标事件循环

**返回值**: 是否实际安装（重复调用返回 False）

---

