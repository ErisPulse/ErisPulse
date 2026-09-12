# QQBot Platform Features Documentation

QQBotAdapter is an adapter built based on the official QQ Bot (QQ OpenAPI) protocol, integrating full-scene functionalities such as group chats, private chats, and channels. It provides OneBot12 standard events, standard API actions, and request operation interfaces.

---

## Documentation Information

- Corresponding Module Version: 5.0.0
- Maintainer: ErisPulse

## Basic Information

- Platform Overview: Official QQ Bot Development Interface, supports various scenarios including group chats, private chats, and channels
- Adapter Name: QQBotAdapter
- Connection Method: **WebSocket long connection** (default) or **Webhook HTTP callback** (configured per account, Ed25519 signature verification)
- Authentication Method: appId + clientSecret to obtain access_token (7200s, automatically refreshed 45s in advance)
- API Root Address: `https://api.bot.qq.com` (official unified domain since v5, sandbox is deprecated)
- OneBot12 Compatibility: Full coverage of message sending/receiving, events, **standard API actions**, and **request operations**
- Multi-Account Support: Supported, any account under `accounts` can run in parallel (can mix websocket/webhook modes)

## Configuration Instructions

```toml
# config.toml
[QQBot_Adapter]
intents = "[0, 9, 12, 25, 26, 27]"   # Global: Subscribed event intents (JSON array, supports event names)

[QQBot_Adapter.accounts.default]
appid = "YOUR_APPID"                 # QQ Bot Application ID (required)
secret = "YOUR_CLIENT_SECRET"        # QQ Bot Client Secret (required)
mode = "websocket"                   # Event reception method: websocket / webhook
bot_id = ""                          # Bot ID (left empty to auto-fetch; can be manually filled for Using() location)
gateway_url = ""                     # WebSocket Gateway URL (left empty to dynamically fetch via /gateway/bot)
api_base_url = "https://api.bot.qq.com"  # API root URL (customizable for proxy use)
webhook_path = "/webhook"            # Webhook callback path (生效于 mode=webhook)
enabled = true
```

**Breaking Changes in v5:**
- The official unified use of `api.bot.qq.com`, `sandbox` configuration is deprecated (old configurations are automatically migrated and ignored)
- Old flat configuration (directly writing appid/secret under `[QQBot_Adapter]`) is automatically migrated to `accounts.default`
- Framework is a **soft dependency**: Installing the adapter does not pull the framework version; runtime checks for `ErisPulse>=2.7.1` and prompts accordingly

**Intents Explanation (supports bit positions or event names):**

| Bit | Event Name | Description |
|----|------------|-------------|
| 0 | GUILDS | Channel changes |
| 1 | GUILD_MEMBERS | Channel member changes |
| 9 | GUILD_MESSAGES | Channel messages (private domain) |
| 12 | DIRECT_MESSAGE | Channel direct messages |
| 24 | GROUP_MEMBER | Group member changes (v5 addition) |
| 25 | GROUP_AND_C2C_EVENT | Group @ messages and private chat messages |
| 26 | INTERACTION | Interaction events (buttons, etc.) |
| 27 | MESSAGE_AUDIT | Message audit events |
| 30 | PUBLIC_GUILD_MESSAGES | Channel messages (public domain) |

## Message Sending

### Basic Sending

```python
from ErisPulse import sdk
qqbot = sdk.adapter.get("qqbot")

await qqbot.Send.To("user", user_openid).Text("Hello World!")

# Group mention message (automatically uses <qqbot-at-user id="x" /> format)
await qqbot.Send.To("group", group_openid).At("member_openid").Text("@you")

# Channel message (automatically uses <@user_id> format for mentions)
await qqbot.Send.To("channel", channel_id).Text("Channel message")

# Passive reply (automatically includes msg_id, no need to manually Reply)
await qqbot.Send.To("group", group_openid).Reply(msg_id).Text("Reply content")

# Rich Media (supports URL / local path / binary; automatically splits uploads over 5MB)
await qqbot.Send.To("group", gid).Image("https://example.com/img.png")

# Markdown (native / template)
await qqbot.Send.To("group", gid).Markdown("# Title\n- List")
await qqbot.Send.To("user", uid).Markdown(template_id=1, kv=[{"key": "title", "value": "Notice"}])

# Keyboard (automatically sets type to markdown and attaches bot_appid)
await qqbot.Send.To("group", gid).Keyboard(keyboard).Text("Please select")

# Streaming Message (for private chats)
await qqbot.Send.To("user", openid).Stream("Answer content")

# Multiple Accounts
await qqbot.Send.Using("account2").To("group", gid).Text("Sent from second bot")
```

## OneBot12 Standard API Actions

```python
result = await qqbot.Api.get_self_info()                     # Bot information
result = await qqbot.Api.get_group_info(group_openid)        # Group information
result = await qqbot.Api.get_group_member_list(group_openid) # List of group members (auto-paginated)
result = await qqbot.Api.get_guild_list()                    # List of guilds/channels
result = await qqbot.Api.get_channel_list(guild_id)          # List of sub-channels
await qqbot.Api.delete_message(message_id)                   # Delete message (auto-routed endpoint based on message source)
result = await qqbot.Api.get_status()                        # Multi-account running status
result = await qqbot.Api.Using("account2").get_self_info()   # Specify account
```

