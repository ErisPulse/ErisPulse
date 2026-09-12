# Yunhu User Platform Features Documentation

YunhuUserAdapter is an adapter built based on the Yunhu User Account Protocol. It enables login via user email accounts, uses WebSocket to receive events, and provides a unified interface for event handling and message operations.

---

## Document Information

- Corresponding Module Version: 4.2.0
- Maintainer: wsu2059

## Basic Information

- **Platform Introduction**: Yunhu is an enterprise-level instant messaging platform. This adapter interacts with it through **user accounts** (not bot accounts).
- **Adapter Name**: YunhuUserAdapter
- **Multiple Account Support**: Supports identifying and configuring multiple user accounts via account names.
- **Chained Modifier Support**: Supports chained modifier methods such as `.Reply()`.
- **OneBot12 Compatibility**: Supports sending OneBot12 formatted messages.
- **Communication Method**: Logs in via email to obtain a token, uses WebSocket to receive events, and sends messages using the HTTP + Protobuf protocol.
- **Session Types**: Supports private chat (user), group chat (group), and bot sessions (bot).

## v5 Paradigm Update (4.2.0)

- **BaseConverter Inheritance**; **spawn_background Task Ownership** (WS Listening Task)
- **Complete User API Suite** (Based on yhchatAPI full.proto / v1 endpoints, protobuf over HTTP):
  - User: get_user / edit_nickname / edit_avatar
  - Friends: Address Book / Application List / Application / Accept / Ignore / Delete
  - Groups: Group Info / Member List / Create / Dissolve / Invite / Remove / Mute / Robot List
  - Conversations: Conversation List; Messages: List / Recall / Button Submission
- **Framework Soft Dependencies**: Runtime detection of ErisPulse>=2.7.1 with prompt; Version logs output on startup

## List of Functionality Already Integrated

### Event Reception (WebSocket, protobuf encoding)

| WS cmd | Event | Description |
|--------|-------|-------------|
| `push_message` | `message` | Private chat/group chat/Bot session messages (text/HTML/Markdown/image/video/audio/file/emotion/form/article/sticker/button/A2UI) |
| `edit_message` | `notice` (`message_edit`) | Message edit notification |
| `file_send_message` | `notice` (`yunhu_user_file_send`) | Super file sharing |
| `bot_board_message` | `notice` (`yunhu_user_bot_board`) | Bot bulletin board |

### Api DSL Method Mapping (YunhuHTTPClient → UserAPI v1 Endpoints)

| Category | Api Method | Endpoint | Description |
|----------|------------|----------|-------------|
| Account | `get_self_info()` | `/user/info` | Login user information (nickname/avatar/user_id) |
| User | `get_user(user_id)` | `/user/get-user` | Detailed user information |
| User | `edit_nickname(nickname)` | `/user/edit-nickname` | Modify own nickname |
| User | `edit_avatar(url)` | `/user/edit-avatar` | Modify own avatar |
| Friends | `get_friend_address_book(md5)` | `/friend/address-book-list` | Address book (cursor pagination) |
| Friends | `get_friend_requests()` | `/friend/request-list` | List of friend/group join requests |
| Friends | `friend_apply(user_id, desc)` | `/friend/apply` | Apply to add a friend |
| Friends | `friend_agree_apply(user_id)` | `/friend/agree-apply` | Accept friend request |
| Friends | `friend_ignore_apply(user_id)` | `/friend/ignore-apply` | Ignore friend request |
| Friends | `friend_delete(user_id)` | `/friend/delete-friend` | Delete a friend |
| Group | `get_group_info(group_id)` | `/group/info` | Group information |
| Group | `get_group_member_list(group_id)` | `/group/list-member` | List of group members (supports keyword search) |
| Group | `create_group(name, ...)` | `/group/create-group` | Create a group |
| Group | `dismiss_group(group_id)` | `/group/dismiss-group` | Dissolve a group |
| Group | `group_invite(group_id, user_ids)` | `/group/invite` | Invite users to join the group |
| Group | `group_remove_member(group_id, user_id)` | `/group/remove-member` | Remove a member from the group |
| Group | `group_gag_member(group_id, user_id, seconds)` | `/group/gag-member` | Mute a group member (0=unmute) |
| Group | `get_group_bot_list(group_id)` | `/group/bot-list` | List of bots in the group |
| Conversation | `get_conversation_list(md5)` | `/conversation/list` | List of conversations (cursor pagination) |
| Message | `get_message_list(chat_id, chat_type, ...)` | `/msg/list-message` | List of messages (multiple pagination variants available in HTTP client) |
| Message | `delete_message(msg_id, chat_id, chat_type)` | `/msg/recall-msg` | Recall messages (batch recall available in HTTP client) |
| Message | `button_report(...)` | `/msg/button-report` | Button click reporting |
| Actions | `get_status` / `get_version` / `get_supported_actions` | - | Runtime status/version/supported actions |

