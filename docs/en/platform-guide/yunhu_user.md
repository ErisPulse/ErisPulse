# Yunhu User Adapter Feature Documentation

YunhuUserAdapter is an adapter built based on the Yunhu user account protocol, which enables login through user email accounts, receives events via WebSocket, and provides a unified interface for event handling and message operations.

---

## Document Information

- Corresponding Module Version: 4.6.1
- Maintainer: wsu2059
- Last Updated: 2026-11-10

## Basic Information

- Platform Overview: Yunhu is an enterprise-level instant messaging platform. This adapter interacts with it via **user accounts** (not bot accounts).
- Adapter Name: YunhuUserAdapter
- Multi-account Support: Supports identifying and configuring multiple user accounts by account name.
- Chainable Modifier Support: Supports chainable modifier methods such as `.Reply()`.
- OneBot12 Compatibility: Supports sending messages in OneBot12 format.
- Communication Method: Uses email login to obtain a token, receives events via WebSocket, and sends messages using HTTP + Protobuf protocol.
- Session Types: Supports private chat (`user`), group chat (`group`), and bot session (`chat_type=3`, mapped to `private` since 4.6.1).

## v5 Paradigm Update (4.2.0)

- **BaseConverter Inheritance**; **spawn_background Task Assignment** (WS listening task)
- **Full User API Set** (based on yhchatAPI full.proto / v1 endpoint, protobuf over HTTP):
  - User: `get_user` / `edit_nickname` / `edit_avatar`
  - Friends: Address book / request list / apply / agree / ignore / delete
  - Groups: Group info / member list / create / dismiss / invite / remove / mute / bot list
  - Conversations: Conversation list; Messages: list / recall / button report
- **Framework Soft Dependency**: Runtime detection of ErisPulse>=2.7.1 with prompt; outputs version logs on startup

## Features Already Connected to the Platform

### Event Reception (WebSocket, protobuf encoding)

| WS cmd | Event | Description |
|--------|-------|-------------|
| `push_message` | `message` | Private chat/group chat/Bot session messages (text/HTML/Markdown/image/video/audio/file/emoji/article/sticker/button/A2UI) |
| `edit_message` | `notice` (`message_edit`) | Message edit notification |
| `file_send_message` | `notice` (`yunhu_user_file_send`) | Super file sharing |
| `bot_board_message` | `notice` (`yunhu_user_bot_board`) | Bot announcement board |

### Api DSL Method Mapping (YunhuHTTPClient → User API v1 endpoint)

| Category | Api Method | Endpoint | Description |
|----------|------------|----------|-------------|
| Account | `get_self_info()` | `/user/info` | Logged-in user information (nickname/avatar/user_id) |
| User | `get_user(user_id)` | `/user/get-user` | User details |
| User | `edit_nickname(nickname)` | `/user/edit-nickname` | Change own nickname |
| User | `edit_avatar(url)` | `/user/edit-avatar` | Change own avatar |
| Friends | `get_friend_address_book(md5)` | `/friend/address-book-list` | Address book (cursor pagination) |
| Friends | `get_friend_requests()` | `/friend/request-list` | Friend/group join application list |
| Friends | `friend_apply(user_id, desc)` | `/friend/apply` | Apply to add friend |
| Friends | `friend_agree_apply(user_id)` | `/friend/agree-apply` | Agree to friend application |
| Friends | `friend_ignore_apply(user_id)` | `/friend/ignore-apply` | Ignore friend application |
| Friends | `friend_delete(user_id)` | `/friend/delete-friend` | Delete friend |
| Groups | `get_group_info(group_id)` | `/group/info` | Group information |
| Groups | `get_group_member_list(group_id)` | `/group/list-member` | Group member list (supports keyword) |
| Groups | `create_group(name, ...)` | `/group/create-group` | Create group |
| Groups | `dismiss_group(group_id)` | `/group/dismiss-group` | Dismiss group |
| Groups | `group_invite(group_id, user_ids)` | `/group/invite` | Invite into group |
| Groups | `group_remove_member(group_id, user_id)` | `/group/remove-member` | Remove group member |
| Groups | `group_gag_member(group_id, user_id, seconds)` | `/group/gag-member` | Mute group member (0=unmute) |
| Groups | `get_group_bot_list(group_id)` | `/group/bot-list` | List of bots in group |
| Conversations | `get_conversation_list(md5)` | `/conversation/list` | Conversation list (cursor pagination) |
| Messages | `get_message_list(chat_id, chat_type, ...)` | `/msg/list-message` | Message list (various pagination variants available in HTTP client) |
| Messages | `delete_message(msg_id, chat_id, chat_type)` | `/msg/recall-msg` | Recall message (batch recall available in HTTP client) |
| Messages | `button_report(...)` | `/msg/button-report` | Button click report |
| Meta Actions | `get_status` / `get_version` / `get_supported_actions` | - | Runtime status/version/supported actions |

