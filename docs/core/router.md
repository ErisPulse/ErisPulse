# 路由管理器

ErisPulse 路由管理器提供统一的 HTTP 和 WebSocket 路由管理，支持多适配器路由注册和生命周期管理。它基于 FastAPI 构建，提供了完整的 Web 服务功能，使模块和适配器能够轻松暴露 HTTP API 和 WebSocket 服务。

## 概述

路由管理器是 ErisPulse 的核心组件之一，提供以下主要功能：

- **HTTP 路由管理**：支持多种 HTTP 方法的路由注册
- **WebSocket 支持**：完整的 WebSocket 连接管理和自定义认证
- **生命周期集成**：与 ErisPulse 生命周期系统深度集成
- **统一错误处理**：提供统一的错误处理和日志记录
- **SSL/TLS 支持**：支持 HTTPS 和 WSS 安全连接
- **路由查询**：提供路由列表和健康检查端点

## RouterManager 类

`RouterManager` 是路由管理系统的核心类，负责所有路由的注册和管理：

```python
from ErisPulse.Core import router

# 获取全局路由管理器实例
# router 是预创建的 RouterManager 实例
```

## 基本使用

### 启动路由服务器

```python
from ErisPulse.Core import router
import asyncio

async def start_server():
    # 使用默认配置启动 (0.0.0.0:8000)
    await router.start()
    
    # 或者使用自定义配置
    await router.start(
        host="0.0.0.0",
        port=8080,
        ssl_certfile="/path/to/cert.pem",
        ssl_keyfile="/path/to/key.pem"
    )

asyncio.run(start_server())
```

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

# 注册 POST 路由
async def data_handler(request: Request):
    data = await request.json()
    return {"received": data}

router.register_http_route(
    module_name="my_module",
    path="/data",
    handler=data_handler,
    methods=["POST"]
)
```

### 注册 WebSocket 路由

```python
from fastapi import WebSocket
from ErisPulse.Core import router

async def websocket_handler(websocket: WebSocket):
    await websocket.accept()
    
    try:
        while True:
            # 接收消息
            data = await websocket.receive_text()
            
            # 处理消息
            response = f"Echo: {data}"
            
            # 发送响应
            await websocket.send_text(response)
            
    except Exception as e:
        print(f"WebSocket 错误: {e}")

# 简单 WebSocket 注册
router.register_websocket(
    module_name="my_module",
    path="/ws",
    handler=websocket_handler
)

# 带认证的 WebSocket 注册
async def auth_handler(websocket: WebSocket) -> bool:
    # 自定义认证逻辑
    token = websocket.query_params.get("token")
    return token == "secret_token"

router.register_websocket(
    module_name="my_module",
    path="/secure_ws",
    handler=websocket_handler,
    auth_handler=auth_handler
)
```

### 取消注册路由

```python
# 取消 HTTP 路由
router.unregister_http_route("my_module", "/hello")

# 取消 WebSocket 路由
router.unregister_websocket("my_module", "/ws")
```

## 核心功能详解

### HTTP 路由

#### 路径处理

路由路径会自动添加模块名称作为前缀，避免冲突：

```python
# 注册路径 "/api" 到模块 "my_module"
# 实际访问路径为 "/my_module/api"
router.register_http_route("my_module", "/api", handler)
```

#### 多方法支持

可以为同一路径注册多种 HTTP 方法：

```python
async def handle_request(request):
    return {"method": request.method}

router.register_http_route(
    module_name="my_module",
    path="/multi",
    handler=handle_request,
    methods=["GET", "POST", "PUT", "DELETE"]
)
```

#### FastAPI 依赖注入

路由处理器可以使用 FastAPI 的依赖注入功能：

```python
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer

security = HTTPBearer()

async def protected_handler(
    request: Request,
    credentials=Depends(security)
):
    # 认证后的处理逻辑
    return {"message": "认证成功", "token": credentials.credentials}

router.register_http_route(
    module_name="my_module",
    path="/protected",
    handler=protected_handler,
    methods=["GET"]
)
```

### WebSocket 路由

#### 认证机制

WebSocket 支持自定义认证逻辑：

```python
async def custom_auth(websocket: WebSocket) -> bool:
    # 从查询参数获取认证信息
    token = websocket.query_params.get("token")
    
    # 从请求头获取认证信息
    auth_header = websocket.headers.get("authorization")
    
    # 自定义认证逻辑
    if token == "valid_token" or auth_header == "Bearer valid_token":
        return True
    
    return False

async def secure_websocket_handler(websocket: WebSocket):
    # 只有通过认证的连接才会到达这里
    await websocket.accept()
    await websocket.send_text("认证成功")

router.register_websocket(
    module_name="my_module",
    path="/secure_ws",
    handler=secure_websocket_handler,
    auth_handler=custom_auth
)
```

#### 连接管理

WebSocket 处理器可以管理连接状态和生命周期：

```python
from typing import Dict, Set
import json

# 全局连接管理
active_connections: Dict[str, Set[WebSocket]] = {}

async def chat_handler(websocket: WebSocket):
    await websocket.accept()
    
    # 获取房间 ID
    room_id = websocket.query_params.get("room", "default")
    
    # 添加到房间连接池
    if room_id not in active_connections:
        active_connections[room_id] = set()
    active_connections[room_id].add(websocket)
    
    try:
        while True:
            # 接收消息
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # 广播消息到房间内其他连接
            for connection in active_connections[room_id]:
                if connection != websocket:
                    await connection.send_text(json.dumps(message))
                    
    except Exception as e:
        print(f"WebSocket 错误: {e}")
    finally:
        # 连接断开时清理
        active_connections[room_id].discard(websocket)
        if not active_connections[room_id]:
            del active_connections[room_id]

