# Yunhu Platform Feature Documentation

YunhuAdapter is an adapter built based on the Yunhu protocol, integrating all Yunhu functional modules and providing a unified event handling and message operation interface.

---



## Document Information

- Corresponding Module Version: 4.3.0
- Maintainer: ErisPulse


## Basic Information

- Platform Introduction: Yunhu is an enterprise-level instant messaging platform
- Adapter Name: YunhuAdapter
- Multi-account Support: Supports identifying and configuring multiple Yunhu robot accounts through bot_id
- Chainable Modifier Support: Supports chainable modifier methods such as `.Reply()`
- OneBot12 Compatibility: Supports sending OneBot12 formatted messages

For documentation links, replace `docs/en/` with `docs/en/`.

## Supported Message Sending Types

All sending methods are implemented through a fluent syntax, for example:

```python
from ErisPulse.Core import adapter
yunhu = adapter.get("yunhu")

await yunhu.Send.To("user", user_id).Text("Hello World!")
```

The supported sending types include:
- `.Text(text: str)`: Send plain text messages.
- `.Html(html: str)`: Send HTML formatted messages.
- `.Markdown(markdown: str)`: Send Markdown formatted messages.
- `.A2UI(text: str)`: Send A2UI formatted messages.
- `.Image(file: bytes, stream: bool = False, filename: str = None)`: Send image messages, supporting streaming upload and custom file names.
- `.Video(file: bytes, stream: bool = False, filename: str = None)`: Send video messages, supporting streaming upload and custom file names.
- `.File(file: bytes, stream: bool = False, filename: str = None)`: Send file messages, supporting streaming upload and custom file names.
- `.Batch(target_ids: List[str], message: str, content_type: str = "text", **kwargs)`: Batch send messages.
- `.Edit(msg_id: str, text: str, content_type: str = "text", buttons: List = None)`: Edit existing messages.
- `.Recall(msg_id: str)`: Recall messages.
- `.Board(content: str, content_type: str = "text")`: Publish announcement boards. The scope is inferred by `To()` (specifying a target = local board, not specifying = global board). Fluent modifiers: `.Expire(duration)` for relative expiration (in seconds), `.ExpireAt(timestamp)` for absolute expiration (in second-level timestamps), `.ForMember(member_id)` for group member boards; **automatically converts to recall board when content is empty**. Still compatible with old-style `Board("local", "announcement")` explicit scope syntax.
- `.DismissBoard()`: Recall announcement boards. The scope is also inferred by `To()`, supports `.ForMember(member_id)`; still compatible with old-style `DismissBoard("local")` syntax.
- `.Stream(content_type: str, content_generator: AsyncGenerator, **kwargs)`: Send streaming messages.

### Group Management Methods

All group management methods require specifying the group through fluent syntax, for example:
```python
from ErisPulse.Core import adapter
yunhu = adapter.get("yunhu")

await yunhu.Send.To("group", group_id).Kick(user_id)
```

- `.Kick(user_id: str)`: Remove a group member. The bot needs the `Allow Remove Group Member` permission.
- `.Ban(user_id: str, duration: int = 600)`: Mute a user. `duration` is the mute duration (in seconds), 0 means unmute, -1 means permanent mute. The bot needs the `Allow Mute Users` permission.
- `.CreateTag(tag: str, color: str = None, desc: str = None, sort: int = None)`: Create a group tag. `color` format is #RRGGBB, `sort` smaller values appear earlier. The bot needs the `Allow Control Tag Group` permission.
- `.EditTag(tag: str, new_tag: str = None, color: str = None, desc: str = None, sort: int = None)`: Edit a group tag. Each parameter is optional, not provided means no modification. The bot needs the `Allow Control Tag Group` permission.
- `.DeleteTag(tag: str)`: Delete a group tag. The bot needs the `Allow Control Tag Group` permission.
- `.GetTagList()`: Get the group tag list. Returns response data containing a `list` array.
- `.AddUserTag(user_id: str, tag: str)`: Add a tag to a user. The bot needs the `Allow Control Tag Group` permission.
- `.RemoveUserTag(user_id: str, tag: str)`: Remove a tag from a user. The bot needs the `Allow Control Tag Group` permission.
- `.SetMsgTypeLimit(types: str)`: Control message types within the group. `types` is a comma-separated string of message type names (e.g., `"text,image,video"`), an empty string means no restriction. The bot needs the `Allow Modify Group Info` permission.

