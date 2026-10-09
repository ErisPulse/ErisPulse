# Connection Pool and Broadcasting

Connections (server-side WebSocket / SSE / client-side outbound WebSocket) are **first-class resources at the framework level** in ErisPulse:  
They are automatically registered into a unified registry upon establishment, supporting broadcasting, business group subscription, and cross-module transfer/reuse. When a module is unloaded, the framework automatically closes and recovers them—business logic no longer needs to manually create `_ws_clients` collections, nor will memory leaks occur due to forgotten cleanup.

> The examples in this document use **root import** syntax (recommended for 2.10+):  
> `from ErisPulse import connections, router, client, WebSocketConnection`

## Overview

```python
from ErisPulse import connections, router, WebSocketConnection

# Server side: Connection is automatically registered; join business group in handler
@router.ws("MyModule", "/ws")
async def handle(ws: WebSocketConnection):
    ws.join_group("room:1")            # Group naming is entirely business-defined
    async for msg in ws.iter_text():
        ...                             # When disconnected, framework automatically unregisters and cleans up the group

# Anywhere: Broadcast to a group (returns success/failure details)
result = await connections.broadcast({"type": "notify"}, group="room:1")
if not result.ok:
    ...                                 # result.failed: {connection_id: exception}
```

All three types of connections enter the registry:

| kind | source | owner | description |
|------|--------|-------|-------------|
| `server` | `@router.ws(...)` / `register_websocket(...)` | module name that registered the route | automatically unregisters on disconnect |
| `sse` | `@router.sse(...)` / `register_sse(...)` | module name that registered the route | broadcasting uses `sse.send()` |
| `client` | `await client.ws_connect(url)` | current module (or explicitly `owner=`) | closes automatically on disconnect or adapter stop; framework closes all connections when adapter stops |

To disable automatic registration: pass `track=False` to the route, or pass `track=False` to outbound connections—the behavior of legacy code remains unchanged.

## Viewing the Connection Pool

```python
from ErisPulse import connections

# View the connection pool of a module ("how many live connections does this module currently have?")
conns = connections.list(namespace="Dashboard")
for conn in conns:
    print(conn.id, conn.kind, conn.groups, conn.meta)

# Filter by other dimensions (all conditions AND)
connections.list(owner="MyAdapter", kind="client")
connections.list(group="tenant:acme")

# Global statistics (counts across all dimensions)
stats = connections.stats()
# {'total': 5, 'by_kind': {...}, 'by_namespace': {...}, 'by_owner': {...}, 'groups': {...}}

# Ownership audit counts (ownership facade is also visible)
from ErisPulse import ownership
ownership.counts("Dashboard")   # {'connections': 3, ...}
```

Each connection has readable identity information: `conn.id` (e.g., `Dashboard:1a2b3c4d`), `conn.namespace`,  
`conn.owner`, `conn.kind`, `conn.groups`, `conn.meta` (business-defined dictionary).

## Broadcasting and Subscription

### Groups (Subscription Model)

Groups are **flat strings**, and naming is entirely business-defined (rooms / tenants / topics...),  
with nested levels expressed via naming conventions (e.g., `tenant:acme/room:1`); the framework does not constrain the format.

Both directions can be operated:

```python
# Direction 1: Connection side actively joins/leaves (inside handler)
@router.ws("Chat", "/ws")
async def handle(ws: WebSocketConnection):
    ws.join_group("room:1")        # Equivalent to connections.assign(ws.id, "room:1")
    ws.leave_group("room:1")

# Direction 2: Management side passively assigns (route side / other modules)
connections.assign(conn_id, "tenant:acme")
connections.dismiss(conn_id, "tenant:acme")   # If no group name is passed, leaves all groups
```

When a connection disconnects, it automatically leaves all groups; no business cleanup is required.

### Broadcasting

```python
result = await connections.broadcast(
    data,                       # For WS: send_json; for SSE: send (automatically JSON-serializes)
    namespace="Dashboard",      # Filter by namespace
    group="room:1",             # Filter by group
    kind="sse",                 # Filter by connection type
    owner="MyAdapter",          # Filter by owner
    ids={conn_id, ...},         # Explicitly specify candidate set (filter conditions still apply)
    exclude={conn_id},          # Exclude certain connections
    timeout=10.0,               # Timeout per connection (not total duration)
    concurrency=64,             # Maximum concurrent sends
    raise_on_error=False,       # If True, raises the first exception if there are failed items
)
result.total      # Number of target connections (before exclusions)
result.sent       # List of successfully sent connection IDs
result.failed     # {connection ID: exception object} (timeout/disconnected/send failed)
result.excluded   # Excluded connection IDs
result.ok         # Whether all were successfully delivered
```

