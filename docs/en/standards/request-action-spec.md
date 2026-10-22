# ErisPulse Request Operation Specification

> [!TIP]
> **When to read this**: When your adapter needs to handle friend requests/group invitations (converting request events, implementing `accept`/`reject`), or when your module needs to use `event.approve()` / `event.reject()` to approve requests, refer to this document. Otherwise, skip it.

This document defines the standardized specification for request event operations in ErisPulse adapters, including field requirements for request events, usage of the Request DSL, and adapter implementation requirements.

## 1. Overview

Request events (`type: "request"`) are a special event type defined in the OneBot12 standard, representing requests that require the Bot to make a decision (such as friend requests, group invitations, etc.).

Unlike message events, request events require **two-way interaction**:
1. **Receiving**: The adapter converts platform-native requests into standard request events
2. **Responding**: Modules perform operations via the `Request` DSL or `Event.approve()`/`Event.reject()`

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
    └─→ Or operate directly through the adapter
            await adapter.Request("req_id").accept()
```

## 2. Request Event Field Requirements

### 2.1 Standard Fields

In addition to the required OneBot12 standard fields, request events must include the following fields:

| Field | Type | Required | Description |
|------|------|------|------|
| `request_id` | string | **Strongly recommended** | Request identifier, used for accept/reject operations |
| `user_id` | string | Yes | ID of the requester |
| `user_nickname` | string | No | Nickname of the requester |
| `comment` | string | No | Message attached to the request |

### 2.2 The `request_id` Field

`request_id` is the core identifier for request operations:

- **Purpose**: Identifies an operable request, used by the `Request` DSL
- **Generation rules**:
  - Prefer the platform's native request identifier (e.g., OneBot11's `flag` field, Telegram's `chat_invite_link`, etc.)
  - If the platform has no native request ID, the adapter should generate a unique identifier (suggested format: `{platform}_{timestamp}_{user_id}`)
- **Uniqueness**: Should remain unique within the same platform scope
- **Missing behavior**: When `request_id` is missing, `event.approve()` / `event.reject()` will raise `ValueError`

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

# Specify a Bot account
await adapter.Request("req_id").Using("bot1").accept()

# With a note (via kwargs)
await adapter.Request("req_id").accept(comment="Welcome")
await adapter.Request("req_id").reject(comment="Not adding for now")

# Combined usage
await adapter.Request("req_id").Using("bot1").accept(comment="Welcome")
```

### 3.2 Method List

| Method | Description | Return Value |
|------|------|--------|
| `Using(account_id)` | Specify the Bot account to perform the operation | `RequestDSL` (supports chaining) |
| `accept(**kwargs)` | Approve the request | `asyncio.Task` (returns the standard response after await) |
| `reject(**kwargs)` | Reject the request | `asyncio.Task` (returns the standard response after await) |

### 3.3 Return Value Format

Operations return the standard API response format:

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
    "message": "The request has expired or does not exist"
}
```

**Not implemented** (adapter does not override `accept`/`reject`):
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
    # Check the request ID
    request_id = event.get_request_id()
    if not request_id:
        print("Warning: request event is missing request_id")
        return
    
    # Approve the request
    result = await event.approve()
    
    # Or reject the request
    # result = await event.reject(comment="Not adding friends for now")
    
    # Check the result
    if result.get("status") == "ok":
        print("Operation succeeded")
    else:
        print(f"Operation failed: {result.get('message')}")
```

### 4.1 Event Method List

| Method | Description | Return Value |
|------|------|--------|
| `get_request_id()` | Get the request ID | `str` |
| `approve(comment=None)` | Approve the current request event | Standard response format |
| `reject(comment=None)` | Reject the current request event | Standard response format |

## 5. Adapter Implementation Requirements

### 5.1 Converter Requirements

When converting request events, the adapter's converter **must** correctly set the `request_id` field:

```python
def convert_request_event(self, raw_event: dict) -> dict:
    """Convert a platform-native request event"""
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
    Extract the request ID from a platform-native event
    
    Prefer the platform's native request identifier; generate a unique ID if unavailable
    """
    # Prefer the platform's native ID
    if flag := raw_event.get("flag"):
        return str(flag)
    if request_key := raw_event.get("request_key"):
        return str(request_key)
    
    # Fallback: generate a unique ID
    import hashlib
    raw = f"{self._platform_name}_{raw_event.get('user_id')}_{raw_event.get('timestamp')}"
    return hashlib.md5(raw.encode()).hexdigest()
```

