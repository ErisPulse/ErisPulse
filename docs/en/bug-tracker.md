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

**Issue**: `Event.is_friend_add()` checks `detail_type == "friend_add"`, and `Event.is_friend_delete()` checks `detail_type == "friend_delete"`, but the OneBot12 standard defines the `detail_type` values as `"friend_increase"` and `"friend_decrease"`. This is inconsistent with the values used by