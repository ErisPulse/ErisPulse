# Kook Platform Features Documentation

KookAdapter is an adapter built on the Kook (Kaihei La) Bot WebSocket protocol, integrating all Kook functionality modules and providing a unified interface for event handling and message operations.

---

## Document Information

- Corresponding Module Version: 4.1.0
- Maintainer: ShanFish

## Basic Information

- Platform Introduction: Kook (formerly Kaihei La) is a community platform that supports text, voice, and video communication, providing a complete Bot development interface.
- Adapter Name: KookAdapter
- Multi-account Support: Supports configuring multiple Kook bots simultaneously.
- Connection Method: WebSocket long connection (via Kook gateway).
- Authentication Method: Identity authentication based on Bot Token.
- Chained Modifier Support: Supports chained modifier methods such as `.Reply()`, `.At()`, `.AtAll()`.
- OneBot12 Compatibility: Supports sending OneBot12 formatted messages.

## Configuration

KookAdapter supports multi-account configuration, where each account corresponds to an independent Kook bot.

```toml
# config.toml
# Account 1
[KookAdapter.accounts.default]
token = "YOUR_BOT_TOKEN"     # Kook Bot Token (required, format: Bot xxx/xxx)
bot_id = ""                   # Bot User ID (optional, if not set, it will be parsed from token)
compress = true               # Whether to enable WebSocket compression (optional, default is true)
enabled = true                # Whether to enable this account (optional, default is true)

# Account 2
[KookAdapter.accounts.bot2]
token = "ANOTHER_BOT_TOKEN"
bot_id = ""
enabled = true
```

> Compatibility with old configurations: If an old single-account `[KookAdapter]` configuration (including token) is detected, it will be automatically migrated to `accounts.default`.