### 5.2 Request Inner Class Implementation

The adapter only needs to override `accept` and `reject` in the `Request` inner class:

```python
from ErisPulse.Core import BaseAdapter, RequestDSL

class MyAdapter(BaseAdapter):
    
    class Request(RequestDSL):
        """MyPlatform request operation implementation"""
        
        def accept(self, **kwargs):
            """
            Approve the request
            
            :param kwargs: Extended parameters, e.g., comment="a note"
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
            """Reject the request"""
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

### 5.3 Platforms That Do Not Support Request Operations

If the platform itself does not support friend request/group invitation operations (e.g., some platforms handle requests automatically), the adapter can:

1. **Not override the `Request` inner class**: Use the base class's default implementation; calling `accept()`/`reject()` returns `retcode=10002`
2. **Skip `request_id` during conversion**: Do not generate `request_id`, letting `event.approve()` raise `ValueError`
3. **Log warnings**: Log a warning in `accept`/`reject` and return an appropriate error code

### 5.4 Summary: Send and Request in Parallel

The adapter has two parallel DSL inner classes, each with its own responsibility:

```
BaseAdapter
├── Send(SendDSL)     ← Message sending
│   ├── Raw_ob12()    ← Must be implemented
│   ├── Text()        ← Recommended to implement
│   └── Image()       ← Implement as needed
│
└── Request(RequestDSL) ← Request operations
    ├── accept()        ← Implement as needed
    └── reject()        ← Implement as needed
```

### 5.5 Adapter `__init__` Notes

When overriding the `__init__` of the `Request` inner class, you must pass through the parameters and call `super().__init__()`. See [Adapter Development Getting Started - `__init__` Notes](../developer-guide/adapters/getting-started.md#init-notes) (`Request` works the same way, with parameters `adapter, request_id, account_id`).

## 6. Adapter Implementation Checklist

### Basic Requirements
- [ ] If `__init__` is overridden, `super().__init__()` has been called (ensures Send / Request factory initialization)

### Request Event Conversion
- [ ] Request events include the `request_id` field (strongly recommended)
- [ ] `detail_type` is correctly mapped to `"friend"` or `"group"`
- [ ] Platform raw data is preserved in the `{platform}_raw` field
- [ ] The `request_id` generation rules are documented

### Request Operations
- [ ] The `Request` inner class is implemented (if the platform supports request operations)
- [ ] The `accept()` method is implemented
- [ ] The `reject()` method is implemented
- [ ] Operations return the standard API response format
- [ ] Unsupported operations return `retcode=10002`
- [ ] Network errors return `retcode=33xxx` (following the API response standard)

## 7. Error Code Extensions

Recommended error codes for the **adapter implementation layer** related to request operations (following the [API Response Standard](api-response.md) §3.2,
customized in the last three digits of the `34xxx` platform error range):

| Error Code | Error Name | Description |
|-------|-------|------|
| 34001 | Request Not Found | The request does not exist or has expired |
| 34002 | Request Already Handled | The request has already been handled |
| 34003 | Request Not Supported | The platform does not support this type of request operation |
| 34004 | Permission Denied | The Bot has no permission to handle this request (returned by the platform) |

> **Boundary with framework codes**: The `340xx` codes above are request handling failures returned by the **platform/adapter**;
> when the ErisPulse framework disables a module's request action via `scope.actions`, it **returns `34601` directly before calling the adapter**
> (Action Denied, see [API Response Standard §5.3](api-response.md#53-framework-extension-return-codes-last-three-digits-of-the-34xxx-platform-error-range)).
> The two do not replace each other: first pass the `34601` framework gate, then fall to the platform-layer `340xx` errors.

## 8. Related Documents

**Reference alongside when implementing request operations**:
- [Event Conversion Standard](event-conversion.md) - Complete event conversion specification (including `request_id` field requirements)
- [API Response Standard](api-response.md) - Adapter API response format standard (operation return values and error codes)

**Other DSLs of the same adapter**:
- [Send Method Specification](send-method-spec.md) - Method naming and parameter specifications for the Send class
- [Session Types Standard](session-types.md) - Session type definitions and mapping relationships