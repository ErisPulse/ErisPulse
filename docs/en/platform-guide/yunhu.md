# Yunhu Platform Feature Documentation

YunhuAdapter is an adapter built on the Yunhu protocol, integrating all Yunhu functional modules and providing a unified interface for event handling and message operations.

---

## Document Information

- Corresponding module version: 4.4.0
- Maintainer: ErisPulse

## Basic Information

- Platform Overview: Yunhu is an enterprise-level instant messaging platform
- Adapter Name: YunhuAdapter
- Multi-account Support: Supports identifying and configuring multiple Yunhu robot accounts via bot_id
- Chainable Modifier Support: Supports chainable modifier methods such as `.Reply()`
- OneBot12 Compatibility: Supports sending OneBot12 format messages

## v5 Paradigm Update (4.4.0)

This adapter has completed alignment with the v5 paradigm (incremental upgrade, API compatible):

- **Full set of official server APIs** (Api DSL extension methods): Edit messages, batch sending, message lists, user/global dashboards, group member mute, remove group members, group message type control, group tag CRUD, user tagging
- **Standard keyboard segment** (cross-platform interactive component standard): {"type": "keyboard", "data": {"rows": [[{"label", "type": "callback|link", "data"}]]}} segment automatically converted to Yunhu buttons; .Buttons(rows) / .Keyboard(rows) modifiers accept generic structure (native structure backward compatible)
- **Standard fields for interaction callbacks**: Button click/A2UI event includes standard fields interaction_id / button_data
- **spawn_background task ownership**: WS connection tasks changed to use runtime.spawn_background
- **Framework soft dependency**: Runtime detection of ErisPulse>=2.7.1 with prompt; version logs output on startup

### Platform Extension Actions (call / Api methods)

```python
from ErisPulse import sdk
yunhu = sdk.adapter.get("yunhu")

# Api methods (official server API)
await yunhu.Api.edit_message(msg_id, recv_id, "group", "text", {"text": "New content"})
await yunhu.Api.batch_send(["userId1", "userId2"], "text", {"text": "Announcement"})
await yunhu.Api.get_message_list(group_id, "group", before=10)
await yunhu.Api.set_user_board(chat_id, "group", "Dashboard content", expire_time=3600)
await yunhu.Api.dismiss_global_board()
await yunhu.Api.gag_group_member(group_id, user_id, 600)      # Mute for 600 seconds, 0=unmute
await yunhu.Api.remove_group_member(group_id, user_id)
await yunhu.Api.set_group_msg_type_limit(group_id, "text,image")
await yunhu.Api.create_group_tag(group_id, "VIP", color="#FF5733")
await yunhu.Api.add_user_tag(group_id, user_id, "VIP")

# Button click callback (standard fields)
from ErisPulse.Core.Event import notice

@notice.on_notice()
async def handle_button(event):
    if event.get("platform") == "yunhu" and event.get("button_data"):
        data = event["button_data"]     # Cross-platform unified value retrieval
        interaction_id = event["interaction_id"]
```

> Complete standard documentation is available at [Cross-Platform Interactive Component Standard](../standards/standardization-guide.md).

---
## Supported Message Sending Types

All sending methods are implemented through chainable syntax, for example:
```python
from ErisPulse.Core import adapter
yunhu = adapter.get("yunhu")

await yunhu.Send.To("user", user_id).Text("Hello World!")
```

