---
name: erispulse-shadow-transcript
description: "适用于：新旧版本灰度对照（shadow）、消息收件箱与行为追踪（transcript）。覆盖场景：When you need gradual release—running a new version in parallel, comparing behaviors, and promoting or rolling back. Skip if not needed; it won't affect other features.。When you need message history, conversation recovery, or want to adjust the retention policy for the inbox. If not needed, you can skip this section without affecting other features.。"
---

# ErisPulse 影子灰度与消息追踪

This skill is auto-built from the ErisPulse documentation.
Repository: https://github.com/ErisPulse/ErisPulse
Source paths are annotated per section; see docs/ in the repository for the latest content.

## 影子模块

> 来源: `docs/en/advanced/shadow.md`（https://github.com/ErisPulse/ErisPulse/blob/main/docs/en/advanced/shadow.md）

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

## 消息追踪

> 来源: `docs/en/advanced/transcript.md`（https://github.com/ErisPulse/ErisPulse/blob/main/docs/en/advanced/transcript.md）

# Transcript (Conversation Inbox)

> [!TIP]
> **When to read this**: When you need message history, conversation recovery, or want to adjust the retention policy for the inbox. If not needed, you can skip this section without affecting other features.

The conversation inbox automatically records messages sent and received by the bot (organized by the session key `platform:detail_type:target_id`), providing historical data for conversation recovery (`event.history`), shadow module diff, cold-start replay, and more. This document explains its **storage model**, what each retention policy knob protects, and the real cost of runtime override APIs and relaxed restrictions.

> Before changing any limits, please read the "Risks and Auditing" section first—each knob exists for a specific reason.

## How It Works

```
Message ──append()──▶ Write buffer (in-memory deque, hard cap of 4096 lines)
                        │  Flushed to storage in batches every 1 second (≤64 lines per batch, single transaction)
                        ▼
              transcript table of the storage backend (sqlite by default)
                        │  Retention cleanup lazily triggered once every ~32 appends
                        ▼
              ┌─ Per-session FIFO trimming (max_per_session, default 50 entries)
              └─ Global TTL deletion (ttl_hours, default 168 = 7 days)
```

Three layers of protection, each guarding against a different risk:

| Knob | Default | What it protects | Effect of disabling (=0) |
|------|--------|----------|------------------|
| Write buffer cap | 4096 lines (constant, not configurable) | **Memory**: backlog accumulated during storage outages won't blow up RAM | Cannot be disabled—this is the memory defense line |
| Per-entry text truncation | 2000 characters (constant, not configurable) | Memory/disk footprint of a single message | Cannot be disabled |
| `max_per_session` | 50 entries/session | **Disk growth**: unbounded accumulation of a single session's history | That session's history grows without limit |
| `ttl_hours` | 168 (7 days) | **Disk growth**: long-term accumulation across all sessions | The `transcript` table grows without limit |

Key insight: **the write buffer has a hard cap, so loosening the retention policies won't directly blow up memory**;
the real risk lies in the storage layer and downstream consumers (see next section).

> [!TIP]
> **Applications that don't need session memory can disable the feature entirely**: setting `ErisPulse.transcript.enabled = false`
> stops automatic recording of inbound/outbound messages—nothing is written to the memory buffer or storage, saving resident memory
> and continuous storage-layer IO. The session inbox mainly serves two purposes: AI context injection and anti-repetition; deployments
> that need neither (e.g., purely command-driven bots) are advised to disable it.

## Configuration

```toml
[ErisPulse.transcript]
enabled = true          # Whether to auto-record
max_per_session = 50    # Number of entries retained per session (0 = disable session trimming)
ttl_hours = 168.0       # Global retention duration (in hours, 0 = never clean up)
self_echo = "bot"       # Inbound bot echo handling: bot / skip / user
```

Environment variable overrides work as well: `ERISPULSE_TRANSCRIPT_MAX_PER_SESSION`, `ERISPULSE_TRANSCRIPT_TTL_HOURS`,
`ERISPULSE_TRANSCRIPT_SELF_ECHO`.
Configuration changes take effect hot (within the write buffer flush cadence, with a maximum delay of ~1 second).

> [!TIP]
> **Disable it if you don't need conversation memory**: The only consumers of the inbox are conversation restore / shadow diff / cold-start replay.
> If your bot (or deployed modules) don't use these capabilities at all, setting `enabled = false`
> will eliminate the inbox's memory buffer and background batch flush IO—message sending/receiving and command handling are completely unaffected.

## Message Attribution (sender and meta)

Every record from all query interfaces (`get` / `recent` / `get_by_trace` / `event.history`) uniformly carries attribution fields, used to distinguish "who said it / which module sent it":

| Field | Meaning |
|------|------|
| `sender` | Sender identifier: `user_id` for inbound; bot account / `self.user_id` at echo time for outbound |
| `meta` | Metadata at the moment of recording (whitelist contract, not the full raw event) |

The `meta` whitelist:

- **Inbound**: `nickname` (the nickname at the time of the event; a later lookup yields the "current nickname"),
  `self_id` (bot account), `sub_type`, `message_id`; echo messages additionally carry `self_echo: true`;
- **Outbound**: sending context (`platform` / `method` / `detail_type` / `target_id` /
  `bot_id` / `trace_id` / `preview`) and `module` (the module to which the send is attributed, see below).

For records from older versions (from the era without a meta column), `meta` is `{}`, so callers using `meta.get("nickname", "")` degrade gracefully; when the storage backend does not support ALTER, it likewise silently falls back to `{}`.

### Outbound Attribution (meta.module)

Multiple modules on the same instance may send messages (chat, admin, scheduled reminders). The `meta.module` of an outbound record identifies the sending attribution, with a value priority of `current_owner > current_caller > ""`:

| Sending scenario | module value |
|----------|-----------|
| During module code invoked via `module.call` | Target module name |
| Sending within a module's event handler | Name of the module that registered the handler (automatically injected during dispatch) |
| The framework itself / no module context | `""` |

The `message.sent` / `message.sending` hook payloads (send_ctx) likewise carry the `module` field.

### Inbound Bot Echo (self_echo)

Some platforms/protocol implementations report messages sent by the bot itself back as message events (e.g., OneBot v11's `report-self-message`, Telegram outgoing messages). Before recording inbound messages, the framework identifies echoes by `self.user_id == user_id` and handles them according to the `self_echo` configuration:

| Value | Behavior |
|------|------|
| `"bot"` (default) | Still recorded, but with `role="bot"`, `sender=self_id`, `meta.self_echo=true` |
| `"skip"` | Not recorded (when the adapter also triggers `message.sent`, an outbound record naturally exists) |
| `"user"` | Recorded with `role="user"` (legacy behavior, compatibility escape hatch) |

On platforms that do not echo back (`self.user_id != user_id` always holds), the behavior is exactly the same as having this feature disabled.

### Session-Filtered recent

```python
from ErisPulse import transcript

# Global time window across sessions (cold-start replay semantics, default)
transcript.recent(3600)

# Restrict to a single session: server-side filtering, avoiding the client
# comparing session_key item by item after a global fetch
transcript.recent(3600, session_key="onebot11:group:123")
```

`session_key=None` keeps the cross-session semantics; an empty string `""` is equivalent to no filtering (fault-tolerant).

## Runtime Override API

When you need to dynamically adjust settings at runtime (for example, to temporarily extend retention for a specific scenario):

```python
from ErisPulse import transcript

# Override (takes precedence over configuration; only in-memory, values revert to configuration after restart)
transcript.set_retention(max_per_session=500, ttl_hours=24 * 30)

# Query effective values and their source
transcript.get_retention()
# {'max_per_session': 500, 'ttl_hours': 720.0, 'overridden': ['max_per_session', 'ttl_hours']}

# Restore configuration-based values
transcript.reset_retention()
```

- Passing `0` disables the corresponding strategy (will log a warning for traceability); negative numbers raise `ValueError`;
- The override takes effect during the next retention cleanup (lazy, with a maximum delay of ~32 append operations);
- The `transcript` singleton can be imported from the root package or via `sdk.transcript`.

## Risks and Audits: Read Before Relaxing Limits

After disabling `max_per_session` / `ttl_hours` (or significantly increasing them), the `transcript` table will grow **unlimited** with message volume. The consequences are as follows:

1. **Disk full** — sqlite single-file continues to expand, making the storage layer unavailable once disk space is exhausted;
2. **Query degradation** — scanning costs for `get()` / `recent()` / `get_by_trace()` increase as the table grows;
3. **Downstream memory pressure (the real source of OOM)** — consumers that load entire historical segments into memory (such as restoring conversation with history, full panel retrieval, or your business code `get(session, n)` requesting large n) will consume more memory as the table grows, potentially triggering OOM kill in extreme cases.

**Before relaxing the limits, ask yourself three questions**: How long of history do you need? How large should it be? Who will clean it up? If the answer depends on "never deleting," the correct approach is usually external archiving (regularly moving old data to a dedicated database), rather than letting the inbox retain unlimited history.

Auditing methods (regularly check table size):

```python
# Query row count and size via ORM/SQL builder (example for sqlite)
from ErisPulse import storage

row = storage.Table("transcript").raw_sql("SELECT COUNT(*) AS n FROM transcript")
```

```sql
-- Direct query on sqlite file (table size)
SELECT COUNT(*) FROM transcript;
```

A warning log stating "Retention policy has been disabled" means someone disabled the policy with 0; please confirm if this was your operation.

## Boundaries with Other Mechanisms

- **Interactive session timer / wait_reply**: See [Interactive Session System](interaction.md), which is unrelated to the inbox;
- **History back for conversation recovery**: `resume(with_history=N)` retrieves the most recent N messages from the inbox—after the inbox is trimmed, the amount of history that can be recovered decreases (increasing `max_per_session` extends the recoverable window);
- **Shadow module diff**: Relies on the `get_by_trace` query chain; an inbox with a short TTL shortens the diff window.
