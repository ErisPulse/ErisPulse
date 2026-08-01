# Bug Tracker

This document records the known bugs of the ErisPulse SDK and their fixes, arranged in chronological order by the release version.

> **For Readers**
> No software is born perfect; even the most careful developers leave small mistakes. This tracker includes only issues that have a practical impact on operation—those that are too minor, not even reaching the "minor" level, will not appear here. Although the list contains many "critical" items, the original purpose of publicly documenting these bugs is to make troubleshooting and tracing smoother, not to create anxiety: issues that are visible, recorded, and fixed are themselves proof that the project is continuously improving. Seeing this list should not cause panic; it is a troubleshooting tool, not a source of fear.

> **How to Read & Maintenance Guidelines**
> - Each bug entry includes structured fields such as problem description, root cause analysis, affected version range, and fix solution. It is recommended to check the "affected version" before upgrading to see if it covers the current version.
> - If you need to add a new bug entry, please supplement the content at the corresponding location, following the field specifications and severity/type classification below.

---

## Field Descriptions

### Required Fields

| Field | Description |
|------|------|
| **Problem** | The external manifestation of the bug, the abnormal phenomenon observable by the user. Try to provide error messages or typical scenarios |
| **Cause** | Root cause analysis, pointing to specific code defects (including "root cause chain" diagrams for complex scenarios) |
| **Affected Version** | The affected version range, in the format `introduced version - fixed version` (including both dev versions) |
| **Fixed Version** | The specific version number that fixed the bug |
| **Fix Content** | A brief description of the fix solution, including key code changes |
| **Fix Date** | The release date of the corresponding fixed version, in `YYYY/MM/DD` format |
| **Severity** | Marked according to the "Severity Classification" below |
| **Type** | Marked according to the "Type Classification" below, can be combined (e.g., `Adapter / Routing`) |

### Optional Fields

| Field | Description | Applicable Scenarios |
|------|------|---------|
| **Reproduction Steps** | The minimal reproducible path to trigger the bug | Suggest supplementing for complex or sporadic bugs |
| **关联** | Related Issue / PR / Commit links | Supplement when there are external discussion records |
| **Regression Test** | Test case locations to verify the fix and prevent regression | Supplement when corresponding pytest cases are written |

---

## Severity Classification

| Identifier | Level | Judgment Criteria | Typical Manifestations |
|------|------|---------|---------|
| 🔴 | Critical | Causes process crash, data loss/damage, complete unavailability of core functions, security vulnerabilities | OOM Kill, message cannot be sent, module cannot be loaded, hot reload failure |
| 🟡 | Medium | Function anomaly but with workaround, non-core function failure, sporadic issues | Incorrect status judgment, repeated trigger, cache expiration, inaccurate error prompts |
| 🟢 | Minor | Does not affect core functions, only code quality or experience issues, potential risks not yet triggered | Deprecated API, dead code, missing warning logs |

---

## Type Classification

| Type | Coverage Range |
|------|---------|
| Configuration System | `ConfigManager`, configuration read/write, configuration Schema, hot update |
| Event System | `Event` module (command/message/notice/request/meta), event dispatch, handler registration |
| Adapter | `AdapterManager`, `BaseAdapter`, account parsing, Bot status, middleware |
| Routing | `RouterManager`, HTTP/WebSocket/SSE routing, rate limiting, CORS |
| Client | `HttpClient`, `ClientWebSocket`, aiohttp wrapper |
| Storage | `StorageManager`, SQLite, SQL builder, nested keys |
| Loading System | `Loader`, `LazyModule`, `ModuleInitializer`, strict mode, module discovery |
| CLI | `epsdk` command, `init`/`run`/`install`, parameter parsing, signal handling |
| Runtime | `sdk.run`/`restart`/`uninit`, lifecycle, signal, subprocess |

---

## Entry Template

When adding a new bug entry, please follow the following format:

```markdown
### [BUG-XXX] Title

**Problem**: Problem description (error message or typical phenomenon)
**Cause**: Root cause analysis
**Affected Version**: Introduced version - Fixed version
**Fixed Version**: x.x.x
**Fix Content**: Fix solution
**Fix Date**: YYYY/MM/DD

<!-- Optional fields -->
**Reproduction Steps**: (Suggest supplementing for complex bugs)
**关联**: (Issue/PR links)
**Regression Test**: (Test case path)

**Severity**: 🔴 Critical | 🟡 Medium | 🟢 Minor
**Type**: Configuration System / Event System / Adapter / Routing / Client / Storage / Loading System / CLI / Runtime
```

---

## Statistical Overview

| Severity | Count |
|--------|------|
| 🔴 Critical | 14 |
| 🟡 Medium | 12 |
| 🟢 Minor | 2 |
| **Total** | **28** |

