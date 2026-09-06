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
| 🟡 Moderate | 13 |
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

> Note: A single bug may belong to multiple types, the above table is counted by primary type.

---

## Fixed Bugs

### [BUG-001] Event handler registered multiple times causes event to be processed multiple times

**Issue**: When registering multiple handlers using decorators such as `@message` / `@notice`, the same event is triggered multiple times, causing commands to be executed multiple times and logs to be output repeatedly.

**Cause**: The `BaseEventHandler` lacks deduplication logic when registering handlers with the adapter event bus. Each decorator mounts the handler once, leading to multiple calls during event dispatch.

**Affected Versions**: 2.2.0-dev.0 - 2.2.1-dev.0

**Fixed Version**: 2.2.1-dev.0

**Fix**: Optimize `BaseEventHandler` to ensure each event type is registered only once with the adapter, preventing repeated triggering.

**Fix Date**: 2025/08/18

**Severity**: 🔴 Severe

**Type**: Event System

---

### [BUG-002] Init command adapter configuration path type error

**Issue**: When using the `ep init` command for interactive initialization, selecting the configuration adapter causes a type error:

```
Interactive initialization failed: unsupported operand type(s) for /: 'str' and 'str'
```

**Cause**: In version 2.3.7, when adjusting the configuration file path, the method parameter types were inconsistent. The `_configure_adapters_interactive_sync` method receives a `str` type parameter, but internally uses the `Path` `/` operator to concatenate paths.

**Affected Versions**: 2.3.7 - 2.3.9-dev.1

**Fixed Version**: 2.3.9-dev.1

**Fix**: Change the parameter type of the `_configure_adapters_interactive_sync` method from `str` to `Path`, and pass a `Path` object directly during the call.

**Fix Date**: 2026/03/23

**Severity**: 🟡 Moderate

**Type**: CLI

---

### [BUG-003] Command event invalid after restart

**Issue**: After calling `sdk.restart()`, commands registered via `@command` cannot be triggered, resulting in the robot not responding after sending a command.

**Cause**: After `adapter.shutdown()` clears the event bus, the `_linked_to_adapter_bus` status of `BaseEventHandler` is not reset to `False`, causing the `_process_event` method to believe it has been mounted to the adapter bus and skip re-mounting.

**Affected Versions**: 2.2.x - 2.4.0-dev.2

**Fixed Version**: 2.4.0-dev.3

**Fix**: Introduce `_linked_to_adapter_bus` status tracking. After `_clear_handlers()` disconnects from the bus, `register()` automatically re-mounts next time, adapting to shutdown/restart scenarios.

**Fix Date**: 2026/04/09

**Severity**: 🔴 Severe

**Type**: Event System

---

### [BUG-004] Lifecycle event handler not cleaned up

**Issue**: After `sdk.restart()`, old lifecycle event handlers still exist and trigger repeatedly, causing the same event to be processed multiple times.

**Cause**: The `lifecycle._handlers` dictionary is never cleared during `uninit()`, so old and new handlers both exist after restart.

**Affected Versions**: 2.3.0 - 2.4.0-dev.2

**Fixed Version**: 2.4.0-dev.3

**Fix**: Clear `lifecycle._handlers` at the end of the `Uninitializer` cleanup process (after all events are submitted).

**Fix Date**: 2026/04/09

**Severity**: 🟡 Moderate

**Type**: Runtime

---

### [BUG-005] Event.is_friend_add/is_friend_delete detail_type inconsistent with OB12 standard

**Issue**: `Event.is_friend_add()` checks `detail_type == "friend_add"`, `Event.is_friend_delete()` checks `detail_type == "friend_delete"`, but the OneBot12 standard defines `detail_type` values as `"friend_increase"` and `"friend_decrease"`. This inconsistency with the values used in `notice.py`'s `on_friend_add`/`on_friend_remove` decorators causes the corresponding `is_friend_add()`/`is_friend_delete()` judgment methods to return `False` when handlers registered via decorators are triggered.

**Cause**: `wrapper.py` uses non-standard naming, while `notice.py` uses the correct OB12 standard naming.

**Affected Versions**: Implemented since the beginning

**Fixed Version**: 2.4.2-dev.1

**Fix**: Change the matching value of `is_friend_add()` from `"friend_add"` to `"friend_increase"`, and `is_friend_delete()` from `"friend_delete"` to `"friend_decrease"`.

**Fix Date**: 2026/04/13

**Severity**: 🟡 Moderate

**Type**: Event System

---

### [BUG-006] adapter.clear() does not clean _started_instances causing incorrect state after restart

**Issue**: The `AdapterManager.clear()` method clears `_adapters`, `_adapter_info`, handlers, and `_bots`, but omits `_started_instances`. If `clear()` is called while the adapter is running, `_started_instances` retains dangling references, causing incorrect state judgment after restart.

