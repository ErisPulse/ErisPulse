# Bug Tracker

This document records the known bugs of the ErisPulse SDK and their fixes, arranged in chronological order by the version in which they were fixed.

> **For Readers**
> No software is inherently perfect; even the most careful developers leave small errors. The bugs recorded here are all issues that have a tangible impact on operation—those that are too minor to even reach the "minor" level will not appear here. Although the list contains many "severe" items, the original intention of publicly documenting these bugs is to facilitate smoother troubleshooting and traceability, not to create anxiety: problems that are visible, recorded, and fixed are themselves proof that the project is continuously improving. Seeing this list should not cause worry—it is a troubleshooting tool, not a source of fear.

> **How to Read & Maintenance Conventions**
> - Each bug record includes structured fields such as problem description, root cause analysis, affected version range, and fix solution. It is recommended to check if the "affected version" covers your current version before upgrading.
> - If you need to add a new bug entry, please supplement content at the corresponding position, following the field specifications and severity/type classifications described below.

---

## Field Descriptions

### Required Fields

| Field | Description |
|------|------|
| **Problem** | The external manifestation of the bug, observable abnormal phenomena by the user. Try to provide error messages or typical scenarios |
| **Cause** | Root cause analysis, pointing to specific code defects (including "root cause chain" diagrams for complex scenarios) |
| **Affected Version** | The affected version range, in the format `Introduced Version - Fixed Version` (including both dev versions) |
| **Fixed Version** | The specific version number that fixed the bug |
| **Fix Content** | A brief description of the fix, including key code changes |
| **Fix Date** | The release date corresponding to the fixed version, in the format `YYYY/MM/DD` |
| **Severity** | Marked according to the "Severity Classification" below |
| **Type** | Marked according to the "Type Classification" below, can be combined (e.g., `Adapter / Router`) |

### Optional Fields

| Field | Description | Applicable Scenarios |
|------|------|---------|
| **Reproduction Steps** | The minimal reproducible path to trigger the bug | Complex bugs, occasional bugs are recommended to supplement |
| **关联** | Related Issue / PR / Commit links | Supplement when there are external discussion records |
| **Regression Test** | Test case location for verifying the fix and preventing regression | Supplement when corresponding pytest cases have been written |

---

## Severity Classification

| Identifier | Level | Judgment Criteria | Typical Manifestations |
|------|------|---------|---------|
| 🔴 | Severe | Causes process crash, data loss/damage, core functionality completely unusable, security vulnerabilities | OOM Kill, message cannot be sent, module cannot be loaded, hot reload failure |
| 🟡 | Moderate | Functional abnormalities but with workaround paths, non-core functionality failure, occasional problems | Incorrect status judgment, repeated triggering, cache expiration, inaccurate error prompts |
| 🟢 | Minor | Does not affect core functionality, only code quality or experience issues, potential risks not yet triggered | Deprecated API, dead code, missing warning logs |

---

## Type Classification

| Type | Coverage Scope |
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
| 🟢 Minor | 1 |
| **Total** | **25** |

| Type | Count |
|------|------|
| Adapter | 6 |
| Event System | 4 |
| Storage | 3 |
| Loader | 3 |
| CLI | 3 |
| Configuration System | 3 |
| Router | 1 |
| Client | 1 |
| Runtime | 1 |

> Note: A single bug can belong to multiple types; the above table counts based on the primary type.

---

## Fixed Bugs

### [BUG-001] Event handler duplicate registration causes event to be processed multiple times

**Problem**: When registering handlers using multiple `@message` / `@notice` decorators, the same event is triggered multiple times, causing commands to be executed multiple times and logs to be output repeatedly.

**Cause**: `BaseEventHandler` lacks deduplication logic when registering handlers to the adapter event bus. Each decorator mounts the handler to the bus once, resulting in multiple calls during event distribution.

**Affected Version**: 2.2.0-dev.0 - 2.2.1-dev.0

**Fixed Version**: 2.2.1-dev.0

