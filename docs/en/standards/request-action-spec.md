# ErisPulse Request Operation Specification

> [!TIP]
> **When to read this**: When your adapter needs to handle friend requests/group invitations (converting request events, implementing `accept`/`reject`, including contextual retention of request types for heterogeneous endpoints), or when modules use `event.approve()` / `event.reject()` to approve requests, refer to this document. Skip if not needed.

This document defines the standardized specification for request event operations in ErisPulse adapters, including required fields for request events, usage of the Request DSL, and adapter implementation requirements.

## 1. Overview

Request events (`type: "request"`) are a special event type defined in the OneBot12 standard, representing requests that require a Bot to make a decision (such as friend requests, group invitations, etc.).

Unlike message events, request events require **bidirectional interaction**:
1. **Receiving**: The adapter converts native platform requests into standard request events
2. **Responding**: Modules execute operations through the `Request` DSL or `Event.approve()`/`Event.reject()` methods

```
Platform Native Request Event
    │
    ▼
Converter.convert()        ← Adapter implementation (forward conversion)
    │
    ▼
Standard Request Event (with request_id)
    │
    ├─→ Module Processor @request.on_friend_request()
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
    │       Platform API Call
    │
    └─→ Or directly through adapter operations
            await adapter.Request("req_id").accept()
```

## 2. Request Event Field Requirements

### 2.1 Standard Fields

Request events must include OneBot12 standard fields, plus the following fields:

| Field | Type | Required | Description |
|------|------|------|------|
| `request_id` | string | **Strongly recommended** | Request identifier, used for approve/reject operations |
| `user_id` | string | Yes | ID of the request initiator |
| `user_nickname` | string | No | Nickname of the request initiator |
| `comment` | string | No | Request comment |

### 2.2 `request_id` Field

`request_id` is the core identifier for request operations:

- **Usage**: Identifies a request that can be operated on, used by the `Request` DSL
- **Generation Rules**:
  - Prefer using the platform's native request identifier (e.g., OneBot11's `flag` field, Telegram's `chat_invite_link`, etc.)
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
  "comment": "Please add as friend",
  "request_id": "flag_abc123",
  "onebot11_raw": {...},
  "onebot11_raw_type": "request"
}
```

## 3. Request DSL

### 3.1 Chained Calls

`Request` provides a chain-call interface consistent with `Send`:

```python
# Basic usage
await adapter.Request("req_id").accept()
await adapter.Request("req_id").reject()

# Specify Bot account
await adapter.Request("req_id").Using("bot1").accept()

# With comment (via kwargs)
await adapter.Request("req_id").accept(comment="Welcome")
await adapter.Request("req_id").reject(comment="Not adding for now")

