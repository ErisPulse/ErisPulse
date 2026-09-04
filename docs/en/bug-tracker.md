# Bug Tracker

This document records the known bugs of the ErisPulse SDK and their repair status, arranged in chronological order by the time of repair.

> **For the Reader**
> No software is inherently perfect, and even the most careful developers leave small mistakes. This tracker only includes issues that have a real impact on operation—those that are too minor to even reach the "minor" level will not appear here. Although the list contains many items marked as "severe," the reason for publicly documenting these bugs is to make troubleshooting and tracing smoother, not to create anxiety: problems that can be seen, recorded, and fixed are proof that the project is continuously improving. There is no need to worry when viewing this list; it is a troubleshooting tool, not a source of fear.

> **How to Read & Maintenance Conventions**
> - Each bug entry contains structured fields such as problem description, root cause analysis, affected version range, repair solution, etc. It is recommended to check the "affected version" field before upgrading to see if it covers the version currently in use.
> - If you need to add a new bug entry, please supplement the content at the corresponding location, following the field specifications and severity/type classification below.

---

## Field Descriptions

### Mandatory Fields

| Field | Description |
|------|------|
| **Problem** | The external manifestation of the bug, the abnormal phenomenon observable by the user. Try to provide error messages or typical scenarios |
| **Root Cause** | Root cause analysis, pointing to specific code defects (including "root cause chain" diagrams for complex scenarios) |
| **Affected Version** | The affected version range, in the format `introduced version - fixed version` (including dev versions at both ends) |
| **Fixed Version** | The specific version number that fixed the bug |
| **Repair Content** | A brief description of the repair solution, including key code changes |
| **Repair Date** | The release date of the corresponding fixed version, in `YYYY/MM/DD` format |
| **Severity** | Marked according to the "Severity Classification" below |
| **Type** | Marked according to the "Type Classification" below, can be combined (e.g., `Adapter / Router`) |

### Optional Fields

| Field | Description | Applicable Scenarios |
|------|------|---------|
| **Reproduction Steps** | The minimal reproducible path to trigger the bug | Complex bugs, occasional bugs are recommended to supplement |
| **关联** | Related Issue / PR / Commit links | Supplement when there are external discussion records |
| **Regression Test** | Test case locations to verify repair and prevent recurrence | Supplement when corresponding pytest cases have been written |

---

## Severity Classification

| Identifier | Level | Judgment Criteria | Typical Manifestations |
|------|------|---------|---------|
| 🔴 | Severe | Causes process crash, data loss/damage, complete unavailability of core functions, security vulnerabilities | OOM Kill, inability to send messages, module loading failure, hot reload failure |
| 🟡 | Moderate | Functional abnormalities but with workaround paths, non-core function failure, occasional problems | Incorrect status judgment, repeated triggering, cache expiration, inaccurate error messages |
| 🟢 | Minor | No impact on core functions, only code quality or experience issues, potential risks not yet triggered | Deprecated API, dead code, missing warning logs |

---

## Type Classification

| Type | Coverage |
|------|---------|
| Configuration System | `ConfigManager`, configuration reading/writing, configuration Schema, hot update |
| Event System | `Event` module (command/message/notice/request/meta), event distribution, handler registration |
| Adapter | `AdapterManager`, `BaseAdapter`, account parsing, Bot status, middleware |
| Router | `RouterManager`, HTTP/WebSocket/SSE routing, rate limiting, CORS |
| Client | `HttpClient`, `ClientWebSocket`, aiohttp wrapper |
| Storage | `StorageManager`, SQLite, SQL builder, nested keys |
| Loader | `Loader`, `LazyModule`, `ModuleInitializer`, strict mode, module discovery |
| CLI | `epsdk` command, `init`/`run`/`install`, argument parsing, signal handling |
| Runtime | `sdk.run`/`restart`/`uninit`, lifecycle, signal, subprocess |

---

## Entry Template

When adding a new bug entry, follow the format below:

```markdown
### [BUG-XXX] Title

**Problem**: Problem description (error message or typical phenomenon)
**Root Cause**: Root cause analysis
**Affected Version**: Introduced version - Fixed version
**Fixed Version**: x.x.x
**Repair Content**: Repair solution
**Repair Date**: YYYY/MM/DD

<!-- Optional fields -->
**Reproduction Steps**: (Recommended for complex bugs)
**关联**: (Issue/PR link)
**Regression Test**: (Test case path)

**Severity**: 🔴 Severe | 🟡 Moderate | 🟢 Minor
**Type**: Configuration System / Event System / Adapter / Router / Client / Storage / Loader / CLI / Runtime
```

---

## Statistics Overview

| Severity | Count |
|--------|------|
| 🔴 Severe | 16 |
| 🟡 Moderate | 13 |
| 🟢 Minor | 2 |
| **Total** | **31** |

| Type | Count |
|------|------|
| Adapter | 6 |
| Configuration System | 7 |
| Event System | 5 |
| CLI | 3 |
| Storage | 3 |
| Loader | 4 |
| Router | 2 |
| Client | 1 |
| Runtime | 1 |

> Note: A single bug can belong to multiple types; the table above counts by main type.

---

## Fixed Bugs

### [BUG-001] Event handler duplicate registration causes events to be processed multiple times

**Problem**: When using multiple `@message` / `@notice` decorators to register handlers, the same event is triggered multiple times, causing commands to be executed multiple times and log outputs to repeat.

**Root Cause**: `BaseEventHandler` lacks deduplication logic when registering handlers with the adapter event bus; each decorator mounts once to the bus, causing multiple calls during event distribution.

