# Interactive Conversation System

> [!TIP]
> **When you need to read this**: When you need `wait_reply`, multi-turn conversations, timed reminders, conversation mutual exclusion, or session tracing. If not needed, you can skip it without affecting the use of other features.

> **What you will learn after reading**: The full parameter usage and cancellation reasons for `wait_reply`, the declarative multi-turn chain with `.got()`, session timers (remind / escalate), multi-path waiting (expect / select), and session mutual exclusion leases.

> **What this chapter does not cover**: Multi-turn conversation branch state machines and restart recovery (see [Conversation Multi-turn Conversations](conversation.md)); mailbox retention policy knobs and runtime overrides (see [Conversation Mailbox](transcript.md)).

> [!NOTE]
> This chapter requires ErisPulse **2.8.0+**.

ErisPulse has made "continuous interaction with users" into a framework-level infrastructure: from a single `wait_reply`, to timed reminders, multi-path waiting, session mutual exclusion, and restart recovery, all are scheduled by a unified **Interactive Conversation Manager** (`Core/Event/interaction.py`, `sdk.interaction`).

{!--< tips >!--}
Each capability covered in this article comes with its own **ownership (owner)**: interaction waiting, leases, and timers all record the module name at registration time. When a module is unloaded or an adapter is closed, the framework automatically cleans up and immediately notifies the waiting party instead of waiting for a timeout—this is an extension of the ownership system in the interaction dimension (see [Ownership System](ownership.md)).
{!--< /tips >!--}

## Waiting for Reply: wait_reply

**In one sentence**: Suspends the current coroutine to wait for the next message from the target user, returns the reply event on match, returns `None` on timeout or cancellation, `pattern` / `regex` / `validator` can filter out invalid replies.

`wait_reply` is the foundation of interactive sessions — it suspends the current coroutine and waits for the target user's next message as a "reply".

```python
from ErisPulse.Core.Event import command

@command("ask")
async def ask_command(event):
    reply = await event.wait_reply(prompt="Please enter your name:", timeout=30)
    if reply is None:
        await event.reply("Timed out.")
        return
    await event.reply(f"Hello, {reply.get_text()}!")
```

### All Parameters Overview

| Parameter | Description | Default |
|-----------|-------------|---------|
| `prompt` | The prompt message sent before suspension | None |
| `timeout` | Timeout for waiting (seconds) | 60 |
| `pattern` | Glob filter (`*` / `?` / `[seq]`), continues waiting if not matched | None |
| `regex` | Regular expression filter (must match both `pattern` and `regex` if both provided), continues waiting if not matched | None |
| `validator` | Validation function (receives Event, returns bool), continues waiting if failed | None |
| `callback` | Callback when reply is received (alternative to returning values) | None |
| `method` | Method for sending the prompt | "Text" |
| `session` | **Session-level waiting**: Any reply from anyone in the same session (group/channel) can match | False |

```python
# Only accepts numeric amounts, otherwise continues waiting
reply = await event.wait_reply("Please enter the amount:", regex=r"\d+\s*元", timeout=30)

# Session-level waiting: In group collaboration scenarios, any group member's reply can match
reply = await event.wait_reply(session=True, prompt="Which expert can help answer this?")
```

### The Boundary Between Waiting and Commands (Command Bypass)

During waiting, if a message containing a **registered command** (e.g., `/cancel`) is received, it is by default passed to the command dispatcher and not consumed as a reply (configuration item `ErisPulse.event.wait_reply.cmdpass`, if `True` it reverses — all messages are treated as replies). The text matching criterion is consistent with the command dispatcher: `alt_message` is prioritized, and if missing, falls back to message segment concatenation (effective for pure message segment adapters since 2.10.1).

### When Does Waiting Get Cancelled

Waiting is no longer "only waiting until timeout" — the following situations will **immediately terminate** the waiting (causing `wait_reply` to return `None`), rather than letting the caller wait until timeout:

| Trigger | Cancellation Reason (`InteractionCancelled.reason`) | Description |
|---------|----------------------------------------------------|-------------|
| Module owner is unloaded / disabled | `owner_unload` | Ownership cleanup: whoever registered the wait is cancelled when the owner disappears |
| Adapter shutdown / restart | `platform_stop` | All waits suspended by this platform are cancelled |
| New wait / lease replaces in the same session | `conflict` | See "Session Arbitration" below |
| Replier is blacklisted / owner module is unbound | `revoked` | Reply match **permission recheck**: scope identity dimension + module dimension |
| User reply matches | — | Normal path, returns reply event |

The underlying exception is `InteractionCancelled` (part of the `InteractionError` exception hierarchy), and `wait_reply` has converted it to return `None`. Callers needing the reason can directly use the low-level API `sdk.interaction.register()`.

### Complete Matching Chain for Reply Events

When a reply message arrives, the interaction manager performs the following sequential checks (executed **before** command matching, prioritizing conversation continuity — even if the message has been claimed by a higher-priority processor, the suspended conversation can still complete):

```
Session key match (exact user dimension → session-level fallback)
  → pattern / regex text filtering (continues waiting if not matched)
  → validator check (continues waiting if failed)
  → permission recheck (scope identity dimension + owner module dimension, fails to terminate waiting)
  → wake up waiting party + claim event (mark_processed)
```

## Declarative Multi-turn: `.got()` Chain (2.11+)

`@command` returns a **multi-turn control proxy**, declaring collection steps sequentially using `.got()`—steps receive collected values by parameter name (including command entry parameters), and types are automatically parsed according to `type=` or annotations. Underneath, it compiles into a Conversation: each step is a branch, automatic checkpoint saving, and **user replies resume from the saved step after restart** (the recovery factory is automatically registered during decoration and unregistered with module unload).

```python
@command("weather")
async def weather(event):
    pass  # Entry: the prompt of the first .got is automatically sent, no manual question needed

@weather.got("city", prompt="Please directly reply with the city name")
async def weather_city(event, city: str):
    await event.reply(f"{city}: Sunny, 25℃")

@weather.got("days", prompt="How many days to forecast?", type=int, retry_prompt="Please enter a number")
async def weather_days(event, city: str, days: int):
    await event.reply(f"{city} future {days} days...")
```

### Parameter Description

