# Bug Tracker

This document records the known bugs and their fixes in the ErisPulse SDK.

---

## Fixed Bugs

### [BUG-001] Init Command Adapter Configuration Path Type Error

**Issue**: When using the `ep init` command for interactive initialization, selecting a configuration adapter results in a type error:

```
Interactive initialization failed: unsupported operand type(s) for /: 'str' and 'str'
```

**Cause**: When adjusting the configuration file path in version 2.3.7, the method parameter types were inconsistent. `_configure_adapters_interactive_sync` received a `str` type parameter, but internally used the `Path` `/` operator to concatenate paths.

**Affected Versions**: 2.3.7 - 2.3.9-dev.1

**Fixed Version**: 2.3.9-dev.1

**Fix**: Changed the parameter type of `_configure_adapters_interactive_sync` from `str` to `Path`, and directly pass a `Path` object when calling.

**Fix Date**: 2026/03/23

---

### [BUG-002] Command Events Fail After Restart

**Issue**: After calling `sdk.restart()`, commands registered via `@command` cannot be triggered, resulting in the bot not responding after sending a command.

**Cause**: After `adapter.shutdown()` clears the event bus, the `_linked_to_adapter_bus` status in `BaseEventHandler` is not reset to `False`, causing the `_process_event` method to believe it is already mounted on the adapter bus and skip re-mounting.

**Affected Versions**: 2.2.x - 2.4.0-dev.2

**Fixed Version**: 2.4.0-dev.3

**Fix**: Introduced `_linked_to_adapter_bus` status tracking. After `_clear_handlers()` disconnects the bus, the next `register()` automatically re-mounts, adapting to shutdown/restart scenarios.

**Fix Date**: 2026/04/09

---

### [BUG-003] Lifecycle Event Handlers Not Cleared

**Issue**: After `sdk.restart()`, old lifecycle event handlers still exist and trigger repeatedly, causing the same event to be processed multiple times.

**Cause**: The `lifecycle._handlers` dictionary was never cleared during `uninit()`, so old and new handlers coexist after restart.

**Affected Versions**: 2.3.0 - 2.4.0-dev.2

**Fixed Version**: 2.4.0-dev.3

**Fix**: At the end of the cleanup process in `Uninitializer` (after all events are submitted), clear `lifecycle._handlers`.

**Fix Date**: 2026/04/09

---

### [BUG-004] Event.confirm() Confirmation Word Set Assignment Duplicated

**Issue**: In the `Event.confirm()` method, the assignment code for the `_yes`, `_no`, and `_all` variables was duplicated twice (totaling 6 lines), causing unnecessary repeated calculations.

**Cause**: Code copy-paste error.

**Affected Versions**: 2.4.0-dev.4

**Fixed Version**: 2.4.2-dev.1

**Fix**: Remove the duplicate assignment code (lines 739-741) in `wrapper.py`.

**Fix Date**: 2026/04/13

---

### [BUG-005] MessageBuilder.at Method Definition Overwritten (Dead Code)

**Issue**: The `MessageBuilder` class defines the `at` method three times: an instance method, a static method, and finally overwritten by `_DualMethod`. The first two definitions are never executed and are dead code.

**Cause**: When refactoring to `_DualMethod` dual-mode descriptor, the old manual definitions were forgotten to be deleted.

**Affected Versions**: 2.4.0-dev.0

**Fixed Version**: 2.4.2-dev.1

**Fix**: Delete the two dead `at` method definitions (lines 159-181) in `message_builder.py`, keeping only the `_DualMethod` assignment.

**Fix Date**: 2026/04/13

---

### [BUG-006] Event.is_friend_add/is_friend_delete detail_type Inconsistent with OB12 Standard

**Issue**: `Event.is_friend_add()` checks `detail_type == "friend_add"`, and `Event.is_friend_delete()` checks `detail_type == "friend_delete"`, but the OneBot12 standard defines `detail_type` values as `"friend_increase"` and `"friend_decrease"`. This inconsistency with the values used by `notice.py`'s `on_friend_add`/`on_friend_remove` decorators causes handlers registered via decorators to fail when corresponding `is_friend_add()`/`is_friend_delete()` judgment methods return `False`.

**Cause**: `wrapper.py` used non-standard naming, while `notice.py` used the correct OB12 standard naming.

**Affected Versions**: From rq implementation to present

**Fixed Version**: 2.4.2-dev.1

**Fix**: Change the matching value in `is_friend_add()` from `"friend_add"` to `"friend_increase"`, and `is_friend_delete()` from `"friend_delete"` to `"friend_decrease"`.

**Fix Date**: 2026/04/13

---

