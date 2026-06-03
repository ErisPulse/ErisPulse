# 基礎概念

本指南介紹 ErisPulse 的核心概念，幫助你理解框架的設計思想和基本架構。

## 事件驅動架構

ErisPulse 採用事件驅動架構，所有的交互都通過事件來傳遞和處理。

### 事件流程

```
用戶發送消息
      │
      ▼
平台接收
      │
      ▼
適配器接收平台原生事件
      │
      ▼
轉換為 OneBot12 標準事件
      │
      ▼
提交到事件系統
      │
      ▼
分發給已註冊的處理器
      │
      ▼
模組處理事件
      │
      ▼
通過適配器發送響應
      │
      ▼
平台顯示給用戶
```

### OneBot12 標準

ErisPulse 使用 OneBot12 作為核心事件標準。OneBot12 是一個通用的聊天機器人應用介面標準，定義了統一的事件格式。

所有適配器都將平台特定的事件轉換為 OneBot12 格式，確保代碼的一致性。

## 核心組件

### 1. SDK 對象

SDK 是所有功能的統一入口點，提供對核心組件的訪問。

```python
from ErisPulse import sdk

# 訪問核心模組
sdk.storage    # 存儲系統
sdk.config     # 配置系統
sdk.logger     # 日誌系統
sdk.adapter    # 適配器系統
sdk.module     # 模組系統
sdk.router     # 路由系統
sdk.client     # HTTP 客戶端
sdk.lifecycle  # 生命周期系統
```

### 2. Event 對象

Event 對象封裝了事件數據，提供了便捷的訪問方法。

```python
@command("info")
async def info_handler(event):
    # 獲取事件信息
    event_id = event.get_id()
    user_id = event.get_user_id()
    platform = event.get_platform()
    text = event.get_text()
    
    # 發送回复
    await event.reply(f"用戶: {user_id}, 平台: {platform}")
```

### 3. 適配器

適配器是 ErisPulse 與外部平台之間的橋梁。

**職責：**
- 接收平台原生事件
- 轉換為 OneBot12 標準格式
- 將標準格式事件發送到平台

**示例適配器：**
- Yunhu 適配器：與雲湖平台通信
- Telegram 適配器：與 Telegram Bot API 通信
- OneBot11 適配器：與 OneBot11 兼容的應用通信
- Email 適配器：處理郵件收發

### 4. 模組

模組是功能擴展的基本單位，可以：

- 註冊事件處理器
- 實現業務邏輯
- 調用適配器發送消息
- 使用核心模組提供的服務

```python
from ErisPulse.Core.Bases import BaseModule
from ErisPulse import sdk

class MyModule(BaseModule):
    def __init__(self):
        self.sdk = sdk
        self.logger = sdk.logger.get_child("MyModule")

    @staticmethod
    def get_load_strategy():
        from ErisPulse.loaders import ModuleLoadStrategy
        return ModuleLoadStrategy(
            lazy_load=True,
            priority=0
        )

    async def on_load(self, event):
        """模組加載時調用"""
        # 註冊事件處理器
        @command("mycmd", help="我的命令")
        async def my_command(event):
            await event.reply("命令執行成功")

        self.logger.info("模組已加載")

    async def on_unload(self, event):
        """模組卸載時調用"""
        self.logger.info("模組已卸載")
```

## 事件類型

### 消息事件

處理用戶發送的任何消息（包括私聊和群聊）。

```python
from ErisPulse.Core.Event import message

@message.on_message()
async def message_handler(event):
    text = event.get_text()
    await event.reply(f"收到消息: {text}")
```

### 命令事件

處理以命令前綴開頭的消息（如 `/hello`）。

```python
from ErisPulse.Core.Event import command

@command("hello", help="發送問候")
async def hello_handler(event):
    await event.reply("你好！")
```

### 通知事件

處理系統通知（如好友添加、群成員變化）。

```python
from ErisPulse.Core.Event import notice

@notice.on_friend_add()
async def friend_add_handler(event):
    await event.reply("歡迎添加我為好友！")
```

### 請求事件

處理用戶請求（如好友請求、群邀請）。

```python
from ErisPulse.Core.Event import request

@request.on_friend_request()
async def friend_request_handler(event):
    await event.reply("已收到你的好友請求")
```

### 元事件

處理系統級事件（如連接、心跳）。

```python
from ErisPulse.Core.Event import meta

@meta.on_connect()
async def connect_handler(event):
    platform = event.get_platform()
    sdk.logger.info(f"{platform} 連接成功")
```

## 核心模組說明

### Storage（儲存）

基於 SQLite 的鍵值存儲系統，用於持久化數據。

```python
# 設置值
sdk.storage.set("key", "value")

# 獲取值
value = sdk.storage.get("key", "default_value")

# 批量操作
sdk.storage.set_multi({
    "key1": "value1",
    "key2": "value2"
})

# 事務
with sdk.storage.transaction():
    sdk.storage.set("key1", "value1")
    sdk.storage.set("key2", "value2")
```

### Config（配置）

TOML 格式的配置文件管理。

```python
# 獲取配置
config = sdk.config.getConfig("MyModule", {})

# 設置配置
sdk.config.setConfig("MyModule", {"key": "value"})

# 讀取嵌套配置
value = sdk.config.getConfig("MyModule.subkey", "default")
```