The supported sending types include:
- `.Text(text: str)`: Send plain text message.
- `.Html(html: str)`: Send HTML formatted message.
- `.Markdown(markdown: str)`: Send Markdown formatted message.
- `.A2UI(text: str)`: Send A2UI formatted message.
- `.Image(file: bytes, stream: bool = False, filename: str = None)`: Send image message, supports streaming upload and custom filename.
- `.Video(file: bytes, stream: bool = False, filename: str = None)`: Send video message, supports streaming upload and custom filename.
- `.File(file: bytes, stream: bool = False, filename: str = None)`: Send file message, supports streaming upload and custom filename.
- `.Batch(target_ids: List[str], message: str, content_type: str = "text", **kwargs)`: Batch send messages.
- `.Edit(msg_id: str, text: str, content_type: str = "text", buttons: List = None)`: Edit existing message.
- `.Recall(msg_id: str)`: Recall message.
- `.Board(content: str, content_type: str = "text")`: Publish announcement board. Scope inferred from `To()` (specifying target=local board, not specifying=global board). Chainable modifiers: `.Expire(duration)` relative expiration (seconds), `.ExpireAt(timestamp)` absolute expiration (second-level timestamp), `.ForMember(member_id)` group member board; **automatically撤销 board when content is empty**. Still compatible with old-style `Board("local", "announcement")` explicit scope syntax.
- `.DismissBoard()`: Recall announcement board. Scope inferred from `To()`, supports `.ForMember(member_id)`; still compatible with old-style `DismissBoard("local")` syntax.
- `.Stream(content_type: str, content_generator: AsyncGenerator, **kwargs)`: Send streaming message.

### Group Management Methods

All group management methods need to specify the group through chainable syntax, for example:
```python
from ErisPulse.Core import adapter
yunhu = adapter.get("yunhu")

await yunhu.Send.To("group", group_id).Kick(user_id)
```

- `.Kick(user_id: str)`: Remove group member. The bot needs `Allow removing group members` permission.
- `.Ban(user_id: str, duration: int = 600)`: Mute user. `duration` is mute duration (seconds), 0 is unmute, -1 is permanent mute. The bot needs `Allow muting users` permission.
- `.CreateTag(tag: str, color: str = None, desc: str = None, sort: int = None)`: Create group tag. `color` format is #RRGGBB, `sort` smaller is more forward. The bot needs `Allow controlling tag group` permission.
- `.EditTag(tag: str, new_tag: str = None, color: str = None, desc: str = None, sort: int = None)`: Modify group tag. Optional parameters, if not passed, will not modify. The bot needs `Allow controlling tag group` permission.
- `.DeleteTag(tag: str)`: Delete group tag. The bot needs `Allow controlling tag group` permission.
- `.GetTagList()` : Get group tag list. Returns response data containing `list` array.
- `.AddUserTag(user_id: str, tag: str)`: Add tag to user. The bot needs `Allow controlling tag group` permission.
- `.RemoveUserTag(user_id: str, tag: str)`: Remove tag from user. The bot needs `Allow controlling tag group` permission.
- `.SetMsgTypeLimit(types: str)`: Control group message types. `types` is message type name, multiple separated by commas (e.g. `"text,image,video"`), empty string means no restriction. The bot needs `Allow modifying group information` permission.

### Message Query Methods

To get the historical message list of a specified session (user/group), you need to specify the target through chainable syntax, for example:
```python
from ErisPulse.Core import adapter
yunhu = adapter.get("yunhu")

result = await yunhu.Send.To("group", group_id).GetMessages(before=10)
```

- `.GetMessages(message_id: str = None, before: int = None, after: int = None)`: Get session history messages. Returns response data containing `list` array and `total` count.
  - `message_id`: Message ID (optional). If not filled, combined with `before` returns the most recent N messages.
  - `before`: Returns the N messages before the specified message ID.
  - `after`: Returns the N messages after the specified message ID.
  - > **Note:** At least one of `before` and `after` must be specified and greater than 0, otherwise the server will not return any message.

Board scope is automatically inferred by `To()`:
- Specifying `To(target_type, target_id)` → Local board (specified user/group)
- Not specifying `To()` → Global board

```python
# Local board (expires in 60 seconds)
await yunhu.Send.To("group", group_id).Expire(60).Board("Announcement", content_type="markdown")

# Group member board (visible only to specified member)
await yunhu.Send.To("group", group_id).ForMember(user_id).Board("Visible only to you")

# Absolute timestamp expiration
await yunhu.Send.To("group", group_id).ExpireAt(1785208268).Board("Expires at specified time")

# Global board
await yunhu.Send.Board("Global Announcement")

# Clear local board (content empty → automatically recall)
await yunhu.Send.To("group", group_id).Board("")
```

