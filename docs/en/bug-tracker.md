# Bug Tracker

This document records known bugs in the ErisPulse SDK and their fixes, arranged in chronological order by the version in which they were fixed.

> **To the Reader**
> No software is born perfect; even the most careful developers leave behind small errors. This tracker only includes bugs that have a tangible impact on operation—those that are too minor to even be classified as "minor" are not included here. Although the list may seem to have many "severe" items, the purpose of publicly documenting these bugs is to make troubleshooting and tracing smoother, not to create anxiety: problems that are visible, documented, and fixed are proof that the project is continuously improving. Don't be alarmed by this list; it is a troubleshooting tool, not a source of fear.

> **How to Read & Maintenance Conventions**
> - Each bug entry includes structured fields such as problem description, root cause analysis, affected version range, and fix plan. It is recommended to check if the affected version covers your current version before upgrading.
> - If you need to add a new bug entry, please supplement content at the corresponding location, following the field specifications and severity/type classifications below.

---

## Field Descriptions

### Required Fields

| Field | Description |
|------|------|
| **Problem** | The external manifestation of the bug, the abnormal phenomenon observable by the user. Try to provide error messages or typical scenarios |
| **Cause** | Root cause analysis, pointing to specific code defects (including "root cause chain" diagrams for complex scenarios) |
| **Affected Version** | The affected version range, in the format `introduced version - fixed version` (including both dev versions) |
| **Fixed Version** | The specific version number in which the bug was fixed |
| **Fix Content** | A brief description of the fix, including key code changes |
| **Fix Date** | The release date of the corresponding fixed version, in `YYYY/MM/DD` format |
| **Severity** | As per the "Severity Classification" below |
| **Type** | As per the "Type Classification" below, can be combined (e.g., `Adapter / Router`) |

### Optional Fields

| Field | Description | Applicable Scenarios |
|------|------|---------|
| **Reproduction Steps** | The minimal reproducible path to trigger the bug | Complex bugs, sporadic bugs are recommended to supplement |
| **Link** | Related Issue / PR / Commit links | Supplement when there are external discussion records |
| **Regression Test** | Test cases for verifying the fix and preventing regression | Supplement when corresponding pytest cases have been written |

---

## Severity Classification

| Identifier | Level | Judgment Standard | Typical Manifestations |
|------|------|---------|---------|
| 🔴 | Severe | Causes process crash, data loss/damage, core functionality completely unusable, security vulnerabilities | OOM Kill, message cannot be sent, module cannot be loaded, hot reload failure |
| 🟡 | Medium | Functional anomalies but with workaround paths, non-core functionality failure, sporadic problems | Incorrect status judgment, repeated triggering, cache expiration, inaccurate error messages |
| 🟢 | Minor | Does not affect core functionality, only code quality or experience issues, potential risks not yet triggered | Deprecated APIs, dead code, missing warning logs |

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
| CLI | `epsdk` command, `init`/`run`/`install`, argument parsing, signal handling |
| Runtime | `sdk.run`/`restart`/`uninit`, lifecycle, signals, subprocess |

---

## Entry Template

Please follow the format below when adding a new bug entry:

```markdown
### [BUG-XXX] Title

**Problem**: Problem description (error message or typical phenomenon)
**Cause**: Root cause analysis
**Affected Version**: Introduced version - Fixed version
**Fixed Version**: x.x.x
**Fix Content**: Fix plan
**Fix Date**: YYYY/MM/DD

<!-- Optional fields -->
**Reproduction Steps**: (Recommended for complex bugs)
**Link**: (Issue/PR links)
**Regression Test**: (Test case path)

**Severity**: 🔴 Severe | 🟡 Medium | 🟢 Minor
**Type**: Configuration System / Event System / Adapter / Router / Client / Storage / Loader / CLI / Runtime
```

---

## Statistics Overview

| Severity | Count |
|--------|------|
| 🔴 Severe | 16 |
| 🟡 Medium | 17 |
| 🟢 Minor | 3 |
| **Total** | **36** |

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

> Note: A single bug can belong to multiple types; the table above is counted by primary type.
> Note: Bug IDs BUG-028 / BUG-031 are missing (abandoned during registration, not recycled or renumbered to maintain existing ID stability).

---

## Fixed Bugs

### [BUG-001] Event handler registration duplication causes multiple event triggers

**Problem**: When using multiple `@message` / `@notice` decorators to register handlers, the same event is triggered multiple times, causing commands to be executed multiple times and logs to be output repeatedly.

**Cause**: `BaseEventHandler` lacks deduplication logic when registering handlers with the adapter event bus, each decorator mounts the handler once to the bus, resulting in multiple calls during event distribution.

**Affected Version**: 2.2.0-dev.0 - 2.2.1-dev.0

**Fixed Version**: 2.2.1-dev.0

**Fix Content**: Optimize `BaseEventHandler` to ensure each event type is only registered once with the adapter, avoiding repeated triggers.

**Fix Date**: 2025/08/18

**Severity**: 🔴 Severe

**Type**: Event System

---

### [BUG-002] Init command adapter configuration path type error

**Problem**: When using the `ep init` command for interactive initialization, selecting the configuration adapter results in a type error:

```
Interactive initialization failed: unsupported operand type(s) for /: 'str' and 'str'
```

**Cause**: When adjusting the configuration file path in version 2.3.7, the method parameter type is inconsistent. `_configure_adapters_interactive_sync` receives a `str` type parameter but internally uses the `Path` `/` operator to concatenate paths.

**Affected Version**: 2.3.7 - 2.3.9-dev.1

**Fixed Version**: 2.3.9-dev.1

**Fix Content**: Change the parameter type of `_configure_adapters_interactive_sync` from `str` to `Path`, passing `Path` objects directly when calling.

**Fix Date**: 2026/03/23

**Severity**: 🟡 Medium

**Type**: CLI

---

### [BUG-003] Commands fail to trigger after restart

**Problem**: After calling `sdk.restart()`, commands registered with `@command` are not triggered, resulting in no response from the robot after sending a command.

**Cause**: `adapter.shutdown()` clears the event bus, but the `_linked_to_adapter_bus` status of `BaseEventHandler` is not reset to `False`, causing the `_process_event` method to think it is already mounted to the adapter bus and skip re-registration.

**Affected Version**: 2.2.x - 2.4.0-dev.2

**Fixed Version**: 2.4.0-dev.3

**Fix Content**: Introduce `_linked_to_adapter_bus` status tracking, `clear_handlers()` disconnects the bus connection, and the next `register()` automatically re-registers, adapting to shutdown/restart scenarios.

**Fix Date**: 2026/04/09

**Severity**: 🔴 Severe

**Type**: Event System

---

### [BUG-004] Lifecycle event handlers not cleared

**Problem**: After `sdk.restart()`, old lifecycle event handlers still exist and are triggered repeatedly, causing the same event to be processed multiple times.

**Cause**: The `lifecycle._handlers` dictionary is never cleared during `uninit()`, resulting in old and new handlers both existing after restart.

**Affected Version**: 2.3.0 - 2.4.0-dev.2

**Fixed Version**: 2.4.0-dev.3

**Fix Content**: Clear `lifecycle._handlers` at the end of the `Uninitializer` cleanup process (after all events are submitted), adapting to shutdown/restart scenarios.

**Fix Date**: 2026/04/09

