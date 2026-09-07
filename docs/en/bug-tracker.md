# Bug Tracker

This document records known bugs in the ErisPulse SDK and their fixes, arranged in chronological order by the version in which they were fixed.

> **For Readers**
> No software is born perfect, and even the most careful developers may leave behind minor errors. The bugs listed here are all those that have a tangible impact on operation—those that are too subtle to even qualify as "minor" will not appear here. Although the list contains a significant number of "critical" items, the original purpose of publicly documenting these bugs is to facilitate troubleshooting and tracing, not to create anxiety: bugs that are visible, recorded, and fixed are themselves proof that the project is continuously improving. Seeing this list should not cause concern; it is a troubleshooting tool, not a source of fear.

> **How to Read & Maintenance Guidelines**
> - Each bug entry contains structured fields such as problem description, root cause analysis, affected version range, and fix solution. It is recommended to check if the "affected version" covers the version you are currently using before upgrading.
> - If you need to add a new bug entry, please add content at the corresponding location, following the field specifications and severity/type classifications described below.

---

## Field Descriptions

### Required Fields

| Field | Description |
|-------|-------------|
| **Problem** | The external manifestation of the bug, i.e., observable abnormal phenomena to users. Provide error messages or typical scenarios whenever possible. |
| **Root Cause** | Root cause analysis, pointing to specific code defects (including a "Root Cause Chain" diagram for complex scenarios) |
| **Affected Versions** | The affected version range, in the format `introduced version - fixed version` (including both dev versions) |
| **Fixed Version** | The specific version number that fixed the bug |
| **Fix Description** | A brief description of the fix, including key code changes |
| **Fix Date** | The release date corresponding to the fixed version, in `YYYY/MM/DD` format |
| **Severity** | Mark according to the "Severity Classification" below |
| **Type** | Mark according to the "Type Classification" below, multiple types can be combined (e.g., `Adapter / Routing`) |

### Optional Fields

| Field | Description | Applicable Scenarios |
|-------|-------------|----------------------|
| **Reproduction Steps** | The minimal reproducible path to trigger the bug | Recommended for complex or sporadic bugs |
| **References** | Links to related Issues / PRs / Commits | Supplement when there are external discussions |
| **Regression Test** | Location of test cases used to verify the fix and prevent regression | Supplement when corresponding pytest cases have been written |

## Severity Levels

| Identifier | Level | Criteria | Typical Manifestations |
|------------|-------|---------|---------|
| 🔴 | Critical | Causes process crash, data loss/damage, core functionality completely unavailable, security vulnerabilities | OOM Kill, message cannot be sent, module cannot be loaded, hot reload failure |
| 🟡 | Medium | Function anomaly but with workaround, non-core functionality failure, intermittent issues | Incorrect state judgment, repeated triggering, cache expiration, inaccurate error messages |
| 🟢 | Minor | Does not affect core functionality, only code quality or experience issues, potential risks not yet triggered | Deprecated API, dead code, missing warning logs |

---

## Type Classification

| Type | Coverage |
|------|---------|
| Configuration System | `ConfigManager`, Configuration reading/writing, Configuration Schema, Hot reload |
| Event System | `Event` module (command/message/notice/request/meta), Event dispatching, Handler registration |
| Adapters | `AdapterManager`, `BaseAdapter`, Account parsing, Bot status, Middleware |
| Routing | `RouterManager`, HTTP/WebSocket/SSE routing, Rate limiting, CORS |
| Client | `HttpClient`, `ClientWebSocket`, aiohttp wrapper |
| Storage | `StorageManager`, SQLite, SQL builder, Nested keys |
| Loading System | `Loader`, `LazyModule`, `ModuleInitializer`, Strict mode, Module discovery |
| CLI | `epsdk` command, `init`/`run`/`install`, Argument parsing, Signal handling |
| Runtime | `sdk.run`/`restart`/`uninit`, Lifecycle, Signal, Subprocess |

---

## Item Template

To add a new bug item, please follow the format below:

```markdown
### [BUG-XXX] Title

**Problem**: Problem description (error message or typical phenomenon)
**Cause**: Root cause analysis
**Affected Versions**: Introduced version - Fixed version
**Fixed Version**: x.x.x
**Fix Content**: Fix solution
**Fix Date**: YYYY/MM/DD

<!-- Optional fields -->
**Reproduction Steps**: (Recommended for complex bugs)
**Related**: (Issue/PR links)
**Regression Test**: (Test case path)

**Severity**: 🔴 Critical | 🟡 Medium | 🟢 Minor
**Type**: Configuration System / Event System / Adapter / Router / Client / Storage / Loader System / CLI / Runtime
```

---

## Statistics Overview

| Severity | Count |
|----------|-------|
| 🔴 Critical | 15 |
| 🟡 Medium | 13 |
| 🟢 Minor | 2 |
| **Total** | **30** |

| Type | Count |
|------|-------|
| Adapters | 6 |
| Configuration System | 7 |
| Event System | 5 |
| CLI | 3 |
| Storage | 3 |
| Loading System | 3 |
| Routing | 2 |
| Client | 1 |
| Runtime | 1 |

> Note: A single bug can belong to multiple types; the table above is counted by primary type.

---

## Fixed Bugs

### [BUG-001] Event Handler Repeated Registration Causes Multiple Event Handling

**Issue**: When registering multiple handlers using decorators such as `@message` / `@notice`, the same event is triggered multiple times, causing commands to execute multiple times and logs to be duplicated.

