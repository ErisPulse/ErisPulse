# Bug Tracker

This document records known bugs and fixes for the ErisPulse SDK.

---

## Fixed Bugs

### [BUG-001] Incorrect path type for Init command adapter configuration

**Issue**: When using the `ep init` command for interactive initialization, selecting a configuration adapter results in a type error:

```
Interactive initialization failed: unsupported operand type(s) for /: 'str' and 'str'
```

**Cause**: In version 2.3.7, when adjusting configuration file paths, method parameter types were inconsistent. `_configure_adapters_interactive_sync` receives `str` type parameters but uses the `/` operator of `Path` internally to concatenate paths.

**Affected Versions**: 2.3.7 - 2.3.9-dev.1

**Fixed Version**: 2.3.9-dev.1

**Fix Details**: Changed the parameter type of `_configure_adapters_interactive_sync` method from `str` to `Path`, passing `Path` objects directly when calling.

**Fix Date**: 2026/03/23

---

### [BUG-002] Command events fail after restart

**Issue**: After calling `sdk.restart()`, commands registered via `@command` cannot be triggered; the bot shows no response after sending a command.

**Cause**: After `adapter.shutdown()` clears the event bus, the `_linked_to_adapter_bus` state of `BaseEventHandler` is not reset to `False`, causing the `_process_event` method to think it is already mounted to the adapter bus and skipping the remounting operation.

**Affected Versions**: 2.2.x - 2.4.0-dev.2

**Fixed Version**: 2.4.0-dev.3

**Fix Details**: Introduced `_linked_to_adapter_bus` state tracking. After `_clear_handlers()` disconnects the bus, the next `register()` automatically remounts, adapting to shutdown/restart scenarios.

**Fix Date**: 2026/04/09

---

### [BUG-003] Lifecycle event handlers not cleaned up

**Issue**: After `sdk.restart()`, old lifecycle event handlers persist and trigger repeatedly, causing a single event to be processed multiple times.

**Cause**: The `lifecycle._handlers` dictionary was never cleaned up during `uninit()`, causing old handlers to coexist with new handlers after restart.

**Affected Versions**: 2.3.0 - 2.4.0-dev.2

**Fixed Version**: 2.4.0-dev.3

**Fix Details**: At the end of the cleanup process in `Uninitializer` (after all events are submitted), clear `lifecycle._handlers`.

**Fix Date**: 2026/04/09

---

### [BUG-004] Duplicate assignment of keywords in Event.confirm()

**Issue**: In the `Event.confirm()` method, the assignment code for three variables `_yes`, `_no`, and `_all` is completely duplicated twice (6 lines total), leading to meaningless repeated calculation.

**Cause**: Code copy-paste error.

**Affected Versions**: 2.4.0-dev.4

**Fixed Version**: 2.4.2-dev.1

**Fix Details**: Remove the duplicate assignment code at lines 739-741 in `wrapper.py`.

**Fix Date**: 2026/04/13

---

### [BUG-005] MessageBuilder.at method definition overwritten (Dead Code)

**Issue**: The `at` method in the `MessageBuilder` class is defined three times: once as an instance method, once as a static method, and finally overwritten by the `_DualMethod` assignment. The first two definitions are dead code that will never be executed.

**Cause**: When refactoring to `_DualMethod` dual-mode descriptor, the old manual definitions were forgotten to be deleted.

**Affected Versions**: 2.4.0-dev.0

**Fixed Version**: 2.4.2-dev.1

**Fix Details**: Remove the two dead `at` method definitions at lines 159-181 in `message_builder.py`, keeping only the `_DualMethod` assignment.

**Fix Date**: 2026/04/13

---

### [BUG-006] detail_type mismatch in Event.is_friend_add/is_friend_delete with OB12 standard

**Issue**: `Event.is_friend_add()` checks `detail_type == "friend_add"` and `Event.is_friend_delete()` checks `detail_type == "friend_delete"`. However, the OneBot12 standard defines these values as `"friend_increase"` and `"friend_decrease"`. This is inconsistent with the values used by the `on_friend_add`/`on_friend_remove` decorators in `notice.py`. As a result, handlers registered via decorators trigger correctly, but the corresponding `is_friend_add()`/`is_friend_delete()` judgment methods return `False`.

