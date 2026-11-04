# Exception System and Catching Guide

> [!NOTE]
> **L1 Core Must-Read** — one of the five core documents in the homepage "Reading Path", essential for module development.

All custom exceptions in ErisPulse inherit from `ErisPulseError`; underlying library exceptions (aiohttp, aiomysql, etc.)
are caught inside the framework and converted into the corresponding ErisPulse exceptions — business code **does not need to depend on any underlying library exception types**.

{!--< tips >!--}
1. For a broad fallback: catch `ErisPulseError` (the base class of all framework exceptions)
2. For precise handling: catch per module (e.g., `ModuleCallTimeoutError`, `StorageUnreachableError`)
3. Storage operations do not raise by default: on failure they log and return `False / None / default`; subscribe to the `storage.unreachable` / `storage.recovered` events for connection status changes
{!--< /tips >!--}

## Exception Overview

```text
ErisPulseError                      # Base class of all framework exceptions
├── ClientError                     # HTTP/WS client request exception base class (Core/client)
│   ├── ClientConnectionError       # Connection-layer errors: DNS resolution failure, connection refused, network unreachable
│   ├── ClientTimeoutError          # Request timeout
│   └── HTTPStatusError             # HTTP status code errors (e.g., 4xx/5xx with raise_for_status)
├── WebSocketError                  # WebSocket exception base class (WS connections in Core/client)
│   └── WebSocketDisconnect         # WebSocket disconnection (common to server/client)
├── ConnectionRegistryError         # Connection registry exception base class (Core/connections, 2.10+)
│   ├── ConnectionNotFoundError     # Connection not found / disconnected and deregistered (connections.get/close)
│   └── ConnectionPermissionError   # Non-owner closing another's connection (close right belongs to the creator)
├── StorageError                    # Storage exception base class (Core/storage)
│   └── StorageUnreachableError     # Storage backend unreachable (pool-creation retries exhausted: database unreachable / wrong credentials)
├── InteractionError                # Interaction session exception base class (Core/Event/interaction)
│   ├── InteractionCancelled        # Pending wait/lease cancelled (converted to returning None by wait_reply upstream)
│   └── SessionOccupiedError        # Session exclusive lease occupied (hold() acquisition failed)
├── ModuleError                     # Module system exception base class (Core/module)
│   └── ModuleCallError             # Inter-module call exception base class
│       ├── ModuleNotAvailableError # Target module not registered / not enabled / initialization failed (incl. lazy-load access)
│       ├── ServiceNotProvidedError # Target module does not declare the service (outside the meta.services whitelist)
│       └── ModuleCallTimeoutError  # Called method execution timeout (default 30s)
├── ShadowError                     # Shadow module exception base class (Core/shadow)
│   ├── ShadowStateError            # State unmet: target not loaded / active shadow exists / no shadow bound (start/dismiss)
│   ├── ShadowSourceError           # Shadow source unavailable: path missing / loader missing / loading failed (start)
│   └── ShadowPromoteError          # Promotion failed: shadow not registered / not loaded / loader has no snapshot / reload failed (promote)
└── StrictModeError                 # Fatal strict-mode violation (aborts startup, loaders/strict)
```

## Structured Attributes

After catching an exception, you can read structured attributes (no need to parse message text):

| Exception | Attributes |
|------|------|
| `ClientError` (incl. subclasses) | `.url` request URL, `.method` request method, `.attempts` number of attempts made (when retries exhausted) |
| `HTTPStatusError` | `.status` status code, `.message` response message |
| `WebSocketDisconnect` | `.code` close code, `.reason` close reason |
| `ConnectionNotFoundError` | `.connection_id` the connection id that was looked up |
| `ConnectionPermissionError` | `.connection_id` target connection id, `.owner` the owner the connection belongs to |
| `StorageUnreachableError` | `.backend` backend name (sqlite/mysql/postgres), `.cooldown` cooldown seconds |
| `ModuleCallError` (incl. subclasses) | `.module` target module name, `.method` target method name |
| `ModuleCallTimeoutError` | Inherits `.module/.method`, plus `.timeout` timeout limit (seconds) |
| `InteractionCancelled` | `.reason` cancellation reason, `.wait_key` session key |
| `SessionOccupiedError` | `.wait_key` session key, `.owner` the occupier |
| `StrictModeError` | `.violations` list of violation records |

