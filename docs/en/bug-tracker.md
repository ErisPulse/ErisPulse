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
|----------|-------|
| 🔴 Critical | 16 |
| 🟡 Moderate | 17 |
| 🟢 Minor | 3 |
| **Total** | **36** |

| Type | Count |
|------|-------|
| Adapters | 6 |
| Configuration System | 10 |
| Event System | 7 |
| CLI | 3 |
| Storage | 3 |
| Loading System | 3 |
| Routing | 2 |
| Client | 1 |
| Runtime | 1 |

> Note: A single bug can belong to multiple types; the table above is counted by the primary type.

## Fixed Bugs

### [BUG-001] Event handler registration duplication causing multiple event processing

**Issue**: When registering multiple handlers using decorators like `@message` / `@notice`, the same event is triggered multiple times, causing commands to execute multiple times and logs to be duplicated.

**Cause**: `BaseEventHandler` lacks deduplication logic when registering handlers to the adapter event bus. Each decorator mounts a handler once, leading to multiple calls during event distribution.

**Affected Versions**: 2.2.0-dev.0 - 2.2.1-dev.0

**Fixed Version**: 2.2.1-dev.0

**Fix**: Optimized `BaseEventHandler` to ensure each event type is registered only once to the adapter, preventing duplicate triggers.

**Fix Date**: 2025/08/18

**Severity**: 🔴 Critical

**Type**: Event system

---

### [BUG-002] Init command adapter configuration path type error

**Issue**: Using `ep init` for interactive initialization, selecting a configuration adapter results in an error:

```
Interactive initialization failed: unsupported operand type(s) for /: 'str' and 'str'
```

**Cause**: In version 2.3.7, the configuration file path adjustment caused inconsistent parameter types. The method `_configure_adapters_interactive_sync` accepts `str` but internally uses the `Path` `/` operator to concatenate paths.

**Affected Versions**: 2.3.7 - 2.3.9-dev.1

**Fixed Version**: 2.3.9-dev.1

**Fix**: Changed the parameter type of `_configure_adapters_interactive_sync` from `str` to `Path`, passing `Path` objects directly.

**Fix Date**: 2026/03/23

**Severity**: 🟡 Medium

**Type**: CLI

---

### [BUG-003] Commands fail after restart

**Issue**: After calling `sdk.restart()`, commands registered via `@command` are not triggered, causing the robot to be unresponsive after sending a command.

**Cause**: `adapter.shutdown()` clears the event bus, but `BaseEventHandler`'s `_linked_to_adapter_bus` status is not reset to `False`, causing `_process_event` to skip re-registration as it believes it's already linked to the adapter bus.

**Affected Versions**: 2.2.x - 2.4.0-dev.2

**Fixed Version**: 2.4.0-dev.3

**Fix**: Introduced `_linked_to_adapter_bus` status tracking; after `_clear_handlers()` disconnects the bus, `register()` automatically re-registers next time, adapting to shutdown/restart scenarios.

**Fix Date**: 2026/04/09

**Severity**: 🔴 Critical

**Type**: Event system

---

### [BUG-004] Lifecycle event handlers not cleaned up

**Issue**: After `sdk.restart()`, old lifecycle event handlers remain and are triggered repeatedly, causing the same event to be processed multiple times.

**Cause**: The `lifecycle._handlers` dictionary was never cleared in `uninit()`, leaving old and new handlers both active after restart.

**Affected Versions**: 2.3.0 - 2.4.0-dev.2

**Fixed Version**: 2.4.0-dev.3

**Fix**: Clear `lifecycle._handlers` at the end of the `Uninitializer` cleanup process (after all events are submitted).

**Fix Date**: 2026/04/09

**Severity**: 🟡 Medium

**Type**: Runtime

---

### [BUG-005] Event.is_friend_add/is_friend_delete detail_type inconsistent with OB12 standard

**Issue**: `Event.is_friend_add()` checks `detail_type == "friend_add"`, `Event.is_friend_delete()` checks `detail_type == "friend_delete"`, but OneBot12 standard defines `detail_type` values as `"friend_increase"` and `"friend_decrease"`. This inconsistency causes handlers registered via decorators to fail when `is_friend_add()`/`is_friend_delete()` returns `False`.

**Cause**: `wrapper.py` uses non-standard naming, while `notice.py` uses correct OB12 standard naming.

**Affected Versions**: Since implementation

**Fixed Version**: 2.4.2-dev.1

**Fix**: Changed `is_friend_add()`'s match value from `"friend_add"` to `"friend_increase"`, and `is_friend_delete()` from `"friend_delete"` to `"friend_decrease"`.

**Fix Date**: 2026/04/13

**Severity**: 🟡 Medium

**Type**: Event system

---

### [BUG-006] adapter.clear() not clearing _started_instances causing incorrect state after restart

**Issue**: `AdapterManager.clear()` clears `_adapters`, `_adapter_info`, handlers, and `_bots`, but omits `_started_instances`. If `clear()` is called while adapters are running, `_started_instances` retains dangling references, causing incorrect state after restart.

**Cause**: When `_started_instances` was introduced in 2.4.0-dev.1, it was not cleared in `clear()`.

**Affected Versions**: 2.4.0-dev.1 - 2.4.2-dev.0

**Fixed Version**: 2.4.2-dev.1

**Fix**: Added `self._started_instances.clear()` in the `clear()` method.

**Fix Date**: 2026/04/13

**Severity**: 🟡 Medium

**Type**: Adapter

---

### [BUG-007] command.wait_reply() uses deprecated asyncio.get_event_loop()

**Issue**: `CommandHandler.wait_reply()` uses `asyncio.get_event_loop()` to create futures and get timestamps, which is deprecated in Python 3.10+. In asynchronous contexts, `asyncio.get_running_loop()` should be used. This is inconsistent with `wrapper.py`'s `wait_for()` method, which uses `get_running_loop()`.

**Cause**: The old API was used during development, and the new `wait_for()` method used the correct API but did not retroactively fix old code.

**Affected Versions**: 2.3.0-dev.0

**Fixed Version**: 2.4.2-dev.1

**Fix**: Replaced `asyncio.get_event_loop()` with `asyncio.get_running_loop()` in `command.py`.

