---
name: erispulse-communication
description: "适用于：模块间通信（RPC/定向/广播）、HTTP/WS 客户端、连接管理。覆盖场景：When you need cross-module calls (RPC), service contracts, directed events, or cold-start replay. Skip if not needed, as it won't affect the usage of other features.。When you need WebSocket/SSE connection pools, broadcast groups, cross-module pushing, or to check connections. Skip if not needed, as it does not affect the use of other features.。When you need to make outbound HTTP / WebSocket requests. Skip if not needed, it doesn't affect the use of other features.。When you need HTTP/WebSocket/SSE routes (including connection pool broadcasting). Skip if not needed, as it does not affect the use of other features.。"
---

# ErisPulse 通信与连接

This skill is auto-built from the ErisPulse documentation.
Repository: https://github.com/ErisPulse/ErisPulse
Source paths are annotated per section; see docs/ in the repository for the latest content.

## 模块间通信

> 来源: `docs/en/advanced/module-communication.md`（https://github.com/ErisPulse/ErisPulse/blob/main/docs/en/advanced/module-communication.md）

# Inter-Module Communication

> [!TIP]
> **When to read this**: When you need cross-module calls (RPC), service contracts, directed events, or cold-start replay. Skip if not needed, as it won't affect the usage of other features.

> **After reading, you will know**: The selection mnemonic for the three-layer communication model (RPC / directed events / broadcast), `meta.services` service contracts and service directory, outbound audit configuration, lazy wake-up, and cold-start replay.
>
> **This section does not cover**: The registration / triggering / priority mechanism of the lifecycle event system itself (see [Lifecycle Management](lifecycle.md)); lazy loading configuration and `activate_on` declaration (see [Lazy Loading System](lazy-loading.md)).

> [!NOTE]
> This chapter requires ErisPulse **2.8.0+**.

ErisPulse's modules have a **three-layer communication model**, arranged from "point-to-point → directed → broadcast":

| Layer | API | Semantics | Typical Scenarios |
|---|---|---|---|
| **RPC** | `await sdk.module.call("Chat", "get_history", ...)` | Point-to-point request-response with contract / audit / timeout | Invoking capabilities of another module (e.g., fetching history, translation, refund) |
| **Directed Events** | `await lifecycle.emit("message_received", {...}, to="Chat")` | Distributed only to lifecycle hooks registered by the specified module | Upstream state change notification to downstream (e.g., "a new message was received") |
| **Broadcast** | `await lifecycle.emit("config.updated", {...})` | Framework-wide lifecycle events | Hot configuration updates, module up/down events |

{!--< tips >!--}
Selection Mnemonic: **Use `call` when you need a return value, use `emit(..., to=...)` to notify a specific module's hooks, and use `emit(...)` to notify everyone.**
{!--< /tips >!--}

## RPC: module.call

```python
result = await sdk.module.call("Chat", "get_history", session_id, n=20)
```

Difference from direct attribute access `sdk.module.Chat.get_history(...)` (unchanged):

| | `module.call()` | Direct attribute access |
|---|---|---|
| Target not registered / enabled | Throws `ModuleNotAvailableError` | Throws `AttributeError` |
| Lazy-loaded module | **Automatically wakes up** (event-driven modules use activation lock) | Async initialization throws RuntimeError |
| `current_owner` | Attributed to the **target module** (its internal wait_reply / send / logs are correctly attributed) | Maintains caller |
| Timeout | Default 30 seconds (`timeout=` overrides, None means no timeout) | None |
| Scope audit | Caller passes through outbound gate `actions.<caller>.call` | None |
| Contract validation | `meta.services` whitelist | None |

### Exception Hierarchy

```
ModuleError                      # Base class for module system exceptions
└── ModuleCallError              # Base class for cross-module calls (includes module / method attributes)
    ├── ModuleNotAvailableError  # Target not registered / enabled / activation failed
    ├── ServiceNotProvidedError  # Method not in services whitelist / private method / does not exist
    └── ModuleCallTimeoutError   # Coroutine method timeout
```

All are part of the `ErisPulseError` hierarchy, and can be caught via `from ErisPulse.Core import ModuleCallError`.

## Service Contract: meta.services

The service provider declares the whitelist of services offered externally in `get_meta()` (symmetrical to the `commands` field):

```python
from ErisPulse.Core.Bases import BaseModule, ModuleMeta

class ChatModule(BaseModule):
    @staticmethod
    def get_meta() -> ModuleMeta:
        return ModuleMeta(
            name="Chat",
            services=[
                "get_history",                                       # Simple form
                {"name": "translate", "description": "Translate text into a specified language"},  # With description
            ],
        )

    async def get_history(self, session_id, n=20): ...
    async def translate(self, text, target_lang): ...
    def _internal_helper(self): ...   # Methods with leading underscore are always prohibited from external calls
```

**By default, services are invisible to developers**:

- If `services` is not declared → all **public** methods are naturally callable via `module.call()` (consistent with direct attribute access),
  no declaration is required
- After declaration → the scope is restricted to the whitelist, calling outside the whitelist raises `ServiceNotProvidedError`—used to mark
  "these methods are the ones promised externally"
- The main control authority lies with the user: `scope.actions` configuration determines "who can call whom" (see audit below),
  the module author's `services` is only a service declaration, and the two layers are independent

**Service Descriptions**: Provide human- or AI-readable descriptions for each service—leave empty if not needed,
the description is automatically taken from the **first line of the method's docstring** (the framework already requires docstring style):

```python
async def translate(self, text, target_lang):
    """Translate text into a specified language"""    # ← This line automatically becomes the service description
    ...
```

**Parameter Hints**: The caller (especially AI agents) needs to know the meaning of each parameter. Leave empty if not needed,
hints are automatically taken from the **`:param:` lines** in the method's docstring:

```python
async def render_card(self, html, width=800, height=0):
    """Render HTML into an image file

    :param html: HTML text to render          ← Automatically becomes the parameter hint
    :param width: Canvas width in pixels, 0 for adaptive to content
    :param height: Canvas height in pixels, 0 for adaptive to content
    """
```

