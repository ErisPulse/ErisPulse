# Yunhu Platform Feature Documentation

YunhuAdapter is an adapter built based on the Yunhu protocol, integrating all Yunhu functional modules and providing a unified interface for event handling and message operations.

---

## Documentation Information

- Corresponding Module Version: 4.4.0
- Maintainer: ErisPulse

## Basic Information

- Platform Introduction: Yunhu is an enterprise-grade instant messaging platform.
- Adapter Name: YunhuAdapter
- Multi-account Support: Supports identifying and configuring multiple Yunhu bot accounts via `bot_id`.
- Chained Modifier Support: Supports chained modifier methods such as `.Reply()`.
- OneBot12 Compatibility: Supports sending messages in the OneBot12 format.

## v5 Paradigm Update (4.4.0)

This adapter has completed alignment with the v5 paradigm (incremental upgrade, API compatible):

- **Official Server API Suite** (Api DSL extension methods): Edit message, batch send, message list, user/global dashboard, mute group members, remove group members, group message type control, group tag CRUD, user tagging
- **Standard keyboard segment** (cross-platform interaction component standard): {"type": "keyboard", "data": {"rows": [[{"label", "type": "callback|link", "data"}]]}} segment automatically converted to Yunhu buttons; .Buttons(rows) / .Keyboard(rows) decorators accept generic structure (native structure is backward compatible)
- **Standard interaction callback fields**: Button click/A2UI events include standard fields interaction_id / button_data
- **spawn_background task ownership**: WS connection tasks now use runtime.spawn_background
- **Framework soft dependencies**: Runtime detection of ErisPulse>=2.7.1 with prompts; version logs output on startup

### Platform Extension Actions (call / Api Methods)

```python
from ErisPulse import sdk
yunhu = sdk.adapter.get("yunhu")

# Api Methods (Official Server API)
await yunhu.Api.edit_message(msg_id, recv_id, "group", "text", {"text": "New Content"})
await yunhu.Api.batch_send(["userId1", "userId2"], "text", {"text": "Announcement"})
await yunhu.Api.get_message_list(group_id, "group", before=10)
await yunhu.Api.set_user_board(chat_id, "group", "Dashboard Content", expire_time=3600)
await yunhu.Api.dismiss_global_board()
await yunhu.Api.gag_group_member(group_id, user_id, 600)      # Mute for 600 seconds, 0 = unmute
await yunhu.Api.remove_group_member(group_id, user_id)
await yunhu.Api.set_group_msg_type_limit(group_id, "text,image")
await yunhu.Api.create_group_tag(group_id, "VIP", color="#FF5733")
await yunhu.Api.add_user_tag(group_id, user_id, "VIP")

# Button Click Callback (Standard Fields)
from ErisPulse.Core.Event import notice

@notice.on_notice()
async def handle_button(event):
    if event.get("platform") == "yunhu" and event.get("button_data"):
        data = event["button_data"]     # Cross-platform unified field access
        interaction_id = event["interaction_id"]
```

> Complete standard documentation available at [Cross-Platform Interaction Component Standard](../../standards/standardization-guide.md).

## Supported Message Sending Types

All sending methods are implemented through a fluent syntax, for example:
```python
from ErisPulse.Core import adapter
yunhu = adapter.get("yunhu")

await yunhu.Send.To("user", user_id).Text("Hello World!")
```

