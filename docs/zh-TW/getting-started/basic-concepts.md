# 基礎概念

本指南介紹 ErisPulse 的核心概念，幫助你理解框架的設計思想和基本架構。

## 事件驅動架構

ErisPulse 採用事件驅動架構，所有的互動都透過事件來傳遞和處理。

### 事件流程

```
使用者發送訊息
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
透過適配器發送回應
      │
      ▼
平台顯示給使用者
```

### OneBot12 標準

ErisPulse 使用 OneBot12 作為核心事件標準。OneBot12 是一個通用的聊天機器人應用介面標準，定義了統一的事件格式。

所有適配器都會將平台特定的事件轉換為 OneBot12 格式，確保程式碼的一致性。

## 核心元件

### 1. SDK 物件

SDK 是所有功能的統一入口點，提供對核心元件的存取。

```python
from ErisPulse import sdk

# 存取核心模組
sdk.storage    # 存儲系統
sdk.config     # 配置系統
sdk.logger     # 日誌系統
sdk.adapter    # 適配器系統
sdk.module     # 模組系統
sdk.router     # 路由系統
sdk.client     # HTTP 客戶端
sdk.lifecycle  # 生命週期系統
```

### 2. Event 物件

Event 物件封裝了事件資料，提供了便捷的存取方法。

```python
@command("info")
async def info_handler(event):
    # 獲取事件資訊
    event_id = event.get_id()
    user_id = event.get_user_id()
    platform = event.get_platform()
    text = event.get_text()
    
    # 發送回覆
    await event.reply(f"使用者: {user_id}, 平台: {platform}")
```

### 3. 適配器

適配器是 ErisPulse 與外部平台之間的橋樑。

**職責：**
- 接收平台原生事件
- 轉換為 OneBot12 標準格式
- 將標準格式事件發送到平台

**示例適配器：**
- Yunhu 適配器：與雲湖平台通訊
- Telegram 適配器：與 Telegram Bot API 通訊
- OneBot11 適配器：與 OneBot11 相容的應用通訊
- Email 適配器：處理郵件收發

### 4. 模組

模組是功能擴充的基本單位，可以：

- 註冊事件處理器
- 實現業務邏輯
- 呼叫適配器發送訊息
- 使用核心模組提供的服務

#### 模組發現機制

ErisPulse 透過 Python 的 `importlib.metadata.entry_points` 發現已安裝的模組。模組在 `pyproject.toml` 中宣告入口點：

```toml
[project.entry-points."erispulse.module"]
MyModule = "my_package:Main"
```

SDK 初始化時會掃描所有 `erispulse.module` 組的入口點，將模組類註冊到 `ModuleManager`，然後按依賴關係拓撲排序後依次初始化。

#### 最小可用模組

```python
from ErisPulse.Core.Bases import BaseModule
from ErisPulse import sdk

class Main(BaseModule):
    def __init__(self):
        self.sdk = sdk
        self.logger = sdk.logger.get_child("MyModule")

    async def on_load(self, event):
        self.logger.info("模組已載入")

    async def on_unload(self, event):
        self.logger.info("模組已卸載")
```

#### 模組生命週期

- **註冊**：SDK 發現模組類並註冊到管理器
- **載入**：建立模組實例，呼叫 `on_load(event)`（`event = {"module_name": "MyModule"}`）
- **卸載**：呼叫 `on_unload(event)`，清理資源

#### 載入策略

透過 `get_load_strategy()` 宣告模組的載入行為：

```python
from ErisPulse.loaders import ModuleLoadStrategy

class Main(BaseModule):
    @staticmethod
    def get_load_strategy():
        return ModuleLoadStrategy(
            lazy_load=True,   # 是否懶載入（預設 True）
            priority=0        # 載入優先級，數值越大越先初始化
        )
```

- **`lazy_load=True`（預設）**：模組在首次被 `sdk.MyModule` 存取時才初始化，減少啟動時間
- **`lazy_load=False`**：SDK 啟動時立即初始化，適合需要監聽生命週期事件或執行定時任務的模組
- **`priority`**：同優先級的模組按註冊順序載入；數值越大越先初始化

> 詳細的懶載入機制說明請參考 [懶載入系統](../advanced/lazy-loading.md)。

## 事件類型

ErisPulse 支援 5 類事件：