| Type | Count |
|------|------|
| Adapter | 6 |
| Configuration System | 5 |
| Event System | 5 |
| CLI | 3 |
| Storage | 3 |
| Loading System | 3 |
| Routing | 2 |
| Client | 1 |
| Runtime | 1 |

> Note: A single bug can belong to multiple types, the table above counts by primary type.

---

## Fixed Bugs

### [BUG-001] Event handler duplicate registration causes event to be processed multiple times

**Problem**: When using multiple `@message` / `@notice` decorators to register handlers, the same event is triggered multiple times, causing the command to be executed multiple times and logs to be output repeatedly.

**Cause**: `BaseEventHandler` lacks deduplication logic when registering handlers with the adapter event bus; each decorator mounts once to the bus, causing multiple calls during event dispatch.

**Affected Version**: 2.2.0-dev.0 - 2.2.1-dev.0

**Fixed Version**: 2.2.1-dev.0

**Fix Content**: Optimize `BaseEventHandler` to ensure each event type registers only once with the adapter, avoiding repeated triggers.

**Fix Date**: 2025/08/18

**Severity**: 🔴 Critical

**Type**: Event System

---

### [BUG-002] Init command adapter configuration path type error

**Problem**: When using the `ep init` command for interactive initialization, selecting the configuration adapter results in a type error:

```
Interactive initialization failed: unsupported operand type(s) for /: 'str' and 'str'
```

**Cause**: When adjusting the configuration file path in version 2.3.7, the method parameter types were inconsistent. `_configure_adapters_interactive_sync` receives `str` type parameters, but internally uses the `Path` `/` operator to concatenate paths.

**Affected Version**: 2.3.7 - 2.3.9-dev.1

**Fixed Version**: 2.3.9-dev.1

**Fix Content**: Change the parameter type of the `_configure_adapters_interactive_sync` method from `str` to `Path`, and directly pass `Path` objects when calling.

**Fix Date**: 2026/03/23

**Severity**: 🟡 Medium

**Type**: CLI

---

### [BUG-003] Commands fail after restart

**Problem**: After calling `sdk.restart()`, commands registered via `@command` cannot be triggered, manifested as the robot being unresponsive after sending a command.

**Cause**: After `adapter.shutdown()` clears the event bus, the `_linked_to_adapter_bus` status of `BaseEventHandler` is not reset to `False`, causing the `_process_event` method to believe it has been mounted to the adapter bus and skips re-mounting.

**Affected Version**: 2.2.x - 2.4.0-dev.2

**Fixed Version**: 2.4.0-dev.3

**Fix Content**: Introduce `_linked_to_adapter_bus` status tracking; after `_clear_handlers()` disconnects the bus, `register()` automatically re-mounts next time, adapting to shutdown/restart scenarios.

**Fix Date**: 2026/04/09

**Severity**: 🔴 Critical

**Type**: Event System

---

### [BUG-004] Lifecycle event handlers not cleaned up

**Problem**: After `sdk.restart()`, old lifecycle event handlers still exist and are repeatedly triggered, causing the same event to be processed multiple times.

**Cause**: The `lifecycle._handlers` dictionary is never cleared during `uninit()`, causing old and new handlers to coexist after restart.

**Affected Version**: 2.3.0 - 2.4.0-dev.2

**Fixed Version**: 2.4.0-dev.3

**Fix Content**: Clear `lifecycle._handlers` at the end of the `Uninitializer` cleanup process (after all events are submitted).

**Fix Date**: 2026/04/09

**Severity**: 🟡 Medium

**Type**: Runtime

---

### [BUG-005] Event.is_friend_add/is_friend_delete's detail_type inconsistent with OB12 standard

**Problem**: `Event.is_friend_add()` checks `detail_type == "friend_add"`, `Event.is_friend_delete()` checks `detail_type == "friend_delete"`, but OneBot12 standard defines `detail_type` values as `"friend_increase"` and `"friend_decrease"`. This inconsistency with the values used in `notice.py`'s `on_friend_add`/`on_friend_remove` decorators causes the corresponding `is_friend_add()`/`is_friend_delete()` judgment methods to return `False` when handlers registered via decorators are triggered.

**Cause**: `wrapper.py` uses non-standard naming, while `notice.py` uses correct OB12 standard naming.

**Affected Version**: From implementation to present

**Fixed Version**: 2.4.2-dev.1

**Fix Content**: Change `is_friend_add()`'s matching value from `"friend_add"` to `"friend_increase"`, `is_friend_delete()` from `"friend_delete"` to `"friend_decrease"`.

**Fix Date**: 2026/04/13

**Severity**: 🟡 Medium

**Type**: Event System

---

### [BUG-006] adapter.clear() does not clean up _started_instances, causing incorrect status after restart

**Problem**: The `AdapterManager.clear()` method clears `_adapters`, `_adapter_info`, handlers, and `_bots`, but omits `_started_instances`. If `clear()` is called while the adapter is running, `_started_instances` retains dangling references, leading to incorrect status after restart.

