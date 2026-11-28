# Kook Platform Feature Documentation

KookAdapter is an adapter built based on the Kook (Open Black) Bot WebSocket protocol, integrating all Kook functional modules and providing a unified interface for event handling and message operations.

---

## Document Information

- Corresponding Module Version: 4.3.2
- Maintainer: ShanFish
- Last Updated: 2026-11-10

## Basic Information

- Platform Overview: Kook (formerly Open Black) is a community platform supporting text, voice, and video communication, providing a complete Bot development interface
- Adapter Name: KookAdapter
- Multi-account Support: Supports configuring multiple Kook bots simultaneously
- Connection Method: WebSocket long connection (via Kook gateway)
- Authentication Method: Identity authentication based on Bot Token
- Chainable Modifier Support: Supports chainable modifier methods such as `.Reply()`, `.At()`, `.AtAll()`
- OneBot12 Compatibility: Supports sending OneBot12 format messages

## Configuration Instructions

KookAdapter supports multi-account configuration, with each account corresponding to an independent Kook bot.

```toml
# config.toml
# Account 1
[KookAdapter.accounts.default]
token = "YOUR_BOT_TOKEN"     # Kook Bot Token (required, format: Bot xxx/xxx)
bot_id = ""                   # Bot user ID (optional, if not filled, parsed from token)
compress = true               # Whether to enable WebSocket compression (optional, default is true)
enabled = true                # Whether to enable (optional, default is true)

# Account 2
[KookAdapter.accounts.bot2]
token = "ANOTHER_BOT_TOKEN"
bot_id = ""
enabled = true
```

> Compatibility with old configuration: If an old single-account `[KookAdapter]` configuration (containing token) is detected, it will be automatically migrated to `accounts.default`.

**Configuration Item Description (per account):**
- `token`: Kook Bot's Token (required), obtained from [Kook Developer Center](https://developer.kookapp.cn), format is `Bot xxx/xxx`
- `bot_id`: Bot's user ID (optional), if not filled, the adapter will try to automatically parse it from the token. It is recommended to fill it manually to ensure accuracy
- `compress`: Whether to enable WebSocket data compression (optional, default is `true`), zlib is used to decompress data when enabled
- `enabled`: Whether to enable this account (optional, default is true)

**API Environment:**
- Kook API base address: `https://www.kookapp.cn/api/v3`
- WebSocket gateway is dynamically obtained via API: `POST /gateway/index`

## Standardization Alignment (4.3.2)

### Events and Accounts

- **Event `self.account_id` Injection**: All events carry the account name that generated them; in multi-account scenarios, `event.reply()` automatically handles replies based on that account

### Api Signature Alignment

| Action | Signature | Description |
|------|------|------|
| get_channel_info | `(guild_id, channel_id)` | New signature guild_id first parameter; when only one positional parameter is passed, old signature is compatible (treated as channel_id) |
| get_channel_member_list | `(guild_id, channel_id)` | Same compatibility rules as above |
| get_guild_info / get_guild_list | - | data uses `guild_id` / `guild_name` fields (old `group_*` fields are retained to avoid breaking existing callers) |

### Error Code Standardization

Error codes have been standardized according to the SDK, and Kook platform original error codes (401xx/4xxxx, etc.) are no longer directly used as retcode:

| retcode | Description |
|---------|------|
| 0 | Success (successful response `message` is empty string) |
| 33001 | Network error (request exception, account API instance not initialized, etc.) |
| 34100 | Platform error (Kook returns non-zero code; original response is preserved in `kook_raw`, original code is stored in `kook_code` field) |
| 10002 | Unsupported action (`get_guild_member_info` / `get_guild_member_list` / `set_guild_name` / `leave_guild` / `leave_channel` explicitly return; unknown API endpoint no longer throws an exception, returns 10002 uniformly) |

## v5 Paradigm Update (4.1.0)

This adapter has completed the v5 paradigm alignment (incremental upgrade, API compatible):

- **BaseConverter Inheritance**: Common fields of converters are built by framework `build_base_event`
- **Api DSL**: Standard API action mapping (see below)
- **Standard keyboard Segment**: `{"type": "keyboard", "data": {"rows": [[{"label", "type": "callback|link", "data"}]]}}` Text + keyboard automatically combined into Kook card message (section + action-group); .Keyboard(rows) modifier accepts generic structure
- **spawn_background Task Assignment**: Connection tasks use runtime.spawn_background
- **Framework Soft Dependency**: Runtime checks for ErisPulse>=2.7.1 and prompts; startup outputs version log

### Standard API Actions

