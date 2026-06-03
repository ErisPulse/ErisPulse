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