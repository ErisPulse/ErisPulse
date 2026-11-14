# Adapter Standardization Specification

> [!TIP]
> **When to read this**: When you are converting platform-native events into OneBot12-standard events in your adapter—refer to this document to ensure required fields, message segment structure, extension field naming (`{platform}_` prefix), and session type inference are correct. Skip if not needed.

## 1. Core Principles
1. Strict Compatibility: All standard fields must fully comply with the OneBot12 specification.
2. Clear Extension: Platform-specific features must be prefixed with `{platform}_` (e.g., `yunhu_form`).
3. Data Integrity: Original event data must be preserved in the `{platform}_raw` field, and the original event type must be preserved in the `{platform}_raw_type` field.
4. Time Uniformity: All timestamps must be converted to 10-digit Unix timestamps (seconds).
5. Platform Consistency: The `platform` field must match the name/alias registered for the platform in ErisPulse.

## 2. Standard Field Requirements

### 2.1 Required Fields
| Field | Type | Description |
|------|------|------|
| id | string | Unique event identifier |
| time | integer | Unix timestamp (seconds) |
| type | string | Event type |
| detail_type | string | Event detail type (see [Session Type Standard](session-types.md)) |
| sub_type | string | Event sub-type |
| platform | string | Platform name |
| self | object | Bot self information |
| self.platform | string | Platform name |
| self.user_id | string | Bot user ID |

> **OneBot12 Baseline**: `self.platform` / `self.user_id` and `message_id` in message events are baseline-defined fields in OneBot12. The framework directly adopts the baseline definition and does not introduce proprietary extension keys (e.g., `self.account_id` is a limited extension key, used only as a placeholder identifier for dynamic accounts before `user_id` is obtained, see §6).

**detail_type Specification**:
- Must use ErisPulse standard session types (see [Session Type Standard](session-types.md))
- Supported types: `private`, `group`, `user`, `channel`, `guild`, `thread`
- The adapter is responsible for mapping the platform-native type to the standard type

### 2.2 Message Event Fields
| Field | Type | Description |
|------|------|------|
| message_id | string | Message ID (OneBot12 baseline standard required field; the adapter must produce it at the top level of the event) |
| message | array | Array of message segments |
| alt_message | string | Alternate text for message segments |
| user_id | string | User ID |
| user_nickname | string | User nickname (optional) |

### 2.3 Notice Event Fields
| Field | Type | Description |
|------|------|------|
| user_id | string | User ID |
| user_nickname | string | User nickname (optional) |
| operator_id | string | Operator ID (optional) |

### 2.4 Request Event Fields
| Field | Type | Description |
|------|------|------|
| user_id | string | User ID |
| user_nickname | string | User nickname (optional) |
| comment | string | Request note (optional) |
| request_id | string | Request identifier (***strongly recommended***, used for approve/reject operations via the `Request` DSL) |

**`request_id` Field Explanation**:
- `request_id` is the unique operation identifier for request events, used to execute approve/reject operations via the `Request` DSL.
- When converting request events, the adapter should map the platform-native request identifier to this field.
- If the platform itself does not have a request ID, the adapter should generate a unique identifier (e.g., based on a hash of timestamp + user ID).
- When `request_id` is missing, `event.approve()` / `event.reject()` will raise a `ValueError`.

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

| Type | Description | data Fields |
|------|------|----------|
| `text` | Plain text | `text: str` |
| `image` | Image | `file`, `url: str` |
| `voice` | Voice (locally recorded sound, distinct from `audio`) | `file`, `url: str` |
| `audio` | Audio (playable music file, distinct from `voice`) | `file`, `url: str` |
| `video` | Video | `file`, `url: str` |
| `file` | File | `file`, `url: str`, `filename: str` |
| `mention` | @User | `user_id: str`, `user_name: str` |
| `mention_all` | @All Members | No data fields |
| `reply` | Reply | `message_id: str`, `user_id: str` (the original sender, the adapter should try to fill it in the receiving direction) |
| `location` | Location | `latitude: float`, `longitude: float`, `title: str` (optional), `content: str` (optional) |
| `face` | Face (ErisPulse cross-platform extension segment) | `id: str` |
| `keyboard` | Button/Inline Keyboard (ErisPulse cross-platform extension segment) | `rows: list[list[button]]` (see 4.1.1) |

> **Field Mapping with OneBot12 Baseline**: Media segments (`image` / `voice` / `audio` / `video` / `file`) in the OneBot12 baseline are `file_id: str`; this standard's `file` (send form superset: URL / local path / bytes) and `url` (receive backlink) are bidirectionally mapped by the adapter to the platform's `file_id` resource. `face` / `keyboard` are extension segments outside the OneBot12 baseline.

