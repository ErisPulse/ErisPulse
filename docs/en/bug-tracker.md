# Bug Tracker

This document records known bugs and their fixes for the ErisPulse SDK, ordered chronologically by the version in which they were resolved.

> **For the Reader**
> No software is born perfect, and even the most careful developers leave small mistakes behind. This tracker only includes issues that have a real impact on operation—those that are so minor they don't even reach the "minor" category are not included here. Although the number of "serious" items on the list may seem large, the original intention of publicly documenting these bugs is to make troubleshooting and tracing smoother, not to create anxiety: problems that can be seen, recorded, and fixed are proof that the project is constantly improving. There is no need to be anxious when seeing this list; it is a troubleshooting tool, not a source of fear.

> **How to Read & Maintenance Conventions**
> - Each bug record contains structured fields such as problem description, root cause analysis, affected version range, fix solution, etc. It is recommended to check the "affected version" before upgrading to see if it covers the version currently in use.
> - If you need to add a new bug entry, please supplement the content at the corresponding location, following the field specifications and severity/type classification below.

---

## Field Descriptions

### Mandatory Fields

| Field | Description |
|------|------|
| **Problem** | The external manifestation of the bug, the abnormal phenomenon observable by the user. Try to provide error messages or typical scenarios |
| **Cause** | Root cause analysis, pointing to specific code defects (including "root cause chain" diagrams for complex scenarios) |
| **Affected Version** | The affected version range, in the format `introduced version - fixed version` (including both dev versions) |
| **Fixed Version** | The specific version number that fixed the bug |
| **Fix Content** | A brief description of the fix, including key code changes |
| **Fix Date** | The release date of the corresponding fixed version, in `YYYY/MM/DD` format |
| **Severity** | As specified in the "Severity Classification" below |
| **Type** | As specified in the "Type Classification" below, can be combined (e.g., `Adapter / Router`)|

### Optional Fields

| Field | Description | Applicable Scenarios |
|------|------|---------|
| **Reproduction Steps** | The minimal reproducible path to trigger the bug | Complex bugs, intermittent bugs are recommended to supplement |
| **关联** | Related Issue / PR / Commit links | Supplement when there are external discussion records |
| **Regression Test** | Test case location to verify the fix and prevent regression | Supplement when corresponding pytest cases are written |

---

## Severity Classification

| Identifier | Level | Judgment Criteria | Typical Manifestations |
|------|------|---------|---------|
| 🔴 | Severe | Causes process crash, data loss/damage, core functionality completely unavailable, security vulnerabilities | OOM Kill, message cannot be sent, module cannot be loaded, hot reload failure |
| 🟡 | Moderate | Function abnormality but with workaround, non-core functionality failure, intermittent issues | Incorrect status judgment, repeated triggering, cache expiration, inaccurate error messages |
| 🟢 | Minor | Does not affect core functionality, only code quality or experience issues, potential risks not triggered | Deprecated API, dead code, missing warning logs |

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

When adding a new bug entry, follow the following format:

```markdown
### [BUG-XXX] Title

**Problem**: Problem description (error message or typical phenomenon)
**Cause**: Root cause analysis
**Affected Version**: Introduced version - Fixed version
**Fixed Version**: x.x.x
**Fix Content**: Fix solution
**Fix Date**: YYYY/MM/DD

<!-- Optional Fields -->
**Reproduction Steps**: (Recommended for complex bugs)
**关联**: (Issue/PR links)
**Regression Test**: (Test case path)

**Severity**: 🔴 Severe | 🟡 Moderate | 🟢 Minor
**Type**: Configuration System / Event System / Adapter / Router / Client / Storage / Loader / CLI / Runtime
```

---

## Statistics Overview

| Severity | Count |
|--------|------|
| 🔴 Severe | 18 |
| 🟡 Moderate | 18 |
| 🟢 Minor | 3 |
| **Total** | **39** |

| Type | Count |
|------|------|
| Adapter | 6 |
| Configuration System | 10 |
| Event System | 7 |
| CLI | 3 |
| Storage | 3 |
| Loader | 3 |
| Router | 2 |
| Client | 1 |
| Runtime | 1 |

> Note: A single bug can belong to multiple types; the table above counts by main type.

---

## Fixed Bugs

### [BUG-001] Event handler registration duplication causes event to be processed multiple times

**Problem**: When using multiple `@message` / `@notice` decorators to register handlers, the same event is triggered multiple times, causing the command to be executed multiple times and log output repeated.

**Cause**: `BaseEventHandler` registers handlers to the adapter event bus without deduplication logic; each decorator registers once to the bus, causing the event dispatcher to be called multiple times.

**Affected Version**: 2.2.0-dev.0 - 2.2.1-dev.0

**Fixed Version**: 2.2.1-dev.0

**Fix Content**: Optimize `BaseEventHandler` to ensure each event type registers only once to the adapter, preventing repeated triggering.

**Fix Date**: 2025/08/18

**Severity**: 🔴 Severe

**Type**: Event System

---

### [BUG-002] Adapter configuration path type error in Init command

**Problem**: When using the `ep init` command for interactive initialization, selecting the configuration adapter results in a type error:

```
Interactive initialization failed: unsupported operand type(s) for /: 'str' and 'str'
```

**Cause**: In version 2.3.7, when adjusting the configuration file path, the method parameter types were inconsistent. `_configure_adapters_interactive_sync` receives a `str` type parameter, but internally uses the `Path` `/` operator to concatenate paths.

**Affected Version**: 2.3.7 - 2.3.9-dev.1

**Fixed Version**: 2.3.9-dev.1

**Fix Content**: Change the parameter type of `_configure_adapters_interactive_sync` from `str` to `Path`, passing `Path` objects directly when calling.

**Fix Date**: 2026/03/23

**Severity**: 🟡 Moderate

**Type**: CLI

---

### [BUG-003] Commands fail after restart

**Problem**: After calling `sdk.restart()`, commands registered via `@command` are not triggered, resulting in no response from the robot after sending a command.

**Cause**: `adapter.shutdown()` clears the event bus, but the `_linked_to_adapter_bus` status of `BaseEventHandler` is not reset to `False`, causing the `_process_event` method to think it is already linked to the adapter bus and skip re-linking.

**Affected Version**: 2.2.x - 2.4.0-dev.2

**Fixed Version**: 2.4.0-dev.3

**Fix Content**: Introduce `_linked_to_adapter_bus` status tracking; after `_clear_handlers()` disconnects the bus, the next `register()` will automatically re-link, adapting to shutdown/restart scenarios.

**Fix Date**: 2026/04/09

**Severity**: 🔴 Severe

**Type**: Event System

---

### [BUG-004] Lifecycle event handlers not cleaned up

**Problem**: After `sdk.restart()`, old lifecycle event handlers still exist and are triggered repeatedly, causing the same event to be processed multiple times.

**Cause**: The `lifecycle._handlers` dictionary was never cleared in `uninit()`, so old handlers and new handlers coexist after restart.

**Affected Version**: 2.3.0 - 2.4.0-dev.2