**Cause**: When `_started_instances` was introduced in 2.4.0-dev.1, it was not synchronized for cleanup in `clear()`.

**Affected Version**: 2.4.0-dev.1 - 2.4.2-dev.0

**Fixed Version**: 2.4.2-dev.1

**Fix Content**: Add `self._started_instances.clear()` in the `clear()` method.

**Fix Date**: 2026/04/13

**Severity**: 🟡 Medium

**Type**: Adapter

---

### [BUG-007] command.wait_reply() uses deprecated asyncio.get_event_loop()

**Problem**: The `CommandHandler.wait_reply()` method uses `asyncio.get_event_loop()` to create futures and get timestamps. This method has been deprecated in Python 3.10+, and `asyncio.get_running_loop()` should be used in asynchronous contexts. It is inconsistent with `wait_for()` in `wrapper.py` which uses `get_running_loop()`.

**Cause**: The old API was used during development, and the newly added `wait_for()` uses the correct API but old code was not retroactively fixed.

**Affected Version**: 2.3.0-dev.0

**Fixed Version**: 2.4.2-dev.1

**Fix Content**: Replace `asyncio.get_event_loop()` with `asyncio.get_running_loop()` in two places in `command.py`.

**Fix Date**: 2026/04/13

**Severity**: 🟢 Minor

**Type**: Event System

---

### [BUG-008] Bot offline event is repeatedly submitted during shutdown

**Problem**: When calling `adapter.shutdown()` to close all adapters, `_update_bot_status()` repeatedly submits Bot offline events during the shutdown process, causing the same batch of Bots to be marked offline multiple times and triggering multiple `adapter.bot.offline` lifecycle events.

**Cause**: The Bot status tracking system introduced in 2.4.0-dev.1 did not set a "shutting down" flag during `shutdown()`, so `_update_bot_status()` cannot distinguish normal offline from cascading offline during shutdown.

**Affected Version**: 2.4.0-dev.1 - 2.4.2-dev.1

**Fixed Version**: 2.4.2-dev.1

**Fix Content**: Add `_is_being_shutdown` flag in `AdapterManager`, set to True at the start of `shutdown()` and cleared at the end; `_update_bot_status()` checks this flag and skips repeated submissions during shutdown.

**Fix Date**: 2026/04/21

**Severity**: 🟡 Medium

**Type**: Adapter

---

### [BUG-009] LazyModule synchronous access to BaseModule leads to incomplete initialization

**Problem**: When users access properties of a lazily loaded BaseModule in a synchronous context, the module uses `loop.create_task()` for asynchronous initialization but does not wait, causing the property access to possibly be incomplete and leading to race conditions.

**Cause**: `_ensure_initialized()` uses `loop.create_task(self._initialize())` and returns immediately without ensuring initialization is complete.

**Affected Version**: 2.4.0-dev.0 - 2.4.2-dev.1

**Fixed Version**: 2.4.2-dev.2

**Fix Content**: In synchronous contexts, BaseModule initialization is changed to use `asyncio.run(self._initialize())` to ensure initialization is complete before returning. The transparent proxy feature is maintained, and users do not need to perceive the difference between synchronous and asynchronous contexts.

**Fix Date**: 2026/04/21

**Severity**: 🟡 Medium

**Type**: Loading System

---

### [BUG-010] Multi-threaded configuration system write leads to data loss

**Problem**: In a multi-threaded environment, when multiple threads call `config.setConfig()` simultaneously, the `_flush_config()` read-modify-write operation is not atomic, potentially leading to partial write loss.

**Cause**: Although `_flush_config()` uses `RLock`, there is no file lock protection between file read and write, and the Timer of `_schedule_write` may be triggered multiple times, causing overwrite.

**Affected Version**: 2.3.0 - 2.4.2-dev.1

**Fixed Version**: 2.4.2-dev.2

**Fix Content**:
1. Add file locking mechanism (`_file_lock`) to ensure atomic file operations
2. Write to a temporary file and then atomically rename (using `os.replace`/`os.rename`)
3. Improve `_schedule_write` Timer cancellation and rescheduling logic

**Fix Date**: 2026/04/21

**Severity**: 🔴 Critical

**Type**: Configuration System

---

### [BUG-011] Ctrl+C cannot stop program on Windows

**Problem**: When running `python main.py` directly on Windows, pressing Ctrl+C does not terminate the program. After the program starts normally and outputs the routing server information, Ctrl+C has no response, and the process can only be forcibly killed via the task manager. However, stopping via `epsdk run` works normally—though `epsdk run` runs through a subprocess model.

**Cause**: The `serve()` function of the Hypercorn ASGI server internally registers its own SIGINT handler via `signal.signal(SIGINT, handler)`, overriding Python's default `KeyboardInterrupt` handling mechanism. When Hypercorn is started as a background task via `asyncio.create_task()`, its internal shutdown process cannot be triggered normally (because it expects the `worker_serve` mode), causing the Ctrl+C signal to be swallowed by Hypercorn but not triggering any cleanup actions.

