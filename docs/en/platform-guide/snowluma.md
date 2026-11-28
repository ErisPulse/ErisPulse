# SnowLuma Platform Features Documentation

SnowLumaAdapter is an adapter built on top of the SnowLuma backend (NTQQ hook), communicating via the OneBot v11 protocol. It is installed as an optional extension of `ErisPulse-OneBot11Adapter[snowluma]` (`pip install "ErisPulse-OneBot11Adapter[snowluma]"`).

---

## Document Information

- Corresponding module version: 0.3.4
- Maintainer: ErisPulse
- Protocol version: OneBot v11 (NapCat/go-cqhttp compatible extensions)
- Last updated: 2026-11-10

## Basic Information

- Platform overview: SnowLuma is a QQ protocol implementation based on the NTQQ hook, with its APIs fully aligned to NapCat, providing services externally via the OneBot v11 protocol (default ports: HTTP 3000, WS 3001)
- Adapter name: SnowLumaAdapter
- Supported protocol/API version: OneBot V11 (the official action catalog contains 200 actions in total, fully covered by the adapter; fully compatible with NapCat and can connect directly to a NapCat backend)
- Multi-account support: multi-account architecture by default, supporting configuring and running multiple accounts simultaneously
- Configuration key: `SnowLuma_Adapter`
- i18n: supports 5 languages (zh-CN / zh-TW / en / ja / ru)

### Relationship with the OneBot11 Adapter

SnowLuma uses the OB11 protocol; standard action and event conversion is isomorphic with the OneBot11 adapter (OB12 standard action names are automatically mapped).
Main differences:

1. **Default client mode**: actively connects to the SnowLuma WS (`ws://127.0.0.1:3001`), no public network listening required; also supports server (reverse WS) / http (API + polling) / webhook (API + reporting) — four modes in total
2. **Automatic bot_id detection**: no need to fill in the QQ number in the account configuration; the adapter automatically detects and maintains the `self_id → account_name` mapping after startup
3. **Full wrapping of 200 actions**: 169 typed methods (127 general extensions + 42 SnowLuma-specific), with the rest being Core direct calls / ApiDSL passthrough / server-side aliases; for the complete comparison see the adapter repository [docs/api-coverage.md](https://github.com/ErisPulse/ErisPulse-SnowLumaAdapter/blob/main/docs/api-coverage.md)
4. **Merged-forward extension pipeline**: dedicated endpoint + `upload_forward_msg` (upload nodes to get resid) + `get_forward_msg` (parse forwarded content), with three-level fallback

---

## Standard API Actions (Api DSL)

The adapter automatically maps OneBot12 standard action names to OB11 action names, so modules can call them uniformly across platforms:

| OB12 Standard Action | OB11 Action | Description |
|--------------|-----------|------|
| get_self_info | get_login_info | Field normalization: user_id/user_name/user_displayname |
| get_user_info | get_stranger_info | Field normalization |
| delete_message | delete_msg | Recall a message |
| leave_group | set_group_leave | Leave a group |
| upload_file | upload_group_file / upload_private_file | Extended optional group_id/user_id parameters |

### Basic Usage

```python
from ErisPulse import sdk
snowluma = sdk.adapter.get("snowluma")

# Get bot information
result = await snowluma.Api.get_self_info()
print(result["data"]["user_id"], result["data"]["user_name"])

# Recall a message
await snowluma.Api.delete_message(message_id=123456)

# upload_file extended parameters (OB11 file upload binding target, group_id/user_id optional)
await snowluma.Api.upload_file(type="path", name="doc.pdf", path="./doc.pdf", group_id="123456")
await snowluma.Api.upload_file(type="url", name="img.jpg", url="https://...", user_id="789")

# Specify an account (multi-account)
result = await snowluma.Api.Using("main").get_self_info()

# A few actions such as server-side aliases are invoked via the call() escape hatch (SnowLuma/NapCat common)
result = await snowluma.Api.call("upload_foward_msg", messages=[...])  # alias of upload_forward_msg
```

> **Naming convention**: OB11 protocol extensions use the action name directly (`send_poke`), without the `snowluma.` prefix. Only truly platform-unique features use `{prefix}.xxx`.

## Standardization Alignment

This section describes how the adapter aligns with the ErisPulse standardization specifications. For details, see the SDK documentation "Request Action Specification" (`docs/en/standards/request-action-spec.md`) and "API Response Specification" (`docs/en/standards/api-response.md`).

### Request Event Handling (since 0.3.3)

The adapter implements the receiving and responding of request events according to the request action specification (isomorphic with the OneBot11 adapter):

- **Context retention**: the event entry maps `request_id` to `{request_type, sub_type, group_id, account, ts}` and caches it (TTL 3600 seconds, cap of 512 entries, cleared after the request is handled successfully) for subsequent `accept()`/`reject()` routing
- **Endpoint routing priority**: explicit kwargs of `accept()`/`reject()` (`request_type`/`sub_type`/`group_id` are reserved names) > context retained from the event > fall back to the friend endpoint (`set_friend_add_request`) and emit a WARNING
- **Group invitation/join request**: when `request_type == "group"`, it is correctly routed to `set_group_add_request` (join `sub_type="add"`, invitation `sub_type="invite"`)
- **Deprecation note**: specifying the request type via the private parameter `_request_type` is deprecated; values passed this way will be ignored

### call_api Error Codes

- HTTP call failure (connection error/timeout) returns a standard failure response with `retcode=33001`
- Abnormal response format (cannot be parsed into the standard structure) returns `retcode=34100`, with the raw data kept in the `snowluma_raw` field

| retcode | Meaning | Trigger Scenario |
|---------|------|----------|
| 0 | Success | Action executed successfully |
| 33001 | Network error | HTTP call failure, API call timeout |
| 34100 | Platform error | Abnormal response format (raw data kept in `snowluma_raw`) |

### Dual Compatibility of Account Fields and send_context

- `call_api` accepts both the standard field `account_id` and the legacy field name `_account_id` (standard name takes priority); the framework ApiDSL adapts automatically, and `account_id` is recommended in module code
- All Send DSL methods read `send_context`: within an event chain the account of the current event source is used automatically; an account explicitly specified via `Using()` takes priority

### Event Field Normalization

- The top-level `type` of meta events is unified to `"meta"` (the original `meta_event` is no longer used)
- All platform-specific fields are identified with the `snowluma_` prefix, with raw data kept in `snowluma_raw`

---

## Supported Message Sending Types

All send methods are implemented via chained syntax, for example:

```python
from ErisPulse import sdk
snowluma = sdk.adapter.get("snowluma")

# Send using the default account
await snowluma.Send.To("group", group_id).Text("Hello World!")

# Send using a specific account
await snowluma.Send.Using("main").To("group", group_id).Text("Message from the main account")

# Chained modifiers: @user + reply
await snowluma.Send.To("group", group_id).At(123456).Reply(msg_id).Text("Reply message")
```

### Basic Send Methods

- `.Text(text: str)`: Sends a plain text message.
- `.Image(file: Union[str, bytes], filename: str = "image.png")`: Sends an image (supports URL, Base64, or bytes).
- `.Voice(file: Union[str, bytes], filename: str = "voice.amr")`: Sends a voice message.
- `.Video(file: Union[str, bytes], filename: str = "video.mp4")`: Sends a video message.
- `.Face(id: Union[str, int])`: Sends a QQ emoticon.
- `.File(file: Union[str, bytes], filename: str = "file.dat")`: Sends a file.
- `.MergeForward(nodes, title="Merged Chat History")`: Sends a merged-forward message (see the next section).
- `.Raw_ob12(message: List[Dict], **kwargs)`: Sends a message in OneBot12 format (automatically converted to OB11; a list of pure node segments is automatically routed to merged forward).
- `.Recall(message_id: Union[str, int])`: Recalls a message.

### Merged Forward

```python
nodes = [
    {
        "type": "node",
        "data": {
            "user_id": "10000",
            "nickname": "MyBot",
            "content": [{"type": "text", "data": {"text": "[1/3] Title\nBody..."}}],
        },
    },
]

# Send merged forward (three-level fallback, applicable to both SnowLuma / NapCat backends):
# ① Dedicated endpoint send_group/private_forward_msg (NapCat native, SnowLuma compatible)
# ② upload_forward_msg to get resid → send_msg sends the forward segment (SnowLuma extension pipeline)
# ③ send_msg directly sends the node segments
await snowluma.Send.To("group", group_id).MergeForward(nodes)

# Parse a received merged-forward message (inbound forward segments are passed through as onebot11_forward, data.id is the resid)
result = await snowluma.Api.get_forward_msg(id="resid_xxx")
```

### Group Operation Methods

The following methods require specifying the target group via `To("group", group_id)`:

- `.Kick(user_id, reject_add_request=False)`: Kicks a group member.
- `.Ban(user_id, duration=1800)`: Mutes a group member (in seconds); 0 means unmute.
- `.WholeBan(enable=True)`: Enables/disables mute for all members.
- `.SetAdmin(user_id, enable=True)`: Sets/removes a group admin.
- `.SetCard(user_id, card="")`: Sets a group card (member alias).
- `.SetGroupName(name)`: Changes the group name.
- `.Leave(is_dismiss=False)`: Leaves the group (the owner can dismiss it).
- `.SetTitle(user_id, title="")`: Sets a group title.
- `.SetPortrait(file)`: Sets the group avatar.

### Poke / Social

- `.GroupPoke(user_id)`: Pokes within a group (requires `To("group", group_id)`).
- `.FriendPoke(user_id)`: Pokes a friend.
- `.SendPoke(user_id)`: Sends a poke (general).
- `.SetMsgEmojiLike(message_id, emoji_id)`: Message emoji reaction.

### QQ Zone

- `.QzoneMsg(content)`: Posts a QQ Zone moment.
- `.QzoneLike(tid)` / `.QzoneUnlike(tid)`: Like/unlike.
- `.QzoneComment(tid, content)`: Comment.
- `.QzoneDelete(tid)`: Delete.

### Group Files / Message History / Read Status

- `.UploadGroupFile(file, name)`: Uploads a group file (requires `To("group", group_id)`).
- `.GetGroupFileUrl(file_id)`: Gets the group file download URL.
- `.GetGroupMsgHistory(message_id=0, count=20)`: Gets group message history (message_id=0 starts from the latest).
- `.GetFriendMsgHistory(user_id, count=20)`: Gets friend message history.
- `.MarkMsgAsRead(message_id)`: Marks as read by message ID.
- `.SetOnlineStatus(status)`: Sets the online status.

### Send to Conversation (SnowLuma extension, group/private auto-routing)

- `.AIRecord(character, text, chat_type=1)`: Sends an AI voice to the group (requires `To("group", group_id)`; characters come from `Api.get_ai_characters`).
- `.CustomFace(emoji_id, reply_to=None)`: Sends an account's favorite emoji (preserves the emoji display style).
- `.FlashMsg(fileset_id)`: Sends a flash-transfer message (the peer can download it upon receipt).
- `.ForwardSingle(message_id)`: Forwards a single message to the current conversation.
- `.TuwenArk(title, desc, jump_url, summary="[Share]", preview_url=...)`: Sends an image-text Ark card.

### More Send Convenience Methods

| Method | Corresponding Action | Description |
|------|---------|------|
| `.GroupReaction(msg_id, emoji_id)` | `set_group_reaction` | Group emoji reaction |
| `.SetEssenceMsg(msg_id)` | `set_essence_msg` | Set essence message |
| `.DeleteEssenceMsg(msg_id)` | `delete_essence_msg` | Remove essence message |
| `.SetFriendRemark(uid, remark)` | `set_friend_remark` | Set friend remark |
| `.OcrImage(image)` | `ocr_image` | OCR image recognition |
| `.GetImage(file)` | `get_image` | Get image info |
| `.GetRecord(file)` | `get_record` | Get voice info |
| `.FetchPttText(message_id)` | `fetch_ptt_text` | Voice-to-text |

### Chained Modifier Methods (combinable)

- `.At(user_id: Union[str, int])`: Mentions a specified user (can be called multiple times).
- `.AtAll()`: Mentions all members.
- `.Reply(message_id: Union[str, int])`: Replies to a specified message.

---

## OB11 Extension Actions (Api DSL)

The official action catalog contains **200 actions** in total; the adapter provides typed wrappers for 169 of them (`OB11ExtensionApi` 127 general + `SnowLumaExtensionApi` 42 SnowLuma-specific), with the rest being Core direct calls / ApiDSL passthrough / server-side aliases; see the [coverage comparison table](https://github.com/ErisPulse/ErisPulse-SnowLumaAdapter/blob/main/docs/api-coverage.md) in the adapter repository for the per-action status.
All actions can be called directly via `Api.call("action_name", ...)` (the SnowLuma/NapCat common part is portable across backends). Group overview:

| Group | Representative Actions |
|------|----------|
| Poke / Social | send_poke / group_poke / friend_poke / send_like |
| Message Reactions / Essence | set_msg_emoji_like / get_msg_emoji_likes / fetch_emoji_like / set_essence_msg / get_essence_msg_list |
| Read / Status | mark_msg_as_read / mark_all_as_read / set_online_status / set_diy_online_status / set_input_status / nc_get_user_status |
| Message History | get_group_msg_history / get_friend_msg_history |
| Group Admin Extensions | set_group_reaction / set_group_remark / set_group_sign / set_group_todo (including cancel/complete/list) / get_group_info_ex / get_group_shut_list / get_group_at_all_remain / set_group_kick_members / set_group_member_invite_policy / set_group_search / set_group_robot_add_option |
| Group Tags / Admin Settings | add_group_tag / delete_group_tag / get_group_tags / get_group_admin_settings / set_group_add_option / set_group_member_permissions / set_group_new_member_history_visibility |
| Friends / Contacts | set_friend_remark / delete_friend / set_friends_category / get_unidirectional_friend_list / get_friends_with_category / get_doubt_friends_add_request (including handling) |
| Group Files | get_group_file_url / get_private_file_url / get_group_root_files / get_group_files_by_folder / create_group_file_folder / delete_group_file (including folder deletion/renaming) / move_group_file / trans_group_file / get_group_file_system_info |
| Group Info | get_group_honor_info / get_group_share_link / get_group_system_msg / get_group_ignore_add_request / get_group_ignored_notifies |
| Group Albums (list) | get_group_album_list / get_group_album_media_list |
| QQ Zone | send_qzone_msg / get_qzone_msg_list / get_qzone_feeds / like_qzone / unlike_qzone / comment_qzone / delete_qzone_msg |
| Merged Forward / Single Forward | get_forward_msg / upload_forward_msg / send_forward_msg / forward_group_single_msg / forward_friend_single_msg |
| Ark Cards / Mini Apps | send_ark_share / send_group_ark_share / share_peer / share_group_ex / send_tuwen_ark / get_mini_app_ark / get_share_link |
| AI Voice | get_ai_characters / get_ai_record / send_group_ai_record |
| Group Notices / Device Model / Dress-Up | get_group_notice / send_group_notice / delete_group_notice / get_model_show / set_model_show / get_friend_dress |
| Media / OCR | ocr_image / get_image / get_record / fetch_ptt_text |
| Credentials / Capabilities | get_cookies / get_csrf_token / get_credentials / get_clientkey / can_send_image / can_send_record / get_version_info |
| Tools / Misc | check_url_safely / clean_cache / get_file / get_rkey / get_rkey_server / translate_en2zh / get_online_clients / get_profile_like / click_inline_keyboard_button |

### Usage Examples

```python
snowluma = sdk.adapter.get("snowluma")

# Mark as read (located by message ID)
await snowluma.Api.mark_msg_as_read(message_id=123)

# Voice-to-text (located by message ID)
result = await snowluma.Api.fetch_ptt_text(message_id=123)

# Emoji reaction details
result = await snowluma.Api.get_msg_emoji_likes(message_id=123)

# Group notice
await snowluma.Api.send_group_notice(group_id=123456, content="Announcement", pinned=1)

# AI voice
await snowluma.Api.send_group_ai_record(group_id=123456, character="1002", text="Hello")
```

## SnowLuma-Specific Actions (SnowLumaExtensionApi)

The following actions are specific to the SnowLuma server (not common to NapCat/Lagrange), and are likewise provided as typed methods:

### QQ Zone Extensions

```python
# Moment details and one page of comments (requires access permission)
result = await snowluma.Api.get_qzone_msg_detail(tid="tid_xxx", num=20)
# Change the visibility of an already-posted moment: 1=everyone, 4=friends, 16=part of friends, 64=self only, 128=hidden from part of friends
await snowluma.Api.set_qzone_msg_right(tid="tid_xxx", ugc_right=64)
# Blacklist/unblacklist someone (the bot's own Zone blacklist)
await snowluma.Api.set_qzone_ban(user_id=789, enable=True)
```

### Group Albums

```python
result = await snowluma.Api.get_qun_album_list(group_id=123456)
await snowluma.Api.upload_image_to_qun_album(group_id=123456, album_id="a1", album_name="Album", file="https://a.jpg")
await snowluma.Api.upload_video_to_qun_album(group_id=123456, album_id="a1", album_name="Album", file="./v.mp4")
await snowluma.Api.do_group_album_comment(group_id=123456, album_id="a1", lloc="xxx", content="Nice shot")
await snowluma.Api.del_group_album_media(group_id=123456, album_id="a1", lloc="xxx")
```

### System Emoticons

```python
result = await snowluma.Api.fetch_sys_faces()            # Full catalog (by group)
result = await snowluma.Api.search_sys_faces(query="smile")  # Search by name/alias/number
result = await snowluma.Api.fetch_face_entity(face_id=1)   # Query by number
result = await snowluma.Api.fetch_super_face_id(face_id=1) # Whether it is in super-emoticon format
```

### Streaming Interfaces

```python
# Upload a file in chunks to the bot's local storage (new stream → chunk by chunk → is_complete merges, returns a sendable local path)
await snowluma.Api.upload_file_stream(stream_id="uuid", total_chunks=2, file_size=1024, filename="a.txt")
# Streaming download (file_info → file_chunk* → file_complete returned frame by frame)
await snowluma.Api.download_file_stream(file_id="cached-id", chunk_size=65536)
await snowluma.Api.download_file_image_stream(file="https://a.jpg")
await snowluma.Api.download_file_record_stream(file_id="cached-record")
await snowluma.Api.clean_stream_temp_file()
```

### Flash Transfer / Favorite Emojis / Low-Level Channels

```python
# QQ flash transfer: share code → fileset_id → send/list/direct link
fileset = await snowluma.Api.get_fileset_id(share_code="abcd1234")
await snowluma.Api.send_flash_msg(fileset_id="fs_xxx", group_id=123456)
result = await snowluma.Api.get_flash_file_list(fileset_id="fs_xxx")
result = await snowluma.Api.download_fileset(fileset_id="fs_xxx")

# Favorite emojis
await snowluma.Api.add_custom_face(file="https://a.gif")
result = await snowluma.Api.fetch_custom_face(count=10, return_type="url")
await snowluma.Api.send_custom_face(emoji_id="emoji_id_or_md5", group_id=123456)

# Low-level channels (advanced usage)
await snowluma.Api.send_packet(cmd="Oidb.0xxxx", data="hex...")
await snowluma.Api.request_decrypt_key(db_path="./db")
await snowluma.Api.bot_exit()
```

---

## Event Type Mapping

### Standard OB12 Mapping

| OB11 Raw Type | Converted detail_type | Description |
|--------------|-------------------|------|
| message_type: private | `private` | Private message |
| message_type: group | `group` | Group message |
| request_type: friend | `friend` | Friend request |
| request_type: group | `group` | Group request (join/invitation) |
| notice_type: group_upload | `group_file_upload` | Group file upload |
| notice_type: group_admin | `group_admin_change` | Group admin change |
| notice_type: group_increase | `group_member_increase` | Group member increase |
| notice_type: group_decrease | `group_member_decrease` | Group member decrease |
| notice_type: group_ban | `group_ban` | Group mute |
| notice_type: friend_add | `friend_increase` | Friend added |
| notice_type: friend_delete | `friend_decrease` | Friend removed |
| notice_type: group_recall / friend_recall | `message_recall` | Message recall |

### Platform-Specific Events and Extended Segments

- Platform-specific events (poke/honor, etc.) use a detail_type with the `snowluma_` prefix
- Unrecognized CQ code types are passed through with the `onebot11_{type}` prefix (protocol-level prefix)
- Inbound merged-forward message segments are `onebot11_forward` (`data.id` is the resid; the content can be parsed via `Api.get_forward_msg(id=...)`)

### Extended Field Notes

- All platform-specific fields are identified with the `snowluma_` prefix
- Raw event data is kept in the `snowluma_raw` field
- The raw event type is kept in the `snowluma_raw_type` field
- The top-level `type` of meta events is unified to `"meta"`

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
|------|----------|------|
| `get_raw_event()` | `dict` | Gets the complete raw SnowLuma event data |
| `get_raw_self_id()` | `str` | Gets the raw self_id (the bot's QQ number) |
| `get_sender_info()` | `dict` | Gets the full sender information (including nickname, role, level, etc.) |
| `get_sender_role()` | `str` | Gets the sender's role in the group (owner/admin/member) |
| `get_sender_level()` | `int` | Gets the sender's level |
| `get_sender_title()` | `str` | Gets the sender's group title |
| `is_system_message()` | `bool` | Determines whether it is a system message |

---

## Configuration Options

The SnowLuma adapter adopts a multi-account architecture, with each account configured independently. The configuration key is `SnowLuma_Adapter`.

### Account Configuration Fields

| Field | Type | Required | Default | Description |
|------|------|------|--------|------|
| `mode` | `str` | No | `"client"` | `client` (actively connects to WS) / `server` (reverse WS) / `http` (HTTP API + polling) / `webhook` (HTTP API + reporting) |
| `url` | `str` | No | `"ws://127.0.0.1:3001"` | WebSocket address for client mode (SnowLuma default WS port 3001) |
| `token` | `str` | No | `""` | Access token (Bearer authentication) |
| `server_path` | `str` | No | `"/"` | WebSocket path for server mode |
| `http_url` | `str` | No | `"http://127.0.0.1:3000"` | API address for http/webhook mode |
| `poll_interval` | `float` | No | `1.0` | Event polling interval for http mode (seconds) |
| `webhook_path` | `str` | No | `"/snowluma_{account}"` | Report routing prefix for webhook mode |
| `enabled` | `bool` | No | `true` | Whether to enable this account |
| `name` | `str` | No | `""` | Account note name |

> bot_id (QQ number) requires no configuration: the adapter detects it automatically after connecting and maintains the `self_id → account_name` mapping;
> `event.reply()` is automatically routed to the source account.

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

All send methods return a Task object, which can be awaited directly to obtain the send result. The returned result follows the ErisPulse adapter standardized return specification:

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

### Multi-Account Send Syntax

```python
# Account selection method
await snowluma.Send.Using("main").To("group", 123456).Text("Message from the main account")

# API call approach
await snowluma.call_api("send_msg", account_id="main", group_id=123456, message="Hello")
```

## self_id Automatic Mapping

The adapter automatically establishes a mapping from the OneBot `self_id` (QQ number) to `account_name`, which is used for event reply routing:

```python
@message.on_message()
async def handler(event):
    # Automatically routed to the correct account
    await event.reply("Automatically routed to the source account")
```