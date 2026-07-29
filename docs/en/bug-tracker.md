# Bug Tracker

This document records the known bugs of the ErisPulse SDK and their fixes, arranged in chronological order by the time of fix.

> **For Readers**
> No software is born perfect; even the most careful developers leave small mistakes. The bugs listed here are all issues that have a real impact on operation—those that are too minor to even reach the "minor" level do not appear here. Although the list contains many items marked as "severe," the original intention of publicly documenting these bugs is to facilitate troubleshooting and traceability, not to create anxiety: problems that are visible, recorded, and fixed are themselves proof that the project is continuously improving. Do not feel anxious when you see this list; it is a troubleshooting tool, not a source of fear.

> **How to Read & Maintenance Conventions**
> - Each bug record includes structured fields such as problem description, root cause analysis, affected version range, and fix solution. It is recommended to check the "Affected Versions" field before upgrading to see if it covers the version currently in use.
> - If you need to add a new bug entry, please supplement the content at the corresponding position, following the field specifications and severity/type classifications below.

---

## Field Descriptions

### Required Fields

| Field | Description |
|------|------|
| **Problem** | The external manifestation of the bug, the abnormal phenomenon observable by the user. Try to provide error messages or typical scenarios |
| **Cause** | Root cause analysis, pointing to specific code defects (including "root cause chain" diagrams for complex scenarios) |
| **Affected Versions** | The affected version range, format `introduced version - fixed version` (including both dev versions) |
| **Fixed Version** | The specific version number that fixed the bug |
| **Fix Content** | A brief description of the fix solution, including key code changes |
| **Fix Date** | The release date of the corresponding fixed version, using the `YYYY/MM/DD` format |
| **Severity** | Marked according to the "Severity Grading" below |
| **Type** | Marked according to the "Type Classification" below, can be combined (e.g., `Adapter / Router`) |

### Optional Fields

| Field | Description | Applicable Scenarios |
|------|------|---------|
| **Reproduction Steps** | The minimal reproducible path to trigger the bug | Complex bugs, sporadic bugs are recommended to supplement |
| **关联** | Related Issue / PR / Commit links | Supplement when there are external discussion records |
| **Regression Test** | The location of test cases for verifying the fix and preventing regression | Supplement when corresponding pytest cases have been written |

---

## Severity Grading

| Identifier | Level | Judgment Criteria | Typical Manifestations |
|------|------|---------|---------|
| 🔴 | Severe | Causes process crash, data loss/damage, core functionality completely unusable, security vulnerabilities | OOM Kill, message cannot be sent, module cannot be loaded, hot reload failure |
| 🟡 | Moderate | Function abnormal but with workaround, non-core functionality failure, sporadic problems | Incorrect status judgment, repeated trigger, cache expiration, inaccurate error prompts |
| 🟢 | Minor | Does not affect core functionality, only code quality or experience issues, potential risks not yet triggered | Deprecated API, dead code, missing warning logs |

---

## Type Classification

| Type | Coverage Range |
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

When adding a new bug entry, please follow the following format:

```markdown
### [BUG-XXX] Title

**Problem**: Problem description (error message or typical phenomenon)
**Cause**: Root cause analysis
**Affected Versions**: Introduced version - Fixed version
**Fixed Version**: x.x.x
**Fix Content**: Fix solution
**Fix Date**: YYYY/MM/DD

<!-- Optional fields -->
**Reproduction Steps**: (Recommended to supplement for complex bugs)
**关联**: (Issue/PR links)
**Regression Test**: (Test case path)

**Severity**: 🔴 Severe | 🟡 Moderate | 🟢 Minor
**Type**: Configuration System / Event System / Adapter / Router / Client / Storage / Loader / CLI / Runtime
```

---

## Statistics Overview

| Severity | Count |
|--------|------|
| 🔴 Severe | 13 |
| 🟡 Moderate | 11 |
| 🟢 Minor | 2 |
| **Total** | **26** |

| Type | Count |
|------|------|
| Adapter | 6 |
| Event System | 5 |
| Storage | 3 |
| Loader | 3 |
| CLI | 3 |
| Configuration System | 3 |
| Router | 1 |
| Client | 1 |
| Runtime | 1 |

> Note: A single bug can belong to multiple types, the table above counts by main type.

---

## Fixed Bugs

