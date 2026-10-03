# Bug Tracker

This document records known bugs and their fixes for the ErisPulse SDK, ordered chronologically by the version in which they were fixed.

> **To the Reader**
> No software is inherently perfect; even the most meticulous developers leave behind small errors. This tracker includes only issues that have a tangible impact on operation—those that are too minor or subtle to even warrant a "minor" classification will not appear here. The list may seem to have a large number of "severe" items, but the purpose of publicly documenting these bugs is to facilitate smoother troubleshooting and retrospective analysis, not to create anxiety: problems that are visible, documented, and fixed are proof of the project's continuous improvement. There is no need to be alarmed upon seeing this list; it is a troubleshooting tool, not a source of fear.

> **How to Read & Maintenance Guidelines**
> - Each bug entry contains structured fields such as problem description, root cause analysis, affected version range, fix solution, etc. It is recommended to check the "Affected Version" field before upgrading to see if it covers the version you are currently using.
> - If you need to add a new bug entry, please supplement the content at the corresponding location, following the field specifications and severity/type classifications below.

---

## Field Descriptions

### Mandatory Fields

| Field | Description |
|------|------|
| **Problem** | The external manifestation of the bug, observable anomalies from the user's perspective. Try to provide error messages or typical scenarios. |
| **Cause** | Root cause analysis, pointing to specific code defects (including "Root Cause Chain" diagrams for complex scenarios) |
| **Affected Version** | Affected version range, format `Introduced Version - Fixed Version` (including dev versions) |
| **Fixed Version** | The specific version number that fixed the bug |
| **Fix Content** | Brief description of the fix, including key code changes |
| **Fix Date** | The release date of the corresponding fixed version, using the `YYYY/MM/DD` format |
| **Severity** | Marked according to the "Severity Classification" below |
| **Type** | Marked according to the "Type Classification" below, can be combined (e.g., `Adapter / Router`) |

### Optional Fields

| Field | Description | Applicable Scenarios |
|------|------|---------|
| **Reproduction Steps** | The minimal reproducible path to trigger the bug | Complex bugs, intermittent bugs are recommended to supplement |
| **关联** | Related Issue / PR / Commit links | Supplement when there are external discussion records |
| **Regression Test** | Test case location for verifying the fix and preventing regression | Supplement when corresponding pytest cases are written |

---

## Severity Classification

| Identifier | Level | Judgment Criteria | Typical Manifestations |
|------|------|---------|---------|
| 🔴 | Severe | Causes process crash, data loss/damage, core functionality completely unusable, security vulnerabilities | OOM Kill, message cannot be sent, module cannot be loaded, hot reload failure |
| 🟡 | Medium | Functional anomalies but with workarounds, non-core functionality failure, intermittent issues | Incorrect status judgment, repeated triggering, cache expiration, inaccurate error messages |
| 🟢 | Minor | Does not affect core functionality, only code quality or experience issues, potential risks not yet triggered | Deprecated API, dead code, missing warning logs |

---

## Type Classification

| Type | Scope |
|------|---------|
| Configuration System | `ConfigManager`, configuration read/write, configuration Schema, hot update |
| Event System | `Event` module (command/message/notice/request/meta), event distribution, handler registration |
| Adapter | `AdapterManager`, `BaseAdapter`, account parsing, Bot status, middleware |
| Router | `RouterManager`, HTTP/WebSocket/SSE routing, rate limiting, CORS |
| Client | `HttpClient`, `ClientWebSocket`, aiohttp wrapper |
| Storage | `StorageManager`, SQLite, SQL builder, nested keys |
| Loader | `Loader`, `LazyModule`, `ModuleInitializer`, strict mode, module discovery |
| CLI | `epsdk` command, `init`/`run`/`install`, parameter parsing, signal handling |
| Runtime | `sdk.run`/`restart`/`uninit`, lifecycle, signals, subprocess |

---

## Entry Template

When adding a new bug entry, follow the format below:

```markdown
### [BUG-XXX] Title

**Problem**: Problem description (error message or typical phenomenon)
**Cause**: Root cause analysis
**Affected Version**: Introduced Version - Fixed Version
**Fixed Version**: x.x.x
**Fix Content**: Fix solution
**Fix Date**: YYYY/MM/DD

<!-- Optional fields -->
**Reproduction Steps**: (Recommended for complex bugs)
**关联**: (Issue/PR link)
**Regression Test**: (Test case path)

**Severity**: 🔴 Severe | 🟡 Medium | 🟢 Minor
**Type**: Configuration System / Event System / Adapter / Router / Client / Storage / Loader / CLI / Runtime
```

---

## Statistics Overview

| Severity | Count |
|--------|------|
| 🔴 Severe | 16 |
| 🟡 Medium | 18 |
| 🟢 Minor | 3 |
| **Total** | **37** |

| Type | Count |
|------|------|
| Adapter | 6 |
| Configuration System | 11 |
| Event System | 7 |
| CLI | 3 |
| Storage | 3 |
| Loader | 3 |
| Router | 2 |
| Client | 1 |
| Runtime | 1 |

> Note: A single bug can belong to multiple types; the table above counts by primary type.
> Note: BUG-028 / BUG-031 are missing (abandoned during registration, numbering not recycled for stability).

---

## Fixed Bugs

### [BUG-001] Event handler registration leads to duplicate event processing

**Problem**: When using multiple `@message` / `@notice` decorators to register handlers, the same event is triggered multiple times, causing commands to be executed multiple times and logs to be output repeatedly.

**Cause**: `BaseEventHandler` registers handlers to the adapter event bus without deduplication logic; each decorator mounts once to the bus, resulting in multiple calls during event distribution.

**Affected Version**: 2.2.0-dev.0 - 2.2.1-dev.0

**Fixed Version**: 2.2.1-dev.0

**Fix Content**: Optimize `BaseEventHandler` to ensure each event type is registered to the adapter only once, avoiding duplicate triggers.

**Fix Date**: 2025/08/18

**Severity**: 🔴 Severe

**Type**: Event System

---

### [BUG-002] Adapter configuration path type error in Init command

**Problem**: When using the `ep init` command for interactive initialization, selecting the configuration adapter results in a type error:

```
Interactive initialization failed: unsupported operand type(s) for /: 'str' and 'str'
```

**Cause**: In version 2.3.7, when adjusting the configuration file path, the method parameter types are inconsistent. `_configure_adapters_interactive_sync` receives a `str` type parameter but internally uses the `/` operator of `Path` to concatenate paths.

**Affected Version**: 2.3.7 - 2.3.9-dev.1

**Fixed Version**: 2.3.9-dev.1

**Fix Content**: Change the parameter type of `_configure_adapters_interactive_sync` from `str` to `Path`, passing `Path` objects directly during calls.

**Fix Date**: 2026/03/23

**Severity**: 🟡 Medium

**Type**: CLI

---

### [BUG-003] Commands fail to trigger after restart

**Problem**: After calling `sdk.restart()`, commands registered via `@command` are not triggered, resulting in the robot not responding when a command is sent.

**Cause**: `adapter.shutdown()` clears the event bus, but the `_linked_to_adapter_bus` status of `BaseEventHandler` is not reset to `False`, causing `_process_event` to think it is already linked to the adapter bus and skip re-linking.

**Affected Version**: 2.2.x - 2.4.0-dev.2

**Fixed Version**: 2.4.0-dev.3

**Fix Content**: Introduce `_linked_to_adapter_bus` status tracking; after `_clear_handlers()` disconnects the bus, the next `register()` automatically re-links, adapting to shutdown/restart scenarios.

**Fix Date**: 2026/04/09

**Severity**: 🔴 Severe

