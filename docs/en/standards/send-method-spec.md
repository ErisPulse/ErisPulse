# ErisPulse Send Method Specification

> [!TIP]
> **When to read this**: When implementing the `Send` class in your adapter—refer to this document for method naming, media parameter (URL/path/bytes) support, `Raw_ob12` reverse conversion, and merge forwarding capabilities. Skip if not needed.

This document defines the naming, parameter, and reverse conversion requirements for send methods in ErisPulse adapters.

## 0. Keyword Definitions

The terms **must (MUST)**, **should (SHOULD)**, and **may (MAY)** in this document are interpreted as follows (referencing RFC 2119):

| Keyword | Meaning | Consequence of Violation |
|--------|------|---------|
| **Must** | Mandatory requirement; framework behavior/cross-platform consistency depends on it | Adapter is considered non-compliant; module code may not work |
| **Should** | Strongly recommended; follow unless there is a compelling reason | If deviated, the adapter documentation must explain the reason and alternative behavior |
| **May** | Optional; decide based on platform capability | None |

## 1. Standard Method Naming

All send methods use **PascalCase** (capitalized first letter).

### 1.1 Standard Send Methods

| Method Name | Description | Parameter Type | Implementation Requirement |
|-------|------|---------|---------|
| `Text` | Send text message | `str` | Must |
| `Image` | Send image | `str` \| `bytes` | Must (built-in in base class; see §6.4) |
| `Voice` | Send voice | `str` \| `bytes` | Must (built-in in base class; if platform does not support voice, follow §2.1.5) |
| `Video` | Send video | `str` \| `bytes` | Must (built-in in base class; if platform does not support video, follow §2.1.5) |
| `File` | Send file | `str` \| `bytes`, `filename: str \| None = None` | Must (built-in in base class) |
| `At` | @ user/group | `str` (user_id) | Modifier method, optional |
| `Face` | Send emoji | `str` (emoji) | May |
| `Reply` | Reply to message | `str` (message_id) | Modifier method, optional |
| `Forward` | Forward message | `str` (message_id) | May |
| `Markdown` | Send Markdown message | `str` | May |
| `HTML` | Send HTML message | `str` | May |
| `Card` | Send card message | `dict` | May |

> Standard methods (`Text`/`Image`/`Voice`/`Video`/`File`) are built into the base class `SendDSL` and default to delegating to `Raw_ob12`. Adapters **do not need to re-implement** these methods to obtain type signatures; only override individual methods when the platform requires special logic (see §6.4).

### 1.2 Chained Modifier Methods

| Method Name | Description | Parameter Type |
|-------|------|---------|
| `At` | @ user (can be called multiple times) | `str` (user_id) |
| `AtAll` | @ all members | None |
| `Reply` | Reply to message | `str` (message_id) |

### 1.3 Protocol Methods

| Method Name | Description | Required? |
|-------|------|---------|
| `Raw_ob12` | Send OneBot12 format message segment | Must |

**`Raw_ob12` is a required method**. This is one of the adapter's core responsibilities: receiving OneBot12 standard message segments and converting them into native platform API calls. `Raw_ob12` serves as the unified entry point for reverse conversion (OneBot12 → platform), ensuring modules can send messages using standard message segments without relying on platform-specific methods.

**Behavior when `Raw_ob12` is not overridden**: The default base class implementation will log an **error-level** message and return a standard error response format (`status: "failed"`, `retcode: 10002`), indicating that the adapter developer must implement this method.

### 1.4 Recommended Extension Naming Convention

If adapters need to support sending non-OneBot12 format raw data (such as platform-specific JSON, XML, etc.), the following naming convention is recommended:

| Recommended Method Name | Description |
|-----------|------|
| `Raw_json` | Send arbitrary JSON data |
| `Raw_xml` | Send arbitrary XML data |

**Note**: These methods are **not** default methods provided by the base class, nor are they mandatory to implement. They are only naming conventions, and adapters can define them as needed. If an adapter does not support these formats, it does not need to define them.

**MessageBuilder**: ErisPulse provides the `MessageBuilder` utility class for easily constructing OneBot12 message segment lists, which can be used in conjunction with `Raw_ob12`. See [MessageBuilder Detailed Explanation](../advanced/message-builder.md).

## 2. Parameter Specification Details

### 2.1 Media Message Sending Protocol (`Image` / `Voice` / `Video` / `File`)

This section is the **unified protocol standard** for media sending: modules can use the same code to call the four media methods, and adapters are responsible for converting the various forms of the `file` parameter into native platform upload/send behavior.