**Affected Version**: 2.2.0-dev.0 - 2.2.1-dev.0

**Fixed Version**: 2.2.1-dev.0

**Repair Content**: Optimize `BaseEventHandler` to ensure each event type is registered with the adapter only once, avoiding repeated triggering.

**Repair Date**: 2025/08/18

**Severity**: 🔴 Severe

**Type**: Event System

---

### [BUG-002] Init command adapter configuration path type error

**Problem**: When using the `ep init` command for interactive initialization, selecting the configuration adapter results in a type error:

```
Interactive initialization failed: unsupported operand type(s) for /: 'str' and 'str'
```

**Root Cause**: When adjusting the configuration file path in version 2.3.7, the method parameter type is inconsistent. `_configure_adapters_interactive_sync` receives a `str` type parameter, but internally uses the `Path` `/` operator to concatenate paths.

**Affected Version**: 2.3.7 - 2.3.9-dev.1

**Fixed Version**: 2.3.9-dev.1

**Repair Content**: Change the parameter type of `_configure_adapters_interactive_sync` from `str` to `Path`, and pass a `Path` object directly when calling.

**Repair Date**: 2026/03/23

**Severity**: 🟡 Moderate

**Type**: CLI

---

### [BUG-003] Commands fail after restart

**Problem**: After calling `sdk.restart()`, commands registered via `@command` are not triggered, manifesting as the robot not responding after sending a command.

**Root Cause**: `adapter.shutdown()` clears the event bus, but the `_linked_to_adapter_bus` status of `BaseEventHandler` is not reset to `False`, causing the `_process_event` method to consider itself already mounted to the adapter bus and skip re-mounting.

**Affected Version**: 2.2.x - 2.4.0-dev.2

**Fixed Version**: 2.4.0-dev.3

**Repair Content**: Introduce `_linked_to_adapter_bus` status tracking; after `_clear_handlers()` disconnects the bus, the next `register()` automatically re-mounts, adapting to shutdown/restart scenarios.

**Repair Date**: 2026/04/09

**Severity**: 🔴 Severe

**Type**: Event System

---

### [BUG-004] Lifecycle event handlers not cleared

**Problem**: After `sdk.restart()`, old lifecycle event handlers remain and trigger repeatedly, causing the same event to be processed multiple times.

**Root Cause**: The `lifecycle._handlers` dictionary is never cleared in `uninit()`, so old and new handlers coexist after restart.

**Affected Version**: 2.3.0 - 2.4.0-dev.2

**Fixed Version**: 2.4.0-dev.3

**Repair Content**: Clear `lifecycle._handlers` at the end of the `Uninitializer` cleanup process (after all events are submitted).

**Repair Date**: 2026/04/09

**Severity**: 🟡 Moderate

**Type**: Runtime

---

### [BUG-005] Event.is_friend_add/is_friend_delete detail_type inconsistent with OB12 standard

**Problem**: `Event.is_friend_add()` checks `detail_type == "friend_add"`, `Event.is_friend_delete()` checks `detail_type == "friend_delete"`, but OneBot12 standard defines `detail_type` values as `"friend_increase"` and `"friend_decrease"`. Inconsistent with the values used in `notice.py`'s `on_friend_add`/`on_friend_remove` decorators, causing handlers registered via decorators to trigger, but corresponding `is_friend_add()`/`is_friend_delete()` judgment methods return `False`.

**Root Cause**: `wrapper.py` uses non-standard naming, while `notice.py` uses correct OB12 standard naming.

**Affected Version**: Implemented to date

**Fixed Version**: 2.4.2-dev.1

**Repair Content**: Change `is_friend_add()` match value from `"friend_add"` to `"friend_increase"`, `is_friend_delete()` from `"friend_delete"` to `"friend_decrease"`.

**Repair Date**: 2026/04/13

**Severity**: 🟡 Moderate

**Type**: Event System

---

### [BUG-006] adapter.clear() does not clear _started_instances causing incorrect status after restart

**Problem**: The `AdapterManager.clear()` method clears `_adapters`, `_adapter_info`, handlers, and `_bots`, but omits clearing `_started_instances`. If `clear()` is called while the adapter is running, `_started_instances` retains dangling references, causing incorrect status judgment after restart.

**Root Cause**: When `_started_instances` was introduced in 2.4.0-dev.1, it was not cleared synchronously in `clear()`.

**Affected Version**: 2.4.0-dev.1 - 2.4.2-dev.0

**Fixed Version**: 2.4.2-dev.1

**Repair Content**: Add `self._started_instances.clear()` in the `clear()` method.

**Repair Date**: 2026/04/13

**Severity**: 🟡 Moderate

**Type**: Adapter

---

### [BUG-007] command.wait_reply() uses deprecated asyncio.get_event_loop()

**Problem**: The `CommandHandler.wait_reply()` method uses `asyncio.get_event_loop()` to create futures and retrieve timestamps. This method has been deprecated in Python 3.10+, and in asynchronous contexts, `asyncio.get_running_loop()` should be used. This is inconsistent with `wrapper.py`'s `wait_for()` method, which uses `get_running_loop()`.

**Root Cause**: The development used the old API, and the newly added `wait_for()` method used the correct API but did not retroactively fix the old code.

**Affected Version**: 2.3.0-dev.0

**Fixed Version**: 2.4.2-dev.1

**Repair Content**: Replace `asyncio.get_event_loop()` in `command.py` with `asyncio.get_running_loop()` in two places.

**Repair Date**: 2026/04/13

**Severity**: 🟢 Minor

**Type**: Event System

---

### [BUG-008] Bot offline events are repeatedly submitted during shutdown

