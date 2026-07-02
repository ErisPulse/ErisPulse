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


##### `async async _stop_adapter(platform: str)`

> **内部方法** 
停止单个平台适配器——shutdown 即清理。

将"停止适配器"与"回收其注册的资源"绑定在一次调用里：调用适配器自身的
``shutdown()`` 后立即清理该平台的路由/事件/命令。restart、启动失败重试等
场景均经此入口，保证适配器一旦停止、归属资源必被回收，无需调用方再补清理。

对未注册的平台直接返回；``shutdown()`` 与清理均幂等，半途失败的重试场景
也能正确回收 start() 期间已注册的资源。

:param platform: 平台名称

---


##### `_cleanup_adapter_resources(platform: str)`

> **内部方法** 
适配器资源兜底清理（与模块卸载对齐颗粒度）。

清理该平台在运行期间注册的所有路由、命令与事件处理器。同时覆盖两种注册方式：
- 直接以平台名为命名空间注册的路由（unregister_all_by_namespace）
- 适配器以平台名为 owner、用细颗粒度命名空间（如 onebot11_default）注册的路由
  （unregister_all_by_owner，依赖 start() 期间注入的 current_owner）

:param platform: 平台名称

---


##### `async async restart(platform: str)`

重启指定平台适配器（shutdown + 资源兜底清理 + start）

框架自动处理该平台在运行期间注册的路由/事件/命令清理（与模块卸载对齐颗粒度），
并在重启时注入 owner，使新注册的资源可被后续按 owner 清理。
第三方模块（如 Dashboard）的热重载应调用本方法，而非直接操作适配器实例。

:param platform: 平台名称
:return: 是否实际执行了重启（平台存在且原本在运行时为 True）

**示例**:
```python
>>> await sdk.adapter.restart("OneBot11")
```

---


##### `clear()`

清除所有适配器实例和信息

> **内部方法** 
此方法用于反初始化时完全重置适配器管理器状态

---


##### `_config_register(platform: str, enabled: bool = True)`

注册新平台适配器（仅当平台不存在时注册）

:param platform: 平台名称
- **enabled** (`bool`): 是否启用适配器 (默认: True，新适配器默认启用)
**返回值** (`bool`): 操作是否成功

---


##### `exists(platform: str)`

检查平台是否已注册

:param platform: 平台名称
:return: 平台是否已注册（即 adapter.register() 已被调用）

---


##### `is_enabled(platform: str)`

检查平台适配器是否启用

:param platform: 平台名称
:return: 平台适配器是否启用

> **提示**
> 适配器启用条件：
> 1. 适配器在配置文件中（ErisPulse.adapters.status.{platform} 存在）
> 2. 配置值为启用状态
> 如果适配器未在配置中，默认启用并自动写入配置

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
注意: 此方法仅取消注册, 不关闭已启动的适配器

---


##### `list_registered()`

列出所有已注册的平台

:return: 平台名称列表

---


##### `list_items()`

列出所有平台适配器状态

合并配置项与已注册适配器，确保禁用适配器也可见。

:return: {平台名: 是否启用} 字典

---


##### `list_adapters()`

兼容性方法 - 保持向后兼容

:return: {平台名: 是否启用} 字典

> **已弃用** 此方法已弃用，请使用 list_items() 代替

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

每个事件处理器（handler）都在独立的 asyncio.Task 中执行，
单个处理器阻塞不会影响框架的事件分发和其他处理器运行。

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


##### `_dispatch_handler_task(func: Callable, data: Any)`

> **内部方法** 
将事件处理器包装为独立 asyncio.Task 并调度执行

处理器在独立 Task 中运行，不会阻塞 adapter.emit() 的后续流程。
自动捕获处理器异常并记录日志，同时监控处理器执行耗时。

:param func: 事件处理器函数
:param data: 事件数据
:param event_type: 事件类型（用于日志）
:param platform: 平台名称（用于日志）
:return: asyncio.Task

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
包含已禁用适配器以便于管理。

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
>>> #         },
>>> #         "disabled_platform": {
>>> #             "status": "disabled",
>>> #             "enabled": False,
>>> #             "bots": {}
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


##### `get_connection_info(platform: str)`

获取适配器的连接信息（路由URL、状态等）

结合路由管理器的路由数据，返回指定平台适配器的完整连接信息，
包括 base_url、HTTP 路由、WebSocket 路由和 SSE 路由的完整 URL。

路由注册时的 ``module_name`` 必须与适配器的 ``platform`` 名称完全一致，
否则路由信息将无法被正确关联。

:param platform: 平台名称
:return: 连接信息字典，平台不存在时返回 None

**示例**:
```python
>>> info = sdk.adapter.get_connection_info("onebot11")
>>> # {
>>> #     "platform": "onebot11",
>>> #     "status": "started",
>>> #     "connection": {
>>> #         "base_url": "http://localhost:8080",
>>> #         "http_routes": [
>>> #             {"path": "/onebot11/webhook", "method": "POST",
>>> #              "url": "http://localhost:8080/onebot11/webhook"}
>>> #         ],
>>> #         "websocket_routes": [
>>> #             {"path": "/onebot11/ws",
>>> #              "url": "ws://localhost:8080/onebot11/ws"}
>>> #         ],
>>> #         "sse_routes": [
>>> #             {"path": "/onebot11/events",
>>> #              "url": "http://localhost:8080/onebot11/events"}
>>> #         ]
>>> #     }
>>> # }
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

