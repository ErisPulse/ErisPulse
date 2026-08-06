# Bug Tracker

This document records known bugs of the ErisPulse SDK and their fixes, arranged in chronological order by the version in which they were fixed.

> **To the Reader**
> No software is inherently perfect; even the most careful developers may leave small errors. The bugs listed here are all issues that have a practical impact on runtime—those that are too minor to even reach the "minor" severity level will not appear here. Although the list contains many "critical" items, the original intention of publicly documenting these bugs is to make troubleshooting and tracing smoother, not to create anxiety: problems that can be seen, recorded, and fixed are themselves proof that the project continues to improve. Do not feel anxious upon seeing this list; it is a troubleshooting tool, not a source of fear.

> **How to Read & Maintenance Guidelines**
> - Each bug record includes structured fields such as problem description, root cause analysis, affected version range, and fix solution. It is recommended to check whether the "affected version" covers your current version before upgrading.
> - If you need to add a new bug entry, please add content at the corresponding location, following the field specifications and severity/type classification described below.

---

Please directly return the complete translated Markdown content, without including any other text.

Once again, please note: if the document contains language switch lines (lines with language names separated by `` | ``), strictly follow the format requirements above in item 8, and do not write incorrect formats such as ``[**Label**](file)``.

## Field Descriptions

### Required Fields

| Field | Description |
|-------|-------------|
| **Issue** | The external manifestation of the bug, observable abnormal phenomena to the user. Provide error messages or typical scenarios whenever possible |
| **Root Cause** | Root cause analysis, pointing to specific code defects (including "root cause chain" diagrams for complex scenarios) |
| **Affected Versions** | The affected version range, in the format `introduced version - fixed version` (including both dev versions) |
| **Fixed Version** | The specific version number that fixed the bug |
| **Fix Description** | Brief description of the fix, including key code changes |
| **Fix Date** | The release date of the corresponding fixed version, in `YYYY/MM/DD` format |
| **Severity** | Mark according to the "Severity Classification" below |
| **Type** | Mark according to the "Type Classification" below, can be combined (e.g., `Adapter / Routing`) |

### Optional Fields

| Field | Description | Applicable Scenarios |
|-------|-------------|----------------------|
| **Reproduction Steps** | The minimal reproducible path to trigger the bug | For complex or intermittent bugs, it is recommended to supplement this |
| **References** | Links to related Issues / PRs / Commits | Supplement when there are external discussion records |
| **Regression Test** | Location of test cases to verify the fix and prevent recurrence | Supplement when corresponding pytest cases have been written |

---

Please directly return the complete translated Markdown content, without including any other text.

## Severity Levels

| Identifier | Level | Criteria | Typical Manifestations |
|------------|-------|---------|---------|
| 🔴 | Critical | Process crash, data loss/damage, core functionality completely unavailable, security vulnerabilities | OOM Kill, inability to send messages, module loading failure, hot reload failure |
| 🟡 | Medium | Functional anomalies but with workaround paths, non-core functionality failure, occasional issues | Incorrect state detection, repeated triggers, cache expiration, inaccurate error messages |
| 🟢 | Minor | Does not affect core functionality, only code quality or experience issues, potential risks not yet triggered | Deprecated APIs, dead code, missing warning logs |

## Type Classification

| Type | Coverage |
|------|---------|
| Configuration System | `ConfigManager`, configuration read/write, configuration Schema, hot reload |
| Event System | `Event` module (command/message/notice/request/meta), event dispatch, handler registration |
| Adapter | `AdapterManager`, `BaseAdapter`, account parsing, Bot status, middleware |
| Routing | `RouterManager`, HTTP/WebSocket/SSE routing, rate limiting, CORS |
| Client | `HttpClient`, `ClientWebSocket`, aiohttp wrapper |
| Storage | `StorageManager`, SQLite, SQL builder, nested keys |
| Loading System | `Loader`, `LazyModule`, `ModuleInitializer`, strict mode, module discovery |
| CLI | `epsdk` commands, `init`/`run`/`install`, argument parsing, signal handling |
| Runtime | `sdk.run`/`restart`/`uninit`, lifecycle, signals, subprocesses |

---

Please directly return the complete translated Markdown content without any additional text.

## Item Template

To add a new bug item, please follow the format below:

```markdown
### [BUG-XXX] Title

**Issue**: Problem description (error message or typical phenomenon)
**Root Cause**: Root cause analysis
**Affected Versions**: Introduced version - Fixed version
**Fixed Version**: x.x.x
**Fix Content**: Fix solution
**Fix Date**: YYYY/MM/DD

<!-- Optional fields -->
**Steps to Reproduce**: (Recommended for complex bugs)
**Related**: (Issue/PR links)
**Regression Test**: (Test case path)

**Severity**: 🔴 Critical | 🟡 Medium | 🟢 Minor
**Type**: Configuration System / Event System / Adapter / Routing / Client / Storage / Loading System / CLI / Runtime
```

---

Please directly return the complete translated Markdown content, without any additional text.

Once again, please note: if the document contains language switch lines (with language names separated by `` | ``), strictly adhere to the format requirements above in item 8, and do not write incorrect formats such as ``[**Label**](file)``.

## Statistics Overview

| Severity | Count |
|----------|-------|
| 🔴 Critical | 15 |
| 🟡 Medium | 12 |
| 🟢 Minor | 2 |
| **Total** | **29** |

