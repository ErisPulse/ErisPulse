# Interactive Conversation System

> [!TIP]
> **When to read this section**: When you need `wait_reply`, multi-turn conversation, timed reminders, session mutual exclusion, or traceability. If not needed, you can skip this section without affecting the use of other features.

> [!NOTE]
> This chapter requires ErisPulse **2.8.0+**.

ErisPulse has made "continuous interaction with users" into a framework-level infrastructure: from a single `wait_reply`, to timed reminders, multi-path waiting, session mutual exclusion, and restart recovery, all are scheduled by a unified **Interactive Session Manager** (`Core/Event/interaction.py`, `sdk.interaction`).

{!--< tips >!--}
Each capability covered in this article comes with its own **ownership (owner)**: interaction waiting, leases, and timers are all recorded with the module name at registration time. When the module is unloaded or the adapter is closed, the framework automatically cleans up and the waiting party immediately receives a notification instead of waiting for a timeout—this is an extension of the ownership system in the interaction dimension (see [Ownership System](ownership.md)).
{!--< /tips >!--}

## Waiting for Reply: wait_reply

`wait_reply` is the cornerstone of interactive sessions — it suspends the current coroutine and waits for the target user to "reply" in the next message.

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
| `prompt` | The prompt message sent before suspension | None |
| `timeout` | Wait timeout (seconds) | 60 |
| `pattern` | Glob filter (`*` / `?` / `[seq]`), continue waiting if not matched | None |
| `regex` | Regex filter (must match both pattern and regex if both are given), continue waiting if not matched | None |
| `validator` | Validation function (receives Event, returns bool), continue waiting if failed | None |
| `callback` | Callback when reply is received (alternative to returning values) | None |
| `method` | Method to send the prompt | "Text" |
| `session` | **Session-level waiting**: replies from anyone in the same session (group/channel) can match | False |

```python
# Only accept numeric amounts, otherwise continue waiting
reply = await event.wait_reply("Please enter the amount:", regex=r"\d+\s*元", timeout=30)

# Session-level waiting: for group collaboration, replies from any group member can match
reply = await event.wait_reply(session=True, prompt="Which expert can help answer?")
```

### The Boundary Between Waiting and Commands (Command Bypass)

During waiting, if a message containing a **registered command** (e.g., `/cancel`) is received, it is by default passed to the command dispatcher and not consumed as a reply (configuration item `ErisPulse.event.wait_reply.cmdpass`, if `True` it reverses — all messages are treated as replies). The text judgment criteria are consistent with command dispatch: `alt_message` takes precedence, and if missing, falls back to message segment concatenation (effective for pure message segment adapters since 2.10.1).

### When Will Waiting Be Cancelled

Waiting is no longer "just waiting until timeout" — the following situations will **immediately terminate** the waiting (`wait_reply` returns `None`), rather than letting the caller wait until timeout:

| Trigger | Cancellation Reason (`InteractionCancelled.reason`) | Description |
|---------|-----------------------------------------------------|-------------|
| The owning module is unloaded / disabled | `owner_unload` | Ownership cleanup: whoever registered the waiting is canceled when they disappear |
| Adapter is stopped / restarted | `platform_stop` | All waiting suspended on this platform is canceled |
| Conflicting with a new waiting / lease in the same session | `conflict` | See "Session Arbitration" below |
| The replier is blacklisted / owner module is unbound | `revoked` | Permission复查 on reply match: scope identity dimension + module dimension |
| The reply is matched | — | Normal path, returns the reply event |

The underlying exception is `InteractionCancelled` (part of the `InteractionError` exception hierarchy), and `wait_reply` has converted it to return `None`. If the reason is needed, the caller can directly use the low-level API `sdk.interaction.register()`.

### Complete Matching Chain for Reply

When a reply message arrives, the interaction manager executes the following sequence of judgments (executed before command matching, prioritizing conversation continuity — even if the message has been claimed by another high-priority processor, the suspended conversation can still complete):

