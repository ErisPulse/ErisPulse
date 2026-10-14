# Interactive Session System

> [!TIP]
> **When to read this**: When you need `wait_reply`, multi-turn dialogues, timed reminders, session mutual exclusion, or traceability. Skip if not needed, as it does not affect the usage of other features.

> [!NOTE]
> This section requires ErisPulse **2.8.0+**.

ErisPulse has made "continuous interaction with users" a framework-level infrastructure: from a single `wait_reply`, to timed reminders, multi-path waiting, session mutual exclusion, and restart recovery, all are scheduled by a unified **Interactive Session Manager** (`Core/Event/interaction.py`, `sdk.interaction`).

{!--< tips >!--}
Every capability covered in this article comes with its own **ownership (owner)**: interaction waiting, leases, and timers all record the module name at registration time. When a module is unloaded or an adapter is closed, the framework automatically cleans up and the waiting party is immediately notified instead of waiting until timeout — this is an extension of the ownership system in the interaction dimension (see [Ownership System](ownership.md)).
{!--< /tips >!--}

## Waiting for Reply: `wait_reply`

`wait_reply` is the foundation of interactive sessions — it suspends the current coroutine and waits for a reply from the target user in the next message.

```python
from ErisPulse.Core.Event import command

@command("ask")
async def ask_command(event):
    reply = await event.wait_reply(prompt="Please enter your name:", timeout=30)
    if reply is None:
        await event.reply("Timed out")
        return
    await event.reply(f"Hello, {reply.get_text()}!")
```

### All Parameters Overview

| Parameter | Description | Default |
|-----------|-------------|---------|
| `prompt` | Message sent before suspending | None |
| `timeout` | Wait timeout (seconds) | 60 |
| `pattern` | Glob filter (`*` / `?` / `[seq]`), continue waiting if not matched | None |
| `regex` | Regex filter (must match if both `pattern` and `regex` are given), continue waiting if not matched | None |
| `validator` | Validation function (receives Event, returns bool), continue waiting if failed | None |
| `callback` | Callback when reply is received (alternative to return-value style) | None |
| `method` | Method for sending `prompt` | "Text" |
| `session` | **Session-level waiting**: replies from anyone in the same session (group/channel) can match | False |

```python
# Only accept numeric amounts, otherwise continue waiting
reply = await event.wait_reply("Please enter the amount:", regex=r"\d+\s*元", timeout=30)

# Session-level waiting: group collaboration scenario, any group member's reply can match
reply = await event.wait_reply(session=True, prompt="Which expert can help answer?")
```

### The Boundary Between Waiting and Commands (Command Penetration)

During waiting, if a message containing a **registered command** (e.g., `/cancel`) is received, it is by default passed to the command dispatcher and not consumed as a reply (configuration item `ErisPulse.event.wait_reply.cmdpass`, `True` reverses this — messages are always treated as replies). The text judgment standard is consistent with command dispatch: `alt_message` is prioritized, and if missing, message segments are concatenated (生效于 2.10.1起纯 message 段适配器同样生效).

### When Will Waiting Be Cancelled

Waiting is no longer "only waiting until timeout" — the following situations will **immediately terminate** the waiting (`wait_reply` returns `None`), rather than letting the caller wait until timeout:

| Trigger | Cancellation Reason (`InteractionCancelled.reason`) | Description |
|---------|------------------------------------------|-------------|
| Owner module is unloaded / disabled | `owner_unload` | Ownership cleanup: whoever registered the waiting, when they disappear, it is all reclaimed |
| Adapter is closed / restarted | `platform_stop` | All waiting suspended on this platform is cancelled |
| New waiting / lease replaces the same session | `conflict` | See "Session Arbitration" below |
| Replier is blacklisted / owner module is unbound | `revoked` | Permission recheck for reply match: scope identity dimension + module dimension |
| Reply is matched | — | Normal path, return reply event |

The underlying exception is `InteractionCancelled` (attached to the `InteractionError` exception system), and `wait_reply` has converted it to return `None`. Callers who need the reason can directly use the low-level API `sdk.interaction.register()`.

### Complete Matching Chain for Reply

When a reply message arrives, the interaction manager executes the following sequence of judgments (executed **before** command matching, dialog continuity is prioritized — even if the message has been claimed by another high-priority processor, the suspended dialog can still complete):