**Cause**: `wrapper.py` uses non-standard naming, while `notice.py` uses the correct OB12 standard naming.

**Affected Versions**: rq implementation onwards

**Fixed Version**: 2.4.2-dev.1

**Fix Details**: Change the matching value for `is_friend_add()` from `"friend_add"` to `"friend_increase"` and for `is_friend_delete()` from `"friend_delete"` to `"friend_decrease"`.

**Fix Date**: 2026/04/13

---

### [BUG-007] adapter.clear() fails to clean up _started_instances causing incorrect state after restart

**Issue**: The `AdapterManager.clear()` method clears `_adapters`, `_adapter_info`, handlers, and `_bots`, but omits the `_started_instances` collection. If `clear()` is called while adapters are running, `_started_instances` retains dangling references, causing incorrect state judgment after restart.

**Cause**: `_started_instances` introduced in 2.4.0-dev.1 was not cleared synchronously in `clear()`.

**Affected Versions**: 2.4.0-dev.1 - 2.4.2-dev.0

**Fixed Version**: 2.4.2-dev.1

**Fix Details**: Add `self._started_instances.clear()` in the `clear()` method.

**Fix Date**: 2026/04/13

---

### [BUG-008] command.wait_reply() uses deprecated asyncio.get_event_loop()

**Issue**: The `CommandHandler.wait_reply()` method uses `asyncio.get_event_loop()` to create futures and get timestamps. This method is deprecated in Python 3.10+, and `asyncio.get_running_loop()` should be used in async contexts. This is inconsistent with the `wait_for()` method in `wrapper.py` within the same file, which uses `get_running_loop()`.

**Cause**: Old API was used during development; later additions like `wait_for()` used the correct API but did not backport the fix to the old code.

**Affected Versions**: 2.3.0-dev.0

**Fixed Version**: 2.4.2-dev.1

**Fix Details**: Replace two instances of `asyncio.get_event_loop()` with `asyncio.get_running_loop()` in `command.py`.

**Fix Date**: 2026/04/13

---

### [BUG-009] Event.collect() silently skips fields missing a key

**Issue**: In the `Event.collect()` method, when iterating over a list of fields, if a field dictionary is missing a `key`, that field is silently skipped without any log or warning output. If a developer makes a typo (e.g., using `"Key"` instead of `"key"`), the entire field is quietly ignored, making downstream behavior difficult to troubleshoot.

**Cause**: Lack of input validation and error feedback.

**Affected Versions**: 2.4.0-dev.4

**Fixed Version**: 2.4.2-dev.1

**Fix Details**: Add `logger.warning()` before skipping to log information about the field missing a `key`.

**Fix Date**: 2026/04/13

---

### [BUG-010] LazyModule synchronous access to BaseModule causes incomplete initialization

**Issue**: When a user accesses a lazily loaded BaseModule property in a synchronous context, the module uses `loop.create_task()` for asynchronous initialization but does not wait. As a result, the property access may occur before initialization is complete, causing a race condition.

**Cause**: `_ensure_initialized()` immediately returns after calling `loop.create_task(self._initialize())` for BaseModule without ensuring completion.

**Affected Versions**: 2.4.0-dev.0 - 2.4.2-dev.1

**Fixed Version**: 2.4.2-dev.2

**Fix Details**: In synchronous contexts, change the initialization of BaseModule to use `asyncio.run(self._initialize())` to ensure completion before returning. Maintain transparent proxy behavior so users are unaware of sync/async differences.

**Fix Date**: 2026/04/21

---

### [BUG-011] Data loss in configuration system due to multi-threaded writes

**Issue**: In a multi-threaded environment, when multiple threads call `config.setConfig()` simultaneously, the read-modify-write operation in `_flush_config()` is not atomic, potentially leading to lost writes.

**Cause**: Although `_flush_config()` uses `RLock`, there is no file lock protection between file read and write operations, and the Timer in `_schedule_write` might be triggered multiple times causing overwrites.

**Affected Versions**: 2.3.0 - 2.4.2-dev.1

