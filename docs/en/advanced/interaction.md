# Interactive Session System

> [!NOTE]
> This chapter requires ErisPulse **2.8.0+**.

ErisPulse has built "continuous interaction with users" into its core infrastructure: from a single `wait_reply`, to scheduled reminders, multi-path waiting, session mutual exclusion, and restart recovery, all are managed by a unified **Interactive Session Manager** (`Core/Event/interaction.py`, `sdk.interaction`).

{!--< tips >!--}
Each capability covered in this document comes with its own **ownership** (owner): interactive waiting, leases, and timers all record the module name at registration time. When the module is unloaded or the adapter is closed, the framework automatically cleans up and notifies the waiting party immediately, rather than waiting until timeout. This is an extension of the ownership system in the interactive dimension (see [Ownership System](ownership.md)).
{!--< /tips >!--}

## Waiting for Reply: wait_reply

`wait_reply` is the cornerstone of interactive sessions—suspending the current coroutine and waiting for a reply from the target user in the next message.

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
| `prompt` | The prompt message sent before suspending | None |
| `timeout` | Timeout for waiting (seconds) | 60 |
| `pattern` | Glob filter (`*` / `?` / `[seq]`), continue waiting if not matched | None |
| `regex` | Regular expression filter (must match both pattern and regex if both are provided), continue waiting if not matched | None |
| `validator` | Validation function (receives Event, returns bool), continue waiting if failed | None |
| `callback` | Callback when reply is received (alternative to value-returning approach) | None |
| `method` | Method for sending prompt | "Text" |
| `session` | **Session-level waiting**: replies from anyone in the same session (group/channel) can match | False |

```python
# Accept only numeric amounts, otherwise continue waiting
reply = await event.wait_reply("Please enter the amount:", regex=r"\d+\s*元", timeout=30)

# Session-level waiting: group collaboration scenario, any group member's reply can match
reply = await event.wait_reply(session=True, prompt="Which expert can help answer?")
```

### When Will Waiting Be Cancelled

Waiting is no longer "only waiting until timeout"—the following conditions will cause the waiting to **terminate immediately** (`wait_reply` returns `None`), rather than letting the caller wait until timeout:

| Trigger | Cancellation Reason (`InteractionCancelled.reason`) | Description |
|---------|------------------------------------------------------|-------------|
| Owner module is unloaded / disabled | `owner_unload` | Ownership cleanup: whoever registered the waiting, when they disappear, it is reclaimed together |
| Adapter is stopped / restarted | `platform_stop` | All waiting suspended on this platform is cancelled |
| Same session is replaced by new waiting / lease | `conflict` | See "Session Arbitration" below |
| Replier is blacklisted / owner module is unbound | `revoked` | Permission recheck for reply hit: scope identity dimension + module dimension |
| User reply is matched | —— | Normal path, returns reply event |

The underlying exception is `InteractionCancelled` (attached to the `InteractionError` exception hierarchy), and `wait_reply` has converted it to returning `None`; calling parties who need the reason can directly use the low-level API `sdk.interaction.register()`.

### Complete Reply Matching Decision Chain

When a reply message arrives, the interaction manager follows the following sequence to decide (executed **before** command matching, conversation continuity takes priority— even if the message has been claimed by another high-priority processor, the suspended conversation can still complete):

```
Session key hit (exact user dimension → session-level fallback)
  → pattern / regex text filter (continue waiting if not matched)
  → validator check (continue waiting if failed)
  → Permission recheck (scope identity dimension + owner module dimension, terminate waiting if failed)
  → Wake up waiting party + claim event (mark_processed)
```

## Session Timers: remind / escalate

Transform "timeout" from a return value into a programmable primitive. Timers are attached to interactive sessions and are automatically cancelled when the module is unloaded or the adapter is closed, with a single session active remind limit of 5.

### remind: Remind if No Reply

```python
@command("ticket")
async def ticket_command(event):
    await event.reply("Your ticket has been submitted, and the processing result will be notified here.")
    # Remind gently after 5 minutes of no reply; any reply from the user will automatically cancel it
    event.remind(300, "Are you still there? I will notify you as soon as there is a result.")
    reply = await event.wait_reply(timeout=3600)
    ...
```

- `event.remind(delay, text=None, *, callback=None)`: Sends `text` (or executes `callback(event)`, supports synchronous / asynchronous) to the current session when the timer expires.
- Returns a `Reminder` handle: `reminder.cancel()` to manually cancel, `reminder.expired` to query status.
- Automatically cancels after the user replies in this session—this is the semantics of "reminder":
  Reminders only appear when the user is silent.
- Also available within `Conversation`: `conv.remind(120, "Are you still considering?")`

### escalate: Guaranteed Upgrade at a Point in Time

```python
event.escalate(1800, lambda e: notify_master(f"Ticket not processed for 30 minutes: {event.get_command_args()}"))
```

The only difference from `remind`: **Not cancelled by user replies**—the escalation action (notifying the master, transferring to human) is a "guaranteed timeout" promise, cancelled only by manual `cancel()` / module unload / adapter shutdown.

