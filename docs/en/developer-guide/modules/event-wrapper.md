# Event Wrapper Class In-Depth Guide

> [!NOTE]
> **L1 Core Required Reading** — one of the five core documents in the homepage "Reading Path"; essential for module development.


The `event` parameter in a handler can directly call `.get_text()` / `.reply()` / `.wait_reply()` thanks to the Event wrapper class. This page is its complete method reference — consult it as needed when writing event handlers; method signatures and behaviors are authoritative here.

## Adding Type Annotations to the event Parameter

The `event` parameter of an event handler is an **Event wrapper class** (a dict subclass). It is **strongly recommended** to add an `Event` type annotation to it (it runs fine without an annotation at runtime; the annotation serves IDE completion and static checking):

```python
from ErisPulse.Core.Event import Event

@message.on_private_message()
async def handler(event: Event):
    text = event.get_text()   # IDE auto-completes all convenience methods
    await event.reply(text)   # Typos can be caught by static checking
```

Without the annotation, the IDE cannot recognize methods on the Event (`get_text()` / `reply()` / `wait_reply()` / platform extension methods are not suggested), so you have to rely on memory to spell them.

> **Note the distinction**: the `event` of event handler callbacks is an **Event wrapper class** (annotated as `Event`); the `event` of the module lifecycle methods `on_load` / `on_unload` is a plain **dict** (annotated as `dict`). Do not confuse the two.

## Core Features

- **Fully dict-compatible**: Event inherits from dict
- **Convenience methods**: provides a large number of convenience methods
- **Dot access**: supports accessing event fields with dot notation
- **Backward compatible**: all methods are optional

## Core Field Methods

```python
from ErisPulse.Core.Event import command, Event

@command("info")
async def info_command(event: Event):
    event_id = event.get_id()
    platform = event.get_platform()
    time = event.get_time()
    print(f"ID: {event_id}, Platform: {platform}, Time: {time}")
```

## Message Event Methods

```python
from ErisPulse.Core.Event import message, Event

@message.on_private_message()
async def private_handler(event: Event):
    text = event.get_text()
    user_id = event.get_user_id()
    nickname = event.get_user_nickname()
    await event.reply(f"Hello, {nickname}!")
```

## Message Type Checks

```python
from ErisPulse.Core.Event import message, Event

@message.on_group_message()
async def group_handler(event: Event):
    is_private = event.is_private_message()
    is_group = event.is_group_message()
    is_at = event.is_at_message()
    await event.reply(f"Type: {'private chat' if is_private else 'group chat'}")
```

## Reply Features

```python
from ErisPulse.Core.Event import command, Event

@command("ask")
async def ask_command(event: Event):
    await event.reply("Please enter your name:")
    reply = await event.wait_reply(timeout=30)
    if reply:
        name = reply.get_text()
        await event.reply(f"Hello, {name}!")

@command("price")
async def price_command(event: Event):
    await event.reply("Please enter the amount (e.g., 5 yuan):")
    # The reply must match the regex, otherwise it keeps waiting until timeout
    reply = await event.wait_reply(timeout=30, regex=r"\d+\s*yuan")
    if reply:
        await event.reply(f"Amount received: {reply.get_text()}")
```

#### Beyond reply: send_chain

For scenarios `reply()` cannot cover — platform-specific modifier methods (such as Expire/Board types), several consecutive modifiers,
or action-type sends without a content parameter — use `event.send_chain` to obtain a send chain with the target and sending account already set,
append modifiers freely, then send:

```python
await event.send_chain.At(event.user_id).Text("content")     # chained modifiers + send
```

For the list of modifier methods, see [Send Method Specification](../../standards/send-method-spec.md).

## Advanced Interaction Sessions

> [!NOTE]
> The capabilities in this section require ErisPulse **2.8.0+**.

```python
# Session timed reminder: reminds after 5 minutes with no reply, auto-cancels once the user replies
reminder = event.remind(300, "Still there? Reply \"exit\" if you don't want to chat anymore")
reminder.cancel()  # Can also be cancelled manually

# Timeout escalation: guaranteed delivery at the deadline (not cancelled by a reply), e.g., notify the owner when a ticket is unhandled for too long
event.escalate(1800, lambda e: notify_master("Ticket timed out"))

# Multi-way wait: wait for "agree" and "decline" simultaneously, first come first served
which, reply = await event.select(
    event.expect(pattern="agree*", user="10001"),
    event.expect(pattern="decline*", user="10002"),
    timeout=60,
)
if which is None:
    await event.reply("Timed out without receiving approval")

# Session-level wait: any reply from anyone in the same group can match (group collaboration)
reply = await event.wait_reply(session=True, prompt="Could anyone kindly help answer?")

# Session inbox: the latest 20 messages in the current session (including the bot; foundation for AI context / anti-repetition)
messages = await event.history(20)

# Message transaction: automatically recalls messages sent within the transaction on exception
async with event.message_tx():
    await event.reply("Processing, please wait...")
    result = await do_something()
    await event.reply(f"Done: {result}")
```