**Cause**: When `_started_instances` was introduced in 2.4.0-dev.1, it was not cleared synchronously in `clear()`.

**Affected Versions**: 2.4.0-dev.1 - 2.4.2-dev.0

**Fixed Version**: 2.4.2-dev.1

**Fix**: Add `self._started_instances.clear()` in the `clear()` method.

**Fix Date**: 2026/04/13

**Severity**: 🟡 Moderate

**Type**: Adapter

---

### [BUG-007] command.wait_reply() uses deprecated asyncio.get_event_loop()

**Issue**: The `CommandHandler.wait_reply()` method uses `asyncio.get_event_loop()` to create futures and get timestamps. This method is deprecated in Python 3.10+ and should use `asyncio.get_running_loop()` in asynchronous contexts. It is inconsistent with the `wait_for()` method in the same file `wrapper.py`, which uses `get_running_loop()`.

**Cause**: The old API was used during development, and the newly added `wait_for()` method used the correct API but did not retroactively fix the old code.

**Affected Versions**: 2.3.0-dev.0

**Fixed Version**: 2.4.2-dev.1

**Fix**: Replace two instances of `asyncio.get_event_loop()` in `command.py` with `asyncio.get_running_loop()`.

**Fix Date**: 2026/04/13

**Severity**: 🟢 Minor

**Type**: Event System

---

### [BUG-008] Bot offline event is repeatedly submitted during shutdown

**Issue**: When calling `adapter.shutdown()` to shut down all adapters, `_update_bot_status()` repeatedly submits Bot offline events during the shutdown process, causing the same batch of Bots to be marked offline multiple times and triggering the `adapter.bot.offline` lifecycle event multiple times.

**Cause**: The Bot status tracking system introduced in 2.4.0-dev.1 did not set a "shutting down" flag during `shutdown()`, so `_update_bot_status()` could not distinguish between normal offline and cascading offline during the shutdown process.

**Affected Versions**: 2.4.0-dev.1 - 2.4.2-dev.1

**Fixed Version**: 2.4.2-dev.1

**Fix**: Add `_is_being_shutdown` flag in `AdapterManager`. Set it to True at the start of `shutdown()` and clear it at the end; `_update_bot_status()` checks this flag and skips repeated submissions during the shutdown process.

**Fix Date**: 2026/04/21

**Severity**: 🟡 Moderate

**Type**: Adapter

---

### [BUG-009] LazyModule synchronous access to BaseModule causes incomplete initialization

**Issue**: When users access lazy-loaded BaseModule attributes in synchronous contexts, the module uses `loop.create_task()` for asynchronous initialization but does not wait, causing the attribute access to possibly be incomplete and leading to race conditions.

**Cause**: `_ensure_initialized()` uses `loop.create_task(self._initialize())` and returns immediately without ensuring initialization is complete.

**Affected Versions**: 2.4.0-dev.0 - 2.4.2-dev.1

**Fixed Version**: 2.4.2-dev.2

**Fix**: In synchronous contexts, BaseModule initialization is changed to use `asyncio.run(self._initialize())` to ensure initialization is complete before returning. The transparent proxy feature is maintained, and users do not need to perceive the difference between synchronous and asynchronous contexts.

**Fix Date**: 2026/04/21

**Severity**: 🟡 Moderate

**Type**: Loading System

---

### [BUG-010] Multi-threaded configuration system writing causes data loss

**Issue**: In a multi-threaded environment, when multiple threads call `config.setConfig()` simultaneously, the `_flush_config()` read-modify-write operation is not atomic, potentially causing partial write loss.

**Cause**: Although `_flush_config()` uses `RLock`, there is no file lock protection between file read and write, and the `_schedule_write` Timer may be triggered multiple times, causing overwrite.

**Affected Versions**: 2.3.0 - 2.4.2-dev.1

**Fixed Version**: 2.4.2-dev.2

**Fix**:
1. Add file locking mechanism (`_file_lock`) to ensure atomic file operations
2. Use temporary file writing followed by atomic renaming (`os.replace`/`os.rename`)
3. Improve `_schedule_write` Timer cancellation and rescheduling logic

**Fix Date**: 2026/04/21

**Severity**: 🔴 Severe

**Type**: Configuration System

---

### [BUG-011] Windows Ctrl+C cannot stop the program

**Issue**: When running `python main.py` directly on Windows, pressing Ctrl+C does not terminate the program. After the program starts normally and outputs the routing server information, Ctrl+C has no response, and the process can only be forcibly killed via the task manager. However, it can be stopped normally when started via `epsdk run`—but `epsdk run` uses a sub-process model.

**Cause**: The `serve()` function of the Hypercorn ASGI server internally registers its own SIGINT handler via `signal.signal(SIGINT, handler)`, overriding Python's default `KeyboardInterrupt` handling mechanism. When Hypercorn is started as a background task via `asyncio.create_task()`, its internal shutdown process cannot be triggered normally (because it expects the `worker_serve` mode), causing the Ctrl+C signal to be swallowed by Hypercorn without triggering any cleanup actions.

