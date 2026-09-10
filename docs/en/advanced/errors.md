# Exception System and Handling Guide

All custom exceptions in ErisPulse inherit from `ErisPulseError`. Underlying library exceptions (e.g., aiohttp, aiomysql, etc.) are captured internally and converted to corresponding ErisPulse exceptions—business code **does not need to rely on any underlying library exception types**.

{!--< tips >!--}
1. For broad error handling: catch `ErisPulseError` (base class for all framework exceptions)
2. For precise handling: catch by module (e.g., `ModuleCallTimeoutError`, `StorageUnreachableError`)
3. Storage operations do not throw by default: log failures and return `False / None / default`; subscribe to `storage.unreachable` / `storage.recovered` events for connection state changes
{!--< /tips >!--}

## Exception Overview

```text
ErisPulseError                      # Base class for all framework exceptions
├── ClientError                     # Base class for HTTP/WS client request exceptions (Core/client)
│   ├── ClientConnectionError       # Connection layer errors: DNS resolution failed, connection refused, network unreachable
│   ├── ClientTimeoutError          # Request timeout
│   └── HTTPStatusError             # HTTP status code errors (e.g., 4xx/5xx with raise_for_status)
├── WebSocketError                  # Base class for WebSocket exceptions (Core/client WS connections)
│   └── WebSocketDisconnect         # WebSocket disconnected (common to both server and client)
├── StorageError                    # Base class for storage exceptions (Core/storage)
│   └── StorageUnreachableError     # Storage backend unreachable (retry exhaustion: database unreachable/credential error)
├── InteractionError                # Base class for interaction session exceptions (Core/Event/interaction)
│   ├── InteractionCancelled        # Canceled pending wait/lease (wait_reply upper layer returns None)
│   └── SessionOccupiedError        # Session exclusive lease occupied (hold() acquisition failed)
├── ModuleError                     # Base class for module system exceptions (Core/module)
│   └── ModuleCallError             # Base class for module call exceptions
│       ├── ModuleNotAvailableError # Target module not registered/unavailable/initialization failed (including lazy loading access)
│       ├── ServiceNotProvidedError # Target module did not declare this service (outside meta.services whitelist)
│       └── ModuleCallTimeoutError  # Called method execution timeout (default 30s)
└── StrictModeError                 # Fatal violation in strict mode (halts startup process, loaders/strict)
```

## Structured Properties

After catching an exception, you can read structured properties (no need to parse message text):

| Exception | Properties |
|-----------|------------|
| `ClientError` (and subclasses) | `.url` Request URL, `.method` Request method, `.attempts` Number of attempts (when retries exhausted) |
| `HTTPStatusError` | `.status` Status code, `.message` Response message |
| `WebSocketDisconnect` | `.code` Close code, `.reason` Close reason |
| `StorageUnreachableError` | `.backend` Backend name (sqlite/mysql/postgres), `.cooldown` Cool-down seconds |
| `ModuleCallError` (and subclasses) | `.module` Target module name, `.method` Target method name |
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

Thrown when `sdk.client` / HTTP client and WebSocket client initiate requests:

| Exception | Location | Typical Scenario |
|-----------|----------|------------------|
| `ClientError` | Request encapsulation layer | Other client errors (underlying aiohttp exceptions already converted) |
| `ClientConnectionError` | Connection establishment phase | Target service unreachable, DNS failure, connection refused |
| `ClientTimeoutError` | Request execution phase | Exceeds request timeout |
| `HTTPStatusError` | `raise_for_status()` | Response status code is 4xx/5xx |

```python
from ErisPulse.Core.Bases.errors import ClientTimeoutError

try:
    resp = await sdk.client.get("https://api.example.com", timeout=5)
except ClientTimeoutError:
    ...
```

### WebSocket Series — `Core/client.py` (`send` / `receive`)

| Exception | Location | Typical Scenario |
|-----------|----------|------------------|
| `WebSocketError` | WS send/receive methods | Connection closed, received unexpected message type, underlying WS exception |
| `WebSocketDisconnect` | WS send/receive methods | Peer disconnected normally (framework will auto-reconnect) |

### Storage Series — `Core/storage` / `Core/Bases/sql_base.py`

