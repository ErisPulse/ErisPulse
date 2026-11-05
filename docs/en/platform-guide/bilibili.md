# Bilibili Platform Features Documentation

BilibiliAdapter is a Bilibili direct message (DM) adapter based on bilibili-api-python, supporting dual login via Cookie / QR code and event-driven DM sending and receiving.

---

## Document Information

- Corresponding module version: 0.1.0
- Maintainer: ErisPulse

## Basic Information

- Platform overview: Bilibili DM bot (no official personal Bot API; uses the Web DM API via simulated login)
- Adapter name: BilibiliAdapter
- Multi-account support: Supported (one Bilibili account per adapter account, with independent session listening)
- Connection method: Event-driven session listening (bilibili-api `Session`)
- Authentication method: Cookie (SESSDATA / bili_jct / buvid3 / dedeuserid) or QR code login via the panel
- Chain modifier support: Supports chained modifier methods such as `.Reply()`
- OneBot12 compatibility: Supports standard message segments (text / image)

## Configuration

```toml
[BilibiliAdapter.accounts.default]
login_mode = "cookie"          # cookie = manually filled credentials / qrcode = panel QR scan (recommended)
sessdata = "YOUR_SESSDATA"     # required in cookie mode
bili_jct = "YOUR_BILI_JCT"     # required in cookie mode
buvid3 = "YOUR_BUVID3"         # optional, reduces the probability of triggering risk control
dedeuserid = "YOUR_UID"        # optional, i.e. the account UID
bot_id = ""                    # leave empty; auto-fetched after login
enabled = true
```

**Configuration items (per account):**

- `login_mode`: Login method. `cookie` for manually filled credentials; `qrcode` for panel QR scan (recommended). In both modes, the credentials ultimately end up in fields such as sessdata/bili_jct
- `sessdata` / `bili_jct`: Login-state Cookies (required in cookie mode; displayed as password fields in the panel)
- `buvid3`: Device fingerprint Cookie (optional); including it significantly reduces the probability of triggering risk control
- `dedeuserid`: Account UID (optional), which also serves as the default source for `bot_id`
- `bot_id`: Account UID; if left empty, it is automatically fetched via `get_self_info` after login

**QR code login flow**: After saving `login_mode = "qrcode"`, go to Dashboard → Component Configuration → Add Account Wizard and select "Scan QR Code to Log in to Bilibili" → scan the QR code with the Bilibili app → confirm on your phone → the adapter polls the login status (scan → confirm → done), and the credentials are automatically written into the account configuration and take effect.

> The adapter also registers the `POST /bilibili/qr/start` (fetch the QR code; returns an image URL + session token) and `POST /bilibili/qr/poll` (poll the login status) endpoints, which third-party frontends can also integrate with directly. Polling requests must carry the `poll_token` returned by start to prevent unauthorized polling.

## Message Sending

All sending methods return a Task; await it to obtain the standard response (see "Return Value Format").

### Basic Sending

```python
from ErisPulse import sdk
bili = sdk.adapter.get("bilibili")

# Text DM (target is the other party's UID)
await bili.Send.To("user", "123456789").Text("Hello Bilibili!")

# Image DM (URL or local path, converted to a Bilibili DM image)
await bili.Send.To("user", "123456789").Image("https://example.com/pic.jpg")
await bili.Send.To("user", "123456789").Image("./local.png")
```

### Chain Modifier Methods

```python
# Reply to a specified message (msg_key comes from the message_id of the received message)
await bili.Send.To("user", "123456789").Reply("msg_key").Text("Got it!")
```

### OneBot12 Standard Segment Sending

```python
message = [
    {"type": "text", "data": {"text": "First line"}},
    {"type": "image", "data": {"file": "https://example.com/img.jpg"}},
]
await bili.Send.To("user", "123456789").Raw_ob12(message)
```

### Multi-account Sending

```python
await bili.Send.Using("account2").To("user", "123456789").Text("From the second account")
```

### Supported and Unsupported Message Segments

| Segment | Supported | Description |
|----|------|------|
| `text` | Yes | Concatenated and sent via `send_msg` (TEXT) |
| `image` | Yes | `file` is a URL / local path, sent via `send_msg` (PICTURE) |
| `reply` | Partially | Accepted by the modifier; Bilibili DMs have no quote display, it is only used as sending context |
| `mention` / `face` / `voice` / `video` / `file`, etc. | No | Returns `retcode=10002` and lists the received segment types |

