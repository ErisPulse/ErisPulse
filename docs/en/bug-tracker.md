# Bug Tracker

This document records known bugs of the ErisPulse SDK and their resolution status, ordered chronologically by the version in which they were fixed.

> **For Readers**
> No software is inherently perfect; even the most careful developers leave small mistakes. This tracker includes only issues that have a practical impact on operation—those too minor to even reach the "minor" level are not included here. Although the number of "critical" items in the list may seem large, the original intention of publicly documenting these bugs is to facilitate troubleshooting and traceability, not to create anxiety: problems that are visible, recorded, and fixed are proof that the project is continuously improving. Don't be alarmed by this list; it is a troubleshooting tool, not a source of fear.

> **How to Read & Maintenance Guidelines**
> - Each bug record includes structured fields such as problem description, root cause analysis, affected version range, and fix solution. It is recommended to check the "Affected Version" before upgrading to see if your current version is covered.
> - If you need to add a new bug entry, please add content at the corresponding position, following the field specifications and severity/type classifications below.

---

## Field Descriptions

### Mandatory Fields

| Field | Description |
|------|------|
| **Problem** | The external manifestation of the bug, observable anomalies by users. Try to provide error messages or typical scenarios |
| **Cause** | Root cause analysis, pointing to specific code defects (including "root cause chain" diagrams for complex scenarios) |
| **Affected Version** | Affected version range, format `introduced version - fixed version` (including dev versions) |
| **Fixed Version** | The specific version number that fixed the bug |
| **Fix Content** | Brief description of the fix solution, including key code changes |
| **Fix Date** | The release date of the corresponding fixed version, in `YYYY/MM/DD` format |
| **Severity** | As per the "Severity Classification" below |
| **Type** | As per the "Type Classification" below, can be combined (e.g., `Adapter / Router`) |

### Optional Fields

| Field | Description | Applicable Scenarios |
|------|------|---------|
| **Reproduction Steps** | The minimal reproducible path to trigger the bug | Complex bugs, sporadic bugs are recommended to supplement |
| **关联** | Related Issue / PR / Commit links | Supplement when there are external discussion records |
| **Regression Test** | Test case location for verifying the fix and preventing regression | Supplement when corresponding pytest cases are written |

---

## Severity Classification

| Identifier | Level | Judgment Criteria | Typical Manifestations |
|------|------|---------|---------|
| 🔴 | Critical | Causes process crash, data loss/damage, core functionality completely unusable, security vulnerabilities | OOM Kill, message cannot be sent, module cannot be loaded, hot reload fails |
| 🟡 | Medium | Functional anomalies but with workaround paths, non-core functionality failure, sporadic problems | Incorrect status judgment, repeated triggers, cache expiration, inaccurate error prompts |
| 🟢 | Minor | Does not affect core functionality, only code quality or experience issues, potential risks not yet triggered | Deprecated APIs, dead code, missing warning logs |

---

## Type Classification

| Type | Coverage Scope |
|------|---------|
| Configuration System | `ConfigManager`, configuration reading/writing, configuration Schema, hot update |
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

Please follow the format below when adding a new bug entry:

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
**关联**: (Issue/PR links)
**Regression Test**: (Test case path)

