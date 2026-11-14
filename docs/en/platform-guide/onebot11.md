# OneBot11 Platform Feature Documentation

OneBot11Adapter is an adapter built based on the OneBot V11 protocol.

---

## Document Information

- Corresponding Module Version: 4.6.2
- Maintainer: ErisPulse
- Last Updated: 2026-11-10

## Basic Information

- Platform Overview: OneBot is a standard for chatbot application interfaces
- Adapter Name: OneBotAdapter
- Supported Protocol/API Version: OneBot V11
- Multi-Account Support: Default multi-account architecture, supports simultaneous configuration and operation of multiple OneBot accounts
- Configuration Key Name: `OneBotAdapter`

## v5 Paradigm Update (from 4.3.0)

This adapter has completed alignment with the v5 paradigm (incremental upgrade, API compatible):

- **BaseConverter Inheritance**: Common fields of converters (id/time/platform/self/raw) are built by the framework build_base_event, and are overridden by OB11 field names (echo/time/self_id)
- **spawn_background Task Ownership**: Client mode connection tasks are changed to use Runtime.spawn_background (owner ownership, automatic shutdown recovery)
- **Framework Soft Dependency**: Installing the adapter no longer declares a hard dependency on ErisPulse, avoiding pip parsing to adjust the framework version; runtime detection of ErisPulse>=2.7.1 and logging a warning when the version is too low
- **Startup Version Log**: Outputs OneBotAdapter vX.Y.Z loaded during initialization

Existing capabilities (supported since 4.2.0): Multi-account, standard action mapping of Api DSL (get_self_info→get_login_info, etc.), Request DSL (friend/group request approval: event.approve() / event.reject()), EventMixin, i18n.