### [BUG-001] Event handler duplicate registration causes event to be processed multiple times

**Problem**: When registering handlers using multiple `@message` / `@notice` decorators, the same event is triggered multiple times, causing commands to be executed multiple times and logs to be output repeatedly.

**Cause**: `BaseEventHandler` lacks deduplication logic when registering handlers with the adapter event bus. Each decorator mounts a handler to the bus once, causing the event to be called multiple times during distribution.

**Affected Versions**: 2.2.0-dev.0 - 2.2.1-dev.0

**Fixed Version**: 2.2.1-dev.0

**Fix Content**: Optimize `BaseEventHandler` to ensure each event type is registered with the adapter only once, avoiding repeated triggers.

**Fix Date**: 2025/08/18

**Severity**: 🔴 Severe

**Type**: Event System

---

### [BUG-002] Init command adapter configuration path type error

**Problem**: When using the `ep init` command for interactive initialization, selecting the adapter configuration results in a type error:

```
Interactive initialization failed: unsupported operand type(s) for /: 'str' and 'str'
```

**Cause**: When adjusting the configuration file path in version 2.3.7, the method parameter types were inconsistent. `_configure_adapters_interactive_sync` receives a `str` type parameter, but internally uses the `Path` `/` operator to concatenate paths.

**Affected Versions**: 2.3.7 - 2.3.9-dev.1

**Fixed Version**: 2.3.9-dev.1

**Fix Content**: Change the parameter type of the `_configure_adapters_interactive_sync` method from `str` to `Path`, and pass a `Path` object directly when calling.

**Fix Date**: 2026/03/23

**Severity**: 🟡 Moderate

**Type**: CLI

---

### [BUG-003] Commands fail after restart

**Problem**: After calling `sdk.restart()`, commands registered via `@command` cannot be triggered, resulting in the robot not responding after sending a command.

**Cause**: After `adapter.shutdown()` clears the event bus, the `_linked_to_adapter_bus` status of `BaseEventHandler` is not reset to `False`, causing the `_process_event` method to consider it already mounted to the adapter bus and skip re-registration.

**Affected Versions**: 2.2.x - 2.4.0-dev.2

**Fixed Version**: 2.4.0-dev.3

**Fix Content**: Introduce `_linked_to_adapter_bus` status tracking. After `_clear_handlers()` disconnects the bus, `register()` automatically re-registers next time, adapting to shutdown/restart scenarios.

**Fix Date**: 2026/04/09

**Severity**: 🔴 Severe

**Type**: Event System

---

### [BUG-004] Lifecycle event handlers not cleaned up

**Problem**: After `sdk.restart()`, old lifecycle event handlers still exist and trigger repeatedly, causing the same event to be processed multiple times.

**Cause**: The `lifecycle._handlers` dictionary is never cleared in `uninit()`, so old and new handlers coexist after restart.

**Affected Versions**: 2.3.0 - 2.4.0-dev.2

**Fixed Version**: 2.4.0-dev.3

**Fix Content**: Clear `lifecycle._handlers` at the end of the `Uninitializer` cleanup process (after all events are submitted).

**Fix Date**: 2026/04/09

**Severity**: 🟡 Moderate

**Type**: Runtime

---

### [BUG-005] Event.is_friend_add/is_friend_delete detail_type inconsistent with OB12 standard

**Problem**: `Event.is_friend_add()` checks `detail_type == "friend_add"`, `Event.is_friend_delete()` checks `detail_type == "friend_delete"`, but OneBot12 standard defines `detail_type` values as `"friend_increase"` and `"friend_decrease"`. This is inconsistent with the values used by `notice.py`'s `on_friend_add`/`on_friend_remove` decorators, causing handlers registered via decorators to fail when corresponding `is_friend_add()`/`is_friend_delete()` judgment methods return `False`.

**Cause**: `wrapper.py` uses non-standard naming, while `notice.py` uses correct OB12 standard naming.

**Affected Versions**: From implementation to present

**Fixed Version**: 2.4.2-dev.1

**Fix Content**: Change the matching value of `is_friend_add()` from `"friend_add"` to `"friend_increase"`, and `is_friend_delete()` from `"friend_delete"` to `"friend_decrease"`.

**Fix Date**: 2026/04/13

**Severity**: 🟡 Moderate

**Type**: Event System

---

### [BUG-006] adapter.clear() does not clean _started_instances, causing incorrect status after restart

