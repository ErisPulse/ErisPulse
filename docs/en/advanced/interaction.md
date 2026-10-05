# Interactive Session System

> [!NOTE]
> This chapter requires ErisPulse **2.8.0+**.

ErisPulse has made "continuous interaction with users" a framework-level infrastructure: from a single `wait_reply`, to timed reminders, multi-path waiting, session mutual exclusion, and restart recovery, all are scheduled by a unified **Interactive Session Manager** (`Core/Event/interaction.py`, `sdk.interaction`).

{!--< tips >!--}
Every capability covered in this document comes with an inherent **ownership**: interaction waiting, leases, and timers all record the module name at registration time. When a module is unloaded or an adapter is closed, the framework automatically cleans up and immediately notifies the waiting party, instead of waiting until timeout — this is an extension of the ownership system in the context of interaction (see [Ownership System](ownership.md)).
{!--< /tips >!--}

## Waiting for Reply: wait_reply

`wait_reply` is the cornerstone of interactive sessions — it suspends the current coroutine and waits for a "reply" from the target user in the next message.

```python
from ErisPulse.Core.Event import command

@command("ask")
async def ask_command(event):
    reply = await event.wait_reply(prompt="Please enter your name:", timeout=30)
    if reply is None:
        await event.reply("Timeout")
        return
    await event.reply(f"Hello, {reply.get_text()}!")
```

### Full Parameter Overview

| Parameter | Description | Default |
|-----------|-------------|---------|
| `prompt` | The prompt message sent before suspension | None |
| `timeout` | Timeout for waiting (seconds) | 60 |
| `pattern` | Glob filtering (`*` / `?` / `[seq]`), continues waiting if not matched | None |
| `regex` | Regex filtering (must match both pattern and regex if both are given), continues waiting if not matched | None |
| `validator` | Validation function (receives Event, returns bool), continues waiting if failed | None |
| `callback` | Callback when a reply is received (alternative to value-returning approach) | None |
| `method` | Method for sending the prompt | "Text" |
| `session` | **Session-level waiting**: replies from anyone in the same session (group/channel) can match | False |

```python
# Only accepts numeric amounts, otherwise continues waiting
reply = await event.wait_reply("Please enter the amount:", regex=r"\d+\s*元", timeout=30)

# Session-level waiting: group collaboration scenario, any group member's reply can match
reply = await event.wait_reply(session=True, prompt="Which expert can help answer?")
```

### When Will Waiting Be Cancelled

Waiting is no longer "only waiting for timeout" — the following situations will immediately terminate the waiting (returning `None` from `wait_reply`), rather than letting the caller wait until timeout:

| Trigger | Cancellation Reason (`InteractionCancelled.reason`) | Description |
|---------|-----------------------------------------------------|-------------|
| Module ownership unloaded / disabled | `owner_unload` | Ownership cleanup: whoever registered the wait is reclaimed when they disappear |
| Adapter closed / restarted | `platform_stop` | All waits suspended on this platform are cancelled |
| New wait / lease replaces within the same session | `conflict` | See "Session Arbitration" below |
| Replier blacklisted / owner module unbound | `revoked` | Permission recheck for reply match: scope identity dimension + module dimension |
| User reply matched | — | Normal path, returns reply event |

The underlying exception is `InteractionCancelled` (part of the `InteractionError` exception hierarchy), and `wait_reply` has converted it to return `None`. Callers needing the reason can directly use the low-level API `sdk.interaction.register()`.

### Complete Reply Matching Chain

When a reply message arrives, the interaction manager follows the sequence below (executed before command matching, prioritizing conversation continuity — even if the message is claimed by another high-priority handler, the suspended conversation can still complete):

```
Session key match (exact user dimension → session-level fallback)
  → pattern / regex text filtering (continues waiting if not matched)
  → validator validation (continues waiting if failed)
  → Permission recheck (scope identity dimension + owner module dimension, fails to terminate waiting)
  → Wake up waiting party + claim event (mark_processed)
```

## Session Timers: remind / escalate

Convert "timeout" from a return value into a programmable primitive. Timers are attached to interactive sessions and automatically cancelled when modules are unloaded or adapters are closed, with a single session active remind limit of 5.

### remind: Remind if no reply

```python
@command("ticket")
async def ticket_command(event):
    await event.reply("The ticket has been submitted. You will be notified here about the processing result.")
    # Remind gently after 5 minutes of no reply; any user reply will automatically cancel it
    event.remind(300, "Are you still there? You will be notified immediately when there is a result.")
    reply = await event.wait_reply(timeout=3600)
    ...
```

- `event.remind(delay, text=None, *, callback=None)`: Sends `text` (or executes `callback(event)`, supporting synchronous / asynchronous) to the current session upon expiration. **Mandatory validation**: `text` and `callback` must be chosen exclusively (neither given throws `ValueError`)
- Returns a `Reminder` handle: `reminder.cancel()` to manually cancel, `reminder.expired` to query status
- Automatically cancels upon user reply in the session — this is the semantic of "reminder": reminders only appear when the user is silent
- Also available within `Conversation`: `conv.remind(120, "Are you still considering?")`

### escalate: Guaranteed escalation at the deadline

```python
event.escalate(1800, lambda e: notify_master(f"Ticket not processed for 30 minutes: {event.get_command_args()}"))
```

