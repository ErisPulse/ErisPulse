# Interactive Session System

> [!NOTE]
> This chapter requires ErisPulse **2.8.0+**.

ErisPulse has made "continuous interaction with users" into a framework-level infrastructure: from a single `wait_reply`, to scheduled reminders, multi-path waiting, session mutual exclusion, and restart recovery, all are scheduled by a unified **Interactive Session Manager** (`Core/Event/interaction.py`, `sdk.interaction`).

{!--< tips >!--}
Each capability covered in this article comes with a **owner** (owner): interaction waiting, lease, and timers all record the module name at registration time. When the module is unloaded or the adapter is closed, the framework automatically cleans up and the waiting party immediately receives a notification instead of waiting for a timeout — this is an extension of the ownership system in the interactive dimension (see [Ownership System](ownership.md)).
{!--< /tips >!--}

## Waiting for Reply: wait_reply

`wait_reply` is the cornerstone of interactive sessions — it suspends the current coroutine and waits for the target user to "reply" in the next message.

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

### Full Parameter Overview

| Parameter | Description | Default |
|-----------|-------------|---------|
| `prompt` | The prompt message sent before suspension | None |
| `timeout` | Timeout for waiting (seconds) | 60 |
| `pattern` | Glob filter (`*` / `?` / `[seq]`), continues waiting if not matched | None |
| `regex` | Regex filter (must match both pattern and regex if both are given), continues waiting if not matched | None |
| `validator` | Validation function (receives Event, returns bool), continues waiting if failed | None |
| `callback` | Callback when reply is received (alternative to return-value style) | None |
| `method` | Method to send the prompt | "Text" |
| `session` | **Session-level waiting**: replies from anyone in the same session (group/channel) can match | False |

```python
# Only accepts numeric amounts, otherwise continues waiting
reply = await event.wait_reply("Please enter the amount:", regex=r"\d+\s*元", timeout=30)

# Session-level waiting: group collaboration scenario, any group member's reply can match
reply = await event.wait_reply(session=True, prompt="Which expert can help answer?")
```

### When Will the Waiting Be Cancelled

Waiting is no longer "only waiting for timeout" — the following conditions will **immediately terminate** the waiting (returning `None` from `wait_reply`), instead of letting the caller wait until timeout:

| Trigger | Cancellation Reason (`InteractionCancelled.reason`) | Description |
|---------|-----------------------------------------------------|-------------|
| The owning module is unloaded / disabled | `owner_unload` | Ownership cleanup: whoever registered the waiting, when it disappears, it is reclaimed together |
| Adapter is stopped / restarted | `platform_stop` | All waiting suspended on this platform is cancelled |
| New waiting / lease replaces in the same session | `conflict` | See "Session Arbitration" below |
| The reply sender is blacklisted / owner module is unbound | `revoked` | Permission review for reply matching: scope identity dimension + module dimension |
| Reply is received | — | Normal path, returns the reply event |

The underlying exception is `InteractionCancelled` (under the `InteractionError` exception hierarchy), and `wait_reply` has converted it to return `None`. Callers who need the reason can directly use the low-level API `sdk.interaction.register()`.

### Complete Matching Chain for Reply

When a reply message arrives, the interactive manager executes the following sequence of determinations (executed before command matching, prioritizing conversation continuity — even if the message has been claimed by a higher-priority handler, the suspended conversation can still complete):

```
Session key match (precise user dimension → session-level fallback)
  → pattern / regex text filtering (continues waiting if not matched)
  → validator validation (continues waiting if failed)
  → permission review (scope identity dimension + module dimension, fails then terminates waiting)
  → wake up the waiting party + claim event (mark_processed)
```

## Session Timers: remind / escalate

Turn "timeout" from a return value into a composable primitive. Timers are attached to interactive sessions and are automatically cancelled when the module is unloaded or the adapter is stopped. The single session active remind limit is 5.

### remind: Remind if No Reply

```python
@command("ticket")
async def ticket_command(event):
    await event.reply("The ticket has been submitted, the processing result will be notified here.")
    # If there is no reply within 5 minutes, gently remind once; any reply from the user will automatically cancel it
    event.remind(300, "Are you still there? The result will be notified to you as soon as possible.")
    reply = await event.wait_reply(timeout=3600)
    ...
```

- `event.remind(delay, text=None, *, callback=None)`: Sends `text` (or executes `callback(event)`, supports synchronous / asynchronous) to the current session after `delay` expires. **Mandatory validation**: `text` and `callback` must be chosen exclusively (if neither is given, `ValueError` is thrown)
- Returns a `Reminder` handle: `reminder.cancel()` to manually cancel, `reminder.expired` to query status
- Automatically cancels after the user replies in this session — this is the semantics of "reminder": reminders only appear when the user is silent
- Also available within `Conversation`: `conv.remind(120, "Are you still considering?")`

### escalate: Guaranteed Delivery at a Point in Time

```python
event.escalate(1800, lambda e: notify_master(f"Ticket not processed for 30 minutes: {event.get_command_args()}"))
```

The only difference from `remind`: **not cancelled by user reply** — escalation actions (notifying the master, transferring to human) are a "guaranteed delivery" promise, cancelled only by manual `cancel()` / module unload / adapter stop.

| | `remind` | `escalate` |
|---|---|---|
| Behavior on expiration | Sends text / executes callback | Executes callback |
| User reply | **Automatically cancels** | Unaffected |
| Ownership cleanup (unload / stop platform) | Cancels | Cancels |
| Single session limit | 5 | Unlimited (ownership cleanup as fallback) |