**Type**: Event System

---

### [BUG-004] Lifecycle event handlers not cleared

**Problem**: After `sdk.restart()`, old lifecycle event handlers still exist and are triggered repeatedly, causing the same event to be processed multiple times.

**Cause**: The `lifecycle._handlers` dictionary is never cleared during `uninit()`, causing old and new handlers to coexist after restart.

**Affected Version**: 2.3.0 - 2.4.0-dev.2

**Fixed Version**: 2.4.0-dev.3

**Fix Content**: Clear `lifecycle._handlers` at the end of the `Uninitializer` cleanup process (after all events are submitted), adapting to shutdown/restart scenarios.

**Fix Date**: 2026/04/09

**Severity**: 🟡 Medium

**Type**: Runtime

---

### [BUG-005] Event.is_friend_add/is_friend_delete detail_type inconsistent with OB12 standard

**Problem**: `Event.is_friend_add()` checks `detail_type == "friend_add"`, `Event.is_friend_delete()` checks `detail_type == "friend_delete"`, but the OneBot12 standard defines `detail_type` values as `"friend_increase"` and `"friend_decrease"`. This inconsistency with the values used by `notice.py`'s `on_friend_add`/`on_friend_remove` decorators causes handlers registered via decorators to fail when the corresponding `is_friend_add()`/`is_friend_delete()` judgment methods return `False`.

**Cause**: `wrapper.py` uses non-standard naming, while `notice.py` uses the correct OB12 standard naming.

**Affected Version**: Implemented since

**Fixed Version**: 2.4.2-dev.1

**Fix Content**: Change `is_friend_add()`'s matching value from `"friend_add"` to `"friend_increase"`, and `is_friend_delete()` from `"friend_delete"` to `"friend_decrease"`.

**Fix Date**: 2026/04/13

**Severity**: 🟡 Medium

**Type**: Event System

---

### [BUG-006] adapter.clear() not clearing _started_instances causing incorrect status after restart

**Problem**: The `AdapterManager.clear()` method clears `_adapters`, `_adapter_info`, handlers, and `_bots`, but omits clearing `_started_instances`. If an adapter is running when `clear()` is called, `_started_instances` retains dangling references, causing incorrect status judgment after restart.

**Cause**: When `_started_instances` was introduced in 2.4.0-dev.1, it was not cleared in `clear()`.

**Affected Version**: 2.4.0-dev.1 - 2.4.2-dev.0

**Fixed Version**: 2.4.2-dev.1

**Fix Content**: Add `self._started_instances.clear()` in the `clear()` method.

**Fix Date**: 2026/04/13

**Severity**: 🟡 Medium

**Type**: Adapter

---

### [BUG-007] command.wait_reply() uses deprecated asyncio.get_event_loop()

**Problem**: The `CommandHandler.wait_reply()` method uses `asyncio.get_event_loop()` to create futures and get timestamps, which has been deprecated in Python 3.10+. In asynchronous contexts, `asyncio.get_running_loop()` should be used. This is inconsistent with the `get_running_loop()` used in the `wrapper.py`'s `wait_for()` method.

**Cause**: The development used the old API, and the newly added `wait_for()` method used the correct API but did not retroactively fix the old code.

**Affected Version**: 2.3.0-dev.0

**Fixed Version**: 2.4.2-dev.1

**Fix Content**: Replace `asyncio.get_event_loop()` in `command.py` with `asyncio.get_running_loop()`.

**Fix Date**: 2026/04/13

**Severity**: 🟢 Minor

**Type**: Event System

---

### [BUG-008] Bot offline events repeatedly submitted during shutdown

**Problem**: When calling `adapter.shutdown()` to shut down all adapters, `_update_bot_status()` repeatedly submits Bot offline events during the shutdown process, causing the same batch of Bots to be marked offline multiple times and triggering multiple `adapter.bot.offline` lifecycle events.

**Cause**: The Bot status tracking system introduced in 2.4.0-dev.1 did not set a "shutting down" flag during `shutdown()`, so `_update_bot_status()` could not distinguish between normal offline and cascading offline during shutdown.

**Affected Version**: 2.4.0-dev.1 - 2.4.2-dev.1

**Fixed Version**: 2.4.2-dev.1

**Fix Content**: Add `_is_being_shutdown` flag in `AdapterManager`; set it to True at the start of `shutdown()` and clear it at the end; `_update_bot_status()` skips repeated submissions during shutdown based on this flag.

**Fix Date**: 2026/04/21

**Severity**: 🟡 Medium

**Type**: Adapter

---

### [BUG-009] LazyModule synchronous access to BaseModule causing incomplete initialization

**Problem**: When users access properties of a lazily loaded BaseModule in a synchronous context, the module uses `loop.create_task()` for asynchronous initialization but does not wait, leading to race conditions when properties are accessed before initialization is complete.

**Cause**: `_ensure_initialized()` for BaseModule uses `loop.create_task(self._initialize())` and returns immediately without ensuring initialization is complete.

**Affected Version**: 2.4.0-dev.0 - 2.4.2-dev.1

**Fixed Version**: 2.4.2-dev.2

**Fix Content**: In synchronous contexts, BaseModule initialization is changed to use `asyncio.run(self._initialize())` to ensure initialization is complete before returning. The transparent proxy characteristic is maintained, and users do not need to perceive the difference between synchronous and asynchronous contexts.

**Fix Date**: 2026/04/21

**Severity**: 🟡 Medium

**Type**: Loader

---

### [BUG-010] Multi-threaded configuration system write causing data loss

**Problem**: In a multi-threaded environment, when multiple threads simultaneously call `config.setConfig()`, the `_flush_config()` read-modify-write operation is not atomic, potentially causing some writes to be lost.

**Cause**: Although `_flush_config()` uses an `RLock`, there is no file lock protection between file reads and writes, and the `_schedule_write` Timer may be triggered multiple times, leading to overwrites.

**Affected Version**: 2.3.0 - 2.4.2-dev.1

**Fixed Version**: 2.4.2-dev.2

**Fix Content**:
1. Add file locking mechanism (`_file_lock`) to ensure atomic file operations
2. Use temporary files for writing and then atomically rename (`os.replace`/`os.rename`)
3. Improve `_schedule_write` Timer cancellation and re-scheduling logic

**Fix Date**: 2026/04/21

**Severity**: 🔴 Severe

**Type**: Configuration System

---

### [BUG-011] Windows Ctrl+C unable to stop the program

**Problem**: When running `python main.py` directly on Windows, pressing Ctrl+C does not terminate the program. After the program starts normally and outputs the routing server information, Ctrl+C has no response, and the process can only be forcibly terminated via the task manager. However, running via `epsdk run` works normally—though `epsdk run` uses a subprocess model.

**Cause**: The Hypercorn ASGI server's `serve()` function internally registers its own SIGINT handler via `signal.signal(SIGINT, handler)`, overriding Python's default `KeyboardInterrupt` handling mechanism. When Hypercorn is started as a background task via `asyncio.create_task()`, its internal shutdown process cannot be triggered properly (as it expects the `worker_serve` mode), causing the Ctrl+C signal to be swallowed by Hypercorn without triggering any cleanup actions.

**Affected Version**: 2.3.6 - 2.4.2

**Fixed Version**: 2.4.3-dev.0

**Fix Content**:
1. Switch the ASGI server from Hypercorn to Uvicorn (`pyproject.toml` dependency change)
2. Use `uvicorn.Server._serve()` to start the server directly, **bypassing** the `capture_signals()` signal handling context manager
3. Implement graceful shutdown via `server.should_exit = True`, canceling the background task if timeout occurs
4. Synchronize removal of the subprocess running model and `runtime/cleanup.py` cleanup module (no longer needed for subprocess cleanup)

