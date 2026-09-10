# Bug Tracker

This document records known bugs of the ErisPulse SDK and their fixes, arranged in chronological order by the version in which they were fixed.

> **For Readers**
> No software is perfect by nature, and even the most careful developers can leave behind minor errors. This tracker only includes issues that have a practical impact on operation—those that are too subtle to even reach the "minor" level will not appear here. Although the list contains a significant number of "critical" items, the original intention of publicly documenting these bugs is to make troubleshooting and tracing smoother, not to create anxiety: problems that can be seen, recorded, and fixed are themselves proof that the project is continuously improving. There is no need to be anxious when seeing this list; it is a troubleshooting tool, not a source of fear.

> **How to Read & Maintenance Conventions**
> - Each bug record includes structured fields such as problem description, root cause analysis, affected version range, fix solution, etc. It is recommended to check the "affected version" before upgrading to see if it covers your current version.
> - If you need to add a new bug entry, please supplement content at the corresponding position, following the field specifications and severity/type classifications described below.

---

## Field Descriptions

### Required Fields

| Field | Description |
|------|------|
| **Problem** | The external manifestation of the bug, the abnormal phenomenon observable by the user. Try to provide error messages or typical scenarios |
| **Cause** | Root cause analysis, pointing to specific code defects (including "root cause chain" diagrams for complex scenarios) |
| **Affected Version** | Affected version range, in the format `introduced version - fixed version` (including dev versions at both ends) |
| **Fixed Version** | The specific version number that fixed the bug |
| **Fix Content** | A brief description of the fix solution, including key code changes |
| **Fix Date** | The release date of the corresponding fixed version, in `YYYY/MM/DD` format |
| **Severity** | Marked according to the "Severity Classification" below |
| **Type** | Marked according to the "Type Classification" below, can be combined (e.g., `Adapter / Router`) |

### Optional Fields

| Field | Description | Applicable Scenarios |
|------|------|---------|
| **Reproduction Steps** | The minimal reproducible path to trigger the bug | Complex bugs, sporadic bugs are recommended to supplement |
| **关联** | Related Issue / PR / Commit links | Supplement when there are external discussion records |
| **Regression Test** | Test case location to verify fix and prevent regression | Supplement when corresponding pytest cases have been written |

---

## Severity Classification

| Icon | Level | Judgment Criteria | Typical Manifestations |
|------|------|---------|---------|
| 🔴 | Critical | Causes process crash, data loss/damage, complete unavailability of core functions, security vulnerabilities | OOM Kill, message cannot be sent, module cannot be loaded, hot reload failure |
| 🟡 | Medium | Function abnormality but with workaround, non-core function failure, sporadic problems | Incorrect status judgment, repeated triggers, cache expiration, inaccurate error messages |
| 🟢 | Minor | Does not affect core functions, only code quality or experience issues, potential risks not yet triggered | Deprecated API, dead code, missing warning logs |

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
| Runtime | `sdk.run`/`restart`/`uninit`, lifecycle, signal, subprocess |

---

## Entry Template

When adding a new bug entry, follow the format below:

```markdown
### [BUG-XXX] Title

**Problem**: Problem description (error message or typical phenomenon)
**Cause**: Root cause analysis
**Affected Version**: Introduced version - Fixed version
**Fixed Version**: x.x.x
**Fix Content**: Fix solution
**Fix Date**: YYYY/MM/DD

<!-- Optional fields -->
**Reproduction Steps**: (Recommended for complex bugs)
**关联**: (Issue/PR link)
**Regression Test**: (Test case path)

**Severity**: 🔴 Critical | 🟡 Medium | 🟢 Minor
**Type**: Configuration System / Event System / Adapter / Router / Client / Storage / Loader / CLI / Runtime
```

---

## Statistics Overview

| Severity | Count |
|--------|------|
| 🔴 Critical | 16 |
| 🟡 Medium | 16 |
| 🟢 Minor | 2 |
| **Total** | **34** |

| Type | Count |
|------|------|
| Adapter | 6 |
| Configuration System | 9 |
| Event System | 6 |
| CLI | 3 |
| Storage | 3 |
| Loader | 3 |
| Router | 2 |
| Client | 1 |
| Runtime | 1 |

> Note: A single bug can belong to multiple types; the above table counts by primary type.

---

## Fixed Bugs

### [BUG-001] Event handler duplicate registration causes event to be processed multiple times

**Problem**: When registering multiple handlers using decorators like `@message` or `@notice`, the same event is triggered multiple times, causing commands to be executed multiple times and logs to be output repeatedly.

**Cause**: `BaseEventHandler` lacks deduplication logic when registering handlers with the adapter event bus; each decorator registers once with the bus, causing the event dispatcher to be called multiple times.

**Affected Version**: 2.2.0-dev.0 - 2.2.1-dev.0

**Fixed Version**: 2.2.1-dev.0

**Fix Content**: Optimize `BaseEventHandler` to ensure each event type registers only once with the adapter, avoiding repeated triggers.

**Fix Date**: 2025/08/18

**Severity**: 🔴 Critical

**Type**: Event System

---

### [BUG-002] Init command adapter configuration path type error

**Problem**: When using the `ep init` command for interactive initialization, selecting the adapter configuration results in a type error:

```
Interactive initialization failed: unsupported operand type(s) for /: 'str' and 'str'
```

**Cause**: When adjusting the configuration file path in version 2.3.7, the method parameter type is inconsistent. `_configure_adapters_interactive_sync` receives a `str` type parameter, but internally uses the `Path` `/` operator to concatenate paths.

**Affected Version**: 2.3.7 - 2.3.9-dev.1

**Fixed Version**: 2.3.9-dev.1

**Fix Content**: Change the parameter type of `_configure_adapters_interactive_sync` from `str` to `Path`, passing a `Path` object directly when called.

**Fix Date**: 2026/03/23

**Severity**: 🟡 Medium

**Type**: CLI

---

### [BUG-003] Commands fail after restart