```python
from ErisPulse import sdk
kook = sdk.adapter.get("kook")

result = await kook.Api.get_self_info()              # GET /users/@me
result = await kook.Api.get_user_info(user_id)       # POST /user/view
result = await kook.Api.get_guild_info(guild_id)     # POST /guild/view (data uses guild_id / guild_name)
result = await kook.Api.get_guild_list()             # POST /guild/list
result = await kook.Api.get_channel_info(guild_id, channel_id)  # POST /channel/view (new signature guild_id first parameter)
result = await kook.Api.get_channel_list(guild_id)   # POST /channel/list
await kook.Api.delete_message(msg_id)                # POST /message/delete
result = await kook.Api.Using("main").get_self_info()
```

### Buttons (keyboard)

```python
rows = [[{"label": "Option A", "type": "callback", "data": "vote:A"},
         {"label": "Official Site",  "type": "link",     "data": "https://example.com"}]]
await kook.Send.To("channel", channel_id).Keyboard(rows).Text("Please select")
# Text and buttons automatically combined into Kook card message (section + action-group)

# Button click callback (standard fields)
from ErisPulse.Core.Event import notice

@notice.on_notice()
async def handle_button(event):
    if event.get("platform") == "kook" and event.get("button_data"):
        data = event["button_data"]
```

---

## Supported Message Sending Types

All sending methods are implemented through chainable syntax, for example:
```python
from ErisPulse.Core import adapter
kook = adapter.get("kook")

await kook.Send.To("group", channel_id).Text("Hello World!")
```

The supported sending types include:
- `.Text(text: str)`: Send plain text message.
- `.Image(file: bytes | str)`: Send image message, supports file path, URL, binary data.
- `.Video(file: bytes | str)`: Send video message, supports file path, URL, binary data.
- `.File(file: bytes | str, filename: str = None)`: Send file message, supports file path, URL, binary data.
- `.Voice(file: bytes | str)`: Send voice message, supports file path, URL, binary data.
- `.Markdown(text: str)`: Send KMarkdown format message.
- `.Card(card_data: dict)`: Send card message (CardMessage).
- `.MergeForward(nodes, title="Merged Chat Record")`: Send merged forward message (rendered as card: header header + each message as a section, KMD escaped, ≤40 nodes).
- `.Raw_ob12(message: List[Dict], **kwargs)`: Send OneBot12 format message.

### Chainable Modifier Methods (can be combined)

Chainable modifier methods return `self`, support chained calls, must be called before the final sending method:

- `.Reply(message_id: str)`: Reply (quote) to a specified message.
- `.At(user_id: str)`: @ a specified user, can be called multiple times to @ multiple users.
- `.AtAll()`: @ everyone.

### Chainable Call Examples

```python
# Basic sending
await kook.Send.To("group", channel_id).Text("Hello")

# Reply to message
await kook.Send.To("group", channel_id).Reply(msg_id).Text("Reply message")

# @ user
await kook.Send.To("group", channel_id).At("user_id").Text("Hello")

# @ multiple users
await kook.Send.To("group", channel_id).At("user1").At("user2").Text("Multiple users@")

# @ all
await kook.Send.To("group", channel_id).AtAll().Text("Announcement")

# Combined usage
await kook.Send.To("group", channel_id).Reply(msg_id).At("user_id").Text("Composite message")
```

### OneBot12 Message Support

The adapter supports sending OneBot12 format messages, facilitating cross-platform message compatibility:

```python
# Send OneBot12 format message
ob12_msg = [{"type": "text", "data": {"text": "Hello"}}]
await kook.Send.To("group", channel_id).Raw_ob12(ob12_msg)

# Combined with chainable modifiers
ob12_msg = [{"type": "text", "data": {"text": "Reply message"}}]
await kook.Send.To("group", channel_id).Reply(msg_id).Raw_ob12(ob12_msg)

# Use mention and reply message segments in Raw_ob12
ob12_msg = [
    {"type": "text", "data": {"text": "Hello "}},
    {"type": "mention", "data": {"user_id": "user_id"}},
    {"type": "reply", "data": {"message_id": "msg_id"}}
]
await kook.Send.To("group", channel_id).Raw_ob12(ob12_msg)
```

### Additional Operation Methods

In addition to sending messages, the Kook adapter also supports the following operations:

```python
# Edit message (only supports KMarkdown type=9 and CardMessage type=10)
await kook.Send.To("group", channel_id).Edit(msg_id, "**Updated content**")

# Recall message
await kook.Send.To("group", channel_id).Recall(msg_id)

# Upload file (get file URL)
result = await kook.Send.Upload("C:/path/to/file.jpg")
file_url = result["data"]["url"]
```

## Send Method Return Values

All send methods return a Task object, which can be awaited to get the send result. The return result follows the ErisPulse adapter standardization return specification:

```python
{
    "status": "ok",           // Execution status: "ok" or "failed"
    "retcode": 0,             // Return code (0 for success, platform errors unified as 34100)
    "data": {...},            // Response data
    "message_id": "xxx",      // Message ID
    "message": "",            // Error message (empty string for successful response)
    "kook_raw": {...},        // Original response data
    "kook_code": 0            // Kook original code (preserved when error occurs)
}
```

