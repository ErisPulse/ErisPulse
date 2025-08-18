# ErisPulse 适配器开发文档

**生成时间**: 2025-08-18 15:39:06

本文件由多个开发文档合并而成，用于辅助开发者理解 ErisPulse 的相关功能。

## 目录

1. [快速开始指南](#quick-startmd)
2. [核心功能使用说明](#UseCoremd)
3. [适配器开发指南](#Adaptermd)
4. [API响应标准](#APIResponsemd)
5. [事件转换标准](#EventConversionmd)

## 各文件对应内容说明

| 文件名 | 作用 |
|--------|------|
| [quick-start.md](#quick-startmd) | 快速开始指南 |
| [UseCore.md](#UseCoremd) | 核心功能使用说明 |
| [Adapter.md](#Adaptermd) | 适配器开发指南 |
| [APIResponse.md](#APIResponsemd) | API响应标准 |
| [EventConversion.md](#EventConversionmd) | 事件转换标准 |

---

<a id="quick-startmd"></a>
## 快速开始指南

# 快速开始

## 安装ErisPulse

### 使用 pip 安装
确保你的 Python 版本 >= 3.8，然后使用 pip 安装 ErisPulse：
```bash
pip install ErisPulse
```

### 更先进的安装方法
> 采用 [`uv`](https://github.com/astral-sh/uv) 作为 Python 工具链

### 1. 安装 uv

#### 通用方法 (pip):
```bash
pip install uv
```

#### macOS/Linux:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

#### Windows (PowerShell):
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

验证安装:
```bash
uv --version
```

### 2. 创建虚拟环境,并安装 ErisPulse

```bash
uv python install 3.12              # 安装 Python 3.12
uv venv                             # 创建虚拟环境
source .venv/bin/activate           # 激活环境 (Windows: .venv\Scripts\activate)
uv pip install ErisPulse --upgrade  # 安装框架
```

---

## 初始化项目

1. 创建项目目录并进入：

```bash
mkdir my_bot && cd my_bot
```

2. 初始化 SDK 并生成配置文件：

```bsah
ep-init
```
这将在当前目录下生成 `config.yml` 和 `main.py` 入口。

---

## 安装模块

你可以通过 CLI 安装所需模块：

```bash
epsdk install Yunhu AIChat
```

你也可以手动编写模块逻辑，参考开发者文档进行模块开发。

---

## 运行你的机器人
运行我们自动生成的程序入口：
```bash
epsdk run main.py
```

或者使用热重载模式（开发时推荐）：

```bash
epsdk run main.py --reload
```


---

<a id="UseCoremd"></a>
## 核心功能使用说明

# ErisPulse 核心模块使用指南

## 核心模块
| 名称 | 用途 |
|------|------|
| `sdk` | SDK对象 |
| `storage`/`sdk.storage` | 获取/设置数据库配置 |
| `config`/`sdk.config` | 获取/设置模块配置 |
| `module_registry`/`sdk.module_registry` | 模块状态管理器 |
| `adapter`/`sdk.adapter` | 适配器管理/获取实例 |
| `module`/`sdk.module` | 获取模块实例 |
| `logger`/`sdk.logger` | 日志记录器 |
| `BaseAdapter`/`sdk.BaseAdapter` | 适配器基类 |
| `Event`/`sdk.Event` | 事件处理模块 |

> 注意: `Event` 模块是 ErisPulse 2.2.0 引入的新模块,发布模块时请注意提醒用户兼容性问题
Event 模块包含以下子模块：

| 子模块 | 用途 |
|-------|------|
| `Event.command` | 命令处理 |
| `Event.message` | 消息事件处理 |
| `Event.notice` | 通知事件处理 |
| `Event.request` | 请求事件处理 |
| `Event.meta` | 元事件处理 |
| `Event.exceptions` | 事件异常处理 |

```python
# 直接导入方式
from ErisPulse.Core import (
        storage, config, module_registry,
        adapter, module, logger,
        BaseAdapter, Event
    )

# 通过SDK对象方式
from ErisPulse import sdk
sdk.storage  # 等同于直接导入的storage
```

## 模块使用
- 所有模块通过 `sdk` 对象统一管理
- 每个模块拥有独立命名空间，使用 `sdk` 进行调用
- 可以在模块间使用 `sdk.<module_name>.<func>` 的方式调用其他模块中的方法

## 适配器使用
- 适配器是ErisPulse的核心，负责与平台进行交互

适配器事件分为两类：
- 标准事件：平台转换为的标准事件，其格式为标准的 OneBot12 事件格式 | 需要判断接收到的消息的 `platform` 字段，来确定消息来自哪个平台
- 原生事件：平台原生事件 通过 sdk.adapter.<Adapter>.on() 监听对应平台的原生事件
适配器标准事件的拓展以及支持的消息发送类型，请参考 [PlatformFeatures.md](docs/PlatformFeatures.md)

建议使用标准事件进行事件的处理，适配器会自动将原生事件转换为标准事件

```python
# 启动适配器
await sdk.adapter.startup("MyAdapter")  # 不指定名称则启动所有适配器
# 另外可以传入列表，例如 sdk.adapter.startup(["Telegram", "Yunhu"])

# 监听 OneBot12 标准事件
@adapter.on("message")
async def on_message(data):
    platform = data.get("platform")
    detail_type = "user" if data.get("detail_type") == "private" else "group"
    detail_id = data.get("user_id") if detail_type == "user" else data.get("group_id")
    Sender = None

    if hasattr(adapter, platform):
        Sender = getattr(adapter, platform).To(detail_type, detail_id)
    
    Sender.Text(data.get("alt_message"))

# 监听平台原生事件
@adapter.Telegram.on("message")
async def on_raw_message(data):
    # Do something ...
```
平台原生事件监听并不建议使用，因为格式不保证与 OneBot12 兼容，另外 OneBot12 的标准事件规定了一个拓展字段 `{{platform}}_raw` 用于传输平台原生数据

## 事件处理模块(Event)
Event 模块提供了一套完整的事件处理机制，支持命令处理、消息处理、通知处理、请求处理和元事件处理等功能。

### 命令处理
```python
from ErisPulse.Core.Event import command

# 基本命令
@command("hello", help="发送问候消息")
async def hello_command(event):
    platform = event["platform"]
    user_id = event["user_id"]
    
    # 发送回复消息
    adapter_instance = getattr(sdk.adapter, platform)
    await adapter_instance.Send.To("user", user_id).Text("Hello World!")

# 带参数的命令
@command("echo", help="回显消息", usage="/echo <内容>")
async def echo_command(event):
    platform = event["platform"]
    user_id = event["user_id"]
    args = event["command"]["args"]
    
    if not args:
        await send_reply(event, "请提供要回显的内容")
        return
    
    message = " ".join(args)
    adapter_instance = getattr(sdk.adapter, platform)
    await adapter_instance.Send.To("user", user_id).Text(message)

# 带别名的命令
@command(["help", "h"], aliases=["帮助"], help="显示帮助信息")
async def help_command(event):
    platform = event["platform"]
    user_id = event["user_id"]
    help_text = command.help()
    
    adapter_instance = getattr(sdk.adapter, platform)
    await adapter_instance.Send.To("user", user_id).Text(help_text)

# 带权限检查的命令
def is_admin(event):
    # 检查是否为管理员
    user_id = event.get("user_id")
    return user_id in ["admin_id_1", "admin_id_2"]

@command("admin", permission=is_admin, help="管理员命令")
async def admin_command(event):
    # 只有管理员才能执行
    pass

# 隐藏命令
@command("secret", hidden=True, help="秘密命令")
async def secret_command(event):
    # 不会在帮助中显示
    pass

# 命令组
@command("admin.reload", group="admin", help="重新加载模块")
async def reload_command(event):
    # 管理员命令逻辑
    pass
```

### 消息处理
```python
from ErisPulse.Core.Event import message

# 处理所有消息
@message.on_message()
async def handle_message(event):
    sdk.logger.info(f"收到消息: {event['alt_message']}")

# 处理私聊消息
@message.on_private_message()
async def handle_private_message(event):
    user_id = event["user_id"]
    sdk.logger.info(f"收到私聊消息，来自用户: {user_id}")

# 处理群聊消息
@message.on_group_message()
async def handle_group_message(event):
    group_id = event["group_id"]
    user_id = event["user_id"]
    sdk.logger.info(f"收到群消息，群: {group_id}，用户: {user_id}")

# 处理@消息
@message.on_at_message()
async def handle_at_message(event):
    user_id = event["user_id"]
    sdk.logger.info(f"收到@消息，来自用户: {user_id}")
```

### 通知处理
```python
from ErisPulse.Core.Event import notice

# 处理好友添加通知
@notice.on_friend_add()
async def handle_friend_add(event):
    user_id = event["user_id"]
    sdk.logger.info(f"新好友添加: {user_id}")
    
    # 发送欢迎消息
    platform = event["platform"]
    adapter_instance = getattr(sdk.adapter, platform)
    await adapter_instance.Send.To("user", user_id).Text("欢迎添加我为好友！")

# 处理群成员增加通知
@notice.on_group_increase()
async def handle_group_increase(event):
    group_id = event["group_id"]
    user_id = event["user_id"]
    sdk.logger.info(f"新成员加入群: {group_id}，用户: {user_id}")

# 处理好友删除通知
@notice.on_friend_remove()
async def handle_friend_remove(event):
    user_id = event["user_id"]
    sdk.logger.info(f"好友删除: {user_id}")

# 处理群成员减少通知
@notice.on_group_decrease()
async def handle_group_decrease(event):
    group_id = event["group_id"]
    user_id = event["user_id"]
    sdk.logger.info(f"群成员减少，群: {group_id}，用户: {user_id}")
```

### 请求处理
```python
from ErisPulse.Core.Event import request

# 处理好友请求
@request.on_friend_request()
async def handle_friend_request(event):
    user_id = event["user_id"]
    sdk.logger.info(f"收到好友请求，来自用户: {user_id}")

# 处理群邀请请求
@request.on_group_request()
async def handle_group_request(event):
    group_id = event["group_id"]
    user_id = event["user_id"]
    sdk.logger.info(f"收到群邀请请求，群: {group_id}，用户: {user_id}")
```

### 元事件处理
```python
from ErisPulse.Core.Event import meta

# 处理连接事件
@meta.on_connect()
async def handle_connect(event):
    platform = event["platform"]
    sdk.logger.info(f"平台 {platform} 连接成功")

# 处理断开连接事件
@meta.on_disconnect()
async def handle_disconnect(event):
    platform = event["platform"]
    sdk.logger.info(f"平台 {platform} 断开连接")

# 处理心跳事件
@meta.on_heartbeat()
async def handle_heartbeat(event):
    platform = event["platform"]
    sdk.logger.debug(f"平台 {platform} 心跳")
```

### 高级功能

#### 优先级控制
```python
# 设置处理器优先级
@message.on_message(priority=10)
async def high_priority_handler(event):
    # 高优先级处理器先执行
    pass

@message.on_message(priority=20)
async def low_priority_handler(event):
    # 低优先级处理器后执行
    pass
```

#### 条件处理器
```python
# 定义条件函数
def keyword_condition(event):
    message_segments = event.get("message", [])
    for segment in message_segments:
        if segment.get("type") == "text":
            text = segment.get("data", {}).get("text", "")
            return "关键词" in text
    return False

# 注册条件处理器
@message.on_message(condition=keyword_condition)
async def keyword_handler(event):
    # 只有消息包含"关键词"时才会执行
    pass
```

## 核心模块功能详解

### 1. 日志模块(logger)
```python
logger.set_module_level("MyModule", "DEBUG")  # 设置模块日志级别
logger.save_logs("log.txt")  # 保存日志到文件

# 日志级别
logger.debug("调试信息")
logger.info("运行状态")
logger.warning("警告信息")
logger.error("错误信息")
logger.critical("致命错误")  # 会触发程序崩溃

# 子模块日志记录
# 使用 get_child 方法创建子模块日志记录器，便于更好地组织和识别日志来源
network_logger = logger.get_child("Network")
network_logger.info("网络模块初始化完成")

# 支持多级子模块
http_logger = network_logger.get_child("HTTP")
http_logger.debug("发送HTTP请求")

# 子模块日志记录器使用与主日志记录器相同的配置和功能
# 所有配置操作仍然通过主 logger 对象进行
logger.set_module_level("MyModule", "INFO")  # 影响所有相关子模块
logger.set_output_file("app.log")  # 所有日志都会输出到指定文件
```

### 2. 持久化数据存储(storage)
```python
# 数据库配置操作
storage.set("key", "value")  # 设置配置项
value = storage.get("key", "default")  # 获取配置项
storage.delete("key")  # 删除配置项

# 事务操作
with storage.transaction():
    storage.set('important_key', 'value')
    storage.delete('temp_key')  # 异常时自动回滚

# 批量操作
storage.set_multi({
    "key1": "value1",
    "key2": "value2"
})
storage.delete_multi(["key1", "key2"])
```

### 3. 配置模块(config)
```python
# 模块配置操作（读写config.toml）
module_config = config.getConfig("MyModule")  # 获取模块配置
if module_config is None:
    config.setConfig("MyModule", {"MyKey": "MyValue"})  # 设置默认配置

# 嵌套配置访问
nested_value = config.getConfig("MyModule.subkey.value", "default")
config.setConfig("MyModule.subkey.value", "new_value")
```

### 4. 异常处理模块(exceptions)
```python
# ErisPulse提供了统一的异常处理机制，可以自动捕获和格式化异常信息
# 对于异步代码，可以为特定事件循环设置异常处理器

import asyncio
from ErisPulse.Core import exceptions

# 为当前运行的事件循环设置异常处理器
loop = asyncio.get_running_loop()
exceptions.setup_async_loop(loop)

# 或者不传参数，自动获取当前事件循环 || 但不建议这么做，因为运行主程序时可能使用了其他的异步库
exceptions.setup_async_loop()

# 这样设置后，异步代码中的未捕获异常会被统一处理并格式化输出
```

### 5. 模块管理器(module)
```python
# 直接获取模块实例
my_module = module.get("MyModule")

# 通过属性访问获取模块实例
my_module = module.MyModule

# 检查模块是否存在
if "MyModule" in module:
    # 模块存在并且处于启用状态
    pass

# 检查模块是否启用
if module.is_enabled("MyModule"):
    # 模块已启用
    pass

# 获取模块信息
info = module.get_info("MyModule")

# 列出所有模块
all_modules = module.list_modules()

# 启用/禁用模块
module.enable("MyModule")
module.disable("MyModule")
```

## 配置管理

### 1. 命令前缀配置
```toml
[ErisPulse]
[ErisPulse.event]
[ErisPulse.event.command]
prefix = "/"
case_sensitive = true
allow_space_prefix = false

[ErisPulse.event.message]
ignore_self = true
```

### 2. 框架配置
```toml
[ErisPulse]
[ErisPulse.server]
host = "0.0.0.0"
port = 8000
ssl_certfile = ""
ssl_keyfile = ""

[ErisPulse.logger]
level = "INFO"
log_files = []
memory_limit = 1000
```

更多详细信息请参考[API文档](docs/api/)


---

<a id="Adaptermd"></a>
## 适配器开发指南

# ErisPulse 适配器开发指南

### 1. 目录结构
一个标准的适配器包结构应该是：

```
MyAdapter/
├── pyproject.toml
├── README.md
├── LICENSE
└── MyAdapter/
    ├── __init__.py
    ├── Core.py
    └── Converter.py
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
from ErisPulse.Core import router

# 这里仅你使用 websocket 作为通信协议时需要 | 第一个作为参数的类型是 WebSocket, 第二个是 WebSocketDisconnect，当 ws 连接断开时触发你的捕捉
# 一般来说你不用在依赖中添加 fastapi, 因为它已经内置在 ErisPulse 中了
from fastapi import WebSocket, WebSocketDisconnect

class MyAdapter(BaseAdapter):
    def __init__(self, sdk):    # 这里是不强制传入sdk的，你可以选择不传入 
        self.sdk = sdk
        self.storage = self.sdk.storage
        self.logger = self.sdk.logger
        
        self.logger.info("MyModule 初始化完成")
        self.config = self._get_config()
        self.converter = self._setup_converter()  # 获取转换器实例
        self.convert = self.converter.convert

    def _setup_converter(self):
        from .Converter import MyPlatformConverter
        return MyPlatformConverter()

    def _get_config(self):
        # 加载配置方法，你需要在这里进行必要的配置加载逻辑
        config = self.sdk.config.getConfig("MyAdapter", {})

        if config is None:
            default_config = {...}
            # 这里默认配置会生成到用户的 config.toml 文件中
            self.sdk.config.setConfig("MyAdapter", default_config)
            return default_config
        return config

    class Send(BaseAdapter.Send):  # 继承BaseAdapter内置的Send类
        """
        Send消息发送DSL，支持四种调用方式(继承的Send类包含了To和Using方法):
        1. 指定类型和ID: To(type,id).Func() -> 设置_target_type和_target_id/_target_to
           示例: Send.To("group",123).Text("hi")
        2. 指定发送账号: Using(account_id).Func() -> 设置_account_id
           示例: Send.Using("bot1").Text("hi")
        3. 组合使用: Using(account_id).To(type,id).Func()
           示例: Send.Using("bot1").To("user","123").Text("hi")
        4. 直接调用: Func() -> 不设置目标属性
           示例: Send.Text("broadcast")
        """
        
        def Text(self, text: str):
            """发送文本消息（可重写实现）"""
            return asyncio.create_task(
                self._adapter.call_api(
                    endpoint="/send",
                    content=text,
                    recvId=self._target_id,    # 来自To()设置的属性
                    recvType=self._target_type # 来自To(type,id)设置的属性
                )
            )
            
        def Image(self, file: bytes):
            """发送图片消息"""
            return asyncio.create_task(
                self._adapter.call_api(
                    endpoint="/send_image",
                    file=file,
                    recvId=self._target_id,    # 自动使用To()设置的属性
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

调用方式支持以下组合：

1. 指定发送账号和接收目标：
```python
sdk.adapter.MyPlatform.Send.Using("bot1").To("user", "U1001").Text("你好")
```

2. 仅指定接收目标：
```python
sdk.adapter.MyPlatform.Send.To("user", "U1001").Text("你好")
```

3. 仅指定发送账号：
```python
sdk.adapter.MyPlatform.Send.Using("bot1").Text("广播消息")
```

4. 直接调用：
```python
sdk.adapter.MyPlatform.Send.Text("广播消息")
```

`Using`方法用于指定发送账号，会设置`self._account_id`属性，可以在后续API调用中使用。

---

## 5. 事件转换与路由注册

适配器需要处理平台原生事件并转换为OneBot12标准格式，同时需要向底层框架注册路由。以下是两种典型实现方式：

### 5.1 WebSocket 方式实现

```python
async def _ws_handler(self, websocket: WebSocket):
    """WebSocket连接处理器"""
    self.connection = websocket
    self.logger.info("客户端已连接")

    try:
        while True:
            data = await websocket.receive_text()
            try:
                event = json.loads(data)
                # 提交原生事件到适配器
                # 原生事件需要通过指定平台来获取 比如 sdk.adapter.MyPlatform.on("事件类型")
                self.emit(data.get("event_type"), data)

                # 转换为OneBot12标准事件
                onebot_event = self.convert(event)
                if onebot_event:
                    # 提交标准事件到框架 | 这里直接通过 sdk.adaoter.on("事件类型") 便可以获取到事件，但是需要判断字段里面的platform字段来区分适配器
                    await self.sdk.adapter.emit(onebot_event)
            except json.JSONDecodeError:
                self.logger.error(f"JSON解析失败: {data}")
    except WebSocketDisconnect:
        self.logger.info("客户端断开连接")
    finally:
        self.connection = None

async def start(self):
    """注册WebSocket路由"""
    from ErisPulse.Core import router
    router.register_websocket(
        module_name="myplatform",  # 适配器名
        path="/ws",  # 路由路径
        handler=self._ws_handler,  # 处理器
        auth_handler=self._auth_handler  # 认证处理器(可选)
    )
```

### 5.2 WebHook 方式实现

```python
async def _webhook_handler(self, request: Request):
    """WebHook请求处理器"""
    try:
        data = await request.json()

        # 提交原生事件到适配器
        # 原生事件需要通过指定平台来获取 比如 sdk.adapter.MyPlatform.on("事件类型")
        self.emit(data.get("event_type"), data)

        # 转换为OneBot12标准事件
        onebot_event = self.convert(data)=
        if onebot_event:
            # 提交标准事件到框架 | 这里直接通过 sdk.adaoter.on("事件类型") 便可以获取到事件，但是需要判断字段里面的platform字段来区分适配器
            await self.sdk.adapter.emit(onebot_event)
        return JSONResponse({"status": "ok"})
    except Exception as e:
        self.logger.error(f"处理WebHook失败: {str(e)}")
        return JSONResponse({"status": "failed"}, status_code=400)

async def start(self):
    """注册WebHook路由"""
    from ErisPulse.Core import router
    router.register_http_route(
        module_name="myplatform",  # 适配器名
        path="/webhook",  # 路由路径
        handler=self._webhook_handler,  # 处理器
        methods=["POST"]  # 支持的HTTP方法
    )
```

### 5.3 事件转换器实现

适配器应提供标准的事件转换器，将平台原生事件转换为OneBot12格式 具体实现请参考[事件转换标准文档](docs/AdapterStandards/EventConversion.md)：

```python
class MyPlatformConverter:
    def convert(self, raw_event: Dict) -> Optional[Dict]:
        """将平台原生事件转换为OneBot12标准格式"""
        if not isinstance(raw_event, dict):
            return None

        # 基础事件结构
        onebot_event = {
            "id": str(raw_event.get("event_id", uuid.uuid4())),
            "time": int(time.time()),
            "type": "",  # message/notice/request/meta_event
            "detail_type": "",
            "platform": "myplatform",
            "self": {
                "platform": "myplatform",
                "user_id": str(raw_event.get("bot_id", ""))
            },
            "myplatform_raw": raw_event  # 保留原始数据
        }

        # 根据事件类型分发处理
        event_type = raw_event.get("type")
        if event_type == "message":
            return self._handle_message(raw_event, onebot_event)
        elif event_type == "notice":
            return self._handle_notice(raw_event, onebot_event)
        
        return None
```

## 6. API响应标准

适配器的`call_api`方法必须返回符合以下标准的响应结构：

### 6.1 成功响应格式

```python
{
    "status": "ok",  # 必须
    "retcode": 0,  # 必须，0表示成功
    "data": {  # 必须，成功时返回的数据
        "message_id": "123456",  # 消息ID(如果有)
        "time": 1632847927.599013  # 时间戳(如果有)
    },
    "message": "",  # 必须，成功时为空字符串
    "message_id": "123456",  # 可选，消息ID
    "echo": "1234",  # 可选，当请求中包含echo时返回
    "myplatform_raw": {...}  # 可选，原始响应数据
}
```

### 6.2 失败响应格式

```python
{
    "status": "failed",  # 必须
    "retcode": 10003,  # 必须，非0错误码
    "data": None,  # 必须，失败时为null
    "message": "缺少必要参数",  # 必须，错误描述
    "message_id": "",  # 可选，失败时为空字符串
    "echo": "1234",  # 可选，当请求中包含echo时返回
    "myplatform_raw": {...}  # 可选，原始响应数据
}
```

### 6.3 实现示例

```python
async def call_api(self, endpoint: str, **params):
    try:
        # 调用平台API
        raw_response = await self._platform_api_call(endpoint, **params)
        
        # 标准化响应
        standardized = {
            "status": "ok" if raw_response["success"] else "failed",
            "retcode": 0 if raw_response["success"] else raw_response.get("code", 10001),
            "data": raw_response.get("data"),
            "message": raw_response.get("message", ""),
            "message_id": raw_response.get("data", {}).get("message_id", ""),
            "myplatform_raw": raw_response
        }
        
        if "echo" in params:
            standardized["echo"] = params["echo"]
            
        return standardized
        
    except Exception as e:
        return {
            "status": "failed",
            "retcode": 34000,  # 平台错误代码段
            "data": None,
            "message": str(e),
            "message_id": ""
        }
```

## 7. 错误代码规范

适配器应遵循以下错误代码范围：

| 代码范围 | 类型 | 说明 |
|---------|------|------|
| 0 | 成功 | 必须为0 |
| 1xxxx | 请求错误 | 无效参数、不支持的操作等 |
| 2xxxx | 处理器错误 | 适配器内部处理错误 |
| 3xxxx | 执行错误 | 平台API调用错误 |
| 34xxx | 平台错误 | 平台返回的错误 |

建议在适配器中定义常量：

```python
class ErrorCode:
    SUCCESS = 0
    INVALID_PARAMS = 10003
    UNSUPPORTED_ACTION = 10002
    INTERNAL_ERROR = 20001
    PLATFORM_ERROR = 34000
```

---

## 开发建议

### 1. 使用异步编程模型
- **优先使用异步库**：如 `aiohttp`、`asyncpg` 等，避免阻塞主线程。
- **合理使用事件循环**：确保异步函数正确地被 `await` 或调度为任务（`create_task`）。

### 2. 异常处理与日志记录
- **统一异常处理机制**：直接 `raise` 异常，上层会自动捕获并记录日志。
- **详细的日志输出**：在关键路径上打印调试日志，便于问题排查。

### 3. 模块化与解耦设计
- **职责单一原则**：每个模块/类只做一件事，降低耦合度。
- **依赖注入**：通过构造函数传递依赖对象（如 `sdk`），提高可测试性。

### 4. 性能优化
- **避免死循环**：避免无止境的循环导致阻塞或内存泄漏。
- **使用智能缓存**：对频繁查询的数据使用缓存，例如数据库查询结果、配置信息等。

### 5. 安全与隐私
- **敏感数据保护**：避免将密钥、密码等硬编码在代码中，使用sdk的配置模块。
- **输入验证**：对所有用户输入进行校验，防止注入攻击等安全问题。

---

*文档最后更新于 2025-08-11 14:43:21*

---

<a id="APIResponsemd"></a>
## API响应标准

# ErisPulse 适配器标准化返回规范

## 1. 说明
为什么会有这个规范？

为了确保各平台发送接口返回统一性与OneBot12兼容性，ErisPulse适配器在API响应格式上采用了OneBot12定义的消息发送返回结构标准。

但ErisPulse的协议有一些特殊性定义:
- 1. 基础字段中，message_id是必须的，但OneBot12标准中无此字段
- 2. 返回内容中需要添加 {platform_name}_raw 字段，用于存放原始响应数据

## 2. 基础返回结构
所有动作响应必须包含以下基础字段：

| 字段名 | 数据类型 | 必选 | 说明 |
|-------|---------|------|------|
| status | string | 是 | 执行状态，必须是"ok"或"failed" |
| retcode | int64 | 是 | 返回码，遵循OneBot12返回码规则 |
| data | any | 是 | 响应数据，成功时包含请求结果，失败时为null |
| message_id | string | 是 | 消息ID，用于标识消息, 没有则为空字符串 |
| message | string | 是 | 错误信息，成功时为空字符串 |
| {platform_name}_raw | any | 否 | 原始响应数据 |

可选字段：
| 字段名 | 数据类型 | 必选 | 说明 |
|-------|---------|------|------|
| echo | string | 否 | 当请求中包含echo字段时，原样返回 |

## 3. 完整字段规范

### 3.1 通用字段

#### 成功响应示例
```json
{
    "status": "ok",
    "retcode": 0,
    "data": {
        "message_id": "1234",
        "time": 1632847927.599013
    },
    "message_id": "1234",
    "message": "",
    "echo": "1234",
    "telegram_raw": {...}
}
```

#### 失败响应示例
```json
{
    "status": "failed",
    "retcode": 10003,
    "data": null,
    "message_id": "",
    "message": "缺少必要参数: user_id",
    "echo": "1234",
    "telegram_raw": {...}
}
```

### 3.2 返回码规范

#### 0 成功（OK）
- 0: 成功（OK）

#### 1xxxx 动作请求错误（Request Error）
| 错误码 | 错误名 | 说明 |
|-------|-------|------|
| 10001 | Bad Request | 无效的动作请求 |
| 10002 | Unsupported Action | 不支持的动作请求 |
| 10003 | Bad Param | 无效的动作请求参数 |
| 10004 | Unsupported Param | 不支持的动作请求参数 |
| 10005 | Unsupported Segment | 不支持的消息段类型 |
| 10006 | Bad Segment Data | 无效的消息段参数 |
| 10007 | Unsupported Segment Data | 不支持的消息段参数 |
| 10101 | Who Am I | 未指定机器人账号 |
| 10102 | Unknown Self | 未知的机器人账号 |

#### 2xxxx 动作处理器错误（Handler Error）
| 错误码 | 错误名 | 说明 |
|-------|-------|------|
| 20001 | Bad Handler | 动作处理器实现错误 |
| 20002 | Internal Handler Error | 动作处理器运行时抛出异常 |

#### 3xxxx 动作执行错误（Execution Error）
| 错误码范围 | 错误类型 | 说明 |
|-----------|---------|------|
| 31xxx | Database Error | 数据库错误 |
| 32xxx | Filesystem Error | 文件系统错误 |
| 33xxx | Network Error | 网络错误 |
| 34xxx | Platform Error | 机器人平台错误 |
| 35xxx | Logic Error | 动作逻辑错误 |
| 36xxx | I Am Tired | 实现决定罢工 |

#### 保留错误段
- 4xxxx、5xxxx: 保留段，不应使用
- 6xxxx～9xxxx: 其他错误段，供实现自定义使用

## 4. 实现要求
1. 所有响应必须包含status、retcode、data和message字段
2. 当请求中包含非空echo字段时，响应必须包含相同值的echo字段
3. 返回码必须严格遵循OneBot12规范
4. 错误信息(message)应当是人类可读的描述

## 5. 注意事项
- 对于3xxxx错误码，低三位可由实现自行定义
- 避免使用保留错误段(4xxxx、5xxxx)
- 错误信息应当简洁明了，便于调试

---

<a id="EventConversionmd"></a>
## 事件转换标准

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

### 2.3 非标准字段（非必须，但建议实现）
|字段|触发类型|示例|
|-|-|-|
|user_nickname|涉及用户|"用户昵称"|

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
  "user_nickname": "YingXinche",
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
  "user_nickname": "YingXinche",
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
  "user_nickname": "YingXinche",
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

---

# API参考

## API文档目录

- [ErisPulse\Core\Event\__init__.md](#ErisPulse_Core_Event___init__)
- [ErisPulse\Core\Event\base.md](#ErisPulse_Core_Event_base)
- [ErisPulse\Core\Event\command.md](#ErisPulse_Core_Event_command)
- [ErisPulse\Core\Event\exceptions.md](#ErisPulse_Core_Event_exceptions)
- [ErisPulse\Core\Event\message.md](#ErisPulse_Core_Event_message)
- [ErisPulse\Core\Event\meta.md](#ErisPulse_Core_Event_meta)
- [ErisPulse\Core\Event\notice.md](#ErisPulse_Core_Event_notice)
- [ErisPulse\Core\Event\request.md](#ErisPulse_Core_Event_request)
- [ErisPulse\Core\adapter.md](#ErisPulse_Core_adapter)
- [ErisPulse\Core\config.md](#ErisPulse_Core_config)
- [ErisPulse\Core\env.md](#ErisPulse_Core_env)
- [ErisPulse\Core\erispulse_config.md](#ErisPulse_Core_erispulse_config)
- [ErisPulse\Core\exceptions.md](#ErisPulse_Core_exceptions)
- [ErisPulse\Core\logger.md](#ErisPulse_Core_logger)
- [ErisPulse\Core\module.md](#ErisPulse_Core_module)
- [ErisPulse\Core\module_registry.md](#ErisPulse_Core_module_registry)
- [ErisPulse\Core\router.md](#ErisPulse_Core_router)
- [ErisPulse\Core\storage.md](#ErisPulse_Core_storage)
- [ErisPulse\__init__.md](#ErisPulse___init__)
- [ErisPulse\__main__.md](#ErisPulse___main__)

---

<a id="ErisPulse_Core_Event___init__"></a>
## ErisPulse\Core\Event\__init__.md


<sup>更新时间: 2025-08-18 15:39:00</sup>

---

## 模块概述


ErisPulse 事件处理模块

提供统一的事件处理接口，支持命令、消息、通知、请求和元事件处理

<div class='admonition tip'><p class='admonition-title'>提示</p><p>1. 所有事件处理都基于OneBot12标准事件格式
2. 通过装饰器方式注册事件处理器
3. 支持优先级和条件过滤</p></div>

---

## 函数列表

### `_setup_default_config()`

<div class='admonition warning'><p class='admonition-title'>内部方法</p><p></p></div>
设置默认配置

---

<sub>文档最后更新于 2025-08-18 15:39:00</sub>

<a id="ErisPulse_Core_Event_base"></a>
## ErisPulse\Core\Event\base.md


<sup>更新时间: 2025-08-18 15:39:00</sup>

---

## 模块概述


ErisPulse 事件处理基础模块

提供事件处理的核心功能，包括事件注册和处理

<div class='admonition tip'><p class='admonition-title'>提示</p><p>1. 所有事件处理都基于OneBot12标准事件格式
2. 通过适配器系统进行事件分发和接收</p></div>

---

## 类列表

### `class BaseEventHandler`

基础事件处理器

提供事件处理的基本功能，包括处理器注册等


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

##### `__call__(priority: int = 0, condition: Callable = None)`

装饰器方式注册事件处理器

:param priority: 处理器优先级
:param condition: 处理器条件函数
:return: 装饰器函数

---

##### async `async _process_event(event: Dict[str, Any])`

处理事件

<div class='admonition warning'><p class='admonition-title'>内部方法</p><p></p></div>
内部使用的方法，用于处理事件

:param event: 事件数据

---

##### `unregister(handler: Callable)`

注销事件处理器

:param handler: 要注销的事件处理器

---

<sub>文档最后更新于 2025-08-18 15:39:00</sub>

<a id="ErisPulse_Core_Event_command"></a>
## ErisPulse\Core\Event\command.md


<sup>更新时间: 2025-08-18 15:39:00</sup>

---

## 模块概述


ErisPulse 命令处理模块

提供基于装饰器的命令注册和处理功能

<div class='admonition tip'><p class='admonition-title'>提示</p><p>1. 支持命令别名和命令组
2. 支持命令权限控制
3. 支持命令帮助系统</p></div>

---

<sub>文档最后更新于 2025-08-18 15:39:00</sub>

<a id="ErisPulse_Core_Event_exceptions"></a>
## ErisPulse\Core\Event\exceptions.md


<sup>更新时间: 2025-08-18 15:39:00</sup>

---

## 模块概述


ErisPulse 事件系统异常处理模块

提供事件系统中可能发生的各种异常类型定义

---

## 类列表

### `class EventException(Exception)`

事件系统基础异常

所有事件系统相关异常的基类


### `class CommandException(EventException)`

命令处理异常

当命令处理过程中发生错误时抛出


### `class EventHandlerException(EventException)`

事件处理器异常

当事件处理器执行过程中发生错误时抛出


### `class EventNotFoundException(EventException)`

事件未找到异常

当尝试获取不存在的事件处理器时抛出


<sub>文档最后更新于 2025-08-18 15:39:00</sub>

<a id="ErisPulse_Core_Event_message"></a>
## ErisPulse\Core\Event\message.md


<sup>更新时间: 2025-08-18 15:39:00</sup>

---

## 模块概述


ErisPulse 消息处理模块

提供基于装饰器的消息事件处理功能

<div class='admonition tip'><p class='admonition-title'>提示</p><p>1. 支持私聊、群聊消息分类处理
2. 支持@消息特殊处理
3. 支持自定义条件过滤</p></div>

---

<sub>文档最后更新于 2025-08-18 15:39:00</sub>

<a id="ErisPulse_Core_Event_meta"></a>
## ErisPulse\Core\Event\meta.md


<sup>更新时间: 2025-08-18 15:39:00</sup>

---

## 模块概述


ErisPulse 元事件处理模块

提供基于装饰器的元事件处理功能

<div class='admonition tip'><p class='admonition-title'>提示</p><p>1. 支持连接、断开连接等生命周期事件
2. 适用于系统状态监控和初始化操作</p></div>

---

<sub>文档最后更新于 2025-08-18 15:39:00</sub>

<a id="ErisPulse_Core_Event_notice"></a>
## ErisPulse\Core\Event\notice.md


<sup>更新时间: 2025-08-18 15:39:00</sup>

---

## 模块概述


ErisPulse 通知处理模块

提供基于装饰器的通知事件处理功能

<div class='admonition tip'><p class='admonition-title'>提示</p><p>1. 支持好友、群组等不同类型通知
2. 支持成员变动等细粒度事件</p></div>

---

<sub>文档最后更新于 2025-08-18 15:39:00</sub>

<a id="ErisPulse_Core_Event_request"></a>
## ErisPulse\Core\Event\request.md


<sup>更新时间: 2025-08-18 15:39:00</sup>

---

## 模块概述


ErisPulse 请求处理模块

提供基于装饰器的请求事件处理功能

<div class='admonition tip'><p class='admonition-title'>提示</p><p>1. 支持好友请求、群邀请等不同类型请求
2. 可以通过返回特定值来同意或拒绝请求</p></div>

---

<sub>文档最后更新于 2025-08-18 15:39:00</sub>

<a id="ErisPulse_Core_adapter"></a>
## ErisPulse\Core\adapter.md


<sup>更新时间: 2025-08-18 15:39:00</sup>

---

## 模块概述


ErisPulse 适配器系统

提供平台适配器基类、消息发送DSL和适配器管理功能。支持多平台消息处理、事件驱动和生命周期管理。

<div class='admonition tip'><p class='admonition-title'>提示</p><p>1. 适配器必须继承BaseAdapter并实现必要方法
2. 使用SendDSL实现链式调用风格的消息发送接口
3. 适配器管理器支持多平台适配器的注册和生命周期管理
4. 支持OneBot12协议的事件处理</p></div>

---

## 类列表

### `class SendDSLBase`

消息发送DSL基类

用于实现 Send.To(...).Func(...) 风格的链式调用接口

<div class='admonition tip'><p class='admonition-title'>提示</p><p>1. 子类应实现具体的消息发送方法(如Text, Image等)
2. 通过__getattr__实现动态方法调用</p></div>


#### 方法列表

##### `__init__(adapter: 'BaseAdapter', target_type: Optional[str] = None, target_id: Optional[str] = None, account_id: Optional[str] = None)`

初始化DSL发送器

:param adapter: 所属适配器实例
:param target_type: 目标类型(可选)
:param target_id: 目标ID(可选)
:param _account_id: 发送账号(可选)

---

##### `To(target_type: str = None, target_id: Union[str, int] = None)`

设置消息目标

:param target_type: 目标类型(可选)
:param target_id: 目标ID(可选)
:return: SendDSL实例

<details class='example'><summary>示例</summary>

```python
>>> adapter.Send.To("user", "123").Text("Hello")
>>> adapter.Send.To("123").Text("Hello")  # 简化形式
```
</details>

---

##### `Using(account_id: Union[str, int])`

设置发送账号

:param _account_id: 发送账号
:return: SendDSL实例

<details class='example'><summary>示例</summary>

```python
>>> adapter.Send.Using("bot1").To("123").Text("Hello")
>>> adapter.Send.To("123").Using("bot1").Text("Hello")  # 支持乱序
```
</details>

---

### `class BaseAdapter`

适配器基类

提供与外部平台交互的标准接口，子类必须实现必要方法

<div class='admonition tip'><p class='admonition-title'>提示</p><p>1. 必须实现call_api, start和shutdown方法
2. 可以自定义Send类实现平台特定的消息发送逻辑
3. 通过on装饰器注册事件处理器
4. 支持OneBot12协议的事件处理</p></div>


#### 方法列表

##### `__init__()`

初始化适配器

---

##### `on(event_type: str = '*')`

适配器事件监听装饰器

:param event_type: 事件类型
:return: 装饰器函数

---

##### `middleware(func: Callable)`

添加中间件处理器

:param func: 中间件函数
:return: 中间件函数

<details class='example'><summary>示例</summary>

```python
>>> @adapter.middleware
>>> async def log_middleware(data):
>>>     print(f"处理数据: {data}")
>>>     return data
```
</details>

---

##### async `async call_api(endpoint: str)`

调用平台API的抽象方法

:param endpoint: API端点
:param params: API参数
:return: API调用结果
<dt>异常</dt><dd><code>NotImplementedError</code> 必须由子类实现</dd>

---

##### async `async start()`

启动适配器的抽象方法

<dt>异常</dt><dd><code>NotImplementedError</code> 必须由子类实现</dd>

---

##### async `async shutdown()`

关闭适配器的抽象方法

<dt>异常</dt><dd><code>NotImplementedError</code> 必须由子类实现</dd>

---

##### async `async emit(event_type: str, data: Any)`

触发原生协议事件

:param event_type: 事件类型
:param data: 事件数据

<details class='example'><summary>示例</summary>

```python
>>> await adapter.emit("message", {"text": "Hello"})
```
</details>

---

##### async `async send(target_type: str, target_id: str, message: Any)`

发送消息的便捷方法

:param target_type: 目标类型
:param target_id: 目标ID
:param message: 消息内容
:param kwargs: 其他参数
    - method: 发送方法名(默认为"Text")
:return: 发送结果

<dt>异常</dt><dd><code>AttributeError</code> 当发送方法不存在时抛出</dd>
    
<details class='example'><summary>示例</summary>

```python
>>> await adapter.send("user", "123", "Hello")
>>> await adapter.send("group", "456", "Hello", method="Markdown")
```
</details>

---

### `class AdapterManager`

适配器管理器

管理多个平台适配器的注册、启动和关闭

<div class='admonition tip'><p class='admonition-title'>提示</p><p>1. 通过register方法注册适配器
2. 通过startup方法启动适配器
3. 通过shutdown方法关闭所有适配器
4. 通过on装饰器注册OneBot12协议事件处理器</p></div>


#### 方法列表

##### `Adapter()`

获取BaseAdapter类，用于访问原始事件监听

:return: BaseAdapter类

<details class='example'><summary>示例</summary>

```python
>>> @sdk.adapter.Adapter.on("raw_event")
>>> async def handle_raw(data):
>>>     print("收到原始事件:", data)
```
</details>

---

##### `on(event_type: str = '*')`

OneBot12协议事件监听装饰器

:param event_type: OneBot12事件类型
:return: 装饰器函数

<details class='example'><summary>示例</summary>

```python
>>> @sdk.adapter.on("message")
>>> async def handle_message(data):
>>>     print(f"收到OneBot12消息: {data}")
```
</details>

---

##### `middleware(func: Callable)`

添加OneBot12中间件处理器

:param func: 中间件函数
:return: 中间件函数

<details class='example'><summary>示例</summary>

```python
>>> @sdk.adapter.middleware
>>> async def onebot_middleware(data):
>>>     print("处理OneBot12数据:", data)
>>>     return data
```
</details>

---

##### async `async emit(data: Any)`

提交OneBot12协议事件到指定平台

:param platform: 平台名称
:param event_type: OneBot12事件类型
:param data: 符合OneBot12标准的事件数据

<dt>异常</dt><dd><code>ValueError</code> 当平台未注册时抛出</dd>
    
<details class='example'><summary>示例</summary>

```python
>>> await sdk.adapter.emit("MyPlatform", "message", {
>>>     "id": "123",
>>>     "time": 1620000000,
>>>     "type": "message",
>>>     "detail_type": "private",
>>>     "message": [{"type": "text", "data": {"text": "Hello"}}]
>>> })
```
</details>

---

##### `register(platform: str, adapter_class: Type[BaseAdapter])`

注册新的适配器类

:param platform: 平台名称
:param adapter_class: 适配器类
:return: 注册是否成功

<dt>异常</dt><dd><code>TypeError</code> 当适配器类无效时抛出</dd>
    
<details class='example'><summary>示例</summary>

```python
>>> adapter.register("MyPlatform", MyPlatformAdapter)
```
</details>

---

##### async `async startup(platforms: List[str] = None)`

启动指定的适配器

:param platforms: 要启动的平台列表，None表示所有平台

<dt>异常</dt><dd><code>ValueError</code> 当平台未注册时抛出</dd>
    
<details class='example'><summary>示例</summary>

```python
>>> # 启动所有适配器
>>> await adapter.startup()
>>> # 启动指定适配器
>>> await adapter.startup(["Platform1", "Platform2"])
```
</details>

---

##### async `async _run_adapter(adapter: BaseAdapter, platform: str)`

<div class='admonition warning'><p class='admonition-title'>内部方法</p><p></p></div>
运行适配器实例

:param adapter: 适配器实例
:param platform: 平台名称

---

##### async `async shutdown()`

关闭所有适配器

<details class='example'><summary>示例</summary>

```python
>>> await adapter.shutdown()
```
</details>

---

##### `get(platform: str)`

获取指定平台的适配器实例

:param platform: 平台名称
:return: 适配器实例或None
    
<details class='example'><summary>示例</summary>

```python
>>> adapter = adapter.get("MyPlatform")
```
</details>

---

##### `__getattr__(platform: str)`

通过属性访问获取适配器实例

:param platform: 平台名称
:return: 适配器实例

<dt>异常</dt><dd><code>AttributeError</code> 当平台未注册时抛出</dd>
    
<details class='example'><summary>示例</summary>

```python
>>> adapter = adapter.MyPlatform
```
</details>

---

##### `platforms()`

获取所有已注册的平台列表

:return: 平台名称列表
    
<details class='example'><summary>示例</summary>

```python
>>> print("已注册平台:", adapter.platforms)
```
</details>

---

<sub>文档最后更新于 2025-08-18 15:39:00</sub>

<a id="ErisPulse_Core_config"></a>
## ErisPulse\Core\config.md


<sup>更新时间: 2025-08-18 15:39:00</sup>

---

## 模块概述


ErisPulse 配置中心

集中管理所有配置项，避免循环导入问题
提供自动补全缺失配置项的功能

---

<sub>文档最后更新于 2025-08-18 15:39:00</sub>

<a id="ErisPulse_Core_env"></a>
## ErisPulse\Core\env.md


<sup>更新时间: 2025-08-18 15:39:00</sup>

---

## 模块概述


ErisPulse 环境模块 (已弃用)

此模块已重命名为 storage，为保持向后兼容性而保留。
建议使用 from ErisPulse.Core import storage 替代 from ErisPulse.Core import env

<div class='admonition attention'><p class='admonition-title'>已弃用</p><p>请使用 storage 模块替代</p></div>

---

<sub>文档最后更新于 2025-08-18 15:39:00</sub>

<a id="ErisPulse_Core_erispulse_config"></a>
## ErisPulse\Core\erispulse_config.md


<sup>更新时间: 2025-08-18 15:39:00</sup>

---

## 模块概述


ErisPulse 框架配置管理

专门管理 ErisPulse 框架自身的配置项。

---

## 函数列表

### `_ensure_erispulse_config_structure(config_dict: Dict[str, Any])`

确保 ErisPulse 配置结构完整，补全缺失的配置项

:param config_dict: 当前配置
:return: 补全后的完整配置

---

### `get_erispulse_config()`

获取 ErisPulse 框架配置，自动补全缺失的配置项并保存

:return: 完整的 ErisPulse 配置字典

---

### `update_erispulse_config(new_config: Dict[str, Any])`

更新 ErisPulse 配置，自动补全缺失的配置项

:param new_config: 新的配置字典
:return: 是否更新成功

---

### `get_server_config()`

获取服务器配置，确保结构完整

:return: 服务器配置字典

---

### `get_logger_config()`

获取日志配置，确保结构完整

:return: 日志配置字典

---

<sub>文档最后更新于 2025-08-18 15:39:00</sub>

<a id="ErisPulse_Core_exceptions"></a>
## ErisPulse\Core\exceptions.md


<sup>更新时间: 2025-08-18 15:39:00</sup>

---

## 模块概述


ErisPulse 全局异常处理系统

提供统一的异常捕获和格式化功能，支持同步和异步代码的异常处理。

---

## 函数列表

### `global_exception_handler(exc_type: Type[Exception], exc_value: Exception, exc_traceback: Any)`

全局异常处理器

:param exc_type: 异常类型
:param exc_value: 异常值
:param exc_traceback: 追踪信息

---

### `async_exception_handler(loop: asyncio.AbstractEventLoop, context: Dict[str, Any])`

异步异常处理器

:param loop: 事件循环
:param context: 上下文字典

---

### `setup_async_loop(loop: asyncio.AbstractEventLoop = None)`

为指定的事件循环设置异常处理器

:param loop: 事件循环实例，如果为None则使用当前事件循环

---

<sub>文档最后更新于 2025-08-18 15:39:00</sub>

<a id="ErisPulse_Core_logger"></a>
## ErisPulse\Core\logger.md


<sup>更新时间: 2025-08-18 15:39:00</sup>

---

## 模块概述


ErisPulse 日志系统

提供模块化日志记录功能，支持多级日志、模块过滤和内存存储。

<div class='admonition tip'><p class='admonition-title'>提示</p><p>1. 支持按模块设置不同日志级别
2. 日志可存储在内存中供后续分析
3. 自动识别调用模块名称</p></div>

---

## 类列表

### `class Logger`

日志管理器

提供模块化日志记录和存储功能

<div class='admonition tip'><p class='admonition-title'>提示</p><p>1. 使用set_module_level设置模块日志级别
2. 使用get_logs获取历史日志
3. 支持标准日志级别(DEBUG, INFO等)</p></div>


#### 方法列表

##### `set_memory_limit(limit: int)`

设置日志内存存储上限

:param limit: 日志存储上限
:return: bool 设置是否成功

---

##### `set_level(level: str)`

设置全局日志级别

:param level: 日志级别(DEBUG/INFO/WARNING/ERROR/CRITICAL)
:return: bool 设置是否成功

---

##### `set_module_level(module_name: str, level: str)`

设置指定模块日志级别

:param module_name: 模块名称
:param level: 日志级别(DEBUG/INFO/WARNING/ERROR/CRITICAL)
:return: bool 设置是否成功

---

##### `set_output_file(path)`

设置日志输出

:param path: 日志文件路径 Str/List
:return: bool 设置是否成功

---

##### `save_logs(path)`

保存所有在内存中记录的日志

:param path: 日志文件路径 Str/List
:return: bool 设置是否成功

---

##### `get_logs(module_name: str = None)`

获取日志内容

:param module_name (可选): 模块名称
:return: dict 日志内容

---

##### `get_child(child_name: str = None)`

获取子日志记录器

:param child_name: 子模块名称(可选)
:return: LoggerChild 子日志记录器实例

---

### `class LoggerChild`

子日志记录器

用于创建具有特定名称的子日志记录器，仅改变模块名称，其他功能全部委托给父日志记录器


#### 方法列表

##### `__init__(parent_logger: Logger, name: str)`

初始化子日志记录器

:param parent_logger: 父日志记录器实例
:param name: 子日志记录器名称

---

##### `get_child(child_name: str)`

获取子日志记录器的子记录器

:param child_name: 子模块名称
:return: LoggerChild 子日志记录器实例

---

<sub>文档最后更新于 2025-08-18 15:39:00</sub>

<a id="ErisPulse_Core_module"></a>
## ErisPulse\Core\module.md


<sup>更新时间: 2025-08-18 15:39:00</sup>

---

## 模块概述


ErisPulse 模块管理模块

提供便捷的模块访问接口

---

## 类列表

### `class ModuleManager`

模块管理器

提供便捷的模块访问接口，支持获取模块实例、检查模块状态等操作


#### 方法列表

##### `get(module_name: str)`

获取指定模块的实例

<dt><code>module_name</code> <span class='type-hint'>str</span></dt><dd>模块名称</dd>
<dt>返回值</dt><dd><span class='type-hint'>Any</span> 模块实例或None</dd>

---

##### `exists(module_name: str)`

检查模块是否存在

<dt><code>module_name</code> <span class='type-hint'>str</span></dt><dd>模块名称</dd>
<dt>返回值</dt><dd><span class='type-hint'>bool</span> 模块是否存在</dd>

---

##### `is_enabled(module_name: str)`

检查模块是否启用

<dt><code>module_name</code> <span class='type-hint'>str</span></dt><dd>模块名称</dd>
<dt>返回值</dt><dd><span class='type-hint'>bool</span> 模块是否启用</dd>

---

##### `enable(module_name: str)`

启用模块

<dt><code>module_name</code> <span class='type-hint'>str</span></dt><dd>模块名称</dd>
<dt>返回值</dt><dd><span class='type-hint'>bool</span> 操作是否成功</dd>

---

##### `disable(module_name: str)`

禁用模块

<dt><code>module_name</code> <span class='type-hint'>str</span></dt><dd>模块名称</dd>
<dt>返回值</dt><dd><span class='type-hint'>bool</span> 操作是否成功</dd>

---

##### `list_modules()`

列出所有模块信息

<dt>返回值</dt><dd><span class='type-hint'>Dict[str, Dict[str, Any</span> ]] 模块信息字典</dd>

---

##### `get_info(module_name: str)`

获取模块详细信息

<dt><code>module_name</code> <span class='type-hint'>str</span></dt><dd>模块名称</dd>
<dt>返回值</dt><dd><span class='type-hint'>Optional[Dict[str, Any</span> ]] 模块信息字典</dd>

---

##### `__getattr__(module_name: str)`

通过属性访问获取模块实例

<dt><code>module_name</code> <span class='type-hint'>str</span></dt><dd>模块名称</dd>
<dt>返回值</dt><dd><span class='type-hint'>Any</span> 模块实例</dd>
<dt>异常</dt><dd><code>AttributeError</code> 当模块不存在或未启用时</dd>

---

##### `__contains__(module_name: str)`

检查模块是否存在且处于启用状态

<dt><code>module_name</code> <span class='type-hint'>str</span></dt><dd>模块名称</dd>
<dt>返回值</dt><dd><span class='type-hint'>bool</span> 模块是否存在且启用</dd>

---

<sub>文档最后更新于 2025-08-18 15:39:00</sub>

<a id="ErisPulse_Core_module_registry"></a>
## ErisPulse\Core\module_registry.md


<sup>更新时间: 2025-08-18 15:39:00</sup>

---

## 模块概述


ErisPulse 模块管理器

提供模块的注册、状态管理和依赖关系处理功能。支持模块的启用/禁用、版本控制和依赖解析。

<div class='admonition tip'><p class='admonition-title'>提示</p><p>1. 使用模块前缀区分不同模块的配置
2. 支持模块状态持久化存储
3. 自动处理模块间的依赖关系</p></div>

---

## 类列表

### `class ModuleRegistry`

ErisPulse 模块注册表

管理所有模块的注册信息和启用状态

<div class='admonition tip'><p class='admonition-title'>提示</p><p>1. 模块信息通过 set_module/get_module 管理
2. 模块状态通过 set_module_status/get_module_status 控制
3. 支持批量操作模块信息</p></div>


#### 方法列表

##### `_ensure_prefixes()`

<div class='admonition warning'><p class='admonition-title'>内部方法</p><p></p></div>
确保模块前缀配置存在

---

##### `module_prefix()`

获取模块数据前缀

:return: 模块数据前缀字符串

---

##### `status_prefix()`

获取模块状态前缀

:return: 模块状态前缀字符串

---

##### `set_module_status(module_name: str, status: bool)`

设置模块启用状态

<dt><code>module_name</code> <span class='type-hint'>str</span></dt><dd>模块名称</dd>
<dt><code>status</code> <span class='type-hint'>bool</span></dt><dd>启用状态 (True=启用, False=禁用)</dd>

<details class='example'><summary>示例</summary>

```python
>>> # 启用模块
>>> module_registry.set_module_status("MyModule", True)
>>> # 禁用模块
>>> module_registry.set_module_status("MyModule", False)
```
</details>

---

##### `get_module_status(module_name: str)`

获取模块启用状态

<dt><code>module_name</code> <span class='type-hint'>str</span></dt><dd>模块名称</dd>
<dt>返回值</dt><dd><span class='type-hint'>bool</span> 模块是否启用</dd>

<details class='example'><summary>示例</summary>

```python
>>> if module_registry.get_module_status("MyModule"):
>>>     print("模块已启用")
```
</details>

---

##### `set_module(module_name: str, module_info: Dict[str, Any])`

注册或更新模块信息

<dt><code>module_name</code> <span class='type-hint'>str</span></dt><dd>模块名称</dd>
<dt><code>module_info</code> <span class='type-hint'>Dict[str, Any</span></dt><dd>] 模块信息字典</dd>
    必须包含 version 和 description 字段

<details class='example'><summary>示例</summary>

```python
>>> module_registry.set_module("MyModule", {
>>>     "version": "1.0.0",
>>>     "description": "我的模块",
>>>     "dependencies": [],
>>>     "author": "开发者",
>>>     "license": "MIT"
>>> })
```
</details>

---

##### `get_module(module_name: str)`

获取模块信息

<dt><code>module_name</code> <span class='type-hint'>str</span></dt><dd>模块名称</dd>
<dt>返回值</dt><dd><span class='type-hint'>Optional[Dict[str, Any</span> ]] 模块信息字典或None</dd>

<details class='example'><summary>示例</summary>

```python
>>> module_info = module_registry.get_module("MyModule")
>>> if module_info:
>>>     print(f"模块版本: {module_info.get('version')}")
```
</details>

---

##### `set_all_modules(modules_info: Dict[str, Dict[str, Any]])`

批量设置模块信息

<dt><code>modules_info</code> <span class='type-hint'>Dict[str, Dict[str, Any</span></dt><dd>]] 模块信息字典</dd>
    格式: {模块名: 模块信息}

<details class='example'><summary>示例</summary>

```python
>>> module_registry.set_all_modules({
>>>     "Module1": {"version": "1.0", "status": True},
>>>     "Module2": {"version": "2.0", "status": False}
>>> })
```
</details>

---

##### `get_all_modules()`

获取所有已注册模块信息

<dt>返回值</dt><dd><span class='type-hint'>Dict[str, Dict[str, Any</span> ]] 所有模块信息字典</dd>

<details class='example'><summary>示例</summary>

```python
>>> all_modules = module_registry.get_all_modules()
>>> for name, info in all_modules.items():
>>>     print(f"{name}: {info.get('status')}")
```
</details>

---

##### `update_module(module_name: str, module_info: Dict[str, Any])`

更新模块信息

:param module_name: 模块名称
:param module_info: 完整的模块信息字典

---

##### `remove_module(module_name: str)`

移除模块注册信息

<dt><code>module_name</code> <span class='type-hint'>str</span></dt><dd>模块名称</dd>
<dt>返回值</dt><dd><span class='type-hint'>bool</span> 是否成功移除</dd>

<details class='example'><summary>示例</summary>

```python
>>> if module_registry.remove_module("OldModule"):
>>>     print("模块已移除")
```
</details>

---

##### `update_prefixes(module_prefix: Optional[str] = None, status_prefix: Optional[str] = None)`

更新模块存储前缀配置

<dt><code>module_prefix</code> <span class='type-hint'>Optional[str</span></dt><dd>] 模块数据前缀 (默认: "erispulse.data.modules.info:")</dd>
<dt><code>status_prefix</code> <span class='type-hint'>Optional[str</span></dt><dd>] 模块状态前缀 (默认: "erispulse.data.modules.status:")</dd>

<details class='example'><summary>示例</summary>

```python
>>> # 更新模块前缀
>>> module_registry.update_prefixes(
>>>     module_prefix="custom.module.data:",
>>>     status_prefix="custom.module.status:"
>>> )
```
</details>

---

<sub>文档最后更新于 2025-08-18 15:39:00</sub>

<a id="ErisPulse_Core_router"></a>
## ErisPulse\Core\router.md


<sup>更新时间: 2025-08-18 15:39:00</sup>

---

## 模块概述


ErisPulse 路由系统

提供统一的HTTP和WebSocket路由管理，支持多适配器路由注册和生命周期管理。

<div class='admonition tip'><p class='admonition-title'>提示</p><p>1. 适配器只需注册路由，无需自行管理服务器
2. WebSocket支持自定义认证逻辑
3. 兼容FastAPI 0.68+ 版本</p></div>

---

## 类列表

### `class RouterManager`

路由管理器

<div class='admonition tip'><p class='admonition-title'>提示</p><p>核心功能：
- HTTP/WebSocket路由注册
- 生命周期管理
- 统一错误处理</p></div>


#### 方法列表

##### `__init__()`

初始化路由管理器

<div class='admonition tip'><p class='admonition-title'>提示</p><p>会自动创建FastAPI实例并设置核心路由</p></div>

---

##### `_setup_core_routes()`

设置系统核心路由

<div class='admonition warning'><p class='admonition-title'>内部方法</p><p></p></div>
此方法仅供内部使用
{!--< /internal-use >!--}

---

##### `register_http_route(module_name: str, path: str, handler: Callable, methods: List[str] = ['POST'])`

注册HTTP路由

:param module_name: str 模块名称
:param path: str 路由路径
:param handler: Callable 处理函数
:param methods: List[str] HTTP方法列表(默认["POST"])

<dt>异常</dt><dd><code>ValueError</code> 当路径已注册时抛出</dd>

---

##### `register_webhook()`

兼容性方法：注册HTTP路由（适配器旧接口）

---

##### `register_websocket(module_name: str, path: str, handler: Callable[[WebSocket], Awaitable[Any]], auth_handler: Optional[Callable[[WebSocket], Awaitable[bool]]] = None)`

注册WebSocket路由

:param module_name: str 模块名称
:param path: str WebSocket路径
:param handler: Callable[[WebSocket], Awaitable[Any]] 主处理函数
:param auth_handler: Optional[Callable[[WebSocket], Awaitable[bool]]] 认证函数

<dt>异常</dt><dd><code>ValueError</code> 当路径已注册时抛出</dd>

---

##### `get_app()`

获取FastAPI应用实例

:return: FastAPI应用实例

---

##### async `async start(host: str = '0.0.0.0', port: int = 8000, ssl_certfile: Optional[str] = None, ssl_keyfile: Optional[str] = None)`

启动路由服务器

:param host: str 监听地址(默认"0.0.0.0")
:param port: int 监听端口(默认8000)
:param ssl_certfile: Optional[str] SSL证书路径
:param ssl_keyfile: Optional[str] SSL密钥路径

<dt>异常</dt><dd><code>RuntimeError</code> 当服务器已在运行时抛出</dd>

---

##### async `async stop()`

停止服务器

---

<sub>文档最后更新于 2025-08-18 15:39:00</sub>

<a id="ErisPulse_Core_storage"></a>
## ErisPulse\Core\storage.md


<sup>更新时间: 2025-08-18 15:39:00</sup>

---

## 模块概述


ErisPulse 存储管理模块

提供键值存储、事务支持、快照和恢复功能，用于管理框架运行时数据。
基于SQLite实现持久化存储，支持复杂数据类型和原子操作。

<div class='admonition tip'><p class='admonition-title'>提示</p><p>1. 支持JSON序列化存储复杂数据类型
2. 提供事务支持确保数据一致性
3. 自动快照功能防止数据丢失</p></div>

---

## 类列表

### `class StorageManager`

存储管理器

单例模式实现，提供键值存储的增删改查、事务和快照管理

<div class='admonition tip'><p class='admonition-title'>提示</p><p>1. 使用get/set方法操作存储项
2. 使用transaction上下文管理事务
3. 使用snapshot/restore管理数据快照</p></div>


#### 方法列表

##### `_init_db()`

<div class='admonition warning'><p class='admonition-title'>内部方法</p><p></p></div>
初始化数据库

---

##### `get(key: str, default: Any = None)`

获取存储项的值

:param key: 存储项键名
:param default: 默认值(当键不存在时返回)
:return: 存储项的值

<details class='example'><summary>示例</summary>

```python
>>> timeout = storage.get("network.timeout", 30)
>>> user_settings = storage.get("user.settings", {})
```
</details>

---

##### `get_all_keys()`

获取所有存储项的键名

:return: 键名列表

<details class='example'><summary>示例</summary>

```python
>>> all_keys = storage.get_all_keys()
>>> print(f"共有 {len(all_keys)} 个存储项")
```
</details>

---

##### `set(key: str, value: Any)`

设置存储项的值

:param key: 存储项键名
:param value: 存储项的值
:return: 操作是否成功

<details class='example'><summary>示例</summary>

```python
>>> storage.set("app.name", "MyApp")
>>> storage.set("user.settings", {"theme": "dark"})
```
</details>

---

##### `set_multi(items: Dict[str, Any])`

批量设置多个存储项

:param items: 键值对字典
:return: 操作是否成功

<details class='example'><summary>示例</summary>

```python
>>> storage.set_multi({
>>>     "app.name": "MyApp",
>>>     "app.version": "1.0.0",
>>>     "app.debug": True
>>> })
```
</details>

---

##### `getConfig(key: str, default: Any = None)`

获取模块/适配器配置项（委托给config模块）
:param key: 配置项的键(支持点分隔符如"module.sub.key")
:param default: 默认值
:return: 配置项的值

---

##### `setConfig(key: str, value: Any)`

设置模块/适配器配置（委托给config模块）
:param key: 配置项键名(支持点分隔符如"module.sub.key")
:param value: 配置项值
:return: 操作是否成功

---

##### `delete(key: str)`

删除存储项

:param key: 存储项键名
:return: 操作是否成功

<details class='example'><summary>示例</summary>

```python
>>> storage.delete("temp.session")
```
</details>

---

##### `delete_multi(keys: List[str])`

批量删除多个存储项

:param keys: 键名列表
:return: 操作是否成功

<details class='example'><summary>示例</summary>

```python
>>> storage.delete_multi(["temp.key1", "temp.key2"])
```
</details>

---

##### `get_multi(keys: List[str])`

批量获取多个存储项的值

:param keys: 键名列表
:return: 键值对字典

<details class='example'><summary>示例</summary>

```python
>>> settings = storage.get_multi(["app.name", "app.version"])
```
</details>

---

##### `transaction()`

创建事务上下文

:return: 事务上下文管理器

<details class='example'><summary>示例</summary>

```python
>>> with storage.transaction():
>>>     storage.set("key1", "value1")
>>>     storage.set("key2", "value2")
```
</details>

---

##### `_check_auto_snapshot()`

<div class='admonition warning'><p class='admonition-title'>内部方法</p><p></p></div>
检查并执行自动快照

---

##### `set_snapshot_interval(seconds: int)`

设置自动快照间隔

:param seconds: 间隔秒数

<details class='example'><summary>示例</summary>

```python
>>> # 每30分钟自动快照
>>> storage.set_snapshot_interval(1800)
```
</details>

---

##### `clear()`

清空所有存储项

:return: 操作是否成功

<details class='example'><summary>示例</summary>

```python
>>> storage.clear()  # 清空所有存储
```
</details>

---

##### `__getattr__(key: str)`

通过属性访问存储项

:param key: 存储项键名
:return: 存储项的值

<dt>异常</dt><dd><code>KeyError</code> 当存储项不存在时抛出</dd>
    
<details class='example'><summary>示例</summary>

```python
>>> app_name = storage.app_name
```
</details>

---

##### `__setattr__(key: str, value: Any)`

通过属性设置存储项

:param key: 存储项键名
:param value: 存储项的值
    
<details class='example'><summary>示例</summary>

```python
>>> storage.app_name = "MyApp"
```
</details>

---

##### `snapshot(name: Optional[str] = None)`

创建数据库快照

:param name: 快照名称(可选)
:return: 快照文件路径

<details class='example'><summary>示例</summary>

```python
>>> # 创建命名快照
>>> snapshot_path = storage.snapshot("before_update")
>>> # 创建时间戳快照
>>> snapshot_path = storage.snapshot()
```
</details>

---

##### `restore(snapshot_name: str)`

从快照恢复数据库

:param snapshot_name: 快照名称或路径
:return: 恢复是否成功

<details class='example'><summary>示例</summary>

```python
>>> storage.restore("before_update")
```
</details>

---

##### `list_snapshots()`

列出所有可用的快照

:return: 快照信息列表(名称, 创建时间, 大小)

<details class='example'><summary>示例</summary>

```python
>>> for name, date, size in storage.list_snapshots():
>>>     print(f"{name} - {date} ({size} bytes)")
```
</details>

---

##### `delete_snapshot(snapshot_name: str)`

删除指定的快照

:param snapshot_name: 快照名称
:return: 删除是否成功

<details class='example'><summary>示例</summary>

```python
>>> storage.delete_snapshot("old_backup")
```
</details>

---

<sub>文档最后更新于 2025-08-18 15:39:00</sub>

<a id="ErisPulse___init__"></a>
## ErisPulse\__init__.md


<sup>更新时间: 2025-08-18 15:39:00</sup>

---

## 模块概述


ErisPulse SDK 主模块

提供SDK核心功能模块加载和初始化功能

<div class='admonition tip'><p class='admonition-title'>提示</p><p>1. 使用前请确保已正确安装所有依赖
2. 调用sdk.init()进行初始化
3. 模块加载采用懒加载机制</p></div>

---

## 函数列表

### `init_progress()`

初始化项目环境文件

1. 检查并创建main.py入口文件
2. 确保基础目录结构存在

:return: bool 是否创建了新的main.py文件

<div class='admonition tip'><p class='admonition-title'>提示</p><p>1. 如果main.py已存在则不会覆盖
2. 此方法通常由SDK内部调用</p></div>

---

### `_prepare_environment()`

<div class='admonition warning'><p class='admonition-title'>内部方法</p><p></p></div>
准备运行环境

初始化项目环境文件

:return: bool 环境准备是否成功

---

### `init()`

SDK初始化入口

:return: bool SDK初始化是否成功

---

### `init_task()`

SDK初始化入口，返回Task对象

:return: asyncio.Task 初始化任务

---

### `load_module(module_name: str)`

手动加载指定模块

:param module_name: str 要加载的模块名称
:return: bool 加载是否成功

<div class='admonition tip'><p class='admonition-title'>提示</p><p>1. 可用于手动触发懒加载模块的初始化
2. 如果模块不存在或已加载会返回False</p></div>

---

## 类列表

### `class LazyModule`

懒加载模块包装器

当模块第一次被访问时才进行实例化

<div class='admonition tip'><p class='admonition-title'>提示</p><p>1. 模块的实际实例化会在第一次属性访问时进行
2. 依赖模块会在被使用时自动初始化</p></div>


#### 方法列表

##### `__init__(module_name: str, module_class: Type, sdk_ref: Any, module_info: Dict[str, Any])`

初始化懒加载包装器

:param module_name: str 模块名称
:param module_class: Type 模块类
:param sdk_ref: Any SDK引用
:param module_info: Dict[str, Any] 模块信息字典

---

##### `_initialize()`

实际初始化模块

<dt>异常</dt><dd><code>LazyLoadError</code> 当模块初始化失败时抛出</dd>

---

##### `__getattr__(name: str)`

属性访问时触发初始化

:param name: str 要访问的属性名
:return: Any 模块属性值

---

##### `__call__()`

调用时触发初始化

:param args: 位置参数
:param kwargs: 关键字参数
:return: Any 模块调用结果

---

##### `__bool__()`

判断模块布尔值时触发初始化

:return: bool 模块布尔值

---

##### `__str__()`

转换为字符串时触发初始化

:return: str 模块字符串表示

---

##### `__copy__()`

浅拷贝时返回自身，保持懒加载特性

:return: self

---

##### `__deepcopy__(memo)`

深拷贝时返回自身，保持懒加载特性

:param memo: memo
:return: self

---

### `class AdapterLoader`

适配器加载器

专门用于从PyPI包加载和初始化适配器

<div class='admonition tip'><p class='admonition-title'>提示</p><p>1. 适配器必须通过entry-points机制注册到erispulse.adapter组
2. 适配器类必须继承BaseAdapter
3. 适配器不适用懒加载</p></div>


#### 方法列表

##### `load()`

从PyPI包entry-points加载适配器

:return: 
    Dict[str, object]: 适配器对象字典 {适配器名: 模块对象}
    List[str]: 启用的适配器名称列表
    List[str]: 停用的适配器名称列表
    
<dt>异常</dt><dd><code>ImportError</code> 当无法加载适配器时抛出</dd>

---

##### `_process_adapter(entry_point: Any, adapter_objs: Dict[str, object], enabled_adapters: List[str], disabled_adapters: List[str])`

<div class='admonition warning'><p class='admonition-title'>内部方法</p><p></p></div>
处理单个适配器entry-point

:param entry_point: entry-point对象
:param adapter_objs: 适配器对象字典
:param enabled_adapters: 启用的适配器列表
:param disabled_adapters: 停用的适配器列表

:return: 
    Dict[str, object]: 更新后的适配器对象字典
    List[str]: 更新后的启用适配器列表 
    List[str]: 更新后的禁用适配器列表
    
<dt>异常</dt><dd><code>ImportError</code> 当适配器加载失败时抛出</dd>

---

### `class ModuleLoader`

模块加载器

专门用于从PyPI包加载和初始化普通模块

<div class='admonition tip'><p class='admonition-title'>提示</p><p>1. 模块必须通过entry-points机制注册到erispulse.module组
2. 模块类名应与entry-point名称一致</p></div>


#### 方法列表

##### `load()`

从PyPI包entry-points加载模块

:return: 
    Dict[str, object]: 模块对象字典 {模块名: 模块对象}
    List[str]: 启用的模块名称列表
    List[str]: 停用的模块名称列表
    
<dt>异常</dt><dd><code>ImportError</code> 当无法加载模块时抛出</dd>

---

##### `_process_module(entry_point: Any, module_objs: Dict[str, object], enabled_modules: List[str], disabled_modules: List[str])`

<div class='admonition warning'><p class='admonition-title'>内部方法</p><p></p></div>
处理单个模块entry-point

:param entry_point: entry-point对象
:param module_objs: 模块对象字典
:param enabled_modules: 启用的模块列表
:param disabled_modules: 停用的模块列表

:return: 
    Dict[str, object]: 更新后的模块对象字典
    List[str]: 更新后的启用模块列表 
    List[str]: 更新后的禁用模块列表
    
<dt>异常</dt><dd><code>ImportError</code> 当模块加载失败时抛出</dd>

---

##### `_should_lazy_load(module_class: Type)`

检查模块是否应该懒加载

:param module_class: Type 模块类
:return: bool 如果返回 False，则立即加载；否则懒加载

---

### `class ModuleInitializer`

模块初始化器

负责协调适配器和模块的初始化流程

<div class='admonition tip'><p class='admonition-title'>提示</p><p>1. 初始化顺序：适配器 → 模块
2. 模块初始化采用懒加载机制</p></div>


#### 方法列表

##### `init()`

初始化所有模块和适配器

执行步骤:
1. 从PyPI包加载适配器
2. 从PyPI包加载模块
3. 预记录所有模块信息
4. 注册适配器
5. 初始化各模块

:return: bool 初始化是否成功
<dt>异常</dt><dd><code>InitError</code> 当初始化失败时抛出</dd>

---

##### `_initialize_modules(modules: List[str], module_objs: Dict[str, Any])`

<div class='admonition warning'><p class='admonition-title'>内部方法</p><p></p></div>
初始化模块

:param modules: List[str] 模块名称列表
:param module_objs: Dict[str, Any] 模块对象字典

:return: bool 模块初始化是否成功

---

##### `_register_adapters(adapters: List[str], adapter_objs: Dict[str, Any])`

<div class='admonition warning'><p class='admonition-title'>内部方法</p><p></p></div>
注册适配器

:param adapters: List[str] 适配器名称列表
:param adapter_objs: Dict[str, Any] 适配器对象字典

:return: bool 适配器注册是否成功

---

<sub>文档最后更新于 2025-08-18 15:39:00</sub>

<a id="ErisPulse___main__"></a>
## ErisPulse\__main__.md


<sup>更新时间: 2025-08-18 15:39:00</sup>

---

## 模块概述


ErisPulse SDK 命令行工具

提供ErisPulse生态系统的包管理、模块控制和开发工具功能。

<div class='admonition tip'><p class='admonition-title'>提示</p><p>1. 需要Python 3.8+环境
2. Windows平台需要colorama支持ANSI颜色</p></div>

---

## 函数列表

### `main()`

CLI入口点

<div class='admonition tip'><p class='admonition-title'>提示</p><p>1. 创建CLI实例并运行
2. 处理全局异常</p></div>

---

## 类列表

### `class CommandHighlighter(RegexHighlighter)`

高亮CLI命令和参数

<div class='admonition tip'><p class='admonition-title'>提示</p><p>使用正则表达式匹配命令行参数和选项</p></div>


### `class PackageManager`

ErisPulse包管理器

提供包安装、卸载、升级和查询功能

<div class='admonition tip'><p class='admonition-title'>提示</p><p>1. 支持本地和远程包管理
2. 包含1小时缓存机制</p></div>


#### 方法列表

##### `__init__()`

初始化包管理器

---

##### async `async _fetch_remote_packages(url: str)`

从指定URL获取远程包数据

:param url: 远程包数据URL
:return: 解析后的JSON数据，失败返回None

<dt>异常</dt><dd><code>ClientError</code> 网络请求失败时抛出</dd>
<dt>异常</dt><dd><code>JSONDecodeError</code> JSON解析失败时抛出</dd>

---

##### async `async get_remote_packages(force_refresh: bool = False)`

获取远程包列表，带缓存机制

:param force_refresh: 是否强制刷新缓存
:return: 包含模块和适配器的字典

:return:
    dict: {
        "modules": {模块名: 模块信息},
        "adapters": {适配器名: 适配器信息},
        "cli_extensions": {扩展名: 扩展信息}
    }

---

##### `get_installed_packages()`

获取已安装的包信息

:return: 已安装包字典，包含模块、适配器和CLI扩展

:return:
    dict: {
        "modules": {模块名: 模块信息},
        "adapters": {适配器名: 适配器信息},
        "cli_extensions": {扩展名: 扩展信息}
    }

---

##### `_is_module_enabled(module_name: str)`

检查模块是否启用

:param module_name: 模块名称
:return: 模块是否启用

<dt>异常</dt><dd><code>ImportError</code> 核心模块不可用时抛出</dd>

---

##### `_normalize_name(name: str)`

标准化包名，统一转为小写以实现大小写不敏感比较

:param name: 原始名称
:return: 标准化后的名称

---

##### async `async _find_package_by_alias(alias: str)`

通过别名查找实际包名（大小写不敏感）

:param alias: 包别名
:return: 实际包名，未找到返回None

---

##### `_find_installed_package_by_name(name: str)`

在已安装包中查找实际包名（大小写不敏感）

:param name: 包名或别名
:return: 实际包名，未找到返回None

---

##### `_run_pip_command_with_output(args: List[str], description: str)`

执行pip命令并捕获输出

:param args: pip命令参数列表
:param description: 进度条描述
:return: (是否成功, 标准输出, 标准错误)

---

##### `_compare_versions(version1: str, version2: str)`

比较两个版本号

:param version1: 版本号1
:param version2: 版本号2
:return: 1 if version1 > version2, -1 if version1 < version2, 0 if equal

---

##### `_check_sdk_compatibility(min_sdk_version: str)`

检查SDK版本兼容性

:param min_sdk_version: 所需的最小SDK版本
:return: (是否兼容, 当前版本信息)

---

##### async `async _get_package_info(package_name: str)`

获取包的详细信息（包括min_sdk_version等）

:param package_name: 包名或别名
:return: 包信息字典

---

##### `install_package(package_names: List[str], upgrade: bool = False, pre: bool = False)`

安装指定包（支持多个包）

:param package_names: 要安装的包名或别名列表
:param upgrade: 是否升级已安装的包
:param pre: 是否包含预发布版本
:return: 安装是否成功

---

##### `uninstall_package(package_names: List[str])`

卸载指定包（支持多个包，支持别名）

:param package_names: 要卸载的包名或别名列表
:return: 卸载是否成功

---

##### `upgrade_all()`

升级所有已安装的ErisPulse包

:return: 升级是否成功

<dt>异常</dt><dd><code>KeyboardInterrupt</code> 用户取消操作时抛出</dd>

---

##### `upgrade_package(package_names: List[str], pre: bool = False)`

升级指定包（支持多个包）

:param package_names: 要升级的包名或别名列表
:param pre: 是否包含预发布版本
:return: 升级是否成功

---

##### `search_package(query: str)`

搜索包（本地和远程）

:param query: 搜索关键词
:return: 匹配的包信息

---

##### `get_installed_version()`

获取当前安装的ErisPulse版本

:return: 当前版本号

---

##### async `async get_pypi_versions()`

从PyPI获取ErisPulse的所有可用版本

:return: 版本信息列表

---

##### `_is_pre_release(version: str)`

判断版本是否为预发布版本

:param version: 版本号
:return: 是否为预发布版本

---

##### `update_self(target_version: str = None, force: bool = False)`

更新ErisPulse SDK本身

:param target_version: 目标版本号，None表示更新到最新版本
:param force: 是否强制更新
:return: 更新是否成功

---

### `class ReloadHandler(FileSystemEventHandler)`

文件系统事件处理器

实现热重载功能，监控文件变化并重启进程

<div class='admonition tip'><p class='admonition-title'>提示</p><p>1. 支持.py文件修改重载
2. 支持配置文件修改重载</p></div>


#### 方法列表

##### `__init__(script_path: str, reload_mode: bool = False)`

初始化处理器

:param script_path: 要监控的脚本路径
:param reload_mode: 是否启用重载模式

---

##### `start_process()`

启动监控进程

---

##### `_terminate_process()`

终止当前进程

:raises subprocess.TimeoutExpired: 进程终止超时时抛出

---

##### `on_modified(event)`

文件修改事件处理

:param event: 文件系统事件

---

##### `_handle_reload(event, reason: str)`

处理热重载逻辑
:param event: 文件系统事件
:param reason: 重载原因

---

### `class CLI`

ErisPulse命令行接口

提供完整的命令行交互功能

<div class='admonition tip'><p class='admonition-title'>提示</p><p>1. 支持动态加载第三方命令
2. 支持模块化子命令系统</p></div>


#### 方法列表

##### `__init__()`

初始化CLI

---

##### `_create_parser()`

创建命令行参数解析器

:return: 配置好的ArgumentParser实例

---

##### `_get_external_commands()`

获取所有已注册的第三方命令名称

:return: 第三方命令名称列表

---

##### `_load_external_commands(subparsers)`

加载第三方CLI命令

:param subparsers: 子命令解析器

<dt>异常</dt><dd><code>ImportError</code> 加载命令失败时抛出</dd>

---

##### `_print_version()`

打印版本信息

---

##### `_print_installed_packages(pkg_type: str, outdated_only: bool = False)`

打印已安装包信息

:param pkg_type: 包类型 (modules/adapters/cli/all)
:param outdated_only: 是否只显示可升级的包

---

##### `_print_remote_packages(pkg_type: str)`

打印远程包信息

:param pkg_type: 包类型 (modules/adapters/cli/all)

---

##### `_is_package_outdated(package_name: str, current_version: str)`

检查包是否过时

:param package_name: 包名
:param current_version: 当前版本
:return: 是否有新版本可用

---

##### `_resolve_package_name(short_name: str)`

解析简称到完整包名（大小写不敏感）

:param short_name: 模块/适配器简称
:return: 完整包名，未找到返回None

---

##### `_print_search_results(query: str, results: Dict[str, List[Dict[str, str]]])`

打印搜索结果

:param query: 搜索关键词
:param results: 搜索结果

---

##### `_print_version_list(versions: List[Dict[str, Any]], include_pre: bool = False)`

打印版本列表

:param versions: 版本信息列表
:param include_pre: 是否包含预发布版本

---

##### `_setup_watchdog(script_path: str, reload_mode: bool)`

设置文件监控

:param script_path: 要监控的脚本路径
:param reload_mode: 是否启用重载模式

---

##### `_cleanup()`

清理资源

---

##### `run()`

运行CLI

<dt>异常</dt><dd><code>KeyboardInterrupt</code> 用户中断时抛出</dd>
<dt>异常</dt><dd><code>Exception</code> 命令执行失败时抛出</dd>

---

##### `_cleanup_adapters()`

清理适配器资源

---

<sub>文档最后更新于 2025-08-18 15:39:00</sub>

---