**Fix Date**: 2026/04/28

**Severity**: 🔴 Severe

**Type**: CLI / Runtime

---

### [BUG-012] Hot reload after updating modules does not activate new code

**Problem**: After executing `sdk.restart()` for a soft reload, the new code (such as newly added API routes) of modules/adapters upgraded via `epsdk install` does not take effect, and the old logic is still executed. A complete process restart is required to load the latest code.

**Cause**: `_do_restart()` calls `entry_point.load()` during re-initialization, but this function returns cached module objects from `sys.modules` instead of reloading from disk.

**Affected Version**: Early versions - 2.4.3-dev.1

**Fixed Version**: 2.4.3-dev.1

**Fix Content**: Clear the cache of loaded modules/adapters in `sys.modules` before `init()` and after `uninit()`, so that `entry_point.load()` reloads the latest code from disk. Added `_collect_top_level_modules()` and `_invalidate_module_cache()` helper methods, deriving top-level module names via `top_level.txt` or entry-point values.

**Fix Date**: 2026/05/03

**Severity**: 🔴 Severe

**Type**: Loader / Runtime

---

### [BUG-013] Module loading strategy sorting logic error

**Problem**: `ModuleLoadStrategy` provides a `priority` field to declare module initialization priority, but the implementation has a flaw, causing modules not to be initialized in the expected priority order; instead, they are loaded in the default order of `entry_points()`. When modules have initialization dependencies, the correct initialization order cannot be ensured via `priority`.

**Cause**: The implementation of the loading strategy has a flawed sorting logic; `initialize_modules()` does not sort the module list by `priority`.

**Affected Version**: 2.3.4 - 2.4.5-dev.2

**Fixed Version**: 2.4.5-dev.3

**Fix Content**: Before `initialize_modules()` iteration, sort the module list by `priority` in descending order. Modules with the same priority maintain their original relative order (stable sort).

**Fix Date**: 2026/05/15

**Severity**: 🟡 Medium

**Type**: Loader

---

### [BUG-014] Adapter middleware returning None causes event data loss

**Problem**: When `adapter.emit()` executes the OneBot12 middleware chain, if a middleware returns `None` (e.g., forgetting to `return data`), the subsequent middleware and all event handlers receive `processed_data` as `None`, causing event processing to fail completely.

**Cause**: The middleware chain implementation `processed_data = await middleware(processed_data)` does not check if the return value is `None`, directly overwriting the previous processing result.

**Affected Version**: unknown - 2.4.5-dev.3

**Fixed Version**: 2.4.5-dev.4

**Fix Content**: If middleware returns `None`, ignore the return value, retain the original data, and output a warning-level log.

**Fix Date**: 2026/05/15

**Severity**: 🔴 Severe

**Type**: Adapter / Event System

---

### [BUG-015] Configuration file path depends on working directory

**Problem**: The `ConfigManager`'s configuration file path defaults to the relative path `"config/config.toml"`, which relies on `os.getcwd()` at runtime. If the working directory changes during runtime (e.g., via `os.chdir()`), configuration file read/write operations point to the wrong location, causing configuration loss or reading old data.

**Cause**: In `__init__`, the relative path is stored directly without resolving it to an absolute path at initialization.

**Affected Version**: 2.3.7 - 2.4.5-dev.3

**Fixed Version**: 2.4.5-dev.4

**Fix Content**: In `ConfigManager.__init__()`, if the passed path is a relative path, automatically resolve it to an absolute path using `os.path.abspath()`.

**Fix Date**: 2026/05/15

**Severity**: 🟡 Medium

**Type**: Configuration System

---

### [BUG-016] BaseStorage confuses storing None value with missing key

**Problem**: `BaseStorage.get_multi()` / `__getattr__()` cannot distinguish between "key does not exist" and "key's value is None", so when a user explicitly stores `None` and reads it later, it is treated as if the key does not exist.

**Cause**: The retrieval logic directly uses `value is None` to determine if a key exists, lacking an independent "missing" marker.

**Affected Version**: Early versions - 2.4.6-dev.6

**Fixed Version**: 2.4.6-dev.6

**Fix Content**: Introduce `_SENTINEL` sentinel value to distinguish between "key does not exist" and "value is None", so they are no longer confused.

**Fix Date**: 2026/06/07

**Severity**: 🟡 Medium

**Type**: Storage

---

### [BUG-017] WebSocket route auto_accept flag lost after service restart

**Problem**: After a service restart (such as `sdk.restart()`), the `auto_accept` configuration for all WebSocket routes reverts to `False`, and the originally expected auto-accepted connections remain pending, with clients receiving no response for a long time, resulting in WS connections freezing.

**Cause**: `_restore_routes_from_records()` hardcodes `auto_accept` to `False` when restoring routes from persistent records, without reading the true value from the original record; also, when the route storage tuple expanded from a binary tuple to a ternary tuple, the restoration logic was not synchronized.

**Affected Version**: 2.3.8-dev.0 - 2.4.6-dev.6

**Fixed Version**: 2.4.6-dev.6

**Fix Content**: The route storage tuple expands to `(handler, auth_handler, auto_accept)`, and `_restore_routes_from_records()` reads the true `auto_accept` value from the record instead of hardcoding `False`.

**Fix Date**: 2026/06/07

**Severity**: 🔴 Severe

**Type**: Router

---

### [BUG-018] Concurrent calls to HTTP/WS client cause crashes and connection leaks

**Problem**: The HTTP and WebSocket clients in `Core/client.py` have multiple stability defects in concurrent scenarios, leading to connection leaks or process crashes:
- Concurrent calls to `ClientWebSocket.receive()` from multiple coroutines cause aiohttp to throw `Concurrent call to receive() is not allowed`
- Concurrent calls to `_get_http_session()` / `_get_ws_session()` may create multiple sessions, and `_drain_sessions()` does not close old connections, causing connection leaks
- The exception handling order in `request()` is incorrect: `except ClientConnectionError` (ErisPulse exception) is never triggered, aiohttp connection errors are caught by the generic `except Exception`, causing the "retry connection + session recreation" logic (dead code) to never execute
- `send_json()` ignores the `mode="binary"` parameter; `_get_ws_session()` does not pass default request headers

**Cause**: The client's initial implementation (2.4.6-dev.5) lacks concurrency protection and proper handling of aiohttp exception hierarchy and ErisPulse custom exception inheritance.

**Affected Version**: 2.4.6-dev.5 - 2.4.8

**Fixed Version**: 2.4.8

**Fix Content**:
1. Add `_recv_lock` to serialize all `receive()` / `receive_text()` / `receive_bytes()` calls
2. Add `_session_lock` to protect session creation; `_drain_sessions()` is changed to an asynchronous method and truly closes old sessions
3. Refactor `request()` exception handling order: `asyncio.TimeoutError` → `aiohttp.ClientConnectionError` (triggers session recreation) → `aiohttp.ClientError` → `ClientError` (transparent pass) → `Exception`
4. Fix `send_json()`'s mode handling, `_get_ws_session()`'s default request header passing, `close()`'s concurrency race, and `HttpResponse.__aexit__`'s repeated `release()`

**Fix Date**: 2026/06/12

**Severity**: 🔴 Severe

**Type**: Client

---

### [BUG-019] Adapter hot reload causes route conflicts leading to reload failure

**Problem**: When a third-party module (such as Dashboard) triggers adapter hot reload, or when adapter startup fails and retries, old routes (such as `onebot11_default`) are not cleared, causing `WebSocket path ... already registered` conflicts, leading to reload failure. A complete process restart is required to recover.

