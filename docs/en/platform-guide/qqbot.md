# QQBot Platform Feature Documentation

QQBotAdapter is an adapter built based on the QQBot (QQ Bot Documentation) protocol, integrating all QQBot functional modules and providing unified event handling and message operation interfaces.

---

## Document Information

- Corresponding Module Version: 1.0.0
- Maintainer: ErisPulse

## Basic Information

- Platform Overview: QQBot is the official development interface provided by QQ for bots, supporting various scenarios such as group chat, private chat, and channels.
- Adapter Name: QQBotAdapter
- Connection Method: WebSocket long connection (via QQBot gateway)
- Authentication Method: Access token obtained based on appId + clientSecret
- Chainable Modifier Support: Supports chainable modifier methods such as `.Reply()`, `.At()`, `.AtAll()`, `.Keyboard()`
- OneBot12 Compatibility: Supports sending OneBot12 format messages

## Configuration Instructions

```toml
# config.toml
[QQBot_Adapter]
appid = "YOUR_APPID"          # QQ Bot application ID (required)
secret = "YOUR_CLIENT_SECRET"  # QQ Bot client secret (required)
sandbox = false                 # Whether to use sandbox environment (optional, default is false)
intents = [1, 30, 25]          # List of event intents to subscribe to (optional)
gateway_url = "wss://api.sgroup.qq.com/websocket/"  # Custom gateway address (optional)
```

**Configuration Item Description:**
- `appid`: QQ Bot application ID (required), obtained from the QQ Open Platform
- `secret`: QQ Bot client secret (required), obtained from the QQ Open Platform
- `sandbox`: Whether to use the sandbox environment, the sandbox environment API address is `https://sandbox.api.sgroup.qq.com`
- `intents`: List of event subscription intents, each value is shifted left and bitwise OR-ed
  - `1`: Guild-related events
  - `25`: Guild message events
  - `30`: Group @ message events
- `gateway_url`: WebSocket gateway address, default is `wss://api.sgroup.qq.com/websocket/`

**API Environments:**
- Production Environment: `https://api.sgroup.qq.com`
- Sandbox Environment: `https://sandbox.api.sgroup.qq.com`

## Supported Message Sending Types

All sending methods are implemented through chainable syntax, for example:
```python
from ErisPulse.Core import adapter
qqbot = adapter.get("qqbot")

await qqbot.Send.To("user", user_openid).Text("Hello World!")
```

Supported sending types include:
- `.Text(text: str)`: Send plain text messages.
- `.Image(file: bytes | str)`: Send image messages, supporting file paths, URLs, and binary data.
- `.Markdown(content: str)`: Send Markdown formatted messages.
- `.Ark(template_id: int, kv: list)`: Send Ark template messages.
- `.Embed(embed_data: dict)`: Send Embed messages.
- `.Raw_ob12(message: List[Dict], **kwargs)`: Send OneBot12 formatted messages.

### Chainable Modifier Methods (Can be Combined)

Chainable modifier methods return `self`, supporting chained calls, and must be called before the final sending method:

- `.Reply(message_id: str)`: Reply to a specified message.
- `.At(user_id: str)`: @ a specified user (insert content in the format `<@user_id>`).
- `.AtAll()`: @ everyone (insert `@everyone` text).
- `.Keyboard(keyboard: dict)`: Add keyboard buttons.

### Chainable Call Examples

```python
# Basic sending
await qqbot.Send.To("user", user_openid).Text("Hello")

# Reply to a message
await qqbot.Send.To("group", group_openid).Reply(msg_id).Text("Reply message")

# Reply + Button
await qqbot.Send.To("group", group_openid).Reply(msg_id).Keyboard(keyboard).Text("Message with reply and keyboard")

# @ User
await qqbot.Send.To("group", group_openid).At("member_openid").Text("Hello")

# Combined usage
await qqbot.Send.To("group", group_openid).Reply(msg_id).At("member_openid").Keyboard(keyboard).Text("Composite message")
```