### Message Query Methods

Retrieve the historical message list of a specified session (user/group), requiring specifying the target through fluent syntax, for example:
```python
from ErisPulse.Core import adapter
yunhu = adapter.get("yunhu")

result = await yunhu.Send.To("group", group_id).GetMessages(before=10)
```

- `.GetMessages(message_id: str = None, before: int = None, after: int = None)`: Retrieve session history messages. Returns response data containing a `list` array and `total` count.
  - `message_id`: Message ID (optional). When not provided, combined with `before` returns the most recent N messages.
  - `before`: Returns N messages before the specified message ID.
  - `after`: Returns N messages after the specified message ID.
  - > **Note:** At least one of `before` and `after` must be specified and greater than 0, otherwise the server will not return any messages.

The board scope is automatically inferred by `To()`:
- Specifying `To(target_type, target_id)` → local board (specific user/group)
- Not specifying `To()` → global board

```python
# Local board (expires relatively after 60 seconds)
await yunhu.Send.To("group", group_id).Expire(60).Board("Announcement", content_type="markdown")

# Group member board (visible only to specified member)
await yunhu.Send.To("group", group_id).ForMember(user_id).Board("Visible only to you")

# Absolute timestamp expiration
await yunhu.Send.To("group", group_id).ExpireAt(1785208268).Board("Expires at specified time")

# Global board
await yunhu.Send.Board("Global Announcement")

# Clear local board (empty content → automatically revoked)
await yunhu.Send.To("group", group_id).Board("")
```

### Button Parameter Description

The `buttons` parameter is a nested list representing the layout and functionality of buttons. Each button object contains the following fields:

| Field        | Type   | Required | Description                                                                 |
|--------------|--------|----------|-----------------------------------------------------------------------------|
| `text`       | string | Yes      | Text on the button                                                          |
| `actionType` | int    | Yes      | Action type:<br>`1`: Navigate URL<br>`2`: Copy<br>`3`: Report on click       |
| `url`        | string | No       | Used when `actionType=1`, representing the target URL for navigation        |
| `value`      | string | No       | When `actionType=2`, this value will be copied to the clipboard<br>When `actionType=3`, this value will be sent to the subscriber |

Example:
```python
buttons = [
    [
        {"text": "Copy", "actionType": 2, "value": "xxxx"},
        {"text": "Click to Navigate", "actionType": 1, "url": "http://www.baidu.com"},
        {"text": "Report Event", "actionType": 3, "value": "xxxxx"}
    ]
]
await yunhu.Send.To("user", user_id).Buttons(buttons).Text("Message with buttons")
```
> **Note:**
> - Only when the user clicks the **report event** button will a push be received; **copy** and **navigate URL** actions will not trigger a push.

### Fluent Modifier Methods (Combinable)

Fluent modifier methods return `self`, supporting fluent calls, and must be called before the final sending method:

- `.Reply(message_id: str)`: Reply to a specified message.
- `.At(user_id: str)`: Mention a specified user.
- `.AtAll()`: Mention everyone.
- `.Buttons(buttons: List)`: Add buttons.

### Fluent Call Examples

```python
# Basic sending
await yunhu.Send.To("user", user_id).Text("Hello")

# Reply to a message
await yunhu.Send.To("group", group_id).Reply(msg_id).Text("Reply message")

# Reply + buttons
await yunhu.Send.To("group", group_id).Reply(msg_id).Buttons(buttons).Text("Message with reply and buttons")
```

### Group Management Examples

