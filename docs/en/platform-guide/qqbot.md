# QQBot Platform Features Documentation

QQBotAdapter is an adapter based on the QQBot (QQ Robot Documentation) protocol, integrating all functional modules of QQBot to provide a unified event handling and message operation interface.

---

## Document Information

- Corresponding module version: 1.0.0
- Maintainer: ErisPulse

## Basic Information

- Platform Introduction: QQBot is the official development interface for QQ robots, supporting group chats, private chats, channels and other scenarios
- Adapter Name: QQBotAdapter
- Connection Method: WebSocket long connection (via QQBot gateway)
- Authentication Method: Based on appId + clientSecret to obtain access_token
- Chaining Support: Supports chaining methods like `.Reply()`, `.At()`, `.AtAll()`, `.Keyboard()`
- OneBot12 Compatibility: Supports sending OneBot12 format messages

## Configuration Instructions

```toml
# config.toml
[QQBot_Adapter]
appid = "YOUR_APPID"          # QQ Bot application ID (required)
secret = "YOUR_CLIENT_SECRET"  # QQ Bot client secret (required)
sandbox = false                 # Whether to use sandbox environment (optional, default to false)
intents = [1, 30, 25]          # Subscribed event intents bit (optional)
gateway_url = "wss://api.sgroup.qq.com/websocket/"  # Custom gateway URL (optional)
```

**Configuration Items Description:**
- `appid`: QQ Bot application ID (required), obtained from QQ Open Platform
- `secret`: QQ Bot client secret (required), obtained from QQ Open Platform
- `sandbox`: Whether to use sandbox environment, sandbox environment API address is `https://sandbox.api.sgroup.qq.com`
- `intents`: Event subscription intents list, each value will be shifted left and then bitwise OR operated
  - `1`: Channel-related events
  - `25`: Channel message events
  - `30`: Group @ message events
- `gateway_url`: WebSocket gateway URL, default is `wss://api.sgroup.qq.com/websocket/`

**API Environment:**
- Production Environment: `https://api.sgroup.qq.com`
- Sandbox Environment: `https://sandbox.api.sgroup.qq.com`

## Supported Message Sending Types

All sending methods are implemented through chaining syntax, for example:
```python
from ErisPulse.Core import adapter
qqbot = adapter.get("qqbot")

await qqbot.Send.To("user", user_openid).Text("Hello World!")
```

Supported sending types include:
- `.Text(text: str)`: Send plain text messages.
- `.Image(file: bytes | str)`: Send image messages, supports file paths, URLs, and binary data.
- `.Markdown(content: str)`: Send Markdown format messages.
- `.Ark(template_id: int, kv: list)`: Send Ark template messages.
- `.Embed(embed_data: dict)`: Send Embed messages.
- `.Raw_ob12(message: List[Dict], **kwargs)`: Send OneBot12 format messages.

### Chaining Methods (Can be used in combination)

Chaining methods return `self`, support chained calls, and must be called before the final sending method:
- `.Reply(message_id: str)`: Reply to a specific message.
- `.At(user_id: str)`: @ a specific user (inserts content in `<@user_id>` format).
- `.AtAll()`: @ everyone (inserts `@everyone` text).
- `.Keyboard(keyboard: dict)`: Add keyboard buttons.

### Chaining Example

```python
# Basic sending
await qqbot.Send.To("user", user_openid).Text("Hello")

# Reply message
await qqbot.Send.To("group", group_openid).Reply(msg_id).Text("Reply message")

# Reply + Button
await qqbot.Send.To("group", group_openid).Reply(msg_id).Keyboard(keyboard).Text("Message with reply and keyboard")

# @ user
await qqbot.Send.To("group", group_openid).At("member_openid").Text("Hello")

# Combined usage
await qqbot.Send.To("group", group_openid).Reply(msg_id).At("member_openid").Keyboard(keyboard).Text("Complex message")
```

### OneBot12 Message Support

The adapter supports sending OneBot12 format messages for cross-platform compatibility:
```python
# Send OneBot12 format message
ob12_msg = [{"type": "text", "data": {"text": "Hello"}}]
await qqbot.Send.To("user", user_openid).Raw_ob12(ob12_msg)

# With chaining
ob12_msg = [{"type": "text", "data": {"text": "Reply message"}}]
await qqbot.Send.To("group", group_openid).Reply(msg_id).Raw_ob12(ob12_msg)
```

## Sending Method Return Values

All sending methods return a Task object, which can be directly awaited to get the sending result. The return result follows the ErisPulse adapter standardized return specification:

```python
{
    "status": "ok",           // Execution status: "ok" or "failed"
    "retcode": 0,             // Return code
    "data": {...},            // Response data
    "message_id": "123456",   // Message ID
    "message": "",            // Error message
    "qqbot_raw": {...}        // Original response data
}
```

### Error Code Description

| retcode | Description |
|---------|-------------|
| 0 | Success |
| 10003 | Cannot determine sending target |
| 32000 | Request timeout |
| 33000 | API call exception |
| 34000 | API returned unexpected format or business error |

## Special Event Types

Requires `platform=="qqbot"` detection before using platform-specific features

### Core Differences

1. **OpenID System**: QQBot uses openid instead of QQ numbers, with users and groups identified by openid strings
2. **Group Messages Must @**: In-group messages are only received when users @ the bot (`GROUP_AT_MESSAGE_CREATE`)
3. **Channel System**: QQBot supports channels (Guilds) and sub-channels (Channels) for messages and events
4. **Message Moderation**: Sent messages may require moderation, with results notified via `qqbot_audit_pass`/`qqbot_audit_reject` events
5. **Passive Reply**: Group and private chat messages support passive reply mechanism, requiring `msg_id` to be carried when sending

### Extended Fields

- All special fields are prefixed with `qqbot_`
- Raw data is preserved in the `qqbot_raw` field
- `qqbot_raw_type` identifies the original QQBot event type (e.g., `C2C_MESSAGE_CREATE`)
- Attachment data is saved in the `qqbot_attachment` field with original attachment information

### Special Field Examples

```python
# Group @ message
{
  "type": "message",
  "detail_type": "group",
  "user_id": "MEMBER_OPENID",
  "group_id": "GROUP_OPENID",
  "qqbot_group_openid": "GROUP_OPENID",
  "qqbot_member_openid": "MEMBER_OPENID