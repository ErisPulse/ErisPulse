# 路由管理器

ErisPulse 路由管理器提供统一的 HTTP 和 WebSocket 路由管理，支持多适配器路由注册和生命周期管理。它基于 FastAPI 构建，提供了完整的 Web 服务功能。

## 概述

路由管理器的主要功能：

- **HTTP 路由管理**：支持多种 HTTP 方法的路由注册
- **WebSocket 支持**：完整的 WebSocket 连接管理和自定义认证
- **生命周期集成**：与 ErisPulse 生命周期系统深度集成
- **统一错误处理**：提供统一的错误处理和日志记录
- **SSL/TLS 支持**：支持 HTTPS 和 WSS 安全连接

## 基本使用

### 注册 HTTP 路由

```python
from fastapi import Request
from ErisPulse.Core import router

async def hello_handler(request: Request):
    return {"message": "Hello World"}

# 注册 GET 路由
router.register_http_route(
    module_name="my_module",
    path="/hello",
    handler=hello_handler,
    methods=["GET"]
)
```

### 注册 WebSocket 路由

```python
from fastapi import WebSocket

# 默认自动接受连接
async def websocket_handler(websocket: WebSocket):
    # 默认情况下无需手动 accept，内部已自动调用
    while True:
        data = await websocket.receive_text()
        await websocket.send_text(f"Echo: {data}")

router.register_websocket(
    module_name="my_module",
    path="/ws",
    handler=websocket_handler,
    auto_accept=True  # 默认为 True，可省略
)

# 手动控制连接
async def manual_websocket_handler(websocket: WebSocket):
    # 根据 condition 决定是否接受连接
    if some_condition:
        await websocket.accept()
        # 处理连接...
    else:
        await websocket.close(code=1008, reason="Not allowed")

router.register_websocket(
    module_name="my_module",
    path="/secure_ws",
    handler=manual_websocket_handler,
    auto_accept=False  # 手动控制连接
)
```

**参数说明：**

- `module_name`: 模块名称
- `path`: WebSocket 路径
- `handler`: 处理函数
- `auth_handler`: 可选的认证函数
- `auto_accept`: 是否自动接受连接（默认 `True`）
  - `True`: 框架自动调用 `websocket.accept()`，handler 无需手动调用
  - `False`: handler 必须自行调用 `websocket.accept()` 或 `websocket.close()`

### 注销路由

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

## 路径处理

路由路径会自动添加模块名称作为前缀，避免冲突：

```python
# 注册路径 "/api" 到模块 "my_module"
# 实际访问路径为 "/my_module/api"
router.register_http_route("my_module", "/api", handler)
```

## 认证机制

WebSocket 支持自定义认证逻辑：

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

1. **路由命名规范**：使用清晰、描述性的路径名
2. **安全性考虑**：为敏感操作实现认证机制
3. **错误处理**：实现适当的错误处理和响应格式
4. **连接管理**：实现适当的连接清理

## 相关文档

- [模块开发指南](../developer-guide/modules/getting-started.md) - 了解模块路由注册
- [最佳实践](../developer-guide/modules/best-practices.md) - 路由使用建议