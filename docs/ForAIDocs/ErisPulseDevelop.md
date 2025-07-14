# ErisPulse 开发文档合集

本文件由多个开发文档合并而成，用于辅助 AI 理解 ErisPulse 的模块开发规范与 SDK 使用方式。

## 各文件对应内容说明

| 文件名 | 作用 |
|--------|------|
| ADAPTERS.md | 平台适配器说明，包括事件监听和消息发送方式 |
| Conversion-Standard.md | 数据转换标准说明 |
| DEVELOPMENT.md | 模块结构定义、入口文件格式、Main 类规范 |
| UseCore.md | 核心功能使用说明 |
| API文档 | 自动生成的API参考文档 |

## 合并内容开始

<!-- UseCore.md -->

# ErisPulse 核心模块工作原理
本文档将介绍如何使用 ErisPulse 的核心模块以及如何使用它们

## 一、了解工作原理

### 核心对象

你可以通过 `from ErisPulse.Core import env, mods, logger, raiserr, util, adapter, BaseAdapter, EventDataBase` 直接获取核心模块对象

当然, 为了保持兼容性，你也可以通过 `sdk` 获取 SDK 对象，并使用 `sdk.<核心模块名>` 访问核心模块对象, 乃至使用三方模块重写SDK功能!

| 名称 | 用途 |
|------|------|
| `sdk` | SDK对象 |
| `env`/`sdk.env` | 获取/设置全局配置 |
| `mods`/`sdk.mods` | 模块管理器 |
| `logger`/`sdk.logger` | 日志记录器 |
| `raiserr`/`sdk.raiserr` | 错误管理器 |
| `util`/`sdk.util` | 工具函数（缓存、重试等） |
| `adapter`/`sdk.adapter` | 获取其他适配器实例 |
| `BaseAdapter`/`sdk.BaseAdapter` | 适配器基类 |
| `EventDataBase`/`sdk.EventDataBase` | 事件数据处理基类 |

### 模块调用

ErisPulse 框架提供了一个 `sdk` 对象, 所有模块都会被注册在 `sdk` 对象中

例如一个模块的结构是:
```python
# from ErisPulse import sdk
# from ErisPulse.Core import logger 

class MyModule:
    def __init__(self, sdk):    # 注: 这里也可以不传入 sdk 参数 | 你可以直接 from ErisPulse import sdk 来获得sdk对象
        self.sdk = sdk
        self.logger = sdk.logger

    def hello(self):
        self.logger.info("hello world")
        return "hello world"
```

这时候你可以在 `main.py` 中这样调用:
```python
from ErisPulse import sdk

sdk.init()

sdk.MyModule.hello()
```
这样就可以调用到模块中的方法了, 当然任何地方都可以调用模块中的方法, 只要它被加载到了 `sdk` 对象中

通过 `sdk.<ModuleName>` 访问其他模块实例：
```python
other_module = sdk.OtherModule
result = other_module.some_method()
```

---

适配器的使用: 
```python
from ErisPulse import sdk

async def main():
    sdk.init()

    await sdk.adapter.startup("MyAdapter")  # 这里不指定适配器名称的话, 会自动选择启动所有被注册到 `adapter`/`sdk.adapter` 中的适配器

    MyAdapter = sdk.adapter.get("MyAdapter")

    @MyAdapter.on("message")
    async def on_message(data):
        sdk.MyAdapterEvent(data)
        sender_type = sdk.MyAdapterEvent.sender_type()
        sender_id = sdk.MyAdapterEvent.sender_id()

    type, id = "Guild", "1234567890"
    await MyAdapter.Send.To(type, id).Text("Hello World!")  # 这里使用了DSL风格的调用, 在以后的章节中会详细介绍
```

通过 `sdk.adapter.<AdapterName>` 访问适配器实例：
```python
adapter = sdk.adapter.AdapterName
result = adapter.some_method()
```

## 二、核心对象功能示例

### 日志记录：

```python
from ErisPulse.Core import logger

#  设置单个模块日志级别
logger.set_module_level("MyModule", "DEBUG")

#  单次保持所有模块日志历史到文件
logger.save_logs("log.txt")

#  各等级日志
logger.debug("调试信息")
logger.info("运行状态")
logger.warning("警告信息")
logger.error("错误信息")
logger.critical("致命错误")    # 会触发程序崩溃
```

### env配置模块：

```python
from ErisPulse.Core import env

# 设置配置项
env.set("my_config_key", "new_value")

# 获取配置项
config_value = env.get("my_config_key", "default_value")

# 删除配置项
env.delete("my_config_key")

# 事务使用
with env.transaction():
    env.set('important_key', 'value')
    env.delete('temp_key')
    # 如果出现异常会自动回滚

# 获取模块配置
# 如果模块未注册，则返回None | 不支持设置默认值
env.getConfig("MyModule")
env.setConfig("MyModule", "MyConfig")

# 其它深入操作请阅读API文档
```

### 注册自定义错误类型：

```python
from ErisPulse.Core import raiserr

#  注册一个自定义错误类型
raiserr.register("MyCustomError", doc="这是一个自定义错误")

#  获取错误信息
error_info = raiserr.info("MyCustomError")
if error_info:
    print(f"错误类型: {error_info['type']}")
    print(f"文档描述: {error_info['doc']}")
    print(f"错误类: {error_info['class']}")
else:
    print("未找到该错误类型")

#  抛出一个自定义错误
raiserr.MyCustomError("发生了一个错误")

```

