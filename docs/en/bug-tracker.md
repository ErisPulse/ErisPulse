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
|----------|-------|
| 🔴 Critical | 16 |
| 🟡 Medium | 16 |
| 🟢 Low | 3 |
| **Total** | **35** |

| Type | Count |
|------|-------|
| Adapters | 6 |
| Configuration System | 10 |
| Event System | 6 |
| CLI | 3 |
| Storage | 3 |
| Loader System | 3 |
| Routing | 2 |
| Client | 1 |
| Runtime | 1 |

> Note: A single bug can belong to multiple types; the table above is counted by primary type.

---

## Fixed Bugs

### [BUG-001] Event handler registered multiple times causing event to be processed multiple times

**Issue**: When registering handlers using multiple `@message` / `@notice` decorators, the same event is triggered multiple times, causing commands to execute multiple times and logs to be output repeatedly.

**Cause**: `BaseEventHandler` lacks deduplication logic when registering handlers with the adapter event bus. Each decorator mounts a handler to the bus, causing the event to be called multiple times during dispatch.

**Affected Versions**: 2.2.0-dev.0 - 2.2.1-dev.0

**Fixed Version**: 2.2.1-dev.0

**Fix**: Optimized `BaseEventHandler` to ensure each event type is registered only once with the adapter, avoiding repeated triggers.

**Fix Date**: 2025/08/18

**Severity**: 🔴 Critical

**Type**: Event System

---

### [BUG-002] Init command adapter configuration path type error

**Issue**: When using the `ep init` command for interactive initialization, selecting a configuration adapter results in a type error:

```
Interactive initialization failed: unsupported operand type(s) for /: 'str' and 'str'
```

**Cause**: During configuration file path adjustment in version 2.3.7, method parameter types were inconsistent. `_configure_adapters_interactive_sync` receives a `str` type parameter but internally uses the `Path` `/` operator to concatenate paths.

**Affected Versions**: 2.3.7 - 2.3.9-dev.1

**Fixed Version**: 2.3.9-dev.1

**Fix**: Changed the parameter type of `_configure_adapters_interactive_sync` from `str` to `Path`, passing `Path` objects directly during calls.

**Fix Date**: 2026/03/23

**Severity**: 🟡 Medium

**Type**: CLI

---

### [BUG-003] Commands fail after restart

**Issue**: After calling `sdk.restart()`, commands registered via `@command` are not triggered, resulting in the robot not responding after sending a command.

**Cause**: `adapter.shutdown()` clears the event bus, but `BaseEventHandler`'s `_linked_to_adapter_bus` status is not reset to `False`, causing `_process_event` to believe it is already linked to the adapter bus and skip re-linking.

**Affected Versions**: 2.2.x - 2.4.0-dev.2

**Fixed Version**: 2.4.0-dev.3

**Fix**: Introduced `_linked_to_adapter_bus` status tracking. After `_clear_handlers()` disconnects the bus, `register()` automatically re-links next time, adapting to shutdown/restart scenarios.

**Fix Date**: 2026/04/09

**Severity**: 🔴 Critical

**Type**: Event System

---

### [BUG-004] Lifecycle event handler not cleaned up

**Issue**: After `sdk.restart()`, old lifecycle event handlers remain and trigger repeatedly, causing the same event to be processed multiple times.

**Cause**: The `lifecycle._handlers` dictionary is never cleared in `uninit()`, leaving old and new handlers both active after restart.

**Affected Versions**: 2.3.0 - 2.4.0-dev.2

**Fixed Version**: 2.4.0-dev.3

**Fix**: Clear `lifecycle._handlers` at the end of the `Uninitializer` cleanup process (after all events are submitted).

**Fix Date**: 2026/04/09

**Severity**: 🟡 Medium

**Type**: Runtime

---

### [BUG-005] Event.is_friend_add/is_friend_delete detail_type inconsistent with OB12 standard

**Issue**: `Event.is_friend_add()` checks `detail_type == "friend_add"`, `Event.is_friend_delete()` checks `detail_type == "friend_delete"`, but OneBot12 standard defines `detail_type` values as `"friend_increase"` and `"friend_decrease"`. This inconsistency with `notice.py`'s `on_friend_add`/`on_friend_remove` decorators causes handlers registered via decorators to trigger, but corresponding `is_friend_add()`/`is_friend_delete()` methods return `False`.

**Cause**: `wrapper.py` uses non-standard naming, while `notice.py` uses correct OB12 standard naming.

**Affected Versions**: Since implementation

**Fixed Version**: 2.4.2-dev.1

**Fix**: Changed `is_friend_add()`'s matching value from `"friend_add"` to `"friend_increase"`, and `is_friend_delete()` from `"friend_delete"` to `"friend_decrease"`.

**Fix Date**: 2026/04/13

**Severity**: 🟡 Medium

**Type**: Event System

---

### [BUG-006] adapter.clear() does not clean _started_instances causing incorrect state after restart

**Issue**: `AdapterManager.clear()` clears `_adapters`, `_adapter_info`, handlers, and `_bots`, but omits `_started_instances`. If `clear()` is called while the adapter is running, `_started_instances` retains dangling references, leading to incorrect state after restart.

**Cause**: When `_started_instances` was introduced in 2.4.0-dev.1, it was not cleared in `clear()`.

**Affected Versions**: 2.4.0-dev.1 - 2.4.2-dev.0

**Fixed Version**: 2.4.2-dev.1

**Fix**: Added `self._started_instances.clear()` to the `clear()` method.

**Fix Date**: 2026/04/13

**Severity**: 🟡 Medium

**Type**: Adapter

---

### [BUG-007] command.wait_reply() uses deprecated asyncio.get_event_loop()

**Issue**: The `CommandHandler.wait_reply()` method uses `asyncio.get_event_loop()` to create futures and get timestamps, which is deprecated in Python 3.10+. In asynchronous contexts, `asyncio.get_running_loop()` should be used. This is inconsistent with `wrapper.py`'s `wait_for()` method in the same file, which uses `get_running_loop()`.