## Standard API Actions (Api)

```python
from ErisPulse import sdk
bili = sdk.adapter.get("bilibili")

# Self info (nickname/avatar/UID)
result = await bili.Api.get_self_info()

# User public info (any user, nickname/avatar)
result = await bili.Api.get_user_info("123456789")

# Fetch history messages of a specified session (begin_seqno is used for pagination)
result = await bili.Api.get_session_msgs("123456789", begin_seqno=0)

# Status and version
result = await bili.Api.get_status()
result = await bili.Api.get_version()

# Multi-account
result = await bili.Api.Using("account2").get_self_info()
```

### Supported Standard Actions

| Method | Description | Data Source |
|------|------|---------|
| `get_self_info()` | Self info (mid/name/face) | Web API (space info) |
| `get_user_info(user_id)` | User public info (nickname/avatar) | Web API (user info card) |
| `get_session_msgs(talker_id, begin_seqno)` | Session history messages | Web DM API (session_msgs) |
| `get_status()` | Adapter running status | Local |
| `get_version()` | Adapter version | Local |

### Unsupported Standard Actions

The following standard actions have no corresponding capability in Bilibili DMs; calling them returns `retcode=10002`:

- `get_friend_list` / `get_group_list` / `get_group_member_info`
- `delete_message` (in Bilibili DMs, only the other party can withdraw their own messages)
- `set_group_name` / `leave_group` and other group management actions

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

All sending and API methods follow the ErisPulse adapter standardized return specification:

```python
{
    "status": "ok",              # ok / failed
    "retcode": 0,                # 0 success; 10002 unsupported; 10003 parameter/target error; 34000 Bilibili API error
    "data": {...},               # Response data (raw send_msg return)
    "self": {"platform": "bilibili", "user_id": "..."},
    "message_id": "123456",      # Bilibili msg_key
    "message": "",               # Error message
    "bilibili_raw": {...}        # Raw response
}
```

## Event Types

Check for `platform == "bilibili"` before using this platform's features.

### Event Mapping

| Bilibili DM Event | Adapter Event | Description |
|--------------|--------------|------|
| TEXT (text message) | message (text segment) | Regular private chat text |
| PICTURE (image message) | message (image segment) | content.pictures → image segment (URL) |
| WITHDRAW (withdrawal) | Logged only | The other party withdrew a message |

### Event Field Example

```python
{
  "id": "uuid",
  "time": 1793277000,
  "type": "message",
  "detail_type": "private",
  "platform": "bilibili",
  "self": {"platform": "bilibili", "user_id": "10000", "user_name": "Bot Nickname", "account_id": "default"},
  "user_id": "123456789",                  # Other party's UID (sender_uid)
  "user_nickname": "Xiao Wang",            # content.sender_name (may be missing)
  "message": [{"type": "text", "data": {"text": "Hello"}}],
  "alt_message": "Hello",
  "bilibili_raw": {...},                   # Raw Bilibili DM data
  "bilibili_raw_type": "text"              # text / picture
}
```

### Extended Field Description

- All platform-specific fields are identified with the `bilibili_` prefix (`bilibili_raw` / `bilibili_raw_type`)
- Received images arrive as image segments; `data.file` is a Bilibili image hosting URL
- `user_nickname` comes from the message content's `sender_name`, which may be missing for some message types

## Notes

1. **Bilibili has no official personal Bot API**: This adapter uses the Web DM API via simulated login, which is unofficial usage; the API may change with Bilibili updates
2. **Risk control**: High-frequency/bulk DMs easily trigger risk control (the account's DM function may be temporarily muted). Be sure to implement throttling on the module side; including `buvid3` can reduce the probability
3. **Login state expiration**: After the Cookies expire, the adapter logs an error; please scan the QR code again or update the Cookies. Credentials are displayed as password fields in the panel
4. One-on-one chat limitation: Only one-on-one DMs are supported; fan group chats are not yet supported
5. Compliance: Do not use for violations such as harassment or marketing mass-mailing; comply with Bilibili community rules