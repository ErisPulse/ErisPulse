# SnowLuma Platform Feature Document

SnowLumaAdapter is an adapter built on the SnowLuma backend (NTQQ hook), communicating via the OneBot v11 protocol.

---

## Document Information

- Corresponding Module Version: 0.1.0
- Maintainer: ErisPulse

## Basic Information

- Platform Overview: SnowLuma is a QQ protocol implementation based on NTQQ hook, with APIs fully aligned with NapCat, providing services through the OneBot v11 protocol (default ports: HTTP 3000, WS 3001).
- Adapter Name: SnowLumaAdapter
- Supported Protocol/API Version: OneBot V11 (including SnowLuma extension actions, fully compatible with NapCat, directly connectable to NapCat backend)
- Multi-account Support: Default multi-account architecture, supports simultaneous configuration and operation of multiple accounts
- Configuration Key Name: `SnowLuma_Adapter`

### Relationship with OneBot11 Adapter

SnowLuma uses the OB11 protocol, with standard actions and events converted in the same structure as the OneBot11 adapter (OB12 standard action names are automatically mapped). Main differences:

1. **Default client mode**: Actively connects to SnowLuma WS (`ws://127.0.0.1:3001`), no need for public network listening
2. **Automatic bot_id recognition**: No need to fill in the QQ number in account configuration; the adapter automatically detects and maintains the `self_id → account_name` mapping after startup
3. **109 extension actions**: Poke, QQ Space, group files/photos, message history, highlights, read status, etc., SnowLuma/NapCat compatible extensions
4. **Merged forward extension chain**: Dedicated endpoint + `upload_forward_msg` (upload node takes resid) + `get_forward_msg` (parse forwarded content) three-level fallback

---

## Standard API Actions (API DSL)

The adapter automatically maps OneBot12 standard action names to OB11 action names, allowing modules to invoke cross-platform uniformly:

| OB12 Standard Action | OB11 Action | Description |
|----------------------|-------------|-------------|
| get_self_info        | get_login_info | Standardized fields user_id/user_name/user_displayname |
| get_user_info        | get_stranger_info | Standardized fields |
| delete_message       | delete_msg | Recall message |
| leave_group          | set_group_leave | Leave group |
| upload_file          | upload_group_file / upload_private_file | Extended group_id/user_id optional parameters |

### Basic Usage

```python
from ErisPulse import sdk
snowluma = sdk.adapter.get("snowluma")

# Get bot information
result = await snowluma.Api.get_self_info()
print(result["data"]["user_id"], result["data"]["user_name"])

# Recall message
await snowluma.Api.delete_message(message_id=123456)

# Specify account (multi-account)
result = await snowluma.Api.Using("main").get_self_info()

# Call extension actions through call() escape hatch (SnowLuma/NapCat universal)
result = await snowluma.Api.call("send_poke", group_id=123, user_id=456)
```

---

## Supported Message Sending Types

All sending methods are implemented using chained syntax, for example:

```python
from ErisPulse import sdk
snowluma = sdk.adapter.get("snowluma")

# Send using default account
await snowluma.Send.To("group", group_id).Text("Hello World!")

# Send using specific account
await snowluma.Send.Using("main").To("group", group_id).Text("Message from main account")

# Chained modifiers: @user + reply
await snowluma.Send.To("group", group_id).At(123456).Reply(msg_id).Text("Reply message")
```

### Basic Sending Methods

- `.Text(text: str)`: Send plain text message.
- `.Image(file: Union[str, bytes], filename: str = "image.png")`: Send image (supports URL, Base64, or bytes).
- `.Voice(file: Union[str, bytes], filename: str = "voice.amr")`: Send voice message.
- `.Video(file: Union[str, bytes], filename: str = "video.mp4")`: Send video message.
- `.Face(id: Union[str, int])`: Send QQ emoticon.
- `.File(file: Union[str, bytes], filename: str = "file.dat")`: Send file.
- `.MergeForward(nodes, title="Merged Chat Record")`: Send merged forward message (see next section).
- `.Raw_ob12(message: List[Dict], **kwargs)`: Send OneBot12 format message (automatically converted to OB11; pure node list automatically routed to merged forward).
- `.Recall(message_id: Union[str, int])`: Recall message.

### Merged Forward

