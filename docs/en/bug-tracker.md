# Bug Tracker

This document records known bugs and fixes for the ErisPulse SDK.

---

## Fixed Bugs

### [BUG-001] Init command adapter configuration path type error

**Issue**: When using the `ep init` command for interactive initialization, selecting a configuration adapter results in a type error:

```
Interactive initialization failed: unsupported operand type(s) for /: 'str' and 'str'
```

**Cause**: In version 2.3.7, when adjusting the configuration file path, the method parameter type was inconsistent. `_configure_adapters_interactive_sync` receives `str` type parameters, but internally uses the `Path` `/` operator to concatenate paths.

**Affected Versions**: 2.3.7 - 2.3.9-dev.1

**Fixed Version**: 2.3.9-dev.1

**Fix**: Changed the parameter type of the `_configure_adapters_interactive_sync` method from `str` to `Path`, passing `Path` objects directly when calling.

**Fix Date**: 2026/03/23

---

### [BUG-002] Command events stop working after restart

**Issue**: After calling `sdk.restart()`, commands registered via `@command` cannot be triggered. This manifests as the bot not responding after sending a command.

**Cause**: After `adapter.shutdown()` clears the event bus, the `_linked_to_adapter_bus` state of `BaseEventHandler` is not reset to `False`, causing the `_process_event` method to believe it is already mounted to the adapter bus and skipping the remount operation.

**Affected Versions**: 2.2.x - 2.4.0-dev.2

**Fixed Version**: 2.4.0-dev.3

**Fix**: Introduced `_linked_to_adapter_bus` state tracking. After `_clear_handlers()` disconnects from the bus, `register()` automatically remounts on the next call, adapting to shutdown/restart scenarios.

**Fix Date**: 2026/04/09

---

### [BUG-003] Lifecycle event handlers are not cleaned up

**Issue**: After `sdk.restart()`, old lifecycle event handlers remain active and trigger repeatedly, causing a single event to be processed multiple times.

**Cause**: The `lifecycle._handlers` dictionary is never cleaned up during `uninit()`, resulting in old handlers coexisting with new ones after a restart.

**Affected Versions**: 2.3.0 - 2.4.0-dev.2

**Fixed Version**: 2.4.0-dev.3

**Fix**: At the end of the cleanup flow in `Uninitializer` (after all events are submitted), clear `lifecycle._handlers`.

**Fix Date**: 2026/04/09

---

### [BUG-004] Duplicate assignment of confirmation word collection in Event.confirm()

**Issue**: In the `Event.confirm()` method, the assignment code for the three variables `_yes`, `_no`, and `_all` is completely duplicated twice (6 lines total), resulting in meaningless duplicate calculations.

**Cause**: A code copy-paste error.

**Affected Versions**: 2.4.0-dev.4

**Fixed Version**: 2.4.2-dev.1

**Fix**: Remove the duplicate assignment code in lines 739-741 of `wrapper.py`.

**Fix Date**: 2026/04/13

---

### [BUG-005] MessageBuilder.at method definition is overridden (Dead code)

**Issue**: The `at` method in the `MessageBuilder` class is defined three times: once as an instance method, once as a static method, and finally overridden by a `_DualMethod` assignment. The first two definitions are dead code that will never execute.

**Cause**: When refactoring to the `_DualMethod` dual-mode descriptor, the old manual definitions were forgotten and not deleted.

**Affected Versions**: 2.4.0-dev.0

**Fixed Version**: 2.4.2-dev.1

**Fix**: Delete the two dead `at` method definitions in lines 159-181 of `message_builder.py`, keeping only the `_DualMethod` assignment.

**Fix Date**: 2026/04/13

---

### [BUG-006] Inconsistency between Event.is_friend_add/is_friend_delete detail_type and OB12 standard

**Issue**: `Event.is_friend_add()` checks `detail_type == "friend_add"`, and `Event.is_friend_delete()` checks `detail_type == "friend_delete"`. However, the OneBot12 standard defines the `detail_type` values as `"friend_increase"` and `"friend_decrease"`. This is inconsistent with the values used by the `on_friend_add`/`on_friend_remove` decorators in `notice.py`, causing the corresponding `is_friend_add()`/`is_friend_delete()` judgment methods to return `False` when handlers are triggered via the decorators.

**Cause**: Non-standard naming was used in `wrapper.py`, while `notice.py` used the correct OB12 standard naming.

**Affected Versions**: Since implementation of rq

**Fixed Version**: 2.4.2-dev.1

**Fix**: Changed the matching value of `is_friend_add()` from `"friend_add"` to `"friend_increase"`, and changed `is_friend_delete()` from `"friend_delete"` to `"friend_decrease"`.

**Fix Date**: 2026/04/13

---

### [BUG-007] adapter.clear() does not clear _started_instances causing incorrect state after restart

**Issue**: The `AdapterManager.clear()` method clears `_adapters`, `_adapter_info`, handlers, and `_bots`, but omits the `_started_instances` collection. If `clear()` is called while an adapter is running, `_started_instances` retains dangling references, causing incorrect state judgments after a restart.

