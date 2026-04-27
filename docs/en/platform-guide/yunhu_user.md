# Yunhu User Platform Features Documentation

YunhuUserAdapter is an adapter based on the Yunhu user account protocol, allowing login through user email accounts, receiving events via WebSocket, and providing unified event processing and message operation interfaces.

---

## Document Information

- Corresponding Module Version: 1.4.0
- Maintainer: wsu2059

## Basic Information

- Platform Introduction: Yunhu is an enterprise-level instant messaging platform. This adapter interacts with it through **user accounts** (rather than bot accounts).
- Adapter Name: YunhuUserAdapter
- Multi-account Support: Supports identifying and configuring multiple user accounts through account names.
- Chain Decorator Support: Supports chained decorator methods like `.Reply()`.
- OneBot12 Compatibility: Supports sending OneBot12 format messages.
- Communication Method: Login via email to get token, use WebSocket to receive events, HTTP + Protobuf protocol to send messages.
- Session Types: Supports private chat (user), group chat (group), and bot chat (bot).

## Supported Message Sending Types

All sending methods are implemented through chained syntax, for example:
```python
from ErisPulse.Core import adapter
yunhu_user = adapter.get("yunhu_user")

await yunhu_user.Send.To("user", user_id).Text("Hello World!")
```

Supported sending types include:
- `.Text(text: str, buttons: Optional[List] = None)`: Send plain text messages.
- `.Html(html: str, buttons: Optional[List] = None)`: Send HTML format messages.
- `.Markdown(markdown: str, buttons: Optional[List] = None)`: Send Markdown format messages.
- `.Image(file: Union[str, bytes], buttons: Optional[List] = None)`: Send image messages, supporting URLs, local paths, or binary data.
- `.Video(file: Union[str, bytes], buttons: Optional[List] = None)`: Send video messages, supporting URLs, local paths, or binary data.
- `.Audio(file: Union[str, bytes], buttons: Optional[List] = None)`: Send voice messages, supporting URLs, local paths, or binary data, with automatic audio duration detection.
- `.Voice(file: Union[str, bytes], buttons: Optional[List] = None)`: Alias for `.Audio()`.
- `.File(file: Union[str, bytes], file_name: Optional[str] = None, buttons: Optional[List] = None)`: Send file messages, supporting URLs, local paths, or binary data.
- `.Face(file: Union[str, bytes], buttons: Optional[List] = None)`: Send emoji/sticker messages, supporting sticker IDs, sticker URLs, or binary image data.
- `.A2ui(a2ui_data: Union[str, Dict, List], buttons: Optional[List] = None)`: Send A2UI messages (message type 14), A2UI JSON data will be filled in the text field to send.
- `.Edit(msg_id: str, text: str, content_type: str = "text")`: Edit existing messages.
- `.Recall(msg_id: str)`: Recall messages.
- `.Raw_ob12(message: Union[List, Dict])`: Send OneBot12 format messages.

### Media File Processing

All media types (images, videos, audio, files) support the following input methods:
- **URL**: `"https://example.com/image.jpg"` — Automatically download and then upload
- **Local Path**: `"/path/to/file.jpg"` — Automatically read and then upload
- **Binary Data**: `open("file.jpg", "rb").read()` — Direct upload

Media files are automatically uploaded to Qiniu cloud storage, supporting the following features:
- Automatically detect file type and MIME using the `filetype` library
- Automatically calculate file size
- Automatically detect audio duration for audio files (supporting MP3, MP4/M4A formats)

### Button Parameter Description

The `buttons` parameter is a nested list representing the button layout and functionality. Each button object contains the following fields:

| Field         | Type   | Required | Description                                                                 |
|--------------|--------|----------|----------------------------------------------------------------------------|
| `text`       | string | Yes      | Text on the button                                                        |
| `actionType` | int    | Yes      | Action type:<br>`1`: Jump to URL<br>`2`: Copy<br>`3`: Click report           |
| `url`        | string | No       | Used when `actionType=1`, represents the target URL to jump to            |
| `value`      | string | No       | When `actionType=2`, this value will be copied to clipboard<br>When `actionType=3`, this value will be sent to the subscription end |

