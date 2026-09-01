# Event Wrapper Class Details

The Event module provides a powerful Event wrapper class that simplifies event handling.

Please directly return the complete translated Markdown content without including any other text.

Once again, please note: If the document contains a language switch line (a line with language names separated by `` | ``), strictly adhere to the format requirements in point 8 above and do not write incorrect formats such as ``[**Label**](file)``.

## Type Annotations for the event Parameter

The `event` parameter of event handlers is an **Event wrapper class** (a subclass of dict). It is highly recommended to add type annotations to it:

```python
from ErisPulse.Core.Event import Event

@message.on_private_message()
async def handler(event: Event):
    text = event.get_text()   # IDE auto-completes all convenient methods
    await event.reply(text)   # Spelling errors can be detected during static checking
```

Without annotations, the IDE cannot recognize methods on Event (`get_text()` / `reply()` / `wait_reply()` / platform extension methods are not suggested), and you can only rely on memory for spelling.

> **Note**: The `event` in event handler callbacks is an **Event wrapper class** (annotated as `Event`); the `event` in module lifecycle methods `on_load` / `on_unload` is a regular **dict** (annotated as `dict`), and these should not be confused.

7. **Important: Path Replacement Rules**
   - Replace `docs/en/` in document links with `docs/en/`
   - For example: `docs/en/quick-start.md` should be changed to `docs/en/quick-start.md`
   - For links pointing to non-current language version files (e.g., `README.xx.md`), keep them unchanged
   - This ensures that links point to the correct language version of the document

## Core Features

- **Full Dictionary Compatibility**: Event inherits from dict
- **Convenient Methods**: Provides a large number of convenient methods
- **Dot-style Access**: Supports accessing event fields using dot notation
- **Backward Compatibility**: All methods are optional

Please directly return the complete translated Markdown content without any additional text.

## Core Field Methods

```python
from ErisPulse.Core.Event import command

@command("info")
async def info_command(event: Event):
    event_id = event.get_id()
    platform = event.get_platform()
    time = event.get_time()
    print(f"ID: {event_id}, Platform: {platform}, Time: {time}")
```

7. **Important: Path Replacement Rules**
   - Replace `docs/en/` with `docs/en/` in document links
   - For example: `docs/en/quick-start.md` should be changed to `docs/en/quick-start.md`
   - For links pointing to non-current language version files (e.g., `README.xx.md` format links), keep them unchanged
   - This ensures links point to the correct language version of the document

## Message Event Methods

```python
from ErisPulse.Core.Event import message

@message.on_private_message()
async def private_handler(event: Event):
    text = event.get_text()
    user_id = event.get_user_id()
    nickname = event.get_user_nickname()
    await event.reply(f"Hello, {nickname}!")
```

7. **Important: Path Replacement Rules**
   - Replace `docs/en/` with `docs/en/` in document links
   - For example: `docs/en/quick-start.md` should be changed to `docs/en/quick-start.md`
   - For links pointing to non-current language version files (such as `README.xx.md` format links), keep them unchanged
   - This ensures links point to the correct language version of the document

## Message Type Detection

```python
from ErisPulse.Core.Event import message

@message.on_group_message()
async def group_handler(event: Event):
    is_private = event.is_private_message()
    is_group = event.is_group_message()
    is_at = event.is_at_message()
    await event.reply(f"Type: {'Private Chat' if is_private else 'Group Chat'}")
```

7. **Important: Path Replacement Rules**
   - Replace `docs/en/` in document links with `docs/en/`
   - For example: `docs/en/quick-start.md` should be changed to `docs/en/quick-start.md`
   - For links pointing to non-current language version files (such as `README.xx.md`), keep them unchanged
   - This ensures that links point to the correct language version of the document

## Reply Functionality

```python
from ErisPulse.Core.Event import command

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
    # The reply must match the regex; otherwise, continue waiting until timeout
    reply = await event.wait_reply(timeout=30, regex=r"\d+\s*元")
    if reply:
        await event.reply(f"Received amount: {reply.get_text()}")
```

## Command Information Retrieval

```python
from ErisPulse.Core.Event import command

@command("cmdinfo")
async def cmdinfo_command(event: Event):
    cmd_name = event.get_command_name()
    cmd_args = event.get_command_args()
    await event.reply(f"Command: {cmd_name}, Arguments: {cmd_args}")
```

7. **Important: Path Replacement Rule**
   - Replace `docs/en/` in document links with `docs/en/`
   - For example: `docs/en/quick-start.md` should be changed to `docs/en/quick-start.md`
   - For links pointing to non-current language version files (e.g., `README.xx.md` format links), keep them unchanged
   - This ensures links point to the correct language version of the document

