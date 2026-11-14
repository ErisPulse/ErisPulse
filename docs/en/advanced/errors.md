# Exception Hierarchy and Catching Guide

> [!NOTE]
> **L1 Core Must-Read** — one of the five core documents in the homepage "Reading Path", essential for module development.


All custom exceptions in ErisPulse inherit from `ErisPulseError`; underlying library exceptions (aiohttp, aiomysql, etc.) are caught inside the framework and converted into the corresponding ErisPulse exceptions — business code **does not need to depend on any underlying library exception types**.

{!--< tips >!--}
1. For a broad fallback: catch `ErisPulseError` (the base class of all framework exceptions)
2. For precise handling: catch per module (e.g., `ModuleCallTimeoutError`, `StorageOperationError`, `StorageUnreachableError`)
3. Storage write operation failures **throw by default** `StorageOperationError` (since 2.12); connection-level unreachability fast-fails during the cooldown period and still returns `False / None / default`; subscribe to `storage.unreachable` / `storage.recovered` events for connection state changes
{!--< /tips >!--}

## Exception Overview

```text
ErisPulseError                      # Base class of all framework exceptions
├── ClientError                     # HTTP/WS client request exception base class (Core/client)
│   ├── ClientConnectionError       # Connection-layer errors: DNS resolution failure, connection refused, network unreachable
│   ├── ClientTimeoutError          # Request timeout
│   └── HTTPStatusError             # HTTP status code error (e.g., 4xx/5xx with raise_for_status)
├── WebSocketError                  # WebSocket exception base class (WS connections of Core/client)
│   └── WebSocketDisconnect         # WebSocket disconnection (shared by server/client)
├── ConnectionRegistryError         # Connection registry exception base class (Core/connections, 2.10+)
│   ├── ConnectionNotFoundError     # Connection not found / already closed and deregistered (connections.get/close)
│   └── ConnectionPermissionError   # Non-owner closing another's connection (close right belongs to the creator)
├── StorageError                    # Storage exception base class (Core/storage)
│   ├── StorageOperationError       # Storage operation execution failure (thrown by default on write paths since 2.12)
│   └── StorageUnreachableError     # Storage backend unreachable (pool creation retries exhausted: database unreachable / wrong credentials)
├── InteractionError                # Interaction session exception base class (Core/Event/interaction)
│   ├── InteractionCancelled        # Pending wait/lease was cancelled (converted to returning None at the wait_reply layer)
│   └── SessionOccupiedError        # Session mutual-exclusion lease occupied (hold() acquisition failed)
├── ModuleError                     # Module system exception base class (Core/module)
│   └── ModuleCallError             # Inter-module call exception base class
│       ├── ModuleNotAvailableError # Target module not registered / not enabled / initialization failed (including lazy-load access)
│       ├── ServiceNotProvidedError # Target module did not declare this service (outside the meta.services whitelist)
│       └── ModuleCallTimeoutError  # Called method execution timed out (default 30s)
├── ShadowError                     # Shadow module exception base class (Core/shadow)
│   ├── ShadowStateError            # State not satisfied: target not loaded / active shadow already exists / no shadow bound (start/dismiss)
│   ├── ShadowSourceError           # Shadow source unavailable: path does not exist / loader missing / loading failed (start)
│   └── ShadowPromoteError          # Promotion failed: shadow not registered / not loaded / loader has no snapshot / reload failed (promote)
└── StrictModeError                 # Strict mode fatal violation (aborts startup, loaders/strict)
```

## Structured Attributes

After catching an exception, you can read structured attributes (no need to parse message text):

| Exception | Attributes |
|------|------|
| `ClientError` (including subclasses) | `.url` request URL, `.method` request method, `.attempts` number of attempts (when retries are exhausted) |
| `HTTPStatusError` | `.status` status code, `.message` response message |
| `WebSocketDisconnect` | `.code` close code, `.reason` close reason |
| `ConnectionNotFoundError` | `.connection_id` the connection id that was looked up |
| `ConnectionPermissionError` | `.connection_id` target connection id, `.owner` owner of the connection |
| `StorageUnreachableError` | `.backend` backend name (sqlite/mysql/postgres), `.cooldown` cooldown in seconds |
| `StorageOperationError` | `.operation` operation name (set/delete/clear/set_multi/transaction_begin), `.key` operation key |
| `ModuleCallError` (including subclasses) | `.module` target module name, `.method` target method name |
| `ModuleCallTimeoutError` | Inherits `.module/.method`, plus `.timeout` timeout limit (seconds) |
| `InteractionCancelled` | `.reason` cancellation reason, `.wait_key` session key |
| `SessionOccupiedError` | `.wait_key` session key, `.owner` occupier |
| `StrictModeError` | `.violations` list of violation records |