**Cause**: The `BaseEventHandler` registers handlers to the adapter event bus without deduplication logic, causing each decorator to mount the handler once, resulting in multiple calls during event dispatch.

**Affected Versions**: 2.2.0-dev.0 - 2.2.1-dev.0

**Fixed Version**: 2.2.1-dev.0

**Fix**: Optimized `BaseEventHandler` to ensure each event type is registered only once to the adapter, preventing repeated triggering.

**Fix Date**: 2025/08/18

**Severity**: 🔴 Critical

**Type**: Event System

---

### [BUG-002] Init Command Adapter Configuration Path Type Error

**Issue**: When using the `ep init` command for interactive initialization, selecting a configuration adapter results in a type error:

```
Interactive initialization failed: unsupported operand type(s) for /: 'str' and 'str'
```

**Cause**: In version 2.3.7, the configuration file path adjustment had inconsistent method parameter types. The `_configure_adapters_interactive_sync` method received a `str` type parameter, but internally used the `Path` `/` operator to concatenate paths.

**Affected Versions**: 2.3.7 - 2.3.9-dev.1

**Fixed Version**: 2.3.9-dev.1

**Fix**: Changed the parameter type of `_configure_adapters_interactive_sync` from `str` to `Path`, passing `Path` objects directly during calls.

**Fix Date**: 2026/03/23

**Severity**: 🟡 Moderate

**Type**: CLI

---

### [BUG-003] Command Events Fail After Restart

**Issue**: After calling `sdk.restart()`, commands registered via `@command` are not triggered, resulting in the robot not responding after sending a command.

**Cause**: After `adapter.shutdown()` clears the event bus, the `_linked_to_adapter_bus` status of `BaseEventHandler` is not reset to `False`, causing the `_process_event` method to believe it is already mounted to the adapter bus and skip re-mounting.

**Affected Versions**: 2.2.x - 2.4.0-dev.2

**Fixed Version**: 2.4.0-dev.3

**Fix**: Introduced `_linked_to_adapter_bus` status tracking; after `_clear_handlers()` disconnects from the bus, `register()` automatically re-mounts next time, adapting to shutdown/restart scenarios.

**Fix Date**: 2026/04/09

**Severity**: 🔴 Critical

**Type**: Event System

---

### [BUG-004] Lifecycle Event Handlers Not Cleared

**Issue**: After `sdk.restart()`, old lifecycle event handlers still exist and trigger repeatedly, causing the same event to be processed multiple times.

**Cause**: The `lifecycle._handlers` dictionary was never cleared during `uninit()`, leaving old handlers and new handlers both active after restart.

**Affected Versions**: 2.3.0 - 2.4.0-dev.2

**Fixed Version**: 2.4.0-dev.3

**Fix**: In the cleanup process of `Uninitializer` (after all events are submitted), clear `lifecycle._handlers`.

**Fix Date**: 2026/04/09

**Severity**: 🟡 Moderate

**Type**: Runtime

---

### [BUG-005] Event.is_friend_add/is_friend_delete detail_type Inconsistent with OB12 Standard

**Issue**: `Event.is_friend_add()` checks `detail_type == "friend_add"`, `Event.is_friend_delete()` checks `detail_type == "friend_delete"`, but the OneBot12 standard defines `detail_type` values as `"friend_increase"` and `"friend_decrease"`. This inconsistency with `notice.py`'s `on_friend_add`/`on_friend_remove` decorators causes handlers registered via decorators to fail when the corresponding `is_friend_add()`/`is_friend_delete()` methods return `False`.

**Cause**: `wrapper.py` uses non-standard naming, while `notice.py` uses the correct OB12 standard naming.

**Affected Versions**: Since implementation

**Fixed Version**: 2.4.2-dev.1

**Fix**: Changed `is_friend_add()`'s matching value from `"friend_add"` to `"friend_increase"`, and `is_friend_delete()` from `"friend_delete"` to `"friend_decrease"`.

**Fix Date**: 2026/04/13

**Severity**: 🟡 Moderate

**Type**: Event System

---

### [BUG-006] adapter.clear() Not Clearing _started_instances Leading to Incorrect State After Restart

**Issue**: The `AdapterManager.clear()` method clears `_adapters`, `_adapter_info`, handlers, and `_bots`, but omits `_started_instances`. If `clear()` is called while an adapter is running, `_started_instances` retains dangling references, causing incorrect state detection after restart.

**Cause**: When `_started_instances` was introduced in 2.4.0-dev.1, it was not cleared in `clear()`.

**Affected Versions**: 2.4.0-dev.1 - 2.4.2-dev.0

**Fixed Version**: 2.4.2-dev.1

**Fix**: Added `self._started_instances.clear()` in the `clear()` method.

**Fix Date**: 2026/04/13

**Severity**: 🟡 Moderate

**Type**: Adapter

---

### [BUG-007] command.wait_reply() Uses Deprecated asyncio.get_event_loop()

**Issue**: The `CommandHandler.wait_reply()` method uses `asyncio.get_event_loop()` to create futures and get timestamps, which is deprecated in Python 3.10+. In asynchronous contexts, `asyncio.get_running_loop()` should be used. This is inconsistent with `wrapper.py`'s `wait_for()` method in the same file, which uses `get_running_loop()`.

**Cause**: The old API was used during development, and the newly added `wait_for()` method used the correct API but did not retroactively fix the old code.

**Affected Versions**: 2.3.0-dev.0

**Fixed Version**: 2.4.2-dev.1

**Fix**: Replaced two instances of `asyncio.get_event_loop()` in `command.py` with `asyncio.get_running_loop()`.

