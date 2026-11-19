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

## Statistics Overview

| Severity | Count |
|----------|-------|
| 🔴 Critical | 17 |
| 🟡 Medium | 28 |
| 🟢 Minor | 4 |
| **Total** | **49** |

| Type | Count |
|------|-------|
| Event System | 13 |
| Configuration System | 14 |
| Adapter | 6 |
| CLI | 4 |
| Storage | 4 |
| Loader System | 4 |
| Routing | 2 |
| Client | 1 |
| Runtime | 1 |

> Note: A single bug may belong to multiple types; the table above is counted by primary type.
> Note: The IDs BUG-028 / BUG-031 are vacant (discarded during registration; existing numbering is kept stable and not recycled or reordered).

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

### [BUG-034] Scope persist=False runtime bindings silently wiped out by any subsequent configuration write

**Issue**: Runtime writes such as `scope.set_module(..., persist=False)` only modify the in-memory `self._data`; however, scope subscribes to the `config.set` / `config.updated` events, so any code writing configuration (e.g., a module writing its own default configuration at load time) triggers scope to rebuild the entire configuration tree from the configuration file, silently losing all previously established runtime bindings (evaluation falls back to the default allow), with no log hint whatsoever. Scenarios that depend on runtime bindings (Dashboard "runtime-only" toggles, dynamic runtime disabling of modules) regress in behavior after an unrelated module writes configuration.

**Root Cause**: Root cause chain: `scope.set/delete(persist=False)` only writes to memory (`Core/scope.py`) → any `setConfig` triggers the `config.set` event → `_on_config_updated` unconditionally calls `_load_config()` → `_apply_tree()` wholesale-replaces with `self._data = {...}` → runtime bindings not present in the configuration file are discarded.

**Affected Versions**: 2.8.0-dev.1 - 2.8.0-dev.2
**Fixed Version**: 2.8.0-dev.2
**Fix**: Introduced a runtime override layer `_runtime_overrides` (including deletion sentinels): `persist=False` writes/deletes are recorded into the override layer, and `_apply_tree()` replays them in write order after rebuilding the persistence layer, so runtime rules remain valid after any configuration write; `persist=True` writes/deletes clear the corresponding override records (user persistence semantics take priority); `config.set` is filtered precisely by event key, and `config.updated` compares the old and new scope sections, rebuilding only when scope actually changed (incidentally avoiding unrelated writes flushing the evaluation LRU cache); added `unregister_by_owner()` for fallback cleanup alongside callers when modules unload. The persist=False runtime overrides of `Core.Event.overrides` had the same issue and were fixed synchronously with the override layer architecture.
**Fix Date**: 2026/09/09

**Reproduction Steps**: ① `scope.set_module("testplat", blocked=["TestB"], persist=False)` → evaluation returns False; ② any module executes `config.setConfig("HelpModule", {...})` → triggers a scope rebuild; ③ `scope.is_allowed("testplat", None, "TestB")` returns True (expected to still be False).
**Related**: Issue #432
**Regression Tests**: `tests/unit/test_unit_scope.py::TestRuntimeOverrideSurvival` (survival across unrelated writes / tree rebuild replay / deletion sentinel / persistence clearing / precise invalidation / owner cleanup)

**Severity**: 🟡 Medium
**Type**: Configuration System / Runtime

---

### [BUG-035] Configuration panel select options and dict fields rendered as [object Object]

**Issue**: In the WebUI configuration panel, the option dropdown of select fields displays `[object Object]` (e.g., dynamically generated color scheme style options); dict fields without a declared control type (e.g., `stalker_mode`, `knowledge_base` and other nested configuration sections) display `[object Object]` in the text box and cannot be viewed or edited properly.

**Root Cause**: Two independent defects: ① the framework i18n parser `_resolve_i18n_text` only restores dictionaries carrying an `i18n` key; when option labels are dictionaries containing only `default` (dynamic text without an i18n key), they are passed through as-is, and the frontend's `esc(label)` string coercion yields `[object Object]`; ② the Dashboard rendering branch only uses a JSON textarea for array types, while dict values fall into the plain text input branch and get coerced via `String()`. Additionally, if a module mistakenly declares `_schema_meta` as a regular dataclass field (missing the `ClassVar` annotation), it enters the schema as a configuration field, aggravating the confusion.

