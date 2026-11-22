# Event Wrapper Class in Detail

> [!NOTE]
> **L1 Core Must-Read** — one of the five core documents in the "Reading Path" on the homepage, essential for module development.

The `event` parameter in handlers can directly call `.get_text()` / `.reply()` / `.wait_reply()` thanks to the Event wrapper class. This document is its complete method reference — consult it as needed when writing event handlers; method signatures and behaviors here are authoritative.

## Adding Type Annotations for the event Parameter

The `event` parameter of an event handler is an **Event wrapper class** (a dict subclass). It is **strongly recommended** to annotate it with the `Event` type (it still runs without the annotation at runtime; the annotation serves IDE autocompletion and static checks):

```python
from ErisPulse.Core.Event import Event

@message.on_private_message()
async def handler(event: Event):
    text = event.get_text()   # IDE autocompletes all convenience methods
    await event.reply(text)   # typos can be caught by static checks
```

Without the annotation, the IDE cannot recognize the methods on Event (`get_text()` / `reply()` / `wait_reply()` / platform extension methods are all not suggested), and you have to spell them from memory.

> **Note the distinction**: the `event` in event handler callbacks is an **Event wrapper class** (annotated as `Event`); the `event` in module lifecycle methods `on_load` / `on_unload` is a plain **dict** (annotated as `dict`). Do not confuse the two.

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
    await event.reply(f"Type: {'Private chat' if is_private else 'Group chat'}")
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
    await event.reply("Please enter an amount (e.g., 5 yuan):")
    # The reply must match the regex, otherwise keep waiting until timeout
    reply = await event.wait_reply(timeout=30, regex=r"\d+\s*yuan")
    if reply:
        await event.reply(f"Amount received: {reply.get_text()}")
```

#### Beyond reply: send_chain

For scenarios `reply()` cannot cover — platform-specific modifier methods (such as Expire/Board types), multiple consecutive modifiers,
or action-type sends without a content parameter — use `event.send_chain` to obtain a send chain with the target and sending account already set,
then freely append modifiers and send:

```python
await event.send_chain.At(event.user_id).Text("content")     # chained modifiers + send
```

For the list of modifier methods, see [Send Method Specification](../../standards/send-method-spec.md).

## Advanced Interactive Sessions

> [!NOTE]
> Features in this section require ErisPulse **2.8.0+**.

```python
# Session timed reminder: remind after 5 minutes without a reply; auto-cancels once the user replies
reminder = event.remind(300, "Still there? Reply 'quit' if you don't want to chat")
reminder.cancel()  # can also be cancelled manually

# Timeout escalation: guaranteed delivery when time is up (not cancelled by replies), e.g. notify the master when a ticket stays unhandled for too long
event.escalate(1800, lambda e: notify_master("Ticket timed out"))

# Multi-path waiting: wait for "agree" and "decline" simultaneously; first come, first served
which, reply = await event.select(
    event.expect(pattern="agree*", user="10001"),
    event.expect(pattern="decline*", user="10002"),
    timeout=60,
)
if which is None:
    await event.reply("Approval not received before timeout")

# Session-level waiting: replies from anyone in the same group can match (group collaboration)
reply = await event.wait_reply(session=True, prompt="Could any expert here help answer?")

# Session inbox: the most recent 20 messages of the current session (including the bot; foundation for AI context / repeat prevention)
messages = await event.history(20)

# Message transaction: automatically recalls messages already sent within the transaction when an exception occurs
async with event.message_tx():
    await event.reply("Processing, please wait...")
    result = await do_something()
    await event.reply(f"Done: {result}")
