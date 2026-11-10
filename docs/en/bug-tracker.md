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

### [BUG-001] Event handlers registered multiple times causing events to be processed multiple times

**Issue**: When registering multiple handlers using decorators like `@message` or `@notice`, the same event is triggered multiple times, leading to commands being executed multiple times and logs being duplicated.

**Cause**: The `BaseEventHandler` registers handlers to the adapter event bus without deduplication logic. Each decorator registers a handler once, resulting in multiple calls when events are dispatched.

**Affected Versions**: 2.2.0-dev.0 - 2.2.1-dev.0

**Fixed Version**: 2.2.1-dev.0

**Fix**: Optimized `BaseEventHandler` to ensure each event type is registered only once with the adapter, preventing repeated triggers.

**Fix Date**: 2025/08/18

**Severity**: 🔴 Critical

**Type**: Event System

---

### [BUG-002] Init command adapter configuration path type error

**Issue**: When using the `ep init` command for interactive initialization, selecting a configuration adapter results in a type error:

```
Interactive initialization failed: unsupported operand type(s) for /: 'str' and 'str'
```

**Cause**: In version 2.3.7, when adjusting the configuration file path, the method parameter types were inconsistent. The `_configure_adapters_interactive_sync` method received a `str` type parameter but internally used the `Path` `/` operator to concatenate paths.

**Affected Versions**: 2.3.7 - 2.3.9-dev.1

**Fixed Version**: 2.3.9-dev.1

**Fix**: Changed the parameter type of the `_configure_adapters_interactive_sync` method from `str` to `Path`, passing `Path` objects directly when called.

**Fix Date**: 2026/03/23

**Severity**: 🟡 Moderate

**Type**: CLI

---

### [BUG-003] Command events fail after restart

**Issue**: After calling `sdk.restart()`, commands registered via `@command` are not triggered, resulting in no robot response after sending a command.

**Cause**: After `adapter.shutdown()` clears the event bus, the `_linked_to_adapter_bus` status of `BaseEventHandler` is not reset to `False`, causing the `_process_event` method to consider it already linked to the adapter bus and skip re-linking.

**Affected Versions**: 2.2.x - 2.4.0-dev.2

**Fixed Version**: 2.4.0-dev.3

**Fix**: Added `_linked_to_adapter_bus` status tracking; after `clear_handlers()` disconnects the bus, the next `register()` automatically re-links, adapting to shutdown/restart scenarios.

**Fix Date**: 2026/04/09

**Severity**: 🔴 Critical

**Type**: Event System

---

### [BUG-004] Lifecycle event handlers not cleaned up

**Issue**: After `sdk.restart()`, old lifecycle event handlers still exist and trigger repeatedly, causing the same event to be processed multiple times.

**Cause**: The `lifecycle._handlers` dictionary was never cleared in `uninit()`, resulting in old and new handlers coexisting after restart.

**Affected Versions**: 2.3.0 - 2.4.0-dev.2

**Fixed Version**: 2.4.0-dev.3

**Fix**: In the cleanup process of `Uninitializer` (after all events are submitted), clear `lifecycle._handlers`.

**Fix Date**: 2026/04/09

**Severity**: 🟡 Moderate

**Type**: Runtime

---

### [BUG-005] Event.is_friend_add/is_friend_delete detail_type inconsistent with OB12 standard

**Issue**: `Event.is_friend_add()` checks `detail_type == "friend_add"`, `Event.is_friend_delete()` checks `detail_type == "friend_delete"`, but the OneBot12 standard defines `detail_type` values as `"friend_increase"` and `"friend_decrease"`. This inconsistency with the values used in `notice.py`'s `on_friend_add`/`on_friend_remove` decorators causes handlers registered via decorators to fail when triggered, as the corresponding `is_friend_add()`/`is_friend_delete()` methods return `False`.

**Cause**: `wrapper.py` uses non-standard naming, while `notice.py` uses the correct OB12 standard naming.

**Affected Versions**: Since implementation

**Fixed Version**: 2.4.2-dev.1

**Fix**: Changed `is_friend_add()`'s matching value from `"friend_add"` to `"friend_increase"`, and `is_friend_delete()` from `"friend_delete"` to `"friend_decrease"`.

**Fix Date**: 2026/04/13

**Severity**: 🟡 Moderate

**Type**: Event System

---

### [BUG-006] adapter.clear() not cleaning _started_instances causing incorrect state after restart

**Issue**: The `AdapterManager.clear()` method clears `_adapters`, `_adapter_info`, handlers, and `_bots`, but omits `_started_instances`. If `clear()` is called while the adapter is running, `_started_instances` retains dangling references, causing incorrect state judgment after restart.

**Cause**: When `_started_instances` was introduced in 2.4.0-dev.1, it was not synchronized for cleanup in `clear()`.

**Affected Versions**: 2.4.0-dev.1 - 2.4.2-dev.0

**Fixed Version**: 2.4.2-dev.1

**Fix**: Added `self._started_instances.clear()` in the `clear()` method.

**Fix Date**: 2026/04/13

**Severity**: 🟡 Moderate

**Type**: Adapter

---

### [BUG-007] command.wait_reply() using deprecated asyncio.get_event_loop()

**Issue**: The `CommandHandler.wait_reply()` method uses `asyncio.get_event_loop()` to create futures and get timestamps, which has been deprecated since Python 3.10. In asynchronous contexts, `asyncio.get_running_loop()` should be used. This is inconsistent with `wrapper.py`'s `wait_for()` method in the same file, which uses `get_running_loop()`.

**Cause**: The old API was used during development, and the newly added `wait_for()` method used the correct API but did not retroactively fix the old code.

**Affected Versions**: 2.3.0-dev.0

**Fixed Version**: 2.4.2-dev.1

**Fix**: Replaced two instances of `asyncio.get_event_loop()` in `command.py` with `asyncio.get_running_loop()`.

**Fix Date**: 2026/04/13

**Severity**: 🟢 Minor

**Type**: Event System

---

### [BUG-008] Bot offline event submitted repeatedly during shutdown

**Issue**: When calling `adapter.shutdown()` to close all adapters, `_update_bot_status()` repeatedly submits Bot offline events during the shutdown process, causing the same batch of Bots to be marked offline multiple times and triggering multiple `adapter.bot.offline` lifecycle events.

**Cause**: The Bot status tracking system introduced in 2.4.0-dev.1 did not set a "shutting down" flag during `shutdown()`, so `_update_bot_status()` could not distinguish between normal offline and cascading offline during shutdown.

**Affected Versions**: 2.4.0-dev.1 - 2.4.2-dev.1

**Fixed Version**: 2.4.2-dev.1

**Fix**: Added `_is_being_shutdown` flag in `AdapterManager`, set to True at the start of `shutdown()` and cleared at the end; `_update_bot_status()` checks this flag and skips repeated submissions during shutdown.

**Fix Date**: 2026/04/21

**Severity**: 🟡 Moderate

**Type**: Adapter

---

### [BUG-009] LazyModule synchronous access to BaseModule causing incomplete initialization

**Issue**: When users access lazy-loaded BaseModule attributes in synchronous contexts, the module uses `loop.create_task()` for asynchronous initialization but does not wait, leading to race conditions when attributes are accessed before initialization completes.

**Cause**: `_ensure_initialized()` uses `loop.create_task(self._initialize())` and returns immediately without ensuring initialization completes.

**Affected Versions**: 2.4.0-dev.0 - 2.4.2-dev.1

**Fixed Version**: 2.4.2-dev.2

**Fix**: In synchronous contexts, BaseModule initialization is changed to use `asyncio.run(self._initialize())` to ensure initialization completes before returning. The transparent proxy feature is maintained, so users do not need to perceive the difference between synchronous and asynchronous contexts.

**Fix Date**: 2026/04/21

**Severity**: 🟡 Moderate

**Type**: Loading System

---

### [BUG-010] Multi-threaded configuration system writing causing data loss

**Issue**: In multi-threaded environments, when multiple threads call `config.setConfig()` simultaneously, the `read-modify-write` operation in `_flush_config()` is not atomic, potentially causing partial write loss.

**Cause**: Although `_flush_config()` uses `RLock`, there is no file lock protection between file read and write, and `_schedule_write`'s Timer may be triggered multiple times, causing overwrite.

**Affected Versions**: 2.3.0 - 2.4.2-dev.1

**Fixed Version**: 2.4.2-dev.2

**Fix**:
1. Added file lock mechanism (`_file_lock`) to ensure atomic file operations
2. Used temporary file writing followed by atomic renaming (`os.replace`/`os.rename`)
3. Improved `_schedule_write`'s Timer cancellation and rescheduling logic