**Cause**: `AdapterManager.shutdown()` only clears routes via `unregister_all_by_namespace(platform)`, but adapters (such as OneBot11) register WebSocket routes with `onebot11_{account_name}` as the namespace, resulting in a granularity mismatch and an empty operation for clearing; startup failure retry paths are also not cleared of previous residual routes.

**Affected Version**: Early versions - 2.4.9

**Fixed Version**: 2.4.9

**Fix Content**:
1. Route registration automatically tracks `owner → namespace` relationships via `current_owner` ContextVar
2. Add `unregister_all_by_owner(owner)`, cleaning up by owner during stop/restart, covering fine-grained namespaces
3. Add `_stop_adapter(platform)` primitive (stop equals cleanup), binding stopping an adapter and reclaiming its registered resources in a single call, used by `restart()` and startup failure retries
4. Add framework-level `adapter.restart(platform)` API, third-party modules should call this method instead of directly operating adapter instances

**Fix Date**: 2026/06/12

**Severity**: 🔴 Severe

**Type**: Adapter / Router

---

### [BUG-020] Subprocess mode `ep run <script>` cannot find subpackages in the script's directory

**Problem**: When running a script with `ep r .\main.py` in non-hot-reload mode, if the script has relative imports (e.g., `from qg import ...`), it reports `No module named 'qg'` errors. However, the `--reload` mode works correctly.

**Cause**: The non-hot-reload mode directly calls `runpy.run_path()` to execute the script, which does not automatically add the script's directory to `sys.path`. In contrast, the `--reload` mode runs via `subprocess.Popen` subprocess, which automatically inherits the current working directory, making `sys.path[0]` the script's directory, so it works correctly.

**Affected Version**: 2.5.0 - 2.5.2-dev.0

**Fixed Version**: 2.5.2-dev.0

**Fix Content**: Before calling `runpy.run_path()`, manually insert the script's directory into `sys.path[0]`.

**Fix Date**: 2026/06/27

**Severity**: 🟡 Medium

**Type**: CLI

---

### [BUG-021] SQL query builder rejects valid wildcards and list expressions

**Problem**: `SQLiteQueryBuilder`'s `_build_select_sql()` calls `_validate_identifier()` for all SELECT columns, which uses a strict whitelist regex `^[a-zA-Z_][a-zA-Z0-9_]*$`, causing valid SQL syntax to be incorrectly judged as unsafe column names:
- `SELECT *` — `*` is a standard SQL wildcard
- `SELECT COUNT(*)` — aggregate function
- `SELECT users.name` — qualified column name
- `SELECT col AS alias` — column alias

Among these, `Select("*")` is used by modules like Cron, causing module `on_load` execution to fail and the module to fail to load.

**Cause**: In version 2.4.6, enhanced SQL injection protection was introduced, adding the `_validate_identifier()` whitelist validation. This validation is applied to all column names, but not distinguished between read-side (SELECT/ORDER BY) and write-side (INSERT/UPDATE). SELECT columns allow complex SQL expressions and should not be restricted by simple identifier whitelist.

**Affected Version**: 2.4.6 - 2.5.2-dev.1

**Fixed Version**: 2.5.2-dev.2

**Fix Content**: Change the SELECT/ORDER BY column validation from whitelist mode to blacklist mode:
1. Add `_validate_select_column()` function, only blocking SQL injection dangerous characters (`;` `'` `"` `--` `/*` `*/` `\x00` newline)
2. Allow any valid SQL column expression (`*`, `table.*`, `table.column`, `COUNT(*)`, `col AS alias`, etc.)
3. INSERT/UPDATE column names still maintain strict whitelist validation (only allow simple identifiers)

**Fix Date**: 2026/06/29

**Severity**: 🔴 Severe

**Type**: Storage

---

### [BUG-022] _resolve_account() account resolution regression (_accounts_data not populated)

**Problem**: After the 2.5.2 configuration system refactoring, multi-account adapters that declare `AccountConfigClass` report `ValueError("未声明 AccountConfigClass，无法解析账户")` when calling methods like `wait_reply`, `reply` that require sending messages. Even if the adapter correctly configures multi-account information, account resolution still fails.

**Cause**: In 2.5.2-dev.5, `_load_accounts()` (responsible for reading configuration + validation + populating `_accounts_data`) was refactored into `_ensure_accounts_exist()` (only generating configuration templates), but `_resolve_account()` still checks `self._accounts_data is None`. Since `_ensure_accounts_exist()` no longer populates `_accounts_data`, this attribute remains `None`, causing `_resolve_account()` to prematurely return `(None, None)`, and account resolution fails completely.

**Root Cause Chain**:
```
_load_accounts() was deleted
  → __init__ no longer populates _accounts_data
    → _accounts_data remains None
      → _resolve_account() checks _accounts_data is None → return (None, None)
        → downstream calls to _resolve_account (e.g. call_api) get None
          → triggers error
```

**Affected Version**: 2.5.2-dev.5 - 2.5.2

**Fixed Version**: 2.5.3

**Fix Content**: In `BaseAdapter.__init__`, after `self._ensure_accounts_exist()`, restore the population of `_accounts_data`:
```python
if self.AccountConfigClass is not None:
    self._ensure_accounts_exist()
    self._accounts_data = self.accounts  # restore population, data source is real-time read accounts attribute
```
The `_resolve_account()` logic remains unchanged, fully backward compatible:
- For adapters that do not declare `AccountConfigClass`: `_accounts_data` remains `None` → return `(None, None)`
- For adapters that declare `AccountConfigClass`: `_accounts_data` is populated → normal resolution
- For adapters that overwrite `_load_accounts` or manually set `_accounts_data`: override after `super().__init__()` call, highest priority

**Fix Date**: 2026/07/07

**Severity**: 🔴 Severe

**Type**: Adapter / Configuration System

---

### [BUG-023] After modifying account configuration, adapter cache is not refreshed causing account resolution failure

**Problem**: After users modify the account configuration of a multi-account adapter (e.g., filling in the token) through the Dashboard, the adapter still uses the old cache, and calling methods related to sending messages reports `未找到可用账户 (account_id=default)`. The process must be restarted to make the new configuration take effect.

**Cause**: `_accounts_data` is only read from the configuration storage once during `BaseAdapter.__init__`, and is not refreshed thereafter. `AdapterManager._run_adapter()` and `restart()` do not re-read the account configuration before calling `adapter.start()`, causing the cache to be out of sync with the actual configuration.

**Affected Version**: 2.4.6 - 2.5.4

**Fixed Version**: 2.5.4

**Fix Content**: In `AdapterManager._run_adapter()` and `restart()`, refresh `adapter._accounts_data = adapter.accounts` before calling `adapter.start()`, ensuring that the latest configuration is used each time the adapter starts.

**Fix Date**: 2026/07/09

**Severity**: 🔴 Severe

**Type**: Adapter / Configuration System

---

### [BUG-024] storage.set() writing large numeric ID keys triggers OOM Kill

**Problem**: When calling `storage.set()` to write a nested key path containing a large pure numeric field (such as QQ group ID `871684833`), the process is killed by the container OOM (exit code -9), causing the service to crash and unable to recover.

**Cause**: In the recursive implementation of `_set_nested_value`, the pure numeric field in the nested key path is mistakenly identified as a list index by `isdigit()`, triggering `current.extend([None] * (index - len(current) + 1))`, attempting to allocate hundreds of millions of elements, instantly exhausting memory.

**Root Cause Chain**:
```
The key path contains a pure numeric field (such as group ID 871684833)
  → isdigit() mistakenly identifies it as an array index
    → extend([None] * (871684833 - len(current) + 1))
      → attempts to allocate hundreds of millions of elements
        → memory exhausted → container OOM Kill (exit code -9)
```