**Problem**: When calling `adapter.shutdown()` to shut down all adapters, `_update_bot_status()` repeatedly submits Bot offline events during the shutdown process, causing the same batch of Bots to be marked offline multiple times and triggering multiple `adapter.bot.offline` lifecycle events.

**Root Cause**: The Bot status tracking system introduced in 2.4.0-dev.1 did not set a "shutting down" flag during `shutdown()`, so `_update_bot_status()` could not distinguish between normal offline and cascading offline during shutdown.

**Affected Version**: 2.4.0-dev.1 - 2.4.2-dev.1

**Fixed Version**: 2.4.2-dev.1

**Repair Content**: Add `_is_being_shutdown` flag in `AdapterManager`; set it to True at the start of `shutdown()` and clear it at the end; `_update_bot_status()` skips repeated submissions during shutdown after checking this flag.

**Repair Date**: 2026/04/21

**Severity**: 🟡 Moderate

**Type**: Adapter

---

### [BUG-009] LazyModule synchronous access to BaseModule causes incomplete initialization

**Problem**: When users access the attributes of a lazily loaded BaseModule in a synchronous context, the module uses `loop.create_task()` for asynchronous initialization but does not wait, causing initialization to possibly not complete before attribute access, leading to race conditions.

**Root Cause**: `_ensure_initialized()` uses `loop.create_task(self._initialize())` and returns immediately without ensuring initialization completion.

**Affected Version**: 2.4.0-dev.0 - 2.4.2-dev.1

**Fixed Version**: 2.4.2-dev.2

**Repair Content**: In synchronous contexts, BaseModule initialization is changed to use `asyncio.run(self._initialize())` to ensure initialization completion before returning. The transparent proxy feature is maintained, and users do not need to perceive the difference between synchronous and asynchronous contexts.

**Repair Date**: 2026/04/21

**Severity**: 🟡 Moderate

**Type**: Loader

---

### [BUG-010] Multi-threaded configuration system writing leads to data loss

**Problem**: In a multi-threaded environment, when multiple threads simultaneously call `config.setConfig()`, the `_flush_config()` read-modify-write operation is not atomic, potentially causing partial write loss.

**Root Cause**: Although `_flush_config()` uses `RLock`, there is no file lock protection between file read and write, and the `_schedule_write` Timer may be triggered multiple times, causing overwrite.

**Affected Version**: 2.3.0 - 2.4.2-dev.1

**Fixed Version**: 2.4.2-dev.2

**Repair Content**:
1. Add file locking mechanism (`_file_lock`) to ensure atomic file operations
2. Use temporary file writing followed by atomic rename (`os.replace`/`os.rename`)
3. Improve `_schedule_write` Timer cancellation and rescheduling logic

**Repair Date**: 2026/04/21

**Severity**: 🔴 Severe

**Type**: Configuration System

---

### [BUG-011] Windows Ctrl+C cannot stop the program

**Problem**: When running `python main.py` directly on Windows, pressing Ctrl+C does not terminate the program. After the program starts normally and outputs the routing server information, Ctrl+C has no response, and the process can only be forcibly killed via the task manager. However, it can be stopped normally when started via `epsdk run`, but `epsdk run` uses a subprocess model.

**Root Cause**: The Hypercorn ASGI server's `serve()` function internally registers its own SIGINT handler via `signal.signal(SIGINT, handler)`, overriding Python's default `KeyboardInterrupt` handling mechanism. When Hypercorn is started as a background task via `asyncio.create_task()`, its internal shutdown process cannot be triggered normally (because it expects the `worker_serve` mode), causing the Ctrl+C signal to be swallowed by Hypercorn without triggering any cleanup actions.

**Affected Version**: 2.3.6 - 2.4.2

**Fixed Version**: 2.4.3-dev.0

**Repair Content**:
1. Switch the ASGI server from Hypercorn to Uvicorn (`pyproject.toml` dependency change)
2. Start the server directly using `uvicorn.Server._serve()`, **bypassing** the `capture_signals()` signal handling context manager
3. Implement graceful shutdown via `server.should_exit = True`, canceling the background task on timeout
4. Synchronously remove the subprocess running model and `runtime/cleanup.py` cleanup module (subprocess cleanup mechanism is no longer needed)

**Repair Date**: 2026/04/28

**Severity**: 🔴 Severe

**Type**: CLI / Runtime

---

### [BUG-012] Updated module Python code does not take effect after hot restart

**Problem**: After executing `sdk.restart()` soft restart, the new code (such as new API routes) of modules/adapters upgraded via `epsdk install` does not take effect, and old logic is still running. The latest code must be loaded by completely restarting the process.

**Root Cause**: `_do_restart()` calls `entry_point.load()` during re-initialization, but the function returns cached old module objects from `sys.modules` instead of reloading from disk.

**Affected Version**: Early versions - 2.4.3-dev.1

**Fixed Version**: 2.4.3-dev.1

**Repair Content**: Clear the cache of loaded modules/adapters in `sys.modules` before `init()` after `uninit()`, so that `entry_point.load()` loads the latest code from disk. Add `_collect_top_level_modules()` and `_invalidate_module_cache()` helper methods, deriving top-level module names via `top_level.txt` or entry-point value.

**Repair Date**: 2026/05/03

**Severity**: 🔴 Severe

**Type**: Loader / Runtime

---

### [BUG-013] Module loading strategy sort logic error

**Problem**: `ModuleLoadStrategy` provides a `priority` field to declare module initialization priority, but the implementation of the loading strategy has an error, causing modules to be initialized in an unexpected order, actually loaded in the default order of `entry_points()`. When modules have loading dependencies, they cannot ensure the correct initialization order via `priority`.

