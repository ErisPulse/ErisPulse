# Discord Platform Feature Documentation

The DiscordAdapter is an adapter built based on the Discord Gateway (WebSocket) and REST API v10 protocol. It integrates the core functionality of Discord Bots, providing a unified event handling and message operation interface.

---

## Document Information

- Corresponding Module Version: 4.0.0
- Maintainer: ErisPulse
- Discord API Version: v10

## Basic Information

- Platform Introduction: Discord is a widely popular community communication platform that supports various forms of sessions such as servers, channels, and direct messages (DMs), and provides a comprehensive Bot development interface.
- Adapter Name: DiscordAdapter
- Multi-Account Support: Supports configuring multiple Discord Bots simultaneously.
- Connection Method: Gateway WebSocket (receive events) + REST API (send messages/call interfaces).
- Authentication Method: Bot Token (HTTP Header `Authorization: Bot {token}`, Gateway IDENTIFY payload carries token).
- Chained Modifier Support: Supports chained modifier methods such as `.Reply()`, `.At()`, `.AtAll()`.
- OneBot12 Compatibility: Supports sending OneBot12 formatted messages.

## Configuration Description

The DiscordAdapter supports multi-account configuration, where each account corresponds to a separate Discord Bot.

```toml
# config.toml

# Account 1
[DiscordAdapter.accounts.default]
token = "YOUR_BOT_TOKEN"       # Discord Bot Token (Required)
intents = 33281                 # Gateway Intents (Optional, default 33281)
enabled = true                  # Enable (Optional, default true)

# Account 2
[DiscordAdapter.accounts.bot2]
token = "ANOTHER_BOT_TOKEN"
intents = 33281
enabled = true
```

**Configuration Item Descriptions (per account):**

