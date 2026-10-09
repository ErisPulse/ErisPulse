# Transcript

The Transcript Inbox automatically records messages sent and received by the bot (organized by session key `platform:detail_type:target_id`), providing historical data for conversation recovery (`event.history`), shadow module diff, cold start replay, and more. This document explains its **storage model, what each retention policy knob protects**, and the real cost of runtime override APIs and放开限制.

> Before changing any limits, please read the "Risks and Audits" section first—each knob exists for a reason.

## How It Works

```
Message ──append()──▶ Write buffer (in-memory deque, hard limit 4096 lines)
                        │  Batched persistence every 1 second (batch ≤64 lines, single transaction)
                        ▼
              transcript table in storage backend (default sqlite)
                        │  Lazy trigger of retention cleanup after ~32 appends
                        ▼
              ┌─ FIFO trimming by session (max_per_session, default 50 lines)
              └─ Global TTL deletion (ttl_hours, default 168 = 7 days)
```

Three levels of protection, each guarding against different risks:

| Knob | Default | Protection | Consequence if disabled (=0) |
|------|---------|------------|------------------------------|
| Write buffer limit | 4096 lines (constant, not configurable) | **Memory**: Prevents RAM blowup during storage unavailability | Cannot be disabled—this is the memory safety net |
| Single text truncation | 2000 characters (constant, not configurable) | Memory/disk usage per message | Cannot be disabled |
| `max_per_session` | 50 lines/session | **Disk growth**: Prevents infinite accumulation of session history | Session history grows indefinitely |
| `ttl_hours` | 168 (7 days) | **Disk growth**: Prevents long-term accumulation across all sessions | `transcript` table grows indefinitely |

Key insight: **The write buffer has a hard limit, so relaxing retention policies won't directly blow up memory**;  
The real risk lies in the storage layer and downstream consumers (see next section).

## Configuration

```toml
[ErisPulse.transcript]
enabled = true          # Whether to automatically record
max_per_session = 50    # Number of entries to retain per session (0 = disable session trimming)
ttl_hours = 168.0       # Global retention duration (hours, 0 = never clean up)
```

Environment variables also take effect: `ERISPULSE_TRANSCRIPT_MAX_PER_SESSION`, `ERISPULSE_TRANSCRIPT_TTL_HOURS`.  
Configuration changes take effect immediately (within the write buffer flush interval, with a maximum delay of ~1 second).

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