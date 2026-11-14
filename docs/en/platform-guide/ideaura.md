# Platform Features Document for Huafeng Coffeehouse (RockyChat)

IdeauraAdapter is an adapter built on the RockyChat platform API, integrating all platform functionality modules and providing a unified interface for event handling and message operations.

---

## Document Information

- Corresponding Module: ErisPulse-Ideaura
- Corresponding Module Version: 4.3.2
- Maintainer: ErisPulse
- Last Updated: 2026-11-10

## Basic Information

- Platform Introduction: Huafeng Coffee Shop (RockyChat) is an instant messaging platform.
- Adapter Name: IdeauraAdapter
- Multi-account Support: Supports configuring multiple accounts via Bot Token.
- Chainable Modifier Support: Supports chainable modifier methods such as `.At()`, `.AtAll()`, `.Reply()`, `.Command()`, etc.
- OneBot12 Compatibility: Supports sending OneBot12 formatted messages.

## Standardized Alignment (4.3.2)

### Events and Accounts

1. **Event `self.account_id` Injection**: All events carry the account name that generated them; in multi-account scenarios, `event.reply()` automatically handles and sends replies according to the originating account.
2. **Optional `bot_id` Field Added to Account Configuration**: `IdeauraAccountConfig` supports `bot_id`, which is used to explicitly specify the Bot user ID corresponding to the account.
3. **Standard `request_id` Added to Friend Request Events**: The `friend_request` / `friend_event` events now have a top-level `request_id` field (with the same value as `ideaura_request_id`), allowing approval or rejection of requests using `event.approve()` or `event.reject()`.

Example for handling friend requests:

```python
from ErisPulse.Core.Event import request

@request.on_request()
async def handle_friend_request(event):
    if event.get("platform") != "ideaura":
        return
    # event["request_id"] has the same value as ideaura_request_id
    if event.get("detail_type") == "friend":
        await event.approve()    # Approve the friend request
    # await event.reject()       # Reject the friend request
```

The interface conventions follow the SDK standard: [Request and Approval Action Specification](../standards/request-action-spec.md).

### Action and Error Code Standardization

1. **Standard Action Names Are No Longer Forwarded as HTTP Paths**: When `call_api` receives an unimplemented standard action name (such as `get_self_info`), it returns error code 10002 instead of forwarding it as an HTTP path to the platform; platform HTTP path calls must use the `/api/` prefix.
2. Error codes have been standardized (all old values such as HTTP status codes, `-1`, `34000`, etc., have been removed):

| retcode | Description |
|---------|-------------|
| 0 | Success |
| 33001 | Network error (request exceptions, timeouts, etc.) |
| 34100 | Platform error (the original response is preserved in the `ideaura_raw` field) |
| 10002 | Unsupported action/message segment (unimplemented standard action, Face emoji segment, etc.) |

### Send Specification

- The HTML method name is `HTML` (`Html` is a reserved alias).
- `Face` segments return error code 10002 (no longer fall back to plain text sending), and a warning log is output.
- Unknown message segments in Raw_ob12 are skipped and a warning is output; if all message segments cannot be processed, error code 10002 is returned.

## v5 Paradigm Update (4.1.0)

- **BaseConverter Inheritance**: Common fields of converters are built by the framework's `build_base_event`
- **spawn_background Task Ownership**: Account connection tasks are now managed using `runtime.spawn_background`
- **Framework Soft Dependency**: Runtime checks for ErisPulse>=2.7.1 and provides a warning; version logs are output on startup
- Request DSL query interface (`Request(request_id)`) is postponed; friend request approval can now be handled through event methods `event.approve()` / `event.reject()` (see "Standardization Alignment (4.3.2)")

### Platform Capabilities Already Integrated

- **Events**: Message edit/withdraw/forward/read (`ideaura_message_*`), friend request, friend add/remove, online status (`friend_online/offline`)
- **Sending**: Text / Image / Markdown / Raw_ob12 (chained Reply/At/AtAll modifiers)
- **Friend Request Approval**: Supported since 4.3.2 via event methods `event.approve()` / `event.reject()`
- **Not Yet Integrated**: Api DSL (REST API interface to be added after platform availability), Request DSL query interface

