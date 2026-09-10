# Core Module API

This document provides a quick reference of the ErisPulse core module APIs, including method signatures and brief descriptions. Click the "Full Documentation" link for each module to learn detailed usage and examples.

## Storage Module

A key-value storage system based on SQLite, supporting generic SQL chained queries.

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
sdk.storage.my_key          # Equivalent to sdk.storage.get("my_key")
sdk.storage.my_key = "val"  # Equivalent to sdk.storage.set("my_key", "val")
```

### SQL Chained Query

The Storage module provides a chained-call style generic SQL query builder, supporting CRUD operations for custom tables.

```python
sdk.storage.CreateTable("users", {
    "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
    "name": "TEXT NOT NULL",
})

sdk.storage.Table("users").Insert({"name": "Alice"}).Execute()
rows = sdk.storage.Table("users").Select("name").Where("id > ?", 0).Execute()
```

> For the full chained query API (Select/Insert/Update/Delete/Where/OrderBy/Limit, AlterTable, transactions, etc.), refer to [SQL Query Builder](../advanced/sql-builder.md).

### Storage Backend Abstraction

`StorageManager` inherits from the `BaseStorage` abstract base class, supporting extensions to other storage media (Redis, MySQL, etc.).

```python
from ErisPulse.Core.Bases.storage import BaseStorage, BaseQueryBuilder
```

### Asynchronous Interfaces

Both Storage and Config modules provide asynchronous methods (prefixed with `a`), which can be safely called in asynchronous handlers. Synchronous methods are retained, requiring no changes to existing code.

```python
# Asynchronous storage
value = await sdk.storage.aget("key")
await sdk.storage.aset("key", "value")
await sdk.storage.adelete("key")
keys = await sdk.storage.aget_all_keys()
await sdk.storage.aclear()

# Asynchronous batch operations
values = await sdk.storage.aget_multi(["k1", "k2"])
await sdk.storage.aset_multi({"k1": "v1", "k2": "v2"})
await sdk.storage.adelete_multi(["k1", "k2"])

# Asynchronous configuration
value = await sdk.config.agetConfig("MyModule.key")
await sdk.config.asetConfig("MyModule.key", "value")
await sdk.config.aforce_save()
await sdk.config.areload()
```

## Config Module

TOML-based configuration file management, supporting dot-separated key paths.

### API Overview

| Method | Description |
|------|------|
| `getConfig(key, default)` | Read configuration, supports dot paths like `"MyModule.subkey"` |
| `setConfig(key, value, immediate=False)` | Write configuration. If `immediate=True`, save immediately to file |
| `force_save()` | Force write in-memory configuration to file |
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

> `setConfig` uses delayed writing by default (batch saved every 5 seconds). Setting `immediate=True` forces immediate persistence to the configuration file. Configuration changes trigger the `config.set` lifecycle event.

## Logger Module

A modular logging system based on Rich output, supporting child loggers and module-level control.

### Basic Usage

```python
sdk.logger.debug("Debug message")
sdk.logger.info("Info message")
sdk.logger.warning("Warning message")
sdk.logger.error("Error message")
sdk.logger.critical("Critical error")
```

### Child Loggers

```python
child_logger = sdk.logger.get_child("MyModule")
child_logger.info("Child module log")

child_logger.get_child("utils")  # Supports nesting
```

### Log Level Control

```python
sdk.logger.set_level("DEBUG")                          # Global level
sdk.logger.set_module_level("MyModule", "DEBUG")       # Module level

# Supported levels (from lowest to highest):
# TRACE, DEBUG, INFO, WARNING, ERROR, CRITICAL
# TRACE is the lowest level, outputs detailed framework debug information (event dispatch, route registration, etc.)
sdk.logger.set_level("TRACE")                          # Enable all logs
```

### Log Subscription (Push Mode)

For modules like Dashboard to receive structured logs in real-time, supporting level filtering and historical replay.

> **Explicit subscription of low-level logs**: The `min_level` of a subscriber can be lower than the global log level. In this case, low-level logs are **only pushed to matching subscribers**, not output to console, nor written to memory, thus avoiding pollution of the main log stream.
>
> ```python
> # Global level is INFO, but can still subscribe to DEBUG logs
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
    #     "message": "Strict mode:...",
    # }
    pass

