# Interactive Session System

> [!NOTE]
> This chapter requires ErisPulse **2.8.0+**.

ErisPulse has made "continuous interaction with users" into a framework-level infrastructure: from a single `wait_reply`, to scheduled reminders, multi-path waiting, session mutual exclusion, and restart recovery, all are scheduled by a unified **Interactive Session Manager** (`Core/Event/interaction.py`, `sdk.interaction`).

{!--< tips >!--}
Every capability covered in this article has its own **ownership (owner)**: interaction waiting, leases, and timers all record the module name at registration time. When the module is unloaded or the adapter is closed, the framework automatically cleans up, and the waiting party immediately receives a notification instead of waiting for a timeout — this is an extension of the ownership system in the interaction dimension (see [Ownership System](ownership.md)).
{!--< /tips >!--}

## Waiting for Reply: `wait_reply`

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
| `timeout` | Wait timeout (seconds) | 60 |
| `pattern` | Glob filter (`*` / `?` / `[seq]`), continue waiting if not matched | None |
| `regex` | Regex filter (must match both `pattern` and `regex` if both provided), continue waiting if not matched | None |
| `validator` | Validation function (receives Event, returns bool), continue waiting if fails | None |
| `callback` | Callback when reply is received (alternative to value-returning style) | None |
| `method` | Method for sending the prompt | "Text" |
| `session` | **Session-level waiting**: replies from anyone in the same session (group/channel) can match | False |

```python
# Only accepts numeric amounts, otherwise continue waiting
reply = await event.wait_reply("Please enter the amount:", regex=r"\d+\s*元", timeout=30)

# Session-level waiting: group collaboration scenario, any group member's reply can match
reply = await event.wait_reply(session=True, prompt="Which expert can help answer?")
```

### When Will Waiting Be Cancelled

Waiting is no longer "only waiting for timeout" — the following situations will **immediately terminate** the waiting (returning `None` from `wait_reply`), rather than letting the caller wait until timeout:

| Trigger | Cancellation Reason (`InteractionCancelled.reason`) | Description |
|---------|-----------------------------------------------------|-------------|
| Owner module unloaded / disabled | `owner_unload` | Ownership cleanup: whoever registered the wait will be reclaimed when it disappears |
| Adapter closed / restarted | `platform_stop` | All waits suspended on this platform are cancelled |
| Same session replaced by new wait / lease | `conflict` | See "Session Arbitration" below |
| Replier blacklisted / owner module unbound | `revoked` | Permission复查 (scope identity dimension + module dimension) for reply matching |
| User replies matched | — | Normal path, returns reply event |

The underlying exception is `InteractionCancelled` (attached to the `InteractionError` exception hierarchy), and `wait_reply` has converted it to return `None`; callers who need the reason can directly use the low-level API `sdk.interaction.register()`.

### Complete Decision Chain for Reply Matching

When a reply message arrives, the interaction manager executes the following decision chain (executed before command matching, prioritizing conversation continuity — even if the message has been claimed by a higher-priority processor, the suspended conversation can still complete):

```
Session key match (exact user dimension → session-level fallback)
  → pattern / regex text filter (continue waiting if not matched)
  → validator check (continue waiting if fails)
  → Permission复查 (scope identity dimension + owner module dimension, terminates wait if fails)
  → Wake up waiting party + claim event (mark_processed)
```

## Session Timers: `remind` / `escalate`

Turn "timeout" from a return value into a programmable primitive. Timers are attached to interactive sessions and are automatically cancelled when the module is unloaded or the adapter is closed, with a maximum of 5 active reminds per session.

### `remind`: Remind if no reply

```python
@command("ticket")
async def ticket_command(event):
    await event.reply("Your ticket has been submitted. The processing result will be notified here.")
    # Remind gently after 5 minutes of no reply; any reply from the user will automatically cancel it
    event.remind(300, "Still there? We will notify you as soon as there is a result.")
    reply = await event.wait_reply(timeout=3600)
    ...
```

- `event.remind(delay, text=None, *, callback=None)`: Sends `text` (or executes `callback(event)`, supports synchronous / asynchronous) to the current session upon expiration.
- Returns a `Reminder` handle: `reminder.cancel()` to manually cancel, `reminder.expired` to query status.
- Automatically cancelled by user replies in the session — this is the semantic of "reminder": reminders only appear when the user is silent.
- Also available within `Conversation`: `conv.remind(120, "Still considering?")`

### `escalate`: Guaranteed escalation at a specific time

```python
event.escalate(1800, lambda e: notify_master(f"Ticket processed after 30 minutes: {event.get_command_args()}"))
```

The only difference from `remind`: **not cancelled by user replies** — escalation actions (notifying the owner, transferring to human) are a "guaranteed timeout" promise, cancelled only by manual `cancel()` / module unload / adapter shutdown.

| | `remind` | `escalate` |
|---|---|---|
| Expiration behavior | Send text / execute callback | Execute callback |
| User reply | **Automatically cancelled** | Unaffected |
| Ownership cleanup (unload / close platform) | Cancelled | Cancelled |
| Maximum per session | 5 | Unlimited (ownership cleanup as fallback) |

