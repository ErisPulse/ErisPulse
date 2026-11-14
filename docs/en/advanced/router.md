# Router Manager

> [!TIP]  
> **When to read this**: When you need HTTP/WebSocket/SSE routing (including connection pool broadcasting). Skip if not needed, as it does not affect other features.

The ErisPulse Router Manager provides unified HTTP and WebSocket routing management, supporting multi-adapter route registration and lifecycle management. Under the hood, it uses an abstraction layer (currently FastAPI + Uvicorn).

## Overview

The main functions of the Router Manager:

- **Decorator routing**: Supports `@http` / `@get` / `@post` / `@put` / `@delete` / `@ws` decorators for quick registration
- **Automatic injection**: Route handlers do not need to import FastAPI types, the framework automatically injects abstract objects
- **Route grouping**: Supports `RouteGroup` with prefix and version number
- **Route middleware**: Supports glob pattern matching for request interception
- **Rate limiting**: Built-in sliding window rate limiting
- **CORS support**: One-click enable Cross-Origin Resource Sharing
- **Security headers**: Automatically add security response headers
- **Automatic documentation**: Interactive documentation based on OpenAPI
- **WebSocket support**: Full WebSocket connection management, custom authentication, and lifecycle hooks
- **Lifecycle integration**: Deep integration with ErisPulse lifecycle system
- **SSL/TLS support**: Supports HTTPS and WSS secure connections
- **Home page entry**: Supports modules registering quick entry buttons on the root route `/`, supports internationalization

## Abstract Types

ErisPulse provides server-side abstract types, so modules do not need to directly depend on FastAPI:

| Abstract Type | FastAPI Correspondence | Description |
|---------------|------------------------|-------------|
| `HttpRequest` | `fastapi.Request` | HTTP request encapsulation, fully compatible interface |
| `WebSocketConnection` | `fastapi.WebSocket` | WebSocket connection encapsulation, additional lifecycle hooks |
| `WebSocketDisconnect` | `fastapi.WebSocketDisconnect` | WebSocket disconnect exception |

> `WebSocketConnection` inherits from `WebSocketConnectionBase`, sharing the same send/receive/iter/close interface with client-side WebSocket (`ClientWebSocket`). Client and server-side WebSocket can use the same business logic code.  
> Through the `.raw` attribute, you can access the underlying FastAPI native object. Code directly using FastAPI types is also fully compatible.

## Decorator Routing (Recommended)

### Registration Forms: Single-Parameter (Recommended) and Dual-Parameter

Decorator routing supports two forms, **single-parameter is recommended**—consistent with command/event triggers, and the namespace is automatically assigned to the current module:

```python
from ErisPulse import router

# Single parameter (recommended): automatically assigned to module_name/hello → actual path /my_module/hello
@router.get("/hello")
async def hello():
    return {"ok": True}

# Single parameter WebSocket: @ws("chat") → /my_module/chat
@router.ws("chat")
async def chat(ws):
    ...

# Dual parameter: explicitly specify module name (rules remain unchanged, used when registering across modules/tool code)
@router.get("other_module", "/info")
async def get_info(request):
    return {"method": request.method, "path": str(request.url)}
```

> [!NOTE]  
> Single-parameter form requires registration within the module/adapter **load context** (the framework has injected the assignment during loading); calling outside of a context without assignment will throw a `ValueError` and prompt to explicitly pass the module name.

### HTTP Decorators

```python
from ErisPulse import router, HttpRequest

# You can also explicitly annotate with abstract types
@router.post("/data")
async def post_data(request: HttpRequest):
    data = await request.json()
    return {"received": data}

@router.put("/data/{item_id}")
async def update_data(request):
    return {"updated": True}

@router.delete("/data/{item_id}")
async def delete_data(request):
    return {"deleted": True}
```

> **Automatic injection rule**: When the handler's first parameter is named `request` or `req` and has no FastAPI type annotation, the framework automatically injects `HttpRequest`. Handlers without parameters or non-request parameter names are unaffected.

#### Response Return Convention (2.10+)

Handler return values support **tuple convention** (recommended style, clearly controlling status codes), dict/str/Response still work as before:

```python
@router.post("/login")
async def login(request):
    if not check_token(request):
        # (body, status_code) → 401 JSON
        return {"error": "unauthorized", "message": "token invalid"}, 401
    # (body, status_code, headers) can also include response headers
    return {"user_id": 1}, 200, {"X-Request-Cost": "12ms"}

# Or use the respond() helper function (message is automatically merged into the response body)
from ErisPulse import respond

@router.get("/me")
async def me():
    return respond({"user_id": 1}, status_code=200, message="ok")
```