```
Session key match (exact user dimension → session-level fallback)
  → pattern / regex text filter (continue waiting if not matched)
  → validator check (continue waiting if failed)
  → permission recheck (scope identity dimension + owner module dimension, terminate waiting if failed)
  → wake up waiting party + claim event (mark_processed)
```

## Session Timers: `remind` / `escalate`

Turn "timeout" from a return value into a programmable primitive. Timers are attached to interactive sessions and are automatically cancelled when the module is unloaded or the adapter is closed. The maximum number of active remind timers per session is 5.

### `remind`: Gentle Reminder if No Reply

```python
@command("ticket")
async def ticket_command(event):
    await event.reply("The ticket has been submitted, and the result will be notified here.")
    # If there is no reply for 5 minutes, gently remind once; any reply from the user will automatically cancel it
    event.remind(300, "Are you still there? I will notify you as soon as there is a result.")
    reply = await event.wait_reply(timeout=3600)
    ...
```

- `event.remind(delay, text=None, *, callback=None)`: Sends `text` (or executes `callback(event)`, supports synchronous / asynchronous) to the current session when the timer expires. **Mandatory check**: `text` and `callback` must be chosen exclusively (if neither is provided, a `ValueError` is thrown)
- Returns a `Reminder` handle: `reminder.cancel()` manually cancels, `reminder.expired` queries the status
- Automatically cancels after the user replies in this session — this is the semantics of "reminder": reminders only appear when the user is silent
- Similarly available within `Conversation`: `conv.remind(120, "Are you still considering?")`

### `escalate`: Guaranteed Delivery at the Deadline

```python
event.escalate(1800, lambda e: notify_master(f"Ticket not processed for 30 minutes: {event.get_command_args()}"))
```

The only difference from `remind` is that it is **not automatically cancelled by user replies** — escalation actions (notifying the owner, transferring to human support) are a "guaranteed delivery" promise, cancelled only by manual `cancel()` / module unload / adapter shutdown.

| | `remind` | `escalate` |
|---|---|---|
| Behavior on expiration | Send text / execute callback | Execute callback |
| User reply | **Automatically cancelled** | Unaffected |
| Ownership cleanup (unload / close platform) | Cancelled | Cancelled |
| Maximum per session | 5 | Unlimited (cleaned up by ownership) |

## Multi-path Waiting: `expect` + `select`

Simultaneously suspends multiple expectations, with the **first to arrive wins** — typical scenarios: waiting for admin approval while also waiting for user withdrawal, or multi-person collaborative voting.

```python
which, reply = await event.select(
    event.expect(pattern="Agree*", user="10001"),
    event.expect(pattern="Reject*", user="10002"),
    event.expect(validator=lambda e: e.get_text() == "Suspend", session=True),
    timeout=60,
)
if which is None:
    await event.reply("No approval result received within 60 seconds")
elif which == 0:
    await event.reply("Approved")
elif which == 1:
    await event.reply("Rejected")
```

- `event.expect(...)` constructs an **expectation description** (does not register any waiting): supports `pattern` / `regex` / `validator` / `user` (limits the replier) / `session` (anyone can reply)
- `event.select(*expectations, timeout=60)`: registers uniformly → any match returns `(index, reply event)` → unmet expectations are automatically cancelled; if all timeout, returns `(None, None)`. **Mandatory check**: at least one expectation must be provided, otherwise a `ValueError` is thrown
- The matched event has been claimed by the framework (`mark_processed`), and will not be consumed repeatedly by other processors

{!--< tips >!--}
Compared to manually orchestrating `select` with multi-threaded `asyncio.wait`: unmet expectations are automatically cleaned up, matched events are automatically claimed, permission rechecks and ownership cleanup are all effective — no need to manage any Future yourself.
{!--< /tips >!--}

> [!NOTE]
> Starting from 2.10.1, `select` is a **aggregated waiting**: all expectations are merged into a single entry + custom match judgment, multiple paths with the same key (e.g., two different patterns for the same user) no longer cancel each other, and the first match returns. The judgment criterion for reply text is `alt_message` priority + message segment fallback (consistent with command dispatch).
>
> Boundary explanation: `event.wait_for(...)` is directly attached to the adapter event bus, **not passing** through middleware and `detail_type` condition filtering (identity admission is covered by the distribution entry); for complete pipeline waiting, use `wait_reply` / `select`.

## Session Mutual Exclusion: `acquire` / `hold` / `get_owner_of`