**Problem**: The `AdapterManager.clear()` method clears `_adapters`, `_adapter_info`, handlers, and `_bots`, but omits `_started_instances`. If `clear()` is called while the adapter is running, `_started_instances` retains dangling references, causing incorrect status judgment after restart.

**Cause**: When `_started_instances` was introduced in 2.4.0-dev.1, it was not synchronized for cleaning in `clear()`.

**Affected Versions**: 2.4.0-dev.1 - 2.4.2-dev.0

**Fixed Version**: 2.4.2-dev.1

**Fix Content**: Add `self._started_instances.clear()` in the `clear()` method.

**Fix Date**: 2026/04/13

**Severity**: 🟡 Moderate

**Type**: Adapter

---

### [BUG-007] command.wait_reply() uses deprecated asyncio.get_event_loop()

**Problem**: The `CommandHandler.wait_reply()` method uses `asyncio.get_event_loop()` to create a future and get a timestamp. This method has been deprecated in Python 3.10+, and `asyncio.get_running_loop()` should be used in asynchronous contexts. It is inconsistent with the `get_running_loop()` used in the `wait_for()` method in the same file `wrapper.py`.

**Cause**: The old API was used during development, and the newly added `wait_for()` method used the correct API but did not retroactively fix the old code.

**Affected Versions**: 2.3.0-dev.0

**Fixed Version**: 2.4.2-dev.1

**Fix Content**: Replace two instances of `asyncio.get_event_loop()` in `command.py` with `asyncio.get_running_loop()`.

**Fix Date**: 2026/04/13

**Severity**: 🟢 Minor

**Type**: Event System

---

### [BUG-008] Bot offline event repeatedly submitted during shutdown

**Problem**: When calling `adapter.shutdown()` to close all adapters, `_update_bot_status()` repeatedly submits Bot offline events during the shutdown process, causing the same batch of Bots to be marked offline multiple times and triggering the `adapter.bot.offline` lifecycle event multiple times.

**Cause**: The Bot status tracking system introduced in 2.4.0-dev.1 did not set a "shutting down" flag during `shutdown()`, so `_update_bot_status()` could not distinguish between normal offline and cascading offline during the shutdown process.

**Affected Versions**: 2.4.0-dev.1 - 2.4.2-dev.1

**Fixed Version**: 2.4.2-dev.1

**Fix Content**: Add `_is_being_shutdown` flag in `AdapterManager`. Set it to True at the start of `shutdown()` and clear it at the end; `_update_bot_status()` checks this flag and skips repeated submissions during the shutdown process.

**Fix Date**: 2026/04/21

**Severity**: 🟡 Moderate

**Type**: Adapter

---

### [BUG-009] LazyModule synchronous access to BaseModule causes incomplete initialization

**Problem**: When a user accesses a lazily loaded BaseModule attribute in a synchronous context, the module uses `loop.create_task()` for asynchronous initialization but does not wait, causing the attribute access to possibly not complete initialization and leading to race conditions.

**Cause**: `_ensure_initialized()` uses `loop.create_task(self._initialize())` and returns immediately without ensuring initialization completion.

**Affected Versions**: 2.4.0-dev.0 - 2.4.2-dev.1

**Fixed Version**: 2.4.2-dev.2

**Fix Content**: In a synchronous context, BaseModule's initialization is changed to use `asyncio.run(self._initialize())`, ensuring initialization completion before returning. The transparent proxy feature is maintained, and users do not need to be aware of the difference between synchronous and asynchronous.

**Fix Date**: 2026/04/21

**Severity**: 🟡 Moderate

**Type**: Loader System

---

### [BUG-010] Multi-threaded configuration system write causes data loss

**Problem**: In a multi-threaded environment, when multiple threads simultaneously call `config.setConfig()`, the `_flush_config()` read-modify-write operation is not atomic, potentially causing partial write loss.

**Cause**: Although `_flush_config()` uses `RLock`, there is no file lock protection between file read and write, and `_schedule_write`'s Timer may be triggered multiple times, causing overwrite.

**Affected Versions**: 2.3.0 - 2.4.2-dev.1

**Fixed Version**: 2.4.2-dev.2

