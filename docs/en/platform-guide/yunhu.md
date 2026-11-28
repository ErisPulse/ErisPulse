# Yunhu Platform Features Documentation

YunhuAdapter is an adapter built on the Yunhu protocol, integrating all Yunhu functional modules and providing unified event handling and message operation interfaces.

---

## Document Information

- Corresponding module version: 4.6.2
- Maintainer: ErisPulse
- Last updated: 2026-11-10

## Basic Information

- Platform overview: Yunhu is an enterprise-grade instant messaging platform
- Adapter name: YunhuAdapter
- Multi-account support: Supports identifying and configuring multiple Yunhu bot accounts via bot_id
- Chained modifier support: Supports chained modifier methods such as `.Reply()`
- OneBot12 compatibility: Supports sending messages in OneBot12 format

## v5 Paradigm Update (4.4.0)

This adapter has completed v5 paradigm alignment (incremental upgrade, API compatible):

- **Complete official server-side API set** (Api DSL extension methods): edit message, batch send, message list, user/global board, group member mute, remove group member, group message type control, group tag CRUD, user tagging
- **Standard keyboard segment** (cross-platform interactive component standard): the {"type": "keyboard", "data": {"rows": [[{"label", "type": "callback|link", "data"}]]}} segment is automatically converted to Yunhu buttons; the .Buttons(rows) / .Keyboard(rows) modifiers accept generic structures (native structures remain backward compatible)
- **Standard interaction callback fields**: button click / A2UI events include the standard interaction_id / button_data fields
- **spawn_background task ownership**: WS connection tasks now use `runtime.spawn_background`
- **Framework soft dependency**: detects ErisPulse>=2.7.1 at runtime and prompts; outputs version logs at startup

### Platform Extension Actions (call / Api Methods)

```python
from ErisPulse import sdk
yunhu = sdk.adapter.get("yunhu")

# Api methods (official server-side API)
await yunhu.Api.edit_message(msg_id, recv_id, "group", "text", {"text": "New content"})
await yunhu.Api.batch_send(["userId1", "userId2"], "text", {"text": "Announcement"})
await yunhu.Api.get_message_list(group_id, "group", before=10)
await yunhu.Api.set_user_board(chat_id, "group", "Board content", expire_time=3600)
await yunhu.Api.dismiss_global_board()
await yunhu.Api.gag_group_member(group_id, user_id, 600)      # Mute for 600 seconds, 0 = unmute
await yunhu.Api.remove_group_member(group_id, user_id)
await yunhu.Api.set_group_msg_type_limit(group_id, "text,image")
await yunhu.Api.create_group_tag(group_id, "VIP", color="#FF5733")
await yunhu.Api.add_user_tag(group_id, user_id, "VIP")

# Button click callback (standard fields)
from ErisPulse.Core.Event import notice

@notice.on_notice()
async def handle_button(event):
    if event.get("platform") == "yunhu" and event.get("button_data"):
        data = event["button_data"]     # Unified cross-platform access
        interaction_id = event["interaction_id"]
```

> For the complete standard description, see [Cross-Platform Interactive Component Standard](../standards/standardization-guide.md).

## Standardization Alignment (4.6.2)

This version completes the adapter's standardization alignment; the response structure and error codes follow the [API Response Specification](../standards/api-response.md).

### Account and Multi-Account Closed Loop

- **Event injection of `self.account_id`** (internal account name): the `self` object of received events carries the account name that produced the event, and `event.reply()` automatically routes to **the account that received the event**, so in multi-account scenarios you no longer need to manually call `Using(bot_id)`
- **`call_api` dual-compatible fields**: both `account_id` (standard name) and `_account_id` (legacy name) can specify the account; the framework ApiDSL (`Api.Using(...)`) adapts automatically
- **`Send` reads `send_context`** (event account fallback): when calling `Send` within an event-handling context, it falls back to the originating account by default

### Error Code Specification