**Affected Versions**: 2.3.6 - 2.4.2

**Fixed Version**: 2.4.3-dev.0

**Fix**:
1. Switch the ASGI server from Hypercorn to Uvicorn (`pyproject.toml` dependency change)
2. Start the server directly using `uvicorn.Server._serve()`, **bypassing** the `capture_signals()` signal handling context manager
3. Implement graceful shutdown via `server.should_exit = True`, and cancel the background task if timeout occurs
4. Synchronously remove the sub-process running model and `runtime/cleanup.py` cleanup module (sub-process cleanup mechanism is no longer needed)

**Fix Date**: 2026/04/28

**Severity**: 🔴 Severe

**Type**: CLI / Runtime

---

### [BUG-012] Hot restart does not apply updated module Python code

**Issue**: After executing `sdk.restart()` for a soft restart, the new code (e.g., new API routes) of modules/adapters upgraded via `epsdk install` does not take effect, and old logic is still running. The latest code can only be loaded by completely restarting the process.

**Cause**: `_do_restart()` calls `entry_point.load()` during re-initialization, but this function returns a cached old module object from `sys.modules` rather than reloading from disk.

**Affected Versions**: Early versions - 2.4.3-dev.1

**Fixed Version**: 2.4.3-dev.1

**Fix**: Clear the cache of loaded modules/adapters in `sys.modules` after `uninit()` and before `init`, so `entry_point.load()` loads the latest code from disk. Add `_collect_top_level_modules()` and `_invalidate_module_cache()` helper methods to deduce top-level module names via `top_level.txt` or entry-point value.

**Fix Date**: 2026/05/03

**Severity**: 🔴 Severe

**Type**: Loading System / Runtime

---

### [BUG-013] Module loading strategy sorting logic error

**Issue**: `ModuleLoadStrategy` provides a `priority` field to declare the initialization priority of modules, but the implementation of the loading strategy has an error, causing modules to be initialized in an order different from the expected priority, actually loading in the default order of `entry_points()`. When modules have initialization dependencies, they cannot ensure the correct initialization order through `priority`.

**Cause**: The sorting logic in the implementation of the loading strategy is incorrect, and `initialize_modules()` does not sort the module list by `priority`.

**Affected Versions**: 2.3.4 - 2.4.5-dev.2

**Fixed Version**: 2.4.5-dev.3

**Fix**: Before traversing in `initialize_modules()`, sort the module list by `priority` in descending order. Modules with the same priority maintain their original relative order (stable sort).

**Fix Date**: 2026/05/15

**Severity**: 🟡 Moderate

**Type**: Loading System

---

### [BUG-014] Adapter middleware returning None causes event data loss

**Issue**: During the execution of OneBot12 middleware chains in `adapter.emit()`, if a middleware returns `None` (e.g., forgetting to `return data`), the subsequent middleware and all event handlers receive `processed_data` as `None`, causing event processing to fail completely.

**Cause**: The middleware chain implementation `processed_data = await middleware(processed_data)` does not check if the return value is `None`, directly overwriting the result of the previous step.

**Affected Versions**: unknown - 2.4.5-dev.3

**Fixed Version**: 2.4.5-dev.4

**Fix**: When a middleware returns `None`, ignore the return value, retain the original data, and output a warning-level log.

**Fix Date**: 2026/05/15

**Severity**: 🔴 Severe

**Type**: Adapter / Event System

---

### [BUG-015] Configuration file path depends on working directory

**Issue**: The configuration file path in `ConfigManager` is default relative path `"config/config.toml"`, resolved at runtime using `os.getcwd()`. If the working directory changes during runtime (e.g., via `os.chdir()`), the read/write operations of the configuration file point to the wrong location, causing configuration loss or reading old data.

**Cause**: In `__init__`, the relative path is directly stored without being resolved to an absolute path at initialization.

**Affected Versions**: 2.3.7 - 2.4.5-dev.3

**Fixed Version**: 2.4.5-dev.4

**Fix**: In `ConfigManager.__init__()`, if the passed path is relative, automatically resolve it to an absolute path using `os.path.abspath()`.

**Fix Date**: 2026/05/15

**Severity**: 🟡 Moderate

**Type**: Configuration System

---

### [BUG-016] BaseStorage confuses storing value None with key not existing

**Issue**: `BaseStorage.get_multi()` / `__getattr__()` cannot distinguish between "key not existing" and "key's value is None", treating a user explicitly storing `None` as if the key does not exist.

**Cause**: The retrieval logic directly uses `value is None` to determine if the key exists, lacking an independent "missing" marker.

**Affected Versions**: Early versions - 2.4.6-dev.6

**Fixed Version**: 2.4.6-dev.6