## Retrieving Command Info

```python
from ErisPulse.Core.Event import command, Event

@command("cmdinfo")
async def cmdinfo_command(event: Event):
    cmd_name = event.get_command_name()
    cmd_args = event.get_command_args()
    await event.reply(f"Command: {cmd_name}, Args: {cmd_args}")
```

## Notice Event Methods

```python
from ErisPulse.Core.Event import notice, Event

@notice.on_friend_add()
async def friend_add_handler(event: Event):
    await event.reply("Thanks for adding me as a friend!")
```

## Method Quick Reference

### Core Methods

#### Event Basic Info
- `get_id()` - Get the event ID
- `get_time()` - Get the event timestamp (Unix seconds)
- `get_type()` - Get the event type (message/notice/request/meta)
- `get_detail_type()` - Get the event detail type (private/group/friend, etc.)
- `get_platform()` - Get the platform name

#### Bot Info
- `get_self_platform()` - Get the bot's platform name
- `get_self_user_id()` - Get the bot's user ID
- `get_self_account_id()` - Get the bot's account ID (multi-bot mode)
- `get_self_info()` - Get the bot's full info dictionary

#### Session Identifiers
- `get_target_id()` - Get the unified target ID (group chat returns `group_id`, channel returns `channel_id`, private chat returns `user_id`; takes the first non-empty value in the order group → channel → guild → thread → user)
- `get_session_id()` - Get the unique session identifier, in the format `{platform}:{detail_type}:{target_id}`

### Message Event Methods

#### Message Content
- `get_message()` - Get the message segment array (OneBot12 format)
- `get_alt_message()` - Get the alternate message text
- `get_text()` - Get plain text content (alias of `get_alt_message()`)
- `get_message_text()` - Get plain text content (alias of `get_alt_message()`)

#### Sender Info
- `get_user_id()` - Get the sender's user ID
- `get_user_nickname()` - Get the sender's nickname
- `get_sender()` - Get the sender's full info dictionary

#### Group/Channel Info
- `get_group_id()` - Get the group ID (group chat messages)
- `get_channel_id()` - Get the channel ID (channel messages)
- `get_guild_id()` - Get the guild ID (guild messages)
- `get_thread_id()` - Get the thread/subchannel ID (thread messages)

#### @ Message Related
- `has_mention()` - Whether the event mentions the bot
- `get_mentions()` - Get the list of all mentioned user IDs

### Message Type Checks

#### Basic Checks
- `is_message()` - Whether it is a message event
- `is_private_message()` - Whether it is a private chat message
- `is_group_message()` - Whether it is a group chat message
- `is_at_message()` - Whether it is an @ message (alias of `has_mention()`)

### Notice Event Methods

#### Notice Operator
- `get_operator_id()` - Get the operator ID
- `get_operator_nickname()` - Get the operator nickname

#### Notice Type Checks
- `is_notice()` - Whether it is a notice event
- `is_group_member_increase()` - Group member increase event
- `is_group_member_decrease()` - Group member decrease event
- `is_friend_add()` - Friend addition event (matches `detail_type == "friend_increase"`)
- `is_friend_delete()` - Friend deletion event (matches `detail_type == "friend_decrease"`)

### Request Event Methods

#### Request Info
- `get_comment()` - Get the request comment

#### Request Type Checks
- `is_request()` - Whether it is a request event
- `is_friend_request()` - Whether it is a friend request
- `is_group_request()` - Whether it is a group request

#### Request Approval (approve / reject)

Register a request handler and make decisions on requests:

```python
from ErisPulse.Core.Event import request

@request.on_friend_request()
async def handle_friend(event):
    request_id = event.get_request_id()   # Request identifier (approve/reject raises ValueError when missing)
    if event.get_comment() == "secret code":
        result = await event.approve()    # Approve (optional comment: approve(comment="Welcome"))
    else:
        result = await event.reject()     # Reject
    if result.get("status") != "ok":
        # Standard response format; on failure, message explains the reason (e.g., 34001 request expired)
        pass

@request.on_group_request()               # Group join request / group invitation
async def handle_group(event):
    await event.approve()
```

