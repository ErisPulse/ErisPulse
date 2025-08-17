# `ErisPulse.Core.Event.request` 模块

<sup>更新时间: 2025-08-17 09:01:35</sup>

---

## 模块概述


ErisPulse 请求处理模块

提供基于装饰器的请求事件处理功能

---

## 类列表

### `class RequestHandler`

请求处理器

提供不同类型请求事件的处理功能（如好友申请、群邀请等）


#### 方法列表

##### `__init__()`

初始化请求处理器

---

##### `on_request(priority: int = 0)`

通用请求事件装饰器

:param priority: 处理器优先级
:return: 装饰器函数

---

##### `on_friend_request(priority: int = 0)`

好友请求事件装饰器

:param priority: 处理器优先级
:return: 装饰器函数

---

##### `on_group_request(priority: int = 0)`

群邀请请求事件装饰器

:param priority: 处理器优先级
:return: 装饰器函数

---

<sub>文档最后更新于 2025-08-17 09:01:35</sub>