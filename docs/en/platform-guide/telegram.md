# Telegram Platform Features Documentation

TelegramAdapter is an adapter built on the Telegram Bot API, supporting multiple message types and event handling.

---

## Document Information

- Corresponding module version: 4.3.3
- Maintainer: ErisPulse
- Last updated: 2026-11-10

## Basic Information

- Platform overview: Telegram is a cross-platform instant messaging application
- Adapter name: TelegramAdapter
- Supported protocol/API version: Telegram Bot API
- Chat type mapping: `private` → use `user` when sending; `group`/`supergroup` → `group`; `channel` → `channel`

## Standardization Alignment (4.3.3)

This section describes the standardization alignment completed in version 4.3.3: event changes, multi-account conventions, error code specifications, and Send specifications.

### Event Changes

1. **Group join request event standardization**:
   - `detail_type` changed from `telegram_chat_join_request` to the standard `"group"`, with `sub_type="join"`
   - `@request.on_group_request()` can now directly match this event
   - The `request_id` composition rule remains unchanged: `tjr_{chat_id}_{user_id}_{date}`
   - The event can be approved via `event.approve()` / `event.reject()` (corresponding to `approveChatJoinRequest` / `declineChatJoinRequest`)
2. **Event `self.account_id` injection**: All events carry the name of the account that produced them; in multi-account scenarios, `event.reply()` automatically sends via that account
3. **unknown events**: `self.user_id` is filled with the bot_id (consistent with message event behavior)

The request event interface conventions follow the SDK standard: [Request and Approval Action Specification](../standards/request-action-spec.md).

### Accounts and Multi-Account

`call_api` supports dual-compatible account fields: the standard field `account_id` (ApiDSL.Using passes this name) / the legacy alias `_account_id`; the framework's ApiDSL automatically adapts to both new and old adapters.

```python
from ErisPulse import sdk
telegram = sdk.adapter.get("telegram")

await telegram.Api.Using("main").get_self_info()        # Specify the account the standard way
await telegram.Api.get_self_info(account_id="main")     # Explicitly pass the standard field account_id
```

### Error Code Specification

| retcode | Description |
|---------|------|
| 0 | Success |
| 33001 | Network error (connection failure, timeout, etc.) |
| 34100 | Platform rejection (the original response is retained in the `telegram_raw` field) |
| 10002 | Unsupported action (e.g., `get_friend_list` / `get_group_list`; the Telegram Bot API has no corresponding endpoints) |

### Send Specification

- The HTML method is named `HTML`; `Html` is a reserved alias
- The `Location` signature now includes the optional `title` / `content` parameters
- `AnswerCallback` / `Raw_json` use the send_context account: when the send DSL is called within an event handling chain, sending automatically uses the account associated with the current event

## Standard Api Actions (Api DSL)

The adapter maps OB12 standard actions to the Telegram Bot API and standardizes the data fields:

| OB12 Standard Action | Telegram API | data Fields |
|--------------|--------------|----------|
| get_self_info | getMe | user_id / user_name / user_displayname |
| get_user_info(user_id) | getChat | user_id / user_name / user_displayname |
| get_group_info(group_id) | getChat | group_id / group_name |
| get_group_member_info(group_id, user_id) | getChatMember | user_id / user_name / telegram_role |
| delete_message(message_id) | deleteMessage | Automatically completes chat_id via the message registry |
| leave_group(group_id) | leaveChat | - |

Extended actions: get_group_admin_list(group_id) (admin list), get_chat_member_count(chat_id) (member count).

```python
from ErisPulse import sdk
telegram = sdk.adapter.get("telegram")

result = await telegram.Api.get_self_info()
result = await telegram.Api.get_group_info(group_id=-100123)
result = await telegram.Api.get_group_admin_list(-100123)
await telegram.Api.delete_message(message_id=55)   # Automatically completes chat_id
result = await telegram.Api.Using("main").get_self_info()
```