**Fix Date**: 2026/04/13

**Severity**: 🟢 Minor

**Type**: Event System

---

### [BUG-008] Bot Offline Event Repeatedly Submitted During Shutdown

**Issue**: When calling `adapter.shutdown()` to shut down all adapters, `_update_bot_status()` repeatedly submits Bot offline events during the shutdown process, causing the same batch of Bots to be marked offline multiple times and triggering the `adapter.bot.offline` lifecycle event multiple times.

**Cause**: The Bot status tracking system introduced in 2.4.0-dev.1 did not set a "shutting down" flag during `shutdown()`, so `_update_bot_status()` could not distinguish between normal offline and cascading offline during shutdown.

**Affected Versions**: 2.4.0-dev.1 - 2.4.2-dev.1

**Fixed Version**: 2.4.2-dev.1

**Fix**: Added `_is_being_shutdown` flag in `AdapterManager`, set to True at the start of `shutdown()` and cleared at the end; `_update_bot_status()` checks this flag and skips repeated submissions during shutdown.

**Fix Date**: 2026/04/21

**Severity**: 🟡 Moderate

**Type**: Adapter

---

### [BUG-009] LazyModule Synchronous Access to BaseModule Causing Incomplete Initialization

**Issue**: When users access lazy-loaded BaseModule attributes in synchronous contexts, the module uses `loop.create_task()` for asynchronous initialization but does not wait, leading to race conditions when attributes are accessed before initialization completes.

**Cause**: `_ensure_initialized()` uses `loop.create_task(self._initialize())` and returns immediately without ensuring initialization completes.

**Affected Versions**: 2.4.0-dev.0 - 2.4.2-dev.1

**Fixed Version**: 2.4.2-dev.2

**Fix**: In synchronous contexts, BaseModule initialization is changed to use `asyncio.run(self._initialize())` to ensure initialization completes before returning. The transparent proxy feature is maintained, so users do not need to perceive the difference between synchronous and asynchronous contexts.

**Fix Date**: 2026/04/21

**Severity**: 🟡 Moderate

**Type**: Loading System

---

### [BUG-010] Multi-threaded Configuration System Write Leads to Data Loss

**Issue**: In multi-threaded environments, when multiple threads call `config.setConfig()` simultaneously, the non-atomic read-modify-write operation in `_flush_config()` can lead to partial write loss.

**Cause**: Although `_flush_config()` uses `RLock`, there is no file lock protection between file reads and writes, and the `_schedule_write` Timer can be triggered multiple times, causing overwrites.

**Affected Versions**: 2.3.0 - 2.4.2-dev.1

**Fixed Version**: 2.4.2-dev.2

**Fix**:
1. Added file locking mechanism (`_file_lock`) to ensure atomic file operations.
2. Used temporary file writing followed by atomic renaming (`os.replace`/`os.rename`).
3. Improved `_schedule_write` Timer cancellation and rescheduling logic.

**Fix Date**: 2026/04/21

**Severity**: 🔴 Critical

**Type**: Configuration System

---

### [BUG-011] Windows Ctrl+C Cannot Stop Program

**Issue**: When running `python main.py` directly on Windows, pressing Ctrl+C cannot terminate the program. After the program starts normally and outputs the routing server information, Ctrl+C has no response, and the process can only be forcibly killed via Task Manager. However, it can be stopped normally when started via `epsdk run`, but `epsdk run` uses a subprocess model.

**Cause**: The `serve()` function of the Hypercorn ASGI server internally registers its own SIGINT handler via `signal.signal(SIGINT, handler)`, overriding Python's default `KeyboardInterrupt` handling mechanism. When Hypercorn is started as a background task via `asyncio.create_task()`, its internal shutdown process cannot be triggered normally (because it expects the `worker_serve` mode), causing the Ctrl+C signal to be swallowed by Hypercorn without any cleanup actions.

**Affected Versions**: 2.3.6 - 2.4.2

**Fixed Version**: 2.4.3-dev.0

**Fix**:
1. Switched the ASGI server from Hypercorn to Uvicorn (dependency change in `pyproject.toml`).
2. Started the server directly using `uvicorn.Server._serve()`, **bypassing** the `capture_signals()` signal handling context manager.
3. Used `server.should_exit = True` for graceful shutdown, and canceled the background task if timeout occurs.
4. Synchronized removal of the subprocess running model and `runtime/cleanup.py` cleanup module (subprocess cleanup mechanism is no longer needed).

**Fix Date**: 2026/04/28

**Severity**: 🔴 Critical

**Type**: CLI / Runtime

---

### [BUG-012] Hot Restart After Module Update Code Not生效

**Issue**: After executing `sdk.restart()` for a soft restart, the new code (such as new API routes) of modules/adapters upgraded via `epsdk install` does not take effect, and old logic is still executed. The latest code can only be loaded by completely restarting the process.

**Cause**: In `_do_restart()`, when re-initializing, `entry_point.load()` is called, but this function returns a cached old module object from `sys.modules` instead of reloading from disk.

**Affected Versions**: Early versions - 2.4.3-dev.1

**Fixed Version**: 2.4.3-dev.1

**Fix**: Clear the cache of loaded modules/adapters in `sys.modules` after `uninit()` and before `init()`, so that `entry_point.load()` loads the latest code from disk. Added `_collect_top_level_modules()` and `_invalidate_module_cache()` helper methods to deduce top-level module names via `top_level.txt` or entry-point value.

**Fix Date**: 2026/05/03

**Severity**: 🔴 Critical

**Type**: Loading System / Runtime

---