Example:
```python
buttons = [
    [
        {"text": "Copy", "actionType": 2, "value": "xxxx"},
        {"text": "Click to Jump", "actionType": 1, "url": "http://www.baidu.com"},
        {"text": "Report Event", "actionType": 3, "value": "xxxxx"}
    ]
]
await yunhu_user.Send.To("user", user_id).Buttons(buttons).Text("Message with buttons")
```

### Chained Decorator Methods (Combinable)

Chained decorator methods return `self`, supporting chained calls and must be called before the final sending method:

- `.Reply(message_id: str)`: Reply to a specific message.
- `.At(user_id: str)`: @mention a specific user (in text form @user_id).
- `.AtAll()`: @mention everyone (pseudo @all, sends @all text).
- `.Buttons(buttons: List)`: Add buttons.

> **Note:** Because user accounts are special, even non-admin users can @everyone, but `AtAll()` here only sends a @everyone text, which is a pseudo @everyone.

### Chained Call Examples

```python
# Basic sending
await yunhu_user.Send.To("user", user_id).Text("Hello")

# Reply to message
await yunhu_user.Send.To("group", group_id).Reply(msg_id).Text("Reply message")

# Reply + buttons
await yunhu_user.Send.To("group", group_id).Reply(msg_id).Buttons(buttons).Text("Message with reply and buttons")

# Specify account + reply + buttons
await yunhu_user.Send.Using("default").To("group", group_id).Reply(msg_id).Buttons(buttons).Text("Complete chained call")
```

### OneBot12 Message Support

The adapter supports sending OneBot12 format messages for cross-platform message compatibility:

- `.Raw_ob12(message: List[Dict], **kwargs)`: Send OneBot12 format messages.

```python
# Send OneBot12 format message
ob12_msg = [{"type": "text", "data": {"text": "Hello"}}]
await yunhu_user.Send.To("user", user_id).Raw_ob12(ob12_msg)

# With chained decorators
ob12_msg = [{"type": "text", "data": {"text": "Reply message"}}]
await yunhu_user.Send.To("group", group_id).Reply(msg_id).Raw_ob12(ob12_msg)
```

Raw_ob12 supports automatically grouping and processing mixed message segments:
- `text`, `mention` types can be merged into one group for sending
- `image`, `video`, `audio`, `file`, `face`, `markdown`, `html`, `a2ui` etc. types each form their own group
- `reply` type can be attached to any group

## Method Return Values

All sending methods return a Task object, which can be directly awaited to get the sending result. The return result follows the ErisPulse adapter standardized return specification:

```python
{
    "status": "ok",           // Execution status
    "retcode": 0,             // Return code
    "data": {...},            // Response data
    "message_id": "123456",   // Message ID
    "message": "",            // Error message
    "yunhu_user_raw": {...}   // Original response data
}
```

## Special Event Types

Requires checking `platform == "yunhu_user"` before using platform-specific features

### Core Differences

1. Special event types:
    - Super file sharing: `yunhu_user_file_send`
    - Bot announcement board: `yunhu_user_bot_board`
    - Message edit notification: `message_edit`
    - Message deletion notification: `message_delete` (recall)
2. Special message segment types:
    - Form message segment: `yunhu_user_form`
    - Article message segment: `yunhu_user_post`
    - Sticker message segment: `yunhu_user_sticker`
    - Button message segment: `yunhu_user_button`
    - A2UI message segment: `a2ui`
3. Extended fields:
    - All special fields are prefixed with `yunhu_user_`
    - Original data is retained in the `yunhu_user_raw` field
    - Original event type is recorded in the `yunhu_user_raw_type` field
    - In private chats, `self.user_id` represents the current logged-in user ID

### Supported Original Event Types

| Original Event Type | OneBot12 Type | Description |
|--------------------|--------------|-------------|
| `push_message` | `message` | Push message (private chat, group chat, bot chat) |
| `edit_message` | `notice` (`message_edit`) | Message edit event |
| `file_send_message` | `notice` (`yunhu_user_file_send`) | Super file sharing event |
| `bot_board_message` | `notice` (`yunhu_user_bot_board`) | Bot announcement board event |

> Other event types (such as `heartbeat_ack`, `draft_input`, `stream_message`, etc.) will be ignored.

### OneBot12 Supported detail_type