**Fix Content**:
1. Add file locking mechanism (`_file_lock`) to ensure atomic file operations
2. Use atomic renaming after writing to a temporary file (`os.replace`/`os.rename`)
3. Improve `_schedule_write`'s Timer cancellation and rescheduling logic

**Fix Date**: 2026/04/21

**Severity**: 🔴 Severe

**Type**: Configuration System

---

### [BUG-011] Ctrl+C cannot stop program on Windows

**Problem**: When running `python main.py` directly on Windows, pressing Ctrl+C cannot terminate the program. After the program starts normally and outputs the routing server information, Ctrl+C has no response at all and can only be forcibly killed via Task Manager. However, it can be stopped normally when started via `epsdk run`—but `epsdk run` runs via a subprocess model.

**Cause**: The `serve()` function of the Hypercorn ASGI server internally registers its own SIGINT handler via `signal.signal(SIGINT, handler)`, overriding Python's default `KeyboardInterrupt` handling mechanism. When Hypercorn is started as a background task via `asyncio.create_task()`, its internal shutdown process cannot be triggered normally (because it expects the `worker_serve` mode), causing the Ctrl+C signal to be swallowed by Hypercorn but not triggering any cleanup actions.

**Affected Versions**: 2.3.6 - 2.4.2

**Fixed Version**: 2.4.3-dev.0

**Fix Content**:
1. Switch ASGI server from Hypercorn to Uvicorn (`pyproject.toml` dependency change)
2. Start the server directly using `uvicorn.Server._serve()`, **bypassing** the `capture_signals()` signal handling context manager
3. Implement graceful shutdown via `server.should_exit = True`, cancel background task on timeout
4. Synchronously remove subprocess running model and `runtime/cleanup.py` cleanup module (subprocess cleanup mechanism no longer needed)

**Fix Date**: 2026/04/28

**Severity**: 🔴 Severe

**Type**: CLI / Runtime

---

### [BUG-012] Updated module Python code not effective after hot restart

**Problem**: After executing `sdk.restart()` for a soft restart, the new code (such as new API routes) of modules/adapters upgraded via `epsdk install` is not effective, and the old version logic is still running. The latest code can only be loaded by completely restarting the process.

**Cause**: `_do_restart()` calls `entry_point.load()` during re-initialization, but this function returns a cached old module object from `sys.modules` rather than reloading from disk.

**Affected Versions**: Early versions - 2.4.3-dev.1

**Fixed Version**: 2.4.3-dev.1

**Fix Content**: Clear the cache of loaded modules/adapters in `sys.modules` after `uninit()` and before `init()` to ensure `entry_point.load()` loads the latest code from disk. Add auxiliary methods `_collect_top_level_modules()` and `_invalidate_module_cache` to derive top-level module names via `top_level.txt` or entry-point value.

**Fix Date**: 2026/05/03

**Severity**: 🔴 Severe

**Type**: Loader System / Runtime

---

### [BUG-013] Module loading strategy sorting logic error

**Problem**: `ModuleLoadStrategy` provides a `priority` field to declare the initialization priority of modules, but the implementation of the loading strategy has an error, causing modules to be initialized not in the expected priority order, but actually loaded in the default order of `entry_points()`. When modules have loading dependencies, the correct initialization order cannot be ensured through `priority`.

**Cause**: There is a sorting logic error in the implementation of the loading strategy; `initialize_modules()` does not sort the module list by `priority`.

**Affected Versions**: 2.3.4 - 2.4.5-dev.2

**Fixed Version**: 2.4.5-dev.3

**Fix Content**: Sort the module list by `priority` in descending order before traversing `initialize_modules()`. Modules with the same priority maintain their original relative order (stable sorting).

**Fix Date**: 2026/05/15

**Severity**: 🟡 Moderate

**Type**: Loader System

---

### [BUG-014] Adapter middleware returning None causes event data loss

**Problem**: When executing the OneBot12 middleware chain in `adapter.emit()`, if a middleware returns `None` (e.g., forgetting to `return data`), the subsequent middleware and all event handlers receive `processed_data` as `None`, causing event processing to fail completely.

**Cause**: The middleware chain implementation `processed_data = await middleware(processed_data)` does not check if the return value is `None`, directly overwriting the result of the previous step.

**Affected Versions**: unknown - 2.4.5-dev.3

**Fixed Version**: 2.4.5-dev.4

**Fix Content**: Ignore the return value if the middleware returns `None`, retain the original data and continue passing, and output a warning-level log.