Ownership has moved from "resources" to "sessions" — "who is currently occupying this user" becomes a first-class query.

```python
# Query: who is currently interacting with this session? (Returns None if idle)
owner = sdk.interaction.get_owner_of(event)
if owner and owner != "MyModule":
    return  # Another module is in dialogue, avoid disturbing

# Mutual exclusion lease: exclusive session (deny policy, returns None if occupied)
lease = sdk.interaction.acquire(event)          # Default TTL 1 hour, can pass ttl=
if lease is None:
    return  # Already occupied
try:
    ...  # Exclusive interaction
finally:
    lease.release()
```

Context manager form (throws `SessionOccupiedError` if acquisition fails):

```python
with sdk.interaction.hold(event) as lease:
    ...  # Automatically released on exit
```

Leases support `renew(ttl)` to extend; TTL is lazily expired — expired leases are automatically cleaned up on next access.

When `Conversation.resume()` resumes a dialogue, the framework automatically acquires a lease (see [Conversation Multi-turn Dialogue](conversation.md)'s "Takeover on Resume") — the resumed dialogue naturally holds the session, and other modules cannot intervene.

## Session Inbox: `event.history`

> Retention policy (7 days / maximum number of entries) and runtime override API, risks, and auditing are covered in the [Session Inbox](transcript.md) special topic.

A unified record of recent message streams per session (both user and bot), serving as a **shared fact base** for AI context, anti-repetition, and behavior analysis modules — modules no longer store history individually.

```python
messages = await event.history(20)   # The most recent 20 entries in the current session, in ascending order
for m in messages:
    print(m["role"], ":", m["text"])  # role: "user" / "bot"
```

- Automatic recording: inbound messages (role=user) + robot outbound text (role=bot)
- Storage: separate SQLite table, retention policy = per session maximum (default 50) + global TTL (default 7 days)
- Writing method: memory buffer + background batch write to disk (delay up to 1 second), query interface automatically combines unflushed buffer rows — "read your own write" within the same process is unaffected; automatic flush on normal exit (`sdk.uninit` / process exit). **Hard crash / forced kill may lose the last ~1 second of records**: this base is positioned as a recent context cache, not suitable for audit-level persistence
- Configuration: `ErisPulse.transcript = {enabled = true, max_per_session = 50, ttl_hours = 168}`
- Manager API: `sdk.transcript.append() / get() / clear()`, `aflush()` / `flush()` manual flush

## Message Transaction: `message_tx`

All outbound sends within a transaction are automatically recorded; **on abnormal exit, all sent messages are automatically withdrawn in reverse order** (skipped if adapter does not implement `delete_message`, but the ledger is still recorded normally).

```python
async with event.message_tx():
    await event.reply("Processing, please wait")
    result = await do_something()          # This throws an exception →
    await event.reply(f"Completed: {result}")   # The previous "processing" is automatically withdrawn
```

Outbound sends outside a transaction are not recorded (zero overhead); `get_send_receipts()` can view receipts of messages sent in the current transaction.

## Trace ID

Each inbound event automatically receives a trace ID (reusing `event["id"], generated if missing), which is carried through:

- Handler context (`get_current_trace_id()` to read)
- Outbound sends (`[Send]` log lines append `[trace:...]`, `message.sending/sent` hooks' `trace_id` field)
- Lifecycle hook data (dict automatically adds `_trace_id`)
- Directed events (`lifecycle.emit(..., to=...)`) and message transaction receipts

When a message is processed by multiple modules, the entire chain can be connected using the same ID (for logging / slow query / audit).

## Relationship with Other Systems

- **Ownership**: Waiting / leases / timers all record owner, and are reclaimed on unload (see [Ownership System](ownership.md))
- **Scope**: Reply matching checks identity + module dimension; cross-module calls audit out-of-band (see [Scope](scope.md))
- **Conversation**: Multi-turn dialogue is a state machine on top of interactive sessions (see [Conversation](conversation.md)), and its waiting also enjoys all cancellation / recheck / ownership semantics described on this page

## Related Documentation

- [Conversation Multi-turn Dialogue](conversation.md) - Branch state machine, automatic checkpoints, and restart recovery
- [Ownership (owner) System](ownership.md) - Full picture and design boundaries of ownership cleanup
- [Scope (scope)](scope.md) - Configuration methods for permission recheck and out-of-band audit
- [Module Communication](module-communication.md) - Cross-module calls and directed events