# `ErisPulse.Core.Event.base` 模块

---

## 模块概述


ErisPulse 事件处理基础模块

提供事件处理的核心功能，包括事件注册和处理

> **提示**
> 1. 所有事件处理都基于OneBot12标准事件格式
> 2. 通过适配器系统进行事件分发和接收

---

## 函数列表


### `async async _invoke_handler(handler_info: dict, event: Event)`

> **内部方法** 
执行单个事件处理器

:param handler_info: 处理器信息字典
:param event: 事件对象

---


## 类列表


### `class BaseEventHandler`

基础事件处理器

提供事件处理的基本功能，包括处理器注册和注销

内部维护与适配器事件总线的连接状态（_linked_to_adapter_bus），
确保 _process_event 在适配器总线被清空（如 shutdown/restart）后能重新挂载。


#### 方法列表


##### `__init__(event_type: str, module_name: str = None)`

初始化事件处理器

:param event_type: 事件类型
:param module_name: 模块名称

---


##### `register(handler: Callable, priority: int = 0, condition: Callable = None)`

注册事件处理器

:param handler: 事件处理器函数
:param priority: 处理器优先级，数值越小优先级越高
:param condition: 处理器条件函数，返回True时才会执行处理器

---


##### `unregister(handler: Callable)`

注销事件处理器

:param handler: 要注销的事件处理器
:return: 是否成功注销

---


##### `__call__(priority: int = 0, condition: Callable = None)`

装饰器方式注册事件处理器

:param priority: 处理器优先级
:param condition: 处理器条件函数
:return: 装饰器函数

---


##### `async async _process_event(event: dict[str, Any])`

处理事件

> **内部方法** 
同优先级处理器并行执行，不同优先级按顺序串行执行。
同优先级处理器的修改冲突采用后者覆盖前者的策略。

:param event: 事件数据

---


##### `_clear_handlers()`

> **内部方法** 
清除所有已注册的事件处理器，并断开与适配器事件总线的连接

断开连接后，下次调用 register() 时会自动重新挂载 _process_event 到适配器总线，
以适配 shutdown/restart 等场景下适配器总线被清空的情况。

:return: 被清除的处理器数量

---

