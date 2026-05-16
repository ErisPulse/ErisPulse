# 路由管理器

ErisPulse 路由管理器提供統一的 HTTP 和 WebSocket 路由管理，支援多適配器路由註冊和生命週期管理。它基於 FastAPI 構建，提供了完整的 Web 服務功能。

## 概述

路由管理器的主要功能：

- **裝飾器路由**：支援 `@http` / `@get` / `@post` / `@put` / `@delete` / `@ws` 裝飾器快捷註冊
- **路由分組**：支援帶前綴和版本號的 `RouteGroup`
- **路由中間件**：支援 glob 模式匹配的請求攔截
- **速率限制**：內建滑動窗口限流
- **CORS 支援**：一鍵開啟跨域資源共享
- **安全頭**：自動添加安全回應頭
- **自動文件**：基於 OpenAPI 的互動式文件
- **WebSocket 支援**：完整的 WebSocket 連線管理和自訂認證
- **生命週期整合**：與 ErisPulse 生命週期系統深度整合
- **SSL/TLS 支援**：支援 HTTPS 和 WSS 安全連線

## 裝飾器路由（推薦）

### HTTP 裝飾器

```python
from ErisPulse.Core import router
from fastapi import Request

# 通用 HTTP 路由
@router.http("my_module", "/api", methods=["GET", "POST"])
async def api_handler(request: Request):
    return {"message": "Hello"}

# 快捷方法
@router.get("my_module", "/info")
async def get_info(request: Request):
    return {"info": "data"}

@router.post("my_module", "/data")
async def post_data(request: Request):
    data = await request.json()
    return {"received": data}

@router.put("my_module", "/data/{item_id}")
async def update_data(request: Request):
    return {"updated": True}

@router.delete("my_module", "/data/{item_id}")
async def delete_data(request: Request):
    return {"deleted": True}
```

> **注意**：`module_name` 必須作為第一個參數顯式傳入，路由路徑會自動添加模組名前綴。

### WebSocket 裝飾器

```python
from fastapi import WebSocket

# 基本 WebSocket
@router.ws("my_module", "/ws")
async def websocket_handler(websocket: WebSocket):
    while True:
        data = await websocket.receive_text()
        await websocket.send_text(f"Echo: {data}")

# 帶認證的 WebSocket（推薦：使用 auth_handler 控制連接）
async def ws_auth(websocket: WebSocket) -> bool:
    token = websocket.query_params.get("token")
    return token == "secret"

@router.ws("my_module", "/secure_ws", auth_handler=ws_auth)
async def secure_ws_handler(websocket: WebSocket):
    while True:
        data = await websocket.receive_text()
        await websocket.send_text(f"Echo: {data}")
```

## 傳統註冊方式

```python
from fastapi import Request

async def hello_handler(request: Request):
    return {"message": "Hello World"}

# 基本註冊
router.register_http_route(
    module_name="my_module",
    path="/hello",
    handler=hello_handler,
    methods=["GET"],
)

# 帶限流和文件資訊
router.register_http_route(
    module_name="my_module",
    path="/api/data",
    handler=data_handler,
    methods=["POST"],
    rate_limit="10/minute",
    summary="數據介面",
    tags=["API"],
)
```

### WebSocket 註冊

```python
from fastapi import WebSocket

async def websocket_handler(websocket: WebSocket):
    while True:
        data = await websocket.receive_text()
        await websocket.send_text(f"Echo: {data}")

# 基本註冊
router.register_websocket(
    module_name="my_module",
    path="/ws",
    handler=websocket_handler,
)

# 帶認證的註冊（推薦）
async def auth_handler(websocket: WebSocket) -> bool:
    token = websocket.query_params.get("token")
    return token == "secret"

router.register_websocket(
    module_name="my_module",
    path="/secure_ws",
    handler=websocket_handler,
    auth_handler=auth_handler,
)
```

**參數說明：**