**Fix Date**: 2026/04/21

**Severity**: 🔴 Critical

**Type**: Configuration System

---

### [BUG-011] Windows Ctrl+C unable to stop program

**Issue**: When running `python main.py` directly on Windows, pressing Ctrl+C does not terminate the program. After the program starts normally and outputs the router server information, Ctrl+C has no response, requiring the process to be forcibly killed via Task Manager. However, it can be stopped normally when started via `epsdk run`—but `epsdk run` runs through a subprocess model.

**Cause**: The `serve()` function of Hypercorn ASGI server internally registers its own SIGINT handler via `signal.signal(SIGINT, handler)`, overriding Python's default `KeyboardInterrupt` handling mechanism. When Hypercorn is started as a background task via `asyncio.create_task()`, its internal shutdown process cannot be triggered normally (as it expects the `worker_serve` mode), causing the Ctrl+C signal to be swallowed by Hypercorn without triggering any cleanup actions.

**Affected Versions**: 2.3.6 - 2.4.2

**Fixed Version**: 2.4.3-dev.0

**Fix**:
1. Switched the ASGI server from Hypercorn to Uvicorn (`pyproject.toml` dependency change)
2. Started the server directly using `uvicorn.Server._serve()`, **bypassing** the `capture_signals()` signal handling context manager
3. Implemented graceful shutdown via `server.should_exit = True`, canceling background tasks on timeout
4. Synchronously removed the subprocess running model and `runtime/cleanup.py` cleanup module (subprocess cleanup mechanism no longer needed)

**Fix Date**: 2026/04/28

**Severity**: 🔴 Critical

**Type**: CLI / Runtime

---

### [BUG-012] Hot restart failing to load updated module code

**Issue**: After executing `sdk.restart()` for a soft restart, the new code (e.g., new API routes) of modules/adapters upgraded via `epsdk install` does not take effect, and old logic is still run. The latest code must be loaded by completely restarting the process.

**Cause**: `_do_restart()` calls `entry_point.load()` during re-initialization, but this function returns cached old module objects from `sys.modules` instead of reloading from disk.

**Affected Versions**: Early versions - 2.4.3-dev.1

**Fixed Version**: 2.4.3-dev.1

**Fix**: After `uninit()` and before `init()`, clear the cache of loaded modules/adapters from `sys.modules` to ensure `entry_point.load()` loads the latest code from disk. Added `_collect_top_level_modules()` and `_invalidate_module_cache()` helper methods to deduce top-level module names via `top_level.txt` or entry-point value.

**Fix Date**: 2026/05/03

**Severity**: 🔴 Critical

**Type**: Loading System / Runtime

---

### [BUG-013] Module loading strategy sort logic error

**Issue**: `ModuleLoadStrategy` provides a `priority` field to declare module initialization priority, but the loading strategy implementation has a flaw, causing modules to be initialized in an unexpected order, actually following the `entry_points()` default order. When modules have initialization dependencies, the correct initialization order cannot be ensured through `priority`.

**Cause**: The sorting logic in the loading strategy implementation is flawed; `initialize_modules()` does not sort the module list by `priority`.

**Affected Versions**: 2.3.4 - 2.4.5-dev.2

**Fixed Version**: 2.4.5-dev.3

**Fix**: Before traversing `initialize_modules()`, sort the module list by `priority` in descending order. Modules with the same priority maintain their original relative order (stable sort).

**Fix Date**: 2026/05/15

**Severity**: 🟡 Moderate

**Type**: Loading System

---

### [BUG-014] Adapter middleware returning None causing event data loss

**Issue**: In `adapter.emit()` when executing the OneBot12 middleware chain, if a middleware returns `None` (e.g., forgetting to `return data`), subsequent middlewares and all event handlers receive `processed_data` as `None`, causing event processing to fail completely.

**Cause**: The middleware chain implementation `processed_data = await middleware(processed_data)` does not check if the return value is `None`, directly overwriting the previous processing result.

**Affected Versions**: unknown - 2.4.5-dev.3

**Fixed Version**: 2.4.5-dev.4

**Fix**: When a middleware returns `None`, ignore the return value, retain the original data, and output a warning-level log.

**Fix Date**: 2026/05/15

**Severity**: 🔴 Critical

**Type**: Adapter / Event System

---

### [BUG-015] Configuration file path dependent on working directory

**Issue**: The `ConfigManager`'s configuration file path defaults to the relative path `"config/config.toml"`, which relies on `os.getcwd()` for resolution at runtime. If the working directory changes during runtime (e.g., via `os.chdir()`), configuration file read/write operations point to the wrong location, causing configuration loss or reading old data.

**Cause**: In `__init__`, the relative path is directly stored without resolving it to an absolute path during initialization.

**Affected Versions**: 2.3.7 - 2.4.5-dev.3

**Fixed Version**: 2.4.5-dev.4

**Fix**: In `ConfigManager.__init__()`, if the passed path is relative, automatically resolve it to an absolute path using `os.path.abspath()`.

**Fix Date**: 2026/05/15

**Severity**: 🟡 Moderate

**Type**: Configuration System

---

### [BUG-016] BaseStorage confusing storing value None with key not existing

**Issue**: `BaseStorage.get_multi()` / `__getattr__()` cannot distinguish between "key not existing" and "key's value is None", treating a user explicitly stored `None` as if the key does not exist.

**Cause**: The retrieval logic directly uses `value is None` to determine if the key exists, lacking an independent "missing" marker.

**Affected Versions**: Early versions - 2.4.6-dev.6

**Fixed Version**: 2.4.6-dev.6

**Fix**: Introduced `_SENTINEL` sentinel value to distinguish "key not existing" from "value is None", eliminating confusion.

**Fix Date**: 2026/06/07

**Severity**: 🟡 Moderate

**Type**: Storage

---

### [BUG-017] WebSocket route auto_accept flag lost after service restart

**Issue**: After a service restart (e.g., `sdk.restart()`), all WebSocket routes' `auto_accept` configuration revert to `False`, causing originally expected auto-accept connections to hang, with clients receiving no response for a long time, manifesting as a stuck WebSocket connection.

**Cause**: `_restore_routes_from_records()` hardcodes `auto_accept` to `False` when restoring routes from persistent records, not reading the original record's value; simultaneously, the route storage tuple expanded from a binary tuple to a ternary tuple without synchronously updating the restore logic.

**Affected Versions**: 2.3.8-dev.0 - 2.4.6-dev.6

**Fixed Version**: 2.4.6-dev.6

**Fix**: The route storage tuple expanded to `(handler, auth_handler, auto_accept)`, and `_restore_routes_from_records()` reads the real `auto_accept` value from the record instead of hardcoding `False`.

**Fix Date**: 2026/06/07

**Severity**: 🔴 Critical

**Type**: Routing

---

### [BUG-018] HTTP/WS client concurrent calls causing crash and connection leaks

**Issue**: The HTTP and WebSocket clients in `Core/client.py` have multiple stability defects in concurrent scenarios, leading to connection leaks or process crashes:
- Concurrent calls to `ClientWebSocket.receive()` result in aiohttp raising `Concurrent call to receive() is not allowed`
- Concurrent calls to `_get_http_session()` / `_get_ws_session()` may create multiple sessions, and `_drain_sessions()` does not close old connections, causing connection leaks
- The exception handling order in `request()` is incorrect: `except ClientConnectionError` (ErisPulse exception) is never triggered, aiohttp's connection errors are caught by the general `except Exception`, leading to the "retry connection + session rebuild" logic (dead code) never executed
- `send_json()` ignores the `mode="binary"` parameter; `_get_ws_session()` does not pass default request headers

**Cause**: The client was initially implemented (2.4.6-dev.5) without concurrency protection and exception classification, mishandling aiohttp's exception hierarchy and ErisPulse's custom exception inheritance.

**Affected Versions**: 2.4.6-dev.5 - 2.4.8

**Fixed Version**: 2.4.8

**Fix**:
1. Added `_recv_lock` to serialize all `receive()` / `receive_text()` / `receive_bytes()` calls
2. Added `_session_lock` to protect session creation; `_drain_sessions()` changed to an async method and truly closes old sessions
3. Reconstructed `request()` exception handling order: `asyncio.TimeoutError` → `aiohttp.ClientConnectionError` (triggers session rebuild) → `aiohttp.ClientError` → `ClientError` (transparent pass) → `Exception`
4. Fixed `send_json()`'s mode handling, `_get_ws_session()`'s default request header pass, `close()`'s concurrent race, and `HttpResponse.__aexit__`'s repeated `release()`

**Fix Date**: 2026/06/12

**Severity**: 🔴 Critical

