# ErisPulse Request Operation Specification

This document defines the standardized specification for request event operations in the ErisPulse adapter, including field requirements for request events, usage of the Request DSL, and adapter implementation requirements.

## 1. Overview

The request event (`type: "request"`) is a special event type defined in the OneBot12 standard, representing requests that require the Bot to make a decision (such as friend requests or group invitations).

Unlike message events, request events require **bidirectional interaction**:
1. **Receiving**: The adapter converts the platform-native request into a standard request event
2. **Responding**: The module executes operations via the `Request` DSL or `Event.approve()`/`Event.reject()`

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
    │       ├─→ event.approve()     ← Approve the request
    │       └─→ event.reject()      ← Reject the request
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
    └─→ Or directly through adapter operations
            await adapter.Request("req_id").accept()
```

## 2. Request Event Field Requirements

### 2.1 Standard Fields

The request event must include OneBot12 standard fields and the following additional fields:

| Field | Type | Required | Description |
|------|------|------|------|
| `request_id` | string | **Strongly recommended** | Request identifier, used for approve/reject operations |
| `user_id` | string | Yes | ID of the request initiator |
| `user_nickname` | string | No | Nickname of the request initiator |
| `comment` | string | No | Request comment |

### 2.2 `request_id` Field

`request_id` is the core identifier for request operations:

- **Purpose**: Identifies an actionable request, used by the `Request` DSL
- **Generation Rules**:
  - Prefer using the platform-native request identifier (e.g., OneBot11's `flag` field, Telegram's `chat_invite_link`, etc.)
  - If the platform lacks a native request ID, the adapter should generate a unique identifier (recommended format: `{platform}_{timestamp}_{user_id}`)
- **Uniqueness**: Should be unique within the same platform
- **Missing Behavior**: When `request_id` is missing, `event.approve()` / `event.reject()` will raise a `ValueError`

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

### 3.1 Chainable Calls

`Request` provides a chainable API similar to `Send`:

```python
# Basic usage
await adapter.Request("req_id").accept()
await adapter.Request("req_id").reject()

# Specify Bot account
await adapter.Request("req_id").Using("bot1").accept()

# Include comment (via kwargs)
await adapter.Request("req_id").accept(comment="Welcome")
await adapter.Request("req_id").reject(comment="Not adding for now")

# Combined usage
await adapter.Request("req_id").Using("bot1").accept(comment="Welcome")
```

### 3.2 Method List

| Method | Description | Return Value |
|------|------|--------|
| `Using(account_id)` | Specify the Bot account for the operation | `RequestDSL` (supports chainable calls) |
| `accept(**kwargs)` | Approve the request | `asyncio.Task` (await returns standard response) |
| `reject(**kwargs)` | Reject the request | `asyncio.Task` (await returns standard response) |

### 3.3 Return Value Format

The operation returns a standard API response format:

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
    "message": "Request expired or does not exist"
}
```

**Not Implemented** (adapter did not override `accept`/`reject`):
```json
{
    "status": "failed",
    "retcode": 10002,
    "data": null,
    "message_id": "",
    "message": "Platform MyAdapter has not implemented request operation (accept)"
}
```

## 4. Event Convenience Methods

The `Event` wrapper class provides convenient methods suitable for use in request event handlers:

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
    # result = await event.reject(comment="Not adding as friend for now")
    
    # Check result
    if result.get("status") == "ok":
        print("Operation successful")
    else:
        print(f"Operation failed: {result.get('message')}")
```

### 4.1 Event Method List

| Method | Description | Return Value |
|------|------|--------|
| `get_request_id()` | Get request ID | `str` |
| `approve(comment=None)` | Approve current request event | Standard response format |
| `reject(comment=None)` | Reject current request event | Standard response format |

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
        "request_id": self._extract_request_id(raw_event),  # ← Key field
        f"{self._platform_name}_raw": raw_event,
        f"{self._platform_name}_raw_type": raw_event.get("type", ""),
    }

def _extract_request_id(self, raw_event: dict) -> str:
    """
    Extract request ID from platform-native event
    
    Prefer using platform-native request identifier, or generate a unique ID if none exists
    """
    # Prefer using platform-native ID
    if flag := raw_event.get("flag"):
        return str(flag)
    if request_key := raw_event.get("request_key"):
        return str(request_key)
    
    # Fallback: Generate unique ID
    import hashlib
    raw = f"{self._platform_name}_{raw_event.get('user_id')}_{raw_event.get('timestamp')}"
    return hashlib.md5(raw.encode()).hexdigest()
```