> The Telegram Bot API has no endpoints for retrieving friend lists/group lists; get_friend_list/get_group_list explicitly return
> retcode=10002 (unsupported action).

---

## Request Operations (Request DSL)

Handles group join requests, based on approveChatJoinRequest / declineChatJoinRequest. Since 4.3.3, `chat_join_request` is mapped to the standard `group` request event (`sub_type="join"`), so `@request.on_group_request()` can now directly match it:

```python
from ErisPulse.Core.Event import request

@request.on_group_request()
async def handle_join_request(event):
    if event.get("platform") != "telegram":
        return
    # event["request_id"] is a synthetic identifier (tjr_{chat_id}_{user_id}_{date}; the rule is unchanged)
    if event.get("sub_type") == "join":
        await event.approve()          # Approve (approveChatJoinRequest)
    # await event.reject()             # Reject (declineChatJoinRequest)

# Manual invocation (the corresponding request event must have been received first to register the context)
await telegram.Request(event["request_id"]).accept()
await telegram.Request(event["request_id"]).reject()
await telegram.Request(event["request_id"]).Using("main").accept()
```

---

## Supported Message Sending Types

All send methods are implemented via chained syntax, for example:
```python
from ErisPulse.Core import adapter
telegram = adapter.get("telegram")

await telegram.Send.To("user", user_id).Text("Hello World!")
```

### Basic Send Methods

| Method | Description | Parameters |
|------|------|------|
| `.Text(text)` | Send a plain text message | `text: str` |
| `.Face(emoji)` | Send an emoji dice | `emoji: str` (e.g., 🎲 🎯 🏀) |
| `.Markdown(text, content_type)` | Send a Markdown-formatted message | `content_type` defaults to `"MarkdownV2"` |
| `.HTML(text)` | Send an HTML-formatted message (`Html` is a reserved alias) | `text: str` |
| `.MergeForward(nodes, title)` | Send a merged forwarded message (title + each item as a blockquote, truncated at 4096) | `nodes: List[Dict]`, `title: str` |
| `.Sticker(file)` | Send a sticker | `file: str (file_id/URL) \| bytes` |
| `.Location(lat, lng, title="", content="")` | Send a location (optional title and content) | `latitude: float, longitude: float, title: str, content: str` |
| `.Venue(lat, lng, title, addr)` | Send a venue | Includes title and address |
| `.Contact(phone, first, last)` | Send a contact | Includes phone number and name |

### Media Send Methods

All media methods support two input types: `bytes` (upload) and `str` (file_id / URL):

| Method | Description |
|------|------|
| `.Image(file, caption, content_type)` | Send an image |
| `.Video(file, caption, content_type)` | Send a video |
| `.Voice(file, caption)` | Send a voice message |
| `.Audio(file, caption, content_type)` | Send audio |
| `.File(file, caption)` | Send a file |
| `.Document(file, caption, content_type)` | Alias of File |

### Message Management Methods

| Method | Description |
|------|------|
| `.Edit(message_id, text, content_type)` | Edit an existing message |
| `.Recall(message_id)` | Delete the specified message |
| `.Forward(from_chat_id, message_id)` | Forward a message (preserving the source) |
| `.CopyMessage(from_chat_id, message_id)` | Copy a message (without the source) |
| `.AnswerCallback(callback_query_id, text, show_alert)` | Answer a callback query (uses the send_context account) |

### Raw Message Sending

- `.Raw_ob12(message: List[Dict])`: Send a message in OneBot12 standard format
- `.Raw_json(json_str: str)`: Send a raw JSON-format message (uses the send_context account)

### Chained Modifier Methods

| Method | Description |
|------|------|
| `.At(user_id)` | @mention a specified user (implemented via Telegram entities; can be called multiple times) |
| `.AtAll()` | @mention all members (sends the `@All` text) |
| `.Reply(message_id)` | Reply to a specified message |
| `.Keyboard(inline_keyboard)` | Set an inline keyboard (`list[list[dict]]`) |
| `.ProtectContent(protect)` | Protect content (prevents forwarding and saving) |
| `.Silent(silent)` | Send silently (does not notify the user) |

