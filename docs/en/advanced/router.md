# Router Manager

The ErisPulse Router Manager provides unified HTTP and WebSocket routing management, supporting multi-adapter route registration and lifecycle management. The underlying layer is encapsulated through an abstraction layer (currently FastAPI + Uvicorn).

## Overview

The main functions of the Router Manager are:

- **Decorator Routes**: Support `@http` / `@get` / `@post` / `@put` / `@delete` / `@ws` decorators for quick registration
- **Automatic Injection**: Route handlers do not need to import FastAPI types; the framework automatically injects abstract objects
- **Route Grouping**: Support `RouteGroup` with prefix and version number
- **Route Middleware**: Support request interception with glob pattern matching
- **Rate Limiting**: Built-in sliding window rate limiting
- **CORS Support**: One-click enable Cross-Origin Resource Sharing
- **Security Headers**: Automatically add security response headers
- **Automatic Documentation**: Interactive documentation based on OpenAPI
- **WebSocket Support**: Complete WebSocket connection management, custom authentication, and lifecycle hooks
- **Lifecycle Integration**: Deep integration with the ErisPulse lifecycle system
- **SSL/TLS Support**: Support HTTPS and WSS secure connections
- **Home Page Entry**: Support modules to register quick entry buttons on the root route `/`, supporting internationalization

## Abstract Types

ErisPulse provides server-side abstract types, allowing modules to avoid direct dependency on FastAPI:

| Abstract Type | FastAPI Correspondence | Description |
|---------------|------------------------|-------------|
| `HttpRequest` | `fastapi.Request` | HTTP request encapsulation, fully compatible interface |
| `WebSocketConnection` | `fastapi.WebSocket` | WebSocket connection encapsulation, additional lifecycle hooks provided |
| `WebSocketDisconnect` | `fastapi.WebSocketDisconnect` | WebSocket disconnection exception |

> `WebSocketConnection` inherits from `WebSocketConnectionBase`, sharing the same send/receive/iter/close interface with the client-side WebSocket (`ClientWebSocket`). The same business logic code can be used for both client and server side.
>
> The underlying FastAPI native object can be accessed via the `.raw` attribute. Code using native FastAPI types is also fully compatible.

## Decorator Routes (Recommended)

### Registration Forms: Single-Parameter (Recommended) and Two-Parameter

Decorator routes support two forms; **single-parameter is recommended**—consistent with command/event triggers, with automatic namespace assignment to the current module:

```python
from ErisPulse import router

# Single-parameter (recommended): automatically assigned to module_name/hello → actual path /my_module/hello
@router.get("/hello")
async def hello():
    return {"ok": True}

# Single-parameter WebSocket: @ws("chat") → /my_module/chat
@router.ws("chat")
async def chat(ws):
    ...

# Two-parameter: explicitly specify module name (same rule, used when registering across modules/tool code)
@router.get("other_module", "/info")
async def get_info(request):
    return {"method": request.method, "path": str(request.url)}
```

> [!NOTE]
> Single-parameter form requires registration within the module/adapter **loading context** (the framework has injected the namespace); calling without a context will throw a `ValueError` and prompt to explicitly pass the module name.

### HTTP Decorators

```python
from ErisPulse import router, HttpRequest

# Also can explicitly annotate abstract types
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

> **Automatic Injection Rule**: When the handler's first parameter is named `request` or `req` and has no FastAPI type annotation, the framework automatically injects `HttpRequest`. Handlers without parameters or with non-request parameter names are unaffected.

#### Response Return Convention (2.10+)

Handler return values support **tuple convention** (recommended writing style, explicitly controlling status code), while dict/str/Response remain unchanged:

```python
@router.post("/login")
async def login(request):
    if not check_token(request):
        # (body, status_code) → 401 JSON
        return {"error": "unauthorized", "message": "token invalid"}, 401
    # (body, status_code, headers) can also include response headers
    return {"user_id": 1}, 200, {"X-Request-Cost": "12ms"}

# Or use the respond() helper function (message automatically merged into response body)
from ErisPulse import respond

@router.get("/me")
async def me():
    return respond({"user_id": 1}, status_code=200, message="ok")
```

Path/query parameters can be directly annotated using FastAPI native annotations (`item_id: int`, `page: int = 1`), and middleware is covered in the [Route Middleware](#route-middleware) section.

### WebSocket Decorators

```python
from ErisPulse import WebSocketConnection, WebSocketDisconnect

# Basic WebSocket (single-parameter form)
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

# WebSocket with authentication
async def ws_auth(ws: WebSocketConnection) -> bool:
    token = ws.query_params.get("token")
    return token == "secret"

@router.ws("secure_ws", auth_handler=ws_auth)
async def secure_ws_handler(ws):
    while True:
        data = await ws.receive_text()
        await ws.send_text(f"Echo: {data}")
