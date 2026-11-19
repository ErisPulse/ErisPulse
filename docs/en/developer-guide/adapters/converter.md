# Event Converter Implementation Guide

> [!TIP]
> **When to read this**: Required reading within the adapter development path (event converter). Skip it if not needed — it won't affect the use of other features.

After the adapter receives a platform-native event, the event Converter transforms it into ErisPulse's unified OneBot12 standard format — how platform events enter the framework is decided by this single class.

## Converter Responsibilities

```
Platform-native event ──→ Converter.convert() ──→ OneBot12 standard event
```

The Converter is only responsible for **forward conversion** (receiving direction), i.e., converting the platform's native event data into the OneBot12 standard format. Reverse conversion (sending direction) is handled by the `Send.Raw_ob12()` method.

### Core Principles

1. **Lossless conversion**: The original data must be fully preserved in the `{platform}_raw` field
2. **Standard compatibility**: The converted event must conform to the OneBot12 standard format
3. **Platform extensions**: Platform-specific data is stored in fields prefixed with `{platform}_`

## BaseConverter Base Class (Recommended)

Starting from 2.7.0, the framework provides the `BaseConverter` base class (`ErisPulse.Core.Bases`), which encapsulates **common field construction** for OneBot12 events and **common message segment helpers**, so that converters only need to focus on type mapping:

```python
from ErisPulse.Core.Bases import BaseConverter


class MyConverter(BaseConverter):
    def __init__(self):
        super().__init__(platform="myplatform")

    def convert(self, raw_event: dict) -> dict | None:
        if not isinstance(raw_event, dict):
            return None
        event_type = raw_event.get("type", "")
        base = self.build_base_event(raw_event, event_type)  # id/time/platform/self/raw
        if event_type == "message":
            base["type"] = "message"
            base["detail_type"] = "group" if raw_event.get("group_id") else "private"
            base["user_id"] = str(raw_event.get("sender_id", ""))
            base["message"] = [self.text(raw_event.get("content", ""))]
            base["alt_message"] = raw_event.get("content", "")
            return base
        return None
```

Common fields already populated by `build_base_event()`:

| Field | Source |
|------|--------|
| `id` | `raw_event["event_id"]`, defaults to an auto-generated UUID |
| `time` | `raw_event["timestamp"]`, defaults to the current time |
| `platform` | The `platform` passed in at construction |
| `self` | `{"platform": ..., "user_id": raw_event["bot_id"]}` |
| `{platform}_raw` | The raw event (satisfies the "lossless conversion" principle) |
| `{platform}_raw_type` | The raw event type |

Common message segment helper methods (all static methods, reusable directly):

```python
converter.text("hi")          # {"type": "text", "data": {"text": "hi"}}
converter.at("123456")        # {"type": "at", "data": {"user_id": "123456"}}
converter.image("file.png")   # {"type": "image", "data": {"file": "file.png"}}
```

> When implementing manually, the common field construction in `build_base_event` is boilerplate code that must be written repeatedly. Using `BaseConverter` saves you this part and naturally satisfies "lossless conversion" (the raw event always goes into `{platform}_raw`).

## The convert() Method

### Method Signature

```python
def convert(self, raw_event: dict) -> dict:
    """
    Convert a platform-native event into the OneBot12 standard format

    :param raw_event: Platform-native event data
    :return: A OneBot12 standard-format event dictionary
    """
    pass
```

### Return Value Structure

The converted event dictionary should contain the following standard fields:

```python
{
    "id": "Unique event ID",
    "time": 1234567890,           # Unix timestamp (seconds)
    "type": "message",             # Event type
    "detail_type": "private",      # Detail type
    "platform": "myplatform",      # Platform name
    "self": {
        "platform": "myplatform",
        "user_id": "bot_user_id"
    },

    # Message event fields
    "user_id": "sender_id",
    "message": [...],              # List of OneBot12 message segments
    "alt_message": "Plain text content",

    # The raw data must be preserved
    "myplatform_raw": { ... },     # Complete platform-native event data
    "myplatform_raw_type": "Native event type name",
}
```

## Required Field Mapping

### Common Fields (All Event Types)

| OB12 Field | Type | Description |
|-----------|------|-------------|
| `id` | str | Unique event identifier |
| `time` | int | Unix timestamp (seconds) |
| `type` | str | Event type: `message` / `notice` / `request` / `meta` |
| `detail_type` | str | Detail type: `private` / `group` / `friend`, etc. |
| `platform` | str | Platform name, consistent with the adapter's registered name |
| `self` | dict | Bot information: `{"platform": "...", "user_id": "..."}` |

### Additional Fields for Message Events