### Sending Examples

```python
# Basic text sending
await telegram.Send.To("user", user_id).Text("Hello World!")

# Message with an inline keyboard
from ErisPulse import sdk
telegram = sdk.adapter.get("telegram")
keyboard = [
    [{"text": "Button 1", "callback_data": "btn1"}, {"text": "Button 2", "callback_data": "btn2"}],
    [{"text": "Visit Website", "url": "https://example.com"}],
]
await telegram.Send.To("group", group_id).Keyboard(keyboard).Text("Please choose:")

# Media sending (via URL)
await telegram.Send.To("group", group_id).Image("https://example.com/image.jpg", caption="Image")

# @user
await telegram.Send.To("group", group_id).At("6117725680").Text("Hello!")

# Reply + protected content
await telegram.Send.To("group", group_id).Reply("12345").ProtectContent().Text("Confidential message")

# Silent sending
await telegram.Send.To("group", group_id).Silent().Text("Silent notification")

# HTML-formatted message (Html is an alias for the old name)
await telegram.Send.To("user", user_id).HTML("<b>Bold</b> <i>Italic</i>")

# Send a location (with title)
await telegram.Send.To("user", user_id).Location(39.9042, 116.4074, title="Tiananmen", content="Beijing city center")

# Answer a callback query
await telegram.Send.AnswerCallback(callback_query_id, text="Processed", show_alert=False)

# OneBot12 composite message
ob12_message = [
    {"type": "text", "data": {"text": "Complex message:"}},
    {"type": "mention", "data": {"user_id": "6117725680", "user_name": "Username"}},
    {"type": "reply", "data": {"message_id": "12345"}},
    {"type": "image", "data": {"file": "https://http.cat/200"}}
]
await telegram.Send.To("group", group_id).Raw_ob12(ob12_message)

# Send a sticker
await telegram.Send.To("user", user_id).Sticker("CAACAgIAAxkBAA...")  # file_id
```

## Platform-Specific Event Types

Telegram event conversion follows the OneBot12 standard, while also providing platform extensions via the `telegram_` prefix.

### Message Event detail_type Mapping

| Telegram chat.type | OneBot12 detail_type | Send Target Type |
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
| `telegram_my_chat_member` | Changes in the Bot's own member status |
| `telegram_chat_member` | Chat member changes |
| `telegram_shipping_query` | Shipping query |
| `telegram_pre_checkout_query` | Pre-checkout query |

> The chat join request (chat_join_request) has been standardized into a `group` request event (`sub_type="join"`).
> `telegram_chat_join_request` is no longer used as the detail_type; related platform fields
> (such as `telegram_chat_join_request_id` and `telegram_chat`) are still retained.

### Standard Message Segment Types

Converted message segments use the OneBot12 standard format:

| Message Segment Type | Description | data Fields |
|---|---|---|
| `text` | Plain text (excluding @username) | `text` |
| `mention` | @user (standard OB12) | `user_id`, `user_name` |
| `reply` | Reply quote | `message_id`, `user_id` |
| `image` | Image | `file_id`, `url` |
| `video` | Video | `file_id`, `url`, `duration`, `width`, `height` |
| `voice` | Voice | `file_id`, `url`, `duration` |
| `audio` | Audio | `file_id`, `url`, `duration`, `title`, `performer` |
| `file` | File | `file_id`, `url`, `file_name`, `file_size`, `mime_type` |
| `location` | Location | `latitude`, `longitude`, optional `title`, `address` |

### Platform Extension Message Segments

Extension message segments identified by the `telegram_` prefix:

| Message Segment Type | Description | data Fields |
|---|---|---|
| `telegram_sticker` | Sticker | `file_id`, `emoji`, `sticker_type`, `url` |
| `telegram_animation` | GIF animation | `file_id`, `url`, `duration`, `caption` |
| `telegram_contact` | Contact | `phone_number`, `first_name`, `last_name`, `user_id` |
| `telegram_inline_keyboard` | Inline keyboard | `inline_keyboard` |

