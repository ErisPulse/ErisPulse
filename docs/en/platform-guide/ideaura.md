# Platform Features Document for Huafeng Coffeehouse (RockyChat)

IdeauraAdapter is an adapter built on the RockyChat platform API, integrating all platform functionality modules and providing a unified interface for event handling and message operations.

---

## Documentation Information

- Corresponding Module: ErisPulse-Ideaura
- Corresponding Module Version: 4.0.1
- Maintainer: ErisPulse

## Basic Information

- Platform Introduction: Huafeng Coffee Shop (RockyChat) is an instant messaging platform.
- Adapter Name: IdeauraAdapter
- Multi-account Support: Supports configuring multiple accounts via Bot Token.
- Chainable Modifier Support: Supports chainable modifier methods such as `.At()`, `.AtAll()`, `.Reply()`, `.Command()`, etc.
- OneBot12 Compatibility: Supports sending OneBot12 formatted messages.

## Supported Message Sending Types

All sending methods are implemented through a fluent interface, for example:
```python
from ErisPulse.Core import adapter
ideaura = adapter.get("ideaura")

await ideaura.Send.To("group", "chatroom").Text("Hello World!")
```

The supported sending types include:
- `.Text(text: str)` : Send plain text messages.
- `.Image(file, filename: str = None)` : Send image messages, supporting bytes/URL/local path.
- `.Video(file, filename: str = None)` : Send video messages, supporting bytes/URL/local path.
- `.File(file, filename: str = None)` : Send file messages, supporting bytes/URL/local path.
- `.Voice(file, filename: str = None)` : Send voice messages (sent as files).
- `.Face(face_id: str)` : Send emoticons (sent as plain text emoji).
- `.Markdown(text: str)` : Send Markdown formatted messages.
- `.Html(html: str)` : Send HTML formatted messages.
- `.Edit(message_id: str, text: str, content_type: str = "text")` : Edit existing messages.
- `.Recall(message_id: str)` : Recall messages.

### Fluent Modifier Methods (Combinable)

Modifier methods return `self`, supporting fluent calls, and must be called before the final sending method:

- `.At(user_id: str, name: str = None)` : At a specific user.
- `.AtAll()` : At all users.
- `.Reply(message_id: str)` : Reply to a specific message.
- `.Command(command_id: str)` : Trigger a Bot command, used in conjunction with sending methods (sends the message as the specified command).

### Fluent Call Examples

```python
# Basic sending
await ideaura.Send.To("user", user_id).Text("Hello")

# Trigger Bot command
await ideaura.Send.To("group", "chatroom").Command("550e8400-e29b-41d4-a716-446655440000").Text("/weather 北京")

# At a user
await ideaura.Send.To("group", "chatroom").At("456").Text("@李四 你好")

# At multiple users
await ideaura.Send.To("group", "chatroom").At("456").At("789").Text("@多人")

# Reply to a message
await ideaura.Send.To("group", "chatroom").Reply(msg_id).Text("回复消息")

# Reply + At
await ideaura.Send.To("group", "chatroom").Reply(msg_id).At("456").Text("回复并@")
```

### Sending to Different Targets

```python
# Send to a chatroom
await ideaura.Send.To("group", "chatroom").Text("聊天室消息")

# Send to a topic
await ideaura.Send.To("group", "topic_id").Text("话题消息")

# Send a private message
await ideaura.Send.To("user", "user_id").Text("私聊消息")
```

### OneBot12 Message Support

The adapter supports sending OneBot12 formatted messages for cross-platform message compatibility:

- `.Raw_ob12(message: List[Dict], **kwargs)` : Send OneBot12 formatted messages.

```python
# Send OneBot12 formatted message
ob12_msg = [{"type": "text", "data": {"text": "Hello"}}]
await ideaura.Send.To("user", user_id).Raw_ob12(ob12_msg)

# Combined with fluent modifiers
ob12_msg = [{"type": "text", "data": {"text": "回复消息"}}]
await ideaura.Send.To("group", "chatroom").Reply(msg_id).Raw_ob12(ob12_msg)
```

## Send Method Return Values

All send methods return a Task object, which can be directly awaited to obtain the send result. The returned result follows the ErisPulse adapter standardization return specification:

```python
{
    "status": "ok",           // Execution status
    "retcode": 0,             // Return code
    "data": {...},            // Response data
    "self": {...},            // Self information (including user_id)
    "message_id": "123456",   // Message ID
    "message": "",            // Error message
    "ideaura_raw": {...}      // Raw response data
}
```

## Unique Event Types

The `platform=="ideaura"` check is required before using platform-specific features.

### Core Differences

