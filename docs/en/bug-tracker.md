# Bug Tracker

This document records known bugs of the ErisPulse SDK and their fixes, arranged in chronological order by the version in which they were fixed.

> **To the Reader**  
> No software is inherently perfect; even the most careful developers leave small errors. This tracker only includes issues that have a real impact on operation—those too minor to even reach the "minor" category will not appear here. While the number of "critical" items in the list may seem substantial, the purpose of publicly documenting these bugs is to make troubleshooting and retrospective analysis smoother, not to create anxiety: problems that can be seen, recorded, and fixed are proof that the project is continuously improving. Don't feel anxious when viewing this list; it is a troubleshooting tool, not a source of fear.

> **How to Read & Maintenance Guidelines**  
> - Each bug record includes structured fields such as problem description, root cause analysis, affected version range, and fix solution. It is recommended to check the "Affected Version" before upgrading to see if your current version is covered.  
> - If you need to add a new bug entry, please supplement content at the corresponding location, following the field specifications and severity/type classifications described below.

---

## Field Descriptions

### Required Fields

| Field | Description |
|------|------|
| **Problem** | The external manifestation of the bug, observable anomalies from the user's perspective. Try to provide error messages or typical scenarios |
| **Root Cause** | Root cause analysis, pointing to specific code defects (including "root cause chain" diagrams for complex scenarios) |
| **Affected Version** | The affected version range, in the format `introduced version - fixed version` (including dev versions) |
| **Fixed Version** | The specific version number that fixed the bug |
| **Fix Description** | A brief description of the fix, including key code changes |
| **Fix Date** | The release date of the corresponding fixed version, in `YYYY/MM/DD` format |
| **Severity** | Marked according to the "Severity Classification" below |
| **Type** | Marked according to the "Type Classification" below, can be combined (e.g., `Adapter / Router`) |

### Optional Fields

| Field | Description | Applicable Scenarios |
|------|------|---------|
| **Reproduction Steps** | The minimal reproducible path to trigger the bug | Complex bugs, occasional bugs are recommended to supplement |
| **关联** | Related Issue / PR / Commit links | Supplement when there are external discussion records |
| **Regression Test** | Test case location to verify the fix and prevent regression | Supplement when corresponding pytest cases are written |

---

## Severity Classification

| Identifier | Level | Judgment Criteria | Typical Manifestations |
|------|------|---------|---------|
| 🔴 | Critical | Causes process crash, data loss/damage, complete unavailability of core features, security vulnerabilities | OOM Kill, message cannot be sent, module cannot be loaded, hot reload failure |
| 🟡 | Medium | Functional abnormalities but with workaround paths, non-core function failures, occasional problems | Incorrect status judgment, repeated triggering, cache expiration, inaccurate error prompts |
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
| CLI | `epsdk` command, `init`/`run`/`install`, argument parsing, signal handling |
| Runtime | `sdk.run`/`restart`/`uninit`, lifecycle, signal, subprocess |

---

## Entry Template

When adding a new bug entry, follow the format below:

```markdown
### [BUG-XXX] Title

**Problem**: Problem description (error message or typical phenomenon)
**Root Cause**: Root cause analysis
**Affected Version**: Introduced version - Fixed version
**Fixed Version**: x.x.x
**Fix Description**: Fix solution
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
| 🔴 Critical | 15 |
| 🟡 Medium | 14 |
| 🟢 Minor | 2 |
| **Total** | **31** |

| Type | Count |
|------|------|
| Adapter | 6 |
| Configuration System | 7 |
| Event System | 6 |
| CLI | 3 |
| Storage | 3 |
| Loader | 3 |
| Router | 2 |
| Client | 1 |
| Runtime | 1 |

> Note: A single bug can belong to multiple types; the table above counts by primary type.

---

## Fixed Bugs

### [BUG-001] Event handler duplicate registration causing event to be processed multiple times

**Problem**: When registering handlers using multiple `@message` / `@notice` decorators, the same event is triggered multiple times, causing commands to be executed multiple times and logs to be output repeatedly.

**Root Cause**: `BaseEventHandler` lacks deduplication logic when registering handlers with the adapter event bus; each decorator mounts to the bus once, causing the event dispatcher to be called multiple times.

**Affected Version**: 2.2.0-dev.0 - 2.2.1-dev.0

**Fixed Version**: 2.2.1-dev.0

**Fix Description**: Optimize `BaseEventHandler` to ensure each event type is only registered once with the adapter, avoiding repeated triggering.

**Fix Date**: 2025/08/18

**Severity**: 🔴 Critical

**Type**: Event System

---

### [BUG-002] Init command adapter configuration path type error

**Problem**: When using the `ep init` command for interactive initialization, selecting the configuration adapter results in a type error:

```
Interactive initialization failed: unsupported operand type(s) for /: 'str' and 'str'
```

**Root Cause**: When adjusting the configuration file path in version 2.3.7, the method parameter types were inconsistent. `_configure_adapters_interactive_sync` receives a `str` type parameter but internally uses the `Path` `/` operator to concatenate paths.

**Affected Version**: 2.3.7 - 2.3.9-dev.1

**Fixed Version**: 2.3.9-dev.1

**Fix Description**: Change the parameter type of `_configure_adapters_interactive_sync` from `str` to `Path`, passing a `Path` object directly when calling.

**Fix Date**: 2026/03/23

**Severity**: 🟡 Medium

**Type**: CLI

---

### [BUG-003] Commands fail after restart

**Problem**: After calling `sdk.restart()`, commands registered via `@command` are not triggered, resulting in the robot not responding after sending a command.

**Root Cause**: After `adapter.shutdown()` clears the event bus, the `_linked_to_adapter_bus` status of `BaseEventHandler` is not reset to `False`, causing the `_process_event` method to think it has been mounted to the adapter bus and skip re-mounting.

**Affected Version**: 2.2.x - 2.4.0-dev.2

**Fixed Version**: 2.4.0-dev.3

**Fix Description**: Introduce `_linked_to_adapter_bus` status tracking; after `_clear_handlers()` disconnects from the bus, the next `register()` automatically re-mounts, adapting to shutdown/restart scenarios.

**Fix Date**: 2026/04/09

**Severity**: 🔴 Critical

**Type**: Event System

---

### [BUG-004] Lifecycle event handlers not cleared

**Problem**: After `sdk.restart()`, old lifecycle event handlers still exist and trigger repeatedly, causing the same event to be processed multiple times.

**Root Cause**: The `lifecycle._handlers` dictionary is never cleared in `uninit()`, causing old and new handlers to coexist after restart.

**Affected Version**: 2.3.0 - 2.4.0-dev.2

**Fixed Version**: 2.4.0-dev.3

**Fix Description**: Clear `lifecycle._handlers` at the end of the `Uninitializer` cleanup process (after all events are submitted).

**Fix Date**: 2026/04/09

**Severity**: 🟡 Medium

**Type**: Runtime

---

### [BUG-005] Event.is_friend_add/is_friend_delete detail_type inconsistent with OB12 standard

**Problem**: `Event.is_friend_add()` checks `detail_type == "friend_add"`, `Event.is_friend_delete()` checks `detail_type == "friend_delete"`, but OneBot12 standard defines `detail_type` values as `"friend_increase"` and `"friend_decrease"`. This inconsistency with the values used by `notice.py`'s `on_friend_add`/`on_friend_remove` decorators causes handlers registered via decorators to trigger, but corresponding `is_friend_add()`/`is_friend_delete()` judgment methods return `False`.

**Root Cause**: `wrapper.py` uses non-standard naming, while `notice.py` uses the correct OB12 standard naming.

**Affected Version**: Since implementation

**Fixed Version**: 2.4.2-dev.1

**Fix Description**: Change `is_friend_add()`'s matching value from `"friend_add"` to `"friend_increase"`, `is_friend_delete()` from `"friend_delete"` to `"friend_decrease"`.

**Fix Date**: 2026/04/13

**Severity**: 🟡 Medium

**Type**: Event System

---

### [BUG-006] adapter.clear() does not clear _started_instances causing incorrect status after restart

**Problem**: The `AdapterManager.clear()` method clears `_adapters`, `_adapter_info`, handlers, and `_bots`, but omits `_started_instances`. If `clear()` is called while the adapter is running, `_started_instances` retains dangling references, causing incorrect status judgment after restart.

**Root Cause**: When `_started_instances` was introduced in 2.4.0-dev.1, it was not cleared in `clear()`.

**Affected Version**: 2.4.0-dev.1 - 2.4.2-dev.0

**Fixed Version**: 2.4.2-dev.1

**Fix Description**: Add `self._started_instances.clear()` in the `clear()` method.

**Fix Date**: 2026/04/13

**Severity**: 🟡 Medium

**Type**: Adapter

---

### [BUG-007] command.wait_reply() uses deprecated asyncio.get_event_loop()

**Problem**: The `CommandHandler.wait_reply()` method uses `asyncio.get_event_loop()` to create futures and get timestamps, which has been deprecated in Python 3.10+. In asynchronous contexts, `asyncio.get_running_loop()` should be used. This is inconsistent with `wrapper.py`'s `wait_for()` method, which uses `get_running_loop()`.

**Root Cause**: The old API was used during development, and the newly added `wait_for()` used the correct API but did not retroactively fix the old code.

**Affected Version**: 2.3.0-dev.0

**Fixed Version**: 2.4.2-dev.1

**Fix Description**: Replace the two `asyncio.get_event_loop()` calls in `command.py` with `asyncio.get_running_loop()`.

**Fix Date**: 2026/04/13

**Severity**: 🟢 Minor

**Type**: Event System

---

### [BUG-008] Bot offline events are repeatedly submitted during shutdown

**Problem**: When calling `adapter.shutdown()` to shut down all adapters, `_update_bot_status()` repeatedly submits Bot offline events during the shutdown process, causing the same batch of Bots to be marked offline multiple times and triggering multiple `adapter.bot.offline` lifecycle events.

**Root Cause**: The Bot status tracking system introduced in 2.4.0-dev.1 did not set a "shutting down" flag during `shutdown()`, so `_update_bot_status()` could not distinguish between normal offline and cascading offline during shutdown.

**Affected Version**: 2.4.0-dev.1 - 2.4.2-dev.1

**Fixed Version**: 2.4.2-dev.1

**Fix Description**: Add `_is_being_shutdown` flag in `AdapterManager`; set to True at the start of `shutdown()` and clear at the end; `_update_bot_status()` skips repeated submissions during shutdown after checking this flag.

**Fix Date**: 2026/04/21

**Severity**: 🟡 Medium

**Type**: Adapter

---

### [BUG-009] LazyModule synchronous access to BaseModule causes incomplete initialization

**Problem**: When users access properties of a lazily loaded BaseModule in a synchronous context, the module uses `loop.create_task()` for asynchronous initialization but does not wait, causing the property access to possibly occur before initialization is complete, leading to race conditions.

**Root Cause**: `_ensure_initialized()` uses `loop.create_task(self._initialize())` and returns immediately without ensuring initialization is complete.

**Affected Version**: 2.4.0-dev.0 - 2.4.2-dev.1

**Fixed Version**: 2.4.2-dev.2

**Fix Description**: In synchronous contexts, BaseModule initialization is changed to use `asyncio.run(self._initialize())` to ensure initialization is complete before returning. The transparent proxy feature is maintained, and users do not need to be aware of the difference between synchronous and asynchronous contexts.

**Fix Date**: 2026/04/21

**Severity**: 🟡 Medium

**Type**: Loader

---

### [BUG-010] Multi-threaded write to configuration system causes data loss

**Problem**: In a multi-threaded environment, if multiple threads call `config.setConfig()` simultaneously, the `_flush_config()` read-modify-write operation is not atomic, potentially causing partial write loss.

**Root Cause**: Although `_flush_config()` uses `RLock`, there is no file lock protection between file read and write, and the Timer in `_schedule_write` may be triggered multiple times, causing overwrite.

**Affected Version**: 2.3.0 - 2.4.2-dev.1

**Fixed Version**: 2.4.2-dev.2

**Fix Description**:
1. Add file lock mechanism (`_file_lock`) to ensure atomic file operations
2. Use temporary file write and atomic rename (`os.replace`/`os.rename`)
3. Improve `_schedule_write` Timer cancellation and re-scheduling logic

**Fix Date**: 2026/04/21

**Severity**: 🔴 Critical

**Type**: Configuration System

---

### [BUG-011] Windows Ctrl+C cannot stop the program

**Problem**: When running `python main.py` directly on Windows, pressing Ctrl+C does not terminate the program. After the program starts normally and outputs the routing server information, Ctrl+C has no response, and the process can only be forcibly killed via Task Manager. However, it can be stopped normally when started via `epsdk run`—but `epsdk run` runs through a subprocess model.

**Root Cause**: The Hypercorn ASGI server's `serve()` function internally registers its own SIGINT handler via `signal.signal(SIGINT, handler)`, overriding Python's default `KeyboardInterrupt` handling mechanism. When Hypercorn is started as a background task via `asyncio.create_task()`, its internal shutdown process cannot be triggered normally (because it expects the `worker_serve` mode), causing the Ctrl+C signal to be swallowed by Hypercorn but not triggering any cleanup actions.

**Affected Version**: 2.3.6 - 2.4.2

**Fixed Version**: 2.4.3-dev.0

**Fix Description**:
1. Switch the ASGI server from Hypercorn to Uvicorn (`pyproject.toml` dependency change)
2. Start the server directly using `uvicorn.Server._serve()` and **bypass** the `capture_signals()` signal handling context manager
3. Implement graceful shutdown via `server.should_exit = True`, and cancel the background task if timeout occurs
4. Synchronously remove the subprocess running model and `runtime/cleanup.py` cleanup module (no longer need subprocess cleanup mechanism)

**Fix Date**: 2026/04/28

**Severity**: 🔴 Critical

**Type**: CLI / Runtime

---

### [BUG-012] Hot restart does not load updated module code

**Problem**: After executing `sdk.restart()` soft restart, the new code (such as new API routes) of modules/adapters upgraded via `epsdk install` does not take effect, and old logic is still executed. The latest code must be loaded by completely restarting the process.

**Root Cause**: `_do_restart()` reinitializes by calling `entry_point.load()`, but this function returns cached old module objects from `sys.modules` instead of reloading from disk.

**Affected Version**: Early versions - 2.4.3-dev.1

**Fixed Version**: 2.4.3-dev.1

**Fix Description**: Clear the cache of loaded modules/adapters from `sys.modules` before `init()` after `uninit()`, so that `entry_point.load()` loads the latest code from disk. Add `_collect_top_level_modules()` and `_invalidate_module_cache()` helper methods to derive top-level module names via `top_level.txt` or entry-point value.

**Fix Date**: 2026/05/03

**Severity**: 🔴 Critical

**Type**: Loader / Runtime

---

### [BUG-013] Module loading strategy sorting logic error

**Problem**: `ModuleLoadStrategy` provides a `priority` field to declare module initialization priority, but the loading strategy implementation has an error, causing modules to be initialized in an unexpected order instead of the expected priority order. When modules have initialization dependencies, they cannot ensure correct initialization order through `priority`.

**Root Cause**: The sorting logic in the loading strategy implementation is incorrect; `initialize_modules()` does not sort the module list by `priority`.

**Affected Version**: 2.3.4 - 2.4.5-dev.2

**Fixed Version**: 2.4.5-dev.3

**Fix Description**: Before traversing in `initialize_modules()`, sort the module list by `priority` in descending order. Modules with the same priority maintain their original relative order (stable sort).

**Fix Date**: 2026/05/15

**Severity**: 🟡 Medium

**Type**: Loader

---

### [BUG-014] Adapter middleware returning None causes event data loss

**Problem**: During the execution of OneBot12 middleware chains in `adapter.emit()`, if a middleware returns `None` (e.g., forgetting to `return data`), subsequent middleware and all event handlers receive `processed_data` as `None`, causing event processing to fail completely.

**Root Cause**: The middleware chain implementation `processed_data = await middleware(processed_data)` does not check if the return value is `None`, directly overwriting the result of the previous step.

**Affected Version**: unknown - 2.4.5-dev.3

**Fixed Version**: 2.4.5-dev.4

**Fix Description**: When middleware returns `None`, ignore the return value, keep the original data, and output a warning-level log.

**Fix Date**: 2026/05/15

**Severity**: 🔴 Critical

**Type**: Adapter / Event System

---

### [BUG-015] Configuration file path depends on working directory

**Problem**: The configuration file path in `ConfigManager` is a relative path `"config/config.toml"` by default, and is resolved using `os.getcwd()` at runtime. If the working directory changes during runtime (e.g., via `os.chdir()`), file read/write operations will point to the wrong location, causing configuration loss or reading old data.

**Root Cause**: In `__init__`, the relative path is directly stored without being resolved to an absolute path at initialization.

**Affected Version**: 2.3.7 - 2.4.5-dev.3

**Fixed Version**: 2.4.5-dev.4

**Fix Description**: In `ConfigManager.__init__()`, if the passed path is relative, automatically resolve it to an absolute path using `os.path.abspath()`.

**Fix Date**: 2026/05/15

**Severity**: 🟡 Medium

**Type**: Configuration System

---

### [BUG-016] BaseStorage confuses storing value None with non-existent key

**Problem**: `BaseStorage.get_multi()` / `__getattr__()` cannot distinguish between "key does not exist" and "key's value is None", and when a user explicitly stores `None`, it is treated as if the key does not exist upon retrieval.

**Root Cause**: The value retrieval logic directly uses `value is None` to determine if the key exists, lacking an independent "missing" marker.

**Affected Version**: Early versions - 2.4.6-dev.6

**Fixed Version**: 2.4.6-dev.6

**Fix Description**: Introduce `_SENTINEL` sentinel value to distinguish between "key does not exist" and "value is None", no longer confusing them.

**Fix Date**: 2026/06/07

**Severity**: 🟡 Medium

**Type**: Storage

---

### [BUG-017] WebSocket route auto_accept flag lost after service restart

**Problem**: After a service restart (such as `sdk.restart()`), the `auto_accept` configuration for all WebSocket routes reverts to `False`, and connections that were expected to be automatically accepted remain pending, with clients receiving no response for a long time, resulting in WS connections hanging.

**Root Cause**: `_restore_routes_from_records()` hardcodes `auto_accept` as `False` when restoring routes from persistent records, without reading the original record's value; also, when the route storage tuple was extended from a binary to a ternary tuple, the restore logic was not synchronized.

**Affected Version**: 2.3.8-dev.0 - 2.4.6-dev.6

**Fixed Version**: 2.4.6-dev.6

**Fix Description**: The route storage tuple is extended to `(handler, auth_handler, auto_accept)`, and `_restore_routes_from_records()` reads the real `auto_accept` value from the record instead of hardcoding `False`.

**Fix Date**: 2026/06/07

**Severity**: 🔴 Critical

**Type**: Router

---

### [BUG-018] HTTP/WS client concurrent calls cause crashes and connection leaks

**Problem**: The HTTP and WebSocket clients in `Core/client.py` have multiple stability defects in concurrent scenarios, leading to connection leaks or process crashes:
- Multiple coroutines concurrently calling `ClientWebSocket.receive()` cause aiohttp to throw `Concurrent call to receive() is not allowed`
- Concurrent calls to `_get_http_session()` / `_get_ws_session()` may create multiple sessions, and `_drain_sessions()` does not close old connections, causing connection leaks
- The exception handling order in `request()` is incorrect: `except ClientConnectionError` (ErisPulse exception) is never triggered, aiohttp connection errors are caught by generic `except Exception`, causing the "retry + session reinitialization" logic (dead code) to never execute
- `send_json()` ignores the `mode="binary"` parameter; `_get_ws_session()` does not pass default request headers

**Root Cause**: The client's initial implementation (2.4.6-dev.5) lacks concurrency protection and exception classification, handling aiohttp exception hierarchy and ErisPulse custom exception inheritance relationships improperly.

**Affected Version**: 2.4.6-dev.5 - 2.4.8

**Fixed Version**: 2.4.8

**Fix Description**:
1. Add `_recv_lock` to serialize all `receive()` / `receive_text()` / `receive_bytes()` calls
2. Add `_session_lock` to protect session creation; `_drain_sessions()` is changed to an asynchronous method and truly closes old sessions
3. Refactor `request()` exception handling order: `asyncio.TimeoutError` → `aiohttp.ClientConnectionError` (triggers session reinitialization) → `aiohttp.ClientError` → `ClientError` (transparent pass) → `Exception`
4. Fix `send_json()`'s mode handling, `_get_ws_session()` default request header pass, `close()` concurrency race, `HttpResponse.__aexit__` duplicate `release()`

**Fix Date**: 2026/06/12

**Severity**: 🔴 Critical

**Type**: Client

---

### [BUG-019] Adapter hot reload causes route conflicts and reload failure

**Problem**: When a third-party module (such as Dashboard) triggers adapter hot reload, or when adapter startup fails and retries, old routes (such as `onebot11_default`) are not cleared, causing `WebSocket path ... already registered` conflicts and reload failures. A complete process restart is required to restore.

**Root Cause**: `AdapterManager.shutdown()` only clears routes via `unregister_all_by_namespace(platform)`, but adapters (such as OneBot11) register WebSocket routes with `onebot11_{account_name}` as the namespace, resulting in a granularity mismatch and an empty cleanup; startup failure retry paths also do not clear the previous route residue.

**Affected Version**: Early versions - 2.4.9

**Fixed Version**: 2.4.9

**Fix Description**:
1. Route registration automatically tracks `owner → namespace` ownership relationships via `current_owner` ContextVar
2. Add `unregister_all_by_owner(owner)`, stopping/restarting simultaneously clears by owner, covering fine-grained namespaces
3. Add `_stop_adapter(platform)` primitive ("stop equals cleanup"), binding stopping an adapter with reclaiming its registered resources in a single call, `restart()` and startup failure retry both go through this entry
4. Add framework-level `adapter.restart(platform)` API, third-party modules should call this method instead of directly operating adapter instances

**Fix Date**: 2026/06/12

**Severity**: 🔴 Critical

**Type**: Adapter / Router

---

### [BUG-020] Subprocess mode `ep run <script>` cannot find sub-packages in script's directory

**Problem**: When running a script using `ep r .\main.py` in non-hot-reload mode, if the script has relative imports (such as `from qg import ...`), it reports `No module named 'qg'`. However, the `--reload` mode works normally.

**Root Cause**: The non-hot-reload mode directly calls `runpy.run_path()` to execute the script, which does not automatically add the script's directory to `sys.path`. In contrast, the `--reload` mode runs through `subprocess.Popen` subprocess, which automatically inherits the current working directory, so `sys.path[0]` is the script's directory, allowing normal operation.

**Affected Version**: 2.5.0 - 2.5.2-dev.0

**Fixed Version**: 2.5.2-dev.0

**Fix Description**: Before calling `runpy.run_path()`, manually insert the script's directory into `sys.path[0]`.

**Fix Date**: 2026/06/27

**Severity**: 🟡 Medium

**Type**: CLI

---

### [BUG-021] SQL query builder rejects valid wildcard and list expressions

**Problem**: `SQLiteQueryBuilder`'s `_build_select_sql()` validates all SELECT columns using `_validate_identifier()`, which uses a strict whitelist regex `^[a-zA-Z_][a-zA-Z0-9_]*$`, causing legitimate SQL syntax to be mistakenly judged as unsafe column names:

- `SELECT *` — `*` is a standard SQL wildcard
- `SELECT COUNT(*)` — aggregate function
- `SELECT users.name` — qualified column name
- `SELECT col AS alias` — column alias

Among these, `Select("*")` is used by modules like Cron, causing module `on_load` execution to fail and the module to fail to load.

**Root Cause**: In version 2.4.6, SQL injection protection was enhanced by introducing `_validate_identifier()` whitelist validation. This validation is applied to all column names, but does not distinguish between read-side (SELECT/ORDER BY) and write-side (INSERT/UPDATE). SELECT columns allow complex SQL expressions and should not be restricted by simple identifier whitelists.

**Affected Version**: 2.4.6 - 2.5.2-dev.1

**Fixed Version**: 2.5.2-dev.2

**Fix Description**: Change the SELECT/ORDER BY column validation from whitelist mode to blacklist mode:
1. Add `_validate_select_column()` function, only blocking SQL injection dangerous characters (`;` `'` `"` `--` `/*` `*/` `\x00` newline)
2. Allow any valid SQL column expression (`*`, `table.*`, `table.column`, `COUNT(*)`, `col AS alias`, etc.)
3. INSERT/UPDATE column names still maintain strict whitelist validation (only allow simple identifiers)