| Exception | Location | Typical Scenario |
|-----------|----------|------------------|
| `StorageError` | Storage layer | Base class for storage-related exceptions |
| `StorageUnreachableError` | Pool creation phase | Database unreachable / credential error / network isolation, retry exhausted |

> **Failure semantics for storage operations**: KV and query operations **do not throw by default**—failures log ERROR and return `False` / `None` / `default` (to avoid blocking framework operation due to connection issues). Thus, business code usually **does not** catch `StorageUnreachableError` (it is mainly used for direct storage layer operations or custom backends). For runtime connection state awareness, subscribe to lifecycle events `storage.unreachable` / `storage.recovered` (see [Lifecycle Events](lifecycle.md#storage-connection-status)).

See [Storage Backend → Connection Failure Behavior](storage-backends.md#connection-failure-behavior) for details on connection failure behavior.

### Interaction — `Core/Event/interaction.py`

Related to `wait_reply` / session lease / reminder timer:

| Exception | Location | Typical Scenario |
|-----------|----------|------------------|
| `InteractionError` | Interaction session layer | Base class for interaction session exceptions |
| `InteractionCancelled` | When pending wait is canceled | Set on the waiting future (the waiting code can catch and get `.reason`) |
| `SessionOccupiedError` | `hold()` lease acquisition failed | Session already occupied by another owner (`.owner` can check the occupier) |

When wait is canceled (module unload / platform shutdown / new wait in same session replaces it), `wait_reply` **returns `None`** instead of throwing an exception (`InteractionCancelled` is internally converted); only catch it directly when distinguishing the cancellation reason is needed.

### Module Series — `Core/module.py` (`sdk.module.call`)

| Exception | Location | Typical Scenario |
|-----------|----------|------------------|
| `ModuleError` | Module system | Base class for module system exceptions |
| `ModuleCallError` | `module.call()` | Base class for module call exceptions |
| `ModuleNotAvailableError` | `module.call()` / lazy loading attribute access | Target not registered / disabled / initialization failed |
| `ServiceNotProvidedError` | `module.call()` | Target `meta.services` whitelist did not declare this method |
| `ModuleCallTimeoutError` | `module.call()` | Called coroutine exceeds timeout (default 30s) |

"Target module unavailable" in different access paths:

| Access Path | Exception |
|-------------|-----------|
| `await sdk.module.call("X", "method")` | `ModuleNotAvailableError` (typed) |
| `sdk.module.X.attr` (lazy loading attribute access, after initialization failure) | `ModuleNotAvailableError` |
| `sdk.module.X` (attribute access when module is disabled) | `AttributeError` (Python attribute convention, `hasattr` relies on this semantics) |

```python
from ErisPulse.Core.Bases.errors import ModuleNotAvailableError, ServiceNotProvidedError

try:
    history = await sdk.module.call("Chat", "get_history", session_id, n=20)
except ModuleNotAvailableError:
    ...  # Target module does not exist / is disabled
except ServiceNotProvidedError:
    ...  # Target module does not provide this service
```

### Framework Internal Parameter Validation (ValueError)

Parameter validation in storage query builders (empty column types, `Insert` non-dict, unsafe column types, etc.) throws standard `ValueError`—these are **development-time coding errors**, and normal business code should not catch them, but rather correct the calls.

Standard adapter actions do not throw exceptions on failure: return a response dictionary with `retcode` (protocol semantics, e.g., `retcode=10002` means action not implemented)—this is a parallel error channel to client layer "failures throw `ClientError`". Adapter development must handle both.

## Handling Recommendations

```python
from ErisPulse.Core import ErisPulseError  # Base class is aggregated from Core

try:
    ...
except ErisPulseError as e:
    ...  # General catch-all: all framework custom exceptions
```

- For module development: catch as needed (see table above), use `ErisPulseError` as a fallback at the outermost layer
- All exceptions are aggregated and exported from `ErisPulse.Core` (including `SessionOccupiedError` / `InteractionCancelled` / `StrictModeError`), or can be imported from `ErisPulse.Core.Bases.errors`
- Full definitions are in `src/ErisPulse/Core/Bases/errors.py`