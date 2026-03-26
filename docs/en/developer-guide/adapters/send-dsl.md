# SendDSL Deep Dive

SendDSL is a chain-style message sending interface provided by the ErisPulse adapter.

## Basic Usage

### 1. Specify Type and ID

```python
await adapter.Send.To("group", "123").Text("Hello")
```

### 2. Specify ID Only

```python
await adapter.Send.To("123").Text("Hello")
```

### 3. Specify Sending Account

```python
await adapter.Send.Using("bot1").Text("Hello")
```

### 4. Combine Usage

```python
await adapter.Send.Using("bot1").To("group", "123").Text("Hello")
```

## Method Chain

```
Using/Account() → To() → [Modifier Methods] → [Sending Methods]
```

## Sending Methods

All sending methods must return an `asyncio.Task` object.

### Basic Methods

| Method Name | Description | Return Value |
|--------|------|---------|
| `Text(text: str)` | Send text message | `asyncio.Task` |
| `Image(file: bytes \| str)` | Send image | `asyncio.Task` |
| `Voice(file: bytes \| str)` | Send voice message | `asyncio.Task` |
| `Video(file: bytes \| str)` | Send video | `asyncio.Task` |
| `File(file: bytes \| str)` | Send file | `asyncio.Task` |

### Raw Methods

| Method Name | Description | Return Value |
|--------|------|---------|
| `Raw_ob12(message)` | Send OneBot12 format message | `asyncio.Task` |
| `Raw_json(json_str)` | Send raw JSON message | `asyncio.Task` |

## Modifier Methods

Modifier methods return `self` to support chain calling.

### At Method

```python
# @Single user
await adapter.Send.To("group", "123").At("456").Text("Hello")

# @Multiple users
await adapter.Send.To("group", "123").At("456").At("789").Text("Hello to you all")
```

### AtAll Method

```python
# @All members
await adapter.Send.To("group", "123").AtAll().Text("Hello everyone")
```

### Reply Method

```python
# Reply to message
await adapter.Send.To("group", "123").Reply("msg_id").Text("Reply content")
```

### Combine Modifiers

```python
await adapter.Send.To("group", "123").At("456").Reply("msg_id").Text("Reply to @message")
```

## Account Management

### Using Method

```python
# Use account name
await adapter.Send.Using("account1").To("user", "123").Text("Hello")

# Use account ID
await adapter.Send.Using("bot_id").To("user", "123").Text("Hello")
```

### Account Method

The `Account` method is equivalent to `Using`:

```python
await adapter.Send.Account("account1").To("user", "123").Text("Hello")
```

## Asynchronous Handling

### Do Not Wait for Result

```python
# Message is sent in the background
task = adapter.Send.To("user", "123").Text("Hello")

# Continue with other operations
# ...
```

### Wait for Result

```python
# Directly await to get result
result = await adapter.Send.To("user", "123").Text("Hello")
print(f"Send result: {result}")

# Save Task first, await later
task = adapter.Send.To("user", "123").Text("Hello")
# ... other operations ...
result = await task
```

## Naming Conventions

### PascalCase Naming

All sending methods use PascalCase (Upper Camel Case):

```python
# ✅ Correct
def Text(self, text: str):
    pass

def Image(self, file: bytes):
    pass

# ❌ Wrong
def text(self, text: str):
    pass

def send_image(self, file: bytes):
    pass
```

### Platform-Specific Methods

Adding platform prefix methods is not recommended:

```python
# ✅ Recommended
def Sticker(self, sticker_id: str):
    pass

# ❌ Not recommended
def TelegramSticker(self, sticker_id: str):
    pass
```

Use the `Raw` method instead:

```python
# ✅ Recommended
await adapter.Send.Raw_ob12([{"type": "sticker", ...}])

# ❌ Not recommended
def TelegramSticker(self, ...):
    pass
```

## Return Values

### Task Object

All sending methods return `asyncio.Task`:

```python
import asyncio

def Text(self, text: str):
    return asyncio.create_task(
        self._adapter.call_api(
            endpoint="/send",
            content=text,
            recvId=self._target_id,
            recvType=self._target_type
        )
    )
```

### Standardized Response

`call_api` should return a standardized response:

```python
async def call_api(self, endpoint: str, **params):
    return {
        "status": "ok" or "failed",
        "retcode": 0 or error_code,
        "data": {...},
        "message_id": "msg_id" or "",
        "message": "",
        "{platform}_raw": raw_response
    }
```

## Complete Examples

### Basic Usage

```python
from ErisPulse.Core import adapter

my_adapter = adapter.get("myplatform")

# Send text
await my_adapter.Send.To("user", "123").Text("Hello World!")

# Send image
await my_adapter.Send.To("group", "456").Image("https://example.com/image.jpg")

# Send file
with open("document.pdf", "rb") as f:
    await my_adapter.Send.To("user", "123").File(f.read())
```

### Chain Calling

```python
# @user + reply
await my_adapter.Send.To("group", "456").At("789").Reply("msg123").Text("Reply to @message")

# @all + multiple modifiers
await my_adapter.Send.Using("bot1").To("group", "456").AtAll().Text("Announcement message")
```

### Raw Messages

```python
# Send OneBot12 format message
ob12_msg = [
    {"type": "text", "data": {"text": "Hello"}},
    {"type": "image", "data": {"file": "https://example.com/image.jpg"}}
]
await my_adapter.Send.To("group", "456").Raw_ob12(ob12_msg)
```

## Related Documentation

- [Adapter Development Getting Started](getting-started.md) - Create adapter
- [Adapter Core Concepts](core-concepts.md) - Understand adapter architecture
- [Adapter Best Practices](best-practices.md) - Develop high-quality adapters
- [Sending Method Naming Conventions](../../standards/send-type-naming.md) - Naming conventions