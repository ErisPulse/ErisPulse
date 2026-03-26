# 核心模組 API

本文件詳細介紹了 ErisPulse 的核心模組 API。

## Storage 模組

### 基本操作

```python
from ErisPulse import sdk

# 設定值
sdk.storage.set("key", "value")

# 取得值
value = sdk.storage.get("key", default_value)

# 刪除值
sdk.storage.delete("key")

# 檢查鍵是否存在
exists = sdk.storage.exists("key")
```

### 事務操作

```python
# 使用事務確保資料一致性
with sdk.storage.transaction():
    sdk.storage.set("key1", "value1")
    sdk.storage.set("key2", "value2")
    # 如果任何操作失敗，所有變更都會回滾
```

### 批次操作

```python
# 批次設定
sdk.storage.set_multi({
    "key1": "value1",
    "key2": "value2",
    "key3": "value3"
})

# 批次取得
values = sdk.storage.get_multi(["key1", "key2", "key3"])

# 批次刪除
sdk.storage.delete_multi(["key1", "key2", "key3"])
```

## Config 模組

### 讀取配置

```python
from ErisPulse import sdk

# 取得配置
config = sdk.config.getConfig("MyModule", {})

# 取得巢狀配置
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
# 取得子日誌記錄器
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

# 取得適配器實例
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
# 取得所有平台
platforms = sdk.adapter.platforms

# 檢查適配器是否存在
exists = sdk.adapter.exists("platform_name")

# 啟用/停用適配器
sdk.adapter.enable("platform_name")
sdk.adapter.disable("platform_name")

# 啟動/關閉適配器
await sdk.adapter.startup(["platform1", "platform2"])
await sdk.adapter.shutdown()
```

## Module 模組

### 取得模組

```python
from ErisPulse import sdk

# 取得模組實例
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

# 檢查模組是否啟用
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
# 監聽特定事件
@sdk.lifecycle.on("module.init")
async def handle_module_init(event_data):
    print(f"模組初始化: {event_data}")

# 監聽父級事件
@sdk.lifecycle.on("module")
async def handle_any_module_event(event_data):
    print(f"模組事件: {event_data}")

# 監聽所有事件
@sdk.lifecycle.on("*")
async def handle_any_event(event_data):
    print(f"系統事件: {event_data}")
```

### 計時器

```python
# 開始計時
sdk.lifecycle.start_timer("my_operation")

# ... 執行操作 ...

# 取得持續時間
duration = sdk.lifecycle.get_duration("my_operation")

# 停止計時
total_time = sdk.lifecycle.stop_timer("my_operation")
```

## Router 模組

### HTTP 路由

```python
from ErisPulse import sdk
from fastapi import Request

# 註冊 HTTP 路由
async def handler(request: Request):
    data = await request.json()
    return {"status": "ok", "data": data}

sdk.router.register_http_route(
    module_name="MyModule",
    path="/api",
    handler=handler,
    methods=["POST"]
)

# 取消路由
sdk.router.unregister_http_route("MyModule", "/api")
```

### WebSocket 路由

```python
from ErisPulse import sdk
from fastapi import WebSocket

# 註冊 WebSocket 路由（預設自動接受連線）
async def websocket_handler(websocket: WebSocket):
    # 預設情況下無需手動 accept，內部已自動呼叫
    while True:
        data = await websocket.receive_text()
        await websocket.send_text(f"Echo: {data}")

sdk.router.register_websocket(
    module_name="my_module",
    path="/ws",
    handler=websocket_handler,
    auto_accept=True  # 預設為 True，可省略
)

# 註冊 WebSocket 路由（手動控制連線）
async def manual_websocket_handler(websocket: WebSocket):
    # 根據 condition 決定是否接受連線
    if some_condition:
        await websocket.accept()
        # 處理連線...
    else:
        await websocket.close(code=1008, reason="Not allowed")

async def auth_handler(websocket: WebSocket) -> bool:
    token = websocket.query_params.get("token")
    if token == "<PASSWORD>":
        return True
    return False

sdk.router.register_websocket(
    module_name="my_module",
    path="/secure_ws",
    handler=manual_websocket_handler,
    auth_handler=auth_handler,