**Affected Version**: 2.5.1 - 2.5.5

**Fixed Version**: 2.5.5

**Fix Content**:
1. Always use a dictionary when pre-creating intermediate layers, no longer guessing the container type based on whether the next segment is a number
2. Only when the container itself is a list and the index is less than `STORAGE_MAX_LIST_INDEX` (10000) do we handle it as an index; large indexes are safely skipped
3. Change the recursive implementation to an iterative one, eliminating potential infinite recursion risks in the original code
4. Add `STORAGE_MAX_LIST_INDEX` constant to `Core/constants.py`, centrally managing the safe index upper limit

**Fix Date**: 2026/07/10

**Reproduction Steps**:
```python
# Writing a nested key path containing a large number field (such as QQ group ID) triggers OOM
await sdk.storage.aset("groups.871684833.name", "某群")
# → Process memory surges instantly, killed by OOM
```

**Regression Test**: `tests/unit/test_unit_storage.py` adds 4 regression test cases
- `test_nested_key_numeric_segment_as_dict_key` — precisely reproduces the OOM scenario
- `test_nested_key_numeric_segment_multiple` — multiple consecutive number fields as dictionary keys
- `test_nested_key_existing_list_index_set_within_limit` — existing list index write within limit
- `test_nested_key_list_index_safety_limit` — safety limit for large indexes

**Severity**: 🔴 Severe

**Type**: Storage

---

### [BUG-025] on_config_update callback not called by core route

**Problem**: `on_config_update(old, new)` callback is defined in the base class (`BaseModule` / `BaseAdapter`), but the framework core does not link these events to the callback. As a result, when the configuration is modified via the configuration management panel, the callback is triggered, but when the `config.toml` file is manually edited or `setConfig()` is called, the `on_config_update` is not triggered.

**Cause**: `ConfigManager` emits `config.set` / `config.updated` lifecycle events when the configuration changes, but there is no subscription logic to forward these events to each component's `on_config_update` method.

**Root Cause Chain**:
```
Core does not subscribe to config.set / config.updated
  → Configuration change events are not forwarded
    → on_config_update is not called
      → Manual editing of file / code setConfig does not trigger hot update callback
```

**Affected Version**: All versions

**Fixed Version**: 2.6.2

**Fix Content**: `ModuleManager` / `AdapterManager` register subscriptions for `config.set` (covering code `setConfig()` path) and `config.updated` (covering manual file editing path), match by configuration key prefix and call the corresponding component's `on_config_update`, passing type-safe configuration objects. Also fix `_flush_config()` writing to file without synchronizing `_config_mtime`, avoiding framework self-writing being mistakenly judged as external modification and repeatedly triggering `config.updated`.

**Compatibility Note**: The framework core now centrally maintains configuration hot updates. Previously, the configuration management panel triggered it on behalf of the core, which has been removed; after upgrading the framework, the configuration management panel must also be upgraded, otherwise duplicate triggers (core + panel each call once) will occur. The `on_config_update` method signature and semantics remain unchanged, subclasses do not need to modify.

**Fix Date**: 2026/07/23

**Severity**: 🟡 Medium

**Type**: Configuration System

---

### [BUG-026] notice/request event reply target inference error

**Problem**: In group notification events (such as member joining a group `group_member_increase`), calling `event.reply()` sends the message to the private chat of the user who triggered the event, not to the group where the event occurred. The same applies to friend notification events, where the reply target may be incorrect.

**Cause**: `infer_receive_type()` directly returns the event's `detail_type` as the session type. For message events, this is correct (the `detail_type` values `private`/`group` are the session types), but for notice/request events, the `detail_type` is a semantic sub-type (such as `group_member_increase`, `friend_increase`), not the session type. Subsequent `convert_to_send_type()` and `get_id_field()` lookups in the mapping table do not find the value, defaulting to `"user"` / `"user_id"`, resulting in the reply target being incorrect.

**Root Cause Chain**:
```
notice event detail_type="group_member_increase"
  → infer_receive_type() directly returns "group_member_increase"
    → convert_to_send_type("group_member_increase") not in mapping table → default "user"
    → get_id_field("group_member_increase") not in mapping table → default "user_id"
      → target_id = event["user_id"]  ← new member's private chat (not the group)
```

**Affected Version**: All versions

**Fixed Version**: 2.7.0-dev.3

**Fix Content**: `infer_receive_type()` adds a check—only return `detail_type` directly if it is a known session type (standard or custom type); otherwise, infer the correct session type based on the ID field (`group_id` / `channel_id` / `user_id` etc.).

**Regression Test**: `tests/unit/test_unit_session_type.py` → `TestNoticeRequestTypeInference` (10 test cases)

**Fix Date**: 2026/07/29

**Severity**: 🟢 Minor

**Type**: Event System

---

### [BUG-027] Route rate limiting cleanup task uses fixed window causing long window rate limiting rules to fail

**Problem**: When routing rate limiting is configured as a long window rule (such as `100/hour`, `{"requests": 100, "window": 3600}`), the rate limiting is ineffective—practically behaving like `100/minute` (about 6000 requests per hour), failing to provide the intended hourly protection.

**Cause**: `_apply_rate_limit` parses the actual `window` for each route (up to 3600 seconds), and the per-request check does use this window; however, the background cleanup task `_cleanup_expired_rate_limits` uses a fixed constant `DEFAULT_RATE_LIMIT_WINDOW_SECS` (60 seconds) as the cleanup threshold for all routes. Thus, time stamps earlier than 60 seconds are cleared by the cleanup task, so the hour window never accumulates close to 100 records, and the rate limiting is severely weakened.

**Root Cause Chain**:
```
_apply_rate_limit parses window=3600 (100/hour)
  → per-request check uses 3600s retention time (correct)
  → but _cleanup_expired_rate_limits uses fixed max_window=60s for cleanup
    → time stamps before 60 seconds are cleared
      → the hour window only retains records from the last 1 minute
        → 100/hour actually degrades to ~100/minute (relaxed by about 60x)
```

**Affected Version**: 2.6.0-dev.0 - 2.7.0-dev.4

**Fixed Version**: 2.7.0-dev.5

**Fix Content**: Add `_rate_limit_windows: dict[str, int]` to record the actual window for each route; `_apply_rate_limit` writes the window when creating a new entry for the first time; `_cleanup_expired_rate_limits` cleans up based on each key's own window (fallback to default if missing); cleanup and deletion of entries and `stop()` synchronize maintenance of the two dictionaries.

**Fix Date**: 2026/07/31

**Regression Test**: `tests/unit/test_unit_router.py` → `TestRateLimit::test_cleanup_respects_per_route_window`

**Severity**: 🔴 Severe

**Type**: Router

---

### [BUG-029] Configuration listener task broadcasts incomplete TOML and silently swallows exceptions

**Problem**: When a user manually edits `config.toml` and saves it halfway (producing a temporary syntax error), the configuration monitoring background thread detects the mtime change, reloads the configuration, but fails to load it and still broadcasts an empty configuration `{}` as `config.updated`, causing adapters/modules' `on_config_update` to receive an empty configuration and mistakenly assume all configuration items have been cleared and revert to default values. Additionally, the listener loop uses `except Exception: pass` to silently swallow all exceptions, making it impossible to diagnose watcher faults.

**Cause**: Two defects叠加:
1. `_load_config` overwrites `self._cache` as `{}` when TOML syntax errors/permission errors occur, but the background listener thread `_watch_loop` and cache timeout path `_check_cache_validity` both execute `_emit_config_updated(new_config={})` unconditionally after calling `_load_config()`, broadcasting the "empty cache produced by loading failure" as a real change.
2. `_watch_loop`'s `except Exception: pass` does not log any errors.