**Type**: Client

---

### [BUG-019] Adapter hot reload causing route conflicts and reload failure

**Issue**: When a third-party module (e.g., Dashboard) triggers adapter hot reload, or when adapter startup fails and retries, due to the uncleaned old routes (e.g., `onebot11_default`) from the previous registration, a `WebSocket path ... already registered` conflict is thrown, causing reload failure. A full process restart is required to recover.

**Cause**: `AdapterManager.shutdown()` only cleans routes via `unregister_all_by_namespace(platform)`, but adapters (e.g., OneBot11) register WebSocket routes using `onebot11_{account_name}` as the namespace, resulting in a granularity mismatch and an empty cleanup operation; startup failure retry paths also do not clean up previous residual routes.

**Affected Versions**: Early versions - 2.4.9

**Fixed Version**: 2.4.9

**Fix**:
1. Route registration automatically tracks `owner → namespace` ownership relationships via `current_owner` ContextVar
2. Added `unregister_all_by_owner(owner)`, cleaning up by owner during stop/restart, covering fine-grained namespaces
3. Added `_stop_adapter(platform)` primitive (stop equals cleanup), binding stopping the adapter and reclaiming its registered resources in a single call; `restart()` and startup failure retries both go through this entry
4. Added framework-level `adapter.restart(platform)` API, which third-party modules should call instead of directly manipulating adapter instances

**Fix Date**: 2026/06/12

**Severity**: 🔴 Critical

**Type**: Adapter / Routing

---

### [BUG-020] Subprocess mode `ep run <script>` cannot find subpackages in script directory

**Issue**: When running a script using `ep r .\main.py` in non-hot-reload mode, if the script has relative imports (e.g., `from qg import ...`), it reports `No module named 'qg'`. However, the `--reload` mode works fine.

**Cause**: The non-hot-reload mode directly calls `runpy.run_path()` to execute the script, which does not automatically add the script's directory to `sys.path`. In contrast, the `--reload` mode runs via `subprocess.Popen`, where the subprocess automatically inherits the current working directory, making `sys.path[0]` the script's directory, allowing it to work.

**Affected Versions**: 2.5.0 - 2.5.2-dev.0

**Fixed Version**: 2.5.2-dev.0

**Fix**: Before calling `runpy.run_path()`, manually insert the script's directory into `sys.path[0]`.

**Fix Date**: 2026/06/27

**Severity**: 🟡 Moderate

**Type**: CLI

---

### [BUG-021] SQL query builder rejecting valid wildcards and list expressions

**Issue**: `SQLiteQueryBuilder`'s `_build_select_sql()` calls `_validate_identifier()` for all SELECT columns, which uses a strict whitelist regex `^[a-zA-Z_][a-zA-Z0-9_]*$`, causing legitimate SQL syntax to be incorrectly judged as unsafe column names:
- `SELECT *` — `*` is a standard SQL wildcard
- `SELECT COUNT(*)` — aggregate function
- `SELECT users.name` — qualified column name
- `SELECT col AS alias` — column alias

Among these, `Select("*")` is used by modules like Cron, causing module `on_load` execution to fail and the module to fail to load.

**Cause**: In version 2.4.6, SQL injection protection was enhanced, introducing the `_validate_identifier()` whitelist validation. This validation is applied to all column names, but does not distinguish between read-side (SELECT/ORDER BY) and write-side (INSERT/UPDATE). SELECT columns allow complex SQL expressions and should not be restricted by simple identifier whitelists.

**Affected Versions**: 2.4.6 - 2.5.2-dev.1

**Fixed Version**: 2.5.2-dev.2

**Fix**: Changed the SELECT/ORDER BY column validation from whitelist mode to blacklist mode:
1. Added `_validate_select_column()` function, only blocking SQL injection dangerous characters (`;` `'` `"` `--` `/*` `*/` `\x00` newline)
2. Allowed any valid SQL column expression (`*`, `table.*`, `table.column`, `COUNT(*)`, `col AS alias`, etc.)
3. INSERT/UPDATE column names still maintain strict whitelist validation (only allow simple identifiers)

**Fix Date**: 2026/06/29

**Severity**: 🔴 Critical

**Type**: Storage

---

### [BUG-022] _resolve_account() account resolution regression (_accounts_data not filled)

**Issue**: After the 2.5.2 configuration system refactor, multi-account adapters declaring `AccountConfigClass` fail to resolve accounts when calling methods like `wait_reply`, `reply` that require sending messages. Even if the adapter correctly configures multi-account information, account resolution still fails.

**Cause**: In 2.5.2-dev.5, `_load_accounts()` (responsible for reading configuration + validation + filling `_accounts_data`) was refactored into `_ensure_accounts_exist()` (only generates configuration template), but `_resolve_account()` still checks `self._accounts_data is None`. Since `_ensure_accounts_exist()` no longer fills `_accounts_data`, this attribute remains `None`, causing `_resolve_account()` to prematurely return `(None, None)`, rendering account resolution completely ineffective.

**Root Cause Chain**:
```
_load_accounts() was deleted
  → __init__ no longer fills _accounts_data
    → _accounts_data is always None
      → _resolve_account() checks _accounts_data is None → return (None, None)
        → downstream calls to _resolve_account() (e.g., call_api) receive None
          → trigger error
```

**Affected Versions**: 2.5.2-dev.5 - 2.5.2

**Fixed Version**: 2.5.3

**Fix**: In `BaseAdapter.__init__`, after `_ensure_accounts_exist()`, restore the filling of `_accounts_data`:
```python
if self.AccountConfigClass is not None:
    self._ensure_accounts_exist()
    self._accounts_data = self.accounts  # restore filling, data source is the real-time read accounts property
```
The `_resolve_account()` logic remains unchanged, fully backward compatible:
- Adapters not declaring `AccountConfigClass`: `_accounts_data` remains `None` → return `(None, None)`
- Adapters declaring `AccountConfigClass`: `_accounts_data` is filled → normal resolution
- Adapters overwriting `_load_accounts` or manually setting `_accounts_data`: overwrite after `super().__init__()` with highest priority

**Fix Date**: 2026/07/07

**Severity**: 🔴 Critical

**Type**: Adapter / Configuration System

---

### [BUG-023] Adapter cache not refreshed after account configuration modification causing account resolution failure

**Issue**: After users modify the account configuration of multi-account adapters (e.g., filling in token) via Dashboard, the adapter still uses the old cache, and calling message-sending-related methods reports `未找到可用账户 (account_id=default)`. The new configuration must be loaded by restarting the process.

**Cause**: `_accounts_data` is only read from the configuration storage once in `BaseAdapter.__init__`, and is not refreshed afterwards. `AdapterManager._run_adapter()` and `restart()` do not re-read the account configuration before calling `adapter.start()`, causing the cache to be out of sync with the actual configuration.

**Affected Versions**: 2.4.6 - 2.5.4

**Fixed Version**: 2.5.4

**Fix**: In `AdapterManager._run_adapter()` and `restart()`, refresh `adapter._accounts_data = adapter.accounts` before calling `adapter.start()`, ensuring the latest configuration is used each time the adapter starts.

**Fix Date**: 2026/07/09

**Severity**: 🔴 Critical

**Type**: Adapter / Configuration System

---

### [BUG-024] storage.set() writing large numeric ID keys triggers OOM Kill

**Issue**: When calling `storage.set()` to write a nested key path containing a large numeric field (e.g., QQ group ID `871684833`), the process is killed by the container OOM (exit code -9), causing the service to crash and become unrecoverable.

**Cause**: In the recursive implementation of `_set_nested_value`, pure numeric fields in the nested key path are misjudged by `isdigit()` as list indices, triggering `current.extend([None] * (index - len(current) + 1))`, which attempts to allocate hundreds of millions of elements, instantly exhausting memory.

**Root Cause Chain**:
```
Key path contains a pure numeric field (e.g., group ID 871684833)
  → isdigit() misjudges as array index
    → extend([None] * (871684833 - len(current) + 1))
      → attempts to allocate hundreds of millions of elements
        → memory exhausted → container OOM Kill (exit code -9)
```

**Affected Versions**: 2.5.1 - 2.5.5

**Fixed Version**: 2.5.5

**Fix**:
1. Always use a dictionary when pre-creating intermediate layers, no longer guessing the container type based on whether the next segment is a number
2. When setting the final value, only handle indexing if the container itself is a list and the index is less than `STORAGE_MAX_LIST_INDEX` (10000); ignore large indices safely
3. Change the recursive implementation to an iterative one, eliminating potential infinite recursion risks in the original code
4. Add `STORAGE_MAX_LIST_INDEX` constant to `Core/constants.py`, centrally managing the safe index upper limit