```python
from ErisPulse.Core.Bases.errors import ClientError

try:
    resp = await sdk.client.post(url, json=payload)
except ClientError as e:
    print(f"Request failed {e.method} {e.url}, {e.attempts} attempts in total: {e}")
```

## Exception Details and Where They Occur

### Client Series — `Core/client.py` / `Core/Bases/client.py`

Thrown when requests are made via `sdk.client` / the HTTP client and WebSocket client:

| Exception | Where It Occurs | Typical Scenario |
|------|----------|----------|
| `ClientError` | Request wrapper layer | Other client errors (underlying aiohttp exceptions already converted) |
| `ClientConnectionError` | Connection establishment phase | Target service unreachable, DNS failure, connection refused |
| `ClientTimeoutError` | Request execution phase | Request timeout exceeded |
| `HTTPStatusError` | `raise_for_status()` | Response status code is 4xx/5xx |

```python
from ErisPulse.Core.Bases.errors import ClientTimeoutError

try:
    resp = await sdk.client.get("https://api.example.com", timeout=5)
except ClientTimeoutError:
    ...
```

### WebSocket Series — `Core/client.py` (`send` / `receive`)

| Exception | Where It Occurs | Typical Scenario |
|------|----------|----------|
| `WebSocketError` | WS send/receive methods | Connection already closed, unexpected message type received, underlying WS exception |
| `WebSocketDisconnect` | WS send/receive methods | Peer disconnected normally (the framework will reconnect automatically) |

### Connection Registry Series — `Core/connections.py` (2.10+)

| Exception | Where It Occurs | Typical Scenario |
|------|----------|----------|
| `ConnectionNotFoundError` | `connections.get` / `assign` / `dismiss` / `close` | Connection id does not exist or has been closed and deregistered |
| `ConnectionPermissionError` | Non-owner calling `conn.close()` | Closing another module's connection across modules (sending and grouping are not restricted) |

### Storage Series — `Core/storage` / `Core/Bases/sql_base.py`

| Exception | Where It Occurs | Typical Scenario |
|------|----------|----------|
| `StorageError` | Storage layer | Base class of storage-related exceptions |
| `StorageOperationError` | KV write path / transaction begin (since 2.12) | Write lock contention timeout / SQL error / constraint conflict / transaction begin timeout — **thrown by default** |
| `StorageUnreachableError` | Pool creation phase | Database unreachable / wrong credentials / network isolation, retries exhausted |