**Root Cause Chain**:
```
User saves halfway → TOML syntax error
  → _load_config() overwrites _cache = {}
    → _watch_loop unconditionally _emit_config_updated(new_config={})
      → adapters/modules on_config_update receive empty config
        → mistakenly assume configuration has been cleared, revert to default values
```

**Affected Version**: 2.6.2-dev.1 - 2.7.0-dev.4

**Fixed Version**: 2.7.0-dev.5

**Fix Content**:
1. `_load_config` changed to return `bool`; if TOML syntax error/permission error/other errors occur, retain the last valid cache (no longer overwrite as `{}`), only record diagnostic logs and return `False`
2. `_watch_loop` and `_check_cache_validity` only emit `config.updated` if `_load_config()` returns `True`
3. `_watch_loop`'s `except Exception` changed to log at warning level (new i18n key `core.config.watcher_error`, five languages synchronized)

**Fix Date**: 2026/07/31

**Regression Test**: `tests/unit/test_unit_config.py` → `test_malformed_toml_preserves_last_valid_cache`, `test_permission_denied_logs_clear_message` (updated to verify retaining cache and returning False)

**Severity**: 🟡 Medium

**Type**: Configuration System

---

### [BUG-030] Configuration watcher race condition causes setConfig delay write silently loses data

**Problem**: Multiple users report that after using `config.setConfig(key, value)` (default `immediate=False`), their module configuration is not written to `config.toml`, while other modules' configurations are normal. Setting `immediate=True` (force flush) can avoid this. The result is: configuration written during runtime is lost after the next restart, while configuration generated during startup remains.

**Cause**: Two overlapping defects:
1. **Logical defect**: `_watch_loop` unconditionally `_dirty_keys.clear()` when `_check_file_change()` returns `True`, regardless of whether the file change is due to external modification. However, `_check_file_change()` only uses `!=` to compare mtime; the framework's own `_flush_config` writing also changes mtime—although `_flush_config` updates `_config_mtime` after writing, the watcher thread may still observe mtime differences (and on coarse-grained file systems) between file write and mtime assignment, mistakenly identifying it as "external modification" and clearing all dirty keys.
2. **Thread defect**: `_watch_loop` operates `_write_timer`/`_dirty_keys` without holding `_lock`, leading to data races with `setConfig` (holding lock to write `_dirty_keys`), `_schedule_write` (holding lock to write `_write_timer`).

**Root Cause Chain**:
```
Module A setConfig(immediate=True) → flush writes to disk, mtime changes
  → User module setConfig(immediate=False) → enters _dirty_keys, flushes to disk after 5s
    → Watcher loop, _check_file_change observes mtime difference from previous self-write
      → _dirty_keys.clear() → User module's dirty keys are silently discarded
        → Configuration missing after restart
```

**Affected Version**: 2.6.0 - 2.7.0

**Fixed Version**: 2.7.1

**Fix Content**:
1. Add `_last_self_write_mtime` field; `_flush_config` records it after writing; `_check_file_change` compares it first when mtime changes, returns `False` if matches, indicating self-write
2. `_watch_loop` holds `_lock` throughout; retains `_dirty_keys` for actual external modification (merge semantics), merges dirty keys with external content during next flush (dirty keys take precedence), no longer `clear()`
3. `getConfig`/`_check_cache_validity` paths are unaffected (their reload does not clear dirty keys)

**Fix Date**: 2026/08/06

**Regression Test**: `tests/unit/test_unit_config.py` → `test_self_write_not_detected_as_external`, `test_external_change_preserves_dirty_keys`, `test_flush_merges_dirty_with_external`

**Severity**: 🔴 Severe

**Type**: Configuration System

---

### [BUG-032] Configuration delay write period "write after read" reads old value

**Problem**: After writing a dot-separated key with `config.setConfig()` (default `immediate=False` delay of about 5 seconds), immediately reading its parent/ancestor node (e.g., `set_erispulse_section("scope.actions.MyModule", {...})` then calling `get_erispulse_config()`) returns the old value, the written sub-key "disappears" until the flush, affecting scenario like scope configuration hot update ("write-read-write") (exposed by 2.8.0 test plugin `/t_section` use case).

**Cause**: `setConfig` stores dot-separated keys as **flat** entries in the dirty queue `_dirty_keys`, only `getConfig`'s **exact key query** hits the dirty queue; tree-path queries (e.g., `getConfig("ErisPulse.scope")`) only go through the cache tree, not overlaying dirty values—during the delay write period (`_flush_config` merges dirty keys into cache and clears the queue), a read-you-write gap forms.

**Affected Version**: 2.6.0 - 2.8.0-dev.1

**Fixed Version**: 2.8.0-dev.1

**Fix Content**: `getConfig` introduces dirty overlay semantics—① exact match dirty key returns directly (original behavior unchanged); ② dirty key is an ancestor of the query key → take the longest dirty ancestor and parse the remaining path in its value subtree; ③ dirty key is a descendant of the query key → build an overlay subtree (`_dirty_overlay`) and deeply merge it with the cache subtree (`_deep_merge`, override priority, without modifying the original cache object). Without dirty keys, go through the original fast path, zero additional overhead.

**Fix Date**: 2026/09/04

**Regression Test**: `tests/unit/test_unit_config.py` → `test_get_config_overlays_dirty_descendant`, `test_get_config_overlay_merges_with_cache_siblings`, `test_get_config_dirty_ancestor_query`, `test_get_config_dirty_exact_key_still_wins`

**Severity**: 🟡 Medium

**Type**: Configuration System

---

### [BUG-033] wait_reply hangs and replies are starved by high-priority processors

**Problem**: When a module calls `wait_reply()` to wait for a user reply, if that reply message is claimed by a higher-priority event processor (`mark_processed()`), the command dispatcher checks `_processed` status at the entry and returns directly, so the reply matching logic at the end of the dispatcher never executes—the waiting party receives no reply and times out, returning `None`. Typical trigger scenario: using high-priority message processors (recording/auditing/blocking) results in random failures of dialog-style interactions.

**Cause**: Reply matching `_check_pending_reply` is placed at the end of `_handle_message` (only executed if the command is not matched), while `_processed` checking is before it—the order of claim checking and reply matching is reversed. Interactive waiting is a framework-level session continuation mechanism, not a competition between processors, and should not be affected by other processors' claim.

**Affected Version**: 2.2.0-dev.0 - 2.8.0-dev.1

**Fixed Version**: 2.8.0-dev.2

**Fix Content**: Move reply matching to the entry of `_handle_message` (before `_processed` checking, only for message events): first try to complete pending dialogues, if matched, the event is marked as processed, and subsequent checks short-circuit naturally; if not matched, continue the original command matching process. Also delegate the judgment chain to a new interaction session manager (`Core/Event/interaction.py`), gaining session cancellation and permission review capabilities.

**Fix Date**: 2026/09/08

**Regression Test**: `tests/unit/test_unit_interaction.py` (TestRegisterResolve match/not match/claim mark), `tests/unit/test_unit_event.py` (wait_reply full chain)

**Severity**: 🟡 Medium

**Type**: Event System / Command System

---

### [BUG-034] Scope persist=False runtime binding is silently overwritten by any subsequent configuration write

