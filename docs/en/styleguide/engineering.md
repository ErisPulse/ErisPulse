# Engineering Robustness Rules

This page defines the robustness discipline for the ErisPulse source code. Each rule explains the "why" along with real cases from this repository; please read through this page before contributing code—the parts outside CI are enforced through code review.

## 1. Tiered Exception Traceability

An `except` block is not a garbage can. What you do after catching an exception depends on what you are swallowing:

| Category | Criteria | Handling |
|------|------|------|
| Probing | A safe default exists after failure, and failure is harmless (e.g., probing for an instance attribute name and falling back to the class name) | `pass` is acceptable |
| Degradation | Execution falls back to an alternative path after failure, but the failure is still worth knowing about (e.g., an optional dependency is missing) | Leave a `logger.debug` trace |
| Resource release | Shutdown paths for connections, file handles, threads, and tasks | At least `logger.debug`; escalate to `warning` if repeated |
| Data writing | Write paths for configuration persistence, message recording, and state persistence | Start at `warning`—silent data loss cannot be investigated after the fact |

**Double-layer degradation is forbidden**: do not wrap the "logging call itself" in another `try/except: pass`—an alert that disappears under exceptional conditions is no alert at all.

Negative examples (all fixed, kept as cautionary references):

- The final flush failure inside the configuration manager's `close()` was silently swallowed—a user modified the configuration and shut down the process, and the changes were lost without a trace
- When the HTTP client replaced a session, the old session's `close()` failure was silently swallowed—connection resource leak
- The `warning` for repeated initialization calls was itself wrapped in `try/except: pass`—the alert disappeared when i18n was not yet ready

## 2. Log Level Discipline

- **Failure events are at least `warning`**: retry exhaustion, rollback triggered, subscriber callback failure, state replay failure—these mean "system state deviates from expectations"; at `debug` level they are invisible to users
- **Failures inside loops must be throttled**: repeated exceptions in sweep loops, watchers, and background GC should use "first-occurrence warning + subsequent counting/cool-down" or be downgraded to `debug` with periodic summaries, to prevent log flooding
- `trace` is reserved for the normal flow of high-frequency hot paths; `error` is reserved for failures that have already affected request results

## 3. Centralized Behavioral Parameters

Timeouts, retry counts, cool-down periods, and polling intervals must all be defined in `Core/constants.py` (CLI-side behavioral parameters go into this file as well), named `*_TIMEOUT_SECS` / `*_RETRY_*` / `*_COOLDOWN_SECS`, with a comment stating where each is used. Bare numeric timeouts (`timeout=30`, `sleep(5)`) are forbidden in implementation files—bare values with the same semantics scattered across multiple places are where drift begins.

**Scope**: this rule applies to the core repository; third-party modules / adapters are advised to centralize behavioral parameters within their own modules, but are not required to place them in `Core/constants.py`.

## 4. Public API Contract

Classes and methods without a leading underscore must have, simultaneously: a complete docstring (see the [Docstring Style Guide](docstring.md)) and type annotations for all parameters and return values. Internal implementations (`_`-prefixed) may be more relaxed, but once they appear in documentation or examples they are held to the public standard.

**Legacy boundary**: the above requirements apply to **newly added / touched files**; retroactively backfilling the entire legacy codebase is not enforced. Legacy issues are presented as a baseline in checks, and once a file is touched, its legacy issues escalate to blocking.

## 5. No Singleton Back-References

Framework components (managers, loaders, base classes) must not hold back-reference fields to the "root SDK singleton":

- A back-reference field couples the component's lifecycle with assembly order; once the assembler forgets to wire it up, the feature **silently fails** instead of raising an error—this project once had hot-reload/dependency notification silently broken across six release versions because the caller of `set_sdk_ref` was removed
- When a root reference is needed, use either constructor injection (passed in by the composition root) or lazy resolution (import on first use)—pick one; lazy resolution can never "forget to be called"
- When you need another component's state, prefer event subscription or the facade over reaching into someone else's registry; a manager instance's own state must be cleaned up by itself and must not be routed through the global facade (the facade internally is a singleton back-reference and cannot cover independent instances)

## 6. Cleanup and Rollback Discipline

- Uninstall/cleanup paths must be idempotent: retrying after a mid-way failure or uninstalling repeatedly must not double-release or raise errors
- Take a snapshot before irreversible operations (uninstall, reload, config deletion); snapshot rollback has "best-effort" semantics, and a failed rollback must leave a `warning`
- Cleanup order: task cancellation → connection shutdown → external hooks → registry reclamation; each step fails independently, and a single step's failure must not block the following ones

## 7. Testing Discipline

- Every behavior change requires a test change; every bug fix must first have a red test that reproduces the bug
- Exception paths and boundaries (empty inputs, timeouts, repeated calls, partial initialization) are treated on par with normal paths—the regression safety net is what gives you the confidence to refactor
- Tests are allowed to access internal structures, but access points should be centralized: when the internal layout changes, migrating tests means changing imports and paths, not assertion semantics

**Legacy boundary**: the above discipline applies to **newly added / touched files**; retroactively backfilling tests across the entire legacy codebase is not enforced. Legacy coverage gaps are presented as a baseline in checks, and once a file is touched, its legacy issues escalate to blocking.