For fine-grained control (overriding docstring or multi-language support), use the dict form to declare `description` and `parameters`
(both support i18n dictionaries; `parameters` are merged with the docstring **by parameter**, explicit declaration within a single parameter takes precedence,
parameters declared that do not exist in the signature are filtered):

```python
services=[
    {"name": "translate", "description": "Translate text into a specified language"},
    {"name": "summarize", "description": {"i18n": "Chat.meta.svc.summarize", "default": "Summarize conversation"}},
    {
        "name": "render_card",
        "description": "Render HTML into an image file",
        "parameters": {"html": "HTML text", "width": "Width in pixels, 0 for adaptive"},
    },
]
```

## Service Directory: services()

```python
sdk.module.services()
# {'Chat': [{'name': 'get_history', 'signature': '(session_id, n=20)',
#            'description': 'Translate text into the specified language',
#            'parameters': {'session_id': 'Session ID', 'n': 'Number of entries to return'}}]}

sdk.module.services("Chat")   # Query only a specific module
```

- Only modules that explicitly declare `meta.services` are listed (modules without declaration do not appear in the directory)
- Each service includes a method signature string (extracted via `inspect.signature`), description text, and parameter hints
- **Lazily loaded modules are also included in the directory** (service discovery occurs before loading) — the caller can decide whether to `call()` to activate the target module
- Modules are also included in the topology: each entry in `sdk.module.get_topology()` contains a `services` field

{!--< tips >!--}
**MCP Roadmap**: The service directory (name + signature + description + parameter hints) naturally forms the shape of an MCP tool — each service becomes ``{"name", "description", "parameters"}``. In the future, the framework could directly expose ``services()`` as an MCP server endpoint, allowing AI to discover and invoke module capabilities; ``scope.actions.call`` auditing naturally becomes a security gate for AI calls.
{!--< /tips >!--}

## Outbound Audit: Who Can Call Whom

Each `module.call()` passes through the scope outbound gate as the **caller module**:

```toml
[ErisPulse.scope.actions.CallerModule.call]
deny = ["Chat.get_history"]        # Deny CallerModule from calling Chat's get_history
# allow = ["Chat.get_*"]           # Or whitelist: only allow calling Chat's get-* services
```

- `name` format is `<target module>.<method name>`, supporting exact / glob / `re:` regex
- Framework-level calls (without owner context, e.g., startup scripts) are not subject to audit constraints
- Denied calls throw `ModuleCallError` (TRACE log `core.module.call_denied`)

See [Scope (scope)](scope.md) for configuration details on the outbound dimension.

## Directed Events: lifecycle.emit with to parameter

Lifecycle events support directed propagation: when `to` specifies the target owner (owner), the event is only delivered to hooks registered by that owner (modules automatically register hooks in `on_load` and record the owner). Other modules and wildcard `*` handlers do not receive the event.

```python
from ErisPulse.Core.lifecycle import lifecycle

# Emitter: event is only delivered to hooks registered by Chat module
await lifecycle.emit("message_received", {"text": "hi", "from": "u1"}, to="Chat")

# Subscriber (inside Chat module): register same-name hook, owner is automatically recorded during registration
@lifecycle.on("message_received")
async def on_message_received(data): ...

@lifecycle.on("message")          # Point prefix also works (filtered by owner)
async def on_any(data): ...
```

Semantic details:

- If the target owner has no registered hooks → the event is **silently discarded** (does not send to non-existent places), use `lifecycle.has_handlers("message_received")` to probe in advance
- When `data` is a dict, it automatically carries `_trace_id` (without overriding existing values), integrating with full-chain tracing
- Broadcast and directed events share the same hook registration: `emit(...)` without `to` broadcasts to the entire framework, while with `to` the same event is only visible to the target module
- `emit_sync` / `submit_event` (compatibility API) also support `to=` parameter