### Not Yet Connected (endpoints known, full.proto messages complete, can be extended as needed)

- User: Verification code login, badges, gold bean records, bind phone/email, notification settings, user data storage
- Friends: Do not disturb (no-notify), delete request records
- Groups: Command list, categories, recommendations, live room, edit group info/group nickname/keywords, auto-approval on group join, file limit in group, event SSE
- Conversations: Pin/sort/delete, do not disturb
- Messages: Forward, A2UI submission, message list image retrieval, file download records
- Group tags: list / relate / relate-cancel / create / edit / delete / members (endpoints `/group-tag/*`)

> Extension method: Add methods in `YunhuHTTPClient` following existing patterns (`_proto_request` / `_json_request` generic wrapper), then expose in `Api` class. Endpoint and message definitions refer to `yhchatAPI/src/api/v1/*.md` and `yhchatAPI/src/full.proto`.

### User API Example

```python
from ErisPulse import sdk
yunhu_user = sdk.adapter.get("yunhu_user")

result = await yunhu_user.Api.get_self_info()
result = await yunhu_user.Api.get_friend_requests()          # Friend application list
await yunhu_user.Api.friend_agree_apply(user_id)             # Agree to friend application
result = await yunhu_user.Api.get_group_member_list(group_id)
result = await yunhu_user.Api.get_conversation_list()        # Conversation list
await yunhu_user.Api.delete_message(msg_id, chat_id, chat_type)  # Recall message
```

## Friend Application Handling (Added in 4.6.0)

Yunhu user-side WebSocket **does not push friend application events**. The adapter defaults to enabling polling to fetch application lists and synthesizes standard request events (following [Request Action Specification](../standards/request-action-spec.md)):

- **Account Configuration**: `poll_friend_requests = true` (default enabled), `poll_interval = 60` (polling interval in seconds, minimum 5 seconds); set to `false` to disable polling
- **Polling Logic**: Pulls `/friend/request-list` at intervals, diffing out **new applications** and synthesizing standard request events:
  - `type="request"`, `detail_type="friend"`
  - `request_id` = **applicant's user_id**
  - `user_nickname` / `comment` from application data, original entries preserved in `yunhu_user_raw`
- **Event Deduplication**: Processed applications will not be re-issued as events

### Approval via Module Side (Event-based)

```python
from ErisPulse.Core.Event import request

@request.on_friend_request()
async def handle_friend_request(event):
    if event.get("platform") != "yunhu_user":
        return

    applicant = event.get("user_id")
    nickname = event.get("user_nickname", "")
    comment = event.get("comment", "")
    print(f"Friend application: {nickname}({applicant}) with comment: {comment}")

    # Approve friend application (accept = approve friend)
    await event.approve()
    # Or ignore application (reject = ignore)
    # await event.reject()
```

### Direct Call via Adapter (Request DSL)

```python
from ErisPulse.Core import adapter
yunhu_user = adapter.get("yunhu_user")

# request_id is the applicant's user_id
await yunhu_user.Request("applicant_user_id").accept()   # accept = approve friend
await yunhu_user.Request("applicant_user_id").reject()   # reject = ignore application

# Multi-account: specify account for approval
await yunhu_user.Request("applicant_user_id").Using("default").accept()
```

> `accept()` internally calls `/friend/agree-apply`, `reject()` calls `/friend/ignore-apply`; both return standard responses (`status` / `retcode` / `message` / `yunhu_user_raw`).

## Standardization Alignment (4.6.1)

Response structure and error codes follow [API Response Specification](../standards/api-response.md).

### Standard Response

Api DSL 20 methods uniformly return standard responses: `status` / `retcode` / `data` / `message_id` / `message`, with platform raw data also present in `data` and top-level `yunhu_user_raw`. Raw data from `get_self_info` is moved to the top-level response `yunhu_user_raw`.

### Error Code Specification