**Fix Date**: 2026/06/29

**Severity**: 🔴 Critical

**Type**: Storage

---

### [BUG-022] _resolve_account() account resolution regression (_accounts_data not populated)

**Problem**: After the 2.5.2 configuration system refactoring, multi-account adapters declaring `AccountConfigClass` report `ValueError("未声明 AccountConfigClass，无法解析账户")` when calling methods like `wait_reply`, `reply` that require sending messages. Even if the adapter correctly configures multi-account information, account resolution still fails.

**Root Cause**: In 2.5.2-dev.5, `_load_accounts()` (responsible for reading configuration + validation + populating `_accounts_data`) was refactored into `_ensure_accounts_exist()` (only generates configuration template), but `_resolve_account()` still checks `self._accounts_data is None`. Since `_ensure_accounts_exist()` no longer populates `_accounts_data`, this attribute remains `None`, causing `_resolve_account()` to prematurely return `(None, None)`, and account resolution completely fails downstream.

**Root Cause Chain**:
```
_load_accounts() was deleted
  → __init__ no longer populates _accounts_data
    → _accounts_data is always None
      → _resolve_account() checks _accounts_data is None → return (None, None)
        → downstream places calling _resolve_account (e.g. call_api) get None
          → triggers error
```

**Affected Version**: 2.5.2-dev.5 - 2.5.2

