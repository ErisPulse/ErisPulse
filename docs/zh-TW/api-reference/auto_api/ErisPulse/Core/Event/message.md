# `ErisPulse.Core.Event.message` 模块

---

## 模块概述


ErisPulse 消息处理模块

提供基于装饰器的消息事件处理功能

> **提示**
> 1. 支持私聊、群聊消息分类处理
> 2. 支持@消息特殊处理
> 3. 支持自定义条件过滤
> 4. 支持 pattern（glob 通配符）/ regex（正则）文本匹配过滤

---

## 函数列表


### `_combine_conditions()`

> **内部方法**
组合多个条件函数为"全部满足"；过滤掉 None

---


## 类列表


### `class MessageHandler`

消息事件处理器

提供不同类型消息事件的处理功能


#### 方法列表


##### `on_message(priority: int = 0, pattern: str | None = None, regex: str | None = None)`

消息事件装饰器

- **priority** (`处理器优先级`): - **pattern**: glob 通配符（``*`` / ``?`` / ``[seq]``），消息文本须匹配才触发
- **regex** (`正则表达式，消息文本须匹配（search）才触发；与`): pattern 同时给定时须都匹配
**返回值**: 装饰器函数

---


##### `unregister(handler: Callable)`

取消注册的事件处理器

- **handler** (`要取消注册的处理器`): **返回值**: 是否成功取消注册

---


##### `remove_message_handler(handler: Callable)`

取消注册消息事件处理器

- **handler** (`要取消注册的处理器`): **返回值**: 是否成功取消注册

---


##### `on_private_message(priority: int = 0, pattern: str | None = None, regex: str | None = None)`

私聊消息事件装饰器

- **priority** (`处理器优先级`): - **pattern**: glob 通配符（``*`` / ``?`` / ``[seq]``），消息文本须匹配才触发
- **regex** (`正则表达式，消息文本须匹配（search）才触发；与`): pattern 同时给定时须都匹配
**返回值**: 装饰器函数

---


##### `remove_private_message_handler(handler: Callable)`

取消注册私聊消息事件处理器

- **handler** (`要取消注册的处理器`): **返回值**: 是否成功取消注册

---


##### `on_group_message(priority: int = 0, pattern: str | None = None, regex: str | None = None)`

群聊消息事件装饰器

- **priority** (`处理器优先级`): - **pattern**: glob 通配符（``*`` / ``?`` / ``[seq]``），消息文本须匹配才触发
- **regex** (`正则表达式，消息文本须匹配（search）才触发；与`): pattern 同时给定时须都匹配
**返回值**: 装饰器函数

---


##### `remove_group_message_handler(handler: Callable)`

取消注册群聊消息事件处理器

- **handler** (`要取消注册的处理器`): **返回值**: 是否成功取消注册

---


##### `on_at_message(priority: int = 0, pattern: str | None = None, regex: str | None = None)`

@消息事件装饰器

- **priority** (`处理器优先级`): - **pattern**: glob 通配符（``*`` / ``?`` / ``[seq]``），消息文本须匹配才触发
- **regex** (`正则表达式，消息文本须匹配（search）才触发；与`): pattern 同时给定时须都匹配
**返回值**: 装饰器函数

---


##### `remove_at_message_handler(handler: Callable)`

取消注册@消息事件处理器

- **handler** (`要取消注册的处理器`): **返回值**: 是否成功取消注册

---


##### `_clear_message_handlers()`

> **内部方法**
清除所有已注册的消息处理器

**返回值**: 被清除的处理器数量

---

