# Core Module API

This document details the ErisPulse core module API.

## Storage Module

### Basic Operations

```python
from ErisPulse import sdk

# Set value
sdk.storage.set("key", "value")

# Get value
value = sdk.storage.get("key", default_value)

# Get all keys
keys = sdk.storage.keys()

# Delete value
sdk.storage.delete("key")
```

### Transaction Operations

```python
# Use transactions to ensure data consistency
with sdk.storage.transaction():
    sdk.storage.set("key1", "value1")
    sdk.storage.set("key2", "value2")
    # If any operation fails, all changes will be rolled back
```

### Batch Operations

```python
# Batch set
sdk.storage.set_multi({
    "key1": "value1",
    "key2": "value2",
    "key3": "value3"
})

# Batch get
values = sdk.storage.get_multi(["key1", "key2", "key3"])

# Batch delete
sdk.storage.delete_multi(["key1", "key2", "key3"])
```

### SQL Chain Query

The Storage module provides a chain-style API general-purpose SQL query builder, supporting CRUD operations for custom tables.

> See [SQL Query Builder](../advanced/sql-builder.md) for complete documentation.

```python
from ErisPulse import sdk

# Create custom table
sdk.storage.CreateTable("users", {
    "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
    "name": "TEXT NOT NULL",
    "age": "INTEGER DEFAULT 0"
})

# Insert data
sdk.storage.Table("users").Insert({"name": "Alice", "age": 30}).Execute()

# Batch insert
sdk.storage.Table("users").InsertMulti([
    {"name": "Bob", "age": 25},
    {"name": "Charlie", "age": 35}
]).Execute()

# Query data
rows = (sdk.storage.Table("users")
    .Select("name", "age")
    .Where("age > ?", 18)
    .OrderBy("name")
    .Limit(10)
    .Execute())

# Update data
sdk.storage.Table("users").Update({"age": 31}).Where("name = ?", "Alice").Execute()

# Delete data
sdk.storage.Table("users").Delete().Where("name = ?", "Bob").Execute()

# Count
count = sdk.storage.Table("users").Where("age > ?", 18).Count()

# Existence check
exists = sdk.storage.Table("users").Where("name = ?", "Alice").Exists()

# Get single record
row = sdk.storage.Table("users").Select("name", "age").Where("name = ?", "Alice").ExecuteOne()

# Modify table structure
sdk.storage.AlterTable("users").AddColumn("email", "TEXT").Execute()
sdk.storage.AlterTable("users").RenameTo("members").Execute()

# Check if table exists
if sdk.storage.HasTable("users"):
    sdk.storage.DropTable("users")

# Chained operations in transaction
with sdk.storage.transaction():
    sdk.storage.Table("users").Insert({"name": "Dave", "age": 40}).Execute()
    sdk.storage.Table("users").Update({"age": 41}).Where("name = ?", "Dave").Execute()

# Reuse query conditions
base = sdk.storage.Table("users").Where("age > ?", 20)
rows = base.copy().Select("name").OrderBy("name").Limit(5).Execute()
count = base.copy().Count()
```

### Storage Backend Abstraction

The `StorageManager` inherits from the `BaseStorage` abstract base class, supporting future expansion to other storage media (Redis, MySQL, etc.).

```python
from ErisPulse.Core.Bases.storage import BaseStorage, BaseQueryBuilder

# BaseStorage defines the unified interface: get/set/delete/Table/CreateTable/DropTable, etc.
# BaseQueryBuilder defines the chained query interface: Select/Insert/Update/Delete/Where/OrderBy/Limit, etc.
```

## Config Module

### Reading Configuration

```python
from ErisPulse import sdk

# Get configuration
config = sdk.config.getConfig("MyModule", {})

# Get nested configuration
value = sdk.config.getConfig("MyModule.subkey.value", "default")
```

### Writing Configuration

```python
# Set configuration
sdk.config.setConfig("MyModule", {"key": "value"})

# Set nested configuration
sdk.config.setConfig("MyModule.subkey.value", "new_value")
```

### Configuration Example

```python
def _load_config(self):
    config = sdk.config.getConfig("MyModule")
    if not config:
        # Create default configuration
        default_config = {
            "api_url": "https://api.example.com",
            "timeout": 30,
            "cache_ttl": 3600
        }
        sdk.config.setConfig("MyModule", default_config, immediate=True)  # When the third parameter is True, save the configuration immediately, making it convenient for users to directly modify the configuration file
        return default_config
    return config
```