#### 2.1.1 Valid Forms of the `file` Parameter

| Form | Example | Adapter Requirement |
|------|------|-----------|
| HTTP(S) URL | `https://example.com/image.jpg` | **Must** accept |
| Local file path | `/path/to/file.jpg`, `C:\path\to\file.jpg` | **Must** accept |
| Binary data | `b"\x89PNG..."` | **Must** accept |
| `file://` URI | `file:///path/to/file.jpg` | **Should** accept (can be forwarded as a local path) |
| Base64 string / Data URI | `iVBORw0KGgo=...`, `data:image/png;base64,...` | **Should** accept (compatible with OneBot12 ecosystem conventions) |

> Adapters **must** behave consistently across the three required forms—modules receive the same message regardless of whether they pass a URL, path, or bytes. If the platform cannot directly use a certain form (e.g., the platform API does not support referencing external URLs), the adapter should download/read and then upload, **not** require the module to retry with a different form.

#### 2.1.2 Form Determination Order

When implementing media parameter handling, adapters **should** determine the form in the following order:

1. `bytes` type → upload directly
2. String starting with `http://` / `https://` → handle as URL (direct reference or download and upload, depending on platform capability)
3. String starting with `file://` → strip prefix and handle as local path
4. Other strings → handle as local path (read and upload if exists; return standard error response if does not exist)

```python
def _resolve_media(self, file: "str | bytes") -> bytes:
    """Form determination and normalization (example)"""
    if isinstance(file, (bytes, bytearray)):
        return bytes(file)
    if file.startswith(("http://", "https://")):
        return self._download(file)          # download if platform cannot reference URL
    if file.startswith("file://"):
        file = file[len("file://"):]
    with open(file, "rb") as f:              # local path
        return f.read()
```

#### 2.1.3 File Name Semantics for `File`

`File` method signature: `File(file, filename=None)` (where `filename` is optional; built-in in base class).

File name **derivation order** (when adapter generates file name without explicit `filename`):

1. Explicit `filename` parameter (highest priority)
2. URL's basename (e.g., `https://host/a/b/report.pdf` → `report.pdf`, query string stripped)
3. Local path's basename (e.g., `/tmp/data/backup.zip` → `backup.zip`)
4. Platform default generation (e.g., `file_{timestamp}`; **should** retain real extension—extension affects platform-side type recognition and preview behavior)

> `Image` / `Voice` / `Video` can also accept `filename` (passed via message segment `data.filename`), but only `File`'s file name has cross-platform semantic guarantees.

#### 2.1.4 Declaration Obligation for Platform Restrictions

Platforms have different constraints on media size, format (MIME), duration (audio/video), etc. Adapters **should**:

- Declare supported media types and limits in the adapter documentation
- Return **standard error response** for over-limit or unsupported input (`status: "failed"`; `retcode` uses `10002` or platform-specific error code, `message` explains the reason), **not** throw an exception to interrupt module logic

#### 2.1.5 Capability Degradation Steps

When a platform does not support a certain media **type**, follow the following degradation steps (in line with the "capability degradation without error" principle):

| Scenario | Degradation Behavior |
|------|---------|
| `Voice` does not support voice messages | **Should** send as `File` (or platform-adjacent form); if cannot express, return `retcode=10002` |
| `Video` does not support video messages | Same as above |
| Media type completely unsupported (no file capability) | Return `retcode=10002`, `message` indicates unsupported data type |
| Form not supported (e.g., cannot handle base64) | Return `retcode=10002`, **can** in `message` prompt module to use URL/bytes |

**Prohibited actions**: Silent discard (no return), throw an exception, or require module to write platform-specific handling.

### 2.2 @ User Parameter Specification

**Method:** `At` (modifier method)

**Parameter:** `user_id` (`str`)

**Requirements:**
- `user_id` should be a string-type user identifier
- The `user_id` format may differ across platforms (numbers, UUIDs, strings, etc.)
- The adapter is responsible for converting `user_id` into the platform-specific format
- Note that the actual send method call should be placed at the last position.

**Example:**
```python
# Single @ user
Send.To("group", "g123").At("123456").Text("Hello")

# Multiple @ users (chained call)
send.To("group", "g123").At("123456").At("789012").Text("Hello everyone")
```

### 2.3 Reply Message Parameter Specification

**Method:** `Reply` (modifier method)

**Parameter:** `message_id` (`str`)

**Requirements:**
- `message_id` should be a string-type message identifier
- Should be the ID of a previously received message
- Some platforms may not support the reply function; adapters should degrade gracefully

