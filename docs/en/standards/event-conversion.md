# Adapter Standardization Conversion Specification

## 1. Core Principles
1.  **Strict Compatibility:** All standard fields must fully comply with the OneBot12 specification.
2.  **Explicit Extension:** Platform-specific features must add a `{platform}_` prefix (e.g., yunhu_form).
3.  **Data Integrity:** Original event data must be preserved in the `{platform}_raw` field, and the original event type must be preserved in the `{platform}_raw_type` field.
4.  **Time Unification:** All timestamps must be converted to 10-digit Unix timestamps (seconds).
5.  **Platform Unification:** The `platform` item name must be consistent with the name/alias registered in ErisPulse.

## 2. Standard Field Requirements

### 2.1 Required Fields
| Field | Type | Description |
|-------|------|-------------|
| id | string | Unique event identifier |
| time | integer | Unix timestamp (seconds) |
| type | string | Event type |
| detail_type | string | Event detail type (see [Session Types Standard](session-types.md)) |
| platform | string | Platform name |
| self | object | Bot self-information |
| self.platform | string | Platform name |
| self.user_id | string | Bot user ID |

**detail_type Specification**:
- Must use ErisPulse standard session types (see [Session Types Standard](session-types.md))
- Supported types: `private`, `group`, `user`, `channel`, `guild`, `thread`
- The adapter is responsible for mapping platform-native types to standard types

### 2.2 Message Event Fields
| Field | Type | Description |
|-------|------|-------------|
| message | array | Message segment array |
| alt_message | string | Message segment fallback text |
| user_id | string | User ID |
| user_nickname | string | User nickname (optional) |

### 2.3 Notice Event Fields
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
  "onebot11_raw": {...},
  "onebot11_raw_type": "request" // onebot11 original event type is request
}
```

## 4. Message Segment Standard

### 4.1 Generic Message Segment
```json
{
  "type": "text",
  "data": {
    "text": "Hello World"
  }
}
```

### 4.2 Special Message Segment
Platform-specific message segments need to add platform prefixes:
```json
{
  "type": "yunhu_form",
  "data": {
    "form_id": "123456"
  }
}
```

## 5. Unknown Event Handling

For unrecognizable event types, a warning event should be generated:
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

## 6. Platform Specific Fields

All platform-specific fields must be prefixed with the platform name.

For example:
- Yunhu platform: `yunhu_`
- Telegram platform: `telegram_`
- OneBot11 platform: `onebot11_`

### 6.1 Specific Field Examples
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

## 7. Adapter Implementation Checklist
- [ ] All standard fields have been correctly mapped
- [ ] Platform-specific fields have been prefixed
- [ ] Timestamps have been converted to 10-digit seconds
- [ ] Raw data is saved in {platform}_raw, and original event type is saved to {platform}_raw_type
- [ ] alt_message for message segments has been generated
- [ ] All event types have passed unit tests
- [ ] Documentation contains complete examples and descriptions