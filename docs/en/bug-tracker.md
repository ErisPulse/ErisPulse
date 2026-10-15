# Bug Tracker

This document records known bugs in the ErisPulse SDK and their fixes, arranged in chronological order by the version in which they were fixed.

> **For the Reader**
> No software is born perfect, and even the most careful developers leave small mistakes. This tracker only includes issues that have a practical impact on operation—those that are too minor to even qualify as "minor" are not included here. While the list of "Critical" items may seem large, the purpose of publicly documenting these bugs is to make troubleshooting and retrospective analysis smoother, not to create anxiety: problems that can be seen, recorded, and fixed are proof that the project is continuously improving. There is no need to be alarmed by this list; it is a troubleshooting tool, not a source of fear.

> **How to Read & Maintenance Conventions**
> - Each bug entry contains structured fields such as problem description, root cause analysis, affected version range, fix solution, etc. It is recommended to check the "Affected Version" before upgrading to see if it covers the version currently in use.
> - If you need to add a new bug entry, please supplement the content at the corresponding position, following the field specifications and severity/type classification below.

---

## Field Description

### Required Fields

| Field | Description |
|------|------|
| **Problem** | The external manifestation of the bug, the abnormal phenomenon observable by the user. Try to provide error messages or typical scenarios |
| **Cause** | Root cause analysis, pointing to specific code defects (including "root cause chain" diagrams for complex scenarios) |
| **Affected Version** | The affected version range, in the format `Introduced Version - Fixed Version` (including both dev versions) |
| **Fixed Version** | The specific version number in which the bug was fixed |
| **Fix Content** | A brief description of the fix, including key code changes |
| **Fix Date** | The release date of the corresponding fixed version, in `YYYY/MM/DD` format |
| **Severity** | As per the "Severity Classification" below |
| **Type** | As per the "Type Classification" below, can be combined (e.g., `Adapter / Routing`) |

### Optional Fields

| Field | Description | Applicable Scenarios |
|------|------|---------|
| **Reproduction Steps** | The minimal reproducible path to trigger the bug | Complex bugs, occasional bugs are recommended to supplement |
| **关联** | Related Issue / PR / Commit links | Supplement when there are external discussion records |
| **Regression Test** | Test cases for verifying the fix and preventing regression | Supplement when corresponding pytest cases have been written |

---

## Severity Classification

| Icon | Level | Judgment Criteria | Typical Manifestations |
|------|------|---------|---------|
| 🔴 | Critical | Causes process crash, data loss/damage, core functionality completely unusable, security vulnerabilities | OOM Kill, message cannot be sent, module cannot be loaded, hot reload fails |
| 🟡 | Medium | Function abnormality but with workaround, non-core functionality failure, occasional problems | Status judgment error, repeated trigger, cache expiration, inaccurate error message |
| 🟢 | Minor | Does not affect core functionality, only code quality or experience issues, potential risks not yet triggered | Deprecated API, dead code, missing warning logs |

---

## Type Classification

| Type | Coverage Scope |
|------|---------|
| Configuration System | `ConfigManager`, configuration read/write, configuration Schema, hot reload |
| Event System | `Event` module (command/message/notice/request/meta), event distribution, handler registration |
| Adapter | `AdapterManager`, `BaseAdapter`, account parsing, Bot status, middleware |
| Routing | `RouterManager`, HTTP/WebSocket/SSE routing, rate limiting, CORS |
| Client | `HttpClient`, `ClientWebSocket`, aiohttp wrapper |
| Storage | `StorageManager`, SQLite, SQL builder, nested keys |
| Loading System | `Loader`, `LazyModule`, `ModuleInitializer`, strict mode, module discovery |
| CLI | `epsdk` command, `init`/`run`/`install`, argument parsing, signal handling |
| Runtime | `sdk.run`/`restart`/`uninit`, lifecycle, signal, subprocess |

---

## Entry Template

When adding a new bug entry, please follow the following format:

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
**关联**: (Issue/PR links)
**Regression Test**: (Path to verification test cases)