**Media Segment `file` Field Format** (send direction, `image` / `audio` / `video` / `file` generic):

| Form | Example | Adapter Requirements |
|------|------|-----------|
| HTTP(S) URL | `https://example.com/a.png` | **Must** accept |
| Local file path | `/tmp/a.png`, `C:\tmp\a.png` | **Must** accept |
| Binary data | `bytes` | **Must** accept |
| `file://` URI / Base64 / Data URI | `file:///tmp/a.png`, `data:image/png;base64,...` | **Should** accept |

> The complete media sending protocol (form determination order, filename derivation, capability degradation ladder) is detailed in
> [Send Method Specification §2.1](send-method-spec.md#21-media-message-sending-protocolimage--voice--video--file).

**Field Direction Semantics**:

- `file`: **Send direction** content source (the above forms); **Receive direction** is filled by the adapter with a platform retrievable form (usually a downloadable URL, or a resource identifier usable with `get_file`-like actions)
- `url`: **Receive direction** platform backlink (the adapter should fill it as much as possible when converting platform events, for direct use by modules); **Send direction** can be omitted
- `filename`: `file` segment's file name (send direction optional, if missing the adapter generates it according to the derivation order in [Send Method Specification §2.1.3](send-method-spec.md); receive direction **should** fill the platform's original file name)

```json
{
  "type": "text",
  "data": {
    "text": "Hello World"
  }
}
```

### 4.1.1 keyboard Button/Inline Keyboard Segment (Cross-Platform Universal)

Buttons/Inline keyboards exist on multiple platforms (Telegram / Yunhu / QQBot / Kook / Discord, etc.), representing a **cross-platform universal concept**, thus they are standard message segments (no platform prefix). Adapters should convert standard segments into platform-native structures; platform-native extension segments (e.g., `telegram_inline_keyboard`) continue to be retained and passed through.

```json
{
  "type": "keyboard",
  "data": {
    "rows": [
      [
        {"label": "Option A", "type": "callback", "data": "vote:A"},
        {"label": "Website", "type": "link", "data": "https://example.com"}
      ]
    ]
  }
}
```

**Field Description**:

| Field | Type | Required | Description |
|------|------|------|------|
| `rows` | 2D array | Yes | Each sub-array is a row of buttons |
| `rows[][].label` | str | Yes | Button display text |
| `rows[][].type` | str | Yes | `callback` (click back data) / `link` (jump to URL) |
| `rows[][].data` | str | Yes | Callback data (type=callback) or jump address (type=link) |
| `rows[][].*` | Any | No | Platform-specific optional fields (e.g., `web_app`, `menus`), adapters map or ignore based on capability |

**Adapter Conversion Reference** (full mapping and interaction callback event standard in [Cross-Platform Interaction Component Standard](standardization-guide.md)):

| Platform | Standard Segment → Platform Native |
|------|------------------|
| Telegram | `inline_keyboard`: `[{text, callback_data \| url}]` |
| Yunhu | `buttons`: `[{label, action_type: 2=callback \| 1=jump, ...}]` |
| QQBot | `keyboard.content.rows`: `[{label, type: 2=callback \| 0=jump, data}]` (requires markdown type message) |
| Kook | Card action-group module |
| Discord | components: `action_row` + `buttons` (custom_id/url) |

### 4.2 Platform Extension Message Segments

Platform-specific message segments require a platform prefix:

```json
// Yunhu - Form
{"type": "yunhu_form", "data": {"form_id": "123456", "form_name": "Registration Form"}}

// Telegram - Sticker
{"type": "telegram_sticker", "data": {"file_id": "CAACAgIAAxkBAA...", "emoji": "😂"}}
```

**Extension Message Segment Requirements**:
1. **No prefix in `data` internal fields**: `{"type": "yunhu_form", "data": {"form_id": "..."}}` instead of `{"type": "yunhu_form", "data": {"yunhu_form_id": "..."}}`
2. **Provide degradation solutions**: Modules may not recognize extension message segments; adapters should provide text alternatives in `alt_message`
3. **Complete documentation**: Each extension message segment must be documented in the adapter documentation with `type`, `data` structure, and usage scenarios

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

---

## 6. Extension Naming Convention

### 6.1 Field Naming

**Rule**: `{platform}_{field_name}`

```
Platform Prefix    Field Name            Full Field Name
────────    ───────          ──────────
yunhu       command           yunhu_command
telegram    sticker_file_id   telegram_sticker_file_id
onebot11    anonymous         onebot11_anonymous
email       subject           email_subject
```