**Problem**: `scope.set_module(..., persist=False)` and other runtime bindings only modify memory `self._data`; but scope subscribes to `config.set` / `config.updated` events, and any code writing configuration (e.g., a module loading its own default configuration) triggers scope to rebuild the configuration tree from the configuration file, causing all previous runtime bindings to be silently lost (reverting to default allow), with no log prompts. Scenarios relying on runtime bindings (Dashboard "runtime-only" switches, module runtime dynamic disable) revert to behavior after unrelated module writes configuration.

**Cause**: Root cause chain: `scope.set/delete(persist=False)` only writes to memory (`Core/scope.py`) → any `setConfig` triggers `config.set` event → `_on_config_updated` unconditionally `_load_config()` → `_apply_tree()` replaces `self._data = {...}` globally → runtime bindings not in the configuration file are discarded.

**Affected Version**: 2.8.0-dev.1 - 2.8.0-dev.2
**Fixed Version**: 2.8.0-dev.2
**Fix Content**: Introduce a runtime overlay layer `_runtime_overrides` (including deletion sentinel): `persist=False` write/delete records into the overlay layer, `apply_tree()` rebuilds the persistent layer and replays in write order, runtime rules remain effective after any configuration write; `persist=True` write/delete clears corresponding overlay records (user persistence semantics take precedence); `config.set` filters events by key precisely, `config.updated` compares new and old scope sections, only rebuilds if scope actually changes (avoiding irrelevant write flushing判定 LRU cache); add `unregister_by_owner()` for module unload to clean up with the caller. `Core.Event.overrides`'s persist=False runtime overwrite has a similar problem, fixed synchronously with the overlay architecture.
**Fix Date**: 2026/09/09

**Reproduction Steps**: ① `scope.set_module("testplat", blocked=["TestB"], persist=False)` →判定 False; ② any module executes `config.setConfig("HelpModule", {...})` → triggers scope rebuild; ③ `scope.is_allowed("testplat", None, "TestB")` returns True (expected still False).
**关联**: Issue #432
**Regression Test**: `tests/unit/test_unit_scope.py::TestRuntimeOverrideSurvival` (irrelevant write survives/ tree rebuild replays/ deletion sentinel/ persistent clear/ precise invalidation/ owner cleanup)

**Severity**: 🟡 Medium
**Type**: Configuration System / Runtime

---

### [BUG-035] Configuration panel select options and dict fields rendered as [object Object]

**Problem**: In the WebUI configuration panel, select field options drop-down displays `[object Object]` (e.g., dynamically generated color style options); dict fields (such as `stalker_mode`, `knowledge_base`, etc.) without declared control types display `[object Object]` in text boxes, making it impossible to view and edit normally.

**Cause**: Two independent defects: ① The framework's i18n resolver `_resolve_i18n_text` only restores dictionaries with an `i18n` key, and when the option label is a dictionary with only `default` (no i18n key for dynamic text), it is passed through as is, and the frontend `esc(label)` string coercion results in `[object Object]`; ② The Dashboard rendering branch only handles JSON textarea for array types, dict values fall into the plain text input branch and are coerced by `String()`. Additionally, if a module mistakenly declares `_schema_meta` as a regular dataclass field (missing `ClassVar` annotation), it is treated as a configuration field and enters the schema, exacerbating the confusion.

**Affected Version**: 2.7.0 - 2.8.0-dev.2
**Fixed Version**: 2.8.0-dev.2
**Fix Content**: ① `_resolve_i18n_text` supports dictionaries with only `default` as a key, restoring them to text; ② The framework's schema/template/default value/population/validation/five places uniformly exclude fields prefixed with an underscore (mistaken declaration is harmless); ③ Dashboard select option label objects are parsed as fallback (prioritizing `default`), dict/table fields are rendered as JSON textarea (saving path as `tp=object` JSON.parse back, complete round-trip).
**Fix Date**: 2026/09/09

**Regression Test**: `tests/unit/test_unit_config.py::TestResolveI18nDefaultOnlyDict`, `TestSchemaUnderscoreFieldExclusion`

**Severity**: 🟡 Medium
**Type**: Configuration System

---

### [BUG-036] Multi-instance shared configuration directory causes occasional configuration write failures (ENOENT)

**Problem**: In Docker deployment scenarios (multiple containers mounting the same host configuration directory), the log occasionally shows two consecutive lines of "Failed to write configuration file ... [Errno 2] No such file or directory: '...config.toml.tmp' -> '...config.toml'". This configuration write is discarded (the old configuration is fully retained, no configuration loss is observed), the function is unaffected, but the alert repeatedly interferes with troubleshooting, and the configuration items to be written must wait for the next write to be written to disk.

**Cause**: Root cause chain: `_flush_config` / `setConfigTemplate` use a **fixed-name** temporary file `config.toml.tmp` to carry new content, `write()` does not `fsync` before `rename()` directly. Two ErisPulse instances sharing the same configuration directory, B instance `open("w")` may **truncate** A instance's ongoing temporary file → A's `rename()` when the target has been taken by B or content truncated, reports ENOENT (i.e., the two error messages in the user log). In reported cases, only write failure alerts are observed (the old configuration is retained); if the timing is more extreme, `rename` may output an empty/half-written `config.toml` (a potential risk, not yet exploded in real environments). In single-instance scenarios, ext4 delayed allocation also has the "rename metadata before data block is written" crash window (SIGKILL / power loss). `_file_lock` is a process-level `threading.RLock`, which has no constraint on cross-process/cross-container writes.

**Affected Version**: 2.2.0-dev.0 - 2.8.0

**Fixed Version**: 2.8.1

**Fix Content**: Converge all configuration writes to `_atomic_write_text()`: use `mkstemp` in the same directory to generate a process-unique temporary file (eliminate fixed-name contention, degrade to last-writer-wins in multi-instance scenarios, no more ENOENT); write to disk with `flush + fsync` (eliminate "rename is effective, data not written" window); use `os.replace` to atomically replace the target (atomic on both POSIX/Windows, either the disk has complete old content or complete new content at any moment); additionally `fsync` the configuration directory on POSIX. Three write points (`_flush_config`, `setConfigTemplate`, root directory configuration migration) are all switched; exception path cleanup logic is restructured with the unique temporary file name. Add **multi-instance detection**: acquire an advisory lock (`flock` on POSIX / `msvcrt.locking` on Windows) to exclusively hold the configuration directory lock file `.erispulse_config.lock` at startup, output i18n warning if occupied (does not block startup), the lock is automatically released by the OS when the process exits, no ghost lock.

**Fix Date**: 2026/09/13

**Reproduction Steps**: ① Two containers mount the same host `config/` directory and run ErisPulse simultaneously; ② Any instance triggers a configuration write (such as module registration default configuration); ③ Observe the log for ENOENT write failure alerts, this write is discarded (the old configuration is retained).

**关联**: User report (1Panel container ×2)

**Regression Test**: `tests/unit/test_unit_config_atomic_write.py` (complete content write / no temporary file residue / write failure preserves original file / concurrent writes by two instances always result in valid files / lock file creation / multi-instance warning / atomic write for migration)

**Severity**: 🟢 Minor

**Type**: Configuration System

---

### [BUG-037] Space-separated command names registered as subcommands never trigger

**Problem**: After registering a subcommand with a space-separated command name (such as `@command("admin add")`), the command can be registered normally and appears in the help list, but when the user sends `/admin add`, the robot never responds—the input is matched as `admin` + parameter `["add"]` by the parent token command; if the parent token is also unregistered, there is complete no response. Only when using dot-separated naming (e.g., `admin.reload`, treated as a single token) can this be avoided.

**Cause**: Root cause chain: `CommandHandler.__call__` stores any command name (including space-separated forms) as a flat key in the `self.commands` dictionary → during distribution, `_try_execute_command` only matches the first token of the message (`cmd_name = parts[0]`) → multi-token command names as dictionary keys are never found. The registration and matching phases have inconsistent assumptions about the command name space, and there is no registration-time warning (silent failure).