**Fixed Version**: 2.5.3

**Fix Description**: In `BaseAdapter.__init__`, after `_ensure_accounts_exist()`, restore the population of `_accounts_data`:
```python
if self.AccountConfigClass is not None:
    self._ensure_accounts_exist()
    self._accounts_data = self.accounts  # restore population, data source is real-time read accounts property
```
The `_resolve_account()` logic remains unchanged, fully backward compatible:
- Adapters that do not declare `AccountConfigClass`: `_accounts_data` remains `None` → return `(None, None)`
- Adapters that declare `AccountConfigClass`: `_accounts_data` is populated → normal resolution
- Adapters that overwrite `_load_accounts` or manually set `_accounts_data`: override in `super().__init__()` later, highest priority

**Fix Date**: 2026/07/07

**Severity**: 🔴 Critical

**Type**: Adapter / Configuration System

---

### [BUG-023] Account configuration modification does not refresh adapter cache, causing account resolution failure

**Problem**: After users modify multi-account adapter account configurations (such as filling in tokens) via Dashboard, the adapter still uses old cached data, and calling message-sending-related methods reports `未找到可用账户 (account_id=default)`. A process restart is required to make the new configuration take effect.

**Root Cause**: `_accounts_data` is only read from the configuration storage once during `BaseAdapter.__init__()`, and is never refreshed afterward. `AdapterManager._run_adapter()` and `restart()` do not re-read account configuration before calling `adapter.start()`, causing the cache and actual configuration to be out of sync.