**Affected Version**: 2.3.6 - 2.4.2

**Fixed Version**: 2.4.3-dev.0

**Fix Content**:
1. Switch the ASGI server from Hypercorn to Uvicorn (`pyproject.toml` dependency change)
2. Start the server directly using `uvicorn.Server._serve()`, **bypassing** the `capture_signals()` signal handling context manager
3. Implement graceful shutdown via `server.should_exit = True`, and cancel the background task on timeout
4. Synchronously remove the subprocess running model and the `runtime/cleanup.py` cleanup module (subprocess cleanup mechanism is no longer needed)

**Fix Date**: 2026/04/28

**Severity**: 🔴 Critical

**Type**: CLI / Runtime

---

### [BUG-012] Updated module Python code not effective after hot restart

**Problem**: After executing `sdk.restart()` for a soft restart, the new code (such as new API routes) of modules/adapters upgraded via `epsdk install` does not take effect and still runs the old logic. The latest code can only be loaded by completely restarting the process.

**Cause**: `_do_restart()` calls `entry_point.load()` during re-initialization, but this function returns a cached old module object from `sys.modules` rather than reloading from disk.

**Affected Version**: Early versions - 2.4.3-dev.1

**Fixed Version**: 2.4.3-dev.1

**Fix Content**: Clear the cache of loaded modules/adapters in `sys.modules` after `uninit()` and before `init`, so `entry_point.load()` loads the latest code from disk. Add auxiliary methods `_collect_top_level_modules()` and `_invalidate_module_cache()` to deduce top-level module names via `top_level.txt` or entry-point value.

**Fix Date**: 2026/05/03

**Severity**: 🔴 Critical

**Type**: Loading System / Runtime

---

### [BUG-013] Module loading strategy sorting logic error

**Problem**: `ModuleLoadStrategy` provides a `priority` field to declare the initialization priority of modules, but the implementation of the loading strategy has an error, causing modules to be initialized not in the expected priority order but in the default order of `entry_points()`. When modules have loading dependencies, the correct initialization order cannot be ensured through `priority`.

**Cause**: The sorting logic in the loading strategy implementation is incorrect, and `initialize_modules()` does not sort the module list by `priority`.

**Affected Version**: 2.3.4 - 2.4.5-dev.2

**Fixed Version**: 2.4.5-dev.3

**Fix Content**: Sort the module list by `priority` in descending order before traversing `initialize_modules()`. Modules with the same priority maintain their original relative order (stable sorting).

**Fix Date**: 2026/05/15

**Severity**: 🟡 Medium

**Type**: Loading System

---

### [BUG-014] Adapter middleware returning None causes event data loss

**Problem**: When executing the OneBot12 middleware chain in `adapter.emit()`, if a middleware returns `None` (e.g., forgetting to `return data`), the subsequent middleware and all event handlers receive `processed_data` as `None`, causing event processing to fail completely.

**Cause**: The middleware chain implementation `processed_data = await middleware(processed_data)` does not check if the return value is `None`, directly overwriting the result from the previous step.

**Affected Version**: unknown - 2.4.5-dev.3

**Fixed Version**: 2.4.5-dev.4

**Fix Content**: Ignore the return value if middleware returns `None`, retain the original data and pass it on, and output a warning-level log.

**Fix Date**: 2026/05/15

**Severity**: 🔴 Critical

**Type**: Adapter / Event System

---

### [BUG-015] Configuration file path depends on working directory

**Problem**: The configuration file path of `ConfigManager` defaults to a relative path `"config/config.toml"`, which is resolved at runtime using `os.getcwd()`. If the working directory changes during runtime (e.g., via `os.chdir()`), the read/write operations of the configuration file point to the wrong location, leading to configuration loss or reading old data.

**Cause**: The relative path is directly stored in `__init__` without being resolved to an absolute path at initialization.

**Affected Version**: 2.3.7 - 2.4.5-dev.3

**Fixed Version**: 2.4.5-dev.4

**Fix Content**: In `ConfigManager.__init__()`, if the passed path is a relative path, automatically resolve it to an absolute path using `os.path.abspath()`.

**Fix Date**: 2026/05/15

**Severity**: 🟡 Medium

**Type**: Configuration System

---

### [BUG-016] BaseStorage confuses storing value None with key not existing

**Problem**: `BaseStorage.get_multi()` / `__getattr__()` cannot distinguish between "key not existing" and "key's value is None", treating a user explicitly stored `None` as if the key does not exist.

**Cause**: The value retrieval logic directly uses `value is None` to determine if a key exists, lacking an independent "missing" marker.

**Affected Version**: Early versions - 2.4.6-dev.6

**Fixed Version**: 2.4.6-dev.6

