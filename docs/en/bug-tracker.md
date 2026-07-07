# Bug Tracker

This document records the known bugs and fixes for ErisPulse SDK.

---

## Fixed Bugs

### [BUG-001] Init command adapter configuration path type mismatch

**Issue**: When using the `ep init` command for interactive initialization, selecting the configuration adapter results in a type error:

```
Interactive initialization failed: unsupported operand type(s) for /: 'str' and 'str'
```

**Root Cause**: In version 2.3.7, when adjusting the configuration file path, the method parameter type was inconsistent. `_configure_adapters_interactive_sync` receives `str` type parameters, but internally uses the `/` operator of `Path` to concatenate paths.

**Affected Versions**: 2.3.7 - 2.3.9-dev.1

**Fixed Version**: 2.3.9-dev.1

**Fix Content**: Changed the parameter type of the `_configure_adapters_interactive_sync` method from `str` to `Path`, and pass `Path` objects directly when calling.

**Fix Date**: 2026/03/23

---

### [BUG-002] Command events fail after restart

**Issue**: After calling `sdk.restart()`, commands registered via `@command` cannot be triggered. The bot becomes unresponsive when a command is sent.

**Root Cause**: After `adapter.shutdown()` clears the event bus, the `_linked_to_adapter_bus` status of `BaseEventHandler` is not reset to `False`, causing the `_process_event` method to believe it is already mounted to the adapter bus and skipping the remount operation.

**Affected Versions**: 2.2.x - 2.4.0-dev.2

**Fixed Version**: 2.4.0-dev.3

**Fix Content**: Introduced `_linked_to_adapter_bus` state tracking. After `_clear_handlers()` disconnects the bus, the next `register()` automatically remounts, adapting to shutdown/restart scenarios.

**Fix Date**: 2026/04/09

---

### [BUG-003] Lifecycle event handlers not cleaned up

**Issue**: After `sdk.restart()`, old lifecycle event handlers remain and fire repeatedly, causing the same event to be processed multiple times.

**Root Cause**: The `lifecycle._handlers` dictionary was never cleaned up during `uninit()`, so after restart, old handlers coexist with new handlers.

**Affected Versions**: 2.3.0 - 2.4.0-dev.2

**Fixed Version**: 2.4.0-dev.3

**Fix Content**: Clear `lifecycle._handlers` at the end of the cleanup flow in `Uninitializer` (after all events are committed).

**Fix Date**: 2026/04/09

---

### [BUG-004] Duplicate assignment of confirmation word set in Event.confirm()

**Issue**: In the `Event.confirm()` method, the assignment code for the three variables `_yes`, `_no`, and `_all` is completely duplicated twice (6 lines total), causing meaningless redundant computation.

**Root Cause**: Code copy-paste error.

**Affected Versions**: 2.4.0-dev.4

**Fixed Version**: 2.4.2-dev.1

**Fix Content**: Delete the duplicate assignment code at lines 739-741 in `wrapper.py`.

**Fix Date**: 2026/04/13

---

### [BUG-005] MessageBuilder.at method definition overwritten (dead code)

**Issue**: The `at` method in the `MessageBuilder` class is defined three times: once as an instance method, once as a static method, and finally overwritten by assignment from `_DualMethod`. The first two definitions are dead code that will never execute.

**Root Cause**: When refactoring to the `_DualMethod` dual-mode descriptor, the old manual definitions were not deleted.

**Affected Versions**: 2.4.0-dev.0

**Fixed Version**: 2.4.2-dev.1

**Fix Content**: Delete the two dead `at` method definitions at lines 159-181 in `message_builder.py`, keeping only the `_DualMethod` assignment.

**Fix Date**: 2026/04/13

---

### [BUG-006] Detail type of Event.is_friend_add/is_friend_delete inconsistent with OB12 standard

**Issue**: `Event.is_friend_add()` checks `detail_type == "friend_add"`, `Event.is_friend_delete()` checks `detail_type == "friend_delete"`, but the OneBot12 standard defines `detail_type` values as `"friend_increase"` and `"friend_decrease"`. This is inconsistent with the values used by the `on_friend_add`/`on_friend_remove` decorators in `notice.py`, causing `is_friend_add()`/`is_friend_delete()` to return `False` when handlers registered via decorators are triggered.

**Root Cause**: Non-standard naming was used in `wrapper.py`, while `notice.py` used the correct OB12 standard naming.

**Affected Versions**: Since real-world implementation (rq实装至今)

**Fixed Version**: 2.4.2-dev.1

**Fix Content**: Changed the matching values in `is_friend_add()` from `"friend_add"` to `"friend_increase"`, and in `is_friend_delete()` from `"friend_delete"` to `"friend_decrease"`.

