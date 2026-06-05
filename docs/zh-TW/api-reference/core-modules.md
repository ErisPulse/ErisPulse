# 核心模組 API

本文檔詳細介紹了 ErisPulse 的核心模組 API。

## Storage 模組

### 基本操作

```python
from ErisPulse import sdk

# 設定值
sdk.storage.set("key", "value")

# 取得值
value = sdk.storage.get("key", default_value)

# 获取所有键
keys = sdk.storage.keys()

# 刪除值
sdk.storage.delete("key")
```

### 事務操作

```python
# 使用事务确保数据一致性
with sdk.storage.transaction():
    sdk.storage.set("key1", "value1")
    sdk.storage.set("key2", "value2")
    # 如果任何操作失敗，所有變更都會回滾
```

### 批次操作

```python
# 批量设置
sdk.storage.set_multi({
    "key1": "value1",
    "key2": "value2",
    "key3": "value3"
})

# 批量获取
values = sdk.storage.get_multi(["key1", "key2", "key3"])

# 批量刪除
sdk.storage.delete_multi(["key1", "key2", "key3"])
```

### SQL 鏈式查詢

Storage 模組提供鏈式呼叫風格的通用 SQL 查詢建構器，支援自訂表的 CRUD 操作。

> 詳見 [SQL 查詢建構器](../advanced/sql-builder.md) 获取完整文档。

```python
from ErisPulse import sdk

# 建立自訂表
sdk.storage.CreateTable("users", {
    "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
    "name": "TEXT NOT NULL",
    "age": "INTEGER DEFAULT 0"
})

# 插入資料
sdk.storage.Table("users").Insert({"name": "Alice", "age": 30}).Execute()

# 批量插入
sdk.storage.Table("users").InsertMulti([
    {"name": "Bob", "age": 25},
    {"name": "Charlie", "age": 35}
]).Execute()

# 查詢資料
rows = (sdk.storage.Table("users")
    .Select("name", "age")
    .Where("age > ?", 18)
    .OrderBy("name")
    .Limit(10)
    .Execute())

# 更新資料
sdk.storage.Table("users").Update({"age": 31}).Where("name = ?", "Alice").Execute()

# 刪除資料
sdk.storage.Table("users").Delete().Where("name = ?", "Bob").Execute()

# 計數
count = sdk.storage.Table("users").Where("age > ?", 18).Count()

# 存在性檢查
exists = sdk.storage.Table("users").Where("name = ?", "Alice").Exists()

# 取得單條記錄
row = sdk.storage.Table("users").Select("name", "age").Where("name = ?", "Alice").ExecuteOne()

# 修改表結構
sdk.storage.AlterTable("users").AddColumn("email", "TEXT").Execute()
sdk.storage.AlterTable("users").RenameTo("members").Execute()

# 檢查表是否存在
if sdk.storage.HasTable("users"):
    sdk.storage.DropTable("users")

# 事务中的鏈式操作
with sdk.storage.transaction():
    sdk.storage.Table("users").Insert({"name": "Dave", "age": 40}).Execute()
    sdk.storage.Table("users").Update({"age": 41}).Where("name = ?", "Dave").Execute()

# 複用查詢條件
base = sdk.storage.Table("users").Where("age > ?", 20)
rows = base.copy().Select("name").OrderBy("name").Limit(5).Execute()
count = base.copy().Count()
```

### 存儲後端抽象

`StorageManager` 繼承自 `BaseStorage` 抽象基類，支援未來拓展其他存儲介質（Redis、MySQL 等）。

```python
from ErisPulse.Core.Bases.storage import BaseStorage, BaseQueryBuilder

# BaseStorage 定義了統一介面：get/set/delete/Table/CreateTable/DropTable 等
# BaseQueryBuilder 定義了鏈式查詢介面：Select/Insert/Update/Delete/Where/OrderBy/Limit 等
```

## Config 模組

### 讀取配置

```python
from ErisPulse import sdk

# 获取配置
config = sdk.config.getConfig("MyModule", {})

# 获取巢狀配置
value = sdk.config.getConfig("MyModule.subkey.value", "default")
```

### 寫入配置

```python
# 設定配置
sdk.config.setConfig("MyModule", {"key": "value"})

# 設定巢狀配置
sdk.config.setConfig("MyModule.subkey.value", "new_value")
```

### 配置範例

```python
def _load_config(self):
    config = sdk.config.getConfig("MyModule")
    if not config:
        # 建立預設配置
        default_config = {
            "api_url": "https://api.example.com",
            "timeout": 30,
            "cache_ttl": 3600
        }
        sdk.config.setConfig("MyModule", default_config, immediate=True)  # 第三個參數為 True 時，立即儲存配置，是方便使用者可以直接修改設定檔的
        return default_config
    return config
```