**Fixed Version**: 2.4.0-dev.3

**Fix Content**: Clear `lifecycle._handlers` at the end of the `Uninitializer` cleanup process (after all events are submitted), adapting to shutdown/restart scenarios.

**Fix Date**: 2026/04/09

**Severity**: 🟡 Moderate

**Type**: Runtime

---

### [BUG-005] Event.is_friend_add/is_friend_delete detail_type inconsistent with OB12 standard

**Problem**: `Event.is_friend_add()` checks `detail_type == "friend_add"`, `Event.is_friend_delete()` checks `detail_type == "friend_delete"`, but the OneBot12 standard defines the `detail_type` values as `"friend_increase"` and `"friend_decrease"`. This is inconsistent with the values used in `notice.py`'s `on_friend_add`/`on_friend_remove` decorators, causing the corresponding `is_friend_add()`/`is_friend_delete()` judgment methods to return `False` when handlers registered via decorators are triggered.

**Cause**: `wrapper.py` uses non-standard naming, while `notice.py` uses the correct OB12 standard naming.

**Affected Version**: Implemented to date

**Fixed Version**: 2.4.2-dev.1

**Fix Content**: Change `is_friend_add()`'s matching value from `"friend_add"` to `"friend_increase"`, and `is_friend_delete()` from `"friend_delete"` to `"friend_decrease"`.

**Fix Date**: 2026/04/13

**Severity**: 🟡 Moderate

**Type**: Event System

---

### [BUG-006] adapter.clear() does not clean up _started_instances causing incorrect state after restart

**Problem**: The `AdapterManager.clear()` method clears `_adapters`, `_adapter_info`, handlers, and `_bots`, but omits cleaning up the `_started_instances` set. If `clear()` is called while the adapter is running, `_started_instances` retains dangling references, causing incorrect state judgment after restart.

**Cause**: When `_started_instances` was introduced in 2.4.0-dev.1, it was not synchronized in `clear()`.

**Affected Version**: 2.4.0-dev.1 - 2.4.2-dev.0

**Fixed Version**: 2.4.2-dev.1

**Fix Content**: Add `self._started_instances.clear()` in the `clear()` method.

**Fix Date**: 2026/04/13

**Severity**: 🟡 Moderate

**Type**: Adapter

---

### [BUG-007] command.wait_reply() uses deprecated asyncio.get_event_loop()

**Problem**: The `CommandHandler.wait_reply()` method uses `asyncio.get_event_loop()` to create futures and get timestamps, which has been deprecated in Python 3.10+. In asynchronous contexts, `asyncio.get_running_loop()` should be used. This is inconsistent with the `get_running_loop()` used in the `wrapper.py` `wait_for()` method.

**Cause**: The old API was used during development, and the newly added `wait_for()` used the correct API but did not retrospectively fix the old code.

**Affected Version**: 2.3.0-dev.0

**Fixed Version**: 2.4.2-dev.1

**Fix Content**: Replace `asyncio.get_event_loop()` in `command.py` with `asyncio.get_running_loop()` in two places.

**Fix Date**: 2026/04/13

**Severity**: 🟢 Minor

**Type**: Event System

---

### [BUG-008] Bot offline event is repeatedly submitted during shutdown

**Problem**: When calling `adapter.shutdown()` to shut down all adapters, `_update_bot_status()` repeatedly submits Bot offline events during the shutdown process, causing the same batch of Bots to be marked offline multiple times and triggering multiple `adapter.bot.offline` lifecycle events.

**Cause**: The Bot status tracking system introduced in 2.4.0-dev.1 did not set a "shutting down" flag during `shutdown()`, so `_update_bot_status()` could not distinguish between normal offline and cascading offline during the shutdown process.

**Affected Version**: 2.4.0-dev.1 - 2.4.2-dev.1

**Fixed Version**: 2.4.2-dev.1

**Fix Content**: Add `_is_being_shutdown` flag in `AdapterManager`, set to True at the start of `shutdown()` and cleared at the end; `_update_bot_status()` skips repeated submissions during the shutdown process after checking this flag.

**Fix Date**: 2026/04/21

**Severity**: 🟡 Moderate

**Type**: Adapter

---

### [BUG-009] LazyModule synchronous access to BaseModule causes incomplete initialization

**Problem**: When users access the properties of a lazily loaded BaseModule in a synchronous context, the module uses `loop.create_task()` for asynchronous initialization but does not wait, resulting in race conditions when the properties are accessed before initialization is complete.

**Cause**: `_ensure_initialized()` uses `loop.create_task(self._initialize())` and returns immediately without ensuring initialization is complete.

**Affected Version**: 2.4.0-dev.0 - 2.4.2-dev.1

**Fixed Version**: 2.4.2-dev.2

**Fix Content**: In synchronous contexts, BaseModule initialization is changed to use `asyncio.run(self._initialize())`, ensuring initialization is complete before returning. The transparent proxy feature is maintained, and users do not need to be aware of the difference between synchronous and asynchronous contexts.

**Fix Date**: 2026/04/21

**Severity**: 🟡 Moderate

**Type**: Loader

---

### [BUG-010] Multi-threaded configuration system write causes data loss

**Problem**: In a multi-threaded environment, when multiple threads call `config.setConfig()` simultaneously, the `_flush_config()` read-modify-write operation is not atomic, potentially causing some writes to be lost.

**Cause**: Although `_flush_config()` uses `RLock`, there is no file lock protection between file reads and writes, and the `_schedule_write` Timer may be triggered multiple times, causing overwrites.

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

### [BUG-011] Windows Ctrl+C does not stop the program

**Problem**: When running `python main.py` directly on Windows, pressing Ctrl+C does not terminate the program. After the program starts normally and outputs the routing server information, Ctrl+C has no response and can only be forcibly terminated via the task manager. However, it can be stopped normally when started via `epsdk run`—but `epsdk run` runs via a subprocess model.

**Cause**: The Hypercorn ASGI server's `serve()` function internally registers its own SIGINT handler with `signal.signal(SIGINT, handler)`, overriding Python's default `KeyboardInterrupt` handling mechanism. When starting Hypercorn as a background task via `asyncio.create_task()`, the internal shutdown process of Hypercorn cannot be triggered normally (because it expects the `worker_serve` mode), causing Ctrl+C signals to be swallowed by Hypercorn but not triggering any cleanup actions.

**Affected Version**: 2.3.6 - 2.4.2

**Fixed Version**: 2.4.3-dev.0

**Fix Content**:
1. Switch ASGI server from Hypercorn to Uvicorn (`pyproject.toml` dependency change)
2. Use `uvicorn.Server._serve()` to start the server directly, **bypassing** the `capture_signals()` signal handling context manager
3. Use `server.should_exit = True` to implement graceful shutdown, canceling the background task if timeout occurs
4. Synchronize removal of the subprocess running model and `runtime/cleanup.py` cleanup module (no longer needed for subprocess cleanup mechanism)

**Fix Date**: 2026/04/28

**Severity**: 🔴 Severe

**Type**: CLI / Runtime

---