**Cause**: The development used an old API, and the newly added `wait_for()` used the correct API but did not retroactively fix the old code.

**Affected Versions**: 2.3.0-dev.0

**Fixed Version**: 2.4.2-dev.1

**Fix**: Replaced two instances of `asyncio.get_event_loop()` in `command.py` with `asyncio.get_running_loop()`.

**Fix Date**: 2026/04/13

**Severity**: 🟢 Minor

**Type**: Event System

---

### [BUG-008] Bot offline event submitted repeatedly during shutdown

**Issue**: When calling `adapter.shutdown()` to close all adapters, `_update_bot_status()` repeatedly submits Bot offline events during the shutdown process, causing the same batch of Bots to be marked offline multiple times and triggering multiple `adapter.bot.offline` lifecycle events.

**Cause**: The Bot status tracking system introduced in 2.4.0-dev.1 did not set a "shutting down" flag during `shutdown()`. `_update_bot_status()` could not distinguish between normal offline and cascading offline during shutdown.

**Affected Versions**: 2.4.0-dev.1 - 2.4.2-dev.1

**Fixed Version**: 2.4.2-dev.1

**Fix**: Added `_is_being_shutdown` flag in `AdapterManager`. Set to True at the start of `shutdown()` and cleared at the end; `_update_bot_status()` skips repeated submissions during shutdown based on this flag.

**Fix Date**: 2026/04/21

**Severity**: 🟡 Medium

**Type**: Adapter

---

### [BUG-009] LazyModule synchronously accessing BaseModule causes incomplete initialization

**Issue**: When users access lazy-loaded BaseModule attributes in synchronous contexts, the module uses `loop.create_task()` for asynchronous initialization but does not await it, leading to race conditions when attributes are accessed before initialization completes.

**Cause**: `_ensure_initialized()` for BaseModule uses `loop.create_task(self._initialize())` and returns immediately without ensuring initialization completes.

**Affected Versions**: 2.4.0-dev.0 - 2.4.2-dev.1

**Fixed Version**: 2.4.2-dev.2

**Fix**: In synchronous contexts, BaseModule's initialization is changed to use `asyncio.run(self._initialize())` to ensure initialization completes before returning. The transparent proxy feature is maintained, so users do not need to be aware of synchronous/asynchronous differences.

**Fix Date**: 2026/04/21

**Severity**: 🟡 Medium

**Type**: Loading System

---

### [BUG-010] Multi-threaded configuration system write causes data loss

**Issue**: In multi-threaded environments, when multiple threads call `config.setConfig()` simultaneously, the `_flush_config()` read-modify-write operation is not atomic, potentially causing partial writes to be lost.

**Cause**: Although `_flush_config()` uses `RLock`, there is no file lock protection between file read and write, and `_schedule_write`'s Timer may be triggered multiple times, causing overwrites.

**Affected Versions**: 2.3.0 - 2.4.2-dev.1

**Fixed Version**: 2.4.2-dev.2

**Fix**:
1. Added file locking mechanism (`_file_lock`) to ensure atomic file operations
2. Used temporary files for writing and then atomically renamed (`os.replace`/`os.rename`)
3. Improved `_schedule_write`'s Timer cancellation and rescheduling logic

**Fix Date**: 2026/04/21

**Severity**: 🔴 Critical

**Type**: Configuration System

---

### [BUG-011] Windows Ctrl+C cannot stop the program

**Issue**: When running `python main.py` directly on Windows, pressing Ctrl+C does not terminate the program. After the program starts normally and outputs the router server information, Ctrl+C has no response and can only be forcefully killed via the task manager. However, it can be stopped normally when started via `epsdk run`—but `epsdk run` uses a subprocess model.

**Cause**: The Hypercorn ASGI server's `serve()` function internally registers its own SIGINT handler via `signal.signal(SIGINT, handler)`, overriding Python's default `KeyboardInterrupt` handling mechanism. When Hypercorn is started as a background task via `asyncio.create_task()`, its internal shutdown process cannot be triggered normally (as it expects `worker_serve` mode), causing Ctrl+C signals to be swallowed by Hypercorn but not triggering any cleanup actions.

**Affected Versions**: 2.3.6 - 2.4.2

**Fixed Version**: 2.4.3-dev.0

**Fix**:
1. Switched ASGI server from Hypercorn to Uvicorn (`pyproject.toml` dependency change)
2. Used `uvicorn.Server._serve()` to start the server directly, **bypassing** the `capture_signals()` signal handling context manager
3. Achieved graceful shutdown via `server.should_exit = True`, canceling background tasks on timeout
4. Synchronized removal of subprocess running model and `runtime/cleanup.py` cleanup module (no longer needed)

**Fix Date**: 2026/04/28

**Severity**: 🔴 Critical

**Type**: CLI / Runtime

---

### [BUG-012] Updated module Python code not effective after hot restart

**Issue**: After executing `sdk.restart()` soft restart, the new code (such as added API routes) of modules/adapters upgraded via `epsdk install` is not effective, and old logic is still running. A complete process restart is required to load the latest code.

**Cause**: `_do_restart()` calls `entry_point.load()` during re-initialization, but this function returns cached old module objects from `sys.modules` instead of reloading from disk.

**Affected Versions**: Early versions - 2.4.3-dev.1

**Fixed Version**: 2.4.3-dev.1

**Fix**: Clear cached loaded modules/adapters from `sys.modules` after `uninit()` and before `init()` to ensure `entry_point.load()` loads the latest code from disk. Added `_collect_top_level_modules()` and `_invalidate_module_cache()` helper methods to deduce top-level module names via `top_level.txt` or entry-point value.

**Fix Date**: 2026/05/03

**Severity**: 🔴 Critical

**Type**: Loading System / Runtime

---

### [BUG-013] Module loading strategy sorting logic error

