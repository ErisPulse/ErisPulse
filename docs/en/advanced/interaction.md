# Interactive Session System

> [!NOTE]  
> This chapter requires ErisPulse **2.8.0+**.

ErisPulse has made "continuous interaction with users" into a framework-level infrastructure: from a single `wait_reply`, to scheduled reminders, multi-path waiting, session mutual exclusion, and restart recovery, all are scheduled by a unified **Interactive Session Manager** (`Core/Event/interaction.py`, `sdk.interaction`).

{!--< tips >!--}
Each capability covered in this document comes with its own **ownership (owner)**: interaction waiting, leases, and timers all record the module name at registration time. When a module is unloaded or an adapter is closed, the framework automatically cleans up and immediately notifies the waiting party, rather than waiting for a timeout. This is an extension of the ownership system in the interaction dimension (see [Ownership System](ownership.md)).
{!--< /tips >!--}

## Waiting for Reply: wait_reply

`wait_reply` is the cornerstone of interactive sessions—suspending the current coroutine and waiting for a reply from the target user in the next message.

```python
from ErisPulse.Core.Event import command

@command("ask")
async def ask_command(event):
    reply = await event.wait_reply(prompt="Please enter your name:", timeout=30)
    if reply is None:
        await event.reply("Timeout.")
        return
    await event.reply(f"Hello, {reply.get_text()}!")
```

### Full Parameter Overview

| Parameter | Description | Default |
|-----------|-------------|---------|
| `prompt` | The prompt message sent before suspending | None |
| `timeout` | Timeout for waiting (seconds) | 60 |
| `pattern` | Glob filter (`*` / `?` / `[seq]`), continue waiting if not matched | None |
| `regex` | Regular expression filter (must match if both pattern and regex are given), continue waiting if not matched | None |
| `validator` | Validation function (receives Event, returns bool), continue waiting if failed | None |
| `callback` | Callback when a reply is received (alternative to value-returning style) | None |
| `method` | Method for sending the prompt | "Text" |
| `session` | **Session-level waiting**: replies from anyone in the same session (group/channel) can match | False |

```python
# Only accepts numeric amounts, otherwise continues waiting
reply = await event.wait_reply("Please enter the amount:", regex=r"\d+\s*元", timeout=30)

# Session-level waiting: for group collaboration, any group member's reply can match
reply = await event.wait_reply(session=True, prompt="Which expert can help answer?")
```

### When Will Waiting Be Cancelled

Waiting is no longer "only waiting for timeout"—the following conditions will cause waiting to **terminate immediately** (`wait_reply` returns `None`), rather than letting the caller wait until timeout:

| Trigger | Cancellation Reason (`InteractionCancelled.reason`) | Description |
|---------|-----------------------------------------------------|-------------|
| Module owner is unloaded / disabled | `owner_unload` | Ownership cleanup: whoever registered the waiting, when they disappear, it is reclaimed together |
| Adapter is stopped / restarted | `platform_stop` | All waiting suspended on this platform is cancelled |
| Same session is replaced by new waiting / lease | `conflict` | See "Session Arbitration" below |
| Replier is blacklisted / owner module is unbound | `revoked` | Permission review for reply match: scope identity dimension + module dimension |
| User reply matches | — | Normal path, returns reply event |

The underlying exception is `InteractionCancelled` (part of the `InteractionError` exception hierarchy), and `wait_reply` has converted it to return `None`. Callers who need the reason can directly use the low-level API `sdk.interaction.register()`.

### Complete Matching Chain for Reply

When a reply message arrives, the interaction manager executes the following sequence of checks (executed before command matching, ensuring conversation continuity— even if the message has been claimed by another high-priority handler, the suspended conversation can still complete):

```
Session key match (exact user dimension → session-level fallback)
  → pattern / regex text filtering (continue waiting if not matched)
  → validator check (continue waiting if failed)
  → permission review (scope identity dimension + owner module dimension, terminate if failed)
  → wake up waiting party + claim event (mark_processed)
```

## Session Timers: remind / escalate

Transform "timeout" from a return value into a composable primitive. Timers are attached to interactive sessions and are automatically cancelled when the module is unloaded or the adapter is stopped. The maximum number of active reminds per session is 5.

### remind: Remind if No Reply

```python
@command("ticket")
async def ticket_command(event):
    await event.reply("The ticket has been submitted. You will be notified here with the result.")
    # Remind gently after 5 minutes if no reply; any reply from the user will automatically cancel it
    event.remind(300, "Still there? We will notify you as soon as there is a result.")
    reply = await event.wait_reply(timeout=3600)
    ...
```

- `event.remind(delay, text=None, *, callback=None)`: Sends `text` (or executes `callback(event)`, supports synchronous / asynchronous) to the current session when the timer expires. **Mandatory validation**: `text` and `callback` must be chosen exclusively (if neither is provided, `ValueError` is raised).
- Returns a `Reminder` handle: `reminder.cancel()` to manually cancel, `reminder.expired` to query status.
- Automatically cancelled when the user replies in the session—this is the semantic of "reminder": reminders only appear when the user is silent.
- Also available within `Conversation`: `conv.remind(120, "Still considering?")`

### escalate: Guaranteed Delivery at a Certain Time

```python
event.escalate(1800, lambda e: notify_master(f"Ticket not processed for 30 minutes: {event.get_command_args()}"))
```

The only difference from `remind`: **not cancelled by user reply**—escalation actions (notifying the owner, transferring to human support) are a "guaranteed timeout" promise, cancelled only by manual `cancel()` / module unload / adapter stop.

