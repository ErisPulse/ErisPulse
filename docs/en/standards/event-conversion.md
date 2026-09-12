# Adapter Standardization Conversion Specification

## 1. Core Principles

1. Strict Compatibility: All standard fields must fully comply with the OneBot12 specification.
2. Explicit Extensions: Platform-specific features must be prefixed with {platform}_ (e.g., yunhu_form).
3. Data Integrity: Original event data must be preserved in the {platform}_raw field, and the original event type must be preserved in the {platform}_raw_type field.
4. Time Standardization: All timestamps must be converted to 10-digit Unix timestamps (in seconds).
5. Platform Consistency: The platform field name must match the name/alias you registered in ErisPulse.

## 2. Standard Field Requirements

### 2.1 Required Fields
| Field | Type | Description |
|-------|------|-------------|
| id | string | Unique identifier for the event |
| time | integer | Unix timestamp (in seconds) |
| type | string | Event type |
| detail_type | string | Detailed event type (see [Session Type Standard](session-types.md)) |
| platform | string | Platform name |
| self | object | Bot self information |
| self.platform | string | Platform name |
| self.user_id | string | Bot user ID |

**detail_type Specification**:
- Must use ErisPulse standard session types (see [Session Type Standard](session-types.md))
- Supported types: `private`, `group`, `user`, `channel`, `guild`, `thread`
- Adapters are responsible for mapping native platform types to standard types

### 2.2 Message Event Fields
| Field | Type | Description |
|-------|------|-------------|
| message | array | Array of message segments |
| alt_message | string | Alternate text for message segments |
| user_id | string | User ID |
| user_nickname | string | User nickname (optional) |

### 2.3 Notification Event Fields
| Field | Type | Description |
|-------|------|-------------|
| user_id | string | User ID |
| user_nickname | string | User nickname (optional) |
| operator_id | string | Operator ID (optional) |

### 2.4 Request Event Fields
| Field | Type | Description |
|-------|------|-------------|
| user_id | string | User ID |
| user_nickname | string | User nickname (optional) |
| comment | string | Request comment (optional) |
| request_id | string | Request identifier (**strongly recommended**, used to approve/reject request operations) |

**`request_id` Field Explanation**:
- `request_id` is the unique operation identifier for request events, used to execute approve/reject operations via the `HandleRequest` DSL
- Adapters should map native platform request identifiers to this field when converting request events
- If the platform does not have a request ID, the adapter should generate a unique identifier (e.g., a hash based on timestamp + user ID)
- When `request_id` is missing, `event.approve()` / `event.reject()` will raise a `ValueError`

## 3. Event Format Examples

### 3.1 Message Event (message)
```json
{
  "id": "1234567890",
  "time": 1752241223,
  "type": "message",
  "detail_type": "group",
  "platform": "yunhu",
  "self": {
    "platform": "yunhu",
    "user_id": "bot_123"
  },
  "message": [
    {
      "type": "text",
      "data": {
        "text": "抽奖 超级大奖"
      }
    }
  ],
  "alt_message": "抽奖 超级大奖",
  "user_id": "user_456",
  "user_nickname": "YingXinche",
  "group_id": "group_789",
  "yunhu_raw": {...},
  "yunhu_raw_type": "message.receive.normal",
  "yunhu_command": {
    "name": "抽奖",
    "args": "超级大奖"
  }
}
```

### 3.2 Notice Event (notice)
```json
{
  "id": "1234567891",
  "time": 1752241224,
  "type": "notice",
  "detail_type": "group_member_increase",
  "platform": "yunhu",
  "self": {
    "platform": "yunhu",
    "user_id": "bot_123"
  },
  "user_id": "user_456",
  "user_nickname": "YingXinche",
  "group_id": "group_789",
  "operator_id": "",
  "yunhu_raw": {...},
  "yunhu_raw_type": "bot.followed"
}
```

### 3.3 Request Event (request)
```json
{
  "id": "1234567892",
  "time": 1752241225,
  "type": "request",
  "detail_type": "friend",
  "platform": "onebot11",
  "self": {
    "platform": "onebot11",
    "user_id": "bot_123"
  },
  "user_id": "user_456",
  "user_nickname": "YingXinche",
  "comment": "请加好友",
  "request_id": "req_abc123",
  "onebot11_raw": {...},
  "onebot11_raw_type": "request"
}
```

## 4. Message Segment Standard

### 4.1 Standard Message Segments

Standard message segments **do not** require a platform prefix.

