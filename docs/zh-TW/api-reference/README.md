# API 參考

本目錄包含 ErisPulse 框架的 API 參考文件。

## 文件列表

- [核心模組 API](core-modules.md) - 儲存、設定、日誌等核心模組 API
- [事件系統 API](event-system.md) - Event 模組 API 參考
- [適配器系統 API](adapter-system.md) - Adapter 管理器 API 參考
- [ErisPulse 自動生成 API](auto_api/README.md) - 自動生成 API 參考

## API 概覽

### 核心模組

ErisPulse SDK 提供以下核心模組：

| 模組 | 路徑 | 說明 |
|------|------|------|
| `sdk.storage` | `sdk.storage` | 儲存系統 |
| `sdk.config` | `sdk.config` | 設定管理 |
| `sdk.logger` | `sdk.logger` | 日誌系統 |
| `sdk.adapter` | `sdk.adapter` | 適配器管理 |
| `sdk.module` | `sdk.module` | 模組管理 |
| `sdk.lifecycle` | `sdk.lifecycle` | 生命週期管理 |
| `sdk.router` | `sdk.router` | 路由管理 |

### 事件系統

Event 模組提供以下子模組：

| 模組 | 路徑 | 說明 |
|------|------|------|
| `command` | `ErisPulse.Core.Event.command` | 命令處理 |
| `message` | `ErisPulse.Core.Event.message` | 訊息事件 |
| `notice` | `ErisPulse.Core.Event.notice` | 通知事件 |
| `request` | `ErisPulse.Core.Event.request` | 請求事件 |
| `meta` | `ErisPulse.Core.Event.meta` | 元事件 |

### 基類

ErisPulse 提供以下基類：

| 基類 | 路徑 | 說明 |
|------|------|------|
| `BaseModule` | `ErisPulse.Core.Bases.BaseModule` | 模組基類 |
| `BaseAdapter` | `ErisPulse.Core.Bases.BaseAdapter` | 適配器基類 |

## 使用範例

### 存取核心模組

```python
from ErisPulse import sdk

# 儲存系統
sdk.storage.set("key", "value")
value = sdk.storage.get("key")

# 設定管理
config = sdk.config.getConfig("MyModule")

# 日誌系統
sdk.logger.info("日誌資訊")

# 適配器管理
adapter = sdk.adapter.get("platform")
await adapter.Send.To("user", "123").Text("Hello")

# 模組管理
module = sdk.module.get("ModuleName")

# 生命週期管理
await sdk.lifecycle.submit_event("custom.event", msg="自訂事件")

# 路由管理
sdk.router.register_http_route("MyModule", "/api", handler, ["GET"])
```

### 使用事件系統

```python
from ErisPulse.Core.Event import command, message, notice, request, meta

# 命令處理
@command("hello", help="問候命令")
async def hello_handler(event):
    await event.reply("你好！")

# 訊息處理
@message.on_group_message()
async def group_handler(event):
    sdk.logger.info(f"收到群訊息: {event.get_text()}")

# 通知處理
@notice.on_friend_add()
async def friend_add_handler(event):
    await event.reply("歡迎新增我為好友！")

# 請求處理
@request.on_friend_request()
async def friend_request_handler(event):
    pass

# 元事件處理
@meta.on_connect()
async def connect_handler(event):
    sdk.logger.info("平台連線成功")
```

### 繼承基類

```python
from ErisPulse.Core.Bases import BaseModule

class MyModule(BaseModule):
    def __init__(self):
        super().__init__()
        self.sdk = sdk
    
    async def on_load(self, event):
        """模組載入"""
        pass
    
    async def on_unload(self, event):
        """模組卸載"""
        pass
```

## 相關文件

- [核心概念](../getting-started/basic-concepts.md) - 理解框架核心概念
- [模組開發指南](../developer-guide/modules/) - 開發自訂模組
- [適配器開發指南](../developer-guide/adapters/) - 開發平台適配器