## Logger Module

### Basic Logging

```python
from ErisPulse import sdk

# Different log levels
sdk.logger.debug("Debug info")
sdk.logger.info("Runtime info")
sdk.logger.warning("Warning info")
sdk.logger.error("Error info")
sdk.logger.critical("Fatal error")
```

### Child Loggers

```python
# Get child logger
child_logger = sdk.logger.get_child("MyModule")
child_logger.info("Submodule log")

# Sub-modules can also have sub-module logs, allowing for more precise control of log output
child_logger.get_child("utils")
```

### Log Output

```python
# Set output file
sdk.logger.set_output_file("app.log")

# Save logs to file
sdk.logger.save_logs("log.txt")
```

## Adapter Module

### Getting Adapters

```python
from ErisPulse import sdk

# Get adapter instance
adapter = sdk.adapter.get("platform_name")

# Access via property
adapter = sdk.adapter.platform_name
```

### Adapter Events

```python
# Listen for standard events
@sdk.adapter.on("message")
async def handle_message(event):
    pass

# Listen for platform-specific events
@sdk.adapter.on("message", platform="yunhu")
async def handle_yunhu_message(event):
    pass

# Listen for platform native events
@sdk.adapter.on("raw_event", raw=True, platform="yunhu")
async def handle_raw_event(data):
    pass
```

### Adapter Management

```python
# Get all platforms
platforms = sdk.adapter.platforms

# Check if adapter exists
exists = sdk.adapter.exists("platform_name")

# Enable/disable adapter
sdk.adapter.enable("platform_name")
sdk.adapter.disable("platform_name")

# Start/shutdown adapter
await sdk.adapter.startup(["platform1", "platform2"])
await sdk.adapter.shutdown(["platform1", "platform2"])

# Check if adapter is running
is_running = sdk.adapter.is_running("platform_name")

# List all running adapters
running = sdk.adapter.list_running()
```

## Module Module

### Getting Modules

```python
from ErisPulse import sdk

# Get module instance
module = sdk.module.get("ModuleName")

# Access via property
module = sdk.module.ModuleName
module = sdk.ModuleName
```

### Module Management

```python
# Check if module exists
exists = sdk.module.exists("ModuleName")

# Check if module is loaded
is_loaded = sdk.module.is_loaded("ModuleName")

# Check if module is enabled
is_enabled = sdk.module.is_enabled("ModuleName")

# Enable/disable module
sdk.module.enable("ModuleName")
sdk.module.disable("ModuleName")

# Load module
await sdk.module.load("ModuleName")

# Unload module
await sdk.module.unload("ModuleName")

# List loaded modules
loaded = sdk.module.list_loaded()

# List registered modules
registered = sdk.module.list_registered()

# Get module info
info = sdk.module.get_info("ModuleName")

# Get module status summary
summary = sdk.module.get_status_summary()
# {"modules": {"ModuleName": {"status": "loaded", "enabled": True, "is_base_module": True}}}

# Check if module is running (equivalent to is_loaded)
is_running = sdk.module.is_running("ModuleName")

# List all running modules
running = sdk.module.list_running()
```

## Lifecycle Module

### Event Submission

```python
from ErisPulse import sdk

# Submit custom event
await sdk.lifecycle.submit_event(
    "custom.event",
    data={"key": "value"},
    source="MyModule",
    msg="Custom event description"
)
```

### Event Listening

```python
# Listen for specific event
@sdk.lifecycle.on("module.init")
async def handle_module_init(event_data):
    print(f"Module initialized: {event_data}")

# Listen for parent event
@sdk.lifecycle.on("module")
async def handle_any_module_event(event_data):
    print(f"Module event: {event_data}")

# Listen for all events
@sdk.lifecycle.on("*")
async def handle_any_event(event_data):
    print(f"System event: {event_data}")
```

### Timers

```python
# Start timer
sdk.lifecycle.start_timer("my_operation")

# ... perform operation ...

# Get duration
duration = sdk.lifecycle.get_duration("my_operation")

# Stop timer
total_time = sdk.lifecycle.stop_timer("my_operation")
```

## Router Module

### Abstract Types

Router supports two type annotation styles:

```python
# ErisPulse abstract types (recommended, portable)
from ErisPulse.Core import HttpRequest, WebSocketConnection

@sdk.router.get("MyModule", "/api")
async def handler(request: HttpRequest):
    data = await request.json()
    return {"status": "ok"}

# FastAPI native types (compatibility with existing code)
from fastapi import Request, WebSocket

@sdk.router.get("MyModule", "/api2")
async def handler(request: Request):
    return {"status": "ok"}
```

> The routing system automatically injects objects of the corresponding type based on parameter annotations. See [Router Manager](../advanced/router.md) for details.

### Decorator Routing (Recommended)

```python
from ErisPulse import sdk
from fastapi import Request

# HTTP route decorator
@sdk.router.http("MyModule", "/api", methods=["GET", "POST"])
async def api_handler(request: Request):
    return {"status": "ok"}

# Shortcut method decorators
@sdk.router.get("MyModule", "/info")
async def get_info(request: Request):
    return {"module": "MyModule"}

@sdk.router.post("MyModule", "/data")
async def post_data(request: Request):
    data = await request.json()
    return {"received": data}

@sdk.router.put("MyModule", "/data/{item_id}")
async def put_data(request: Request):
    return {"updated": True}

@sdk.router.delete("MyModule", "/data/{item_id}")
async def delete_data(request: Request):
    return {"deleted": True}

# WebSocket decorator
from fastapi import WebSocket

@sdk.router.ws("MyModule", "/ws")
async def websocket_handler(websocket: WebSocket):
    while True:
        data = await websocket.receive_text()
        await websocket.send_text(f"Echo: {data}")

# Authenticated WebSocket decorator
async def ws_auth(websocket: WebSocket) -> bool:
    token = websocket.query_params.get("token")
    return token == "secret"

@sdk.router.ws("MyModule", "/secure_ws", auth_handler=ws_auth)
async def secure_ws_handler(websocket: WebSocket):
    while True:
        data = await websocket.receive_text()
        await websocket.send_text(f"Echo: {data}")
```

### Traditional Registration

```python
from ErisPulse import sdk
from fastapi import Request

async def handler(request: Request):
    data = await request.json()
    return {"status": "ok", "data": data}

sdk.router.register_http_route(
    module_name="MyModule",
    path="/api",
    handler=handler,
    methods=["POST"],
    rate_limit="10/minute",
    summary="Data interface",
    tags=["API"],
)

sdk.router.unregister_http_route("MyModule", "/api")
```

### WebSocket Routes

```python
from ErisPulse import sdk
from fastapi import WebSocket

async def websocket_handler(websocket: WebSocket):
    while True:
        data = await websocket.receive_text()
        await websocket.send_text(f"Echo: {data}")

# Basic registration (auto-accepts connection)
sdk.router.register_websocket(
    module_name="my_module",
    path="/ws",
    handler=websocket_handler,
)

# Authenticated registration (Recommended: use auth_handler to control connections)
async def auth_handler(websocket: WebSocket) -> bool:
    token = websocket.query_params.get("token")
    return token == "secret"

sdk.router.register_websocket(
    module_name="my_module",
    path="/secure_ws",
    handler=websocket_handler,
    auth_handler=auth_handler,
)

# Unregister route
sdk.router.unregister_websocket("MyModule", "/ws")
```

**Parameter Description:**

| Parameter | Description | Default |
|------|------|--------|
| `module_name` | Module name (required) | - |
| `path` | WebSocket path | - |
| `handler` | Handler function | - |
| `auth_handler` | Authentication function, returning `False` will automatically close the connection | `None` |
| `auto_accept` | Whether to automatically `accept()` | `True` |

> **Recommended**: Use `auth_handler` for connection confirmation instead of disabling `auto_accept`. Only set `auto_accept=False` when you need full control over the connection process.

### Route Grouping

```python
# Create route group
group = sdk.router.group("MyModule", prefix="/v1")

# Register routes within the group
@group.get("/users")
async def list_users(request: Request):
    return {"users": []}

@group.post("/users")
async def create_user(request: Request):
    return {"created": True}

# Versioned group
v2 = sdk.router.group("MyModule", prefix="/v2", version="2")
```

### Route Middleware

```python
# Global middleware (glob matching)
@sdk.router.middleware("/MyModule/*")
async def auth_middleware(request: Request, call_next):
    token = request.headers.get("Authorization")
    if not token:
        return {"error": "Unauthorized"}
    response = await call_next(request)
    return response

# Specific path middleware
@sdk.router.middleware("/MyModule/admin/*")
async def admin_middleware(request: Request, call_next):
    return await call_next(request)
```