Supported standard actions: `get_self_info` / `get_group_info` / `get_group_member_info` / `get_group_member_list` / `get_guild_info` / `get_guild_list` / `get_guild_member_info` / `get_guild_member_list` / `get_channel_info` / `get_channel_list` / `set_channel_name` / `leave_channel` / `delete_message` / `get_status` / `get_version` / `get_supported_actions`. Unsupported actions return `retcode=10002`.

## Request Operations (Group Join Approval)

The `GROUP_JOIN_REQUEST` event is converted into the OneBot12 `request` event, supporting standardized approval:

```python
from ErisPulse.Core.Event import request as request_event

@request_event.on_request()
async def handle_join(event):
    if event.get("platform") == "qqbot":
        await event.approve()                  # Approve
        # await event.reject(comment="Reason") # Reject
```

`request_id` = Official `join_request_id`, the adapter automatically caches the request context and routes it to `POST /v2/groups/{group_openid}/approval_join_request/{member_openid}`.

## @Robot Detection Mechanism (Important)

On QQ, the fact that a user is mentioned ("@") is carried by an event name. In group messages, the @ marker is represented as `<@{group space openid}>` (which is **not in the same ID system** as the bot_id returned by READY). The adapter automatically handles the following:

1. **Marker Parsing**: Both `<@openid>` and `<qqbot-at-user>` styles are parsed into mention segments (no remnants remain in the text).
2. **Name Normalization**: When the bot name returned by `/users/@me` matches the nickname in the mentions array, it is recognized as an @-to-robot mention. The mention segment is normalized to bot_id (the original openid is preserved in `data.qqbot_openid`).
3. **OpenID Learning**: Automatically learns the bot's openid in each group, used for @ recognition in "receive all group messages" mode.
4. **Injection Guarantee**: `GROUP_AT_MESSAGE_CREATE` / `AT_MESSAGE_CREATE` guarantee the presence of a robot mention segment.

Therefore, `on_at_message()` / `event.is_at_message()` can be directly used on the qqbot platform. After enabling the "receive all group messages" permission, @ messages are pushed via `GROUP_MESSAGE_CREATE` (`GROUP_AT_MESSAGE_CREATE` no longer arrives), and the adapter can still recognize them.

## Platform Native API Method Family

The adapter exposes the complete QQ official API (see platform-features.md in the adapter repository):

- **Bot**: `get_me()`, `reply_interaction()`
- **Guild**: `get_guilds/get_guild/mute_guild_all/roles management/api_permission`
- **Subchannel**: `get_channels/get_channel/create_channel/update_channel/delete_channel/pins`
- **Guild Members**: `get_guild_members/get_guild_member/mute/roles/kick`
- **Permissions/Reactions/Schedules/Posts/Audio**: Full set of methods
- **Group Management** (some interfaces are only available to whitelisted bots): `get_group_members/get_group_bot_state/banlist/join_approval/mute/approval policy`
- **Menu Panels**: `get_custom_menu/update_custom_menu/command panel CRUD`
- **Rich Media**: `_upload_media` (URL/path/binary, automatically chunks if over 5MB), `stream_message` (streaming messages)

## WebSocket / Webhook Connection

### WebSocket Flow

1. Obtain `access_token` using `appId` + `clientSecret` (automatically refreshed 45 seconds in advance, with 3 retry attempts on failure)
2. Dynamically obtain the gateway address via `GET /gateway/bot` (use `gateway_url` directly when configuring)
3. OP_HELLO → Identify/Resume → READY (obtain `session_id` and `bot_id`) → Heartbeat loop
4. Reconnection on disconnection: up to 50 attempts, exponential backoff `min(5 * 2^n, 300)` seconds; OP_RECONNECT preserves session

### Webhook Mode

After setting account `mode = "webhook"`, register HTTP routes via ErisPulse router:

- Ed25519 signature verification (seed = secret filled cyclically to 32 bytes), verify `X-Signature-Ed25519` against `X-Signature-Timestamp + body`
- Automatic handling of op=13 signature verification handshake and op=0 event distribution
- Depends on `cryptography` library (installed with adapter)

## Error Code Description

| retcode | Description |
|---------|-------------|
| 0 | Success |
| 10001 | Missing parameter |
| 10002 | Unsupported action |
| 10003 | Unable to determine target/account |
| 32000 | Request timeout |
| 33000 | Network/API call exception |
| 34001 | Request does not exist or has expired (Request DSL) |
| 34100 | Media upload failed |
| 34000+ | Platform business error (passed through official code) |

## Usage Examples

### Handling Group Messages (Mention Detection)

```python
from ErisPulse.Core.Event import message

@message.on_at_message()
async def handle_at(event):
    if event.get("platform") != "qqbot":
        return
    text = event.get_text()
    if text == "签到":
        await event.reply("已签到")
```

### Handling Interaction Events

```python
from ErisPulse.Core.Event import notice

@notice.on_notice()
async def handle_interaction(event):
    if event.get("platform") != "qqbot":
        return
    if event.get("detail_type") == "qqbot_interaction":
        await qqbot.reply_interaction(event.get("qqbot_interaction_id"), code=0)
        button_id = event.get("qqbot_button_id", "")
        # Handle button...
```

### Multi-Account Startup

```toml
[QQBot_Adapter.accounts.bot_a]
appid = "A_APPID"
secret = "..."
enabled = true

[QQBot_Adapter.accounts.bot_b]
appid = "B_APPID"
secret = "..."
mode = "webhook"
enabled = true
```

Two accounts start in parallel: bot_a uses WebSocket, bot_b uses Webhook, and they do not interfere with each other.