**Affected Versions**: 2.7.0 - 2.8.0-dev.2
**Fixed Version**: 2.8.0-dev.2
**Fix**: ① `_resolve_i18n_text` now supports restoring dictionaries containing only `default` to text; ② the framework excludes underscore-prefixed fields in all five places—schema/template/defaults/filling/validation (making accidental declarations harmless); ③ Dashboard select option label objects get fallback parsing (`default` first), and dict/table fields render as a JSON textarea (the save path writes back with `tp=object` JSON.parse, full round-trip).
**Fix Date**: 2026/09/09

**Regression Tests**: `tests/unit/test_unit_config.py::TestResolveI18nDefaultOnlyDict`, `TestSchemaUnderscoreFieldExclusion`

**Severity**: 🟡 Medium
**Type**: Configuration System

---

### [BUG-036] Occasional configuration write failures (ENOENT) when multiple instances share a configuration directory

**Issue**: In Docker deployment scenarios (multiple containers mounting the same host configuration directory), logs occasionally show two consecutive `Failed to write configuration file ... [Errno 2] No such file or directory: '...config.toml.tmp' -> '...config.toml'` entries. The configuration write in question is discarded (the old configuration is fully preserved; no configuration loss was observed) and functionality is unaffected, but the recurring warnings interfere with troubleshooting, and the pending configuration items must wait for the next write to reach disk.

**Root Cause**: Root cause chain: `_flush_config` / `setConfigTemplate` use a **fixed-name** temporary file `config.toml.tmp` to carry the new content and call `rename()` directly after `write()` without `fsync`. When two ErisPulse instances share the same configuration directory, instance B's `open("w")` may **truncate** the temporary file instance A is writing → when A renames, the target has already been taken away by B or its content truncated, reporting ENOENT (i.e., the two consecutive errors in user logs). In reported cases this only manifested as write-failure warnings (old configuration preserved); with a more extreme interleaving, rename could output an empty/half-written `config.toml` (a potential risk that has not yet erupted in real environments). In single-instance scenarios, ext4 delayed allocation likewise has the crash window of "rename metadata hitting disk before data blocks" (SIGKILL / power loss). `_file_lock` is an in-process `threading.RLock` with no constraint over cross-process/cross-container writes.

**Affected Versions**: 2.2.0-dev.0 - 2.8.0

**Fixed Version**: 2.8.1

**Fix**: Configuration writes are unified into `_atomic_write_text()`: `mkstemp` in the same directory generates a process-unique temporary file (eliminating fixed-name contention; under multiple instances it degrades to last-writer-wins, no more ENOENT) → after writing, `flush + fsync` forces the data to disk (eliminating the "rename already took effect, data not yet on disk" window) → `os.replace` atomically replaces the target (atomic on both POSIX/Windows; at any moment the disk holds either the complete old content or the complete new content); under POSIX, the configuration directory is additionally fsynced. All three write points—`_flush_config`, `setConfigTemplate`, and root directory configuration migration—are switched over; the exception-path cleanup logic is restructured along with the unique temporary file name. Added **multi-instance detection**: at startup, an advisory lock (POSIX `flock` / Windows `msvcrt.locking`) exclusively holds the configuration directory lock file `.erispulse_config.lock`; if occupied, an i18n warning is emitted (without blocking startup); the lock is automatically released by the OS at process exit, with no ghost locks.

**Fix Date**: 2026/09/13

**Reproduction Steps**: ① Two containers mount the same host `config/` directory and run ErisPulse simultaneously; ② any instance triggers a configuration write (e.g., a module registering default configuration); ③ observe ENOENT write-failure warnings in the logs, with the write discarded (old configuration preserved).

**Related**: User report (1Panel containers ×2)

**Regression Tests**: `tests/unit/test_unit_config_atomic_write.py` (complete content write / no temporary file residue / original file preserved on write failure / file always valid under dual-instance concurrent writes / lock file creation / multi-instance warning / migration atomic write)