### [BUG-013] Module Loading Strategy Sorting Logic Error

**Issue**: `ModuleLoadStrategy` provides a `priority` field to declare the initialization priority of modules, but the implementation of the loading strategy has an error, causing modules to be initialized in an unexpected priority order, actually loaded in the default order of `entry_points()`. When modules have loading dependencies, the correct initialization order cannot be ensured through `priority`.

**Cause**: The sorting logic in the implementation of the loading strategy is incorrect; `initialize_modules()` does not sort the module list by `priority`.

**Affected Versions**: 2.3.4 - 2.4.5-dev.2

**Fixed Version**: 2.4.5-dev.3

**Fix**: Sort the module list by `priority` (descending) before traversing `initialize_modules()`. Modules with the same priority maintain their original relative order (stable sort).

**Fix Date**: 2026/05/15

**Severity**: 🟡 Moderate

**Type**: Loading System

---

### [BUG-014] Adapter Middleware Returning None Causes Event Data Loss

**Issue**: During the execution of OneBot12 middleware chains in `adapter.emit()`, if a middleware returns `None` (e.g., forgetting to `return data`), the subsequent middleware and all event handlers receive `processed_data` as `None`, causing event processing to fail completely.

**Cause**: The middleware chain implementation `processed_data = await middleware(processed_data)` does not check if the return value is `None`, directly overwriting the result from the previous step.

**Affected Versions**: unknown - 2.4.5-dev.3

**Fixed Version**: 2.4.5-dev.4

**Fix**: Ignore the return value if the middleware returns `None`, retain the original data, and output a warning-level log.

**Fix Date**: 2026/05/15

**Severity**: 🔴 Critical

**Type**: Adapter / Event System

---

### [BUG-015] Configuration File Path Relies on Working Directory

**Issue**: The configuration file path of `ConfigManager` is default relative path `"config/config.toml"`, which relies on `os.getcwd()` for resolution at runtime. If the working directory changes during runtime (e.g., via `os.chdir()`), the read/write operations of the configuration file point to the wrong location, leading to configuration loss or reading old data.

**Cause**: In `__init__`, the relative path is directly stored without being resolved to an absolute path at initialization.

**Affected Versions**: 2.3.7 - 2.4.5-dev.3

**Fixed Version**: 2.4.5-dev.4

**Fix**: In `ConfigManager.__init__()`, if the passed path is a relative path, automatically resolve it to an absolute path using `os.path.abspath()`.

**Fix Date**: 2026/05/15

**Severity**: 🟡 Moderate

**Type**: Configuration System

---

### [BUG-016] BaseStorage Confuses Storage Value None with Key Not Existing

**Issue**: `BaseStorage.get_multi()` / `__getattr__()` cannot distinguish between "key not existing" and "key's value is `None`", so when a user explicitly stores `None` and then reads it, it is treated as the key not existing.

**Cause**: The value retrieval logic directly uses `value is None` to determine if the key exists, lacking an independent "missing" marker.

**Affected Versions**: Early versions - 2.4.6-dev.6

**Fixed Version**: 2.4.6-dev.6

**Fix**: Introduced `_SENTINEL` sentinel value to distinguish between "key not existing" and "value is None", so they are no longer confused.

**Fix Date**: 2026/06/07

**Severity**: 🟡 Moderate

**Type**: Storage

---

### [BUG-017] WebSocket Route auto_accept Flag Lost After Service Restart

**Issue**: After a service restart (such as `sdk.restart()`), the `auto_accept` configuration of all WebSocket routes becomes `False`, and the originally expected automatic accept connections become suspended, causing the client to not receive responses for a long time, manifesting as a stuck WebSocket connection.

**Cause**: In `_restore_routes_from_records()`, when restoring routes from persistent records, `auto_accept` is hard-coded to `False` instead of reading the value from the original record; also, when the route storage tuple was expanded from a binary tuple to a ternary tuple, the restoration logic was not synchronized.

**Affected Versions**: 2.3.8-dev.0 - 2.4.6-dev.6

**Fixed Version**: 2.4.6-dev.6

**Fix**: The route storage tuple was expanded to `(handler, auth_handler, auto_accept)`, and `_restore_routes_from_records()` reads the real `auto_accept` value from the record instead of hard-coding `False`.

**Fix Date**: 2026/06/07

**Severity**: 🔴 Critical

**Type**: Routing

---

### [BUG-018] HTTP/WS Client Concurrent Calls Lead to Crash and Connection Leak

**Issue**: The HTTP and WebSocket clients in `Core/client.py` have multiple stability defects in concurrent scenarios, leading to connection leaks or process crashes:
- Multiple coroutines calling `ClientWebSocket.receive()` concurrently cause aiohttp to throw `Concurrent call to receive() is not allowed`
- `_get_http_session()` / `_get_ws_session()` concurrent calls may create multiple sessions, and `_drain_sessions()` does not close old connections, causing connection leaks
- The exception handling order in `request()` is incorrect: `except ClientConnectionError` (ErisPulse exception) is never triggered, aiohttp connection errors are caught by generic `except Exception`, causing the "retry + session rebuild" logic (dead code) to never execute
- `send_json()` ignores the `mode="binary"` parameter; `_get_ws_session()` does not pass default request headers

**Cause**: The client was initially implemented (2.4.6-dev.5) without concurrent protection and exception classification, handling the aiohttp exception system and ErisPulse custom exception inheritance relationship improperly.

**Affected Versions**: 2.4.6-dev.5 - 2.4.8

**Fixed Version**: 2.4.8

