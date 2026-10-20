# Module Troubleshooting Guide

> [!TIP]
> **When to read this**: When a module "doesn't respond", commands don't trigger, or events aren't received. Skip if not needed; it won't affect other features.

When a module "doesn't respond", symptoms are divided into three types of issues, each with corresponding framework diagnostic tools (RFC EPRFC-2026-001 Direction Five):

| Symptom | Diagnostic Tool | Positioning Level |
|------|---------|---------|
| Module not loaded | `ErisPulse.runtime.explain_module(name)` | Registration and loading chain |
| Event not responded | `ErisPulse.runtime.explain_event(event)` | Distribution entry check |
| Command not triggered | Distribution decision chain (Test side `DispatchTrace` / framework built-in `trace`) | Command determination chain |

Both diagnostic functions are **pure read** operations, do not change any state, and can be called at any time; they return machine-readable dicts, which can be rendered as human-readable text with `format_report()`.

## Scenario 1: Module Not Loaded

```python
from ErisPulse.runtime import explain_module, format_report

report = explain_module("MyModule")
print(format_report(report))
```

`explain_module()` checks each item and provides conclusions, covering the following causes:

| Check Item | Description |
|-------|------|
| Not registered | Package not installed, entry-point group name incorrect, or registration name inconsistent with query name |
| Lazy loading not instantiated | **Normal state, not a fault**: Lazy-loaded modules are instantiated only when first called (`module.call` / command triggered, etc.) |
| Configuration disabled | `ErisPulse.modules.status.<module name> = false` (default enabled if not configured) |
| Dependencies not loaded | There are modules in the module's declared `depends` list that are not ready |
| SDK version not satisfied | The module's metadata declares a `min_sdk_version` higher than the current framework version |
| on_load exception | Registered normally but not loaded and no above reasons — check the ERROR record corresponding to the module name in the startup log |

The returned dict's structured fields: `registered` / `loaded` / `lazy` / `enabled` (`None` means default enabled if not configured) / `missing_dependencies` / `sdk_version_ok` / `conclusion` (one-sentence conclusion) / `reasons` (list of reasons).

## Scenario 2: Event Not Responded

```python
from ErisPulse.runtime import explain_event, format_report

report = explain_event(event)   # Processor gets Event or raw event dict
print(format_report(report))
```

`explain_event()` outputs conclusions in the actual check order of distribution entry points:

1. **Platform adapter not registered**: The `platform` adapter instance does not exist — the event never enters the framework.
2. **Identity dimension rejected by scope**: User / session / Bot / adapter is blacklisted — the event is completely discarded at the distribution entry point. Scope configuration is found in [Module Configuration](../user-guide/configuration.md).
3. **Module blocked by session**: Distinguish between the current session's `available_modules` (available) and `blocked_modules` (blocked by scope).
4. **Text resembles command but not matched**: Has command prefix but does not match any registered command — check prefix configuration and command name.

If entry checks pass but there is still no response, the conclusion will guide further checks at two locations:

- **Processor filtering conditions**: `detail_type` / `pattern=` / `regex=` conditions are not met;
- **Middleware rejection**: Middleware explicitly returning `False` discards the event at the event level and triggers the `adapter.event.blocked` lifecycle hook (carrying middleware name and full event) — you can register this hook to audit "who discarded the event".

## Scenario 3: Command Not Triggered (Distribution Decision Chain)

For a message with a prefix to truly execute a command, it must sequentially pass through: command text determination → command match (with spelling suggestions if not matched) → scope → user ACL → owner check → permission function → cooldown / rate limiting / usage silently discarded → deprecated rejection and notification → parameter parsing → execution. The framework records each decision point as a causal chain, providing a conclusion on "why it wasn't triggered."

### In Testing: TestBot.dispatch returns DispatchTrace

It is recommended to use testing to reproduce the issue and directly read the causal chain (tool usage is described in [Module Testing](testing.md)):

```python
trace = await bot.dispatch(create_command_event("dailyx", user_id="123"))

trace.verdict          # executed / rejected / dropped / failed / no_match / passed
print(trace.explain()) # Line-by-line causal explanation (current language)
trace.assert_no_match()
```

### Framework Built-in trace Module