| retcode | Meaning | Description |
|---------|---------|-------------|
| 0 | Success | — |
| 33001 | Network error | Network exceptions such as failure to connect to the Yunhu server |
| 34100 | Platform failure | Yunhu returned a failure; the raw response is preserved in `yunhu_raw` |
| 10002 | Unsupported | Resource does not exist (bot/user/group not found) or standard actions without corresponding platform capability |
| 10003 | Parameter error | Missing or invalid parameters |

> **4.6.2 changes**: after the adapter added `_platform`, `make_response` automatically carries `yunhu_raw` via the framework, and platform failures uniformly return `34100`; "bot/user/group not found" was adjusted from `34001` to `10002` (resource does not exist).

### Response Structure Adjustment

The non-standard top-level `self` field of the original response has been moved into `data.self_info` (containing bot_id); the top level retains only standard fields and `yunhu_raw`:

```json
{
  "status": "ok",
  "retcode": 0,
  "data": {
    "self_info": {"user_id": "bot_id"},
    "messageInfo": {"msgId": "..."}
  },
  "message_id": "123456",
  "message": "",
  "yunhu_raw": {}
}
```

### Unknown Events Are No Longer Silently Dropped

Unrecognized Yunhu events now produce `type="unknown"` events (`detail_type` is the raw event type, with raw data preserved in `yunhu_raw`) and emit warning logs, so modules can troubleshoot unhandled event types accordingly.

### Platform Extension Method Conventions

Historical platform extension methods (`edit_message` / `batch_send` / `set_user_board` / `gag_group_member` / `create_group_tag`, etc.) remain available; **new platform extensions uniformly go through `Api.call("yunhu.xxx", **params)`** (see "Platform Extension Actions" below).

---

## Supported Message Send Types

All send methods are implemented via chained syntax, for example:
```python
from ErisPulse.Core import adapter
yunhu = adapter.get("yunhu")

await yunhu.Send.To("user", user_id).Text("Hello World!")
```

Supported send types include:
- `.Text(text: str)`: Sends a plain text message.
- `.Html(html: str)`: Sends an HTML-format message. `.HTML(html)` is an alias (consistent with the standard Send method naming).
- `.Markdown(markdown: str)`: Sends a Markdown-format message.
- `.MergeForward(nodes, title="Merged Chat History")`: Sends a merged forward message (rendered as a collapsible `<details>` HTML card, sent via the html channel).
- `.A2UI(text: str)`: Sends an A2UI-format message.
- `.Image(file: bytes, stream: bool = False, filename: str = None)`: Sends an image message, supports streaming upload and custom filenames.
- `.Video(file: bytes, stream: bool = False, filename: str = None)`: Sends a video message, supports streaming upload and custom filenames.
- `.File(file: bytes, stream: bool = False, filename: str = None)`: Sends a file message, supports streaming upload and custom filenames.
- `.Batch(target_ids: List[str], message: str, content_type: str = "text", **kwargs)`: Sends messages in batch.
- `.Edit(msg_id: str, text: str, content_type: str = "text", buttons: List = None)`: Edits an existing message.
- `.Recall(msg_id: str)`: Recalls a message.
- `.Board(content: str, content_type: str = "text")`: Publishes an announcement board. The scope is inferred by `To()` (target specified = local board, not specified = global board). Chained modifiers: `.Expire(duration)` relative expiration (seconds), `.ExpireAt(timestamp)` absolute expiration (second-level timestamp), `.ForMember(member_id)` group member board; **automatically converts to revoking the board when content is empty**. The legacy explicit scope style `Board("local", "Announcement")` remains compatible.
- `.DismissBoard()`: Revokes an announcement board. The scope is likewise inferred by `To()`, and `.ForMember(member_id)` is supported; the legacy `DismissBoard("local")` style remains compatible.
- `.Stream(content_type: str, content_generator: AsyncGenerator, **kwargs)`: Sends a streaming message.

### Group Management Methods

All group management methods require specifying the group via chained syntax, for example:
```python
from ErisPulse.Core import adapter
yunhu = adapter.get("yunhu")

await yunhu.Send.To("group", group_id).Kick(user_id)
```