**Root Cause**: The implementation of the loading strategy has a sorting logic error; `initialize_modules()` does not sort the module list by `priority`.

**Affected Version**: 2.3.4 - 2.4.5-dev.2

**Fixed Version**: 2.4.5-dev.3

**Repair Content**: Before `initialize_modules()` iteration, sort the module list by `priority` in descending order. Modules with the same priority maintain their original relative order (stable sort).

**Repair Date**: 2026/05/15

**Severity**: 🟡 Moderate

**Type**: Loader

---

### [BUG-014] Adapter middleware returning None causes event data loss

**Problem**: When `adapter.emit()` executes the OneBot12 middleware chain, if a middleware returns `None` (e.g., forgetting to `return data`), subsequent middleware and all event handlers receive `processed_data` as `None`, causing event processing to fail completely.

**Root Cause**: The middleware chain implementation `processed_data = await middleware(processed_data)` does not check if the return value is `None`, directly overwriting the previous processing result.

**Affected Version**: unknown - 2.4.5-dev.3

**Fixed Version**: 2.4.5-dev.4

**Repair Content**: When middleware returns `None`, ignore the return value, retain the original data, and output a warning-level log.

**Repair Date**: 2026/05/15

**Severity**: 🔴 Severe

**Type**: Adapter / Event System

---

### [BUG-015] Configuration file path depends on working directory

**Problem**: The `ConfigManager`'s configuration file path defaults to the relative path `"config/config.toml"`, which depends on `os.getcwd()` at runtime. If the working directory changes during runtime (e.g., via `os.chdir()`), configuration file read/write operations point to the wrong location, causing configuration loss or reading old data.

**Root Cause**: In `__init__`, the relative path is directly stored without resolving it to an absolute path at initialization.

**Affected Version**: 2.3.7 - 2.4.5-dev.3

**Fixed Version**: 2.4.5-dev.4

**Repair Content**: In `ConfigManager.__init__()`, if the passed path is relative, automatically resolve it to an absolute path via `os.path.abspath()`.

**Repair Date**: 2026/05/15

**Severity**: 🟡 Moderate

**Type**: Configuration System

---

### [BUG-016] BaseStorage confuses storing value None with key not existing

**Problem**: `BaseStorage.get_multi()` / `__getattr__()` cannot distinguish between "key not existing" and "key's value is None", treating a user explicitly stored `None` as if the key does not exist.

**Root Cause**: The value retrieval logic directly uses `value is None` to check if the key exists, lacking an independent "missing" marker.

**Affected Version**: Early versions - 2.4.6-dev.6

**Fixed Version**: 2.4.6-dev.6

**Repair Content**: Introduce `_SENTINEL` sentinel value to distinguish "key not existing" from "value is None", no longer confusing the two.

**Repair Date**: 2026/06/07

**Severity**: 🟡 Moderate

**Type**: Storage

---

### [BUG-017] WebSocket route auto_accept flag lost after service restart

**Problem**: After service restart (e.g., `sdk.restart()`), all WebSocket route `auto_accept` configurations revert to `False`. Previously expected auto-accept connections become suspended, and clients receive no response for a long time, manifesting as WS connections hanging.

**Root Cause**: `_restore_routes_from_records()` hardcodes `auto_accept` as `False` when restoring routes from persistent records, not reading the original record's value; simultaneously, the route storage tuple extended to a three-tuple was not synchronized with the restoration logic.

**Affected Version**: 2.3.8-dev.0 - 2.4.6-dev.6

**Fixed Version**: 2.4.6-dev.6

**Repair Content**: The route storage tuple is extended to `(handler, auth_handler, auto_accept)`, and `_restore_routes_from_records()` reads the real `auto_accept` value from the record instead of hardcoding `False`.

**Repair Date**: 2026/06/07

**Severity**: 🔴 Severe

**Type**: Router

---

### [BUG-018] HTTP/WS client concurrent calls lead to crashes and connection leaks

**Problem**: The HTTP and WebSocket clients in `Core/client.py` have multiple stability defects in concurrent scenarios, leading to connection leaks or process crashes:
- Concurrent calls to `ClientWebSocket.receive()` by multiple coroutines cause aiohttp to throw `Concurrent call to receive() is not allowed`
- Concurrent calls to `_get_http_session()` / `_get_ws_session()` may create multiple sessions, and `_drain_sessions()` does not close old connections, causing connection leaks
- The exception handling order in `request()` is incorrect: `except ClientConnectionError` (ErisPulse exception) is never triggered, aiohttp connection errors are caught by the generic `except Exception`, causing the "retry connection + session recreation" logic (dead code) to never execute
- `send_json()` ignores the `mode="binary"` parameter; `_get_ws_session()` does not pass default request headers

**Root Cause**: The initial client implementation (2.4.6-dev.5) lacked concurrency protection and exception classification, improperly handling aiohttp exception hierarchy and ErisPulse custom exception inheritance relationships.

**Affected Version**: 2.4.6-dev.5 - 2.4.8

**Fixed Version**: 2.4.8

**Repair Content**:
1. Add `_recv_lock` to serialize all `receive()` / `receive_text()` / `receive_bytes()` calls
2. Add `_session_lock` to protect session creation; `_drain_sessions()` is changed to an asynchronous method and truly closes old sessions
3. Refactor `request()` exception handling order: `asyncio.TimeoutError` → `aiohttp.ClientConnectionError` (triggers session recreation) → `aiohttp.ClientError` → `ClientError` (transparent) → `Exception`
4. Fix `send_json()` mode handling, pass default request headers in `_get_ws_session()`, fix `close()` concurrency race, and fix `HttpResponse.__aexit__` duplicate `release()`

