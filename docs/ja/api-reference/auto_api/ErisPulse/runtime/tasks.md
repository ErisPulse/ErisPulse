# `ErisPulse.runtime.tasks` 模块

---

## 模块概述


后台任务管理工具

提供 fire-and-forget 模式的任务调度，避免被 GC 回收，并支持按
资源归属者（模块名/适配器平台名）跟踪与取消任务。

> **提示**
> 1. ``spawn_background(coro)`` 调度一个不关心返回值的协程
> 2. 任务自动归属到当前 ``owner_scope`` 上下文（模块/适配器），卸载时可由框架兜底取消
> 3. ``cancel_owner_tasks(owner)`` 取消并等待指定归属者的全部后台任务
> 4. ``cancel_all_background_tasks()`` 供 ``sdk.uninit()`` 兜底清理

---

## 函数列表


### `register_main_loop(loop: asyncio.AbstractEventLoop)`

注册当前主事件循环

供后台线程将协程调度回主循环使用（见 ``spawn_background``）。

> **内部方法**
由 SDK 启动流程调用；重复注册会覆盖为最新循环。

- **loop**: 正在运行的主事件循环

---


### `_get_main_loop()`

线程安全地读取已注册的主事件循环

> **内部方法**
仅供 ``spawn_background`` 等内部调度使用。

**返回值** (`已注册的主事件循环，未注册时返回`): None

---


### `_track_owner_task(owner: str | None, task: Any)`

将任务登记到归属者索引

> **内部方法**

- **owner** (`资源归属者（模块名/适配器平台名），None`): 表示无归属
- **task** (`已调度的`): Task 或 Future

---


### `get_owner_tasks(owner: str | None)`

获取指定归属者名下未完成的后台任务集合

用于调试与泄漏可见性：模块/适配器卸载后若仍有存活任务，
可通过此接口检查（正常情况下框架已在卸载时兜底取消）。

- **owner** (`资源归属者（模块名/适配器平台名），None`): 表示无归属任务
**返回值**: 未完成任务集合的浅拷贝

---


### `async cancel_owner_tasks(owner: str | None)`

取消并等待指定归属者的全部后台任务

模块卸载 / 适配器关闭时由框架调用，兜底清理模块在 ``on_unload``
中未自行取消的任务，防止任务持有实例引用导致模块无法被回收
（热重载泄漏的常见根因）。

- **owner** (`资源归属者（模块名/适配器平台名）`): - **timeout**: 等待任务回收的超时秒数，超时后不再阻塞
**返回值**: 发起取消的任务数

---


### `async cancel_all_background_tasks()`

取消并等待全部后台任务

供 ``sdk.uninit()`` 在清理阶段兜底调用，确保框架退出时没有
悬挂的 fire-and-forget 任务（如 message.sending 钩子、异步
生命周期处理器调度等）。

- **timeout** (`等待任务回收的超时秒数`): **返回值**: 发起取消的任务数

---


### `spawn_background(coro: Awaitable[_T] | Coroutine[_T, Any, Any])`

调度一个 fire-and-forget 后台任务

优先在当前线程的事件循环中调度；如果当前线程没有运行中的事件循环
（如配置监听后台线程），则优先调度回主事件循环（若已注册且正在运行），
否则创建一个临时事件循环同步执行，确保协程在任何情况下都会被运行。

任务会自动归属到当前 ``owner_scope`` 上下文（模块名/适配器平台名），
卸载/关闭时框架按归属兜底取消；也可通过 ``owner`` 参数显式指定。

内部将协程包装为 :class:`asyncio.Task`，并把引用保留到模块级集合中，
直到任务结束自动清理。避免直接调用 ``loop.create_task`` / ``asyncio.ensure_future``
后由于引用丢失被 GC 提前回收（``RUF006`` 警告对应的真实风险）。

- **coro** (`待执行的协程或可等待对象`): - **owner**: 显式指定资源归属者；缺省时从当前 owner 上下文捕获
**返回值** (`创建出的`): :class:`asyncio.Task` / 调度回主循环的
         :class:`concurrent.futures.Future`，调用方可忽略返回值；
         在临时事件循环中同步执行时返回 ``None``

**示例**:
```python
>>> spawn_background(some_async_work())
```

---