**Fix Date**: 2026/05/15

**Severity**: 🔴 Severe

**Type**: Adapter / Event System

---

### [BUG-015] Configuration file path depends on working directory

**Problem**: The configuration file path of `ConfigManager` is a relative path `"config/config.toml"` by default, which is resolved at runtime using `os.getcwd()`. If the working directory changes during runtime (e.g., via `os.chdir()`), file read/write operations will point to the wrong location, causing configuration loss or reading old data.

**Cause**: The relative path is directly stored in `__init__` without being resolved to an absolute path at initialization.

**Affected Versions**: 2.3.7 - 2.4.5-dev.3

**Fixed Version**: 2.4.5-dev.4

**Fix Content**: In `ConfigManager.__init__()`, if the passed path is a relative path, automatically resolve it to an absolute path using `os.path.abspath()`.

**Fix Date**: 2026/05/15

**Severity**: 🟡 Moderate

**Type**: Configuration System

---

### [BUG-016] BaseStorage confuses storing value None with key not existing

**Problem**: `BaseStorage.get_multi()` / `__getattr__()` cannot distinguish between "key does not exist" and "key's value is None", treating user-stored `None` as if the key does not exist when reading.

**Cause**: The retrieval logic directly uses `value is None` to determine if the key exists, lacking an independent "missing" marker.

**Affected Versions**: Early versions - 2.4.6-dev.6

**Fixed Version**: 2.4.6-dev.6

**Fix Content**: Introduce `_SENTINEL` sentinel value to distinguish "key does not exist" from "value is None", no longer confusing the two.

**Fix Date**: 2026/06/07

**Severity**: 🟡 Moderate

**Type**: Storage

---

### [BUG-017] WebSocket route auto_accept flag lost after service restart

**Problem**: After service restart (e.g., `sdk.restart()`), the `auto_accept` configuration of all WebSocket routes reverts to `False`, and connections that were expected to be automatically accepted remain pending, causing clients to receive no response for a long time, manifesting as a stuck WebSocket connection.

**Cause**: In `_restore_routes_from_records()`, when restoring routes from persistent records, `auto_accept` is hardcoded to `False` instead of reading the value from the original record; also, when the route storage tuple expanded from a binary to a ternary tuple, the restoration logic was not synchronized.

**Affected Versions**: 2.3.8-dev.0 - 2.4.6-dev.6

**Fixed Version**: 2.4.6-dev.6

**Fix Content**: The route storage tuple is expanded to `(handler, auth_handler, auto_accept)`, and `_restore_routes_from_records()` reads the true `auto_accept` value from the record instead of hardcoding `False`.

**Fix Date**: 2026/06/07

**Severity**: 🔴 Severe

**Type**: Router

---

### [BUG-018] HTTP/WS client concurrent calls lead to crash and connection leak

**Problem**: The HTTP and WebSocket clients in `Core/client.py` have multiple stability defects in concurrent scenarios, leading to connection leaks or process crashes:
- Multiple coroutines calling `ClientWebSocket.receive()` concurrently cause aiohttp to throw `Concurrent call to receive() is not allowed`
- Concurrent calls to `_get_http_session()` / `_get_ws_session()` may create multiple sessions, and `_drain_sessions()` does not close old connections, causing connection leaks
- The exception handling order in `request()` is incorrect: `except ClientConnectionError` (ErisPulse exception) is never triggered, aiohttp connection errors are caught by the general `except Exception`, causing the "retry + session reinitialization" logic (dead code) to never execute
- `send_json()` ignores the `mode="binary"` parameter; `_get_ws_session()` does not pass default request headers

**Cause**: The initial client implementation (2.4.6-dev.5) lacked concurrent protection and exception classification, and improperly handled the relationship between aiohttp exception hierarchy and ErisPulse custom exceptions.

**Affected Versions**: 2.4.6-dev.5 - 2.4.8

**Fixed Version**: 2.4.8

**Fix Content**:
1. Add `_recv_lock` to serialize all `receive()` / `receive_text()` / `receive_bytes()` calls
2. Add `_session_lock` to protect session creation; `_drain_sessions()` is changed to an async method and truly closes old sessions
3. Refactor `request()` exception handling order: `asyncio.TimeoutError` → `aiohttp.ClientConnectionError` (triggers session reinitialization) → `aiohttp.ClientError` → `ClientError` (transparent pass) → `Exception`
4. Fix `send_json()`'s mode handling, `_get_ws_session()` default request header pass, `close()` concurrency race, `HttpResponse.__aexit__` duplicate `release()`