**Severity**: 🟢 Minor

**Type**: Configuration System

---

### [BUG-037] Space-separated subcommand names can never be triggered after registration

**Issue**: After registering subcommands with space-separated multi-token command names (e.g., `@command("admin add")`), the command registers normally and appears in the help list, but when a user sends `/admin add` the bot never responds—the input is matched by the parent token command as `admin` + arguments `["add"]`; if the parent token is also unregistered, there is no response at all. It can only be avoided by using dot-separated naming (`admin.reload`, a single token as a whole).

**Root Cause**: Root cause chain: `CommandHandler.__call__` stores any command name (including space forms) as-is into the flat `self.commands` dictionary → during dispatch, `_try_execute_command` only matches the first token of the message (`cmd_name = parts[0]`) → multi-token command names as dictionary keys can never be found. The registration and matching stages make inconsistent assumptions about command name spacing, and there is no registration-time warning (silent failure).

**Affected Versions**: Since the command system's introduction - 2.8.0

**Fixed Version**: 2.8.1

**Fix**: The matching layer is changed to **longest prefix matching**: attempts degrade step by step starting from the longest candidate (`" ".join(parts[:n])`, with n capped by the cached `_max_name_tokens`, the maximum token count among registered command names/aliases); upon a hit, it executes with the remaining tokens as arguments, and downstream scope/ACL/override/master/permission chains naturally apply to the full command name. Accompanying semantics: when parent and child coexist, input for unregistered subcommands falls back to the parent command (historical behavior unchanged); when a subcommand does not declare `permission`, it inherits along the parent chain from the nearest ancestor command that declares a permission (protecting the parent command protects all of its subcommands); when only single-token commands are registered, the first round hits immediately and dispatch overhead is identical to before. `unregister` / `unregister_by_owner` / full cleanup maintain the token count cache in sync.

**Fix Date**: 2026/09/13

**Reproduction Steps**: ① Register `@command("admin add")` in a module; ② send `/admin add x`; ③ before the fix, no response (or it is caught as arguments by a simultaneously registered `/admin`); after the fix, `admin add` triggers and `get_command_args()` returns `["x"]`.

**Regression Tests**: `tests/unit/test_unit_command_subcommand.py` (longest prefix matching / subcommand-only trigger / three-level nesting / both case-sensitivity modes / single and multi-token aliases / full name in event payload / full name in lifecycle hooks / six permission inheritance cases / ACL glob full name / master / unregistration fallback and cache recomputation)

**Severity**: 🟡 Medium

**Type**: Event System

---

### [BUG-038] persist=False runtime bindings get incidentally persisted by persistence writes and "resurrect" from disk after module unloading

**Issue**: Runtime bindings written with `scope.set(path, value, persist=False)` (documented as never persisted, invalidated upon process restart, cleaned up on module unload) get written into the user's `config.toml` as a diff alongside any unrelated `persist=True` write (the default, e.g., module `set_module` / WebUI saving configuration); thereafter, even after the module unloads and unregisters the runtime binding, the binding still "resurrects" from disk on the next configuration reload and remains in effect, and it survives process restarts—contrary to the semantic contract that "runtime bindings are never persisted", and extremely hard to troubleshoot.

**Root Cause**: Root cause chain: `ScopeManager.set()` first writes the value into the in-memory configuration tree `_data` (runtime bindings likewise write directly into `_data`) → the persistence branch takes a deep-copy snapshot of **the entire `_data`** and commits it to `update_erispulse_config` for diff-based persistence → the values of `persist=False` bindings get mixed into the snapshot. `delete(persist=True)` shares the same origin: it hands a live reference into `_data` (the `parent` node) to the deferred dirty-write queue, so runtime modifications to sibling keys under that node during the deferred flush window get persisted as well, and the live reference lingering in the dirty queue creates a cross-write pollution window.

**Affected Versions**: 2.8.0-dev.2 - 2.9.0-dev.0

**Fixed Version**: 2.9.0-dev.2