**Repair Date**: 2026/06/12

**Severity**: 🔴 Severe

**Type**: Client

---

### [BUG-019] Adapter hot reload causes route conflicts leading to reload failure

**Problem**: When a third-party module (such as Dashboard) triggers adapter hot reload, or when adapter startup fails and retries, old routes (such as `onebot11_default`) are not cleared, causing `WebSocket path ... already registered` conflicts, leading to reload failure. A complete process restart is required to recover.

**Root Cause**: `AdapterManager.shutdown()` only clears routes via `unregister_all_by_namespace(platform)`, but adapters (such as OneBot11) register WebSocket routes using `onebot11_{account_name}` as the namespace, resulting in a granularity mismatch that makes cleanup a no-op; route cleanup is also not performed for failed startup retries.

**Affected Version**: Early versions - 2.4.9

**Fixed Version**: 2.4.9

**Repair Content**:
1. Automatically track `owner → namespace` relationships during route registration via `current_owner` ContextVar
2. Add `unregister_all_by_owner(owner)`, stopping/restarting with cleanup of its registered resources bound in a single call, `restart()` and startup failure retries both use this entry
3. Add framework-level `adapter.restart(platform)` API, third-party modules should call this method instead of directly operating adapter instances

**Repair Date**: 2026/06/12

**Severity**: 🔴 Severe

**Type**: Adapter / Router

---

### [BUG-020] Subprocess mode `ep run <script>` cannot find sub-packages in script's directory

**Problem**: When running a script non-hot-reload mode via `ep r .\main.py`, if the script has relative imports (such as `from qg import ...`), it reports `No module named 'qg'`. The `--reload` mode works normally.

**Root Cause**: Non-hot-reload mode directly calls `runpy.run_path()` to execute the script, which does not automatically add the script's directory to `sys.path`. The `--reload` mode runs via `subprocess.Popen` subprocess, which automatically inherits the current working directory, so `sys.path[0]` is the script's directory, allowing normal operation.

**Affected Version**: 2.5.0 - 2.5.2-dev.0

**Fixed Version**: 2.5.2-dev.0

**Repair Content**: Before calling `runpy.run_path()`, manually insert the script's directory into `sys.path[0]`.

**Repair Date**: 2026/06/27

**Severity**: 🟡 Moderate

**Type**: CLI

---

### [BUG-021] SQL query builder rejects valid wildcard and list expressions

**Problem**: `SQLiteQueryBuilder`'s `_build_select_sql()` validates all SELECT columns via `_validate_identifier()`, which uses a strict whitelist regex `^[a-zA-Z_][a-zA-Z0-9_]*$`, causing legitimate SQL syntax to be incorrectly judged as unsafe column names:

- `SELECT *` — `*` is a standard SQL wildcard
- `SELECT COUNT(*)` — aggregate function
- `SELECT users.name` — qualified column name
- `SELECT col AS alias` — column alias

Among them, `Select("*")` is used by Cron and other modules, causing module `on_load` execution to fail and the module cannot be loaded.

**Root Cause**: In 2.4.6, SQL injection protection was enhanced, introducing `_validate_identifier()` whitelist validation. This validation is applied to all column names but does not distinguish between read端 (SELECT/ORDER BY) and write端 (INSERT/UPDATE). SELECT columns allow complex SQL expressions and should not be restricted by simple identifier white lists.

**Affected Version**: 2.4.6 - 2.5.2-dev.1

**Fixed Version**: 2.5.2-dev.2

**Repair Content**: Change SELECT/ORDER BY column validation from whitelist mode to blacklist mode:
1. Add `_validate_select_column()` function, only blocking SQL injection dangerous characters (`;` `'` `"` `--` `/*` `*/` `\x00` newline)
2. Allow any valid SQL column expressions (`*`, `table.*`, `table.column`, `COUNT(*)`, `col AS alias`, etc.)
3. INSERT/UPDATE column names still maintain strict whitelist validation (only allow simple identifiers)

**Repair Date**: 2026/06/29

**Severity**: 🔴 Severe

**Type**: Storage

---

### [BUG-022] _resolve_account() account resolution regression (_accounts_data not filled)

**Problem**: After the 2.5.2 configuration system refactoring, multi-account adapters declaring `AccountConfigClass` report an error `ValueError("AccountConfigClass not declared, cannot resolve account")` when calling `wait_reply`, `reply` and other methods that need to send messages. Even if the adapter correctly configures multi-account information, account resolution still fails.

**Root Cause**: In 2.5.2-dev.5, `_load_accounts()` (responsible for reading configuration + validation + filling `_accounts_data`) was refactored into `_ensure_accounts_exist()` (only generates configuration template), but `_resolve_account()` still checks `self._accounts_data is None`. Since `_ensure_accounts_exist()` no longer fills `_accounts_data`, this attribute remains `None`, causing `_resolve_account()` to prematurely return `(None, None)`, and account resolution fails completely.

**Root Cause Chain**:
```
_load_accounts() is deleted
  → __init__ no longer fills _accounts_data
    → _accounts_data is always None
      → _resolve_account() checks _accounts_data is None → return (None, None)
        → downstream places calling _resolve_account() (e.g., call_api) get None
          → trigger error
```

**Affected Version**: 2.5.2-dev.5 - 2.5.2

**Fixed Version**: 2.5.3

