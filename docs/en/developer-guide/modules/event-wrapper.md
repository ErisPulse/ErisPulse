# Event Wrapper Class in Detail

> [!NOTE]
> **L1 Core Must-Read** — one of the five core documents in the "Reading Path" on the homepage; essential for module development.


The reason the `event` parameter in handlers can directly call `.get_text()` / `.reply()` / `.wait_reply()` is the Event wrapper class. This page is its complete method reference — consult it as needed when writing event handlers; the method signatures and behaviors here are authoritative.

## Adding Type Annotations to the `event` Parameter

The `event` parameter of an event handler is an **Event wrapper class** (a dict subclass). It is **strongly recommended** to add the `Event` type annotation to it (the code still runs without annotations at runtime; annotations serve IDE autocompletion and static checking):

```python
from ErisPulse.Core.Event import Event

@message.on_private_message()
async def handler(event: Event):
    text = event.get_text()   # The IDE autocompletes all convenience methods
    await event.reply(text)   # Typos can be caught during static checking
```

Without annotations, the IDE cannot recognize methods on Event (`get_text()` / `reply()` / `wait_reply()` / platform extension methods are not suggested), so you would have to rely on memory to spell them.

> **Note the distinction**: the `event` of an event handler callback is an **Event wrapper class** (annotated as `Event`); the `event` of the module lifecycle methods `on_load` / `on_unload` is a plain **dict** (annotated as `dict`). Do not confuse the two.

## Core Features

- **Fully dict-compatible**: Event inherits from dict
- **Convenience methods**: Provides a large number of convenience methods
- **Dot access**: Supports accessing event fields via dot notation
- **Backward compatible**: All methods are optional

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

## Message Type Detection

```python
from ErisPulse.Core.Event import message, Event

@message.on_group_message()
async def group_handler(event: Event):
    is_private = event.is_private_message()
    is_group = event.is_group_message()
    is_at = event.is_at_message()
    await event.reply(f"Type: {'Private' if is_private else 'Group'}")
```

## Reply Functionality

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

For scenarios that `reply()` cannot cover — platform-specific modifier methods (such as Expire/Board types), multiple consecutive modifiers, and action-type sends without content parameters — use `event.send_chain` to get a send chain with the target and sending account already set, freely append modifiers, and then send:

```python
await event.send_chain.At(event.user_id).Text("content")     # Chained modifiers + send
```

For the list of modifier methods, see [Send Method Specification](../../standards/send-method-spec.md).

## Advanced Interactive Sessions

> [!NOTE]
> The features in this section require ErisPulse **2.8.0+**.

