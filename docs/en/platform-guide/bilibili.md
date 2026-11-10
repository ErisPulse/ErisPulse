# Bilibili Platform Features Documentation

BilibiliAdapter is a Bilibili direct message adapter based on bilibili-api-python, supporting Cookie / QR code dual login and event-driven private message sending and receiving.

---

## Document Information

- Corresponding module version: 0.3.1
- Maintainer: ErisPulse
- Last updated: 2026-11-10

## Basic Information

- Platform overview: Bilibili direct message bot (no official personal Bot API; uses the Web private message API via simulated login)
- Adapter name: BilibiliAdapter
- Multi-account support: Supported (one Bilibili account per adapter account, with independent session listening)
- Connection method: Event-driven session listening (bilibili-api `Session`)
- Authentication: Cookie (SESSDATA / bili_jct / buvid3 / dedeuserid) or panel QR code login
- Chained modifier support: Supports chained modifier methods such as `.Reply()`
- OneBot12 compatibility: Supports standard message segments (text / image)

## Configuration

```toml
[BilibiliAdapter.accounts.default]
login_mode = "cookie"          # cookie=manually filled credentials / qrcode=panel QR code scan (recommended)
sessdata = "YOUR_SESSDATA"     # required in cookie mode
bili_jct = "YOUR_BILI_JCT"     # required in cookie mode
buvid3 = "YOUR_BUVID3"         # optional, reduces risk-control probability
dedeuserid = "YOUR_UID"        # optional, i.e., the account UID
bot_id = ""                    # leave empty to auto-fetch after login
enabled = true
```

**Configuration item descriptions (per account):**

- `login_mode`: Login method. `cookie` for manually filled credentials; `qrcode` for panel QR code scan (recommended). Credentials for both modes are ultimately stored in fields such as sessdata/bili_jct
- `sessdata` / `bili_jct`: Login-state Cookies (required in cookie mode; displayed in password form in the panel)
- `buvid3`: Device fingerprint Cookie (optional); carrying it significantly reduces the probability of risk control
- `dedeuserid`: Account UID (optional); also serves as the default source for `bot_id`
- `bot_id`: Account UID; if left empty, it is automatically fetched via `get_self_info` after login

**QR code login flow**: After saving with `login_mode = "qrcode"`, select "Scan QR Code to Log in to Bilibili" in Dashboard → Component Configuration → Add Account Wizard → scan the QR code with the Bilibili APP → confirm on the phone → the adapter polls the login status (scan → confirm → done), and the credentials are automatically written into that account's configuration and take effect.

> The adapter also registers the `POST /bilibili/qr/start` (get QR code, returns image URL + session token) and `POST /bilibili/qr/poll` (poll login status) endpoints, which third-party frontends can also integrate with directly. Polling requests must carry the `poll_token` returned by start to prevent unauthorized polling.

## Standardization Alignment

This section describes how the adapter aligns with the ErisPulse standardization specifications. For specification details, see the SDK documentation "API Response Specification" (`docs/en/standards/api-response.md`).

### Api.Using() Account Routing Fix (0.3.1)

Previously, the `Api` DSL methods did not correctly consume the account specified by `Using()`; this has now been fixed: the `_account_id` passed explicitly via `Using()` and the `api_context` from the event chain (the account where the event originated) are both correctly routed to the corresponding account's runtime, falling back to the first account on failure.

### Message Events Add Top-Level message_id

Message events now include a top-level `message_id` field (taken from `msg_key`), consistent with the standard response structure, and can be used directly with the `Reply()` chained modifier.

### Error Code Normalization (0.3.1)

bilibili_api exceptions are categorized by class: network-type exceptions (`NetworkException`, etc.) return `33001`, platform API errors return `34100` (the original 34000/10004 are no longer used), and the raw response is retained in `bilibili_raw`.

| retcode | Description |
|---------|------|
| 0 | Success |
| 10002 | Unsupported action/message segment |
| 10003 | Parameter/target error |
| 33001 | Network error (connection exception, timeout) |
| 34100 | Bilibili API error (raw response retained in `bilibili_raw`) |

### Meta-Action Standardization

- The `data` of `get_self_info` / `get_user_info` contains standard fields: `user_id` / `user_name` / `user_displayname` / `user_remark` (Bilibili has no remark concept, so `user_remark` is always empty) and `avatar`
- `get_version` returns `{"impl": "ErisPulse-BilibiliAdapter", "version": "...", "onebot_version": "12"}`
- `get_supported_actions` returns a list of supported action names

### Others

- `call_api` accepts both the standard field `account_id` and the legacy field name `_account_id` (standard name takes precedence); the framework's ApiDSL adapts automatically
- Converter inherits the framework's `BaseConverter`; common fields (id/time/platform/self/raw) are built uniformly by the framework

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

### Chained Modifier Methods