# Direct call style
sdk.logger.handler("my-handler", min_level="INFO")(on_log)
sdk.logger.remove_handler("my-handler")
```

| Method | Description |
|------|------|
| `handler(id, *, min_level)(func)` | Decorator/inline call dual-use. If `id` is empty, function name is used. `min_level` can be lower than global level (low-level logs are only pushed to subscribers, not to console/memory). History logs are automatically replayed upon registration |
| `remove_handler(id)` | Remove subscriber |

### Output Control

```python
sdk.logger.set_output_file("app.log")
sdk.logger.save_logs("log.txt")
sdk.logger.get_logs("MyModule")
sdk.logger.set_memory_limit(1000)
```

## Adapter Module

Adapter manager, managing registration, startup, and shutdown of multi-platform adapters.

### API Overview

| Method | Description |
|------|------|
| `get(platform)` | Get adapter instance |
| `exists(platform)` | Check if adapter is registered |
| `enable(platform)` / `disable(platform)` | Enable/disable adapter |
| `is_enabled(platform)` | Check if enabled |
| `startup(platforms)` / `shutdown(platforms)` | Start/stop adapters |
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

> For the full adapter management API, see [Adapter System API](adapter-system.md).

## Module Module

Module manager, managing plugin registration, loading, and unloading.

### API Overview

| Method | Description |
|------|------|
| `get(name)` | Get module instance or lazy-loaded proxy (returns proxy if registered but not loaded) |
| `exists(name)` | Check if registered |
| `is_loaded(name)` | Check if loaded |
| `is_enabled(name)` | Check if enabled |
| `enable(name)` / `disable(name)` | Enable/disable module |
| `load(name)` / `unload(name)` | Load/unload module |
| `call(module, method, *args, timeout=None, **kwargs)` | Cross-module call to target module's service method (protocolized RPC) |
| `list_registered()` | List registered modules |
| `list_loaded()` | List loaded modules |
| `get_info(name)` | Get module information |
| `get_status_summary()` | Get module status summary |

### Attribute Access

```python
module = sdk.module.get("ModuleName")
module = sdk.module.ModuleName
module = sdk.ModuleName  # Equivalent shortcut
```

### Inter-Module Call (RPC)

```python
# Protocolized call: typed errors / lazy module auto-wake / owner attribution / timeout semantics
result = await sdk.module.call("Chat", "get_history", session_id, n=20)
```

Difference between `module.call()` and direct service access `sdk.module.Chat.get_history(...)`:

| | `module.call()` | Direct attribute access |
|---|---|---|
| Target not registered/enabled | Throws `ModuleNotAvailableError` | Throws `AttributeError` |
| Lazy-loaded module | Auto-wakes | Async initialization of module throws RuntimeError |
| `current_owner` | Attributed to target module | Retains caller |
| Timeout | Default 30s, can be overridden | None |
| Scope audit | `actions.<caller>.call` | None |

### Service Contract (meta.services)

Service provider declares the public white list in the `services` field of `get_meta()` (symmetrical to `commands`). After declaration, the call surface is tightened:

```python
class ChatModule(BaseModule):
    @staticmethod
    def get_meta() -> ModuleMeta:
        return ModuleMeta(services=["get_history", "translate"])

    async def get_history(self, session_id, n=20): ...
```

- **Default = Developer-transparent**: If `services` is not declared, any **public** method can be called (backward compatibility), private methods with underscore are always prohibited; control of restrictions is mainly on the user-side scope configuration
- After declaration: Only methods in the whitelist are callable, calling outside throws `ServiceNotProvidedError`
- Caller restriction: `scope.set_action("CallerModule", "call", deny="Chat.get_history")`

**Service Description (description)**: `services` supports dict form to declare description for each service (supports plain string or i18n dict), for service directory / AI call point description consumption:

```python
return ModuleMeta(
    services=[
        "get_history",                              # Simple form: description automatically taken from first line of method docstring
        {"name": "translate", "description": "Translate text into specified language"},
        {"name": "summarize", "description": {"i18n": "Chat.meta.svc.summarize", "default": "Summarize conversation"}},
    ],
)
```

Description resolution priority: **Explicit description (i18n resolved to current language) > Method docstring first line > Empty string**.

### Service Directory (services)

```python
sdk.module.services()
# {'Chat': [{'name': 'get_history', 'signature': '(session_id, n=20)',
#            'description': 'Get session history'}]}

sdk.module.services("Chat")  # Query only specified module
```

Only lists modules that explicitly declare `meta.services`. Each service includes method signature string and description text, providing data foundation for MCP (exposing call points to AI).

> Directed event delivery belongs to the lifecycle layer: `lifecycle.emit(event, data, to="ModuleName")`, see [Inter-Module Communication](../advanced/module-communication.md).

## Lifecycle Module

Event-driven lifecycle manager, providing event submission and listening functionality.

### API Overview

| Method | Description |
|------|------|
| `on(event, priority=0)` | Decorator to register event handler, supports dot matching and wildcard `*` |
| `register(event, handler, priority=0)` | Functional registration of handler |
| `unregister(event, handler=None)` | Remove handler |
| `emit(event, data, to=None)` | Asynchronously trigger event; if `to` specifies owner, event is directed |
| `emit_sync(event, data, to=None)` | Synchronously trigger event (asynchronous handlers are scheduled with create_task) |
| `submit_event(event_type, msg, data, source, to=None)` | Submit standard format event (compatible with old version) |
| `start_timer(id)` / `stop_timer(id)` | Performance timer |

### Example

```python
@sdk.lifecycle.on("module.init")
async def handle_module_init(event_data):
    print(f"Module initialized: {event_data}")