**Issue**: `ModuleLoadStrategy` provides a `priority` field to declare module initialization priority, but the implementation has a flaw, causing modules not to be initialized in the expected priority order. Instead, they are initialized in the default order of `entry_points()`. When modules have initialization dependencies, `priority` cannot ensure the correct initialization order.

**Cause**: The implementation of the loading strategy has a sorting logic error; `initialize_modules()` does not use `priority` to sort the module list.

**Affected Versions**: 2.3.4 - 2.4.5-dev.2

**Fixed Version**: 2.4.5-dev.3

**Fix**: Before the `initialize_modules()` traversal, sort the module list by `priority` in descending order. Modules with the same priority maintain their original relative order (stable sorting).

**Fix Date**: 2026/05/15

**Severity**: 🟡 Medium

**Type**: Loading System

---

### [BUG-014] Adapter middleware returning None causes event data loss

**Issue**: When executing the OneBot12 middleware chain in `adapter.emit()`, if a middleware returns `None` (e.g., forgetting `return data`), subsequent middlewares and all event handlers receive `processed_data` as `None`, causing event processing to fail completely.

**Cause**: The middleware chain implementation `processed_data = await middleware(processed_data)` does not check if the return value is `None`, directly overwriting the previous processing result.

**Affected Versions**: unknown - 2.4.5-dev.3

**Fixed Version**: 2.4.5-dev.4

**Fix**: When middleware returns `None`, ignore the return value, retain the original data, and output a warning-level log.

**Fix Date**: 2026/05/15

**Severity**: 🔴 Critical

**Type**: Adapter / Event System

---

### [BUG-015] Configuration file path depends on working directory

**Issue**: `ConfigManager`'s configuration file path defaults to the relative path `"config/config.toml"`, which is resolved at runtime using `os.getcwd()`. If the working directory changes during runtime (e.g., via `os.chdir()`), file read/write operations point to the wrong location, causing configuration loss or reading old data.

**Cause**: In `__init__`, the relative path is directly stored without being resolved to an absolute path at initialization.

**Affected Versions**: 2.3.7 - 2.4.5-dev.3

**Fixed Version**: 2.4.5-dev.4

**Fix**: In `ConfigManager.__init__()`, if the passed path is relative, automatically resolve it to an absolute path using `os.path.abspath()`.

**Fix Date**: 2026/05/15

**Severity**: 🟡 Medium

**Type**: Configuration System

---

### [BUG-016] BaseStorage confuses storing value None with non-existent key

**Issue**: `BaseStorage.get_multi()` / `__getattr__()` cannot distinguish between "key does not exist" and "key's value is None", treating a user explicitly stored `None` as if the key does not exist.

**Cause**: The value retrieval logic directly uses `value is None` to check if the key exists, lacking an independent "missing" marker.

**Affected Versions**: Early versions - 2.4.6-dev.6

**Fixed Version**: 2.4.6-dev.6

**Fix**: Introduced `_SENTINEL` sentinel value to distinguish "key does not exist" from "value is None", eliminating confusion between the two.

**Fix Date**: 2026/06/07

**Severity**: 🟡 Medium

**Type**: Storage

---

### [BUG-017] WebSocket route auto_accept flag lost after service restart

**Issue**: After a service restart (such as `sdk.restart()`), all WebSocket routes' `auto_accept` configuration revert to `False`. Routes that originally expected automatic acceptance become suspended, and clients do not receive responses for a long time, resulting in WS connections hanging.

**Cause**: `_restore_routes_from_records()` hardcodes `auto_accept` to `False` when restoring routes from persistent records, not reading the original record's value. Also, when the route storage tuple expanded from a binary to a ternary tuple, the restoration logic was not synchronized.

**Affected Versions**: 2.3.8-dev.0 - 2.4.6-dev.6

**Fixed Version**: 2.4.6-dev.6

**Fix**: Route storage tuples expanded to `(handler, auth_handler, auto_accept)`, and `_restore_routes_from_records()` reads the true `auto_accept` value from the record instead of hardcoding `False`.

**Fix Date**: 2026/06/07

**Severity**: 🔴 Critical

**Type**: Routing

---

### [BUG-018] HTTP/WS client concurrent calls cause crashes and connection leaks

**Issue**: `Core/client.py`'s HTTP and WebSocket clients have multiple stability defects in concurrent scenarios, leading to connection leaks or process crashes:
- Concurrent calls to `ClientWebSocket.receive()` by multiple coroutines cause aiohttp to throw `Concurrent call to receive() is not allowed`
- Concurrent calls to `_get_http_session()` / `_get_ws_session()` may create multiple sessions, and `_drain_sessions()` does not close old connections, causing connection leaks
- `request()`'s exception handling order is incorrect: `except ClientConnectionError` (ErisPulse exception) never triggers, aiohttp connection errors are caught by generic `except Exception`, causing "connection retry + session rebuild" logic (dead code) never executed
- `send_json()` ignores `mode="binary"` parameter; `_get_ws_session()` does not pass default request headers

**Cause**: The client's initial implementation (2.4.6-dev.5) lacked concurrency protection and exception classification, improperly handling aiohttp exception hierarchy and ErisPulse custom exception inheritance.

**Affected Versions**: 2.4.6-dev.5 - 2.4.8

**Fixed Version**: 2.4.8

**Fix**:
1. Added `_recv_lock` to serialize all `receive()` / `receive_text()` / `receive_bytes()` calls
2. Added `_session_lock` to protect session creation; `_drain_sessions()` changed to an async method and truly closes old sessions
3. Reconstructed `request()` exception handling order: `asyncio.TimeoutError` → `aiohttp.ClientConnectionError` (triggers session rebuild) → `aiohttp.ClientError` → `ClientError` (transparent pass) → `Exception`
4. Fixed `send_json()`'s mode handling, `_get_ws_session()` default request header passing, `close()` concurrency race, and `HttpResponse.__aexit__` duplicate `release()`

**Fix Date**: 2026/06/12