**Fix Date**: 2026/07/10

**Reproduction Steps**:
```python
# Trigger by writing a nested key path containing a large number field (e.g., QQ group ID)
await sdk.storage.aset("groups.871684833.name", "某群")
# → Process memory surges instantly, killed by OOM
```

**Regression Tests**: `tests/unit/test_unit_storage.py` adds 4 regression test cases
- `test_nested_key_numeric_segment_as_dict_key` — precisely reproduces OOM scenario
- `test_nested_key_numeric_segment_multiple` — multiple consecutive numeric fields as dictionary keys
- `test_nested_key_existing_list_index_set_within_limit` — existing list index write within limit
- `test_nested_key_list_index_safety_limit` — safety limit verification for large indices

**Severity**: 🔴 Critical

**Type**: Storage

---

### [BUG-025] on_config_update callback not core-routed

**Issue**: The `on_config_update(old, new)` callback is defined in the base class (`BaseModule` / `BaseAdapter`), but the core framework does not associate it with the configuration change event. The actual behavior is: when modifying configuration via the configuration management panel, it can be triggered, but when manually editing `config.toml` or calling `setConfig()` code, `on_config_update` is not triggered.

**Cause**: `ConfigManager` emits `config.set` / `config.updated` lifecycle events when configuration changes, but lacks the subscription logic to forward these events to each component's `on_config_update` method.

**Root Cause Chain**:
```
Core does not subscribe to config.set / config.updated
  → configuration change events have no forwarding
    → on_config_update is not called
      → manual file editing / code setConfig does not trigger hot update callback
```

**Affected Versions**: All versions

**Fixed Version**: 2.6.2

**Fix**: `ModuleManager` / `AdapterManager` register `config.set` (covers code `setConfig()` path) and `config.updated` (covers manual file editing path) event subscriptions, match by configuration key prefix and call the corresponding component's `on_config_update`, passing type-safe configuration objects. Also fix `_flush_config()` writing file without synchronizing `_config_mtime`, avoiding framework self-writing being mistakenly judged as external modification and repeatedly triggering `config.updated` by file monitoring task.

**Compatibility Note**: Configuration hot update is now centrally maintained by the framework core. Previously, the configuration management panel triggered the logic, which has been removed, so after upgrading the framework, the configuration management panel must also be upgraded, otherwise duplicate triggers (core + panel each call once) will occur. The `on_config_update` method signature and semantics remain unchanged, subclasses need no modification.

**Fix Date**: 2026/07/23

**Severity**: 🟡 Moderate

**Type**: Configuration System

---

### [BUG-026] notice/request event reply target inference error

**Issue**: When calling `event.reply()` in a group notice event (e.g., member joining group `group_member_increase`), the message is sent to the user who triggered the event's private chat, not the group where the event occurred. Similarly, in friend notice events, the reply target may be incorrect.

**Cause**: `infer_receive_type()` directly returns the event's `detail_type` as the session type. For message events, this is correct (`detail_type` values `private`/`group` are session types), but for notice/request events, `detail_type` is a semantic subtype (e.g., `group_member_increase`, `friend_increase`), not a session type. Subsequent `convert_to_send_type()` and `get_id_field()` lookups in the mapping table fail to find the value, defaulting to `"user"` / `"user_id"`, causing the reply target to be incorrect.

**Root Cause Chain**:
```
notice event detail_type="group_member_increase"
  → infer_receive_type() directly returns "group_member_increase"
    → convert_to_send_type("group_member_increase") not in mapping table → default to "user"
    → get_id_field("group_member_increase") not in mapping table → default to "user_id"
      → target_id = event["user_id"]  ← new member's private chat (not the group)
```

**Affected Versions**: All versions

**Fixed Version**: 2.7.0-dev.3

**Fix**: `infer_receive_type()` adds a check—`detail_type` is returned directly only if it is a known session type (standard or custom type); otherwise, the correct session type is inferred based on the ID field (`group_id` / `channel_id` / `user_id`, etc.).

**Regression Tests**: `tests/unit/test_unit_session_type.py` → `TestNoticeRequestTypeInference` (10 test cases)

**Fix Date**: 2026/07/29

**Severity**: 🟢 Minor

**Type**: Event System

---

### [BUG-027] Route rate limiting cleanup task uses fixed window causing long window rate limit rules to fail

**Issue**: When setting route rate limiting rules to long windows (e.g., `100/hour`, `{"requests": 100, "window": 3600}`), rate limiting is ineffective—practically behaving like `100/minute` (up to ~6000 requests per hour), failing to provide the expected hourly protection.

**Cause**: `_apply_rate_limit` parses the actual `window` (up to 3600 seconds) per route, and per-request checks use this window; however, the background cleanup task `_cleanup_expired_rate_limits` uses a fixed constant `DEFAULT_RATE_LIMIT_WINDOW_SECS` (60 seconds) as the unified cleanup threshold for all routes. Thus, time stamps earlier than 60 seconds are cleared prematurely by the cleanup task, preventing the hour window from accumulating nearly 100 records, severely weakening the rate limit.

**Root Cause Chain**:
```
_apply_rate_limit parses window=3600 (100/hour)
  → per-request check uses 3600s retention time (correct)
  → but _cleanup_expired_rate_limits uses fixed max_window=60s for cleanup
    → time stamps earlier than 60s are cleared
      → the hour window always retains only the most recent 1 minute of records
        → 100/hour effectively degrades to ~100/minute (relaxed by ~60x)
```

**Affected Versions**: 2.6.0-dev.0 - 2.7.0-dev.4

**Fixed Version**: 2.7.0-dev.5

**Fix**: Added `_rate_limit_windows: dict[str, int]` to record each route's actual window; `_apply_rate_limit` writes the window on first entry creation; `_cleanup_expired_rate_limits` changes to clean up by each key's own window (fallback to default if missing); cleanup deletion and `stop()` synchronously maintain both dictionaries.

**Fix Date**: 2026/07/31

**Regression Tests**: `tests/unit/test_unit_router.py` → `TestRateLimit::test_cleanup_respects_per_route_window`

**Severity**: 🔴 Critical

**Type**: Routing

---

### [BUG-029] Configuration listener task broadcasts incomplete TOML and silently swallows exceptions

**Issue**: When the user manually edits `config.toml` and saves it halfway (producing a temporary syntax error), the configuration monitoring background thread detects the mtime change, reloads the configuration, but fails to load and still broadcasts an empty configuration `{}` via the `config.updated` event, causing adapters/modules' `on_config_update` to receive an empty configuration, mistakenly perceiving all configuration items as cleared and reverting to default values. Additionally, the listener loop uses `except Exception: pass` to silently swallow all exceptions, making it impossible to diagnose watcher failures.

**Cause**: Two defects叠加:
1. `_load_config` overwrites `self._cache` to `{}` when TOML syntax error/permission error occurs, but the background listener thread `_watch_loop` and cache timeout path `_check_cache_validity` unconditionally execute `_emit_config_updated()` after calling `_load_config()`, broadcasting the "empty cache from failed load" as a real change.
2. `_watch_loop`'s `except Exception` does not log any messages.

**Root Cause Chain**:
```
User saves halfway → TOML syntax error
  → _load_config() overwrites _cache = {}
    → _watch_loop unconditionally _emit_config_updated(new_config={})
      → adapters/modules on_config_update receive empty configuration
        → mistakenly perceive configuration as cleared, revert to default values
```

**Affected Versions**: 2.6.2-dev.1 - 2.7.0-dev.4

**Fixed Version**: 2.7.0-dev.5

**Fix**:
1. `_load_config` changed to return `bool`; on TOML syntax error/permission/other errors, retain the last valid cache (do not overwrite to `{}`), only record diagnostic logs and return `False`
2. `_watch_loop` and `_check_cache_validity` emit `config.updated` only if `_load_config()` returns `True`
3. `_watch_loop`'s `except Exception` changed to warn-level logging (new i18n key `core.config.watcher_error`, synchronized in five languages)

**Fix Date**: 2026/07/31

**Regression Tests**: `tests/unit/test_unit_config.py` → `test_malformed_toml_preserves_last_valid_cache`, `test_permission_denied_logs_clear_message` (updated to verify cache retention + return False)

**Severity**: 🟡 Moderate

**Type**: Configuration System

---

### [BUG-030] Configuration watcher race condition causing setConfig delayed write silently loses data

**Issue**: Multiple users reported that after using `config.setConfig(key, value)` (default `immediate=False`) to write configuration, their module configurations did not write to `config.toml`, while other modules' configurations were normal. Setting `immediate=True` (force flush) could avoid this. The result is: configuration written during runtime is lost after next restart, while configuration generated during startup is retained.

