# Exception System and Handling Guide

All custom exceptions in ErisPulse inherit from `ErisPulseError`. Underlying library exceptions (e.g., aiohttp, aiomysql, etc.) are caught and converted into corresponding ErisPulse exceptions within the framework — business code **does not need to rely on any underlying library exception types**.

{!--< tips >!--}
1. For broad fallback: catch `ErisPulseError` (the base class for all framework exceptions)
2. For precise handling: catch by module (e.g., `ModuleCallTimeoutError`, `StorageUnreachableError`)
3. Storage operations do not throw by default: failures are logged and `False / None / default` returned; subscribe to `storage.unreachable` / `storage.recovered` events for connection state changes
{!--< /tips >!--}

## Exception Overview

```text
ErisPulseError                      # Base class for all framework exceptions
├── ClientError                     # Base class for HTTP/WS client request exceptions (Core/client)
│   ├── ClientConnectionError       # Connection layer errors: DNS resolution failure, connection refused, unreachable network
│   ├── ClientTimeoutError          # Request timeout
│   └── HTTPStatusError             # HTTP status code errors (e.g., 4xx/5xx with raise_for_status)
├── WebSocketError                  # Base class for WebSocket exceptions (Core/client's WS connection)
│   └── WebSocketDisconnect         # WebSocket disconnection (common to server/client)
├── StorageError                    # Base class for storage exceptions (Core/storage)
│   └── StorageUnreachableError     # Storage backend unreachable (retry exhaustion: database unreachable/credential error)
├── InteractionError                # Base class for interaction session exceptions (Core/Event/interaction)
│   ├── InteractionCancelled        # Canceled pending wait/lease (wait_reply upper layer returns None)
│   └── SessionOccupiedError        # Session mutual exclusion lease occupied (hold() acquisition failed)
├── ModuleError                     # Base class for module system exceptions (Core/module)
│   └── ModuleCallError             # Base class for module call exceptions
│       ├── ModuleNotAvailableError # Target module not registered/unavailable/initialization failed (including lazy loading access)
│       ├── ServiceNotProvidedError # Target module did not declare the service (outside meta.services whitelist)
│       └── ModuleCallTimeoutError  # Target method execution timeout (default 30s)
├── ShadowError                     # Base class for shadow module exceptions (Core/shadow)
│   ├── ShadowStateError            # State mismatch: target not loaded/active shadow exists/unbound shadow (start/dismiss)
│   ├── ShadowSourceError           # Unavailable shadow source: path does not exist/loader missing/loading failed (start)
│   └── ShadowPromoteError          # Promotion failed: shadow not registered/loaded/loader no snapshot/reload failed (promote)
└── StrictModeError                 # Strict mode fatal violation (halts startup process, loaders/strict)
```

## Structured Properties

After catching an exception, you can read structured properties (no need to parse message text):

| Exception | Property |
|-----------|----------|
| `ClientError` (including subclasses) | `.url` Request URL, `.method` Request method, `.attempts` Number of attempts (when retries exhausted) |
| `HTTPStatusError` | `.status` Status code, `.message` Response message |
| `WebSocketDisconnect` | `.code` Close code, `.reason` Close reason |
| `StorageUnreachableError` | `.backend` Backend name (sqlite/mysql/postgres), `.cooldown` Cool-down seconds |
| `ModuleCallError` (including subclasses) | `.module` Target module name, `.method` Target method name |
| `ModuleCallTimeoutError` | Inherits `.module/.method`, also has `.timeout` Timeout limit (seconds) |
| `InteractionCancelled` | `.reason` Cancellation reason, `.wait_key` Session key |
| `SessionOccupiedError` | `.wait_key` Session key, `.owner` Occupier |
| `StrictModeError` | `.violations` List of violation records |

```python
from ErisPulse.Core.Bases.errors import ClientError

try:
    resp = await sdk.client.post(url, json=payload)
except ClientError as e:
    print(f"Request failed {e.method} {e.url}, attempted {e.attempts} times: {e}")
```

## Exception Descriptions and Occurrence Locations

### Client Series — `Core/client.py` / `Core/Bases/client.py`

Thrown when `sdk.client` or HTTP/WebSocket clients initiate requests:

| Exception | Occurrence Location | Typical Scenarios |
|-----------|---------------------|-------------------|
| `ClientError` | Request encapsulation layer | Other client errors (underlying aiohttp exceptions are converted) |
| `ClientConnectionError` | Connection establishment phase | Target service unreachable, DNS failure, connection refused |
| `ClientTimeoutError` | Request execution phase | Exceeded request timeout |
| `HTTPStatusError` | `raise_for_status()` | Response status code is 4xx/5xx |

```python
from ErisPulse.Core.Bases.errors import ClientTimeoutError

try:
    resp = await sdk.client.get("https://api.example.com", timeout=5)
except ClientTimeoutError:
    ...
```

### WebSocket Series — `Core/client.py` (`send` / `receive`)

| Exception | Occurrence Location | Typical Scenarios |
|-----------|---------------------|-------------------|
| `WebSocketError` | WS send/receive methods | Connection closed, unexpected message type received, underlying WS exception |
| `WebSocketDisconnect` | WS send/receive methods | Peer disconnected normally (framework will auto-reconnect) |

### Storage Series — `Core/storage` / `Core/Bases/sql_base.py`

