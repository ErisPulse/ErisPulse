# `ErisPulse.runtime.owner_cleanup` 模块

---

## 模块概述


归属清理钩子（owner cleanup hooks）

允许**框架外部**（工具模块 / 适配器）参与归属权清理链：工具模块替其它
模块托管资源时（如定时任务模块持有其回调、注册表类模块持有其条目），
可在对方注册资源的瞬间通过 ``on_cleanup`` 登记一个清理钩子；该模块被
卸载 / 禁用（或适配器关闭）时，框架在归属权清理链内统一触发钩子，
工具模块借此**抛弃内部持有的句柄**，让已卸载模块的实例可被正常回收。

> **提示**
> 1. ``on_cleanup(cb)`` 在当前 owner（模块/适配器）上下文内登记清理钩子，
> 卸载时框架回调 ``cb(owner)``
> 2. 回调支持同步 / 异步（异步回调带超时保护），异常被隔离、不影响其余清理
> 3. ``off_cleanup(cb)`` 供工具模块在自身 ``on_unload`` 中注销自己的钩子
> 4. 框架在模块 unload / disable 与适配器 shutdown 清理链内调用
> ``run_owner_cleanups(owner)`` 触发钩子（每步失败仅记日志，不中断清理）

---

## 函数列表


### `on_cleanup(callback: Callable[[str], Any])`

登记归属清理钩子：``owner`` 被卸载/禁用时由框架回调 ``callback(owner)``

供工具模块在替其它模块托管资源时使用——在对方注册资源的调用路径内
登记钩子，框架在该模块卸载链内触发回调，工具模块据此抛弃内部持有的
句柄，避免已卸载模块无法被 GC。

owner 解析优先级：显式 ``owner=`` 参数 > ``current_caller``（经
``module.call`` 被调用期间，owner 已归因到本模块，调用方身份在
caller 上下文）> ``current_owner``（对方 ``on_load`` 等直接调用场景）。

- **callback** (`清理回调，签名`): ``callback(owner: str)``，支持同步/异步
- **owner** (`目标归属者（模块名/平台名），缺省按上述优先级自动解析`): **返回值** (`str`): 解析并登记的目标 owner（可直接用作自有句柄的记名键）
**异常**: `ValueError` - 无法确定目标 owner 时抛出

**示例**:
```python
>>> # 工具模块（如定时任务）托管外部回调时按 owner 记名并登记钩子
>>> def register_handler(handler):
...     owner = on_cleanup(lambda o: _drop_owner_handlers(o))
...     _handlers.append((owner, handler))
```

---


### `off_cleanup(callback: Callable[[str], Any], owner: str | None = None)`

注销归属清理钩子

工具模块应在自身 ``on_unload`` 中调用 ``off_cleanup(cb)`` 注销自己
登记过的钩子，避免钩子表持有自身实例引用导致无法被回收。

- **callback** (`已登记的清理回调`): - **owner**: 仅注销该 owner 名下的钩子；None 表示注销该回调的全部
**返回值** (`int`): 实际注销的条目数

**示例**:
```python
>>> async def on_unload(self, event):
...     off_cleanup(self._owner_guard)  # 移除本模块登记的全部钩子
```

---


### `async run_owner_cleanups(owner: str)`

触发并移除指定 owner 的全部清理钩子（框架清理链内部调用）

依次执行钩子并从表中移除；异步回调带超时保护（超时视同失败），
单个回调异常被隔离、仅记日志，不中断其余钩子与清理链。

> **内部方法**
由模块卸载/禁用与适配器关闭的清理链调用；重复调用同一 owner 时
首次后即为空操作。

- **owner** (`归属者（模块名/适配器平台名）`): **返回值** (`int`): 成功执行的回调数

---


### `_log_failure(owner: str, callback: Callable[[str], Any])`

记录钩子执行失败（惰性导入框架日志/i18n，避免运行时层的循环依赖）

> **内部方法**

---