**Fix**: Introduced a persistence baseline `_persisted_tree` (refreshed with the disk-loaded, validated tree whenever the configuration tree is rebuilt) as the mirror of disk truth: `set(persist=True)` applies only the current change onto the baseline and then commits the diff; runtime bindings never enter persisted content; "read-immediately-after-write" now restores directly from the in-memory final-state snapshot instead of rebuilding via `_apply_tree`, to avoid polluting the baseline. `delete(persist=True)` follows the same approach: it applies the deletion onto the baseline and hands the deep copy of the baseline subtree to the persistence layer; `set_action`'s wholesale-replacement semantics deletes by the same approach first and then writes, so old rule keys do not linger in persisted content.

**Fix Date**: 2026/09/27

**Reproduction Steps**: ① Execute `scope.set("bots.p.debug_mode", {"blocked": ["X"]}, persist=False)` in a module; ② trigger any persistence write (e.g., another module calls `set_module`); ③ open `config/config.toml` and observe that `debug_mode` has been written (before the fix); ④ after unloading the module (runtime binding unregistered), trigger a configuration reload—`scope.get("bots.p.debug_mode")` still returns the binding value.

**Regression Tests**: `tests/unit/test_unit_scope.py::TestPersistBaseline` (runtime bindings not persisted alongside unrelated persistence writes / no resurrection on configuration reload after unload-unregister / delete commits the baseline subtree without runtime sibling keys / set_action replacement leaves no residual keys / cache_size configuration takes effect)

**Severity**: 🔴 Critical

**Type**: Configuration System

---

### [BUG-039] Read/write inconsistency when whole-section writes and dotted writes coexist (dotted overrides lost)

**Issue**: Within the deferred flush window, when a whole-section write (`setConfig("Mod", {...})`, e.g., a `BaseModule.cfg` write-back) and a dotted write (`setConfig("Mod.key", v)`, e.g., configuration hot update / test tool override) coexist for the same section, there are two variants: Variant A (read path)—`getConfig("Mod")` whole-section read returns the stale whole-section pending-write snapshot and cannot see the later dotted override (the dotted read path is normal); Variant B (write path, more severe)—when the dotted write comes first and the whole-section write later (the common sequence of test tool injecting an override → module `self.cfg = ...` write-back), flush applies dirty keys in insertion order, and the whole-section write wholesale-replaces the section, so **the dotted override is permanently lost on disk**. The production combination of "configuration hot update + module runtime write-back" can trigger it, and it is unrelated to test environments (exposed by ErisPulse-DailyCard test feedback).

**Root Cause**: Stage ① of `getConfig` (exact hit on `_dirty_keys`) does an early `return self._dirty_keys[key]`, completely bypassing Stage ④'s `_dirty_overlay` descendant overlaying; `_flush_config` applies dirty keys in `_dirty_keys` insertion order, so when the whole-section write happens to be ordered after the dotted write, the dotted value is wholesale-replaced. Also: Stage ① returns the dirty queue's **live object reference**, so a caller modifying the returned dict in place directly alters the pending-to-disk state.

**Affected Versions**: 2.6.0 - 2.9.0-dev.2

**Fixed Version**: 2.9.0-dev.2

**Fix**: Within the dirty window, semantics are unified to **specificity first**—dotted (more specific) pending-write values take priority over whole-section (broader) pending-write values, with the read path and the disk persistence path sharing the same approach: ① `getConfig`, after an exact hit on a pending key, still overlays `_dirty_overlay` descendant pending values (non-dict values return the overlaid subtree, consistent with the ③+④ scalar corner cases); ② `_flush_config` applies dirty keys sorted by path depth (whole-sections/ancestors first, dotted/descendants after, with a stable sort preserving write order within the same depth). Trade-off: within the same dirty window (about 5 seconds), a whole-section write-back cannot cover a still-pending dotted write—after the read-path fix, read-modify-write naturally carries the dotted values, so the actual impact is minimal. ③ `getConfig` returns involving pending values (exact hit / ancestor subtree / overlaid merge) are changed to `copy.deepcopy` isolated copies, no longer leaking internal dirty queue references; the no-dirty-key fast path and pure cache reads behave unchanged.

**Fix Date**: 2026/09/28