## Supported Message Sending Types

All sending methods are implemented using a fluent interface, for example:
```python
from ErisPulse.Core import adapter
ideaura = adapter.get("ideaura")

await ideaura.Send.To("group", "chatroom").Text("Hello World!")
```

The supported message types include:
- `.Text(text: str)`: Sends plain text messages.
- `.Image(file, filename: str = None)`: Sends image messages, supporting bytes/URL/local path.
- `.Video(file, filename: str = None)`: Sends video messages, supporting bytes/URL/local path.
- `.File(file, filename: str = None)`: Sends file messages, supporting bytes/URL/local path.
- `.Voice(file, filename: str = None)`: Sends voice messages (as files).
- `.Face(face_id: str)`: Sends emoticons (not supported by platforms since 4.3.2, returns retcode=10002 and skips, no longer falls back to text).
- `.Markdown(text: str)`: Sends messages in Markdown format.
- `.HTML(html: str)`: Sends messages in HTML format (`Html` is a reserved alias).
- `.MergeForward(nodes, title="Merged Chat Logs")`: Sends merged forward messages (rendered as `<details>` collapsible HTML cards).
- `.Edit(message_id: str, text: str, content_type: str = "text")`: Edits an existing message.
- `.Recall(message_id: str)`: Recalls a message.

### Fluent Modifier Methods (can be combined)

Modifier methods return `self`, supporting fluent chaining, and must be called before the final sending method:

- `.At(user_id: str, name: str = None)`: Mentions a specified user.
- `.AtAll()`: Mentions everyone.
- `.Reply(message_id: str)`: Replies to a specified message.
- `.Command(command_id: str)`: Triggers a Bot command, used in conjunction with sending methods (sends the message as a specified command).

### Fluent Chaining Examples

```python
# Basic sending
await ideaura.Send.To("user", user_id).Text("Hello")

# Trigger Bot command
await ideaura.Send.To("group", "chatroom").Command("550e8400-e29b-41d4-a716-446655440000").Text("/weather 北京")

# Mention user
await ideaura.Send.To("group", "chatroom").At("456").Text("@李四 你好")

# Mention multiple users
await ideaura.Send.To("group", "chatroom").At("456").At("789").Text("@多人")

# Reply to message
await ideaura.Send.To("group", "chatroom").Reply(msg_id).Text("回复消息")

# Reply + Mention
await ideaura.Send.To("group", "chatroom").Reply(msg_id).At("456").Text("回复并@")

# HTML formatted message
await ideaura.Send.To("group", "chatroom").HTML("<p>HTML message</p>")
```

### Sending to Different Targets

```python
# Send to chatroom
await ideaura.Send.To("group", "chatroom").Text("聊天室消息")

# Send to topic
await ideaura.Send.To("group", "topic_id").Text("话题消息")

# Send private message
await ideaura.Send.To("user", "user_id").Text("私聊消息")
```

### OneBot12 Message Support

The adapter supports sending OneBot12 formatted messages, facilitating cross-platform message compatibility:

- `.Raw_ob12(message: List[Dict], **kwargs)`: Sends OneBot12 formatted messages.

```python
# Send OneBot12 formatted message
ob12_msg = [{"type": "text", "data": {"text": "Hello"}}]
await ideaura.Send.To("user", user_id).Raw_ob12(ob12_msg)

# Combined with fluent modifiers
ob12_msg = [{"type": "text", "data": {"text": "回复消息"}}]
await ideaura.Send.To("group", "chatroom").Reply(msg_id).Raw_ob12(ob12_msg)
```

> Unknown message segments will be skipped and logged as warnings; if all message segments are unprocessable, returns retcode=10002.

## Return Values of Send Methods

All send methods return a Task object, which can be awaited directly to obtain the send result. The returned result follows the ErisPulse adapter's standardized return specification:

```python
{
    "status": "ok",           // Execution status
    "retcode": 0,             // Return code (0 indicates success; error codes see "Standardized Alignment (4.3.2)")
    "data": {...},            // Response data
    "self": {...},            // Self information (including user_id)
    "message_id": "123456",   // Message ID
    "message": "",            // Error message
    "ideaura_raw": {...}      // Raw response data
}
```