```python
from ErisPulse.Core.Bases.errors import ClientError

try:
    resp = await sdk.client.post(url, json=payload)
except ClientError as e:
    print(f"Request failed {e.method} {e.url}, {e.attempts} attempts in total: {e}")
```

## Exception Descriptions and Where They Occur

### Client Family — `Core/client.py` / `Core/Bases/client.py`

Raised when the `sdk.client` / HTTP client and WebSocket client make requests:

| Exception | Where It Occurs | Typical Scenarios |
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

### WebSocket Family — `Core/client.py` (`send` / `receive`)

| Exception | Where It Occurs | Typical Scenarios |
|------|----------|----------|
| `WebSocketError` | WS send/receive methods | Connection already closed, unexpected message type received, underlying WS exception |
| `WebSocketDisconnect` | WS send/receive methods | Peer normally disconnected (the framework will auto-reconnect) |

### Connection Registry Family — `Core/connections.py` (2.10+)

| Exception | Where It Occurs | Typical Scenarios |
|------|----------|----------|
| `ConnectionNotFoundError` | `connections.get` / `assign` / `dismiss` / `close` | Connection id does not exist or has been disconnected and deregistered |
| `ConnectionPermissionError` | Non-owner calling `conn.close()` | Closing another module's connection across modules (sending and grouping are not restricted) |

### Storage Family — `Core/storage` / `Core/Bases/sql_base.py`

| Exception | Where It Occurs | Typical Scenarios |
|------|----------|----------|
| `StorageError` | Storage layer | Storage-related exception base class |
| `StorageUnreachableError` | Pool creation phase | Database unreachable / wrong credentials / network isolation, retries exhausted |

