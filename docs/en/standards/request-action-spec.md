# ErisPulse Request Operation Specification

This document defines the standardized specification for request event operations in the ErisPulse adapter, including field requirements for request events, usage of the Request DSL, and adapter implementation requirements.

## 1. Overview

Request events (`type: "request"`) are special event types defined in the OneBot12 standard, representing requests that require the Bot to make decisions (such as friend requests, group invitations, etc.).

Unlike message events, request events require **bidirectional interaction**:
1. **Receiving**: The adapter converts platform-native requests into standard request events
2. **Responding**: The module performs operations through the `Request` DSL or `Event.approve()`/`Event.reject()`

```
Platform-native request event
    │
    ▼
Converter.convert()        ← Adapter implementation (forward conversion)
    │
    ▼
Standard request event (with request_id)
    │
    ├─→ Module handler @request.on_friend_request()
    │       │
    │       ├─→ event.approve()     ← Approve request
    │       └─→ event.reject()      ← Reject request
    │               │
    │               ▼
    │       adapter.Request(request_id).accept()
    │               │
    │               ▼
    │       BaseAdapter.Request.accept()  ← Adapter override
    │               │
    │               ▼
    │       Platform API call
    │
    └─→ Or direct adapter operation
            await adapter.Request("req_id").accept()
```

## 2. Request Event Field Requirements

### 2.1 Standard Fields

In addition to the required OneBot12 standard fields, request events must include the following fields:

| Field | Type | Required | Description |
|------|------|----------|-------------|
| `request_id` | string | **Strongly Recommended** | Request identifier for approve/reject operations |
| `user_id` | string | Yes | Request initiator ID |
| `user_nickname` | string | No | Request initiator nickname |
| `comment` | string | No | Request message/comment |

### 2.2 `request_id` Field

The `request_id` is the core identifier for request operations:

- **Purpose**: Identifies an actionable request for use with the `Request` DSL
- **Generation Rules**:
  - Prefer platform-native request identifiers (e.g., OneBot11's `flag` field, Telegram's `chat_invite_link`, etc.)
  - If the platform has no native request ID, the adapter should generate a unique identifier (recommended format: `{platform}_{timestamp}_{user_id}`)
- **Uniqueness**: Should remain unique within the same platform scope
- **Missing Behavior**: When `request_id` is missing, `event.approve()` / `event.reject()` will raise `ValueError`

### 2.3 Request Event Example

```json
{
  "id": "evt_123456",
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
  "comment": "Please add me as a friend",
  "request_id": "flag_abc123",
  "onebot11_raw": {...},
  "onebot11_raw_type": "request"
}
```

## 3. Request DSL

### 3.1 Chained Calls

`Request` provides a chained call interface consistent with the `Send` style:

```python
# Basic usage
await adapter.Request("req_id").accept()
await adapter.Request("req_id").reject()

# Specify bot account
await adapter.Request("req_id").Using("bot1").accept()

# Include comment (via kwargs)
await adapter.Request("req_id").accept(comment="Welcome")
await adapter.Request("req_id").reject(comment="Not adding at this time")

# Combined usage
await adapter.Request("req_id").Using("bot1").accept(comment="Welcome")
```

### 3.2 Method List

| Method | Description | Return Value |
|--------|-------------|--------------|
| `Using(account_id)` | Specify the bot account for operation | `RequestDSL` (supports chaining) |
| `accept(**kwargs)` | Approve request | `asyncio.Task` (returns standard response after awaiting) |
| `reject(**kwargs)` | Reject request | `asyncio.Task` (returns standard response after awaiting) |

### 3.3 Return Value Format

Operations return standard API response format:

**Success**:
```json
{
    "status": "ok",
    "retcode": 0,
    "data": null,
    "message_id": "",
    "message": ""
}
```

**Failure**:
```json
{
    "status": "failed",
    "retcode": 34001,
    "data": null,
    "message_id": "",
    "message": "Request expired or not found"
}
```

