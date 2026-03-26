# OneBot11 Platform Features Documentation

OneBot11Adapter is an adapter built based on the OneBot V11 protocol.

---

## Documentation Information

- Corresponding Module Version: 3.6.0
- Maintainer: ErisPulse

## Basic Information

- Platform Introduction: OneBot is a chatbot application interface standard
- Adapter Name: OneBotAdapter
- Supported Protocol/API Version: OneBot V11
- Multi-account Support: Default multi-account architecture, supports configuring and running multiple OneBot accounts simultaneously
- Legacy Configuration Compatibility: Compatible with old version configuration formats, provides migration reminders (non-automatic migration)

## Supported Message Sending Types

All sending methods are implemented via chaining syntax, for example:
```python
from ErisPulse.Core import adapter
onebot = adapter.get("onebot11")

# Send using default account
await onebot.Send.To("group", group_id).Text("Hello World!")

# Send using specific account
await onebot.Send.Using("main").To("group", group_id).Text("Message from main account")

# Chain modifiers: @ user + reply
await onebot.Send.To("group", group_id).At(123456).Reply(msg_id).Text("Reply message")

# @ all members
await onebot.Send.To("group", group_id).AtAll().Text("Announcement message")
```

### Basic Sending Methods

- `.Text(text: str)`: Send plain text message.
- `.Image(file: Union[str, bytes], filename: str = "image.png")`: Send image (supports URL, Base64, or bytes).
- `.Voice(file: Union[str, bytes], filename: str = "voice.amr")`: Send voice message.
- `.Video(file: Union[str, bytes], filename: str = "video.mp4")`: Send video message.
- `.Face(id: Union[str, int])`: Send QQ emoticon.
- `.File(file: Union[str, bytes], filename: str = "file.dat")`: Send file (auto-detect type).
- `.Raw_ob12(message: List[Dict], **kwargs)`: Send OneBot12 format message (auto-converted to OB11).
- `.Recall(message_id: Union[str, int])`: Recall message.

### Chained Modifier Methods (Combinable)

Chained modifier methods return `self`, support chaining, and must be called before the final sending method:

- `.At(user_id: Union[str, int], name: str = None)`: @ specific user (can be called multiple times).
- `.AtAll()`: @ all members.
- `.Reply(message_id: Union[str, int])`: Reply to specific message.

### Chained Call Examples

```python
# Basic send
await onebot.Send.To("group", 123456).Text("Hello")

# @ single user
await onebot.Send.To("group", 123456).At(789012).Text("Hello")

# @ multiple users
await onebot.Send.To("group", 123456).At(111).At(222).At(333).Text("Hello everyone")

# Send OneBot12 format message
ob12_msg = [{"type": "text", "data": {"text": "Hello"}}]
await onebot.Send.To("group", 123456).Raw_ob12(ob12_msg)
```

### Unsupported Type Handling

If an undefined sending method is called, the adapter returns a text prompt:
```python
# Call non-existent method
await onebot.Send.To("group", 123456).SomeUnsupportedMethod(arg1, arg2)
# Actual send: "[Unsupported send type] Method Name: SomeUnsupportedMethod, Arguments: [...]"
```

## Specific Event Types

OneBot11 events are converted to the OneBot12 protocol, where standard fields fully comply with the OneBot12 protocol, but there are the following differences:

### Core Differences

1.  **Specific Event Types:**
    -   CQ Code Extension Event: `onebot11_cq_{type}`
    -   Honor Change Event: `onebot11_honor`
    -   Poke Event: `onebot11_poke`
    -   Group Red Packet Lucky King Event: `onebot11_lucky_king`

2.  **Extension Fields:**
    -   All specific fields are identified with the `onebot11_` prefix
    -   Original CQ code message retained in the `onebot11_raw_message` field
    -   Original event data retained in the `onebot11_raw` field

### Special Field Examples

