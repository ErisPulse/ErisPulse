# `ErisPulse.runtime.resource_track` 模块

---

## 模块概述


合作式资源登记（tracked resources）

任务工厂拦截是**无感层**：主循环（及装了工厂的后台循环）上任何
``asyncio.create_task`` 自动归属。但拦截有结构性盲区——非主循环上创建、
不经任务体系持有引用的资源（第三方连接池、asyncssh/aiohttp client 等
Loop-bound 对象）永远不会经过任务工厂。本模块提供**合作式精确层**：
模块把带 ``release()`` 方法的资源显式登记到归属面，owner 被
``ownership.reclaim`` 回收时无论资源存活于哪个事件循环都统一释放。

> **提示**
> 1. ``track(resource)`` 在当前 owner 上下文内登记资源（需实现 ``release()``，
> 同步或异步均可），返回解析出的 owner 名
> 2. 资源自身被关闭/复用时用 ``untrack(resource)`` 注销，避免重复释放
> 3. ``release_owner_tracked(owner)`` 由 ``ownership.reclaim_tasks`` 在回收链内
> 调用：逐个释放、单步异常隔离记日志、异步释放带超时保护
> 4. 登记即审计可见：``ownership.counts()`` 的 ``tracked`` 计数 / ``orphans()``
> 孤儿扫描自动覆盖本表

---

## 函数列表


### `_log_and_t(key: str, level: str = 'warning', **kwargs: Any) -> str`

**内部方法** 惰性取日志与翻译（运行时层避免顶层导入 Core 的循环依赖）

---


### `track(resource: Any, *, owner: str | None = None) -> str`

登记合作式资源：owner 被 reclaim 时自动调用 ``resource.release()``

供模块持有任务体系外的资源（第三方连接池 / Loop-bound client）时使用。
资源须实现 ``release()``（同步或异步；返回 awaitable 时释放链会等待其
完成，超时保护见 :data:`TRACKED_RELEASE_TIMEOUT_SECS`）。

owner 解析优先级：显式 ``owner=`` 参数 > ``current_caller`` >
``current_owner``（与 ``on_cleanup`` 一致）。

- **resource**: 带 ``release()`` 方法的资源对象
- **owner**: 目标归属者（模块名/平台名），缺省按上述优先级自动解析

**返回值** (`str`): 解析并登记的目标 owner

**异常**: `ValueError` - 无法确定目标 owner 或资源未实现 ``release()`` 时抛出

**示例**:

```python
# 模块 on_load 内持有 asyncssh 连接池（Loop-bound，拦截层够不着）：
self._pool = await asyncssh.create_pool(host)
track(self._pool)  # 卸载/重载时归属链自动释放，无需 on_unload 手收
```

---


### `untrack(resource: Any, owner: str | None = None) -> int`

注销合作式资源（自身已关闭 / 生命周期自行管理时调用）

- **resource**: 已登记的资源对象
- **owner**: 仅注销该 owner 名下的该资源；None 表示全部 owner

**返回值** (`int`): 实际注销的条目数

**示例**:

```python
# 资源被显式复用（如全局单例池跨重载存活）时脱离归属链：
untrack(self._pool)
```

---


### `get_owner_tracked(owner: str) -> list[Any]`

获取指定归属者名下已登记的资源列表（只读）

- **owner**: 资源归属者（模块名/适配器平台名）

**返回值**: 资源列表的浅拷贝（正常情况下框架已在回收链释放并清空）

---


### `async release_owner_tracked(owner: str) -> int`

释放并移除指定 owner 的全部登记资源（框架回收链内部调用）

按注册顺序逆序释放（后登记的先释放，模拟栈式收尾）；``release()``
返回 awaitable 时等待其完成（超时视同失败），单个资源异常被隔离、
仅记日志，不中断其余释放。

**内部方法**
由 ``ownership.reclaim_tasks`` 调用；重复调用同一 owner 时首次后即为
空操作。

- **owner**: 归属者（模块名/适配器平台名）

**返回值** (`int`): 成功释放的资源数

---


### `_log_release_failure(owner: str, resource: Any, *, error: Exception | None = None, timeout: bool = False) -> None`

记录资源释放失败（惰性导入框架日志/i18n，避免运行时层的循环依赖）

**内部方法**

---