**Cause**: When introducing `_started_instances` in version 2.4.0-dev.1, it was not cleaned up synchronously in `clear()`.

**Affected Versions**: 2.4.0-dev.1 - 2.4.2-dev.0

**Fixed Version**: 2.4.2-dev.1

**Fix**: Added `self._started_instances.clear()` to the `clear()` method.

**Fix Date**: 2026/04/13

---

### [BUG-008] command.wait_reply() uses deprecated asyncio.get_event_loop()

**Issue**: The `CommandHandler.wait_reply()` method uses `asyncio.get_event_loop()` to create futures and get timestamps. This method is deprecated in Python 3.10+, and `asyncio.get_running_loop()` should be used in async contexts. This is inconsistent with the `wait_for()` method in `wrapper.py` in the same file, which uses `get_running_loop()`.

**Cause**: The older API was used during development, and while the newly added `wait_for()` used the correct API, the old code was not backported.

**Affected Versions**: 2.3.0-dev.0

**Fixed Version**: 2.4.2-dev.1

**Fix**: Replaced the two occurrences of `asyncio.get_event_loop()` in `command.py` with `asyncio.get_running_loop()`.

**Fix Date**: 2026/04/13

---

### [BUG-009] Event.collect() silently skips when field is missing key

**Issue**: When traversing the list of fields in the `Event.collect()` method, if a field dictionary is missing a `key`, the field is silently skipped without outputting any logs or warnings. If a developer makes a typo (e.g., `"Key"` instead of `"key"`), the entire field is quietly ignored, making it difficult to troubleshoot downstream behavior.

**Cause**: Lack of input validation and error feedback.

**Affected Versions**: 2.4.0-dev.4

**Fixed Version**: 2.4.2-dev.1

**Fix**: Added `logger.warning()` to log the field information before skipping when a `key` is missing.

**Fix Date**: 2026/04/13

---

### [BUG-010] LazyModule synchronous access to BaseModule causes initialization not to complete

**Issue**: When a user accesses a lazy-loaded BaseModule property in a synchronous context, the module uses `loop.create_task()` for asynchronous initialization but does not wait. This may result in the property not being fully initialized during access, leading to a race condition.

**Cause**: `_ensure_initialized()` returns immediately after using `loop.create_task(self._initialize())` for the BaseModule, without ensuring initialization is complete.

**Affected Versions**: 2.4.0-dev.0 - 2.4.2-dev.1

**Fixed Version**: 2.4.2-dev.2

**Fix**: Changed the BaseModule initialization in synchronous contexts to use `asyncio.run(self._initialize())`, ensuring initialization completes before returning. The transparent proxy behavior is preserved, so users do not need to be aware of the synchronous/asynchronous difference.

**Fix Date**: 2026/04/21

---

### [BUG-011] Multithreaded writing in the configuration system leads to data loss

**Issue**: In a multithreaded environment, when multiple threads call `config.setConfig()` simultaneously, the read-modify-write operation of `_flush_config()` is not atomic, which may result in partial data loss.

**Cause**: Although `_flush_config()` uses an `RLock`, there is no file lock protection between file reading and writing. Additionally, the Timer in `_schedule_write` might be triggered multiple times, leading to overwrites.

**Affected Versions**: 2.3.0 - 2.4.2-dev.1

**Fixed Version**: 2.4.2-dev.2

**Fix**:
1. Added a file lock mechanism (`_file_lock`) to ensure atomicity of file operations.
2. Use temporary files for writing and then rename them atomically (`os.replace`/`os.rename`).
3. Improved the Timer cancellation and rescheduling logic for `_schedule_write`.

**Fix Date**: 2026/04/21

---

### [BUG-012] Inaccurate error message for SDK attribute access

**Issue**: When accessing a non-existent attribute, the error message "You may be using the wrong SDK registration object" may mislead users, when in reality the module may simply not be enabled or the name may be misspelled.

**Cause**: The error message in `__getattribute__` does not distinguish between different scenarios, providing a vague hint uniformly.

**Affected Versions**: 2.0.0 - 2.4.2-dev.1

**Fixed Version**: 2.4.2-dev.2

**Fix**: Distinguish between different scenarios based on the attribute name:
1. Registered but not enabled: Hint that the module/adapter is not enabled.
2. Does not exist at all: Hint to check the name spelling.
Also re-raise the original `AttributeError` to facilitate catching by upper layers.

**Fix Date**: 2026/04/21

---

### [BUG-013] Uninitializer's cleanup logic for uninitialized LazyModule is overly complex

**Issue**: `Uninitializer` creates temporary instances for LazyModules that have never been accessed to call `on_unload`, making the code complex and error-prone.

**Cause**: It attempts to call lifecycle methods for all LazyModules, but uninitialized modules do not need and should not be initialized.

**Affected Versions**: 2.4.0-dev.0 - 2.4.2-dev.1

**Fixed Version**: 2.4.2-dev.2