| Type | Count |
|------|-------|
| Adapters | 6 |
| Configuration System | 6 |
| Event System | 5 |
| CLI | 3 |
| Storage | 3 |
| Loading System | 3 |
| Routing | 2 |
| Client | 1 |
| Runtime | 1 |

> Note: A single bug can belong to multiple types; the table above is counted by primary type.

---

Please directly return the complete translated Markdown content without any additional text.

Once again, please note: if the document contains a language switch line (with each language name separated by `` | ``), strictly follow the format requirement in item 8 above and do not write incorrect formats like ``[**Label**](file)``.

## Fixed Bugs

### [BUG-001] Event handler registered multiple times causing event to be processed multiple times

**Issue**: When registering handlers using multiple `@message` / `@notice` decorators, the same event is triggered multiple times, causing commands to be executed multiple times and logs to be output repeatedly.

**Cause**: `BaseEventHandler` lacks deduplication logic when registering handlers with the adapter event bus. Each decorator mounts the handler once to the bus, resulting in multiple calls during event distribution.

**Affected Versions**: 2.2.0-dev.0 - 2.2.1-dev.0

**Fixed Version**: 2.2.1-dev.0

**Fix**: Optimize `BaseEventHandler` to ensure each event type is registered only once with the adapter, preventing repeated triggers.

**Fix Date**: 2025/08/18

**Severity**: 🔴 Critical

**Type**: Event System

---

### [BUG-002] Init command adapter configuration path type error

**Issue**: When using the `ep init` command for interactive initialization, selecting the configuration adapter results in a type error:

```
Interactive initialization failed: unsupported operand type(s) for /: 'str' and 'str'
```

**Cause**: In version 2.3.7, when adjusting the configuration file path, method parameter types were inconsistent. `_configure_adapters_interactive_sync` receives `str` type parameters, but internally uses the `Path` `/` operator to concatenate paths.

**Affected Versions**: 2.3.7 - 2.3.9-dev.1

**Fixed Version**: 2.3.9-dev.1

**Fix**: Change the parameter type of `_configure_adapters_interactive_sync` from `str` to `Path`, passing `Path` objects directly when called.

**Fix Date**: 2026/03/23

**Severity**: 🟡 Medium

**Type**: CLI

---

### [BUG-003] Commands fail after restart

**Issue**: After calling `sdk.restart()`, commands registered via `@command` cannot be triggered, resulting in the robot not responding after sending a command.

**Cause**: `adapter.shutdown()` clears the event bus, but `BaseEventHandler`'s `_linked_to_adapter_bus` status is not reset to `False`, causing `_process_event` to believe it is already mounted to the adapter bus and skip re-registration.

**Affected Versions**: 2.2.x - 2.4.0-dev.2

**Fixed Version**: 2.4.0-dev.3

**Fix**: Introduce `_linked_to_adapter_bus` status tracking. After `_clear_handlers()` disconnects the bus, `register()` automatically re-registers next time, adapting to shutdown/restart scenarios.

**Fix Date**: 2026/04/09

**Severity**: 🔴 Critical

**Type**: Event System

---

### [BUG-004] Lifecycle event handlers not cleaned up

**Issue**: After `sdk.restart()`, old lifecycle event handlers still exist and are repeatedly triggered, causing the same event to be processed multiple times.

**Cause**: The `lifecycle._handlers` dictionary is never cleared during `uninit()`, leaving old and new handlers both active after restart.

**Affected Versions**: 2.3.0 - 2.4.0-dev.2

**Fixed Version**: 2.4.0-dev.3

**Fix**: Clear `lifecycle._handlers` at the end of the `Uninitializer` cleanup process (after all events are submitted).

**Fix Date**: 2026/04/09

**Severity**: 🟡 Medium

**Type**: Runtime

---

### [BUG-005] Event.is_friend_add/is_friend_delete detail_type inconsistent with OB12 standard

**Issue**: `Event.is_friend_add()` checks `detail_type == "friend_add"`, `Event.is_friend_delete()` checks `detail_type == "friend_delete"`, but the OneBot12 standard defines `detail_type` values as `"friend_increase"` and `"friend_decrease"`. This inconsistency with the values used in `notice.py`'s `on_friend_add`/`on_friend_remove` decorators causes handlers registered via decorators to fail when the corresponding `is_friend_add()`/`is_friend_delete()` methods return `False`.

**Cause**: `wrapper.py` uses non-standard naming, while `notice.py` uses correct OB12 standard naming.

**Affected Versions**: Since implementation

**Fixed Version**: 2.4.2-dev.1

**Fix**: Change the matching value of `is_friend_add()` from `"friend_add"` to `"friend_increase"`, and `is_friend_delete()` from `"friend_delete"` to `"friend_decrease"`.

**Fix Date**: 2026/04/13

**Severity**: 🟡 Medium

**Type**: Event System

---

### [BUG-006] adapter.clear() not clearing _started_instances causing incorrect state after restart

**Issue**: The `AdapterManager.clear()` method clears `_adapters`, `_adapter_info`, handlers, and `_bots`, but omits `_started_instances`. If `clear()` is called while adapters are running, `_started_instances` retains dangling references, causing incorrect state after restart.

**Cause**: When `_started_instances` was introduced in 2.4.0-dev.1, it was not cleared in `clear()`.

**Affected Versions**: 2.4.0-dev.1 - 2.4.2-dev.0

