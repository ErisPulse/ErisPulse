# Core Module API

This document provides a quick reference for the ErisPulse core module API, including method signatures and brief descriptions. Click the "Full Documentation" link for each module to view detailed usage and examples.

## Storage Module

A key-value storage system based on SQLite, supporting generic SQL chainable queries.

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

### SQL Chainable Queries

The Storage module provides a chainable query builder style for generic SQL queries, supporting CRUD operations on custom tables.

```python
sdk.storage.CreateTable("users", {
    "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
    "name": "TEXT NOT NULL",
})

sdk.storage.Table("users").Insert({"name": "Alice"}).Execute()
rows = sdk.storage.Table("users").Select("name").Where("id > ?", 0).Execute()
```

> For the complete chainable query API (Select/Insert/Update/Delete/Where/OrderBy/Limit, AlterTable, transactions, etc.), refer to [SQL Query Builder](../advanced/sql-builder.md).

### Storage Backend Abstraction

`StorageManager` inherits from the `BaseStorage` abstract base class, supporting extension to other storage mediums (Redis, MySQL, etc.).

```python
from ErisPulse.Core.Bases.storage import BaseStorage, BaseQueryBuilder
```

### Asynchronous Interfaces

The Storage and Config modules both provide asynchronous methods (prefixed with `a`), which can be safely called within asynchronous handlers. Synchronous methods are retained for backward compatibility, requiring no modifications to existing code.

```python
# Asynchronous Storage
value = await sdk.storage.aget("key")
await sdk.storage.aset("key", "value")
await sdk.storage.adelete("key")
keys = await sdk.storage.aget_all_keys()
await sdk.storage.aclear()

# Asynchronous Batch Operations
values = await sdk.storage.aget_multi(["k1", "k2"])
await sdk.storage.aset_multi({"k1": "v1", "k2": "v2"})
await sdk.storage.adelete_multi(["k1", "k2"])

# Asynchronous Configuration
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
| `getConfig(key, default)` | Retrieve configuration, supports dot paths like `"MyModule.subkey"` |
| `setConfig(key, value, immediate=False)` | Write configuration. If `immediate=True`, save immediately to file |
| `force_save()` | Force-write in-memory configuration to file |
| `reload()` | Reload configuration from file |
| `agetConfig(key, default)` | Asynchronously retrieve configuration |
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

> `setConfig` uses delayed write by default (batch save every 5 seconds). Setting `immediate=True` will immediately persist to the configuration file. Configuration changes trigger the `config.set` lifecycle event.

## Logger Module

A modular logging system based on Rich output, supporting sub-loggers and module-level control.

### Basic Usage

```python
sdk.logger.debug("Debug message")
sdk.logger.info("Info message")
sdk.logger.warning("Warning message")
sdk.logger.error("Error message")
sdk.logger.critical("Critical error")
```

### Sub-loggers

```python
child_logger = sdk.logger.get_child("MyModule")
child_logger.info("Submodule log")

child_logger.get_child("utils")  # Supports nesting
```

### Log Level Control

```python
sdk.logger.set_level("DEBUG")                          # Global level
sdk.logger.set_module_level("MyModule", "DEBUG")       # Module level

# Supported levels (from low to high):
# TRACE, DEBUG, INFO, WARNING, ERROR, CRITICAL
# TRACE is the lowest level, outputting detailed framework internal debug information (event dispatch, route registration, etc.)
sdk.logger.set_level("TRACE")                          # Enable all logs
```

### Log Subscription (Push Mode)

For modules like Dashboard to receive structured logs in real-time, supporting level filtering and historical replay.

> **Explicitly subscribe to lower-level logs**: The `min_level` of a subscriber can be lower than the global log level. In this case, low-level logs are **only pushed to matching subscribers**, not output to the console, nor written to memory, thus avoiding pollution of the main log stream.
>
> ```python
> # Global level is INFO, but you can still subscribe to DEBUG logs individually
> @sdk.logger.handler("debug-tracer", min_level="DEBUG")
> def on_debug(log_data: dict): ...
> ```

```python
# Decorator approach
@sdk.logger.handler("my-handler", min_level="INFO")
def on_log(log_data: dict):
    # log_data = {
    #     "timestamp": "2026-06-29T22:00:00.123456",
    #     "level": "WARNING", "level_num": 30,
    #     "module": "ErisPulse.Core.adapter",
    #     "message": "Strict mode:...",
    # }
    pass