### Logger（日誌）

模組化日誌系統。

```python
# 記錄日誌
sdk.logger.info("這是一條信息")
sdk.logger.warning("這是一條警告")
sdk.logger.error("這是一條錯誤")

# 獲取子日誌記錄器
child_logger = sdk.logger.get_child("submodule")
child_logger.info("子模組日誌")
```

**屬性訪問語法糖**

除了使用 `get_child()` 方法外，你還可以通過**屬性訪問**的方式創建子logger，這是一種更簡潔的**語法糖**寫法：

```python
# 通過屬性訪問創建子logger
sdk.logger.mymodule.info("模組消息")

# 支持嵌套訪問
sdk.logger.mymodule.database.info("數據庫消息")
```

### Router（路由）

HTTP 和 WebSocket 路由管理，支援 FastAPI 原生類型和 ErisPulse 抽象類型。

> 路由處理器支援兩種類型註解：FastAPI 原生類型（`fastapi.Request` / `fastapi.WebSocket`）和 ErisPulse 抽象類型（`HttpRequest` / `WebSocketConnection`）。推薦使用抽象類型以獲得更好的可移植性。

```python
from ErisPulse import sdk

# 方式一：使用 ErisPulse 抽象類型（推薦）
from ErisPulse.Core import HttpRequest, WebSocketConnection

@sdk.router.get("MyModule", "/api")
async def handler(request: HttpRequest):
    data = await request.json()
    return {"status": "ok"}

@sdk.router.ws("MyModule", "/ws")
async def ws_handler(ws: WebSocketConnection):
    data = await ws.receive_text()
    await ws.send_text(f"Echo: {data}")

# 方式二：使用 FastAPI 原生類型（兼容已有代碼）
from fastapi import Request, WebSocket

@sdk.router.get("MyModule", "/api2")
async def handler2(request: Request):
    return {"status": "ok"}
```

{!--< tips >!--}
> **自動注入**：路由系統會根據參數註解自動注入對應類型的對象，無需手動創建。
> 
> **常見問題**：如果看到 `{"detail":[{"type":"missing","loc":["query","request"],"msg":"Field required"}]}` 錯誤，說明缺少類型註解。請確保 HTTP 處理器參數使用 `request` 註解，WebSocket 處理器參數使用 `websocket` 或 `ws` 註解。

更多路由功能請參考 [路由管理器](../advanced/router.md)。

### Client（HTTP 客戶端）

統一的 HTTP 客戶端，用於發送 HTTP 請求。模組和適配器應優先使用全局客戶端而非直接導入 `aiohttp`。

```python
from ErisPulse.Core import client

# GET 請求
resp = await client.get("https://api.example.com/users")
data = await resp.json()

# POST 請求
resp = await client.post(
    "https://api.example.com/users",
    json={"name": "Alice"},
)

# 響應屬性
resp.status        # 狀態碼 (如 200)
resp.headers       # 響應頭
body = await resp.text()   # 文本響應體
data = await resp.json()   # JSON 解析
```

{!--< tips >!--}
> 全局客戶端具有自動重試、超時控制、請求統計和生命周期事件集成等功能。詳見 [HTTP 客戶端](../advanced/http-client.md)。
>
> 也可通過 `from ErisPulse import sdk` 使用 `sdk.client`，效果相同。

## SendDSL 消息發送

適配器提供鏈式調用的消息發送接口。

### 基礎發送

```python
# 獲取適配器實例
yunhu = sdk.adapter.get("yunhu")

# 發送消息
await yunhu.Send.To("user", "U1001").Text("Hello")

# 指定發送賬號
await yunhu.Send.Using("bot1").To("group", "G1001").Text("群消息")
```

### 鏈式修飾

```python
# @用戶
await yunhu.Send.To("group", "G1001").At("U2001").Text("@消息")

# 回復消息
await yunhu.Send.To("group", "G1001").Reply("msg123").Text("回复")

# @全體
await yunhu.Send.To("group", "G1001").AtAll().Text("公告")
```

### Event 回復方法

Event 對象提供了便捷的回复方法：

```python
@command("test")
async def test_handler(event):
    # 簡單文本回复
    await event.reply("回复内容")
    
    # 發送圖片
    await event.reply("http://example.com/image.jpg", method="Image")
    
    # 發送語音
    await event.reply("http://example.com/voice.mp3", method="Voice")
```

## 懶載入系統

ErisPulse 支持模組懶載入，模組只在首次被訪問時才初始化，提高啟動速度。

```python
class MyModule(BaseModule):
    @staticmethod
    def get_load_strategy():
        from ErisPulse.loaders import ModuleLoadStrategy
        return ModuleLoadStrategy(
            lazy_load=True,   # 啟用懶載入（默認）
            priority=0       # 載入優先級
        )
```

**需要立即載入的場景：**
- 監聽生命周期事件的模組
- 定時任務模組
- 需要在應用啟動時就初始化的模組

## 下一步

- [事件處理入門](event-handling.md) - 學習如何處理各類事件
- [常見任務示例](common-tasks.md) - 掌握常用功能的實現