Since 4.3.1, request event handling is implemented according to the specification, see the following [Standardization Alignment](#standardization-alignment) section.

---

## Standard API Actions (Api DSL)

The adapter automatically maps OneBot12 standard action names to OB11 action names, allowing modules to call them uniformly across platforms:

| OB12 Standard Action | OB11 Action | Description |
|----------------------|-------------|-------------|
| get_self_info        | get_login_info | Standardized fields: user_id/user_name/user_displayname |
| get_user_info        | get_stranger_info | Standardized fields |
| delete_message       | delete_msg  | Recall message |
| leave_group          | set_group_leave | Leave group |
| get_friend_list      | get_friend_list | Action name consistent, default pass-through |
| get_group_info       | get_group_info | Action name consistent, default pass-through |
| upload_file          | upload_group_file / upload_private_file | Extended group_id/user_id optional parameters, filetype automatically detects type routing |

### Basic Usage

```python
from ErisPulse import sdk
onebot = sdk.adapter.get("onebot11")

# Get bot information
result = await onebot.Api.get_self_info()
print(result["data"]["user_id"], result["data"]["user_name"])

# Recall message
await onebot.Api.delete_message(message_id=123456)

# Upload group file (filetype automatically detects type routing to upload_group_file)
result = await onebot.Api.upload_file(group_id=123456, file="/path/to/file.zip")

# Specify account (multi-account)
result = await onebot.Api.Using("main").get_self_info()

# Unmapped OB11 actions are called via the call() escape hatch (NapCat/Lagrange common extensions)
result = await onebot.Api.call("send_poke", group_id=123, user_id=456)
```

### OB11 Protocol Extensions (NapCat/go-cqhttp/SnowLuma Common)

Frequently used extension actions have been encapsulated into typed methods (`OB11ExtensionApi` mixin), supporting IDE completion:

```python
await onebot.Api.send_poke(user_id=789, group_id=123456)
await onebot.Api.set_msg_emoji_like(message_id=123, emoji_id="76")
await onebot.Api.mark_msg_as_read(group_id=123456)
result = await onebot.Api.get_group_msg_history(group_id=123456, count=20)
await onebot.Api.set_essence_msg(message_id=123)
result = await onebot.Api.ocr_image(image="https://example.com/img.png")
```

> Extension actions use OB11 action names directly, without platform prefixes. Actions that are not encapsulated are called using `Api.call("action_name", ...)`.

### Send Query Methods (Deprecated)

The following Send methods are still available but marked as deprecated, it is recommended to use Api DSL instead:

| Send Method (Deprecated) | Api DSL Alternative |
|--------------------------|---------------------|
| `Send.GetLoginInfo()`    | `Api.get_self_info()` |
| `Send.GetFriendList()`   | `Api.get_friend_list()` |
| `Send.GetGroupInfo()`    | `Api.get_group_info(group_id)` |
| `Send.GetGroupList()`    | `Api.get_group_list()` |
| `Send.GetGroupMemberInfo(uid)` | `Api.get_group_member_info(gid, uid)` |
| `Send.GetGroupMemberList()` | `Api.get_group_member_list(gid)` |
| `Send.GetMsg(mid)`       | `Api.call("get_msg", message_id=mid)` |
| `Send.GetForwardMsg(id)` | `Api.call("get_forward_msg", id=id)` |

## Standardization Alignment

This section explains the adapter's alignment with ErisPulse standardization specifications. For specification details, refer to the SDK documentation "Request Operation Specification" (`docs/en/standards/request-action-spec.md`) and "API Response Specification" (`docs/en/standards/api-response.md`).

### Request Event Handling (from 4.3.1)

The adapter implements request event handling according to the request operation specification:

- **Context Retention**: The event entry maps `request_id` to `{request_type, sub_type, group_id, account, ts}` and caches it (TTL 3600 seconds, maximum 512 entries, cleared after successful request processing), for subsequent `accept()`/`reject()` routing
- **Endpoint Routing Priority**: `accept()`/`reject()` kwargs explicitly passed parameters (`request_type`/`sub_type`/`group_id` as reserved names) > event retained context > fallback friend endpoint (`set_friend_add_request`) and outputs WARNING
- **Group Invitation/Join Request**: When `request_type == "group"`, correctly routes to `set_group_add_request` (add group `sub_type="add"`, invite `sub_type="invite"`)
- **Deprecation Notice**: The method of specifying request type via private parameter `_request_type` before 4.3.1 is deprecated and will be ignored if passed

### call_api Error Handling

- When the account is not connected or the connection is closed, `call_api` no longer throws `ConnectionError`, but returns a standard failure response (`status="failed"`, `retcode=33001`)
- API call timeout also returns a standard failure response (`retcode=33001`)

### Account Field Dual Compatibility

- `call_api` accepts both standard field `account_id` and old field name `_account_id` (standard name takes precedence); framework ApiDSL automatically adapts, module code is recommended to use `account_id`
- Send DSL all methods read `send_context`: automatically uses the current event source account within the event chain, explicitly specified `Using()` account takes precedence

### Error Code Specification

| retcode | Meaning | Triggered Scenario |
|---------|---------|--------------------|
| 0 | Success | Action executed successfully |
| 33001 | Network Error | Account not connected, connection closed, API call timeout |
| 10002 | Unsupported Action | Called an unimplemented action |
| 10003 | Parameter Error | Missing required parameters |

> Platform raw response data is retained in the `onebot11_raw` field.

---

## Supported Message Sending Types

All send methods are implemented through chain syntax, for example:
```python
from ErisPulse.Core import adapter
onebot = adapter.get("onebot11")

# Send using the default account
await onebot.Send.To("group", group_id).Text("Hello World!")

# Send using a specific account
await onebot.Send.Using("main").To("group", group_id).Text("Message from main account")

# Chain modifiers: @user + reply
await onebot.Send.To("group", group_id).At(123456).Reply(msg_id).Text("Reply message")

# @all members
await onebot.Send.To("group", group_id).AtAll().Text("Announcement message")
```

### Basic Send Methods

- `.Text(text: str)`: Send plain text message.
- `.Image(file: Union[str, bytes], filename: str = "image.png")`: Send image (supports URL, Base64, or bytes).
- `.Voice(file: Union[str, bytes], filename: str = "voice.amr")`: Send voice message.
- `.Video(file: Union[str, bytes], filename: str = "video.mp4")`: Send video message.
- `.Face(id: Union[str, int])`: Send QQ emoticon.
- `.File(file: Union[str, bytes], filename: str = "file.dat")`: Send file (auto-detects type).
- `.Raw_ob12(message: List[Dict], **kwargs)`: Send OneBot12 formatted message (auto-converts to OB11).
- `.Recall(message_id: Union[str, int])`: Recall message.

### Group Operation Methods

The following methods must specify the target group via `To("group", group_id)` and execute operations within the group context:

- `.Kick(user_id, reject_add_request=False)`: Kick group member.
- `.Ban(user_id, duration=1800)`: Mute group member (in seconds), 0 means unmute.
- `.WholeBan(enable=True)`: Enable/disable group-wide mute.
- `.SetAdmin(user_id, enable=True)`: Set/unset group admin.
- `.SetCard(user_id, card="")`: Set group nickname.
- `.SetGroupName(name)`: Modify group name.
- `.Leave(is_dismiss=False)`: Leave group (group owner can dismiss).
- `.SetTitle(user_id, title="")`: Set group title.
- `.SetPortrait(file)`: Set group portrait.

### Query Methods

- `.GetMsg(message_id)`: Get message content.
- `.GetForwardMsg(id)`: Get forwarded message.
- `.GetLoginInfo()`: Get current login account information.
- `.GetFriendList()`: Get friend list.
- `.GetGroupInfo()`: Get group information (requires `To("group", group_id)`).
- `.GetGroupList()`: Get group list.
- `.GetGroupMemberInfo(user_id)`: Get group member information (requires `To("group", group_id)`).
- `.GetGroupMemberList()`: Get group member list (requires `To("group", group_id)`).

### Friend Operation Methods

- `.Like(user_id, times=1)`: Send friend like (maximum 10 times).

### Chain Modifier Methods (can be combined)

Chain modifier methods return `self`, supporting chained calls, must be called before the final send method:

- `.At(user_id: Union[str, int], name: str = None)`: @ specified user (can be called multiple times).
- `.AtAll()`: @ all members.
- `.Reply(message_id: Union[str, int])`: Reply to specified message.

### Chained Call Examples

```python
# Basic send
await onebot.Send.To("group", 123456).Text("Hello")

# @ single user
await onebot.Send.To("group", 123456).At(789012).Text("Hello")

# @ multiple users
await onebot.Send.To("group", 123456).At(111).At(222).At(333).Text("Hello everyone")

# Send OneBot12 formatted message
ob12_msg = [{"type": "text", "data": {"text": "Hello"}}]
await onebot.Send.To("group", 123456).Raw_ob12(ob12_msg)

# Like
await onebot.Send.Like(123456, times=10)

# Mute group member
await onebot.Send.To("group", 123456).Ban(789012, duration=3600)

# Unmute
await onebot.Send.To("group", 123456).Ban(789012, duration=0)

# Kick member
await onebot.Send.To("group", 123456).Kick(789012)

# Set group admin
await onebot.Send.To("group", 123456).SetAdmin(789012)

# Modify group name
await onebot.Send.To("group", 123456).SetGroupName("New group name")

# Get group info
result = await onebot.Send.To("group", 123456).GetGroupInfo()

# Specify account operation
await onebot.Send.Using("main").To("group", 123456).Ban(789012)
```

### Handling Unsupported Types

If an undefined send method is called, the adapter returns a text prompt:
```python
# Call an undefined method
await onebot.Send.To("group", 123456).SomeUnsupportedMethod(arg1, arg2)
# Actually sends: "[Unsupported send type] Method name: SomeUnsupportedMethod, Parameters: [...]"
```

## Request Operations (Request DSL)

The adapter provides a request operation DSL for handling friend and group requests (add group/invite) approval/rejection operations.

### Event Shortcut Methods

Request events support `event.approve()` and `event.reject()` shortcut methods, which internally automatically call the Request DSL:

```python
from ErisPulse.Core.Event import request

@request.on_friend_request()
async def handle_friend_request(event):
    comment = event.get("comment", "")

    if comment == "passphrase":
        await event.approve()
    else:
        await event.reject()

@request.on_group_request()
async def handle_group_request(event):
    group_id = event.get("group_id")
    await event.approve()
```

### Manually Calling Request DSL

```python
# Approve request
await onebot.Request("flag_string").accept()

# Reject request
await onebot.Request("flag_string").reject()

# Specify account operation
await onebot.Request("flag_string").Using("main").accept()
```

### Complete Example

```python
from ErisPulse.Core.Event import request

@request.on_friend_request()
async def handle_friend_request(event):
    comment = event.get("comment", "")

    # Method 1: Use Event shortcut method
    if comment == "passphrase":
        await event.approve()
    else:
        await event.reject()

    # Method 2: Use Request DSL
    flag = event.get("flag")
    if comment == "passphrase":
        await onebot.Request(flag).accept()
    else:
        await onebot.Request(flag).reject()
```

### Request Operation Return Value

```python
{
    "status": "ok",
    "retcode": 0,
    "data": {...},
    "message_id": "",
    "message": ""
}
```

## Event Type Mapping

### Standard OB12 Mapping

| OB11 Original Type | Converted detail_type | Description |
|--------------------|-----------------------|-------------|
| message_type: private | `private` | Private chat message |
| message_type: group | `group` | Group chat message |
| request_type: friend | `friend` | Friend request |
| request_type: group | `group` | Group request |
| meta_event_type: heartbeat | `heartbeat` | Heartbeat |
| notice_type: group_upload | `group_file_upload` | Group file upload |
| notice_type: group_admin | `group_admin_change` | Group admin change |
| notice_type: group_increase | `group_member_increase` | Group member increase |
| notice_type: group_decrease | `group_member_decrease` | Group member decrease |
| notice_type: group_ban | `group_ban` | Group mute |
| notice_type: friend_add | `friend_increase` | Friend add |
| notice_type: friend_delete | `friend_decrease` | Friend delete |
| notice_type: group_recall / friend_recall | `message_recall` | Message recall |

### Platform-Specific Events (onebot11_ prefix)

| OB11 Original Type | Converted detail_type | Description |
|--------------------|-----------------------|-------------|
| meta_event_type: lifecycle | `onebot11_lifecycle` | OneBot implementation lifecycle |
| notify + sub_type: honor | `onebot11_honor` | Group honor change |
| notify + sub_type: poke | `onebot11_poke` | Poke |
| notify + sub_type: lucky_king | `onebot11_lucky_king` | Group red envelope lucky king |
| CQ code unknown type | Message segment `onebot11_{type}` | Unrecognized CQ code |

### Event Examples

```json
// Friend request
{
  "type": "request",
  "detail_type": "friend",
  "user_id": "789012",
  "comment": "Please add friend",
  "request_id": "flag_abc123",
  "flag": "flag_abc123"
}

// Heartbeat
{
  "type": "meta_event",
  "detail_type": "heartbeat",
  "interval": 5000,
  "status": {...}
}

// Lifecycle (platform-specific)
{
  "type": "meta_event",
  "detail_type": "onebot11_lifecycle",
  "sub_type": "enable"
}

// Poke (platform-specific)
{
  "type": "notice",
  "detail_type": "onebot11_poke",
  "group_id": "123456",
  "user_id": "789012",
  "target_id": "345678"
}

// Group red envelope lucky king (platform-specific)
{
  "type": "notice",
  "detail_type": "onebot11_lucky_king",
  "group_id": "123456",
  "user_id": "789012",
  "target_id": "345678"
}

// Honor change (platform-specific)
{
  "type": "notice",
  "detail_type": "onebot11_honor",
  "group_id": "123456",
  "user_id": "789012",
  "honor_type": "talkative"
}

// CQ code extension message segment
{
  "type": "message",
  "message": [
    {"type": "onebot11_shake", "data": {}}
  ]
}
```

### Extension Field Explanation

- All specific fields are prefixed with `onebot11_`
- Original event data is retained in the `onebot11_raw` field
- Original event type is retained in the `onebot11_raw_type` field
- Message content CQ codes are converted to corresponding message segments (standard types without prefix, unknown types with `onebot11_` prefix)
- Reply messages add `reply` type message segments
- @ messages add `mention` type message segments

## Event Extension Methods

The OneBot11 adapter registers the following platform-specific methods for event objects, which can be directly called in event handlers:

```python
from ErisPulse.Core.Event import message

@message.on_message()
async def handle_message(event):
    raw_event = event.get_raw_event()
    raw_self_id = event.get_raw_self_id()
    sender_info = event.get_sender_info()
    sender_role = event.get_sender_role()
```

### Method List

| Method | Return Type | Description |
|--------|-------------|-------------|
| `get_raw_event()` | `dict` | Get complete raw OneBot11 event data |
| `get_raw_self_id()` | `str` | Get original self_id (Bot's QQ number) |
| `get_sender_info()` | `dict` | Get complete sender information (including nickname, role, level, etc.) |
| `get_sender_role()` | `str` | Get sender's role in the group (owner/admin/member) |
| `get_sender_level()` | `int` | Get sender's level |
| `get_sender_title()` | `str` | Get sender's group title |
| `is_system_message()` | `bool` | Determine if it is a system message (sub_type == "system") |

### Usage Example

```python
from ErisPulse.Core.Event import message, command

@message.on_group_message()
async def handle_group(event):
    role = event.get_sender_role()
    if role == "admin" or role == "owner":
        await event.reply("Hello admin!")

    title = event.get_sender_title()
    if title:
        await event.reply(f"Your title is: {title}")

@command("whoami")
async def whoami(event):
    info = event.get_sender_info()
    nickname = info.get("nickname", "unknown")
    level = event.get_sender_level()
    await event.reply(f"Nickname: {nickname}, Level: {level}")
```

## Configuration Options

The OneBot11 adapter uses a multi-account architecture, with each account configured independently. The configuration key name is `OneBotAdapter`.

### Account Configuration Fields

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `bot_id` | `str` | Yes | `""` | Bot's QQ number, used to identify the account |
| `mode` | `str` | No | `"server"` | Operation mode: `"server"` (passive listening) or `"client"` (active connection) |
| `url` | `str` | No | `"ws://127.0.0.1:3001"` | WebSocket address for Client mode |
| `token` | `str` | No | `""` | Authentication token (Client mode connection token / Server mode verification token) |
| `server_path` | `str` | No | `"/"` | WebSocket path for Server mode |
| `enabled` | `bool` | No | `true` | Whether to enable this account |
| `name` | `str` | No | `""` | Account comment name |

### Built-in Default Values

- Reconnection interval: 30 seconds
- API call timeout: 30 seconds

### Configuration Example

```toml
[OneBotAdapter.accounts.main]
bot_id = "123456789"
mode = "server"
server_path = "/onebot-main"
token = "main_token"
enabled = true

[OneBotAdapter.accounts.backup]
bot_id = "987654321"
mode = "client"
url = "ws://127.0.0.1:3002"
token = "backup_token"
enabled = true

[OneBotAdapter.accounts.test]
bot_id = "111222333"
mode = "client"
url = "ws://127.0.0.1:3003"
enabled = false
```

### Default Configuration

If no accounts are configured, the adapter will automatically create:
```toml
[OneBotAdapter.accounts.default]
bot_id = ""
mode = "server"
server_path = "/"
enabled = true
```

## Send Method Return Values

All send methods return a Task object, which can be awaited to get the send result. The return result follows the ErisPulse adapter standardization return specification:

```python
{
    "status": "ok",
    "retcode": 0,
    "data": {...},
    "message_id": "123456",
    "message": "",
    "onebot11_raw": {...}
}
```

### Multi-Account Send Syntax

```python
# Account selection methods
await onebot.Send.Using("main").To("group", 123456).Text("Main account message")
await onebot.Send.Using("backup").To("group", 123456).Image("http://example.com/image.jpg")

# API call method
await onebot.call_api("send_msg", account_id="main", group_id=123456, message="Hello")
```

### Account Resolution Priority

The resolution priority of `account_id` parameters in `call_api` and `Using()`:
1. Exact match account name
2. Match `bot_id` field
3. Match any `str` type field of the account
4. Fall back to the first enabled account

## Asynchronous Processing Mechanism

The OneBot11 adapter uses an asynchronous non-blocking design, ensuring:
1. Message sending does not block the event handling loop
2. Multiple concurrent send operations can proceed simultaneously
3. API responses are handled in a timely manner
4. WebSocket connections remain active
5. Multi-account concurrent processing, with each account running independently

## Error Handling

The adapter provides a comprehensive error handling mechanism:
1. Network connection exceptions automatically reconnect (supports independent reconnection for each account, interval 30 seconds)
2. API call timeout handling (fixed 30-second timeout, timeout returns `retcode=33001` standard failure response)
3. When the account is not connected or the connection is closed, `call_api` returns `retcode=33001` standard failure response, no longer throws `ConnectionError`
4. Automatically retries connection failures at the interval

## Enhanced Event Handling

In multi-account mode, all events automatically add account information:
```python
{
    "type": "message",
    "detail_type": "private",
    "self": {"user_id": "123456789", "platform": "onebot11"},
    "platform": "onebot11",
    // ... other event fields
}
```

The adapter automatically maintains the `self_id → account_name` mapping, allowing `event.reply()` to correctly route to the source account without manually specifying the account.

## Management Interface

```python
# Get all account information
accounts = onebot.accounts

# Check account connection status
connection_status = {
    account_id: connection is not None and not connection.closed
    for account_id, connection in onebot.connections.items()
}

# Dynamically enable/disable accounts (requires adapter restart)
onebot.accounts["test"].enabled = False
```

## self_id Automatic Mapping

The adapter automatically establishes a mapping between OneBot `self_id` (QQ number) and `account_name`, used for event routing back:

```python
# Adapter automatically completes
# When receiving an event, the self.user_id field is filled with bot_id
# The adapter automatically records: self_id("123456789") → account_name("main")

# Therefore, event.reply() can automatically find the correct account to send messages
@message.on_message()
async def handler(event):
    await event.reply("Automatically routed to the correct account")
```