**Fixed Version**: 2.4.2-dev.2

**Fix Details**:
1. Add a file lock mechanism (`_file_lock`) to ensure atomicity of file operations
2. Use temporary file writes followed by atomic rename (`os.replace`/`os.rename`)
3. Improve `_schedule_write` Timer cancel and reschedule logic

**Fix Date**: 2026/04/21

---

### [BUG-012] Inaccurate error messages for SDK attribute access

**Issue**: When accessing a non-existent attribute, the error message "You may have used the wrong SDK registration object" can mislead users. The actual issue might be that the module is not enabled or the name is misspelled.

**Cause**: The error message in `__getattribute__` does not distinguish between different scenarios, providing a generic, vague hint in all cases.

**Affected Versions**: 2.0.0 - 2.4.2-dev.1

**Fixed Version**: 2.4.2-dev.2

**Fix Details**: Distinguish different scenarios based on attribute name:
1. Registered but not enabled: Prompt that module/adapter is not enabled
2. Does not exist at all: Prompt to check spelling
Also re-raise the original `AttributeError` for upper layers to catch.

**Fix Date**: 2026/04/21

---

### [BUG-013] Uninitializer cleanup logic for uninitialized LazyModules is too complex

**Issue**: `Uninitializer` creates temporary instances for LazyModules that have never been accessed just to call `on_unload`. This code is complex and error-prone.

**Cause**: An attempt was made to call lifecycle methods for all LazyModules, but uninitialized modules do not need nor should they be initialized.

**Affected Versions**: 2.4.0-dev.0 - 2.4.2-dev.1

**Fixed Version**: 2.4.2-dev.2

**Fix Details**: Simplify cleanup logic to only process initialized LazyModules:
1. Skip uninitialized LazyModules without creating temporary instances
2. Call `on_unload` only for initialized modules
3. Remove complex temporary instance creation logic

**Fix Date**: 2026/04/21

---

### [BUG-014] CTRL+C cannot stop the program on Windows

**Issue**: When running `python main.py` directly on Windows, pressing CTRL+C does not terminate the program. After the program starts normally and outputs the router server information, CTRL+C has no response at all, and the process can only be killed via Task Manager. However, it works fine when stopped via `epsdk run`—but `epsdk run` runs via the subprocess model.

**Cause**: Inside Hypercorn ASGI server's `serve()` function, it registers its own SIGINT handler via `signal.signal(SIGINT, handler)`, overriding Python's default `KeyboardInterrupt` handling mechanism. When starting Hypercorn as a background task via `asyncio.create_task()`, Hypercorn's internal shutdown flow cannot trigger properly (because it expects `worker_serve` mode). As a result, the CTRL+C signal is swallowed by Hypercorn but triggers no cleanup actions.

**Affected Versions**: [2.3.6 - 2.4.2]

**Fixed Version**: 2.4.3-dev.0

**Fix Details**:
1. Switch ASGI server from Hypercorn to Uvicorn (change dependency in `pyproject.toml`)
2. Use `uvicorn.Server._serve()` to start the server directly, **bypassing** the `capture_signals()` signal handling context manager
3. Implement graceful shutdown via `server.should_exit = True`, canceling background task on timeout
4. Synchronously remove subprocess runtime model and `runtime/cleanup.py` cleanup module (subprocess cleanup mechanism is no longer needed)

**Fix Date**: 2026/04/28

---

### [BUG-015] Incorrect sorting logic in module loading strategy

**Issue**: `ModuleLoadStrategy` provides a `priority` field to declare module initialization priority, but the implementation of the loading strategy contains a flaw, causing modules to be initialized in the order returned by `entry_points()` instead of the expected priority order. When there are loading dependencies between modules, the correct initialization sequence cannot be guaranteed via `priority`.

**Cause**: The sorting logic in the loading strategy implementation is incorrect; `initialize_modules()` does not sort the module list by `priority`.

**Affected Versions**: 2.3.4 - 2.4.5-dev.2

**Fixed Version**: 2.4.5-dev.3

**Fix Details**: Before iterating in `initialize_modules()`, sort the module list in descending order of `priority`. Modules with the same priority maintain their original relative order (stable sort).