| | `remind` | `escalate` |
|---|---|---|
| Behavior on expiration | Send text / execute callback | Execute callback |
| User reply | **Automatically cancelled** | Unaffected |
| Ownership cleanup (unload / stop platform) | Cancelled | Cancelled |
| Maximum per session | 5 | Unlimited (cleaned up by ownership cleanup) |

## Multi-path Waiting: expect + select

Simultaneously suspends multiple expectations, **first come, first served**—typical scenarios: waiting for admin approval while also waiting for user withdrawal, or multi-person collaborative voting.

```python
which, reply = await event.select(
    event.expect(pattern="Agree*", user="10001"),
    event.expect(pattern="Reject*", user="10002"),
    event.expect(validator=lambda e: e.get_text() == "Suspended", session=True),
    timeout=60,
)
if which is None:
    await event.reply("No approval result received within 60 seconds.")
elif which == 0:
    await event.reply("Approved.")
elif which == 1:
    await event.reply("Rejected.")
```

- `event.expect(...)` constructs an **expectation description** (does not register any waiting): supports `pattern` / `regex` / `validator` / `user` (limits the replier) / `session` (anyone can reply).
- `event.select(*expectations, timeout=60)`: Registers uniformly → returns `(index, reply event)` as soon as any match is found → unmet expectations are automatically cancelled; returns `(None, None)` if all timeout. **Mandatory validation**: at least one expectation must be provided, otherwise `ValueError` is raised.
- The matched event is claimed by the framework (`mark_processed`), and will not be consumed again by other handlers.

{!--< tips >!--}
Compared to manually orchestrating with `asyncio.wait` in multithreading: unmet expectations are automatically cleaned up, matched events are automatically claimed, and permission review and ownership cleanup are all effective—no need to manage any Future yourself.
{!--< /tips >!--}

## Session Mutual Exclusion: acquire / hold / get_owner_of

Ownership moves from "resources" to "sessions"—"which module is currently occupying this session" becomes a first-class query.

```python
# Query: Who is currently interacting with this session? (Returns None if idle)
owner = sdk.interaction.get_owner_of(event)
if owner and owner != "MyModule":
    return  # Another module is already in conversation, avoid interruption

# Mutual exclusion lease: exclusive session (deny policy, returns None if occupied)
lease = sdk.interaction.acquire(event)          # Default TTL is 1 hour, can pass ttl=
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
    ...  # Lease is automatically released on exit
```

Leases support `renew(ttl)` for renewal; TTL is lazily expired—expired leases are automatically cleaned up on next access.

When `Conversation.resume()` restores a conversation, the framework automatically acquires the lease (see "Resumption as Takeover" in [Conversation Multi-turn Dialogue](conversation.md))—the resumed conversation naturally holds the session, and other modules cannot intervene.

## Session Inbox: event.history

A unified record of recent message streams for each session (including both user and bot messages), serving as a shared factual foundation for AI context, anti-repetition, and behavioral analysis modules—modules no longer need to store history individually.

```python
messages = await event.history(20)   # The last 20 messages in the current session, in ascending time order
for m in messages:
    print(m["role"], ":", m["text"])  # role: "user" / "bot"
```

- Automatic recording: inbound messages (role=user) + bot outbound text (role=bot)
- Storage: independent SQLite table, retention policy = per session limit (default 50) + global TTL (default 7 days)
- Configuration: `ErisPulse.transcript = {enabled = true, max_per_session = 50, ttl_hours = 168}`
- Manager API: `sdk.transcript.append() / get() / clear()`

## Message Transaction: message_tx

All outbound messages within a transaction are automatically logged; **on abnormal exit, previously sent messages are automatically recalled in reverse order** (skipped if the adapter does not implement `delete_message`, but the ledger is still recorded normally).

```python
async with event.message_tx():
    await event.reply("Processing, please wait")
    result = await do_something()          # If an exception is thrown here →
    await event.reply(f"Completed: {result}")   # The previous "processing" message is automatically recalled
```

Outbound messages sent outside a transaction are not logged (zero overhead); `get_send_receipts()` can view receipts of messages already sent in the current transaction.

## Trace ID

Each inbound event automatically receives a trace ID (reusing `event["id"], generated if missing), which is carried through:

- Handler context (`get_current_trace_id()` to read)
- Outbound sending (`[Send]` log line appends `[trace:...]`, `message.sending/sent` hooks have `trace_id` field)
- Lifecycle hook data (dict automatically adds `_trace_id`)
- Directed events (`lifecycle.emit(..., to=...)`) and message transaction receipts

When a message is processed by multiple modules, the entire chain can be connected using the same ID (logging / slow query / audit).

## Relationship with Other Systems

- **Ownership**: Waiting / leases / timers all record owner, and are reclaimed on unload (see [Ownership System](ownership.md))
- **Scope**: Reply matching checks identity + module dimension; cross-module calls audit the outbound dimension (see [Scope](scope.md))
- **Conversation**: Multi-turn dialogue is a state machine on top of interactive sessions (see [Conversation](conversation.md)), and its waiting also enjoys all cancellation / review / ownership semantics described in this page.

## Related Documentation

- [Conversation Multi-turn Dialogue](conversation.md) - Branch state machine, automatic checkpoints, and restart recovery
- [Ownership (owner) System](ownership.md) - Overview and design boundaries of ownership cleanup
- [Scope (scope)](scope.md) - Configuration of permission review and outbound audit
- [Module-to-Module Communication](module-communication.md) - Cross-module calls and directed events