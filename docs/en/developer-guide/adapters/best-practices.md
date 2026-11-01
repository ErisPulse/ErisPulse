# Adapter Development Best Practices

> [!TIP]
> **When to read this**: Recommended reading after your adapter skeleton is up and running (engineering best practices). Feel free to skip it if not needed—it won't affect the use of other features.

This document consolidates the engineering conventions for adapter development: Bot status reporting, connection retry and heartbeat, multi-account resolution, and standardized error responses. Following them helps you avoid common platform integration problems such as silent disconnects, sending to the wrong target in multi-account setups, and errors that are hard to locate.

## Bot Status Management and Meta Events

Adapters should proactively send meta events via `adapter.emit()` so that the framework can automatically track each Bot's connection state, online/offline status, and heartbeat information.

### 1. When to Send Meta Events

| Event | `detail_type` | Trigger | Framework Behavior |
|------|--------------|---------|---------|
| Connect | `"connect"` | When the Bot establishes a connection with the platform | Registers the Bot and triggers the `adapter.bot.online` lifecycle event |
| Disconnect | `"disconnect"` | When the Bot disconnects from the platform | Marks the Bot offline and triggers the `adapter.bot.offline` lifecycle event |
| Heartbeat | `"heartbeat"` | Sent periodically (every 30-60 seconds recommended) | Updates the Bot's active time and metadata |

### 2. Sending Meta Events

The framework provides the `emit_meta()` method, which sends a meta event in a single line:

```python
class MyAdapter(BaseAdapter):
    async def _ws_handler(self, websocket):
        bot_id = self._get_bot_id()

        # Bot online: send the connect event in one line
        await self.emit_meta("connect", bot_id, user_name="MyBot", nickname="My Bot")

        try:
            while True:
                data = await websocket.receive_text()
                event = self.convert(data)
                if event:
                    await self.adapter.emit(event)
        except WebSocketDisconnect:
            pass
        finally:
            # Bot offline
            await self.emit_meta("disconnect", bot_id)
```

You can also manually construct a standard meta event (the legacy approach remains compatible):

```python
await self.adapter.emit({
    "id": str(uuid4()),
    "time": int(time.time()),
    "type": "meta",
    "detail_type": "connect",
    "platform": "myplatform",
    "self": {
        "platform": "myplatform",
        "user_id": bot_id,
        "user_name": "MyBot",
        "avatar": "https://example.com/avatar.jpg",
    },
    "myplatform_raw": raw_data,
    "myplatform_raw_type": "connected",
})
```

### 3. Heartbeat Events

While the connection is alive, the adapter should periodically send heartbeat events to update the Bot's active time:

```python
class MyAdapter(BaseAdapter):
    async def _heartbeat_loop(self, bot_id: str):
        while self._connected:
            # Send a meta heartbeat to the framework (done in one line)
            await self.emit_meta("heartbeat", bot_id)
            await asyncio.sleep(30)
```

### 4. Automatic `self` Field Discovery

The framework's `adapter.emit()` automatically processes the `self` field in all events (not just meta events):

- The `self` field in **regular events** (message/notice/request) is automatically discovered and used to register the Bot
- **Extended `self` field info**: the optional fields `user_name`, `nickname`, `avatar`, and `account_id` are supported

```python
# Simply include the self field in the converter to register the Bot automatically
onebot_event = {
    "type": "message",
    "detail_type": "private",
    "platform": "myplatform",
    "self": {
        "platform": "myplatform",
        "user_id": "bot123",
        "user_name": "MyBot",
        "nickname": "My Bot",
    },
    # ... other fields
}
await self.adapter.emit(onebot_event)
# Bot "bot123" has been automatically registered and its active time updated
```

### 5. Bot Status Query

