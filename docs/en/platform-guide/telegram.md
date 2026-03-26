# Telegram Platform Features Documentation

TelegramAdapter is an adapter built based on the Telegram Bot API, supporting multiple message types and event handling.

---

## Document Information

- Corresponding Module Version: 3.5.0
- Maintainer: ErisPulse

## Basic Information

- Platform Introduction: Telegram is a cross-platform instant messaging software
- Adapter Name: TelegramAdapter
- Supported Protocols/API Versions: Telegram Bot API

## Supported Message Sending Types

All sending methods are implemented via chained syntax, for example:
```python
from ErisPulse.Core import adapter
telegram = adapter.get("telegram")

await telegram.Send.To("user", user_id).Text("Hello World!")
```

### Basic Sending Methods

- `.Text(text: str)`: Sends a plain text message.
- `.Face(emoji: str)`: Sends an emoji message.
- `.Markdown(text: str, content_type: str = "MarkdownV2")`: Sends a Markdown format message.
- `.HTML(text: str)`: Sends an HTML format message.

### Media Sending Methods

All media methods support two input methods:
- **URL Method**: Pass a string URL directly
- **File Upload**: Pass `bytes` type data

- `.Image(file: bytes | str, caption: str = "", content_type: str = None)`: Sends an image message
- `.Video(file: bytes | str, caption: str = "", content_type: str = None)`: Sends a video message
- `.Voice(file: bytes | str, caption: str = "")`: Sends a voice message
- `.Audio(file: bytes | str, caption: str = "", content_type: str = None)`: Sends an audio message
- `.File(file: bytes | str, caption: str = "")`: Sends a file message
- `.Document(file: bytes | str, caption: str = "", content_type: str = None)`: Sends a document message (Alias of File)

### Message Management Methods

- `.Edit(message_id: int, text: str, content_type: str = None)`: Edits an existing message.
- `.Recall(message_id: int)`: Deletes a specified message.

### Raw Message Sending

- `.Raw_ob12(message: List[Dict])`: Sends a OneBot12 standard format message
  - Supports complex combined messages (text + @user + reply + media)
  - Automatically treats text as the media message's caption
- `.Raw_json(json_str: str)`: Sends a raw JSON format message

### Chained Modifying Methods

- `.At(user_id: str)`: Mentions a specific user (can be called multiple times)
- `.AtAll()`: Mentions all members
- `.Reply(message_id: str)`: Replies to a specified message

### Method Name Mapping

Sending methods support case-insensitive calls and automatically convert to standard method names via a mapping table:
```python
# The following are equivalent
telegram.Send.To("group", 123).Text("hello")
telegram.Send.To("group", 123).text("hello")
telegram.Send.To("group", 123).TEXT("hello")
```

### Sending Examples

```python
# Basic text sending
await telegram.Send.To("group", group_id).Text("Hello World!")

# Media sending (URL Method)
await telegram.Send.To("group", group_id).Image("https://example.com/image.jpg", caption="This is an image")

# Media sending (File Upload)
with open("image.jpg", "rb") as f:
    await telegram.Send.To("group", group_id).Image(f.read())

# @User
await telegram.Send.To("group", group_id).At("6117725680").Text("Hello!")

# Reply to message
await telegram.Send.To("group", group_id).Reply("12345").Text("Reply content")

# Combined usage
await telegram.Send.To("group", group_id).Reply("12345").At("6117725680").Image("https://example.com/image.jpg", caption="Look at this picture")

# OneBot12 combined message
ob12_message = [
    {"type": "text", "data": {"text": "Complex combined message:"}},
    {"type": "mention", "data": {"user_id": "6117725680", "name": "Username"}},
    {"type": "reply", "data": {"message_id": "12345"}},
    {"type": "image", "data": {"file": "https://http.cat/200"}}
]
await telegram.Send.To("group", group_id).Raw_ob12(ob12_message)
```

### Unsupported Method Notifications

When calling unsupported sending methods, a text notification is automatically sent:
```python
# Unsupported sending type
await telegram.Send.To("group", group_id).UnknownMethod("data")
# Will send: [Unsupported sending type] Method name: UnknownMethod, Parameters: [...]
```

## Specific Event Types

Telegram events are converted to the OneBot12 protocol. While standard fields fully comply with the OneBot12 protocol, the following differences exist:

### Core Differences

1. Specific Event Types:
   - Inline Query: `telegram_inline_query`
   - Callback Query: `telegram_callback_query`
   - Poll Event: `telegram_poll`
   - Poll Answer: `telegram_poll_answer`

2. Extended Fields:
   - All specific fields are identified with the `telegram_` prefix
   - Original data is preserved in the `telegram_raw` field
   - Channel messages use `detail_type="channel"`

### Event Listening Methods

The Telegram adapter supports two methods for listening to events:

```python
# Using original event name
@sdk.adapter.Telegram.on("message")
async def handle_message(event):
    pass

# Using mapped event name
@sdk.adapter.Telegram.on("message")
async def handle_message(event):
    pass
```

### Special Field Examples

```python
# Callback Query event
{
  "type": "notice",
  "detail_type": "telegram_callback_query",
  "user_id": "123456",
  "user_nickname": "YingXinche",
  "telegram_callback_data": {
    "id": "cb_123",
    "data": "callback_data",
    "message_id": "msg_456"
  }
}

# Inline Query event
{
  "type": "notice",
  "detail_type": "telegram_inline_query",
  "user_id": "789012",
  "user_nickname": "YingXinche",
  "telegram_inline_query": {
    "id": "iq_789",
    "query": "search_text",
    "offset": "0"
  }
}

# Channel message
{
  "type": "message",
  "detail_type": "channel",
  "message_id": "msg_345",
  "channel_id": "channel_123",
  "telegram_chat": {
    "title": "News Channel",
    "username": "news_official"
  }
}
```

## Extended Field Descriptions

- All specific fields are identified with the `telegram_` prefix
- Original data is preserved in the `telegram_raw` field
- Channel messages use `detail_type="channel"`
- Entities within message content (e.g., bold, links) are converted into corresponding message segments
- Reply messages will have a message segment of type `telegram_reply` added

## Configuration Options

The Telegram adapter supports the following configuration options:

### Basic Configuration
- `token`: Telegram Bot Token
- `proxy_enabled`: Whether to enable proxy

### Proxy Configuration
- `proxy.host`: Proxy server address
- `proxy.port`: Proxy port
- `proxy.type`: Proxy type ("socks4" or "socks5")

### Operating Mode

The Telegram adapter only supports **Polling** mode. The Webhook mode has been removed.

Configuration Example:
```toml
[Telegram_Adapter]
token = "YOUR_BOT_TOKEN"
proxy_enabled = false

[Telegram_Adapter.proxy]
host = "127.0.0.1"
port = 1080
type = "socks5"