**Severity**: 🔴 Critical

**Type**: Client

---

### [BUG-019] Adapter hot reload causes route conflicts and reload failure

**Issue**: When third-party modules (such as Dashboard) trigger adapter hot reload, or when adapter startup fails and retries, old routes (such as `onebot11_default`) are not cleared, throwing a `WebSocket path ... already registered` conflict, causing reload failure. A complete process restart is required to recover.

**Cause**: `AdapterManager.shutdown()` only clears routes via `unregister_all_by_namespace(platform)`, but adapters (such as OneBot11) register WebSocket routes using `onebot11_{account_name}` as the namespace, resulting in a granularity mismatch and an empty operation; startup failure retry paths are also not cleared of previous residual routes.

**Affected Versions**: Early versions - 2.4.9

**Fixed Version**: 2.4.9

**Fix**:
1. Automatically track `owner → namespace` relationships during route registration via `current_owner` ContextVar
2. Added `unregister_all_by_owner(owner)`, cleaning up by owner during stop/restart, covering fine-grained namespaces
3. Added `_stop_adapter(platform)` primitive ("stop equals cleanup"), binding stopping the adapter and reclaiming its registered resources in a single call, accessed by `restart()` and startup failure retries
4. Added framework-level `adapter.restart(platform)` API, third-party modules should call this method instead of directly operating adapter instances

**Fix Date**: 2026/06/12

**Severity**: 🔴 Critical

**Type**: Adapter / Routing

---

### [BUG-020] Subprocess mode `ep run <script>` cannot find subpackages in script's directory

**Issue**: When running a script using `ep r .\main.py` in non-hot-reload mode, if the script has relative imports (such as `from qg import ...`), it reports `No module named 'qg'`. The `--reload` mode works normally.

**Cause**: The non-hot-reload mode directly calls `runpy.run_path()` to execute the script, which does not automatically add the script's directory to `sys.path`. The `--reload` mode runs via `subprocess.Popen` subprocess, which automatically inherits the current working directory, making `sys.path[0]` the script's directory, so it works normally.

**Affected Versions**: 2.5.0 - 2.5.2-dev.0

**Fixed Version**: 2.5.2-dev.0

**Fix**: Before calling `runpy.run_path()`, manually insert the script's directory into `sys.path[0]`.

**Fix Date**: 2026/06/27

**Severity**: 🟡 Medium

**Type**: CLI

---

### [BUG-021] SQL query builder rejects valid wildcard and list expressions

**Issue**: `SQLiteQueryBuilder`'s `_build_select_sql()` validates all SELECT columns with `_validate_identifier()`, which uses a strict whitelist regex `^[a-zA-Z_][a-zA-Z0-9_]*$`, causing valid SQL syntax to be incorrectly judged as unsafe column names:
- `SELECT *` — `*` is a standard SQL wildcard
- `SELECT COUNT(*)` — aggregate function
- `SELECT users.name` — qualified column name
- `SELECT col AS alias` — column alias

Among these, `Select("*")` is used by modules like Cron, causing module `on_load` execution to fail and the module cannot be loaded.

**Cause**: In version 2.4.6, SQL injection protection was enhanced, introducing `_validate_identifier()` whitelist validation. This validation is applied to all column names but does not distinguish between read-side (SELECT/ORDER BY) and write-side (INSERT/UPDATE). SELECT columns allow complex SQL expressions and should not be restricted by simple identifier whitelists.

**Affected Versions**: 2.4.6 - 2.5.2-dev.1

**Fixed Version**: 2.5.2-dev.2

**Fix**: Changed the column validation for SELECT/ORDER BY from whitelist mode to blacklist mode:
1. Added `_validate_select_column()` function, only blocking dangerous SQL injection characters (`;` `'` `"` `--` `/*` `*/` `\x00` newline)
2. Allow any valid SQL column expression (`*`, `table.*`, `table.column`, `COUNT(*)`, `col AS alias`, etc.)
3. INSERT/UPDATE column names remain strictly validated by whitelist (only allow simple identifiers)

**Fix Date**: 2026/06/29

**Severity**: 🔴 Critical

**Type**: Storage

---

### [BUG-022] _resolve_account() account resolution regression (_accounts_data not populated)

**Issue**: After the 2.5.2 configuration system refactor, multi-account adapters declaring `AccountConfigClass` report `ValueError("未声明 AccountConfigClass，无法解析账户")` when calling methods like `wait_reply`, `reply` that require sending messages. Even if the adapter correctly configures multi-account information, account resolution still fails.

**Cause**: In 2.5.2-dev.5, `_load_accounts()` (responsible for reading configuration + validation + populating `_accounts_data`) was refactored into `_ensure_accounts_exist()` (only generating configuration templates), but `_resolve_account()` still checks `self._accounts_data is None`. Since `_ensure_accounts_exist()` no longer populates `_accounts_data`, this attribute remains `None`, causing `_resolve_account()` to prematurely return `(None, None)`, and account resolution fails completely.

**Root Cause Chain**:
```
_load_accounts() was deleted
  → __init__ no longer populates _accounts_data
    → _accounts_data is always None
      → _resolve_account() checks _accounts_data is None → return (None, None)
        → downstream places calling _resolve_account (e.g. call_api) get None
          → trigger error
```

**Affected Versions**: 2.5.2-dev.5 - 2.5.2

**Fixed Version**: 2.5.3

**Fix**: In `BaseAdapter.__init__`, after `_ensure_accounts_exist()`, restore the population of `_accounts_data`:
```python
if self.AccountConfigClass is not None:
    self._ensure_accounts_exist()
    self._accounts_data = self.accounts  # restore population, data source is real-time read accounts property
```
The `_resolve_account()` logic remains unchanged, ensuring full backward compatibility:
- Adapters not declaring `AccountConfigClass`: `_accounts_data` remains `None` → return `(None, None)`
- Adapters declaring `AccountConfigClass`: `_accounts_data` is populated → normal resolution
- Adapters overwriting `_load_accounts` or manually setting `_accounts_data`: overwrite after `super().__init__()`, highest priority