| | `remind` | `escalate` |
|---|---|---|
| Behavior on expiration | Send text / execute callback | Execute callback |
| User reply | **Automatically cancelled** | Unaffected |
| Ownership cleanup (unload / close platform) | Cancelled | Cancelled |
| Single session limit | 5 | Unlimited (cleaned up by ownership) |

## Multi-path Waiting: expect + select

Simultaneously suspends multiple expectations, **first-come, first-served**—typical scenarios: waiting for administrator approval while waiting for user withdrawal, or multi-person collaboration voting.

```python
which, reply = await event.select(
    event.expect(pattern="Agree*", user="10001"),
    event.expect(pattern="Reject*", user="10002"),
    event.expect(validator=lambda e: e.get_text() == "Suspended", session=True),
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
- `event.select(*expectations, timeout=60)`: Registers uniformly → returns `(index, reply event)` on the first match → unmet expectations are automatically cancelled; returns `(None, None)` if all time out
- The matched event has been claimed by the framework (via `mark_processed`), and will not be consumed by other processors again

{!--< tips >!--}
Compared to manual orchestration with multi-threaded `asyncio.wait`, `select` automatically cleans up unmet expectations, automatically claims matched events, and ensures permission rechecks and ownership cleanup—all without needing to manage any Future yourself.
{!--< /tips >!--}

## Session Mutual Exclusion: acquire / hold / get_owner_of

Ownership moves from "resources" to "sessions"—"who is currently occupying this user" becomes a first-class query.

```python
# Query: Is this session currently being interacted with? (Returns None if idle)
owner = sdk.interaction.get_owner_of(event)
if owner and owner != "MyModule":
    return  # Another module is already interacting, avoid interrupting

# Mutual exclusion lease: exclusive session (deny policy, returns None if occupied)
lease = sdk.interaction.acquire(event)          # Default TTL 1 hour, ttl can be passed
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

Leases support `renew(ttl)` renewal; TTL is lazily expired—the expired lease is automatically cleaned up on next access.

When `Conversation.resume()` resumes a conversation, the framework automatically acquires the lease (see "Resumption Takes Over" in [Conversation Multi-turn Dialogue](conversation.md))—the resumed conversation naturally holds the session, and other modules cannot insert.

## Session Inbox: event.history

A unified record of recent message streams per session (both user and robot), serving as a **shared factual foundation** for AI contexts, anti-repetition, and behavioral analysis modules—modules no longer store history individually.

```python
messages = await event.history(20)   # Recent 20 messages of current session, in ascending time order
for m in messages:
    print(m["role"], ":", m["text"])  # role: "user" / "bot"
```

- Automatic recording: inbound messages (role=user) + robot outbound text (role=bot)
- Storage: independent SQLite table, retention policy = per session limit (default 50) + global TTL (default 7 days)
- Configuration: `ErisPulse.transcript = {enabled = true, max_per_session = 50, ttl_hours = 168}`
- Manager API: `sdk.transcript.append() / get() / clear()`

## Message Transaction: message_tx

All outbound sends within a transaction are automatically recorded; **on abnormal exit, previously sent messages are automatically recalled in reverse order** (skipped if adapter does not implement `delete_message`, but the ledger is still recorded properly).

```python
async with event.message_tx():
    await event.reply("Processing, please wait")
    result = await do_something()          # Exception thrown here →
    await event.reply(f"Completed: {result}")   # The previous "processing" message is automatically recalled
```

Outbound sends outside a transaction are not recorded (zero overhead); `get_send_receipts()` can view the receipts of messages already sent in the current transaction.

## Trace ID

Each inbound event automatically receives a trace ID (reusing `event["id"], generating one if missing), which is carried through:

- Handler context (`get_current_trace_id()` to read)
- Outbound sends (`[Send]` log lines append `[trace:...]`, `message.sending/sent` hooks have a `trace_id` field)
- Lifecycle hook data (dict automatically adds `_trace_id`)
- Directed events (`emit_to`) and message transaction receipts

When a message is processed by multiple modules, the entire chain can be linked with the same ID (for logging / slow query / audit).

## Relationship with Other Systems

- **Ownership**: Waiting / leases / timers all record owner, and are reclaimed on unload (see [Ownership System](ownership.md))
- **Scope**: Permission recheck for reply hits at both identity and module dimensions; cross-module audit steps out of the outbound dimension (see [Scope](scope.md))
- **Conversation**: Multi-turn dialogue is a branching state machine above interactive sessions (see [Conversation](conversation.md)), and its waiting also enjoys all cancellation / recheck / ownership semantics described on this page

## Related Documentation

- [Conversation Multi-turn Dialogue](conversation.md) - Branching state machine, automatic checkpoints, and restart recovery
- [Ownership (owner) System](ownership.md) - Overview and design boundaries of ownership cleanup
- [Scope (scope)](scope.md) - Configuration methods for permission recheck and outbound audit
- [Module-to-Module Communication](module-communication.md) - Cross-module calls and directed events