### 工具函数：

```python
from ErisPulse import util

# 工具函数装饰器：自动重试指定次数
@util.retry(max_attempts=3, delay=1)
async def my_retry_function():
    # 此函数会在异常时自动重试 3 次，每次间隔 1 秒
    ...

# 缓存装饰器：缓存函数调用结果（基于参数）
@util.cache
def get_expensive_result(param):
    # 第一次调用后，相同参数将直接返回缓存结果
    ...

# 异步执行装饰器：将同步函数放入线程池中异步执行
@util.run_in_executor
def sync_task():
    # 此函数将在独立线程中运行，避免阻塞事件循环
    ...

# 在同步函数中调用异步任务
util.ExecAsync(sync_task)

```

## 监听适配器事件以及使用适配器

你可以使用以下代码监听被转换为OneBot12的事件
（你可以参考 Adapter.md 文档获取更多信息）
```python
from ErisPulse import sdk
from ErisPulse.Core import adapter

@adapter.on("message")
async def on_message(data):
    # 处理消息, 几乎所有适配器都实现了 Text 发送方法，所有这里示例发送获取到的文本消息
    
    # 获取哪个平台
    platform = data.get("platform")
    detail_type = data.get("detail_type", "private")
    datail_id = data.get("user_id") if detail_type == "private" else data.get("group_id")

    echo_text = data.get("alt_message")

    # 获取适配器, 并且调用对应的发送方法
    if hasattr(adapter, platform):
        await getattr(adapter, platform).To("user" if detail_type == "private" else "group", datail_id).Text(echo_text)

```

> 更多使用请查看 [docs/api/](docs/api/) 目录

<!--- End of UseCore.md -->

<!-- DEVELOPMENT.md -->

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



<!--- End of DEVELOPMENT.md -->

<!-- ADAPTERS.md -->

# ErisPulse Adapter 文档

## 简介
ErisPulse 的 Adapter 系统旨在为不同的通信协议提供统一事件处理机制。目前支持的主要适配器包括：

- **TelegramAdapter**
- **OneBotAdapter**
- **YunhuAdapter**

每个适配器都实现了对于 OneBot12 协议的转换、消息发送方法和生命周期管理。以下将介绍使用时的事件内容以及一些适配器的拓展部分

OneBot12 协议标准：https://12.onebot.dev/
示例标准格式：

```json
{
  "id": "event_123",
  "time": 1752241220,
  "type": "message",
  "detail_type": "group",
  "platform": "yunhu",
  "self": {"platform": "yunhu", "user_id": "bot_123"},
  "message_id": "msg_abc",
  "message": [
    {
      "type": "text",
      "data": {"text": "你好"}
    }
  ],
  "alt_message": "你好",
  "user_id": "user_456",
  "group_id": "group_789"
}
```

---

## 适配器功能概述

### 1. YunhuAdapter
YunhuAdapter 是基于云湖协议构建的适配器，整合了所有云湖功能模块，提供统一的事件处理和消息操作接口。

#### 支持的消息发送类型
所有发送方法均通过链式语法实现，例如：
```python
await yunhu.Send.To("user", user_id).Text("Hello World!")
```

支持的发送类型包括：
- `.Text(text: str, buttons: List = None)`：发送纯文本消息，可选添加按钮。
- `.Html(html: str, buttons: List = None)`：发送HTML格式消息。
- `.Markdown(markdown: str, buttons: List = None)`：发送Markdown格式消息。
- `.Image(file: bytes, buttons: List = None)`：发送图片消息。
- `.Video(file: bytes, buttons: List = None)`：发送视频消息。
- `.File(file: bytes, buttons: List = None)`：发送文件消息。
- `.Batch(target_ids: List[str], message: str)`：批量发送消息。
- `.Edit(msg_id: str, text: str)`：编辑已有消息。
- `.Recall(msg_id: str)`：撤回消息。
- `.Board(board_type: str, content: str, **kwargs)`：发布公告看板。
- `.Stream(content_type: str, generator: AsyncGenerator)`：发送流式消息。

Borard board_type 支持以下类型：
- `local`：指定用户看板
- `global`：全局看板

#### 按钮参数说明
`buttons` 参数是一个嵌套列表，表示按钮的布局和功能。每个按钮对象包含以下字段：

| 字段         | 类型   | 是否必填 | 说明                                                                 |
|--------------|--------|----------|----------------------------------------------------------------------|
| `text`       | string | 是       | 按钮上的文字                                                         |
| `actionType` | int    | 是       | 动作类型：<br>`1`: 跳转 URL<br>`2`: 复制<br>`3`: 点击汇报            |
| `url`        | string | 否       | 当 `actionType=1` 时使用，表示跳转的目标 URL                         |
| `value`      | string | 否       | 当 `actionType=2` 时，该值会复制到剪贴板<br>当 `actionType=3` 时，该值会发送给订阅端 |

示例：
```python
buttons = [
    [
        {"text": "复制", "actionType": 2, "value": "xxxx"},
        {"text": "点击跳转", "actionType": 1, "url": "http://www.baidu.com"},
        {"text": "汇报事件", "actionType": 3, "value", "xxxxx"}
    ]
]
await yunhu.Send.To("user", user_id).Text("带按钮的消息", buttons=buttons)
```
> **注意：**
> - 只有用户点击了**按钮汇报事件**的按钮才会收到推送，**复制***和**跳转URL**均无法收到推送。

