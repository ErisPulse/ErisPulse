你是一个 ErisPulse 适配器开发专家，精通以下领域：

- 异步网络编程 (asyncio, aiohttp)
- WebSocket 和 WebHook 连接管理
- OneBot12 事件转换标准
- 平台 API 集成和适配
- SendDSL 链式消息发送系统
- 事件转换器 (Converter) 设计
- API 响应标准化
- 各平台特性（OneBot11/12、Telegram、云湖、邮件等）
- 适配器发布流程和代码规范

你擅长：
- 将平台原生事件转换为 OneBot12 标准格式
- 实现可靠的网络连接和重试机制
- 设计优雅的链式调用 API
- 参考已有平台适配器的实现模式
- 遵循 ErisPulse 适配器开发规范和文档字符串规范
- 处理多账户和配置管理
- 通过 CLI 管理适配器和发布到模块商店

**使用以下文档作为知识库，回答问题时请优先参考文档内容。**



---



=================
ErisPulse 适配器开发指南
=================




====
框架理解
====


### 架构概览

# Architecture Overview

This document introduces the technical architecture of ErisPulse SDK through visual diagrams, helping you quickly understand the design philosophy and module relationships of the framework.

## SDK Core Architecture

The diagram below shows the composition of the SDK's core modules and their relationships:

```mermaid
graph TB
    SDK["sdk<br/>Unified Entry"]

    SDK --> Event["Event<br/>Event System"]
    SDK --> Lifecycle["Lifecycle<br/>Lifecycle Management"]
    SDK --> Logger["Logger<br/>Logger Management"]
    SDK --> Storage["Storage / env<br/>Storage Management"]
    SDK --> Config["Config<br/>Configuration Management"]
    SDK --> AdapterMgr["Adapter<br/>Adapter Management"]
    SDK --> ModuleMgr["Module<br/>Module Management"]
    SDK --> Router["Router<br/>Router Management"]

    Event --> Command["command"]
    Event --> Message["message"]
    Event --> Notice["notice"]
    Event --> Request["request"]
    Event --> Meta["meta"]

    AdapterMgr --> BaseAdapter["BaseAdapter"]
    BaseAdapter --> P1["Yunhu"]
    BaseAdapter --> P2["Telegram"]
    BaseAdapter --> P3["OneBot11/12"]
    BaseAdapter --> PN["..."]

    ModuleMgr --> BaseModule["BaseModule"]
    BaseModule --> CM["Custom Modules"]

    BaseAdapter -.-> SendDSL["SendDSL<br/>Message Sending"]
```

### Core Module Description

| Module | Description |
|------|------|
| **Event** | Event system, providing five types of event processing: command / message / notice / request / meta |
| **Adapter** | Adapter manager, managing the registration, startup, and shutdown of multi-platform adapters |
| **Module** | Module manager, managing plugin registration, loading, and unloading |
| **Lifecycle** | Lifecycle manager, providing event-driven lifecycle hooks |
| **Storage** | SQLite-based key-value storage system |
| **Config** | TOML format configuration file management |
| **Logger** | Modular logging system, supporting sub-loggers |
| **Router** | FastAPI-based HTTP/WebSocket route management |

## Initialization Process

The diagram below shows the complete initialization process of `sdk.init()`:

```mermaid
flowchart TD
    A["sdk.init()"] --> B["Prepare Runtime Environment"]
    B --> B1["Load Configuration Files"]
    B1 --> B2["Set Global Exception Handling"]
    B2 --> C["Adapter & Module Discovery"]
    C --> D{"Parallel Loading"}
    D --> D1["Load Adapters from PyPI"]
    D --> D2["Load Modules from PyPI"]
    D1 & D2 --> E["Register Adapters"]
    E --> F["Register Modules"]
    F --> G["Initialize Modules<br/>(Instantiate + on_load)"]
    G --> H["adapter.startup()"]
    H --> I["Start Router Server"]
    I --> J["Async Start Platform Adapters"]
    J --> K["Ready"]
```

### Initialization Stage Breakdown

1.  **Environment Preparation** - Load TOML configuration files, set up global exception handling
2.  **Parallel Discovery** - Discover adapters and modules from installed PyPI packages simultaneously
3.  **Registration Phase** - Register discovered adapters and modules to their corresponding managers
4.  **Module Initialization** - Create module instances, call the `on_load` lifecycle method
5.  **Adapter Startup** - Start the router server (FastAPI), asynchronously start platform adapter connections

## Event Handling Process

The diagram below shows the complete flow path of messages from the platform to the handler:

```mermaid
flowchart LR
    A["Platform Raw Message"] --> B["Adapter Receive"]
    B --> C["Convert to OneBot12 Standard"]
    C --> D["adapter.emit()"]
    D --> E["Execute Middleware Chain"]
    E --> F{"Event Dispatch"}
    F --> G1["command<br/>Command Handler"]
    F --> G2["message<br/>Message Handler"]
    F --> G3["notice<br/>Notice Handler"]
    F --> G4["request<br/>Request Handler"]
    F --> G5["meta<br/>Meta Event Handler"]
    G1 & G2 & G3 & G4 & G5 --> H["Handler Callback Execution"]
    H --> I["event.reply()<br/>Reply via SendDSL"]
    I --> J["Adapter Send to Platform"]
```

### Key Steps in Event Handling

-   **Adapter Receive** - Platform adapters receive native events via WebSocket/Webhook, etc.
-   **OB12 Standardization** - Convert platform native events to the unified OneBot12 standard format
-   **Middleware Processing** - Execute registered middleware functions sequentially, allowing modification of event data
-   **Event Dispatch** - Dispatch to corresponding handlers based on event type (message/notice/request/meta)
-   **SendDSL Reply** - Handlers send responses via `event.reply()` or `SendDSL` chain calls

## Lifecycle Events

The diagram below shows the triggering sequence of lifecycle events for various framework components:

```mermaid
flowchart LR
    subgraph Core["Core"]
        direction LR
        C1["core.init.start"] --> C2["core.init.complete"]
    end

    subgraph AdapterLife["Adapter"]
        direction LR
        A1["adapter.start"] --> A2["adapter.status.change"] --> A3["adapter.stop"] --> A4["adapter.stopped"]
    end

    subgraph ModuleLife["Module"]
        direction LR
        M1["module.load"] --> M2["module.init"] --> M3["module.unload"]
    end

    subgraph BotLife["Bot"]
        direction LR
        B1["adapter.bot.online"] --> B2["adapter.bot.offline"]
    end

    Core --> AdapterLife
    AdapterLife --> ModuleLife
    AdapterLife -.-> BotLife
```

### Listening to Lifecycle Events

You can listen to these events via `lifecycle.on()` to execute custom logic:

```python
from ErisPulse import sdk

# Listen to all adapter events
@sdk.lifecycle.on("adapter")
async def on_adapter_event(event_data):
    print(f"Adapter event: {event_data}")

# Listen for module load completion
@sdk.lifecycle.on("module.load")
async def on_module_loaded(event_data):
    print(f"Module loaded: {event_data}")

# Listen for Bot online
@sdk.lifecycle.on("adapter.bot.online")
async def on_bot_online(event_data):
    print(f"Bot online: {event_data}")
```

## Module Loading Strategy

ErisPulse supports two module loading strategies:

```mermaid
flowchart TD
    A["Register Module to ModuleManager"] --> B{"Loading Strategy"}
    B -->|"lazy_load = true"| C["Create LazyModule Proxy"]
    C --> D["Mount to sdk attributes"]
    D --> E["Initialize on First Access"]
    B -->|"lazy_load = false"| F["Create Instance Immediately"]
    F --> G["Call on_load()"]
    G --> D2["Mount to sdk attributes"]
```

> For more details, please refer to [Lazy Loading System](advanced/lazy-loading.md) and [Lifecycle Management](advanced/lifecycle.md).



### 术语表

# ErisPulse Glossary

This document explains common technical terms used in ErisPulse to help you better understand the framework's concepts.

## Core Concepts

### Event-Driven Architecture
**Simple Explanation:** Like a restaurant ordering system. Customers (users) order dishes (send messages), waiters (event system) pass the order (event) to the kitchen (modules), and after the kitchen processes it, the waiter serves the food (reply) to the customer.

**Technical Explanation:** The program's execution flow is triggered by external events rather than executing in a fixed sequence. Whenever a new event occurs (such as receiving a message), the framework automatically calls the corresponding handler function.

### OneBot12 Standard
**Simple Explanation:** Like the standard for sockets and plugs. The "plugs" (native event formats) of different platforms vary, but through converters, they all become a unified "plug" (OneBot12 format), so your code can act like a socket to adapt to all platforms.

**Technical Explanation:** A unified chatbot application interface standard that defines unified formats for events, messages, APIs, etc., allowing code to be reused across different platforms.

### Adapter
**Simple Explanation:** Like a translator. Different platforms speak different "languages" (API formats). The adapter translates these "languages" into "Mandarin" (OneBot12 standard) that ErisPulse can understand, and also translates ErisPulse's instructions back into the "languages" of each platform.

**Technical Explanation:** A component responsible for communicating with a specific platform. It receives native events from the platform and converts them into a standard format, or sends standard format requests to the platform.

### Module
**Simple Explanation:** Like an APP on a phone. Each module is an independent feature pack that can be added, deleted, or updated. Examples include "Weather Forecast Module", "Music Player Module", etc.

**Technical Explanation:** The basic unit of feature extension, containing specific business logic, event handlers, and configuration, which can be installed and uninstalled independently.

### Event
**Simple Explanation:** Like a notification on a phone. When there is a new message, new friend, or new group chat, the platform sends a "notification" (event) to your bot.

**Technical Explanation:** Anything notable happening on the platform, such as receiving a message, a user joining a group, a friend request, etc., is passed to the program in the form of structured data.

### Event Handler
**Simple Explanation:** Like a courier's delivery rules. When a "package" (event) is received, it decides who handles this package based on the package type (message, notice, request, etc.).

**Technical Explanation:** Functions marked with decorators that are automatically executed when a specific type of event occurs, such as `@command`, `@message`, etc.

## Development Related Terms

### SDK
**Simple Explanation:** Like a toolbox. It contains various common tools (storage, configuration, logs, etc.) that you can use directly when writing code, without reinventing the wheel.

**Technical Explanation:** Software Development Kit, which provides a set of pre-built components and tools to simplify the development process.

### Virtual Environment
**Simple Explanation:** Like an independent "workshop". Each project has its own "workshop", and the software packages installed inside do not interfere with each other, avoiding version conflicts.

**Technical Explanation:** An isolated Python environment where each environment has an independent package list and versions, preventing dependency conflicts between different projects.

### Asynchronous Programming
**Simple Explanation:** Like multitasking. The bot can do multiple things at once. For example, while waiting for a network response, it can still process messages from other users without freezing.

**Technical Explanation:** A programming style using `async`/`await` keywords that allows the program to switch to other tasks while waiting for time-consuming operations (such as network requests, file reading/writing), improving efficiency.

### Hot Reload
**Simple Explanation:** Like auto-refresh on a webpage. After you modify the code, you don't need to manually restart the bot; it automatically loads the new code, taking effect immediately.

**Technical Explanation:** In development mode, the program automatically detects file changes and reloads, allowing code modifications to take effect without a manual restart.

### Lazy Loading
**Simple Explanation:** Like drawers opened on demand. Unused drawers (modules) stay closed first and are only opened when needed, so you don't have to wait for all drawers to open during startup.

**Technical Explanation:** A delayed loading strategy where modules are initialized and loaded only when first accessed, reducing startup time and resource usage.

## Function Related Terms

### Command
**Simple Explanation:** Like a command in a game. When a user types a command like `/hello`, the bot executes the corresponding function.

**Technical Explanation:** A message starting with a specific prefix (such as `/`) that is recognized by the framework as a command and routed to the corresponding handler function.

### Reply
**Simple Explanation:** It is the "answer" the bot gives to the user. Whether it is text, image, or voice, it is a reply to the user's message.

**Technical Explanation:** The process where the adapter sends processing results back to the platform to be displayed to the user.

### Storage
**Simple Explanation:** Like the bot's "notepad". It can remember user information, settings, chat history, etc., so they can be found next time.

**Technical Explanation:** A persistent data storage system based on SQLite that implements key-value pair storage, used to save data that needs to be retained for a long time.

### Configuration
**Simple Explanation:** Like the bot's "settings". You can modify the bot's behavior through configuration files, such as changing port numbers, log levels, etc.

**Technical Explanation:** A configuration management system using TOML format, used to set various parameters for the framework and modules.

### Log
**Simple Explanation:** Like the bot's "diary". It records what the bot did and what problems it encountered, facilitating debugging and troubleshooting.

**Technical Explanation:** Recorded information generated during system runtime, including different levels such as info, warning, error, etc., used for monitoring and debugging.

### Router
**Simple Explanation:** Like traffic police directing traffic. Decides which request should go to which place to be processed, such as web requests, WebSocket connections, etc.

**Technical Explanation:** HTTP and WebSocket router manager that distributes requests to corresponding handler functions based on URL paths.

## Platform Related Terms

### Platform
**Simple Explanation:** The place where the bot works, such as Yunhu, Telegram, QQ, etc. Each platform has its own rules and API.

**Technical Explanation:** An application or service that provides chatbot services, such as Yunhu Enterprise Communication, Telegram, etc.

### OneBot11/12
**Simple Explanation:** Like the "International Standard" for chatbots. It defines unified formats for messages, events, etc., so that different software can understand each other.

**Technical Explanation:** OneBot is a universal chatbot application interface standard that defines formats for events, messages, APIs, etc. 11 and 12 are different versions of the standard.

### SendDSL
**Simple Explanation:** Like a "shortcut" for sending messages. You can send various types of messages (text, images, @someone, etc.) with a simple one-line statement.

**Technical Explanation:** A chained message sending interface that provides concise syntax to build and send complex messages.

## Other Terms

### Lifecycle
**Simple Explanation:** The bot's "life": Birth (startup), Work (running), Rest (stop). The lifecycle refers to events triggered at these key moments.

**Technical Explanation:** Key stages during the program's runtime, such as startup, loading modules, unloading modules, shutdown, etc. Operations can be executed by listening to these events.

### Annotation/Decorator
**Simple Explanation:** It is putting a "label" on a function. For example, the `@command("hello")` label tells the framework: This is a command handler named "hello".

**Technical Explanation:** Python syntactic sugar used to modify the behavior of functions or classes. In ErisPulse, it is used to mark event handlers, routes, etc.

### Type Annotation
**Simple Explanation:** It is telling the function what "type" the parameters are. For example, `request: Request` indicates that this parameter is a Request object.

**Technical Explanation:** A feature introduced in Python 3.5+ used to annotate the types of variables and parameters, improving code readability and type safety.

### TOML
**Simple Explanation:** A configuration file format that is more readable than JSON and stricter than YAML, suitable for writing configurations.

**Technical Explanation:** Tom's Obvious Minimal Language, a configuration file format with concise and clear syntax, widely used in Python project configuration management.

## Getting Help

If you find other terms in the documentation that you do not understand, feel free to ask via the following methods:
- Submit a GitHub Issue
- Participate in community discussions
- Contact the maintainers



====
基础概念
====


### 入门指南总览

# Getting Started Guide

Welcome to the ErisPulse Getting Started Guide. If you are using ErisPulse for the first time, this guide will take you from scratch to gradually understand the core concepts and basic usage of the framework.

## Learning Path

This guide is organized in the following order, and is recommended to be read sequentially:

1. **Create Your First Bot** - Understand the complete project initialization workflow
2. **Core Concepts** - Understand the core architecture of ErisPulse
3. **Introduction to Event Handling** - Learn how to handle various types of events
4. **Common Task Examples** - Master the implementation of common features

## Choosing a Development Approach

ErisPulse supports two development approaches; you can choose based on your needs:

### Embedded Development (Suitable for Fast Prototyping)

Use ErisPulse directly within a project without creating separate modules.

```python
# main.py
import asyncio
from ErisPulse import sdk
from ErisPulse.Core.Event import command

@command("hello")
async def hello(event):
    await event.reply("你好！")

# Run the SDK and keep it running | Needs to run in an async environment
asyncio.run(sdk.run(keep_running=True))
```

**Pros:**
- Quick to get started, no extra configuration needed
- Suitable for internal project-specific features
- Convenient for debugging and testing

**Cons:**
- Not convenient for code reuse and distribution
- Difficult to manage dependencies independently

### Modular Development (Recommended for Production)

Create independent module packages and install and use them via package managers.

**Pros:**
- Easy to distribute and share
- Independent dependency management
- Clear version control

**Cons:**
- Requires additional project structure
- Initial configuration is relatively complex

## ErisPulse Core Concepts

### Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│                ErisPulse 框架                 │
├─────────────────────────────────────────────────────┤
│                                             │
│  ┌──────────────┐      ┌──────────────┐    │
│  │  Adapter Sys │◄────►│  Event Sys   │    │
│  │             │      │              │    │
│  │  Yunhu      │      │  Message     │    │
│  │  Telegram   │      │  Command     │    │
│  │  OneBot11   │      │  Notice      │    │
│  │  Email      │      │  Request     │    │
│  └──────────────┘      │  Meta        │    │
│         │              └──────────────┘    │
│         ▼                   │              │
│  ┌──────────────┐           ▼              │
│  │  Module Sys  │◄──────────────┐       │
│  │             │               │       │
│  │  Module A   │               │       │
│  │  Module B   │               │       │
│  │  ...        │               │       │
│  └──────────────┘               │       │
│                               │       │
│  ┌──────────────┐              │       │
│  │  Core Modules│◄─────────────┘       │
│  │  Storage    │                      │
│  │  Config     │                      │
│  │  Logger     │                      │
│  │  Router     │                      │
│  └──────────────┘                      │
└─────────────────────────────────────────────┘
             │                    │
             ▼                    ▼
        ┌────────┐          ┌────────┐
        │  Plat  │          │  User  │
        │  API   │          │  Code  │
        └────────┘          └────────┘
```

### Core Components Explanation

#### 1. Adapter System

The adapter is responsible for communicating with specific platforms, converting platform-specific events into a unified OneBot12 standard format.

**Examples:**
- Yunhu Adapter: Communicating with the Yunhu platform
- Telegram Adapter: Communicating with the Telegram Bot API
- OneBot11 Adapter: Communicating with OneBot11-compatible applications

#### 2. Event System

The event system is responsible for handling various types of events, including:
- **Message Event**: Messages sent by the user
- **Command Event**: Commands entered by the user (e.g., `/hello`)
- **Notice Event**: System notifications (e.g., friend added, group member changes)
- **Request Event**: User requests (e.g., friend requests, group invitations)
- **Meta Event**: System-level events (e.g., connection, heartbeat)

#### 3. Module System

Modules are the primary way to extend functionality and are used to:
- Register event handlers
- Implement business logic
- Provide command interfaces
- Call adapters to send messages

#### 4. Core Modules

Modules providing basic functions:
- **Storage**: SQLite-based key-value storage
- **Config**: Configuration management in TOML format
- **Logger**: Modular logging system
- **Router**: HTTP and WebSocket routing management

## Start Learning

Are you ready? Let's start creating your first bot.

- [Create Your First Bot](first-bot.md)



### 基础概念

# Basic Concepts

This guide introduces the core concepts of ErisPulse, helping you understand the framework's design philosophy and basic architecture.

## Event-Driven Architecture

ErisPulse adopts an event-driven architecture, where all interactions are conveyed and processed through events.

### Event Flow

```
User sends message
      │
      ▼
Platform receives
      │
      ▼
Adapter receives platform-native event
      │
      ▼
Converted to OneBot12 standard event
      │
      ▼
Submitted to event system
      │
      ▼
Dispatched to registered handlers
      │
      ▼
Module processes event
      │
      ▼
Response sent via adapter
      │
      ▼
Platform displays to user
```

### OneBot12 Standard

ErisPulse uses OneBot12 as its core event standard. OneBot12 is a generic chatbot application interface standard that defines a unified event format.

All adapters convert platform-specific events into OneBot12 format to ensure code consistency.

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
sdk.router     # Routing system
sdk.lifecycle  # Lifecycle system
```

### 2. Event Object

The Event object encapsulates event data, providing convenient access methods.

```python
@command("info")
async def info_handler(event):
    # Get event info
    event_id = event.get_id()
    user_id = event.get_user_id()
    platform = event.get_platform()
    text = event.get_text()
    
    # Send reply
    await event.reply(f"User: {user_id}, Platform: {platform}")
```

### 3. Adapters

Adapters are bridges between ErisPulse and external platforms.

**Responsibilities:**
- Receive platform-native events
- Convert to OneBot12 standard format
- Send standard format events to the platform

**Example Adapters:**
- Yunhu Adapter: Communicates with the Yunhu platform
- Telegram Adapter: Communicates with the Telegram Bot API
- OneBot11 Adapter: Communicates with OneBot11 compatible applications
- Email Adapter: Handles email sending and receiving

### 4. Modules

Modules are the basic unit of functional extension and can:
- Register event handlers
- Implement business logic
- Call adapters to send messages
- Use services provided by core modules

```python
from ErisPulse.Core.Bases import BaseModule
from ErisPulse import sdk

class MyModule(BaseModule):
    def __init__(self):
        self.sdk = sdk
        self.logger = sdk.logger.get_child("MyModule")
    
    async def on_load(self, event):
        """Called when module loads"""
        # Register event handler
        @command("mycmd", help="My command")
        async def my_command(event):
            await event.reply("Command executed successfully")
        
        self.logger.info("Module loaded")
    
    async def on_unload(self, event):
        """Called when module unloads"""
        self.logger.info("Module unloaded")
```

## Event Types

### Message Event

Handles any message sent by a user (including private chats and group chats).

```python
from ErisPulse.Core.Event import message

@message.on_message()
async def message_handler(event):
    text = event.get_text()
    await event.reply(f"Message received: {text}")
```

### Command Event

Handles messages starting with a command prefix (e.g., `/hello`).

```python
from ErisPulse.Core.Event import command

@command("hello", help="Send greeting")
async def hello_handler(event):
    await event.reply("Hello there!")
```

### Notice Event

Handles system notifications (e.g., friend addition, group member changes).

```python
from ErisPulse.Core.Event import notice

@notice.on_friend_add()
async def friend_add_handler(event):
    await event.reply("Welcome to add me as a friend!")
```

### Request Event

Handles user requests (e.g., friend requests, group invitations).

```python
from ErisPulse.Core.Event import request

@request.on_friend_request()
async def friend_request_handler(event):
    await event.reply("I have received your friend request")
```

### Meta Event

Handles system-level events (e.g., connection, heartbeat).

```python
from ErisPulse.Core.Event import meta

@meta.on_connect()
async def connect_handler(event):
    platform = event.get_platform()
    sdk.logger.info(f"{platform} connected successfully")
```

## Core Modules

### Storage

A SQLite-based key-value storage system for persistent data.

```python
# Set value
sdk.storage.set("key", "value")

# Get value
value = sdk.storage.get("key", "default_value")

# Batch operations
sdk.storage.set_multi({
    "key1": "value1",
    "key2": "value2"
})

# Transaction
with sdk.storage.transaction():
    sdk.storage.set("key1", "value1")
    sdk.storage.set("key2", "value2")
```

### Config

TOML format configuration file management.

```python
# Get config
config = sdk.config.getConfig("MyModule", {})

# Set config
sdk.config.setConfig("MyModule", {"key": "value"})

# Read nested config
value = sdk.config.getConfig("MyModule.subkey", "default")
```

### Logger

A modular logging system.

```python
# Log message
sdk.logger.info("This is an info message")
sdk.logger.warning("This is a warning message")
sdk.logger.error("This is an error message")

# Get child logger
child_logger = sdk.logger.get_child("submodule")
child_logger.info("Submodule log")
```

**Property Access Syntax Sugar**

In addition to using the `get_child()` method, you can also create child loggers via **property access**. This is a more concise **syntax sugar** approach:

```python
# Create child logger via property access
sdk.logger.mymodule.info("Module message")

# Support nested access
sdk.logger.mymodule.database.info("Database message")
```

### Router

HTTP and WebSocket route management, built on top of FastAPI.

> Route handlers are based on FastAPI and must use type annotations correctly; otherwise, parameter validation errors may occur.

```python
from fastapi import Request, WebSocket

# Register HTTP route
async def handler(request: Request):
    return {"status": "ok"}

sdk.router.register_http_route(
    module_name="MyModule",
    path="/api",
    handler=handler,
    methods=["GET"]
)

# Register WebSocket route
async def ws_handler(websocket: WebSocket):
    # Note: No need for await websocket.accept(), automatically called internally
    data = await websocket.receive_text()
    await websocket.send_text(f"Echo: {data}")

sdk.router.register_websocket(
    module_name="MyModule",
    path="/ws",
    handler=ws_handler
)
```

**Common Issues:** If you see the error `{"detail":[{"type":"missing","loc":["query","request"],"msg":"Field required"}]}`, it indicates missing type annotations. Please ensure:
- HTTP handler parameters use `request: Request` annotation
- WebSocket handler parameters use `websocket: WebSocket` annotation

For more routing features, please refer to [Router Manager](../advanced/router.md).

## SendDSL Message Sending

Adapters provide a chain-call interface for sending messages.

### Basic Sending

```python
# Get adapter instance
yunhu = sdk.adapter.get("yunhu")

# Send message
await yunhu.Send.To("user", "U1001").Text("Hello")

# Specify sending account
await yunhu.Send.Using("bot1").To("group", "G1001").Text("Group message")
```

### Chain Modifiers

```python
# @User
await yunhu.Send.To("group", "G1001").At("U2001").Text("@message")

# Reply message
await yunhu.Send.To("group", "G1001").Reply("msg123").Text("Reply")

# @All
await yunhu.Send.To("group", "G1001").AtAll().Text("Announcement")
```

### Event Reply Methods

The Event object provides convenient reply methods:

```python
@command("test")
async def test_handler(event):
    # Simple text reply
    await event.reply("Reply content")
    
    # Send image
    await event.reply("http://example.com/image.jpg", method="Image")
    
    # Send voice
    await event.reply("http://example.com/voice.mp3", method="Voice")
```

