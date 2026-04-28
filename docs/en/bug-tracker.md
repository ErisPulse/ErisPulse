# Bug Tracker

This document records known bugs and their fixes for the ErisPulse SDK.

---

## Fixed Bugs

### [BUG-001] Init Command Adapter Configuration Path Type Error

**Issue**: When performing interactive initialization using the `ep init` command, a type error occurs when selecting the configuration adapter:

```
Interactive initialization failed: unsupported operand type(s) for /: 'str' and 'str'
```

**Root Cause**: In version 2.3.7, when adjusting the configuration file path, the method parameter types were inconsistent. `_configure_adapters_interactive_sync` accepts a `str` type parameter, but internally uses the `/` operator of `Path` to concatenate paths.

**Affected Versions**: 2.3.7 - 2.3.9-dev.1

**Fixed Version**: 2.3.9-dev.1

**Fix Details**: Changed the parameter type of the `_configure_adapters_interactive_sync` method from `str` to `Path`, and passed the `Path` object directly when calling.

**Fix Date**: 2026/03/23

---

### [BUG-002] Command Events Fail After Restart

**Issue**: After calling `sdk.restart()`, commands registered via `@command` cannot be triggered, manifesting as the bot being unresponsive after commands are sent.

**Root Cause**: After `adapter.shutdown()` clears the event bus, the `_linked_to_adapter_bus` state of `BaseEventHandler` was not reset to `False`. This caused the `_process_event` method to believe it was already mounted to the adapter bus, thus skipping the re-mounting operation.

**Affected Versions**: 2.2.x - 2.4.0-dev.2

**Fixed Version**: 2.4.0-dev.3

**Fix Details**: Introduced `_linked_to_adapter_bus` state tracking. After `_clear_handlers()` disconnects the bus, the next `register()` automatically re-mounts, adapting to shutdown/restart scenarios.

**Fix Date**: 2026/04/09

---

### [BUG-003] Lifecycle Event Handlers Not Cleared

**Issue**: After `sdk.restart()`, old lifecycle event handlers still exist and are triggered repeatedly, causing the same event to be processed multiple times.

**Root Cause**: The `lifecycle._handlers` dictionary was never cleared during `uninit()`. After restart, old and new handlers existed simultaneously.

**Affected Versions**: 2.3.0 - 2.4.0-dev.2

**Fixed Version**: 2.4.0-dev.3

**Fix Details**: Cleared `lifecycle._handlers` at the end of the `Uninitializer` cleanup process (after all events are submitted).

**Fix Date**: 2026/04/09

---

### [BUG-004] Event.confirm() Confirmation Word Set Duplicate Assignment

**Issue**: In the `Event.confirm()` method, the assignment code for the three variables `_yes`, `_no`, and `_all` is completely duplicated twice (6 lines in total), resulting in meaningless redundant calculations.

**Root Cause**: Code copy-paste error.

**Affected Versions**: 2.4.0-dev.4

**Fixed Version**: 2.4.2-dev.1

**Fix Details**: Deleted the duplicate assignment code in lines 739-741 of `wrapper.py`.

**Fix Date**: 2026/04/13

---

### [BUG-005] MessageBuilder.at Method Definition Overridden (Dead Code)

**Issue**: The `at` method in the `MessageBuilder` class is defined three times: once as an instance method, once as a static method, and finally overridden by a `_DualMethod` assignment. The first two definitions are dead code that will never be executed.

**Root Cause**: When refactoring to the `_DualMethod` dual-mode descriptor, the old manual definitions were not removed.

**Affected Versions**: 2.4.0-dev.0

**Fixed Version**: 2.4.2-dev.1

**Fix Details**: Deleted the two dead `at` method definitions in lines 159-181 of `message_builder.py`, keeping only the `_DualMethod` assignment.

**Fix Date**: 2026/04/13

---

### [BUG-006] `detail_type` of `Event.is_friend_add/is_friend_delete` Inconsistent with OB12 Standard