**Cause**: Two overlapping defects:
1. **Logical defect**: `_watch_loop` unconditionally `_dirty_keys.clear()` when `_check_file_change()` returns `True`. But `_check_file_change()` only uses `!=` to compare mtime, and the framework's own `_flush_config` writing also changes mtime—although `_flush_config` updates `_config_mtime` after writing, the watcher thread may still observe the mtime difference between file writing and mtime assignment (and on coarse-grained file systems), mistakenly judging it as "external modification" and clearing all dirty keys.
2. **Thread defect**: `_watch_loop` operates `_write_timer`/`_dirty_keys` without holding `_lock`, causing data races with `setConfig` (holding lock to write `_dirty_keys`), `_schedule_write` (holding lock to write `_write_timer`).

**Root Cause Chain**:
```
Module A setConfig(immediate=True) → flush writes, mtime changes
  → User module setConfig(immediate=False) → enters _dirty_keys, flushes after 5s
    → watcher polls, _check_file_change observes mtime difference from previous self-write
      → _dirty_keys.clear() → user module's dirty keys are silently discarded
        → configuration missing after restart
```

**Affected Versions**: 2.6.0 - 2.7.0

**Fixed Version**: 2.7.1

**Fix**:
1. Added `_last_self_write_mtime` field; `_flush_config` records it after writing; `_check_file_change` compares it first when mtime changes, matches then returns `False`
2. Entire `_watch_loop` holds `_lock`; truly external modification retains `_dirty_keys` (merge semantics), next flush merges with external content (dirty keys take precedence), no longer `clear()`
3. `getConfig`/`_check_cache_validity` path is unaffected (reload does not clear dirty keys)

**Fix Date**: 2026/08/06

**Regression Tests**: `tests/unit/test_unit_config.py` → `test_self_write_not_detected_as_external`, `test_external_change_preserves_dirty_keys`, `test_flush_merges_dirty_with_external`

**Severity**: 🔴 Critical

**Type**: Configuration System

---

### [BUG-032] Configuration delay write period "write-then-read" reads old values

**Issue**: After `config.setConfig()` (default `immediate=False` delayed ~5 seconds write), writing a dotted key and immediately reading its parent/ancestor node (e.g., `set_erispulse_section("scope.actions.MyModule", {...})` then calling `get_erispulse_config()`) returns the old value, the written sub-key "disappears", only visible after flush. Scope configuration hot update and other "write-read-write" scenarios are affected (2.8.0 test plugin `/t_section` use case exposes this).

**Cause**: `setConfig` stores dotted keys in the dirty queue `_dirty_keys` in flat form, only `getConfig`'s exact key query hits the dirty queue; tree path query (e.g., `getConfig("ErisPulse.scope")`) only walks the cache tree, not overlaying dirty values—during the delay flush period (`_flush_config` merges dirty keys into cache and clears the queue), a read-you-write gap forms.

**Affected Versions**: 2.6.0 - 2.8.0-dev.1

**Fixed Version**: 2.8.0-dev.1

**Fix**: `getConfig` introduces dirty overlay semantics—① exact match dirty key returns directly (original behavior unchanged); ② dirty key is the query key's ancestor → take the longest dirty ancestor and parse the remaining path in its value subtree; ③ dirty key is the query key's descendant → build an overlay subtree (`_dirty_overlay`) and deep merge with the cache subtree (`_deep_merge`, override priority, does not modify original cache object). No dirty key uses the original fast path, zero additional overhead.

**Fix Date**: 2026/09/04

**Regression Tests**: `tests/unit/test_unit_config.py` → `test_get_config_overlays_dirty_descendant`, `test_get_config_overlay_merges_with_cache_siblings`, `test_get_config_overlay_new_branch`, `test_get_config_dirty_ancestor_query`, `test_get_config_dirty_exact_key_still_wins`

**Severity**: 🟡 Moderate

**Type**: Configuration System

---

### [BUG-033] wait_reply suspended replies starved by high-priority processors

**Issue**: When a module calls `wait_reply()` to wait for a user reply, if the reply message is claimed by a higher-priority event handler (`mark_processed()`), the command dispatcher sees the `_processed` flag at the entry and returns directly, leaving the reply matching logic at the end of the dispatcher never executed—the waiting party receives no reply and can only wait until timeout returns `None`. Typical trigger scenario: robots using high-priority message processors (recording/auditing/blocking types) cause random failure of all dialog interactions.

**Cause**: Reply matching `_check_pending_reply` is placed at the end of `_handle_message` (only executed if command does not match), while `_processed` checking is before it—the order of claim checking and reply hit determination is reversed. Interactive waiting is a framework-level session continuation mechanism, not a competing processor, and should not be affected by other processors' claim.

**Affected Versions**: 2.2.0-dev.0 - 2.8.0-dev.1

**Fixed Version**: 2.8.0-dev.2

**Fix**: Move reply hit determination to the entry of `_handle_message` (before `_processed` checking, only for message events): first attempt to complete the suspended conversation, if hit, the event is marked as processed, and the subsequent checks naturally short-circuit; if not hit, continue the original command matching process. Also delegate the determination chain to a new session manager (`Core/Event/interaction.py`), gaining the ability to cancel by affiliation and permission review.

**Fix Date**: 2026/09/08

**Regression Tests**: `tests/unit/test_unit_interaction.py` (TestRegisterResolve hit/miss/claim flag), `tests/unit/test_unit_event.py` (wait_reply full chain)

**Severity**: 🟡 Moderate

**Type**: Event System / Command System

### [BUG-034] Runtime bindings with persist=False in scope are silently overridden by subsequent configuration writes

**Issue**: `scope.set_module(..., persist=False)` and similar runtime writes only modify memory `self._data`; however, scope subscribes to `config.set` / `config.updated` events, and any code writing configuration (e.g., a module loading its own default configuration) triggers scope to rebuild the configuration tree from the configuration file, silently discarding all previous runtime bindings (reverting to default allow), with no log warning. Scenarios depending on runtime bindings (e.g., Dashboard "runtime-only" switches, dynamic module disable during runtime) revert to default behavior after unrelated module configuration writes.

**Root Cause**: Root cause chain: `scope.set/delete(persist=False)` only writes memory (`Core/scope.py`) → any `setConfig` triggers `config.set` event → `_on_config_updated` unconditionally calls `_load_config()` → `_apply_tree()` replaces `self._data = {...}` in its entirety → runtime bindings not present in the configuration file are discarded.

**Affected Versions**: 2.8.0-dev.1 - 2.8.0-dev.2  
**Fixed Version**: 2.8.0-dev.2  
**Fix Details**: Introduced a runtime overlay layer `_runtime_overrides` (including deletion sentinel): `persist=False` writes/deletes are recorded in the overlay layer, and `_apply_tree()` rebuilds the persistent layer and replays in write order, ensuring runtime rules remain effective after any configuration write; `persist=True` writes/deletes clear corresponding overlay records (user persistence semantics take precedence); `config.set` filters events by key precisely, `config.updated` compares new and old scope nodes, and only rebuilds when scope actually changes (including avoiding LRU cache invalidation due to unrelated writes); added `unregister_by_owner()` for module unload cleanup by caller. `Core.Event.overrides` has a similar issue with persist=False runtime overrides, which is also fixed with the overlay architecture.  
**Fix Date**: 2026/09/09  

**Reproduction Steps**:  
① `scope.set_module("testplat", blocked=["TestB"], persist=False)` → returns False;  
② Any module executes `config.setConfig("HelpModule", {...})` → triggers scope rebuild;  
③ `scope.is_allowed("testplat", None, "TestB")` returns True (expected to remain False).  
**关联**: Issue #432  
**Regression Tests**: `tests/unit/test_unit_scope.py::TestRuntimeOverrideSurvival` (survival of unrelated writes / tree rebuild replay / deletion sentinel / persistence clear / precise invalidation / owner cleanup)  

**Severity**: 🟡 Medium  
**Type**: Configuration System / Runtime  

---

### [BUG-035] Configuration panel select options and dict fields rendered as [object Object]

**Issue**: In the WebUI configuration panel, select field options display as `[object Object]` (e.g., dynamically generated color style options); undeclared control type dict fields (e.g., `stalker_mode`, `knowledge_base`, etc.) display as `[object Object]` in text boxes, making them impossible to view or edit.