**Fix Date**: 2026/06/12

**Severity**: 🔴 Severe

**Type**: Client

---

### [BUG-019] Adapter hot reload causes route conflict and reload failure

**Problem**: When a third-party module (such as Dashboard) triggers adapter hot reload, or when adapter startup fails and retries, because the old routes (such as `onebot11_default`) registered last time are not cleared, a `WebSocket path ... already registered` conflict is thrown, causing the reload to fail. The process needs to be completely restarted to recover.

**Cause**: `AdapterManager.shutdown()` only cleans routes with `unregister_all_by_namespace(platform)`, but adapters (such as OneBot11) register WebSocket routes with `onebot11_{account_name}` as the namespace, resulting in a mismatch in granularity and making cleanup an empty operation; startup failure retry paths also do not clear the previous route residue.

**Affected Versions**: Early versions - 2.4.9

**Fixed Version**: 2.4.9

**Fix Content**:
1. Automatically track `owner → namespace` ownership relationships during route registration via `current_owner` ContextVar
2. Add `unregister_all_by_owner(owner)`, stopping/restarting simultaneously cleans by owner, covering fine-grained namespaces
3. Add the primitive `_stop_adapter(platform)` ("stop equals cleanup"), binding stopping the adapter and reclaiming its registered resources in a single call, `restart()` and startup failure retry both go through this entry
4. Add framework-level `adapter.restart(platform)` API, third-party modules should call this method instead of directly operating adapter instances

**Fix Date**: 2026/06/12

**Severity**: 🔴 Severe

**Type**: Adapter / Router

---

### [BUG-020] Subprocess mode `ep run <script>` cannot find subpackages in script directory

**Problem**: When running a script using `ep r .\main.py` in non-hot-reload mode, if the script has relative imports (such as `from qg import ...`), it reports a `No module named 'qg'` error. However, the `--reload` mode can run normally.

**Cause**: The non-hot-reload mode directly calls `runpy.run_path()` to execute the script, and this function does not automatically add the script's directory to `sys.path`. The `--reload` mode runs via `subprocess.Popen` subprocess, which automatically inherits the current working directory, so `sys.path[0]` is the script's directory, allowing normal operation.

**Affected Versions**: 2.5.0 - 2.5.2-dev.0

**Fixed Version**: 2.5.2-dev.0

**Fix Content**: Before calling `runpy.run_path()`, manually insert the script's directory into `sys.path[0]`.

**Fix Date**: 2026/06/27

**Severity**: 🟡 Moderate

**Type**: CLI

---

### [BUG-021] SQL query builder rejects valid wildcard and list expressions

**Problem**: `SQLiteQueryBuilder`'s `_build_select_sql()` calls `_validate_identifier()` for all SELECT columns, and this function uses a strict whitelist regex `^[a-zA-Z_][a-zA-Z0-9_]*$`, causing legitimate SQL syntax to be misjudged as unsafe column names:

- `SELECT *` — `*` is a standard SQL wildcard
- `SELECT COUNT(*)` — aggregate function
- `SELECT users.name` — qualified column name
- `SELECT col AS alias` — column alias

Among these, `Select("*")` is used by modules like Cron, causing module `on_load` execution to fail and the module cannot be loaded.

**Cause**: In version 2.4.6, SQL injection protection was enhanced, introducing `_validate_identifier()` whitelist validation. This validation is applied to all column names but does not distinguish between read-end (SELECT/ORDER BY) and write-end (INSERT/UPDATE). SELECT columns allow complex SQL expressions and should not be restricted by simple identifier whitelist.

**Affected Versions**: 2.4.6 - 2.5.2-dev.1

**Fixed Version**: 2.5.2-dev.2

**Fix Content**: Change the column validation for SELECT/ORDER BY from whitelist mode to blacklist mode:
1. Add `_validate_select_column()` function, only intercepting SQL injection dangerous characters (`;` `'` `"` `--` `/*` `*/` `\x00` newline)
2. Allow any valid SQL column expression (`*`, `table.*`, `table.column`, `COUNT(*)`, `col AS alias`, etc.)
3. INSERT/UPDATE column names still maintain strict whitelist validation (only allow simple identifiers)