**Fix Date**: 2026/04/13

**Severity**: 🟢 Minor

**Type**: Event system

---

### [BUG-008] Bot offline event duplicated during shutdown

**Issue**: When calling `adapter.shutdown()` to shut down all adapters, `_update_bot_status()` repeatedly submits Bot offline events during shutdown, causing the same batch of Bots to be marked offline multiple times and triggering the `adapter.bot.offline` lifecycle event multiple times.

**Cause**: The Bot status tracking system introduced in 2.4.0-dev.1 did not set a "shutting down" flag during `shutdown()`, so `_update_bot_status()` could not distinguish between normal offline and cascading offline during shutdown.

**Affected Versions**: 2.4.0-dev.1 - 2.4.2-dev.1

**Fixed Version**: 2.4.2-dev.1

**Fix**: Added `_is_being_shutdown` flag in `AdapterManager`, set to True at the start of `shutdown()` and cleared at the end; `_update_bot_status()` skips duplicate submissions during shutdown if the flag is set.

**Fix Date**: 2026/04/21

**Severity**: 🟡 Medium

**Type**: Adapter

---

### [BUG-009] LazyModule synchronous access to BaseModule causing incomplete initialization

**Issue**: When accessing lazy-loaded BaseModule attributes in a synchronous context, the module uses `loop.create_task()` for asynchronous initialization without waiting, leading to race conditions when the attribute is accessed before initialization completes.

**Cause**: `_ensure_initialized()` uses `loop.create_task(self._initialize())` and immediately returns without ensuring initialization completes.

**Affected Versions**: 2.4.0-dev.0 - 2.4.2-dev.1

**Fixed Version**: 2.4.2-dev.2

**Fix**: In synchronous contexts, BaseModule's initialization is changed to use `asyncio.run(self._initialize())` to ensure initialization completes before returning. The transparent proxy feature is maintained, so users do not need to be aware of synchronous/asynchronous differences.

**Fix Date**: 2026/04/21

**Severity**: 🟡 Medium

**Type**: Loading system

---

### [BUG-010] Multi-threaded configuration system write causing data loss

**Issue**: In multi-threaded environments, calling `config.setConfig()` multiple times may result in partial writes being lost due to non-atomic read-modify-write operations in `_flush_config()`. Although `_flush_config()` uses `RLock`, file read and write operations lack file lock protection, and `_schedule_write`'s Timer may be triggered multiple times, causing overwrites.

**Cause**: `_flush_config()` uses `RLock` but lacks file lock protection between file read and write, and `_schedule_write`'s Timer may be triggered multiple times, causing overwrites.

**Affected Versions**: 2.3.0 - 2.4.2-dev.1

**Fixed Version**: 2.4.2-dev.2

**Fix**:
1. Added file lock mechanism (`_file_lock`) to ensure atomic file operations
2. Used temporary file for writing and atomically renamed (`os.replace`/`os.rename`)
3. Improved `_schedule_write`'s Timer cancellation and rescheduling logic

**Fix Date**: 2026/04/21

**Severity**: 🔴 Critical

**Type**: Configuration system

---

### [BUG-011] Windows Ctrl+C unable to stop program

**Issue**: On Windows, running `python main.py` directly, pressing Ctrl+C does not terminate the program. After the program starts and outputs the routing server information, Ctrl+C has no response, requiring the process to be forcefully killed via Task Manager. However, running via `epsdk run` works normally—though `epsdk run` uses a subprocess model.

**Cause**: The Hypercorn ASGI server's `serve()` function internally registers its own SIGINT handler via `signal.signal(SIGINT, handler)`, overriding Python's default `KeyboardInterrupt` handling mechanism. When Hypercorn is started as a background task via `asyncio.create_task()`, its internal shutdown process cannot be triggered normally (as it expects `worker_serve` mode), causing Ctrl+C signals to be swallowed by Hypercorn without triggering any cleanup actions.

**Affected Versions**: 2.3.6 - 2.4.2

**Fixed Version**: 2.4.3-dev.0

**Fix**:
1. Switched ASGI server from Hypercorn to Uvicorn (`pyproject.toml` dependency change)
2. Used `uvicorn.Server._serve()` to start the server, **bypassing** the `capture_signals()` signal handling context manager
3. Implemented graceful stop via `server.should_exit = True`, canceling background tasks if timeout occurs
4. Synchronized removal of subprocess model and `runtime/cleanup.py` cleanup module (no longer needed)

**Fix Date**: 2026/04/28

**Severity**: 🔴 Critical

**Type**: CLI / Runtime

---

### [BUG-012] Hot restart after module update not生效

**Issue**: After executing `sdk.restart()` for a soft restart, the new code (e.g., new API routes) of modules/adapters upgraded via `epsdk install` is not生效, and old logic is still running. The latest code must be loaded by completely restarting the process.

**Cause**: `_do_restart()` calls `entry_point.load()` during re-initialization, but this function returns a cached old module object from `sys.modules` instead of reloading from disk.

**Affected Versions**: Early versions - 2.4.3-dev.1

**Fixed Version**: 2.4.3-dev.1

**Fix**: Clear `sys.modules` cache of loaded modules/adapters before `init()` in `uninit()`, so `entry_point.load()` loads the latest code from disk. Added `_collect_top_level_modules()` and `_invalidate_module_cache()` helper methods to derive top-level module names via `top_level.txt` or entry-point value.

**Fix Date**: 2026/05/03

**Severity**: 🔴 Critical

**Type**: Loading system / Runtime

---

### [BUG-013] Module load strategy sorting logic error

**Issue**: `ModuleLoadStrategy` provides a `priority` field to declare module initialization priority, but the implementation has a flaw, causing modules to be initialized in the wrong order and not according to the declared `priority`. When modules have initialization dependencies, the correct order cannot be ensured via `priority`.

**Cause**: The implementation of the load strategy has a flawed sorting logic; `initialize_modules()` does not sort the module list by `priority`.

**Affected Versions**: 2.3.4 - 2.4.5-dev.2

**Fixed Version**: 2.4.5-dev.3

**Fix**: Before traversing in `initialize_modules()`, sort the module list by `priority` in descending order. Modules with the same priority maintain their original relative order (stable sort).