**Severity**: 🔴 Critical | 🟡 Medium | 🟢 Minor
**Type**: Configuration System / Event System / Adapter / Router / Client / Storage / Loader / CLI / Runtime
```

---

## Statistics Overview

| Severity | Count |
|--------|------|
| 🔴 Critical | 16 |
| 🟡 Medium | 17 |
| 🟢 Minor | 3 |
| **Total** | **36** |

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

> Note: A single bug can belong to multiple types; the table counts by primary type.

---

## Fixed Bugs

### [BUG-001] Event handler registration duplication leads to multiple event triggers

**Problem**: When using multiple `@message` / `@notice` decorators to register handlers, the same event is triggered multiple times, causing commands to be executed multiple times and logs to be output repeatedly.

**Cause**: `BaseEventHandler` registers handlers to the adapter event bus without deduplication logic; each decorator mounts to the bus once, resulting in multiple calls during event distribution.

**Affected Version**: 2.2.0-dev.0 - 2.2.1-dev.0

**Fixed Version**: 2.2.1-dev.0

**Fix Content**: Optimize `BaseEventHandler` to ensure each event type registers only once to the adapter, avoiding repeated triggers.

**Fix Date**: 2025/08/18

**Severity**: 🔴 Critical

**Type**: Event System

---

### [BUG-002] Init command adapter configuration path type error

**Problem**: When using the `ep init` command for interactive initialization, selecting the configuration adapter results in a type error:

```
Interactive initialization failed: unsupported operand type(s) for /: 'str' and 'str'
```

**Cause**: In version 2.3.7, adjusting the configuration file path caused inconsistent method parameter types. `_configure_adapters_interactive_sync` receives a `str` type parameter but internally uses the `Path` `/` operator to concatenate paths.

**Affected Version**: 2.3.7 - 2.3.9-dev.1

**Fixed Version**: 2.3.9-dev.1

**Fix Content**: Change the parameter type of `_configure_adapters_interactive_sync` from `str` to `Path`, passing `Path` objects directly when called.

**Fix Date**: 2026/03/23

**Severity**: 🟡 Medium

**Type**: CLI

---

### [BUG-003] Commands fail after restart

**Problem**: After calling `sdk.restart()`, commands registered via `@command` are not triggered, causing the robot to be unresponsive after sending a command.

**Cause**: After `adapter.shutdown()` clears the event bus, the `_linked_to_adapter_bus` status of `BaseEventHandler` is not reset to `False`, causing the `_process_event` method to think it has been mounted to the adapter bus and skip re-mounting.

**Affected Version**: 2.2.x - 2.4.0-dev.2

**Fixed Version**: 2.4.0-dev.3

**Fix Content**: Introduce `_linked_to_adapter_bus` status tracking; after `_clear_handlers()` disconnects the bus, the next `register()` automatically re-mounts, adapting to shutdown/restart scenarios.

**Fix Date**: 2026/04/09

**Severity**: 🔴 Critical

**Type**: Event System

---

### [BUG-004] Lifecycle event handler not cleaned up

**Problem**: After `sdk.restart()`, old lifecycle event handlers still exist and are repeatedly triggered, causing the same event to be processed multiple times.

**Cause**: The `lifecycle._handlers` dictionary was never cleared in `uninit()`, leaving old handlers and new handlers coexisting after restart.

**Affected Version**: 2.3.0 - 2.4.0-dev.2

**Fixed Version**: 2.4.0-dev.3

**Fix Content**: Clear `lifecycle._handlers` at the end of the `Uninitializer` cleanup process (after all events are submitted), clearing old handlers.

**Fix Date**: 2026/04/09

**Severity**: 🟡 Medium

**Type**: Runtime

---

### [BUG-005] Event.is_friend_add/is_friend_delete detail_type inconsistent with OB12 standard

**Problem**: `Event.is_friend_add()` checks `detail_type == "friend_add"`, `Event.is_friend_delete()` checks `detail_type == "friend_delete"`, but OneBot12 standard defines `detail_type` values as `"friend_increase"` and `"friend_decrease"`. This inconsistency with the values used by `notice.py`'s `on_friend_add`/`on_friend_remove` decorators causes handlers registered via decorators to fail when the corresponding `is_friend_add()`/`is_friend_delete()` judgment methods return `False`.

**Cause**: `wrapper.py` uses non-standard naming, while `notice.py` uses the correct OB12 standard naming.

**Affected Version**: Since implementation

**Fixed Version**: 2.4.2-dev.1

**Fix Content**: Change `is_friend_add()`'s matching value from `"friend_add"` to `"friend_increase"`, and `is_friend_delete()` from `"friend_delete"` to `"friend_decrease"`.

**Fix Date**: 2026/04/13

**Severity**: 🟡 Medium

**Type**: Event System

---

### [BUG-006] adapter.clear() does not clear _started_instances, causing incorrect state after restart

**Problem**: The `AdapterManager.clear()` method clears `_adapters`, `_adapter_info`, handlers, and `_bots`, but omits clearing the `_started_instances` set. If `clear()` is called while the adapter is running, `_started_instances` retains dangling references, causing incorrect state judgment after restart.

**Cause**: When `_started_instances` was introduced in 2.4.0-dev.1, it was not cleared in `clear()`.

**Affected Version**: 2.4.0-dev.1 - 2.4.2-dev.0

**Fixed Version**: 2.4.2-dev.1

**Fix Content**: Add `self._started_instances.clear()` in the `clear()` method.

**Fix Date**: 2026/04/13

**Severity**: 🟡 Medium

**Type**: Adapter

---

### [BUG-007] command.wait_reply() uses deprecated asyncio.get_event_loop()

**Problem**: The `CommandHandler.wait_reply()` method uses `asyncio.get_event_loop()` to create futures and obtain timestamps, which has been deprecated in Python 3.10+. In asynchronous contexts, `asyncio.get_running_loop()` should be used. This is inconsistent with the `get_running_loop()` used in the `wrapper.py` `wait_for()` method in the same file.

**Cause**: The development used the old API, and the newly added `wait_for()` method used the correct API but did not retroactively fix the old code.

**Affected Version**: 2.3.0-dev.0

**Fixed Version**: 2.4.2-dev.1

**Fix Content**: Replace `asyncio.get_event_loop()` with `asyncio.get_running_loop()` in `command.py` in two places.

**Fix Date**: 2026/04/13

**Severity**: 🟢 Minor

**Type**: Event System

---

### [BUG-008] Bot offline event is repeatedly submitted during shutdown

**Problem**: When calling `adapter.shutdown()` to shut down all adapters, `_update_bot_status()` repeatedly submits Bot offline events during the shutdown process, causing the same batch of Bots to be marked offline multiple times and triggering multiple `adapter.bot.offline` lifecycle events.

**Cause**: The Bot status tracking system introduced in 2.4.0-dev.1 did not set a "shutting down" flag during shutdown, so `_update_bot_status()` could not distinguish between normal offline and cascading offline during shutdown.

**Affected Version**: 2.4.0-dev.1 - 2.4.2-dev.1

**Fixed Version**: 2.4.2-dev.1

**Fix Content**: Add `_is_being_shutdown` flag in `AdapterManager`. Set it to True at the start of `shutdown()` and clear it at the end; `_update_bot_status()` skips repeated submissions during shutdown after checking the flag.

**Fix Date**: 2026/04/21

**Severity**: 🟡 Medium

**Type**: Adapter

---

### [BUG-009] LazyModule synchronous access to BaseModule leads to incomplete initialization

**Problem**: When users access a lazy-loaded BaseModule attribute in a synchronous context, the module uses `loop.create_task()` for asynchronous initialization but does not wait, causing initialization to possibly complete before attribute access, leading to race conditions.

**Cause**: `_ensure_initialized()` uses `loop.create_task(self._initialize())` and returns immediately without ensuring initialization is complete.

**Affected Version**: 2.4.0-dev.0 - 2.4.2-dev.1

**Fixed Version**: 2.4.2-dev.2

**Fix Content**: In synchronous contexts, BaseModule initialization is changed to use `asyncio.run(self._initialize())`, ensuring initialization is complete before returning. The transparent proxy feature is maintained, so users do not need to be aware of the difference between synchronous and asynchronous contexts.

**Fix Date**: 2026/04/21

**Severity**: 🟡 Medium

**Type**: Loader

---

### [BUG-010] Multi-threaded configuration write leads to data loss

**Problem**: In multi-threaded environments, when multiple threads simultaneously call `config.setConfig()`, the `_flush_config()` read-modify-write operation is not atomic, potentially causing partial write loss.

**Cause**: Although `_flush_config()` uses `RLock`, there is no file lock protection between file read and write, and the `_schedule_write` Timer may be triggered multiple times, causing overwrite.

**Affected Version**: 2.3.0 - 2.4.2-dev.1

**Fixed Version**: 2.4.2-dev.2

**Fix Content**:
1. Add file locking mechanism (`_file_lock`) to ensure atomic file operations
2. Use temporary file for writing and then atomically rename (`os.replace`/`os.rename`)
3. Improve `_schedule_write` Timer cancellation and re-scheduling logic

**Fix Date**: 2026/04/21

**Severity**: 🔴 Critical

**Type**: Configuration System

---

### [BUG-011] Windows Ctrl+C cannot stop the program

**Problem**: When running `python main.py` directly on Windows, pressing Ctrl+C does not terminate the program. After the program starts normally and outputs the routing server information, Ctrl+C has no response and can only be forcibly terminated via the task manager. However, stopping via `epsdk run` works normally—though `epsdk run` runs through a subprocess model.

**Cause**: The Hypercorn ASGI server's `serve()` function internally registers its own SIGINT handler via `signal.signal(SIGINT, handler)`, overriding Python's default `KeyboardInterrupt` handling mechanism. When Hypercorn is started as a background task via `asyncio.create_task()`, its internal shutdown process cannot be triggered properly (because it expects the `worker_serve` mode), causing the Ctrl+C signal to be swallowed by Hypercorn without triggering any cleanup actions.

**Affected Version**: 2.3.6 - 2.4.2

**Fixed Version**: 2.4.3-dev.0

**Fix Content**:
1. Switch the ASGI server from Hypercorn to Uvicorn (`pyproject.toml` dependency change)
2. Use `uvicorn.Server._serve()` to start the server directly, bypassing the `capture_signals` signal handling context manager
3. Use `server.should_exit = True` for graceful shutdown, canceling the background task if timeout occurs
4. Synchronously remove the subprocess running model and `runtime/cleanup.py` cleanup module (no longer needed)

**Fix Date**: 2026/04/28

**Severity**: 🔴 Critical

**Type**: CLI / Runtime

---

### [BUG-012] Hot restart after updating modules does not take effect

**Problem**: After executing `sdk.restart()` for a soft restart, the new code (such as new API routes) of modules/adapters upgraded via `epsdk install` does not take effect and still runs old logic. The latest code can only be loaded by completely restarting the process.

**Cause**: `_do_restart()` calls `entry_point.load()` during re-initialization, but this function returns the cached old module object from `sys.modules` instead of reloading from disk.

**Affected Version**: Early versions - 2.4.3-dev.1

**Fixed Version**: 2.4.3-dev.1

**Fix Content**: Clear the cache of loaded modules/adapters in `sys.modules` before `init()` after `uninit()`, so that `entry_point.load()` loads the latest code from disk. Added `_collect_top_level_modules()` and `_invalidate_module_cache()` helper methods, deriving top-level module names via `top_level.txt` or entry-point value.

**Fix Date**: 2026/05/03

**Severity**: 🔴 Critical

**Type**: Loader / Runtime

---

### [BUG-013] Module loading strategy sorting logic error

**Problem**: `ModuleLoadStrategy` provides a `priority` field to declare the initialization priority of modules, but the implementation of the loading strategy has a flaw, causing modules not to be initialized in the expected priority order; instead, they are loaded in the default order of `entry_points()`. When modules have initialization dependencies, they cannot ensure the correct initialization order through `priority`.

**Cause**: The implementation of the loading strategy has a flawed sorting logic; `initialize_modules()` does not sort the module list by `priority` before iteration.

**Affected Version**: 2.3.4 - 2.4.5-dev.2

**Fixed Version**: 2.4.5-dev.3

**Fix Content**: Before `initialize_modules()` iteration, sort the module list by `priority` in descending order. Modules with the same priority maintain their original relative order (stable sort).

**Fix Date**: 2026/05/15

**Severity**: 🟡 Medium

**Type**: Loader

---

### [BUG-014] Adapter middleware returning None causes event data loss

**Problem**: When `adapter.emit()` executes the OneBot12 middleware chain, if a middleware returns `None` (e.g., forgetting to `return data`), subsequent middlewares and all event handlers receive `processed_data` as `None`, causing event processing to fail completely.

**Cause**: The middleware chain implementation `processed_data = await middleware(processed_data)` does not check if the return value is `None`, directly overwriting the result of the previous step.

**Affected Version**: unknown - 2.4.5-dev.3

**Fixed Version**: 2.4.5-dev.4

**Fix Content**: When middleware returns `None`, ignore the return value, retain the original data, and output a warning-level log.

**Fix Date**: 2026/05/15

**Severity**: 🔴 Critical

**Type**: Adapter / Event System

---

### [BUG-015] Configuration file path depends on working directory

**Problem**: The configuration file path in `ConfigManager` is a relative path `"config/config.toml"` by default, resolved using `os.getcwd()` at runtime. If the working directory changes during runtime (e.g., via `os.chdir()`), configuration file read/write operations point to the wrong location, leading to configuration loss or reading old data.

**Cause**: In `__init__`, the relative path is stored directly without being resolved to an absolute path during initialization.

**Affected Version**: 2.3.7 - 2.4.5-dev.3

**Fixed Version**: 2.4.5-dev.4

**Fix Content**: In `ConfigManager.__init__()`, if the passed path is relative, automatically resolve it to an absolute path using `os.path.abspath()`.

**Fix Date**: 2026/05/15

**Severity**: 🟡 Medium

**Type**: Configuration System

---

### [BUG-016] BaseStorage confuses storing None value with missing key

**Problem**: `BaseStorage.get_multi()` / `__getattr__()` cannot distinguish between "key does not exist" and "key's value is None", so when a user explicitly stores `None` and then reads it, it is treated as the key not existing.

**Cause**: The retrieval logic directly uses `value is None` to determine if the key exists, lacking an independent "missing" marker.

**Affected Version**: Early versions - 2.4.6-dev.6

**Fixed Version**: 2.4.6-dev.6

**Fix Content**: Introduce `_SENTINEL` sentinel value to distinguish between "key does not exist" and "value is None", no longer confusing the two.

**Fix Date**: 2026/06/07

**Severity**: 🟡 Medium

**Type**: Storage

---

### [BUG-017] WebSocket route auto_accept flag lost after service restart

**Problem**: After a service restart (such as `sdk.restart()`), the `auto_accept` configuration of all WebSocket routes becomes `False`, and the originally expected automatic accept connections remain pending, causing the client to receive no response for a long time, manifesting as a stuck WebSocket connection.

**Cause**: `_restore_routes_from_records()` hardcodes `auto_accept` as `False` when restoring routes from persistent records, without reading the original record's value; also, the route storage tuple expanded from a binary tuple to a ternary tuple was not synchronized with the restoration logic.

**Affected Version**: 2.3.8-dev.0 - 2.4.6-dev.6

**Fixed Version**: 2.4.6-dev.6

**Fix Content**: The route storage tuple is expanded to `(handler, auth_handler, auto_accept)`, and `_restore_routes_from_records()` reads the real `auto_accept` value from the record instead of hardcoding `False`.

**Fix Date**: 2026/06/07

**Severity**: 🔴 Critical

**Type**: Router

---

### [BUG-018] Concurrent calls to HTTP/WS client cause crashes and connection leaks

**Problem**: The HTTP and WebSocket clients in `Core/client.py` have multiple stability flaws in concurrent scenarios, leading to connection leaks or process crashes:
- Concurrent calls to `ClientWebSocket.receive()` by multiple coroutines cause aiohttp to throw `Concurrent call to receive() is not allowed`
- Concurrent calls to `_get_http_session()` / `_get_ws_session()` may create multiple sessions, and `_drain_sessions()` does not close old connections, causing connection leaks
- The exception handling order in `request()` is incorrect: `except ClientConnectionError` (ErisPulse exception) is never triggered, aiohttp connection errors are caught by the general `except Exception`, causing the "connection retry + session rebuild" logic (dead code) to never execute
- `send_json()` ignores the `mode="binary"` parameter; `_get_ws_session()` does not pass default request headers

**Cause**: The initial client implementation (2.4.6-dev.5) lacks concurrent protection and exception classification, improperly handling the aiohttp exception hierarchy and ErisPulse custom exception inheritance relationship.

**Affected Version**: 2.4.6-dev.5 - 2.4.8

**Fixed Version**: 2.4.8

**Fix Content**:
1. Add `_recv_lock` to serialize all `receive()` / `receive_text()` / `receive_bytes()` calls
2. Add `_session_lock` to protect session creation; `_drain_sessions()` is changed to an asynchronous method and truly closes old sessions
3. Refactor the `request()` exception handling order: `asyncio.TimeoutError` → `aiohttp.ClientConnectionError` (triggers session rebuild) → `aiohttp.ClientError` → `ClientError` (transparent pass) → `Exception`
4. Fix `send_json()`'s mode handling, `_get_ws_session()`'s default request header pass, `close()`'s concurrent race condition, `HttpResponse.__aexit__`'s repeated `release()`

**Fix Date**: 2026/06/12

**Severity**: 🔴 Critical

**Type**: Client

---

### [BUG-019] Hot reload of adapter causes route conflicts leading to reload failure

**Problem**: When a third-party module (such as Dashboard) triggers adapter hot reload, or adapter startup fails and retries, old routes (such as `onebot11_default`) are not cleared due to previous registration, throwing a `WebSocket path ... already registered` conflict, causing reload failure. A complete process restart is required to restore.

**Cause**: `AdapterManager.shutdown()` only clears routes with `unregister_all_by_namespace(platform)`, but adapters (such as OneBot11) register WebSocket routes with `onebot11_{account_name}` as namespace, resulting in a granularity mismatch and making cleanup an empty operation; startup failure retry routes are also not cleared of residual routes from the previous session.

**Affected Version**: Early versions - 2.4.9

**Fixed Version**: 2.4.9

**Fix Content**:
1. Route registration automatically tracks `owner → namespace` relationship through `current_owner` ContextVar
2. Add `unregister_all_by_owner(owner)`, stopping/restarting with cleanup by owner, covering fine-grained namespace
3. Add `_stop_adapter(platform)` primitive ("stop equals cleanup"), binding stopping adapter and recycling its registered resources in one call, `restart()` and startup failure retry both go through this entry
4. Add framework-level `adapter.restart(platform)` API, third-party modules should call this method instead of directly operating adapter instances

**Fix Date**: 2026/06/12

**Severity**: 🔴 Critical

**Type**: Adapter / Router

---

### [BUG-020] Subprocess mode `ep run <script>` cannot find submodules in script's directory

**Problem**: When using `ep r .\main.py` to run a script without hot reload, if the script has relative imports (such as `from qg import ...`), it reports `No module named 'qg'` error. While the `--reload` mode works normally.

**Cause**: The non-hot reload mode directly calls `runpy.run_path()` to execute the script, which does not automatically add the script's directory to `sys.path`. The `--reload` mode runs via `subprocess.Popen` subprocess, which inherits the current working directory, and `sys.path[0]` is the script's directory, so it works normally.

**Affected Version**: 2.5.0 - 2.5.2-dev.0

**Fixed Version**: 2.5.2-dev.0

**Fix Content**: Before calling `runpy.run_path()`, manually insert the script's directory into `sys.path[0]`.

**Fix Date**: 2026/06/27

**Severity**: 🟡 Medium

**Type**: CLI

---

### [BUG-021] SQL query builder rejects legitimate wildcard and list expressions

**Problem**: `SQLiteQueryBuilder`'s `_build_select_sql()` calls `_validate_identifier()` for all SELECT columns, which uses a strict whitelist regex `^[a-zA-Z_][a-zA-Z0-9_]*$`, causing legitimate SQL syntax to be incorrectly judged as unsafe column names:

- `SELECT *` — `*` is a standard SQL wildcard
- `SELECT COUNT(*)` — aggregate function
- `SELECT users.name` — qualified column name
- `SELECT col AS alias` — column alias

Among them, `Select("*")` is used by Cron and other modules, causing the module `on_load` execution to fail and the module cannot load.

**Cause**: In version 2.4.6, enhanced SQL injection protection introduced `_validate_identifier()` whitelist validation. This validation is applied to all column names, but does not distinguish between read端 (SELECT/ORDER BY) and write端 (INSERT/UPDATE). SELECT columns allow complex SQL expressions and should not be restricted by simple identifier whitelist.

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

### [BUG-022] _resolve_account() account resolution regression (_accounts_data not populated)

**Problem**: After the configuration system was refactored in 2.5.2, declaring `AccountConfigClass` for multi-account adapters results in errors like `ValueError("未声明 AccountConfigClass，无法解析账户")` when calling methods that require sending messages, such as `wait_reply`, `reply`, etc. Even if the adapter correctly configures multi-account information, account resolution still fails.

**Cause**: In 2.5.2-dev.5, `_load_accounts()` (responsible for reading configuration + validation + populating `_accounts_data`) was refactored into `_ensure_accounts_exist()` (only generates configuration template), but `_resolve_account()` still checks `self._accounts_data is None`. Since `_ensure_accounts_exist()` no longer populates `_accounts_data`, this attribute remains `None`, causing `_resolve_account()` to prematurely return `(None, None)`, and account resolution fails completely.

**Root Cause Chain**:
```
_load_accounts() was deleted
  → __init__ no longer populates _accounts_data
    → _accounts_data is always None
      → _resolve_account() checks _accounts_data is None → return (None, None)
        → downstream calls to _resolve_account (e.g. call_api) get None
          → triggers error
