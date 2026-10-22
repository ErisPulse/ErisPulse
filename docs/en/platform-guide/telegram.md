# Telegram Platform Feature Documentation

TelegramAdapter is an adapter built on top of the Telegram Bot API, supporting multiple message types and event handling.

---

## Document Information

- Corresponding Module Version: 4.3.0
- Maintainer: ErisPulse

## Basic Information

- Platform Overview: Telegram is a cross-platform instant messaging application
- Adapter Name: TelegramAdapter
- Supported Protocol/API Version: Telegram Bot API
- Session Type Mapping: `private` → use `user` when sending, `group`/`supergroup` → `group`, `channel` → `channel`

## Standard API Actions (API DSL)

The adapter maps OB12 standard actions to the Telegram Bot API and standardizes the data field:

| OB12 Standard Action | Telegram API | Data Field |
|----------------------|--------------|------------|
| get_self_info | getMe | user_id / user_name / user_displayname |
| get_user_info(user_id) | getChat | user_id / user_name / user_displayname |
| get_group_info(group_id) | getChat | group_id / group_name |
| get_group_member_info(group_id, user_id) | getChatMember | user_id / user_name / telegram_role |
| delete_message(message_id) | deleteMessage | chat_id automatically completed via message registry |
| leave_group(group_id) | leaveChat | - |

Extended actions: get_group_admin_list(group_id) (admin list), get_chat_member_count(chat_id) (member count).

```python
from ErisPulse import sdk
telegram = sdk.adapter.get("telegram")

result = await telegram.Api.get_self_info()
result = await telegram.Api.get_group_info(group_id=-100123)
result = await telegram.Api.get_group_admin_list(-100123)
await telegram.Api.delete_message(message_id=55)   # chat_id automatically completed
result = await telegram.Api.Using("main").get_self_info()
```

> Telegram Bot API does not provide an interface to retrieve friend or group lists; get_friend_list/get_group_list returns code=10002.

---

## Request Operations (Request DSL)

Handles group join requests (chat_join_request event), based on approveChatJoinRequest / declineChatJoinRequest:

```python
from ErisPulse.Core.Event import request

@request.on_request()
async def handle_join_request(event):
    if event.get("platform") != "telegram":
        return
    # event["request_id"] is a synthesized identifier (tjr_{chat_id}_{user_id}_{date})
    if event.get("user_nickname"):
        await event.approve()          # Approve
    # await event.reject()             # Reject

# Manual invocation (must have received corresponding request event to register context)
await telegram.Request(event["request_id"]).accept()
await telegram.Request(event["request_id"]).reject()
await telegram.Request(event["request_id"]).Using("main").accept()
```

---

## Supported Message Sending Types

All sending methods use a fluent interface, for example:
```python
from ErisPulse.Core import adapter
telegram = adapter.get("telegram")

await telegram.Send.To("user", user_id).Text("Hello World!")
```

### Basic Sending Methods

| Method | Description | Parameters |
|--------|-------------|------------|
| `.Text(text)` | Send plain text message | `text: str` |
| `.Face(emoji)` | Send emoji dice | `emoji: str` (e.g. 🎲 🎯 🏀) |
| `.Markdown(text, content_type)` | Send Markdown formatted message | `content_type` defaults to `"MarkdownV2"` |
| `.HTML(text)` | Send HTML formatted message | `text: str` |
| `.MergeForward(nodes, title)` | Send merged forward message (title + each blockquote block, truncated at 4096) | `nodes: List[Dict]`, `title: str` |
| `.Sticker(file)` | Send sticker | `file: str (file_id/URL) \| bytes` |
| `.Location(lat, lng)` | Send location | `latitude: float, longitude: float` |
| `.Venue(lat, lng, title, addr)` | Send venue | Includes title and address |
| `.Contact(phone, first, last)` | Send contact | Includes phone number and name |

### Media Sending Methods

All media methods support both `bytes` (upload) and `str` (file_id / URL) inputs:

| Method | Description |
|--------|-------------|
| `.Image(file, caption, content_type)` | Send image |
| `.Video(file, caption, content_type)` | Send video |
| `.Voice(file, caption)` | Send voice |
| `.Audio(file, caption, content_type)` | Send audio |
| `.File(file, caption)` | Send file |
| `.Document(file, caption, content_type)` | Alias for File |

### Message Management Methods

| Method | Description |
|--------|-------------|
| `.Edit(message_id, text, content_type)` | Edit existing message |
| `.Recall(message_id)` | Delete specified message |
| `.Forward(from_chat_id, message_id)` | Forward message (retaining source) |
| `.CopyMessage(from_chat_id, message_id)` | Copy message (without source) |
| `.AnswerCallback(callback_query_id, text, show_alert)` | Respond to callback query |

### Raw Message Sending

- `.Raw_ob12(message: List[Dict])`: Send OneBot12 standard format message
- `.Raw_json(json_str: str)`: Send raw JSON format message

### Fluent Modifier Methods