The decision chain is provided by `ErisPulse.Core.Event.trace`, defaulting to **zero overhead** — decision points are skipped when not in the collection context, and the production path is imperceptible:

```python
from ErisPulse.Core.Event import (
    start_dispatch_trace,
    format_dispatch_trace,
    final_verdict,
)

with start_dispatch_trace() as records:
    ...  # Collect distribution events (including their derived processor tasks) within the collection context

print(format_dispatch_trace(records))   # Human-readable causal chain (current language)
print(final_verdict(records))           # Overall conclusion
```

The `final_verdict()` values:

| Conclusion | Meaning |
|------|------|
| `executed` | Command executed |
| `rejected` | Rejected by permission-type determination (scope / ACL / owner / permission function) |
| `dropped` | Silently discarded (cooldown / rate limit / usage / middleware rejection) |
| `failed` | Execution error |
| `no_match` | Has prefix but does not match any command |
| `passed` | Non-command text, passed to message processor |

Records are machine-readable dicts (`stage` / `verdict` / `message_key` / `params`), and custom displays can filter by `stage` (e.g., only see `cooldown`).

### Identifying Governance-Type Silent Matches

When `cooldown=` / `rate_limit=` / `usage_limit=` is matched, it is **silently discarded by default** (command is still claimed, not passed to lower-priority processors), which can be mistaken for a "broken command": the phenomenon is that some users can use it, some users have no response, and the corresponding `stage`'s `dropped` record appears in the decision chain. Deprecated commands (`deprecated=`) manifest as automatically replying with deprecation text upon invocation (`deprecated_reject=True` rejects execution).

## Scenario 4: After Code Changes Reload, Still Old Behavior (2.11+)

Check in order:

1. **Check return values and failure scenarios**: When `reload` / `load` returns `False`, directly call `sdk.module.last_error("module name")` — returns exception and full traceback (including line numbers), no need to search log files; `module.get_info(name)["last_error"]` is the same source.
2. **Syntax errors won't unload**: `reload` performs a syntax pre-check before unloading; if it fails, it is rejected (old instance continues to serve), and the log gives file + line number; fix the syntax and reload again.
3. **Identity unchanged warning**: When the log shows "code identity unchanged after reload" or the event `identity_changed: false`, it means the old code is still running in the process (common for C extensions with non-clearable caches) — such modules need a framework restart.
4. **Confirm module source is reloadable**: Modules registered at runtime (`sdk.module.register()`) are refused to reload if the class definition is in `__main__` / entry script (guard warning); move the class to a reloadable module file.
5. **Lazy-loaded modules forcibly activated**: Reloading activates modules that were originally lazy-loaded (explicit log); modules in sleep (dormant) state remain dormant.

## Scenario 5: Module "Enabled but Not Receiving Events" (Lazy-loaded Dormant, 2.11+)

A lazy-loaded module declared with `dormant_after` will **automatically go dormant** after idle time exceeds the threshold: runtime resources are released, event handlers are unregistered, so it no longer receives events (except those declared in `activate_on` — events first wake up then forward).

- **Confirm if dormant**: Search logs for "dormant" / `module.sleep` events, or observe `sdk.module.get_status_summary()` where the module is no longer `loaded`.
- **Wake up immediately**: Any attribute access (`sdk.module_name.any_attribute`) or `await sdk.module.call(...)`.
- **Don't want automatic dormancy**: Remove the `dormant_after` declaration in `get_load_strategy()`.
- **State lost?**: Before dormancy, `on_before_unload(reason="dormant")` is triggered; if the module does not implement this hook to save state, dormancy loses memory state (same as unloading) — for continued state, refer to [Lazy Loading Dormant](../advanced/lazy-loading.md#lazy-loading-dormant-dormant_after).

## General Recommendations

- Before troubleshooting, set logs to `DEBUG` / `TRACE` (configuration in [Developer Guide](README.md#Debugging_Tips)) to see internal framework processes such as module loading, routing registration, and event distribution;
- `explain_module` / `explain_event` can be called anytime, pure read, no side effects, suitable for direct attachment to operations commands or management panels;
- For "command not triggered" issues, first write a `DispatchTrace` assertion test to reproduce — `assert_executed` / `assert_rejected` assertion failures will automatically include the full causal chain.