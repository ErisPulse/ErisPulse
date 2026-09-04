# ErisPulse Adapter Standardized Return Specification

## 1. Description
Why does this specification exist?

To ensure the uniformity of interface responses across platforms and compatibility with OneBot12, the ErisPulse adapter adopts the message sending return structure standard defined by OneBot12 for API response formats.

However, ErisPulse's protocol includes some special definitions:
- 1. In the basic fields, `message_id` is required, but this field is not defined in the OneBot12 standard.
- 2. The return content needs to add a `{platform_name}_raw` field to store the raw response data.

## 2. Basic Return Structure
All action responses must include the following basic fields:

| Field Name | Data Type | Required | Description |
|------------|-----------|----------|-------------|
| status | string | Yes | Execution status, must be "ok" or "failed" |
| retcode | int64 | Yes | Return code, follows OneBot12 return code rules |
| data | any | Yes | Response data, contains the request result on success, null on failure |
| message_id | string | Yes | Message ID, used to identify the message; empty string if not available |
| message | string | Yes | Error message, empty string on success |
| {platform_name}_raw | any | No | Raw response data |

Optional field:
| Field Name | Data Type | Required | Description |
|------------|-----------|----------|-------------|
| echo | string | No | Returns the value of the echo field from the request, if present |

## 3. Complete Field Specification

### 3.1 Common Fields

#### Success Response Example
```json
{
    "status": "ok",
    "retcode": 0,
    "data": {
        "message_id": "1234",
        "time": 1632847927.599013
    },
    "message_id": "1234",
    "message": "",
    "echo": "1234",
    "telegram_raw": {...}
}
```

#### Failure Response Example
```json
{
    "status": "failed",
    "retcode": 10003,
    "data": null,
    "message_id": "",
    "message": "Missing required parameter: user_id",
    "echo": "1234",
    "telegram_raw": {...}
}
```

### 3.2 Return Code Specification

#### 0 Success (OK)
- 0: Success (OK)

#### 1xxxx Request Error
| Error Code | Error Name | Description |
|-------|-------|------|
| 10001 | Bad Request | Invalid action request |
| 10002 | Unsupported Action | Unsupported action request |
| 10003 | Bad Param | Invalid action request parameter |
| 10004 | Unsupported Param | Unsupported action request parameter |
| 10005 | Unsupported Segment | Unsupported message segment type |
| 10006 | Bad Segment Data | Invalid message segment parameter |
| 10007 | Unsupported Segment Data | Unsupported message segment parameter |
| 10101 | Who Am I | Robot account not specified |
| 10102 | Unknown Self | Unknown robot account |

#### 2xxxx Handler Error
| Error Code | Error Name | Description |
|-------|-------|------|
| 20001 | Bad Handler | Action handler implementation error |
| 20002 | Internal Handler Error | Exception thrown during action handler runtime |

#### 3xxxx Execution Error
| Error Code Range | Error Type | Description |
|-----------|---------|------|
| 31xxx | Database Error | Database error |
| 32xxx | Filesystem Error | File system error |
| 33xxx | Network Error | Network error |
| 34xxx | Platform Error | Robot platform error |
| 35xxx | Logic Error | Action logic error |
| 36xxx | I Am Tired | Implementation decided to strike |

#### Reserved Error Ranges
- 4xxxx, 5xxxx: Reserved ranges, should not be used
- 6xxxx–9xxxx: Other error ranges, for custom implementation use

## 4. Implementation Requirements
1. All responses must include the status, retcode, data, and message fields.
2. When the request contains a non-empty echo field, the response must include an echo field with the same value.
3. Return codes must strictly follow the OneBot12 specification.
4. Error messages (message) should be human-readable descriptions.

## 5. Extension Specifications

ErisPulse extends the OneBot12 standard return structure as follows:

### 5.1 `message_id` Required Field

In the OneBot12 standard, `message_id` is located inside the `data` object and is not mandatory. ErisPulse elevates it to a **required** top-level field:

- If `message_id` cannot be obtained, it should be set to an empty string `""`
- Ensure `message_id` is always present, so modules do not need to perform null checks

### 5.2 `{platform}_raw` Raw Response Field

The return value should include the `{platform}_raw` field, which stores a complete deep copy of the raw response data from the platform:

```json
{
    "status": "ok",
    "retcode": 0,
    "data": {"message_id": "1234", "time": 1632847927},
    "message_id": "1234",
    "message": "",
    "telegram_raw": {
        "ok": true,
        "result": {"message_id": 1234, "date": 1632847927, ...}
    }
}
```

**Requirements**:
- `{platform}_raw` must be a deep copy of the original response, not a reference
- `platform` must exactly match the platform name registered by the adapter (case-sensitive)
- Error information from the original response should also be retained for debugging purposes

### 5.3 Framework Extension Return Codes (Custom Low Three Digits in the 34xxx Platform Error Segment)

The OneBot12 specification allows implementations to define custom low three digits in `3xxxx`. The `34xxx` segment is semantically defined as **Platform Error** (robot platform errors, such as failures caused by platform restrictions). Within `34xxx`, the low three digits are used hierarchically based on responsibility:

| Low Three Digits Segment | Responsibility | Purpose |
|-------------------------|----------------|---------|
| `340xx` | Adapter Implementation | Request operation family (Request Not Found / Already Handled / Not Supported / Permission Denied, see request-action-spec §7) |
| `341xx`～`345xx` | Adapter Implementation | Platform-side permission / risk control / account restrictions (implement custom low three digits, original error in `{platform}_raw`) |
| `346xx` | **ErisPulse Framework (Reserved)** | Framework-level interception and generic failures; adapters/modules should not use these codes |
| `347xx`～`349xx` | Adapter Implementation | Other platform execution errors |

ErisPulse framework currently uses the `346xx` codes:

| Error Code | Error Name | Description |
|------------|------------|-------------|
| 34600 | SDK Failure | Framework-level generic failure (default return code for `make_error()`) |
| 34601 | Action Denied | Outbound action is disabled by the control plane (`scope.actions`), call not initiated, directly return this response |

> Responsibility distinction: `34601` is **framework-level interception before the call** (module does not have permission to initiate the action); `34004` / `34xxx` platform codes are **actions already sent but rejected by the platform** (e.g., Bot lacks permissions, blocked by risk control). When modules check for permission issues, they should check both types: first check `34601` (module itself is disabled by scope), then check `34xxx` (platform-side restrictions).

The return structure follows the standard failure response in §2:

```json
{
    "status": "failed",
    "retcode": 34601,
    "data": null,
    "message_id": "",
    "message": "action 'send' denied by scope.actions"
}
```

### 5.4 Adapter Implementation Checklist

- [ ] Include `status`, `retcode`, `data`, `message_id`, `message` fields
- [ ] Return codes follow the OneBot12 specification (see §3.2)
- [ ] `message_id` is always present (set to empty string if unavailable)
- [ ] `{platform}_raw` contains the raw response data from the platform

## 6. Notes
- For error codes in the 3xxxx range, the last three digits can be defined by the implementation.
- Avoid using reserved error ranges (4xxxx, 5xxxx).
- **`34600` / `34601` are reserved error codes for the ErisPulse framework** (see §5.3); adapters/modules should avoid using them.
- Error messages should be concise and clear for debugging purposes.