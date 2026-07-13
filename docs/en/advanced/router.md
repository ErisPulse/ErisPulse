# Router Manager

The ErisPulse Router Manager provides unified HTTP and WebSocket routing management, supporting multi-adapter route registration and lifecycle management. Under the hood, it is wrapped by an abstraction layer (currently FastAPI + Uvicorn)

## Overview

Key features of the Router Manager:

- **Decorator Routes**: Support `@http` / `@get` / `@post` / `@put` / `@delete` / `@ws` decorators for quick registration
- **Auto Injection**: Route handlers do not need to import FastAPI types; the framework automatically injects abstract objects
- **Route Groups**: Support for `RouteGroup` with prefix and version
- **Route Middleware**: Request interception supporting glob pattern matching
- **Rate Limiting**: Built-in sliding window rate limiting
- **CORS Support**: One-click enable Cross-Origin Resource Sharing
- **Security Headers**: Automatic addition of security response headers
- **Auto Docs**: Interactive documentation based on OpenAPI
- **WebSocket Support**: Complete WebSocket connection management, custom authentication, and lifecycle hooks
- **Lifecycle Integration**: Deep integration with the ErisPulse lifecycle system
- **SSL/TLS Support**: Support for HTTPS and WSS secure connections
- **Home Page Entry**: Support for module shortcuts on the root route `/`, with internationalization support

## Abstract Types

ErisPulse provides server-side abstract types to allow modules to avoid direct dependencies on FastAPI:

| Abstract Type | FastAPI Equivalent | Description |
|--------------|-------------------|-------------|
| `HttpRequest` | `fastapi.Request` | HTTP request wrapper, fully compatible interface |
| `WebSocketConnection` | `fastapi.WebSocket` | WebSocket connection wrapper, additionally provides lifecycle hooks |
| `WebSocketDisconnect` | `fastapi.WebSocketDisconnect` | WebSocket disconnect exception |

> `WebSocketConnection` inherits from `WebSocketConnectionBase` and shares the same send/receive/iter/close interface as client WebSockets (`ClientWebSocket`). Client and server WebSockets can use the same business logic code.
>
> Access the underlying FastAPI native object via the `.raw` attribute. Code directly using FastAPI types is also fully compatible.

## Decorator Routes (Recommended)

### HTTP Decorators

```python
from ErisPulse.Core import router
@router.get("my_module", "/info")
async def get_info(request):
    return {"method": request.method, "path": str(request.url)}

# Can also explicitly annotate abstract types
from ErisPulse.Core import HttpRequest

@router.post("my_module", "/data")
async def post_data(request: HttpRequest):
    data = await request.json()
    return {"received": data}

@router.put("my_module", "/data/{item_id}")
async def update_data(request):
    return {"updated": True}

@router.delete("my_module", "/data/{item_id}")
async def delete_data(request):
    return {"deleted": True}
```

> **Auto Injection Rule**: When the first parameter name of the handler is `request` or `req` and there are no FastAPI type annotations, the framework automatically injects `HttpRequest`. Handlers with no parameters or parameters that are not named request are unaffected.

### WebSocket Decorators

```python
from ErisPulse.Core import WebSocketConnection, WebSocketDisconnect

# Basic WebSocket
@router.ws("my_module", "/ws")
async def websocket_handler(ws):
    async for msg in ws.iter_text():
        await ws.send_text(f"Echo: {msg}")

# WebSocket with lifecycle hooks
@router.ws("my_module", "/ws/chat")
async def chat(ws: WebSocketConnection):
    @ws.on_disconnect
    async def on_disconnect(ws, reason="unknown"):
        print(f"User disconnected: {reason}")

    @ws.on_error
    async def on_error(ws, error=""):
        print(f"Connection error: {error}")

    async for msg in ws.iter_text():
        await ws.send_text(f"Echo: {msg}")

# WebSocket with authentication
async def ws_auth(ws: WebSocketConnection) -> bool:
    token = ws.query_params.get("token")
    return token == "secret"

@router.ws("my_module", "/secure_ws", auth_handler=ws_auth)
async def secure_ws_handler(ws):
    while True:
        data = await ws.receive_text()
        await ws.send_text(f"Echo: {data}")
```

> **Note**: WebSocket handlers and authentication handlers also support auto injection. You can get `WebSocketConnection` without parameter annotations. Annotating `fastapi.WebSocket` also passes the native object, but using abstract types is recommended.

## Traditional Registration Method

```python
async def hello_handler(request):
    return {"message": "Hello World"}

# Basic registration
router.register_http_route(
    module_name="my_module",
    path="/hello",
    handler=hello_handler,
    methods=["GET"],
)

# With rate limiting and doc info
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
from ErisPulse.Core import WebSocketConnection

async def websocket_handler(ws: WebSocketConnection):
    async for msg in ws.iter_text():
        await ws.send_text(f"Echo: {msg}")

# Basic registration
router.register_websocket(
    module_name="my_module",
    path="/ws",
    handler=websocket_handler,
)

# Registration with authentication (Recommended)
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

**Parameter Description:**

| Parameter | Description | Default |
|-----------|-------------|---------|
| `module_name` | Module name (Required) | - |
| `path` | WebSocket path | - |
| `handler` | Handler function | - |
| `auth_handler` | Authentication function, connection closes automatically if returns `False` | `None` |
| `auto_accept` | Whether to automatically `accept()` | `True` |

> **Recommendation**: Use `auth_handler` for connection confirmation instead of disabling `auto_accept`. Only set `auto_accept=False` when you need full control over the connection flow.

## WebSocket Lifecycle Hooks

`WebSocketConnection` provides registration for disconnection and error callbacks, eliminating the need for manual try/catch:

```python
from ErisPulse.Core import WebSocketConnection