**Fix**: Introduce `_SENTINEL` sentinel value to distinguish between "key not existing" and "value is None", no longer confusing the two.

**Fix Date**: 2026/06/07

**Severity**: 🟡 Moderate

**Type**: Storage

---

### [BUG-017] WebSocket route auto_accept flag lost after service restart

**Issue**: After service restart (e.g., `sdk.restart()`), the `auto_accept` configuration of all WebSocket routes reverts to `False`, and connections that were expected to be automatically accepted remain pending, causing the client to not receive responses for a long time, manifesting as a stuck WebSocket connection.

**Cause**: `_restore_routes_from_records()` hardcodes `auto_accept` to `False` when restoring routes from persistent records, without reading the original record's value; also, when the route storage tuple expanded from a binary tuple to a ternary tuple, the restoration logic was not synchronized.

**Affected Versions**: 2.3.8-dev.0 - 2.4.6-dev.6

**Fixed Version**: 2.4.6-dev.6

**Fix**: The route storage tuple expands to `(handler, auth_handler, auto_accept)`, and `_restore_routes_from_records()` reads the real `auto_accept` value from the record instead of hardcoding `False`.

**Fix Date**: 2026/06/07

**Severity**: 🔴 Severe

**Type**: Routing

---

### [BUG-018] HTTP/WS client concurrent calls cause crash and connection leak

**Issue**: The HTTP and WebSocket clients in `Core/client.py` have multiple stability defects in concurrent scenarios, leading to connection leaks or process crashes:
- Concurrent calls to `ClientWebSocket.receive()` by multiple coroutines throw `Concurrent call to receive() is not allowed` from aiohttp.
- Concurrent calls to `_get_http_session()` / `_get_ws_session()` may create multiple sessions, and `_drain_sessions()` does not close old connections, causing connection leaks.
- The exception handling order in `request()` is incorrect: `except ClientConnectionError` (ErisPulse exception) is never triggered, and aiohttp's connection errors are caught by the generic `except Exception`, causing the "retry connection + session rebuild" logic (dead code) to never execute.
- `send_json()` ignores the `mode="binary"` parameter; `_get_ws_session()` does not pass default request headers.

**Cause**: The client's initial implementation (2.4.6-dev.5) lacks concurrency protection and exception classification, and improperly handles aiohttp's exception hierarchy and ErisPulse's custom exception inheritance.

**Affected Versions**: 2.4.6-dev.5 - 2.4.8

**Fixed Version**: 2.4.8

**Fix**:
1. Add `_recv_lock` to serialize all `receive()` / `receive_text()` / `receive_bytes()` calls.
2. Add `_session_lock` to protect session creation; `_drain_sessions()` is changed to an asynchronous method and truly closes old sessions.
3. Refactor `request()` exception handling order: `asyncio.TimeoutError` → `aiohttp.ClientConnectionError` (triggers session rebuild) → `aiohttp.ClientError` → `ClientError` (transparent pass) → `Exception`.
4. Fix `send_json()`'s mode handling, default request headers in `_get_ws_session()`, concurrent race conditions in `close()`, and repeated `release()` in `HttpResponse.__aexit__`.

**Fix Date**: 2026/06/12

**Severity**: 🔴 Severe

**Type**: Client

---

### [BUG-019] Adapter hot reload causes route conflicts and reload failure

**Issue**: When a third-party module (such as Dashboard) triggers adapter hot reload, or when adapter startup fails and retries, due to the uncleaned old routes (such as `onebot11_default`) registered previously, a `WebSocket path ... already registered` conflict is thrown, causing reload failure. A complete restart is required to restore.

**Cause**: `AdapterManager.shutdown()` only clears routes with `unregister_all_by_namespace(platform)`, but adapters (such as OneBot11) register WebSocket routes with `onebot11_{account_name}` as the namespace, resulting in a granularity mismatch and making cleanup an empty operation; route cleanup is also not performed for failed startup retries.

**Affected Versions**: Early versions - 2.4.9

**Fixed Version**: 2.4.9

**Fix**:
1. Route registration automatically tracks `owner → namespace` ownership relationships via `current_owner` ContextVar.
2. Add `unregister_all_by_owner(owner)`, cleaning up by owner during stop/restart, covering fine-grained namespaces.
3. Add `_stop_adapter(platform)` primitive ("stop equals cleanup"), binding stopping the adapter and reclaiming its registered resources in one call; `restart()` and failed startup retries both go through this entry.
4. Add framework-level `adapter.restart(platform)` API; third-party modules should call this method instead of directly operating the adapter instance.

**Fix Date**: 2026/06/12

**Severity**: 🔴 Severe

**Type**: Adapter / Routing

---

### [BUG-020] Subprocess mode `ep run <script>` cannot find sub-packages in the script's directory

**Issue**: When running a script using `ep r .\main.py` in non-hot-reload mode, if the script has relative imports (such as `from qg import ...`), it reports `No module named 'qg'` error. The `--reload` mode works normally.