**Severity**: 🔴 Critical | 🟡 Medium | 🟢 Minor
**Type**: Configuration System / Event System / Adapter / Routing / Client / Storage / Loading System / CLI / Runtime
```

---

## Statistics Overview

| Severity | Count |
|--------|------|
| 🔴 Critical | 16 |
| 🟡 Medium | 19 |
| 🟢 Minor | 3 |
| **Total** | **38** |

| Type | Count |
|------|------|
| Adapter | 6 |
| Configuration System | 12 |
| Event System | 7 |
| CLI | 3 |
| Storage | 3 |
| Loading System | 3 |
| Routing | 2 |
| Client | 1 |
| Runtime | 1 |

> Note: A single bug can belong to multiple types; the table above is counted by primary type.
> Note: BUG-028 / BUG-031 ID gaps (abandoned during registration, not recycled or renumbered to maintain existing numbering stability).

---

## Fixed Bugs

### [BUG-001] Event Handler Duplicates Triggering Events Multiple Times

**Problem**: When using multiple `@message` / `@notice` decorators to register handlers, the same event is triggered multiple times, causing commands to be executed multiple times and logs to be output repeatedly.

**Cause**: `BaseEventHandler` registers handlers to the adapter event bus without deduplication logic. Each decorator mounts once to the bus, causing the event distribution to be called multiple times.

**Affected Version**: 2.2.0-dev.0 - 2.2.1-dev.0

**Fixed Version**: 2.2.1-dev.0

**Fix Content**: Optimize `BaseEventHandler` to ensure each event type is registered to the adapter only once, avoiding repeated triggers.

**Fix Date**: 2025/08/18

**Severity**: 🔴 Critical

**Type**: Event System

---

### [BUG-002] Init Command Adapter Configuration Path Type Error

**Problem**: When using the `ep init` command for interactive initialization, selecting the configuration adapter results in a type error:

```
Interactive initialization failed: unsupported operand type(s) for /: 'str' and 'str'
```

**Cause**: In version 2.3.7, when adjusting the configuration file path, the method parameter type is inconsistent. `_configure_adapters_interactive_sync` receives a `str` type parameter, but internally uses the `/` operator of `Path` to concatenate paths.

**Affected Version**: 2.3.7 - 2.3.9-dev.1

**Fixed Version**: 2.3.9-dev.1

**Fix Content**: Change the parameter type of `_configure_adapters_interactive_sync` from `str` to `Path`, and pass `Path` objects directly when calling.

**Fix Date**: 2026/03/23

**Severity**: 🟡 Medium

**Type**: CLI

---

### [BUG-003] Commands Not Triggered After Restart

**Problem**: After calling `sdk.restart()`, commands registered via `@command` are not triggered, resulting in the robot not responding after sending a command.

**Cause**: After `adapter.shutdown()` clears the event bus, the `_linked_to_adapter_bus` status of `BaseEventHandler` is not reset to `False`, causing the `_process_event` method to consider it already mounted to the adapter bus and skip the re-mounting operation.

**Affected Version**: 2.2.x - 2.4.0-dev.2

**Fixed Version**: 2.4.0-dev.3

**Fix Content**: Introduce `_linked_to_adapter_bus` status tracking; after `clear_handlers()` disconnects the bus, it automatically re-mounts on the next `register()` call, adapting to shutdown/restart scenarios.

**Fix Date**: 2026/04/09

**Severity**: 🔴 Critical

**Type**: Event System

---

### [BUG-004] Lifecycle Event Handlers Not Cleared

**Problem**: After `sdk.restart()`, old lifecycle event handlers still exist and are repeatedly triggered, causing the same event to be processed multiple times.

**Cause**: The `lifecycle._handlers` dictionary was never cleared in `uninit()`, so old and new handlers coexist after restart.

**Affected Version**: 2.3.0 - 2.4.0-dev.2

**Fixed Version**: 2.4.0-dev.3

**Fix Content**: Clear `lifecycle._handlers` at the end of the `Uninitializer` cleanup process (after all events are submitted).

**Fix Date**: 2026/04/09

**Severity**: 🟡 Medium

**Type**: Runtime

---

### [BUG-005] Event.is_friend_add/is_friend_delete detail_type Inconsistent with OB12 Standard

**Problem**: `Event.is_friend_add()` checks `detail_type == "friend_add"`, `Event.is_friend_delete()` checks `detail_type == "friend_delete"`, but OneBot12 standard defines `detail_type` values as `"friend_increase"` and `"friend_decrease"`. This inconsistency with the values used in `notice.py`'s `on_friend_add`/`on_friend_remove` decorators causes handlers registered via decorators to trigger, but the corresponding `is_friend_add()`/`is_friend_delete()` judgment methods return `False`.

**Cause**: `wrapper.py` uses non-standard naming, while `notice.py` uses the correct OB12 standard naming.

**Affected Version**: Implemented to date

**Fixed Version**: 2.4.2-dev.1

**Fix Content**: Change `is_friend_add()`'s matching value from `"friend_add"` to `"friend_increase"`, and `is_friend_delete()` from `"friend_delete"` to `"friend_decrease"`.

**Fix Date**: 2026/04/13

**Severity**: 🟡 Medium

**Type**: Event System

---

### [BUG-006] adapter.clear() Does Not Clear _started_instances, Leading to Incorrect State After Restart

**Problem**: The `AdapterManager.clear()` method clears `_adapters`, `_adapter_info`, handlers, and `_bots`, but omits clearing the `_started_instances` set. If the adapter is running and `clear()` is called, `_started_instances` retains dangling references, leading to incorrect state judgment after restart.

**Cause**: When `_started_instances` was introduced in 2.4.0-dev.1, it was not cleared in `clear()`.

**Affected Version**: 2.4.0-dev.1 - 2.4.2-dev.0

**Fixed Version**: 2.4.2-dev.1

**Fix Content**: Add `self._started_instances.clear()` in the `clear()` method.

**Fix Date**: 2026/04/13

**Severity**: 🟡 Medium

**Type**: Adapter

---

### [BUG-007] command.wait_reply() Uses Deprecated asyncio.get_event_loop()

**Problem**: The `CommandHandler.wait_reply()` method uses `asyncio.get_event_loop()` to create futures and retrieve timestamps, which has been deprecated in Python 3.10+. In asynchronous contexts, `asyncio.get_running_loop()` should be used. This differs from the `get_running_loop()` used in the `wrapper.py`'s `wait_for()` method.

**Cause**: The old API was used during development, and the newly added `wait_for()` method used the correct API but did not backport the fix for the old code.

**Affected Version**: 2.3.0-dev.0

**Fixed Version**: 2.4.2-dev.1

**Fix Content**: Replace `asyncio.get_event_loop()` with `asyncio.get_running_loop()` in two places in `command.py`.

**Fix Date**: 2026/04/13

**Severity**: 🟢 Minor

**Type**: Event System

---

### [BUG-008] Bot Offline Event Repeatedly Submitted During shutdown

**Problem**: When calling `adapter.shutdown()` to close all adapters, `_update_bot_status()` repeatedly submits Bot offline events during the shutdown process, causing the same batch of Bots to be marked offline multiple times and triggering multiple `adapter.bot.offline` lifecycle events.

**Cause**: The Bot status tracking system introduced in 2.4.0-dev.1 did not set a "shutting down" flag during `shutdown()`, so `_update_bot_status()` could not distinguish between normal offline and cascading offline during the shutdown process.

**Affected Version**: 2.4.0-dev.1 - 2.4.2-dev.1

**Fixed Version**: 2.4.2-dev.1

**Fix Content**: Add `_is_being_shutdown` flag in `AdapterManager`; set it to True at the start of `shutdown()` and clear it at the end; `_update_bot_status()` skips repeated submissions during the shutdown process after checking this flag.

**Fix Date**: 2026/04/21

**Severity**: 🟡 Medium

**Type**: Adapter

---

### [BUG-009] LazyModule Synchronous Access to BaseModule Leads to Uninitialized Completion

**Problem**: When users access the properties of a lazily loaded BaseModule in a synchronous context, the module uses `loop.create_task()` for asynchronous initialization but does not wait, leading to race conditions when properties are accessed before initialization is complete.

**Cause**: `_ensure_initialized()` uses `loop.create_task(self._initialize())` and returns immediately without ensuring initialization is complete.

**Affected Version**: 2.4.0-dev.0 - 2.4.2-dev.1

**Fixed Version**: 2.4.2-dev.2

**Fix Content**: In synchronous contexts, BaseModule initialization is changed to use `asyncio.run(self._initialize())` to ensure initialization is complete before returning. The transparent proxy feature is maintained, and users do not need to perceive the difference between synchronous and asynchronous contexts.

**Fix Date**: 2026/04/21

**Severity**: 🟡 Medium

**Type**: Loading System

---

### [BUG-010] Multi-threaded Configuration Writing Causes Data Loss

**Problem**: In a multi-threaded environment, when multiple threads simultaneously call `config.setConfig()`, the `_flush_config()` read-modify-write operation is not atomic, potentially causing some writes to be lost.

**Cause**: Although `_flush_config()` uses `RLock`, there is no file lock protection between file reads and writes, and `_schedule_write`'s Timer may be triggered multiple times, causing overwrites.

**Affected Version**: 2.3.0 - 2.4.2-dev.1

**Fixed Version**: 2.4.2-dev.2

**Fix Content**:
1. Add file locking mechanism (`_file_lock`) to ensure atomic file operations
2. Use temporary files for writing and then atomically rename (`os.replace`/`os.rename`)
3. Improve `_schedule_write`'s Timer cancellation and rescheduling logic

**Fix Date**: 2026/04/21

**Severity**: 🔴 Critical

**Type**: Configuration System

---

### [BUG-011] Windows Ctrl+C Cannot Stop Program

**Problem**: When running `python main.py` directly on Windows, pressing Ctrl+C does not terminate the program. After the program starts normally and outputs the routing server information, Ctrl+C has no response, and the process can only be forcibly killed via the task manager. However, running via `epsdk run` works normally—though `epsdk run` runs via a subprocess model.

**Cause**: The Hypercorn ASGI server's `serve()` function internally registers its own SIGINT handler via `signal.signal(SIGINT, handler)`, overriding Python's default `KeyboardInterrupt` handling mechanism. When Hypercorn is started as a background task via `asyncio.create_task()`, its internal shutdown process cannot be triggered normally (because it expects the `worker_serve` mode), causing the Ctrl+C signal to be swallowed by Hypercorn without triggering any cleanup actions.

**Affected Version**: 2.3.6 - 2.4.2

**Fixed Version**: 2.4.3-dev.0

**Fix Content**:
1. Switch the ASGI server from Hypercorn to Uvicorn (`pyproject.toml` dependency change)
2. Use `uvicorn.Server._serve()` to directly start the server, **bypassing** the `capture_signals()` signal handling context manager
3. Implement graceful shutdown via `server.should_exit = True`, and cancel the background task if timeout occurs
4. Synchronously remove the subprocess running model and `runtime/cleanup.py` cleanup module (no longer needed for subprocess cleanup)

**Fix Date**: 2026/04/28

**Severity**: 🔴 Critical

**Type**: CLI / Runtime

---

### [BUG-012] Hot Restart After Module Update Does Not Take Effect

**Problem**: After executing `sdk.restart()` for a soft restart, the new code (such as new API routes) of modules/adapters upgraded via `epsdk install` does not take effect, and the old logic is still run. The process must be fully restarted to load the latest code.

**Cause**: `_do_restart()` calls `entry_point.load()` during re-initialization, but this function returns the cached old module object from `sys.modules` instead of reloading from disk.

**Affected Version**: Early versions - 2.4.3-dev.1

**Fixed Version**: 2.4.3-dev.1

**Fix Content**: Clear the cache of loaded modules/adapters in `sys.modules` before `init()` and after `uninit()`, so that `entry_point.load()` reloads the latest code from disk. Added `_collect_top_level_modules()` and `_invalidate_module_cache()` helper methods to derive top-level module names via `top_level.txt` or entry-point value.

**Fix Date**: 2026/05/03

**Severity**: 🔴 Critical

**Type**: Loading System / Runtime

---

### [BUG-013] Module Loading Strategy Sorting Logic Error

**Problem**: `ModuleLoadStrategy` provides a `priority` field to declare the initialization priority of modules, but the implementation of the loading strategy has an error, causing modules not to be initialized in the expected priority order, but rather in the default order of `entry_points()`. When modules have initialization dependencies, the correct initialization order cannot be ensured via `priority`.

**Cause**: The sorting logic in the loading strategy implementation is incorrect; `initialize_modules()` does not sort the module list by `priority`.

**Affected Version**: 2.3.4 - 2.4.5-dev.2

**Fixed Version**: 2.4.5-dev.3

**Fix Content**: Before traversing in `initialize_modules()`, sort the module list by `priority` in descending order. Modules with the same priority maintain their original relative order (stable sorting).

**Fix Date**: 2026/05/15

**Severity**: 🟡 Medium

**Type**: Loading System

---

### [BUG-014] Adapter Middleware Returning None Causes Event Data Loss

**Problem**: When `adapter.emit()` executes the OneBot12 middleware chain, if a middleware returns `None` (e.g., forgetting to `return data`), subsequent middlewares and all event handlers receive `processed_data` as `None`, causing event processing to fail completely.

**Cause**: The middleware chain implementation `processed_data = await middleware(processed_data)` does not check if the return value is `None`, directly overwriting the result of the previous step.

**Affected Version**: unknown - 2.4.5-dev.3

**Fixed Version**: 2.4.5-dev.4

**Fix Content**: If middleware returns `None`, ignore the return value, retain the original data, and output a warning-level log.

**Fix Date**: 2026/05/15

**Severity**: 🔴 Critical

**Type**: Adapter / Event System

---

### [BUG-015] Configuration File Path Depends on Working Directory

**Problem**: `ConfigManager`'s configuration file path is a relative path `"config/config.toml"` by default, resolved using `os.getcwd()` at runtime. If the working directory changes during runtime (e.g., via `os.chdir()`), configuration file read/write operations point to the wrong location, causing configuration loss or reading old data.

**Cause**: The relative path is directly stored in `__init__` without being resolved to an absolute path at initialization.

**Affected Version**: 2.3.7 - 2.4.5-dev.3

**Fixed Version**: 2.4.5-dev.4

**Fix Content**: In `ConfigManager.__init__()`, if the passed path is a relative path, automatically resolve it to an absolute path using `os.path.abspath()`.

**Fix Date**: 2026/05/15

**Severity**: 🟡 Medium

**Type**: Configuration System

---

### [BUG-016] BaseStorage Confuses Storing Value None with Key Not Existing

**Problem**: `BaseStorage.get_multi()` / `__getattr__()` cannot distinguish between "key not existing" and "key's value is `None`", so when a user explicitly stores `None`, it is treated as if the key does not exist when read again.

**Cause**: The value retrieval logic directly uses `value is None` to determine if the key exists, lacking an independent "missing" marker.

**Affected Version**: Early versions - 2.4.6-dev.6

**Fixed Version**: 2.4.6-dev.6

**Fix Content**: Introduce `_SENTINEL` sentinel value to distinguish between "key not existing" and "value is None", so they are no longer confused.

**Fix Date**: 2026/06/07

**Severity**: 🟡 Medium

**Type**: Storage

---

### [BUG-017] WebSocket Route auto_accept Flag Lost After Service Restart

**Problem**: After a service restart (such as `sdk.restart()`), the `auto_accept` configuration for all WebSocket routes becomes `False`, and connections that were expected to be automatically accepted remain pending, causing the client to receive no response for a long time, manifesting as a stuck WebSocket connection.

**Cause**: `_restore_routes_from_records()` hardcodes `auto_accept` as `False` when restoring routes from persistent records, not reading the actual value from the record; also, when the route storage tuple was expanded from a binary tuple to a ternary tuple, the restore logic was not synchronized.

**Affected Version**: 2.3.8-dev.0 - 2.4.6-dev.6

**Fixed Version**: 2.4.6-dev.6

**Fix Content**: Route storage tuples are expanded to `(handler, auth_handler, auto_accept)`, and `_restore_routes_from_records()` reads the real `auto_accept` value from the record instead of hardcoding `False`.

**Fix Date**: 2026/06/07

**Severity**: 🔴 Critical

**Type**: Routing

---

### [BUG-018] Concurrent Calls to HTTP/WS Clients Cause Crashes and Connection Leaks

**Problem**: The HTTP and WebSocket clients in `Core/client.py` have multiple stability defects in concurrent scenarios, leading to connection leaks or process crashes:
- Concurrent calls to `ClientWebSocket.receive()` with aiohttp throw `Concurrent call to receive() is not allowed`
- `_get_http_session()` / `_get_ws_session()` concurrent calls may create multiple sessions and `_drain_sessions()` does not close old connections, causing connection leaks
- `request()`'s exception handling order is incorrect: `except ClientConnectionError` (ErisPulse exception) is never triggered, aiohttp connection errors are caught by the generic `except Exception`, causing the "retry + session rebuild" logic (dead code) to never execute
- `send_json()` ignores the `mode="binary"` parameter; `get_ws_session()` does not pass default request headers

**Cause**: The client was initially implemented (2.4.6-dev.5) without concurrency protection and improper handling of aiohttp exception hierarchy and ErisPulse custom exception inheritance.

**Affected Version**: 2.4.6-dev.5 - 2.4.8

**Fixed Version**: 2.4.8

**Fix Content**:
1. Add `_recv_lock` to serialize all `receive()` / `receive_text()` / `receive_bytes()` calls
2. Add `_session_lock` to protect session creation; `_drain_sessions()` is changed to an async method and truly closes old sessions
3. Refactor `request()` exception handling order: `asyncio.TimeoutError` → `aiohttp.ClientConnectionError` (triggers session rebuild) → `aiohttp.ClientError` → `ClientError` (transparent pass) → `Exception`
4. Fix `send_json()`'s mode handling, `get_ws_session()`'s default request headers, `close()`'s concurrency race, and `HttpResponse.__aexit__`'s repeated `release()`

**Fix Date**: 2026/06/12

**Severity**: 🔴 Critical

**Type**: Client

---

### [BUG-019] Adapter Hot Reload Causes Route Conflicts and Fails to Reload

**Problem**: Third-party modules (such as Dashboard) trigger adapter hot reload, or adapter startup fails and retries, due to the previous registration of old routes (such as `onebot11_default`) not being cleared, throwing a `WebSocket path ... already registered` conflict, causing reload failure. A complete restart of the process is required to restore.

**Cause**: `AdapterManager.shutdown()` only clears routes via `unregister_all_by_namespace(platform)`, but adapters (such as OneBot11) register WebSocket routes with `onebot11_{account_name}` as the namespace, with granularity that does not match, resulting in clearing being a no-op; startup failure retry paths are also not cleared of previously residual routes.

**Affected Version**: Early versions - 2.4.9

**Fixed Version**: 2.4.9

**Fix Content**:
1. Route registration automatically tracks `owner → namespace` affiliation via `current_owner` ContextVar
2. Add `unregister_all_by_owner(owner)`, stopping/restarting with cleanup of resources bound in a single call, covering fine-grained namespaces
3. Add `_stop_adapter(platform)` primitive (stop equals cleanup), binding stopping the adapter and reclaiming its registered resources in one call, called by `restart()` and startup failure retries
4. Add framework-level `adapter.restart(platform)` API, third-party modules should call this method instead of directly operating adapter instances

**Fix Date**: 2026/06/12

**Severity**: 🔴 Critical

**Type**: Adapter / Routing

---

### [BUG-020] Subprocess Mode `ep run <script>` Cannot Find Subpackages in Script's Directory

**Problem**: When running a script using `ep r .\main.py` in non-hot-reload mode, if the script has relative imports (such as `from qg import ...`), it reports `No module named 'qg'` error. While `--reload` mode works normally.

**Cause**: Non-hot-reload mode directly calls `runpy.run_path()` to execute the script, which does not automatically add the script's directory to `sys.path`. While `--reload` mode runs via `subprocess.Popen` subprocess, the subprocess automatically inherits the current working directory, making `sys.path[0]` the script's directory, so it works.

**Affected Version**: 2.5.0 - 2.5.2-dev.0

**Fixed Version**: 2.5.2-dev.0

**Fix Content**: Before calling `runpy.run_path()`, manually insert the script's directory into `sys.path[0]`.

**Fix Date**: 2026/06/27

**Severity**: 🟡 Medium

**Type**: CLI

---

### [BUG-021] SQL Query Builder Rejects Legitimate Wildcard and List Expressions

**Problem**: `SQLiteQueryBuilder`'s `_build_select_sql()` calls `_validate_identifier()` for all SELECT columns, which uses a strict whitelist regular expression `^[a-zA-Z_][a-zA-Z0-9_]*$`, causing legitimate SQL syntax to be incorrectly judged as unsafe column names:

- `SELECT *` — `*` is a standard SQL wildcard
- `SELECT COUNT(*)` — aggregate function
- `SELECT users.name` — qualified column name
- `SELECT col AS alias` — column alias

Among them, `Select("*")` is used by modules like Cron, causing module `on_load` execution to fail and the module cannot be loaded.

**Cause**: In version 2.4.6, SQL injection protection was enhanced, introducing the `_validate_identifier()` whitelist validation. This validation is applied to all column names, but does not distinguish between read端 (SELECT/ORDER BY) and write端 (INSERT/UPDATE). SELECT columns allow complex SQL expressions and should not be restricted by simple identifier whitelists.

**Affected Version**: 2.4.6 - 2.5.2-dev.1

**Fixed Version**: 2.5.2-dev.2

**Fix Content**: Change the SELECT/ORDER BY column validation from whitelist mode to blacklist mode:
1. Add `_validate_select_column()` function, only blocking SQL injection dangerous characters (`;` `'` `"` `--` `/*` `*/` `\x00` newline)
2. Allow any valid SQL column expression (`*`, `table.*`, `table.column`, `COUNT(*)`, `col AS alias`, etc.)
3. INSERT/UPDATE column names still maintain strict whitelist validation (only allow simple identifiers)

