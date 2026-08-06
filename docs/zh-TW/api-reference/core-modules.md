# 核心模組 API

本文件提供 ErisPulse 核心模組的 API 快速參考，包含方法簽章與簡要說明。詳細用法與範例請點擊各模組的「完整文件」連結。

```
Language: [简体中文](../zh-CN/README.md) | 繁體中文
```

::: tip
本文件提供 ErisPulse 核心模組的 API 快速參考，包含方法簽章與簡要說明。詳細用法與範例請點擊各模組的「完整文件」連結。
:::

## 模組詳情

下表列出核心模組的主要功能及入口方法。

::: tip
:::

| 模組名稱 | 描述 | 文件連結 |
| :--- | :--- | :--- |
| **ErisCore** | 核心邏輯與初始化 | [完整文件](docs/zh-TW/core/eris-core.md) |
| **Events** | 事件處理 | [完整文件](docs/zh-TW/core/events.md) |
| **Utils** | 工具函式 | [完整文件](docs/zh-TW/core/utils.md) |
| **Schema** | 資料架構與驗證 | [完整文件](docs/zh-TW/core/schema.md) |

::: tip
:::

## 核心模組 API

### ErisCore

核心邏輯與初始化。

::: tip
:::

#### 方法

*   **`init(config: ErisCoreConfig): Promise`** - 初始化核心模組。
    *   **參數**：
        *   `config`: 模組配置。
    *   **回傳**：成功時回傳 `Promise<void>`，失敗時回傳 `Promise<Error>`。
    *   **範例**：
        ```typescript
        const config = {
            logger: 'eris-logger',
            features: ['auth', 'cache'],
        };

        // 這裡是中文註解 - 這裡是中文字串 - 這裡也是中文 - 中文註解2
        const initPromise = erisCore.init(config);

        initPromise.then(() => {
            console.log('Initialization successful - 初始化成功 - success - 中文: 成功');
        }).catch((error) => {
            console.error('Initialization failed - 初始化失敗 - error - 中文: 失敗');
        });
        ```

### Events

事件處理。

::: tip
:::

#### 方法

*   **`on(event: string, listener: (...args: any[]) => void): void`** - 註冊事件監聽器。
    *   **參數**：
        *   `event`: 事件名稱。
        *   `listener`: 回呼函式。
    *   **範例**：
        ```typescript
        // 監聽事件 - 監聽事件
        events.on('messageCreate', (message) => {
            console.log(`Received message from user: ${message.author.username}`);
        });
        ```

### Utils

工具函式。

::: tip
:::

#### 方法

*   **`validate(schema: object, data: any): boolean`** - 驗證資料是否符合架構。
    *   **參數**：
        *   `schema`: 架構定義。
        *   `data`: 要驗證的資料。
    *   **回傳**：布林值，表示是否通過驗證。
    *   **範例**：
        ```typescript
        const schema = {
            name: 'string',
            age: 'number',
        };

        const userData = { name: 'Alice', age: 25 };

        // 驗證 - 中文
        const isValid = utils.validate(schema, userData);
        console.log(isValid ? 'Data is valid - 資料有效 - valid - 中文: 有效' : 'Data is invalid - 資料無效 - invalid - 中文: 無效');
        ```

### Schema

資料架構與驗證。

::: tip
:::

#### 方法

*   **`create(type: string, definition: any): SchemaType`** - 建立架構類型。
    *   **參數**：
        *   `type`: 類型名稱。
        *   `definition`: 架構定義。
    *   **回傳**：新建立的架構類型。
    *   **範例**：
        ```typescript
        const userSchema = schema.create('user', {
            properties: {
                id: 'string',
                name: 'string',
            },
            required: ['id', 'name'],
        });

        const user = {
            id: '12345',
            name: 'Alice',
        };

        // 驗證 - 中文
        if (userSchema.validate(user)) {
            console.log('User is valid - 使用者有效 - valid - 中文: 有效');
        }
        ```

::: tip
:::

**相關連結**：
*   [核心模組概覽](docs/zh-TW/core/README.md)
*   [架構文件](docs/zh-TW/core/schema.md)
*   [工具函式](docs/zh-TW/core/utils.md)

## Storage 模組

基於 SQLite 的鍵值儲存系統，支援通用 SQL 鏈式查詢。

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
sdk.storage.my_key          # 等同於 sdk.storage.get("my_key")
sdk.storage.my_key = "val"  # 等同於 sdk.storage.set("my_key", "val")
```

### SQL 鏈式查詢

Storage 模組提供鏈式呼叫風格的通用 SQL 查詢建構器，支援自訂表的 CRUD 操作。

```python
sdk.storage.CreateTable("users", {
    "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
    "name": "TEXT NOT NULL",
})