# Combined usage
await adapter.Request("req_id").Using("bot1").accept(comment="Welcome")
```

### 3.2 Method List

| Method | Description | Return Value |
|------|------|--------|
| `Using(account_id)` | Specify the Bot account for the operation | `RequestDSL` (supports chained calls) |
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

**Not Implemented** (Adapter did not override `_do_accept`/`_do_reject`):
```json
{
    "status": "failed",
    "retcode": 10002,
    "data": null,
    "message_id": "",
    "message": "Platform MyAdapter did not implement request operation (accept)"
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
        print("Warning: Request event lacks request_id")
        return
    
    # Approve request
    result = await event.approve()
    
    # Or reject request
    # result = await event.reject(comment="Not adding friend for now")
    
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
    Extract request ID from platform-native event.
    
    Prefer using the platform-native request identifier; if none, generate a unique ID
    """
    # Prefer using platform-native ID
    if flag := raw_event.get("flag"):
        return str(flag)
    if request_key := raw_event.get("request_key"):
        return str(request_key)
    
    # Fallback: generate unique ID
    import hashlib
    raw = f"{self._platform_name}_{raw_event.get('user_id')}_{raw_event.get('timestamp')}"
    return hashlib.md5(raw.encode()).hexdigest()
```

### 5.2 Request Internal Class Implementation

The base class's `accept()` / `reject()` are public entry points: they include scope authorization gates (`scope.actions.<owner>.request`, returning 34601 if disabled) and task wrapping. **Adapters should not override public entry points**—overriding them bypasses the authorization gate. Adapters should override `_do_accept` / `_do_reject` (async methods, directly returning standard response dict).

> **Multi-account reminder**: `_do_accept` / `_do_reject` internally call `call_api` directly, and the account is not automatically injected—accounts are obtained via `self.request_context.get("account_id")` (explicitly specified with `Using()` > automatically bound via event chain, same as `send_context` in `Send`). If not passed as `account_id`, multi-account deployment will default to the default account.

```python
from ErisPulse.Core import BaseAdapter, RequestDSL

class MyAdapter(BaseAdapter):
    
    class Request(RequestDSL):
        """MyPlatform request operation implementation"""
        
        async def _do_accept(self, **kwargs) -> dict:
            """
            Approve request.
            
            :param kwargs: Extension parameters, e.g., comment="comment"
            :return: Standard response format dict
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
            """Reject request (same structure as _do_accept: approve=False)"""
```

### 5.3 Request Type Context Retention (Required for Heterogeneous Endpoints)

#### 5.3.1 Contract Gap

`Request` DSL is a stateless handle: the caller only holds `request_id` (see §3). Request type is not in the call parameters. However, many platform's approve/reject endpoints are **heterogeneous**—for example, in the OneBot11 system:

| Request Type | Endpoint |
|---|---|
| Friend Addition | `set_friend_add_request(flag, approve)` |
| Group Application / Invitation | `set_group_add_request(flag, sub_type, approve)`, `sub_type ∈ {"add", "invite"}` |

The caller only knows `request_id`, but the endpoint selection requires the type. This context can only be supplemented by the adapter: the request event is received and converted by the adapter (type information is available at the time of conversion), and the request type corresponding to a `request_id` does not change. If the adapter does not retain it, it can only guess the endpoint or rely on non-standard parameters from the caller—typical failure forms are **group invitations sent to the friend endpoint**, where the flag is parsed by the protocol side as a user ID and errors occur.

#### 5.3.2 Specification Requirements

For adapters with heterogeneous endpoints (approve/reject need to route by request type), `accept` / `reject` implementation must satisfy:

1. **Event-side retention**: At the entry point where the adapter receives the request event, write `request_id → {request type, sub_type, group_id, account}` into the instance's internal cache (uniform fields as in §5.3.3), and clean up expired entries at the same time
2. **Operation-side routing**: In `_do_accept` / `_do_reject`, the endpoint selection order is **kwargs explicit parameters > cache > fallback to default endpoint with WARNING**—if the type is unknown, a log must be issued (observable), and silent endpoint selection is not allowed
3. **Reserved parameter names**: Explicit override parameters are uniformly named `request_type` / `sub_type` / `group_id` (no leading underscore, same name and meaning across adapters); do not use private names like `_request_type` (standard callers will not pass)
4. **Account reading and ownership verification**: The operation account is uniformly obtained via the base class property `self.request_context.get("account_id")` (explicitly specified with `Using()` > automatically bound via event chain, same as `send_context` in `Send`); the account from the event arrival is used as a fallback when the event chain is missing (e.g., synthesized events from polling, rebuilt across restarts). **If the account cannot be resolved to a specific account instance, it must fail quickly** (return 34005), and silent fallback to the default account is not allowed—fallback will send the operation to the wrong connection (flag does not exist in the default account session, platform reports invalid, and multi-account manifests as "only the first account can operate")
5. **Default persistence**: The retention medium defaults to the framework's unified storage (`self.sdk.storage`) **single-key snapshot**—requests are low-frequency approval events (friend/group requests, not message streams), written through at the time of event arrival (library footprint is always 1 key); loaded once at startup and zero overhead on read paths during runtime; if storage is unavailable, degrade to only memory (WARNING), without blocking event flow
6. **Cleanup after processing**: Delete the `request_id` entry after successful submission and synchronize the snapshot

Platforms with a single request endpoint (e.g., unified `/set_request`) do not need to retain, and can pass through directly. This section is for adapter implementation standards, and the `Request` DSL contract is unaffected.

#### 5.3.3 Uniform entry fields (medium-agnostic)

Context entries follow the uniform field shape below. **Field shapes are interoperation contracts**: memory dict, KV value, ORM row all follow the same shape for persistence, ensuring shape consistency for cross-adapter aggregation or migration; storage medium is self-selected, and field semantics do not change with the medium.

| Field | Type | Required | Semantics and source |
|---|---|---|---|
| `request_type` | `str` | Yes | Request type, taken from event `detail_type` (`"friend"` / `"group"`) |
| `sub_type` | `str \| None` | Required for group requests | Group request sub-type `"add"` / `"invite"`, taken from platform-native event (OB11 system `sub_type`) |
| `group_id` | `str \| None` | Required for group requests | Target group ID, taken from platform-native event |
| `account` | `str \| None` | Required for multi-account | Event arrival account, taken from event `self.user_id` |
| `ts` | `float` | Yes | Unix timestamp (seconds) of event arrival, used as TTL baseline |

Entry consistency rules:

- **One-to-one mapping**: One `request_id` corresponds to at most one entry; duplicate events with the same `request_id` overwrite the entry (idempotent)
- **Cleanup after processing**: Delete the entry immediately after successful submission
- **TTL**: Use `ts` as the baseline, recommended TTL is 1 hour (covering platform-side request validity); expired entries are treated as not retained, use fallback default endpoint + WARNING
- **Key name (when persisting to KV)**: `{adapter config key}:request_ctx:{request_id}`, avoiding cross-adapter conflicts

#### 5.3.4 Reference Implementation (Default Single-Key Snapshot with Unified Storage)

The retention medium **defaults to framework unified storage** (`self.sdk.storage`): request events are low-frequency approval events (friend/group requests, not message streams), written through immediately upon arrival, avoiding write pressure. The storage format is a **single-key snapshot**—the entire context dictionary is written as one key (library footprint is always 1 key, automatically converging with processing), without separate key writes for each flag. Once loaded back into memory at startup, read paths during runtime have zero overhead.

```python
import time

from ErisPulse.Core import BaseAdapter, RequestDSL


class MyAdapter(BaseAdapter):
    """Platform with heterogeneous request endpoints (separate endpoints for friend and group requests)"""

    _REQ_CTX_TTL = 86400   # Retention seconds (covering platform-side flag validity, survives restart)
    _REQ_CTX_MAX = 512     # Maximum entry capacity

    def __init__(self, sdk=None):
        super().__init__(sdk)
        self._request_ctx: dict[str, dict] = {}   # request_id → request context (in-memory)
        self._ctx_key = f"{self._get_config_key()}:request_ctx"   # Single-key snapshot

    async def start(self):
        # Load on startup (survives restart); handle storage unavailability as cold start
        try:
            loaded = self.sdk.storage.get(self._ctx_key, {}) or {}
            now = time.time()
            self._request_ctx = {k: v for k, v in loaded.items()
                                 if now - v.get("ts", 0) <= self._REQ_CTX_TTL}
        except Exception as e:
            self.logger.warning(f"Request context loading failed (handled as cold start): {e}")
            self._request_ctx = {}

    def _persist_ctx(self) -> None:
        """Single-key snapshot write-through (degrade to only memory if storage unavailable, does not block event flow)"""
        try:
            self.sdk.storage.set(self._ctx_key, self._request_ctx)
        except Exception as e:
            self.logger.warning(f"Request context write-through failed (degraded to only memory): {e}")

    def remember_request(self, request_id: str, *, request_type: str,
                         sub_type: str | None = None, group_id: str | None = None,
                         account: str | None = None) -> None:
        """Event-side retention of request context (call at the entry point where the adapter receives request events)"""
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
            "account": account,             # Event arrival account (self.user_id of event / substitute account name)
            "ts": now,
        }
        self._persist_ctx()

    class Request(RequestDSL):
        """Endpoint routing: kwargs explicit parameters > cache > fallback to default endpoint + WARNING"""

        def _route(self, **kwargs) -> dict:
            ctx = {k: kwargs[k] for k in ("request_type", "sub_type", "group_id") if kwargs.get(k)}
            cached = self._adapter._request_ctx.get(self._request_id, {})
            if not ctx.get("request_type"):
                ctx.update({k: v for k, v in cached.items()
                            if k in ("request_type", "sub_type", "group_id") and v})
                ctx.setdefault("account", cached.get("account"))
            if not ctx.get("request_type"):
                self._adapter.logger.warning(f"Request {self._request_id} type unknown, fallback to friend endpoint")
                ctx["request_type"] = "friend"
            return ctx

        def _resolve_or_fail(self, account):
            """
            Approval account ownership verification: fail fast if resolution fails (34005), do not fallback to default account.

            Fallback to default account will send the operation to the wrong connection (flag does not exist in that account's session,
            platform reports invalid, manifesting as the "only the first account can operate" mysterious fault).
            """
            if not account:
                return None, None            # Maintain default account semantics when no account information
            name, inst = self._adapter._resolve_account(account)
            hit = str(account) == str(name) or str(account) == str(getattr(inst, "bot_id", "") or "")
            if not hit:
                self._adapter.logger.warning(
                    f"Request {self._request_id} account {account} cannot be resolved, refuse to fallback to default account")
                return None, "34005"
            return (name, inst), None

        async def _do_accept(self, **kwargs) -> dict:
            """Approve request; kwargs type routing available via request_type / sub_type / group_id"""
            return await self._do_action(approve=True, **kwargs)

        async def _do_reject(self, **kwargs) -> dict:
            """Reject request (same structure as _do_accept: approve=False)"""
            return await self._do_action(approve=False, **kwargs)

        async def _do_action(self, approve: bool, **kwargs) -> dict:
            ctx = self._route(**kwargs)
            account = self.request_context.get("account_id") or ctx.get("account")
            resolved, fail = self._resolve_or_fail(account)
            if fail:
                return {
                    "status": "failed", "retcode": 34005, "data": None,
                    "message_id": "", "message": f"Request account {account} cannot be resolved to account instance",
                }
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
                    "status": "failed", "retcode": 34001, "data": None,
                    "message_id": "",
                    "message": f"Request operation failed: {e}",
                }
            if response["status"] == "ok":
                self._adapter._request_ctx.pop(self._request_id, None)   # Cleanup after processing
                self._adapter._persist_ctx()
            return response
