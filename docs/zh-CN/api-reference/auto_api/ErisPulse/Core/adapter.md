# `ErisPulse.Core.adapter` 模块

---

## 模块概述


ErisPulse 适配器系统

提供平台适配器管理功能。支持多平台消息处理、事件驱动和生命周期管理。

---

## 类列表


### `class AdapterManager(ManagerBase)`

适配器管理器

管理多个平台适配器的注册、启动和关闭，提供与模块管理器一致的接口

> **提示**
> 1. 通过register方法注册适配器
> 2. 通过startup方法启动适配器
> 3. 通过shutdown方法关闭所有适配器
> 4. 通过on装饰器注册OneBot12协议事件处理器


#### 方法列表


##### `set_sdk_ref(sdk)`

设置 SDK 引用

:param sdk: SDK 实例
:return: 是否设置成功

---


##### `register(platform: str, adapter_class: type[BaseAdapter], adapter_info: dict | None = None)`

注册新的适配器类（标准化注册方法）

:param platform: 平台名称
:param adapter_class: 适配器类
:param adapter_info: 适配器信息
:return: 注册是否成功

**异常**: `TypeError` - 当适配器类无效时抛出

**示例**:
```python
>>> adapter.register("MyPlatform", MyPlatformAdapter)
```

---


##### `async async startup(platforms: str | list[str] | None = None)`

启动指定的适配器

:param platforms: 要启动的平台，可以是单个平台名、平台名列表或None（表示所有平台）
**异常**: `ValueError` - 当平台未注册时抛出

**示例**:
```python
>>> # 启动所有适配器
>>> await adapter.startup()
>>> # 启动单个适配器
>>> await adapter.startup("Platform1")
>>> # 启动多个适配器
>>> await adapter.startup(["Platform1", "Platform2"])
```

---


##### `async async _run_adapter(adapter: BaseAdapter, platform: str)`

> **内部方法** 
运行适配器实例

:param adapter: 适配器实例
:param platform: 平台名称

---


##### `async async shutdown(platforms: str | list[str] | None = None)`

关闭指定的适配器

:param platforms: 要关闭的平台，可以是单个平台名、平台名列表或None（表示所有平台）
**异常**: `ValueError` - 当平台未注册时抛出

**示例**:
```python
>>> # 关闭所有适配器
>>> await adapter.shutdown()
>>> # 关闭单个适配器
>>> await adapter.shutdown("Platform1")
>>> # 关闭多个适配器
>>> await adapter.shutdown(["Platform1", "Platform2"])
```

---


##### `clear()`

清除所有适配器实例和信息

> **内部方法** 
此方法用于反初始化时完全重置适配器管理器状态

---


##### `_config_register(platform: str, enabled: bool = False)`

注册新平台适配器（仅当平台不存在时注册）

:param platform: 平台名称
- **enabled** (`bool`): 是否启用适配器
**返回值** (`bool`): 操作是否成功

---


##### `exists(platform: str)`

检查平台是否存在

:param platform: 平台名称
**返回值** (`bool`): 平台是否存在

---


##### `is_enabled(platform: str)`

检查平台适配器是否启用

:param platform: 平台名称
**返回值** (`bool`): 平台适配器是否启用

---


##### `enable(platform: str)`

启用平台适配器

:param platform: 平台名称
**返回值** (`bool`): 操作是否成功

---


##### `disable(platform: str)`

禁用平台适配器

:param platform: 平台名称
**返回值** (`bool`): 操作是否成功

---


##### `unregister(platform: str)`

取消注册适配器

:param platform: 平台名称
:return: 是否取消成功

> **内部方法** 
注意：此方法仅取消注册，不关闭已启动的适配器

---


##### `list_registered()`

列出所有已注册的平台

:return: 平台名称列表

---


##### `list_items()`

列出所有平台适配器状态

:return: {平台名: 是否启用} 字典

---


##### `list_adapters()`

列出所有平台适配器状态

> **已弃用** 请使用 list_items() 代替

**返回值** (`dict[str, bool`): ] 平台适配器状态字典

---


##### `on(event_type: str = '*')`

OneBot12协议事件监听装饰器

:param event_type: OneBot12事件类型
:param raw: 是否监听原生事件
:param platform: 指定平台，None表示监听所有平台
:return: 装饰器函数

**示例**:
```python
>>> # 监听OneBot12标准事件（所有平台）
>>> @sdk.adapter.on("message")
>>> async def handle_message(data):
>>>     print(f"收到OneBot12消息: {data}")
>>>
>>> # 监听特定平台的OneBot12标准事件
>>> @sdk.adapter.on("message", platform="onebot11")
>>> async def handle_onebot11_message(data):
>>>     print(f"收到OneBot11标准消息: {data}")
>>>
>>> # 监听平台原生事件
>>> @sdk.adapter.on("message", raw=True, platform="onebot11")
>>> async def handle_raw_message(data):
>>>     print(f"收到OneBot11原生事件: {data}")
>>>
>>> # 监听所有平台的原生事件
>>> @sdk.adapter.on("message", raw=True)
>>> async def handle_all_raw_message(data):
>>>     print(f"收到原生事件: {data}")
```

---


##### `middleware(func: Callable)`

添加OneBot12中间件处理器

:param func: 中间件函数
:return: 中间件函数

**示例**:
```python
>>> @sdk.adapter.middleware
>>> async def onebot_middleware(data):
>>>     print("处理OneBot12数据:", data)
>>>     return data
```

---


##### `async async emit(data: Any)`