**Fix Date**: 2026/04/13

---

### [BUG-007] adapter.clear() does not clean _started_instances causing incorrect state after restart

**Issue**: The `AdapterManager.clear()` method clears `_adapters`, `_adapter_info`, handlers, and `_bots`, but misses the `_started_instances` set. If `clear()` is called while an adapter is running, `_started_instances` retains dangling references, causing state judgment errors after restart.

**Root Cause**: When `_started_instances` was introduced in 2.4.0-dev.1, it was not synchronized in the `clear()` method.

**Affected Versions**: 2.4.0-dev.1 - 2.4.2-dev.0

**Fixed Version**: 2.4.2-dev.1

**Fix Content**: Added `self._started_instances.clear()` to the `clear()` method.

**Fix Date**: 2026/04/13

---

### [BUG-008] command.wait_reply() uses deprecated asyncio.get_event_loop()

**Issue**: The `CommandHandler.wait_reply()` method uses `asyncio.get_event_loop()` to create futures and get timestamps. This method is deprecated in Python 3.10+; `asyncio.get_running_loop()` should be used in async contexts. This is inconsistent with the `wait_for()` method in `wrapper.py` in the same file, which uses `get_running_loop()`.

**Root Cause**: An older API was used during development. Later additions of `wait_for()` used the correct API but did not retroactively fix the old code.

**Affected Versions**: 2.3.0-dev.0

**Fixed Version**: 2.4.2-dev.1

**Fix Content**: Replaced two occurrences of `asyncio.get_event_loop()` with `asyncio.get_running_loop()` in `command.py`.

**Fix Date**: 2026/04/13

---

### [BUG-009] Event.collect() silently skips fields missing a key

**Issue**: In the `Event.collect()` method, when iterating over the field list, if a field dictionary is missing a `key`, it is silently skipped without any log output or warning. If a developer misspells a key (e.g., `"Key"` instead of `"key"`), the entire field is ignored, making downstream behavior difficult to troubleshoot.

**Root Cause**: Missing input validation and error feedback.

**Affected Versions**: 2.4.0-dev.4

**Fixed Version**: 2.4.2-dev.1

**Fix Content**: Added `logger.warning()` before skipping to record information about fields missing a `key`.

**Fix Date**: 2026/04/13

---

### [BUG-010] LazyModule synchronous access to BaseModule causes incomplete initialization

**Issue**: When accessing a lazy-loaded BaseModule property in a synchronous context, the module uses `loop.create_task()` for asynchronous initialization but does not wait, meaning the property access may occur before initialization is complete, leading to a race condition.

**Root Cause**: `_ensure_initialized()` calls `loop.create_task(self._initialize())` on BaseModule and immediately returns without ensuring initialization is complete.

**Affected Versions**: 2.4.0-dev.0 - 2.4.2-dev.1

**Fixed Version**: 2.4.2-dev.2

**Fix Content**: In synchronous contexts, changed BaseModule initialization to use `asyncio.run(self._initialize())` to ensure initialization completes before returning. Maintains transparent proxy characteristics, so users don't need to perceive sync/async differences.

**Fix Date**: 2026/04/21

---

### [BUG-011] Multithreaded writing in the configuration system causes data loss

**Issue**: In a multithreaded environment, when multiple threads call `config.setConfig()` simultaneously, the read-modify-write operation of `_flush_config()` is not atomic, potentially leading to partial write loss.

**Root Cause**: Although `_flush_config()` uses `RLock`, there is no file lock protection between file reading and writing, and the Timer of `_schedule_write` may be triggered multiple times, causing overwrites.

**Affected Versions**: 2.3.0 - 2.4.2-dev.1

**Fixed Version**: 2.4.2-dev.2

**Fix Content**:
1. Added a file lock mechanism (`_file_lock`) to ensure atomicity of file operations.
2. Use temporary file writes followed by atomic rename (`os.replace`/`os.rename`).
3. Improved `_schedule_write` Timer cancellation and rescheduling logic.

**Fix Date**: 2026/04/21

---

### [BUG-012] Inaccurate error message for SDK property access

**Issue**: When accessing a non-existent property, the error message "您可能使用了错误的SDK注册对象" (You might be using the wrong SDK registration object) can be misleading. It may be that a module is not enabled or there is a typo in the name.

**Root Cause**: The error message in `__getattribute__` does not distinguish between different scenarios, providing a uniform vague prompt.

**Affected Versions**: 2.0.0 - 2.4.2-dev.1

**Fixed Version**: 2.4.2-dev.2

