# 核心模組 API

本文檔提供 ErisPulse 核心模組的 API 快速參考，包含方法簽名和簡要說明。詳細用法和示例請點擊各模組的「完整文件」連結。

## Storage 模組

基於 SQLite 的鍵值儲存系統，支援通用 SQL 串流查詢。

### 基本操作

```python
from ErisPulse import sdk

sdk.storage.set("key", "value")
value = sdk.storage.get("key", default_value)
keys = sdk.storage.keys()
sdk.storage.delete("key")
```

### 批量操作

```python
sdk.storage.set_multi({"key1": "val1", "key2": "val2"})
values = sdk.storage.get_multi(["key1", "key2"])
sdk.storage.delete_multi(["key1", "key2"])
```

### 事務操作

```python
with sdk.storage.transaction():
    sdk.storage.set("key1", "value1")
    sdk.storage.set("key2", "value2")
```

### 屬性存取

```python
sdk.storage.my_key          # 等價於 sdk.storage.get("my_key")
sdk.storage.my_key = "val"  # 等價於 sdk.storage.set("my_key", "val")
```

### SQL 串流查詢

Storage 模組提供串流呼叫風格的通用 SQL 查詢建構器，支援自訂表的 CRUD 操作。

```python
sdk.storage.CreateTable("users", {
    "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
    "name": "TEXT NOT NULL",
})

sdk.storage.Table("users").Insert({"name": "Alice"}).Execute()
rows = sdk.storage.Table("users").Select("name").Where("id > ?", 0).Execute()
```

> 完整的串流查詢 API（Select/Insert/Update/Delete/Where/OrderBy/Limit、AlterTable、事務等）請參考 [SQL 查詢建構器](../advanced/sql-builder.md)。

### 儲存後端抽象

`StorageManager` 繼承自 `BaseStorage` 抽象基類，支援擴展其他儲存介質（Redis、MySQL 等）。

```python
from ErisPulse.Core.Bases.storage import BaseStorage, BaseQueryBuilder
```

### 異步介面

Storage 和 Config 模組均提供異步方法（前綴 `a`），可在異步處理器中安全調用。同步方法繼續保留，無需修改現有程式碼。

```python
# 異步儲存
value = await sdk.storage.aget("key")
await sdk.storage.aset("key", "value")
await sdk.storage.adelete("key")
keys = await sdk.storage.aget_all_keys()
await sdk.storage.aclear()

# 異步批量操作
values = await sdk.storage.aget_multi(["k1", "k2"])
await sdk.storage.aset_multi({"k1": "v1", "k2": "v2"})
await sdk.storage.adelete_multi(["k1", "k2"])

# 異步配置
value = await sdk.config.agetConfig("MyModule.key")
await sdk.config.asetConfig("MyModule.key", "value")
await sdk.config.aforce_save()
await sdk.config.areload()
```

## Config 模組

TOML 格式的配置文件管理，支援點號分隔的鍵路徑。

### API 概覽

| 方法 | 說明 |
|------|------|
| `getConfig(key, default)` | 讀取配置，支援點號路徑如 `"MyModule.subkey"` |
| `setConfig(key, value, immediate=False)` | 寫入配置。`immediate=True` 時立即儲存到檔案 |
| `force_save()` | 強制將記憶體中的配置寫入檔案 |
| `reload()` | 從檔案重新載入配置 |
| `agetConfig(key, default)` | 異步讀取配置 |
| `asetConfig(key, value, immediate)` | 異步寫入配置 |
| `aforce_save()` | 異步強制儲存 |
| `areload()` | 異步重新載入 |

### 範例

```python
config = sdk.config.getConfig("MyModule", {})
value = sdk.config.getConfig("MyModule.timeout", 30)

sdk.config.setConfig("MyModule", {"key": "value"})
sdk.config.setConfig("MyModule.timeout", 60, immediate=True)
```

> `setConfig` 預設採用延遲寫入（每 5 秒批量儲存），設定 `immediate=True` 可立即持久化到配置檔案。配置變更會觸發 `config.set` 生命週期事件。

## Logger 模組

模組化日誌系統，基於 Rich 輸出，支援子日誌器和模組級別控制。

### 基本用法

```python
sdk.logger.debug("調試資訊")
sdk.logger.info("運行資訊")
sdk.logger.warning("警告資訊")
sdk.logger.error("錯誤資訊")
sdk.logger.critical("致命錯誤")
```

### 子日誌器

```python
child_logger = sdk.logger.get_child("MyModule")
child_logger.info("子模組日誌")

child_logger.get_child("utils")  # 支援嵌套
```

### 日誌等級控制