**Requirements**:
- `platform` must exactly match the platform name registered with the adapter (case-sensitive)
- `field_name` uses `snake_case` naming
- No double underscores `__` at the beginning (reserved for Python)
- No field names that conflict with standard fields (e.g., `type`, `time`, `message`, etc.)

### 6.2 Message Segment Type Naming

**Rule**: `{platform}_{segment_type}`

Standard message segment types (`text`, `image`, `audio`, `video`, `mention`, `reply`, etc.) **do not** require a platform prefix. Only platform-specific message segment types require a prefix.

### 6.3 Raw Data Field Naming

The following field names are **reserved fields** that all adapters must follow:

| Reserved Field | Type | Description |
|---------|------|------|
| `{platform}_raw` | `any` | A complete copy of the original platform event data |
| `{platform}_raw_type` | `string` | The identifier of the original platform event type |

**Requirements**:
- `{platform}_raw` must be a deep copy of the original data, not a reference
- `{platform}_raw_type` must be a string, even if the platform uses a numeric type, it must be converted to a string
- These two fields must exist in all events (if unavailable, use `null` and empty string `""`)

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
- The top-level key must have a platform prefix
- Nested internal fields **do not** have a platform prefix
- Nested depth is recommended to be no more than 3 levels

### 6.6 `self` Field Extension

The standard required fields for the `self` object (`platform`, `user_id`) are listed in §2.1. The following are ErisPulse extensions for optional fields:

| Field | Type | Description |
|------|------|------|
| `self.user_name` | `string` | Bot nickname |
| `self.avatar` | `string` | Bot avatar URL |
| `self.account_id` | `string` | **Limited extension key (account name substitution)**: When a dynamically injected account does not yet have a `user_id`, use the account name/account identifier as a placeholder to ensure the event can be attributed; once `self.user_id` is available, it must be prioritized. The framework uses the `account_id or user_id`口径 to be compatible with both—when using account name substitution, `reply()` binds to the correct account via account name matching.

> **Runtime Boundary**: Events must always carry `self.user_id` (including during the window before binding is established). The connection layer injects known identifiers into events received before the binding table is filled and before the connect meta arrives: when the bot's `user_id` is not yet obtained, use the account name to fill `self.account_id` as a placeholder (the framework parses via the `account_id or user_id`口径, and the account name can route back to the correct account via account name matching); once obtained, prioritize filling `self.user_id`—the framework needs to be able to determine "which account this event comes from" at any stage of the event. The consequence of missing it is certain: `event.reply()` does not inject an account, and sending without a specified account falls back to the first enabled account, which for multi-account adapters manifests as "sent from the default account."

> **Bot Status Tracking**: Adapters inform the framework of the bot's connection status by sending `type: "meta"` events. Supported `detail_type`: `connect` (online), `heartbeat` (heartbeat), `disconnect` (offline). The system automatically extracts the bot metadata from the `self` field in these events for status tracking. Additionally, the `self` field in regular events is automatically discovered for the bot. See [Adapter System API - Bot Status Management](../api-reference/adapter-system.md).

---

## 7. Session Type Extension

ErisPulse extends the OneBot12 standard `private` and `group` with the following session types:

| Type | OneBot12 Standard | ErisPulse Extension | Description |
|------|:-----------:|:------------:|------|
| `private` | ✅ | — | One-on-one private chat |
| `group` | ✅ | — | Group chat |
| `user` | — | ✅ | User type (Telegram, etc.) |
| `channel` | — | ✅ | Channel (broadcast) |
| `guild` | — | ✅ | Server/community |
| `thread` | — | ✅ | Thread/subchannel |

**Adapter Custom Type Extension**:

```python
from ErisPulse.Core.Event.session_type import register_custom_type

# Register in adapter startup
register_custom_type(
    receive_type="email",      # detail_type in receive events
    send_type="email",         # target type when sending
    id_field="email_id",       # corresponding ID field name
    platform="email"           # platform identifier
)
```

**Custom Type Requirements**:
- Must be registered in the adapter's `start()` and unregistered in `shutdown()`
- `receive_type` should not conflict with standard types
- `id_field` should follow the `{target}_id` naming pattern

> Complete session type definitions and mapping relationships are available in [Session Type Standard](session-types.md).

---

## 8. Module Developer Guide

### 8.1 Accessing Extension Fields

```python
from ErisPulse.Core.Event import message

@message()
async def handle_message(event):
    # Access standard fields
    text = event.get_text()
    user_id = event.get_user_id()

    # Access platform extension fields - Method 1: Direct get
    yunhu_command = event.get("yunhu_command")

    # Access platform extension fields - Method 2: Dot notation access (Event wrapper class)
    # event.yunhu_command

    # Access raw data
    raw_data = event.get("yunhu_raw")
    raw_type = event.get_raw_type()

    # Platform detection
    platform = event.get_platform()
    if platform == "yunhu":
        pass
    elif platform == "telegram":
        pass
```