**Repair Content**: In `BaseAdapter.__init__`, after `_ensure_accounts_exist()`, restore the filling of `_accounts_data`:
```python
if self.AccountConfigClass is not None:
    self._ensure_accounts_exist()
    self._accounts_data = self.accounts  # Restore filling, data source is real-time read accounts attribute
```
The `_resolve_account()` logic remains unchanged, fully backward compatible:
- Adapters that do not declare `AccountConfigClass`: `_accounts_data` remains `None` → return `(None, None)`
- Adapters that declare `AccountConfigClass`: `_accounts_data` is filled → normal resolution
- Adapters that override `_load_accounts` or manually set `_accounts_data`: overwrite after `super().__init__()` call, highest priority

**Repair Date**: 2026/07/07

**Severity**: 🔴 Severe

**Type**: Adapter / Configuration System

---

### [BUG-023] Cache not refreshed after account configuration modification leads to account resolution failure

**Problem**: After users modify the multi-account adapter's account configuration (such as filling in token) via Dashboard, the adapter still uses the old cache, and calling message-sending-related methods reports `No available account (account_id=default)`. A process restart is required to make the new configuration effective.

**Root Cause**: `_accounts_data` is only read from the configuration storage once during `BaseAdapter.__init__`, and is not refreshed afterwards. `AdapterManager._run_adapter()` and `restart()` do not re-read the account configuration before calling `adapter.start()`, causing the cache to be out of sync with the actual configuration.

**Affected Version**: 2.4.6 - 2.5.4

**Fixed Version**: 2.5.4

**Repair Content**: In `AdapterManager._run_adapter()` and `restart()`, before calling `adapter.start()`, refresh `adapter._accounts_data = adapter.accounts` to ensure that the latest configuration is used each time it starts.

**Repair Date**: 2026/07/09

**Severity**: 🔴 Severe

**Type**: Adapter / Configuration System

---

### [BUG-024] storage.set() writing large numeric key triggers OOM Kill

**Problem**: Calling `storage.set()` to write a nested key path containing a large pure numeric field (such as QQ group number `871684833`) causes the process to be killed by container OOM (exit code -9), crashing the service and making it impossible to recover.

**Root Cause**: In the recursive implementation of `_set_nested_value`, pure numeric fields in the nested key path are mistakenly identified as list indices by `isdigit()`, triggering `current.extend([None] * (index - len(current) + 1))`, attempting to allocate hundreds of millions of elements, instantly exhausting memory.

**Root Cause Chain**:
```
Key path contains pure numeric field (such as group number 871684833)
  → isdigit() mistakenly identifies as array index
    → extend([None] * (871684833 - len(current) + 1))
      → attempts to allocate hundreds of millions of elements
        → memory exhausted → container OOM Kill (exit code -9)
```

**Affected Version**: 2.5.1 - 2.5.5

**Fixed Version**: 2.5.5

**Repair Content**:
1. Always use a dictionary when pre-creating intermediate layers, never guess the container type based on whether the next segment is a number
2. Only handle indexing when the container itself is a list and the index is less than `STORAGE_MAX_LIST_INDEX` (10000), safely skip large indices
3. Change the recursive implementation to an iterative one, eliminating the potential infinite recursion risk in the original code
4. Add `STORAGE_MAX_LIST_INDEX` constant to `Core/constants.py`, centrally managing the index safety limit

**Repair Date**: 2026/07/10

**Reproduction Steps**:
```python
# Writing a nested key path containing a large number field (such as QQ group number) triggers the OOM scenario
await sdk.storage.aset("groups.871684833.name", "Some group")
# → Process memory surges instantly, killed by OOM
```

**Regression Tests**: `tests/unit/test_unit_storage.py` adds 4 regression test cases
- `test_nested_key_numeric_segment_as_dict_key` — precisely reproduces the OOM scenario
- `test_nested_key_numeric_segment_multiple` — multiple consecutive numeric fields as dictionary keys
- `test_nested_key_existing_list_index_set_within_limit` — existing list index write within limit
- `test_nested_key_list_index_safety_limit` — safety limit verification for large indices

**Severity**: 🔴 Severe

**Type**: Storage

---

### [BUG-025] on_config_update callback not called by core routes

**Problem**: The `on_config_update(old, new)` callback is defined in the base class (`BaseModule` / `BaseAdapter`), but the framework core does not associate it with configuration change events. The actual manifestation: when modifying configuration via the configuration management panel, it can be triggered, but manual editing of `config.toml` or code calling `setConfig()` does not trigger `on_config_update`.

**Root Cause**: `ConfigManager` emits `config.set` / `config.updated` lifecycle events when configuration changes, but lacks logic to forward these events to each component's `on_config_update` method.

**Root Cause Chain**:
```
Core does not subscribe to config.set / config.updated
  → Configuration change events have no forwarding
    → on_config_update is not called
      → Manual file edit / code setConfig does not trigger hot update callback
```

**Affected Version**: All versions

**Fixed Version**: 2.6.2

**Repair Content**: `ModuleManager` / `AdapterManager` register `config.set` (covering code `setConfig()` path) and `config.updated` (covering manual file edit path) event subscriptions, match by configuration key prefix and call the corresponding component's `on_config_update`, passing type-safe configuration objects. Also fix `_flush_config()` writing file without synchronizing `_config_mtime`, avoiding the framework's own writing being misjudged as external modification by file monitoring task and repeatedly triggering `config.updated`.

**Compatibility Note**: Configuration hot update is now centrally maintained by the framework core. The logic previously handled by the configuration management panel has been removed, and after upgrading the framework, the configuration management panel must also be upgraded, otherwise double triggering (core + panel each call) will occur. The `on_config_update` method signature and semantics remain unchanged, subclasses do not need modification.