**Fixed Version**: 2.4.2-dev.1

**Fix**: Add `self._started_instances.clear()` in the `clear()` method.

**Fix Date**: 2026/04/13

**Severity**: 🟡 Medium

**Type**: Adapter

---

### [BUG-007] command.wait_reply() uses deprecated asyncio.get_event_loop()

**Issue**: The `CommandHandler.wait_reply()` method uses `asyncio.get_event_loop()` to create futures and get timestamps. This method is deprecated in Python 3.10+ and should use `asyncio.get_running_loop()` in asynchronous contexts. It is inconsistent with `get_running_loop()` used in the `wait_for()` method in the same file, `wrapper.py`.

**Cause**: The old API was used during development, and the newly added `wait_for()` method used the correct API but did not retroactively fix the old code.

**Affected Versions**: 2.3.0-dev.0

**Fixed Version**: 2.4.2-dev.1

**Fix**: Replace `asyncio.get_event_loop()` with `asyncio.get_running_loop()` in two places in `command.py`.

**Fix Date**: 2026/04/13

**Severity**: 🟢 Minor

**Type**: Event System

---

### [BUG-008] Bot offline event repeatedly submitted during shutdown

**Issue**: When calling `adapter.shutdown()` to shut down all adapters, `_update_bot_status()` repeatedly submits Bot offline events during the shutdown process, causing the same batch of Bots to be marked offline multiple times and triggering the `adapter.bot.offline` lifecycle event multiple times.

**Cause**: The Bot status tracking system introduced in 2.4.0-dev.1 does not set a "shutting down" flag during `shutdown()`, so `_update_bot_status()` cannot distinguish between normal offline and cascade offline during shutdown.

**Affected Versions**: 2.4.0-dev.1 - 2.4.2-dev.1

**Fixed Version**: 2.4.2-dev.1

**Fix**: Add `_is_being_shutdown` flag in `AdapterManager`. Set it to True at the start of `shutdown()` and clear it at the end; `_update_bot_status()` checks this flag and skips duplicate submissions during shutdown.

**Fix Date**: 2026/04/21

**Severity**: 🟡 Medium

**Type**: Adapter

---

### [BUG-009] LazyModule synchronous access to BaseModule causing incomplete initialization

**Issue**: When users access lazy-loaded BaseModule attributes in synchronous contexts, the module uses `loop.create_task()` for asynchronous initialization but does not await it, leading to race conditions when attributes are accessed before initialization completes.

**Cause**: `_ensure_initialized()` uses `loop.create_task(self._initialize())` and returns immediately without ensuring initialization completes.

**Affected Versions**: 2.4.0-dev.0 - 2.4.2-dev.1

**Fixed Version**: 2.4.2-dev.2

**Fix**: In synchronous contexts, BaseModule initialization is changed to use `asyncio.run(self._initialize())`, ensuring initialization completes before returning. The transparent proxy feature is maintained, so users do not need to be aware of synchronous/asynchronous differences.

**Fix Date**: 2026/04/21

**Severity**: 🟡 Medium

**Type**: Loading System

---

### [BUG-010] Multi-threaded configuration system writing causing data loss

**Issue**: In multi-threaded environments, when multiple threads call `config.setConfig()` simultaneously, the `_flush_config()` read-modify-write operation is not atomic, leading to potential partial write loss.

**Cause**: Although `_flush_config()` uses `RLock`, there is no file lock protection between file read and write, and `_schedule_write`'s Timer may be triggered multiple times causing overwrites.

**Affected Versions**: 2.3.0 - 2.4.2-dev.1

**Fixed Version**: 2.4.2-dev.2

**Fix**:
1. Add file lock mechanism (`_file_lock`) to ensure atomic file operations
2. Use atomic rename after writing to a temporary file (`os.replace`/`os.rename`)
3. Improve `_schedule_write` Timer cancellation and rescheduling logic

**Fix Date**: 2026/04/21

**Severity**: 🔴 Critical

**Type**: Configuration System

---

### [BUG-011] Windows Ctrl+C unable to stop program

**Issue**: When running `python main.py` directly on Windows, pressing Ctrl+C does not terminate the program. After the program starts normally and outputs the router server information, Ctrl+C has no response and can only be forcibly killed via Task Manager. However, it can stop normally when started via `epsdk run`, which runs through a subprocess model.

**Cause**: The `serve()` function of the Hypercorn ASGI server registers its own SIGINT handler internally, overriding Python's default `KeyboardInterrupt` handling mechanism. When Hypercorn is started as a background task via `asyncio.create_task()`, its internal shutdown process cannot be triggered normally (because it expects the `worker_serve` mode), causing the Ctrl+C signal to be swallowed by Hypercorn without triggering any cleanup actions.

**Affected Versions**: 2.3.6 - 2.4.2

**Fixed Version**: 2.4.3-dev.0

**Fix**:
1. Switch ASGI server from Hypercorn to Uvicorn (`pyproject.toml` dependency change)
2. Start the server directly using `uvicorn.Server._serve()`, bypassing the `capture_signals()` signal handling context manager
3. Implement graceful shutdown via `server.should_exit = True`, canceling background tasks if timeout occurs
4. Simultaneously remove the subprocess running model and `runtime/cleanup.py` cleanup module (subprocess cleanup mechanism no longer needed)

**Fix Date**: 2026/04/28

**Severity**: 🔴 Critical

