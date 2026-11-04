# Core Modules API

> [!TIP]
> **When to read this**: When you need core capabilities such as storage, configuration, logging, module management, routing, or the HTTP client and can't recall the exact method signatures, use this document as a quick reference. Otherwise, skip it.

This document provides a quick API reference for the ErisPulse core modules, including method signatures and brief descriptions. For detailed usage and examples, click the "Full Documentation" link for each module.

## Storage Module

A key-value storage system based on configurable backends (SQLite/MySQL/PostgreSQL) with generic SQL chained query support; backends can be switched with a single configuration change. See [Storage Backends](../advanced/storage-backends.md) for details.

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

### SQL Chained Queries

The Storage module provides a chainable generic SQL query builder supporting CRUD operations on custom tables.

```python
sdk.storage.CreateTable("users", {
    "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
    "name": "TEXT NOT NULL",
})

sdk.storage.Table("users").Insert({"name": "Alice"}).Execute()
rows = sdk.storage.Table("users").Select("name").Where("id > ?", 0).Execute()
```

> For the full chained query API (Select/Insert/Update/Delete/Where/OrderBy/Limit, AlterTable, transactions, etc.), see [SQL Query Builder](../advanced/sql-builder.md).

### Storage Backend Abstraction

`StorageManager` inherits from the `BaseStorage` abstract base class and supports extension to other storage media (Redis, MySQL, etc.).

```python
from ErisPulse.Core.Bases.storage import BaseStorage, BaseQueryBuilder
```

### Async Interfaces

Both the Storage and Config modules provide async methods (prefixed with `a`): **async methods are the native primary interface, while sync methods are a compatibility layer** (internally bridged to run on a background event loop). Existing sync code requires no changes; for new code in async handlers, prefer the async methods.

```python
# Async storage
value = await sdk.storage.aget("key")
await sdk.storage.aset("key", "value")
await sdk.storage.adelete("key")
keys = await sdk.storage.aget_all_keys()
await sdk.storage.aclear()

# Async batch operations
values = await sdk.storage.aget_multi(["k1", "k2"])
await sdk.storage.aset_multi({"k1": "v1", "k2": "v2"})
await sdk.storage.adelete_multi(["k1", "k2"])

# Async configuration
value = await sdk.config.agetConfig("MyModule.key")
await sdk.config.asetConfig("MyModule.key", "value")
await sdk.config.aforce_save()
await sdk.config.areload()
```

## Config Module

TOML-format configuration file management with support for dot-separated key paths.

### API Overview

| Method | Description |
|------|------|
| `getConfig(key, default)` | Read configuration; supports dot paths such as `"MyModule.subkey"` |
| `getAllConfig()` | Full configuration snapshot (deep copy, including a view of pending unwritten values) |
| `setConfig(key, value, immediate=False)` | Write configuration. Saves to file immediately when `immediate=True` |
| `delConfig(key, immediate=False)` | Delete a configuration key (distinct from setting it empty), removing it from the file; triggers the `config.set` event (`new_value=None`) |
| `force_save()` | Force-write the in-memory configuration to file |
| `reload()` | Reload the configuration from file |
| `agetConfig(key, default)` | Async read configuration |
| `agetAllConfig()` | Async get full configuration snapshot |
| `asetConfig(key, value, immediate)` | Async write configuration |
| `adelConfig(key, immediate)` | Async delete a configuration key (same behavior as `delConfig`) |
| `aforce_save()` | Async force save |
| `areload()` | Async reload |

### Examples

```python
config = sdk.config.getConfig("MyModule", {})
value = sdk.config.getConfig("MyModule.timeout", 30)

snapshot = sdk.config.getAllConfig()          # Full snapshot (deep copy)
sdk.config.delConfig("MyModule.deprecated")  # Delete key (delayed write)

sdk.config.setConfig("MyModule", {"key": "value"})
sdk.config.setConfig("MyModule.timeout", 60, immediate=True)

# Async interfaces (prefer these in async handlers)
snapshot = await sdk.config.agetAllConfig()
await sdk.config.adelConfig("MyModule.deprecated")  # Async delete key
```

> `setConfig` uses delayed writes by default (batch saves every 5 seconds); set `immediate=True` to persist to the configuration file immediately. Configuration changes trigger the `config.set` lifecycle event.
> `delete` likewise supports delayed writes and the `config.set` event (`new_value=None`); existing `on_config_update` listeners can detect deletions with zero changes.