**Severity**: 🟡 Medium

**Type**: Runtime

---

### [BUG-005] Event.is_friend_add/is_friend_delete detail_type inconsistent with OB12 standard

**Problem**: `Event.is_friend_add()` checks `detail_type == "friend_add"`, `Event.is_friend_delete()` checks `detail_type == "friend_delete"`, but the OneBot12 standard defines `detail_type` values as `"friend_increase"` and `"friend_decrease"`. This is inconsistent with the values used in `notice.py`'s `on_friend_add`/`on_friend_remove` decorators, causing handlers registered via decorators to fail when the corresponding `is_friend_add()`/`is_friend_delete()` judgment methods return `False`.

**Cause**: `wrapper.py` uses non-standard naming, while `notice.py` uses the correct OB12 standard naming.

**Affected Version**: Implemented since

**Fixed Version**: 2.4.2-dev.1

**Fix Content**: Change `is_friend_add()`'s matching value from `"friend_add"` to `"friend_increase"`, and `is_friend_delete()` from `"friend_delete"` to `"friend_decrease"`.

**Fix Date**: 2026/04/13

**Severity**: 🟡 Medium

**Type**: Event System

---

### [BUG-006] adapter.clear() does not clear _started_instances, causing incorrect state after restart

**Problem**: The `AdapterManager.clear()` method clears `_adapters`, `_adapter_info`, handlers, and `_bots`, but omits `_started_instances`. If an adapter is running and `clear()` is called, `_started_instances` retains dangling references, causing incorrect state judgment after restart.

**Cause**: When `_started_instances` was introduced in 2.4.0-dev.1, it was not cleared in `clear()`.

**Affected Version**: 2.4.0-dev.1 - 2.4.2-dev.0

**Fixed Version**: 2.4.2-dev.1

**Fix Content**: Add `self._started_instances.clear()` in the `clear()` method.

**Fix Date**: 2026/04/13

**Severity**: 🟡 Medium

**Type**: Adapter

---

### [BUG-007] command.wait_reply() uses deprecated asyncio.get_event_loop()

**Problem**: The `CommandHandler.wait_reply()` method uses `asyncio.get_event_loop()` to create futures and obtain timestamps, which has been deprecated in Python 3.10+. In asynchronous contexts, `asyncio.get_running_loop()` should be used. This is inconsistent with the `get_running_loop()` used in the `wrapper.py` `wait_for()` method.

**Cause**: The old API was used during development, and the new `wait_for()` method used the correct API but did not retrospectively fix the old code.

**Affected Version**: 2.3.0-dev.0

**Fixed Version**: 2.4.2-dev.1

**Fix Content**: Replace `asyncio.get_event_loop()` with `asyncio.get_running_loop()` in two places in `command.py`.

**Fix Date**: 2026/04/13

**Severity**: 🟢 Minor

**Type**: Event System

---

### [BUG-008] Bot offline event is repeatedly submitted during shutdown

**Problem**: When calling `adapter.shutdown()` to shut down all adapters, `_update_bot_status()` repeatedly submits Bot offline events during the shutdown process, causing the same batch of Bots to be marked offline multiple times and triggering the `adapter.bot.offline` lifecycle event multiple times.

**Cause**: The Bot status tracking system introduced in 2.4.0-dev.1 did not set a "shutting down" flag during `shutdown()`, so `_update_bot_status()` could not distinguish between normal offline and cascading offline during the shutdown process.

**Affected Version**: 2.4.0-dev.1 - 2.4.2-dev.1

**Fixed Version**: 2.4.2-dev.1

**Fix Content**: Add `_is_being_shutdown` flag in `AdapterManager`, set to True at the start of `shutdown()` and cleared at the end; `_update_bot_status()` skips repeated submissions during the shutdown process after checking the flag.

**Fix Date**: 2026/04/21

**Severity**: 🟡 Medium

**Type**: Adapter

---

### [BUG-009] LazyModule synchronous access to BaseModule leads to incomplete initialization

**Problem**: When users access the attributes of a lazy-loaded BaseModule in a synchronous context, the module uses `loop.create_task()` for asynchronous initialization but does not wait, leading to race conditions when attributes are accessed before initialization is complete.

**Cause**: `_ensure_initialized()` uses `loop.create_task(self._initialize())` and returns immediately without ensuring initialization is complete.

**Affected Version**: 2.4.0-dev.0 - 2.4.2-dev.1

**Fixed Version**: 2.4.2-dev.2

**Fix Content**: In synchronous contexts, BaseModule initialization is changed to use `asyncio.run(self._initialize())`, ensuring initialization is complete before returning. The transparent proxy feature is maintained, so users do not need to be aware of synchronous/asynchronous differences.

**Fix Date**: 2026/04/21

**Severity**: 🟡 Medium

**Type**: Loader System

---

### [BUG-010] Multi-threaded configuration system write leads to data loss

**Problem**: In a multi-threaded environment, when multiple threads simultaneously call `config.setConfig()`, the `_flush_config()` read-modify-write operation is not atomic, potentially leading to partial write loss.

**Cause**: Although `_flush_config()` uses `RLock`, there is no file lock protection between file reading and writing, and the `_schedule_write` Timer may be triggered multiple times, causing overwrites.

**Affected Version**: 2.3.0 - 2.4.2-dev.1

**Fixed Version**: 2.4.2-dev.2

**Fix Content**:
1. Add file lock mechanism (`_file_lock`) to ensure atomic file operations
2. Use temporary file for writing and then atomically rename (`os.replace`/`os.rename`)
3. Improve `_schedule_write` Timer cancellation and re-scheduling logic

**Fix Date**: 2026/04/21

**Severity**: 🔴 Severe

**Type**: Configuration System

---

### [BUG-011] Windows Ctrl+C cannot stop the program

**Problem**: When running `python main.py` directly on Windows, pressing Ctrl+C does not terminate the program. The program starts normally and outputs routing server information, but Ctrl+C has no response and can only be forcibly terminated via Task Manager. However, running via `epsdk run` works normally—though `epsdk run` uses a subprocess model.

**Cause**: The Hypercorn ASGI server's `serve()` function internally registers its own `SIGINT` handler via `signal.signal(SIGINT, handler)`, overriding Python's default `KeyboardInterrupt` mechanism. When Hypercorn is started as a background task via `asyncio.create_task()`, its internal shutdown process cannot be triggered (because it expects the `worker_serve` mode), causing the `SIGINT` signal to be swallowed by Hypercorn without triggering any cleanup actions.

**Affected Version**: 2.3.6 - 2.4.2

**Fixed Version**: 2.4.3-dev.0

**Fix Content**:
1. Switch ASGI server from Hypercorn to Uvicorn (`pyproject.toml` dependency change)
2. Use `uvicorn.Server._serve()` to directly start the server, **bypassing** the `capture_signals()` signal handling context manager
3. Implement graceful shutdown via `server.should_exit = True`, cancel background tasks if timeout occurs
4. Synchronize removal of subprocess running model and `runtime/cleanup.py` cleanup module (no longer needed for subprocess cleanup mechanism)

**Fix Date**: 2026/04/28

**Severity**: 🔴 Severe

**Type**: CLI / Runtime

---

### [BUG-012] Hot restart does not activate updated module Python code

**Problem**: After executing `sdk.restart()` for a soft restart, the new code (such as new API routes) of modules/adapters upgraded via `epsdk install` does not take effect; it still runs the old version logic. A full restart of the process is required to load the latest code.

