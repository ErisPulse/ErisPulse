# `ErisPulse.runtime.context` 模块

---

## 模块概述


ErisPulse 运行时上下文

提供 contextvars 基础设施，用于追踪事件处理器、路由等资源的归属者。
在模块/适配器加载期间设置当前 owner，使资源注册能自动标记来源，
从而支持按模块精确清理（热禁用、热重载）。

> **提示**
> 使用方式::
> from ErisPulse.runtime.context import current_owner
> # 模块加载时
> token = current_owner.set("Dashboard")
> try:
> # ... 模块 __init__ / on_load 执行期间，注册的 handler 会自动打上 owner="Dashboard"
> pass
> finally:
> current_owner.reset(token)
> # handler 注册时读取
> owner = current_owner.get()  # 返回 "Dashboard" 或 None

---
