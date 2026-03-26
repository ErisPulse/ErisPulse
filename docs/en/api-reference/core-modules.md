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

# Delete value
sdk.storage.delete("key")

# Check if key exists
exists = sdk.storage.exists("key")
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
await sdk.adapter.shutdown()
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

## Router Module

### HTTP Routes

```python
from ErisPulse import sdk
from fastapi import Request

# Register HTTP route
async def handler(request: Request):
    data = await request.json()
    return {"status": "ok", "data": data}

sdk.router.register_http_route(
    module_name="MyModule",
    path="/api",
    handler=handler,
    methods=["POST"]
)

# Unregister route
sdk.router.unregister_http_route("MyModule", "/api")
```

### WebSocket Routes

```python
from ErisPulse import sdk
from fastapi import WebSocket

# Register WebSocket route (automatically accepts connection by default)
async def websocket_handler(websocket: WebSocket):
    # No manual accept needed by default, it is called internally automatically
    while True:
        data = await websocket.receive_text()
        await websocket.send_text(f"Echo: {data}")

sdk.router.register_websocket(
    module_name="my_module",
    path="/ws",
    handler=websocket_handler,
    auto_accept=True  # Default is True, can be omitted
)

# Register WebSocket route (manual connection control)
async def manual_websocket_handler(websocket: WebSocket):
    # Decide whether to accept connection based on condition
    if some_condition:
        await websocket.accept()
        # Handle connection...
    else:
        await websocket.close(code=1008, reason="Not allowed")

async def auth_handler(websocket: WebSocket) -> bool:
    token = websocket.query_params.get("token")
    if token == "<PASSWORD>":
        return True
    return False

sdk.router.register_websocket(
    module_name="my_module",
    path="/secure_ws",
    handler=manual_websocket_handler,
    auth_handler=auth_handler,
    auto_accept=False  # Manual connection control
)

# Unregister route
sdk.router.unregister_websocket("MyModule", "/ws")
```

**Parameter Description:**

- `module_name`: Module name
- `path`: WebSocket path
- `handler`: Handler function
- `auth_handler`: Optional authentication function
- `auto_accept`: Whether to automatically accept connection (default `True`)
  - `True`: Framework automatically calls `websocket.accept()`, handler does not need to call it manually
  - `False`: handler must call `websocket.accept()` or `websocket.close()` itself

### Route Information

```python
# Get FastAPI application instance
app = sdk.router.get_app()

# Add middleware
@app.middleware("http")
async def add_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Custom-Header"] = "value"
    return response
```

## Related Documents

- [Event System API](event-system.md) - Event Module API
- [Adapter System API](adapter-system.md) - Adapter Management API