## Multi-path Waiting: `expect` + `select`

Suspends multiple expectations simultaneously, **first-come, first-served** — typical scenarios: waiting for administrator approval while waiting for user withdrawal, or multi-person collaborative voting.

```python
which, reply = await event.select(
    event.expect(pattern="同意*", user="10001"),
    event.expect(pattern="拒绝*", user="10002"),
    event.expect(validator=lambda e: e.get_text() == "搁置", session=True),
    timeout=60,
)
if which is None:
    await event.reply("No approval result received within 60 seconds")
elif which == 0:
    await event.reply("Approved")
elif which == 1:
    await event.reply("Rejected")
```

- `event.expect(...)` constructs an **expectation description** (does not register any waiting): supports `pattern` / `regex` / `validator` / `user` (limits reply sender) / `session` (anyone can reply).
- `event.select(*expectations, timeout=60)`: Registers uniformly → returns `(index, reply event)` as soon as any match occurs → unmet expectations are automatically cancelled; returns `(None, None)` if all timeout.
- The matched event is claimed by the framework (`mark_processed`), and will not be consumed repeatedly by other processors.

{!--< tips >!--}
Compared to manually orchestrating `asyncio.wait` in multi-threading: unmet expectations are automatically cleaned up, matched events are automatically claimed, and permission复查 and ownership cleanup are all effective — no need to manage any Future yourself.
{!--< /tips >!--}

## Session Mutual Exclusion: `acquire` / `hold` / `get_owner_of`

Ownership moves from "resources" to "session" — "who is currently occupying this user" becomes a first-class query.

```python
# Query: Is this session currently being interacted with? (Returns None if idle)
owner = sdk.interaction.get_owner_of(event)
if owner and owner != "MyModule":
    return  # Another module is currently in conversation, avoid interference

# Mutual exclusion lease: exclusive session (deny policy, returns None if occupied)
lease = sdk.interaction.acquire(event)          # Default TTL 1 hour, can pass ttl=
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

When `Conversation.resume()` resumes a conversation, the framework automatically acquires the lease (see "Resumption as Takeover" in [Conversation Multi-turn Dialogue](conversation.md)) — the resumed conversation naturally holds the session, and other modules cannot intervene.

## Session Inbox: `event.history`

A unified record of recent message streams per session (both user and robot), serving as a **shared factual foundation** for AI context, anti-repetition, and behavioral analysis modules — modules no longer store history individually.

```python
messages = await event.history(20)   # Last 20 messages in the current session, ascending by time
for m in messages:
    print(m["role"], ":", m["text"])  # role: "user" / "bot"
```

- Automatic recording: inbound messages (role=user) + robot outbound text (role=bot)
- Storage: independent SQLite table, retention policy = per-session limit (default 50) + global TTL (default 7 days)
- Configuration: `ErisPulse.transcript = {enabled = true, max_per_session = 50, ttl_hours = 168}`
- Manager API: `sdk.transcript.append() / get() / clear()`

## Message Transaction: `message_tx`

All outbound sends within a transaction are automatically recorded; **on abnormal exit, previously sent messages are automatically withdrawn in reverse order** (skipped if adapter does not implement `delete_message`, but the ledger is still recorded normally).

```python
async with event.message_tx():
    await event.reply("Processing, please wait")
    result = await do_something()          # If an exception is thrown here →
    await event.reply(f"Completed: {result}")   # The previous "processing" message is automatically withdrawn
```

Out-of-transaction sends are not recorded (zero overhead); `get_send_receipts()` can view receipts of messages already sent in the current transaction.

## Trace ID

Each inbound event automatically receives a trace ID (reusing `event["id"], generating one if missing), which is carried through:

- Handler context (`get_current_trace_id()` to read)
- Outbound sends (`[Send]` log lines append `[trace:...]`, `message.sending/sent` hooks' `trace_id` field)
- Lifecycle hook data (dict automatically adds `_trace_id`)
- Directed events (`lifecycle.emit(..., to=...)`) and message transaction receipts

When a message is processed by multiple modules in succession, the same ID can be used to trace the entire chain (logging / slow query / auditing).

## Relationship with Other Systems

- **Ownership**: Waiting / leases / timers all record owner, and are reclaimed on unload (see [Ownership System](ownership.md))
- **Scope**: Reply matching checks identity + module dimension; cross-module call auditing goes out of the outbound dimension (see [Scope](scope.md))
- **Conversation**: Multi-turn dialogue is a branch state machine on top of interactive sessions (see [Conversation](conversation.md)), and its waiting also enjoys all cancellation /复查 / ownership semantics described on this page.

## Related Documents

- [Conversation Multi-turn Dialogue](conversation.md) - Branch state machine, automatic checkpoints, and restart recovery
- [Ownership (owner) System](ownership.md) - Full view and design boundaries of ownership cleanup
- [Scope (scope)](scope.md) - Configuration methods for permission复查 and outbound auditing
- [Inter-module Communication](module-communication.md) - Cross-module calls and directed events