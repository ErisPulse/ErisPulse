# Core Modules API

This document provides a quick reference for the ErisPulse core modules' APIs, including method signatures and brief descriptions. For detailed usage and examples, please click the "Full Documentation" link for each module.

### Overview
**MurmurHash**: <a href="docs/en/murmurhash.md">Full Documentation</a>
**Pkg**: <a href="docs/en/pkg.md">Full Documentation</a>
**Pz**: <a href="docs/en/pz.md">Full Documentation</a>

### MurmurHash
The **MurmurHash** module provides a custom implementation of MurmurHash3. It supports 32-bit and 128-bit hashing. This implementation is optimized for hashing large amounts of data.

#### Public API

```go
package murmurhash

// Hash32 computes the 32-bit hash of the input data.
func Hash32(data []byte) uint32
```

#### Examples

```go
package main

import (
	"fmt"
	"erispulse/docs/en/murmurhash"
)

func main() {
	data := []byte("ErisPulse")
	hash := murmurhash.Hash32(data)
	fmt.Printf("Hash: %d\n", hash)
}
```

---

### Pkg
**Pkg** is a utility module designed to manage and retrieve package information. It helps developers handle dependencies and versioning logic.

#### Public API

```go
package pkg

// GetVersion returns the current version of the application.
func GetVersion() string
```

#### Examples

```go
package main

import (
	"fmt"
	"erispulse/docs/en/pkg"
)

func main() {
	version := pkg.GetVersion()
	fmt.Printf("Application Version: %s\n", version)
}
```

---

### Pz
**Pz** is a specialized module for defining and executing standard project templates. It provides a flexible framework to scaffold projects based on pre-configured structures.

#### Public API

```go
package pz

// Init initializes the project scaffolding process.
// projectPath: The root directory path for the project.
// templateName: The name of the template to use.
func Init(projectPath string, templateName string) error
```

#### Examples

```go
package main

import (
	"fmt"
	"erispulse/docs/en/pz"
)

func main() {
	path := "/my/new/project"
	template := "web-app"
	err := pz.Init(path, template)
	if err != nil {
		fmt.Printf("Failed to initialize project: %v\n", err)
	} else {
		fmt.Println("Project initialized successfully.")
	}
}
```

---

### API Summary

| Module | Status | Description |
| :--- | :--- | :--- |
| **MurmurHash** | ✅ Stable | Fast hashing algorithm implementation. |
| **Pkg** | ✅ Stable | Dependency and version management utilities. |
| **Pz** | ✅ Stable | Project scaffolding and template engine. |

---

## Storage Module

A key-value storage system based on SQLite, supporting general SQL chained queries.

### Basic Operations

```python
from ErisPulse import sdk

sdk.storage.set("key", "value")
value = sdk.storage.get("key", default_value)
keys = sdk.storage.keys()
sdk.storage.delete("key")
```

### Batch Operations

```python
sdk.storage.set_multi({"key1": "val1", "key2": "val2"})
values = sdk.storage.get_multi(["key1", "key2"])
sdk.storage.delete_multi(["key1", "key2"])
```

### Transaction Operations

```python
with sdk.storage.transaction():
    sdk.storage.set("key1", "value1")
    sdk.storage.set("key2", "value2")
```

### Attribute Access

```python
sdk.storage.my_key          # equivalent to sdk.storage.get("my_key")
sdk.storage.my_key = "val"  # equivalent to sdk.storage.set("my_key", "val")
```

### SQL Chained Queries

The Storage module provides a generic SQL query builder in chained call style, supporting CRUD operations on custom tables.

```python
sdk.storage.CreateTable("users", {
    "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
    "name": "TEXT NOT NULL",
})

sdk.storage.Table("users").Insert({"name": "Alice"}).Execute()
rows = sdk.storage.Table("users").Select("name").Where("id > ?", 0).Execute()
```

> For the complete chained query API (Select/Insert/Update/Delete/Where/OrderBy/Limit, AlterTable, transactions, etc.), please refer to [SQL Query Builder](../advanced/sql-builder.md).

### Storage Backend Abstraction

`StorageManager` inherits from the `BaseStorage` abstract base class, supporting extension to other storage mediums (Redis, MySQL, etc.).

```python
from ErisPulse.Core.Bases.storage import BaseStorage, BaseQueryBuilder
```

### Async Interfaces

Both the Storage and Config modules provide async methods (prefix `a`), which can be safely called in async handlers. Sync methods continue to be retained, requiring no modification to existing code.

