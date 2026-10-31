---
name: erispulse-shadow-transcript
description: "适用于：新旧版本灰度对照（shadow）、消息收件箱与行为追踪（transcript）。覆盖场景：When you need gradual release—running a new version in parallel, comparing behaviors, and promoting or rolling back. Skip if not needed; it won't affect other features.。When you need message history, conversation resume, or to adjust inbox retention policies. Skip it otherwise; it won't affect the use of other features.。"
---

# ErisPulse 影子灰度与消息追踪

This skill is auto-built from the ErisPulse documentation.
Repository: https://github.com/ErisPulse/ErisPulse
Source paths are annotated per section; see docs/ in the repository for the latest content.

## 内容大纲

AI 按需读取：只读需要的章节即可，不必全文加载。

- 影子模块: 29-49 行
- Quick Start: 51-76 行
- Five Isolation Gates: 78-88 行
- Honest Boundaries (Can't Be Blocked): 90-96 行
- Promote and Rollback: 98-102 行
- 消息追踪: 104-118 行
- How It Works: 120-151 行
- Configuration: 153-172 行
- Message Attribution (sender and meta): 174-236 行
- Runtime Override API: 238-258 行
- Risks and Auditing: Must-Read Before Lifting Limits: 260-289 行
- Boundaries with Other Mechanisms: 291-297 行

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

# Session Inbox (Transcript)

> [!TIP]
> **When to read this**: When you need message history, conversation resume, or to adjust inbox retention policies. Skip it otherwise; it won't affect the use of other features.


The session inbox automatically records messages sent and received by the bot (organized by conversation key `platform:detail_type:target_id`),
providing historical data for conversation resume (`event.history`), shadow module diffs, cold-start replay, and more.
This document explains its **storage model and what each retention-policy knob protects**, as well as the runtime override API and the real cost of lifting limits.

> Before changing any limits, read through the "Risks and Auditing" section first — every knob exists for a reason.

## How It Works

```
Message ──append()──▶ Write buffer (in-memory deque, hard cap of 4096 rows)
                        │  Batched flush to disk every 1 second (≤64 rows per batch, single transaction)
                        ▼
              transcript table in the storage backend (sqlite by default)
                        │  Lazy retention cleanup triggered every ~32 appends
                        ▼
              ┌─ Per-session FIFO trimming (max_per_session, default 50 entries)
              └─ Global TTL deletion (ttl_hours, default 168 = 7 days)
```

Three layers of protection, each guarding against a different risk:

| Knob | Default | What It Protects | Consequence of Disabling (=0) |
|------|--------|----------|------------------|
| Write buffer cap | 4096 rows (constant, not configurable) | **Memory**: backlog accumulated while storage is unavailable won't blow up RAM | Cannot be disabled — this is the memory defense line |
| Per-message text truncation | 2000 characters (constant, not configurable) | Memory/disk footprint of a single message | Cannot be disabled |
| `max_per_session` | 50 per session | **Disk growth**: unbounded accumulation of a single session's history | That session's history grows without bound |
| `ttl_hours` | 168 (7 days) | **Disk growth**: long-term accumulation across all sessions | The `transcript` table grows without bound |

Key insight: **the write buffer has a hard cap, so lifting retention policies won't directly blow up memory**;
the real risk lies in the storage layer and downstream consumers (see the next section).

> [!TIP]
> **Applications that don't need conversation memory can disable it entirely**: setting
> `ErisPulse.transcript.enabled = false` stops automatic recording of inbound/outbound
> messages — nothing is written to the memory buffer or to storage, saving resident memory
> and continuous storage-layer IO. The session inbox mainly serves two needs: AI context
> injection and repeat-message prevention. Deployments that use neither (e.g., purely
> command-driven bots) are advised to disable it.

## Configuration

```toml
[ErisPulse.transcript]
enabled = true          # Whether to record automatically
max_per_session = 50    # Entries retained per session (0 = disable per-session trimming)
ttl_hours = 168.0       # Global retention duration (hours, 0 = never clean up)
self_echo = "bot"       # Inbound bot echo handling: bot / skip / user
```

Environment variable overrides work as well: `ERISPULSE_TRANSCRIPT_MAX_PER_SESSION`, `ERISPULSE_TRANSCRIPT_TTL_HOURS`,
`ERISPULSE_TRANSCRIPT_SELF_ECHO`.
Configuration changes take effect hot (within the write buffer's flush cadence, at most ~1 second delay).

> [!TIP]
> **Disable it if you don't need conversation memory**: the inbox's only consumers are
> conversation resume / shadow diff / cold-start replay. If your bot (or the modules you
> deploy) doesn't use these capabilities at all, setting `enabled = false`
> saves the inbox's memory buffer and background batch-flush IO — message sending/receiving
> and command handling are completely unaffected.

## Message Attribution (sender and meta)

Every record from all query interfaces (`get` / `recent` / `get_by_trace` / `event.history`)
uniformly carries attribution fields, used to distinguish "who said it / which module sent it":

| Field | Meaning |
|------|------|
| `sender` | Sender identity: `user_id` for inbound; the bot account, or `self.user_id` in the echo case, for outbound |
| `meta` | Metadata captured at record time (whitelist contract, not the full raw event) |

The `meta` whitelist:

- **Inbound**: `nickname` (nickname at event time; a later lookup yields the "current nickname"),
  `self_id` (bot account), `sub_type`, `message_id`; echo messages additionally carry `self_echo: true`;
- **Outbound**: sending context (`platform` / `method` / `detail_type` / `target_id` /
  `bot_id` / `trace_id` / `preview`) and `module` (the module attributed as sender, see below).

For records from older versions (from the era before the meta column), `meta` is `{}`,
so a caller's `meta.get("nickname", "")` degrades gracefully; when the storage backend
doesn't support ALTER, it likewise silently falls back to `{}`.

### Outbound Attribution (meta.module)

Multiple modules on the same instance may send messages (chat, management, scheduled reminders). The `meta.module`
of outbound records identifies the sending attribution, with value priority `current_owner > current_caller > ""`:

| Sending Scenario | module Value |
|----------|-----------|
| During module code invoked via `module.call` | Target module name |
| Sent inside a module's event handler | Name of the module that registered the handler (auto-injected during dispatch) |
| Framework itself / no module context | `""` |

The `message.sent` / `message.sending` hook payloads (send_ctx) also carry the `module` field.

### Inbound Bot Echo (self_echo)

Some platforms/protocol implementations report messages sent by the bot itself back as
message events (e.g., OneBot v11's `report-self-message`, Telegram outgoing messages).
Before recording an inbound message, the framework identifies echoes by
`self.user_id == user_id` and handles them according to the `self_echo` configuration:

| Value | Behavior |
|------|------|
| `"bot"` (default) | Still recorded, but with `role="bot"`, `sender=self_id`, `meta.self_echo=true` |
| `"skip"` | Not recorded (when the adapter also triggers `message.sent`, an outbound record exists naturally) |
| `"user"` | Recorded with `role="user"` (legacy behavior, a compatibility escape hatch) |

On platforms that don't echo (`self.user_id != user_id` always holds), the behavior is exactly the same as having this feature disabled.

### Session-Filtered recent

```python
from ErisPulse import transcript

# Global time window across sessions (cold-start replay semantics, default)
transcript.recent(3600)

# Restricted to a single session: server-side filtering, avoiding client-side
# per-entry session_key comparison after a global fetch
transcript.recent(3600, session_key="onebot11:group:123")
```

`session_key=None` keeps the cross-session semantics; an empty string `""` is equivalent to no filtering (fault tolerant).

## Runtime Override API

When you need to adjust dynamically at runtime (e.g., temporarily extend retention for a particular scenario):

```python
from ErisPulse import transcript

# Override (takes precedence over config; memory-only, config values are restored after restart)
transcript.set_retention(max_per_session=500, ttl_hours=24 * 30)

# Query effective values and their sources
transcript.get_retention()
# {'max_per_session': 500, 'ttl_hours': 720.0, 'overridden': ['max_per_session', 'ttl_hours']}

# Restore config-driven behavior
transcript.reset_retention()
```

- Passing `0` disables the corresponding policy (a warning log is emitted for the record); negative values raise `ValueError`;
- Overrides take effect at the next retention cleanup (lazy, delayed at most by the cadence of ~32 appends);
- The `transcript` singleton can be imported from the root package, or accessed via `sdk.transcript`.

## Risks and Auditing: Must-Read Before Lifting Limits

After disabling `max_per_session` / `ttl_hours` (or greatly increasing them), the `transcript` table
**grows without bound** along with message volume. The chain of consequences:

1. **Disk exhaustion** — the sqlite single file keeps swelling; once disk runs out, the framework's storage layer becomes unavailable;
2. **Query degradation** — the scan costs of `get()` / `recent()` / `get_by_trace()` grow with the table;
3. **Downstream memory pressure (the real source of OOM)** — consumers that load entire stretches of history into memory
   (conversation resume with history, full panel fetches, your business code calling `get(session, n)` with a large n)
   eat more memory as the table grows, and in extreme cases trigger an OOM kill.

**Ask yourself three things before lifting limits**: How far back do you need history? How much of it? Who does the cleanup?
If the answer relies on "never delete anything", the right approach is usually external archiving
(periodically moving old data to a dedicated database), not letting the inbox retain everything indefinitely.

Auditing measures (periodically check table size):

```python
# Query row count and size via the ORM/SQL builder (sqlite as an example)
from ErisPulse import storage

row = storage.Table("transcript").raw_sql("SELECT COUNT(*) AS n FROM transcript")
```

```sql
-- Query the sqlite file directly (table size)
SELECT COUNT(*) FROM transcript;
```

Receiving a warning log of `Retention policy has been disabled` = someone disabled a policy with 0; please confirm it was your own action.

## Boundaries with Other Mechanisms

- **Interactive session timers / wait_reply**: see [Interactive Session System](interaction.md); unrelated to the inbox;
- **History restoration for conversation resume**: `resume(with_history=N)` fetches the most recent N entries from the inbox —
  once the inbox has been trimmed, less history can be restored (increasing `max_per_session` extends the recoverable window);
- **Shadow module diff**: relies on `get_by_trace` chain queries; an inbox with too short a TTL shortens the diffable window.