- `.Kick(user_id: str)`: Removes a group member. The bot needs the `Allow removing group members` permission.
- `.Ban(user_id: str, duration: int = 600)`: Mutes a user. `duration` is the mute duration (seconds); 0 means unmute, -1 means permanent mute. The bot needs the `Allow muting users` permission.
- `.CreateTag(tag: str, color: str = None, desc: str = None, sort: int = None)`: Creates a group tag. The `color` format is #RRGGBB, and a smaller `sort` value places the tag earlier. The bot needs the `Allow controlling tag groups` permission.
- `.EditTag(tag: str, new_tag: str = None, color: str = None, desc: str = None, sort: int = None)`: Modifies a group tag. All parameters are optional; unspecified ones are left unchanged. The bot needs the `Allow controlling tag groups` permission.
- `.DeleteTag(tag: str)`: Deletes a group tag. The bot needs the `Allow controlling tag groups` permission.
- `.GetTagList()`: Gets the group tag list. Returns response data containing a `list` array.
- `.AddUserTag(user_id: str, tag: str)`: Adds a tag to a user. The bot needs the `Allow controlling tag groups` permission.
- `.RemoveUserTag(user_id: str, tag: str)`: Removes a tag from a user. The bot needs the `Allow controlling tag groups` permission.
- `.SetMsgTypeLimit(types: str)`: Controls message types within the group. `types` is the message type name; multiple types are separated by commas (e.g. `"text,image,video"`), and an empty string means no restriction. The bot needs the `Allow modifying group information` permission.

### Message Query Methods

To get the historical message list of a specified conversation (user/group), you need to specify the target via chained syntax, for example:
```python
from ErisPulse.Core import adapter
yunhu = adapter.get("yunhu")

result = await yunhu.Send.To("group", group_id).GetMessages(before=10)
```

- `.GetMessages(message_id: str = None, before: int = None, after: int = None)`: Gets conversation history messages. Returns response data containing a `list` array and a `total` count.
  - `message_id`: Message ID (optional). When omitted, combined with `before` it returns the most recent N messages.
  - `before`: Returns the N messages before the specified message ID.
  - `after`: Returns the N messages after the specified message ID.
  - > **Note:** At least one of `before` and `after` must be specified and greater than 0; otherwise the server will not return any messages.

The Board scope is automatically inferred by `To()`:
- Specifying `To(target_type, target_id)` → local board (specified user/group)
- Not specifying `To()` → global board

```python
# Local board (relative expiration after 60 seconds)
await yunhu.Send.To("group", group_id).Expire(60).Board("Announcement", content_type="markdown")

# Group member board (visible only to the specified member)
await yunhu.Send.To("group", group_id).ForMember(user_id).Board("Visible only to you")

# Absolute timestamp expiration
await yunhu.Send.To("group", group_id).ExpireAt(1785208268).Board("Expires at specified time")

# Global board
await yunhu.Send.Board("Global announcement")

# Clear the local board (empty content → automatic revoke)
await yunhu.Send.To("group", group_id).Board("")
```

### Button Parameter Description

The `buttons` parameter is a nested list representing the layout and functionality of buttons. Each button object contains the following fields:

| Field        | Type   | Required | Description                                                          |
|--------------|--------|----------|----------------------------------------------------------------------|
| `text`       | string | Yes      | Text on the button                                                   |
| `actionType` | int    | Yes      | Action type:<br>`1`: Open URL<br>`2`: Copy<br>`3`: Click report      |
| `url`        | string | No       | Used when `actionType=1`, indicating the target URL to open          |
| `value`      | string | No       | When `actionType=2`, this value is copied to the clipboard<br>When `actionType=3`, this value is sent to the subscriber |

Example:
```python
buttons = [
    [
        {"text": "Copy", "actionType": 2, "value": "xxxx"},
        {"text": "Click to open", "actionType": 1, "url": "http://www.baidu.com"},
        {"text": "Report event", "actionType": 3, "value": "xxxxx"}
    ]
]
await yunhu.Send.To("user", user_id).Buttons(buttons).Text("Message with buttons")
```
> **Note:**
> - Push notifications are only received when the user clicks the **button report event** button; **copy** and **open URL** buttons cannot trigger push notifications.