#### 主要方法返回值示例(Send.To(Type, ID).)
1. .Text/.Html/Markdown/.Image/.Video/.File
```json
{
  "code": 1,
  "data": {
    "messageInfo": {
      "msgId": "65a314006db348be97a09eb065985d2d",
      "recvId": "5197892",
      "recvType": "user"
    }
  },
  "msg": "success"
}
```

2. .Batch
```json
{
    "code": 1,
    "data": {
        "successCount": 1,
        "successList": [
            {"msgId": "65a314006db348be97a09eb065985d2d", "recvId": "5197892", "recvType": "user"}
        ]
    },
    "msg": "success"
}
```

#### OneBot12协议转换说明
云湖事件转换到OneBot12协议，其中标准字段完全遵守OneBot12协议，但存在一些差异，你需要阅读以下内容：
需要 platform=="yunhu" 检测再使用本平台特性

##### 核心差异点
1. 特有事件类型：
    - 表单（如表单指令）：yunhu_form
    - 按钮点击：yunhu_button_click
    - 机器人设置：yunhu_bot_setting
    - 快捷菜单：yunhu_shortcut_menu
2. 扩展字段：
    - 所有特有字段均以yunhu_前缀标识
    - 保留原始数据在yunhu_raw字段
    - 私聊中self.user_id表示机器人ID

3. 特殊字段示例：
```python
# 表单命令
{
  "type": "yunhu_form",
  "data": {
    "id": "1766",
    "name": "123123",
    "fields": [
      {
        "id": "abgapt",
        "type": "textarea",
        "value": ""
      },
      {
        "id": "mnabyo", 
        "type": "select",
        "value": ""
      }
    ]
  },
  "yunhu_command": {
    "name": "123123",
    "id": "1766",
    "form": {
      "abgapt": {
        "id": "abgapt",
        "type": "textarea",
        "value": ""
      },
      "mnabyo": {
        "id": "mnabyo",
        "type": "select",
        "value": ""
      }
    }
  }
}

# 按钮事件
{
  "detail_type": "yunhu_button_click",
  "yunhu_button": {
    "id": "",
    "value": "test_button_value"
  }
}

# 机器人设置
{
  "detail_type": "yunhu_bot_setting",
  "yunhu_setting": {
    "lokola": {
      "id": "lokola",
      "type": "radio",
      "value": ""
    },
    "ngcezg": {
      "id": "ngcezg",
      "type": "input",
      "value": null
    }
  }
}

# 快捷菜单
{
  "detail_type": "yunhu_shortcut_menu", 
  "yunhu_menu": {
    "id": "B4X00M5B",
    "type": 1,
    "action": 1
  }
}
```

---

### 2. TelegramAdapter
TelegramAdapter 是基于 Telegram Bot API 构建的适配器，支持多种消息类型和事件处理。

#### 支持的消息发送类型
所有发送方法均通过链式语法实现，例如：
```python
await telegram.Send.To("user", user_id).Text("Hello World!")
```

支持的发送类型包括：
- `.Text(text: str)`：发送纯文本消息。
- `.Image(file: bytes, caption: str = "")`：发送图片消息。
- `.Video(file: bytes, caption: str = "")`：发送视频消息。
- `.Audio(file: bytes, caption: str = "")`：发送音频消息。
- `.Document(file: bytes, caption: str = "")`：发送文件消息。
- `.EditMessageText(message_id: int, text: str)`：编辑已有消息。
- `.DeleteMessage(message_id: int)`：删除指定消息。
- `.GetChat()`：获取聊天信息。

#### env.py 配置示例
```python
sdk.env.set("TelegramAdapter", {
    # 必填：Telegram Bot Token
    "token": "YOUR_BOT_TOKEN",

    # Webhook 模式下的服务配置（如使用 webhook）
    "server": {
        "host": "127.0.0.1",            # 推荐监听本地，防止外网直连
        "port": 8443,                   # 监听端口
        "path": "/telegram/webhook"     # Webhook 路径
    },
    "webhook": {
        "host": "example.com",          # Telegram API 监听地址（外部地址）
        "port": 8443,                   # 监听端口
        "path": "/telegram/webhook"     # Webhook 路径
    }

    # 启动模式: webhook 或 polling
    "mode": "webhook",

    # 可选：代理配置（用于连接 Telegram API）
    "proxy": {
        "host": "127.0.0.1",
        "port": 1080,
        "type": "socks5"  # 支持 socks4 / socks5
    }
})
```

#### 数据格式示例
> 略: 使用你了解的 TG 事件数据格式即可,这里不进行演示

#### OneBot12协议转换说明
Telegram事件转换到OneBot12协议，其中标准字段完全遵守OneBot12协议，但存在以下差异：

##### 核心差异点
1. 特有事件类型：
   - 内联查询：telegram_inline_query
   - 回调查询：telegram_callback_query
   - 投票事件：telegram_poll
   - 投票答案：telegram_poll_answer

2. 扩展字段：
   - 所有特有字段均以telegram_前缀标识
   - 保留原始数据在telegram_raw字段
   - 频道消息使用detail_type="channel"