**Affected Version**: 2.4.6 - 2.5.4

**Fixed Version**: 2.5.4

**Fix Description**: In `AdapterManager._run_adapter()` and `restart()`, before calling `adapter.start()`, refresh `adapter._accounts_data = adapter.accounts` to ensure the latest configuration is used on each startup.

**Fix Date**: 2026/07/09

**Severity**: 🔴 Critical

**Type**: Adapter / Configuration System

---

### [BUG-024] storage.set() writing large numeric ID keys triggers OOM Kill

**Problem**: When calling `storage.set()` to write a nested key path containing a large pure numeric field (such as QQ group ID `871684833`), the process is killed by container OOM (exit code -9), and the service crashes and cannot recover.

**Root Cause**: In the recursive implementation of `_set_nested_value`, pure numeric fields in the nested key path are mistakenly identified as list indices by `isdigit()`, triggering `current.extend([None] * (index - len(current) + 1))`, attempting to allocate hundreds of millions of elements, instantly exhausting memory.

**Root Cause Chain**:
```
Key path contains pure numeric field (such as group ID 871684833)
  → isdigit() mistakenly identifies as array index
    → extend([None] * (871684833 - len(current) + 1))
      → attempts to allocate hundreds of millions of elements
        → memory exhausted → container OOM Kill (exit code -9)
```

