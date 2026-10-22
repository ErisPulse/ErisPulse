# Module Troubleshooting Guide

> [!TIP]
> **When to read this**: When your bot "doesn't respond" — a module is installed but not loaded, commands get no reply, event handlers don't execute, code still behaves the old way after reload, or a module is clearly enabled yet receives no events — find the matching scenario by symptom. Skip this if not needed; it does not affect the use of other features.

When a module "doesn't respond", troubleshoot by symptom against the corresponding scenario; the first three scenario categories have framework diagnostic tools that give conclusions directly:

| Symptom | Diagnostic Tool | Located Layer |
|------|---------|---------|
| Module not loaded | `ErisPulse.runtime.explain_module(name)` | Registration and loading chain |
| Event not responded | `ErisPulse.runtime.explain_event(event)` | Dispatch entry check |
| Command not triggered | Dispatch decision chain (test-side `DispatchTrace` / built-in `trace`) | Command judgment chain |

Both diagnostic functions are **pure read** operations that change no state and can be called at any time; they return machine-readable dicts, and `format_report()` renders them into human-readable text.

## Scenario 1: Module Not Loaded

```python
from ErisPulse.runtime import explain_module, format_report

report = explain_module("MyModule")
print(format_report(report))
```

`explain_module()` checks item by item and gives a conclusion, covering the following causes:

| Check Item | Description |
|-------|------|
| Not registered | Package not installed, wrong entry-point group name, or the registered name differs from the queried name |
| Lazy-loaded, not yet instantiated | **Normal state, not a fault**: lazy-loaded modules are only instantiated upon first invocation (`module.call` / command trigger, etc.) |
| Disabled by config | `ErisPulse.modules.status.<module_name> = false` (enabled by default when unconfigured) |
| Dependencies not loaded | Some modules in the module's declared `depends` list are not ready |
| SDK version requirement unmet | The `min_sdk_version` declared in the module metadata is higher than the current framework version |
| on_load exception | Registered normally but not loaded with none of the above causes — check the startup logs for ERROR entries matching the module name |

Structured fields of the returned dict: `registered` / `loaded` / `lazy` / `enabled` (`None` means unconfigured, i.e. enabled by default) / `missing_dependencies` / `sdk_version_ok` / `conclusion` (a one-sentence conclusion) / `reasons` (a list of reasons).

## Scenario 2: Event Not Responding

```python
from ErisPulse.runtime import explain_event, format_report

report = explain_event(event)   # The Event obtained inside the handler or the raw event dict
print(format_report(report))
```

`explain_event()` outputs conclusions in the actual check order of the dispatch entry:

1. **Platform adapter not registered**: no adapter instance exists for the corresponding `platform` — the event never entered the framework at all.
2. **Identity dimension rejected by scope**: the user / session / Bot / adapter is blacklisted — the event is dropped entirely at the dispatch entry. For scope configuration, see [Module Configuration](../user-guide/configuration.md).
3. **Module blocked by session**: distinguish the current session's `available_modules` (available) from `blocked_modules` (blocked by scope).
4. **Text looks like a command but no match**: it carries the command prefix but is not any registered command — check the prefix configuration and command names.

When all entry checks pass but there is still no response, the conclusion will direct you to check two more places:

- **Handler filter conditions**: conditions such as `detail_type` / `pattern=` / `regex=` are not satisfied;
- **Middleware veto**: a middleware explicitly returning `False` drops the event at the event level and triggers the `adapter.event.blocked` lifecycle hook (carrying the middleware name and the full event) — you can register this hook to audit "who dropped the event".

## Scenario 3: Command Not Triggered (Dispatch Decision Chain)

For a prefixed message to actually execute a command, it must pass through in sequence: command text judgment → command match (with spelling suggestions on miss) → scope → user ACL → master check → permission function → silent drop by cooldown / rate limit / usage → deprecation rejection with notice → argument parsing → execution. The framework records each judgment point as a causal chain and gives a conclusion on "why it wasn't triggered".

### In tests: TestBot.dispatch returns a DispatchTrace

It is recommended to reproduce the problem in a test and then read the causal chain directly (for tool usage, see [Module Testing](testing.md)):

```python
trace = await bot.dispatch(create_command_event("dailyx", user_id="123"))

trace.verdict          # executed / rejected / dropped / failed / no_match / passed
print(trace.explain()) # Line-by-line causal explanation (in the current language)
trace.assert_no_match()
```

### Framework built-in trace module

The decision chain is provided by `ErisPulse.Core.Event.trace`, which is **zero-overhead** by default — when not inside a collection context, judgment points are skipped directly, leaving the production path unaffected:

```python
from ErisPulse.Core.Event import (
    start_dispatch_trace,
    format_dispatch_trace,
    final_verdict,
)

with start_dispatch_trace() as records:
    ...  # Dispatches occurring within the collection context (including their derived handler tasks)

print(format_dispatch_trace(records))   # Human-readable causal chain (in the current language)
print(final_verdict(records))           # Overall verdict
```

Possible values of `final_verdict()`:

| Verdict | Meaning |
|------|------|
| `executed` | The command was executed |
| `rejected` | Rejected by a permission-type judgment (scope / ACL / master / permission function) |
| `dropped` | Silently dropped (cooldown / rate limit / usage / middleware veto) |
| `failed` | An error occurred during execution |
| `no_match` | Prefixed but matched no command |
| `passed` | Non-command text, passed through to message handlers |

Records are machine-readable dicts (`stage` / `verdict` / `message_key` / `params`); for custom display you can filter by `stage` (e.g., only view `cooldown`).

### Distinguishing silent hits from governance limits

When `cooldown=` / `rate_limit=` / `usage_limit=` are hit, they are **silently dropped by default** (the command is still claimed, and is not leaked to lower-priority handlers), which can easily be misjudged as "the command is broken": the symptom is that some users can use it while others get no response, and the decision chain shows `dropped` records for the corresponding `stage`. A `deprecated=` command, on the other hand, automatically replies with the deprecation notice when invoked (and refuses execution when `deprecated_reject=True`).

## Scenario 4: Code Still Behaves the Old Way After reload (2.11+)

Check in order:

1. **Check the return value and the failure scene**: when `reload` / `load` returns `False`, directly call
   `sdk.module.last_error("module_name")` — it returns the exception and the full traceback (including the error line number),
   so there is no need to dig through log files; `module.get_info(name)["last_error"]` comes from the same source.
2. **Syntax errors do not unload**: reload performs a syntax precheck before unloading and refuses on failure (the old instance keeps serving);
   the log gives the file + line number; fix the syntax and reload again.
3. **Identity unchanged warning**: when the log shows "code identity unchanged after reload" or the event carries `identity_changed: false`,
   it means the old code is still running in the process (common with C extensions and other caches that cannot be cleared) — such modules require a framework restart.
4. **Confirm the module source is re-importable**: for modules registered at runtime (`sdk.module.register()`), re-import is refused when the class is defined in
   `__main__` / the entry script (guard warning); please move the class into an importable module file.
5. **Lazy-loaded modules get forcibly activated**: reloading activates modules that were originally lazy-loaded (with an explicit log); modules in dormancy
   (sleep) remain dormant.

## Scenario 5: Module "Clearly Enabled But Not Receiving Events" (Lazy Loading Dormancy, 2.11+)

A lazy-loaded module that declares `dormant_after` will **automatically go dormant** after idling past the threshold: runtime resources are released and
event handlers are unregistered, so it no longer receives events (except events declared in `activate_on` — such events wake it up first and are then forwarded).

- Confirm whether it is dormant: search the logs for "has gone dormant" / `module.sleep` events, or observe
  `sdk.module.get_status_summary()` where the module is no longer `loaded`
- Wake it immediately: any attribute access (`sdk.<module_name>.<any_attribute>`) or `await sdk.module.call(...)`
- If you do not want auto-dormancy: remove the `dormant_after` declaration from `get_load_strategy()`
- Whether state is lost: before going dormant, `on_before_unload(reason="dormant")` is triggered; if the module does not implement
  this hook to save its state, dormancy loses the in-memory state (same as unloading) — to carry state across, see
  [Lazy Loading Dormancy](../advanced/lazy-loading.md#lazy-loading-dormancydormant_after)

## General Suggestions

- Before troubleshooting, set the log level to `DEBUG` / `TRACE` (for configuration, see [Developer Guide](README.md#debugging-tips)); this lets you see framework internals such as module loading, route registration, and event dispatch;
- `explain_module` / `explain_event` can be called at any time and are pure reads with no side effects, making them suitable to wire directly into ops commands or admin panels;
- For "command not triggered" problems, prefer writing a `DispatchTrace` assertion test to reproduce it — when assertions like `assert_executed` / `assert_rejected` fail, the full causal chain is attached automatically.

## Problem Still Unresolved

- **Check known issues first**: refer to [Bug Tracker](../bug-tracker.md) to confirm whether it is a recorded issue and check for its workaround;
- **Submit feedback**: when reporting to [GitHub Issues](https://github.com/ErisPulse/ErisPulse/issues), attach the output of `explain_module` / `explain_event`, the `DispatchTrace` causal chain, and the framework version number — this can greatly shorten the time to locate the problem;
- **Discussion and help**: when you are unsure whether it is a bug, first describe the symptom and reproduction steps in [Discussions](https://github.com/ErisPulse/ErisPulse/discussions).