```python
# Session scheduled reminder: remind after 5 minutes without a reply; auto-cancels once the user replies
reminder = event.remind(300, "Still there? Reply 'quit' if you don't want to chat")
reminder.cancel()  # Can also be cancelled manually

# Timeout escalation: guaranteed to fire on time (not cancelled by replies), e.g., notify the master if unhandled for too long
event.escalate(1800, lambda e: notify_master("Ticket timed out"))

# Multi-way wait: wait for "agree" and "decline" at the same time; first come, first served
which, reply = await event.select(
    event.expect(pattern="agree*", user="10001"),
    event.expect(pattern="decline*", user="10002"),
    timeout=60,
)
if which is None:
    await event.reply("Approval not received before timeout")

# Session-level wait: replies from anyone in the same group can match (group collaboration)
reply = await event.wait_reply(session=True, prompt="Can anyone help answer this?")

# Session inbox: the 20 most recent messages in the current session (including the bot; foundation for AI context / anti-repetition)
messages = await event.history(20)

# Message transaction: automatically recalls messages sent within the transaction if an exception occurs
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
- `get_time()` - Get the event timestamp (Unix seconds)
- `get_type()` - Get the event type (message/notice/request/meta)
- `get_detail_type()` - Get the event detail type (private/group/friend, etc.)
- `get_platform()` - Get the platform name

#### Bot Information
- `get_self_platform()` - Get the bot's platform name
- `get_self_user_id()` - Get the bot's user ID
- `get_self_account_id()` - Get the bot's account ID (multi-Bot mode)
- `get_self_info()` - Get the complete bot info dictionary

#### Session Identification
- `get_target_id()` - Get the unified target ID (returns `group_id` for group chats, `channel_id` for channels, `user_id` for private chats; takes the first non-empty value in the order group → channel → guild → thread → user)
- `get_session_id()` - Get the unique session identifier, in the format `{platform}:{detail_type}:{target_id}`

### Message Event Methods

#### Message Content
- `get_message()` - Get the message segment array (OneBot12 format)
- `get_alt_message()` - Get the message's alternate text
- `get_text()` - Get the plain text content (alias of `get_alt_message()`)
- `get_message_text()` - Get the plain text content (alias of `get_alt_message()`)

#### Sender Information
- `get_user_id()` - Get the sender's user ID
- `get_user_nickname()` - Get the sender's nickname
- `get_sender()` - Get the complete sender info dictionary

#### Group/Channel Information
- `get_group_id()` - Get the group ID (group messages)
- `get_channel_id()` - Get the channel ID (channel messages)
- `get_guild_id()` - Get the guild ID (guild messages)
- `get_thread_id()` - Get the thread/sub-channel ID (thread messages)

#### @ Mentions
- `has_mention()` - Whether the message @-mentions the bot
- `get_mentions()` - Get the list of all @-mentioned user IDs

### Message Type Checks

#### Basic Checks
- `is_message()` - Whether the event is a message event
- `is_private_message()` - Whether it is a private message
- `is_group_message()` - Whether it is a group message
- `is_at_message()` - Whether it is an @message (alias of `has_mention()`)

### Notice Event Methods

#### Notice Operator
- `get_operator_id()` - Get the operator ID
- `get_operator_nickname()` - Get the operator nickname

#### Notice Type Checks
- `is_notice()` - Whether the event is a notice event
- `is_group_member_increase()` - Group member increase event
- `is_group_member_decrease()` - Group member decrease event
- `is_friend_add()` - Friend addition event (matches `detail_type == "friend_increase"`)
- `is_friend_delete()` - Friend deletion event (matches `detail_type == "friend_decrease"`)

### Request Event Methods

#### Request Information
- `get_comment()` - Get the request comment

#### Request Type Checks
- `is_request()` - Whether the event is a request event
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
        result = await event.approve()    # Approve (with an optional note: approve(comment="Welcome"))
    else:
        result = await event.reject()     # Reject
    if result.get("status") != "ok":
        # Standard response format; on failure, message explains the reason (e.g., 34001 request expired)
        pass

@request.on_group_request()               # Group join request / group invite
async def handle_group(event):
    await event.approve()
```

> Approval actions are executed through the adapter's `Request` DSL; see
> [Request Action Specification](../../standards/request-action-spec.md) for return values, error codes, and adapter implementation requirements. The generic registrar
> `request.on_request()` (which does not distinguish types) is also available.

#### Chain Control (done / is_processed / is_stopped)

- `done(claim=True)` - Claim (default) or only block subsequent lower-priority handlers
- `is_processed()` - Whether the current event has been claimed
- `is_stopped()` - Whether the current event's processing chain has been blocked

