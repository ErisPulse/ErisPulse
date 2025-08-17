# `ErisPulse.Core.Event.notice` 模块

<sup>更新时间: 2025-08-17 09:01:35</sup>

---

## 模块概述


ErisPulse 通知处理模块

提供基于装饰器的通知事件处理功能

---

## 类列表

### `class NoticeHandler`

通知处理器

提供不同类型通知事件的处理功能


#### 方法列表

##### `__init__()`

初始化通知处理器

---

##### `on_notice(priority: int = 0)`

通用通知事件装饰器

:param priority: 处理器优先级
:return: 装饰器函数

---

##### `on_friend_add(priority: int = 0)`

好友添加通知事件装饰器

:param priority: 处理器优先级
:return: 装饰器函数

---

##### `on_friend_remove(priority: int = 0)`

好友删除通知事件装饰器

:param priority: 处理器优先级
:return: 装饰器函数

---

##### `on_group_increase(priority: int = 0)`

群成员增加通知事件装饰器

:param priority: 处理器优先级
:return: 装饰器函数

---

##### `on_group_decrease(priority: int = 0)`

群成员减少通知事件装饰器

:param priority: 处理器优先级
:return: 装饰器函数

---

<sub>文档最后更新于 2025-08-17 09:01:35</sub>