The supported sending types include:
- `.Text(text: str)`: Sends a plain text message.
- `.Html(html: str)`: Sends an HTML formatted message.
- `.Markdown(markdown: str)`: Sends a Markdown formatted message.
- `.A2UI(text: str)`: Sends an A2UI formatted message.
- `.Image(file: bytes, stream: bool = False, filename: str = None)`: Sends an image message, supporting streaming upload and custom file names.
- `.Video(file: bytes, stream: bool = False, filename: str = None)`: Sends a video message, supporting streaming upload and custom file names.
- `.File(file: bytes, stream: bool = False, filename: str = None)`: Sends a file message, supporting streaming upload and custom file names.
- `.Batch(target_ids: List[str], message: str, content_type: str = "text", **kwargs)`: Sends messages in batch.
- `.Edit(msg_id: str, text: str, content_type: str = "text", buttons: List = None)`: Edits an existing message.
- `.Recall(msg_id: str)`: Recalls a message.
- `.Board(content: str, content_type: str = "text")`: Publishes an announcement board. The scope is inferred by `To()` (specifying target = local board, not specifying = global board). Fluent modifiers: `.Expire(duration)` for relative expiration (seconds), `.ExpireAt(timestamp)` for absolute expiration (second-level timestamp), `.ForMember(member_id)` for group member board; **automatically reverts to a revoke board when content is empty**. Still compatible with the old-style `Board("local", "announcement")` explicit scope syntax.
- `.DismissBoard()`: Revokes an announcement board. The scope is still inferred by `To()`, supports `.ForMember(member_id)`; still compatible with the old-style `DismissBoard("local")` syntax.
- `.Stream(content_type: str, content_generator: AsyncGenerator, **kwargs)`: Sends a stream message.

### Group Management Methods

All group management methods require specifying the group through fluent syntax, for example:
```python
from ErisPulse.Core import adapter
yunhu = adapter.get("yunhu")

await yunhu.Send.To("group", group_id).Kick(user_id)
```

- `.Kick(user_id: str)`: Removes a group member. The bot needs the `Allow Remove Group Member` permission.
- `.Ban(user_id: str, duration: int = 600)`: Mutes a user. `duration` is the mute duration (in seconds), 0 means unmute, -1 means permanent mute. The bot needs the `Allow Mute User` permission.
- `.CreateTag(tag: str, color: str = None, desc: str = None, sort: int = None)`: Creates a group tag. `color` format is #RRGGBB, `sort`越小越靠前. The bot needs the `Allow Control Tag Group` permission.
- `.EditTag(tag: str, new_tag: str = None, color: str = None, desc: str = None, sort: int = None)`: Edits a group tag. Parameters are optional, not passed means no modification. The bot needs the `Allow Control Tag Group` permission.
- `.DeleteTag(tag: str)`: Deletes a group tag. The bot needs the `Allow Control Tag Group` permission.
- `.GetTagList()`: Retrieves the group tag list. Returns a response containing a `list` array.
- `.AddUserTag(user_id: str, tag: str)`: Adds a tag to a user. The bot needs the `Allow Control Tag Group` permission.
- `.RemoveUserTag(user_id: str, tag: str)`: Removes a tag from a user. The bot needs the `Allow Control Tag Group` permission.
- `.SetMsgTypeLimit(types: str)`: Controls message types within the group. `types` is a comma-separated string of message type names (e.g., `"text,image,video"`), an empty string means no restriction. The bot needs the `Allow Modify Group Info` permission.

### Message Query Methods

To retrieve the history message list of a specified session (user/group), you need to specify the target through fluent syntax, for example:
```python
from ErisPulse.Core import adapter
yunhu = adapter.get("yunhu")

result = await yunhu.Send.To("group", group_id).GetMessages(before=10)
```

- `.GetMessages(message_id: str = None, before: int = None, after: int = None)`: Retrieves the session's history messages. Returns a response containing a `list` array and `total` count.
  - `message_id`: Message ID (optional). Not filled in with `before` returns the most recent N messages.
  - `before`: Returns N messages before the specified message ID.
  - `after`: Returns N messages after the specified message ID.
  - > **Note:** At least one of `before` and `after` must be specified and greater than 0, otherwise the server will not return any messages.

Board scope is automatically inferred by `To()`:
- Specifying `To(target_type, target_id)` → Local board (specific user/group)
- Not specifying `To()` → Global board