```

**Affected Version**: 2.5.2-dev.5 - 2.5.2

**Fixed Version**: 2.5.3

**Fix Content**: In `BaseAdapter.__init__`, after `_ensure_accounts_exist()`, restore the population of `_accounts_data`:
```python
if self.AccountConfigClass is not None:
    self._ensure_accounts_exist()
    self._accounts_data = self.accounts  # Restore population, data source is real-time read accounts property
```
The `_resolve_account()` logic remains unchanged, fully backward compatible:
- For adapters that do not declare `AccountConfigClass`: `_accounts_data` remains `None` → return `(None, None)`
- For adapters that declare `AccountConfigClass`: `_accounts_data` is populated → normal resolution
- For adapters that override `_load_accounts` or manually set `_accounts_data`: override after `super().__init__()` call, highest priority

**Fix Date**: 2026/07/07

**Severity**: 🔴 Critical

**Type**: Adapter / Configuration System

---

### [BUG-023] Adapter cache not refreshed after account configuration modification leads to account resolution failure

**Problem**: After users modify the account configuration of a multi-account adapter (such as filling in the token) via Dashboard, the adapter still uses the old cache, and calling message-sending-related methods reports `未找到可用账户 (account_id=default)`. The new configuration must be restarted to take effect.

**Cause**: `_accounts_data` is only read from the configuration storage once during `BaseAdapter.__init__`, and is not refreshed afterwards. `AdapterManager._run_adapter()` and `restart()` do not re-read the account configuration before calling `adapter.start()`, causing the cache to be out of sync with the actual configuration.

**Affected Version**: 2.4.6 - 2.5.4

**Fixed Version**: 2.5.4

**Fix Content**: In `AdapterManager._run_adapter()` and `restart()`, before calling `adapter.start()`, refresh `adapter._accounts_data = adapter.accounts` to ensure the latest configuration is used each time the adapter starts.

**Fix Date**: 2026/07/09

**Severity**: 🔴 Critical

**Type**: Adapter / Configuration System

---

### [BUG-024] storage.set() writing large numeric ID keys triggers OOM Kill

**Problem**: When calling `storage.set()` to write a nested key path containing a large numeric field (such as QQ group number `871684833`), the process is OOM Killed (exit code -9), causing the service to crash and unable to recover.

**Cause**: In the recursive implementation of `_set_nested_value`, pure numeric segments in the nested key path are mistakenly identified as list indices by `isdigit()`, triggering `current.extend([None] * (index - len(current) + 1))`, attempting to allocate hundreds of millions of elements, instantly consuming all memory.

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
1. Always use a dictionary when pre-creating intermediate layers, never guess the container type based on whether the next segment is a number
2. Only when the container itself is a list and the index is less than `STORAGE_MAX_LIST_INDEX` (10000) do we handle it by index; large indices are safely skipped
3. Change the recursive implementation to an iterative one, eliminating the potential for infinite recursion in the original code
4. Add `STORAGE_MAX_LIST_INDEX` constant to `Core/constants.py`, centrally managing the index safety limit

**Fix Date**: 2026/07/10

**Reproduction Steps**:
```python
# Writing a nested key path containing a large number field (such as a QQ group number) triggers OOM
await sdk.storage.aset("groups.871684833.name", "某群")
# → Process memory surges instantly, OOM Kill
```

**Regression Test**: `tests/unit/test_unit_storage.py` adds 4 regression test cases
- `test_nested_key_numeric_segment_as_dict_key` — precisely reproduces the OOM scenario
- `test_nested_key_numeric_segment_multiple` — multiple consecutive numeric segments as dictionary keys
- `test_nested_key_existing_list_index_set_within_limit` — existing list index write within limit
- `test_nested_key_list_index_safety_limit` — safety limit verification for large indices

**Severity**: 🔴 Critical

**Type**: Storage

---

### [BUG-025] on_config_update callback not triggered by core router

**Problem**: `on_config_update(old, new)` is defined in the base class (`BaseModule` / `BaseAdapter`), but the framework core does not associate it with configuration change events. The actual manifestation: when modifying configuration via the configuration management panel, it can be triggered, but when manually editing `config.toml` or calling `setConfig()` programmatically, `on_config_update` is not triggered.

**Cause**: `ConfigManager` emits `config.set` / `config.updated` lifecycle events when configuration changes, but lacks the subscription logic to forward these events to each component's `on_config_update` method.

**Root Cause Chain**:
```
Core does not subscribe to config.set / config.updated
  → Configuration change events are not forwarded
    → on_config_update is not called
      → Manual file editing or code setConfig does not trigger hot update callback