**Fix Content**: Optimize `BaseEventHandler` to ensure each event type is registered to the adapter only once, avoiding repeated triggers.

**Fix Date**: 2025/08/18

**Severity**: 🔴 Severe

**Type**: Event System

---

### [BUG-002] Init command adapter configuration path type error

**Problem**: When using the `ep init` command for interactive initialization, selecting the configuration adapter results in a type error:

```
Interactive initialization failed: unsupported operand type(s) for /: 'str' and 'str'
```

**Cause**: When adjusting the configuration file path in version 2.3.7, the method parameter types were inconsistent. `_configure_adapters_interactive_sync` receives a `str` type parameter, but internally uses the `Path` `/` operator to concatenate paths.

**Affected Version**: 2.3.7 - 2.3.9-dev.1

**Fixed Version**: 2.3.9-dev.1

**Fix Content**: Change the parameter type of the `_configure_adapters_interactive_sync` method from `str` to `Path`, passing a `Path` object directly when calling.

**Fix Date**: 2026/03/23

**Severity**: 🟡 Moderate

**Type**: CLI

---

### [BUG-003] Commands fail after restart

**Problem**: After calling `sdk.restart()`, commands registered via `@command` are not triggered, resulting in the robot not responding after sending a command.

**Cause**: After `adapter.shutdown()` clears the event bus, the `_linked_to_adapter_bus` status of `BaseEventHandler` is not reset to `False`, causing the `_process_event` method to think it has been mounted to the adapter bus and skip the re-mounting operation.

**Affected Version**: 2.2.x - 2.4.0-dev.2

**Fixed Version**: 2.4.0-dev.3

**Fix Content**: Introduce `_linked_to_adapter_bus` status tracking. After `_clear_handlers()` disconnects from the bus, `register()` automatically re-mounts next time, adapting to shutdown/restart scenarios.

**Fix Date**: 2026/04/09

**Severity**: 🔴 Severe

**Type**: Event System

---

### [BUG-004] Lifecycle event handlers not cleared

**Problem**: After `sdk.restart()`, old lifecycle event handlers still exist and are triggered repeatedly, causing the same event to be processed multiple times.

**Cause**: The `lifecycle._handlers` dictionary was never cleared in `uninit()`, causing old and new handlers to coexist after restart.

**Affected Version**: 2.3.0 - 2.4.0-dev.2

**Fixed Version**: 2.4.0-dev.3

**Fix Content**: Clear `lifecycle._handlers` at the end of the `Uninitializer` cleanup process (after all events are submitted).

**Fix Date**: 2026/04/09

**Severity**: 🟡 Moderate

**Type**: Runtime

---

### [BUG-005] Event.is_friend_add/is_friend_delete detail_type inconsistent with OB12 standard

**Problem**: `Event.is_friend_add()` checks `detail_type == "friend_add"`, `Event.is_friend_delete()` checks `detail_type == "friend_delete"`, but OneBot12 standard defines `detail_type` values as `"friend_increase"` and `"friend_decrease"`. Inconsistent with values used by `notice.py`'s `on_friend_add`/`on_friend_remove` decorators, causing handlers registered via decorators to return `False` when `is_friend_add()`/`is_friend_delete()` judgment methods are triggered.

**Cause**: `wrapper.py` uses non-standard naming, while `notice.py` uses correct OB12 standard naming.

**Affected Version**: Implemented to present

**Fixed Version**: 2.4.2-dev.1

**Fix Content**: Change `is_friend_add()`'s matching value from `"friend_add"` to `"friend_increase"`, `is_friend_delete()` from `"friend_delete"` to `"friend_decrease"`.

**Fix Date**: 2026/04/13

**Severity**: 🟡 Moderate

**Type**: Event System

---

### [BUG-006] adapter.clear() does not clear _started_instances causing incorrect status after restart

**Problem**: The `AdapterManager.clear()` method clears `_adapters`, `_adapter_info`, handlers, and `_bots`, but omits `_started_instances` set. If `clear()` is called while the adapter is running, `_started_instances` retains dangling references, causing incorrect status judgment after restart.