```
Session key match (exact user dimension → session-level fallback)
  → pattern / regex text filter (continue waiting if not matched)
  → validator check (continue waiting if failed)
  → Permission复查 (scope identity dimension + owner module dimension, cancel if failed)
  → Wake up the waiting party + claim the event (mark_processed)
```

## Session Timers: remind / escalate

Transform "timeout" from a return value into a composable primitive. Timers are attached to interactive sessions and are automatically canceled when the module is unloaded or the adapter is stopped. The single session active remind limit is 5.

### remind: Gentle Reminder if No Reply

```python
@command("ticket")
async def ticket_command(event):
    await event.reply("Your ticket has been submitted. You will be notified here with the processing result.")
    # Remind gently after 5 minutes of no reply; any reply from the user will automatically cancel it
    event.remind(300, "Are you still there? We will notify you as soon as there is a result.")
    reply = await event.wait_reply(timeout=3600)
    ...
```

- `event.remind(delay, text=None, *, callback=None)`: Sends `text` (or executes `callback(event)`, supporting synchronous / asynchronous) to the current session upon expiration. **Mandatory check**: `text` and `callback` must be chosen exclusively (neither given throws `ValueError`)
- Returns a `Reminder` handle: `reminder.cancel()` manually cancels, `reminder.expired` queries the status
- Automatically canceled by user reply in the same session — this is the semantics of "reminder": reminders only appear when the user is silent
- Also available within `Conversation`: `conv.remind(120, "Are you still considering?")`

### escalate: Guaranteed Escalation on Time

```python
event.escalate(1800, lambda e: notify_master(f"Ticket not processed for 30 minutes: {event.get_command_args()}"))
```

The only difference from `remind` is that it is **not canceled by user reply** — escalation actions (notifying the owner, transferring to human) are a "guaranteed timeout" commitment, canceled only by manual `cancel()` / module unload / adapter stop.

| | `remind` | `escalate` |
|---|---|---|
| Behavior on expiration | Send text / execute callback | Execute callback |
| User reply | **Automatically canceled** | Unaffected |
| Ownership cleanup (unload / stop platform) | Canceled | Canceled |
| Single session limit | 5 | Unlimited (canceled by ownership cleanup as a fallback) |

## Multi-path Waiting: expect + select

Simultaneously suspends multiple expectations, **first-come, first-served** — typical scenarios: waiting for admin approval while also waiting for user withdrawal, or multi-person collaborative voting.

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
- `event.select(*expectations, timeout=60)`: Registers uniformly → returns `(index, reply event)` as soon as any match is found → unmet expectations are automatically canceled; returns `(None, None)` if all timeout. **Mandatory check**: at least one expectation must be provided, otherwise `ValueError` is thrown
- The matched event is claimed by the framework (`mark_processed`), and will not be consumed by other processors

{!--< tips >!--}
`select` compared to manually orchestrated multi-threading `asyncio.wait`: unmet expectations are automatically cleaned up, matched events are automatically claimed, permission复查 and ownership cleanup are fully effective — no need to manage any Future yourself.
{!--< /tips >!--}

> [!NOTE]
> As of 2.10.1, `select` is a **aggregated waiting**: all expectations are merged into a single entry + custom match judgment, multiple paths with the same key (e.g., two different patterns for the same user) no longer cancel each other, and the first path to match returns. The judgment criterion for reply text is `alt_message` priority + message segment fallback (consistent with command dispatch).
>
> Boundary explanation: `event.wait_for(...)` is directly attached to the adapter event bus, **not passing** through middleware and `detail_type` condition filtering (identity admission is covered by the dispatch entrance); for complete pipeline waiting, use `wait_reply` / `select`.

## Session Mutual Exclusion: acquire / hold / get_owner_of

Ownership moves from "resources" to "session" — "who is currently occupying this user" becomes a first-class query.