```python
# Local board (expires after 60 seconds)
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

| Field         | Type   | Required | Description                                                                 |
|---------------|--------|----------|------------------------------------------------------------------------------|
| `text`        | string | Yes      | Text on the button                                                           |
| `actionType`  | int    | Yes      | Action type: <br>`1`: Navigate URL<br>`2`: Copy<br>`3`: Report on click      |
| `url`         | string | No       | Used when `actionType=1`, indicating the target URL for navigation           |
| `value`       | string | No       | When `actionType=2`, this value will be copied to the clipboard<br>When `actionType=3`, this value will be sent to the subscriber |

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
> **Note:** Only users who click the **report event** button will receive a push notification; neither **copy** nor **navigate URL** will trigger a push notification.

### Fluent Modifier Methods (Combinable)

Fluent modifier methods return `self`, supporting chained calls, and must be called before the final sending method:

- `.Reply(message_id: str)`: Replies to a specified message.
- `.At(user_id: str)`: Mentions a specified user.
- `.AtAll()`: Mentions everyone.
- `.Buttons(buttons: List)`: Adds buttons.

### Fluent Call Examples

```python
# Basic sending
await yunhu.Send.To("user", user_id).Text("Hello")

# Reply to a message
await yunhu.Send.To("group", group_id).Reply(msg_id).Text("Replied message")

# Reply + buttons
await yunhu.Send.To("group", group_id).Reply(msg_id).Buttons(buttons).Text("Message with reply and buttons")
```

### Group Management Examples

```python
from ErisPulse.Core import adapter
yunhu = adapter.get("yunhu")

# Remove group member
await yunhu.Send.To("group", group_id).Kick(user_id)

# Mute user (10 minutes)
await yunhu.Send.To("group", group_id).Ban(user_id, duration=600)

# Unmute user
await yunhu.Send.To("group", group_id).Ban(user_id, duration=0)

# Permanent mute user
await yunhu.Send.To("group", group_id).Ban(user_id, duration=-1)

# Create group tag
await yunhu.Send.To("group", group_id).CreateTag("VIP User", color="#FF5733", desc="VIP Member")

# Edit group tag
await yunhu.Send.To("group", group_id).EditTag("VIP User", new_tag="SVIP User", color="#33C4FF")

# Delete group tag
await yunhu.Send.To("group", group_id).DeleteTag("VIP User")

# Get group tag list
result = await yunhu.Send.To("group", group_id).GetTagList()

# Add tag to user
await yunhu.Send.To("group", group_id).AddUserTag(user_id, "VIP User")

# Remove tag from user
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

# Get the last 10 messages in the group (returns 10 messages in total)
result = await yunhu.Send.To("group", group_id).GetMessages(before=10)

# Get the 10 messages before the specified message ID in the group (returns 11 messages in total)
result = await yunhu.Send.To("group", group_id).GetMessages(message_id="msg_xxx", before=10)

# Get 10 messages before and after the specified message ID in the group (returns 21 messages in total)
result = await yunhu.Send.To("group", group_id).GetMessages(message_id="msg_xxx", before=10, after=10)

# Get history messages in user session
result = await yunhu.Send.To("user", user_id).GetMessages(message_id="msg_xxx", before=10)
```

### OneBot12 Message Support

The adapter supports sending OneBot12 formatted messages, facilitating cross-platform message compatibility:

- `.Raw_ob12(message: List[Dict], **kwargs)`: Sends a OneBot12 formatted message.

```python
# Send OneBot12 formatted message
ob12_msg = [{"type": "text", "data": {"text": "Hello"}}]
await yunhu.Send.To("user", user_id).Raw_ob12(ob12_msg)

# Combined with fluent modifiers
ob12_msg = [{"type": "text", "data": {"text": "Replied message"}}]
await yunhu.Send.To("group", group_id).Reply(msg_id).Raw_ob12(ob12_msg)
```

## Standard API Actions (ApiDSL)

> [!NOTE]
> This feature requires ErisPulse **2.7.0+** and YunhuAdapter **4.3.0+**.

In addition to the `Send` chain-based sending, the adapter also provides the `Api` inner class, exposing standard OneBot12 API actions and Yunhu platform extension actions. All methods return a standard response format.

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

# Message recall (requires additional chat_id + chat_type)
await yunhu.Api.delete_message("msg_id", chat_id="123", chat_type="group")

# Multi-account: Specify Bot account
info = await yunhu.Api.Using("bot1").get_self_info()
```

