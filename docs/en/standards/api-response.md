# ErisPulse Adapter Standard Return Specification

> [!TIP]
> **When to read this**: When implementing `call_api` / Send / Request in your adapter, you need to confirm that the response structure and return codes conform to the ErisPulse standard, or when troubleshooting the meaning of a specific `retcode`. Otherwise, you can skip this.

## 1. Explanation
Why does this specification exist?

To ensure consistency of the response structure for sending interfaces across platforms and compatibility with OneBot12, ErisPulse adapters adopt the message sending response structure standard defined by OneBot12.

However, ErisPulse's protocol has some special definitions:
- 1. In the basic fields, `message_id` is required, but it is not present in the OneBot12 standard.
- 2. The response content must include a `{platform_name}_raw` field to store the raw response data.

## 2. Basic Return Structure
All action responses must include the following basic fields:

| Field Name | Data Type | Required | Description |
|-------|---------|------|------|
| status | string | Yes | Execution status, must be "ok" or "failed" |
| retcode | int64 | Yes | Return code, follows OneBot12 return code rules |
| data | any | Yes | Response data, contains the request result on success, null on failure |
| message_id | string | Yes | Message ID, used to identify the message, empty string if not available |
| message | string | Yes | Error message, empty string on success |
| {platform_name}_raw | any | No | Raw response data |

Optional fields:
| Field Name | Data Type | Required | Description |
|-------|---------|------|------|
| echo | string | No | If the request contains an echo field, it is returned unchanged |

## 3. Complete Field Specification

### 3.1 General Fields

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
| 20002 | Internal Handler Error | Action handler runtime exception |

#### 3xxxx Execution Error
| Error Code Range | Error Type | Description |
|-----------|---------|------|
| 31xxx | Database Error | Database error |
| 32xxx | Filesystem Error | Filesystem error |
| 33xxx | Network Error | Network error |
| 34xxx | Platform Error | Robot platform error |
| 35xxx | Logic Error | Action logic error |
| 36xxx | I Am Tired | Implementation decides to strike |

#### Reserved Error Ranges
- 4xxxx, 5xxxx: Reserved ranges, should not be used
- 6xxxx–9xxxx: Other error ranges, for custom implementation use

## 4. Implementation Requirements
1. All responses must include `status`, `retcode`, `data`, and `message` fields
2. If the request contains a non-empty `echo` field, the response must include the same `echo` field value
3. Return codes must strictly follow the OneBot12 specification
4. Error messages (`message`) should be human-readable descriptions

### 4.1 Response Construction Helper: `make_response` / `make_error`

Adapters should use the two helpers on `BaseAdapter` to construct standard responses, without manually writing dictionaries:

```python
# Success (for send / call_api / _do_accept and all other standard response return locations)
return self.make_response(
    data=result,                    # Response data
    message_id=result.get("message_id", ""),
    raw=result,                     # Platform raw response → automatically attached to {platform}_raw field
)

# Failure (status fixed to "failed")
return self.make_error(
    retcode=34100,                  # Default 34600 (SDK Failure); platform errors should use custom 34xxx
    message="Platform risk control rejected",
    raw=response,
)
```

| Helper | Signature | Semantics |
|------|------|------|
| `make_response` | `(*, status="ok", retcode=0, data=None, message_id="", message="", raw=None)` | Assembles standard structure; if `raw` is not None, automatically attaches the `{platform}_raw` key (platform name taken from `self._platform`) |
| `make_error` | `(retcode=34600, message="", raw=None)` | Shortcut for `make_response(status="failed", ...)` |

> Manually writing equivalent dictionaries is also valid (as long as the structure is consistent); the value of helpers is in automatically attaching `{platform}_raw` with the correct platform name and ensuring field completeness.

## 5. Extension Specifications

ErisPulse extends the OneBot12 standard return structure as follows:

### 5.1 `message_id` Required Field

In the OneBot12 standard, `message_id` is located inside the `data` object and is not mandatory. ErisPulse elevates it to a required top-level field:

- When `message_id` cannot be obtained, it should be set to an empty string `""`
- Ensure `message_id` always exists; modules do not need to check for null

> **Note the distinction**: This section's top-level elevation applies only to **action responses** (outbound). For inbound message **events**, `message_id` is a required top-level field in the OneBot12 baseline, see [Event Conversion Standard](event-conversion.md).

### 5.2 `{platform}_raw` Raw Response Field

The response should include a `{platform}_raw` field to store a complete copy of the platform's raw response data:

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
- `{platform}_raw` must be a deep copy of the raw response, not a reference
- `platform` must exactly match the platform name registered with the adapter (case-sensitive)
- Error information from the raw response should also be retained for debugging

### 5.3 Framework Extension Return Codes (Customization of Last Three Digits in 34xxx Platform Error Segment)

OneBot12 specification allows custom implementation of the last three digits of `3xxxx`. `34xxx` semantics are **Platform Error** (robot platform error, e.g., platform restrictions causing failure). Within `34xxx`, the last three digits are used in a layered manner by responsibility:

| Last Three Digits | Responsibility | Purpose |
|---------|------|------|
| `340xx` | Adapter Implementation | Request operation group (Request Not Found / Already Handled / Not Supported / Permission Denied, see request-action-spec §7) |
| `341xx`–`345xx` | Adapter Implementation | Platform-side permission / risk control / account restriction errors (custom low three digits, original error in `{platform}_raw`) |
| `346xx` | **ErisPulse Framework (Reserved)** | Framework-level interception and general failure; adapters/modules should not use |
| `347xx`–`349xx` | Adapter Implementation | Other platform execution errors |

ErisPulse framework currently uses `346xx` codes:

| Error Code | Error Name | Description |
|-------|-------|------|
| 34600 | SDK Failure | Framework general failure (default return code for `make_error()`) |
| 34601 | Action Denied | Outbound action denied by scope.actions, call not initiated, directly return this response |

> Responsibility distinction: `34601` is **framework-level interception before call** (module is not qualified to initiate the action); `34004` / `34xxx` platform codes are **actions already sent but rejected by the platform** (e.g., Bot lacks permission, is blocked by risk control). Modules should check both types of errors when handling permission issues: first check `34601` (module is disabled by scope), then check `34xxx` (platform-side restrictions).

The return structure is the standard failure response from §2:

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
- [ ] `message_id` always exists (empty string if unavailable)
- [ ] `{platform}_raw` contains platform raw response data

## 6. Notes
- For `3xxxx` error codes, the last three digits can be defined by the implementation
- Avoid using reserved error ranges (4xxxx, 5xxxx)
- **`34600` / `34601` are reserved by the ErisPulse framework** (see §5.3), adapters/modules should avoid using them
- Error messages should be concise and clear for debugging

---

## Next Steps

- **Implement DSL return values with corresponding checks**: [API Action Standard](api-action-spec.md) (standard action's `data` field), [Request Action Specification](request-action-spec.md) (request operation's 34001-34004 extension), [Send Method Specification](send-method-spec.md) (degraded semantics for send failures)
- **Troubleshoot permission-related failures**: First check `34601` (module disabled by scope, framework intercepts before call, see §5.3), then check `34xxx` (action sent but rejected by platform side)