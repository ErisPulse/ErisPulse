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

### Configuration Auditing

Config module has built-in caller-aware and auditing functionality to track read/write sources of configurations:

```python
# Enable auditing (disabled by default)
sdk.config.enable_audit(True)

# Listen for configuration changes
@sdk.config.on_change("MyModule")
def on_config_change(key, old_value, new_value, caller):
    print(f"Configuration changed: {key}")
    print(f"  Old value: {old_value} -> New value: {new_value}")
    print(f"  Caller: {caller.file}:{caller.lineno} ({caller.function})")

# Get audit logs
log = sdk.config.get_audit_log(limit=10)
for entry in log:
    print(f"[{entry.timestamp}] {entry.operation} {entry.key} by {entry.caller.function}")

# Disable auditing
sdk.config.enable_audit(False)
```

Audit logs contain:
- `operation`: Operation type (`get` / `set`)
- `key`: Configuration key path
- `caller`: Caller information (file name, line number, function name, module name)
- `timestamp`: Operation timestamp

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

# Submodules can have their own child loggers, allowing for more precise control over log output
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

# Access via attribute
adapter = sdk.adapter.platform_name
```

### Adapter Events

```python
# Listen for standard events
@sdk.adapter.on("message")
async def handle_message(event):
    pass

# Listen for events on a specific platform
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

# Enable/Disable adapter
sdk.adapter.enable("platform_name")
sdk.adapter.disable("platform_name")

# Start/Shutdown adapter
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

# Access via attribute
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

# Enable/Disable module
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

# Get module information
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
    print(f"Module initialization: {event_data}")

# Listen for parent event
@sdk.lifecycle.on("module")
async def handle_any_module_event(event_data):
    print(f"Module event: {event_data}")

# Listen for all events
@sdk.lifecycle.on("*")
async def handle_any_event(event_data):
    print(f"System event: {event_data}")
```

### Timer

```python
# Start timer
sdk.lifecycle.start_timer("my_operation")

# ... Perform operations ...

# Get duration
duration = sdk.lifecycle.get_duration("my_operation")

# Stop timer
total_time = sdk.lifecycle.stop_timer("my_operation")
```

## Metrics Module

### Basic Usage

```python
from ErisPulse import sdk

# Register built-in metrics (HTTP requests count, module loading time, etc.)
sdk.metrics.register_builtin_metrics()

# Get all metrics snapshot
snapshot = sdk.metrics.get_all_metrics()
```

### Metric Types

#### Counter

```python
from ErisPulse.Core.metrics import Counter

counter = Counter("http_requests_total", description="Total HTTP requests")
counter.inc()            # +1
counter.inc(5)           # +5
print(counter.value)     # 6
```

#### Gauge

```python
from ErisPulse.Core.metrics import Gauge

gauge = Gauge("active_connections", description="Active connections count")
gauge.inc()              # +1
gauge.dec()              # -1
gauge.set(42)            # Set to 42
print(gauge.value)       # 42
```

#### Histogram

```python
from ErisPulse.Core.metrics import Histogram

hist = Histogram("request_duration_seconds", description="Request duration")
hist.observe(0.15)
hist.observe(0.32)
hist.observe(1.2)
print(hist.count)        # 3
print(hist.sum)          # 1.67
print(hist.percentile(50))  # P50
print(hist.percentile(95))  # P95
print(hist.percentile(99))  # P99
```

### Custom Metrics

```python
from ErisPulse import sdk

# Register custom metrics via MetricsManager
sdk.metrics.counter("my_module.errors", description="Module error count")
sdk.metrics.gauge("my_module.queue_size", description="Queue size")
sdk.metrics.histogram("my_module.process_time", description="Processing time")

# Get and use
sdk.metrics.get("my_module.errors").inc()
```

### @timed Decorator

```python
from ErisPulse.Core.metrics import timed

@timed("my_module.handler_duration")
async def handle_request():
    # Function execution time will be automatically recorded to Histogram metric
    await do_something()
```

## Router Module

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
    summary="Data API",
    tags=["API"],
)

sdk.router.unregister_http_route("MyModule", "/api")
```

### WebSocket Routing

```python
from ErisPulse import sdk
from fastapi import WebSocket

async def websocket_handler(websocket: WebSocket):
    while True:
        data = await websocket.receive_text()
        await websocket.send_text(f"Echo: {data}")

# Basic registration (auto accepts connection)
sdk.router.register_websocket(
    module_name="my_module",
    path="/ws",
    handler=websocket_handler,
)

# Authenticated registration (recommended: use auth_handler to control connection)
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

| Parameter | Description | Default Value |
|----------|-------------|--------------|
| `module_name` | Module name (required) | - |
| `path` | WebSocket path | - |
| `handler` | Handler function | - |
| `auth_handler` | Auth function, returns `False` to auto-close connection | `None` |
| `auto_accept` | Whether to auto `accept()` | `True` |

> **Recommendation**: Use `auth_handler` for connection confirmation rather than disabling `auto_accept`. Only set `auto_accept=False` when you need full control over the connection process.

### Route Grouping

```python
# Create route group
group = sdk.router.group("MyModule", prefix="/v1")

# Register routes in group
@group.get("/users")
async def list_users(request: Request):
    return {"users": []}

@group.post("/users")
async def create_user(request: Request):
    return {"created": True}

# Versioned grouping
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
# Programmatic way
sdk.router.setup_cors(
    allow_origins=["https://example.com"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Configuration file way (config.toml)
# [router.cors]
# allow_origins = ["https://example.com"]
# allow_methods = ["GET", "POST"]
# allow_headers = ["*"]
```

### Security Headers

```python
# Automatically add security response headers
sdk.router.setup_security_headers()

# Configuration file way (config.toml)
# [router.security]
# enabled = true
```

### Auto Documentation

```python
# Router enables OpenAPI documentation by default
# Disable documentation
sdk.router.disable_docs()

# Custom documentation info
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

## Related Documentation

- [Event System API](event-system.md) - Event module API
- [Adapter System API](adapter-system.md) - Adapter management API