| retcode | Meaning | Description |
|---------|---------|-------------|
| 0 | Success | — |
| 33001 | Network Error | HTTP/WS connection-related exceptions |
| 34100 | Platform Failure | Yunhu user-side returned failure; raw response preserved in `yunhu_user_raw` |
| 10002 | Not Supported | Platform lacks corresponding capability for standard actions |
| 10003 | Parameter Error | Missing request_id, no available account, etc. |

### Event Field Corrections

- **`chat_type=3` (bot session) mapped to `private`** (original `"bot"` is non-standard; original chat_type preserved in `yunhu_user_raw`)
- **`edit_message` event id prefixed with `edit:`** to avoid duplicate id with create events and being deduplicated by downstream
- **`message_id` always present**: empty string as fallback if missing
- **Event `time` uses message timestamp** (seconds), not adapter processing time

### Account and Multi-account

- `call_api` supports dual-compatible account fields: `account_id` (standard name) / `_account_id` (old name), framework ApiDSL (`Api.Using(...)`) automatically adapts
- `Send` reads `send_context` (event account fallback): when calling `Send` from event context, default falls back to the source account
- Event replies are recommended to use `event.reply()`, which automatically routes to the handling account

---

## Supported Message Sending Types

All sending methods are implemented via chainable syntax, for example:
```python
from ErisPulse.Core import adapter
yunhu_user = adapter.get("yunhu_user")

await yunhu_user.Send.To("user", user_id).Text("Hello World!")
```

Supported sending types include:
- `.Text(text: str, buttons: Optional[List] = None)`: Send plain text message.
- `.Html(html: str, buttons: Optional[List] = None)`: Send HTML formatted message.
- `.Markdown(markdown: str, buttons: Optional[List] = None)`: Send Markdown formatted message.
- `.MergeForward(nodes, title="Merged Chat Record")`: Send merged forward message (rendered as `<details>` collapsed HTML card, sent via msg_type=8 HTML channel).
- `.Image(file: Union[str, bytes], buttons: Optional[List] = None)`: Send image message, supports URL, local path, or binary data.
- `.Video(file: Union[str, bytes], buttons: Optional[List] = None)`: Send video message, supports URL, local path, or binary data.
- `.Audio(file: Union[str, bytes], buttons: Optional[List] = None)`: Send voice message, supports URL, local path, or binary data, automatically detects audio duration.
- `.Voice(file: Union[str, bytes], buttons: Optional[List] = None)`: Alias for `.Audio()`.
- `.File(file: Union[str, bytes], file_name: Optional[str] = None, buttons: Optional[List] = None)`: Send file message, supports URL, local path, or binary data.
- `.Face(file: Union[str, bytes], buttons: Optional[List] = None)`: Send emoji/sticker message, supports sticker ID, sticker URL, or binary image data.
- `.A2ui(a2ui_data: Union[str, Dict, List], buttons: Optional[List] = None)`: Send A2UI message (msg_type=14), A2UI JSON data is filled into the text field for sending.
- `.Edit(msg_id: str, text: str, content_type: str = "text")`: Edit an existing message.
- `.Recall(msg_id: str)`: Recall message.
- `.Raw_ob12(message: Union[List, Dict])`: Send OneBot12 formatted message.

### Media File Handling

All media types (image, video, audio, file) support the following input methods:
- **URL**: `"https://example.com/image.jpg"` — automatically downloads and uploads
- **Local Path**: `"/path/to/file.jpg"` — automatically reads and uploads
- **Binary Data**: `open("file.jpg", "rb").read()` — directly uploads

Media files are automatically uploaded to Qiniu Cloud storage, supporting the following features:
- Automatic file type and MIME detection via `filetype` library
- Automatic file size calculation
- Automatic audio duration detection (supports MP3, MP4/M4A formats)

### Button Parameter Description

The `buttons` parameter is a nested list, representing button layout and functionality. Each button object contains the following fields:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `text` | string | Yes | Text on the button |
| `actionType` | int | Yes | Action type:<br>`1`: Navigate to URL<br>`2`: Copy<br>`3`: Click report |
| `url` | string | No | Used when `actionType=1`, indicating the target URL for navigation |
| `value` | string | No | When `actionType=2`, this value is copied to the clipboard<br>When `actionType=3`, this value is sent to the subscriber |

