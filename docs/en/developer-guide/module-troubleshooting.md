# Module Troubleshooting Guide

When a module "doesn't respond," it can be categorized into three types of issues, each with corresponding framework diagnostic tools (RFC EPRFC-2026-001 Direction Five):

| Symptom | Diagnostic Tool | Diagnostic Level |
|---------|----------------|------------------|
| Module not loaded | `ErisPulse.runtime.explain_module(name)` | Registration and loading chain |
| Event not handled | `ErisPulse.runtime.explain_event(event)` | Distribution entry point check |
| Command not triggered | Distribution decision chain (test side `DispatchTrace` / framework built-in `trace`) | Command determination chain |

Both diagnostic functions are **pure read** operations, do not change any state, and can be called at any time; they return a machine-readable dict, which can be rendered into human-readable text using `format_report()`.

## Scenario 1: Module Not Loaded

```python
from ErisPulse.runtime import explain_module, format_report

report = explain_module("MyModule")
print(format_report(report))
```

`explain_module()` checks each item and provides a conclusion, covering the following reasons:

| Check Item | Description |
|-------|------|
| Not Registered | The package is not installed, the entry-point group name is incorrect, or the registered name does not match the query name |
| Lazy Loading Not Instantiated | **Normal state, not a fault**: The lazy-loaded module is instantiated only when it is first called (e.g., `module.call` / command triggered) |
| Configuration Disabled | `ErisPulse.modules.status.<module_name> = false` (default enabled if not configured) |
| Dependencies Not Loaded | There are modules in the module's declared `depends` list that are not ready |
| SDK Version Not Satisfied | The module's metadata declares a `min_sdk_version` higher than the current framework version |
| on_load Exception | Registered normally but not loaded and none of the above reasons apply—check the ERROR record corresponding to the module name in the startup log |

The returned dict contains structured fields: `registered` / `loaded` / `lazy` / `enabled` (`None` means default enabled if not configured) / `missing_dependencies` / `sdk_version_ok` / `conclusion` (a one-sentence conclusion) / `reasons` (list of reasons).

## Scenario 2: Event Not Responding

```python
from ErisPulse.runtime import explain_event, format_report

report = explain_event(event)   # Event received within the processor or the original event dict
print(format_report(report))
```

`explain_event()` outputs conclusions in the actual order of checks at the distribution entry point:

1. **Platform Adapter Not Registered**: The adapter instance corresponding to `platform` does not exist—the event never enters the framework.
2. **Identity Dimension Rejected by Scope**: The user/session/Bot/adapter is blacklisted—the event is completely discarded at the distribution entry point. See [Module Configuration](../user-guide/configuration.md) for scope configuration.
3. **Module Blocked by Session**: Distinguish between the current session's `available_modules` (available) and `blocked_modules` (blocked by scope).
4. **Text Resembles Command but Not Matched**: The text has a command prefix but does not match any registered command—check the prefix configuration and command name.

If all entry point checks pass but there is still no response, the conclusion will guide you to further check two places:

- **Processor Filter Conditions**: Conditions such as `detail_type` / `pattern=` / `regex=` are not satisfied;
- **Middleware Rejection**: Middleware explicitly returning `False` will discard the event at the event level and trigger the `adapter.event.blocked` lifecycle hook (carrying the middleware name and the full event)—you can register this hook to audit "who discarded the event."

## Scenario 3: Command Not Triggered (Dispatch Decision Chain)

For a message with a prefix to truly execute a command, it must sequentially pass through: command text determination → command match (with spelling suggestions if not matched) → scope → user ACL → owner check → permission function → cooldown / rate limiting / usage silent discard → deprecated rejection and notification → parameter parsing → execution. The framework records each decision point as a causal chain, providing a conclusion on "why the command was not triggered."

### Testing: TestBot.dispatch returns DispatchTrace

It is recommended to use tests to reproduce issues and directly read the causal chain (tool usage is described in [Module Testing](testing.md)):

```python
trace = await bot.dispatch(create_command_event("dailyx", user_id="123"))

trace.verdict          # executed / rejected / dropped / failed / no_match / passed
print(trace.explain()) # Line-by-line causal explanation (in current language)
trace.assert_no_match()
```

### Framework Built-in trace Module

The decision chain is provided by `ErisPulse.Core.Event.trace`, with **zero overhead** by default — decision points are skipped when not within a collection context, and the production path remains unaffected:

```python
from ErisPulse.Core.Event import (
    start_dispatch_trace,
    format_dispatch_trace,
    final_verdict,
)

with start_dispatch_trace() as records:
    ...  # Collect dispatch events (including their derived handler tasks) within the collection context

print(format_dispatch_trace(records))   # Human-readable causal chain (in current language)
print(final_verdict(records))           # Overall conclusion
```

The values of `final_verdict()` are:

| Conclusion | Meaning |
|------------|---------|
| `executed` | The command was executed |
| `rejected` | Rejected by permission-related checks (scope / ACL / owner / permission function) |
| `dropped` | Silently discarded (cooldown / rate limiting / usage / middleware rejection) |
| `failed` | Execution failed |
| `no_match` | Message has a prefix but does not match any command |
| `passed` | Not a command text, passed to the message handler |

The records are in machine-readable dict format (`stage` / `verdict` / `message_key` / `params`), and custom display can filter by `stage` (e.g., only show `cooldown`).

### Identifying Governance Silent Matches

When `cooldown=`, `rate_limit=`, or `usage_limit=` are triggered, they are **silently discarded by default** (the command is still claimed, not passed to lower-priority handlers), which can be mistaken for a "broken command": the phenomenon is that some users can use it while others get no response, and the corresponding `stage`'s `dropped` record appears in the decision chain. Deprecated commands (`deprecated=`) automatically reply with the deprecation message upon invocation (rejected from execution when `deprecated_reject=True`).

## General Recommendations

- Before troubleshooting, set the log level to `DEBUG` / `TRACE` (see [Developer Guide](README.md#Debugging_Tips) for configuration). This will show internal framework processes such as module loading, route registration, and event dispatching;
- `explain_module` / `explain_event` can be called at any time and are purely read-only with no side effects, making them suitable for direct attachment to operations commands or management panels;
- For issues related to commands not triggering, first write a `DispatchTrace` assertion test to reproduce the problem—when assertions like `assert_executed` / `assert_rejected` fail, a complete causal chain will be automatically provided.