| OB12 Field | Type | Description |
|-----------|------|-------------|
| `user_id` | str | Sender ID |
| `message` | list[dict] | List of OneBot12 message segments |
| `alt_message` | str | Plain text fallback content |

### Additional Fields for Notice Events

| OB12 Field | Type | Description |
|-----------|------|-------------|
| `user_id` | str | Related user ID |
| `operator_id` | str | Operator ID (e.g., group member changes) |

## Message Segment Conversion

The OneBot12 standard defines the following message segment types:

```python
# Text
{"type": "text", "data": {"text": "Hello"}}

# Image
{"type": "image", "data": {"file": "https://example.com/img.jpg"}}

# Audio
{"type": "audio", "data": {"file": "https://example.com/audio.mp3"}}

# Video
{"type": "video", "data": {"file": "https://example.com/video.mp4"}}

# File
{"type": "file", "data": {"file": "https://example.com/doc.pdf"}}

# Mention (@)
{"type": "mention", "data": {"user_id": "123"}}

# Mention all (@everyone)
{"type": "mention_all", "data": {}}

# Reply
{"type": "reply", "data": {"message_id": "msg_123"}}
```

If the platform has message segment types that are not supported, you can omit that segment or convert it to the closest standard type.

## alt_message Rendering Conventions

`alt_message` is the plain text fallback content of a message event, used for log archiving, `extract_text` text matching, and as a fallback for command dispatch. Adapters should follow these conventions when generating `alt_message` (pay special attention to mention segments):

- **Mention segments** should preferably be rendered as `@nickname`; fall back to `@{user_id}` when the platform does not provide a nickname; render as `@everyone` when `user_id` is `all` (mentioning all members)
- **When both the nickname and `user_id` are missing, omit the segment** and never output an empty `"@"` — for example, `"@ help"` would pollute text matching and command parsing
- Beware of the `data.get("user_name", fallback)` pitfall: if `user_name` was stored as an empty string by default when constructing the segment, the key exists, so the fallback never takes effect; use the pattern `data.get("user_name") or data.get("user_id")` instead
- The rendering style of other message segments (e.g., `[image]`, `[voice]`) and the way segments are joined together (`""` or `" "`) should keep each adapter's existing convention; forced unification is not required

```python
# Mention segment rendering example
data = seg.get("data") or {}
user_id = str(data.get("user_id") or "").strip()
user_name = str(data.get("user_name") or "").strip()
if user_id == "all":
    parts.append("@everyone")
elif user_name:
    parts.append(f"@{user_name}")
elif user_id:
    parts.append(f"@{user_id}")
```

## Platform Extension Fields

Platform-specific data should be stored using the `{platform}_` prefix to avoid conflicts with standard fields:

```python
{
    # Standard fields
    "type": "message",
    "detail_type": "group",
    # ...

    # Platform extension fields
    "myplatform_raw": { ... },          # Raw event data (required)
    "myplatform_raw_type": "chat",      # Raw event type (required)

    # Other platform-specific fields
    "myplatform_group_name": "Group name",
    "myplatform_sender_role": "admin",
}
```

> **Important**: The `{platform}_raw` field is required; ErisPulse's event system and modules may rely on it to access the platform's raw data.

## Complete Example

The following is a complete Converter implementation:

```python
class MyConverter:
    def __init__(self, platform: str):
        self.platform = platform

    def convert(self, raw_event: dict) -> dict:
        event_type = raw_event.get("type", "")

        base_event = {
            "id": raw_event.get("id", ""),
            "time": raw_event.get("timestamp", 0),
            "platform": self.platform,
            "self": {
                "platform": self.platform,
                "user_id": raw_event.get("self_id", ""),
            },
            "myplatform_raw": raw_event,
            "myplatform_raw_type": event_type,
        }

        if event_type == "chat":
            return self._convert_message(raw_event, base_event)
        elif event_type == "notification":
            return self._convert_notice(raw_event, base_event)
        elif event_type == "request":
            return self._convert_request(raw_event, base_event)

        return base_event

    def _convert_message(self, raw: dict, base: dict) -> dict:
        base["type"] = "message"
        base["detail_type"] = "group" if raw.get("group_id") else "private"
        base["user_id"] = raw.get("sender_id", "")
        base["message"] = self._convert_message_segments(raw.get("content", ""))
        base["alt_message"] = raw.get("content", "")

        if raw.get("group_id"):
            base["group_id"] = raw["group_id"]

        return base

    def _convert_message_segments(self, content: str) -> list:
        segments = []
        if content:
            segments.append({"type": "text", "data": {"text": content}})
        return segments

    def _convert_notice(self, raw: dict, base: dict) -> dict:
        base["type"] = "notice"
        notification_type = raw.get("notification_type", "")

        if notification_type == "member_join":
            base["detail_type"] = "group_member_increase"
            base["user_id"] = raw.get("user_id", "")
            base["group_id"] = raw.get("group_id", "")
            base["operator_id"] = raw.get("operator_id", "")
        elif notification_type == "friend_add":
            base["detail_type"] = "friend_increase"
            base["user_id"] = raw.get("user_id", "")

        return base

    def _convert_request(self, raw: dict, base: dict) -> dict:
        base["type"] = "request"
        request_type = raw.get("request_type", "")

        if request_type == "friend":
            base["detail_type"] = "friend"
            base["user_id"] = raw.get("user_id", "")
            base["comment"] = raw.get("message", "")
        elif request_type == "group_invite":
            base["detail_type"] = "group"
            base["group_id"] = raw.get("group_id", "")
            base["user_id"] = raw.get("inviter_id", "")

        return base
```

