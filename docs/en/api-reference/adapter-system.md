# Adapter System API

This document details the API of the ErisPulse adapter system.

## Adapter Manager

### Getting Adapters

```python
from ErisPulse import sdk

# Get adapter by name
adapter = sdk.adapter.get("platform_name")

# Access via property
adapter = sdk.adapter.platform_name
```

### Adapter Event Listening

```python
# Listen to OneBot12 standard events
@sdk.adapter.on("message")
async def handle_message(event):
    pass

# Listen to standard events of a specific platform
@sdk.adapter.on("message", platform="yunhu")
async def handle_yunhu_message(event):
    pass

# Listen to platform native events
@sdk.adapter.on("raw_event", raw=True, platform="yunhu")
async def handle_raw_event(data):
    pass
```

### Adapter Management

```python
# Get all platforms
platforms = sdk.adapter.platforms

# Check if adapter exists
exists = sdk.adapter.exists("platform_name")

# Enable/Disable adapter
sdk.adapter.enable("platform_name")
sdk.adapter.disable("platform_name")

# Start/Shutdown adapter
await sdk.adapter.startup(["platform1", "platform2"])
await sdk.adapter.shutdown()
```

## Middleware

### Registering Middleware

```python
# Add middleware
@sdk.adapter.middleware
async def my_middleware(event):
    # Process event
    sdk.logger.info(f"Middleware processing: {event}")
    return event
```

### Middleware Execution Order

Middleware executes in the order of registration, running before the event is dispatched to handlers.

## Send Message Sending

### Basic Sending

```python
# Get adapter
adapter = sdk.adapter.get("platform")

# Send text message
await adapter.Send.To("user", "123").Text("Hello")

# Send image message
await adapter.Send.To("group", "456").Image("https://example.com/image.jpg")
```

### Specify Sending Account

```python
# Use account name
await adapter.Send.Using("account1").To("user", "123").Text("Hello")

# Use account ID
await adapter.Send.Using("bot_id").To("user", "123").Text("Hello")
```

### Query Supported Sending Methods
> Since the new standard specification requires overriding the `__getattr__` method to implement a fallback sending mechanism, it is not possible to use the `hasattr` method to check if a method exists. Therefore, starting from `2.3.5-dev.3`, a `list_sends` method has been added to query all supported sending methods.

```python
# List all sending methods supported by the platform
methods = sdk.adapter.list_sends("onebot11")
# Returns: ["Text", "Image", "Voice", "Markdown", ...]

# Get detailed information for a specific method
info = sdk.adapter.send_info("onebot11", "Text")
# Returns:
# {
#     "name": "Text",
#     "parameters": [
#         {"name": "text", "type": "str", "default": null, "annotation": "str"}
#     ],
#     "return_type": "Awaitable[Any]",
#     "docstring": "Send text message..."
# }
```

### Chained Modifiers

```python
# Mention user
await adapter.Send.To("group", "456").At("789").Text("Hello")

# Mention all members
await adapter.Send.To("group", "456").AtAll().Text("Hello everyone")

# Reply to message
await adapter.Send.To("group", "456").Reply("msg_id").Text("Reply content")

# Combined use
await adapter.Send.To("group", "456").At("789").Reply("msg_id").Text("Reply to mentioned message")
```

## API Calls

### call_api Method
> Note that the API calling methods may vary for different platforms. Please refer to the corresponding platform adapter documentation.
> Direct use of the `call_api` method is not recommended; it is suggested to use the `Send` class for message sending.

```python
# Call platform API
result = await adapter.call_api(
    endpoint="/send",
    content="Hello",
    recvId="123",
    recvType="user"
)

# Standardized response
{
    "status": "ok",
    "retcode": 0,
    "data": {...},
    "message_id": "msg_id",
    "message": "",
    "{platform}_raw": raw_response
}
```

## Adapter Base Class

### BaseAdapter Methods

```python
from ErisPulse.Core import BaseAdapter

class MyAdapter(BaseAdapter):
    def __init__(self, sdk):
        # Initialize adapter
        pass
    
    async def start(self):
        """Start adapter (must implement)"""
        pass
    
    async def shutdown(self):
        """Shutdown adapter (must implement)"""
        pass
    
    async def call_api(self, endpoint: str, **params):
        """Call platform API (must implement)"""
        pass
```

### Send Nested Class

```python
class MyAdapter(BaseAdapter):
    class Send(BaseAdapter.Send):
        def Text(self, text: str):
            """Send text message"""
            import asyncio
            return asyncio.create_task(
                self._adapter.call_api(
                    endpoint="/send",
                    content=text,
                    recvId=self._target_id,
                    recvType=self._target_type
                )
            )
```

## Related Documentation

- [Core Modules API](core-modules.md) - Core Modules API
- [Event System API](event-system.md) - Event Module API
- [Adapter Development Guide](../developer-guide/adapters/) - Developing Platform Adapters