**Fix Date**: 2026/05/15

**Severity**: 🟡 Medium

**Type**: Loading system

---

### [BUG-014] Adapter middleware returning None causing event data loss

**Issue**: When `adapter.emit()` executes the OneBot12 middleware chain, if a middleware returns `None` (e.g., forgetting to `return data`), subsequent middleware and all event handlers receive `processed_data` as `None`, causing event processing to fail completely.

**Cause**: The middleware chain implementation `processed_data = await middleware(processed_data)` does not check if the return value is `None`, directly overwriting the previous processing result.

**Affected Versions**: unknown - 2.4.5-dev.3

**Fixed Version**: 2.4.5-dev.4

**Fix**: Ignore the `None` return value from middleware, retain the original data, and output a warning-level log.

**Fix Date**: 2026/05/15

**Severity**: 🔴 Critical

**Type**: Adapter / Event system

---

### [BUG-015] Configuration file path depends on working directory

**Issue**: `ConfigManager`'s configuration file path defaults to the relative path `"config/config.toml"`, which resolves at runtime using `os.getcwd()`. If the working directory changes during runtime (e.g., via `os.chdir()`), file read/write operations point to the wrong location, causing configuration loss or reading old data.

**Cause**: In `__init__`, the relative path is stored directly without resolving it to an absolute path at initialization.

**Affected Versions**: 2.3.7 - 2.4.5-dev.3

**Fixed Version**: 2.4.5-dev.4

**Fix**: In `ConfigManager.__init__()`, if the passed path is relative, automatically resolve it to an absolute path using `os.path.abspath()`.

**Fix Date**: 2026/05/15

**Severity**: 🟡 Medium

**Type**: Configuration system

---

### [BUG-016] BaseStorage confusing storing None value with missing key

**Issue**: `BaseStorage.get_multi()` / `__getattr__()` cannot distinguish between "key missing" and "key value is None", so when a user explicitly stores `None`, subsequent reads treat it as a missing key.

**Cause**: The value retrieval logic directly uses `value is None` to check if the key exists, lacking an independent "missing" marker.

**Affected Versions**: Early versions - 2.4.6-dev.6

**Fixed Version**: 2.4.6-dev.6

**Fix**: Introduced `_SENTINEL` sentinel value to distinguish between "key missing" and "value is None", eliminating confusion.

**Fix Date**: 2026/06/07

**Severity**: 🟡 Medium

**Type**: Storage

---

### [BUG-017] WebSocket route auto_accept flag lost after service restart

**Issue**: After a service restart (e.g., `sdk.restart()`), all WebSocket route `auto_accept` configurations revert to `False`, causing previously expected auto-accept connections to hang, with clients receiving no response for a long time, resulting in WS connections freezing.

**Cause**: `_restore_routes_from_records()` hardcodes `auto_accept` to `False` when restoring routes from persistent records, not reading the original record value; also, when the route storage tuple expanded from a binary to a ternary tuple, the restore logic was not synchronized.

**Affected Versions**: 2.3.8-dev.0 - 2.4.6-dev.6

**Fixed Version**: 2.4.6-dev.6

**Fix**: The route storage tuple expanded to `(handler, auth_handler, auto_accept)`, and `_restore_routes_from_records()` reads the real `auto_accept` value from the record instead of hardcoding `False`.

**Fix Date**: 2026/06/07

**Severity**: 🔴 Critical

**Type**: Routing

---

### [BUG-018] HTTP/WS client concurrent calls causing crashes and connection leaks

**Issue**: The HTTP and WebSocket clients in `Core/client.py` have multiple stability issues in concurrent scenarios, leading to connection leaks or process crashes:
- Concurrent calls to `ClientWebSocket.receive()` throw `Concurrent call to receive() is not allowed` from aiohttp
- Concurrent calls to `_get_http_session()` / `_get_ws_session()` may create multiple sessions, and `_drain_sessions()` does not close old connections, causing leaks
- `request()` exception handling order is incorrect: `except ClientConnectionError` (ErisPulse exception) never triggers, aiohttp connection errors are caught by generic `except Exception`, causing "retry + session rebuild" logic (dead code) to never execute
- `send_json()` ignores `mode="binary"` parameter; `_get_ws_session()` does not pass default request headers

**Cause**: The initial client implementation (2.4.6-dev.5) lacked concurrency protection and proper exception classification, mishandling aiohttp exception hierarchy and ErisPulse custom exception inheritance.

**Affected Versions**: 2.4.6-dev.5 - 2.4.8

**Fixed Version**: 2.4.8

**Fix**:
1. Added `_recv_lock` to serialize all `receive()` / `receive_text()` / `receive_bytes()` calls
2. Added `_session_lock` to protect session creation; `_drain_sessions()` changed to an async method and truly closes old sessions
3. Reconstructed `request()` exception handling order: `asyncio.TimeoutError` → `aiohttp.ClientConnectionError` (triggers session rebuild) → `aiohttp.ClientError` → `ClientError` (transparent pass) → `Exception`
4. Fixed `send_json()` mode handling, `_get_ws_session()` default request header pass, `close()` concurrency race, `HttpResponse.__aexit__` duplicate `release()`

**Fix Date**: 2026/06/12

**Severity**: 🔴 Critical

**Type**: Client

---

### [BUG-019] Adapter hot reload route conflict causing reload failure

**Issue**: When a third-party module (e.g., Dashboard) triggers adapter hot reload, or when adapter startup fails and retries, old routes (e.g., `onebot11_default`) are not cleared, causing a `WebSocket path ... already registered` conflict, leading to reload failure. A full process restart is required to recover.

**Cause**: `AdapterManager.shutdown()` only clears routes via `unregister_all_by_namespace(platform)`, but adapters (e.g., OneBot11) register WS routes with `onebot11_{account_name}` as the namespace, resulting in a granularity mismatch and an empty operation; startup failure retry paths also do not clear previous route remnants.

**Affected Versions**: Early versions - 2.4.9

**Fixed Version**: 2.4.9