### Chained Modifier Methods (Composable)

Chained modifier methods return `self`, support chained calls, and must be called before the final send method:

- `.Reply(message_id: str)`: Replies to the specified message.
- `.At(user_id: str)`: Mentions the specified user.
- `.AtAll()`: Mentions everyone.
- `.Buttons(buttons: List)`: Adds buttons.

### Chained Call Examples

```python
# Basic send
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

# Modify a group tag
await yunhu.Send.To("group", group_id).EditTag("VIP User", new_tag="SVIP User", color="#33C4FF")

# Delete a group tag
await yunhu.Send.To("group", group_id).DeleteTag("VIP User")

# Get the group tag list
result = await yunhu.Send.To("group", group_id).GetTagList()

# Add a tag to a user
await yunhu.Send.To("group", group_id).AddUserTag(user_id, "VIP User")

# Remove a user's tag
await yunhu.Send.To("group", group_id).RemoveUserTag(user_id, "VIP User")

# Set a message type restriction
await yunhu.Send.To("group", group_id).SetMsgTypeLimit("text,image,video")

# Cancel the message type restriction
await yunhu.Send.To("group", group_id).SetMsgTypeLimit("")
```

### Message Query Examples

```python
from ErisPulse.Core import adapter
yunhu = adapter.get("yunhu")

# Get the 10 most recent group messages (10 returned in total)
result = await yunhu.Send.To("group", group_id).GetMessages(before=10)

# Get the 10 messages before a specified message ID in the group (11 returned in total)
result = await yunhu.Send.To("group", group_id).GetMessages(message_id="msg_xxx", before=10)

# Get 10 messages before and after a specified message ID in the group (21 returned in total)
result = await yunhu.Send.To("group", group_id).GetMessages(message_id="msg_xxx", before=10, after=10)

# Get user conversation history messages
result = await yunhu.Send.To("user", user_id).GetMessages(message_id="msg_xxx", before=10)
```

### OneBot12 Message Support

The adapter supports sending messages in OneBot12 format for cross-platform message compatibility:

- `.Raw_ob12(message: List[Dict], **kwargs)`: Sends a message in OneBot12 format.

```python
# Send a message in OneBot12 format
ob12_msg = [{"type": "text", "data": {"text": "Hello"}}]
await yunhu.Send.To("user", user_id).Raw_ob12(ob12_msg)

# Combined with chained modifiers
ob12_msg = [{"type": "text", "data": {"text": "Reply message"}}]
await yunhu.Send.To("group", group_id).Reply(msg_id).Raw_ob12(ob12_msg)
```

## Standard API Actions (ApiDSL)

> [!NOTE]
> This feature requires ErisPulse **2.7.0+** and YunhuAdapter **4.3.0+**.

In addition to `Send` chained sending, the adapter also provides an `Api` inner class exposing OneBot12 standard API actions and Yunhu platform extension actions. All methods return the standard response format.

```python
from ErisPulse.Core import adapter
yunhu = adapter.get("yunhu")

# Information queries (via public Web API, no authentication required)
result = await yunhu.Api.get_self_info()              # Bot's own information
result = await yunhu.Api.get_user_info("7058262")     # Any user's information
result = await yunhu.Api.get_group_info("635409929")  # Group information

# File operations
result = await yunhu.Api.upload_file(type="path", name="a.png", path="./a.png")
result = await yunhu.Api.get_file("https://chat-file.jwznb.com/xxx")

# Recall a message (chat_id + chat_type additionally required)
await yunhu.Api.delete_message("msg_id", chat_id="123", chat_type="group")

# Multi-account: specify a Bot account
info = await yunhu.Api.Using("bot1").get_self_info()
```

### Supported Standard Actions

