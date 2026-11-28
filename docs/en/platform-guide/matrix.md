# Matrix Platform Features Documentation

MatrixAdapter is an adapter built on the [Matrix protocol](https://spec.matrix.org/), integrating all core functional modules of the Matrix protocol and providing unified event handling and message operation interfaces.

---

## Document Information

- Module version: 4.6.1
- Maintainer: ErisPulse
- Last updated: 2026-11-10

## Basic Information

- Platform introduction: Matrix is an open decentralized communication protocol, supporting various scenarios such as private chats and groups
- Adapter name: MatrixAdapter
- Multi-account support: Supports configuring multiple Matrix accounts simultaneously
- Connection method: Long Polling (via the Matrix Sync API `/sync`)
- Authentication: Obtain the token via access_token or user_id + password login
- Chained modifier support: Supports chained modifier methods such as `.Reply()`, `.At()`, `.AtAll()`
- OneBot12 compatibility: Supports sending OneBot12 format messages

## Configuration

MatrixAdapter supports multi-account configuration, with homeserver and authentication information configured independently for each account.

```toml
# config.toml
# Account 1
[Matrix_Adapter.accounts.default]
homeserver = "https://matrix.org"          # Matrix server address (required)
access_token = "YOUR_ACCESS_TOKEN"          # Access token (choose either this or user_id+password)
user_id = ""                                # Matrix user ID (e.g., @bot:matrix.org)
password = ""                               # Matrix user password
auto_accept_invites = true                  # Whether to auto-accept room invitations (optional, defaults to true)
enabled = true                              # Whether to enable (optional, defaults to true)

# Account 2
[Matrix_Adapter.accounts.bot2]
homeserver = "https://matrix.example.com"
access_token = "ANOTHER_TOKEN"
enabled = true
```

> Legacy configuration compatibility: If an old single-account `[Matrix_Adapter]` configuration (containing access_token) is detected, it will be automatically migrated to `accounts.default`.

**Configuration options (per account):**
- `homeserver`: Matrix server address (required), defaults to `https://matrix.org`
- `access_token`: Access token, obtainable from a Matrix client. If you already have a token, just fill it in directly
- `user_id`: Matrix user ID (e.g., `@bot:matrix.org`), used together with `password` for login
- `password`: Matrix user password, used for automatic login to obtain the access_token
- `auto_accept_invites`: Whether to automatically accept room invitations, defaults to `true`
- `enabled`: Whether to enable this account (optional, defaults to true)
- `encryption_enabled`: Whether to enable end-to-end encryption, defaults to `false`
- `trust_all_devices`: Whether to automatically trust unverified devices (E2EE), defaults to `true`
- `device_id`: Device ID (E2EE, usually obtained automatically; no need to fill in)
- `store_path`: Encrypted session storage directory (E2EE), defaults to `data/matrix/<account name>`

**Authentication methods:**
- Method 1 (recommended): Provide `access_token` directly
- Method 2: Provide `user_id` and `password`; the adapter will automatically call the login API to obtain the token

## v5 Paradigm Update (4.2.0)

- **BaseConverter inheritance**: Common converter fields are built by the framework's build_base_event
- **Api DSL**: get_self_info/get_user_info/get_group_info/get_group_list/get_group_member_list/leave_group/delete_message(redact) + meta actions
- **Message events supplemented with message_id** (event_id); the message registry supports delete_message
- **spawn_background task ownership**: Sync/heartbeat tasks now use runtime.spawn_background
- **Framework soft dependency**: Runtime detection of ErisPulse>=2.7.1 with a prompt; version logs output at startup
- Matrix has no native button capability; standard keyboard segments are gracefully ignored (no error is raised)

## End-to-End Encryption (4.3.0)

Starting from 4.3.0, the adapter natively supports end-to-end encryption for encrypted rooms (based on matrix-nio[e2e] / vodozemac):

```toml
[Matrix_Adapter.accounts.default]
user_id = "@bot:matrix.org"
password = "YOUR_PASSWORD"
encryption_enabled = true       # Enable (defaults to false; existing deployments are unaffected)
trust_all_devices = true        # Auto-trust unverified devices (default; false for strict mode)
```

- Messages in encrypted rooms are automatically decrypted/encrypted when sent or received; media is end-to-end encrypted (`m.file.encrypted`)
- `device_id` is resolved and persisted automatically; sessions are stored in `store_path` (defaults to `data/matrix/<account name>`, **do not delete**, otherwise historical messages cannot be decrypted)
- The Event Mixin adds `event.is_encrypted()`; media segments carry `matrix_encrypted_file` (JWK), which can be decrypted using `MatrixAdapter.decrypt_media()`
- Cross-signing and server-side key backup are not supported; requires Python >= 3.10
- Automatically degrades to plaintext mode when E2EE is not enabled or matrix-nio is not installed

For details, see the [End-to-End Encryption (E2EE)](#end-to-end-encryption-e2ee) section below and the [Adapter README](https://github.com/ErisPulse/ErisPulse-MatrixAdapter).

## Standardization Alignment

This section describes the adapter's behavior aligned with the ErisPulse standardization specification. For details of the specifications, see the SDK documentation "API Response Specification" (`docs/en/standards/api-response.md`) and "Send Method Specification" (`docs/en/standards/send-method-spec.md`).

### Multi-Account Handling (since 4.6.1)

- All events are injected with `self.account_id` (source account name); accounts logged in via access_token can correctly complete multi-account handling and event routing even when `user_id` is empty

### Error Code Normalization (4.6.x)

- **Media upload/download failures and request timeouts unified to 33001** (network error)
- **Platform API failures unified to 34100** (platform error); the Matrix errcode is preserved in the `message` and `matrix_raw` fields
- **Missing redaction context 10003**: `delete_message` returns a parameter error when the message's owning context cannot be found

| retcode | Description |
|---------|------|
| 0 | Success |
| 10002 | Unsupported action (e.g., get_friend_list; Matrix has no friend concept) |
| 10003 | Invalid send target (cannot be resolved to a Matrix room); missing redaction context |
| 33001 | Network error (media upload/download failure, request timeout) |
| 34100 | Platform API failure (Matrix errcode preserved in message and matrix_raw) |

### Send Specification

- All Send methods read `send_context`: within an event chain, the current event's source account is used automatically; an account explicitly specified via `Using()` takes priority
- HTML method: `.Html(html, fallback)` sends rich text messages; `HTML` is the canonical spelling alias (`Html` is retained for compatibility with existing modules)
- `get_group_list` returns each item with the `group_name` field filled in (consistent with `get_group_info`)

### Standard Api Action Example

```python
from ErisPulse import sdk
matrix = sdk.adapter.get("matrix")
result = await matrix.Api.get_self_info()            # /account/whoami
result = await matrix.Api.get_group_info(room_id)    # m.room.name
result = await matrix.Api.get_group_list()           # /joined_rooms (each item includes group_name)
await matrix.Api.delete_message(event_id)            # redact (registry fills in room_id)
```

---

### Integrated Platform Capabilities

- **Events**: messages (m.room.message: text/image/file/audio-video/reply/edit), member join/leave (m.room.member), room name changes and other state events
- **Conversations**: private chats (automatic DM room discovery) / groups (rooms); sending supports Text/Image/File/Voice/Video/Markdown/Raw_ob12
- **API**: whoami/profile/joined_rooms/room state/member list/leave/redact (see the Api DSL above)

---

## Supported Message Send Types

All send methods are implemented via chained syntax, for example:
```python
from ErisPulse.Core import adapter
matrix = adapter.get("matrix")

await matrix.Send.To("group", room_id).Text("Hello World!")
```

Supported send types include:
- `.Text(text: str)`: Sends a plain text message.
- `.Image(file: bytes | str)`: Sends an image message; supports file paths, URLs, MXC URIs, and binary data.
- `.Voice(file: bytes | str)`: Sends a voice message; supports file paths, URLs, MXC URIs, and binary data.
- `.Video(file: bytes | str)`: Sends a video message; supports file paths, URLs, MXC URIs, and binary data.
- `.File(file: bytes | str, filename: str = "")`: Sends a file message; supports file paths, URLs, MXC URIs, and binary data.
- `.Notice(text: str)`: Sends a notice message (Matrix's m.notice type).
- `.Html(html: str, fallback: str = "")`: Sends an HTML format message; supports rich text content (`HTML` is the canonical spelling alias).
- `.MergeForward(nodes, title="Merged Chat Records")`: Sends a merged-forward message (in the form of a formatted_body blockquote; the whitelist strips details/inline styles).
- `.Raw_ob12(message: List[Dict], **kwargs)`: Sends OneBot12 format messages.

### Chained Modifier Methods (Combinable)

Chained modifier methods return `self` and support chained calls; they must be called before the final send method:

- `.Reply(message_id: str)`: Replies to the specified message (via the Matrix `m.in_reply_to` relation).
- `.At(user_id: str)`: Mentions the specified user (implemented via the Matrix `m.mentions` field).
- `.AtAll()`: Mentions everyone in the room (implemented via the Matrix `@room` mention).

### Chained Call Examples

```python
# Basic send (the "user" target supports a user ID (@user:server, automatically looking up the DM room) or a room ID (!room:server))
await matrix.Send.To("user", "@alice:matrix.org").Text("Hello")

# Reply to a message
await matrix.Send.To("group", room_id).Reply("$event_id").Text("Reply message")

# Mention a user
await matrix.Send.To("group", room_id).At("@user:matrix.org").Text("Hello")

# Mention everyone
await matrix.Send.To("group", room_id).AtAll().Text("Announcement")

# Combined usage: reply + mention
await matrix.Send.To("group", room_id).Reply("$event_id").At("@user:matrix.org").Text("Composite message")

# Send an HTML message
await matrix.Send.To("group", room_id).Html("<h1>Title</h1><p>Content</p>", fallback="Title\nContent")

# Send a notice message
await matrix.Send.To("group", room_id).Notice("System notice")
```

### OneBot12 Message Support

The adapter supports sending OneBot12 format messages, facilitating cross-platform message compatibility:

```python
# Send a OneBot12 format message
ob12_msg = [{"type": "text", "data": {"text": "Hello"}}]
await matrix.Send.To("user", dm_room_id).Raw_ob12(ob12_msg)

# Combined with chained modifiers
ob12_msg = [{"type": "text", "data": {"text": "Reply message"}}]
await matrix.Send.To("group", room_id).Reply("$event_id").Raw_ob12(ob12_msg)

# Complex message
ob12_msg = [
    {"type": "text", "data": {"text": "Check out this image:"}},
    {"type": "image", "data": {"file": "https://example.com/image.png"}},
    {"type": "text", "data": {"text": "Not bad, right?"}}
]
await matrix.Send.To("group", room_id).Raw_ob12(ob12_msg)

# Location message (standard location segment → Matrix m.location; split into separate events when coexisting with text)
ob12_msg = [
    {"type": "text", "data": {"text": "I'm here"}},
    {"type": "location", "data": {"latitude": 39.9, "longitude": 116.4, "title": "Beijing"}}
]
await matrix.Send.To("group", room_id).Raw_ob12(ob12_msg)
```

## Send Method Return Values

All send methods return a Task object, which can be awaited directly to obtain the send result. The returned result follows the ErisPulse adapter standardized return specification:

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

For the error code specification, see the [Standardization Alignment](#standardization-alignment) section above.

## Platform-Specific Event Types

A `platform=="matrix"` check is required before using this platform's features

### Core Differences

1. **Decentralized architecture**: Matrix is a decentralized communication protocol; user IDs are in the format `@user:server.domain`, and room IDs are in the format `!room_id:server.domain`
2. **Room concept**: Matrix does not distinguish between group chats and private chats; all conversations are "rooms". The adapter automatically identifies private chat rooms via DM (Direct Message) account data
3. **Long Polling sync**: Uses the `/sync` API for long polling to fetch new events, rather than WebSocket
4. **MXC URI**: Media files are referenced in the format `mxc://server.domain/media_id`
5. **HTML rich text**: Supports sending HTML format messages via `formatted_body`
6. **Emoji reactions**: Supports message-level emoji reactions (Reaction), distinct from traditional reply messages
7. **Message editing**: Supports editing sent messages via the `m.replace` relation
8. **Message redaction**: Supports redacting/deleting messages via `m.room.redaction`

### Extended Fields

- All platform-specific fields are identified with the `matrix_` prefix
- Raw data is preserved in the `matrix_raw` field
- `matrix_raw_type` identifies the original Matrix event type (e.g., `m.room.message`, `m.room.member`)

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

# Emoji reaction
{
  "type": "notice",
  "detail_type": "matrix_reaction",
  "matrix_reaction_event_id": "$reacted_msg_id",
  "matrix_reaction_key": "👍"
}

# Message redaction
{
  "type": "notice",
  "detail_type": "matrix_redaction",
  "matrix_redacted_event_id": "$deleted_msg_id"
}

# Message edit
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

Matrix messages are automatically converted to the corresponding message segments based on `msgtype`:

| msgtype | Converted Type | Description |
|---|---|---|
| m.text | `text` | Text message |
| m.notice | `text` | Notice message |
| m.emote | `text` | Action message |
| m.image | `image` | Image message |
| m.audio | `audio` | Audio message (the standard message segment name is `audio`; `voice` is the send method name, not a segment name) |
| m.video | `video` | Video message |
| m.file | `file` | File message |
| m.location | `location` | Location message (latitude/longitude parsed from the geo URI) |

> Mention: `m.mentions` in the message content (Matrix v1.11+ specification) is converted to the standard `mention` segment—
> `m.mentions.user_ids` → `mention(user_id=...)`, `m.mentions.room` → `mention(user_id="all")`.

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

// Location message (latitude/longitude parsed from the geo URI)
{
  "type": "location",
  "data": {
    "latitude": 39.9,
    "longitude": 116.4,
    "matrix_geo_uri": "geo:39.9,116.4",
    "text": "Beijing"
  }
}
```

### Event Mixin Methods

MatrixAdapter registers the following event mixin methods, which can be called directly in event handling:

| Method | Return Type | Description |
|------|----------|------|
| `get_room_id()` | `str` | Get the room ID |
| `get_matrix_event_type()` | `str` | Get the original Matrix event type |
| `get_matrix_sender()` | `str` | Get the original sender ID |
| `get_reaction_key()` | `str` | Get the reaction emoji |
| `is_edited()` | `bool` | Determine whether the message is an edit |
| `is_notice()` | `bool` | Determine whether the message is of the m.notice type |

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

### Sync Flow

1. Authenticate using access_token or user_id + password
2. Call `/_matrix/client/v3/account/whoami` to obtain bot_user_id
3. Emit the connect meta event
4. Perform the initial sync (`/_matrix/client/v3/sync?timeout=0`) to obtain the `next_batch` token
5. Discover DM rooms (`/_matrix/client/v3/user/{user_id}/account_data/m.direct`)
6. Start the Long Polling sync loop (`/_matrix/client/v3/sync?since={next_batch}&timeout=30000`)
7. Process the new events returned by each sync, convert them, and emit them

### Heartbeat Mechanism

- The adapter emits a `heartbeat` meta event every 30 seconds
- Emits a `connect` meta event upon successful connection
- Emits a `disconnect` meta event upon shutdown

### Room Invitations

- When a room invitation (a room in the `invite` state) is received, if `auto_accept_invites` is configured as `true` (default), the adapter will automatically join the room
- Joining a room calls the `/_matrix/client/v3/join/{room_id}` API

## End-to-End Encryption (E2EE)

Since 4.3.0, the adapter natively supports end-to-end encryption for encrypted rooms (based on matrix-nio[e2e] / vodozemac), enabled with `encryption_enabled = true`.

### How It Works

- **Sync**: When enabled, sync runs through the nio E2EE session; device key upload, one-time key replenishment, and to-device messages (Olm/Megolm session key distribution) are all handled automatically; `m.room.encrypted` events in the timeline are automatically decrypted into plaintext events before unified conversion
- **Sending**: When the target room is an encrypted room, the Megolm session is shared automatically and the payload is encrypted; events that fail to decrypt are skipped and a warning is logged
- **Media**: Media uploads in encrypted rooms are end-to-end encrypted (`m.file.encrypted`); received media segments carry `matrix_encrypted_file` (JWK, containing url/key/iv/hashes); after downloading the ciphertext, it can be decrypted via `MatrixAdapter.decrypt_media(ciphertext, key, iv, sha256)`
- **Device**: `device_id` is resolved automatically (login response → `/whoami` → local persistence); re-login with the password reuses the same device; `trust_all_devices = true` (default) automatically trusts unverified devices (common practice for bots), `false` is strict mode
- **Fallback**: When E2EE is not enabled or matrix-nio is not installed, it automatically falls back to the plaintext REST path, with behavior identical to previous versions

### Module-Side Interfaces

- Event Mixin: `event.is_encrypted()` determines whether the message comes from an encrypted room
- Media segment markers: `encrypted: true` and `matrix_encrypted_file` (JWK)
- Decryption helper: `MatrixAdapter.decrypt_media(file_bytes, key, iv, hash_value) -> bytes`

### Known Limitations

- Cross-signing and server-side key backup (room key backup) are not supported
- Once the local session storage directory (`store_path`, defaults to `data/matrix/<account name>`) is deleted, historical messages cannot be decrypted
- Interactive SAS (emoji) verification is not yet supported; planned for a future version

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

### Handling Emoji Reactions

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
        # Handle the emoji reaction...
```

### Sending Media Messages

```python
# Send an image (URL)
await matrix.Send.To("group", room_id).Image("https://example.com/image.png")

# Send an image (MXC URI)
await matrix.Send.To("group", room_id).Image("mxc://matrix.org/abc123")

# Send an image (binary data)
with open("image.png", "rb") as f:
    image_bytes = f.read()
await matrix.Send.To("group", room_id).Image(image_bytes)

# Send an image (local file path)
await matrix.Send.To("group", room_id).Image("/path/to/image.png")

# Send a file (with filename)
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
        # Handle the edited message...
```

### Listening for Member Changes

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