**Fix**:
1. Automatically track `owner → namespace` relationships during route registration via `current_owner` ContextVar
2. Added `unregister_all_by_owner(owner)`, clearing routes by owner during stop/restart, covering fine-grained namespaces
3. Added `_stop_adapter(platform)` primitive ("stop equals cleanup"), binding adapter stop and resource recycling in one call; `restart()` and startup failure retry both use this entry
4. Added framework-level `adapter.restart(platform)` API, third-party modules should call this method instead of directly manipulating adapter instances

**Fix Date**: 2026/06/12

**Severity**: 🔴 Critical

**Type**: Adapter / Routing

---

### [BUG-020] Subprocess mode `ep run <script>` cannot find subpackages in script directory

**Issue**: When running a script with `ep r .\main.py` in non-hot-reload mode, if the script has relative imports (e.g., `from qg import ...`), it raises `No module named 'qg'`. The `--reload` mode works fine.

**Cause**: The non-hot-reload mode directly calls `runpy.run_path()` to execute the script, which does not automatically add the script's directory to `sys.path`. The `--reload` mode runs via `subprocess.Popen`, which inherits the current working directory, so `sys.path[0]` is the script's directory, enabling normal execution.

**Affected Versions**: 2.5.0 - 2.5.2-dev.0

**Fixed Version**: 2.5.2-dev.0

**Fix**: Before calling `runpy.run_path()`, manually insert the script's directory into `sys.path[0]`.

**Fix Date**: 2026/06/27

**Severity**: 🟡 Medium

**Type**: CLI

---

### [BUG-021] SQL query builder rejects valid wildcards and list expressions

**Issue**: `SQLiteQueryBuilder`'s `_build_select_sql()` validates all SELECT columns using `_validate_identifier()`, which uses a strict whitelist regex `^[a-zA-Z_][a-zA-Z0-9_]*$`, causing legitimate SQL syntax to be incorrectly flagged as unsafe column names:

- `SELECT *` — `*` is a standard SQL wildcard
- `SELECT COUNT(*)` — aggregate function
- `SELECT users.name` — qualified column name
- `SELECT col AS alias` — column alias

Among these, `Select("*")` is used by modules like Cron, causing module `on_load` execution to fail and the module to fail to load.

**Cause**: In version 2.4.6, SQL injection protection was enhanced, introducing the `_validate_identifier()` whitelist validation. This validation is applied to all column names, but it does not distinguish between read-side (SELECT/ORDER BY) and write-side (INSERT/UPDATE). SELECT columns allow complex SQL expressions and should not be restricted by simple identifier whitelists.

**Affected Versions**: 2.4.6 - 2.5.2-dev.1

**Fixed Version**: 2.5.2-dev.2

**Fix**: Changed the SELECT/ORDER BY column validation from whitelist mode to blacklist mode:
1. Added `_validate_select_column()` function, only blocking SQL injection dangerous characters (`;` `'` `"` `--` `/*` `*/` `\x00` newline)
2. Allowed any valid SQL column expression (`*`, `table.*`, `table.column`, `COUNT(*)`, `col AS alias`, etc.)
3. INSERT/UPDATE column names still maintain strict whitelist validation (only allow simple identifiers)

**Fix Date**: 2026/06/29

**Severity**: 🔴 Critical

**Type**: Storage

---

### [BUG-022] _resolve_account() account resolution regression (_accounts_data not populated)

**Issue**: After the 2.5.2 configuration system refactor, multi-account adapters declared with `AccountConfigClass` fail to resolve accounts when calling methods like `wait_reply`, `reply`, etc., throwing `ValueError("未声明 AccountConfigClass，无法解析账户")`. Even if the adapter correctly configures multi-account information, account resolution still fails.

**Cause**: In 2.5.2-dev.5, `_load_accounts()` (responsible for reading, validating, and populating `_accounts_data`) was refactored into `_ensure_accounts_exist()` (only generating configuration templates), but `_resolve_account()` still checks `self._accounts_data is None`. Since `_ensure_accounts_exist()` no longer populates `_accounts_data`, this attribute remains `None`, causing `_resolve_account()` to prematurely return `(None, None)`, and account resolution fails completely.

**Root Cause Chain**:
```
_load_accounts() was deleted
  → __init__ no longer populates _accounts_data
    → _accounts_data is always None
      → _resolve_account() checks _accounts_data is None → return (None, None)
        → downstream calls to _resolve_account() (e.g., call_api) get None
          → trigger error
```

**Affected Versions**: 2.5.2-dev.5 - 2.5.2

**Fixed Version**: 2.5.3

**Fix**: In `BaseAdapter.__init__`, after `self._ensure_accounts_exist()`, restore the population of `_accounts_data`:
```python
if self.AccountConfigClass is not None:
    self._ensure_accounts_exist()
    self._accounts_data = self.accounts  # restore population, data source is real-time read accounts attribute
```
The `_resolve_account()` logic remains unchanged, fully backward compatible:
- Adapters that do not declare `AccountConfigClass`: `_accounts_data` remains `None` → return `(None, None)`
- Adapters that declare `AccountConfigClass`: `_accounts_data` is populated → normal resolution
- Adapters that override `_load_accounts` or manually set `_accounts_data`: override after `super().__init__()` call, highest priority

**Fix Date**: 2026/07/07

**Severity**: 🔴 Critical

**Type**: Adapter / Configuration system

---

### [BUG-023] Adapter cache not refreshed after account configuration change causing account resolution failure

**Issue**: After users modify multi-account adapter account configurations (e.g., filling in token) via Dashboard, the adapter still uses old cache, and calling message-sending-related methods reports `未找到可用账户 (account_id=default)`. A full process restart is required for the new configuration to take effect.

**Cause**: `_accounts_data` is only read from the configuration storage once at `BaseAdapter.__init__`, and is not refreshed afterwards. `AdapterManager._run_adapter()` and `restart()` do not re-read the account configuration before calling `adapter.start()`, causing the cache to be out of sync with the actual configuration.

**Affected Versions**: 2.4.6 - 2.5.4

**Fixed Version**: 2.5.4

**Fix**: In `AdapterManager._run_adapter()` and `restart()`, before calling `adapter.start()`, refresh `adapter._accounts_data = adapter.accounts` to ensure the latest configuration is used each time.

**Fix Date**: 2026/07/09

**Severity**: 🔴 Critical

**Type**: Adapter / Configuration system

---

