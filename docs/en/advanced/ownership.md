# Ownership (owner) System

> [!TIP]
> **When to read this**: When debugging resource leaks, understanding the unload cleanup chain, or declaring owned resources. Skip it if not needed — doing so does not affect the use of other features.

> **What you will learn**: how the owner context automatically attributes resources, the full inventory of owned
> resources, the complete sequence of the cleanup chain during unload/disable, and which resources
> are not cleaned up on unload (design boundaries).
>
> **Not covered here**: permission decisions on "when a resource takes effect" (see [Scope (scope)](scope.md));
> recommended patterns for background tasks and the boundaries of forced cancellation (see [Lifecycle Management · Background Task Ownership and Auto-Cancellation](lifecycle.md#background-task-ownership-and-auto-cancellation)).


Ownership is the cornerstone of "plug-and-play" modules: every framework resource a module registers during loading
is automatically attributed by name, and on unload/disable all attributed resources are reclaimed in one go —
module authors only need to declare resources, without hand-writing cleanup logic.

> **Related systems**: scope decides "whether a resource takes effect" at event dispatch time,
> while ownership decides, over the lifecycle, "who a resource belongs to and whose unload reclaims it".
> For scopes see [Unified Control Plane (scope)](scope.md); for background tasks see
> [Lifecycle Management](lifecycle.md#background-task-ownership-and-auto-cancellation).

{!--< tips >!--}
1. Attribution is automatically recorded by `current_owner` **at the moment of registration**, with zero changes to module code
2. Unload/disable share the same cleanup chain (`_cleanup_module_registrations`); a failure at any step only logs a warning and does not interrupt
3. Resources with user-configuration semantics (persistent overrides / scope rules / command ACLs) are **not** cleaned up on module unload
4. External handles hosted by tool modules can be hooked into the cleanup chain via `on_cleanup(cb)` and are called back automatically when the other module unloads (see [Tool Module Guide](#tool-module-guide-hosting-handles-of-other-modules))
{!--< /tips >!--}

## owner Context Mechanism

The owner is passed via the context variable `current_owner` (`ErisPulse.runtime.context`):

```python
from ErisPulse.runtime import owner_scope, get_current_owner

with owner_scope("MyModule"):
    # All resources registered within this block are automatically attributed to MyModule
    assert get_current_owner() == "MyModule"
```

The framework automatically injects the owner at the following moments (no manual wrapping needed in module/adapter code):

| Moment | owner value | Location |
|------|----------|------|
| Module `load()` | Module name | Instantiation + the entire `on_load` |
| Adapter `start()` / `restart()` | Platform name | The entire adapter startup |
| `activate_on` lazy-load stub registration | Module name | Placeholder command/handler registration |
| During event handler execution | The module owning the handler | Re-injection at handler / command entry points |

Execution-time re-injection means: when a command handler declared in `on_load` calls
registration APIs **while running** (e.g. `sdk.adapter.on()`, `overrides.*.set(persist=False)`),
those registrations are also automatically attributed to this module.

## Inventory of Owned Resources

All of the following resources registered by a module within its loading context are attributed and automatically reclaimed on unload/disable:

| Resource | Registration | Cleanup call |
|------|----------|----------|
| Commands | `@command()` / command dict declaration | `command.unregister_by_owner()` |
| Event handlers | `@message` / `@notice` / `@request` / `@meta` | `handler.unregister_by_owner()` |
| Adapter event listeners | `sdk.adapter.on()` / `raw=True` | `adapter.unregister_handlers_by_owner()` |
| Adapter middleware | `@sdk.adapter.middleware` | Same as above |
| Routes (HTTP/WS/SSE) | `router.http()` / `websocket()` / `sse()` | Double fallback by namespace + by owner |
| Route middleware | `@router.middleware()` / `add_middleware()` | `router.unregister_all_by_owner()` |
| Dashboard home entries | `router.register_home_entry()` | `unregister_home_entries_by_owner()` |
| Custom session types | `register_custom_type()` | `unregister_custom_types_by_owner()` |
| Platform event method injection | `register_event_method()` / `register_event_mixin()` | `unregister_event_methods_by_owner()` (automatically reclaimed on module unload; old closures no longer leak) |
| Background tasks | `self.spawn()` | `cancel_owner_tasks()` |
| External ownership cleanup hooks (hosted by tool modules) | `runtime.on_cleanup(cb)` | `run_owner_cleanups()` (triggered within the unload/disable/adapter-shutdown chain) |
| Lifecycle hooks | `lifecycle.register()` | `lifecycle.unregister_by_owner()` |
| Master identity provider | `master.provider` | `master.unregister_by_owner()` |
| i18n translation keys | `I18nClass` declaration (domain=module name) | `i18n.unregister_domain()` |
| Event overrides (runtime) | `overrides.*.set(persist=False)` | `overrides.unregister_by_owner()` |
| Interaction sessions (wait_reply waits / leases) | `event.wait_reply()` / `sdk.interaction.acquire()` | `interaction.cancel_by_owner()` (waiting parties receive cancellation immediately) |
| Context data | `runtime/context` recorded per owner | Precisely cleaned per module |

The corresponding adapter-side resources (with the platform name as owner) are reclaimed by `_cleanup_adapter_resources` on adapter `shutdown()` / `restart()`, plus:

| Resource | Cleanup call |
|------|----------|
| The adapter's own `on()` handlers and middleware | `adapter.unregister_handlers_by_owner(platform)` |
| Platform event method extensions (`EventMixin`) | `unregister_platform_event_methods(platform)` |
| Custom session types | `unregister_custom_types_by_owner(platform)` |
| Interaction sessions (pending wait_reply / leases on that platform) | `interaction.cancel_by_platform(platform)` |
| i18n translation domain (domain=config key) | `i18n.unregister_domain(config_key)` |
| Fine-grained namespace routes | `router.unregister_all_by_owner(platform)` |

## Unload/Disable Cleanup Sequence

`unload()` and `disable()` share the same cleanup chain (each step wrapped in its own try/except;
failures are only logged and **do not interrupt subsequent cleanup**):

```mermaid
flowchart TD
    A["unload / disable"] --> B["on_unload() (timeout protection)"]
    B --> C["Fallback cancellation of background tasks (cancel_owner_tasks)"]
    C --> C1["External ownership cleanup hooks<br/>(registered by tool modules via on_cleanup, triggered by run_owner_cleanups)"]
    C1 --> D["_cleanup_module_registrations<br/>= ownership.reclaim_sync() (ownership facade)"]
    D --> D1["i18n translation domains"]
    D1 --> D2["Routes: namespace + owner fallback<br/>(precise removal by route object identity,<br/>including middleware / home entries)"]
    D2 --> D3["Adapter event handlers / middleware"]
    D3 --> D4["Commands + event handlers"]
    D4 --> D5["Custom session types"]
    D5 --> D5b["Platform event method injection"]
    D5b --> D6["Runtime event overrides (persist=False)"]
    D6 --> D7["Master identity provider"]
    D7 --> D8["Lifecycle hooks"]
    D8 --> E["Remove SDK attributes + lazy-load proxies"]
    E --> F["Automatic light audit: orphan owner warnings"]
```

On exit, `sdk.uninit()` additionally performs a global fallback: all adapters shutdown → all modules unload →
`router.stop()` (clearing routes/middleware/home entries) → `cancel_all_background_tasks()` →
clearing event handlers and hooks.

## Unified Ownership Facade (ownership)

The sixteen steps of the cleanup chain converge under the unified ownership facade `ErisPulse.Core.ownership`,
whose four verbs cover "unregistration, counting, scanning, and auditing" — each subsystem's own `*_by_owner`
unregister functions remain unchanged and serve as the facade's internal implementation:

| Verb | Purpose |
|------|------|
| `ownership.reclaim(owner)` | Unified unregistration of all resources under an owner (task cancellation → cleanup hooks → registration-type resources; full async version) |
| `ownership.reclaim_sync(owner)` | Unregistration of registration-type resources (sync version, for the synchronous unload path) |
| `ownership.counts(owner=None)` | Read-only counting of resources registered under an owner (None for all owners) |
| `ownership.orphans()` | Orphan scan: resources still registered while their owner is gone (hard evidence list of leaks) |
| `ownership.audit(owner, deep=)` | Leak audit report (counts + orphans + optional gc instance census) |

```python
from ErisPulse.Core import ownership

ownership.reclaim_sync("MyModule")       # {'commands': 1, 'routes_http': 2, ...}
ownership.counts("MyModule")             # Count of registered resources
ownership.orphans()                      # [{"owner": "ghost", "total": 2, ...}]
```

**Audit entry points**:

- **Automatic light audit** after unload/reload: a WARNING is raised as soon as orphan owner resources are found (zero-cost counting scan)
- `sdk.module.audit(name, deep=True)`: gc census of module instances — when instances cannot be reclaimed,
  it reports the types of the referencing parties (pinpointing "who is holding the old instance"); it carries
  global pause overhead and is meant only for explicit troubleshooting
- The deep census is an explicit operation: no config keys, no automatic repairs

## Hot-Reload Failure Rollback

Hot reload follows "**snapshot before unload → automatic restore on failure → replay on_load**": on syntax errors in
the new version, missing dependencies, or load failures, the old instance and registration state (registry entries,
sdk attributes, sys.modules entries) are automatically restored, after which the old instance's `on_load` is
**replayed within the ownership context** (`reason` is `"rollback"`), so external resources disconnected during
unload are re-established; afterwards a `module.rollback` event is emitted (payload `{module_name, success}`).

Boundary notes:

- Replay failure or timeout **only warns** — no rollback of the rollback; the old instance stays in a
  "finalized" state (consistent with 2.11.2 and earlier behavior), and the logs make this explicit
- References to the old instance manually cached by third parties at runtime are not covered by restoration
- If the target package has already been uninstalled (entry-point gone), it is treated as a successful unload and no rollback is performed
- The `on_unload` payload carries `reason` (`unload` / `reload` / `disable` /
  `cascade` / `dormant` / `load-failed`), so modules can defer closing
  resources that need to survive across reloads when the reason is `reload`

For the full capability boundaries of hot reload, cross-loop semantics, and module-side guidelines, see the next section.

## Hot-Reload Boundaries

Hot reload can replace code, rebuild registrations, and roll back failed reloads — but it is **not a process restart**.
What gets reclaimed are **runtime resources registered in the ownership system**; resources belonging to no owner,
data with user-configuration semantics, and references cached inside third-party libraries do not disappear with a reload.

### Capability Boundaries

| Object | Behavior after reload | Notes |
|------|-----------|------|
| Module code / class definitions | Supported, re-imported | Old `sys.modules` entries are cleaned up |
| `on_unload` / `on_load` | Supported, triggered in order | `on_load` is replayed on failure rollback (see previous section) |
| Commands / handlers / routes / lifecycle hooks | Supported, automatically unregistered then re-registered | Cleaned via the ownership reclaim chain |
| `spawn_background` / `spawn_later` / `spawn_thread` | Supported, cancelled per owner | Threads are only registered for observation and cannot be force-killed |
| Any `asyncio.create_task` on the main loop | Supported, automatically attributed and cancelled | Intercepted by the task factory (including tasks created inside third-party libraries) |
| Tasks spawned on the storage bridge loop | Supported, automatically attributed and cancelled | The bridge loop also has a task factory installed |
| Resources registered via `ownership.track()` | Supported, call `release()` | Loop-bound resources beyond the task factory's reach |
| `on_cleanup` hooks | Supported, triggered | Tool modules use them to discard hosted handles |
| Persistent overrides (`persist=True`) / config files | Untouched, preserved | User assets |
| Object references cached inside third-party libraries | Untouched | Invisible to the framework; modules must release them themselves |
| Event loops `new`-ed by the module itself / bare threads | Not reclaimed | See the guidelines below |
| Resources of an adapter after rollback | Not aligned | The adapter side does not yet replay `start()` |

### Three-Tier Resource Governance

1. **Transparent interception tier** — event-loop-level task factory. Any task creation inside an owner context
   is automatically attributed, covering the main loop and the storage bridge loop.
2. **Ownership-aware scheduling tier** — `spawn_background` / `spawn_later` / `spawn_thread`.
3. **Cooperative registration tier** — `ownership.track()` / `on_cleanup()`, for resources structurally
   out of reach (Loop-bound connection pools, third-party clients).

### Event Loop Boundaries

| Loop | Created by | Task factory | Purpose |
|------|--------|-----------|------|
| Main loop | `sdk.run()` / `sdk.init()` | Installed | All business code |
| Storage bridge loop | `AsyncBridge` (first synchronous storage call) | Installed | Background execution of the synchronous storage API |
| Temporary loop | `spawn_background` fallback | Not installed, closed after use | Last resort when the main loop is not ready |

**The temporary loop is a last resort**: it synchronously blocks the calling thread, and after the loop closes,
child tasks spawned inside the coroutine are lost (the log shows a `temp_loop_fallback` warning). Seeing this
warning means a module scheduled a background task at the wrong time.

**Cross-loop cancellation is best-effort**: when `cancel_owner_tasks` finds tasks on other still-running loops,
it posts cancellation via `call_soon_threadsafe` and logs a `cross_loop_task_residual` warning, but **does not
wait** for them to finish (waiting across loops is unsafe). Seeing this warning means you should check whether
an event loop was created manually.

### Module-Side Guidelines

```python
# Recommended
spawn_background(self._poll())            # Ownership-aware background task
spawn_later(30, lambda: self._cleanup())  # Ownership-aware delayed task
spawn_thread("poller", self._loop_body)   # Ownership-aware thread (entry automatically carries the owner)
ownership.track(pool)                     # Explicitly register Loop-bound resources
await sdk.storage.aget(key)               # Use the async API directly in async contexts

# Avoid
asyncio.create_task(self._poll())         # Bare call: no reference, easily GC'd
asyncio.new_event_loop()                  # Self-built loop: completely out of the ownership system's reach
threading.Thread(target=self._loop_body)  # Bare thread: entry has no owner context
self._storage.get(key)                    # Synchronous storage call in an async context: blocks the main loop
```

### Troubleshooting Checklist

1. `cross_loop_task_residual` in the logs? → Some resources live on a self-built loop
2. `temp_loop_fallback` in the logs? → A background task was scheduled before the main loop was ready
3. `attached to a different loop` error? → Check whether a loop was self-built or connection objects are reused across loops
4. `ownership.orphans()` returns output? → Some resources under an owner are still alive after unload

## Design Boundaries: Which Resources Are Not Cleaned Up on Unload

Ownership reclaims only **runtime resources registered by module code**. The following resources carry
**user-configuration semantics** (the user is in control and may have configured them deliberately) and
persist with the configuration after the module is unloaded:

| Resource | Semantics | Notes |
|------|------|------|
| `overrides.*.set(persist=True)` | Persistent override | Written to the config file, effective across restarts; not deleted on module unload (explicit user configuration) |
| Scope rules such as `scope.set_action()` | Permission control plane | Managed by the user/Dashboard; unloading a module does not reclaim the rules |
| `overrides.acl.set(persist=True)` | Command ACL | Same as above |
| Conversation `save()` persistence | Multi-turn conversation archive | Data assets are not cleaned up |

Runtime temporary writes (`persist=False`) are reclaimed with the owner — **whether or not something is persisted is
the dividing line between "user assets" and "module runtime state"**.

## Internal Implementation: How Ownership Works

**In one sentence**: the attribution chain (contextvar propagation) decides "who gets credited", while the cancellation chain (the task registry) decides "whether something can be cancelled on unload" — the two chains operate independently, and correct cleanup requires both.

The ownership system consists of **two independent chains**; understanding their division of labor is the prerequisite for debugging ownership issues:

### Attribution Chain (contextvar Propagation)

ContextVars such as `current_owner` in `runtime/context.py` handle **attribution** —
"which owner the resources registered / calls initiated by this code at this moment are credited to".
Propagation follows Python contextvars semantics:

| Execution path | Does the context propagate | Attribution result |
|---------|----------------|---------|
| Synchronous call chains / `await` chains | ✅ Propagates | Correct attribution |
| `asyncio.create_task` inside `owner_scope` | ✅ Propagates (the task copies the context at creation time) | Framework calls **inside** the task are correctly attributed |
| `run_in_executor` / bare threads | ❌ Does not propagate | Attribution lost |
| Self-built event loops | ❌ Does not propagate | Attribution lost |

> Attribution ≠ registration: context propagation only affects "who gets credited"; whether a resource can be
> cleaned up depends on whether it entered the cancellation chain described below.

### Cancellation Chain (Task Registry)

The `_owner_tasks` registry in `runtime/tasks.py` handles the **lifecycle** —
"which unfinished tasks belong to an owner, to be cancelled together on unload". Tasks enter the registry via:

1. **Explicit scheduling**: `spawn_background()` / `self.spawn()` → captures `current_owner`
   (or an explicit `owner=` argument) at creation → registered in the table;
2. **Automatic Task Factory registration** (2.8.3): `install_owner_task_factory()`
   is installed on the main event loop at framework startup — **any** task creation (including `create_task`
   inside third-party libraries) reads `current_owner` when passing through the factory, and is registered if it is not None.

The registry self-cleans: every task carries a `done_callback` and is removed from the table upon completion — no leaks.

### Cancellation Sequence (Module Unload)

```
module.unload()
  → on_unload(event)                    # Module cleans up on its own (fallback timeout protection)
  → Framework unregisters the owner's commands/events/hooks/routes
  → cancel_owner_tasks(owner)           # Fallback cancellation via the task registry
      → task.cancel() one by one        # Excluding the task currently executing the cancellation logic itself
      → await gather(pending, timeout)  # Wait for reclamation (timeout no longer blocks)
```

### Troubleshooting Approach

- **Resource not cleaned up** → Check the registry: does `get_owner_tasks("MyModule")` contain the task?
  If not, the registration path bypassed the ownership chain (import time / threads / standalone loops); locate it against the table above.
- **Attribution error** → Check the value of `get_current_owner()` at the moment of the error; for asynchronous deferred execution
  (callbacks/tasks), attribution comes from the context at creation time, not at execution time.

## Module Author Guide

### Recommended Patterns

```python
from ErisPulse import sdk
from ErisPulse.Core.Event import command
from ErisPulse.runtime import owner_scope, spawn_background

class MyModule(BaseModule):
    async def on_load(self, event):
        # Framework resources: automatically attributed, no manual cleanup needed
        self.task = self.spawn(self.polling())      # Background task
        sdk.router.register_home_entry("My Module", "/my")  # Home entry

        # Module-owned resources: wrap them in owner_scope to bring them into the ownership system
        with owner_scope("MyModule"):
            self.client.on_event(self._handle)      # Hypothetical custom registration

    async def on_unload(self, event):
        # Framework resources have been reclaimed automatically; only clean up module-owned resources not covered by owner_scope
        await self.client.close()
```

### Caveats

- **Registrations at import time have no owner**: hooks/handlers registered at module top level (at import time)
  happen before `owner_scope` and are treated as framework-level resources (owner=None), thus **not cleaned up**.
  Always register inside `on_load()`.
- **i18n registration with a custom domain**: if the domain of `i18n.register(domain=...)` is not equal to the
  module name, it will not be reclaimed automatically; keep domain=module name.
- **Use `self.spawn()` for background tasks**: since 2.8.3, bare `asyncio.create_task` is also **automatically and
  implicitly attributed** (Task Factory automatic registration, fallback cancellation on unload); but `self.spawn()`
  remains the recommended pattern — it supports scheduling from non-main-loop threads back to the main loop,
  explicit `owner=` specification, and GC protection for fire-and-forget tasks.
  In versions **before 2.8.3**, bare tasks are not attributed; `self.spawn()` is mandatory.
- The cleanup chain "warns only on failure": an exception in one cleanup step does not block reclamation of the
  remaining resources; it is visible at DEBUG/WARNING log level, and TRACE can be enabled for troubleshooting.

### Registration Timing → Attribution Results Table

| Registration scenario | Attribution result | Notes |
|---------|---------|------|
| Registration inside `on_load()` via framework APIs (command/event/lifecycle/route decorators) | Attributed to the module | Automatically unregistered on unload |
| Registration at module top level (import time) | **No owner** (owner=None) | Not cleaned up; do not use |
| Background tasks created via `self.spawn()` | Attributed to the module | Automatically cancelled on unload |
| Registration via third-party APIs inside `owner_scope("Name")` | Attributed to the module | Requires the third-party callback to run synchronously within the scope |
| Bare `asyncio.create_task` (including `loop.create_task` / `ensure_future`) | **Automatic attribution** (Task Factory, 2.8.3+) | Reads `current_owner` at the instant of creation; automatically registered within an owner context and cancelled as a fallback on unload; see [Internal Implementation](#internal-implementation-how-ownership-works) below |
| Tasks created inside third-party library async callbacks (aiohttp / APScheduler etc.) | **Automatic attribution** (Task Factory, 2.8.3+) | If `current_owner` is already injected when the callback runs (e.g. during framework handler execution), the task is automatically registered |
| `run_in_executor` (thread pool) | **No owner** (not an asyncio.Task) | Threads are outside the task factory's jurisdiction; manage their lifecycle yourself |
| Registration in a standalone event loop (self-built loop) | **No owner** | The Task Factory is installed only on the main loop; contextvars also do not propagate across event loops |

> Principle: **ownership follows the `current_owner` context at the moment of registration**; any async deferral,
> thread pool, or standalone loop leaves that context — when attribution is needed, explicitly enter `owner_scope`.

## Tool Module Guide: Hosting Handles of Other Modules

**Scenario**: "tool modules" such as cron schedulers, registries, and connection pools hold things on behalf of
other modules — when they call `sdk.Cron.on_trigger(handler)` in their `on_load`, a callback pointing to their
instance is stored in your container. The framework automatically cleans up all framework resources the other
module registered, but it cannot clean up **references inside your private container**: after the other module
unloads, your container still holds its instance, so that instance can no longer be reclaimed by the GC
(a memory leak — the `purge` leak diagnostics report it as "unreclaimable").

**Solution**: call `on_cleanup()` in the same function where you register the other module's items,
and the framework will automatically call your cleanup function when the other module is unloaded / disabled:

```python
from ErisPulse.Core.Bases import BaseModule
from ErisPulse.runtime import off_cleanup, on_cleanup

class CronModule(BaseModule):
    def __init__(self):
        self._entries = {}  # {module name: list of callbacks hosted for that module}

    def on_trigger(self, handler):
        # Automatically identifies the calling module's name (correct for both direct calls in on_load and module.call);
        # the return value is the resolved owner, which can be used directly as the attribution key
        owner = on_cleanup(self._drop)
        self._entries.setdefault(owner, []).append(handler)

    def _drop(self, owner: str):
        """Called automatically by the framework when the other module is unloaded/disabled: just discard its handles"""
        self._entries.pop(owner, None)

    async def on_unload(self, event):
        off_cleanup(self._drop)  # ③ Unregister the hook before unloading yourself, to avoid the hook table holding self
```

Guaranteed framework behavior:

| Concern | Behavior |
|--------|------|
| Trigger timing | The other module's unload / disable, or adapter shutdown — all triggered within the framework cleanup chain, earlier than the purge leak diagnostics |
| Caller identification | Direct calls use `current_owner`; calls made via `module.call()` use the caller (`current_caller`); you can also specify it explicitly via `on_cleanup(cb, owner="module name")`. **Strict validation**: raises `ValueError` when the owner cannot be resolved (all three sources missing) — private tool modules should register hooks within their own loading context |
| Callback signature | `cb(owner: str)`, sync / async both supported; async callbacks come with timeout protection (`CLEANUP_CALLBACK_TIMEOUT_SECS`, default 10 seconds) |
| Fault tolerance | An exception / timeout in a single callback is only logged and does not affect the remaining hooks or the cleanup chain |
| Duplicate registration | Identical `(owner, callback)` pairs are idempotently deduplicated |

**When it is not needed**: if what the other module registered are framework resources (commands, event handlers,
routes, background tasks...), the framework already cleans them up fully automatically (see
[Inventory of Owned Resources](#inventory-of-owned-resources) above). Only handles of the other module held in
your private container need `on_cleanup`.
For the quick-reference version from the module development perspective, see
[Best Practices · Tool Modules](../developer-guide/modules/best-practices.md#tool-modules-catch-unload-notifications-when-holding-others-stuff).

## Related Documentation

Choose based on your next step:

- **To control "whether a resource takes effect" (the permission plane)** → [Scope (scope)](scope.md) — ownership governs "who a resource belongs to and whose unload reclaims it", while scope governs "when a resource takes effect"
- **Fallback cancellation of background tasks / timers** → [Lifecycle Management · Background Task Ownership and Auto-Cancellation](lifecycle.md#background-task-ownership-and-auto-cancellation)
- **Canary releases isolated under a separate owner** → [Shadow Modules and Graduation](shadow.md)
- **Quick reference and recommended patterns from the module development perspective** → [Module Best Practices](../developer-guide/modules/best-practices.md)