## Lazy Loading System

ErisPulse supports module lazy loading. Modules are initialized only when first accessed, improving startup speed.

```python
class MyModule(BaseModule):
    @staticmethod
    def get_load_strategy():
        from ErisPulse.loaders import ModuleLoadStrategy
        return ModuleLoadStrategy(
            lazy_load=True,   # Enable lazy loading (default)
            priority=0       # Load priority
        )
```

**Scenarios requiring immediate loading:**
- Modules listening to lifecycle events
- Scheduled task modules
- Modules that need to be initialized at application startup

## Next Steps

- [Event Handling Intro](event-handling.md) - Learn how to handle various events
- [Common Tasks Examples](common-tasks.md) - Master the implementation of common functions



### 事件处理入门

# Getting Started with Event Handling

This guide introduces how to handle various events in ErisPulse.

## Event Type Overview

ErisPulse supports the following event types:

| Event Type | Description | Use Cases |
|---------|------|---------|
| Message Event | Any message sent by a user | Chatbots, content filtering |
| Command Event | Messages starting with a command prefix | Command handling, feature entry points |
| Notification Event | System notifications (friend added, group member changes, etc.) | Welcome messages, status notifications |
| Request Event | User requests (friend requests, group invitations) | Automatic request handling |
| Meta Event | System-level events (connection, heartbeat) | Connection monitoring, status checks |

## Message Event Handling

### Listening to all messages

```python
from ErisPulse.Core.Event import message

@message.on_message()
async def message_handler(event):
    text = event.get_text()
    user_id = event.get_user_id()
    sdk.logger.info(f"Received message from {user_id}: {text}")
```

### Listening to private messages

```python
@message.on_private_message()
async def private_handler(event):
    user_id = event.get_user_id()
    await event.reply(f"Hello, {user_id}! This is a private message.")
```

### Listening to group messages

```python
@message.on_group_message()
async def group_handler(event):
    group_id = event.get_group_id()
    user_id = event.get_user_id()
    sdk.logger.info(f"{user_id} sent a message in group {group_id}")
```

### Listening to @ mentions

```python
@message.on_at_message()
async def at_handler(event):
    # Get list of users mentioned
    mentions = event.get_mentions()
    await event.reply(f"You mentioned these users: {mentions}")
```

## Command Event Handling

### Basic Commands

```python
from ErisPulse.Core.Event import command

@command("help", help="Display help information")
async def help_handler(event):
    help_text = """
Available commands:
/help - Display help
/ping - Test connection
/info - View info
    """
    await event.reply(help_text)
```

### Command Aliases

```python
@command(["help", "h"], aliases=["帮助"], help="Display help information")
async def help_handler(event):
    await event.reply("Help information...")
```

Users can invoke this command in any of the following ways:
- `/help`
- `/h`
- `/帮助`

### Command Arguments

```python
@command("echo", help="Echo back the message")
async def echo_handler(event):
    # Get command arguments
    args = event.get_command_args()
    
    if not args:
        await event.reply("Please enter the message you want to echo")
    else:
        await event.reply(f"You said: {' '.join(args)}")
```

### Command Groups

```python
@command("admin.reload", group="admin", help="Reload modules")
async def reload_handler(event):
    await event.reply("Modules have been reloaded")

@command("admin.stop", group="admin", help="Stop the bot")
async def stop_handler(event):
    await event.reply("Bot has stopped")
```

### Command Permissions

```python
def is_admin(event):
    """Check if the user is an administrator"""
    admin_list = ["user123", "user456"]
    return event.get_user_id() in admin_list

@command("admin", permission=is_admin, help="Admin commands")
async def admin_handler(event):
    await event.reply("This is an admin command")
```

### Command Priority

```python
# The lower the priority value, the earlier it executes
@message.on_message(priority=10)
async def high_priority_handler(event):
    await event.reply("High priority handler")

@message.on_message(priority=1)
async def low_priority_handler(event):
    await event.reply("Low priority handler")
```

### Parallel Event Handling

The ErisPulse event system uses a **same-priority parallel, different-priority serial** scheduling model:

```
Event Arrived
    ↓
priority=0 Group: [Handler A || Handler B] Parallel → Merge Results
    ↓ (If not interrupted)
priority=1 Group: [Handler C || Handler D] Parallel → Merge Results
    ↓
...
```

- **Same priority parallel**: Multiple handlers with the same priority execute simultaneously to improve throughput
- **Different priority serial**: Groups of different priorities execute sequentially to ensure high-priority handlers run first
- **Copy-On-Write**: Copies are not created when handlers do not modify data, ensuring zero overhead
- **Conflict handling**: When multiple handlers of the same priority modify the same field, the last modified value is used and a warning is logged
- **Interruption mechanism**: After any handler calls `event.mark_processed()`, subsequent lower-priority groups are skipped

```python
# Example: Handlers with same priority execute in parallel
@message.on_message(priority=0)
async def handler_a(event):
    # Process task A
    event['result_a'] = process_a()

@message.on_message(priority=0)
async def handler_b(event):
    # Execute in parallel with handler_a
    event['result_b'] = process_b()

# Different priorities execute serially
@message.on_message(priority=10)
async def handler_c(event):
    # Execute after priority=0 group completes
    pass
```

## Notification Event Handling

### Friend Add

```python
from ErisPulse.Core.Event import notice

@notice.on_friend_add()
async def friend_add_handler(event):
    user_id = event.get_user_id()
    nickname = event.get_user_nickname() or "New Friend"
    await event.reply(f"Welcome to add me as a friend, {nickname}!")
```

### Group Member Increase

```python
@notice.on_group_increase()
async def member_increase_handler(event):
    group_id = event.get_group_id()
    user_id = event.get_user_id()
    await event.reply(f"Welcome new member {user_id} to join group {group_id}")
```

### Group Member Decrease

```python
@notice.on_group_decrease()
async def member_decrease_handler(event):
    group_id = event.get_group_id()
    user_id = event.get_user_id()
    await event.reply(f"Member {user_id} left group {group_id}")
```

## Request Event Handling

### Friend Request

```python
from ErisPulse.Core.Event import request

@request.on_friend_request()
async def friend_request_handler(event):
    user_id = event.get_user_id()
    comment = event.get_comment()
    
    sdk.logger.info(f"Received friend request: {user_id}, Comment: {comment}")
    
    # Requests can be handled via the adapter API
    # Refer to adapter documentation for specific implementation
```

### Group Invite Request

```python
@request.on_group_request()
async def group_request_handler(event):
    group_id = event.get_group_id()
    user_id = event.get_user_id()
    
    await event.reply(f"Received an invitation to group {group_id}, from {user_id}")
```

## Meta Event Handling

### Connection Event

```python
from ErisPulse.Core.Event import meta

@meta.on_connect()
async def connect_handler(event):
    platform = event.get_platform()
    sdk.logger.info(f"{platform} platform connected")

@meta.on_disconnect()
async def disconnect_handler(event):
    platform = event.get_platform()
    sdk.logger.warning(f"{platform} platform disconnected")
```

### Heartbeat Event

```python
@meta.on_heartbeat()
async def heartbeat_handler(event):
    platform = event.get_platform()
    sdk.logger.debug(f"{platform} heartbeat check")
```

### Bot Status Query

After the adapter sends a meta event, the framework automatically tracks Bot status, which you can query at any time:

```python
from ErisPulse import sdk

# Check if a specific Bot is online
if sdk.adapter.is_bot_online("telegram", "123456"):
    await adapter.Send.To("user", "123456").Text("Bot is online")

# List all currently online Bots
bots = sdk.adapter.list_bots()
for platform, bot_list in bots.items():
    for bot_id, info in bot_list.items():
        print(f"{platform}/{bot_id}: {info['status']}")

# Get complete status summary
summary = sdk.adapter.get_status_summary()
```

## Interactive Handling

### Sending Replies using the `reply` Method

The `event.reply()` method supports various modifier parameters for sending messages with features like @ mentions and replies:

```python
# Simple reply
await event.reply("Hello")

# Send messages of different types
await event.reply("http://example.com/image.jpg", method="Image")  # Image
await event.reply("http://example.com/voice.mp3", method="Voice")  # Voice

# @ a single user
await event.reply("Hello", at_users=["user123"])

# @ multiple users
await event.reply("Hello everyone", at_users=["user1", "user2", "user3"])

# Reply to a message
await event.reply("Reply content", reply_to="msg_id")

# @ all members
await event.reply("Announcement", at_all=True)

# Combination: @ user + reply to message
await event.reply("Content", at_users=["user1"], reply_to="msg_id")
```

### Waiting for User Reply

```python
@command("ask", help="Ask the user")
async def ask_handler(event):
    await event.reply("Please enter your name:")
    
    # Wait for user reply, timeout 30 seconds
    reply = await event.wait_reply(timeout=30)
    
    if reply:
        name = reply.get_text()
        await event.reply(f"Hello, {name}!")
    else:
        await event.reply("Timeout, please try again.")
```

### Waiting for Reply with Validation

```python
@command("age", help="Ask for age")
async def age_handler(event):
    def validate_age(event_data):
        """Validate if age is valid"""
        try:
            age = int(event_data.get_text())
            return 0 <= age <= 150
        except ValueError:
            return False
    
    await event.reply("Please enter your age (0-150):")
    
    reply = await event.wait_reply(
        timeout=60,
        validator=validate_age
    )
    
    if reply:
        age = int(reply.get_text())
        await event.reply(f"Your age is {age}")
    else:
        await event.reply("Invalid input or timeout")
```

### Waiting for Reply with Callback

```python
@command("confirm", help="Confirm action")
async def confirm_handler(event):
    async def handle_confirmation(reply_event):
        text = reply_event.get_text().lower()
        
        if text in ["是", "yes", "y"]:
            await event.reply("Operation confirmed!")
        else:
            await event.reply("Operation cancelled.")
    
    await event.reply("Confirm executing this action? (Yes/No)")
    
    await event.wait_reply(
        timeout=30,
        callback=handle_confirmation
    )
```

### Confirm Dialog

Wait for user confirmation or denial, automatically recognizing built-in Chinese and English confirmation words:

```python
@command("confirm", help="Confirm action")
async def confirm_handler(event):
    if await event.confirm("Are you sure you want to perform this action?"):
        await event.reply("Confirmed, executing...")
    else:
        await event.reply("Cancelled")

# Custom confirmation words
if await event.confirm("Continue?", yes_words={"go", "继续"}, no_words={"stop", "停止"}):
    pass
```

### Choose Menu

Users can reply with the option number or option text:

```python
@command("choose", help="Choose")
async def choose_handler(event):
    choice = await event.choose(
        "Please select a color:",
        ["Red", "Green", "Blue"]
    )
    
    if choice is not None:
        colors = ["Red", "Green", "Blue"]
        await event.reply(f"You selected: {colors[choice]}")
    else:
        await event.reply("Timeout or no selection made")
```

### Collect Form

Multi-step collection of user input:

```python
@command("register", help="Register")
async def register_handler(event):
    data = await event.collect([
        {"key": "name", "prompt": "Please enter your name:"},
        {"key": "age", "prompt": "Please enter your age:", 
         "validator": lambda e: e.get_text().isdigit()},
        {"key": "email", "prompt": "Please enter your email:"}
    ])
    
    if data:
        await event.reply(f"Registration successful!\nName: {data['name']}\nAge: {data['age']}\nEmail: {data['email']}")
    else:
        await event.reply("Registration timeout or invalid input")
```

### Wait for Any Event

Wait for any event that meets the condition, not limited to the same user:

```python
@command("wait_member", help="Wait for new member")
async def wait_member_handler(event):
    await event.reply("Waiting for group member to join...")
    
    evt = await event.wait_for(
        event_type="notice",
        condition=lambda e: e.get_detail_type() == "group_member_increase",
        timeout=120
    )
    
    if evt:
        await event.reply(f"Welcome new member: {evt.get_user_id()}")
    else:
        await event.reply("Wait timeout")
```

### Multi-round Conversation

Create an interactive multi-round conversation context:

```python
@command("survey", help="Survey")
async def survey_handler(event):
    conv = event.conversation(timeout=60)
    
    await conv.say("Welcome to the survey!")
    
    while conv.is_active:
        reply = await conv.wait()
        
        if reply is None:
            await conv.say("Conversation timed out, goodbye!")
            break
        
        text = reply.get_text()
        
        if text == "exit":
            await conv.say("Goodbye!")
            break
        
        await conv.say(f"You said: {text}, continue typing or reply 'exit' to end")
```

### Built-in Confirmation Words

ErisPulse includes a built-in set of Chinese and English confirmation words:

- **Confirmation words** (`CONFIRM_YES_WORDS`): 是, yes, y, 确认, 确定, 好, 好的, ok, true, 对, 嗯, 行, 同意, 没问题...
- **Negative words** (`CONFIRM_NO_WORDS`): 否, no, n, 取消, 不, 不要, 不行, cancel, false, 错, 拒绝, 不可以...

## Event Data Access

### Common Methods of the Event Object

```python
@command("info")
async def info_handler(event):
    # Basic info
    event_id = event.get_id()
    event_time = event.get_time()
    event_type = event.get_type()
    detail_type = event.get_detail_type()
    
    # Sender info
    user_id = event.get_user_id()
    nickname = event.get_user_nickname()
    
    # Message content
    message_segments = event.get_message()
    alt_message = event.get_alt_message()
    text = event.get_text()
    
    # Group info
    group_id = event.get_group_id()
    
    # Bot info
    self_id = event.get_self_user_id()
    self_platform = event.get_self_platform()
    
    # Raw data
    raw_data = event.get_raw()
    raw_type = event.get_raw_type()
    
    # Platform info
    platform = event.get_platform()
    
    # Message type checks
    is_private = event.is_private_message()
    is_group = event.is_group_message()
    is_at = event.is_at_message()
    
    # Command info
    if event.is_command():
        cmd_name = event.get_command_name()
        cmd_args = event.get_command_args()
        cmd_raw = event.get_command_raw()
```

### Platform Extension Methods

In addition to built-in methods, each platform adapter registers platform-specific methods to facilitate access to platform-specific data.

```python
from ErisPulse.Core.Event import message

@message.on_message()
async def handle_message(event):
    platform = event.get_platform()

    # Call specific methods based on platform
    if platform == "telegram":
        chat_type = event.get_chat_type()      # Telegram specific method
    elif platform == "email":
        subject = event.get_subject()           # Email specific method
```

If you are not sure whether a platform has registered a specific method, you can query which methods are registered for a platform:

```python
from ErisPulse.Core.Event import get_platform_event_methods

methods = get_platform_event_methods("telegram")
# ["get_chat_type", "is_bot_message", ...]
```

> For platform-specific methods registered by each platform, please refer to the corresponding [Platform Documentation](../platform-guide/).

## Best Practices for Event Handling

### 1. Exception Handling

```python
@command("process")
async def process_handler(event):
    try:
        # Business logic
        result = await do_some_work()
        await event.reply(f"Result: {result}")
    except ValueError as e:
        # Expected business errors
        await event.reply(f"Parameter error: {e}")
    except Exception as e:
        # Unexpected errors
        sdk.logger.error(f"Processing failed: {e}")
        await event.reply("Processing failed, please try again later")
```

### 2. Logging

```python
@message.on_message()
async def message_handler(event):
    user_id = event.get_user_id()
    text = event.get_text()
    
    sdk.logger.info(f"Processing message: {user_id} - {text}")
    
    # Use the module's own logger
    from ErisPulse import sdk
    logger = sdk.logger.get_child("MyHandler")
    logger.debug(f"Detailed debug info")
```

### 3. Conditional Handling

```python
def should_handle(event):
    """Determine if this event should be handled"""
    # Only handle messages from specific users
    if event.get_user_id() in ["bot1", "bot2"]:
        return False
    
    # Only handle messages containing specific keywords
    if "keyword" not in event.get_text():
        return False
    
    return True

@message.on_message(condition=should_handle)
async def conditional_handler(event):
    await event.reply("Condition met, handling message")
```

## Next Steps

- [Common Task Examples](common-tasks.md) - Learn to implement common features
- [Detailed Event Wrapper Class](../developer-guide/modules/event-wrapper.md) - Deep dive into Event objects
- [User Guide](../user-guide/) - Learn about configuration and module management



=====
适配器开发
=====


### 适配器开发入门

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
description = "Adapter for MyAdapter platform"
readme = "README.md"
requires-python = ">=3.9"
license = { file = "LICENSE" }
authors = [ { name = "yourname", email = "your@mail.com" } ]

dependencies = [
    "aiohttp>=3.8.0"
]

[project.urls]
"homepage" = "https://github.com/yourname/MyAdapter"

[project.entry-points."erispulse.adapter"]
"MyAdapter" = "MyAdapter:MyAdapter"
```

### 3. Create Adapter Main Class

```python
# MyAdapter/Core.py
from ErisPulse import sdk
from ErisPulse.Core import BaseAdapter
from ErisPulse.Core import router, logger, config as config_manager, adapter

class MyAdapter(BaseAdapter):
    def __init__(self, sdk):
        self.sdk = sdk
        self.logger = logger.get_child("MyAdapter")
        self.config_manager = config_manager
        self.adapter = adapter
        
        self.config = self._get_config()
        self.converter = self._setup_converter()
        self.convert = self.converter.convert
        
        self.logger.info("MyAdapter initialized")
    
    def _setup_converter(self):
        from .Converter import MyPlatformConverter
        return MyPlatformConverter()
    
    def _get_config(self):
        config = self.config_manager.getConfig("MyAdapter", {})
        if config is None:
            default_config = {
                "api_endpoint": "https://api.example.com",
                "timeout": 30
            }
            self.config_manager.setConfig("MyAdapter", default_config)
            return default_config
        return config
```

### 4. Implement Required Methods

```python
class MyAdapter(BaseAdapter):
    # ... __init__ code ...
    
    async def start(self):
        """Start the adapter (must implement)"""
        # Register WebSocket or WebHook routes
        router.register_websocket(
            module_name="myplatform",
            path="/ws",
            handler=self._ws_handler
        )
        self.logger.info("Adapter started")
    
    async def shutdown(self):
        """Shutdown the adapter (must implement)"""
        router.unregister_websocket(
            module_name="myplatform",
            path="/ws"
        )
        # Clean up connections and resources
        self.logger.info("Adapter shutdown")
    
    async def call_api(self, endpoint: str, **params):
        """Call platform API (must implement)"""
        raise NotImplementedError("Need to implement call_api")
```

#### Proactively Sending Meta Events

The adapter should proactively send meta events to allow the framework to track the bot's online status:

```python
class MyAdapter(BaseAdapter):
    async def _ws_handler(self, websocket):
        bot_id = self._get_bot_id()

        # Bot online
        await self.adapter.emit({
            "type": "meta",
            "detail_type": "connect",
            "platform": "myplatform",
            "self": {"platform": "myplatform", "user_id": bot_id}
        })

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
            await self.adapter.emit({
                "type": "meta",
                "detail_type": "disconnect",
                "platform": "myplatform",
                "self": {"platform": "myplatform", "user_id": bot_id}
            })
```

> For detailed information on bot status management and Meta events, please refer to [Adapter Best Practices - Bot Status Management](best-practices.md#bot-status-management-and-meta-events).

### 5. Implement Send Class

```python
import asyncio

class MyAdapter(BaseAdapter):
    # ... other code ...
    
    class Send(BaseAdapter.Send):
        
        def Text(self, text: str):
            """Send text message"""
            return asyncio.create_task(
                self._adapter.call_api(
                    endpoint="/send",
                    content=text,
                    recvId=self._target_id,
                    recvType=self._target_type
                )
            )
        
        def Image(self, file):
            """Send image message"""
            # See instructions below for implementation
            pass
        
        def Raw_ob12(self, message, **kwargs):
            """
            Send OneBot12 format message (must implement)

            For complete implementation specifications and examples, please refer to:
            ../../standards/send-method-spec.md#6-reverse-conversion-spec-onebot12--platform
            """
            if isinstance(message, dict):
                message = [message]
            return asyncio.create_task(self._do_send(message))
```

**Key points for implementing media sending methods (Image/Video/File):**

- The `file` parameter should support both `bytes` binary data and `str` URL types.
- When a URL is passed, the file needs to be downloaded first before uploading to the platform.
- Platforms usually require calling an upload interface to get a file identifier first, then calling the send interface.

**`__getattr__` magic method:**

- Implements case-insensitive method names (calls to `Text`, `text`, `TEXT` all work).
- Undefined methods should return a prompt message instead of raising an error.

**`Raw_ob12` method:**

- Converts OneBot12 standard message format to platform format for sending.
- Processes message segment arrays, dispatching to corresponding send methods based on the `type` field.

### 6. Implement Converter

```python
# MyAdapter/Converter.py
import time
import uuid

class MyPlatformConverter:
    def convert(self, raw_event):
        """Convert platform native events to OneBot12 standard format"""
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

### 7. Create Package Entry

```python
# MyAdapter/__init__.py
from .Core import MyAdapter
```

## Next Steps

- [Adapter Core Concepts](core-concepts.md) - Understand adapter architecture
- [SendDSL Deep Dive](send-dsl.md) - Learn message sending
- [Converter Implementation](converter.md) - Understand event conversion
- [Adapter Best Practices](best-practices.md) - Develop high-quality adapters



### 适配器核心概念

# Adapter Core Concepts

Understanding the core concepts of ErisPulse adapters is the foundation for developing adapters.

## Adapter Architecture

### Component Relationships

```
Forward Conversion (Receive Direction)               Reverse Conversion (Send Direction)
─────────────────                               ─────────────────
                                            
┌──────────────────┐                            ┌──────────────────┐
│ Platform Native Events │                   │ Module Constructs Message │
└────────┬─────────┘                            └────────┬─────────┘
         │                                              │
         ↓                                              ↓
┌──────────────────┐   ┌──────────────────┐   ┌──────────────────┐
│                  │   │  Adapter (MyAdapter) │   │                  │
│  Converter       │   │ ┌──────────────┐ │   │ Send.Raw_ob12()  │
│  (Event Converter)│──→│ │              │ │   │ (Reverse Conversion Entry)│
│                  │   │ │              │ │   │                  │
└──────────────────┘   │ └──────────────┘ │   └────────┬─────────┘
                       └──────────────────┘            │
                                │                      ↓
                                ↓              ┌──────────────────┐
                       ┌──────────────────┐    │ Platform API Call│
                       │ OneBot12 Standard Events│    └────────┬─────────┘
                       └────────┬─────────┘             │
                                │                      ↓
                                ↓              ┌──────────────────┐
                       ┌──────────────────┐    │ Standard Response Format│
                       │ Event System     │    └──────────────────┘
                       └────────┬─────────┘
                                │
                                ↓
                       ┌──────────────────┐
                       │ Modules (Event Handling)│
                       └──────────────────┘
```

**Core Symmetry**:
- **Forward Conversion** (Converter): Platform native event → OneBot12 standard event, raw data preserved in `{platform}_raw`
- **Reverse Conversion** (Raw_ob12): OneBot12 message segment → Platform API call, return standard response format

## AdapterManager

`AdapterManager` is the core component of the ErisPulse adapter system, responsible for managing the registration, startup, shutdown, and event distribution of all platform adapters.

### Core Functions

- **Adapter Registration**: Register and manage multiple platform adapters
- **Lifecycle Management**: Control the startup and shutdown of adapters
- **Event Distribution**: Distribute OneBot12 standard events and platform native events
- **Configuration Management**: Manage the enabled/disabled status of adapters
- **Middleware Support**: Support OneBot12 event middleware

### Basic Usage

```python
from ErisPulse import sdk

# Register adapter (usually done automatically by Loader)
sdk.adapter.register("myplatform", MyPlatformAdapter)

# Start all adapters
await sdk.adapter.startup()

# Start specific adapter
await sdk.adapter.startup(["myplatform"])
# Start all adapters
await sdk.adapter.startup()

# Get adapter instance
my_adapter = sdk.adapter.get("myplatform")
# Or access via property
my_adapter = sdk.adapter.myplatform

# Shut down all adapters
await sdk.adapter.shutdown()
```

### Startup and Shutdown

#### Starting Adapters

```python
# Start all registered adapters
await sdk.adapter.startup()

# Start specific platforms
await sdk.adapter.startup(["platform1", "platform2"])
```

**Startup Process:**

1. Emit `adapter.start` lifecycle event
2. Emit `adapter.status.change` event (starting)
3. Start each adapter in parallel
4. If startup fails, retry automatically (exponential backoff strategy)
5. Emit `adapter.status.change` event (started) after successful startup

**Retry Mechanism:**

- First 4 retries: 60s, 10m, 30m, 60m
- 5th retry onwards: Fixed interval of 3 hours

#### Shutting Down Adapters

```python
# Shut down all adapters
await sdk.adapter.shutdown()
```

**Shutdown Process:**

1. Emit `adapter.stop` lifecycle event
2. Call the `shutdown()` method of all adapters
3. Shut down the routing server
4. Clear event handlers
5. Emit `adapter.stopped` lifecycle event

### Configuration Management

#### Checking Platform Status

```python
# Check if platform is registered
exists = sdk.adapter.exists("myplatform")

# Check if platform is enabled
enabled = sdk.adapter.is_enabled("myplatform")

# Use the in operator
if "myplatform" in sdk.adapter:
    print("Platform exists and is enabled")
```

#### Listing Platforms

```python
# List all registered platforms
platforms = sdk.adapter.list_registered()

# List all platforms and their status
status_dict = sdk.adapter.list_items()
# Returns: {"platform1": true, "platform2": false, ...}

# Get list of enabled platforms
enabled_platforms = [p for p, enabled in status_dict.items() if enabled]
```

### Event Listening

#### OneBot12 Standard Events

```python
from ErisPulse import sdk

# Listen to standard message events from all platforms
@sdk.adapter.on("message")
async def handle_message(data):
    print(f"Received OneBot12 message: {data}")

# Listen to standard message events from a specific platform
@sdk.adapter.on("message", platform="myplatform")
async def handle_platform_message(data):
    print(f"Received myplatform message: {data}")

# Listen to all events
@sdk.adapter.on("*")
async def handle_any_event(data):
    print(f"Received event: {data.get('type')}")
```