Example:
```python
buttons = [
    [
        {"text": "Copy", "actionType": 2, "value": "xxxx"},
        {"text": "Click to Navigate", "actionType": 1, "url": "http://www.baidu.com"},
        {"text": "Report Event", "actionType": 3, "value": "xxxxx"}
    ]
]
await yunhu_user.Send.To("user", user_id).Buttons(buttons).Text("Message with buttons")
```

### Chainable Modifier Methods (Can be Combined)

Chainable modifier methods return `self`, supporting chained calls, must be called before the final send method:

- `.Reply(message_id: str)`: Reply to a specific message.
- `.At(user_id: str)`: @ a specific user (text form @user_id).
- `.AtAll()`: @ everyone (pseudo-@all, sends @all text).
- `.Buttons(buttons: List)`: Add buttons.

> **Note:** Since user accounts are special, even non-admin users can @all, but here `AtAll()` only sends a text mentioning everyone, which is a pseudo-@all.

### Chained Call Examples

```python
# Basic send
await yunhu_user.Send.To("user", user_id).Text("Hello")

# Reply to message
await yunhu_user.Send.To("group", group_id).Reply(msg_id).Text("Reply message")

# Reply + buttons
await yunhu_user.Send.To("group", group_id).Reply(msg_id).Buttons(buttons).Text("Message with reply and buttons")

# Specify account + reply + buttons
await yunhu_user.Send.Using("default").To("group", group_id).Reply(msg_id).Buttons(buttons).Text("Complete chained call")
```

### OneBot12 Message Support

The adapter supports sending OneBot12 formatted messages, facilitating cross-platform message compatibility:

- `.Raw_ob12(message: List[Dict], **kwargs)`: Send OneBot12 formatted message.

```python
# Send OneBot12 formatted message
ob12_msg = [{"type": "text", "data": {"text": "Hello"}}]
await yunhu_user.Send.To("user", user_id).Raw_ob12(ob12_msg)

# Combined with chainable modifiers
ob12_msg = [{"type": "text", "data": {"text": "Reply message"}}]
await yunhu_user.Send.To("group", group_id).Reply(msg_id).Raw_ob12(ob12_msg)
```

Raw_ob12 supports automatic grouping of mixed message segments:
- `text`, `mention` types can be merged into one group
- `image`, `video`, `audio`, `file`, `face`, `markdown`, `html`, `a2ui` types each form independent groups
- `reply` type can be attached to any group

## Send Method Return Values

All send methods return a Task object, which can be awaited to get the send result. The return result follows ErisPulse adapter standardized return specification:

```python
{
    "status": "ok",           // Execution status
    "retcode": 0,             // Return code
    "data": {...},            // Response data
    "message_id": "123456",   // Message ID
    "message": "",            // Error message
    "yunhu_user_raw": {...}   // Raw response data
}
```

## Platform-Specific Event Types

Use `platform == "yunhu_user"` check before using platform-specific features.

### Core Differences

1. Platform-specific event types:
    - Super file sharing: `yunhu_user_file_send`
    - Bot announcement board: `yunhu_user_bot_board`
    - Message edit notification: `message_edit`
    - Message delete notification: `message_delete` (recall)
2. Platform-specific message segment types:
    - Form message segment: `yunhu_user_form`
    - Article message segment: `yunhu_user_post`
    - Sticker message segment: `yunhu_user_sticker`
    - Button message segment: `yunhu_user_button`
    - A2UI message segment: `a2ui`
3. Extended fields:
    - All platform-specific fields are prefixed with `yunhu_user_`
    - Original data preserved in `yunhu_user_raw` field
    - Original event type recorded in `yunhu_user_raw_type` field
    - In private chat, `self.user_id` indicates the current logged-in user ID

### Supported Raw Event Types

| Raw Event Type | OneBot12 Type | Description |
|----------------|---------------|-------------|
| `push_message` | `message` | Push message (private chat, group chat, bot session) |
| `edit_message` | `notice` (`message_edit`) | Message edit event |
| `file_send_message` | `notice` (`yunhu_user_file_send`) | Super file sharing event |
| `bot_board_message` | `notice` (`yunhu_user_bot_board`) | Bot announcement board event |

> Other event types (such as `heartbeat_ack`, `draft_input`, `stream_message`, etc.) are ignored.

### OneBot12 Supported detail_type

| OneBot12 detail_type | Yunhu chat_type | Description |
|----------------------|-----------------|-------------|
| `private` | 1 | Private chat message |
| `group` | 2 | Group chat message |
| `private` | 3 | Bot session (since 4.6.1 mapped to `private`, original `"bot"` non-standard; original chat_type preserved in `yunhu_user_raw`) |

