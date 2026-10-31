# Matrix Platform Feature Documentation

MatrixAdapter is an adapter built on the [Matrix protocol](https://spec.matrix.org/), integrating all core functional modules of the Matrix protocol and providing unified event handling and message operation interfaces.

---

## Document Information

- Corresponding module version: 4.4.0
- Maintainer: ErisPulse

## Basic Information

- Platform Overview: Matrix is an open, decentralized communication protocol supporting various scenarios such as private chats and group chats.
- Adapter Name: MatrixAdapter
- Multi-account Support: Supports simultaneous configuration of multiple Matrix accounts
- Connection Method: Long Polling (via Matrix Sync API `/sync`)
- Authentication Method: Based on access_token or user_id + password to obtain token
- Chainable Modifier Support: Supports chainable modifier methods such as `.Reply()`, `.At()`, and `.AtAll()`
- OneBot12 Compatibility: Supports sending OneBot12 formatted messages

## Configuration Explanation

MatrixAdapter supports multi-account configuration, with each account having independent homeserver and authentication information.

```toml
# config.toml
# Account 1
[Matrix_Adapter.accounts.default]
homeserver = "https://matrix.org"          # Matrix server address (required)
access_token = "YOUR_ACCESS_TOKEN"          # Access token (either this or user_id+password)
user_id = ""                                # Matrix user ID (e.g. @bot:matrix.org)
password = ""                               # Matrix user password
auto_accept_invites = true                  # Whether to automatically accept room invites (optional, default is true)
enabled = true                              # Whether to enable (optional, default is true)

# Account 2
[Matrix_Adapter.accounts.bot2]
homeserver = "https://matrix.example.com"
access_token = "ANOTHER_TOKEN"
enabled = true
```

> Compatibility with old configuration: If an old single-account `[Matrix_Adapter]` configuration (including access_token) is detected, it will be automatically migrated to `accounts.default`.

**Configuration Item Explanation (per account):**
- `homeserver`: Matrix server address (required), default is `https://matrix.org`
- `access_token`: Access token, obtainable from a Matrix client. If you already have a token, simply fill it in
- `user_id`: Matrix user ID (e.g. `@bot:matrix.org`), used in conjunction with `password` for login
- `password`: Matrix user password, used for automatic login to obtain access_token
- `auto_accept_invites`: Whether to automatically accept room invites, default is `true`
- `enabled`: Whether to enable this account (optional, default is true)

**Authentication Method:**
- Method 1 (Recommended): Directly provide `access_token`
- Method 2: Provide `user_id` and `password`, the adapter will automatically call the login interface to obtain the token

## v5 Paradigm Update (4.2.0)

- **BaseConverter Inheritance**: Common fields of converters are built by framework build_base_event
- **Api DSL**: get_self_info/get_user_info/get_group_info/get_group_list/get_group_member_list/leave_group/delete_message(redact) + meta actions
- **Message Event Supplement message_id** (event_id); Message registration table supports delete_message
- **spawn_background Task Assignment**: Synchronous/heartbeat tasks use runtime.spawn_background
- **Framework Soft Dependency**: Runtime detects ErisPulse>=2.7.1 and prompts; Version logs output on startup
- Matrix has no native button capability, standard keyboard segment is gracefully ignored (no error)

## End-to-End Encryption (4.3.0)

Starting from 4.3.0, the adapter natively supports end-to-end encryption for encrypted rooms (based on matrix-nio[e2e] / vodozemac):

```toml
[Matrix_Adapter.accounts.default]
user_id = "@bot:matrix.org"
password = "YOUR_PASSWORD"
encryption_enabled = true       # Enable (default false, existing deployments unaffected)
trust_all_devices = true        # Automatically trust unverified devices (default; false for strict mode)
```

- Automatic decryption/encryption for encrypted room message sending/receiving, media end-to-end encryption (`m.file.encrypted`)
- `device_id` is automatically parsed and persisted; sessions are stored in `store_path` (default `data/matrix/<account name>`, **do not delete**, otherwise historical messages cannot be decrypted)
- Event Mixin adds `event.is_encrypted()`; media segment carries `matrix_encrypted_file` (JWK), which can be decrypted using `MatrixAdapter.decrypt_media()`
- Cross-signing and server-side key backup are not supported; requires Python >= 3.10
- If not enabled or matrix-nio is not installed, it automatically falls back to plaintext mode

See the [adapter README](https://github.com/ErisPulse/ErisPulse-MatrixAdapter) for detailed explanation.

### Standard API Action Examples

```python
from ErisPulse import sdk
matrix = sdk.adapter.get("matrix")
result = await matrix.Api.get_self_info()            # /account/whoami
result = await matrix.Api.get_group_info(room_id)    # m.room.name
result = await matrix.Api.get_group_list()           # /joined_rooms
await matrix.Api.delete_message(event_id)            # redact (room_id completed in registration table)
```

---

### Supported Platform Capabilities

- **Events**: Message events (m.room.message: text/image/file/audio/video/reply/edit), member changes (m.room.member), room name changes, and other status events
- **Sessions**: Private chat (DM rooms are automatically discovered) / group (room); Supports sending Text/Image/File/Voice/Video/Markdown/Raw_ob12
- **API**: whoami/profile/joined_rooms/room status/member list/leave/redact (see above Api DSL)

---

## Supported Message Sending Types

All sending methods use chainable syntax, for example:
```python
from ErisPulse.Core import adapter
matrix = adapter.get("matrix")

await matrix.Send.To("group", room_id).Text("Hello World!")
```

Supported sending types include:
- `.Text(text: str)`: Send plain text messages.
- `.Image(file: bytes | str)`: Send image messages, supporting file paths, URLs, MXC URIs, and binary data.
- `.Voice(file: bytes | str)`: Send voice messages, supporting file paths, URLs, MXC URIs, and binary data.
- `.Video(file: bytes | str)`: Send video messages, supporting file paths, URLs, MXC URIs, and binary data.
- `.File(file: bytes | str, filename: str = "")`: Send file messages, supporting file paths, URLs, MXC URIs, and binary data.
- `.Notice(text: str)`: Send notification messages (m.notice type in Matrix).
- `.Html(html: str, fallback: str = "")`: Send HTML formatted messages, supporting rich text content.
- `.MergeForward(nodes, title="Merged Chat Record")`: Send merged forward messages (formatted_body blockquote form; whitelist will strip details/inline styles).
- `.Raw_ob12(message: List[Dict], **kwargs)`: Send OneBot12 formatted messages.

### Chainable Modifier Methods (can be combined)

Chainable modifier methods return `self`, supporting chained calls, and must be called before the final sending method:

- `.Reply(message_id: str)`: Reply to a specific message (via Matrix `m.in_reply_to` relationship).
- `.At(user_id: str)`: Mention a specific user (via Matrix `m.mentions` field).
- `.AtAll()`: Mention everyone in the room (via Matrix `@room` mention).

### Chained Call Examples

```python
# Basic sending
await matrix.Send.To("user", dm_room_id).Text("Hello")

# Reply to a message
await matrix.Send.To("group", room_id).Reply("$event_id").Text("Reply message")

# Mention a user
await matrix.Send.To("group", room_id).At("@user:matrix.org").Text("Hello")

# Mention everyone
await matrix.Send.To("group", room_id).AtAll().Text("Announcement")

# Combination: Reply + Mention
await matrix.Send.To("group", room_id).Reply("$event_id").At("@user:matrix.org").Text("Composite message")

# Send HTML message
await matrix.Send.To("group", room_id).Html("<h1>Title</h1><p>Content</p>", fallback="Title\nContent")

# Send notification message
await matrix.Send.To("group", room_id).Notice("System notification")
```

### OneBot12 Message Support

The adapter supports sending OneBot12 formatted messages, facilitating cross-platform message compatibility:

```python
# Send OneBot12 formatted message
ob12_msg = [{"type": "text", "data": {"text": "Hello"}}]
await matrix.Send.To("user", dm_room_id).Raw_ob12(ob12_msg)

# Combined with chainable modifiers
ob12_msg = [{"type": "text", "data": {"text": "Reply message"}}]
await matrix.Send.To("group", room_id).Reply("$event_id").Raw_ob12(ob12_msg)

# Complex message
ob12_msg = [
    {"type": "text", "data": {"text": "Look at this picture: "}},
    {"type": "image", "data": {"file": "https://example.com/image.png"}},
    {"type": "text", "data": {"text": "Isn't it nice? "}}
]
await matrix.Send.To("group", room_id).Raw_ob12(ob12_msg)
```

## Send Method Return Values

All sending methods return a Task object, which can be awaited to obtain the sending result. The returned result follows the ErisPulse adapter standard return specification:

```python
{
    "status": "ok",           // Execution status: "ok" or "failed"
    "retcode": 0,             // Return code
    "data": {...},            // Response data
    "message_id": "$event_id", // Matrix event ID
    "message": "",            // Error message
    "matrix_raw": {...}       // Raw response data
}
```

### Error Code Explanation

| retcode | Description |
|---------|-------------|
| 0 | Success |
| 32000 | Request timeout or media upload failed |
| 33000 | API call exception |
| 34000 | API returned unexpected format or business error |

## Unique Event Types

Use `platform=="matrix"` to detect and use this platform-specific feature

### Core Differences

1. **Decentralized Architecture**: Matrix is a decentralized communication protocol, with user IDs in the format `@user:server.domain` and room IDs in the format `!room_id:server.domain`
2. **Room Concept**: Matrix does not distinguish between group chats and private chats; all conversations are "rooms." The adapter automatically identifies private chat rooms through DM (Direct Message) account data
3. **Long Polling Synchronization**: Uses the `/sync` API for long polling to fetch new events, rather than WebSocket
4. **MXC URI**: Media files are referenced using the `mxc://server.domain/media_id` format
5. **HTML Rich Text**: Supports sending HTML formatted messages through `formatted_body`
6. **Reaction Emojis**: Supports emoji reactions at the message level (Reaction), distinct from traditional reply messages
7. **Message Editing**: Supports editing previously sent messages via `m.replace` relationship
8. **Message Recall**: Supports recalling/deleting messages via `m.room.redaction`

### Extended Fields

- All unique fields are prefixed with `matrix_`
- Original data is retained in the `matrix_raw` field
- `matrix_raw_type` indicates the original Matrix event type (such as `m.room.message`, `m.room.member`)

### Special Field Examples

```python
# Group message
{
  "type": "message",
  "detail_type": "group",
  "user_id": "@user:matrix.org",
  "group_id": "!room_id:matrix.org",
  "matrix_room_id": "!room_id:matrix.org"
}

# Private chat message
{
  "type": "message",
  "detail_type": "private",
  "user_id": "@user:matrix.org",
  "matrix_room_id": "!dm_room_id:matrix.org"
}

# Reaction emoji
{
  "type": "notice",
  "detail_type": "matrix_reaction",
  "matrix_reaction_event_id": "$reacted_msg_id",
  "matrix_reaction_key": "👍"
}

# Message recall
{
  "type": "notice",
  "detail_type": "matrix_redaction",
  "matrix_redacted_event_id": "$deleted_msg_id"
}

# Message editing
{
  "type": "message",
  "detail_type": "group",
  "matrix_edit": true,
  "matrix_original_event_id": "$original_event_id"
}

# Thread message
{
  "type": "message",
  "detail_type": "group",
  "thread_id": "$thread_root_id"
}
```

### Message Segment Types

Matrix messages are automatically converted to corresponding message segments based on `msgtype`:

| msgtype | Converted Type | Description |
|---|---|---|
| m.text | `text` | Text message |
| m.notice | `text` | Notification message |
| m.emote | `text` | Action message |
| m.image | `image` | Image message |
| m.audio | `voice` | Audio message |
| m.video | `video` | Video message |
| m.file | `file` | File message |
| m.location | `location` | Location message |

Message segment structure example:

```json
// Text message (with HTML)
{
  "type": "text",
  "data": {
    "text": "Plain text content",
    "html": "<b>HTML content</b>"
  }
}

// Image message
{
  "type": "image",
  "data": {
    "url": "mxc://matrix.org/abc123",
    "filename": "photo.png",
    "matrix_mxc": "mxc://matrix.org/abc123",
    "info": {
      "mimetype": "image/png",
      "w": 800,
      "h": 600,
      "size": 123456
    }
  }
}

// Location message
{
  "type": "location",
  "data": {
    "latitude": 0.0,
    "longitude": 0.0,
    "matrix_geo_uri": "geo:39.9,116.4",
    "text": "Beijing, China"
  }
}
```

### Event Mixin Methods

MatrixAdapter registers the following event mixin methods, which can be directly called in event handling:

| Method | Return Type | Description |
|------|----------|------|
| `get_room_id()` | `str` | Get room ID |
| `get_matrix_event_type()` | `str` | Get original Matrix event type |
| `get_matrix_sender()` | `str` | Get original sender ID |
| `get_reaction_key()` | `str` | Get reaction emoji |
| `is_edited()` | `bool` | Determine if the message is an edited message |
| `is_notice()` | `bool` | Determine if the message is of m.notice type |

```python
@message.on_message()
async def handle_message(event):
    if event.get("platform") != "matrix":
        return

    room_id = event.get_room_id()
    event_type = event.get_matrix_event_type()
    sender = event.get_matrix_sender()
    is_edited = event.is_edited()
    is_notice = event.is_notice()
```

## Sync API Connection

### Synchronization Process

1. Authenticate using access_token or user_id + password
2. Call `/_matrix/client/v3/account/whoami` to get bot_user_id
3. Emit connect meta event
4. Perform initial synchronization (`/_matrix/client/v3/sync?timeout=0`) to obtain `next_batch` token
5. Discover DM rooms (`/_matrix/client/v3/user/{user_id}/account_data/m.direct`)
6. Begin Long Polling synchronization loop (`/_matrix/client/v3/sync?since={next_batch}&timeout=30000`)
7. Process new events returned from each synchronization and convert and emit them

### Heartbeat Mechanism

- The adapter emits a `heartbeat` meta event every 30 seconds
- Emits a `connect` meta event upon successful connection
- Emits a `disconnect` meta event upon disconnection

### Room Invitations

- When receiving a room invitation (room with `invite` status), if the `auto_accept_invites` configuration is `true` (default), the adapter will automatically join the room
- Joining the room calls the `/_matrix/client/v3/join/{room_id}` interface

## Usage Examples

### Handling Group Messages

```python
from ErisPulse.Core.Event import message
from ErisPulse import sdk

matrix = sdk.adapter.get("matrix")

@message.on_message()
async def handle_group_msg(event):
    if event.get("platform") != "matrix":
        return
    if event.get("detail_type") != "group":
        return

    text = event.get_text()
    room_id = event.get("group_id")

    if text == "hello":
        await matrix.Send.To("group", room_id).Reply(
            event.get("message_id")
        ).Text("Hello!")
```

### Handling Reaction Emojis

```python
from ErisPulse.Core.Event import notice

@notice.on_notice()
async def handle_reaction(event):
    if event.get("platform") != "matrix":
        return

    if event.get("detail_type") == "matrix_reaction":
        reaction_key = event.get("matrix_reaction_key")
        reacted_event_id = event.get("matrix_reaction_event_id")
        room_id = event.get_room_id()
        # Handle reaction emoji...
```

### Sending Media Messages

```python
# Send image (URL)
await matrix.Send.To("group", room_id).Image("https://example.com/image.png")

# Send image (MXC URI)
await matrix.Send.To("group", room_id).Image("mxc://matrix.org/abc123")

# Send image (binary data)
with open("image.png", "rb") as f:
    image_bytes = f.read()
await matrix.Send.To("group", room_id).Image(image_bytes)

# Send image (local file path)
await matrix.Send.To("group", room_id).Image("/path/to/image.png")

# Send file (with filename)
await matrix.Send.To("group", room_id).File("/path/to/document.pdf", filename="document.pdf")
```

### Handling Message Edits

```python
@message.on_message()
async def handle_edited_message(event):
    if event.get("platform") != "matrix":
        return

    if event.is_edited():
        original_id = event.get("matrix_original_event_id")
        # Handle edited message...
```

### Listening to Member Changes

```python
@notice.on_notice()
async def handle_member_change(event):
    if event.get("platform") != "matrix":
        return

    detail_type = event.get("detail_type")

    if detail_type == "group_member_increase":
        user_id = event.get("user_id")
        nickname = event.get("user_nickname")
        print(f"User {nickname} ({user_id}) joined the room")

    elif detail_type == "group_member_decrease":
        user_id = event.get("user_id")
        operator_id = event.get("operator_id")
        print(f"User {user_id} was removed, operator: {operator_id}")
```