### Error Code Description

| retcode | Description |
|---------|------|
| 0 | Success |
| 33001 | Network error (request exception, account API instance not initialized, etc.) |
| 34100 | Platform error (Kook returns non-zero code, original response preserved in `kook_raw`, original code stored in `kook_code`) |
| 10002 | Unsupported action (see "Standardization Alignment (4.3.2)" error code specification) |

## Platform-Specific Event Types

Use platform-specific features only after checking `platform=="kook"`

### Core Differences

1. **Channel System**: Kook uses a server (Guild) and channel (Channel) two-layer structure, with channels being the basic message sending target
2. **Message Types**: Kook supports multiple message types including text(1), image(2), video(3), file(4), voice(8), KMarkdown(9), and card messages(10)
3. **Private Messaging System**: Kook distinguishes between channel messages and private messages, using different API endpoints
4. **Message Sequence Numbers**: Kook WebSocket uses `sn` sequence numbers to ensure message ordering, supporting message buffering and out-of-order reordering
5. **Message Editing and Recall**: Supports editing sent messages (only KMarkdown and CardMessage) and recalling messages

### Extended Fields

- All platform-specific fields are prefixed with `kook_`
- Original data is preserved in the `kook_raw` field
- `kook_raw_type` indicates the original Kook message type number (e.g., `1` for text, `255` for notification events)
- Event `self.account_id` is the account name that generated the event (in multi-account scenarios, `event.reply()` automatically handles replies based on that account)

### Special Field Examples

```python
# Channel text message
{
  "type": "message",
  "detail_type": "group",
  "user_id": "User ID",
  "group_id": "Channel ID",
  "channel_id": "Channel ID",
  "message_id": "Message ID",
  "self": {
    "platform": "kook",
    "user_id": "Bot ID",
    "account_id": "default"
  },
  "kook_raw": {...},
  "kook_raw_type": "1",
  "message": [
    {"type": "text", "data": {"text": "Hello"}}
  ],
  "alt_message": "Hello"
}

# Message with image
{
  "type": "message",
  "detail_type": "group",
  "user_id": "User ID",
  "group_id": "Channel ID",
  "channel_id": "Channel ID",
  "message_id": "Message ID",
  "kook_raw": {...},
  "kook_raw_type": "2",
  "message": [
    {"type": "image", "data": {"file": "Image URL", "url": "Image URL"}}
  ],
  "alt_message": "Image content"
}

# KMarkdown message
{
  "type": "message",
  "detail_type": "group",
  "user_id": "User ID",
  "group_id": "Channel ID",
  "message_id": "Message ID",
  "kook_raw": {...},
  "kook_raw_type": "9",
  "message": [
    {"type": "text", "data": {"text": "Parsed plain text"}}
  ]
}

# Card message
{
  "type": "message",
  "detail_type": "group",
  "user_id": "User ID",
  "group_id": "Channel ID",
  "message_id": "Message ID",
  "kook_raw": {...},
  "kook_raw_type": "10",
  "message": [
    {"type": "json", "data": {"data": "Card JSON content"}}
  ]
}

# Private chat message
{
  "type": "message",
  "detail_type": "private",
  "user_id": "User ID",
  "message_id": "Message ID",
  "kook_raw": {...},
  "kook_raw_type": "1",
  "message": [
    {"type": "text", "data": {"text": "Private chat content"}}
  ]
}
```

### Message Segment Types

Kook's message types are automatically converted to corresponding message segments based on the `type` field:

| Kook type | Converted Type | Description |
|---|---|---|
| 1 | `text` | Text message |
| 2 | `image` | Image message |
| 3 | `video` | Video message |
| 4 | `file` | File message |
| 8 | `record` | Voice message |
| 9 | `text` | KMarkdown message (extract plain text content) |
| 10 | `json` | Card message (original JSON) |

Message segment structure example:
```json
{
  "type": "image",
  "data": {
    "file": "Image URL",
    "url": "Image URL"
  }
}
```

### Mention Message Segment

When a message contains @ information, a `mention` message segment is inserted before the message segment:

```json
{
  "type": "mention",
  "data": {
    "user_id": "User ID being mentioned"
  }
}
```

### mention_all Message Segment

When the message is a @all, a `mention_all` message segment is inserted:

```json
{
  "type": "mention_all",
  "data": {}
}
```

## WebSocket Connection

### Connection Flow

1. Use Bot Token to call `POST /gateway/index` to obtain the WebSocket gateway address
2. Connect to the WebSocket gateway
3. Receive HELLO (s=1) signal, verify connection status
4. Start heartbeat loop (PING, s=2, every 30 seconds)
5. Receive message events (s=0), use sn sequence number to ensure ordering
6. Receive heartbeat response PONG (s=3)