### [BUG-007] adapter.clear() Did Not Clear _started_instances, Causing Incorrect State After Restart

**Issue**: The `AdapterManager.clear()` method cleared `_adapters`, `_adapter_info`, handlers, and `_bots`, but missed clearing the `_started_instances` set. If `clear()` is called while the adapter is running, `_started_instances` retains dangling references, causing incorrect state after restart.

**Cause**: When `_started_instances` was introduced in 2.4.0-dev.1, it was not synchronized in `clear()`.

**Affected Versions**: 2.4.0-dev.1 - 2.4.2-dev.0

**Fixed Version**: 2.4.2-dev.1

**Fix**: Add `self._started_instances.clear()` in the `clear()` method.

**Fix Date**: 2026/04/13

---

### [BUG-008] command.wait_reply() Used Deprecated asyncio.get_event_loop()

**Issue**: The `CommandHandler.wait_reply()` method uses `asyncio.get_event_loop()` to create a future and get a timestamp. This method is deprecated in Python 3.10+, and `asyncio.get_running_loop()` should be used in asynchronous contexts. It is inconsistent with `wrapper.py`'s `wait_for()` method in the same file, which uses `get_running_loop()`.

**Cause**: The old API was used during development, and the newly added `wait_for()` used the correct API but did not retroactively fix the old code.

**Affected Versions**: 2.3.0-dev.0

**Fixed Version**: 2.4.2-dev.1

**Fix**: Replace the two `asyncio.get_event_loop()` calls in `command.py` with `asyncio.get_running_loop()`.

**Fix Date**: 2026/04/13

---

### [BUG-009] Event.collect() Silently Skips Fields Missing key

**Issue**: When `Event.collect()` iterates through a list of fields, if a field dictionary is missing the `key`, it silently skips the field without logging any warning or error. If a developer makes a typo (e.g., `"Key"` instead of `"key"`), the entire field is silently ignored, making downstream behavior difficult to debug.

**Cause**: Missing input validation and error feedback.

**Affected Versions**: 2.4.0-dev.4

**Fixed Version**: 2.4.2-dev.1

**Fix**: Add `logger.warning()` to log missing `key` field information before skipping.

**Fix Date**: 2026/04/13

---

### [BUG-010] LazyModule Synchronous Access to BaseModule Causes Incomplete Initialization

**Issue**: When users access a lazily loaded BaseModule attribute in a synchronous context, the module uses `loop.create_task()` for asynchronous initialization but does not await it, leading to possible incomplete initialization during attribute access and causing race conditions.

**Cause**: After `_ensure_initialized()` uses `loop.create_task(self._initialize())`, it immediately returns without ensuring initialization is complete.

**Affected Versions**: 2.4.0-dev.0 - 2.4.2-dev.1

**Fixed Version**: 2.4.2-dev.2

**Fix**: In synchronous contexts, BaseModule initialization is changed to use `asyncio.run(self._initialize())` to ensure initialization is complete before returning. The transparent proxy feature is maintained, so users do not need to perceive the difference between synchronous and asynchronous contexts.

**Fix Date**: 2026/04/21

---

### [BUG-011] Configuration System Multi-threaded Write Causes Data Loss

**Issue**: In a multi-threaded environment, when multiple threads simultaneously call `config.setConfig()`, the `_flush_config()` read-modify-write operation is not atomic, potentially causing partial write loss.

**Cause**: Although `_flush_config()` uses `RLock`, there is no file lock protection between file read and write, and `_schedule_write`'s Timer may be triggered multiple times, causing overwrites.

**Affected Versions**: 2.3.0 - 2.4.2-dev.1

**Fixed Version**: 2.4.2-dev.2

**Fix**: 
1. Add file locking mechanism (`_file_lock`) to ensure atomic file operations.
2. Use temporary file writing followed by atomic renaming (`os.replace`/`os.rename`).
3. Improve `_schedule_write` Timer cancellation and rescheduling logic.

**Fix Date**: 2026/04/21

---

### [BUG-012] SDK Attribute Access Error Message Is Inaccurate

**Issue**: When accessing a non-existent attribute, the error message "You may have used the wrong SDK registration object" may mislead users; the actual issue could be an unenabled module or a spelling error in the name.

**Cause**: The error message in `__getattribute__` does not distinguish between different scenarios and provides a vague message uniformly.

**Affected Versions**: 2.0.0 - 2.4.2-dev.1

**Fixed Version**: 2.4.2-dev.2

**Fix**: Differentiate scenarios based on the attribute name:
1. For registered but unenabled: indicate the module/adapter is not enabled.
2. For completely non-existent: prompt to check the name spelling.
Also, re-raise the original AttributeError for upper-level handling.