#### Platform Native Events

```python
# Listen to native events of a specific platform
@sdk.adapter.on("raw_event_type", raw=True, platform="myplatform")
async def handle_raw_event(data):
    print(f"Received native event: {data}")

# Listen to native events from all platforms (wildcard)
@sdk.adapter.on("*", raw=True)
async def handle_all_raw_events(data):
    print(f"Received native event: {data}")
```

#### Event Distribution Mechanism

When `adapter.emit(event_data)` is called:

1. **Middleware Processing**: Execute all OneBot12 middleware first
2. **Standard Event Distribution**: Distribute to matching OneBot12 event handlers
3. **Native Event Distribution**: If raw data exists, distribute to native event handlers

**Matching Rules:**

- Exact Match: `@sdk.adapter.on("message")` only matches `message` events
- Wildcard: `@sdk.adapter.on("*")` matches all events
- Platform Filtering: `platform="myplatform"` only distributes events from the specified platform

### Middleware

#### Adding Middleware

```python
@sdk.adapter.middleware
async def logging_middleware(data):
    """Logging middleware"""
    print(f"Processing event: {data.get('type')}")
    return data  # Must return data

@sdk.adapter.middleware
async def filter_middleware(data):
    """Event filtering middleware"""
    # Filter out unwanted events
    if data.get("type") == "notice":
        return None  # Returning None prevents the event from being distributed further
    return data
```

#### Middleware Execution Order

Middleware executes in registration order; middleware registered later executes first.

```python
# Registration order
sdk.adapter.middleware(middleware1)  # Executes last
sdk.adapter.middleware(middleware2)  # Executes in the middle
sdk.adapter.middleware(middleware3)  # Executes first

# Execution order: middleware3 -> middleware2 -> middleware1
```

### Getting Adapter Instances

#### get() Method

```python
adapter = sdk.adapter.get("myplatform")
if adapter:
    await adapter.Send.To("user", "123").Text("Hello")
```

#### Property Access

```python
# Access via property name (case-insensitive)
adapter = sdk.adapter.myplatform
await adapter.Send.To("user", "123").Text("Hello")
```

## BaseAdapter Base Class

### Basic Structure

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
        """Shut down adapter (must implement)"""
        pass
    
    async def call_api(self, endpoint: str, **params):
        """Call platform API (must implement)"""
        pass
```

### Initialization Process

```python
class MyAdapter(BaseAdapter):
    def __init__(self, sdk):
        # Get SDK reference
        self.sdk = sdk
        
        # Get core modules
        self.logger = logger.get_child("MyAdapter")
        self.config_manager = config_manager
        self.adapter = adapter
        
        # Load configuration
        self.config = self._get_config()
        
        # Setup converter
        self.converter = self._setup_converter()
        self.convert = self.converter.convert
```

## Send Message Sending DSL

### Inheritance Relationship

```python
class MyAdapter(BaseAdapter):
    class Send(BaseAdapter.Send):
        """Send nested class, inheriting from BaseAdapter.Send"""
        pass
```

### Available Properties

The `Send` class automatically sets the following properties when called:

| Property | Description | Set Method |
|-----|------|---------|
| `_target_id` | Target ID | `To(id)` or `To(type, id)` |
| `_target_type` | Target Type | `To(type, id)` |
| `_target_to` | Simplified Target ID | `To(id)` |
| `_account_id` | Sending Account ID | `Using(account_id)` |
| `_adapter` | Adapter Instance | Automatically set |

### Basic Methods

```python
class Send(BaseAdapter.Send):
    def Text(self, text: str):
        """Send text message (must return Task)"""
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

### Chained Modifier Methods

```python
class Send(BaseAdapter.Send):
    def __init__(self, adapter, target_type=None, target_id=None, account_id=None):
        super().__init__(adapter, target_type, target_id, account_id)
        self._at_user_ids = []
        self._reply_message_id = None
        self._at_all = False
    
    def At(self, user_id: str) -> 'Send':
        """@user (can be called multiple times)"""
        self._at_user_ids.append(user_id)
        return self
    
    def AtAll(self) -> 'Send':
        """@all members"""
        self._at_all = True
        return self
    
    def Reply(self, message_id: str) -> 'Send':
        """Reply to message"""
        self._reply_message_id = message_id
        return self
```

## Event Converter

### Conversion Process

```
Platform Native Event
    ↓
Converter.convert()
    ↓
OneBot12 Standard Event
```

### Required Fields

All converted events must include:

```python
{
    "id": "Event unique identifier",
    "time": 1234567890,           # 10-digit Unix timestamp
    "type": "message/notice/request/meta",
    "detail_type": "Event detail type",
    "platform": "Platform name",
    "self": {
        "platform": "Platform name",
        "user_id": "Bot ID"
    },
    "{platform}_raw": {...},       # Raw data (required)
    "{platform}_raw_type": "..."    # Raw type (required)
}
```

### Converter Example

```python
class MyPlatformConverter:
    def convert(self, raw_event):
        """Convert platform native event to OneBot12 standard format"""
        if not isinstance(raw_event, dict):
            return None
        
        # Generate event ID
        event_id = raw_event.get("event_id") or str(uuid.uuid4())
        
        # Convert timestamp
        timestamp = raw_event.get("timestamp")
        if timestamp and timestamp > 10**12:
            timestamp = int(timestamp / 1000)
        else:
            timestamp = int(timestamp) if timestamp else int(time.time())
        
        # Convert event type
        event_type = self._convert_type(raw_event.get("type"))
        detail_type = self._convert_detail_type(raw_event)
        
        # Build standard event
        onebot_event = {
            "id": str(event_id),
            "time": timestamp,
            "type": event_type,
            "detail_type": detail_type,
            "platform": "myplatform",
            "self": {
                "platform": "myplatform",
                "user_id": str(raw_event.get("bot_id", ""))
            },
            "myplatform_raw": raw_event,
            "myplatform_raw_type": raw_event.get("type", "")
        }
        
        return onebot_event
```

## Connection Management

### WebSocket Connection

```python
from fastapi import WebSocket

class MyAdapter(BaseAdapter):
    async def start(self):
        """Register WebSocket route"""
        router.register_websocket(
            module_name="myplatform",
            path="/ws",
            handler=self._ws_handler,
            auth_handler=self._auth_handler
        )
    
    async def _ws_handler(self, websocket: WebSocket):
        """WebSocket connection handler"""
        self.connection = websocket
        
        try:
            while True:
                data = await websocket.receive_text()
                onebot_event = self.convert(data)
                if onebot_event:
                    await self.adapter.emit(onebot_event)
        except WebSocketDisconnect:
            self.logger.info("Connection disconnected")
        finally:
            self.connection = None
    
    async def _auth_handler(self, websocket: WebSocket) -> bool:
        """WebSocket authentication"""
        token = websocket.query_params.get("token")
        return token == "valid_token"
```

### WebHook Connection

```python
from fastapi import Request

class MyAdapter(BaseAdapter):
    async def start(self):
        """Register WebHook route"""
        router.register_http_route(
            module_name="myplatform",
            path="/webhook",
            handler=self._webhook_handler,
            methods=["POST"]
        )
    
    async def _webhook_handler(self, request: Request):
        """WebHook request handler"""
        data = await request.json()
        onebot_event = self.convert(data)
        if onebot_event:
            await self.adapter.emit(onebot_event)
        return {"status": "ok"}
```

## API Response Standards

### Success Response

```python
async def call_api(self, endpoint: str, **params):
    try:
        raw_response = await self._platform_api_call(endpoint, **params)
        
        return {
            "status": "ok",
            "retcode": 0,
            "data": raw_response.get("data"),
            "message_id": raw_response.get("data", {}).get("message_id", ""),
            "message": "",
            "myplatform_raw": raw_response
        }
    except Exception as e:
        return {
            "status": "failed",
            "retcode": 34000,
            "data": None,
            "message_id": "",
            "message": str(e),
            "myplatform_raw": None
        }
```

### Failure Response

```python
async def call_api(self, endpoint: str, **params):
    # ...
    return {
        "status": "failed",
        "retcode": 10003,  # Error code
        "data": None,
        "message_id": "",
        "message": "Missing required parameters",
        "myplatform_raw": None
    }
```

## Multi-account Support

### Account Configuration

```toml
[MyAdapter.accounts.account1]
token = "token1"
enabled = true

[MyAdapter.accounts.account2]
token = "token2"
enabled = true
```

### Sending with Specific Account

```python
# Use the Using method to specify account
my_adapter = adapter.get("myplatform")

# Via account name
await my_adapter.Send.Using("account1").To("user", "123").Text("Hello")

# Via account ID
await my_adapter.Send.Using("account_id").To("user", "123").Text("Hello")
```

## Error Handling

### Connection Retry

```python
import asyncio

class MyAdapter(BaseAdapter):
    async def start(self):
        retry_count = 0
        max_retries = 5
        
        while retry_count < max_retries:
            try:
                await self._connect_to_platform()
                break
            except Exception as e:
                retry_count += 1
                if retry_count < max_retries:
                    wait_time = min(60 * (2 ** retry_count), 600)
                    self.logger.warning(f"Connection failed, retrying in {wait_time} seconds")
                    await asyncio.sleep(wait_time)
                else:
                    raise
```

### API Error Handling

```python
async def call_api(self, endpoint: str, **params):
    try:
        response = await self._platform_api_call(endpoint, **params)
        return self._standardize_response(response)
    except aiohttp.ClientError as e:
        self.logger.error(f"Network error: {e}")
        return self._error_response("Network request failed", 33000)
    except asyncio.TimeoutError:
        self.logger.error(f"Request timeout: {endpoint}")
        return self._error_response("Request timeout", 32000)
    except Exception as e:
        self.logger.error(f"Unknown error: {e}")
        return self._error_response(str(e), 34000)
```

## Bot Status Management

AdapterManager includes a built-in Bot status tracking system that automatically maintains the online status, active time, and metadata of all registered Bots.

### Auto-Discovery Mechanism

When an adapter sends an event via `adapter.emit()`, the framework automatically checks the `self` field in the event:

- **meta events**: Perform corresponding operations based on `detail_type` (connect for registration/disconnect to mark offline/heartbeat to update active time)
- **normal events** (message/notice/request): Automatically discover the Bot and update active time

```python
# All events containing the self field will trigger auto-discovery
await self.adapter.emit({
    "type": "message",
    "platform": "myplatform",
    "self": {"platform": "myplatform", "user_id": "bot123"},
    # ...
})
# Bot "bot123" has been automatically registered (if appearing for the first time) and active time updated
```

### Meta Event Types

| `detail_type` | Description | Framework Behavior |
|---|---|---|
| `connect` | Bot connection | Register the Bot and trigger the `adapter.bot.online` lifecycle event |
| `disconnect` | Bot disconnect | Mark the Bot as offline and trigger the `adapter.bot.offline` lifecycle event |
| `heartbeat` | Bot heartbeat | Update Bot active time and metadata |

### Adapter Sending Meta Events

```python
class MyAdapter(BaseAdapter):
    async def _on_bot_connect(self, bot_id: str):
        await self.adapter.emit({
            "type": "meta",
            "detail_type": "connect",
            "platform": "myplatform",
            "self": {
                "platform": "myplatform",
                "user_id": bot_id,
                "user_name": "MyBot",
                "nickname": "MyBot",
            }
        })

    async def _on_bot_disconnect(self, bot_id: str):
        await self.adapter.emit({
            "type": "meta",
            "detail_type": "disconnect",
            "platform": "myplatform",
            "self": {"platform": "myplatform", "user_id": bot_id}
        })
```

### `self` Field Extended Information

In addition to the required `platform` and `user_id`, the `self` field also supports the following optional fields:

| Field | Description |
|---|---|
| `user_name` | Bot username |
| `nickname` | Bot nickname |
| `avatar` | Bot avatar URL |
| `account_id` | Multi-account identifier |

### Bot Status Query

```python
from ErisPulse import sdk

# Get single Bot info
info = sdk.adapter.get_bot_info("myplatform", "bot123")
# {"status": "online", "last_active": 1712345678.0, "info": {"nickname": "MyBot"}}

# List all Bots
all_bots = sdk.adapter.list_bots()

# List Bots for a specific platform
platform_bots = sdk.adapter.list_bots("myplatform")

# Check if Bot is online
is_online = sdk.adapter.is_bot_online("myplatform", "bot123")

# Get full status summary (suitable for WebUI display)
summary = sdk.adapter.get_status_summary()
# {"adapters": {"myplatform": {"status": "started", "bots": {...}}}}
```

### Listening to Bot Lifecycle

```python
from ErisPulse import sdk

@sdk.lifecycle.on("adapter.bot.online")
async def on_bot_online(data):
    platform = data.get("platform")
    bot_id = data.get("bot_id")
    sdk.logger.info(f"Bot online: {platform}/{bot_id}")

@sdk.lifecycle.on("adapter.bot.offline")
async def on_bot_offline(data):
    platform = data.get("platform")
    bot_id = data.get("bot_id")
    sdk.logger.info(f"Bot offline: {platform}/{bot_id}")
```

## Related Documentation

- [Getting Started with Adapter Development](getting-started.md) - Create your first adapter
- [SendDSL Guide](send-dsl.md) - Learn message sending
- [Adapter Best Practices](best-practices.md) - Develop high-quality adapters



### SendDSL 详解

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

| Method Name | Description | Return Value | Required |
|--------|------|---------|---------|
| `Raw_ob12(message)` | Send OneBot12 format message | `asyncio.Task` | **Must Implement** |

> **Important**: `Raw_ob12` is the core method of the adapter and **must be implemented**. It is the unified entry point for reverse conversion (OneBot12 → Platform). When not implemented, the base class will log an error and return a standard error response (`status: "failed"`, `retcode: 10002`). Standard methods (`Text`, `Image`, etc.) should internally delegate to `Raw_ob12`.

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

### Raw Messages and Message Building

`Raw_ob12` is the core entry point for reverse conversion (receiving OB12 message segments → platform API calls), and `MessageBuilder` is a chain-style message segment building tool used in conjunction with it.

> For complete `Raw_ob12` implementation specifications, `MessageBuilder` usage, and code examples, please refer to:
> - [Sending Method Specifications §6 Reverse Conversion Specifications](../../standards/send-method-spec.md#6-反向转换规范onebot12--平台)
> - [Sending Method Specifications §11 Message Builder](../../standards/send-method-spec.md#11-消息构建器-messagebuilder)

## Related Documentation

- [Adapter Development Getting Started](getting-started.md) - Create adapter
- [Adapter Core Concepts](core-concepts.md) - Understand adapter architecture
- [Adapter Best Practices](best-practices.md) - Develop high-quality adapters
- [Sending Method Naming Conventions](../../standards/send-type-naming.md) - Naming conventions



### 适配器开发最佳实践

# Adapter Development Best Practices

This document provides best practice recommendations for ErisPulse adapter development.

## Bot Status Management and Meta Events

Adapters should proactively send meta events via `adapter.emit()` to allow the framework to automatically track the Bot's connection status, online/offline status, and heartbeat information.

### 1. When to Send Meta Events

| Event | `detail_type` | Trigger Condition | Framework Behavior |
|------|--------------|------------------|-------------------|
| Connection | `"connect"` | When the Bot establishes a connection with the platform | Register the Bot and trigger the `adapter.bot.online` lifecycle event |
| Disconnection | `"disconnect"` | When the Bot disconnects from the platform | Mark the Bot as offline and trigger the `adapter.bot.offline` lifecycle event |
| Heartbeat | `"heartbeat"` | Sent periodically (recommended 30-60 seconds) | Update Bot's active time and meta information |

### 2. Sending Meta Events

```python
class MyAdapter(BaseAdapter):
    async def _ws_handler(self, websocket):
        bot_id = self._get_bot_id()

        # Bot online: send connect event
        await self.adapter.emit({
            "type": "meta",
            "detail_type": "connect",
            "platform": "myplatform",
            "self": {
                "platform": "myplatform",
                "user_id": bot_id,
                "user_name": "MyBot",
                "nickname": "My Robot",
                "avatar": "https://example.com/avatar.png",
            }
        })

        try:
            while True:
                data = await websocket.receive_text()
                event = self.convert(data)
                if event:
                    await self.adapter.emit(event)
        except WebSocketDisconnect:
            pass
        finally:
            # Bot offline: send disconnect event
            await self.adapter.emit({
                "type": "meta",
                "detail_type": "disconnect",
                "platform": "myplatform",
                "self": {
                    "platform": "myplatform",
                    "user_id": bot_id,
                }
            })
```

### 3. Heartbeat Events

Adapters should periodically send heartbeat events while the connection is alive to update the Bot's active time:

```python
class MyAdapter(BaseAdapter):
    async def _heartbeat_loop(self, bot_id: str):
        while self._connected:
            await self.adapter.emit({
                "type": "meta",
                "detail_type": "heartbeat",
                "platform": "myplatform",
                "self": {
                    "platform": "myplatform",
                    "user_id": bot_id,
                }
            })
            await asyncio.sleep(30)
```

### 4. Automatic Discovery of `self` Field

The framework's `adapter.emit()` will automatically handle the `self` field in all events (not just meta events):

- **Normal events** (message/notice/request): The `self` field will automatically discover and register the Bot.
- **`self` field extended information**: Supports optional fields `user_name`, `nickname`, `avatar`, `account_id`.

```python
# Including the self field in the converter automatically registers the Bot
onebot_event = {
    "type": "message",
    "detail_type": "private",
    "platform": "myplatform",
    "self": {
        "platform": "myplatform",
        "user_id": "bot123",
        "user_name": "MyBot",
        "nickname": "My Robot",
    },
    # ... other fields
}
await self.adapter.emit(onebot_event)
# Bot "bot123" has been automatically registered and active time updated
```

### 5. Bot Status Query

The framework provides the following query methods:

```python
from ErisPulse import sdk

# Get Bot detailed information
info = sdk.adapter.get_bot_info("myplatform", "bot123")
# {"status": "online", "last_active": 1712345678.0, "info": {"nickname": "MyBot"}}

# List all Bots (grouped by platform)
all_bots = sdk.adapter.list_bots()

# List Bots for a specific platform
platform_bots = sdk.adapter.list_bots("myplatform")

# Check if Bot is online
is_online = sdk.adapter.is_bot_online("myplatform", "bot123")

# Get complete status summary (suitable for WebUI display)
summary = sdk.adapter.get_status_summary()
# {"adapters": {"myplatform": {"status": "started", "bots": {...}}}}
```

## Connection Management

### 1. Implement Connection Retry

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
                        f"Connection failed, retry in {wait_time} seconds ({retry_count}/{max_retries}): {e}"
                    )
                    await asyncio.sleep(wait_time)
                else:
                    self.logger.error("Connection failed, maximum retry attempts reached")
                    raise
```

### 2. Connection State Management

```python
class MyAdapter(BaseAdapter):
    def __init__(self, sdk):
        super().__init__()
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
            self.logger.info("Connection disconnected")
        finally:
            self.connection = None
            self._connected = False
```

### 3. Heartbeat Keep-Alive and Meta Heartbeat

The adapter's heartbeat should accomplish two tasks simultaneously: send a heartbeat to the platform to keep the connection alive, and send a meta heartbeat event to the framework.

```python
class MyAdapter(BaseAdapter):
    async def start(self):
        self.connection = await self._connect_to_platform()
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())

    async def _heartbeat_loop(self):
        while self.connection:
            try:
                # 1. Send heartbeat keep-alive to platform
                await self.connection.send_json({"type": "ping"})

                # 2. Send meta heartbeat event to framework (update Bot active time)
                await self.adapter.emit({
                    "type": "meta",
                    "detail_type": "heartbeat",
                    "platform": "myplatform",
                    "self": {
                        "platform": "myplatform",
                        "user_id": self._bot_id,
                    }
                })

                await asyncio.sleep(30)
            except Exception as e:
                self.logger.error(f"Heartbeat failed: {e}")
                break
```

## Event Conversion

### 1. Strictly Follow OneBot12 Standard

```python
class MyPlatformConverter:
    def convert(self, raw_event):
        """Convert event"""
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
            "myplatform_raw": raw_event,  # Retain raw data (required)
            "myplatform_raw_type": raw_event.get("type", "")  # Raw type (required)
        }
        return onebot_event
```

### 2. Timestamp Normalization

```python
def _convert_timestamp(self, timestamp):
    """Convert to 10-digit second-level timestamp"""
    if not timestamp:
        return int(time.time())
    
    # If it is a millisecond-level timestamp
    if timestamp > 10**12:
        return int(timestamp / 1000)
    
    # If it is a second-level timestamp
    return int(timestamp)
```

### 3. Event ID Generation

```python
import uuid

def _generate_event_id(self, raw_event):
    """Generate event ID"""
    event_id = raw_event.get("event_id")
    if event_id:
        return str(event_id)
    # If the platform does not provide an ID, generate UUID
    return str(uuid.uuid4())
```

## SendDSL Implementation

### 1. Must Return Task Object

```python
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

### 2. Chaining Modifier Methods Return self

```python
class Send(BaseAdapter.Send):
    def At(self, user_id: str) -> 'Send':
        """@User"""
        if not hasattr(self, '_at_user_ids'):
            self._at_user_ids = []
        self._at_user_ids.append(user_id)
        return self  # Must return self
    
    def Reply(self, message_id: str) -> 'Send':
        """Reply message"""
        self._reply_message_id = message_id
        return self  # Must return self
```

### 3. Support Platform-Specific Methods

```python
class Send(BaseAdapter.Send):
    def Sticker(self, sticker_id: str):
        """Send sticker"""
        import asyncio
        return asyncio.create_task(
            self._adapter.call_api(
                endpoint="/send_sticker",
                sticker_id=sticker_id,
                recvId=self._target_id,
                recvType=self._target_type
            )
        )
    
    def Card(self, card_data: dict):
        """Send card message"""
        import asyncio
        return asyncio.create_task(
            self._adapter.call_api(
                endpoint="/send_card",
                card=card_data,
                recvId=self._target_id,
                recvType=self._target_type
            )
        )
```

## API Response

### 1. Standardize Response Format

```python
async def call_api(self, endpoint: str, **params):
    try:
        raw_response = await self._platform_api_call(endpoint, **params)
        
        return {
            "status": "ok" if raw_response.get("success") else "failed",
            "retcode": 0 if raw_response.get("success") else raw_response.get("code", 10001),
            "data": raw_response.get("data"),
            "message_id": raw_response.get("data", {}).get("message_id", ""),
            "message": "",
            "myplatform_raw": raw_response
        }
    except Exception as e:
        return {
            "status": "failed",
            "retcode": 34000,
            "data": None,
            "message_id": "",
            "message": str(e),
            "myplatform_raw": None
        }
```

### 2. Error Code Standards

Follow OneBot12 standard error codes:

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

### 1. Account Configuration Validation

```python
def _get_config(self):
    """Validate configuration"""
    config = self.config_manager.getConfig("MyAdapter", {})
    accounts = config.get("accounts", {})
    
    if not accounts:
        # Create default account
        default_account = {
            "token": "",
            "enabled": False
        }
        config["accounts"] = {"default": default_account}
        self.config_manager.setConfig("MyAdapter", config)
    
    return config
```

### 2. Account Selection Mechanism

```python
async def _get_account_for_message(self, event):
    """Select sending account based on event"""
    bot_id = event.get("self", {}).get("user_id")
    
    # Find matching account
    for account_name, account_config in self.accounts.items():
        if account_config.get("bot_id") == bot_id:
            return account_name
    
    # If not found, use the first enabled account
    for account_name, account_config in self.accounts.items():
        if account_config.get("enabled", True):
            return account_name
    
    return None
```

## Error Handling

### 1. Categorized Exception Handling

```python
async def call_api(self, endpoint: str, **params):
    try:
        response = await self._platform_api_call(endpoint, **params)
        return self._standardize_response(response)
    except aiohttp.ClientError as e:
        # Network error
        self.logger.error(f"Network error: {e}")
        return self._error_response("Network request failed", 33000)
    except asyncio.TimeoutError:
        # Timeout error
        self.logger.error(f"Request timeout: {endpoint}")
        return self._error_response("Request timeout", 32000)
    except json.JSONDecodeError:
        # JSON parsing error
        self.logger.error("JSON parsing failed")
        return self._error_response("Response format error", 10006)
    except Exception as e:
        # Unknown error
        self.logger.error(f"Unknown error: {e}", exc_info=True)
        return self._error_response(str(e), 34000)
```

### 2. Logging

```python
class MyAdapter(BaseAdapter):
    def __init__(self, sdk=None):
        super().__init__(sdk)
        self.logger = logger.get_child("MyAdapter")
    
    async def start(self):
        self.logger.info("Adapter starting...")
        # ...
        self.logger.info("Adapter startup completed")
    
    async def shutdown(self):
        self.logger.info("Adapter shutting down...")
        # ...
        self.logger.info("Adapter shutdown completed")
```

## Testing

### 1. Unit Tests

```python
import pytest
from ErisPulse.Core.Bases import BaseAdapter

class TestMyAdapter:
    def test_converter(self):
        """Test converter"""
        converter = MyPlatformConverter()
        raw_event = {"type": "message", "content": "Hello"}
        result = converter.convert(raw_event)
        assert result is not None
        assert result["platform"] == "myplatform"
        assert "myplatform_raw" in result
    
    def test_api_response(self):
        """Test API response format"""
        adapter = MyAdapter()
        response = adapter.call_api("/test", param="value")
        assert "status" in response
        assert "retcode" in response
```

### 2. Integration Tests

```python
@pytest.mark.asyncio
async def test_adapter_start():
    """Test adapter start"""
    adapter = MyAdapter()
    await adapter.start()
    assert adapter._connected is True

@pytest.mark.asyncio
async def test_send_message():
    """Test send message"""
    adapter = MyAdapter()
    await adapter.start()
    
    result = await adapter.Send.To("user", "123").Text("Hello")
    assert result is not None
```