**Problem**: After calling `sdk.restart()`, commands registered with `@command` are not triggered, resulting in the robot not responding after sending a command.

**Cause**: `adapter.shutdown()` clears the event bus, but `BaseEventHandler`'s `_linked_to_adapter_bus` status is not reset to `False`, causing the `_process_event` method to think it is already linked to the adapter bus and skip re-linking.

**Affected Version**: 2.2.x - 2.4.0-dev.2

**Fixed Version**: 2.4.0-dev.3

**Fix Content**: Introduce `_linked_to_adapter_bus` status tracking; after `_clear_handlers()` disconnects from the bus, the next `register()` automatically re-links, adapting to shutdown/restart scenarios.

**Fix Date**: 2026/04/09

**Severity**: 🔴 Critical

**Type**: Event System

---

### [BUG-004] Lifecycle event handlers not cleared

**Problem**: After `sdk.restart()`, old lifecycle event handlers still exist and are triggered repeatedly, causing the same event to be processed multiple times.

**Cause**: The `lifecycle._handlers` dictionary is never cleared in `uninit()`, so old and new handlers coexist after restart.

**Affected Version**: 2.3.0 - 2.4.0-dev.2

**Fixed Version**: 2.4.0-dev.3

**Fix Content**: Clear `lifecycle._handlers` at the end of the `Uninitializer` cleanup process (after all events are submitted).

**Fix Date**: 2026/04/09

**Severity**: 🟡 Medium

**Type**: Runtime

---

### [BUG-005] Event.is_friend_add/is_friend_delete's detail_type inconsistent with OB12 standard

**Problem**: `Event.is_friend_add()` checks `detail_type == "friend_add"`, `Event.is_friend_delete()` checks `detail_type == "friend_delete"`, but OneBot12 standard defines `detail_type` values as `"friend_increase"` and `"friend_decrease"`. This inconsistency with `notice.py`'s `on_friend_add`/`on_friend_remove` decorators using the correct values causes handlers registered via decorators to trigger, but the corresponding `is_friend_add()`/`is_friend_delete()` judgment methods return `False`.

**Cause**: `wrapper.py` uses non-standard naming, while `notice.py` uses the correct OB12 standard naming.

**Affected Version**: Implemented since

**Fixed Version**: 2.4.2-dev.1

**Fix Content**: Change `is_friend_add()`'s matching value from `"friend_add"` to `"friend_increase"`, and `is_friend_delete()` from `"friend_delete"` to `"friend_decrease"`.

**Fix Date**: 2026/04/13

**Severity**: 🟡 Medium

**Type**: Event System

---

### [BUG-006] adapter.clear() does not clear _started_instances causing incorrect state after restart

**Problem**: The `AdapterManager.clear()` method clears `_adapters`, `_adapter_info`, handlers, and `_bots`, but omits clearing `_started_instances`. If the adapter is running and `clear()` is called, `_started_instances` retains dangling references, causing incorrect state judgment after restart.

**Cause**: When `_started_instances` was introduced in 2.4.0-dev.1, it was not cleared in `clear()`.

**Affected Version**: 2.4.0-dev.1 - 2.4.2-dev.0

**Fixed Version**: 2.4.2-dev.1

**Fix Content**: Add `self._started_instances.clear()` in the `clear()` method.

**Fix Date**: 2026/04/13

**Severity**: 🟡 Medium

**Type**: Adapter

---

### [BUG-007] command.wait_reply() uses deprecated asyncio.get_event_loop()

**Problem**: The `CommandHandler.wait_reply()` method uses `asyncio.get_event_loop()` to create futures and get timestamps, which is deprecated in Python 3.10+. In asynchronous contexts, `asyncio.get_running_loop()` should be used. This is inconsistent with `wrapper.py`'s `wait_for()` method, which uses `get_running_loop()`.

**Cause**: The old API was used during development, and the newly added `wait_for()` method used the correct API but did not retroactively fix the old code.

**Affected Version**: 2.3.0-dev.0

**Fixed Version**: 2.4.2-dev.1

**Fix Content**: Replace `asyncio.get_event_loop()` in `command.py` with `asyncio.get_running_loop()` in two places.

**Fix Date**: 2026/04/13

**Severity**: 🟢 Minor

**Type**: Event System

---

### [BUG-008] Bot offline event is repeatedly submitted during shutdown

**Problem**: When calling `adapter.shutdown()` to shut down all adapters, `_update_bot_status()` repeatedly submits Bot offline events during the shutdown process, causing the same batch of Bots to be marked offline multiple times and triggering multiple `adapter.bot.offline` lifecycle events.

**Cause**: The Bot status tracking system introduced in 2.4.0-dev.1 did not set a "shutting down" flag during `shutdown()`, so `_update_bot_status()` could not distinguish between normal offline and cascade offline during shutdown.

**Affected Version**: 2.4.0-dev.1 - 2.4.2-dev.1

**Fixed Version**: 2.4.2-dev.1

**Fix Content**: Add `_is_being_shutdown` flag in `AdapterManager`, set to True at the start of `shutdown()` and cleared at the end; `_update_bot_status()` skips repeated submissions during shutdown based on this flag.

**Fix Date**: 2026/04/21

**Severity**: 🟡 Medium

**Type**: Adapter

---

### [BUG-009] LazyModule synchronous access to BaseModule causes incomplete initialization

**Problem**: When accessing lazy-loaded BaseModule attributes in synchronous contexts, the module uses `loop.create_task()` for asynchronous initialization but does not wait, leading to race conditions when attributes are accessed before initialization is complete.

**Cause**: `_ensure_initialized()` uses `loop.create_task(self._initialize())` and returns immediately without ensuring initialization is complete.

**Affected Version**: 2.4.0-dev.0 - 2.4.2-dev.1

**Fixed Version**: 2.4.2-dev.2

**Fix Content**: In synchronous contexts, BaseModule initialization is changed to use `asyncio.run(self._initialize())` to ensure initialization is complete before returning. The transparent proxy feature is maintained, so users do not need to be aware of the difference between synchronous and asynchronous contexts.