## Logger 模組

### 基本日誌

```python
from ErisPulse import sdk

# 不同日誌層級
sdk.logger.debug("除錯資訊")
sdk.logger.info("執行資訊")
sdk.logger.warning("警告資訊")
sdk.logger.error("錯誤資訊")
sdk.logger.critical("致命錯誤")
```

### 子日誌記錄器

```python
# 获取子日誌記錄器
child_logger = sdk.logger.get_child("MyModule")
child_logger.info("子模組日誌")

# 子模組還可以有子模組的日誌，這樣可以更精確地控制日誌輸出
child_logger.get_child("utils")
```

### 日誌輸出

```python
# 設定輸出檔案
sdk.logger.set_output_file("app.log")

# 儲存日誌到檔案
sdk.logger.save_logs("log.txt")
```

## Adapter 模組

### 取得適配器

```python
from ErisPulse import sdk

# 获取适配器實例
adapter = sdk.adapter.get("platform_name")

# 透過屬性存取
adapter = sdk.adapter.platform_name
```

### 適配器事件

```python
# 監聽標準事件
@sdk.adapter.on("message")
async def handle_message(event):
    pass

# 監聽特定平台的事件
@sdk.adapter.on("message", platform="yunhu")
async def handle_yunhu_message(event):
    pass

# 監聽平台原生事件
@sdk.adapter.on("raw_event", raw=True, platform="yunhu")
async def handle_raw_event(data):
    pass
```

### 適配器管理

```python
# 获取所有平台
platforms = sdk.adapter.platforms

# 檢查適配器是否存在
exists = sdk.adapter.exists("platform_name")

# 啟用/停用適配器
sdk.adapter.enable("platform_name")
sdk.adapter.disable("platform_name")

# 啟動/關閉適配器
await sdk.adapter.startup(["platform1", "platform2"])
await sdk.adapter.shutdown(["platform1", "platform2"])

# 檢查適配器是否正在運行
is_running = sdk.adapter.is_running("platform_name")

# 列出所有正在運行的適配器
running = sdk.adapter.list_running()
```

## Module 模組

### 取得模組

```python
from ErisPulse import sdk

# 获取模組實例
module = sdk.module.get("ModuleName")

# 透過屬性存取
module = sdk.module.ModuleName
module = sdk.ModuleName
```

### 模組管理

```python
# 檢查模組是否存在
exists = sdk.module.exists("ModuleName")

# 檢查模組是否已載入
is_loaded = sdk.module.is_loaded("ModuleName")

# 檢查模組是否已啟用
is_enabled = sdk.module.is_enabled("ModuleName")

# 啟用/停用模組
sdk.module.enable("ModuleName")
sdk.module.disable("ModuleName")

# 載入模組
await sdk.module.load("ModuleName")

# 卸載模組
await sdk.module.unload("ModuleName")

# 列出已載入的模組
loaded = sdk.module.list_loaded()

# 列出已註冊的模組
registered = sdk.module.list_registered()

# 获取模組資訊
info = sdk.module.get_info("ModuleName")

# 获取模組狀態摘要
summary = sdk.module.get_status_summary()
# {"modules": {"ModuleName": {"status": "loaded", "enabled": True, "is_base_module": True}}}

# 檢查模組是否正在運行（等價於 is_loaded）
is_running = sdk.module.is_running("ModuleName")

# 列出所有正在運行的模組
running = sdk.module.list_running()
```

## Lifecycle 模組

### 事件提交

```python
from ErisPulse import sdk

# 提交自訂事件
await sdk.lifecycle.submit_event(
    "custom.event",
    data={"key": "value"},
    source="MyModule",
    msg="自訂事件描述"
)
```

### 事件監聽

```python
# 監聯特定事件
@sdk.lifecycle.on("module.init")
async def handle_module_init(event_data):
    print(f"模組初始化: {event_data}")

# 監聯父級事件
@sdk.lifecycle.on("module")
async def handle_any_module_event(event_data):
    print(f"模組事件: {event_data}")

# 監聯所有事件
@sdk.lifecycle.on("*")
async def handle_any_event(event_data):
    print(f"系統事件: {event_data}")
```

### 計時器

```python
# 開始計時
sdk.lifecycle.start_timer("my_operation")

# ... 執行操作 ...

# 获取持续时间
duration = sdk.lifecycle.get_duration("my_operation")

# 停止計時
total_time = sdk.lifecycle.stop_timer("my_operation")
```

## Router 模組

### 抽象類型

