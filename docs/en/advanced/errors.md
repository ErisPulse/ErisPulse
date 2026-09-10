# Exception System and Handling Guide

All custom exceptions in ErisPulse inherit from `ErisPulseError`. Underlying library exceptions (such as aiohttp, aiomysql, etc.) are caught internally by the framework and converted into corresponding ErisPulse exceptions—application code **does not need to rely on any underlying library exception types**.

<!-- < tips > -->
1. To broadly catch all exceptions: catch `ErisPulseError` (the base class for all framework exceptions)
2. To precisely handle specific exceptions: catch by module (e.g., `ModuleCallTimeoutError`, `StorageUnreachableError`)
3. Storage operations do not throw by default: failures are logged and `False / None / default` is returned
<!-- < /tips > -->

## Exception Overview

```text
ErisPulseError                      # Base class for all framework exceptions
├── ClientError                     # Base class for HTTP/WS client request exceptions (Core/client)
│   ├── ClientConnectionError       # Connection layer error: DNS resolution failed, connection refused, unreachable network
│   ├── ClientTimeoutError          # Request timeout
│   └── HTTPStatusError             # HTTP status code error (e.g., 4xx/5xx and raise_for_status)
├── WebSocketError                  # Base class for WebSocket exceptions (WS connection in Core/client)
│   └── WebSocketDisconnect         # WebSocket disconnected (common for both server and client)
├── StorageError                    # Base class for storage exceptions (Core/storage)
│   └── StorageUnreachableError     # Storage backend unreachable (retry pool exhausted: database unreachable, credential error)
├── InteractionError                # Base class for interaction session exceptions (Core/Event/interaction)
├── ModuleError                     # Base class for module system exceptions (Core/module)
│   └── ModuleCallError             # Base class for module call exceptions
│       ├── ModuleNotAvailableError # Target module not registered/unavailable/failed to load
│       ├── ServiceNotProvidedError # Target module did not declare the service (outside meta.services whitelist)
│       └── ModuleCallTimeoutError  # Execution timeout for called method (default 30s)
└── (Framework internal errors)     # ValueError and others for parameter validation, see below
```

## Exception Descriptions and Occurrence Locations

### Client Series — `Core/client.py` / `Core/Bases/client.py`

`sdk.client` / HTTP client and WebSocket client throw exceptions when initiating requests:

| Exception | Location | Typical Scenario |
|-----------|----------|------------------|
| `ClientError` | Request wrapper layer | Other client errors (low-level aiohttp exceptions already converted) |
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

| Exception | Location | Typical Scenario |
|-----------|----------|------------------|
| `WebSocketError` | WS send/receive methods | Connection closed, received unexpected message type, low-level WS exception |
| `WebSocketDisconnect` | WS send/receive methods | Remote end disconnected normally (framework will automatically reconnect) |

### Storage Series — `Core/storage` / `Core/Bases/sql_base.py`

| Exception | Location | Typical Scenario |
|-----------|----------|------------------|
| `StorageError` | Storage layer | Base class for storage-related exceptions |
| `StorageUnreachableError` | Pool creation phase | Database unreachable / credential error / network isolation, retry exhausted |

> **Failure semantics of storage operations**: KV and query operations **do not throw by default**—failures are logged as ERROR and return `False` / `None` / `default` (to avoid blocking the framework due to connection issues). `StorageUnreachableError` is mainly used for internal framework cooldown and reconnection decisions; to precisely detect failures, check the return value.

See [Storage Backend → Connection Failure Behavior](docs/en/storage-backends.md#connection-failure-behavior) for connection failure behavior details.

### Interaction — `Core/Event/interaction.py`

`wait_reply` / session lease / reminder timer related:

| Exception | Location | Typical Scenario |
|-----------|----------|------------------|
| `InteractionError` | Interaction session layer | Base class for interaction session exceptions |

When waiting is cancelled (module unloaded / platform shutdown / new wait in the same session replaces it), `wait_reply` **returns `None`** instead of throwing an exception; if the session lease is occupied, `hold()` throws `SessionOccupiedError` (inherited from `InteractionError`).

### Module Series — `Core/module.py` (`sdk.module.call`)

| Exception | Location | Typical Scenario |
|-----------|----------|------------------|
| `ModuleError` | Module system | Base class for module system exceptions |
| `ModuleCallError` | `module.call()` | Base class for module call exceptions |
| `ModuleNotAvailableError` | `module.call()` | Target not registered / not enabled / loading failed |
| `ServiceNotProvidedError` | `module.call()` | Target `meta.services` whitelist does not declare the method |
| `ModuleCallTimeoutError` | `module.call()` | Called coroutine exceeds timeout (default 30s) |

```python
from ErisPulse.Core.Bases.errors import ModuleNotAvailableError, ServiceNotProvidedError

try:
    history = await sdk.module.call("Chat", "get_history", session_id, n=20)
except ModuleNotAvailableError:
    ...  # Target module does not exist / not enabled
except ServiceNotProvidedError:
    ...  # Target module does not provide this service
```

### Framework Internal Parameter Validation (ValueError)

Parameter validation for storage query builder (empty column type, `Insert` not dict, unsafe column type, etc.) throws standard `ValueError`—these are **development-time coding errors**; normal business code should not catch them, but rather correct the call.

## Exception Handling Recommendations

```python
from ErisPulse.Core import ErisPulseError  # Base class is already exported from Core

try:
    ...
except ErisPulseError as e:
    ...  # Unified fallback: all framework-defined exceptions
```

- Module Development: Catch exceptions precisely as needed (see table above), use `ErisPulseError` as a fallback at the outermost level
- All exceptions are exported from `ErisPulse.Core` and can also be imported from `ErisPulse.Core.Bases.errors`
- Full definitions can be found in `src/ErisPulse/Core/Bases/errors.py`