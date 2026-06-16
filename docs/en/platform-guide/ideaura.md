# Ideaura Cafe Platform Features Documentation

IdeauraAdapter is an adapter built based on the Ideaura Cafe (Allons) platform API, integrating all platform function modules and providing unified event handling and message operation interfaces.

---

## Document Information

- Corresponding Module: ErisPulse-Ideaura
- Maintainer: ErisPulse

## Basic Information

- Platform Introduction: Ideaura Cafe (Allons) is an instant messaging platform
- Adapter Name: IdeauraAdapter
- Multi-account Support: Supports configuring multiple accounts via token or email/password (one of the two)
- Chaining Support: Supports chaining methods such as `.At()`, `.AtAll()`, `.Reply()`
- OneBot12 Compatibility: Supports sending OneBot12 format messages

## Supported Message Sending Types

All sending methods are implemented through chain syntax, for example:
```python
from ErisPulse.Core import adapter
ideaura = adapter.get("ideaura")

await ideaura.Send.To("group", "chatroom").Text("Hello World!")
```

Supported sending types include:
- `.Text(text: str)`: Send plain text messages.
- `.Image(file, filename: str = None)`: Send image messages, supporting bytes/URL/local paths.
- `.Video(file, filename: str = None)`: Send video messages, supporting bytes/URL/local paths.
- `.File(file, filename: str = None)`: Send file messages, supporting bytes/URL/local paths.
- `.Voice(file, filename: str = None)`: Send voice messages (sent as files).
- `.Face(face_id: str)`: Send emoticons (sends emoji as plain text).
- `.Markdown(text: str)`: Send Markdown format messages.
- `.Html(html: str)`: Send HTML format messages.
- `.Edit(message_id: str, text: str, content_type: str = "text")`: Edit existing messages.
- `.Recall(message_id: str)`: Recall messages.

### Chaining Methods (Can be used in combination)

Chaining methods return `self`, support method chaining, and must be called before the final sending method:
- `.At(user_id: str, name: str = None)`: @ specific user.
- `.AtAll()`: @ everyone.
- `.Reply(message_id: str)`: Reply to specific message.

### Chaining Examples

```python
# Basic sending
await ideaura.Send.To("user", user_id).Text("Hello")

# @ user
await ideaura.Send.To("group", "chatroom").At("456").Text("@Li Si 你好")

# @ multiple users
await ideaura.Send.To("group", "chatroom").At("456").At("789").Text("@多人")

# Reply to message
await ideaura.Send.To("group", "chatroom").Reply(msg_id).Text("回复消息")

# Reply + @
await ideaura.Send.To("group", "chatroom").Reply(msg_id).At("456").Text("回复并@")
```

### Sending to Different Targets

```python
# Send to chat room
await ideaura.Send.To("group", "chatroom").Text("聊天室消息")

# Send to topic
await ideaura.Send.To("group", "topic_id").Text("话题消息")

# Send private message
await ideaura.Send.To("user", "user_id").Text("私聊消息")
```

### OneBot12 Message Support

The adapter supports sending OneBot12 format messages for cross-platform message compatibility:
- `.Raw_ob12(message: List[Dict], **kwargs)`: Send OneBot12 format messages.

```python
# Send OneBot12 format message
ob12_msg = [{"type": "text", "data": {"text": "Hello"}}]
await ideaura.Send.To("user", user_id).Raw_ob12(ob12_msg)

# With chaining
ob12_msg = [{"type": "text", "data": {"text": "回复消息"}}]
await ideaura.Send.To("group", "chatroom").Reply(msg_id).Raw_ob12(ob12_msg)
```

## Return Values of Sending Methods

All sending methods return a Task object that can be directly awaited to get the sending result. The returned result follows the ErisPulse adapter standardized return specification:

```python
{
    "status": "ok",           // Execution status
    "retcode": 0,             // Return code
    "data": {...},            // Response data
    "self": {...},            // Self information (contains user_id)
    "message_id": "123456",   // Message ID
    "message": "",            // Error message
    "ideaura_raw": {...}      // Raw response data
}
```

## Special Event Types

Requires `platform=="ideaura"` detection before using platform-specific features

### Core Differences

