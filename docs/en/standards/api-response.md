# ErisPulse Adapter Standardized Return Specification

## 1. Description
Why is this specification here?

To ensure consistency in return interfaces across platforms and OneBot12 compatibility, the ErisPulse adapter adopts the OneBot12-defined message sending return structure standard for API response formats.

However, the ErisPulse protocol has some specific definitions:
- 1. In basic fields, `message_id` is mandatory, but it does not exist in the OneBot12 standard.
- 2. The return content needs to add a `{platform_name}_raw` field to store raw response data.

## 2. Basic Return Structure
All action responses must include the following basic fields:

| Field Name | Data Type | Required | Description |
|-------|---------|------|------|
| status | string | Yes | Execution status, must be "ok" or "failed" |
| retcode | int64 | Yes | Return code, follows OneBot12 return code rules |
| data | any | Yes | Response data, contains request result when successful, null when failed |
| message_id | string | Yes | Message ID, used to identify the message, empty string if none |
| message | string | Yes | Error message, empty string when successful |
| {platform_name}_raw | any | No | Raw response data |

Optional Fields:
| Field Name | Data Type | Required | Description |
|-------|---------|------|------|
| echo | string | No | When the request contains an echo field, return it unchanged |

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

#### 1xxxx Action Request Errors (Request Error)
| Error Code | Error Name | Description |
|-------|-------|------|
| 10001 | Bad Request | Invalid action request |
| 10002 | Unsupported Action | Unsupported action request |
| 10003 | Bad Param | Invalid action request parameters |
| 10004 | Unsupported Param | Unsupported action request parameters |
| 10005 | Unsupported Segment | Unsupported message segment type |
| 10006 | Bad Segment Data | Invalid message segment parameters |
| 10007 | Unsupported Segment Data | Unsupported message segment parameters |
| 10101 | Who Am I | Bot account not specified |
| 10102 | Unknown Self | Unknown bot account |

#### 2xxxx Action Handler Errors (Handler Error)
| Error Code | Error Name | Description |
|-------|-------|------|
| 20001 | Bad Handler | Action handler implementation error |
| 20002 | Internal Handler Error | Exception thrown by action handler runtime |

#### 3xxxx Action Execution Errors (Execution Error)
| Error Code Range | Error Type | Description |
|-----------|---------|------|
| 31xxx | Database Error | Database error |
| 32xxx | Filesystem Error | Filesystem error |
| 33xxx | Network Error | Network error |
| 34xxx | Platform Error | Bot platform error |
| 35xxx | Logic Error | Action logic error |
| 36xxx | I Am Tired | Implementation decided to go on strike |

#### Reserved Error Ranges
- 4xxxx, 5xxxx: Reserved segments, should not be used
- 6xxxx~9xxxx: Other error segments, available for implementation custom use

## 4. Implementation Requirements
1. All responses must include status, retcode, data, and message fields
2. When the request contains a non-empty echo field, the response must include an echo field with the same value
3. Return codes must strictly follow OneBot12 specification
4. Error messages (message) should be human-readable descriptions

## 5. Extended Specifications

ErisPulse makes the following extensions on top of the OneBot12 standard return structure:

### 5.1 `message_id` Mandatory Field

In the OneBot12 standard, `message_id` is inside the `data` object and is not mandatory. ErisPulse elevates it to a top-level **mandatory** field:

- Should be set to an empty string `""` when `message_id` cannot be obtained
- Ensure `message_id` always exists, modules do not need to perform null checks

### 5.2 `{platform}_raw` Raw Response Field

The return value should include a `{platform}_raw` field, containing a complete copy of the platform's raw response data:

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
- `platform` must match the platform name used during adapter registration exactly (case-sensitive)
- Error messages within the raw response should also be preserved to facilitate debugging

### 5.3 Adapter Implementation Checklist

- [ ] Include `status`, `retcode`, `data`, `message_id`, `message` fields
- [ ] Return codes follow OneBot12 specification (see §3.2)
- [ ] `message_id` always exists (empty string if unable to obtain)
- [ ] `{platform}_raw` contains platform raw response data

## 6. Notes
- For 3xxxx error codes, the last three digits can be defined by the implementation
- Avoid using reserved error segments (4xxxx, 5xxxx)
- Error messages should be concise and clear for debugging