**Cause**: `_do_restart()` calls `entry_point.load()` during re-initialization, but this function returns a cached module object from `sys.modules` instead of reloading from disk.

**Affected Version**: Early versions - 2.4.3-dev.1

**Fixed Version**: 2.4.3-dev.1

**Fix Content**: Clear the cache of loaded modules/adapters from `sys.modules` before `init()` to ensure `entry_point.load()` reloads the latest code from disk. Add `_collect_top_level_modules()` and `_invalidate_module_cache()` helper methods, deriving top-level module names via `top_level.txt` or entry-point value.

**Fix Date**: 2026/05/03

**Severity**: 🔴 Severe

**Type**: Loader System / Runtime

---

### [BUG-013] Module loading strategy sorting logic error

**Problem**: `ModuleLoadStrategy` provides a `priority` field to declare module initialization priority, but the implementation has a flaw, causing modules to not initialize in the expected priority order, actually loading in the default `entry_points()` order. When modules have initialization dependencies, the correct initialization sequence cannot be ensured via `priority`.

**Cause**: The implementation of the sorting logic in the loading strategy is flawed; `initialize_modules()` does not sort the module list by `priority`.

**Affected Version**: 2.3.4 - 2.4.5-dev.2

**Fixed Version**: 2.4.5-dev.3

**Fix Content**: Before `initialize_modules()` iteration, sort the module list by `priority` in descending order. Modules with the same priority maintain their original relative order (stable sorting).

**Fix Date**: 2026/05/15

**Severity**: 🟡 Medium

**Type**: Loader System

---

### [BUG-014] Adapter middleware returning None causes event data loss

**Problem**: When `adapter.emit()` executes the OneBot12 middleware chain, if a middleware returns `None` (e.g., forgetting to `return data`), subsequent middlewares and all event handlers receive `processed_data` as `None`, causing event processing to fail completely.

**Cause**: The middleware chain implementation `processed_data = await middleware(processed_data)` does not check if the return value is `None`, directly overwriting the previous processing result.

**Affected Version**: unknown - 2.4.5-dev.3

**Fixed Version**: 2.4.5-dev.4

**Fix Content**: When middleware returns `None`, ignore the return value, retain the original data, and output a warning-level log.

**Fix Date**: 2026/05/15

**Severity**: 🔴 Severe

**Type**: Adapter / Event System

---

### [BUG-015] Configuration file path depends on working directory

**Problem**: The `ConfigManager`'s configuration file path is a relative path `"config/config.toml"`, which depends on `os.getcwd()` at runtime. If the working directory changes during runtime (e.g., via `os.chdir()`), configuration file read/write operations point to the wrong location, leading to configuration loss or reading old data.

**Cause**: The relative path is directly stored in `__init__` without being resolved to an absolute path at initialization.

**Affected Version**: 2.3.7 - 2.4.5-dev.3

**Fixed Version**: 2.4.5-dev.4

**Fix Content**: In `ConfigManager.__init__()`, if the passed path is a relative path, automatically resolve it to an absolute path using `os.path.abspath()`.

**Fix Date**: 2026/05/15

**Severity**: 🟡 Medium

**Type**: Configuration System

---

### [BUG-016] BaseStorage confuses storing None value with missing key

**Problem**: `BaseStorage.get_multi()` / `__getattr__()` cannot distinguish between "key does not exist" and "key's value is None", so when a user explicitly stores `None` and then reads it, it is treated as the key not existing.

**Cause**: The retrieval logic directly uses `value is None` to check if the key exists, lacking an independent "missing" marker.

**Affected Version**: Early versions - 2.4.6-dev.6

**Fixed Version**: 2.4.6-dev.6

**Fix Content**: Introduce `_SENTINEL` sentinel value to distinguish between "key does not exist" and "value is None", so they are no longer confused.

**Fix Date**: 2026/06/07

**Severity**: 🟡 Medium

**Type**: Storage

---

### [BUG-017] WebSocket route auto_accept flag lost after service restart

**Problem**: After a service restart (such as `sdk.restart()`), the `auto_accept` configuration for all WebSocket routes becomes `False`, and the originally expected automatic accept connections become pending, with clients receiving no response for a long time, resulting in WS connections being stuck.

**Cause**: `_restore_routes_from_records()` hardcodes `auto_accept` to `False` when restoring routes from persistent records, not reading the original record value; also, when the route storage tuple expanded from a binary tuple to a ternary tuple, the restore logic was not synchronized.

**Affected Version**: 2.3.8-dev.0 - 2.4.6-dev.6

**Fixed Version**: 2.4.6-dev.6

**Fix Content**: The route storage tuple expands to `(handler, auth_handler, auto_accept)`, and `_restore_routes_from_records()` reads the real `auto_accept` value from the record instead of hardcoding `False`.

**Fix Date**: 2026/06/07

**Severity**: 🔴 Severe

**Type**: Router

---

### [BUG-018] Concurrent calls to HTTP/WS client cause crashes and connection leaks

**Problem**: The HTTP and WebSocket clients in `Core/client.py` have multiple stability defects in concurrent scenarios, leading to connection leaks or process crashes:
- Concurrent calls to `ClientWebSocket.receive()` from multiple coroutines cause aiohttp to throw `Concurrent call to receive() is not allowed`
- `_get_http_session()` / `_get_ws_session()` concurrent calls may create multiple sessions, and `_drain_sessions()` does not close old connections, causing connection leaks
- `request()`'s exception handling order is incorrect: `except ClientConnectionError` (ErisPulse exception) is never triggered, aiohttp connection errors are caught by the general `except Exception`, causing the "retry + session re-creation" logic (dead code) never executed
- `send_json()` ignores the `mode="binary"` parameter; `_get_ws_session()` does not pass default request headers

**Cause**: The initial client implementation (2.4.6-dev.5) lacked concurrent protection and improper handling of aiohttp exception hierarchy and ErisPulse custom exception inheritance.

**Affected Version**: 2.4.6-dev.5 - 2.4.8

**Fixed Version**: 2.4.8

**Fix Content**:
1. Add `_recv_lock` to serialize all `receive()` / `receive_text()` / `receive_bytes()` calls
2. Add `_session_lock` to protect session creation; `_drain_sessions()` is changed to an asynchronous method and truly closes old sessions
3. Refactor `request()` exception handling order: `asyncio.TimeoutError` → `aiohttp.ClientConnectionError` (triggers session re-creation) → `aiohttp.ClientError` → `ClientError` (transparent pass) → `Exception`
4. Fix `send_json()` mode handling, `_get_ws_session()` default request header pass, `close()` concurrent race, `HttpResponse.__aexit__` duplicate `release()`

**Fix Date**: 2026/06/12

**Severity**: 🔴 Severe

**Type**: Client

---

### [BUG-019] Adapter hot reload causes route conflicts and reload failure

**Problem**: When third-party modules (such as Dashboard) trigger adapter hot reload, or when adapter startup fails and retries, because the previous registered old routes (such as `onebot11_default`) are not cleared, a `WebSocket path ... already registered` conflict is thrown, causing reload failure. A complete process restart is required to recover.