sdk.storage.Table("users").Insert({"name": "Alice"}).Execute()
rows = sdk.storage.Table("users").Select("name").Where("id > ?", 0).Execute()
```

> 完整的鏈式查詢 API（Select/Insert/Update/Delete/Where/OrderBy/Limit、AlterTable、事務等）請參考 [SQL 查詢建構器](../zh-TW/advanced/sql-builder.md)。

### 儲存後端抽象

`StorageManager` 繼承自 `BaseStorage` 抽象基底類別，支援擴充其他儲存媒體（Redis、MySQL 等）。

```python
from ErisPulse.Core.Bases.storage import BaseStorage, BaseQueryBuilder
```

### 非同步介面

Storage 和 Config 模組均提供非同步方法（字首 `a`），可在非同步處理器中安全呼叫。同步方法繼續保留，無需修改現有程式碼。

```python
# 非同步儲存
value = await sdk.storage.aget("key")
await sdk.storage.aset("key", "value")
await sdk.storage.adelete("key")
keys = await sdk.storage.aget_all_keys()
await sdk.storage.aclear()

# 非同步批量操作
values = await sdk.storage.aget_multi(["k1", "k2"])
await sdk.storage.aset_multi({"k1": "v1", "k2": "v2"})
await sdk.storage.adelete_multi(["k1", "k2"])

# 非同步設定
value = await sdk.config.agetConfig("MyModule.key")
await sdk.config.asetConfig("MyModule.key", "value")
await sdk.config.aforce_save()
await sdk.config.areload()

## Config 模組

TOML 格式的配置檔案管理，支援點號分隔的鍵路徑。

### API 概覽

| 方法 | 說明 |
|------|------|
| `getConfig(key, default)` | 讀取配置，支援點號路徑如 `"MyModule.subkey"` |
| `setConfig(key, value, immediate=False)` | 寫入配置。`immediate=True` 時立即儲存到檔案 |
| `force_save()` | 強制將記憶體中的配置寫入檔案 |
| `reload()` | 從檔案重新載入配置 |
| `agetConfig(key, default)` | 非同步讀取配置 |
| `asetConfig(key, value, immediate)` | 非同步寫入配置 |
| `aforce_save()` | 非同步強制儲存 |
| `areload()` | 非同步重新載入 |

### 範例

```python
config = sdk.config.getConfig("MyModule", {})
value = sdk.config.getConfig("MyModule.timeout", 30)

sdk.config.setConfig("MyModule", {"key": "value"})
sdk.config.setConfig("MyModule.timeout", 60, immediate=True)
```

> `setConfig` 預設採用延遲寫入（每 5 秒批次儲存），設定 `immediate=True` 可立即持續化到配置檔案。配置變更會觸發 `config.set` 生命週期事件。

## Logger 模組

模組化日誌系統，基於 Rich 輸出，支援子日誌器和模組層級控制。

### 基本用法

```python
sdk.logger.debug("偵錯資訊")
sdk.logger.info("執行資訊")
sdk.logger.warning("警告資訊")
sdk.logger.error("錯誤資訊")
sdk.logger.critical("致命錯誤")
```

### 子日誌器

```python
child_logger = sdk.logger.get_child("MyModule")
child_logger.info("子模組日誌")

child_logger.get_child("utils")  # 支援巢狀
```

### 日誌層級控制

```python
sdk.logger.set_level("DEBUG")                          # 全域層級
sdk.logger.set_module_level("MyModule", "DEBUG")       # 模組層級

# 支援的層級（由低到高）：
# TRACE, DEBUG, INFO, WARNING, ERROR, CRITICAL
# TRACE 為最低層級，輸出框架內部詳細偵錯資訊（事件分發、路由註冊等）
sdk.logger.set_level("TRACE")                          # 開啟全部日誌
```

### 日誌訂閱（推模式）

供 Dashboard 等模組即時接收結構化日誌，支援等級篩選和歷史補發。

> **顯式訂閱低層級日誌**：訂閱器的 `min_level` 可低於全域日誌層級。此時低層級日誌**僅推送到符合的訂閱器**，不會輸出到主控台，也不會寫入記憶體，從而避免污染主日誌串流。
>
> ```python
> # 全域為 INFO，仍可單獨訂閱 DEBUG 日誌
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
| `handler(id, *, min_level)(func)` | 裝飾器/直接呼叫兩用。`id` 為空時取函數名。`min_level` 可低於全域層級（低層級日誌僅推送訂閱器，不進主控台/記憶體）。註冊時自動補發歷史日誌 |
| `remove_handler(id)` | 移除訂閱器 |

### 輸出控制

```python
sdk.logger.set_output_file("app.log")
sdk.logger.save_logs("log.txt")
sdk.logger.get_logs("MyModule")
sdk.logger.set_memory_limit(1000)