**Fix Date**: 2026/06/29

**Severity**: 🔴 Critical

**Type**: Storage

---

### [BUG-022] _resolve_account() Account Resolution Regression (_accounts_data Not Populated)

**Problem**: After the 2.5.2 configuration system refactoring, multi-account adapters that declare `AccountConfigClass` report an error `ValueError("AccountConfigClass not declared, unable to resolve account")` when calling methods like `wait_reply`, `reply` that require sending messages. Even if the adapter correctly configures multi-account information, account resolution still fails.

**Cause**: In 2.5.2-dev.5, `_load_accounts()` (responsible for reading configuration + validation + populating `_accounts_data`) was refactored into `_ensure_accounts_exist()` (only generates configuration template), but `_resolve_account()` still checks `self._accounts_data is None`. Since `_ensure_accounts_exist()` no longer populates `_accounts_data`, this attribute remains `None`, causing `_resolve_account()` to return `(None, None)` early, and downstream calls to `_resolve_account` (such as `call_api`) receive `None`, triggering an error.

**Root Cause Chain**:
```
_load_accounts() was removed
  → __init__ no longer populates _accounts_data
    → _accounts_data is always None
      → _resolve_account() checks _accounts_data is None → return (None, None)
        → downstream calls to _resolve_account (e.g. call_api) get None
          → triggers error
```