**Fix Date**: 2026/04/21

**Severity**: 🟡 Medium

**Type**: Loader

---

### [BUG-010] Multi-threaded configuration system write causes data loss

**Problem**: In a multi-threaded environment, when multiple threads simultaneously call `config.setConfig()`, the `_flush_config()` read-modify-write operation is not atomic, potentially causing partial write loss.

**Cause**: Although `_flush_config()` uses `RLock`, there is no file lock protection between file read and write, and `_schedule_write`'s Timer may be triggered multiple times, causing overwrite.

**Affected Version**: 2.3.0 - 2.4.2-dev.1

**Fixed Version**: 2.4.2-dev.2

**Fix Content**:
1. Add file lock mechanism (`_file_lock`) to ensure atomic file operations
2. Use temporary file for write and then atomically rename (`os.replace`/`os.rename`)
3. Improve `_schedule_write` Timer cancellation and rescheduling logic

**Fix Date**: 2026/04/21

**Severity**: 🔴 Critical

**Type**: Configuration System

---

### [BUG-011] Windows Ctrl+C cannot stop the program

**Problem**: When running `python main.py` directly on Windows, pressing Ctrl+C does not terminate the program. After the program starts normally and outputs the routing server information, Ctrl+C has no response and can only be forcibly killed via the task manager. However, stopping with `epsdk run` works normally—though `epsdk run` runs via a subprocess model.

**Cause**: The Hypercorn ASGI server's `serve()` function internally registers its own SIGINT handler via `signal.signal(SIGINT, handler)`, overriding Python's default `KeyboardInterrupt` handling mechanism. When Hypercorn is started as a background task via `asyncio.create_task()`, its internal shutdown process cannot be triggered normally (because it expects the `worker_serve` mode), causing the Ctrl+C signal to be swallowed by Hypercorn but not triggering any cleanup actions.

**Affected Version**: 2.3.6 - 2.4.2

**Fixed Version**: 2.4.3-dev.0

**Fix Content**:
1. Switch the ASGI server from Hypercorn to Uvicorn (in `pyproject.toml` dependency change)
2. Use `uvicorn.Server._serve()` to start the server directly, **bypassing** the `capture_signals()` signal handling context manager
3. Implement graceful shutdown via `server.should_exit = True`, canceling the background task on timeout
4. Synchronously remove the subprocess model and `runtime/cleanup.py` cleanup module (subprocess cleanup mechanism no longer needed)

**Fix Date**: 2026/04/28

**Severity**: 🔴 Critical

**Type**: CLI / Runtime

---

### [BUG-012] Hot restart does not apply updated module code

**Problem**: After executing `sdk.restart()` soft restart, the new code (such as new API routes) of modules/adapters upgraded via `epsdk install` does not take effect, and old logic is still running. The latest code must be loaded by completely restarting the process.

**Cause**: `_do_restart()` reinitializes by calling `entry_point.load()`, but this function returns a cached old module object from `sys.modules` rather than reloading from disk.

**Affected Version**: Early versions - 2.4.3-dev.1

**Fixed Version**: 2.4.3-dev.1

**Fix Content**: Before `init()`, clear the cache of loaded modules/adapters in `sys.modules` so that `entry_point.load()` loads the latest code from disk. Add `_collect_top_level_modules()` and `_invalidate_module_cache()` helper methods, deriving top-level module names via `top_level.txt` or entry-point value.

**Fix Date**: 2026/05/03

**Severity**: 🔴 Critical

**Type**: Loader / Runtime

---

### [BUG-013] Module loading strategy sort logic error

**Problem**: `ModuleLoadStrategy` provides a `priority` field to declare module initialization priority, but the implementation has an error, causing modules not to be initialized in the expected priority order, but instead in the default order of `entry_points()`. When modules have initialization dependencies, they cannot ensure the correct initialization order through `priority`.

**Cause**: The implementation of the loading strategy has a sorting logic error; `initialize_modules()` does not sort the module list by `priority`.

**Affected Version**: 2.3.4 - 2.4.5-dev.2

**Fixed Version**: 2.4.5-dev.3

**Fix Content**: Before traversing `initialize_modules()`, sort the module list by `priority` in descending order. Modules with the same priority maintain their original relative order (stable sort).

**Fix Date**: 2026/05/15

**Severity**: 🟡 Medium

**Type**: Loader

---

### [BUG-014] Adapter middleware returning None causes event data loss

**Problem**: When `adapter.emit()` executes the OneBot12 middleware chain, if a middleware returns `None` (e.g., forgetting to `return data`), subsequent middlewares and all event handlers receive `processed_data` as `None`, causing event processing to fail completely.

**Cause**: The middleware chain implementation `processed_data = await middleware(processed_data)` does not check if the return value is `None`, directly overwriting the result from the previous step.

**Affected Version**: unknown - 2.4.5-dev.3

**Fixed Version**: 2.4.5-dev.4

**Fix Content**: When middleware returns `None`, ignore the return value, retain the original data, and output a warning-level log.

**Fix Date**: 2026/05/15

**Severity**: 🔴 Critical

**Type**: Adapter / Event System

---

### [BUG-015] Configuration file path depends on working directory

**Problem**: `ConfigManager`'s configuration file path defaults to the relative path `"config/config.toml"`, which relies on `os.getcwd()` for resolution at runtime. If the working directory changes during runtime (e.g., via `os.chdir()`), configuration file read/write operations will point to the wrong location, causing configuration loss or reading old data.

**Cause**: In `__init__`, the relative path is directly stored without being resolved to an absolute path at initialization.

**Affected Version**: 2.3.7 - 2.4.5-dev.3

**Fixed Version**: 2.4.5-dev.4

**Fix Content**: In `ConfigManager.__init__()`, if the passed path is relative, automatically resolve it to an absolute path using `os.path.abspath()`.

**Fix Date**: 2026/05/15

**Severity**: 🟡 Medium

**Type**: Configuration System

---