**Reproduction Steps**: ① `setConfig("FB.y", 1)`; ② `setConfig("FB", {"z": 2})`; ③ `force_save()`—before the fix, the disk only has `[FB] z = 2` left (y lost); after the fix, `{"y": 1, "z": 2}`. Variant A: after steps ①②, without flushing, directly call `getConfig("FB")`—before the fix it does not contain `y`; after the fix it is visible.

**Regression Tests**: `tests/unit/test_unit_config.py::TestSectionAndDottedDirtyConsistency` (Variant A in both insertion orders / Variant B persistence independent of order / three-level mixed survival / isolated copies / ancestor subtree isolation)

**Severity**: 🟡 Medium

**Type**: Configuration System

### [BUG-040] Trailing command arguments silently lost for platform-segmented messages

**Issue**: When a platform splits one message into multiple text segments (e.g., a mention segment wedged between `/kick` and its arguments, or IME segmentation), command dispatch only takes the first text segment for matching—`/at @xxx 123` parses as `at` with no arguments; commands declaring `args=` directly report "missing arguments", with no trace left.
**Root Cause**: The text extraction loop in `command.py` breaks after taking the first `type=="text"` segment; the remaining segments (including all non-text segments) are discarded.
**Affected Versions**: 2.6.0 (command dispatch introduced) - 2.10.0
**Fixed Version**: 2.10.1-dev.0
**Fix**: Command text now collects all text segments in segment order joined by spaces; mention/image interlayers no longer render the command entirely unparseable; malformed segment tolerance added in sync (`message` being None/string/non-dict segments no longer break through the dispatcher).
**Regression Tests**: tests/unit/test_unit_command_multiseg.py

**Severity**: 🟡 Medium
**Type**: Event System

### [BUG-041] Denied commands re-run the entire chain via alt_message: duplicate replies and double-triggered permission function side effects

**Issue**: When the adapter's `alt_message` differs from the message segment text (e.g., the alt contains an @-text prefix), after a matched command is denied by scope/ACL/master/permission, the dispatcher re-runs the entire chain with alt_message—the user receives two "insufficient permission" replies, and custom permission functions (which often carry DB query/counting side effects) are called twice.
**Root Cause**: The denial path's `return False` shares the same return value with "no command matched", so the dispatcher concludes it may attempt the alt fallback; but the event had already been claimed before denial, so the re-run merely redundantly executed the reply and permission evaluation.
**Affected Versions**: 2.9.0 (governance/permission chain took shape) - 2.10.0
**Fixed Version**: 2.10.1-dev.0
**Fix**: Text handling changed to a three-state contract (unmatched/consumed/rejected)—after matching a registered command (whether denied or not), alt fallback no longer occurs; alt fallback is kept only when no command is matched.
**Regression Tests**: tests/unit/test_unit_command_multiseg.py::test_denied_command_not_rerun_via_alt

**Severity**: 🟡 Medium
**Type**: Event System

### [BUG-042] wait_reply registered inside a command handler is immediately consumed by the same triggering message

**Issue**: When `wait_reply` is called / an interaction wait is registered within a command execution body, the wait is immediately hit by the same command message—the interaction flow's first question is skipped, and the "user reply" is actually the command text itself (irrelevant answers/data pollution).
**Root Cause**: `_handle_message` calls `interaction.resolve` once at the beginning and once at the end of the method; the second resolve at the end, after command execution, hits waits newly registered during execution; when cmdpass is off, the alt-missing scenario evaluates as an empty string and passes through directly, aggravating the problem.
**Affected Versions**: 2.8.0 (interaction session system introduced) - 2.10.0
**Fixed Version**: 2.10.1-dev.0
**Fix**: The dispatch chain converged to a single `interaction.resolve` (at the beginning of the method), removing the second call at the end; waits are now uniformly consumed by the next message.
**Regression Tests**: tests/unit/test_unit_command_multiseg.py::test_wait_reply_not_consumed_by_command_trigger

**Severity**: 🟡 Medium
**Type**: Event System

### [BUG-043] select(): multi-branch waits on the same key where later ones silently cancel earlier ones