```python
from ErisPulse.Core import adapter
yunhu = adapter.get("yunhu")

# Remove a group member
await yunhu.Send.To("group", group_id).Kick(user_id)

# Mute a user (10 minutes)
await yunhu.Send.To("group", group_id).Ban(user_id, duration=600)

# Unmute
await yunhu.Send.To("group", group_id).Ban(user_id, duration=0)

# Permanent mute
await yunhu.Send.To("group", group_id).Ban(user_id, duration=-1)

# Create a group tag
await yunhu.Send.To("group", group_id).CreateTag("VIP User", color="#FF5733", desc="VIP Member")

# Edit a group tag
await yunhu.Send.To("group", group_id).EditTag("VIP User", new_tag="SVIP User", color="#33C4FF")

# Delete a group tag
await yunhu.Send.To("group", group_id).DeleteTag("VIP User")

# Get group tag list
result = await yunhu.Send.To("group", group_id).GetTagList()

# Add a tag to a user
await yunhu.Send.To("group", group_id).AddUserTag(user_id, "VIP User")

# Remove a tag from a user
await yunhu.Send.To("group", group_id).RemoveUserTag(user_id, "VIP User")

# Set message type limit
await yunhu.Send.To("group", group_id).SetMsgTypeLimit("text,image,video")

# Remove message type limit
await yunhu.Send.To("group", group_id).SetMsgTypeLimit("")
```

### Message Query Examples

```python
from ErisPulse.Core import adapter
yunhu = adapter.get("yunhu")

# Get the last 10 messages in the group (returns 10 messages total)
result = await yunhu.Send.To("group", group_id).GetMessages(before=10)

# Get 10 messages before a specified message ID in the group (returns 11 messages total)
result = await yunhu.Send.To("group", group_id).GetMessages(message_id="msg_xxx", before=10)

# Get 10 messages before and after a specified message ID in the group (returns 21 messages total)
result = await yunhu.Send.To("group", group_id).GetMessages(message_id="msg_xxx", before=10, after=10)

# Get historical messages in a user session
result = await yunhu.Send.To("user", user_id).GetMessages(message_id="msg_xxx", before=10)
```

### OneBot12 Message Support

The adapter supports sending OneBot12 formatted messages, facilitating cross-platform message compatibility:

- `.Raw_ob12(message: List[Dict], **kwargs)`: Send OneBot12 formatted messages.

```python
# Send OneBot12 formatted message
ob12_msg = [{"type": "text", "data": {"text": "Hello"}}]
await yunhu.Send.To("user", user_id).Raw_ob12(ob12_msg)

# Combined with fluent modifiers
ob12_msg = [{"type": "text", "data": {"text": "Reply message"}}]
await yunhu.Send.To("group", group_id).Reply(msg_id).Raw_ob12(ob12_msg)

## Standard API Actions (ApiDSL)

> [!NOTE]
> This feature requires ErisPulse **2.7.0+** and YunhuAdapter **4.3.0+**.

In addition to the `Send` chainable sending, the adapter also provides the `Api` inner class, exposing OneBot12 standard API actions and Yunhu platform extension actions. All methods return a standard response format.

```python
from ErisPulse.Core import adapter
yunhu = adapter.get("yunhu")

# Information queries (via public Web API, no authentication required)
result = await yunhu.Api.get_self_info()              # Robot self information
result = await yunhu.Api.get_user_info("7058262")     # Any user information
result = await yunhu.Api.get_group_info("635409929")  # Group information

# File operations
result = await yunhu.Api.upload_file(type="path", name="a.png", path="./a.png")
result = await yunhu.Api.get_file("https://chat-file.jwznb.com/xxx")

# Recall message (requires additional chat_id + chat_type)
await yunhu.Api.delete_message("msg_id", chat_id="123", chat_type="group")