**Type**: CLI / Runtime

---

### [BUG-012] Hot restart after module update does not take effect

**Issue**: After executing `sdk.restart()` for a soft restart, the new code (such as new API routes) of modules/adapters upgraded via `epsdk install` does not take effect and old logic is still running. The latest code can only be loaded by fully restarting the process.

**Cause**: `_do_restart()` calls `entry_point.load()` during re-initialization, but this function returns cached old module objects from `sys.modules` instead of reloading from disk.

**Affected Versions**: Early versions - 2.4.3-dev.1

**Fixed Version**: 2.4.3-dev.1

**Fix**: Clear the cache of loaded modules/adapters packages in `sys.modules` after `uninit()` and before `init()` to ensure `entry_point.load()` loads the latest code from disk. Add auxiliary methods `_collect_top_level_modules()` and `_invalidate_module_cache()` to derive top-level module names via `top_level.txt` or entry-point value.

**Fix Date**: 2026/05/03

**Severity**: 🔴 Critical

**Type**: Loading System / Runtime

---

### [BUG-013] Module loading strategy sorting logic error

**Issue**: `ModuleLoadStrategy` provides a `priority` field to declare module initialization priority, but the implementation of the loading strategy has an error, causing modules to be initialized in an unexpected order instead of the intended priority order. Modules are loaded in the default order of `entry_points()`. When modules have initialization dependencies, the correct initialization order cannot be ensured through `priority`.

**Cause**: The sorting logic in the implementation of the loading strategy is incorrect; `initialize_modules()` does not sort the module list by `priority`.

**Affected Versions**: 2.3.4 - 2.4.5-dev.2

**Fixed Version**: 2.4.5-dev.3

**Fix**: Sort the module list by `priority` in descending order before traversing `initialize_modules()`. Modules with the same priority maintain their original relative order (stable sorting).

**Fix Date**: 2026/05/15

**Severity**: 🟡 Medium

**Type**: Loading System

---

### [BUG-014] Adapter middleware returning None causing event data loss

**Issue**: During the execution of the OneBot12 middleware chain in `adapter.emit()`, if a middleware returns `None` (e.g., forgetting to `return data`), the `processed_data` received by subsequent middleware and all event handlers becomes `None`, causing event processing to fail completely.

**Cause**: The implementation of the middleware chain `processed_data = await middleware(processed_data)` does not check if the return value is `None`, directly overwriting the result of the previous step.

**Affected Versions**: unknown - 2.4.5-dev.3

**Fixed Version**: 2.4.5-dev.4

**Fix**: When middleware returns `None`, ignore the return value, retain the original data, and output a warning-level log.

**Fix Date**: 2026/05/15

**Severity**: 🔴 Critical

**Type**: Adapter / Event System

---

### [BUG-015] Configuration file path depends on working directory

**Issue**: The configuration file path of `ConfigManager` is a relative path `"config/config.toml"` by default, which is resolved at runtime using `os.getcwd()`. If the working directory changes during runtime (e.g., via `os.chdir()`), read/write operations on the configuration file will point to the wrong location, causing configuration loss or reading old data.

**Cause**: The relative path is stored directly in `__init__` without being resolved to an absolute path at initialization.

**Affected Versions**: 2.3.7 - 2.4.5-dev.3

**Fixed Version**: 2.4.5-dev.4

**Fix**: In `ConfigManager.__init__()`, if the passed path is relative, automatically resolve it to an absolute path using `os.path.abspath()`.

**Fix Date**: 2026/05/15

**Severity**: 🟡 Medium

**Type**: Configuration System

---

### [BUG-016] BaseStorage confuses storing value None with key not existing

**Issue**: `BaseStorage.get_multi()` / `__getattr__()` cannot distinguish between "key does not exist" and "key's value is None", treating explicitly stored `None` as if the key does not exist.

**Cause**: The retrieval logic directly uses `value is None` to check if the key exists, lacking an independent "missing" marker.

**Affected Versions**: Early versions - 2.4.6-dev.6

**Fixed Version**: 2.4.6-dev.6

**Fix**: Introduce `_SENTINEL` sentinel value to distinguish between "key does not exist" and "value is None", no longer confusing the two.

**Fix Date**: 2026/06/07

**Severity**: 🟡 Medium

**Type**: Storage

---

### [BUG-017] WebSocket route auto_accept flag lost after service restart

**Issue**: After service restart (e.g., `sdk.restart()`), the `auto_accept` configuration of all WebSocket routes reverts to `False`, causing connections that were expected to be automatically accepted to hang, and clients remain unresponsive for a long time, resulting in a stuck WebSocket connection.

**Cause**: `_restore_routes_from_records()` hardcodes `auto_accept` to `False` when restoring routes from persistent records, not reading the original record's value; also, when the route storage tuple expanded from a binary tuple to a ternary tuple, the restoration logic was not synchronized.

**Affected Versions**: 2.3.8-dev.0 - 2.4.6-dev.6

**Fixed Version**: 2.4.6-dev.6

**Fix**: Route storage tuple expanded to `(handler, auth_handler, auto_accept)`, `_restore_routes_from_records()` reads the real `auto_accept` value from the record instead of hardcoding `False`.

**Fix Date**: 2026/06/07

**Severity**: 🔴 Critical

**Type**: Routing

---

### [BUG-018] HTTP/WS client concurrent calls causing crash and connection leak