**Cause**: `AdapterManager.shutdown()` only clears routes via `unregister_all_by_namespace(platform)`, but adapters (such as OneBot11) register WebSocket routes with `onebot11_{account_name}` as the namespace, resulting in a granularity mismatch and making the cleanup an empty operation; startup failure retry routes are also not cleared of previous residual routes.

**Affected Version**: Early versions - 2.4.9

**Fixed Version**: 2.4.9

**Fix Content**:
1. Automatically track `owner → namespace` ownership relationships during route registration via `current_owner` ContextVar
2. Add `unregister_all_by_owner(owner)`, stopping/restarting adapters and cleaning up their registered resources in a single call, covering fine-grained namespaces
3. Add `_stop_adapter(platform)` primitive (stop equals cleanup), binding stopping adapters and reclaiming their registered resources in one call, `restart()` and startup failure retry both go through this entry
4. Add framework-level `adapter.restart(platform)` API, third-party modules should call this method instead of directly operating adapter instances

**Fix Date**: 2026/06/12

**Severity**: 🔴 Severe

**Type**: Adapter / Router

---

### [BUG-020] Subprocess mode `ep run <script>` cannot find sub-packages in the script's directory

**Problem**: When running a script with `ep r .\main.py` in non-hot-reload mode, if the script has relative imports (such as `from qg import ...`), it reports `No module named 'qg'`. However, the `--reload` mode works normally.

**Cause**: The non-hot-reload mode directly calls `runpy.run_path()` to execute the script, which does not automatically add the script's directory to `sys.path`. In contrast, the `--reload` mode runs via `subprocess.Popen` subprocess, which automatically inherits the current working directory, so `sys.path[0]` is the script's directory, allowing it to work properly.

**Affected Version**: 2.5.0 - 2.5.2-dev.0

**Fixed Version**: 2.5.2-dev.0

**Fix Content**: Before calling `runpy.run_path()`, manually insert the script's directory into `sys.path[0]`.

**Fix Date**: 2026/06/27

**Severity**: 🟡 Medium

**Type**: CLI

---

### [BUG-021] SQL Query Builder rejects valid wildcard and list expressions

**Problem**: `_build_select_sql()` in `SQLiteQueryBuilder` validates all SELECT columns using `_validate_identifier()`, which uses a strict whitelist regex `^[a-zA-Z_][a-zA-Z0-9_]*$`, causing valid SQL syntax to be incorrectly judged as unsafe column names:

- `SELECT *` — `*` is a standard SQL wildcard
- `SELECT COUNT(*)` — aggregate function
- `SELECT users.name` — qualified column name
- `SELECT col AS alias` — column alias

Among these, `Select("*")` is used by modules like Cron, causing module `on_load` execution to fail and the module to fail to load.

**Cause**: In version 2.4.6, SQL injection protection was enhanced, introducing `_validate_identifier()` whitelist validation. This validation is applied to all column names, but not differentiated between read-side (SELECT/ORDER BY) and write-side (INSERT/UPDATE). SELECT columns allow complex SQL expressions and should not be restricted by simple identifier whitelist.

**Affected Version**: 2.4.6 - 2.5.2-dev.1

**Fixed Version**: 2.5.2-dev.2

**Fix Content**: Change SELECT/ORDER BY column validation from whitelist mode to blacklist mode:
1. Add `_validate_select_column()` function, only blocking SQL injection dangerous characters (`;` `'` `"` `--` `/*` `*/` `\x00` newline)
2. Allow any valid SQL column expression (`*`, `table.*`, `table.column`, `COUNT(*)`, `col AS alias`, etc.)
3. INSERT/UPDATE column names still maintain strict whitelist validation (only allow simple identifiers)

**Fix Date**: 2026/06/29

**Severity**: 🔴 Severe

**Type**: Storage

---

### [BUG-022] _resolve_account() account resolution regression (_accounts_data not populated)

**Problem**: After the configuration system was refactored in version 2.5.2, multi-account adapters that declared `AccountConfigClass` encountered errors when calling methods that require sending messages, such as `wait_reply` and `reply`, reporting `ValueError("AccountConfigClass not declared, unable to resolve account")`. Even though the adapter correctly configured multi-account information, account resolution still failed.

**Cause**: In 2.5.2-dev.5, `_load_accounts()` (responsible for reading configuration, validation, and populating `_accounts_data`) was refactored into `_ensure_accounts_exist()` (only generating configuration templates), but `_resolve_account()` still checks `self._accounts_data is None`. Since `_ensure_accounts_exist()` no longer populates `_accounts_data`, this attribute remains `None`, causing `_resolve_account()` to prematurely return `(None, None)`, and account resolution fails completely.

**Root Cause Chain**:
```
_load_accounts() was deleted
  → __init__ no longer populates _accounts_data
    → _accounts_data remains None
      → _resolve_account() checks _accounts_data is None → return (None, None)
        → downstream calls to _resolve_account() (e.g., call_api) get None
          → triggers error
```

**Affected Version**: 2.5.2-dev.5 - 2.5.2

**Fixed Version**: 2.5.3

**Fix Content**: In `BaseAdapter.__init__`, after `_ensure_accounts_exist()`, restore the population of `_accounts_data`:
```python
if self.AccountConfigClass is not None:
    self._ensure_accounts_exist()
    self._accounts_data = self.accounts  # restore population, data source is real-time read accounts attribute
```
The `_resolve_account()` logic remains unchanged, fully backward compatible:
- Adapters that do not declare `AccountConfigClass`: `_accounts_data` remains `None` → return `(None, None)`
- Adapters that declare `AccountConfigClass`: `_accounts_data` is populated → normal resolution
- Adapters that overwrite `_load_accounts` or manually set `_accounts_data`: override in `super().__init__()` after, highest priority

**Fix Date**: 2026/07/07

**Severity**: 🔴 Severe

**Type**: Adapter / Configuration System

---

### [BUG-023] Cache not refreshed after account configuration modification leads to account resolution failure

**Problem**: After users modify the account configuration of a multi-account adapter (such as filling in the token) through the Dashboard, the adapter still uses the old cache, and calling message-sending related methods reports `No available account (account_id=default)`. The process must be restarted for the new configuration to take effect.

**Cause**: `_accounts_data` is only read from configuration storage once at `BaseAdapter.__init__`, and is never refreshed afterwards. `AdapterManager._run_adapter()` and `restart()` do not re-read the account configuration before calling `adapter.start()`, causing the cache to be out of sync with the actual configuration.

**Affected Version**: 2.4.6 - 2.5.4

**Fixed Version**: 2.5.4

**Fix Content**: In `AdapterManager._run_adapter()` and `restart()`, before calling `adapter.start()`, refresh `adapter._accounts_data = adapter.accounts` to ensure the latest configuration is used each time the adapter starts.

**Fix Date**: 2026/07/09

**Severity**: 🔴 Severe

**Type**: Adapter / Configuration System

---

### [BUG-024] storage.set() writing large numeric ID keys triggers OOM Kill

**Problem**: When calling `storage.set()` to write a nested key path containing a large numeric field (such as QQ group ID `871684833`), the process is killed by container OOM (exit code -9), causing the service to crash and become unrecoverable.

**Cause**: In the recursive implementation of `_set_nested_value`, pure numeric segments in the nested key path are mistakenly identified as list indices by `isdigit()`, triggering `current.extend([None] * (index - len(current) + 1))`, attempting to allocate hundreds of millions of elements, instantly exhausting memory.