### [BUG-024] storage.set() writing large numeric ID keys triggers OOM Kill

**Issue**: Calling `storage.set()` to write a nested key path containing a large pure number field (e.g., QQ group ID `871684833`) causes the process to be killed by container OOM (exit code -9), crashing the service and making it impossible to recover.

**Cause**: In the recursive implementation of `_set_nested_value`, pure number fields in the nested key path are mistakenly identified as list indices by `isdigit()`, triggering `current.extend([None] * (index - len(current) + 1))`, attempting to allocate hundreds of millions of elements, instantly exhausting memory.

**Root Cause Chain**:
```
Key path contains pure number field (e.g., group ID 871684833)
  → isdigit() mistakenly identifies as array index
    → extend([None] * (871684833 - len(current) + 1))
      → attempts to allocate hundreds of millions of elements
        → memory exhausted → container OOM Kill (exit code -9)
```

**Affected Versions**: 2.5.1 - 2.5.5

**Fixed Version**: 2.5.5

**Fix**:
1. Always use dictionaries when pre-creating intermediate layers, never guess container type based on whether the next segment is a number
2. Only handle as index when the container itself is a list and the index is less than `STORAGE_MAX_LIST_INDEX` (10000); skip large indices safely
3. Change the recursive implementation to iterative to eliminate potential infinite recursion in the original code
4. Add `STORAGE_MAX_LIST_INDEX` constant to `Core/constants.py`, centrally managing the safe index upper limit

**Fix Date**: 2026/07/10

**Reproduction Steps**:
```python
# Writing a nested key path containing a large number field (e.g., QQ group ID) triggers the OOM scenario
await sdk.storage.aset("groups.871684833.name", "某群")
# → Process memory spikes instantly, killed by OOM
```

**Regression Tests**: `tests/unit/test_unit_storage.py` adds 4 regression test cases
- `test_nested_key_numeric_segment_as_dict_key` — precisely reproduces the OOM scenario
- `test_nested_key_numeric_segment_multiple` — multiple continuous number fields as dictionary keys
- `test_nested_key_existing_list_index_set_within_limit` — writing to an existing list index within the limit
- `test_nested_key_list_index_safety_limit` — safety limit verification for large indices

**Severity**: 🔴 Critical

**Type**: Storage

---

### [BUG-025] on_config_update callback not triggered by core routes

**Issue**: `on_config_update(old, new)` is defined in the base class (`BaseModule` / `BaseAdapter`), but the framework core does not link it to configuration change events. As a result, when editing the configuration management panel, the callback is triggered, but manual editing of `config.toml` or code calling `setConfig()` does not trigger `on_config_update`.

**Cause**: `ConfigManager` emits `config.set` / `config.updated` lifecycle events when configuration changes, but lacks the subscription logic to forward these events to each component's `on_config_update` method.

**Root Cause Chain**:
```
Core does not subscribe to config.set / config.updated
  → Configuration change events are not forwarded
    → on_config_update is not called
      → Manual file editing / code setConfig does not trigger hot update callback
```

**Affected Versions**: All versions

**Fixed Version**: 2.6.2

**Fix**: `ModuleManager` / `AdapterManager` register `config.set` (covers code `setConfig()` path) and `config.updated` (covers manual file editing path) event subscriptions, matching by configuration key prefix and calling the corresponding component's `on_config_update`, passing type-safe configuration objects. Also fix `_flush_config()` not synchronizing `_config_mtime` after writing files, avoiding framework self-writing being misjudged as external modification and repeatedly triggering `config.updated`.

**Compatibility Note**: Configuration hot update is now centrally maintained by the framework core. Previously, the configuration management panel triggered it on behalf of the framework, which has been removed; after upgrading the framework, the configuration management panel must also be upgraded, otherwise double triggering (core + panel) will occur. The `on_config_update` method signature and semantics remain unchanged, subclasses do not need modification.

**Fix Date**: 2026/07/23

**Severity**: 🟡 Medium

**Type**: Configuration system

---

### [BUG-026] notice/request event reply target inference error

**Issue**: When calling `event.reply()` in a group notice event (e.g., member joining a group `group_member_increase`), the message is sent to the user who triggered the event's private chat, not to the group where the event occurred. The same applies to friend notice events, where the reply target may be incorrect.

**Cause**: `infer_receive_type()` directly returns the event's `detail_type` as the session type. For message events, this is correct (`detail_type` values `private`/`group` are session types), but for notice/request events, `detail_type` is a semantic subtype (e.g., `group_member_increase`, `friend_increase`), not a session type. Subsequent `convert_to_send_type()` and `get_id_field()` cannot find the value in the mapping table, defaulting to `"user"` / `"user_id"`, causing the reply target to be incorrect.

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

**Fix**: `infer_receive_type()` adds a check—`detail_type` is only returned directly if it is a known session type (standard or custom type); otherwise, the session type is inferred based on the ID field (`group_id` / `channel_id` / `user_id`, etc.).

**Regression Tests**: `tests/unit/test_unit_session_type.py` → `TestNoticeRequestTypeInference` (10 test cases)

**Fix Date**: 2026/07/29

**Severity**: 🟢 Minor

**Type**: Event system

---

### [BUG-027] Route rate-limiting cleanup task uses fixed window causing long-window rules to fail

**Issue**: When route rate-limiting is configured with a long window rule (e.g., `100/hour`, `{"requests": 100, "window": 3600}`), the rate-limiting is ineffective—practically behaving like `100/minute` (up to ~6000 requests per hour), failing to provide the expected hourly protection.

**Cause**: `_apply_rate_limit` parses the actual `window` per route (up to 3600 seconds), and per-request checks use this window; however, the background cleanup task `_cleanup_expired_rate_limits` uses a fixed constant `DEFAULT_RATE_LIMIT_WINDOW_SECS` (60 seconds) as the unified cleanup threshold for all routes. Thus, entries older than 60 seconds are cleared early, preventing the accumulation of nearly 100 entries within the hour window, severely weakening the rate-limiting.

**Root Cause Chain**:
```
_apply_rate_limit parses window=3600 (100/hour)
  → per-request checks use 3600s retention time (correct)
  → but _cleanup_expired_rate_limits uses fixed max_window=60s for cleanup
    → timestamps older than 60s are cleared
      → within the hour window, only recent 1 minute's records remain
        → 100/hour effectively degrades to ~100/minute (relaxed by ~60x)
```