**Configuration item description (per account):**
- `token`: The Token of the Kook Bot (required), obtained from [Kook Developer Center](https://developer.kookapp.cn), format is `Bot xxx/xxx`
- `bot_id`: The User ID of the Bot (optional), if not set, the adapter will try to automatically parse it from the token. It is recommended to manually set it to ensure accuracy
- `compress`: Whether to enable WebSocket data compression (optional, default is `true`), enables zlib decompression of data
- `enabled`: Whether to enable this account (optional, default is true)

**API Environment:**
- Kook API base address: `https://www.kookapp.cn/api/v3`
- WebSocket gateway is dynamically obtained through API: `POST /gateway/index`

## v5 Paradigm Update (4.1.0)

This adapter has completed alignment with the v5 paradigm (incremental upgrade, API compatible):

- **BaseConverter Inheritance**: Common fields of converters are built by the framework `build_base_event`
- **Api DSL**: Standard API action mapping (see below)
- **Standard keyboard segment**: `{"type": "keyboard", "data": {"rows": [[{"label", "type": "callback|link", "data"}]]}}` Text + keyboard automatically combine into Kook card messages (section + action-group); .Keyboard(rows) decorator accepts generic structure
- **spawn_background task ownership**: Connection tasks use runtime.spawn_background
- **Framework soft dependency**: Runtime detection of ErisPulse>=2.7.1 with prompt; version logs output on startup

### Standard API Actions

```python
from ErisPulse import sdk
kook = sdk.adapter.get("kook")

result = await kook.Api.get_self_info()              # GET /users/@me
result = await kook.Api.get_user_info(user_id)       # POST /user/view
result = await kook.Api.get_guild_info(guild_id)     # POST /guild/view
result = await kook.Api.get_guild_list()             # POST /guild/list
result = await kook.Api.get_channel_info(channel_id) # POST /channel/view
result = await kook.Api.get_channel_list(guild_id)   # POST /channel/list
await kook.Api.delete_message(msg_id)                # POST /message/delete
result = await kook.Api.Using("main").get_self_info()
```

### Buttons (keyboard)

```python
rows = [[{"label": "Option A", "type": "callback", "data": "vote:A"},
         {"label": "Website",  "type": "link",     "data": "https://example.com"}]]
await kook.Send.To("channel", channel_id).Keyboard(rows).Text("Please select")
# Text and buttons automatically combine into Kook card messages (section + action-group)

# Button click callback (standard fields)
from ErisPulse.Core.Event import notice

@notice.on_notice()
async def handle_button(event):
    if event.get("platform") == "kook" and event.get("button_data"):
        data = event["button_data"]
```
---

## Supported Message Sending Types

All sending methods are implemented through a fluent API syntax, for example:
```python
from ErisPulse.Core import adapter
kook = adapter.get("kook")

await kook.Send.To("group", channel_id).Text("Hello World!")
```

The supported sending types include:
- `.Text(text: str)`: Sends a plain text message.
- `.Image(file: bytes | str)`: Sends an image message, supports file paths, URLs, and binary data.
- `.Video(file: bytes | str)`: Sends a video message, supports file paths, URLs, and binary data.
- `.File(file: bytes | str, filename: str = None)`: Sends a file message, supports file paths, URLs, and binary data.
- `.Voice(file: bytes | str)`: Sends a voice message, supports file paths, URLs, and binary data.
- `.Markdown(text: str)`: Sends a message in KMarkdown format.
- `.Card(card_data: dict)`: Sends a card message (CardMessage).
- `.Raw_ob12(message: List[Dict], **kwargs)`: Sends a OneBot12 formatted message.

### Fluent Modifier Methods (Can Be Combined)

Modifier methods return `self` and support fluent chaining, which must be called before the final sending method:

- `.Reply(message_id: str)`: Replies (references) a specified message.
- `.At(user_id: str)`: Mentions a specified user, can be called multiple times to mention multiple users.
- `.AtAll()`: Mentions everyone.

### Fluent Chaining Examples

```python
# Basic sending
await kook.Send.To("group", channel_id).Text("Hello")

# Reply to a message
await kook.Send.To("group", channel_id).Reply(msg_id).Text("Replied message")

# Mention a user
await kook.Send.To("group", channel_id).At("user_id").Text("Hello")

# Mention multiple users
await kook.Send.To("group", channel_id).At("user1").At("user2").Text("Multiple users @")

# Mention everyone
await kook.Send.To("group", channel_id).AtAll().Text("Announcement")

# Combine methods
await kook.Send.To("group", channel_id).Reply(msg_id).At("user_id").Text("Composite message")
```

### OneBot12 Message Support

The adapter supports sending OneBot12 formatted messages for cross-platform message compatibility:

```python
# Send a OneBot12 formatted message
ob12_msg = [{"type": "text", "data": {"text": "Hello"}}]
await kook.Send.To("group", channel_id).Raw_ob12(ob12_msg)

# Combine with fluent modifiers
ob12_msg = [{"type": "text", "data": {"text": "Replied message"}}]
await kook.Send.To("group", channel_id).Reply(msg_id).Raw_ob12(ob12_msg)

# Use mention and reply message segments within Raw_ob12
ob12_msg = [
    {"type": "text", "data": {"text": "Hello "}},
    {"type": "mention", "data": {"user_id": "user_id"}},
    {"type": "reply", "data": {"message_id": "msg_id"}}
]
await kook.Send.To("group", channel_id).Raw_ob12(ob12_msg)
```

### Additional Operation Methods

In addition to sending messages, the Kook adapter supports the following operations:

```python
# Edit a message (supports only KMarkdown type=9 and CardMessage type=10)
await kook.Send.To("group", channel_id).Edit(msg_id, "**Updated content**")

# Recall a message
await kook.Send.To("group", channel_id).Recall(msg_id)

# Upload a file (get file URL)
result = await kook.Send.Upload("C:/path/to/file.jpg")
file_url = result["data"]["url"]
```

## Return Values of Send Methods

All send methods return a Task object, which can be awaited directly to obtain the send result. The returned result follows the ErisPulse adapter's standardized return specification:

```python
{
    "status": "ok",           // Execution status: "ok" or "failed"
    "retcode": 0,             // Return code (Kook API's code)
    "data": {...},            // Response data
    "message_id": "xxx",      // Message ID
    "message": "",            // Error message
    "kook_raw": {...}         // Raw response data
}
```

### Error Code Explanation

| retcode | Description |
|---------|-------------|
| 0 | Success |
| 40100 | Invalid or missing Token |
| 40101 | Token expired |
| 40102 | Token does not match Bot |
| 40103 | Missing permissions |
| 40000 | Invalid parameter |
| 40400 | Target does not exist |
| 40300 | No permission to perform operation |
| 50000 | Internal server error |
| -1 | Internal adapter error |

## Platform-specific Event Types

Use `platform=="kook"` to detect and utilize platform-specific features.

### Core Differences

1. **Channel System**: Kook uses a two-tier structure of servers (Guild) and channels (Channel), with channels serving as the basic message sending targets.
2. **Message Types**: Kook supports various message types, including text (1), image (2), video (3), file (4), voice (8), KMarkdown (9), and card messages (10).
3. **Private Messaging System**: Kook distinguishes between channel messages and private messages, using different API endpoints.
4. **Message Sequence Numbers**: Kook's WebSocket uses `sn` sequence numbers to ensure message ordering, supporting message buffering and out-of-order reordering.
5. **Message Editing and Deletion**: Supports editing sent messages (only KMarkdown and CardMessage) and deleting messages.

### Extended Fields

- All platform-specific fields are prefixed with `kook_`.
- Original data is retained in the `kook_raw` field.
- `kook_raw_type` indicates the original Kook message type number (e.g., `1` for text, `255` for notification events).

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
    "user_id": "Mentioned User ID"
  }
}
```

### mention_all Message Segment

When a message is a mention to all, a `mention_all` message segment is inserted:

```json
{
  "type": "mention_all",
  "data": {}
}
```

## WebSocket Connection

### Connection Flow

1. Use the Bot Token to call `POST /gateway/index` to obtain the WebSocket gateway address.
2. Connect to the WebSocket gateway.
3. Upon receiving the HELLO (s=1) signal, verify the connection status.
4. Begin the heartbeat loop (PING, s=2, sent every 30 seconds).
5. Receive message events (s=0), using the sn sequence number to ensure order.
6. Receive the heartbeat response PONG (s=3).

### Signal Types

| Signal | s Value | Description |
|--------|---------|-------------|
| HELLO | 1 | Server welcome signal, received after successful connection. |
| PING | 2 | Client heartbeat, sent every 30 seconds, includes the current sn. |
| PONG | 3 | Heartbeat response. |
| RESUME | 4 | Resume connection signal, includes sn to resume session. |
| RECONNECT | 5 | Server requests reconnection, requires obtaining a new gateway. |
| RESUME_ACK | 6 | Response indicating successful RESUME. |

### Disconnection and Reconnection

- After an abnormal disconnection, the adapter automatically retries the connection.
- If there was a previous `sn > 0`, it first attempts to RESUME (s=4) the connection.
- After a failed RESUME, reset sn and the message queue, then perform a new connection (HELLO flow).
- Upon receiving the RECONNECT (s=5) signal, clear the status and reconnect.

### Message Sequence Number Mechanism

Kook WebSocket uses `sn` (incrementing sequence number) to ensure message order:

- Each time a message event (s=0) is received, sn is incremented.
- If a received message has a non-continuous sn, enter the temporary storage mode.
- Messages in the temporary storage area are sorted by sn, waiting for missing messages to arrive before processing in order.
- After the temporary storage area is cleared, automatically exit the temporary storage mode.

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

### Handling Notification Events (like emoji reactions)

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
        print(f"User {user_id} added an emoji reaction to message {msg_id}")

    elif sub_type == "deleted_reaction":
        emoji = event.get("emoji", {})
        user_id = event.get("user_id")
        msg_id = event.get("message_id")
        print(f"User {user_id} removed an emoji reaction from message {msg_id}")
```

