# ErisPulse API Action Standards

This document defines the unified interface specification for **OneBot12 Standard API Actions** in the ErisPulse adapter, enabling module developers to program against a standard interface, with the adapter responsible for mapping to the platform's native API.

## 1. Design Background

In ErisPulse, message segments (message send/receive) and event formats already fully follow the OneBot12 standard, but **API Action Calls** (such as getting user info, getting group list, recalling messages) were previously not unified—module developers had to write different `call_api` calls for each platform.

`ApiDSL` resolves this issue by providing strongly-typed standard action methods:

```
Module code (Cross-platform unified)             Adapter implementation (Platform specific)
─────────────────              ──────────────────
adapter.Api.get_user_info("123")  →  adapter call_api / Override
adapter.Api.get_group_list()      →  adapter call_api / Override
adapter.Api.delete_message("id")  →  adapter call_api / Override
```

## 2. Three-Layer DSL Parallel Structure

The ErisPulse adapter has three parallel internal DSL classes, each with its specific duty:

```
BaseAdapter
├── Send(SendDSL)       ← Message sending (Text/Image/Raw_ob12)
├── Request(RequestDSL)  ← Request operations (accept/reject)
└── Api(ApiDSL)          ← Standard API Actions (Info query/Group management/Message management/File operations)★
```

| DSL | Duty | Method Style | Return Value |
|-----|------|-------------|--------------|
| `Send` | Sending messages | Chained + `asyncio.Task` | Standard response |
| `Request` | Handling request events | `asyncio.Task` | Standard response |
| `Api` | Query/Management operations | `async` methods | Standard response |

## 3. Standard Action List

### 3.1 User Related

| Method | OB12 Action | Params | data Return |
|--------|-------------|--------|-------------|
| `get_self_info()` | `get_self_info` | None | `user_id`, `user_name`, `user_displayname` |
| `get_user_info(user_id)` | `get_user_info` | `user_id: str` | `user_id`, `user_name`, `user_displayname`, `user_remark` |
| `get_friend_list()` | `get_friend_list` | None | `list[get_user_info response]` |

### 3.2 Group Related

| Method | OB12 Action | Params | data Return |
|--------|-------------|--------|-------------|
| `get_group_info(group_id)` | `get_group_info` | `group_id: str` | `group_id`, `group_name` |
| `get_group_list()` | `get_group_list` | None | `list[get_group_info response]` |
| `get_group_member_info(group_id, user_id)` | `get_group_member_info` | `group_id: str`, `user_id: str` | `user_id`, `user_name`, `user_displayname` |
| `get_group_member_list(group_id)` | `get_group_member_list` | `group_id: str` | `list[get_group_member_info response]` |
| `set_group_name(group_id, group_name)` | `set_group_name` | `group_id: str`, `group_name: str` | None |
| `leave_group(group_id)` | `leave_group` | `group_id: str` | None |

### 3.3 Message Management

| Method | OB12 Action | Params | Note |
|--------|-------------|--------|------|
| `delete_message(message_id)` | `delete_message` | `message_id: str` | Recall/Delete message |

> **Sending Messages** (`send_message`) is handled by `Raw_ob12` in `SendDSL` and is not repeated in `ApiDSL`.

### 3.4 File Operations

| Method | OB12 Action | Params | data Return |
|--------|-------------|--------|-------------|
| `upload_file(*, type, name, ...)` | `upload_file` | `type`, `name`, `url`/`path`/`data`, `headers?`, `sha256?` | `file_id` |
| `get_file(file_id, type)` | `get_file` | `file_id: str`, `type: str` | `name`, `url`/`path`/`data` |

`upload_file` `type` parameter:
- `"url"`: Upload via URL (must provide `url`)
- `"path"`: Upload via local path (must provide `path`)
- `"data"`: Upload via binary data (must provide `data`)

### 3.5 General Extension Actions

| Method | Note |
|--------|------|
| `call(action, **params)` | Escape hatch for platform extension actions, following OB12 extension naming rules `{prefix}.{action}` |

## 4. Usage

### 4.1 Basic Call

```python
from ErisPulse import adapter

# Get user info (Cross-platform unified)
result = await adapter.myplatform.Api.get_user_info("123456")
if result["status"] == "ok":
    user_name = result["data"]["user_name"]
    print(f"User Name: {user_name}")

# Get group list
result = await adapter.myplatform.Api.get_group_list()
groups = result["data"]

# Recall message
await adapter.myplatform.Api.delete_message("msg_123456")
```

### 4.2 Specify Bot Account (Multi-account mode)

```python
# Execute operations using a specific Bot account
info = await adapter.myplatform.Api.Using("bot1").get_self_info()
```

### 4.3 Platform Extension Actions