## Logger Module

A modular logging system built on Rich output, supporting child loggers and per-module level control.

### Basic Usage

```python
sdk.logger.debug("Debug message")
sdk.logger.info("Runtime message")
sdk.logger.warning("Warning message")
sdk.logger.error("Error message")
sdk.logger.critical("Critical error")
```

### Child Loggers

```python
child_logger = sdk.logger.get_child("MyModule")
child_logger.info("Submodule log")

child_logger.get_child("utils")  # Nesting supported
```

### Log Level Control

```python
sdk.logger.set_level("DEBUG")                          # Global level
sdk.logger.set_module_level("MyModule", "DEBUG")       # Module level

# Supported levels (low to high):
# TRACE, DEBUG, INFO, WARNING, ERROR, CRITICAL
# TRACE is the lowest level, outputting detailed internal framework debug info (event dispatching, route registration, etc.)
sdk.logger.set_level("TRACE")                          # Enable all logging
```

### Log Subscription (Push Mode)

Allows modules such as the Dashboard to receive structured logs in real time, with level filtering and history backfill support.

> **Explicitly subscribing to low-level logs**: A subscriber's `min_level` may be lower than the global log level. In that case, low-level logs are **pushed only to matching subscribers**, without being printed to the console or written to memory, avoiding pollution of the main log stream.
>
> ```python
> # With the global level at INFO, you can still subscribe to DEBUG logs separately
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
|------|------|
| `handler(id, *, min_level)(func)` | Works as a decorator or direct call. Falls back to the function name when `id` is empty. `min_level` may be lower than the global level (low-level logs are pushed only to subscribers, not to console/memory). Historical logs are backfilled automatically upon registration |
| `remove_handler(id)` | Remove a subscriber |

### Output Control

```python
sdk.logger.set_output_file("app.log")
sdk.logger.save_logs("log.txt")
sdk.logger.get_logs("MyModule")
sdk.logger.set_memory_limit(1000)
```

## Adapter Module

The adapter manager, which handles registration, startup, and shutdown of multi-platform adapters.

### API Overview

| Method | Description |
|------|------|
| `get(platform)` | Get an adapter instance |
| `exists(platform)` | Check whether an adapter is registered |
| `enable(platform)` / `disable(platform)` | Enable/disable an adapter |
| `is_enabled(platform)` | Check whether it is enabled |
| `startup(platforms)` / `shutdown(platforms)` | Start/shutdown adapters |
| `is_running(platform)` | Check whether an adapter is running |
| `list_running()` | List all running adapters |
| `platforms` | Get the list of all platform names |
| `get_info(platform)` | Adapter registration info (json-safe: meta + class name) |
| `get_meta(platform, resolve_i18n=True)` | Adapter description metadata (aligned with `module.get_meta`, supports i18n resolution) |

### Adapter Events

```python
@sdk.adapter.on("message")
async def handle_message(event):
    pass

@sdk.adapter.on("message", platform="yunhu")
async def handle_yunhu_message(event):
    pass
```

### Bot Status Queries

```python
sdk.adapter.get_bot_info("telegram", "123456")
sdk.adapter.list_bots("telegram")
sdk.adapter.is_bot_online("telegram", "123456")
sdk.adapter.get_status_summary()
```

> For the full adapter management API, see [Adapter System API](adapter-system.md).

## Module Module

The module manager, which handles registration, loading, and unloading of plugins.

### API Overview

| Method | Description |
|------|------|
| `get(name)` | Get a module instance or lazy-load proxy (returns a proxy when registered but not loaded) |
| `exists(name)` | Check whether it is registered |
| `is_loaded(name)` | Check whether it is loaded |
| `is_enabled(name)` | Check whether it is enabled |
| `enable(name)` / `disable(name)` | Enable/disable a module |
| `load(name)` / `unload(name)` | Load/unload a module |
| `call(module, method, *args, timeout=None, **kwargs)` | Cross-module invocation of the target module's service methods (protocol-based RPC) |
| `list_registered()` | List registered modules |
| `list_loaded()` | List loaded modules |
| `get_info(name)` | Get module information |
| `get_status_summary()` | Get a module status summary |

### Attribute Access

```python
module = sdk.module.get("ModuleName")
module = sdk.module.ModuleName
module = sdk.ModuleName  # Equivalent shortcut
```

### Cross-Module Calls (RPC)

```python
# Protocol-based calls: typed errors / lazy module auto-wakeup / owner attribution / timeout semantics
result = await sdk.module.call("Chat", "get_history", session_id, n=20)
```

Differences from raw attribute access on the provider `sdk.module.Chat.get_history(...)`:

| | `module.call()` | Raw attribute access |
|---|---|---|
| Target not registered/not enabled | Raises `ModuleNotAvailableError` | Raises `AttributeError` |
| Lazy-loaded module | Auto-wakeup | Async-init modules raise RuntimeError |
| `current_owner` | Attributed to the target module | Remains the caller |
| Timeout | 30s by default, overridable | None |
| Scope audit | `actions.<caller>.call` | None |

### Service Contracts (meta.services)

The provider declares an external whitelist in the `services` field of `get_meta()` (symmetric with `commands`); once declared, the callable surface is narrowed:

```python
class ChatModule(BaseModule):
    @staticmethod
    def get_meta() -> ModuleMeta:
        return ModuleMeta(services=["get_history", "translate"])

    async def get_history(self, session_id, n=20): ...
