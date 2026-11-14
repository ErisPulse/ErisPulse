# ErisPulse Session Type Standard

> [!TIP]
> **When to read this**: When mapping platform-native session types to standard types (private/group/channel/guild/thread) in an adapter, or when unsure what target type to pass to `Send.To()` in a module, or to understand the automatic conversion of `event.reply()` — refer to this document. Skip it otherwise.

This document defines the session type standard supported by ErisPulse, covering receive event types and send target types.

## 1. Core Concepts

### 1.1 Receive Types && Send Types

ErisPulse distinguishes between two session types:

- **Receive Type**: The `detail_type` field of received events
- **Send Type**: The target type of the `Send.To()` method when sending messages

### 1.2 Type Mapping Relationships

```
Receive Type (detail_type)     Send Type (Send.To)
─────────────────        ────────────────
private                 →        user
group                   →        group
channel                 →        channel
guild                   →        guild
thread                  →        thread
user                    →        user
```

**Key Points**:
- `private` is the receive-time type; the standard send type is `user`
- `group`, `channel`, `guild`, and `thread` use the same type for both receiving and sending
- **Recommended path**: Use `event.reply()` directly — it automatically completes type conversion and target inference, with no manual handling needed (the `private` → `user` automatic conversion happens here)
- **For manual sending**: Pass the send type directly (e.g., `Send.To("user", ...)`); manually passing a receive type such as `Send.To("private", ...)` can still be auto-converted, but is not recommended (see §6.1)

## 2. Standard Session Types

### 2.1 OneBot12 Standard Types

#### private
- **Receive Type**: `private`
- **Send Type**: `user`
- **Description**: One-to-one private chat messages
- **ID Field**: `user_id`
- **Applicable Platforms**: All platforms supporting private chats

#### group
- **Receive Type**: `group`
- **Send Type**: `group`
- **Description**: Group chat messages, including various forms of groups (e.g., Telegram supergroup)
- **ID Field**: `group_id`
- **Applicable Platforms**: All platforms supporting group chats

#### user
- **Receive Type**: `user`
- **Send Type**: `user`
- **Description**: User type; some platforms (e.g., Telegram) represent private chats as user instead of private
- **ID Field**: `user_id`
- **Applicable Platforms**: Telegram and similar platforms

### 2.2 ErisPulse Extension Types

#### channel
- **Receive Type**: `channel`
- **Send Type**: `channel`
- **Description**: Channel messages, supporting broadcast-style messages to multiple users
- **ID Field**: `channel_id`
- **Applicable Platforms**: Discord, Telegram, Line, etc.

#### guild
- **Receive Type**: `guild`
- **Send Type**: `guild`
- **Description**: Server/community messages, typically used for Discord Guild-level events
- **ID Field**: `guild_id`
- **Applicable Platforms**: Discord, etc.

#### thread
- **Receive Type**: `thread`
- **Send Type**: `thread`
- **Description**: Thread/sub-channel messages, used for sub-discussion areas within a community
- **ID Field**: `thread_id`
- **Applicable Platforms**: Discord Threads, Telegram Topics, etc.

## 3. Platform Type Mapping

### 3.1 Mapping Principles

Adapters are responsible for mapping platform-native types to ErisPulse standard types:

```
Platform Native Type → ErisPulse Standard Type → Send Type
```

### 3.2 Common Platform Mapping Examples

#### Telegram
```
Telegram Type          ErisPulse Receive Type    Send Type
─────────────────      ────────────────       ───────────
private                private                 user
group                  group                   group
supergroup             group                   group  # Mapped to group
channel                channel                 channel
```

#### Discord
```
Discord Type          ErisPulse Receive Type    Send Type
─────────────────      ────────────────       ───────────
Direct Message         private                user
Text Channel           channel                channel
Guild                  guild                  guild
Thread                 thread                 thread
```

#### OneBot11
```
OneBot11 Type        ErisPulse Receive Type    Send Type
─────────────────      ────────────────       ───────────
private                private                user
group                  group                  group
discuss                group                  group  # Mapped to group
```

## 4. Custom Type Extension

### 4.1 Registering Custom Types

Adapters can register custom session types:

```python
from ErisPulse.Core.Event import register_custom_type

# Register a custom type
register_custom_type(
    receive_type="my_custom_type",
    send_type="custom",
    id_field="custom_id",
    platform="MyPlatform"
)
```

### 4.2 Using Custom Types

After registration, the system automatically handles conversion and inference for that type:

```python
# Automatic inference
receive_type = infer_receive_type(event, platform="MyPlatform")
# Returns: "my_custom_type"

# Convert to send type
send_type = convert_to_send_type(receive_type, platform="MyPlatform")
# Returns: "custom"

# Get the corresponding ID
target_id = get_target_id(event, platform="MyPlatform")
# Returns: event["custom_id"]
```

### 4.3 Unregistering Custom Types

```python
from ErisPulse.Core.Event import unregister_custom_type

unregister_custom_type("my_custom_type", platform="MyPlatform")
```

## 5. Automatic Type Inference

When an event has no explicit `detail_type` field, the system automatically infers the type based on existing ID fields:

> [!NOTE]
> **2.7.0+ Behavior Change**: `detail_type` is adopted directly only when it is a **known session type** (standard or custom). The `detail_type` of notice/request events (such as `group_member_increase` and `friend_increase`) are **semantic subtypes** rather than session types, so the correct session type is instead inferred from ID fields.

### 5.1 Inference Priority

```
Priority (high to low):
1. group_id     → group
2. channel_id   → channel
3. guild_id     → guild
4. thread_id    → thread
5. user_id      → private
```

### 5.2 Usage Examples