### Not Yet Integrated (Endpoints Known, full.proto Messages Complete, Extendable as Needed)

- User: Verification code login, badges, gold bean records, bind phone/email, notification settings, user data storage/retrieval
- Friends: Do-not-disturb (no-notify), delete request records
- Group: Command list, categories, recommendations, live room, edit group info/group nickname/keywords, auto-approval for group join, group file restrictions, event SSE
- Conversation: Pin/sort/delete, do-not-disturb
- Message: Forward, A2UI submission, message list image retrieval, file download records
- Group Tags: list / relate / relate-cancel / create / edit / delete / members (endpoint `/group-tag/*`)

> Extension Method: Add new methods in `YunhuHTTPClient` following the existing pattern (`_proto_request` / `_json_request` for generic wrapping), then expose them in the `Api` class. Refer to `yhchatAPI/src/api/v1/*.md` and `yhchatAPI/src/full.proto` for endpoints and message definitions.

### UserAPI Example

```python
from ErisPulse import sdk
yunhu_user = sdk.adapter.get("yunhu_user")

result = await yunhu_user.Api.get_self_info()
result = await yunhu_user.Api.get_friend_requests()          # List of friend requests
await yunhu_user.Api.friend_agree_apply(user_id)             # Accept friend request
result = await yunhu_user.Api.get_group_member_list(group_id)
result = await yunhu_user.Api.get_conversation_list()        # List of conversations
await yunhu_user.Api.delete_message(msg_id, chat_id, chat_type)  # Recall message
```

## Supported Message Types

All send methods are implemented using a fluent syntax, for example:
```python
from ErisPulse.Core import adapter
yunhu_user = adapter.get("yunhu_user")

await yunhu_user.Send.To("user", user_id).Text("Hello World!")
```

The supported message types include:
- `.Text(text: str, buttons: Optional[List] = None)` - Send plain text messages.
- `.Html(html: str, buttons: Optional[List] = None)` - Send HTML formatted messages.
- `.Markdown(markdown: str, buttons: Optional[List] = None)` - Send Markdown formatted messages.
- `.Image(file: Union[str, bytes], buttons: Optional[List] = None)` - Send image messages, supporting URLs, local paths, or binary data.
- `.Video(file: Union[str, bytes], buttons: Optional[List] = None)` - Send video messages, supporting URLs, local paths, or binary data.
- `.Audio(file: Union[str, bytes], buttons: Optional[List] = None)` - Send voice messages, supporting URLs, local paths, or binary data, with automatic audio duration detection.
- `.Voice(file: Union[str, bytes], buttons: Optional[List] = None)` - Alias for `.Audio()`.
- `.File(file: Union[str, bytes], file_name: Optional[str] = None, buttons: Optional[List] = None)` - Send file messages, supporting URLs, local paths, or binary data.
- `.Face(file: Union[str, bytes], buttons: Optional[List] = None)` - Send emoticons/stickers, supporting sticker IDs, sticker URLs, or binary image data.
- `.A2ui(a2ui_data: Union[str, Dict, List], buttons: Optional[List] = None)` - Send A2UI messages (message type 14), where A2UI JSON data is filled into the text field for sending.
- `.Edit(msg_id: str, text: str, content_type: str = "text")` - Edit an existing message.
- `.Recall(msg_id: str)` - Recall a message.
- `.Raw_ob12(message: Union[List, Dict])` - Send OneBot12 formatted messages.

### Media File Handling

All media types (images, videos, audio, files) support the following input methods:
- **URL**: `"https://example.com/image.jpg"` — Automatically downloads and uploads
- **Local Path**: `"/path/to/file.jpg"` — Automatically reads and uploads
- **Binary Data**: `open("file.jpg", "rb").read()` — Directly uploads