| Parameter | Description |
|-----------|-------------|
| `name` | Collected value name (injected into subsequent step functions by parameter name; unique within the flow, duplicate declarations cause registration-time errors) |
| `prompt` | Question automatically sent when entering this step |
| `timeout` | Single-step waiting timeout (seconds or "90s" / "1h30m" duration string, default 60s) |
| `type` | Value type (`int` / `float` / `str`…; if parsing fails, `retry_prompt` is automatically resent, up to `max_retries` times) |
| `validator` / `pattern` / `regex` | Reply filtering and validation (semantically consistent with [`wait_reply`](#waiting-for-replywait_reply)) |
| `session` | Session-level waiting (anyone in the same session can match) |
| `cmdpass` | Command pass three-state (default `/cancel` and other commands execute normally during waiting) |

### Semantics and Boundaries

- **Any step timeout / interruption → entire flow ends** and checkpoints are cleared (consistent with `wait_reply` semantics); intermediate results can be output at any time within step functions using `event.reply(...)`
- **Only one suspended interaction per user at a time**—the second flow's waiting will replace the previous one (`InteractionCancelled("conflict")`); for mutual exclusion prompts, please use [Session Lease](#session-mutual-exclusionacquire--hold--get_owner_of)
- Collected values exist only within the flow; for complex state that needs to be carried across restarts, use [Conversation](conversation.md) directly (`context` + `branch/goto` + manual checkpoint)
- `@command` returns a proxy object: calling behavior, `__name__`, docstring, and custom attributes are identical to the original function; `command.unregister(代理)` automatically unpacks

## Session Timers: remind / escalate

Turn "timeout" from a return value into a compositional primitive. Timers are attached to interactive sessions and automatically canceled with module unload or adapter shutdown, with a single session active remind limit of 5.

### remind: Gentle Reminder if No Reply

```python
@command("ticket")
async def ticket_command(event):
    await event.reply("The ticket has been submitted, the result will be notified here")
    # Remind gently after 5 minutes of no reply; any user reply automatically cancels it
    event.remind(300, "Are you still there? We will notify you as soon as there is a result")
    reply = await event.wait_reply(timeout=3600)
    ...
```

- `event.remind(delay, text=None, *, callback=None)`: Sends `text` (or executes `callback(event)`, supporting synchronous/asynchronous) to the current session upon expiration. **Mandatory check**: `text` and `callback` must be chosen exclusively (neither raises `ValueError`)
- Returns a `Reminder` handle: `reminder.cancel()` manually cancels, `reminder.expired` queries status
- Automatically cancels upon user reply in the session—this is the "reminder" semantics: reminders only appear when the user is silent
- Also available within `Conversation`: `conv.remind(120, "Are you still considering?")`

### escalate: Guaranteed Escalation at Deadline

```python
event.escalate(1800, lambda e: notify_master(f"Ticket not processed for 30 minutes: {event.get_command_args()}"))
```

The only difference from `remind` is that it is **not canceled by user reply**—escalation actions (notifying the master, transferring to human) are a "guaranteed timeout" promise, canceled only by manual `cancel()` / module unload / adapter shutdown.

| | `remind` | `escalate` |
|---|---|---|
| Expiration Behavior | Send text / execute callback | Execute callback |
| User Reply | **Automatically canceled** | Unaffected |
| Ownership Cleanup (Unload / Close Platform) | Canceled | Canceled |
| Single Session Limit | 5 | Unlimited (canceled by ownership cleanup as fallback) |

## Multi-Way Waiting: expect + select

**In one sentence**: `expect` only describes the expectation without registering any waiting, while `select` suspends multiple expectations at once, returning `(index, reply event)` as soon as any one matches, and automatically cleans up unmatched ones.

Suspend multiple expectations at once, **first come, first served**—typical scenarios: waiting for an admin approval while also waiting for a user to withdraw, or multi-person collaborative voting.

```python
which, reply = await event.select(
    event.expect(pattern="同意*", user="10001"),
    event.expect(pattern="拒绝*", user="10002"),
    event.expect(validator=lambda e: e.get_text() == "搁置", session=True),
    timeout=60,
)
if which is None:
    await event.reply("60 秒内未收到任何审批结果")
elif which == 0:
    await event.reply("已同意")
elif which == 1:
    await event.reply("已拒绝")
```

- `event.expect(...)` constructs an **expectation description** (without registering any waiting): supports `pattern` / `regex` / `validator` / `user` (limit reply sender) / `session` (anyone can reply)
- `event.select(*expectations, timeout=60)`: registers all expectations uniformly → returns `(index, reply event)` as soon as any one matches → unmet expectations are automatically canceled; returns `(None, None)` if all timeout. **Mandatory validation**: at least one expectation must be provided, otherwise a `ValueError` is thrown
- The matched event is marked as processed by the framework (`mark_processed`), so it won't be consumed again by other handlers

{!--< tips >!--}
Compared to manually orchestrating `asyncio.wait` in multi-threading: automatically cleans up unmet expectations, automatically acknowledges matched events, and all permission checks and cleanup are automatically handled—no need to manage any Future yourself.
{!--< /tips >!--}

> [!NOTE]
> Starting from 2.10.1, `select` is a **collective waiting**: all expectations are merged into a single entry + custom matching logic, and multiple paths with the same key (e.g., two different patterns for the same user) no longer cancel each other out; the first matched path returns. The matching criterion for reply text is `alt_message` priority + message segment fallback (consistent with command dispatching).
>
> Boundary clarification: `event.wait_for(...)` is directly attached to the adapter event bus, **not passing** through middleware and `detail_type` condition filtering (identity access is handled at the dispatch entry). For complete pipeline waiting, use `wait_reply` / `select`.

## Session Mutual Exclusion: acquire / hold / get_owner_of

Ownership moves from "resources" to "session"—"who is currently occupying this user" becomes a first-class query.

```python
# Query: who is currently interacting in this session? (Returns None if idle)
owner = sdk.interaction.get_owner_of(event)
if owner and owner != "MyModule":
    return  # Another module is already in conversation, avoid interruption

# Mutual exclusion lease: exclusively occupy the session (deny policy, returns None if occupied)
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
    ...  # Lease automatically released on exit
```

Leases support `renew(ttl)` renewal; TTL is lazily expired—the expired lease is automatically cleaned up on next access.

`Conversation.resume()` automatically acquires the lease when resuming a conversation (see [Conversation Multi-turn Dialogue](conversation.md)'s "resume takes over")—the resumed conversation naturally holds the session, and other modules cannot intervene.

## Session Inbox: event.history

> Retention policy (7 days / maximum number of entries) and runtime override API, risks, and audit are covered in the [Session Inbox](transcript.md) special topic.

Unified record of recent message streams per session (both user and bot), serving as a **shared fact base** for AI context, anti-repetition, and behavioral analysis modules—modules no longer store history individually.

```python
messages = await event.history(20)   # Last 20 messages in the current session, ascending order
for m in messages:
    print(m["role"], ":", m["text"])  # role: "user" / "bot"
```

- Automatic recording: inbound messages (role=user) + bot outbound text (role=bot)
- Storage: separate SQLite table, retention policy = per session limit (default 50) + global TTL (default 7 days)
- Writing method: memory buffer + background batch persistence (delay up to 1 second), query interface automatically merges un-persisted buffer rows—reading your own writes in the same process is unaffected; normal exit (`sdk.uninit` / process exit) automatically flushes. **Hard crash / forced kill may lose recent about 1 second of records**: this base is positioned as a recent context cache, not suitable for audit-level persistence
- Configuration: `ErisPulse.transcript = {enabled = true, max_per_session = 50, ttl_hours = 168}`
- Manager API: `sdk.transcript.append() / get() / clear()`, `aflush()` / `flush()` manually flush

## Message Transaction: message_tx

All outbound sends within the transaction are automatically logged; **on abnormal exit, previously sent messages are automatically withdrawn in reverse order** (skipped if adapter does not implement `delete_message`, but the ledger is still recorded normally).

```python
async with event.message_tx():
    await event.reply("Processing, please wait")
    result = await do_something()          # Exception thrown here →
    await event.reply(f"Completed: {result}")   # The previous "processing" message is automatically withdrawn
```

Sends outside the transaction are not logged (zero overhead); `get_send_receipts()` can view receipts of messages already sent in the current transaction.

## Trace ID

Each inbound event automatically receives a trace ID (reusing `event["id"], generating one if missing), which is carried through:

- Handler context (`get_current_trace_id()` to read)
- Outbound sends (`[Send]` log line appends `[trace:...]`, `message.sending/sent` hooks have `trace_id` field)
- Lifecycle hook data (dict automatically adds `_trace_id`)
- Directed events (`lifecycle.emit(..., to=...)`) and message transaction receipts

When a message is processed by multiple modules, the same ID can be used to link the entire chain (logging / slow query / audit).

## Relationship with Other Systems

- **Ownership**: Waiting / leases / timers all record owner, and are reclaimed on unload (see [Ownership System](ownership.md))
- **Scope**: Reply match checks identity + module dimension; cross-module audit goes through outbound dimension (see [Scope](scope.md))
- **Conversation**: Multi-turn dialogue is a branch state machine above interactive sessions (see [Conversation](conversation.md)), and its waiting also enjoys all cancellation / recheck / ownership semantics in this page

## Related Documentation

- [Conversation Multi-turn Dialogue](conversation.md) - Branch state machine, automatic checkpoints, and restart recovery
- [Ownership (owner) System](ownership.md) - Overview and design boundaries of ownership cleanup
- [Scope (scope)](scope.md) - Configuration method for permission recheck and outbound audit
- [Module Communication](module-communication.md) - Cross-module calls and directed events