**Repair Date**: 2026/07/23

**Severity**: 🟡 Moderate

**Type**: Configuration System

---

### [BUG-026] notice/request event reply target inference error

**Problem**: In group notice events (such as member joining group `group_member_increase`), calling `event.reply()` sends the message to the user who triggered the event's private chat, not to the group where the event occurred. The same applies to friend notice events, where the reply target may be wrong.

**Root Cause**: `infer_receive_type()` directly returns the event's `detail_type` as the session type. For message events, this is correct (the `detail_type` values `private`/`group` are the session types), but for notice/request events, the `detail_type` is a semantic subtype (such as `group_member_increase`, `friend_increase`), not the session type. Subsequent `convert_to_send_type()` and `get_id_field()` in the mapping table do not find the value, defaulting to `"user"` / `"user_id"`, causing the reply target to be wrong.

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

**Repair Content**: `infer_receive_type()` adds a check—`detail_type` is only returned directly if it is a known session type (standard type or custom type); otherwise, the session type is inferred based on the ID field (`group_id` / `channel_id` / `user_id`, etc.).

**Regression Tests**: `tests/unit/test_unit_session_type.py` → `TestNoticeRequestTypeInference` (10 cases)

**Repair Date**: 2026/07/29

**Severity**: 🟢 Minor

**Type**: Event System

---

### [BUG-027] Route rate limiting cleanup task uses fixed window causing long window rate limiting rules to fail

**Problem**: When routing rate limiting is configured as a long window rule (such as `100/hour`, `{"requests": 100, "window": 3600}`), rate limiting is ineffective—actually behaving like `100/minute` (up to about 6000 requests per hour), completely failing to provide the intended hourly protection.

**Root Cause**: `_apply_rate_limit` parses the actual `window` (up to 3600 seconds) for each route, and per-request checks use this window; however, the background cleanup task `_cleanup_expired_rate_limits` uses a fixed constant `DEFAULT_RATE_LIMIT_WINDOW_SECS` (60 seconds) as the unified cleanup threshold for all routes. Thus, time stamps earlier than 60 seconds in the `100/hour` route are cleared early by the cleanup task, and the hour window never accumulates close to 100 records, severely weakening the rate limiting.

**Root Cause Chain**:
```
_apply_rate_limit parses window=3600 (100/hour)
  → per-request check uses 3600s retention time (correct)
  → but _cleanup_expired_rate_limits uses fixed max_window=60s to clean up
    → time stamps earlier than 60 seconds are all cleared
      → the hour window only keeps records from the last 1 minute
        → 100/hour actually degrades to ~100/minute (relaxed by about 60 times)
```

**Affected Version**: 2.6.0-dev.0 - 2.7.0-dev.4

**Fixed Version**: 2.7.0-dev.5

**Repair Content**: Add `_rate_limit_windows: dict[str, int]` to record each route's actual window by store key; `_apply_rate_limit` writes the window when creating an entry for the first time; `_cleanup_expired_rate_limits` changes to clean up by each key's own window (fallback to default value if missing); cleanup deletion and `stop()` synchronize maintenance of both dictionaries.

**Repair Date**: 2026/07/31

**Regression Tests**: `tests/unit/test_unit_router.py` → `TestRateLimit::test_cleanup_respects_per_route_window`

**Severity**: 🔴 Severe

**Type**: Router

---

### [BUG-029] Configuration listener task broadcasts incomplete TOML and silently swallows exceptions

**Problem**: When the user manually edits `config.toml` and saves halfway (producing a temporary syntax error), the configuration listener background thread detects the mtime change, reloads the configuration, but fails to load and still broadcasts an empty configuration `{}` via the `config.updated` event, causing adapters/modules' `on_config_update` to receive an empty configuration, mistakenly assuming all configuration items have been cleared and reverting to default values. Additionally, the listener loop uses `except Exception: pass` to silently swallow all exceptions, making it impossible to diagnose watcher failures.

**Root Cause**: Two defects overlap:
1. `_load_config` overwrites `self._cache` as `{}` when TOML syntax error/permission error occurs, but the background listener thread `_watch_loop` and cache timeout path `_check_cache_validity` both unconditionally execute `_emit_config_updated()` after calling `_load_config()`, broadcasting the "empty cache produced by failed load" as a real change.
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

**Repair Content**:
1. `_load_config` is changed to return `bool`; for TOML syntax error/permission/other errors, the last valid cache is retained (not overwritten as `{}`), only diagnostic logs are recorded and `False` is returned
2. `_watch_loop` and `_check_cache_validity` only emit `config.updated` if `_load_config()` returns `True`
3. `_watch_loop`'s `except Exception` is changed to log at warning level (new i18n key `core.config.watcher_error`, synchronized in five languages)

**Repair Date**: 2026/07/31

**Regression Tests**: `tests/unit/test_unit_config.py` → `test_malformed_toml_preserves_last_valid_cache`, `test_permission_denied_logs_clear_message` (updated to verify cache retention + return False)

**Severity**: 🟡 Moderate

**Type**: Configuration System

---

### [BUG-030] Configuration watcher race condition causes setConfig delayed write silently drops data

**Problem**: Multiple users report that after running `config.setConfig(key, value)` (default `immediate=False`), their module configuration is not written to `config.toml`, while other modules' configurations are normal. Setting `immediate=True` (force flush) can avoid this. The manifestation: configuration written at runtime is lost after the next restart, while configuration generated at startup via template is retained.