**Fix**:
1. Added `_recv_lock` to serialize all `receive()` / `receive_text()` / `receive_bytes()` calls
2. Added `_session_lock` to protect session creation; `_drain_sessions()` was changed to an asynchronous method and truly closes old sessions
3. Reconstructed `request()` exception handling order: `asyncio.TimeoutError` → `aiohttp.ClientConnectionError` (triggers session rebuild) → `aiohttp.ClientError` → `ClientError` (transparent pass) → `Exception`
4. Fixed `send_json()`'s mode handling, `_get_ws_session()`'s default request header pass, `close()`'s concurrent race condition, and `HttpResponse.__aexit__`'s repeated `release()`

**Fix Date**: 2026/06/12

**Severity**: 🔴 Critical

**Type**: Client

---

### [BUG-019] Adapter Hot Reload Route Conflict Causes Reload Failure

**Issue**: When a third-party module (such as Dashboard) triggers adapter hot reload, or when adapter startup fails and retries, due to the uncleaned old routes (such as `onebot11_default`) registered last time, an error is thrown: "WebSocket path ... already registered", causing reload failure. A complete restart of the process is required to recover.

**Cause**: `AdapterManager.shutdown()` only cleans routes using `unregister_all_by_namespace(platform)`, but adapters (such as OneBot11) register WebSocket routes using `onebot11_{account_name}` as the namespace, resulting in a mismatch in granularity and making cleanup an empty operation; route cleanup is also not performed for failed startup retries.

**Affected Versions**: Early versions - 2.4.9

**Fixed Version**: 2.4.9

**Fix**:
1. Route registration automatically tracks `owner → namespace` relationships using `current_owner` ContextVar
2. Added `unregister_all_by_owner(owner)`, cleaning up by owner during stop/restart, covering fine-grained namespaces
3. Added `_stop_adapter(platform)` primitive ("stop equals cleanup"), binding stopping the adapter and reclaiming its registered resources in one call; `restart()` and failed startup retries both go through this entry
4. Added framework-level `adapter.restart(platform)` API; third-party modules should call this method instead of directly operating the adapter instance

**Fix Date**: 2026/06/12

**Severity**: 🔴 Critical

**Type**: Adapter / Routing

---

### [BUG-020] Subprocess Mode `ep run <script>` Cannot Find Sub-packages in Script's Directory

**Issue**: When running a script using `ep r .\main.py` in non-hot-reload mode, if the script has relative imports (such as `from qg import ...`), it reports `No module named 'qg'` error. The `--reload` mode works normally.

**Cause**: The non-hot-reload mode directly calls `runpy.run_path()` to execute the script, which does not automatically add the script's directory to `sys.path`. The `--reload` mode runs via `subprocess.Popen` subprocess, which automatically inherits the current working directory, making `sys.path[0]` the script's directory, so it works normally.

**Affected Versions**: 2.5.0 - 2.5.2-dev.0

**Fixed Version**: 2.5.2-dev.0

**Fix**: Before calling `runpy.run_path()`, manually insert the script's directory into `sys.path[0]`.

**Fix Date**: 2026/06/27

**Severity**: 🟡 Moderate

**Type**: CLI

---

### [BUG-021] SQL Query Builder Rejects Valid Wildcard and List Expressions

**Issue**: `SQLiteQueryBuilder`'s `_build_select_sql()` calls `_validate_identifier()` for all SELECT columns, which uses a strict whitelist regex `^[a-zA-Z_][a-zA-Z0-9_]*$`, causing legitimate SQL syntax to be incorrectly judged as unsafe column names:

- `SELECT *` — `*` is a standard SQL wildcard
- `SELECT COUNT(*)` — aggregate function
- `SELECT users.name` — qualified column name
- `SELECT col AS alias` — column alias

Among these, `Select("*")` is used by modules like Cron, causing module `on_load` execution to fail and the module to fail to load.

**Cause**: In version 2.4.6, SQL injection protection was enhanced, introducing `_validate_identifier()` whitelist validation. This validation is applied to all column names but does not distinguish between the read end (SELECT/ORDER BY) and the write end (INSERT/UPDATE). SELECT columns allow complex SQL expressions and should not be restricted by simple identifier whitelist.

**Affected Versions**: 2.4.6 - 2.5.2-dev.1

**Fixed Version**: 2.5.2-dev.2

**Fix**: Changed the column validation for SELECT/ORDER BY from whitelist mode to blacklist mode:
1. Added `_validate_select_column()` function, only blocking SQL injection dangerous characters (`;` `'` `"` `--` `/*` `*/` `\x00` newline)
2. Allowed any valid SQL column expression (`*`, `table.*`, `table.column`, `COUNT(*)`, `col AS alias`, etc.)
3. INSERT/UPDATE column names still maintain strict whitelist validation (only allow simple identifiers)

**Fix Date**: 2026/06/29

**Severity**: 🔴 Critical

**Type**: Storage

---

### [BUG-022] _resolve_account() Account Resolution Regression (_accounts_data Not Populated)

**Issue**: After the configuration system was refactored in version 2.5.2, multi-account adapters that declared `AccountConfigClass` failed to resolve accounts when calling methods like `wait_reply`, `reply` that need to send messages. Even if the adapter correctly configured multi-account information, account resolution still failed.

**Cause**: In 2.5.2-dev.5, `_load_accounts()` (responsible for reading configuration + validation + populating `_accounts_data`) was refactored into `_ensure_accounts_exist()` (only generating configuration templates), but `_resolve_account()` still checks `self._accounts_data is None`. Since `_ensure_accounts_exist()` no longer populates `_accounts_data`, this attribute remains `None`, causing `_resolve_account()` to prematurely return `(None, None)`, and account resolution fails completely.

