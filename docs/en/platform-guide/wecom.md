# Enterprise WeChat (WeCom) Platform Features Documentation

WeComAdapter is an adapter built based on the Enterprise WeChat self-built application API, which receives messages via callbacks, actively sends messages using the application message interface, and provides contact list and message card capabilities.

---

## Documentation Information

- Corresponding Module Version: 0.1.2
- Maintainer: ErisPulse
- Last Updated: 2026-11-10

## Basic Information

- Platform Overview: WeCom self-built app robot, suitable for internal enterprise notifications, intelligent Q&A, office automation, and other scenarios
- Adapter Name: WeComAdapter
- Platform Registration Name: `wecom` (alias `wxwork`)
- Multi-account Support: Supports configuring multiple enterprises simultaneously (each account corresponds to a corpid + app)
- Connection Method: HTTP callback reception (configure message receiving URL in the WeCom backend) + active API sending
- Authentication Method: corpid + secret to obtain access_token (automatic refresh)
- Callback Encryption/Decryption: Token + EncodingAESKey (official WeCom encryption/decryption protocol)
- Session Type Mapping: App message → `private` (member private message), app group chat → `group`
- Chained Modifier Support: Supports chained modifier methods such as `.Reply()`
- OneBot12 Compatibility: Supports sending OneBot12 standard message segments

## Standardized Alignment (0.1.2)

This version completes the alignment of adapter standardization, with response structure and error codes following the [API Response Specification](../standards/api-response.md).

### Accounts & Multi-Accounts

- `call_api` supports dual-compatible account fields: `account_id` (standard name) / `_account_id` (old name), the framework ApiDSL (`Api.Using(...)`) automatically adapts
- **`get_user_info` and 5 other address book API methods (`get_user_info` / `get_department_list` / `get_department_users` / `get_user_by_mobile` / `userid_to_openid` / `openid_to_userid`) have fixed the `Using()` fallback**: When the account is missing, it falls back to the account specified by `Api.Using(...)`, instead of being ignored
- `Send` reads `send_context` (event account fallback): When calling `Send` from event context, it defaults to falling back to the source account

### Standard Fields

- **Message events complete the top-level `message_id`** (obtained from WeCom MsgId, falling back to uuid if missing)
- **Standardized fields returned by query methods like `get_user_info`**: `user_id` / `user_name` / `user_displayname`, with original data preserved in `wecom_raw`
- **`get_self_info` completes `user_displayname`** (`user_id` is corpid, `user_name` / `user_displayname` is `wecom:{account name}`)
- Converter reuses framework `BaseConverter` (common field ids/time/platform/self/wecom_raw are unified by `build_base_event`)

### Error Code Specification

| retcode | Meaning | Description |
|---------|---------|-------------|
| 0 | Success | — |
| 34100 | Platform Failure | WeCom returned failure (errcode != 0); the original response is preserved in `wecom_raw` |
| 10003 | Parameter Error | Missing or invalid parameter |

## Configuration Guide

```toml
# config.toml
[WeComAdapter.accounts.default]
corpid = "YOUR_CORP_ID"        # Enterprise ID (Required, found in the Enterprise WeChat backend under "My Enterprise")
secret = "YOUR_APP_SECRET"     # Application Secret (Required, found in the self-built application details page)
agentid = 1000002              # Application AgentId (Required, found in the self-built application details page)
callback_enabled = true        # Enable callback reception (default true; if disabled, only active sending is available)
token = "YOUR_CALLBACK_TOKEN"  # Callback verification Token (configured in the Enterprise WeChat backend for receiving messages)
encoding_aes_key = "YOUR_AES_KEY_43CHARS"  # Callback encryption/decryption key (43 characters)
callback_path = "/wecom/{account}"         # Callback path, supports the {account} placeholder
enabled = true
```

**Configuration Item Explanation (per account):**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `corpid` | string | Yes | Enterprise ID |
| `secret` | string | Yes | Application Secret |
| `agentid` | int | Optional | Application AgentID |
| `callback_enabled` | bool | No | Callback reception switch (default enabled) |
| `token` | string | No | Callback verification Token |
| `encoding_aes_key` | string | No | Callback encryption/decryption key (43 characters) |
| `callback_path` | string | No | Callback path, supports `{account}` placeholder |
| `enabled` | bool | No | Whether to enable (default true) |

