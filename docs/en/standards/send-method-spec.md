# ErisPulse Send Method Specification

This document defines the naming conventions, parameter specifications, and reverse conversion requirements for the `Send` class methods in the ErisPulse adapter.

## 0. Keyword Conventions

The keywords **MUST**, **SHOULD**, and **MAY** in this document are interpreted as follows (referencing RFC 2119):

| Keyword | Meaning | Consequence of Violation |
|--------|------|---------|
| **MUST** | Mandatory requirement; framework behavior or cross-platform consistency depends on it | Adapter is considered non-compliant with the standard; module code may not work |
| **SHOULD** | Strongly recommended; unless there is a compelling reason, follow it | When deviating, the reason and alternative behavior must be explained in the adapter documentation |
| **MAY** | Optional; decide based on platform capabilities | None |

## 1. Standard Method Naming

All send methods use **PascalCase** (capitalized first letter).

### 1.1 Standard Send Methods

| Method Name | Description | Parameter Type | Implementation Requirement |
|-------|------|---------|---------|
| `Text` | Send text message | `str` | MUST |
| `Image` | Send image | `str` \| `bytes` | MUST (built-in in base class, see §6.4) |
| `Voice` | Send voice | `str` \| `bytes` | MUST (built-in in base class; if platform does not support voice, downgrade per §2.1.5) |
| `Video` | Send video | `str` \| `bytes` | MUST (built-in in base class; if platform does not support video, downgrade per §2.1.5) |
| `File` | Send file | `str` \| `bytes`, `filename: str \| None = None` | MUST (built-in in base class) |
| `At` | @ user/group | `str` (user_id) | Modifier method, optional |
| `Face` | Send emoji | `str` (emoji) | MAY |
| `Reply` | Reply to message | `str` (message_id) | Modifier method, optional |
| `Forward` | Forward message | `str` (message_id) | MAY |
| `Markdown` | Send Markdown message | `str` | MAY |
| `HTML` | Send HTML message | `str` | MAY |
| `Card` | Send card message | `dict` | MAY |

> Standard methods (`Text`/`Image`/`Voice`/`Video`/`File`) are built-in in the base class `SendDSL` and default to delegating to `Raw_ob12`. Adapters **do not need to re-implement** these methods to obtain type signatures; only override individual methods when the platform requires special logic (see §6.4).

### 1.2 Chained Modifier Methods

| Method Name | Description | Parameter Type |
|-------|------|---------|
| `At` | @ user (can be called multiple times) | `str` (user_id) |
| `AtAll` | @ all members | None |
| `Reply` | Reply to message | `str` (message_id) |

### 1.3 Protocol Methods

| Method Name | Description | Required? |
|-------|------|---------|
| `Raw_ob12` | Send OneBot12 formatted message segment | MUST |

**`Raw_ob12` is a required method**. This is one of the adapter's core responsibilities: receiving OneBot12 standard message segments and converting them into native platform API calls. `Raw_ob12` is the unified entry point for reverse conversion (OneBot12 → platform), ensuring that modules can send messages directly using standard message segments without relying on platform-specific methods.

**Behavior when `Raw_ob12` is not overridden**: The default base class implementation will log an **error-level** message and return a standard error response format (`status: "failed"`, `retcode: 10002`), prompting adapter developers to implement this method.

### 1.4 Recommended Extension Naming Convention

If adapters need to support sending non-OneBot12 formatted raw data (such as platform-specific JSON, XML, etc.), the following naming conventions are recommended:

| Recommended Method Name | Description |
|-----------|------|
| `Raw_json` | Send arbitrary JSON data |
| `Raw_xml` | Send arbitrary XML data |

**Note**: These methods are **not** provided by the base class and are not mandatory. They are only naming conventions, and adapters can define them as needed. If an adapter does not support these formats, there is no need to define them.

