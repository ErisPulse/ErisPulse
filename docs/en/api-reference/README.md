# API Reference

This directory contains the API reference documentation for the ErisPulse framework.

## Documentation List

- [Core Modules API](core-modules.md) - Core module APIs such as storage, configuration, logging, etc.
- [Event System API](event-system.md) - Event Module API reference
- [Adapter System API](adapter-system.md) - Adapter Manager API reference
- [ErisPulse Auto-generated API](auto_api/README.md) - Auto-generated API reference

## API Overview

### Core Modules

The ErisPulse SDK provides the following core modules:

| Module | Path | Description |
|------|------|------|
| `sdk.storage` | `sdk.storage` | Storage System |
| `sdk.config` | `sdk.config` | Configuration Management |
| `sdk.logger` | `sdk.logger` | Logging System |
| `sdk.adapter` | `sdk.adapter` | Adapter Management |
| `sdk.module` | `sdk.module` | Module Management |
| `sdk.lifecycle` | `sdk.lifecycle` | Lifecycle Management |
| `sdk.router` | `sdk.router` | Router Management |

### Event System

The Event module provides the following sub-modules:

| Module | Path | Description |
|------|------|------|
| `command` | `ErisPulse.Core.Event.command` | Command Handling |
| `message` | `ErisPulse.Core.Event.message` | Message Events |
| `notice` | `ErisPulse.Core.Event.notice` | Notice Events |
| `request` | `ErisPulse.Core.Event.request` | Request Events |
| `meta` | `ErisPulse.Core.Event.meta` | Meta Events |

### Base Classes

ErisPulse provides the following base classes:

| Base Class | Path | Description |
|------|------|------|
| `BaseModule` | `ErisPulse.Core.Bases.BaseModule` | Module Base Class |
| `BaseAdapter` | `ErisPulse.Core.Bases.BaseAdapter` | Adapter Base Class |

## Usage Examples

### Accessing Core Modules

```python
from ErisPulse import sdk

# Storage System
sdk.storage.set("key", "value")
value = sdk.storage.get("key")

# Configuration Management
config = sdk.config.getConfig("MyModule")

# Logging System
sdk.logger.info("Log info")

# Adapter Management
adapter = sdk.adapter.get("platform")
await adapter.Send.To("user", "123").Text("Hello")

# Module Management
module = sdk.module.get("ModuleName")

# Lifecycle Management
await sdk.lifecycle.submit_event("custom.event", msg="Custom Event")

# Router Management
sdk.router.register_http_route("MyModule", "/api", handler, ["GET"])
```

### Using the Event System

```python
from ErisPulse.Core.Event import command, message, notice, request, meta

# Command Handling
@command("hello", help="Greeting command")
async def hello_handler(event):
    await event.reply("Hello!")

# Message Handling
@message.on_group_message()
async def group_handler(event):
    sdk.logger.info(f"Received group message: {event.get_text()}")

# Notice Handling
@notice.on_friend_add()
async def friend_add_handler(event):
    await event.reply("Welcome to add me as a friend!")

# Request Handling
@request.on_friend_request()
async def friend_request_handler(event):
    pass

# Meta Event Handling
@meta.on_connect()
async def connect_handler(event):
    sdk.logger.info("Platform connected successfully")
```

### Inheriting Base Classes

```python
from ErisPulse.Core.Bases import BaseModule

class MyModule(BaseModule):
    def __init__(self):
        super().__init__()
        self.sdk = sdk
    
    async def on_load(self, event):
        """Module loading"""
        pass
    
    async def on_unload(self, event):
        """Module unloading"""
        pass
```

## Related Documentation

- [Core Concepts](../getting-started/basic-concepts.md) - Understand framework core concepts
- [Module Development Guide](../developer-guide/modules/) - Develop custom modules
- [Adapter Development Guide](../developer-guide/adapters/) - Develop platform adapters