**Cause**: The non-hot-reload mode directly calls `runpy.run_path()` to execute the script, which does not automatically add the script's directory to `sys.path`. The `--reload` mode runs via `subprocess.Popen` subprocess, which automatically inherits the current working directory, making `sys.path[0]` the script's directory, so it works normally.

**Affected Versions**: 2.5.0 - 2.5.2-dev.0

**Fixed Version**: 2.5.2-dev.0

**Fix**: Before calling `runpy.run_path()`, manually insert the script's directory into `sys.path[0]`.

**Fix Date**: 2026/06/27

**Severity**: 🟡 Moderate

**Type**: CLI

---

### [BUG-021] SQL query builder rejects valid wildcard and list expressions

**Issue**: `SQLiteQueryBuilder`'s `_build_select_sql()` calls `_validate_identifier()` for all SELECT columns, which uses a strict whitelist regex `^[a-zA-Z_][a-zA-Z0-9_]*$`, causing legitimate SQL syntax to be incorrectly judged as unsafe column names:

- `SELECT *` — `*` is a standard SQL wildcard
- `SELECT COUNT(*)` — aggregate function
- `SELECT users.name` — qualified column name
- `SELECT col AS alias` — column alias

Among them, `Select("*")` is used by Cron and other modules, causing module `on_load` execution to fail and the module cannot be loaded.

**Cause**: In version 2.4.6, SQL injection protection was enhanced, introducing `_validate_identifier()` whitelist validation. This validation is applied to all column names but does not distinguish between read end (SELECT/ORDER BY) and write end (INSERT/UPDATE). SELECT columns allow complex SQL expressions and should not be restricted by simple identifier whitelists.

**Affected Versions**: 2.4.6 - 2.5.2-dev.1

**Fixed Version**: 2.5.2-dev.2

**Fix**: Change the SELECT/ORDER BY column validation from whitelist mode to blacklist mode:
1. Add `_validate_select_column()` function, only blocking SQL injection dangerous characters (`;` `'` `"` `--` `/*` `*/` `\x00` newline)
2. Allow any valid SQL column expression (`*`, `table.*`, `table.column`, `COUNT(*)`, `col AS alias`, etc.)
3. INSERT/UPDATE column names still maintain strict whitelist validation (only allow simple identifiers)

**Fix Date**: 2026/06/29

**Severity**: 🔴 Severe

**Type**: Storage

---

### [BUG-022] _resolve_account() account resolution regression (_accounts_data not filled)

**Issue**: After the 2.5.2 configuration system refactoring, multi-account adapters that declare `AccountConfigClass` report `ValueError("未声明 AccountConfigClass，无法解析账户")` when calling methods that need to send messages, such as `wait_reply` and `reply`. Even if the adapter correctly configures multi-account information, account resolution still fails.

**Cause**: In 2.5.2-dev.5, `_load_accounts()` (responsible for reading configuration + validation + filling `_accounts_data`) was refactored into `_ensure_accounts_exist()` (only generates configuration template), but `_resolve_account()` still checks `self._accounts_data is None`. Since `_ensure_accounts_exist()` no longer fills `_accounts_data`, this attribute remains `None`, causing `_resolve_account()` to prematurely return `(None, None)`, and account resolution fails completely.

**Root Cause Chain**:
```
_load_accounts() was deleted
  → __init__ no longer fills _accounts_data
    → _accounts_data remains None
      → _resolve_account() checks _accounts_data is None → return (None, None)
        → downstream places calling _resolve_account (e.g., call_api) get None
          → trigger error
```

**Affected Versions**: 2.5.2-dev.5 - 2.5.2

**Fixed Version**: 2.5.3

**Fix**: In `BaseAdapter.__init__`, after `_ensure_accounts_exist()`, restore the filling of `_accounts_data`:
```python
if self.AccountConfigClass is not None:
    self._ensure_accounts_exist()
    self._accounts_data = self.accounts  # restore filling, data source is real-time read accounts attribute
```
The `_resolve_account()` logic remains unchanged, fully backward compatible:
- For adapters that do not declare `AccountConfigClass`: `_accounts_data` remains `None` → return `(None, None)`
- For adapters that declare `AccountConfigClass`: `_accounts_data` is filled → normal resolution
- For adapters that override `_load_accounts` or manually set `_accounts_data`: override in `super().__init__()` with highest priority

**Fix Date**: 2026/07/07

**Severity**: 🔴 Severe

**Type**: Adapter / Configuration System

---

### [BUG-023] Adapter cache not refreshed after account configuration modification causing account resolution failure

**Issue**: After users modify the account configuration of multi-account adapters via Dashboard, the adapter still uses the old cache, and calls to message-sending related methods report `未找到可用账户 (account_id=default)`. A complete process restart is required for the new configuration to take effect.

