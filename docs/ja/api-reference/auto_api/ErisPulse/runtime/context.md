# `ErisPulse.runtime.context` 模块

---

## 模块概述


ErisPulse 运行时上下文

提供 contextvars 基础设施，用于追踪事件处理器、路由等资源的归属者。
在模块/适配器加载期间设置当前 owner，使资源注册能自动标记来源，
从而支持按模块精确清理（热禁用、热重载）。

> **提示**
> 使用方式::
> from ErisPulse.runtime.context import owner_scope, get_current_owner
> # 或通过 SDK：sdk.context.owner_scope(...) / sdk.context.get_current_owner()
> # 在指定 owner 上下文下执行代码块（自动复位）
> with owner_scope("Dashboard"):
> # 注册的 handler 会自动打上 owner="Dashboard"
> pass
> # 读取当前 owner
> owner = get_current_owner()  # 返回 "Dashboard" 或 None

---

## 函数列表


### `owner_scope(owner: str | None)`

在指定 owner 上下文下执行代码块（退出时自动复位 current_owner）

模块/适配器在非加载场景下注册资源（命令/事件处理器/路由/生命周期钩子）时，
可用本上下文管理器让资源自动归属到指定 owner，从而被作用域过滤与按 owner 清理识别。
比手写 ``token = current_owner.set(...); try/finally: reset`` 更简洁安全。

- **owner** (`资源归属者（模块名或适配器平台名），None`): 表示清除当前 owner

**示例**:
```python
>>> with owner_scope("MyModule"):
...     @command("hello")
...     async def hello(event): ...
```

---


### `get_current_owner()`

获取当前资源归属者（模块名或适配器平台名）

在事件处理器 / 命令 / 钩子执行期间，框架已注入对应模块或适配器的 owner，
可用于日志归因、权限判断等。

**返回值** (`当前`): owner，不在任何加载/执行上下文时返回 None

**示例**:
```python
>>> owner = get_current_owner()
```

---


### `get_current_caller()`

获取当前跨模块调用的调用方身份（模块名或适配器平台名）

经 ``sdk.module.call()`` 被调用期间，``current_owner`` 已归因到目标
模块（自己的代码归属自己），而调用方身份保留在本上下文中——被调方
可据此识别"谁在调用我"。直接属性访问（``sdk.Cron.once(...)``）不经
此上下文，此时调用方身份即 ``get_current_owner()``。

**返回值** (`调用方身份，非`): ``module.call`` 调用链或框架层调用时返回 None

**示例**:
```python
>>> caller = get_current_caller()  # "OrderModule" 或 None
```

---


### `get_handler_waits()`

获取当前 handler 的 wait_reply 调用记录（slow-log 归因用）

**返回值** (`记录列表或`): None（不在 handler / Task 上下文内）

---


### `get_current_trace_id()`

获取当前事件处理链路的追踪 ID（trace-id）

在事件分发 / handler 执行 / 出站发送期间可读取，用于跨模块日志关联；
不在事件处理上下文内（如后台定时任务）返回 None。

**返回值** (`当前`): trace-id 或 None

**示例**:
```python
>>> trace_id = get_current_trace_id()
```

---


### `get_send_receipts()`

获取当前消息事务的回执账本

仅在 ``Event.message_tx()`` 事务内返回非 None；
可用于查看本次事务已发送了哪些消息。

**返回值** (`回执记录列表或`): None（不在事务内）

**示例**:
```python
>>> receipts = get_send_receipts()
```

---