### [BUG-016] BaseStorage confuses storing value None with nonexistent key

**Problem**: `BaseStorage.get_multi()` / `__getattr__()` cannot distinguish between "key does not exist" and "key's value is None", so when a user explicitly stores `None` and then reads it, it is treated as if the key does not exist.

**Cause**: The value retrieval logic directly uses `value is None` to determine if the key exists, lacking an independent "missing" marker.

**Affected Version**: Early versions - 2.4.6-dev.6

**Fixed Version**: 2.4.6-dev.6

**Fix Content**: Introduce `_SENTINEL` sentinel value to distinguish between "key does not exist" and "value is None", so they are no longer confused.

**Fix Date**: 2026/06/07

**Severity**: 🟡 Medium

**Type**: Storage

---

### [BUG-017] WebSocket route auto_accept flag lost after service restart

**Problem**: After a service restart (such as `sdk.restart()`), the `auto_accept` configuration for all WebSocket routes becomes `False`, and connections that were expected to be automatically accepted remain pending, causing the client to wait for a long time without response, resulting in WS connection hanging.

**Cause**: `_restore_routes_from_records()` hardcodes `auto_accept` as `False` when restoring routes from persistent records, not reading the value from the original record; also, when the route storage tuple expanded from a binary tuple to a ternary tuple, the restoration logic was not synchronized.

**Affected Version**: 2.3.8-dev.0 - 2.4.6-dev.6

**Fixed Version**: 2.4.6-dev.6

**Fix Content**: The route storage tuple expands to `(handler, auth_handler, auto_accept)`, and `_restore_routes_from_records()` reads the real `auto_accept` value from the record instead of hardcoding `False`.

**Fix Date**: 2026/06/07

**Severity**: 🔴 Critical

**Type**: Router

---

### [BUG-018] Concurrent calls to HTTP/WS client cause crashes and connection leaks

**Problem**: The HTTP and WebSocket clients in `Core/client.py` have multiple stability defects in concurrent scenarios, leading to connection leaks or process crashes:
- Concurrent calls to `ClientWebSocket.receive()` with aiohttp raise `Concurrent call to receive() is not allowed`
- Concurrent calls to `_get_http_session()` / `_get_ws_session()` may create multiple sessions, and `_drain_sessions()` does not close old connections, causing connection leaks
- `request()` exception handling order is incorrect: `except ClientConnectionError` (ErisPulse exception) is never triggered, aiohttp connection errors are caught by the general `except Exception`, causing the "connection retry + session recreation" logic (dead code) never executed
- `send_json()` ignores `mode="binary"` parameter; `_get_ws_session()` does not pass default request headers

**Cause**: The client's initial implementation (2.4.6-dev.5) lacks concurrency protection and exception classification, and improperly handles aiohttp exception hierarchy and ErisPulse custom exception inheritance.

**Affected Version**: 2.4.6-dev.5 - 2.4.8

**Fixed Version**: 2.4.8

**Fix Content**:
1. Add `_recv_lock` to serialize all `receive()` / `receive_text()` / `receive_bytes()` calls
2. Add `_session_lock` to protect session creation; `_drain_sessions()` is changed to an asynchronous method and truly closes old sessions
3. Refactor `request()` exception handling order: `asyncio.TimeoutError` → `aiohttp.ClientConnectionError` (triggers session recreation) → `aiohttp.ClientError` → `ClientError` (propagates) → `Exception`
4. Fix `send_json()` mode handling, `_get_ws_session()` default request headers, `close()` concurrency race, `HttpResponse.__aexit__` duplicate `release()`

**Fix Date**: 2026/06/12

**Severity**: 🔴 Critical

**Type**: Client

---

### [BUG-019] Adapter hot reload causes route conflicts leading to reload failure

**Problem**: Third-party modules (such as Dashboard) trigger adapter hot reload, or adapter startup fails and retries, because the previous registered old routes (such as `onebot11_default`) are not cleared, throwing a `WebSocket path ... already registered` conflict, causing reload failure. A complete restart of the process is required to recover.

**Cause**: `AdapterManager.shutdown()` only clears routes with `unregister_all_by_namespace(platform)`, but adapters (such as OneBot11) register WebSocket routes with `onebot11_{account_name}` as the namespace, resulting in a granularity mismatch and making cleanup an empty operation; startup failure retry paths also do not clear previous route remnants.

**Affected Version**: Early versions - 2.4.9

**Fixed Version**: 2.4.9

**Fix Content**:
1. Route registration automatically tracks `owner → namespace` ownership relationships via `current_owner` ContextVar
2. Add `unregister_all_by_owner(owner)`, stopping/restarting with cleanup of all resources registered by owner, covering fine-grained namespace
3. Add `_stop_adapter(platform)` primitive ("stop equals cleanup"), binding stopping the adapter and reclaiming its registered resources in one call, `restart()` and startup failure retry both go through this entry
4. Add framework-level `adapter.restart(platform)` API, third-party modules should call this method instead of directly operating the adapter instance

**Fix Date**: 2026/06/12

**Severity**: 🔴 Critical

**Type**: Adapter / Router

---

### [BUG-020] Subprocess mode `ep run <script>` cannot find subpackages in script's directory

**Problem**: When running a script with `ep r .\main.py` in non-hot-reload mode, if the script has relative imports (such as `from qg import ...`), it reports `No module named 'qg'`. The `--reload` mode works normally.

**Cause**: Non-hot-reload mode directly calls `runpy.run_path()` to execute the script, which does not automatically add the script's directory to `sys.path`. The `--reload` mode runs via `subprocess.Popen` subprocess, which automatically inherits the current working directory, making `sys.path[0]` the script's directory, so it works normally.

**Affected Version**: 2.5.0 - 2.5.2-dev.0

**Fixed Version**: 2.5.2-dev.0

**Fix Content**: Before calling `runpy.run_path()`, manually insert the script's directory into `sys.path[0]`.

**Fix Date**: 2026/06/27

**Severity**: 🟡 Medium

**Type**: CLI

---

