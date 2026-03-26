# 路由管理器

ErisPulse 路由管理器提供統一的 HTTP 和 WebSocket 路由管理，支援多適配器路由註冊和生命週期管理。它基於 FastAPI 構建，提供了完整的 Web 服務功能。

## 概述

路由管理器的主要功能：

- **HTTP 路由管理**：支援多種 HTTP 方法的路由註冊
- **WebSocket 支援**：完整的 WebSocket 連線管理和自訂認證
- **生命週期整合**：與 ErisPulse 生命週期系統深度整合
- **統一錯誤處理**：提供統一的錯誤處理和日誌記錄
- **SSL/TLS 支援**：支援 HTTPS 和 WSS 安全連線

## 基本使用

### 註冊 HTTP 路由

```python
from fastapi import Request
from ErisPulse.Core import router

async def hello_handler(request: Request):
    return {"message": "Hello World"}

# 註冊 GET 路由
router.register_http_route(
    module_name="my_module",
    path="/hello",
    handler=hello_handler,
    methods=["GET"]
)
```

### 註冊 WebSocket 路由

```python
from fastapi import WebSocket

# 預設自動接受連線
async def websocket_handler(websocket: WebSocket):
    # 預設情況下無需手動 accept，內部已自動呼叫
    while True:
        data = await websocket.receive_text()
        await websocket.send_text(f"Echo: {data}")

router.register_websocket(
    module_name="my_module",
    path="/ws",
    handler=websocket_handler,
    auto_accept=True  # 預設為 True，可省略
)

# 手動控制連線
async def manual_websocket_handler(websocket: WebSocket):
    # 根據 condition 決定是否接受連線
    if some_condition:
        await websocket.accept()
        # 處理連線...
    else:
        await websocket.close(code=1008, reason="Not allowed")

router.register_websocket(
    module_name="my_module",
    path="/secure_ws",
    handler=manual_websocket_handler,
    auto_accept=False  # 手動控制連線
)
```

**參數說明：**

- `module_name`: 模組名稱
- `path`: WebSocket 路徑
- `handler`: 處理函式
- `auth_handler`: 可選的認證函式
- `auto_accept`: 是否自動接受連線（預設 `True`）
  - `True`: 框架自動呼叫 `websocket.accept()`，handler 無需手動呼叫
  - `False`: handler 必須自行呼叫 `websocket.accept()` 或 `websocket.close()`

### 註銷路由

```python
router.unregister_http_route(
    module_name="my_module",
    path="/hello"
)

router.unregister_websocket(
    module_name="my_module",
    path="/ws"
)
```

## 路徑處理

路由路徑會自動添加模組名稱作為前綴，避免衝突：

```python
# 註冊路徑 "/api" 到模組 "my_module"
# 實際存取路徑為 "/my_module/api"
router.register_http_route("my_module", "/api", handler)
```

## 認證機制

WebSocket 支援自訂認證邏輯：

```python
async def auth_handler(websocket: WebSocket) -> bool:
    token = websocket.query_params.get("token")
    if token == "<PASSWORD>":
        return True
    return False

router.register_websocket(
    module_name="my_module",
    path="/secure_ws",
    handler=websocket_handler,
    auth_handler=auth_handler
)
```

## 系統路由

路由管理器自動提供兩個系統路由：

### 健康檢查

```python
GET /health
# 回傳:
{"status": "ok", "service": "ErisPulse Router"}
```

### 路由列表

```python
GET /routes
# 回傳所有已註冊的路由資訊
```

## 生命週期整合

```python
from ErisPulse.Core import lifecycle

@lifecycle.on("server.start")
async def on_server_start(event):
    print(f"伺服器已啟動: {event['data']['base_url']}")

@lifecycle.on("server.stop")
async def on_server_stop(event):
    print("伺服器正在停止...")
```

## 最佳實務

1. **路由命名規範**：使用清晰、描述性的路徑名稱
2. **安全性考量**：為敏感操作實作認證機制
3. **錯誤處理**：實作適當的錯誤處理和回應格式
4. **連線管理**：實作適當的連線清理

## 相關文件

- [模組開發指南](../developer-guide/modules/getting-started.md) - 了解模組路由註冊
- [最佳實務](../developer-guide/modules/best-practices.md) - 路由使用建議