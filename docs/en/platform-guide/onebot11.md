# OneBot11 Platform Feature Documentation

OneBot11Adapter is an adapter built based on the OneBot V11 protocol.

---

Please directly return the complete translated Markdown content without including any other text.

Once again, please note: if the document contains language switch lines (lines with language names separated by `` | ``), strictly adhere to the format requirements outlined in point 8 above, and do not write incorrect formats such as ``[**Label**](file)``.

## Document Information

- Corresponding Module Version: 4.0.0
- Maintainer: ErisPulse

Please directly return the translated complete Markdown content, without including any other text.

## Basic Information

- Platform Overview: OneBot is a chatbot application programming interface standard
- Adapter Name: OneBotAdapter
- Supported Protocol/API Version: OneBot V11
- Multi-account Support: Default multi-account architecture, supports configuring and running multiple OneBot accounts simultaneously
- Configuration Key Name: `OneBotAdapter`

Please directly return the complete translated Markdown content, without including any other text.

Once again, please note: if the document contains a language switch line (with each language name separated by `` | ``), be sure to strictly follow the format requirements in item 8 above, and do not write the incorrect format ``[**Label**](file)``.

## Supported Message Sending Types

All sending methods are implemented through a fluent syntax, for example:
```python
from ErisPulse.Core import adapter
onebot = adapter.get("onebot11")

# Send using the default account
await onebot.Send.To("group", group_id).Text("Hello World!")

# Send using a specific account
await onebot.Send.Using("main").To("group", group_id).Text("Message from main account")

# Chainable modifiers: @ user + reply
await onebot.Send.To("group", group_id).At(123456).Reply(msg_id).Text("Reply message")

# @全体成员
await onebot.Send.To("group", group_id).AtAll().Text("Announcement message")
```

### Basic Sending Methods

- `.Text(text: str)` : Send plain text messages.
- `.Image(file: Union[str, bytes], filename: str = "image.png")` : Send images (supports URL, Base64, or bytes).
- `.Voice(file: Union[str, bytes], filename: str = "voice.amr")` : Send voice messages.
- `.Video(file: Union[str, bytes], filename: str = "video.mp4")` : Send video messages.
- `.Face(id: Union[str, int])` : Send QQ emoticons.
- `.File(file: Union[str, bytes], filename: str = "file.dat")` : Send files (automatic type detection).
- `.Raw_ob12(message: List[Dict], **kwargs)` : Send OneBot12 format messages (automatically converted to OB11).
- `.Recall(message_id: Union[str, int])` : Recall messages.

### Group Operation Methods

The following methods must be used with `To("group", group_id)` to specify the target group and execute operations in the group context:

- `.Kick(user_id, reject_add_request=False)` : Kick a group member.
- `.Ban(user_id, duration=1800)` : Mute a group member (in seconds); 0 means unmute.
- `.WholeBan(enable=True)` : Enable/disable mute for all members.
- `.SetAdmin(user_id, enable=True)` : Set/unset group admin.
- `.SetCard(user_id, card="")` : Set group nickname.
- `.SetGroupName(name)` : Modify group name.
- `.Leave(is_dismiss=False)` : Leave the group (group owner can dismiss).
- `.SetTitle(user_id, title="")` : Set group title.
- `.SetPortrait(file)` : Set group avatar.

### Query Methods

- `.GetMsg(message_id)` : Get message content.
- `.GetForwardMsg(id)` : Get merged forwarded messages.
- `.GetLoginInfo()` : Get current login account information.
- `.GetFriendList()` : Get friend list.
- `.GetGroupInfo()` : Get group information (requires `To("group", group_id)`).
- `.GetGroupList()` : Get group list.
- `.GetGroupMemberInfo(user_id)` : Get group member information (requires `To("group", group_id)`).
- `.GetGroupMemberList()` : Get group member list (requires `To("group", group_id)`).

### Friend Operation Methods

- `.Like(user_id, times=1)` : Send a friend like (maximum 10 times).

### Chainable Modifier Methods (can be combined)

Chainable modifier methods return `self`, supporting fluent calls, must be called before the final sending method:

- `.At(user_id: Union[str, int], name: str = None)` : @ specified user (can be called multiple times).
- `.AtAll()` : @全体成员.
- `.Reply(message_id: Union[str, int])` : Reply to a specific message.

### Fluent Call Examples