```python
# Reply to a specific message (msg_key comes from the message_id of the received message)
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

### Multi-Account Sending

```python
await bili.Send.Using("account2").To("user", "123456789").Text("Message from the second account")
```

### Supported and Unsupported Message Segments

| Segment | Supported | Description |
|----|------|------|
| `text` | Supported | Concatenated and sent via `send_msg` (TEXT) |
| `image` | Supported | `file` is a URL / local path, sent via `send_msg` (PICTURE) |
| `reply` | Partially supported | Accepted by the modifier; Bilibili private messages have no quote display, used only as send context |
| `mention` / `face` / `voice` / `video` / `file`, etc. | Unsupported | Returns `retcode=10002` and lists the received segment types |

## Standard API Actions (Api)

```python
from ErisPulse import sdk
bili = sdk.adapter.get("bilibili")

# Self information (nickname/avatar/UID)
result = await bili.Api.get_self_info()

# User public information (any user, nickname/avatar)
result = await bili.Api.get_user_info("123456789")

# Fetch historical messages of a specified session (begin_seqno is used for pagination)
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
| `get_self_info()` | Self information (mid/name/face) | Web API (space info) |
| `get_user_info(user_id)` | User public information (nickname/avatar) | Web API (user info card) |
| `get_session_msgs(talker_id, begin_seqno)` | Session history messages | Web private message API (session_msgs) |
| `get_status()` | Adapter running status | Local |
| `get_version()` | Adapter version (impl/version/onebot_version) | Local |
| `get_supported_actions()` | List of supported action names | Local |

### Unsupported Standard Actions

The following standard actions have no corresponding capability in Bilibili private messages; calling them returns `retcode=10002`:

- `get_friend_list` / `get_group_list` / `get_group_member_info`
- `delete_message` (in Bilibili private messages, only the other party can recall their own messages)
- Group management actions such as `set_group_name` / `leave_group`

### Generic Action Entry

```python
# send_message: combined sending of text and image segments (equivalent to the Send chain)
result = await bili.call_api(
    "send_message",
    account_id="default",
    target_id="123456789",
    message=[{"type": "text", "data": {"text": "hi"}}],
)
```

### Content Browsing Extension Actions (for ecosystem modules)

Content browsing extensions are provided via `Api.call()` / `call_api()` (for use by ecosystem modules such as `call_adapter_api`):

```python
result = await bili.Api.call("get_user_dynamics", uid="123456789")   # User dynamics (simplified entries)
result = await bili.Api.call("search_video", keyword="keyword", page=1)  # Video search
result = await bili.Api.call("get_popular")                          # Popular content
```

## Return Value Format

All send and API methods follow the ErisPulse adapter standardization return specification:

```python
{
    "status": "ok",              # ok / failed
    "retcode": 0,                # 0 success; 10002 unsupported; 10003 parameter/target error; 33001 network error; 34100 Bilibili API error
    "data": {...},               # Response data (raw send_msg return)
    "self": {"platform": "bilibili", "user_id": "..."},
    "message_id": "123456",      # Bilibili msg_key
    "message": "",               # Error message
    "bilibili_raw": {...}        # Raw response
}
```

## Event Types

Check `platform == "bilibili"` before using the platform-specific features described in this section.

### Event Mapping

| Bilibili Private Message Event | Adapter Event | Description |
|--------------|--------------|------|
| TEXT (text message) | message (text segment) | Regular private chat text |
| PICTURE (image message) | message (image segment) | content.pictures → image segment (URL) |
| WITHDRAW (recall) | Log only | The other party recalls a message |

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
  "user_nickname": "Xiao Wang",                  # content.sender_name (may be missing)
  "message": [{"type": "text", "data": {"text": "Hello"}}],
  "alt_message": "Hello",
  "bilibili_raw": {...},                   # Raw Bilibili private message data
  "bilibili_raw_type": "text"              # text / picture
}
```

### Extension Field Descriptions

- All platform-specific fields are identified by the `bilibili_` prefix (`bilibili_raw` / `bilibili_raw_type`)
- Received images are image segments, with `data.file` being a Bilibili image hosting URL
- `user_nickname` comes from the message content's `sender_name` and may be missing for some message types

## Notes

1. **No official personal Bot API**: This adapter uses the Web private message API via simulated login, which is unofficial usage; the API may change with Bilibili updates
2. **Risk control**: High-frequency/bulk private messages can easily trigger risk control (the account's private message function is temporarily muted). Be sure to implement throttling on the module side; carrying `buvid3` can reduce the probability
3. **Login state expiration**: After Cookies expire, the adapter logs error messages; please re-scan the QR code or update the Cookies. Credentials are displayed in password form in the panel
4. One-on-one chat limitation: Only one-to-one private messages are supported; fan group chats are not yet supported
5. Compliance: Do not use for harassment, bulk marketing, or other rule-violating purposes; comply with Bilibili community rules