**Cause**: When `_started_instances` was introduced in 2.4.0-dev.1, it was not synchronized in `clear()`.

**Affected Version**: 2.4.0-dev.1 - 2.4.2-dev.0

**Fixed Version**: 2.4.2-dev.1

**Fix Content**: Add `self._started_instances.clear()` in the `clear()` method.

**Fix Date**: 2026/04/13

**Severity**: 🟡 Moderate

**Type**: Adapter

---

### [BUG-007] command.wait_reply() uses deprecated asyncio.get_event_loop()

**Problem**: The `CommandHandler.wait_reply()` method uses `asyncio.get_event_loop()` to create futures and get timestamps. This method has been deprecated in Python 3.10+, and `asyncio.get_running_loop()` should be used in asynchronous contexts. Inconsistent with `wrapper.py`'s `wait_for()` method in the same file, which uses `get_running_loop()`.

**Cause**: The old API was used during development, and the newly added `wait_for()` method used the correct API but did not retroactively fix the old code.

**Affected Version**: 2.3.0-dev.0

**Fixed Version**: 2.4.2-dev.1

**Fix Content**: Replace `asyncio.get_event_loop()` with `asyncio.get_running_loop()` in two places in `command.py`.

**Fix Date**: 2026/04/13

**Severity**: 🟢 Minor

**Type**: Event System

---

### [BUG-008] Bot offline event repeatedly submitted during shutdown

**Problem**: When calling `adapter.shutdown()` to close all adapters, `_update_bot_status()` repeatedly submits Bot offline events during the shutdown process, causing the same batch of Bots to be marked offline multiple times and triggering multiple `adapter.bot.offline` lifecycle events.

**Cause**: The Bot status tracking system introduced in 2.4.0-dev.1 did not set a "shutting down" flag during `shutdown()`, so `_update_bot_status()` could not distinguish between normal offline and cascading offline during shutdown.

**Affected Version**: 2.4.0-dev.1 - 2.4.2-dev.1

**Fixed Version**: 2.4.2-dev.1

**Fix Content**: Add `_is_being_shutdown` flag in `AdapterManager`, set to True at the start of `shutdown()` and cleared at the end; `_update_bot_status()` checks this flag and skips repeated submissions during shutdown.

**Fix Date**: 2026/04/21

**Severity**: 🟡 Moderate

**Type**: Adapter

---

### [BUG-009] LazyModule synchronous access to BaseModule causes incomplete initialization

**Problem**: When users access properties of a lazily loaded BaseModule in a synchronous context, the module uses `loop.create_task()` for asynchronous initialization but does not wait, leading to race conditions when accessing properties before initialization is complete.

**Cause**: `_ensure_initialized()` uses `loop.create_task(self._initialize())` and returns immediately without ensuring initialization is complete.

**Affected Version**: 2.4.0-dev.0 - 2.4.2-dev.1

**Fixed Version**: 2.4.2-dev.2

**Fix Content**: In synchronous contexts, BaseModule initialization is changed to use `asyncio.run(self._initialize())` to ensure initialization is complete before returning. The transparent proxy feature is maintained, and users do not need to be aware of the difference between synchronous and asynchronous contexts.

**Fix Date**: 2026/04/21

**Severity**: 🟡 Moderate

**Type**: Loader

---

### [BUG-010] Multi-threaded configuration system writes cause data loss

**Problem**: In a multi-threaded environment, multiple threads calling `config.setConfig()` simultaneously result in non-atomic read-modify-write operations in `_flush_config()`, potentially causing partial write loss.

**Cause**: Although `_flush_config()` uses `RLock`, there is no file lock protection between file read and write, and the `_schedule_write` Timer may be triggered multiple times, causing overwrite.

**Affected Version**: 2.3.0 - 2.4.2-dev.1

**Fixed Version**: 2.4.2-dev.2

**Fix Content**:
1. Add file locking mechanism (`_file_lock`) to ensure atomic file operations
2. Write to a temporary file and then atomically rename it (`os.replace`/`os.rename`)
3. Improve `_schedule_write` Timer cancellation and rescheduling logic