- `token`: Discord Bot Token (Required), obtained from [Discord Developer Portal](https://discord.com/developers/applications).
- `intents`: Gateway Intents bit mask (Optional, default `33281`), determines the types of events the Bot subscribes to.
- `bot_id`: Bot's user ID (Optional, automatically obtained at runtime from the READY event, no need to manually fill in).
- `enabled`: Whether to enable this account (Optional, default `true`).

### Gateway Intents

Intents use a bit mask, calculated by bitwise ORing (`|`) the values of each Intent:

| Intent | Bit | Value | Description | Privileged |
|-------|------|------|------|------|
| GUILDS | `1 << 0` | 1 | Guild create/delete/update, channel, role changes | No |
| GUILD_MEMBERS | `1 << 1` | 2 | Member join/leave/update | Yes |
| GUILD_MESSAGES | `1 << 9` | 512 | Guild message send/receive | No |
| MESSAGE_CONTENT | `1 << 15` | 32768 | Message content (content is empty without this Intent) | Yes |

Default value `33281` = `GUILDS(1) | GUILD_MESSAGES(512) | MESSAGE_CONTENT(32768)`.

> **Note**: Privileged Intents must be enabled in Discord Developer Portal → Bot → Privileged Gateway Intents. If the Bot is in over 100 guilds, Discord audit is also required.

**API Environment:**
- Discord REST API Base URL: `https://discord.com/api/v10`
- Gateway WebSocket URL: Dynamically obtained via `GET /gateway/bot`, usually `wss://gateway.discord.gg/?v=10&encoding=json`

## Supported Message Sending Types

All sending methods are implemented via a chained syntax, for example:
```python
from ErisPulse.Core import adapter
discord = adapter.get("discord")

await discord.Send.To("group", channel_id).Text("Hello World!")
```

Supported sending types include:
- `.Text(text: str)`: Sends a plain text message.
- `.Embed(embed: dict | list)`: Sends an Embed message, supports single or multiple Embeds.
- `.Image(file: bytes | str, filename: str = "image.png")`: Sends an image, supports binary data or URL.
- `.File(file: bytes | str, filename: str = None)`: Sends a file, supports binary data or URL.
- `.Reply(content: str, message_id: str)`: Replies to a specific message (convenience terminal method).
- `.Raw_ob12(message: List[Dict], **kwargs)`: Sends a OneBot12 formatted message.
- `.Raw_json(json_str: str)`: Sends arbitrary Discord API request JSON.

### Chained Modifier Methods (Composable)

Chained modifier methods return `self`, supporting chaining calls. They must be called before the final sending method:

- `.Reply(message_id: str)`: Replies (references) to a specific message, sets `message_reference`.
- `.At(user_id: str)`: @mentions a specific user, converts to `<@user_id>`, can be called multiple times.
- `.AtAll()`: @mentions everyone, converts to `@everyone`.

### Chained Call Examples

```python
# Basic sending
await discord.Send.To("group", channel_id).Text("Hello")

# Reply to message
await discord.Send.To("group", channel_id).Reply(msg_id).Text("Reply content")

# Convenient reply (in one step)
await discord.Send.To("group", channel_id).Reply("Reply content", msg_id)

# @User
await discord.Send.To("group", channel_id).At("user_id").Text("Hello")

# @Multiple Users
await discord.Send.To("group", channel_id).At("user1").At("user2").Text("Multi-user @")

# @All
await discord.Send.To("group", channel_id).AtAll().Text("Announcement")

# Combined usage
await discord.Send.To("group", channel_id).Reply(msg_id).At("user_id").Text("Composite message")

# Embed message
embed = {
    "title": "Notification",
    "description": "This is an embedded message",
    "color": 5814783,
    "fields": [{"name": "Field", "value": "Value", "inline": True}],
}
await discord.Send.To("group", channel_id).Embed(embed)

# Send Image
await discord.Send.To("group", channel_id).Image("https://example.com/image.png")
```

### Direct Message Sending

When sending direct messages, the adapter automatically creates a DM channel:

```python
# Send DM
await discord.Send.To("user", user_id).Text("DM content")
await discord.Send.To("user", user_id).Embed(embed)
```

### Message Operations

```python
# Recall message
await discord.Send.To("group", channel_id).Recall(msg_id)

# OneBot12 format
ob12_msg = [
    {"type": "text", "data": {"text": "Hello "}},
    {"type": "mention", "data": {"user_id": "user_id"}},
]
await discord.Send.To("group", channel_id).Raw_ob12(ob12_msg)
```

## Sending Method Return Values

All sending methods return a Task object, which can be awaited directly to get the sending result. The return result follows the ErisPulse adapter standard return specification:

```python
{
    "status": "ok",           // Execution status: "ok" or "failed"
    "retcode": 0,             // Return code (0 for success)
    "data": {...},            // Discord API raw response
    "message_id": "xxx",      // Message ID (when sending a message)
    "message": "",            // Error message
    "discord_raw": {...}      // Raw response data
}
```

### Error Code Description

| retcode | Description |
|---------|------|
| 0 | Success |
| 33001 | Network error (connection failed, timeout, etc.) |
| 34000 | Discord API error (insufficient permissions, invalid parameters, etc.) |

## Unique Event Types

Use `platform == "discord"` check before using this platform's features.

### Core Differences

1. **Server/Channel System**: Discord uses a two-layer structure of Guilds (Servers) and Channels. Channels are the basic target for sending messages.
2. **Gateway Events**: All events are received via the WebSocket Gateway using Opcode + Dispatch mechanism.
3. **Intents Subscription**: Subscribe to event types via bit masks; `MESSAGE_CONTENT` requires Privileged permissions.
4. **Message Segment Types**: Supports message segments such as text, images, files, video, audio, Embeds, Stickers, etc.
5. **Mention Format**: Discord uses the `<@user_id>` format to represent user mentions.

### Extended Fields

All unique fields are prefixed with `discord_`:
- `discord_raw`: Raw Discord event data.
- `discord_raw_type`: Raw event type name (e.g., `MESSAGE_CREATE`).
- `discord_guild_id`: Guild ID.
- `discord_channel_id`: Channel ID.

### detail_type Mapping

| Discord Scenario | detail_type | Description |
|---|---|---|
| Channel Message | `channel` | ErisPulse extended type |
| Direct Message (DM) | `private` | OneBot12 standard type |

### Event Type Mapping

| Discord Event | OneBot12 type | detail_type | Description |
|---|---|---|---|
| MESSAGE_CREATE | message | channel/private | Message created |
| MESSAGE_UPDATE | message | channel/private | Message edited |
| MESSAGE_DELETE | notice | group_message_delete / private_message_delete | Message deleted |
| GUILD_MEMBER_ADD | notice | group_member_increase | Member joined |
| GUILD_MEMBER_REMOVE | notice | group_member_decrease | Member left |
| GUILD_MEMBER_UPDATE | notice | group_member_update | Member info updated |
| GUILD_ROLE_CREATE | notice | group_role_create | Role created |
| GUILD_ROLE_DELETE | notice | group_role_delete | Role deleted |
| CHANNEL_CREATE | notice | channel_create | Channel created |
| CHANNEL_DELETE | notice | channel_delete | Channel deleted |
| INTERACTION_CREATE | request | interaction | Interaction (buttons, commands, etc.) |

### Special Field Examples

```python
# Channel text message
{
  "type": "message",
  "detail_type": "channel",
  "user_id": "SenderID",
  "user_nickname": "Username",
  "group_id": "ChannelID",
  "message_id": "MessageID",
  "discord_raw": {...},
  "discord_raw_type": "MESSAGE_CREATE",
  "discord_guild_id": "GuildID",
  "discord_channel_id": "ChannelID",
  "message": [
    {"type": "text", "data": {"text": "Hello"}}
  ],
  "alt_message": "Hello"
}

# Private message
{
  "type": "message",
  "detail_type": "private",
  "user_id": "SenderID",
  "user_nickname": "Username",
  "message_id": "MessageID",
  "discord_raw": {...},
  "discord_raw_type": "MESSAGE_CREATE",
  "discord_channel_id": "DMChannelID",
  "message": [
    {"type": "text", "data": {"text": "DM content"}}
  ],
  "alt_message": "DM content"
}

# Message with Embed
{
  "type": "message",
  "detail_type": "channel",
  "message": [
    {"type": "discord_embed", "data": {"embed": {...}}}
  ],
  "alt_message": "[Embedded Message]"
}

# Message with attachment
{
  "type": "message",
  "detail_type": "channel",
  "message": [
    {"type": "text", "data": {"text": "Look at this picture"}},
    {"type": "image", "data": {"file": "ImageURL", "url": "ImageURL", "file_name": "image.png"}}
  ],
  "alt_message": "Look at this picture [Image]"
}
```

### Message Segment Types

Discord message content is automatically converted to corresponding message segments based on the `content`, `attachments`, and `embeds` fields:

| Source | Converted Type | Description |
|---|---|---|
| content text | `text` | Plain text content |
| content `<@id>` | `mention` | User mention |
| content `<@&id>` | `discord_role_mention` | Role mention |
| content `<#id>` | `discord_channel_mention` | Channel mention |
| attachments (image/*) | `image` | Image attachment |
| attachments (video/*) | `video` | Video attachment |
| attachments (audio/*) | `audio` | Audio attachment |
| attachments (other) | `file` | File attachment |
| embeds | `discord_embed` | Embedded message |
| sticker_items | `discord_sticker` | Sticker |

### discord_embed Message Segment

```json
{
  "type": "discord_embed",
  "data": {
    "embed": {
      "title": "Title",
      "description": "Description",
      "color": 12345,
      "fields": [...],
      "image": {"url": "..."},
      "thumbnail": {"url": "..."},
      "footer": {"text": "..."}
    }
  }
}
```

## Gateway Connection

### Connection Flow

1. Call `GET /gateway/bot` to obtain the WebSocket gateway URL
2. Connect to `wss://gateway.discord.gg/?v=10&encoding=json`
3. Receive opcode 10 HELLO: contains `heartbeat_interval`
4. Send opcode 2 IDENTIFY: carries token, intents, properties
5. Start heartbeat loop: send opcode 1 Heartbeat at intervals of `heartbeat_interval`
6. Receive opcode 0 Dispatch: event dispatch (`t`=event name, `s`=sequence, `d`=data)
7. Receive opcode 11 Heartbeat ACK: heartbeat confirmation

### Opcode Description

| Opcode | Name | Direction | Description |
|--------|------|------|------|
| 0 | Dispatch | Receive | Event dispatch (contains `t`, `s`, `d` fields) |
| 1 | Heartbeat | Send/Receive | Heartbeat (carries last `seq`) |
| 2 | Identify | Send | Authentication |
| 6 | Resume | Send | Resume session |
| 7 | Reconnect | Receive | Server requires reconnection |
| 9 | Invalid Session | Receive | Invalid session |
| 10 | Hello | Receive | Connection handshake (contains heartbeat_interval) |
| 11 | Heartbeat ACK | Receive | Heartbeat confirmation |

### Disconnect Reconnection and RESUME

- After disconnection, the adapter automatically retries connection
- If a `session_id` was previously available, RESUME (opcode 6) is attempted to restore the session
- RESUME carries `token`, `session_id`, and the last `seq`, and missed events are resent after restoration
- When opcode 7 (Reconnect) is received, keep session state and reconnect
- When opcode 9 (Invalid Session) is received and `d=false`, clear the session and re-IDENTIFY

### Heartbeat Mechanism

- After receiving HELLO, wait `heartbeat_interval * random()` milliseconds before sending the first heartbeat
- Subsequently, send a heartbeat every `heartbeat_interval` milliseconds
- The heartbeat carries the last `seq` value (opcode 1, `d: seq`)
- If no ACK (opcode 11) is received within `heartbeat_interval` after sending a heartbeat, the connection is considered abnormal and reconnection occurs

## Usage Examples

### Handling Channel Messages

```python
from ErisPulse.Core.Event import message
from ErisPulse import sdk

discord = sdk.adapter.get("discord")

@message.on_message()
async def handle_group_msg(event):
    if event.get("platform") != "discord":
        return

    text = event.get_text()
    channel_id = event.get("group_id")

    if text == "hello":
        await discord.Send.To("group", channel_id).Text("Hello!")
```

### Handling Direct Messages

```python
@message.on_message()
async def handle_private_msg(event):
    if event.get("platform") != "discord":
        return
    if not event.is_dm():
        return

    text = event.get_text()
    user_id = event.get("user_id")

    await discord.Send.To("user", user_id).Text(f"You said: {text}")
```

### Sending Embed Messages

```python
embed = {
    "title": "Server Announcement",
    "description": "Welcome to the ErisPulse Discord Adapter",
    "color": 3447003,
    "fields": [
        {"name": "Version", "value": "4.0.0", "inline": True},
        {"name": "Framework", "value": "ErisPulse", "inline": True},
    ],
    "footer": {"text": "Powered by ErisPulse"},
    "timestamp": "2025-01-01T00:00:00.000Z",
}
await discord.Send.To("group", channel_id).Embed(embed)
```

### Using Discord-Specific Methods

```python
@message.on_message()
async def handle(event):
    if event.get("platform") != "discord":
        return

    channel_id = event.get_channel_id()
    guild_id = event.get_guild_id()
    is_dm = event.is_dm()
    embeds = event.get_embeds()
    attachments = event.get_attachments()

    if embeds:
        await discord.Send.To("group", channel_id).Text(
            f"Received {len(embeds)} Embed(s)"
        )
```

### Handling Interaction Events

```python
from ErisPulse.Core.Event import request

@request.on_request()
async def handle_interaction(event):
    if event.get("platform") != "discord":
        return

    interaction = event.get_interaction_data()
    if interaction.get("type") == 3:  # MESSAGE_COMPONENT
        await event.reply("Button clicked!")