1. Special event types:
   - Message edit: ideaura_message_edit
   - Message recall: ideaura_message_recall
   - Message forward: ideaura_message_forward
   - Message read: ideaura_message_read
   - Friend rejected: ideaura_friend_rejected
   - Friend online: ideaura_friend_online
   - Friend offline: ideaura_friend_offline
   - User status change: ideaura_user_status_change
   - Forwarded message segment: ideaura_forwarded
   - Edit marker segment: ideaura_edited
   - Markdown message segment: ideaura_markdown
   - HTML message segment: ideaura_html
2. Extended fields:
   - All special fields are prefixed with `ideaura_`
   - Raw data is preserved in the `ideaura_raw` field
   - `self.user_id` represents the current account's user ID

### Message Edit Event

```python
{
  "type": "notice",
  "detail_type": "ideaura_message_edit",
  "platform": "ideaura",
  "message_id": "消息ID",
  "user_id": "编辑者ID",
  "ideaura_new_content": "编辑后的内容",
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
  "message_id": "被撤回的消息ID",
  "user_id": "撤回者ID",
  "group_id": "chatroom",
  "ideaura_source_type": "chatroom",
  "ideaura_recall_time": "撤回时间",
  "ideaura_is_self": false
}
```

### Message Forward Event

```python
{
  "type": "notice",
  "detail_type": "ideaura_message_forward",
  "platform": "ideaura",
  "message_id": "原始消息ID",
  "user_id": "转发者ID",
  "ideaura_forward_to": "目标话题ID",
  "ideaura_original_message_id": "原始消息ID",
  "ideaura_forwarded_message_id": "转发后的新消息ID"
}
```

### Message Read Event

```python
{
  "type": "notice",
  "detail_type": "ideaura_message_read",
  "platform": "ideaura",
  "message_id": "消息ID",
  "ideaura_reader_id": "已读者ID",
  "ideaura_reader_name": "已读者昵称"
}
```

### Friend Online Event

```python
{
  "type": "notice",
  "detail_type": "ideaura_friend_online",
  "platform": "ideaura",
  "user_id": "好友ID",
  "user_nickname": "好友昵称",
  "ideaura_friend_avatar": "头像URL",
  "ideaura_presence_status": "online"
}
```

### Friend Offline Event

```python
{
  "type": "notice",
  "detail_type": "ideaura_friend_offline",
  "platform": "ideaura",
  "user_id": "好友ID",
  "ideaura_presence_status": "offline"
}
```

### User Status Change Event

```python
{
  "type": "notice",
  "detail_type": "ideaura_user_status_change",
  "platform": "ideaura",
  "user_id": "用户ID",
  "ideaura_status": "新状态",
  "ideaura_previous_status": "旧状态"
}
```

### Friend Request Event

```python
{
  "type": "request",
  "detail_type": "friend",
  "platform": "ideaura",
  "user_id": "请求者ID",
  "user_nickname": "请求者昵称",
  "ideaura_request_id": "请求ID",
  "ideaura_message": "验证消息"
}
```

### Friend Rejected Event

```python
{
  "type": "notice",
  "detail_type": "ideaura_friend_rejected",
  "platform": "ideaura",
  "user_id": "拒绝者ID",
  "user_nickname": "拒绝者昵称",
  "ideaura_request_id": "请求ID",
  "ideaura_requester_id": "请求发起者ID",
  "ideaura_requester_name": "请求发起者昵称"
}
```

### Forwarded Message Segment (ideaura_forwarded)

When receiving forwarded messages, the message segment type is `ideaura_forwarded`:

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
                print(f"转发消息，源ID: {data['forward_source_id']}")

@notice.on_notice()
async def handle_notice(event):
    if event.get_platform() != "ideaura":
        return

    detail_type = event.get("detail_type")

    if detail_type == "ideaura_message_edit":
        new_content = event.get("ideaura_new_content", "")
        print(f"消息被编辑: {new_content}")

    elif detail_type == "ideaura_message_recall":
        message_id = event.get("message_id")
        print(f"消息被撤回: {message_id}")

    elif detail_type == "ideaura_friend_online":
        friend_name = event.get_user_nickname()
        print(f"好友上线: {friend_name}")

    elif detail_type == "ideaura_user_status_change":
        status = event.get("ideaura_status")
        print(f"用户状态变更: {status}")
