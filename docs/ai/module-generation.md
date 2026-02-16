# AI 模块生成指南

本指南帮助你使用 AI 快速生成符合 ErisPulse 规范的模块和适配器代码。

---

## ErisPulse 核心功能概述

在开始之前，建议先了解 ErisPulse 的核心功能，以便向 AI 提供准确的上下文：

### 核心架构

- **事件驱动架构**：基于 OneBot12 标准的事件系统
- **模块化设计**：通过模块和适配器实现功能扩展
- **懒加载机制**：模块按需加载，提升启动速度
- **跨平台支持**：通过适配器系统支持多种平台

### 核心模块

| 模块 | 功能说明 |
|------|---------|
| `sdk.storage` | 基于 SQLite 的键值存储系统 |
| `sdk.config` | TOML 格式配置文件管理 |
| `sdk.logger` | 模块化日志系统 |
| `sdk.adapter` | 适配器管理系统 |
| `sdk.module` | 模块管理系统 |
| `sdk.Event` | 事件处理模块（命令、消息、通知、请求、元事件） |
| `sdk.lifecycle` | 生命周期事件管理 |
| `sdk.router` | HTTP/WebSocket 路由管理 |

### 事件系统

ErisPulse 支持以下事件类型：

- **消息事件**：处理用户发送的消息（私聊、群聊、@消息）
- **命令事件**：处理用户输入的命令（支持命令组、权限检查、等待回复）
- **通知事件**：处理系统通知（好友添加、群成员变化等）
- **请求事件**：处理请求（好友请求、群邀请等）
- **元事件**：处理系统级事件（连接、断开连接、心跳等）

### SendDSL 消息发送

适配器通过链式调用风格发送消息：

```python
# 基础发送
await adapter.Send.To("user", "123").Text("Hello")

# 指定发送账号（多账户支持）
await adapter.Send.Using("bot1").To("user", "123").Text("Hello")

# 链式修饰（@用户、回复等）
await adapter.Send.To("group", "456").At("789").Reply("123").Text("回复消息")

# @全体成员
await adapter.Send.To("group", "456").AtAll().Text("公告消息")
```

### 支持的平台

- **云湖 (Yunhu)**：企业级即时通讯平台
- **Telegram**：跨平台即时通讯软件
- **OneBot11/12**：通用聊天机器人应用接口标准
- **邮件 (Email)**：基于 SMTP/IMAP 协议

---

## AI 开发物料选择

根据你的生成需求选择合适的文档：

| 文档类型 | 适用场景 | 推荐度 |
|---------|----------|--------|
| **ErisPulse-ModuleDev.md** | 模块开发 | ⭐⭐⭐⭐⭐ |
| **ErisPulse-AdapterDev.md** | 适配器开发 | ⭐⭐⭐⭐⭐ |
| **ErisPulse-Core.md** | 核心功能参考 | ⭐⭐⭐ |
| **ErisPulse-Full.md** | 完整开发参考（仅限大模型） | ⭐⭐ |

### 文档获取方式

所有文档位于 `docs/ai/AIDocs/` 目录下：

- `ErisPulse-ModuleDev.md` - 模块开发专用物料
- `ErisPulse-AdapterDev.md` - 适配器开发专用物料
- `ErisPulse-Core.md` - 核心功能参考
- `ErisPulse-Full.md` - 完整开发参考

> 💡 **提示**：
> - 对于大多数 AI 模型，推荐使用专用的 Module/Adapter 文档
> - Full 文档包含所有内容，仅推荐给具有强大上下文能力的大模型
> - 建议在提示词中明确告知 AI 使用哪个文档

---

## 模块开发指南

### 模块结构

一个标准的模块包结构：

```
MyModule/
├── pyproject.toml    # 项目配置
├── README.md         # 项目说明
├── LICENSE           # 许可证文件
└── MyModule/
    ├── __init__.py  # 模块入口
    └── Core.py      # 核心逻辑（推荐使用 Core.py，但可以使用任何你喜欢的文件名）
```

### pyproject.toml 配置