Router 支援兩種類型註解風格：

```python
# ErisPulse 抽象類型（推薦，可移植性強）
from ErisPulse.Core import HttpRequest, WebSocketConnection

@sdk.router.get("MyModule", "/api")
async def handler(request: HttpRequest):
    data = await request.json()
    return {"status": "ok"}

# FastAPI 原生類型（相容已有代碼）
from fastapi import Request, WebSocket

@sdk.router.get("MyModule", "/api2")
async def handler(request: Request):
    return {"status": "ok"}
```

> 路由系統根據參數註解自動注入對應類型的物件，詳見 [路由管理器](../advanced/router.md)。

### 裝飾器路由（推薦）

```python
from ErisPulse import sdk
from fastapi import Request

# HTTP 路由裝飾器
@sdk.router.http("MyModule", "/api", methods=["GET", "POST"])
async def api_handler(request: Request):
    return {"status": "ok"}

# 快捷方法裝飾器
@sdk.router.get("MyModule", "/info")
async def get_info(request: Request):
    return {"module": "MyModule"}

@sdk.router.post("MyModule", "/data")
async def post_data(request: Request):
    data = await request.json()
    return {"received": data}

@sdk.router.put("MyModule", "/data/{item_id}")
async def put_data(request: Request):
    return {"updated": True}

@sdk.router.delete("MyModule", "/data/{item_id}")
async def delete_data(request: Request):
    return {"deleted": True}

# WebSocket 裝飾器
from fastapi import WebSocket

@sdk.router.ws("MyModule", "/ws")
async def websocket_handler(websocket: WebSocket):
    while True:
        data = await websocket.receive_text()
        await websocket.send_text(f"Echo: {data}")

# 帶認證的 WebSocket 裝飾器
async def ws_auth(websocket: WebSocket) -> bool:
    token = websocket.query_params.get("token")
    return token == "secret"

@sdk.router.ws("MyModule", "/secure_ws", auth_handler=ws_auth)
async def secure_ws_handler(websocket: WebSocket):
    while True:
        data = await websocket.receive_text()
        await websocket.send_text(f"Echo: {data}")
```

### 傳統註冊方式

```python
from ErisPulse import sdk
from fastapi import Request

async def handler(request: Request):
    data = await request.json()
    return {"status": "ok", "data": data}

sdk.router.register_http_route(
    module_name="MyModule",
    path="/api",
    handler=handler,
    methods=["POST"],
    rate_limit="10/minute",
    summary="資料介面",
    tags=["API"],
)

sdk.router.unregister_http_route("MyModule", "/api")
```

### WebSocket 路由

```python
from ErisPulse import sdk
from fastapi import WebSocket

async def websocket_handler(websocket: WebSocket):
    while True:
        data = await websocket.receive_text()
        await websocket.send_text(f"Echo: {data}")

# 基本註冊（自動接受連線）
sdk.router.register_websocket(
    module_name="my_module",
    path="/ws",
    handler=websocket_handler,
)

# 帶認證的註冊（推薦：使用 auth_handler 控制連線）
async def auth_handler(websocket: WebSocket) -> bool:
    token = websocket.query_params.get("token")
    return token == "secret"

sdk.router.register_websocket(
    module_name="my_module",
    path="/secure_ws",
    handler=websocket_handler,
    auth_handler=auth_handler,
)

# 取消路由
sdk.router.unregister_websocket("MyModule", "/ws")
```

**參數說明：**

| 參數 | 說明 | 預設值 |
|------|------|--------|
| `module_name` | 模組名稱（必須） | - |
| `path` | WebSocket 路徑 | - |
| `handler` | 處理函數 | - |
| `auth_handler` | 認證函數，返回 `False` 會自動關閉連線 | `None` |
| `auto_accept` | 是否自動 `accept()` | `True` |

> **推薦**：使用 `auth_handler` 進行連線確認，而非關閉 `auto_accept`。僅在你需要完全控制連線流程時才設置 `auto_accept=False`。

### 路由分組

```python
# 建立路由組
group = sdk.router.group("MyModule", prefix="/v1")

# 在組內註冊路由
@group.get("/users")
async def list_users(request: Request):
    return {"users": []}

@group.post("/users")
async def create_user(request: Request):
    return {"created": True}

# 帶版本號的分組
v2 = sdk.router.group("MyModule", prefix="/v2", version="2")
```

### 路由中間件

```python
# 全局中間件（glob 匹配）
@sdk.router.middleware("/MyModule/*")
async def auth_middleware(request: Request, call_next):
    token = request.headers.get("Authorization")
    if not token:
        return {"error": "Unauthorized"}
    response = await call_next(request)
    return response

# 特定路徑中間件
@sdk.router.middleware("/MyModule/admin/*")
async def admin_middleware(request: Request, call_next):
    return await call_next(request)
```

