# QQBot Platform Features Documentation

QQBotAdapter is an adapter built on the official QQ bot (QQ OpenAPI) protocol, integrating full-scenario features such as group chat, private chat, and guilds, and providing OneBot12 standard events, standard Api actions, and request action interfaces.

---

## Document Information

- Corresponding module version: 5.3.3
- Maintainer: ErisPulse
- Last updated: 2026-11-10

## Basic Information

- Platform introduction: Official QQ bot development interface, supporting group chat, private chat, guilds, and other scenarios
- Adapter name: QQBotAdapter
- Connection method: **WebSocket long connection** (default) or **Webhook HTTP callback** (per-account configuration, Ed25519 signature verification)
- Authentication: appId + clientSecret to obtain an access_token (valid 7200s, auto-refreshed 45s in advance)
- API base URL: `https://api.bot.qq.com` (the official unified domain since v5; sandbox is deprecated)
- OneBot12 compatibility: full coverage of message sending/receiving, events, **standard Api actions**, and **request actions**
- Multiple accounts: supported; any account under `accounts` runs in parallel (websocket/webhook modes can be mixed)

## Configuration

```toml
# config.toml
[QQBot_Adapter]
intents = "[0, 9, 12, 25, 26, 27]"   # Global: event intents to subscribe to (JSON array, supports event names)

[QQBot_Adapter.accounts.default]
appid = "YOUR_APPID"                 # QQ bot application ID (required)
secret = "YOUR_CLIENT_SECRET"        # QQ bot client secret (required)
mode = "websocket"                   # Event receiving method: websocket / webhook
bot_id = ""                          # Bot ID (leave empty to fetch automatically; can be filled manually for Using() targeting)
gateway_url = ""                     # WebSocket gateway URL (leave empty to fetch dynamically via /gateway/bot)
api_base_url = "https://api.bot.qq.com"  # API base URL (customizable for proxying)
access_token_url = ""                # Custom token endpoint (leave empty to use the official endpoint)
webhook_path = "/webhook"            # Webhook callback path (effective when mode=webhook)
enabled = true
```

**v5 breaking changes:**
- The `sandbox` field is deprecated: the official unified domain `api.bot.qq.com` is used; sandbox in old configs is automatically migrated and ignored (with a warning printed)
- Old flat configuration (appid/secret written directly under `[QQBot_Adapter]`) is automatically migrated to `accounts.default`
- The framework is a **soft dependency**: installing the adapter will not pull in a framework version; at runtime `ErisPulse>=2.7.1` is detected and prompted

**intents description (supports bit numbers or event names):**

| Bit | Event Name | Description |
|----|--------|------|
| 0 | GUILDS | Guild changes |
| 1 | GUILD_MEMBERS | Guild member changes |
| 9 | GUILD_MESSAGES | Guild messages (private domain requires review) |
| 10 | GUILD_MESSAGE_REACTIONS | Guild message reactions |
| 12 | DIRECT_MESSAGE | Guild direct messages |
| 24 | GROUP_MEMBER | Group member changes (**new in v5**) |
| 25 | GROUP_AND_C2C_EVENT | Group @ messages and private chat messages |
| 26 | INTERACTION | Interaction events (buttons, etc.) |
| 27 | MESSAGE_AUDIT | Message audit events |
| 28 | FORUMS_EVENT | Forum events (private domain only) |
| 29 | AUDIO_ACTION | Audio operations |
| 30 | PUBLIC_GUILD_MESSAGES | Guild messages (public domain) |

```toml
# The two forms are equivalent
intents = "[0, 9, 12, 25, 26, 27]"
intents = '["GUILDS", "GUILD_MESSAGES", "DIRECT_MESSAGE", "GROUP_AND_C2C_EVENT", "INTERACTION", "MESSAGE_AUDIT"]'
```

## Standardization Alignment

This section describes the adapter's behaviors aligned with the ErisPulse standardization specifications. For specification details, see the SDK documentation "Request Action Specification" (`docs/en/standards/request-action-spec.md`) and "API Response Specification" (`docs/en/standards/api-response.md`).

### Error Code Normalization (5.3.x)