| Method | Description |
|--------|-------------|
| `.At(user_id)` | @ specified user (implemented via Telegram entities, can be called multiple times) |
| `.AtAll()` | @ all members (send `@All` text) |
| `.Reply(message_id)` | Reply to specified message |
| `.Keyboard(inline_keyboard)` | Set inline keyboard (`list[list[dict]]`) |
| `.ProtectContent(protect)` | Protect content (prevent forwarding and saving) |
| `.Silent(silent)` | Silent send (no notification to user) |

### Sending Examples

```python
# Basic text sending
await telegram.Send.To("user", user_id).Text("Hello World!")

# Message with inline keyboard
from ErisPulse import sdk
telegram = sdk.adapter.get("telegram")
keyboard = [
    [{"text": "Button 1", "callback_data": "btn1"}, {"text": "Button 2", "callback_data": "btn2"}],
    [{"text": "Visit Website", "url": "https://example.com"}],
]
await telegram.Send.To("group", group_id).Keyboard(keyboard).Text("Please select:")

# Media sending (URL method)
await telegram.Send.To("group", group_id).Image("https://example.com/image.jpg", caption="Image")

# @ user
await telegram.Send.To("group", group_id).At("6117725680").Text("Hello!")

# Reply + protect content
await telegram.Send.To("group", group_id).Reply("12345").ProtectContent().Text("Confidential message")

# Silent send
await telegram.Send.To("group", group_id).Silent().Text("Silent notification")

# Respond to callback query
await telegram.Send.AnswerCallback(callback_query_id, text="Processed", show_alert=False)

# OneBot12 composite message
ob12_message = [
    {"type": "text", "data": {"text": "Complex message: "}},
    {"type": "mention", "data": {"user_id": "6117725680", "user_name": "Username"}},
    {"type": "reply", "data": {"message_id": "12345"}},
    {"type": "image", "data": {"file": "https://http.cat/200"}}
]
await telegram.Send.To("group", group_id).Raw_ob12(ob12_message)

# Send sticker
await telegram.Send.To("user", user_id).Sticker("CAACAgIAAxkBAA...")  # file_id

# Send location
await telegram.Send.To("user", user_id).Location(39.9042, 116.4074)
```

## Platform-Specific Event Types

Telegram events are converted following the OneBot12 standard, with platform extensions provided via the `telegram_` prefix.

### Message Event detail_type Mapping

| Telegram chat.type | OneBot12 detail_type | Sending Target Type |
|---|---|---|
| `private` | `private` | `user` |
| `group` | `group` | `group` |
| `supergroup` | `group` | `group` |
| `channel` | `channel` | `channel` |

### Platform-Specific Event Types

| detail_type | Description |
|---|---|
| `telegram_callback_query` | Callback query (inline keyboard button click) |
| `telegram_inline_query` | Inline query |
| `telegram_chosen_inline_result` | Chosen inline result |
| `telegram_poll` | Poll event |
| `telegram_poll_answer` | Poll answer |
| `telegram_my_chat_member` | Bot member status change |
| `telegram_chat_member` | Chat member change |
| `telegram_chat_join_request` | Join chat request |
| `telegram_shipping_query` | Shipping query |
| `telegram_pre_checkout_query` | Pre-checkout query |

### Standard Message Segment Types

Converted message segments use OneBot12 standard format:

| Message Segment Type | Description | Data Field |
|---|---|---|
| `text` | Plain text (without @username) | `text` |
| `mention` | @ user (standard OB12) | `user_id`, `user_name` |
| `reply` | Reply reference | `message_id`, `user_id` |
| `image` | Image | `file_id`, `url` |
| `video` | Video | `file_id`, `url`, `duration`, `width`, `height` |
| `voice` | Voice | `file_id`, `url`, `duration` |
| `audio` | Audio | `file_id`, `url`, `duration`, `title`, `performer` |
| `file` | File | `file_id`, `url`, `file_name`, `file_size`, `mime_type` |
| `location` | Location | `latitude`, `longitude`, optional `title`, `address` |

### Platform Extension Message Segments

Message segments with `telegram_` prefix:

| Message Segment Type | Description | Data Field |
|---|---|---|
| `telegram_sticker` | Sticker | `file_id`, `emoji`, `sticker_type`, `url` |
| `telegram_animation` | GIF animation | `file_id`, `url`, `duration`, `caption` |
| `telegram_contact` | Contact | `phone_number`, `first_name`, `last_name`, `user_id` |
| `telegram_inline_keyboard` | Inline keyboard | `inline_keyboard` |

### Event Examples

#### Group Message (with @ mention)
```python
{
  "type": "message",
  "detail_type": "group",
  "platform": "telegram",
  "user_id": "6117725680",
  "user_nickname": "WSu2059",
  "group_id": "-1002850921906",
  "message_id": "172",
  "message": [
    {"type": "text", "data": {"text": "/it.echo "}},
    {"type": "mention", "data": {"user_id": "", "user_name": "@nm123_91178"}}
  ],
  "alt_message": "/it.echo @nm123_91178",
  "telegram_chat": {
    "id": -1002850921906,
    "title": "ErisPulse",
    "username": "erispulse",
    "type": "supergroup"
  }
}
```