**Not Implemented** (adapter hasn't overridden `accept`/`reject`):
```json
{
    "status": "failed",
    "retcode": 10002,
    "data": null,
    "message_id": "",
    "message": "Platform MyAdapter has not implemented request operations (accept)"
}
```

## 4. Event Convenience Methods

The `Event` wrapper class provides convenience methods suitable for use in request event handlers:

```python
from ErisPulse.Core.Event import request

@request.on_friend_request()
async def handle_friend_request(event):
    # Check request ID
    request_id = event.get_request_id()
    if not request_id:
        print("Warning: Request event missing request_id")
        return
    
    # Approve request
    result = await event.approve()
    
    # Or reject request
    # result = await event.reject(comment="Not adding friends at this time")
    
    # Check result
    if result.get("status") == "ok":
        print("Operation successful")
    else:
        print(f"Operation failed: {result.get('message')}")
```

### 4.1 Event Method List

| Method | Description | Return Value |
|--------|-------------|--------------|
| `get_request_id()` | Get request ID | `str` |
| `approve(comment=None)` | Approve the current request event | Standard response format |
| `reject(comment=None)` | Reject the current request event | Standard response format |

## 5. Adapter Implementation Requirements

### 5.1 Converter Requirements

The adapter's converter must correctly set the `request_id` field when converting request events:

```python
def convert_request_event(self, raw_event: dict) -> dict:
    """Convert platform-native request event"""
    return {
        "id": self._generate_event_id(raw_event),
        "time": int(time.time()),
        "type": "request",
        "detail_type": self._map_request_type(raw_event),  # "friend" or "group"
        "platform": self._platform_name,
        "self": {
            "platform": self._platform_name,
            "user_id": str(self._bot_id),
        },
        "user_id": str(raw_event.get("user_id", "")),
        "user_nickname": raw_event.get("nickname", ""),
        "comment": raw_event.get("message", ""),
        "request_id": self._extract_request_id(raw_event),  # ← Critical field
        f"{self._platform_name}_raw": raw_event,
        f"{self._platform_name}_raw_type": raw_event.get("type", ""),
    }

def _extract_request_id(self, raw_event: dict) -> str:
    """
    Extract request ID from platform-native event
    
    Prefer platform-native request identifiers, generate unique ID if none available
    """
    # Prefer platform-native ID
    if flag := raw_event.get("flag"):
        return str(flag)
    if request_key := raw_event.get("request_key"):
        return str(request_key)
    
    # Fallback: Generate unique ID
    import hashlib
    raw = f"{self._platform_name}_{raw_event.get('user_id')}_{raw_event.get('timestamp')}"
    return hashlib.md5(raw.encode()).hexdigest()
```

### 5.2 Request Inner Class Implementation

Adapters can override `accept` and `reject` in the `Request` inner class:

```python
from ErisPulse.Core import BaseAdapter, RequestDSL

class MyAdapter(BaseAdapter):
    
    class Request(RequestDSL):
        """MyPlatform request operation implementation"""
        
        def accept(self, **kwargs):
            """
            Approve request
            
            :param kwargs: Extended parameters, e.g., comment="Note"
            :return: asyncio.Task
            """
            async def _do():
                try:
                    result = await self._adapter.call_api(
                        endpoint="/set_request",
                        request_id=self._request_id,
                        approve=True,
                        **kwargs,
                    )
                    return {
                        "status": "ok" if result.get("code") == 0 else "failed",
                        "retcode": result.get("code", 0),
                        "data": None,
                        "message_id": "",
                        "message": result.get("message", ""),
                    }
                except Exception as e:
                    return {
                        "status": "failed",
                        "retcode": 34001,
                        "data": None,
                        "message_id": "",
                        "message": f"Request operation failed: {e}",
                    }
            
            return self._create_task(_do())
        
        def reject(self, **kwargs):
            """Reject request"""
            async def _do():
                try:
                    result = await self._adapter.call_api(
                        endpoint="/set_request",
                        request_id=self._request_id,
                        approve=False,
                        **kwargs,
                    )
                    return {
                        "status": "ok" if result.get("code") == 0 else "failed",
                        "retcode": result.get("code", 0),
                        "data": None,
                        "message_id": "",
                        "message": result.get("message", ""),
                    }
                except Exception as e:
                    return {
                        "status": "failed",
                        "retcode": 34001,
                        "data": None,
                        "message_id": "",
                        "message": f"Request operation failed: {e}",
                    }
            
            return self._create_task(_do())
```

### 5.3 Platforms Without Request Operations

If the platform itself doesn't support friend requests/group invitation operations (some platforms auto-process requests), the adapter can:

1. **Not override the `Request` inner class**: Use the base class default implementation, returning `retcode=10002` when calling `accept()`/`reject()`
2. **Skip `request_id` during conversion**: Don't generate `request_id`, let `event.approve()` raise `ValueError`
3. **Log warnings**: Record warnings in `accept`/`reject` and return appropriate error codes

### 5.4 Summary: Send and Request in Parallel

The adapter has two parallel DSL inner classes, each with its own responsibilities:

```
BaseAdapter
├── Send(SendDSL)     ← Message sending
│   ├── Raw_ob12()    ← Must implement
│   ├── Text()        ← Recommended implementation
│   └── Image()       ← Implement as needed
│
└── Request(RequestDSL) ← Request operations
    ├── accept()        ← Implement as needed
    └── reject()        ← Implement as needed
```

### 5.5 Adapter `__init__` Considerations

When overriding the `__init__` of the `Request` inner class, you must pass through parameters and call `super().__init__()`, see [Getting Started with Adapter Development - `__init__` Considerations](../../developer-guide/adapters/getting-started.md#init-considerations) (same applies to `Request`, parameters are `adapter, request_id, account_id`).

## 6. Adapter Implementation Checklist

### Basic Requirements
- [ ] If `__init__` is overridden, `super().__init__()` has been called (ensuring Send / Request factory initialization)

### Request Event Conversion
- [ ] Request event includes `request_id` field (strongly recommended)
- [ ] `detail_type` correctly maps to `"friend"` or `"group"`
- [ ] Platform raw data is preserved in `{platform}_raw` field
- [ ] `request_id` generation rules are documented

### Request Operations
- [ ] `Request` inner class is implemented (if platform supports request operations)
- [ ] `accept()` method is implemented
- [ ] `reject()` method is implemented
- [ ] Operations return standard API response format
- [ ] Unsupported operations return `retcode=10002`
- [ ] Network errors return `retcode=33xxx` (following API response standards)

## 7. Error Code Extensions

Recommended error codes for request operations (following [API Response Standards](api-response.md) §3.2):

| Error Code | Error Name | Description |
|------------|------------|-------------|
| 34001 | Request Not Found | Request doesn't exist or has expired |
| 34002 | Request Already Handled | Request has already been processed |
| 34003 | Request Not Supported | Platform doesn't support this type of request operation |
| 34004 | Permission Denied | Bot has no permission to handle this request |

## 8. Related Documentation

- [Event Conversion Standards](event-conversion.md) - Complete event conversion specification
- [API Response Standards](api-response.md) - Adapter API response format standards
- [Send Method Specification](send-method-spec.md) - Send class method naming and parameter specifications
- [Session Type Standards](session-types.md) - Session type definitions and mapping relationships