**Fix Content**: Distinguish between different scenarios based on property name:
1. Registered but not enabled: Prompt that the module/adapter is not enabled.
2. Completely non-existent: Prompt to check name spelling.
Re-raise the original AttributeError to facilitate capture by upper layers.

**Fix Date**: 2026/04/21

---

### [BUG-013] Uninitializer cleanup logic for uninitialized LazyModules is overly complex

**Issue**: `Uninitializer` creates temporary instances for LazyModules that have never been accessed to call `on_unload`, which is complex and error-prone.

**Root Cause**: It attempts to call lifecycle methods for all LazyModules, but uninitialized modules do not need to and should not be initialized.

**Affected Versions**: 2.4.0-dev.0 - 2.4.2-dev.1

**Fixed Version**: 2.4.2-dev.2

**Fix Content**: Simplified the cleanup logic to only handle initialized LazyModules:
1. Skip uninitialized LazyModules, do not create temporary instances.
2. Call `on_unload` only for initialized modules.
3. Delete the complex temporary instance creation logic.

**Fix Date**: 2026/04/21

---

### [BUG-014] CTRL+C cannot stop the program on Windows

**Issue**: When running `python main.py` directly on Windows, pressing CTRL+C cannot terminate the program. The program starts normally and outputs the router server information, after which CTRL+C is completely unresponsive, and the process must be force-killed via Task Manager. Running via `epsdk run` works fine to stop, but `epsdk run` runs via a subprocess model.

**Root Cause**: Hypercorn ASGI server's `serve()` function internally registers its own SIGINT handler via `signal.signal(SIGINT, handler)`, overwriting Python's default `KeyboardInterrupt` handling mechanism. When Hypercorn is started as a background task via `asyncio.create_task()`, Hypercorn's internal shutdown flow cannot trigger normally (because it expects `worker_serve` mode), causing the CTRL+C signal to be swallowed by Hypercorn without triggering any cleanup actions.

**Affected Versions**: [2.3.6 - 2.4.2]

**Fixed Version**: 2.4.3-dev.0

**Fix Content**:
1. Switched the ASGI server from Hypercorn to Uvicorn (dependency change in `pyproject.toml`).
2. Start the server directly using `uvicorn.Server._serve()`, **bypassing** the `capture_signals()` signal handling context manager.
3. Implement graceful shutdown via `server.should_exit = True`, or cancel background tasks on timeout.
4. Synchronously remove the subprocess runtime model and `runtime/cleanup.py` cleanup module (subprocess cleanup mechanism is no longer needed).

**Fix Date**: 2026/04/28

---

### [BUG-015] Sorting logic error in module loading strategy

**Issue**: `ModuleLoadStrategy` provides a `priority` field to declare module initialization priority, but the implementation of the loading strategy contains an error, causing modules to not initialize in the expected priority order, but actually in the default order of `entry_points()`. When there are loading dependencies between modules, the correct initialization order cannot be guaranteed via `priority`.

**Root Cause**: The sorting logic in the loading strategy implementation is incorrect, and `initialize_modules()` does not use `priority` to sort the list of modules.

**Affected Versions**: 2.3.4 - 2.4.5-dev.2

**Fixed Version**: 2.4.5-dev.3

**Fix Content**: Sort the module list by `priority` in descending order before iterating in `initialize_modules()`. Modules with the same priority maintain their original relative order (stable sort).

**Fix Date**: 2026/05/15

---

### [BUG-016] Event data loss due to middleware returning None

**Issue**: When `adapter.emit()` executes the OneBot12 middleware chain, if a middleware returns `None` (e.g., forgetting to `return data`), `processed_data` received by subsequent middleware and all event handlers becomes `None`, causing event processing to fail completely.

**Root Cause**: The middleware chain implementation `processed_data = await middleware(processed_data)` does not check if the return value is `None`, directly overwriting the result of the previous step.

**Affected Versions**: unknown - 2.4.5-dev.3

**Fixed Version**: 2.4.5-dev.4

**Fix Content**: Ignore the return value if the middleware returns `None`, preserve the original data to continue passing it, and output a warning-level log.

**Fix Date**: 2026/05/15

---

### [BUG-017] Configuration file path depends on working directory

**Issue**: The configuration file path for `ConfigManager` defaults to a relative path `"config/config.toml"`, which relies on `os.getcwd()` to resolve at runtime. If the working directory changes during runtime (e.g., via `os.chdir()`), read and write operations on the configuration file will point to the wrong location, causing configuration loss or reading old data.

**Root Cause**: The relative path is stored directly in `__init__` without resolving it to an absolute path during initialization.

**Affected Versions**: 2.3.7 - 2.4.5-dev.3

**Fixed Version**: 2.4.5-dev.4

**Fix Content**: In `ConfigManager.__init__()`, if the provided path is a relative path, automatically resolve it to an absolute path via `os.path.abspath()`.

