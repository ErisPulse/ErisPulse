# ErisPulse API Action Standard

This document defines the unified interface specification for **OneBot12 Standard API Actions** in ErisPulse adapters, enabling module developers to program against standard interfaces, with adapters responsible for mapping to platform-native APIs.

> **Scope**: In OneBot12 standard actions, `ApiDSL` provides strongly-typed methods for user/group/channel/message management/meta general interfaces (with `send_message` handled by `SendDSL.Raw_ob12`). File resource actions (`upload_file` / `get_file` / chunked) are retained only as degraded pass-through, see §3.5 for details. Platform extension actions are invoked via `Api.call("prefix.action", ...)` escape hatch. Action parameters and return structures follow the OneBot12 specification (located in `onebot/specs/interface/` in the repository).

## 1. Design Background

In ErisPulse, message segments (message send/receive) and event formats already fully conform to the OneBot12 standard, but **API action calls** (such as retrieving user information, group list, or deleting messages) were previously inconsistent—module developers had to write different `call_api` calls for each platform.

`ApiDSL` resolves this issue by providing strongly-typed standard action methods:

```
Module Code (Cross-Platform Consistency)       Adapter Implementation (Platform-Specific)
───────────────────────────────────────        ────────────────────────────────────────
adapter.Api.get_user_info("123")  →  Adapter call_api / Override
adapter.Api.get_group_list()      →  Adapter call_api / Override
adapter.Api.delete_message("id")  →  Adapter call_api / Override
```

## 2. Three Parallel DSL Structures

ErisPulse adapters have three parallel internal DSL classes, each with distinct responsibilities:

```
BaseAdapter
├── Send(SendDSL)       ← Message Sending (Text/Image/Raw_ob12)
├── Request(RequestDSL)  ← Request Handling (accept/reject)
└── Api(ApiDSL)          ← Standard API Actions (Users/Groups/Channels/Message Management/File/Meta) ★
```

| DSL | Responsibility | Method Style | Return Value |
|-----|----------------|--------------|--------------|
| `Send` | Sending Messages | Chained + `asyncio.Task` | Standard Response |
| `Request` | Handling Request Events | `asyncio.Task` | Standard Response |
| `Api` | Query/Management Operations | `async` Methods | Standard Response |

## 3. Standard Action List

### 3.1 User-Related

| Method | OB12 Action | Parameters | data Return |
|--------|-------------|------------|-------------|
| `get_self_info()` | `get_self_info` | None | `user_id`, `user_name`, `user_displayname` |
| `get_user_info(user_id)` | `get_user_info` | `user_id: str` | `user_id`, `user_name`, `user_displayname`, `user_remark` |
| `get_friend_list()` | `get_friend_list` | None | `list[get_user_info response]` |

### 3.2 Group-Related

| Method | OB12 Action | Parameters | data Return |
|--------|-------------|------------|-------------|
| `get_group_info(group_id)` | `get_group_info` | `group_id: str` | `group_id`, `group_name` |
| `get_group_list()` | `get_group_list` | None | `list[get_group_info response]` |
| `get_group_member_info(group_id, user_id)` | `get_group_member_info` | `group_id: str`, `user_id: str` | `user_id`, `user_name`, `user_displayname` |
| `get_group_member_list(group_id)` | `get_group_member_list` | `group_id: str` | `list[get_group_member_info response]` |
| `set_group_name(group_id, group_name)` | `set_group_name` | `group_id: str`, `group_name: str` | None |
| `leave_group(group_id)` | `leave_group` | `group_id: str` | None |

### 3.3 Message Management

| Method | OB12 Action | Parameters | Description |
|--------|-------------|------------|-------------|
| `delete_message(message_id)` | `delete_message` | `message_id: str` | Recall/Delete Message |

> **Sending Messages** (`send_message`) is handled by `SendDSL`'s `Raw_ob12`, and is not repeated in `ApiDSL`.

### 3.4 Channel (Guild) Related

OneBot12 channel system is hierarchical: **channel (guild)** and **sub-channel (channel)**.

| Method | OB12 Action | Parameters | data Return |
|--------|-------------|------------|-------------|
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

> The channel system is independent from the group system: platforms such as Discord, QQ channels, and Kook implement channel interfaces, while traditional platforms like QQ and WeChat implement group interfaces. Both can coexist or exist independently.