### Button Parameter Description

The `buttons` parameter is a nested list representing the button layout and functionality. Each button object contains the following fields:

| Field        | Type   | Required | Description                                                                 |
|--------------|--------|----------|-----------------------------------------------------------------------------|
| `text`       | string | Yes      | Text on the button                                                          |
| `actionType` | int    | Yes      | Action type: <br>`1`: Navigate URL<br>`2`: Copy<br>`3`: Click report        |
| `url`        | string | No       | Used when `actionType=1`, indicating the target URL for navigation          |
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
> - Only user clicks on the **report event** button will receive a push notification, **copy** and **navigate URL** cannot receive a push notification.

### Chainable Modifier Methods (can be combined)

Chainable modifier methods return `self`, support chained calls, must be called before the final send method:

- `.Reply(message_id: str)`: Reply to a specified message.
- `.At(user_id: str)`: @ a specified user.
- `.AtAll()`: @ all users.
- `.Buttons(buttons: List)`: Add buttons.

### Chainable Call Examples

```python
# Basic send
await yunhu.Send.To("user", user_id).Text("Hello")

# Reply to message
await yunhu.Send.To("group", group_id).Reply(msg_id).Text("Reply message")

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

# Unmute
await yunhu.Send.To("group", group_id).Ban(user_id, duration=0)

# Permanent mute
await yunhu.Send.To("group", group_id).Ban(user_id, duration=-1)

# Create group tag
await yunhu.Send.To("group", group_id).CreateTag("VIP User", color="#FF5733", desc="VIP Member")

# Modify group tag
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

# Clear message type limit
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

The adapter supports sending OneBot12 format messages, facilitating cross-platform message compatibility:

- `.Raw_ob12(message: List[Dict], **kwargs)`: Send OneBot12 format message.

```python
# Send OneBot12 format message
ob12_msg = [{"type": "text", "data": {"text": "Hello"}}]
await yunhu.Send.To("user", user_id).Raw_ob12(ob12_msg)

# Combined with chainable modifiers
ob12_msg = [{"type": "text", "data": {"text": "Reply message"}}]
await yunhu.Send.To("group", group_id).Reply(msg_id).Raw_ob12(ob12_msg)
```

## Standard API Actions (ApiDSL)

> [!NOTE]
> This feature requires ErisPulse **2.7.0+** and YunhuAdapter **4.3.0+**.

In addition to the `Send` chainable sending, the adapter also provides the `Api` inner class, exposing OneBot12 standard API actions and Yunhu platform extension actions. All methods return a standard response format.

```python
from ErisPulse.Core import adapter
yunhu = adapter.get("yunhu")

# Information query (via public Web API, no authentication required)
result = await yunhu.Api.get_self_info()              # Robot self information
result = await yunhu.Api.get_user_info("7058262")     # Any user information
result = await yunhu.Api.get_group_info("635409929")  # Group information

# File operations
result = await yunhu.Api.upload_file(type="path", name="a.png", path="./a.png")
result = await yunhu.Api.get_file("https://chat-file.jwznb.com/xxx")

# Recall message (requires additional chat_id + chat_type)
await yunhu.Api.delete_message("msg_id", chat_id="123", chat_type="group")