### Signal Types

| Signal | s value | Description |
|------|-----|------|
| HELLO | 1 | Server welcome signal, received after successful connection |
| PING | 2 | Client heartbeat, sent every 30 seconds, carrying current sn |
| PONG | 3 | Heartbeat response |
| RESUME | 4 | Resume connection signal, carrying sn to resume session |
| RECONNECT | 5 | Server requests reconnection, need to re-obtain gateway |
| RESUME_ACK | 6 | RESUME success response |

### Disconnection and Reconnection

- After an abnormal disconnection, the adapter automatically retries the connection
- If there was a previous `sn > 0`, it first attempts to RESUME (s=4) to resume the connection
- After RESUME fails, reset sn and message queue, and reconnect from scratch (HELLO process)
- When RECONNECT (s=5) signal is received, clear the state and reconnect

### Message Sequence Number Mechanism

Kook WebSocket uses `sn` (incrementing sequence number) to ensure message ordering:

- Every time a message event (s=0) is received, sn is incremented
- If the received message sn is not continuous, enter buffering mode
- Messages in the buffer are sorted by sn, waiting for missing messages to arrive before processing in order
- After the buffer is cleared, automatically exit buffering mode

## Usage Examples

### Handling Channel Messages

```python
from ErisPulse.Core.Event import message
from ErisPulse import sdk

kook = sdk.adapter.get("kook")

@message.on_message()
async def handle_group_msg(event):
    if event.get("platform") != "kook":
        return
    if event.get("detail_type") != "group":
        return

    text = event.get_text()
    channel_id = event.get("group_id")

    if text == "hello":
        await kook.Send.To("group", channel_id).Text("Hello!")
```

### Handling Private Messages

```python
@message.on_message()
async def handle_private_msg(event):
    if event.get("platform") != "kook":
        return
    if event.get("detail_type") != "private":
        return

    text = event.get_text()
    user_id = event.get("user_id")

    await kook.Send.To("user", user_id).Text(f"You said: {text}")
```

### Handling Notification Events (Emoji Reactions, etc.)

```python
from ErisPulse.Core.Event import notice

@notice.on_notice()
async def handle_notice(event):
    if event.get("platform") != "kook":
        return

    sub_type = event.get("sub_type")

    if sub_type == "added_reaction":
        emoji = event.get("emoji", {})
        user_id = event.get("user_id")
        msg_id = event.get("message_id")
        print(f"User {user_id} added emoji reaction to message {msg_id}")

    elif sub_type == "deleted_reaction":
        emoji = event.get("emoji", {})
        user_id = event.get("user_id")
        msg_id = event.get("message_id")
        print(f"User {user_id} removed emoji reaction from message {msg_id}")
```

### Sending Media Messages

```python
# Send image (URL)
await kook.Send.To("group", channel_id).Image("https://example.com/image.png")

# Send image (binary)
with open("image.png", "rb") as f:
    image_bytes = f.read()
await kook.Send.To("group", channel_id).Image(image_bytes)

# Send video
await kook.Send.To("group", channel_id).Video("https://example.com/video.mp4")

# Send file
await kook.Send.To("group", channel_id).File("https://example.com/file.pdf", filename="document.pdf")

# Send voice
await kook.Send.To("group", channel_id).Voice("https://example.com/voice.mp3")
```

### Sending KMarkdown and Card Messages

```python
# KMarkdown
await kook.Send.To("group", channel_id).Markdown("**Bold** *Italic* [Link](https://example.com)")

# Card message
card = {
    "type": "card",
    "theme": "primary",
    "size": "lg",
    "modules": [
        {"type": "header", "text": {"type": "plain-text", "content": "Title"}},
        {"type": "section", "text": {"type": "kmarkdown", "content": "Content"}}
    ]
}
await kook.Send.To("group", channel_id).Card(card)
```

### Message Editing and Recall

```python
# Send message
result = await kook.Send.To("group", channel_id).Markdown("**Original content**")
msg_id = result["data"]["msg_id"]

# Edit message (only supports KMarkdown and CardMessage)
await kook.Send.To("group", channel_id).Edit(msg_id, "**Updated content**")

# Recall message
await kook.Send.To("group", channel_id).Recall(msg_id)
```

### Handling Private Message Edit and Delete Notifications

```python
@notice.on_notice()
async def handle_private_notice(event):
    if event.get("platform") != "kook":
        return

    sub_type = event.get("sub_type")

    if sub_type == "updated_private_message":
        msg_id = event.get("message_id")
        content = event.get("content")
        print(f"Private message updated: {msg_id}, new content: {content}")

    elif sub_type == "deleted_private_message":
        msg_id = event.get("message_id")
        print(f"Private message deleted: {msg_id}")
```