```

#### 5.3.5 Edge Cases and Degradation

**Degradation semantics**: If unified storage is unavailable (connection failure cooling period fast-fail), write-through degrades to only memory (WARNING observable), events are still distributed; after restart, entries are lost and the "type unknown fallback + WARNING" path is taken.

**Equivalent media**: Built-in ORM (`request_id` primary key table, see [Data Model Layer](../developer-guide/orm.md)) semantics are equivalent, adapters can choose as needed; no additional files or new dependencies.

**Multi-instance boundaries**: This specification does not cover multi-process instance coordination—ErisPulse is a single-process multi-bot model (multi-account in the same process, requests naturally side with their account), unified storage satisfies restart semantics; cross-instance sharing (multi-process account distribution) will be addressed as needed.

### 5.4 Platform Does Not Support Request Operations

If the platform itself does not support friend requests/group invitations (e.g., some platforms handle requests automatically), the adapter can:

1. **Do not override the `Request` inner class**: Use the base class default implementation, `accept()`/`reject()` returns `retcode=10002`
2. **Skip `request_id` generation in conversion**: Do not generate `request_id`, let `event.approve()` raise `ValueError`
3. **Log**: In `_do_accept` / `_do_reject`, log a warning and return an appropriate error code

### 5.5 Summary: Send and Request in Parallel

The adapter has two parallel DSL inner classes, each with its own responsibilities:

```
BaseAdapter
├── Send(SendDSL)     ← Message sending
│   ├── Raw_ob12()    ← Must implement
│   ├── Text()        ← Recommended implementation
│   └── Image()       ← Implement as needed
│
└── Request(RequestDSL) ← Request operations
    ├── accept()        ← Public entry point (scope gate + task wrapping, do not override)
    ├── reject()        ← Public entry point (same as above)
    ├── _do_accept()    ← Implement as needed
    └── _do_reject()    ← Implement as needed
