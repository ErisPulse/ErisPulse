# ErisPulse 开发者指南
本文档将介绍如何开发一个 ErisPulse 模块，另外你可以参考 `examples` 目录下的模块包

---

## 一、模块开发

### 1. 目录结构

一个标准模块包应该是：

```
MyModule/
├── pyproject.toml    # 项目配置
├── README.md         # 项目说明
├── LICENSE           # 许可证文件
└── MyModule/
    ├── __init__.py  # 模块入口
    └── Core.py      # 核心逻辑
```

### 2. `pyproject.toml` 文件
模块的配置文件, 包括模块信息、依赖项、模块/适配器入口点等信息

```toml
[project]
name = "ErisPulse-MyModule"     # 模块名称, 建议使用 ErisPulse-<模块名称> 的格式命名
version = "1.0.0"
description = "一个非常哇塞的模块"
readme = "README.md"
requires-python = ">=3.9"
license = { file = "LICENSE" }
authors = [ { name = "yourname", email = "your@mail.com" } ]
dependencies = [
    
]

[project.urls]
"homepage" = "https://github.com/yourname/MyModule"

[project.entry-points]
"erispulse.module" = { "MyModule" = "MyModule:Main" }

```

### 3. `MyModule/__init__.py` 文件

顾名思义,这只是使你的模块变成一个Python包, 你可以在这里导入模块核心逻辑, 当然也可以让他保持空白

示例这里导入了模块核心逻辑

```python
from .Core import Main
```

---

### 3. `MyModule/Core.py` 文件

实现模块主类 `Main`, 其中 `sdk` 参数的传入在 `2.x.x`版本 中不再是必须的，但推荐传入

```python
# 这也是一种可选的获取 `sdk`对象 的方式
# from ErisPulse import sdk

class Main:
    def __init__(self, sdk):
        self.sdk = sdk
        self.logger = sdk.logger
        self.env = sdk.env
        self.util = sdk.util
        self.raiserr = sdk.raiserr

        self.logger.info("模块已加载")
        self.config = self._get_config()

    def _get_config(self):
        config = env.getConfig("MyModule")
        if not config:
            default_config = {
                "my_config_key": "default_value"
            }
            env.setConfig("MyModule", default_config)
            return default_config
        return config

    def print_hello(self):
        self.logger.info("Hello World!")

```

- 所有 SDK 提供的功能都可通过 `sdk` 对象访问。
```python
# 这时候在其它地方可以访问到该模块
from ErisPulse import sdk
sdk.MyModule.print_hello()

# 运行模块主程序（推荐使用CLI命令）
# epsdk run main.py --reload
```
### 4. `LICENSE` 文件
`LICENSE` 文件用于声明模块的版权信息, 示例模块的声明默认为 `MIT` 协议。

---

## 二、平台适配器开发（Adapter）

适配器用于对接不同平台的消息协议（如 Yunhu、OneBot 等），是框架与外部平台交互的核心组件。

### 1. 目录结构

```
MyAdapter/
├── pyproject.toml
├── README.md
├── LICENSE
└── MyAdapter/
    ├── __init__.py
    └── Core.py
```

### 2. `pyproject.toml` 文件
```toml
[project]
name = "ErisPulse-MyAdapter"
version = "1.0.0"
description = "MyAdapter是一个非常酷的平台，这个适配器可以帮你绽放更亮的光芒"
readme = "README.md"
requires-python = ">=3.9"
license = { file = "LICENSE" }
authors = [ { name = "yourname", email = "your@mail.com" } ]

dependencies = [
    
]

[project.urls]
"homepage" = "https://github.com/yourname/MyAdapter"

[project.entry-points]
"erispulse.adapter" = { "MyAdapter" = "MyAdapter:MyAdapter" }

```

### 3. `MyAdapter/__init__.py` 文件

顾名思义,这只是使你的模块变成一个Python包, 你可以在这里导入模块核心逻辑, 当然也可以让他保持空白

示例这里导入了模块核心逻辑

```python
from .Core import MyAdapter
```

### 4. `MyAdapter/Core.py`
实现适配器主类 `MyAdapter`，并提供适配器类继承 `BaseAdapter`, 实现嵌套类Send以实现例如 Send.To(type, id).Text("hello world") 的语法

