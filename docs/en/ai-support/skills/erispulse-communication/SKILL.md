---
name: erispulse-communication
description: "适用于：模块间通信（RPC/定向/广播）、HTTP/WS 客户端、连接管理。覆盖场景：When you need cross-module calls (RPC), service contracts, directed events, or cold-start replay. Skip if not needed, as it won't affect the usage of other features.。When you need WebSocket/SSE connection pools, group subscriptions, cross-module push, or need to inspect connections. Skip otherwise, as it does not affect other features.。When you need outbound HTTP / WebSocket requests. Skip if not needed, as it does not affect other features.。When you need HTTP / WebSocket / SSE routing (including connection pool broadcasting). Skip if not needed, as it does not affect other features.。"
---

# ErisPulse 通信与连接

This skill is auto-built from the ErisPulse documentation.
Repository: https://github.com/ErisPulse/ErisPulse
Source paths are annotated per section; see docs/ in the repository for the latest content.

## 内容大纲

AI 按需读取：只读需要的章节即可，不必全文加载。

- 模块间通信: 68-94 行
- RPC: module.call: 96-123 行
- Service Contract: meta.services: 125-193 行
- Service Directory: services(): 195-213 行
- Outbound Audit: Who Can Call Whom: 215-229 行
- Directed Events: lifecycle.emit with to parameter: 231-257 行
- Lazy Loading and Invocation: 259-269 行
- Cold Start Replay: 271-299 行
- Event Idempotency Deduplication: 301-310 行
- 连接管理: 312-328 行
- Overview: 330-356 行
- Inspecting the Connection Pool: 358-381 行
- Broadcasting and Subscriptions: 383-444 行
- Cross-Module Transfer / Reuse: 446-465 行
- Outbound Connections (Client Side): 467-480 行
- Cross-Thread Delivery: 482-496 行
- Unload and Cleanup Semantics: 498-503 行
- API Overview: 505-519 行
- 网络客户端: 521-530 行
- Overview: 532-543 行
- Quick Start: 545-592 行
- HttpResponse: 594-615 行
- Request Methods: 617-700 行
- Parameter Descriptions: 702-723 行
- Timeout and Retry: 725-743 行
- Custom Default Headers: 745-755 行
- Request Statistics: 757-768 行
- Lifecycle Events: 770-794 行
- Context Management: 796-803 行
- WebSocket Client: 805-912 行
- Exception Hierarchy: 914-990 行
- Using in Adapters: 992-1015 行
- Best Practices: 1017-1025 行
- 路由: 1027-1036 行
- Overview: 1038-1053 行
- Abstract Types: 1055-1067 行
- Decorator-based Routing (Recommended): 1069-1187 行
- Traditional Registration Method: 1189-1254 行
- WebSocket Lifecycle Hooks: 1256-1278 行
- Route Grouping: 1280-1295 行
- Route Middleware: 1297-1312 行
- Request Correlation ID (X-Request-ID): 1314-1337 行
- Rate Limiting: 1339-1353 行
- CORS Configuration: 1355-1372 行
- Security Headers: 1374-1387 行
- Automatic Documentation: 1389-1403 行
- Path Handling: 1405-1416 行
- System Routes: 1418-1437 行
- Home Page Entry: 1439-1476 行
- Lifecycle Integration: 1478-1490 行
- Best Practices: 1492-1501 行

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

# Connection Pools and Broadcasting

> [!TIP]
> **When to read this**: When you need WebSocket/SSE connection pools, group subscriptions, cross-module push, or need to inspect connections. Skip otherwise, as it does not affect other features.

> **What you will learn**: How the three types of connections are automatically registered into the registry, group subscription and broadcast APIs, cross-module reuse and ownership, and the cleanup semantics for connections when modules are unloaded.
>
> **What this section does not cover**: WebSocket/SSE route registration and connection lifecycle hooks (see [Router Manager](router.md)); client-side HTTP requests (see [Network Client](client.md)).

