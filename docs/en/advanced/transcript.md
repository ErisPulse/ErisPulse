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

## Related Documentation

- **Where to consume inbox history**: Conversation Restoration [Conversation](conversation.md), Event-level Read [event.history](interaction.md#conversation-inbox-eventhistory), Shadow Diff [Shadow Module and Gray Release to Production](shadow.md)
- **Storage interfaces used for audit table sizing** → [Storage Backends](storage-backends.md) and [SQL Query Builder](sql-builder.md)