```python
# Call platform-specific extension actions (recommended using {prefix}.{action} naming)
result = await adapter.telegram.Api.call(
    "telegram.send_sticker",
    sticker_id="CAACAgIAAxkBAA...",
)
```

### 4.4 In Event Handlers

```python
from ErisPulse.Core.Event import message

@message()
async def handle(event):
    # Get sender detailed info
    user_id = event.get_user_id()
    platform = event.get_platform()

    result = await getattr(adapter, platform).Api.get_user_info(user_id)
    if result["status"] == "ok":
        user_name = result["data"]["user_name"]
        await event.reply(f"Hello, {user_name}!")
```

## 5. Adapter Implementation

### 5.1 Default Behavior (Zero Configuration)

The default implementation of `ApiDSL` passes the standard action name directly to `adapter.call_api()`:

```python
# ApiDSL default implementation is equivalent to:
async def get_user_info(self, user_id: str) -> dict:
    return await self._adapter.call_api("get_user_info", user_id=user_id, account_id=self._account_id)
```

**适用场景**：The adapter backend is itself a OneBot12 implementation (e.g., NapCat, Lagrange), and `call_api` natively supports standard action names.

### 5.2 Override Standard Methods (Map to Platform Native API)

Adapters can override individual standard methods to map them to platform native APIs:

```python
class MyAdapter(BaseAdapter):

    class Api(BaseAdapter.Api):
        """MyPlatform Standard API Action Implementation"""

        async def get_user_info(self, user_id: str) -> dict:
            # Map to platform native API
            raw = await self._adapter._request("GET", f"/users/{user_id}")
            if raw.get("code") != 0:
                return self._adapter.make_error(retcode=34001, message="User not found")

            user = raw["data"]
            return self._adapter.make_response(
                data={
                    "user_id": str(user["id"]),
                    "user_name": user.get("nick", ""),
                    "user_displayname": user.get("display_name", ""),
                    "user_remark": user.get("remark", ""),
                },
                raw=raw,
            )

        async def get_friend_list(self) -> dict:
            raw = await self._adapter._request("GET", "/friends")
            friends = [
                {
                    "user_id": str(u["id"]),
                    "user_name": u.get("nick", ""),
                    "user_displayname": u.get("display_name", ""),
                    "user_remark": u.get("remark", ""),
                }
                for u in raw.get("data", [])
            ]
            return self._adapter.make_response(data=friends, raw=raw)
```

### 5.3 Unsupported Actions

Standard methods not covered by the adapter go to the default implementation (delegated to `call_api`). If `call_api` also does not support the action, it should return a standard error response:

```python
async def call_api(self, endpoint: str, **params):
    if endpoint not in self._supported_endpoints:
        return self.make_error(retcode=10002, message=f"Unsupported action: {endpoint}")
    # ... Platform API call
```

Module developers can determine support via the `retcode` in the return value:

```python
result = await adapter.myplatform.Api.get_friend_list()
if result["retcode"] == 10002:
    print("This platform does not support getting friend list")
```

## 6. Response Format

All `ApiDSL` methods return the standard API response format (see [API Response Standard](docs/en/api-response.md)):

```json
{
    "status": "ok",
    "retcode": 0,
    "data": { ... },
    "message_id": "",
    "message": "",
    "myplatform_raw": { ... }
}
```

> **注意**：For info query actions, `message_id` is an empty string (only message sending actions have `message_id`).

## 7. Relationship with SendDSL / RequestDSL

| Scenario | Use DSL | Example |
|----------|---------|---------|
| Sending messages | `Send` | `adapter.Send.To("group", "123").Text("hi")` |
| Accept/Reject request | `Request` | `adapter.Request("req_id").accept()` |
| Get User/Group info | `Api` | `adapter.Api.get_user_info("123")` |
| Recall message | `Api` | `adapter.Api.delete_message("msg_id")` |
| Leave group | `Api` | `adapter.Api.leave_group("group_id")` |

## 8. Adapter Implementation Checklist

### Standard Actions
- [ ] `call_api` can handle standard action names (or override corresponding `ApiDSL` methods)
- [ ] Unsupported actions return `retcode=10002`
- [ ] Return values follow standard API response format
- [ ] `data` field contains OB12 standard defined fields

### Extension Actions
- [ ] Platform extension actions use `{prefix}.{action}` naming
- [ ] Extension action parameters and responses still follow OB12 action request/response structure

## 9. Related Documentation

- [API Response Standard](docs/en/api-response.md) - Adapter API response format standard
- [Sending Method Specification](docs/en/send-method-spec.md) - Send class method naming and parameter specification
- [Request Operation Specification](docs/en/request-action-spec.md) - Usage of Request DSL
- [Event Conversion Standard](docs/en/event-conversion.md) - Event format and message segment standards