## Unique Event Types

Use platform=="ideaura" check to utilize platform-specific features.

### Core Differences

1. Unique event types:
    - Message edit: ideaura_message_edit
    - Message recall: ideaura_message_recall
    - Message forward: ideaura_message_forward
    - Message read: ideaura_message_read
    - Friend rejected: ideaura_friend_rejected
    - Friend online: ideaura_friend_online
    - Friend offline: ideaura_friend_offline
    - User status change: ideaura_user_status_change
    - Forwarded message segment: ideaura_forwarded
    - Edited mark segment: ideaura_edited
    - Markdown message segment: ideaura_markdown
    - HTML message segment: ideaura_html
    - Bot command message segment: ideaura_command
2. Extended fields:
    - All unique fields are prefixed with `ideaura_`
    - Original data is preserved in the `ideaura_raw` field
    - Event `self.user_id` indicates the current account's user ID, `self.account_id` is the account name

### Message Edit Event

```python
{
  "type": "notice",
  "detail_type": "ideaura_message_edit",
  "platform": "ideaura",
  "message_id": "Message ID",
  "user_id": "Editor ID",
  "ideaura_new_content": "Content after edit",
  "ideaura_updated_message": { ... },
  "ideaura_source_type": "chatroom/topic/private"
}
```

### Message Recall Event

```python
{
  "type": "notice",
  "detail_type": "ideaura_message_recall",
  "platform": "ideaura",
  "message_id": "Message ID to be recalled",
  "user_id": "Recaller ID",
  "group_id": "chatroom",
  "ideaura_source_type": "chatroom",
  "ideaura_recall_time": "Recall time",
  "ideaura_is_self": false
}
```

### Message Forward Event

```python
{
  "type": "notice",
  "detail_type": "ideaura_message_forward",
  "platform": "ideaura",
  "message_id": "Original message ID",
  "user_id": "Forwarder ID",
  "ideaura_forward_to": "Target topic ID",
  "ideaura_original_message_id": "Original message ID",
  "ideaura_forwarded_message_id": "New message ID after forwarding"
}
```

### Message Read Event

```python
{
  "type": "notice",
  "detail_type": "ideaura_message_read",
  "platform": "ideaura",
  "message_id": "Message ID",
  "ideaura_reader_id": "Reader ID",
  "ideaura_reader_name": "Reader nickname"
}
```

### Friend Online Event

```python
{
  "type": "notice",
  "detail_type": "ideaura_friend_online",
  "platform": "ideaura",
  "user_id": "Friend ID",
  "user_nickname": "Friend nickname",
  "ideaura_friend_avatar": "Avatar URL",
  "ideaura_presence_status": "online"
}
```

### Friend Offline Event

```python
{
  "type": "notice",
  "detail_type": "ideaura_friend_offline",
  "platform": "ideaura",
  "user_id": "Friend ID",
  "ideaura_presence_status": "offline"
}
```

### User Status Change Event

```python
{
  "type": "notice",
  "detail_type": "ideaura_user_status_change",
  "platform": "ideaura",
  "user_id": "User ID",
  "ideaura_status": "New status",
  "ideaura_previous_status": "Previous status"
}
```

### Friend Request Event

Starting from version 4.3.2, a standard `request_id` field is added at the top level (same value as `ideaura_request_id`), which can be approved using `event.approve()` or `event.reject()`:

```python
{
  "type": "request",
  "detail_type": "friend",
  "platform": "ideaura",
  "user_id": "Requester ID",
  "user_nickname": "Requester nickname",
  "request_id": "Request ID",
  "ideaura_request_id": "Request ID",
  "ideaura_message": "Verification message"
}
```

### Friend Rejected Event

```python
{
  "type": "notice",
  "detail_type": "ideaura_friend_rejected",
  "platform": "ideaura",
  "user_id": "Rejector ID",
  "user_nickname": "Rejector nickname",
  "ideaura_request_id": "Request ID",
  "ideaura_requester_id": "Request initiator ID",
  "ideaura_requester_name": "Request initiator nickname"
}
```