# Multiple accounts: specify Bot account
info = await yunhu.Api.Using("bot1").get_self_info()
```

### Supported Standard Actions

| Method | Description | Data Source |
|------|------|---------|
| `get_self_info()` | Robot self information | Public Web API (bot-info) |
| `get_user_info(user_id)` | User information (any user can query) | Public Web API (user/homepage) |
| `get_group_info(group_id)` | Group information | Public Web API (group-info) |
| `upload_file(*, type, name, ...)` | Upload file (automatically determines image/video/file) | Bot open API |
| `get_file(file_id)` | Get file (file_id is the URL) | — |
| `delete_message(message_id, *, chat_id, chat_type)` | Recall message | Bot open API (/bot/recall) |

> **Note**: `get_self_info` / `get_user_info` / `get_group_info` are implemented via **unofficial public Web API** (chat-web-go.jwzhd.com). These interfaces require no authentication but are not officially documented and may change with platform updates; failure returns a standard error response.

### Unsupported Standard Actions

The following standard actions have no corresponding API in Yunhu, and calling them returns `retcode=10002` (unsupported operation):
- `get_friend_list` (The "robot user list" of Bot open API is still pending launch)
- `get_group_list` / `get_group_member_info` / `get_group_member_list`
- `set_group_name` / `leave_group`

### Platform Extension Actions

Call Yunhu-specific actions via `Api.call("yunhu.xxx", **params)` (parameters use OB12-style naming, adapter automatically translates them to Yunhu fields):

| Extension Action | Description | Equivalent Send Method |
|---------|------|---------------|
| `yunhu.recall` | Recall message (msg_id, chat_id, chat_type) | `Send.To(...).Recall(msg_id)` |
| `yunhu.kick` | Remove group member (group_id, user_id) | `Send.To("group", g).Kick(uid)` |
| `yunhu.ban` | Mute (group_id, user_id, duration) | `Send.To("group", g).Ban(uid, duration)` |
| `yunhu.unban` | Unmute (group_id, user_id) | `Send.To("group", g).Ban(uid, duration=0)` |
| `yunhu.tag.create/edit/delete/list` | Group tag CRUD (group_id, ...) | `Send.To("group", g).CreateTag(...)` etc. |
| `yunhu.tag.relate` / `yunhu.tag.relate_cancel` | Add/remove tags to/from users | `Send.To("group", g).AddUserTag(...)` etc. |
| `yunhu.set_member_title` / `yunhu.unset_member_title` | **Member title semantic alias** (tag ≈ title, internally mapped to tag.relate) | — |
| `yunhu.msg_type_limit` | Group message type limit (group_id, type) | `Send.To("group", g).SetMsgTypeLimit(...)` |
| `yunhu.get_messages` | Get historical messages (chat_id, chat_type, message_id?, before?, after?) | `Send.To(...).GetMessages(...)` |
| `yunhu.bot_info` | Public bot-info query (bot_id) | — |
| `yunhu.user_homepage` | Public user homepage query (user_id) | — |

```python
# Platform extension example
await yunhu.Api.call("yunhu.kick", group_id="123", user_id="456")
await yunhu.Api.call("yunhu.set_member_title", group_id="123", user_id="456", title="VIP")
result = await yunhu.Api.call("yunhu.get_messages", chat_id="123", chat_type="group", before=10)
```

> **Tags and Titles**: Yunhu's "tag" semantics are equivalent to OneBot12 group member `title`. `yunhu.set_member_title` is a native semantic alias of `yunhu.tag.relate`, both internally mapped to the same endpoint. In group message events, the sender's role is mapped from `senderUserLevel` to the standard `role` field (owner/admin/member).

## Return Values of Send Methods

All send methods return a Task object, which can be awaited directly to obtain the send result. The returned result follows the ErisPulse adapter's standardized return specification:

```python
{
    "status": "ok",           // Execution status
    "retcode": 0,             // Return code
    "data": {...},            // Response data
    "self": {...},            // Self information (including bot_id)
    "message_id": "123456",   // Message ID
    "message": "",            // Error message
    "yunhu_raw": {...}        // Raw response data
}
```



## Unique Event Types

Use platform=="yunhu" to detect and use platform-specific features

### Core Differences

1. Unique event types:
    - Form (e.g. form command): yunhu_form
    - Expression pack/sticker message segment: yunhu_expression
    - Button click: yunhu_button_click
    - A2UI button click: yunhu_a2ui_button
    - Robot settings: yunhu_bot_setting
    - Quick menu: yunhu_shortcut_menu
2. Standard field extension (4.3.0+):
    - Message events add standard `role` field (mapped from Yunhu `senderUserLevel` to `owner`/`admin`/`member`)
    - New `user_avatar` field (sender's avatar URL)
3. Extended fields:
    - All unique fields are prefixed with yunhu_
    - Original data is retained in yunhu_raw field
    - In private chat, self.user_id represents the bot ID

### Example of Special Fields

```python
# Form command
{
  "type": "message",
  "detail_type": "private",
  "yunhu_command": {
    "name": "Form command name",
    "id": "Command ID",
    "form": {
      "fieldID1": {
        "id": "fieldID1",
        "type": "input/textarea/select/radio/checkbox/switch",
        "label": "Field label",
        "value": "Field value"
      }
    }
  }
}