```python
from ErisPulse import sdk
from ErisPulse.Core import BaseAdapter

class MyAdapter(BaseAdapter):
    def __init__(self):    # 适配器有显式的导入sdk对象, 所以不需导入sdk对象
        self.sdk = sdk
        self.env = self.sdk.env
        self.logger = self.sdk.logger
        
        self.logger.info("MyModule 初始化完成")
        self.config = self._get_config()

    def _get_config(self):
        # 加载配置方法，你需要在这里进行必要的配置加载逻辑
        config = self.env.getConfig("MyAdapter", {})

        if config is None:
            default_config = {...}
            # 这里默认配置会生成到用户的 config.toml 文件中
            self.env.setConfig("MyAdapter", default_config)
            return default_config
        return config
    class Send(BaseAdapter.Send):  # 继承BaseAdapter内置的Send类
        # 底层SendDSL中提供了To方法，用户调用的时候类会被定义 `self._target_type` 和 `self._target_id`/`self._target_to` 三个属性
        # 当你只需要一个接受的To时，例如 mail 的To只是一个邮箱，那么你可以使用 `self.To(email)`，这时只会有 `self._target_id`/`self._target_to` 两个属性被定义
        # 或者说你不需要用户的To，那么用户也可以直接使用 Send.Func(text) 的方式直接调用这里的方法
        
        # 可以重写Text方法提供平台特定实现
        def Text(self, text: str):
            return asyncio.create_task(
                self._adapter.call_api(
                    endpoint="/send",
                    content=text,
                    recvId=self._target_id,
                    recvType=self._target_type
                )
            )
            
        # 添加新的消息类型
        def Image(self, file: bytes):
            return asyncio.create_task(
                self._adapter.call_api(
                    endpoint="/send_image",
                    file=file,
                    recvId=self._target_id,
                    recvType=self._target_type
                )
            )

    # 这里的call_api方法需要被实现, 哪怕他是类似邮箱时一个轮询一个发送stmp无需请求api的实现
    # 因为这是必须继承的方法
    async def call_api(self, endpoint: str, **params):
        raise NotImplementedError()

    # 适配器设定了启动和停止的方法，用户可以直接通过 sdk.adapter.setup() 来启动所有适配器，
    # 当然在底层捕捉到adapter的错误时我们会尝试停止适配器再进行重启等操作
    # 启动方法，你需要在这里定义你的adapter启动时候的逻辑
    async def start(self):
        raise NotImplementedError()
    # 停止方法，你需要在这里进行必要的释放资源等逻辑
    async def shutdown(self):
        raise NotImplementedError()
```
### 接口规范说明

#### 必须实现的方法

| 方法 | 描述 |
|------|------|
| `call_api(endpoint: str, **params)` | 调用平台 API |
| `start()` | 启动适配器 |
| `shutdown()` | 关闭适配器资源 |

#### 可选实现的方法

| 方法 | 描述 |
|------|------|
| `on(event_type: str)` | 注册事件处理器 |
| `add_handler(event_type: str, func: Callable)/add_handler(func: Callable)` | 添加事件处理器 |
| `middleware(func: Callable)` | 添加中间件处理传入数据 |
| `emit(event_type: str, data: Any)` | 自定义事件分发逻辑 |

- 在适配器中如果需要向底层提交事件，请使用 `emit()` 方法。
- 这时用户可以通过 `on([事件类型])` 修饰器 或者 `add_handler()` 获取到你提交到adapter的事件。

> ⚠️ 注意：
> - 适配器类必须继承 `sdk.BaseAdapter`；
> - 必须实现 `call_api`, `start`, `shutdown` 方法 和 `Send`类并继承自 `super().Send`；
> - 推荐实现 `.Text(...)` 方法作为基础消息发送接口。
> - To中的接受者类型不允许例如 "private" 的格式，当然这是一个规范，但为了兼容性，请使用 "user" / "group" / other

### 4. DSL 风格消息接口（SendDSL）

每个适配器可定义一组链式调用风格的方法，例如：

```python
class Send((BaseAdapter.Send):
    def Text(self, text: str):
        return asyncio.create_task(
            self._adapter.call_api(...)
        )

    def Image(self, file: bytes):
        return asyncio.create_task(
            self._upload_file_and_call_api(...)
        )
```

调用方式如下：

```python
sdk.adapter.MyPlatform.Send.To("user", "U1001").Text("你好")
```

> 建议方法名首字母大写，保持命名统一。

---

## 三、开发建议

### 1. 使用异步编程模型
- **优先使用异步库**：如 `aiohttp`、`asyncpg` 等，避免阻塞主线程。
- **合理使用事件循环**：确保异步函数正确地被 `await` 或调度为任务（`create_task`）。

### 2. 异常处理与日志记录
- **统一异常处理机制**：结合 `raiserr` 注册自定义错误类型，提供清晰的错误信息。
- **详细的日志输出**：在关键路径上打印调试日志，便于问题排查。

### 3. 模块化与解耦设计
- **职责单一原则**：每个模块/类只做一件事，降低耦合度。
- **依赖注入**：通过构造函数传递依赖对象（如 `sdk`），提高可测试性。

### 4. 性能优化
- **缓存机制**：利用 `@sdk.util.cache` 缓存频繁调用的结果。
- **资源复用**：连接池、线程池等应尽量复用，避免重复创建销毁开销。

### 5. 安全与隐私
- **敏感数据保护**：避免将密钥、密码等硬编码在代码中，使用环境变量或配置中心。
- **输入验证**：对所有用户输入进行校验，防止注入攻击等安全问题。

