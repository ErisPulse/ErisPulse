# `ErisPulse.Core.lifecycle` 模块

---

## 模块概述


ErisPulse 生命周期管理模块

提供统一的钩子/事件管理和触发机制，支持点式结构事件监听

> **提示**
> 1. 使用 @lifecycle.on("event.name") 注册事件处理器
> 2. 使用 await lifecycle.emit("event.name", data) 触发事件
> 3. 使用 lifecycle.start_timer() / stop_timer() 进行计时
> 4. 旧版 submit_event() API 保持兼容

---

## 函数列表


### `_get_logger()`

延迟导入 logger，避免循环依赖（lifecycle → logger → config → lifecycle）

---


## 类列表


### `class _NullLogger`

静默日志器，在 logger 模块尚未初始化时作为替代


### `class LifecycleManager`

生命周期管理器

统一的钩子/事件系统，支持：
- 点式结构事件监听（如 module.init 可被 module 监听到）
- 通配符监听（* 匹配所有事件）
- 优先级排序
- 同步/异步处理器
- 计时器

> **提示**
> 两种注册方式等价：
> >>> @lifecycle.on("module.load")
> ... async def on_load(data):
> ...     print(data)
> >>> lifecycle.register("module.load", on_load)
> 两种触发方式等价：
> >>> await lifecycle.emit("module.load", {"module_name": "Test"})
> >>> await lifecycle.submit_event("module.load", data={"module_name": "Test"})


#### 方法列表


##### `on(event: str)`

注册事件处理器（装饰器模式）

:param event: str 事件名称，支持点式结构和通配符
:param priority: int 优先级，数值越大越先执行 (默认: 0)
:return: Callable 装饰器

**异常**: `ValueError` - 当事件名无效时抛出

**示例**:
```python
>>> @lifecycle.on("module.load")
... async def on_module_load(data):
...     print(f"模块加载: {data}")
>>>
>>> @lifecycle.on("adapter.*")
... def on_adapter_event(data):
...     pass
```

---


##### `register(event: str, handler: Callable)`

注册事件处理器（函数调用模式）

:param event: str 事件名称
:param handler: Callable 处理函数
:param priority: int 优先级，数值越大越先执行 (默认: 0)

**示例**:
```python
>>> lifecycle.register("config.set", my_handler, priority=10)
```

---


##### `unregister(event: str, handler: Callable = None)`

取消注册事件处理器

:param event: str 事件名称
:param handler: Callable 指定取消的处理器，为 None 时取消该事件所有处理器

**示例**:
```python
>>> lifecycle.unregister("config.set", my_handler)  # 取消指定处理器
>>> lifecycle.unregister("config.set")               # 取消所有处理器
```

---


##### `async async emit(event: str, data: Any = None)`

触发事件（异步，精简版）

按优先级执行匹配的处理器。处理器返回非 None 值时，
该值将作为新的 data 传递给后续处理器。

:param event: str 事件名称
:param data: Any 事件数据
:return: Any 经过所有处理器处理后的数据

**示例**:
```python
>>> result = await lifecycle.emit("config.set", {"key": "test", "value": 42})
```

---


##### `emit_sync(event: str, data: Any = None)`

触发事件（同步，精简版）

同步执行所有处理器。异步处理器会在当前事件循环中以 create_task 调度。
注意：同步模式下异步处理器的返回值无法回传。

:param event: str 事件名称
:param data: Any 事件数据
:return: Any 处理后的数据

**示例**:
```python
>>> result = lifecycle.emit_sync("config.set", {"key": "test"})
```

---


##### `async async submit_event(event_type: str)`

提交生命周期事件（兼容旧版 API）

构建标准事件格式后通过 emit 触发，处理器接收标准事件字典。

:param event_type: str 事件名称
:param source: str 事件来源(默认"ErisPulse")
:param msg: str 事件描述
:param data: dict 事件相关数据
:param timestamp: float 时间戳(默认当前时间)

**示例**:
```python
>>> await lifecycle.submit_event("module.load", data={"module_name": "Test"})
```

---


##### `start_timer(timer_id: str)`

开始计时

:param timer_id: str 计时器ID

---


##### `get_duration(timer_id: str)`

获取指定计时器的持续时间

:param timer_id: str 计时器ID
:return: float 持续时间(秒)

---


##### `stop_timer(timer_id: str)`

停止计时并返回持续时间

:param timer_id: str 计时器ID
:return: float 持续时间(秒)

---


##### `async async _execute_handlers(hook_name: str, event: str, data: Any)`

执行匹配的事件处理器（异步）

:param hook_name: str 注册的钩子名
:param event: str 实际事件名
:param data: Any 事件数据
:return: Any 处理后的数据

---


##### `_execute_handlers_sync(hook_name: str, event: str, data: Any)`

执行匹配的事件处理器（同步）

:param hook_name: str 注册的钩子名
:param event: str 实际事件名
:param data: Any 事件数据
:return: Any 处理后的数据

---


##### `clear()`

清除所有已注册的处理器和计时器

**示例**:
```python
>>> lifecycle.clear()
```

---


##### `list_hooks()`

列出所有已注册的钩子及其处理器数量

:return: dict 钩子名称到处理器数量的映射

**示例**:
```python
>>> info = lifecycle.list_hooks()
>>> # {"module.load": 2, "adapter.start": 1}
```

---

