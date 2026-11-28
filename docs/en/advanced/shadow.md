# Shadow Modules and Gray-Scale Promotion

> [!TIP]
> **When to read this**: when you need a gray-scale release — trial-running a new version in parallel, comparing behavior, and promoting or rolling back. Skip it otherwise; it does not affect the use of other features.

> **After reading you will know**: the five isolation gates of shadow modules, how behavior diffs are aligned,
> the `promote` and failure-rollback flow, and the honest boundaries the framework cannot intercept.
>
> **Not covered here**: the general mechanisms of hot reload and ownership cleanup for ordinary modules
> (see [Ownership (owner) System](ownership.md)).


A shadow = the **new version** of the same module, trial-running side by side with the live old version under a separate owner (e.g. `roll_shadow`): it receives **copies** of real events, and its outbound traffic is **intercepted and recorded** rather than actually sent — compare the two versions' behavior in `shadow_diff`, and once confirmed harmless, `promote` promotes it with one call; `dismiss` abandons it at any time. **Zero changes to module code, driven entirely by runtime APIs**: an ops action of the same family as `load / unload / reload`, invoked directly by the Dashboard / custom management modules, with no configuration items to write.

{!--< tips >!--}
1. Start: ``await sdk.module.shadow_start("roll", source="path/to/v2")``
   — the new version's code coexists with the old under a separate owner (defaults to the path name)
2. Shadows do not participate in real dispatch or the dependency graph: same-named commands go into the shadow command catalog, routes are registered but not mounted,
   lifecycle broadcasts are silenced, and `module.call` / dependency resolution still point to v1
3. Promotion is always confirmed by a human: ``await sdk.module.promote_shadow("roll")``; on failure it automatically rolls back and the old instance keeps serving; ``dismiss_shadow`` abandons it at any time
{!--< /tips >!--}

## Quick Start

```python
# v2 code: ordinary module style, zero shadow awareness (any directory, e.g. downloads/roll_v2/)
```

```python
# In the live bot (called from the Dashboard / a management module), one line starts the gray-scale run:
await sdk.module.shadow_start("roll", source="downloads/roll_v2")
# → the shadow coexists with v1 under the separate owner "roll_v2"; its outbound is intercepted and recorded

# Compare behavior during the trial run:
report = sdk.module.shadow_diff("roll")
# {"shadow_owner": "roll_v2", "count": 3, "aligned": [...]}
```

- **What v1 actually sent**: the bot timeline from the inbox (transcript)
- **What v2 intended to send**: the shadow ledger (what the outbound gate recorded as "wanted to send")
- The two are aligned by `trace_id` — for the same message, at a glance you can see why each version triggered or didn't, and what it wanted to send vs. what it actually sent

Once confirmed correct, promote:

```python
await sdk.module.promote_shadow("roll")   # promote; on failure, auto-rollback to v1
await sdk.module.dismiss_shadow("roll")   # or: dismiss the shadow
```

## Five Isolation Gates

| Gate | Mechanism |
|----|------|
| Event copy | The shadow handler receives an **independent copy** of the event (with a `shadow` marker) — the shadow's rewriting / claiming / stopping propagation only affects the copy and does not touch the original event chain |
| Outbound gate | The shadow's `Send` DSL and `Api` calls are all intercepted and recorded (with fake responses shaped as success), never actually sent — the shadow will not send duplicate replies |
| Storage overlay | The shadow's KV writes go into an in-memory overlay and are discarded before persisting; reads check the overlay first and pass through to the real database on miss (the gray-scale runs against real data); deletes record tombstones |
| Route blocking | The shadow's HTTP/WS/SSE routes are registered but not mounted; same-named commands go into the shadow command catalog, and platform event method injection is forbidden |
| Lifecycle silence | The shadow does not broadcast its own lifecycle events and does not join the ecosystem dependency graph (`module.call` and dependency resolution still point to v1, preventing half-finished work from being depended on) |

Configuration inheritance: the shadow by default **inherits the original module's configuration section** (otherwise the gray-scale run would be distorted); after promotion, the configuration takes effect in place.

## Honest Boundaries (What Cannot Be Intercepted)

- Sends / APIs / KV storage / the unified HTTP client going through the framework are **all interceptable**;
  a module bypassing the framework to spin up raw `aiohttp` or open threads to write to external systems — the framework cannot intercept that
- **ORM reads/writes are not within the overlay semantics** (a per-row overlay cannot be cleanly implemented at the SQL layer) —
  during the shadow period, avoid relying on ORM write isolation
- **The shadow source is a local path**: the new version's code is imported by path and loaded under a separate owner; the same PyPI package
  within the same interpreter is limited by the single key of `sys.modules` and cannot have the old and new versions coexist
- The leak auditor (`sdk.module.audit`) can see shadow resource ownership; side effects that bypass the framework
  will at least not be silent

## Promotion and Rollback

The `promote` flow: snapshot the current version (including cascading dependents) → fully unload → register and load the shadow under its real name → any step failing automatically rolls back and the old instance keeps serving (best-effort semantics: side effects already executed by `on_unload` are irrevocable; after rollback the old instance is in a finalized state). After a successful promotion, shadow resources are reclaimed and bindings released; the original module's configuration section takes effect in place.

**Persistence reminder**: promote is a runtime switch — to still run v2 after a restart, you need to **persistently install** the new version (`pip install -U` the new version / replace the plugin files). The runtime switch does not do package management for you. The Dashboard's "Promote and Persist" automates this step: after a successful promotion it pip-installs in the background the original whl saved to disk at upload time; an ordinary `promote` does not write to disk.

## Three Hard Boundaries

| Boundary | Description |
|------|------|
| pip exclusivity | During the shadow period it **only unpacks, never installs**: the original whl is saved to `shadows/<module>/` solely for persistence after promotion; no pip install occurs while the shadow runs, avoiding overwriting installed packages and drifting live behavior |
| promote does not persist to disk | `promote_shadow` only performs a runtime switch and does not touch the package manager; after a restart it reverts to v1 (the configuration still points to the old version). When v2 must survive a restart, use "Promote and Persist" or a manual `pip install` |
| Third-party dependencies = versions already installed in the process | Third-party libraries imported by the shadow use the **versions already installed in the current process**; new dependencies declared by the whl are not installed automatically, and the shadow fails to load when a dependency is missing (the error is raised as-is) |

> whl ingestion, `list_shadows`, and "Promote and Persist" (`shadow_ingest_whl` /
> `shadow_promote_persist` / `shadow_persist_status`) require ErisPulse **2.12+**;
> older SDKs automatically degrade to the basic shadow (unpack-and-start only, no persistence), and Dashboard capability detection switches automatically.

Ops query surface: `sdk.module.list_shadows()` returns all current bindings
`{original module name: shadow owner name}`, for the Dashboard / scripts to aggregate and display.

The implementation of whl ingestion and "Promote and Persist" belongs to the SDK: unpacking / disk persistence / pip orchestration evolve with SDK versions, and the Dashboard is merely the calling entry point.

## Related Documentation

- [Ownership (owner) System](ownership.md) — the mechanism foundation for isolating shadows under separate owners
- [Interaction Sessions](interaction.md) — `trace_id` and the inbox/transcript (the data source for diff alignment)
- [Scope](scope.md) — the control plane for event admission and outbound