**Affected Version**: 2.5.2-dev.5 - 2.5.2

**Fixed Version**: 2.5.3

**Fix Content**: Restore `_accounts_data` population in `BaseAdapter.__init__` after `self._ensure_accounts_exist()`:
```python
if self.AccountConfigClass is not None:
    self._ensure_accounts_exist()
    self._accounts_data = self.accounts  # Restore population, data source is real-time read accounts property
```
The `_resolve_account()` logic remains unchanged, fully backward compatible:
- Adapters that do not declare `AccountConfigClass`: `_accounts_data` remains `None` → return `(None, None)`
- Adapters that declare `AccountConfigClass`: `_accounts_data` is populated → normal resolution
- Adapters that overwrite `_load_accounts` or manually set `_accounts_data`: overwrite after `super().__init__()` call, highest priority

**Fix Date**: 2026/07/07

**Severity**: 🔴 Critical

**Type**: Adapter / Configuration System

---

### [BUG-023] Adapter Cache Not Refreshed After Account Configuration Modification, Leading to Account Resolution Failure

**Problem**: After users modify the account configuration of a multi-account adapter (such as filling in the token) via Dashboard, the adapter still uses the old cache, and calling message-sending-related methods reports `No available account (account_id=default)`. The process must be restarted for the new configuration to take effect.

**Cause**: `_accounts_data` is only read once from the configuration storage in `BaseAdapter.__init__`, and is not refreshed thereafter. `AdapterManager._run_adapter()` and `restart()` do not re-read the account configuration before calling `adapter.start()`, causing the cache to be out of sync with the actual configuration.

**Affected Version**: 2.4.6 - 2.5.4

**Fixed Version**: 2.5.4

**Fix Content**: In `AdapterManager._run_adapter()` and `restart()`, before calling `adapter.start()`, refresh `adapter._accounts_data = adapter.accounts` to ensure that the latest configuration is used each time.

**Fix Date**: 2026/07/09

**Severity**: 🔴 Critical

**Type**: Adapter / Configuration System

---

### [BUG-024] storage.set() Writing Large Numeric ID Keys Triggers OOM Kill

**Problem**: When calling `storage.set()` to write a nested key path containing a large pure number field (such as QQ group number `871684833`), the process is killed by container OOM (exit code -9), causing the service to crash and unable to recover.

**Cause**: In the recursive implementation of `_set_nested_value`, pure number fields in the nested key path are mistakenly identified as list indices by `isdigit()`, triggering `current.extend([None] * (index - len(current) + 1))`, attempting to allocate a list with hundreds of millions of elements, instantly exhausting memory.

**Root Cause Chain**:
```
Key path contains pure number field (such as group number 871684833)
  → isdigit() mistakenly identifies as array index
    → extend([None] * (871684833 - len(current) + 1))
      → attempts to allocate hundreds of millions of elements
        → memory exhausted → container OOM Kill (exit code -9)
```

**Affected Version**: 2.5.1 - 2.5.5

**Fixed Version**: 2.5.5

**Fix Content**:
1. Always use a dictionary when pre-creating intermediate layers, no longer guessing container type based on whether the next segment is a number
2. When setting the final value, only process as an index if the container itself is a list and the index is less than `STORAGE_MAX_LIST_INDEX` (10000); skip large indices safely
3. Change the recursive implementation to an iterative one, eliminating potential infinite recursion in the original code
4. Add `STORAGE_MAX_LIST_INDEX` constant to `Core/constants.py`, centrally managing the index safety limit

**Fix Date**: 2026/07/10

**Reproduction Steps**:
```python
# Writing a nested key path containing a large number field (such as QQ group number) triggers the OOM
await sdk.storage.aset("groups.871684833.name", "某群")
# → Process memory instantly surges, killed by OOM
```

**Regression Test**: 4 new regression test cases in `tests/unit/test_unit_storage.py`
- `test_nested_key_numeric_segment_as_dict_key` — precisely reproduces the OOM scenario
- `test_nested_key_numeric_segment_multiple` — multiple consecutive number fields as dictionary keys
- `test_nested_key_existing_list_index_set_within_limit` — reasonable index write to an existing list
- `test_nested_key_list_index_safety_limit` — safety limit verification for large indices

**Severity**: 🔴 Critical

**Type**: Storage

---

### [BUG-025] on_config_update Callback Not Triggered by Core Routes

**Problem**: The `on_config_update(old, new)` callback is defined in the base class (`BaseModule` / `BaseAdapter`), but the core framework does not associate it with configuration change events. As a result, when modifying configuration via the configuration management panel, it can be triggered, but when manually editing `config.toml` or calling `setConfig()` programmatically, `on_config_update` is not triggered.

**Cause**: `ConfigManager` emits `config.set` / `config.updated` lifecycle events when configuration changes, but lacks the subscription logic to forward these events to each component's `on_config_update` method.

**Root Cause Chain**:
```
Core does not subscribe to config.set / config.updated
  → Configuration change events are not forwarded
    → on_config_update is not called
      → Manual file editing / code setConfig does not trigger hot update callback
```

**Affected Version**: All versions

**Fixed Version**: 2.6.2

**Fix Content**: `ModuleManager` / `AdapterManager` register `config.set` (covering code `setConfig()` path) and `config.updated` (covering manual file editing path) event subscriptions, matching by configuration key prefix and calling the corresponding component's `on_config_update`, passing type-safe configuration objects. Also fix the issue where `_flush_config()` does not synchronize `_config_mtime` after writing the file, avoiding the framework itself writing being mistakenly judged as external modification and repeatedly triggering `config.updated`.

**Compatibility Note**: Hot configuration updates are now maintained by the framework core. Previously, the configuration management panel triggered it on its behalf, which has been removed, so the panel needs to be upgraded in sync with the framework, otherwise double triggering (core + panel each call) will occur. The `on_config_update` method signature and semantics remain unchanged, subclasses do not need to modify.

**Fix Date**: 2026/07/23

**Severity**: 🟡 Medium

**Type**: Configuration System

---

### [BUG-026] notice/request Event reply Target Inference Error

**Problem**: In group notification events (such as member joining group `group_member_increase`), calling `event.reply()` sends the message to the user's private chat who triggered the event, not to the group where the event occurred. The same applies to friend notification events, where the reply target may be confused.