**Issue**: When multiple expectations of `event.select()` derive the same session key (same user with different patterns, multiple session expectations, etc.), the later-registered branch cancels the earlier-registered one as a "conflict", and select throws `InteractionCancelled` directly instead of the documented timeout return of `(None, None)`.
**Root Cause**: Each branch independently calls `interaction.register`, whose mutual-exclusion semantics cancel old waits on the same key with `REASON_CONFLICT`; the comment's claim that "multiple branches for the same user, thanks to event copies, are independent and do not conflict with each other" does not hold—copies only change user_id, and multiple branches for the same user have completely identical keys.
**Affected Versions**: 2.9.0 (select introduced) - 2.10.0
**Fixed Version**: 2.10.1-dev.0
**Fix**: select changed to aggregated waiting—all expectations are merged into a single entry with a custom matcher (registered by key set, sharing the same future); any branch hit returns the corresponding index; multiple branches on the same key naturally coexist.
**Regression Tests**: tests/unit/test_unit_command_multiseg.py::test_select_same_user_multi_branch

**Severity**: 🟡 Medium
**Type**: Event System

### [BUG-044] BaseConverter.at() produces the OB11 legacy "at" segment, unrecognized by framework-wide mention detection

**Issue**: When adapters use `BaseConverter.at()` to assemble inbound events, `must_at_bot` / `has_mention()` / `on_at_message` are all blind—@bot commands silently fail in groups.
**Root Cause**: `at()` produces `{"type": "at"}` (the OB11 form), while all framework mention detection and the construction side (MessageBuilder/send decorators) use OB12's `"mention"`; the two tracks coexist with no warning of any kind.
**Affected Versions**: Introduced no earlier than 2.5.0 - 2.10.0
**Fixed Version**: 2.10.1-dev.0
**Fix**: `at()` now produces `{"type": "mention", "data": {"user_id": ...}}` (the method name kept as an alias, with a new `mention` alias added).
**Regression Tests**: tests/unit/test_unit_command_multiseg.py::test_converter_at_produces_mention

**Severity**: 🟡 Medium
**Type**: Adapter

### [BUG-045] On adapters without alt_message, interaction primitives time out forever and command pass-through fails

**Issue**: When adapters only fill the message segment without `alt_message`: `confirm` / `choose` / `collect` wait forever on the user's plain-text reply (e.g., "yes"); registered commands during the wait can never pass through for execution; `Event.get_text()` returns an empty string, causing scaffold examples to silently fail.
**Root Cause**: All of the above paths take the `alt_message` string directly with no message-segment fallback—under the framework's contract that "alt_message is an optional adapter field", segment-only filling is a legitimate form.
**Affected Versions**: Each interaction primitive's introduction version - 2.10.0
**Fixed Version**: 2.10.1-dev.0
**Fix**: Unified to the `extract_text` approach of `alt_message` first + text segment fallback (the five value-taking/validation points of interaction primitives, cmdpass evaluation, `Event.get_text()/get_message_text()`).
**Regression Tests**: tests/unit/test_unit_command_multiseg.py

**Severity**: 🟡 Medium
**Type**: Event System

### [BUG-046] Nested sub-table headers in declarative configuration templates drift into top-level tables

**Issue**: When a configuration declared with nested dataclasses (ConfigClass containing nested dataclass fields) first generates a configuration template, the sub-table header `[Nested]` lands at the file's top level instead of inside the component section—the adapter reads `cfg.nested_field` and gets no value; `config.full.example` is similarly misplaced.
**Root Cause**: The template generator renders relative table headers for nested dataclasses (`[Nested]`), whereas TOML table header semantics are absolute paths computed from the root; the old `setConfigTemplate` implementation moves parsed table objects into the component section, and `full.example` is assembled directly from text—neither path re-anchors the relative table header under the component path.
**Affected Versions**: 2.10.0 - 2.10.1 (nested dataclass template rendering introduced with these versions)
**Fixed Version**: 2.10.2
**Fix**: `setConfigTemplate` precisely re-anchors table headers according to the set of sub-table paths parsed from the template (`[Nested]` → `[ComponentName.Nested]`); the `config.full.example` generation side now passes `_prefix` to directly produce absolute table headers.
**Regression Tests**: tests/unit/test_unit_config.py::TestTomlclassEngineMigration::test_template_write_idempotent_and_nested_anchored

