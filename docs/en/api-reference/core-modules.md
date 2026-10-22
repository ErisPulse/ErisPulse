# Core Module API

> [!TIP]
> **When to read this**: When you need to use core capabilities like storage, configuration, logging, module management, routing, or HTTP client, but can't remember the exact method signatures, quickly refer to this document. Skip if not needed.

This document provides a quick reference for ErisPulse core module APIs, including method signatures and brief descriptions. For detailed usage and examples, please click the "Full Documentation" links for each module.

## Storage Module

A key-value storage system based on configurable backends (SQLite/MySQL/PostgreSQL), supporting generic SQL chain query, with backend switching via configuration, see [Storage Backends](../advanced/storage-backends.md).

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

### SQL Chain Query

The Storage module provides a chain-call style generic SQL query builder, supporting CRUD operations for custom tables.

```python
sdk.storage.CreateTable("users", {
    "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
    "name": "TEXT NOT NULL",
})

sdk.storage.Table("users").Insert({"name": "Alice"}).Execute()
rows = sdk.storage.Table("users").Select("name").Where("id > ?", 0).Execute()
```

> For the complete chain query API (Select/Insert/Update/Delete/Where/OrderBy/Limit, AlterTable, transactions, etc.), see [SQL Query Builder](../advanced/sql-builder.md).

### Storage Backend Abstraction

`StorageManager` inherits from `BaseStorage` abstract base class, supporting extension to other storage media (Redis, MySQL, etc.).

```python
from ErisPulse.Core.Bases.storage import BaseStorage, BaseQueryBuilder
```

### Asynchronous Interfaces

The Storage and Config modules both provide asynchronous methods (prefixed with `a`): **Asynchronous is the native main interface, synchronous methods are compatibility layers** (internal bridge to background event loop execution). Existing synchronous code does not need modification; in new code within asynchronous handlers, prefer asynchronous methods.

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
| `getAllConfig()` | Full configuration snapshot (deep copy, including uncommitted pending values) |
| `setConfig(key, value, immediate=False)` | Write configuration. If `immediate=True`, immediately save to file |
| `delConfig(key, immediate=False)` | Delete configuration key (distinct from setting to empty), remove from file; triggers `config.set` event (`new_value=None`) |
| `force_save()` | Forcefully write in-memory configuration to file |
| `reload()` | Reload configuration from file |
| `agetConfig(key, default)` | Asynchronously read configuration |
| `agetAllConfig()` | Asynchronously get full configuration snapshot |
| `asetConfig(key, value, immediate)` | Asynchronously write configuration |
| `adelConfig(key, immediate)` | Asynchronously delete configuration key (behavior same as `delConfig`) |
| `aforce_save()` | Asynchronously force save |
| `areload()` | Asynchronously reload |

### Examples

```python
config = sdk.config.getConfig("MyModule", {})
value = sdk.config.getConfig("MyModule.timeout", 30)

snapshot = sdk.config.getAllConfig()          # Full snapshot (deep copy)
sdk.config.delConfig("MyModule.deprecated")  # Delete key (delayed write)

sdk.config.setConfig("MyModule", {"key": "value"})
sdk.config.setConfig("MyModule.timeout", 60, immediate=True)

# Asynchronous interface (prefer in asynchronous handlers)
snapshot = await sdk.config.agetAllConfig()
await sdk.config.adelConfig("MyModule.deprecated")  # Asynchronously delete key
```

> `setConfig` defaults to delayed write (batch save every 5 seconds), setting `immediate=True` immediately persists to the configuration file. Configuration changes trigger the `config.set` lifecycle event.
> `delete` also supports delayed write and `config.set` event (`new_value=None`), existing `on_config_update` listeners require zero changes to detect deletion.

## Logger Module

Modular logging system, based on Rich output, supports child loggers and module-level control.

### Basic Usage

```python
sdk.logger.debug("Debug information")
sdk.logger.info("Runtime information")
sdk.logger.warning("Warning information")
sdk.logger.error("Error information")
sdk.logger.critical("Critical error")
```