```python
# Basic sending
await onebot.Send.To("group", 123456).Text("Hello")

# @ single user
await onebot.Send.To("group", 123456).At(789012).Text("你好")

# @ multiple users
await onebot.Send.To("group", 123456).At(111).At(222).At(333).Text("大家好")

# Send OneBot12 format message
ob12_msg = [{"type": "text", "data": {"text": "Hello"}}]
await onebot.Send.To("group", 123456).Raw_ob12(ob12_msg)

# Like
await onebot.Send.Like(123456, times=10)

# Mute group member
await onebot.Send.To("group", 123456).Ban(789012, duration=3600)

# Unmute
await onebot.Send.To("group", 123456).Ban(789012, duration=0)

# Kick
await onebot.Send.To("group", 123456).Kick(789012)

# Set group admin
await onebot.Send.To("group", 123456).SetAdmin(789012)

# Modify group name
await onebot.Send.To("group", 123456).SetGroupName("New Group Name")

# Get group info
result = await onebot.Send.To("group", 123456).GetGroupInfo()

# Specify account operation
await onebot.Send.Using("main").To("group", 123456).Ban(789012)
```

### Handling Unsupported Types

If an undefined sending method is called, the adapter will return a text prompt:
```python
# Call an undefined method
await onebot.Send.To("group", 123456).SomeUnsupportedMethod(arg1, arg2)
# Actually sent: "[Unsupported sending type] Method name: SomeUnsupportedMethod, Parameters: [...]"

## Request Operations (Request DSL)

The adapter provides a Request Operations DSL for handling approval/rejection operations of friend requests and group requests (joining/inviting).

### Event Shortcut Methods

Request events support the `event.approve()` and `event.reject()` shortcut methods, which internally automatically call the Request DSL:

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

### Manual Call to Request DSL

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
| notice_type: group_ban | `group_ban` | Group ban |
| notice_type: friend_add | `friend_increase` | Friend added |
| notice_type: friend_delete | `friend_decrease` | Friend removed |
| notice_type: group_recall / friend_recall | `message_recall` | Message recall |

### Platform-specific Events (onebot11_ prefix)

| OB11 Original Type | Converted detail_type | Description |
|--------------------|-----------------------|-------------|
| meta_event_type: lifecycle | `onebot11_lifecycle` | OneBot implementation lifecycle |
| notify + sub_type: honor | `onebot11_honor` | Group honor change |
| notify + sub_type: poke | `onebot11_poke` | Poke |
| notify + sub_type: lucky_king | `onebot11_lucky_king` | Group red packet luckiest king |
| Unknown CQ Code type | Message segment `onebot11_{type}` | Unrecognized CQ Code |

### Event Examples

```python
// Friend request
{
  "type": "request",
  "detail_type": "friend",
  "user_id": "789012",
  "comment": "Please add as friend",
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

// Group red packet luckiest king (platform-specific)
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

// CQ Code extended message segment
{
  "type": "message",
  "message": [
    {"type": "onebot11_shake", "data": {}}
  ]
}
```

### Extended Field Description

- All platform-specific fields are prefixed with `onebot11_`
- Original event data is preserved in the `onebot11_raw` field
- Original event type is preserved in the `onebot11_raw_type` field
- CQ Code in message content is converted to corresponding message segments (standard types without prefix, unknown types with `onebot11_` prefix)
- Reply messages will have a `reply` type message segment added
- @ messages will have a `mention` type message segment added

## Event Extension Methods

The OneBot11 adapter registers the following platform-specific methods for event objects, which can be directly called in event handlers:

```python
from ErisPulse.Core.Event import message

@message.on_message()
async def handle_message(event):
    raw_self_id = event.get_raw_self_id()
    sender_info = event.get_sender_info()
    sender_role = event.get_sender_role()
```

### Method List

| Method | Return Type | Description |
|--------|-------------|-------------|
| `get_raw_event()` | `dict` | Retrieve the complete raw event data from OneBot11 |
| `get_raw_self_id()` | `str` | Retrieve the raw self_id (Bot's QQ number) |
| `get_sender_info()` | `dict` | Retrieve complete sender information (including nickname, role, level, etc.) |
| `get_sender_role()` | `str` | Retrieve the role of the sender within the group (owner/admin/member) |
| `get_sender_level()` | `int` | Retrieve the sender's level |
| `get_sender_title()` | `str` | Retrieve the sender's group title |
| `is_system_message()` | `bool` | Determine if the message is a system message (sub_type == "system") |

### Usage Examples

```python
from ErisPulse.Core.Event import message, command

@message.on_group_message()
async def handle_group(event):
    role = event.get_sender_role()
    if role == "admin" or role == "owner":
        await event.reply("Hello, admin!")

    title = event.get_sender_title()
    if title:
        await event.reply(f"Your title is: {title}")

@command("whoami")
async def whoami(event):
    info = event.get_sender_info()
    nickname = info.get("nickname", "Unknown")
    level = event.get_sender_level()
    await event.reply(f"Nickname: {nickname}, Level: {level}")

## Configuration Options

The OneBot11 adapter uses a multi-account architecture, with each account having independent configuration. The configuration key is named `OneBotAdapter`.

### Account Configuration Fields

| Field | Type | Required | Default | Description |
|------|------|------|--------|------|
| `bot_id` | `str` | Yes | `""` | The robot's QQ number, used to identify the account |
| `mode` | `str` | No | `"server"` | Running mode: `"server"` (passive listening) or `"client"` (active connection) |
| `url` | `str` | No | `"ws://127.0.0.1:3001"` | WebSocket address for Client mode |
| `token` | `str` | No | `""` | Authentication Token (Token for Client mode connection / Token for Server mode verification) |
| `server_path` | `str` | No | `"/"` | WebSocket path for Server mode |
| `enabled` | `bool` | No | `true` | Whether to enable this account |
| `name` | `str` | No | `""` | Account comment name |

### Built-in Defaults

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

If no account is configured, the adapter will automatically create:
```toml
[OneBotAdapter.accounts.default]
bot_id = ""
mode = "server"
server_path = "/"
enabled = true

## Send Method Return Values

All send methods return a Task object, which can be directly awaited to obtain the send result. The returned result follows the ErisPulse adapter's standardized return specification:

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
# Account selection method
await onebot.Send.Using("main").To("group", 123456).Text("Main account message")
await onebot.Send.Using("backup").To("group", 123456).Image("http://example.com/image.jpg")

# Select account by bot_id
await onebot.Send.Using("123456789").To("group", 123456).Text("Selected by QQ number")

# API call method
await onebot.call_api("send_msg", account_id="main", group_id=123456, message="Hello")
```

### Account Resolution Priority

The resolution priority of the `account_id` parameter in `call_api` and `Using()`:
1. Exact match of account name
2. Match `bot_id` field
3. Match any `str` type field of the account
4. Fall back to the first enabled account

Please directly return the translated complete Markdown content without including any other text.

## Asynchronous Processing Mechanism

The OneBot11 adapter adopts an asynchronous non-blocking design to ensure:
1. Message sending does not block the event handling loop
2. Multiple concurrent send operations can be performed simultaneously
3. API responses can be processed promptly
4. WebSocket connections remain active
5. Concurrent processing of multiple accounts, with each account running independently

Please directly return the complete translated Markdown content, without including any other text.

Once again, if the document contains language switching lines (with each language name separated by `` | ``), strictly follow the above rule #8 for formatting, and do not write incorrect formats such as ``[**Label**](file)``.

## Error Handling

Adapters provide a comprehensive error handling mechanism:
1. Automatic reconnection for network connection exceptions (supports independent reconnection for each account, with a 30-second interval)
2. API call timeout handling (fixed 30-second timeout)
3. Automatic retry at intervals when connection fails

For document links containing `docs/en/`, replace them with `docs/en/`:
- For example: `docs/en/quick-start.md` should be changed to `docs/en/quick-start.md`
- For links pointing to non-current language version files (e.g., `README.xx.md` format), keep them unchanged
- This ensures links point to the correct language version of the document

## Event Handling Enhancement

In multi-account mode, all events will automatically include account information:
```python
{
    "type": "message",
    "detail_type": "private",
    "self": {"user_id": "123456789", "platform": "onebot11"},
    "platform": "onebot11",
    // ... other event fields
}
```

The adapter automatically maintains the `self_id → account_name` mapping, so `event.reply()` can correctly route to the originating account without manually specifying the account.

For documentation links, replace `docs/en/` with `docs/en/`:
- For example: `docs/en/quick-start.md` should be changed to `docs/en/quick-start.md`
- For links pointing to non-current language version files (e.g., `README.xx.md`), keep them unchanged to ensure they point to the correct language version of the document.

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

## self_id Automatic Mapping

The adapter will automatically establish a mapping relationship between OneBot `self_id` (QQ number) and `account_name`, used for event routing:

```python
# Automatically completed internally by the adapter
# When an event is received, the self.user_id field is filled with bot_id
# The adapter automatically records: self_id("123456789") → account_name("main")

# Therefore event.reply() can automatically find the correct account to send messages
@message.on_message()
async def handler(event):
    await event.reply("Automatically routed to the correct account")
```

7. **Important: Path Replacement Rules**
   - Replace `docs/en/` in document links with `docs/en/`
   - For example: `docs/en/quick-start.md` should be changed to `docs/en/quick-start.md`
   - For links pointing to non-current language version files (e.g., links in the form of `README.xx.md`), keep them unchanged
   - This ensures that links point to the correct language version of the document