**Root Cause**: Two independent defects: ① The framework's i18n resolver `_resolve_i18n_text` only restores dictionaries with an `i18n` key, and option labels that are dictionaries with only a `default` key (without an i18n key for dynamic text) are passed through as-is, resulting in `[object Object]` from the frontend `esc(label)` string coercion; ② Dashboard rendering branches only apply JSON textarea for array types, and dict values fall into the plain text input branch and are coerced by `String()`. Additionally, if a module mistakenly declares `_schema_meta` as a regular dataclass field (missing `ClassVar` annotation), it becomes a configuration field in the schema, exacerbating the confusion.

**Affected Versions**: 2.7.0 - 2.8.0-dev.2  
**Fixed Version**: 2.8.0-dev.2  
**Fix Details**:  
① `_resolve_i18n_text` supports dictionaries with only a `default` key, restoring them as text;  
② Framework schema/templates/default values/filling/validation exclude all fields with underscore prefixes in five places (harmless if mistakenly declared);  
③ Dashboard select option label objects are fallback parsed (prioritizing `default`), and dict/table fields are rendered as JSON textarea (saving path by `tp=object` JSON.parse backwrite, complete round trip).  
**Fix Date**: 2026/09/09  

**Regression Tests**: `tests/unit/test_unit_config.py::TestResolveI18nDefaultOnlyDict`, `TestSchemaUnderscoreFieldExclusion`  

**Severity**: 🟡 Medium  
**Type**: Configuration System  

---

### [BUG-036] Configuration write failures (ENOENT) when multiple instances share config directory

**Issue**: In Docker deployment scenarios (multiple containers mounting the same host config directory), logs occasionally show two consecutive `Failed to write configuration file ... [Errno 2] No such file or directory: '...config.toml.tmp' -> '...config.toml'`. This configuration write is discarded (old configuration is fully retained, no configuration loss observed), functionality is unaffected, but repeated alerts interfere with troubleshooting, and pending configuration items must wait for the next write to be written to disk.

**Root Cause**: Root cause chain: `_flush_config` / `setConfigTemplate` uses a **fixed-name** temporary file `config.toml.tmp` to carry new content, `write()` without `fsync` directly `rename()`. When two ErisPulse instances share the same config directory, instance B's `open("w")` may **truncate** the temporary file that instance A is writing to → when A renames, the target has already been taken or truncated by B, resulting in ENOENT (i.e., the two consecutive error logs in the user's log). In the reported case, only a write failure alert is observed (old configuration retained); if the timing is more extreme, rename may output an empty or partially truncated `config.toml` (a potential risk, not yet manifested in real environments). In single-instance scenarios, ext4 delayed allocation also has a "rename metadata before data block is written" crash window (SIGKILL / power loss). `_file_lock` is an in-process `threading.RLock`, providing no constraint for cross-process/cross-container writes.

**Affected Versions**: 2.2.0-dev.0 - 2.8.0  
**Fixed Version**: 2.8.1  
**Fix Details**: Configuration writes are unified to `_atomic_write_text()`: generate a unique temporary file per process in the same directory (`mkstemp`, eliminating fixed-name contention, degenerating to last-writer-wins in multi-instance scenarios, no more ENOENT) → after writing, `flush + fsync` forces data to disk (eliminating the "rename effective, data not written" window) → `os.replace` atomically replaces the target (atomic on POSIX/Windows, at any moment the disk has either complete old content or complete new content); additionally `fsync` the configuration directory on POSIX. Three write points (`_flush_config`, `setConfigTemplate`, root directory configuration migration) are switched; cleanup logic for exception paths is restructured with the unique temporary filename. Added **multi-instance detection**: at startup, an advisory lock (`flock` on POSIX / `msvcrt.locking` on Windows) exclusively holds the configuration directory lock file `.erispulse_config.lock`; if occupied, an i18n warning is output (does not block startup), and the lock is automatically released by the OS when the process exits, with no ghost locks.

**Fix Date**: 2026/09/13  

**Reproduction Steps**:  
① Two containers mount the same host `config/` directory and run ErisPulse simultaneously;  
② Trigger a configuration write in any instance (e.g., module registering default configuration);  
③ Observe ENOENT write failure alerts in the logs, with this write discarded (old configuration retained).  

**关联**: User report (1Panel container ×2)  

**Regression Tests**: `tests/unit/test_unit_config_atomic_write.py` (complete content write / no temporary file residue / write failure preserves original file / double instance concurrent write always valid / lock file creation / multi-instance warning / migration atomic write)  

**Severity**: 🟢 Minor  
**Type**: Configuration System  

---

### [BUG-037] Commands with space-separated names never get triggered after registration

**Issue**: After registering a subcommand with a space-separated multi-token command name (e.g., `@command("admin add")`), the command can be registered and appears in the help list, but when the user sends `/admin add`, the bot never responds—the input is matched as `admin` + parameter `["add"]` by the parent token command; if the parent token is also unregistered, there is no response at all. Only using dot-separated naming (e.g., `admin.reload`, as a single token) can avoid this.

**Root Cause**: Root cause chain: `CommandHandler.__call__` stores any command name (including space-separated forms) directly into the flattened `self.commands` dictionary → at dispatch time, `_try_execute_command` only matches the first message token (`cmd_name = parts[0]`) → multi-token command names as dictionary keys are never found. The registration and matching stages have inconsistent assumptions about command name space, and there is no warning during registration (silent failure).

**Affected Versions**: From introduction of command system to 2.8.0  
**Fixed Version**: 2.8.1  
**Fix Details**: The matching layer is changed to **longest prefix matching**: from the longest candidate (`" ".join(parts[:n])`, n capped by the maximum token count of registered command names/aliases `_max_name_tokens`) try down step by step, and execute with remaining tokens as parameters upon match; downstream scope/ACL/overwrites/master/permission chain naturally applies to the full command name. Accompanying semantics: when parent and child coexist, unregistered subcommands fall back to the parent command (unchanged historical behavior); if a subcommand does not declare `permission`, it inherits the nearest ancestor command's declared permission (protecting the parent command protects all its subcommands); only when registering a single-token command is the first round matched, and the dispatch overhead is consistent with the original. `unregister` / `unregister_by_owner` / full cleanup also maintain the token count cache.

**Fix Date**: 2026/09/13  

**Reproduction Steps**:  
① Register `@command("admin add")` in a module;  
② Send `/admin add x`;  
③ Before the fix, there is no response (or it is caught by the simultaneously registered `/admin` as a parameter), after the fix, `admin add` triggers and `get_command_args()` is `["x"]`.  

**Regression Tests**: `tests/unit/test_unit_command_subcommand.py` (longest prefix matching / only subcommand triggers / three-level nesting / case-sensitive two modes / single and multi-token alias / event payload full name / lifecycle hook full name / permission inheritance six cases / ACL glob full name / master / unregistration fallback and cache recalculation)  

**Severity**: 🟡 Medium  
**Type**: Event System  

---

### [BUG-038] Runtime bindings with persist=False are persistently written to disk, reviving after module unload

**Issue**: Runtime bindings written with `scope.set(path, value, persist=False)` (documented as not writing to disk, invalidating after process restart, and cleaning up after module unload) are included in any unrelated `persist=True` write (default, such as module `set_module` or WebUI saving configuration) and written to the user's `config.toml`; after the module is unloaded and the runtime binding is unregistered, the binding is "revived" from disk and continues to be effective on the next configuration reload, and persists after process restart—contradicting the "runtime binding not writing to disk" semantic contract, and extremely difficult to troubleshoot.

**Root Cause**: Root cause chain: `ScopeManager.set()` first writes the value into the memory configuration tree `_data` (runtime bindings are also directly written into `_data`) → the persistence branch makes a deep copy snapshot of the entire `_data` and submits it to `update_erispulse_config` for differential writing to disk → the snapshot mixes in the values of `persist=False` bindings. `delete(persist=True)` is the same source: the live reference (parent node) is handed over to the delayed dirty queue, and during the period the dirty queue lingers, runtime modifications to sibling keys of the node are written to disk together, and the live reference exists in the dirty queue during the cross-write pollution window.

**Affected Versions**: 2.8.0-dev.2 - 2.9.0-dev.0  
**Fixed Version**: 2.9.0-dev.2  
**Fix Details**: A persistence baseline `_persisted_tree` (the configuration tree refreshed with the disk-loaded, validated tree as the mirror of disk truth) is introduced: `set(persist=True)` only applies the current change to the baseline and submits the differential, never including runtime bindings in the persistence content; "write and immediately read" is restored using a memory final state snapshot directly, without going through `_apply_tree` to avoid polluting the baseline. `delete(persist=True)` is the same口径: apply the deletion to the baseline and hand over a deep copy of the baseline subtree to the persistence layer; `set_action` replaces semantics first delete according to the same口径 and then write, old rule keys do not remain in the persistence content.

**Fix Date**: 2026/09/27  