**Root Cause Chain**:
```
_load_accounts() was deleted
  → __init__ no longer populates _accounts_data
    → _accounts_data is always None
      → _resolve_account() checks _accounts_data is None → return (None, None)
        → downstream places calling _resolve_account (e.g., call_api) get None
          → triggers error
```

**Affected Versions**: 2.5.2-dev.5 - 2.5.2

**Fixed Version**: 2.5.3

**Fix**: In `BaseAdapter.__init__`, after `_ensure_accounts_exist()`, restore `_accounts_data` population:
```python
if self.AccountConfigClass is not None:
    self._ensure_accounts_exist()
    self._accounts_data = self.accounts  # restore population, data source is real-time read accounts attribute
```
The `_resolve_account()` logic remains unchanged, fully backward compatible:
- Adapters that do not declare `AccountConfigClass`: `_accounts_data` remains `None` → return `(None, None)`
- Adapters that declare `AccountConfigClass`: `_accounts_data` is populated → normal resolution
- Adapters that override `_load_accounts` or manually set `_accounts_data`: after `super().__init__()`, override, highest priority

**Fix Date**: 2026/07/07

**Severity**: 🔴 Critical

**Type**: Adapter / Configuration System

---

### [BUG-023] Adapter Cache Not Refreshed After Account Configuration Change

**Issue**: After users modify multi-account adapter account configurations (such as filling in token) through Dashboard, the adapter still uses old cache, and calling message-sending-related methods reports `未找到可用账户 (account_id=default)`. The new configuration must be reloaded by restarting the process.

**Cause**: `_accounts_data` is only read from configuration storage once during `BaseAdapter.__init__`, and is not refreshed thereafter. `AdapterManager._run_adapter()` and `restart()` do not re-read account configuration before calling `adapter.start()`, causing cache and actual configuration to be out of sync.

**Affected Versions**: 2.4.6 - 2.5.4

**Fixed Version**: 2.5.4

**Fix**: In `AdapterManager._run_adapter()` and `restart()`, refresh `adapter._accounts_data = adapter.accounts` before calling `adapter.start()`, ensuring the latest configuration is used each time it starts.

**Fix Date**: 2026/07/09

**Severity**: 🔴 Critical

**Type**: Adapter / Configuration System

---

### [BUG-024] storage.set() Writing Large Number ID Keys Triggers OOM Kill

**Issue**: When calling `storage.set()` to write a nested key path containing a large pure number field (such as QQ group number `871684833`), the process is killed by container OOM (exit code -9), causing the service to crash and unable to recover.

**Cause**: In the recursive implementation of `_set_nested_value`, pure number fields in the nested key path are mistakenly identified as list indices by `isdigit()`, triggering `current.extend([None] * (index - len(current) + 1))`, attempting to allocate hundreds of millions of elements, instantly exhausting memory.

**Root Cause Chain**:
```
Key path contains pure number field (such as group number 871684833)
  → isdigit() mistakenly identifies as array index
    → extend([None] * (871684833 - len(current) + 1))
      → attempts to allocate hundreds of millions of elements
        → memory exhausted → container OOM Kill (exit code -9)
```

**Affected Versions**: 2.5.1 - 2.5.5

**Fixed Version**: 2.5.5

**Fix**:
1. Always use a dictionary when pre-creating intermediate layers, no longer guess container type based on whether the next segment is a number
2. When setting the final value, only handle indexing if the container itself is a list and the index is less than `STORAGE_MAX_LIST_INDEX` (10000); ignore large indices safely
3. Change the recursive implementation to an iterative one, eliminating potential infinite recursion risks in the original code
4. Add `STORAGE_MAX_LIST_INDEX` constant to `Core/constants.py`, centrally managing the safe upper limit for indexes

**Fix Date**: 2026/07/10

**Reproduction Steps**:
```python
# Writing a nested key path containing a large number field (such as QQ group number) triggers OOM
await sdk.storage.aset("groups.871684833.name", "某群")
# → process memory spikes instantly, killed by OOM
```

**Regression Tests**: `tests/unit/test_unit_storage.py` adds 4 regression test cases
- `test_nested_key_numeric_segment_as_dict_key` — precisely reproduces OOM scenario
- `test_nested_key_numeric_segment_multiple` — multiple consecutive number fields as dictionary keys
- `test_nested_key_existing_list_index_set_within_limit` — reasonable index write to existing list
- `test_nested_key_list_index_safety_limit` — safety limit verification for large index

**Severity**: 🔴 Critical

**Type**: Storage

---

### [BUG-025] on_config_update Callback Not Core-Routed

**Issue**: The `on_config_update(old, new)` callback is defined in the base class (`BaseModule` / `BaseAdapter`), but the core framework does not associate it with configuration change events. The actual behavior is: when editing configuration through the configuration management panel, it can be triggered, but when manually editing `config.toml` or calling `setConfig()` via code, `on_config_update` is not triggered.

**Cause**: `ConfigManager` emits `config.set` / `config.updated` lifecycle events when configuration changes, but lacks the subscription logic to forward these events to each component's `on_config_update` method.

**Root Cause Chain**:
```
Core does not subscribe to config.set / config.updated
  → configuration change events are not forwarded
    → on_config_update is not called
      → manual file editing / code setConfig does not trigger hot update callback
```

**Affected Versions**: All versions

**Fixed Version**: 2.6.2