Connections (server-side WebSocket/SSE / client-side outbound WebSocket) in ErisPulse are **first-class framework-level resources**: they are automatically registered into a unified registry upon establishment, support broadcasting, business group subscriptions, and cross-module reuse. When modules are unloaded, the framework automatically closes and recycles them—business logic no longer needs to maintain `_ws_clients` collections, and there is no risk of memory leaks due to forgotten cleanup.

> All examples in this document use **root import** syntax (recommended since 2.10):  
> `from ErisPulse import connections, router, client, WebSocketConnection`

## Overview

```python
from ErisPulse import connections, router, WebSocketConnection

# Server-side: connections are automatically registered, join business groups in handler
@router.ws("MyModule", "/ws")
async def handle(ws: WebSocketConnection):
    ws.join_group("room:1")            # Group naming is entirely business-defined
    async for msg in ws.iter_text():
        ...                             # Framework automatically unregisters and cleans up on disconnect

# Anywhere: broadcast to a group (returns detailed success/failure status)
result = await connections.broadcast({"type": "notify"}, group="room:1")
if not result.ok:
    ...                                 # result.failed: {connection id: exception}
```

All three connection types are registered into a unified registry:

| kind | source | owner | description |
|------|--------|-------|-------------|
| `server` | `@router.ws(...)` / `register_websocket(...)` | module name registering the route | automatically unregisters on disconnect |
| `sse` | `@router.sse(...)` / `register_sse(...)` | module name registering the route | broadcasting uses `sse.send()` |
| `client` | `await client.ws_connect(url)` | current module (or explicitly specified `owner=`) | automatically unregisters on close or remote disconnect; framework closes all connections when the adapter stops |

To disable automatic registration: pass `track=False` to the route, or pass `track=False` to outbound connections. This preserves behavior for legacy code.

## Inspecting the Connection Pool

```python
from ErisPulse import connections

# View the connection pool for a specific module ("how many active connections does this module have?")
conns = connections.list(namespace="Dashboard")
for conn in conns:
    print(conn.id, conn.kind, conn.groups, conn.meta)

# Filter by other dimensions (all conditions AND together)
connections.list(owner="MyAdapter", kind="client")
connections.list(group="tenant:acme")

# Global statistics (counts across all dimensions)
stats = connections.stats()
# {'total': 5, 'by_kind': {...}, 'by_namespace': {...}, 'by_owner': {...}, 'groups': {...}}

# Ownership audit counts (ownership facade is also visible)
from ErisPulse import ownership
ownership.counts("Dashboard")   # {'connections': 3, ...}
```

Each connection provides readable identity information: `conn.id` (e.g., `Dashboard:1a2b3c4d`), `conn.namespace`, `conn.owner`, `conn.kind`, `conn.groups`, and `conn.meta` (a business-defined dictionary).

## Broadcasting and Subscriptions

### Groups (Subscription Model)

Groups are **flat strings**; naming is entirely business-defined (rooms / tenants / topics...), with nested levels expressed through naming conventions (e.g., `tenant:acme/room:1`). The framework does not constrain the format.

Both directions are supported:

```python
# Direction 1: Connection-side active join/leave (inside handler)
@router.ws("Chat", "/ws")
async def handle(ws: WebSocketConnection):
    ws.join_group("room:1")        # Equivalent to connections.assign(ws.id, "room:1")
    ws.leave_group("room:1")

# Direction 2: Management-side passive assignment (from route side / other modules)
connections.assign(conn_id, "tenant:acme")
connections.dismiss(conn_id, "tenant:acme")   # Omit group name to leave all groups
```

Connections automatically leave all groups on disconnect, with no business cleanup required.

### Broadcasting