```python
# Async Storage
value = await sdk.storage.aget("key")
await sdk.storage.aset("key", "value")
await sdk.storage.adelete("key")
keys = await sdk.storage.aget_all_keys()
await sdk.storage.aclear()

# Async Batch Operations
values = await sdk.storage.aget_multi(["k1", "k2"])
await sdk.storage.aset_multi({"k1": "v1", "k2": "v2"})
await sdk.storage.adelete_multi(["k1", "k2"])

# Async Config
value = await sdk.config.agetConfig("MyModule.key")
await sdk.config.asetConfig("MyModule.key", "value")
await sdk.config.aforce_save()
await sdk.config.areload()

## Config Module

TOML format configuration file management, supporting dot-separated key paths.

### API Overview

| Method | Description |
|------|------|
| `getConfig(key, default)` | Read configuration, supports dot path like `"MyModule.subkey"` |
| `setConfig(key, value, immediate=False)` | Write configuration. `immediate=True` saves to file immediately |
| `force_save()` | Force write configuration in memory to file |
| `reload()` | Reload configuration from file |
| `agetConfig(key, default)` | Asynchronously read configuration |
| `asetConfig(key, value, immediate)` | Asynchronously write configuration |
| `aforce_save()` | Asynchronously force save |
| `areload()` | Asynchronously reload |

### Example

```python
config = sdk.config.getConfig("MyModule", {})
value = sdk.config.getConfig("MyModule.timeout", 30)

sdk.config.setConfig("MyModule", {"key": "value"})
sdk.config.setConfig("MyModule.timeout", 60, immediate=True)
```

> `setConfig` uses lazy write (saves in batch every 5 seconds) by default. Setting `immediate=True` can persist to the config file immediately. Configuration changes trigger the `config.set` lifecycle event.

## Logger Module

A modular logging system based on Rich output, supporting child loggers and module-level control.

### Basic Usage

```python
sdk.logger.debug("debug message")
sdk.logger.info("runtime information")
sdk.logger.warning("warning message")
sdk.logger.error("error message")
sdk.logger.critical("fatal error")
```

### Child Loggers

```python
child_logger = sdk.logger.get_child("MyModule")
child_logger.info("child module log")

child_logger.get_child("utils")  # Nested child loggers are supported
```

### Log Level Control

```python
sdk.logger.set_level("DEBUG")                          # Global level
sdk.logger.set_module_level("MyModule", "DEBUG")       # Module level

# Supported levels (from lowest to highest):
# TRACE, DEBUG, INFO, WARNING, ERROR, CRITICAL
# TRACE is the lowest level; it outputs framework-internal detailed debugging information (event dispatching, routing registration, etc.)
sdk.logger.set_level("TRACE")                          # Enable all logs
```

### Log Subscription (Push Mode)

Provides a way for modules such as Dashboard to receive structured logs in real-time, supporting level filtering and historical log replay.

> **Explicit Subscription for Low-Level Logs**: The `min_level` of the subscriber can be lower than the global log level. In this case, low-level logs are **pushed only to matching subscribers**, and will not be output to the console or written to memory, thereby avoiding pollution of the main log stream.
>
> ```python
> # Global level is INFO, but DEBUG logs can still be subscribed separately
> @sdk.logger.handler("debug-tracer", min_level="DEBUG")
> def on_debug(log_data: dict): ...
> ```

```python
# Decorator style
@sdk.logger.handler("my-handler", min_level="INFO")
def on_log(log_data: dict):
    # log_data = {
    #     "timestamp": "2026-06-29T22:00:00.123456",
    #     "level": "WARNING", "level_num": 30,
    #     "module": "ErisPulse.Core.adapter",
    #     "message": "Strict mode: ...",
    # }
    pass

# Direct call style
sdk.logger.handler("my-handler", min_level="INFO")(on_log)
sdk.logger.remove_handler("my-handler")
```

| Method | Description |
|--------|-------------|
| `handler(id, *, min_level)(func)` | Decorator or direct call. `id` is empty, uses function name. `min_level` can be lower than global level (low-level logs are only pushed to subscribers, not console/memory). Registers and replays historical logs automatically. |
| `remove_handler(id)` | Removes a subscriber. |

### Output Control

```python
sdk.logger.set_output_file("app.log")
sdk.logger.save_logs("log.txt")
sdk.logger.get_logs("MyModule")
sdk.logger.set_memory_limit(1000)

## Adapter Module

The adapter manager manages the registration, startup, and shutdown of multi-platform adapters.

### API Overview

| Method | Description |
|------|------|
| `get(platform)` | Get adapter instance |
| `exists(platform)` | Check if adapter is registered |
| `enable(platform)` / `disable(platform)` | Enable/disable adapter |
| `is_enabled(platform)` | Check if enabled |
| `startup(platforms)` / `shutdown(platforms)` | Start/stop adapter |
| `is_running(platform)` | Check if adapter is running |
| `list_running()` | List all running adapters |
| `platforms` | Get list of all platform names |

### Adapter Events

```python
@sdk.adapter.on("message")
async def handle_message(event):
    pass

@sdk.adapter.on("message", platform="yunhu")
async def handle_yunhu_message(event):
    pass
```

### Bot Status Query