```

**Affected Version**: All versions

**Fixed Version**: 2.6.2

**Fix Content**: `ModuleManager` / `AdapterManager` register `config.set` (covering code `setConfig()` path) and `config.updated` (covering manual file editing path) event subscriptions, match by configuration key prefix and call the corresponding component's `on_config_update`, passing type-safe configuration objects. Also fix `_flush_config()` not synchronizing `_config_mtime` after writing the file, avoiding the framework's own write being misjudged as an external modification by the file monitoring task and repeatedly triggering `config.updated`.

**Compatibility Note**: Hot configuration updates are now centrally maintained by the framework core. Previously, the configuration management panel triggered it on its behalf, which has been removed; after upgrading the framework, the configuration management panel must also be upgraded, otherwise it will be triggered twice (core + panel each call once). The `on_config_update` method signature and semantics remain unchanged, subclasses need no modification.

**Fix Date**: 2026/07/23

**Severity**: 🟡 Medium

**Type**: Configuration System

---

### [BUG-026] notice/request event reply target inferred incorrectly

**Problem**: In group notification events (such as member joining a group `group_member_increase`), calling `event.reply()` sends the message to the user who triggered the event's private chat, not the group where the event occurred. The same applies to friend notification events, where the reply target may be incorrect.

**Cause**: `infer_receive_type()` directly returns the event's `detail_type` as the session type. For message events, this is correct (`detail_type` values `private`/`group` are session types), but for notice/request events, `detail_type` is a semantic subtype (such as `group_member_increase`, `friend_increase`), not a session type. The subsequent `convert_to_send_type()` and `get_id_field()` mapping tables do not find this value, defaulting to `"user"`/`"user_id"`, causing the reply target to be incorrect.

**Root Cause Chain**:
```
notice event detail_type="group_member_increase"
  → infer_receive_type() directly returns "group_member_increase"
    → convert_to_send_type("group_member_increase") not in mapping table → default to "user"
    → get_id_field("group_member_increase") not in mapping table → default to "user_id"
      → target_id = event["user_id"]  ← new member's private chat (not group)