```python
result = await connections.broadcast(
    data,                       # For WS: uses send_json; for SSE: uses send (auto-serialized to JSON)
    namespace="Dashboard",      # Filter by namespace
    group="room:1",             # Filter by group
    kind="sse",                 # Filter by connection type
    owner="MyAdapter",          # Filter by owner
    ids={conn_id, ...},         # Explicitly specify candidate set (filter conditions still apply)
    exclude={conn_id},          # Exclude certain connections
    timeout=10.0,               # Timeout per connection (not total duration)
    concurrency=64,             # Maximum concurrent sends
    raise_on_error=False,       # If True, raises the first exception if any failures occur
)
result.total      # Total number of target connections (before exclusions)
result.sent       # List of successfully sent connection IDs
result.failed     # {connection id: exception object} (timeout/disconnected/send failure)
result.excluded   # Connection IDs that were excluded
result.ok         # Whether all messages were delivered
```

Filter conditions are combined with **AND**; failure of one does not affect others; connections in `ids` that no longer exist are counted in `failed` (to inform business logic of the full picture).

### Lifecycle Events

Events are emitted for registration/unregistration and group changes, allowing modules like Dashboard to subscribe for real-time updates:

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

Connections are framework-registered resources, and any module can retrieve and **reuse** them by connection ID—no need to recreate a new connection, and no need to know who created it:

```python
from ErisPulse import connections

conn = connections.get("Dashboard:1a2b3c4d")   # Throws ConnectionNotFoundError if not found or disconnected
await conn.send_json({"ping": 1})              # Any module can send
conn.join_group("someone-elses-room")          # Can also participate in groups
```

**Ownership and Close Rights**:

- The `owner` (module that created the connection) has exclusive close rights. Calling `close()` from a non-owner throws `ConnectionPermissionError` (import `ConnectionPermissionError` from ErisPulse);
- Sending and group operations are open to all modules, no authorization required;
- When the owner module unloads or the adapter stops, the framework **closes and unregisters** all connections owned by it (server-side and outbound), and any remaining references will result in failed sends; listening to the `connection.unregistered` event can detect this;
- Internal framework cleanup paths use `close(force=True)` to bypass checks.

> Attribution Note: Close permission checks rely on runtime owner context (`owner_scope` / event dispatch / `spawn_background` automatically carry context). Calls without context attribution (legacy code without attribution) are allowed, ensuring zero breaking changes; new code called within an owner context is protected.

## Outbound Connections (Client Side)

```python
from ErisPulse import client

ws = await client.ws_connect("wss://example.com/ws")
ws.id          # Already registered, can be queried and broadcasted via connections
ws.owner       # Current module (explicitly specify `owner=` if owner context is unavailable)

# Explicitly specify owner if owner context is unavailable (e.g., in tool thread callbacks), so it can be automatically recycled on unload:
ws = await client.ws_connect("wss://example.com/ws", owner="MyAdapter")
```

Remote disconnects or local `close()` will automatically unregister the connection; when modules are unloaded, the framework closes all their outbound connections. The era of old code managing connections manually and leaking them due to forgotten cleanup is over.

## Cross-Thread Delivery

To reach connections (broadcast / push / close) from a sub-thread, use the framework's standard tools to deliver back to the main loop—**do not manually use `run_coroutine_threadsafe`**:

```python
from ErisPulse import run_main_loop, spawn_later, spawn_thread

# Blockingly retrieve results from a sub-thread:
run_main_loop(connections.broadcast({"tick": 1}, group="room:1"), timeout=5)

# Background thread + delayed task (with owner attribution, automatically cancelled on unload):
def push_tick():
    return connections.broadcast({"tick": 1}, group="room:1")
spawn_later(30, push_tick, owner="MyModule")
```

## Unload and Cleanup Semantics

The ownership recycling chain during module unload or adapter stop proceeds as follows: cancel associated background tasks and timers → **close and unregister owned connections** → trigger the `on_cleanup` hook → unregister routes and handlers. See [Ownership (owner) System](ownership.md).

> [!WARNING]
> Since 2.10, module unload will close all registered WS/SSE/outbound connections under its name. Downstream components relying on "connections remaining alive after unload" (e.g., old Dashboard push) should be aware—this is the expected behavior to eliminate connection leaks.