**Fix Date**: 2026/05/15

---

### [BUG-018] Subprocess mode `ep run <script>` cannot find subpackages in the script's directory

**Issue**: When running a script in non-hot-reload mode using `ep r .\main.py`, if the script has relative imports (e.g., `from qg import ...`), a `No module named 'qg'` error occurs. The `--reload` mode runs normally.

**Root Cause**: The non-hot-reload mode calls `runpy.run_path()` directly to execute the script, which does not automatically add the script's directory to `sys.path`. The `--reload` mode runs via `subprocess.Popen` subprocess, which automatically inherits the current working directory. `sys.path[0]` is the script's directory, so it works normally.

**Affected Versions**: 2.5.0 - 2.5.2-dev.0

**Fixed Version**: 2.5.2-dev.0

**Fix Content**: Manually insert the script's directory into `sys.path[0]` before calling `runpy.run_path()`.

**Fix Date**: 2026/06/27

---

### [BUG-019] SQLite query builder rejects valid wildcards and column expressions

**Issue**: `_build_select_sql()` in `SQLiteQueryBuilder` calls `_validate_identifier()` for all SELECT columns. This function uses a strict whitelist regex `^[a-zA-Z_][a-zA-Z0-9_]*$`, causing legitimate SQL syntax to be misjudged as unsafe column names:

- `SELECT *` — `*` is the SQL standard wildcard
- `SELECT COUNT(*)` — aggregate function
- `SELECT users.name` — qualified column name
- `SELECT col AS alias` — column alias

`Select("*")` is used by modules like Cron, causing `on_load` to fail to execute and modules to fail to load.

**Root Cause**: Version 2.4.6 enhanced SQL injection protection by introducing the `_validate_identifier()` whitelist check. This check was applied to all column names but did not distinguish between the read side (SELECT/ORDER BY) and the write side (INSERT/UPDATE). SELECT columns allow complex SQL expressions and should not be limited by a simple identifier whitelist.

**Affected Versions**: 2.4.6 - 2.5.2-dev.1

**Fixed Version**: 2.5.2-dev.2

**Fix Content**: Changed the column validation for SELECT/ORDER BY from whitelist mode to blacklist mode:
1. Added `_validate_select_column()` function to only intercept SQL injection dangerous characters (`;` `'` `"` `--` `/*` `*/` `\x00` newline).
2. Allow arbitrary valid SQL column expressions (`*`, `table.*`, `table.column`, `COUNT(*)`, `col AS alias`, etc.).
3. INSERT/UPDATE column names still maintain strict whitelist validation (allowing only simple identifiers).

**Fix Date**: 2026/06/29

---

### [BUG-020] Account resolution regression in _resolve_account() (_accounts_data not populated)

**Issue**: After the 2.5.2 configuration system refactor, adapters declaring `AccountConfigClass` reported `ValueError("未声明 AccountConfigClass，无法解析账户")` when calling methods requiring message sending like `wait_reply`, `reply`, etc. Even if the adapter was correctly configured with multi-account info, account resolution still failed.

**Root Cause**: Version 2.5.2-dev.5 refactored `_load_accounts()` (responsible for reading config + validation + populating `_accounts_data`) into `_ensure_accounts_exist()` (which only generates a config template), but `_resolve_account()` still checks `self._accounts_data is None`. Since `_ensure_accounts_exist()` no longer populates `_accounts_data`, this property is always `None`, causing `_resolve_account()` to return `(None, None)` early, completely breaking account resolution.

**Root Cause Chain**:
```
_load_accounts() was deleted
  → __init__ no longer populates _accounts_data
    → _accounts_data is always None
      → _resolve_account() checks _accounts_data is None → return (None, None)
        → Downstream calls to _resolve_account (like call_api) get None
          → Triggers error
```

**Affected Versions**: 2.5.2-dev.5 - 2.5.2

**Fixed Version**: 2.5.3

**Fix Content**: In `BaseAdapter.__init__`, restore population of `_accounts_data` after `_ensure_accounts_exist()`:
```python
if self.AccountConfigClass is not None:
    self._ensure_accounts_exist()
    self._accounts_data = self.accounts  # Restore population, data source is the live accounts property
```
The `_resolve_account()` logic remains unchanged, fully backward compatible:
- Adapters not declaring `AccountConfigClass`: `_accounts_data` stays `None` → returns `(None, None)`
- Adapters declaring `AccountConfigClass`: `_accounts_data` is populated → resolves normally
- Adapters overriding `_load_accounts` or manually setting `_accounts_data`: override after `super().__init__()`, highest priority

**Fix Date**: 2026/07/07