### Message Event Example

```python
{
    "id": "event_id",
    "time": 1234567890,
    "type": "message",
    "detail_type": "group",
    "platform": "yunhu_user",
    "self": {
        "platform": "yunhu_user",
        "user_id": "your_user_id"
    },
    "message": [
        {"type": "text", "data": {"text": "Message content"}}
    ],
    "alt_message": "Message content",
    "user_id": "sender_user_id",
    "user_nickname": "Sender's nickname",
    "group_id": "group_id",
    "message_id": "msg_id",
    "yunhu_user_raw": {...},
    "yunhu_user_raw_type": "push_message"
}
```

### Message Edit Notification Example

```python
{
    "type": "notice",
    "detail_type": "message_edit",
    "platform": "yunhu_user",
    "self": {
        "platform": "yunhu_user",
        "user_id": "your_user_id"
    },
    "message_id": "msg_id",
    "user_id": "sender_user_id",
    "user_nickname": "Sender's nickname",
    "edit_time": 1234567890,
    "group_id": "group_id",
    "yunhu_user_raw": {...},
    "yunhu_user_raw_type": "edit_message"
}
```

### Super File Sharing Event Example

```python
{
    "type": "notice",
    "detail_type": "yunhu_user_file_send",
    "platform": "yunhu_user",
    "self": {
        "platform": "yunhu_user",
        "user_id": "your_user_id"
    },
    "user_id": "send_user_id",
    "user_nickname": "",
    "yunhu_user_file_send": {
        "send_user_id": "Sender ID",
        "user_id": "Recipient user ID",
        "send_type": "Send type",
        "data": "File data"
    },
    "yunhu_user_raw": {...},
    "yunhu_user_raw_type": "file_send_message"
}
```

### Bot Announcement Board Event Example

```python
{
    "type": "notice",
    "detail_type": "yunhu_user_bot_board",
    "platform": "yunhu_user",
    "self": {
        "platform": "yunhu_user",
        "user_id": "your_user_id"
    },
    "bot_id": "bot_id",
    "bot_name": "Bot name",
    "yunhu_user_bot_board": {
        "bot_id": "bot_id",
        "chat_id": "chat_id",
        "chat_type": 1,
        "content": "Announcement content",
        "content_type": 1,
        "last_update_time": 1234567890
    },
    "yunhu_user_raw": {...},
    "yunhu_user_raw_type": "bot_board_message"
}
```

### Event Handling Example

```python
from ErisPulse.Core.Event import message, notice

@message.on_message()
async def handle_yunhu_user_message(event):
    """Handle Yunhu user message"""
    if event.get("platform") != "yunhu_user":
        return
    
    user_id = event.get("user_id", "")
    user_nickname = event.get("user_nickname", "")
    alt_message = event.get("alt_message", "")
    
    print(f"User {user_nickname}({user_id}): {alt_message}")
    
    # Check for platform-specific message segment types
    for segment in event.get("message", []):
        seg_type = segment.get("type", "")
        
        if seg_type == "yunhu_user_form":
            form_data = segment["data"]["form"]
            print(f"Received form message: {form_data}")
        
        elif seg_type == "yunhu_user_post":
            post_data = segment["data"]
            print(f"Received article message: {post_data.get('post_title', '')}")
        
        elif seg_type == "yunhu_user_sticker":
            sticker_url = segment["data"]["file_id"]
            print(f"Received sticker message: {sticker_url}")
        
        elif seg_type == "yunhu_user_button":
            buttons = segment["data"]["buttons"]
            print(f"Message contains buttons: {buttons}")
        
        elif seg_type == "a2ui":
            a2ui_data = segment["data"]["a2ui"]
            print(f"Received A2UI message: {a2ui_data}")
    
    # Use event.reply() to automatically reply
    await event.reply(f"Echo: {alt_message}")

@notice.on_notice()
async def handle_yunhu_user_notice(event):
    """Handle Yunhu user notice events"""
    if event.get("platform") != "yunhu_user":
        return
    
    detail_type = event.get("detail_type", "")
    
    if detail_type == "message_edit":
        message_id = event.get("message_id", "")
        user_nickname = event.get("user_nickname", "")
        edit_time = event.get("edit_time", 0)
        print(f"User {user_nickname} edited message {message_id}")
    
    elif detail_type == "yunhu_user_file_send":
        file_data = event.get("yunhu_user_file_send", {})
        print(f"Received super file sharing: {file_data}")
    
    elif detail_type == "yunhu_user_bot_board":
        board_data = event.get("yunhu_user_bot_board", {})
        bot_name = event.get("bot_name", "")
        print(f"Bot {bot_name} published announcement: {board_data.get('content', '')}")
```