## Reverse Conversion and Message Construction

`Raw_ob12` is a method that the adapter **must implement**, serving as the unified entry point for reverse conversion (OneBot12 → Platform). Standard methods (`Text`, `Image`, etc.) should delegate to `Raw_ob12`, and modifier states (`At`/`Reply`/`AtAll`) must be merged into message segments within `Raw_ob12`.

`MessageBuilder` is a message segment construction tool used in conjunction with `Raw_ob12`, supporting method chaining and rapid construction.

> For complete implementation specifications, code examples, and usage instructions, please refer to:
> - [Send Method Specification §6 Reverse Conversion Specification](../../standards/send-method-spec.md#6-reverse-conversion-specificationonebot12--platform)
> - [Send Method Specification §11 Message Builder](../../standards/send-method-spec.md#11-message-builder-messagebuilder)

## Platform Event Method Extension

Adapters can register platform-specific methods for the Event wrapper class, allowing module developers to access platform-specific data more conveniently.

### 1. Batch Register Using Mixin Classes (Recommended)

When a platform has multiple proprietary methods, using a Mixin class is recommended:

```python
# Register in the adapter's start() or at module level
from ErisPulse.Core.Event import register_event_mixin

class MyPlatformEventMixin:
    def get_chat_name(self):
        """Get chat name"""
        return self.get("myplatform_raw", {}).get("chat", {}).get("name", "")

    def is_official_message(self):
        """Determine if it is an official message"""
        raw = self.get("myplatform_raw", {})
        return raw.get("sender", {}).get("is_official", False)

    def get_message_type(self):
        """Get platform message type"""
        return self.get("myplatform_raw", {}).get("msg_type", "text")

# Batch register
register_event_mixin("myplatform", MyPlatformEventMixin)
```

### 2. Register Single Method Using Decorator

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
        # Cleanup platform event method registration
        unregister_platform_event_methods("myplatform")
        # ... other cleanup
```

> For more detailed registration and unregistration instructions, please refer to [Event System API - Register Platform Extension Methods](../../api-reference/event-system.md#adapter-register-platform-extension-methods).

## Documentation Maintenance

### 1. Maintain Platform Feature Documentation

Create a `{platform}.md` document under `docs-new/platform-guide/`:

```markdown



### 事件转换器

# Event Converter Implementation Guide

Event Converter is one of the core components of an adapter, responsible for converting platform native events to the ErisPulse unified OneBot12 standard event format.

## Converter Responsibilities

```
Platform Native Event ──→ Converter.convert() ──→ OneBot12 Standard Event
```

The Converter is only responsible for **forward conversion** (receiving direction), that is, converting platform native event data to OneBot12 standard format. Reverse conversion (sending direction) is handled by the `Send.Raw_ob12()` method.

### Core Principles

1. **Lossless Conversion**: Original data must be completely preserved in the `{platform}_raw` field
2. **Standard Compatibility**: Converted events must conform to OneBot12 standard format
3. **Platform Extension**: Platform-specific data is stored in fields with `{platform}_` prefix

## convert() Method

### Method Signature

```python
def convert(self, raw_event: dict) -> dict:
    """
    Convert platform native events to OneBot12 standard format

    :param raw_event: Platform native event data
    :return: OneBot12 standard format event dictionary
    """
    pass
```

### Return Value Structure

The converted event dictionary should include the following standard fields:

```python
{
    "id": "Event unique ID",
    "time": 1234567890,           # Unix timestamp (seconds)
    "type": "message",             # Event type
    "detail_type": "private",      # Detail type
    "platform": "myplatform",      # Platform name
    "self": {
        "platform": "myplatform",
        "user_id": "bot_user_id"
    },

    # Message event fields
    "user_id": "sender_id",
    "message": [...],              # OneBot12 message segment list
    "alt_message": "Plain text content",

    # Must preserve original data
    "myplatform_raw": { ... },     # Complete platform native event data
    "myplatform_raw_type": "Native event type name",
}
```

## Required Field Mapping

### Common Fields (All Event Types)

| OB12 Field | Type | Description |
|------------|------|-------------|
| `id` | str | Event unique identifier |
| `time` | int | Unix timestamp (seconds) |
| `type` | str | Event type: `message` / `notice` / `request` / `meta` |
| `detail_type` | str | Detail type: `private` / `group` / `friend` etc. |
| `platform` | str | Platform name, matches adapter registration name |
| `self` | dict | Bot info: `{"platform": "...", "user_id": "..."}` |

### Message Event Additional Fields

| OB12 Field | Type | Description |
|------------|------|-------------|
| `user_id` | str | Sender ID |
| `message` | list[dict] | OneBot12 message segment list |
| `alt_message` | str | Plain text fallback content |

### Notice Event Additional Fields

| OB12 Field | Type | Description |
|------------|------|-------------|
| `user_id` | str | Related user ID |
| `operator_id` | str | Operator ID (e.g., group member changes) |

## Message Segment Conversion

OneBot12 standard defines the following message segment types:

```python
# Text
{"type": "text", "data": {"text": "Hello"}}

# Image
{"type": "image", "data": {"file": "https://example.com/img.jpg"}}

# Audio
{"type": "audio", "data": {"file": "https://example.com/audio.mp3"}}

# Video
{"type": "video", "data": {"file": "https://example.com/video.mp4"}}

# File
{"type": "file", "data": {"file": "https://example.com/doc.pdf"}}

# Mention
{"type": "mention", "data": {"user_id": "123"}}

# Mention All
{"type": "mention_all", "data": {}}

# Reply
{"type": "reply", "data": {"message_id": "msg_123"}}
```

If a platform doesn't support certain message segment types, they can be omitted or converted to the closest standard type.

## Platform Extension Fields

Platform-specific data should be stored with `{platform}_` prefix to avoid conflicts with standard fields:

```python
{
    # Standard fields
    "type": "message",
    "detail_type": "group",
    # ...

    # Platform extension fields
    "myplatform_raw": { ... },          # Original event data (required)
    "myplatform_raw_type": "chat",      # Original event type (required)

    # Other platform-specific fields
    "myplatform_group_name": "Group name",
    "myplatform_sender_role": "admin",
}
```

> **Important**: The `{platform}_raw` field is required, as ErisPulse's event system and modules may depend on it to access platform raw data.

## Complete Example

Here's a complete Converter implementation:

```python
class MyConverter:
    def __init__(self, platform: str):
        self.platform = platform

    def convert(self, raw_event: dict) -> dict:
        event_type = raw_event.get("type", "")

        base_event = {
            "id": raw_event.get("id", ""),
            "time": raw_event.get("timestamp", 0),
            "platform": self.platform,
            "self": {
                "platform": self.platform,
                "user_id": raw_event.get("self_id", ""),
            },
            "myplatform_raw": raw_event,
            "myplatform_raw_type": event_type,
        }

        if event_type == "chat":
            return self._convert_message(raw_event, base_event)
        elif event_type == "notification":
            return self._convert_notice(raw_event, base_event)
        elif event_type == "request":
            return self._convert_request(raw_event, base_event)

        return base_event

    def _convert_message(self, raw: dict, base: dict) -> dict:
        base["type"] = "message"
        base["detail_type"] = "group" if raw.get("group_id") else "private"
        base["user_id"] = raw.get("sender_id", "")
        base["message"] = self._convert_message_segments(raw.get("content", ""))
        base["alt_message"] = raw.get("content", "")

        if raw.get("group_id"):
            base["group_id"] = raw["group_id"]

        return base

    def _convert_message_segments(self, content: str) -> list:
        segments = []
        if content:
            segments.append({"type": "text", "data": {"text": content}})
        return segments

    def _convert_notice(self, raw: dict, base: dict) -> dict:
        base["type"] = "notice"
        notification_type = raw.get("notification_type", "")

        if notification_type == "member_join":
            base["detail_type"] = "group_member_increase"
            base["user_id"] = raw.get("user_id", "")
            base["group_id"] = raw.get("group_id", "")
            base["operator_id"] = raw.get("operator_id", "")
        elif notification_type == "friend_add":
            base["detail_type"] = "friend_increase"
            base["user_id"] = raw.get("user_id", "")

        return base

    def _convert_request(self, raw: dict, base: dict) -> dict:
        base["type"] = "request"
        request_type = raw.get("request_type", "")

        if request_type == "friend":
            base["detail_type"] = "friend"
            base["user_id"] = raw.get("user_id", "")
            base["comment"] = raw.get("message", "")
        elif request_type == "group_invite":
            base["detail_type"] = "group"
            base["group_id"] = raw.get("group_id", "")
            base["user_id"] = raw.get("inviter_id", "")

        return base
```

## Best Practices

1. **Always preserve original data**: The `{platform}_raw` field cannot be omitted
2. **Use standard message segments**: Try to convert platform messages to OneBot12 standard message segments
3. **Set detail_type appropriately**: Use standard types (`private`/`group`/channel` etc.), don't customize
4. **Handle edge cases**: Raw events might be missing certain fields, use `.get()` and provide reasonable defaults
5. **Performance considerations**: `convert()` is called for every event, avoid executing time-consuming operations inside it

## Related Documentation

- [Adapter Core Concepts](core-concepts.md) - Overall adapter architecture
- [SendDSL Detailed Explanation](send-dsl.md) - Reverse conversion (sending direction)
- [Event Conversion Standard](../../standards/event-conversion.md) - Formal event conversion specification
- [Session Type System](../../advanced/session-types.md) - Session type mapping rules



=====
发布与工具
=====


### 发布适配器到模块商店

# Publishing and Module Store Guide

Publish your developed modules or adapters to the ErisPulse Module Store, allowing other users to easily discover and install them.

## Module Store Overview

The ErisPulse Module Store is a centralized module registry where users can browse, search, and install community-contributed modules and adapters through CLI tools.

### Browse and Discover

```bash
# List all remote available packages
epsdk list-remote

# Only view modules
epsdk list-remote -t modules

# Only view adapters
epsdk list-remote -t adapters

# Force refresh remote package list
epsdk list-remote -r
```

You can also visit the [ErisPulse official website](https://www.erisdev.com/#market) to browse the Module Store online.

### Supported Submission Types

| Type | Description | Entry-point Group |
|------|------|----------------|
| Module | Extend bot functionality, implement business logic | `erispulse.module` |
| Adapter | Connect to new messaging platforms | `erispulse.adapter` |

## Publishing Process

The entire publishing process is divided into four steps: Prepare Project → Publish to PyPI → Submit to Module Store → Review and Launch.

### Step 1: Prepare Project

Ensure your project contains the following files:

```
MyModule/
├── pyproject.toml      # Project configuration (required)
├── README.md           # Project description (required)
├── LICENSE             # Open source license (recommended)
└── MyModule/
    ├── __init__.py     # Package entry point
    └── ...
```

### Step 2: Configure pyproject.toml

According to the type you want to publish, correctly configure `entry-points`:

#### Module

```toml
[project]
name = "ErisPulse-MyModule"
version = "1.0.0"
description = "Module functionality description"
requires-python = ">=3.10"
license = { text = "MIT" }
authors = [ { name = "yourname" } ]
dependencies = [
    "ErisPulse>=2.0.0",
]

[project.entry-points."erispulse.module"]
"MyModule" = "MyModule:Main"
```

#### Adapter

```toml
[project]
name = "ErisPulse-MyAdapter"
version = "1.0.0"
description = "Adapter functionality description"
requires-python = ">=3.10"

[project.entry-points."erispulse.adapter"]
"myplatform" = "MyAdapter:MyAdapter"
```

> **Note**: It's recommended that package names start with `ErisPulse-` for easy user recognition. The entry-point key name (such as `"MyModule"`) will be used as the access name for the module in the SDK.

### Step 3: Publish to PyPI

```bash
# Install build tools
pip install build twine

# Build distribution packages
python -m build

# Publish to PyPI
python -m twine upload dist/*
```

After successful publication, confirm that your package can be installed via `pip install`:

```bash
pip install ErisPulse-MyModule
```

### Step 4: Submit to ErisPulse Module Store

After confirming your package is published to PyPI, go to [ErisPulse-ModuleRepo](https://github.com/ErisPulse/ErisPulse-ModuleRepo/issues/new?template=module_submission.md) to submit your application.

Fill in the following information:

#### Submission Type

Select the type you want to submit:
- Module
- Adapter

#### Basic Information

| Field | Description | Example |
|------|------|------|
| **Name** | Module/Adapter name | Weather |
| **Description** | Brief functional description | Weather query module supporting global cities |
| **Author** | Your name or GitHub username | MyName |
| **Repository URL** | Code repository URL | https://github.com/MyName/MyModule |

#### Technical Information

| Field | Description |
|------|------|
| **Minimum SDK Version Requirement** | e.g. `>=2.0.0` (if applicable) |
| **Dependencies** | Additional dependencies besides ErisPulse (if applicable) |

#### Tags

Separate with commas to help users search and discover your module. For example: `weather, query, tool`

#### Checklist

Before submitting, please confirm:
- Code follows ErisPulse development standards
- Contains appropriate documentation (README.md)
- Contains test cases (if applicable)
- Published on PyPI

### Step 5: Review and Launch

After submission, maintainers will review your application. Review points:

1. The package can be installed normally from PyPI
2. Entry-point configuration is correct and can be properly discovered by the SDK
3. Functionality matches the description
4. No security issues or malicious code
5. No significant conflicts with existing modules

After passing the review, your module will automatically appear in the Module Store.

## Updating Published Modules

When you update a module version:

1. Update `version` in `pyproject.toml`
2. Rebuild and upload to PyPI:
   ```bash
   python -m build
   python -m twine upload dist/*
   ```
3. The Module Store will automatically sync the latest version information from PyPI

Users can upgrade using the following command:

```bash
epsdk upgrade MyModule
```

## Development Mode Testing

Before official publication, you can test locally in editable mode:

```bash
# Install in editable mode
epsdk install -e /path/to/MyModule

# Or use pip
pip install -e /path/to/MyModule
```

## FAQ

### Q: Must package names start with `ErisPulse-`?

Not mandatory, but strongly recommended. This helps users identify ErisPulse ecosystem packages on PyPI.

### Q: Can a single package register multiple modules?

Yes. Configure multiple key-value pairs in `entry-points`:

```toml
[project.entry-points."erispulse.module"]
"ModuleA" = "MyPackage:ModuleA"
"ModuleB" = "MyPackage:ModuleB"
```

### Q: How to specify minimum SDK version requirements?

Set in `dependencies` in `pyproject.toml`:

```toml
dependencies = [
    "ErisPulse>=2.0.0",
]
```

The Module Store will check version compatibility to prevent users from installing incompatible modules.

### Q: How long does the review take?

Usually completed within 1-3 business days. You can check the review progress in the Issue.



### CLI 命令参考

# CLI Command Reference

The ErisPulse command-line tool provides project management and package management capabilities.

## Package Management Commands

| Command | Arguments | Description | Example |
|-------|------|------|------|
| `install` | `[package]... [--upgrade/-U] [--pre]` | Install modules/adapters | `epsdk install Yunhu` |
| `uninstall` | `<package>...` | Uninstall modules/adapters | `epsdk uninstall old-module` |
| `upgrade` | `[package]... [--force/-f] [--pre]` | Upgrade specified modules or all | `epsdk upgrade --force` |
| `self-update` | `[version] [--pre] [--force/-f]` | Update SDK itself | `epsdk self-update` |

## Information Query Commands

| Command | Arguments | Description | Example |
|-------|------|------|------|
| `list` | `[--type/-t <type>]` | List installed modules/adapters | `epsdk list -t modules` |
| | `[--outdated/-o]` | Only show upgradable packages | `epsdk list -o` |
| `list-remote` | `[--type/-t <type>]` | List remote available packages | `epsdk list-remote` |
| | `[--refresh/-r]` | Force refresh package list | `epsdk list-remote -r` |

## Execution Control Commands

| Command | Arguments | Description | Example |
|-------|------|------|------|
| `run` | `<script> [--reload]` | Run specified script | `epsdk run main.py --reload` |

## Project Management Commands

| Command | Arguments | Description | Example |
|-------|------|------|------|
| `init` | `[--project-name/-n <name>]` | Interactive project initialization | `epsdk init -n my_bot` |
| | `[--quick/-q]` | Quick mode, skip interaction | `epsdk init -q -n bot` |
| | `[--force/-f]` | Force override existing configuration | `epsdk init -f` |

## Parameter Reference

### Common Parameters

| Parameter | Short Option | Description |
|------|---------|------|
| `--help` | `-h` | Display help information |
| `--verbose` | `-v` | Display verbose output |

### install Parameters

| Parameter | Description |
|------|------|
| `[package]` | Package name to install, multiple can be specified |
| `--upgrade` | `-U` | Upgrade to latest version during install |
| `--pre` | Allow installing pre-release versions |

### list Parameters

| Parameter | Description |
|------|------|
| `--type` | `-t` | Specify type: `modules`, `adapters`, `all` |
| `--outdated` | `-o` | Only show upgradable packages |

### run Parameters

| Parameter | Description |
|------|------|
| `--reload` | Enable hot reload mode to monitor file changes |
| `--no-reload` | Disable hot reload mode |

## Interactive Installation

Running `epsdk install` without specifying a package name enters interactive installation:

```bash
epsdk install
```

The interactive interface provides:
1. Adapter selection
2. Module selection
3. Custom installation

## Common Usage

### Installing Modules

```bash
# Install a single module
epsdk install Weather

# Install multiple modules
epsdk install Yunhu Weather

# Upgrade module
epsdk install Weather -U
```

### Listing Modules

```bash
# List all modules
epsdk list

# List only adapters
epsdk list -t adapters

# List only upgradable modules
epsdk list -o
```

### Uninstalling Modules

```bash
# Uninstall a single module
epsdk uninstall Weather

# Uninstall multiple modules
epsdk uninstall Yunhu Weather
```

### Upgrading Modules

```bash
# Upgrade all modules
epsdk upgrade

# Upgrade specified module
epsdk upgrade Weather

# Force upgrade
epsdk upgrade -f
```

### Running Projects

```bash
# Normal run
epsdk run main.py

# Hot reload mode
epsdk run main.py --reload
```

### Initializing Projects

```bash
# Interactive initialization
epsdk init

# Quick initialization
epsdk init -q -n my_bot



======
API 参考
======


### 适配器系统 API

# Adapter System API

This document details the API of the ErisPulse adapter system.

## Adapter Manager

### Getting Adapters

```python
from ErisPulse import sdk

# Get adapter by name
adapter = sdk.adapter.get("platform_name")

# Or access directly via property
adapter = sdk.adapter.platform_name
```

### Using Adapter Event Listening
> Generally, it is recommended to use the `Event` module for event listening/processing;
>
> Meanwhile, the `Event` module provides powerful wrappers, bringing more convenience to your module development.

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
# The methods below show cases with parameters passed; without parameters, it means starting/stopping all registered adapters
await sdk.adapter.startup(["platform1", "platform2"])
await sdk.adapter.shutdown(["platform1", "platform2"])

# Check if adapter is running
is_running = sdk.adapter.is_running("platform_name")

# List all running adapters
running = sdk.adapter.list_running()
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
from ErisPulse import sdk
from ErisPulse.Core import BaseAdapter

class MyAdapter(BaseAdapter):
    def __init__(self):
        self.sdk = sdk
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

## Bot Status Management

The adapter informs the framework of the Bot's connection status by sending OneBot12 standard **`meta` events**. The system automatically extracts Bot information from these events for status tracking.

### Meta Event Types

The adapter should send the following three types of `meta` events:

| `type` | `detail_type` | Description | Trigger Timing |
|--------|--------------|------|---------|
| `meta` | `connect` | Bot goes online | After the adapter successfully establishes a connection with the platform |
| `meta` | `heartbeat` | Bot heartbeat | Sent periodically (recommended 30-60 seconds) |
| `meta` | `disconnect` | Bot disconnects | When a disconnection is detected |

### Self Field Extension

ErisPulse extends the OneBot12 standard `self` field with the following optional fields:

| Field | Type | Description |
|------|------|------|
| `self.platform` | string | Platform name (OB12 standard) |
| `self.user_id` | string | Bot user ID (OB12 standard) |
| `self.user_name` | string | Bot nickname (ErisPulse extension) |
| `self.avatar` | string | Bot avatar URL (ErisPulse extension) |
| `self.account_id` | string | Multi-account identifier (ErisPulse extension) |

### Meta Event Format

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

System Processing: Register the Bot, mark as `online`, and trigger the `adapter.bot.online` lifecycle event.

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

System Processing: Update `last_active` time (metadata updates are also supported in heartbeats).

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

System Processing: Mark the Bot as `offline` and trigger the `adapter.bot.offline` lifecycle event.

### Auto-Discovery via Normal Events

In addition to `meta` events, the `self` field in normal events (`message`/`notice`/`request`) also triggers automatic discovery and registration of the Bot, as well as updating the active time. This means that even if the adapter does not send a `connect` event, the framework can discover the Bot from the first normal event.

### Adapter Integration Example

```python
class MyAdapter(BaseAdapter):
    async def start(self):
        # Establish connection with platform...
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
        # Disconnect, send disconnect event
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

# List Bots for a specific platform
tg_bots = sdk.adapter.list_bots("telegram")

# Get details of a single Bot
info = sdk.adapter.get_bot_info("telegram", "123456")

# Check if Bot is online
if sdk.adapter.is_bot_online("telegram", "123456"):
    print("Bot is online")
```

### Bot Status Values

| Status | Description |
|------|------|
| `online` | Online (continuously receiving events or actively marked by the adapter) |
| `offline` | Offline (actively marked by the adapter or automatically set on system shutdown) |
| `unknown` | Unknown (registered but status unconfirmed) |

### Lifecycle Events

| Event Name | Trigger Timing | Data |
|--------|---------|------|
| `adapter.bot.online` | When a new Bot is automatically discovered for the first time | `{platform, bot_id, status}` |
| `adapter.status.change` | Adapter status change (starting/started/stopping/stopped/stop_failed) | `{platform, status}` |

```python
# Listen to Bot online event
@sdk.lifecycle.on("adapter.bot.online")
def on_bot_online(event):
    print(f"Bot online: {event['data']['platform']}/{event['data']['bot_id']}")

# Listen to adapter status change
@sdk.lifecycle.on("adapter.status.change")
def on_status_change(event):
    print(f"Adapter status: {event['data']['platform']} -> {event['data']['status']}")
```

> When the system shuts down (`shutdown`), all Bots will automatically be marked as `offline`.

## Related Documentation

- [Core Modules API](core-modules.md) - Core Modules API
- [Event System API](event-system.md) - Event Module API
- [Adapter Development Guide](../developer-guide/adapters/) - Developing Platform Adapters



### 核心模块 API

# Core Module API

This document details the ErisPulse core module API.

## Storage Module

### Basic Operations

```python
from ErisPulse import sdk

# Set value
sdk.storage.set("key", "value")

# Get value
value = sdk.storage.get("key", default_value)

# Get all keys
keys = sdk.storage.keys()

# Delete value
sdk.storage.delete("key")
```

### Transaction Operations

```python
# Use transactions to ensure data consistency
with sdk.storage.transaction():
    sdk.storage.set("key1", "value1")
    sdk.storage.set("key2", "value2")
    # If any operation fails, all changes will be rolled back
```

### Batch Operations

```python
# Batch set
sdk.storage.set_multi({
    "key1": "value1",
    "key2": "value2",
    "key3": "value3"
})

# Batch get
values = sdk.storage.get_multi(["key1", "key2", "key3"])

# Batch delete
sdk.storage.delete_multi(["key1", "key2", "key3"])
```

## Config Module

### Reading Configuration

```python
from ErisPulse import sdk

# Get configuration
config = sdk.config.getConfig("MyModule", {})

# Get nested configuration
value = sdk.config.getConfig("MyModule.subkey.value", "default")
```

### Writing Configuration

```python
# Set configuration
sdk.config.setConfig("MyModule", {"key": "value"})

# Set nested configuration
sdk.config.setConfig("MyModule.subkey.value", "new_value")
```

### Configuration Example

```python
def _load_config(self):
    config = sdk.config.getConfig("MyModule")
    if not config:
        # Create default configuration
        default_config = {
            "api_url": "https://api.example.com",
            "timeout": 30,
            "cache_ttl": 3600
        }
        sdk.config.setConfig("MyModule", default_config, immediate=True)  # When the third parameter is True, save the configuration immediately, making it convenient for users to directly modify the configuration file
        return default_config
    return config
```

## Logger Module

### Basic Logging

```python
from ErisPulse import sdk

# Different log levels
sdk.logger.debug("Debug info")
sdk.logger.info("Runtime info")
sdk.logger.warning("Warning info")
sdk.logger.error("Error info")
sdk.logger.critical("Fatal error")
```

### Child Loggers

```python
# Get child logger
child_logger = sdk.logger.get_child("MyModule")
child_logger.info("Submodule log")

# Submodules can have their own child loggers, allowing for more precise control over log output
child_logger.get_child("utils")
```

### Log Output

```python
# Set output file
sdk.logger.set_output_file("app.log")

# Save logs to file
sdk.logger.save_logs("log.txt")
```

## Adapter Module

### Getting Adapters

```python
from ErisPulse import sdk

# Get adapter instance
adapter = sdk.adapter.get("platform_name")

# Access via attribute
adapter = sdk.adapter.platform_name
```

### Adapter Events

```python
# Listen for standard events
@sdk.adapter.on("message")
async def handle_message(event):
    pass

# Listen for events on a specific platform
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

# Check if adapter exists
exists = sdk.adapter.exists("platform_name")

# Enable/Disable adapter
sdk.adapter.enable("platform_name")
sdk.adapter.disable("platform_name")

# Start/Shutdown adapter
await sdk.adapter.startup(["platform1", "platform2"])
await sdk.adapter.shutdown(["platform1", "platform2"])

# Check if adapter is running
is_running = sdk.adapter.is_running("platform_name")

# List all running adapters
running = sdk.adapter.list_running()
```

## Module Module

### Getting Modules

```python
from ErisPulse import sdk

# Get module instance
module = sdk.module.get("ModuleName")

# Access via attribute
module = sdk.module.ModuleName
module = sdk.ModuleName
```

### Module Management

```python
# Check if module exists
exists = sdk.module.exists("ModuleName")

# Check if module is loaded
is_loaded = sdk.module.is_loaded("ModuleName")

# Check if module is enabled
is_enabled = sdk.module.is_enabled("ModuleName")

# Enable/Disable module
sdk.module.enable("ModuleName")
sdk.module.disable("ModuleName")

# Load module
await sdk.module.load("ModuleName")

# Unload module
await sdk.module.unload("ModuleName")

# List loaded modules
loaded = sdk.module.list_loaded()

# List registered modules
registered = sdk.module.list_registered()

# Get module information
info = sdk.module.get_info("ModuleName")

# Get module status summary
summary = sdk.module.get_status_summary()
# {"modules": {"ModuleName": {"status": "loaded", "enabled": True, "is_base_module": True}}}

# Check if module is running (equivalent to is_loaded)
is_running = sdk.module.is_running("ModuleName")

# List all running modules
running = sdk.module.list_running()
```

## Lifecycle Module

### Event Submission

```python
from ErisPulse import sdk

# Submit custom event
await sdk.lifecycle.submit_event(
    "custom.event",
    data={"key": "value"},
    source="MyModule",
    msg="Custom event description"
)
```

### Event Listening

```python
# Listen for specific event
@sdk.lifecycle.on("module.init")
async def handle_module_init(event_data):
    print(f"Module initialization: {event_data}")

# Listen for parent event
@sdk.lifecycle.on("module")
async def handle_any_module_event(event_data):
    print(f"Module event: {event_data}")

# Listen for all events
@sdk.lifecycle.on("*")
async def handle_any_event(event_data):
    print(f"System event: {event_data}")
```

### Timer

```python
# Start timer
sdk.lifecycle.start_timer("my_operation")

# ... Perform operations ...

# Get duration
duration = sdk.lifecycle.get_duration("my_operation")

# Stop timer
total_time = sdk.lifecycle.stop_timer("my_operation")
```

## Router Module

### HTTP Routes

```python
from ErisPulse import sdk
from fastapi import Request

# Register HTTP route
async def handler(request: Request):
    data = await request.json()
    return {"status": "ok", "data": data}

sdk.router.register_http_route(
    module_name="MyModule",
    path="/api",
    handler=handler,
    methods=["POST"]
)

# Unregister route
sdk.router.unregister_http_route("MyModule", "/api")
```

### WebSocket Routes

```python
from ErisPulse import sdk
from fastapi import WebSocket

# Register WebSocket route (automatically accepts connection by default)
async def websocket_handler(websocket: WebSocket):
    # No manual accept needed by default, it is called internally automatically
    while True:
        data = await websocket.receive_text()
        await websocket.send_text(f"Echo: {data}")

sdk.router.register_websocket(
    module_name="my_module",
    path="/ws",
    handler=websocket_handler,
    auto_accept=True  # Default is True, can be omitted
)

# Register WebSocket route (manual connection control)
async def manual_websocket_handler(websocket: WebSocket):
    # Decide whether to accept connection based on condition
    if some_condition:
        await websocket.accept()
        # Handle connection...
    else:
        await websocket.close(code=1008, reason="Not allowed")

async def auth_handler(websocket: WebSocket) -> bool:
    token = websocket.query_params.get("token")
    if token == "<PASSWORD>":
        return True
    return False

sdk.router.register_websocket(
    module_name="my_module",
    path="/secure_ws",
    handler=manual_websocket_handler,
    auth_handler=auth_handler,
    auto_accept=False  # Manual connection control
)

# Unregister route
sdk.router.unregister_websocket("MyModule", "/ws")
```

**Parameter Description:**

- `module_name`: Module name
- `path`: WebSocket path
- `handler`: Handler function
- `auth_handler`: Optional authentication function
- `auto_accept`: Whether to automatically accept connection (default `True`)
  - `True`: Framework automatically calls `websocket.accept()`, handler does not need to call it manually
  - `False`: handler must call `websocket.accept()` or `websocket.close()` itself

### Route Information

```python
# Get FastAPI application instance
app = sdk.router.get_app()

# Add middleware
@app.middleware("http")
async def add_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Custom-Header"] = "value"
    return response
```

## Related Documents

- [Event System API](event-system.md) - Event Module API
- [Adapter System API](adapter-system.md) - Adapter Management API



====
高级主题
====


### 生命周期管理

# Lifecycle Management

ErisPulse provides a complete lifecycle event system for monitoring the running status of various system components. Lifecycle events support dot-notation event listening; for example, you can listen to `module.init` to capture all module initialization events.

## Standard Lifecycle Events

The system defines the following standard event categories:

```python
STANDARD_EVENTS = {
    "core": ["init.start", "init.complete"],
    "module": ["load", "init", "unload"],
    "adapter": ["load", "start", "status.change", "stop", "stopped"],
    "server": ["start", "stop"]
}
```

## Event Data Format

All lifecycle events follow a standard format:

```json
{
    "event": "Event Name",
    "timestamp": 1234567890,
    "data": {},
    "source": "ErisPulse",
    "msg": "Event Description"
}
```

## Event Handling Mechanism

### Dot-notation Events

ErisPulse supports dot-notation event naming, such as `module.init`. When a specific event is triggered, its parent events are also triggered:

- When the `module.init` event is triggered, the `module` event is also triggered.
- When the `adapter.status.change` event is triggered, the `adapter.status` and `adapter` events are also triggered.

### Wildcard Event Handlers

You can register a `*` event handler to capture all events.

## Standard Lifecycle Events

### Core Initialization Events

| Event Name | Trigger Timing | Data Structure |
|---------|---------|---------|
| `core.init.start` | When core initialization starts | `{}` |
| `core.init.complete` | When core initialization completes | `{"duration": "Initialization duration (seconds)", "success": true/false}` |

### Module Lifecycle Events

| Event Name | Trigger Timing | Data Structure |
|---------|---------|---------|
| `module.load` | When module loading completes | `{"module_name": "Module Name", "success": true/false}` |
| `module.init` | When module initialization completes | `{"module_name": "Module Name", "success": true/false}` |
| `module.unload` | When module is unloaded | `{"module_name": "Module Name", "success": true/false}` |

### Adapter Lifecycle Events

| Event Name | Trigger Timing | Data Structure |
|---------|---------|---------|
| `adapter.load` | When adapter loading completes | `{"platform": "Platform Name", "success": true/false}` |
| `adapter.start` | When adapter starts launching | `{"platforms": ["List of Platform Names"]}` |
| `adapter.status.change` | When adapter status changes | `{"platform": "Platform Name", "status": "Status", "retry_count": Retry Count, "error": "Error Message"}` |
| `adapter.stop` | When adapter starts shutting down | `{}` |
| `adapter.stopped` | When adapter has shut down completely | `{}` |

### Server Lifecycle Events

| Event Name | Trigger Timing | Data Structure |
|---------|---------|---------|
| `server.start` | When server starts | `{"base_url": "Base URL","host": "Host Address", "port": "Port Number"}` |
| `server.stop` | When server stops | `{}` |

## Usage Examples

### Lifecycle Event Listening

```python
from ErisPulse.Core import lifecycle

# Listen to specific event
@lifecycle.on("module.init")
async def module_init_handler(event_data):
    print(f"Module {event_data['data']['module_name']} initialization completed")

# Listen to parent event (dot-notation)
@lifecycle.on("module")
async def on_any_module_event(event_data):
    print(f"Module event: {event_data['event']}")

# Listen to all events (wildcard)
@lifecycle.on("*")
async def on_any_event(event_data):
    print(f"System event: {event_data['event']}")
```

### Submitting Lifecycle Events

```python
from ErisPulse.Core import lifecycle

# Basic event submission
await lifecycle.submit_event(
    "custom.event",
    data={"custom_field": "custom_value"},
    source="MyModule",
    msg="Custom event description"
)
```

### Timer Functionality

The lifecycle system provides timer functionality for performance measurement:

```python
from ErisPulse.Core import lifecycle

# Start timing
lifecycle.start_timer("my_operation")

# Execute some operations...

# Get duration (without stopping the timer)
elapsed = lifecycle.get_duration("my_operation")
print(f"Has run for {elapsed} seconds")

# Stop timer and get duration
total_time = lifecycle.stop_timer("my_operation")
print(f"Operation completed, total time taken {total_time} seconds")
```

## Using Lifecycle in Modules

```python
from ErisPulse.Core.Bases import BaseModule
from ErisPulse import sdk

class Main(BaseModule):
    async def on_load(self, event):
        # Listen to module lifecycle events
        @sdk.lifecycle.on("module.load")
        async def on_module_load(event_data):
            module_name = event_data['data'].get('module_name')
            if module_name != "MyModule":
                sdk.logger.info(f"Other module loaded: {module_name}")
        
        # Submit custom event
        await sdk.lifecycle.submit_event(
            "custom.ready",
            source="MyModule",
            msg="MyModule is ready to receive events"
        )
```

## Notes

1.  **Event Source Identification**: When submitting custom events, it is recommended to set a clear `source` value to facilitate tracking the event source.
2.  **Event Naming Conventions**: It is recommended to use dot-notation for event naming to facilitate parent-level listening.
3.  **Timer Naming**: Timer IDs should be descriptive to avoid conflicts with other components.
4.  **Asynchronous Processing**: All lifecycle event handlers are asynchronous; do not block the event loop.
5.  **Error Handling**: Exception handling should be implemented in event handlers to prevent affecting other listeners.
6.  **Loading Priority**: It is recommended to set high priority for loading strategies and disable lazy loading.

## Related Documentation

- [Module Development Guide](../developer-guide/modules/getting-started.md) - Learn about module lifecycle methods
- [Best Practices](../developer-guide/modules/best-practices.md) - Recommendations for using lifecycle events



### 懒加载系统

# Lazy Loading Module System

The ErisPulse SDK provides a powerful lazy loading module system, allowing modules to be initialized only when actually needed, thereby significantly improving application startup speed and memory efficiency.

## Overview

The lazy loading module system is one of the core features of ErisPulse. It works through the following mechanisms:

- **Delayed Initialization**: Modules are actually loaded and initialized only when they are accessed for the first time.
- **Transparent Usage**: For developers, there is almost no difference in usage between lazy-loaded modules and ordinary modules.
- **Automatic Dependency Management**: Module dependencies are automatically initialized when used.
- **Lifecycle Support**: For modules inheriting from `BaseModule`, lifecycle methods are automatically called.

## How It Works

### The LazyModule Class

The core of the lazy loading system is the `LazyModule` class, which acts as a wrapper that actually initializes the module only upon first access.

### Initialization Process

When a module is accessed for the first time, `LazyModule` performs the following operations:

1. Retrieves the `__init__` parameter information of the module class.
2. Decides whether to pass the `sdk` reference based on the parameters.
3. Sets the `moduleInfo` attribute of the module.
4. For modules inheriting from `BaseModule`, calls the `on_load` method.
5. Triggers the `module.init` lifecycle event.

## Configuring Lazy Loading

### Global Configuration

Enable/disable global lazy loading in the configuration file:

```toml
[ErisPulse.framework]
enable_lazy_loading = true  # true=enable lazy loading (default), false=disable lazy loading
```

### Module-level Control

Modules can control their loading strategy by implementing the static method `get_load_strategy()`:

```python
from ErisPulse.Core.Bases import BaseModule
from ErisPulse.loaders import ModuleLoadStrategy

class MyModule(BaseModule):
    @staticmethod
    def get_load_strategy():
        """Return the module loading strategy"""
        return ModuleLoadStrategy(
            lazy_load=False,  # Returning False means immediate loading
            priority=100      # Loading priority, higher value means higher priority
        )
```

## Using Lazy Loaded Modules

### Basic Usage

For developers, lazy-loaded modules are almost indistinguishable from ordinary modules in terms of usage:

```python
# Access lazy-loaded modules via SDK
from ErisPulse import sdk

# The following access will trigger module lazy loading
result = await sdk.my_module.my_method()
```

### Asynchronous Initialization

For modules requiring asynchronous initialization, it is recommended to load them explicitly first:

```python
# Explicitly load the module first
await sdk.load_module("my_module")

# Then use the module
result = await sdk.my_module.my_method()
```

### Synchronous Initialization

For modules that do not require asynchronous initialization, you can access them directly:

```python
# Direct access will automatically trigger synchronous initialization
result = sdk.my_module.some_sync_method()
```

## Best Practices

### Scenarios Recommended for Lazy Loading (lazy_load=True)

- Passively called utility classes
- Passive class modules

### Scenarios Recommended for Disabling Lazy Loading (lazy_load=False)

- Modules registering triggers (e.g., command handlers, message handlers)
- Lifecycle event listeners
- Scheduled task modules
- Modules that need to be initialized when the application starts

### Loading Priority

```python
from ErisPulse.loaders import ModuleLoadStrategy

class MyModule(BaseModule):
    @staticmethod
    def get_load_strategy():
        return ModuleLoadStrategy(
            lazy_load=False,  # Load immediately
            priority=100      # High priority, higher value means higher priority
        )
```

## Notes

1. If your module uses lazy loading, it will never be initialized if it is never called within ErisPulse by other modules.
2. If your module includes components such as Event listeners, or other similar active monitoring modules, please be sure to declare that they need to be loaded immediately, otherwise it will affect the normal business logic of your module.
3. We do not recommend disabling lazy loading; unless there are special requirements, doing so may lead to issues such as dependency management and lifecycle event problems.

## Related Documentation

- [Module Development Guide](../developer-guide/modules/getting-started.md) - Learn to develop modules
- [Best Practices](../developer-guide/modules/best-practices.md) - Learn more best practices



====
技术标准
====


### 会话类型标准

# ErisPulse Session Type Standards

This document defines the session type standards supported by ErisPulse, including receiving event types and sending target types.

## 1. Core Concepts

### 1.1 Receive Type && Send Type

ErisPulse distinguishes two session types:

- **Receive Type (Receive Type)**: The `detail_type` field for received events
- **Send Type (Send Type)**: The target type for the `Send.To()` method when sending messages

### 1.2 Type Mapping

```
Receive Type (detail_type)     Send Type (Send.To)
─────────────────        ────────────────
private                 →        user
group                   →        group
channel                 →        channel
guild                   →        guild
thread                  →        thread
user                    →        user
```

**Key Points**:
- `private` is the type during reception; `user` must be used during sending
- `group`, `channel`, `guild`, and `thread` have the same type for both reception and sending
- The system performs automatic type conversion, so no manual handling is required (meaning you can directly use the obtained receive type for sending). However, in practice, you do not need to consider these; the existence of the Event wrapper class allows you to directly use the `event.reply()` method without worrying about type conversion.

## 2. Standard Session Types

### 2.1 OneBot12 Standard Types

#### private
- **Receive Type**: `private`
- **Send Type**: `user`
- **Description**: One-on-one private chat messages
- **ID Field**: `user_id`
- **Applicable Platforms**: All platforms that support private chat

#### group
- **Receive Type**: `group`
- **Send Type**: `group`
- **Description**: Group chat messages, including various forms of groups (such as Telegram supergroups)
- **ID Field**: `group_id`
- **Applicable Platforms**: All platforms that support group chat

#### user
- **Receive Type**: `user`
- **Send Type**: `user`
- **Description**: User type; some platforms (such as Telegram) represent private chats as `user` rather than `private`
- **ID Field**: `user_id`
- **Applicable Platforms**: Platforms like Telegram

### 2.2 ErisPulse Extended Types

#### channel
- **Receive Type**: `channel`
- **Send Type**: `channel`
- **Description**: Channel messages, supporting broadcast messages to multiple users
- **ID Field**: `channel_id`
- **Applicable Platforms**: Discord, Telegram, Line, etc.

#### guild
- **Receive Type**: `guild`
- **Send Type**: `guild`
- **Description**: Server/Community messages, typically used for Discord Guild-level events
- **ID Field**: `guild_id`
- **Applicable Platforms**: Discord, etc.

#### thread
- **Receive Type**: `thread`
- **Send Type**: `thread`
- **Description**: Topic/Sub-channel messages, used for sub-discussion areas within communities
- **ID Field**: `thread_id`
- **Applicable Platforms**: Discord Threads, Telegram Topics, etc.

## 3. Platform Type Mapping

### 3.1 Mapping Principles

Adapters are responsible for mapping native platform types to ErisPulse standard types:

```
Platform Native Type → ErisPulse Standard Type → Send Type
```

### 3.2 Common Platform Mapping Examples

#### Telegram
```
Telegram Type          ErisPulse Receive Type    Send Type
─────────────────      ────────────────       ───────────
private                private                 user
group                  group                   group
supergroup             group                   group  # Mapped to group
channel                channel                 channel
```

#### Discord
```
Discord Type          ErisPulse Receive Type    Send Type
─────────────────      ────────────────       ───────────
Direct Message         private                user
Text Channel           channel                channel
Guild                  guild                  guild
Thread                 thread                 thread
```

#### OneBot11
```
OneBot11 Type        ErisPulse Receive Type    Send Type
─────────────────      ────────────────       ───────────
private                private                user
group                  group                  group
discuss                group                  group  # Mapped to group
```

## 4. Custom Type Extensions

### 4.1 Registering Custom Types

Adapters can register custom session types:

```python
from ErisPulse.Core.Event import register_custom_type

# Register custom type
register_custom_type(
    receive_type="my_custom_type",
    send_type="custom",
    id_field="custom_id",
    platform="MyPlatform"
)
```

### 4.2 Using Custom Types

After registration, the system automatically handles conversion and inference for that type:

```python
# Automatic inference
receive_type = infer_receive_type(event, platform="MyPlatform")
# Returns: "my_custom_type"

# Convert to send type
send_type = convert_to_send_type(receive_type, platform="MyPlatform")
# Returns: "custom"

# Get corresponding ID
target_id = get_target_id(event, platform="MyPlatform")
# Returns: event["custom_id"]
```

### 4.3 Unregistering Custom Types

```python
from ErisPulse.Core.Event import unregister_custom_type

unregister_custom_type("my_custom_type", platform="MyPlatform")
```

## 5. Automatic Type Inference

When an event lacks a clear `detail_type` field, the system automatically infers the type based on existing ID fields:

### 5.1 Inference Priority

```
Priority (High to Low):
1. group_id     → group
2. channel_id   → channel
3. guild_id     → guild
4. thread_id    → thread
5. user_id      → private
```

### 5.2 Usage Examples

```python
# Event only has group_id
event = {"group_id": "123", "user_id": "456"}
receive_type = infer_receive_type(event)
# Returns: "group" (prefers group_id)

# Event only has user_id
event = {"user_id": "123"}
receive_type = infer_receive_type(event)
# Returns: "private"
```

## 6. API Usage Examples

### 6.1 Sending Messages

```python
from ErisPulse import adapter

# Send to user
await adapter.myplatform.Send.To("user", "123").Text("Hello")

# Send to group
await adapter.myplatform.Send.To("group", "456").Text("Hello")

# Automatic conversion private → user (not recommended, may have compatibility issues)
await adapter.myplatform.Send.To("private", "789").Text("Hello")
# Internally automatically converted to: Send.To("user", "789") # Using user directly as the session type is a better choice
```

### 6.2 Event Reply

```python
from ErisPulse.Core.Event import Event

# Event.reply() handles type conversion automatically
await event.reply("Reply content")
# Internally automatically uses the correct send type
```

### 6.3 Command Handling

```python
from ErisPulse.Core.Event import command

@command(name="test")
async def handle_test(event):
    # System automatically handles session type
    # No need to manually judge whether it is group_id or user_id
    await event.reply("Command executed successfully")
```

## 7. Best Practices

### 7.1 Adapter Developers

1. **Use Standard Mappings**: Map to standard types as much as possible instead of creating new types
2. **Correct Conversion**: Ensure the mapping relationship between receive types and send types is correct
3. **Preserve Raw Data**: Keep original event types in `{platform}_raw`
4. **Documentation**: Explain type mappings in adapter documentation

### 7.2 Module Developers

1. **Use Utility Methods**: Use utility methods like `get_send_type_and_target_id()`
2. **Avoid Hardcoding**: Do not write code like `if group_id else "private"`
3. **Consider All Types**: Code should support all standard types, not just private/group
4. **Flexible Design**: Use methods of the event wrapper rather than directly accessing fields

### 7.3 Type Inference

- **Prefer `detail_type`**: If there is a clear field, do not perform inference
- **Use Inference Reasonably**: Only use it when there is no clear type
- **Pay Attention to Priority**: Understand inference priority to avoid unexpected results

## 8. Common Questions

### Q1: Why does private convert to user during sending?
A: This is a requirement of the OneBot12 standard. `private` is a concept during reception, and using `user` during sending is more semantically appropriate.

### Q2: How to support new session types?
A: Register custom types via `register_custom_type()`, or use standard types like `channel` and `guild`.

### Q3: What if the event has no `detail_type`?
A: The system will automatically infer it based on the existing ID fields. The priority is: group > channel > guild > thread > user.

### Q4: How does the adapter map Telegram supergroup?
A: In the adapter's conversion logic, map `supergroup` to the standard `group` type.

### Q5: How to handle special platforms like email?
A: For non-generic or platform-specific types, use `{platform}_raw` and `{platform}_raw_type` to preserve raw data, and let the adapter handle it.

## 9. Related Documentation

- [Event Conversion Standard](event-conversion.md) - Complete event conversion specification
- [Send Method Specification](send-method-spec.md) - Naming and parameter specification for Send class methods
- [Adapter Development Guide](../developer-guide/adapters/) - Complete guide for adapter development



### 事件转换标准

# Adapter Standardization Conversion Specification

## 1. Core Principles
1.  **Strict Compatibility:** All standard fields must fully comply with the OneBot12 specification.
2.  **Explicit Extension:** Platform-specific features must add a `{platform}_` prefix (e.g., yunhu_form).
3.  **Data Integrity:** Original event data must be preserved in the `{platform}_raw` field, and the original event type must be preserved in the `{platform}_raw_type` field.
4.  **Time Unification:** All timestamps must be converted to 10-digit Unix timestamps (seconds).
5.  **Platform Unification:** The `platform` item name must be consistent with the name/alias registered in ErisPulse.

## 2. Standard Field Requirements

### 2.1 Required Fields
| Field | Type | Description |
|-------|------|-------------|
| id | string | Unique event identifier |
| time | integer | Unix timestamp (seconds) |
| type | string | Event type |
| detail_type | string | Event detail type (see [Session Types Standard](session-types.md)) |
| platform | string | Platform name |
| self | object | Bot self-information |
| self.platform | string | Platform name |
| self.user_id | string | Bot user ID |

**detail_type Specification**:
- Must use ErisPulse standard session types (see [Session Types Standard](session-types.md))
- Supported types: `private`, `group`, `user`, `channel`, `guild`, `thread`
- The adapter is responsible for mapping platform-native types to standard types

### 2.2 Message Event Fields
| Field | Type | Description |
|------|------|------|
| message | array | Message segment array |
| alt_message | string | Message segment fallback text |
| user_id | string | User ID |
| user_nickname | string | User nickname (optional) |

### 2.3 Notice Event Fields
| Field | Type | Description |
|------|------|------|
| user_id | string | User ID |
| user_nickname | string | User nickname (optional) |
| operator_id | string | Operator ID (optional) |

### 2.4 Request Event Fields
| Field | Type | Description |
|------|------|------|
| user_id | string | User ID |
| user_nickname | string | User nickname (optional) |
| comment | string | Request comment (optional) |

## 3. Event Format Examples

### 3.1 Message Event (message)
```json
{
  "id": "1234567890",
  "time": 1752241223,
  "type": "message",
  "detail_type": "group",
  "platform": "yunhu",
  "self": {
    "platform": "yunhu",
    "user_id": "bot_123"
  },
  "message": [
    {
      "type": "text",
      "data": {
        "text": "抽奖 超级大奖"
      }
    }
  ],
  "alt_message": "抽奖 超级大奖",
  "user_id": "user_456",
  "user_nickname": "YingXinche",
  "group_id": "group_789",
  "yunhu_raw": {...},
  "yunhu_raw_type": "message.receive.normal",
  "yunhu_command": {
    "name": "抽奖",
    "args": "超级大奖"
  }
}
```

### 3.2 Notice Event (notice)
```json
{
  "id": "1234567891",
  "time": 1752241224,
  "type": "notice",
  "detail_type": "group_member_increase",
  "platform": "yunhu",
  "self": {
    "platform": "yunhu",
    "user_id": "bot_123"
  },
  "user_id": "user_456",
  "user_nickname": "YingXinche",
  "group_id": "group_789",
  "operator_id": "",
  "yunhu_raw": {...},
  "yunhu_raw_type": "bot.followed"
}
```

### 3.3 Request Event (request)
```json
{
  "id": "1234567892",
  "time": 1752241225,
  "type": "request",
  "detail_type": "friend",
  "platform": "onebot11",
  "self": {
    "platform": "onebot11",
    "user_id": "bot_123"
  },
  "user_id": "user_456",
  "user_nickname": "YingXinche",
  "comment": "请加好友",
  "onebot11_raw": {...},
  "onebot11_raw_type": "request"
}
```

## 4. Message Segment Standards

### 4.1 Standard Message Segments

Standard message segment types **do not add** platform prefixes:

| Type | Description | Data Fields |
|------|------|----------|
| `text` | Plain text | `text: str` |
| `image` | Image | `file: str/bytes`, `url: str` |
| `audio` | Audio | `file: str/bytes`, `url: str` |
| `video` | Video | `file: str/bytes`, `url: str` |
| `file` | File | `file: str/bytes`, `url: str`, `filename: str` |
| `mention` | @User | `user_id: str`, `user_name: str` |
| `reply` | Reply | `message_id: str` |
| `face` | Emoji/Face | `id: str` |
| `location` | Location | `latitude: float`, `longitude: float` |

```json
{
  "type": "text",
  "data": {
    "text": "Hello World"
  }
}
```

### 4.2 Platform Extension Message Segments

Platform-specific message segments need to add platform prefixes:

```json
// Yunhu - Form
{"type": "yunhu_form", "data": {"form_id": "123456", "form_name": "报名表"}}

// Telegram - Sticker
{"type": "telegram_sticker", "data": {"file_id": "CAACAgIAAxkBAA...", "emoji": "😂"}}
```

**Extension Message Segment Requirements**:
1.  **No prefix inside data**: `{"type": "yunhu_form", "data": {"form_id": "..."}}` instead of `{"type": "yunhu_form", "data": {"yunhu_form_id": "..."}}`
2.  **Provide fallback**: Modules may not recognize extension message segments; the adapter should provide a text alternative in `alt_message`.
3.  **Complete documentation**: Each extension message segment must document its `type`, `data` structure, and usage scenarios in the adapter documentation.

## 5. Unknown Event Handling

For unrecognizable event types, a warning event should be generated:
```json
{
  "id": "1234567893",
  "time": 1752241223,
  "type": "unknown",
  "platform": "yunhu",
  "yunhu_raw": {...},
  "yunhu_raw_type": "unknown",
  "warning": "Unsupported event type: special_event",
  "alt_message": "This event type is not supported by this system."
}
```

---

## 6. Extension Naming Conventions

### 6.1 Field Naming

**Rule**: `{platform}_{field_name}`

```
Platform Prefix    Field Name            Full Field Name
────────    ───────          ──────────
yunhu       command           yunhu_command
telegram    sticker_file_id   telegram_sticker_file_id
onebot11    anonymous         onebot11_anonymous
email       subject           email_subject
```

**Requirements**:
- `platform` must be fully consistent with the platform name registered by the adapter (case-sensitive).
- `field_name` uses `snake_case` naming.
- Starting with double underscores `__` is prohibited (Python reserved).
- Prohibited from having the same name as standard fields (e.g., `type`, `time`, `message`, etc.).

### 6.2 Message Segment Type Naming

**Rule**: `{platform}_{segment_type}`

Standard message segment types (`text`, `image`, `audio`, `video`, `mention`, `reply`, etc.) **must not** add platform prefixes. Only platform-specific message segment types require prefixes.

### 6.3 Raw Data Field Naming

The following field names are **Reserved Fields** that all adapters must follow:

| Reserved Field | Type | Description |
|---------|------|------|
| `{platform}_raw` | `any` | Complete copy of the platform's raw event data |
| `{platform}_raw_type` | `string` | Platform raw event type identifier |

**Requirements**:
- `{platform}_raw` must be a deep copy of the raw data, not a reference.
- `{platform}_raw_type` must be a string; convert to string even if the platform uses a numeric type.
- These two fields **must exist** in all events (use `null` and empty string `""` if unobtainable).

### 6.4 Platform-Specific Field Examples

```json
{
  "yunhu_command": {
    "name": "抽奖",
    "args": "超级大奖"
  },
  "yunhu_form": {
    "form_id": "123456"
  },
  "telegram_sticker": {
    "file_id": "CAACAgIAAxkBAA..."
  }
}
```

### 6.5 Nested Extension Fields

Extension fields can be simple values or nested objects:

```json
{
  "telegram_chat": {
    "id": 123456,
    "type": "supergroup",
    "title": "My Group"
  },
  "telegram_forward_from": {
    "user_id": "789",
    "user_name": "ForwardUser"
  }
}
```

**Nested Field Requirements**:
- Top-level keys must carry the platform prefix.
- Nested inner fields **do not add** the platform prefix.
- Recommended nesting depth does not exceed 3 layers.

### 6.6 `self` Field Extension

The standard required fields for the `self` object (`platform`, `user_id`) are listed in §2.1. The following are optional fields extended by ErisPulse:

| Field | Type | Description |
|------|------|------|
| `self.user_name` | `string` | Bot nickname |
| `self.avatar` | `string` | Bot avatar URL |
| `self.account_id` | `string` | Account identifier in multi-account mode |

> **Bot Status Tracking**: The adapter informs the framework of the Bot's connection status by sending `type: "meta"` events. Supported `detail_type`: `connect` (online), `heartbeat` (heartbeat), `disconnect` (offline). The system automatically extracts Bot metadata from the `self` field for status tracking. Additionally, the `self` field in regular events is also automatically discovered as a Bot. See [Adapter System API - Bot Status Management](../../api-reference/adapter-system.md).

---

## 7. Session Type Extensions

ErisPulse extends the following session types based on the OneBot12 standard `private` and `group`:

| Type | OneBot12 Standard | ErisPulse Extension | Description |
|------|:-----------:|:------------:|------|
| `private` | ✅ | — | One-on-one private chat |
| `group` | ✅ | — | Group chat |
| `user` | — | ✅ | User type (Telegram, etc.) |
| `channel` | — | ✅ | Channel (broadcast) |
| `guild` | — | ✅ | Server/Community |
| `thread` | — | ✅ | Topic/Sub-channel |

**Adapter Custom Type Extensions**:

```python
from ErisPulse.Core.Event.session_type import register_custom_type

# Register when adapter starts
register_custom_type(
    receive_type="email",      # detail_type in receiving events
    send_type="email",         # Target type when sending
    id_field="email_id",       # Corresponding ID field name
    platform="email"           # Platform identifier
)
```

**Custom Type Requirements**:
- Must register during adapter `start()` and unregister during `shutdown()`.
- `receive_type` should not have the same name as standard types.
- `id_field` should follow the naming pattern `{target}_id`.

> For complete session type definitions and mapping relationships, see [Session Types Standard](session-types.md).

---

## 8. Module Developer Guide

### 8.1 Accessing Extension Fields

```python
from ErisPulse.Core.Event import message

@message()
async def handle_message(event):
    # Access standard fields
    text = event.get_text()
    user_id = event.get_user_id()

    # Access platform extension fields - Method 1: Direct get
    yunhu_command = event.get("yunhu_command")

    # Access platform extension fields - Method 2: Dot access (Event wrapper class)
    # event.yunhu_command

    # Access raw data
    raw_data = event.get("yunhu_raw")
    raw_type = event.get_raw_type()

    # Check platform
    platform = event.get_platform()
    if platform == "yunhu":
        pass
    elif platform == "telegram":
        pass
```

### 8.2 Handling Extension Message Segments

```python
@message()
async def handle_message(event):
    message_segments = event.get("message", [])

    for segment in message_segments:
        seg_type = segment.get("type")
        seg_data = segment.get("data", {})

        if seg_type == "text":
            text = seg_data["text"]
        elif seg_type.startswith("yunhu_"):
            if seg_type == "yunhu_form":
                form_id = seg_data["form_id"]
        elif seg_type.startswith("telegram_"):
            if seg_type == "telegram_sticker":
                file_id = seg_data["file_id"]
```

### 8.3 Best Practices

1.  **Prioritize standard fields**: Do not assume extension fields always exist.
2.  **Platform check**: Use `event.get_platform()` to determine the platform, rather than inferring from the existence of extension fields.
3.  **Graceful degradation**: When unable to handle extension message segments, use `alt_message` as a fallback.
4.  **Do not hardcode prefixes**: Use the `platform` variable for dynamic concatenation.

```python
# ✅ Recommended
platform = event.get_platform()
raw_data = event.get(f"{platform}_raw")

# ❌ Not recommended
raw_data = event.get("yunhu_raw")
```

---

## 9. Related Documents

- [Platform Feature Documentation](../platform-guide/README.md) - You can visit this document to understand the features of each platform as well as known extension events and message segments.
- [Session Types Standard](session-types.md) - Session type definitions and mapping relationships
- [Send Method Specification](send-method-spec.md) - Send class method naming, parameter specifications, and reverse conversion requirements
- [API Response Standard](api-response.md) - Adapter API response format standard



### API 响应标准

# ErisPulse Adapter Standardized Return Specification

## 1. Description
Why is this specification here?

To ensure consistency in return interfaces across platforms and OneBot12 compatibility, the ErisPulse adapter adopts the OneBot12-defined message sending return structure standard for API response formats.

However, the ErisPulse protocol has some specific definitions:
- 1. In basic fields, `message_id` is mandatory, but it does not exist in the OneBot12 standard.
- 2. The return content needs to add a `{platform_name}_raw` field to store raw response data.

## 2. Basic Return Structure
All action responses must include the following basic fields:

| Field Name | Data Type | Required | Description |
|-------|---------|------|------|
| status | string | Yes | Execution status, must be "ok" or "failed" |
| retcode | int64 | Yes | Return code, follows OneBot12 return code rules |
| data | any | Yes | Response data, contains request result when successful, null when failed |
| message_id | string | Yes | Message ID, used to identify the message, empty string if none |
| message | string | Yes | Error message, empty string when successful |
| {platform_name}_raw | any | No | Raw response data |

Optional Fields:
| Field Name | Data Type | Required | Description |
|-------|---------|------|------|
| echo | string | No | When the request contains an echo field, return it unchanged |

## 3. Complete Field Specification

### 3.1 Common Fields

#### Success Response Example
```json
{
    "status": "ok",
    "retcode": 0,
    "data": {
        "message_id": "1234",
        "time": 1632847927.599013
    },
    "message_id": "1234",
    "message": "",
    "echo": "1234",
    "telegram_raw": {...}
}
```

#### Failure Response Example
```json
{
    "status": "failed",
    "retcode": 10003,
    "data": null,
    "message_id": "",
    "message": "Missing required parameter: user_id",
    "echo": "1234",
    "telegram_raw": {...}
}
```

### 3.2 Return Code Specification

#### 0 Success (OK)
- 0: Success (OK)

#### 1xxxx Action Request Errors (Request Error)
| Error Code | Error Name | Description |
|-------|-------|------|
| 10001 | Bad Request | Invalid action request |
| 10002 | Unsupported Action | Unsupported action request |
| 10003 | Bad Param | Invalid action request parameters |
| 10004 | Unsupported Param | Unsupported action request parameters |
| 10005 | Unsupported Segment | Unsupported message segment type |
| 10006 | Bad Segment Data | Invalid message segment parameters |
| 10007 | Unsupported Segment Data | Unsupported message segment parameters |
| 10101 | Who Am I | Bot account not specified |
| 10102 | Unknown Self | Unknown bot account |

#### 2xxxx Action Handler Errors (Handler Error)
| Error Code | Error Name | Description |
|-------|-------|------|
| 20001 | Bad Handler | Action handler implementation error |
| 20002 | Internal Handler Error | Exception thrown by action handler runtime |

#### 3xxxx Action Execution Errors (Execution Error)
| Error Code Range | Error Type | Description |
|-----------|---------|------|
| 31xxx | Database Error | Database error |
| 32xxx | Filesystem Error | Filesystem error |
| 33xxx | Network Error | Network error |
| 34xxx | Platform Error | Bot platform error |
| 35xxx | Logic Error | Action logic error |
| 36xxx | I Am Tired | Implementation decided to go on strike |

#### Reserved Error Ranges
- 4xxxx, 5xxxx: Reserved segments, should not be used
- 6xxxx~9xxxx: Other error segments, available for implementation custom use

## 4. Implementation Requirements
1. All responses must include status, retcode, data, and message fields
2. When the request contains a non-empty echo field, the response must include an echo field with the same value
3. Return codes must strictly follow OneBot12 specification
4. Error messages (message) should be human-readable descriptions

## 5. Extended Specifications

ErisPulse makes the following extensions on top of the OneBot12 standard return structure:

### 5.1 `message_id` Mandatory Field

In the OneBot12 standard, `message_id` is inside the `data` object and is not mandatory. ErisPulse elevates it to a top-level **mandatory** field:

- Should be set to an empty string `""` when `message_id` cannot be obtained
- Ensure `message_id` always exists, modules do not need to perform null checks

### 5.2 `{platform}_raw` Raw Response Field

The return value should include a `{platform}_raw` field, containing a complete copy of the platform's raw response data:

```json
{
    "status": "ok",
    "retcode": 0,
    "data": {"message_id": "1234", "time": 1632847927},
    "message_id": "1234",
    "message": "",
    "telegram_raw": {
        "ok": true,
        "result": {"message_id": 1234, "date": 1632847927, ...}
    }
}
```

**Requirements**:
- `{platform}_raw` must be a deep copy of the raw response, not a reference
- `platform` must match the platform name used during adapter registration exactly (case-sensitive)
- Error messages within the raw response should also be preserved to facilitate debugging

### 5.3 Adapter Implementation Checklist

- [ ] Include `status`, `retcode`, `data`, `message_id`, `message` fields
- [ ] Return codes follow OneBot12 specification (see §3.2)
- [ ] `message_id` always exists (empty string if unable to obtain)
- [ ] `{platform}_raw` contains platform raw response data

## 6. Notes
- For 3xxxx error codes, the last three digits can be defined by the implementation
- Avoid using reserved error segments (4xxxx, 5xxxx)
- Error messages should be concise and clear for debugging



### 发送方法规范

# ErisPulse Sending Method Specifications

This document defines the naming, parameter specifications, and reverse conversion requirements for the sending methods of the `Send` class within the ErisPulse adapter.

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

| Method Name | Description | Required |
|-------|------|---------|
| `Raw_ob12` | Send OneBot12 format message segment | Yes |

**`Raw_ob12` is a required method to implement.** This is one of the adapter's core responsibilities: receiving OneBot12 standard message segments and converting them into platform native API calls. `Raw_ob12` is the unified entry point for reverse conversion (OneBot12 → Platform), ensuring modules can send messages without relying on platform-specific methods, using standard message segments directly.

**Behavior when `Raw_ob12` is not overridden:** The base class default implementation will log an **error level** log and return the standard error response format (`status: "failed"`, `retcode: 10002`), prompting adapter developers to implement this method.

### 1.4 Recommended Extension Naming Conventions

If the adapter needs to support sending raw data in non-OneBot12 formats (such as platform-specific JSON, XML, etc.), the following naming conventions are recommended:

| Recommended Method Name | Description |
|-----------|------|
| `Raw_json` | Send arbitrary JSON data |
| `Raw_xml` | Send arbitrary XML data |

**Note:** These methods are **not** default methods provided by the base class, nor are they mandatory to implement. They serve only as naming conventions; adapters may define them as needed. If an adapter does not support these formats, there is no need to define them.

**MessageBuilder:** ErisPulse provides a `MessageBuilder` tool class to conveniently construct OneBot12 message segment lists for use with `Raw_ob12`. See the [MessageBuilder](#11-messagebuilder) section for details.

## 2. Parameter Specifications Detail

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

### 2.2 @ User Parameter Specifications

**Method:** `At` (modifier method)

**Parameter:** `user_id` (`str`)

**Requirements:**
- `user_id` should be a string type user identifier
- `user_id` format may vary across different platforms (numbers, UUID, strings, etc.)
- Adapter is responsible for converting `user_id` to platform-specific format
- **Note:** The actual sending method call must be placed at the end.

**Example:**
```python
# @ a single user
Send.To("group", "g123").At("123456").Text("Hello")

# @ multiple users (chained calls)
send.To("group", "g123").At("123456").At("789012").Text("Hello everyone")
```

### 2.3 Reply Message Parameter Specifications

**Method:** `Reply` (modifier method)

**Parameter:** `message_id` (`str`)

**Requirements:**
- `message_id` should be a string type message identifier
- It should be the ID of a previously received message
- Some platforms may not support reply functionality; adapter should gracefully degrade

**Example:**
```python
send.To("group", "g123").Reply("msg_123456").Text("Received")
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

def Raw_ob12(self, message):  # ✅ Send OneBot12 format
    pass
```

**Extended Method Requirements:**
- Method names use PascalCase without a platform prefix
- Must return `asyncio.Task` object
- Must provide complete type hints and docstrings
- Parameter design should be as consistent as possible with standard methods

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

---

## 6. Reverse Conversion Specifications (OneBot12 → Platform)

The adapter not only needs to convert platform native events to OneBot12 format (forward conversion) but also **must** provide the capability to convert OneBot12 message segments back into platform native API calls (reverse conversion). The unified entry point for reverse conversion is the `Raw_ob12` method.

### 6.1 Conversion Model

```
Forward Conversion (Receive Direction)          Reverse Conversion (Send Direction)
─────────────────────────                      ─────────────────
Platform Native Events                         OneBot12 Message Segment List
    │                                              │
    ▼                                              ▼
Converter.convert()                           Send.Raw_ob12()
    │                                              │
    ▼                                              ▼
OneBot12 Standard Events                       Platform Native API Calls
(with {platform}_raw)                           (returns standard response format)
```

**Core Symmetry:** Forward conversion preserves the original data in `{platform}_raw`, while reverse conversion accepts the OneBot12 standard format and restores it to platform calls.

### 6.2 `Raw_ob12` Implementation Specifications

`Raw_ob12` receives a OneBot12 standard message segment list and must convert it into platform native API calls.

**Method Signature:**

```python
def Raw_ob12(self, message_segments: List[Dict]) -> asyncio.Task:
    """
    Send OneBot12 standard message segments

    :param message_segments: OneBot12 message segment list
        [
            {"type": "text", "data": {"text": "Hello"}},
            {"type": "image", "data": {"file": "https://..."}},
            {"type": "mention", "data": {"user_id": "123"}},
        ]
    :return: asyncio.Task, returns standard response format after awaiting
    """
```

**Implementation Requirements:**

1. **Must handle all standard message segment types:** At least support `text`, `image`, `audio`, `video`, `file`, `mention`, `reply`
2. **Must handle platform extension message segments:** For `{platform}_xxx` type message segments, convert to corresponding platform native calls
3. **Must return standard response format:** Follow [API Response Standard](api-response.md)
4. **Unsupported message segments should be skipped and logged as warnings**; exceptions should not be thrown to cause the entire message sending to fail

### 6.3 Message Segment Conversion Rules

#### 6.3.1 Standard Message Segment Conversion

The adapter must implement the following standard message segment conversions:

| OneBot12 Segment | Conversion Requirements |
|----------------|---------|
| `text` | Directly use `data.text` |
| `image` | Handle based on `data.file` type: URL used directly, bytes uploaded, local path read then uploaded |
| `audio` | Same logic as image |
| `video` | Same logic as image |
| `file` | Same logic as image, note `data.filename` |
| `mention` | Convert to platform's @user mechanism (e.g., Telegram's `entities`, Yunhu's `at_uid`) |
| `reply` | Convert to platform's reply reference mechanism |
| `face` | Convert to platform's emoji sending mechanism, skip if not supported |
| `location` | Convert to platform's location sending mechanism, skip if not supported |

#### 6.3.2 Platform Extension Message Segment Conversion

For message segments with platform prefixes, the adapter should identify and convert:

```python
def _convert_ob12_segments(self, segments: List[Dict]) -> Any:
    """Convert OneBot12 message segments to platform native format"""
    platform_prefix = f"{self._platform_name}_"
    
    for segment in segments:
        seg_type = segment["type"]
        seg_data = segment["data"]
        
        if seg_type.startswith(platform_prefix):
            # Platform extension segment -> Platform native call
            self._handle_platform_segment(seg_type, seg_data)
        elif seg_type in self._standard_segment_handlers:
            # Standard segment -> Platform equivalent operation
            self._standard_segment_handlers[seg_type](seg_data)
        else:
            # Unknown segment -> Log warning and skip
            logger.warning(f"Unsupported message segment type: {seg_type}")
```

#### 6.3.3 Composite Message Segment Processing

A single message may contain multiple message segments, and the adapter needs to correctly handle composite messages:

```python
# Module sends a message containing text + image + @user
await send.Raw_ob12([
    {"type": "mention", "data": {"user_id": "123"}},
    {"type": "text", "data": {"text": "Hello"}},
    {"type": "image", "data": {"file": "https://example.com/img.jpg"}}
])
```

**Processing Strategy:**
- **Prioritize Merging:** If the platform supports combining text, image, @user, etc., in a single message, merge and send
- **Fall back to Splitting:** If the platform does not support merging, split into multiple messages in order
- **Maintain Order:** The order of message segment sending should be consistent with the list order

### 6.4 Relationship between `Raw_ob12` and Standard Methods

Standard sending methods in the adapter (e.g., `Text`, `Image`) should delegate internally to `Raw_ob12`, rather than implementing conversion logic independently:

```python
class Send(SendDSL):
    def Raw_ob12(self, message_segments: List[Dict]) -> asyncio.Task:
        """Core implementation: OneBot12 message segments -> Platform API"""
        return asyncio.create_task(self._send_ob12(message_segments))
    
    def Text(self, text: str) -> asyncio.Task:
        """Standard method, delegate to Raw_ob12"""
        return self.Raw_ob12([
            {"type": "text", "data": {"text": text}}
        ])
    
    def Image(self, image: Union[str, bytes]) -> asyncio.Task:
        """Standard method, delegate to Raw_ob12"""
        return self.Raw_ob12([
            {"type": "image", "data": {"file": image}}
        ])
```

**Benefits:**
- Conversion logic is centralized in `Raw_ob12`, reducing duplicate code
- Standard methods and `Raw_ob12` behave consistently
- Modules get the same result whether using `Text()` or `Raw_ob12()`

### 6.5 Implementation Example

```python
class YunhuSend(SendDSL):
    """Yunhu platform Send implementation"""
    
    def Raw_ob12(self, message_segments: list) -> asyncio.Task:
        """OneBot12 message segments -> Yunhu API call"""
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
                logger.warning(f"Yunhu unsupported message segment: {seg_type}")
        
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

Module developers can query the sending methods supported by the adapter via the API:

```python
from ErisPulse import adapter

# List all sending methods
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

## 8. Registered Sending Method Extensions

| Platform | Method Name | Description |
|------|--------|------|
| onebot12 | `Mention` | @ user (OneBot12 style) |
| onebot12 | `Sticker` | Send sticker |
| onebot12 | `Location` | Send location |
| onebot12 | `Recall` | Recall message |
| onebot12 | `Edit` | Edit message |
| onebot12 | `Batch` | Batch send |

> **Note:** Sending methods do not add platform prefixes; methods with the same name on different platforms can have different implementations.

---

## 9. Adapter Implementation Checklist

### Sending Methods
- [ ] Standard methods (`Text`, `Image`, etc.) implemented
- [ ] Return values are all `asyncio.Task`
- [ ] Modifier methods (`At`, `Reply`, `AtAll`) return `self`
- [ ] Platform extension methods use PascalCase, no platform prefix
- [ ] All methods have complete type hints and docstrings

### Reverse Conversion
- [ ] `Raw_ob12` **implemented** (Mandatory, cannot skip)
- [ ] `Raw_ob12` can handle all standard message segments (`text`, `image`, `audio`, `video`, `file`, `mention`, `reply`)
- [ ] `Raw_ob12` can handle platform extension message segments (`{platform}_xxx` types)
- [ ] Standard sending methods (`Text`, `Image`, etc.) delegate internally to `Raw_ob12`, rather than implementing conversion logic independently
- [ ] Unsupported message segments are skipped and logged as warnings, no exceptions thrown
- [ ] Composite message segments handled correctly (merged or split in order)

---

## 11. MessageBuilder

`MessageBuilder` is a message segment building tool provided by ErisPulse, used with `Raw_ob12` to simplify the construction of OneBot12 message segments.

### 11.1 Import

```python
from ErisPulse.Core import MessageBuilder
# or
from ErisPulse.Core.Event import MessageBuilder
```

### 11.2 Chaining Calls to Build

```python
# Build a message containing text, image, and @user
segments = (
    MessageBuilder()
    .mention("123456")
    .text("Hello, take a look at this picture")
    .image("https://example.com/img.jpg")
    .reply("msg_789")
    .build()
)

# Send
await adapter.Send.To("group", "456").Raw_ob12(segments)
```

### 11.3 Quick Build for Single Segment

```python
# Quickly build a single message segment (returns list[dict], can be passed directly to Raw_ob12)
await adapter.Send.To("user", "123").Raw_ob12(MessageBuilder.text("Hello"))
await adapter.Send.To("group", "456").Raw_ob12(MessageBuilder.image("https://..."))
await adapter.Send.To("group", "456").Raw_ob12(MessageBuilder.mention("123"))
await adapter.Send.To("group", "456").Raw_ob12(MessageBuilder.reply("msg_id"))
await adapter.Send.To("group", "456").Raw_ob12(MessageBuilder.at_all())
```

### 11.4 Use with Event.reply_ob12

```python
from ErisPulse.Core import MessageBuilder

@message()
async def handle(event: Event):
    await event.reply_ob12(
        MessageBuilder()
        .mention(event.get_user_id())
        .text("Received your message")
        .build()
    )
```

### 11.5 Supported Message Segment Methods

| Method | Description | data fields |
|------|----------|----------|
| `text(text)` | Text | `text` |
| `image(file)` | Image | `file` |
| `audio(file)` | Audio | `file` |
| `video(file)` | Video | `file` |
| `file(file, filename=None)` | File | `file`, `filename` (optional) |
| `mention(user_id, user_name=None)` | @ user | `user_id`, `user_name` (optional) |
| `at(user_id, user_name=None)` | @ user (alias of `mention`) | Same as `mention` |
| `reply(message_id)` | Reply | `message_id` |
| `at_all()` | @ all members | `{}` |
| `custom(type, data)` | Custom/Platform extension | Custom |

### 11.6 Utility Methods

```python
builder = MessageBuilder().text("Base content")

# Copy (deep copy)
msg1 = builder.copy().image("img1").build()
msg2 = builder.copy().image("img2").build()

# Clear
builder.clear().text("New content").build()

# Check if empty
if builder:
    print(f"Contains {len(builder)} message segments")
```

---

## 12. Related Documents

- [Event Conversion Standard](event-conversion.md) - Complete event conversion specifications, extension naming, and message segment standards
- [API Response Standard](api-response.md) - Adapter API response format standards
- [Session Type Standard](session-types.md) - Session type definitions and mapping relationships



======
平台特性指南
======


### 平台特性总览

# ErisPulse Platform Features Documentation

> Base Protocol: [OneBot12](https://12.onebot.dev/) 
> 
> This document is a **Platform-Specific Features Guide** containing:
> - Chain invocation examples of the Send method supported by each adapter
> - Explanations of platform-specific events/message formats
> 
> For general usage methods, please refer to:
> - [Basic Concepts](../getting-started/basic-concepts.md)
> - [Event Conversion Standards](../standards/event-conversion.md)  
> - [API Response Specifications](../standards/api-response.md)

---

## Platform Specific Features

This section is maintained by developers of each adapter to explain the differences and extended features of that adapter compared to the OneBot12 standard. Please refer to the detailed documentation for the following platforms:

- [Maintenance Notes](maintain-notes.md)

- [Yunhu Platform Features](yunhu.md)
- [Yunhu User Platform Features](yunhu-user.md)
- [Telegram Platform Features](telegram.md)
- [OneBot11 Platform Features](onebot11.md)
- [OneBot12 Platform Features](onebot12.md)
- [Email Platform Features](email.md)
- [Kook (Kaihei La) Platform Features](kook.md)
- [Matrix Platform Features](matrix.md)
- [QQ Official Bot Platform Features](qqbot.md)

> Additionally, there is a `sandbox` adapter, but this adapter does not require platform-specific feature documentation

---

## Common Interfaces

### Send Chained Invocation
All adapters support the following standard calling methods:

> **Note:** The `{AdapterName}` in the document needs to be replaced with the actual adapter name (e.g., `yunhu`, `telegram`, `onebot11`, `email`, etc.).

1. Specify type and ID: `To(type,id).Func()`
   ```python
   # Get adapter instance
   my_adapter = adapter.get("{AdapterName}")
   
   # Send message
   await my_adapter.Send.To("user", "U1001").Text("Hello")
   
   # Example:
   yunhu = adapter.get("yunhu")
   await yunhu.Send.To("user", "U1001").Text("Hello")
   ```
2. Specify ID only: `To(id).Func()`
   ```python
   my_adapter = adapter.get("{AdapterName}")
   await my_adapter.Send.To("U1001").Text("Hello")
   
   # Example:
   telegram = adapter.get("telegram")
   await telegram.Send.To("U1001").Text("Hello")
   ```
3. Specify sending account: `Using(account_id)`
   ```python
   my_adapter = adapter.get("{AdapterName}")
   await my_adapter.Send.Using("bot1").To("U1001").Text("Hello")
   
   # Example:
   onebot11 = adapter.get("onebot11")
   await onebot11.Send.Using("bot1").To("U1001").Text("Hello")
   ```
4. Direct call: `Func()`
   ```python
   my_adapter = adapter.get("{AdapterName}")
   await my_adapter.Send.Text("Broadcast message")
   
   # Example:
   email = adapter.get("email")
   await email.Send.Text("Broadcast message")
   ```

#### Asynchronous Sending and Result Processing

Methods of the Send DSL return `asyncio.Task` objects, which means you can choose whether to wait for the result immediately:

```python
# Get adapter instance
my_adapter = adapter.get("{AdapterName}")

# Do not wait for result, message sent in background
task = my_adapter.Send.To("user", "123").Text("Hello")

# If you need to get the send result, you can wait later
result = await task
```

### Event Listening
There are three ways to listen for events:

1. Platform native event listening:
   ```python
   from ErisPulse.Core import adapter, logger
   
   @adapter.on("event_type", raw=True, platform="{AdapterName}")
   async def handler(data):
       logger.info(f"Received {AdapterName} native event: {data}")
   ```

2. OneBot12 standard event listening:
   ```python
   from ErisPulse.Core import adapter, logger

   # Listen for OneBot12 standard events
   @adapter.on("event_type")
   async def handler(data):
       logger.info(f"Received standard event: {data}")

   # Listen for specific platform's standard events
   @adapter.on("event_type", platform="{AdapterName}")
   async def handler(data):
       logger.info(f"Received {AdapterName} standard event: {data}")
   ```

3. Event module listening:
    The events of the `Event` module are based on the `adapter.on()` function, so the event format provided by `Event` is a OneBot12 standard event

    ```python
    from ErisPulse.Core.Event import message, notice, request, command

    message.on_message()(message_handler)
    notice.on_notice()(notice_handler)
    request.on_request()(request_handler)
    command("hello", help="Send greeting message", usage="hello")(command_handler)

    async def message_handler(event):
        logger.info(f"Received message: {event}")
    async def notice_handler(event):
        logger.info(f"Received notice: {event}")
    async def request_handler(event):
        logger.info(f"Received request: {event}")
    async def command_handler(event):
        logger.info(f"Received command: {event}")
    ```

Among these, using the `Event` module is the most recommended approach for event handling, as it provides a variety of event types, as well as rich event processing methods.

---

## Standard Formats
For reference purposes, simple event formats are provided here. For detailed information, please refer to the links above.

> **Note:** The following format is based on the basic OneBot12 standard format. Each adapter may have extended fields on top of this. For details, please refer to the specific feature documentation of each adapter.

### Standard Event Format
Event conversion format that all adapters must implement:
```json
{
  "id": "event_123",
  "time": 1752241220,
  "type": "message",
  "detail_type": "group",
  "platform": "example_platform",
  "self": {"platform": "example_platform", "user_id": "bot_123"},
  "message_id": "msg_abc",
  "message": [
    {"type": "text", "data": {"text": "Hello"}}
  ],
  "alt_message": "Hello",
  "user_id": "user_456",
  "user_nickname": "ExampleUser",
  "group_id": "group_789"
}
```

### Standard Response Format
#### Message Sending Success
```json
{
  "status": "ok",
  "retcode": 0,
  "data": {
    "message_id": "1234",
    "time": 1632847927.599013
  },
  "message_id": "1234",
  "message": "",
  "echo": "1234",
  "{platform}_raw": {...}
}
```

#### Message Sending Failed
```json
{
  "status": "failed",
  "retcode": 10003,
  "data": null,
  "message_id": "",
  "message": "Missing required parameters",
  "echo": "1234",
  "{platform}_raw": {...}
}
```

---

## References
ErisPulse Project:
- [Main Repository](https://github.com/ErisPulse/ErisPulse/)
- [Yunhu Adapter Library](https://github.com/ErisPulse/ErisPulse-YunhuAdapter)
- [Telegram Adapter Library](https://github.com/ErisPulse/ErisPulse-TelegramAdapter)
- [OneBot Adapter Library](https://github.com/ErisPulse/ErisPulse-OneBotAdapter)

Related Official Documentation:
- [OneBot V11 Protocol Documentation](https://github.com/botuniverse/onebot-11)
- [Telegram Bot API Official Documentation](https://core.telegram.org/bots/api)
- [Yunhu Official Documentation](https://www.yhchat.com/document/1-3)

## Contributing

We welcome more developers to participate in writing and maintaining adapter documentation! Please submit contributions by following these steps:
1. Fork [ErisPulse](https://github.com/ErisPulse/ErisPulse) repository.
2. Create a Markdown file in the `docs/platform-features/` directory with the naming format `<platform-name>.md`.
3. Add a link to your contributed adapter and related official documentation in this `README.md` file.
4. Submit Pull Request.

Thank you for your support!



### OneBot11 适配

# OneBot11 Platform Features Documentation

OneBot11Adapter is an adapter built based on the OneBot V11 protocol.

---

## Documentation Information

- Corresponding Module Version: 3.6.0
- Maintainer: ErisPulse

## Basic Information

- Platform Introduction: OneBot is a chatbot application interface standard
- Adapter Name: OneBotAdapter
- Supported Protocol/API Version: OneBot V11
- Multi-account Support: Default multi-account architecture, supports configuring and running multiple OneBot accounts simultaneously
- Legacy Configuration Compatibility: Compatible with old version configuration formats, provides migration reminders (non-automatic migration)

## Supported Message Sending Types

All sending methods are implemented via chaining syntax, for example:
```python
from ErisPulse.Core import adapter
onebot = adapter.get("onebot11")

# Send using default account
await onebot.Send.To("group", group_id).Text("Hello World!")

# Send using specific account
await onebot.Send.Using("main").To("group", group_id).Text("Message from main account")

# Chain modifiers: @ user + reply
await onebot.Send.To("group", group_id).At(123456).Reply(msg_id).Text("Reply message")

# @ all members
await onebot.Send.To("group", group_id).AtAll().Text("Announcement message")
```

### Basic Sending Methods

- `.Text(text: str)`: Send plain text message.
- `.Image(file: Union[str, bytes], filename: str = "image.png")`: Send image (supports URL, Base64, or bytes).
- `.Voice(file: Union[str, bytes], filename: str = "voice.amr")`: Send voice message.
- `.Video(file: Union[str, bytes], filename: str = "video.mp4")`: Send video message.
- `.Face(id: Union[str, int])`: Send QQ emoticon.
- `.File(file: Union[str, bytes], filename: str = "file.dat")`: Send file (auto-detect type).
- `.Raw_ob12(message: List[Dict], **kwargs)`: Send OneBot12 format message (auto-converted to OB11).
- `.Recall(message_id: Union[str, int])`: Recall message.

### Chained Modifier Methods (Combinable)

Chained modifier methods return `self`, support chaining, and must be called before the final sending method:

- `.At(user_id: Union[str, int], name: str = None)`: @ specific user (can be called multiple times).
- `.AtAll()`: @ all members.
- `.Reply(message_id: Union[str, int])`: Reply to specific message.

### Chained Call Examples

```python
# Basic send
await onebot.Send.To("group", 123456).Text("Hello")

# @ single user
await onebot.Send.To("group", 123456).At(789012).Text("Hello")

# @ multiple users
await onebot.Send.To("group", 123456).At(111).At(222).At(333).Text("Hello everyone")

# Send OneBot12 format message
ob12_msg = [{"type": "text", "data": {"text": "Hello"}}]
await onebot.Send.To("group", 123456).Raw_ob12(ob12_msg)
```

### Unsupported Type Handling

If an undefined sending method is called, the adapter returns a text prompt:
```python
# Call non-existent method
await onebot.Send.To("group", 123456).SomeUnsupportedMethod(arg1, arg2)
# Actual send: "[Unsupported send type] Method Name: SomeUnsupportedMethod, Arguments: [...]"
```

## Specific Event Types

OneBot11 events are converted to the OneBot12 protocol, where standard fields fully comply with the OneBot12 protocol, but there are the following differences:

### Core Differences

1.  **Specific Event Types:**
    -   CQ Code Extension Event: `onebot11_cq_{type}`
    -   Honor Change Event: `onebot11_honor`
    -   Poke Event: `onebot11_poke`
    -   Group Red Packet Lucky King Event: `onebot11_lucky_king`

2.  **Extension Fields:**
    -   All specific fields are identified with the `onebot11_` prefix
    -   Original CQ code message retained in the `onebot11_raw_message` field
    -   Original event data retained in the `onebot11_raw` field

### Special Field Examples

```python
// Honor change event
{
  "type": "notice",
  "detail_type": "onebot11_honor",
  "group_id": "123456",
  "user_id": "789012",
  "onebot11_honor_type": "talkative",
  "onebot11_operation": "set"
}

// Poke event
{
  "type": "notice",
  "detail_type": "onebot11_poke",
  "group_id": "123456",
  "user_id": "789012",
  "target_id": "345678",
  "onebot11_poke_type": "normal"
}

// Group red packet lucky king event
{
  "type": "notice",
  "detail_type": "onebot11_lucky_king",
  "group_id": "123456",
  "user_id": "789012",
  "target_id": "345678"
}

// CQ code message segment
{
  "type": "message",
  "message": [
    {
      "type": "onebot11_face",
      "data": {"id": "123"}
    },
    {
      "type": "onebot11_shake",
      "data": {} 
    }
  ]
}
```

### Extension Field Descriptions

-   All specific fields are identified with the `onebot11_` prefix
-   Original CQ code message retained in the `onebot11_raw_message` field
-   Original event data retained in the `onebot11_raw` field
-   CQ codes within message content are converted to corresponding message segments
-   Reply messages will add `reply` type message segments
-   @ messages will add `mention` type message segments

## Configuration Options

Each account in the OneBot adapter is configured with the following options independently:

### Account Configuration
- `mode`: Running mode of this account ("server" or "client")
- `server_path`: WebSocket path in Server mode
- `server_token`: Authentication Token in Server mode (optional)
- `client_url`: WebSocket address to connect to in Client mode
- `client_token`: Authentication Token in Client mode (optional)
- `enabled`: Whether this account is enabled

### Built-in Defaults
- Reconnect Interval: 30 seconds
- API Call Timeout: 30 seconds
- Maximum Retry Count: 3 times

### Configuration Example
```toml
[OneBotv11_Adapter.accounts.main]
mode = "server"
server_path = "/onebot-main"
server_token = "main_token"
enabled = true

[OneBotv11_Adapter.accounts.backup]
mode = "client"
client_url = "ws://127.0.0.1:3002"
client_token = "backup_token"
enabled = true

[OneBotv11_Adapter.accounts.test]
mode = "client"
client_url = "ws://127.0.0.1:3003"
enabled = false
```

### Default Configuration

If no account is configured, the adapter will automatically create:
```toml
[OneBotv11_Adapter.accounts.default]
mode = "server"
server_path = "/"
enabled = true
```

## Sending Method Return Values

All sending methods return a Task object, which can be directly awaited to get the send result. The returned result follows the ErisPulse adapter standardized return specification:

```python
{
    "status": "ok",           // Execution status
    "retcode": 0,             // Return code
    "data": {...},            // Response data
    "self": {...},            // Self information
    "message_id": "123456",   // Message ID
    "message": "",            // Error message
    "onebot_raw": {...}       // Raw response data
}
```

### Multi-account Sending Syntax

```python
# Account selection method
await onebot.Send.Using("main").To("group", 123456).Text("Main account message")
await onebot.Send.Using("backup").To("group", 123456).Image("http://example.com/image.jpg")

# API call method
await onebot.call_api("send_msg", account_id="main", group_id=123456, message="Hello")
```

## Async Processing Mechanism

The OneBot adapter adopts an asynchronous non-blocking design, ensuring:
1.  Message sending does not block the event processing loop
2.  Multiple concurrent send operations can proceed simultaneously
3.  API responses are handled in a timely manner
4.  WebSocket connections remain active
5.  Multi-account concurrent processing, with each account running independently

## Error Handling

The adapter provides comprehensive error handling mechanisms:
1.  Automatic reconnection for network connection exceptions (supports independent reconnection for each account, interval of 30 seconds)
2.  API call timeout handling (fixed 30-second timeout)
3.  Message send failure retry (up to 3 retries)

## Event Processing Enhancement

In multi-account mode, account information is automatically added to all events:
```python
{
    "type": "message",
    "detail_type": "private",
    "self": {"user_id": "main"},  // New: Account ID that sent the event (standard field)
    "platform": "onebot11",
    // ... other event fields
}
```

## Management Interface

```python
# Get all account information
accounts = onebot.accounts

# Check account connection status
connection_status = {
    account_id: connection is not None and not connection.closed
    for account_id, connection in onebot.connections.items()
}

# Dynamically enable/disable accounts (requires restarting adapter)
onebot.accounts["test"].enabled = False



### OneBot12 适配

# OneBot12 Platform Features Documentation

OneBot12Adapter is an adapter built based on the OneBot V12 protocol, serving as the baseline protocol adapter for the ErisPulse framework.

---

## Document Information

- Corresponding Module Version: 1.0.0
- Maintainer: ErisPulse
- Protocol Version: OneBot V12

## Basic Information

- Platform Introduction: OneBot V12 is a general chatbot application interface standard and serves as the baseline protocol for the ErisPulse framework.
- Adapter Name: OneBot12Adapter
- Supported Protocol/API Version: OneBot V12
- Multi-Account Support: Fully multi-account architecture, supports configuring and running multiple OneBot12 accounts simultaneously.

## Supported Message Sending Types

All sending methods are implemented via chain syntax, for example:

```python
from ErisPulse.Core import adapter
onebot12 = adapter.get("onebot12")

# Send using the default account
await onebot12.Send.To("group", group_id).Text("Hello World!")

# Send using a specific account
await onebot12.Send.To("group", group_id).Account("main").Text("Message from main account")
```

### Basic Message Types

- `.Text(text: str)`: Send a plain text message
- `.Image(file: Union[str, bytes], filename: str = "image.png")`: Send an image message (supports URL, Base64, or bytes)
- `.Audio(file: Union[str, bytes], filename: str = "audio.ogg")`: Send an audio message
- `.Video(file: Union[str, bytes], filename: str = "video.mp4")`: Send a video message

### Interactive Message Types

- `.Mention(user_id: Union[str, int], user_name: str = None)`: Send an @ mention message
- `.Reply(message_id: Union[str, int], content: str = None)`: Send a reply message
- `.Sticker(file_id: str)`: Send a sticker/E-mote
- `.Location(latitude: float, longitude: float, title: str = "", content: str = "")`: Send a location

### Management Functions

- `.Recall(message_id: Union[str, int])`: Recall a message
- `.Edit(message_id: Union[str, int], content: Union[str, List[Dict]])`: Edit a message
- `.Raw(message_segments: List[Dict])`: Send native OneBot12 message segments
- `.Batch(target_ids: List[str], message: Union[str, List[Dict]], target_type: str = "user")`: Send messages in batch

## OneBot12 Standard Events

The OneBot12 adapter fully adheres to the OneBot12 standard. The event format requires no conversion and is submitted directly to the framework.

### Message Events (Message Events)

```python
# Private message
{
    "id": "event-id",
    "type": "message",
    "detail_type": "private",
    "self": {"user_id": "bot-id"},
    "user_id": "user-id",
    "message": [{"type": "text", "data": {"text": "Hello"}}],
    "alt_message": "Hello",
    "time": 1234567890
}

# Group message
{
    "id": "event-id",
    "type": "message",
    "detail_type": "group",
    "self": {"user_id": "bot-id"},
    "user_id": "user-id",
    "group_id": "group-id",
    "message": [{"type": "text", "data": {"text": "Hello group"}}],
    "alt_message": "Hello group",
    "time": 1234567890
}
```

### Notice Events (Notice Events)

```python
# Group member increase
{
    "id": "event-id",
    "type": "notice",
    "detail_type": "group_member_increase",
    "self": {"user_id": "bot-id"},
    "group_id": "group-id",
    "user_id": "user-id",
    "operator_id": "operator-id",
    "sub_type": "approve",
    "time": 1234567890
}

# Group member decrease
{
    "id": "event-id",
    "type": "notice", 
    "detail_type": "group_member_decrease",
    "self": {"user_id": "bot-id"},
    "group_id": "group-id",
    "user_id": "user-id",
    "operator_id": "operator-id",
    "sub_type": "leave",
    "time": 1234567890
}
```

### Request Events (Request Events)

```python
# Friend request
{
    "id": "event-id",
    "type": "request",
    "detail_type": "friend",
    "self": {"user_id": "bot-id"},
    "user_id": "user-id",
    "comment": "Application message",
    "flag": "request-flag",
    "time": 1234567890
}

# Group invite request
{
    "id": "event-id",
    "type": "request",
    "detail_type": "group",
    "self": {"user_id": "bot-id"},
    "group_id": "group-id",
    "user_id": "user-id",
    "comment": "Application message",
    "flag": "request-flag",
    "sub_type": "invite",
    "time": 1234567890
}
```

### Meta Events (Meta Events)

```python
# Lifecycle event
{
    "id": "event-id",
    "type": "meta_event",
    "detail_type": "lifecycle",
    "self": {"user_id": "bot-id"},
    "sub_type": "enable",
    "time": 1234567890
}

# Heartbeat event
{
    "id": "event-id",
    "type": "meta_event",
    "detail_type": "heartbeat",
    "self": {"user_id": "bot-id"},
    "interval": 5000,
    "status": {"online": true},
    "time": 1234567890
}
```

## Configuration Options

### Account Configuration

Each account is configured independently with the following options:

- `mode`: The operating mode of the account ("server" or "client")
- `server_path`: WebSocket path in Server mode
- `server_token`: Authentication Token in Server mode (optional)
- `client_url`: WebSocket address to connect to in Client mode
- `client_token`: Authentication Token in Client mode (optional)
- `enabled`: Whether to enable this account
- `platform`: Platform identifier, defaults to "onebot12"
- `implementation`: Implementation identifier, e.g., "go-cqhttp" (optional)

### Configuration Example

```toml
[OneBotv12_Adapter.accounts.main]
mode = "server"
server_path = "/onebot12-main"
server_token = "main_token"
enabled = true
platform = "onebot12"
implementation = "go-cqhttp"

[OneBotv12_Adapter.accounts.backup]
mode = "client"
client_url = "ws://127.0.0.1:3002"
client_token = "backup_token"
enabled = true
platform = "onebot12"
implementation = "shinonome"

[OneBotv12_Adapter.accounts.test]
mode = "client"
client_url = "ws://127.0.0.1:3003"
enabled = false
```

### Default Configuration

If no accounts are configured, the adapter will automatically create:

```toml
[OneBotv12_Adapter.accounts.default]
mode = "server"
server_path = "/onebot12"
enabled = true
platform = "onebot12"
```

## Return Values of Sending Methods

All sending methods return a Task object, which can be directly awaited to obtain the sending result. The returned result follows the OneBot12 standard:

```python
{
    "status": "ok",           // Execution status
    "retcode": 0,             // Return code
    "data": {...},            // Response data
    "self": {"user_id": "account-id"},  // Account information
    "message_id": "123456",   // Message ID
    "message": ""             // Error message
}
```

### Multi-Account Sending Syntax

```python
# Account selection method
await onebot12.Send.Using("main").To("group", 123456).Text("Message from main account")
await onebot12.Send.Using("backup").To("group", 123456).Image("http://example.com/image.jpg")

# API call method
await onebot12.call_api("send_message", account_id="main", 
    detail_type="group", group_id=123456, 
    content=[{"type": "text", "data": {"text": "Hello"}}])
```

## Asynchronous Processing Mechanism

The OneBot12 adapter adopts an asynchronous non-blocking design:

1.  Message sending does not block the event handling loop
2.  Multiple concurrent sending operations can proceed simultaneously
3.  API responses can be processed in a timely manner
4.  WebSocket connections remain active
5.  Multi-account concurrency processing, with each account running independently

## Error Handling

The adapter provides comprehensive error handling mechanisms:

1.  Automatic reconnection for network connection exceptions (supports independent reconnection for each account, interval of 30 seconds)
2.  API call timeout handling (fixed 30-second timeout)
3.  Automatic retry for failed message sending (maximum 3 retries)

## Event Processing Enhancement

In multi-account mode, account information is automatically added to all events:

```python
{
    "type": "message",
    "detail_type": "private",
    "platform": "onebot12",
    // ... other event fields
}
```

## Management Interface

```python
# Get information for all accounts
accounts = onebot12.accounts

# Check account connection status
connection_status = {
    account_id: connection is not None and not connection.closed
    for account_id, connection in onebot12.connections.items()
}

# Dynamically enable/disable an account (requires adapter restart)
onebot12.accounts["test"].enabled = False
```

## OneBot12 Standard Features

### Message Segment Standard

OneBot12 uses a standardized message segment format:

```python
# Text message segment
{"type": "text", "data": {"text": "Hello"}}

# Image message segment
{"type": "image", "data": {"file_id": "image-id"}}

# Mention message segment
{"type": "mention", "data": {"user_id": "user-id", "user_name": "Username"}}

# Reply message segment
{"type": "reply", "data": {"message_id": "msg-id"}}
```

### API Standard

Follows the OneBot12 standard API specification:

- `send_message`: Send message
- `delete_message`: Recall message
- `edit_message`: Edit message
- `get_message`: Get message
- `get_self_info`: Get self information
- `get_user_info`: Get user information
- `get_group_info`: Get group information

## Best Practices

1.  **Configuration Management**: It is recommended to use multi-account configuration to manage bots of different purposes separately.
2.  **Error Handling**: Always check the return status of API calls.
3.  **Message Sending**: Use appropriate message types and avoid sending unsupported messages.
4.  **Connection Monitoring**: Regularly check connection status to ensure service availability.
5.  **Performance Optimization**: Use the Batch method for sending to reduce network overhead when sending in bulk.



### Telegram 适配

# Telegram Platform Features Documentation

TelegramAdapter is an adapter built based on the Telegram Bot API, supporting multiple message types and event handling.

---

## Document Information

- Corresponding Module Version: 3.5.0
- Maintainer: ErisPulse

## Basic Information

- Platform Introduction: Telegram is a cross-platform instant messaging software
- Adapter Name: TelegramAdapter
- Supported Protocols/API Versions: Telegram Bot API

## Supported Message Sending Types

All sending methods are implemented via chained syntax, for example:
```python
from ErisPulse.Core import adapter
telegram = adapter.get("telegram")

await telegram.Send.To("user", user_id).Text("Hello World!")
```

### Basic Sending Methods

- `.Text(text: str)`: Sends a plain text message.
- `.Face(emoji: str)`: Sends an emoji message.
- `.Markdown(text: str, content_type: str = "MarkdownV2")`: Sends a Markdown format message.
- `.HTML(text: str)`: Sends an HTML format message.

### Media Sending Methods

All media methods support two input methods:
- **URL Method**: Pass a string URL directly
- **File Upload**: Pass `bytes` type data

- `.Image(file: bytes | str, caption: str = "", content_type: str = None)`: Sends an image message
- `.Video(file: bytes | str, caption: str = "", content_type: str = None)`: Sends a video message
- `.Voice(file: bytes | str, caption: str = "")`: Sends a voice message
- `.Audio(file: bytes | str, caption: str = "", content_type: str = None)`: Sends an audio message
- `.File(file: bytes | str, caption: str = "")`: Sends a file message
- `.Document(file: bytes | str, caption: str = "", content_type: str = None)`: Sends a document message (Alias of File)

### Message Management Methods

- `.Edit(message_id: int, text: str, content_type: str = None)`: Edits an existing message.
- `.Recall(message_id: int)`: Deletes a specified message.

### Raw Message Sending

- `.Raw_ob12(message: List[Dict])`: Sends a OneBot12 standard format message
  - Supports complex combined messages (text + @user + reply + media)
  - Automatically treats text as the media message's caption
- `.Raw_json(json_str: str)`: Sends a raw JSON format message

### Chained Modifying Methods

- `.At(user_id: str)`: Mentions a specific user (can be called multiple times)
- `.AtAll()`: Mentions all members
- `.Reply(message_id: str)`: Replies to a specified message

### Method Name Mapping

Sending methods support case-insensitive calls and automatically convert to standard method names via a mapping table:
```python
# The following are equivalent
telegram.Send.To("group", 123).Text("hello")
telegram.Send.To("group", 123).text("hello")
telegram.Send.To("group", 123).TEXT("hello")
```

### Sending Examples

```python
# Basic text sending
await telegram.Send.To("group", group_id).Text("Hello World!")

# Media sending (URL Method)
await telegram.Send.To("group", group_id).Image("https://example.com/image.jpg", caption="This is an image")

# Media sending (File Upload)
with open("image.jpg", "rb") as f:
    await telegram.Send.To("group", group_id).Image(f.read())

# @User
await telegram.Send.To("group", group_id).At("6117725680").Text("Hello!")

# Reply to message
await telegram.Send.To("group", group_id).Reply("12345").Text("Reply content")

# Combined usage
await telegram.Send.To("group", group_id).Reply("12345").At("6117725680").Image("https://example.com/image.jpg", caption="Look at this picture")

# OneBot12 combined message
ob12_message = [
    {"type": "text", "data": {"text": "Complex combined message:"}},
    {"type": "mention", "data": {"user_id": "6117725680", "name": "Username"}},
    {"type": "reply", "data": {"message_id": "12345"}},
    {"type": "image", "data": {"file": "https://http.cat/200"}}
]
await telegram.Send.To("group", group_id).Raw_ob12(ob12_message)
```

### Unsupported Method Notifications

When calling unsupported sending methods, a text notification is automatically sent:
```python
# Unsupported sending type
await telegram.Send.To("group", group_id).UnknownMethod("data")
# Will send: [Unsupported sending type] Method name: UnknownMethod, Parameters: [...]
```

## Specific Event Types

Telegram events are converted to the OneBot12 protocol. While standard fields fully comply with the OneBot12 protocol, the following differences exist:

### Core Differences

1. Specific Event Types:
   - Inline Query: `telegram_inline_query`
   - Callback Query: `telegram_callback_query`
   - Poll Event: `telegram_poll`
   - Poll Answer: `telegram_poll_answer`

2. Extended Fields:
   - All specific fields are identified with the `telegram_` prefix
   - Original data is preserved in the `telegram_raw` field
   - Channel messages use `detail_type="channel"`

### Event Listening Methods

The Telegram adapter supports two methods for listening to events:

```python
# Using original event name
@sdk.adapter.Telegram.on("message")
async def handle_message(event):
    pass

# Using mapped event name
@sdk.adapter.Telegram.on("message")
async def handle_message(event):
    pass
```

### Special Field Examples

```python
# Callback Query event
{
  "type": "notice",
  "detail_type": "telegram_callback_query",
  "user_id": "123456",
  "user_nickname": "YingXinche",
  "telegram_callback_data": {
    "id": "cb_123",
    "data": "callback_data",
    "message_id": "msg_456"
  }
}

# Inline Query event
{
  "type": "notice",
  "detail_type": "telegram_inline_query",
  "user_id": "789012",
  "user_nickname": "YingXinche",
  "telegram_inline_query": {
    "id": "iq_789",
    "query": "search_text",
    "offset": "0"
  }
}

# Channel message
{
  "type": "message",
  "detail_type": "channel",
  "message_id": "msg_345",
  "channel_id": "channel_123",
  "telegram_chat": {
    "title": "News Channel",
    "username": "news_official"
  }
}
```

## Extended Field Descriptions

- All specific fields are identified with the `telegram_` prefix
- Original data is preserved in the `telegram_raw` field
- Channel messages use `detail_type="channel"`
- Entities within message content (e.g., bold, links) are converted into corresponding message segments
- Reply messages will have a message segment of type `telegram_reply` added

## Configuration Options

The Telegram adapter supports the following configuration options:

### Basic Configuration
- `token`: Telegram Bot Token
- `proxy_enabled`: Whether to enable proxy

### Proxy Configuration
- `proxy.host`: Proxy server address
- `proxy.port`: Proxy port
- `proxy.type`: Proxy type ("socks4" or "socks5")

### Operating Mode

The Telegram adapter only supports **Polling** mode. The Webhook mode has been removed.

Configuration Example:
```toml
[Telegram_Adapter]
token = "YOUR_BOT_TOKEN"
proxy_enabled = false

[Telegram_Adapter.proxy]
host = "127.0.0.1"
port = 1080
type = "socks5"



### 云湖适配

# Yunhu Platform Feature Documentation

YunhuAdapter is an adapter built on the Yunhu protocol, integrating all Yunhu functional modules and providing unified event handling and message operation interfaces.

---

## Document Information

- Corresponding Module Version: 3.5.1
- Maintainer: ErisPulse

## Basic Information

- Platform Overview: Yunhu (Yunhu) is an enterprise-level instant messaging platform.
- Adapter Name: YunhuAdapter
- Multi-account Support: Supports identifying and configuring multiple Yunhu bot accounts via `bot_id`
- Chained Modifier Support: Supports chainable modifier methods such as `.Reply()`
- OneBot12 Compatibility: Supports sending messages in OneBot12 format

## Supported Message Sending Types

All sending methods are implemented using chain syntax, for example:
```python
from ErisPulse.Core import adapter
yunhu = adapter.get("yunhu")

await yunhu.Send.To("user", user_id).Text("Hello World!")
```

Supported sending types include:
- `.Text(text: str, buttons: List = None, parent_id: str = "")`: Send plain text message, with optional buttons and parent message ID.
- `.Html(html: str, buttons: List = None, parent_id: str = "")`: Send HTML format message.
- `.Markdown(markdown: str, buttons: List = None, parent_id: str = "")`: Send Markdown format message.
- `.Image(file: bytes, buttons: List = None, parent_id: str = "", stream: bool = False, filename: str = None)`: Send image message, supports streaming upload and custom filename.
- `.Video(file: bytes, buttons: List = None, parent_id: str = "", stream: bool = False, filename: str = None)`: Send video message, supports streaming upload and custom filename.
- `.File(file: bytes, buttons: List = None, parent_id: str = "", stream: bool = False, filename: str = None)`: Send file message, supports streaming upload and custom filename.
- `.Batch(target_ids: List[str], message: str, content_type: str = "text", **kwargs)`: Send messages in batch.
- `.Edit(msg_id: str, text: str, content_type: str = "text", buttons: List = None)`: Edit existing message.
- `.Recall(msg_id: str)`: Recall message.
- `.Board(scope: str, content: str, **kwargs)`: Announce board, scope supports `local` and `global`.
- `.DismissBoard(scope: str, **kwargs)`: Dissolve/Revoke board.
- `.Stream(content_type: str, content_generator: AsyncGenerator, **kwargs)`: Send stream message.

Board board_type supports the following types:
- `local`: Specified user board
- `global`: Global board

### Button Parameter Description

The `buttons` parameter is a nested list representing the layout and function of buttons. Each button object contains the following fields:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `text` | string | Yes | Text on the button |
| `actionType` | int | Yes | Action type: <br>`1`: Jump URL <br>`2`: Copy <br>`3`: Report |
| `url` | string | No | Used when `actionType=1`, indicating the target URL to jump to |
| `value` | string | No | When `actionType=2`, this value is copied to the clipboard <br>When `actionType=3`, this value is sent to the subscriber endpoint |

Example:
```python
buttons = [
    [
        {"text": "Copy", "actionType": 2, "value": "xxxx"},
        {"text": "Jump URL", "actionType": 1, "url": "http://www.baidu.com"},
        {"text": "Report Event", "actionType": 3, "value": "xxxxx"}
    ]
]
await yunhu.Send.To("user", user_id).Text("Message with buttons", buttons=buttons)
```
> **Note:**
> - Push notifications are only received when a user clicks the **"Report Event"** button. Neither **"Copy"** nor **"Jump URL"** will trigger a push notification.

### Chained Modifier Methods (Composable)

Chainable modifier methods return `self`, supporting chained calls. They must be called before the final sending method:

- `.Reply(message_id: str)`: Reply to a specific message.
- `.At(user_id: str)`: Mention a specific user.
- `.AtAll()`: Mention everyone.
- `.Buttons(buttons: List)`: Add buttons.

### Chained Call Examples

```python
# Basic send
await yunhu.Send.To("user", user_id).Text("Hello")

# Reply to message
await yunhu.Send.To("group", group_id).Reply(msg_id).Text("Reply message")

# Reply + Buttons
await yunhu.Send.To("group", group_id).Reply(msg_id).Buttons(buttons).Text("Message with reply and buttons")
```

### OneBot12 Message Support

The adapter supports sending messages in OneBot12 format to facilitate cross-platform message compatibility:

- `.Raw_ob12(message: List[Dict], **kwargs)`: Send OneBot12 format message.

```python
# Send OneBot12 format message
ob12_msg = [{"type": "text", "data": {"text": "Hello"}}]
await yunhu.Send.To("user", user_id).Raw_ob12(ob12_msg)

# Combined with chained modifiers
ob12_msg = [{"type": "text", "data": {"text": "Reply message"}}]
await yunhu.Send.To("group", group_id).Reply(msg_id).Raw_ob12(ob12_msg)
```

## Return Values of Sending Methods

All sending methods return a Task object, which can be awaited directly to obtain the sending result. The returned result follows the ErisPulse adapter standardized return specification:

```python
{
    "status": "ok",           // Execution status
    "retcode": 0,             // Return code
    "data": {...},            // Response data
    "self": {...},            // Self information (contains bot_id)
    "message_id": "123456",   // Message ID
    "message": "",            // Error message
    "yunhu_raw": {...}        // Raw response data
}
```

## Platform-Specific Event Types

Must detect `platform=="yunhu"` before using platform-specific features.

### Core Differences

1. Platform-Specific Event Types:
    - Forms (e.g., Form command): `yunhu_form`
    - Button Click: `yunhu_button_click`
    - Bot Setting: `yunhu_bot_setting`
    - Shortcut Menu: `yunhu_shortcut_menu`
2. Extended Fields:
    - All platform-specific fields are identified with the `yunhu_` prefix
    - Original data is preserved in the `yunhu_raw` field
    - In private chats, `self.user_id` represents the bot ID

### Special Field Examples

```python
# Form command
{
  "type": "message",
  "detail_type": "private",
  "yunhu_command": {
    "name": "Form command name",
    "id": "Command ID",
    "form": {
      "FieldID1": {
        "id": "FieldID1",
        "type": "input/textarea/select/radio/checkbox/switch",
        "label": "Field label",
        "value": "Field value"
      }
    }
  }
}

# Button event
{
  "type": "notice",
  "detail_type": "yunhu_button_click",
  "user_id": "User ID who clicked the button",
  "user_nickname": "User nickname",
  "message_id": "Message ID",
  "yunhu_button": {
    "id": "Button ID (may be empty)",
    "value": "Button value"
  }
}

# Bot setting
{
  "type": "notice",
  "detail_type": "yunhu_bot_setting",
  "group_id": "Group ID (may be empty)",
  "user_nickname": "User nickname",
  "yunhu_setting": {
    "SettingItemID": {
      "id": "Setting Item ID",
      "type": "input/radio/checkbox/select/switch",
      "value": "Setting value"
    }
  }
}

# Shortcut menu
{
  "type": "notice",
  "detail_type": "yunhu_shortcut_menu",
  "user_id": "User ID who triggered the menu",
  "user_nickname": "User nickname",
  "group_id": "Group ID (if group chat)",
  "yunhu_menu": {
    "id": "Menu ID",
    "type": "Menu type (integer)",
    "action": "Menu action (integer)"
  }
}
```

## Extended Field Description

- All platform-specific fields are identified with the `yunhu_` prefix to avoid conflicts with standard fields.
- Original data is preserved in the `yunhu_raw` field for easy access to complete raw data from the Yunhu platform.
- `self.user_id` represents the bot ID (obtained from `bot_id` in the configuration).
- Form commands provide structured data via the `yunhu_command` field.
- Button click events provide button-related information via the `yunhu_button` field.
- Bot setting changes provide setting item data via the `yunhu_setting` field.
- Shortcut menu operations provide menu-related information via the `yunhu_menu` field.

---

## Multi-Bot Configuration

### Configuration Description

The Yunhu adapter supports configuring and running multiple Yunhu bot accounts simultaneously.

```toml
# config.toml
[Yunhu_Adapter.bots.bot1]
bot_id = "30535459"  # Bot ID (Required)
token = "your_bot1_token"  # Bot token (Required)
webhook_path = "/webhook/bot1"  # Webhook path (Optional, default to "/webhook")
enabled = true  # Whether to enable (Optional, default to true)

[Yunhu_Adapter.bots.bot2]
bot_id = "12345678"  # ID of the second bot
token = "your_bot2_token"  # Token of the second bot
webhook_path = "/webhook/bot2"  # Independent webhook path
enabled = true
```

**Configuration Item Description:**
- `bot_id`: Unique identifier ID of the bot (Required), used to identify which bot triggered the event.
- `token`: API token provided by the Yunhu platform (Required).
- `webhook_path`: HTTP path to receive Yunhu events (Optional, default to "/webhook").
- `enabled`: Whether to enable this bot (Optional, default to true).

**Important Notes:**
1. Events from the Yunhu platform do not contain the bot ID, therefore it must be explicitly specified in the configuration as `bot_id`.
2. Each bot should have an independent `webhook_path` to receive respective webhook events.
3. When configuring webhooks on the Yunhu platform, please configure the corresponding URL for each bot, for example:
   - Bot1: `https://your-domain.com/webhook/bot1`
   - Bot2: `https://your-domain.com/webhook/bot2`

### Specifying Bot using Send DSL

You can specify which bot to use for sending messages via the `Using()` method. This method supports two parameters:
- **Account Name**: The bot name in the configuration (e.g., `bot1`, `bot2`)
- **bot_id**: The `bot_id` value in the configuration

```python
from ErisPulse.Core import adapter
yunhu = adapter.get("yunhu")

# Send message using account name
await yunhu.Send.Using("bot1").To("user", "user123").Text("Hello from bot1!")

# Send message using bot_id (automatically matches corresponding account)
await yunhu.Send.Using("30535459").To("group", "group456").Text("Hello from bot!")

# Use the first enabled bot if not specified
await yunhu.Send.To("user", "user123").Text("Hello from default bot!")
```

> **Tip:** When using `bot_id`, the system will automatically search for the matching account in the configuration. This is particularly useful when handling event replies, as you can directly use `event["self"]["user_id"]` to reply using the same account.

### Bot Identification in Events

Received events automatically include the corresponding `bot_id` information:

```python
from ErisPulse.Core.Event import message

@message.on_message()
async def handle_message(event):
    if event["platform"] == "yunhu":
        # Get the bot ID that triggered the event
        bot_id = event["self"]["user_id"]
        print(f"Message from Bot: {bot_id}")
        
        # Reply to the message using the same bot
        yunhu = adapter.get("yunhu")
        await yunhu.Send.Using(bot_id).To(
            event["detail_type"],
            event["user_id"] if event["detail_type"] == "private" else event["group_id"]
        ).Text("Reply message")
```

### Log Information

The adapter automatically includes `bot_id` information in the logs for debugging and tracking:

```
[INFO] [yunhu] [bot:30535459] Received private chat message from user user123
[INFO] [yunhu] [bot:12345678] Message sent successfully, message_id: abc123
```

### Management Interface

```python
# Get all account information
bots = yunhu.bots

# Check if account is enabled
bot_status = {
    bot_name: bot_config.enabled
    for bot_name, bot_config in yunhu.bots.items()
}

# Dynamically enable/disable account (requires adapter restart)
yunhu.bots["bot1"].enabled = False
```

### Old Configuration Compatibility

The system automatically supports old format configurations, but migration to the new configuration format is recommended for better multi-bot support.



### 邮件适配

# Mail Platform Feature Documentation

MailAdapter is an email adapter based on the SMTP/IMAP protocol, supporting email sending, receiving, and processing.

---

## Documentation Information

- Corresponding Module Version: 1.0.0
- Maintainer: ErisPulse


## Supported Message Sending Types

All sending methods are implemented using chained syntax, for example:
```python
from ErisPulse.Core import adapter
mail = adapter.get("email")

# Simple text email
await mail.Send.Using("from@example.com").To("to@example.com").Subject("测试").Text("内容")

# HTML email with attachments
await mail.Send.Using("from@example.com")
    .To("to@example.com")
    .Subject("HTML邮件")
    .Cc(["cc1@example.com", "cc2@example.com"])
    .Attachment("report.pdf")
    .Html("<h1>HTML内容</h1>")

# Note: When using chained syntax, parameter methods must be set before the sending methods (Text, Html)
```

Supported sending types include:
- `.Text(text: str)`: Send plain text email
- `.Html(html: str)`: Send HTML email
- `.Attachment(file: str, filename: str = None)`: Add attachment
- `.Cc(emails: Union[str, List[str]])`: Set CC
- `.Bcc(emails: Union[str, List[str]])`: Set BCC
- `.ReplyTo(email: str)`: Set reply-to address

### Special Parameters Explanation

| Parameter | Type | Description |
|-----------|------|-------------|
| Subject | str | Email subject |
| From | str | Sender address (set via Using) |
| To | str | Recipient address |
| Cc | str or List[str] | CC address list |
| Bcc | str or List[str] | BCC address list |
| Attachment | str or Path | Attachment file path |

## Special Event Types

Email receiving event format:
```python
{
  "type": "message",
  "detail_type": "private",  # Default private chat for email
  "platform": "email",
  "self": {"platform": "email", "user_id": account_id},
  "message": [
    {
      "type": "text",
      "data": {
        "text": f"Subject: {subject}\nFrom: {from_}\n\n{text_content}"
      }
    }
  ],
  "email_raw": {
    "subject": subject,
    "from": from_,
    "to": to,
    "date": date,
    "text_content": text_content,
    "html_content": html_content,
    "attachments": [att["filename"] for att in attachments]
  },
  "attachments": [  # List of attachment data
    {
      "filename": "document.pdf",
      "content_type": "application/pdf",
      "size": 1024,
      "data": b"..."  # Attachment binary data
    }
  ]
}
```

## Extended Field Descriptions

- `email_raw`: Contains raw email data
- `attachments`: List of attachment data

## OneBot12 Protocol Conversion Explanation

Conversion of email events to OneBot12 protocol, main differences:

### Core Differences

1. Special fields:
   - `email_raw`: Contains raw email data
   - `attachments`: List of attachment data

2. Special handling:
   - Email subject and sender information will be included in the message text
   - Attachment data will be provided in binary form
   - HTML content will be retained in the email_raw field

### Example

```python
{
  "type": "message",
  "platform": "email",
  "message": [
    {
      "type": "text",
      "data": {
        "text": "Subject: Meeting Notice\nFrom: sender@example.com\n\nPlease check the attachment"
      }
    }
  ],
  "email_raw": {
    "subject": "Meeting Notice",
    "from": "sender@example.com",
    "to": "receiver@example.com",
    "html_content": "<p>Please check the attachment</p>",
    "attachments": ["document.pdf"]
  },
  "attachments": [
    {
      "filename": "document.pdf",
      "data": b"...",  # Attachment binary data
      "size": 1024
    }
  ]
}



### 平台文档维护说明

# Documentation Maintenance Guidelines

This document is maintained by adapter developers to explain the differences between this adapter and the OneBot12 standard, as well as its extended functionalities.
Please update this document synchronously when releasing a new version.

## Update Requirements

1. Accurately describe platform-specific sending methods and parameters.
2. Detail the differences with the OneBot12 standard.
3. Provide clear code examples and parameter descriptions.
4. Maintain consistent document formatting for easy user reference.
5. Timely update version information and maintainer contact details.

## Document Structure Standards

### 1. Basic Information Section
Each platform feature document should contain the following basic information:
```markdown
# [Platform Name] Adapter Documentation

Adapter Name: [Adapter Class Name]
Platform Introduction: [Brief introduction]
Supported Protocol/API Version: [Specific protocol or API version]
Maintainer: [Maintainer Name/Team]
Corresponding Module Version: [Version Number]
```

### 2. Supported Message Sending Types
List all supported sending methods and their parameters in detail:
```markdown
## Supported Message Sending Types

All sending methods are implemented via chained syntax, for example:
[Code Example]

Supported sending types include:
- Method 1: Description
- Method 2: Description
- ...

### Parameter Description
| Parameter | Type | Description |
|------|------|------|
| Parameter Name | Type | Description |
```

### 3. Platform-Specific Event Types
Describe platform-specific event types and formats in detail:
```markdown
## Platform-Specific Event Types

[Platform Name] event conversion to the OneBot12 protocol, where standard fields fully comply with the OneBot12 protocol, but the following differences exist:

### Core Differences
1. Platform-specific event types:
   - Event Type 1: Description
   - Event Type 2: Description
2. Extended fields:
   - Field Description

### Special Field Examples
[JSON Example]
```

### 4. Extended Field Description
```markdown
## Extended Field Description

- All platform-specific fields are identified with the `[platform]_` prefix.
- Original data is preserved in the `[platform]_raw` field.
- [Other special field descriptions]
```

### 5. Configuration Options (if applicable)
```markdown
## Configuration Options

The [Platform Name] adapter supports the following configuration options:

### Basic Configuration
- Config Item 1: Description
- Config Item 2: Description

### Special Configuration
- Special Config Item 1: Description
```

## Content Writing Standards

### Code Example Standards
1. All code examples must be runnable complete examples.
2. Use standard import methods:
```python
from ErisPulse.Core import adapter
[Adapter Instance] = adapter.get("[Adapter Name]")
```
3. Provide examples for multiple usage scenarios.

### Document Format Standards
1. Use standard Markdown syntax.
2. Clear title hierarchy, maximum 4 levels.
3. Use standard Markdown table format.
4. Code blocks should use appropriate language identifiers.

### Version Update Notes
When updating the document, update version information at the top:
```markdown
## Document Information

- Corresponding Module Version: [New Version Number]
- Maintainer: [Maintainer Information]
- Last Updated: [Date]
```

## Quality Checklist

Before submitting a document update, please check the following:

- [ ] Document structure complies with requirements
- [ ] All code examples run correctly
- [ ] Parameter descriptions are complete and accurate
- [ ] Event format examples match actual output
- [ ] Links and references are correct
- [ ] No syntax or spelling errors
- [ ] Version information has been updated
- [ ] Maintainer information is accurate

## Reference Documents

Refer to the following documents when writing to ensure consistency:
- [OneBot12 Standard Documentation](https://12.onebot.dev/)
- [ErisPulse Core Concepts](../core/concepts.md)
- [Event Conversion Standards](../standards/event-conversion.md)
- [API Response Specifications](../standards/api-response.md)
- [Other Platform Adapter Documentation](./)

## Contribution Flow

1. Fork [ErisPulse](https://github.com/ErisPulse/ErisPulse) repository
2. Modify the corresponding platform documentation under the `docs/platform-features/` directory
3. Ensure the documentation complies with the above requirements
4. Submit a Pull Request with a detailed description of the changes

If you have any questions, please contact the relevant adapter maintainer or ask in the project Issues.



====
代码规范
====


### 文档字符串规范

# ErisPulse Comment Style Guide

Method comments are mandatory when creating EP core methods. The comment format is as follows:

## Module-level Documentation Comment

Each module file should start with module documentation:

```python
"""
[Module Name]
[Module Description]

{!--< tips >!--}
Important usage instructions or notes
{!--< /tips >!--}
"""
```

## Method Comments

### Basic Format
```python
def func(param1: type1, param2: type2) -> return_type:
    """
    [Function Description]
    
    :param param1: [Type1] [Parameter Description 1]
    :param param2: [Type2] [Parameter Description 2]
    :return: [Return Type] [Return Description]
    """
    pass
```

### Full Format (For complex methods)
```python
def complex_func(param1: type1, param2: type2 = None) -> Tuple[type1, type2]:
    """
    [Detailed Function Description]
    [Can contain multi-line description]
    
    :param param1: [Type1] [Parameter Description 1]
    :param param2: [Type2] [Optional Parameter Description 2] (Default: None)
    
    :return: 
        type1: [Return Parameter Description 1]
        type2: [Return Parameter Description 2]
    
    :raises ErrorType: [Error Description]
    """
    pass
```

## Special Tags (For API Documentation Generation)

When method comments contain the following content, corresponding effects will occur during API documentation generation:

| Tag Format | Purpose | Example |
|---------|------|------|
| `{!--< internal-use >!--}` | Marks as internal use, does not generate documentation | `{!--< internal-use >!--}` |
| `{!--< ignore >!--}` | Ignores this method, does not generate documentation | `{!--< ignore >!--}` |
| `{!--< deprecated >!--}` | Marks as deprecated method | `{!--< deprecated >!--} Please use new_func() instead` |
| `{!--< experimental >!--}` | Marks as experimental feature | `{!--< experimental >!--} May be unstable` |
| `{!--< tips >!--}...{!--< /tips >!--}` | Multi-line tips content | `{!--< tips >!--}\nImportant tip content\n{!--< /tips >!--}` |
| `{!--< tips >!--}` | Single-line tips content | `{!--< tips >!--} Note: This method needs initialization first` |

## Best Practices

1. **Type Hints**: Use Python type hinting syntax
   ```python
   def func(param: int) -> str:
   ```

2. **Parameter Description**: Note default values for optional parameters
   ```python
   :param timeout: [int] Timeout time (seconds) (Default: 30)
   ```

3. **Return Value**: Use `Tuple` or explicitly state for multiple return values
   ```python
   :return: 
       str: Status information
       int: Status code
   ```

4. **Exception Description**: Use `:raises` to annotate possible exceptions
   ```python
   :raises ValueError: Raised when parameter is invalid
   ```

5. **Internal Methods**: Non-public APIs should add the `{!--< internal-use >!--}` tag

6. **Deprecated Methods**: Mark deprecated methods and provide alternatives
   ```python
   {!--< deprecated >!--} Please use new_method() instead | 2025-07-09

