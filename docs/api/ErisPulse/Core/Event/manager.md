# `ErisPulse.Core.Event.manager` 模块

<sup>更新时间: 2025-08-17 03:30:27</sup>

---

## 模块概述


ErisPulse 事件管理器

提供全局事件管理功能，包括事件处理器创建、模块事件管理等

---

## 类列表

### `class EventManager`

事件管理器

管理所有事件处理器，提供全局事件处理功能


#### 方法列表

##### `__init__()`

初始化事件管理器

---

##### `create_event_handler(event_type: str, module_name: str = None)`

创建事件处理器

:param event_type: 事件类型
:param module_name: 模块名称
:return: 事件处理器实例

---

##### `get_event_handler(event_type: str)`

获取事件处理器

:param event_type: 事件类型
:return: 事件处理器实例，如果不存在则返回None

---

##### `register_module_event(module_name: str, event_type: str)`

注册模块事件

:param module_name: 模块名称
:param event_type: 事件类型

---

##### `middleware(func: Callable)`

添加全局中间件

:param func: 中间件函数
:return: 中间件函数

---

##### async `async emit(event_type: str, event_data: Dict[str, Any])`

触发事件

:param event_type: 事件类型
:param event_data: 事件数据

---

##### `get_module_events(module_name: str)`

获取模块注册的事件

:param module_name: 模块名称
:return: 事件类型列表

---

##### `cleanup_module_events(module_name: str)`

清理模块事件

:param module_name: 模块名称

---

<sub>文档最后更新于 2025-08-17 03:30:27</sub>