| Method | Description | Data Source |
|------|------|---------|
| `get_self_info()` | Bot's own information | Public Web API (bot-info) |
| `get_user_info(user_id)` | User information (any user queryable) | Public Web API (user/homepage) |
| `get_group_info(group_id)` | Group information | Public Web API (group-info) |
| `upload_file(*, type, name, ...)` | Upload a file (automatically determines image/video/file) | Bot Open API |
| `get_file(file_id)` | Get a file (file_id is the URL; automatically downloads with Referer and returns base64) | Proxied download |
| `delete_message(message_id, *, chat_id, chat_type)` | Recall a message | Bot Open API (/bot/recall) |

#### Media Messages and Hotlink Protection (4.6.3)

The Yunhu media CDN (`chat-img.jwznb.com`, etc.) has **Referer hotlink protection** enabled: bare `GET` requests always receive `403`, and requests must carry `Referer: https://im.jwzhd.com/`.

- When media messages (image/video/file/audio) are received, the media segment within the event already carries this value in `data.headers.Referer`; modules performing their own downloads should include this header
- Or directly use `call_api("get_file", file_id=<url>)`; the adapter proxies the download and returns base64 (automatically handling hotlink protection)

```python
seg = event["message"][0]          # {"type": "image", "data": {...}}
img = await bot.call_api("get_file", file_id=seg["data"]["url"])
raw_bytes = base64.b64decode(img["data"]["base64"])
```

> **Note**: `get_self_info` / `get_user_info` / `get_group_info` are implemented via **unofficial public Web APIs** (chat-web-go.jwzhd.com). These endpoints require no authentication but are not officially documented and may change with platform updates; they return a standard error response on failure.

### Unsupported Standard Actions