**Root Cause Chain**:
```
Key path contains pure numeric segment (such as group ID 871684833)
  → isdigit() mistakenly identifies as array index
    → extend([None] * (871684833 - len(current) + 1))
      → attempts to allocate hundreds of millions of elements
        → memory exhausted → container OOM Kill (exit code -9)
```

**Affected Version**: 2.5.1 - 2.5.5

**Fixed Version**: 2.5.5

**Fix Content**:
1. Always use dictionaries when pre-creating intermediate layers, no longer guessing container type based on whether the next segment is a number
2. When setting the final value, only handle as an index if the container itself is a list and the index is less than `STORAGE_MAX_LIST_INDEX` (10000); ignore large indices safely
3. Change the recursive implementation to iterative, eliminating potential infinite recursion risks in the original code
4. Add `STORAGE_MAX_LIST_INDEX` constant to `Core/constants.py`, centrally managing the index safety limit

**Fix Date**: 2026/07/10

**Reproduction Steps**:
```python
# Trigger by writing a nested key path containing a large number field (such as QQ group ID)
await sdk.storage.aset("groups.871684833.name", "某群")
# → Process memory spikes instantly, killed by OOM
```

**Regression Test**: `tests/unit/test_unit_storage.py` adds 4 regression test cases
- `test_nested_key_numeric_segment_as_dict_key` — precisely reproduces OOM scenario
- `test_nested_key_numeric_segment_multiple` — multiple consecutive numeric segments all treated as dictionary keys
- `test_nested_key_existing_list_index_set_within_limit` — existing list index set within limit
- `test_nested_key_list_index_safety_limit` — safety limit verification for large indices

**Severity**: 🔴 Severe

**Type**: Storage

---

### [BUG-025] on_config_update callback not triggered by core routes

**Problem**: `on_config_update(old, new)` callback is defined in the base class (`BaseModule` / `BaseAdapter`), but the core framework does not associate it with configuration change events. As a result, when the configuration is modified via the configuration management panel, the callback is triggered, but when the `config.toml` file is manually edited or `setConfig()` is called, the `on_config_update` callback is not triggered.

**Cause**: `ConfigManager` emits `config.set` / `config.updated` lifecycle events when the configuration changes, but lacks the subscription logic to forward these events to each component's `on_config_update` method.

**Root Cause Chain**:
```
Core does not subscribe to config.set / config.updated
  → Configuration change events are not forwarded
    → on_config_update is not called
      → Manual file edits or code setConfig do not trigger hot update callbacks
```

**Affected Version**: All versions

**Fixed Version**: 2.6.2

**Fix Content**: `ModuleManager` / `AdapterManager` register `config.set` (covering code `setConfig()` path) and `config.updated` (covering manual file edit path) event subscriptions, match by configuration key prefix and call the corresponding component's `on_config_update`, passing type-safe configuration objects. Also fix `_flush_config()` not synchronously updating `_config_mtime`, avoiding the framework itself writing being mistakenly judged as external modification and repeatedly triggering `config.updated`.

**Compatibility Note**: The core framework now centrally maintains configuration hot updates. Previously, the configuration management panel handled the trigger, which has been removed; upgrading the framework requires simultaneous upgrade of the configuration management panel, otherwise duplicate triggers (core + panel each call once) will occur. The `on_config_update` method signature and semantics remain unchanged, subclasses do not need modification.

**Fix Date**: 2026/07/23

**Severity**: 🟡 Medium

**Type**: Configuration System

---

### [BUG-026] notice/request event reply target inference error

**Problem**: In group notification events (such as member joining a group `group_member_increase`), calling `event.reply()` sends the message to the private chat of the user who triggered the event, not to the group where the event occurred. Similarly, in friend notification events, the reply target may be misdirected.

**Cause**: `infer_receive_type()` directly returns the `detail_type` as the session type. For message events, this is correct (the `detail_type` values `private`/`group` are the session types), but for notice/request events, the `detail_type` is a semantic subtype (such as `group_member_increase`, `friend_increase`), not the session type. Subsequent `convert_to_send_type()` and `get_id_field()` lookups in the mapping table do not find this value, defaulting to `"user"` / `"user_id"`, causing the reply target to be misdirected.

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

### [BUG-027] Route rate limiting cleanup task uses fixed window causing long window rate limit rules to fail

**Problem**: When routing rate limiting is configured as a long window rule (such as `100/hour`, `{"requests": 100, "window": 3600}`), the rate limiting is essentially ineffective—actual performance is close to `100/minute` (up to approximately 6000 requests per hour), failing to provide the expected hourly protection.

**Cause**: `_apply_rate_limit` parses the actual `window` (up to 3600 seconds) for each route, and per-request checks do use this window; however, the background cleanup task `_cleanup_expired_rate_limits` uses a fixed constant `DEFAULT_RATE_LIMIT_WINDOW_SECS` (60 seconds) as the unified cleanup threshold for all routes. Thus, `100/hour` routes have timestamps earlier than 60 seconds cleared by the cleanup task, so the hour window never accumulates close to 100 records, severely weakening the rate limiting.

**Root Cause Chain**:
```
_apply_rate_limit parses window=3600 (100/hour)
  → per-request check uses 3600s retention time (correct)
  → but _cleanup_expired_rate_limits uses fixed max_window=60s to clean up
    → timestamps earlier than 60s are cleared
      → the hour window only retains records from the last 1 minute
        → 100/hour actually degrades to ~100/minute (relaxed by about 60 times)
```

**Affected Version**: 2.6.0-dev.0 - 2.7.0-dev.4

**Fixed Version**: 2.7.0-dev.5

**Fix Content**: Add `_rate_limit_windows: dict[str, int]` to record the actual window for each route; `_apply_rate_limit` writes the window when creating an entry for the first time; `_cleanup_expired_rate_limits` cleans up based on each key's own window (fallback to default value if missing); cleanup deletion and `stop()` synchronize maintenance of the two dictionaries.

**Fix Date**: 2026/07/31

**Regression Test**: `tests/unit/test_unit_router.py` → `TestRateLimit::test_cleanup_respects_per_route_window`

**Severity**: 🔴 Severe

**Type**: Router

---

### [BUG-029] Configuration listener task broadcasts incomplete TOML and silently swallows exceptions

**Problem**: When a user manually edits `config.toml` and saves halfway (producing a temporary syntax error), the configuration monitoring background thread detects the mtime change, reloads the configuration, but fails to load and still broadcasts an empty configuration `{}` as `config.updated`, causing adapters/modules' `on_config_update` to receive an empty configuration, mistakenly assuming all configuration items were cleared and reverting to default values. Additionally, the listener loop uses `except Exception: pass` to silently swallow all exceptions, making it impossible to troubleshoot watcher faults.

**Cause**: Two defects overlap:
1. `_load_config` overwrites `self._cache` with `{}` when TOML syntax errors/permission errors occur, but the background listener thread `_watch_loop` and cache timeout path `_check_cache_validity` both execute `_emit_config_updated()` unconditionally after calling `_load_config()`, broadcasting the "empty cache produced by failed load" as a real change.
2. `_watch_loop` uses `except Exception: pass` without logging any errors.

**Root Cause Chain**:
```
User saves halfway → TOML syntax error
  → _load_config() overwrites _cache = {}
    → _watch_loop unconditionally _emit_config_updated(new_config={})
      → Adapters/modules on_config_update receive empty config
        → Misjudges configuration as cleared, reverts to default values
```