### Child Loggers

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
# TRACE is the lowest level, outputs detailed framework internal debug information (event dispatch, routing registration, etc.)
sdk.logger.set_level("TRACE")                          # Enable all logs
```

### Log Subscription (Push Mode)

For modules like Dashboard to receive structured logs in real-time, supports level filtering and historical replay.

> **Explicitly subscribe to lower-level logs**: The `min_level` of a subscriber can be lower than the global log level. In this case, low-level logs are **only pushed to matching subscribers**, not output to console, nor written to memory, thus avoiding pollution of the main log stream.
>
> ```python
> # Global is INFO, still can individually subscribe to DEBUG logs
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
| `handler(id, *, min_level)(func)` | Decorator/inline call dual-use. If `id` is empty, use function name. `min_level` can be lower than global level (low-level logs only push to matching subscribers, not to console/memory). Registering automatically replays historical logs |
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
| `get_info(platform)` | Adapter registration information (json-safe: meta + class name) |
| `get_meta(platform, resolve_i18n=True)` | Adapter introduction metadata (aligned with `module.get_meta`, supports i18n resolution) |

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

### Inter-Module Calls (RPC)

```python
# Protocolized call: typed errors / lazy module auto-wake-up / owner attribution / timeout semantics
result = await sdk.module.call("Chat", "get_history", session_id, n=20)
```

Difference between `module.call()` and direct service access `sdk.module.Chat.get_history(...)`:

| | `module.call()` | Direct attribute access |
|---|---|---|
| Target not registered/enabled | Throws `ModuleNotAvailableError` | Throws `AttributeError` |
| Lazy-loaded module | Auto-wake-up | Async module initialization throws RuntimeError |
| `current_owner` | Attributed to target module | Retains caller |
| Timeout | Default 30s, can be overridden | None |
| Scope audit | `actions.<caller>.call` | None |

### Service Contract (`meta.services`)

Service provider declares a white-listed external API in `get_meta()`'s `services` field (symmetrical with `commands`), tightening the call surface after declaration:

```python
class ChatModule(BaseModule):
    @staticmethod
    def get_meta() -> ModuleMeta:
        return ModuleMeta(services=["get_history", "translate"])

    async def get_history(self, session_id, n=20): ...
```

- **Default = Developer-agnostic**: If `services` is not declared, any **public** method can be called (backward compatibility), private methods with underscore are always forbidden; the main control for restrictions is on the user-side scope configuration
- After declaration: Only methods in the white-list are allowed, calling beyond the list throws `ServiceNotProvidedError`
- Caller restriction: `scope.set_action("CallerModule", "call", deny="Chat.get_history")`

**Service Description (`description`)**: `services` supports dict form to declare description for each service (supports plain string or i18n dict), for service directory / AI call point description consumption:

```python
return ModuleMeta(
    services=[
        "get_history",                              # Simple form: description automatically takes the first line of method docstring
        {"name": "translate", "description": "Translate text into specified language"},
        {"name": "summarize", "description": {"i18n": "Chat.meta.svc.summarize", "default": "Summarize conversation"}},
    ],
)
```

Description resolution priority: **Explicit description (i18n resolved to current language) > First line of method docstring > Empty string**.

### Service Directory (`services`)

```python
sdk.module.services()
# {'Chat': [{'name': 'get_history', 'signature': '(session_id, n=20)',
#            'description': 'Get conversation history'}]}

sdk.module.services("Chat")  # Query only specific module
```

Only lists modules that explicitly declare `meta.services`; each service includes method signature string and description text, providing data foundation for MCP (exposing call points to AI).

> Directed event delivery belongs to the lifecycle layer: `lifecycle.emit(event, data, to="ModuleName")`, see [Inter-Module Communication](../advanced/module-communication.md).

## Lifecycle Module

Event-driven lifecycle manager, providing event submission and listening functionality.

### API Overview

| Method | Description |
|------|------|
| `on(event, priority=0)` | Decorator to register event handler, supports dot matching and wildcard `*` |
| `register(event, handler, priority=0)` | Function-style registration of handler |
| `unregister(event, handler=None)` | Remove handler |
| `emit(event, data, to=None)` | Asynchronously trigger event; if `to` specifies owner, deliver only to that module |
| `emit_sync(event, data, to=None)` | Synchronously trigger event (in asynchronous handlers, scheduled via create_task) |
| `submit_event(event_type, msg, data, source, to=None)` | Submit standard format event (compatible with old version) |
| `start_timer(id)` / `stop_timer(id)` | Performance timer |

### Examples