- **Platform errors unified to 34100**: when the official QQ API returns an error, `retcode=34100` is returned, and the original response (including the official `code`/`message`) is preserved in the `qqbot_raw` field (media upload failures also use 34100)
- **Timeout 33001**: API call timeouts return `retcode=33001` (the former 32000 is no longer used)
- **Missing recall context 10003**: `delete_message` returns `retcode=10003` (parameter error) when the context owning the message cannot be found
- **Request family reserved 34001/34003**: `34001` is returned when a request does not exist or has expired; `34003` is returned when the request context lacks routing parameters

| retcode | Description |
|---------|------|
| 0 | Success |
| 10001 | Missing parameters / empty endpoint |
| 10002 | Unsupported action |
| 10003 | Unable to determine send target/account, missing recall context, and other parameter errors |
| 33000 | Network/API call exception |
| 33001 | Request timeout |
| 34001 | Request does not exist or has expired (Request DSL) |
| 34003 | Request context lacks routing parameters (Request DSL) |
| 34100 | Platform business error (original response and official code preserved in `qqbot_raw`) |

### Notification Event Naming (5.3.x)

Friend add/remove notification events are unified to standard naming:

| Official Event | Converted detail_type | Description |
|----------|-------------------|------|
| FRIEND_ADD | `friend_increase` | Friend added (the former `friend_add` is deprecated) |
| FRIEND_DEL | `friend_decrease` | Friend removed (the former `friend_del` is deprecated) |

### Request Context Retention (since 5.3.2)

The group join request event entry maps `request_id` to the application context (group/applicant openid) and caches it (TTL 3600 seconds, cap of 512 entries, cleaned up after the request is processed successfully); when performing approval, it routes to `POST /v2/groups/{group_openid}/approval_join_request/{member_openid}`.

### Extended Action Routing (5.3.x)

Guild member permission queries are provided through extended actions with the platform prefix:

```python
result = await qqbot.Api.call("qqbot.get_channel_member_permissions", channel_id="...", member_id="...")
```

### Stream Send Reads send_context

Streaming messages (`.Stream()`) read `send_context`: within an event chain, the account from the current event source is used automatically; an account explicitly specified via `Using()` takes priority.

## Message Sending

### Basic Sending

```python
from ErisPulse import sdk
qqbot = sdk.adapter.get("qqbot")

# Send text
await qqbot.Send.To("user", user_openid).Text("Hello World!")

# Group @ message (automatically uses the <qqbot-at-user id="x" /> format)
await qqbot.Send.To("group", group_openid).At("member_openid").Text("@you")
await qqbot.Send.To("group", group_openid).AtAll().Text("Announcement")

# Guild channel message (@ automatically uses the <@user_id> format)
await qqbot.Send.To("channel", channel_id).Text("Guild channel message")

# Guild direct message (create the session first)
dms = await qqbot.create_dms(user_id, source_guild_id)
await qqbot.Send.To("dms", dms["data"]["guild_id"]).Text("Direct message")

# Reply to a message (passive reply, automatically carries msg_id)
await qqbot.Send.To("group", group_openid).Reply(msg_id).Text("Reply content")

# Multiple accounts (Using/Account specifies account name or bot_id)
await qqbot.Send.Using("account2").To("group", group_openid).Text("From the second bot")
```

### Rich Media

```python
# URL / local path / binary three-form support; automatic chunked upload for files over 5MB
await qqbot.Send.To("group", gid).Image("https://example.com/img.png")
await qqbot.Send.To("user", uid).Image("/path/to/local.png")
await qqbot.Send.To("user", uid).Voice(open("audio.mp3", "rb").read())
await qqbot.Send.To("user", uid).Video("https://example.com/v.mp4")
await qqbot.Send.To("user", uid).File(b"...", filename="doc.pdf")

# Guild channel images go through multipart direct upload (file_image)
await qqbot.Send.To("channel", cid).Image(open("img.png", "rb").read())
```

`file_type` mapping: image=1, video=2, voice=3, file=4 (determined automatically by message segment type; `file` segments are inferred by file extension).

### Markdown / Ark / Embed / Keyboard