**Affected Versions**: 2.6.0-dev.0 - 2.7.0-dev.4

**Fixed Version**: 2.7.0-dev.5

**Fix**: Added `_rate_limit_windows: dict[str, int]` to record each route's actual window by store key; `_apply_rate_limit` writes the window on first entry creation; `_cleanup_expired_rate_limits` cleans up by each key's own window (fallback to default if missing); cleanup and deletion of entries and `stop()` synchronize maintenance of both dictionaries.

**Fix Date**: 2026/07/31

**Regression Tests**: `tests/unit/test_unit_router.py` → `TestRateLimit::test_cleanup_respects_per_route_window`

**Severity**: 🔴 Critical

**Type**: Routing

---

### [BUG-029] Configuration listener broadcasts incomplete TOML and silently swallows exceptions

**Issue**: When a user manually edits `config.toml` and saves it halfway (producing a temporary syntax error), the configuration listener background thread detects the mtime change, reloads the configuration, but fails to load and still broadcasts an empty configuration `{}` as `config.updated`, causing adapters/modules' `on_config_update` to receive an empty configuration, mistakenly assuming all configuration items have been cleared and reverting to default values. Additionally, the listener loop uses `except Exception: pass` to silently swallow all exceptions, making it impossible to troubleshoot watcher failures.

**Cause**: Two defects overlap:
1. `_load_config` overwrites `self._cache` to `{}` if TOML syntax/permission errors occur, but the background listener thread `_watch_loop` and cache timeout path `_check_cache_validity` call `_emit_config_updated()` unconditionally after `_load_config()`, broadcasting the "empty cache" produced by failed loading.
2. `_watch_loop`'s `except Exception` does not log any errors.

**Root Cause Chain**:
```
User saves halfway → TOML syntax error
  → _load_config() overwrites _cache = {}
    → _watch_loop unconditionally _emit_config_updated(new_config={})
      → Adapter/Module on_config_update receives empty config
        → Mistakes configuration as cleared, reverts to default values
```

**Affected Versions**: 2.6.2-dev.1 - 2.7.0-dev.4

**Fixed Version**: 2.7.0-dev.5

**Fix**:
1. `_load_config` changed to return `bool`; if TOML syntax/permission/other errors occur, **retain the last valid cache** (do not overwrite to `{}`), only record diagnostic logs and return `False`
2. `_watch_loop` and `_check_cache_validity` only emit `config.updated` if `_load_config()` returns `True`
3. `_watch_loop`'s `except Exception` changed to log at warning level (added i18n key `core.config.watcher_error`, synchronized for five languages)

**Fix Date**: 2026/07/31

**Regression Tests**: `tests/unit/test_unit_config.py` → `test_malformed_toml_preserves_last_valid_cache`, `test_permission_denied_logs_clear_message` (updated to verify cache retention and return False)

**Severity**: 🟡 Medium

**Type**: Configuration system

---

### [BUG-030] Configuration watcher race causes setConfig delay write to silently drop data

**Issue**: Multiple users reported that using `config.setConfig(key, value)` (default `immediate=False`) does not write their module configuration to `config.toml`, while other modules' configurations are normal. Setting `immediate=True` (force flush) can avoid this. The result is: configuration written during runtime is lost after the next restart, but the configuration generated during startup persists.

**Cause**: Two overlapping defects:
1. **Logical defect**: `_watch_loop` unconditionally `_dirty_keys.clear()` all pending keys when `_check_file_change()` returns `True`. But `_check_file_change()` only uses `!=` to compare mtime, and the framework's own `_flush_config` write also changes mtime—although `_flush_config` updates `_config_mtime` after writing, the watcher thread may still observe mtime differences between file write and mtime assignment (and on coarse-grained file systems), mistakenly identifying it as "external modification" and clearing all pending keys.
2. **Thread defect**: `_watch_loop` operates `_write_timer`/`_dirty_keys` without holding `_lock`, creating data races with `setConfig` (holds lock to write `_dirty_keys`), `_schedule_write` (holds lock to write `_write_timer`).

**Root Cause Chain**:
```
ModuleA setConfig(immediate=True) → flush writes, mtime changes
  → User module setConfig(immediate=False) → enters _dirty_keys, flushes in 5s
    → Watcher polls, _check_file_change observes mtime difference from previous self-write
      → _dirty_keys.clear() → User module's pending keys are silently dropped
        → Configuration missing after restart
```

**Affected Versions**: 2.6.0 - 2.7.0

**Fixed Version**: 2.7.1

**Fix**:
1. Added `_last_self_write_mtime` field; `_flush_config` records it after writing; `_check_file_change` first compares this value when mtime changes, matching indicates self-write returns `False`
2. `_watch_loop` holds `_lock` throughout; truly external modification retains `_dirty_keys` (merge semantics), next flush merges with external content (dirty keys first), no longer `clear()`
3. `getConfig`/`_check_cache_validity` paths are unaffected (their reload does not clear dirty keys)

**Fix Date**: 2026/08/06

**Regression Tests**: `tests/unit/test_unit_config.py` → `test_self_write_not_detected_as_external`, `test_external_change_preserves_dirty_keys`, `test_flush_merges_dirty_with_external`

**Severity**: 🔴 Critical

**Type**: Configuration system

---

### [BUG-032] Configuration delay write period "write-then-read" reads old values

**Issue**: After `config.setConfig()` (default `immediate=False` delay about 5 seconds flush), writing a dot-separated key and immediately reading its **parent/ancestor node** (e.g., `set_erispulse_section("scope.actions.MyModule", {...})` then calling `get_erispulse_config()`) returns the old value, the written sub-key "disappears", only visible after flush. Scenarios like scope configuration hot update ("write-read-write") are affected (2.8.0 test plugin `/t_section` use case exposed).

**Cause**: `setConfig` stores dot-separated keys as **flat** entries in the dirty queue `_dirty_keys`, only `getConfig`'s **exact key query** hits the dirty queue; tree-path queries (e.g., `getConfig("ErisPulse.scope")`) only walk the cache tree, not overlay dirty values—during the delay flush period (`_flush_config` merges dirty keys into cache and clears the queue), a read-you-write gap occurs.

