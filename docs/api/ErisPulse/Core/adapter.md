# `ErisPulse/Core/adapter` 模块

ErisPulse 适配器系统

提供平台适配器基类、消息发送DSL和适配器管理功能。支持多平台消息处理、事件驱动和生命周期管理。

> **提示**：
1. 适配器必须继承BaseAdapter并实现必要方法
2. 使用SendDSL实现链式调用风格的消息发送接口
3. 适配器管理器支持多平台适配器的注册和生命周期管理
4. 支持OneBot12协议的事件处理

## 类

### `SendDSLBase`

消息发送DSL基类

用于实现 Send.To(...).Func(...) 风格的链式调用接口

> **提示**：
1. 子类应实现具体的消息发送方法(如Text, Image等)
2. 通过__getattr__实现动态方法调用


#### 方法

##### `__init__`

初始化DSL发送器

:param adapter: 所属适配器实例
:param target_type: 目标类型(可选)
:param target_id: 目标ID(可选)


##### `To`

设置消息目标

:param target_type: 目标类型(可选)
:param target_id: 目标ID(可选)
:return: SendDSL实例

:example:
>>> adapter.Send.To("user", "123").Text("Hello")
>>> adapter.Send.To("123").Text("Hello")  # 简化形式


### `BaseAdapter`

适配器基类

提供与外部平台交互的标准接口，子类必须实现必要方法

> **提示**：
1. 必须实现call_api, start和shutdown方法
2. 可以自定义Send类实现平台特定的消息发送逻辑
3. 通过on装饰器注册事件处理器
4. 支持OneBot12协议的事件处理


#### 方法

##### `__init__`

初始化适配器


##### `on`

适配器事件监听装饰器

:param event_type: 事件类型
:param onebot12: 是否监听OneBot12协议事件
:return: 装饰器函数

:example:
>>> @adapter.on("message")
>>> async def handle_message(data):
>>>     print(f"收到消息: {data}")


##### `middleware`

添加中间件处理器

:param func: 中间件函数
:return: 中间件函数

:example:
>>> @adapter.middleware
>>> async def log_middleware(data):
>>>     print(f"处理数据: {data}")
>>>     return data


##### `call_api`

调用平台API的抽象方法

:param endpoint: API端点
:param params: API参数
:return: API调用结果

:raises NotImplementedError: 必须由子类实现


##### `start`

启动适配器的抽象方法

:raises NotImplementedError: 必须由子类实现


##### `shutdown`

关闭适配器的抽象方法

:raises NotImplementedError: 必须由子类实现


##### `add_handler`

添加事件处理器

:param args: 参数列表
    - 1个参数: 处理器函数(监听所有事件)
    - 2个参数: 事件类型和处理器函数
    
:raises TypeError: 当参数数量无效时抛出
    
:example:
>>> # 监听所有事件
>>> adapter.add_handler(handle_all_events)
>>> # 监听特定事件
>>> adapter.add_handler("message", handle_message)


##### `emit`

触发原生协议事件

:param event_type: 事件类型
:param data: 事件数据

:example:
>>> await adapter.emit("message", {"text": "Hello"})


##### `emit_onebot12`

提交OneBot12协议事件

:param event_type: OneBot12事件类型
:param onebot_data: 符合OneBot12标准的事件数据

:example:
>>> await adapter.emit_onebot12("message", {
>>>     "id": "123",
>>>     "time": 1620000000,
>>>     "type": "message",
>>>     "detail_type": "private",
>>>     "message": [{"type": "text", "data": {"text": "Hello"}}]
>>> })


##### `send`

发送消息的便捷方法

:param target_type: 目标类型
:param target_id: 目标ID
:param message: 消息内容
:param kwargs: 其他参数
    - method: 发送方法名(默认为"Text")
:return: 发送结果

:raises AttributeError: 当发送方法不存在时抛出
    
:example:
>>> await adapter.send("user", "123", "Hello")
>>> await adapter.send("group", "456", "Hello", method="Markdown")


### `AdapterManager`

适配器管理器

管理多个平台适配器的注册、启动和关闭

> **提示**：
1. 通过register方法注册适配器
2. 通过startup方法启动适配器
3. 通过shutdown方法关闭所有适配器
4. 通过on装饰器注册OneBot12协议事件处理器


#### 方法

##### `Adapter`

获取BaseAdapter类，用于访问原始事件监听

:return: BaseAdapter类

:example:
>>> @sdk.adapter.Adapter.on("raw_event")
>>> async def handle_raw(data):
>>>     print("收到原始事件:", data)


##### `on`

OneBot12协议事件监听装饰器

:param event_type: OneBot12事件类型
:return: 装饰器函数

:example:
>>> @sdk.adapter.on("message")
>>> async def handle_message(data):
>>>     print(f"收到OneBot12消息: {data}")


##### `middleware`

添加OneBot12中间件处理器

:param func: 中间件函数
:return: 中间件函数

:example:
>>> @sdk.adapter.middleware
>>> async def onebot_middleware(data):
>>>     print("处理OneBot12数据:", data)
>>>     return data


##### `emit`

提交OneBot12协议事件到指定平台

:param platform: 平台名称
:param event_type: OneBot12事件类型
:param data: 符合OneBot12标准的事件数据

:raises ValueError: 当平台未注册时抛出
    
:example:
>>> await sdk.adapter.emit("MyPlatform", "message", {
>>>     "id": "123",
>>>     "time": 1620000000,
>>>     "type": "message",
>>>     "detail_type": "private",
>>>     "message": [{"type": "text", "data": {"text": "Hello"}}]
>>> })


##### `register`

注册新的适配器类

:param platform: 平台名称
:param adapter_class: 适配器类
:return: 注册是否成功

:raises TypeError: 当适配器类无效时抛出
    
:example:
>>> adapter.register("MyPlatform", MyPlatformAdapter)


##### `startup`

启动指定的适配器

:param platforms: 要启动的平台列表，None表示所有平台

:raises ValueError: 当平台未注册时抛出
    
:example:
>>> # 启动所有适配器
>>> await adapter.startup()
>>> # 启动指定适配器
>>> await adapter.startup(["Platform1", "Platform2"])


##### `shutdown`

关闭所有适配器

:example:
>>> await adapter.shutdown()


##### `get`

获取指定平台的适配器实例

:param platform: 平台名称
:return: 适配器实例或None
    
:example:
>>> adapter = adapter.get("MyPlatform")


##### `__getattr__`

通过属性访问获取适配器实例

:param platform: 平台名称
:return: 适配器实例

:raises AttributeError: 当平台未注册时抛出
    
:example:
>>> adapter = adapter.MyPlatform


##### `platforms`

获取所有已注册的平台列表

:return: 平台名称列表
    
:example:
>>> print("已注册平台:", adapter.platforms)