```python
# Query: Is this session currently being interacted with? (Returns None if idle)
owner = sdk.interaction.get_owner_of(event)
if owner and owner != "MyModule":
    return  # Another module is currently in conversation, avoid interrupting

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
    ...  # Lease is automatically released on exit
```

The lease supports `renew(ttl)` to extend; TTL is lazily expired — expired leases are automatically cleaned up on next access.

When `Conversation.resume()` resumes a conversation, the framework automatically acquires the lease (see [Conversation Multi-turn Dialogue](conversation.md)'s "Resume Takes Over") — the resumed conversation naturally holds the session, and other modules cannot insert.

## Session Inbox: event.history

> Retention policy (7 days / maximum number of entries) and runtime override API, risks, and audit are covered in the dedicated [Session Inbox](transcript.md) topic.

A unified record of recent message streams per session (both user and bot), serving as a shared factual base for AI context, anti-spam, and behavioral analysis modules — each module no longer stores history individually.

```python
messages = await event.history(20)   # The most recent 20 entries in the current session, in ascending order
for m in messages:
    print(m["role"], ":", m["text"])  # role: "user" / "bot"
```

- Automatic recording: inbound messages (role=user) + bot outbound text (role=bot)
- Storage: separate SQLite table, retention policy = per session limit (default 50) + global TTL (default 7 days)
- Writing method: memory buffer + background batch persistence (delay up to 1 second), query interface automatically merges un-persisted buffer rows — reads within the same process are unaffected; automatic flush on normal exit (`sdk.uninit` / process exit). **Hard crash / force kill may lose the last ~1 second of records**: this base is positioned as a recent context cache, not suitable for audit-level persistence
- Configuration: `ErisPulse.transcript = {enabled = true, max_per_session = 50, ttl_hours = 168}`
- Manager API: `sdk.transcript.append() / get() / clear()`, `aflush()` / `flush()` to manually flush

## Message Transaction: message_tx

All outbound sends within a transaction are automatically logged; **on abnormal exit, previously sent messages are automatically recalled in reverse order** (skipped if the adapter does not implement `delete_message`, but the ledger is still recorded).

```python
async with event.message_tx():
    await event.reply("Processing, please wait")
    result = await do_something()          # If an exception is thrown here →
    await event.reply(f"Completed: {result}")   # The previous "processing" is automatically recalled
```

Outbound sends outside a transaction are not logged (zero overhead); `get_send_receipts()` can view receipts of messages sent in the current transaction.

## Trace ID

Each inbound event automatically receives a trace ID (reusing `event["id"], generating one if missing), which is carried through:

- Handler context (`get_current_trace_id()` to read)
- Outbound sends (`[Send]` log lines append `[trace:...]`, `message.sending/sent` hooks have a `trace_id` field)
- Lifecycle hook data (dict automatically adds `_trace_id`)
- Directed events (`lifecycle.emit(..., to=...)`) and message transaction receipts

When a message is processed by multiple modules, the same ID can be used to link the entire chain (logging / slow query / audit).

## Relationship with Other Systems

- **Ownership**: Waiting / leases / timers all record owner, and are recycled when unloaded (see [Ownership System](ownership.md))
- **Scope**: Reply matching checks identity + module dimension; cross-module calls audit outbound dimension (see [Scope](scope.md))
- **Conversation**: Multi-turn dialogue is a state machine on top of interactive sessions (see [Conversation](conversation.md)), and its waiting also enjoys all cancellation /复查 / ownership semantics described on this page

## Related Documentation

- [Conversation Multi-turn Dialogue](conversation.md) - Branch state machine, automatic checkpoints, and restart recovery
- [Ownership (owner) System](ownership.md) - Overview and design boundaries of ownership cleanup
- [Scope (scope)](scope.md) - Configuration methods for permission复查 and outbound auditing
- [Inter-module Communication](module-communication.md) - Cross-module calls and directed events