# Multi-account: specify Bot account
info = await yunhu.Api.Using("bot1").get_self_info()
```

### Supported Standard Actions

| Method | Description | Data Source |
|--------|-------------|-------------|
| `get_self_info()` | Robot self information | Public Web API (bot-info) |
| `get_user_info(user_id)` | User information (any user can query) | Public Web API (user/homepage) |
| `get_group_info(group_id)` | Group information | Public Web API (group-info) |
| `upload_file(*, type, name, ...)` | Upload file (automatically determine image/video/file) | Bot open API |
| `get_file(file_id)` | Get file (file_id is URL) | — |
| `delete_message(message_id, *, chat_id, chat_type)` | Recall message | Bot open API (/bot/recall) |

> **Note**: `get_self_info` / `get_user_info` / `get_group_info` are implemented through **non-official public Web API** (chat-web-go.jwzhd.com). These interfaces require no authentication but are not officially documented and may change with platform updates; failure returns a standard error response.

### Unsupported Standard Actions

The following standard actions have no corresponding API in Yunhu, and calling them returns `retcode=10002` (unsupported operation):
- `get_friend_list` (Bot open API's "robot user list" is still pending launch)
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
| `yunhu.tag.relate` / `yunhu.tag.relate_cancel` | Add/Remove tag from user | `Send.To("group", g).AddUserTag(...)` etc. |
| `yunhu.set_member_title` / `yunhu.unset_member_title` | **Member title semantic alias** (tag ≈ title, internally mapped to tag.relate) | — |
| `yunhu.msg_type_limit` | Group message type limit (group_id, type) | `Send.To("group", g).SetMsgTypeLimit(...)` |
| `yunhu.get_messages` | Get history messages (chat_id, chat_type, message_id?, before?, after?) | `Send.To(...).GetMessages(...)` |
| `yunhu.bot_info` | Public bot-info query (bot_id) | — |
| `yunhu.user_homepage` | Public user homepage query (user_id) | — |

```python
# Example of platform extension
await yunhu.Api.call("yunhu.kick", group_id="123", user_id="456")
await yunhu.Api.call("yunhu.set_member_title", group_id="123", user_id="456", title="VIP")
result = await yunhu.Api.call("yunhu.get_messages", chat_id="123", chat_type="group", before=10)
```

> **Tags and Titles**: In Yunhu, "tag" semantics are equivalent to OneBot12 group member `title`. `yunhu.set_member_title` is a native semantic alias for `yunhu.tag.relate`, both internally mapping to the same endpoint. In group message events, the sender's role is mapped to the standard `role` field from Yunhu's `senderUserLevel` (owner/admin/member).

## Send Method Return Values

All send methods return a Task object, which can be awaited to get the send result. The return result follows the ErisPulse adapter standardization return specification:

```python
{
    "status": "ok",           // Execution status
    "retcode": 0,             // Return code
    "data": {...},            // Response data
    "self": {...},            // Self information (includes bot_id)
    "message_id": "123456",   // Message ID
    "message": "",            // Error message
    "yunhu_raw": {...}        // Raw response data
}
```

## Unique Event Types

Platform-specific features should be used only after checking platform=="yunhu"

### Core Differences

1. Unique event types:
    - Forms (e.g., form commands): yunhu_form
    - Emoticon/pack sticker message segments: yunhu_expression
    - Button click: yunhu_button_click
    - A2UI button click: yunhu_a2ui_button
    - Bot settings: yunhu_bot_setting
    - Quick menu: yunhu_shortcut_menu
2. Standard field extension (4.3.0+):
    - Message events add standard `role` field (mapped from Yunhu `senderUserLevel` to `owner`/`admin`/`member`)
    - Add `user_avatar` field (sender's avatar URL)
3. Extension fields:
    - All unique fields are prefixed with yunhu_
    - Original data is retained in the yunhu_raw field
    - In private chat, self.user_id represents the robot ID

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
  "user_id": "Operation user ID",
  "user_nickname": "User nickname",
  "message_id": "Message ID",
  "yunhu_a2ui": {
    "recv_id": "Recipient ID",
    "recv_type": "Recipient type",
    "action_name": "Action name",
    "source_component_id": "Source component ID",
    "form_context": {},
    "interaction_json": "Interaction data JSON string"
  }
}

### Button Click Event Handling Example

```python
from ErisPulse.Core.Event import notice