```python
sdk.logger.set_level("DEBUG")                          # 全局等級
sdk.logger.set_module_level("MyModule", "DEBUG")       # 模組等級

# 支援的等級（由低到高）：
# TRACE, DEBUG, INFO, WARNING, ERROR, CRITICAL
# TRACE 為最低等級，輸出框架內部詳細調試資訊（事件分發、路由註冊等）
sdk.logger.set_level("TRACE")                          # 開啟全部日誌
```

### 日誌訂閱（推模式）

供 Dashboard 等模組即時接收結構化日誌，支援等級篩選和歷史補發。

> **顯式訂閱低等級日誌**：訂閱器的 `min_level` 可低於全局日誌等級。此時低等級日誌**僅推送到匹配的訂閱器**，不會輸出到控制台，也不會寫入記憶體，從而避免污染主日誌流。
>
> ```python
> # 全局為 INFO，仍可單獨訂閱 DEBUG 日誌
> @sdk.logger.handler("debug-tracer", min_level="DEBUG")
> def on_debug(log_data: dict): ...
> ```

```python
# 裝飾器方式
@sdk.logger.handler("my-handler", min_level="INFO")
def on_log(log_data: dict):
    # log_data = {
    #     "timestamp": "2026-06-29T22:00:00.123456",
    #     "level": "WARNING", "level_num": 30,
    #     "module": "ErisPulse.Core.adapter",
    #     "message": "嚴格模式：...",
    # }
    pass

# 直接呼叫方式
sdk.logger.handler("my-handler", min_level="INFO")(on_log)
sdk.logger.remove_handler("my-handler")
```

| 方法 | 說明 |
|------|------|
| `handler(id, *, min_level)(func)` | 裝飾器/直接呼叫兩用。`id` 為空時取函數名。`min_level` 可低於全局等級（低等級日誌僅推送到匹配的訂閱器，不進控制台/記憶體）。註冊時自動補發歷史日誌 |
| `remove_handler(id)` | 移除訂閱器 |

### 輸出控制

```python
sdk.logger.set_output_file("app.log")
sdk.logger.save_logs("log.txt")
sdk.logger.get_logs("MyModule")
sdk.logger.set_memory_limit(1000)
```

## Adapter 模組

適配器管理器，管理多平台適配器的註冊、啟動和關閉。

### API 概覽

| 方法 | 說明 |
|------|------|
| `get(platform)` | 獲取適配器實例 |
| `exists(platform)` | 檢查適配器是否已註冊 |
| `enable(platform)` / `disable(platform)` | 啟用/禁用適配器 |
| `is_enabled(platform)` | 檢查是否啟用 |
| `startup(platforms)` / `shutdown(platforms)` | 啟動/關閉適配器 |
| `is_running(platform)` | 檢查適配器是否正在運行 |
| `list_running()` | 列出所有正在運行的適配器 |
| `platforms` | 獲取所有平台名稱列表 |

### 適配器事件

```python
@sdk.adapter.on("message")
async def handle_message(event):
    pass

@sdk.adapter.on("message", platform="yunhu")
async def handle_yunhu_message(event):
    pass
```

### Bot 狀態查詢

```python
sdk.adapter.get_bot_info("telegram", "123456")
sdk.adapter.list_bots("telegram")
sdk.adapter.is_bot_online("telegram", "123456")
sdk.adapter.get_status_summary()
```

> 完整的適配器管理 API 請參考 [適配器系統 API](adapter-system.md)。

## 模組

模組管理器，管理插件的註冊、載入和卸載。

### API 概覽

| 方法 | 說明 |
|------|------|
| `get(name)` | 取得模組實例或懶加載代理（已註冊但未載入時返回代理） |
| `exists(name)` | 檢查是否已註冊 |
| `is_loaded(name)` | 檢查是否已載入 |
| `is_enabled(name)` | 檢查是否啟用 |
| `enable(name)` / `disable(name)` | 啟用/停用模組 |
| `load(name)` / `unload(name)` | 載入/卸載模組 |
| `call(module, method, *args, timeout=None, **kwargs)` | 跨模組呼叫目標模組的服務方法（協定化 RPC） |
| `emit_to(module, event, data)` | 向指定模組定向投遞生命週期事件 |
| `list_registered()` | 列出已註冊模組 |
| `list_loaded()` | 列出已載入模組 |
| `get_info(name)` | 取得模組資訊 |
| `get_status_summary()` | 取得模組狀態摘要 |

### 屬性存取

```python
module = sdk.module.get("ModuleName")
module = sdk.module.ModuleName
module = sdk.ModuleName  # 等價快捷方式
```

### 模組間呼叫（RPC）

```python
# 協定化呼叫：類型化錯誤 / 懶模組自動喚醒 / owner 歸因 / 超時語義
result = await sdk.module.call("Chat", "get_history", session_id, n=20)
```

與服務方裸屬性存取 `sdk.module.Chat.get_history(...)` 的差異：