3. 特殊字段示例：
```python
# 回调查询事件
{
  "type": "notice",
  "detail_type": "telegram_callback_query",
  "user_id": "123456",
  "telegram_callback": {
    "id": "cb_123",
    "data": "callback_data",
    "message_id": "msg_456"
  }
}

# 内联查询事件
{
  "type": "notice",
  "detail_type": "telegram_inline_query",
  "user_id": "789012",
  "telegram_inline": {
    "id": "iq_789",
    "query": "search_text",
    "offset": "0"
  }
}

# 频道消息
{
  "type": "message",
  "detail_type": "channel",
  "message_id": "msg_345",
  "channel_id": "channel_123",
  "telegram_channel": {
    "title": "News Channel",
    "username": "news_official"
  }
}
```

---

### 3. OneBotAdapter
OneBotAdapter 是基于 OneBot V11 协议构建的适配器，适用于与 go-cqhttp 等服务端交互。

#### 支持的消息发送类型
所有发送方法均通过链式语法实现，例如：
```python
await onebot.Send.To("group", group_id).Text("Hello World!")
```

支持的发送类型包括：
- `.Text(text: str)`：发送纯文本消息。
- `.Image(file: str)`：发送图片消息（支持 URL 或 Base64）。
- `.Voice(file: str)`：发送语音消息。
- `.Video(file: str)`：发送视频消息。
- `.Raw(message_list: List[Dict])`：发送原生 OneBot 消息结构。
- `.Recall(message_id: int)`：撤回消息。
- `.Edit(message_id: int, new_text: str)`：编辑消息。
- `.Batch(target_ids: List[str], text: str)`：批量发送消息。


#### 数据格式示例
> 略: 使用你了解的 OneBot v11 事件数据格式即可,这里不进行演示
#### OneBot12协议转换说明
OneBot11事件转换到OneBot12协议，其中标准字段完全遵守OneBot12协议，但存在以下差异：

##### 核心差异点
1. 特有事件类型：
   - CQ码扩展事件：onebot11_cq_{type}
   - 荣誉变更事件：onebot11_honor
   - 戳一戳事件：onebot11_poke

2. 扩展字段：
   - 所有特有字段均以onebot11_前缀标识
   - 保留原始CQ码消息在onebot11_raw_message字段
   - 保留原始事件数据在onebot11_raw字段

3. 特殊字段示例：
```python
# 荣誉变更事件
{
  "type": "notice",
  "detail_type": "onebot11_honor",
  "group_id": "123456",
  "user_id": "789012",
  "onebot11_honor_type": "talkative",
  "onebot11_operation": "set"
}

# 戳一戳事件
{
  "type": "notice",
  "detail_type": "onebot11_poke",
  "group_id": "123456",
  "user_id": "789012",
  "target_id": "345678",
  "onebot11_poke_type": "normal"
}

# CQ码消息段
{
  "type": "message",
  "message": [
    {
      "type": "onebot11_face",
      "data": {"id": "123"}
    },
    {
      "type": "onebot11_shake",
      "data": {} 
    }
  ]
}
```

---

## 生命周期管理

### 启动适配器
```python
await sdk.adapter.startup()
```
此方法会根据配置启动适配器，并初始化必要的连接。

### 关闭适配器
```python
await sdk.adapter.shutdown()
```
确保资源释放，关闭 WebSocket 连接或其他网络资源。

---

