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