**Cause**: `_accounts_data` is only read from configuration storage once in `BaseAdapter.__init__`, and is not refreshed afterward. `AdapterManager._run_adapter()` and `restart()` do not re-read account configuration before calling `adapter.start()`, causing the cache to be out of sync with the actual configuration.

**Affected Versions**: 2.4.6 - 2.5.4

**Fixed Version**: 2.5.4

**Fix**: In `AdapterManager._run_adapter()` and `restart()`, before calling `adapter.start()`, refresh `adapter._accounts_data = adapter.accounts` to ensure the latest configuration is used each time the adapter starts.

**Fix Date**: 2026/07/09

**Severity**: 🔴 Severe

**Type**: Adapter / Configuration System

---

### [BUG-024] storage.set() writing large numeric ID keys triggers OOM Kill

**Issue**: When calling `storage.set()` to write a nested key path containing a large pure numeric field (such as QQ group number `871684833`), the process is killed by container OOM (exit code -9), causing the service to crash and become unrecoverable.

**Cause**: In the recursive implementation of `_set_nested_value`, pure numeric fields in the nested key path are mistakenly identified as list indices by `isdigit()`, triggering `current.extend([None] * (index - len(current) + 1))`, attempting to allocate hundreds of millions of list elements, instantly exhausting memory.

**Root Cause Chain**:
```
Key path contains pure numeric field (such as group number 871684833)
  → isdigit() mistakenly identifies as array index
    → extend([None] * (871684833 - len(current) + 1))
      → attempts to allocate hundreds of millions of elements
        → memory exhausted → container OOM Kill (exit code -9)
```

**Affected Versions**: 2.5.1 - 2.5.5

**Fixed Version**: 2.5.5

**Fix**:
1. Always use a dictionary when pre-creating intermediate layers, never guess container type based on whether the next segment is a number.
2. When setting the final value, only handle indexing if the container itself is a list and the index is less than `STORAGE_MAX_LIST_INDEX` (10000); skip large indices safely.
3. Change the recursive implementation to an iterative one, eliminating potential infinite recursion risks in the original code.
4. Add `STORAGE_MAX_LIST_INDEX` constant to `Core/constants.py`, centrally managing the safe index upper limit.

**Fix Date**: 2026/07/10

**Reproduction Steps**:
```python
# Writing a nested key path containing a large number field (such as QQ group number) triggers OOM
await sdk.storage.aset("groups.871684833.name", "某群")
# → process memory spikes instantly, killed by OOM
```

**Regression Tests**: `tests/unit/test_unit_storage.py` adds 4 regression test cases
- `test_nested_key_numeric_segment_as_dict_key` — precisely reproduces OOM scenario
- `test_nested_key_numeric_segment_multiple` — multiple consecutive numeric fields as dictionary keys
- `test_nested_key_existing_list_index_set_within_limit` — existing list index write within limit
- `test_nested_key_list_index_safety_limit` — safety limit verification for large index

**Severity**: 🔴 Severe

**Type**: Storage

---

### [BUG-025] on_config_update callback not routed by core

**Issue**: The `on_config_update(old, new)` callback is defined in the base class (`BaseModule` / `BaseAdapter`), but the core framework does not associate it with configuration change events. The actual behavior is: when modifying configuration through the configuration management panel, the callback can be triggered, but when manually editing `config.toml` or calling `setConfig()` via code, `on_config_update` is not triggered.

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

**Fix**: `ModuleManager` / `AdapterManager` register `config.set` (covers code `setConfig()` path) and `config.updated` (covers manual file editing path) event subscriptions, match by configuration key prefix, and call the corresponding component's `on_config_update`, passing type-safe configuration objects. Also fix `_flush_config()` writing file without synchronizing `_config_mtime`, avoiding the framework's own write being misjudged as external modification and repeatedly triggering `config.updated` by file monitoring task.

**Compatibility Note**: Configuration hot update is now centrally maintained by the framework core. Previously, the logic of triggering by the configuration management panel has been removed, and the panel needs to be upgraded synchronously after upgrading the framework, otherwise duplicate triggering (core + panel each call once) will occur. The `on_config_update` method signature and semantics remain unchanged, subclasses need no modification.

**Fix Date**: 2026/07/23

**Severity**: 🟡 Moderate

**Type**: Configuration System

---

### [BUG-026] notice/request event reply target inference error

**Issue**: When calling `event.reply()` in a group notice event (such as member joining a group `group_member_increase`), the message is sent to the user who triggered the event's private chat, not the group where the event occurred. The same applies to friend notice events, where the reply target may be incorrect.

**Cause**: `infer_receive_type()` directly returns the event's `detail_type` as the session type. For `message` events, this is correct (`detail_type` values `private`/`group` are the session types), but for `notice/request` events, `detail_type` is a semantic subtype (such as `group_member_increase`, `friend_increase`), not the session type. Subsequent `convert_to_send_type()` and `get_id_field()` cannot find this value in the mapping table, defaulting to `"user"` / `"user_id"`, causing the reply target to be incorrect.