**Fix Date**: 2026/04/21

**Severity**: 🔴 Severe

**Type**: Configuration System

---

### [BUG-011] Windows Ctrl+C cannot stop the program

**Problem**: When running `python main.py` directly on Windows, pressing Ctrl+C does not terminate the program. After the program starts normally and outputs the routing server information, Ctrl+C has no response at all, and the process can only be forcibly killed through the task manager. However, it can be stopped normally when started via `epsdk run`—but `epsdk run` runs through a subprocess model.

**Cause**: The `serve()` function of the Hypercorn ASGI server internally registers its own SIGINT handler via `signal.signal(SIGINT, handler)`, overriding Python's default `KeyboardInterrupt` handling mechanism. When Hypercorn is started as a background task via `asyncio.create_task()`, its internal shutdown process cannot be triggered normally (because it expects the `worker_serve` mode), causing the Ctrl+C signal to be swallowed by Hypercorn without triggering any cleanup actions.

**Affected Version**: 2.3.6 - 2.4.2

**Fixed Version**: 2.4.3-dev.0

**Fix Content**:
1. Switch the ASGI server from Hypercorn to Uvicorn (`pyproject.toml` dependency change)
2. Use `uvicorn.Server._serve()` to start the server directly, **bypassing** the `capture_signals()` signal handling context manager
3. Implement graceful shutdown via `server.should_exit = True`, and cancel the background task if timeout occurs
4. Synchronously remove the subprocess running model and the `runtime/cleanup.py` cleanup module (subprocess cleanup mechanism is no longer needed)

**Fix Date**: 2026/04/28

**Severity**: 🔴 Severe

**Type**: CLI / Runtime

---

### [BUG-012] Hot restart does not activate updated module Python code

**Problem**: After executing `sdk.restart()` soft restart, the new code (such as new API routes) of modules/adapters upgraded via `epsdk install` does not take effect, and the old logic is still running. The latest code must be loaded by completely restarting the process.

**Cause**: `_do_restart()` calls `entry_point.load()` when reinitializing, but this function returns cached old module objects from `sys.modules` instead of reloading from disk.

**Affected Version**: Early versions - 2.4.3-dev.1

**Fixed Version**: 2.4.3-dev.1

**Fix Content**: Clear the cache of loaded modules/adapters packages in `sys.modules` before `init()` and after `uninit()` so that `entry_point.load()` loads the latest code from disk. Add auxiliary methods `_collect_top_level_modules()` and `_invalidate_module_cache()` to derive top-level module names via `top_level.txt` or entry-point value.

**Fix Date**: 2026/05/03

**Severity**: 🔴 Severe

**Type**: Loader / Runtime

---

### [BUG-013] Module loading strategy sort logic error

**Problem**: `ModuleLoadStrategy` provides a `priority` field to declare module initialization priority, but the implementation of the loading strategy has a mistake, causing modules to not be initialized in the expected priority order; instead, they are loaded in the default order of `entry_points()`. When there are initialization dependencies between modules, `priority` cannot ensure the correct initialization order.

**Cause**: There is a mistake in the sorting logic of the loading strategy implementation; `initialize_modules()` does not sort the module list by `priority`.

**Affected Version**: 2.3.4 - 2.4.5-dev.2

**Fixed Version**: 2.4.5-dev.3

**Fix Content**: Before traversing `initialize_modules()`, sort the module list by `priority` in descending order. Modules with the same priority maintain their original relative order (stable sorting).

**Fix Date**: 2026/05/15

**Severity**: 🟡 Moderate

**Type**: Loader

---

### [BUG-014] Adapter middleware returning None causes event data loss

**Problem**: When executing the OneBot12 middleware chain in `adapter.emit()`, if a middleware returns `None` (e.g., forgetting to `return data`), the `processed_data` received by subsequent middlewares and all event handlers becomes `None`, causing event processing to fail completely.