**Fix Date**: 2026/07/07

**Severity**: 🔴 Critical

**Type**: Adapter / Configuration System

---

### [BUG-023] Adapter cache not refreshed after account configuration modification causing account resolution failure

**Issue**: After users modify multi-account adapter account configurations (such as filling in token) via Dashboard, the adapter still uses old cache, and calling message-related methods reports `未找到可用账户 (account_id=default)`. A process restart is required for the new configuration to take effect.

**Cause**: `_accounts_data` is only read from configuration storage once at `BaseAdapter.__init__`, and is never refreshed afterward. `AdapterManager._run_adapter()` and `restart()` do not re-read account configuration before calling `adapter.start()`, causing cache and actual configuration to be out of sync.

**Affected Versions**: 2.4.6 - 2.5.4

**Fixed Version**: 2.5.4

**Fix**: In `AdapterManager._run_adapter()` and `restart()`, before calling `adapter.start()`, refresh `adapter._accounts_data = adapter.accounts` to ensure the latest configuration is used on each start.

**Fix Date**: 2026/07/09

**Severity**: 🔴 Critical

**Type**: Adapter / Configuration System

---

### [BUG-024] storage.set() writing large numeric ID key triggers OOM Kill

**Issue**: Calling `storage.set()` to write a nested key path containing a large numeric field (such as QQ group ID `871684833`) causes the process to be OOM killed (exit code -9), resulting in service crash and inability to recover.

**Cause**: In the recursive implementation of `_set_nested_value`, nested key paths with pure numeric fields are mistakenly identified as list indices by `isdigit()`, triggering `current.extend([None] * (index - len(current) + 1))` to attempt allocating hundreds of millions of elements, instantly exhausting memory.

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

**Fix**:
1. Always use dictionaries when pre-creating intermediate layers, no longer guessing container type based on whether the next segment is a number
2. When setting the final value, only process as an index if the container itself is a list and the index is less than `STORAGE_MAX_LIST_INDEX` (10000); safely skip large indices
3. Change the recursive implementation to an iterative one, eliminating potential infinite recursion risks in the original code
4. Add `STORAGE_MAX_LIST_INDEX` constant to `Core/constants.py`, centrally managing the safe upper limit for indices

**Fix Date**: 2026/07/10

**Reproduction Steps**:
```python
# Writing a nested key path containing a large number field (such as QQ group ID) triggers OOM
await sdk.storage.aset("groups.871684833.name", "某群")
# → Process memory surges instantly, OOM Kill
```

**Regression Tests**: `tests/unit/test_unit_storage.py` adds 4 new regression cases
- `test_nested_key_numeric_segment_as_dict_key` — precisely reproduces OOM scenario
- `test_nested_key_numeric_segment_multiple` — multiple consecutive numeric fields as dictionary keys
- `test_nested_key_existing_list_index_set_within_limit` — existing list index write within limit
- `test_nested_key_list_index_safety_limit` — safety limit validation for large indices

**Severity**: 🔴 Critical

**Type**: Storage

---

### [BUG-025] on_config_update callback not triggered by core router

**Issue**: The `on_config_update(old, new)` callback is defined in the base class (`BaseModule` / `BaseAdapter`), but the core framework does not associate it with configuration change events. The result is: when editing configuration via the management panel, it triggers, but manual editing of `config.toml` or calling `setConfig()` does not trigger `on_config_update`.

**Cause**: `ConfigManager` emits `config.set` / `config.updated` lifecycle events when configuration changes, but lacks subscription logic to forward these events to each component's `on_config_update` method.

**Root Cause Chain**:
```
Core does not subscribe to config.set / config.updated
  → Configuration change events are not forwarded
    → on_config_update is not called
      → Manual file edit / code setConfig does not trigger hot update callback
```

**Affected Versions**: All versions

**Fixed Version**: 2.6.2

**Fix**: `ModuleManager` / `AdapterManager` register subscriptions for `config.set` (covering code `setConfig()` path) and `config.updated` (covering manual file edit path), match by configuration key prefix, and call corresponding component's `on_config_update`, passing type-safe configuration objects. Also fix `_flush_config()` writing file without synchronizing `_config_mtime`, avoiding framework self-writing being mistakenly judged as external modification and repeatedly triggering `config.updated`.

**Compatibility Note**: Configuration hot update is now centrally maintained by the framework core. Previously, the configuration management panel handled it; this logic has been removed, and upgrading the framework requires upgrading the panel, otherwise double-triggering (core + panel) will occur. The `on_config_update` method signature and semantics remain unchanged; subclasses need no modification.

**Fix Date**: 2026/07/23

**Severity**: 🟡 Medium

**Type**: Configuration System

---

### [BUG-026] notice/request event reply target inference error

**Issue**: In group notification events (such as member joining `group_member_increase`), calling `event.reply()` sends the message to the user who triggered the event's private chat, not the group where the event occurred. The same applies to friend notification events, with reply targets possibly incorrect.

**Cause**: `infer_receive_type()` directly returns the event's `detail_type` as the session type. For message events, this is correct (`detail_type` values `private`/`group` are session types), but for notice/request events, `detail_type` is a semantic subtype (such as `group_member_increase`, `friend_increase`), not a session type. Subsequent `convert_to_send_type()` and `get_id_field()` find no match in the mapping table and default to `"user"` / `"user_id"`, causing reply targets to be incorrect.

**Root Cause Chain**:
```
notice event detail_type="group_member_increase"
  → infer_receive_type() directly returns "group_member_increase"
    → convert_to_send_type("group_member_increase") not in mapping → default "user"
    → get_id_field("group_member_increase") not in mapping → default "user_id"
      → target_id = event["user_id"]  ← new member's private chat (not group)
```

**Affected Versions**: All versions

**Fixed Version**: 2.7.0-dev.3

