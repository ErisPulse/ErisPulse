# Discord Platform Feature Documentation

DiscordAdapter is an adapter built on the Discord Gateway (WebSocket) and REST API v10 protocol, integrating the core functionalities of Discord Bots and providing unified event handling and message operation interfaces.

---

## Document Information

- Corresponding module version: 4.4.3
- Maintainer: ErisPulse
- Discord API version: v10
- Last updated: 2026-11-10

## Basic Information

- **Platform Overview**: Discord is a widely popular community communication platform that supports various conversation formats such as servers, channels, and direct messages, and provides a comprehensive Bot development interface.
- **Adapter Name**: DiscordAdapter
- **Multi-account Support**: Supports configuring multiple Discord bots simultaneously.
- **Connection Method**: Gateway WebSocket (for receiving events) + REST API (for sending messages / invoking APIs)
- **Authentication Method**: Bot Token (HTTP header `Authorization: Bot {token}`, token included in the Gateway IDENTIFY payload)
- **Chained Modifiers Support**: Supports chained modifier methods such as `.Reply()`, `.At()`, and `.AtAll()`
- **OneBot12 Compatibility**: Supports sending OneBot12 formatted messages

## Configuration

DiscordAdapter supports multi-account configuration, with each account corresponding to an independent Discord Bot.

```toml
# config.toml

# Account 1
[DiscordAdapter.accounts.default]
token = "YOUR_BOT_TOKEN"       # Discord Bot Token (required)
intents = 33281                 # Gateway Intents (optional, default: 33281)
enabled = true                  # Whether to enable (optional, default: true)

# Account 2
[DiscordAdapter.accounts.bot2]
token = "ANOTHER_BOT_TOKEN"
intents = 33281
enabled = true
```

**Configuration Item Description (per account):**