| Exception | Occurrence Location | Typical Scenarios |
|-----------|---------------------|-------------------|
| `StorageError` | Storage layer | Base class for storage-related exceptions |
| `StorageUnreachableError` | Pool creation phase | Database unreachable/credential error/network isolation, retries exhausted |

> **Failure semantics for storage operations**: KV and query operations **do not throw by default** — failures are logged as ERROR and `False` / `None` / `default` returned (to avoid blocking framework execution due to connection issues). Therefore, business code typically **does not** catch `StorageUnreachableError` (it is mainly for direct storage layer operations or custom backends). For runtime connection state awareness, subscribe to lifecycle events `storage.unreachable` / `storage.recovered` (see [Lifecycle Events](lifecycle.md#storage-connection-status)).

See [Storage Backend → Connection Failure Behavior](storage-backends.md#connection-failure-behavior) for details on connection failure behavior.

### Interaction — `Core/Event/interaction.py`

Related to `wait_reply` / session leases / reminder timers:

| Exception | Occurrence Location | Typical Scenarios |
|-----------|---------------------|-------------------|
| `InteractionError` | Interaction session layer | Base class for interaction session exceptions |
| `InteractionCancelled` | When pending wait is canceled | Set on the waiting future (the waiting coroutine can catch and get `.reason`) |
| `SessionOccupiedError` | `hold()` lease acquisition failed | Session already occupied by another owner (`.owner` reveals the occupier) |

When a wait is canceled (module unloading / platform shutdown / new wait in same session replaces it), `wait_reply` **returns `None`** instead of throwing an exception (`InteractionCancelled` is converted internally). Only when distinguishing the reason for cancellation should you directly catch it.

### Module Series — `Core/module.py` (`sdk.module.call`)

| Exception | Occurrence Location | Typical Scenarios |
|-----------|---------------------|-------------------|
| `ModuleError` | Module system | Base class for module system exceptions |
| `ModuleCallError` | `module.call()` | Base class for module call exceptions |
| `ModuleNotAvailableError` | `module.call()` / lazy loading attribute access | Target not registered / not enabled / initialization failed |
| `ServiceNotProvidedError` | `module.call()` | Target `meta.services` whitelist did not declare the method |
| `ModuleCallTimeoutError` | `module.call()` | Target coroutine exceeds timeout (default 30s) |

"Target module unavailable" exceptions under different access paths:

| Access Path | Exception |
|-------------|-----------|
| `await sdk.module.call("X", "method")` | `ModuleNotAvailableError` (typed) |
| `sdk.module.X.attr` (lazy loading attribute access, after initialization failure) | `ModuleNotAvailableError` |
| `sdk.module.X` (attribute access when module is not enabled) | `AttributeError` (Python attribute convention, `hasattr` relies on this semantics) |

```python
from ErisPulse.Core.Bases.errors import ModuleNotAvailableError, ServiceNotProvidedError

try:
    history = await sdk.module.call("Chat", "get_history", session_id, n=20)
except ModuleNotAvailableError:
    ...  # Target module does not exist / is not enabled
except ServiceNotProvidedError:
    ...  # Target module does not provide this service
```

### Shadow Series — `Core/shadow.py` (Shadow Modules)

| Exception | Occurrence Location | Typical Scenarios |
|-----------|---------------------|-------------------|
| `ShadowError` | Shadow module mechanism | Base class for all shadow errors (catch all shadow errors) |
| `ShadowStateError` | `shadow_start()` / `dismiss_shadow()` | Target not loaded / active shadow exists / unbound shadow |
| `ShadowSourceError` | `shadow_start()` | Source path does not exist / plugin loader missing / source has no loadable class / loading failed |
| `ShadowPromoteError` | `promote_shadow()` | Shadow not registered / not loaded / loader does not support snapshot / promotion reload failed |

### Framework Internal Parameter Validation (ValueError)

Parameter validation for storage query builders (empty column types, `Insert` not dict, unsafe column types, etc.) throws standard `ValueError` — these are **development-time coding errors**, and normal business code should not catch them, but instead correct the calls.

Adapter standard action failures **do not throw exceptions**: return a response dictionary with `retcode` (protocol semantics, e.g., `retcode=10002` indicates the action is not implemented) — this is a parallel error channel to the client layer's "failures throw `ClientError`". Adapter development must handle both.

## Handling Recommendations

```python
from ErisPulse.Core import ErisPulseError  # Base class is aggregated and exported from Core

try:
    ...
except ErisPulseError as e:
    ...  # Unified fallback: all framework custom exceptions
```

- For module development: catch as needed (see table above), use `ErisPulseError` as a fallback at the outermost layer
- All exceptions are aggregated and exported from `ErisPulse.Core` (including `SessionOccupiedError` / `InteractionCancelled` / `StrictModeError`), also available from `ErisPulse.Core.Bases.errors`
- Full definitions are in `src/ErisPulse/Core/Bases/errors.py`

## Shutdown Noise Folding

Long-running processes often generate a batch of unactionable `Task was destroyed but it is pending!`-like interpreter noise when shutting down (or background loops are canceled). The framework includes **noise folding for similar messages**: within a 2-second window, identical messages are downgraded to TRACE and merged with a count, outputting only once, followed by a suffix indicating "another N similar messages were folded." This is deliberate noise reduction — seeing the folding suffix does not mean the framework swallowed real exceptions; business exceptions (all types above) are still fully output.