# Adapter System API

> [!TIP]
> **When to read this**: Refer to this document when you need to manage adapters (getting instances, starting/stopping them, checking Bot online status), send messages using the Send DSL, register middleware, or integrate Bot status reporting (meta events) into an adapter. Skip it otherwise.

This document provides a detailed introduction to the ErisPulse adapter system API.

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
> In general, it is recommended to use the `Event` module for event listening/processing;
>
> Meanwhile, the `Event` module provides powerful wrappers that can bring more convenience to your module development

```python
# Listen for OneBot12 standard events
@sdk.adapter.on("message")
async def handle_message(event):
    pass

# Listen for standard events from a specific platform
@sdk.adapter.on("message", platform="yunhu")
async def handle_yunhu_message(event):
    pass

# Listen for platform native events
@sdk.adapter.on("raw_event", raw=True, platform="yunhu")
async def handle_raw_event(data):
    pass
```

### Adapter Management

```python
# Get all platforms
platforms = sdk.adapter.platforms

# Check whether an adapter exists
exists = sdk.adapter.exists("platform_name")

# Enable/disable an adapter
sdk.adapter.enable("platform_name")
sdk.adapter.disable("platform_name")

# Start/shut down adapters
# The methods below only show usage with arguments; calling them without arguments starts/stops all registered adapters
await sdk.adapter.startup(["platform1", "platform2"])
await sdk.adapter.shutdown(["platform1", "platform2"])

# Check whether an adapter is running
is_running = sdk.adapter.is_running("platform_name")

# List all running adapters
running = sdk.adapter.list_running()

# Read adapter metadata (aligned with module.get_meta, for consumption by the panel / marketplace, etc.)
info = sdk.adapter.get_info("platform_name")   # Registration info (meta + class name, json-safe)
meta = sdk.adapter.get_meta("platform_name")   # Descriptive metadata (description supports i18n resolution)
raw = sdk.adapter.get_meta("platform_name", resolve_i18n=False)  # Pass through the raw i18n dict
```

## Middleware

Middleware executes before events are dispatched to handlers, allowing you to modify, filter, or log event data.

### Registering Middleware

```python
@sdk.adapter.middleware
async def my_middleware(event):
    sdk.logger.info(f"Middleware processing: {event}")
    return event
```

### Middleware Execution Model

- **Execution order**: Middleware executes in registration order (first registered, first executed)
- **Data passing**: Each middleware receives the `event` data returned by the previous middleware; if a middleware returns `None`, that return value is ignored and the original data continues to be passed along (with a `warning`-level log emitted)
- **Data modification**: Middleware can modify event data and return the modified dict
- **Event veto**: When a middleware explicitly returns `False`, the event is vetoed — the event is dropped, enters no handlers, and produces no outbound side effects; the veto emits a TRACE log and triggers the `adapter.event.blocked` lifecycle hook (carrying the middleware name and the full event)

```python
@sdk.adapter.middleware
async def add_timestamp(event):
    event["processed_at"] = time.time()
    return event

@sdk.adapter.middleware
async def filter_spam(event):
    if event.get("detail_type") == "private":
        text = event.get("alt_message", "")
        if "spam ads" in text:
            return False  # Veto: the event is dropped and enters no handlers
    return event
```

> **Note**: Only an explicit return of `False` vetoes an event (returning falsy values such as an empty dict / `0` / `""` does not veto);
> returning `None` still lets the event through with the payload unchanged. Vetoed events can be audited and investigated
> by listening to the `adapter.event.blocked` hook to figure out "why an event got no response".

## Sending Messages with Send

### Basic Sending

```python
# Get the adapter
adapter = sdk.adapter.get("platform")

# Send a text message
await adapter.Send.To("user", "123").Text("Hello")

# Send an image message
await adapter.Send.To("group", "456").Image("https://example.com/image.jpg")
```

### Specifying the Sending Account

```python
# Use an account name
await adapter.Send.Using("account1").To("user", "123").Text("Hello")

# Use an account ID
await adapter.Send.Using("bot_id").To("user", "123").Text("Hello")
```

### Querying Supported Send Methods

```python
# List all send methods supported by a platform
methods = sdk.adapter.list_sends("onebot11")
# Returns: ["Text", "Image", "Voice", "Markdown", ...]

# Get detailed information about a method
info = sdk.adapter.send_info("onebot11", "Text")
# Returns:
# {
#     "name": "Text",
#     "parameters": [
#         {"name": "text", "type": "str", "default": null, "annotation": "str"}
#     ],
#     "return_type": "Awaitable[Any]",
#     "docstring": "Send a text message..."
# }
```

