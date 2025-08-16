# `ErisPulse.Core.Event.base` 模块

<sup>更新时间: 2025-08-17 04:11:37</sup>

---

## 模块概述


ErisPulse 事件处理基础模块

提供事件处理的核心功能，包括事件注册、处理和中间件支持

---

## 类列表

### `class BaseEventHandler`

基础事件处理器

提供事件处理的基本功能，包括处理器注册、中间件支持等


#### 方法列表

##### `__init__(event_type: str, module_name: str = None)`

初始化事件处理器

:param event_type: 事件类型
:param module_name: 模块名称

---

##### `middleware(func: Callable)`

添加中间件

:param func: 中间件函数
:return: 中间件函数

---

##### `register(handler: Callable, priority: int = 0, condition: Callable = None)`

注册事件处理器

:param handler: 事件处理器函数
:param priority: 处理器优先级，数值越小优先级越高
:param condition: 处理器条件函数，返回True时才会执行处理器

---

##### `__call__(priority: int = 0, condition: Callable = None)`

装饰器方式注册事件处理器

:param priority: 处理器优先级
:param condition: 处理器条件函数
:return: 装饰器函数

---

##### async `async _process_event(event: Dict[str, Any])`

处理事件

<div class='admonition warning'><p class='admonition-title'>内部方法</p><p></p></div>
内部使用的方法，用于处理事件

:param event: 事件数据

---

##### `unregister(handler: Callable)`

注销事件处理器

:param handler: 要注销的事件处理器

---

<sub>文档最后更新于 2025-08-17 04:11:37</sub>