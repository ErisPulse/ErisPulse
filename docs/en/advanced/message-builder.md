# MessageBuilder Explained

`MessageBuilder` is a OneBot12 standard message segment builder provided by ErisPulse, used to construct structured message content, and should be used in conjunction with `Send.Raw_ob12()`.

## Import Methods

`MessageBuilder` supports the following two import methods (both have the same effect; the first is recommended):

```python
from ErisPulse.Core.Event import MessageBuilder        # Recommended, import via package export
from ErisPulse.Core.Event.message_builder import MessageBuilder  # Directly import the module
```

## Dual Mode Mechanism

The `MessageBuilder` provides two usage modes, implemented through Python's descriptor mechanism (`__get__`), achieving different behaviors at the class and instance levels: when methods are called through the class, `__get__` returns the execution result of the static method; when called through an instance, it returns `self` to support method chaining.

### Chaining Mode (Instance)

Use by instantiating `MessageBuilder()`. Each method returns `self`, supporting method chaining, and finally use `.build()` to obtain the message segment list:

```python
from ErisPulse.Core.Event.message_builder import MessageBuilder

segments = (
    MessageBuilder()
    .text("Hello!")
    .image("https://example.com/photo.jpg")
    .build()
)
# [
#     {"type": "text", "data": {"text": "Hello!"}},
#     {"type": "image", "data": {"file": "https://example.com/photo.jpg"}}
# ]
```

### Quick Build Mode (Static)

Call methods directly through the class. Each method directly returns a list of message segments, suitable for single-segment messages:

```python
# Directly returns list[dict], no need for .build()
segments = MessageBuilder.text("Hello!")
# [{"type": "text", "data": {"text": "Hello!"}}]
```

## Message Segment Types

| Method | Type | Data Parameters | Description |
|------|------|---------|------|
| `text(text)` | text | `text` | Text message |
| `image(file)` | image | `file` | Image message |
| `audio(file)` | audio | `file` | Audio message |
| `video(file)` | video | `file` | Video message |
| `file(file, filename?)` | file | `file`, `filename` | File message |
| `mention(user_id, user_name?)` | mention | `user_id`, `user_name` | @Mention a user |
| `at(user_id, user_name?)` | mention | `user_id`, `user_name` | Alias of `mention` |
| `reply(message_id)` | reply | `message_id` | Reply to a message |
| `at_all()` | mention_all | - | @All members |
| `custom(type, data)` | Custom | Custom | Custom message segment |

## Using with Send

The constructed list of message segments is sent using `Send.Raw_ob12()`:

```python
from ErisPulse import sdk
from ErisPulse.Core.Event.message_builder import MessageBuilder

# Build and send using chaining
segments = (
    MessageBuilder()
    .mention("user123", "Zhang San")
    .text(" Please check this image")
    .image("https://example.com/photo.jpg")
    .build()
)
await sdk.adapter.myplatform.Send.To("group", "group456").Raw_ob12(segments)
```

### Replying with Event

```python
from ErisPulse.Core.Event import command

@command("report")
async def report_handler(event):
    await event.reply_ob12(
        MessageBuilder()
        .text("📊 Daily Report Summary\n")
        .text("Tasks completed today: 5\n")
        .text("Tasks in progress: 3")
        .build()
    )
```

## Utility Methods

### copy()

Creates a copy of the current builder, allowing multiple message variants to be created based on the same base content:

```python
base = MessageBuilder().text("Base content").mention("admin")

# Build different messages based on the same prefix
msg1 = base.copy().text(" Variant A").build()
msg2 = base.copy().text(" Variant B").image("img.jpg").build()
```

### clear()

Clears previously added message segments, allowing reuse of the same builder:

```python
builder = MessageBuilder()

for user_id in ["user1", "user2", "user3"]:
    builder.clear()
    msg = builder.mention(user_id).text(" Hello!").build()
    await adapter.Send.To("user", user_id).Raw_ob12(msg)
```

### len() / bool()

```python
builder = MessageBuilder()
print(bool(builder))   # False

builder.text("Hello")
print(len(builder))    # 1
print(bool(builder))   # True
```

## Custom Message Segments

Use the `custom()` method to add platform-specific message segments:

```python
# Add platform-specific message segments
segments = (
    MessageBuilder()
    .text("Please fill out the form:")
    .custom("yunhu_form", {"form_id": "12345"})
    .build()
)
```

> Custom message segments are only effective in the corresponding platform adapter; other adapters will ignore unrecognized message segments.

## Complete Examples

### Multi-element Message

```python
segments = (
    MessageBuilder()
    .reply(event.get_id())                    # Reply to the original message
    .mention(event.get_user_id())             # @ sender
    .text(" This is your query result:\n")    # Text
    .image("https://example.com/chart.png")   # Image
    .text("\nSee the attachment for detailed data:")
    .file("https://example.com/data.csv", filename="data.csv")
    .build()
)
await event.reply_ob12(segments)
```

### Static Factory + Chain Mixing

```python
# Quickly build a single-segment message
simple_msg = MessageBuilder.text("Simple text")

# Chain-build a complex message
complex_msg = (
    MessageBuilder()
    .at_all()
    .text(" 📢 Announcement:")
    .text("Meeting at 3 PM today")
    .build()
)
```

## Related Documentation

- [Adapter SendDSL Detailed Explanation](../developer-guide/adapters/send-dsl.md) - Send chainable sending interface
- [Event Conversion Standard](../standards/event-conversion.md) - Message segment conversion specification
- [Event Wrapper Class](../developer-guide/modules/event-wrapper.md) - Event.reply_ob12() method