### Forward Message Segment (ideaura_forwarded)

When receiving a forwarded message, the segment type is `ideaura_forwarded`:

```json
{
  "type": "ideaura_forwarded",
  "data": {
    "forward_source_id": "1001",
    "original_message_id": "1001"
  }
}
```

| Field | Type | Description |
|-------|------|-------------|
| `forward_source_id` | string | Forward source message ID |
| `original_message_id` | string | Original message ID |

### Bot Command Message Segment (ideaura_command)

When a user triggers a Bot command, the segment type is `ideaura_command`:

```json
{
  "type": "ideaura_command",
  "data": {
    "command_id": "550e8400-e29b-41d4-a716-446655440000"
  }
}
```

| Field | Type | Description |
|-------|------|-------------|
| `command_id` | string | Command UUID |

### Event Handling Example

```python
from ErisPulse.Core.Event import notice, message

@message.on_message()
async def handle_message(event):
    if event.get_platform() == "ideaura":
        # Handle message events
        for segment in event.get("message", []):
            if segment.get("type") == "ideaura_forwarded":
                data = segment["data"]
                print(f"Forwarded message, source ID: {data['forward_source_id']}")

@notice.on_notice()
async def handle_notice(event):
    if event.get_platform() != "ideaura":
        return

    detail_type = event.get("detail_type")

    if detail_type == "ideaura_message_edit":
        new_content = event.get("ideaura_new_content", "")
        print(f"Message edited: {new_content}")

    elif detail_type == "ideaura_message_recall":
        message_id = event.get("message_id")
        print(f"Message recalled: {message_id}")

    elif detail_type == "ideaura_friend_online":
        friend_name = event.get_user_nickname()
        print(f"Friend online: {friend_name}")

    elif detail_type == "ideaura_user_status_change":
        status = event.get("ideaura_status")
        print(f"User status changed: {status}")
```

## Event Mixin Extension Methods

The adapter registers the following platform-specific methods, available only when `platform == "ideaura"`:

| Method | Return Type | Description |
|--------|-------------|-------------|
| `get_source_type()` | `str` | Message source type (`chatroom`/`topic`/`private`) |
| `get_sender_name()` | `str` | Sender's nickname |
| `get_sender_avatar()` | `str` | Sender's avatar URL |
| `is_sender_bot()` | `bool` | Whether the sender is a bot |
| `is_receiver_bot()` | `bool` | Whether the receiver is a bot |
| `get_command_id()` | `str` | The ID of the triggered Bot command (if any, `ideaura_command_id`) |
| `get_command()` | `str` | Alias for `get_command_id()` |
| `get_topic_name()` | `str` | Topic name |
| `get_message_type()` | `str` | Message type (`normal`/`edited`/`forwarded`/`quoted`) |
| `get_message_subtype()` | `str` | Message subtype (`text`/`image`/`video`/`file`/`markdown`/`html`) |
| `is_self_message()` | `bool` | Whether the message was sent by oneself |

```python
from ErisPulse.Core.Event import message

@message.on_message()
async def handle_message(event):
    if event.get_platform() != "ideaura":
        return

    # Get the ID of the triggered Bot command (if any)
    cmd_id = event.get_command_id()
    if cmd_id:
        print(f"Received command: {cmd_id}")
```

## Multi-Account Configuration

### Configuration Description

IdeauraAdapter supports configuring and running multiple accounts simultaneously, using **Bot Token** authentication.