Media files are automatically uploaded to Qiniu Cloud storage, supporting the following features:
- Automatic file type and MIME detection using the `filetype` library
- Automatic file size calculation
- Automatic audio duration detection for audio files (supports MP3, MP4/M4A formats)

### Button Parameter Description

The `buttons` parameter is a nested list representing the layout and functionality of buttons. Each button object contains the following fields:

| Field        | Type   | Required | Description                                                                 |
|--------------|--------|----------|-----------------------------------------------------------------------------|
| `text`       | string | Yes      | Text on the button                                                          |
| `actionType` | int    | Yes      | Action type:<br>`1`: Navigate to URL<br>`2`: Copy<br>`3`: Report on click    |
| `url`        | string | No       | Used when `actionType=1`, indicating the target URL for navigation          |
| `value`      | string | No       | When `actionType=2`, this value is copied to the clipboard<br>When `actionType=3`, this value is sent to the subscriber |

Example:
```python
buttons = [
    [
        {"text": "Copy", "actionType": 2, "value": "xxxx"},
        {"text": "Click to Navigate", "actionType": 1, "url": "http://www.baidu.com"},
        {"text": "Report Event", "actionType": 3, "value": "xxxxx"}
    ]
]
await yunhu_user.Send.To("user", user_id).Buttons(buttons).Text("Message with buttons")
```

### Fluent Modifier Methods (Combinable)

Fluent modifier methods return `self`, supporting fluent calls, and must be called before the final send method:

- `.Reply(message_id: str)` - Reply to a specified message.
- `.At(user_id: str)` - Mention a specified user (text format @user_id).
- `.AtAll()` - Mention everyone (pseudo @all, sends @all text).
- `.Buttons(buttons: List)` - Add buttons.

> **Note:** Since user accounts are special, even non-admin users can pseudo-mention everyone, but `AtAll()` here only sends an @all text, which is a pseudo-mention everyone.

### Fluent Call Examples

```python
# Basic sending
await yunhu_user.Send.To("user", user_id).Text("Hello")

# Reply to a message
await yunhu_user.Send.To("group", group_id).Reply(msg_id).Text("Reply message")

# Reply + buttons
await yunhu_user.Send.To("group", group_id).Reply(msg_id).Buttons(buttons).Text("Message with reply and buttons")

# Specify account + reply + buttons
await yunhu_user.Send.Using("default").To("group", group_id).Reply(msg_id).Buttons(buttons).Text("Full fluent call")
```

### OneBot12 Message Support

The adapter supports sending OneBot12 formatted messages for cross-platform message compatibility:

- `.Raw_ob12(message: List[Dict], **kwargs)` - Send OneBot12 formatted messages.

```python
# Send OneBot12 formatted message
ob12_msg = [{"type": "text", "data": {"text": "Hello"}}]
await yunhu_user.Send.To("user", user_id).Raw_ob12(ob12_msg)

# Combined with fluent modifiers
ob12_msg = [{"type": "text", "data": {"text": "Reply message"}}]
await yunhu_user.Send.To("group", group_id).Reply(msg_id).Raw_ob12(ob12_msg)
```

`Raw_ob12` supports automatic grouping of mixed message segments:
- `text`, `mention` types can be merged into a single group for sending
- `image`, `video`, `audio`, `file`, `face`, `markdown`, `html`, `a2ui` types are each sent as separate groups
- `reply` type can be attached to any group

## Return Values of Send Methods

All send methods return a Task object, which can be awaited directly to obtain the send result. The returned result follows the ErisPulse adapter's standardized return specification:

```python
{
    "status": "ok",           // Execution status
    "retcode": 0,             // Return code
    "data": {...},            // Response data
    "message_id": "123456",   // Message ID
    "message": "",            // Error message
    "yunhu_user_raw": {...}   // Raw response data
}
```

## Unique Event Types

Use platform-specific features only after checking `platform == "yunhu_user"`

### Core Differences

1. Unique event types:
    - Super file sharing: `yunhu_user_file_send`
    - Bot announcement board: `yunhu_user_bot_board`
    - Message edit notification: `message_edit`
    - Message delete notification: `message_delete` (recall)
2. Unique message segment types:
    - Form message segment: `yunhu_user_form`
    - Article message segment: `yunhu_user_post`
    - Sticker message segment: `yunhu_user_sticker`
    - Button message segment: `yunhu_user_button`
    - A2UI message segment: `a2ui`