### Event Examples

#### Group Message (with @mention)
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
  "self": {
    "platform": "telegram",
    "user_id": "6117725680",
    "account_id": "default"
  },
  "telegram_chat": {
    "id": -1002850921906,
    "title": "ErisPulse",
    "username": "erispulse",
    "type": "supergroup"
  }
}
```

#### Group Join Request Event (after standardization)
```python
{
  "type": "request",
  "detail_type": "group",
  "sub_type": "join",
  "platform": "telegram",
  "user_id": "6117725680",
  "user_nickname": "Applicant nickname",
  "request_id": "tjr_-1002850921906_6117725680_1731212345",
  "group_id": "-1002850921906",
  "comment": "Invite link name",
  "self": {
    "platform": "telegram",
    "user_id": "6117725680",
    "account_id": "default"
  },
  "telegram_chat_join_request_id": "",
  "telegram_chat": {
    "id": -1002850921906,
    "title": "ErisPulse",
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
    {"type": "text", "data": {"text": "Please choose:"}},
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

### Message-Related

| Method | Return Type | Description |
|------|----------|------|
| `is_bot_message()` | `bool` | Determine whether the message comes from a bot |
| `is_edited_message()` | `bool` | Determine whether the message has been edited |
| `is_topic_message()` | `bool` | Determine whether it is a topic message |
| `get_update_id()` | `int` | Get the Telegram update ID |
| `get_chat_title()` | `str` | Get the chat title |
| `get_chat_username()` | `str` | Get the chat username |
| `get_forward_from()` | `dict` | Get the forward source information |
| `get_topic_id()` | `str` | Get the topic ID |

### Callback Query-Related

| Method | Return Type | Description |
|------|----------|------|
| `get_callback_data()` | `str` | Get the callback_data of the callback query |
| `get_callback_id()` | `str` | Get the callback query ID (used for answering) |

### Message Segment Data Extraction

| Method | Return Type | Description |
|------|----------|------|
| `get_inline_keyboard()` | `list` | Get the inline keyboard in the message |
| `get_sticker_info()` | `dict` | Get sticker information |
| `get_contact_info()` | `dict` | Get contact information |
| `get_location()` | `dict` | Get location information |

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

    # Chat information
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

        # Answer the callback query
        telegram = sdk.adapter.get("telegram")
        await telegram.Send.AnswerCallback(callback_id, text="Clicked")

        # Reply to the message (in multi-account mode, automatically handled by the account associated with the event)
        await event.reply(f"You clicked: {callback_data}")
```

## Extension Field Descriptions

- All platform-specific fields are identified by the `telegram_` prefix
- The original data is retained in the `telegram_raw` field
- The original event type is retained in the `telegram_raw_type` field
- The event's `self.account_id` is the name of the account that produced the event (in multi-account mode, `event.reply()` is automatically handled by that account)
- Channel messages use `detail_type="channel"`
- Private messages use `detail_type="private"` (must be converted to `user` when sending)
- Topic messages include the `thread_id` field
- @mentions use the standard `mention` message segment type (`type: "mention"`), and the text does not include the @username

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

The Telegram adapter only supports **Polling** mode; the Webhook mode has been removed.

### Proxy Configuration

To connect to the Telegram API through a proxy, use a system-level proxy (environment variables `ALL_PROXY` / `HTTPS_PROXY`).

### Legacy Configuration Migration

The legacy single-token configuration remains automatically compatible:
```toml
# Legacy format (still usable, but migration is recommended)
[Telegram_Adapter]
token = "YOUR_BOT_TOKEN"
```

It is recommended to migrate to the new format:
```toml
[Telegram_Adapter.accounts.default]
token = "YOUR_BOT_TOKEN"
enabled = true
```