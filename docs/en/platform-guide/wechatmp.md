# WeChat MP Adapter - Platform Features Documentation

## Basic Information
- Module Name: `ErisPulse-WechatMpAdapter`
- Platform Identifier: `mp` (Alias: `wechat_mp`)
- Module Version: 4.3.2
- Maintainer: ErisPulse
- Last Updated: 2026-11-10
- Dependencies: `cryptography`

## v5 Paradigm Update (4.2.0)

- **BaseConverter Inheritance**: Common fields of converters are built by the framework's build_base_event
- **Minimal Set of Api DSL**: get_self_info (appid) / get_status / get_version / get_supported_actions
- **Framework Soft Dependency**: Runtime detection of ErisPulse>=2.7.1 with prompt; version logs output on startup

## Standardized Alignment (4.3.2)

The response structure and error codes follow the [API Response Specification](../standards/api-response.md).

### Message Event Completion: message_id

The top-level message event is supplemented with the standard `message_id` field (using WeChat's MsgId; if missing, an empty string is used as a fallback). Modules no longer need to read from `mp_msg_id`.

### Standard Response

All `call_api` / Send calls return a standard response: `status` / `retcode` / `data` / `message_id` / `message` + top-level `mp_raw`. **When passive replies are successful, `message` is an empty string** (`data.passive_reply=true` indicates interception as a passive reply).

### Error Code Specification

| retcode | Meaning | Description |
|---------|---------|-------------|
| 0 | Success | — |
| 34100 | Platform Failure | WeChat API returned errcode != 0; **the original errcode is preserved in `mp_raw`**. Token acquisition failure is also categorized under this code |
| 10003 | Parameter Error / Not Authenticated | Unauthenticated accounts (`verified=false`) calling customer service messages in non-passive reply contexts |

### Accounts and Multi-Account Support

- `call_api` supports dual-compatible account fields: `account_id` (standard name) / `_account_id` (old name), with the framework ApiDSL (`Api.Using(...)`) automatically adapting
- `Send` reads from `send_context` (event account as fallback)
- `get_self_info` supplements standard fields: `user_id` (official account AppID) / `user_name` / `user_displayname` (`wechatmp:{account name}`)

---

### Platform Capabilities Already Integrated

- **Receiving**: Official account callback messages and events such as follow/unfollow (plaintext/safe mode), signature verification
- **Sending**: Customer service messages (Text/Image, etc., via Send DSL)
- **API**: Account information (appid) and operational status (minimal set)

## Supported Message Sending Types

| Method | Description | WeChat API |
|--------|-------------|------------|
| `Text(text)` | Send text message | Customer Service Message `message/custom/send` |
| `Image(file)` | Send image (automatically uploads and retrieves media_id) | Customer Service Message + `media/upload` |
| `Voice(file)` | Send voice (automatically uploads and retrieves media_id) | Customer Service Message + `media/upload` |
| `Video(file, title, description)` | Send video (automatically uploads and retrieves media_id) | Customer Service Message + `media/upload` |
| `Music(url, title, description, ...)` | Send music | Customer Service Message |
| `News(articles)` | Send news message | Customer Service Message |
| `Template(template_id, data, url)` | Send template message | `message/template/send` |
| `Menu(head_content, list, tail_content)` | Send menu message | Customer Service Message `msgmenu` |
| `Raw_ob12(message)` | Send OneBot12 standard message segment | - |

### Media File Notes
- Three parameter types are supported:
  - `str` URL (starting with `http://` or `https://`): automatically downloads and uploads
  - `str` local file path: automatically reads and uploads
  - `bytes` binary data: uploads directly
  - `str` media_id: prefixed with `media:` to reuse an already uploaded media_id
- After upload, a temporary material `media_id` is obtained, valid for 3 days

### Important Restrictions
- Customer service messages can only be sent **within 48 hours** after user interaction with the official account
- After 48 hours, template messages must be used (requires user-authorized scenarios)
- Unverified service accounts (`verified=false`) cannot send messages proactively, only respond passively (see "Verified Service Account and Passive Reply" above)

## Event Types

### Message Events (message)
All user messages have `detail_type: private` (1v1 scenario for official accounts).

| WeChat MsgType | Message Segment Type | Description |
|----------------|----------------------|-------------|
| `text` | `text` | Text message |
| `image` | `image` | Image message |
| `voice` | `voice` | Voice message (includes voice recognition result) |
| `video` | `video` | Video message |
| `shortvideo` | `video` | Short video (marked with `mp_shortvideo`) |
| `location` | `location` | Location message |
| `link` | `text` | Link message (converted to text) |

### Notification Events (notice)
Events are distinguished by the `mp_event` field.

| WeChat Event | `mp_event` | Description |
|--------------|------------|-------------|
| `subscribe` | `subscribe` | Subscribe to official account |
| `unsubscribe` | `unsubscribe` | Unsubscribe from official account |
| `SCAN` | `scan` | Scan a QR code with parameters |
| `LOCATION` | `location_report` | Report location |
| `CLICK` | `menu_click` | Click on a custom menu |
| `VIEW` | `menu_view` | Navigate to a menu link |
| `TEMPLATESENDJOBFINISH` | `template_send_finish` | Template message send result |
| `MASSSENDJOBFINISH` | `mass_send_finish` | Mass message send result |

## Platform Extension Fields

WeChat-specific fields (with `mp_` prefix) in the event object:

| Field | Type | Description |
|------|------|------|
| `mp_raw` | str | Raw XML data |
| `mp_raw_type` | str | Original message/event type |
| `mp_msg_id` | str | WeChat message ID |
| `mp_event` | str | Event type (only for event notifications) |
| `mp_event_key` | str | Event Key (menu click/scan, etc.) |
| `mp_to_user` | str | Receiver's WeChat ID (official account original ID) |
| `mp_from_user` | str | Sender's OpenID |
| `mp_data` | dict | Parsed XML dictionary data |

## Event Extension Methods

Registered via `register_event_mixin("mp", ...)`, allowing direct calls on event objects:

| Method | Return Value | Description |
|--------|--------------|-------------|
| `get_openid()` | str | Sender's OpenID |
| `get_msg_type()` | str | Original WeChat message type |
| `get_event()` | str | Event type (only for event notifications) |
| `get_content()` | str | Pure text content of the message |
| `get_raw_xml()` | str | Raw XML data |

## Configuration Options

### Multi-Account Configuration

Each account corresponds to a WeChat Official Account:

```toml
[WechatMpAdapter.accounts.main]
appid = "wx1234567890abcdef"
appsecret = "your_app_secret_here"
token = "your_callback_token"
encoding_aes_key = ""                    # Required for secure or compatibility mode (43 characters)
callback_path = "/mp/main"               # Callback path
verified = true                          # Whether it is a verified service account (affects active sending capability)
enable = true

[WechatMpAdapter.accounts.secondary]
appid = "wx0987654321fedcba"
appsecret = "another_app_secret"
token = "another_callback_token"
callback_path = "/mp/secondary"
enable = true
```

### Configuration Field Descriptions

| Field | Required | Description |
|-------|----------|-------------|
| `appid` | Yes | Official Account AppID |
| `appsecret` | Yes | Official Account AppSecret (secret) |
| `token` | No | Callback verification token (recommended to enable signature verification) |
| `encoding_aes_key` | No | Message encryption/decryption key (43 characters, required for secure mode) |
| `callback_path` | No | Callback path template, default `/mp/{account}`, where `{account}` is replaced by the account name |
| `verified` | No | Whether it is a **verified service account**, default `true` (see below for details) |
| `enable` | No | Whether to enable, default true |

### Verified Service Account and Passive Replies (`verified`)

- `verified = true` (default, verified service account): Can use **customer service messages** to push actively (within a 48-hour window) and template messages at any time.
- `verified = false` (unverified subscription account):
  - Customer service messages / template messages **can only be sent within the webhook passive reply context** (within 15 seconds after receiving a user message, one reply only) — the adapter will automatically intercept and convert the send operation into a passive reply.
  - Active push (e.g., scheduled tasks) returns `retcode=10003` error (not verified).

## Encryption Mode Explanation

WeChat Official Accounts provide three message encryption and decryption modes:

| Mode | Description | encoding_aes_key | Verification Field |
|------|-------------|------------------|--------------------|
| Plaintext Mode | XML transmitted in plaintext | Not required | `signature` |
| Compatible Mode | Both plaintext and encrypted messages exist | Optional | `signature` / `msg_signature` |
| Secure Mode | Entire message encrypted | Required | `msg_signature` |

This adapter automatically handles:
- Plaintext Mode: Validates `signature` and directly parses XML
- Secure/Compatible Mode: Detects the `Encrypt` field, validates `msg_signature`, and uses AES-256-CBC decryption
- Decryption depends on the `cryptography` library (declared in dependencies)

## Callback Routes

The adapter registers two routes (GET + POST) for each enabled account:

- **GET**: WeChat server access verification. After verifying the signature, it returns the `echostr`.
- **POST**: Receives user messages and events. Verifies the signature → decrypts (if required) → converts → emits.

The actual access paths automatically include the module prefix. For example, if the registered path is `/mp/main`, the actual access paths will be `/mp_{account}_verify/mp/main` and `/mp_{account}_message/mp/main`.

## API Response

All `call_api` calls return a standardized response:

- Success: `status: "ok"`, `retcode: 0`
- Failure: `status: "failed"`, `retcode: 34100` (platform failure; **original errcode is preserved in `mp_raw`**) or `10003` (parameter error / not authenticated)
- Always includes `mp_raw` (raw response) and top-level `message_id` (empty string if missing)