**Fix Content**: Introduce `_SENTINEL` sentinel value to distinguish between "key not existing" and "value is None", so they are no longer confused.

**Fix Date**: 2026/06/07

**Severity**: 🟡 Medium

**Type**: Storage

---

### [BUG-017] WebSocket route auto_accept flag lost after service restart

**Problem**: After a service restart (such as `sdk.restart()`), the `auto_accept` configuration of all WebSocket routes changes back to `False`. Connections that were expected to be automatically accepted become suspended, and clients do not receive responses for a long time, manifesting as a stuck WebSocket connection.

**Cause**: `_restore_routes_from_records()` hardcodes `False` for `auto_accept` when restoring routes from persistent records, without reading the original record's value; also, when the route storage tuple expanded from a binary tuple to a ternary tuple, the restoration logic was not synchronized.

**Affected Version**: 2.3.8-dev.0 - 2.4.6-dev.6

**Fixed Version**: 2.4.6-dev.6

**Fix Content**: The route storage tuple expands to `(handler, auth_handler, auto_accept)`, and `_restore_routes_from_records()` reads the real `auto_accept` value from the record instead of hardcoding `False`.

**Fix Date**: 2026/06/07

**Severity**: 🔴 Critical

**Type**: Routing

---

### [BUG-018] HTTP/WS client concurrent calls cause crash and connection leak

**Problem**: The HTTP and WebSocket clients in `Core/client.py` have multiple stability defects in concurrent scenarios, leading to connection leaks or process crashes:
- Multiple coroutines calling `ClientWebSocket.receive()` concurrently cause aiohttp to throw `Concurrent call to receive() is not allowed`
- Concurrent calls to `_get_http_session()` / `_get_ws_session()` may create multiple sessions, and `_drain_sessions()` does not close old connections, causing connection leaks
- The exception handling order in `request()` is incorrect: `except ClientConnectionError` (ErisPulse exception) is never triggered, aiohttp connection errors are caught by the general `except Exception`, causing the "retry + session reinitialization" logic (dead code) to never execute
- `send_json()` ignores the `mode="binary"` parameter; `_get_ws_session()` does not pass default request headers

**Cause**: The initial implementation of the client (2.4.6-dev.5) lacks concurrent protection and exception classification, and improperly handles the relationship between aiohttp exception system and ErisPulse custom exceptions.

**Affected Version**: 2.4.6-dev.5 - 2.4.8

**Fixed Version**: 2.4.8

**Fix Content**:
1. Add `_recv_lock` to serialize all `receive()` / `receive_text()` / `receive_bytes()` calls
2. Add `_session_lock` to protect session creation; `_drain_sessions()` is changed to an async method and truly closes old sessions
3. Refactor `request()` exception handling order: `asyncio.TimeoutError` → `aiohttp.ClientConnectionError` (triggers session reinitialization) → `aiohttp.ClientError` → `ClientError` (transparent) → `Exception`
4. Fix `send_json()` mode handling, default request header transmission in `_get_ws_session()`, concurrent race condition in `close()`, and repeated `release()` in `HttpResponse.__aexit__`

**Fix Date**: 2026/06/12

**Severity**: 🔴 Critical

**Type**: Client

---

### [BUG-019] Adapter hot reload causes route conflicts and reload failure

**Problem**: When a third-party module (such as Dashboard) triggers adapter hot reload, or when an adapter fails to start and retries, the old routes (such as `onebot11_default`) registered in the previous session are not cleared, causing a `WebSocket path ... already registered` conflict and resulting in reload failure. A complete process restart is required to recover.

**Cause**: `AdapterManager.shutdown()` only clears routes with `unregister_all_by_namespace(platform)`, but adapters (such as OneBot11) register WebSocket routes with `onebot11_{account_name}` as the namespace, resulting in a granularity mismatch and making the cleanup an empty operation; route cleanup on failed startup retries also fails to clear the previous route residue.

**Affected Version**: Early versions - 2.4.9

**Fixed Version**: 2.4.9

**Fix Content**:
1. Automatically track `owner → namespace` ownership relationships during route registration via `current_owner` ContextVar
2. Add `unregister_all_by_owner(owner)`, stopping/restarting adapters clears by owner, covering fine-grained namespaces
3. Add the primitive `_stop_adapter(platform)` ("stop equals cleanup"), binding stopping adapters and reclaiming their registered resources in one call, `restart()` and failed startup retries both go through this entry
4. Add framework-level `adapter.restart(platform)` API, third-party modules should call this method instead of directly operating adapter instances

**Fix Date**: 2026/06/12

**Severity**: 🔴 Critical

**Type**: Adapter / Routing

---

### [BUG-020] Subprocess mode `ep run <script>` cannot find subpackages in script directory

**Problem**: When running a script using `ep r .\main.py` in non-hot-reload mode, if the script has relative imports (such as `from qg import ...`), it reports a `No module named 'qg'` error. However, the `--reload` mode works normally.

