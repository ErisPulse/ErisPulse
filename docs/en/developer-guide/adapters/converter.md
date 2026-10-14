# Event Converter Implementation Guide

> [!TIP]
> **When to read this**: Required reading within the adapter development path (Event Converter). Skip if not needed, as it does not affect the use of other features.

The Event Converter (Converter) is one of the core components of the adapter, responsible for converting native platform events into ErisPulse's unified OneBot12 standard event format.

## Converter Responsibilities

```
Platform-native events ──→ Converter.convert() ──→ OneBot12 standard events
```

The `Converter` is responsible only for **forward conversion** (inbound direction), which means converting platform-native event data into the OneBot12 standard format. Reverse conversion (outbound direction) is handled by the `Send.Raw_ob12()` method.

### Core Principles

1. **Lossless Conversion**: Original data must be fully preserved in the `{platform}_raw` field
2. **Standard Compatibility**: Converted events must conform to the OneBot12 standard format
3. **Platform Extensions**: Platform-specific data is stored in fields prefixed with `{platform}_`

## BaseConverter Base Class (Recommended)

Starting from version 2.7.0, the framework provides the `BaseConverter` base class (`ErisPulse.Core.Bases`), which encapsulates the **common field construction** and **common message segment utilities** for OneBot12 events. This allows converters to focus solely on type mapping:

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

The `build_base_event()` method already fills in the following common fields:

| Field | Source |
|------|------|
| `id` | `raw_event["event_id"]`, a UUID is generated if missing |
| `time` | `raw_event["timestamp"]`, the current time is used if missing |
| `platform` | Provided via the `platform` argument during initialization |
| `self` | `{"platform": ..., "user_id": raw_event["bot_id"]}` |
| `{platform}_raw` | The original event (satisfying the "lossless conversion" principle) |
| `{platform}_raw_type` | The original event type |

Common message segment utility methods (all are static methods, directly reusable):

```python
converter.text("hi")          # {"type": "text", "data": {"text": "hi"}}
converter.at("123456")        # {"type": "at", "data": {"user_id": "123456"}}
converter.image("file.png")   # {"type": "image", "data": {"file": "file.png"}}
```

> When implementing manually, the construction of common fields in `build_base_event` is boilerplate code that must be repeatedly written. Using `BaseConverter` eliminates this part and naturally satisfies "lossless conversion" (the original event is always included in `{platform}_raw`).

## convert() Method

### Method Signature

```python
def convert(self, raw_event: dict) -> dict:
    """
    Converts a platform-native event into OneBot12 standard format

    :param raw_event: Platform-native event data
    :return: Event dictionary in OneBot12 standard format
    """
    pass
```

### Return Value Structure

The converted event dictionary should include the following standard fields:

```python
{
    "id": "Unique event ID",
    "time": 1234567890,           # Unix timestamp (seconds)
    "type": "message",             # Event type
    "detail_type": "private",      # Detailed type
    "platform": "myplatform",      # Platform name
    "self": {
        "platform": "myplatform",
        "user_id": "bot_user_id"
    },

    # Message event fields
    "user_id": "sender_id",
    "message": [...],              # OneBot12 message segment list
    "alt_message": "Plain text content",

    # Must retain original data
    "myplatform_raw": { ... },     # Complete platform-native event data
    "myplatform_raw_type": "Native event type name",
}
```

## Required Field Mapping

### Common Fields (All Event Types)

| OB12 Field | Type | Description |
|------------|------|-------------|
| `id` | str | Unique identifier for the event |
| `time` | int | Unix timestamp (seconds) |
| `type` | str | Event type: `message` / `notice` / `request` / `meta` |
| `detail_type` | str | Detailed type: `private` / `group` / `friend` etc. |
| `platform` | str | Platform name, consistent with the adapter registration name |
| `self` | dict | Bot information: `{"platform": "...", "user_id": "..."}` |

### Additional Fields for Message Events

| OB12 Field | Type | Description |
|------------|------|-------------|
| `user_id` | str | Sender ID |
| `message` | list[dict] | OneBot12 message segment list |
| `alt_message` | str | Plain text alternative content |

### Additional Fields for Notice Events

| OB12 Field | Type | Description |
|------------|------|-------------|
| `user_id` | str | Relevant user ID |
| `operator_id` | str | Operator ID (e.g., group member changes) |

## Message Segment Conversion

The OneBot12 specification defines the following message segment types:

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

# @Mention
{"type": "mention", "data": {"user_id": "123"}}

# @Everyone
{"type": "mention_all", "data": {}}

# Reply
{"type": "reply", "data": {"message_id": "msg_123"}}
```

If a platform does not support a particular message segment type, it can omit that segment or convert it to the closest standard type.

## Platform Extension Fields

Platform-specific data should be stored with a `{platform}_` prefix to avoid conflicts with standard fields:

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
    "myplatform_group_name": "Group Name",
    "myplatform_sender_role": "admin",
}
```

> **Important**: The `{platform}_raw` field is required, as ErisPulse's event system and modules may depend on it to access raw platform data.

## Complete Example

Here is a complete implementation of a Converter:

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

## Rich Media Message Conversion Examples

Platform-specific messages typically contain rich media content such as images, @mentions, and replies. Below is an example of `_convert_message_segments` handling various message types:

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

### 1. Missing `{platform}_raw` Field

This is the most common mistake. Missing the raw data field prevents the module from accessing platform-specific information.

```python
base_event["myplatform_raw"] = raw_event        # Required!
base_event["myplatform_raw_type"] = event_type   # Required!
```

### 2. Incorrect Timestamp Format

The OneBot12 standard requires the `time` field to be a Unix second-level timestamp (integer). If your platform returns a millisecond timestamp or an ISO-formatted string, you need to convert it:

```python
import time

# Milliseconds → Seconds
"time": raw_event.get("timestamp", 0) // 1000

# ISO String → Seconds
"time": int(time.mktime(time.strptime(raw_event["created_at"], "%Y-%m-%dT%H:%M:%S")))
```

### 3. Missing `self` Field

The `self` field contains information about the bot itself, with `user_id` being the bot's account ID. This field is crucial in multi-Bot scenarios:

```python
"self": {
    "platform": self.platform,
    "user_id": raw_event.get("bot_id", ""),   # The bot's own ID
}
```

### 4. Use of Non-standard `detail_type` Values

The `detail_type` must use values defined by the OneBot12 standard, such as `private`, `group`, `friend_increase`, `group_member_increase`, etc. Do not use platform-specific naming.

### 5. Round-trip Consistency

Ensure that the message segment types generated by the Converter correspond to the methods supported by the Send end. For example, if the Converter converts the platform's image message to `{"type": "image", ...}`, then the `Image()` method on the Send end must be able to handle image sending.

## Best Practices

1. **Always retain the original data**: The `{platform}_raw` field must not be omitted.
2. **Use standard message segments**: Try to convert platform-specific messages into OneBot12 standard message segments.
3. **Set `detail_type` appropriately**: Use standard types (`private`/`group`/`channel`, etc.), and do not define custom types.
4. **Handle edge cases**: The original event may lack certain fields; use `.get()` and provide reasonable default values.
5. **Performance considerations**: The `convert()` method is called on each event, so avoid performing time-consuming operations within it.

## Related Documents

- [Adapter Core Concepts](core-concepts.md) - Adapter overall architecture
- [SendDSL Explained](send-dsl.md) - Reverse transformation (send direction)
- [Event Conversion Standard](../../standards/event-conversion.md) - Formal event conversion specification
- [Session Type System](../../standards/session-types.md) - Session type mapping rules