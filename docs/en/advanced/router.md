# Router Manager

The ErisPulse Router Manager provides unified HTTP and WebSocket route management, supporting multi-adapter route registration and lifecycle management. It is built on FastAPI + Uvicorn and provides complete web service capabilities.

## Overview

Key features of the Router Manager:

- **Decorator Routes**: Supports `@http` / `@get` / `@post` / `@put` / `@delete` / `@ws` decorators for quick registration
- **Route Grouping**: Supports `RouteGroup` with prefixes and version numbers
- **Route Middleware**: Supports request interception with glob pattern matching
- **Rate Limiting**: Built-in sliding window rate limiting
- **CORS Support**: One-click enable Cross-Origin Resource Sharing
- **Security Headers**: Automatically adds security response headers
- **Auto Documentation**: Interactive documentation based on OpenAPI
- **WebSocket Support**: Complete WebSocket connection management and custom authentication
- **Lifecycle Integration**: Deeply integrated with the ErisPulse lifecycle system
- **SSL/TLS Support**: Supports HTTPS and WSS secure connections

## Decorator Routes (Recommended)

### HTTP Decorators

```python
from ErisPulse.Core import router
from fastapi import Request

# General HTTP routes
@router.http("my_module", "/api", methods=["GET", "POST"])
async def api_handler(request: Request):
    return {"message": "Hello"}

# Shortcut methods
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

> **Note**: `module_name` must be explicitly passed as the first parameter, and the route path will automatically have the module name prefix added.

### WebSocket Decorators

```python
from fastapi import WebSocket

# Basic WebSocket
@router.ws("my_module", "/ws")
async def websocket_handler(websocket: WebSocket):
    while True:
        data = await websocket.receive_text()
        await websocket.send_text(f"Echo: {data}")

# WebSocket with authentication (Recommended: use auth_handler to control connection)
async def ws_auth(websocket: WebSocket) -> bool:
    token = websocket.query_params.get("token")
    return token == "secret"

@router.ws("my_module", "/secure_ws", auth_handler=ws_auth)
async def secure_ws_handler(websocket: WebSocket):
    while True:
        data = await websocket.receive_text()
        await websocket.send_text(f"Echo: {data}")
```

## Traditional Registration Method

```python
from fastapi import Request

async def hello_handler(request: Request):
    return {"message": "Hello World"}

# Basic registration
router.register_http_route(
    module_name="my_module",
    path="/hello",
    handler=hello_handler,
    methods=["GET"],
)

# Registration with rate limiting and documentation info
router.register_http_route(
    module_name="my_module",
    path="/api/data",
    handler=data_handler,
    methods=["POST"],
    rate_limit="10/minute",
    summary="Data API",
    tags=["API"],
)
```

### WebSocket Registration

```python
from fastapi import WebSocket

async def websocket_handler(websocket: WebSocket):
    while True:
        data = await websocket.receive_text()
        await websocket.send_text(f"Echo: {data}")

# Basic registration
router.register_websocket(
    module_name="my_module",
    path="/ws",
    handler=websocket_handler,
)

# Registration with authentication (Recommended)
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

**Parameter Description:**

| Parameter | Description | Default Value |
|----------|-------------|---------------|
| `module_name` | Module name (required) | - |
| `path` | WebSocket path | - |
| `handler` | Handler function | - |
| `auth_handler` | Authentication function, returning `False` will automatically close the connection | `None` |
| `auto_accept` | Whether to automatically `accept()` | `True` |

> **Recommendation**: Use `auth_handler` for connection confirmation rather than disabling `auto_accept`. Only set `auto_accept=False` when you need complete control over the connection flow.

## Route Grouping

```python
# Create a route group with prefix
group = router.group("my_module", prefix="/v1")

@group.get("/users")
async def list_users(request: Request):
    return {"users": []}

@group.post("/users")
async def create_user(request: Request):
    return {"created": True}

# Actual path: /my_module/v1/users
```

## Route Middleware

Middleware supports glob pattern matching for paths:

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

## Rate Limiting

Use sliding window algorithm to rate limit routes:

```python
@router.get("my_module", "/limited", rate_limit="10/minute")
async def limited_endpoint(request: Request):
    return {"ok": True}

@router.post("my_module", "/submit", rate_limit="5/minute")
async def submit_data(request: Request):
    return {"submitted": True}
```

Rate limiting format: `{count}/{time window}`, e.g., `10/minute`, `100/hour`.

## CORS Configuration

```python
router.setup_cors(
    allow_origins=["https://example.com"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```

Can also configure through `config.toml`:

```toml
[router.cors]
allow_origins = ["https://example.com"]
allow_methods = ["GET", "POST"]
allow_headers = ["*"]
```

## Security Headers

```python
router.setup_security_headers()
```

Automatically adds security headers such as `X-Content-Type-Options`, `X-Frame-Options`, `X-XSS-Protection`, etc.

Can also configure through `config.toml`:

```toml
[router.security]
enabled = true
```

## Auto Documentation

Router defaults to OpenAPI interactive documentation:

```python
# Disable documentation
router.disable_docs()

# Customize documentation info
router.set_docs_info(
    title="My API",
    description="API Documentation",
    version="1.0.0"
)
```

## Path Handling

Route paths automatically have the module name added as a prefix to avoid conflicts:

```python
# Register path "/api" to module "my_module"
# Actual access path is "/my_module/api"
router.register_http_route("my_module", "/api", handler)
```

## Authentication Mechanism

Recommended to use `auth_handler` to control connection access:

```python
async def auth_handler(websocket: WebSocket) -> bool:
    token = websocket.query_params.get("token")
    return token == "secret"

# Decorator method
@router.ws("my_module", "/secure_ws", auth_handler=auth_handler)
async def secure_handler(websocket: WebSocket):
    while True:
        data = await websocket.receive_text()
        await websocket.send_text(f"Echo: {data}")

# Traditional registration method
router.register_websocket(
    module_name="my_module",
    path="/secure_ws",
    handler=websocket_handler,
    auth_handler=auth_handler,
)
```

The `auth_handler` is executed after the connection is established. Returning `False` will automatically close the connection (status code 1008).

> Only set `auto_accept=False` when you need complete control over the connection flow (e.g., custom handshake protocol).

## System Routes

The Router Manager automatically provides two system routes:

### Health Check

```python
GET /health
# Returns:
{"status": "ok", "service": "ErisPulse Router"}
```

### Route List

```python
GET /routes
# Returns information for all registered routes
```

## Lifecycle Integration

```python
from ErisPulse.Core import lifecycle

@lifecycle.on("server.start")
async def on_server_start(event):
    print(f"Server started: {event['data']['base_url']}")

@lifecycle.on("server.stop")
async def on_server_stop(event):
    print("Server is stopping...")
```

## Best Practices

1. **Prioritize Decorators**: `@router.get()` etc. are more concise than `register_http_route()`
2. **Explicitly Pass module_name**: The first parameter to decorators must be the module name and cannot be omitted
3. **Use Route Groups**: Use `create_group()` to organize multiple routes for the same module
4. **Security Considerations**: Implement authentication mechanisms and security headers for sensitive operations
5. **Reasonable Rate Limiting**: Set rate limits for high-frequency APIs
6. **Error Handling**: Implement appropriate error handling and response formats

## Related Documentation

- [Module Development Guide](../developer-guide/modules/getting-started.md) - Learn about module route registration
- [Best Practices](../developer-guide/modules/best-practices.md) - Suggestions for route usage