```toml
[project]
name = "ErisPulse-MyModule"     # 模块名称，建议使用 ErisPulse-<模块名称> 格式
version = "1.0.0"
description = "模块功能描述"
readme = "README.md"
requires-python = ">=3.9"
license = { file = "LICENSE" }
authors = [ { name = "yourname", email = "your@mail.com" } ]
dependencies = [
    # 模块依赖
]

# 模块主页，用于在模块管理器中显示模块信息
[project.urls]
"homepage" = "https://github.com/yourname/MyModule"

# 模块入口点
[project.entry-points."erispulse.module"]
"MyModule" = "MyModule:Main"
```

### 模块核心实现

```python
from ErisPulse import sdk
from ErisPulse.Core.Bases import BaseModule
from ErisPulse.Core.Event import command, message, notice

class Main(BaseModule):
    def __init__(self):
        self.sdk = sdk
        self.logger = sdk.logger.get_child("MyModule")
        self.storage = sdk.storage
        self.config = sdk.config
        self.module_config = self._load_config()

    @staticmethod
    def get_load_strategy():
        """
        返回模块加载策略
        
        lazy_load: False 表示立即加载，True 表示懒加载（默认）
        priority: 加载优先级，数值越大优先级越高（默认为 0）
        """
        from ErisPulse.loaders import ModuleLoadStrategy
        return ModuleLoadStrategy(
            lazy_load=True,  # 懒加载，首次访问时才加载
            priority=0       # 默认优先级
        )

    async def on_load(self, event):
        """模块加载时调用"""
        # 注册命令处理器
        @command("hello", help="发送问候消息")
        async def hello_command(event):
            await event.reply("你好！")
        
        # 注册消息处理器
        @message.on_group_message()
        async def group_handler(event):
            self.logger.info(f"收到群消息: {event.get_alt_message()}")
        
        self.logger.info("模块已加载")

    async def on_unload(self, event):
        """模块卸载时调用"""
        # 清理资源
        await self._cleanup_resources()
        self.logger.info("模块已卸载")

    def _load_config(self):
        """加载模块配置"""
        config = self.sdk.config.getConfig("MyModule")
        if not config:
            default_config = {
                "api_url": "https://api.example.com",
                "timeout": 30
            }
            self.sdk.config.setConfig("MyModule", default_config)
            self.logger.warning("未找到模块配置，已创建默认配置")
            return default_config
        return config

    async def _cleanup_resources(self):
        """清理资源"""
        pass
```

### Event 事件包装类

ErisPulse 提供了便捷的 Event 包装类，简化事件处理：

```python
from ErisPulse.Core.Event import command, message

@command("info", help="获取用户信息")
async def info_command(event):
    # 获取核心事件信息
    event_id = event.get_id()
    platform = event.get_platform()
    user_id = event.get_user_id()
    nickname = event.get_user_nickname()
    text = event.get_text()
    
    # 判断消息类型
    is_private = event.is_private_message()
    is_group = event.is_group_message()
    
    # 便捷回复
    await event.reply(f"用户: {nickname}({user_id}), 类型: {'私聊' if is_private else '群聊'}")

@message.on_group_message()
async def group_handler(event):
    # 获取消息内容
    text = event.get_text()
    user_id = event.get_user_id()
    
    # 等待用户回复
    await event.reply("请输入你的姓名:")
    reply = await event.wait_reply(timeout=30)
    
    if reply:
        name = reply.get_text()
        await event.reply(f"你好，{name}！")
```

### 懒加载策略

```python
@staticmethod
def get_load_strategy():
    """
    推荐使用懒加载的场景：
    - ✅ 大多数功能模块
    - ✅ 命令处理模块
    - ✅ 按需加载的扩展功能
    
    推荐禁用懒加载的场景（lazy_load=False）：
    - ❌ 生命周期事件监听器
    - ❌ 定时任务模块
    - ❌ 需要在应用启动时就初始化的模块
    """
    from ErisPulse.loaders import ModuleLoadStrategy
    return ModuleLoadStrategy(
        lazy_load=False,  # 立即加载
        priority=100      # 高优先级
    )
```