| OneBot12 detail_type | Yunhu chat_type | Description |
|---------------------|---------------|-------------|
| `private` | 1 | Private chat message |
| `group` | 2 | Group chat message |
| `bot` | 3 | Bot chat |

### Message Event Example

```python
{
    "id": "event_id",
    "time": 1234567890,
    "type": "message",
    "detail_type": "group",
    "platform": "yunhu_user",
    "self": {
        "platform": "yunhu_user",
        "user_id": "your_user_id"
    },
    "message": [
        {"type": "text", "data": {"text": "Message content"}}
    ],
    "alt_message": "Message content",
    "user_id": "sender_user_id",
    "user_nickname": "Sender nickname",
    "group_id": "group_id",
    "message_id": "msg_id",
    "yunhu_user_raw": {...},
    "yunhu_user_raw_type": "push_message"
}
```

### Message Edit Notification Example

```python
{
    "type": "notice",
    "detail_type": "message_edit",
    "platform": "yunhu_user",
    "self": {
        "platform": "yunhu_user",
        "user_id": "your_user_id"
    },
    "message_id": "msg_id",
    "user_id": "sender_user_id",
    "user_nickname": "Sender nickname",
    "edit_time": 1234567890,
    "group_id": "group_id",
    "yunhu_user_raw": {...},
    "yunhu_user_raw_type": "edit_message"
}
```

### Super File Sharing Event Example

```python
{
    "type": "notice",
    "detail_type": "yunhu_user_file_send",
    "platform": "yunhu_user",
    "self": {
        "platform": "yunhu_user",
        "user_id": "your_user_id"
    },
    "user_id": "send_user_id",
    "user_nickname": "",
    "yunhu_user_file_send": {
        "send_user_id": "Sender ID",
        "user_id": "Recipient user ID",
        "send_type": "Send type",
        "data": "File data"
    },
    "yunhu_user_raw": {...},
    "yunhu_user_raw_type": "file_send_message"
}
```

### Bot Announcement Board Event Example

```python
{
    "type": "notice",
    "detail_type": "yunhu_user_bot_board",
    "platform": "yunhu_user",
    "self": {
        "platform": "yunhu_user",
        "user_id": "your_user_id"
    },
    "bot_id": "bot_id",
    "bot_name": "Bot name",
    "yunhu_user_bot_board": {
        "bot_id": "bot_id",
        "chat_id": "chat_id",
        "chat_type": 1,
        "content": "Announcement content",
        "content_type": 1,
        "last_update_time": 1234567890
    },
    "yunhu_user_raw": {...},
    "yunhu_user_raw_type": "bot_board_message"
}
```

### Event Handling Example

```python
from ErisPulse.Core.Event import message, notice

@message.on_message()
async def handle_yunhu_user_message(event):
    """Handle Yunhu user messages"""
    if event.get("platform") != "yunhu_user":
        return
    
    user_id = event.get("user_id", "")
    user_nickname = event.get("user_nickname", "")
    alt_message = event.get("alt_message", "")
    
    print(f"User {user_nickname}({user_id}): {alt_message}")
    
    # Check for special types in message segments
    for segment in event.get("message", []):
        seg_type = segment.get("type", "")
        
        if seg_type == "yunhu_user_form":
            form_data = segment["data"]["form"]
            print(f"Received form message: {form_data}")
        
        elif seg_type == "yunhu_user_post":
            post_data = segment["data"]
            print(f"Received article message: {post_data.get('post_title', '')}")
        
        elif seg_type == "yunhu_user_sticker":
            sticker_url = segment["data"]["file_id"]
            print(f"Received sticker message: {sticker_url}")
        
        elif seg_type == "yunhu_user_button":
            buttons = segment["data"]["buttons"]
            print(f"Message contains buttons: {buttons}")
        
        elif seg_type == "a2ui":
            a2ui_data = segment["data"]["a2ui"]
            print(f"Received A2UI message: {a2ui_data}")
    
    # Use event.reply() to automatically reply
    await event.reply(f"Echo: {alt_message}")

@notice.on_notice()
async def handle_yunhu_user_notice(event):
    """Handle Yunhu user notification events"""
    if event.get("platform") != "yunhu_user":
        return
    
    detail_type = event.get("detail_type", "")
    
    if detail_type == "message_edit":
        message_id = event.get("message_id", "")
        user_nickname = event.get("user_nickname", "")
        edit_time = event.get("edit_time", 0)
        print(f"User {user_nickname} edited message {message_id}")
    
    elif detail_type == "yunhu_user_file_send":
        file_data = event.get("yunhu_user_file_send", {})
        print(f"Received super file sharing: {file_data}")
    
    elif detail_type == "yunhu_user_bot_board":
        board_data = event.get("yunhu_user_bot_board", {})
        bot_name = event.get("bot_name", "")
        print(f"Bot {bot_name} published announcement: {board_data.get('content', '')}")
```