```python
# Event has only group_id
event = {"group_id": "123", "user_id": "456"}
receive_type = infer_receive_type(event)
# Returns: "group" (group_id takes priority)

# Event has only user_id
event = {"user_id": "123"}
receive_type = infer_receive_type(event)
# Returns: "private"

# A notice event's detail_type is a semantic subtype; 2.7.0+ infers from ID fields
event = {"type": "notice", "detail_type": "group_member_increase", "group_id": "123"}
receive_type = infer_receive_type(event)
# Returns: "group" (not "group_member_increase")
```

## 6. API Usage Examples

### 6.1 Sending Messages

```python
from ErisPulse import adapter

# Send to a user
await adapter.myplatform.Send.To("user", "123").Text("Hello")

# Send to a group
await adapter.myplatform.Send.To("group", "456").Text("Hello")

# Automatic private → user conversion: manually passing a receive type is not recommended (may cause compatibility issues)
await adapter.myplatform.Send.To("private", "789").Text("Hello")
# Internally auto-converted to: Send.To("user", "789")
# Recommended practice: use the send type user directly for manual sending, or use event.reply() to complete the conversion automatically (see 6.2)
```

### 6.2 Event Reply

```python
from ErisPulse.Core.Event import Event

# Event.reply() automatically handles type conversion (recommended path)
await event.reply("Reply content")
# Internally uses the correct send type automatically (conversions like private → user happen here)
```

### 6.3 Command Handling

```python
from ErisPulse.Core.Event import command

@command(name="test")
async def handle_test(event):
    # The system automatically handles session types
    # No need to manually check whether it is group_id or user_id
    await event.reply("Command executed successfully")
```

## 7. Core API Reference

### 7.1 Type Conversion

```python
from ErisPulse.Core.Event import convert_to_send_type, convert_to_receive_type

# Receive type → Send type
convert_to_send_type("private")  # → "user"
convert_to_send_type("group")    # → "group"

# Send type → Receive type
convert_to_receive_type("user")   # → "private"
convert_to_receive_type("group")  # → "group"
```

### 7.2 ID Field Query

```python
from ErisPulse.Core.Event import get_id_field, get_receive_type

get_id_field("group")    # → "group_id"
get_id_field("private")  # → "user_id"

get_receive_type("group_id")  # → "group"
get_receive_type("user_id")   # → "private"
```

### 7.3 One-Step Send Information Retrieval

```python
from ErisPulse.Core.Event import get_send_type_and_target_id

event = {"detail_type": "private", "user_id": "123"}
send_type, target_id = get_send_type_and_target_id(event)
# send_type = "user", target_id = "123"

# Use directly with Send.To()
await adapter.Send.To(send_type, target_id).Text("Hello")
```

### 7.4 Getting the Target ID

```python
from ErisPulse.Core.Event import get_target_id

event = {"detail_type": "group", "group_id": "456"}
get_target_id(event)  # → "456"
```

## 8. Utility Methods

```python
from ErisPulse.Core.Event import (
    is_standard_type,
    is_valid_send_type,
    get_standard_types,
    get_send_types,
    clear_custom_types,
)

is_standard_type("private")     # True
is_standard_type("custom_type") # False

is_valid_send_type("user")      # True
is_valid_send_type("invalid")   # False

get_standard_types()  # {"private", "group", "channel", "guild", "thread", "user"}
get_send_types()      # {"user", "group", "channel", "guild", "thread"}

clear_custom_types()                # Clear all
clear_custom_types(platform="discord")  # Clear only those for the specified platform
```

## 9. Best Practices

### 7.1 Adapter Developers

1. **Use standard mappings**: Map to standard types whenever possible, rather than creating new types
2. **Convert correctly**: Ensure the mapping relationship between receive and send types is correct
3. **Preserve original data**: Keep original event types in `{platform}_raw`
4. **Document it**: Describe the type mapping relationships in the adapter documentation

### 7.2 Module Developers

1. **Use utility methods**: Use utility methods such as `get_send_type_and_target_id()`
2. **Avoid hardcoding**: Do not write code like `if group_id else "private"`
3. **Consider all types**: Code should support all standard types, not just private/group
4. **Design flexibly**: Use event wrapper methods instead of accessing fields directly

### 7.3 Type Inference

- **Prefer detail_type**: If an explicit field exists, do not perform inference
- **Use inference sensibly**: Only use it when there is no explicit type
- **Mind the priority**: Understand the inference priority to avoid unexpected results

## 10. FAQ

### Q1: Why is private converted to user when sending?

A: This is required by the OneBot12 standard. `private` is a receive-time concept; `user` is more semantically appropriate when sending.

### Q2: How do I support new session types?

A: Register custom types via `register_custom_type()`, or directly use standard types such as `channel` and `guild`.

### Q3: What if an event has no detail_type?

A: The system automatically infers it based on existing ID fields. Priority: group > channel > guild > thread > user.

### Q4: How should adapters map Telegram supergroup?

A: In the adapter's conversion logic, map `supergroup` to the standard `group` type.

### Q5: How are special platforms like email handled?

A: For non-universal or platform-specific types, use `{platform}_raw` and `{platform}_raw_type` to preserve the original data, and let the adapter handle them itself.

## 11. Related Documentation

**Adapter side (mapping and conversion)**:
- [Event Conversion Standard](event-conversion.md) - Complete event conversion specification
- [Send Method Specification](send-method-spec.md) - Send class method naming and parameter specifications
- [Adapter Development Guide](../developer-guide/adapters/) - Complete guide to adapter development

**Module side (avoiding manual type conversion)**:
- Use `event.reply()` to automatically complete type conversion and target inference; see [Event Wrapper Class Explained](../developer-guide/modules/event-wrapper.md) for details