### Supported Standard Actions

| Method | Description | Data Source |
|--------|-------------|-------------|
| `get_self_info()` | Robot self information | Public Web API (bot-info) |
| `get_user_info(user_id)` | User information (any user can query) | Public Web API (user/homepage) |
| `get_group_info(group_id)` | Group information | Public Web API (group-info) |
| `upload_file(*, type, name, ...)` | Upload file (auto-detect image/video/file) | Bot open API |
| `get_file(file_id)` | Get file (file_id is URL) | — |
| `delete_message(message_id, *, chat_id, chat_type)` | Recall message | Bot open API (/bot/recall) |

> **Note**: `get_self_info` / `get_user_info` / `get_group_info` are implemented via **non-official public Web API** (chat-web-go.jwzhd.com). These interfaces require no authentication but are not officially documented and may change with platform updates; failure returns a standard error response.

### Unsupported Standard Actions

The following standard actions have no corresponding API in Yunhu, and calling them returns `retcode=10002` (unsupported operation):
- `get_friend_list` (the "robot user list" in Bot open API is still pending launch)
- `get_group_list` / `get_group_member_info` / `get_group_member_list`
- `set_group_name` / `leave_group`

### Platform Extension Actions

Call Yunhu-specific actions via `Api.call("yunhu.xxx", **params)` (parameters use OB12-style naming, adapter automatically translates to Yunhu fields):

| Extension Action | Description | Equivalent Send Method |
|------------------|-------------|------------------------|
| `yunhu.recall` | Recall message (msg_id, chat_id, chat_type) | `Send.To(...).Recall(msg_id)` |
| `yunhu.kick` | Remove group member (group_id, user_id) | `Send.To("group", g).Kick(uid)` |
| `yunhu.ban` | Mute (group_id, user_id, duration) | `Send.To("group", g).Ban(uid, duration)` |
| `yunhu.unban` | Unmute (group_id, user_id) | `Send.To("group", g).Ban(uid, duration=0)` |
| `yunhu.tag.create/edit/delete/list` | Group tag CRUD (group_id, ...) | `Send.To("group", g).CreateTag(...)` etc. |
| `yunhu.tag.relate` / `yunhu.tag.relate_cancel` | Add/remove tag for user | `Send.To("group", g).AddUserTag(...)` etc. |
| `yunhu.set_member_title` / `yunhu.unset_member_title` | **Member title semantic alias** (tag ≈ title, internally mapped to tag.relate) | — |
| `yunhu.msg_type_limit` | Group message type restriction (group_id, type) | `Send.To("group", g).SetMsgTypeLimit(...)` |
| `yunhu.get_messages` | Get historical messages (chat_id, chat_type, message_id?, before?, after?) | `Send.To(...).GetMessages(...)` |
| `yunhu.bot_info` | Public bot-info query (bot_id) | — |
| `yunhu.user_homepage` | Public user homepage query (user_id) | — |

```python
# Platform extension example
await yunhu.Api.call("yunhu.kick", group_id="123", user_id="456")
await yunhu.Api.call("yunhu.set_member_title", group_id="123", user_id="456", title="VIP")
result = await yunhu.Api.call("yunhu.get_messages", chat_id="123", chat_type="group", before=10)
```

> **Tags and Titles**: Yunhu's "tag" semantics are equivalent to OneBot12 group member `title`. `yunhu.set_member_title` is a native semantic alias for `yunhu.tag.relate`, both internally mapped to the same endpoint. In group message events, the sender's role is mapped from `senderUserLevel` to the standard `role` field (owner/admin/member).

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

Platform-specific features require `platform=="yunhu"` check before use.

### Core Differences