```python
nodes = [
    {
        "type": "node",
        "data": {
            "user_id": "10000",
            "nickname": "MyBot",
            "content": [{"type": "text", "data": {"text": "【1/3】Title\nBody…"}}],
        },
    },
]

# Send merged forward (three-level fallback, suitable for SnowLuma / NapCat backends):
# ① send_group/private_forward_msg dedicated endpoint (native to NapCat, SnowLuma compatible)
# ② upload_forward_msg takes resid → send_msg sends forward segment (SnowLuma extension chain)
# ③ send_msg directly sends node segment
await snowluma.Send.To("group", group_id).MergeForward(nodes)

# Parse received merged forward message (inbound forward segments are transmitted as onebot11_forward, data.id is resid)
result = await snowluma.Api.get_forward_msg(id="resid_xxx")
```

### Group Operation Methods

The following methods require specifying the target group via `To("group", group_id)`:

- `.Kick(user_id, reject_add_request=False)`: Kick a group member.
- `.Ban(user_id, duration=1800)`: Mute a group member (in seconds), 0 means unmute.
- `.WholeBan(enable=True)`: Enable/Disable all-mute.
- `.SetAdmin(user_id, enable=True)`: Set/unset group admin.
- `.SetCard(user_id, card="")`: Set group nickname.
- `.SetGroupName(name)`: Modify group name.
- `.Leave(is_dismiss=False)`: Leave group (group owner can dismiss).
- `.SetTitle(user_id, title="")`: Set group title.
- `.SetPortrait(file)`: Set group avatar.

### Poke / Social

- `.GroupPoke(user_id)`: Poke a user in a group (requires `To("group", group_id)`).
- `.FriendPoke(user_id)`: Poke a friend.
- `.SendPoke(user_id)`: Send a poke (universal).
- `.SetMsgEmojiLike(message_id, emoji_id)`: Message emoji reaction.

### QQ Space

- `.QzoneMsg(content)`: Post a QQ Space status.
- `.QzoneLike(tid)` / `.QzoneUnlike(tid)`: Like/unlike.
- `.QzoneComment(tid, content)`: Comment.
- `.QzoneDelete(tid)`: Delete.

### Group Files / Message History / Read Status

- `.UploadGroupFile(file, name)`: Upload group file (requires `To("group", group_id)`).
- `.GetGroupFileUrl(file_id)`: Get group file download link.
- `.GetGroupMsgHistory(message_seq=0, count=20)`: Get group message history.
- `.GetFriendMsgHistory(user_id, count=20)`: Get friend message history.
- `.MarkMsgAsRead()`: Mark current conversation as read.
- `.SetOnlineStatus(status)`: Set online status.

### Chained Modifier Methods (can be combined)

- `.At(user_id: Union[str, int])`: @ specified user (can be called multiple times).
- `.AtAll()`: @ all members.
- `.Reply(message_id: Union[str, int])`: Reply to a specified message.

---

## OB11 Extension Actions (API DSL)

In addition to standard actions, `OB11ExtensionApi` mixin provides over 60 type-safe extension methods. All 109 extension actions can be directly called via `Api.call("action_name", ...)` (SnowLuma/NapCat universal). Group overview:

| Group | Representative Action |
|-------|-----------------------|
| Poke / Social | send_poke / group_poke / friend_poke / send_like |
| Message Reaction / Highlights | set_msg_emoji_like / get_emoji_likes / set_essence_msg / get_essence_msg_list |
| Read / Status | mark_msg_as_read / mark_group_msg_as_read / mark_all_as_read / set_online_status / set_input_status |
| Message History | get_group_msg_history / get_friend_msg_history |
| Group Management Extensions | set_group_reaction / set_group_remark / set_group_sign / set_group_todo / get_group_info_ex / get_group_shut_list / get_group_at_all_remain |
| Friends / Contacts | set_friend_remark / get_unidirectional_friend_list / get_friends_with_category / get_recent_contact |
| Group Files | get_group_file_url / get_private_file_url / get_group_root_files / get_group_files_by_folder / create_group_file_folder / delete_group_file |
| Group Album | get_group_album_list / get_group_album_media_list |
| QQ Space | send_qzone_msg / get_qzone_msg_list / get_qzone_feeds |
| Merged Forward | get_forward_msg / upload_forward_msg |
| Media / OCR | ocr_image / get_image |

---