| 參數 | 說明 | 預設值 |
|------|------|--------|
| `module_name` | 模組名稱（必須） | - |
| `path` | WebSocket 路徑 | - |
| `handler` | 處理函式 | - |
| `auth_handler` | 認證函式，返回 `False` 會自動關閉連接 | `None` |
| `auto_accept` | 是否自動 `accept()` | `True` |

> **推薦**：使用 `auth_handler` 進行連接確認，而非關閉 `auto_accept`。僅在你需要完全控制連接流程時才設置 `auto_accept=False`。

## 路由分組

```python
# 創建帶前綴的路由組
group = router.group("my_module", prefix="/v1")

@group.get("/users")
async def list_users(request: Request):
    return {"users": []}

@group.post("/users")
async def create_user(request: Request):
    return {"created": True}

# 實際路徑: /my_module/v1/users
```

## 路由中間件

中間件支援 glob 模式匹配路徑：

```python
@router.middleware("/my_module/*")
async def auth_middleware(request: Request, call_next):
    token = request.headers.get("Authorization")
    if not token:
        return {"error": "Unauthorized"}
    return await call_next(request)

@router.middleware("/my_module/admin/*")
async def admin_middleware(request: Request, call_next):
    return await call_next(request)
```

## 速率限制

使用滑動窗口演算法對路由進行限流：

```python
@router.get("my_module", "/limited", rate_limit="10/minute")
async def limited_endpoint(request: Request):
    return {"ok": True}

@router.post("my_module", "/submit", rate_limit="5/minute")
async def submit_data(request: Request):
    return {"submitted": True}
```

速率限制格式：`{次數}/{時間視窗}`，如 `10/minute`、`100/hour`。

## CORS 配置

```python
router.setup_cors(
    allow_origins=["https://example.com"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```

也可通過 `config.toml` 配置：

```toml
[router.cors]
allow_origins = ["https://example.com"]
allow_methods = ["GET", "POST"]
allow_headers = ["*"]
```

## 安全頭

```python
router.setup_security_headers()
```

自動添加 `X-Content-Type-Options`、`X-Frame-Options`、`X-XSS-Protection` 等安全頭。

也可通過 `config.toml` 配置：

```toml
[router.security]
enabled = true
```

## 自動文件

Router 預設啟用 OpenAPI 互動式文件：

```python
# 禁用文件
router.disable_docs()

# 自定義文件資訊
router.set_docs_info(
    title="My API",
    description="API 文件",
    version="1.0.0"
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

推薦使用 `auth_handler` 控制連接訪問：

```python
async def auth_handler(websocket: WebSocket) -> bool:
    token = websocket.query_params.get("token")
    return token == "secret"

# 裝飾器方式
@router.ws("my_module", "/secure_ws", auth_handler=auth_handler)
async def secure_handler(websocket: WebSocket):
    while True:
        data = await websocket.receive_text()
        await websocket.send_text(f"Echo: {data}")

# 傳統註冊方式
router.register_websocket(
    module_name="my_module",
    path="/secure_ws",
    handler=websocket_handler,
    auth_handler=auth_handler,
)
```

`auth_handler` 在連接建立後執行，返回 `False` 會自動關閉連接（狀態碼 1008）。

> 僅在你需要完全控制連接流程（如自訂握手協定）時才設置 `auto_accept=False`。

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

## 最佳實踐

1. **優先使用裝飾器**：`@router.get()` 等裝飾器比 `register_http_route()` 更簡潔
2. **顯式傳入 module_name**：裝飾器第一個參數必須為模組名，不可省略
3. **使用路由分組**：對同一模組的多個路由使用 `create_group()` 組織
4. **安全性考量**：為敏感操作實作認證機制和安全頭
5. **合理限流**：對高頻介面設置速率限制
6. **錯誤處理**：實作適當的錯誤處理和回應格式

## 相關文件

- [模組開發指南](../developer-guide/modules/getting-started.md) - 了解模組路由註冊
- [最佳實踐](../developer-guide/modules/best-practices.md) - 路由使用建議