**Fix**: `infer_receive_type()` adds a check—`detail_type` is only returned directly if it is a known session type (standard or custom); otherwise, the session type is inferred from the ID field (`group_id` / `channel_id` / `user_id`, etc.).

**Regression Tests**: `tests/unit/test_unit_session_type.py` → `TestNoticeRequestTypeInference` (10 cases)

**Fix Date**: 2026/07/29

**Severity**: 🟢 Minor

**Type**: Event System

---

### [BUG-027] Route rate limiting cleanup task uses fixed window causing long window rules to fail

**Issue**: When routing rate limiting is configured as a long window rule (such as `100/hour`, `{"requests": 100, "window": 3600}`), the rate limiting is ineffective—practically behaving like `100/minute` (up to ~6000 requests per hour), failing to provide the expected hourly protection.

**Cause**: `_apply_rate_limit` parses the actual `window` for each route (up to 3600 seconds), and per-request checks do use this window; however, the background cleanup task `_cleanup_expired_rate_limits` uses a fixed constant `DEFAULT_RATE_LIMIT_WINDOW_SECS` (60 seconds) as the unified cleanup threshold for all routes. Thus, time stamps earlier than 60 seconds in the `100/hour` route are cleared early by the cleanup task, preventing the accumulation of nearly 100 records within the hour window, severely weakening the rate limiting.

**Root Cause Chain**:
```
_apply_rate_limit parses window=3600 (100/hour)
  → per-request checks use 3600s retention time (correct)
  → but _cleanup_expired_rate_limits uses fixed max_window=60s to clean
    → time stamps earlier than 60s are cleared
      → the hour window only retains records from the last 1 minute
        → 100/hour effectively degrades to ~100/minute (relaxed by ~60x)
```

**Affected Versions**: 2.6.0-dev.0 - 2.7.0-dev.4

**Fixed Version**: 2.7.0-dev.5

**Fix**: Added `_rate_limit_windows: dict[str, int]` to record each route's actual window by store key; `_apply_rate_limit` writes the window when creating the entry for the first time; `_cleanup_expired_rate_limits` changes to clean by each key's own window (falling back to default if missing); cleanup and deletion of entries and `stop()` synchronize maintenance of the two dictionaries.

**Fix Date**: 2026/07/31

**Regression Tests**: `tests/unit/test_unit_router.py` → `TestRateLimit::test_cleanup_respects_per_route_window`

**Severity**: 🔴 Critical

**Type**: Routing

---

### [BUG-029] Configuration listener broadcasts incomplete TOML and silently swallows exceptions

**Issue**: When a user manually edits `config.toml` and saves it halfway (producing a temporary syntax error), the configuration monitoring background thread detects the mtime change, reloads the configuration, but fails to load and still broadcasts an empty configuration `{}` for `config.updated`, causing adapters/modules' `on_config_update` to receive an empty configuration and mistakenly assume all configuration items were cleared, reverting to default values. Additionally, the listener loop uses `except Exception: pass` to silently swallow all exceptions, making it impossible to diagnose watcher failures.

**Cause**: Two defects overlap:
1. `_load_config` overwrites `self._cache` to `{}` when TOML syntax errors/permission errors occur, but the background listener thread `_watch_loop` and cache timeout path `_check_cache_validity` call `_emit_config_updated()` unconditionally after `_load_config()`, broadcasting the "empty cache from failed load" as a real change.
2. `_watch_loop`'s `except Exception: pass` does not log any errors.

**Root Cause Chain**:
```
User saves halfway → TOML syntax error
  → _load_config() overwrites _cache = {}
    → _watch_loop unconditionally _emit_config_updated(new_config={})
      → Adapters/modules on_config_update receive empty config
        → Mistake configuration as cleared, revert to default values
```

**Affected Versions**: 2.6.2-dev.1 - 2.7.0-dev.4

**Fixed Version**: 2.7.0-dev.5

**Fix**:
1. `_load_config` changed to return `bool`; TOML syntax errors/permission errors/other errors retain the last valid cache (no longer overwrite to `{}`), only record diagnostic logs and return `False`
2. `_watch_loop` and `_check_cache_validity` only emit `config.updated` if `_load_config()` returns `True`
3. `_watch_loop`'s `except Exception` changed to warn-level logging (new i18n key `core.config.watcher_error`, five languages synchronized)

**Fix Date**: 2026/07/31

**Regression Tests**: `tests/unit/test_unit_config.py` → `test_malformed_toml_preserves_last_valid_cache`, `test_permission_denied_logs_clear_message` (updated to verify cache retention + return False)

**Severity**: 🟡 Medium

**Type**: Configuration System

---

### [BUG-030] Configuration watcher race condition causes setConfig delayed write to silently drop data

**Issue**: Multiple users report that after using `config.setConfig(key, value)` (default `immediate=False`), their module configuration is not written to `config.toml`, while other module configurations are normal. Setting `immediate=True` (force flush) can avoid this. The result is: configuration written at runtime is lost after the next restart, while configuration generated at startup via templates is retained.

**Cause**: Two overlapping defects:
1. **Logical defect**: `_watch_loop` unconditionally `_dirty_keys.clear()` when `_check_file_change()` returns `True`. But `_check_file_change()` only uses `!=` to compare mtime, and the framework's own `_flush_config` writing also changes mtime—although `_flush_config` updates `_config_mtime` after writing, the watcher thread may still observe mtime differences between file writing and mtime assignment (and on coarse-grained file systems), mistakenly identifying it as "external modification" and clearing all dirty keys.
2. **Thread defect**: `_watch_loop` operates `_write_timer`/`_dirty_keys` without holding `_lock`, creating data races with `setConfig` (holding lock to write `_dirty_keys`), `_schedule_write` (holding lock to write `_write_timer`).