**Affected Versions**: 2.6.0 - 2.8.0-dev.1

**Fixed Version**: 2.8.0-dev.1

**Fix**: `getConfig` introduces dirty overlay semantics—① exact hit in dirty key returns directly (original behavior unchanged); ② dirty key is the query key's ancestor → take the longest dirty ancestor and parse the remaining path in its value subtree; ③ dirty key is the query key's descendant → build an overlay subtree (`_dirty_overlay`) and deep merge with the cache subtree (`_deep_merge`, override priority, without modifying original cache object). When there is no dirty key, walk the original fast path, zero additional overhead.

**Fix Date**: 2026/09/04

**Regression Tests**: `tests/unit/test_unit_config.py` → `test_get_config_overlays_dirty_descendant`, `test_get_config_overlay_merges_with_cache_siblings`, `test_get_config_overlay_new_branch`, `test_get_config_dirty_ancestor_query`, `test_get_config_dirty_exact_key_still_wins`

**Severity**: 🟡 Medium

**Type**: Configuration system

---

### [BUG-033] wait_reply hung reply is starved by high-priority handlers

**Issue**: When a module calls `wait_reply()` to wait for a user reply, if that reply message is claimed by a higher-priority event handler (`mark_processed()`), the command dispatcher sees the `_processed` flag at entry and returns directly, leaving the reply matching logic at the end of `_handle_message` never executed—waiting parties receive no reply, only timeout and return `None`. Typical trigger scenario: robots using high-priority message handlers (recording/audit/blocking) have random failures in interactive conversations.

**Cause**: Reply matching `_check_pending_reply` is placed at the end of `_handle_message` (only executed if command does not match), while `_processed` checking is before it—claim checking and reply matching order are reversed. Interactive waiting is a framework-level session continuation mechanism, not a competing handler, and should not be affected by other handlers' claims.

**Affected Versions**: 2.2.0-dev.0 - 2.8.0-dev.1

**Fixed Version**: 2.8.0-dev.2

**Fix**: Move reply matching to the entry of `_handle_message` (before `_processed` checking, only for message events): first attempt to complete pending dialogue, if matched, the event is marked as processed, and subsequent checks naturally short-circuit; if not matched, continue the original command matching process. The judgment chain delegates to a new interaction session manager (`Core/Event/interaction.py`), gaining the ability to cancel by owner and recheck permissions.

**Fix Date**: 2026/09/08

**Regression Tests**: `tests/unit/test_unit_interaction.py` (TestRegisterResolve matched/unmatched/claimed flag), `tests/unit/test_unit_event.py` (full chain of wait_reply)

**Severity**: 🟡 Medium

**Type**: Event system / Command system

---

### [BUG-034] Scope persist=False runtime binding is silently overridden by subsequent configuration writes

**Issue**: `scope.set_module(..., persist=False)` and other runtime writes only modify memory `self._data`; but scope subscribes to `config.set` / `config.updated` events, and any code writing configuration (e.g., a module loading writes its own default configuration) triggers scope to rebuild the configuration tree from the configuration file, causing all previous runtime bindings to be silently lost (reverted to default allow), with no log prompts. Scenarios dependent on runtime bindings (Dashboard "runtime-only" switches, module runtime dynamic disabling) revert behavior after unrelated module configuration writes.

**Cause**: Root cause chain: `scope.set/delete(persist=False)` only writes memory (`Core/scope.py`) → any `setConfig` triggers `config.set` event → `_on_config_updated` unconditionally `_load_config()` → `_apply_tree()` replaces the persistent layer with `self._data = {...}` → runtime bindings not in the configuration file are discarded.

**Affected Versions**: 2.8.0-dev.1 - 2.8.0-dev.2
**Fixed Version**: 2.8.0-dev.2
**Fix**: Introduced a runtime override layer `_runtime_overrides` (with delete sentinel): `persist=False` write/delete records into the override layer, `_apply_tree()` rebuilds the persistent layer and replays in write order, runtime rules remain effective after any configuration write; `persist=True` write/delete clears corresponding override records (user persistence semantics take precedence); `config.set` filters by event key, `config.updated` compares new and old scope nodes, only rebuilds if scope actually changes (avoiding irrelevant writes flushing判定 LRU cache); added `unregister_by_owner()` for module unload to clean up with the caller. `Core.Event.overrides` has a similar issue with persist=False runtime overrides, fixed with the override layer architecture.
**Fix Date**: 2026/09/09

**Reproduction Steps**: ① `scope.set_module("testplat", blocked=["TestB"], persist=False)` →判定 False; ② any module executes `config.setConfig("HelpModule", {...})` → triggers scope rebuild; ③ `scope.is_allowed("testplat", None, "TestB")` returns True (expected still False).
**关联**: Issue #432
**Regression Tests**: `tests/unit/test_unit_scope.py::TestRuntimeOverrideSurvival` (irrelevant write survives/ tree rebuild replays/ delete sentinel/ persistence clears/ precise invalidation/ owner cleanup)

**Severity**: 🟡 Medium
**Type**: Configuration system / Runtime

---

### [BUG-035] Configuration panel select options and dict fields render as [object Object]

**Issue**: In the WebUI configuration panel, select field options dropdown displays `[object Object]` (e.g., dynamically generated color style options); dict fields (e.g., `stalker_mode`, `knowledge_base`, etc.) without declared control types display `[object Object]` in text boxes, making them impossible to view and edit.

**Cause**: Two independent defects: ① The framework's i18n resolver `_resolve_i18n_text` only restores dictionaries with an `i18n` key, so option labels as dictionaries with only `default` (no i18n key for dynamic text) are passed through as-is, and the frontend `esc(label)` string coercion results in `[object Object]`; ② Dashboard rendering branches only do JSON textarea for array types, dict values fall into the plain text input branch and are `String()` coerced. Additionally, if a module mistakenly declares `_schema_meta` as a regular dataclass field (missing `ClassVar` annotation), it will be treated as a configuration field, exacerbating confusion.