### Rate Limiting

```python
# Set rate limit for route (sliding window)
@sdk.router.get("MyModule", "/limited", rate_limit="10/minute")
async def limited_endpoint(request: Request):
    return {"ok": True}

@sdk.router.post("MyModule", "/submit", rate_limit="5/minute")
async def submit_data(request: Request):
    return {"submitted": True}
```

### CORS Configuration

```python
# Code method
sdk.router.setup_cors(
    allow_origins=["https://example.com"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Configuration file method (config.toml)
# [router.cors]
# allow_origins = ["https://example.com"]
# allow_methods = ["GET", "POST"]
# allow_headers = ["*"]
```

### Security Headers

```python
# Automatically add security response headers
sdk.router.setup_security_headers()

# Configuration file method (config.toml)
# [router.security]
# enabled = true
```

### Auto Documentation

```python
# Router has OpenAPI documentation enabled by default
# Disable docs
sdk.router.disable_docs()

# Customize documentation info
sdk.router.set_docs_info(
    title="My API",
    description="API documentation",
    version="1.0.0"
)
```

### Route Information

```python
app = sdk.router.get_app()
```

## HTTP Client Module

### Basic Requests

```python
from ErisPulse.Core import client

# GET request
resp = await client.get("https://api.example.com/users")
data = await resp.json()

# POST request
resp = await client.post(
    "https://api.example.com/users",
    json={"name": "Alice", "age": 30},
)

# PUT / DELETE / PATCH
resp = await client.put("https://api.example.com/users/1", json={"name": "Bob"})
resp = await client.delete("https://api.example.com/users/1")
resp = await client.patch("https://api.example.com/users/1", json={"age": 31})

# Generic request method
resp = await client.request("OPTIONS", "https://api.example.com/resource")
```

### Response Object

```python
from ErisPulse.Core import client

resp = await client.get("https://api.example.com/users")

resp.status        # int - HTTP status code (e.g. 200, 404)
resp.reason        # str | None - Reason phrase (e.g. "OK")
resp.headers       # Response headers (case-insensitive)
resp.content_type  # str | None - Content-Type
resp.url           # Final URL (may change due to redirects)
resp.raw           # Underlying native response object (currently aiohttp.ClientResponse)

# Read response body
body = await resp.read()       # bytes
text = await resp.text()       # str
data = await resp.json()       # Parse JSON
text = await resp.text("gbk")  # Specify encoding
```

### Request Parameters

| Parameter | Type | Description |
|------|------|------|
| `url` | `str` | Request URL |
| `params` | `dict[str, str]` | Query parameters (optional) |
| `headers` | `dict[str, str]` | Extra request headers (optional) |
| `data` | `Any` | Request body (form or raw data) (optional) |
| `json` | `Any` | JSON request body (optional) |
| `timeout` | `float` | Request timeout in seconds (optional, overrides default) |
| `max_retries` | `int` | Maximum number of retries for this request (optional, overrides default) |

### Custom Client

```python
from ErisPulse.Core import HttpClient

# Create a custom client (non-global singleton)
client = HttpClient(
    timeout=60,
    connect_timeout=5,
    max_retries=3,
    retry_delay=2,
    headers={"Authorization": "Bearer token"},
    user_agent="MyBot/1.0",
)

# Context manager for automatic session closing
async with HttpClient(timeout=30) as client:
    resp = await client.get("https://httpbin.org/get")
```

### Request Statistics

```python
from ErisPulse.Core import client

# View stats
stats = client.stats
# {"total_requests": 42, "total_errors": 1, "total_bytes_sent": 0, "total_bytes_received": 0}

# Reset stats
client.reset_stats()
```

### Lifecycle Events

```python
from ErisPulse.Core import lifecycle

@lifecycle.on("client.request")
async def on_request(event_data):
    print(f"{event_data['method']} {event_data['url']} -> {event_data['status']} ({event_data['elapsed']}s)")
```

## Related Documentation

- [Event System API](event-system.md) - Event Module API
- [Adapter System API](adapter-system.md) - Adapter Management API
- [HTTP Client](../advanced/http-client.md) - HTTP Client full documentation
- [Router Manager](../advanced/router.md) - Router Manager full documentation