**Issue**: The HTTP and WebSocket clients in `Core/client.py` have multiple stability defects in concurrent scenarios, leading to connection leaks or process crashes:
- Multiple coroutines calling `ClientWebSocket.receive()` concurrently cause aiohttp to throw `Concurrent call to receive() is not allowed`
- Concurrent calls to `_get_http_session()` / `_get_ws_session()` may create multiple sessions, and `_drain_sessions()` does not close old connections, causing connection leaks
- The exception handling order in `request()` is incorrect: `except ClientConnectionError` (ErisPulse exception) is never triggered, aiohttp connection errors are caught by the generic `except Exception`, causing the "retry connection + session reinitialization" logic (dead code) to never execute
- `send_json()` ignores the `mode="binary"` parameter; `_get_ws_session()` does not pass default request headers

**Cause**: The client's initial implementation (2.4.6-dev.5) lacks concurrent protection and exception classification, and improperly handles the inheritance relationship between aiohttp exception system and ErisPulse custom exceptions.

**Affected Versions**: 2.4.6-dev.5 - 2.4.8

**Fixed Version**: 2.4.8

**Fix**:
1. Add `_recv_lock` to serialize all `receive()` / `receive_text()` / `receive_bytes()` calls
2. Add `_session_lock` to protect session creation; `_drain_sessions()` is changed to an asynchronous method and truly closes old sessions
3. Refactor `request()` exception handling order: `asyncio.TimeoutError` → `aiohttp.ClientConnectionError` (triggers session reinitialization) → `aiohttp.ClientError` → `ClientError` (transparent pass) → `Exception`
4. Fix `send_json()` mode handling, `_get_ws_session()` default request header pass, `close()` concurrent race condition, `HttpResponse.__aexit__` duplicate `release()`

**Fix Date**: 2026/06/12

**Severity**: 🔴 Critical

**Type**: Client

---

### [BUG-019] Adapter hot reload causes route conflict and reload failure

**Issue**: When a third-party module (e.g., Dashboard) triggers adapter hot reload or adapter startup fails and retries, due to the old routes (e.g., `onebot11_default`) not being cleared from the previous registration, a `WebSocket path ... already registered` conflict is thrown, causing reload failure. A complete process restart is required to recover.

**Cause**: `AdapterManager.shutdown()` only clears routes with `unregister_all_by_namespace(platform)`, but adapters (e.g., OneBot11) register WebSocket routes with the namespace `onebot11_{account_name}`, resulting in a granularity mismatch and making the cleanup an empty operation; startup failure retry paths also do not clear the remaining routes from the previous attempt.

**Affected Versions**: Early versions - 2.4.9

**Fixed Version**: 2.4.9

**Fix**:
1. Automatically track `owner → namespace` ownership relationships during route registration via `current_owner` ContextVar
2. Add `unregister_all_by_owner(owner)`, which clears routes by owner during stop/restart, covering fine-grained namespaces
3. Add the `_stop_adapter(platform)` primitive ("stop equals cleanup"), binding stopping the adapter and reclaiming its registered resources in a single call; `restart()` and startup failure retry both go through this entry point
4. Add the framework-level `adapter.restart(platform)` API, which third-party modules should call instead of directly operating the adapter instance

**Fix Date**: 2026/06/12

**Severity**: 🔴 Critical

**Type**: Adapter / Routing

---

### [BUG-020] Subprocess mode `ep run <script>` cannot find sub-packages in the script's directory

**Issue**: When running a script using `ep r .\main.py` in non-hot-reload mode, if the script has relative imports (e.g., `from qg import ...`), it reports a `No module named 'qg'` error. However, the `--reload` mode works normally.

**Cause**: The non-hot-reload mode directly calls `runpy.run_path()` to execute the script, which does not automatically add the script's directory to `sys.path`. In contrast, the `--reload` mode runs via `subprocess.Popen` as a subprocess, which automatically inherits the current working directory, making `sys.path[0]` the script's directory, so it works normally.

**Affected Versions**: 2.5.0 - 2.5.2-dev.0

**Fixed Version**: 2.5.2-dev.0

**Fix**: Before calling `runpy.run_path()`, manually insert the script's directory into `sys.path[0]`.

**Fix Date**: 2026/06/27

**Severity**: 🟡 Medium

**Type**: CLI

---

### [BUG-021] SQL query builder rejects valid wildcard and list expressions

**Issue**: `SQLiteQueryBuilder`'s `_build_select_sql()` calls `_validate_identifier()` for all SELECT columns, which uses a strict whitelist regex `^[a-zA-Z_][a-zA-Z0-9_]*$`, causing legitimate SQL syntax to be incorrectly judged as unsafe column names:
- `SELECT *` — `*` is a standard SQL wildcard
- `SELECT COUNT(*)` — aggregate function
- `SELECT users.name` — qualified column name
- `SELECT col AS alias` — column alias

Among these, `Select("*")` is used by modules like Cron, causing module `on_load` execution to fail and the module to fail to load.

**Cause**: In version 2.4.6, SQL injection protection was enhanced, introducing `_validate_identifier()` whitelist validation. This validation is applied to all column names, but not differentiated between read-side (SELECT/ORDER BY) and write-side (INSERT/UPDATE). SELECT columns allow complex SQL expressions and should not be restricted by simple identifier whitelists.

**Affected Versions**: 2.4.6 - 2.5.2-dev.1