```

- **Default = invisible to developers**: When `services` is not declared, any **public** method can be called (backward compatible); underscore-private methods are always forbidden. The primary control over restrictions lies in user-side scope configuration
- Once declared: only whitelisted methods are callable; out-of-scope calls raise `ServiceNotProvidedError`
- Caller-side restriction: `scope.set_action("CallerModule", "call", deny="Chat.get_history")`

**Service descriptions**: `services` supports a dict form to declare a description for each service
(plain strings or i18n dicts are both supported), for consumption by the service catalog / AI call-site descriptions:

```python
return ModuleMeta(
    services=[
        "get_history",                              # Simple form: description automatically taken from the first line of the method docstring
        {"name": "translate", "description": "Translate text into the specified language"},
        {"name": "summarize", "description": {"i18n": "Chat.meta.svc.summarize", "default": "Summarize the conversation"}},
    ],
)
```

Description resolution priority: **explicit description (i18n resolved to the current language) > first line of the method docstring > empty string**.

### Service Catalog (services)

```python
sdk.module.services()
# {'Chat': [{'name': 'get_history', 'signature': '(session_id, n=20)',
#            'description': 'Get session history'}]}

sdk.module.services("Chat")  # Query only the specified module
```

Only modules that **explicitly declare** `meta.services` are listed; each service includes a method signature string
and description text, providing the data foundation for MCP-ization (exposing call sites to AI).

> Directed event delivery belongs to the lifecycle layer: `lifecycle.emit(event, data, to="ModuleName")`;
> see [Module Communication](../advanced/module-communication.md) for details.

## Lifecycle Module

An event-driven lifecycle manager providing event submission and listening capabilities.

### API Overview

| Method | Description |
|------|------|
| `on(event, priority=0)` | Decorator to register event handlers; supports dot matching and the `*` wildcard |
| `register(event, handler, priority=0)` | Functional handler registration |
| `unregister(event, handler=None)` | Remove a handler |
| `emit(event, data, to=None)` | Emit an event asynchronously; directed delivery when `to` specifies an owner |
| `emit_sync(event, data, to=None)` | Emit an event synchronously (async handlers are scheduled via create_task) |
| `submit_event(event_type, msg, data, source, to=None)` | Submit a standard-format event (legacy compatible) |
| `start_timer(id)` / `stop_timer(id)` | Performance timers |

### Examples

```python
@sdk.lifecycle.on("module.init")
async def handle_module_init(event_data):
    print(f"Module initialized: {event_data}")

@sdk.lifecycle.on("module")
async def handle_any_module_event(event_data):
    print(f"Module event: {event_data}")

await sdk.lifecycle.emit("custom.event", {"key": "value"})

# Directed delivery: dispatched only to hooks registered by the Chat module
await sdk.lifecycle.emit("message_received", {"text": "hi"}, to="Chat")
```

> For the full list of standard events and detailed usage, see [Lifecycle Management](../advanced/lifecycle.md).

## Router Module

An HTTP/WebSocket route manager built on FastAPI + Uvicorn, supporting decorator-based routes, middleware, grouping, rate limiting, and CORS.

> For the full routing API documentation (decorator routes, WebSocket, middleware, rate limiting, CORS, security headers, etc.), see [Router Manager](../advanced/router.md).

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

# Route group
group = sdk.router.group("MyModule", prefix="/v1")
@group.get("/users")
async def list_users(request: HttpRequest):
    return {"users": []}
```

