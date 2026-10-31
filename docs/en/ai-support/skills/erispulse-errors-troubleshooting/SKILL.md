---
name: erispulse-errors-troubleshooting
description: "适用于：遇到异常/组件不工作时的诊断路径：异常总览、排障指南、bug 追踪。覆盖场景：All custom exceptions in ErisPulse inherit from `ErisPulseError`. Underlying library exceptions (such as aiohttp, aiomysql, etc.) are captured internally by the framework and converted into corresponding ErisPulse exceptions — business code **does not need to depend on any underlying library exception types**.。This document records known bugs of the ErisPulse SDK and their repair status, arranged in chronological order by the time of repair version.。"
---

# ErisPulse 异常体系与排障

This skill is auto-built from the ErisPulse documentation.
Repository: https://github.com/ErisPulse/ErisPulse
Source paths are annotated per section; see docs/ in the repository for the latest content.

## 内容大纲

AI 按需读取：只读需要的章节即可，不必全文加载。

- 异常捕获总览: 30-45 行
- Exception Overview: 47-75 行
- Structured Attributes: 77-102 行
- Exception Descriptions and Occurrence Locations: 104-205 行
- Handling Recommendations: 207-220 行
- Noise Folding on Shutdown: 222-224 行
- 已知问题追踪: 226-241 行
- Field Descriptions: 243-266 行
- Severity Classification: 268-276 行
- Type Classification: 278-292 行
- Item Template: 294-317 行
- Statistical Overview: 319-343 行
- Fixed Bugs: 345-1373 行

## 异常捕获总览

> 来源: `docs/en/advanced/errors.md`（https://github.com/ErisPulse/ErisPulse/blob/main/docs/en/advanced/errors.md）

# Exception System and Handling Guide

> [!NOTE]
> **L1 Core Reading** — One of the five core documents in the "Reading Path" on the homepage, essential for module development.

All custom exceptions in ErisPulse inherit from `ErisPulseError`. Underlying library exceptions (such as aiohttp, aiomysql, etc.) are captured internally by the framework and converted into corresponding ErisPulse exceptions — business code **does not need to depend on any underlying library exception types**.

{!--< tips >!--}
1. To catch broadly as a fallback: catch `ErisPulseError` (the base class for all framework exceptions)
2. To handle precisely: catch by module (e.g., `ModuleCallTimeoutError`, `StorageUnreachableError`)
3. Storage operations do not throw by default: log failures and return `False / None / default`; subscribe to `storage.unreachable` / `storage.recovered` events for connection state changes
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

## Noise Folding on Shutdown