router.register_websocket(
    module_name="chat",
    path="/room",
    handler=chat_handler
)
```

### 系统路由

路由管理器自动提供两个系统路由：

#### 健康检查

```python
GET /health
# 返回:
{
    "status": "ok",
    "service": "ErisPulse Router"
}
```

#### 路由列表

```python
GET /routes
# 返回:
{
    "http_routes": [
        {
            "path": "/my_module/api",
            "adapter": "my_module",
            "methods": ["GET", "POST"]
        }
    ],
    "websocket_routes": [
        {
            "path": "/my_module/ws",
            "adapter": "my_module",
            "requires_auth": false
        }
    ],
    "base_url": "http://127.0.0.1:8000"
}
```

## 配置选项

### 服务器配置

通过配置文件可以设置默认的服务器参数：

```toml
[ErisPulse.server]
host = "0.0.0.0"
port = 8000
ssl_certfile = "/path/to/cert.pem"
ssl_keyfile = "/path/to/key.pem"
```

### 日志配置

控制路由管理器的日志级别：

```toml
[ErisPulse.logger]
level = "INFO"
```

## 生命周期集成

路由管理器与 ErisPulse 生命周期系统深度集成：

```python
# 服务器启动时触发事件
await lifecycle.submit_event(
    "server.start",
    msg="路由服务器已启动",
    data={
        "base_url": "http://127.0.0.1:8000",
        "host": "0.0.0.0",
        "port": 8000,
    }
)

# 服务器停止时触发事件
await lifecycle.submit_event("server.stop", msg="服务器已停止")
```

可以监听这些事件来执行相关操作：

```python
from ErisPulse.Core import lifecycle

@lifecycle.on_event("server.start")
async def on_server_start(event):
    print(f"服务器已启动: {event['data']['base_url']}")
    # 执行启动后的初始化操作

@lifecycle.on_event("server.stop")
async def on_server_stop(event):
    print("服务器正在停止...")
    # 执行清理操作
```

## 适配器集成

适配器可以轻松集成路由功能：

```python
from ErisPulse.Core.Bases import BaseAdapter
from ErisPulse.Core import router
from fastapi import Request, WebSocket

class MyAdapter(BaseAdapter):
    async def on_load(self, event: dict) -> bool:
        # 注册 HTTP 路由
        await self.register_routes()
        return True
    
    async def register_routes(self):
        # HTTP API 路由
        async def api_handler(request: Request):
            data = await self.process_request(request)
            return data
        
        router.register_http_route(
            module_name=self.name,
            path="/api",
            handler=api_handler,
            methods=["POST"]
        )
        
        # WebSocket 路由
        async def ws_handler(websocket: WebSocket):
            await self.handle_websocket(websocket)
        
        router.register_websocket(
            module_name=self.name,
            path="/ws",
            handler=ws_handler,
            auth_handler=self.auth_check
        )
    
    async def auth_check(self, websocket: WebSocket) -> bool:
        # 适配器特定的认证逻辑
        return await self.verify_websocket_auth(websocket)
```

## 高级用例

### API 版本控制

```python
# v1 API
async def api_v1_handler(request: Request):
    return {"version": "v1", "data": "..."}

router.register_http_route(
    module_name="my_module",
    path="/v1/api",
    handler=api_v1_handler
)

# v2 API
async def api_v2_handler(request: Request):
    return {"version": "v2", "data": "..."}

router.register_http_route(
    module_name="my_module",
    path="/v2/api",
    handler=api_v2_handler
)
```

### 中间件集成

```python
from fastapi import FastAPI, Request
from ErisPulse.Core import router

# 获取 FastAPI 实例
app = router.get_app()

# 添加中间件
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

# 添加异常处理器
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"message": "内部服务器错误", "detail": str(exc)}
    )
```

### 动态路由

```python
from fastapi import Request

# 动态路由参数
async def user_handler(request: Request, user_id: str):
    return {"user_id": user_id}

router.register_http_route(
    module_name="my_module",
    path="/users/{user_id}",
    handler=user_handler,
    methods=["GET"]
)
```

## 最佳实践

### 1. 路由命名

- 使用清晰的路由路径
- 包含模块名称作为前缀
- 使用名词而不是动词

### 2. 错误处理

- 在路由处理器中实现适当的错误处理
- 使用 FastAPI 的异常处理器统一处理错误
- 记录详细的错误日志

### 3. 认证与授权

- 为敏感路由实现认证
- 使用一致的认证机制
- 考虑使用 FastAPI 的安全工具

### 4. WebSocket 连接管理

- 实现适当的连接清理
- 限制并发连接数
- 处理连接超时

## 故障排除

### 常见问题

1. **路由冲突**
   ```
   ValueError: 路径 /my_module/api 已注册
   ```
   解决方案：使用不同的路径或先取消注册现有路由

2. **WebSocket 认证失败**
   - 检查认证逻辑是否正确
   - 确认认证信息传递方式
   - 查看服务器日志

3. **SSL 证书问题**
   - 确认证书文件路径正确
   - 检查证书格式
   - 验证证书有效期

4. **端口占用**
   - 更改端口号
   - 检查其他服务占用情况
   - 确认防火墙设置

## 总结

ErisPulse 路由管理器提供了强大而灵活的 Web 服务功能，使模块和适配器能够轻松暴露 HTTP API 和 WebSocket 服务。通过 FastAPI 的强大功能、统一的错误处理、生命周期集成和认证支持，它为构建复杂的 Web 应用提供了坚实的基础。