### [BUG-012] Hot restart does not activate updated module Python code

**Problem**: After executing `sdk.restart()` for a soft restart, the new code (such as new API routes) of modules/adapters upgraded via `epsdk install` does not take effect and still runs old logic. A complete process restart is required to load the latest code.

**Cause**: `_do_restart()` calls `entry_point.load()` during re-initialization, but this function returns a cached old module object from `sys.modules` instead of reloading from disk.

**Affected Version**: Early versions - 2.4.3-dev.1

**Fixed Version**: 2.4.3-dev.1

**Fix Content**: Clear the cache of loaded modules/adapters from `sys.modules` before `uninit()` and after `init()` to ensure `entry_point.load()` loads the latest code from disk. Add `_collect_top_level_modules()` and `_invalidate_module_cache()` helper methods, inferring top-level module names via `top_level.txt` or entry-point value.

**Fix Date**: 2026/05/03

**Severity**: 🔴 Severe

**Type**: Loader / Runtime

---

### [BUG-013] Module loading strategy sorting logic error

**Problem**: `ModuleLoadStrategy` provides a `priority` field to declare the initialization priority of modules, but the implementation of the loading strategy has an error, causing modules not to be initialized in the expected priority order, but rather in the default order of `entry_points()`. When modules have initialization dependencies, the correct initialization order cannot be ensured by `priority`.

**Cause**: There is an error in the sorting logic of the loading strategy implementation; `initialize_modules()` does not sort the module list by `priority`.

**Affected Version**: 2.3.4 - 2.4.5-dev.2

**Fixed Version**: 2.4.5-dev.3

**Fix Content**: Before `initialize_modules()` iteration, sort the module list by `priority` in descending order. Modules with the same priority maintain their original relative order (stable sorting).

**Fix Date**: 2026/05/15

**Severity**: 🟡 Moderate

**Type**: Loader

---

### [BUG-014] Adapter middleware returning None causes event data loss

**Problem**: When `adapter.emit()` executes the OneBot12 middleware chain, if a middleware returns `None` (for example, forgetting to `return data`), the subsequent middleware and all event handlers receive `processed_data` as `None`, causing event processing to fail completely.

**Cause**: The middleware chain implementation `processed_data = await middleware(processed_data)` does not check if the return value is `None`, directly overwriting the result from the previous step.

**Affected Version**: unknown - 2.4.5-dev.3

**Fixed Version**: 2.4.5-dev.4

**Fix Content**: If middleware returns `None`, ignore the return value, keep the original data and pass it on, and output a warning-level log.

**Fix Date**: 2026/05/15

**Severity**: 🔴 Severe

**Type**: Adapter / Event System

---

### [BUG-015] Configuration file path depends on working directory

**Problem**: The configuration file path in `ConfigManager` defaults to the relative path `"config/config.toml"`, which depends on `os.getcwd()` at runtime. If the working directory changes during runtime (for example, via `os.chdir()`), the configuration file read/write operations will point to the wrong location, leading to configuration loss or reading old data.

**Cause**: In `__init__`, the relative path is directly stored without being resolved to an absolute path at initialization.

**Affected Version**: 2.3.7 - 2.4.5-dev.3

**Fixed Version**: 2.4.5-dev.4

**Fix Content**: In `ConfigManager.__init__()`, if the passed path is a relative path, automatically resolve it to an absolute path using `os.path.abspath()`.

**Fix Date**: 2026/05/15

**Severity**: 🟡 Moderate

**Type**: Configuration System

---

### [BUG-016] BaseStorage confuses storing None value with missing key

**Problem**: `BaseStorage.get_multi()` / `__getattr__()` cannot distinguish between "key does not exist" and "key's value is None", so when a user explicitly stores `None` and then reads it, it is treated as the key not existing.

**Cause**: The value retrieval logic directly uses `value is None` to determine if the key exists, lacking an independent "missing" marker.

**Affected Version**: Early versions - 2.4.6-dev.6

**Fixed Version**: 2.4.6-dev.6

**Fix Content**: Introduce `_SENTINEL` sentinel value to distinguish "key does not exist" from "value is None", so they are no longer confused.

**Fix Date**: 2026/06/07

**Severity**: 🟡 Moderate

**Type**: Storage

---

### [BUG-017] WebSocket route auto_accept flag lost after service restart

**Problem**: After a service restart (such as `sdk.restart()`), the `auto_accept` configuration for all WebSocket routes reverts to `False`, and the originally expected automatic accept connections become suspended, causing clients to wait a long time without receiving a response, manifesting as WS connections hanging.

**Cause**: `_restore_routes_from_records()` hardcodes `auto_accept` to `False` when restoring routes from persistent records, not reading the value from the original record; also, when the route storage tuple expanded from a binary tuple to a ternary tuple, the restoration logic was not synchronized.

**Affected Version**: 2.3.8-dev.0 - 2.4.6-dev.6

**Fixed Version**: 2.4.6-dev.6

**Fix Content**: The route storage tuple expands to `(handler, auth_handler, auto_accept)`, and `_restore_routes_from_records()` reads the real `auto_accept` value from the record instead of hardcoding `False`.

**Fix Date**: 2026/06/07

**Severity**: 🔴 Severe

**Type**: Router

---

### [BUG-018] HTTP/WS client concurrent calls cause crashes and connection leaks

**Problem**: The HTTP and WebSocket clients in `Core/client.py` have multiple stability defects in concurrent scenarios, leading to connection leaks or process crashes:
- Multiple coroutines concurrently calling `ClientWebSocket.receive()` cause aiohttp to throw `Concurrent call to receive() is not allowed`
- `_get_http_session()` / `_get_ws_session()` concurrent calls may create multiple sessions and `_drain_sessions()` does not close old connections, causing connection leaks
- `request()` exception handling order is incorrect: `except ClientConnectionError` (ErisPulse exception) is never triggered, aiohttp connection errors are caught by the general `except Exception`, leading to the "retry connection + session rebuild" logic (dead code) never executed
- `send_json()` ignores the `mode="binary"` parameter; `_get_ws_session()` does not pass default request headers

**Cause**: The client's initial implementation (2.4.6-dev.5) lacked concurrency protection and improper handling of aiohttp exception hierarchy and ErisPulse custom exception inheritance.

**Affected Version**: 2.4.6-dev.5 - 2.4.8

**Fixed Version**: 2.4.8

**Fix Content**:
1. Add `_recv_lock` to serialize all `receive()` / `receive_text()` / `receive_bytes()` calls
2. Add `_session_lock` to protect session creation; `_drain_sessions()` is changed to an async method and truly closes old sessions
3. Refactor `request()` exception handling order: `asyncio.TimeoutError` → `aiohttp.ClientConnectionError` (triggers session rebuild) → `aiohttp.ClientError` → `ClientError` (transparent pass) → `Exception`
4. Fix `send_json()` mode handling, `_get_ws_session()` default request header passing, `close()` concurrency race, `HttpResponse.__aexit__` duplicate `release()`

**Fix Date**: 2026/06/12

**Severity**: 🔴 Severe

**Type**: Client

