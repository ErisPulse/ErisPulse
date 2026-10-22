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

## Related Documentation

- **Register Server-side WS/SSE Routes** → [Router Manager](router.md)
- **Establish Client-side Outbound WebSocket** → [Network Client](http-client.md)
- **How Connections Are Recycled When Modules Are Unloaded** → [Ownership (Owner) System](ownership.md)
- **Connection-Related Exceptions (`ConnectionNotFoundError` / `ConnectionPermissionError`)** → [Exception System and Handling Guide](errors.md)