## API Overview

| API | Description |
|-----|-------------|
| `connections.get(id)` | Retrieve a connection (cross-module entry point), throws `ConnectionNotFoundError` if not found |
| `connections.list(namespace=, owner=, group=, kind=)` | Filter and query connection lists |
| `connections.stats(namespace=, owner=)` | Count statistics across various dimensions |
| `connections.assign(id, *groups)` / `dismiss(id, *groups)` | Management-side join/leave groups |
| `await connections.broadcast(data, ...)` | Broadcast, returns `BroadcastResult` |
| `await connections.close(id, force=False)` | Close and unregister (with permission check) |
| `await connections.close_owner(owner)` | Close and unregister all connections owned by a specific owner (called by framework unload chain) |
| `conn.join_group(*groups)` / `conn.leave_group(*groups)` | Connection-side group operations |
| `conn.send_json / send_text / iter_text / ...` | Send/receive (server/client interface is consistent) |
| `conn.meta` | Business metadata dictionary |
| `conn.close(force=False)` | Close (throws `ConnectionPermissionError` for non-owner) |

## 网络客户端

> 来源: `docs/en/advanced/client.md`（https://github.com/ErisPulse/ErisPulse/blob/main/docs/en/advanced/client.md）

# Network Client

> [!TIP]
> **When to read this**: When you need outbound HTTP / WebSocket requests. Skip if not needed, as it does not affect other features.

ErisPulse provides a unified network client that aggregates HTTP requests, WebSocket connections, and connection pool management. Modules and adapters **must** use this client instead of directly importing third-party libraries such as `aiohttp` / `httpx` / `requests`.

## Overview

The main features of the network client are:

- **Unified interface**: Provides `get` / `post` / `put` / `delete` / `patch` / `request` methods
- **WebSocket client**: Establishes client WebSocket connections via `ws_connect`
- **Automatic logging**: All requests are automatically logged and statistics are recorded
- **Lifecycle integration**: Each request triggers the `client.request` lifecycle event; WebSocket connections trigger the `client.ws.connect` event
- **Retry support**: Configurable automatic retry count and interval
- **Timeout control**: Independent connection timeout and request timeout
- **Connection pool reuse**: Connection pool management based on `aiohttp.ClientSession`
- **Exception system**: `aiohttp` exceptions are automatically converted to ErisPulse exceptions (ClientError hierarchy)

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
from ErisPulse import client   # Root import from 2.10+ (ErisPulse.Core.client deep path still compatible)

ws = await client.ws_connect("wss://example.com/ws")

async for text in ws.iter_text():
    await ws.send_text(f"Echo: {text}")
```

#### Outbound Connections Auto-Registered in Pool (2.10+)

Connections established via `ws_connect` are **automatically registered** into the framework connection pool (set `track=False` to disable):
They can be viewed via `connections.list(owner=...)` and messages can be broadcast to them; connections are automatically unregistered upon closure or remote disconnection;
**All outbound connections under a module or adapter are uniformly closed by the framework when the module is unloaded or the adapter stops**, eliminating leaks.

```python
from ErisPulse import client, connections

ws = await client.ws_connect("wss://example.com/ws")
print(ws.id, ws.owner)   # Already registered: connection id and owner

