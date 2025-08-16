# `ErisPulse.Core.Event.meta` 模块

<sup>更新时间: 2025-08-17 03:30:27</sup>

---

## 模块概述


ErisPulse 元事件处理模块

提供基于装饰器的元事件处理功能

---

## 类列表

### `class MetaHandler`

元事件处理器

提供元事件（如连接、断开连接、心跳等）的处理功能


#### 方法列表

##### `__init__()`

初始化元事件处理器

---

##### `on_meta(priority: int = 0)`

通用元事件装饰器

:param priority: 处理器优先级
:return: 装饰器函数

---

##### `on_connect(priority: int = 0)`

连接事件装饰器

:param priority: 处理器优先级
:return: 装饰器函数

---

##### `on_disconnect(priority: int = 0)`

断开连接事件装饰器

:param priority: 处理器优先级
:return: 装饰器函数

---

##### `on_heartbeat(priority: int = 0)`

心跳事件装饰器

:param priority: 处理器优先级
:return: 装饰器函数

---

<sub>文档最后更新于 2025-08-17 03:30:27</sub>