For the complete semantics of claiming and blocking (priority interaction, command claiming), see
[Event Handling Basics · Chain Control: Claim and Block](../../getting-started/event-handling.md#chain-control-claim-and-block).

### Reply Features

#### Basic Reply
- `reply(content, method="Text", at_sender=False, quote=False, at_users=None, reply_to=None, at_all=False, via=None, **kwargs)` - General reply method
  - `content`: Content to send (text, URL, etc.)
  - `method`: Send method, default "Text"; options include "Image"/"Voice"/"Video"/"File", etc.
  - `at_sender`: Whether to @ the sender (automatically extracts user_id)
  - `quote`: Whether to quote-reply to the current message (automatically extracts message_id)
  - `at_users`: List of users to @, e.g., `["user1", "user2"]`
  - `reply_to`: Manually specify the message ID to reply to
  - `at_all`: Whether to @ all members
  - `**kwargs`: Extra parameters (e.g., user_id for the Mention method)

- `reply_ob12(message)` - Reply with OneBot12 message segments
  - `message`: OneBot12 message segment list or dict; can be built with MessageBuilder

#### Platform Capability Queries
- `supports(method)` - Check whether the current platform supports a given send method (e.g., `"Image"`, `"Voice"`), returns `bool`
- `available_methods()` - List all available send methods on the current platform, returns a list of method names

#### Forwarding

> **Note**: Forwarding must be implemented through the adapter's Send DSL; the Event wrapper class itself does not provide direct forwarding methods.

```python
# Forward a message to a group
adapter = sdk.adapter.get(event.get_platform())
target_id = event.get_group_id()  # or specify another group ID
await adapter.Send.To("group", target_id).Text(event.get_text())
```

> **Multi-account deployment**: Sending within the chain handling the event **does not require explicitly specifying an account** — the framework injects the account identifier of the triggering event into the call context at the event dispatch entry, and `Send` / `Api` / `Request` chains automatically bind to the triggering event's account when none is explicitly specified (an explicit `Using()` always takes precedence; scenarios without event context, such as timers, fall back to the default account). That is, the forwarding in the example above is sent from "the account that received this event", with no extra code required.

#### Cross-account Duplicate Receipt

When multiple accounts are in the same group, the same physical message may be received once through each account. The framework handles this according to `ErisPulse.framework.cross_account_policy` (default `off`, no correlation):

- `mark`: Subsequent copies are dispatched as usual, but a `multi_receipt` field is injected at the top level of the event (`{"event_id": id of the first received event, "self_id": first receiving account}`) — modules read this field and decide on their own whether to skip responding
- `drop`: Copies are dropped directly at the dispatch entry, transparent to modules

### Wait-for-Reply Features

- `wait_reply(prompt=None, timeout=60.0, callback=None, validator=None, method="Text", pattern=None, regex=None)` - Wait for a user reply
  - `prompt`: Prompt message; if provided, it will be sent to the user
  - `timeout`: Wait timeout in seconds, default 60 seconds
  - `callback`: Callback function, executed when a reply is received
  - `validator`: Validation function used to check whether the reply is valid
  - `method`: Method for sending the prompt message, default "Text"
  - `pattern`: glob wildcard (`*` / `?` / `[seq]`); the reply text must match, otherwise the wait continues
  - `regex`: Regular expression; the reply text must match (`pattern` and `regex` are mutually exclusive), otherwise the wait continues
  - Returns the Event object of the user's reply; returns None on timeout

#### Interaction Methods

- `confirm(prompt=None, timeout=60.0, yes_words=None, no_words=None, method="Text", hint=False)` - Confirmation dialog
  - Returns `True` (confirmed) / `False` (denied) / `None` (timeout)
  - Built-in automatic recognition of Chinese and English confirmation words; custom word sets are supported
  - `method`: Send method, default "Text"; non-text methods such as "Image"/"Markdown" are supported for sending prompts
  - `hint`: Whether to automatically append confirmation word hints at the end of the prompt (e.g., "(yes/no)"), default False

- `choose(prompt, options, timeout=60.0, method="Text", options_format="auto", merge_prompt=False, placeholder="{options}")` - Selection menu
  - `options`: List of option texts
  - Returns the option index (0-based); returns `None` on timeout
  - `method`: Send method, default "Text"; text-based methods (Text/Markdown/md/Html/h5) merge options at the end by default
  - `options_format`: Option format (default: "auto", automatically selects a built-in style based on the method)
    - `"auto"`: Markdown → unordered list (`- 1. Option`), Html → ordered list (`<ol>`), others → plain text list
    - `"list"`: One per line, e.g., ``1. Option A\n2. Option B``
    - `"inline"`: Single-line display, e.g., ``1.A | 2.B``
    - `"md"`: Markdown unordered list
    - `"html"`: Html ordered list
    - `callable`: Custom function that receives ``list[str]`` and returns ``str``
  - `merge_prompt`: Whether to force merging into a single message, default False
    - `False` (default): text-based methods merge automatically; non-text methods send the prompt first, then send the Text options
    - `True`: merge into a single message regardless of the method, sent using the user-specified method
  - `placeholder`: Placeholder where options are inserted, default `{options}`; positions in the prompt containing this marker are replaced with option text; set to an empty string to always append at the end

- `collect(fields, timeout_per_field=60.0)` - Form collection
  - `fields`: List of fields; each item contains `key`, `prompt`, optional `validator`, and optional `method`
  - Returns a `{key: value}` dictionary; returns `None` if any field times out
  - Each field supports a `method` key to specify the send method, e.g., use `{"key": "avatar", "prompt": "Please send an avatar", "method": "Image"}` when collecting images
  - Each field supports an optional `options` key (a list); when provided, the field becomes a multiple-choice question (automatically invoking the choose logic)
  - Each field supports optional `options_format`, `merge_prompt`, and `placeholder` keys to control the option format, message merging behavior, and placeholder

- `wait_for(event_type="message", condition=None, timeout=60.0)` - Wait for any event
  - `condition`: Filter function; a match occurs when it returns `True`
  - Returns the matching Event object; returns `None` on timeout

- `conversation(timeout=60.0)` - Create a multi-turn conversation context
  - Returns a `Conversation` object supporting `say()`/`wait()`/`confirm()`/`choose()`/`collect()`/`stop()`
  - The `is_active` attribute indicates whether the conversation is active

#### Interaction Method Examples

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
choice = await event.choose("Please choose:", ["Cat", "Dog"],
    options_format=lambda opts: " / ".join(opts))
# Output: Cat / Dog

# options_format="auto" (default): automatically selects a built-in style based on the method
# Markdown → unordered list
choice = await event.choose(
    "## Please choose", ["Cat", "Dog"],
    method="Markdown",  # auto is recognized as an md list
)
# Output:
# ## Please choose
# - 1. Cat
# - 2. Dog

# Html → ordered list
choice = await event.choose(
    "<h2>Please choose</h2>", ["Cat", "Dog"],
    method="Html", merge_prompt=True,  # auto is recognized as an html list
)
# Output:
# <h2>Please choose</h2>
# <ol><li>1. Cat</li><li>2. Dog</li></ol>

# Merge mode + placeholder
choice = await event.choose(
    "## Please choose\n{options}\nPlease reply with a number",
    ["Cat", "Dog"],
    method="Markdown", merge_prompt=True,
)

# Custom placeholder
choice = await event.choose(
    "Please choose: [choices]",
    ["Cat", "Dog"],
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

> For the complete usage of Conversation multi-turn dialogues, see [Conversation Multi-turn Dialogue](../../advanced/conversation.md).

### Command Information

#### Command Basics
- `get_command_name()` - Get the command name
- `get_command_args()` - Get the list of command arguments
- `get_command_raw()` - Get the raw command text
- `get_command_info()` - Get the complete command info dictionary
- `is_command()` - Whether the event is a command

### Raw Data

- `get_raw()` - Get the platform's raw event data
- `get_raw_type()` - Get the platform's raw event type

### Platform Extension Methods

Adapters can register platform-specific methods on the Event wrapper class. Methods are only available on Event instances of the corresponding platform; accessing them from other platforms raises an `AttributeError`.

Platform methods take effect through `Event.__getattribute__` with priority over built-in methods, so they can override built-in interaction methods such as `confirm`, `choose`, `collect`, and `wait_reply`, providing platform-specific implementations (e.g., buttons, cards, etc.). Built-in implementations are exported as `_builtin_*` functions for overriders to call.

```python
# Email event - only email methods available
event = Event({"platform": "email", "email_raw": {"subject": "Hello"}})
event.get_subject()      # ✅ returns "Hello"
event.get_chat_type()    # ❌ AttributeError

# Telegram event - only Telegram methods available
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

### Cross-platform Extension (Wildcard)

`register_event_method` and `register_event_mixin` support passing `"*"` as the platform name; registered methods are available on Event instances of **all platforms**. Suitable for features that need cross-platform reuse, such as AI chat and context management.

```python
from ErisPulse.Core.Event.wrapper import register_event_method

@register_event_method("*")
async def ai_chat(self, prompt: str):
    # self is the Event instance; event data and built-in methods are accessible
    await self.reply(f"AI: {prompt}")
```

After registration, event handlers on any platform can call `event.ai_chat(...)`.

Method resolution priority (from high to low): platform-specific methods → wildcard methods → built-in methods → dict key access.

> For how adapter developers can register extension methods, see [Event System API - Cross-platform Extension](../../api-reference/event-system.md#cross-platform-extension-wildcard).

## Related Documentation

### Continue the Module Development Path

- [Getting Started with Module Development](getting-started.md) - Create your first module
- [Module Best Practices](best-practices.md) - Develop high-quality modules

### Going Deeper with Interaction Capabilities

- [Conversation Multi-Turn Dialog](../../advanced/conversation.md) - A complete session engine on top of `wait_reply` (collection, validation, branching)