**Cause**: The middleware chain implementation `processed_data = await middleware(processed_data)` does not check if the return value is `None`, directly overwriting the result of the previous step.

**Affected Version**: unknown - 2.4.5-dev.3

**Fixed Version**: 2.4.5-dev.4

**Fix Content**: When middleware returns `None`, ignore the return value, retain the original data, and continue passing it, outputting a warning-level log.

**Fix Date**: 2026/05/15

**Severity**: 🔴 Severe

**Type**: Adapter / Event System

---

### [BUG-015] Configuration file path depends on working directory

**Problem**: The configuration file path of `ConfigManager` is a relative path `"config/config.toml"` by default, and is resolved at runtime using `os.getcwd()`. If the working directory changes during runtime (e.g., via `os.chdir()`), configuration file read/write operations will point to the wrong location, causing configuration loss or reading old data.

**Cause**: The relative path is directly stored in `__init__` without being resolved to an absolute path at initialization.

**Affected Version**: 2.3.7 - 2.4.5-dev.3

**Fixed Version**: 2.4.5-dev.4

**Fix Content**: In `ConfigManager.__init__()`, if the passed path is a relative path, automatically resolve it to an absolute path using `os.path.abspath()`.

**Fix Date**: 2026/05/15

**Severity**: 🟡 Moderate

**Type**: Configuration System

---

### [BUG-016] BaseStorage confuses storing None value with key not existing

**Problem**: `BaseStorage.get_multi()` / `__getattr__()` cannot distinguish between "key does not exist" and "the key's value is None", so after a user explicitly stores `None` and reads it again, it is treated as if the key does not exist.

**Cause**: The value retrieval logic directly uses `value is None` to determine if the key exists, lacking an independent "missing" marker.

**Affected Version**: Early versions - 2.4.6-dev.6

**Fixed Version**: 2.4.6-dev.6

**Fix Content**: Introduce `_SENTINEL` sentinel value to distinguish "key does not exist" from "value is None", so they are no longer confused.

**Fix Date**: 2026/06/07

**Severity**: 🟡 Moderate

**Type**: Storage

---

### [BUG-017] WebSocket route auto_accept flag lost after service restart

**Problem**: After service restart (e.g., `sdk.restart()`), the `auto_accept` configuration of all WebSocket routes is reset to `False`. Connections that were expected to be automatically accepted become pending, and clients receive no response for a long time, resulting in WS connections being stuck.

**Cause**: `_restore_routes_from_records()` hardcodes `auto_accept` to `False` when restoring routes from persistent records, not reading the value from the original record; at the same time, the route storage tuple was extended from a binary tuple to a ternary tuple without synchronously updating the restoration logic.

**Affected Version**: 2.3.8-dev.0 - 2.4.6-dev.6

**Fixed Version**: 2.4.6-dev.6

**Fix Content**: The route storage tuple is extended to `(handler, auth_handler, auto_accept)`, and `_restore_routes_from_records()` reads the real `auto_accept` value from the record instead of hardcoding `False`.

**Fix Date**: 2026/06/07

**Severity**: 🔴 Severe

**Type**: Router

---

### [BUG-018] HTTP/WS client concurrent calls cause crash and connection leak

**Problem**: The HTTP and WebSocket clients in `Core/client.py` have multiple stability defects in concurrent scenarios, leading to connection leaks or process crashes:
- Concurrent calls to `ClientWebSocket.receive()` by multiple coroutines cause aiohttp to throw `Concurrent call to receive() is not allowed`
- Concurrent calls to `_get_http_session()` / `_get_ws_session()` may create multiple sessions, and `_drain_sessions()` does not close old connections, causing connection leaks
- The exception handling order in `request()` is incorrect: `except ClientConnectionError` (ErisPulse exception) is never triggered, aiohttp connection errors are caught by generic `except Exception`, causing the "retry connection + session rebuild" logic (dead code) to never execute
- `send_json()` ignores the `mode="binary"` parameter; `_get_ws_session()` does not pass default request headers