**Root Cause Chain**:
```
Module A setConfig(immediate=True) → flush writes, mtime changes
  → User module setConfig(immediate=False) → enters _dirty_keys, flushes in 5s
    → Watcher polls, _check_file_change observes mtime difference from its own previous write
      → _dirty_keys.clear() → User module's dirty keys are silently dropped
        → Configuration missing on next restart
```

**Affected Versions**: 2.6.0 - 2.7.0

**Fixed Version**: 2.7.1

**Fix**:
1. Added `_last_self_write_mtime` field; `_flush_config` records it after writing; `_check_file_change` first compares this value when mtime changes, matching indicates self-write and returns `False`
2. `_watch_loop` holds `_lock` for the entire segment; retains `_dirty_keys` for actual external modification (merge semantics), next flush merges with external content (dirty keys take precedence), no longer `clear()`
3. `getConfig`/`_check_cache_validity` paths are unaffected (their reload does not clear dirty keys)

**Fix Date**: 2026/08/06

**Regression Tests**: `tests/unit/test_unit_config.py` → `test_self_write_not_detected_as_external`, `test_external_change_preserves_dirty_keys`, `test_flush_merges_dirty_with_external`

**Severity**: 🔴 Critical

**Type**: Configuration System

---

### [BUG-032] Configuration delay write period "write-then-read" reads old values

**Issue**: After `config.setConfig()` (default `immediate=False` delay ~5s to write), writing a dot-key and immediately reading its **parent/ancestor node** (such as `set_erispulse_section("scope.actions.MyModule", {...})` followed by `get_erispulse_config()`) returns the old value, with the written sub-key "disappearing" until the next flush. Hot update scenarios for scope configurations ("write-read-write") are affected (2.8.0 test plugin `/t_section` use case exposed).

**Cause**: `setConfig` stores dot-keys in the dirty queue `_dirty_keys` in **flat form**, only `getConfig`'s **exact key query** hits the dirty queue; tree-path queries (`getConfig("ErisPulse.scope")`) only go through the cache tree, not overlaying dirty values—during the delay write period (`_flush_config` merges dirty keys into cache and clears the queue), a read-you-write gap forms.

**Affected Versions**: 2.6.0 - 2.8.0-dev.1

**Fixed Version**: 2.8.0-dev.1

**Fix**: `getConfig` introduces dirty overlay semantics—① exact match dirty key returns directly (original behavior unchanged); ② dirty key is the query key's ancestor → take the longest dirty ancestor, parse the remaining path in its value subtree; ③ dirty key is the query key's descendant → build an overlay subtree (`_dirty_overlay`) and deeply merge it with the cache subtree (`_deep_merge`, override priority, not modifying the original cache object). Without dirty keys, the original fast path is used, zero additional overhead.

**Fix Date**: 2026/09/04

**Regression Tests**: `tests/unit/test_unit_config.py` → `test_get_config_overlays_dirty_descendant`, `test_get_config_overlay_merges_with_cache_siblings`, `test_get_config_overlay_new_branch`, `test_get_config_dirty_ancestor_query`, `test_get_config_dirty_exact_key_still_wins`

**Severity**: 🟡 Medium

**Type**: Configuration System

---

### [BUG-033] wait_reply hung replies are starved by high-priority processors

**Issue**: When a module calls `wait_reply()` to wait for a user reply, if that reply message is claimed by a higher-priority event processor (`mark_processed()`), the command dispatcher sees the `_processed` flag at the entry and returns directly, so the reply matching `_check_pending_reply` hanging at the end of `_handle_message` never executes—the waiting party receives no reply and can only wait until timeout returns `None`. Typical trigger scenario: robots using high-priority message processors (recording/audit/interception) have random failures in all dialog interactions.

**Cause**: Reply matching `_check_pending_reply` is placed at the end of `_handle_message` (only executed if message is not matched), while `_processed` checking is before it—the order of claim checking and reply matching is reversed. Interactive waiting is a framework-level session continuation mechanism, not a competing processor, and should not be affected by other processors' claim.

**Affected Versions**: 2.2.0-dev.0 - 2.8.0-dev.1

**Fixed Version**: 2.8.0-dev.2

**Fix**: Move reply matching to the entry of `_handle_message` (before `_processed` checking, only for message events): first try to complete the pending conversation, mark the event as processed if matched, and the subsequent checks naturally short-circuit; if not matched, continue the original command matching process. The judgment chain is delegated to a new interaction session manager (`Core/Event/interaction.py`), incidentally gaining the ability to cancel by affiliation and permission review.

**Fix Date**: 2026/09/08

**Regression Tests**: `tests/unit/test_unit_interaction.py` (TestRegisterResolve matched/unmatched/claim flag), `tests/unit/test_unit_event.py` (full chain of wait_reply)

**Severity**: 🟡 Medium

**Type**: Event System / Command System

---

### [BUG-034] Scope persist=False runtime binding silently overridden by any subsequent config write

**Issue**: `scope.set_module(..., persist=False)` and other runtime writes only modify memory `self._data`; but scope subscribes to `config.set` / `config.updated` events, so any code writing configuration (such as a module loading its own default configuration) triggers scope to rebuild the configuration tree from the configuration file, discarding all previous runtime bindings (reverting judgment to default allow), with no log warning. Scenarios dependent on runtime bindings (Dashboard "runtime-only" switches, module runtime dynamic disabling) revert behavior after unrelated module writes configuration.

**Cause**: Root cause chain: `scope.set/delete(persist=False)` only writes memory (`Core/scope.py`) → any `setConfig` triggers `config.set` event → `_on_config_updated` unconditionally `_load_config()` → `_apply_tree()` replaces `self._data = {...}` with the entire persistent layer, runtime bindings not in the configuration file are discarded.