**Fix**: Simplify the cleanup logic to only handle initialized LazyModules:
1. Skip uninitialized LazyModules without creating temporary instances.
2. Call `on_unload` only for initialized modules.
3. Remove the complex temporary instance creation logic.

**Fix Date**: 2026/04/21

---

### [BUG-014] CTRL+C cannot stop the program on Windows

**Issue**: When running `python main.py` directly on Windows, pressing CTRL+C cannot terminate the program. The program starts normally and outputs routing server information, after which CTRL+C is completely unresponsive, and the process can only be killed via Task Manager. However, starting via `epsdk run` works fine to stop—but `epsdk run` runs via a subprocess model.

**Cause**: Hypercorn ASGI server's `serve()` function internally registers its own SIGINT handler via `signal.signal(SIGINT, handler)`, which overrides Python's default `KeyboardInterrupt` handling mechanism. When Hypercorn is started as a background task via `asyncio.create_task()`, Hypercorn's internal shutdown flow cannot trigger properly (as it expects the `worker_serve` mode), causing the CTRL+C signal to be swallowed by Hypercorn without triggering any cleanup actions.

**Affected Versions**: [2.3.6 - 2.4.2]

**Fixed Version**: 2.4.3-dev.0

**Fix**:
1. Switched the ASGI server from Hypercorn to Uvicorn (change in `pyproject.toml` dependencies).
2. Use `uvicorn.Server._serve()` to start the server directly, **bypassing** the `capture_signals()` signal handling context manager.
3. Implement graceful shutdown via `server.should_exit = True`, cancelling the background task on timeout.
4. Synchronously remove the subprocess runtime model and the `runtime/cleanup.py` cleanup module (subprocess cleanup mechanism is no longer needed).

**Fix Date**: 2026/04/28

---

### [BUG-015] Incorrect sorting logic in module loading strategy

**Issue**: `ModuleLoadStrategy` provides a `priority` field to declare the initialization priority of modules, but the implementation of the loading strategy has a flaw, causing modules to not be initialized in the expected priority order. Instead, they are loaded in the default order of `entry_points()`. When there are loading dependencies between modules, the correct initialization order cannot be guaranteed via `priority`.

**Cause**: The sorting logic in the loading strategy implementation is incorrect, and `initialize_modules()` does not sort the module list by `priority`.

**Affected Versions**: 2.3.4 - 2.4.5-dev.2

**Fixed Version**: 2.4.5-dev.3

**Fix**: Sort the module list by `priority` in descending order before iterating in `initialize_modules()`. Modules with the same priority maintain their original relative order (stable sort).

**Fix Date**: 2026/05/15

---

### [BUG-016] Event data loss due to adapter middleware returning None

**Issue**: When `adapter.emit()` executes the OneBot12 middleware chain, if a middleware returns `None` (for example, forgetting `return data`), the `processed_data` received by subsequent middleware and all event handlers becomes `None`, causing event processing to fail completely.

**Cause**: The implementation of the middleware chain `processed_data = await middleware(processed_data)` does not check if the return value is `None`, directly overwriting the result of the previous step.

**Affected Versions**: unknown - 2.4.5-dev.3

**Fixed Version**: 2.4.5-dev.4

**Fix**: Ignore the return value when middleware returns `None`, preserve the original data to continue passing it, and output a warning-level log.

**Fix Date**: 2026/05/15

---

### [BUG-017] Configuration file path depends on working directory

**Issue**: The configuration file path in `ConfigManager` defaults to the relative path `"config/config.toml"`, relying on `os.getcwd()` to resolve it at runtime. If the working directory changes during runtime (e.g., via `os.chdir()`), read/write operations on the configuration file will point to the wrong location, leading to configuration loss or reading old data.

**Cause**: Relative paths are stored directly in `__init__` without being parsed into absolute paths during initialization.

**Affected Versions**: 2.3.7 - 2.4.5-dev.3

**Fixed Version**: 2.4.5-dev.4

**Fix**: In `ConfigManager.__init__()`, if the passed path is a relative path, automatically resolve it to an absolute path using `os.path.abspath()`.

**Fix Date**: 2026/05/15

---

### [BUG-018] Subprocess mode `ep run <script>` cannot find submodule of script directory

**Issue**: When running a script with `ep r .\main.py` in non-hot-reload mode, if the script has relative imports (e.g., `from qg import ...`), a `No module named 'qg'` error is raised. However, the `--reload` mode runs normally.

**Cause**: The non-hot-reload mode directly calls `runpy.run_path()` to execute the script, which does not automatically add the script's directory to `sys.path`. The `--reload` mode runs via a `subprocess.Popen` subprocess, which inherits the current working directory automatically. Thus, `sys.path[0]` is the script's directory, allowing it to work normally.

**Affected Versions**: 2.5.0 - 2.5.2-dev.0

**Fixed Version**: 2.5.2-dev.0

**Fix**: Manually insert the directory where the script is located into `sys.path[0]` before calling `runpy.run_path()`.

**Fix Date**: 2026/06/27