```python
# Native Markdown
await qqbot.Send.To("group", gid).Markdown("# Title\n- List item")

# Template Markdown
await qqbot.Send.To("user", uid).Markdown(template_id=1, kv=[{"key": "title", "value": "Notification"}])
await qqbot.Send.To("user", uid).Markdown(custom_template_id="23456", kv=[...])

# Ark template
await qqbot.Send.To("user", uid).Ark(23, [{"key": "a", "value": "b"}])

# Embed (guild channels/guild DMs only)
await qqbot.Send.To("channel", cid).Embed({"title": "Title", "content": "Content"})

# Keyboard (automatically set to the markdown type with bot_appid attached)
keyboard = {"content": {"rows": [[{"label": "Confirm", "type": 2, "data": "ok"}]]}}
await qqbot.Send.To("group", gid).Keyboard(keyboard).Text("Please choose")

# Merged forward (the official md has no collapse syntax, rendered as a quoted list; requires native Markdown permission, automatically falls back to plain text on failure)
await qqbot.Send.To("group", gid).MergeForward(nodes)
```

### Streaming Messages (new in v5, C2C only)

```python
# One-shot streaming send (input_state=10 completes directly)
await qqbot.Send.To("user", openid).Stream("Answer content")

# Multi-turn append streaming
r = await qqbot.stream_message(openid, "First segment", input_state=1, msg_id=passive_msg_id)
stream_id = r["data"]["id"]
r = await qqbot.stream_message(openid, "Second segment", stream_msg_id=stream_id, index=1, input_state=1)
r = await qqbot.stream_message(openid, "Final segment", stream_msg_id=stream_id, index=2, input_state=10)
```

### Message Recall

```python
# Standard Api action: automatically routes to the corresponding recall endpoint based on the message source (group/private chat/guild channel/DM)
await qqbot.Api.delete_message(message_id)
```

The adapter automatically registers the owning target of sent/received messages, so no manual passing of group_id/channel_id is needed; `retcode=10003` is returned when the context is missing.

## OneBot12 Standard Api Actions (new in v5)

```python
# Bot information
result = await qqbot.Api.get_self_info()

# Group management
result = await qqbot.Api.get_group_info(group_openid)          # {group_id, group_name}
result = await qqbot.Api.get_group_member_list(group_openid)   # automatic paginated aggregation
result = await qqbot.Api.get_group_member_info(group_openid, member_openid)

# Guild channels
result = await qqbot.Api.get_guild_list()
result = await qqbot.Api.get_guild_info(guild_id)
result = await qqbot.Api.get_guild_member_list(guild_id)
result = await qqbot.Api.get_channel_list(guild_id)
result = await qqbot.Api.get_channel_info(guild_id, channel_id)
await qqbot.Api.set_channel_name(guild_id, channel_id, "New name")
await qqbot.Api.leave_channel(guild_id, channel_id)            # delete sub-channel

# Meta actions
result = await qqbot.Api.get_status()   # {"good": bool, "bots": [...]}
result = await qqbot.Api.get_version()  # {"impl": "ErisPulse-QQBotAdapter", "onebot_version": "12"}

# Multiple accounts
result = await qqbot.Api.Using("account2").get_self_info()
```

Supported standard actions: `get_self_info` / `get_group_info` / `get_group_member_info` / `get_group_member_list` / `get_guild_info` / `get_guild_list` / `get_guild_member_info` / `get_guild_member_list` / `get_channel_info` / `get_channel_list` / `set_channel_name` / `leave_channel` / `delete_message` / `get_status` / `get_version` / `get_supported_actions`. Unsupported actions return `retcode=10002` (e.g., `get_friend_list`, as the official QQ API has no corresponding endpoint).

## Request Actions (Request DSL, new in v5)

The `GROUP_JOIN_REQUEST` (group join request) event is converted into a one-to-one interactive `request` event, supporting standardized approval:

```python
from ErisPulse.Core.Event import request as request_event

@request_event.on_request()
async def handle_join_request(event):
    if event.get("platform") != "qqbot":
        return
    # Auto-approve
    result = await event.approve()
    # Or reject: await event.reject(comment="Does not meet the requirements")
    # Or specify an account: await qqbot.Request(event["request_id"]).Using("account2").accept()
```

- `request_id` = official `join_request_id`
- The adapter automatically caches the application context (group/applicant openid), routing to `POST /v2/groups/{group_openid}/approval_join_request/{member_openid}` when executing
- Rejection can include `reject_reason`; `retcode=34001` is returned when the context has expired

You can also call the platform methods directly:

```python
await qqbot.approve_group_join(group_openid, member_openid, join_request_id, approve=True)
await qqbot.approve_group_join(group_openid, member_openid, approve=False, reject_reason="Reason")
```

## Platform Native API Method Family

The adapter exposes the full official QQ API (the first parameter is mostly the target ID; `account_id` optionally specifies an account):

### Bot / Interaction
`get_me()`, `reply_interaction(interaction_id, code=0)`

### Guild
`get_guilds()`, `get_guild(guild_id)`, `mute_guild_all(guild_id, mute_seconds)`,
`get_guild_roles` / `create_guild_role` / `update_guild_role` / `delete_guild_role`,
`get_guild_api_permission`, `demand_guild_api_permission(guild_id, channel_id, path, method, desc)`

### Sub-channel (Channel)
`get_channels`, `get_channel`, `create_channel(guild_id, name, type=0, ...)`, `update_channel(channel_id, name=..., ...)`, `delete_channel`,
`get_channel_pins`, `pin_message`, `unpin_message`

### Guild Members
`get_guild_members`, `get_guild_member`, `mute_guild_members` (batch/whole guild), `mute_guild_member`,
`add_guild_member_role` / `remove_guild_member_role`, `kick_guild_member`

### Permissions / Announcements / Reactions
`get_channel_role_permissions`, `update_channel_role_permissions`, `get_channel_member_permissions` (extended action `qqbot.get_channel_member_permissions`), `update_channel_member_permissions`, `create_announce`,
`add_reaction`, `delete_reaction`, `get_reaction_users`

### Schedules / Threads / Audio
`get_schedules`, `get_schedule`, `create_schedule`, `update_schedule`, `delete_schedule`,
`get_threads`, `get_thread`, `publish_thread(channel_id, title, content, format=3)`, `delete_thread`,
`control_audio(channel_id, audio_url, text, status)`, `mic_online`, `mic_offline`

### Group Management (v2, **some endpoints are only available to whitelisted bots**)
```python
await qqbot.get_group_info_raw(group_openid)          # Group information
await qqbot.get_group_bot_state(group_openid)         # Bot's state in the group
await qqbot.get_group_members(group_openid)           # Member list (with next_cursor)
await qqbot.get_group_member(group_openid, member_openid)
await qqbot.batch_remove_group_members(group_openid, [member_openid], add_to_blacklist=False)
await qqbot.get_group_member_blacklist(group_openid)
await qqbot.update_group_member_blacklist(group_openid, "add", [member_openid])
await qqbot.get_group_join_requests(group_openid)     # Group join request list
await qqbot.approve_group_join(...)                   # Approve group join requests
await qqbot.get_group_restrict_setting(group_openid)  # Mute settings
await qqbot.set_group_restrict(group_openid, [{"op": "add", "member_openid": "...", "mute_expire_at": 123}])
# Group join approval strategies
await qqbot.get_join_approval_strategies()
await qqbot.create_join_approval_strategy(strategy_dict)
await qqbot.update_join_approval_strategy(strategy_id, **fields)
await qqbot.delete_join_approval_strategy(strategy_id)
await qqbot.execute_join_approval_strategy(strategy_id)
await qqbot.update_join_approval_strategy_whitelist(strategy_id, "add", [user_ids])
```

### Custom Menu / Command Panel (new in v5)
```python
# Global custom menu (effective for C2C only; up to 5 sub-menu items, non-nestable)
menu_items = [
    {"type": "send_message", "content": {"label": "Help", "content": "/help"}},
    {"type": "link", "content": {"label": "Official website", "content": "https://example.com"}},
]
await qqbot.update_custom_menu(menu_items)
result = await qqbot.get_custom_menu()

# Command panel (scope: c2c/group/channel/dm; up to 20 per bot)
await qqbot.create_command_panel("c2c", [
    {"type": "command", "content": {"label": "Weather query", "content": "/weather"}},
    {"type": "link", "content": {"label": "More", "content": "https://example.com"}},
], remark="Panel remark", target_type="all")
await qqbot.get_command_panels("c2c")
await qqbot.get_command_panel(panel_id)
await qqbot.update_command_panel(panel_id, items)
await qqbot.delete_command_panel(panel_id)
await qqbot.update_command_panel_targets(panel_id, "add", user_openids=[...])
```

## WebSocket Connection

### Connection Flow