**Affected Version**: 2.5.1 - 2.5.5

**Fixed Version**: 2.5.5

**Fix Description**:
1. Always use dictionaries when pre-creating intermediate layers, never guess container type based on whether the next segment is a number
2. Only when the container itself is a list and the index is less than `STORAGE_MAX_LIST_INDEX` (10000) do we handle it by index, skipping large indices safely
3. Change the recursive implementation to an iterative one, eliminating potential infinite recursion risks in the original code
4. Add `STORAGE_MAX_LIST_INDEX` constant to `Core/constants.py`, centrally managing the index safety upper limit

**Fix Date**: 2026/07/10

**Reproduction Steps**:
```python
# Writing a nested key path containing a large number field (such as QQ group ID) triggers OOM
await sdk.storage.aset("groups.871684833.name", "某群")
# → Process memory surges instantly, killed by OOM
```

**Regression Tests**: `tests/unit/test_unit_storage.py` adds 4 new regression test cases
- `test_nested_key_numeric_segment_as_dict_key` — precisely reproduces the OOM scenario
- `test_nested_key_numeric_segment_multiple` — multiple consecutive number fields as dictionary keys
- `test_nested_key_existing_list_index_set_within_limit` — existing list index write within limit
- `test_nested_key_list_index_safety_limit` — safety limit verification for large index

**Severity**: 🔴 Critical

**Type**: Storage

---

### [BUG-025] on_config_update callback not called by core router

**Problem**: `on_config_update(old, new)` is defined in the base class (`BaseModule` / `BaseAdapter`), but the framework core does not associate it with configuration change events. The actual manifestation: when modifying configuration through the configuration management panel, it can be triggered, but when manually editing `config.toml` or calling `setConfig()` programmatically, `on_config_update` is not triggered.

**Root Cause**: `ConfigManager` emits `config.set` / `config.updated` lifecycle events when configuration changes, but lacks the subscription logic to forward these events to each component's `on_config_update` method.

**Root Cause Chain**:
```
Core does not subscribe to config.set / config.updated
  → Configuration change events are not forwarded
    → on_config_update is not called
      → Manual file editing / code setConfig does not trigger hot update callback
```

**Affected Version**: All versions

**Fixed Version**: 2.6.2

**Fix Description**: `ModuleManager` / `AdapterManager` registers subscriptions for `config.set` (covering code `setConfig()` path) and `config.updated` (covering manual file editing path), matches by configuration key prefix, and calls the corresponding component's `on_config_update`, passing type-safe configuration objects. Also fixes `_flush_config()` not synchronizing `_config_mtime` after writing the file, preventing the framework's own write from being mistakenly detected as an external modification by the file monitoring task and repeatedly triggering `config.updated`.

**Compatibility Note**: Configuration hot update is now centrally maintained by the framework core. Previously, the logic of triggering by the configuration management panel has been removed, and after upgrading the framework, the configuration management panel must also be upgraded synchronously, otherwise repeated triggering will occur (core + panel each trigger once). The `on_config_update` method signature and semantics remain unchanged, and subclasses do not need modification.

**Fix Date**: 2026/07/23

**Severity**: 🟡 Medium

**Type**: Configuration System

---

### [BUG-026] notice/request event reply target inferred incorrectly

**Problem**: When calling `event.reply()` in a group notification event (such as member joining a group `group_member_increase`), the message is sent to the user who triggered the event's private chat, rather than to the group where the event occurred. The same applies to friend notification events, where the reply target may be incorrect.

