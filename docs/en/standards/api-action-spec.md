# ErisPulse API Action Standard

> [!TIP]
> **When to read this**: When implementing Api DSL standard actions in an adapter (get_user_info / delete_message, etc.), or calling these standard actions cross-platform in a module and needing to confirm parameters and data fields. Skip it if you don't need it.

This document defines the unified interface specification for **OneBot12 standard API actions** in ErisPulse adapters, allowing module developers to program against a standard interface while adapters are responsible for mapping to platform-native APIs.

> **Scope**: Among the OneBot12 standard actions, `ApiDSL` provides strongly typed methods for user /
> group / guild / message management / Meta regular interfaces (`send_message` is
> handled by `SendDSL.Raw_ob12`). File resource actions (`upload_file` / `get_file` / fragmented) are
> retained only as degraded pass-through, see §3.5. Platform extension actions are invoked through
> the `Api.call("prefix.action", ...)` escape hatch. Action parameters and return structures follow
> the OneBot12 specification (`onebot/specs/interface/` in the repository).

## 1. Design Background

In ErisPulse, message segments (message send/receive) and event formats already fully follow the OneBot12 standard, but **API action calls** (such as getting user info, getting group lists, recalling messages, etc.) were previously not unified—module developers had to write different `call_api` calls for each platform.

`ApiDSL` solves this problem by providing strongly typed standard action methods:

```
Module code (cross-platform unified)       Adapter implementation (platform-specific)
─────────────────              ──────────────────
adapter.Api.get_user_info("123")  →  adapter call_api / override
adapter.Api.get_group_list()      →  adapter call_api / override
adapter.Api.delete_message("id")  →  adapter call_api / override
```

## 2. Three Parallel DSL Classes

ErisPulse adapters have three parallel DSL inner classes, each with its own responsibility:

```
BaseAdapter
├── Send(SendDSL)       ← Message sending (Text/Image/Raw_ob12)
├── Request(RequestDSL)  ← Request operations (accept/reject)
└── Api(ApiDSL)          ← Standard API actions (user/group/guild/message management/file/meta) ★
```

| DSL | Responsibility | Method Style | Return Value |
|-----|------|---------|--------|
| `Send` | Send messages | Chained + `asyncio.Task` | Standard response |
| `Request` | Handle request events | `asyncio.Task` | Standard response |
| `Api` | Query/management operations | `async` methods | Standard response |

## 3. Standard Action List

### 3.1 User-Related

| Method | OB12 Action | Parameters | data Return |
|------|----------|------|----------|
| `get_self_info()` | `get_self_info` | None | `user_id`, `user_name`, `user_displayname` |
| `get_user_info(user_id)` | `get_user_info` | `user_id: str` | `user_id`, `user_name`, `user_displayname`, `user_remark` |
| `get_friend_list()` | `get_friend_list` | None | `list[get_user_info response]` |

### 3.2 Group-Related

| Method | OB12 Action | Parameters | data Return |
|------|----------|------|----------|
| `get_group_info(group_id)` | `get_group_info` | `group_id: str` | `group_id`, `group_name` |
| `get_group_list()` | `get_group_list` | None | `list[get_group_info response]` |
| `get_group_member_info(group_id, user_id)` | `get_group_member_info` | `group_id: str`, `user_id: str` | `user_id`, `user_name`, `user_displayname` |
| `get_group_member_list(group_id)` | `get_group_member_list` | `group_id: str` | `list[get_group_member_info response]` |
| `set_group_name(group_id, group_name)` | `set_group_name` | `group_id: str`, `group_name: str` | None |
| `leave_group(group_id)` | `leave_group` | `group_id: str` | None |

### 3.3 Message Management

| Method | OB12 Action | Parameters | Description |
|------|----------|------|------|
| `delete_message(message_id)` | `delete_message` | `message_id: str` | Recall/delete a message |

> **Message sending** (`send_message`) is handled by `SendDSL`'s `Raw_ob12` and is not duplicated in `ApiDSL`.

