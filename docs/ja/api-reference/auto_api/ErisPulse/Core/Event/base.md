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


### `async _invoke_handler(handler_info: dict, event: Event)`

> **内部方法**
执行单个事件处理器

- **handler_info** (`处理器信息字典`): - **event**: 事件对象

---


## 类列表


### `class BaseEventHandler`

基础事件处理器

提供事件处理的基本功能，包括处理器注册和注销

内部维护与适配器事件总线的连接状态（_linked_to_adapter_bus），
确保 _process_event 在适配器总线被清空（如 shutdown/restart）后能重新挂载。


#### 方法列表


##### `__init__(event_type: str, module_name: str | None = None)`

初始化事件处理器

- **event_type** (`事件类型`): - **module_name**: 模块名称

---


##### `register(handler: Callable, priority: int = DEFAULT_HANDLER_PRIORITY, condition: Callable | None = None, scope_exempt: bool = False)`

注册事件处理器

- **handler** (`事件处理器函数`): - **priority**: 处理器优先级，数值越大优先级越高
- **condition** (`处理器条件函数，返回True时才会执行处理器`): - **scope_exempt**: 是否豁免作用域过滤（框架级处理器专用，默认 False）。
                     为 True 时不参与模块作用域判断，始终执行。

---


##### `unregister(handler: Callable)`

注销事件处理器

- **handler** (`要注销的事件处理器`): **返回值**: 是否成功注销

---


##### `unregister_by_owner(owner: str)`

> **内部方法**
按归属者精确移除事件处理器

- **owner** (`归属者（模块名）`): **返回值**: 移除的处理器数量

---


##### `__call__(priority: int = DEFAULT_HANDLER_PRIORITY, condition: Callable | None = None)`

装饰器方式注册事件处理器

- **priority** (`处理器优先级，数值越大优先级越高`): - **condition**: 处理器条件函数
**返回值**: 装饰器函数

---


##### `async _process_event(event: dict[str, Any])`

处理事件

> **内部方法**
同优先级处理器并行执行，不同优先级按顺序串行执行。
同优先级处理器的修改冲突采用后者覆盖前者的策略。

- **event**: 事件数据

---


##### `_is_scope_allowed(handler_info: dict, platform: str, bot_id: str, session_id: str)`

> **内部方法**
判断处理器是否通过模块作用域检查

框架级处理器（``scope_exempt`` 或 owner 为空）始终放行；
模块级处理器按 owner 与当前事件所属平台/Bot/会话判定。

- **handler_info** (`处理器信息字典`): - **platform**: 事件平台名称
- **bot_id** (`事件`): Bot 标识（可能为空字符串）
- **session_id** (`事件会话标识（群`): / 频道 / 私聊，可能为空字符串）
**返回值**: 是否允许执行

---


##### `_is_scope_handler_ok(handler_info: dict, event)`

> **内部方法**
判断处理器是否通过控制面文本过滤（scope.handlers.<module>）

框架级处理器（scope_exempt 或 owner 为空）始终放行；
模块级处理器按其 owner 在 ``scope.handlers`` 中配置的 pattern / regex
条件过滤（与代码内条件 AND，需同时满足）。

- **handler_info** (`处理器信息字典`): - **event**: 事件对象
**返回值**: 是否允许执行

---


##### `_clear_handlers()`

> **内部方法**
清除所有已注册的事件处理器，并断开与适配器事件总线的连接

断开连接后，下次调用 register() 时会自动重新挂载 _process_event 到适配器总线，
以适配 shutdown/restart 等场景下适配器总线被清空的情况。

**返回值**: 被清除的处理器数量

---