```python
@sdk.lifecycle.on("module.init")
async def handle_module_init(event_data):
    print(f"Module initialized: {event_data}")

@sdk.lifecycle.on("module")
async def handle_any_module_event(event_data):
    print(f"Module event: {event_data}")

await sdk.lifecycle.emit("custom.event", {"key": "value"})

# Directed delivery: only deliver to hooks registered by Chat module
await sdk.lifecycle.emit("message_received", {"text": "hi"}, to="Chat")
```

> For the complete list of standard events and detailed usage, see [Lifecycle Management](../advanced/lifecycle.md).

## Router Module

HTTP/WebSocket routing manager, based on FastAPI + Uvicorn, supports decorator routing, middleware, grouping, rate limiting, CORS.

> For the complete routing API documentation (decorator routing, WebSocket, middleware, rate limiting, CORS, security headers, etc.), see [Router Manager](../advanced/router.md).

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

> For the complete network client documentation (request methods, response objects, WebSocket client, exception hierarchy, etc.), see [Network Client](../advanced/http-client.md).

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

Exports a snapshot of the current runtime state of the framework, for debugging and diagnostics.

```python
import json
state = sdk.dump_state()
print(json.dumps(state, indent=2, ensure_ascii=False, default=str))
```

The returned structure includes the status of the following subsystems:

| Field | Description |
|------|------|
| `sdk` | SDK initialization status, Python version, runtime platform, timestamp |
| `adapters` | List of registered/started adapters, online status of Bots per platform |
| `modules` | List of registered/enabled/disabled/lazy-loaded modules |
| `events` | Number of handlers for various event types (message/notice/request/meta/commands) |
| `router` | Server running status, number of HTTP/WebSocket routes |

> [!NOTE]
> Added in ErisPulse **2.5.2+**

## Interaction Sessions

Manages wait_reply suspension and session mutual exclusion leases (`sdk.interaction`).

### Common Methods

```python
# Session timeout reminder: 5 minutes without reply will remind, user reply cancels automatically
reminder = event.remind(300, "Still there?")
reminder.cancel()  # Manually cancel

# Timeout escalation: guaranteed delivery at the deadline (not cancelled by reply)
event.escalate(1800, lambda e: notify_master("30 minutes unhandled"))

# Multi-path waiting: first come, first served
which, reply = await event.select(
    event.expect(pattern="agree*", user="A"),
    event.expect(pattern="reject*", user="B"),
    timeout=60,
)

# Session-level waiting: reply from anyone in the same group can match
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

# Suspend session count
sdk.interaction.counts()  # {'waits': 2, 'leases': 1, 'timers': 3, 'owners': {'Chat': 3}}
```

When modules are unloaded or adapters are shut down, their suspended waits and timers are automatically canceled (waits immediately return `None`), and reply matches automatically recheck scope permissions (if user is blacklisted/module is unbound, wait is terminated).

> [!NOTE]
> This section's capabilities were added in ErisPulse **2.8.0+**

## Transcript Session Inbox

Automatic recording and querying of recent message flows per session (`sdk.transcript`), serving as a public foundation for AI conversation, anti-repetition, and other context-memory modules.

### Common Methods

```python
# Convenient query (recommended): recent 20 messages of current session (including user and bot, in ascending time order)
messages = await event.history(20)
for m in messages:
    print(m["role"], ":", m["text"])

# Manager API
sdk.transcript.append(event, "user", "text")
sdk.transcript.get(event, n=20)
sdk.transcript.clear(event)
```

Configuration (`ErisPulse.transcript`): `enabled` (default enabled), `max_per_session` (per-session limit, default 50), `ttl_hours` (global expiration time, default 168 hours). Data is stored in a separate SQLite table, with lazy cleanup for over-limit/expired entries.

> [!NOTE]
> This section's capabilities were added in ErisPulse **2.8.0+**

## Related Documentation

**Continue to check API**:
- [Event System API](event-system.md) - Event module API
- [Adapter System API](adapter-system.md) - Adapter management API

**Deep dive into a subsystem's full documentation**:
- [SQL Query Builder](../advanced/sql-builder.md) - Full documentation for SQL chain query
- [Router Manager](../advanced/router.md) - Full documentation for router manager
- [Network Client](../advanced/http-client.md) - Full documentation for network client
- [Lifecycle Management](../advanced/lifecycle.md) - Full documentation for lifecycle