### 路由注册

模块可以注册 HTTP 和 WebSocket 路由：

```python
from fastapi import Request, WebSocket

async def on_load(self, event):
    # 注册 HTTP 路由
    async def get_info():
        return {"module": "MyModule", "status": "running"}
    
    self.sdk.router.register_http_route(
        module_name="MyModule",
        path="/info",
        handler=get_info,
        methods=["GET"]
    )
    
    # 注册 WebSocket 路由
    async def websocket_handler(websocket: WebSocket):
        await websocket.accept()
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"Echo: {data}")
    
    self.sdk.router.register_websocket(
        module_name="MyModule",
        path="/ws",
        handler=websocket_handler
    )
```

---

## 适配器开发指南

### 适配器结构

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

### pyproject.toml 配置

```toml
[project]
name = "ErisPulse-MyAdapter"
version = "1.0.0"
description = "适配器功能描述"
readme = "README.md"
requires-python = ">=3.9"
license = { file = "LICENSE" }
authors = [ { name = "yourname", email = "your@mail.com" } ]

[project.urls]
"homepage" = "https://github.com/yourname/MyAdapter"

[project.entry-points."erispulse.adapter"]
"MyAdapter" = "MyAdapter:MyAdapter"
```

### 适配器核心实现

```python
from ErisPulse import sdk
from ErisPulse.Core import BaseAdapter
from ErisPulse.Core import router, logger, config as config_manager, adapter
from fastapi import WebSocket, WebSocketDisconnect

class MyAdapter(BaseAdapter):
    def __init__(self, sdk=None):
        self.sdk = sdk
        self.logger = logger.get_child("MyAdapter")
        self.config_manager = config_manager
        self.adapter = adapter
        self.config = self._get_config()
        self.converter = self._setup_converter()
        self.convert = self.converter.convert

    def _setup_converter(self):
        from .Converter import MyPlatformConverter
        return MyPlatformConverter()

    def _get_config(self):
        """加载配置"""
        if not self.config_manager:
            return {}
        
        config = self.config_manager.getConfig("MyAdapter", {})
        if config is None:
            default_config = {
                # 默认配置
            }
            self.config_manager.setConfig("MyAdapter", default_config)
            return default_config
        return config

    class Send(BaseAdapter.Send):
        """Send 消息发送 DSL"""
        
        def Text(self, text: str):
            """发送文本消息"""
            import asyncio
            return asyncio.create_task(
                self._adapter.call_api(
                    endpoint="/send",
                    content=text,
                    recvId=self._target_id,
                    recvType=self._target_type
                )
            )
        
        def Image(self, file: bytes):
            """发送图片消息"""
            import asyncio
            return asyncio.create_task(
                self._adapter.call_api(
                    endpoint="/send_image",
                    file=file,
                    recvId=self._target_id,
                    recvType=self._target_type
                )
            )

    async def call_api(self, endpoint: str, **params):
        """调用平台 API（必须实现）"""
        raise NotImplementedError("需要实现平台特定的 API 调用")

    async def start(self):
        """启动适配器（必须实现）"""
        raise NotImplementedError("需要实现适配器启动逻辑")

    async def shutdown(self):
        """关闭适配器（必须实现）"""
        raise NotImplementedError("需要实现适配器关闭逻辑")
```

### 事件转换器

```python
class MyPlatformConverter:
    def convert(self, raw_event):
        """将平台原生事件转换为 OneBot12 标准格式"""
        if not isinstance(raw_event, dict):
            return None
        
        onebot_event = {
            "id": self._generate_event_id(raw_event),
            "time": self._convert_timestamp(raw_event.get("timestamp")),
            "type": self._convert_event_type(raw_event.get("type")),
            "detail_type": self._convert_detail_type(raw_event),
            "platform": "myplatform",
            "self": {
                "platform": "myplatform",
                "user_id": str(raw_event.get("bot_id", ""))
            },
            "myplatform_raw": raw_event,          # 保留原始数据（必须）
            "myplatform_raw_type": raw_event.get("type", "")  # 保留原始事件类型（必须）
        }
        return onebot_event
    
    def _generate_event_id(self, raw_event):
        """生成事件 ID"""
        event_id = raw_event.get("event_id")
        if event_id:
            return str(event_id)
        import uuid
        return str(uuid.uuid4())
    
    def _convert_timestamp(self, timestamp):
        """转换时间戳为 10 位秒级时间戳"""
        if not timestamp:
            import time
            return int(time.time())
        if timestamp > 10**12:
            return int(timestamp / 1000)
        return int(timestamp)
```