For the query APIs (`get_bot_info()` / `list_bots()` / `is_bot_online()` / `get_status_summary()`) and the Bot lifecycle event table, see [Adapter System API - Bot Status Management](../../api-reference/adapter-system.md#bot-status-management).

## Connection Management

### 1. Implementing Connection Retry

```python
import asyncio

class MyAdapter(BaseAdapter):
    async def start(self):
        retry_count = 0
        max_retries = 5
        
        while retry_count < max_retries:
            try:
                await self._connect_to_platform()
                self.logger.info("Connection successful")
                break
            except Exception as e:
                retry_count += 1
                if retry_count < max_retries:
                    # Exponential backoff strategy
                    wait_time = min(60 * (2 ** retry_count), 600)
                    self.logger.warning(
                        f"Connection failed, retrying in {wait_time} seconds ({retry_count}/{max_retries}): {e}"
                    )
                    await asyncio.sleep(wait_time)
                else:
                    self.logger.error("Connection failed, maximum retries reached")
                    raise
```

### 2. Connection State Management

```python
class MyAdapter(BaseAdapter):
    async def start(self):
        self.connection = None
        self._connected = False
    
    async def _ws_handler(self, websocket: WebSocket):
        self.connection = websocket
        self._connected = True
        self.logger.info("Connection established")
        
        try:
            while True:
                data = await websocket.receive_text()
                await self._process_event(data)
        except WebSocketDisconnect:
            self.logger.info("Connection closed")
        finally:
            self.connection = None
            self._connected = False
```

### 3. Heartbeat Keep-Alive and Meta Heartbeat

The adapter's heartbeat should accomplish two tasks at once: sending a keep-alive heartbeat to the platform and sending a meta heartbeat event to the framework.

```python
class MyAdapter(BaseAdapter):
    async def start(self):
        self.connection = await self._connect_to_platform()
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())

    async def _heartbeat_loop(self):
        while self.connection:
            try:
                # 1. Send a keep-alive heartbeat to the platform
                await self.connection.send_json({"type": "ping"})

                # 2. Send a meta heartbeat to the framework (one line with emit_meta)
                await self.emit_meta("heartbeat", self._bot_id)

                await asyncio.sleep(30)
            except Exception as e:
                self.logger.error(f"Heartbeat failed: {e}")
                break
```

### 4. Exposing Connection Info

Routes registered by the adapter should be visible to users so they can configure the platform-side callback URL. It is recommended to proactively log connection info in `start()`:

```python
class MyAdapter(BaseAdapter):
    async def start(self):
        router.register_websocket(
            module_name=self.platform,
            path="/ws",
            handler=self._ws_handler
        )

        if self.sdk:
            info = self.sdk.adapter.get_connection_info(self.platform)
            if info:
                self.logger.info(f"WebSocket URL: "
                    f"{info.get('connection', {}).get('base_url', '')}"
                    f"{info.get('connection', {}).get('websocket_routes', [])}")
```

Users can view all adapter routes and connection URLs via the following APIs:

```python
from ErisPulse import sdk

# Adapter-level connection info (recommended)
info = sdk.adapter.get_connection_info("myplatform")

# Route manager-level queries
sdk.router.list_namespaces()              # List all namespaces
sdk.router.get_module_routes("myplatform")  # Detailed route info
sdk.router.get_module_urls("myplatform")    # Full connection URLs
```

> **Note**: The `module_name` used at route registration must exactly match the adapter's `platform` name registered in ErisPulse; otherwise `get_connection_info()` will fail to associate the routes. Multi-account adapters should register a sub-path for each account (e.g., `/account1/webhook`, `/account2/webhook`) instead of using different `module_name` values.

### 5. HTTP Route Lifecycle

The lifecycle of HTTP/WebSocket routes registered by adapters/modules via `router` is automatically managed by the framework based on the **ownership principle**:

- The `module_name` (namespace) at registration time is the ownership identifier. **On reload / stop / unload, the framework automatically cleans up all routes and connection resources under that ownership**, so no manual unregistration is needed
- Therefore, **routes must be unconditionally re-registered in `start()` (`on_load` for modules)**. Do not optimize with instance-level boolean flags to "register only once": config hot reload (e.g., account field changes saved instantly) triggers stop/start while **reusing the same instance**, and leftover flags will cause routes to be **permanently lost** after cleanup, manifesting as 404s on endpoints that persist until the process restarts

```python
class MyAdapter(BaseAdapter):
    async def start(self):
        # Unconditionally re-register on every startup (after reload, routes have been auto-cleaned with the previous stop)
        router.register_http_route(self.platform, "/qr/start", self._qr_start, methods=["POST"])
        router.register_http_route(self.platform, "/qr/poll", self._qr_poll, methods=["POST"])
```

The same applies on the module side (register in `on_load`):

```python
class MyModule(BaseModule):
    async def on_load(self):
        router.register_http_route("MyModule", "/api/panel", self._panel, methods=["GET"])
```

When you need to **manually unload routes in advance** (e.g., dynamically taking an entry point offline), you can actively unregister them:

```python
from ErisPulse.Core import router

router.unregister_http_route(self.platform, "/qr/start")
```

- Frontend/callers may receive route 404s during the hot-reload window; this is transient. For browser-facing interactive pages, a limited number of automatic retries on 404 is recommended

## Event Conversion

### 1. Strictly Follow the OneBot12 Standard

```python
class MyPlatformConverter:
    def convert(self, raw_event):
        """Convert an event"""
        onebot_event = {
            "id": str(raw_event.get("event_id", uuid.uuid4())),
            "time": int(time.time()),
            "type": self._convert_type(raw_event.get("type")),
            "detail_type": self._convert_detail_type(raw_event),
            "platform": "myplatform",
            "self": {
                "platform": "myplatform",
                "user_id": str(raw_event.get("bot_id", ""))
            },
            "myplatform_raw": raw_event,  # Keep the raw data (required)
            "myplatform_raw_type": raw_event.get("type", "")  # Raw type (required)
        }
        return onebot_event
```

### 2. Timestamp Normalization

```python
def _convert_timestamp(self, timestamp):
    """Convert to a 10-digit second-level timestamp"""
    if not timestamp:
        return int(time.time())
    
    # If it's a millisecond-level timestamp
    if timestamp > 10**12:
        return int(timestamp / 1000)
    
    # If it's a second-level timestamp
    return int(timestamp)
```

### 3. Event ID Generation

```python
import uuid

def _generate_event_id(self, raw_event):
    """Generate an event ID"""
    event_id = raw_event.get("event_id")
    if event_id:
        return str(event_id)
    # If the platform doesn't provide an ID, generate a UUID
    return str(uuid.uuid4())
```

## SendDSL Implementation

The `At`/`AtAll`/`Reply` modifiers are built into the framework's SendDSL base class; the adapter only needs to implement `Raw_ob12` and the concrete send methods. Use `self._apply_modifiers(message)` and `self.send_context` to simplify development.

### 1. Must Return a Task Object

```python
class Send(BaseAdapter.Send):
    def Raw_ob12(self, message, **kwargs):
        """Recommended implementation: use the framework helper methods"""
        async def _do_send():
            segments = self._apply_modifiers(message)
            return await self._adapter.call_api(
                endpoint="/send_message",
                message=segments,
                **self.send_context,
                **kwargs
            )
        return asyncio.create_task(_do_send())

    def Text(self, text: str):
        return self.Raw_ob12([{"type": "text", "data": {"text": text}}])
```

### 2. Chained Modifier Methods Return self

```python
class Send(BaseAdapter.Send):

    def __init__(self, adapter, target_type=None, target_id=None, account_id=None):
        super().__init__(adapter, target_type, target_id, account_id)
        self.buttons = []

    def Button(self, content: list) -> 'Send':
        self.buttons.append(content)
        return self # Return self
```

### 3. Support Platform-Specific Methods

```python
class Send(BaseAdapter.Send):
    def Sticker(self, sticker_id: str):
        """Send a sticker"""
        return asyncio.create_task(
            self._adapter.call_api(
                endpoint="/send_sticker",
                message=[{"type": "sticker", "data": {"id": sticker_id}}],
                **self.send_context
            )
        )
    
    def Card(self, card_data: dict):
        """Send a card message"""
        return asyncio.create_task(
            self._adapter.call_api(
                endpoint="/send_card",
                message=[{"type": "card", "data": card_data}],
                **self.send_context
            )
        )
```

## API Responses

### 1. Standardized Response Format

The framework provides the `make_response()` and `make_error()` methods to build standardized responses:

```python
async def call_api(self, endpoint: str, **params):
    try:
        raw_response = await self._platform_api_call(endpoint, **params)
        
        if raw_response.get("success"):
            return self.make_response(
                data=raw_response.get("data"),
                message_id=raw_response.get("data", {}).get("message_id", ""),
                raw=raw_response,
            )
        else:
            return self.make_error(
                retcode=raw_response.get("code", 10001),
                message=raw_response.get("message", ""),
                raw=raw_response,
            )
    except Exception as e:
        return self.make_error(message=str(e))
```

`make_response()` automatically generates a response dict containing the `{platform}_raw` key. `make_error()` uses `retcode=34000` (Platform Error) by default.

### 2. Error Code Conventions

Follow the OneBot12 standard error codes:

```python
# 1xxxx - Action request errors
10001: Bad Request
10002: Unsupported Action
10003: Bad Param

# 2xxxx - Action handler errors
20001: Bad Handler
20002: Internal Handler Error

# 3xxxx - Action execution errors
31000: Database Error
32000: Filesystem Error
33000: Network Error
34000: Platform Error
35000: Logic Error
```

## Multi-Account Support

### 1. Declarative Configuration (Recommended)

After declaring a config class with `AccountConfigClass`, the framework automatically manages multi-account loading, validation, and template generation. The `BotAccountConfig` base class provides the `enabled` and `name` fields, so adapters don't need to declare them:

```python
from dataclasses import dataclass, field
from ErisPulse.Core.Bases import BotAccountConfig

@dataclass
class MyBotConfig(BotAccountConfig):
    token: str = field(default="", metadata={
        "description": {"i18n": "my_adapter.bot_token", "default": "Bot Token"},
        "required": True,
        "secret": True,
    })

class MyAdapter(BaseAdapter):
    AccountConfigClass = MyBotConfig
    
    async def start(self):
        for name, account in self.enabled_accounts.items():
            self.logger.info(f"Starting account {name}")
            await self._connect(name, account.token)
            # bot_id is automatically obtained from the platform protocol/login response and filled in by the framework
    
    async def call_api(self, endpoint: str, **params):
        account_id = params.pop("account_id", None)
        name, account = self._resolve_account(account_id)
        # name: account name, account: MyBotConfig instance
```

The configuration file is automatically generated as:

```toml
[MyAdapter.accounts.default]
token = ""
enabled = true
name = ""
```

### 2. Account Resolution Mechanism

The framework provides a built-in `_resolve_account()` method with the following matching priority:

1. **Account name** — exact match against the config key name
2. **`bot_id` field** — the automatically obtained bot_id (i.e., `event["self"]["user_id"]`)
3. **Any str field** — other string fields in the config
4. **Fallback** — the first enabled account

```python
# Match by account name
name, account = self._resolve_account("account1")

# Match by bot_id (most common approach, from the event)
name, account = self._resolve_account("bot_123")

# Get the first enabled account (pass None)
name, account = self._resolve_account(None)
```

## Error Handling

### 1. Categorized Exception Handling

Use `make_error()` to build standardized error responses. When making requests through `sdk.client`, catch ErisPulse exceptions:

```python
from ErisPulse.Core.Bases.errors import ClientError, ClientTimeoutError

async def call_api(self, endpoint: str, **params):
    try:
        from ErisPulse.Core import client
        resp = await client.post(
            f"https://api.platform.com/{endpoint}",
            json=params,
            max_retries=2,
        )
        response = await resp.json()
        return self.make_response(data=response, raw=response)
    except ClientTimeoutError:
        self.logger.error(f"Request timed out: {endpoint}")
        return self.make_error(retcode=32000, message="Request timed out")
    except ClientError as e:
        self.logger.error(f"Network error: {e}")
        return self.make_error(retcode=33000, message="Network request failed")
    except json.JSONDecodeError:
        self.logger.error("JSON parsing failed")
        return self.make_error(retcode=10006, message="Invalid response format")
    except Exception as e:
        self.logger.error(f"Unknown error: {e}", exc_info=True)
        return self.make_error(message=str(e))
```

> **Backward compatibility**: Legacy adapter code that uses `aiohttp` directly is unaffected and can still catch `aiohttp.ClientError`. Exception conversion only takes effect for requests made through `sdk.client`.

### 2. Logging

The framework automatically creates a child logger for each adapter (`sdk.logger.get_child("MyAdapter")`), so no manual initialization is needed:

```python
class MyAdapter(BaseAdapter):
    # ConfigClass = ...  # self.logger is automatically available after declaring a config class
    
    async def start(self):
        self.logger.info("Adapter starting...")
        # ...
        self.logger.info("Adapter started")
    
    async def shutdown(self):
        self.logger.info("Adapter shutting down...")
        # ...
        self.logger.info("Adapter shutdown complete")
```

## Testing

### 1. Unit Testing

```python
import pytest
from ErisPulse.Core.Bases import BaseAdapter

class TestMyAdapter:
    def test_converter(self):
        """Test the converter"""
        converter = MyPlatformConverter()
        raw_event = {"type": "message", "content": "Hello"}
        result = converter.convert(raw_event)
        assert result is not None
        assert result["platform"] == "myplatform"
        assert "myplatform_raw" in result
    
    def test_api_response(self):
        """Test the API response format"""
        adapter = MyAdapter()
        response = adapter.call_api("/test", param="value")
        assert "status" in response
        assert "retcode" in response
```

### 2. Integration Testing

```python
@pytest.mark.asyncio
async def test_adapter_start():
    """Test adapter startup"""
    adapter = MyAdapter()
    await adapter.start()
    assert adapter._connected is True

@pytest.mark.asyncio
async def test_send_message():
    """Test sending a message"""
    adapter = MyAdapter()
    await adapter.start()
    
    result = await adapter.Send.To("user", "123").Text("Hello")
    assert result is not None
```

## Reverse Conversion and Message Building

`Raw_ob12` is a method that adapters **must implement**; it is the unified entry point for reverse conversion (OneBot12 → platform). Standard methods (`Text`, `Image`, etc.) should delegate to `Raw_ob12`, and modifier state (`At`/`Reply`/`AtAll`) must be merged into message segments within `Raw_ob12`.

`MessageBuilder` is a message segment building tool used together with `Raw_ob12`, supporting chained calls and quick construction.

> For the complete implementation specification, code examples, and usage, see:
> - [Send Method Spec §6 Reverse Conversion Spec](../../standards/send-method-spec.md#6-reverse-conversion-spec-onebot12--platform)
> - [Send Method Spec §11 Message Builder](../../standards/send-method-spec.md#11-message-builder-messagebuilder)

## Platform Event Method Extensions

Adapters can register platform-specific methods on the Event wrapper classes, allowing module developers to access platform-specific data more conveniently.

### 1. Batch Registration with a Mixin Class (Recommended)

When the platform has multiple specific methods, using a Mixin class is recommended:

```python
# Register at the adapter's start() or at module level
from ErisPulse.Core.Event import register_event_mixin

class MyPlatformEventMixin:
    def get_chat_name(self):
        """Get the chat name"""
        return self.get("myplatform_raw", {}).get("chat", {}).get("name", "")

    def is_official_message(self):
        """Check whether the message is official"""
        raw = self.get("myplatform_raw", {})
        return raw.get("sender", {}).get("is_official", False)

    def get_message_type(self):
        """Get the platform message type"""
        return self.get("myplatform_raw", {}).get("msg_type", "text")

# Batch registration
register_event_mixin("myplatform", MyPlatformEventMixin)
```

### 2. Registering a Single Method with a Decorator

```python
from ErisPulse.Core.Event import register_event_method

@register_event_method("myplatform")
def get_chat_name(self):
    return self.get("myplatform_raw", {}).get("chat", {}).get("name", "")
```

### 3. Cleanup on Adapter Shutdown

```python
from ErisPulse.Core.Event import unregister_platform_event_methods

class MyAdapter(BaseAdapter):
    async def shutdown(self):
        # Clean up platform event method registrations
        unregister_platform_event_methods("myplatform")
        # ... other cleanup
```

> For more details on registration and unregistration, see [Event System API - Registering Platform Extension Methods](../../api-reference/event-system.md#adapter-registered-platform-extension-methods).

## Documentation Maintenance

### 1. Maintain Platform Feature Documentation

Create the `{platform}.md` documentation under `docs/en/platform-guide/` (versions in other languages are generated automatically):

```markdown
# Platform Name Adapter Documentation

## Basic Information
- Module version: 1.0.0
- Maintainer: Your Name

## Supported Message Send Types
...

## Platform-Specific Event Types
...

## Configuration Options
...
```

### 2. Update Version Information

When releasing a new version, update the version information in the documentation:

```toml
[project]
version = "2.0.0"  # Update the version number
```

## Related Documentation

### Review the Prerequisites

- [Adapter Development Getting Started](getting-started.md) - Create your first adapter
- [Adapter Core Concepts](core-concepts.md) - Understand the adapter architecture
- [SendDSL in Depth](send-dsl.md) - Learn message sending

### After Your Adapter Is Complete

- [Publishing and Module Store Guide](../publishing.md) - Publish to PyPI and the Module Store