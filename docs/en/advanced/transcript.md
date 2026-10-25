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

## Related Documentation

- **Where inbox history is consumed**: conversation resume [Conversation](conversation.md), event-level reading [event.history](interaction.md#session-inboxeventhistory), shadow diff [Shadow Modules and Gray-Release Promotion](shadow.md)
- **Storage interfaces used for auditing table size** → [Storage Backends](storage-backends.md) and [SQL Query Builder](sql-builder.md)