**Example:**
```python
send.To("group", "g123").Reply("msg_123456").Text("Received")
```

### 2.4 Merge Forward Capability (`MergeForward`, Optional)

`MergeForward(nodes)` is an **optional capability method**: it packages multiple contents into a "merged forward / rich text collapse" form for sending, with the adapter deciding the best presentation based on platform capability. This differs semantically from `Forward(from_chat_id, message_id)` (forwarding **existing** messages) in §1.1; both coexist.

> **Standard Background**: The OneBot12 core standard does not have a node message segment or a merged forward API—"message node" is a concept implemented at the OneBot v11 ecosystem level (go-cqhttp extension), and v12 has delegated such platform-specific capabilities to the extension mechanism. ErisPulse's landing approach is equivalent to the extension mechanism: **no new standard message segments are added, but optional capability methods + `list_sends` runtime detection**—adapters that implement `MergeForward` automatically gain capability, and those that do not implement it automatically fall back to plain text, with zero module modifications.

**Method Signature:**

```python
def MergeForward(self, nodes: List[Dict]) -> asyncio.Task:
    """
    Send merged forward / rich text collapse message

    :param nodes: List of merged forward nodes (go-cqhttp extension's OneBot v11 node format):
        [
            {
                "type": "node",
                "data": {
                    "user_id": "10000",     # Displayed sender ID
                    "nickname": "MyBot",     # Displayed sender nickname
                    "content": [            # List of message segments, currently text segments
                        {"type": "text", "data": {"text": "【1/3】Title\nBody…"}}
                    ],
                },
            },
        ]
    :return: asyncio.Task, await to return standard response format
    """
```

**Implementation Requirements:**