**Cause**: The client's initial implementation (2.4.6-dev.5) lacks concurrency protection and exception classification, and improperly handles the inheritance relationship between aiohttp exception system and ErisPulse custom exceptions.

**Affected Version**: 2.4.6-dev.5 - 2.4.8

**Fixed Version**: 2.4.8

**Fix Content**:
1. Add `_recv_lock` to serialize all `receive()` / `receive_text()` / `receive_bytes()` calls
2. Add `_session_lock` to protect session creation; `_drain_sessions()` is changed to an async method and truly closes old sessions
3. Refactor `request()` exception handling order: `asyncio.TimeoutError` → `aiohttp.ClientConnectionError` (triggers session rebuild) → `aiohttp.ClientError` → `ClientError` (transparent pass) → `Exception`
4. Fix `send_json()`'s mode handling, `_get_ws_session()` default request header pass, `close()` concurrent race, `HttpResponse.__aexit__` repeated `release()`

**Fix Date**: 2026/06/12

**Severity**: 🔴 Severe

**Type**: Client

---

### [BUG-019] Adapter hot reload causes route conflict and reload failure

**Problem**: When a third-party module (such as Dashboard) triggers adapter hot reload, or when an adapter fails to start and retries, the old routes (such as `onebot11_default`) registered in the previous session are not cleared, causing a `WebSocket path ... already registered` conflict, leading to reload failure. The process needs to be completely restarted to recover.

**Cause**: `AdapterManager.shutdown()` only clears routes with `unregister_all_by_namespace(platform)`, but adapters (such as OneBot11) register WebSocket routes with `onebot11_{account_name}` as the namespace, resulting in a granularity mismatch and making the cleanup an empty operation; the route from the failed startup retry is also not cleared of the previous residual route.

**Affected Version**: Early versions - 2.4.9

**Fixed Version**: 2.4.9

**Fix Content**:
1. Automatically track `owner → namespace` ownership relationships during route registration via `current_owner` ContextVar
2. Add `unregister_all_by_owner(owner)`, stopping/restarting with owner-level cleanup, covering fine-grained namespaces
3. Add `_stop_adapter(platform)` primitive ("stop and clean up"), binding stopping the adapter and reclaiming its registered resources in a single call; `restart()` and failed startup retry both go through this entry
4. Add framework-level `adapter.restart(platform)` API; third-party modules should call this method instead of directly manipulating adapter instances

**Fix Date**: 2026/06/12

**Severity**: 🔴 Severe

**Type**: Adapter / Router

---

### [BUG-020] Subprocess mode `ep run <script>` cannot find subpackages in the script's directory

**Problem**: When running a script using `ep r .\main.py` in non-hot-reload mode, if the script has relative imports (such as `from qg import ...`), it reports a `No module named 'qg'` error. However, the `--reload` mode works normally.

**Cause**: The non-hot-reload mode directly calls `runpy.run_path()` to execute the script, which does not automatically add the script's directory to `sys.path`. In contrast, the `--reload` mode runs through `subprocess.Popen` subprocess, which automatically inherits the current working directory, making `sys.path[0]` the script's directory, so it works normally.

**Affected Version**: 2.5.0 - 2.5.2-dev.0

**Fixed Version**: 2.5.2-dev.0

**Fix Content**: Before calling `runpy.run_path()`, manually insert the script's directory into `sys.path[0]`.

**Fix Date**: 2026/06/27

**Severity**: 🟡 Moderate

**Type**: CLI

---

### [BUG-021] SQL query builder rejects legitimate wildcard and list expressions

**Problem**: `SQLiteQueryBuilder`'s `_build_select_sql()` calls `_validate_identifier()` for all SELECT columns, and this function uses a strict whitelist regular expression `^[a-zA-Z_][a-zA-Z0-9_]*$`, causing legitimate SQL syntax to be incorrectly judged as unsafe column names:

- `SELECT *` — `*` is a standard SQL wildcard
- `SELECT COUNT(*)` — aggregate function
- `SELECT users.name` — qualified column name
- `SELECT col AS alias` — column alias

