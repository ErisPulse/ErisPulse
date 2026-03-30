# ErisPulse Sending Method Specifications

This document defines the naming, parameter specifications, and reverse conversion requirements for the sending methods of the `Send` class within the ErisPulse adapter.

## 1. Standard Method Naming

All sending methods use **PascalCase**, with the first letter capitalized.

### 1.1 Standard Sending Methods

| Method Name | Description | Parameter Type |
|-------|------|---------|
| `Text` | Send text message | `str` |
| `Image` | Send image | `bytes` \| `str` (URL/Path) |
| `Voice` | Send voice/audio | `bytes` \| `str` (URL/Path) |
| `Video` | Send video | `bytes` \| `str` (URL/Path) |
| `File` | Send file | `bytes` \| `str` (URL/Path) |
| `At` | @ user/group | `str` (user_id) |
| `Face` | Send emoji | `str` (emoji) |
| `Reply` | Reply to message | `str` (message_id) |
| `Forward` | Forward message | `str` (message_id) |
| `Markdown` | Send Markdown message | `str` |
| `HTML` | Send HTML message | `str` |
| `Card` | Send card message | `dict` |

### 1.2 Chain Modifier Methods

| Method Name | Description | Parameter Type |
|-------|------|---------|
| `At` | @ user (callable multiple times) | `str` (user_id) |
| `AtAll` | @ all members | N/A |
| `Reply` | Reply to message | `str` (message_id) |

### 1.3 Protocol Methods

| Method Name | Description | Required |
|-------|------|---------|
| `Raw_ob12` | Send OneBot12 format message segment | Yes |

**`Raw_ob12` is a required method to implement.** This is one of the adapter's core responsibilities: receiving OneBot12 standard message segments and converting them into platform native API calls. `Raw_ob12` is the unified entry point for reverse conversion (OneBot12 → Platform), ensuring modules can send messages without relying on platform-specific methods, using standard message segments directly.

**Behavior when `Raw_ob12` is not overridden:** The base class default implementation will log an **error level** log and return the standard error response format (`status: "failed"`, `retcode: 10002`), prompting adapter developers to implement this method.

### 1.4 Recommended Extension Naming Conventions

If the adapter needs to support sending raw data in non-OneBot12 formats (such as platform-specific JSON, XML, etc.), the following naming conventions are recommended:

| Recommended Method Name | Description |
|-----------|------|
| `Raw_json` | Send arbitrary JSON data |
| `Raw_xml` | Send arbitrary XML data |

**Note:** These methods are **not** default methods provided by the base class, nor are they mandatory to implement. They serve only as naming conventions; adapters may define them as needed. If an adapter does not support these formats, there is no need to define them.