## Notification Event Methods

```python
from ErisPulse.Core.Event import notice

@notice.on_friend_add()
async def friend_add_handler(event: Event):
    await event.reply("Welcome to add me as a friend!")
```

Please directly return the complete translated Markdown content without any additional text.

Once again, if the document contains language switch lines (where language names are separated by `` | ``), strictly follow the format requirements in item 8 above and do not write incorrect formats like ``[**Label**](file)``.

## Method Quick Reference

### Core Methods

#### Event Basic Information
- `get_id()` - Get event ID
- `get_time()` - Get event timestamp (Unix seconds)
- `get_type()` - Get event type (message/notice/request/meta)
- `get_detail_type()` - Get detailed event type (private/group/friend etc.)
- `get_platform()` - Get platform name

#### Bot Information
- `get_self_platform()` - Get bot platform name
- `get_self_user_id()` - Get bot user ID
- `get_self_account_id()` - Get bot account ID (multi-Bot mode)
- `get_self_info()` - Get complete bot information as dictionary

#### Session Identifiers
- `get_target_id()` - Get unified target ID (returns `group_id` for group chats, `channel_id` for channels, `user_id` for private chats, returns first non-empty value in order: group → channel → guild → thread → user)
- `get_session_id()` - Get unique session identifier, format is `{platform}:{detail_type}:{target_id}`

### Message Event Methods

#### Message Content
- `get_message()` - Get message segments array (OneBot12 format)
- `get_alt_message()` - Get alternative message text
- `get_text()` - Get plain text content (`get_alt_message()` alias)
- `get_message_text()` - Get plain text content (`get_alt_message()` alias)

#### Sender Information
- `get_user_id()` - Get sender user ID
- `get_user_nickname()` - Get sender nickname
- `get_sender()` - Get sender complete information dictionary

#### Group/Channel Information
- `get_group_id()` - Get group ID (group chat messages)
- `get_channel_id()` - Get channel ID (channel messages)
- `get_guild_id()` - Get server ID (server messages)
- `get_thread_id()` - Get topic/subchannel ID (topic messages)

#### @Message Related
- `has_mention()` - Whether message contains @bot
- `get_mentions()` - Get list of all mentioned user IDs

### Message Type Checks

#### Basic Checks
- `is_message()` - Whether event is a message event
- `is_private_message()` - Whether event is a private message
- `is_group_message()` - Whether event is a group message
- `is_at_message()` - Whether event is an @message (`has_mention()` alias)

### Notice Event Methods

#### Operator Information
- `get_operator_id()` - Get operator ID
- `get_operator_nickname()` - Get operator nickname

#### Notice Type Checks
- `is_notice()` - Whether event is a notice event
- `is_group_member_increase()` - Group member increase event
- `is_group_member_decrease()` - Group member decrease event
- `is_friend_add()` - Friend add event (matches `detail_type == "friend_increase"`)
- `is_friend_delete()` - Friend delete event (matches `detail_type == "friend_decrease"`)

### Request Event Methods

#### Request Information
- `get_comment()` - Get request comment

#### Request Type Checks
- `is_request()` - Whether event is a request event
- `is_friend_request()` - Whether event is a friend request
- `is_group_request()` - Whether event is a group request

### Reply Functionality

#### Basic Reply
- `reply(content, method="Text", at_sender=False, quote=False, at_users=None, reply_to=None, at_all=False, via=None, **kwargs)` - General reply method
  - `content`: content to send (text, URL, etc.)
  - `method`: send method, default "Text", optional "Image"/"Voice"/"Video"/"File" etc.
  - `at_sender`: whether to @ sender (automatically extracts user_id)
  - `quote`: whether to quote reply to current message (automatically extracts message_id)
  - `at_users`: list of users to @, e.g. `["user1", "user2"]`
  - `reply_to`: manually specify message ID to reply to
  - `at_all`: whether to @ all members
  - `**kwargs`: additional parameters (e.g. user_id for Mention method)

- `reply_ob12(message)` - Reply using OneBot12 message segments
  - `message`: OneBot12 message segments list or dictionary, can be built with MessageBuilder

#### Platform Capability Query
- `supports(method)` - Check if current platform supports a send method (e.g. `"Image"`, `"Voice"`), returns `bool`
- `available_methods()` - List all available send methods on current platform, returns list of method names

#### Forwarding Functionality

> **Note**: Forwarding functionality needs to be implemented via adapter's Send DSL; Event wrapper class itself does not provide direct forwarding methods.

```python
# Forward message to group
adapter = sdk.adapter.get(event.get_platform())
target_id = event.get_group_id()  # or specify other group ID
await adapter.Send.To("group", target_id).Text(event.get_text())
```

