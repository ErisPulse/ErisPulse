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
│   ├── ClientConnectionError       # Connection layer error: DNS resolution failed, connection refused, network unreachable
│   ├── ClientTimeoutError          # Request timeout
│   └── HTTPStatusError             # HTTP status code error (e.g., 4xx/5xx with raise_for_status)
├── WebSocketError                  # Base class for WebSocket exceptions (WS connection in Core/client)
│   └── WebSocketDisconnect         # WebSocket disconnected (common for both server and client)
├── ConnectionRegistryError         # Base class for connection registry exceptions (Core/connections, 2.10+)
│   ├── ConnectionNotFoundError     # Connection does not exist / has been disconnected/unregistered (connections.get/close)
│   └── ConnectionPermissionError   # Closing another's connection without owner permission (closing rights belong to creator)
├── StorageError                    # Base class for storage exceptions (Core/storage)
│   └── StorageUnreachableError     # Storage backend unreachable (retry exhausted: database unreachable/credentials error)
├── InteractionError                # Base class for interaction session exceptions (Core/Event/interaction)
│   ├── InteractionCancelled        # Pending wait/lease canceled (wait_reply upper layer returns None)
│   └── SessionOccupiedError        # Session mutual exclusion lease occupied (hold() acquisition failed)
├── ModuleError                     # Base class for module system exceptions (Core/module)
│   └── ModuleCallError             # Base class for module inter-call exceptions
│       ├── ModuleNotAvailableError # Target module not registered/unavailable/initialization failed (including lazy loading access)
│       ├── ServiceNotProvidedError # Target module did not declare this service (outside meta.services whitelist)
│       └── ModuleCallTimeoutError  # Called method execution timeout (default 30s)
├── ShadowError                     # Base class for shadow module exceptions (Core/shadow)
│   ├── ShadowStateError            # State mismatch: target not loaded/active shadow already exists/not bound shadow (start/dismiss)
│   ├── ShadowSourceError           # Shadow source unavailable: path does not exist/loader missing/loading failed (start)
│   └── ShadowPromoteError          # Promotion failed: shadow not registered/not loaded/loader has no snapshot/reload failed (promote)
└── StrictModeError                 # Strict mode fatal violation (aborts startup process, loaders/strict)
```

## Structured Attributes

After capturing an exception, you can read structured attributes (without parsing the message text):

| Exception | Attributes |
|---|---|
| `ClientError` (with subclasses) | `.url` Request URL, `.method` Request method, `.attempts` Number of attempts (when retries are exhausted) |
| `HTTPStatusError` | `.status` Status code, `.message` Response message |
| `WebSocketDisconnect` | `.code` Close code, `.reason` Close reason |
| `ConnectionNotFoundError` | `.connection_id` Connection ID searched for |
| `ConnectionPermissionError` | `.connection_id` Target connection ID, `.owner` Owner of the connection |
| `StorageUnreachableError` | `.backend` Backend name (sqlite/mysql/postgres), `.cooldown` Cool-down seconds |
| `ModuleCallError` (with subclasses) | `.module` Target module name, `.method` Target method name |
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

`sdk.client` / HTTP client and WebSocket client raise exceptions when initiating requests:

| Exception | Occurrence Location | Typical Scenario |
|-----------|---------------------|------------------|
| `ClientError` | Request wrapper layer | Other client errors (lower-level aiohttp exceptions have been converted) |
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

| Exception | Occurrence Location | Typical Scenario |
|-----------|---------------------|------------------|
| `WebSocketError` | WS send/receive methods | Connection closed, received unexpected message type, low-level WS exception |
| `WebSocketDisconnect` | WS send/receive methods | Peer disconnected normally (framework will automatically reconnect) |

### Connection Registry Series — `Core/connections.py` (2.10+)

| Exception | Occurrence Location | Typical Scenario |
|-----------|---------------------|------------------|
| `ConnectionNotFoundError` | `connections.get` / `assign` / `dismiss` / `close` | Connection ID does not exist or has been disconnected and unregistered |
| `ConnectionPermissionError` | Non-owner calls `conn.close()` | Closing someone else's connection across modules (sending and grouping are not restricted) |

### Storage Series — `Core/storage` / `Core/Bases/sql_base.py`

| Exception | Occurrence Location | Typical Scenario |
|-----------|---------------------|------------------|
| `StorageError` | Storage layer | Base class for storage-related exceptions |
| `StorageUnreachableError` | Pool creation phase | Database unreachable / credential error / network isolation, retry exhausted |

> **Failure semantics of storage operations**: KV and query operations **do not throw exceptions by default**—failures are logged as ERROR and return `False` / `None` / `default` (to avoid blocking the framework due to connection issues). Therefore, business code typically **does not** catch `StorageUnreachableError` (it is mainly used for direct storage layer operations or custom backends). To perceive connection status at runtime, subscribe to lifecycle events `storage.unreachable` / `storage.recovered` (see [Lifecycle Events](lifecycle.md#storage-connection-status)).

See [Storage Backend → Connection Failure Behavior](storage-backends.md#connection-failure-behavior) for details on handling connection failures.

### Interaction — `Core/Event/interaction.py`

`wait_reply` / session lease / reminder timer related:

| Exception | Occurrence Location | Typical Scenario |
|-----------|---------------------|------------------|
| `InteractionError` | Interaction session layer | Base class for interaction session exceptions |
| `InteractionCancelled` | When pending wait is cancelled | Set on the waiting future (the waiting part can catch and get `.reason`) |
| `SessionOccupiedError` | `hold()` lease acquisition failed | Session is already occupied by another owner (`.owner` can check the occupier) |

When waiting is cancelled (module unloading / platform shutdown / new wait replaces the same session), `wait_reply` **returns `None`** instead of throwing an exception (`InteractionCancelled` is internally converted); only directly catch it when distinguishing the reason for cancellation.

### Module Series — `Core/module.py` (`sdk.module.call`)

| Exception | Occurrence Location | Typical Scenario |
|-----------|---------------------|------------------|
| `ModuleError` | Module system | Base class for module system exceptions |
| `ModuleCallError` | `module.call()` | Base class for module call exceptions |
| `ModuleNotAvailableError` | `module.call()` / lazy-loaded attribute access | Target not registered / not enabled / initialization failed |
| `ServiceNotProvidedError` | `module.call()` | Target `meta.services` whitelist does not declare this method |
| `ModuleCallTimeoutError` | `module.call()` | Called coroutine exceeds timeout (default 30s) |

"Target module unavailable" exception types under different access paths:

| Access Path | Exception |
|-------------|-----------|
| `await sdk.module.call("X", "method")` | `ModuleNotAvailableError` (typed) |
| `sdk.module.X.attr` (lazy-loaded attribute access, after initialization failure) | `ModuleNotAvailableError` |
| `sdk.module.X` (module attribute access when module is not enabled) | `AttributeError` (Python attribute convention, `hasattr` relies on this semantics) |

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

| Exception | Occurrence Location | Typical Scenario |
|-----------|---------------------|------------------|
| `ShadowError` | Shadow module mechanism | Base class for shadow exceptions (catch all shadow errors) |
| `ShadowStateError` | `shadow_start()` / `dismiss_shadow()` | Target not loaded / active shadow exists / shadow not bound |
| `ShadowSourceError` | `shadow_start()` | Source path does not exist / plugin loader missing / source has no loadable class / loading failed |
| `ShadowPromoteError` | `promote_shadow()` | Shadow not registered / not loaded / loader does not support snapshot / promotion reload failed |

### Framework Internal Parameter Validation (ValueError)

Parameter validation for storage query builder (empty column types, `Insert` not dict, unsafe column types, etc.) throws standard `ValueError`—these are **development-time coding errors**, and normal business code should not catch them, but instead fix the calls.

Adaptor standard action failures **do not throw exceptions**: return a response dictionary with `retcode` (protocol semantics, e.g., `retcode=10002` means the action is not implemented)—this is a parallel error channel to client layer "failures throw `ClientError`", and adaptor development must handle both.

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