| Type | Description | data field |
|------|-------------|------------|
| `text` | Plain text | `text: str` |
| `image` | Image | `file: str/bytes`, `url: str` |
| `audio` | Audio | `file: str/bytes`, `url: str` |
| `video` | Video | `file: str/bytes`, `url: str` |
| `file` | File | `file: str/bytes`, `url: str`, `filename: str` |
| `mention` | @User | `user_id: str`, `user_name: str` |
| `reply` | Reply | `message_id: str` |
| `face` | Emoji | `id: str` |
| `location` | Location | `latitude: float`, `longitude: float` |
| `keyboard` | Button / Inline Keyboard | `rows: list[list[button]]` (see 4.1.1) |

```json
{
  "type": "text",
  "data": {
    "text": "Hello World"
  }
}
```

### 4.1.1 keyboard Button / Inline Keyboard Segment (Cross-Platform Compatible)

Buttons and inline keyboards are supported on multiple platforms (Telegram / Yunhu / QQBot / Kook / Discord, etc.), making them a **cross-platform compatible concept**. Therefore, they are defined as standard message segments (without platform prefix). Adapters should convert standard segments into platform-native structures; platform-native extended segments (e.g., `telegram_inline_keyboard`) remain as passthrough.

```json
{
  "type": "keyboard",
  "data": {
    "rows": [
      [
        {"label": "Option A", "type": "callback", "data": "vote:A"},
        {"label": "Official Website", "type": "link", "data": "https://example.com"}
      ]
    ]
  }
}
```

**Field Description:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `rows` | 2D array | Yes | Each sub-array represents a row of buttons |
| `rows[][].label` | str | Yes | Button display text |
| `rows[][].type` | str | Yes | `callback` (click to return data) / `link` (redirect to URL) |
| `rows[][].data` | str | Yes | Callback data (type=callback) or redirect address (type=link) |
| `rows[][].*` | Any | No | Platform-specific optional fields (e.g., `web_app`, `menus`), adapters map or ignore based on capability |

**Adapter Conversion Reference** (for full mapping and interaction callback event standards, see [Cross-Platform Interaction Component Standard](standardization-guide.md)):

| Platform | Standard Segment → Platform Native |
|----------|-----------------------------------|
| Telegram | `inline_keyboard`: `[{text, callback_data \| url}]` |
| Yunhu | `buttons`: `[{label, action_type: 2=callback \| 1=redirect, ...}]` |
| QQBot | `keyboard.content.rows`: `[{label, type: 2=callback \| 0=redirect, data}]` (requires markdown-type message) |
| Kook | Card action-group module |
| Discord | components: `action_row` + `buttons` (custom_id/url) |

### 4.2 Platform-Extended Message Segments

Platform-specific message segments require a platform prefix:

```json
// Yunhu - Form
{"type": "yunhu_form", "data": {"form_id": "123456", "form_name": "Registration Form"}}

// Telegram - Sticker
{"type": "telegram_sticker", "data": {"file_id": "CAACAgIAAxkBAA...", "emoji": "😂"}}
```

**Extended Message Segment Requirements**:
1. **No prefix in data fields**: `{"type": "yunhu_form", "data": {"form_id": "..."}}` instead of `{"type": "yunhu_form", "data": {"yunhu_form_id": "..."}}`
2. **Provide fallback options**: Modules may not recognize extended message segments; adapters should provide text alternatives in `alt_message`
3. **Complete documentation**: Each extended message segment must be documented in the adapter, including `type`, `data` structure, and usage scenarios

## 5. Handling Unknown Events

For unrecognized event types, a warning event should be generated:
```json
{
  "id": "1234567893",
  "time": 1752241223,
  "type": "unknown",
  "platform": "yunhu",
  "yunhu_raw": {...},
  "yunhu_raw_type": "unknown",
  "warning": "Unsupported event type: special_event",
  "alt_message": "This event type is not supported by this system."
}
```

## 6. Extension Naming Convention

### 6.1 Field Naming

**Rule**: `{platform}_{field_name}`

```
Platform Prefix  Field Name          Full Field Name
──────────────── ─────────────────── ───────────────────
yunhu            command             yunhu_command
telegram         sticker_file_id     telegram_sticker_file_id
onebot11         anonymous           onebot11_anonymous
email            subject             email_subject
```

**Requirements**:
- `platform` must exactly match the platform name registered with the adapter (case-sensitive)
- `field_name` must use `snake_case` naming
- Double underscores `__` at the beginning are forbidden (reserved by Python)
- Field names must not conflict with standard fields (e.g., `type`, `time`, `message`, etc.)

### 6.2 Message Segment Type Naming

**Rule**: `{platform}_{segment_type}`

Standard message segment types (`text`, `image`, `audio`, `video`, `mention`, `reply`, etc.) **must not** have a platform prefix. Only platform-specific message segment types require a prefix.

### 6.3 Raw Data Field Naming

The following field names are **reserved fields** that all adapters must follow:

| Reserved Field | Type | Description |
|----------------|------|-------------|
| `{platform}_raw` | `any` | A deep copy of the complete original platform event data |
| `{platform}_raw_type` | `string` | The platform's original event type identifier |

**Requirements**:
- `{platform}_raw` must be a deep copy of the original data, not a reference
- `{platform}_raw_type` must be a string; if the platform uses a numeric type, it must be converted to a string
- These two fields must exist in all events (use `null` if unavailable, and an empty string `""` if the type is unavailable)

### 6.4 Platform-Specific Field Examples

```json
{
  "yunhu_command": {
    "name": "抽奖",
    "args": "超级大奖"
  },
  "yunhu_form": {
    "form_id": "123456"
  },
  "telegram_sticker": {
    "file_id": "CAACAgIAAxkBAA..."
  }
}
```

### 6.5 Nested Extension Fields

Extension fields can be simple values or nested objects:

```json
{
  "telegram_chat": {
    "id": 123456,
    "type": "supergroup",
    "title": "My Group"
  },
  "telegram_forward_from": {
    "user_id": "789",
    "user_name": "ForwardUser"
  }
}
```

**Nested Field Requirements**:
- Top-level keys must include the platform prefix
- Nested internal fields **must not** include the platform prefix
- Nesting depth should be limited to 3 levels

### 6.6 `self` Field Extension

The standard required fields for the `self` object (`platform`, `user_id`) are listed in §2.1. The following are optional fields extended by ErisPulse:

| Field | Type | Description |
|-------|------|-------------|
| `self.user_name` | `string` | Bot nickname |
| `self.avatar` | `string` | Bot avatar URL |
| `self.account_id` | `string` | Account identifier in multi-account mode |

> **Bot Status Tracking**: Adapters inform the framework of the Bot's connection status by sending `type: "meta"` events. Supported `detail_type` values are: `connect` (online), `heartbeat` (heartbeat), `disconnect` (offline). The system automatically extracts Bot metadata from the `self` field in these events for status tracking. Additionally, the `self` field in regular events is also automatically detected as the Bot. See [Adapter System API - Bot Status Management](../api-reference/adapter-system.md) for more details.

---

## 7. Session Type Extension

ErisPulse extends the OneBot12 standard's `private` and `group` session types with the following additional session types:

| Type | OneBot12 Standard | ErisPulse Extension | Description |
|------|:-----------:|:------------:|------|
| `private` | ✅ | — | One-to-one private chat |
| `group` | ✅ | — | Group chat |
| `user` | — | ✅ | User type (e.g., Telegram) |
| `channel` | — | ✅ | Channel (broadcast-style) |
| `guild` | — | ✅ | Server/community |
| `thread` | — | ✅ | Topic/subchannel |

**Adapter Custom Type Extension**:

```python
from ErisPulse.Core.Event.session_type import register_custom_type

# Register during adapter startup
register_custom_type(
    receive_type="email",      # detail_type in receive events
    send_type="email",         # target type for sending
    id_field="email_id",       # corresponding ID field name
    platform="email"           # platform identifier
)
```

**Custom Type Requirements**:
- Must be registered during the adapter's `start()` and unregistered during `shutdown()`
- `receive_type` should not conflict with standard types
- `id_field` should follow the `{target}_id` naming convention

> For a complete definition and mapping of session types, see [Session Types Standard](session-types.md).

## 8. Module Developer Guide

### 8.1 Accessing Extended Fields

```python
from ErisPulse.Core.Event import message

@message()
async def handle_message(event):
    # Access standard fields
    text = event.get_text()
    user_id = event.get_user_id()

    # Access platform extended fields - Method 1: Direct get
    yunhu_command = event.get("yunhu_command")

    # Access platform extended fields - Method 2: Dot-style access (Event wrapper class)
    # event.yunhu_command

    # Access raw data
    raw_data = event.get("yunhu_raw")
    raw_type = event.get_raw_type()

    # Determine platform
    platform = event.get_platform()
    if platform == "yunhu":
        pass
    elif platform == "telegram":
        pass
```

### 8.2 Handling Extended Message Segments

```python
@message()
async def handle_message(event):
    message_segments = event.get("message", [])

    for segment in message_segments:
        seg_type = segment.get("type")
        seg_data = segment.get("data", {})

        if seg_type == "text":
            text = seg_data["text"]
        elif seg_type.startswith("yunhu_"):
            if seg_type == "yunhu_form":
                form_id = seg_data["form_id"]
        elif seg_type.startswith("telegram_"):
            if seg_type == "telegram_sticker":
                file_id = seg_data["file_id"]
```

### 8.3 Best Practices