Path/query parameters use FastAPI native annotations directly (`item_id: int`, `page: int = 1`). Middleware is covered in the [Route Middleware](#route-middleware) section.

### WebSocket Decorators

```python
from ErisPulse import WebSocketConnection, WebSocketDisconnect

# Basic WebSocket (single parameter form)
@router.ws("ws")
async def websocket_handler(ws):
    async for msg in ws.iter_text():
        await ws.send_text(f"Echo: {msg}")

# WebSocket with lifecycle hooks
@router.ws("/ws/chat")
async def chat(ws: WebSocketConnection):
    @ws.on_disconnect
    async def on_disconnect(ws, reason="unknown"):
        print(f"User disconnected: {reason}")

    @ws.on_error
    async def on_error(ws, error=""):
        print(f"Connection error: {error}")

    async for msg in ws.iter_text():
        await ws.send_text(f"Echo: {msg}")

# WebSocket with authentication (token read from environment variable, do not hardcode in code)
import os

async def ws_auth(ws: WebSocketConnection) -> bool:
    token = ws.query_params.get("token")
    expected = os.environ.get("ERISPULSE_WS_TOKEN", "")
    return bool(expected) and token == expected

@router.ws("secure_ws", auth_handler=ws_auth)
async def secure_ws_handler(ws):
    while True:
        data = await ws.receive_text()
        await ws.send_text(f"Echo: {data}")
```

> **Note**: WebSocket handlers and authentication handlers also support automatic injection. You can get `WebSocketConnection` without parameter annotations. Passing the native `fastapi.WebSocket` is also possible, but abstract types are recommended.

### Automatic Connection Registration (Connection Pool, 2.10+)

Connections established via `@ws` / `@sse` are **automatically registered** into the framework connection pool by default (`track=False` disables registration):  
Within the handler, `ws.id` / `ws.join_group(...)` are available, and any module can use `connections.list(namespace=...)` to view connections in its module and broadcast to groups.  
See [Connection Pool and Broadcasting](connections.md) for details.

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

# With rate limiting and documentation information
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

# Registration with authentication (recommended)
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
| `module_name` | Module name (required) | - |
| `path` | WebSocket path | - |
| `handler` | Handler function | - |
| `auth_handler` | Authentication function, returns `False` will automatically close the connection | `None` |
| `auto_accept` | Whether to automatically `accept()` | `True` |

> **Recommendation**: Use `auth_handler` for connection confirmation, rather than setting `auto_accept=False`. Only set `auto_accept=False` when you need full control over the connection process.

## WebSocket Lifecycle Hooks

`WebSocketConnection` provides callback registration for disconnect and error, eliminating the need for manual try/catch:

```python
from ErisPulse.Core import WebSocketConnection

@router.ws("my_module", "/ws")
async def my_ws(ws: WebSocketConnection):
    # Decorator way to register
    @ws.on_disconnect
    async def on_close(ws, reason="unknown"):
        print(f"Disconnect reason: {reason}")

    # Can also call directly
    async def on_err(ws, error=""):
        print(f"Error: {error}")
    ws.on_error(on_err)

    # Normal business logic
    async for msg in ws.iter_text():
        await ws.send_text(f"Echo: {msg}")
```

## Route Grouping

```python
# Create a route group with a prefix
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

Middleware supports glob pattern matching paths:

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

## Request Correlation ID (X-Request-ID)

Starting from 2.7.0, each HTTP request carries an `X-Request-ID` correlation ID for log/trace linkage:

- **Generation rule**: Prefers to reuse the `X-Request-ID` request header from the client (distributed tracing scenarios); otherwise, it generates a UUID automatically
- **Response header**: The response writes back `X-Request-ID`, making it easy for the client to correlate requests with logs
- **Lifecycle events**: The `server.request` and `server.response` event data add a `request_id` field

```python
# In modules, listen for request events and trace request-response by request_id
@sdk.lifecycle.on("server.request")
async def on_request(data):
    print(f"[{data['request_id']}] {data['method']} {data['path']}")

@sdk.lifecycle.on("server.response")
async def on_response(data):
    print(f"[{data['request_id']}] -> {data['status_code']}")
```

The client can customize the ID for cross-service tracing:

```bash
curl -H "X-Request-ID: my-trace-id" http://localhost:8080/my_module/health
```

## Rate Limiting

Use the sliding window algorithm to rate limit routes:

```python
@router.get("my_module", "/limited", rate_limit="10/minute")
async def limited_endpoint(request):
    return {"ok": True}

@router.post("my_module", "/submit", rate_limit="5/minute")
async def submit_data(request):
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

It can also be configured via `config.toml`:

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

It can also be configured via `config.toml`:

```toml
[router.security]
enabled = true
```

## Automatic Documentation

The router enables OpenAPI interactive documentation by default:

```python
# Disable documentation
router.disable_docs()

# Customize documentation information
router.set_docs_info(
    title="My API",
    description="API documentation",
    version="1.0.0"
)
```

## Path Handling

Route paths are automatically prefixed with the module name to avoid conflicts:

```python
# Register path "/api" to module "my_module"
# The actual access path is "/my_module/api"
router.register_http_route("my_module", "/api", handler)
```

> [!WARNING]  
> Route paths (including module name prefix) are **case-sensitive**. The registered module name's case determines the actual path: when the module name is `Test`, registering `/api` results in the actual path being `/Test/api`, and accessing `/test/api` will return 404.

## System Routes

The router manager automatically provides the following system routes:

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

The root route `/` displays the ErisPulse brand page and automatically detects the availability of Dashboard, adding an entry button.

## Home Page Entry

The router manager allows external modules to register quick entry buttons on the root route `/`, making it convenient for users to access various modules' management pages quickly.

### Register Entry

```python
# Simple registration
router.register_home_entry(
    name="My Panel",
    url="/mymodule/admin",
)

# Registration with icon (SVG)
router.register_home_entry(
    name="Console",
    url="/console",
    icon_svg='<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M4 17l6-6-6-6"/><path d="M12 19h8"/></svg>',
)

# Internationalization support (project i18n dictionary format)
router.register_home_entry(
    name={"i18n": "mymodule.home.entry", "default": "My Panel"},
    url="/mymodule/admin",
)
```

**Parameter Description:**

| Parameter | Type | Description | Required |
|-----------|------|-------------|----------|
| `name` | `str` / `dict` | Button display text; when passing a dictionary `{"i18n": "key", "default": "text"}`, use internationalization | Yes |
| `url` | `str` | Button link address | Yes |
| `icon_svg` | `str` | Optional SVG icon markup | No |

### Dashboard Auto-Registration

When `sdk.Dashboard` is detected as available, the router manager automatically adds a Dashboard button to the entry list at the first position, without manual registration.

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

## Advanced HttpRequest Properties

Besides `method` / `query` / `headers` / `json` / `body`, `HttpRequest` also exposes advanced capabilities (useful for authentication middleware, disconnection-aware long tasks):

| Property / Method | Description |
|-------------------|-------------|
| `request.session` | Session dict (requires session middleware support), persists across requests |
| `request.auth` | Authentication information (written by authentication middleware) |
| `request.user` | Current user object (written by authentication middleware) |
| `request.url_for(name, **params)` | Reverse routing: generates URL by route name |
| `await request.is_disconnected()` | Whether the client has disconnected (used for SSE/long task polling exit) |
| `request.raw` | Underlying Starlette request object (escape hatch, see compatibility note below) |

## Escape Hatch: router.app

`router.app` directly exposes the underlying FastAPI application instance (lazily created, loaded on first access to web stack and core route registration), covering scenarios where decorators cannot express—mounting sub-applications, global middleware, integrating with the FastAPI ecosystem (StaticFiles / background task templates, etc.):

```python
from ErisPulse.Core import router
from starlette.staticfiles import StaticFiles

app = router.app
app.mount("/static", StaticFiles(directory="static"), name="static")
```

> [!WARNING]  
> **Compatibility boundary**: `router.app` is an escape hatch, not a stable contract—it exposes the current web stack (FastAPI/Starlette) instance. If the framework migrates the underlying web implementation in the future, code depending on the internal structure of `app` (middleware order, Starlette-specific APIs) will encounter **breaking changes**. Prioritize using `@router.http` / `HttpRequest` abstraction layer (same applies to `request.raw`), and limit the use of `.app` to a single adapter layer within the module—this reduces the adaptation surface when migrating.

## Best Practices

1. **Prefer abstract types**: Use `HttpRequest` / `WebSocketConnection` instead of `fastapi.Request` / `fastapi.WebSocket`, avoiding hard dependencies
2. **Leverage automatic injection**: Name the first parameter of the handler `request` or `req`, and obtain `HttpRequest` without any type annotation
3. **Prefer single-parameter form**: In the module load context, prefer single-parameter form (automatic namespace assignment); when registering across modules/tool code, explicitly pass the module name
4. **Use route grouping**: Use `group()` to organize multiple routes of the same module
5. **Security considerations**: Implement authentication mechanisms and security headers for sensitive operations
6. **Reasonable rate limiting**: Set rate limits for high-frequency interfaces
7. **Use lifecycle hooks**: Handle WebSocket exceptions through `@ws.on_disconnect` / `@ws.on_error`, avoiding manual try/catch
8. **Constrained use of escape hatches**: Use `router.app` / `request.raw` only when the abstraction layer cannot express, and limit the dependency to a single point, reducing the adaptation surface when the framework's underlying implementation changes

## Related Documentation

- [Network Client](client.md) - Use the built-in request client to send requests
- [Module Development Guide](../developer-guide/modules/getting-started.md) - Learn about module route registration
- [Best Practices](../developer-guide/modules/best-practices.md) - Routing usage recommendations