**MessageBuilder:** ErisPulse provides a `MessageBuilder` tool class to conveniently construct OneBot12 message segment lists for use with `Raw_ob12`. See the [MessageBuilder](#11-messagebuilder) section for details.

## 2. Parameter Specifications Detail

### 2.1 Media Message Parameter Specifications

Media messages (`Image`, `Voice`, `Video`, `File`) support two parameter types:

#### 2.1.1 String Parameters (URL or File Path)

**Format:** `str`

**Supported Types:**
- **URL:** Network resource address (e.g., `https://example.com/image.jpg`)
- **File Path:** Local file path (e.g., `/path/to/file.jpg` or `C:\\path\\to\\file.jpg`)

**Use Cases:**
- File is already online, send URL directly
- File is on local disk, send file path
- Adapter automatically handles file upload

**Recommendation:** Prioritize using URL, if unavailable, use local file path.

**Example:**
```python
# Use URL
send.Image("https://example.com/image.jpg")

# Use local file path
send.Image("/path/to/local/image.jpg")
send.Image("C:\\path\\to\\local\\image.jpg")
```

#### 2.1.2 Binary Data Parameters

**Format:** `bytes`

**Use Cases:**
- File is already in memory (e.g., downloaded from network, read from other sources)
- Need to process before sending (e.g., image compression, format conversion)
- Avoid re-reading files

**Notes:**
- Uploading large files may consume significant memory
- It is recommended to set reasonable file size limits

**Example:**
```python
# Read from network and send
import requests
image_data = requests.get("https://example.com/image.jpg").content
send.Image(image_data)

# Read from file and send
with open("/path/to/local/image.jpg", "rb") as f:
    image_data = f.read()
send.Image(image_data)
```

#### 2.1.3 Parameter Processing Priority

When the adapter receives media message parameters, they should be processed in the following order:

1. **URL Parameter:** Send directly using the URL (some platform adapters may perform URL download before upload)
2. **File Path:** Detect if it is a local path, and if so, upload the file
3. **Binary Data:** Upload the binary data directly

**Adapter Implementation Suggestion:**
```python
def Image(self, image: Union[bytes, str]):
    if isinstance(image, str):
        # Determine if it is a URL or local path
        if image.startswith(("http://", "https://")):
            # Send URL directly
            return self._send_image_by_url(image)
        else:
            # Local path, read and upload
            with open(image, "rb") as f:
                return self._upload_image(f.read())
    elif isinstance(image, bytes):
        # Binary data, upload directly
        return self._upload_image(image)
```

### 2.2 @ User Parameter Specifications

**Method:** `At` (modifier method)

**Parameter:** `user_id` (`str`)

**Requirements:**
- `user_id` should be a string type user identifier
- `user_id` format may vary across different platforms (numbers, UUID, strings, etc.)
- Adapter is responsible for converting `user_id` to platform-specific format
- **Note:** The actual sending method call must be placed at the end.

**Example:**
```python
# @ a single user
Send.To("group", "g123").At("123456").Text("Hello")

# @ multiple users (chained calls)
send.To("group", "g123").At("123456").At("789012").Text("Hello everyone")
```

### 2.3 Reply Message Parameter Specifications

**Method:** `Reply` (modifier method)

**Parameter:** `message_id` (`str`)

**Requirements:**
- `message_id` should be a string type message identifier
- It should be the ID of a previously received message
- Some platforms may not support reply functionality; adapter should gracefully degrade

**Example:**
```python
send.To("group", "g123").Reply("msg_123456").Text("Received")
```

## 3. Platform-Specific Method Naming

**Do not** directly add platform-prefixed methods to the `Send` class. It is recommended to use generic method names or `Raw_{protocol}` methods.

**Not Recommended:**
```python
def YunhuForm(self, form_id: str):  # ❌ Not recommended
    pass

def TelegramSticker(self, sticker_id: str):  # ❌ Not recommended
    pass
```

**Recommended:**
```python
def Form(self, form_id: str):  # ✅ Generic method name
    pass

def Sticker(self, sticker_id: str):  # ✅ Generic method name
    pass

def Raw_ob12(self, message):  # ✅ Send OneBot12 format
    pass
```

**Extended Method Requirements:**
- Method names use PascalCase without a platform prefix
- Must return `asyncio.Task` object
- Must provide complete type hints and docstrings
- Parameter design should be as consistent as possible with standard methods

## 4. Parameter Naming Specifications

| Parameter Name | Description | Type |
|-------|------|------|
| `text` | Text content | `str` |
| `url` / `file` | File URL or binary data | `str` / `bytes` |
| `user_id` | User ID | `str` / `int` |
| `group_id` | Group ID | `str` / `int` |
| `message_id` | Message ID | `str` |
| `data` | Data object (e.g., card data) | `dict` |

## 5. Return Value Specifications

- **Sending Methods** (e.g., `Text`, `Image`): Must return an `asyncio.Task` object
- **Modifier Methods** (e.g., `At`, `Reply`, `AtAll`): Must return `self` to support chaining

---

## 6. Reverse Conversion Specifications (OneBot12 → Platform)

The adapter not only needs to convert platform native events to OneBot12 format (forward conversion) but also **must** provide the capability to convert OneBot12 message segments back into platform native API calls (reverse conversion). The unified entry point for reverse conversion is the `Raw_ob12` method.

### 6.1 Conversion Model

```
Forward Conversion (Receive Direction)          Reverse Conversion (Send Direction)
─────────────────────────                      ─────────────────
Platform Native Events                         OneBot12 Message Segment List
    │                                              │
    ▼                                              ▼
Converter.convert()                           Send.Raw_ob12()
    │                                              │
    ▼                                              ▼
OneBot12 Standard Events                       Platform Native API Calls
(with {platform}_raw)                           (returns standard response format)
```

**Core Symmetry:** Forward conversion preserves the original data in `{platform}_raw`, while reverse conversion accepts the OneBot12 standard format and restores it to platform calls.

### 6.2 `Raw_ob12` Implementation Specifications

`Raw_ob12` receives a OneBot12 standard message segment list and must convert it into platform native API calls.

**Method Signature:**

```python
def Raw_ob12(self, message_segments: List[Dict]) -> asyncio.Task:
    """
    Send OneBot12 standard message segments

    :param message_segments: OneBot12 message segment list
        [
            {"type": "text", "data": {"text": "Hello"}},
            {"type": "image", "data": {"file": "https://..."}},
            {"type": "mention", "data": {"user_id": "123"}},
        ]
    :return: asyncio.Task, returns standard response format after awaiting
    """
```

**Implementation Requirements:**

1. **Must handle all standard message segment types:** At least support `text`, `image`, `audio`, `video`, `file`, `mention`, `reply`
2. **Must handle platform extension message segments:** For `{platform}_xxx` type message segments, convert to corresponding platform native calls
3. **Must return standard response format:** Follow [API Response Standard](api-response.md)
4. **Unsupported message segments should be skipped and logged as warnings**; exceptions should not be thrown to cause the entire message sending to fail

### 6.3 Message Segment Conversion Rules

#### 6.3.1 Standard Message Segment Conversion

The adapter must implement the following standard message segment conversions:

| OneBot12 Segment | Conversion Requirements |
|----------------|---------|
| `text` | Directly use `data.text` |
| `image` | Handle based on `data.file` type: URL used directly, bytes uploaded, local path read then uploaded |
| `audio` | Same logic as image |
| `video` | Same logic as image |
| `file` | Same logic as image, note `data.filename` |
| `mention` | Convert to platform's @user mechanism (e.g., Telegram's `entities`, Yunhu's `at_uid`) |
| `reply` | Convert to platform's reply reference mechanism |
| `face` | Convert to platform's emoji sending mechanism, skip if not supported |
| `location` | Convert to platform's location sending mechanism, skip if not supported |

#### 6.3.2 Platform Extension Message Segment Conversion

For message segments with platform prefixes, the adapter should identify and convert:

```python
def _convert_ob12_segments(self, segments: List[Dict]) -> Any:
    """Convert OneBot12 message segments to platform native format"""
    platform_prefix = f"{self._platform_name}_"
    
    for segment in segments:
        seg_type = segment["type"]
        seg_data = segment["data"]
        
        if seg_type.startswith(platform_prefix):
            # Platform extension segment -> Platform native call
            self._handle_platform_segment(seg_type, seg_data)
        elif seg_type in self._standard_segment_handlers:
            # Standard segment -> Platform equivalent operation
            self._standard_segment_handlers[seg_type](seg_data)
        else:
            # Unknown segment -> Log warning and skip
            logger.warning(f"Unsupported message segment type: {seg_type}")
```

#### 6.3.3 Composite Message Segment Processing

A single message may contain multiple message segments, and the adapter needs to correctly handle composite messages:

```python
# Module sends a message containing text + image + @user
await send.Raw_ob12([
    {"type": "mention", "data": {"user_id": "123"}},
    {"type": "text", "data": {"text": "Hello"}},
    {"type": "image", "data": {"file": "https://example.com/img.jpg"}}
])
```

**Processing Strategy:**
- **Prioritize Merging:** If the platform supports combining text, image, @user, etc., in a single message, merge and send
- **Fall back to Splitting:** If the platform does not support merging, split into multiple messages in order
- **Maintain Order:** The order of message segment sending should be consistent with the list order

### 6.4 Relationship between `Raw_ob12` and Standard Methods

Standard sending methods in the adapter (e.g., `Text`, `Image`) should delegate internally to `Raw_ob12`, rather than implementing conversion logic independently:

```python
class Send(SendDSL):
    def Raw_ob12(self, message_segments: List[Dict]) -> asyncio.Task:
        """Core implementation: OneBot12 message segments -> Platform API"""
        return asyncio.create_task(self._send_ob12(message_segments))
    
    def Text(self, text: str) -> asyncio.Task:
        """Standard method, delegate to Raw_ob12"""
        return self.Raw_ob12([
            {"type": "text", "data": {"text": text}}
        ])
    
    def Image(self, image: Union[str, bytes]) -> asyncio.Task:
        """Standard method, delegate to Raw_ob12"""
        return self.Raw_ob12([
            {"type": "image", "data": {"file": image}}
        ])
```

**Benefits:**
- Conversion logic is centralized in `Raw_ob12`, reducing duplicate code
- Standard methods and `Raw_ob12` behave consistently
- Modules get the same result whether using `Text()` or `Raw_ob12()`

### 6.5 Implementation Example

```python
class YunhuSend(SendDSL):
    """Yunhu platform Send implementation"""
    
    def Raw_ob12(self, message_segments: list) -> asyncio.Task:
        """OneBot12 message segments -> Yunhu API call"""
        return asyncio.create_task(self._do_send(message_segments))
    
    async def _do_send(self, segments: list) -> dict:
        """Actual sending logic"""
        # 1. Parse modifier state
        at_users = self._at_users or []
        reply_to = self._reply_to
        at_all = self._at_all
        
        # 2. Convert message segments
        yunhu_elements = []
        for seg in segments:
            seg_type = seg["type"]
            seg_data = seg["data"]
            
            if seg_type == "text":
                yunhu_elements.append({"type": "text", "content": seg_data["text"]})
            elif seg_type == "image":
                yunhu_elements.append({"type": "image", "url": seg_data["file"]})
            elif seg_type == "mention":
                at_users.append(seg_data["user_id"])
            elif seg_type == "reply":
                reply_to = seg_data["message_id"]
            elif seg_type == "yunhu_form":
                # Platform extension message segment
                yunhu_elements.append({"type": "form", "form_id": seg_data["form_id"]})
            else:
                logger.warning(f"Yunhu unsupported message segment: {seg_type}")
        
        # 3. Call Yunhu API
        response = await self._call_yunhu_api(yunhu_elements, at_users, reply_to, at_all)
        
        # 4. Return standard response format
        return {
            "status": "ok" if response["code"] == 0 else "failed",
            "retcode": response["code"],
            "data": {"message_id": response.get("msg_id", ""), "time": int(time.time())},
            "message_id": response.get("msg_id", ""),
            "message": "",
            "yunhu_raw": response
        }
```

---

## 7. Method Discovery

Module developers can query the sending methods supported by the adapter via the API:

```python
from ErisPulse import adapter

# List all sending methods
methods = adapter.list_sends("myplatform")
# ["Batch", "Form", "Image", "Recall", "Sticker", "Text", ...]

# View method details
info = adapter.send_info("myplatform", "Form")
# {
#     "name": "Form",
#     "parameters": [{"name": "form_id", "type": "str", ...}],
#     "return_type": "Awaitable[Any]",
#     "docstring": "Send Yunhu form"
# }
```

---

## 8. Registered Sending Method Extensions

| Platform | Method Name | Description |
|------|--------|------|
| onebot12 | `Mention` | @ user (OneBot12 style) |
| onebot12 | `Sticker` | Send sticker |
| onebot12 | `Location` | Send location |
| onebot12 | `Recall` | Recall message |
| onebot12 | `Edit` | Edit message |
| onebot12 | `Batch` | Batch send |

> **Note:** Sending methods do not add platform prefixes; methods with the same name on different platforms can have different implementations.

---

## 9. Adapter Implementation Checklist

### Sending Methods
- [ ] Standard methods (`Text`, `Image`, etc.) implemented
- [ ] Return values are all `asyncio.Task`
- [ ] Modifier methods (`At`, `Reply`, `AtAll`) return `self`
- [ ] Platform extension methods use PascalCase, no platform prefix
- [ ] All methods have complete type hints and docstrings

### Reverse Conversion
- [ ] `Raw_ob12` **implemented** (Mandatory, cannot skip)
- [ ] `Raw_ob12` can handle all standard message segments (`text`, `image`, `audio`, `video`, `file`, `mention`, `reply`)
- [ ] `Raw_ob12` can handle platform extension message segments (`{platform}_xxx` types)
- [ ] Standard sending methods (`Text`, `Image`, etc.) delegate internally to `Raw_ob12`, rather than implementing conversion logic independently
- [ ] Unsupported message segments are skipped and logged as warnings, no exceptions thrown
- [ ] Composite message segments handled correctly (merged or split in order)

---

## 11. MessageBuilder

`MessageBuilder` is a message segment building tool provided by ErisPulse, used with `Raw_ob12` to simplify the construction of OneBot12 message segments.

### 11.1 Import

```python
from ErisPulse.Core import MessageBuilder
# or
from ErisPulse.Core.Event import MessageBuilder
```

### 11.2 Chaining Calls to Build

```python
# Build a message containing text, image, and @user
segments = (
    MessageBuilder()
    .mention("123456")
    .text("Hello, take a look at this picture")
    .image("https://example.com/img.jpg")
    .reply("msg_789")
    .build()
)

# Send
await adapter.Send.To("group", "456").Raw_ob12(segments)
```

### 11.3 Quick Build for Single Segment

```python
# Quickly build a single message segment (returns list[dict], can be passed directly to Raw_ob12)
await adapter.Send.To("user", "123").Raw_ob12(MessageBuilder.text("Hello"))
await adapter.Send.To("group", "456").Raw_ob12(MessageBuilder.image("https://..."))
await adapter.Send.To("group", "456").Raw_ob12(MessageBuilder.mention("123"))
await adapter.Send.To("group", "456").Raw_ob12(MessageBuilder.reply("msg_id"))
await adapter.Send.To("group", "456").Raw_ob12(MessageBuilder.at_all())
```

### 11.4 Use with Event.reply_ob12

```python
from ErisPulse.Core import MessageBuilder

@message()
async def handle(event: Event):
    await event.reply_ob12(
        MessageBuilder()
        .mention(event.get_user_id())
        .text("Received your message")
        .build()
    )
```

### 11.5 Supported Message Segment Methods

| Method | Description | data fields |
|------|----------|----------|
| `text(text)` | Text | `text` |
| `image(file)` | Image | `file` |
| `audio(file)` | Audio | `file` |
| `video(file)` | Video | `file` |
| `file(file, filename=None)` | File | `file`, `filename` (optional) |
| `mention(user_id, user_name=None)` | @ user | `user_id`, `user_name` (optional) |
| `at(user_id, user_name=None)` | @ user (alias of `mention`) | Same as `mention` |
| `reply(message_id)` | Reply | `message_id` |
| `at_all()` | @ all members | `{}` |
| `custom(type, data)` | Custom/Platform extension | Custom |

### 11.6 Utility Methods

```python
builder = MessageBuilder().text("Base content")

# Copy (deep copy)
msg1 = builder.copy().image("img1").build()
msg2 = builder.copy().image("img2").build()

# Clear
builder.clear().text("New content").build()

# Check if empty
if builder:
    print(f"Contains {len(builder)} message segments")
```

---

## 12. Related Documents

- [Event Conversion Standard](event-conversion.md) - Complete event conversion specifications, extension naming, and message segment standards
- [API Response Standard](api-response.md) - Adapter API response format standards
- [Session Type Standard](session-types.md) - Session type definitions and mapping relationships