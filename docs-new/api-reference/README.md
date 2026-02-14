# API 参考

本目录包含 ErisPulse 框架的 API 参考文档。

## 文档列表

- [核心模块 API](core-modules.md) - 存储、配置、日志等核心模块 API
- [事件系统 API](event-system.md) - Event 模块 API 参考
- [适配器系统 API](adapter-system.md) - Adapter 管理器 API 参考

## API 概览

### 核心模块

ErisPulse SDK 提供以下核心模块：

| 模块 | 路径 | 说明 |
|------|------|------|
| `sdk.storage` | `sdk.storage` | 存储系统 |
| `sdk.config` | `sdk.config` | 配置管理 |
| `sdk.logger` | `sdk.logger` | 日志系统 |
| `sdk.adapter` | `sdk.adapter` | 适配器管理 |
| `sdk.module` | `sdk.module` | 模块管理 |
| `sdk.lifecycle` | `sdk.lifecycle` | 生命周期管理 |
| `sdk.router` | `sdk.router` | 路由管理 |

### 事件系统

Event 模块提供以下子模块：

| 模块 | 路径 | 说明 |
|------|------|------|
| `command` | `ErisPulse.Core.Event.command` | 命令处理 |
| `message` | `ErisPulse.Core.Event.message` | 消息事件 |
| `notice` | `ErisPulse.Core.Event.notice` | 通知事件 |
| `request` | `ErisPulse.Core.Event.request` | 请求事件 |
| `meta` | `ErisPulse.Core.Event.meta` | 元事件 |

### 基类

ErisPulse 提供以下基类：

| 基类 | 路径 | 说明 |
|------|------|------|
| `BaseModule` | `ErisPulse.Core.Bases.BaseModule` | 模块基类 |
| `BaseAdapter` | `ErisPulse.Core.Bases.BaseAdapter` | 适配器基类 |

## 使用示例

### 访问核心模块

```python
from ErisPulse import sdk

# 存储系统
sdk.storage.set("key", "value")
value = sdk.storage.get("key")

# 配置管理
config = sdk.config.getConfig("MyModule")

# 日志系统
sdk.logger.info("日志信息")

# 适配器管理
adapter = sdk.adapter.get("platform")
await adapter.Send.To("user", "123").Text("Hello")

# 模块管理
module = sdk.module.get("ModuleName")

# 生命周期管理
await sdk.lifecycle.submit_event("custom.event", msg="自定义事件")

# 路由管理
sdk.router.register_http_route("MyModule", "/api", handler, ["GET"])
```

### 使用事件系统

```python
from ErisPulse.Core.Event import command, message, notice, request, meta

# 命令处理
@command("hello", help="问候命令")
async def hello_handler(event):
    await event.reply("你好！")

# 消息处理
@message.on_group_message()
async def group_handler(event):
    sdk.logger.info(f"收到群消息: {event.get_text()}")

# 通知处理
@notice.on_friend_add()
async def friend_add_handler(event):
    await event.reply("欢迎添加我为好友！")

# 请求处理
@request.on_friend_request()
async def friend_request_handler(event):
    pass

# 元事件处理
@meta.on_connect()
async def connect_handler(event):
    sdk.logger.info("平台连接成功")
```

### 继承基类

```python
from ErisPulse.Core.Bases import BaseModule

class MyModule(BaseModule):
    def __init__(self):
        super().__init__()
        self.sdk = sdk
    
    async def on_load(self, event):
        """模块加载"""
        pass
    
    async def on_unload(self, event):
        """模块卸载"""
        pass
```

## 相关文档

- [核心概念](../getting-started/basic-concepts.md) - 理解框架核心概念
- [模块开发指南](../developer-guide/modules/) - 开发自定义模块
- [适配器开发指南](../developer-guide/adapters/) - 开发平台适配器