**Affected Versions**: 2.8.0-dev.1 - 2.8.0-dev.2
**Fixed Version**: 2.8.0-dev.2
**Fix**: Introduced a runtime override layer `_runtime_overrides` (with deletion sentinel): `persist=False` writes/Deletes are recorded in the override layer, `_apply_tree()` rebuilds the persistent layer and replays in write order, runtime rules remain effective after any configuration write; `persist=True` writes/Deletes clear corresponding override records (user persistence semantics take precedence); `config.set` filters by event key, `config.updated` compares new and old scope nodes, only rebuilds if scope actually changes (附带避免无关写入冲刷判定 LRU 缓存); added `unregister_by_owner()` for module unloading to clean up with the caller. `Core.Event.overrides` has a similar issue with persist=False runtime overrides, fixed with the override layer architecture.
**Fix Date**: 2026/09/09

**Reproduction Steps**: ① `scope.set_module("testplat", blocked=["TestB"], persist=False)` → judgment False; ② Any module executes `config.setConfig("HelpModule", {...})` → triggers scope rebuild; ③ `scope.is_allowed("testplat", None, "TestB")` returns True (expected still False).
**关联**: Issue #432
**Regression Tests**: `tests/unit/test_unit_scope.py::TestRuntimeOverrideSurvival` (irrelevant write survives/Tree rebuild replays/Delete sentinel/Persistent clear/Exact invalidation/Owner cleanup)

**Severity**: 🟡 Medium
**Type**: Configuration System / Runtime

---

### [BUG-035] Configuration panel select options and dict fields rendered as [object Object]

**Issue**: In the WebUI configuration panel, select field options dropdown displays `[object Object]` (such as dynamically generated color style options); undeclared control type dict fields (such as `stalker_mode`, `knowledge_base`, etc., nested configuration segments) display `[object Object]` in text boxes, making them impossible to view and edit normally.

**Cause**: Two independent defects: ① The framework i18n resolver `_resolve_i18n_text` only restores dicts with `i18n` keys, and option labels with only `default` keys (no `i18n` key for dynamic text) are passed through as-is, and the frontend `esc(label)` string coercion results in `[object Object]`; ② Dashboard rendering branches only do JSON textarea for array types, dict values fall into plain text input branches and are `String()` coerced. Additionally, if modules misdeclare `_schema_meta` as a regular dataclass field (missing `ClassVar` annotation), it enters the schema as a configuration field, exacerbating the confusion.

**Affected Versions**: 2.7.0 - 2.8.0-dev.2
**Fixed Version**: 2.8.0-dev.2
**Fix**: ① `_resolve_i18n_text` supports dicts with only `default` keys, restoring them to text; ② Framework schema/template/default value/filling/validation always exclude fields with underscores at the beginning (harmless if misdeclared); ③ Dashboard select option label objects fallback to `default` priority, dict/table fields rendered as JSON textarea (save path as `tp=object` JSON.parse back, complete round trip).
**Fix Date**: 2026/09/09

**Regression Tests**: `tests/unit/test_unit_config.py::TestResolveI18nDefaultOnlyDict`, `TestSchemaUnderscoreFieldExclusion`

**Severity**: 🟡 Medium
**Type**: Configuration System

---

### [BUG-036] Multi-instance shared configuration directory causes occasional configuration write failures (ENOENT)

**Issue**: In Docker deployment scenarios (multiple containers mounting the same host configuration directory), logs occasionally show two consecutive `Failed to write configuration file ... [Errno 2] No such file or directory: '...config.toml.tmp' -> '...config.toml'`. This configuration write is discarded (old configuration is fully retained, no configuration loss is observed), functionality is unaffected, but repeated alerts interfere with troubleshooting, and the configuration items to be written must wait for the next write to be written.

**Cause**: Root cause chain: `_flush_config` / `setConfigTemplate` uses a **fixed-name** temporary file `config.toml.tmp` to carry new content, `write()` does not `fsync` before `rename()` directly. When two ErisPulse instances share the same configuration directory, B instance `open("w")` may **truncate** A instance's currently writing temporary file → A `rename` finds the target file already taken or content truncated by B, reporting ENOENT (i.e., the user's log shows two consecutive error messages). In reported cases, only a write failure alert is shown (old configuration is retained); if the timing is more extreme, `rename` may output an empty/half-written `config.toml` (a potential risk, not yet exploded in real environments). In single-instance scenarios, ext4's delayed allocation also has a "rename metadata before data block is written" crash window (SIGKILL / power loss). `_file_lock` is a process-level `threading.RLock`, providing no constraint for cross-process/cross-container writes.

**Affected Versions**: 2.2.0-dev.0 - 2.8.0

**Fixed Version**: 2.8.1-dev.0

**Fix**: Configuration writes are unified to `_atomic_write_text()`: `mkstemp` generates a process-unique temporary file in the same directory (eliminating fixed-name contention, multi-instance degradation to last-writer-wins, no ENOENT); after writing, `flush + fsync` forces data to be written (eliminating the "rename effective, data not written" window); `os.replace` atomically replaces the target (POSIX/Windows are atomic, at any moment the disk has either the complete old content or the complete new content); fsync the configuration directory on POSIX. All three write points (`_flush_config`, `setConfigTemplate`, root directory configuration migration) switch; exception path cleanup logic is restructured with the unique temporary file name. Added **multi-instance detection**: at startup, an advisory lock (`flock` on POSIX / `msvcrt.locking` on Windows) exclusively holds the configuration directory lock file `.erispulse_config.lock`, if occupied, outputs an i18n warning (does not block startup), the lock is automatically released by the OS when the process exits, with no ghost locks.

**Fix Date**: 2026/09/13

**Reproduction Steps**: ① Two containers mount the same host `config/` directory and run ErisPulse; ② Trigger configuration write (such as module registering default configuration) in any instance; ③ Observe logs showing ENOENT write failure alerts, this write is discarded (old configuration is retained).

**关联**: User report (1Panel container x2)

**Regression Tests**: `tests/unit/test_unit_config_atomic_write.py` (complete content write/no temporary file residue/write failure preserves original file/two-instance concurrent writes always legal/file lock creation/multi-instance warning/migration atomic write)

**Severity**: 🟢 Minor

**Type**: Configuration System