> [!WARNING]
> Starting from version 4.0.1, **email/password login has been removed** and only Bot Token is supported. Bot Token can be obtained from [MSCPO Open Platform](https://open.mscpo.com/rockychat/bots) (it starts with `bot-token-`).

```toml
# config.toml
# Account 1
[IdeauraAdapter.accounts.default]
token = "bot-token-xxxxxx1"      # API Token for the bot (required)
bot_id = ""                      # Bot user ID (optional, explicitly specify the bot associated with the account)
enabled = true                   # Whether to enable this account (optional, default is true)

# Account 2
[IdeauraAdapter.accounts.bot2]
token = "bot-token-xxxxxx2"
bot_id = ""
enabled = true

# Optional: Custom server address
[IdeauraAdapter]
base_url = "https://api.mscpo.com/api/rockychat"
ws_url = "wss://api-cofe.allons-y.uk:3009/mqtt"
heartbeat_interval = 30
```

**Configuration Item Descriptions:**
- `token`: API Token for the bot (required, starts with `bot-token-`)
- `bot_id`: Bot user ID (optional, supported since 4.3.2, used to explicitly specify the bot associated with the account)
- `enabled`: Whether to enable this account (optional, default is true)

**Global Configuration Items:**
- `base_url`: API server address (optional, default is `https://api.mscpo.com/api/rockychat`)
- `ws_url`: WebSocket server address (optional, default is the official address of HuaFeng Coffee House)
- `heartbeat_interval`: Heartbeat interval in seconds (optional, default is 30 seconds)

### Using Send DSL to Specify Account

You can specify which account to use for sending messages using the `Using()` method:

```python
from ErisPulse.Core import adapter
ideaura = adapter.get("ideaura")

# Send message using account name
await ideaura.Send.Using("default").To("user", "user123").Text("Hello from account 1!")

# Send message using user_id (automatically matches the corresponding account)
await ideaura.Send.Using("456").To("group", "chatroom").Text("Hello from account 2!")

# If not specified, use the first enabled account
await ideaura.Send.To("user", "user123").Text("Hello from default account!")
```

### Account Identification in Events

Received events will automatically include corresponding account information (since 4.3.2, `self.account_id` is the account name):

```python
from ErisPulse.Core.Event import message

@message.on_message()
async def handle_message(event):
    if event["platform"] == "ideaura":
        account_id = event["self"]["account_id"]
        print(f"Message received from account: {account_id}")
```

## Extension Field Description

- All custom fields are prefixed with `ideaura_` to avoid conflicts with standard fields.
- The original data is retained in the `ideaura_raw` field, allowing access to the complete original data from the platform.
- `self.user_id` represents the user ID of the currently logged-in account, and `self.account_id` is the account name.
- `ideaura_source_type`: Source type of the message (`chatroom`/`topic`/`private`)
- `ideaura_sender_name`: Nickname of the sender
- `ideaura_sender_avatar`: URL of the sender's avatar
- `ideaura_sender_is_bot`: Whether the sender is a bot
- `ideaura_is_self`: Whether the message was sent by oneself (self-messages have been filtered)
- `ideaura_topic_name`: Name of the topic
- `ideaura_message_type`: Message type (normal/edited/forwarded/quoted)
- `ideaura_message_subtype`: Message sub-type (text/image/video/file/markdown/html)

### File Handling Features

- File size limit: 10MB (both download and local reading are limited)
- Automatic file type detection: Detects actual file types using magic bytes in the file header
- Intelligent file name parsing: Automatically corrects meaningless extensions such as `.bin`/`.dat`/`.tmp`
- Supports three file input methods: bytes, URL, and local path
- Automatically downloads and uploads URL files to the server

### Supported File Types

Detected automatically via magic bytes:

| Type | Extensions |
|------|------------|
| Image | png, jpg, gif, webp |
| Video | mp4, avi, flv |
| Audio | mp3, wav, ogg |
| Document | pdf, docx |

## Notes

1. The default API server address is `https://api.mscpo.com/api/rockychat` (customizable via `base_url`); the WebSocket address `wss://api-cofe.allons-y.uk:3009/mqtt` is a platform-specific address and does not change with the adapter name.
2. The adapter uses a WebSocket long connection to receive events and supports automatic reconnection (with a fixed 5-second delay).
3. Messages sent by the adapter itself (`isSelf: true`) are automatically filtered and will not generate events.
4. @All (`AtAll()`) requires administrator privileges.
5. The file upload size limit is 10MB.
6. Audio files are sent as a `file` subtype (the platform does not distinguish independent audio types).
7. Emojis (`Face()`) are not supported by the platform, returning retcode=10002 and skipping (no longer downgraded to plain text).
8. Call `shutdown()` before program exit to ensure resource release.