```

---

## Multi-account Configuration

### Configuration

IdeauraAdapter supports configuring and running multiple accounts simultaneously, with each account able to choose between Token login or email/password login (one of the two).

```toml
# config.toml
# Account 1: Token login (recommended, no email/password required)
[IdeauraAdapter.accounts.default]
token = "your-token-here"        # Login Token (optional, if provided, email+password is not required)
enabled = true                   # Enable account (optional, default true)

# Account 2: Email/password login
[IdeauraAdapter.accounts.bot2]
email = "user2@example.com"      # Login email
password = "password2"           # Login password
enabled = true

# Optional: Custom server address
[IdeauraAdapter]
base_url = "https://api-cofe.allons-y.uk:3009"
ws_url = "wss://api-cofe.allons-y.uk:3009/mqtt"
heartbeat_interval = 30
```

**Configuration Description:**
- `token`: Login Token (optional, if provided, email+password is not required)
- `email`: Login email (optional for Token login, required for email/password login)
- `password`: Login password (optional for Token login, required for email/password login)
- `enabled`: Whether to enable this account (optional, default true)

**Global Configuration Items:**
- `base_url`: API server address (optional, default to Ideaura Cafe official address)
- `ws_url`: WebSocket server address (optional, default to Ideaura Cafe official address)
- `heartbeat_interval`: Heartbeat interval in seconds (optional, default 30 seconds)

### Use Send DSL to Specify Account

You can specify which account to use for sending messages through the `Using()` method:

```python
from ErisPulse.Core import adapter
ideaura = adapter.get("ideaura")

# Send message using account name
await ideaura.Send.Using("default").To("user", "user123").Text("Hello from account 1!")

# Send message using user_id (automatically matches corresponding account)
await ideaura.Send.Using("456").To("group", "chatroom").Text("Hello from account 2!")

# Use the first enabled account when not specified
await ideaura.Send.To("user", "user123").Text("Hello from default account!")
```

### Account Identification in Events

Received events automatically contain corresponding account information:

```python
from ErisPulse.Core.Event import message

@message.on_message()
async def handle_message(event):
    if event["platform"] == "ideaura":
        account_id = event["self"]["user_id"]
        print(f"Message from account: {account_id}")
```

---

## Extended Fields Description

- All special fields are prefixed with `ideaura_` to avoid conflicts with standard fields
- Raw data is preserved in the `ideaura_raw` field for easy access to the platform's complete raw data
- `self.user_id` represents the user ID of the currently logged-in account
- `ideaura_source_type`: Message source type (`chatroom`/`topic`/`private`)
- `ideaura_sender_name`: Sender nickname
- `ideaura_sender_avatar`: Sender avatar URL
- `ideaura_sender_is_bot`: Whether the sender is a bot
- `ideaura_is_self`: Whether the message was sent by the current account itself (self-messages are filtered out)
- `ideaura_topic_name`: Topic name
- `ideaura_message_type`: Message type (`normal`/`edited`/`forwarded`/`quoted`)
- `ideaura_message_subtype`: Message sub-type (`text`/`image`/`video`/`file`/`markdown`/`html`)

### File Handling Features

- File size limit: 10MB (both download and local reading have limits)
- Automatic file type detection: Detects actual type through file header magic bytes
- Intelligent filename parsing: Automatically corrects meaningless extensions like `.bin`/`.dat`/`.tmp`
- Supports bytes, URL, and local path as file input methods
- URL files are automatically downloaded and uploaded to the server

### Supported File Types

Automatically detected through magic bytes:

| Type | Extensions |
|------|------------|
| Image | png, jpg, gif, webp |
| Video | mp4, avi, flv |
| Audio | mp3, wav, ogg |
| Document | pdf, docx |

---

## Notes

1. Server address `api-cofe.allons-y.uk` is a built-in platform address and does not change with adapter name
2. The adapter uses WebSocket long connections to receive events, supports auto-reconnect (fixed 5-second delay)
3. Messages sent by the adapter itself (`isSelf: true`) are automatically filtered and will not generate events
4. `@everyone` (`AtAll()`) requires administrator privileges
5. File upload size limit is 10MB
6. Audio files are sent as `file` sub-type (the platform does not distinguish independent audio types)
7. Emoticons (`Face()`) are sent as plain text emoji
8. Please call `shutdown()` on program exit to ensure resource release