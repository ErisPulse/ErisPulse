# Bilibili Platform Feature Documentation

BilibiliAdapter is a Bilibili private message adapter based on bilibili-api-python, supporting dual login via Cookie / QR code scanning and event-driven private message sending/receiving.

---

## Document Information

- Corresponding module version: 0.1.0
- Maintainer: ErisPulse

## Basic Information

- Platform introduction: Bilibili private message bot (no official personal Bot API, uses the Web private message API via simulated login)
- Adapter name: BilibiliAdapter
- Multi-account support: Supported (one Bilibili account per bot account, with independent session listening)
- Connection method: Event-driven session listening (bilibili-api `Session`)
- Authentication method: Cookie (SESSDATA / bili_jct / buvid3 / dedeuserid) or panel QR code login
- Chain modifier support: Supports chained modifier methods such as `.Reply()`
- OneBot12 compatibility: Supports standard message segments (text / image)

## Configuration

```toml
[BilibiliAdapter.accounts.default]
login_mode = "cookie"          # cookie=manually filled credentials / qrcode=panel QR code scan (recommended)
sessdata = "YOUR_SESSDATA"     # required in cookie mode
bili_jct = "YOUR_BILI_JCT"     # required in cookie mode
buvid3 = "YOUR_BUVID3"         # optional, reduces risk control probability
dedeuserid = "YOUR_UID"        # optional, i.e., the account UID
bot_id = ""                    # leave empty, auto-fetched after login
enabled = true
```

**Configuration item description (per account):**

- `login_mode`: Login method. `cookie` for manually filled credentials; `qrcode` for panel QR code scanning (recommended). Credentials in both modes ultimately end up in fields such as sessdata/bili_jct
- `sessdata` / `bili_jct`: Login state Cookies (required in cookie mode; displayed in password form in the panel)
- `buvid3`: Device fingerprint Cookie (optional); including it significantly reduces the probability of triggering risk control
- `dedeuserid`: Account UID (optional), also serves as the default source for `bot_id`
- `bot_id`: Account UID; if left empty, it is automatically fetched via `get_self_info` after login

**QR code login flow**: After saving with `login_mode = "qrcode"`, select "Scan QR Code to Log in to Bilibili" in Dashboard → Component Configuration → Add Account Wizard → Scan the QR code with the Bilibili APP → Confirm on phone → The adapter polls the login status (scan → confirm → done), and the credentials are automatically written into the account configuration and take effect.

> The adapter also registers the `POST /bilibili/qr/start` (fetch QR code, returns image URL + session token) and `POST /bilibili/qr/poll` (poll login status) endpoints, which third-party frontends can also integrate with directly. Polling requests must carry the `poll_token` returned by start to prevent unauthorized polling.

## Message Sending

All send methods return a Task; after awaiting, you get the standard response (see "Return Value Format").

### Basic Sending

```python
from ErisPulse import sdk
bili = sdk.adapter.get("bilibili")

# Text private message (target is the other party's UID)
await bili.Send.To("user", "123456789").Text("Hello Bilibili!")

# Image private message (URL or local path, converted to a Bilibili private message image)
await bili.Send.To("user", "123456789").Image("https://example.com/pic.jpg")
await bili.Send.To("user", "123456789").Image("./local.png")
```

### Chain Modifier Methods

```python
# Reply to a specific message (msg_key comes from the message_id of the received message)
await bili.Send.To("user", "123456789").Reply("msg_key").Text("Received!")
```

### OneBot12 Standard Segment Sending

```python
message = [
    {"type": "text", "data": {"text": "First line"}},
    {"type": "image", "data": {"file": "https://example.com/img.jpg"}},
]
await bili.Send.To("user", "123456789").Raw_ob12(message)
```

### Multi-Account Sending

```python
await bili.Send.Using("account2").To("user", "123456789").Text("From the second account")
```

### Supported and Unsupported Message Segments

| Segment | Support | Description |
|---------|---------|-------------|
| `text` | Supported | Concatenated and sent via `send_msg` (TEXT) |
| `image` | Supported | `file` is a URL / local path, sent via `send_msg` (PICTURE) |
| `reply` | Partially supported | Accepted by modifiers; Bilibili private messages have no quote display, used only as send context |
| `mention` / `face` / `voice` / `video` / `file` etc. | Not supported | Returns `retcode=10002` and lists the received segment types |