### WebSocket/WebHook 路由注册

```python
# WebSocket 方式
async def _ws_handler(self, websocket: WebSocket):
    self.connection = websocket
    try:
        while True:
            data = await websocket.receive_text()
            onebot_event = self.convert(data)
            if onebot_event and self.adapter:
                await self.adapter.emit(onebot_event)
    except WebSocketDisconnect:
        self.connection = None

async def start(self):
    from ErisPulse.Core import router
    router.register_websocket(
        module_name="myplatform",
        path="/ws",
        handler=self._ws_handler
    )

# WebHook 方式
async def _webhook_handler(self, request: Request):
    data = await request.json()
    onebot_event = self.convert(data)
    if onebot_event and self.adapter:
        await self.adapter.emit(onebot_event)
    return {"status": "ok"}

async def start(self):
    from ErisPulse.Core import router
    router.register_http_route(
        module_name="myplatform",
        path="/webhook",
        handler=self._webhook_handler,
        methods=["POST"]
    )
```

### API 响应标准

```python
async def call_api(self, endpoint: str, **params):
    try:
        raw_response = await self._platform_api_call(endpoint, **params)
        
        standardized = {
            "status": "ok" if raw_response.get("success", False) else "failed",
            "retcode": 0 if raw_response.get("success", False) else raw_response.get("code", 10001),
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
            "retcode": 34000,
            "data": None,
            "message": str(e),
            "message_id": ""
        }
```

---

## 需求描述规范

### 模块需求描述模板

```markdown
我需要一个 [模块名称] 模块，具体需求如下：

## 功能描述
[详细描述模块的功能需求]

## 核心功能
1. [功能1描述]
2. [功能2描述]
3. ...

## 事件处理
- 需要监听的事件类型：[消息/命令/通知/请求]
- 事件处理逻辑：[详细说明]

## 消息发送
- 需要使用的发送方法：[Text/Image/Voice/Video 等]
- 是否需要使用链式修饰：[@用户/回复/@全体等]
- 是否需要支持多平台：[支持的平台列表]

## 配置需求
- 需要的配置项：[列出所有配置项及其默认值]
- 配置项说明：[每个配置项的用途]

## 存储需求
- 是否需要持久化存储数据：[是/否]
- 存储的数据结构：[数据结构说明]

## 平台特性
- 是否需要使用平台特有功能：[是/否]
- 需要的平台：[列出平台名称]
- 特性说明：[详细说明]

## 其他需求
- [其他特殊需求说明]

请根据 ErisPulse Module 规范生成完整模块代码，包括：
1. 完整的 pyproject.toml 配置
2. 模块核心实现（__init__.py 和 Core.py）
3. 事件处理器注册
4. 配置管理
5. 适当的错误处理和日志记录
```

### 适配器需求描述模板

```markdown
我需要一个 [适配器名称] 适配器，具体需求如下：

## 平台信息
- 平台名称：[平台名称]
- 平台文档链接：[文档链接]
- 通信协议：[WebSocket/WebHook/其他]

## 核心功能
1. [功能1描述]
2. [功能2描述]
3. ...

## 事件转换
- 平台事件类型：[列出主要的事件类型]
- OneBot12 标准事件映射：[事件类型映射表]
- 需要保留的原始字段：[原始字段列表]

## 消息发送
- 支持的发送类型：[Text/Image/Voice/Video/File 等]
- 特殊发送方法：[平台特有的发送方法]
- 是否支持链式修饰：[@用户/回复/@全体等]

## 连接管理
- 连接方式：[WebSocket/WebHook/其他]
- 重连机制：[是否需要自动重连]
- 认证方式：[认证方式说明]

## 配置需求
- 必需的配置项：[列出配置项]
- 可选的配置项：[列出配置项]
- 配置项说明：[每个配置项的用途]

## API 调用
- 需要实现的 API 端点：[列出 API 端点]
- API 请求格式：[请求格式说明]
- API 响应格式：[响应格式说明]

## 其他需求
- [其他特殊需求说明]

请根据 ErisPulse Adapter 规范生成完整适配器代码，包括：
1. 完整的 pyproject.toml 配置
2. 适配器核心实现（__init__.py 和 Core.py）
3. 事件转换器实现（Converter.py）
4. Send 类实现
5. WebSocket/WebHook 路由注册
6. 适当的错误处理和日志记录
```

