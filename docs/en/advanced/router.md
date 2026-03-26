# Router Manager

The ErisPulse Router Manager provides unified HTTP and WebSocket route management, supporting multi-adapter route registration and lifecycle management. It is built on FastAPI and provides complete web service capabilities.

## Overview

Key features of the Router Manager:

- **HTTP Route Management**: Supports route registration for various HTTP methods
- **WebSocket Support**: Complete WebSocket connection management and custom authentication
- **Lifecycle Integration**: Deeply integrated with the ErisPulse lifecycle system
- **Unified Error Handling**: Provides unified error handling and logging
- **SSL/TLS Support**: Supports HTTPS and WSS secure connections

## Basic Usage

### Registering HTTP Routes

```python
from fastapi import Request
from ErisPulse.Core import router

async def hello_handler(request: Request):
    return {"message": "Hello World"}

# Register GET route
router.register_http_route(
    module_name="my_module",
    path="/hello",
    handler=hello_handler,
    methods=["GET"]
)
```

### Registering WebSocket Routes

```python
from fastapi import WebSocket

# Automatically accepts connection by default
async def websocket_handler(websocket: WebSocket):
    # No manual accept needed by default, automatically called internally
    while True:
        data = await websocket.receive_text()
        await websocket.send_text(f"Echo: {data}")

router.register_websocket(
    module_name="my_module",
    path="/ws",
    handler=websocket_handler,
    auto_accept=True  # Defaults to True, can be omitted
)

# Manually control connection
async def manual_websocket_handler(websocket: WebSocket):
    # Decide whether to accept connection based on condition
    if some_condition:
        await websocket.accept()
        # Handle connection...
    else:
        await websocket.close(code=1008, reason="Not allowed")

router.register_websocket(
    module_name="my_module",
    path="/secure_ws",
    handler=manual_websocket_handler,
    auto_accept=False  # Manually control connection
)
```

**Parameter Description:**

- `module_name`: Module name
- `path`: WebSocket path
- `handler`: Handler function
- `auth_handler`: Optional authentication function
- `auto_accept`: Whether to automatically accept the connection (default `True`)
  - `True`: The framework automatically calls `websocket.accept()`, the handler does not need to call it manually
  - `False`: The handler must call `websocket.accept()` or `websocket.close()` itself

### Unregistering Routes

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

## Path Handling

Route paths automatically have the module name added as a prefix to avoid conflicts:

```python
# Register path "/api" to module "my_module"
# Actual access path is "/my_module/api"
router.register_http_route("my_module", "/api", handler)
```

## Authentication Mechanism

WebSocket supports custom authentication logic:

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

1. **Route Naming Conventions**: Use clear, descriptive path names
2. **Security Considerations**: Implement authentication mechanisms for sensitive operations
3. **Error Handling**: Implement appropriate error handling and response formats
4. **Connection Management**: Implement appropriate connection cleanup

## Related Documentation

- [Module Development Guide](../developer-guide/modules/getting-started.md) - Learn about module route registration
- [Best Practices](../developer-guide/modules/best-practices.md) - Suggestions for route usage