**Reproduction Steps**:  
① In a module, execute `scope.set("bots.p.debug_mode", {"blocked": ["X"]}, persist=False)`;  
② Trigger any persistent write (e.g., another module calls `set_module`);  
③ Open `config/config.toml`, and see `debug_mode` has been written (before fix);  
④ After the module is unloaded (the runtime binding is unregistered), trigger a configuration reload, and `scope.get("bots.p.debug_mode")` still returns the bound value.  

**Regression Tests**: `tests/unit/test_unit_scope.py::TestPersistBaseline` (runtime bindings do not write to disk with unrelated persistent writes / do not revive after unload and configuration reload / delete submits baseline subtree without runtime sibling keys / set_action replacement leaves no residual keys / cache_size configuration takes effect)  

**Severity**: 🔴 Severe  
**Type**: Configuration System  

---

### [BUG-039] Inconsistent read/write when section write and dotted write coexist (dotted overwrite lost)

**Issue**: During the delayed flush window, when both section write (`setConfig("Mod", {...})`, such as `BaseModule.cfg` writing back) and dotted write (`setConfig("Mod.key", v)`, such as configuration hot-reload/test tool overwrite) coexist in the same section, there are two variants: Variant A (read path) — `getConfig("Mod")` returns the old section write snapshot, not seeing the later dotted overwrite (dotted read path is normal); Variant B (write path, heavier) — dotted write first, section write later (common timing of test tool injection overwrite → module `self.cfg = ...` writing back), flush applies dirty keys in insertion order, section write overall replaces the section, **dotted overwrite is permanently lost on disk**. The production environment "configuration hot-reload + module runtime write-back" combination can trigger this, unrelated to the test environment (ErisPulse-DailyCard test feedback exposed).

**Root Cause**: `getConfig` first segment (exact hit `_dirty_keys`) returns `self._dirty_keys[key]` early, completely bypassing the fourth segment `_dirty_overlay` descendant overlay; `_flush_config` applies dirty keys in insertion order, and section write happens after dotted write, so the dotted value is replaced. Also: the first segment returns dirty queue **original object reference**, and callers modifying the returned dict in-place directly change the pending-to-disk state.

**Affected Versions**: 2.6.0 - 2.9.0-dev.2  
**Fixed Version**: 2.9.0-dev.2  
**Fix Details**: During the dirty window, unify to **specificity-first semantics** — dotted (more specific) pending write values take precedence over section (wider) pending write values, read path and flush path are the same口径: ① `getConfig` after exact hit pending write key still overlays `_dirty_overlay` descendant pending write values (non-dict values return overlaid subtrees, same口径 as ③+④ scalar edge cases); ② `_flush_config` applies dirty keys in path depth order (section/ancestor first, dotted/descendant last, stable sort maintains insertion order within same depth). Cost: within the same dirty window (about 5 seconds), section write-back cannot overwrite still-pending dotted write — after read path fix, read-modify-write naturally carries dotted values, actual impact surface is minimal. ③ Involved pending write values `getConfig` return (exact hit / ancestor subtree / overlay merge) is changed to `copy.deepcopy` isolation copy, no longer leaks dirty queue internal reference; no dirty key fast path and pure cache read behavior unchanged.

**Fix Date**: 2026/09/28  

**Reproduction Steps**:  
① `setConfig("FB.y", 1)`;  
② `setConfig("FB", {"z": 2})`;  
③ `force_save()` — before fix, disk only has `[FB] z = 2` (y lost), after fix `{"y": 1, "z": 2}`; Variant A: after steps ①②, not flush directly `getConfig("FB")` — before fix does not contain `y`, after fix visible.

**Regression Tests**: `tests/unit/test_unit_config.py::TestSectionAndDottedDirtyConsistency` (Variant A two insertion orders / Variant B flush and order independent / three-level mixed survival / isolation copy / ancestor subtree isolation)  

**Severity**: 🟡 Medium  
**Type**: Configuration System  

### [BUG-040] Command tail parameters silently lost in platform-chunked messages

**Issue**: When the platform splits a message into multiple text segments (e.g., `/kick` and parameters are interleaved with mention segments, or input method segmentation), command dispatch only takes the first text segment for matching — `/艾特 @xxx 123` is parsed as `艾特` with no parameters, commands declared with `args=` report "missing parameters", and there is no trace left.
**Root Cause**: In `command.py`, the text extraction loop takes the first `type=="text"` segment and `break`s, discarding the remaining segments (including all non-text segments).
**Affected Versions**: 2.6.0 (command dispatch introduced) - 2.10.0
**Fixed Version**: 2.10.1-dev.0
**Fix Details**: Command text is changed to collect all text segments in order and concatenate with spaces; mention/image layers no longer cause the entire command to fail parsing; also complete error-tolerant segment handling (if `message` is None/string/non-dict segment, no longer crashes the dispatcher).
**Regression Tests**: tests/unit/test_unit_command_multiseg.py

**Severity**: 🟡 Medium
**Type**: Event System

### [BUG-041] Rejected command reruns entire alt_message chain: duplicate replies and permission function side effects triggered twice

**Issue**: When the adapter's `alt_message` is inconsistent with the message segment text (e.g., alt contains @text prefix), if a command is rejected by scope/ACL/master/permission, the dispatcher reruns the entire chain using alt_message — the user receives two "permission denied" replies, and custom permission functions (often with database queries/counting side effects) are called twice.
**Root Cause**: The `return False` for rejection and "command not matched" share the same return value, leading the dispatcher to believe alt fallback is possible; the event has already been claimed before rejection, and the rerun only executes reply and permission checks again.
**Affected Versions**: 2.9.0 (governance/permission chain formed) - 2.10.0
**Fixed Version**: 2.10.1-dev.0
**Fix Details**: Text processing is changed to a three-state contract (unmatched/consumed/rejected) — after matching a registered command (regardless of rejection), alt fallback is no longer attempted; only when no command is matched is alt fallback maintained.
**Regression Tests**: tests/unit/test_unit_command_multiseg.py::test_denied_command_not_rerun_via_alt

**Severity**: 🟡 Medium
**Type**: Event System

### [BUG-042] wait_reply registered within command handler is immediately consumed by the same triggering message

**Issue**: When `wait_reply` / registering interaction wait is called within the command execution body, the wait is immediately matched by the same command message — the first interaction is skipped, and the "user reply" is actually the command text itself (wrong answer/data pollution).
**Root Cause**: `_handle_message` calls `interaction.resolve` at both the beginning and end of the method, and the second resolve at the end matches the new wait registered during execution; when cmdpass is off, the alt absence scenario is determined as empty string and directly passed, exacerbating the problem.
**Affected Versions**: 2.8.0 (interactive session system introduced) - 2.10.0
**Fixed Version**: 2.10.1-dev.0
**Fix Details**: The dispatch chain is converged to a single `interaction.resolve` (at the method beginning), and the end second call is deleted; waits are unified to be consumed by the next message.
**Regression Tests**: tests/unit/test_unit_command_multiseg.py::test_wait_reply_not_consumed_by_command_trigger

**Severity**: 🟡 Medium
**Type**: Event System

### [BUG-043] Multiple wait paths with same key in select() silently cancel earlier ones

**Issue**: When `event.select()` multiple expectations derive the same session key (same user different pattern, multiple session expectations, etc.), the later registered path cancels the earlier one with "conflict", and select directly throws `InteractionCancelled` instead of the documented timeout return `(None, None)`.
**Root Cause**: Each path independently calls `interaction.register`, and its mutual exclusion semantics send `REASON_CONFLICT` to cancel the old wait for the same key; the comment claiming "multiple paths for the same user are independent events and do not conflict" is incorrect — the副本 only changes user_id, and the keys for multiple paths for the same user are completely identical.
**Affected Versions**: 2.9.0 (select introduced) - 2.10.0
**Fixed Version**: 2.10.1-dev.0
**Fix Details**: select is changed to aggregate waits — all expectations are merged into a single entry with a custom matcher (registered by key set, sharing the same future), and any path match returns the corresponding index; multiple paths with the same key naturally coexist.
**Regression Tests**: tests/unit/test_unit_command_multiseg.py::test_select_same_user_multi_branch

**Severity**: 🟡 Medium
**Type**: Event System

### [BUG-044] BaseConverter.at() produces OB11 legacy "at" segment, full framework mention detection does not recognize