---

## 示例模板

### 示例 1：天气查询模块

```markdown
我需要一个天气查询模块 WeatherBot，具体需求如下：

## 功能描述
当用户在群聊中发送"weather 上海"时，调用 OpenWeatherMap API 查询天气，返回中文格式的天气信息卡片。

## 核心功能
1. 支持城市名称查询天气
2. 支持城市 ID 查询天气
3. 缓存查询结果（5分钟有效期）
4. 支持多平台

## 事件处理
- 需要监听的事件类型：消息事件
- 事件处理逻辑：
  - 解析用户输入的城市名称或 ID
  - 检查缓存
  - 调用 OpenWeatherMap API
  - 缓存结果
  - 格式化天气信息并发送

## 消息发送
- 需要使用的发送方法：Text
- 是否需要使用链式修饰：否
- 是否需要支持多平台：是，通过获取event的平台来确定使用哪个平台的适配器发送消息

## 配置需求
- 需要的配置项：
  - api_key: OpenWeatherMap API 密钥（必填）
  - default_city: 默认城市（可选，默认："北京"）
  - cache_ttl: 缓存有效期，单位秒（可选，默认：300）
  - timeout: API 请求超时时间，单位秒（可选，默认：30）

## 存储需求
- 是否需要持久化存储数据：是
- 存储的数据结构：
  - weather_cache: {city: {data: 天气数据, timestamp: 时间戳}}

## 平台特性
- 是否需要使用平台特有功能：是
- 需要的平台：云湖、Telegram、OneBot11、OneBot12
- 特性说明：
  - 云湖：使用 button 特性展示天气信息卡片
  - Telegram：支持 Markdown 格式
  - OneBot11/12：使用纯文本格式

## 其他需求
- 需要添加错误处理：API 请求失败时返回友好的错误信息
- 需要添加日志记录：记录每次 API 调用和缓存命中情况

请根据 ErisPulse Module 规范生成完整模块代码。
```

### 示例 2：简单命令模块

```markdown
我需要一个简单的命令模块 SimpleCommands，具体需求如下：

## 功能描述
提供一些实用的基础命令，包括：
- /help - 显示帮助信息
- /ping - 测试机器人是否在线
- /echo [text] - 回显用户输入的文本
- /time - 显示当前时间

## 核心功能
1. 命令注册和处理
2. 命令帮助系统
3. 命令别名支持

## 事件处理
- 需要监听的事件类型：命令事件
- 事件处理逻辑：
  - 解析命令参数
  - 执行对应的命令逻辑
  - 返回执行结果

## 消息发送
- 需要使用的发送方法：Text
- 是否需要使用链式修饰：否
- 是否需要支持多平台：是（所有平台）

## 配置需求
- 需要的配置项：无

## 存储需求
- 是否需要持久化存储数据：否

## 平台特性
- 是否需要使用平台特有功能：否
- 需要的平台：所有平台

## 其他需求
- 需要添加权限检查：/echo 命令仅管理员可用
- 需要添加日志记录：记录所有命令执行

请根据 ErisPulse Module 规范生成完整模块代码。
```

### 示例 3：邮件适配器