---

### [BUG-019] Adapter hot reload causes route conflicts leading to reload failure

**Problem**: When a third-party module (such as Dashboard) triggers adapter hot reload, or when adapter startup fails and retries, due to the uncleaned old routes (such as `onebot11_default`) from the previous registration, the error `WebSocket path ... already registered` is thrown, causing the reload to fail. A complete process restart is required to recover.

**Cause**: `AdapterManager.shutdown()` only clears routes via `unregister_all_by_namespace(platform)`, but adapters (such as OneBot11) register WebSocket routes with the namespace `onebot11_{account_name}`, resulting in a granularity mismatch and making cleanup an empty operation; startup failure retry paths also do not clean up previous residual routes.

**Affected Version**: Early versions - 2.4.9

**Fixed Version**: 2.4.9

**Fix Content**:
1. Route registration automatically tracks `owner → namespace` relationships via `current_owner` ContextVar
2. Add `unregister_all_by_owner(owner)`, cleaning up by owner during stop/restart, covering fine-grained namespaces
3. Add `_stop_adapter(platform)` primitive ("stop equals cleanup"), binding stopping the adapter and reclaiming its registered resources in a single call, `restart()` and startup failure retry both go through this entry
4. Add framework-level `adapter.restart(platform)` API, third-party modules should call this method instead of directly operating adapter instances

**Fix Date**: 2026/06/12

**Severity**: 🔴 Severe

**Type**: Adapter / Router

---

### [BUG-020] Subprocess mode `ep run <script>` cannot find subpackages in the script's directory

**Problem**: When running a script with `ep r .\main.py` in non-hot-reload mode, if the script has relative imports (such as `from qg import ...`), it reports `No module named 'qg'` error. However, the `--reload` mode works normally.

**Cause**: The non-hot-reload mode directly calls `runpy.run_path()` to execute the script, which does not automatically add the script's directory to `sys.path`. In contrast, the `--reload` mode runs via `subprocess.Popen` subprocess, which automatically inherits the current working directory, making `sys.path[0]` the script's directory, so it works normally.

**Affected Version**: 2.5.0 - 2.5.2-dev.0

**Fixed Version**: 2.5.2-dev.0

**Fix Content**: Before calling `runpy.run_path()`, manually insert the script's directory into `sys.path[0]`.

**Fix Date**: 2026/06/27

**Severity**: 🟡 Moderate

**Type**: CLI

---

### [BUG-021] SQL query builder rejects legitimate wildcards and list expressions

**Problem**: `SQLiteQueryBuilder`'s `_build_select_sql()` validates all SELECT columns using `_validate_identifier()`, which uses a strict whitelist regex `^[a-zA-Z_][a-zA-Z0-9_]*$`, causing legitimate SQL syntax to be incorrectly judged as unsafe column names:

- `SELECT *` — `*` is a standard SQL wildcard
- `SELECT COUNT(*)` — aggregate function
- `SELECT users.name` — qualified column name
- `SELECT col AS alias` — column alias

Among these, `Select("*")` is used by Cron and other modules, causing module `on_load` execution failure and preventing the module from loading.

**Cause**: In version 2.4.6, SQL injection protection was enhanced, introducing the `_validate_identifier()` whitelist validation. This validation is applied to all column names, but not distinguished between read side (SELECT/ORDER BY) and write side (INSERT/UPDATE). SELECT columns allow complex SQL expressions and should not be restricted by simple identifier whitelist validation.

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

### [BUG-022] _resolve_account() account resolution regression (_accounts_data not filled)

**Problem**: After the 2.5.2 configuration system refactor, multi-account adapters declaring `AccountConfigClass` fail to resolve accounts when calling methods like `wait_reply`, `reply`, etc., which require sending messages. Even if the adapter correctly configures multi-account information, account resolution still fails.

**Cause**: In 2.5.2-dev.5, `_load_accounts()` (responsible for reading configuration + validation + filling `_accounts_data`) was refactored into `_ensure_accounts_exist()` (only generates configuration template), but `_resolve_account()` still checks `self._accounts_data is None`. Since `_ensure_accounts_exist()` no longer fills `_accounts_data`, this property remains `None`, causing `_resolve_account()` to prematurely return `(None, None)`, and account resolution fails completely.

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
    self._accounts_data = self.accounts  # Restore filling, data source is real-time read accounts attribute
```
The logic of `_resolve_account()` remains unchanged, fully backward compatible:
- Adapters that do not declare `AccountConfigClass`: `_accounts_data` remains `None` → return `(None, None)`
- Adapters that declare `AccountConfigClass`: `_accounts_data` is filled → normal resolution
- Adapters that overwrite `_load_accounts` or manually set `_accounts_data`: overwrite in `super().__init__()` after, highest priority

**Fix Date**: 2026/07/07

**Severity**: 🔴 Severe

**Type**: Adapter / Configuration System

---

### [BUG-023] After modifying account configuration, adapter cache is not refreshed causing account resolution failure

**Problem**: After users modify the account configuration of multi-account adapters (such as filling in tokens) through the Dashboard, the adapter still uses the old cache, and calling message-sending-related methods reports `No available account (account_id=default)`. The process must be restarted for the new configuration to take effect.

**Cause**: `_accounts_data` is only read from the configuration storage once at `BaseAdapter.__init__`, and is never refreshed afterward. `AdapterManager._run_adapter()` and `restart()` do not re-read the account configuration before calling `adapter.start()`, causing the cache to be out of sync with the actual configuration.

**Affected Version**: 2.4.6 - 2.5.4

**Fixed Version**: 2.5.4

**Fix Content**: In `AdapterManager._run_adapter()` and `restart()`, before calling `adapter.start()`, refresh `adapter._accounts_data = adapter.accounts` to ensure that the latest configuration is used each time the adapter starts.

**Fix Date**: 2026/07/09

**Severity**: 🔴 Severe

**Type**: Adapter / Configuration System

---

### [BUG-024] storage.set() writing large numeric ID keys triggers OOM Kill

**Problem**: When calling `storage.set()` to write a nested key path containing a large numeric field (such as QQ group ID `871684833`), the process is killed by the container OOM (exit code -9), causing the service to crash and unable to recover.

**Cause**: In the recursive implementation of `_set_nested_value`, the pure numeric field in the nested key path is mistakenly identified by `isdigit()` as a list index, triggering `current.extend([None] * (index - len(current) + 1))`, attempting to allocate hundreds of millions of elements, instantly exhausting memory.

**Root Cause Chain**:
```
The key path contains a pure numeric field (such as group ID 871684833)
  → isdigit() mistakenly identifies it as an array index
    → extend([None] * (871684833 - len(current) + 1))
      → attempts to allocate hundreds of millions of elements
        → memory exhaustion → container OOM Kill (exit code -9)