### 3.5 File Resource Operations

> [!WARNING]
> **File resource model (two-segment file_id) is "degraded and available" in ErisPulse**: ErisPulse does not use the "upload first, then reference by file_id" model for file sending/receiving—modules send files using `SendDSL.File(file, filename)` (URL/path/bytes are directly transmitted at send time, see [Send Method Specification](send-method-spec.md)). This section's `upload_file` / `get_file` / chunked actions depend on platform-specific `file_id` file resource capabilities, which are **not universally applicable**; only when the adapter backend naturally supports this capability should it be passed through. Framework-built adapters **do not implement or recommend implementing** this, and calls typically return `retcode=10002`. When modules need to transfer files cross-platform, please use `SendDSL.File` instead of relying on file_id.
>
> **Outlook**: Standardizing the `file_id` resource model to the framework layer is a future direction, but is not provided in the current version.

**Whole-file transfer (small files):**

| Method | OB12 Action | Parameters | data Return |
|--------|-------------|------------|-------------|
| `upload_file(*, type, name, ...)` | `upload_file` | `type`, `name`, `url`/`path`/`data`, `headers?`, `sha256?` | `file_id` |
| `get_file(file_id, type)` | `get_file` | `file_id: str`, `type: str` | `name`, `url`/`path`/`data` |

The `type` parameter of `upload_file`:
- `"url"`: Upload via URL (must provide `url`)
- `"path"`: Upload via local path (must provide `path`)
- `"data"`: Upload via binary data (must provide `data`)

#### 3.5.1 Chunked Transfer (Large Files, Part of the Above Degraded Scope)

OneBot12 chunked actions distinguish stages by `stage`. `ApiDSL` splits the three/two stages of the same action into independent methods (`offset` is byte offset, `data` in JSON is Base64); the following table is for reference only—adapters do not need to or should not force implementation:

**Three-step chunked upload**: `prepare` → `transfer` (loop through chunks) → `finish`

| Method | Corresponding stage | Parameters | data Return |
|--------|---------------------|------------|-------------|
| `upload_file_fragmented_prepare(name, total_size)` | `prepare` | `name: str`, `total_size: int` | `file_id` (used during transfer) |
| `upload_file_fragmented_transfer(file_id, offset, data)` | `transfer` | `file_id`, `offset: int`, `data: bytes` | None |
| `upload_file_fragmented_finish(file_id, sha256)` | `finish` | `file_id`, `sha256: str` (full file checksum) | `file_id` |

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

**Two-step chunked download**: `prepare` → `transfer` (loop to fetch chunks)