### 速率限制

```python
# 對路由設置速率限制（滑動窗口）
@sdk.router.get("MyModule", "/limited", rate_limit="10/minute")
async def limited_endpoint(request: Request):
    return {"ok": True}

@sdk.router.post("MyModule", "/submit", rate_limit="5/minute")
async def submit_data(request: Request):
    return {"submitted": True}
```

### CORS 配置

```python
# 代碼方式
sdk.router.setup_cors(
    allow_origins=["https://example.com"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# 配置文件方式（config.toml）
# [router.cors]
# allow_origins = ["https://example.com"]
# allow_methods = ["GET", "POST"]
# allow_headers = ["*"]
```

### 安全頭

```python
# 自動添加安全響應頭
sdk.router.setup_security_headers()

# 配置文件方式（config.toml）
# [router.security]
# enabled = true
```

### 自動文檔

```python
# Router 預設啟用 OpenAPI 文檔
# 禁用文檔
sdk.router.disable_docs()

# 自定義文檔信息
sdk.router.set_docs_info(
    title="My API",
    description="API 文檔",
    version="1.0.0"
)
```

### 路由信息

```python
app = sdk.router.get_app()
```

## HTTP Client 模組

### 基本請求

```python
from ErisPulse.Core import client

# GET 請求
resp = await client.get("https://api.example.com/users")
data = await resp.json()

# POST 請求
resp = await client.post(
    "https://api.example.com/users",
    json={"name": "Alice", "age": 30},
)

# PUT / DELETE / PATCH
resp = await client.put("https://api.example.com/users/1", json={"name": "Bob"})
resp = await client.delete("https://api.example.com/users/1")
resp = await client.patch("https://api.example.com/users/1", json={"age": 31})

# 通用 request 方法
resp = await client.request("OPTIONS", "https://api.example.com/resource")
```

### 響應對象

```python
from ErisPulse.Core import client

resp = await client.get("https://api.example.com/users")

resp.status        # int - HTTP 狀態碼 (如 200, 404)
resp.reason        # str | None - 狀態描述 (如 "OK")
resp.headers       # 響應頭 (大小寫不敏感)
resp.content_type  # str | None - Content-Type
resp.url           # 最終 URL (可能因重定向變化)
resp.raw           # 底層原生響應對象 (當前為 aiohttp.ClientResponse)

# 讀取響應體
body = await resp.read()       # bytes
text = await resp.text()       # str
data = await resp.json()       # 解析 JSON
text = await resp.text("gbk")  # 指定編碼
```

### 請求參數

| 參數 | 類型 | 說明 |
|------|------|------|
| `url` | `str` | 請求 URL |
| `params` | `dict[str, str]` | 查詢參數 (可選) |
| `headers` | `dict[str, str]` | 額外請求頭 (可選) |
| `data` | `Any` | 請求體 (表單或原始數據) (可選) |
| `json` | `Any` | JSON 請求體 (可選) |
| `timeout` | `float` | 本次請求超時 (秒) (可選, 覆蓋默認值) |
| `max_retries` | `int` | 本次最大重試次數 (可選, 覆蓋默認值) |

### 自定義客戶端

```python
from ErisPulse.Core import HttpClient

# 創建自定義客戶端（非全局單例）
client = HttpClient(
    timeout=60,
    connect_timeout=5,
    max_retries=3,
    retry_delay=2,
    headers={"Authorization": "Bearer token"},
    user_agent="MyBot/1.0",
)

# 上下文管理器，自動關閉會話
async with HttpClient(timeout=30) as client:
    resp = await client.get("https://httpbin.org/get")
```

### 請求統計

```python
from ErisPulse.Core import client

# 查看統計
stats = client.stats
# {"total_requests": 42, "total_errors": 1, "total_bytes_sent": 0, "total_bytes_received": 0}

# 重置統計
client.reset_stats()
```

### 生命周期事件

```python
from ErisPulse.Core import lifecycle

@lifecycle.on("client.request")
async def on_request(event_data):
    print(f"{event_data['method']} {event_data['url']} -> {event_data['status']} ({event_data['elapsed']}s)")
```

## 相關文檔

- [事件系統 API](event-system.md) - Event 模組 API
- [適配器系統 API](adapter-system.md) - Adapter 管理 API
- [HTTP 客戶端](../advanced/http-client.md) - HTTP 客戶端完整文檔
- [路由管理器](../advanced/router.md) - 路由管理器完整文檔