@notice.on_notice()
async def handle_yunhu_notice(event):
    """Handle Yunhu notice events

    Use the generic on_notice() decorator to handle all notice events,
    then distinguish different types of notices by detail_type
    event.reply() will automatically reply through the Yunhu platform
    """
    # Check if it is a button click event
    if event.get("detail_type") == "yunhu_button_click":
        user_id = event.get_user_id()
        user_nickname = event.get_user_nickname()
        button_value = event.get("yunhu_button", {}).get("value", "")

        print(f"User {user_nickname}({user_id}) clicked the button: {button_value}")

        # Use event.reply() to automatically reply (will automatically select the correct sending method based on platform)
        if button_value == "confirm":
            await event.reply("You clicked the confirm button!")
        elif button_value == "cancel":
            await event.reply("Operation canceled")
        else:
            await event.reply(f"Received your selection: {button_value}")

    # Handle quick menu event
    elif event.get("detail_type") == "yunhu_shortcut_menu":
        menu_id = event.get("yunhu_menu", {}).get("id", "")
        await event.reply(f"Triggered quick menu: {menu_id}")

    # Handle bot setting change
    elif event.get("detail_type") == "yunhu_bot_setting":
        settings = event.get("yunhu_setting", {})
        await event.reply(f"Settings updated: {settings}")

    # Handle A2UI button event
    elif event.get("detail_type") == "yunhu_a2ui_button":
        a2ui = event.get("yunhu_a2ui", {})
        action_name = a2ui.get("action_name", "")
        form_context = a2ui.get("form_context", {})
        await event.reply(f"A2UI operation: {action_name}, form data: {form_context}")
```

### Sending Message with Buttons Using Chainable Calls

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

# Send message with buttons to group
await yunhu.Send.To("group", "123456").Buttons(buttons).Text("Please confirm the following operation")

# Send message with buttons to private chat
await yunhu.Send.To("user", "789").Buttons(buttons).Text("Please select your preference settings")
```

### Sending A2UI Message

```python
from ErisPulse import sdk

yunhu = sdk.adapter.get("yunhu")

# Send A2UI message
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
  "user_id": "User ID who triggered the menu",
  "user_nickname": "User nickname",
  "group_id": "Group ID (if group chat)",
  "yunhu_menu": {
    "id": "Menu ID",
    "type": "Menu type (integer)",
    "action": "Menu action (integer)"
  }
}
```

## Event Mixin Extension Methods

The adapter registers the following platform-specific methods, available only when `platform == "yunhu"`:

| Method | Return Type | Description |
|------|----------|------|
| `get_raw_event()` | `dict` | Get Yunhu raw event data (`yunhu_raw`) |
| `get_sender_level()` | `str` | Sender's original Yunhu level (`owner/administrator/member/unknown`) |
| `get_sender_role()` | `str` | Sender's OneBot12 standard role (`owner/admin/member`) |
| `get_sender_title()` | `str` | Sender's title (standard `title` field accessor, reserved) |
| `get_sender_avatar()` | `str` | Sender's avatar URL |
| `get_command()` | `dict` | Command data (only for command message events, `yunhu_command`) |
| `get_button_value()` | `str` | Button click event's value (`yunhu_button.value`) |
| `get_a2ui_action()` | `str` | A2UI button event's actionName |
| `get_a2ui_form_context()` | `dict` | A2UI button event's form context |
| `get_menu_id()` | `str` | Quick menu event ID (`yunhu_menu.id`) |
| `get_setting()` | `dict` | Bot setting event's setting data (`yunhu_setting`) |
| `is_command_message()` | `bool` | Whether it is a command message |
| `is_button_click()` | `bool` | Whether it is a button click event |
| `is_a2ui_button()` | `bool` | Whether it is an A2UI button event |

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

## Extension Field Descriptions

- All unique fields are prefixed with `yunhu_` to avoid conflicts with standard fields
- Original data is retained in the `yunhu_raw` field for accessing complete Yunhu platform data
- `self.user_id` represents the robot ID (obtained from the bot_id in configuration)
- Form commands provide structured data through the `yunhu_command` field
- Button click events provide button information through the `yunhu_button` field
- A2UI button events provide A2UI interaction information through the `yunhu_a2ui` field
- Bot setting changes provide setting item data through the `yunhu_setting` field
- Quick menu operations provide menu information through the `yunhu_menu` field
- Emoticon/sticker message segments provide sticker data (sticker_id, sticker pack ID, image size, etc.) through the `yunhu_expression` segment