**Affected Versions**: 2.7.0 - 2.8.0-dev.2
**Fixed Version**: 2.8.0-dev.2
**Fix**: ① `_resolve_i18n_text` supports dictionaries with only `default` as text; ② framework schema/template/default value/filling/validation five places exclude fields with underscore prefix (harmless if mistakenly declared); ③ Dashboard select option label object fallback parsing (prioritize `default`), dict/table fields rendered as JSON textarea (save path as `tp=object` JSON.parse back, complete round trip).
**Fix Date**: 2026/09/09

**Regression Tests**: `tests/unit/test_unit_config.py::TestResolveI18nDefaultOnlyDict`, `TestSchemaUnderscoreFieldExclusion`

**Severity**: 🟡 Medium
**Type**: Configuration system

---

### [BUG-036] Multi-instance shared configuration directory causes occasional configuration write failures (ENOENT)

**Issue**: In Docker deployment scenarios (multiple containers mounting the same host configuration directory), log messages occasionally show two consecutive lines "Failed to write configuration file ... [Errno 2] No such file or directory: '...config.toml.tmp' -> '...config.toml'". This configuration write is discarded (the old configuration is fully preserved, no configuration loss is observed), functionality is unaffected, but repeated alerts interfere with troubleshooting, and pending configuration items must wait for the next write to persist.

**Cause**: Root cause chain: `_flush_config` / `setConfigTemplate` use a **fixed-name** temporary file `config.toml.tmp` to carry new content, `write()` without `fsync` directly `rename()` it. Two ErisPulse instances sharing the same configuration directory, B instance's `open("w")` may **truncate** A instance's ongoing temporary file → A's `rename` finds the target already taken or content truncated, reporting ENOENT (i.e., the user's log shows two consecutive error lines). In reported cases, only write failure alerts are observed (old configuration preserved); if the timing overlap is more extreme, `rename` might output an empty/half-written `config.toml` (a potential risk, not yet exploded in real environments). In single-instance scenarios, ext4's delayed allocation also has a "rename metadata before data block" crash window (SIGKILL / power loss). `_file_lock` is a process-level `threading.RLock`, providing no constraint for cross-process/cross-container writes.

**Affected Versions**: 2.2.0-dev.0 - 2.8.0

**Fixed Version**: 2.8.1

**Fix**: Configuration writes are unified to `_atomic_write_text()`: `mkstemp` generates a unique temporary file per process in the same directory (eliminating fixed-name contention, multiple instances degrade to last-writer-wins, no more ENOENT) → after writing, `flush + fsync` forces data to disk (eliminating the "rename effective, data not yet written" window) → `os.replace` atomically replaces the target (atomic on POSIX/Windows, at any moment the disk has either the complete old content or the complete new content); additional `fsync` on the configuration directory on POSIX. The three write points `_flush_config`, `setConfigTemplate`, and root directory configuration migration all switch; cleanup logic for abnormal paths is restructured with the unique temporary file name. Added **multi-instance detection**: on startup, an advisory lock (`flock` on POSIX / `msvcrt.locking` on Windows) exclusively holds a lock file `.erispulse_config.lock` in the configuration directory; if occupied, an i18n warning is output (does not block startup), the lock is automatically released by the OS when the process exits, with no ghost locks.

**Fix Date**: 2026/09/13

**Reproduction Steps**: ① Two containers mount the same host `config/` directory and run ErisPulse simultaneously; ② Any instance triggers a configuration write (e.g., module registers default configuration); ③ Observe log messages showing ENOENT write failure alerts, this write is discarded (old configuration preserved).

**关联**: User report (1Panel container ×2)

**Regression Tests**: `tests/unit/test_unit_config_atomic_write.py` (complete content write / no temporary file residue / write failure preserves original file / concurrent write of two instances always produces valid files / lock file creation / multi-instance warning / atomic write for migration)

**Severity**: 🟢 Minor

**Type**: Configuration system

---

### [BUG-037] Empty space command name registration never triggers

**Issue**: After registering a subcommand with a space-separated multi-token command name (e.g., `@command("admin add")`), the command can be registered and appears in the help list, but when users send `/admin add`, the robot never responds—the input is matched as the parent token command `admin` with argument `["add"]`; if the parent token is also unregistered, there is no response. Only when using dot-separated names (e.g., `admin.reload`, treated as a single token) can this be avoided.

**Cause**: Root cause chain: `CommandHandler.__call__` stores any command name (with spaces) as-is in the flattened `self.commands` dictionary → during dispatch, `_try_execute_command` only matches the first message token (`cmd_name = parts[0]`) → multi-token command names as dictionary keys are never found. The registration and matching phases have inconsistent assumptions about the command name space, and there is no registration-time warning (silent failure).

**Affected Versions**: From the introduction of the command system onwards - 2.8.0

**Fixed Version**: 2.8.1

**Fix**: The matching layer changes to **longest prefix matching**: starting from the longest candidate (`" ".join(parts[:n])`, with `n` capped by the maximum number of tokens in registered command names/aliases cached in `_max_name_tokens`), it tries matching step by step, and if matched, executes with the remaining tokens as arguments, with downstream effects (scope/ACL/overriding/master/permission chains) naturally applying to the full command name. Accompanying semantics: when parent and child commands coexist, unregistered subcommands fall back to the parent command (unchanged historical behavior); if a subcommand does not declare `permission`, it inherits the most recently declared ancestor command's permission (protecting the parent command protects all its subcommands); only when registering single-token commands is the first round matched, and the dispatch overhead is consistent with the original. `unregister` / `unregister_by_owner` / full cleanup also maintains the token count cache.

**Fix Date**: 2026/09/13

**Reproduction Steps**: ① Register `@command("admin add")` in a module; ② Send `/admin add x`; ③ Before the fix, there is no response (or it is caught by the registered `/admin` as a parameter), after the fix, `admin add` is triggered and `get_command_args()` is `["x"]`.

**Regression Tests**: `tests/unit/test_unit_command_subcommand.py` (longest prefix matching / only subcommand triggers / three-level nesting / case-sensitive two modes / single and multi-token aliases / event payload full name / lifecycle hooks full name / permission inheritance six examples / ACL glob full name / master / unregistration fallback and cache recalculation)

**Severity**: 🟡 Medium

**Type**: Event system