**Affected Version**: From the introduction of the command system onwards - 2.8.0

**Fixed Version**: 2.8.1

**Fix Content**: The matching layer changes to **longest prefix matching**: from the longest candidate (`" ".join(parts[:n])`, n capped by the maximum number of tokens in registered command names/aliases cached in `_max_name_tokens`) try matching step by step, if matched, execute with the remaining tokens as parameters, downstream scope/ACL/overriding/master/permission chain naturally applies to the full command name. Accompanying semantics: when parent and child coexist, unregistered child command input falls back to the parent command (historical behavior unchanged); if a child command does not declare `permission`, it inherits the most recently declared ancestor command's permission (protecting the parent command protects all its child commands); only registering a single-token command hits the first round, distribution overhead is consistent with the original. `unregister` / `unregister_by_owner` / full cleanup synchronously maintains the token count cache.

**Fix Date**: 2026/09/13

**Reproduction Steps**: ① Module-level `@command("admin add")` registration; ② Send `/admin add x`; ③ Before the fix, there is no response (or is caught by the unregistered `/admin` as a parameter), after the fix `admin add` triggers and `get_command_args()` is `["x"]`.

**Regression Test**: `tests/unit/test_unit_command_subcommand.py` (longest prefix matching / only child command triggers / three-level nesting / case sensitivity two modes / single and multi-token alias / event payload full name / lifecycle hooks full name / permission inheritance six examples / ACL glob full name / master / unregistration fallback and cache recalculation)

**Severity**: 🟡 Medium

**Type**: Event System

---

### [BUG-038] persist=False runtime bindings are written to disk along with persistent writes, reviving from disk after module unloading

**Problem**: Runtime bindings written with `scope.set(path, value, persist=False)` (documented as not writing to disk, expiring after process restart, and cleared when the module is unloaded) are written to disk along with any unrelated `persist=True` write (default, such as module `set_module` / WebUI saving configuration); after the module is unloaded and the runtime binding is cleared, the binding is "revived" from disk and continues to be effective after configuration reload, remaining even after process restart—contrary to the "runtime binding does not write to disk" semantic contract, and extremely difficult to troubleshoot.

**Cause**: Root cause chain: `ScopeManager.set()` first writes the value to the memory configuration tree `_data` (runtime bindings are also directly written to `_data`) → the persistence branch makes a deep copy snapshot of the entire `_data` tree and submits it to `update_erispulse_config` for differential writing → the snapshot includes the value of the `persist=False` binding. `delete(persist=True)` is the same source: the live reference (parent node) is handed over to the delayed write dirty queue, and during the delayed write period, the live reference exists in the dirty queue, causing a cross-write contamination window.

**Affected Version**: 2.8.0-dev.2 - 2.9.0-dev.0

**Fixed Version**: 2.9.0-dev.2

**Fix Content**: Introduce a persistence baseline `_persisted_tree` (the configuration tree is refreshed from the disk-loaded, validated tree as the mirror image of the disk truth): `set(persist=True)` only applies the current change to the baseline and submits the differential for persistence, runtime bindings never enter the persistent content; "write-then-read" is changed to restore the memory final state snapshot directly, no longer through `_apply_tree` reconstruction to avoid contaminating the baseline. `delete(persist=True)` is the same口径: apply the deletion to the baseline and hand over the deep copy of the baseline subtree to the persistence layer; `set_action` overall replacement semantics first deletes according to the same口径 and then writes, old rule keys do not remain in the persistent content.

**Fix Date**: 2026/09/27

**Reproduction Steps**: ① Module-level `scope.set("bots.p.debug_mode", {"blocked": ["X"]}, persist=False)`; ② Trigger any persistent write (such as another module calling `set_module`); ③ Open `config/config.toml`, see `debug_mode` has been written (before fix); ④ After unloading the module (runtime binding is cleared), trigger configuration reload, `scope.get("bots.p.debug_mode")` still returns the bound value.

**Regression Test**: `tests/unit/test_unit_scope.py::TestPersistBaseline` (runtime binding does not go to disk with unrelated persistent write / does not revive after module unload / delete submits baseline subtree without runtime sibling keys / set_action replacement leaves no residual keys / cache_size configuration takes effect)

**Severity**: 🔴 Severe

**Type**: Configuration System

---

### [BUG-039] Reading and writing inconsistency with section write and dot write (dot overwrite lost)

**Problem**: During the delay write window, when both section write (`setConfig("Mod", {...})`, such as `BaseModule.cfg` writing back) and dot write (`setConfig("Mod.key", v)`, such as configuration hot update / test tool overwrite) coexist, there are two variants: Variant A (read path) — `getConfig("Mod")` returns the old section read from the pending snapshot, not seeing the later dot overwrites (dot read path is normal); Variant B (write path, more serious) — dot write first, section write later (test tool injects overwrite → module `self.cfg = ...` writing back is a common timing), flush applies dirty keys in insertion order, section write completely replaces the section, **dot overwrites are permanently lost on disk**. Production environment "configuration hot update + module runtime write back" combination can trigger this, unrelated to test environment (ErisPulse-DailyCard test feedback exposed).

**Cause**: `getConfig` first segment (exact match `_dirty_keys`) returns early `return self._dirty_keys[key]`, completely bypassing the fourth segment `_dirty_overlay` descendant overlay; `_flush_config` applies dirty keys in insertion order, section write (ancestor) first, dot write (descendant) later (stable sort maintains insertion order for same depth writes). Also: the return of `getConfig` for exact match `_dirty_keys` still overlays `_dirty_overlay` descendants (not dict value returns overlay subtree, consistent with ③+④ scalar edges), and the return of `getConfig` for exact match, ancestor subtree, and overlay merge is changed to `copy.deepcopy` isolation copy, no longer leaking dirty queue internal references; no dirty key fast path and pure cache read behavior unchanged.

**Affected Version**: 2.6.0 - 2.9.0-dev.2

**Fixed Version**: 2.9.0-dev.2

**Fix Content**: In the dirty window, unify **specificity priority** semantics — dot write (more specific) takes precedence over section write (wider) in both read and write paths: ① `getConfig` returns the exact match dirty key and then overlays `_dirty_overlay` descendant dirty values (non-dict value returns overlay subtree, consistent with ③+④ scalar edges); ② `_flush_config` applies dirty keys in path depth order (section/ancestor first, dot/descendant later, stable sort maintains insertion order for same depth writes). Cost: within the same dirty window (about 5 seconds), section write back cannot overwrite still pending dot write — read path fixed, read-modify-write naturally carries dot value, actual impact surface is extremely small. ③ Involved dirty value `getConfig` returns (exact match / ancestor subtree / overlay merge) changed to `copy.deepcopy` isolation copy, no longer leak dirty queue internal references; no dirty key fast path and pure cache read behavior unchanged.

**Fix Date**: 2026/09/28

**Reproduction Steps**: ① `setConfig("FB.y", 1)`; ② `setConfig("FB", {"z": 2})`; ③ `force_save()` — before fix, disk only has `[FB] z = 2` (y lost), after fix `{"y": 1, "z": 2}`; Variant A: steps ①② without saving directly `getConfig("FB")` — before fix does not contain `y`, after fix visible.

**Regression Test**: `tests/unit/test_unit_config.py::TestSectionAndDottedDirtyConsistency` (Variant A two insertion orders / Variant B flush and order irrelevant / three-level mixed survival / isolation copy / ancestor subtree isolation)

**Severity**: 🟡 Medium

**Type**: Configuration System