**Root Cause Chain**:
```
notice event detail_type="group_member_increase"
  → infer_receive_type() directly returns "group_member_increase"
    → convert_to_send_type("group_member_increase") not in mapping table → default to "user"
    → get_id_field("group_member_increase") not in mapping table → default to "user_id"
      → target_id = event["user_id"]  ← new member's private chat (not group)
```

**Affected Versions**: All versions

**Fixed Version**: 2.7.0-dev.3

**Fix**: `infer_receive_type()` adds a check—only returns `detail_type` directly if it is a known session type (standard type or custom type); otherwise, infers the correct session type based on the ID field (`group_id` / `channel_id` / `user_id`, etc.).

**Regression Tests**: `tests/unit/test_unit_session_type.py` → `TestNoticeRequestTypeInference` (10 test cases)

**Fix Date**: 2026/07/29

**Severity**: 🟢 Minor

**Type**: Event System

---

### [BUG-027] Route rate limiting cleanup task uses fixed window causing long window rate limit rules to fail

**Issue**: When configuring route rate limiting as a long window rule (such as `100/hour`, `{"requests": 100, "window": 3600}`), the rate limiting is ineffective—practically behaving like `100/minute` (up to about 6000 requests per hour), failing to provide the expected hourly protection.

**Cause**: `_apply_rate_limit` parses the actual `window` (up to 3600 seconds) per route, and per-request checks do use this window; however, the background cleanup task `_cleanup_expired_rate_limits` uses a fixed constant `DEFAULT_RATE_LIMIT_WINDOW_SECS` (60 seconds) as the unified cleanup threshold for all routes. Thus, time stamps earlier than 60 seconds are cleared by the cleanup task, preventing the accumulation of nearly 100 records within the hour window, severely weakening the rate limiting.

**Root Cause Chain**:
```
_apply_rate_limit parses window=3600 (100/hour)
  → per-request check uses 3600s retention time (correct)
  → but _cleanup_expired_rate_limits uses fixed max_window=60s cleanup
    → time stamps earlier than 60s are cleared
      → the hour window always retains only the records from the last 1 minute
        → 100/hour effectively degrades to ~100/minute (relaxed by about 60 times)
```

**Affected Versions**: 2.6.0-dev.0 - 2.7.0-dev.4

**Fixed Version**: 2.7.0-dev.5

**Fix**: Add `_rate_limit_windows: dict[str, int]` to record the actual window per route; `_apply_rate_limit` writes the window when creating entries for the first time; `_cleanup_expired_rate_limits` is changed to clean up based on each key's own window (fallback to default value if missing); cleanup deletion and `stop()` synchronize maintenance of both dictionaries.

**Fix Date**: 2026/07/31

**Regression Tests**: `tests/unit/test_unit_router.py` → `TestRateLimit::test_cleanup_respects_per_route_window`

**Severity**: 🔴 Severe

**Type**: Routing

---

### [BUG-029] Configuration listener task broadcasts incomplete TOML and silently swallows exceptions

**Issue**: When the user manually edits `config.toml` and saves it halfway (producing a temporary syntax error), the configuration monitoring background thread detects the mtime change, reloads the configuration, but fails to load and still broadcasts an empty configuration `{}` via the `config.updated` event, causing adapters/modules' `on_config_update` to receive an empty configuration and mistakenly assume all configuration items were cleared, reverting to default values. Additionally, the listener loop uses `except Exception: pass` to silently swallow all exceptions, making it impossible to diagnose watcher failures.

**Cause**: Two defects overlap:
1. `_load_config` overwrites `self._cache` to `{}` when TOML syntax errors/permission errors occur, but the background listener thread `_watch_loop` and cache timeout path `_check_cache_validity` unconditionally execute `_emit_config_updated()` after calling `_load_config()`, broadcasting the "empty cache produced by failed load" as a real change.
2. `_watch_loop`'s `except Exception` does not log any messages.

**Root Cause Chain**:
```
User saves halfway → TOML syntax error
  → _load_config() overwrites _cache = {}
    → _watch_loop unconditionally _emit_config_updated(new_config={})
      → adapters/modules on_config_update receive empty configuration
        → mistakenly assume configuration was cleared, revert to default values
```

**Affected Versions**: 2.6.2-dev.1 - 2.7.0-dev.4

**Fixed Version**: 2.7.0-dev.5

**Fix**:
1. `_load_config` is changed to return `bool`; when TOML syntax errors/permission errors/other errors occur, it **retains the last valid cache** (does not overwrite to `{}`), only logs diagnostic messages, and returns `False`
2. `_watch_loop` and `_check_cache_validity` only emit `config.updated` if `_load_config()` returns `True`
3. `_watch_loop`'s `except Exception` is changed to log at warning level (new i18n key `core.config.watcher_error`, synchronized in five languages)