### 5.2 Request Internal Class Implementation

The adapter implements `accept` and `reject` in the `Request` internal class:

```python
from ErisPulse.Core import BaseAdapter, RequestDSL

class MyAdapter(BaseAdapter):
    
    class Request(RequestDSL):
        """MyPlatform request operation implementation"""
        
        def accept(self, **kwargs):
            """
            Approve request
            
            :param kwargs: Additional parameters, e.g., comment="remark"
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

### 5.3 Platform Does Not Support Request Operations

If the platform does not support friend requests or group invitations (e.g., some platforms automatically handle requests), the adapter can:

1. **Do not override `Request` internal class**: Use the base class default implementation, calling `accept()`/`reject()` returns `retcode=10002`
2. **Skip `request_id` generation during conversion**: Do not generate `request_id`, let `event.approve()` raise `ValueError`
3. **Log warnings**: Record warnings in `accept`/`reject` and return appropriate error codes

### 5.4 Summary: Send and Request in Parallel

The adapter has two parallel DSL internal classes, each with its own responsibilities:

```
BaseAdapter
├── Send(SendDSL)     ← Message sending
│   ├── Raw_ob12()    ← Must be implemented
│   ├── Text()        ← Recommended implementation
│   └── Image()       ← Implemented as needed
│
└── Request(RequestDSL) ← Request operations
    ├── accept()        ← Implemented as needed
    └── reject()        ← Implemented as needed
```

### 5.5 Adapter `__init__` Considerations

When overriding the `Request` internal class's `__init__`, you must pass through parameters and call `super().__init__()`, see [Adapter Development Guide - `__init__` Considerations](../developer-guide/adapters/getting-started.md#init-注意事项) (`Request` is similar, parameters are `adapter, request_id, account_id`).

## 6. Adapter Implementation Checklist

### Basic Requirements
- [ ] If `__init__` is overridden, `super().__init__()` has been called (to ensure Send/Request factory initialization)

### Request Event Conversion
- [ ] Request event includes the `request_id` field (strongly recommended)
- [ ] `detail_type` correctly maps to `"friend"` or `"group"`
- [ ] Platform-native data is preserved in the `{platform}_raw` field
- [ ] `request_id` generation rules are documented

### Request Operations
- [ ] `Request` internal class is implemented (if the platform supports request operations)
- [ ] `accept()` method is implemented
- [ ] `reject()` method is implemented
- [ ] Operation returns standard API response format
- [ ] Operations not supported return `retcode=10002`
- [ ] Network errors return `retcode=33xxx` (following API response standards)

## 7. Error Code Extension

For **adapter implementation layer** related to request operations, the following recommended error codes are suggested (following [API Response Standard](api-response.md) §3.2, falling within the `34xxx` platform error segment's lower three digits for custom use):

| Error Code | Error Name | Description |
|-------|-------|------|
| 34001 | Request Not Found | Request does not exist or has expired |
| 34002 | Request Already Handled | Request has already been handled |
| 34003 | Request Not Supported | Platform does not support this type of request operation |
| 34004 | Permission Denied | Bot does not have permission to handle this request (returned by platform) |

> **Boundary with Framework Codes**: The above `340xx` are **platform/adapter**-returned request handling failures; when the ErisPulse framework disables a module's request action in `scope.actions`, it **directly returns `34601` (Action Denied)** before calling the adapter (see [API Response Standard §5.3](api-response.md#53-framework-extended-return-codes-34xxx-custom-use-in-the-lower-three-digits-of-the-platform-error-segment)), and the two are not substitutes: first pass the `34601` framework gate, then fall back to the platform layer `340xx` errors.

## 8. Related Documentation

- [Event Conversion Standard](event-conversion.md) - Complete event conversion specification
- [API Response Standard](api-response.md) - Standard format for adapter API responses
- [Send Method Specification](send-method-spec.md) - Naming and parameter conventions for Send class methods
- [Session Type Standard](session-types.md) - Definition and mapping of session types