**Cause**: `infer_receive_type()` directly returns the `detail_type` as the session type. For message events, this is correct (the `detail_type` values `private`/`group` are the session types), but for notice/request events, the `detail_type` is a semantic sub-type (such as `group_member_increase`, `friend_increase`), not the session type. Subsequent `convert_to_send_type()` and `get_id_field()` in the mapping table do not find this value, defaulting to `"user"` / `"user_id"`, causing the reply target to be confused.

**Root Cause Chain**:
```
notice event detail_type="group_member_increase"
  → infer_receive_type() directly returns "group_member_increase"
    → convert_to_send_type("group_member_increase") not in mapping table → default "user"
    → get_id_field("group_member_increase") not in mapping table → default "user_id"
      → target_id = event["user_id"]  ← New member private chat (not group)
```

**Affected Version**: All versions

**Fixed Version**: 2.7.0-dev.3

**Fix Content**: `infer_receive_type()` adds a judgment—only if `detail_type` is a known session type (standard type or custom type) is it directly returned; otherwise, the session type is inferred based on the ID field (`group_id` / `channel_id` / `user_id` etc.).

**Regression Test**: `tests/unit/test_unit_session_type.py` → `TestNoticeRequestTypeInference` (10 test cases)

**Fix Date**: 2026/07/29

**Severity**: 🟢 Minor

**Type**: Event System

---

### [BUG-027] Routing Rate Limiting Cleanup Task Uses Fixed Window Causing Long Window Rules to Fail

**Problem**: When routing rate limiting is configured as a long window rule (such as `100/hour`, `{"requests": 100, "window": 3600}`), the rate limiting is virtually useless—practically behaving like `100/minute` (up to about 6000 requests per hour), failing to provide the expected hourly protection.

**Cause**: `_apply_rate_limit` parses the actual `window` (maximum 3600 seconds) for each route, and the per-request check indeed uses this window; however, the background cleanup task `_cleanup_expired_rate_limits` uses a fixed constant `DEFAULT_RATE_LIMIT_WINDOW_SECS` (60 seconds) as the cleanup threshold for all routes. Thus, time stamps earlier than 60 seconds are cleared by the cleanup task, so the hour window never accumulates close to 100 records, severely weakening the rate limiting.

**Root Cause Chain**:
```
_apply_rate_limit parses window=3600 (100/hour)
  → per-request check uses 3600s retention time (correct)
  → but _cleanup_expired_rate_limits uses fixed max_window=60s to clean up
    → Time stamps earlier than 60 seconds are cleared
      → The hour window only retains records from the last 1 minute
        → 100/hour actually degrades to ~100/minute (relaxed by about 60 times)
```

**Affected Version**: 2.6.0-dev.0 - 2.7.0-dev.4

**Fixed Version**: 2.7.0-dev.5

**Fix Content**: Add `_rate_limit_windows: dict[str, int]` to record the actual window for each route; write the window when the first entry is created in `_apply_rate_limit`; `_cleanup_expired_rate_limits` cleans up by each key's own window (fallback to default if missing); maintain both dictionaries during cleanup and `stop()`; delete entries.

**Fix Date**: 2026/07/31

**Regression Test**: `tests/unit/test_unit_router.py` → `TestRateLimit::test_cleanup_respects_per_route_window`

**Severity**: 🔴 Critical

**Type**: Routing

---

### [BUG-029] Configuration Watcher Broadcasts Half-written TOML and Silently Swallows Exceptions

**Problem**: When the user manually edits `config.toml` and saves it halfway (creating a temporary syntax error), the configuration monitoring background thread detects the mtime change, reloads the configuration, but fails to load and still broadcasts an empty configuration `{}` as `config.updated`, causing adapters/modules' `on_config_update` to receive an empty configuration, mistakenly assuming all configuration items have been cleared and reverting to default values. Additionally, the watch loop silently swallows all exceptions with `except Exception: pass`, making it impossible to troubleshoot watcher failures.

**Cause**: Two overlapping defects:
1. `_load_config` overwrites `self._cache` with `{}` when TOML syntax error/permission error occurs, but the background monitoring thread `_watch_loop` and cache timeout path `_check_cache_validity` both unconditionally execute `_emit_config_updated()` after calling `_load_config()`, broadcasting the "empty cache" produced by failed loading as a real change.
2. `_watch_loop` uses `except Exception: pass` without logging any exceptions.

**Root Cause Chain**:
```
User saves halfway → TOML syntax error
  → _load_config() overwrites _cache = {}
    → _watch_loop unconditionally _emit_config_updated(new_config={})
      → Adapters/modules on_config_update receive empty configuration
        → Mistakenly assume all configurations have been cleared, revert to default values
```

**Affected Version**: 2.6.2-dev.1 - 2.7.0-dev.4

**Fixed Version**: 2.7.0-dev.5

**Fix Content**:
1. `_load_config` returns a bool; in case of TOML syntax error/permission error/other errors, it retains the last valid cache (no longer overwrites with `{}`), only records diagnostic logs, and returns `False`
2. `_watch_loop` and `_check_cache_validity` only emit `config.updated` if `_load_config()` returns `True`
3. `_watch_loop`'s `except Exception` is changed to log with warning level (new i18n key `core.config.watcher_error`, five languages synchronized)

**Fix Date**: 2026/07/31

**Regression Test**: `tests/unit/test_unit_config.py` → `test_malformed_toml_preserves_last_valid_cache`, `test_permission_denied_logs_clear_message` (updated to verify cache retention and return False)

**Severity**: 🟡 Medium

**Type**: Configuration System

---

### [BUG-030] Configuration Watcher Race Condition Causes Delayed setConfig to Silently Drop Data

**Problem**: Multiple users report that after using `config.setConfig(key, value)` (default `immediate=False`), their module configuration is not written to `config.toml`, while other modules' configurations are normal. Setting `immediate=True` (force flush) can avoid this. This manifests as configuration written during runtime is lost after the next restart, while configuration generated during startup is retained.

**Cause**: Two overlapping defects:
1. **Logical Defect**: `_watch_loop` unconditionally `_dirty_keys.clear()` when `_check_file_change()` returns `True`. However, `_check_file_change()` only uses `!=` to compare mtime, and the framework's own `_flush_config` write also changes mtime—although `_flush_config` updates `_config_mtime` after writing, the watcher thread may still observe a mtime difference between file write and mtime assignment (and on coarse-grained file systems), mistakenly judging it as "external modification" and clearing all dirty keys.
2. **Thread Defect**: `_watch_loop` operates `_write_timer`/`_dirty_keys` without holding `_lock`, creating data races with `setConfig` (holding lock to write `_dirty_keys`), `_schedule_write` (holding lock to write `_write_timer`).

**Root Cause Chain**:
```
Module A setConfig(immediate=True) → flush writes, mtime changes
  → User module setConfig(immediate=False) → enters _dirty_keys, flushes in 5s
    → Watcher loop, _check_file_change observes mtime difference from its own write
      → _dirty_keys.clear() → User module's dirty keys are silently discarded
        → Configuration missing after restart
```

**Affected Version**: 2.6.0 - 2.7.0

**Fixed Version**: 2.7.1

**Fix Content**:
1. Add `_last_self_write_mtime` field; `_flush_config` records it after writing; `_check_file_change` compares it first when mtime changes, matching indicates self-write returns `False`
2. `_watch_loop` holds `_lock` throughout; retains `_dirty_keys` for actual external modification (merge semantics), merges dirty keys with external content on next flush (dirty keys take precedence), no longer `clear()`
3. `getConfig`/`_check_cache_validity` paths are unaffected (their reload does not clear dirty keys)

**Fix Date**: 2026/08/06

**Regression Test**: `tests/unit/test_unit_config.py` → `test_self_write_not_detected_as_external`, `test_external_change_preserves_dirty_keys`, `test_flush_merges_dirty_with_external`

**Severity**: 🔴 Critical

**Type**: Configuration System

---

### [BUG-032] Reading Immediately After Writing Config Returns Old Value

**Problem**: `config.setConfig()` (default `immediate=False` delays about 5 seconds for flush) writes a dot-key, and immediately reads its **parent/ancestor node** (e.g., `set_erispulse_section("scope.actions.MyModule", {...})` followed by `get_erispulse_config()`) returns the old value, with the written sub-key "disappearing" until the flush. Scenarios involving scope configuration hot updates (such as the "write-read-write" scenario in the 2.8.0 test plugin `/t_section`) are affected.

**Cause**: `setConfig` stores dot-keys as **flat** entries in the dirty queue `_dirty_keys`, and only `getConfig`'s **exact key query** hits the dirty queue; tree path queries (e.g., `getConfig("ErisPulse.scope")`) only go through the cache tree, not overlaying dirty values—creating a read-you-write-break layer during the delay flush (`_flush_config` merges dirty keys into the cache and clears the queue) until the flush.