### OneBot12 Message Support

The adapter supports sending OneBot12 formatted messages, facilitating cross-platform message compatibility:

```python
# Send OneBot12 formatted message
ob12_msg = [{"type": "text", "data": {"text": "Hello"}}]
await qqbot.Send.To("user", user_openid).Raw_ob12(ob12_msg)

# Combined with chainable modifiers
ob12_msg = [{"type": "text", "data": {"text": "Reply message"}}]
await qqbot.Send.To("group", group_openid).Reply(msg_id).Raw_ob12(ob12_msg)
```

## Sending Method Return Values

All sending methods return a Task object, which can be awaited to get the sending result. The returned result follows the ErisPulse adapter standardization return specification:

```python
{
    "status": "ok",           // Execution status: "ok" or "failed"
    "retcode": 0,             // Return code
    "data": {...},            // Response data
    "message_id": "123456",   // Message ID
    "message": "",            // Error message
    "qqbot_raw": {...}        // Raw response data
}
```

### Error Code Explanation

| retcode | Description |
|---------|-------------|
| 0 | Success |
| 10003 | Unable to determine the recipient |
| 32000 | Request timeout |
| 33000 | API call exception |
| 34000 | API returned unexpected format or business error |

## Platform-Specific Event Types

Use platform-specific features only after checking `platform=="qqbot"`

### Core Differences

1. **OpenID System**: QQBot uses OpenID instead of QQ numbers, with both user and group identifiers being OpenID strings.
2. **Group Messages Require @**: Group messages are only received when a user @s the bot (`GROUP_AT_MESSAGE_CREATE`).
3. **Guild System**: QQBot supports messages and events in guilds (Guild) and sub-channels (Channel).
4. **Message Review**: Sent messages may require review, with results notified via `qqbot_audit_pass`/`qqbot_audit_reject` events.
5. **Passive Reply**: Group and private chat messages support passive reply mechanisms, requiring `msg_id` to be carried when sending.

### Extended Fields

- All platform-specific fields are prefixed with `qqbot_`
- Original data is preserved in the `qqbot_raw` field
- `qqbot_raw_type` indicates the original QQBot event type (e.g., `C2C_MESSAGE_CREATE`)
- Attachment data is saved in the `qqbot_attachment` field

### Special Field Examples

```python
# Group @ message
{
  "type": "message",
  "detail_type": "group",
  "user_id": "MEMBER_OPENID",
  "group_id": "GROUP_OPENID",
  "qqbot_group_openid": "GROUP_OPENID",
  "qqbot_member_openid": "MEMBER_OPENID",
  "qqbot_event_id": "Message event ID",
  "qqbot_reply_token": "Reply token"
}

# Private chat message
{
  "type": "message",
  "detail_type": "private",
  "user_id": "USER_OPENID",
  "qqbot_openid": "USER_OPENID",
  "qqbot_event_id": "Message event ID",
  "qqbot_reply_token": "Reply token"
}

# Interaction event
{
  "type": "notice",
  "detail_type": "qqbot_interaction",
  "qqbot_interaction_id": "Interaction ID",
  "qqbot_interaction_type": "Interaction type",
  "qqbot_interaction_data": {
    "...": "Interaction data"
  }
}

# Message review
{
  "type": "notice",
  "detail_type": "qqbot_audit_pass",
  "qqbot_audit_id": "Review ID",
  "qqbot_message_id": "Message ID"
}

# Message deletion
{
  "type": "notice",
  "detail_type": "qqbot_message_delete",
  "message_id": "Deleted message ID",
  "operator_id": "Operator ID"
}

# Reaction
{
  "type": "notice",
  "detail_type": "qqbot_reaction_add",
  "qqbot_raw": {
    "...": "Raw data"
  }
}
```

### Guild Message Segments

Guild messages support the `mentions` field, which is converted into `mention` message segments:

```json
{
  "type": "mention",
  "data": {
    "user_id": "Mentioned user ID",
    "user_name": "Mentioned user nickname"
  }
}
```