# Button event
{
  "type": "notice",
  "detail_type": "yunhu_button_click",
  "user_id": "User ID who clicked the button",
  "user_nickname": "User nickname",
  "message_id": "Message ID",
  "yunhu_button": {
    "id": "Button ID (may be empty)",
    "value": "Button value"
  }
}

# A2UI button event
{
  "type": "notice",
  "detail_type": "yunhu_a2ui_button",
  "user_id": "Operator user ID",
  "user_nickname": "User nickname",
  "message_id": "Message ID",
  "yunhu_a2ui": {
    "recv_id": "Recipient ID",
    "recv_type": "Recipient type",
    "action_name": "Action name",
    "source_component_id": "Source component ID",
    "form_context": {},
    "interaction_json": "JSON string of interaction data"
  }
}

### Example of Button Click Event Handling

```python
from ErisPulse.Core.Event import notice

@notice.on_notice()
async def handle_yunhu_notice(event):
    """Handle Yunhu notification events

    Use the generic on_notice() decorator to handle all notification events,
    then distinguish different types of notifications by detail_type
    event.reply() will automatically reply through the Yunhu platform
    """

# Check if it is a button click event
    if event.get("detail_type") == "yunhu_button_click":
        user_id = event.get_user_id()
        user_nickname = event.get_user_nickname()
        button_value = event.get("yunhu_button", {}).get("value", "")

        print(f"User {user_nickname}({user_id}) clicked the button: {button_value}")

# Auto reply using event.reply() (will automatically select the correct sending method based on the platform)
        if button_value == "confirm":
            await event.reply("You clicked the confirm button!")
        elif button_value == "cancel":
            await event.reply("The operation has been cancelled")
        else:
            await event.reply(f"Received your selection: {button_value}")



# Handling Quick Menu Events
    elif event.get("detail_type") == "yunhu_shortcut_menu":
        menu_id = event.get("yunhu_menu", {}).get("id", "")
        await event.reply(f"Triggered quick menu: {menu_id}")

# Handling Robot Setting Changes
    elif event.get("detail_type") == "yunhu_bot_setting":
        settings = event.get("yunhu_setting", {})
        await event.reply(f"Settings have been updated: {settings}")



# Handling A2UI Button Events
    elif event.get("detail_type") == "yunhu_a2ui_button":
        a2ui = event.get("yunhu_a2ui", {})
        action_name = a2ui.get("action_name", "")
        form_context = a2ui.get("form_context", {})
        await event.reply(f"A2UI Action: {action_name}, Form Data: {form_context}")
```

### Sending a Message with Buttons Using Chained Calls

```python
from ErisPulse import sdk

yunhu = sdk.adapter.get("yunhu")

buttons = [
    [
        {"text": "Confirm", "actionType": 3, "value": "confirm"},
        {"text": "Cancel", "actionType": 3, "value": "cancel"},
        {"text": "View Details", "actionType": 1, "url": "http://example.com/detail"}
    ]
]

# Send a Message with Buttons to a Group
await yunhu.Send.To("group", "123456").Buttons(buttons).Text("Please confirm the following operation")



# Send a Message with Buttons to User's Private Chat
await yunhu.Send.To("user", "789").Buttons(buttons).Text("Please select your preference settings")

### Send A2UI Message

```python
from ErisPulse import sdk

yunhu = sdk.adapter.get("yunhu")