> **Failure semantics of storage operations**: KV and query operations **do not raise by default** — on failure they log an ERROR entry and
> return `False` / `None` / `default` (to prevent connection issues from blocking framework operation). Therefore business code usually
> **will not** catch `StorageUnreachableError` (it is mainly for direct use on the storage internals or custom backends).
> To perceive connection status at runtime, subscribe to the lifecycle events `storage.unreachable` / `storage.recovered`
> (see [lifecycle events](lifecycle.md#storage-connection-status)).

For connection failure behavior, see [Storage Backends → Connection Failure Behavior](storage-backends.md#connection-failure-behavior).

### Interaction — `Core/Event/interaction.py`

Related to `wait_reply` / session leases / reminder timers:

| Exception | Where It Occurs | Typical Scenarios |
|------|----------|----------|
| `InteractionError` | Interaction session layer | Interaction session exception base class |
| `InteractionCancelled` | When a pending wait is cancelled | Set on the waiting future (the waiting side can catch it to get `.reason`) |
| `SessionOccupiedError` | `hold()` lease acquisition failed | Session already occupied by another owner (`.owner` reveals the occupier) |

When a wait is cancelled (module unload / platform shutdown / replaced by a new wait in the same session), `wait_reply` **returns `None`**
instead of raising an exception (`InteractionCancelled` is converted internally); only catch it directly when you need to distinguish cancellation reasons.

### Module Family — `Core/module.py` (`sdk.module.call`)

| Exception | Where It Occurs | Typical Scenarios |
|------|----------|----------|
| `ModuleError` | Module system | Module system exception base class |
| `ModuleCallError` | `module.call()` | Inter-module call exception base class |
| `ModuleNotAvailableError` | `module.call()` / lazy-load attribute access | Target not registered / not enabled / initialization failed |
| `ServiceNotProvidedError` | `module.call()` | The target's `meta.services` whitelist does not declare the method |
| `ModuleCallTimeoutError` | `module.call()` | The called coroutine exceeds the timeout (default 30s) |

Exception types for "target module unavailable" under different access paths:

| Access Path | Exception |
|----------|------|
| `await sdk.module.call("X", "method")` | `ModuleNotAvailableError` (typed) |
| `sdk.module.X.attr` (lazy-load attribute access, after initialization failure) | `ModuleNotAvailableError` |
| `sdk.module.X` (attribute access when the module is not enabled) | `AttributeError` (Python attribute convention, `hasattr` depends on this semantics) |

```python
from ErisPulse.Core.Bases.errors import ModuleNotAvailableError, ServiceNotProvidedError

try:
    history = await sdk.module.call("Chat", "get_history", session_id, n=20)
except ModuleNotAvailableError:
    ...  # Target module does not exist / is not enabled
except ServiceNotProvidedError:
    ...  # Target module does not provide this service
```

### Shadow Family — `Core/shadow.py` (shadow modules)

| Exception | Where It Occurs | Typical Scenarios |
|------|----------|----------|
| `ShadowError` | Shadow module mechanism | Shadow exception base class (catch all shadow errors uniformly) |
| `ShadowStateError` | `shadow_start()` / `dismiss_shadow()` | Target not loaded / an active shadow already exists / no shadow bound |
| `ShadowSourceError` | `shadow_start()` | Source path missing / plugin loader missing / no loadable class in source / loading failed |
| `ShadowPromoteError` | `promote_shadow()` | Shadow not registered / not loaded / loader does not support snapshots / promotion reload failed |

### Framework-Internal Parameter Validation (ValueError)

Parameter validation in the storage query builder (empty column types, non-dict `Insert`, unsafe column types, etc.) raises standard
`ValueError` — these are **development-time coding errors**; normal business code should not catch them but fix the call instead.

Adapter standard action failures **do not raise exceptions**: they return a response dict with `retcode` (protocol semantics, e.g.,
`retcode=10002` means the action is not implemented) — this and the client layer's "raise `ClientError` on failure" are two parallel
error channels; adapter development must handle both.

## Catching Recommendations

```python
from ErisPulse.Core import ErisPulseError  # Base class aggregated and re-exported from Core

try:
    ...
except ErisPulseError as e:
    ...  # Unified fallback: all framework custom exceptions
```

- Module development: catch precisely as needed (table above); the outermost layer can use `ErisPulseError` as a fallback
- All exceptions are aggregated and exported from `ErisPulse.Core` (including `SessionOccupiedError` / `InteractionCancelled` / `StrictModeError`); they can also be imported from `ErisPulse.Core.Bases.errors`
- For the full definitions see `src/ErisPulse/Core/Bases/errors.py`

## Shutdown Noise Folding

When long-running resident processes shut down (or background loops are cancelled), the event loop often flushes out a batch of worthless
interpreter noise such as `Task was destroyed but it is pending!`. The framework has built-in **same-type noise folding**:
same-type messages within a 2-second window are downgraded to TRACE and merged into a count, output only once, ending with
the "(N more similar messages folded)" suffix. This is deliberate noise reduction — seeing the folding suffix does not mean
the framework swallowed real exceptions; business exceptions (all types in the table above) are still output in full as usual. Folding targets only interpreter exit noise;
business exceptions are unaffected. For which level of exception deserves logging and which can be downgraded/folded, follow
[Engineering Robustness Rules · Exception Logging Classification](../styleguide/engineering.md#1-exception-logging-classification).

## Related Documents

Choose by troubleshooting intent:

- **Storage operations return `False` / `None` and you want to figure out connection status** → [Storage Backends · Connection Failure Behavior](storage-backends.md#connection-failure-behavior), or subscribe to the [storage.unreachable / storage.recovered events](lifecycle.md#storage-connection-status)
- **`wait_reply` returns `None` and you want to know what cancelled it** → [Interaction Session System](interaction.md) (cancellation reason reference table)
- **`module.call` raises a module call exception** → [Inter-Module Communication](module-communication.md)
- **Connection / WebSocket errors** → [Network Client](client.md) (the ClientError family) and [Connection Pool and Broadcast](connections.md) (connection registry exceptions)