提交OneBot12协议事件到指定平台

:param data: 符合OneBot12标准的事件数据

**示例**:
```python
>>> await sdk.adapter.emit({
>>>     "id": "123",
>>>     "time": 1620000000,
>>>     "type": "message",
>>>     "detail_type": "private",
>>>     "message": [{"type": "text", "data": {"text": "Hello"}}],
>>>     "platform": "myplatform",
>>>     "myplatform_raw": {...平台原生事件数据...},
>>>     "myplatform_raw_type": "text_message"
>>> })
```

---


##### `_auto_register_bot(platform: str, self_info: dict)`

> **内部方法** 
自动注册Bot（从OB12事件self字段提取），提取所有扩展字段作为Bot元信息

self字段标准扩展：
- self.user_id (必须) - Bot用户ID
- self.user_name (可选) - Bot昵称
- self.avatar (可选) - Bot头像URL
- self.account_id (可选) - 多账户标识

:param platform: 平台名称
:param self_info: 事件中的self字段内容
:return: 是否为新注册的Bot

---


##### `_update_bot_status(platform: str, bot_id: str, status: str)`

> **内部方法** 
更新Bot状态

:param platform: 平台名称
:param bot_id: Bot用户ID
:param status: 状态值（online/offline）

---


##### `_update_bot_heartbeat(platform: str, self_info: dict)`

> **内部方法** 
更新Bot心跳（更新活跃时间和元信息）

:param platform: 平台名称
:param self_info: 事件中的self字段内容

---


##### `get_bot_info(platform: str, bot_id: str)`

获取Bot详细信息

:param platform: 平台名称
:param bot_id: Bot用户ID
:return: Bot信息字典，包含status/last_active/info，不存在则返回None

**示例**:
```python
>>> info = adapter.get_bot_info("telegram", "123456")
>>> # {"status": "online", "last_active": 1712345678.0, "info": {"nickname": "MyBot"}}
```

---


##### `list_bots(platform: str | None = None)`

列出Bot信息

:param platform: 平台名称，None表示列出所有平台的Bot
:return: Bot信息字典 {platform: {bot_id: {status, last_active, info}}}

**示例**:
```python
>>> # 列出所有Bot
>>> all_bots = adapter.list_bots()
>>> # 列出指定平台的Bot
>>> tg_bots = adapter.list_bots("telegram")
```

---


##### `is_bot_online(platform: str, bot_id: str)`

检查Bot是否在线

:param platform: 平台名称
:param bot_id: Bot用户ID
:return: Bot是否在线

**示例**:
```python
>>> if adapter.is_bot_online("telegram", "123456"):
...     print("Bot在线")
```

---


##### `get_status_summary()`

获取适配器与Bot的完整状态摘要

返回所有适配器的运行状态及各适配器下的Bot状态，便于WebUI展示。

:return: 状态摘要字典

**示例**:
```python
>>> summary = adapter.get_status_summary()
>>> # {
>>> #     "adapters": {
>>> #         "telegram": {
>>> #             "status": "started",
>>> #             "bots": {
>>> #                 "123456": {
>>> #                     "status": "online",
>>> #                     "last_active": 1712345678.0,
>>> #                     "info": {"nickname": "MyBot"}
>>> #                 }
>>> #             }
>>> #         }
>>> #     }
>>> # }
```

---


##### `get(platform: str)`

获取指定平台的适配器实例

:param platform: 平台名称
:return: 适配器实例或None

**示例**:
```python
>>> adapter = adapter.get("MyPlatform")
```

---


##### `is_running(platform: str)`

检查适配器是否正在运行（已启动）

:param platform: 平台名称
:return: 适配器是否正在运行

**示例**:
```python
>>> if adapter.is_running("onebot11"):
>>>     print("onebot11 适配器正在运行")
```

---


##### `list_running()`

列出所有正在运行的适配器（已启动）

:return: 平台名称列表

**示例**:
```python
>>> running = adapter.list_running()
>>> print("正在运行的适配器:", running)
```

---


##### `list_sends(platform: str)`

列出指定平台支持的发送方法

:param platform: 平台名称
:return: 发送方法名列表
**异常**: `ValueError` - 当平台不存在时抛出

**示例**:
```python
>>> methods = adapter.list_sends("onebot11")
>>> print(methods)  # ["Text", "Image", "Voice", ...]
```

---


##### `send_info(platform: str, method_name: str)`

获取指定发送方法的详细信息

:param platform: 平台名称
:param method_name: 发送方法名
:return: 方法信息字典，包含name, parameters, return_type, docstring
**异常**: `ValueError` - 当平台或方法不存在时抛出

**示例**:
```python
>>> info = adapter.send_info("onebot11", "Text")
>>> print(info)
# {
#     "name": "Text",
#     "parameters": [
#         {"name": "text", "type": "str", "default": null, "annotation": "str"}
#     ],
#     "return_type": "Awaitable[Any]",
#     "docstring": "发送文本消息..."
# }
```

---


##### `platforms()`

获取所有已注册的平台列表

:return: 平台名称列表

**示例**:
```python
>>> print("已注册平台:", adapter.platforms)
```

---


##### `__getattr__(platform: str)`

通过属性访问获取适配器实例

:param platform: 平台名称
:return: 适配器实例
**异常**: `AttributeError` - 当平台不存在或未启用时

---


##### `__contains__(platform: str)`

检查平台是否存在且处于启用状态

:param platform: 平台名称
**返回值** (`bool`): 平台是否存在且启用

---

