# ErisPulse Sending Method Specifications

This document defines the naming and parameter specifications for the sending methods of the `Send` class within the ErisPulse adapter.

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

| Method Name | Description |
|-------|------|
| `Raw_ob12` | Send raw OneBot12 format message |
| `Raw_json` | Send raw JSON format message |
| `Raw_xml` | Send raw XML format message |

## 2. Detailed Parameter Specifications

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

### 2.2 Text Message Parameter Specifications

**Method:** `Text`

**Parameter:** `text` (`str`)

**Requirements:**
- Supports plain text content
- No formatting processing (e.g., Markdown, HTML)
- It is recommended to limit text length (e.g., 2000-5000 characters)
- For very long text, users should be prompted to truncate or send in segments

**Example:**
```python
# Simple text
send.Text("Hello, World!")

# Long text (recommended to split)
long_text = "Very long text content..."
if len(long_text) > 2000:
    # Send in segments
    for i in range(0, len(long_text), 2000):
        send.Text(long_text[i:i+2000])
else:
    send.Text(long_text)
```

### 2.3 @ User Parameter Specifications

**Method:** `At` (modifier method)

**Parameter:** `user_id` (`str`)

**Requirements:**
- `user_id` should be a string type user identifier
- `user_id` format may vary across different platforms (numbers, UUID, strings, etc.)
- Adapter is responsible for converting `user_id` to platform-specific format

**Example:**
```python
# @ a single user
send.Text("Hello").At("123456")

# @ multiple users (chained calls)
send.Text("Hello everyone").At("123456").At("789012")
```

### 2.4 Reply Message Parameter Specifications

**Method:** `Reply` (modifier method)

**Parameter:** `message_id` (`str`)

**Requirements:**
- `message_id` should be a string type message identifier
- It should be the ID of a previously received message
- Some platforms may not support reply functionality; adapter should gracefully degrade

**Example:**
```python
# Reply to a message
send.Text("Received").Reply("msg_123456")
```

### 2.5 Card Message Parameter Specifications

**Method:** `Card`

**Parameter:** `data` (`dict`)

**Requirements:**
- `data` should be a dictionary type card data
- Specific format depends on the platform (e.g., Telegram's InlineKeyboard, OneBot12's card)
- Adapter should validate data format and convert to platform-specific format
- Platforms that do not support cards should downgrade to text message

**Example:**
```python
# Send card data
card_data = {
    "type": "image",
    "title": "Card Title",
    "content": "Card Content",
    "image": "https://example.com/image.jpg"
}
send.Card(card_data)
```

### 2.6 Parameter Validation and Error Handling

**General Requirements:**
1. **Type Check:** Verify parameter types are correct
2. **Range Check:** Verify parameter values are within reasonable limits
3. **Existence Check:** Verify required parameters exist
4. **Format Check:** Verify formats of URL, file paths, etc. are correct

**Error Handling Suggestion:**
```python
def Image(self, image: Union[bytes, str]):
    # Type check
    if not isinstance(image, (bytes, str)):
        raise TypeError("Parameter must be of type bytes or str")
    
    # URL format check
    if isinstance(image, str) and not image.startswith(("http://", "https://")):
        # Check if it is a local file path
        if not os.path.exists(image):
            raise FileNotFoundError(f"File does not exist: {image}")
    
    # File size check
    if isinstance(image, bytes) and len(image) > 10 * 1024 * 1024:  # 10MB
        raise ValueError("File size exceeds limit (10MB)")
    
    # Send message
    return self._send_image(image)
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

# Or use Raw method
def Raw_ob12(self, message):  # ✅ Send OneBot12 format
    pass
```

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

## 6. Related Documentation

- [Adapter System - SendDSL Overview](../core/adapters.md) - View calling methods and usage examples
- [Adapter Development Guide](../development/adapter.md) - View adapter implementation requirements
- [Module Development Guide](../development/module.md) - View message sending examples within modules