**Fix Date**: 2026/05/15

---

### [BUG-016] Event data loss due to adapter middleware returning None

**Issue**: When `adapter.emit()` executes the OneBot12 middleware chain, if a middleware returns `None` (e.g., forgetting to `return data`), `processed_data` becomes `None` for subsequent middlewares and all event handlers, causing event processing to fail completely.

**Cause**: The middleware chain implementation `processed_data = await middleware(processed_data)` does not check if the return value is `None`, simply overwriting the result of the previous step.

**Affected Versions**: unknown - 2.4.5-dev.3

**Fixed Version**: 2.4.5-dev.4

**Fix Details**: When middleware returns `None`, ignore that return value and preserve the original data for continued propagation, while outputting a warning-level log.

**Fix Date**: 2026/05/15

---

### [BUG-017] Configuration file path relies on working directory

**Issue**: The default configuration file path for `ConfigManager` is the relative path `"config/config.toml"`, relying on `os.getcwd()` to resolve at runtime. If the working directory changes during runtime (e.g., via `os.chdir()`), read and write operations for the config file will point to the wrong location, causing configuration loss or reading of stale data.

**Cause**: The relative path was stored directly in `__init__` without being resolved to an absolute path during initialization.

**Affected Versions**: 2.3.7 - 2.4.5-dev.3

**Fixed Version**: 2.4.5-dev.4

**Fix Details**: In `ConfigManager.__init__()`, if the provided path is a relative path, automatically resolve it to an absolute path using `os.path.abspath()`.

**Fix Date**: 2026/05/15

---

### [BUG-018] subprocess mode `ep run <script>` cannot find subpackages of script directory

**Issue**: When running a script using `ep r .\main.py` in non-hot-reload mode, if the script has relative imports (e.g., `from qg import ...`), it raises `No module named 'qg'` error. However, the `--reload` mode works correctly.

**Cause**: The non-hot-reload mode calls `runpy.run_path()` directly to execute the script, which does not automatically add the script's directory to `sys.path`. The `--reload` mode runs via `subprocess.Popen`, which automatically inherits the current working directory, making `sys.path[0]` the script's directory, thus working correctly.

**Affected Versions**: 2.5.0 - 2.5.2-dev.0

**Fixed Version**: 2.5.2-dev.0

**Fix Details**: Before calling `runpy.run_path()`, manually insert the script's directory into `sys.path[0]`.

**Fix Date**: 2026/06/27

---

### [BUG-019] SQL query builder rejects valid wildcards and column expressions

**Issue**: `_build_select_sql()` in `SQLiteQueryBuilder` calls `_validate_identifier()` for all SELECT columns. This function uses a strict whitelist regex `^[a-zA-Z_][a-zA-Z0-9_]*$`, causing legitimate SQL syntax to be misjudged as unsafe column names:

- `SELECT *` — `*` is a SQL standard wildcard
- `SELECT COUNT(*)` — aggregate function
- `SELECT users.name` — qualified column name
- `SELECT col AS alias` — column alias

Notably, `Select("*")` is used by modules like Cron, causing `on_load` execution to fail and preventing module loading.

**Cause**: Version 2.4.6 enhanced SQL injection protection by introducing `_validate_identifier()` whitelist validation. This validation applies to all column names but does not distinguish between the read side (SELECT/ORDER BY) and write side (INSERT/UPDATE). SELECT columns allow complex SQL expressions and should not be restricted by a simple identifier whitelist.

**Affected Versions**: 2.4.6 - 2.5.2-dev.1

**Fixed Version**: 2.5.2-dev.2

**Fix Details**: Change column validation for SELECT/ORDER BY from whitelist mode to blacklist mode:
1. Add new `_validate_select_column()` function that only intercepts SQL injection dangerous characters (`;` `'` `"` `--` `/*` `*/` `\x00` newline)
2. Allow any legitimate SQL column expression (`*`, `table.*`, `table.column`, `COUNT(*)`, `col AS alias`, etc.)
3. Keep strict whitelist validation for INSERT/UPDATE column names (only simple identifiers allowed)

**Fix Date**: 2026/06/29