@sdk.lifecycle.on("module")
async def handle_any_module_event(event_data):
    print(f"Module event: {event_data}")

await sdk.lifecycle.emit("custom.event", {"key": "value"})

# Directed delivery: only distributed to hooks registered by Chat module
await sdk.lifecycle.emit("message_received", {"text": "hi"}, to="Chat")
```

> For the complete list of standard events and detailed usage, see [Lifecycle Management](../advanced/lifecycle.md).

## Router Module

HTTP/WebSocket router manager, based on FastAPI + Uvicorn, supporting decorator routes, middleware, grouping, rate limiting, CORS.

> For the complete router API documentation (decorator routes, WebSocket, middleware, rate limiting, CORS, security headers, etc.), see [Router Manager](../advanced/router.md).

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
```

## HTTP Client Module

Unified network client, aggregating HTTP requests, WebSocket connections, connection pool management, automatic retries, request statistics, and lifecycle event integration.

> For the complete network client documentation (request methods, response objects, WebSocket client, exception system, etc.), see [Network Client](../advanced/http-client.md).

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
```

## SDK Debugging

### dump_state()

Exports a snapshot of the current running state of the framework, used for debugging and diagnosis.

```python
import json
state = sdk.dump_state()
print(json.dumps(state, indent=2, ensure_ascii=False, default=str))
```

The returned structure contains the status of the following subsystems:

| Field | Description |
|------|------|
| `sdk` | SDK initialization status, Python version, running platform, timestamp |
| `adapters` | List of registered/started adapters, online status of bots on each platform |
| `modules` | List of registered/enabled/disabled/lazy-loaded modules |
| `events` | Number of handlers for various event types (message/notice/request/meta/commands) |
| `router` | Server running status, number of HTTP/WebSocket routes |

> [!NOTE]
> Added in ErisPulse **2.5.2+**

## Interaction Session

Manages wait_reply suspension and session mutual exclusion leases (`sdk.interaction`).

### Common Methods

```python
# Session timeout reminder: Remind after 5 minutes of no reply, reminder is automatically canceled if user replies
reminder = event.remind(300, "Are you still there?")
reminder.cancel()  # Manually cancel

# Timeout escalation: Guaranteed delivery at a certain point (not canceled by reply)
event.escalate(1800, lambda e: notify_master("30 minutes not processed"))

# Multi-path waiting: First come, first served
which, reply = await event.select(
    event.expect(pattern="agree*", user="A"),
    event.expect(pattern="reject*", user="B"),
    timeout=60,
)

# Session-level waiting: Reply from anyone in the same group can match
reply = await event.wait_reply(session=True, prompt="Can someone help answer?")

# Query current session ownership (who is interacting with this user)
owner = sdk.interaction.get_owner_of(event)

# Declare session mutual exclusion lease (returns None if occupied)
lease = sdk.interaction.acquire(event)
if lease:
    try:
        ...  # Exclusive interaction
    finally:
        lease.release()

# Context manager form (throws SessionOccupiedError if occupied)
with sdk.interaction.hold(event) as lease:
    ...

# Session suspension statistics
sdk.interaction.counts()  # {'waits': 2, 'leases': 1, 'timers': 3, 'owners': {'Chat': 3}}
```

When modules are unloaded or adapters are shut down, their suspended waits and timers are automatically canceled (waiting parties immediately return `None`), and reply matches automatically recheck scope permissions (if user is blacklisted or module is unbound, waiting is terminated).

> [!NOTE]
> This section's capabilities were added in ErisPulse **2.8.0+**

## Transcript Session Inbox

Automatic recording and querying of recent message streams per session (`sdk.transcript`), serving as a public base for context memory modules like AI conversation and anti-repetition.

### Common Methods

```python
# Convenient query (recommended): Last 20 messages in current session (including user and bot, in ascending order)
messages = await event.history(20)
for m in messages:
    print(m["role"], ":", m["text"])

# Manager API
sdk.transcript.append(event, "user", "text")
sdk.transcript.get(event, n=20)
sdk.transcript.clear(event)
```

Configuration (`ErisPulse.transcript`): `enabled` (default enabled), `max_per_session` (default 50 per session limit), `ttl_hours` (default 168 hours global expiration). Data is stored in a separate SQLite table, with lazy cleanup for over-limit or expired entries.

> [!NOTE]
> This section's capabilities were added in ErisPulse **2.8.0+**

## Related Documentation

- [Event System API](event-system.md) - Event module API
- [Adapter System API](adapter-system.md) - Adapter management API
- [SQL Query Builder](../advanced/sql-builder.md) - Full documentation of SQL chained query
- [Router Manager](../advanced/router.md) - Full router manager documentation
- [Network Client](../advanced/http-client.md) - Full network client documentation
- [Lifecycle Management](../advanced/lifecycle.md) - Full lifecycle documentation