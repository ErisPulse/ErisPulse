# `ErisPulse.Core.Event.message` 模块

<sup>更新时间: 2025-08-17 09:01:35</sup>

---

## 模块概述


ErisPulse 消息处理模块

提供基于装饰器的消息事件处理功能

---

## 类列表

### `class MessageHandler`

消息处理器

提供不同类型消息事件的处理功能


#### 方法列表

##### `__init__()`

初始化消息处理器

---

##### `on_message(priority: int = 0)`

消息事件装饰器

:param priority: 处理器优先级
:return: 装饰器函数

---

##### `on_private_message(priority: int = 0)`

私聊消息事件装饰器

:param priority: 处理器优先级
:return: 装饰器函数

---

##### `on_group_message(priority: int = 0)`

群聊消息事件装饰器

:param priority: 处理器优先级
:return: 装饰器函数

---

##### `on_at_message(priority: int = 0)`

@消息事件装饰器

:param priority: 处理器优先级
:return: 装饰器函数

---

<sub>文档最后更新于 2025-08-17 09:01:35</sub>