**Root Cause**: Two overlapping defects:
1. **Logical defect**: `_watch_loop` unconditionally `_dirty_keys.clear()` any dirty keys when `_check_file_change()` returns `True`. But `_check_file_change()` only uses `!=` to compare mtime, and the framework's own `_flush_config` writing also changes mtime—although `_flush_config` updates `_config_mtime` after writing, the watcher thread may still observe the mtime difference (and on coarse-grained file systems) between file writing and mtime assignment, mistakenly identifying it as "external modification" and clearing all dirty keys.
2. **Thread defect**: `_watch_loop` operates `_write_timer`/`_dirty_keys` without holding `_lock`, creating data races with `setConfig` (holding lock to write `_dirty_keys`), `_schedule_write` (holding lock to write `_write_timer`).

**Root Cause Chain**:
```
Module A setConfig(immediate=True) → flush writes, mtime changes
  → User module setConfig(immediate=False) → enters _dirty_keys, flushes after 5s
    → watcher polls, _check_file_change observes mtime difference from its own previous write
      → _dirty_keys.clear() → user module's dirty keys are silently dropped
        → configuration missing after restart
```

**Affected Version**: 2.6.0 - 2.7.0

**Fixed Version**: 2.7.1

**Repair Content**:
1. Add `_last_self_write_mtime` field; `_flush_config` records it after writing; `_check_file_change` compares it first when mtime changes, matching indicates self-write returns `False`
2. `_watch_loop` holds `_lock` throughout; truly external modification retains `_dirty_keys` (merge semantics), next flush merges with external content (dirty keys take precedence), no longer `clear()`
3. `getConfig`/`_check_cache_validity` path is unaffected (its reload does not clear dirty keys)

**Repair Date**: 2026/08/06

**Regression Tests**: `tests/unit/test_unit_config.py` → `test_self_write_not_detected_as_external`, `test_external_change_preserves_dirty_keys`, `test_flush_merges_dirty_with_external`

**Severity**: 🔴 Severe

**Type**: Configuration System

---

### [BUG-031] Local plugin hot reload completely unusable (reload_plugin always returns False)

**Problem**: Calling `sdk.reload_plugin(name)` or triggering reload via `sdk.enable_plugin_hot_reload()` file monitoring logs WARNING "Hot reload unavailable: SDK has not initialized module loader" and returns `False`—even though the framework has been initialized normally and plugins have been loaded from `plugins/`, the hot reload feature is completely ineffective in the real runtime path.

**Root Cause**: `ModuleLoader` is only created as an internal property of `Initializer` (`Initializer.__init__`'s `self._module_loader`), never injected into the SDK instance; while `sdk.reload_plugin()` checks and reads `self._module_loader` on the SDK instance (always `None`). Additionally, the same method passes `self._sdk` attribute to the loader that does not exist on the SDK (a second latent breakpoint, triggered after fixing the first).

**Affected Version**: 2.8.0-dev.0 - 2.8.0-dev.1

**Fixed Version**: 2.8.0-dev.1

**Repair Content**:
1. After creating the loader in `Initializer.__init__()`, inject `sdk_instance._module_loader = self._module_loader` (rebuilds the hard restart to re-point to the new loader)
2. Synchronize clearing `sdk._module_loader` during the uninit phase to avoid reloading via stale loader after unloading
3. `reload_plugin` changes to pass the SDK instance itself (self) to the loader

**Repair Date**: 2026/09/04

**Regression Tests**: `tests/unit/test_unit_plugin_reload.py` → `TestSDKLoaderWiring` (inject wiring / uninit gracefully False / passing SDK itself)

**Severity**: 🔴 Severe

**Type**: Loader

---

### [BUG-033] "Write-then-read" reads old values during delayed configuration write

**Problem**: After `config.setConfig()` (default `immediate=False` delayed write for ~5 seconds) writes a dot-separated key, immediately reading its **parent/ancestor node** (e.g., `set_erispulse_section("scope.handlers.MyModule", {...})` followed by `get_erispulse_config()`) returns the old value, the written sub-key "disappears," and becomes visible only after the flush. Control plane scope configuration hot updates and other "write-read-write" scenarios are affected (2.8.0 test plugin `/t_section` exposes this).

**Root Cause**: `setConfig` stores dot-separated keys as **flat forms** in the dirty queue `_dirty_keys`, and only `getConfig`'s **exact key queries** hit the dirty queue; tree path queries (e.g., `getConfig("ErisPulse.scope")`) only walk the cache tree, not overlay dirty values—creating a read-you-write gap during delayed flush (`_flush_config` merges dirty keys into the cache and clears the queue) until the flush.

**Affected Version**: 2.6.0 - 2.8.0-dev.1

**Fixed Version**: 2.8.0-dev.1

**Repair Content**: `getConfig` introduces dirty overlay semantics—① exact match dirty keys return directly (original behavior unchanged); ② dirty keys are ancestor of query key → take the longest dirty ancestor and parse the remaining path in its value subtree; ③ dirty keys are descendant of query key → build an overlay subtree (`_dirty_overlay`) and deep merge it with the cache subtree (`_deep_merge`, override priority, not modifying the original cache object). No dirty keys go to the original fast path, zero additional overhead.

**Repair Date**: 2026/09/04

**Regression Tests**: `tests/unit/test_unit_config.py` → `test_get_config_overlays_dirty_descendant`, `test_get_config_overlay_merges_with_cache_siblings`, `test_get_config_overlay_new_branch`, `test_get_config_dirty_ancestor_query`, `test_get_config_dirty_exact_key_still_wins`

**Severity**: 🟡 Moderate

**Type**: Configuration System