**Cause**: The non-hot-reload mode directly calls `runpy.run_path()` to execute the script, which does not automatically add the script's directory to `sys.path`. In contrast, the `--reload` mode runs via `subprocess.Popen` subprocess, which automatically inherits the current working directory, making `sys.path[0]` the script's directory, so it works normally.

**Affected Version**: 2.5.0 - 2.5.2-dev.0

**Fixed Version**: 2.5.2-dev.0

**Fix Content**: Before calling `runpy.run_path()`, manually insert the script's directory into `sys.path[0]`.

**Fix Date**: 2026/06/27

**Severity**: 🟡 Medium

**Type**: CLI

---

### [BUG-021] SQL query builder rejects valid wildcard and list expressions

**Problem**: `SQLiteQueryBuilder`'s `_build_select_sql()` calls `_validate_identifier()` for all SELECT columns, which uses a strict whitelist regex `^[a-zA-Z_][a-zA-Z0-9_]*$`, causing legitimate SQL syntax to be wrongly judged as unsafe column names:

- `SELECT *` — `*` is a standard SQL wildcard
- `SELECT COUNT(*)` — aggregate function
- `SELECT users.name` — qualified column name
- `SELECT col AS alias` — column alias

Among them, `Select("*")` is used by modules like Cron, causing module `on_load` execution to fail and the module cannot be loaded.

**Cause**: In version 2.4.6, SQL injection protection was enhanced, introducing `_validate_identifier()` whitelist validation. This validation applies to all column names but does not distinguish between read-side (SELECT/ORDER BY) and write-side (INSERT/UPDATE). SELECT columns allow complex SQL expressions and should not be restricted by simple identifier whitelists.

**Affected Version**: 2.4.6 - 2.5.2-dev.1

**Fixed Version**: 2.5.2-dev.2

**Fix Content**: Change the column validation for SELECT/ORDER BY from whitelist mode to blacklist mode:
1. Add `_validate_select_column()` function, which only blocks SQL injection dangerous characters (`;` `'` `"` `--` `/*` `*/` `\x00` newline)
2. Allow any valid SQL column expression (`*`, `table.*`, `table.column`, `COUNT(*)`, `col AS alias`, etc.)
3. INSERT/UPDATE column names still maintain strict whitelist validation (only allow simple identifiers)

**Fix Date**: 2026/06/29

**Severity**: 🔴 Critical

**Type**: Storage

---

### [BUG-022] _resolve_account() account resolution regression (_accounts_data not populated)

**Problem**: After the 2.5.2 configuration system refactoring, multi-account adapters declaring `AccountConfigClass` report an error `ValueError("AccountConfigClass not declared, cannot resolve account")` when calling methods like `wait_reply`, `reply` that require sending messages. Even if the adapter correctly configures multi-account information, account resolution still fails.

**Cause**: In 2.5.2-dev.5, `_load_accounts()` (responsible for reading configuration + validating + populating `_accounts_data`) was refactored into `_ensure_accounts_exist()` (only generates configuration template), but `_resolve_account()` still checks `self._accounts_data is None`. Since `_ensure_accounts_exist()` no longer populates `_accounts_data`, this attribute remains `None`, causing `_resolve_account()` to prematurely return `(None, None)`, and account resolution completely fails.