## HTTP Client Module

A unified network client that aggregates HTTP requests, WebSocket connections, connection pool management, automatic retries, request statistics, and lifecycle event integration.

> For the full network client documentation (request methods, response objects, WebSocket client, exception hierarchy, etc.), see [Network Client](../advanced/client.md).

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

Exports a snapshot of the framework's current runtime state for debugging and diagnostics.

```python
import json
state = sdk.dump_state()
print(json.dumps(state, indent=2, ensure_ascii=False, default=str))
```

The returned structure contains the state of the following subsystems:

| Field | Description |
|------|------|
| `sdk` | SDK initialization state, Python version, runtime platform, timestamp |
| `adapters` | Registered/started adapter list, per-platform Bot online status |
| `modules` | Registered/enabled/disabled/lazy-loaded module list |
| `events` | Handler counts by event type (message/notice/request/meta/commands) |
| `router` | Server running state, HTTP/WebSocket route counts |

> [!NOTE]
> Added in ErisPulse **2.5.2+**

## Interaction Sessions

Manages pending wait_reply waits and session mutual-exclusion leases (`sdk.interaction`).

### Common Methods

```python
# Session timed reminder: remind after 5 minutes with no reply; auto-cancelled when the user replies
reminder = event.remind(300, "Are you still there?")
reminder.cancel()  # Manual cancellation

# Timeout escalation: guaranteed delivery when due (not cancelled by a reply)
event.escalate(1800, lambda e: notify_master("Unhandled for 30 minutes"))

# Multi-way wait: first come, first served
which, reply = await event.select(
    event.expect(pattern="Agree*", user="A"),
    event.expect(pattern="Decline*", user="B"),
    timeout=60,
)

# Session-level wait: replies from anyone in the same group can match
reply = await event.wait_reply(session=True, prompt="Can anyone help answer?")

# Query the session's current owner (who is interacting with this user)
owner = sdk.interaction.get_owner_of(event)

# Acquire a session mutual-exclusion lease (returns None if occupied)
lease = sdk.interaction.acquire(event)
if lease:
    try:
        ...  # Exclusive interaction
    finally:
        lease.release()

# Context manager form (raises SessionOccupiedError if occupied)
with sdk.interaction.hold(event) as lease:
    ...

# Pending session statistics
sdk.interaction.counts()  # {'waits': 2, 'leases': 1, 'timers': 3, 'owners': {'Chat': 3}}
```

When a module is unloaded or an adapter shuts down, its pending waits and timers are automatically cancelled (the waiting side immediately returns `None`);
when a reply matches, scope permissions are automatically re-checked (the wait terminates if the user has been blacklisted or the module has been unbound).

> [!NOTE]
> Capabilities in this section were added in ErisPulse **2.8.0+**

## Transcript Session Inbox

Automatic recording and querying of each session's recent message stream (`sdk.transcript`), serving as a shared foundation for context-memory modules such as AI conversation and anti-repetition.

### Common Methods

```python
# Convenient query (recommended): the 20 most recent messages of the current session (both user and bot, in ascending time order)
messages = await event.history(20)
for m in messages:
    print(m["role"], ":", m["text"])

# Manager API
sdk.transcript.append(event, "user", "text")
sdk.transcript.get(event, n=20)
sdk.transcript.clear(event)
```

Configuration (`ErisPulse.transcript`): `enabled` (on by default), `max_per_session` (per-session cap, default 50),
`ttl_hours` (global expiry, default 168 hours). Data is stored in a separate SQLite table; over-limit/expired entries are lazily cleaned up.

> [!NOTE]
> Capabilities in this section were added in ErisPulse **2.8.0+**

## Related Documentation

**Continue browsing the API**:
- [Event System API](event-system.md) - Event module API
- [Adapter System API](adapter-system.md) - Adapter management API

**Full documentation for a specific subsystem**:
- [SQL Query Builder](../advanced/sql-builder.md) - Full SQL chained query documentation
- [Router Manager](../advanced/router.md) - Full router manager documentation
- [Network Client](../advanced/client.md) - Full network client documentation
- [Lifecycle Management](../advanced/lifecycle.md) - Full lifecycle documentation