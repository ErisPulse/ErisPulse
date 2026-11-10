# ErisPulse Request Operation Specification

> [!TIP]
> **When to read this**: When your adapter needs to handle friend requests/group invitations (converting request events, implementing `accept`/`reject`, including request-type context retention for heterogeneous endpoints), or when a module needs to use `event.approve()` / `event.reject()` to approve requests, refer to this document. Otherwise, skip it.

This document defines the standardized specification for request event operations in ErisPulse adapters, including field requirements for request events, usage of the Request DSL, and adapter implementation requirements.

## 1. Overview

Request events (`type: "request"`) are a special event type defined in the OneBot12 standard, representing requests that require the Bot to make a decision (e.g., friend requests, group invitations, etc.).

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
Standard request event (containing request_id)
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
    │       BaseAdapter.Request.accept()  ← Overridden by adapter
    │               │
    │               ▼
    │       Platform API call
    │
    └─→ Or operate directly through the adapter
            await adapter.Request("req_id").accept()
```

## 2. Request Event Field Requirements

### 2.1 Standard Fields

In addition to the required OneBot12 standard fields, request events must also include the following fields:

| Field | Type | Required | Description |
|------|------|------|------|
| `request_id` | string | **Strongly recommended** | Request identifier, used for accept/reject operations |
| `user_id` | string | Yes | ID of the request initiator |
| `user_nickname` | string | No | Nickname of the request initiator |
| `comment` | string | No | Message attached to the request |

### 2.2 The `request_id` Field

`request_id` is the core identifier for request operations:

- **Purpose**: Identifies an actionable request, used by the `Request` DSL
- **Generation rules**:
  - Prefer the platform's native request identifier (e.g., OneBot11's `flag` field, Telegram's `chat_invite_link`, etc.)
  - If the platform has no native request ID, the adapter should generate a unique identifier (recommended format: `{platform}_{timestamp}_{user_id}`)
- **Uniqueness**: Should remain unique within the scope of a single platform
- **Missing behavior**: When `request_id` is missing, `event.approve()` / `event.reject()` will raise a `ValueError`

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

`Request` provides a chaining interface consistent in style with `Send`:

```python
# Basic usage
await adapter.Request("req_id").accept()
await adapter.Request("req_id").reject()

# Specify the Bot account
await adapter.Request("req_id").Using("bot1").accept()

# With a remark (via kwargs)
await adapter.Request("req_id").accept(comment="Welcome")
await adapter.Request("req_id").reject(comment="Not adding for now")

# Combined usage
await adapter.Request("req_id").Using("bot1").accept(comment="Welcome")
```

### 3.2 Method List

| Method | Description | Return Value |
|------|------|--------|
| `Using(account_id)` | Specifies the Bot account that performs the operation | `RequestDSL` (supports chaining) |
| `accept(**kwargs)` | Accepts the request | `asyncio.Task` (returns the standard response after awaiting) |
| `reject(**kwargs)` | Rejects the request | `asyncio.Task` (returns the standard response after awaiting) |

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

**Not implemented** (the adapter has not overridden `_do_accept`/`_do_reject`):
```json
{
    "status": "failed",
    "retcode": 10002,
    "data": null,
    "message_id": "",
    "message": "Platform MyAdapter has not implemented request operations"
}
```

## 4. Event Convenience Methods

The `Event` wrapper class provides convenience methods, suitable for use in request event handlers:

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
    # result = await event.reject(comment="Not adding as friend for now")
    
    # Check the result
    if result.get("status") == "ok":
        print("Operation succeeded")
    else:
        print(f"Operation failed: {result.get('message')}")
```

### 4.1 Event Method List

| Method | Description | Return Value |
|------|------|--------|
| `get_request_id()` | Gets the request ID | `str` |
| `approve(comment=None)` | Approves the current request event | Standard response format |
| `reject(comment=None)` | Rejects the current request event | Standard response format |

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
        "request_id": self._extract_request_id(raw_event),  # ← key field
        f"{self._platform_name}_raw": raw_event,
        f"{self._platform_name}_raw_type": raw_event.get("type", ""),
    }

