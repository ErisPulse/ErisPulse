# 路由管理器

ErisPulse 路由管理器提供统一的 HTTP 和 WebSocket 路由管理，支持多适配器路由注册和生命周期管理。底层通过抽象层封装（当前为 FastAPI + Uvicorn）

## 概述

路由管理器的主要功能：

- **装饰器路由**：支持 `@http` / `@get` / `@post` / `@put` / `@delete` / `@ws` 装饰器快捷注册
- **自动注入**：路由处理器无需导入 FastAPI 类型，框架自动注入抽象对象
- **路由分组**：支持带前缀和版本号的 `RouteGroup`
- **路由中间件**：支持 glob 模式匹配的请求拦截
- **速率限制**：内置滑动窗口限流
- **CORS 支持**：一键开启跨域资源共享
- **安全头**：自动添加安全响应头
- **自动文档**：基于 OpenAPI 的交互式文档
- **WebSocket 支持**：完整的 WebSocket 连接管理、自定义认证和生命周期钩子
- **生命周期集成**：与 ErisPulse 生命周期系统深度集成
- **SSL/TLS 支持**：支持 HTTPS 和 WSS 安全连接

## 抽象类型

ErisPulse 提供了服务端抽象类型，使模块无需直接依赖 FastAPI：

| 抽象类型 | FastAPI 对应 | 说明 |
|---------|-------------|------|
| `HttpRequest` | `fastapi.Request` | HTTP 请求封装，接口完全兼容 |
| `WebSocketConnection` | `fastapi.WebSocket` | WebSocket 连接封装，额外提供生命周期钩子 |
| `WebSocketDisconnect` | `fastapi.WebSocketDisconnect` | WebSocket 断开异常 |

> 通过 `.raw` 属性可访问底层 FastAPI 原生对象。直接使用 FastAPI 类型的代码也完全兼容。

## 装饰器路由（推荐）

### HTTP 装饰器

```python
from ErisPulse.Core import router
@router.get("my_module", "/info")
async def get_info(request):
    return {"method": request.method, "path": str(request.url)}

# 也可显式标注抽象类型
from ErisPulse.Core import HttpRequest

@router.post("my_module", "/data")
async def post_data(request: HttpRequest):
    data = await request.json()
    return {"received": data}

# 继续使用 FastAPI 类型也完全兼容
from fastapi import Request

@router.put("my_module", "/data/{item_id}")
async def update_data(request: Request):
    return {"updated": True}

@router.delete("my_module", "/data/{item_id}")
async def delete_data(request: Request):
    return {"deleted": True}
```

> **自动注入规则**：当处理器第一个参数名为 `request` 或 `req` 且无 FastAPI 类型注解时，框架自动注入 `HttpRequest`。无参数或非请求参数名的处理器不受影响。

### WebSocket 装饰器

```python
from ErisPulse.Core import WebSocketConnection, WebSocketDisconnect

# 基本 WebSocket
@router.ws("my_module", "/ws")
async def websocket_handler(ws):
    async for msg in ws.iter_text():
        await ws.send_text(f"Echo: {msg}")

# 带生命周期钩子的 WebSocket
@router.ws("my_module", "/ws/chat")
async def chat(ws: WebSocketConnection):
    @ws.on_disconnect
    async def on_disconnect(ws, reason="unknown"):
        print(f"用户断开: {reason}")

    @ws.on_error
    async def on_error(ws, error=""):
        print(f"连接错误: {error}")

    async for msg in ws.iter_text():
        await ws.send_text(f"Echo: {msg}")

# 带认证的 WebSocket
async def ws_auth(ws: WebSocketConnection) -> bool:
    token = ws.query_params.get("token")
    return token == "secret"

@router.ws("my_module", "/secure_ws", auth_handler=ws_auth)
async def secure_ws_handler(ws):
    while True:
        data = await ws.receive_text()
        await ws.send_text(f"Echo: {data}")
```

> **注意**：WebSocket 处理器和认证处理器也支持自动注入。如果参数注解为 `fastapi.WebSocket`，则传入原生对象；否则传入 `WebSocketConnection`。

## 传统注册方式

```python
async def hello_handler(request):
    return {"message": "Hello World"}

# 基本注册
router.register_http_route(
    module_name="my_module",
    path="/hello",
    handler=hello_handler,
    methods=["GET"],
)

# 带限流和文档信息
router.register_http_route(
    module_name="my_module",
    path="/api/data",
    handler=data_handler,
    methods=["POST"],
    rate_limit="10/minute",
    summary="数据接口",
    tags=["API"],
)
```

### WebSocket 注册

```python
from ErisPulse.Core import WebSocketConnection

async def websocket_handler(ws: WebSocketConnection):
    async for msg in ws.iter_text():
        await ws.send_text(f"Echo: {msg}")

# 基本注册
router.register_websocket(
    module_name="my_module",
    path="/ws",
    handler=websocket_handler,
)

# 带认证的注册（推荐）
async def auth_handler(ws: WebSocketConnection) -> bool:
    token = ws.query_params.get("token")
    return token == "secret"

router.register_websocket(
    module_name="my_module",
    path="/secure_ws",
    handler=websocket_handler,
    auth_handler=auth_handler,
)
```

**参数说明：**

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `module_name` | 模块名称（必须） | - |
| `path` | WebSocket 路径 | - |
| `handler` | 处理函数 | - |
| `auth_handler` | 认证函数，返回 `False` 会自动关闭连接 | `None` |
| `auto_accept` | 是否自动 `accept()` | `True` |

