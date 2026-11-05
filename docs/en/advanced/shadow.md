# Shadow Modules and Gradual Promotion

> [!TIP]
> **When to read this**: When you need gradual release—running a new version in parallel, comparing behaviors, and promoting or rolling back. Skip if not needed; it won't affect other features.

> **After reading, you will know**: The five isolation gates of shadow modules, alignment methods for behavior diff, the `promote` promotion and rollback flow when promotion fails, and the honest boundaries that the framework cannot block.
>
> **This section does not cover**: The general hot reload and ownership cleanup mechanism for ordinary modules (see [Ownership (owner) System](ownership.md)).

A shadow module is a **new version** of the same module, running in parallel with the live version under an independent owner (e.g., `roll_shadow`). It receives **copies** of real events, and its outbound messages are **intercepted and recorded** rather than actually sent. By comparing behaviors in `shadow_diff`, you can confirm the new version is harmless before promoting it with one click via `promote`, or discarding it at any time with `dismiss`. **No code changes are required**; the entire process is driven by runtime APIs: similar to `load / unload / reload`, these operations can be directly invoked by the Dashboard or custom management modules, with no configuration needed.

{!--< tips >!--}
1. Start: ``await sdk.module.shadow_start("roll", source="path/to/v2")``
   ——The new version runs in parallel with the old version under an independent owner (default is the path name).
2. The shadow does not participate in real distribution or dependency graphs: commands with the same name go into the shadow directory, routes are registered but not mounted, lifecycle broadcasts are silent, and `module.call` and dependency resolution still point to v1.
3. Promotion is always confirmed by a human: ``await sdk.module.promote_shadow("roll")``; if it fails, the old instance automatically rolls back and continues serving; ``dismiss_shadow`` discards the shadow at any time.
{!--< /tips >!--}

## Quick Start

```python
# v2 code: Standard module format, shadow-agnostic (any directory, e.g. downloads/roll_v2/)
```

```python
# In production bot (Dashboard / Management module call), start shadow with one line:
await sdk.module.shadow_start("roll", source="downloads/roll_v2")
# → Shadow runs independently as owner "roll_v2", coexisting with v1, with outbound traffic intercepted and tracked

# During trial period, compare behaviors:
report = sdk.module.shadow_diff("roll")
# {"shadow_owner": "roll_v2", "count": 3, "aligned": [...]}
```

- **v1 actual send**: Bot timeline from inbox (transcript)
- **v2 intended send**: Shadow ledger ("what was intended to be sent" recorded in outbound gate)
- Both aligned by `trace_id` — for the same message, both versions' triggers/missed triggers and intended vs. actual sends are clearly visible

After confirming correctness, promote:

```python
await sdk.module.promote_shadow("roll")   # Promote, rollback to v1 on failure
await sdk.module.dismiss_shadow("roll")   # Or: discard shadow
```

## Five Isolation Gates

| Gate | Mechanism |
|------|-----------|
| Event Copy | The shadow handler receives an **independent copy** of the event (marked with `shadow`) — modifications, claims, or stopping propagation by the shadow only affect the copy, not the original event chain |
| Outbound Gate | All `Send` DSL and `Api` calls from the shadow are intercepted and recorded (with a fake success response), without actually being sent — the shadow will not send duplicate replies |
| Storage Overlay | KV writes from the shadow go into an in-memory overlay and are discarded from the persistent store; reads first check the overlay, and if not found, transparently read from the real store (gray-scale runs against real data); deletes are recorded as tombstones |
| Routing Shield | HTTP/WS/SSE routes from the shadow are only registered but not mounted; commands with the same name are registered in the shadow command directory, and platform event method injection is prohibited |
| Lifecycle Silence | The shadow does not broadcast its own lifecycle events, nor does it participate in the ecosystem dependency graph (`module.call` and dependency resolution still point to v1, preventing half-finished components from being depended upon) |

Configuration Inheritance: The shadow **inherits the configuration section from the original module by default** (otherwise gray-scale would be distorted), and the configuration takes effect in place after promotion.

## Honest Boundaries (Can't Be Blocked)

- The framework can intercept all sending / API / KV storage / unified HTTP client operations;
  However, modules bypassing the framework by directly starting `aiohttp`, spawning threads, or writing to external systems cannot be intercepted by the framework.
- **ORM read/write operations are not within the coverage semantics** (clean implementation at the SQL layer is not possible with line-by-line overlay) — during shadow periods, it is recommended to avoid relying on ORM for isolation.
- **Shadow source is a local path**: New code is imported via path and loaded by an independent owner; the same PyPI package cannot exist in both old and new versions within the same interpreter due to the `sys.modules` single-key limitation.
- The leak auditor (`sdk.module.audit`) can see the ownership of shadow resources; side effects bypassing the framework will at least not go unnoticed.

## Promote and Rollback

The `promote` process: take a snapshot of the current version (including cascading dependents) → completely uninstall → register the shadow instance with the real name and load it. If any step fails, automatic rollback occurs and the old instance continues to serve (best-effort semantics: side effects executed by `on_unload` cannot be undone, and the old instance is in a cleaned-up state after rollback). Promoted shadow resources are reclaimed and bindings are released; the original module configuration section takes effect in place.

**Persistence Reminder**: `promote` is a runtime switch—after a restart, v2 will still be used. You need to **persistently install** the new version (`pip install -U` the new version / replace the plugin file). The runtime switch will not automatically handle package management for you.

## Related Documentation

- [Ownership (owner) System](ownership.md) —— The foundation of the shadow's isolation mechanism as an independent owner
- [Interaction Session](interaction.md) —— `trace_id` and inbox (diff-aligned data source)
- [Scope](scope.md) —— Control plane for event admission and outbound