**Severity**: 🟡 Medium
**Type**: Configuration System / Adapter

---

### [BUG-047] Service directory full enumeration misses lazy-loaded modules

**Issue**: The `sdk.module.services()` full directory always skips uninstantiated (lazy-loaded) modules—even if a module declares `meta.services`, it does not appear in the directory, so consumers that rely on the directory as their discovery entry point (AI agents, help modules, etc.) cannot discover its services; the single-module exact query `services("Name")` and topology `get_topology()` are unaffected.
**Root Cause**: The `ModuleManager.services()` full enumeration branch unconditionally `continue`s on modules without a contract cache (not loaded) **even after resolving the contract on the spot**—the intent was to skip "modules that do not declare services", but in practice it skipped unloaded modules entirely; loaded modules are unaffected because the contract cache is written at load time.
**Affected Versions**: 2.9.0 - 2.10.1 (module RPC and service directory introduced with 2.9.0)
**Fixed Version**: 2.10.2
**Fix**: Removed the unconditional skip; the decision is uniformly made by "skip only when the resolution result is empty"; unloaded modules resolve `get_meta().services` on the spot (consistent with the `module.call()` whitelist), and modules declaring services enter the directory as usual.
**Regression Tests**: tests/unit/test_unit_module_rpc.py::TestServicesDirectory::test_lazy_declared_module_in_full_directory

**Severity**: 🟡 Medium
**Type**: Loading System

### [BUG-048] Conversation inbox query APIs lose message attribution (sender and event metadata)

**Issue**: Records returned by all inbox query interfaces (`get()` / `get_by_trace()` / `event.history()`) contain only `role/text/ts/event_id`—the `sender` column already present in the storage layer is dropped by the query layer, so in group chat replay, messages from different members are indistinguishable at the API layer (the AI mistakes member B for the previous conversation partner A); inbound records also do not archive metadata such as the nickname at event time, so later retroactive lookups get "the current nickname" rather than "the nickname at the time".
**Root Cause**: The comment when the `sender` column was added in 2.8.0 already stated it was for "restoring message sources during replay", but neither the SELECT nor the return construction carried it (an implementation oversight); metadata archiving was never designed—`append()` has no meta channel, and the table schema has no corresponding column.
**Affected Versions**: 2.8.0 - 2.11.0 (sender column introduced with 2.8.0)
**Fixed Version**: 2.11.1-dev.0
**Fix**: Added a `meta` column (whitelist contract: inbound nickname/self_id/sub_type/message_id, outbound send context and module; old tables migrate automatically, silently falling back to `{}` when the backend does not support ALTER); `append()` gained a `meta` parameter threaded through the in-memory buffer and batch flushing; `get` / `recent` / `get_by_trace` / `event.history` uniformly return `sender` + `meta` (falling back to `{}` on corrupted JSON).
**Related**: #467 (same batch as #468 / #469 / #470)
**Regression Tests**: tests/unit/test_unit_transcript_attribution.py::TestSenderMetaReadback / TestMetaMigration

**Severity**: 🟡 Medium
**Type**: Conversation Inbox / Storage System

### [BUG-049] Inbound bot self-message echoes recorded as user, polluting inbox attribution

**Issue**: On platforms/protocol ends with message echo enabled (OneBot v11 `report-self-message`, Telegram outgoing, etc.), when messages the bot itself sent are reported as message events, the inbox always records `role="user"`—bot self-messages are indistinguishable from real user input, downstream modules process bot self-messages as user input (the AI responds to what the "user" supposedly said), and role statistics become distorted.
**Root Cause**: The inbound auto-recording point (`Core/adapter.py`) unconditionally records `role="user"` for all `event_type == "message"`, without consuming the `self` field for bot echo detection—yet the bot auto-discovery logic immediately after already consumes the same field (available at recording time; the recording logic simply missed it).
**Affected Versions**: 2.8.0 - 2.11.0 (inbox auto-recording introduced with 2.8.0)
**Fixed Version**: 2.11.1-dev.0
**Fix**: Echoes are identified by `self.user_id == user_id` before recording, and handled per the new configuration `ErisPulse.transcript.self_echo` in three modes: `"bot"` (default) records `role="bot"` + `sender=self_id` + `meta.self_echo=true`; `"skip"` does not record; `"user"` keeps the old behavior. For non-echo platforms (self missing or unequal), behavior remains unchanged field by field.
**Related**: #470 (relies on #467's meta column to carry the self_echo marker)
**Regression Tests**: tests/unit/test_unit_transcript_attribution.py::TestSelfEcho