@router.ws("my_module", "/ws")
async def my_ws(ws: WebSocketConnection):
    # Register via decorator
    @ws.on_disconnect
    async def on_close(ws, reason="unknown"):
        print(f"Reason for disconnect: {reason}")

    # Can also call directly
    async def on_err(ws, error=""):
        print(f"Error: {error}")
    ws.on_error(on_err)

    # Normal business logic
    async for msg in ws.iter_text():
        await ws.send_text(f"Echo: {msg}")
```

## Route Groups

```python
# Create a route group with prefix
group = router.group("my_module", prefix="/v1")

@group.get("/users")
async def list_users(request):
    return {"users": []}

@group.post("/users")
async def create_user(request):
    return {"created": True}

# Actual path: /my_module/v1/users
```

## Route Middleware

Middleware supports glob pattern matching for paths:

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

## Rate Limiting

Rate limit routes using the sliding window algorithm:

```python
@router.get("my_module", "/limited", rate_limit="10/minute")
async def limited_endpoint(request):
    return {"ok": True}

@router.post("my_module", "/submit", rate_limit="5/minute")
async def submit_data(request):
    return {"submitted": True}
```

Rate limit format: `{count}/{time_window}`, e.g., `10/minute`, `100/hour`.

## CORS Configuration

```python
router.setup_cors(
    allow_origins=["https://example.com"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```

Can also be configured via `config.toml`:

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

Automatically adds security headers such as `X-Content-Type-Options`, `X-Frame-Options`, `X-XSS-Protection`.

Can also be configured via `config.toml`:

```toml
[router.security]
enabled = true
```

## Auto Documentation

The Router enables OpenAPI interactive documentation by default:

```python
# Disable docs
router.disable_docs()

# Custom doc info
router.set_docs_info(
    title="My API",
    description="API Documentation",
    version="1.0.0"
)
```

## Path Handling

Route paths are automatically prefixed with the module name to avoid conflicts:

```python
# Register path "/api" to module "my_module"
# Actual access path is "/my_module/api"
router.register_http_route("my_module", "/api", handler)
```

## System Routes

The Router Manager automatically provides the following system routes:

### Health Check

```
GET /health
# Returns:
{"status": "ok", "service": "ErisPulse Router"}
```

### Root Page

```
GET /
# Returns ErisPulse brand page
```

The root route `/` displays the ErisPulse brand page, automatically detects Dashboard availability and adds entry buttons.

## Home Page Entry

The Router Manager allows external modules to register shortcut entry buttons on the root route `/`, making it easy for users to quickly access management pages for various modules.

### Register Entry

```python
# Simple registration
router.register_home_entry(
    name="My Dashboard",
    url="/mymodule/admin",
)

# Registration with icon (SVG)
router.register_home_entry(
    name="Console",
    url="/console",
    icon_svg='<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M4 17l6-6-6-6"/><path d="M12 19h8"/></svg>',
)

# Registration with internationalization (Project i18n dictionary format)
router.register_home_entry(
    name={"i18n": "mymodule.home.entry", "default": "我的面板"},
    url="/mymodule/admin",
)
```

**Parameter Description:**

| Parameter | Type | Description | Required |
|-----------|------|-------------|----------|
| `name` | `str` / `dict` | Button display text; uses internationalization when passed as `{"i18n": "key", "default": "text"}` dict | Yes |
| `url` | `str` | Button link address | Yes |
| `icon_svg` | `str` | Optional SVG icon markup | No |

### Dashboard Auto Registration

When `sdk.Dashboard` is detected as available, the Router Manager automatically adds a Dashboard button to the top of the entry list without manual registration.

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

1. **Prefer Abstract Types**: Use `HttpRequest` / `WebSocketConnection` instead of `fastapi.Request` / `fastapi.WebSocket` to avoid hard dependencies
2. **Leverage Auto Injection**: Name the first parameter of the handler `request` or `req` to get `HttpRequest` without any type annotations
3. **Explicitly Pass module_name**: The first argument of the decorator must be the module name and cannot be omitted
4. **Use Route Groups**: Use `group()` to organize multiple routes for the same module
5. **Security Considerations**: Implement authentication mechanisms and security headers for sensitive operations
6. **Reasonable Rate Limiting**: Set rate limits for high-frequency APIs
7. **Use Lifecycle Hooks**: Handle WebSocket exceptions via `@ws.on_disconnect` / `@ws.on_error` to avoid manual try/catch

## Related Documentation

- [HTTP Client](http-client.md) - Sending requests using the built-in HTTP client
- [Module Development Guide](../developer-guide/modules/getting-started.md) - Understanding module route registration
- [Best Practices](../developer-guide/modules/best-practices.md) - Recommendations for using routes