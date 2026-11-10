# Router Manager

> [!TIP]
> **When to read this**: When you need HTTP / WebSocket / SSE routing (including connection pool broadcasting). Skip it otherwise; it does not affect the use of other features.


The ErisPulse Router Manager provides unified HTTP and WebSocket route management, supporting multi-adapter route registration and lifecycle management. It is wrapped via an abstraction layer underneath (currently FastAPI + Uvicorn).

## Overview

The main features of the Router Manager:

- **Decorator routes**: supports `@http` / `@get` / `@post` / `@put` / `@delete` / `@ws` decorators for quick registration
- **Auto injection**: route handlers do not need to import FastAPI types; the framework automatically injects abstract objects
- **Route groups**: supports `RouteGroup` with prefixes and version numbers
- **Route middleware**: supports glob pattern-matched request interception
- **Rate limiting**: built-in sliding window rate limiting
- **CORS support**: enable Cross-Origin Resource Sharing with a single call
- **Security headers**: automatically adds security response headers
- **Automatic docs**: OpenAPI-based interactive documentation
- **WebSocket support**: full WebSocket connection management, custom authentication, and lifecycle hooks
- **Lifecycle integration**: deeply integrated with the ErisPulse lifecycle system
- **SSL/TLS support**: supports HTTPS and WSS secure connections
- **Home page entries**: supports modules registering quick-entry buttons on the root route `/`, with internationalization support

## Abstract Types

ErisPulse provides server-side abstract types so that modules do not need to depend on FastAPI directly:

| Abstract Type | FastAPI Equivalent | Description |
|---------|-------------|------|
| `HttpRequest` | `fastapi.Request` | HTTP request wrapper, fully compatible interface |
| `WebSocketConnection` | `fastapi.WebSocket` | WebSocket connection wrapper, with additional lifecycle hooks |
| `WebSocketDisconnect` | `fastapi.WebSocketDisconnect` | WebSocket disconnect exception |

> `WebSocketConnection` inherits from `WebSocketConnectionBase` and shares the same send/receive/iter/close interface as the client-side WebSocket (`ClientWebSocket`). Client and server WebSockets can use the same business logic code.
>
> The underlying native FastAPI object can be accessed via the `.raw` property. Code that uses FastAPI types directly is also fully compatible.

## Decorator Routes (Recommended)

### Registration Forms: Single-Argument (Recommended) and Two-Argument

Decorator routes support two forms. The **single-argument form is recommended** — it is consistent with command / event triggers, and the namespace is automatically attributed to the current module:

```python
from ErisPulse import router

# Single-argument (recommended): auto-attributed to module_name/hello → actual path /my_module/hello
@router.get("/hello")
async def hello():
    return {"ok": True}

# Single-argument WebSocket: @ws("chat") → /my_module/chat
@router.ws("chat")
async def chat(ws):
    ...

# Two-argument: explicitly specify the module name (rules unchanged; used when registering from cross-module/utility code)
@router.get("other_module", "/info")
async def get_info(request):
    return {"method": request.method, "path": str(request.url)}
```

> [!NOTE]
> The single-argument form requires registration within a module/adapter **loading context** (the framework has already injected the attribution during loading);
> calling it in a context without attribution raises a `ValueError` prompting you to pass the module name explicitly.

### HTTP Decorators

```python
from ErisPulse import router, HttpRequest

# You can also explicitly annotate abstract types
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

> **Auto injection rule**: when the first parameter of a handler is named `request` or `req` and has no FastAPI type annotation, the framework automatically injects `HttpRequest`. Handlers with no parameters or with other parameter names are unaffected.

#### Response Return Conventions (2.10+)

Handler return values support the **tuple convention** (recommended; explicitly controls the status code), while dict/str/Response work as before:

```python
@router.post("/login")
async def login(request):
    if not check_token(request):
        # (body, status_code) → 401 JSON
        return {"error": "unauthorized", "message": "invalid token"}, 401
    # (body, status_code, headers) can also carry response headers
    return {"user_id": 1}, 200, {"X-Request-Cost": "12ms"}

# Or use the respond() helper (message is merged into the response body automatically)
from ErisPulse import respond

@router.get("/me")
async def me():
    return respond({"user_id": 1}, status_code=200, message="ok")
```

Path / query parameters can use native FastAPI annotations directly (`item_id: int`, `page: int = 1`);
for middleware, see the [Route Middleware](#route-middleware) section.

### WebSocket Decorators

```python
from ErisPulse import WebSocketConnection, WebSocketDisconnect

# Basic WebSocket (single-argument form)
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

# WebSocket with authentication (read the token from an environment variable; do not hardcode it in code)
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

> **Note**: WebSocket handlers and authentication handlers also support auto injection. You get a `WebSocketConnection` without any parameter annotation. Annotating with `fastapi.WebSocket` also passes in the native object, but abstract types are recommended.

### Automatic Connection Registration (Connection Pool, 2.10+)

Connections established by `@ws` / `@sse` are **automatically registered** into the framework's connection pool by default (`track=False` disables this):
within the handler, `ws.id` / `ws.join_group(...)` are available, and any module can
use `connections.list(namespace=...)` to view this module's connections and broadcast to groups.
See [Connection Pool and Broadcasting](connections.md) for details.

## Traditional Registration

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

# With rate limiting and docs info
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

**Parameters:**