**Root Cause**: `infer_receive_type()` directly returns the event's `detail_type` as the session type. For message events, this is correct (the `detail_type` values `private`/`group` are the session types), but for notice/request events, the `detail_type` is a semantic subtype (such as `group_member_increase`, `friend_increase`), not the session type. Subsequent `convert_to_send_type()` and `get_id_field()` lookups in the mapping table do not find the value, defaulting to `"user"` / `"user_id"`, causing the reply target to be incorrect.

**Root Cause Chain**:
```
notice event detail_type="group_member_increase"
  → infer_receive_type() directly returns "group_member_increase"
    → convert_to_send_type("group_member_increase") not in mapping table → default to "user"
    → get_id_field("group_member_increase") not in mapping table → default to "user_id"
      → target_id = event["user_id"]  ← new member's private chat (not the group)
```

**Affected Version**: All versions

**Fixed Version**: 2.7.0-dev.3

**Fix Description**: `infer_receive_type()` adds a check—`detail_type` is only returned directly if it is a known session type (standard or custom type); otherwise, the correct session type is inferred based on the ID field (`group_id` / `channel_id` / `user_id`, etc.).

**Regression Tests**: `tests/unit/test_unit_session_type.py` → `TestNoticeRequestTypeInference` (10 test cases)

**Fix Date**: 2026/07/29

**Severity**: 🟢 Minor

**Type**: Event System

---

### [BUG-027] Route rate limiter cleanup task uses fixed window causing long window rate limit rules to fail

**Problem**: When setting route rate limiting rules to long windows (such as `100/hour`, `{"requests": 100, "window": 3600}`), the rate limiting is ineffective—manifesting as approximately `100/minute` (up to about 6000 requests per hour), completely failing to provide the intended hourly protection.

**Root Cause**: `_apply_rate_limit` parses the actual `window` (up to 3600 seconds) for each route, and per-request checks do use this window; however, the background cleanup task `_cleanup_expired_rate_limits` uses a fixed constant `DEFAULT_RATE_LIMIT_WINDOW_SECS` (60 seconds) as the unified cleanup threshold for all routes. Thus, time stamps earlier than 60 seconds are cleared by the cleanup task, preventing the accumulation of nearly 100 records within the hour window, severely weakening the rate limiting.

**Root Cause Chain**:
```
_apply_rate_limit parses window=3600 (100/hour)
  → per-request checks use 3600s retention time (correct)
  → but _cleanup_expired_rate_limits uses fixed max_window=60s to clean
    → 60s old time stamps are all cleared
      → the hour window only retains records from the last 1 minute
        → 100/hour actually degrades to ~100/minute (relaxed by about 60 times)
```

**Affected Version**: 2.6.0-dev.0 - 2.7.0-dev.4

**Fixed Version**: 2.7.0-dev.5

**Fix Description**: Add `_rate_limit_windows: dict[str, int]` to record the actual window for each route by store key; `_apply_rate_limit` writes the window on first creation of an entry; `_cleanup_expired_rate_limits` is changed to clean by each key's own window (fallback to default if missing); cleanup deletion and `stop()` synchronize maintenance of both dictionaries.

**Fix Date**: 2026/07/31

**Regression Tests**: `tests/unit/test_unit_router.py` → `TestRateLimit::test_cleanup_respects_per_route_window`

**Severity**: 🔴 Critical

**Type**: Router

---

### [BUG-029] Configuration listener broadcasts incomplete TOML and silently swallows exceptions

**Problem**: When users manually edit `config.toml` and save it halfway (producing a temporary syntax error), the configuration monitoring background thread detects a change in mtime, reloads the configuration, but fails to load and still emits an empty configuration `{}` via the `config.updated` event, causing adapters/modules' `on_config_update` to receive an empty configuration and mistakenly assume all configuration items have been cleared and revert to default values. Additionally, the listener loop uses `except Exception: pass` to silently swallow all exceptions, making it impossible to diagnose watcher faults.

**Root Cause**: Two defects overlap:
1. `_load_config` overwrites `self._cache` as `{}` when TOML syntax errors/permission errors occur, but the background listener thread `_watch_loop` and cache timeout path `_check_cache_validity` both unconditionally execute `_emit_config_updated()` after calling `_load_config()`, broadcasting the "empty cache from failed load" as a real change.
2. `_watch_loop`'s `except Exception: pass` does not log any exceptions.

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

**Fix Description**:
1. `_load_config` is changed to return `bool`; when TOML syntax errors/permission errors/other errors occur, it **retains the last valid cache** (no longer overwrites as `{}`), only logs diagnostic messages and returns `False`
2. `_watch_loop` and `_check_cache_validity` only emit `config.updated` when `_load_config()` returns `True`
3. `_watch_loop`'s `except Exception` is changed to log at warning level (new i18n key `core.config.watcher_error`, synchronized in five languages)

**Fix Date**: 2026/07/31

**Regression Tests**: `tests/unit/test_unit_config.py` → `test_malformed_toml_preserves_last_valid_cache`, `test_permission_denied_logs_clear_message` (updated to verify cache retention and return False)

**Severity**: 🟡 Medium

**Type**: Configuration System

---

### [BUG-030] Configuration watcher race condition causes setConfig delayed write to silently drop data

**Problem**: Multiple users report that after using `config.setConfig(key, value)` (default `immediate=False`), their module configuration is not written to `config.toml`, while other modules' configurations are normal. Setting `immediate=True` (force flush) can avoid this. Manifestation: configuration written at runtime is lost after the next restart, while configuration generated at startup via template is retained.