```python
sdk.adapter.get_bot_info("telegram", "123456")
sdk.adapter.list_bots("telegram")
sdk.adapter.is_bot_online("telegram", "123456")
sdk.adapter.get_status_summary()
```

> For the complete adapter management API, please refer to [Adapter System API](adapter-system.md).

## Module

The module manager manages the registration, loading, and unloading of plugins.

### API Overview

| Method | Description |
|--------|-------------|
| `get(name)` | Get module instance or lazy load proxy (returns proxy if registered but not yet loaded) |
| `exists(name)` | Check if already registered |
| `is_loaded(name)` | Check if already loaded |
| `is_enabled(name)` | Check if enabled |
| `enable(name)` / `disable(name)` | Enable/disable module |
| `load(name)` / `unload(name)` | Load/unload module |
| `list_registered()` | List registered modules |
| `list_loaded()` | List loaded modules |
| `get_info(name)` | Get module info |
| `get_status_summary()` | Get module status summary |

### Property Access

```python
module = sdk.module.get("ModuleName")
module = sdk.module.ModuleName
module = sdk.ModuleName  # Equivalent shortcut

## Lifecycle Module

An event-driven lifecycle manager that provides event emission and listening capabilities.

### API Overview

| Method | Description |
|------|------|
| `on(event, priority=0)` | Decorator to register event handlers, supporting dot notation matching and wildcards `*` |
| `register(event, handler, priority=0)` | Functional registration of handlers |
| `unregister(event, handler=None)` | Remove handlers |
| `emit(event, data)` | Asynchronously trigger an event |
| `emit_sync(event, data)` | Synchronously trigger an event |
| `submit_event(event_type, msg, data, source)` | Submit a standard format event (legacy compatible) |
| `start_timer(id)` / `stop_timer(id)` | Performance timers |

### Example

```python
@sdk.lifecycle.on("module.init")
async def handle_module_init(event_data):
    print(f"模块初始化: {event_data}")

@sdk.lifecycle.on("module")
async def handle_any_module_event(event_data):
    print(f"模块事件: {event_data}")

await sdk.lifecycle.emit("custom.event", {"key": "value"})
```

> For a complete list of standard events and detailed usage, please refer to [Lifecycle Management](../advanced/lifecycle.md).

## Router Module

HTTP/WebSocket router manager, based on FastAPI + Uvicorn, supports decorator routing, middleware, grouping, rate limiting, and CORS.

> For the complete router API documentation (decorator routing, WebSocket, middleware, rate limiting, CORS, security headers, etc.), please refer to [Router Manager](../advanced/router.md).

### Quick Reference

```python
# HTTP route
@sdk.router.get("MyModule", "/api")
async def handler(request: HttpRequest):
    return {"status": "ok"}

# WebSocket route
@sdk.router.ws("MyModule", "/ws")
async def ws_handler(ws: WebSocketConnection):
    async for text in ws.iter_text():
        await ws.send_text(f"Echo: {text}")

# Route grouping
group = sdk.router.group("MyModule", prefix="/v1")
@group.get("/users")
async def list_users(request: HttpRequest):
    return {"users": []}

## HTTP Client Module

A unified network client that aggregates HTTP requests, WebSocket connections, connection pool management, automatic retry, request statistics, and lifecycle event integration.

> For complete network client documentation (request methods, response objects, WebSocket client, exception hierarchy, etc.), please refer to [Network Client](../advanced/http-client.md).

### Quick Reference

```python
from ErisPulse.Core import client

# HTTP request
resp = await client.get("https://api.example.com/users")
data = await resp.json()

# WebSocket
ws = await client.ws_connect("wss://example.com/ws")
async for text in ws.iter_text():
    await ws.send_text(f"Echo: {text}")

## SDK Debugging

### dump_state()

Exports a snapshot of the framework's current runtime state, used for debugging and diagnostics.

```python
import json
state = sdk.dump_state()
print(json.dumps(state, indent=2, ensure_ascii=False, default=str))
```

The returned structure contains the status of the following subsystems:

| Field | Description |
|------|------|
| `sdk` | SDK initialization status, Python version, runtime platform, timestamp |
| `adapters` | List of registered/started adapters, online status of bots on each platform |
| `modules` | List of registered/enabled/disabled/lazy-loaded modules |
| `events` | Count of various event handlers (message/notice/request/meta/commands) |
| `router` | Server runtime status, number of HTTP/WebSocket routes |

> Added in 2.5.2

## Related Documentation

- [Event System API](event-system.md) - Event module API
- [Adapter System API](adapter-system.md) - Adapter management API
- [SQL Query Builder](../advanced/sql-builder.md) - Complete documentation for SQL chain queries
- [Router Manager](../advanced/router.md) - Complete documentation for the router manager
- [HTTP Client](../advanced/http-client.md) - Complete documentation for the HTTP client
- [Lifecycle Management](../advanced/lifecycle.md) - Complete documentation for lifecycle