1. Unique event types:
    - Form (e.g., form command): `yunhu_form`
    - Emoji pack/sticker message segment: `yunhu_expression`
    - Button click: `yunhu_button_click`
    - A2UI button click: `yunhu_a2ui_button`
    - Bot setting: `yunhu_bot_setting`
    - Quick menu: `yunhu_shortcut_menu`
2. Standard field extension (4.3.0+):
    - Message events add standard `role` field (mapped from Yunhu's `senderUserLevel` to `owner`/`admin`/`member`)
    - New `user_avatar` field (sender's avatar URL)
3. Extended fields:
    - All unique fields are prefixed with `yunhu_`
    - Original data is preserved in the `yunhu_raw` field
    - In private chats, `self.user_id` represents the bot ID

### Special Field Examples

```python
# Form command
{
  "type": "message",
  "detail_type": "private",
  "yunhu_command": {
    "name": "Form command name",
    "id": "Command ID",
    "form": {
      "Field ID1": {
        "id": "Field ID1",
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

### Button Click Event Handling Example

```python
from ErisPulse.Core.Event import notice

@notice.on_notice()
async def handle_yunhu_notice(event):
    """Handle Yunhu notification events

    Use the generic on_notice() decorator to handle all notification events,
    then distinguish between different types of notifications using detail_type.
    event.reply() will automatically reply through the Yunhu platform.
    """

# Check if it is a button click event
    if event.get("detail_type") == "yunhu_button_click":
        user_id = event.get_user_id()
        user_nickname = event.get_user_nickname()
        button_value = event.get("yunhu_button", {}).get("value", "")

        print(f"User {user_nickname}({user_id}) clicked the button: {button_value}")

# Auto-respond using event.reply() (will automatically select the correct sending method based on the platform)
        if button_value == "confirm":
            await event.reply("You clicked the confirm button!")
        elif button_value == "cancel":
            await event.reply("The operation has been cancelled")
        else:
            await event.reply(f"Received your selection: {button_value}")

# Handling Shortcut Menu Events
    elif event.get("detail_type") == "yunhu_shortcut_menu":
        menu_id = event.get("yunhu_menu", {}).get("id", "")
        await event.reply(f"Shortcut menu triggered: {menu_id}")

# Handling Bot Setting Changes
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

### Sending Message with Buttons Using Chained Calls

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

# Sending a Message with Buttons to a Group  
await yunhu.Send.To("group", "123456").Buttons(buttons).Text("Please confirm the following action")

# Sending a Message with Buttons to a User's Private Chat
await yunhu.Send.To("user", "789").Buttons(buttons).Text("Please select your preferred settings")

### Sending A2UI Messages

```python
from ErisPulse import sdk

yunhu = sdk.adapter.get("yunhu")
```

# Sending A2UI Messages
await yunhu.Send.To("user", user_id).A2UI("A2UI interactive card content")
```

# Bot Settings
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
  "user_id": "User ID that triggered the menu",
  "user_nickname": "User nickname",
  "group_id": "Group ID (if it's a group chat)",
  "yunhu_menu": {
    "id": "Menu ID",
    "type": "Menu type (integer)",
    "action": "Menu action (integer)"
  }
}
```

## Event Mixin Extension Methods

The adapter has registered the following platform-specific methods, available only when `platform == "yunhu"`:

| Method | Return Type | Description |
|--------|-------------|-------------|
| `get_raw_event()` | `dict` | Get raw Yunhu event data (`yunhu_raw`) |
| `get_sender_level()` | `str` | Sender's original Yunhu level (owner/administrator/member/unknown) |
| `get_sender_role()` | `str` | Sender's OneBot12 standard role (owner/admin/member) |
| `get_sender_title()` | `str` | Sender's title (standard `title` field accessor, reserved) |
| `get_sender_avatar()` | `str` | Sender's avatar URL |
| `get_command()` | `dict` | Command data (only for command message events, `yunhu_command`) |
| `get_button_value()` | `str` | The `value` of a button click event (`yunhu_button.value`) |
| `get_a2ui_action()` | `str` | The `actionName` of an A2UI button event |
| `get_a2ui_form_context()` | `dict` | The form context of an A2UI button event |
| `get_menu_id()` | `str` | Shortcut menu event ID (`yunhu_menu.id`) |
| `get_setting()` | `dict` | Setting data from a bot setting event (`yunhu_setting`) |
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
```

## Extension Field Description

- All custom fields are prefixed with `yunhu_` to avoid conflicts with standard fields
- Original data is retained in the `yunhu_raw` field for accessing the complete raw data from the Yunhu platform
- `self.user_id` represents the bot ID (obtained from the bot_id in the configuration)
- Form commands provide structured data through the `yunhu_command` field
- Button click events provide button-related information through the `yunhu_button` field
- A2UI button events provide A2UI interaction-related information through the `yunhu_a2ui` field
- Bot setting changes provide setting item data through the `yunhu_setting` field
- Quick menu operations provide menu-related information through the `yunhu_menu` field
- Emoji/Sticker messages provide sticker data (sticker_id, sticker pack ID, image dimensions, etc.) through the `yunhu_expression` message segment

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
| `image_name` | string | File path of the expression image |
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
```

## Multiple Bot Configuration

### Configuration Explanation

Yunhu Adapter supports configuring and running multiple Yunhu bot accounts simultaneously.

```toml
# config.toml
[Yunhu_Adapter.accounts.bot1]
token = "your_bot1_token"  # Bot token (required)
mode = "ws"  # Receive mode (optional, default is "ws", options: "ws", "webhook")
webhook_path = "/webhook/bot1"  # Webhook path (optional, default is "/webhook")
enabled = true  # Whether to enable (optional, default is true)

[Yunhu_Adapter.accounts.bot2]
token = "your_bot2_token"  # Second bot's token
webhook_path = "/webhook/bot2"  # Independent webhook path
enabled = true
```

**Configuration Item Explanation:**
- `token`: API token provided by Yunhu platform (required)
- `mode`: Receive mode (optional, default is `"ws"`, options: `"ws"`, `"webhook"`)
- `webhook_path`: HTTP path for receiving Yunhu events (optional, default is `"/webhook"`, used only in webhook mode)
- `enabled`: Whether to enable this account (optional, default is true)

**Important Notes:**
1. Yunhu platform's bot ID is automatically detected at **runtime**, no need to specify in configuration
2. In webhook mode, each bot should have an independent `webhook_path` to receive its own webhook events
3. When configuring webhooks on the Yunhu platform, please set corresponding URLs for each bot, for example:
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

# Send message using bot_id (automatically matches corresponding account)
await yunhu.Send.Using("30535459").To("group", "group456").Text("Hello from bot!")

# Use first enabled bot if not specified
await yunhu.Send.To("user", "user123").Text("Hello from default bot!")
```

> **Note:** When using `bot_id`, the system will automatically find the matching account in the configuration. This is especially useful when handling event replies, as you can directly use `event["self"]["user_id"]` to reply using the same account.

### Bot Identification in Events

Received events will automatically include the corresponding `bot_id` information:

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

The adapter will automatically include `bot_id` information in logs, which helps with debugging and tracking:

```
[INFO] [yunhu] [bot:30535459] Received private message from user user123
[INFO] [yunhu] [bot:12345678] Message sent successfully, message_id: abc123
```

### Management Interface

```python
# Get all account information
bots = yunhu.bots

# Check if account is enabled
bot_status = {
    bot_name: bot_config.enabled
    for bot_name, bot_config in yunhu.bots.items()
}

# Dynamically enable/disable account (requires adapter restart)
yunhu.bots["bot1"].enabled = False
```

### Legacy Configuration Compatibility

Older `[Yunhu_Adapter.bots.*]` configurations (including the `bot_id` field) will be automatically migrated to the `accounts` format (`bot_id` has been changed to automatic detection at runtime, and the value in the configuration will be ignored); it is recommended to migrate to the new format as soon as possible.