# Direct call approach
sdk.logger.handler("my-handler", min_level="INFO")(on_log)
sdk.logger.remove_handler("my-handler")
```

| Method | Description |
|------|------|
| `handler(id, *, min_level)(func)` | Decorator/functional approach. If `id` is empty, the function name is used. `min_level` can be lower than the global level (low-level logs are only pushed to matching subscribers, not to console/memory). History logs are automatically replayed upon registration |
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
| `get(platform)` | Retrieve adapter instance |
| `exists(platform)` | Check if adapter is registered |
| `enable(platform)` / `disable(platform)` | Enable/disable adapter |
| `is_enabled(platform)` | Check if enabled |
| `startup(platforms)` / `shutdown(platforms)` | Start/stop adapter |
| `is_running(platform)` | Check if adapter is running |
| `list_running()` | List all running adapters |
| `platforms` | Retrieve list of all platform names |

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

> For the complete adapter management API, see [Adapter System API](adapter-system.md).

## Module Module

The module manager, responsible for registering, loading, and unloading plugins.

### API Overview

| Method | Description |
|--------|-------------|
| `get(name)` | Retrieve a module instance or a lazy-loading proxy (returns a proxy if the module is registered but not loaded) |
| `exists(name)` | Check if the module is registered |
| `is_loaded(name)` | Check if the module is loaded |
| `is_enabled(name)` | Check if the module is enabled |
| `enable(name)` / `disable(name)` | Enable/disable the module |
| `load(name)` / `unload(name)` | Load/unload the module |
| `call(module, method, *args, timeout=None, **kwargs)` | Call a service method in a target module across modules (protocolized RPC) |
| `emit_to(module, event, data)` | Deliver a lifecycle event to a specific module |
| `list_registered()` | List all registered modules |
| `list_loaded()` | List all loaded modules |
| `get_info(name)` | Retrieve module information |
| `get_status_summary()` | Get a status summary of modules |

### Attribute Access

```python
module = sdk.module.get("ModuleName")
module = sdk.module.ModuleName
module = sdk.ModuleName  # Equivalent shortcut
```

### Inter-Module Calls (RPC)

```python
# Protocolized call: typed errors / lazy module auto-wakeup / owner attribution / timeout semantics
result = await sdk.module.call("Chat", "get_history", session_id, n=20)
```

Differences between `module.call()` and direct service access `sdk.module.Chat.get_history(...)`:

| | `module.call()` | Direct attribute access |
|---|---|---|
| Target not registered/unavailable | Throws `ModuleNotAvailableError` | Throws `AttributeError` |
| Lazy-loaded module | Automatically wakes up | Async initialization throws `RuntimeError` |
| `current_owner` | Attributed to the target module | Retains the caller's context |
| Timeout | Default 30s, can be overridden | None |
| Scope audit | `actions.<caller>.call` | None |

### Service Contract (`meta.services`)

Service providers declare a white-list of exposed services in the `services` field of `get_meta()`, symmetric to `commands`. After declaration, the call surface is restricted:

```python
class ChatModule(BaseModule):
    @staticmethod
    def get_meta() -> ModuleMeta:
        return ModuleMeta(services=["get_history", "translate"])

    async def get_history(self, session_id, n=20): ...
```

- **Default = Developer-agnostic**: If `services` is not declared, any **public** method can be called (backward compatibility), and private methods (prefixed with underscore) are always forbidden; the primary control for restrictions lies in the user-side scope configuration.
- After declaration: Only methods in the whitelist are callable, and calling outside the whitelist throws `ServiceNotProvidedError`.
- Caller restrictions: `scope.set_action("CallerModule", "call", deny="Chat.get_history")`

**Service Description (`description`)**: `services` supports a dict format to declare descriptions for each service (supports plain strings or i18n dictionaries), providing data for service directories or AI consumption:

```python
return ModuleMeta(
    services=[
        "get_history",                              # Simple form: description automatically taken from the first line of the method's docstring
        {"name": "translate", "description": "Translate text into the specified language"},
        {"name": "summarize", "description": {"i18n": "Chat.meta.svc.summarize", "default": "Summarize conversation"}},
    ],
)
```

Description resolution priority: **Explicit description (i18n resolved to current language) > First line of method docstring > Empty string**.

### Service Directory (`services`)

```python
sdk.module.services()
# {'Chat': [{'name': 'get_history', 'signature': '(session_id, n=20)',
#            'description': 'Retrieve conversation history'}]}

sdk.module.services("Chat")  # Query only a specific module
```

Lists only modules that explicitly declare `meta.services`. Each service includes a method signature string and description text, providing the data foundation for MCP (exposing call points to AI).

### Directed Events (`emit_to`)

```python
# Sender: Validates that the target module is enabled and delivers the event to `module.<name>.<event>`
await sdk.module.emit_to("Chat", "message_received", {"text": "hi"})