**Affected Version**: 2.6.2-dev.1 - 2.7.0-dev.4

**Fixed Version**: 2.7.0-dev.5

**Fix Content**:
1. `_load_config` changed to return `bool`; if TOML syntax errors/permission errors/other errors occur, retain the last valid cache (do not overwrite with `{}`), only record diagnostic logs and return `False`
2. `_watch_loop` and `_check_cache_validity` only emit `config.updated` if `_load_config()` returns `True`
3. `_watch_loop`'s `except Exception` changed to log at warning level (new i18n key `core.config.watcher_error`, five languages synchronized)

**Fix Date**: 2026/07/31

**Regression Test**: `tests/unit/test_unit_config.py` → `test_malformed_toml_preserves_last_valid_cache`, `test_permission_denied_logs_clear_message` (updated to verify cache retention and return False)

**Severity**: 🟡 Medium

**Type**: Configuration System

---

### [BUG-030] Configuration watcher race condition causes setConfig delayed write silently drops data

**Problem**: Multiple users report that after using `config.setConfig(key, value)` (default `immediate=False`), their module configuration is not written to `config.toml`, while other modules' configurations are normal. Setting `immediate=True` (force flush) can bypass this. Manifested as: configuration written during runtime is lost after the next restart, while configuration generated during startup persists.

**Cause**: Two overlapping defects:
1. **Logical flaw**: `_watch_loop` unconditionally `_dirty_keys.clear()` when `_check_file_change()` returns `True`, discarding all pending keys. However, `_check_file_change()` only uses `!=` to compare mtime, and the framework's own `_flush_config` writing also changes mtime—although `_flush_config` updates `_config_mtime` after writing, the watcher thread may still observe mtime differences between file writing and `_config_mtime` assignment (and on coarse-grained file systems), mistakenly judging it as "external modification" and clearing all pending keys.
2. **Thread flaw**: `_watch_loop` operates `_write_timer`/`_dirty_keys` without holding `_lock`, creating data races with `setConfig` (holding lock to write `_dirty_keys`), `_schedule_write` (holding lock to write `_write_timer`).

**Root Cause Chain**:
```
ModuleA setConfig(immediate=True) → flush writes, mtime changes
  → User module setConfig(immediate=False) → enters _dirty_keys, flushes in 5s
    → Watcher loop, _check_file_change observes mtime difference from its own previous write
      → _dirty_keys.clear() → User module's pending keys are silently discarded
        → Configuration missing after restart
```

**Affected Version**: 2.6.0 - 2.7.0

**Fixed Version**: 2.7.1

**Fix Content**:
1. Add `_last_self_write_mtime` field, `_flush_config` records it after writing; `_check_file_change` compares this value first when mtime changes, matching indicates self-write and returns `False`
2. Entire `_watch_loop` section holds `_lock`; retain `_dirty_keys` for true external modification (merge semantics), next flush merges with external content (dirty keys take precedence), no longer `clear()`
3. `getConfig`/`_check_cache_validity` paths unaffected (their reload does not clear dirty keys)

**Fix Date**: 2026/08/06

**Regression Test**: `tests/unit/test_unit_config.py` → `test_self_write_not_detected_as_external`, `test_external_change_preserves_dirty_keys`, `test_flush_merges_dirty_with_external`

**Severity**: 🔴 Severe

**Type**: Configuration System

---

### [BUG-032] Configuration delay write period "write after read" reads old value

**Problem**: After `config.setConfig()` (default `immediate=False` delay about 5 seconds to flush), writing a dot-separated key and immediately reading its parent/ancestor node (such as `set_erispulse_section("scope.actions.MyModule", {...})` followed by `get_erispulse_config()`) returns the old value, the written sub-key "disappears" until the flush, affecting scope configuration hot updates and other "write-read-write" scenarios (2.8.0 test plugin `/t_section` case exposed).

**Cause**: `setConfig` stores dot-separated keys as a **flat** list in the dirty queue `_dirty_keys`, only `getConfig`'s **exact key query** hits the dirty queue; tree path queries (`getConfig("ErisPulse.scope")`) only go through the cache tree, not overlaying dirty values—during the delay write period (`_flush_config` merges dirty keys into the cache and clears the queue), a read-you-write gap forms.

**Affected Version**: 2.6.0 - 2.8.0-dev.1

**Fixed Version**: 2.8.0-dev.1

**Fix Content**: `getConfig` introduces dirty overlay semantics—① exact match in dirty key returns directly (original behavior unchanged); ② dirty key is the query key's ancestor → take the longest dirty ancestor and parse the remaining path in its value subtree; ③ dirty key is the query key's descendant → build an overlay subtree (`_dirty_overlay`) and deeply merge with the cache subtree (`_deep_merge`, override priority, without modifying the original cache object). No dirty key uses the original fast path, zero additional overhead.

**Fix Date**: 2026/09/04

**Regression Test**: `tests/unit/test_unit_config.py` → `test_get_config_overlays_dirty_descendant`, `test_get_config_overlay_merges_with_cache_siblings`, `test_get_config_overlay_new_branch`, `test_get_config_dirty_ancestor_query`, `test_get_config_dirty_exact_key_still_wins`

**Severity**: 🟡 Medium

**Type**: Configuration System

---

### [BUG-033] wait_reply hangs replies are starved by high-priority handlers

**Problem**: When a module calls `wait_reply()` to wait for a user reply, if that reply message is claimed by a higher-priority event handler (`mark_processed()`), the command dispatcher sees the `_processed` flag at the entry and returns directly, never executing the reply matching logic at the end of the dispatcher—waiting parties receive no reply, only timing out and returning `None`. Typical trigger scenario: using high-priority message handlers (recording/auditing/blocking classes) in a robot, all dialog interactions randomly fail.

**Cause**: Reply matching `_check_pending_reply` is placed at the end of `_handle_message` (only executed if command matching fails), while `_processed` checking is before it—the order of claim checking and reply matching is reversed. Interaction waiting is a framework-level session continuation mechanism, not a competing handler, and should not be affected by other handlers' claim.

**Affected Version**: 2.2.0-dev.0 - 2.8.0-dev.1

**Fixed Version**: 2.8.0-dev.2

**Fix Content**: Move reply matching to the entry of `_handle_message` (before `_processed` checking, only for message events): first try to complete pending conversations, if matched, the event is marked as processed, and subsequent checks naturally short-circuit; if not matched, continue the original command matching process. Also delegate the judgment chain to a new interaction session manager (`Core/Event/interaction.py`), gaining the ability to cancel and review permissions by affiliation.

**Fix Date**: 2026/09/08

**Regression Test**: `tests/unit/test_unit_interaction.py` (TestRegisterResolve match/unmatched/claim flag), `tests/unit/test_unit_event.py` (wait_reply full chain)

**Severity**: 🟡 Medium

**Type**: Event System / Command System

---

### [BUG-034] Scope persist=False runtime binding is silently overwritten by any subsequent configuration write

**Problem**: `scope.set_module(..., persist=False)` and other runtime writes only modify memory `self._data`; but scope subscribes to `config.set` / `config.updated` events, and any code writing configuration (such as another module loading its default configuration) triggers scope to rebuild the configuration tree from the configuration file, discarding all previous runtime bindings (reverting to default allow), with no log prompts. Scenarios depending on runtime bindings (Dashboard "runtime-only" switches, module runtime dynamic disabling) revert to behavior after unrelated module configuration writes.