**Root Cause Chain**:
```
_load_accounts() was deleted
  → __init__ no longer populates _accounts_data
    → _accounts_data is always None
      → _resolve_account() checks _accounts_data is None → return (None, None)
        → downstream places calling _resolve_account() (e.g. call_api) get None
          → trigger error
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
- Adapters not declaring `AccountConfigClass`: `_accounts_data` remains `None` → return `(None, None)`
- Adapters declaring `AccountConfigClass`: `_accounts_data` is populated → normal resolution
- Adapters overwriting `_load_accounts` or manually setting `_accounts_data`: overwrite after `super().__init__()` with highest priority

**Fix Date**: 2026/07/07

**Severity**: 🔴 Critical

**Type**: Adapter / Configuration System

---

### [BUG-023] Adapter cache not refreshed after account configuration change causing account resolution failure

**Problem**: After users modify the account configuration of a multi-account adapter (such as filling in the token) via Dashboard, the adapter still uses the old cache, and calling message-sending-related methods reports `No available account (account_id=default)`. The process must be restarted to make the new configuration take effect.

**Cause**: `_accounts_data` is only read from the configuration storage once in `BaseAdapter.__init__`, and is never refreshed afterwards. `AdapterManager._run_adapter()` and `restart()` do not re-read the account configuration before calling `adapter.start()`, causing the cache to be out of sync with the actual configuration.

**Affected Version**: 2.4.6 - 2.5.4

**Fixed Version**: 2.5.4

**Fix Content**: In `AdapterManager._run_adapter()` and `restart()`, before calling `adapter.start()`, refresh `adapter._accounts_data = adapter.accounts`, ensuring the latest configuration is used each time the adapter starts.

**Fix Date**: 2026/07/09

**Severity**: 🔴 Critical

**Type**: Adapter / Configuration System

---

### [BUG-024] storage.set() writing large numeric ID keys triggers OOM Kill

**Problem**: When calling `storage.set()` to write a nested key path containing a large numeric field (such as QQ group ID `871684833`), the process is OOM killed (exit code -9), causing the service to crash and become unrecoverable.

**Cause**: In the recursive implementation of `_set_nested_value`, pure numeric fields in the nested key path are mistakenly identified as list indices by `isdigit()`, triggering `current.extend([None] * (index - len(current) + 1))`, attempting to allocate a list with hundreds of millions of elements, instantly exhausting memory.

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

**Fix Content**:
1. Always use dictionaries when pre-creating intermediate layers, no longer guess container types based on whether the next segment is a number
2. When setting the final value, only handle indexing if the container itself is a list and the index is less than `STORAGE_MAX_LIST_INDEX` (10000); safely skip large indices
3. Change the recursive implementation to an iterative one, eliminating potential infinite recursion risks in the original code
4. Add `STORAGE_MAX_LIST_INDEX` constant to `Core/constants.py`, centrally managing the safe upper limit for indices

**Fix Date**: 2026/07/10

**Reproduction Steps**:
```python
# Writing a nested key path containing a large number field (such as a QQ group ID) triggers the OOM scenario
await sdk.storage.aset("groups.871684833.name", "Some Group")
# → Process memory spikes instantly, OOM Kill
```

**Regression Test**: Add 4 regression test cases to `tests/unit/test_unit_storage.py`
- `test_nested_key_numeric_segment_as_dict_key` — precisely reproduces the OOM scenario
- `test_nested_key_numeric_segment_multiple` — multiple consecutive numeric fields as dictionary keys
- `test_nested_key_existing_list_index_set_within_limit` — existing list index write within limit
- `test_nested_key_list_index_safety_limit` — safety limit validation for large indices

**Severity**: 🔴 Critical

**Type**: Storage

---

### [BUG-025] on_config_update callback not called by core router

**Problem**: The `on_config_update(old, new)` callback is defined in the base class (`BaseModule` / `BaseAdapter`), but the core framework does not associate it with configuration change events. The actual behavior is: when modifying configuration through the configuration management panel, it can be triggered, but when manually editing `config.toml` or calling `setConfig()` via code, `on_config_update` is not triggered.

**Cause**: `ConfigManager` emits `config.set` / `config.updated` lifecycle events when configuration changes, but lacks the subscription logic to forward these events to each component's `on_config_update` method.

**Root Cause Chain**:
```
Core does not subscribe to config.set / config.updated
  → Configuration change events are not forwarded
    → on_config_update is not called
      → Manual file editing / code setConfig does not trigger hot update callback
```

**Affected Version**: All versions

**Fixed Version**: 2.6.2

**Fix Content**: `ModuleManager` / `AdapterManager` register `config.set` (covering code `setConfig()` path) and `config.updated` (covering manual file editing path) event subscriptions, match by configuration key prefix and call the corresponding component's `on_config_update`, passing type-safe configuration objects. Also fix `_flush_config()` not synchronizing `_config_mtime` after writing the file, avoiding the framework's own write being misjudged as an external modification by the file monitoring task and repeatedly triggering `config.updated`.

**Compatibility Note**: Hot configuration updates are now centrally maintained by the framework core. The logic previously triggered by the configuration management panel has been removed, and upgrading the framework requires upgrading the configuration management panel as well, otherwise duplicate triggers (core + panel each call once) will occur. The `on_config_update` method signature and semantics remain unchanged, and subclasses do not need modification.

**Fix Date**: 2026/07/23

**Severity**: 🟡 Medium

**Type**: Configuration System

---

### [BUG-026] notice/request event reply target inferred incorrectly

**Problem**: When calling `event.reply()` in a group notification event (such as member joining `group_member_increase`), the message is sent to the private chat of the user who triggered the event, not the group where the event occurred. The same applies to friend notification events, where the reply target may be incorrect.

**Cause**: `infer_receive_type()` directly returns the event's `detail_type` as the session type. For message events, this is correct (`detail_type` values `private`/`group` are session types), but for notice/request events, `detail_type` is a semantic subtype (such as `group_member_increase`, `friend_increase`), not a session type. Subsequent `convert_to_send_type()` and `get_id_field()` cannot find the value in the mapping table and fall back to the default `"user"` / `"user_id"`, causing the reply target to be incorrect.

**Root Cause Chain**:
```
notice event detail_type="group_member_increase"
  → infer_receive_type() directly returns "group_member_increase"
    → convert_to_send_type("group_member_increase") not in mapping table → fallback "user"
    → get_id_field("group_member_increase") not in mapping table → fallback "user_id"
      → target_id = event["user_id"]  ← new member's private chat (not the group)