1. Obtain an access_token with appId + clientSecret (`POST https://bots.qq.com/app/getAppAccessToken`)
2. Dynamically obtain the gateway URL via `GET /gateway/bot` (used directly when `gateway_url` is configured)
3. Receive OP_HELLO (op=10) and get the heartbeat interval
4. Send OP_IDENTIFY (op=2) for authentication (intents support bitwise combination)
5. Receive READY, obtain session_id and bot_id, and send the connect meta event
6. Heartbeat loop (op=1) and event dispatch (op=0)

### Disconnection and Reconnection

- Maximum 50 reconnect attempts with exponential backoff `min(5 * 2^n, 300)` seconds
- On OP_RECONNECT (op=7) the session is retained (Resume); on OP_INVALID_SESSION (op=9) re-Identify
- The reconnect counter is reset automatically when send/receive work normally

### Token Management

- The access_token is valid for 7200 seconds and is **auto-refreshed 45 seconds in advance** (lazily checked at request time)
- Refresh failures are automatically retried 3 times (with increasing delay)
- Request headers: `Authorization: QQBot {token}` + **`X-Union-Appid: {appid}`** (new in v5)

## Webhook Integration (new in v5)

Set the account's `mode` to `webhook` to switch to HTTP callback for receiving events:

```toml
[QQBot_Adapter.accounts.mybot]
appid = "..."
secret = "..."
mode = "webhook"
webhook_path = "/webhook"    # multiple webhook accounts automatically append the account name to avoid conflicts
```

- The adapter registers HTTP routes via the ErisPulse router; the startup log outputs the full callback URL
- **Ed25519 signature verification**: seed = the secret cyclically padded to 32 bytes; verifies the `X-Signature-Ed25519` signature over `X-Signature-Timestamp + body`
- Automatically handles the op=13 signature verification handshake (callback URL configuration validation) and op=0 event dispatch
- Depends on the `cryptography` library (installed together with the adapter)

## Event Subscription and the openid System

1. QQBot uses the openid system rather than QQ numbers; user/group identifiers are all openid strings
2. Group messages are only received by default when a user @-mentions the bot (`GROUP_AT_MESSAGE_CREATE`)
3. **Receiving all group messages**: the corresponding permission must be enabled in the bot management console on the [QQ Open Platform](https://q.qq.com/) (there is no API to set it); once enabled, non-@ group messages are pushed as `GROUP_MESSAGE_CREATE`, and the adapter fully supports the conversion (marked `qqbot_is_at_message=false`; if the message contains an @-bot marker, it is automatically recognized as an @ message)
4. **@ detection**: QQ carries "being @" through the event name, and the @ marker in group messages is `<@{group openid}>` (an id system different from the READY bot_id). The adapter automatically parses both marker styles and injects/normalizes the bot mention segment, ensuring `on_at_message()`/`is_at_message()` work; it also automatically learns the bot's openid in each group, so @ messages within `GROUP_MESSAGE_CREATE` under the "receive all group messages" mode can also be recognized (the original openid is preserved in the mention segment's `data.qqbot_openid`)
5. Passive replies: group/private chat messages must carry `msg_id` or `event_id`, which the adapter automatically caches and attaches
6. `event_id` cannot be mixed with rich media (official limitation); the adapter handles this with automatic degradation
7. Sending may trigger an audit; the result is notified via the `qqbot_audit_pass` / `qqbot_audit_reject` events
8. Call `shutdown()` on program exit to release resources

## Usage Examples

### Handling Group Messages (@ detection)

```python
from ErisPulse.Core.Event import message

@message.on_at_message()
async def handle_at(event):
    if event.get("platform") != "qqbot":
        return
    text = event.get_text()
    if text == "check-in":
        await event.reply("Checked in")
```

### Handling Button Interactions

```python
from ErisPulse.Core.Event import notice

@notice.on_notice()
async def handle_interaction(event):
    if event.get("detail_type") != "qqbot_interaction":
        return
    button_id = event.get("qqbot_button_id")
    await qqbot.reply_interaction(event.get("qqbot_interaction_id"), code=0)
    if button_id == "confirm":
        await qqbot.Send.To("group", event.get("group_id")).Text("Confirmed")
```

### Multiple Account Startup

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

Both accounts start in parallel: bot_a uses WebSocket and bot_b uses Webhook, without affecting each other.