**Cause**: Root cause chain: `scope.set/delete(persist=False)` only writes to memory (`Core/scope.py`) → any `setConfig` triggers `config.set` event → `_on_config_updated` unconditionally `_load_config()` → `_apply_tree()` replaces `self._data = {...}` with the entire tree → runtime bindings not in the configuration file are discarded.

**Affected Version**: 2.8.0-dev.1 - 2.8.0-dev.2
**Fixed Version**: 2.8.0-dev.2
**Fix Content**: Introduce a runtime override layer `_runtime_overrides` (with deletion sentinel): `persist=False` write/delete records in the override layer, `_apply_tree()` rebuilds the persistent layer and replays in insertion order, runtime rules remain effective after any configuration write; `persist=True` write/delete clears corresponding override records (user persistence semantics take precedence); `config.set` filters by event key, `config.updated` compares new and old scope sections, only rebuilding if scope actually changes (attached to avoid irrelevant writes flushing judgment LRU cache); add `unregister_by_owner()` for module unload to clean up with the caller. `Core.Event.overrides` with persist=False runtime override has similar issues, fixed with the override layer architecture.
**Fix Date**: 2026/09/09

**Reproduction Steps**: ① `scope.set_module("testplat", blocked=["TestB"], persist=False)` → judgment False; ② any module executes `config.setConfig("HelpModule", {...})` → triggers scope rebuild; ③ `scope.is_allowed("testplat", None, "TestB")` returns True (expected still False).
**Link**: Issue #432
**Regression Test**: `tests/unit/test_unit_scope.py::TestRuntimeOverrideSurvival` (irrelevant write survives/rebuild replay/delete sentinel/persistent clear/precise invalidation/owner cleanup)

**Severity**: 🟡 Medium
**Type**: Configuration System / Runtime

---

### [BUG-035] Configuration panel select options and dict fields render as [object Object]

**Problem**: In the WebUI configuration panel, select field options dropdown displays `[object Object]` (such as dynamically generated color style options); dict fields (such as `stalker_mode`, `knowledge_base` and other nested configuration segments) display `[object Object]` in text boxes, making it impossible to view and edit normally.

**Cause**: Two independent defects: ① The framework i18n resolver `_resolve_i18n_text` only restores dicts with `i18n` keys, options labels are dicts with only `default` (no `i18n` key for dynamic text) and are passed through as-is, frontend `esc(label)` string coercion yields `[object Object]`; ② Dashboard rendering branch only handles array types with JSON textarea, dict values fall into plain text input branch and are `String()` coerced. Additionally, if a module declares `_schema_meta` as a regular dataclass field (missing `ClassVar` annotation), it becomes a configuration field in schema, exacerbating confusion.

**Affected Version**: 2.7.0 - 2.8.0-dev.2
**Fixed Version**: 2.8.0-dev.2
**Fix Content**: ① `_resolve_i18n_text` supports dicts with only `default` as text; ② framework schema/template/default value/filling/validation five places exclude fields with underscore prefix (misdeclaration harmless); ③ Dashboard select options label object fallback parsing (priority `default`), dict/table fields rendered as JSON textarea (save path as `tp=object` JSON.parse back, complete round-trip).
**Fix Date**: 2026/09/09

**Regression Test**: `tests/unit/test_unit_config.py::TestResolveI18nDefaultOnlyDict`, `TestSchemaUnderscoreFieldExclusion`

**Severity**: 🟡 Medium
**Type**: Configuration System

---

### [BUG-036] Multi-instance shared configuration directory causes occasional configuration write failures (ENOENT)

**Problem**: In Docker deployment scenarios (multiple containers mounting the same host configuration directory), log messages occasionally show two consecutive lines of `Failed to write configuration file ... [Errno 2] No such file or directory: '...config.toml.tmp' -> '...config.toml'`. This configuration write is discarded (old configuration is fully retained, no configuration loss observed), functionality is unaffected, but alerts repeatedly interfere with troubleshooting, and pending configuration items must wait for the next write to be written to disk.

**Cause**: Root cause chain: `_flush_config` / `setConfigTemplate` use a **fixed-name** temporary file `config.toml.tmp` to hold new content, `write()` does not `fsync` before `rename()`. Two ErisPulse instances sharing the same configuration directory, B instance `open("w")` may **truncate** A instance's temporarily writing file → A `rename()` when the target has been taken over or content truncated by B, reports ENOENT (i.e., the two consecutive error messages in the user log). In reported cases, only write failure alerts were observed (old configuration retained); if the timing overlap is more extreme, `rename` may output an empty/half-written `config.toml` (potential risk, not yet exploded in real environments). In single-instance scenarios, ext4 delayed allocation also has the "rename metadata before data block is written" crash window (SIGKILL / power failure). `_file_lock` is a process-level `threading.RLock`, not constraining cross-process/cross-container writes.

**Affected Version**: 2.2.0-dev.0 - 2.8.0

**Fixed Version**: 2.8.1

**Fix Content**: Converge all configuration writes to `_atomic_write_text()`: generate process-unique temporary file (eliminate fixed-name competition, multiple instances degrade to last-writer-wins, no longer ENOENT) → write and `flush + fsync` to force data to disk (eliminate "rename effective, data not yet written" window) → `os.replace` atomically replace target (atomic on POSIX/Windows, either complete old content or complete new content on disk at any moment); additionally `fsync` configuration directory on POSIX. Three write points: `_flush_config`, `setConfigTemplate`, root directory configuration migration all switch; exception path cleanup logic restructured with unique temporary file name. Add **multi-instance detection**: advisory lock (POSIX `flock` / Windows `msvcrt.locking`) on startup to exclusively hold configuration directory lock file `.erispulse_config.lock`, output i18n warning if occupied (does not block startup), lock released automatically by OS when process exits, no ghost lock.

**Fix Date**: 2026/09/13

**Reproduction Steps**: ① Two containers mount the same host `config/` directory and run ErisPulse; ② Any instance triggers configuration write (such as module registration default configuration); ③ Observe log error of ENOENT write failure, this write is discarded (old configuration retained).

**Link**: User report (1Panel container ×2)

**Regression Test**: `tests/unit/test_unit_config_atomic_write.py` (content fully written/no temporary file residue/write failure preserves original file/two instances concurrent write file always valid/lock file creation/multi-instance warning/migration atomic write)

**Severity**: 🟢 Minor

**Type**: Configuration System

---

### [BUG-037] Space-separated command names registered but never triggered

**Problem**: After registering a subcommand with a space-separated command name (such as `@command("admin add")`), the command can be registered and appear in the help list, but when the user sends `/admin add`, the robot never responds—the input is matched as `admin` + parameters `["add"]` by the parent token command; if the parent token is also unregistered, there is no response at all. Only when using dot-separated naming (e.g., `admin.reload`, treated as a single token) can it be avoided.

**Cause**: Root cause chain: `CommandHandler.__call__` stores any command name (including space-separated forms) as-is in the flat `self.commands` dictionary → during dispatch `_try_execute_command`, only the first message token is matched (`cmd_name = parts[0]`) → multi-token command names as dictionary keys are never found. The registration and matching phases have inconsistent assumptions about the command name space, and there is no registration-time warning (silent failure).