**Root Cause**: Two overlapping defects:
1. **Logical defect**: `_watch_loop` unconditionally `_dirty_keys.clear()` all dirty keys when `_check_file_change()` returns `True`. But `_check_file_change()` only uses `!=` to compare mtime, and the framework's own `_flush_config` write also changes mtime—although `_flush_config` updates `_config_mtime` after writing, the watcher thread may still observe the mtime difference (and on coarse-grained filesystems) between file write and mtime assignment, mistakenly identifying it as "external modification" and clearing all dirty keys.
2. **Thread defect**: `_watch_loop` operates `_write_timer`/`_dirty_keys` without holding `_lock`, competing with `setConfig` (holding lock to write `_dirty_keys`), `_schedule_write` (holding lock to write `_write_timer`) for data.

**Root Cause Chain**:
```
Module A setConfig(immediate=True) → flush writes, mtime changes
  → User module setConfig(immediate=False) → enters _dirty_keys, flushes after 5s
    → Watcher polling, _check_file_change observes mtime difference from previous self-write
      → _dirty_keys.clear() → Dirty keys of user module are silently dropped
        → Configuration missing after restart
```

**Affected Version**: 2.6.0 - 2.7.0

**Fixed Version**: 2.7.1

**Fix Description**:
1. Add `_last_self_write_mtime` field; `_flush_config` records it after writing; `_check_file_change` compares it first when mtime changes, if matches, identifies as self-write and returns `False`
2. `_watch_loop` holds `_lock` throughout; retains `_dirty_keys` on true external modification (merge semantics), merges next flush with external content (dirty keys take precedence), no longer `clear()`
3. `getConfig`/`_check_cache_validity` path is unaffected (its reload does not clear dirty keys)

**Fix Date**: 2026/08/06

**Regression Tests**: `tests/unit/test_unit_config.py` → `test_self_write_not_detected_as_external`, `test_external_change_preserves_dirty_keys`, `test_flush_merges_dirty_with_external`

**Severity**: 🔴 Critical

**Type**: Configuration System

---

### [BUG-032] Configuration delay write causes "write-then-read" to read old values

**Problem**: After `config.setConfig()` (default `immediate=False` delay for about 5 seconds) writes a dot-separated key, immediately reading its **parent/ancestor node** (such as `set_erispulse_section("scope.actions.MyModule", {...})` followed by `get_erispulse_config()`) returns the old value, the written sub-key "disappears" until the flush, affecting scenarios like configuration hot update with "write-read-write" (exposed by test plugin `/t_section` use case in 2.8.0).

**Root Cause**: `setConfig` stores dot-separated keys in the dirty queue `_dirty_keys` in **flat form**, only `getConfig`'s **exact key query** hits the dirty queue; tree-path queries (`getConfig("ErisPulse.scope")`) only go through the cache tree, not overlaying dirty values—during the delay write (`_flush_config` merges dirty keys into the cache and clears the queue), a read-you-write gap forms.

**Affected Version**: 2.6.0 - 2.8.0-dev.1

**Fixed Version**: 2.8.0-dev.1

**Fix Description**: `getConfig` introduces dirty overlay semantics—① exact match dirty key returns directly (original behavior unchanged); ② dirty key is the query key's ancestor → take the longest dirty ancestor, parse the remaining path in its value subtree; ③ dirty key is the query key's descendant → construct an overlay subtree (`_dirty_overlay`) and deep merge with the cache subtree (`_deep_merge`, override priority, not modifying the original cache object). Without dirty keys, the fast path is taken, zero additional overhead.

**Fix Date**: 2026/09/04

**Regression Tests**: `tests/unit/test_unit_config.py` → `test_get_config_overlays_dirty_descendant`, `test_get_config_overlay_merges_with_cache_siblings`, `test_get_config_overlay_new_branch`, `test_get_config_dirty_ancestor_query`, `test_get_config_dirty_exact_key_still_wins`

**Severity**: 🟡 Medium

**Type**: Configuration System

---

### [BUG-033] wait_reply hangs and is starved by high-priority processors

**Problem**: While a module calls `wait_reply()` waiting for user reply, if that reply message is claimed by a higher-priority event processor (`mark_processed()`), the command dispatcher sees the `_processed` flag at the entrance and returns directly, never executing the reply matching logic at the end of the dispatcher—waiting parties receive no reply and can only wait until timeout returns `None`. Typical trigger scenario: robots using high-priority message processors (recording/auditing/blocking classes), all dialog interactions randomly fail.

**Root Cause**: Reply matching `_check_pending_reply` is placed at the end of `_handle_message` (only executed if command is not matched), while `_processed` checking is before it—the order of claim check and reply match judgment is reversed. Interaction waiting is a framework-level session continuation mechanism, not a competing processor, and should not be affected by other processors' claim.

**Affected Version**: 2.2.0-dev.0 - 2.8.0-dev.1

**Fixed Version**: 2.8.0-dev.2

**Fix Description**: Move reply match judgment to the entrance of `_handle_message` (before `_processed` check, only for message events): first try to complete the pending conversation, if matched, the event is marked as processed, and the subsequent checks naturally short-circuit; if not matched, continue the original command matching process. The judgment chain delegates to a new interaction session manager (`Core/Event/interaction.py`), incidentally gaining ability to cancel by affiliation and permission review.

**Fix Date**: 2026/09/08

**Regression Tests**: `tests/unit/test_unit_interaction.py` (TestRegisterResolve match/not match/claim flag), `tests/unit/test_unit_event.py` (full chain of wait_reply)

**Severity**: 🟡 Medium

**Type**: Event System / Command System