3. Extended fields:
    - All unique fields are prefixed with `yunhu_user_`
    - Original data is preserved in the `yunhu_user_raw` field
    - Original event type is recorded in the `yunhu_user_raw_type` field
    - In private chats, `self.user_id` represents the currently logged-in user ID

### Supported Original Event Types

| Original Event Type | OneBot12 Type | Description |
|---------------------|---------------|-------------|
| `push_message` | `message` | Pushed message (private chat, group chat, Bot session) |
| `edit_message` | `notice` (`message_edit`) | Message edit event |
| `file_send_message` | `notice` (`yunhu_user_file_send`) | Super file sharing event |
| `bot_board_message` | `notice` (`yunhu_user_bot_board`) | Bot announcement board event |

> Other event types (such as `heartbeat_ack`, `draft_input`, `stream_message`, etc.) will be ignored.

### OneBot12 Supported detail_type

| OneBot12 detail_type | Yunhu chat_type | Description |
|----------------------|-----------------|-------------|
| `private` | 1 | Private chat message |
| `group` | 2 | Group chat message |
| `bot` | 3 | Bot session |

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
    
    # Check for unique segment types in the message
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

## Extension Field Description

- All custom fields are prefixed with `yunhu_user_` to avoid conflicts with standard fields.
- The original data is preserved in the `yunhu_user_raw` field, allowing access to the complete raw data from the Yunhu platform.
- The original event type is recorded in the `yunhu_user_raw_type` field (such as `push_message`, `edit_message`, etc.).
- `self.user_id` represents the current logged-in user ID (obtained from the login response).
- Super file sharing is provided through the `yunhu_user_file_send` field, which contains file sharing data.
- Robot announcement board data is provided through the `yunhu_user_bot_board` field.

### Custom Message Segment Types

#### Form Message Segment (yunhu_user_form)

When `content_type` is 5, the message segment type is `yunhu_user_form`:

```json
{
    "type": "yunhu_user_form",
    "data": {
        "form": "Form data"
    }
}
```

#### Article Message Segment (yunhu_user_post)

When `content_type` is 6, the message segment type is `yunhu_user_post`:

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
|-------|------|-------------|
| `post_id` | string | Unique identifier for the article |
| `post_title` | string | Article title |
| `post_content` | string | Article content |

#### Sticker Message Segment (yunhu_user_sticker)

When `content_type` is 7, the message segment type is `yunhu_user_sticker`:

```json
{
    "type": "yunhu_user_sticker",
    "data": {
        "file_id": "Sticker image URL"
    }
}
```

| Field | Type | Description |
|-------|------|-------------|
| `file_id` | string | Sticker image URL |

#### Button Message Segment (yunhu_user_button)

When the message contains buttons, a `yunhu_user_button` message segment is appended:

```json
{
    "type": "yunhu_user_button",
    "data": {
        "buttons": [[{"text": "Button text", "actionType": 3, "value": "value"}]]
    }
}
```

#### A2UI Message Segment (a2ui)

When `content_type` is 14, the message segment type is `a2ui`:

```json
{
    "type": "a2ui",
    "data": {
        "a2ui": "A2UI JSON data"
    }
}
```

## Multi-Account Configuration

### Configuration Description

The `YunhuUserAdapter` supports configuring and running multiple user accounts simultaneously.

```toml
# config.toml
[YunhuUserAdapter]
ws_reconnect_interval = 30  # WebSocket reconnection interval (seconds)
ws_timeout = 70             # WebSocket timeout (seconds)

[YunhuUserAdapter.accounts.default]
email = "user1@example.com"  # User email (required)
password = "password1"       # User password (required)
platform = "windows"         # Login platform (optional, default: windows)
device_id = ""               # Device ID (optional, auto-generated if not provided)
enabled = true               # Whether to enable this account (optional, default: true)

[YunhuUserAdapter.accounts.account2]
email = "user2@example.com"
password = "password2"
platform = "android"
device_id = "fixed_device_id_2"
enabled = true
```

**Configuration Item Description:**
- `email`: User email (required), used to log in to the Yunhu platform
- `password`: User password (required)
- `platform`: Login platform identifier (optional, default: `windows`), valid values: `windows`, `macos`, `linux`, `ios`, `android`
- `device_id`: Device ID (optional, auto-generated if not provided), it is recommended to set a fixed value to maintain session consistency
- `enabled`: Whether to enable this account (optional, default: `true`)

