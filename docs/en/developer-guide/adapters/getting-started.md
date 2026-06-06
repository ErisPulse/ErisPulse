# Getting Started with Adapter Development

This guide helps you get started with developing ErisPulse adapters to connect new messaging platforms.

## Adapter Introduction

### What is an Adapter

The adapter is a bridge between ErisPulse and various messaging platforms, responsible for:

1. **Forward Conversion**: Receiving platform events and converting them to OneBot12 standard format (Converter)
2. **Reverse Conversion**: Converting OneBot12 message segments to platform API calls (`Raw_ob12`)
3. Managing connections with the platform (WebSocket/WebHook)
4. Providing a unified SendDSL message sending interface

### Adapter Architecture

```
Forward Conversion (Receive)                 Reverse Conversion (Send)
────────────────────────                 ────────────────────────
Platform Event                             Module Building Message
    ↓                                          ↓
Converter.convert()                    Send.Raw_ob12()
    ↓                                          ↓
OneBot12 Standard Event              Platform Native API Call
    ↓                                          ↓
Event System                            Standard Response Format
    ↓
Module Processing
```

## Directory Structure

Standard adapter package structure:

```
MyAdapter/
├── pyproject.toml          # Project configuration
├── README.md               # Project description
├── LICENSE                 # License
└── MyAdapter/
    ├── __init__.py          # Package entry
    ├── Core.py               # Adapter main class
    └── Converter.py          # Event converter
```

## Quick Start

### 1. Create Project

```bash
mkdir MyAdapter && cd MyAdapter
```

### 2. Create pyproject.toml

```toml
[project]
name = "ErisPulse-MyAdapter"
version = "1.0.0"
description = "MyAdapter platform adapter"
readme = "README.md"
requires-python = ">=3.10"
license = { file = "LICENSE" }
authors = [ { name = "yourname", email = "your@mail.com" } ]

dependencies = [
    "ErisPulse>=2.4.0"  # ErisPulse already includes aiohttp built-in, usually no need for separate dependency
]

[project.urls]
"homepage" = "https://github.com/yourname/MyAdapter"

[project.entry-points."erispulse.adapter"]
"MyAdapter" = "MyAdapter:MyAdapter"
```

### 3. Create Adapter Main Class

The framework provides `ConfigClass` / `AccountConfigClass` declarative configuration management. The adapter only needs to declare the configuration class to automatically load, validate, and generate configuration templates.

```python
# MyAdapter/Core.py
from dataclasses import dataclass, field
from ErisPulse.Core import BaseAdapter
from ErisPulse.runtime.config_schema import AdapterConfig

@dataclass
class MyAdapterConfig(AdapterConfig):
    """MyAdapter configuration"""
    api_endpoint: str = field(
        default="https://api.example.com",
        metadata={
            "description": "API endpoint",
            "required": False,
            "webui": {"widget": "text", "group": "connection", "order": 1},
        },
    )
    token: str = field(
        default="",
        metadata={
            "description": "Platform token",
            "required": True,
            "secret": True,
            "webui": {"widget": "password", "group": "basic", "order": 2},
        },
    )

class MyAdapter(BaseAdapter):
    ConfigClass = MyAdapterConfig  # Declare the configuration class, framework manages automatically
    
    # No need to override __init__! Framework handles automatically:
    # - self.sdk / self.logger are automatically set
    # - self.config is automatically loaded
    # - self.Send / self.Request are automatically initialized
    
    def _setup_converter(self):
        from .Converter import MyPlatformConverter
        return MyPlatformConverter()
```