**Affected Version**: 2.6.0 - 2.8.0-dev.1

**Fixed Version**: 2.8.0-dev.1

**Fix Content**: `getConfig` introduces dirty overlay semantics—① exact hit on dirty key returns directly (original behavior unchanged); ② dirty key is an ancestor of the query key → take the longest dirty ancestor, parse the remaining path in its value subtree; ③ dirty key is a descendant of the query key → build an overlay subtree (`_dirty_overlay`) and deeply merge it with the cache subtree (`_deep_merge`, override priority, without modifying the original cache object). No dirty key path uses the original fast path, zero additional overhead.

**Fix Date**: 2026/09/04

**Regression Test**: `tests/unit/test_unit_config.py` → `test_get_config_overlays_dirty_descendant`, `test_get_config_overlay_merges_with_cache_siblings`, `test_get_config_overlay_new_branch`, `test_get_config_dirty_ancestor_query`, `test_get_config_dirty_exact_key_still_wins`

**Severity**: 🟡 Medium

**Type**: Configuration System

---

### [BUG-033] wait_reply Hangs and Replies Are Starved by High-Priority Handlers

**Problem**: When a module calls `wait_reply()` to wait for a user reply, if that reply message is claimed by a higher-priority event handler (`mark_processed()`), the command dispatcher sees the `_processed` flag at the entry and directly returns, so the reply matching logic at the end of the dispatcher is never executed—waiting parties receive no reply and can only wait until timeout returns `None`. Typical trigger scenario: robots using high-priority message handlers (recording/auditing/blocking types) have random failures in all dialog interactions.

**Cause**: Reply matching `_check_pending_reply` is attached to `_handle_message` at the end (only executed if command matching fails), while the `_processed` check is before it—reordering the claim check and reply match judgment. Interactive waiting is a framework-level session continuation mechanism, not a competition between handlers, and should not be affected by other handlers' claim.

**Affected Version**: 2.2.0-dev.0 - 2.8.0-dev.1

**Fixed Version**: 2.8.0-dev.2

**Fix Content**: Move reply matching judgment to the entry of `_handle_message` (before `_processed` check, only for message events): first try to complete the pending conversation, if matched, the event is marked as processed, and the subsequent checks naturally short-circuit; if not matched, continue the original command matching process. Also delegate the judgment chain to a new session manager (`Core/Event/interaction.py`), gaining the ability to cancel by affiliation and permission review.

**Fix Date**: 2026/09/08

**Regression Test**: `tests/unit/test_unit_interaction.py` (TestRegisterResolve matched/unmatched/claimed mark), `tests/unit/test_unit_event.py` (wait_reply full chain)

**Severity**: 🟡 Medium

**Type**: Event System / Command System

---

### [BUG-034] persist=False Runtime Binding Is Silently Overwritten by Any Later Configuration Write

**Problem**: `scope.set_module(..., persist=False)` writes only modify the memory `self._data`; but the scope subscribes to `config.set` / `config.updated` events, and any code writing configuration (such as a module loading its own default configuration) triggers the scope to rebuild the configuration tree from the configuration file, discarding all previous runtime bindings (reverting to default allow), with no log prompts. Scenarios dependent on runtime bindings (Dashboard "runtime-only" switches, module runtime dynamic disabling) revert in behavior after unrelated module configuration writes.

**Cause**: Root cause chain: `scope.set/delete(persist=False)` only writes to memory `_data` (Core/scope.py) → any `setConfig` triggers `config.set` event → `_on_config_updated` unconditionally `_load_config()` → `_apply_tree()` replaces `_data = {...}` in whole → runtime bindings not in the configuration file are discarded.

**Affected Version**: 2.8.0-dev.1 - 2.8.0-dev.2
**Fixed Version**: 2.8.0-dev.2
**Fix Content**: Introduce a runtime overlay layer `_runtime_overrides` (with deletion sentinel): `persist=False` writes/records are written into the overlay layer, and `_apply_tree()` rebuilds the persistent layer after the configuration file reload, keeping the runtime rules effective after any configuration write; `persist=True` writes/clears corresponding overlay records (user persistence semantics take precedence); `config.set` filters by event key precisely, `config.updated` compares new and old scope sections, only rebuilding if the scope actually changes (avoiding flushing unrelated writes); add `unregister_by_owner()` for module unloading to clean up with the owner's call. `Core.Event.overrides` has a similar issue with persist=False runtime overrides, fixed with the overlay architecture.
**Fix Date**: 2026/09/09

**Reproduction Steps**: ① `scope.set_module("testplat", blocked=["TestB"], persist=False)` → judgment False; ② Any module executes `config.setConfig("HelpModule", {...})` → triggers scope rebuild; ③ `scope.is_allowed("testplat", None, "TestB")` returns True (expected still False).
**关联**: Issue #432
**Regression Test**: `tests/unit/test_unit_scope.py::TestRuntimeOverrideSurvival` (unrelated write survives/rebuilds/replays/deletion sentinel/persistence clears/precise invalidation/owner cleanup)

**Severity**: 🟡 Medium
**Type**: Configuration System / Runtime

---

### [BUG-035] Configuration Panel Select Options and Dict Fields Rendered as [object Object]

**Problem**: In the WebUI configuration panel, select field options display `[object Object]` (such as dynamically generated color style options); dict fields (such as `stalker_mode`, `knowledge_base`, etc.) that are not declared with control types display `[object Object]` in text boxes, making them unviewable and uneditable.

**Cause**: Two independent defects: ① The framework's i18n resolver `_resolve_i18n_text` only restores dict with `i18n` key, and option labels are dynamic text without `i18n` key (only `default`), which are passed through, and the frontend `esc(label)` string coercion yields `[object Object]`; ② The Dashboard rendering branch only handles JSON textarea for array types, and dict/value falls into the plain text input branch and is converted by `String()`. Additionally, if a module declares `_schema_meta` as a regular dataclass field (missing `ClassVar` annotation), it will be treated as a configuration field in the schema, exacerbating the confusion.

**Affected Version**: 2.7.0 - 2.8.0-dev.2
**Fixed Version**: 2.8.0-dev.2
**Fix Content**: ① `_resolve_i18n_text` supports dict with only `default` key restored as text; ② Framework schema/template/default value/filling/validation five places always exclude fields with underscore prefix (misdeclaration harmless); ③ Dashboard select option label object fallback parsing (prioritize `default`), dict/table fields rendered as JSON textarea (save path as `tp=object` JSON.parse backwrite, complete round trip).
**Fix Date**: 2026/09/09

**Regression Test**: `tests/unit/test_unit_config.py::TestResolveI18nDefaultOnlyDict`, `TestSchemaUnderscoreFieldExclusion`

**Severity**: 🟡 Medium
**Type**: Configuration System

---

### [BUG-036] Configuration Write Fails Occasionally (ENOENT) When Multiple Instances Share Configuration Directory

**Problem**: In Docker deployment scenarios (multiple containers mounting the same host configuration directory), the log occasionally shows two consecutive `Failed to write configuration file ... [Errno 2] No such file or directory: '...config.toml.tmp' -> '...config.toml'`. This configuration write is discarded (the old configuration is fully preserved, no configuration loss observed), functionality is unaffected, but the alert repeatedly interferes with troubleshooting, and the pending configuration items need to wait for the next write to be written.

**Cause**: Root cause chain: `_flush_config` / `setConfigTemplate` use a **fixed-name** temporary file `config.toml.tmp` to carry new content, `write()` does not `fsync` before directly `rename()` it. Two ErisPulse instances sharing the same configuration directory may truncate the temporary file that instance A is writing, causing A to report ENOENT when renaming (i.e., the two consecutive error messages in the user log). In the reported case, only the write failure alert was observed (the old configuration was preserved); if the timing of the overlap was more extreme, `rename` could output an empty or partially written `config.toml` (a potential risk that has not yet erupted in real environments). In single-instance scenarios, ext4 delayed allocation also has a "rename metadata before data block is written" window (SIGKILL / power failure). `_file_lock` is a process-level `threading.RLock`, which has no constraint on cross-process/cross-container writes.

**Affected Version**: 2.2.0-dev.0 - 2.8.0

**Fixed Version**: 2.8.1