| Method | Corresponding stage | Parameters | data Return |
|--------|---------------------|------------|-------------|
| `get_file_fragmented_prepare(file_id)` | `prepare` | `file_id` | `name`, `total_size`, `sha256` |
| `get_file_fragmented_transfer(file_id, offset, size)` | `transfer` | `file_id`, `offset: int`, `size: int` | `data` (this chunk's bytes) |

### 3.6 Meta Actions

Meta actions are not account-specific and do not require `Using()` to specify a Bot.

| Method | OB12 Action | Parameters | data Return |
|--------|-------------|------------|-------------|
| `get_latest_events(limit, timeout)` | `get_latest_events` | `limit: int=0`, `timeout: int=0` | Array of event objects (excluding meta events) |
| `get_supported_actions()` | `get_supported_actions` | None | `list[str]` supported action names |
| `get_status()` | `get_status` | None | `good: bool`, `bots: list[{self, online, ...}]` |
| `get_version()` | `get_version` | None | `impl`, `version`, `onebot_version` |

### 3.7 General Extension Actions

| Method | Description |
|--------|-------------|
| `call(action, **params)` | Escape hatch for platform extension actions, following OB12 extension naming rules `{prefix}.{action}` |

## 4. Usage

### 4.1 Basic Calls

```python
from ErisPulse import adapter

# Get user information (cross-platform consistency)
result = await adapter.myplatform.Api.get_user_info("123456")
if result["status"] == "ok":
    user_name = result["data"]["user_name"]
    print(f"Username: {user_name}")

# Get group list
result = await adapter.myplatform.Api.get_group_list()
groups = result["data"]

# Delete message
await adapter.myplatform.Api.delete_message("msg_123456")
```

### 4.2 Specifying Bot Account (Multi-account Mode)

```python
# Execute operation using a specific Bot account
info = await adapter.myplatform.Api.Using("bot1").get_self_info()
```

### 4.3 Platform Extension Actions

```python
# Call platform-specific extension actions (suggest using {prefix}.{action} naming)
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
    # Get sender's detailed information
    user_id = event.get_user_id()
    platform = event.get_platform()

    result = await getattr(adapter, platform).Api.get_user_info(user_id)
    if result["status"] == "ok":
        user_name = result["data"]["user_name"]
        await event.reply(f"Hello, {user_name}!")
```

## 5. Adapter Implementation

### 5.1 Default Behavior (Zero Configuration)

The default implementation of `ApiDSL` passes the standard action name as `endpoint` directly to `adapter.call_api()`:

```python
# ApiDSL default implementation is equivalent to:
async def get_user_info(self, user_id: str) -> dict:
    return await self._adapter.call_api("get_user_info", user_id=user_id, account_id=self._account_id)
```

**Applicable Scenarios**: When the adapter's underlying backend itself conforms to the OneBot12 standard action protocol, `call_api` naturally supports standard action names (e.g., directly interfacing with a service that follows this protocol).

### 5.2 Overriding Standard Methods (Mapping to Platform Native API)

Adapters can override individual standard methods to map them to platform-native APIs:

```python
class MyAdapter(BaseAdapter):

    class Api(BaseAdapter.Api):
        """MyPlatform standard API action implementation"""

        async def get_user_info(self, user_id: str) -> dict:
            # Map to platform-native API
            raw = await self._adapter._request("GET", f"/users/{user_id}")
            if raw.get("code") != 0:
                return self._adapter.make_error(retcode=34600, message="User does not exist")

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

Standard methods not overridden by the adapter use the default implementation (delegated to `call_api`). If `call_api` does not support the action, it should return a standard error response:

```python
async def call_api(self, endpoint: str, **params):
    if endpoint not in self._supported_endpoints:
        return self.make_error(retcode=10002, message=f"Unsupported action: {endpoint}")
    # ... platform API call
```

Module developers can determine support by checking the `retcode` in the return value:

```python
result = await adapter.myplatform.Api.get_friend_list()
if result["retcode"] == 10002:
    print("This platform does not support retrieving friend list")
```

## 6. Response Format

All `ApiDSL` methods return the standard API response format (see [API Response Standard](api-response.md)):

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

> **Note**: For information query actions, `message_id` is an empty string (only message sending actions have `message_id`).

## 7. Relationship with SendDSL / RequestDSL

| Scenario | Use DSL | Example |
|----------|---------|---------|
| Sending Messages | `Send` | `adapter.Send.To("group", "123").Text("hi")` |
| Accept/Reject Requests | `Request` | `adapter.Request("req_id").accept()` |
| Get User/Group Info | `Api` | `adapter.Api.get_user_info("123")` |
| Delete Message | `Api` | `adapter.Api.delete_message("msg_id")` |
| Leave Group | `Api` | `adapter.Api.leave_group("group_id")` |

## 8. Adapter Implementation Checklist

### Standard Actions
- [ ] `call_api` can handle standard action names (or override corresponding `ApiDSL` methods)
- [ ] Unsupported actions return `retcode=10002`
- [ ] Return values follow the standard API response format
- [ ] `data` field contains fields defined in the OB12 standard
- [ ] Channel platform must implement `get_guild_*` / `get_channel_*` / `leave_guild` / `leave_channel`
- [ ] Meta actions (`get_status` / `get_version` / `get_supported_actions`) are recommended to be implemented
- [ ] **File sending uses `SendDSL.File` (direct upload)**; file resource actions (`upload_file`/`get_file`/chunked) **are not mandatory**, only required when the backend has `file_id` resource capability

### Extension Actions
- [ ] Platform extension actions use `{prefix}.{action}` naming
- [ ] Extension action parameters and responses still follow the OB12 action request/response structure

## 9. Related Documents

- [API Response Standard](api-response.md) - Standard response format for adapter API
- [Send Method Specification](send-method-spec.md) - Naming and parameter conventions for Send class methods
- [Request Action Specification](request-action-spec.md) - Usage of Request DSL
- [Event Conversion Standard](event-conversion.md) - Event format and message segment standards