```

**Affected Version**: 2.5.1 - 2.5.5

**Fixed Version**: 2.5.5

**Fix Content**:
1. Always use dictionaries when pre-creating intermediate layers, no longer guessing the container type based on whether the next segment is a number
2. Only when the container itself is a list and the index is less than `STORAGE_MAX_LIST_INDEX` (10000) do we handle it by index, skipping large indexes safely
3. Change the recursive implementation to an iterative one, eliminating potential infinite recursion risks in the original code
4. Add `STORAGE_MAX_LIST_INDEX` constant to `Core/constants.py`, centrally managing the index safety limit

**Fix Date**: 2026/07/10

**Reproduction Steps**:
```python
# Trigger by writing a nested key path containing a large number field (such as QQ group ID)
await sdk.storage.aset("groups.871684833.name", "某群")
# → Process memory surges instantly, killed by OOM
```

**Regression Test**: `tests/unit/test_unit_storage.py` adds 4 regression test cases
- `test_nested_key_numeric_segment_as_dict_key` — precisely reproduces the OOM scenario
- `test_nested_key_numeric_segment_multiple` — multiple consecutive numeric segments as dictionary keys
- `test_nested_key_existing_list_index_set_within_limit` — existing list index write within limit
- `test_nested_key_list_index_safety_limit` — safety limit verification for large indexes

**Severity**: 🔴 Severe

**Type**: Storage

---

### [BUG-025] on_config_update callback not called by core router

**Problem**: `on_config_update(old, new)` callback is defined in the base class (`BaseModule` / `BaseAdapter`), but the core framework does not subscribe these events to the configuration change event. As a result, when the configuration is modified via the configuration management panel, the callback is triggered, but when manually editing `config.toml` or calling `setConfig()` programmatically, the `on_config_update` is not triggered.

**Cause**: `ConfigManager` emits `config.set` / `config.updated` lifecycle events when the configuration changes, but lacks the subscription logic to forward these events to each component's `on_config_update` method.

**Root Cause Chain**:
```
Core does not subscribe to config.set / config.updated
  → Configuration change events are not forwarded
    → on_config_update is not called
      → Manual file editing / code setConfig does not trigger hot update callback
```

**Affected Version**: All versions

**Fixed Version**: 2.6.2

**Fix Content**: `ModuleManager` / `AdapterManager` register subscriptions for `config.set` (covering code `setConfig()` path) and `config.updated` (covering manual file editing path), match by configuration key prefix and call the corresponding component's `on_config_update`, passing type-safe configuration objects. Also fix `_flush_config()` not synchronizing `_config_mtime` after writing the file, avoiding the framework's own write being misjudged as an external modification by the file monitoring task and repeatedly triggering `config.updated`.

**Compatibility Note**: Hot configuration updates are now centrally maintained by the framework core. Previously, the configuration management panel handled the trigger, which has been removed; after upgrading the framework, the configuration management panel must also be upgraded, otherwise duplicate triggers will occur (core + panel each trigger once). The `on_config_update` method signature and semantics remain unchanged, subclasses do not need modification.

**Fix Date**: 2026/07/23

**Severity**: 🟡 Moderate

**Type**: Configuration System

---

### [BUG-026] notice/request event reply target inference error

**Problem**: In group notification events (such as member joining a group `group_member_increase`), calling `event.reply()` sends the message to the user who triggered the event's private chat, not to the group where the event occurred. Similarly for friend notification events, the reply target may be incorrect.

**Cause**: `infer_receive_type()` directly returns the event's `detail_type` as the session type. For message events this is correct (the `detail_type` values `private`/`group` are the session types), but for notice/request events the `detail_type` is a semantic subtype (such as `group_member_increase`, `friend_increase`), not the session type. The subsequent `convert_to_send_type()` and `get_id_field()` lookups in the mapping table do not find the value, defaulting to `"user"` / `"user_id"`, resulting in the wrong reply target.

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

**Fix Content**: `infer_receive_type()` adds a check—only returns `detail_type` directly if it is a known session type (standard or custom type); otherwise, infers the correct session type based on the ID field (`group_id` / `channel_id` / `user_id`, etc.).

**Regression Test**: `tests/unit/test_unit_session_type.py` → `TestNoticeRequestTypeInference` (10 test cases)

**Fix Date**: 2026/07/29

**Severity**: 🟢 Minor

**Type**: Event System

---

### [BUG-027] Router rate-limiting cleanup task uses fixed window causing long-window rate-limiting rules to fail

**Problem**: When routing rate-limiting is configured as a long-window rule (such as `100/hour`, `{"requests": 100, "window": 3600}`), the rate-limiting is ineffective—practically behaving like `100/minute` (up to about 6000 requests per hour), failing to provide the intended hourly protection.

**Cause**: `_apply_rate_limit` parses the actual `window` per route (up to 3600 seconds), and per-request checks do use this window; however, the background cleanup task `_cleanup_expired_rate_limits` uses a fixed constant `DEFAULT_RATE_LIMIT_WINDOW_SECS` (60 seconds) as the cleanup threshold for all routes. Thus, time stamps earlier than 60 seconds in the `100/hour` route are cleared by the cleanup task, so the hour window never accumulates close to 100 records, severely weakening the rate-limiting.

**Root Cause Chain**:
```
_apply_rate_limit parses window=3600 (100/hour)
  → per-request checks use 3600s to retain timestamps (correct)
  → but _cleanup_expired_rate_limits uses fixed max_window=60s to clean up
    → time stamps earlier than 60 seconds are cleared
      → the hour window only retains records from the last 1 minute
        → 100/hour effectively degrades to ~100/minute (relaxed by about 60 times)
```

**Affected Version**: 2.6.0-dev.0 - 2.7.0-dev.4

**Fixed Version**: 2.7.0-dev.5

**Fix Content**: Add `_rate_limit_windows: dict[str, int]` to record the actual window per route; `_apply_rate_limit` writes the window when first creating an entry; `_cleanup_expired_rate_limits` changes to clean up by each key's own window (fallback to default value if missing); cleanup deletion and `stop()` synchronize maintenance of both dictionaries.

**Fix Date**: 2026/07/31

**Regression Test**: `tests/unit/test_unit_router.py` → `TestRateLimit::test_cleanup_respects_per_route_window`

**Severity**: 🔴 Severe

**Type**: Router

---

### [BUG-029] Configuration listener task broadcasts incomplete TOML and silently swallows exceptions

**Problem**: When users manually edit `config.toml` and save halfway (producing a temporary syntax error), the configuration listening background thread detects the mtime change, reloads the configuration, but fails to load and still broadcasts an empty configuration `{}` via the `config.updated` event, causing adapters/modules' `on_config_update` to receive an empty configuration, mistakenly assuming all configuration items were cleared and reverting to default values. Additionally, the listener loop uses `except Exception: pass` to silently swallow all exceptions, making it impossible to diagnose watcher faults.

**Cause**: Two defects叠加:
1. `_load_config` overwrites `self._cache` to `{}` when TOML syntax error/permission error occurs, but the background listener thread `_watch_loop` and cache timeout path `_check_cache_validity` both call `_emit_config_updated()` after `_load_config()` without condition, broadcasting the "empty cache produced by load failure" as a real change.
2. `_watch_loop`'s `except Exception: pass` does not log any errors.

**Root Cause Chain**:
```
User saves halfway → TOML syntax error
  → _load_config() overwrites _cache = {}
    → _watch_loop unconditionally _emit_config_updated(new_config={})
      → Adapters/modules on_config_update receive empty config
        → Mistake configuration as cleared, revert to default values