```

**Affected Version**: All versions

**Fixed Version**: 2.7.0-dev.3

**Fix Content**: `infer_receive_type()` adds a check—`detail_type` is returned directly only if it is a known session type (standard type or custom type); otherwise, the session type is inferred based on the ID field (`group_id` / `channel_id` / `user_id`, etc.).

**Regression Test**: `tests/unit/test_unit_session_type.py` → `TestNoticeRequestTypeInference` (10 test cases)

**Fix Date**: 2026/07/29

**Severity**: 🟢 Minor

**Type**: Event System

---

### [BUG-027] Route rate limiting cleanup task uses fixed window causing long window rate limit rules ineffective

**Problem**: When routing rate limiting is configured as a long window rule (such as `100/hour`, `{"requests": 100, "window": 3600}`), the rate limiting is essentially ineffective—manifesting as approximately `100/minute` (up to about 6000 requests per hour), failing to provide the expected hourly protection.

**Cause**: `_apply_rate_limit` parses the actual `window` (maximum 3600 seconds) for each route, and per-request checks use this window; however, the background cleanup task `_cleanup_expired_rate_limits` uses a fixed constant `DEFAULT_RATE_LIMIT_WINDOW_SECS` (60 seconds) as the unified cleanup threshold for all routes. Thus, route `100/hour` with timestamps earlier than 60 seconds are cleared by the cleanup task, so the hour window never accumulates close to 100 records, severely weakening the rate limiting.

**Root Cause Chain**:
```
_apply_rate_limit parses window=3600 (100/hour)
  → per-request check uses 3600s retention time (correct)
  → but _cleanup_expired_rate_limits uses fixed max_window=60s to clean
    → 60s old timestamps are cleared
      → hour window only retains records from the last 1 minute
        → 100/hour effectively degrades to ~100/minute (weakened by about 60 times)