### Attachment Message Segments

QQBot attachments are automatically converted into corresponding message segments based on `content_type`:

| content_type Prefix | Conversion Type | Description |
|---|---|---|
| `image` | `image` | Image message |
| `video` | `video` | Video message |
| `audio` | `voice` | Voice message |
| Others | `file` | File message |

Attachment message segment structure:
```json
{
  "type": "image",
  "data": {
    "url": "Attachment URL",
    "qqbot_attachment": {
      "content_type": "image/png",
      "url": "Original attachment URL"
    }
  }
}
```

## WebSocket Connection

### Connection Flow

1. Use appId + clientSecret to obtain access_token
2. Connect to the WebSocket gateway
3. Receive OP_HELLO (op=10) message to get the heartbeat interval
4. Send OP_IDENTIFY (op=2) for identity verification
5. Receive READY event to get session_id and bot_id
6. Start heartbeat loop (OP_HEARTBEAT, op=1)
7. Receive event distribution (OP_DISPATCH, op=0)

### Reconnection

- Supports automatic reconnection, with a maximum of 50 reconnection attempts
- Reconnection wait time uses exponential backoff algorithm: `min(5 * 2^min(count, 6), 300)` seconds
- Supports session recovery (OP_RESUME, op=6), using session_id + seq to resume
- Automatic reconnection is triggered upon receiving OP_RECONNECT (op=7) or OP_INVALID_SESSION (op=9)

### Token Refresh

- access_token typically has a validity of 7200 seconds
- The adapter automatically refreshes the token every 7080 seconds (7200-120)
- Refresh endpoint: `POST https://bots.qq.com/app/getAppAccessToken`

## Event Subscription (Intents)

Intents values are combined using bitwise operations:

```python
intents = [1, 30, 25]
value = 0
for intent in intents:
    value |= (1 << intent)
```

Common intent values:
| Intent Value | Description |
|--------------|-------------|
| 1 | Guild-related events (GUILD_CREATE, etc.) |
| 25 | Guild message events (AT_MESSAGE_CREATE, etc.) |
| 30 | Group @ message events (GROUP_AT_MESSAGE_CREATE, etc.) |

## Usage Examples

### Handling Group Messages

```python
from ErisPulse.Core.Event import message
from ErisPulse import sdk

qqbot = sdk.adapter.get("qqbot")

@message.on_message()
async def handle_group_msg(event):
    if event.get("platform") != "qqbot":
        return
    if event.get("detail_type") != "group":
        return

    text = event.get_text()
    group_id = event.get("group_id")

    if text == "hello":
        await qqbot.Send.To("group", group_id).Reply(
            event.get("message_id")
        ).Text("Hello!")
```

### Handling Interaction Events

```python
from ErisPulse.Core.Event import notice

@notice.on_notice()
async def handle_interaction(event):
    if event.get("platform") != "qqbot":
        return

    if event.get("detail_type") == "qqbot_interaction":
        interaction_id = event.get("qqbot_interaction_id", "")
        interaction_data = event.get("qqbot_interaction_data", {})
        # Handle interaction...
```

### Sending Media Messages

```python
# Send image (URL)
await qqbot.Send.To("group", group_openid).Image("https://example.com/image.png")

# Send image (binary)
with open("image.png", "rb") as f:
    image_bytes = f.read()
await qqbot.Send.To("user", user_openid).Image(image_bytes)
```

### Listening for Message Review Results

```python
@notice.on_notice()
async def handle_audit(event):
    if event.get("platform") != "qqbot":
        return

    detail_type = event.get("detail_type")

    if detail_type == "qqbot_audit_pass":
        msg_id = event.get("qqbot_message_id")
        print(f"Message review passed: {msg_id}")

    elif detail_type == "qqbot_audit_reject":
        reason = event.get("qqbot_audit_reject_reason", "")
        print(f"Message review rejected: {reason}")
```