**Fix Date**: 2026/04/21

---

### [BUG-013] Uninitializer Cleanup Logic for Uninitialized LazyModule Too Complex

**Issue**: `Uninitializer` creates a temporary instance for never-accessed LazyModule to call `on_unload`, resulting in complex and error-prone code.

**Cause**: Attempting to call lifecycle methods for all LazyModule, but uninitialised modules do not need or should not be initialized.

**Affected Versions**: 2.4.0-dev.0 - 2.4.2-dev.1

**Fixed Version**: 2.4.2-dev.2

**Fix**: Simplify cleanup logic to handle only initialized LazyModule:
1. Skip uninitialised LazyModule, do not create temporary instances.
2. Only call `on_unload` for initialized modules.
3. Delete complex temporary instance creation logic.

**Fix Date**: 2026/04/21

---

### [BUG-014] Windows Ctrl+C Cannot Stop Program

**Issue**: When running `python main.py` directly on Windows, pressing Ctrl+C cannot terminate the program. After the program starts normally and outputs the routing server information, Ctrl+C has no response and can only be forcibly terminated via the task manager. However, stopping works normally when started via `epsdk run`, though `epsdk run` uses a subprocess model.

**Cause**: The `serve()` function of Hypercorn ASGI server internally registers its own SIGINT handler via `signal.signal(SIGINT, handler)`, overriding Python's default `KeyboardInterrupt` handling mechanism. When Hypercorn is started as a background task via `asyncio.create_task()`, its internal shutdown process cannot be triggered normally (as it expects `worker_serve` mode), causing the Ctrl+C signal to be swallowed by Hypercorn without triggering any cleanup actions.

**Affected Versions**: [2.3.6 - 2.4.2]

**Fixed Version**: 2.4.3-dev.0

**Fix**: 
1. Switch the ASGI server from Hypercorn to Uvicorn (`pyproject.toml` dependency change).
2. Start the server directly using `uvicorn.Server._serve()`, **bypassing** the `capture_signals()` signal handling context manager.
3. Implement graceful shutdown via `server.should_exit = True`, and cancel the background task if timeout occurs.
4. Simultaneously remove the subprocess running model and the `runtime/cleanup.py` cleanup module (subprocess cleanup mechanism is no longer needed).

**Fix Date**: 2026/04/28

---

### [BUG-015] Module Loading Strategy Sorting Logic Error

**Issue**: `ModuleLoadStrategy` provides a `priority` field to declare the initialization priority of modules, but the implementation of the loading strategy has an error, causing modules not to be initialized in the expected priority order. Instead, they are loaded in the default order of `entry_points()`. When modules have loading dependencies, the correct initialization order cannot be ensured through `priority`.

**Cause**: The sorting logic in the loading strategy implementation is incorrect, and `initialize_modules()` does not use `priority` to sort the module list.

**Affected Versions**: 2.3.4 - 2.4.5-dev.2

**Fixed Version**: 2.4.5-dev.3

**Fix**: Before traversing in `initialize_modules()`, sort the module list by `priority` in descending order. Modules with the same priority maintain their original relative order (stable sort).

**Fix Date**: 2026/05/15

---

### [BUG-016] Adapter Middleware Returning None Causes Event Data Loss

**Issue**: When `adapter.emit()` executes the OneBot12 middleware chain, if a middleware returns `None` (e.g., forgetting `return data`), subsequent middleware and all event handlers receive `processed_data` as `None`, causing event processing to fail completely.

**Cause**: The middleware chain implementation `processed_data = await middleware(processed_data)` does not check if the return value is `None`, directly overwriting the result from the previous step.

**Affected Versions**: unknown - 2.4.5-dev.3

**Fixed Version**: 2.4.5-dev.4

**Fix**: When middleware returns `None`, ignore the return value, retain the original data, and continue passing it, and output a warning-level log.

**Fix Date**: 2026/05/15

---

### [BUG-017] Configuration File Path Depends on Working Directory

**Issue**: The default configuration file path of `ConfigManager` is the relative path `"config/config.toml"`, which is resolved at runtime using `os.getcwd()`. If the working directory changes during runtime (e.g., via `os.chdir()`), configuration file read/write operations will point to the wrong location, leading to configuration loss or reading old data.

**Cause**: In `__init__`, the relative path is directly stored without being resolved to an absolute path at initialization.

**Affected Versions**: 2.3.7 - 2.4.5-dev.3

**Fixed Version**: 2.4.5-dev.4

**Fix**: In `ConfigManager.__init__()`, if the passed path is relative, automatically resolve it to an absolute path using `os.path.abspath()`.

**Fix Date**: 2026/05/15

---