> **推荐**：使用 `auth_handler` 进行连接确认，而非关闭 `auto_accept`。仅在你需要完全控制连接流程时才设置 `auto_accept=False`。

## WebSocket 生命周期钩子

`WebSocketConnection` 提供了断开连接和错误的回调注册，无需手动 try/catch：

```python
from ErisPulse.Core import WebSocketConnection

@router.ws("my_module", "/ws")
async def my_ws(ws: WebSocketConnection):
    # 装饰器方式注册
    @ws.on_disconnect
    async def on_close(ws, reason="unknown"):
        print(f"断开原因: {reason}")

    # 也可直接调用
    async def on_err(ws, error=""):
        print(f"错误: {error}")
    ws.on_error(on_err)

    # 正常业务逻辑
    async for msg in ws.iter_text():
        await ws.send_text(f"Echo: {msg}")
```

## 路由分组

```python
# 创建带前缀的路由组
group = router.group("my_module", prefix="/v1")

@group.get("/users")
async def list_users(request):
    return {"users": []}

@group.post("/users")
async def create_user(request):
    return {"created": True}

# 实际路径: /my_module/v1/users
```

## 路由中间件

中间件支持 glob 模式匹配路径：

```python
@router.middleware("/my_module/*")
async def auth_middleware(request, call_next):
    token = request.headers.get("Authorization")
    if not token:
        return {"error": "Unauthorized"}
    return await call_next(request)

@router.middleware("/my_module/admin/*")
async def admin_middleware(request, call_next):
    return await call_next(request)
```

## 速率限制

使用滑动窗口算法对路由进行限流：

```python
@router.get("my_module", "/limited", rate_limit="10/minute")
async def limited_endpoint(request):
    return {"ok": True}

@router.post("my_module", "/submit", rate_limit="5/minute")
async def submit_data(request):
    return {"submitted": True}
```

速率限制格式：`{次数}/{时间窗口}`，如 `10/minute`、`100/hour`。

## CORS 配置

```python
router.setup_cors(
    allow_origins=["https://example.com"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```

也可通过 `config.toml` 配置：

```toml
[router.cors]
allow_origins = ["https://example.com"]
allow_methods = ["GET", "POST"]
allow_headers = ["*"]
```

## 安全头

```python
router.setup_security_headers()
```

自动添加 `X-Content-Type-Options`、`X-Frame-Options`、`X-XSS-Protection` 等安全头。

也可通过 `config.toml` 配置：

```toml
[router.security]
enabled = true
```

## 自动文档

Router 默认启用 OpenAPI 交互式文档：

```python
# 禁用文档
router.disable_docs()

# 自定义文档信息
router.set_docs_info(
    title="My API",
    description="API 文档",
    version="1.0.0"
)
```

## 路径处理

路由路径会自动添加模块名称作为前缀，避免冲突：

```python
# 注册路径 "/api" 到模块 "my_module"
# 实际访问路径为 "/my_module/api"
router.register_http_route("my_module", "/api", handler)
```

## 认证机制

推荐使用 `auth_handler` 控制连接访问：

```python
from ErisPulse.Core import WebSocketConnection

async def auth_handler(ws: WebSocketConnection) -> bool:
    token = ws.query_params.get("token")
    return token == "secret"

# 装饰器方式
@router.ws("my_module", "/secure_ws", auth_handler=auth_handler)
async def secure_handler(ws):
    while True:
        data = await ws.receive_text()
        await ws.send_text(f"Echo: {data}")

# 传统注册方式
router.register_websocket(
    module_name="my_module",
    path="/secure_ws",
    handler=websocket_handler,
    auth_handler=auth_handler,
)
```

`auth_handler` 在连接建立后执行，返回 `False` 会自动关闭连接（状态码 1008）。

> 仅在你需要完全控制连接流程（如自定义握手协议）时才设置 `auto_accept=False`。

## 系统路由

路由管理器自动提供两个系统路由：

### 健康检查

```python
GET /health
# 返回:
{"status": "ok", "service": "ErisPulse Router"}
```

### 路由列表

```python
GET /routes
# 返回所有已注册的路由信息
```

## 生命周期集成

```python
from ErisPulse.Core import lifecycle

@lifecycle.on("server.start")
async def on_server_start(event):
    print(f"服务器已启动: {event['data']['base_url']}")

@lifecycle.on("server.stop")
async def on_server_stop(event):
    print("服务器正在停止...")
```

## 最佳实践

1. **优先使用抽象类型**：使用 `HttpRequest` / `WebSocketConnection` 替代 `fastapi.Request` / `fastapi.WebSocket`，避免硬依赖
2. **利用自动注入**：处理器第一个参数命名为 `request` 或 `req`，无需任何类型注解即可获得 `HttpRequest`
3. **显式传入 module_name**：装饰器第一个参数必须为模块名，不可省略
4. **使用路由分组**：对同一模块的多个路由使用 `group()` 组织
5. **安全性考虑**：为敏感操作实现认证机制和安全头
6. **合理限流**：对高频接口设置速率限制
7. **使用生命周期钩子**：通过 `@ws.on_disconnect` / `@ws.on_error` 处理 WebSocket 异常，避免手动 try/catch

## 相关文档

- [HTTP 客户端](http-client.md) - 使用内置 HTTP 客户端发送请求
- [模块开发指南](../developer-guide/modules/getting-started.md) - 了解模块路由注册
- [最佳实践](../developer-guide/modules/best-practices.md) - 路由使用建议