**Fix Date**: 2026/06/29

**Severity**: 🔴 Severe

**Type**: Storage

---

### [BUG-022] _resolve_account() account resolution regression (_accounts_data not filled)

**Problem**: After the configuration system was refactored in version 2.5.2, multi-account adapters declaring `AccountConfigClass` report an error `ValueError("AccountConfigClass not declared, unable to resolve account")` when calling methods that need to send messages, such as `wait_reply` and `reply`. Even if the adapter correctly configures multi-account information, account resolution still fails.

**Cause**: In 2.5.2-dev.5, `_load_accounts()` (responsible for reading configuration + validation + filling `_accounts_data`) was refactored into `_ensure_accounts_exist()` (only generating configuration template), but `_resolve_account()` still checks `self._accounts_data is None`. Since `_ensure_accounts_exist()` no longer fills `_accounts_data`, this attribute remains `None`, causing `_resolve_account()` to prematurely return `(None, None)`, and account resolution completely fails.

**Root Cause Chain**:
```
_load_accounts() was deleted
  → __init__ no longer fills _accounts_data
    → _accounts_data is always None
      → _resolve_account() checks _accounts_data is None → return (None, None)
        → places that call _resolve_account() (such as call_api) get None
          → triggers error
```

**Affected Versions**: 2.5.2-dev.5 - 2.5.2

**Fixed Version**: 2.5.3

**Fix Content**: Restore `_accounts_data` filling in `BaseAdapter.__init__` after `_ensure_accounts_exist()`:
```python
if self.AccountConfigClass is not None:
    self._ensure_accounts_exist()
    self._accounts_data = self.accounts  # Restore filling, data source is real-time read accounts property
```
The `_resolve_account()` logic remains unchanged, fully backward compatible:
- Adapters that do not declare `AccountConfigClass`: `_accounts_data` remains `None` → return `(None, None)`
- Adapters that declare `AccountConfigClass`: `_accounts_data` is filled → normal resolution
- Adapters that overwrite `_load_accounts` or manually set `_accounts_data`: overwrite in `super().__init__()` after, highest priority

**Fix Date**: 2026/07/07

**Severity**: 🔴 Severe

**Type**: Adapter / Configuration System

---

### [BUG-023] Adapter cache not refreshed after account configuration modification causes account resolution failure

**Problem**: After users modify the account configuration of a multi-account adapter (such as filling in the token) through Dashboard, the adapter still uses the old cache, and calling message-sending-related methods reports `No available account found (account_id=default)`. The process must be restarted for the new configuration to take effect.

**Cause**: `_accounts_data` is only read once from the configuration storage at `BaseAdapter.__init__`, and is not refreshed afterwards. `AdapterManager._run_adapter()` and `restart()` do not re-read the account configuration before calling `adapter.start()`, causing the cache to be out of sync with the actual configuration.

**Affected Versions**: 2.4.6 - 2.5.4

**Fixed Version**: 2.5.4

**Fix Content**: In `AdapterManager._run_adapter()` and `restart()`, refresh `adapter._accounts_data = adapter.accounts` before calling `adapter.start()`, ensuring the latest configuration is used for each startup.

**Fix Date**: 2026/07/09

**Severity**: 🔴 Severe

**Type**: Adapter / Configuration System

---

### [BUG-024] storage.set() triggers OOM Kill when writing large numeric ID keys

**Problem**: When calling `storage.set()` to write a nested key path containing a large numeric field (such as QQ group ID `871684833`), the process is OOM killed (exit code -9), and the service crashes and cannot recover.

**Cause**: In the recursive implementation of `_set_nested_value`, pure numeric fields in the nested key path are mistakenly identified as list indices by `isdigit()`, triggering `current.extend([None] * (index - len(current) + 1))`, attempting to allocate a list with hundreds of millions of elements, instantly exhausting memory.

**Root Cause Chain**:
```
Key path contains pure numeric field (such as group ID 871684833)
  → isdigit() mistakenly identifies as array index
    → extend([None] * (871684833 - len(current) + 1))
      → attempts to allocate hundreds of millions of elements
        → memory exhausted → container OOM Kill (exit code -9)
```

**Affected Versions**: 2.5.1 - 2.5.5