**Issue**: `Event.is_friend_add()` checks `detail_type == "friend_add"`, and `Event.is_friend_delete()` checks `detail_type == "friend_delete"`, but the OneBot12 standard defines the `detail_type` values as `"friend_increase"` and `"friend_decrease"`. This is inconsistent with the values used by the `on_friend_add`/`on_friend_remove` decorators in `notice.py`, causing the corresponding `is_friend_add()`/`is_friend_delete()` determination methods to return `False` when handlers registered via decorators are triggered.

**Root Cause**: Non-standard naming was used in `wrapper.py`, whereas correct OB12 standard naming was used in `notice.py`.

**Affected Versions**: Since rq implementation

**Fixed Version**: 2.4.2-dev.1

**Fix Details**: Changed the matching value for `is_friend_add()` from `"friend_add"` to `"friend_increase"`, and for `is_friend_delete()` from `"friend_delete"` to `"friend_decrease"`.

**Fix Date**: 2026/04/13

---

### [BUG-007] `adapter.clear()` Fails to Clear `_started_instances` Causing Incorrect Status After Restart

**Issue**: The `AdapterManager.clear()` method cleared `_adapters`, `_adapter_info`, handlers, and `_bots`, but missed the `_started_instances` set. If `clear()` is called while the adapter is running, `_started_instances` retains dangling references, leading to incorrect status judgment after restart.

**Root Cause**: When `_started_instances` was introduced in version 2.4.0-dev.1, it was not synchronously cleared in `clear()`.

**Affected Versions**: 2.4.0-dev.1 - 2.4.2-dev.0

**Fixed Version**: 2.4.2-dev.1

**Fix Details**: Added `self._started_instances.clear()` to the `clear()` method.

**Fix Date**: 2026/04/13

---

### [BUG-008] `command.wait_reply()` Uses Deprecated `asyncio.get_event_loop()`

**Issue**: The `CommandHandler.wait_reply()` method uses `asyncio.get_event_loop()` to create a future and get the timestamp. This method is deprecated in Python 3.10+, and `asyncio.get_running_loop()` should be used in asynchronous contexts. This is inconsistent with `get_running_loop()` used by the `wait_for()` method in the same file `wrapper.py`.

**Root Cause**: The old API was used during development, and the subsequently added `wait_for()` used the correct API, but the old code was not fixed retrospectively.

**Affected Versions**: 2.3.0-dev.0

**Fixed Version**: 2.4.2-dev.1

**Fix Details**: Replaced both instances of `asyncio.get_event_loop()` in `command.py` with `asyncio.get_running_loop()`.

**Fix Date**: 2026/04/13

---

### [BUG-009] `Event.collect()` Silently Skips When Field is Missing `key`

**Issue**: When iterating through the field list, the `Event.collect()` method silently skips fields if the field dictionary is missing a `key`, without outputting any logs or warnings. If a developer makes a typo (e.g., `"Key"` instead of `"key"`), the entire field is quietly ignored, making downstream behavior difficult to troubleshoot.

**Root Cause**: Lack of input validation and error feedback.

**Affected Versions**: 2.4.0-dev.4

**Fixed Version**: 2.4.2-dev.1

**Fix Details**: Added `logger.warning()` before skipping to record information about the field missing the `key`.

**Fix Date**: 2026/04/13

---

### [BUG-010] LazyModule Synchronous Access to BaseModule Leads to Incomplete Initialization

**Issue**: When a user accesses a lazily loaded BaseModule attribute in a synchronous context, the module uses `loop.create_task()` for asynchronous initialization but does not wait, causing the attribute access to potentially occur before initialization is complete, leading to a race condition.

**Root Cause**: `_ensure_initialized()` returns immediately after using `loop.create_task(self._initialize())` for BaseModule, without ensuring initialization is complete.

**Affected Versions**: 2.4.0-dev.0 - 2.4.2-dev.1

**Fixed Version**: 2.4.2-dev.2

**Fix Details**: In a synchronous context, BaseModule initialization is changed to use `asyncio.run(self._initialize())` to ensure initialization is complete before returning. Maintains transparent proxy characteristics, so users do not need to perceive the synchronous/asynchronous difference.