## Rich Media Message Conversion Example

Messages from real platforms usually contain rich media content such as images, mentions, and replies. Below is an example of `_convert_message_segments` handling multiple message types:

```python
def _convert_message_segments(self, raw_content: list) -> list:
    """Convert a list of platform-native message segments into OneBot12 standard message segments"""
    segments = []

    for item in raw_content:
        item_type = item.get("type", "")

        if item_type == "text":
            segments.append({
                "type": "text",
                "data": {"text": item.get("content", "")}
            })

        elif item_type == "image":
            file_url = item.get("url") or item.get("file_id", "")
            segments.append({
                "type": "image",
                "data": {"file": file_url}
            })

        elif item_type == "at":
            segments.append({
                "type": "mention",
                "data": {"user_id": item.get("target_id", "")}
            })

        elif item_type == "reply":
            segments.append({
                "type": "reply",
                "data": {"message_id": item.get("reply_to_id", "")}
            })

        elif item_type == "at_all":
            segments.append({"type": "mention_all", "data": {}})

        else:
            segments.append({
                "type": "text",
                "data": {"text": f"[Unsupported message type: {item_type}]"}
            })

    return segments
```

## Common Pitfalls

### 1. Missing the `{platform}_raw` Field

This is the most common mistake. A missing raw data field prevents modules from accessing platform-specific information.

```python
base_event["myplatform_raw"] = raw_event        # Required!
base_event["myplatform_raw_type"] = event_type   # Required!
```

### 2. Incorrect Timestamp Format

The OneBot12 standard requires the `time` field to be a Unix second-level timestamp (integer). If your platform returns millisecond timestamps or ISO format strings, conversion is needed:

```python
import time

# Milliseconds → seconds
"time": raw_event.get("timestamp", 0) // 1000

# ISO string → seconds
"time": int(time.mktime(time.strptime(raw_event["created_at"], "%Y-%m-%dT%H:%M:%S")))
```

### 3. Missing the `self` Field

The `self` field contains the bot's own information, where `user_id` is the bot's account ID. This field is critical in multi-bot scenarios:

```python
"self": {
    "platform": self.platform,
    "user_id": raw_event.get("bot_id", ""),   # The bot's own ID
}
```

### 4. Using Non-Standard Values for detail_type

`detail_type` must use values defined by the OneBot12 standard, such as `private`, `group`, `friend_increase`, `group_member_increase`, etc. Do not use platform-specific naming.

### 5. Round-Trip Consistency

Ensure that the message segment types generated by the Converter correspond to the methods supported on the Send side. For example, if the Converter converts the platform's image messages into `{"type": "image", ...}`, then the `Image()` method on the Send side must be able to handle image sending.

## Best Practices

1. **Always preserve the raw data**: The `{platform}_raw` field must not be omitted
2. **Use standard message segments**: Convert platform messages into OneBot12 standard message segments whenever possible
3. **Set detail_type appropriately**: Use standard types (`private`/`group`/`channel`, etc.); do not invent custom ones
4. **Handle edge cases**: Raw events may lack certain fields; use `.get()` and provide sensible default values
5. **Performance considerations**: `convert()` is called for every event; avoid performing time-consuming operations inside it

## Related Documentation

### Continue the Adapter Development Path

- [Adapter Core Concepts](core-concepts.md) - Overall adapter architecture
- [SendDSL in Detail](send-dsl.md) - Reverse conversion (sending direction)

### Follow the Formal Specifications

- [Event Conversion Standard](../../standards/event-conversion.md) - The formal event conversion specification
- [Session Type System](../../standards/session-types.md) - Session type mapping rules