Among them, `Select("*")` is used by modules like Cron, causing module `on_load` execution to fail and the module cannot be loaded.

**Cause**: In version 2.4.6, SQL injection protection was enhanced, introducing the `_validate_identifier()` whitelist validation. This validation is applied to all column names, but does not distinguish between read end (SELECT/ORDER BY) and write end (INSERT/UPDATE). SELECT columns allow complex SQL expressions and should not be restricted by a simple identifier whitelist.

**Affected Version**: 2.4.6 - 2.5.2-dev.1

**Fixed Version**: 2.5.2-dev.2

**Fix Content**: Change the column validation for SELECT/ORDER BY from whitelist mode to blacklist mode:
1. Add `_validate_select_column()` function, only intercepting SQL injection dangerous characters (`;` `'` `"` `--` `/*` `*/` `\x00` newline)
2. Allow any valid SQL column expression (`*`, `table.*`, `table.column`, `COUNT(*)`, `col AS alias`, etc.)
3. INSERT/UPDATE column names still maintain strict whitelist validation (only allow simple identifiers)

**Fix Date**: 2026/06/29

**Severity**: 🔴 Severe

**Type**: Storage

---

### [BUG-022] _resolve_account() account resolution regression (_accounts_data not populated)

**Problem**: After the configuration system was refactored in version 2.5.2, adapters declaring `AccountConfigClass` failed to resolve accounts when calling methods that require sending messages, such as `wait_reply` and `reply`, reporting an error `ValueError("AccountConfigClass not declared, unable to resolve account")`. Even if the adapter correctly configured multi-account information, account resolution still failed.

**Cause**: In 2.5.2-dev.5, `_load_accounts()` (responsible for reading configuration + validation + populating `_accounts_data`) was refactored into `_ensure_accounts_exist()` (only generating configuration templates), but `_resolve_account()` still checks `self._accounts_data is None`. Since `_ensure_accounts_exist()` no longer populates `_accounts_data`, this attribute is always `None`, causing `_resolve_account()` to prematurely return `(None, None)`, and account resolution fails completely.

**Root Cause Chain**:
```
_load_accounts() was deleted
  → __init__ no longer populates _accounts_data
    → _accounts_data is always None
      → _resolve_account() checks _accounts_data is None → return (None, None)
        → downstream places calling _resolve_account() (e.g., call_api) get None
          → triggers error
```

**Affected Version**: 2.5.2-dev.5 - 2.5.2

**Fixed Version**: 2.5.3

**Fix Content**: In `BaseAdapter.__init__`, after `_ensure_accounts_exist()`, restore the population of `_accounts_data`:
```python
if self.AccountConfigClass is not None:
    self._ensure_accounts_exist()
    self._accounts_data = self.accounts  # Restore population, data source is real-time read accounts attribute
```
The logic of `_resolve_account()` remains unchanged, fully backward compatible:
- Adapters that do not declare `AccountConfigClass`: `_accounts_data` remains `None` → return `(None, None)`
- Adapters that declare `AccountConfigClass`: `_accounts_data` is populated → normal resolution
- Adapters that overwrite `_load_accounts` or manually set `_accounts_data`: overwrite after `super().__init__()` call, highest priority

**Fix Date**: 2026/07/07

**Severity**: 🔴 Severe

**Type**: Adapter / Configuration System

---

### [BUG-023] Adapter cache not refreshed after account configuration modification causing account resolution failure

**Problem**: After users modify the account configuration of a multi-account adapter via Dashboard (such as filling in the token), the adapter still uses the old cache, and calls to message-sending methods report `No available account found (account_id=default)`. The process must be restarted to make the new configuration effective.

**Cause**: `_accounts_data` is only read from the configuration storage once at `BaseAdapter.__init__`, and is never refreshed afterward. `AdapterManager._run_adapter()` and `restart()` do not re-read the account configuration before calling `adapter.start()`, causing the cache to be out of sync with the actual configuration.

**Affected Version**: 2.4.6 - 2.5.4