1. **Platform has native merged forward** (OneBot11 system): **Must** call the dedicated protocol endpoint (`send_group_forward_msg` / `send_private_forward_msg`)—NapCat implementations will reject `send_msg` carrying node segments (retcode 1400); if the dedicated endpoint fails, **can** fall back to `send_msg` sending node segments directly
2. **Platform has no native forward but has rich text** (Yunhu / Telegram / Kook / Discord / Matrix, etc.): **Should** render nodes into the platform's rich text collapse form (HTML collapse card / Card / Embed / blockquote list), refer to style and adapter-specific task list in `SDK/Adapter/ADAPTER_FORWARD_GUIDE.md`
3. **Neither exists**: **Should not** implement this method (and must not return success while sending node dictionaries as plain text)—if not implemented, `list_sends` does not contain `MergeForward`, and the caller automatically falls back to plain text
4. **Failure semantics**: Return standard error response (`status: "failed"`) or throw an exception is acceptable; the caller will fall back to plain text sending, and content is not lost
5. **Should not** call `Raw_ob12` to send the same nodes inside `MergeForward` (OneBot11's `Raw_ob12` has built-in automatic routing of pure node segments, which would cause a loop)
6. **Outbound node segment parsing** (universal adapter convention): Each adapter's `Raw_ob12` segment distribution should register `node` segments—pure node lists are automatically routed to the adapter's merged forward presentation (platforms with `MergeForward` are equivalent to direct calls; platforms without this method extract each node's text to output "nickname: body" line by line in original form); text from node segments in mixed lists is merged into the body.
   Any adapter receiving a node segment must not silently discard it.

**Platform Implementation Forms** (see `SDK/Adapter/ADAPTER_FORWARD_GUIDE.md`):

- Native endpoint: OneBot11, SnowLuma (three-tiered fallback: `send_group/private_forward_msg` dedicated endpoint → `upload_forward_msg` to get resid and send forward segment → send node segments directly; SnowLuma API aligns fully with NapCat, adapters can directly connect to NapCat backend)
- Folded HTML `<details>` card: Yunhu (bot/user protocol), Email, Sandbox, Allons(Ideaura)
- Whitelisted HTML / quote block: Telegram (`<b>`+`<blockquote>`), Matrix (blockquote variant, whitelisted stripping of details/internal styles)
- Platform card: Kook (Card header+section), Discord (Embed fields)
- Official Markdown quote list: QQBot (official md has no collapse syntax, server-side validation rejects invalid tags 40034011)
- Not implemented (node segments output as original text for degradation): OneBot12 (standard has no node segments), WeCom, Terminal, Webhook, WechatMp

**Caller Detection Example:**

```python
sends = adapter.list_sends(platform)
if "MergeForward" in sends:
    await adapter.Send.To("group", "123").MergeForward(nodes)
else:
    await adapter.Send.To("group", "123").Text(plain_text)
```

> Reference Implementation: `ErisPulse-OneBot11Adapter` (dedicated endpoint → `send_msg` fallback); rendering templates and adapter-specific task lists are in `SDK/Adapter/ADAPTER_FORWARD_GUIDE.md`.

## 3. Platform-Specific Method Naming

**Not recommended** to directly add platform-prefixed methods in the `Send` class. Use generic method names or `Raw_{protocol}` methods.

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

**Extension Method Requirements**:
- Method names use PascalCase, no platform prefix
- Must return an `asyncio.Task` object
- Must provide complete type annotations and docstrings
- Parameter design should be as consistent as possible with standard method styles

## 4. Parameter Naming Convention

| Parameter Name | Description | Type |
|-------|------|------|
| `text` | Text content | `str` |
| `file` | Media content (URL/path/bytes, see §2.1.1) | `str` / `bytes` |
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
Forward Conversion (Receiving Direction)                Reverse Conversion (Sending Direction)
─────────────────                ─────────────────
Platform-native Event                       OneBot12 Message Segment List
    │                                  │
    ▼                                  ▼
Converter.convert()               Send.Raw_ob12()
    │                                  │
    ▼                                  ▼
OneBot12 Standard Event                  Platform-native API Call
(Containing {platform}_raw)             (Return Standard Response Format)
```

**Core Symmetry**: Forward conversion retains original data in `{platform}_raw`, and reverse conversion accepts OneBot12 standard format and restores it into a platform call.

### 6.2 `Raw_ob12` Implementation Convention

`Raw_ob12` receives OneBot12 standard message segment lists and must convert them into platform-native API calls.

**Method Signature**:

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
    :return: asyncio.Task, await to return standard response format
    """
```

**Implementation Requirements**:

1. **Must handle all standard message segment types**: At least support `text`, `image`, `audio`, `video`, `file`, `mention`, `reply`
2. **Must handle platform extension message segments**: For `{platform}_xxx` type message segments, convert them into corresponding platform-native calls
3. **Must return standard response format**: Follow [API Response Standard](api-response.md)
4. **Unsupported message segments should be skipped and warning logged**, not throw an exception causing the entire message to fail

### 6.3 Message Segment Conversion Rules

#### 6.3.1 Standard Message Segment Conversion

Adapters must implement the following standard message segment conversions:

| OneBot12 Message Segment | Conversion Requirement |
|----------------|---------|
| `text` | Directly use `data.text` |
| `image` | `data.file` handled according to §2.1 media protocol (three must forms + determination order) |
| `audio` | Same handling logic as image |
| `video` | Same handling logic as image |
| `file` | Same handling logic as image; filename handled according to §2.1.3 derivation order for `data.filename` |
| `mention` | Convert to platform's @ user mechanism (e.g., Telegram's `entities`, Yunhu's `at_uid`) |
| `reply` | Convert to platform's reply reference mechanism |
| `face` | Convert to platform's emoji sending mechanism, skip if not supported |
| `location` | Convert to platform's location sending mechanism, skip if not supported |

#### 6.3.2 Platform Extension Message Segment Conversion

For message segments with platform prefixes, adapters should recognize and convert them:

```python
def _convert_ob12_segments(self, segments: List[Dict]) -> Any:
    """Convert OneBot12 message segments to platform-native format"""
    platform_prefix = f"{self._platform_name}_"
    
    for segment in segments:
        seg_type = segment["type"]
        seg_data = segment["data"]
        
        if seg_type.startswith(platform_prefix):
            # Platform extension message segment → platform-native call
            self._handle_platform_segment(seg_type, seg_data)
        elif seg_type in self._standard_segment_handlers:
            # Standard message segment → platform equivalent operation
            self._standard_segment_handlers[seg_type](seg_data)
        else:
            # Unknown message segment → log warning and skip
            logger.warning(f"Unsupported message segment type: {seg_type}")
```

#### 6.3.3 Handling of Composite Message Segments

A message may contain multiple message segments, and adapters need to handle composite messages correctly:

```python
# Module sends a message containing text+image+@ user
await send.Raw_ob12([
    {"type": "mention", "data": {"user_id": "123"}},
    {"type": "text", "data": {"text": "Hello"}},
    {"type": "image", "data": {"file": "https://example.com/img.jpg"}}
])
```

**Handling Strategy**:
- **Prioritize merging**: If the platform supports combining text, image, @, etc., in a single message, merge and send
- **Fallback to splitting**: If the platform does not support merging, send as multiple messages in sequence
- **Maintain order**: The sending order of message segments should match the list order

### 6.4 Relationship Between `Raw_ob12` and Standard Methods

The adapter's standard send methods (`Text`, `Image`, etc.) are **already implemented and default-delegated to `Raw_ob12` by the `SendDSL` base class**; adapter subclasses do not need to re-implement them:

```python
class Send(SendDSL):
    def Raw_ob12(self, message_segments: List[Dict]) -> asyncio.Task:
        """Core implementation: OneBot12 message segments → platform API (must implement)"""
        return asyncio.create_task(self._send_ob12(message_segments))

    # Text/Image/Voice/Video/File inherited from base class, automatically delegated to Raw_ob12
    # If platform-specific logic is needed, override individual methods:
    # def Text(self, text: str) -> asyncio.Task:
    #     return self.Raw_ob12([{"type": "text", "data": {"text": text}}])
```

**Benefits**:
- Conversion logic is centralized in `Raw_ob12`, reducing duplicate code
- Standard methods and `Raw_ob12` have identical behavior
- Modules get the same result whether using `Text()` or `Raw_ob12()`
- The base class provides type signatures, allowing IDE to complete standard methods

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

Module developers can query the adapter's supported send methods (don't hardcode the platform's method list in the module—each adapter's extension methods evolve with version changes, so runtime discovery is the standard):

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
- [ ] Standard methods (`Text`, `Image`, etc.) implemented
- [ ] Return values are all `asyncio.Task`
- [ ] Modifier methods (`At`, `Reply`, `AtAll`) return `self`
- [ ] Platform extension methods use PascalCase, no platform prefix
- [ ] All methods have complete type annotations and docstrings

### Media Sending Protocol
- [ ] `file` parameter **must forms** all supported: HTTP(S) URL / local path / `bytes` (see §2.1.1)
- [ ] Form determination order follows §2.1.2 (bytes → URL → `file://` → path)
- [ ] `File`'s filename derivation order follows §2.1.3 (explicit `filename` > URL basename > path basename > platform default)
- [ ] Platform's media restrictions (size / MIME / duration) are declared in adapter documentation (§2.1.4)
- [ ] Unsupported media types handled by the degradation ladder in §2.1.5: degraded to similar type or return `retcode=10002`, no exception thrown, no silent discard

### Merge Forward (Optional, see §2.4)
- [ ] Platform has native merged forward: `MergeForward` uses protocol dedicated endpoint, fails back to `send_msg` (OneBot11 system)
- [ ] Platform has no native forward but has rich text: `MergeForward` renders into platform's folded form (HTML card / Card / Embed / blockquote)
- [ ] Neither exists: **do not implement** `MergeForward`, do not return success while sending node dictionary as plain text
- [ ] `MergeForward` does not call `Raw_ob12` to forward the same nodes internally

### Reverse Conversion
- [ ] `Raw_ob12` **implemented** (required, cannot skip)
- [ ] `Raw_ob12` can handle all standard message segments (`text`, `image`, `audio`, `video`, `file`, `mention`, `reply`)
- [ ] `Raw_ob12` can handle platform extension message segments (`{platform}_xxx` type)
- [ ] Standard send methods (`Text`, `Image`, etc.) internally delegate to `Raw_ob12`, not implement separate conversion logic
- [ ] Unsupported message segments are skipped and warning logged, not thrown as an exception
- [ ] Composite message segments are correctly handled (merged or sent sequentially)

---

## 11. MessageBuilder - Adapter-Side Notes

`MessageBuilder` is a OneBot12 message segment builder tool provided by ErisPulse, for **module-side** message construction:
Chained calls (or static quick construction) ultimately produce a standard message segment list `[{"type": ..., "data": ...}]`,
which is directly passed to `Raw_ob12` by the caller.

**Adapter-side only needs to know this**: `Raw_ob12` receives exactly this product—structurally identical to a hand-written message segment list,
and processed according to the segment distribution logic in §6.2, without needing to perceive whether it comes from `MessageBuilder` or a literal list.

> Full usage (dual-mode mechanism, all message segment methods, `copy()` / `clear()` utility methods, and examples) is in [MessageBuilder Detailed Explanation](../advanced/message-builder.md), not repeated here.

---

## 12. Related Documents

**For implementing send return values, refer to:**
- [API Response Standard](api-response.md) - Standard format for adapter API responses

**For other sides of the same adapter:**
- [Event Conversion Standard](event-conversion.md) - Complete event conversion specification, extension naming, and message segment standard
- [Session Type Standard](session-types.md) - Definition and mapping of session types
- [Request Operation Specification](request-action-spec.md) - Field requirements for request events, HandleRequest DSL, and adapter implementation requirements