## Extended Field Description

- All platform-specific fields are prefixed with `yunhu_user_` to avoid conflicts with standard fields
- Original data is preserved in the `yunhu_user_raw` field, allowing access to complete raw data from the Yunhu platform
- Original event type is recorded in the `yunhu_user_raw_type` field (e.g., `push_message`, `edit_message`, etc.)
- `self.user_id` indicates the current logged-in user ID (obtained from login response)
- Super file sharing is provided through the `yunhu_user_file_send` field
- Bot announcement board is provided through the `yunhu_user_bot_board` field

### Platform-Specific Message Segment Types

#### Form Message Segment (yunhu_user_form)

When content_type is 5, the message segment type is `yunhu_user_form`:

```json
{
    "type": "yunhu_user_form",
    "data": {
        "form": "Form data"
    }
}
```

#### Article Message Segment (yunhu_user_post)

When content_type is 6, the message segment type is `yunhu_user_post`:

```json
{
    "type": "yunhu_user_post",
    "data": {
        "post_id": "Article ID",
        "post_title": "Article title",
        "post_content": "Article content"
    }
}
```

| Field | Type | Description |
|-------|------|-------------|
| `post_id` | string | Unique article identifier |
| `post_title` | string | Article title |
| `post_content` | string | Article content |

#### Sticker Message Segment (yunhu_user_sticker)

When content_type is 7, the message segment type is `yunhu_user_sticker`:

```json
{
    "type": "yunhu_user_sticker",
    "data": {
        "file_id": "Sticker image URL"
    }
}
```

| Field | Type | Description |
|-------|------|-------------|
| `file_id` | string | Sticker image URL |

#### Button Message Segment (yunhu_user_button)

When the message contains buttons, a `yunhu_user_button` message segment is attached:

```json
{
    "type": "yunhu_user_button",
    "data": {
        "buttons": [[{"text": "Button text", "actionType": 3, "value": "value"}]]
    }
}
```

#### A2UI Message Segment (a2ui)

When content_type is 14, the message segment type is `a2ui`:

```json
{
    "type": "a2ui",
    "data": {
        "a2ui": "A2UI JSON data"
    }
}
```

---

## Multi-account Configuration

### Configuration Description

YunhuUserAdapter supports configuring and running multiple user accounts simultaneously.

```toml
# config.toml
[YunhuUserAdapter]
ws_reconnect_interval = 30  # WebSocket reconnection interval (seconds)
ws_timeout = 70             # WebSocket timeout (seconds)

[YunhuUserAdapter.accounts.default]
email = "user1@example.com"  # User email (required)
password = "password1"       # User password (required)
platform = "windows"         # Login platform (optional, default windows)
device_id = ""               # Device ID (optional, auto-generated if not provided)
poll_friend_requests = true  # Poll friend requests (optional, default true)
poll_interval = 60           # Friend request polling interval (seconds, optional, default 60)
enabled = true               # Whether to enable (optional, default true)

[YunhuUserAdapter.accounts.account2]
email = "user2@example.com"
password = "password2"
platform = "android"
device_id = "fixed_device_id_2"
enabled = true
```

**Configuration Item Description:**
- `email`: User email (required), used to log in to the Yunhu platform
- `password`: User password (required)
- `platform`: Login platform identifier (optional, default `windows`), possible values: `windows`, `macos`, `linux`, `ios`, `android`
- `device_id`: Device ID (optional, auto-generated if not provided), it is recommended to provide a fixed value to maintain session consistency
- `poll_friend_requests`: Whether to poll friend requests (optional, default `true`; see "Friend Application Handling")
- `poll_interval`: Friend request polling interval (seconds, optional, default 60, minimum 5)
- `enabled`: Whether to enable this account (optional, default `true`)

**Adapter-level configuration:**
- `ws_reconnect_interval`: WebSocket reconnection interval (seconds, default 30)
- `ws_timeout`: WebSocket timeout (seconds, default 70)