- `corpid` / `secret` / `agentid`: Obtained from the self-built application page in the [Enterprise WeChat management backend](https://work.weixin.qq.com) (first two are required)
- `callback_enabled`: Callback reception switch (default enabled). **If disabled, the adapter skips callback route registration and retains only active sending capability**; related callback fields in the panel will be hidden accordingly
- `token` / `encoding_aes_key`: Used for callback message validation and encryption/decryption, must match the configuration in the "Receive Messages" section of the Enterprise WeChat backend
- `callback_path`: Callback reception path (default `/wecom/{account}`), the full URL must be configured in the Enterprise WeChat backend: `http(s)://your_address:port/wecom/<account>`

**Prerequisites for Receiving Messages**: In the Enterprise WeChat backend → Self-built application → "Receive Messages" setting, enable API message reception, and fill in the above complete callback address. The Token and EncodingAESKey must match the configuration. **Note**: Enterprise WeChat requires the callback URL to be publicly accessible (it is recommended to use reverse proxy).

**API Environment**:
- API base address: `https://qyapi.weixin.qq.com/cgi-bin`
- `access_token` is automatically obtained and cached with refresh, no manual management required

## Supported Message Types

All send methods are implemented using a fluent interface, for example:

```python
from ErisPulse import sdk
wecom = sdk.adapter.get("wecom")

# Basic messages (target_type: "user"=user "group"=group chat)
await wecom.Send.To("user", "zhangsan").Text("Hello")
await wecom.Send.To("group", "group_chat_id").Markdown("**Bold** notification")

# Media (local path / bytes / URL; automatically uploads temporary material before sending)
await wecom.Send.To("user", "zhangsan").Image("banner.png")
await wecom.Send.To("user", "zhangsan").Voice("voice.amr")
await wecom.Send.To("user", "zhangsan").Video("demo.mp4")
await wecom.Send.To("user", "zhangsan").File("report.pdf")

# News and cards
await wecom.Send.To("user", "zhangsan").News([
    {"title": "Title", "description": "Summary", "url": "https://...", "picurl": "https://.../img.png"},
])  # Up to 8 items

await wecom.Send.To("user", "zhangsan").TextCard(
    title="Approval Reminder",
    description="You have a document pending approval",
    url="https://oa.example.com/approval/1",
    btntxt="Go Process",
)

await wecom.Send.To("user", "zhangsan").TemplateCard(
    card_type="text_notice",  # WeCom card type, other parameters passed as official card JSON
    source={"icon_url": "...", "desc": "OA"},
    main_title={"title": "Meeting Reminder"},
)

# Passive reply: event.reply() directly replies to the source user when receiving a message

# Specify account for multi-account sending
await wecom.Send.To("user", "UserID", account_id="app2").Text("Sent via app2")
```

### Basic Send Methods

| Method | Description | Parameters |
|--------|-------------|------------|
| `.Text(text)` | Send plain text message | `text: str` |
| `.Markdown(content)` | Send Markdown message (supported for app messages) | `content: str` |

### Media Send Methods

Media methods support both `bytes` (automatically uploads to get media_id) and `str` (already uploaded media_id or path/URL):

| Method | Description |
|--------|-------------|
| `.Image(file, filename)` | Send image |
| `.Voice(file, filename)` | Send voice (AMR format required, WeCom limitation) |
| `.Audio(file, filename)` | Alias for Voice |
| `.Video(file, filename)` | Send video |
| `.File(file, filename)` | Send file |

### Rich Text Card Methods

| Method | Description |
|--------|-------------|
| `.News(articles)` | Send news message (up to 8 items) |
| `.TextCard(title, description, url, btntxt)` | Send text card |
| `.TextCardMiniProgram(**kwargs)` | Send mini program notification card |
| `.TemplateCard(card_type, **kwargs)` | Send template card |

### Raw Message Sending

- `.Raw_ob12(message: List[Dict])`: Send OneBot12 standard format message

### Fluent Modifier Methods

| Method | Description |
|--------|-------------|
| `.At(user_id)` | @ specified user (implemented by framework SendDSL base class) |
| `.AtAll()` | @ all members (implemented by framework SendDSL base class) |
| `.Reply(message_id)` | Reply to specified message (implemented by framework SendDSL base class) |

### Send Target Mapping

| OB12 target_type | WeCom target field | API Interface |
|------------------|--------------------|---------------|
| `user` / `private` | `touser` | `message/send` |
| `group` | `chatid` | `appchat/send` |

## Standard API Actions

```python
info = await wecom.Api.get_self_info()          # Application information (corpid/agentid)
status = await wecom.Api.get_status()           # Running status
ver = await wecom.Api.get_version()             # Adapter version

# Address Book (access_token automatically injected; Using() fallback effective from 0.1.2 onwards)
user = await wecom.Api.get_user_info("zhangsan")            # Member details (name/department/position/avatar)
depts = await wecom.Api.get_department_list(0)              # Department list (0=root department)
members = await wecom.Api.get_department_users(2)           # Department member list
uid = await wecom.Api.get_user_by_mobile("13800000000")     # Find userid by mobile number
openid = await wecom.Api.userid_to_openid("zhangsan")       # userid → openid (red packet/external payment)
userid = await wecom.Api.openid_to_userid("oXXXX")          # openid → userid

# Multiple accounts: specify enterprise account
result = await wecom.Api.Using("corp2").get_user_info("lisi")

# Direct call to any WeCom API (endpoint relative to cgi-bin, access_token automatically included)
result = await wecom.Api.call("message/send", touser="zhangsan", msgtype="text", agentid=1000002, text={"content": "hi"})
```

## Platform-specific Event Types

Use `platform == "wecom"` to check for platform-specific features. WeCom event conversions follow the OneBot12 standard, with platform extensions provided via the `wecom_` prefix.

### Message Event detail_type Mapping

All messages received by WeCom applications are mapped to `private` (private message):

| WeCom Message | OneBot12 type / detail_type |
|---|---|
| `text` | `message` / `private` |
| `image` | `message` / `private` |
| `voice` | `message` / `private` |
| `video` / `shortvideo` | `message` / `private` |
| `location` | `message` / `private` |
| `link` | `message` / `private` |

### Platform-specific Event Types (notice)

| detail_type | Description |
|---|---|
| `wecom_subscribe` | User subscribed / entered application (subscribe / enter_agent) |
| `wecom_unsubscribe` | User unsubscribed |
| `wecom_location_report` | Location report |
| `wecom_menu_click` | Menu click event (click) |
| `wecom_menu_view` | Menu view event (view) |
| `wecom_scancode` | Scan code event |
| `wecom_menu_photo` | Photo/album event |

> Report events (subscription/menu clicks, etc.) are converted to `request` / `notice` type events.

### Standard Message Segment Types

Converted message segments use the OneBot12 standard format:

| Message Segment Type | Description | data Fields |
|---|---|---|
| `text` | Plain text | `text` |
| `image` | Image | `file` (PicUrl or MediaId), `url` |
| `audio` | Audio | `file` (MediaId) |
| `video` | Video | `file` (MediaId), `thumbnail` |
| `location` | Location | `latitude`, `longitude`, `title` |
| `file` | File/Link | `file`, `filename`, `url` |

### Platform Extension Message Segments

Message segments with `wecom_` prefix (for sending direction):

| Message Segment Type | Description | data Fields |
|---|---|---|
| `wecom_markdown` | Markdown message | `content` |
| `wecom_news` | News message | `articles` (list) |
| `wecom_textcard` | Text card | `title`, `description`, `url`, `btntxt` |
| `wecom_miniprogram_notice` | Mini Program Notice | Native fields passed through |
| `wecom_template_card` | Template card | `card_type` + native fields |

### Event Examples

#### Text Message

```python
{
  "id": "1234567890123456",
  "time": 1348831860,
  "type": "message",
  "detail_type": "private",
  "platform": "wecom",
  "self": {"platform": "wecom", "user_id": "Corpid"},
  "message_id": "1234567890123456",
  "user_id": "UserID",
  "user_nickname": "UserID",
  "message": [{"type": "text", "data": {"text": "Message content"}}],
  "alt_message": "Message content",
  "wecom_raw": {"MsgType": "text", "Content": "Message content", "...": "..."},
  "wecom_raw_type": "text",
  "wecom_agentid": "1000002",
  "wecom_corpid": "Corpid",
  "wecom_msg_id": "1234567890123456"
}
```

> **0.1.2 Change**: Message events now include the top-level `message_id` (using WeCom MsgId; fallback to uuid if missing).

#### Menu Click Event

```python
{
  "type": "notice",
  "detail_type": "wecom_menu_click",
  "platform": "wecom",
  "user_id": "UserID",
  "wecom_event_key": "menu_key_1",
  "wecom_raw_type": "event"
}
```

## Event Mixin Extension Methods

The adapter registers the following platform-specific methods, available only when `platform == "wecom"`:

| Method | Return Type | Description |
|--------|-------------|-------------|
| `get_user_id()` | `str` | Get the sender's UserID |
| `get_msg_type()` | `str` | Get the WeCom message type (text/image/...) |
| `get_content()` | `str` | Get the plain text content of the message |
| `get_agentid()` | `str` | Get the application AgentID |
| `get_corpid()` | `str` | Get the enterprise Corpid |
| `get_msg_id()` | `str` | Get the message MsgId |
| `get_raw_xml()` | `str` | Get the decrypted raw XML |
| `get_raw()` | `dict` | Get the parsed raw data dictionary |
| `get_event_key()` | `str` | Get the EventKey of the menu event |
| `get_media_id()` | `str` | Get the MediaId of the media message |

### Usage Example

```python
from ErisPulse.Core.Event import message, notice

@message.on_message()
async def handle_message(event):
    if event.get("platform") != "wecom":
        return

    msg_type = event.get_msg_type()
    user_id = event.get_user_id()
    content = event.get_content()

    if msg_type == "text":
        await event.reply(f"Received: {content}")

@notice.on_notice()
async def handle_notice(event):
    if event.get("platform") != "wecom":
        return

    if event.get("detail_type") == "wecom_menu_click":
        key = event.get_event_key()
        await event.reply(f"You clicked the menu: {key}")
```

## Extension Field Description

- All unique fields are identified with the `wecom_` prefix.
- Original data is retained in the `wecom_raw` field (parsed dictionary).
- The decrypted original XML is retained in the `wecom_raw_xml` field.
- The original event type is retained in the `wecom_raw_type` field.
- `wecom_corpid`: Enterprise ID.
- `wecom_agentid`: Application AgentID.
- `wecom_msg_id`: WeCom message ID.

## Authentication and Encryption

### access_token Management

- Each account has an independently cached access_token
- Validity period: 7200 seconds, automatically refreshed 5 minutes in advance
- When the token expires (errcode 40014/42001), the cache is automatically cleared and the request is retried

### Message Encryption and Decryption

- Algorithm: AES-256-CBC (PKCS7 padding)
- Key: `base64decode(EncodingAESKey + "=")` (32 bytes)
- IV: First 16 bytes of the key
- Signature: `sha1("".join(sorted([token, timestamp, nonce, encrypt])))`
- Required library: `cryptography`

## Notes

1. **Callback URL must be publicly accessible**: Use an internal network penetration tool for local development; in production, it is recommended to use Nginx reverse proxy to the ErisPulse router port.
2. **Outbound message frequency**: Limited by the enterprise WeChat application message interface (daily quota per application is related to the size of the enterprise); for mass messaging scenarios, use `TaskCard`/`TemplateCard` combined with tags.
3. **access_token validity**: The adapter automatically refreshes the token; when multiple instances are deployed with the same corpid+secret, be aware of the official token mutual kick limit (it is recommended to have one instance handle sending and receiving).
4. **Media files**: Voice files must be in AMR format (enterprise WeChat restriction); for large files, use the temporary material interface (the adapter handles this automatically).