# `ErisPulse.Core.Event.request` 模块

---

## 模块概述


ErisPulse 请求处理模块

提供基于装饰器的请求事件处理功能

> **提示**
> 1. 支持好友请求、群邀请等不同类型请求
> 2. 在处理器中可通过 event.approve() 同意请求或 event.reject() 拒绝请求
> 3. 请求事件必须包含 request_id 字段才能执行操作

---

## 类列表


### `class RequestHandler`

请求事件处理器

提供请求事件处理功能


#### 方法列表


##### `on_request(priority: int = 0)`

通用请求事件装饰器

- **priority** (`处理器优先级`): **返回值**: 装饰器函数

---


##### `unregister(handler: Callable)`

取消注册的事件处理器

- **handler** (`要取消注册的处理器`): **返回值**: 是否成功取消注册

---


##### `remove_request_handler(handler: Callable)`

取消注册通用请求事件处理器

- **handler** (`要取消注册的处理器`): **返回值**: 是否成功取消注册

---


##### `on_friend_request(priority: int = 0)`

好友请求事件装饰器

- **priority** (`处理器优先级`): **返回值**: 装饰器函数

---


##### `remove_friend_request_handler(handler: Callable)`

取消注册好友请求事件处理器

- **handler** (`要取消注册的处理器`): **返回值**: 是否成功取消注册

---


##### `on_group_request(priority: int = 0)`

群邀请请求事件装饰器

- **priority** (`处理器优先级`): **返回值**: 装饰器函数

---


##### `remove_group_request_handler(handler: Callable)`

取消注册群邀请请求事件处理器

- **handler** (`要取消注册的处理器`): **返回值**: 是否成功取消注册

---


##### `_clear_request_handlers()`

> **内部方法**
清除所有已注册的请求处理器

**返回值**: 被清除的处理器数量

---