### Emoticon/Sticker Message Segment (yunhu_expression)

When a user sends an emoticon or sticker, the message segment type is `yunhu_expression`:

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
|------|------|------|
| `sticker_id` | string | Unique sticker identifier |
| `sticker_pack_id` | string | Sticker pack ID |
| `expression_id` | string | Expression ID |
| `image_name` | string | Expression image file path |
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

---

## Multi-Bot Configuration

### Configuration Instructions

The Yunhu adapter supports configuring and running multiple Yunhu robot accounts simultaneously.

```toml
# config.toml
[Yunhu_Adapter.accounts.bot1]
token = "your_bot1_token"  # Robot token (required)
mode = "ws"  # Receive mode (optional, default "ws", options: "ws", "webhook")
webhook_path = "/webhook/bot1"  # Webhook path (optional, default "/webhook", used in webhook mode)
enabled = true  # Enable (optional, default true)

[Yunhu_Adapter.accounts.bot2]
token = "your_bot2_token"  # Second robot's token
webhook_path = "/webhook/bot2"  # Unique webhook path
enabled = true
```

**Configuration Item Description:**
- `token`: Yunhu platform's API token (required)
- `mode`: Receive mode (optional, default "ws", options "ws", "webhook")
- `webhook_path`: HTTP path for receiving Yunhu events (optional, default "/webhook", used in webhook mode)
- `enabled`: Whether to enable the account (optional, default true)

**Important Notes:**
1. The robot ID in the Yunhu platform is automatically detected at runtime and does not need to be specified in the configuration
2. Each bot in webhook mode should have a unique `webhook_path` to receive its own webhook events
3. When configuring webhooks on the Yunhu platform, please set up corresponding URLs for each bot, for example:
   - Bot1: `https://your-domain.com/webhook/bot1`
   - Bot2: `https://your-domain.com/webhook/bot2`

### Using Send DSL to Specify Bot

You can specify which bot to use for sending messages via the `Using()` method. This method supports two types of parameters:
- **Account name**: The name of the bot in the configuration (e.g., `bot1`, `bot2`)
- **bot_id**: The `bot_id` value in the configuration

```python
from ErisPulse.Core import adapter
yunhu = adapter.get("yunhu")

# Send message using account name
await yunhu.Send.Using("bot1").To("user", "user123").Text("Hello from bot1!")

# Send message using bot_id (automatically matches the corresponding account)
await yunhu.Send.Using("30535459").To("group", "group456").Text("Hello from bot!")

# Send message without specifying, uses the first enabled bot
await yunhu.Send.To("user", "user123").Text("Hello from default bot!")
```

> **Note:** When using `bot_id`, the system will automatically find the matching account in the configuration. This is especially useful when handling event replies, where you can directly use `event["self"]["user_id"]` to reply with the same account.

### Bot Identifier in Events

Events received will automatically include the corresponding `bot_id` information:

```python
from ErisPulse.Core.Event import message

@message.on_message()
async def handle_message(event):
    if event["platform"] == "yunhu":
        # Get the robot ID that triggered the event
        bot_id = event["self"]["user_id"]
        print(f"Message from Bot: {bot_id}")
        
        # Reply using the same bot
        yunhu = adapter.get("yunhu")
        await yunhu.Send.Using(bot_id).To(
            event["detail_type"],
            event["user_id"] if event["detail_type"] == "private" else event["group_id"]
        ).Text("Reply message")
```

### Logging Information

The adapter will automatically include `bot_id` information in the logs, which is helpful for debugging and tracking:

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

### Backward Compatibility for Old Configuration

Old configuration format `[Yunhu_Adapter.bots.*]` (with `bot_id` field) will be automatically migrated to the `accounts` format (`bot_id` is now automatically detected at runtime, and the value in the configuration will be ignored); it is recommended to migrate to the new format as soon as possible.