# When owner context is unavailable (e.g., tool thread callback), explicitly specify the owner for automatic cleanup upon unload:
ws2 = await client.ws_connect("wss://example.com/ws2", owner="MyAdapter")
```

See [Connection Pool and Broadcasting](connections.md) for more details.

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
resp.raw          # raw underlying response object (currently aiohttp.ClientResponse)

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
    data={"description": "Avatar"},            # Optional: also carry regular form fields
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

## Parameter Descriptions

### HTTP Request Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `url` | `str` | Request URL |
| `params` | `dict[str, str]` | Query parameters (optional) |
| `headers` | `dict[str, str]` | Additional request headers (optional) |
| `data` | `Any` | Request body (form or raw data) (optional) |
| `json` | `Any` | JSON request body (optional) |
| `files` | `dict[str, Any]` | File upload fields (optional, automatically constructs multipart/form-data) |
| `timeout` | `float` | Request timeout (seconds) (optional, overrides default value) |
| `max_retries` | `int` | Maximum retry count for this request (optional, overrides default value) |

### ws_connect Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `url` | `str` | WebSocket server URL |
| `headers` | `dict[str, str]` | Additional request headers (optional) |
| `heartbeat` | `float` | Heartbeat interval in seconds (optional) |

## Timeout and Retry

```python
from ErisPulse.Core import Client

# Create a client with custom timeout settings
client = Client(
    timeout=60,           # Total request timeout 60s
    connect_timeout=5,    # Connection timeout 5s
    max_retries=3,        # Retry failed requests 3 times
    retry_delay=2,        # Retry interval 2s
)

# Override timeout for a single request
resp = await client.get("https://slow-api.example.com/data", timeout=120)
```

> [!NOTE]
> The client class was renamed to `Client` starting from version 2.8.0 (`sdk.client` property name remains unchanged); the old name `HttpClient` is retained as a compatibility alias, and old code does not need modification.

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

The `client.request` event is triggered after each request completes, useful for monitoring:

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
# As a context manager, automatically closes the session
async with Client(timeout=30) as client:
    resp = await client.get("https://httpbin.org/get")
    data = await resp.json()
```

## WebSocket Client

WebSocket client connections are established via `client.ws_connect()`, returning a `ClientWebSocket` object. The client and server WebSocket share the same `WebSocketConnectionBase` base class, with identical send/receive/iter interfaces.

### Basic Usage

```python
from ErisPulse.Core import client

ws = await client.ws_connect("wss://example.com/ws", heartbeat=30)

await ws.send_text("Hello")
await ws.send_bytes(b"\x00\x01\x02")
await ws.send_json({"type": "ping"})
```

### Receiving Messages

#### High-Level Methods (Recommended)

Automatically filter message types, and raise `WebSocketDisconnect` on disconnection:

```python
from ErisPulse.Core import client
from ErisPulse.Core.Bases.errors import WebSocketDisconnect

ws = await client.ws_connect("wss://example.com/ws")

# Single message receive
text = await ws.receive_text()    # str
data = await ws.receive_bytes()   # bytes
obj = await ws.receive_json()     # dict / list

# Iterate messages (automatically stops on disconnection)
async for text in ws.iter_text():
    print(text)

async for data in ws.iter_bytes():
    print(data)

async for obj in ws.iter_json():
    print(obj)
```

#### Low-Level Methods

Use `receive()` and `iter_messages()` to handle raw message types, distinguishing between TEXT / BINARY / CLOSE / ERROR:

```python
from ErisPulse.Core import client
from ErisPulse.Core.Bases.websocket import WSMessage

ws = await client.ws_connect("wss://example.com/ws")

# Single raw message receive
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
| `raw` | `object` | Underlying raw object (aiohttp.ClientWebSocketResponse) |

### Lifecycle Hooks

Consistent with `server-side WebSocketConnection`, supports `on_disconnect` and `on_error` callbacks:

```python
from ErisPulse.Core import client

ws = await client.ws_connect("wss://example.com/ws")

@ws.on_disconnect
async def handle_disconnect(ws, reason="unknown"):
    print(f"Connection closed: {reason}")

@ws.on_error
async def handle_error(ws, error=""):
    print(f"Connection error: {error}")