> Approval actions are executed via the adapter's `Request` DSL; see
> [Request Action Specification](../../standards/request-action-spec.md) for return values, error codes, and adapter implementation requirements. The generic registrar
> `request.on_request()` (no type distinction) is also available.

#### Chain Control (done / is_processed / is_stopped)

- `done(claim=True)` - Claim (default) or only block subsequent lower-priority handlers
- `is_processed()` - Whether the current event has been claimed
- `is_stopped()` - Whether the current event's processing chain has been blocked

For the full semantics of claiming and blocking (priority interaction, command claiming), see
[Event Handling Basics · Chain Control: Claiming and Blocking](../../getting-started/event-handling.md#chain-control-claiming-and-blocking).

### Reply Features

#### Basic Reply
- `reply(content, method="Text", at_sender=False, quote=False, at_users=None, reply_to=None, at_all=False, via=None, **kwargs)` - Universal reply method
  - `content`: Content to send (text, URL, etc.)
  - `method`: Send method, default "Text"; options include "Image"/"Voice"/"Video"/"File", etc.
  - `at_sender`: Whether to @ the sender (automatically extracts user_id)
  - `quote`: Whether to quote-reply the current message (automatically extracts message_id)
  - `at_users`: List of users to @, e.g., `["user1", "user2"]`
  - `reply_to`: Manually specify the message ID to reply to
  - `at_all`: Whether to @ all members
  - `**kwargs`: Additional parameters (e.g., user_id for the Mention method)

- `reply_ob12(message)` - Reply using OneBot12 message segments
  - `message`: OneBot12 message segment list or dict, can be built with MessageBuilder

#### Platform Capability Queries
- `supports(method)` - Check whether the current platform supports a send method (e.g., `"Image"`, `"Voice"`), returns `bool`
- `available_methods()` - List all available send methods on the current platform, returns a list of method names

#### Forwarding

> **Note**: The forwarding feature must be implemented via the adapter's Send DSL; the Event wrapper class itself does not provide a direct forwarding method.

```python
# Forward a message to a group
adapter = sdk.adapter.get(event.get_platform())
target_id = event.get_group_id()  # or specify another group ID
await adapter.Send.To("group", target_id).Text(event.get_text())
```

> **Multi-account deployment**: Sending within the chain that handles an event requires **no explicit account specification** — the framework injects the account identifier that triggered the event into the call context at the event dispatch entry. `Send` / `Api` / `Request` chains automatically bind to the event-triggering account when none is explicitly specified (explicit `Using()` always takes precedence; scenarios without event context, such as timers, use the default account). That is, the forwarding in the example above is sent from "the account that received this event" with no extra code.

#### Cross-Account Duplicate Reception

When multiple accounts join the same group, the same physical message may be received once through each account. The framework handles this according to `ErisPulse.framework.cross_account_policy` (default `off`, no association):

- `mark`: subsequent copies are dispatched as usual, but a `multi_receipt` field is injected at the top level of the event (`{"event_id": id of the first received event, "self_id": first receiving account}`) — modules read this field and decide on their own whether to skip responding
- `drop`: copies are dropped directly at the dispatch entry; modules never see them
- **@ mention privilege**: copies whose mention target matches this account's identity (`self.user_id` / `self.account_id`) do not participate in association (no `multi_receipt` is injected and they are not `drop`ped) — the mentioned account's module (driven by `on_at_message`) can always receive its own event
- **Session account binding**: `ErisPulse.framework.session_accounts` can precisely bind a session to a single owning account (a bound session is dispatched only by the owning account; copies on other accounts are dropped; this works independently of the policy, and the @ mention privilege is still preserved)

### Wait-for-Reply Features

- `wait_reply(prompt=None, timeout=60.0, callback=None, validator=None, method="Text", pattern=None, regex=None)` - Wait for a user reply
  - `prompt`: Prompt message; sent to the user if provided
  - `timeout`: Wait timeout (seconds), default 60 seconds
  - `callback`: Callback function, executed when a reply is received
  - `validator`: Validation function used to verify whether a reply is valid
  - `method`: Method for sending the prompt message, default "Text"
  - `pattern`: Glob wildcard (`*` / `?` / `[seq]`); the reply text must match, otherwise it keeps waiting
  - `regex`: Regular expression; the reply text must match (choose either `pattern` or `regex`), otherwise it keeps waiting
  - Returns the Event object of the user's reply; returns None on timeout

#### Interaction Methods

- `confirm(prompt=None, timeout=60.0, yes_words=None, no_words=None, method="Text", hint=False)` - Confirmation dialogue
  - Returns `True` (confirmed) / `False` (denied) / `None` (timeout)
  - Built-in recognition of Chinese and English confirmation words, with customizable word sets
  - `method`: Send method, default "Text"; supports sending the prompt in non-text ways such as "Image"/"Markdown"
  - `hint`: Whether to automatically append a confirmation hint at the end of the prompt (e.g., "(yes/no)"), default False

- `choose(prompt, options, timeout=60.0, method="Text", options_format="auto", merge_prompt=False, placeholder="{options}")` - Selection menu
  - `options`: List of option texts
  - Returns the selected option index (0-based); returns `None` on timeout
  - `method`: Send method, default "Text"; text-type methods (Text/Markdown/md/Html/h5) merge the options at the end by default
  - `options_format`: Option format (default: "auto", automatically selects a built-in style based on method)
    - `"auto"`: Markdown → unordered list (`- 1. Option`), Html → ordered list (`<ol>`), others → plain text list
    - `"list"`: one per line, e.g., ``1. Option A\n2. Option B``
    - `"inline"`: single-line display, e.g., ``1.A | 2.B``
    - `"md"`: Markdown unordered list
    - `"html"`: Html ordered list
    - `callable`: custom function, receives ``list[str]`` and returns ``str``
  - `merge_prompt`: Whether to force merging into a single message, default False
    - `False` (default): text-type methods merge automatically; non-text methods send the prompt first, then send the Text options
    - `True`: merged into a single message regardless of method, sent with the user-specified method
  - `placeholder`: Placeholder for inserting options, default `{options}`; occurrences of this marker in the prompt are replaced with the option text; set to an empty string to always append at the end

- `collect(fields, timeout_per_field=60.0)` - Form collection
  - `fields`: List of fields; each item includes `key`, `prompt`, optional `validator`, and optional `method`
  - Returns a `{key: value}` dict; returns `None` if any field times out
  - Each field supports a `method` key to specify the send method, e.g., for collecting an image use `{"key": "avatar", "prompt": "Please send an avatar", "method": "Image"}`
  - Each field supports an optional `options` key (list); when provided, the field becomes a multiple-choice question (the choose logic is invoked automatically)
  - Each field supports optional `options_format`, `merge_prompt`, and `placeholder` keys to control option format, message merging behavior, and the placeholder

- `wait_for(event_type="message", condition=None, timeout=60.0)` - Wait for any event
  - `condition`: Filter function; matches when it returns `True`
  - Returns the matched Event object; returns `None` on timeout

- `conversation(timeout=60.0)` - Create a multi-turn conversation context
  - Returns a `Conversation` object supporting `say()`/`wait()`/`confirm()`/`choose()`/`collect()`/`stop()`
  - The `is_active` property indicates whether the conversation is active

#### Interaction Method Examples

**confirm() - Confirmation dialogue:**

```python
from ErisPulse.Core.Event import Event
@command("delete", help="Delete data")
async def delete_handler(event: Event):
    if await event.confirm("Are you sure you want to delete all data?"):
        sdk.storage.delete("all_data")
        await event.reply("Data deleted")
    else:
        await event.reply("Cancelled")
```

**confirm() - With hint:**

```python
# hint=True appends "(yes/no)" at the end of the prompt
if await event.confirm("Continue?", hint=True):
    await event.reply("Continued")
# The user sees: Continue? (yes/no)
```

**choose() - Selection menu:**

```python
from ErisPulse.Core.Event import Event
@command("color", help="Choose a color")
async def color_handler(event: Event):
    choice = await event.choose("Please choose a color:", ["Red", "Green", "Blue"])
    if choice is not None:
        colors = ["Red", "Green", "Blue"]
        await event.reply(f"You chose: {colors[choice]}")
```

**choose() - Option formatting and message merging:**

```python
# inline format: options displayed on the same line
choice = await event.choose("Please choose:", ["A", "B", "C"], options_format="inline")
# Output: 1.A | 2.B | 3.C

# Custom format
choice = await event.choose("Please choose:", ["cat", "dog"],
    options_format=lambda opts: " / ".join(opts))
# Output: cat / dog

# options_format="auto" (default): automatically selects a built-in style based on method
# Markdown → unordered list
choice = await event.choose(
    "## Please choose", ["cat", "dog"],
    method="Markdown",  # auto recognized as an md list
)
# Output:
# ## Please choose
# - 1. cat
# - 2. dog

# Html → ordered list
choice = await event.choose(
    "<h2>Please choose</h2>", ["cat", "dog"],
    method="Html", merge_prompt=True,  # auto recognized as an html list
)
# Output:
# <h2>Please choose</h2>
# <ol><li>1. cat</li><li>2. dog</li></ol>

# Merge mode + placeholder
choice = await event.choose(
    "## Please choose\n{options}\nPlease reply with a number",
    ["cat", "dog"],
    method="Markdown", merge_prompt=True,
)

# Custom placeholder
choice = await event.choose(
    "Please choose: [choices]",
    ["cat", "dog"],
    placeholder="[choices]",
)
```

**collect() - Form collection:**

```python
from ErisPulse.Core.Event import Event
@command("register", help="Register")
async def register_handler(event: Event):
    data = await event.collect([
        {"key": "name", "prompt": "Please enter your name:"},
        {"key": "age", "prompt": "Please enter your age:",
         "validator": lambda e: e.get_text().isdigit()},
    ])
    if data:
        await event.reply(f"Registration successful! {data['name']}, {data['age']} years old")
```

**reply with non-Text methods:**

```python
await event.reply("http://example.com/img.jpg", method="Image")
await event.reply("http://example.com/audio.mp3", method="Voice")

from ErisPulse.Core.Event import MessageBuilder
segments = MessageBuilder.text("Look at this image:").image("http://example.com/img.jpg").build()
await event.reply_ob12(segments)
```

> For the complete Conversation multi-turn dialogue usage, see [Conversation Multi-Turn Dialogue](../../advanced/conversation.md).

### Command Info

#### Command Basics
- `get_command_name()` - Get the command name
- `get_command_args()` - Get the command argument list
- `get_command_raw()` - Get the raw command text
- `get_command_info()` - Get the full command info dictionary
- `is_command()` - Whether it is a command

### Raw Data

- `get_raw()` - Get the platform's raw event data
- `get_raw_type()` - Get the platform's raw event type

### Platform Extension Methods

Adapters can register platform-specific methods for the Event wrapper class. A method is available only on Event instances of the corresponding platform; accessing it from other platforms raises an `AttributeError`.

Platform methods take effect via `Event.__getattribute__` with priority over built-in methods, so you can override built-in interaction methods such as `confirm`, `choose`, `collect`, and `wait_reply` with platform-flavored implementations (e.g., buttons, cards). The built-in implementations are exported as `_builtin_*` functions for overriders to call.

```python
# Email event - email methods only
event = Event({"platform": "email", "email_raw": {"subject": "Hello"}})
event.get_subject()      # ✅ returns "Hello"
event.get_chat_type()    # ❌ AttributeError

# Telegram event - Telegram methods only
event = Event({"platform": "telegram", "telegram_raw": {"chat": {"type": "private"}}})
event.get_chat_type()    # ✅ returns "private"
event.get_subject()      # ❌ AttributeError

# Built-in methods are always available
event.get_text()         # ✅ any platform
event.reply("hi")        # ✅ any platform
```

### Querying Registered Methods

```python
from ErisPulse.Core.Event import get_platform_event_methods

methods = get_platform_event_methods("email")
# ["get_subject", "get_from", ...]
```

### `hasattr` and `dir` Support

```python
hasattr(event, "get_subject")   # returns True only when platform="email"
"get_subject" in dir(event)     # same as above
```

### Cross-Platform Extensions (Wildcards)

`register_event_method` and `register_event_mixin` accept `"*"` as the platform name; registered methods are available on Event instances across **all platforms**. Suitable for features that need cross-platform reuse, such as AI chat and context management.

```python
from ErisPulse.Core.Event.wrapper import register_event_method

@register_event_method("*")
async def ai_chat(self, prompt: str):
    # self is an Event instance; event data and built-in methods are accessible
    await self.reply(f"AI: {prompt}")
```

Once registered, event handlers on any platform can call `event.ai_chat(...)`.

Method resolution priority (high to low): platform-specific methods → wildcard methods → built-in methods → dict key access.

> For how adapter developers register extension methods, see [Event System API - Cross-Platform Extensions (Wildcards)](../../api-reference/event-system.md#cross-platform-extensions-wildcards).

## Related Documents

### Continue the Module Development Path

- [Module Development Basics](getting-started.md) - Create your first module
- [Module Best Practices](best-practices.md) - Develop high-quality modules

### Deepen Interaction Capabilities

- [Conversation Multi-Turn Dialogue](../../advanced/conversation.md) - A complete conversation engine on top of `wait_reply` (collection, validation, branch jumps)