```markdown
我需要一个邮件适配器 EmailAdapter，具体需求如下：

## 平台信息
- 平台名称：Email
- 通信协议：SMTP（发送）和 IMAP（接收）
- 平台文档链接：https://docs.python.org/3/library/email.html

## 核心功能
1. 支持发送邮件（SMTP）
2. 支持接收邮件（IMAP）
3. 支持附件
4. 支持 HTML 和纯文本格式

## 事件转换
- 平台事件类型：邮件接收事件
- OneBot12 标准事件映射：
  - 邮件接收 → message 事件（detail_type: "private"）
  - 邮件主题 → message 的 alt_message
  - 邮件内容 → message 的 message 段
  - 发件人 → user_id
  - 收件人 → group_id（如果有多个收件人）
- 需要保留的原始字段：
  - email_raw: 包含完整的邮件原始数据
  - attachments: 附件数据列表

## 消息发送
- 支持的发送类型：Text、Html、Attachment
- 特殊发送方法：
  - Subject(subject): 设置邮件主题
  - Cc(emails): 设置抄送
  - Bcc(emails): 设置密送
  - ReplyTo(email): 设置回复地址
- 是否支持链式修饰：否
- 是否需要支持多平台：否

## 连接管理
- 连接方式：IMAP（接收）和 SMTP（发送）
- 重连机制：IMAP 需要，SMTP 不需要
- 认证方式：用户名和密码认证

## 配置需求
- 必需的配置项：
  - imap_server: IMAP 服务器地址（必填）
  - imap_port: IMAP 端口（必填）
  - imap_username: IMAP 用户名（必填）
  - imap_password: IMAP 密码（必填）
  - smtp_server: SMTP 服务器地址（必填）
  - smtp_port: SMTP 端口（必填）
  - smtp_username: SMTP 用户名（必填）
  - smtp_password: SMTP 密码（必填）
- 可选的配置项：
  - imap_ssl: 是否使用 SSL 连接（默认：true）
  - smtp_ssl: 是否使用 SSL 连接（默认：true）
  - check_interval: 邮件检查间隔，单位秒（默认：60）

## API 调用
- 需要实现的 API 端点：
  - send_email: 发送邮件
  - receive_email: 接收邮件
- API 请求格式：[根据实际 API 定义]
- API 响应格式：[根据实际 API 定义]

## 其他需求
- 需要添加错误处理：连接失败、认证失败等
- 需要添加日志记录：记录邮件收发情况
- 需要支持附件：支持发送和接收附件
- 需要支持 HTML：支持 HTML 格式的邮件内容

请根据 ErisPulse Adapter 规范生成完整适配器代码。
```

---

## 测试与验证

### 模块测试

```bash
# 安装模块依赖
epsdk install <你的模块包目录>

# 运行测试
epsdk run main.py --reload
```

### 适配器测试

```bash
# 安装适配器依赖
epsdk install <你的适配器包目录>

# 测试事件接收
# 发送测试事件到适配器，检查是否正确转换为 OneBot12 标准事件

# 测试消息发送
# 通过适配器发送测试消息，检查是否正确发送到平台
```

### 验证清单

#### 模块验证

- [ ] 模块是否正确注册
- [ ] 事件处理器是否正确工作
- [ ] 消息发送是否正常
- [ ] 配置是否正确加载
- [ ] 日志是否正常输出
- [ ] 错误处理是否完善
- [ ] 是否支持懒加载（如适用）
- [ ] 路由是否正确注册（如适用）

#### 适配器验证

- [ ] 适配器是否正确注册
- [ ] 事件转换是否正确
- [ ] 原始数据是否保留
- [ ] API 调用是否正常
- [ ] API 响应格式是否正确
- [ ] 连接管理是否正常
- [ ] 消息发送是否正常
- [ ] 日志是否正常输出
- [ ] 错误处理是否完善

---

## 常见问题

### Q: 推荐使用什么 AI 工具？

A: 推荐使用以下 AI 工具：
- **VS Code + GitHub Copilot**：可以直接操作文件系统，适合快速开发
- **Cursor**：强大的 AI 编码助手，支持多文件编辑
- **ChatGPT / Claude**：可以通过对话生成代码，然后手动复制到文件中

### Q: 可以发布 AI 生成的模块吗？