### [BUG-021] SQL query builder rejects valid wildcard and list expressions

**Problem**: `SQLiteQueryBuilder`'s `_build_select_sql()` validates all SELECT columns with `_validate_identifier()`, which uses a strict whitelist regex `^[a-zA-Z_][a-zA-Z0-9_]*$`, causing valid SQL syntax to be incorrectly judged as unsafe column names:

- `SELECT *` — `*` is a standard SQL wildcard
- `SELECT COUNT(*)` — aggregate function
- `SELECT users.name` — qualified column name
- `SELECT col AS alias` — column alias

Among these, `Select("*")` is used by Cron and other modules, causing module `on_load` execution to fail and modules cannot load.

**Cause**: In version 2.4.6, SQL injection protection was enhanced by introducing `_validate_identifier()` whitelist validation. This validation applies to all column names, but does not distinguish between read-side (SELECT/ORDER BY) and write-side (INSERT/UPDATE). SELECT columns allow complex SQL expressions and should not be restricted by simple identifier whitelist.

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

### [BUG-022] _resolve_account() account resolution regression (_accounts_data not filled)

**Problem**: After the 2.5.2 configuration system refactoring, multi-account adapters declaring `AccountConfigClass` report `ValueError("未声明 AccountConfigClass，无法解析账户")` when calling `wait_reply`, `reply`, and other methods requiring message sending. Even if the adapter correctly configures multi-account information, account resolution still fails.

**Cause**: In 2.5.2-dev.5, `_load_accounts()` (responsible for reading configuration + validation + filling `_accounts_data`) was refactored into `_ensure_accounts_exist()` (only generates configuration template), but `_resolve_account()` still checks `self._accounts_data is None`. Since `_ensure_accounts_exist()` no longer fills `_accounts_data`, this attribute remains `None`, causing `_resolve_account()` to prematurely return `(None, None)`, and account resolution fails completely.

**Root Cause Chain**:
```
_load_accounts() was deleted
  → __init__ no longer fills _accounts_data
    → _accounts_data is always None
      → _resolve_account() checks _accounts_data is None → return (None, None)
        → downstream calls to _resolve_account (e.g. call_api) get None
          → triggers error
```

**Affected Version**: 2.5.2-dev.5 - 2.5.2

**Fixed Version**: 2.5.3

**Fix Content**: In `BaseAdapter.__init__`, after `self._ensure_accounts_exist()`, restore the filling of `_accounts_data`:
```python
if self.AccountConfigClass is not None:
    self._ensure_accounts_exist()
    self._accounts_data = self.accounts  # restore filling, data source is real-time read accounts property
```
The `_resolve_account()` logic remains unchanged, fully backward compatible:
- Adapters that do not declare `AccountConfigClass`: `_accounts_data` remains `None` → return `(None, None)`
- Adapters that declare `AccountConfigClass`: `_accounts_data` is filled → normal resolution
- Adapters that overwrite `_load_accounts` or manually set `_accounts_data`: override in `super().__init__()` with highest priority

**Fix Date**: 2026/07/07

**Severity**: 🔴 Critical

**Type**: Adapter / Configuration System

---

### [BUG-023] Adapter cache not refreshed after account configuration modification causes account resolution failure

**Problem**: After users modify the account configuration of a multi-account adapter (such as filling in the token) through the Dashboard, the adapter still uses the old cache, and calling message-sending-related methods reports `未找到可用账户 (account_id=default)`. The process must be restarted to make the new configuration effective.

**Cause**: `_accounts_data` is only read from the configuration storage once during `BaseAdapter.__init__`, and is never refreshed afterward. `AdapterManager._run_adapter()` and `restart()` do not re-read the account configuration before calling `adapter.start()`, causing the cache to be out of sync with the actual configuration.

**Affected Version**: 2.4.6 - 2.5.4

**Fixed Version**: 2.5.4

**Fix Content**: In `AdapterManager._run_adapter()` and `restart()`, before calling `adapter.start()`, refresh `adapter._accounts_data = adapter.accounts` to ensure the latest configuration is used each time the adapter starts.

**Fix Date**: 2026/07/09

**Severity**: 🔴 Critical

**Type**: Adapter / Configuration System

---

### [BUG-024] storage.set() writing large numeric key triggers OOM Kill

**Problem**: When calling `storage.set()` to write a nested key path containing a large numeric field (such as QQ group number `871684833`), the process is killed by container OOM (exit code -9), and the service crashes and cannot recover.

**Cause**: In the recursive implementation of `_set_nested_value`, a pure numeric field in the nested key path is misjudged as a list index by `isdigit()`, triggering `current.extend([None] * (index - len(current) + 1))`, attempting to allocate hundreds of millions of elements, instantly exhausting memory.

**Root Cause Chain**:
```
Key path contains pure numeric field (such as group number 871684833)
  → isdigit() misjudged as array index
    → extend([None] * (871684833 - len(current) + 1))
      → attempt to allocate hundreds of millions of elements
        → memory exhausted → container OOM Kill (exit code -9)
```

**Affected Version**: 2.5.1 - 2.5.5

**Fixed Version**: 2.5.5

**Fix Content**:
1. Always use a dictionary when pre-creating intermediate layers, never guess the container type based on whether the next segment is a number
2. Only handle index processing when the container itself is a list and the index is less than `STORAGE_MAX_LIST_INDEX` (10000); skip large indexes safely
3. Change the recursive implementation to an iterative one, eliminating potential infinite recursion risks in the original code
4. Add `STORAGE_MAX_LIST_INDEX` constant to `Core/constants.py`, centrally managing the index safety upper limit

**Fix Date**: 2026/07/10

**Reproduction Steps**:
```python
# Writing a nested key path containing a large number field (such as QQ group number) triggers OOM
await sdk.storage.aset("groups.871684833.name", "某群")
# → process memory surges instantly, killed by OOM
```

