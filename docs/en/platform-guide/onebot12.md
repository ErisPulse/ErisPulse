# OneBot12 Platform Feature Documentation

OneBot12Adapter is an adapter built based on the OneBot V12 protocol, serving as the baseline protocol adapter for the ErisPulse framework.

---

## Document Information

- Corresponding Module Version: 4.0.0
- Maintainer: ErisPulse
- Protocol Version: OneBot V12

## Basic Information

- Platform Overview: OneBot V12 is a general-purpose chatbot application interface standard, serving as the baseline protocol for the ErisPulse framework.
- Adapter Name: OneBot12Adapter
- Supported Protocol/API Version: OneBot V12
- Multi-Account Support: Fully multi-account architecture, supporting the configuration and operation of multiple OneBot12 accounts simultaneously.

## Supported Message Sending Types

All sending methods are implemented using a fluent interface syntax, for example:

```python
from ErisPulse.Core import adapter
onebot12 = adapter.get("onebot12")

# Send using the default account
await onebot12.Send.To("group", group_id).Text("Hello World!")

# Specify a particular account for sending
await onebot12.Send.To("group", group_id).Account("main").Text("Message from main account")
```

### Case-Insensitive Method Calls

All sending methods and fluent modifiers support case-insensitive calls, and the adapter automatically maps them to the correct standard method names:

```python
# All of the following calls are equivalent
await onebot12.Send.To("user", 123).Text("hello")
await onebot12.Send.To("user", 123).text("hello")
await onebot12.Send.To("user", 123).TEXT("hello")

# Fluent modifiers also support case-insensitivity
await onebot12.Send.To("group", 123).At(456).Text("hello")
await onebot12.Send.To("group", 123).at(456).TEXT("hello")
await onebot12.Send.To("group", 123).AT(456).text("hello")
```

### Unsupported Method Calls

When calling an unsupported method, the adapter returns a friendly text message instead of throwing an exception:

```python
# Calling an unsupported method
result = await onebot12.Send.To("user", 123).UnsupportedMethod("test")

# The returned result is the sent text message
# Message content: [Unsupported sending type] Method name: UnsupportedMethod, Parameters: [args[0]: 'test']
```

### Basic Message Types

- `.Text(text: str)` - Send plain text message
- `.Image(file: Union[str, bytes], filename: str = "image.png")` - Send image message (supports URL, Base64, or bytes)
- `.Audio(file: Union[str, bytes], filename: str = "audio.ogg")` - Send audio message
- `.Voice(file: Union[str, bytes], filename: str = "voice.ogg")` - Send voice message (alias of Audio, compatible with OneBot11)
- `.Video(file: Union[str, bytes], filename: str = "video.mp4")` - Send video message

### Fluent Modifier Methods (return self to support fluent chaining)

- `.At(user_id: Union[str, int])` - Mention user (can be called multiple times)
- `.AtAll()` - Mention all group members
- `.Reply(message_id: Union[str, int])` - Reply to a message

### Raw Message Sending

- `.Raw_ob12(message: Union[Dict, List[Dict]], **kwargs)` - Send raw OneBot12 format message (follows naming conventions)

### Other Message Types

- `.Sticker(file_id: str)` - Send sticker/gift
- `.Location(latitude: float, longitude: float, title: str = "", content: str = "")` - Send location

### Management Functions

- `.Recall(message_id: Union[str, int])` - Recall message
- `.Edit(message_id: Union[str, int], content: Union[str, List[Dict]])` - Edit message
- `.Raw(message_segments: List[Dict])` - Send native OneBot12 message segments
- `.Batch(target_ids: List[str], message: Union[str, List[Dict]], target_type: str = "user")` - Batch send messages

## OneBot12 Standard Events

The OneBot12 adapter fully complies with the OneBot12 standard, and event formats do not require conversion, they are directly submitted to the framework.

### New Feature: Raw Event Type Field

In accordance with the `standards/event-conversion.md` specification, all events will retain the raw event type field `onebot12_raw_type`:

```python
{
    "id": "event-id",
    "type": "message",              # Event type
    "onebot12_raw_type": "message", # Raw event type (same as type)
    "detail_type": "private",
    "self": {"user_id": "bot-id"},
    "user_id": "user-id",
    "message": [{"type": "text", "data": {"text": "Hello"}}],
    "alt_message": "Hello",
    "time": 1234567890
}
```

### Message Events