**Fixed Version**: 2.5.4

**Fix Content**: In `AdapterManager._run_adapter()` and `restart()`, before calling `adapter.start()`, refresh `adapter._accounts_data = adapter.accounts` to ensure the latest configuration is used each time it starts.

**Fix Date**: 2026/07/09

**Severity**: 🔴 Severe

**Type**: Adapter / Configuration System

---

### [BUG-024] storage.set() writing large numeric ID keys triggers OOM Kill

**Problem**: Calling `storage.set()` to write a nested key path containing a large pure numeric field (such as QQ group number `871684833`) causes the process to be OOM killed (exit code -9), crashing the service and making it impossible to recover.

**Cause**: In the recursive implementation of `_set_nested_value`, pure numeric fields in the nested key path are mistakenly identified as list indices by `isdigit()`, triggering `current.extend([None] * (index - len(current) + 1))`, attempting to allocate a list with hundreds of millions of elements, instantly exhausting memory.

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

**Fix Content**:
1. Always use dictionaries when pre-creating intermediate layers, no longer guess container type based on whether the next segment is a number
2. When setting the final value, only process by index if the container itself is a list and the index is less than `STORAGE_MAX_LIST_INDEX` (10000); skip large indices safely
3. Change the recursive implementation to an iterative implementation, eliminating the potential for infinite recursion in the original code
4. Add `STORAGE_MAX_LIST_INDEX` constant to `Core/constants.py`, centrally managing the safe upper limit for indices

**Fix Date**: 2026/07/10

**Reproduction Steps**:
```python
# Writing a nested key path containing a large numeric field (such as a QQ group number) triggers the OOM scenario
await sdk.storage.aset("groups.871684833.name", "Some group")
# → Process memory surges instantly, OOM Kill
```

**Regression Test**: Add 4 regression test cases to `tests/unit/test_unit_storage.py`
- `test_nested_key_numeric_segment_as_dict_key` — precisely reproduces the OOM scenario
- `test_nested_key_numeric_segment_multiple` — multiple consecutive numeric fields as dictionary keys
- `test_nested_key_existing_list_index_set_within_limit` — existing list index write within limit
- `test_nested_key_list_index_safety_limit` — safety limit for large indices

**Severity**: 🔴 Severe

**Type**: Storage

---

### [BUG-025] on_config_update callback not triggered by core

**Problem**: `on_config_update(old, new)` callback is defined in the base class (`BaseModule` / `BaseAdapter`), but the core framework does not associate it with configuration change events. The actual behavior: when modifying configuration via the configuration management panel, it can be triggered, but manual editing of `config.toml` or code calling `setConfig()` does not trigger `on_config_update`.

**Cause**: `ConfigManager` emits `config.set` / `config.updated` lifecycle events when configuration changes, but lacks subscription logic to forward these events to each component's `on_config_update` method.

**Root Cause Chain**:
```
Core does not subscribe to config.set / config.updated
  → Configuration change events are not forwarded
    → on_config_update is not called
      → Manual file editing / code setConfig does not trigger hot update callback
```

**Affected Version**: All versions

**Fixed Version**: 2.6.2

**Fix Content**: `ModuleManager` / `AdapterManager` register `config.set` (covers code `setConfig()` path) and `config.updated` (covers manual file editing path) event subscriptions, match by configuration key prefix, and call the corresponding component's `on_config_update`, passing type-safe configuration objects. Also fix `_flush_config()` not synchronously updating `_config_mtime` after writing the file, preventing the framework's own write from being mistakenly judged as external modification by the file monitoring task and repeatedly triggering `config.updated`.

**Compatibility Note**: Hot configuration updates are now maintained by the core framework. The previously handled logic by the configuration management panel has been removed; after upgrading the framework, the panel must also be upgraded, otherwise duplicate triggers (core + panel each call once) will occur. The `on_config_update` method signature and semantics remain unchanged, and subclasses do not need modification.

**Fix Date**: 2026/07/23

**Severity**: 🟡 Moderate

**Type**: Configuration System