**Regression Test**: `tests/unit/test_unit_storage.py` adds 4 regression test cases
- `test_nested_key_numeric_segment_as_dict_key` — precisely reproduces OOM scenario
- `test_nested_key_numeric_segment_multiple` — multiple consecutive numeric fields as dictionary keys
- `test_nested_key_existing_list_index_set_within_limit` — existing list index write within limit
- `test_nested_key_list_index_safety_limit` — safety limit verification for large index

**Severity**: 🔴 Critical

**Type**: Storage

---

### [BUG-025] on_config_update callback not called by core router

**Problem**: `on_config_update(old, new)` is defined in the base class (`BaseModule` / `BaseAdapter`), but the framework core does not associate it with configuration change events. As a result, manual editing of `config.toml` or code calls to `setConfig()` do not trigger `on_config_update`.

**Cause**: `ConfigManager` emits `config.set` / `config.updated` lifecycle events when configuration changes, but lacks the subscription logic to forward these events to each component's `on_config_update` method.

**Root Cause Chain**:
```
Core does not subscribe config.set / config.updated
  → configuration change events are not forwarded
    → on_config_update is not called
      → manual file edit / code setConfig does not trigger hot update callback
```

**Affected Version**: All versions

**Fixed Version**: 2.6.2

**Fix Content**: `ModuleManager` / `AdapterManager` register `config.set` (covers code `setConfig()` path) and `config.updated` (covers manual file edit path) event subscriptions, match by configuration key prefix and call the corresponding component's `on_config_update`, passing type-safe configuration objects. Also fix `_flush_config()` writing file without synchronizing `_config_mtime`, avoiding framework's own write being mistakenly judged as external modification by file monitoring task and repeatedly triggering `config.updated`.

**Compatibility Note**: Configuration hot update is now unified and maintained by the framework core. Previously, the configuration management panel triggered it on behalf of the core; this logic has been removed, and upgrading the framework requires upgrading the configuration management panel as well, otherwise duplicate triggers (core + panel each call once) will occur. The `on_config_update` method signature and semantics remain unchanged, and subclasses do not need modification.

**Fix Date**: 2026/07/23

**Severity**: 🟡 Medium

**Type**: Configuration System

---

### [BUG-026] notice/request event reply target inference error

**Problem**: In group notification events (such as member joining a group `group_member_increase`), calling `event.reply()` sends the message to the private chat of the user who triggered the event, not the group where the event occurred. The same applies to friend notification events, where the reply target may be incorrect.

**Cause**: `infer_receive_type()` directly returns the event's `detail_type` as the session type. For message events, this is correct (`detail_type` values `private`/`group` are session types), but for notice/request events, `detail_type` is a semantic subtype (such as `group_member_increase`, `friend_increase`), not a session type. Later, `convert_to_send_type()` and `get_id_field()` do not find the value in the mapping table, defaulting to `"user"` / `"user_id"`, causing the reply target to be incorrect.

**Root Cause Chain**:
```
notice event detail_type="group_member_increase"
  → infer_receive_type() directly returns "group_member_increase"
    → convert_to_send_type("group_member_increase") not in mapping table → default "user"
    → get_id_field("group_member_increase") not in mapping table → default "user_id"
      → target_id = event["user_id"]  ← new member's private chat (not group)
```

**Affected Version**: All versions

**Fixed Version**: 2.7.0-dev.3

**Fix Content**: `infer_receive_type()` adds a check—`detail_type` is only returned directly if it is a known session type (standard or custom type); otherwise, the session type is inferred based on the ID field (`group_id` / `channel_id` / `user_id`, etc.).

**Regression Test**: `tests/unit/test_unit_session_type.py` → `TestNoticeRequestTypeInference` (10 test cases)

**Fix Date**: 2026/07/29

**Severity**: 🟢 Minor

**Type**: Event System

---

### [BUG-027] Route rate limiting cleanup task uses fixed window causing long window rate limit rules to fail

**Problem**: When route rate limiting is configured as a long window rule (such as `100/hour`, `{"requests": 100, "window": 3600}`), rate limiting is ineffective—practically similar to `100/minute` (up to about 6000 requests per hour), completely failing to provide the expected hourly protection.

**Cause**: `_apply_rate_limit` parses the actual `window` (maximum 3600 seconds) for each route, and per-request checks do use this window; however, the background cleanup task `_cleanup_expired_rate_limits` uses the fixed constant `DEFAULT_RATE_LIMIT_WINDOW_SECS` (60 seconds) as the unified cleanup threshold for all routes. Thus, time stamps earlier than 60 seconds in the `100/hour` route are cleared early by the cleanup task, and the hour window never accumulates close to 100 records, severely weakening the rate limit.

**Root Cause Chain**:
```
_apply_rate_limit parses window=3600 (100/hour)
  → per-request check uses 3600s to retain timestamps (correct)
  → but _cleanup_expired_rate_limits uses fixed max_window=60s to clean
    → time stamps earlier than 60s are cleared
      → only the most recent 1 minute's records remain in the hour window
        → 100/hour effectively degrades to ~100/minute (relaxed about 60 times)
```

**Affected Version**: 2.6.0-dev.0 - 2.7.0-dev.4

**Fixed Version**: 2.7.0-dev.5

**Fix Content**: Add `_rate_limit_windows: dict[str, int]` to record each route's actual window by store key; `_apply_rate_limit` writes the window when creating entries for the first time; `_cleanup_expired_rate_limits` cleans up by each key's own window (fallback to default if missing); cleanup deletion and `stop()` synchronize maintenance of both dictionaries.

**Fix Date**: 2026/07/31

**Regression Test**: `tests/unit/test_unit_router.py` → `TestRateLimit::test_cleanup_respects_per_route_window`

**Severity**: 🔴 Critical

**Type**: Router

---

### [BUG-029] Configuration listener broadcasts incomplete TOML and silently swallows exceptions

**Problem**: When a user edits `config.toml` and saves it halfway (producing a temporary syntax error), the configuration listening background thread detects mtime changes, reloads the configuration, but fails to load and still broadcasts an empty configuration `{}` as `config.updated`, causing adapters/modules' `on_config_update` to receive an empty configuration and mistakenly assume all configuration items have been cleared, reverting to default values. Additionally, the listener loop uses `except Exception: pass` to silently swallow all exceptions, making it impossible to troubleshoot watcher failures.