```python
# Private message
{
    "id": "event-id",
    "type": "message",
    "onebot12_raw_type": "message",
    "detail_type": "private",
    "self": {"user_id": "bot-id"},
    "user_id": "user-id",
    "message": [{"type": "text", "data": {"text": "Hello"}}],
    "alt_message": "Hello",
    "time": 1234567890
}

# Group message
{
    "id": "event-id",
    "type": "message",
    "onebot12_raw_type": "message",
    "detail_type": "group",
    "self": {"user_id": "bot-id"},
    "user_id": "user-id",
    "group_id": "group-id",
    "message": [{"type": "text", "data": {"text": "Hello group"}}],
    "alt_message": "Hello group",
    "time": 1234567890
}
```

### Notice Events

```python
# Group member increase
{
    "id": "event-id",
    "type": "notice",
    "onebot12_raw_type": "notice",
    "detail_type": "group_member_increase",
    "self": {"user_id": "bot-id"},
    "group_id": "group-id",
    "user_id": "user-id",
    "operator_id": "operator-id",
    "sub_type": "approve",
    "time": 1234567890
}

# Group member decrease
{
    "id": "event-id",
    "type": "notice",
    "onebot12_raw_type": "notice",
    "detail_type": "group_member_decrease",
    "self": {"user_id": "bot-id"},
    "group_id": "group-id",
    "user_id": "user-id",
    "operator_id": "operator-id",
    "sub_type": "leave",
    "time": 1234567890
}
```

### Request Events

```python
# Friend request
{
    "id": "event-id",
    "type": "request",
    "onebot12_raw_type": "request",
    "detail_type": "friend",
    "self": {"user_id": "bot-id"},
    "user_id": "user-id",
    "comment": "申请消息",
    "flag": "request-flag",
    "time": 1234567890
}

# Group invitation request
{
    "id": "event-id",
    "type": "request",
    "onebot12_raw_type": "request",
    "detail_type": "group",
    "self": {"user_id": "bot-id"},
    "group_id": "group-id",
    "user_id": "user-id",
    "comment": "申请消息",
    "flag": "request-flag",
    "sub_type": "invite",
    "time": 1234567890
}
```

### Meta Events

```python
# Lifecycle event
{
    "id": "event-id",
    "type": "meta_event",
    "onebot12_raw_type": "meta_event",
    "detail_type": "lifecycle",
    "self": {"user_id": "bot-id"},
    "sub_type": "enable",
    "time": 1234567890
}

# Heartbeat event
{
    "id": "event-id",
    "type": "meta_event",
    "onebot12_raw_type": "meta_event",
    "detail_type": "heartbeat",
    "self": {"user_id": "bot-id"},
    "interval": 5000,
    "status": {"online": true},
    "time": 1234567890
}
```

## Configuration Options

### Account Configuration

Each account has the following independent configuration options:

- `mode`: The running mode of the account ("server" or "client")
- `server_path`: The WebSocket path for Server mode
- `server_token`: The authentication token for Server mode (optional)
- `client_url`: The WebSocket address to connect to in Client mode
- `client_token`: The authentication token for Client mode (optional)
- `enabled`: Whether to enable this account
- `platform`: The platform identifier, default is "onebot12"
- `implementation`: The implementation identifier, such as "go-cqhttp" (optional)

### Configuration Example

```toml
[OneBotv12_Adapter.accounts.main]
mode = "server"
server_path = "/onebot12-main"
server_token = "main_token"
enabled = true
platform = "onebot12"
implementation = "go-cqhttp"

[OneBotv12_Adapter.accounts.backup]
mode = "client"
client_url = "ws://127.0.0.1:3002"
client_token = "backup_token"
enabled = true
platform = "onebot12"
implementation = "shinonome"

[OneBotv12_Adapter.accounts.test]
mode = "client"
client_url = "ws://127.0.0.1:3003"
enabled = false
```

### Default Configuration

If no accounts are configured, the adapter will automatically create:

```toml
[OneBotv12_Adapter.accounts.default]
mode = "server"
server_path = "/onebot12"
enabled = true
platform = "onebot12"
```

## Return Values of Send Methods

### Message Sending Methods
All message sending methods (such as `.Text()`, `.Image()`, `.Raw_ob12()` etc.) return an `asyncio.Task` object, which can be awaited directly to obtain the sending result:

```python
task = await onebot12.Send.To("group", 123456).Text("Hello")
```

### Chained Modifier Methods
All chained modifier methods (such as `.At()`, `.AtAll()`, `.Reply()`) return `self`, supporting chained calls:

```python
# Combining multiple modifier methods
await onebot12.Send.To("group", 123456).Reply("msg123").At(789).At(790).Text("Text")
```

## API Response Standard

Adapters follow the ErisPulse standardized response specification (`standards/api-response.md`):

```python
# Success Response
{
    "status": "ok",              # Required: execution status
    "retcode": 0,                # Required: return code (0 indicates success)
    "data": {                     # Required: response data
        "message_id": "123456",
        "time": 1632847927.599013
    },
    "message_id": "123456",       # Required: message ID (empty string if not present)
    "message": "",                # Required: error message (empty if successful)
    "echo": "1234",               # Optional: echo value from the request returned as-is
    "onebot12_raw": {...}        # Optional: raw response data
}

# Failure Response
{
    "status": "failed",           # Required: execution status
    "retcode": 10003,            # Required: return code (non-zero indicates failure)
    "data": None,                # Required: null for failures
    "message_id": "",            # Required: empty string for failures
    "message": "Missing required parameters",    # Required: error description
    "echo": "1234",              # Optional: echo value from the request returned as-is
    "onebot12_raw": {...}        # Optional: raw response data
}
```

### Error Code Specification

Follows OneBot12 standard error codes:

- **0**: Success
- **1xxxx**: Action request error
- **2xxxx**: Action processor error
- **3xxxx**: Action execution error (33001 indicates network timeout)

### Multi-Account Sending Syntax

```python
# Account selection methods
await onebot12.Send.Using("main").To("group", 123456).Text("Main account message")
await onebot12.Send.Using("backup").To("group", 123456).Image("http://example.com/image.jpg")

# API call method
await onebot12.call_api("send_message", account_id="main", 
    detail_type="group", group_id=123456, 
    content=[{"type": "text", "data": {"text": "Hello"}}])
```

## Asynchronous Processing Mechanism

The OneBot12 adapter adopts an asynchronous non-blocking design:

1. Message sending does not block the event handling loop.
2. Multiple concurrent sending operations can be performed simultaneously.
3. API responses can be handled promptly.
4. WebSocket connections remain active.
5. Concurrent processing of multiple accounts, with each account running independently.

## Error Handling

Adapters provide a comprehensive error handling mechanism:

1. Automatic reconnection for network connection exceptions (supports independent reconnection for each account, with a 30-second interval)
2. Handling API call timeouts (fixed 30-second timeout)
3. Automatic retry for failed message sending (up to 3 retries)
4. Calling unsupported methods will return a friendly text prompt

## Event Handling Enhancement

In multi-account mode, all events will automatically have account information added:

```python
{
    "type": "message",
    "onebot12_raw_type": "message",  // Original event type
    "detail_type": "private",
    "self": {"user_id": "123456"},  // The account ID that sent the event (standard field)
    "platform": "onebot12",
    // ... other event fields
}
```

## Management Interface

```python
# Get all account information
accounts = onebot12.accounts

# Check account connection status
connection_status = {
    account_id: connection is not None and not connection.closed
    for account_id, connection in oneobot12.connections.items()
}

# Dynamically enable/disable account (adapter needs to be restarted)
onebot12.accounts["test"].enabled = False
```

## OneBot12 Standard Features

### Message Segment Standard

OneBot12 uses a standardized message segment format:

```python
# Text message segment
{"type": "text", "data": {"text": "Hello"}}

# Image message segment
{"type": "image", "data": {"file_id": "image-id"}}

# Mention message segment
{"type": "mention", "data": {"user_id": "user-id", "user_name": "Username"}}

# Reply message segment
{"type": "reply", "data": {"message_id": "msg-id"}}
```

### API Standard

Follows the OneBot12 standard API specification:

- `send_message`: Send a message
- `delete_message`: Recall a message
- `edit_message`: Edit a message
- `get_message`: Retrieve a message
- `get_self_info`: Get self information
- `get_user_info`: Get user information
- `get_group_info`: Get group information

## Best Practices

1. **Configuration Management**: It is recommended to use multi-account configurations to manage robots with different purposes separately.
2. **Error Handling**: Always check the return status of API calls.
3. **Message Sending**: Use appropriate message types to avoid sending unsupported messages.
4. **Connection Monitoring**: Regularly check the connection status to ensure service availability.
5. **Performance Optimization**: When sending in batches, use the Batch method to reduce network overhead.
6. **Method Calls**: It is recommended to use standard PascalCase naming (e.g., `.Text()`), but lowercase forms are also supported for compatibility with different programming styles (this approach may be incompatible with older versions).