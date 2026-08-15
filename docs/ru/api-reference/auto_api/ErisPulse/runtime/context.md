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


### `get_handler_waits()`

获取当前 handler 的 wait_reply 调用记录（slow-log 归因用）

**返回值** (`记录列表或`): None（不在 handler / Task 上下文内）

---