### 3.4 Guild-Related

The OneBot12 guild system has two levels: **guild** and **channel**.

| Method | OB12 Action | Parameters | data Return |
|------|----------|------|----------|
| `get_guild_info(guild_id)` | `get_guild_info` | `guild_id: str` | `guild_id`, `guild_name` |
| `get_guild_list()` | `get_guild_list` | None | `list[get_guild_info response]` |
| `set_guild_name(guild_id, guild_name)` | `set_guild_name` | `guild_id: str`, `guild_name: str` | None |
| `get_guild_member_info(guild_id, user_id)` | `get_guild_member_info` | `guild_id: str`, `user_id: str` | `user_id`, `user_name`, `user_displayname` |
| `get_guild_member_list(guild_id)` | `get_guild_member_list` | `guild_id: str` | `list[get_guild_member_info response]` |
| `leave_guild(guild_id)` | `leave_guild` | `guild_id: str` | None |
| `get_channel_info(guild_id, channel_id)` | `get_channel_info` | `guild_id: str`, `channel_id: str` | `channel_id`, `channel_name` |
| `get_channel_list(guild_id, *, joined_only)` | `get_channel_list` | `guild_id: str`, `joined_only: bool=false` | `list[get_channel_info response]` |
| `set_channel_name(guild_id, channel_id, channel_name)` | `set_channel_name` | `guild_id`, `channel_id`, `channel_name` | None |
| `get_channel_member_info(guild_id, channel_id, user_id)` | `get_channel_member_info` | `guild_id`, `channel_id`, `user_id` | `user_id`, `user_name`, `user_displayname` |
| `get_channel_member_list(guild_id, channel_id)` | `get_channel_member_list` | `guild_id`, `channel_id` | `list[get_channel_member_info response]` |
| `leave_channel(guild_id, channel_id)` | `leave_channel` | `guild_id`, `channel_id` | None |

> The guild system and groups are independent of each other: platforms such as Discord / QQ Guild / Kook implement the guild interfaces, while traditional QQ / WeChat implement the group interfaces; both may exist simultaneously or only one of them.

### 3.5 File Resource Operations

> [!WARNING]
> **The file resource model (two-stage file_id) is "degraded availability" in ErisPulse**:
> File send/receive in ErisPulse does not follow the "upload first to get a file_id, then reference it" model—modules send files with
> `SendDSL.File(file, filename)` (URL / path / bytes are **transmitted directly at send time**, see the
> [Send Method Specification](send-method-spec.md)).
> The `upload_file` / `get_file` / fragmented actions in this section depend on platform-specific `file_id` file resource
> capabilities, which are **not general-purpose**; pass-through is only possible when the adapter backend natively has this capability. The framework's built-in
> adapters **neither implement nor recommend implementing** them; calls typically return `retcode=10002`.
> When a module needs to transfer files cross-platform, use `SendDSL.File` and do not rely on file_id.
>
> **Outlook**: Standardizing the `file_id` resource model at the framework layer is a future direction; the current version does not provide it.

Whole-file transfer (small files):

| Method | OB12 Action | Parameters | data Return |
|------|----------|------|----------|
| `upload_file(*, type, name, ...)` | `upload_file` | `type`, `name`, `url`/`path`/`data`, `headers?`, `sha256?` | `file_id` |
| `get_file(file_id, type)` | `get_file` | `file_id: str`, `type: str` | `name`, `url`/`path`/`data` |

The `type` parameter of `upload_file`:
- `"url"`: Upload via URL (requires `url`)
- `"path"`: Upload via local path (requires `path`)
- `"data"`: Upload via binary data (requires `data`)

#### 3.5.1 Fragmented Transfer (Large Files, Within the Above Degraded Scope)

OneBot12 fragmented actions distinguish phases by `stage`. `ApiDSL` splits the three/two phases of the same action into independent methods
(`offset` is a byte offset, and `data` is Base64 in JSON); the tables below are retained for reference only, and adapters need not and should not be forced to implement them:

**Three-step fragmented upload**: `prepare` → `transfer` (loop chunk by chunk) → `finish`

| Method | Corresponding stage | Parameters | data Return |
|------|-----------|------|----------|
| `upload_file_fragmented_prepare(name, total_size)` | `prepare` | `name: str`, `total_size: int` | `file_id` (used during transfer) |
| `upload_file_fragmented_transfer(file_id, offset, data)` | `transfer` | `file_id`, `offset: int`, `data: bytes` | None |
| `upload_file_fragmented_finish(file_id, sha256)` | `finish` | `file_id`, `sha256: str` (whole-file checksum) | `file_id` |

```python
total = os.path.getsize(path)
r = await adapter.Api.upload_file_fragmented_prepare(os.path.basename(path), total)
fid = r["data"]["file_id"]
offset = 0
with open(path, "rb") as f:
    while chunk := f.read(65536):
        await adapter.Api.upload_file_fragmented_transfer(fid, offset, chunk)
        offset += len(chunk)
sha256 = hashlib.sha256(open(path, "rb").read()).hexdigest()
await adapter.Api.upload_file_fragmented_finish(fid, sha256)
```

**Two-step fragmented download**: `prepare` → `transfer` (loop fetching chunks)

| Method | Corresponding stage | Parameters | data Return |
|------|-----------|------|----------|
| `get_file_fragmented_prepare(file_id)` | `prepare` | `file_id` | `name`, `total_size`, `sha256` |
| `get_file_fragmented_transfer(file_id, offset, size)` | `transfer` | `file_id`, `offset: int`, `size: int` | `data` (bytes of the current chunk) |

### 3.6 Meta Actions

Meta actions do not target a specific account and do not require `Using()` to specify a Bot.

| Method | OB12 Action | Parameters | data Return |
|------|----------|------|----------|
| `get_latest_events(limit, timeout)` | `get_latest_events` | `limit: int=0`, `timeout: int=0` | Array of event objects (excluding meta events) |
| `get_supported_actions()` | `get_supported_actions` | None | `list[str]` of supported action names |
| `get_status()` | `get_status` | None | `good: bool`, `bots: list[{self, online, ...}]` |
| `get_version()` | `get_version` | None | `impl`, `version`, `onebot_version` |

### 3.7 Generic Extension Actions

| Method | Description |
|------|------|
| `call(action, **params)` | Escape hatch for platform extension actions, following the OB12 extension naming rule `{prefix}.{action}` |

## 4. Usage

### 4.1 Basic Calls

```python
from ErisPulse import adapter

# Get user info (cross-platform unified)
result = await adapter.myplatform.Api.get_user_info("123456")
if result["status"] == "ok":
    user_name = result["data"]["user_name"]
    print(f"Username: {user_name}")

# Get group list
result = await adapter.myplatform.Api.get_group_list()
groups = result["data"]

# Recall a message
await adapter.myplatform.Api.delete_message("msg_123456")
```

### 4.2 Specifying a Bot Account (Multi-Account Mode)

```python
# Execute operations with a specified Bot account
info = await adapter.myplatform.Api.Using("bot1").get_self_info()
```

### 4.3 Platform Extension Actions

```python
# Call a platform-specific extension action (use the {prefix}.{action} naming convention)
result = await adapter.telegram.Api.call(
    "telegram.send_sticker",
    sticker_id="CAACAgIAAxkBAA...",
)
```

### 4.4 Use in Event Handlers

```python
from ErisPulse.Core.Event import message

@message()
async def handle(event):
    # Get detailed sender info
    user_id = event.get_user_id()
    platform = event.get_platform()

    result = await getattr(adapter, platform).Api.get_user_info(user_id)
    if result["status"] == "ok":
        user_name = result["data"]["user_name"]
        await event.reply(f"Hello, {user_name}!")
```

## 5. Adapter Implementation