**Fixed Version**: 2.5.2-dev.2

**Fix**: Change the column validation for SELECT/ORDER BY from whitelist mode to blacklist mode:
1. Add `_validate_select_column()` function, which only blocks SQL injection dangerous characters (`;` `'` `"` `--` `/*` `*/` `\x00` newline)
2. Allow any valid SQL column expressions (`*`, `table.*`, `table.column`, `COUNT(*)`, `col AS alias`, etc.)
3. INSERT/UPDATE column names still maintain strict whitelist validation (only allow simple identifiers)

**Fix Date**: 2026/06/29

**Severity**: 🔴 Critical

**Type**: Storage

---

### [BUG-022] _resolve_account() account resolution regression (_accounts_data not filled)

**Issue**: After the configuration system was refactored in 2.5.2, multi-account adapters declaring `AccountConfigClass` report `ValueError("AccountConfigClass not declared, unable to resolve account")` when calling methods that require sending messages, such as `wait_reply`, `reply`. Even though the adapter correctly configured multi-account information, account resolution still fails.

**Cause**: In 2.5.2-dev.5, `_load_accounts()` (which reads configuration + validates + fills `_accounts_data`) was refactored into `_ensure_accounts_exist()` (which only generates configuration templates), but `_resolve_account()` still checks `self._accounts_data is None`. Since `_ensure_accounts_exist()` no longer fills `_accounts_data`, this attribute remains `None`, causing `_resolve_account()` to prematurely return `(None, None)`, and account resolution fails completely.

**Root Cause Chain**:
```
_load_accounts() was deleted
  → __init__ no longer fills _accounts_data
    → _accounts_data remains None
      → _resolve_account() checks _accounts_data is None → return (None, None)
        → Downstream places calling _resolve_account() (e.g., call_api) get None
          → Trigger error
```

**Affected Versions**: 2.5.2-dev.5 - 2.5.2

**Fixed Version**: 2.5.3

**Fix**: In `BaseAdapter.__init__`, after `_ensure_accounts_exist()`, restore the filling of `_accounts_data`:
```python
if self.AccountConfigClass is not None:
    self._ensure_accounts_exist()
    self._accounts_data = self.accounts  # Restore filling, data source is real-time read accounts attribute
```
The `_resolve_account()` logic remains unchanged, fully backward compatible:
- Adapters not declaring `AccountConfigClass`: `_accounts_data` remains `None` → return `(None, None)`
- Adapters declaring `AccountConfigClass`: `_accounts_data` is filled → normal resolution
- Adapters overwriting `_load_accounts` or manually setting `_accounts_data`: overwrite after `super().__init__()`, highest priority

**Fix Date**: 2026/07/07

**Severity**: 🔴 Critical

**Type**: Adapter / Configuration System

---

### [BUG-023] Adapter cache not refreshed after account configuration change causing account resolution failure

**Issue**: After users modify the account configuration of multi-account adapters (e.g., filling in token) via Dashboard, the adapter still uses the old cache, and calls to message-sending-related methods report `Account not found (account_id=default)`. The process must be restarted for the new configuration to take effect.

**Cause**: `_accounts_data` is only read from the configuration storage once during `BaseAdapter.__init__`, and is never refreshed afterward. `AdapterManager._run_adapter()` and `restart()` do not re-read the account configuration before calling `adapter.start()`, causing the cache to be out of sync with the actual configuration.

**Affected Versions**: 2.4.6 - 2.5.4

**Fixed Version**: 2.5.4

**Fix**: In `AdapterManager._run_adapter()` and `restart()`, before calling `adapter.start()`, refresh `adapter._accounts_data = adapter.accounts` to ensure the latest configuration is used each time it starts.

**Fix Date**: 2026/07/09

**Severity**: 🔴 Critical

**Type**: Adapter / Configuration System

---

### [BUG-024] storage.set() writing large numeric ID keys triggers OOM Kill

**Issue**: When calling `storage.set()` to write a nested key path containing a large numeric field (e.g., QQ group ID `871684833`), the process is killed by the container OOM (exit code -9), causing the service to crash and become unrecoverable.

**Cause**: In the recursive implementation of `_set_nested_value`, pure numeric fields in the nested key path are mistakenly identified as list indices by `isdigit()`, triggering `current.extend([None] * (index - len(current) + 1))`, attempting to allocate a list with hundreds of millions of elements, instantly exhausting memory.

**Root Cause Chain**:
```
Key path contains pure numeric field (e.g., group ID 871684833)
  → isdigit() mistakenly identifies as array index
    → extend([None] * (871684833 - len(current) + 1))
      → Attempts to allocate hundreds of millions of elements
        → Memory exhausted → container OOM Kill (exit code -9)
```

**Affected Versions**: 2.5.1 - 2.5.5

**Fixed Version**: 2.5.5

**Fix**:
1. Always use a dictionary when pre-creating intermediate layers, never guess the container type based on whether the next segment is a number
2. When setting the final value, only handle indexing if the container itself is a list and the index is less than `STORAGE_MAX_LIST_INDEX` (10000); skip large indices safely
3. Change the recursive implementation to an iterative one, eliminating the potential for infinite recursion in the original code
4. Add `STORAGE_MAX_LIST_INDEX` constant to `Core/constants.py`, centrally managing the safe index upper limit

**Fix Date**: 2026/07/10