### Chained Modifiers

```python
# @a user
await adapter.Send.To("group", "456").At("789").Text("Hello")

# @all members
await adapter.Send.To("group", "456").AtAll().Text("Hello everyone")

# Reply to a message
await adapter.Send.To("group", "456").Reply("msg_id").Text("Reply content")

# Combined usage
await adapter.Send.To("group", "456").At("789").Reply("msg_id").Text("Reply to the mentioned message")
```

## API Calls

### The call_api Method

> **Note**: `call_api` is a low-level method that directly calls the platform's native API; parameters and return values may differ across platforms, so refer to the corresponding platform adapter documentation. **Using the Send DSL to send messages is recommended**; only use `call_api` in scenarios not supported by the Send DSL (e.g., fetching platform-specific data or calling platform management APIs).

```python
# Call a platform API
result = await adapter.call_api(
    endpoint="/send",
    content="Hello",
    recvId="123",
    recvType="user"
)

# Normalized response
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
        """Shut down the adapter (must be implemented)"""
        pass
    
    async def call_api(self, endpoint: str, **params):
        """Call a platform API (must be implemented)"""
        pass
```

### The Send Nested Class

```python
class MyAdapter(BaseAdapter):
    class Send(BaseAdapter.Send):
        def Text(self, text: str):
            """Send a text message"""
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

Adapters inform the framework of a Bot's connection status by sending OneBot12-standard **`meta` events**. The system automatically extracts Bot information from them for status tracking.

### Meta Event Reporting

Adapters report Bot status via `meta` events, with three `detail_type` values: `connect` (register as online), `heartbeat` (keep-alive), and `disconnect` (mark as offline). Sending with the one-liner `emit_meta()` is recommended; even if no meta events are sent, the framework will automatically discover Bots from the `self` field of ordinary events (message/notice/request).

- For the **meta event format and how to send them** (when to send, `emit_meta()` usage, manual construction format), see [Adapter Best Practices - Bot Status Management and Meta Events](../developer-guide/adapters/best-practices.md#bot-status-management-and-meta-events)
- For the **auto-discovery mechanism and framework behavior**, see [Adapter Core Concepts - Bot Status Management](../developer-guide/adapters/core-concepts.md#bot-status-management)

### Querying Bot Status

```python
# Get the full status of all adapters and Bots (WebUI-friendly)
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

# List Bots on a specific platform
tg_bots = sdk.adapter.list_bots("telegram")

# Get details of a single Bot
info = sdk.adapter.get_bot_info("telegram", "123456")

# Check whether a Bot is online
if sdk.adapter.is_bot_online("telegram", "123456"):
    print("Bot is online")
```

### Bot Status Values

| Status | Description |
|--------|-------------|
| `online` | Online (continuously receiving events or actively marked by the adapter) |
| `offline` | Offline (actively marked by the adapter or set automatically at system shutdown) |
| `unknown` | Unknown (registered only, status not yet confirmed) |

### Lifecycle Events

| Event Name | Trigger | Data |
|------------|---------|------|
| `adapter.bot.online` | A new Bot is automatically discovered for the first time | `{platform, bot_id, status}` |
| `adapter.status.change` | Adapter status changes | `{platform, status}`; full set of status values: `starting` / `started` / `start_failed` / `stopping` / `stopped` / `stop_failed` / `skipped-dependency` (startup skipped because a dependent adapter was not ready) / `disabled` (disabled via configuration) |

```python
# Listen for the Bot online event
@sdk.lifecycle.on("adapter.bot.online")
def on_bot_online(event):
    print(f"Bot online: {event['data']['platform']}/{event['data']['bot_id']}")

# Listen for adapter status changes
@sdk.lifecycle.on("adapter.status.change")
def on_status_change(event):
    print(f"Adapter status: {event['data']['platform']} -> {event['data']['status']}")
```

> At system shutdown (`shutdown`), all Bots are automatically marked as `offline`.

## Related Documentation

**Continue exploring the API**:
- [Core Modules API](core-modules.md) - Core module APIs
- [Event System API](event-system.md) - Event module API

**Start writing adapters**:
- [Adapter Development Guide](../developer-guide/adapters/) - Developing platform adapters
- [Adapter Standardization Guide (Overview)](../standards/standardization-guide.md) - Standards reference and checklist before implementing a new adapter