### [BUG-018] Subprocess Mode `ep run <script>` Cannot Find Sub-packages in the Script's Directory

**Issue**: When running a script using `ep r .\main.py` in non-hot-reload mode, if the script has relative imports (e.g., `from qg import ...`), it reports a `No module named 'qg'` error. However, the `--reload` mode works normally.

**Cause**: In non-hot-reload mode, `runpy.run_path()` is called directly to execute the script, and this function does not automatically add the script's directory to `sys.path`. In contrast, the `--reload` mode uses `subprocess.Popen` to run a subprocess, which automatically inherits the current working directory, making `sys.path[0]` the script's directory, so it works normally.

**Affected Versions**: 2.5.0 - 2.5.2-dev.0

**Fixed Version**: 2.5.2-dev.0

**Fix**: Before calling `runpy.run_path()`, manually insert the script's directory into `sys.path[0]`.

**Fix Date**: 2026/06/27

---

### [BUG-019] SQL Query Builder Rejects Legitimate Wildcard and List Expressions

**Issue**: `SQLiteQueryBuilder`'s `_build_select_sql()` calls `_validate_identifier()` for all SELECT columns. This function uses a strict whitelist regex `^[a-zA-Z_][a-zA-Z0-9_]*$`, causing legitimate SQL syntax to be incorrectly judged as unsafe column names:
- `SELECT *` — `*` is a standard SQL wildcard
- `SELECT COUNT(*)` — aggregate function
- `SELECT users.name` — qualified column name
- `SELECT col AS alias` — column alias

Among these, `Select("*")` is used by modules like Cron, causing module `on_load` to fail and the module to fail to load.

**Cause**: In version 2.4.6, SQL injection protection was enhanced by introducing `_validate_identifier()` whitelist validation. This validation was applied to all column names but did not distinguish between read (SELECT/ORDER BY) and write (INSERT/UPDATE) ends. SELECT columns allow complex SQL expressions and should not be restricted by simple identifier whitelist rules.

**Affected Versions**: 2.4.6 - 2.5.2-dev.1

**Fixed Version**: 2.5.2-dev.2

**Fix**: Change the SELECT/ORDER BY column validation from whitelist mode to blacklist mode:
1. Add a new `_validate_select_column()` function that only blocks dangerous SQL injection characters (`;`, `'`, `"`, `--`, `/*`, `*/`, `\x00`, newline).
2. Allow any legitimate SQL column expression (`*`, `table.*`, `table.column`, `COUNT(*)`, `col AS alias`, etc.).
3. Keep strict whitelist validation for INSERT/UPDATE column names (only allow simple identifiers).

**Fix Date**: 2026/06/29

---

### [BUG-020] _resolve_account() Account Resolution Regression (_accounts_data Not Populated)

**Issue**: After the configuration system was refactored in 2.5.2, multi-account adapters declared with `AccountConfigClass` reported an error `ValueError("Account not declared, unable to resolve account")` when calling methods that require sending messages, such as `wait_reply` and `reply`. Even if the adapter was correctly configured with multi-account information, account resolution still failed.

**Cause**: In 2.5.2-dev.5, `_load_accounts()` (responsible for reading configuration, validating, and populating `_accounts_data`) was refactored into `_ensure_accounts_exist()` (only generating configuration templates), but `_resolve_account()` still checked `self._accounts_data is None`. Since `_ensure_accounts_exist()` no longer populates `_accounts_data`, this attribute remains `None`, causing `_resolve_account()` to prematurely return `(None, None)`, and account resolution fails completely.

**Root Cause Chain**:
```
_load_accounts() was deleted
  → __init__ no longer populates _accounts_data
    → _accounts_data is always None
      → _resolve_account() checks _accounts_data is None → return (None, None)
        → downstream places calling _resolve_account() (e.g., call_api) get None
          → trigger error
```

**Affected Versions**: 2.5.2-dev.5 - 2.5.2

**Fixed Version**: 2.5.3

**Fix**: In `BaseAdapter.__init__`, after `_ensure_accounts_exist()`, restore the population of `_accounts_data`:
```python
if self.AccountConfigClass is not None:
    self._ensure_accounts_exist()
    self._accounts_data = self.accounts  # Restore population, data source is the real-time read accounts attribute
```
The `_resolve_account()` logic remains unchanged, ensuring full backward compatibility:
- For adapters that do not declare `AccountConfigClass`: `_accounts_data` remains `None` → return `(None, None)`
- For adapters that declare `AccountConfigClass`: `_accounts_data` is populated → normal resolution
- For adapters that override `_load_accounts` or manually set `_accounts_data`: overwrite after `super().__init__()`, highest priority

**Fix Date**: 2026/07/07