### Wait Reply Functionality

- `wait_reply(prompt=None, timeout=60.0, callback=None, validator=None, method="Text", pattern=None, regex=None)` - Wait for user reply
  - `prompt`: prompt message, if provided will be sent to user
  - `timeout`: timeout in seconds, default 60 seconds
  - `callback`: callback function, executed when reply is received
  - `validator`: validation function, used to validate if reply is valid
  - `method`: send prompt message method, default "Text"
  - `pattern`: glob wildcard (`*` / `?` / `[seq]`), reply text must match, otherwise continue waiting
  - `regex`: regular expression, reply text must match (choose either `pattern` or `regex`), otherwise continue waiting
  - Returns user reply Event object, returns None on timeout

#### Interaction Methods

- `confirm(prompt=None, timeout=60.0, yes_words=None, no_words=None, method="Text", hint=False)` - Confirmation dialog
  - Returns `True` (confirm) / `False` (deny) / `None` (timeout)
  - Built-in Chinese/English confirmation words automatically recognized, custom word sets can be provided
  - `method`: send method, default "Text"; supports "Image"/"Markdown" etc. for non-text prompts
  - `hint`: whether to automatically append confirmation word hint at end of prompt (e.g. "（是/否）"), default False

- `choose(prompt, options, timeout=60.0, method="Text", options_format="auto", merge_prompt=False, placeholder="{options}")` - Choice menu
  - `options`: list of option texts
  - Returns option index (0-based), returns `None` on timeout
  - `method`: send method, default "Text"; text methods (Text/Markdown/md/Html/h5) automatically merge options to end
  - `options_format`: option format (default: "auto", automatically select built-in style based on method)
    - `"auto"`: Markdown→unordered list (`- 1.option`), Html→ordered list (`<ol>`), others→plain text list
    - `"list"`: one per line, e.g. ``1. optionA\n2. optionB``
    - `"inline"`: single line display, e.g. ``1.A | 2.B``
    - `"md"`: Markdown unordered list
    - `"html"`: Html ordered list
    - `callable`: custom function, receives ``list[str]`` and returns ``str``
  - `merge_prompt`: whether to forcibly merge into a single message, default False
    - `False` (default): text methods automatically merge; non-text methods send prompt first then Text options
    - `True`: regardless of method, always merge into a single message, sent with specified method
  - `placeholder`: option insertion placeholder, default `{options}`; if prompt contains this marker, replace it with option text, set to empty string to always append to end

- `collect(fields, timeout_per_field=60.0)` - Form collection
  - `fields`: list of fields, each containing `key`, `prompt`, optional `validator`, optional `method`
  - Returns `{key: value}` dictionary, returns `None` if any field times out
  - Each field supports `method` key to specify send method, e.g. collecting images with `{"key": "avatar", "prompt": "Please send avatar", "method": "Image"}`
  - Each field can have optional `options` key (list), when provided this field becomes a multiple-choice question (automatically calls choose logic)
  - Each field can have optional `options_format`, `merge_prompt`, `placeholder` keys to control option format, message merge behavior, and placeholder

- `wait_for(event_type="message", condition=None, timeout=60.0)` - Wait for any event
  - `condition`: filter function, returns `True` when matched
  - Returns matched Event object, returns `None` on timeout

- `conversation(timeout=60.0)` - Create multi-turn conversation context
  - Returns `Conversation` object, supports `say()`/`wait()`/`confirm()`/`choose()`/`collect()`/`stop()`
  - `is_active` property indicates whether conversation is active

#### Interaction Method Examples

**confirm() - Confirmation dialog:**

```python
@command("delete", help="Delete data")
async def delete_handler(event: Event):
    if await event.confirm("Are you sure to delete all data?"):
        sdk.storage.delete("all_data")
        await event.reply("Data has been deleted")
    else:
        await event.reply("Cancelled")
```

**confirm() - With prompt words:**

```python
# hint=True appends "（是/否）" at end of prompt
if await event.confirm("Continue?", hint=True):
    await event.reply("Continued")
# User sees: Continue?（是/否）
```

**choose() - Choice menu:**

```python
@command("color", help="Choose color")
async def color_handler(event: Event):
    choice = await event.choose("Choose color:", ["Red", "Green", "Blue"])
    if choice is not None:
        colors = ["Red", "Green", "Blue"]
        await event.reply(f"You chose: {colors[choice]}")
```

**choose() - Option formatting and message merging:**