1. **Prefer Standard Fields**: Do not assume extended fields are always present
2. **Platform Detection**: Use `event.get_platform()` to determine the platform, rather than inferring from the presence of extended fields
3. **Graceful Degradation**: Use `alt_message` as a fallback when unable to process extended message segments
4. **Avoid Hardcoding Prefixes**: Dynamically construct using the `platform` variable

```python
# ✅ Recommended
platform = event.get_platform()
raw_data = event.get(f"{platform}_raw")

# ❌ Not recommended
raw_data = event.get("yunhu_raw")
```

### 8.4 Request Event Handling

Module developers can use `event.approve()` and `event.reject()` to handle request events:

```python
from ErisPulse.Core.Event import request

# Friend Request: Auto-approve
@request.on_friend_request()
async def handle_friend_request(event):
    user_name = event.get_user_nickname() or event.get_user_id()
    comment = event.get_comment()
    
    # Approve the request
    result = await event.approve()
    if result.get("status") == "ok":
        print(f"Approved friend request from {user_name}")
    else:
        print(f"Failed to approve friend request: {result.get('message')}")

# Group Invitation: Decide based on conditions
@request.on_group_request()
async def handle_group_request(event):
    comment = event.get_comment()
    
    # Reject the request
    result = await event.reject(comment="Temporarily not joining new group")
```

**Direct Operations via Adapter** (for non-event handler scenarios):

```python
from ErisPulse import adapter

# Directly operate using request_id
await adapter.myplatform.Request("req_abc123").accept()
await adapter.myplatform.Request("req_abc123").reject()

# Specify Bot account for operation
await adapter.myplatform.Request("req_abc123").Using("bot1").accept()

# Include comment
await adapter.myplatform.Request("req_abc123").accept(comment="Welcome")
```

## 9. Session Type Inference for notice / request Events

### 9.1 Problem Background

The `detail_type` of `notice` and `request` events are **semantic subtypes** (e.g., `group_member_increase`, `friend_increase`), not session types (e.g., `group`, `private`).

```
type        detail_type                  Meaning            Session Type
────        ───────────                  ────            ────────
message     group                        Group message         group (detail_type is session type)
message     private                      Private message       private (detail_type is session type)
notice      group_member_increase        Group member increase group (inferred from group_id)
notice      friend_increase              Friend increase       private (inferred from user_id)
request     friend                       Friend request        private (inferred from user_id)
request     group                        Group request         group (detail_type is session type)
```

### 9.2 Inference Rules

The inference order for `infer_receive_type()`:

1. If `detail_type` is a known session type (`private`/`group`/`channel`/`guild`/`thread`/`user`), use it directly
2. If `detail_type` is a custom session type, use it directly
3. Otherwise (semantic subtypes of notice/request), infer based on ID fields:
   - If `group_id` exists → `"group"`
   - If `channel_id` exists → `"channel"`
   - If `guild_id` exists → `"guild"`
   - If `thread_id` exists → `"thread"`
   - If `user_id` exists → `"private"`

### 9.3 `event.reply()` Target Inference

The target of `event.reply()` in notice/request events is determined by session type inference:

- Group notice events (with `group_id`) → reply to the **group**
- Friend notice events (with only `user_id`) → reply to the **private user**

```python
from ErisPulse.Core.Event import notice

@notice.on_group_increase()
async def handle_welcome(event):
    group_id = event.get("group_id")    # "group_789"
    user_id = event.get("user_id")      # "user_456"

    # event.reply() sends to the group (group/group_789)
    await event.reply("Welcome to the group!")

    # If you need to notify the admin (private chat), specify the target explicitly:
    await adapter.Send.To("user", "admin_id").Text(f"New member {user_id} joined {group_id}")
```

### 9.4 Adapter Development Recommendations

Ensure that notice/request events contain the correct ID fields:

| detail_type             | Required ID Fields        | Inferred Session Type |
|-------------------------|---------------------------|------------------------|
| `group_member_increase` | `group_id` + `user_id`    | `group`                |
| `group_member_decrease` | `group_id` + `user_id`    | `group`                |
| `friend_increase`       | `user_id`                 | `private`              |
| `friend_decrease`       | `user_id`                 | `private`              |
| `friend` (request)      | `user_id`                 | `private`              |
| `group` (request)       | `group_id`                | `group`                |

## 10. Related Documents

- [Platform Features Documentation](../platform-guide/README.md) - You can visit this document to learn about platform-specific features, as well as known extension events and message segments.
- [Session Type Standard](session-types.md) - Definition and mapping relationships of session types
- [Send Method Specification](send-method-spec.md) - Naming, parameter specifications, and reverse conversion requirements for methods in the Send class
- [API Response Standard](api-response.md) - Standard format for adapter API responses
- [API Action Specification](api-action-spec.md) - Unified interface for OneBot12 standard API actions