# Basic Concepts

> [!NOTE]
> **Required reading for the L1 core** — the 2nd of the "Five L1 Core Articles" listed on the documentation homepage (Module Development Introduction → **Basic Concepts** → Event Wrapper Class → Configuration File Guide → Exception Handling).

What components does a message pass through from the moment a user sends it to the moment the bot replies? What are adapters and modules each responsible for? After reading this article, you will be able to answer on your own the design questions you encounter when writing handlers, instead of merely copying examples.

## Event-Driven Architecture

ErisPulse adopts an event-driven architecture; all interactions are passed and processed through events.

### Event Flow

```
User sends a message
      │
      ▼
Platform receives it
      │
      ▼
Adapter receives the platform's native event
      │
      ▼
Converted to a OneBot12 standard event
      │
      ▼
Submitted to the event system
      │
      ▼
Dispatched to registered handlers
      │
      ▼
Module processes the event
      │
      ▼
Response sent through the adapter
      │
      ▼
Platform displays it to the user
```

### OneBot12 Standard

ErisPulse uses OneBot12 as its core event standard. OneBot12 is a universal chatbot application interface standard that defines a unified event format.

All adapters convert platform-specific events to the OneBot12 format, ensuring code consistency.

## Core Components

### 1. SDK Object

The SDK is the unified entry point for all functionality, providing access to core components.

```python
from ErisPulse import sdk

# Access core modules
sdk.storage    # Storage system
sdk.config     # Configuration system
sdk.logger     # Logging system
sdk.adapter    # Adapter system
sdk.module     # Module system
sdk.router     # Router system
sdk.client     # HTTP client
sdk.lifecycle  # Lifecycle system
```

> [!WARNING]
> **Always import from the root**: `from ErisPulse.Core import adapter` / `import ErisPulse.Core.adapter`
> binds to the **manager instance** (the `AdapterManager` singleton) rather than the submodule — the
> re-export in the `ErisPulse.Core` package shadows the submodule of the same name. When writing
> tests, patching, or needing the module object itself, always use the `from ErisPulse import sdk`
> root import (`sdk.adapter` is the manager instance).

### 2. Event Object

The Event object encapsulates event data and provides convenient access methods.

```python
@command("info")
async def info_handler(event):
    # Get event information
    event_id = event.get_id()
    user_id = event.get_user_id()
    platform = event.get_platform()
    text = event.get_text()
    
    # Send a reply
    await event.reply(f"User: {user_id}, Platform: {platform}")
```

### 3. Adapter

Adapters are the bridge between ErisPulse and external platforms.

**Responsibilities:**
- Receiving platform-native events
- Converting them to the OneBot12 standard format
- Sending standard-format events to the platform

**Example adapters:**
- Yunhu adapter: communicates with the Yunhu platform
- Telegram adapter: communicates with the Telegram Bot API
- OneBot11 adapter: communicates with OneBot11-compatible applications
- Email adapter: handles email sending and receiving

### 4. Module

Modules are the basic unit of functionality extension; they can:

- Register event handlers
- Implement business logic
- Call adapters to send messages
- Use services provided by core modules

#### Module Discovery Mechanism

ErisPulse discovers installed modules through Python's `importlib.metadata.entry_points`. Modules declare entry points in `pyproject.toml`:

```toml
[project.entry-points."erispulse.module"]
MyModule = "my_package:Main"
```

During SDK initialization, all entry points in the `erispulse.module` group are scanned, module classes are registered with the `ModuleManager`, and then they are initialized one by one after a topological sort by dependencies.

#### Minimal Viable Module

```python
from ErisPulse.Core.Bases import BaseModule
from ErisPulse import sdk

class Main(BaseModule):
    def __init__(self):
        self.sdk = sdk
        self.logger = sdk.logger.get_child("MyModule")

    async def on_load(self, event):
        self.logger.info("Module loaded")

    async def on_unload(self, event):
        self.logger.info("Module unloaded")
```

#### Module Lifecycle

- **Registration**: The SDK discovers the module class and registers it with the manager
- **Loading**: A module instance is created and `on_load(event)` is called (`event = {"module_name": "MyModule"}`)
- **Unloading**: `on_unload(event)` is called to clean up resources

#### Load Strategy

Declare a module's loading behavior via `get_load_strategy()`:

```python
from ErisPulse.loaders import ModuleLoadStrategy

class Main(BaseModule):
    @staticmethod
    def get_load_strategy():
        return ModuleLoadStrategy(
            lazy_load=True,   # Whether to lazy load (default True)
            priority=0        # Load priority; higher values are initialized first
        )
```

- **`lazy_load=True` (default)**: The module is initialized only when first accessed via `sdk.MyModule`, reducing startup time
- **`lazy_load=False`**: The module is initialized immediately at SDK startup, suitable for modules that need to listen for lifecycle events or run scheduled tasks
- **`priority`**: Modules with the same priority are loaded in registration order; higher values are initialized first

> For a detailed explanation of the lazy loading mechanism, see [Lazy Loading System](../advanced/lazy-loading.md).

## Event Types

ErisPulse supports 5 types of events:

| Event Type | Decorator | Description |
|---------|--------|------|
| Message events | `@message.on_message()` | Any message sent by users (private chats, group chats) |
| Command events | `@command("name")` | Messages starting with the command prefix (e.g., `/hello`) |
| Notice events | `@notice.on_friend_add()` etc. | System notices (friend additions, group member changes, etc.) |
| Request events | `@request.on_friend_request()` etc. | User requests (friend requests, group invitations) |
| Meta events | `@meta.on_connect()` etc. | System-level events (connect, disconnect, heartbeat) |

> For detailed usage and code examples of each event type, see [Event Handling Introduction](event-handling.md).

## Core Module Descriptions

### Storage

A SQLite-based key-value storage system for persisting data.

```python
# Set a value
sdk.storage.set("key", "value")

# Get a value
value = sdk.storage.get("key", "default_value")

# Batch operations
sdk.storage.set_multi({
    "key1": "value1",
    "key2": "value2"
})

# Transactions
with sdk.storage.transaction():
    sdk.storage.set("key1", "value1")
    sdk.storage.set("key2", "value2")
```

### Config

TOML-format configuration file management.

```python
# Get configuration
config = sdk.config.getConfig("MyModule", {})

# Set configuration
sdk.config.setConfig("MyModule", {"key": "value"})

# Read nested configuration
value = sdk.config.getConfig("MyModule.subkey", "default")
```

### Logger

A modular logging system.

```python
# Log messages
sdk.logger.info("This is an info message")
sdk.logger.warning("This is a warning")
sdk.logger.error("This is an error")

# Get a child logger
child_logger = sdk.logger.get_child("submodule")
child_logger.info("Submodule log")
```

**Attribute Access Syntactic Sugar**

Besides the `get_child()` method, you can also create child loggers via **attribute access**, which is a more concise **syntactic sugar** style:

```python
# Create a child logger via attribute access
sdk.logger.mymodule.info("Module message")

# Supports nested access
sdk.logger.mymodule.database.info("Database message")
```

### Router

HTTP and WebSocket route management, based on FastAPI + Uvicorn. Supports decorator routes, middleware, grouping, rate limiting, and CORS.

```python
from ErisPulse.Core import HttpRequest

@sdk.router.get("MyModule", "/api")
async def handler(request: HttpRequest):
    data = await request.json()
    return {"status": "ok"}
```

> For the full router API (WebSocket, middleware, rate limiting, CORS, etc.), see [Router Manager](../advanced/router.md).

### Client (Network Client)

A unified network client that consolidates HTTP requests, WebSocket connections, connection pool management, automatic retries, timeout control, request statistics, and lifecycle event integration.

```python
from ErisPulse.Core import client

# HTTP request
resp = await client.get("https://api.example.com/users")
data = await resp.json()

# With retries and timeout
resp = await client.get(url, timeout=30, max_retries=3)

# WebSocket connection
ws = await client.ws_connect("wss://example.com/ws")
async for text in ws.iter_text():
    await ws.send_text(f"Echo: {text}")
```

> For the full network client API, see [Network Client](../advanced/client.md).

## SendDSL Message Sending

Adapters provide a chained-call message sending interface.

### Basic Sending

```python
# Get an adapter instance
yunhu = sdk.adapter.get("yunhu")

# Send a message
await yunhu.Send.To("user", "U1001").Text("Hello")

# Specify the sending account
await yunhu.Send.Using("bot1").To("group", "G1001").Text("Group message")
```

### Chained Modifiers

```python
# Mention a user
await yunhu.Send.To("group", "G1001").At("U2001").Text("@message")

# Reply to a message
await yunhu.Send.To("group", "G1001").Reply("msg123").Text("Reply")

# Mention everyone
await yunhu.Send.To("group", "G1001").AtAll().Text("Announcement")
```

### Event Reply Methods

The Event object provides convenient reply methods:

```python
@command("test")
async def test_handler(event):
    # Simple text reply
    await event.reply("Reply content")
    
    # Send an image
    await event.reply("http://example.com/image.jpg", method="Image")
    
    # Send voice
    await event.reply("http://example.com/voice.mp3", method="Voice")
```

## Lazy Loading System

ErisPulse enables module lazy loading by default; modules are initialized only when first accessed (e.g., `sdk.MyModule`), which significantly improves startup speed.

```python
from ErisPulse.loaders import ModuleLoadStrategy

class Main(BaseModule):
    @staticmethod
    def get_load_strategy():
        return ModuleLoadStrategy(
            lazy_load=True,   # Enable lazy loading (default)
            priority=0        # Load priority; higher values are initialized first
        )
```

**Scenarios requiring lazy loading to be disabled (`lazy_load=False`):**
- Modules that listen for lifecycle events (e.g., `core.init.complete`)
- Modules that start scheduled tasks or background services
- Modules that need to complete initialization before other modules are loaded

> For detailed lazy loading mechanisms and caveats, see [Lazy Loading System](../advanced/lazy-loading.md).

## Next Steps

- **Continue along the L1 path**: Next up, [Event Wrapper Class](../developer-guide/modules/event-wrapper.md) — master all the read/write methods of the event object
- **Learn while writing**: [Event Handling Introduction](event-handling.md) provides copy-ready handler patterns organized by event type; [Common Task Examples](common-tasks.md) covers persistence, scheduled tasks, permission control, and other common features