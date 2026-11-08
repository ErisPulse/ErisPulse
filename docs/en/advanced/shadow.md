# Shadow Modules and Canary Promotion

> [!TIP]
> **When to read this**: When you need a canary release — running a new version in parallel as a trial, comparing behavior, and promoting or rolling back. Skip it otherwise; it does not affect the use of other features.

> **What you'll learn**: The five isolation gates of shadow modules, how behavior diffs are aligned,
> the `promote` promotion and failure rollback flow, and the honest boundaries the framework cannot enforce.
>
> **Not covered here**: The general mechanisms of hot reload and ownership cleanup for regular modules
> (see [Ownership (owner) System](ownership.md)).


A shadow = the **new version** of the same module, coexisting with the live old version under an independent owner (e.g., `roll_shadow`) during a trial run: it receives **copies** of real events, and its outbound traffic is **intercepted and recorded** rather than actually sent — the behavior of the two versions is compared in `shadow_diff`; once confirmed harmless, `promote` promotes it with one click, and `dismiss` discards it at any time. **Zero changes to module code, driven entirely by runtime APIs**: an operational action of the same kind as `load / unload / reload`, called directly by the Dashboard / custom admin modules, with no configuration items to write.

{!--< tips >!--}
1. Start: ``await sdk.module.shadow_start("roll", source="path/to/v2")``
   — the new version's code coexists with the old under an independent owner (defaults to the path name)
2. The shadow does not participate in real dispatch or the dependency graph: same-named commands go into the shadow command catalog, routes are registered but not mounted, lifecycle broadcasts are silenced, and `module.call` and dependency resolution still point to v1
3. Promotion is always confirmed by a human: ``await sdk.module.promote_shadow("roll")``; on failure it rolls back automatically and the old instance keeps serving; ``dismiss_shadow`` discards the shadow at any time
{!--< /tips >!--}

## Quick Start

```python
# v2 code: written as a normal module, zero shadow awareness (any directory, e.g. downloads/roll_v2/)
```

```python
# In the live bot (invoked via the Dashboard / admin module), one line starts the canary:
await sdk.module.shadow_start("roll", source="downloads/roll_v2")
# → The shadow coexists with v1 under the independent owner "roll_v2"; outbound traffic is intercepted and recorded

# Compare behavior during the trial run:
report = sdk.module.shadow_diff("roll")
# {"shadow_owner": "roll_v2", "count": 3, "aligned": [...]}
```

- **v1 actually sent**: the bot timeline from the inbox (transcript)
- **v2 intended to send**: the shadow ledger (what the outbound gate recorded it "wanted to send")
- The two are aligned by `trace_id` — for the same message, why each version triggered or didn't, what it intended to send versus what it actually sent, all at a glance

Once verified, promote:

```python
await sdk.module.promote_shadow("roll")   # Promote; on failure, automatically roll back to v1
await sdk.module.dismiss_shadow("roll")   # Or: discard the shadow
```

## Five Isolation Gates

| Gate | Mechanism |
|----|------|
| Event copy | The shadow handler receives an **independent copy** of the event (tagged with `shadow`) — the shadow's rewrites / claims / stop-propagation only affect the copy, not the original event chain |
| Outbound gate | The shadow's `Send` DSL and `Api` calls are all intercepted and recorded (with success-shaped fake responses), never actually sent — the shadow cannot send duplicate replies |
| Storage overlay | The shadow's KV writes go into an in-memory overlay and are discarded instead of persisted; reads check the overlay first and fall through to the real store on a miss (the canary runs against real data); deletes are recorded as tombstones |
| Route blocking | The shadow's HTTP/WS/SSE routes are registered but not mounted; same-named commands go into the shadow command catalog, and platform event method injection is forbidden |
| Lifecycle silence | The shadow does not broadcast its own lifecycle events and does not participate in the ecosystem dependency graph (`module.call` and dependency resolution still point to v1, preventing half-finished code from being depended upon) |

Config inheritance: by default the shadow **inherits the original module's config section** (otherwise the canary would distort reality); after promotion, the config takes effect in place.

## Honest Boundaries (What Cannot Be Intercepted)

- Sends / API / KV storage / the unified HTTP client that go through the framework **can all be intercepted**; a module bypassing the framework to start a raw `aiohttp` client or spin up threads to write to external systems — the framework cannot intercept those
- **ORM reads/writes are not covered by the overlay semantics** (a per-row overlay cannot be cleanly implemented at the SQL layer) — during the shadow period, avoid relying on ORM write isolation
- **The shadow source is a local path**: the new version's code is imported by path and loaded under an independent owner; within the same interpreter, the same PyPI package is limited by `sys.modules`'s single-key constraint and cannot have old and new versions coexist
- The leak auditor (`sdk.module.audit`) can see shadow resource ownership; side effects that bypass the framework are at least not silent

## Promotion and Rollback

The `promote` flow: snapshot the current version (including cascading dependents) → fully unload → register and load the shadow under its real name → if any step fails, roll back automatically and the old instance keeps serving (best-effort semantics: side effects already executed by `on_unload` cannot be undone; after rollback the old instance is in a finalized state). On a successful promotion, shadow resources are reclaimed and bindings released; the original module's config section takes effect in place.

**Persistence reminder**: promote is a runtime switch — to keep running v2 after a restart, you need to **persistently install** the new version (`pip install -U` the new version / replace the plugin files). The runtime switch does not do package management for you. The Dashboard's "Promote and Persist" automates this step: after a successful promotion, it pip-installs in the background the whl original written to disk at upload time; ordinary `promote` does not write to disk.

## Three Hard Boundaries

| Boundary | Description |
|------|------|
| pip exclusivity | During the shadow period it **only unpacks, never installs**: the whl original is written to `shadows/<module>/`, solely for persistence after promotion; no pip install happens while the shadow runs, avoiding overwriting installed packages and drifting live behavior |
| promote does not persist | `promote_shadow` only performs a runtime switch and does not touch the package manager; after a restart it falls back to v1 (the config still points to the old version). To keep v2 across restarts, use "Promote and Persist" or a manual `pip install` |
| Third-party dependencies = process-installed versions | Third-party libraries imported by the shadow use **the versions already installed in the current process**; new dependencies declared by the whl are not installed automatically, and if dependencies are missing the shadow fails to load (the error is raised as-is) |

Operations query surface: `sdk.module.list_shadows()` returns all current bindings `{original module name: shadow owner name}` for the Dashboard / scripts to aggregate and display.

The implementation of whl ingestion and "Promote and Persist" belongs to the SDK (`shadow_ingest_whl` / `shadow_promote_persist` / `shadow_persist_status`): unpacking / disk persistence / pip orchestration evolves with SDK versions, and the Dashboard is merely the call entry point. For older SDKs the Dashboard retains a local fallback path (unpack-and-start only, no persistence), switching automatically via capability detection.

## Related Documents

- [Ownership (owner) System](ownership.md) — the mechanism underlying the shadow's isolation under an independent owner
- [Interaction Sessions](interaction.md) — `trace_id` and the inbox (the data source for diff alignment)
- [Scope (scope)](scope.md) — event admission and the outbound control plane