**Fix Content**: Configuration writes are unified to `_atomic_write_text()`: generate a unique temporary file (eliminating fixed-name competition, multiple instances degrade to last-writer-wins, no longer ENOENT) → write and `flush + fsync` force data to disk (eliminate the "rename has been effective, data not written" window) → `os.replace` atomically replace the target (POSIX/Windows are atomic, at any moment the disk has either the complete old content or the complete new content); additionally `fsync` the configuration directory on POSIX. All three write points (`_flush_config`, `setConfigTemplate`, root directory configuration migration) are switched; exception path cleanup logic is refactored with the unique temporary file name. Add **multi-instance detection**: acquire an advisory lock (POSIX `flock` / Windows `msvcrt.locking`) to exclusively hold the configuration directory lock file `.erispulse_config.lock` at startup, output an i18n alert if occupied (does not block startup), and the lock is automatically released by the OS when the process exits, with no ghost lock.

**Fix Date**: 2026/09/13

**Reproduction Steps**: ① Two containers mount the same host `config/` directory and run ErisPulse simultaneously; ② Trigger configuration write (such as module registering default configuration) in one instance; ③ Observe the log showing ENOENT write failure alert, this write is discarded (the old configuration is preserved).

**关联**: User report (1Panel container ×2)

**Regression Test**: `tests/unit/test_unit_config_atomic_write.py` (content fully written/no temporary file residue/write failure preserves original file/two instances concurrent write always legal/file lock creation/multi-instance alert/migration atomic write)

**Severity**: 🟢 Minor

**Type**: Configuration System

---

### [BUG-037] Empty Token Command Name Registration Never Triggers

**Problem**: After registering a multi-token command name with spaces (such as `@command("admin add")`), the command can be registered normally and appears in the help list, but when the user sends `/admin add`, the robot never responds—the input is matched as the parent token command with parameters `["add"]`; if the parent token is also unregistered, there is no response at all. Only when using dot-naming (e.g., `admin.reload`, as a single token) can it be avoided.

**Cause**: Root cause chain: `CommandHandler.__call__` stores any command name (including space-form) as a key in the flat `self.commands` dictionary → in the dispatch phase `_try_execute_command`, only the first message token is matched (`cmd_name = parts[0]`) → multi-token command names as dictionary keys are never found. The registration and matching phases have inconsistent assumptions about the command name space, and there is no registration-time warning (silent failure).

**Affected Version**: From the introduction of the command system to 2.8.0

**Fixed Version**: 2.8.1

**Fix Content**: The matching layer is changed to **longest prefix matching**: from the longest candidate (`.join(parts[:n])`, n capped by the maximum number of token in registered command names/aliases `_max_name_tokens`) try matching step by step, hitting triggers execution with the remaining tokens as parameters, downstream scope/ACL/overwrite/master/permission chain naturally works on the full command name. Accompanying semantics: when parent and child are registered, unregistered child commands fall back to the parent command (historical behavior unchanged); when child commands do not declare `permission`, they inherit the permission of the nearest ancestor command that declares permission (protecting the parent command protects all its child commands); only registering a single token command hits in the first round, dispatch overhead is consistent with the original. `unregister` / `unregister_by_owner` / full cleanup synchronously maintain the token count cache.

**Fix Date**: 2026/09/13

**Reproduction Steps**: ① Module registers `@command("admin add")`; ② Sends `/admin add x`; ③ Before fix, there is no response (or is caught by the unregistered `/admin` as a parameter), after fix `admin add` triggers and `get_command_args()` is `["x"]`.

**Regression Test**: `tests/unit/test_unit_command_subcommand.py` (longest prefix matching/only child command triggers/tertiary nesting/case sensitivity two modes/single and multi token alias/event payload full name/lifecycle hook full name/permission inheritance six examples/ACL glob full name/master/unregister fallback and cache recalculation)

**Severity**: 🟡 Medium

**Type**: Event System

---

### [BUG-038] persist=False Runtime Binding Is Persisted and Reproduced from Disk After Module Unload

**Problem**: Runtime bindings written with `scope.set(path, value, persist=False)` (documented promise not to persist, invalid after process restart, cleared after module unload) will be written to disk along with any unrelated `persist=True` write (default value, such as module `set_module`), and after the module is unloaded and the binding is cleared, it is "reproduced" from disk after the next configuration reload and continues to exist after process restart—contrary to the "runtime binding does not persist" semantic contract, and extremely difficult to troubleshoot.

**Cause**: Root cause chain: `ScopeManager.set()` first writes the value to the memory configuration tree `_data` (runtime binding is also directly written to `_data`), and the persistent branch makes a deep copy snapshot of the entire `_data` tree for submission to `update_erispulse_config` differential persistence, mixing the value of the `persist=False` binding into the persistent content. `delete(persist=True)` same source: the live reference (parent node) is handed over to the delayed write dirty queue, and during the delayed flush period, the cross-write contamination window exists for the live reference in the dirty queue.

**Affected Version**: 2.8.0-dev.2 - 2.9.0-dev.0

**Fixed Version**: 2.9.0-dev.2

**Fix Content**: Introduce a persistent baseline `_persisted_tree` (the configuration tree is refreshed from the disk-loaded, validated tree as the mirror of disk truth): `set(persist=True)` only applies this change to the baseline and submits the differential for persistence, never placing runtime bindings into persistent content; "read after write" is changed to directly restore from the memory final state snapshot, no longer through `_apply_tree` reconstruction to pollute the baseline. `delete(persist=True)` same口径: the deep copy of the baseline subtree is handed over to the persistent layer; `set_action` overall replacement first deletes according to the same口径 and then writes, old rule keys do not remain in persistent content.

**Fix Date**: 2026/09/27

**Reproduction Steps**: ① Module executes `scope.set("bots.p.debug_mode", {"blocked": ["X"]}, persist=False)`; ② Trigger any persistent write (such as another module calling `set_module`); ③ Open `config/config.toml`, see `debug_mode` has been written (before fix); ④ Unload the module (runtime binding is cleared) and trigger configuration reload, `scope.get("bots.p.debug_mode")` still returns the bound value.

**Regression Test**: `tests/unit/test_unit_scope.py::TestPersistBaseline` (runtime binding does not persist with unrelated persistent write / unloaded and unloaded after configuration reload not reproduced / delete submits baseline subtree without runtime siblings / set_action replacement leaves no residual key / cache_size configuration effective)

**Severity**: 🔴 Critical

**Type**: Configuration System

---

### [BUG-039] Inconsistent Read-Write with Simultaneous Whole Section Write and Dot Write (Dot Overwrite Lost)

**Problem**: During the window of delayed write, simultaneous whole section write (`setConfig("Mod", {...})`, such as `BaseModule.cfg` writing back) and dot write (`setConfig("Mod.key", v)`, such as configuration hot update / test tool overwrite) have two variants: Variant A (read path) — `getConfig("Mod")` whole section read returns the old whole section pending snapshot, not seeing the later dot overwrite (dot read path is normal); Variant B (write path, more serious) — dot write first, whole section write after (common timing of test tool injection overwrite → module `self.cfg = ...` writing back), flush applies dirty keys in insertion order, whole section write completely replaces the section, **dot overwrite is permanently lost on disk**. Production environment "configuration hot update + module runtime write back" combination can trigger, unrelated to test environment (ErisPulse-DailyCard test feedback exposed).

**Cause**: `getConfig` first segment (exact hit `_dirty_keys`) returns early `return self._dirty_keys[key]`, completely bypassing the fourth segment `_dirty_overlay` descendant overlay; `_flush_config` applies dirty keys in insertion order, whole section write happens after dot write, dot value is replaced. Also: `getConfig` returning (exact hit / ancestor subtree / overlay merge) in the dirty window is changed to `copy.deepcopy` isolated copy, no longer leaking dirty queue internal reference; no dirty key fast path and pure cache read behavior unchanged.

**Affected Version**: 2.6.0 - 2.9.0-dev.2

**Fixed Version**: 2.9.0-dev.2

**Fix Content**: Dirty window unified to **specificity priority** semantics — dot write (more specific) takes precedence over whole section write (more general), read path and flush path same口径: ① `getConfig` exact hit dirty key still overlays `_dirty_overlay` descendant dirty value (non-dict value returns overlay subtree, same口径 as ③+④ scalar edge case); ② `_flush_config` dirty keys applied in path depth order (ancestors first, descendants after, stable sort maintains insertion order within same depth). Cost: within the same dirty window (about 5 seconds) whole section write cannot cover still pending dot write — read path fixed, read-modify-write naturally carries dot value, actual impact surface extremely small. ③ involving dirty value `getConfig` returns (exact hit / ancestor subtree / overlay merge) changed to `copy.deepcopy` isolated copy, no longer leak dirty queue internal reference; no dirty key fast path and pure cache read behavior unchanged.