# Send A2UI Message
await yunhu.Send.To("user", user_id).A2UI("A2UI interactive card content")
```

# Robot Settings
{
  "type": "notice",
  "detail_type": "yunhu_bot_setting",
  "group_id": "Group ID (may be empty)",
  "user_nickname": "User nickname",
  "yunhu_setting": {
    "Setting Item ID": {
      "id": "Setting Item ID",
      "type": "input/radio/checkbox/select/switch",
      "value": "Setting value"
    }
  }
}

# Quick Menu
{
  "type": "notice",
  "detail_type": "yunhu_shortcut_menu",
  "user_id": "User ID who triggered the menu",
  "user_nickname": "User nickname",
  "group_id": "Group ID (if in group chat)",
  "yunhu_menu": {
    "id": "Menu ID",
    "type": "Menu type (integer)",
    "action": "Menu action (integer)"
  }
}

## Event Mixin Extension Methods

The adapter registers the following platform-specific methods, which are only available when `platform == "yunhu"`:

| Method | Return Type | Description |
|--------|-------------|-------------|
| `get_raw_event()` | `dict` | Get raw Yunhu event data (`yunhu_raw`) |
| `get_sender_level()` | `str` | Sender's native Yunhu level (owner/administrator/member/unknown) |
| `get_sender_role()` | `str` | Sender's OneBot12 standard role (owner/admin/member) |
| `get_sender_title()` | `str` | Sender's title (standard `title` field accessor, reserved) |
| `get_sender_avatar()` | `str` | Sender's avatar URL |
| `get_command()` | `dict` | Command data (only for command message events, `yunhu_command`) |
| `get_button_value()` | `str` | The value from a button click event (`yunhu_button.value`) |
| `get_a2ui_action()` | `str` | The actionName from an A2UI button event |
| `get_a2ui_form_context()` | `dict` | The form context from an A2UI button event |
| `get_menu_id()` | `str` | The ID from a shortcut menu event (`yunhu_menu.id`) |
| `get_setting()` | `dict` | The setting data from a robot setting event (`yunhu_setting`) |
| `is_command_message()` | `bool` | Whether the event is a command message |
| `is_button_click()` | `bool` | Whether the event is a button click event |
| `is_a2ui_button()` | `bool` | Whether the event is an A2UI button event |

```python
from ErisPulse.Core.Event import notice

@notice.on_notice()
async def handle_yunhu_notice(event):
    if event.get("platform") != "yunhu":
        return

    if event.is_button_click():
        value = event.get_button_value()
        await event.reply(f"You clicked the button: {value}")

    if event.get("detail_type") == "yunhu_shortcut_menu":
        menu_id = event.get_menu_id()

## Extension Field Description

- All unique fields are prefixed with `yunhu_` to avoid conflicts with standard fields
- The original data is retained in the `yunhu_raw` field, which allows access to the complete raw data from the YUNHU platform
- `self.user_id` represents the bot ID (obtained from the bot_id in the configuration)
- Form instructions are provided as structured data through the `yunhu_command` field
- Button click events are provided with button-related information through the `yunhu_button` field
- A2UI button events are provided with A2UI interaction-related information through the `yunhu_a2ui` field
- Bot setting changes are provided with setting item data through the `yunhu_setting` field
- Quick menu operations are provided with menu-related information through the `yunhu_menu` field
- Emoji/Sticker messages are provided with sticker data (sticker_id, sticker pack ID, image size, etc.) through the `yunhu_expression` message segment

### Emoji/Sticker Message Segment (yunhu_expression)

When a user sends an emoji or sticker, the message segment type is `yunhu_expression`:

```json
{
  "type": "yunhu_expression",
  "data": {
    "sticker_id": "35154",
    "sticker_pack_id": "1670",
    "expression_id": "0",
    "image_name": "sticker/fabb9077f2ba302402ea871cab3686ad7a3fc52c.gif",
    "width": 500,
    "height": 500
  }
}
```

| Field | Type | Description |
|-------|------|-------------|
| `sticker_id` | string | Unique identifier for the sticker |
| `sticker_pack_id` | string | Sticker pack ID |
| `expression_id` | string | Expression ID |
| `image_name` | string | File path to the expression image |
| `width` | int | Image width (optional) |
| `height` | int | Image height (optional) |