**Important Notes:**
1. The adapter uses email login to obtain a token, and after login, it receives events via WebSocket
2. After a WebSocket connection is disconnected, it automatically reconnects, with a maximum of 3 retries
3. It is recommended to set a fixed `device_id` for each account to maintain session consistency
4. Unmodified template accounts (default email and password) will be automatically skipped

### Using Send DSL to Specify Account

You can specify which account to use for sending messages via the `Using()` method. This method supports two types of parameters:
- **Account name**: The account name in the configuration (e.g., `default`, `account2`)
- **user_id**: The user ID obtained after login

```python
from ErisPulse.Core import adapter
yunhu_user = adapter.get("yunhu_user")

# Send message using account name
await yunhu_user.Send.Using("default").To("user", "user123").Text("Hello from account1!")

# Send message using user_id (automatically matches corresponding account)
await yunhu_user.Send.Using("user_id_here").To("group", "group456").Text("Hello from user!")

# If not specified, use the first enabled account
await yunhu_user.Send.To("user", "user123").Text("Hello from default account!")
```

> **Tip:** When using `user_id`, the system automatically finds the matching account in the configuration. This is especially useful when handling event replies, where you can directly use `event["self"]["user_id"]` to reply from the same account.

### Account Information in Events

Events received automatically include the corresponding user ID information:

```python
from ErisPulse.Core.Event import message

@message.on_message()
async def handle_message(event):
    if event["platform"] == "yunhu_user":
        # Get the current logged-in user ID
        my_user_id = event["self"]["user_id"]
        print(f"Message from account: {my_user_id}")
        
        # Reply using the same account
        yunhu_user = adapter.get("yunhu_user")
        await yunhu_user.Send.Using(my_user_id).To(
            event["detail_type"],
            event["user_id"] if event["detail_type"] == "private" else event["group_id"]
        ).Text("Reply message")
```

### Log Information

The adapter automatically includes account information in logs, which is helpful for debugging and tracking:

```
[INFO] Account default (user1@example.com) login successful, user ID: 12345678
[INFO] Account default WebSocket listening task started
[INFO] Account account2 (user2@example.com) login successful, user ID: 87654321
```

### Management Interface

```python
# Get all account information
accounts = yunhu_user.accounts
# Return format: {"default": {"name": "default", "email": "...", "token": "...", "user_id": "...", ...}, ...}

# Check if account is enabled
for account_name, account_config in yunhu_user._account_configs.items():
    print(f"{account_name}: enabled={account_config.enabled}")

# Get HTTP client by account name
http_client = yunhu_user._get_http_client("default")

# Find account by user_id
account_name = yunhu_user._get_account_by_user_id("12345678")
```

## API Calls

The adapter provides a `call_api` method, supporting direct calls to the platform API:

```python
# Send message
result = await yunhu_user.call_api("/send", 
    target_type="group", 
    target_id="group_id",
    account_id="default",
    message={"text": "Hello", "msg_type": 1}
)

# Edit message
result = await yunhu_user.call_api("/edit",
    target_type="group",
    target_id="group_id",
    msg_id="msg_id",
    text="New content",
    content_type="text"
)

# Recall message
result = await yunhu_user.call_api("/recall",
    target_type="group",
    target_id="group_id",
    msg_id="msg_id"
)

# Batch recall message
result = await yunhu_user.call_api("/recall_batch",
    target_type="group",
    target_id="group_id",
    msg_id_list=["msg_id_1", "msg_id_2"]
)

# Get message list
result = await yunhu_user.call_api("/list",
    chat_id="group_id",
    chat_type=2,
    msg_count=10,
    msg_id=""
)

# Get message edit record
result = await yunhu_user.call_api("/list_edit_record",
    msg_id="msg_id",
    size=10,
    page=1
)

# Button event report
result = await yunhu_user.call_api("/button_report",
    chat_id="group_id",
    chat_type=2,
    msg_id="msg_id",
    user_id="user_id",
    button_value="button_value"
)
```

**Supported API Endpoints:**

| Endpoint | Description |
|----------|-------------|
| `/send` | Send message |
| `/edit` | Edit message |
| `/recall` | Recall message |
| `/recall_batch` | Batch recall message |
| `/list` | Get message list |
| `/list_by_seq` | Get message by sequence |
| `/list_by_mid_seq` | Get message by message ID and sequence |
| `/list_edit_record` | Get message edit record |
| `/button_report` | Button event report |