## Standard API Actions (Api)

```python
from ErisPulse import sdk
bili = sdk.adapter.get("bilibili")

# Self info (nickname/avatar/UID)
result = await bili.Api.get_self_info()

# User public info (any user, nickname/avatar)
result = await bili.Api.get_user_info("123456789")

# Fetch history messages of a specified session (begin_seqno used for pagination)
result = await bili.Api.get_session_msgs("123456789", begin_seqno=0)

# Status and version
result = await bili.Api.get_status()
result = await bili.Api.get_version()

# Multi-account
result = await bili.Api.Using("account2").get_self_info()
```

### Supported Standard Actions

| Method | Description | Data Source |
|--------|-------------|-------------|
| `get_self_info()` | Self info (mid/name/face) | Web API (space info) |
| `get_user_info(user_id)` | User public info (nickname/avatar) | Web API (user info card) |
| `get_session_msgs(talker_id, begin_seqno)` | Session history messages | Web private message API (session_msgs) |
| `get_status()` | Adapter running status | Local |
| `get_version()` | Adapter version | Local |

### Unsupported Standard Actions

The following standard actions have no corresponding capability in Bilibili private messages; calls return `retcode=10002`:

- `get_friend_list` / `get_group_list` / `get_group_member_info`
- `delete_message` (in Bilibili private messages, only the sender can recall their own messages)
- Group management actions such as `set_group_name` / `leave_group`

### Generic Action Entry

```python
# send_message: combined sending of text and image segments (equivalent to the Send chain)
result = await bili.call_api(
    "send_message",
    _account_id="default",
    target_id="123456789",
    message=[{"type": "text", "data": {"text": "hi"}}],
)
```

## Return Value Format

All send and API methods follow the ErisPulse adapter standardized return specification:

```python
{
    "status": "ok",              # ok / failed
    "retcode": 0,                # 0 success; 10002 unsupported; 10003 parameter/target error; 33100 Bilibili API error
    "data": {...},               # Response data (raw return of send_msg)
    "self": {"platform": "bilibili", "user_id": "..."},
    "message_id": "123456",      # Bilibili msg_key
    "message": "",               # Error message
    "bilibili_raw": {...}        # Raw response
}
```

## Event Types

You need to check `platform == "bilibili"` before using platform-specific features.

### Event Mapping

| Bilibili Private Message Event | Adapter Event | Description |
|--------------------------------|---------------|-------------|
| TEXT (text message) | message (text segment) | Regular private chat text |
| PICTURE (image message) | message (image segment) | content.pictures → image segment (URL) |
| WITHDRAW (recall) | Log only | The other party recalled a message |

### Event Field Example

```python
{
  "id": "uuid",
  "time": 1793277000,
  "type": "message",
  "detail_type": "private",
  "platform": "bilibili",
  "self": {"platform": "bilibili", "user_id": "10000", "user_name": "Bot nickname", "account_id": "default"},
  "user_id": "123456789",                  # The other party's UID (sender_uid)
  "user_nickname": "Xiao Wang",            # content.sender_name (may be missing)
  "message": [{"type": "text", "data": {"text": "Hello"}}],
  "alt_message": "Hello",
  "bilibili_raw": {...},                   # Bilibili raw private message data
  "bilibili_raw_type": "text"              # text / picture
}
```

### Extended Field Description

- All platform-specific fields are identified with the `bilibili_` prefix (`bilibili_raw` / `bilibili_raw_type`)
- Received images are image segments, and `data.file` is a Bilibili image hosting URL
- `user_nickname` comes from the `sender_name` in the message content, which may be missing for some message types

## Important Notes

1. **Bilibili has no official personal Bot API**: This adapter uses the Web private message API via simulated login, which is unofficial usage; the API may change with Bilibili updates
2. **Risk control**: High-frequency/bulk private messages can easily trigger risk control (the account's private message function may be temporarily banned). Be sure to implement throttling on the module side; including `buvid3` can reduce the probability
3. **Login state expiration**: After the Cookie expires, the adapter will log error messages; please re-scan the QR code or update the Cookie; credentials are displayed in password form in the panel
4. Single chat limitation: Only one-on-one private messages are supported; fan group chats are not yet supported
5. Compliance: Do not use for harassment, marketing mass-sending, or other prohibited purposes; comply with Bilibili community rules