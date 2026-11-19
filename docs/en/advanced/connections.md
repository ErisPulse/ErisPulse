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

## Related Documentation

- **Register server-side WS/SSE routes** → [Router Manager](router.md)
- **Establish client-side outbound WebSocket** → [Network Client](client.md)
- **How connections are recycled when modules are unloaded** → [Ownership (owner) System](ownership.md)
- **Connection-related exceptions (`ConnectionNotFoundError` / `ConnectionPermissionError`)** → [Exception System and Handling Guide](errors.md)