## Event Type Mapping

### Standard OB12 Mapping

| OB11 Original Type | Converted detail_type | Description |
|--------------------|-----------------------|-------------|
| message_type: private | `private` | Private chat message |
| message_type: group | `group` | Group chat message |
| notice_type: group_upload | `group_file_upload` | Group file upload |
| notice_type: group_admin | `group_admin_change` | Group admin change |
| notice_type: group_increase | `group_member_increase` | Group member increase |
| notice_type: group_decrease | `group_member_decrease` | Group member decrease |
| notice_type: group_ban | `group_ban` | Group mute |
| notice_type: friend_add | `friend_increase` | Friend added |
| notice_type: friend_delete | `friend_decrease` | Friend removed |
| notice_type: group_recall / friend_recall | `message_recall` | Message recall |

### Platform-Specific Events and Extension Segments

- Platform-specific events (poke/honor, etc.) use `snowluma_` prefixed detail_type
- Unrecognized CQ code types are transmitted as `onebot11_{type}` prefix (protocol-level prefix)
- Inbound merged forward message segments are `onebot11_forward` (`data.id` is resid, use `Api.get_forward_msg(id=...)` to parse content)

### Extension Field Description

- All unique fields are prefixed with `snowluma_`
- Original event data is retained in `snowluma_raw` field
- Original event type is retained in `snowluma_raw_type` field

---

## Event Extension Methods

```python
from ErisPulse.Core.Event import message

@message.on_message()
async def handle_message(event):
    raw_self_id = event.get_raw_self_id()
    sender_info = event.get_sender_info()
    sender_role = event.get_sender_role()
```

| Method | Return Type | Description |
|--------|-------------|-------------|
| `get_raw_event()` | `dict` | Get complete SnowLuma raw event data |
| `get_raw_self_id()` | `str` | Get raw self_id (Bot's QQ number) |
| `get_sender_info()` | `dict` | Get complete sender information (includes nickname, role, level, etc.) |
| `get_sender_role()` | `str` | Get sender's role in group (owner/admin/member) |
| `get_sender_level()` | `int` | Get sender's level |
| `get_sender_title()` | `str` | Get sender's group title |
| `is_system_message()` | `bool` | Determine if it is a system message |

---

## Configuration Options

SnowLuma adapter adopts a multi-account architecture, with each account independently configured. The configuration key name is `SnowLuma_Adapter`.

### Account Configuration Fields

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `mode` | `str` | No | `"client"` | Running mode: `"client"` (active connection, recommended) or `"server"` (passive listening) |
| `url` | `str` | No | `"ws://127.0.0.1:3001"` | WebSocket address for client mode (SnowLuma default WS port 3001) |
| `token` | `str` | No | `""` | Access token (Bearer authentication) |
| `server_path` | `str` | No | `"/"` | WebSocket path for server mode |
| `enabled` | `bool` | No | `true` | Whether to enable this account |
| `name` | `str` | No | `""` | Account comment name |

> bot_id (QQ number) does not need to be configured: the adapter automatically recognizes it after connection and maintains the `self_id → account_name` mapping. `event.reply()` automatically routes to the originating account.

### Configuration Example

```toml
[SnowLuma_Adapter.accounts.main]
mode = "client"
url = "ws://127.0.0.1:3001"
token = ""
enabled = true

[SnowLuma_Adapter.accounts.second]
mode = "client"
url = "ws://192.168.1.100:3001"
token = "second_token"
enabled = true
```

---

## Send Method Return Values

All send methods return a Task object, which can be directly awaited to obtain the send result. The return result follows the ErisPulse adapter standardized return specification:

```python
{
    "status": "ok",
    "retcode": 0,
    "data": {...},
    "message_id": "123456",
    "message": "",
    "snowluma_raw": {...}
}
```

### Multi-account Send Syntax

```python
# Account selection method
await snowluma.Send.Using("main").To("group", 123456).Text("Message from main account")

# API call method
await snowluma.call_api("send_msg", account_id="main", group_id=123456, message="Hello")
```

## self_id Automatic Mapping

The adapter automatically establishes a mapping relationship from OneBot `self_id` (QQ number) to `account_name`, used for event routing:

```python
@message.on_message()
async def handler(event):
    # Automatically routes to the correct account
    await event.reply("Automatically routes to the originating account")
```