| | `module.call()` | 裸屬性存取 |
|---|---|---|
| 目標未註冊/未啟用 | 抛 `ModuleNotAvailableError` | 抛 `AttributeError` |
| 懶加載模組 | 自動喚醒 | 異步初始化模組拋 RuntimeError |
| `current_owner` | 歸因到目標模組 | 保持呼叫方 |
| 超時 | 預設 30s，可覆蓋 | 無 |
| scope 審計 | `actions.<呼叫方>.call` | 無 |

### 服務契約（meta.services）

服務方在 `get_meta()` 的 `services` 欄位宣告對外白名單（與 `commands` 對稱），宣告後呼叫面收窄：

```python
class ChatModule(BaseModule):
    @staticmethod
    def get_meta() -> ModuleMeta:
        return ModuleMeta(services=["get_history", "translate"])

    async def get_history(self, session_id, n=20): ...
```

- **預設 = 開發者無感**：未宣告 `services` 時任意**公開**方法可被呼叫（向後相容），底線私有方法始終禁止；限制的主控制權在使用者端 scope 配置
- 宣告後：僅白名單內方法可呼叫，越界拋 `ServiceNotProvidedError`
- 呼叫方限制：`scope.set_action("CallerModule", "call", deny="Chat.get_history")`

**服務介紹（description）**：`services` 支援 dict 形態為每個服務宣告介紹  
（支援純字串或 i18n 字典），供服務目錄 / AI 呼叫點描述消費：

```python
return ModuleMeta(
    services=[
        "get_history",                              # 簡單形態：介紹自動取方法 docstring 首行
        {"name": "translate", "description": "把文本翻譯成指定語言"},
        {"name": "summarize", "description": {"i18n": "Chat.meta.svc.summarize", "default": "摘要對話"}},
    ],
)
```

介紹解析優先級：**顯式 description（i18n 解析為當前語言）> 方法 docstring 首行 > 空字串**。

### 服務目錄（services）

```python
sdk.module.services()
# {'Chat': [{'name': 'get_history', 'signature': '(session_id, n=20)',
#            'description': '取得會話歷史'}]}

sdk.module.services("Chat")  # 僅查詢指定模組
```

僅列出**顯式宣告** `meta.services` 的模組；每個服務附方法簽名字串  
與介紹文字，為 MCP 化（呼叫點暴露給 AI）提供資料基礎。

### 定向事件（emit_to）

```python
# 投遞方：校驗目標模組啟用後投遞到 module.<名稱>.<事件>
await sdk.module.emit_to("Chat", "message_received", {"text": "hi"})

# 訂閱方（Chat 模組內）：註冊命名空間鈎子
lifecycle.on("module.Chat.message_received", handler)
lifecycle.on("module.Chat", handler)  # 或接收該模組的全部定向事件
```

> [!NOTE]
> 本節能力新增於 ErisPulse **2.8.0+**

## Lifecycle 模組

事件驅動的生命週期管理器，提供事件提交和監聽功能。

### API 概覽

| 方法 | 說明 |
|------|------|
| `on(event, priority=0)` | 裝飾器註冊事件處理器，支援點號匹配和通配符 `*` |
| `register(event, handler, priority=0)` | 函數式註冊處理器 |
| `unregister(event, handler=None)` | 移除處理器 |
| `emit(event, data)` | 異步觸發事件 |
| `emit_sync(event, data)` | 同步觸發事件 |
| `submit_event(event_type, msg, data, source)` | 提交標準格式事件（相容舊版） |
| `start_timer(id)` / `stop_timer(id)` | 性能計時器 |

### 範例

```python
@sdk.lifecycle.on("module.init")
async def handle_module_init(event_data):
    print(f"模組初始化: {event_data}")

@sdk.lifecycle.on("module")
async def handle_any_module_event(event_data):
    print(f"模組事件: {event_data}")

await sdk.lifecycle.emit("custom.event", {"key": "value"})
```

> 完整的標準事件列表和詳細用法請參考 [生命週期管理](../advanced/lifecycle.md)。

## Router 模組

HTTP/WebSocket 路由管理器，基於 FastAPI + Uvicorn，支援裝飾器路由、中間件、分組、限流、CORS。

> 完整的路由 API 文件（裝飾器路由、WebSocket、中間件、速率限制、CORS、安全頭等）請參考 [路由管理器](../advanced/router.md)。

### 快速參考

```python
# HTTP 路由
@sdk.router.get("MyModule", "/api")
async def handler(request: HttpRequest):
    return {"status": "ok"}

# WebSocket 路由
@sdk.router.ws("MyModule", "/ws")
async def ws_handler(ws: WebSocketConnection):
    async for text in ws.iter_text():
        await ws.send_text(f"Echo: {text}")

# 路由分組
group = sdk.router.group("MyModule", prefix="/v1")
@group.get("/users")
async def list_users(request: HttpRequest):
    return {"users": []}
```