> **Failure semantics of storage operations (layered since 2.12)**:
> - **Write path execution failures throw by default** `StorageOperationError` (`aset` / `adelete` / `aclear` / `set_multi`
>   and the same paths on the synchronous bridge) — the database being reachable but a write failing means the data was not written; silent returns would cause callers to lose data without noticing;
>   use try/except for important writes and perform compensation
> - **Connection-level unreachability** (cooldown-period fast fail) still returns `False` / `None` / `default` (framework resilience semantics);
>   business code usually will not catch `StorageUnreachableError`; to perceive connection state at runtime, subscribe to the lifecycle events
>   `storage.unreachable` / `storage.recovered` (see [Lifecycle Events](lifecycle.md#storage-connection-status))
> - **Transaction begin exceeding 30s** throws `StorageOperationError` (`STORAGE_TXN_BEGIN_TIMEOUT_SECS`) —
>   waiting indefinitely on concurrent long transactions is a framework defect and must be observable

For connection failure behavior, see [Storage Backends → Connection Failure Behavior](storage-backends.md#connection-failure-behavior).

### Interaction — `Core/Event/interaction.py`

Related to `wait_reply` / session leases / reminder timers:

| Exception | Where It Occurs | Typical Scenario |
|------|----------|----------|
| `InteractionError` | Interaction session layer | Base class of interaction session exceptions |
| `InteractionCancelled` | When a pending wait is cancelled | Set on the waiting future (the waiting side can catch it to get `.reason`) |
| `SessionOccupiedError` | `hold()` lease acquisition failed | Session already occupied by another owner (`.owner` can be checked for the occupier) |

When the wait is cancelled (module unload / platform shutdown / a new wait in the same session replaces it), `wait_reply` **returns `None`**
instead of raising an exception (`InteractionCancelled` is converted internally); catch it directly only when you need to distinguish cancellation reasons.

### Module Series — `Core/module.py` (`sdk.module.call`)

| Exception | Where It Occurs | Typical Scenario |
|------|----------|----------|
| `ModuleError` | Module system | Base class of module system exceptions |
| `ModuleCallError` | `module.call()` | Base class of inter-module call exceptions |
| `ModuleNotAvailableError` | `module.call()` / lazy-load attribute access | Target not registered / not enabled / initialization failed |
| `ServiceNotProvidedError` | `module.call()` | The target's `meta.services` whitelist does not declare this method |
| `ModuleCallTimeoutError` | `module.call()` | Called coroutine exceeded the timeout (default 30s) |

Exception types for "target module unavailable" under different access paths:

| Access Path | Exception |
|----------|------|
| `await sdk.module.call("X", "method")` | `ModuleNotAvailableError` (typed) |
| `sdk.module.X.attr` (lazy-load attribute access, after initialization failure) | `ModuleNotAvailableError` |
| `sdk.module.X` (attribute access when the module is not enabled) | `AttributeError` (Python attribute convention; `hasattr` relies on this semantics) |

```python
from ErisPulse.Core.Bases.errors import ModuleNotAvailableError, ServiceNotProvidedError

try:
    history = await sdk.module.call("Chat", "get_history", session_id, n=20)
except ModuleNotAvailableError:
    ...  # Target module does not exist / is not enabled
except ServiceNotProvidedError:
    ...  # Target module does not provide this service
```

### Shadow Series — `Core/shadow.py` (shadow modules)

| Exception | Where It Occurs | Typical Scenario |
|------|----------|----------|
| `ShadowError` | Shadow module mechanism | Base class of shadow exceptions (catch all shadow errors uniformly) |
| `ShadowStateError` | `shadow_start()` / `dismiss_shadow()` | Target not loaded / active shadow already exists / no shadow bound |
| `ShadowSourceError` | `shadow_start()` | Source path does not exist / plugin loader missing / no loadable class in the source / loading failed |
| `ShadowPromoteError` | `promote_shadow()` | Shadow not registered / not loaded / loader does not support snapshots / promotion reload failed |

### Framework Internal Parameter Validation (ValueError)

Parameter validation in the storage query builder (empty column types, `Insert` with non-dict, unsafe column types, etc.) raises the standard
`ValueError` — these are **development-time coding errors**; normal business code should not catch them, but should fix the call instead.

Adapter standard action failures **do not throw exceptions**: they return a response dict with a `retcode` (protocol semantics, e.g.,
`retcode=10002` means the action is not implemented) — this and the client layer's "failure throws `ClientError`" are two parallel
error channels, and adapter development must handle both.

## Catching Recommendations

```python
from ErisPulse.Core import ErisPulseError  # The base class is exported aggregated from Core

try:
    ...
except ErisPulseError as e:
    ...  # Unified fallback: all framework custom exceptions
```

- Module development: catch precisely as needed (see tables above); the outermost layer can fall back to `ErisPulseError`
- All exceptions are exported aggregated from `ErisPulse.Core` (including `SessionOccupiedError` / `InteractionCancelled` / `StrictModeError`), and can also be imported from `ErisPulse.Core.Bases.errors`
- For the complete definitions, see `src/ErisPulse/Core/Bases/errors.py`

## Shutdown Noise Folding

When long-running resident processes shut down (or when background loops are cancelled), the event loop often spews out a batch of worthless
interpreter noise like `Task was destroyed but it is pending!`. The framework has built-in **same-type noise folding**:
same-type messages within a 2-second window are downgraded to TRACE and merged with a count, output only once, ending with the
suffix "(N more same-type messages folded)". This is deliberate noise reduction — seeing the folding suffix does not mean
the framework swallowed real exceptions; business exceptions (all types in the tables above) are output in full as usual. Folding only targets interpreter exit noise;
business exceptions are unaffected. For what severity of exception deserves to be logged and what can be downgraded/folded, follow
[Engineering Robustness Rules · Exception Logging Severity](../styleguide/engineering.md#1-exception-logging-severity).

## Related Documents

Choose by troubleshooting intent:

- **Storage operations return `False` / `None` and you want to understand the connection state** → [Storage Backends · Connection Failure Behavior](storage-backends.md#connection-failure-behavior), or subscribe to the [storage.unreachable / storage.recovered events](lifecycle.md#storage-connection-status)
- **`wait_reply` returns `None` and you want to know what cancelled it** → [Interaction Session System](interaction.md) (cancellation reason comparison table)
- **`module.call` throws a module call exception** → [Inter-Module Communication](module-communication.md)
- **Connection / WebSocket errors** → [Network Client](client.md) (the ClientError hierarchy) and [Connection Pool and Broadcasting](connections.md) (connection registry exceptions)