When long-running processes shut down (or background loops are cancelled), the event loop often emits a batch of `Task was destroyed but it is pending!`-like noise from the interpreter, which lacks actionable value. The framework includes built-in **noise folding for similar events**: within a 2-second window, similar messages are downgraded to TRACE level and merged with a count, outputting only once and appending a suffix such as 「(N additional similar messages have been folded)」. This intentional noise reduction does not mean the framework is suppressing real exceptions; business exceptions (all types listed above) are still fully output as usual. The folding mechanism targets only interpreter exit noise, leaving business exceptions unaffected. What level of exception is worth retaining, and what can be downgraded or folded, follows the [Engineering Robustness Rules · Exception Logging Levels](../styleguide/engineering.md#1-异常留痕分级).

## 已知问题追踪

> 来源: `docs/en/bug-tracker.md`（https://github.com/ErisPulse/ErisPulse/blob/main/docs/en/bug-tracker.md）

# Bug Tracker

This document records known bugs of the ErisPulse SDK and their repair status, arranged in chronological order by the time of repair version.

> **For Readers**
> No software is perfect, and even the most careful developers leave small errors. This tracker includes only issues that have a practical impact on operation—those too minor to even reach the "minor" level are not included here. Although the number of "critical" items may seem high, the intention behind publicly recording these bugs is to make troubleshooting and backtracking smoother, not to create anxiety: problems that are visible, recorded, and fixed are proof that the project is constantly improving. Seeing this list should not cause anxiety; it is a troubleshooting tool, not a source of fear.

> **How to Read & Maintenance Conventions**
> - Each bug record includes structured fields such as problem description, root cause analysis, affected version range, repair solution, etc. It is recommended to check the "affected version" before upgrading to see if it covers the version currently in use.
> - If you need to add a new bug entry, supplement content at the corresponding location, following the field specifications and severity/type classifications below.

---

## Field Descriptions

### Mandatory Fields

| Field | Description |
|------|------|
| **Problem** | The external manifestation of the bug, the abnormal phenomenon observable by the user. Try to provide error messages or typical scenarios |
| **Cause** | Root cause analysis, pointing to specific code defects (including "root cause chain" diagrams for complex scenarios) |
| **Affected Version** | Affected version range, format `introduced version - fixed version` (including both dev versions) |
| **Fixed Version** | The specific version number that fixes the bug |
| **Fixed Content** | Brief description of the repair solution, including key code changes |
| **Fixed Date** | The release date corresponding to the fixed version, using the `YYYY/MM/DD` format |
| **Severity** | Marked according to the "Severity Classification" below |
| **Type** | Marked according to the "Type Classification" below, can be combined (e.g., `Adapter / Router`) |

### Optional Fields

| Field | Description | Applicable Scenarios |
|------|------|---------|
| **Reproduction Steps** | The minimum reproducible path to trigger the bug | Complex bugs, occasional bugs are recommended to supplement |
| **Associated** | Links to related Issue / PR / Commit | Supplement when there is external discussion record |
| **Regression Test** | Test case location to verify repair and prevent regression | Supplement when corresponding pytest cases are written |

---

## Severity Classification

| Icon | Level | Judgment Criteria | Typical Manifestation |
|------|------|---------|---------|
| 🔴 | Critical | Causes process crash, data loss/damage, core functionality completely unavailable, security vulnerabilities | OOM Kill, message cannot be sent, module cannot be loaded, hot reload failure |
| 🟡 | Medium | Function abnormal but with workaround, non-core functionality fails, occasional problems | State judgment error, repeated triggering, cache expiration, inaccurate error message |
| 🟢 | Minor | Does not affect core functionality, only code quality or experience issues, potential risks not triggered | Deprecated API, dead code, missing warning logs |

---

## Type Classification

| Type | Coverage Range |
|------|---------|
| Configuration System | `ConfigManager`, configuration read/write, configuration Schema, hot update |
| Event System | `Event` module (command/message/notice/request/meta), event distribution, processor registration |
| Adapter | `AdapterManager`, `BaseAdapter`, account parsing, Bot status, middleware |
| Router | `RouterManager`, HTTP/WebSocket/SSE routing, rate limiting, CORS |
| Client | `HttpClient`, `ClientWebSocket`, aiohttp wrapper |
| Storage | `StorageManager`, SQLite, SQL builder, nested keys |
| Loader System | `Loader`, `LazyModule`, `ModuleInitializer`, strict mode, module discovery |
| CLI | `epsdk` command, `init`/`run`/`install`, parameter parsing, signal handling |
| Runtime | `sdk.run`/`restart`/`uninit`, lifecycle, signal, subprocess |

---

## Item Template

When adding a new bug item, follow the following format:

```markdown
### [BUG-XXX] Title

**Problem**: Problem description (error message or typical phenomenon)
**Cause**: Root cause analysis
**Affected Version**: Introduced version - Fixed version
**Fixed Version**: x.x.x
**Fixed Content**: Repair solution
**Fixed Date**: YYYY/MM/DD

<!-- Optional fields -->
**Reproduction Steps**: (Recommended for complex bugs)
**Associated**: (Issue/PR link)
**Regression Test**: (Test case path)

**Severity**: 🔴 Critical | 🟡 Medium | 🟢 Minor
**Type**: Configuration System / Event System / Adapter / Router / Client / Storage / Loader System / CLI / Runtime
```

---

## Statistical Overview

| Severity | Quantity |
|--------|------|
| 🔴 Critical | 16 |
| 🟡 Medium | 26 |
| 🟢 Minor | 3 |
| **Total** | **45** |

| Type | Quantity |
|------|------|
| Event System | 12 |
| Configuration System | 12 |
| Adapter | 7 |
| CLI | 3 |
| Storage | 3 |
| Loader System | 4 |
| Router | 2 |
| Client | 1 |
| Runtime | 1 |

> Note: A single bug can belong to multiple types; the table above is counted based on the main type.
> Note: BUG-028 / BUG-031 numbering is vacant (abandoned during registration, numbering remains stable and is not recycled).

---

## Fixed Bugs

### [BUG-001] Event handler duplicate registration causing events to be processed multiple times

**Problem**: When registering handlers with multiple `@message` / `@notice` decorators, the same event would be triggered repeatedly multiple times, causing commands to be executed multiple times and logs to be output redundantly.

**Cause**: `BaseEventHandler` lacked deduplication logic when registering handlers to the adapter event bus; each decorator mounted a handler to the bus once, so the handler was invoked multiple times during event dispatch.

**Affected versions**: 2.2.0-dev.0 - 2.2.1-dev.0

**Fixed version**: 2.2.1-dev.0

**Fix**: Optimized `BaseEventHandler` to ensure each event type registers its handler with the adapter only once, avoiding duplicate triggering.

**Fix date**: 2025/08/18

**Severity**: 🔴 Critical

**Type**: Event System

---

### [BUG-002] Init command adapter configuration path type error

**Problem**: When using the `ep init` command for interactive initialization, selecting to configure adapters raises a type error:

```
Interactive initialization failed: unsupported operand type(s) for /: 'str' and 'str'
```

**Cause**: When version 2.3.7 adjusted the configuration file path, the method parameter types were inconsistent. `_configure_adapters_interactive_sync` receives a `str` type parameter but internally uses the `Path` `/` operator to concatenate paths.

**Affected versions**: 2.3.7 - 2.3.9-dev.1

**Fixed version**: 2.3.9-dev.1

**Fix**: Changed the parameter type of the `_configure_adapters_interactive_sync` method from `str` to `Path`, passing `Path` objects directly at call sites.

**Fix date**: 2026/03/23

**Severity**: 🟡 Medium

**Type**: CLI

---

### [BUG-003] Command events become invalid after restart

**Problem**: After calling `sdk.restart()`, commands registered via `@command` can no longer be triggered; the bot shows no response after commands are sent.

**Cause**: After `adapter.shutdown()` clears the event bus, the `_linked_to_adapter_bus` state of `BaseEventHandler` is not reset to `False`, causing the `_process_event` method to believe it is already mounted to the adapter bus and skip the re-mounting operation.

**Affected versions**: 2.2.x - 2.4.0-dev.2

**Fixed version**: 2.4.0-dev.3

**Fix**: Introduced `_linked_to_adapter_bus` state tracking; after `_clear_handlers()` disconnects from the bus, the next `register()` automatically re-mounts, accommodating shutdown/restart scenarios.

**Fix date**: 2026/04/09

**Severity**: 🔴 Critical

**Type**: Event System

---

### [BUG-004] Lifecycle event handlers not cleaned up

**Problem**: After `sdk.restart()`, old lifecycle event handlers still exist and trigger repeatedly, causing the same event to be processed multiple times.

**Cause**: The `lifecycle._handlers` dictionary was never cleaned up during `uninit()`, so after restart, old and new handlers coexist.

**Affected versions**: 2.3.0 - 2.4.0-dev.2

**Fixed version**: 2.4.0-dev.3

**Fix**: At the end of the `Uninitializer` cleanup flow (after all events are submitted), clear `lifecycle._handlers`.

**Fix date**: 2026/04/09

**Severity**: 🟡 Medium

**Type**: Runtime

---

### [BUG-005] Event.is_friend_add/is_friend_delete detail_type inconsistent with the OB12 standard

**Problem**: `Event.is_friend_add()` checks `detail_type == "friend_add"`, and `Event.is_friend_delete()` checks `detail_type == "friend_delete"`, but the OneBot12 standard defines the `detail_type` values as `"friend_increase"` and `"friend_decrease"`. This is inconsistent with the values used by the `on_friend_add`/`on_friend_remove` decorators in `notice.py`, so when handlers registered via decorators are triggered, the corresponding `is_friend_add()`/`is_friend_delete()` check methods return `False`.

**Cause**: `wrapper.py` used non-standard naming, while `notice.py` used the correct OB12 standard naming.

**Affected versions**: Since implementation

**Fixed version**: 2.4.2-dev.1

**Fix**: Changed the matching value of `is_friend_add()` from `"friend_add"` to `"friend_increase"`, and `is_friend_delete()` from `"friend_delete"` to `"friend_decrease"`.

**Fix date**: 2026/04/13

**Severity**: 🟡 Medium

**Type**: Event System

---

### [BUG-006] adapter.clear() does not clean _started_instances, causing incorrect state after restart

**Problem**: The `AdapterManager.clear()` method clears `_adapters`, `_adapter_info`, handlers, and `_bots`, but misses the `_started_instances` set. If `clear()` is called while adapters are running, `_started_instances` retains dangling references, causing incorrect state determination after restart.

**Cause**: When `_started_instances` was introduced in 2.4.0-dev.1, it was not cleaned up in `clear()` in sync.

**Affected versions**: 2.4.0-dev.1 - 2.4.2-dev.0

**Fixed version**: 2.4.2-dev.1

**Fix**: Added `self._started_instances.clear()` to the `clear()` method.

**Fix date**: 2026/04/13

**Severity**: 🟡 Medium

**Type**: Adapter

---

### [BUG-007] command.wait_reply() uses the deprecated asyncio.get_event_loop()

**Problem**: The `CommandHandler.wait_reply()` method uses `asyncio.get_event_loop()` to create futures and get timestamps; this method is deprecated in Python 3.10+, and `asyncio.get_running_loop()` should be used in async contexts. This is inconsistent with the `get_running_loop()` used by the `wait_for()` method in `wrapper.py` in the same file.

**Cause**: The old API was used during development; the later-added `wait_for()` used the correct API, but the old code was not retroactively fixed.

**Affected versions**: 2.3.0-dev.0

**Fixed version**: 2.4.2-dev.1

**Fix**: Replaced both occurrences of `asyncio.get_event_loop()` in `command.py` with `asyncio.get_running_loop()`.

**Fix date**: 2026/04/13

**Severity**: 🟢 Minor

**Type**: Event System

---

### [BUG-008] Bot offline events submitted repeatedly during shutdown

**Problem**: When calling `adapter.shutdown()` to shut down all adapters, `_update_bot_status()` repeatedly submits Bot offline events during the shutdown flow, causing the same batch of Bots to be marked offline multiple times and triggering multiple `adapter.bot.offline` lifecycle events.

**Cause**: The Bot status tracking system introduced in 2.4.0-dev.1 did not set a "shutting down" flag during `shutdown()`, so `_update_bot_status()` could not distinguish normal offline events from cascading offline events during the shutdown flow.

**Affected versions**: 2.4.0-dev.1 - 2.4.2-dev.1

**Fixed version**: 2.4.2-dev.1

**Fix**: Added the `_is_being_shutdown` flag to `AdapterManager`, set to True at the start of `shutdown()` and cleared at the end; `_update_bot_status()` checks this flag and skips duplicate submissions during the shutdown process.

**Fix date**: 2026/04/21

**Severity**: 🟡 Medium

**Type**: Adapter

---

### [BUG-009] LazyModule synchronous access to BaseModule causing incomplete initialization

**Problem**: When users access lazily loaded BaseModule properties in a synchronous context, the module initializes asynchronously using `loop.create_task()` without awaiting it, so property access may occur before initialization completes, causing race conditions.

**Cause**: For BaseModule, `_ensure_initialized()` calls `loop.create_task(self._initialize())` and returns immediately, without ensuring initialization completion.

**Affected versions**: 2.4.0-dev.0 - 2.4.2-dev.1

**Fixed version**: 2.4.2-dev.2

**Fix**: In synchronous contexts, BaseModule initialization now uses `asyncio.run(self._initialize())`, ensuring initialization completes before returning. The transparent proxy behavior is preserved, so users don't need to be aware of sync/async differences.

**Fix date**: 2026/04/21

**Severity**: 🟡 Medium

**Type**: Loading System

---

### [BUG-010] Multi-threaded configuration system writes causing data loss

**Problem**: In multi-threaded environments, when multiple threads call `config.setConfig()` simultaneously, the `_flush_config()` read-modify-write operation is not atomic, potentially causing partial writes to be lost.

**Cause**: Although `_flush_config()` uses an `RLock`, there is no file lock protection between file reads and writes, and the `_schedule_write` Timer may be triggered multiple times, causing overwrites.

**Affected versions**: 2.3.0 - 2.4.2-dev.1

**Fixed version**: 2.4.2-dev.2

**Fix**:
1. Added a file lock mechanism (`_file_lock`) to ensure atomic file operations
2. Used writing to a temporary file followed by atomic rename (`os.replace`/`os.rename`)
3. Improved the `_schedule_write` Timer cancellation and rescheduling logic

**Fix date**: 2026/04/21

**Severity**: 🔴 Critical

**Type**: Configuration System

---

### [BUG-011] CTRL+C cannot stop the program on Windows

**Problem**: When running `python main.py` directly on Windows, pressing CTRL+C cannot terminate the program. After the program starts normally and outputs route server information, CTRL+C is completely unresponsive; the process can only be forcibly killed via Task Manager. When started via `epsdk run`, stopping works normally—but `epsdk run` runs through a subprocess model.

**Cause**: The `serve()` function of the Hypercorn ASGI server internally registers its own SIGINT handler via `signal.signal(SIGINT, handler)`, overriding Python's default `KeyboardInterrupt` handling mechanism. When Hypercorn is started via `asyncio.create_task()` as a background task, Hypercorn's internal shutdown flow cannot be triggered properly (because it expects the `worker_serve` mode), causing the CTRL+C signal to be swallowed by Hypercorn without triggering any cleanup actions.

**Affected versions**: 2.3.6 - 2.4.2

**Fixed version**: 2.4.3-dev.0

**Fix**:
1. Switched the ASGI server from Hypercorn to Uvicorn (`pyproject.toml` dependency change)
2. Used `uvicorn.Server._serve()` to start the server directly, **bypassing** the `capture_signals()` signal-handling context manager
3. Implemented graceful stopping via `server.should_exit = True`, cancelling the background task on timeout
4. Simultaneously removed the subprocess running model and the `runtime/cleanup.py` cleanup module (the subprocess cleanup mechanism is no longer needed)

**Fix date**: 2026/04/28

**Severity**: 🔴 Critical

**Type**: CLI / Runtime

---

### [BUG-012] Python code of updated modules not taking effect after hot restart

**Problem**: After performing a soft restart with `sdk.restart()`, new code of modules/adapters upgraded via `epsdk install` (such as newly added API routes) does not take effect; the old version logic still runs. A full process restart is required to load the latest code.

**Cause**: `_do_restart()` calls `entry_point.load()` during reinitialization, but this function returns the cached old-version module object from `sys.modules` rather than reloading from disk.

**Affected versions**: Early versions - 2.4.3-dev.1

**Fixed version**: 2.4.3-dev.1

**Fix**: After `uninit()` and before `init()`, clear the caches of loaded module/adapter packages in `sys.modules`, so that `entry_point.load()` loads the latest code from disk. Added the `_collect_top_level_modules()` and `_invalidate_module_cache()` helper methods, deriving top-level module names via `top_level.txt` or the entry-point value.

**Fix date**: 2026/05/03

**Severity**: 🔴 Critical

**Type**: Loading System / Runtime

---

### [BUG-013] Module loading strategy sorting logic error

**Problem**: `ModuleLoadStrategy` provides a `priority` field for declaring a module's initialization priority, but the loading strategy implementation had a mistake, causing modules to not be initialized in the expected priority order, instead loading in the default order of `entry_points()`. When load dependencies exist between modules, the correct initialization order cannot be ensured via `priority`.

**Cause**: The sorting logic in the loading strategy implementation was wrong; `initialize_modules()` did not sort the module list by `priority`.

**Affected versions**: 2.3.4 - 2.4.5-dev.2

**Fixed version**: 2.4.5-dev.3

**Fix**: Before iterating in `initialize_modules()`, sort the module list by `priority` in descending order. Modules with the same priority maintain their original relative order (stable sort).

**Fix date**: 2026/05/15

**Severity**: 🟡 Medium

**Type**: Loading System

---

### [BUG-014] Adapter middleware returning None causing event data loss

**Problem**: When `adapter.emit()` executes the OneBot12 middleware chain, if a middleware returns `None` (e.g., forgetting `return data`), subsequent middleware and all event handlers receive `processed_data` as `None`, causing event processing to fail entirely.

**Cause**: The middleware chain implementation `processed_data = await middleware(processed_data)` did not check whether the return value was `None`, directly overwriting the previous step's processing result.

**Affected versions**: unknown - 2.4.5-dev.3

**Fixed version**: 2.4.5-dev.4

**Fix**: When a middleware returns `None`, ignore the return value, keep the original data to continue passing it along, and output a warning-level log.

**Fix date**: 2026/05/15

**Severity**: 🔴 Critical

**Type**: Adapter / Event System

---

### [BUG-015] Configuration file path depends on working directory

**Problem**: The `ConfigManager` configuration file path defaults to the relative path `"config/config.toml"`, resolved at runtime depending on `os.getcwd()`. If the working directory changes during runtime (e.g., via `os.chdir()`), configuration file read/write operations point to the wrong location, causing configuration loss or stale data being read.

**Cause**: `__init__` directly stores the relative path without resolving it to an absolute path at initialization.

**Affected versions**: 2.3.7 - 2.4.5-dev.3

**Fixed version**: 2.4.5-dev.4

**Fix**: In `ConfigManager.__init__()`, if the passed-in path is relative, automatically resolve it to an absolute path via `os.path.abspath()`.

**Fix date**: 2026/05/15

**Severity**: 🟡 Medium

**Type**: Configuration System

---

### [BUG-016] BaseStorage confuses a stored None value with a missing key

**Problem**: `BaseStorage.get_multi()` / `__getattr__()` cannot distinguish between "key does not exist" and "key's value is `None`"; when a user explicitly stores `None` and then reads it, it is treated as a missing key.

**Cause**: The value retrieval logic directly uses `value is None` to determine key existence, lacking an independent "missing" marker.

**Affected versions**: Early versions - 2.4.6-dev.6

**Fixed version**: 2.4.6-dev.6

**Fix**: Introduced the `_SENTINEL` sentinel value to distinguish "key does not exist" from "value is None"; the two are no longer confused.

**Fix date**: 2026/06/07

**Severity**: 🟡 Medium

**Type**: Storage

---

### [BUG-017] WebSocket route auto_accept flag lost after service restart

**Problem**: After a service restart (e.g., `sdk.restart()`), all WebSocket routes' `auto_accept` configuration reverts to `False`; connections that were expected to be automatically accepted become pending, clients receive no response for a long time, manifesting as WS connections hanging.

**Cause**: `_restore_routes_from_records()` hardcoded `auto_accept` to `False` when restoring routes from persisted records, without reading the value from the original records; meanwhile, when the route storage tuple expanded from a two-tuple to a three-tuple, the restore logic was not updated accordingly.

**Affected versions**: 2.3.8-dev.0 - 2.4.6-dev.6

**Fixed version**: 2.4.6-dev.6

**Fix**: The route storage tuple expanded to `(handler, auth_handler, auto_accept)`; `_restore_routes_from_records()` reads the real `auto_accept` value from records instead of hardcoding `False`.

**Fix date**: 2026/06/07

**Severity**: 🔴 Critical

**Type**: Routing

---

### [BUG-018] HTTP/WS client concurrent calls causing crashes and connection leaks

**Problem**: The HTTP and WebSocket clients in `Core/client.py` have multiple stability defects under concurrent scenarios, causing connection leaks or process crashes:
- When multiple coroutines concurrently call `ClientWebSocket.receive()`, aiohttp throws `Concurrent call to receive() is not allowed`
- Concurrent calls to `_get_http_session()` / `_get_ws_session()` may create multiple sessions, and `_drain_sessions()` does not close old connections, causing connection leaks
- The exception catching order in `request()` is wrong: `except ClientConnectionError` (ErisPulse exception) never triggers; aiohttp's connection errors are caught by the generic `except Exception`, so the "connection retry + session rebuild" logic (dead code) never executes
- `send_json()` ignores the `mode="binary"` parameter; `_get_ws_session()` does not pass default request headers

**Cause**: The initial client implementation (2.4.6-dev.5) lacked concurrency protection and exception classification, and improperly handled the aiohttp exception hierarchy and its inheritance relationship with ErisPulse custom exceptions.

**Affected versions**: 2.4.6-dev.5 - 2.4.8

**Fixed version**: 2.4.8

**Fix**:
1. Added `_recv_lock` to serialize all `receive()` / `receive_text()` / `receive_bytes()` calls
2. Added `_session_lock` to protect session creation; `_drain_sessions()` changed to an async method that actually closes old sessions
3. Refactored the `request()` exception catching order: `asyncio.TimeoutError` → `aiohttp.ClientConnectionError` (triggers session rebuild) → `aiohttp.ClientError` → `ClientError` (pass through) → `Exception`
4. Fixed `send_json()` mode handling, `_get_ws_session()` default header passthrough, the `close()` concurrency race, and the duplicate `release()` in `HttpResponse.__aexit__`

**Fix date**: 2026/06/12

**Severity**: 🔴 Critical

**Type**: Client

---

### [BUG-019] Route conflicts during adapter hot reload causing reload failure

**Problem**: When third-party modules (such as Dashboard) trigger adapter hot reload, or when an adapter retries after a startup failure, because old routes registered previously (such as `onebot11_default`) are not cleaned up, a `WebSocket path ... already registered` conflict is thrown, causing the reload to fail. A full process restart is required to recover.

**Cause**: `AdapterManager.shutdown()` only cleans routes via `unregister_all_by_namespace(platform)`, but adapters (such as OneBot11) register WS routes with `onebot11_{account_name}` as the namespace; the granularity mismatch causes cleanup to be a no-op; the startup failure retry path also does not clean up routes left over from the previous attempt.

**Affected versions**: Early versions - 2.4.9

**Fixed version**: 2.4.9

**Fix**:
1. Route registration now automatically tracks the `owner → namespace` ownership relationship via the `current_owner` ContextVar
2. Added `unregister_all_by_owner(owner)`; stopping/restarting also cleans up by owner, covering fine-grained namespaces
3. Added the `_stop_adapter(platform)` primitive ("stop means cleanup"), binding stopping an adapter with reclaiming its registered resources in a single call; both `restart()` and startup failure retries go through this entry point
4. Added the framework-level `adapter.restart(platform)` API; third-party modules should call this method rather than directly manipulating adapter instances

**Fix date**: 2026/06/12

**Severity**: 🔴 Critical

**Type**: Adapter / Routing

---

### [BUG-020] Subprocess mode `ep run <script>` cannot find subpackages in the script's directory

**Problem**: When running a script with `ep r .\main.py` in non-hot-reload mode, if the script has relative imports (such as `from qg import ...`), a `No module named 'qg'` error is reported. The `--reload` mode works fine.

**Cause**: Non-hot-reload mode directly calls `runpy.run_path()` to execute the script; this function does not automatically add the script's directory to `sys.path`. The `--reload` mode runs via a `subprocess.Popen` subprocess; the subprocess automatically inherits the current working directory, so `sys.path[0]` is the script's directory, and it works normally.

**Affected versions**: 2.5.0 - 2.5.2-dev.0

**Fixed version**: 2.5.2-dev.0

**Fix**: Before the `runpy.run_path()` call, manually insert the script's directory at `sys.path[0]`.

**Fix date**: 2026/06/27

**Severity**: 🟡 Medium

**Type**: CLI

---

### [BUG-021] SQL query builder rejects legitimate wildcards and column expressions

**Problem**: `SQLiteQueryBuilder`'s `_build_select_sql()` calls `_validate_identifier()` for all SELECT columns; this function uses the strict whitelist regex `^[a-zA-Z_][a-zA-Z0-9_]*$`, causing legitimate SQL syntax to be misjudged as unsafe column names:

- `SELECT *` — `*` is the SQL standard wildcard
- `SELECT COUNT(*)` — aggregate function
- `SELECT users.name` — qualified column name
- `SELECT col AS alias` — column alias

Among them, `Select("*")` is used by modules such as Cron, causing module `on_load` execution failure and modules failing to load.

**Cause**: Version 2.4.6 enhanced SQL injection protection by introducing the `_validate_identifier()` whitelist validation. This validation was applied to all column names but did not distinguish between the read side (SELECT/ORDER BY) and the write side (INSERT/UPDATE). SELECT columns allow complex SQL expressions and should not be restricted by the simple identifier whitelist.

**Affected versions**: 2.4.6 - 2.5.2-dev.1

**Fixed version**: 2.5.2-dev.2

**Fix**: Changed SELECT/ORDER BY column validation from whitelist mode to blacklist mode:
1. Added the `_validate_select_column()` function, which only intercepts SQL injection dangerous characters (`;` `'` `"` `--` `/*` `*/` `\x00` newline characters)
2. Allows arbitrary legitimate SQL column expressions (`*`, `table.*`, `table.column`, `COUNT(*)`, `col AS alias`, etc.)
3. INSERT/UPDATE column names still maintain strict whitelist validation (only simple identifiers allowed)

**Fix date**: 2026/06/29

**Severity**: 🔴 Critical

**Type**: Storage

---

### [BUG-022] _resolve_account() account resolution regression (_accounts_data not populated)

**Problem**: After the 2.5.2 configuration system refactor, multi-account adapters that declare `AccountConfigClass` report `ValueError("AccountConfigClass not declared, unable to resolve account")` when calling methods that need to send messages, such as `wait_reply` and `reply`. Even if the adapter is correctly configured with multi-account information, account resolution still fails.

**Cause**: 2.5.2-dev.5 refactored `_load_accounts()` (responsible for reading configuration + validation + populating `_accounts_data`) into `_ensure_accounts_exist()` (only generating configuration templates), but `_resolve_account()` still checks `self._accounts_data is None`. Since `_ensure_accounts_exist()` no longer populates `_accounts_data`, this attribute is always `None`, causing `_resolve_account()` to return `(None, None)` early, and account resolution fails entirely.

**Root cause chain**:
```
_load_accounts() was deleted
  → __init__ no longer populates _accounts_data
    → _accounts_data is always None
      → _resolve_account() checks _accounts_data is None → return (None, None)
        → Downstream callers of _resolve_account (such as call_api) get None
          → Error triggered
```

**Affected versions**: 2.5.2-dev.5 - 2.5.2

**Fixed version**: 2.5.3

**Fix**: In `BaseAdapter.__init__`, restore populating `_accounts_data` after `_ensure_accounts_exist()`:
```python
if self.AccountConfigClass is not None:
    self._ensure_accounts_exist()
    self._accounts_data = self.accounts  # Restore population; data source is the real-time read accounts property
```
The `_resolve_account()` logic remains unchanged, fully backward compatible:
- Adapters that do not declare `AccountConfigClass`: `_accounts_data` stays `None` → returns `(None, None)`
- Adapters that declare `AccountConfigClass`: `_accounts_data` is populated → resolution works normally
- Adapters that override `_load_accounts` or manually set `_accounts_data`: override after `super().__init__()`, taking the highest priority

**Fix date**: 2026/07/07

**Severity**: 🔴 Critical

**Type**: Adapter / Configuration System

---

### [BUG-023] Adapter cache not refreshed after modifying account configuration, causing account resolution failure

**Problem**: After users modify a multi-account adapter's account configuration (such as filling in a token) via the Dashboard, the adapter still uses the old cache; calling message-sending related methods reports `No available account found (account_id=default)`. A process restart is required for the new configuration to take effect.

**Cause**: `_accounts_data` is read from the configuration store only once at `BaseAdapter.__init__` and is never refreshed afterwards. `AdapterManager._run_adapter()` and `restart()` did not re-read the account configuration before calling `adapter.start()`, causing the cache to become out of sync with the actual configuration.

**Affected versions**: 2.4.6 - 2.5.4

**Fixed version**: 2.5.4

**Fix**: In `AdapterManager._run_adapter()` and `restart()`, refresh `adapter._accounts_data = adapter.accounts` before calling `adapter.start()`, ensuring the latest configuration is used on every startup.

**Fix date**: 2026/07/09

**Severity**: 🔴 Critical

**Type**: Adapter / Configuration System

---

### [BUG-024] storage.set() writing large numeric ID keys triggers OOM Kill

**Problem**: When calling `storage.set()` to write a nested key path containing a large pure numeric segment (such as the QQ group number `871684833`), the process is OOM Killed by the container (exit code -9), and the service crashes directly with no recovery.

**Cause**: In the recursive implementation of `_set_nested_value`, pure numeric segments in nested key paths are misjudged as list indices by `isdigit()`, triggering `current.extend([None] * (index - len(current) + 1))`, attempting to allocate a list of hundreds of millions of elements and instantly exhausting memory.

**Root cause chain**:
```
Key path contains a pure numeric segment (such as group number 871684833)
  → isdigit() misjudges it as an array index
    → extend([None] * (871684833 - len(current) + 1))
      → Attempts to allocate hundreds of millions of elements
        → Memory exhausted → Container OOM Kill (exit code -9)
```

**Affected versions**: 2.5.1 - 2.5.5

**Fixed version**: 2.5.5

**Fix**:
1. When pre-creating intermediate layers, always use dictionaries; no longer guess the container type based on whether the next segment is numeric
2. When setting the final value, only process by index if the container itself is already a list and the index is less than `STORAGE_MAX_LIST_INDEX` (10000); oversized indices are safely skipped
3. Changed the recursive implementation to an iterative implementation, eliminating the potential infinite recursion risk in the original code
4. Added the `STORAGE_MAX_LIST_INDEX` constant to `Core/constants.py`, centrally managing the index safety upper limit

**Fix date**: 2026/07/10

**Reproduction steps**:
```python
# Writing a nested key path containing a large numeric segment (such as a QQ group number) triggers it
await sdk.storage.aset("groups.871684833.name", "Some Group")
# → Process memory instantly spikes, killed by OOM
```

**Regression tests**: `tests/unit/test_unit_storage.py` added 4 regression cases
- `test_nested_key_numeric_segment_as_dict_key` — precisely reproduces the OOM scenario
- `test_nested_key_numeric_segment_multiple` — multiple consecutive numeric segments are all treated as dictionary keys
- `test_nested_key_existing_list_index_set_within_limit` — reasonable index writing to an existing list
- `test_nested_key_list_index_safety_limit` — oversized index safety limit verification

**Severity**: 🔴 Critical

**Type**: Storage

---

### [BUG-025] on_config_update callback not routed by the core

**Problem**: The `on_config_update(old, new)` callback is already defined in the base classes (`BaseModule` / `BaseAdapter`), but the framework core does not associate it with configuration change events. Actual behavior: it is triggered when changing configuration via the configuration management panel, but not triggered when manually editing `config.toml` or calling `setConfig()` in code.

**Cause**: `ConfigManager` emits the `config.set` / `config.updated` lifecycle events on configuration changes, but lacks subscription logic to forward these events to each component's `on_config_update` method.

**Root cause chain**:
```
Core does not subscribe to config.set / config.updated
  → Configuration change events not forwarded
    → on_config_update not called
      → Manual file editing / code setConfig does not trigger the hot update callback
```

**Affected versions**: All versions

**Fixed version**: 2.6.2

**Fix**: `ModuleManager` / `AdapterManager` register subscriptions for the `config.set` event (covering the code `setConfig()` path) and the `config.updated` event (covering the manual file editing path); after matching by configuration key prefix, they call the corresponding component's `on_config_update`, passing type-safe configuration objects. Also fixed the issue where `_flush_config()` did not sync `_config_mtime` after writing files, avoiding the framework's own writes being misjudged as external modifications by the file-watching task and repeatedly triggering `config.updated`.

**Compatibility note**: Configuration hot updates are now uniformly maintained by the framework core. The previous logic where the configuration management panel triggered it on behalf has been removed; after upgrading the framework, the configuration management panel needs to be upgraded in sync, otherwise duplicate triggering will occur (core + panel each calling once). The `on_config_update` method signature and semantics remain unchanged; subclasses need no modification.

**Fix date**: 2026/07/23

**Severity**: 🟡 Medium

**Type**: Configuration System

---

### [BUG-026] notice/request event reply target inference error

**Problem**: When calling `event.reply()` in a group notice event (such as member join `group_member_increase`), the message is sent to the private chat of the user who triggered the event, rather than to the group where the event occurred. The same applies to friend notice events; reply targets may be wrong.

**Cause**: `infer_receive_type()` directly returns the event's `detail_type` as the session type. For message events this is correct (the `detail_type` values `private`/`group` are themselves session types), but for notice/request events the `detail_type` is a semantic subtype (such as `group_member_increase`, `friend_increase`), not a session type. The subsequent `convert_to_send_type()` and `get_id_field()` cannot find the value in their mapping tables, falling back to the defaults `"user"` / `"user_id"`, causing the reply target to be wrong.

**Root cause chain**:
```
notice event detail_type="group_member_increase"
  → infer_receive_type() directly returns "group_member_increase"
    → convert_to_send_type("group_member_increase") not in mapping table → fallback "user"
    → get_id_field("group_member_increase") not in mapping table → fallback "user_id"
      → target_id = event["user_id"]  ← New member's private chat (not the group)
```

**Affected versions**: All versions

**Fixed version**: 2.7.0-dev.3

**Fix**: `infer_receive_type()` adds a check—`detail_type` is returned directly only when it is a known session type (standard or custom type); otherwise the correct session type is inferred from the ID fields (`group_id` / `channel_id` / `user_id`, etc.).

**Regression tests**: `tests/unit/test_unit_session_type.py` → `TestNoticeRequestTypeInference` (10 cases)

**Fix date**: 2026/07/29

**Severity**: 🟢 Minor

**Type**: Event System

---

### [BUG-027] Route rate-limit cleanup task using a fixed window causes long-window rate limit rules to fail

**Problem**: When route rate limiting is configured with a long-window rule (such as `100/hour`, `{"requests": 100, "window": 3600}`), the rate limiting is effectively useless—actual behavior is approximately `100/minute` (allowing up to about 6000 requests per hour), completely failing to provide the expected hourly-level protection.

**Cause**: `_apply_rate_limit` resolves each route's actual `window` (up to 3600 seconds), and the per-request checks do use that window; but the background cleanup task `_cleanup_expired_rate_limits` uses the fixed constant `DEFAULT_RATE_LIMIT_WINDOW_SECS` (60 seconds) as the unified cleanup threshold for **all** routes. Thus, in a `100/hour` route, timestamps older than 60 seconds are prematurely cleared by the cleanup task, records within the hour window never accumulate close to 100, and the rate limiting is severely weakened.

**Root cause chain**:
```
_apply_rate_limit resolves window=3600 (100/hour)
  → per-request checks retain timestamps per 3600s (correct)
  → but _cleanup_expired_rate_limits cleans with a fixed max_window=60s
    → timestamps older than 60s are all cleared
      → the hour window always only has the most recent 1 minute of records
        → 100/hour actually degrades to ~100/minute (loosened by about 60x)
```

**Affected versions**: 2.6.0-dev.0 - 2.7.0-dev.4

**Fixed version**: 2.7.0-dev.5

**Fix**: Added `_rate_limit_windows: dict[str, int]` to record each route's actual window by store key; `_apply_rate_limit` writes the window when first creating an entry; `_cleanup_expired_rate_limits` changed to clean by each key's own window (falling back to the default when missing); entry deletions during cleanup and `stop()` maintain both dictionaries in sync.

**Fix date**: 2026/07/31

**Regression tests**: `tests/unit/test_unit_router.py` → `TestRateLimit::test_cleanup_respects_per_route_window`

**Severity**: 🔴 Critical

**Type**: Routing

---

### [BUG-029] Configuration watch task broadcasts half-written TOML and silently swallows exceptions

**Problem**: When a user manually edits `config.toml` and saves halfway (producing a transient syntax error), the configuration-watching background thread detects the mtime change and reloads the configuration, but after a load failure it still emits the `config.updated` event with an empty configuration `{}`, causing adapters/modules' `on_config_update` to receive an empty configuration, mistakenly believing all configuration items were cleared and falling back to defaults. Additionally, the watching loop uses `except Exception: pass` to silently swallow all exceptions, making watcher failures impossible to troubleshoot.

**Cause**: Two defects combined:
1. `_load_config` overwrites `self._cache` to `{}` on TOML syntax errors/permission errors, but both the background watching thread `_watch_loop` and the cache timeout path `_check_cache_validity` **unconditionally** execute `_emit_config_updated()` after calling `_load_config()`, broadcasting "the empty cache produced by a load failure" as a real change.
2. `_watch_loop`'s `except Exception: pass` does not log anything.

**Root cause chain**:
```
User saves halfway → TOML syntax error
  → _load_config() overwrites _cache = {}
    → _watch_loop unconditionally _emit_config_updated(new_config={})
      → Adapters/modules on_config_update receive an empty configuration
        → Misjudges the configuration as cleared, falls back to defaults
```

**Affected versions**: 2.6.2-dev.1 - 2.7.0-dev.4

**Fixed version**: 2.7.0-dev.5

**Fix**:
1. `_load_config` changed to return `bool`; on TOML syntax errors/permission/other errors, **retain the last valid cache** (no longer overwritten to `{}`), only log a diagnostic message and return `False`
2. `_watch_loop` and `_check_cache_validity` only emit `config.updated` when `_load_config()` returns `True`
3. `_watch_loop`'s `except Exception` changed to log at warning level (added the i18n key `core.config.watcher_error`, synchronized across five languages)

**Fix date**: 2026/07/31

**Regression tests**: `tests/unit/test_unit_config.py` → `test_malformed_toml_preserves_last_valid_cache`, `test_permission_denied_logs_clear_message` (updated to verify cache retention + returning False)

**Severity**: 🟡 Medium

**Type**: Configuration System

---

### [BUG-030] Configuration watcher race condition causing setConfig delayed writes to silently lose data

**Problem**: Multiple users reported that after using `config.setConfig(key, value)` (default `immediate=False`), their module configuration was not written to `config.toml`, while other modules' configurations were written normally. Setting `immediate=True` (forced flush) works around it. Manifestation: configuration written during runtime is lost after the next restart, while configuration generated by startup-time templates is retained.

**Cause**: Two combined defects:
1. **Logic defect**: `_watch_loop` unconditionally `_dirty_keys.clear()` discards all pending write keys when `_check_file_change()` returns `True`. But `_check_file_change()` only compares mtime with `!=`; the framework's own `_flush_config` writing to disk also changes the mtime—although `_flush_config` updates `_config_mtime` after writing, the watcher thread may still observe the mtime difference between the file write and the mtime assignment (as well as on coarse-grained filesystems), misjudging it as an "external modification" and clearing all pending write keys.
2. **Threading defect**: `_watch_loop` operates on `_write_timer`/`_dirty_keys` without holding `_lock`, creating data races with `setConfig` (writes `_dirty_keys` holding the lock) and `_schedule_write` (writes `_write_timer` holding the lock).

**Root cause chain**:
```
Module A setConfig(immediate=True) → flush writes to disk, mtime changes
  → User module setConfig(immediate=False) → enters _dirty_keys, flushes after 5s
    → watcher polls, _check_file_change observes the mtime difference from the earlier self-write
      → _dirty_keys.clear() → user module's pending write keys silently discarded
        → Configuration missing after restart
```

**Affected versions**: 2.6.0 - 2.7.0

**Fixed version**: 2.7.1

**Fix**:
1. Added the `_last_self_write_mtime` field, recorded in sync after `_flush_config` writes to disk; `_check_file_change` first compares against this value when the mtime changes; if matched, it is determined to be its own write and returns `False`
2. `_watch_loop` holds `_lock` for the entire section; on a genuine external modification, `_dirty_keys` is retained (merge semantics); the next flush merges with the external content (dirty keys take priority), no longer calling `clear()`
3. The `getConfig`/`_check_cache_validity` paths are unaffected (their reload never cleared dirty keys anyway)

**Fix date**: 2026/08/06

**Regression tests**: `tests/unit/test_unit_config.py` → `test_self_write_not_detected_as_external`, `test_external_change_preserves_dirty_keys`, `test_flush_merges_dirty_with_external`

**Severity**: 🔴 Critical

**Type**: Configuration System

---

### [BUG-032] Stale value read on "write-then-immediate-read" during the configuration delayed flush period

**Problem**: After `config.setConfig()` (default `immediate=False`, delayed flush of about 5 seconds) writes dotted keys, immediately reading their **parent/ancestor nodes** (e.g., calling `get_erispulse_config()` after `set_erispulse_section("scope.actions.MyModule", {...})`) returns the old value; the written child keys "disappear" until after the flush. "Write-read-write" scenarios such as scoped configuration hot updates are affected (exposed by the 2.8.0 test plugin `/t_section` case).

**Cause**: `setConfig` stores dotted keys in the pending write queue `_dirty_keys` in **flat form**; only `getConfig`'s **exact key lookup** hits the pending write queue; tree path queries (`getConfig("ErisPulse.scope")`) only traverse the cache tree without overlaying pending write values—forming a read-your-write gap during the delayed flush period (only `_flush_config` merges dirty keys into the cache and clears the queue).

**Affected versions**: 2.6.0 - 2.8.0-dev.1

**Fixed version**: 2.8.0-dev.1

**Fix**: `getConfig` introduces pending-write overlay semantics—① exact hit on a pending write key returns directly (original behavior unchanged); ② the pending write key is an ancestor of the query key → take the longest pending write ancestor and resolve the remaining path within its value subtree; ③ the pending write key is a descendant of the query key → build an overlay subtree (`_dirty_overlay`) and deep merge it with the cache subtree (`_deep_merge`, override takes priority, without modifying the original cache object). Without pending write keys, the original fast path is used with zero extra overhead.

**Fix date**: 2026/09/04

**Regression tests**: `tests/unit/test_unit_config.py` → `test_get_config_overlays_dirty_descendant`, `test_get_config_overlay_merges_with_cache_siblings`, `test_get_config_overlay_new_branch`, `test_get_config_dirty_ancestor_query`, `test_get_config_dirty_exact_key_still_wins`

**Severity**: 🟡 Medium

**Type**: Configuration System

---

### [BUG-033] wait_reply pending replies starved by high-priority handlers

**Problem**: While a module calls `wait_reply()` waiting for a user reply, if that reply message is claimed by a higher-priority event handler (`mark_processed()`), the command dispatcher sees the `_processed` flag at the entry and returns directly; the reply matching logic at the end of the dispatcher never executes—the waiting party never receives the reply and can only wait until the timeout returns `None`. Typical trigger scenario: bots using high-priority message handlers (logging/audit/interception types), where all conversational interactions fail randomly.

**Cause**: Reply matching `_check_pending_reply` hangs at the end of `_handle_message` (executed only when no command matches), while the `_processed` check comes before it—the claim check and the reply hit determination are in inverted order. Interactive waiting is a framework-level session continuation mechanism rather than a competing handler, and should not be affected by other handlers' claims.

**Affected versions**: 2.2.0-dev.0 - 2.8.0-dev.1

**Fixed version**: 2.8.0-dev.2

**Fix**: The reply hit determination moved earlier to the entry of `_handle_message` (before the `_processed` check, message events only): first try to complete pending conversations; on hit, the event is marked as processed and subsequent checks naturally short-circuit; on miss, continue with the original command matching flow. Meanwhile, the determination chain delegates to the new interaction session manager (`Core/Event/interaction.py`), incidentally gaining cancel-by-owner and permission re-check capabilities.

**Fix date**: 2026/09/08

**Regression tests**: `tests/unit/test_unit_interaction.py` (`TestRegisterResolve` hit/miss/claim marked), `tests/unit/test_unit_event.py` (wait_reply full chain)

**Severity**: 🟡 Medium

**Type**: Event System / Command System


---

### [BUG-034] persist=False runtime bindings silently wiped by arbitrary subsequent configuration writes

**Problem**: Runtime writes like `scope.set_module(..., persist=False)` only modify in-memory `self._data`; but scope subscribes to the `config.set` / `config.updated` events, so any code writing configuration (such as a module writing its default configuration at load time) triggers scope to rebuild the entire configuration tree from the configuration file, and all previous runtime bindings are silently lost (determination falls back to default-allow), with no log hints. Scenarios depending on runtime bindings (Dashboard "runtime only" switches, module runtime dynamic disabling) regress in behavior after an unrelated module writes configuration.

**Cause**: Root cause chain: `scope.set/delete(persist=False)` only writes memory (`Core/scope.py`) → any `setConfig` triggers the `config.set` event → `_on_config_updated` unconditionally `_load_config()` → `_apply_tree()` wholesale replaces with `self._data = {...}` → runtime bindings not in the configuration file are discarded.

**Affected versions**: 2.8.0-dev.1 - 2.8.0-dev.2
**Fixed version**: 2.8.0-dev.2
**Fix**: Introduced the runtime override layer `_runtime_overrides` (with a deletion sentinel): `persist=False` writes/deletes are recorded into the override layer; after `_apply_tree()` rebuilds the persistence layer, they are replayed in write order, so runtime rules remain valid after any configuration write; `persist=True` writes/deletes clear the corresponding override records (user persistence semantics take priority); `config.set` is filtered precisely by event key, and `config.updated` compares old and new scope sections, rebuilding only when scope actually changed (incidentally avoiding unrelated writes flushing the determination LRU cache); added `unregister_by_owner()` for callers to clean up as a fallback when modules unload. `Core.Event.overrides`'s persist=False runtime overrides had the same problem, fixed synchronously with the override layer architecture.
**Fix date**: 2026/09/09

**Reproduction steps**: ① `scope.set_module("testplat", blocked=["TestB"], persist=False)` → determination False; ② any module executes `config.setConfig("HelpModule", {...})` → triggers scope rebuild; ③ `scope.is_allowed("testplat", None, "TestB")` returns True (expected still False).
**Related**: Issue #432
**Regression tests**: `tests/unit/test_unit_scope.py::TestRuntimeOverrideSurvival` (survival from unrelated writes / tree rebuild replay / deletion sentinel / persistence clearing / precise invalidation / owner cleanup)

**Severity**: 🟡 Medium
**Type**: Configuration System / Runtime

---

### [BUG-035] Configuration panel select options and dict fields rendered as [object Object]

**Problem**: In the WebUI configuration panel, the select field's option dropdown displays `[object Object]` (such as dynamically generated color scheme style options); dict fields without declared control types (such as `stalker_mode`, `knowledge_base` and other nested configuration sections) display `[object Object]` in text boxes, unable to be viewed and edited normally.

**Cause**: Two independent defects: ① The framework i18n parser `_resolve_i18n_text` only restores dictionaries with an `i18n` key; when option labels are dictionaries containing only `default` (dynamic text without an i18n key), they are passed through as-is, and the frontend `esc(label)` string coercion yields `[object Object]`; ② The Dashboard rendering branch only makes JSON textareas for array types; dict values fall into the plain text input branch and are coerced via `String()`. Additionally, if a module mistakenly declares `_schema_meta` as a normal dataclass field (missing the `ClassVar` annotation), it enters the schema as a configuration field, aggravating the confusion.

**Affected versions**: 2.7.0 - 2.8.0-dev.2
**Fixed version**: 2.8.0-dev.2
**Fix**: ① `_resolve_i18n_text` supports restoring dictionaries containing only `default` into text; ② The framework's schema/templates/defaults/population/validation—the five places—uniformly exclude underscore-prefixed fields (mistaken declarations become harmless); ③ Dashboard select option label objects get fallback parsing (`default` priority), dict/table fields rendered as a JSON textarea (the save path writes back via `tp=object` JSON.parse, full round trip).
**Fix date**: 2026/09/09

**Regression tests**: `tests/unit/test_unit_config.py::TestResolveI18nDefaultOnlyDict`, `TestSchemaUnderscoreFieldExclusion`

**Severity**: 🟡 Medium
**Type**: Configuration System

---

### [BUG-036] Configuration writes occasionally fail (ENOENT) when multiple instances share a configuration directory

**Problem**: In Docker deployment scenarios (multiple containers mounting the same host configuration directory), the logs occasionally show two consecutive `Failed to write configuration file ... [Errno 2] No such file or directory: '...config.toml.tmp' -> '...config.toml'`. That configuration write is discarded (the old configuration is fully retained, no configuration loss observed), functionality is unaffected, but the alerts appear repeatedly and interfere with troubleshooting, and the pending configuration items need to wait for the next write to be persisted.

**Cause**: Root cause chain: `_flush_config` / `setConfigTemplate` use a **fixed-name** temporary file `config.toml.tmp` to carry the new content, with `write()` followed directly by `rename()` without `fsync`. When two ErisPulse instances share the same configuration directory, instance B's `open("w")` may **truncate** the temporary file instance A is writing → when A renames, the target has been taken by B or its content truncated, reporting ENOENT (i.e., the two consecutive errors in user logs). In reported cases it only manifested as write failure alerts (old configuration retained); with more extreme interleaved timing, rename could output an empty/half-written `config.toml` (a potential risk, not yet erupted in real environments). In single-instance scenarios, ext4 delayed allocation likewise has a "rename metadata lands before data blocks" crash window (SIGKILL / power loss). `_file_lock` is an in-process `threading.RLock`, with no constraint on cross-process/cross-container writes.

**Affected versions**: 2.2.0-dev.0 - 2.8.0

**Fixed version**: 2.8.1

**Fix**: Configuration writes are unified into `_atomic_write_text()`: same-directory `mkstemp` generates a process-unique temporary file (eliminating fixed-name contention; degrades to last-writer-wins under multiple instances, no more ENOENT) → after writing, `flush + fsync` forces data to disk (eliminating the "rename already effective, data not on disk" window) → `os.replace` atomically replaces the target (atomic on both POSIX/Windows; at any moment the disk holds either the complete old content or the complete new content); on POSIX, additionally fsync the configuration directory. All three write points—`_flush_config`, `setConfigTemplate`, and root directory configuration migration—are switched; the exception path cleanup logic is refactored along with the unique temporary file name. Added **multi-instance detection**: at startup, an advisory lock (POSIX `flock` / Windows `msvcrt.locking`) exclusively holds the configuration directory lock file `.erispulse_config.lock`; if occupied, an i18n warning is output (without blocking startup); the lock is automatically released by the OS at process exit, with no ghost locks.

**Fix date**: 2026/09/13

**Reproduction steps**: ① Two containers mount the same host `config/` directory and run ErisPulse simultaneously; ② Any instance triggers a configuration write (such as a module registering default configuration); ③ Observe the log showing an ENOENT write failure alert, with this write discarded (old configuration retained).

**Related**: User report (1Panel containers ×2)

**Regression tests**: `tests/unit/test_unit_config_atomic_write.py` (content fully written / no temporary file residue / original file kept on write failure / dual-instance concurrent writes file always valid / lock file creation / multi-instance warning / migration atomic write)

**Severity**: 🟢 Minor

**Type**: Configuration System

---

### [BUG-037] Space-separated command names can never be triggered after registration

**Problem**: After registering subcommands with space-separated multi-token command names (such as `@command("admin add")`), the commands register normally and appear in help lists, but when a user sends `/admin add`, the bot never responds—the input is matched by the parent token command as `admin` + argument `["add"]`; if the parent token is also not registered, there is completely no response. Only dot-separated naming (`admin.reload`, a single token as a whole) can avoid it.

**Cause**: Root cause chain: `CommandHandler.__call__` stores any command name (including space forms) as-is into the flat `self.commands` dictionary → the dispatch phase `_try_execute_command` only takes the message's first token to match (`cmd_name = parts[0]`) → multi-token command names as dictionary keys can never be found. The two phases of registration and matching have inconsistent assumptions about command name space, with no registration-time warning whatsoever (silent failure).

**Affected versions**: Since the command system was introduced - 2.8.0

**Fixed version**: 2.8.1

**Fix**: The matching layer changed to **longest prefix matching**: attempts are made level by level from the longest candidate (`" ".join(parts[:n])`, with n capped by the maximum token count cache `_max_name_tokens` of registered command names/aliases); on hit, execution proceeds with the remaining tokens as arguments, and the downstream scope/ACL/override/master/permission chains naturally apply to the full command name. Supporting semantics: when parent and child coexist, unregistered subcommand input falls back to the parent command (historical behavior unchanged); when a subcommand does not declare `permission`, it inherits from the nearest ancestor command along the parent chain that declared permission (protecting the parent command protects all of its subcommands); when only single-token commands are registered, the first round hits directly, with dispatch overhead the same as before. `unregister` / `unregister_by_owner` / full cleanup maintain the token count cache in sync.

**Fix date**: 2026/09/13

**Reproduction steps**: ① Register `@command("admin add")` in a module; ② Send `/admin add x`; ③ Before the fix, no response (or caught by a simultaneously registered `/admin` as an argument), after the fix `admin add` triggers and `get_command_args()` is `["x"]`.

**Regression tests**: `tests/unit/test_unit_command_subcommand.py` (longest prefix matching / subcommand-only triggering / three-level nesting / case-sensitive both modes / single and multi-token aliases / event payload full name / lifecycle hooks full name / permission inheritance six cases / ACL glob full name / master / unregister fallback and cache recalculation)

**Severity**: 🟡 Medium

**Type**: Event System

---

### [BUG-038] persist=False runtime bindings written to disk along with persistence writes, "resurrecting" from disk after module unload

**Problem**: Runtime bindings written with `scope.set(path, value, persist=False)` (documented as not written to disk, invalidated on process restart, cleaned up on module unload) get written differentially into the user's `config.toml` along with any unrelated `persist=True` write (the default, such as module `set_module` / WebUI saving configuration); afterwards, even if the module unloads and unregisters the runtime binding, on the next configuration reload the binding still "resurrects" from disk and continues to take effect, persisting even after process restart—contrary to the semantic contract of "runtime bindings are not written to disk", and extremely hard to troubleshoot.

**Cause**: Root cause chain: `ScopeManager.set()` first writes the value into the in-memory configuration tree `_data` (runtime bindings likewise write directly into `_data`) → the persistence branch makes a deep-copy snapshot of **the entire `_data`** and submits it to `update_erispulse_config` for differential persistence → the snapshot mixes in values from `persist=False` bindings. `delete(persist=True)` has the same origin: handing the live reference (`parent` node) of `_data` to the delayed-write dirty queue; runtime modifications to sibling keys under that node during the delayed flush period get written to disk along with it, and the live reference has a cross-write pollution window while lingering in the dirty queue.

**Affected versions**: 2.8.0-dev.2 - 2.9.0-dev.0

**Fixed version**: 2.9.0-dev.2

**Fix**: Introduced the persistence baseline `_persisted_tree` (refreshed with the disk-loaded, validated tree when the configuration tree is rebuilt) as the mirror of disk truth: `set(persist=True)` applies only this change onto the baseline before committing the differential; runtime bindings never enter the persisted content; "write then read immediately" now uses the in-memory final-state snapshot for direct restoration, no longer rebuilding via `_apply_tree` to avoid polluting the baseline. `delete(persist=True)` follows the same approach: applying the deletion onto the baseline and handing the deep copy of the baseline subtree to the persistence layer; `set_action`'s wholesale replacement semantics first deletes with the same approach then writes, so old rule keys do not linger in the persisted content.

**Fix date**: 2026/09/27

**Reproduction steps**: ① In a module execute `scope.set("bots.p.debug_mode", {"blocked": ["X"]}, persist=False)`; ② Trigger any persistence write (such as another module calling `set_module`); ③ Open `config/config.toml`—`debug_mode` is visibly written (before the fix); ④ After unloading the module (runtime binding unregistered), trigger a configuration reload—`scope.get("bots.p.debug_mode")` still returns the binding value.

**Regression tests**: `tests/unit/test_unit_scope.py::TestPersistBaseline` (runtime bindings not persisted with unrelated persistence writes / no resurrection after unload unregister and config reload / delete commits baseline subtree without runtime sibling keys / set_action replacement leaves no residual keys / cache_size configuration effective)

**Severity**: 🔴 Critical

**Type**: Configuration System

---

### [BUG-039] Read-write inconsistency when section writes and dotted writes coexist (dotted overrides lost)

**Problem**: Within the delayed flush window, when a section write (`setConfig("Mod", {...})`, such as a `BaseModule.cfg` write-back) and a dotted write (`setConfig("Mod.key", v)`, such as a configuration hot update / test tool override) coexist in the same section, there are two variants: Variant A (read path)—`getConfig("Mod")` section read returns the old section-write snapshot, not seeing the later dotted override (the dotted read path is normal); Variant B (write path, more severe)—when the dotted write comes first and the section write after (the common timing of a test tool injecting an override → module `self.cfg = ...` write-back), flush applies dirty keys in insertion order, the section write wholesale replaces the section, and the **dotted override is permanently lost on disk**. The production combination of "configuration hot update + module runtime write-back" can trigger it, unrelated to the test environment (exposed by ErisPulse-DailyCard test feedback).

**Cause**: `getConfig`'s ① segment (exact hit on `_dirty_keys`) early-`return`s `self._dirty_keys[key]`, completely bypassing the ④ segment `_dirty_overlay` descendant overlay; `_flush_config` applies dirty keys in `_dirty_keys` insertion order; when the section write happens to come after the dotted write, the dotted value gets wholesale replaced. Also: the ① segment returns the dirty queue's **original object reference**; callers modifying the returned dict in place would directly alter the state pending to be written to disk.

**Affected versions**: 2.6.0 - 2.9.0-dev.2

**Fixed version**: 2.9.0-dev.2

**Fix**: Within the dirty window, unified to **specificity-first** semantics—dotted (more specific) pending write values take priority over section (broader) pending write values, with the read path and the disk path following the same approach: ① `getConfig`, after exact hit on a pending write key, still overlays `_dirty_overlay` descendant pending write values (non-dict values return the overlay subtree, the same approach as the ③+④ scalar corner cases); ② `_flush_config` sorts dirty keys by path depth before applying (sections/ancestors first, dotted/descendants after, with stable sort preserving same-depth write order). Cost: within the same dirty window (about 5 seconds), a section write-back cannot override a still-pending dotted write—after the read path fix, read-modify-write naturally carries the dotted values, so the actual impact is minimal. ③ `getConfig` returns involving pending write values (exact hit / ancestor subtree / overlay merge) changed to `copy.deepcopy` isolated copies, no longer leaking dirty queue internal references; the no-dirty-key fast path and pure cache read behavior are unchanged.

**Fix date**: 2026/09/28

**Reproduction steps**: ① `setConfig("FB.y", 1)`; ② `setConfig("FB", {"z": 2})`; ③ `force_save()`—before the fix, the disk only has `[FB] z = 2` (y lost); after the fix, `{"y": 1, "z": 2}`; Variant A: after steps ①② without flushing, directly `getConfig("FB")`—before the fix it does not contain `y`; after the fix it is visible.

**Regression tests**: `tests/unit/test_unit_config.py::TestSectionAndDottedDirtyConsistency` (Variant A both insertion orders / Variant B persisted regardless of order / three-level mixed survival / isolated copies / ancestor subtree isolation)

**Severity**: 🟡 Medium

**Type**: Configuration System


### [BUG-040] Command trailing arguments of platform-segmented messages silently lost

**Problem**: When a platform splits one message into multiple text segments (such as `/kick` and arguments separated by a mention segment, or IME segmentation), command dispatch only takes the first text segment for matching—`/at @xxx 123` parses to `at` with no arguments; commands declaring `args=` directly report "missing arguments", with no trace left.
**Cause**: The text extraction loop in `command.py` takes the first `type=="text"` segment and then `break`s; remaining segments (including all non-text segments) are discarded.
**Affected versions**: 2.6.0 (introduced with command dispatch) - 2.10.0
**Fixed version**: 2.10.1-dev.0
**Fix**: Command text changed to collect all text segments in order, joined by spaces; mention/image interlayers no longer cause commands to be completely unparseable; also added tolerance for malformed segments (`message` being None/string/non-dict segments no longer break the dispatcher).
**Regression tests**: tests/unit/test_unit_command_multiseg.py

**Severity**: 🟡 Medium
**Type**: Event System

### [BUG-041] Rejected commands rerun the whole chain via alt_message: duplicate replies and permission function side effects triggered twice

**Problem**: When the adapter's `alt_message` differs from the message segment text (such as alt containing an @ text prefix), after a matched command is rejected by scope/ACL/master/permission, the dispatcher reruns the whole chain with alt_message—the user receives two "insufficient permission" replies, and custom permission functions (often with database query/counting side effects) are called twice.
**Cause**: The rejection path's `return False` shares the same return value with "command not matched"; the dispatcher thereby believes it can try the alt fallback; while the event was already claimed before the rejection, the rerun only additionally executed the reply and the permission determination.
**Affected versions**: 2.9.0 (governance/permission chain formed) - 2.10.0
**Fixed version**: 2.10.1-dev.0
**Fix**: Text processing changed to a three-state contract (unmatched/consumed/rejected)—after hitting a registered command (whether rejected or not), there is no longer an alt fallback; the alt fallback is kept only when no command is matched at all.
**Regression tests**: tests/unit/test_unit_command_multiseg.py::test_denied_command_not_rerun_via_alt

**Severity**: 🟡 Medium
**Type**: Event System

### [BUG-042] wait_reply registered inside command handlers immediately consumed by the same triggering message

**Problem**: When calling `wait_reply` / registering an interaction wait inside a command execution body, the wait is immediately hit by the same command message—the interaction flow's first question is skipped, and the "user reply" is actually the command text itself (answering the wrong question / data pollution).
**Cause**: `_handle_message` calls `interaction.resolve` once at both the beginning and the end of the method; after command execution, the ending second resolve hits waits newly registered during execution; when cmdpass is off, the alt-missing scenario is determined to be an empty string and allowed through directly, aggravating the problem.
**Affected versions**: 2.8.0 (introduced with the interaction session system) - 2.10.0
**Fixed version**: 2.10.1-dev.0
**Fix**: The dispatch chain converged to a single `interaction.resolve` (at the beginning of the method), removing the ending second call; waits are uniformly consumed by the next message.
**Regression tests**: tests/unit/test_unit_command_multiseg.py::test_wait_reply_not_consumed_by_command_trigger

**Severity**: 🟡 Medium
**Type**: Event System

### [BUG-043] select() multiple waits on the same key: the later one silently cancels the former

**Problem**: When multiple expectations of `event.select()` derive the same session key (same user with different pattern, multiple session expectations, etc.), the later-registered path cancels the earlier-registered path with a "conflict", and select directly throws `InteractionCancelled` instead of the documented timeout return `(None, None)`.
**Cause**: Each path independently calls `interaction.register`, whose mutual-exclusion semantics cancels old waits with the same key via `REASON_CONFLICT`; the comment claiming "multiple paths for the same user do not conflict with each other because of event copies" does not hold—copies only change user_id; the keys of multiple paths for the same user are completely identical.
**Affected versions**: 2.9.0 (select introduced) - 2.10.0
**Fixed version**: 2.10.1-dev.0
**Fix**: select changed to aggregated waiting—all expectations merged into a single entry of a custom matcher (registered by key set, sharing the same future); any path hit returns the corresponding index; multiple paths on the same key naturally coexist.
**Regression tests**: tests/unit/test_unit_command_multiseg.py::test_select_same_user_multi_branch

**Severity**: 🟡 Medium
**Type**: Event System

### [BUG-044] BaseConverter.at() produces OB11 legacy "at" segments, unrecognized by mention detection across the framework

**Problem**: When adapters use `BaseConverter.at()` to assemble inbound events, `must_at_bot` / `has_mention()` / `on_at_message` are all blind—@bot commands silently fail in groups.
**Cause**: `at()` produces `{"type": "at"}` (OB11 form), while all mention detection and construction sides of the framework (MessageBuilder/sending decorators) use OB12's `"mention"`, with the two tracks coexisting and no warning whatsoever.
**Affected versions**: Introduced no earlier than 2.5.0 - 2.10.0
**Fixed version**: 2.10.1-dev.0
**Fix**: `at()` changed to produce `{"type": "mention", "data": {"user_id": ...}}` (method name kept as an alias, with a new `mention` alias added).
**Regression tests**: tests/unit/test_unit_command_multiseg.py::test_converter_at_produces_mention

**Severity**: 🟡 Medium
**Type**: Adapter

### [BUG-045] On adapters without alt_message, interaction primitives time out permanently and command pass-through fails

**Problem**: When adapters only fill message segments without `alt_message`: `confirm` / `choose` / `collect` wait forever for users' plaintext replies (such as "yes"); registered commands during the waiting period can never pass through for execution; `Event.get_text()` returns empty strings, causing scaffold examples to silently fail.
**Cause**: The above paths all directly take the `alt_message` string with no message-segment fallback—under the framework's contract that "alt_message is an adapter-optional field", segment-only filling is a legal form.
**Affected versions**: Each interaction primitive's introduction version - 2.10.0
**Fixed version**: 2.10.1-dev.0
**Fix**: Unified to the `alt_message`-first + text-segment-fallback `extract_text` approach (five value-taking/validation points of the interaction primitives, cmdpass determination, `Event.get_text()/get_message_text()`).
**Regression tests**: tests/unit/test_unit_command_multiseg.py

**Severity**: 🟡 Medium
**Type**: Event System

### [BUG-046] Declarative configuration templates' nested sub-table headers drifting to top-level tables

**Problem**: When configuration declared with nested dataclasses (ConfigClass containing nested dataclass fields) first generates the configuration template, the sub-table header `[Nested]` lands at the file's top level rather than within the component section—adapters reading `cfg.nested_field` get no value; `config.full.example` is likewise misplaced.
**Cause**: The template generator renders relative table headers for nested dataclasses (`[Nested]`), while TOML table header semantics are absolute paths from the root; `setConfigTemplate`'s old implementation moved the parsed table objects into the component section, and `full.example` directly concatenated text; neither path re-anchored the relative table headers under the component path.
**Affected versions**: 2.10.0 - 2.10.1 (nested dataclass template rendering introduced with that version)
**Fixed version**: 2.10.2
**Fix**: `setConfigTemplate` precisely re-anchors table headers according to the sub-table path set parsed from the template (`[Nested]` → `[ComponentName.Nested]`); the `config.full.example` generation side changed to pass `_prefix` to directly produce absolute table headers.
**Regression tests**: tests/unit/test_unit_config.py::TestTomlclassEngineMigration::test_template_write_idempotent_and_nested_anchored

**Severity**: 🟡 Medium
**Type**: Configuration System / Adapter

---

### [BUG-047] Service directory full enumeration misses lazy-loaded modules

**Problem**: `sdk.module.services()` full directory skips all uninstantiated (lazy-loaded) modules—even modules that declared `meta.services` do not appear in the directory; consumers using the directory as their discovery entry point (AI agents, help modules, etc.) cannot discover their services; single-module precise query `services("Name")` and topology `get_topology()` are unaffected.
**Cause**: `ModuleManager.services()`'s full enumeration branch, for modules without a contract cache (unloaded), still unconditionally `continue`s **after resolving the contracts on-site**—the original intent was to skip "modules that do not declare services", but in practice it skipped unloaded modules entirely; loaded modules are unaffected because their contract cache is written at load time.
**Affected versions**: 2.9.0 - 2.10.1 (module RPC and service directory introduced with 2.9.0)
**Fixed version**: 2.10.2
**Fix**: Removed the unconditional skip, uniformly adjudicated by "skip only if the resolution result is empty"; unloaded modules resolve `get_meta().services` on-site (the same approach as the `module.call()` whitelist); modules that declared services enter the directory as usual.
**Regression tests**: tests/unit/test_unit_module_rpc.py::TestServicesDirectory::test_lazy_declared_module_in_full_directory

**Severity**: 🟡 Medium
**Type**: Loading System

### [BUG-048] Conversation inbox query API loses message attribution (sender and event metadata)

**Problem**: Records returned by all inbox query interfaces (`get()` / `get_by_trace()` / `event.history()`) only have `role/text/ts/event_id`—the `sender` column already existing in the storage layer is dropped by the query layer; in group chat replay, messages from different members are indistinguishable at the API layer (the AI mistakes member B for the previous conversation partner A); inbound records also do not archive metadata such as the nickname at the event moment, so retrospective queries get "the current nickname" rather than "the nickname at the time".
**Cause**: When the `sender` column was added in 2.8.0, the comment already noted it was for "restoring the message source during replay", but neither the Select nor the return construction carried it (implementation oversight); metadata archiving was never designed—`append()` has no meta channel, and the table structure has no corresponding column.
**Affected versions**: 2.8.0 - 2.11.0 (sender column introduced with 2.8.0)
**Fixed version**: 2.11.1-dev.0
**Fix**: Added the `meta` column (whitelist contract: inbound nickname/self_id/sub_type/message_id, outbound sending context and module; old tables auto-migrate, silently falling back to `{}` when the backend does not support ALTER); `append()` added the `meta` parameter threaded through the in-memory buffer and batch persistence; `get` / `recent` / `get_by_trace` / `event.history` uniformly return `sender` + `meta` (JSON corruption falls back to `{}`).
**Related**: #467 (same batch #468 / #469 / #470)
**Regression tests**: tests/unit/test_unit_transcript_attribution.py::TestSenderMetaReadback / TestMetaMigration

**Severity**: 🟡 Medium
**Type**: Conversation Inbox / Storage System

### [BUG-049] Inbound bot self-sent message echoes recorded as user, polluting inbox attribution

**Problem**: When platforms/protocol ends with message echo enabled (OneBot v11 `report-self-message`, Telegram outgoing, etc.) report the bot's own sent messages as message events, the inbox records them all with `role="user"`—the bot's own speech and real user input are indistinguishable; downstream modules treat bot self-speech as user input (the AI responds accordingly to what the "user" said), and role statistics are distorted.
**Cause**: The inbound auto-recording point (`Core/adapter.py`) unconditionally records `role="user"` for all `event_type == "message"`, without consuming the `self` field for bot echo determination—while the bot auto-discovery logic immediately after it was already consuming the same field (available at record time, but the record logic missed it).
**Affected versions**: 2.8.0 - 2.11.0 (inbox auto-recording introduced with 2.8.0)
**Fixed version**: 2.11.1-dev.0
**Fix**: Before recording, identify echoes by `self.user_id == user_id`, handled in three modes per the new configuration `ErisPulse.transcript.self_echo`: `"bot"` (default) records `role="bot"` + `sender=self_id` + `meta.self_echo=true`; `"skip"` does not record; `"user"` keeps the old behavior. Non-echo platforms (self missing or unequal) regress field by field unchanged.
**Related**: #470 (depends on #467's meta column to carry the self_echo marker)
**Regression tests**: tests/unit/test_unit_transcript_attribution.py::TestSelfEcho

**Severity**: 🟡 Medium
**Type**: Adapter / Conversation Inbox