**Fix Date**: 2026/07/31

**Regression Tests**: `tests/unit/test_unit_config.py` → `test_malformed_toml_preserves_last_valid_cache`, `test_permission_denied_logs_clear_message` (updated to verify retained cache and return False)

**Severity**: 🟡 Moderate

**Type**: Configuration System

---

### [BUG-030] Configuration watcher race condition causes setConfig delayed write silently loses data

**Issue**: Multiple users report that after using `config.setConfig(key, value)` (default `immediate=False`), their module configuration is not written to `config.toml`, while other modules' configurations are normal. Setting `immediate=True` (force flush) can avoid this. The behavior is: configuration written at runtime is lost after the next restart, while configuration generated at startup is retained.

**Cause**: Two overlapping defects:
1. **Logical Defect**: `_watch_loop` unconditionally `_dirty_keys.clear()` when `_check_file_change()` returns `True`. However, `_check_file_change()` only uses `!=` to compare mtime, and the framework's own `_flush_config` write also changes mtime—although `_flush_config` updates `_config_mtime` after writing, the watcher thread may observe the mtime difference between file write and mtime assignment (and on coarse-grained file systems) and mistakenly identify it as "external modification" and clear all dirty keys.
2. **Thread Defect**: `_watch_loop` operates `_write_timer`/`_dirty_keys` without holding `_lock`, creating data races with `setConfig` (holds lock to write `_dirty_keys`), `_schedule_write` (holds lock to write `_write_timer`).

**Root Cause Chain**:
```
ModuleA setConfig(immediate=True) → flush write, mtime changes
  → User module setConfig(immediate=False) → enters _dirty_keys, flushes after 5s
    → watcher polling, _check_file_change observes mtime difference from its own previous write
      → _dirty_keys.clear() → user module's dirty keys are silently discarded
        → configuration missing after restart
```

**Affected Versions**: 2.6.0 - 2.7.0

**Fixed Version**: 2.7.1

**Fix**:
1. Add `_last_self_write_mtime` field; after `_flush_config` writes, record it synchronously; in `_check_file_change`, when mtime changes, first compare this value, and if matched, determine it as self-write and return `False`
2. Hold `_lock` for the entire `_watch_loop`; preserve `_dirty_keys` for truly external modifications (merge semantics), and next flush merges with external content (dirty keys take precedence), no longer `clear()`
3. `getConfig`/`_check_cache_validity` paths are unaffected (their reload does not clear dirty keys)

**Fix Date**: 2026/08/06

**Regression Tests**: `tests/unit/test_unit_config.py` → `test_self_write_not_detected_as_external`, `test_external_change_preserves_dirty_keys`, `test_flush_merges_dirty_with_external`

**Severity**: 🔴 Severe

**Type**: Configuration System

---

### [BUG-032] Configuration delay write period "write-then-read" reads old value

**Issue**: After `config.setConfig()` (default `immediate=False` delayed write for about 5 seconds), immediately reading its **parent/ancestor node** (such as `set_erispulse_section("scope.actions.MyModule", {...})` followed by `get_erispulse_config()`) returns the old value, the written subkey "disappears", and only becomes visible after the flush. Scenarios like scope configuration hot updates ("write-read-write") are affected (test plugin `/t_section` use case in 2.8.0 exposes this).

**Cause**: `setConfig` stores dot-separated keys in the dirty queue `_dirty_keys` in **flat form**, and only `getConfig`'s **exact key query** hits the dirty queue; tree path queries (e.g., `getConfig("ErisPulse.scope")`) only go through the cache tree, not overlaying dirty values—during the delay flush (`_flush_config` merges dirty keys into the cache and clears the queue), a "read-you-write" gap forms.

**Affected Versions**: 2.6.0 - 2.8.0-dev.1

**Fixed Version**: 2.8.0-dev.1

**Fix**: Introduce dirty overlay semantics in `getConfig`—① exact hit in dirty key returns directly (original behavior unchanged); ② dirty key is the ancestor of the query key → take the longest dirty ancestor and parse the remaining path in its value subtree; ③ dirty key is the descendant of the query key → build an overlay subtree (`_dirty_overlay`) and deeply merge it with the cache subtree (`_deep_merge`, override priority, without modifying the original cache object). Without dirty keys, go through the original fast path, zero additional overhead.

**Fix Date**: 2026/09/04

**Regression Tests**: `tests/unit/test_unit_config.py` → `test_get_config_overlays_dirty_descendant`, `test_get_config_overlay_merges_with_cache_siblings`, `test_get_config_overlay_new_branch`, `test_get_config_dirty_ancestor_query`, `test_get_config_dirty_exact_key_still_wins`

**Severity**: 🟡 Moderate

**Type**: Configuration System