**Message Builder (`MessageBuilder`)**: ErisPulse provides the `MessageBuilder` utility class to conveniently build OneBot12 message segment lists, used in conjunction with `Raw_ob12`. See the [Message Builder](#11-message-builder-messagebuilder) section.

## 2. Detailed Parameter Specification

### 2.1 Media Message Sending Protocol (`Image` / `Voice` / `Video` / `File`)

This section is the **unified protocol standard** for media sending: modules use the same code to call the four media methods, and adapters are responsible for converting the various forms of the `file` parameter into native platform upload/send behavior.

#### 2.1.1 Valid Forms of the `file` Parameter

| Form | Example | Adapter Requirement |
|------|------|-----------|
| HTTP(S) URL | `https://example.com/image.jpg` | **MUST** accept |
| Local file path | `/path/to/file.jpg`, `C:\path\to\file.jpg` | **MUST** accept |
| Binary data | `b"\x89PNG..."` | **MUST** accept |
| `file://` URI | `file:///path/to/file.jpg` | **SHOULD** accept (can be forwarded as a local path) |
| Base64 string / Data URI | `iVBORw0KGgo=...`, `data:image/png;base64,...` | **SHOULD** accept (compatible with OneBot12 ecosystem convention) |

> Adapters **must** behave consistently across the three mandatory forms—modules receive the same message regardless of whether they pass a URL, path, or bytes. When the platform cannot directly use a certain form (e.g., the platform API does not support referencing external URLs), the adapter should download/read and then upload it, **not** require the module to retry with a different form.

#### 2.1.2 Form Determination Order

When implementing media parameter handling, adapters **should** follow this order to determine the form:

1. `bytes` type → Upload directly
2. String starting with `http://` or `https://` → Process as URL (reference directly or download and upload, depending on platform capability)
3. String starting with `file://` → Strip the prefix and process as a local path
4. Other strings → Process as a local path (read and upload if it exists; return standard error response if it does not)

```python
def _resolve_media(self, file: "str | bytes") -> bytes:
    """Form determination and normalization (example)"""
    if isinstance(file, (bytes, bytearray)):
        return bytes(file)
    if file.startswith(("http://", "https://")):
        return self._download(file)          # Download if platform cannot reference URL
    if file.startswith("file://"):
        file = file[len("file://"):]
    with open(file, "rb") as f:              # Local path
        return f.read()
```

#### 2.1.3 File Name Semantics for `File`

`File` method signature: `File(file, filename=None)` (`filename` is optional, built-in in base class).

**File name derivation order** (adapter generates this when `filename` is not explicitly provided):

1. Explicit `filename` parameter (highest priority)
2. URL's basename (e.g., `https://host/a/b/report.pdf` → `report.pdf`, query string stripped)
3. Local path's basename (e.g., `/tmp/data/backup.zip` → `backup.zip`)
4. Platform default generation (e.g., `file_{timestamp}`; **should** retain the real extension—the extension affects platform-side type recognition and preview behavior)

> `Image` / `Voice` / `Video` can also accept `filename` (passed via message segment `data.filename`), but only `File`'s filename has cross-platform semantic guarantees.

#### 2.1.4 Declaration of Platform Limitations

Each platform has different constraints on media size, format (MIME), duration (audio/video), etc. Adapters **should**:

- Declare supported media types and limitation ranges in the adapter documentation
- Return **standard error response** for over-limit or unsupported input (`status: "failed"`; `retcode` uses `10002` or platform-specific error code, `message` explains the reason); **do not** throw exceptions to interrupt module logic

#### 2.1.5 Capability Degradation Hierarchy

When a platform does not support a certain media **type**, follow this degradation hierarchy (adhering to the principle of "capability degradation without error reporting"):

| Scenario | Degradation Behavior |
|------|---------|
| `Voice` does not support voice messages | **Should** send as `File` (or platform-adjacent form); return `retcode=10002` if unable to express |
| `Video` does not support video messages | Same as above |
| Media type completely unsupported (no file capability) | Return `retcode=10002`, `message` indicates unsupported data type |
| Form not supported (e.g., cannot handle base64) | Return `retcode=10002`, **can** include a message suggesting the module switch to URL/bytes |

**Prohibited actions**: Silent drop (no return), throw exceptions, or require the module to write platform-specific handling code.

### 2.2 @ User Parameter Specification

**Method:** `At` (modifier method)

**Parameter:** `user_id` (`str`)

**Requirements:**
- `user_id` should be a string-type user identifier
- Different platforms may have different `user_id` formats (numbers, UUIDs, strings, etc.)
- The adapter is responsible for converting `user_id` into the platform-specific format
- Note that the actual send method call should be placed at the last position

**Example:**
```python
# Single @ user
Send.To("group", "g123").At("123456").Text("Hello")

# Multiple @ users (chained calls)
send.To("group", "g123").At("123456").At("789012").Text("Hello everyone")
```

### 2.3 Reply Message Parameter Specification

**Method:** `Reply` (modifier method)

**Parameter:** `message_id` (`str`)

**Requirements:**
- `message_id` should be a string-type message identifier
- Should be the ID of a previously received message
- Some platforms may not support reply functionality; adapters should gracefully degrade

**Example:**
```python
send.To("group", "g123").Reply("msg_123456").Text("Received")
```

### 2.4 Merge Forward Capability (`MergeForward`, Optional)

`MergeForward(nodes)` is an **optional capability method**: it packages multiple contents into a "merged forward / rich text fold" format for sending, and the adapter decides the best presentation based on platform capability. This differs from §1.1's `Forward(from_chat_id, message_id)` (forwarding **existing** messages), and both exist in parallel.

> **Standard background**: OneBot12 core standard does not have a node message segment, nor does it have a merge forward API—“message node” is a OneBot v11 ecosystem (go-cqhttp extension) implementation layer concept, and v12 has delegated such platform-specific capabilities to the extension mechanism. ErisPulse's landing approach is the equivalent of the extension mechanism: **no new standard message segments, but optional capability methods + `list_sends` runtime detection**—adapters that implement `MergeForward` automatically gain the capability, and those that do not implement it automatically fall back to plain text, with zero module changes.

**Method signature:**

```python
def MergeForward(self, nodes: List[Dict]) -> asyncio.Task:
    """
    Send merged forward / rich text fold message

    :param nodes: Array of merged forward nodes (go-cqhttp OneBot v11 node format extension):
        [
            {
                "type": "node",
                "data": {
                    "user_id": "10000",     # ID for display
                    "nickname": "QvQChat",  # Display name for sender
                    "content": [            # Array of message segments, currently text segments
                        {"type": "text", "data": {"text": "【1/3】Title\nBody…"}}
                    ],
                },
            },
        ]
    :return: asyncio.Task, await returns standard response format
    """
```

**Implementation requirements:**

1. **Platform has native merge forward** (OneBot11 system): **Must** call the protocol-specific endpoint
   (`send_group_forward_msg` / `send_private_forward_msg`)—NapCat and similar implementations will reject
   `send_msg` carrying node segments (retcode 1400); if the dedicated endpoint fails, **can** fall back to `send_msg` sending node segments directly
2. **Platform has no native forward but has rich text** (Yunhu / Telegram / Kook / Discord / Matrix, etc.):
   **Should** render the nodes into the platform's rich text fold format (HTML fold card / Card / Embed / blockquote list),
   reference style and adapter-specific task lists are in `SDK/Adapter/ADAPTER_FORWARD_GUIDE.md`
3. **Neither exists**: **Do not** implement this method (let alone return success while sending node dictionaries as plain text)—if not implemented, `list_sends` does not contain `MergeForward`, and the caller automatically falls back to plain text
4. **Failure semantics**: Return standard error response (`status: "failed"`) or throw an exception is acceptable; the caller will fall back to plain text sending, content is not lost
5. **Do not** call `Raw_ob12` inside `MergeForward` to send the same nodes (OneBot11's `Raw_ob12`
   has built-in automatic routing for pure node segments, which would cause a loop)

**Caller detection example:**

```python
sends = adapter.list_sends(platform)
if "MergeForward" in sends:
    await adapter.Send.To("group", "123").MergedForward(nodes)
else:
    await adapter.Send.To("group", "123").Text(plain_text)
```

> Reference implementation: `ErisPulse-OneBot11Adapter` (dedicated endpoint → `send_msg` fallback); rendering templates and adapter-specific task lists are in
> `SDK/Adapter/ADAPTER_FORWARD_GUIDE.md`.

## 3. Platform-Specific Method Naming

**Not recommended** to directly add platform-prefixed methods in the Send class. It is recommended to use generic method names or `Raw_{protocol}` methods.

**Not recommended:**
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

**Extension method requirements**:
- Method names use PascalCase, without platform prefix
- Must return an `asyncio.Task` object
- Must provide complete type annotations and docstrings
- Parameter design should be as consistent as possible with standard method style

## 4. Parameter Naming Convention

| Parameter Name | Description | Type |
|-------|------|------|
| `text` | Text content | `str` |
| `file` | Media content (URL / path / binary, see §2.1.1) | `str` / `bytes` |
| `filename` | File name (`File` optional, see §2.1.3) | `str` / `None` |
| `user_id` | User ID | `str` / `int` |
| `group_id` | Group ID | `str` / `int` |
| `message_id` | Message ID | `str` |
| `data` | Data object (e.g., card data) | `dict` |

## 5. Return Value Convention

- **Send methods** (e.g., `Text`, `Image`): Must return an `asyncio.Task` object
- **Modifier methods** (e.g., `At`, `Reply`, `AtAll`): Must return `self` to support chained calls

---

## 6. Reverse Conversion Convention (OneBot12 → Platform)

Adapters must not only convert platform-native events into OneBot12 format (forward conversion), but also **must** provide the ability to convert OneBot12 message segments back into platform-native API calls (reverse conversion). The unified entry point for reverse conversion is the `Raw_ob12` method.

### 6.1 Conversion Model

```
Forward Conversion (Receive Direction)                Reverse Conversion (Send Direction)
─────────────────                ─────────────────
Platform-native Events                       OneBot12 Message Segment List
    │                                  │
    ▼                                  ▼
Converter.convert()               Send.Raw_ob12()
    │                                  │
    ▼                                  ▼
OneBot12 Standard Event (with {platform}_raw)             Platform-native API Call
(Containing {platform}_raw)             (Return Standard Response Format)
```

**Core Symmetry**: Forward conversion retains original data in `{platform}_raw`, and reverse conversion accepts OneBot12 standard format and restores it into platform calls.

### 6.2 `Raw_ob12` Implementation Convention

`Raw_ob12` receives OneBot12 standard message segment lists and must convert them into platform-native API calls.

**Method Signature:**

```python
def Raw_ob12(self, message_segments: List[Dict]) -> asyncio.Task:
    """
    Send OneBot12 Standard Message Segments

    :param message_segments: List of OneBot12 message segments
        [
            {"type": "text", "data": {"text": "Hello"}},
            {"type": "image", "data": {"file": "https://..."}},
            {"type": "mention", "data": {"user_id": "123"}},
        ]
    :return: asyncio.Task, await returns standard response format
    """
```

**Implementation Requirements**:

1. **Must handle all standard message segment types**: At least support `text`, `image`, `audio`, `video`, `file`, `mention`, `reply`
2. **Must handle platform extension message segments**: For `{platform}_xxx` type message segments, convert them into platform-specific native calls
3. **Must return standard response format**: Follow [API Response Standard](api-response.md)
4. **Unsupported message segments should be skipped and warning logged**, should not throw exceptions causing the entire message to fail

### 6.3 Message Segment Conversion Rules

#### 6.3.1 Standard Message Segment Conversion

Adapters must implement the conversion of the following standard message segments:

| OneBot12 Message Segment | Conversion Requirement |
|----------------|---------|
| `text` | Directly use `data.text` |
| `image` | `data.file` processed according to §2.1 media protocol (three must forms + determination order) |
| `audio` | Same image processing logic |
| `video` | Same image processing logic |
| `file` | Same image processing logic; file name processed according to §2.1.3 derivation order `data.filename` |
| `mention` | Convert to platform's @user mechanism (e.g., Telegram's `entities`, Yunhu's `at_uid`) |
| `reply` | Convert to platform's reply reference mechanism |
| `face` | Convert to platform's emoji sending mechanism, skip if not supported |
| `location` | Convert to platform's location sending mechanism, skip if not supported |

#### 6.3.2 Platform Extension Message Segment Conversion

For message segments with platform prefixes, adapters should identify and convert them:

```python
def _convert_ob12_segments(self, segments: List[Dict]) -> Any:
    """Convert OneBot12 message segments to platform-native format"""
    platform_prefix = f"{self._platform_name}_"
    
    for segment in segments:
        seg_type = segment["type"]
        seg_data = segment["data"]
        
        if seg_type.startswith(platform_prefix):
            # Platform extension message segment → Platform-native call
            self._handle_platform_segment(seg_type, seg_data)
        elif seg_type in self._standard_segment_handlers:
            # Standard message segment → Platform equivalent operation
            self._standard_segment_handlers[seg_type](seg_data)
        else:
            # Unknown message segment → Log warning and skip
            logger.warning(f"Unsupported message segment type: {seg_type}")
```

#### 6.3.3 Handling Composite Message Segments

A message may contain multiple message segments, and adapters need to handle composite messages correctly:

```python
# Module sends a message containing text + image + @user
await send.Raw_ob12([
    {"type": "mention", "data": {"user_id": "123"}},
    {"type": "text", "data": {"text": "Hello"}},
    {"type": "image", "data": {"file": "https://example.com/img.jpg"}}
])
```

**Handling Strategy**:
- **Prioritize merging**: If the platform supports combining text, image, and @ in a single message, merge and send
- **Fallback to splitting**: If the platform does not support merging, send as multiple messages in order
- **Maintain order**: The sending order of message segments should match the list order

### 6.4 Relationship between `Raw_ob12` and Standard Methods

The standard send methods (`Text`, `Image`, etc.) of adapters are **already built-in and default delegated to `Raw_ob12` by the `SendDSL` base class**; adapter subclasses do not need to re-implement:

```python
class Send(SendDSL):
    def Raw_ob12(self, message_segments: List[Dict]) -> asyncio.Task:
        """Core implementation: OneBot12 message segments → Platform API (must implement)"""
        return asyncio.create_task(self._send_ob12(message_segments))

    # Text/Image/Voice/Video/File inherited from base class, automatically delegated to Raw_ob12
    # If platform-specific logic is needed, override individual methods:
    # def Text(self, text: str) -> asyncio.Task:
    #     return self.Raw_ob12([{"type": "text", "data": {"text": text}}])
```

**Benefits**:
- Conversion logic is centralized in `Raw_ob12`, reducing code duplication
- Standard methods and `Raw_ob12` have identical behavior
- Modules get the same result whether using `Text()` or `Raw_ob12()`
- The base class provides type signatures, and IDE can complete standard methods

### 6.5 Implementation Example

```python
class YunhuSend(SendDSL):
    """Yunhu platform Send implementation"""
    
    def Raw_ob12(self, message_segments: list) -> asyncio.Task:
        """OneBot12 message segments → Yunhu API call"""
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
                logger.warning(f"Yunhu does not support message segment: {seg_type}")
        
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

Module developers can query the adapter for supported send methods via API (do **not** hardcode a list of platform methods in the module—each adapter's extension methods evolve with version updates, and runtime discovery should be used):

```python
from ErisPulse import adapter

# List all send methods
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

## 9. Adapter Development Notes

For how to correctly override `BaseAdapter`, `Send`, `Request`'s `__init__`, see [Adapter Development Guide - `__init__` Notes](../developer-guide/adapters/getting-started.md#init-注意事项).

---

---

## 10. Adapter Implementation Checklist

### Send Methods
- [ ] Standard methods (`Text`, `Image`, etc.) are implemented
- [ ] Return values are all `asyncio.Task`
- [ ] Modifier methods (`At`, `Reply`, `AtAll`) return `self`
- [ ] Platform extension methods use PascalCase, no platform prefix
- [ ] All methods have complete type annotations and docstrings

### Media Sending Protocol
- [ ] `file` parameter **must forms** are all supported: HTTP(S) URL / local path / `bytes` (see §2.1.1)
- [ ] Form determination order follows §2.1.2 (bytes → URL → `file://` → path)
- [ ] `File`'s filename derivation order follows §2.1.3 (explicit `filename` > URL basename > path basename > platform default)
- [ ] Platform's media limitations (size / MIME / duration) are declared in the adapter documentation (§2.1.4)
- [ ] Unsupported media types are handled according to §2.1.5 degradation hierarchy: degrade to similar types or return `retcode=10002`, do not throw exceptions, do not silently drop

### Merge Forward (Optional, see §2.4)
- [ ] If the platform has native merge forwarding, `MergeForward` uses the protocol-specific endpoint, and if it fails, falls back to `send_msg` (OneBot11 system)
- [ ] If the platform has no native forwarding but has rich text, `MergeForward` renders as the platform's folded format (HTML card / Card / Embed / blockquote list), reference style and adapter-specific task lists are in `SDK/Adapter/ADAPTER_FORWARD_GUIDE.md`
- [ ] If neither exists, **do not implement** `MergeForward`, do not return success while sending node dictionary as plain text
- [ ] Do not call `Raw_ob12` inside `MergeForward` to forward the same nodes

### Reverse Conversion
- [ ] `Raw_ob12` **is implemented** (must, cannot be skipped)
- [ ] `Raw_ob12` can handle all standard message segments (`text`, `image`, `audio`, `video`, `file`, `mention`, `reply`)
- [ ] `Raw_ob12` can handle platform extension message segments (`{platform}_xxx` type)
- [ ] Standard send methods (`Text`, `Image`, etc.) internally delegate to `Raw_ob12`, not implement conversion logic independently
- [ ] Unsupported message segments are skipped and warning logged, not thrown exceptions
- [ ] Composite message segments are handled correctly (merge or split in sequence)

---

## 11. Message Builder (`MessageBuilder`)

`MessageBuilder` is a message segment builder tool provided by ErisPulse, used in conjunction with `Raw_ob12` to simplify the construction of OneBot12 message segments.

### 11.1 Import

```python
from ErisPulse.Core import MessageBuilder
# or
from ErisPulse.Core.Event import MessageBuilder
```

### 11.2 Chainable Build

```python
# Build a message containing text, image, and @user
segments = (
    MessageBuilder()
    .mention("123456")
    .text("Hello, look at this picture")
    .image("https://example.com/img.jpg")
    .reply("msg_789")
    .build()
)

# Send
await adapter.Send.To("group", "456").Raw_ob12(segments)
```

### 11.3 Quick Build Single Segment

```python
# Quickly build a single message segment (returns list[dict], can be directly passed to Raw_ob12)
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
|------|------|----------|
| `text(text)` | Text | `text` |
| `image(file)` | Image | `file` |
| `audio(file)` | Audio | `file` |
| `video(file)` | Video | `file` |
| `file(file, filename=None)` | File | `file`, `filename` (optional) |
| `mention(user_id, user_name=None)` | @user | `user_id`, `user_name` (optional) |
| `at(user_id, user_name=None)` | @user (`mention` alias) | Same as `mention` |
| `reply(message_id)` | Reply | `message_id` |
| `at_all()` | @all members | `{}` |
| `custom(type, data)` | Custom/platform extension | Custom |

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

- [Event Conversion Standard](event-conversion.md) - Complete event conversion specification, extension naming, and message segment standard
- [API Response Standard](api-response.md) - Adapter API response format standard
- [Session Type Standard](session-types.md) - Session type definition and mapping relationship
- [Request Action Specification](request-action-spec.md) - Request event field requirements, HandleRequest DSL, and adapter implementation requirements