## HTTP Client 模組

統一網路客戶端，聚合 HTTP 請求、WebSocket 連接、連接池管理、自動重試、請求統計和生命週期事件集成。

> 完整的網路客戶端文件（請求方法、回應物件、WebSocket 客戶端、例外體系等）請參考 [網路客戶端](../advanced/http-client.md)。

### 快速參考

```python
from ErisPulse.Core import client

# HTTP 請求
resp = await client.get("https://api.example.com/users")
data = await resp.json()

# WebSocket
ws = await client.ws_connect("wss://example.com/ws")
async for text in ws.iter_text():
    await ws.send_text(f"Echo: {text}")
```

## SDK 調試

### dump_state()

匯出框架當前運行狀態的快照，用於調試和診斷。

```python
import json
state = sdk.dump_state()
print(json.dumps(state, indent=2, ensure_ascii=False, default=str))
```

回傳結構包含以下子系統的狀態：

| 字段 | 說明 |
|------|------|
| `sdk` | SDK 初始化狀態、Python 版本、運行平台、時間戳 |
| `adapters` | 已註冊/已啟動的適配器列表、各平台 Bot 在線狀態 |
| `modules` | 已註冊/已啟用/已禁用/懶加載的模塊列表 |
| `events` | 各類事件處理器數量（message/notice/request/meta/commands） |
| `router` | 伺服器運行狀態、HTTP/WebSocket 路由數量 |

> [!NOTE]
> 新增於 ErisPulse **2.5.2+**

## Interaction 交互會話

管理 wait_reply 掛起等待與會話互斥租約（`sdk.interaction`）。

### 常用方法

```python
# 會話定時提醒：5 分鐘無回覆則提醒，使用者回覆自動取消
reminder = event.remind(300, "還在嗎？")
reminder.cancel()  # 手動取消

# 超時升級：到點必達（不被回覆取消）
event.escalate(1800, lambda e: notify_master("30 分鐘未處理"))

# 多路等待：先到先得
which, reply = await event.select(
    event.expect(pattern="同意*", user="A"),
    event.expect(pattern="拒絕*", user="B"),
    timeout=60,
)

# 會話級等待：同群任何人的回覆均可命中
reply = await event.wait_reply(session=True, prompt="誰能幫忙答一下？")

# 查詢會話當前歸屬（誰正在與該使用者交互）
owner = sdk.interaction.get_owner_of(event)

# 聲明會話互斥租約（被佔用返回 None）
lease = sdk.interaction.acquire(event)
if lease:
    try:
        ...  # 獨佔交互
    finally:
        lease.release()

# 上下文管理器形式（被佔用拋 SessionOccupiedError）
with sdk.interaction.hold(event) as lease:
    ...

# 掛起會話統計
sdk.interaction.counts()  # {'waits': 2, 'leases': 1, 'timers': 3, 'owners': {'Chat': 3}}
```

模組卸載 / 适配器關閉時其掛起的等待與定時器自動取消（等待方立即返回 `None`），
回覆命中時自動复查 scope 權限（使用者被拉黑 / 模組被解綁則終止等待）。

> [!NOTE]
> 本節能力新增於 ErisPulse **2.8.0+**

## Transcript 會話收件箱

每會話近期訊息流的自動記錄與查詢（`sdk.transcript`），作為 AI 對話、
防重複發送等上下文記憶類模組的公共底座。

### 常用方法

```python
# 便捷查詢（推薦）：當前會話最近 20 條（包含使用者與機器人，時間升序）
messages = await event.history(20)
for m in messages:
    print(m["role"], ":", m["text"])

# 管理器 API
sdk.transcript.append(event, "user", "文本")
sdk.transcript.get(event, n=20)
sdk.transcript.clear(event)
```

配置（`ErisPulse.transcript`）：`enabled`（預設開啟）、`max_per_session`（每會話上限，預設 50）、
`ttl_hours`（全域過期時間，預設 168 小時）。資料存於獨立 SQLite 表，超出限制或過期時惰性清理。

> [!NOTE]
> 本節功能新增於 ErisPulse **2.8.0+**
> [!TIP]
> 本功能依賴 SQLite，請確保環境已安裝 sqlite3 模組。

## 相關文件

- [事件系統 API](event-system.md) - Event 模組 API
- [適配器系統 API](adapter-system.md) - Adapter 管理 API
- [SQL 查詢建構器](../advanced/sql-builder.md) - SQL 串流查詢完整文件
- [路由管理器](../advanced/router.md) - 路由管理器完整文件
- [網路客戶端](../advanced/http-client.md) - 網路客戶端完整文件
- [生命週期管理](../advanced/lifecycle.md) - 生命週期完整文件