## Extended Field Description

- All special fields are prefixed with `yunhu_user_` to avoid conflicts with standard fields
- Original data is retained in the `yunhu_user_raw` field for accessing complete original data from Yunhu platform
- Original event type is recorded in the `yunhu_user_raw_type` field (such as `push_message`, `edit_message`, etc.)
- `self.user_id` represents the current logged-in user ID (obtained from login response)
- Super file sharing provides file sharing data through the `yunhu_user_file_send` field
- Bot announcement board provides announcement data through the `yunhu_user_bot_board` field

### Special Message Segment Types

#### Form Message Segment (yunhu_user_form)

When content_type is 5, the message segment type is `yunhu_user_form`:

```json
{
    "type": "yunhu_user_form",
    "data": {
        "form": "Form data"
    }
}
```

#### Article Message Segment (yunhu_user_post)

When content_type is 6, the message segment type is `yunhu_user_post`:

```json
{
    "type": "yunhu_user_post",
    "data": {
        "post_id": "Article ID",
        "post_title": "Article title",
        "post_content": "Article content"
    }
}
```

| Field | Type | Description |
|------|------|-------------|
| `post_id` | string | Unique identifier for the article |
| `post_title` | string | Article title |
| `post_content` | string | Article content |

#### Sticker Message Segment (yunhu_user_sticker)

When content_type is 7, the message segment type is `yunhu_user_sticker`:

```json
{
    "type": "yunhu_user_sticker",
    "data": {
        "file_id": "Sticker image URL"
    }
}
```

| Field | Type | Description |
|------|------|-------------|
| `file_id` | string | Sticker image URL |

#### Button Message Segment (yunhu_user_button)

When the message contains buttons, a `yunhu_user_button` message segment is attached:

```json
{
    "type": "yunhu_user_button",
    "data": {
        "buttons": [[{"text": "Button text", "actionType": 3, "value": "Value"}]]
    }
}
```

#### A2UI Message Segment (a2ui)

When content_type is 14, the message segment type is `a2ui`:

```json
{
    "type": "a2ui",
    "data": {
        "a2ui": "A2UI JSON data"
    }
}
```

---

## Multi-Account Configuration

### Configuration Description

YunhuUserAdapter supports configuring and running multiple user accounts simultaneously.

```toml
# config.toml
[YunhuUserAdapter]
ws_reconnect_interval = 30  # WebSocket reconnect interval (seconds)
ws_timeout = 70             # WebSocket timeout (seconds)

[YunhuUserAdapter.accounts.default]
email = "user1@example.com"  # User email (required)
password = "password1"       # User password (required)
platform = "windows"         # Login platform (optional, default windows)
device_id = ""               # Device ID (optional, auto-generated if not specified)
enabled = true               # Whether to enable (optional, default true)

[YunhuUserAdapter.accounts.account2]
email = "user2@example.com"
password = "password2"
platform = "android"
device_id = "fixed_device_id_2"
enabled = true
```

**Configuration Item Description:**
- `email`: User email (required), used to login to Yunhu platform
- `password`: User password (required)
- `platform`: Login platform identifier (optional, default `windows`), optional values: `windows`, `macos`, `linux`, `ios`, `android`
- `device_id`: Device ID (optional, auto-generated if not specified), it is recommended to set a fixed value to maintain session consistency
- `enabled`: Whether to enable this account (optional, default `true`)

**Adapter Level Configuration:**
- `ws_reconnect_interval`: WebSocket reconnect interval (seconds, default 30)
- `ws_timeout`: WebSocket timeout (seconds, default 70)