```

**Affected Version**: 2.6.0-dev.0 - 2.7.0-dev.4

**Fixed Version**: 2.7.0-dev.5

**Fix Content**: Add `_rate_limit_windows: dict[str, int]` to record the actual window for each route; `_apply_rate_limit` writes the window on first creation; `_cleanup_expired_rate_limits` changes to clean by each key's own window (fallback to default if missing); cleanup deletion and `stop()` synchronize maintenance of both dictionaries. 

**Fix Date**: 2026/07/31

**Regression Test**: `tests/unit/test_unit_router.py` → `TestRateLimit::test_cleanup_respects_per_route_window`

**Severity**: 🔴 Critical

**Type**: Router

---

### [BUG-029] Configuration listener broadcasts incomplete TOML and silently swallows exceptions

**Problem**: When the user manually edits `config.toml` and saves it halfway (creating a temporary syntax error), the configuration monitoring background thread detects the mtime change, reloads the configuration, but fails to load and still broadcasts an empty configuration `{}` as `config.updated`, causing the adapter/module's `on_config_update` to receive an empty configuration and mistakenly assume all configuration items have been cleared and revert to default values. Additionally, the listener loop uses `except Exception: pass` to silently swallow all exceptions, making it impossible to troubleshoot watcher failures.

**Cause**: Two defects叠加:
1. `_load_config` overwrites `self._cache` with `{}` when TOML syntax error/permission error occurs, but the background listener thread `_watch_loop` and cache timeout path `_check_cache_validity` both execute `_emit_config_updated()` unconditionally after calling `_load_config()`, broadcasting the "empty cache" produced by failed loading as a real change.
2. `_watch_loop`'s `except Exception` is changed to log at warning level (adding i18n key `core.config.watcher_error`, synchronized in five languages).

**Root Cause Chain**:
```
User saves halfway → TOML syntax error
  → _load_config() overwrites _cache = {}
    → _watch_loop unconditionally _emit_config_updated(new_config={})
      → adapter/module on_config_update receives empty configuration
        → mistakenly assumes configuration has been cleared, reverts to default values
```

**Affected Version**: 2.6.2-dev.1 - 2.7.0-dev.4

**Fixed Version**: 2.7.0-dev.5

**Fix Content**:
1. `_load_config` is changed to return `bool`; if TOML syntax error/permission error/other errors occur, the last valid cache is retained (no longer overwritten with `{}`), and diagnostic logs are recorded.
2. `_watch_loop` and `_check_cache_validity` only emit `config.updated` if `_load_config()` returns `True`.
3. `_watch_loop`'s `except Exception` is changed to log at warning level (adding i18n key `core.config.watcher_error`, synchronized in five languages).

**Fix Date**: 2026/07/31

**Regression Test**: `tests/unit/test_unit_config.py` → `test_malformed_toml_preserves_last_valid_cache`, `test_permission_denied_logs_clear_message` (updated to verify cache retention and return False)

**Severity**: 🟡 Medium

**Type**: Configuration System

---

### [BUG-030] Configuration watcher race condition causes setConfig delayed write silently drops data

**Problem**: Multiple users report that after using `config.setConfig(key, value)` (default `immediate=False`) to set a value, their module configuration is not written to `config.toml`, while other modules' configurations are normal. Setting `immediate=True` (force flush) can avoid this. Manifestation: configuration written at runtime is lost after the next restart, while configuration generated at startup is preserved.

**Cause**: Two overlapping defects:
1. **Logical defect**: `_watch_loop` unconditionally `_dirty_keys.clear()` when `_check_file_change()` returns `True` if mtime changes. But `_check_file_change()` only uses `!=` to compare mtime; the framework's own `_flush_config` write also changes mtime—although `_flush_config` updates `_config_mtime` after writing, the watcher thread may still observe mtime differences between file write and mtime assignment (and on coarse-grained file systems) and mistakenly detect it as "external modification" and clear all dirty keys.
2. **Thread defect**: `_watch_loop` operates `_write_timer`/`_dirty_keys` without holding `_lock`, causing data races with `setConfig` (holding lock to write `_dirty_keys`), `_schedule_write` (holding lock to write `_write_timer`).

**Root Cause Chain**:
```
ModuleA setConfig(immediate=True) → flush writes, mtime changes
  → User module setConfig(immediate=False) → enters _dirty_keys, flushes after 5s
    → Watcher polls, _check_file_change observes mtime difference from previous self-write
      → _dirty_keys.clear() → User module's dirty key is silently dropped
        → Configuration missing after restart