Filter conditions are **AND**; failure of a single item does not affect others; connections in `ids` that no longer exist are counted in `failed` (so the business knows the full picture).

### Lifecycle Events

Lifecycle events are emitted for connection registration/unregistration/group changes, allowing Dashboard and others to subscribe for real-time display:

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

Connections are framework-registered resources; any module can retrieve and **reuse** them via connection ID—  
no need to create another one, nor to know who created the connection:

```python
from ErisPulse import connections

conn = connections.get("Dashboard:1a2b3c4d")   # Raises ConnectionNotFoundError if not exists or disconnected
await conn.send_json({"ping": 1})              # Any module can send
conn.join_group("someone-elses-room")          # Also can participate in groups
```

**Ownership and Closing Rights**:

- The `owner` (module that created the connection) exclusively holds closing rights. Non-owner calls to `close()` raise `ConnectionPermissionError` (`from ErisPulse import ConnectionPermissionError`);
- Sending and group operations are open to all modules, no authorization required;
- When the owner module is unloaded or the adapter stops, the framework **closes and unregisters** all its connections (server-side + outbound), and any remaining references will fail if used; listening to the `connection.unregistered` event allows detection;
- Internal framework recycling paths use `close(force=True)` to bypass checks.

> Attribution note: Closing rights rely on runtime owner context (`owner_scope` / event dispatch / `spawn_background` etc. automatically carry it). Calls without context (legacy code) are allowed to ensure 0-breaking changes; new code in owner context is protected.

## Outbound Connections (Client Side)

```python
from ErisPulse import client

ws = await client.ws_connect("wss://example.com/ws")
ws.id          # Registered, can be queried/broadcasted via connections
ws.owner       # Current module (suggest explicit `owner=` if owner context is unavailable)

# Explicitly specify owner if owner context is unavailable (e.g., in utility thread callbacks) for automatic cleanup on unload:
ws = await client.ws_connect("wss://example.com/ws", owner="MyAdapter")
```

Automatic unregistration occurs on remote disconnect or local `close()`. When a module is unloaded, the framework closes all its outbound connections. The era of old code manually managing connections and leaking due to forgotten cleanup is over.

## Cross-Thread Dispatching

To reach connections (broadcast / push / close) from a child thread, use the framework's standard tools to dispatch back to the main loop—**do not hand-write `run_coroutine_threadsafe`**:

```python
from ErisPulse import run_main_loop, spawn_later, spawn_thread

# Blocking result retrieval from a child thread:
run_main_loop(connections.broadcast({"tick": 1}, group="room:1"), timeout=5)

# Background thread + delayed task (with owner attribution, automatically canceled on unload):
def push_tick():
    return connections.broadcast({"tick": 1}, group="room:1")
spawn_later(30, push_tick, owner="MyModule")
```

## Unload and Cleanup Semantics

The ownership recovery chain on module unload / adapter stop will sequentially: cancel associated background tasks and timers → **close and unregister associated connections** → trigger `on_cleanup` hooks → unregister route/handler and other registered resources. See [Ownership (owner) System](ownership.md).

> [!WARNING]  
> Starting from 2.10, module unload will close all registered WS/SSE/outbound connections under its name. Downstream components relying on "connections remaining alive after unload" (e.g., old Dashboard push) must be aware—this is the expected behavior to prevent connection leaks.

## API Reference

| API | Description |
|-----|-------------|
| `connections.get(id)` | Get a connection (cross-module entry point), raises `ConnectionNotFoundError` if not exists |
| `connections.list(namespace=, owner=, group=, kind=)` | Filter and query connection list |
| `connections.stats(namespace=, owner=)` | Count statistics across all dimensions |
| `connections.assign(id, *groups)` / `dismiss(id, *groups)` | Management-side join/leave groups |
| `await connections.broadcast(data, ...)` | Broadcast, returns `BroadcastResult` |
| `await connections.close(id, force=False)` | Close and unregister (with permission check) |
| `await connections.close_owner(owner)` | Close and unregister all connections under a given owner (called by framework unload chain) |
| `conn.join_group(*groups)` / `conn.leave_group(*groups)` | Connection-side group operations |
| `conn.send_json / send_text / iter_text / ...` | Send/receive (server/client interface consistent) |
| `conn.meta` | Business metadata dictionary |
| `conn.close(force=False)` | Close (raises `ConnectionPermissionError` if not owner) |