### Sending Media Messages

```python
# Sending an image (URL)
await kook.Send.To("group", channel_id).Image("https://example.com/image.png")

# Sending an image (binary)
with open("image.png", "rb") as f:
    image_bytes = f.read()
await kook.Send.To("group", channel_id).Image(image_bytes)

# Sending a video
await kook.Send.To("group", channel_id).Video("https://example.com/video.mp4")

# Sending a file
await kook.Send.To("group", channel_id).File("https://example.com/file.pdf", filename="document.pdf")

# Sending a voice message
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

### Editing and Deleting Messages

```python
# Sending a message
result = await kook.Send.To("group", channel_id).Markdown("**Original content**")
msg_id = result["data"]["msg_id"]

# Editing a message (only supports KMarkdown and CardMessage)
await kook.Send.To("group", channel_id).Edit(msg_id, "**Updated content**")

# Deleting a message
await kook.Send.To("group", channel_id).Recall(msg_id)
```

### Handling Edit and Delete Notifications for Private Messages

```python
@notice.on_notice()
async def handle_private_notice(event):
    if event.get("platform") != "kook":
        return

    sub_type = event.get("sub_type")

    if sub_type == "updated_private_message":
        msg_id = event.get("message_id")
        content = event.get("content")
        print(f"Private message updated: {msg_id}, New content: {content}")

    elif sub_type == "deleted_private_message":
        msg_id = event.get("message_id")
        print(f"Private message deleted: {msg_id}")
```