A: 当然可以！但请确保：
1. 代码符合 ErisPulse 规范
2. 包含完整文档（README.md）
3. 通过基础测试用例
4. 在 pyproject.toml 中正确配置所有信息

### Q: AI 生成的代码有问题怎么办？

A: 建议按以下步骤处理：
1. 检查 AI 是否使用了正确的文档版本
2. 向 AI 提供更详细的需求描述
3. 让 AI 分步生成，逐步验证
4. 参考示例模板，提供更具体的示例

### Q: 如何让 AI 生成更高质量的代码？

A: 建议：
1. 提供详细的需求描述，包括所有细节
2. 提供具体的示例，包括输入和输出
3. 明确指定使用的文档版本
4. 要求 AI 添加注释和文档字符串
5. 要求 AI 遵循 ErisPulse 的编码规范

### Q: 懒加载和立即加载有什么区别？

A:
- **懒加载（lazy_load=True）**：模块在首次被访问时才加载，适用于大多数功能模块
- **立即加载（lazy_load=False）**：模块在 SDK 初始化时立即加载，适用于：
  - 生命周期事件监听器
  - 定时任务模块
  - 需要在应用启动时就初始化的模块

### Q: 如何让模块支持多平台？

A:
1. 使用 `event.get_platform()` 判断平台
2. 根据不同平台调整消息格式
3. 使用平台特定的发送方法（如云湖的 button 特性）
4. 在配置中添加平台特定配置项

### Q: 事件转换时必须保留哪些字段？

A: 必须保留以下字段：
- `{platform}_raw`: 平台原始事件数据
- `{platform}_raw_type`: 平台原始事件类型

这些字段用于调试和访问平台特有功能。

### Q: 如何处理 API �用失败？

A: 建议：
1. 添加重试机制（最多 3 次）
2. 添加超时处理（默认 30 秒）
3. 记录详细的错误日志
4. 向用户返回友好的错误信息
5. 考虑使用缓存避免重复请求失败的 API

---

## 进阶技巧

### 使用生命周期事件

```python
from ErisPulse import sdk

async def on_load(self, event):
    # 监听模块初始化事件
    @sdk.lifecycle.on("module.init")
    async def on_module_init(event_data):
        module_name = event_data['data'].get('module_name')
        if module_name != "MyModule":
            sdk.logger.info(f"其他模块加载: {module_name}")
    
    # 提交自定义事件
    await sdk.lifecycle.submit_event(
        "custom.ready",
        source="MyModule",
        msg="MyModule 已准备好接收事件"
    )
```

### 使用存储系统

```python
# 设置存储项
sdk.storage.set("user.settings", {"theme": "dark", "language": "zh-CN"})

# 获取存储项
settings = sdk.storage.get("user.settings", {})

# 使用事务
with sdk.storage.transaction():
    sdk.storage.set("key1", "value1")
    sdk.storage.set("key2", "value2")

# 批量操作
sdk.storage.set_multi({
    "key1": "value1",
    "key2": "value2"
})
```

### 使用路由系统

```python
# 注册 HTTP 路由
async def get_info():
    return {"module": "MyModule", "status": "running"}

sdk.router.register_http_route(
    module_name="MyModule",
    path="/info",
    handler=get_info,
    methods=["GET"]
)

# 注册 WebSocket 路由
async def websocket_handler(websocket: WebSocket):
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        await websocket.send_text(f"Echo: {data}")

sdk.router.register_websocket(
    module_name="MyModule",
    path="/ws",
    handler=websocket_handler
)
```

---

## 总结

使用本指南，你可以快速生成符合 ErisPulse 规范的模块和适配器代码。关键要点：

1. **选择合适的文档**：根据开发类型选择对应的 AI 开发物料
2. **详细描述需求**：使用提供的模板清晰描述你的需求
3. **遵循规范**：确保生成的代码符合 ErisPulse 的编码规范
4. **测试验证**：使用提供的检查清单验证生成的代码
5. **参考示例**：使用示例模板作为参考，提供更具体的需求描述

祝你开发愉快！