```

**Affected Version**: 2.6.2-dev.1 - 2.7.0-dev.4

**Fixed Version**: 2.7.0-dev.5

**Fix Content**:
1. `_load_config` changed to return `bool`; when TOML syntax error/permission error or other errors occur, keep the last valid cache (do not overwrite to `{}`), only record diagnostic logs and return `False`
2. `_watch_loop` and `_check_cache_validity` only emit `config.updated` when `_load_config()` returns `True`
3. `_watch_loop`'s `except Exception` changed to log at warning level (add i18n key `core.config.watcher_error`, synchronized for five languages)

**Fix Date**: 2026/07/31

**Regression Test**: `tests/unit/test_unit_config.py` → `test_malformed_toml_preserves_last_valid_cache`, `test_permission_denied_logs_clear_message` (updated to verify keeping cache and returning False)

**Severity**: 🟡 Moderate

**Type**: Configuration System

---

### [BUG-030] Configuration watcher race condition causes setConfig delayed write silently drops data

**Problem**: Multiple users report that after using `config.setConfig(key, value)` (default `immediate=False`), their module configuration is not written to `config.toml`, while other modules' configurations are normal. Setting `immediate=True` (force flush) can bypass this. Manifestation: Configuration written at runtime is lost after the next restart, while configuration generated at startup via template is preserved.

**Cause**: Two overlapping defects:
1. **Logical defect**: `_watch_loop` unconditionally `_dirty_keys.clear()` when `_check_file_change()` returns `True` without checking mtime differences. However, `_check_file_change()` only uses `!=` to compare mtime, and the framework's own `_flush_config` writing also changes mtime—although `_flush_config` updates `_config_mtime` after writing, the watcher thread may still observe mtime differences between file write and mtime assignment (and at the coarse-grained file system level), mistakenly detecting it as "external modification" and clearing all dirty keys.
2. **Thread defect**: `_watch_loop` operates `_write_timer`/`_dirty_keys` without holding `_lock`, creating data races with `setConfig` (holding lock to write `_dirty_keys`), `_schedule_write` (holding lock to write `_write_timer`).

**Root Cause Chain**:
```
Module A setConfig(immediate=True) → flush writes to disk, mtime changes
  → User module setConfig(immediate=False) → enters _dirty_keys, flushes to disk after 5 seconds
    → Watcher loop, _check_file_change observes mtime difference from its own previous write
      → _dirty_keys.clear() → Dirty keys from user module are silently dropped
        → Configuration missing after restart