**Affected Version**: From the introduction of the command system - 2.8.0

**Fixed Version**: 2.8.1

**Fix Content**: The matching layer changes to **longest prefix matching**: from the longest candidate (`" ".join(parts[:n])`, n capped by the maximum token count of registered command names/aliases in `_max_name_tokens`) try matching step by step, if matched, execute with the remaining tokens as parameters, downstream scope/ACL/overriding/master/permission chain naturally applies to the full command name. Accompanying semantics: when parent and child coexist, unregistered child command input falls back to the parent command (historical behavior unchanged); if the child command does not declare `permission`, it inherits the most recently declared ancestor command's permission (protecting the parent command protects all its children); only registering single-token commands hits the first round, dispatch overhead is consistent with the original. `unregister` / `unregister_by_owner` / full cleanup synchronously maintains token count cache.

**Fix Date**: 2026/09/13

**Reproduction Steps**: ① Module-level `@command("admin add")` registration; ② Send `/admin add x`; ③ Before fix, no response (or caught by the unregistered `/admin` as parameters), after fix `admin add` triggers and `get_command_args()` is `["x"]`.

**Regression Test**: `tests/unit/test_unit_command_subcommand.py` (longest prefix match/only child command triggers/three-level nesting/case sensitivity two modes/single and multi-token alias/event payload full name/lifecycle hook full name/permission inheritance six cases/ACL glob full name/master/unregister fallback and cache recalculation)

**Severity**: 🟡 Medium

**Type**: Event System

---

### [BUG-038] persist=False runtime binding is written to disk along with persistent write, "revived" from disk after module unload

**Problem**: Runtime bindings written with `scope.set(path, value, persist=False)` (documented promise not to write to disk, invalid after process restart, cleared after module unload) are written to disk along with any unrelated persistent write (default value, such as module `set_module` / WebUI save configuration); after the module is unloaded and the runtime binding is cleared, the binding is "revived" from disk after the next configuration reload and remains effective after process restart—contrary to the "runtime binding does not write to disk" semantic contract, and extremely difficult to troubleshoot.

**Cause**: Root cause chain: `ScopeManager.set()` first writes the value to the memory configuration tree `_data` (runtime binding is also directly written to `_data`) → the persistent branch makes a deep copy snapshot of the entire `_data` tree and submits it to `update_erispulse_config` for differential write to disk → the snapshot includes the values of `persist=False` bindings. `delete(persist=True)` same source: the live reference (parent node) is handed over to the delayed write dirty queue, and during the delayed write period, the live reference exists in the cross-write contamination window.

**Affected Version**: 2.8.0-dev.2 - 2.9.0-dev.0

**Fixed Version**: 2.9.0-dev.1

**Fix Content**: Introduce a persistent baseline `_persisted_tree` (the configuration tree is rebuilt from disk-loaded, validated tree as the mirror of disk truth): `set(persist=True)` only applies the current change to the baseline and submits the differential, runtime bindings never enter the persistent content; "write-then-read" changes use the final state snapshot of memory directly restored, no longer through `_apply_tree` rebuild to avoid polluting the baseline. `delete(persist=True)` same口径: apply deletion to the baseline and hand the deep copy of the baseline subtree to the persistent layer; `set_action` overall replacement semantics first delete according to the same口径 then write, old rule keys are not left in the persistent content.

**Fix Date**: 2026/09/27

**Reproduction Steps**: ① Module-level `scope.set("bots.p.debug_mode", {"blocked": ["X"]}, persist=False)`; ② Trigger any persistent write (such as another module calling `set_module`); ③ Open `config/config.toml`, see `debug_mode` has been written (before fix); ④ After module unload (runtime binding is cleared), trigger configuration reload, `scope.get("bots.p.debug_mode")` still returns the bound value.

**Regression Test**: `tests/unit/test_unit_scope.py::TestPersistBaseline` (runtime binding does not write to disk with unrelated persistent write / unloaded after configuration reload does not revive / delete submits baseline subtree without running-time sibling keys / set_action replacement leaves no residual key / cache_size configuration takes effect)

**Severity**: 🔴 Severe

**Type**: Configuration System

---

### [BUG-039] Conflicting reads and writes of sections and dot-separated keys (dot-separated overwrite lost)

**Problem**: During the delay write window, when both whole-section write (`setConfig("Mod", {...})`, such as `BaseModule.cfg` writing back) and dot-separated write (`setConfig("Mod.key", v)`, such as configuration hot update / test tool overwrite) coexist, there are two variants: Variant A (read path) — `getConfig("Mod")` whole-section read returns the old section pending write snapshot, not seeing the later dot-separated overwrite (dot-separated read path is normal); Variant B (write path, more serious) — dot-separated write before whole-section write (test tool injection overwrite → module `self.cfg = ...` writing back common timing) — `flush` applies dirty keys in insertion order, whole-section write completely replaces the section, the dot-separated overwrite is permanently lost on disk. Production environment "configuration hot update + module runtime write back" combination can trigger this, unrelated to test environment (ErisPulse-DailyCard test feedback exposed).

**Cause**: `getConfig` first segment (exact match `_dirty_keys`) returns early `return self._dirty_keys[key]`, completely bypassing the fourth segment `_dirty_overlay` descendant overlay; `_flush_config` applies dirty keys in insertion order, whole-section write happens to be after dot-separated write, dot-separated values are replaced. Also: `getConfig` returning (exact match / ancestor subtree / overlay merge) in the dirty window is changed to `copy.deepcopy` isolated copy, no longer leaking dirty queue internal references; no dirty key fast path and pure cache read behavior unchanged.

**Affected Version**: 2.6.0 - 2.9.0-dev.1

**Fixed Version**: 2.9.0-dev.1

**Fix Content**: Dirty window unified as **specificity-first** semantics — dot-separated (more specific) pending values take precedence over whole-section (more general) pending values, read path and flush path same口径: ① `getConfig` exact match pending key still overlays `_dirty_overlay` descendant pending values (not dict value returns overlay subtree, same口径 as ③+④ scalar edge cases); ② `_flush_config` dirty keys apply in path depth order (whole-section/ancestor first, dot-separated/descendant later, stable sort maintains same depth write order). Cost: same dirty window (about 5 seconds) whole-section write back cannot override still pending dot-separated write — read path fixed, read-modify-write naturally carries dot-separated value, actual impact surface is extremely small. ③ Involved pending values of `getConfig` return (exact match / ancestor subtree / overlay merge) changed to `copy.deepcopy` isolated copy, no longer leak dirty queue internal reference; no dirty key fast path and pure cache read behavior unchanged.

**Fix Date**: 2026/09/28

**Reproduction Steps**: ① `setConfig("FB.y", 1)`; ② `setConfig("FB", {"z": 2})`; ③ `force_save()` — before fix, only `[FB] z = 2` remains on disk (y lost), after fix `{"y": 1, "z": 2}`; Variant A: steps ①② without save directly `getConfig("FB")` — before fix, does not contain `y`, after fix visible.

**Regression Test**: `tests/unit/test_unit_config.py::TestSectionAndDottedDirtyConsistency` (Variant A two insertion orders / Variant B flush and order independent / three-level mixed survival / isolated copy / ancestor subtree isolation)

**Severity**: 🟡 Medium

**Type**: Configuration System