**Reproduction Steps**:
```python
# Trigger by writing a nested key path containing a large number field (e.g., QQ group ID)
await sdk.storage.aset("groups.871684833.name", "Some group")
# → Process memory spikes instantly, killed by OOM
```

**Regression Tests**: `tests/unit/test_unit_storage.py` adds 4 regression test cases
- `test_nested_key_numeric_segment_as_dict_key` — precisely reproduces the OOM scenario
- `test_nested_key_numeric_segment_multiple` — multiple consecutive numeric fields as dictionary keys
- `test_nested_key_existing_list_index_set_within_limit` — existing list index write within limit
- `test_nested_key_list_index_safety_limit` — safety limit verification for large indices

**Severity**: 🔴 Critical

**Type**: Storage

---

### [BUG-025] on_config_update callback not core-routed

**Issue**: `on_config_update(old, new)` callback is defined in the base class (`BaseModule` / `BaseAdapter`), but the core framework does not associate it with configuration change events. The actual behavior is: when changing configuration through the configuration management panel, it can be triggered, but when manually editing `config.toml` or calling `setConfig()` in code, `on_config_update` is not triggered.

**Cause**: `ConfigManager` emits `config.set` / `config.updated` lifecycle events when configuration changes, but lacks subscription logic to forward these events to each component's `on_config_update` method.

**Root Cause Chain**:
```
Core does not subscribe to config.set / config.updated
  → Configuration change events are not forwarded
    → on_config_update is not called
      → Manual file editing / code setConfig does not trigger hot update callback
```

**Affected Versions**: All versions

**Fixed Version**: 2.6.2

**Fix**: `ModuleManager` / `AdapterManager` register subscriptions for `config.set` (covering code `setConfig()` path) and `config.updated` (covering manual file editing path), match by configuration key prefix and call the corresponding component's `on_config_update`, passing type-safe configuration objects. Also fix `_flush_config()` not synchronizing `_config_mtime` after writing the file, preventing the framework's own write from being mistakenly detected as an external modification by the file monitoring task and repeatedly triggering `config.updated`.

**Compatibility Note**: Configuration hot updates are now maintained by the core framework. The logic previously triggered by the configuration management panel has been removed, and upgrading the framework requires upgrading the configuration management panel as well, otherwise duplicate triggers (core + panel each called once) will occur. The `on_config_update` method signature and semantics remain unchanged, and subclasses do not need modification.

**Fix Date**: 2026/07/23

**Severity**: 🟡 Medium

**Type**: Configuration System

---

### [BUG-026] notice/request event reply target inferred incorrectly

**Issue**: When calling `event.reply()` in a group notice event (e.g., member joining group `group_member_increase`), the message is sent to the user who triggered the event, not the group where the event occurred. The same issue occurs with friend notice events, where the reply target may be misdirected.

**Cause**: `infer_receive_type()` directly returns the event's `detail_type` as the session type. For message events, this is correct (`detail_type` values `private`/`group` are session types), but for notice/request events, `detail_type` is a semantic subtype (e.g., `group_member_increase`, `friend_increase`), not a session type. Subsequent `convert_to_send_type()` and `get_id_field()` cannot find this value in the mapping table, defaulting to `"user"` / `"user_id"`, causing the reply target to be misdirected.

**Root Cause Chain**:
```
notice event detail_type="group_member_increase"
  → infer_receive_type() directly returns "group_member_increase"
    → convert_to_send_type("group_member_increase") not in mapping table → default to "user"
    → get_id_field("group_member_increase") not in mapping table → default to "user_id"
      → target_id = event["user_id"]  ← New member's private chat (not the group)
```

**Affected Versions**: All versions

**Fixed Version**: 2.7.0-dev.3

**Fix**: `infer_receive_type()` adds a check—only return `detail_type` directly as the session type if it is a known session type (standard or custom type); otherwise, infer the correct session type based on the ID field (`group_id` / `channel_id` / `user_id`, etc.).

**Regression Tests**: `tests/unit/test_unit_session_type.py` → `TestNoticeRequestTypeInference` (10 test cases)

**Fix Date**: 2026/07/29

**Severity**: 🟢 Minor

**Type**: Event System

---

### [BUG-027] Route rate limiting cleanup task uses fixed window causing long window rate limit rules to fail

**Issue**: When setting route rate limiting to a long window rule (e.g., `100/hour`, `{"requests": 100, "window": 3600}`), the rate limiting is essentially ineffective—actual performance is similar to `100/minute` (up to about 6000 requests per hour can be passed), completely failing to provide the expected hourly protection.

**Cause**: `_apply_rate_limit` parses the actual `window` for each route (up to 3600 seconds), and per-request checks do use this window; however, the background cleanup task `_cleanup_expired_rate_limits` uses a fixed constant `DEFAULT_RATE_LIMIT_WINDOW_SECS` (60 seconds) as the unified cleanup threshold for all routes. Thus, time stamps earlier than 60 seconds in the `100/hour` route are cleared by the cleanup task prematurely, preventing the hourly window from ever accumulating close to 100 records, severely weakening the rate limiting.

**Root Cause Chain**:
```
_apply_rate_limit parses window=3600 (100/hour)
  → per-request check uses 3600s retention time (correct)
  → but _cleanup_expired_rate_limits uses fixed max_window=60s for cleanup
    → Time stamps earlier than 60 seconds are cleared
      → The hourly window always retains only records from the last 1 minute
        → 100/hour effectively degrades to ~100/minute (relaxed by about 60 times)
```