**Important Notes:**
1. The adapter uses email login to get tokens, and receives events through WebSocket after login
2. WebSocket connection will automatically reconnect after disconnection, with a maximum of 3 retry attempts
3. It is recommended to set a fixed `device_id` for each account to maintain session consistency
4. Template accounts with unchanged default email and password will be automatically skipped

### Using Send DSL to Specify Accounts

You can specify which account to use for sending messages through the `Using()` method. This method supports two parameters:
- **Account name**: The account name in the configuration (such as `default`, `account2`)
- **user_id**: The user ID obtained after login

```python
from ErisPulse.Core import adapter
yunhu_user = adapter.get("yunhu_user")

# Send message using account name
await yunhu_user.Send.Using("default").To("user", "user123").Text("Hello from account1!")

# Send message using user_id (automatically matches corresponding account)
await yunhu_user.Send.Using("user_id_here").To("group", "group456").Text("Hello from user!")

# Use the first enabled account when not specified
await yunhu_user.Send.To("user", "user123").Text("Hello from default account!")
```

> **Tip:** When using `user_id`, the system will automatically find the matching account in the configuration. This is especially useful when handling event replies, where you can directly use `event["self"]["user_id"]` to reply to the same account.

### Account Identification in Events

Received events will automatically contain the corresponding user ID information:

```python
from ErisPulse.Core.Event import message

@message.on_message()
async def handle_message(event):
    if event["platform"] == "yunhu_user":
        # Get current logged-in user ID
        my_user_id = event["self"]["user_id"]
        print(f"Message from account: {my_user_id}")
        
        # Reply using the same account
        yunhu_user = adapter.get("yunhu_user")
        await yunhu_user.Send.Using(my_user_id).To(
            event["detail_type"],
            event["user_id"] if event["detail_type"] == "private" else event["group_id"]
        ).Text("Reply message")
```

### Log Information

The adapter will automatically include account information in logs for debugging and tracking:

```
[INFO] Account default (user1@example.com) login successful, user ID: 12345678
[INFO] Account default WebSocket listening task started
[INFO] Account account2 (user2@example.com) login successful, user ID: 87654321
```

### Management Interface

```python
# Get all account information
accounts = yunhu_user.accounts
# Return format: {"default": {"name": "default", "email": "...", "token": "...", "user_id": "...", ...}, ...}

# Check if account is enabled
for account_name, account_config in yunhu_user._account_configs.items():
    print(f"{account_name}: enabled={account_config.enabled}")

# Get HTTP client by account name
http_client = yunhu_user._get_http_client("default")

# Find account by user_id
account_name = yunhu_user._get_account_by_user_id("12345678")
```

## API Calls

The adapter provides a `call_api` method that supports direct platform API calls:

```python
# Send message
result = await yunhu_user.call_api("/send", 
    target_type="group", 
    target_id="group_id",
    account_id="default",
    message={"text": "Hello", "msg_type": 1}
)

# Edit message
result = await yunhu_user.call_api("/edit",
    target_type="group",
    target_id="group_id",
    msg_id="msg_id",
    text="New content",
    content_type="text"
)

# Recall message
result = await yunhu_user.call_api("/recall",
    target_type="group",
    target_id="group_id",
    msg_id="msg_id"
)

# Batch recall messages
result = await yunhu_user.call_api("/recall_batch",
    target_type="group",
    target_id="group_id",
    msg_id_list=["msg_id_1", "msg_id_2"]
)

# Get message list
result = await yunhu_user.call_api("/list",
    chat_id="group_id",
    chat_type=2,
    msg_count=10,
    msg_id=""
)

# Get message edit records
result = await yunhu_user.call_api("/list_edit_record",
    msg_id="msg_id",
    size=10,
    page=1
)

# Button event report
result = await yunhu_user.call_api("/button_report",
    chat_id="group_id",
    chat_type=2,
    msg_id="msg_id",
    user_id="user_id",
    button_value="button_value"
)
```

**Supported API Endpoints:**

| Endpoint | Description |
|----------|-------------|
| `/send` | Send message |
| `/edit` | Edit message |
| `/recall` | Recall message |
| `/recall_batch` | Batch recall messages |
| `/list` | Get message list |
| `/list_by_seq` | Get message by sequence |
| `/list_by_mid_seq` | Get message by message ID and sequence |
| `/list_edit_record` | Get message edit records |
| `/button_report` | Button event report |