```

## Command Information Retrieval

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

#### Event Basic Information
- `get_id()` - Get the event ID
- `get_time()` - Get the event timestamp (Unix, second-level)
- `get_type()` - Get the event type (message/notice/request/meta)
- `get_detail_type()` - Get the event detail type (private/group/friend, etc.)
- `get_platform()` - Get the platform name

#### Bot Information
- `get_self_platform()` - Get the bot's platform name
- `get_self_user_id()` - Get the bot's user ID
- `get_self_account_id()` - Get the bot's account ID (multi-bot mode)
- `get_self_info()` - Get the bot's complete info dict

#### Session Identifier
- `get_target_id()` - Get the unified target ID (group chat returns `group_id`, channel returns `channel_id`, private chat returns `user_id`; takes the first non-empty value in the order group → channel → guild → thread → user)
- `get_session_id()` - Get the unique session identifier, in the format `{platform}:{detail_type}:{target_id}`

### Message Event Methods

#### Message Content
- `get_message()` - Get the message segment array (OneBot12 format)
- `get_alt_message()` - Get the alternative text of the message
- `get_text()` - Get the plain text content (alias of `get_alt_message()`)
- `get_message_text()` - Get the plain text content (alias of `get_alt_message()`)

#### Sender Information
- `get_user_id()` - Get the sender's user ID
- `get_user_nickname()` - Get the sender's nickname
- `get_sender()` - Get the sender's complete info dict

#### Group/Channel Information
- `get_group_id()` - Get the group ID (group chat messages)
- `get_channel_id()` - Get the channel ID (channel messages)
- `get_guild_id()` - Get the guild ID (guild messages)
- `get_thread_id()` - Get the thread/sub-channel ID (topic messages)

#### Mentions
- `has_mention()` - Whether the message contains an @ of the bot
- `get_mentions()` - Get the list of all @-mentioned user IDs

### Message Type Checks

#### Basic Checks
- `is_message()` - Whether it is a message event
- `is_private_message()` - Whether it is a private message
- `is_group_message()` - Whether it is a group message
- `is_at_message()` - Whether it is an @message (alias of `has_mention()`)

### Notice Event Methods

#### Notice Operator
- `get_operator_id()` - Get the operator ID
- `get_operator_nickname()` - Get the operator nickname

#### Notice Type Checks
- `is_notice()` - Whether it is a notice event
- `is_group_member_increase()` - Group member increase event
- `is_group_member_decrease()` - Group member decrease event
- `is_friend_add()` - Friend add event (matches `detail_type == "friend_increase"`)
- `is_friend_delete()` - Friend delete event (matches `detail_type == "friend_decrease"`)

### Request Event Methods

#### Request Information
- `get_comment()` - Get the request's accompanying comment

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
    request_id = event.get_request_id()   # Request identifier (approve/reject raise ValueError when missing)
    if event.get_comment() == "secret code":
        result = await event.approve()    # Approve (can include a comment: approve(comment="Welcome"))
    else:
        result = await event.reject()     # Reject
    if result.get("status") != "ok":
        # Standard response format; on failure, message explains the reason (e.g. 34001 request expired)
        pass

@request.on_group_request()               # Group join application / group invitation
async def handle_group(event):
    await event.approve()
```

> Approval actions are executed via the adapter `Request` DSL; for return values, error codes and adapter implementation requirements, see
> [Request Action Specification](../../standards/request-action-spec.md). The generic registrar
> `request.on_request()` (type-agnostic) is also available.

#### Chain Control (done / is_processed / is_stopped)

- `done(claim=True)` - Claim (default) or only block subsequent lower-priority handlers
- `is_processed()` - Whether the current event has been claimed
- `is_stopped()` - Whether the current event processing chain has been blocked