**Fix Date**: 2026/09/28

**Reproduction Steps**: ① `setConfig("FB.y", 1)`; ② `setConfig("FB", {"z": 2})`; ③ `force_save()` — before fix disk only has `[FB] z = 2` (y lost), after fix `{"y": 1, "z": 2}`; Variant A: steps ①② without flush directly `getConfig("FB")` — before fix does not contain `y`, after fix visible.

**Regression Test**: `tests/unit/test_unit_config.py::TestSectionAndDottedDirtyConsistency` (Variant A two insertion orders / Variant B flush and order irrelevant / three layers mixed survival / isolated copy / ancestor subtree isolation)

**Severity**: 🟡 Medium

**Type**: Configuration System

---

### [BUG-040] Command Tail Parameters of Platform Split Messages Silently Lost

**Problem**: When the platform splits a message into multiple text segments (such as `/kick` with a mention segment in between or input method segmentation), the command distribution only takes the first text segment for matching — `/艾特 @xxx 123` is parsed as an empty command `艾特` with no parameters, and a command declared with `args=` reports "missing parameter," with no trace.
**Cause**: In `command.py`, the text extraction loop takes the first `type=="text"` segment and `breaks`, discarding the remaining segments (including all non-text segments).
**Affected Version**: 2.6.0 (command distribution introduced) - 2.10.0
**Fixed Version**: 2.10.1-dev.0
**Fix Content**: Command text is changed to collect all text segments in order and concatenate them with spaces; mention/image layers no longer cause the command to fail to parse; simultaneously complete error-tolerant segment handling (message is None/string/non-dict segment no longer crashes the distributor).
**Regression Test**: tests/unit/test_unit_command_multiseg.py

**Severity**: 🟡 Medium
**Type**: Event System

---

### [BUG-041] Rejected Commands via alt_message Chain Re-run: Duplicate Replies and Permission Function Side Effects Triggered Twice

**Problem**: When the adapter's `alt_message` differs from the message segment text (such as alt containing a @text prefix), after a command is rejected by scope/ACL/master/permission, the distributor uses alt_message to re-run the entire chain — the user receives two "permission denied" replies, and custom permission functions (often with database queries/counting side effects) are called twice.
**Cause**: The rejection path `return False` and "no command matched" share the same return value, so the distributor assumes it can try alt fallback; however, the event was already claimed before rejection, and the re-run only executes the reply and permission judgment again.
**Affected Version**: 2.9.0 (governance/permission chain formed) - 2.10.0
**Fixed Version**: 2.10.1-dev.0
**Fix Content**: Text processing changed to three-state contract (unmatched/consumed/rejected) — after matching a registered command (regardless of rejection), alt fallback is not retried; only when no command is matched is alt fallback retained.
**Regression Test**: tests/unit/test_unit_command_multiseg.py::test_denied_command_not_rerun_via_alt

**Severity**: 🟡 Medium
**Type**: Event System

---

### [BUG-042] wait_reply Registered Inside Command Handler Immediately Consumed by Same Trigger Message

**Problem**: When a command handler registers `wait_reply` / registers interaction wait inside the command execution body, the wait is immediately consumed by the same command message — the first question in the interaction flow is skipped, "user reply" is actually the command text itself (wrong answer/data pollution).
**Cause**: `_handle_message` calls `interaction.resolve` twice, once at the beginning and once at the end; the second resolve at the end consumes the wait registered during command execution; cmdpass closes alt missing scenario judgment as empty string and directly releases, aggravating the problem.
**Affected Version**: 2.8.0 (interaction session system introduced) - 2.10.0
**Fixed Version**: 2.10.1-dev.0
**Fix Content**: The distribution chain converges to a single `interaction.resolve` (at the beginning), delete the second call at the end; waits are uniformly consumed by the next message.
**Regression Test**: tests/unit/test_unit_command_multiseg.py::test_wait_reply_not_consumed_by_command_trigger

**Severity**: 🟡 Medium
**Type**: Event System

---

### [BUG-043] Multiple Waitings for Same Key in select() Silently Cancel the Latter by the Former

**Problem**: When `event.select()` derives multiple expectations for the same session key (same user different pattern, multiple session expectations, etc.), the latter registration cancels the former with "conflict," and select directly throws `InteractionCancelled` instead of the documentation-pledged timeout returning `(None, None)`.
**Cause**: Each path independently calls `interaction.register`, and its mutual exclusion semantics send `REASON_CONFLICT` cancellation for the same key old wait; the comment claiming "multiple paths for the same user are independent and do not conflict" is incorrect — replicas only change user_id, the keys for the same user are completely identical.
**Affected Version**: 2.9.0 (select introduced) - 2.10.0
**Fixed Version**: 2.10.1-dev.0
**Fix Content**: select is changed to aggregate waiting — all expectations are merged into a single entry with a custom matcher (register by key set, share the same future), any path hit returns the corresponding index; multiple paths for the same key naturally coexist.
**Regression Test**: tests/unit/test_unit_command_multiseg.py::test_select_same_user_multi_branch

**Severity**: 🟡 Medium
**Type**: Event System

---

### [BUG-044] BaseConverter.at() Produces OB11 Legacy "at" Segment, Framework-wide Mention Detection Does Not Recognize

**Problem**: When the adapter uses `BaseConverter.at()` to assemble the inbound event, `must_at_bot` / `has_mention()` / `on_at_message` are all blind — the @robot command silently fails in the group.
**Cause**: `at()` produces `{"type": "at"}` (OB11 form), while all framework mention detection and construction sides (MessageBuilder/sending modifiers) are for OB12's `"mention"`, two tracks coexist with no warning.
**Affected Version**: Introduced version no earlier than 2.5.0 - 2.10.0
**Fixed Version**: 2.10.1-dev.0
**Fix Content**: `at()` changed to produce `{"type": "mention", "data": {"user_id": ...}}` (method name retained as alias, new `mention` alias added).
**Regression Test**: tests/unit/test_unit_command_multiseg.py::test_converter_at_produces_mention

**Severity**: 🟡 Medium
**Type**: Adapter

---

### [BUG-045] Interaction Primitives Permanently Timeout and Command Penetration Fails Without alt_message

**Problem**: When the adapter only fills the message segment and does not fill `alt_message`, `confirm` / `choose` / `collect` permanently wait for the user's plain text reply (such as "yes"); registered commands during the waiting period can never penetrate execution; `Event.get_text()` returns an empty string causing scaffolding examples to silently fail.
**Cause**: All these paths directly take `alt_message` strings, with no message segment fallback — the framework's "alt_message is an optional field of the adapter" contract, only segment filling is a legal form.
**Affected Version**: All interaction primitive introduction versions - 2.10.0
**Fixed Version**: 2.10.1-dev.0
**Fix Content**: Uniformly take `alt_message` first + text segment fallback `extract_text`口径 (five places of interaction primitive value/verification points, cmdpass judgment, `Event.get_text()/get_message_text()`).
**Regression Test**: tests/unit/test_unit_command_multiseg.py

**Severity**: 🟡 Medium
**Type**: Event System

---

### [BUG-046] Nested Subtable Headers of Declarative Configuration Template Drift to Top Level Table

**Problem**: When a nested dataclass declares configuration (ConfigClass with nested dataclass fields), the nested table header `[Nested]` falls on the top level of the file instead of inside the component section during the first generation of the configuration template — the adapter cannot read `cfg.嵌套字段` value; `config.full.example` also has misplaced.
**Cause**: The template generator renders relative table headers (e.g., `[Nested]`) for nested dataclasses, while TOML table header semantics are absolute paths from the root; `setConfigTemplate` old implementation moves the parsed table object into the component section, and `full.example` directly concatenates text, both paths fail to anchor the relative table header under the component path.

**Affected Version**: 2.10.0 - 2.10.1 (nested dataclass template rendering introduced with this version)
**Fixed Version**: 2.10.2-dev.0
**Fix Content**: `setConfigTemplate` precisely re-anchors table headers (e.g., `[Nested]` → `[组件名.Nested]`) based on the template's parsed sub-table path; `config.full.example` generation side changes to pass `_prefix` to directly produce absolute table headers.
**Regression Test**: tests/unit/test_unit_config.py::TestTomlclassEngineMigration::test_template_write_idempotent_and_nested_anchored

**Severity**: 🟡 Medium
**Type**: Configuration System / Adapter