```

### Closing the Connection

```python
await ws.close(code=1000, reason="Normal closure")
```

## Exception Hierarchy

ErisPulse defines a unified exception hierarchy. Requests initiated via `sdk.client` automatically convert underlying `aiohttp` exceptions into ErisPulse exceptions.

> **Backward Compatibility**: Old modules/adapters that directly use `aiohttp.ClientSession` are unaffected. Exception conversion only occurs when requests are made via `sdk.client`. Code using `aiohttp` directly still catches `aiohttp.ClientError` and other native exceptions. Both approaches can coexist.

### Exception Hierarchy

```
ErisPulseError
├── ClientError                  # Base class for all HTTP/WS client request exceptions
│   ├── ClientConnectionError    # Connection failed (DNS resolution failed, connection refused, network unreachable)
│   ├── ClientTimeoutError       # Connection timeout or request timeout
│   └── HTTPStatusError          # HTTP 4xx/5xx status code errors
└── WebSocketError               # WebSocket exception base class
    └── WebSocketDisconnect      # WebSocket connection closed (common for client and server)
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
    print("Request timed out")
except ClientError as e:
    print(f"Request failed: {e}")

# WebSocket exception handling
try:
    ws = await client.ws_connect("wss://example.com/ws")
    async for text in ws.iter_text():
        await ws.send_text(f"Echo: {text}")
except WebSocketDisconnect as e:
    print(f"Connection closed: code={e.code}, reason={e.reason}")
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

When you need to check the status code after a request and raise an exception, you can manually use:

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

1. **Prefer the global client**: Use `from ErisPulse.Core import client` to obtain the global singleton, facilitating unified management and monitoring by the framework.
2. **Avoid directly importing aiohttp**: Use `client` instead of `aiohttp.ClientSession`, so future changes to the underlying implementation require no code changes. Old code using `aiohttp` directly still works normally, and both approaches can coexist.
3. **Use the ErisPulse exception hierarchy**: When using `sdk.client` for requests, catch `ClientError` instead of `aiohttp.ClientError` to ensure code independence from specific HTTP libraries. Old code using `aiohttp` directly remains unaffected.
4. **Set timeouts appropriately**: Set reasonable timeout values based on API response speed to avoid long blocking.
5. **Use retry mechanisms**: Enable retries for unstable APIs to improve reliability.
6. **Monitor request statistics**: Use `sdk.client.stats` or the `client.request` lifecycle event to monitor request status.
7. **Use high-level WebSocket methods**: Prefer high-level methods such as `iter_text` / `iter_json`, and only use `iter_messages` when distinguishing message types is necessary.

## 路由

> 来源: `docs/en/advanced/router.md`（https://github.com/ErisPulse/ErisPulse/blob/main/docs/en/advanced/router.md）

# Router Manager

> [!TIP]
> **When to read this**: When you need HTTP / WebSocket / SSE routing (including connection pool broadcasting). Skip if not needed, as it does not affect other features.

The ErisPulse Router Manager provides unified HTTP and WebSocket routing management, supporting multi-adapter route registration and lifecycle management. Underlyingly, it is encapsulated through an abstraction layer (currently FastAPI + Uvicorn).

## Overview

The main functions of the Router Manager are:

- **Decorator-based Routing**: Supports `@http` / `@get` / `@post` / `@put` / `@delete` / `@ws` decorators for quick registration
- **Automatic Injection**: Route handlers do not need to import FastAPI types; the framework automatically injects abstract objects
- **Route Grouping**: Supports `RouteGroup` with prefix and version number
- **Route Middleware**: Supports request interception with glob pattern matching
- **Rate Limiting**: Built-in sliding window rate limiting
- **CORS Support**: One-click enable Cross-Origin Resource Sharing
- **Security Headers**: Automatically adds security response headers
- **Automatic Documentation**: Interactive documentation based on OpenAPI
- **WebSocket Support**: Full WebSocket connection management, custom authentication, and lifecycle hooks
- **Lifecycle Integration**: Deeply integrated with ErisPulse lifecycle system
- **SSL/TLS Support**: Supports HTTPS and WSS secure connections
- **Home Page Entry**: Supports module registration of quick entry buttons on root route `/`, supports internationalization

## Abstract Types