```

**Affected Version**: 2.6.0 - 2.7.0

**Fixed Version**: 2.7.1

**Fix Content**:
1. Add `_last_self_write_mtime` field; after `_flush_config` writes to disk, update this value; in `_check_file_change`, first compare this value when mtime changes, if matched, return `False` as self-write.
2. Entire `_watch_loop` section holds `_lock`; retain `_dirty_keys` when actual external modification occurs (merge semantics), next flush merges with external content (dirty keys take precedence), no longer `clear()`
3. `getConfig`/`_check_cache_validity` paths are unaffected (their reload does not clear dirty keys)

**Fix Date**: 2026/08/06

**Regression Test**: `tests/unit/test_unit_config.py` → `test_self_write_not_detected_as_external`, `test_external_change_preserves_dirty_keys`, `test_flush_merges_dirty_with_external`

**Severity**: 🔴 Severe

**Type**: Configuration System

---

### [BUG-032] Configuration delay write period "write after read" reads old value

**Problem**: After `config.setConfig()` (default `immediate=False` delay about 5 seconds to flush), writing a dot-separated key and immediately reading its parent/ancestor node (such as `set_erispulse_section("scope.actions.MyModule", {...})` then calling `get_erispulse_config()`) returns the old value, the written sub-key "disappears" until the flush, affecting "write-read-write" scenarios like scope configuration hot updates (exposed by test plugin `/t_section` in 2.8.0).

**Cause**: `setConfig` stores dot-separated keys in the dirty key queue `_dirty_keys` in a flat form, only `getConfig`'s exact key query hits the dirty key queue; tree path queries (such as `getConfig("ErisPulse.scope")`) only go through the cache tree, not overlay dirty values—during the delay write period (`_flush_config` merges dirty keys into the cache and clears the queue), a read-you-write disconnect occurs.

**Affected Version**: 2.6.0 - 2.8.0-dev.1

**Fixed Version**: 2.8.0-dev.1

**Fix Content**: `getConfig` introduces dirty overlay semantics—① exact hit in dirty key returns directly (original behavior unchanged); ② dirty key is an ancestor of the query key → take the longest dirty ancestor and parse the remaining path in its value subtree; ③ dirty key is a descendant of the query key → build an overlay subtree (`_dirty_overlay`) and deep merge with the cache subtree (`_deep_merge`, override priority, does not modify the original cache object). When there are no dirty keys, go through the original fast path, zero additional overhead.

**Fix Date**: 2026/09/04

**Regression Test**: `tests/unit/test_unit_config.py` → `test_get_config_overlays_dirty_descendant`, `test_get_config_overlay_merges_with_cache_siblings`, `test_get_config_overlay_new_branch`, `test_get_config_dirty_ancestor_query`, `test_get_config_dirty_exact_key_still_wins`

**Severity**: 🟡 Moderate

**Type**: Configuration System

---

### [BUG-033] wait_reply hangs replies are starved by high-priority processors

**Problem**: When a module calls `wait_reply()` to wait for a user reply, if that reply message is claimed by a higher-priority event handler (`mark_processed()`), the command dispatcher sees the `_processed` flag at the entry and returns directly, the reply matching `_check_pending_reply` at the end of `_handle_message` is never executed—waiting parties receive no reply and can only wait until timeout returns `None`. Typical trigger scenario: using high-priority message processors (recording/auditing/blocking classes) in a robot, all dialog interactions randomly fail.

**Cause**: The reply matching `_check_pending_reply` is placed at the end of `_handle_message` (only executed if command matching fails), while the `_processed` check is before it—the order of claim checking and reply matching is reversed. Interactive waiting is a framework-level session continuation mechanism, not a competitive processor, and should not be affected by other processors' claim.

**Affected Version**: 2.2.0-dev.0 - 2.8.0-dev.1

**Fixed Version**: 2.8.0-dev.2

**Fix Content**: Move reply matching to the entry of `_handle_message` (before the `_processed` check, only for message events): first attempt to complete the pending dialog, if matched, the event is marked as processed, the following checks naturally short-circuit; if not matched, continue the original command matching process. The judgment chain delegates to a new interaction session manager (`Core/Event/interaction.py`), incidentally gaining the ability to cancel by affiliation and permission review.

**Fix Date**: 2026/09/08

**Regression Test**: `tests/unit/test_unit_interaction.py` (TestRegisterResolve match/not match/claim mark), `tests/unit/test_unit_event.py` (wait_reply full chain)

**Severity**: 🟡 Moderate

**Type**: Event System / Command System

---

### [BUG-034] Scope persist=False runtime binding is silently overwritten by any subsequent configuration write

**Problem**: `scope.set_module(..., persist=False)` and other runtime writes only modify memory `self._data`; but scope subscribes to `config.set` / `config.updated` events, and any code writing configuration (such as a module loading and writing its default configuration) triggers scope to rebuild the configuration tree from the configuration file, discarding all previous runtime bindings (reverting to default allow), with no log warning. Scenarios depending on runtime bindings (Dashboard "runtime-only" switches, module runtime dynamic disable) behavior reverts after unrelated module configuration writes.

**Cause**: Root cause chain: `scope.set/delete(persist=False)` only writes to memory (`Core/scope.py`); any `setConfig` triggers `config.set` event; `_on_config_updated` unconditionally `_load_config()` → `_apply_tree()` replaces the persistent layer with `self._data = {...}` → runtime bindings not in the configuration file are discarded.

**Affected Version**: 2.8.0-dev.1 - 2.8.0-dev.2
**Fixed Version**: 2.8.0-dev.2
**Fix Content**: Introduce a runtime override layer `_runtime_overrides` (including delete sentinel): `persist=False` write/delete records in the override layer, `_apply_tree()` rebuilds the persistent layer and replays in write order, runtime rules remain effective after any configuration write; `persist=True` write/delete clears corresponding override records (user persistence semantics take precedence); `config.set` filters by event key, `config.updated` compares new and old scope sections, only rebuilds if scope actually changes (attaching to avoid irrelevant write flushing judgment LRU cache); add `unregister_by_owner()` for module unload to clean up with the caller. `Core.Event.overrides` with persist=False runtime overwrite has a similar problem, synchronized with the override layer architecture.
**Fix Date**: 2026/09/09

**Reproduction Steps**: ① `scope.set_module("testplat", blocked=["TestB"], persist=False)` → decision False; ② any module executes `config.setConfig("HelpModule", {...})` → triggers scope rebuild; ③ `scope.is_allowed("testplat", None, "TestB")` returns True (expected still False).
**关联**: Issue #432
**Regression Test**: `tests/unit/test_unit_scope.py::TestRuntimeOverrideSurvival` (irrelevant write survives/rebuild replay/delete sentinel/persistent clear/precise invalidation/owner cleanup)

**Severity**: 🟡 Moderate
**Type**: Configuration System / Runtime

---

### [BUG-035] Configuration panel select options and dict fields render as [object Object]

**Problem**: In the WebUI configuration panel, select field options dropdown displays `[object Object]` (such as dynamically generated color style options); dict fields (such as `stalker_mode`, `knowledge_base`, etc.) without declared control types display `[object Object]` in text boxes, making it impossible to view and edit normally.

**Cause**: Two independent defects: ① The framework i18n resolver `_resolve_i18n_text` only restores dictionaries with the `i18n` key, but option labels are dictionaries with only `default` (no `i18n` key for dynamic text) and are passed through as-is, resulting in `[object Object]` after the frontend `esc(label)` string coercion; ② The Dashboard rendering branch only handles JSON textarea for array types, dict values fall into the plain text input branch and are converted by `String()`. Additionally, if a module declares `_schema_meta` as a regular dataclass field (missing `ClassVar` annotation), it becomes a configuration field in the schema, exacerbating confusion.

**Affected Version**: 2.7.0 - 2.8.0-dev.2
**Fixed Version**: 2.8.0-dev.2
**Fix Content**: ① `_resolve_i18n_text` supports dictionaries with only `default` as text; ② Framework schema/templates/default values/filling/validation all exclude underscore-prefixed fields (harmless if misdeclared); ③ Dashboard select option label objects fallback to parsing (prioritizing `default`), dict/table fields render as JSON textarea (save path as `tp=object` JSON.parse back-write, complete round trip).
**Fix Date**: 2026/09/09

**Regression Test**: `tests/unit/test_unit_config.py::TestResolveI18nDefaultOnlyDict`, `TestSchemaUnderscoreFieldExclusion`

**Severity**: 🟡 Moderate
**Type**: Configuration System

---

### [BUG-036] Multi-instance shared configuration directory causes occasional configuration write failures (ENOENT)

**Problem**: In Docker deployment scenarios (multiple containers mounting the same host configuration directory), log errors occur intermittently: "Failed to write configuration file ... [Errno 2] No such file or directory: '...config.toml.tmp' -> '...config.toml'". This configuration write is discarded (the old configuration is fully preserved, no configuration loss is observed), functionality is unaffected, but the repeated error alarms interfere with troubleshooting, and the configuration items to be written must wait for the next write to be written to disk.

**Cause**: The root cause chain: `_flush_config` / `setConfigTemplate` uses a fixed-name temporary file `config.toml.tmp` to carry new content, `write()` does not `fsync` before directly `rename()` it. Two ErisPulse instances sharing the same configuration directory, B instance `open("w")` may truncate A instance's ongoing temporary file → A `rename()` when the target has been taken by B or the content is truncated, reports ENOENT (i.e., the two consecutive error messages in the user log). In reported cases, only the write failure warning is observed (the old configuration is preserved); if the timing overlap is more extreme, `rename` may output an empty or half-written `config.toml` (a potential risk, not yet triggered in real environments). In single-instance scenarios, ext4's delayed allocation also has a "rename metadata before data block is written" crash window (SIGKILL / power failure). `_file_lock` is a process-level `threading.RLock`, which does not constrain cross-process/cross-container writes.

**Affected Version**: 2.2.0-dev.0 - 2.8.0

**Fixed Version**: 2.8.1

**Fix Content**: Converge all configuration writes to `_atomic_write_text()`: generate a process-unique temporary file with `mkstemp` in the same directory (eliminating fixed-name competition, multi-instance degradation to last-writer-wins, no more ENOENT); after writing, `flush + fsync` to force data to disk (eliminating the "rename is effective, data is not written" window); use `os.replace` to atomically replace the target (atomic on both POSIX/Windows, at any moment the disk has either the complete old content or the complete new content); additionally fsync the configuration directory on POSIX. All three write points (`_flush_config`, `setConfigTemplate`, root directory configuration migration) switch; the exception path cleanup logic is refactored with the unique temporary file name. Add **multi-instance detection**: acquire an advisory lock (`flock` on POSIX / `msvcrt.locking` on Windows) on the configuration directory lock file `.erispulse_config.lock` at startup, output an i18n warning if occupied (does not block startup), the lock is automatically released by the OS when the process exits, no ghost locks.

**Fix Date**: 2026/09/13

**Reproduction Steps**: ① Two containers mount the same host `config/` directory and run ErisPulse simultaneously; ② Trigger a configuration write (such as module registration default configuration) in any instance; ③ Observe the log for ENOENT write failure warnings, this write is discarded (the old configuration is preserved).

**关联**: User report (1Panel container ×2)

**Regression Test**: `tests/unit/test_unit_config_atomic_write.py` (content fully written / no temporary file residue / write failure preserves original file / concurrent write of two instances always results in a legal file / lock file creation / multi-instance warning / atomic write of migration)

**Severity**: 🟢 Minor

**Type**: Configuration System

---

### [BUG-037] Space-separated command names registered but never triggered

**Problem**: After registering a subcommand with a space-separated multi-token command name (such as `@command("admin add")`), the command can be registered normally and appears in the help list, but when the user sends `/admin add`, the robot never responds—the input is matched as `admin` + parameter `["add"]` by the first token command; if the parent token is also unregistered, there is no response. Only when using dot-separated naming (e.g., `admin.reload`, treated as a single token) can this be avoided.

**Cause**: The root cause chain: `CommandHandler.__call__` stores any command name (including space-separated forms) as-is into the flattened `self.commands` dictionary → during the dispatch phase `_try_execute_command`, only the first message token is matched (`cmd_name = parts[0]`) → multi-token command names as dictionary keys are never found. The registration and matching phases have inconsistent assumptions about the command name space, and there is no registration-time warning (silent failure).

**Affected Version**: From the introduction of the command system to 2.8.0

**Fixed Version**: 2.8.1

**Fix Content**: The matching layer changes to **longest prefix matching**: from the longest candidate (`" ".join(parts[:n])`, with `n` capped by the maximum number of token segments for registered command names/aliases, cached in `_max_name_tokens`) downgraded step by step to try, if matched, execute with the remaining tokens as parameters, downstream scope/ACL/overriding/master/permission chain naturally applies to the full command name. Accompanying semantics: when parent and child coexist, unregistered child commands fall back to the parent command (unchanged historical behavior); if a child command does not declare `permission`, it inherits the most recent ancestor command's declared permission (protecting the parent command protects all its child commands); only registering single-token commands hits the first round, dispatch overhead is consistent with the original.

**Fix Date**: 2026/09/13

**Reproduction Steps**: ① Module registers `@command("admin add")`; ② Sends `/admin add x`; ③ Before the fix, there is no response (or is caught by the unregistered `/admin` as a parameter), after the fix `admin add` is triggered and `get_command_args()` is `["x"]`.

**Regression Test**: `tests/unit/test_unit_command_subcommand.py` (longest prefix match/only child command triggered/three-level nesting/case sensitivity in two modes/single and multi-token alias/event payload full name/lifecycle hook full name/permission inheritance six cases/ACL glob full name/master/unregister fallback and cache recalculation)

**Severity**: 🟡 Moderate

**Type**: Event System

---

### [BUG-038] ORM self-managed transactions are skipped on PostgreSQL, data insertion silently lost

**Problem**: On PostgreSQL, ORM `create` / `save` (self-managed transaction insertion with auto-incremented primary key backfill) executes successfully and returns the auto-incremented ID normally, but the data is not actually persisted—when the connection is released, the transaction is rolled back by the connection pool, and subsequent queries find no such row; the connection pool logs show `Resetting connection with an active transaction`. KV transactions (`storage.atransaction()`) are unaffected.

**Cause**: The root cause chain: `Model._insert_and_backfill` self-managed transaction calls `_commit_txn(conn)` / `_rollback_txn(conn)` without returning the `_begin_txn(conn)` handle → PostgreSQL backend's commit/rollback is handle-based (`handle.commit()`, `handle=None` skips directly) → commit silently fails → connection release triggers pool rollback. SQLite / MySQL's commit is statement-based (ignores handle and directly executes COMMIT), so it has never been exposed.

**Affected Version**: 2.9.0-dev.0 (ORM self-managed transaction path introduced) - 2.9.0-dev.1

**Fixed Version**: 2.9.0-dev.1

**Fix Content**: `_insert_and_backfill` receives the `_begin_txn` handle and returns it to `_commit_txn` / `_rollback_txn` (handle remains None if `_begin_txn` throws an exception safely)

**Fix Date**: 2026/09/25

**Reproduction Steps**: PostgreSQL `await Model.create(name="x")` → returns the auto-incremented ID normally → another connection `SELECT COUNT(*)` is 0, and pool log shows active transaction reset warning

**Regression Test**: `tests/devs/orm_realmachine_verify.py` (real machine 14 items: CRUD / auto-migration / relationship mapping / environment transaction, MySQL and PostgreSQL both run)

**Severity**: 🔴 Severe

**Type**: Storage

---

### [BUG-039] ORM boolean field DDL default value `1/0` causes PostgreSQL table creation failure

**Problem**: Model field `Field(default=True)` (boolean declarative default value) causes automatic table creation to fail on PostgreSQL with the error `column "active" is of type boolean but default expression is of type integer`, table creation fails; SQLite / MySQL are unaffected.

**Cause**: `Field._sql_literal` renders boolean default values as numeric literals `1` / `0`; PostgreSQL's BOOLEAN column rejects integer default expressions (requires `DEFAULT TRUE` / `DEFAULT FALSE`).

**Affected Version**: 2.9.0-dev.0 (boolean default value DDL rendering introduced) - 2.9.0-dev.1

**Fixed Version**: 2.9.0-dev.1

**Fix Content**: `_sql_literal` for boolean literals changes to output `TRUE` / `FALSE` (three dialects universally accepted: SQLite ≥3.23, MySQL, PostgreSQL all accept boolean keywords; storage value semantics remain unchanged)

**Fix Date**: 2026/09/25

**Regression Test**: `tests/devs/orm_realmachine_verify.py` (table creation and value round-trip with boolean default value models, MySQL / PostgreSQL both run) + `tests/unit/test_unit_orm_hardening.py`

**Severity**: 🔴 Severe

**Type**: Storage

---

### [BUG-040] `aGetTableColumns` executes with type error, PostgreSQL auto-migration silently fails

**Problem**: ORM auto-migration on PostgreSQL fails to compare existing columns, `aGetTableColumns` reports `cannot unpack non-iterable int object` and returns an empty list → migration comparison always reports "no new columns", new field `ADD COLUMN` silently not executed (does not crash, has fallback, so only fails without error).

**Cause**: `aGetTableColumns` calls `_execute_query` with execution type `"all"`, but the dialect execution funnel only has `"select" / "one" / "count" / "dml" / "dml_multi"` branches → `"all"` falls into the `dml` branch, and asyncpg's `execute` returns a status string (such as `SELECT 3`) for SELECT is parsed as an integer, then unpacked as `(rows, cols)` fails.

**Affected Version**: 2.9.0-dev.0 (auto-migration introduced; SQLite unaffected, MySQL / PostgreSQL affected) - 2.9.0-dev.1

**Fixed Version**: 2.9.0-dev.1

**Fix Content**: Change execution type to `"select"` (existing dialect funnel branch; sqlite / mysql behavior unchanged)

**Fix Date**: 2026/09/25

**Regression Test**: `tests/devs/orm_realmachine_verify.py` (auto-migration items, MySQL / PostgreSQL real machine)

**Severity**: 🟡 Moderate

**Type**: Storage