The only difference from `remind`: **not cancelled by user reply** — escalation actions (notifying the master, transferring to human) are a "guaranteed timeout" commitment, cancelled only by manual `cancel()` / module unload / adapter shutdown.

| | `remind` | `escalate` |
|---|---|---|
| Expiration behavior | Sends text / executes callback | Executes callback |
| User reply | **Automatically cancelled** | Unaffected |
| Ownership cleanup (unload / close platform) | Cancelled | Cancelled |
| Single session limit | 5 | Unlimited (cleanup by ownership as fallback) |

## Multi-path Waiting: expect + select

Suspends multiple expectations simultaneously, **first-come, first-served** — typical scenarios: waiting for admin approval while also waiting for user withdrawal, or multi-person collaborative voting.

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
- `event.select(*expectations, timeout=60)`: Registers uniformly → returns `(index, reply event)` if any is matched → unmet expectations are automatically cancelled; returns `(None, None)` if all timeout. **Mandatory validation**: at least one expectation must be provided, otherwise throws `ValueError`
- The matched event is claimed by the framework (`mark_processed`), not consumed repeatedly by other handlers

{!--< tips >!--}
Compared to manually orchestrating `select` with multi-threaded `asyncio.wait`: unmet expectations are automatically cleaned up, matched events are automatically claimed, permission rechecks and ownership cleanup are fully effective — no need to manage any Future yourself.
{!--< /tips >!--}

## Session Mutual Exclusion: acquire / hold / get_owner_of

Ownership transitions from "resource" to "session" — "who is currently occupying this user" becomes a first-class query.

```python
# Query: Who is currently interacting in this session? (Returns None if idle)
owner = sdk.interaction.get_owner_of(event)
if owner and owner != "MyModule":
    return  # Another module is already in conversation, avoid interruption

# Mutual exclusion lease: exclusive session (deny strategy, returns None if occupied)
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
    ...  # Automatically releases on exit
```

Leases support `renew(ttl)` for renewal; TTL is lazily expired — expired leases are automatically cleaned up on next access.

When `Conversation.resume()` resumes a conversation, the framework automatically acquires a lease (see "Resume as Takeover" in [Conversation Multi-turn Dialogue](conversation.md)) — the resumed conversation naturally holds the session, and other modules cannot intervene.

## Session Inbox: event.history

A unified record of recent message streams per session (both user and bot), serving as a shared factual base for AI context, anti-repetition, and behavioral analysis modules — modules no longer store history individually.

```python
messages = await event.history(20)   # Last 20 messages in the current session, in ascending time order
for m in messages:
    print(m["role"], ":", m["text"])  # role: "user" / "bot"
```

- Automatic recording: inbound messages (role=user) + outbound bot text (role=bot)
- Storage: Independent SQLite table, retention policy = per-session limit (default 50) + global TTL (default 7 days)
- Writing method: Memory buffer + background batch persistence (delay up to 1 second), query interface automatically merges un-persisted buffer rows — reading your own writes in the same process is unaffected; automatic flush on normal exit (`sdk.uninit` / process exit). **Hard crash / forced kill may lose recent records (about 1 second)**: this base is positioned as a recent context cache, not suitable for audit-level persistence
- Configuration: `ErisPulse.transcript = {enabled = true, max_per_session = 50, ttl_hours = 168}`
- Manager API: `sdk.transcript.append() / get() / clear()`, `aflush()` / `flush()` to manually flush

## Message Transaction: message_tx

All outbound sends within a transaction are automatically logged; **on abnormal exit, previously sent messages are automatically withdrawn in reverse order** (skipped if adapter does not implement `delete_message`, but the ledger is still recorded normally).

```python
async with event.message_tx():
    await event.reply("Processing, please wait")
    result = await do_something()          # Exception thrown here →
    await event.reply(f"Completed: {result}")   # The previous "processing" is automatically withdrawn
```

Sends outside a transaction are not logged (zero overhead); `get_send_receipts()` can view receipts of messages already sent in the current transaction.

## Trace ID

Each inbound event automatically receives a trace ID (reuses `event["id"]`, generates if missing), which is carried through:

- Handler context (`get_current_trace_id()` reads it)
- Outbound sends (`[Send]` log lines append `[trace:...]`, `message.sending/sent` hooks have `trace_id` field)
- Lifecycle hook data (dict automatically adds `_trace_id`)
- Directed events (`lifecycle.emit(..., to=...)`) and message transaction receipts

When a message is processed by multiple modules, the entire chain can be connected with the same ID (for logging / slow query / audit).

## Relationship with Other Systems

- **Ownership**: Waiting / lease / timers all record owner, reclaimed on unload (see [Ownership System](ownership.md))
- **Scope**: Permission recheck on reply match (identity + module dimension); cross-module call audit exits outbound dimension (see [Scope](scope.md))
- **Conversation**: Multi-turn dialogue is a state machine on top of interactive sessions (see [Conversation](conversation.md)), and its waiting shares all cancellation / recheck / ownership semantics described on this page

## Related Documentation

- [Conversation Multi-turn Dialogue](conversation.md) - Branch state machine, automatic checkpoints, and restart recovery
- [Ownership (owner) System](ownership.md) - Overview and design boundaries of ownership cleanup
- [Scope (scope)](scope.md) - Configuration for permission recheck and outbound audit
- [Module Communication](module-communication.md) - Cross-module calls and directed events