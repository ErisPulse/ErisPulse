# ErisPulse 方法与接口文档

本文件详细说明 ErisPulse 框架的主要方法、API 入口、模块接口规范及常用调用方式。

---

## 1. SDK 入口对象

ErisPulse 通过 `sdk` 对象暴露核心能力：

- `sdk` 实例具有伪指针特性，第三方模块可以通过重定义 `sdk.<Name>` 的方式重写底层模块。

```python
from ErisPulse import sdk

sdk.env         # 环境与配置管理
sdk.mods        # 模块管理器
sdk.util        # 工具函数和装饰器
sdk.logger      # 日志记录器
sdk.raiserr     # 内置错误管理器
sdk.adapter     # 平台适配器注册中心
sdk.BaseAdapter # 适配器基类
```

---

## 2. 主要方法说明

### 2.1 初始化方法

```python
sdk.init()
```

- **说明**：初始化并加载所有模块，所有模块会被加载到 `sdk` 实例中。
- **用法**：
    ```python
    from ErisPulse import sdk
    sdk.init()
    sdk.<ModuleName>.<ModuleFunc>
    ```

---

### 2.2 日志方法

通过 `sdk.logger` 记录日志：

```python
sdk.logger.debug(Msg)
sdk.logger.info(Msg)
sdk.logger.warning(Msg)
sdk.logger.error(Msg)
sdk.logger.critical(Msg)
```

- **说明**：`logger` 模块提供了基本而健全的日志系统，但显然它不是那么美观，你可以通过安装或自主重写 `logger` 模块来实现美观的日志系统。

---

### 2.3 环境与配置管理

```python
sdk.env.get(Key, [DefValue])
sdk.env.set(Key, Value)
sdk.env.delete(Key)
sdk.env.clear()
sdk.env.load_env_file()
```

- **说明**：用于读取、写入和管理全局配置。

---

### 2.4 模块状态管理

```python
sdk.env.set_module_status(ModuleName, True/False)
sdk.env.get_module_status(ModuleName)
```

- **说明**：启用/禁用模块，查询模块状态。

---

### 2.5 使用内置错误管理

通过 `sdk.raiserr` 注册或抛出错误：

```python
sdk.raiserr.register(ErrTypeName, [Doc], [BaseErrType])
sdk.raiserr.<ErrTypeName>(Msg, [isExit])
```

---

### 2.6 适配器注册与使用

通过 `sdk.adapter` 注册平台适配器：

```python
sdk.adapter.register(platform_name, adapter_class)
```

- **说明**：将指定的适配器类注册到对应平台名下，供后续使用。
- **参数说明**：
  - `platform_name`: 字符串，平台名称（如 `"wechat"`, `"discord"`）
  - `adapter_class`: 继承自 `BaseAdapter` 的类，需实现相应接口。

> **提示**：模块可通过实现 `register_adapters()` 方法返回适配器字典，框架将在初始化时自动注册。

#### 获取已注册适配器

```python
my_adapter_class = sdk.adapter.get("wechat")
adapter_instance = my_adapter_class(config)
```

---

### 2.7 BaseAdapter 接口规范

所有平台适配器必须继承自 BaseAdapter 并至少实现以下方法：

```python
from ErisPulse import sdk

class MyAdapter(sdk.BaseAdapter):
    def __init__(self, sdk):
        super().__init__()
        # 初始化配置等操作

    async def send(self, target, message, **kwargs):
        raise NotImplementedError()

    async def call_api(self, endpoint: str, **params):
        raise NotImplementedError()

    async def start(self):
        raise NotImplementedError()

    async def stop(self):
        raise NotImplementedError()
```

#### 必须实现的方法

- `__init__(self, sdk)`  
  - 初始化适配器，接收sdk实例。
- `async def send(self, target, message, **kwargs)`  
  - 发送消息到指定目标（如用户、群组等）。
  - 抛出 `NotImplementedError` 表示子类必须重写该方法。
- `async def call_api(self, endpoint: str, **params)`  
  - 调用平台 API 的统一接口。
- `async def start(self)`  
  - 启动适配器逻辑，例如连接 WebSocket 或启动监听线程。
- `async def stop(self)`  
  - 停止适配器运行，释放资源。

#### 可选重写的方法

- `async def emit(self, event_type: str, data: Any)` (inherited from `BaseAdapter`)  
  - 用于事件分发，可被覆盖以定制事件处理流程。
- `def middleware(self, func: Callable)`  
  - 添加中间件逻辑，用于在事件触发前进行预处理。

#### 附加功能说明

- `on(event_type: str)`  
  - 装饰器方法，用于注册特定事件类型的处理函数。
  - 示例：
    ```python
    @adapter.on("message")
    async def handle_message(data):
        await process(data)
    ```

- `middleware(func: Callable)`  
  - 注册中间件函数，用于对传入事件数据进行预处理。
  - 示例：
    ```python
    @adapter.middleware
    async def log_middleware(data):
        print("Received event:", data)
        return data
    ```

#### Send（DSL 风格发送接口）

所有平台适配器支持链式调用风格的 `Send.To(...).Func()` 接口，用于更语义化的消息发送。

##### 使用示例：
```python
adapter.QQ.Send.To("user", "U1001").Text(text="你好")
adapter.Yunhu.Send.To("group", "G8888").Image(file="http://example.com/image.jpg")

> **提示**：开发者可通过 `sdk.adapter.get(platform_name)` 获取已注册的适配器类，并通过实例化进行使用。

---

## 3. 模块接口规范（更新）

每个模块应实现如下接口结构，并可选提供适配器注册功能：

```python
# __init__.py
moduleInfo = {
    "meta": {...},
    "dependencies": {...}
}
from .Core import Main
```

```python
# Core.py
class Main:
    def __init__(self, sdk):
        self.sdk = sdk
        self.logger = sdk.logger
```

### 新增可选接口：适配器注册

```python
def register_adapters():
    return {
        "wechat": WeChatAdapter,
        "discord": DiscordAdapter
    }
```

- **说明**：若模块需要为特定平台提供适配逻辑，应返回一个字典，键为平台名称，值为继承自 `BaseAdapter` 的类。
- **自动加载机制**：框架在调用 `sdk.init()` 时会自动检测并注册这些适配器。
- **日志提示**：成功注册后，`sdk` 会记录类似 `"模块 my_module 注册了适配器: wechat"` 的信息。

---

> **提示**：开发者可通过 `sdk.adapter.get(platform_name)` 获取已注册的适配器类，并通过实例化进行使用。

---

> **更多详细开发接口与模块规范请参考 [开发指南](DEVELOPMENT.md)。**