1. Unique Event Types:
    - Message Edit: ideaura_message_edit
    - Message Recall: ideaura_message_recall
    - Message Forward: ideaura_message_forward
    - Message Read: ideaura_message_read
    - Friend Rejected: ideaura_friend_rejected
    - Friend Online: ideaura_friend_online
    - Friend Offline: ideaura_friend_offline
    - User Status Change: ideaura_user_status_change
    - Forwarded Message Segment: ideaura_forwarded
    - Edited Mark Segment: ideaura_edited
    - Markdown Message Segment: ideaura_markdown
    - HTML Message Segment: ideaura_html
    - Bot Command Message Segment: ideaura_command
2. Extended Fields:
    - All unique fields are prefixed with `ideaura_`
    - Original data is preserved in the `ideaura_raw` field
    - `self.user_id` represents the current account's user ID

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

```python
{
  "type": "request",
  "detail_type": "friend",
  "platform": "ideaura",
  "user_id": "Requester ID",
  "user_nickname": "Requester nickname",
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

### Forwarded Message Segment (ideaura_forwarded)

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
|------|------|------|
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
|------|------|------|
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

### Configuration Instructions

IdeauraAdapter supports configuring and running multiple accounts simultaneously, using **Bot Token** authentication.

> [!WARNING]
> Starting from version 4.0.1, **email and password login has been removed**, and only Bot Token is supported. Bot Token can be obtained from [MSCPO Open Platform](https://open.mscpo.com/rockychat/bots) (must start with `bot-token-`).

```toml
# config.toml
# Account 1
[IdeauraAdapter.accounts.default]
token = "bot-token-xxxxxx1"      # API Token for the bot (required)
enabled = true                   # Whether to enable this account (optional, default is true)

# Account 2
[IdeauraAdapter.accounts.bot2]
token = "bot-token-xxxxxx2"
enabled = true

# Optional: Custom server address
[IdeauraAdapter]
base_url = "https://api.mscpo.com/api/rockychat"
ws_url = "wss://api-cofe.allons-y.uk:3009/mqtt"
heartbeat_interval = 30
```

**Configuration Item Description:**
- `token`: API Token for the bot (required, must start with `bot-token-`)
- `enabled`: Whether to enable this account (optional, default is true)

**Global Configuration Items:**
- `base_url`: API server address (optional, default is `https://api.mscpo.com/api/rockychat`)
- `ws_url`: WebSocket server address (optional, default is the official address of Huafeng Coffee House)
- `heartbeat_interval`: Heartbeat interval in seconds (optional, default is 30 seconds)

### Using Send DSL to Specify Account

You can specify which account to use for sending messages via the `Using()` method:

```python
from ErisPulse.Core import adapter
ideaura = adapter.get("ideaura")

# Send message using account name
await ideaura.Send.Using("default").To("user", "user123").Text("Hello from account 1!")

# Send message using user_id (automatically matches corresponding account)
await ideaura.Send.Using("456").To("group", "chatroom").Text("Hello from account 2!")

# If not specified, the first enabled account is used
await ideaura.Send.To("user", "user123").Text("Hello from default account!")
```

### Account Identification in Events

Received events automatically include corresponding account information:

```python
from ErisPulse.Core.Event import message

@message.on_message()
async def handle_message(event):
    if event["platform"] == "ideaura":
        account_id = event["self"]["user_id"]
        print(f"Message received from account: {account_id}")
```

## Extension Field Description

- All special fields are prefixed with `ideaura_` to avoid conflicts with standard fields.
- The original data is retained in the `ideaura_raw` field, allowing access to the platform's complete raw data.
- `self.user_id` represents the user ID of the currently logged-in account.
- `ideaura_source_type`: Message source type (`chatroom`/`topic`/`private`)
- `ideaura_sender_name`: Sender's nickname
- `ideaura_sender_avatar`: Sender's avatar URL
- `ideaura_sender_is_bot`: Whether the sender is a bot
- `ideaura_is_self`: Whether the message was sent by oneself (self-messages have been filtered out)
- `ideaura_topic_name`: Topic name
- `ideaura_message_type`: Message type (normal/edited/forwarded/quoted)
- `ideaura_message_subtype`: Message subtype (text/image/video/file/markdown/html)

### File Handling Features

- File size limit: 10MB (both download and local read are limited)
- Automatic file type detection: Detects actual type via file header magic bytes
- Intelligent filename parsing: Automatically corrects meaningless extensions such as `.bin`/`.dat`/`.tmp`
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
3. Messages sent by itself (`isSelf: true`) are automatically filtered and do not generate events.
4. @all (using `AtAll()`) requires administrator privileges.
5. File upload size is limited to 10MB.
6. Audio files are sent as a `file` subtype (the platform does not distinguish independent audio types).
7. Emojis (using `Face()`) are sent as plain text emoji.
8. Call `shutdown()` when exiting the program to ensure proper resource release.