## Adapter 模組

Adapter 管理器，管理多平台 Adapter 的註冊、啟動和關閉。

### API 概覽

| 方法 | 說明 |
|------|------|
| `get(platform)` | 取得 Adapter 執行個體 |
| `exists(platform)` | 檢查 Adapter 是否已註冊 |
| `enable(platform)` / `disable(platform)` | 啟用/停用 Adapter |
| `is_enabled(platform)` | 檢查是否已啟用 |
| `startup(platforms)` / `shutdown(platforms)` | 啟動/關閉 Adapter |
| `is_running(platform)` | 檢查 Adapter 是否正在執行 |
| `list_running()` | 列出所有正在執行的 Adapter |
| `platforms` | 取得所有平台名稱列表 |

### Adapter 事件

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

> 完整的 Adapter 管理 API 請參考 [Adapter 系統 API](adapter-system.md)。

## Module 模組

模組管理器，管理插件的註冊、載入和卸載。

### API 概覽

| 方法 | 說明 |
|------|------|
| `get(name)` | 取得模組實例或延遲載入代理（已註冊但未載入時返回代理） |
| `exists(name)` | 檢查是否已註冊 |
| `is_loaded(name)` | 檢查是否已載入 |
| `is_enabled(name)` | 檢查是否啟用 |
| `enable(name)` / `disable(name)` | 啟用/停用模組 |
| `load(name)` / `unload(name)` | 載入/卸載模組 |
| `list_registered()` | 列出已註冊模組 |
| `list_loaded()` | 列出已載入模組 |
| `get_info(name)` | 取得模組資訊 |
| `get_status_summary()` | 取得模組狀態摘要 |

### 屬性存取

```python
module = sdk.module.get("模組名稱")
module = sdk.module.模組名稱
module = sdk.模組名稱  # 等價捷徑方式

## Lifecycle 模組

事件驅動的生命週期管理器，提供事件提交和監聽功能。

### API 概覽

| 方法 | 說明 |
|------|------|
| `on(event, priority=0)` | 裝飾器註冊事件處理器，支援點號匹配和萬用字元 `*` |
| `register(event, handler, priority=0)` | 函式式註冊處理器 |
| `unregister(event, handler=None)` | 移除處理器 |
| `emit(event, data)` | 非同步觸發事件 |
| `emit_sync(event, data)` | 同步觸發事件 |
| `submit_event(event_type, msg, data, source)` | 提交標準格式事件（相容舊版） |
| `start_timer(id)` / `stop_timer(id)` | 效能計時器 |

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

HTTP/WebSocket 路由管理器，基於 FastAPI + Uvicorn，支援裝飾器路由、中介軟體、分組、限流、CORS。

> 完整的路由 API 文件（裝飾器路由、WebSocket、中介軟體、速率限制、CORS、安全標頭等）請參考 [路由管理器](../advanced/router.md)。

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
        await ws.send_text(f"回聲: {text}")

# 路由分組
group = sdk.router.group("MyModule", prefix="/v1")
@group.get("/users")
async def list_users(request: HttpRequest):
    return {"users": []}

## HTTP Client 模組

統一網路用戶端，聚合 HTTP 請求、WebSocket 連線、連線池管理、自動重試、請求統計和生命週期事件整合。

> 完整的網路用戶端文件（請求方法、回應物件、WebSocket 用戶端、異常體系等）請參考 [網路用戶端](../zh-TW/advanced/http-client.md)。

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

## SDK 偵錯

### dump_state()

匯出目前執行環境的框架快照，用於偵錯和診斷。

```python
import json
state = sdk.dump_state()
print(json.dumps(state, indent=2, ensure_ascii=False, default=str))
```

傳回結構包含以下子系統的狀態：

| 欄位 | 說明 |
|------|------|
| `sdk` | SDK 初始化狀態、Python 版本、執行平台、時間戳 |
| `adapters` | 已註冊/已啟動的適配器清單、各平台 Bot 上線狀態 |
| `modules` | 已註冊/已啟用/已停用/延遲載入的模組清單 |
| `events` | 各類事件處理器數量（message/notice/request/meta/commands） |
| `router` | 伺服器執行狀態、HTTP/WebSocket 路由數量 |

> 新增於 2.5.2

## 相關文件

- [事件系統 API](event-system.md) - Event 模組 API
- [適配器系統 API](adapter-system.md) - Adapter 管理 API
- [SQL 查詢建構器](../advanced/sql-builder.md) - SQL 串聯查詢完整文件
- [路由管理器](../advanced/router.md) - 路由管理器完整文件
- [網路用戶端](../advanced/http-client.md) - 網路用戶端完整文件
- [生命週期管理](../advanced/lifecycle.md) - 生命週期完整文件