**Issue**: When the adapter uses `BaseConverter.at()` to assemble inbound events, `must_at_bot` / `has_mention()` / `on_at_message` all fail — @bot commands silently fail in groups.
**Root Cause**: `at()` produces `{"type": "at"}` (OB11 form), while the framework's mention detection and construction side (MessageBuilder/send modifiers) are all OB12's `"mention"`, with two rails and no warnings.
**Affected Versions**: Not earlier than 2.5.0 - 2.10.0
**Fixed Version**: 2.10.1-dev.0
**Fix Details**: `at()` is changed to produce `{"type": "mention", "data": {"user_id": ...}}` (method name retained as alias, new `mention` alias added).
**Regression Tests**: tests/unit/test_unit_command_multiseg.py::test_converter_at_produces_mention

**Severity**: 🟡 Medium
**Type**: Adapter

### [BUG-045] Interaction primitives permanently timeout and command penetration fail on adapters without alt_message

**Issue**: When the adapter only fills the message segment and does not fill `alt_message`, `confirm` / `choose` / `collect` wait forever for user plain text replies (e.g., "yes"); registered commands during the waiting period can never penetrate and execute; `Event.get_text()` returns an empty string causing scaffolding examples to silently fail.
**Root Cause**: All the above paths directly take the `alt_message` string, with no message segment fallback — under the framework's "alt_message is an optional field for adapters" contract, only segment filling is a legal form.
**Affected Versions**: All interaction primitive introduction versions - 2.10.0
**Fixed Version**: 2.10.1-dev.0
**Fix Details**: Unify to `alt_message` priority + text segment fallback `extract_text`口径 (five value/verification points for interaction primitives, cmdpass determination, `Event.get_text()/get_message_text()`).
**Regression Tests**: tests/unit/test_unit_command_multiseg.py

**Severity**: 🟡 Medium
**Type**: Event System

### [BUG-046] Declarative configuration template's nested subtable header drifts to top-level table

**Issue**: When declaring nested dataclass configuration (ConfigClass with nested dataclass fields), the subtable header `[Nested]` falls to the top level of the file instead of inside the component section during the first generation of configuration template — adapter reading `cfg.嵌套字段` cannot get the value; `config.full.example` also has the same misplacement.
**Root Cause**: The template generator renders relative table headers (e.g., `[Nested]`) for nested dataclass, while TOML table header semantics are absolute paths from the root; `setConfigTemplate` old implementation moves the parsed table objects into the component section, and `full.example` directly text assembles, both paths fail to anchor the relative table header to the component path.
**Affected Versions**: 2.10.0 - 2.10.1 (nested dataclass template rendering introduced with this version)
**Fixed Version**: 2.10.2
**Fix Details**: `setConfigTemplate` precisely re-anchors table headers according to the template's parsed subtable path (e.g., `[Nested]` → `[组件名.Nested]`); `config.full.example` generation side changes to pass `_prefix` to directly produce absolute table headers.
**Regression Tests**: tests/unit/test_unit_config.py::TestTomlclassEngineMigration::test_template_write_idempotent_and_nested_anchored

**Severity**: 🟡 Medium
**Type**: Configuration System / Adapter

---

### [BUG-047] Service directory full enumeration omits lazy-loaded modules

**Issue**: `sdk.module.services()` full directory skips un-instantiated (lazy-loaded) modules — even if the module declares `meta.services`, it does not appear in the directory; single-module precise query `services("Name")` and topology `get_topology()` are unaffected.
**Root Cause**: In the `ModuleManager.services()` full enumeration branch, for modules without a contract cache (not loaded), it unconditionally `continue` after parsing the contract on the spot — the intention was to skip modules that do not declare services, but it actually skips all un-loaded modules; loaded modules are unaffected because they write the contract cache at load time.
**Affected Versions**: 2.9.0 - 2.10.1 (module RPC and service directory introduced with 2.9.0)
**Fixed Version**: 2.10.2
**Fix Details**: Delete the unconditional skip, unify to "skip only if the parse result is empty"; un-loaded modules parse `get_meta().services` on the spot (same口径 as `module.call()` whitelist), and modules that declare services are included in the directory as usual.
**Regression Tests**: tests/unit/test_unit_module_rpc.py::TestServicesDirectory::test_lazy_declared_module_in_full_directory

**Severity**: 🟡 Medium
**Type**: Loading System

### [BUG-048] Session inbox query API loses message attribution (sender and event metadata)

**Issue**: All inbox query interfaces (`get()` / `get_by_trace()` / `event.history()`) return records with only `role/text/ts/event_id` — the `sender` column stored in the storage layer is discarded by the query layer, making different members' messages in group chat indistinguishable in the API layer (AI mistakenly identifies member B as the previous dialogue partner A); inbound records also do not archive event metadata at the moment of the event, so the nickname at the time of the event is not retrieved during post-event investigation.
**Root Cause**: When `sender` column was added in 2.8.0, the comment clearly stated it is used "to restore message source during replay," but the Select and return construction did not carry it (implementation oversight); metadata archiving was never designed — `append()` has no meta channel, and the table structure has no corresponding column.
**Affected Versions**: 2.8.0 - 2.11.0 (sender column introduced with 2.8.0)
**Fixed Version**: 2.11.1-dev.0
**Fix Details**: Added `meta` column (whitelist contract: inbound nickname/self_id/sub_type/message_id, outbound send context and module; old table automatically migrates, silently reverts to `{}` if backend does not support ALTER); `append()` adds `meta` parameter throughout memory buffer and batch write to disk; `get` / `recent` / `get_by_trace` / `event.history` uniformly return `sender` + `meta` (JSON damage reverts to `{}`).
**关联**: #467 (same batch #468 / #469 / #470)
**Regression Tests**: tests/unit/test_unit_transcript_attribution.py::TestSenderMetaReadback / TestMetaMigration

**Severity**: 🟡 Medium
**Type**: Session Inbox / Storage System

### [BUG-049] Inbound bot self-message echo recorded as user, polluting inbox attribution

**Issue**: Platforms/protocol ends that enable message echo (OneBot v11 `report-self-message`, Telegram outgoing, etc.) report bot self-messages as message events, and the inbox always records `role="user"` — bot self-messages and real user inputs are indistinguishable, and downstream modules treat bot self-messages as user inputs (AI responds to what the "user" said), and role statistics are distorted.
**Root Cause**: The inbound automatic record point (`Core/adapter.py`) unconditionally records `role="user"` for all `event_type == "message"`, without consuming the `self` field to determine bot echo — while the subsequent bot self-detection logic is already consuming the same field (available at the time of recording, but the recording logic missed using it).
**Affected Versions**: 2.8.0 - 2.11.0 (inbox automatic record introduced with 2.8.0)
**Fixed Version**: 2.11.1-dev.0
**Fix Details**: Before recording, identify echo by `self.user_id == user_id`, and handle according to the new configuration `ErisPulse.transcript.self_echo` in three modes: `"bot"` (default) records `role="bot"` + `sender=self_id` + `meta.self_echo=true`; `"skip"` does not record; `"user"` maintains the old behavior. For non-echo platforms (self missing or not equal), each field reverts to unchanged.
**关联**: #470 (depends on #467's meta column to carry the self_echo marker)
**Regression Tests**: tests/unit/test_unit_transcript_attribution.py::TestSelfEcho

**Severity**: 🟡 Medium
**Type**: Adapter / Session Inbox

### [BUG-050] Container execution of `epsdk restart` directly exits container

**Issue**: When the framework runs as the main container process (PID 1) (official image `CMD ["epsdk", "run"]` or direct startup script), after installing a component with `ep i <package>` and executing `epsdk restart` as prompted, the container exits directly and does not restart — the newly installed component is not activated, and the service is interrupted.
**Root Cause**: The implementation of `epsdk restart` is "terminate running instance + relaunch with original parameters" — the relaunch is managed by the epsdk CLI process. In container scenarios, the target instance is PID 1 (main container process), and SIGINT/SIGTERM causes its exit, destroying the entire PID namespace, killing both the CLI itself and the sub-process to be relaunched, making relaunch impossible.
**Affected Versions**: 2.11.0 - 2.11.2 (runtime.json instance control introduced with 2.11.0; earlier versions have no restart command)
**Fixed Version**: 2.12.0-dev.0
**Fix Details**: When `epsdk restart` detects the status file `pid == 1` (characteristic of container main process), it no longer terminates and relaunches, but instead sends `SIGUSR1` to the framework process, and the framework completes the component-level soft restart (module and adapter hot reload pipeline, new installed adapter entry-point immediately takes effect) within the process; `sdk.run()` registers the `SIGUSR1` handler to carry this channel. The whole process restart scenario is handed over to container restart (`docker restart` / restart policy).
**Regression Tests**: tests/unit/test_unit_cli_runtime.py::TestRestartContainerHot

**Severity**: 🔴 Severe (container deployment restart causes service interruption)
**Type**: CLI / Deployment