| 事件類型 | 裝飾器 | 說明 |
|---------|--------|------|
| 訊息事件 | `@message.on_message()` | 使用者發送的任何訊息（私聊、群聊） |
| 命令事件 | `@command("name")` | 以命令字首開頭的訊息（如 `/hello`） |
| 通知事件 | `@notice.on_friend_add()` 等 | 系統通知（好友新增、群成員變化等） |
| 請求事件 | `@request.on_friend_request()` 等 | 使用者請求（好友請求、群邀請） |
| 元事件 | `@meta.on_connect()` 等 | 系統級事件（連線、斷線、心跳） |

> 各事件類型的詳細用法和程式碼範例請參考 [事件處理入門](event-handling.md)。

## 核心模組說明

### Storage（存儲）

基於 SQLite 的鍵值存儲系統，用於持久化資料。

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

TOML 格式的配置檔案管理。

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
sdk.logger.info("這是一條資訊")
sdk.logger.warning("這是一條警告")
sdk.logger.error("這是一條錯誤")

# 獲取子日誌記錄器
child_logger = sdk.logger.get_child("submodule")
child_logger.info("子模組日誌")
```

**屬性存取語法糖**

除了使用 `get_child()` 方法外，你還可以透過**屬性存取**的方式建立子logger，這是一種更簡潔的**語法糖**寫法：

```python
# 透過屬性存取建立子logger
sdk.logger.mymodule.info("模組訊息")

# 支援嵌套存取
sdk.logger.mymodule.database.info("資料庫訊息")
```

### Router（路由）

HTTP 和 WebSocket 路由管理，基於 FastAPI + Uvicorn。支援裝飾器路由、中介軟體、分組、限流、CORS。

```python
from ErisPulse.Core import HttpRequest

@sdk.router.get("MyModule", "/api")
async def handler(request: HttpRequest):
    data = await request.json()
    return {"status": "ok"}
```

> 完整的路由 API（WebSocket、中介軟體、速率限制、CORS 等）請參考 [路由管理器](../advanced/router.md)。

### Client（網絡客戶端）

統一的網絡客戶端，聚合了 HTTP 請求、WebSocket 連線、連線池管理、自動重試、逾時控制、請求統計和生命週期事件整合。

```python
from ErisPulse.Core import client

# HTTP 請求
resp = await client.get("https://api.example.com/users")
data = await resp.json()

# 帶重試和逾時
resp = await client.get(url, timeout=30, max_retries=3)

# WebSocket 連線
ws = await client.ws_connect("wss://example.com/ws")
async for text in ws.iter_text():
    await ws.send_text(f"Echo: {text}")
```

> 完整的網絡客戶端 API 請參考 [網絡客戶端](../advanced/http-client.md)。

## SendDSL 訊息發送

適配器提供鏈式呼叫的訊息發送介面。

### 基礎發送

```python
# 獲取適配器實例
yunhu = sdk.adapter.get("yunhu")

# 發送訊息
await yunhu.Send.To("user", "U1001").Text("Hello")

# 指定發送帳號
await yunhu.Send.Using("bot1").To("group", "G1001").Text("群訊息")
```

### 鏈式修飾

```python
# @使用者
await yunhu.Send.To("group", "G1001").At("U2001").Text("@訊息")

# 回覆訊息
await yunhu.Send.To("group", "G1001").Reply("msg123").Text("回覆")

# @全體
await yunhu.Send.To("group", "G1001").AtAll().Text("公告")
```

### Event 回覆方法

Event 物件提供了便捷的回覆方法：

```python
@command("test")
async def test_handler(event):
    # 簡單文字回覆
    await event.reply("回覆內容")
    
    # 發送圖片
    await event.reply("http://example.com/image.jpg", method="Image")
    
    # 發送語音
    await event.reply("http://example.com/voice.mp3", method="Voice")
```

## 懶載入系統

ErisPulse 預設啟用模組懶載入，模組只在首次被存取（如 `sdk.MyModule`）時才初始化，顯著提高啟動速度。

```python
from ErisPulse.loaders import ModuleLoadStrategy

class Main(BaseModule):
    @staticmethod
    def get_load_strategy():
        return ModuleLoadStrategy(
            lazy_load=True,   # 啟用懶載入（預設）
            priority=0        # 載入優先級，數值越大越先初始化
        )
```

**需要停用懶載入的場景（`lazy_load=False`）：**
- 監聽生命週期事件的模組（如 `core.init.complete`）
- 啟動定時任務或後台服務的模組
- 需要在其他模組載入前完成初始化的模組

> 詳細的懶載入機制和注意事項請參考 [懶載入系統](../advanced/lazy-loading.md)。

## 下一步

- [事件處理入門](event-handling.md) - 學習如何處理各類事件
- [常見任務範例](common-tasks.md) - 掌握常用功能的實現