```

### 5.6 Adapter `__init__` Considerations

When overriding the `Request` inner class `__init__`, you must pass through parameters and call `super().__init__()`, see [Adapter Development Basics - `__init__` Considerations](../developer-guide/adapters/getting-started.md#init-注意事项) (`Request` is the same, parameters are `adapter, request_id, account_id`).

## 6. Adapter Implementation Checklist

### Basic Requirements
- [ ] If `__init__` is overridden, `super().__init__()` has been called (ensure Send / Request factory initialization)

### Request Event Conversion
- [ ] Request event includes `request_id` field (strongly recommended)
- [ ] `detail_type` is correctly mapped to `"friend"` or `"group"`
- [ ] Platform raw data is preserved in the `{platform}_raw` field
- [ ] `request_id` generation rules are documented

### Request Operations
- [ ] `Request` inner class is implemented (if platform supports request operations)
- [ ] `_do_accept()` / `_do_reject()` are overridden (public entry points `accept()` / `reject()` should not be overridden—this bypasses the scope authorization gate)
- [ ] Operation returns standard API response format
- [ ] Unsupported operations return `retcode=10002`
- [ ] Network errors return `retcode=33xxx` (follow API response standard)

### Request Type Context Retention (Heterogeneous Endpoints, see §5.3)
- [ ] Request event entry has retained `request_id → {request type, sub_type, group_id, account}` context
- [ ] Entry fields match the unified field table in §5.3.3 (including `ts` timestamp; `request_id` is one-to-one, deleted after processing)
- [ ] `accept` / `reject` endpoint routing order is kwargs explicit parameters > cache > fallback to default endpoint + WARNING
- [ ] Type override parameters use reserved names `request_type` / `sub_type` / `group_id` (no `_request_type` private naming convention)
- [ ] Cache has TTL and capacity limit, corresponding entries are deleted after successful submission
- [ ] Multi-account: Operation account is read via `self.request_context.get("account_id")` (`Using()` > event chain fallback), arrival account of event is used as fallback when event chain is missing (e.g., polling synthesized events, rebuilt across restarts). **If account cannot be resolved to a specific account instance, fail quickly** (return 34005), do not silently fallback to default account—fallback will send operation to the wrong connection (flag does not exist in default account session, platform reports invalid, multi-account manifests as "only first account can operate")
- [ ] Default unified storage single-key snapshot: loaded at startup, written through at event arrival/processing, degraded to only memory if storage unavailable
- [ ] Cleanup after processing: delete corresponding `request_id` entry and synchronize snapshot

Platforms with a single request endpoint do not need to retain, and can pass through directly. This section is for adapter implementation standards, `Request` DSL contract is unaffected.

## 7. Error Code Extension

Error codes recommended for the **adapter implementation layer** related to request operations (following [API Response Standard](api-response.md) §3.2, falling within the low three digits of the `34xxx` platform error segment):

| Error Code | Error Name | Description |
|-------|-------|------|
| 34001 | Request Not Found | Request does not exist or has expired |
| 34002 | Request Already Handled | Request has already been handled |
| 34003 | Request Not Supported | Platform does not support this type of request operation |
| 34004 | Permission Denied | Bot does not have permission to handle this request (returned by platform) |
| 34005 | Request Account Unresolved | Request account cannot be resolved to account instance (fail fast, do not fallback to default account) |

> **Boundary with framework codes**: The above `340xx` are **platform/adapter** returned request processing failures; ErisPulse framework directly returns `34601` (Action Denied, see [API Response Standard §5.3](api-response.md#53-框架扩展返回码34xxx-平台错误段的低三位自定义)) when `scope.actions` disables a module's request action **before** calling the adapter, and these two are not substitutes: first pass the `34601` framework gate, then fall to the platform layer `340xx` error.

## 8. Related Documentation

**For implementing request operations, refer to the following documents**:
- [Event Conversion Standard](event-conversion.md) - Complete event conversion specification (including `request_id` field requirements)
- [API Response Standard](api-response.md) - Adapter API response format standard (operation return values and error codes)
- [Storage Backends](../advanced/storage-backends.md) - When cross-restart request context persistence is needed, use unified KV storage

**Other DSLs in the same adapter**:
- [Send Method Specification](send-method-spec.md) - Naming and parameter specification for Send class methods
- [Session Type Standard](session-types.md) - Definition and mapping of session types