**Fixed Version**: 2.5.5

**Fix Content**:
1. Always use a dictionary when pre-creating intermediate layers, never guess the container type based on whether the next segment is a number
2. When setting the final value, only handle as an index if the container itself is a list and the index is less than `STORAGE_MAX_LIST_INDEX` (10000), safely skipping large indices
3. Change the recursive implementation to an iterative one, eliminating the potential for infinite recursion in the original code
4. Add `STORAGE_MAX_LIST_INDEX` constant to `Core/constants.py`, centrally managing the safe index upper limit

**Fix Date**: 2026/07/10

**Reproduction Steps**:
```python
# Writing a nested key path containing a large number field (such as a QQ group ID) can trigger the OOM
await sdk.storage.aset("groups.871684833.name", "Some group")
# → Process memory surges instantly, OOM Kill
```

**Regression Test**: `tests/unit/test_unit_storage.py` adds 4 regression test cases
- `test_nested_key_numeric_segment_as_dict_key` — precisely reproduces the OOM scenario
- `test_nested_key_numeric_segment_multiple` — multiple consecutive numeric fields as dictionary keys
- `test_nested_key_existing_list_index_set_within_limit` — existing list reasonable index write
- `test_nested_key_list_index_safety_limit` — safety limit verification for large indices

**Severity**: 🔴 Severe

**Type**: Storage

---

### [BUG-025] on_config_update callback not routed by core

**Problem**: `on_config_update(old, new)` callback is defined in the base class (`BaseModule` / `BaseAdapter`), but the framework core does not associate it with the configuration change event. The actual behavior is: when changing configuration through the configuration management panel, it can be triggered, but when manually editing `config.toml` or calling `setConfig()` through code, `on_config_update` is not triggered.

**Cause**: When `ConfigManager` changes configuration, it emits `config.set` / `config.updated` lifecycle events, but lacks the subscription logic to forward these events to each component's `on_config_update` method.

**Root Cause Chain**:
```
Core does not subscribe to config.set / config.updated
  → configuration change events are not forwarded
    → on_config_update is not called
      → manual file editing / code setConfig does not trigger hot update callback
```

**Affected Versions**: All versions

**Fixed Version**: 2.6.2

**Fix Content**: `ModuleManager` / `AdapterManager` register `config.set` (covering code `setConfig()` path) and `config.updated` (covering manual file editing path) event subscriptions, match by configuration key prefix and call the corresponding component's `on_config_update`, passing type-safe configuration objects. Also fix `_flush_config()` writing file without synchronizing `_config_mtime`, avoiding the framework's own write being mistakenly judged as external modification by file monitoring tasks and repeatedly triggering `config.updated`.

**Compatibility Note**: Configuration hot update is now uniformly maintained by the framework core. The logic previously triggered by the configuration management panel has been removed, and upgrading the framework requires simultaneous upgrade of the configuration management panel, otherwise duplicate triggering (core + panel each called once) will occur. The `on_config_update` method signature and semantics remain unchanged, and subclasses do not need modification.

**Fix Date**: 2026/07/23

**Severity**: 🟡 Moderate

**Type**: Configuration System

---

### [BUG-026] notice/request event reply target inferred incorrectly

**Problem**: When calling `event.reply()` in a group notification event (such as member joining a group `group_member_increase`), the message is sent to the user who triggered the event's private chat, not to the group where the event occurred. The same applies to friend notification events, where the reply target may be incorrect.

**Cause**: `infer_receive_type()` directly returns the event's `detail_type` as the session type. For message events, this is correct (`detail_type` values `private`/`group` are session types), but for notice/request events, `detail_type` is a semantic subtype (such as `group_member_increase`, `friend_increase`), not a session type. The subsequent `convert_to_send_type()` and `get_id_field()` cannot find the value in the mapping table, defaulting to `"user"` / `"user_id"`, causing the reply target to be incorrect.

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

**Fix Content**: `infer_receive_type()` adds a check—`detail_type` is only returned directly if it is a known session type (standard or custom type); otherwise, the correct session type is inferred based on the ID field (`group_id` / `channel_id` / `user_id`, etc.).

**Regression Test**: `tests/unit/test_unit_session_type.py` → `TestNoticeRequestTypeInference` (10 test cases)

**Fix Date**: 2026/07/29

**Severity**: 🟢 Minor

**Type**: Event System