```python
# inline format: options displayed on same line
choice = await event.choose("Choose:", ["A", "B", "C"], options_format="inline")
# Output: 1.A | 2.B | 3.C

# Custom format
choice = await event.choose("Choose:", ["Cat", "Dog"],
    options_format=lambda opts: " / ".join(opts))
# Output: Cat / Dog

# options_format="auto" (default): automatically select built-in style based on method
# Markdown → unordered list
choice = await event.choose(
    "## Choose", ["Cat", "Dog"],
    method="Markdown",  # auto recognizes as md list
)
# Output:
# ## Choose
# - 1. Cat
# - 2. Dog

# Html → ordered list
choice = await event.choose(
    "<h2>Choose</h2>", ["Cat", "Dog"],
    method="Html", merge_prompt=True,  # auto recognizes as html list
)
# Output:
# <h2>Choose</h2>
# <ol><li>1. Cat</li><li>2. Dog</li></ol>

# Merge mode + placeholder
choice = await event.choose(
    "## Choose\n{options}\nReply with number",
    ["Cat", "Dog"],
    method="Markdown", merge_prompt=True,
)

# Custom placeholder
choice = await event.choose(
    "Choose: [choices]",
    ["Cat", "Dog"],
    placeholder="[choices]",
)
```

**collect() - Form collection:**

```python
@command("register", help="Register")
async def register_handler(event: Event):
    data = await event.collect([
        {"key": "name", "prompt": "Please enter name:"},
        {"key": "age", "prompt": "Please enter age:",
         "validator": lambda e: e.get_text().isdigit()},
    ])
    if data:
        await event.reply(f"Registration successful! {data['name']}, {data['age']} years old")
```

**Non-Text method reply:**

```python
await event.reply("http://example.com/img.jpg", method="Image")
await event.reply("http://example.com/audio.mp3", method="Voice")

from ErisPulse.Core.Event import MessageBuilder
segments = MessageBuilder.text("Look at this image:").image("http://example.com/img.jpg").build()
await event.reply_ob12(segments)
```

> For complete usage of Conversation multi-turn dialog, please refer to [Conversation Multi-turn Dialog](../../advanced/conversation.md).

### Command Information

#### Command Basics
- `get_command_name()` - Get command name
- `get_command_args()` - Get command argument list
- `get_command_raw()` - Get raw command text
- `get_command_info()` - Get complete command information as dictionary
- `is_command()` - Whether event is a command

### Raw Data

- `get_raw()` - Get raw platform event data
- `get_raw_type()` - Get raw platform event type

### Platform Extension Methods

Adapters can register platform-specific methods for Event wrapper class. Methods are only available on Event instances of corresponding platforms, and raise `AttributeError` when accessed on other platforms.

Platform methods take precedence over built-in methods via `Event.__getattribute__`, allowing overriding of built-in interactive methods like `confirm`, `choose`, `collect`, `wait_reply` to provide platform-specific features (e.g. buttons, cards). Built-in implementations are exported as `_builtin_*` functions for overriding.

```python
# Email event - only email methods available
event = Event({"platform": "email", "email_raw": {"subject": "Hello"}})
event.get_subject()      # ✅ Returns "Hello"
event.get_chat_type()    # ❌ AttributeError

# Telegram event - only Telegram methods available
event = Event({"platform": "telegram", "telegram_raw": {"chat": {"type": "private"}}})
event.get_chat_type()    # ✅ Returns "private"
event.get_subject()      # ❌ AttributeError

# Built-in methods always available
event.get_text()         # ✅ Any platform
event.reply("hi")        # ✅ Any platform
```

### Query Registered Methods

```python
from ErisPulse.Core.Event import get_platform_event_methods

methods = get_platform_event_methods("email")
# ["get_subject", "get_from", ...]
```

### `hasattr` and `dir` Support

```python
hasattr(event, "get_subject")   # Returns True only when platform="email"
"get_subject" in dir(event)     # Same as above
```

### Cross-platform Extension (Wildcard)

`register_event_method` and `register_event_mixin` support passing `"*"` as platform name, registering methods available on **all platforms**' Event instances. Suitable for cross-platform reusable features such as AI chat, context management.

```python
from ErisPulse.Core.Event.wrapper import register_event_method

@register_event_method("*")
async def ai_chat(self, prompt: str):
    # self is Event instance, can access event data and built-in methods
    await self.reply(f"AI: {prompt}")
```

After registration, any platform's event handler can call `event.ai_chat(...)`.

Method resolution priority (highest to lowest): platform-specific methods → wildcard methods → built-in methods → dictionary key access.

> For adapter developer registration of extension methods, please refer to [Event System API - Cross-platform Extension (Wildcard)](../../api-reference/event-system.md#跨平台扩展通配符).

## Related Documents

- [Getting Started with Module Development](getting-started.md) - Create your first module
- [Best Practices](best-practices.md) - Develop high-quality modules