| Parameter | Description | Default |
|------|------|--------|
| `module_name` | Module name (required) | - |
| `path` | WebSocket path | - |
| `handler` | Handler function | - |
| `auth_handler` | Authentication function; returning `False` automatically closes the connection | `None` |
| `auto_accept` | Whether to automatically `accept()` | `True` |

> **Recommended**: use `auth_handler` for connection verification rather than disabling `auto_accept`. Only set `auto_accept=False` if you need full control over the connection flow.

## WebSocket Lifecycle Hooks

`WebSocketConnection` provides callback registration for disconnection and errors, eliminating the need for manual try/catch:

```python
from ErisPulse.Core import WebSocketConnection

@router.ws("my_module", "/ws")
async def my_ws(ws: WebSocketConnection):
    # Register via decorator
    @ws.on_disconnect
    async def on_close(ws, reason="unknown"):
        print(f"Disconnect reason: {reason}")

    # Or call directly
    async def on_err(ws, error=""):
        print(f"Error: {error}")
    ws.on_error(on_err)

    # Normal business logic
    async for msg in ws.iter_text():
        await ws.send_text(f"Echo: {msg}")
```

## Route Groups

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

## Request Correlation ID (X-Request-ID)

Starting from 2.7.0, every HTTP request carries an `X-Request-ID` correlation ID, used to link logs / trace chains:

- **Generation rule**: prefer the `X-Request-ID` request header passed in by the client (for distributed tracing scenarios); otherwise, a UUID is generated automatically
- **Response header**: the response writes back `X-Request-ID`, making it easy for clients to correlate requests with logs
- **Lifecycle events**: the `server.request` and `server.response` event data now include a `request_id` field

```python
# Listen for request events in a module, linking request-response by request_id
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

Rate limiting is applied to routes using the sliding window algorithm:

```python
@router.get("my_module", "/limited", rate_limit="10/minute")
async def limited_endpoint(request):
    return {"ok": True}

@router.post("my_module", "/submit", rate_limit="5/minute")
async def submit_data(request):
    return {"submitted": True}
```

Rate limit format: `{count}/{time window}`, e.g., `10/minute`, `100/hour`.

## CORS Configuration

```python
router.setup_cors(
    allow_origins=["https://example.com"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```

You can also configure it via `config.toml`:

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

You can also configure it via `config.toml`:

```toml
[router.security]
enabled = true
```

## Automatic Documentation

The Router enables OpenAPI interactive documentation by default:

```python
# Disable docs
router.disable_docs()

# Customize docs info
router.set_docs_info(
    title="My API",
    description="API documentation",
    version="1.0.0"
)
```

## Path Handling

Route paths automatically get the module name as a prefix to avoid conflicts:

```python
# Register path "/api" to module "my_module"
# The actual access path is "/my_module/api"
router.register_http_route("my_module", "/api", handler)
```

> [!WARNING]
> Route paths (including the module name prefix) are **case-sensitive**. The case of the actual path matches the module name as registered: if the module name is `Test`, registering `/api` yields the actual path `/Test/api`, and accessing `/test/api` will return 404.

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
# Returns the ErisPulse branding page
```

The root route `/` displays the ErisPulse branding page, automatically detecting Dashboard availability and adding an entry button.

## Home Page Entries

The Router Manager allows external modules to register quick-entry buttons on the root route `/`, making it convenient for users to quickly access each module's admin pages.

### Registering an Entry

```python
# Simple registration
router.register_home_entry(
    name="My Panel",
    url="/mymodule/admin",
)

# Registration with an icon (SVG)
router.register_home_entry(
    name="Console",
    url="/console",
    icon_svg='<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M4 17l6-6-6-6"/><path d="M12 19h8"/></svg>',
)

# Registration with internationalization support (project i18n dict format)
router.register_home_entry(
    name={"i18n": "mymodule.home.entry", "default": "My Panel"},
    url="/mymodule/admin",
)
```

**Parameters:**

| Parameter | Type | Description | Required |
|------|------|------|------|
| `name` | `str` / `dict` | Button display text; when passing a `{"i18n": "key", "default": "text"}` dict, internationalization is used | Yes |
| `url` | `str` | Button link URL | Yes |
| `icon_svg` | `str` | Optional SVG icon markup | No |

### Dashboard Auto-Registration

When `sdk.Dashboard` is detected as available, the Router Manager automatically adds a Dashboard button at the top of the entry list; no manual registration is needed.

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

1. **Prefer abstract types**: use `HttpRequest` / `WebSocketConnection` instead of `fastapi.Request` / `fastapi.WebSocket` to avoid hard dependencies
2. **Leverage auto injection**: name the first handler parameter `request` or `req` to get an `HttpRequest` without any type annotation
3. **Prefer the single-argument form**: within a module loading context, prefer the single-argument form (auto-attributed namespace); pass the module name explicitly when registering from cross-module/utility code
4. **Use route groups**: use `group()` to organize multiple routes of the same module
5. **Security considerations**: implement authentication mechanisms and security headers for sensitive operations
6. **Sensible rate limiting**: set rate limits for high-frequency endpoints
7. **Use lifecycle hooks**: handle WebSocket exceptions via `@ws.on_disconnect` / `@ws.on_error` instead of manual try/catch

## Related Documentation

- [Network Client](client.md) - Send requests with the built-in request client
- [Module Development Guide](../developer-guide/modules/getting-started.md) - Learn about module route registration
- [Best Practices](../developer-guide/modules/best-practices.md) - Route usage recommendations