# Subscriber (within the Chat module): Registers a namespace hook
lifecycle.on("module.Chat.message_received", handler)
lifecycle.on("module.Chat", handler)  # Or receive all directed events from this module
```

> [!NOTE]
> This feature is new in ErisPulse **2.8.0+**

## Lifecycle Module

Event-driven lifecycle manager, providing event submission and listening functionality.

### API Overview

| Method | Description |
|------|------|
| `on(event, priority=0)` | Decorator to register event handler, supports dot matching and wildcard `*` |
| `register(event, handler, priority=0)` | Functional approach to register handler |
| `unregister(event, handler=None)` | Remove handler |
| `emit(event, data)` | Asynchronously trigger event |
| `emit_sync(event, data)` | Synchronously trigger event |
| `submit_event(event_type, msg, data, source)` | Submit standard format event (compatible with old version) |
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
```

> For the complete list of standard events and detailed usage, see [Lifecycle Management](../advanced/lifecycle.md).

## Router Module

HTTP/WebSocket router manager, based on FastAPI + Uvicorn, supporting decorator routing, middleware, grouping, rate limiting, CORS.

> For the complete router API documentation (decorator routing, WebSocket, middleware, rate limiting, CORS, security headers, etc.), see [Router Manager](../advanced/router.md).

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

Unified network client, aggregating HTTP requests, WebSocket connections, connection pooling, automatic retries, request statistics, and lifecycle event integration.

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

Exports a snapshot of the current running state of the framework, for debugging and diagnostics.

```python
import json
state = sdk.dump_state()
print(json.dumps(state, indent=2, ensure_ascii=False, default=str))
```

The returned structure contains the status of the following subsystems:

| Field | Description |
|-------|-------------|
| `sdk` | SDK initialization status, Python version, runtime platform, timestamp |
| `adapters` | List of registered/started adapters, online status of Bots on each platform |
| `modules` | List of registered/active/disabled/lazy-loaded modules |
| `events` | Number of event handlers for each type (message/notice/request/meta/commands) |
| `router` | Server running status, number of HTTP/WebSocket routes |

> [!NOTE]
> Added in ErisPulse **2.5.2+**

## Interaction Interactions

Manage wait_reply suspended waiting and session mutual exclusion leases (`sdk.interaction`).

### Common Methods

```python
# Session timeout reminder: Remind after 5 minutes of no reply, reminder is automatically canceled when user replies
reminder = event.remind(300, "Are you still there?")
reminder.cancel()  # Cancel manually

# Timeout escalation: Must escalate at a specific time (not canceled by reply)
event.escalate(1800, lambda e: notify_master("30 minutes not handled"))

# Multi-path waiting: First come, first served
which, reply = await event.select(
    event.expect(pattern="agree*", user="A"),
    event.expect(pattern="refuse*", user="B"),
    timeout=60,
)

# Session-level waiting: Reply from anyone in the same group can trigger the event
reply = await event.wait_reply(session=True, prompt="Can someone help answer this?")

# Query current session ownership (who is currently interacting with this user)
owner = sdk.interaction.get_owner_of(event)

# Acquire session mutual exclusion lease (returns None if occupied)
lease = sdk.interaction.acquire(event)
if lease:
    try:
        ...  # Exclusive interaction
    finally:
        lease.release()

# Context manager form (throws SessionOccupiedError if occupied)
with sdk.interaction.hold(event) as lease:
    ...

# Suspended session statistics
sdk.interaction.counts()  # {'waits': 2, 'leases': 1, 'timers': 3, 'owners': {'Chat': 3}}
```

When the module is unloaded or the adapter is closed, all suspended waits and timers are automatically canceled (waiters immediately return `None`). When a reply matches, scope permissions are automatically rechecked (if the user is blacklisted or the module is unbound, the wait is terminated).

> [!NOTE]
> This feature was added in ErisPulse **2.8.0+**

## Transcript Conversation Inbox

An automatic record and query of recent message streams for each conversation (`sdk.transcript`), serving as a common foundation for context-aware modules such as AI conversations and anti-spam features.

### Common Methods

```python
# Convenient query (recommended): The last 20 messages (including users and robots, in ascending time order)
messages = await event.history(20)
for m in messages:
    print(m["role"], ":", m["text"])

# Manager API
sdk.transcript.append(event, "user", "text")
sdk.transcript.get(event, n=20)
sdk.transcript.clear(event)
```

Configuration (`ErisPulse.transcript`): `enabled` (default: enabled), `max_per_session` (maximum per session, default: 50), `ttl_hours` (global expiration time in hours, default: 168). Data is stored in a separate SQLite table, with lazy cleanup when limits are exceeded or data expires.

> [!NOTE]
> This feature was added in ErisPulse **2.8.0+**

## Related Documentation

- [Event System API](event-system.md) - Event module API
- [Adapter System API](adapter-system.md) - Adapter management API
- [SQL Query Builder](../advanced/sql-builder.md) - Full documentation for chainable SQL queries
- [Router Manager](../advanced/router.md) - Full documentation for router manager
- [Network Client](../advanced/http-client.md) - Full documentation for network client
- [Lifecycle Management](../advanced/lifecycle.md) - Full documentation for lifecycle management