The following standard actions have no corresponding Yunhu API and return `retcode=10002` (unsupported operation) when called:
- `get_friend_list` (the Bot Open API's "bot user list" is still pending launch)
- `get_group_list` / `get_group_member_info` / `get_group_member_list`
- `set_group_name` / `leave_group`

### Platform Extension Actions

Call Yunhu-specific actions via `Api.call("yunhu.xxx", **params)` (parameters use OB12-style naming; the adapter automatically translates them into Yunhu fields):

| Extension Action | Description | Equivalent Send Method |
|---------|------|---------------|
| `yunhu.recall` | Recall a message (msg_id, chat_id, chat_type) | `Send.To(...).Recall(msg_id)` |
| `yunhu.kick` | Remove a group member (group_id, user_id) | `Send.To("group", g).Kick(uid)` |
| `yunhu.ban` | Mute (group_id, user_id, duration) | `Send.To("group", g).Ban(uid, duration)` |
| `yunhu.unban` | Unmute (group_id, user_id) | `Send.To("group", g).Ban(uid, duration=0)` |
| `yunhu.tag.create/edit/delete/list` | Group tag CRUD (group_id, ...) | `Send.To("group", g).CreateTag(...)` etc. |
| `yunhu.tag.relate` / `yunhu.tag.relate_cancel` | Add/remove a tag for a user | `Send.To("group", g).AddUserTag(...)` etc. |
| `yunhu.set_member_title` / `yunhu.unset_member_title` | **Semantic aliases for member titles** (tag ≈ title, internally mapped to tag.relate) | — |
| `yunhu.msg_type_limit` | Group message type restriction (group_id, type) | `Send.To("group", g).SetMsgTypeLimit(...)` |
| `yunhu.get_messages` | Get history messages (chat_id, chat_type, message_id?, before?, after?) | `Send.To(...).GetMessages(...)` |
| `yunhu.bot_info` | Public bot-info query (bot_id) | — |
| `yunhu.user_homepage` | Public user homepage query (user_id) | — |

```python
# Platform extension examples
await yunhu.Api.call("yunhu.kick", group_id="123", user_id="456")
await yunhu.Api.call("yunhu.set_member_title", group_id="123", user_id="456", title="VIP")
result = await yunhu.Api.call("yunhu.get_messages", chat_id="123", chat_type="group", before=10)
```

> **Tags and titles**: Yunhu's "tag" semantics are equivalent to the OneBot12 group member `title`. `yunhu.set_member_title` is a native semantic alias of `yunhu.tag.relate`; both internally map to the same endpoint. In group message events, the sender role is mapped from `senderUserLevel` to the standard `role` field (owner/admin/member).

## Send Method Return Values

All send methods return a Task object that can be awaited directly to obtain the send result. The returned result follows the ErisPulse adapter standardized return specification:

```python
{
    "status": "ok",           // Execution status
    "retcode": 0,             // Return code
    "data": {...},            // Response data (self_info contains bot_id, see "Response Structure Adjustment")
    "message_id": "123456",   // Message ID
    "message": "",            // Error message
    "yunhu_raw": {...}        // Raw response data
}
```

> **4.6.2 changes**: the non-standard top-level `self` field of the original response has been moved into `data.self_info`. To get the bot_id, use `result["data"]["self_info"]["user_id"]` instead.

## Platform-Specific Event Types

You need to detect platform=="yunhu" before using these platform-specific features

### Core Differences

1. Platform-specific event types:
    - Forms (e.g. form commands): yunhu_form
    - Emoji/sticker message segment: yunhu_expression
    - Button click: yunhu_button_click
    - A2UI button click: yunhu_a2ui_button
    - Bot settings: yunhu_bot_setting
    - Shortcut menu: yunhu_shortcut_menu
2. Standard field extensions (4.3.0+):
    - Message events add a standard `role` field (mapped from Yunhu `senderUserLevel` to `owner`/`admin`/`member`)
    - New `user_avatar` field (sender avatar URL)
3. Extension fields:
    - All platform-specific fields are prefixed with yunhu_
    - Raw data is preserved in the yunhu_raw field
    - In private chats, self.user_id represents the bot ID

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
      "FieldID1": {
        "id": "FieldID1",
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
  "user_id": "ID of the user who clicked the button",
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
  "user_id": "ID of the operating user",
  "user_nickname": "User nickname",
  "message_id": "Message ID",
  "yunhu_a2ui": {
    "recv_id": "Receiver ID",
    "recv_type": "Receiver type",
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
    """Handle Yunhu notification events

    Use the generic on_notice() decorator to handle all notification events,
    then distinguish different notification types via detail_type
    event.reply() will automatically reply via the Yunhu platform
    """

# Check whether it is a button click event
    if event.get("detail_type") == "yunhu_button_click":
        user_id = event.get_user_id()
        user_nickname = event.get_user_nickname()
        button_value = event.get("yunhu_button", {}).get("value", "")

        print(f"User {user_nickname}({user_id}) clicked the button: {button_value}")

# Use event.reply() for automatic reply (it automatically selects the correct send method based on the platform)
        if button_value == "confirm":
            await event.reply("You clicked the confirm button!")
        elif button_value == "cancel":
            await event.reply("Operation cancelled")
        else:
            await event.reply(f"Received your choice: {button_value}")

# Handle shortcut menu events
    elif event.get("detail_type") == "yunhu_shortcut_menu":
        menu_id = event.get("yunhu_menu", {}).get("id", "")
        await event.reply(f"Shortcut menu triggered: {menu_id}")

# Handle bot setting changes
    elif event.get("detail_type") == "yunhu_bot_setting":
        settings = event.get("yunhu_setting", {})
        await event.reply(f"Settings updated: {settings}")

# Handle A2UI button events
    elif event.get("detail_type") == "yunhu_a2ui_button":
        a2ui = event.get("yunhu_a2ui", {})
        action_name = a2ui.get("action_name", "")
        form_context = a2ui.get("form_context", {})
        await event.reply(f"A2UI action: {action_name}, form data: {form_context}")
```

### Sending Messages with Buttons via Chained Calls

```python
from ErisPulse import sdk

yunhu = sdk.adapter.get("yunhu")

buttons = [
    [
        {"text": "Confirm", "actionType": 3, "value": "confirm"},
        {"text": "Cancel", "actionType": 3, "value": "cancel"},
        {"text": "View details", "actionType": 1, "url": "http://example.com/detail"}
    ]
]

# Send a message with buttons to a group
await yunhu.Send.To("group", "123456").Buttons(buttons).Text("Please confirm the following operation")

# Send a message with buttons to a user in private chat
await yunhu.Send.To("user", "789").Buttons(buttons).Text("Please select your preference settings")
```

### Sending A2UI Messages

```python
from ErisPulse import sdk

yunhu = sdk.adapter.get("yunhu")

# Send an A2UI message
await yunhu.Send.To("user", user_id).A2UI("A2UI interactive card content")
```

# Bot Settings
{
  "type": "notice",
  "detail_type": "yunhu_bot_setting",
  "group_id": "Group ID (may be empty)",
  "user_nickname": "User nickname",
  "yunhu_setting": {
    "Setting item ID": {
      "id": "Setting item ID",
      "type": "input/radio/checkbox/select/switch",
      "value": "Setting value"
    }
  }
}

# Shortcut Menu
{
  "type": "notice",
  "detail_type": "yunhu_shortcut_menu",
  "user_id": "ID of the user who triggered the menu",
  "user_nickname": "User nickname",
  "group_id": "Group ID (if it is a group chat)",
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
| `get_raw_event()` | `dict` | Get the Yunhu raw event data (`yunhu_raw`) |
| `get_sender_level()` | `str` | Sender's Yunhu native level (owner/administrator/member/unknown) |
| `get_sender_role()` | `str` | Sender's OneBot12 standard role (owner/admin/member) |
| `get_sender_title()` | `str` | Sender's title (standard `title` field accessor, reserved) |
| `get_sender_avatar()` | `str` | Sender's avatar URL |
| `get_command()` | `dict` | Command data (command message events only, `yunhu_command`) |
| `get_button_value()` | `str` | The value of the button click event (`yunhu_button.value`) |
| `get_a2ui_action()` | `str` | The actionName of the A2UI button event |
| `get_a2ui_form_context()` | `dict` | The form context of the A2UI button event |
| `get_menu_id()` | `str` | Shortcut menu event ID (`yunhu_menu.id`) |
| `get_setting()` | `dict` | Settings data of the bot setting event (`yunhu_setting`) |
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

## Extension Field Description

- All platform-specific fields are prefixed with `yunhu_` to avoid conflicts with standard fields
- Raw data is preserved in the `yunhu_raw` field for easy access to the complete raw data of the Yunhu platform
- `self.user_id` represents the bot ID (obtained from the bot_id in the configuration)
- Form commands provide structured data via the `yunhu_command` field
- Button click events provide button-related information via the `yunhu_button` field
- A2UI button events provide A2UI interaction-related information via the `yunhu_a2ui` field
- Bot setting changes provide setting item data via the `yunhu_setting` field
- Shortcut menu operations provide menu-related information via the `yunhu_menu` field
- Emoji/sticker messages provide sticker data via the `yunhu_expression` message segment (sticker_id, sticker pack ID, image dimensions, etc.)

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
|------|------|------|
| `sticker_id` | string | Unique sticker identifier |
| `sticker_pack_id` | string | Sticker pack ID |
| `expression_id` | string | Emoji ID |
| `image_name` | string | Emoji image file path |
| `width` | int | Image width (optional) |
| `height` | int | Image height (optional) |

Usage example:
```python
from ErisPulse.Core.Event import message

@message.on_message()
async def handle_message(event):
    if event.get_platform() == "yunhu":
        for segment in event.get("message", []):
            if segment.get("type") == "yunhu_expression":
                data = segment["data"]
                print(f"Received emoji: sticker_id={data['sticker_id']}, pack ID={data['sticker_pack_id']}")
```

---

## Multi-Bot Configuration

### Configuration Description

The Yunhu adapter supports configuring and running multiple Yunhu bot accounts simultaneously.

```toml
# config.toml
[Yunhu_Adapter.accounts.bot1]
token = "your_bot1_token"  # Bot token (required)
mode = "ws"  # Receive mode (optional, defaults to "ws"; options: "ws", "webhook")
webhook_path = "/webhook/bot1"  # Webhook path (optional, defaults to "/webhook")
enabled = true  # Whether to enable (optional, defaults to true)

[Yunhu_Adapter.accounts.bot2]
token = "your_bot2_token"  # The second bot's token
webhook_path = "/webhook/bot2"  # Independent webhook path
enabled = true
```

**Configuration item descriptions:**
- `token`: The API token provided by the Yunhu platform (required)
- `mode`: Receive mode (optional, defaults to `"ws"`; options `"ws"`, `"webhook"`)
- `webhook_path`: The HTTP path for receiving Yunhu events (optional, defaults to "/webhook", used only in webhook mode)
- `enabled`: Whether to enable this account (optional, defaults to true)

**Important notes:**
1. The Yunhu platform bot ID is **automatically detected at runtime**; there is no need to specify it in the configuration
2. In webhook mode, each bot should have its own independent `webhook_path` so it can receive its respective webhook events
3. When configuring the webhook on the Yunhu platform, please configure the corresponding URL for each bot, for example:
   - Bot1: `https://your-domain.com/webhook/bot1`
   - Bot2: `https://your-domain.com/webhook/bot2`

### Specifying a Bot with the Send DSL

You can specify which bot to use for sending messages via the `Using()` method. This method supports two kinds of parameters:
- **Account name**: the bot name in the configuration (e.g. `bot1`, `bot2`)
- **bot_id**: the `bot_id` value in the configuration

```python
from ErisPulse.Core import adapter
yunhu = adapter.get("yunhu")

# Send a message using the account name
await yunhu.Send.Using("bot1").To("user", "user123").Text("Hello from bot1!")

# Send a message using bot_id (automatically matches the corresponding account)
await yunhu.Send.Using("30535459").To("group", "group456").Text("Hello from bot!")

# When not specified, the first enabled bot is used
await yunhu.Send.To("user", "user123").Text("Hello from default bot!")
```

> **Tip:** When using `bot_id`, the system automatically looks up the matching account in the configuration. This is especially useful when handling event replies, where you can directly use `event["self"]["user_id"]` to reply with the same account.

### Bot Identification in Events

Received events automatically include the corresponding `bot_id` information (from 4.6.2 onward, the internal account name `self.account_id` is also injected):

```python
from ErisPulse.Core.Event import message

@message.on_message()
async def handle_message(event):
    if event["platform"] == "yunhu":
        # Get the bot ID that triggered the event
        bot_id = event["self"]["user_id"]
        account_id = event["self"].get("account_id", "")  # Internal account name (e.g. bot1)
        print(f"Message from Bot: {bot_id} (account: {account_id})")

        # Since 4.6.2, event.reply() automatically routes to the receiving account; just reply directly
        await event.reply("Reply message")

        # You can still explicitly specify the account for sending
        yunhu = adapter.get("yunhu")
        await yunhu.Send.Using(bot_id).To(
            event["detail_type"],
            event["user_id"] if event["detail_type"] == "private" else event["group_id"]
        ).Text("Reply message")
```

> **Tip**: `call_api` supports dual-compatible account fields: `account_id` (standard name) and `_account_id` (legacy name). Both the framework ApiDSL's `Using()` and the event account fallback (`send_context`) adapt automatically.

### Log Information

The adapter automatically includes `bot_id` information in logs for easier debugging and tracing:

```
[INFO] [yunhu] [bot:30535459] Received a private message from user user123
[INFO] [yunhu] [bot:12345678] Message sent successfully, message_id: abc123
```

### Management Interface

```python
# Get all account information
bots = yunhu.bots

# Check whether an account is enabled
bot_status = {
    bot_name: bot_config.enabled
    for bot_name, bot_config in yunhu.bots.items()
}

# Dynamically enable/disable an account (adapter restart required)
yunhu.bots["bot1"].enabled = False
```

### Legacy Configuration Compatibility

The legacy `[Yunhu_Adapter.bots.*]` configuration (with the `bot_id` field) is automatically migrated to the `accounts` format (`bot_id` is now automatically detected at runtime, and the value in the configuration is ignored); migrating to the new format as soon as possible is recommended.