ErisPulse provides server-side abstract types, allowing modules to avoid direct dependency on FastAPI:

| Abstract Type | FastAPI Equivalent | Description |
|---------------|--------------------|-------------|
| `HttpRequest` | `fastapi.Request` | HTTP request encapsulation, fully compatible interface |
| `WebSocketConnection` | `fastapi.WebSocket` | WebSocket connection encapsulation, additional lifecycle hooks |
| `WebSocketDisconnect` | `fastapi.WebSocketDisconnect` | WebSocket disconnect exception |

> `WebSocketConnection` inherits from `WebSocketConnectionBase`, sharing the same send/receive/iter/close interface with client-side WebSocket (`ClientWebSocket`). Both client and server-side WebSocket can use the same business logic code.
>
> The underlying FastAPI native object is accessible via the `.raw` property. Code directly using FastAPI types is fully compatible.

## Decorator-based Routing (Recommended)

### Registration Forms: Single Parameter (Recommended) vs. Double Parameter

Decorator-based routing supports two forms, **single parameter is recommended**—consistent with command/event triggers, namespace automatically belongs to the current module:

```python
from ErisPulse import router

# Single parameter (recommended): automatically belongs to module_name/hello → actual path /my_module/hello
@router.get("/hello")
async def hello():
    return {"ok": True}

# Single parameter WebSocket: @ws("chat") → /my_module/chat
@router.ws("chat")
async def chat(ws):
    ...

# Double parameter: explicitly specify module name (use when registering across modules/tool code)
@router.get("other_module", "/info")
async def get_info(request):
    return {"method": request.method, "path": str(request.url)}
```

> [!NOTE]
> Single parameter form requires registration within the module/adapter **loading context** (framework has injected the namespace during loading);
> Calling outside of the context will raise `ValueError` and prompt explicit passing of the module name.

### HTTP Decorators

```python
from ErisPulse import router, HttpRequest

# Also can explicitly annotate abstract types
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

Handler return values support **tuple convention** (recommended syntax, clearly controls status code), dict/str/Response as usual:

```python
@router.post("/login")
async def login(request):
    if not check_token(request):
        # (body, status_code) → 401 JSON
        return {"error": "unauthorized", "message": "token invalid"}, 401
    # (body, status_code, headers) can also include response headers
    return {"user_id": 1}, 200, {"X-Request-Cost": "12ms"}

# Or use respond() helper function (message automatically merged into response body)
from ErisPulse import respond

@router.get("/me")
async def me():
    return respond({"user_id": 1}, status_code=200, message="ok")
```

Path/query parameters can be directly annotated using FastAPI native annotations (`item_id: int`, `page: int = 1`), see [Route Middleware](#route-middleware) section for middleware.

### WebSocket Decorators

```python
from ErisPulse import WebSocketConnection, WebSocketDisconnect

# Basic WebSocket (single parameter form)
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

> **Note**: WebSocket handlers and authentication handlers also support automatic injection. `WebSocketConnection` is available without parameter annotation. Passing the native `fastapi.WebSocket` is also possible, but abstract types are recommended.

### Automatic Connection Registration (Connection Pool, 2.10+)

Connections established via `@ws` / `@sse` are **automatically registered** into the framework connection pool (set `track=False` to disable):
Within the handler, `ws.id` / `ws.join_group(...)` are available, and any module can
`connections.list(namespace=...)` view connections of the module and broadcast to groups.
See [Connection Pool and Broadcasting](connections.md).

## Traditional Registration Method

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

# With authentication (recommended)
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

**Parameter Explanation:**

| Parameter | Description | Default |
|-----------|-------------|---------|
| `module_name` | Module name (required) | - |
| `path` | WebSocket path | - |
| `handler` | Handler function | - |
| `auth_handler` | Authentication function, returning `False` will automatically close the connection | `None` |
| `auto_accept` | Whether to automatically `accept()` | `True` |