**Cause**: Two defects overlap:
1. `_load_config` overwrites `self._cache` as `{}` when TOML syntax errors/permission errors occur, but the background listener thread `_watch_loop` and cache timeout path `_check_cache_validity` both call `_emit_config_updated()` unconditionally after `_load_config()`, broadcasting the "empty cache produced by failed loading" as a real change.
2. `_watch_loop`'s `except Exception: pass` does not log any errors.

**Root Cause Chain**:
```
User saves halfway → TOML syntax error
  → _load_config() overwrites _cache = {}
    → _watch_loop unconditionally _emit_config_updated(new_config={})
      → adapters/modules on_config_update receive empty config
        → incorrectly assume configuration has been cleared, revert to default values
```

**Affected Version**: 2.6.2-dev.1 - 2.7.0-dev.4

**Fixed Version**: 2.7.0-dev.5

**Fix Content**:
1. `_load_config` is changed to return `bool`; when TOML syntax errors/permission errors/other errors occur, it **retains the last valid cache** (does not overwrite as `{}`), only logs diagnostic messages, and returns `False`
2. `_watch_loop` and `_check_cache_validity` only emit `config.updated` if `_load_config()` returns `True`
3. `_watch_loop`'s `except Exception` is changed to log at warning level (adds i18n key `core.config.watcher_error`, synchronized in five languages)

**Fix Date**: 2026/07/31

**Regression Test**: `tests/unit/test_unit_config.py` → `test_malformed_toml_preserves_last_valid_cache`, `test_permission_denied_logs_clear_message` (updated to verify cache retention + return False)

**Severity**: 🟡 Medium

**Type**: Configuration System

---

### [BUG-030] Configuration watcher race condition causes setConfig delayed write to silently drop data

**Problem**: Multiple users report that after using `config.setConfig(key, value)` (default `immediate=False`), their module configuration is not written to `config.toml`, while other modules' configurations are normal. Setting `immediate=True` (force flush) can avoid this. The manifestation is: configuration written at runtime is lost after the next restart, while configuration generated at startup by the template is retained.

**Cause**: Two overlapping defects:
1. **Logical defect**: `_watch_loop` unconditionally `_dirty_keys.clear()` all dirty keys when `_check_file_change()` returns `True`. However, `_check_file_change()` only uses `!=` to compare mtime, and the framework's own `_flush_config` write also changes mtime—although `_flush_config` updates `_config_mtime` after writing, the watcher thread may still observe mtime differences between file writing and mtime assignment (and on coarse-grained file systems), mistakenly judging it as "external modification" and clearing all dirty keys.
2. **Thread defect**: `_watch_loop` operates `_write_timer`/`_dirty_keys` without holding `_lock`, creating data races with `setConfig` (holds lock to write `_dirty_keys`), `_schedule_write` (holds lock to write `_write_timer`).

**Root Cause Chain**:
```
Module A setConfig(immediate=True) → flush writes, mtime changes
  → User module setConfig(immediate=False) → enters _dirty_keys, flushes in 5s
    → watcher polling, _check_file_change observes mtime difference from previous self-write
      → _dirty_keys.clear() → user module's dirty keys are silently dropped
        → configuration missing after restart
```

**Affected Version**: 2.6.0 - 2.7.0

**Fixed Version**: 2.7.1

**Fix Content**:
1. Add `_last_self_write_mtime` field; `_flush_config` records it after writing; `_check_file_change` first compares this value when mtime changes, returns `False` if matches (treated as self-write)
2. `_watch_loop` holds `_lock` for the entire segment; truly external modifications retain `_dirty_keys` (merge semantics), next flush merges with external content (dirty keys take precedence), no longer `clear()`
3. `getConfig`/`_check_cache_validity` paths are unaffected (their reload does not clear dirty keys)

**Fix Date**: 2026/08/06

**Regression Test**: `tests/unit/test_unit_config.py` → `test_self_write_not_detected_as_external`, `test_external_change_preserves_dirty_keys`, `test_flush_merges_dirty_with_external`

**Severity**: 🔴 Critical

**Type**: Configuration System

---

### [BUG-032] Configuration delay write period "write then read immediately" reads old value

**Problem**: After `config.setConfig()` (default `immediate=False` delay about 5 seconds to write), writing a dot-separated key and immediately reading its **parent/ancestor node** (such as `set_erispulse_section("scope.actions.MyModule", {...})` then calling `get_erispulse_config()`) returns the old value, with the written sub-key "disappearing" until the next flush. Scenarios like scope configuration hot updates ("write-read-write") are affected (2.8.0 test plugin `/t_section` cases exposed).

**Cause**: `setConfig` stores dot-separated keys as **flat** entries in the dirty queue `_dirty_keys`, only `getConfig`'s **exact key query** hits the dirty queue; tree path queries (e.g., `getConfig("ErisPulse.scope")`) only walk the cache tree, not overlay dirty values—during the delay write period (`_flush_config` merges dirty keys into cache and clears the queue), a read-you-write gap occurs.

**Affected Version**: 2.6.0 - 2.8.0-dev.1

**Fixed Version**: 2.8.0-dev.1

**Fix Content**: `getConfig` introduces dirty overlay semantics—① exact hit in dirty key returns directly (original behavior unchanged); ② dirty key is the query key's ancestor → take the longest dirty ancestor and parse the remaining path in its value subtree; ③ dirty key is the query key's descendant → build an overlay subtree (`_dirty_overlay`) and deeply merge it with the cache subtree (`_deep_merge`, override takes precedence, does not modify original cache object). Without dirty keys, the original fast path is taken, with zero additional overhead.

**Fix Date**: 2026/09/04

