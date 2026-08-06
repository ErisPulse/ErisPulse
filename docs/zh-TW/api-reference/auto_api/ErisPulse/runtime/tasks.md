# `ErisPulse.runtime.tasks` 模块

---

## 模块概述


后台任务管理工具

提供 fire-and-forget 模式的任务调度，避免被 GC 回收。

> **提示**
> 1. ``spawn_background(coro)`` 调度一个不关心返回值的协程
> 2. 内部使用模块级集合保留 Task 引用，任务完成后自动清理
> 3. 避免出现 ``RUF006`` 所警告的“asyncio 任务悬挂被 GC”问题

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


### `spawn_background(coro: Awaitable[_T] | Coroutine[_T, Any, Any])`

调度一个 fire-and-forget 后台任务

优先在当前线程的事件循环中调度；如果当前线程没有运行中的事件循环
（如配置监听后台线程），则优先调度回主事件循环（若已注册且正在运行），
否则创建一个临时事件循环同步执行，确保协程在任何情况下都会被运行。

内部将协程包装为 :class:`asyncio.Task`，并把引用保留到模块级集合中，
直到任务结束自动清理。避免直接调用 ``loop.create_task`` / ``asyncio.ensure_future``
后由于引用丢失被 GC 提前回收（``RUF006`` 警告对应的真实风险）。

- **coro** (`待执行的协程或可等待对象`): **返回值** (`创建出的`): :class:`asyncio.Task` / 调度回主循环的
         :class:`concurrent.futures.Future`，调用方可忽略返回值；
         在临时事件循环中同步执行时返回 ``None``

**示例**:
```python
>>> spawn_background(some_async_work())
```

---