**Adapter-Level Configuration:**
- `ws_reconnect_interval`: WebSocket reconnection interval (seconds, default: 30)
- `ws_timeout`: WebSocket timeout (seconds, default: 70)

**Important Notes:**
1. The adapter uses email login to obtain a token, and receives events via WebSocket after login.
2. After a WebSocket connection is disconnected, it will automatically reconnect, with up to 3 retry attempts.
3. It is recommended to set a fixed `device_id` for each account to maintain session consistency.
4. Template accounts (default email and password) that have not been modified will be automatically skipped.

### Using Send DSL to Specify Account

You can specify which account to use for sending messages using the `Using()` method. This method supports two types of parameters:
- **Account name**: The account name in the configuration (e.g., `default`, `account2`)
- **user_id**: The user ID obtained after login

```python
from ErisPulse.Core import adapter
yunhu_user = adapter.get("yunhu_user")

# Send message using account name
await yunhu_user.Send.Using("default").To("user", "user123").Text("Hello from account1!")

# Send message using user_id (automatically matches the corresponding account)
await yunhu_user.Send.Using("user_id_here").To("group", "group456").Text("Hello from user!")

# Use the first enabled account if not specified
await yunhu_user.Send.To("user", "user123").Text("Hello from default account!")
```

> **Note:** When using `user_id`, the system automatically finds the matching account in the configuration. This is especially useful when handling event replies, where you can directly use `event["self"]["user_id"]` to reply from the same account.

### Account Identifier in Events

Received events will automatically include the corresponding user ID information:

```python
from ErisPulse.Core.Event import message

@message.on_message()
async def handle_message(event):
    if event["platform"] == "yunhu_user":
        # Get current logged-in user ID
        my_user_id = event["self"]["user_id"]
        print(f"Message received from account: {my_user_id}")
        
        # Reply to the message using the same account
        yunhu_user = adapter.get("yunhu_user")
        await yunhu_user.Send.Using(my_user_id).To(
            event["detail_type"],
            event["user_id"] if event["detail_type"] == "private" else event["group_id"]
        ).Text("Reply message")
```

### Log Information

The adapter will automatically include account information in the logs, which is useful for debugging and tracking:

```
[INFO] Account default (user1@example.com) logged in successfully, user ID: 12345678
[INFO] Account default WebSocket listening task started
[INFO] Account account2 (user2@example.com) logged in successfully, user ID: 87654321
```

### Management Interface

```python
# Get all account information
accounts = yunhu_user.accounts
# Return format: {"default": {"name": "default", "email": "...", "token": "...", "user_id": "...", ...}, ...}

# Check if an account is enabled
for account_name, account_config in yunhu_user._account_configs.items():
    print(f"{account_name}: enabled={account_config.enabled}")

# Get HTTP client by account name
http_client = yunhu_user._get_http_client("default")

# Find account by user_id
account_name = yunhu_user._get_account_by_user_id("12345678")
```

## API Calls

The adapter provides a `call_api` method that supports directly calling the platform API:

```python
# Send a message
result = await yunhu_user.call_api("/send", 
    target_type="group", 
    target_id="group_id",
    account_id="default",
    message={"text": "Hello", "msg_type": 1}
)

# Edit a message
result = await yunhu_user.call_api("/edit",
    target_type="group",
    target_id="group_id",
    msg_id="msg_id",
    text="New content",
    content_type="text"
)

# Recall a message
result = await yunhu_user.call_api("/recall",
    target_type="group",
    target_id="group_id",
    msg_id="msg_id"
)

# Recall multiple messages
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

# Report button event
result = await yunhu_user.call_api("/button_report",
    chat_id="group_id",
    chat_type=2,
    msg_id="msg_id",
    user_id="user_id",
    button_value="button_value"
)
```

**Supported API endpoints:**

| Endpoint | Description |
|----------|-------------|
| `/send` | Send a message |
| `/edit` | Edit a message |
| `/recall` | Recall a message |
| `/recall_batch` | Recall multiple messages |
| `/list` | Get message list |
| `/list_by_seq` | Get messages by sequence |
| `/list_by_mid_seq` | Get messages by message ID and sequence |
| `/list_edit_record` | Get message edit records |
| `/button_report` | Report button event |