#### Callback Query Event
```python
{
  "type": "notice",
  "detail_type": "telegram_callback_query",
  "user_id": "123456",
  "user_nickname": "YingXinche",
  "telegram_callback_id": "cb_123",
  "telegram_callback_data": "callback_data",
  "message_id": "msg_456"
}
```

#### Inline Query Event
```python
{
  "type": "request",
  "detail_type": "telegram_inline_query",
  "user_id": "789012",
  "user_nickname": "YingXinche",
  "telegram_query_id": "iq_789",
  "telegram_query_text": "search_text",
  "telegram_query_offset": "0"
}
```

#### Message with Inline Keyboard
```python
{
  "type": "message",
  "detail_type": "group",
  "message": [
    {"type": "text", "data": {"text": "Please select:"}},
    {
      "type": "telegram_inline_keyboard",
      "data": {
        "inline_keyboard": [
          [{"text": "Button 1", "callback_data": "btn1"}],
          [{"text": "Visit", "url": "https://example.com"}]
        ]
      }
    }
  ]
}
```

## Event Mixin Extension Methods

The adapter registers the following platform-specific methods, available only when `platform == "telegram"`:

### Message-related

| Method | Return Type | Description |
|--------|-------------|-------------|
| `is_bot_message()` | `bool` | Check if message is from bot |
| `is_edited_message()` | `bool` | Check if message is edited |
| `is_topic_message()` | `bool` | Check if message is topic/Topic message |
| `get_update_id()` | `int` | Get Telegram update ID |
| `get_chat_title()` | `str` | Get chat title |
| `get_chat_username()` | `str` | Get chat username |
| `get_forward_from()` | `dict` | Get forwarding source info |
| `get_topic_id()` | `str` | Get topic ID |

### Callback Query-related

| Method | Return Type | Description |
|--------|-------------|-------------|
| `get_callback_data()` | `str` | Get callback query's callback_data |
| `get_callback_id()` | `str` | Get callback query ID (used for response) |

### Message Segment Data Extraction

| Method | Return Type | Description |
|--------|-------------|-------------|
| `get_inline_keyboard()` | `list` | Get inline keyboard from message |
| `get_sticker_info()` | `dict` | Get sticker info |
| `get_contact_info()` | `dict` | Get contact info |
| `get_location()` | `dict` | Get location info |

### Usage Example

```python
from ErisPulse.Core.Event import message, notice

@message.on_message()
async def handle_message(event):
    if event.get("platform") != "telegram":
        return

    # Message properties
    if event.is_bot_message():
        return  # Ignore bot messages

    if event.is_edited_message():
        print("This is an edited message")

    # Chat info
    title = event.get_chat_title()
    username = event.get_chat_username()

    # Forward source
    forward = event.get_forward_from()

    # Message segment data
    sticker = event.get_sticker_info()
    contact = event.get_contact_info()
    location = event.get_location()
    keyboard = event.get_inline_keyboard()

    # Topic
    if event.is_topic_message():
        topic_id = event.get_topic_id()

@notice.on_notice()
async def handle_notice(event):
    if event.get("platform") != "telegram":
        return

    if event.get("detail_type") == "telegram_callback_query":
        callback_data = event.get_callback_data()
        callback_id = event.get_callback_id()

        # Respond to callback query
        telegram = sdk.adapter.get("telegram")
        await telegram.Send.AnswerCallback(callback_id, text="Clicked")

        # Reply to message
        await event.reply(f"You clicked: {callback_data}")
```

## Extension Field Explanation

- All unique fields are prefixed with `telegram_`
- Original data is preserved in the `telegram_raw` field
- Original event type is preserved in the `telegram_raw_type` field
- Channel messages use `detail_type="channel"`
- Private messages use `detail_type="private"` (must be converted to `user` when sending)
- Topic messages include the `thread_id` field
- `@` mentions use the standard `mention` message segment type (`type: "mention"`), with no `@username` in the text

## Configuration Options

The Telegram adapter supports multi-account configuration:

### Configuration Example
```toml
[Telegram_Adapter.accounts.default]
token = "YOUR_BOT_TOKEN"
enabled = true

[Telegram_Adapter.accounts.bot2]
token = "ANOTHER_BOT_TOKEN"
enabled = true
```

### Running Mode

The Telegram adapter only supports **Polling (polling)** mode; Webhook mode has been removed.

### Proxy Configuration

If you need to connect to the Telegram API through a proxy, use system-level proxy (environment variables `ALL_PROXY` / `HTTPS_PROXY`).

### Migration from Old Configuration

Old single-token configuration is automatically compatible:
```toml
# Old format (still usable, but migration is recommended)
[Telegram_Adapter]
token = "YOUR_BOT_TOKEN"
```

Migration is recommended to the new format:
```toml
[Telegram_Adapter.accounts.default]
token = "YOUR_BOT_TOKEN"
enabled = true
```