## Multi-path Waiting: expect + select

Suspends multiple expectations simultaneously, **first-come, first-served** — typical scenarios: waiting for administrator approval while waiting for user withdrawal, or multi-person collaborative voting.

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
- `event.select(*expectations, timeout=60)`: Registers uniformly → returns `(index, reply event)` on first match → unmet expectations are automatically cancelled; all timeouts return `(None, None)`. **Mandatory validation**: at least one expectation must be passed, otherwise `ValueError` is thrown
- The matched event has been claimed by the framework (`mark_processed`), and will not be consumed repeatedly by other processors

{!--< tips >!--}
Compared to manually orchestrating `select` with multi-threading `asyncio.wait`: unmet expectations are automatically cleaned up, matched events are automatically claimed, permission review and ownership cleanup all take effect — no need to manage any Future yourself.
{!--< /tips >!--}

## Session Mutual Exclusion: acquire / hold / get_owner_of

Ownership moves from "resources" to "sessions" — "who is currently occupying this user" becomes a first-class query.

```python
# Query: who is currently interacting with this session? (Returns None if idle)
owner = sdk.interaction.get_owner_of(event)
if owner and owner != "MyModule":
    return  # Another module is already in conversation, avoid interruption

# Mutual exclusion lease: exclusive session (deny policy, returns None if occupied)
lease = sdk.interaction.acquire(event)          # Default TTL 1 hour, ttl= can be passed
if lease is None:
    return  # Already occupied
try:
    ...  # Exclusive interaction
finally:
    lease.release()
```

Context manager form (throws `SessionOccupiedError` on failure):

```python
with sdk.interaction.hold(event) as lease:
    ...  # Automatically released on exit
```

Leases support `renew(ttl)` renewal; TTL is lazily expired — expired leases are automatically cleaned up on next access.

`Conversation.resume()` automatically acquires leases when resuming conversations (see [Conversation Multi-turn Dialogue](conversation.md)'s "Resume Takes Over") — resumed conversations naturally hold the session, and other modules cannot intervene.

## Session Inbox: event.history

> Retention policies (7 days / maximum number of entries) and runtime override APIs, risks, and audits are covered in the [Session Inbox](transcript.md) topic.

A unified record of recent message streams per session (both user and bot), serving as a **shared factual base** for AI contexts, anti-spam, and behavior analysis modules — modules no longer store history individually.

```python
messages = await event.history(20)   # Recent 20 entries of current session, ascending by time
for m in messages:
    print(m["role"], ":", m["text"])  # role: "user" / "bot"
```

- Automatic recording: inbound messages (role=user) + bot outbound text (role=bot)
- Storage: separate SQLite table, retention policy = per-session limit (default 50) + global TTL (default 7 days)
- Writing method: memory buffer + background batch persistence (delay up to 1 second), query interface automatically combines un-persisted buffer rows — "read your write" within the same process is unaffected; normal exit (`sdk.uninit` / process exit) automatically flushes to disk. **Hard crash / forced kill may lose recent records for about 1 second**: this base is positioned as a recent context cache, not suitable for audit-level persistence
- Configuration: `ErisPulse.transcript = {enabled = true, max_per_session = 50, ttl_hours = 168}`
- Manager API: `sdk.transcript.append() / get() / clear()`, `aflush()` / `flush()` to manually flush

## Message Transaction: message_tx

All outbound sends within a transaction are automatically recorded; **on abnormal exit, previously sent messages are automatically withdrawn in reverse order** (skipped if adapter does not implement `delete_message`, but the ledger is still recorded normally).

```python
async with event.message_tx():
    await event.reply("Processing, please wait")
    result = await do_something()          # Exception thrown here →
    await event.reply(f"Completed: {result}")   # The previous "processing" is automatically withdrawn
```

Sends outside a transaction are not recorded (zero overhead); `get_send_receipts()` can view receipts of messages already sent in the current transaction.

## Trace ID

Each inbound event automatically receives a trace ID (reusing `event["id"], generates if missing), which is carried through:

- Handler context (`get_current_trace_id()` to read)
- Outbound sends (`[Send]` log line appends `[trace:...]`, `message.sending/sent` hooks have `trace_id` field)
- Lifecycle hook data (dict automatically adds `_trace_id`)
- Directed events (`lifecycle.emit(..., to=...)`) and message transaction receipts

When a message is processed by multiple modules in succession, the entire chain can be linked with the same ID (for logging / slow query / audit).

## Relationship with Other Systems

- **Ownership**: Waiting / lease / timers all record owner, and are reclaimed on unload (see [Ownership System](ownership.md))
- **Scope**: Reply matching reviews identity + module dimension; cross-module calls audit exit dimension (see [Scope](scope.md))
- **Conversation**: Multi-turn dialogue is a branch state machine above interactive sessions (see [Conversation](conversation.md)), and its waiting enjoys all cancellation / review / ownership semantics described on this page

## Related Documentation

- [Conversation Multi-turn Dialogue](conversation.md) - Branch state machine, automatic checkpoints, and restart recovery
- [Ownership (owner) System](ownership.md) - Full view and design boundaries of ownership cleanup
- [Scope (scope)](scope.md) - Configuration method for permission review and exit audit
- [Module-to-Module Communication](module-communication.md) - Cross-module calls and directed events