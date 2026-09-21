# Adapter System API

This document provides a detailed introduction to the ErisPulse adapter system's API.

## Adapter Manager

### Getting an Adapter

```python
from ErisPulse import sdk

# Get an adapter by name
adapter = sdk.adapter.get("platform_name")

# Or access it directly via attribute
adapter = sdk.adapter.platform_name
```

### Using Adapter Event Listeners
> In general, it is recommended to use the `Event` module for event listening/handling;
>
> The `Event` module also provides powerful wrappers, which can bring more convenience to your module development.

```python
# Listen for OneBot12 standard events
@sdk.adapter.on("message")
async def handle_message(event):
    pass

# Listen for standard events of a specific platform
@sdk.adapter.on("message", platform="yunhu")
async def handle_yunhu_message(event):
    pass

# Listen for platform-native events
@sdk.adapter.on("raw_event", raw=True, platform="yunhu")
async def handle_raw_event(data):
    pass
```

### Adapter Management

```python
# Get all platforms
platforms = sdk.adapter.platforms

# Check if an adapter exists
exists = sdk.adapter.exists("platform_name")

# Enable/Disable an adapter
sdk.adapter.enable("platform_name")
sdk.adapter.disable("platform_name")

# Start/Stop an adapter
# The following methods only show parameter cases; without parameters, it starts/stops all registered adapters
await sdk.adapter.startup(["platform1", "platform2"])
await sdk.adapter.shutdown(["platform1", "platform2"])

# Check if an adapter is running
is_running = sdk.adapter.is_running("platform_name")

# List all running adapters
running = sdk.adapter.list_running()
```

## Middleware

Middleware executes before events are dispatched to handlers, allowing modification, filtering, or logging of event data.

### Registering Middleware

```python
@sdk.adapter.middleware
async def my_middleware(event):
    sdk.logger.info(f"Middleware processing: {event}")
    return event
```

### Middleware Execution Model

- **Execution Order**: Middleware executes in registration order (first registered, first executed)
- **Data Passing**: Each middleware receives the `event` data returned by the previous middleware; if a middleware returns `None`, the return value is ignored and the original data continues to be passed (while outputting a `warning` level log)
- **Data Modification**: Middleware can modify event data and return the modified dictionary
- **Event Rejection**: Explicitly returning `False` rejects the event—the event is discarded, not passed to any handler, and no outbound side effects occur; rejection outputs a TRACE log and triggers the `adapter.event.blocked` lifecycle hook (carrying the middleware name and full event)

```python
@sdk.adapter.middleware
async def add_timestamp(event):
    event["processed_at"] = time.time()
    return event

@sdk.adapter.middleware
async def filter_spam(event):
    if event.get("detail_type") == "private":
        text = event.get("alt_message", "")
        if "spam advertisement" in text:
            return False  # Reject: event is discarded, not passed to any handler
    return event
```

> **Note**: Only explicitly returning `False` rejects the event (returning empty dict / `0` / `""`, etc., falsy values does not reject);
> Returning `None` still allows the event and keeps the payload unchanged. Rejected events can be audited and investigated for "why the event was not responded to" by listening to the `adapter.event.blocked` hook.

## Send Message

### Basic Sending

```python
# Get an adapter
adapter = sdk.adapter.get("platform")

# Send text message
await adapter.Send.To("user", "123").Text("Hello")

# Send image message
await adapter.Send.To("group", "456").Image("https://example.com/image.jpg")
```

### Specifying Sending Account

```python
# Using account name
await adapter.Send.Using("account1").To("user", "123").Text("Hello")

# Using account ID
await adapter.Send.Using("bot_id").To("user", "123").Text("Hello")
```

### Querying Supported Sending Methods

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

### Chaining Modifiers

```python
# @User
await adapter.Send.To("group", "456").At("789").Text("Hello")

# @All Members
await adapter.Send.To("group", "456").AtAll().Text("Hello everyone")

# Reply to message
await adapter.Send.To("group", "456").Reply("msg_id").Text("Reply content")

# Compose multiple actions
await adapter.Send.To("group", "456").At("789").Reply("msg_id").Text("Reply to @ message")
```

## API Calls

### call_api Method

> **Note**: `call_api` is a low-level method for directly calling the platform-native API; parameters and return values may differ across platforms, please refer to the corresponding platform adapter documentation. **It is recommended to use the Send DSL to send messages**, and only use `call_api` in scenarios where the Send DSL is not supported (such as retrieving platform-specific data, calling platform management interfaces, etc.).

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
from ErisPulse import sdk
from ErisPulse.Core import BaseAdapter

class MyAdapter(BaseAdapter):
    def __init__(self):
        super().__init__()
        self.sdk = sdk
        # Initialize the adapter
        pass
    
    async def start(self):
        """Start the adapter (must be implemented)"""
        pass
    
    async def shutdown(self):
        """Shutdown the adapter (must be implemented)"""
        pass
    
    async def call_api(self, endpoint: str, **params):
        """Call platform API (must be implemented)"""
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

## Bot Status Management

Adapters inform the framework of the Bot's connection status by sending OneBot12 standard **`meta` events**. The system automatically extracts Bot information from these events for status tracking.

### meta Event Types

Adapters should send the following three `meta` events:

| `type` | `detail_type` | Description | Trigger Timing |
|--------|--------------|-------------|----------------|
| `meta` | `connect` | Bot connects online | After the adapter successfully establishes a connection with the platform |
| `meta` | `heartbeat` | Bot heartbeat | Sent periodically (recommended every 30-60 seconds) |
| `meta` | `disconnect` | Bot disconnects | When a connection break is detected |

### self Field Extension

ErisPulse extends the standard OneBot12 `self` field with the following optional fields:

| Field | Type | Description |
|-------|------|-------------|
| `self.platform` | string | Platform name (OB12 standard) |
| `self.user_id` | string | Bot user ID (OB12 standard) |
| `self.user_name` | string | Bot nickname (ErisPulse extension) |
| `self.avatar` | string | Bot avatar URL (ErisPulse extension) |
| `self.account_id` | string | Multi-account identifier (ErisPulse extension) |

### meta Event Format

#### connect — Connection Online

```python
await adapter.emit({
    "id": "unique_id",
    "time": 1712345678,
    "type": "meta",
    "detail_type": "connect",
    "platform": "telegram",
    "self": {
        "platform": "telegram",
        "user_id": "123456",
        "user_name": "MyBot",
        "avatar": "https://example.com/avatar.jpg"
    },
    "telegram_raw": {...},
    "telegram_raw_type": "bot_connected"
})
```

System handling: Register the Bot, mark as `online`, trigger the `adapter.bot.online` lifecycle event.

#### heartbeat — Heartbeat

```python
await adapter.emit({
    "id": "unique_id",
    "time": 1712345708,
    "type": "meta",
    "detail_type": "heartbeat",
    "platform": "telegram",
    "self": {
        "platform": "telegram",
        "user_id": "123456"
    }
})
```

System handling: Update `last_active` time (also supports updating metadata in the heartbeat).

#### disconnect — Disconnection

```python
await adapter.emit({
    "id": "unique_id",
    "time": 1712345738,
    "type": "meta",
    "detail_type": "disconnect",
    "platform": "telegram",
    "self": {
        "platform": "telegram",
        "user_id": "123456"
    }
})
```

System handling: Mark the Bot as `offline`, trigger the `adapter.bot.offline` lifecycle event.

### Automatic Discovery of Regular Events

In addition to `meta` events, the `self` field in regular events (`message`/`notice`/`request`) will also automatically discover and register the Bot, updating the active time. This means that even if the adapter does not send a `connect` event, the framework can detect the Bot from the first regular event.

### Adapter Integration Example

```python
class MyAdapter(BaseAdapter):
    async def start(self):
        # Establish connection with the platform...
        connection = await self._connect()
        
        # Connection successful, send connect event
        await adapter.emit({
            "id": str(uuid4()),
            "time": int(time.time()),
            "type": "meta",
            "detail_type": "connect",
            "platform": "myplatform",
            "self": {
                "platform": "myplatform",
                "user_id": self.bot_id,
                "user_name": self.bot_name,
                "avatar": self.bot_avatar
            },
            "myplatform_raw": raw_data,
            "myplatform_raw_type": "connected"
        })
    
    async def on_disconnect(self):
        # Disconnection, send disconnect event
        await adapter.emit({
            "id": str(uuid4()),
            "time": int(time.time()),
            "type": "meta",
            "detail_type": "disconnect",
            "platform": "myplatform",
            "self": {
                "platform": "myplatform",
                "user_id": self.bot_id
            }
        })
```

### Querying Bot Status

```python
# Get complete status of all adapters and Bots (WebUI friendly)
summary = sdk.adapter.get_status_summary()
# {
#     "adapters": {
#         "telegram": {
#             "status": "started",
#             "bots": {
#                 "123456": {
#                     "status": "online",
#                     "last_active": 1712345678.0,
#                     "info": {"nickname": "MyBot"}
#                 }
#             }
#         }
#     }
# }

# List all Bots
all_bots = sdk.adapter.list_bots()

# List Bots of a specific platform
tg_bots = sdk.adapter.list_bots("telegram")

# Get details of a single Bot
info = sdk.adapter.get_bot_info("telegram", "123456")

# Check if a Bot is online
if sdk.adapter.is_bot_online("telegram", "123456"):
    print("Bot is online")
```

### Bot Status Values

| Status | Description |
|--------|-------------|
| `online` | Online (continuously receiving events or actively marked by the adapter) |
| `offline` | Offline (actively marked by the adapter or automatically set when the system shuts down) |
| `unknown` | Unknown (registered but status not confirmed) |

### Lifecycle Events

| Event Name | Trigger Timing | Data |
|------------|----------------|------|
| `adapter.bot.online` | First automatic discovery of a new Bot | `{platform, bot_id, status}` |
| `adapter.status.change` | Adapter status change (starting/started/stopping/stopped/stop_failed) | `{platform, status}` |

```python
# Listen for Bot online event
@sdk.lifecycle.on("adapter.bot.online")
def on_bot_online(event):
    print(f"Bot online: {event['data']['platform']}/{event['data']['bot_id']}")

# Listen for adapter status change
@sdk.lifecycle.on("adapter.status.change")
def on_status_change(event):
    print(f"Adapter status: {event['data']['platform']} -> {event['data']['status']}")
```

> When the system shuts down (`shutdown`), all Bots are automatically marked as `offline`.

## Related Documentation

- [Core Modules API](../docs/en/core-modules.md) - Core Modules API
- [Event System API](../docs/en/event-system.md) - Event Module API
- [Adapter Development Guide](../developer-guide/adapters/) - Developing Platform Adapters