### 8.2 Handling Extension Message Segments

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

1. **Prefer standard fields**: Do not assume extension fields will always exist
2. **Platform detection**: Use `event.get_platform()` to detect the platform, not by checking the existence of extension fields
3. **Graceful degradation**: Use `alt_message` as a fallback when unable to handle extension message segments
4. **Do not hardcode prefixes**: Use `platform` variable to dynamically construct

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

# Friend request: Auto-approve
@request.on_friend_request()
async def handle_friend_request(event):
    user_name = event.get_user_nickname() or event.get_user_id()
    comment = event.get_comment()
    
    # Approve request
    result = await event.approve()
    if result.get("status") == "ok":
        print(f"Approved friend request from {user_name}")
    else:
        print(f"Failed to approve friend request: {result.get('message')}")

# Group invitation: Decide based on conditions
@request.on_group_request()
async def handle_group_request(event):
    comment = event.get_comment()
    
    # Reject request
    result = await event.reject(comment="Not joining new group for now")
```

**Direct operation via adapter** (for non-event handler scenarios):

```python
from ErisPulse import adapter

# Direct operation via request_id
await adapter.myplatform.Request("req_abc123").accept()
await adapter.myplatform.Request("req_abc123").reject()

# Specify bot account
await adapter.myplatform.Request("req_abc123").Using("bot1").accept()

# With comment
await adapter.myplatform.Request("req_abc123").accept(comment="Welcome")
```

---

## 9. Session Type Inference for notice / request Events

### 9.1 Problem Background

The `detail_type` of `notice` and `request` events are **semantic sub-types** (e.g., `group_member_increase`, `friend_increase`), not session types (e.g., `group`, `private`).

```
type        detail_type                  Meaning            Session Type
────        ───────────                  ────            ────────
message     group                        Group message         group (detail_type is session type)
message     private                      Private message       private (detail_type is session type)
notice      group_member_increase        Member increase       group (inferred from group_id)
notice      friend_increase              Friend increase       private (inferred from user_id)
request     friend                       Friend request        private (inferred from user_id)
request     group                        Group request         group (detail_type is session type)
```

### 9.2 Inference Rules

The inference order for `infer_receive_type()`:

1. If `detail_type` is a known session type (`private`/`group`/`channel`/`guild`/`thread`/`user`), use it directly
2. If `detail_type` is a custom session type, use it directly
3. Otherwise (semantic sub-types of notice/request), infer based on ID fields:
   - If `group_id` is present → `"group"`
   - If `channel_id` is present → `"channel"`
   - If `guild_id` is present → `"guild"`
   - If `thread_id` is present → `"thread"`
   - If `user_id` is present → `"private"`

### 9.3 `event.reply()` Target Inference

The send target of `event.reply()` in notice/request events is determined by session type inference:

- Group notice events (with `group_id`) → Reply to **group**
- Friend notice events (with only `user_id`) → Reply to **private chat**

```python
from ErisPulse.Core.Event import notice

@notice.on_group_increase()
async def handle_welcome(event):
    group_id = event.get("group_id")    # "group_789"
    user_id = event.get("user_id")      # "user_456"

    # event.reply() sends to group (group/group_789)
    await event.reply("Welcome to the group!")

    # If you need to notify the admin (private chat), specify the target explicitly:
    await adapter.Send.To("user", "admin_id").Text(f"New member {user_id} joined {group_id}")
```

### 9.4 Adapter Development Recommendations

Ensure notice/request events contain the correct ID fields:

| detail_type | Required ID Field | Inferred Session Type |
|-------------|-------------------|---------------|
| `group_member_increase` | `group_id` + `user_id` | `group` |
| `group_member_decrease` | `group_id` + `user_id` | `group` |
| `friend_increase` | `user_id` | `private` |
| `friend_decrease` | `user_id` | `private` |
| `friend` (request) | `user_id` | `private` |
| `group` (request) | `group_id` | `group` |

---

## 10. Related Documentation

**For implementing converters, refer to:**
- [Session Type Standard](session-types.md) - Session type definitions and mapping relationships
- [API Response Standard](api-response.md) - Standard format for adapter API responses

**For send-side of the same adapter:**
- [Send Method Specification](send-method-spec.md) - Naming, parameter specifications, and reverse conversion requirements for Send class methods
- [API Action Standard](api-action-spec.md) - Unified interface for OneBot12 standard API actions

**For known extension events and message segments for each platform:**
- [Platform Features Documentation](../platform-guide/README.md) - You can access this document to learn about platform features and known extension events and message segments.