**Affected Versions**: 2.6.0-dev.0 - 2.7.0-dev.4

**Fixed Version**: 2.7.0-dev.5

**Fix**: Add `_rate_limit_windows: dict[str, int]` to record the actual window for each store key; write the window when `_apply_rate_limit` first creates an entry; `_cleanup_expired_rate_limits` changes to clean up by each key's own window (fallback to default value if missing); maintain both dictionaries in sync with cleanup and `stop()`.

**Fix Date**: 2026/07/31

**Regression Tests**: `tests/unit/test_unit_router.py` → `TestRateLimit::test_cleanup_respects_per_route_window`

**Severity**: 🔴 Critical

**Type**: Routing

---

### [BUG-029] Configuration listener task broadcasts incomplete TOML and silently swallows exceptions

**Issue**: When users manually edit `config.toml` and save it halfway (producing a transient syntax error), the configuration listener background thread detects mtime changes, reloads the configuration, but after the load fails, it still broadcasts an empty configuration `{}` via the `config.updated` event, causing adapters/modules' `on_config_update` to receive an empty configuration and mistakenly assume all configuration items have been cleared, reverting to default values. Additionally, the listener loop uses `except Exception: pass` to silently swallow all exceptions, making it impossible to diagnose watcher faults.

**Cause**: Two defects overlap:
1. `_load_config` overwrites `self._cache` to `{}` when TOML syntax errors/permission errors occur, but the background listener thread `_watch_loop` and cache timeout path `_check_cache_validity` both unconditionally execute `_emit_config_updated()` after calling `_load_config()`, broadcasting the "empty cache produced by load failure" as a real change.
2. `_watch_loop`'s `except Exception: pass` does not log any messages.

**Root Cause Chain**:
```
User saves halfway → TOML syntax error
  → _load_config() overwrites _cache = {}
    → _watch_loop unconditionally _emit_config_updated(new_config={})
      → Adapters/modules on_config_update receive empty configuration
        → Mistakenly assume configuration has been cleared, revert to default values
```

**Affected Versions**: 2.6.2-dev.1 - 2.7.0-dev.4

**Fixed Version**: 2.7.0-dev.5

**Fix**:
1. Change `_load_config` to return `bool`; on TOML syntax errors/permission errors/other errors, retain the previous valid cache (do not overwrite to `{}`), only record diagnostic logs and return `False`
2. Only emit `config.updated` in `_watch_loop` and `_check_cache_validity` if `_load_config()` returns `True`
3. Change `_watch_loop`'s `except Exception` to log at warning level (add i18n key `core.config.watcher_error`, synchronized in five languages)

**Fix Date**: 2026/07/31

**Regression Tests**: `tests/unit/test_unit_config.py` → `test_malformed_toml_preserves_last_valid_cache`, `test_permission_denied_logs_clear_message` (updated to validate cache retention + return False)

**Severity**: 🟡 Medium

**Type**: Configuration System

---

### [BUG-030] Configuration watcher race condition causing setConfig delayed write silently drops data

**Issue**: Multiple users reported that after using `config.setConfig(key, value)` (default `immediate=False`), their module configuration was not written to `config.toml`, while other module configurations were normal. Setting `immediate=True` (force flush) can avoid this. The manifestation is: configuration written during runtime is lost after the next restart, while configuration generated during startup remains.

**Cause**: Two overlapping defects:
1. **Logical defect**: `_watch_loop` unconditionally `_dirty_keys.clear()` and discards all pending write keys when `_check_file_change()` returns `True`. However, `_check_file_change()` only compares mtime with `!=`, and the framework's own `_flush_config` writing also changes mtime—although `_flush_config` updates `_config_mtime` after writing, the watcher thread may still observe mtime differences between file writing and mtime assignment (and on coarse-grained file systems), mistakenly judging it as "external modification" and clearing all pending write keys.
2. **Thread defect**: `_watch_loop` operates `_write_timer`/`_dirty_keys` without holding `_lock`, creating data races with `setConfig` (holding lock to write `_dirty_keys`), `_schedule_write` (holding lock to write `_write_timer`).

**Root Cause Chain**:
```
Module A setConfig(immediate=True) → flush writes, mtime changes
  → User module setConfig(immediate=False) → enters _dirty_keys, flushes after 5s
    → Watcher polls, _check_file_change observes mtime difference from its own previous write
      → _dirty_keys.clear() → User module's pending write keys are silently discarded
        → Configuration missing after restart
```

**Affected Versions**: 2.6.0 - 2.7.0

**Fixed Version**: 2.7.1

**Fix**:
1. Add `_last_self_write_mtime` field; `_flush_config` records it after writing; `_check_file_change` compares this value first when mtime changes, if matches, judges as its own write and returns `False`
2. Hold `_lock` for the entire `_watch_loop`; retain `_dirty_keys` for truly external modifications (merge semantics), next flush merges with external content (dirty keys have priority), no longer `clear()`
3. `getConfig`/`_check_cache_validity` paths are unaffected (their reload does not clear dirty keys)

**Fix Date**: 2026/08/06

**Regression Tests**: `tests/unit/test_unit_config.py` → `test_self_write_not_detected_as_external`, `test_external_change_preserves_dirty_keys`, `test_flush_merges_dirty_with_external`

**Severity**: 🔴 Critical

**Type**: Configuration System