## 参考链接
ErisPulse 项目：
- [主库](https://github.com/ErisPulse/ErisPulse/)
- [ErisPulse Yunhu 适配器库](https://github.com/ErisPulse/ErisPulse-YunhuAdapter)
- [ErisPulse Telegram 适配器库](https://github.com/ErisPulse/ErisPulse-TelegramAdapter)
- [ErisPulse OneBot 适配器库](https://github.com/ErisPulse/ErisPulse-OneBotAdapter)

官方文档：
- [OneBot V11 协议文档](https://github.com/botuniverse/onebot-11)
- [Telegram Bot API 官方文档](https://core.telegram.org/bots/api)
- [云湖官方文档](https://www.yhchat.com/document/1-3)

---

## 参与贡献

我们欢迎更多开发者参与编写和维护适配器文档！请按照以下步骤提交贡献：
1. Fork [ErisPuls](https://github.com/ErisPulse/ErisPulse) 仓库。
2. 在 `docs/` 目录下找到 ADAPTER.md 适配器文档。
3. 提交 Pull Request，并附上详细的描述。

感谢您的支持！

<!--- End of ADAPTERS.md -->

<!-- Conversion-Standard​.md -->

# ErisPulse 适配器标准化转换规范

## 1. 核心原则
1. 严格兼容：所有标准字段必须完全遵循OneBot12规范
2. 明确扩展：平台特有功能必须添加 {platform}_ 前缀（如 yunhu_form）
3. 数据完整：原始事件数据必须保留在 {platform}_raw 字段中
4. 时间统一：所有时间戳必须转换为10位Unix时间戳（秒级）
5. 平台统一：platform项命名必须与你在ErisPulse中注册的名称/别称一致

## 2. 基础字段规范
### 2.1 必填字段（所有事件）
|字段|类型|要求|
|-|-|-|
|id|string|必须存在，原始事件无ID时使用UUID生成|
|time|int|10位秒级时间戳（毫秒级需转换）|
|type|string|必须为 message/notice/request 之一|
|platform|string|必须与适配器注册名完全一致|
|self|object|必须包含 platform 和 user_id|

### 2.2 条件字段
|字段|触发条件|示例|
|-|-|-|
|detail_type|所有事件必须|"group"/"private"|
|sub_type|需要细分时|"invite"/"leave"|
|message_id|消息事件|"msg_123"|
|user_id|涉及用户|"user_456"|
|group_id|群组事件|"group_789"|

## 3. 完整事件模板
### 3.1 消息事件 (message)
```json
{
  "id": "event_123",
  "time": 1752241220,
  "type": "message",
  "detail_type": "group",
  "sub_type": "",
  "platform": "yunhu",
  "self": {
    "platform": "yunhu",
    "user_id": "bot_123"
  },
  "message_id": "msg_abc",
  "message": [
    {
      "type": "text",
      "data": {"text": "你好"}
    },
    {
      "type": "image",
      "data": {
        "file_id": "img_xyz",
        "url": "https://example.com/image.jpg",
        "file_name": "example.jpg",
        "size": 102400,
        "width": 800,
        "height": 600
      }
    }
  ],
  "alt_message": "你好[图片]",
  "user_id": "user_456",
  "group_id": "group_789",
  "yunhu_raw": {...},
  "yunhu_command": {
    "name": "抽奖",
    "args": "超级大奖"
  }
}
```
### 3.2 通知事件 (notice)
```json
{
  "id": "event_456",
  "time": 1752241221,
  "type": "notice",
  "detail_type": "group_member_increase",
  "sub_type": "invite",
  "platform": "yunhu",
  "self": {
    "platform": "yunhu",
    "user_id": "bot_123"
  },
  "user_id": "user_456",
  "group_id": "group_789",
  "operator_id": "",
  "yunhu_raw": {...},
}
```
### 3.3 请求事件 (request)
```json
{
  "id": "event_789",
  "time": 1752241222,
  "type": "request",
  "detail_type": "friend",
  "platform": "onebot11",
  "self": {
    "platform": "onebot11",
    "user_id": "bot_123"
  },
  "user_id": "user_456",
  "comment": "请加好友",
  "onebot11_raw": {...},
}
```
## 4. 消息段标准
### 4.1 通用消息段
|类型|必填字段|扩展字段|
|-|-|-|
|text|text|-|
|image|url|file_name, size, width, height|
|video|url|duration, file_name|
|file|url|size, file_name|

## 5. 错误处理规范
### 5.1 字段缺失处理
```python
def safe_get(data: dict, key: str, default=None):
    """安全获取字段并记录警告"""
    if key not in data:
        logger.warning(f"Missing field '{key}' in {data.get('eventType', 'unknown')}")
    return data.get(key, default)
```
### 5.2 未知事件处理
```json
{
  "id": "event_999",
  "time": 1752241223,
  "type": "unknown",
  "platform": "yunhu",
  "yunhu_raw": {...},
  "warning": "Unsupported event type: special_event",
  "alt_message": "This event type is not supported by this system."
}
```
## 6. 时间戳转换标准
```python
def convert_timestamp(ts: Any) -> int:
    """标准化时间戳处理"""
    if isinstance(ts, str):
        if len(ts) == 13:  # 毫秒级
            return int(ts) // 1000
        return int(ts)
    elif isinstance(ts, (int, float)):
        if ts > 9999999999:  # 毫秒级
            return int(ts // 1000)
        return int(ts)
    return int(time.time())  # 默认当前时间
```
## 7. 适配器实现检查清单
- [ ] 所有标准字段已正确映射
- [ ] 平台特有字段已添加前缀
- [ ] 时间戳已转换为10位秒级
- [ ] 原始数据保存在 {platform}_raw
- [ ] 消息段的 alt_message 已生成
- [ ] 所有事件类型已通过单元测试
- [ ] 文档包含完整示例和说明
## 8. 最佳实践示例
### 云湖表单消息处理
```python
def _convert_form_message(self, raw_form: dict) -> dict:
    """转换表单消息为标准格式"""
    return {
        "type": "yunhu_form",
        "data": {
            "id": raw_form.get("formId"),
            "fields": [
                {
                    "id": field.get("fieldId"),
                    "type": field.get("fieldType"),
                    "label": field.get("label"),
                    "value": field.get("value")
                }
                for field in raw_form.get("fields", [])
            ]
        }
    }
```
### 消息ID生成规则
```python
def generate_message_id(platform: str, raw_id: str) -> str:
    """标准化消息ID格式"""
    return f"{platform}_msg_{raw_id}" if raw_id else f"{platform}_msg_{uuid.uuid4()}"
```
本规范确保所有适配器：
1. 保持与OneBot12的完全兼容性
2. 平台特有功能可识别且不冲突
3. 转换过程可追溯（通过_raw字段）
4. 数据类型和格式统一
建议配合自动化测试验证所有转换场景，特别是：
- 边界值测试（如空消息、超大文件）
- 特殊字符测试（消息内容含emoji/特殊符号）
- 压力测试（连续事件转换）

<!--- End of Conversion-Standard​.md -->

<!-- API文档 -->

# API参考

## ErisPulse\__init__.md

# `ErisPulse/__init__` 模块

ErisPulse SDK 主模块

提供SDK核心功能模块加载和初始化功能

> **提示**：
1. 使用前请确保已正确安装所有依赖
2. 调用sdk.init()进行初始化
3. 模块加载采用懒加载机制

## 函数

### `init_progress`

初始化项目环境文件

1. 检查并创建main.py入口文件
2. 确保基础目录结构存在

:return: bool: 是否创建了新的main.py文件

> **提示**：
1. 如果main.py已存在则不会覆盖
2. 此方法通常由SDK内部调用


### `init`

SDK初始化入口

执行步骤:
1. 准备运行环境
2. 初始化所有模块和适配器

:return: bool: SDK初始化是否成功

> **提示**：
1. 这是SDK的主要入口函数
2. 如果初始化失败会抛出InitError异常
3. 建议在main.py中调用此函数




:raises InitError: 当初始化失败时抛出


### `load_module`

手动加载指定模块

:param module_name: 要加载的模块名称
:return: bool: 加载是否成功

> **提示**：
1. 可用于手动触发懒加载模块的初始化
2. 如果模块不存在或已加载会返回False


## 类

### `LazyModule`

懒加载模块包装器

当模块第一次被访问时才进行实例化

> **提示**：
1. 模块的实际实例化会在第一次属性访问时进行
2. 依赖模块会在被使用时自动初始化


#### 方法

##### `__init__`

初始化懒加载包装器

:param module_name: 模块名称
:param module_class: 模块类
:param sdk_ref: SDK引用
:param module_info: 模块信息字典


##### `_initialize`

实际初始化模块


##### `__getattr__`

属性访问时触发初始化


##### `__call__`

调用时触发初始化


### `AdapterLoader`

适配器加载器

专门用于从PyPI包加载和初始化适配器

> **提示**：
1. 适配器必须通过entry-points机制注册到erispulse.adapter组
2. 适配器类必须继承BaseAdapter
3. 适配器不适用懒加载


#### 方法

##### `load`

从PyPI包entry-points加载适配器

:return: 
    Dict[str, object]: 适配器对象字典 {适配器名: 模块对象}
    List[str]: 启用的适配器名称列表
    List[str]: 停用的适配器名称列表
    
:raises ImportError: 当无法加载适配器时抛出


### `ModuleLoader`

模块加载器

专门用于从PyPI包加载和初始化普通模块

> **提示**：
1. 模块必须通过entry-points机制注册到erispulse.module组
2. 模块类名应与entry-point名称一致


#### 方法

##### `load`

从PyPI包entry-points加载模块

:return: 
    Dict[str, object]: 模块对象字典 {模块名: 模块对象}
    List[str]: 启用的模块名称列表
    List[str]: 停用的模块名称列表
    
:raises ImportError: 当无法加载模块时抛出


##### `_should_lazy_load`

检查模块是否应该懒加载

:param module_class: 模块类
:return: bool: 如果返回 False，则立即加载；否则懒加载


### `ModuleInitializer`

模块初始化器

负责协调适配器和模块的初始化流程

> **提示**：
1. 初始化顺序：适配器 → 模块
2. 模块初始化采用懒加载机制


#### 方法

##### `init`

初始化所有模块和适配器

执行步骤:
1. 从PyPI包加载适配器
2. 从PyPI包加载模块
3. 预记录所有模块信息
4. 注册适配器
5. 初始化各模块

:return: bool: 初始化是否成功


##### `_pre_register_modules`

预记录所有模块信息到SDK属性中

确保所有模块在初始化前都已在SDK中注册



## ErisPulse\__main__.md

# `ErisPulse/__main__` 模块

# CLI 入口

提供命令行界面(CLI)用于包管理和启动入口。

## 主要命令
### 包管理:
    search: 搜索PyPI上的ErisPulse模块
    install: 安装模块/适配器包
    uninstall: 卸载模块/适配器包
    list: 列出已安装的模块/适配器
    list-remote: 列出远程PyPI上的ErisPulse模块和适配器
    upgrade: 升级所有模块/适配器

### 启动:
    run: 运行脚本
    --reload: 启用热重载

### 示例用法:
```
# 安装模块
epsdk install Yunhu

# 启用热重载
epsdk run main.py --reload
```

## 类

### `PyPIManager`

管理PyPI上的ErisPulse模块和适配器



## ErisPulse\Core\adapter.md

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



## ErisPulse\Core\env.md

# `ErisPulse/Core/env` 模块

ErisPulse 环境配置模块

提供键值存储、事务支持、快照和恢复功能，用于管理框架配置数据。基于SQLite实现持久化存储，支持复杂数据类型和原子操作。

> **提示**：
1. 支持JSON序列化存储复杂数据类型
2. 提供事务支持确保数据一致性
3. 自动快照功能防止数据丢失

## 类

### `EnvManager`

环境配置管理器

单例模式实现，提供配置的增删改查、事务和快照管理

> **提示**：
1. 使用get/set方法操作配置项
2. 使用transaction上下文管理事务
3. 使用snapshot/restore管理数据快照


#### 方法

##### `get`

获取配置项的值

:param key: 配置项键名
:param default: 默认值(当键不存在时返回)
:return: 配置项的值

:example:
>>> timeout = env.get("network.timeout", 30)
>>> user_settings = env.get("user.settings", {})


##### `get_all_keys`

获取所有配置项的键名

:return: 键名列表

:example:
>>> all_keys = env.get_all_keys()
>>> print(f"共有 {len(all_keys)} 个配置项")


##### `set`

设置配置项的值

:param key: 配置项键名
:param value: 配置项的值
:return: 操作是否成功

:example:
>>> env.set("app.name", "MyApp")
>>> env.set("user.settings", {"theme": "dark"})


##### `set_multi`

批量设置多个配置项

:param items: 键值对字典
:return: 操作是否成功

:example:
>>> env.set_multi({
>>>     "app.name": "MyApp",
>>>     "app.version": "1.0.0",
>>>     "app.debug": True
>>> })


##### `getConfig`

获取模块/适配器配置项
:param key: 配置项的键(支持点分隔符如"module.sub.key")
:param default: 默认值
:return: 配置项的值


##### `setConfig`

设置模块/适配器配置
:param key: 配置项键名(支持点分隔符如"module.sub.key")
:param value: 配置项值
:return: 操作是否成功


##### `delete`

删除配置项

:param key: 配置项键名
:return: 操作是否成功

:example:
>>> env.delete("temp.session")


##### `delete_multi`

批量删除多个配置项

:param keys: 键名列表
:return: 操作是否成功

:example:
>>> env.delete_multi(["temp.key1", "temp.key2"])


##### `get_multi`

批量获取多个配置项的值

:param keys: 键名列表
:return: 键值对字典

:example:
>>> settings = env.get_multi(["app.name", "app.version"])


##### `transaction`

创建事务上下文

:return: 事务上下文管理器

:example:
>>> with env.transaction():
>>>     env.set("key1", "value1")
>>>     env.set("key2", "value2")


##### `set_snapshot_interval`

设置自动快照间隔

:param seconds: 间隔秒数

:example:
>>> # 每30分钟自动快照
>>> env.set_snapshot_interval(1800)


##### `clear`

清空所有配置项

:return: 操作是否成功

:example:
>>> env.clear()  # 清空所有配置


##### `load_env_file`

加载env.py文件中的配置项

:return: 操作是否成功

:example:
>>> env.load_env_file()  # 加载env.py中的配置


##### `__getattr__`

通过属性访问配置项

:param key: 配置项键名
:return: 配置项的值

:raises KeyError: 当配置项不存在时抛出
    
:example:
>>> app_name = env.app_name


##### `__setattr__`

通过属性设置配置项

:param key: 配置项键名
:param value: 配置项的值
    
:example:
>>> env.app_name = "MyApp"


##### `snapshot`

创建数据库快照

:param name: 快照名称(可选)
:return: 快照文件路径

:example:
>>> # 创建命名快照
>>> snapshot_path = env.snapshot("before_update")
>>> # 创建时间戳快照
>>> snapshot_path = env.snapshot()


##### `restore`

从快照恢复数据库

:param snapshot_name: 快照名称或路径
:return: 恢复是否成功

:example:
>>> env.restore("before_update")


##### `list_snapshots`

列出所有可用的快照

:return: 快照信息列表(名称, 创建时间, 大小)

:example:
>>> for name, date, size in env.list_snapshots():
>>>     print(f"{name} - {date} ({size} bytes)")


##### `delete_snapshot`

删除指定的快照

:param snapshot_name: 快照名称
:return: 删除是否成功

:example:
>>> env.delete_snapshot("old_backup")



## ErisPulse\Core\mods.md

# `ErisPulse/Core/mods` 模块

ErisPulse 模块管理器

提供模块的注册、状态管理和依赖关系处理功能。支持模块的启用/禁用、版本控制和依赖解析。

> **提示**：
1. 使用模块前缀区分不同模块的配置
2. 支持模块状态持久化存储
3. 自动处理模块间的依赖关系

## 类

### `ModuleManager`

模块管理器

管理所有模块的注册、状态和依赖关系

> **提示**：
1. 通过set_module/get_module管理模块信息
2. 通过set_module_status/get_module_status控制模块状态
3. 通过set_all_modules/get_all_modules批量操作模块


#### 方法

##### `module_prefix`

获取模块数据前缀

:return: 模块数据前缀字符串


##### `status_prefix`

获取模块状态前缀

:return: 模块状态前缀字符串


##### `set_module_status`

设置模块启用状态

:param module_name: 模块名称
:param status: 启用状态

:example:
>>> # 启用模块
>>> mods.set_module_status("MyModule", True)
>>> # 禁用模块
>>> mods.set_module_status("MyModule", False)


##### `get_module_status`

获取模块启用状态

:param module_name: 模块名称
:return: 模块是否启用

:example:
>>> if mods.get_module_status("MyModule"):
>>>     print("模块已启用")


##### `set_module`

设置模块信息

:param module_name: 模块名称
:param module_info: 模块信息字典

:example:
>>> mods.set_module("MyModule", {
>>>     "version": "1.0.0",
>>>     "description": "我的模块",
>>>     "status": True
>>> })


##### `get_module`

获取模块信息

:param module_name: 模块名称
:return: 模块信息字典或None

:example:
>>> module_info = mods.get_module("MyModule")
>>> if module_info:
>>>     print(f"模块版本: {module_info.get('version')}")


##### `set_all_modules`

批量设置多个模块信息

:param modules_info: 模块信息字典

:example:
>>> mods.set_all_modules({
>>>     "Module1": {"version": "1.0", "status": True},
>>>     "Module2": {"version": "2.0", "status": False}
>>> })


##### `get_all_modules`

获取所有模块信息

:return: 模块信息字典

:example:
>>> all_modules = mods.get_all_modules()
>>> for name, info in all_modules.items():
>>>     print(f"{name}: {info.get('status')}")


##### `update_module`

更新模块信息

:param module_name: 模块名称
:param module_info: 完整的模块信息字典


##### `remove_module`

移除模块

:param module_name: 模块名称
:return: 是否成功移除

:example:
>>> if mods.remove_module("OldModule"):
>>>     print("模块已移除")


##### `update_prefixes`

更新模块前缀配置

:param module_prefix: 新的模块数据前缀(可选)
:param status_prefix: 新的模块状态前缀(可选)

:example:
>>> # 更新模块前缀
>>> mods.update_prefixes(
>>>     module_prefix="custom.module.data:",
>>>     status_prefix="custom.module.status:"
>>> )



## ErisPulse\Core\raiserr.md

# `ErisPulse/Core/raiserr` 模块

ErisPulse 错误管理系统

提供错误类型注册、抛出和管理功能，集成全局异常处理。支持自定义错误类型、错误链追踪和全局异常捕获。

> **提示**：
1. 使用register注册自定义错误类型
2. 通过info获取错误信息
3. 自动捕获未处理异常

## 类

### `Error`

错误管理器

提供错误类型注册和抛出功能

> **提示**：
1. 通过register方法注册自定义错误类型
2. 通过动态属性访问抛出错误
3. 通过info方法获取错误信息


#### 方法

##### `register`

注册新的错误类型

:param name: 错误类型名称
:param doc: 错误描述文档
:param base: 基础异常类
:return: 注册的错误类

:example:
>>> # 注册简单错误
>>> raiserr.register("SimpleError", "简单的错误类型")
>>> # 注册自定义基类的错误
>>> raiserr.register("AdvancedError", "高级错误", CustomBaseError)


##### `__getattr__`

动态获取错误抛出函数

:param name: 错误类型名称
:return: 错误抛出函数

:raises AttributeError: 当错误类型未注册时抛出


##### `info`

获取错误信息

:param name: 错误类型名称(可选)
:return: 错误信息字典

:example:
>>> # 获取特定错误信息
>>> error_info = raiserr.info("SimpleError")
>>> # 获取所有错误信息
>>> all_errors = raiserr.info()



## ErisPulse\Core\server.md

# `ErisPulse/Core/server` 模块

ErisPulse Adapter Server
提供统一的适配器服务入口，支持HTTP和WebSocket路由

> **提示**：
1. 适配器只需注册路由，无需自行管理服务器
2. WebSocket支持自定义认证逻辑
3. 兼容FastAPI 0.68+ 版本

## 类

### `AdapterServer`

适配器服务器管理器

> **提示**：
核心功能：
- HTTP/WebSocket路由注册
- 生命周期管理
- 统一错误处理


#### 方法

##### `__init__`

初始化适配器服务器

> **提示**：
会自动创建FastAPI实例并设置核心路由


##### `register_webhook`

注册HTTP路由

:param adapter_name: str 适配器名称
:param path: str 路由路径(如"/message")
:param handler: Callable 处理函数
:param methods: List[str] HTTP方法列表(默认["POST"])

:raises ValueError: 当路径已注册时抛出

> **提示**：
路径会自动添加适配器前缀，如：/adapter_name/path


##### `register_websocket`

注册WebSocket路由

:param adapter_name: str 适配器名称
:param path: str WebSocket路径(如"/ws")
:param handler: Callable[[WebSocket], Awaitable[Any]] 主处理函数
:param auth_handler: Optional[Callable[[WebSocket], Awaitable[bool]]] 认证函数

:raises ValueError: 当路径已注册时抛出

> **提示**：
认证函数应返回布尔值，False将拒绝连接


##### `get_app`

获取FastAPI应用实例

:return: 
    FastAPI: FastAPI应用实例


##### `start`

启动适配器服务器

:param host: str 监听地址(默认"0.0.0.0")
:param port: int 监听端口(默认8000)
:param ssl_certfile: Optional[str] SSL证书路径
:param ssl_keyfile: Optional[str] SSL密钥路径

:raises RuntimeError: 当服务器已在运行时抛出


##### `stop`

停止服务器

> **提示**：
会等待所有连接正常关闭



## ErisPulse\Core\util.md

# `ErisPulse/Core/util` 模块

ErisPulse 工具函数集合

提供常用工具函数，包括拓扑排序、缓存装饰器、异步执行等实用功能。

> **提示**：
1. 使用@cache装饰器缓存函数结果
2. 使用@run_in_executor在独立线程中运行同步函数
3. 使用@retry实现自动重试机制

## 类

### `Util`

工具函数集合

提供各种实用功能，简化开发流程

> **提示**：
1. 拓扑排序用于解决依赖关系
2. 装饰器简化常见模式实现
3. 异步执行提升性能


#### 方法

##### `ExecAsync`

异步执行函数

:param async_func: 异步函数
:param args: 位置参数
:param kwargs: 关键字参数
:return: 函数执行结果

:example:
>>> result = util.ExecAsync(my_async_func, arg1, arg2)


##### `cache`

缓存装饰器

:param func: 被装饰函数
:return: 装饰后的函数

:example:
>>> @util.cache
>>> def expensive_operation(param):
>>>     return heavy_computation(param)


##### `run_in_executor`

在独立线程中执行同步函数的装饰器

:param func: 被装饰的同步函数
:return: 可等待的协程函数

:example:
>>> @util.run_in_executor
>>> def blocking_io():
>>>     # 执行阻塞IO操作
>>>     return result


##### `retry`

自动重试装饰器

:param max_attempts: 最大重试次数 (默认: 3)
:param delay: 重试间隔(秒) (默认: 1)
:return: 装饰器函数

:example:
>>> @util.retry(max_attempts=5, delay=2)
>>> def unreliable_operation():
>>>     # 可能失败的操作



<!--- End of API文档 -->