**Regression Test**: `tests/unit/test_unit_config.py` → `test_get_config_overlays_dirty_descendant`, `test_get_config_overlay_merges_with_cache_siblings`, `test_get_config_overlay_new_branch`, `test_get_config_dirty_ancestor_query`, `test_get_config_dirty_exact_key_still_wins`

**Severity**: 🟡 Medium

**Type**: Configuration System

---

### [BUG-033] wait_reply hanging replies are starved by high-priority processors

**Problem**: When a module calls `wait_reply()` to wait for a user reply, if that reply message is claimed by a higher-priority event handler (`mark_processed()`), the command dispatcher, upon seeing the `_processed` flag at the entry, directly returns, and the reply matching logic at the end of the dispatcher never executes—waiting parties receive no reply, only waiting until timeout returns `None`. Typical trigger scenario: robots using high-priority message handlers (recording/auditing/blocking types) have random failures in all conversational interactions.

**Cause**: Reply matching `_check_pending_reply` is placed at the end of `_handle_message` (only executed if command matching fails), while `_processed` checking is before it—claim checking and reply matching order are reversed. Interactive waiting is a framework-level session continuation mechanism, not a competing processor, and should not be affected by other processors' claim.

**Affected Version**: 2.2.0-dev.0 - 2.8.0-dev.1

**Fixed Version**: 2.8.0-dev.2

**Fix Content**: Move reply matching to the entry of `_handle_message` (before `_processed` checking, only for message events): first try to complete the pending conversation, if matched, the event is marked as processed, and the following checks naturally short-circuit; if not matched, continue the original command matching process. The matching chain delegates to a new interaction session manager (`Core/Event/interaction.py`), gaining permission review and cancellation by affiliation in the process.

**Fix Date**: 2026/09/08

**Regression Test**: `tests/unit/test_unit_interaction.py` (TestRegisterResolve matched/unmatched/claimed mark), `tests/unit/test_unit_event.py` (full chain of wait_reply)

**Severity**: 🟡 Medium

**Type**: Event System / Command System

---

### [BUG-034] Runtime binding with persist=False in scope is silently overridden by any subsequent configuration write

**Problem**: `scope.set_module(..., persist=False)` and other runtime writes only modify memory `self._data`; but scope subscribes to `config.set` / `config.updated` events, and any code writing configuration (such as a module loading and writing its own default configuration) triggers scope to rebuild the configuration tree from the configuration file, discarding all previous runtime bindings (reverting to default allow), with no log warning. Scenarios depending on runtime bindings (Dashboard "runtime-only" switches, module runtime dynamic disabling) behavior reverts after unrelated module configuration writes.

**Cause**: Root cause chain: `scope.set/delete(persist=False)` only writes memory (`Core/scope.py`) → any `setConfig` triggers `config.set` event → `_on_config_updated` unconditionally `_load_config()` → `_apply_tree()` replaces the persistent layer with `self._data = {...}` → runtime bindings not in the configuration file are discarded.

**Affected Version**: 2.8.0-dev.1 - 2.8.0-dev.2
**Fixed Version**: 2.8.0-dev.2
**Fix Content**: Introduce a runtime overlay layer `_runtime_overrides` (with deletion sentinel): `persist=False` write/delete records into the overlay, `_apply_tree()` rebuilds the persistent layer and replays in write order, runtime rules remain effective after any configuration write; `persist=True` write/delete clears corresponding overlay records (user persistent semantics take precedence); `config.set` filters by event key, `config.updated` compares new and old scope sections, only rebuilds if scope actually changes (attaching LRU cache invalidation to avoid unrelated writes flushing); add `unregister_by_owner()` for modules to clean up with the caller at unload. `Core.Event.overrides` has a similar issue with persist=False runtime overrides, fixed synchronously with the overlay architecture.
**Fix Date**: 2026/09/09

**Reproduction Steps**: ① `scope.set_module("testplat", blocked=["TestB"], persist=False)` →判定 False；② Any module executes `config.setConfig("HelpModule", {...})` → triggers scope rebuild；③ `scope.is_allowed("testplat", None, "TestB")` returns True (expected still False)。
**关联**: Issue #432
**Regression Test**: `tests/unit/test_unit_scope.py::TestRuntimeOverrideSurvival` (irrelevant write survives/rebuilds replay/deletion sentinel/persistent clear/precise invalidation/owner cleanup)

**Severity**: 🟡 Medium
**Type**: Configuration System / Runtime

---

### [BUG-035] Configuration panel select options and dict fields render as [object Object]

**Problem**: In the WebUI configuration panel, select field options display `[object Object]` (such as dynamically generated color style options); dict fields without declared control types (such as `stalker_mode`, `knowledge_base`, etc.) display `[object Object]` in text boxes, making it impossible to view and edit normally.

**Cause**: Two independent defects: ① The framework i18n resolver `_resolve_i18n_text` only restores dictionaries with an `i18n` key, so option labels are only `default`-only dictionaries (without an `i18n` key for dynamic text) are passed through as-is, and the frontend `esc(label)` string coercion results in `[object Object]`; ② Dashboard rendering branches only use JSON textarea for array types, dict values fall into the plain text input branch and are `String()` coerced. Additionally, if a module declares `_schema_meta` as a regular dataclass field (missing `ClassVar` annotation), it will be treated as a configuration field, exacerbating confusion.

**Affected Version**: 2.7.0 - 2.8.0-dev.2
**Fixed Version**: 2.8.0-dev.2
**Fix Content**: ① `_resolve_i18n_text` supports dictionaries with only a `default` key, restoring them to text; ② Framework schema/template/default value/filling/validation five places exclude underscore-prefixed fields (harmless if misdeclared); ③ Dashboard select option label object fallback parsing (prioritizing `default`), dict/table fields rendered as JSON textarea (save path as `tp=object` JSON.parse back, complete round-trip).
**Fix Date**: 2026/09/09

**Regression Test**: `tests/unit/test_unit_config.py::TestResolveI18nDefaultOnlyDict`, `TestSchemaUnderscoreFieldExclusion`

**Severity**: 🟡 Medium
**Type**: Configuration System

---