```python
// Honor change event
{
  "type": "notice",
  "detail_type": "onebot11_honor",
  "group_id": "123456",
  "user_id": "789012",
  "onebot11_honor_type": "talkative",
  "onebot11_operation": "set"
}

// Poke event
{
  "type": "notice",
  "detail_type": "onebot11_poke",
  "group_id": "123456",
  "user_id": "789012",
  "target_id": "345678",
  "onebot11_poke_type": "normal"
}

// Group red packet lucky king event
{
  "type": "notice",
  "detail_type": "onebot11_lucky_king",
  "group_id": "123456",
  "user_id": "789012",
  "target_id": "345678"
}

// CQ code message segment
{
  "type": "message",
  "message": [
    {
      "type": "onebot11_face",
      "data": {"id": "123"}
    },
    {
      "type": "onebot11_shake",
      "data": {} 
    }
  ]
}
```

### Extension Field Descriptions

-   All specific fields are identified with the `onebot11_` prefix
-   Original CQ code message retained in the `onebot11_raw_message` field
-   Original event data retained in the `onebot11_raw` field
-   CQ codes within message content are converted to corresponding message segments
-   Reply messages will add `reply` type message segments
-   @ messages will add `mention` type message segments

## Configuration Options

Each account in the OneBot adapter is configured with the following options independently:

### Account Configuration
- `mode`: Running mode of this account ("server" or "client")
- `server_path`: WebSocket path in Server mode
- `server_token`: Authentication Token in Server mode (optional)
- `client_url`: WebSocket address to connect to in Client mode
- `client_token`: Authentication Token in Client mode (optional)
- `enabled`: Whether this account is enabled

### Built-in Defaults
- Reconnect Interval: 30 seconds
- API Call Timeout: 30 seconds
- Maximum Retry Count: 3 times

### Configuration Example
```toml
[OneBotv11_Adapter.accounts.main]
mode = "server"
server_path = "/onebot-main"
server_token = "main_token"
enabled = true

[OneBotv11_Adapter.accounts.backup]
mode = "client"
client_url = "ws://127.0.0.1:3002"
client_token = "backup_token"
enabled = true

[OneBotv11_Adapter.accounts.test]
mode = "client"
client_url = "ws://127.0.0.1:3003"
enabled = false
```

### Default Configuration

If no account is configured, the adapter will automatically create:
```toml
[OneBotv11_Adapter.accounts.default]
mode = "server"
server_path = "/"
enabled = true
```

## Sending Method Return Values

All sending methods return a Task object, which can be directly awaited to get the send result. The returned result follows the ErisPulse adapter standardized return specification:

```python
{
    "status": "ok",           // Execution status
    "retcode": 0,             // Return code
    "data": {...},            // Response data
    "self": {...},            // Self information
    "message_id": "123456",   // Message ID
    "message": "",            // Error message
    "onebot_raw": {...}       // Raw response data
}
```

### Multi-account Sending Syntax

```python
# Account selection method
await onebot.Send.Using("main").To("group", 123456).Text("Main account message")
await onebot.Send.Using("backup").To("group", 123456).Image("http://example.com/image.jpg")

# API call method
await onebot.call_api("send_msg", account_id="main", group_id=123456, message="Hello")
```

## Async Processing Mechanism

The OneBot adapter adopts an asynchronous non-blocking design, ensuring:
1.  Message sending does not block the event processing loop
2.  Multiple concurrent send operations can proceed simultaneously
3.  API responses are handled in a timely manner
4.  WebSocket connections remain active
5.  Multi-account concurrent processing, with each account running independently

## Error Handling

The adapter provides comprehensive error handling mechanisms:
1.  Automatic reconnection for network connection exceptions (supports independent reconnection for each account, interval of 30 seconds)
2.  API call timeout handling (fixed 30-second timeout)
3.  Message send failure retry (up to 3 retries)

## Event Processing Enhancement

In multi-account mode, account information is automatically added to all events:
```python
{
    "type": "message",
    "detail_type": "private",
    "self": {"user_id": "main"},  // New: Account ID that sent the event (standard field)
    "platform": "onebot11",
    // ... other event fields
}
```

## Management Interface

```python
# Get all account information
accounts = onebot.accounts

# Check account connection status
connection_status = {
    account_id: connection is not None and not connection.closed
    for account_id, connection in onebot.connections.items()
}

# Dynamically enable/disable accounts (requires restarting adapter)
onebot.accounts["test"].enabled = False