> ⚠️ **About `__init__`**: In the new version, `BaseAdapter.__init__(self, sdk=None)` automatically handles SDK reference, log initialization, and configuration loading. Most adapters **do not need to override `__init__`**. See [__init__ Considerations](#init-considerations) for details.

> ⚠️ **About `super().__init__()`**: `BaseAdapter.__init__()` is responsible for creating `Send` and `Request` factory instances. If you forget to call it, all message sending and request operations will raise an `AttributeError`. See [__init__ Considerations](#init-considerations) for details.

### 4. Implement Required Methods

```python
class MyAdapter(BaseAdapter):
    # ... __init__ code ...
    
    async def start(self):
        """Start adapter (must implement)"""
        # Register WebSocket or WebHook route
        router.register_websocket(
            module_name="myplatform",
            path="/ws",
            handler=self._ws_handler
        )
        self.logger.info("Adapter started")
    
    async def shutdown(self):
        """Shutdown adapter (must implement)"""
        router.unregister_websocket(
            module_name="myplatform",
            path="/ws"
        )
        # Clean up connections and resources
        self.logger.info("Adapter shutdown")
    
    async def call_api(self, endpoint: str, **params):
        """Call platform API (must implement)"""
        raise NotImplementedError("call_api needs to be implemented")
```

#### Actively Send Meta Events

The adapter should actively send meta events to let the framework track the Bot's online status. Use `emit_meta()` in one line to complete:

```python
class MyAdapter(BaseAdapter):
    async def _ws_handler(self, websocket):
        bot_id = self._get_bot_id()

        # Bot online
        await self.emit_meta("connect", bot_id, user_name="MyBot")

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

> For detailed Bot status management and Meta event descriptions, please refer to [Adapter Best Practices - Bot Status Management](best-practices.md#bot-status-management-and-meta-events).

### 5. Implement Send Class

The `At`/`AtAll`/`Reply` modifiers have been built-in implemented by the framework SendDSL base class, the adapter only needs to implement `Raw_ob12` and specific sending methods.

The framework provides two key helper methods:
- `self._apply_modifiers(message)` — Automatically merges At/AtAll/Reply modifiers into message segments
- `self.send_context` — Gets the send context dictionary (`target_type`, `target_id`, `account_id`)

```python
import asyncio

class MyAdapter(BaseAdapter):
    # ... Other code ...
    
    class Send(BaseAdapter.Send):
        
        def Raw_ob12(self, message, **kwargs):
            """
            Send OneBot12 format message (must implement)

            Use _apply_modifiers to automatically merge modifier states,
            use send_context to get the send context.
            """
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
            """Send text message"""
            return self.Raw_ob12([
                {"type": "text", "data": {"text": text}}
            ])
        
        def Image(self, file):
            """Send image message"""
            return self.Raw_ob12([
                {"type": "image", "data": {"file": file}}
            ])
```

**Key points for media sending methods (Image/Video/File) implementation:**

- The `file` parameter should support both `bytes` binary data and `str` URL types
- When a URL is passed, the file needs to be downloaded first and then uploaded to the platform
- Platforms usually require calling an upload interface first to get a file identifier, then calling the send interface

**`__getattr__` magic method:**

- Implement case-insensitive method names (`Text`, `text`, `TEXT` can all be called)
- Undefined methods should return a prompt message instead of raising an error

**`Raw_ob12` method:**

- Convert OneBot12 standard message format to platform format and send
- Use `self._apply_modifiers(message)` to automatically handle At/AtAll/Reply modifiers
- Use `**self.send_context` to pass target information and account information

### 6. Implement Converter

```python
# MyAdapter/Converter.py
import time
import uuid

class MyPlatformConverter:
    def convert(self, raw_event):
        """Convert platform native event to OneBot12 standard format"""
        if not isinstance(raw_event, dict):
            return None
        
        onebot_event = {
            "id": str(raw_event.get("event_id", uuid.uuid4())),
            "time": int(time.time()),
            "type": self._convert_event_type(raw_event.get("type")),
            "detail_type": self._convert_detail_type(raw_event),
            "platform": "myplatform",
            "self": {
                "platform": "myplatform",
                "user_id": str(raw_event.get("bot_id", ""))
            },
            "myplatform_raw": raw_event,
            "myplatform_raw_type": raw_event.get("type", "")
        }
        
        return onebot_event
    
    def _convert_event_type(self, event_type):
        """Convert event type"""
        type_map = {
            "message": "message",
            "notice": "notice"
        }
        return type_map.get(event_type, "unknown")
    
    def _convert_detail_type(self, raw_event):
        """Convert detail type"""
        return "private"  # Simplified example
```

### 7. Implement Request Class (Request Actions)

If your platform supports friend requests, group invitations, or other requests that require the Bot to make decisions, you can implement the `Request` inner class:

```python
from ErisPulse.Core import BaseAdapter, RequestDSL

class MyAdapter(BaseAdapter):
    # ... Send and other code ...

    class Request(RequestDSL):
        """Request action implementation (friend request, group invitation, etc.)"""

        def accept(self, **kwargs):
            """Accept request"""
            async def _do():
                result = await self._adapter.call_api(
                    endpoint="/set_request",
                    request_id=self._request_id,
                    approve=True,
                    **kwargs,
                )
                return {
                    "status": "ok" if result.get("code") == 0 else "failed",
                    "retcode": result.get("code", 0),
                    "data": None,
                    "message_id": "",
                    "message": result.get("message", ""),
                }
            return self._create_task(_do())

        def reject(self, **kwargs):
            """Reject request"""
            async def _do():
                result = await self._adapter.call_api(
                    endpoint="/set_request",
                    request_id=self._request_id,
                    approve=False,
                    **kwargs,
                )
                return {
                    "status": "ok" if result.get("code") == 0 else "failed",
                    "retcode": result.get("code", 0),
                    "data": None,
                    "message_id": "",
                    "message": result.get("message", ""),
                }
            return self._create_task(_do())
```

Module developer usage:

```python
from ErisPulse.Core.Event import request

@request.on_friend_request()
async def handle_friend_request(event):
    # Via Event convenience method
    await event.approve()
    # Or operate directly via adapter
    await adapter.myplatform.Request("req_id").accept()
```

> If the platform does not support request actions, the `Request` inner class does not need to be implemented. The base class returns `retcode=10002` (unsupported action) by default. See [Request Action Specification](../../standards/request-action-spec.md) for details.

### 8. Create Package Entry

```python
# MyAdapter/__init__.py
from .Core import MyAdapter
```

## `__init__` Considerations

Adapter development may involve `__init__` overrides at three levels. Here are the correct practices for each level.

### 1. BaseAdapter Level (Most cases do not need to override)

`BaseAdapter.__init__(self, sdk=None)` is responsible for creating `Send` / `Request` factory instances and automatically performs the following tasks:

- Accepts the `sdk` parameter and sets `self.sdk`, `self.logger`
- If `ConfigClass` is declared, automatically loads global configuration into `self.config`
- If `AccountConfigClass` is declared, automatically loads multi-account configuration into `self.accounts`

**Most cases do not need to override `__init__`**; simply declare `ConfigClass`:

```python
class MyAdapter(BaseAdapter):
    ConfigClass = MyAdapterConfig  # After declaration, framework manages configuration automatically
    
    async def start(self):
        cfg = self.config  # Type-safe, automatically loaded
        ...
```

If you do need custom initialization, call `super().__init__(sdk)`:

```python
class MyAdapter(BaseAdapter):
    ConfigClass = MyAdapterConfig
    
    def __init__(self, sdk=None):
        super().__init__(sdk)  # Pass in sdk
        self.converter = self._setup_converter()
        self.convert = self.converter.convert
```

### 2. Send Inner Class (Most cases do not need to override)

`SendDSL.__init__` is responsible for state passing in chain calls (target type, target ID, account, etc.). **Most cases, you only need to override methods** (`Raw_ob12`, `Text`, etc.), and do not need to override `__init__`.

If really necessary (such as initializing platform-specific states), **all parameters must be passed through**:

```python
class MyAdapter(BaseAdapter):
    class Send(BaseAdapter.Send):
        # Parameters: adapter, target_type, target_id, account_id
        def __init__(self, adapter, target_type=None, target_id=None, account_id=None):
            super().__init__(adapter, target_type, target_id, account_id)  # ← Must pass through
            self._my_state = None  # Platform-specific initialization
```

**Why must it be passed through?** Each step of the chain call creates a new instance via `self.__class__(...)`:

```python
adapter.Send.To("user", "123")               # → Send(adapter, "user", "123", None)
adapter.Send.To("user", "123").Using("bot1")  # → Send(adapter, "user", "123", "bot1")
```

If the `__init__` signature does not match or `super()` is not called, the chain call will break.

### 3. Request Inner Class (Most cases do not need to override)

Same principle as Send. Parameters are `adapter`, `request_id`, `account_id`:

```python
class MyAdapter(BaseAdapter):
    class Request(RequestDSL):
        # Parameters: adapter, request_id, account_id
        def __init__(self, adapter, request_id=None, account_id=None):
            super().__init__(adapter, request_id, account_id)  # ← Must pass through
            self._my_state = None  # Platform-specific initialization
```

### Summary

| Level | When to override | Must do |
|------|------------|-----------|
| **BaseAdapter** | When adapter state needs to be initialized | `super().__init__(sdk)` (pass sdk parameter) |
| **Send Inner Class** | When send-related state needs to be initialized | `super().__init__(adapter, target_type, target_id, account_id)` |
| **Request Inner Class** | When request-related state needs to be initialized | `super().__init__(adapter, request_id, account_id)` |
| All three levels | In most cases | **Only override methods, do not touch `__init__`** |

## Next Steps

- [Adapter Core Concepts](core-concepts.md) - Learn about adapter architecture
- [SendDSL Details](send-dsl.md) - Learn about message sending
- [Converter Implementation](converter.md) - Learn about event conversion
- [Adapter Best Practices](best-practices.md) - Develop high-quality adapters