> [!NOTE]
> Directed events are lightweight notifications, **do not perform target validation or lazy activation**; for target existence validation, contract audit, or return values, switch to [RPC: module.call](#rpcmodulecall).

## Lazy Loading and Invocation

`module.call()` transparently activates lazy-loaded modules:

- Event-driven lazy modules (`activate_on` declared) → Use activation lock `_activate()`, stub automatically unregisters after activation
- Regular lazy modules → Synchronous initialization or standard loading path (idempotent)
- Activation failure → `ModuleNotAvailableError`

That is: **the caller does not need to care whether the target module is loaded** and does not need to wait for it to be activated.

Directed events (`lifecycle.emit(..., to=...)`) do not perform lazy activation—target not loaded means no hooks, event silently discarded; use `module.call()` if you need to ensure delivery.

## Cold Start Replay

A newly installed / restarted module missed some chat messages—`get_load_strategy(replay=...)` allows the framework to replay the most recent messages from the session inbox to the module itself after it is ready:

```python
from ErisPulse.loaders import ModuleLoadStrategy

class MyAIModule(BaseModule):
    @staticmethod
    def get_load_strategy():
        return ModuleLoadStrategy(
            lazy_load=False,
            priority=100,
            replay="5m",        # Replay the last 5 minutes ("1h" / "300" seconds are also valid)
        )

    async def on_load(self, event):
        @message.on_message()
        async def handle(e):
            if e.get("replayed"):
                # Synthetic event: only supplement context, do not trigger side effects like sending
                ...
```

Semantic details:

- The data source is the [session inbox](interaction.md#session-inbox-eventhistory) (`sdk.transcript.recent()`), executed in the background after module loading, without blocking startup
- Synthetic events carry the `replayed: True` flag, along with complete `platform / detail_type / user_id / alt_message`, and are **only distributed to the module's own handlers**—other modules are unaffected by the replay
- If the inbox is not enabled / no records exist / the replay duration is invalid (`replay_invalid` warning), it is silently skipped

## Event Idempotency Deduplication

After platform websocket reconnection, the same event (with the same `event["id"]`) is often re-sent—event distribution entry deduplicates by id (capacity 4096), so the same id event is only distributed once.

```toml
[ErisPulse.framework]
event_dedupe = true   # Default on; turn off for test environments with fixed id synthetic events
```

The deduplication cache is automatically reset when adapters **register** (start of new connection lifecycle).

## 连接管理

> 来源: `docs/en/advanced/connections.md`（https://github.com/ErisPulse/ErisPulse/blob/main/docs/en/advanced/connections.md）

# Connection Pool and Broadcasting

> [!TIP]
> **When to read this**: When you need WebSocket/SSE connection pools, broadcast groups, cross-module pushing, or to check connections. Skip if not needed, as it does not affect the use of other features.

> **What you will learn**: How three types of connections are automatically registered into the registry, group subscription and broadcast APIs, cross-module reuse and ownership, and the cleanup semantics of connections when modules are unloaded.
>
> **This section does not cover**: WebSocket/SSE route registration and connection lifecycle hooks (see [Router Manager](router.md)); client-side HTTP requests (see [Network Client](http-client.md)).

Connections (server-side WebSocket/SSE / client-side outbound WebSocket) in ErisPulse are **first-class resources at the framework level**: they are automatically registered into a unified registry upon establishment, supporting broadcasting, business group subscription, and cross-module transfer/reuse. When a module is unloaded, the framework automatically closes and recycles them—no need for business code to manually build `_ws_clients` collections, nor worry about leaks due to forgotten cleanup.

> All examples in this document use **root import** syntax (recommended in 2.10+):  
> `from ErisPulse import connections, router, client, WebSocketConnection`

## Overview

```python
from ErisPulse import connections, router, WebSocketConnection

# Server-side: connections are automatically registered; join business groups in handler
@router.ws("MyModule", "/ws")
async def handle(ws: WebSocketConnection):
    ws.join_group("room:1")            # Group naming is entirely business-defined
    async for msg in ws.iter_text():
        ...                             # Framework automatically unregisters and cleans up on disconnect

# Anywhere: broadcast to a group (returns success/failure details)
result = await connections.broadcast({"type": "notify"}, group="room:1")
if not result.ok:
    ...                                 # result.failed: {connection id: exception}
```

Three types of connections are unified into the registry:

| kind | Source | Owner | Description |
|------|--------|-------|-------------|
| `server` | `@router.ws(...)` / `register_websocket(...)` | Module name that registered the route | Automatically unregisters on disconnect |
| `sse` | `@router.sse(...)` / `register_sse(...)` | Module name that registered the route | Broadcasting uses `sse.send()` |
| `client` | `await client.ws_connect(url)` | Current module (or explicit `owner=`) | Automatically unregisters on close/remote disconnect; framework closes all on adapter stop |

To avoid automatic registration: pass `track=False` to routes or outbound connections; old code behavior remains unchanged.

## Checking Connection Pool

```python
from ErisPulse import connections

# Check connection pool of a module ("how many active connections does a module have now?")
conns = connections.list(namespace="Dashboard")
for conn in conns:
    print(conn.id, conn.kind, conn.groups, conn.meta)

# Filter by other dimensions (all conditions AND)
connections.list(owner="MyAdapter", kind="client")
connections.list(group="tenant:acme")

# Global statistics (counts by each dimension)
stats = connections.stats()
# {'total': 5, 'by_kind': {...}, 'by_namespace': {...}, 'by_owner': {...}, 'groups': {...}}

# Ownership audit counts (ownership facade is also visible)
from ErisPulse import ownership
ownership.counts("Dashboard")   # {'connections': 3, ...}
```

Each connection has readable identity information: `conn.id` (e.g., `Dashboard:1a2b3c4d`), `conn.namespace`, `conn.owner`, `conn.kind`, `conn.groups`, `conn.meta` (business-defined dictionary).

## Broadcasting and Subscription

### Groups (Subscription Model)

Groups are **flat strings**, with naming entirely defined by business logic (rooms / tenants / topics...). Nested levels are expressed through naming conventions (e.g., `tenant:acme/room:1`); the framework does not constrain the format.

Both directions can be operated:

```python
# Direction 1: Connection-side active join/leave (inside handler)
@router.ws("Chat", "/ws")
async def handle(ws: WebSocketConnection):
    ws.join_group("room:1")        # Equivalent to connections.assign(ws.id, "room:1")
    ws.leave_group("room:1")

# Direction 2: Management-side passive assignment (route-side / other modules)
connections.assign(conn_id, "tenant:acme")
connections.dismiss(conn_id, "tenant:acme")   # No group name = leave all groups
```

When a connection disconnects, it automatically leaves all groups; no business cleanup is needed.

### Broadcasting

```python
result = await connections.broadcast(
    data,                       # WS uses send_json; SSE uses send (automatic JSON serialization)
    namespace="Dashboard",      # Filter by namespace
    group="room:1",             # Filter by group
    kind="sse",                 # Filter by connection type
    owner="MyAdapter",          # Filter by owner
    ids={conn_id, ...},         # Explicitly specify candidate set (filter conditions still apply)
    exclude={conn_id},          # Exclude certain connections
    timeout=10.0,               # Timeout per connection (not total duration)
    concurrency=64,             # Maximum concurrent send limit
    raise_on_error=False,       # If True, throws the first exception if there are failed items
)
result.total      # Total number of target connections (excluding before)
result.sent       # List of successfully sent connection IDs
result.failed     # {Connection ID: Exception object} (timeout/disconnected/sending failed)
result.excluded   # Excluded connection IDs
result.ok         # Whether all were delivered
```

Filter conditions are **AND**; a single failure does not affect other connections; connections in `ids` that no longer exist are counted in `failed` (letting business know the full picture).

### Lifecycle Events

Lifecycle events are emitted when connections are registered/unregistered/group changes occur; Dashboard and others can subscribe for real-time presentation:

```python
from ErisPulse import lifecycle

@lifecycle.on("connection.registered")
async def on_registered(data): ...
@lifecycle.on("connection.unregistered")
async def on_unregistered(data): ...
@lifecycle.on("connection.group.joined")
async def on_joined(data): ...
@lifecycle.on("connection.group.left")
async def on_left(data): ...
```

## Cross-Module Transfer / Reuse

Connections are framework-registered resources; any module can retrieve and **reuse** them via connection ID—no need to recreate or know who created the connection:

```python
from ErisPulse import connections

conn = connections.get("Dashboard:1a2b3c4d")   # Throws ConnectionNotFoundError if not exists/already disconnected
await conn.send_json({"ping": 1})              # Any module can send
conn.join_group("someone-elses-room")          # Can also participate in groups
```

**Ownership and Close Authority**:

- The `owner` (module that created the connection) has exclusive close authority. Non-owner calls to `close()` throw `ConnectionPermissionError` (`from ErisPulse import ConnectionPermissionError`);
- Sending and group operations are open to all modules, no authorization required;
- When the owner module unloads or the adapter stops, the framework **closes and unregisters** all its connections (server-side + outbound). References still held by the module will fail on sending, and listening to the `connection.unregistered` event can detect this;
- The internal framework recycling path uses `close(force=True)` to bypass checks.

> Attribution Note: Close authority checks depend on runtime owner context (`owner_scope` / event dispatch / `spawn_background` etc. automatically carry it). Calls without context attribution (old code without attribution) are allowed, ensuring zero breakage; new code called within owner context is protected.

## Outbound Connections (Client Side)

```python
from ErisPulse import client

ws = await client.ws_connect("wss://example.com/ws")
ws.id          # Already registered, can be queried/broadcasted via connections
ws.owner       # Current module (suggest explicit owner if owner context is unavailable)

# Explicitly specify owner when owner context is unavailable (e.g., utility thread callback), so unloading can automatically reclaim:
ws = await client.ws_connect("wss://example.com/ws", owner="MyAdapter")
```

Remote active disconnects or local `close()` will automatically unregister the connection; when a module unloads, the framework closes all its outbound connections. The era of old code creating connections manually and managing them, leading to leaks due to forgotten cleanup, is over.

## Cross-Thread Delivery

When reaching connections (broadcasting / pushing / closing) from a sub-thread, use the framework's standard tools to deliver back to the main loop; **do not manually write `run_coroutine_threadsafe`**:

```python
from ErisPulse import run_main_loop, spawn_later, spawn_thread

# Blocking result retrieval from sub-thread:
run_main_loop(connections.broadcast({"tick": 1}, group="room:1"), timeout=5)

# Background thread + delayed task (owner attribution, automatically canceled on unload):
def push_tick():
    return connections.broadcast({"tick": 1}, group="room:1")
spawn_later(30, push_tick, owner="MyModule")
```

## Unload and Cleanup Semantics

The ownership recovery chain on module unload / adapter stop will sequentially: cancel background tasks and timers belonging to the owner → **close and unregister owner connections** → trigger the `on_cleanup` hook → unregister route/processor and other registered resources. See [Ownership (Owner) System](ownership.md).

> [!WARNING]
> Starting from 2.10, module unload will close its registered WS/SSE/outbound connections. Downstream components relying on "connections remaining alive after unload" (such as old Dashboard push) should be aware—this is the expected behavior to prevent connection leaks.

## API Overview

| API | Description |
|-----|-------------|
| `connections.get(id)` | Get connection (cross-module entry), throws `ConnectionNotFoundError` if not exists |
| `connections.list(namespace=, owner=, group=, kind=)` | Filter query connection list |
| `connections.stats(namespace=, owner=)` | Count statistics by each dimension |
| `connections.assign(id, *groups)` / `dismiss(id, *groups)` | Management-side join/leave group |
| `await connections.broadcast(data, ...)` | Broadcast, returns `BroadcastResult` |
| `await connections.close(id, force=False)` | Close and unregister (with permission check) |
| `await connections.close_owner(owner)` | Close and unregister all connections under a specific owner (called by framework unload chain) |
| `conn.join_group(*groups)` / `conn.leave_group(*groups)` | Connection-side group |
| `conn.send_json / send_text / iter_text / ...` | Send/receive (consistent interface for server/client) |
| `conn.meta` | Business metadata dictionary |
| `conn.close(force=False)` | Close (throws `ConnectionPermissionError` if not owner) |

## HTTP 客户端

> 来源: `docs/en/advanced/http-client.md`（https://github.com/ErisPulse/ErisPulse/blob/main/docs/en/advanced/http-client.md）

# Network Client

> [!TIP]
> **When to read this**: When you need to make outbound HTTP / WebSocket requests. Skip if not needed, it doesn't affect the use of other features.

ErisPulse provides a unified network client that aggregates HTTP requests, WebSocket connections, and connection pool management. Modules and adapters **must** use this client instead of directly importing third-party libraries such as `aiohttp`, `httpx`, or `requests`.

## Overview

The main functions of the network client are:

- **Unified interface**: Provides `get` / `post` / `put` / `delete` / `patch` / `request` methods
- **WebSocket client**: Establishes a client-side WebSocket connection via `ws_connect`
- **Automatic logging**: All requests are automatically logged and their statistics recorded
- **Lifecycle integration**: Each request triggers the `client.request` lifecycle event, and WS connections trigger the `client.ws.connect` event
- **Retry support**: Configurable automatic retry counts and intervals
- **Timeout control**: Independent connection and request timeouts
- **Connection pool reuse**: Connection pool management based on `aiohttp.ClientSession`
- **Exception system**: aiohttp exceptions are automatically converted to ErisPulse exceptions (ClientError system)

## Quick Start

### HTTP Requests

```python
from ErisPulse.Core import client

# GET request
resp = await client.get("https://httpbin.org/get")
data = await resp.json()
print(resp.status)  # 200

# POST request
resp = await client.post(
    "https://httpbin.org/post",
    json={"key": "value"},
)
data = await resp.json()
```

### WebSocket Connection

```python
from ErisPulse import client   # 2.10+ root import (ErisPulse.Core.client deep path is still compatible)

ws = await client.ws_connect("wss://example.com/ws")

async for text in ws.iter_text():
    await ws.send_text(f"Echo: {text}")
```

#### Outbound connections automatically join the pool (2.10+)

Connections established via `ws_connect` are **automatically registered** into the framework's connection pool (set `track=False` to disable):
They can be viewed via `connections.list(owner=...)` and broadcasted to; connections are automatically unregistered when closed or disconnected remotely;
**When modules are unloaded or adapters are stopped, the framework closes all outbound connections under their names**, preventing leaks.

```python
from ErisPulse import client, connections

ws = await client.ws_connect("wss://example.com/ws")
print(ws.id, ws.owner)   # Already registered: connection id and owner

# When the owner context is unavailable (e.g., tool thread callback), explicitly specify the owner so it can be automatically recycled on unload:
ws2 = await client.ws_connect("wss://example.com/ws2", owner="MyAdapter")
```

See [Connection Pool and Broadcasting](connections.md).

## HttpResponse

All request methods return an `HttpResponse` object:

```python
from ErisPulse.Core import client

resp = await client.get("https://httpbin.org/get")

resp.status       # int - HTTP status code (e.g., 200, 404)
resp.reason       # str | None - status description (e.g., "OK")
resp.headers      # response headers (case-insensitive)
resp.content_type # str | None - Content-Type
resp.url          # final URL (may change due to redirects)
resp.raw          # underlying native response object (currently aiohttp.ClientResponse)

# Read response body
body = await resp.read()       # bytes
text = await resp.text()       # str
data = await resp.json()       # parse JSON
text = await resp.text("gbk")  # specify encoding
```

## Request Methods

### GET

```python
from ErisPulse.Core import client

resp = await client.get(
    "https://api.example.com/users",
    params={"page": "1", "limit": "10"},
    headers={"Authorization": "Bearer token"},
)
```

### POST

```python
from ErisPulse.Core import client

# JSON request body
resp = await client.post(
    "https://api.example.com/users",
    json={"name": "Alice", "age": 30},
)

# Form request body
resp = await client.post(
    "https://api.example.com/login",
    data={"username": "admin", "password": "123"},
)

# Raw data
resp = await client.post(
    "https://api.example.com/upload",
    data=b"raw bytes",
    headers={"Content-Type": "application/octet-stream"},
)

# File upload (using files parameter, no need to import aiohttp)
# Format: {field name: file object/bytes/(filename, file)/(filename, file, content_type)}
resp = await client.post(
    "https://api.example.com/upload",
    data={"description": "avatar"},            # Optional: can carry regular form fields
    files={
        "file": ("photo.png", open("photo.png", "rb"), "image/png"),
    },
)

# Simplified syntax: directly pass file object
resp = await client.post(
    "https://api.example.com/upload",
    files={"file": open("photo.png", "rb")},
)

# Upload in-memory data directly (no need to write to disk)
import io

resp = await client.post(
    "https://api.example.com/upload",
    files={"file": ("data.txt", io.BytesIO(b"file content"), "text/plain")},
)
```

### PUT / DELETE / PATCH

```python
from ErisPulse.Core import client

resp = await client.put("https://api.example.com/users/1", json={"name": "Bob"})
resp = await client.delete("https://api.example.com/users/1")
resp = await client.patch("https://api.example.com/users/1", json={"age": 31})
```

### Generic request

```python
from ErisPulse.Core import client

resp = await client.request(
    "OPTIONS",
    "https://api.example.com/resource",
    headers={"Origin": "https://example.com"},
)
```

## Parameter Explanation

### HTTP Request Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `url` | `str` | Request URL |
| `params` | `dict[str, str]` | Query parameters (optional) |
| `headers` | `dict[str, str]` | Additional request headers (optional) |
| `data` | `Any` | Request body (form or raw data) (optional) |
| `json` | `Any` | JSON request body (optional) |
| `files` | `dict[str, Any]` | File upload fields (optional, automatically builds multipart/form-data) |
| `timeout` | `float` | Timeout for this request (seconds) (optional, overrides default value) |
| `max_retries` | `int` | Maximum retry attempts for this request (optional, overrides default value) |

### ws_connect Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `url` | `str` | WebSocket server URL |
| `headers` | `dict[str, str]` | Additional request headers (optional) |
| `heartbeat` | `float` | Heartbeat interval in seconds (optional) |

## Timeout and Retries

```python
from ErisPulse.Core import Client

# Create a client with custom timeouts
client = Client(
    timeout=60,           # Total request timeout 60s
    connect_timeout=5,    # Connection timeout 5s
    max_retries=3,        # Failures automatically retry 3 times
    retry_delay=2,        # Retry interval 2s
)

# Override timeout for a single request
resp = await client.get("https://slow-api.example.com/data", timeout=120)
```

> [!NOTE]
> The client class was renamed to `Client` starting from version 2.8.0 (`sdk.client` property name remains unchanged); the old name `HttpClient` is retained as a compatibility alias, so old code does not need modification.

## Custom Default Headers

```python
client = Client(
    headers={
        "Authorization": "Bearer token",
        "X-App-Id": "my-app",
    },
    user_agent="MyBot/1.0",
)
```

## Request Statistics

```python
from ErisPulse.Core import client

# View statistics
stats = client.stats
# {"total_requests": 42, "total_errors": 1, "total_bytes_sent": 0, "total_bytes_received": 0}

# Reset statistics
client.reset_stats()
```

## Lifecycle Events

### HTTP Request Events

The `client.request` event is triggered after each request completes, which can be used for monitoring:

```python
from ErisPulse.Core import lifecycle

@lifecycle.on("client.request")
async def on_request(event_data):
    print(f"{event_data['method']} {event_data['url']} -> {event_data['status']} ({event_data['elapsed']}s)")
```

### WebSocket Connection Events

The `client.ws.connect` event is triggered after each WebSocket connection is established:

```python
from ErisPulse.Core import lifecycle

@lifecycle.on("client.ws.connect")
async def on_ws_connect(event_data):
    print(f"WS Connection: {event_data['url']}")
```

## Context Management

```python
# As a context manager, automatically close the session
async with Client(timeout=30) as client:
    resp = await client.get("https://httpbin.org/get")
    data = await resp.json()
```

## WebSocket Client

Establish a WebSocket client connection via `client.ws_connect()`, returning a `ClientWebSocket` object. The client and server-side WebSocket share the same `WebSocketConnectionBase` base class, with identical send/receive/iter interfaces.

### Basic Usage

```python
from ErisPulse.Core import client

ws = await client.ws_connect("wss://example.com/ws", heartbeat=30)

await ws.send_text("Hello")
await ws.send_bytes(b"\x00\x01\x02")
await ws.send_json({"type": "ping"})
```

### Receiving Messages

#### Advanced Methods (Recommended)

Automatically filter message types, and throw `WebSocketDisconnect` on disconnection:

```python
from ErisPulse.Core import client
from ErisPulse.Core.Bases.errors import WebSocketDisconnect

ws = await client.ws_connect("wss://example.com/ws")

# Single message receive
text = await ws.receive_text()    # str
data = await ws.receive_bytes()   # bytes
obj = await ws.receive_json()     # dict / list

# Iterate receive (automatically stops on disconnection)
async for text in ws.iter_text():
    print(text)

async for data in ws.iter_bytes():
    print(data)

async for obj in ws.iter_json():
    print(obj)
```

#### Low-Level Methods

Use `receive()` and `iter_messages()` to handle raw message types, which allows distinguishing TEXT / BINARY / CLOSE / ERROR:

```python
from ErisPulse.Core import client
from ErisPulse.Core.Bases.websocket import WSMessage

ws = await client.ws_connect("wss://example.com/ws")

# Single message receive raw message
msg = await ws.receive()
# msg.type  -> WSMessage.TEXT / WSMessage.BINARY / WSMessage.CLOSE / WSMessage.ERROR
# msg.data  -> str | bytes | None

# Iterate raw messages (automatically stops on CLOSE/ERROR)
async for msg in ws.iter_messages():
    if msg.type == WSMessage.TEXT:
        print(f"Text: {msg.data}")
    elif msg.type == WSMessage.BINARY:
        print(f"Binary: {len(msg.data)} bytes")
```

### WSMessage

`WSMessage` is a unified WebSocket message type, independent of the underlying library:

| Property | Type | Description |
|----------|------|-------------|
| `type` | `str` | Message type: `WSMessage.TEXT` / `WSMessage.BINARY` / `WSMessage.CLOSE` / `WSMessage.ERROR` |
| `data` | `Any` | Message data |

### ClientWebSocket Properties

| Property | Type | Description |
|----------|------|-------------|
| `url` | `URL` | Connection URL |
| `headers` | `Headers` | Response headers |
| `closed` | `bool` | Whether the connection is closed |
| `raw` | `object` | Underlying native object (aiohttp.ClientWebSocketResponse) |

### Lifecycle Hooks

Consistent with `server-side WebSocketConnection`, supports `on_disconnect` and `on_error` callbacks:

```python
from ErisPulse.Core import client

ws = await client.ws_connect("wss://example.com/ws")

@ws.on_disconnect
async def handle_disconnect(ws, reason="unknown"):
    print(f"Connection disconnected: {reason}")

@ws.on_error
async def handle_error(ws, error=""):
    print(f"Connection error: {error}")
```

### Closing Connection

```python
await ws.close(code=1000, reason="Normal closure")
```

## Exception System

ErisPulse defines a unified exception hierarchy. Requests initiated via `sdk.client` will automatically convert underlying aiohttp exceptions into ErisPulse exceptions.

> **Backward Compatibility**: Old modules/adapters that directly use `aiohttp.ClientSession` are completely unaffected. Exception conversion only occurs when requests are initiated via `sdk.client`. Code that directly uses aiohttp still catches `aiohttp.ClientError` and other native exceptions. Both approaches can coexist.

### Exception Hierarchy

```
ErisPulseError
├── ClientError                  # Base class for all HTTP/WS client request exceptions
│   ├── ClientConnectionError    # Connection failed (DNS resolution failed, connection refused, network unreachable)
│   ├── ClientTimeoutError       # Connection timeout or request timeout
│   └── HTTPStatusError          # HTTP 4xx/5xx status code error
└── WebSocketError               # WebSocket exception base class
    └── WebSocketDisconnect      # WebSocket connection disconnected (common for both client and server)
```

### Exception Handling

```python
from ErisPulse.Core import client
from ErisPulse.Core.Bases.errors import (
    ClientError,
    ClientConnectionError,
    ClientTimeoutError,
    HTTPStatusError,
    WebSocketDisconnect,
    WebSocketError,
)

# HTTP request exception handling
try:
    resp = await client.get("https://api.example.com/data")
    data = await resp.json()
except ClientConnectionError:
    print("Unable to connect to the server")
except ClientTimeoutError:
    print("Request timeout")
except ClientError as e:
    print(f"Request failed: {e}")

# WebSocket exception handling
try:
    ws = await client.ws_connect("wss://example.com/ws")
    async for text in ws.iter_text():
        await ws.send_text(f"Echo: {text}")
except WebSocketDisconnect as e:
    print(f"Connection disconnected: code={e.code}, reason={e.reason}")
except WebSocketError as e:
    print(f"WebSocket error: {e}")
```

### Unified Exception Handling

Use `ClientError` to catch all HTTP/WS client request exceptions:

```python
from ErisPulse.Core.Bases.errors import ClientError

try:
    resp = await client.get("https://api.example.com/data")
except ClientError as e:
    print(f"Client error: {e}")
```

### HTTPStatusError

When you need to check the status code after a request and throw an exception, you can manually use:

```python
from ErisPulse.Core.Bases.errors import HTTPStatusError

resp = await client.get("https://api.example.com/data")
if resp.status >= 400:
    raise HTTPStatusError(resp.status, await resp.text())
```

## Using in Adapters

Adapters can use the global client or create their own client instance to send platform API requests:

```python
from ErisPulse.Core import client
from ErisPulse.Core.Bases import BaseAdapter
from ErisPulse.Core.Bases.errors import ClientError

class MyAdapter(BaseAdapter):
    async def call_api(self, endpoint, **params):
        try:
            resp = await client.post(
                f"https://api.platform.com/{endpoint}",
                json=params,
                headers={"Authorization": f"Bearer {self.token}"},
            )
            return await resp.json()
        except ClientError as e:
            self.logger.error(f"API call failed: {e}")
            raise
```

> You can also use `from ErisPulse import sdk` to access `sdk.client`, with the same effect.

## Best Practices

1. **Prefer the global client**: Use `from ErisPulse.Core import client` to get the global singleton for easier framework management and monitoring
2. **Avoid directly importing aiohttp**: Use `client` instead of `aiohttp.ClientSession` to allow future changes to the underlying implementation without code modification. Old code directly using aiohttp still works normally, and both approaches can coexist
3. **Use the ErisPulse exception system**: When using `sdk.client` for requests, catch `ClientError` instead of `aiohttp.ClientError` to ensure code independence from specific HTTP libraries. Old code using aiohttp directly is unaffected
4. **Set timeouts reasonably**: Set appropriate timeout values based on API response speed to avoid long blocking
5. **Use retry mechanisms**: Enable retries for unstable APIs to improve reliability
6. **Monitor request statistics**: Use `sdk.client.stats` or the `client.request` lifecycle event to monitor request situations
7. **Use advanced WebSocket methods**: Prefer advanced methods like `iter_text` / `iter_json`, and only use `iter_messages` when distinguishing message types is needed

## 路由

> 来源: `docs/en/advanced/router.md`（https://github.com/ErisPulse/ErisPulse/blob/main/docs/en/advanced/router.md）

# Router Manager

> [!TIP]
> **When to read this**: When you need HTTP/WebSocket/SSE routes (including connection pool broadcasting). Skip if not needed, as it does not affect the use of other features.

The ErisPulse Router Manager provides unified HTTP and WebSocket routing management, supporting multi-adapter route registration and lifecycle management. Underlyingly, it encapsulates an abstraction layer (currently FastAPI + Uvicorn).

## Overview

The main functions of the Router Manager are:

- **Decorator Routes**: Supports `@http` / `@get` / `@post` / `@put` / `@delete` / `@ws` decorators for quick registration.
- **Automatic Injection**: Route handlers do not need to import FastAPI types; the framework automatically injects the abstract object.
- **Route Grouping**: Supports `RouteGroup` with prefix and version number.
- **Route Middleware**: Supports request interception with glob pattern matching.
- **Rate Limiting**: Built-in sliding window rate limiting.
- **CORS Support**: One-click enable cross-origin resource sharing.
- **Security Headers**: Automatically adds security response headers.
- **Automatic Documentation**: Interactive documentation based on OpenAPI.
- **WebSocket Support**: Complete WebSocket connection management, custom authentication, and lifecycle hooks.
- **Lifecycle Integration**: Deeply integrated with the ErisPulse lifecycle system.
- **SSL/TLS Support**: Supports HTTPS and WSS secure connections.
- **Home Entry**: Supports modules registering quick entry buttons at the root route `/`, with internationalization support.

## Abstract Types

ErisPulse provides server-side abstraction types to allow modules to avoid direct dependencies on FastAPI:

| Abstract Type | FastAPI Correspondence | Description |
|---------------|------------------------|-------------|
| `HttpRequest` | `fastapi.Request` | HTTP request encapsulation, fully compatible interface |
| `WebSocketConnection` | `fastapi.WebSocket` | WebSocket connection encapsulation, additional lifecycle hooks provided |
| `WebSocketDisconnect` | `fastapi.WebSocketDisconnect` | WebSocket disconnection exception |

> `WebSocketConnection` inherits from `WebSocketConnectionBase`, sharing the same send/receive/iter/close interface with the client-side WebSocket (`ClientWebSocket`). The same business logic code can be used on both client and server.  
> The `.raw` attribute allows access to the underlying native FastAPI object. Code directly using FastAPI types is fully compatible.

## Decorator Routes (Recommended)

### Registration Forms: Single-Parameter (Recommended) and Dual-Parameter

Decorator routes support two forms, **single-parameter is recommended**—it aligns with command/event triggers, and the namespace is automatically assigned to the current module:

```python
from ErisPulse import router

# Single-parameter (Recommended): auto-assigns module_name/hello → actual path /my_module/hello
@router.get("/hello")
async def hello():
    return {"ok": True}

# Single-parameter WebSocket: @ws("chat") → /my_module/chat
@router.ws("chat")
async def chat(ws):
    ...

# Dual-parameter: explicitly specify module name (same rules, used when registering across modules/tool code)
@router.get("other_module", "/info")
async def get_info(request):
    return {"method": request.method, "path": str(request.url)}
```

> [!NOTE]
> The single-parameter form requires registration within the module/adapter **loading context** (the framework has injected the assignment during loading); calling it outside the context will raise a `ValueError` and prompt for explicit module name.

### HTTP Decorators

```python
from ErisPulse import router, HttpRequest

# You can also explicitly annotate with abstract types
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

> **Automatic Injection Rule**: When the handler's first parameter is named `request` or `req` and has no FastAPI type annotation, the framework automatically injects `HttpRequest`. Handlers without parameters or with non-request parameter names are unaffected.

#### Response Return Convention (2.10+)

Handler return values support a **tuple convention** (recommended syntax, clearly controlling status code), while dict/str/Response remain unchanged:

```python
@router.post("/login")
async def login(request):
    if not check_token(request):
        # (body, status_code) → 401 JSON
        return {"error": "unauthorized", "message": "token invalid"}, 401
    # (body, status_code, headers) can also include response headers
    return {"user_id": 1}, 200, {"X-Request-Cost": "12ms"}

# Or use the respond() helper function (message automatically merged into response body)
from ErisPulse import respond

@router.get("/me")
async def me():
    return respond({"user_id": 1}, status_code=200, message="ok")
```

Path/query parameters can be directly annotated using FastAPI native annotations (`item_id: int`, `page: int = 1`), and middleware is described in the [Route Middleware](#route-middleware) section.

### WebSocket Decorators

```python
from ErisPulse import WebSocketConnection, WebSocketDisconnect

# Basic WebSocket (single-parameter form)
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

# WebSocket with authentication
async def ws_auth(ws: WebSocketConnection) -> bool:
    token = ws.query_params.get("token")
    return token == "secret"

@router.ws("secure_ws", auth_handler=ws_auth)
async def secure_ws_handler(ws):
    while True:
        data = await ws.receive_text()
        await ws.send_text(f"Echo: {data}")
```

> **Note**: WebSocket handlers and authentication handlers also support automatic injection. You can obtain `WebSocketConnection` without parameter annotations. Passing in the native object with `fastapi.WebSocket` is also possible, but abstract types are recommended.

### Automatic Connection Registration (Connection Pool, 2.10+)

Connections established via `@ws` / `@sse` are **automatically registered** into the framework connection pool by default (`track=False` to disable):  
Within the handler, `ws.id` / `ws.join_group(...)` are available, and any module can use `connections.list(namespace=...)` to view connections of the current module and broadcast to groups.  
See [Connection Pool and Broadcasting](connections.md).

## Traditional Registration Methods

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

# With rate limiting and documentation information
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

**Parameter Description:**

| Parameter | Description | Default |
|-----------|-------------|---------|
| `module_name` | Module name (required) | - |
| `path` | WebSocket path | - |
| `handler` | Handler function | - |
| `auth_handler` | Authentication function, returns `False` to automatically close connection | `None` |
| `auto_accept` | Whether to automatically `accept()` | `True` |

> **Recommendation**: Use `auth_handler` for connection confirmation, rather than setting `auto_accept=False`. Only set `auto_accept=False` when you need complete control over the connection flow.

## WebSocket Lifecycle Hooks

`WebSocketConnection` provides callback registration for disconnection and errors, eliminating the need for manual try/catch:

```python
from ErisPulse.Core import WebSocketConnection

@router.ws("my_module", "/ws")
async def my_ws(ws: WebSocketConnection):
    # Decorator way to register
    @ws.on_disconnect
    async def on_close(ws, reason="unknown"):
        print(f"Disconnect reason: {reason}")

    # Can also be called directly
    async def on_err(ws, error=""):
        print(f"Error: {error}")
    ws.on_error(on_err)

    # Normal business logic
    async for msg in ws.iter_text():
        await ws.send_text(f"Echo: {msg}")
```

## Route Grouping

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

Middleware supports glob pattern matching paths:

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

Starting from 2.7.0, each HTTP request carries an `X-Request-ID` correlation ID for logging / trace linking:

- **Generation Rule**: Prioritizes using the `X-Request-ID` header from the client (for distributed tracing scenarios); otherwise, generates a UUID automatically
- **Response Header**: The response writes back the `X-Request-ID`, making it easy for the client to correlate requests with logs
- **Lifecycle Events**: The `server.request` and `server.response` event data include a new `request_id` field

```python
# Listen for request events in the module, linking requests-responses by request_id
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

Rate limiting format: `{count}/{time window}`, such as `10/minute`, `100/hour`.

## CORS Configuration

```python
router.setup_cors(
    allow_origins=["https://example.com"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```

It can also be configured via `config.toml`:

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

Automatically adds security headers such as `X-Content-Type-Options`, `X-Frame-Options`, `X-XSS-Protection`.

It can also be configured via `config.toml`:

```toml
[router.security]
enabled = true
```

## Automatic Documentation

The router enables OpenAPI interactive documentation by default:

```python
# Disable documentation
router.disable_docs()

# Customize documentation information
router.set_docs_info(
    title="My API",
    description="API documentation",
    version="1.0.0"
)
```

## Path Handling

Route paths are automatically prefixed with the module name to avoid conflicts:

```python
# Register path "/api" to module "my_module"
# Actual access path is "/my_module/api"
router.register_http_route("my_module", "/api", handler)
```

> [!WARNING]
> Route paths (including module name prefix) are **case-sensitive**. The module name's case in registration determines the actual path: if the module name is `Test`, registering `/api` results in the actual path being `/Test/api`; accessing `/test/api` will return 404.

## System Routes

The router manager automatically provides the following system routes:

### Health Check

```
GET /health
# Returns:
{"status": "ok", "service": "ErisPulse Router"}
```

### Root Page

```
GET /
# Returns ErisPulse brand page
```

The root route `/` displays the ErisPulse brand page, automatically detects Dashboard availability, and adds an entry button.

## Home Entry

The router manager allows external modules to register quick entry buttons on the root route `/`, making it easy for users to quickly access each module's management page.

### Register Entry

```python
# Simple registration
router.register_home_entry(
    name="My Dashboard",
    url="/mymodule/admin",
)

# Registration with icon (SVG)
router.register_home_entry(
    name="Console",
    url="/console",
    icon_svg='<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M4 17l6-6-6-6"/><path d="M12 19h8"/></svg>',
)

# Internationalization support (project i18n dictionary format)
router.register_home_entry(
    name={"i18n": "mymodule.home.entry", "default": "My Dashboard"},
    url="/mymodule/admin",
)
```

**Parameter Description:**

| Parameter | Type | Description | Required |
|-----------|------|-------------|----------|
| `name` | `str` / `dict` | Button display text; if a dictionary `{"i18n": "key", "default": "text"}` is provided, internationalization is used | Yes |
| `url` | `str` | Button link address | Yes |
| `icon_svg` | `str` | Optional SVG icon markup | No |

### Dashboard Auto-Registration

When `sdk.Dashboard` is detected as available, the router manager automatically adds a Dashboard button at the first position in the entry list, without requiring manual registration.

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

1. **Prefer abstract types**: Use `HttpRequest` / `WebSocketConnection` instead of `fastapi.Request` / `fastapi.WebSocket` to avoid hard dependencies
2. **Leverage automatic injection**: Name the first parameter of a handler `request` or `req` to obtain `HttpRequest` without any type annotation
3. **Prefer the single-parameter form**: In module loading contexts, prefer the single-parameter form (automatically assigned to the namespace); when registering in cross-module/utility code, explicitly pass the module name
4. **Use route grouping**: Use `group()` to organize multiple routes within the same module
5. **Security considerations**: Implement authentication mechanisms and security headers for sensitive operations
6. **Apply rate limiting appropriately**: Set rate limits for high-frequency endpoints
7. **Use lifecycle hooks**: Handle WebSocket exceptions via `@ws.on_disconnect` / `@ws.on_error` instead of manual try/catch