- `token`: Discord Bot Token (required), obtained from [Discord Developer Portal](https://discord.com/developers/applications)
- `intents`: Gateway Intents bitmask (optional, default: `33281`), determines the types of events the Bot subscribes to
- `bot_id`: Bot's user ID (optional, automatically retrieved at runtime from the READY event, no need to manually fill)
- `enabled`: Whether to enable this account (optional, default: `true`)

### Gateway Intents

Intents use a bitmask, calculated as the bitwise OR (`|`) of each Intent value:

| Intent | Bit | Value | Description | Privileged |
|-------|------|------|------|------|
| GUILDS | `1 << 0` | 1 | Server creation/deletion/update, channel, role changes | No |
| GUILD_MEMBERS | `1 << 1` | 2 | Member join/leave/update | Yes |
| GUILD_MESSAGES | `1 << 9` | 512 | Server message sending/receiving | No |
| MESSAGE_CONTENT | `1 << 15` | 32768 | Message content (empty if this Intent is not present) | Yes |

Default value `33281` = `GUILDS(1) | GUILD_MESSAGES(512) | MESSAGE_CONTENT(32768)`.

> **Note**: Privileged Intents must be enabled in Discord Developer Portal → Bot → Privileged Gateway Intents. If the Bot is in more than 100 servers, Discord approval is also required.

**API Environment:**
- Discord REST API base URL: `https://discord.com/api/v10`
- Gateway WebSocket URL: Dynamically retrieved via `GET /gateway/bot`, typically `wss://gateway.discord.gg/?v=10&encoding=json`

## Standardization Alignment (4.4.3)

### Event Changes

1. **Event id uniqueness**: The `id` of derived events such as MESSAGE_UPDATE / MESSAGE_DELETE, REACTION_ADD / REMOVE (including REMOVE_ALL / REMOVE_EMOJI) has been changed to `"EventName:OriginalId"` (e.g., `MESSAGE_UPDATE:123456`), so they no longer collide with CREATE event ids and get deduplicated by the framework
2. **Event `self.account_id` injection**: All events carry the account name that produced them; in multi-account scenarios, `event.reply()` automatically sends via that account
3. **INTERACTION_CREATE event fix**: Previously incorrectly marked as `type="request"` (detail_type `interaction`), now changed to `type="notice"`, `detail_type="discord_interaction"`; interaction data is retained in the `discord_interaction` field

### API Signature Alignment

| Action | Signature | Description |
|------|------|------|
| get_channel_info | `(guild_id, channel_id)` | New signature with guild_id as the first parameter; when only one positional argument is passed, the old signature is still supported (treated as channel_id) |
| get_channel_list | `(guild_id, joined_only=False)` | Added the joined_only keyword parameter |
| get_guild_info / get_guild_list | - | data uses `guild_id` / `guild_name` (the old `group_id` / `group_name` fields are retained to avoid breaking existing callers) |

### Error Code Specification

Error codes have been standardized according to the SDK (the original `34000` is no longer used):

| retcode | Description |
|---------|------|
| 0 | Success |
| 33001 | Network error (connection failure, timeout, etc.) |
| 34100 | Platform rejection (the original response is retained in the `discord_raw` field) |
| 10002 | Unsupported action (`get_guild_member_list` / `set_guild_name` / `get_channel_member_info` / `get_channel_member_list` / `leave_channel` explicitly return this; Discord REST has no corresponding semantics) |
| 10003 | Parameter error (e.g., unable to recall a message because no corresponding context exists in the message registry) |

## v5 Paradigm Update (4.2.0)

This adapter has completed v5 paradigm alignment (incremental upgrade, API compatible):

- **BaseConverter inheritance**: Common converter fields are built by the framework's `build_base_event`
- **Api DSL**: Standard Api action mappings (see below)
- **Standard keyboard segment**: Converted to Discord components (action row + buttons); the .Keyboard(rows) modifier accepts generic structures
- **Standard interaction callback fields**: INTERACTION_CREATE events include interaction_id / button_data
- **spawn_background task ownership**: Connection tasks now use runtime.spawn_background
- **Framework soft dependency**: Runtime detection of ErisPulse>=2.7.1 with prompts; version logs output at startup

### Standard Api Actions

```python
from ErisPulse import sdk
discord = sdk.adapter.get("discord")

result = await discord.Api.get_self_info()                # GET /users/@me
result = await discord.Api.get_user_info(user_id)         # GET /users/{id}
result = await discord.Api.get_guild_info(guild_id)       # GET /guilds/{id} (data uses guild_id / guild_name)
result = await discord.Api.get_guild_list()               # GET /users/@me/guilds
result = await discord.Api.get_channel_info(guild_id, channel_id)  # GET /channels/{id} (new signature: guild_id as first parameter)
result = await discord.Api.get_channel_list(guild_id)     # GET /guilds/{id}/channels
result = await discord.Api.get_guild_member_info(gid, uid)
await discord.Api.delete_message(message_id)              # channel_id is auto-completed from the registry
await discord.Api.leave_guild(guild_id)
result = await discord.Api.Using("main").get_self_info()
```

### Buttons (keyboard / components)

```python
rows = [[{"label": "Click", "type": "callback", "data": "btn:1"},
         {"label": "Official Site",  "type": "link",     "data": "https://example.com"}]]
await discord.Send.To("channel", channel_id).Keyboard(rows).Text("Please select")
# Automatically converted to components: callback → custom_id / link → url
```

---

## Supported Message Sending Types

All sending methods are implemented using a fluent interface syntax, for example:
```python
from ErisPulse.Core import adapter
discord = adapter.get("discord")

await discord.Send.To("group", channel_id).Text("Hello World!")
```

The supported sending types include:
- `.Text(text: str)`: Sends a plain text message.
- `.Embed(embed: dict | list)`: Sends an Embed message, supporting single or multiple Embeds.
- `.MergeForward(nodes, title="Merged Chat Records")`: Sends a merged forward message (Embed: title + one field per message, ≤25 fields, value ≤1024).
- `.Image(file: bytes | str, filename: str = "image.png")`: Sends an image, supporting binary data or URL.
- `.File(file: bytes | str, filename: str = None)`: Sends a file, supporting binary data or URL.
- `.Reply(content: str, message_id: str)`: Replies to a specified message (convenient terminal method).
- `.Raw_ob12(message: List[Dict], **kwargs)`: Sends a OneBot12 formatted message.
- `.Raw_json(json_str: str)`: Sends any Discord API request JSON.

### Fluent Modifier Methods (Combinable)

Fluent modifier methods return `self`, supporting chained calls, and must be called before the final sending method:

- `.Reply(message_id: str)`: Replies (references) a specified message, setting `message_reference`.
- `.At(user_id: str)`: Mentions a specified user, converting to `<@user_id>`, can be called multiple times.
- `.AtAll()`: Mentions everyone, converting to `@everyone`.

### Chained Call Examples

```python
# Basic sending
await discord.Send.To("group", channel_id).Text("Hello")

# Reply to message
await discord.Send.To("group", channel_id).Reply(msg_id).Text("Reply message")

# Convenient reply (one step)
await discord.Send.To("group", channel_id).Reply("Reply content", msg_id)

# Mention user
await discord.Send.To("group", channel_id).At("user_id").Text("Hello")

# Mention multiple users
await discord.Send.To("group", channel_id).At("user1").At("user2").Text("Multiple users @")

# Mention all
await discord.Send.To("group", channel_id).AtAll().Text("Announcement")

# Combine methods
await discord.Send.To("group", channel_id).Reply(msg_id).At("user_id").Text("Composite message")

# Embed message
embed = {
    "title": "Notice",
    "description": "This is an embedded message",
    "color": 5814783,
    "fields": [{"name": "Field", "value": "Value", "inline": True}],
}
await discord.Send.To("group", channel_id).Embed(embed)

# Send image
await discord.Send.To("group", channel_id).Image("https://example.com/image.png")
```

### Private Message Sending

When sending private messages, the adapter will automatically create a DM channel:

```python
# Send private message
await discord.Send.To("user", user_id).Text("Private message content")
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

## Send Method Return Values

All send methods return a Task object, which can be directly awaited to obtain the send result. The returned result follows the ErisPulse adapter standardized return specification:

```python
{
    "status": "ok",           // Execution status: "ok" or "failed"
    "retcode": 0,             // Return code (0 indicates success)
    "data": {...},            // Raw Discord API response
    "message_id": "xxx",      // Message ID (when sending a message)
    "message": "",            // Error message
    "discord_raw": {...}      // Raw response data
}
```

### Error Code Descriptions

| retcode | Description |
|---------|-------------|
| 0 | Success |
| 33001 | Network error (connection failure, timeout, etc.) |
| 34100 | Platform rejection (insufficient permissions, invalid parameters, etc.; the raw response is preserved in the `discord_raw` field) |
| 10002 | Unsupported action (see the "Standardization Alignment (4.4.3)" error code specification) |
| 10003 | Invalid parameters (e.g., no corresponding message context when recalling a message) |

## Platform-Specific Event Types

A `platform == "discord"` check is required before using the platform-specific features of this section.

### Core Differences

1. **Server/Channel System**: Discord uses a two-tier structure of servers (Guilds) and channels (Channels); channels are the basic targets for sending messages
2. **Gateway Events**: All events are received through the WebSocket Gateway, using the Opcode + Dispatch mechanism
3. **Intents Subscription**: Event types are subscribed via bitmask; `MESSAGE_CONTENT` requires Privileged permission
4. **Message Segment Types**: Supports message segments such as text, image, file, video, audio, Embed, and Sticker
5. **Mention Format**: Discord uses the `<@user_id>` format to represent user mentions

### Extended Fields

All platform-specific fields are identified by the `discord_` prefix:
- `discord_raw`: Raw Discord event data
- `discord_raw_type`: Raw event type name (e.g., `MESSAGE_CREATE`)
- `discord_guild_id`: Guild ID
- `discord_channel_id`: Channel ID
- `discord_interaction`: Interaction event data (INTERACTION_CREATE)

### detail_type Mapping

| Discord Scenario | detail_type | Description |
|---|---|---|
| Channel message | `channel` | ErisPulse extension type |
| Direct message (DM) | `private` | OneBot12 standard type |

### Event Type Mapping

| Discord Event | OneBot12 type | detail_type | Description |
|---|---|---|---|
| MESSAGE_CREATE | message | channel/private | Message created |
| MESSAGE_UPDATE | message | channel/private | Message edited (id is `MESSAGE_UPDATE:original_id`) |
| MESSAGE_DELETE | notice | group_message_delete / private_message_delete | Message deleted (id is `MESSAGE_DELETE:original_id`) |
| MESSAGE_REACTION_ADD | notice | group_message_reaction_add | Reaction added (id is `MESSAGE_REACTION_ADD:original_id`) |
| MESSAGE_REACTION_REMOVE | notice | group_message_reaction_remove | Reaction removed (id is `MESSAGE_REACTION_REMOVE:original_id`) |
| GUILD_MEMBER_ADD | notice | group_member_increase | Member joined |
| GUILD_MEMBER_REMOVE | notice | group_member_decrease | Member left |
| GUILD_MEMBER_UPDATE | notice | group_member_update | Member info updated |
| GUILD_ROLE_CREATE | notice | group_role_create | Role created |
| GUILD_ROLE_DELETE | notice | group_role_delete | Role deleted |
| CHANNEL_CREATE | notice | channel_create | Channel created |
| CHANNEL_DELETE | notice | channel_delete | Channel deleted |
| INTERACTION_CREATE | notice | discord_interaction | Interaction (buttons, commands, etc.) |

> Since 4.4.3, the `id` of non-creation events such as MESSAGE_UPDATE / MESSAGE_DELETE and
> REACTION_ADD / REMOVE has been changed to `"EventName:original_id"` to avoid id conflicts
> with MESSAGE_CREATE events that would cause deduplication by the framework.

### Special Field Examples

```python
# Channel text message
{
  "type": "message",
  "detail_type": "channel",
  "user_id": "Sender ID",
  "user_nickname": "Username",
  "group_id": "Channel ID",
  "message_id": "Message ID",
  "self": {
    "platform": "discord",
    "user_id": "Bot ID",
    "account_id": "default"
  },
  "discord_raw": {...},
  "discord_raw_type": "MESSAGE_CREATE",
  "discord_guild_id": "Guild ID",
  "discord_channel_id": "Channel ID",
  "message": [
    {"type": "text", "data": {"text": "Hello"}}
  ],
  "alt_message": "Hello"
}

# Direct message
{
  "type": "message",
  "detail_type": "private",
  "user_id": "Sender ID",
  "user_nickname": "Username",
  "message_id": "Message ID",
  "discord_raw": {...},
  "discord_raw_type": "MESSAGE_CREATE",
  "discord_channel_id": "DM Channel ID",
  "message": [
    {"type": "text", "data": {"text": "Direct message content"}}
  ],
  "alt_message": "Direct message content"
}

# Message with an Embed
{
  "type": "message",
  "detail_type": "channel",
  "message": [
    {"type": "discord_embed", "data": {"embed": {...}}}
  ],
  "alt_message": "[Embedded message]"
}

# Message with attachments
{
  "type": "message",
  "detail_type": "channel",
  "message": [
    {"type": "text", "data": {"text": "Look at this picture"}},
    {"type": "image", "data": {"file": "Image URL", "url": "Image URL", "file_name": "image.png"}}
  ],
  "alt_message": "Look at this picture [Image]"
}
```

### Message Segment Types

Discord message content is automatically converted into corresponding message segments based on the `content`, `attachments`, and `embeds` fields:

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

1. Call `GET /gateway/bot` to get the WebSocket gateway URL
2. Connect to `wss://gateway.discord.gg/?v=10&encoding=json`
3. Receive opcode 10 HELLO: contains `heartbeat_interval`
4. Send opcode 2 IDENTIFY: includes token, intents, and properties
5. Start heartbeat loop: send opcode 1 Heartbeat at intervals of `heartbeat_interval`
6. Receive opcode 0 Dispatch: event dispatch (`t`=event name, `s`=sequence number, `d`=data)
7. Receive opcode 11 Heartbeat ACK: heartbeat acknowledgment

### Opcode Reference

| Opcode | Name | Direction | Description |
|--------|------|-----------|-------------|
| 0 | Dispatch | Receive | Event dispatch (includes `t`, `s`, `d` fields) |
| 1 | Heartbeat | Send/Receive | Heartbeat (includes last seq) |
| 2 | Identify | Send | Identity authentication |
| 6 | Resume | Send | Resume session |
| 7 | Reconnect | Receive | Server requests reconnection |
| 9 | Invalid Session | Receive | Invalid session |
| 10 | Hello | Receive | Connection handshake (includes heartbeat_interval) |
| 11 | Heartbeat ACK | Receive | Heartbeat acknowledgment |

### Reconnection and RESUME

- After a connection is disconnected, the adapter automatically retries the connection
- If a previous `session_id` exists, attempt to RESUME (opcode 6) the session first
- RESUME includes `token`, `session_id`, and the last `seq`, restoring missed events after resumption
- When opcode 7 (Reconnect) is received, maintain session state and reconnect
- When opcode 9 (Invalid Session) is received and `d=false`, clear the session and re-authenticate with IDENTIFY

### Heartbeat Mechanism

- After receiving HELLO, wait `heartbeat_interval * random()` milliseconds before sending the first heartbeat
- Subsequently, send a heartbeat every `heartbeat_interval` milliseconds
- The heartbeat includes the last `seq` value (opcode 1, `d: seq`)
- If an ACK (opcode 11) is not received within `heartbeat_interval` milliseconds after sending a heartbeat, consider the connection abnormal and reconnect

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

### Handling Private Messages

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
    "description": "Welcome to the ErisPulse Discord adapter",
    "color": 3447003,
    "fields": [
        {"name": "Version", "value": "4.4.3", "inline": True},
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
            f"Received {len(embeds)} embeds"
        )
```

### Handling Interaction Events

Since 4.4.3, INTERACTION_CREATE events are dispatched as `notice` / `discord_interaction`:

```python
from ErisPulse.Core.Event import notice

@notice.on_notice()
async def handle_interaction(event):
    if event.get("platform") != "discord":
        return
    if event.get("detail_type") != "discord_interaction":
        return

    interaction = event.get_interaction_data()  # Equivalent to event["discord_interaction"]
    if interaction.get("type") == 3:  # MESSAGE_COMPONENT
        await event.reply("Button clicked!")
```