Example usage:
```python
from ErisPulse.Core.Event import message

@message.on_message()
async def handle_message(event):
    if event.get_platform() == "yunhu":
        for segment in event.get("message", []):
            if segment.get("type") == "yunhu_expression":
                data = segment["data"]
                print(f"Received sticker: sticker_id={data['sticker_id']}, pack ID={data['sticker_pack_id']}")

## Multi-Bot Configuration

### Configuration Description

The Yunhu Adapter supports configuring and running multiple Yunhu bot accounts simultaneously.

```toml
# config.toml
[Yunhu_Adapter.accounts.bot1]
token = "your_bot1_token"  # Bot token (required)
mode = "ws"  # Receive mode (optional, default "ws", options: "ws", "webhook")
webhook_path = "/webhook/bot1"  # Webhook path (optional, default "/webhook")
enabled = true  # Whether to enable (optional, default true)

[Yunhu_Adapter.accounts.bot2]
token = "your_bot2_token"  # Second bot's token
webhook_path = "/webhook/bot2"  # Separate webhook path
enabled = true
```

**Configuration Item Description:**
- `token`: API token provided by the Yunhu platform (required)
- `mode`: Receive mode (optional, default `"ws"`, options `"ws"`, `"webhook"`)
- `webhook_path`: HTTP path for receiving Yunhu events (optional, default `"/webhook"`, only used in webhook mode)
- `enabled`: Whether to enable this account (optional, default true)

**Important Notes:**
1. The Yunhu platform's bot ID is automatically detected at **runtime** and does not need to be specified in the configuration.
2. In webhook mode, each bot should have its own `webhook_path` to receive its respective webhook events.
3. When configuring webhooks on the Yunhu platform, please set the corresponding URL for each bot, for example:
   - Bot1: `https://your-domain.com/webhook/bot1`
   - Bot2: `https://your-domain.com/webhook/bot2`

### Using Send DSL to Specify Bot

You can specify which bot to use for sending messages via the `Using()` method. This method supports two types of parameters:
- **Account name**: The bot name in the configuration (e.g., `bot1`, `bot2`)
- **bot_id**: The `bot_id` value in the configuration

```python
from ErisPulse.Core import adapter
yunhu = adapter.get("yunhu")

# Send message using account name
await yunhu.Send.Using("bot1").To("user", "user123").Text("Hello from bot1!")

# Send message using bot_id (automatically matches the corresponding account)
await yunhu.Send.Using("30535459").To("group", "group456").Text("Hello from bot!")

# Use the first enabled bot if not specified
await yunhu.Send.To("user", "user123").Text("Hello from default bot!")
```

> **Tip:** When using `bot_id`, the system automatically finds the matching account in the configuration. This is especially useful when handling event responses, where you can directly use `event["self"]["user_id"]` to reply to the same account.

### Bot Identification in Events

Received events automatically include the corresponding `bot_id` information:

```python
from ErisPulse.Core.Event import message

@message.on_message()
async def handle_message(event):
    if event["platform"] == "yunhu":
        # Get the bot ID that triggered the event
        bot_id = event["self"]["user_id"]
        print(f"Message received from Bot: {bot_id}")
        
        # Reply using the same bot
        yunhu = adapter.get("yunhu")
        await yunhu.Send.Using(bot_id).To(
            event["detail_type"],
            event["user_id"] if event["detail_type"] == "private" else event["group_id"]
        ).Text("Reply message")
```

### Log Information

The adapter automatically includes `bot_id` information in the logs, which is helpful for debugging and tracking:

```
[INFO] [yunhu] [bot:30535459] Received private message from user user123
[INFO] [yunhu] [bot:12345678] Message sent successfully, message_id: abc123
```

### Management Interface

```python
# Get all account information
bots = yunhu.bots

# Check if an account is enabled
bot_status = {
    bot_name: bot_config.enabled
    for bot_name, bot_config in yunhu.bots.items()
}

# Dynamically enable/disable accounts (requires adapter restart)
yunhu.bots["bot1"].enabled = False
```

### Legacy Configuration Compatibility

Legacy `[Yunhu_Adapter.bots.*]` configuration (including the `bot_id` field) will be automatically migrated to the `accounts` format (`bot_id` is now automatically detected at runtime, and values in the configuration will be ignored); it is recommended to migrate to the new format as soon as possible.