**Fix**: `ModuleManager` / `AdapterManager` register `config.set` (covering code `setConfig()` path) and `config.updated` (covering manual file editing path) event subscriptions, match by configuration key prefix and call the corresponding component's `on_config_update`, passing type-safe configuration objects. Also fix `_flush_config()`'s issue of not synchronizing `_config_mtime` after writing the file, avoiding the framework's own write being mistakenly judged as an external modification by the file monitoring task and repeatedly triggering `config.updated`.

**Compatibility Note**: Configuration hot updates are now centrally maintained by the framework core. Previously, the logic of triggering by the configuration management panel has been removed, and after upgrading the framework, the configuration management panel also needs to be upgraded synchronously, otherwise duplicate triggers (core + panel each call once) will occur. The `on_config_update` method signature and semantics remain unchanged, and subclasses do not need modification.

**Fix Date**: 2026/07/23

**Severity**: 🟡 Moderate

**Type**: Configuration System

---

### [BUG-026] notice/request Event reply Target Inference Error

**Issue**: When calling `event.reply()` in a group notice event (such as member joining a group `group_member_increase`), the message is sent to the user who triggered the event's private chat, not to the group where the event occurred. The same applies to friend notice events, where the reply target may be incorrect.

**Cause**: `infer_receive_type()` directly returns the event's `detail_type` as the session type. For message events, this is correct (`detail_type` values `private`/`group` are session types), but for notice/request events, `detail_type` is a semantic subtype (such as `group_member_increase`, `friend_increase`), not a session type. Subsequent `convert_to_send_type()` and `get_id_field()` find no value in the mapping table and default to `"user"` / `"user_id"`, causing the reply target to be incorrect.

**Root Cause Chain**:
```
notice event detail_type="group_member_increase"
  → infer_receive_type() directly returns "group_member_increase"
    → convert_to_send_type("group_member_increase") not in mapping table → default "user"
    → get_id_field("group_member_increase") not in mapping table → default "user_id"
      → target_id = event["user_id"]  ← new member's private chat (not group)
```

**Affected Versions**: All versions

**Fixed Version**: 2.7.0-dev.3

**Fix**: `infer_receive_type()` adds a check—`detail_type` is only returned directly if it is a known session type (standard or custom type); otherwise, the session type is inferred based on the ID field (`group_id` / `channel_id` / `user_id`, etc.).

**Regression Tests**: `tests/unit/test_unit_session_type.py` → `TestNoticeRequestTypeInference` (10 test cases)

**Fix Date**: 2026/07/29

**Severity**: 🟢 Minor

**Type**: Event System

---

### [BUG-027] Route Rate Limiting Cleanup Task Uses Fixed Window Causing Long Window Rules to Fail

**Issue**: When setting route rate limiting to a long window rule (such as `100/hour`, `{"requests": 100, "window": 3600}`), the rate limiting is ineffective—actually behaving like `100/minute` (up to ~6000 requests per hour), completely failing to provide the expected hourly protection.

**Cause**: `_apply_rate_limit` parses the actual `window` (up to 3600 seconds) per route, and per-request checks do use this window; however, the background cleanup task `_cleanup_expired_rate_limits` uses a fixed constant `DEFAULT_RATE_LIMIT_WINDOW_SECS` (60 seconds) as the unified cleanup threshold for all routes. Thus, time stamps earlier than 60 seconds are cleared by the cleanup task, and the hour window never accumulates close to 100 records, severely weakening the rate limiting.

**Root Cause Chain**:
```
_apply_rate_limit parses window=3600 (100/hour)
  → per-request checks use 3600s retention time (correct)
  → but _cleanup_expired_rate_limits uses fixed max_window=60s to clean
    → time stamps earlier than 60s are cleared
      → the hour window only retains records from the last 1 minute
        → 100/hour actually degrades to ~100/minute (relaxed by ~60x)
```

**Affected Versions**: 2.6.0-dev.0 - 2.7.0-dev.4

**Fixed Version**: 2.7.0-dev.5

**Fix**: Added `_rate_limit_windows: dict[str, int]` to record the actual window per store key; `_apply_rate_limit` writes the window when creating entries for the first time; `_cleanup_expired_rate_limits` cleans up by each key's own window (fallback to default value if missing); cleanup deletion and `stop()` synchronize maintenance of both dictionaries.

**Fix Date**: 2026/07/31

**Regression Tests**: `tests/unit/test_unit_router.py` → `TestRateLimit::test_cleanup_respects_per_route_window`

**Severity**: 🔴 Critical

**Type**: Routing

---

### [BUG-029] Configuration Listener Broadcasts Incomplete TOML and Silently Swallows Exceptions

**Issue**: When a user manually edits `config.toml` and saves halfway (producing a transient syntax error), the configuration monitoring background thread detects the mtime change, reloads the configuration, but fails to load and still broadcasts an empty configuration `{}` via `config.updated`, causing adapters/modules' `on_config_update` to receive an empty configuration and mistakenly assume all configuration items were cleared, reverting to default values. Additionally, the listener loop uses `except Exception: pass` to silently swallow all exceptions, making it impossible to diagnose watcher failures.

**Cause**: Two defects叠加:
1. `_load_config` overwrites `self._cache` to `{}` on TOML syntax error/permission error, but the background listener thread `_watch_loop` and cache timeout path `_check_cache_validity` both unconditionally execute `_emit_config_updated()` after calling `_load_config()`, broadcasting the "empty cache produced by failed load" as a real change.
2. `_watch_loop`'s `except Exception: pass` does not log any errors.