> **Recommendation**: Use `auth_handler` for connection confirmation, rather than setting `auto_accept=False`. Only set `auto_accept=False` when you need complete control over the connection flow.

## WebSocket Lifecycle Hooks

`WebSocketConnection` provides callback registration for disconnection and errors, eliminating the need for manual try/catch:

```python
from ErisPulse.Core import WebSocketConnection

@router.ws("my_module", "/ws")
async def my_ws(ws: WebSocketConnection):
    # Decorator-based registration
    @ws.on_disconnect
    async def on_close(ws, reason="unknown"):
        print(f"Disconnect reason: {reason}")

    # Can also call directly
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

Starting from 2.7.0, each HTTP request carries an `X-Request-ID` correlation ID for logging / distributed tracing:

- **Generation Rule**: Prioritizes using the `X-Request-ID` request header from the client (for distributed tracing scenarios); otherwise, generates a UUID
- **Response Header**: The response writes back `X-Request-ID`, allowing the client to correlate requests with logs
- **Lifecycle Events**: `server.request` and `server.response` event data include a new `request_id` field

```python
# Listen for request events in the module, chain requests-responses by request_id
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

Rate limiting is applied to routes using a sliding window algorithm:

```python
@router.get("my_module", "/limited", rate_limit="10/minute")
async def limited_endpoint(request):
    return {"ok": True}

@router.post("my_module", "/submit", rate_limit="5/minute")
async def submit_data(request):
    return {"submitted": True}
```

Rate limiting format: `{count}/{time window}`, e.g., `10/minute`, `100/hour`.

## CORS Configuration

```python
router.setup_cors(
    allow_origins=["https://example.com"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```

Alternatively, configure via `config.toml`:

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

Alternatively, configure via `config.toml`:

```toml
[router.security]
enabled = true
```

## Automatic Documentation

Router enables OpenAPI interactive documentation by default:

```python
# Disable documentation
router.disable_docs()

# Customize documentation information
router.set_docs_info(
    title="My API",
    description="API Documentation",
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
> Route paths (including module name prefix) are **case-sensitive**. The actual path matches the case of the registered module name: if the module name is `Test`, registering `/api` results in the actual path `/Test/api`, and accessing `/test/api` will return 404.

## System Routes

The Router Manager automatically provides the following system routes:

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

The root route `/` displays the ErisPulse brand page, automatically detects Dashboard availability, and adds entry buttons.

## Home Page Entry

The Router Manager allows external modules to register quick entry buttons on the root route `/`, making it easy for users to access management pages of various modules.

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

**Parameter Explanation:**

| Parameter | Type | Description | Required |
|-----------|------|-------------|----------|
| `name` | `str` / `dict` | Button display text; use internationalization when passing `{"i18n": "key", "default": "text"}` dictionary | Yes |
| `url` | `str` | Button link address | Yes |
| `icon_svg` | `str` | Optional SVG icon markup | No |

### Dashboard Automatic Registration

When `sdk.Dashboard` is detected as available, the Router Manager automatically adds a Dashboard button at the beginning of the entry list, without manual registration.

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

1. **Prefer Abstract Types**: Use `HttpRequest` / `WebSocketConnection` instead of `fastapi.Request` / `fastapi.WebSocket` to avoid hard dependencies
2. **Use Automatic Injection**: Name the first parameter of the handler `request` or `req` to automatically obtain `HttpRequest` without any type annotation
3. **Prefer Single Parameter Form**: In the module loading context, prefer the single parameter form (automatic namespace assignment); use explicit module name when registering across modules/tool code
4. **Use Route Grouping**: Use `group()` to organize multiple routes of the same module
5. **Security Consideration**: Implement authentication mechanisms and security headers for sensitive operations
6. **Reasonable Rate Limiting**: Set rate limiting for high-frequency interfaces
7. **Use Lifecycle Hooks**: Handle WebSocket exceptions through `@ws.on_disconnect` / `@ws.on_error` to avoid manual try/catch