```

> **Note**: WebSocket handlers and authentication handlers also support automatic injection. No parameter annotation is needed to obtain a `WebSocketConnection`. Passing the native object via `fastapi.WebSocket` is also possible, but the abstract type is recommended.

### Automatic Connection Registration (Connection Pool, 2.10+)

Connections established via `@ws` / `@sse` are **automatically registered** into the framework connection pool by default (`track=False` disables this):
Within the handler, `ws.id` / `ws.join_group(...)` are available, and any module can
`connections.list(namespace=...)` to view connections in this module and broadcast to groups.
See [Connection Pool and Broadcasting](connections.md).

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
| `auth_handler` | Authentication function, returning `False` will automatically close the connection | `None` |
| `auto_accept` | Whether to automatically `accept()` | `True` |

> **Recommendation**: Use `auth_handler` for connection confirmation, rather than disabling `auto_accept`. Only set `auto_accept=False` if you need complete control over the connection flow.

## WebSocket Lifecycle Hooks

`WebSocketConnection` provides callback registration for disconnection and errors, without manual try/catch:

```python
from ErisPulse.Core import WebSocketConnection

@router.ws("my_module", "/ws")
async def my_ws(ws: WebSocketConnection):
    # Decorator-style registration
    @ws.on_disconnect
    async def on_close(ws, reason="unknown"):
        print(f"Disconnection reason: {reason}")

    # Can also be called directly
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

Starting from version 2.7.0, each HTTP request carries an `X-Request-ID` correlation ID, used for logging / distributed tracing:

- **Generation Rule**: Prioritize using the `X-Request-ID` request header passed from the client (for distributed tracing scenarios); otherwise, generate a UUID
- **Response Header**: The response will write back the `X-Request-ID`, making it convenient for the client to correlate requests with logs
- **Lifecycle Events**: The `server.request` and `server.response` event data will add a `request_id` field

```python
# Listen for request events in the module, and correlate requests-responses by request_id
@sdk.lifecycle.on("server.request")
async def on_request(data):
    print(f"[{data['request_id']}] {data['method']} {data['path']}")

@sdk.lifecycle.on("server.response")
async def on_response(data):
    print(f"[{data['request_id']}] -> {data['status_code']}")
```

Clients can customize the ID for cross-service tracing:

```bash
curl -H "X-Request-ID: my-trace-id" http://localhost:8080/my_module/health
```

## Rate Limiting

Use a sliding window algorithm to limit route access:

```python
@router.get("my_module", "/limited", rate_limit="10/minute")
async def limited_endpoint(request):
    return {"ok": True}

@router.post("my_module", "/submit", rate_limit="5/minute")
async def submit_data(request):
    return {"submitted": True}
```

Rate limiting format: `{count}/{time window}`, such as `10/minute`, `100/hour`.

## CORS Configuration

```python
router.setup_cors(
    allow_origins=["https://example.com"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```

CORS can also be configured via `config.toml`:

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

Automatically add security headers such as `X-Content-Type-Options`, `X-Frame-Options`, and `X-XSS-Protection`.

These can also be configured via `config.toml`:

```toml
[router.security]
enabled = true
```

## Automatic Documentation

The Router automatically enables OpenAPI interactive documentation:

```python
# Disable documentation
router.disable_docs()

# Customize documentation information
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

The root route `/` displays the ErisPulse brand page, automatically detecting Dashboard availability and adding entry buttons.

## Home Page Entry

The Router Manager allows external modules to register quick entry buttons on the root route `/`, making it convenient for users to access the management pages of various modules.

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
| `name` | `str` / `dict` | Button display text; if a dictionary `{"i18n": "key", "default": "text"}` is passed, internationalization is used | Yes |
| `url` | `str` | Button link address | Yes |
| `icon_svg` | `str` | Optional SVG icon markup | No |

### Dashboard Auto-Registration

When the `sdk.Dashboard` is detected as available, the Router Manager automatically adds a Dashboard button at the beginning of the entry list, without requiring manual registration.

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
2. **Use Automatic Injection**: Name the first parameter of the handler `request` or `req` without any type annotation to obtain `HttpRequest`
3. **Explicitly Pass module_name**: The first parameter of the decorator must be the module name, not omitted
4. **Use Route Grouping**: Use `group()` to organize multiple routes within the same module
5. **Security Consideration**: Implement authentication mechanisms and security headers for sensitive operations
6. **Reasonable Rate Limiting**: Set rate limits for high-frequency interfaces
7. **Use Lifecycle Hooks**: Use `@ws.on_disconnect` / `@ws.on_error` to handle WebSocket exceptions, avoiding manual try/catch

## Related Documentation

- [HTTP Client](http-client.md) - Using the built-in HTTP client to send requests
- [Module Development Guide](../developer-guide/modules/getting-started.md) - Learn about module route registration
- [Best Practices](../developer-guide/modules/best-practices.md) - Routing usage recommendations