**Fix Date**: 2026/04/21

---

### [BUG-011] Configuration System Multi-threaded Write Causes Data Loss

**Issue**: In a multi-threaded environment, when multiple threads call `config.setConfig()` simultaneously, the read-modify-write operation of `_flush_config()` is not atomic, potentially causing partial writes to be lost.

**Root Cause**: Although `_flush_config()` uses `RLock`, there is no file lock protection between file reading and writing, and the Timer for `_schedule_write` may be triggered multiple times causing overwrites.

**Affected Versions**: 2.3.0 - 2.4.2-dev.1

**Fixed Version**: 2.4.2-dev.2

**Fix Details**:
1. Added file lock mechanism (`_file_lock`) to ensure file operation atomicity.
2. Use atomic rename (`os.replace`/`os.rename`) after writing to a temporary file.
3. Improved the Timer cancellation and rescheduling logic for `_schedule_write`.

**Fix Date**: 2026/04/21

---

### [BUG-012] SDK Attribute Access Error Message Inaccurate

**Issue**: When accessing a non-existent attribute, the error message "You may be using the wrong SDK registration object" may mislead users. The actual issue could be that the module is not enabled or the name is misspelled.

**Root Cause**: The error message in `__getattribute__` does not distinguish between different scenarios and uniformly provides a vague hint.

**Affected Versions**: 2.0.0 - 2.4.2-dev.1

**Fixed Version**: 2.4.2-dev.2

**Fix Details**: Distinguishes different scenarios based on the attribute name:
1. Registered but not enabled: Prompts that the module/adapter is not enabled.
2. Does not exist at all: Prompts to check name spelling.
Also re-raises the original AttributeError to facilitate catching by upper layers.

**Fix Date**: 2026/04/21

---

### [BUG-013] Uninitializer Cleanup Logic for Uninitialized LazyModule Too Complex

**Issue**: The `Uninitializer` creates temporary instances for LazyModules that have never been accessed to call `on_unload`, resulting in complex and error-prone code.

**Root Cause**: Attempted to call lifecycle methods for all LazyModules, but uninitialized modules do not need and should not be initialized.

**Affected Versions**: 2.4.0-dev.0 - 2.4.2-dev.1

**Fixed Version**: 2.4.2-dev.2

**Fix Details**: Simplified cleanup logic to only handle initialized LazyModules:
1. Skips uninitialized LazyModules without creating temporary instances.
2. Calls `on_unload` only for initialized modules.
3. Deletes complex temporary instance creation logic.

**Fix Date**: 2026/04/21

---

### [BUG-014] Cannot Stop Program with CTRL+C on Windows

**Issue**: When running `python main.py` directly on Windows, pressing CTRL+C cannot terminate the program. The program starts normally and outputs the routing server information, but CTRL+C is completely unresponsive, forcing process termination through the Task Manager. However, when started with `epsdk run`, it stops normally—but `epsdk run` runs through a subprocess model.

**Root Cause**: The `serve()` function of the Hypercorn ASGI server internally registers its own SIGINT handler through `signal.signal(SIGINT, handler)`, overriding Python's default `KeyboardInterrupt` handling mechanism. When Hypercorn is started as a background task via `asyncio.create_task()`, Hypercorn's internal shutdown process cannot be properly triggered (because it expects `worker_serve` mode), causing the CTRL+C signal to be swallowed by Hypercorn without triggering any cleanup actions.

**Affected Versions**: [2.3.6 - 2.4.2]

**Fixed Version**: 2.4.3-dev.0

**Fix Details**:
1. Switched the ASGI server from Hypercorn to Uvicorn (dependency change in `pyproject.toml`)
2. Use `uvicorn.Server._serve()` to directly start the server, **bypassing** the `capture_signals()` signal handling context manager
3. Achieve graceful shutdown via `server.should_exit = True`, with timeout cancelling the background task
4. Synchronously removed the subprocess running model and `runtime/cleanup.py` cleanup module (subprocess cleanup mechanism is no longer needed)

**Fix Date**: 2026/04/28