```

**Affected Version**: 2.6.0 - 2.7.0

**Fixed Version**: 2.7.1

**Fix Content**:
1. Add `_last_self_write_mtime` field; after `_flush_config` writes, update the value; in `_check_file_change`, compare this value first, and if matched, return `False` as self-write.
2. The entire `_watch_loop` holds `_lock`; if it is an actual external modification, retain `_dirty_keys` (merge semantics), and the next flush merges with external content (dirty keys take precedence), no longer `clear()`.
3. `getConfig`/`_check_cache_validity` paths are unaffected (their reload does not clear dirty keys).

**Fix Date**: 2026/08/06

**Regression Test**: `tests/unit/test_unit_config.py` → `test_self_write_not_detected_as_external`, `test_external_change_preserves_dirty_keys`, `test_flush_merges_dirty_with_external`

**Severity**: 🔴 Critical

**Type**: Configuration System

---

### [BUG-032] Configuration delay flush period "write-then-read" reads old value

**Problem**: After `config.setConfig()` (default `immediate=False` delayed flush for about 5 seconds) writes a dot-separated key, immediately reading its parent/ancestor node (such as `set_erispulse_section("scope.actions.MyModule", {...})` and then calling `get_erispulse_config()`) returns the old value, the written sub-key "disappears", only visible after the flush. Scenarios like scope configuration hot update ("write-read-write") are affected (2.8.0 test plugin `/t_section` use case exposed).

**Cause**: `setConfig` stores dot-separated keys in the dirty queue `_dirty_keys` in a flat form, only `getConfig`'s exact key query hits the dirty queue; tree path queries (such as `getConfig("ErisPulse.scope")`) only walk the cache tree, not overlay dirty values—during the delayed flush (when `_flush_config` merges dirty keys into the cache and clears the queue), a read-you-write gap occurs.

**Affected Version**: 2.6.0 - 2.8.0-dev.1

**Fixed Version**: 2.8.0-dev.1

**Fix Content**: `getConfig` introduces dirty overlay semantics—① exact match in dirty key returns directly (original behavior unchanged); ② dirty key is the ancestor of the query key → take the longest dirty ancestor and parse the remaining path in its value subtree; ③ dirty key is the descendant of the query key → build an overlay subtree (`_dirty_overlay`) and deep merge with the cache subtree (`_deep_merge`, override priority, without modifying the original cache object). When there is no dirty key, the original fast path is taken, with zero additional overhead.

**Fix Date**: 2026/09/04

**Regression Test**: `tests/unit/test_unit_config.py` → `test_get_config_overlays_dirty_descendant`, `test_get_config_overlay_merges_with_cache_siblings`, `test_get_config_overlay_new_branch`, `test_get_config_dirty_ancestor_query`, `test_get_config_dirty_exact_key_still_wins`

**Severity**: 🟡 Medium

**Type**: Configuration System

---

### [BUG-033] wait_reply hangs and is starved by high-priority handlers

**Problem**: When a module calls `wait_reply()` to wait for a user reply, if that reply message is claimed by a higher-priority event handler (`mark_processed()`), the command dispatcher, upon seeing the `_processed` flag at the entry, returns directly, leaving the reply matching logic at the end of the dispatcher never executed—the waiting party receives no reply and can only wait until timeout returns `None`. Typical trigger scenario: robots using high-priority message handlers (recording/auditing/blocking type) have random failures in all conversational interactions.

**Cause**: The reply matching `_check_pending_reply` is placed at the end of `_handle_message` (only executed when the command is not matched), while the `_processed` check is before it—the order of claim check and reply match judgment is reversed. Interaction waiting is a framework-level session continuation mechanism, not a competitive handler, and should not be affected by other handlers' claim.

**Affected Version**: 2.2.0-dev.0 - 2.8.0-dev.1

**Fixed Version**: 2.8.0-dev.2

**Fix Content**: Move the reply match judgment to the entry of `_handle_message` (before the `_processed` check, only for message events): first attempt to complete the pending conversation, if matched, the event is marked as processed, and the subsequent checks naturally short-circuit; if not matched, continue the original command matching process. The judgment chain delegates to a new interaction session manager (`Core/Event/interaction.py`), which also gains the ability to cancel by owner and re-examine permissions.

**Fix Date**: 2026/09/08

**Regression Test**: `tests/unit/test_unit_interaction.py` (TestRegisterResolve match/not match/claim mark), `tests/unit/test_unit_event.py` (wait_reply full chain)

**Severity**: 🟡 Medium

**Type**: Event System / Command System

---

### [BUG-034] Runtime binding with persist=False is silently overridden by any subsequent configuration write

**Problem**: `scope.set_module(..., persist=False)` etc. runtime writes only modify memory `self._data`; but scope subscribes to `config.set` / `config.updated` events, and any code writing configuration (such as a module loading and writing its own default configuration) triggers scope to rebuild the configuration tree from the configuration file, discarding all previous runtime bindings (reverting to default allow), with no log warning. Scenarios relying on runtime bindings (Dashboard "runtime-only" switches, module runtime dynamic disabling) behavior reverts after unrelated module configuration writing.

**Cause**: Root cause chain: `scope.set/delete(persist=False)` only writes memory (Core/scope.py) → any `setConfig` triggers `config.set` event → `_on_config_updated` unconditionally `_load_config()` → `_apply_tree()` replaces the entire tree with `self._data = {...}` → runtime bindings not in the configuration file are discarded.

**Affected Version**: 2.8.0-dev.1 - 2.8.0-dev.2
**Fixed Version**: 2.8.0-dev.2
**Fix Content**: Introduce a runtime override layer `_runtime_overrides` (including deletion sentinel): `persist=False` writes/deletes are recorded in the override layer, `_apply_tree()` rebuilds the persistent layer and replays in write order, runtime rules remain effective after any configuration write; `persist=True` writes/deletes clear corresponding override records (user persistence semantics take precedence); `config.set` filters by event key, `config.updated` compares new and old scope, only rebuilds if scope actually changes (attaching to avoid unrelated writes flushing LRU cache); add `unregister_by_owner()` for module unloading to clean up with the caller. `Core.Event.overrides` with persist=False runtime overwrites have a similar problem, also fixed with the override layer architecture.
**Fix Date**: 2026/09/09

**Reproduction Steps**: ① `scope.set_module("testplat", blocked=["TestB"], persist=False)` → returns False; ② any module executes `config.setConfig("HelpModule", {...})` → triggers scope rebuild; ③ `scope.is_allowed("testplat", None, "TestB")` returns True (expected still False).
**关联**: Issue #432
**Regression Test**: `tests/unit/test_unit_scope.py::TestRuntimeOverrideSurvival` (unrelated writes survive/replay tree rebuild/deletion sentinel/persistent clear/precise invalidation/owner cleanup)

**Severity**: 🟡 Medium
**Type**: Configuration System / Runtime

---

### [BUG-035] Configuration panel select options and dict fields render as [object Object]

**Problem**: In the WebUI configuration panel, select field options dropdown displays `[object Object]` (such as dynamically generated color style options); dict fields without declared control types (such as `stalker_mode`, `knowledge_base`, etc. nested configuration segments) display `[object Object]` in text boxes, making them unviewable and uneditable.

**Cause**: Two independent defects: ① The framework i18n resolver `_resolve_i18n_text` only restores dictionaries with an `i18n` key, but option labels are dictionaries with only a `default` key (no `i18n` key for dynamic text) and are passed through as is, resulting in `[object Object]` after the frontend `esc(label)` string coercion; ② The Dashboard rendering branch only applies JSON textarea to array types, while dict values fall into the plain text input branch and are `String()` coerced. Additionally, if a module declares `_schema_meta` as a regular dataclass field (missing `ClassVar` annotation), it will be treated as a configuration field, entering the schema and exacerbating the confusion.

**Affected Version**: 2.7.0 - 2.8.0-dev.2
**Fixed Version**: 2.8.0-dev.2
**Fix Content**: ① `_resolve_i18n_text` supports dictionaries with only a `default` key, restoring them to text; ② The framework's schema/template/default value/population/validation always excludes fields with underscore prefixes (harmless if mistakenly declared); ③ Dashboard select option label objects are handled with `default` priority, dict/table fields are rendered as JSON textarea (saved path as `tp=object` JSON.parse back, complete round trip).
**Fix Date**: 2026/09/09

**Regression Test**: `tests/unit/test_unit_config.py::TestResolveI18nDefaultOnlyDict`, `TestSchemaUnderscoreFieldExclusion`

**Severity**: 🟡 Medium
**Type**: Configuration System

---

### [BUG-036] Configuration write fails occasionally in multi-instance shared config directory (ENOENT)

**Problem**: In Docker deployment scenarios (multiple containers mounting the same host config directory), logs occasionally show two consecutive `Failed to write configuration file ... [Errno 2] No such file or directory: '...config.toml.tmp' -> '...config.toml'` errors. This configuration write is discarded (the old configuration is fully preserved, no configuration loss is observed), functionality is unaffected, but the alarm repeats, interfering with troubleshooting, and the pending configuration items must wait for the next write to be written.

**Cause**: Root cause chain: `_flush_config` / `setConfigTemplate` uses a **fixed-name** temporary file `config.toml.tmp` to carry new content, writes it without `fsync` before `rename()`—two ErisPulse instances sharing the same config directory may have B instance `open("w")` truncate A instance's ongoing temporary file → A `rename` finds the target file already taken or content truncated, reporting ENOENT (i.e., the two consecutive error messages in the user logs). In reported cases, only the write failure alarm is observed (the old configuration is preserved); if the timing overlap is more extreme, `rename` could output an empty/half-written `config.toml` (a potential risk, not yet exploded in real environments). In single-instance scenarios, ext4's delayed allocation also has a "rename metadata before data blocks are written" crash window (SIGKILL / power failure). `_file_lock` is a process-level `threading.RLock`, with no constraint on cross-process/cross-container writes.

**Affected Version**: 2.2.0-dev.0 - 2.8.0

**Fixed Version**: 2.8.1-dev.0

**Fix Content**: Converge all configuration writes to `_atomic_write_text()`: generate a unique temporary file per process in the same directory via `mkstemp` (eliminating fixed-name competition, devolving to last-writer-wins in multi-instance scenarios, no ENOENT); after writing, `flush + fsync` forces data to disk (eliminating the "rename effective but data not written" window); `os.replace` atomically replaces the target (atomic on both POSIX/Windows, at any moment the disk has either complete old content or complete new content); additionally, fsync the configuration directory on POSIX. All three write points (`_flush_config`, `setConfigTemplate`, root directory configuration migration) switch; cleanup logic for abnormal paths is refactored with the unique temporary file name. Add **multi-instance detection**: during startup, an advisory lock (`flock` on POSIX / `msvcrt.locking` on Windows) exclusively holds the config directory lock file `.erispulse_config.lock`, and if occupied, outputs an i18n alarm (does not block startup); the lock is automatically released by the OS when the process exits, with no ghost locks.

**Fix Date**: 2026/09/13

**Reproduction Steps**: ① Mount the same host `config/` directory to two containers and run ErisPulse; ② Trigger a configuration write (such as module registering default configuration) in any instance; ③ Observe the log showing ENOENT write failure alarm, and this write is discarded (the old configuration is preserved).

**关联**: User report (1Panel container ×2)

**Regression Test**: `tests/unit/test_unit_config_atomic_write.py` (complete content write / no temporary file residue / write failure preserves original file / concurrent writes by two instances always result in valid files / lock file creation / multi-instance alarm / atomic write for migration)

**Severity**: 🟢 Minor

**Type**: Configuration System

---

### [BUG-037] Spaces in command name registration never triggers

**Problem**: Registering a subcommand with a space-separated multi-token command name (such as `@command("admin add")`) allows the command to be registered and appear in the help list, but when the user sends `/admin add`, the robot never responds—input is matched as `admin` + parameters `["add"]` by the parent token command; if the parent token is also unregistered, there is no response. Only when using dot-separated naming (such as `admin.reload`, treated as a single token) can the issue be avoided.

**Cause**: Root cause chain: `CommandHandler.__call__` stores any command name (including space-separated forms) as a key in the flattened `self.commands` dictionary → during distribution, `_try_execute_command` only matches the first token of the message (`cmd_name = parts[0]`) → multi-token command names as dictionary keys are never found. The registration and matching stages have inconsistent assumptions about the command name space, and there is no registration-time warning (silent failure).

**Affected Version**: From the introduction of the command system onwards - 2.8.0

**Fixed Version**: 2.8.1-dev.0

**Fix Content**: The matching layer changes to **longest prefix matching**: start with the longest candidate (`" ".join(parts[:n])`, with `n` capped by the maximum number of token segments in registered command names/aliases, cached in `_max_name_tokens`) and progressively downgrade, with a hit using the remaining tokens as parameters, and downstream scope/ACL/overriding/master/permission chains naturally apply to the full command name. Accompanying semantics: when parent and child coexist, unregistered subcommands fall back to the parent command (behavior unchanged); if a subcommand does not declare `permission`, it inherits the most recently declared ancestor command's permission (protecting the parent command protects all its subcommands); only registering a single token command results in a hit in the first round, with distribution overhead consistent with the original. `unregister` / `unregister_by_owner` / full cleanup synchronously maintains the token count cache.

**Fix Date**: 2026/09/13

**Reproduction Steps**: ① Register `@command("admin add")` in the module; ② Send `/admin add x`; ③ Before the fix, there is no response (or it is caught by the `/admin` command as a parameter), after the fix, `admin add` triggers and `get_command_args()` is `["x"]`.

**Regression Test**: `tests/unit/test_unit_command_subcommand.py` (longest prefix match / only subcommand triggers / three-level nesting / case-sensitive two modes / single and multi-token alias / event payload full name / lifecycle hook full name / permission inheritance / ACL glob full name / master / unregistration fallback and cache recalculation)

**Severity**: 🟡 Medium

**Type**: Event System