def _extract_request_id(self, raw_event: dict) -> str:
    """
    Extract the request ID from a platform-native event
    
    Prefer the platform's native request identifier; generate a unique ID if absent
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

### 5.2 Implementing the Request Inner Class

The base class's `accept()` / `reject()` are the public entry points: they include a built-in scope authorization gate (`scope.actions.<owner>.request`; when disabled, a 34601 rejection response is returned directly) and task wrapping. **Adapters must not override the public entry points**—overriding bypasses the authorization gate. Adapters override `_do_accept` / `_do_reject` (async methods that directly return the standard response dict).

> **Multi-account reminder**: Inside `_do_accept` / `_do_reject`, the adapter calls `call_api` itself, and the account is not injected automatically—the account is obtained via `self.request_context.get("account_id")` (explicit specification via `Using()` > automatic binding via the event chain, aligned with Send's `send_context`) and passed to `call_api` as the `account_id` parameter; otherwise, in multi-account deployments the call falls to the default account.

```python
from ErisPulse.Core import BaseAdapter, RequestDSL

class MyAdapter(BaseAdapter):
    
    class Request(RequestDSL):
        """MyPlatform request operation implementation"""
        
        async def _do_accept(self, **kwargs) -> dict:
            """
            Accept the request
            
            :param kwargs: Extended parameters, e.g., comment="remark"
            :return: dict in standard response format
            """
            try:
                result = await self._adapter.call_api(
                    endpoint="/set_request",
                    request_id=self._request_id,
                    account_id=self.request_context.get("account_id"),
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
        
        async def _do_reject(self, **kwargs) -> dict:
            """Reject the request (same structure as _do_accept: approve=False)"""
```

### 5.3 Request-Type Context Retention (Required for Adapters with Heterogeneous Endpoints)

#### 5.3.1 Contract Gap

The `Request` DSL is a stateless handle: the caller only holds `request_id` ([§3](#3-request-dsl)), and the request type is not part of the call parameters. Yet many platforms have **heterogeneous** accept/reject endpoints—taking the OneBot11 family as an example:

| Request Type | Endpoint |
|---|---|
| Friend addition | `set_friend_add_request(flag, approve)` |
| Group application / Group invitation | `set_group_add_request(flag, sub_type, approve)`, `sub_type ∈ {"add", "invite"}` |

The caller only knows `request_id`, but endpoint selection requires the type. Only the adapter can fill in this context: request events are received and converted by the adapter in the first place (the type information is already at hand during conversion), and the request type corresponding to a given `request_id` never changes. If the adapter does not retain it itself, it can only guess the endpoint or rely on the caller passing non-standard parameters—the typical failure mode is **a group invitation being sent to the friend endpoint**, where the flag is parsed by the protocol side as a user_id and an error occurs.

#### 5.3.2 Specification Requirements

For adapters whose platform endpoints are heterogeneous (accept/reject must be routed by request type), the `accept` / `reject` implementations must satisfy:

1. **Event-side retention**: At the entry point where the adapter receives a request event, write `request_id → {request type, sub_type, group_id, account}` into an instance-level cache (unified fields in §5.3.3), and clean up expired entries along the way
2. **Operation-side routing**: The endpoint selection order inside `_do_accept` / `_do_reject` is **explicit kwargs arguments > cache > fall back to the default endpoint and log a WARNING**—an unknown type must be logged (observability); silently picking an endpoint is not allowed
3. **kwargs reserved names**: Explicit override parameters are uniformly named `request_type` / `sub_type` / `group_id` (no underscore prefix, same name and meaning across adapters); private convention names like `_request_type` must not be used (standard callers will not pass them)
4. **Account reading**: The operating account is uniformly obtained via the base class property `self.request_context.get("account_id")` (explicit specification via `Using()` > automatic binding via the event chain, aligned with Send's `send_context`); the cache retains the account at event arrival as a fallback when the event chain is missing (e.g., polling-synthesized events, rebuilds across restarts)
5. **Post-processing cleanup**: After an operation is submitted successfully, delete that `request_id` from the cache

Platforms with a single request endpoint (such as a unified `/set_request`) need no retention; passing through directly is fine. This section is guidance for adapter implementations; the `Request` DSL contract is unaffected.

#### 5.3.3 Unified Entry Fields (Media-Independent)

Context entries are retained in the following unified field shape. **The field shape is an interoperability contract**: in-memory dicts, KV values, and ORM rows are all stored in the same shape, so aggregation or migration across adapters later keeps a consistent shape; the storage medium is your choice, and field semantics do not change with the medium.

| Field | Type | Required | Semantics and Source |
|---|---|---|---|
| `request_type` | `str` | Yes | Request type, taken from the event's `detail_type` (`"friend"` / `"group"`) |
| `sub_type` | `str \| None` | Required for group requests | Group request sub-type `"add"` / `"invite"`, taken from the platform-native event (`sub_type` in the OB11 family) |
| `group_id` | `str \| None` | Required for group requests | Target group ID, taken from the platform-native event |
| `account` | `str \| None` | Required for multi-account | Account at event arrival, taken from the event's `self.user_id` |
| `ts` | `float` | Yes | Unix timestamp (seconds) of event arrival; basis for TTL determination |

Entry consistency rules:

- **One-to-one mapping**: One `request_id` corresponds to at most one entry; duplicate events with the same `request_id` overwrite the entry (idempotent)
- **Delete after processing**: The entry is deleted as soon as an operation is submitted successfully
- **TTL**: Based on `ts`; an order of 1 hour is recommended (covering the platform-side request validity period). Expired entries are treated as not retained, falling back to the default endpoint + WARNING
- **Key name (for KV persistence)**: `{adapter config key}:request_ctx:{request_id}`, to avoid cross-adapter conflicts

#### 5.3.4 Reference Implementation (In-Memory Cache)

```python
import time

from ErisPulse.Core import BaseAdapter, RequestDSL


class MyAdapter(BaseAdapter):
    """Platform with heterogeneous request endpoints (separate endpoints for friend and group requests)"""

    _REQ_CTX_TTL = 3600    # Seconds to retain context; just cover the platform-side request validity period
    _REQ_CTX_MAX = 512     # Cache capacity limit

    def __init__(self, sdk=None):
        super().__init__(sdk)
        self._request_ctx: dict[str, dict] = {}   # request_id → request context

    def remember_request(self, request_id: str, *, request_type: str,
                         sub_type: str | None = None, group_id: str | None = None,
                         account: str | None = None) -> None:
        """Retain request context on the event side (called at the entry point where the adapter receives a request event)"""
        now = time.time()
        expired = [k for k, c in self._request_ctx.items() if now - c["ts"] > self._REQ_CTX_TTL]
        for k in expired:
            self._request_ctx.pop(k)
        while len(self._request_ctx) >= self._REQ_CTX_MAX:
            self._request_ctx.pop(min(self._request_ctx, key=lambda k: self._request_ctx[k]["ts"]))
        self._request_ctx[request_id] = {
            "request_type": request_type,   # "friend" / "group"
            "sub_type": sub_type,           # Group request sub-type: "add" / "invite"
            "group_id": group_id,
            "account": account,             # Account at event arrival (the event's self.user_id)
            "ts": now,
        }

    class Request(RequestDSL):
        """Endpoint routing: explicit kwargs arguments > cache > fall back to the default endpoint + WARNING"""

        def _route(self, **kwargs) -> dict:
            ctx = {k: kwargs[k] for k in ("request_type", "sub_type", "group_id") if kwargs.get(k)}
            cached = self._adapter._request_ctx.get(self._request_id, {})
            if not ctx.get("request_type"):
                ctx.update({k: v for k, v in cached.items()
                            if k in ("request_type", "sub_type", "group_id") and v})
                ctx.setdefault("account", cached.get("account"))
            if not ctx.get("request_type"):
                self._adapter.logger.warning(f"Request {self._request_id} has unknown type, falling back to the friend endpoint")
                ctx["request_type"] = "friend"
            return ctx

        async def _do_accept(self, **kwargs) -> dict:
            """Accept the request; type routing can be explicitly overridden via request_type / sub_type / group_id in kwargs"""
            return await self._do_action(approve=True, **kwargs)

        async def _do_reject(self, **kwargs) -> dict:
            """Reject the request (same structure as _do_accept: approve=False)"""
            return await self._do_action(approve=False, **kwargs)

        async def _do_action(self, approve: bool, **kwargs) -> dict:
            ctx = self._route(**kwargs)
            account = self.request_context.get("account_id") or ctx.get("account")
            try:
                if ctx["request_type"] == "group":
                    result = await self._adapter.call_api(
                        endpoint="/set_group_add_request",
                        flag=self._request_id,
                        sub_type=ctx.get("sub_type") or "add",
                        approve=approve,
                        account_id=account,
                    )
                else:
                    result = await self._adapter.call_api(
                        endpoint="/set_friend_add_request",
                        flag=self._request_id,
                        approve=approve,
                        account_id=account,
                    )
                response = {
                    "status": "ok" if result.get("code") == 0 else "failed",
                    "retcode": result.get("code", 0),
                    "data": None,
                    "message_id": "",
                    "message": result.get("message", ""),
                }
            except Exception as e:
                response = {
                    "status": "failed",
                    "retcode": 34001,
                    "data": None,
                    "message_id": "",
                    "message": f"Request operation failed: {e}",
                }
            if response["status"] == "ok":
                self._adapter._request_ctx.pop(self._request_id, None)   # Cleanup after processing
            return response
```

#### 5.3.5 Persistence Across Restarts (Optional)

In-memory + TTL already covers the vast majority of scenarios: a request typically takes seconds to a few minutes from arrival to processing, the platform side has its own expiration, and the window for losing the cache due to a restart is tiny (fallback endpoint + WARNING already guarantee observability). Only when the adapter cares about "a restart happening exactly at the moment of processing" should the context be persisted to a durable medium. Choose one of the media below; all are stored in the unified field shape of §5.3.3:

- **KV storage**: `self.sdk.storage` (the framework's unified KV storage; for backend switching see [Storage Backends](../advanced/storage-backends.md)):

  ```python
  # Event entry: write (for the key, see the key-name rules in §5.3.3)
  key = f"{self._get_config_key()}:request_ctx:{request_id}"
  self.sdk.storage.set(key, {"request_type": "group", "sub_type": "invite",
                             "group_id": group_id, "account": self_id, "ts": time.time()})

  # Operation side: read + cleanup
  ctx = self.sdk.storage.get(key)
  self.sdk.storage.delete(key)
  ```

  The storage layer does not expire entries: entries carry their own `ts`, and the reader treats an expired entry as not retained (falls back + WARNING); you must `delete` after processing.

- **Built-in ORM**: `Model` / `Field` declarative models (built in since 2.9, see [Data Model Layer](../developer-guide/orm.md)) can serve as an equivalent medium, with table columns created per the unified field table (`request_id` as the primary key). Two notes: `create_table` is idempotent with `IF NOT EXISTS`; later field evolution requires the adapter to migrate existing tables itself; the table belongs to the adapter's own data, not a cross-adapter shared table.

Whichever medium you choose: **a persistence write failure must not block the event flow**—when the storage backend is unavailable (fast-fail during cooldown), degrade to in-memory-only retention and dispatch events as usual; both persistence media are optional, in-memory by default, with no new external dependencies.

### 5.4 The Platform Does Not Support Request Operations

If the platform itself does not support friend request/group invitation operations (e.g., some platforms handle requests automatically), the adapter can:

1. **Not override the `Request` inner class**: use the base class default implementation, which returns `retcode=10002` when `accept()`/`reject()` is called
2. **Skip `request_id` during conversion**: do not generate `request_id`, letting `event.approve()` raise a `ValueError`
3. **Log**: record a warning in `_do_accept` / `_do_reject` and return an appropriate error code

### 5.5 Summary: Send and Request in Parallel

An adapter has two parallel DSL inner classes, each with its own role:

```
BaseAdapter
├── Send(SendDSL)     ← Message sending
│   ├── Raw_ob12()    ← Must implement
│   ├── Text()        ← Recommended to implement
│   └── Image()       ← Implement as needed
│
└── Request(RequestDSL) ← Request operations
    ├── accept()        ← Public entry (scope gate + task wrapping, do not override)
    ├── reject()        ← Public entry (same as above)
    ├── _do_accept()    ← Override as needed
    └── _do_reject()    ← Override as needed
```

### 5.6 Notes on the Adapter `__init__`

When overriding the `__init__` of the `Request` inner class, you must pass through the parameters and call `super().__init__()`. See [Adapter Development Guide - `__init__` Notes](../developer-guide/adapters/getting-started.md#init-notes) (the same applies to `Request`, with parameters `adapter, request_id, account_id`).

## 6. Adapter Implementation Checklist

### Basic Requirements
- [ ] If `__init__` is overridden, `super().__init__()` has been called (ensures the Send / Request factory initialization)

### Request Event Conversion
- [ ] Request events include the `request_id` field (strongly recommended)
- [ ] `detail_type` is correctly mapped to `"friend"` or `"group"`
- [ ] Platform raw data is preserved in the `{platform}_raw` field
- [ ] The `request_id` generation rules are documented

### Request Operations
- [ ] The `Request` inner class is implemented (if the platform supports request operations)
- [ ] `_do_accept()` / `_do_reject()` are overridden (do not override the public entry points `accept()` / `reject()`—it bypasses the scope authorization gate)
- [ ] Operations return the standard API response format
- [ ] Unsupported operations return `retcode=10002`
- [ ] Network errors return `retcode=33xxx` (following the API response standard)

### Request-Type Context Retention (heterogeneous-endpoint platforms, see §5.3)
- [ ] The request event entry point retains `request_id → {request type, sub_type, group_id, account}` context
- [ ] Entry fields match the unified field table in §5.3.3 (including the `ts` timestamp; one-to-one mapping for `request_id`, delete after processing)
- [ ] `accept` / `reject` endpoint routing order is explicit kwargs arguments > cache > fall back to the default endpoint + WARNING
- [ ] Type override parameters use the reserved names `request_type` / `sub_type` / `group_id` (no private convention names like `_request_type`)
- [ ] The cache has a TTL and a capacity limit, and the corresponding entry is cleaned up after an operation is submitted successfully
- [ ] Multi-account: the operating account is read via `self.request_context.get("account_id")` (`Using()` > event-chain fallback), with the cached account as the fallback when the event chain is missing
- [ ] If a persistence medium is used: write failures degrade to in-memory-only retention without blocking the event flow

## 7. Error Code Extensions

Recommended error codes at the **adapter implementation layer** for request operations (following the [API Response Standard](api-response.md) §3.2,
using the three low digits of the `34xxx` platform error range for customization):

| Error Code | Error Name | Description |
|-------|-------|------|
| 34001 | Request Not Found | The request does not exist or has expired |
| 34002 | Request Already Handled | The request has already been processed |
| 34003 | Request Not Supported | The platform does not support this type of request operation |
| 34004 | Permission Denied | The Bot has no permission to process this request (returned by the platform) |

> **Boundary with framework codes**: The `340xx` codes above are request-processing failures returned by the **platform/adapter**;
> when the ErisPulse framework disables a module's request action via `scope.actions`, it returns `34601` (Action Denied) **before calling the adapter** (see [API Response Standard §5.3](api-response.md#53-framework-extension-return-codes-34xxx-platform-error-range-last-three-digits-custom)).
> The two do not replace each other: the `34601` framework gate is passed first, and only then do platform-layer `340xx` errors apply.

## 8. Related Documents

**Companion references when implementing request operations**:
- [Event Conversion Standard](event-conversion.md) - The complete event conversion specification (including `request_id` field requirements)
- [API Response Standard](api-response.md) - The adapter API response format standard (operation return values and error codes)
- [Storage Backends](../advanced/storage-backends.md) - The unified KV storage for when request context needs to persist across restarts

**Other DSLs of the same adapter**:
- [Send Method Specification](send-method-spec.md) - Method naming and parameter specification for the Send class
- [Session Type Standard](session-types.md) - Session type definitions and mapping relationships