For the complete semantics of claim and block (priority interaction, command claiming), see
[Event Handling Basics · Chain Control: Claim and Block](../../getting-started/event-handling.md#chain-control-claim-and-block).

### Reply Features

#### Basic Reply
- `reply(content, method="Text", at_sender=False, quote=False, at_users=None, reply_to=None, at_all=False, via=None, **kwargs)` - General-purpose reply method
  - `content`: content to send (text, URL, etc.)
  - `method`: send method, default "Text", options include "Image"/"Voice"/"Video"/"File", etc.
  - `at_sender`: whether to @ the sender (auto-extracts user_id)
  - `quote`: whether to quote-reply the current message (auto-extracts message_id)
  - `at_users`: list of users to @, e.g. `["user1", "user2"]`
  - `reply_to`: manually specify the message ID to reply to
  - `at_all`: whether to @ all members
  - `**kwargs`: extra parameters (e.g. user_id for the Mention method)

- `reply_ob12(message)` - Reply using OneBot12 message segments
  - `message`: OneBot12 message segment list or dict, can be built with MessageBuilder

#### Platform Capability Queries
- `supports(method)` - Check whether the current platform supports a send method (e.g. `"Image"`, `"Voice"`), returns `bool`
- `available_methods()` - List all send methods available on the current platform, returns a list of method names

#### Forwarding

> **Note**: forwarding must be implemented via the adapter's Send DSL; the Event wrapper class itself does not provide a direct forward method.

```python
# Forward the message to a group
adapter = sdk.adapter.get(event.get_platform())
target_id = event.get_group_id()  # or specify another group ID
await adapter.Send.To("group", target_id).Text(event.get_text())
```

> **Multi-account deployment**: sending within the chain processing an event **does not require explicitly specifying an account** — the framework injects the triggering event's account identifier into the call context at the event dispatch entry; when the `Send` / `Api` / `Request` chains do not explicitly specify an account, the triggering account is bound automatically (an explicit `Using()` always takes precedence; scenarios without event context, such as timers, fall back to the default account). That is, the forwarding in the example above is sent from "the account that received this event", with no extra code needed.

#### Cross-Account Duplicate Receipt

When multiple accounts are in the same group, the same physical message may be received once per account. The framework handles this according to `ErisPulse.framework.cross_account_policy` (default `off`, no correlation):

- `mark`: subsequent copies are dispatched as usual, but a `multi_receipt` field is injected at the top level of the event (`{"event_id": id of the first receiving event, "self_id": first receiving account}`) — modules read this field and decide on their own whether to skip the response
- `drop`: copies are discarded directly at the dispatch entry, transparent to modules
- **At-mention exemption**: copies whose mention target matches this account's identity (`self.user_id` / `self.account_id`) do not participate in correlation (no `multi_receipt` injected, not `drop`ped) — the module of the @-mentioned account (driven by `on_at_message`) always receives its own event
- **Session account binding**: `ErisPulse.framework.session_accounts` can precisely bind a session to a single owning account (bound sessions are dispatched only by the owning account; copies on other accounts are discarded; this takes effect independently of the policy, and the at-mention exemption is preserved as well)

> For configuration formats, prefix key syntax and the division of labor among the three deduplication layers, see [Adapter Core Concepts](../adapters/core-concepts.md) and [Configuration File Reference](../../user-guide/configuration.md).

### Wait-for-Reply Features

- `wait_reply(prompt=None, timeout=60.0, callback=None, validator=None, method="Text", pattern=None, regex=None)` - Wait for a user reply
  - `prompt`: prompt message; if provided, it is sent to the user
  - `timeout`: wait timeout (seconds), default 60 seconds
  - `callback`: callback function executed when a reply is received
  - `validator`: validation function used to check whether a reply is valid
  - `method`: method used to send the prompt message, default "Text"
  - `pattern`: glob wildcard (`*` / `?` / `[seq]`); the reply text must match, otherwise keep waiting
  - `regex`: regular expression; the reply text must match (choose either `pattern` or `regex`), otherwise keep waiting
  - Returns the Event object of the user's reply, or None on timeout

#### Interactive Methods

- `confirm(prompt=None, timeout=60.0, yes_words=None, no_words=None, method="Text", hint=False)` - Confirmation dialog
  - Returns `True` (confirmed) / `False` (denied) / `None` (timeout)
  - Built-in Chinese and English confirmation words are auto-recognized; word sets are customizable
  - `method`: send method, default "Text"; supports non-text methods like "Image"/"Markdown" for sending the prompt
  - `hint`: whether to automatically append a confirmation-words hint at the end of the prompt (e.g. "(yes/no)"), default False

- `choose(prompt, options, timeout=60.0, method="Text", options_format="auto", merge_prompt=False, placeholder="{options}")` - Choice menu
  - `options`: list of option texts
  - Returns the option index (0-based), or `None` on timeout
  - `method`: send method, default "Text"; text-type methods (Text/Markdown/md/Html/h5) merge the options at the end by default
  - `options_format`: option format (default: "auto", picks a built-in style automatically according to method)
    - `"auto"`: Markdown→unordered list (`- 1.option`), Html→ordered list (`<ol>`), others→plain text list
    - `"list"`: one per line, e.g. ``1. Option A\n2. Option B``
    - `"inline"`: single-line display, e.g. ``1.A | 2.B``
    - `"md"`: Markdown unordered list
    - `"html"`: Html ordered list
    - `callable`: custom function that receives ``list[str]`` and returns ``str``
  - `merge_prompt`: whether to force sending merged into a single message, default False
    - `False` (default): text-type methods merge automatically; non-text methods send the prompt first, then send the Text options
    - `True`: merge into a single message regardless of method, sent with the user-specified method
  - `placeholder`: placeholder for inserting the options, default `{options}`; positions in the prompt where this token appears are replaced with the option text; set to an empty string to always append to the end

- `collect(fields, timeout_per_field=60.0)` - Form collection
  - `fields`: list of fields, each containing `key`, `prompt`, optional `validator`, optional `method`
  - Returns a `{key: value}` dict, or `None` if any field times out
  - Each field supports a `method` key to specify the send method, e.g. when collecting an image use `{"key": "avatar", "prompt": "Please send an avatar", "method": "Image"}`
  - Each field can have an optional `options` key (a list); when provided, that field becomes a multiple-choice question (choose logic is invoked automatically)
  - Each field can have optional `options_format`, `merge_prompt`, `placeholder` keys to control option format, message merging behavior and the placeholder

- `wait_for(event_type="message", condition=None, timeout=60.0)` - Wait for any event
  - `condition`: filter function; matches when it returns `True`
  - Returns the matched Event object, or `None` on timeout

- `conversation(timeout=60.0)` - Create a multi-turn conversation context
  - Returns a `Conversation` object supporting `say()`/`wait()`/`confirm()`/`choose()`/`collect()`/`stop()`
  - The `is_active` property indicates whether the conversation is active

#### Interactive Method Examples

**confirm() - Confirmation dialog:**

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
# hint=True appends "(yes/no)" to the end of the prompt
if await event.confirm("Continue?", hint=True):
    await event.reply("Continued")
# The user sees: Continue? (yes/no)
```

**choose() - Choice menu:**

```python
from ErisPulse.Core.Event import Event
@command("color", help="Choose a color")
async def color_handler(event: Event):
    choice = await event.choose("Please choose a color:", ["red", "green", "blue"])
    if choice is not None:
        colors = ["red", "green", "blue"]
        await event.reply(f"You chose: {colors[choice]}")
```

**choose() - Option formatting and message merging:**

```python
# inline format: options are displayed on the same line
choice = await event.choose("Please choose:", ["A", "B", "C"], options_format="inline")
# Output: 1.A | 2.B | 3.C

# Custom format
choice = await event.choose("Please choose:", ["cat", "dog"],
    options_format=lambda opts: " / ".join(opts))
# Output: cat / dog

# options_format="auto" (default): picks a built-in style automatically according to method
# Markdown → unordered list
choice = await event.choose(
    "## Please choose", ["cat", "dog"],
    method="Markdown",  # auto recognizes it as an md list
)
# Output:
# ## Please choose
# - 1. cat
# - 2. dog

# Html → ordered list
choice = await event.choose(
    "<h2>Please choose</h2>", ["cat", "dog"],
    method="Html", merge_prompt=True,  # auto recognizes it as an html list
)
# Output:
# <h2>Please choose</h2>
# <ol><li>1. cat</li><li>2. dog</li></ol>

# Merge mode + placeholder
choice = await event.choose(
    "## Please choose\n{options}\nReply with a number",
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

> For the complete Conversation multi-turn usage, see [Conversation Multi-Turn Dialogs](../../advanced/conversation.md).

### Command Information

#### Command Basics
- `get_command_name()` - Get the command name
- `get_command_args()` - Get the list of command arguments
- `get_command_raw()` - Get the raw command text
- `get_command_info()` - Get the complete command info dict
- `is_command()` - Whether it is a command

### Raw Data

- `get_raw()` - Get the platform's raw event data
- `get_raw_type()` - Get the platform's raw event type

### Platform Extension Methods

Adapters can register platform-specific methods on the Event wrapper class. Methods are only available on Event instances of the corresponding platform; accessing them from other platforms raises an `AttributeError`.

Platform methods take effect via `Event.__getattribute__` with higher priority than built-in methods, so they can override built-in interactive methods such as `confirm`, `choose`, `collect`, `wait_reply` to provide platform-specific implementations (buttons, cards, etc.). The built-in implementations are exported as `_builtin_*` functions for overriding parties to call.

```python
# Email event - only email methods
event = Event({"platform": "email", "email_raw": {"subject": "Hello"}})
event.get_subject()      # ✅ returns "Hello"
event.get_chat_type()    # ❌ AttributeError

# Telegram event - only Telegram methods
event = Event({"platform": "telegram", "telegram_raw": {"chat": {"type": "private"}}})
event.get_chat_type()    # ✅ returns "private"
event.get_subject()      # ❌ AttributeError

# Built-in methods are always available
event.get_text()         # ✅ on any platform
event.reply("hi")        # ✅ on any platform
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

`register_event_method` and `register_event_mixin` accept `"*"` as the platform name; methods registered this way are available on Event instances of **all platforms**. Suitable for cross-platform reusable features such as AI conversation and context management.

```python
from ErisPulse.Core.Event.wrapper import register_event_method

@register_event_method("*")
async def ai_chat(self, prompt: str):
    # self is the Event instance; event data and built-in methods are accessible
    await self.reply(f"AI: {prompt}")
```

After registration, event handlers on any platform can call `event.ai_chat(...)`.

Method resolution priority (high to low): platform-specific methods → wildcard methods → built-in methods → dict key access.

> For how adapter developers register extension methods, see [Event System API - Cross-Platform Extensions](../../api-reference/event-system.md#cross-platform-extensions-wildcards).

## Related Documents

### Continue the Module Development Path

- [Module Development Basics](getting-started.md) - Create your first module
- [Module Best Practices](best-practices.md) - Develop high-quality modules

### Dive Deeper into Interaction Capabilities

- [Conversation Multi-Turn Dialogs](../../advanced/conversation.md) - A complete session engine built on top of `wait_reply` (collection, validation, branching)