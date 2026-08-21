# WechatMp Adapter - Platform Features Documentation

Please directly return the complete translated Markdown content, without any additional text.

Once again, please note: if the document contains a language switch line (with language names separated by `` | ``), strictly adhere to the above format requirements in point 8, and do not write incorrect formats such as ``[**Label**](file)``.

## Basic Information
- Module Name: `ErisPulse-WechatMpAdapter`
- Platform Identifier: `mp` (alias: `wechat_mp`)
- Module Version: 4.1.0
- Maintainer: ErisPulse
- Dependencies: `cryptography`

Please directly return the complete translated Markdown content, without any additional text.

Once again, if the document contains language switching lines (with language names separated by `` | ``), strictly follow the format requirement in item 8 above, and do not write incorrect formats such as ``[**Label**](file)``.

## Supported Message Types

| Method | Description | WeChat API |
|--------|-------------|------------|
| `Text(text)` | Send text | Customer Service Message `message/custom/send` |
| `Image(file)` | Send image (automatically uploads and gets media_id) | Customer Service Message + `media/upload` |
| `Voice(file)` | Send voice (automatically uploads and gets media_id) | Customer Service Message + `media/upload` |
| `Video(file, title, description)` | Send video (automatically uploads and gets media_id) | Customer Service Message + `media/upload` |
| `Music(url, title, description, ...)` | Send music | Customer Service Message |
| `News(articles)` | Send news article message | Customer Service Message |
| `Template(template_id, data, url)` | Send template message | `message/template/send` |
| `Menu(head_content, list, tail_content)` | Send menu message | Customer Service Message `msgmenu` |
| `Raw_ob12(message)` | Send OneBot12 standard message segment | - |

### Media File Notes
- Supports three parameter types:
  - `str` URL (starts with `http://` or `https://`): automatically downloads and uploads
  - `str` local file path: automatically reads and uploads
  - `bytes` binary data: directly uploads
  - `str` media_id: with `media:` prefix, can directly reuse an already uploaded media_id
- After upload, a temporary material `media_id` is obtained, valid for 3 days

### Important Limitations
- Customer Service Messages can only be actively sent within **48 hours** after user interaction with the public account
- After 48 hours, use template messages (requires user-authorized scenarios)
- Unverified service accounts (`verified=false`) cannot send messages proactively; they can only respond passively (see "Verified Service Account and Passive Reply" above)

## Event Types

### Message Events (message)
All user messages have `detail_type: private` (WeChat Official Account 1v1 scenario).

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
| `CLICK` | `menu_click` | Click custom menu |
| `VIEW` | `menu_view` | Navigate menu link |
| `TEMPLATESENDJOBFINISH` | `template_send_finish` | Template message sending result |
| `MASSSENDJOBFINISH` | `mass_send_finish` | Mass message sending result |

## Platform Extension Fields

WeChat-specific fields (with `mp_` prefix) in the event object:

| Field | Type | Description |
|------|------|------|
| `mp_raw` | str | Original XML data |
| `mp_raw_type` | str | Original message/event type |
| `mp_msg_id` | str | WeChat message ID |
| `mp_event` | str | Event type (only for event notifications) |
| `mp_event_key` | str | Event Key (for menu clicks, scanning QR codes, etc.) |
| `mp_to_user` | str | Receiver's WeChat ID (official account original ID) |
| `mp_from_user` | str | Sender's OpenID |
| `mp_data` | dict | Parsed XML dictionary data |

Please replace all `docs/en/` paths in document links with `docs/en/`. For example, `docs/en/quick-start.md` should be changed to `docs/en/quick-start.md`. For links pointing to non-current language version files (e.g., `README.xx.md`), keep them unchanged to ensure the links point to the correct language version of the document.

## Event Extension Methods

Registered via `register_event_mixin("mp", ...)`, these methods can be directly called on event objects:

| Method | Return Value | Description |
|--------|--------------|-------------|
| `get_openid()` | str | Sender's OpenID |
| `get_msg_type()` | str | Original WeChat message type |
| `get_event()` | str | Event type (only for event notifications) |
| `get_content()` | str | Plain text content of the message |
| `get_raw_xml()` | str | Raw XML data |

Please replace paths in document links by replacing `docs/en/` with `docs/en/`. For example, `docs/en/quick-start.md` should be changed to `docs/en/quick-start.md`. For links pointing to non-current language version files (e.g., `README.xx.md`), keep them unchanged to ensure links point to the correct language version of the document.

## Configuration Options

### Multi-account Configuration

Each account corresponds to a WeChat Official Account:

```toml
[WechatMpAdapter.accounts.main]
appid = "wx1234567890abcdef"
appsecret = "your_app_secret_here"
token = "your_callback_token"
encoding_aes_key = ""                    # Required for secure/compatibility mode (43 characters)
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
| `token` | No | Callback verification Token (recommended to enable signature verification) |
| `encoding_aes_key` | No | Message encryption/decryption key (43 characters, required for secure mode) |
| `callback_path` | No | Callback path template, default `/mp/{account}`, where `{account}` will be replaced by the account name |
| `verified` | No | Whether it is a **verified service account**, default `true` (see below for details) |
| `enable` | No | Whether to enable, default true |

### Verified Service Account and Passive Response (`verified`)

- `verified = true` (default, verified service account): Can use **customer service messages** for active push (within a 48-hour window) and template messages at any time.
- `verified = false` (unverified subscription account):
  - Customer service messages / template messages **can only be sent within the webhook passive response context** (within 15 seconds after receiving a user message, one-time reply) — the adapter will automatically intercept and treat the sending as a passive response.
  - Active push (e.g., scheduled tasks) returns `retcode=34003` error.

## Encryption Mode Description

WeChat Official Accounts provide three message encryption and decryption modes:

| Mode | Description | encoding_aes_key | Validation Field |
|------|-------------|------------------|------------------|
| Plaintext Mode | XML transmitted in plaintext | Not required | `signature` |
| Compatible Mode | Both plaintext and ciphertext exist | Optional | `signature` / `msg_signature` |
| Secure Mode | Fully encrypted | Required | `msg_signature` |

This adapter automatically handles:
- Plaintext Mode: Validates `signature`, directly parses XML
- Secure/Compatible Mode: Detects the `Encrypt` field, validates `msg_signature`, and uses AES-256-CBC decryption
- Decryption depends on the `cryptography` library (declared in dependencies)

Please return the translated content directly, without any additional text.

**Important:** If the document contains language switch lines (with language names separated by `` | ``), strictly follow the format requirements above. Do not write incorrect formats such as ``[**Label**](file)``.

## Callback Routes

The adapter registers two routes (GET + POST) for each enabled account:

- **GET**: WeChat server verification, returns `echostr` after signature verification
- **POST**: Receive user messages and events, verify signature → decrypt (if needed) → transform → emit

The actual access path automatically adds the module prefix. For example, if the registered path is `/mp/main`, the actual access paths are `/mp_{account}_verify/mp/main` and `/mp_{account}_message/mp/main`.

Please directly return the complete translated Markdown content, without including any other text.

Once again, if the document contains a language switch line (with language names separated by `` | ``), strictly follow the format requirement in item 8 above, and do not write incorrect formats such as ``[**Label**](file)``.

## API Response

All `call_api` calls return a standardized response:

- Success: `status: "ok"`, `retcode: 0`
- Failure: `status: "failed"`, `retcode: 34000+errcode`
- Always includes `mp_raw` (raw response), `message_id`

Please directly return the complete translated Markdown content, without any additional text.

Once again, please note: If the document contains a language switch line (with each language name separated by `` | ``), strictly follow the format requirement in item 8 above; do not write incorrect formats such as ``[**Label**](file)``.