### 5.1 Default Behavior (Zero Configuration)

The default implementation of `ApiDSL` passes the standard action name directly to `adapter.call_api()` as the `endpoint`:

```python
# The ApiDSL default implementation is equivalent to:
async def get_user_info(self, user_id: str) -> dict:
    return await self._adapter.call_api("get_user_info", user_id=user_id, account_id=self._account_id)
```

**Applicable scenario**: When the adapter's underlying backend itself follows the OneBot12 standard action protocol, `call_api` naturally supports standard action names (e.g., when directly connecting to a server that follows this protocol).

### 5.2 Overriding Standard Methods (Mapping to Platform-Native APIs)

An adapter can override individual standard methods, mapping them to platform-native APIs:

```python
class MyAdapter(BaseAdapter):

    class Api(BaseAdapter.Api):
        """MyPlatform standard API action implementation"""

        async def get_user_info(self, user_id: str) -> dict:
            # Map to platform-native API
            raw = await self._adapter._request("GET", f"/users/{user_id}")
            if raw.get("code") != 0:
                # Platform-side error: use the 341xx–345xx range for the custom low three digits (346xx is reserved by the framework, do not use)
                return self._adapter.make_error(retcode=34400, message="User not found")

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

Standard methods not overridden by the adapter use the default implementation (delegating to `call_api`). If `call_api` also does not support the action, it should return a standard error response:

```python
async def call_api(self, endpoint: str, **params):
    if endpoint not in self._supported_endpoints:
        return self.make_error(retcode=10002, message=f"Unsupported action: {endpoint}")
    # ... platform API call
```

Module developers can check the `retcode` in the return value to determine whether an action is supported:

```python
result = await adapter.myplatform.Api.get_friend_list()
if result["retcode"] == 10002:
    print("This platform does not support getting the friend list")
```

## 6. Response Format

All `ApiDSL` methods return the standard API response format (see the [API Response Standard](api-response.md) for details):

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

> **Note**: For information-query actions, `message_id` is an empty string (only message-sending actions have a `message_id`).

## 7. Relationship with SendDSL / RequestDSL

| Scenario | DSL to Use | Example |
|------|---------|------|
| Send a message | `Send` | `adapter.Send.To("group", "123").Text("hi")` |
| Accept/reject a request | `Request` | `adapter.Request("req_id").accept()` |
| Get user/group info | `Api` | `adapter.Api.get_user_info("123")` |
| Recall a message | `Api` | `adapter.Api.delete_message("msg_id")` |
| Leave a group | `Api` | `adapter.Api.leave_group("group_id")` |

## 8. Adapter Implementation Checklist

### Standard Actions
- [ ] `call_api` can handle standard action names (or override the corresponding `ApiDSL` methods)
- [ ] Unsupported actions return `retcode=10002`
- [ ] Return values follow the standard API response format
- [ ] The `data` field contains the fields defined by the OB12 standard
- [ ] Guild platforms must implement `get_guild_*` / `get_channel_*` / `leave_guild` / `leave_channel`
- [ ] Meta actions (`get_status` / `get_version` / `get_supported_actions`) are recommended to be implemented
- [ ] **File send/receive uses `SendDSL.File` (direct transmission)**; file resource actions (upload_file/get_file/fragmented) are **not mandatory to implement**; pass-through is only needed when the backend has `file_id` resource capability

### Extension Actions
- [ ] Platform extension actions use the `{prefix}.{action}` naming convention
- [ ] Extension action parameters and responses still follow the OB12 action request/response structure

## 9. Related Documents

**Companion reference when implementing Api DSL return values**:
- [API Response Standard](api-response.md) - Adapter API response format standard

**Other DSLs of the same adapter**:
- [Send Method Specification](send-method-spec.md) - Method naming and parameter specification for the Send class
- [Request Action Specification](request-action-spec.md) - How to use the Request DSL

**Event-side companion**:
- [Event Conversion Standard](event-conversion.md) - Event format and message segment standard