```

**Affected Version**: All versions

**Fixed Version**: 2.7.0-dev.3

**Fix Content**: `infer_receive_type()` adds a check—`detail_type` is directly returned only if it is a known session type (standard or custom type); otherwise, the correct session type is inferred based on the ID field (`group_id` / `channel_id` / `user_id`, etc.).

**Regression Test**: `tests/unit/test_unit_session_type.py` → `TestNoticeRequestTypeInference` (10 test cases)

**Fix Date**: 2026/07/29

**Severity**: 🟢 Minor

**Type**: Event System

---

### [BUG-027] Routing rate limit cleanup task uses fixed window causing long window rate limit rules to fail

**Problem**: When routing rate limiting is configured as a long window rule (such as `100/hour`, `{"requests": 100, "window": 3600}`), the rate limit is essentially ineffective—manifesting as approximately `100/minute` (up to about 6000 requests per hour can pass), completely failing to provide the expected hourly protection.

**Cause**: `_apply_rate_limit` parses the actual `window` (up to 3600 seconds) for each route, and per-request checks indeed use this window; however, the background cleanup task `_cleanup_expired_rate_limits` uses a fixed constant `DEFAULT_RATE_LIMIT_WINDOW_SECS` (60 seconds) as the unified cleanup threshold for all routes. Thus, time stamps earlier than 60 seconds in the `100/hour` route are cleared prematurely by the cleanup task, and the hour window never accumulates close to 100 records, severely weakening the rate limit.

**Root Cause Chain**:
```
_apply_rate_limit parses window=3600 (100/hour)
  → per-request check uses 3600s retention time (correct)
  → but _cleanup_expired_rate_limits uses fixed max_window=60s to clean
    → time stamps before 60 seconds are all cleared
      → the hour window only retains the records from the last 1 minute
        → 100/hour effectively degrades to ~100/minute (relaxed by about 60 times)
```

**Affected Version**: 2.6.0-dev.0 - 2.7.0-dev.4

**Fixed Version**: 2.7.0-dev.5

**Fix Content**: Add `_rate_limit_windows: dict[str, int]` to record the actual window for each route; write the window when the `_apply_rate_limit` first creates an entry; change `_cleanup_expired_rate_limits` to clean based on each key's own window (fallback to default value if missing); synchronize maintenance of the two dictionaries with cleanup and `stop()`.

**Fix Date**: 2026/07/31

**Regression Test**: `tests/unit/test_unit_router.py` → `TestRateLimit::test_cleanup_respects_per_route_window`

**Severity**: 🔴 Critical

**Type**: Routing

---

### [BUG-029] Configuration monitoring task broadcasts incomplete TOML and silently swallows exceptions

**Problem**: When the user manually edits `config.toml` and saves it halfway (producing a temporary syntax error), the configuration monitoring background thread detects the mtime change, reloads the configuration, but broadcasts an empty configuration `{}` after the load fails, causing the adapter/module's `on_config_update` to receive an empty configuration and mistakenly believe all configuration items have been cleared, reverting to default values. Additionally, the monitoring loop uses `except Exception: pass` to silently swallow all exceptions, making it impossible to troubleshoot watcher failures.

**Cause**: Two defects overlap:
1. `_load_config` wipes `_cache` to `{}` when TOML syntax error/permission error occurs, but the background monitoring thread `_watch_loop` and cache timeout path `_check_cache_validity` unconditionally execute `_emit_config_updated()` after calling `_load_config()`, broadcasting the "empty cache produced by load failure" as a real change.
2. `_watch_loop`'s `except Exception` does not log any messages.

**Root Cause Chain**:
```
User saves halfway → TOML syntax error
  → _load_config() wipes _cache = {}
    → _watch_loop unconditionally _emit_config_updated(new_config={})
      → Adapter/module on_config_update receives empty configuration
        → Mistakenly believes configuration has been cleared, reverts to default values
```

**Affected Version**: 2.6.2-dev.1 - 2.7.0-dev.4

**Fixed Version**: 2.7.0-dev.5

**Fix Content**:
1. `_load_config` is changed to return `bool`; in case of TOML syntax error/permission error/other errors, it **retains the last valid cache** (no longer wipes to `{}`), only records diagnostic logs and returns `False`
2. `_watch_loop` and `_check_cache_validity` only emit `config.updated` if `_load_config()` returns `True`
3. `_watch_loop`'s `except Exception` is changed to log at warning level (add i18n key `core.config.watcher_error`, synchronized in five languages)

**Fix Date**: 2026/07/31

**Regression Test**: `tests/unit/test_unit_config.py` → `test_malformed_toml_preserves_last_valid_cache`, `test_permission_denied_logs_clear_message` (updated to verify cache retention + return False)

**Severity**: 🟡 Medium

**Type**: Configuration System