**Severity**: 🟡 Medium
**Type**: Adapter / Conversation Inbox

### [BUG-050] Running epsdk restart inside a container exits the container outright

**Issue**: When the framework runs as the container main process (PID 1) (official image `CMD ["epsdk", "run"]` or direct-start scripts), after installing a component with `ep i <package>`, executing `epsdk restart` as prompted makes the container exit outright and never come back up—the newly installed component does not take effect, and service is interrupted.
**Root Cause**: `epsdk restart` is implemented as "terminate the running instance + re-launch with the original arguments"—the re-launch is hosted by the epsdk CLI process. In container scenarios the target instance is PID 1 (the container main process); SIGINT/SIGTERM causing it to exit destroys the entire PID namespace, and the CLI itself along with the child process awaiting re-launch are killed together, so the re-launch can never happen.
**Affected Versions**: 2.11.0 - 2.11.2 (runtime.json instance control introduced with 2.11.0; earlier versions have no restart command)
**Fixed Version**: 2.12.0-dev.0
**Fix**: When `epsdk restart` detects `pid == 1` in the state file (the container main process signature), it no longer terminates and re-launches; instead it sends `SIGUSR1` to the framework process, and the framework completes a component-level soft restart in-process (`sdk.restart()`: the module and adapter hot-reload pipeline; adapter entry-points newly installed at runtime take effect immediately); `sdk.run()` registers a `SIGUSR1` handler to carry this channel. Full-process restart scenarios are delegated to container restarts (`docker restart` / restart policies).
**Regression Tests**: tests/unit/test_unit_cli_runtime.py::TestRestartContainerHot

**Severity**: 🔴 Critical (restart under container deployment means service interruption)
**Type**: CLI / Deployment

### [BUG-051] Cross-account duplicate receipt (drop) collateral damage to at-mention messages, random message loss in multi-account deployments

**Issue**: After enabling `ErisPulse.framework.cross_account_policy = "drop"` in multi-account deployments, when a user @-mentions a certain account in a group, that account often fails to receive the event (the account does not even appear in the framework event stream), intermittently. In real testing, of 22 messages in the same group only 3 reached the mentioned account; @-driven multi-account modules randomly go deaf, with no errors from downstream modules.
**Root Cause**: `_cross_receipt_check`'s content-level deduplication key is a 4-tuple (same platform + same conversation + same sender + same `alt_message` digest), without account or mention dimensions. When the same group message is emitted via multiple account connections, the first arrival takes the slot and later arrivals are dropped directly at the dispatch entry per drop—the @-mentioned target account is often a "later arrival", so the event is swallowed with downstream modules unaware.
**Affected Versions**: 2.12.0 (cross_account_policy introduced with 2.12.0)
**Fixed Version**: 2.12.1-dev.0
**Fix**: Copies whose mention target hits the receiving account's own identity (dual check on `self.user_id` / `self.account_id`) do not participate in cross-account correlation (exempt from both mark / drop)—the mentioned account always receives its own event, while other account copies are deduplicated as usual (@-driven modules filter with the `on_at_message` condition, naturally single-response). Also fixed along the way: `cross_account_policy` configuration changes not taking effect hot (lazy cache invalidated on config.set / config.updated); the missing translation key for `core.adapter.event_duplicated` (trace outputs the key name as-is).
**Regression Tests**: tests/unit/test_unit_adapter.py::TestCrossAccountReceipt (test_drop_preserves_mentioned_account_copy and 6 new cases in total)

**Severity**: 🟢 Minor (drop is a non-default path enabled by explicit configuration, affecting only the dispatch of @-mention messages)
**Type**: Adapter