**Root Cause Chain**:
```
User saves halfway → TOML syntax error
  → _load_config() overwrites _cache = {}
    → _watch_loop unconditionally _emit_config_updated(new_config={})
      → adapters/modules on_config_update receive empty config
        → mistakenly assume configuration was cleared, revert to default values
```

**Affected Versions**: 2.6.2-dev.1 - 2.7.0-dev.4

**Fixed Version**: 2.7.0-dev.5

**Fix**:
1. `_load_config` now returns `bool`; on TOML syntax error/permission/other errors, it **retains the last valid cache** (no longer overwrites to `{}`), only logs diagnostic messages and returns `False`
2. `_watch_loop` and `_check_cache_validity` only emit `config.updated` if `_load_config()` returns `True`
3. `_watch_loop`'s `except Exception` is changed to warn-level logging (new i18n key `core.config.watcher_error`, synchronized in five languages)

**Fix Date**: 2026/07/31

**Regression Tests**: `tests/unit/test_unit_config.py` → `test_malformed_toml_preserves_last_valid_cache`, `test_permission_denied_logs_clear_message` (updated to verify retained cache + return False)

**Severity**: 🟡 Moderate

**Type**: Configuration System

---

### [BUG-030] Configuration watcher Race Condition Causes setConfig Delayed Write Silent Data Loss

**Issue**: Multiple users reported that after using `config.setConfig(key, value)` (default `immediate=False`), their module configuration was not written to `config.toml`, while other module configurations were normal. Setting `immediate=True` (force flush) could avoid this. The result is: configuration written during runtime is lost after the next restart, while configuration generated during startup persists.

**Cause**: Two overlapping defects:
1. **Logical Defect**: `_watch_loop` unconditionally `_dirty_keys.clear()` all pending write keys if `_check_file_change()` returns `True`. However, `_check_file_change()` only compares mtime with `!=`, and the framework's own `_flush_config` write operation also changes mtime—although `_flush_config` updates `_config_mtime` after writing, the watcher thread may still observe mtime differences between file write and mtime assignment (especially on coarse-grained filesystems), mistakenly judging it as "external modification" and discarding all pending write keys.
2. **Thread Defect**: `_watch_loop` operates `_write_timer`/`_dirty_keys` without holding `_lock`, causing data races with `setConfig` (holding lock to write `_dirty_keys`), `_schedule_write` (holding lock to write `_write_timer`).

**Root Cause Chain**:
```
Module A setConfig(immediate=True) → flush write, mtime changes
  → User module setConfig(immediate=False) → enters _dirty_keys, flush after 5s
    → watcher poll, _check_file_change observes mtime difference from previous own write
      → _dirty_keys.clear() → user module's pending write keys are silently discarded
        → configuration missing after restart
```

**Affected Versions**: 2.6.0 - 2.7.0

**Fixed Version**: 2.7.1

**Fix**:
1. Added `_last_self_write_mtime` field; after `_flush_config` writes, it synchronously records; in `_check_file_change`, if mtime changes, first compare this value, and if matched, judge as own write and return `False`
2. `_watch_loop` holds `_lock` throughout; if truly external modification, retains `_dirty_keys` (merge semantics), next flush merges with external content (dirty keys take precedence), no longer `clear()`
3. `getConfig`/`_check_cache_validity` paths are unaffected (their reload does not clear dirty keys)

**Fix Date**: 2026/08/06

**Regression Tests**: `tests/unit/test_unit_config.py` → `test_self_write_not_detected_as_external`, `test_external_change_preserves_dirty_keys`, `test_flush_merges_dirty_with_external`

**Severity**: 🔴 Critical

**Type**: Configuration System

---

### [BUG-032] "Write-After-Read" Reads Old Value During Configuration Delayed Write

**Issue**: After `config.setConfig()` (default `immediate=False` delayed write for ~5 seconds), immediately reading its **parent/ancestor node** (such as `set_erispulse_section("scope.actions.MyModule", {...})` followed by `get_erispulse_config()`) returns the old value, the written sub-key "disappears" until the flush, affecting "write-read-write" scenarios like scope configuration hot updates (exposed by test plugin `/t_section` use case in 2.8.0).

**Cause**: `setConfig` stores dot-separated keys in the pending write queue `_dirty_keys` as **flat form**, only `getConfig`'s **exact key query** hits the pending write queue; tree-path queries (such as `getConfig("ErisPulse.scope")`) only walk the cache tree, not overlay pending write values—during the delayed flush (`_flush_config` merges dirty keys into cache and clears the queue), a read-you-write gap forms.

**Affected Versions**: 2.6.0 - 2.8.0-dev.1

**Fixed Version**: 2.8.0-dev.1

**Fix**: `getConfig` introduces pending write overlay semantics—① exact match pending write key returns directly (original behavior unchanged); ② pending write key is the query key's ancestor → take the longest pending write ancestor and parse the remaining path in its value subtree; ③ pending write key is the query key's descendant → build an overlay subtree (`_dirty_overlay`) and deeply merge it with the cache subtree (`_deep_merge`, override priority, without modifying the original cache object). No pending write key uses the original fast path, zero additional overhead.

**Fix Date**: 2026/09/04

**Regression Tests**: `tests/unit/test_unit_config.py` → `test_get_config_overlays_dirty_descendant`, `test_get_config_overlay_merges_with_cache_siblings`, `test_get_config_overlay_new_branch`, `test_get_config_dirty_ancestor_query`, `test_get_config_dirty_exact_key_still_wins`

**Severity**: 🟡 Moderate

**Type**: Configuration System