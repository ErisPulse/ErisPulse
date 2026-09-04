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

This document introduces the technical architecture of the ErisPulse SDK through visual diagrams to help you quickly understand the framework's design philosophy and module relationships.

Please directly return the complete translated Markdown content without any additional text.

Once again, please note: if the document contains language switch lines (lines with language names separated by `` | ``), strictly follow the formatting requirements outlined in point 8 above, and do not write incorrect formats such as ``[**Label**](file)``.

## SDK Core Architecture

The following diagram illustrates the core modules of the SDK and their relationships:

```mermaid
graph TB
    SDK["sdk<br/>Unified entry point"]

    SDK --> Event["Event<br/>Event system"]
    SDK --> Lifecycle["Lifecycle<br/>Lifecycle management"]
    SDK --> Logger["Logger<br/>Log management"]
    SDK --> Storage["Storage / env<br/>Storage management"]
    SDK --> Config["Config<br/>Configuration management"]
    SDK --> AdapterMgr["Adapter<br/>Adapter management"]
    SDK --> ModuleMgr["Module<br/>Module management"]
    SDK --> Router["Router<br/>Routing management"]
    SDK --> Client["Client<br/>HTTP client"]
    Event --> Command["command"]
    Event --> Message["message"]
    Event --> Notice["notice"]
    Event --> Request["request"]
    Event --> Meta["meta"]
    Event --> Conversation["Conversation<br/>Branch + persistence"]

    AdapterMgr --> BaseAdapter["BaseAdapter"]
    BaseAdapter --> P1["Yunhu"]
    BaseAdapter --> P2["Telegram"]
    BaseAdapter --> P3["OneBot11/12"]
    BaseAdapter --> PN["..."]

    ModuleMgr --> BaseModule["BaseModule"]
    BaseModule --> CM["Custom module"]

    BaseAdapter -.-> SendDSL["SendDSL<br/>Message sending"]
```

### Core Module Descriptions

| Module | Description |
|------|------|
| **Event** | Event system, providing five types of event handling: command / message / notice / request / meta, as well as Conversation for multi-turn dialogues |
| **Adapter** | Adapter manager, managing the registration, startup, and shutdown of multi-platform adapters |
| **Module** | Module manager, managing plugin registration, loading, and unloading, supporting dependency declaration and topological sorting |
| **Lifecycle** | Lifecycle manager, providing event-driven lifecycle hooks |
| **Storage** | Key-value storage system based on SQLite, supporting general SQL chained queries |
| **Config** | Configuration file management in TOML format |
| **Logger** | Modular logging system, supporting sub-loggers |
| **Router** | HTTP/WebSocket routing management, abstracting the underlying backend (currently FastAPI + Uvicorn), supporting decorator routing, middleware, grouping, rate limiting, CORS |
| **Client** | Unified HTTP/WS client (pre-2.8.0 was `HttpClient`, compatible alias retained), abstracting the underlying request library (currently aiohttp), providing request statistics, retry, logging, WebSocket client, ErisPulse exception system, etc. The WebSocket client and server share the `WebSocketConnectionBase` base class |

## Initialization Process

The following diagram illustrates the complete initialization process of `sdk.init()`:

```mermaid
flowchart TD
    A["sdk.init()"] --> B["Prepare runtime environment"]
    B --> B1["Load configuration file"]
    B1 --> B2["Set global exception handling"]
    B2 --> C["Adapter & module discovery"]
    C --> D{"Parallel loading"}
    D --> D1["Load adapters from PyPI"]
    D --> D2["Load modules from PyPI"]
    D1 & D2 --> E["Register adapters"]
    E --> E1["Start adapters"]
    E1 --> F["Register modules"]
    F --> F1{"Dependency validation"}
    F1 -->|"Missing dependencies"| F2["Skip module and log warning"]
    F1 -->|"Dependencies satisfied"| F3["Topological sorting<br/>(Kahn algorithm + priority)"]
    F3 --> G["Initialize modules in order<br/>(instantiation + on_load)"]
    F2 --> G
    G --> H["Start router server"]
    H --> K["Ready to run"]
```

### Detailed Explanation of Initialization Stages

> The complete initialization chain is broken down into (Finder / Loader / Manager / Router), the underlying entry points (`init()` / `init_task()` / `init_sync()`), and manual full startup can be found in [Startup Process and Manual Control](advanced/startup.md).

## Event Handling Flow

The following diagram illustrates the complete message flow from the platform to the handler:

```mermaid
flowchart LR
    A["Platform Raw Message"] --> B["Adapter Receives"]
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
    I --> J["Adapter Sends to Platform"]
```

### Detailed Event Handling Chain

The diagram above shows the "result." Below, we break down what the framework does behind the scenes after `adapter.emit()` is called—this is a three-layer dispatch chain:

```mermaid
sequenceDiagram
    participant P as Platform
    participant A as Adapter Bus Layer<br/>AdapterManager.emit
    participant T as Handler Task Layer<br/>_dispatch_handler_task
    participant E as Event Module Layer<br/>_process_event

    P->>A: Native Event
    A->>A: Extract platform/type/detail_type + raw fields
    A->>A: [Recv] Receive Log
    A->>A: lifecycle.adapter.event.receive (earliest hook)
    A->>A: Process self field (meta branch / Bot auto-registration)
    A->>A: Middleware Chain (serial, can rewrite event data)
    A->>A: Collect handlers (specific type + wildcard *)
    A->>A: Identity Admission + Scope Filtering (silent discard/skip before task creation)
    A->>T: asyncio.create_task (fire-and-forget)
    A->>A: lifecycle.adapter.event.dispatched (final hook)
    T->>T: Acquire concurrency semaphore (default limit 64)
    T->>E: Call Event module-mounted handlers
    E->>E: lifecycle.event.pre_process
    E->>E: ignore_self (message events default to ignore self)
    E->>E: Group by priority: high → low, group inter-serial, group intra-concurrent
    E->>E: Intra-group copy execution + field merge (conflict warning)
    E->>E: Post-group check stop() to block lower priority
    T->>T: Slow Log (warn if over 1s, wait_reply time whitelisted)
```

**What the framework does at each step, and what you can intervene:**

| Phase | What the framework does | What you can intervene |
|------|-------------|-----------|
| Receive | Extract standard fields, retain `{platform}_raw` raw data; write `[Recv]` log | Listen to `adapter.event.receive` to get the earliest event |
| self field | Meta events branch into connect/disconnect/heartbeat; regular events auto-register Bot and trigger `adapter.bot.online` | Listen to `adapter.bot.online` / `bot.offline` |
| Middleware | **Serial** execution, if return value is not None, replace event data | Register middleware to rewrite or intercept events |
| Dispatch Collection | First get specific type handlers, then get `*` wildcard handlers | — |
| Identity Dimension | At dispatch entry point, determine whether to accept event based on user > session > Bot > adapter (`scope.is_identity_allowed`), **discard entire event if rejected** | Bind `ErisPulse.scope.identity` |
| Scope Filtering | Determine `scope.is_allowed` based on module owner (session level > Bot level > platform level), **silently skip if not passed** | Configure scope whitelist/blacklist |
| Scheduling | Each matching handler runs in an independent `asyncio.Task`, `emit()` **returns immediately without waiting** for handler completion | — |
| Priority | High-priority groups execute first; **inter-group serial, intra-group concurrent** (each group holds its own event copy, modified fields are merged back into the original event, conflicts trigger WARNING) | `@command(..., priority=N)` / specify priority at registration |
| Blocking | After each group is processed, check `event.is_stopped()`, if triggered, **do not execute lower priority** | `event.mark_processed(stop=True)` / `event.done()` |

> **Common Misconceptions**:
> 1. **Scope filtering is silent**—filtered handlers do not report errors or respond, only visible in TRACE-level logs (`core.scope.denied`). If "my module did not receive messages," prioritize checking scope binding.
> 2. **Handlers are naturally concurrent**—the framework already creates independent tasks for each handler, so you **do not need** to wrap them with `asyncio.create_task`.
> 3. **No blocking within the same priority group**—`mark_processed(stop=True)` only prevents lower-priority groups from executing, handlers already running concurrently within the same group are not interrupted.
> 4. **Slow log threshold is fixed at 1 second**—if handler execution exceeds 1 second, a WARNING is logged (`wait_reply` waiting time is excluded from the duration), but execution is not interrupted.

> For details on the three-level scope binding and priority, see [Scope System](advanced/scope.md); for the full semantics of claim/blocking, see [Event Handling Introduction](getting-started/event-handling.md); for concurrency limit configuration, see [Configuration Guide](user-guide/configuration.md#Framework_Configuration).

## Lifecycle Events

The following diagram shows the order in which lifecycle events are triggered for each component in the framework:

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

> For the complete event listener methods (`lifecycle.on()` / `once()` / `has_handlers()`), the full list of lifecycle events, and their data formats, see [Lifecycle Management](advanced/lifecycle.md).

## Module Loading Strategies

ErisPulse supports three module loading strategies, declared by the `ModuleLoadStrategy` returned by `get_load_strategy()`:

```mermaid
flowchart TD
    A["Module registered to ModuleManager"] --> B{"Loading Strategy"}
    B -->|"lazy_load = true<br/>+ activate_on declared"| C["Create ModuleActivator proxy"]
    B -->|"lazy_load = true<br/>no activate_on"| D["Create LazyModule proxy"]
    B -->|"lazy_load = false"| E["Create instance immediately"]
    C --> F["Register event/command stubs to dispatcher"]
    F --> G["Mount to sdk attribute"]
    G --> H["Activation triggered by event arrival"]
    H --> I["Instantiate + on_load() + unregister stubs"]
    D --> J["Mount to sdk attribute"]
    J --> K["Initialize on first attribute access"]
    E --> L["Call on_load()"]
    L --> M["Mount to sdk attribute"]
```

> For more details, please refer to [Lazy Loading System](advanced/lazy-loading.md), [Lifecycle Management](advanced/lifecycle.md), and module documentation.

### Event-Driven Lazy Activation (`activate_on`) Trigger Architecture

> [!NOTE]
> This feature requires ErisPulse **2.8.0+**.

`activate_on` allows modules to be loaded only when the **first matching event/command arrives**, avoiding constant memory usage while ensuring events are not lost:

```mermaid
flowchart LR
    subgraph Declare["Module Declaration"]
        S1["get_load_strategy() returns<br/>ModuleLoadStrategy(activate_on=...)"] --> S2["activate_on syntax:<br/>str / dict / list freely mixed"]
        S2 --> S2a["'message' → event type level"]
        S2 --> S2b["{'notice': 'group_member_increase'}<br/>→ type + detail_type"]
        S2 --> S2c["{'command': 'roll'}<br/>→ command trigger (shorthand/list)"]
        S2 --> S2d["{'command': {'name': 'dice', 'help': ...,<br/>'aliases': [...], 'hidden': ...}}<br/>→ command trigger (dict declaration)"]
    end

    subgraph Runtime["Runtime"]
        R1["ModuleActivator registers stubs"] --> R1a["Event stubs → message/notice/request/meta manager<br/>priority ACTIVATION_STUB_PRIORITY (very low)"]
        R1 --> R1b["Command stubs → command manager<br/>placeholder command (mirrors dict-declared help/usage/group/aliases/hidden)"]
        R1a --> R2{"Event trigger arrives"}
        R1b --> R2
        R2 --> R3["Filter by owner scope"]
        R3 --> R4["asyncio.Lock prevents duplicate activation"]
        R4 --> R5["Instantiate module + call on_load()"]
        R5 --> R6["Unregister all stubs"]
        R6 --> R7["Event forwarded to real handler"]
    end

    Declare --> Runtime
```

**Trigger Semantics Key Points:**

> Complete `activate_on` syntax (str / dict / list), command dict declaration, placeholder command help fallback chain, scope filtering, and failure semantics are described in [Lazy Loading System](advanced/lazy-loading.md#event-driven-lazy-activationactivate_on).

## Local Plugin Folder Architecture

> [!NOTE]
> This feature requires ErisPulse **2.8.0+**.

Local plugins (in the `plugins/` directory) do not need to be packaged for release; the framework automatically discovers and loads them during startup:

```mermaid
flowchart TD
    A["Project plugins/ directory<br/>（ErisPulse.framework.plugins_dir, supports multiple directories）"] --> B{"PluginFolderLoader.discover()"}
    B --> C["Single file: dice.py → plugin name = filename"]
    B --> D["Package format: weather/ (with __init__.py) → plugin name = directory name"]
    B --> E["Ignored: __pycache__ / _-prefixed / non .py / directories without __init__.py"]
    C --> F["Import module (spec_from_file_location)"]
    D --> G["Import module (sys.path + import_module)"]
    F --> H["Identify module class: Main (sub-class of BaseModule) preferred, fallback to first sub-class"]
    G --> H
    H --> I["Construct moduleInfo consistent with entry-point"]
    I --> J["ModuleLoader.load() merges<br/>local takes precedence over PyPI packages with same name"]
    J --> K["Shares with installed package modules:<br/>enabled status / scope / meta / i18n / context"]
```

**Conventions and Features:**

- Plugin name origin: filename for single files, directory name for package format
- Local plugin `moduleInfo.meta.source == "plugin_folder"`, seamlessly coexists with PyPI-installed package modules
- When names conflict, local takes precedence (for easy local override and debugging), and disabled plugins remove corresponding entry-point entries

Please directly return the complete translated Markdown content, without any additional text.

## Local Plugin Hot Reload Architecture

Hot reload monitors plugin file changes and automatically reloads the corresponding plugin:

```mermaid
flowchart TD
    A["sdk.enable_plugin_hot_reload()"] --> B["PluginReloadWatcher starts"]
    B --> C["PollingObserver (background daemon thread)<br/>Regularly compares .py file mtime"]
    C --> D{"Plugin file changed"}
    D --> E["Change debouncing (default 1 second)"]
    E --> F["_handle_change parses plugin name<br/>(single file / package format)"]
    F --> G["asyncio.run_coroutine_threadsafe<br/>schedules back to main event loop"]
    G --> H["sdk.reload_plugin(name)"]
    H --> I["Unloads old instance (triggers on_unload)"]
    I --> J["Cleans up registration (unregister + remove sdk attribute)"]
    J --> K["Cleans sys.modules to force re-import"]
    K --> L["Re-discover + register + load"]
    L --> M["Mounts new instance to sdk attribute"]
    M --> N["File deletion → automatically removed from load results"]
```

7. **Important: Path replacement rule**
   - Replace `docs/en/` in document links with `docs/en/`
   - For example: `docs/en/quick-start.md` should be changed to `docs/en/quick-start.md`
   - For links pointing to non-current language version files (e.g., `README.xx.md` format), keep them unchanged
   - This ensures links point to the correct language version of the document



====
快速上手
====


### 快速开始

# Quick Start

> **This is your first step.** Get an ErisPulse robot up and running from scratch in 5 minutes.

## Install ErisPulse

### One-Click Installation Script (Recommended)

The installation script will automatically detect your environment (Docker, Python, uv) and guide you to choose the most suitable installation method.

Windows (PowerShell):
```powershell
irm https://get.erisdev.com/install.ps1 -OutFile install.ps1; powershell -ExecutionPolicy Bypass -File install.ps1
```

macOS / Linux:
```bash
curl -fsSL https://get.erisdev.com/install.sh -o install.sh && chmod +x install.sh && ./install.sh
```

The script will guide you through:

- **Docker Installation** (Recommended if Docker is detected): Select image source (Docker Hub / GHCR), version channel (Stable / Pre-release), Dashboard management panel configuration, port settings
- **Traditional Installation**: Automatically create a virtual environment, select ErisPulse version, optionally install Dashboard management panel module

### Using Docker

The Docker image already includes the ErisPulse framework and Dashboard management panel.

```bash
# Download docker-compose.yml
curl -O https://raw.githubusercontent.com/ErisPulse/ErisPulse/main/docker-compose.yml

# Set Dashboard token and start
ERISPULSE_DASHBOARD_TOKEN=your-token docker compose up -d
```

<details>
<summary>Can't access Docker Hub?</summary>

Use GitHub Container Registry image, modify the `image` in `docker-compose.yml`:

```yaml
image: ghcr.io/erispulse/erispulse:latest
```

</details>

After starting, access `http://<host>:8000/Dashboard` and log in using the set token.

### Using pip

Ensure your Python version is >= 3.10, then install using pip:

```bash
pip install ErisPulse
```

If you have already installed [uv](https://github.com/astral-sh/uv), you can also use `uv pip install ErisPulse` for faster installation.

## Initialize Project

### Interactive Initialization (Recommended)

```bash
epsdk init
```

This will start an interactive wizard that guides you through:
- Project name setup
- Log level configuration
- Server configuration (host and port)
- Adapter selection and configuration
- Project structure creation

### Quick Initialization

```bash
# Quick mode with specified project name
epsdk init -q -n my_bot

# Or just specify the project name
epsdk init -n my_bot
```

### Manual Project Creation

If you prefer to create the project manually:

```bash
mkdir my_bot && cd my_bot
epsdk init
```

## Install Modules

### Install via CLI

```bash
epsdk install Yunhu AIChat
```

### View Available Modules

```bash
epsdk list-remote
```

### Interactive Installation

When no package name is specified, the interactive installation interface is entered:

```bash
epsdk install
```

## Running the Project

```bash
# Run normally
epsdk run main.py

# Hot reload mode (recommended for development)
epsdk run main.py --reload
```

## Enable IDE Completion (Optional)

ErisPulse dynamically discovers modules/adapters, and the IDE cannot complete platform-specific methods by default.  
Run the following command to generate type stubs:

```bash
epsdk types
```

After generation, use the imported types as variable annotations to get precise completion (see [IDE Completion Guide](./getting-started/ide-completion.md)):

```python
from _ep_types import Yunhu
from ErisPulse import sdk

adapter: Yunhu = sdk.adapter.get("yunhu")
await adapter.Send.To("group", "123").Board(...)  # Completion for platform-specific methods
```

## Project Structure

The project structure after initialization:

```
my_bot/
├── config/
│   └── config.toml          # Configuration file
└── main.py                  # Entry file

```

## Configuration File

Basic `config.toml` configuration:

```toml
[ErisPulse.server]
host = "0.0.0.0"
port = 8000

[ErisPulse.logger]
level = "INFO"

[Yunhu_Adapter]
# Adapter configuration
```



### 创建第一个机器人

# Creating Your First Bot

This guide builds upon the [5-Minute Quick Start](../quick-start.md), walking you through writing your first command handler and understanding the execution mechanism.

> If you haven't installed ErisPulse or initialized your project yet, please complete the "Install", "Initialize Project", and "Run Project" steps in the [Quick Start](../quick-start.md) first.

## Step 1: Writing Your First Command

Open `main.py` and write a simple command handler:

```python
from ErisPulse import sdk
from ErisPulse.Core.Event import command

@command("hello", help="Send a greeting message")
async def hello_handler(event):
    """Handle the hello command"""
    user_name = event.get_user_nickname() or "friend"
    await event.reply(f"Hello, {user_name}! I am the ErisPulse bot.")

@command("ping", help="Test if the bot is online")
async def ping_handler(event):
    """Handle the ping command"""
    await event.reply("Pong! The bot is running normally.")

async def main():
    """Main entry function"""
    print("Starting ErisPulse...")
    
    # keep_running=True (default): The framework blocks and maintains execution until a shutdown signal is received (such as Ctrl+C)
    await sdk.run(keep_running=True)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

### `keep_running` Parameter

`sdk.run(keep_running)` controls whether the framework blocks and maintains execution:

- **`keep_running=True` (default)**: `run()` will block indefinitely until a shutdown signal is received (such as Ctrl+C), suitable for pure bot applications.
- **`keep_running=False`**: `run()` returns immediately after initialization; **the framework is not unloaded**—the started adapters/modules continue processing message events as background tasks, allowing you to proceed with your own logic until the event loop ends and the framework closes. For example:

```python
async def main():
    await sdk.run(keep_running=False)   # Return immediately after initialization
    # The framework is running in the background, here you can continue doing other things
    while True:
        await asyncio.sleep(3600)
        print("Check every hour")
```

> In addition to the two modes of `run()`, there are also more granular ways to manually control the lifecycle using `init()`/`uninit()`, and to start/stop adapters/routers independently; see [Startup Process and Manual Control](../advanced/startup.md).

## Step 2: Running the Bot

```bash
# Normal execution
epsdk run main.py

# Development mode (supports hot reload)
epsdk run main.py --reload
```

## Step 3: Testing the Bot

Send commands in your chat platform:

```
/hello
```

You should receive a reply from the bot.

## Code Explanation

### Command Decorator

```python
@command("hello", help="Send a greeting message")
```

- `hello`: Command name, users invoke it via `/hello`
- `help`: Command help description, displayed in the `/help` command

### Event Parameters

```python
async def hello_handler(event):
```

The `event` parameter is an Event object, containing:
- Message content: `event.get_text()`
- Sender information: `event.get_user_id()`, `event.get_user_nickname()`
- Platform information: `event.get_platform()`
- Group information: `event.get_group_id()`
- Raw data: `event.get_raw()`

> For a complete list of Event object methods, refer to [Event Wrapper Class Detailed Explanation](../developer-guide/modules/event-wrapper.md).

### Sending a Reply

```python
await event.reply("Reply content")
```

`event.reply()` is a convenient method for sending messages to the sender.

## Extension: Adding More Features

ErisPulse provides rich event handling and data processing capabilities:

- **Message Listening**: Use `@message.on_message()` to listen to various types of messages → [Introduction to Event Handling](event-handling.md)
- **Notification Listening**: Use `@notice.on_friend_add()` and others to listen to system notifications → [Introduction to Event Handling](event-handling.md)
- **Data Storage**: Use `sdk.storage.get/set` to persist data → [Common Tasks Examples](common-tasks.md)

## Frequently Asked Questions

### Command Not Responding?

1. Check if the adapter is correctly configured; confirm that the adapter's `status` in `config/config.toml` is set to `true`
2. Check the terminal log output to ensure there are no error messages (especially `ERROR` level logs)
3. Confirm the command prefix is correct (default is `/`), check the `[ErisPulse.event.command]` section in the configuration file
4. Ensure the command name is spelled correctly, and pay attention to case sensitivity settings

### How to Modify the Command Prefix?

Add the following to `config.toml`:

```toml
[ErisPulse.event.command]
prefix = "!"
case_sensitive = false
```

### How to Support Multiple Platforms?

ErisPulse uses the OneBot12 standard to unify event formats across different platforms. Handlers registered with `@command` and `@message` automatically receive events from all platforms. You can distinguish the source platform using `event.get_platform()`:

```python
@command("hello")
async def hello_handler(event):
    platform = event.get_platform()
    
    if platform == "yunhu":
        await event.reply("Hello! From Yunhu")
    elif platform == "telegram":
        await event.reply("Hello! From Telegram")
    else:
        await event.reply("Hello!")
```

> For more multi-platform adaptation techniques, see [Common Tasks Examples](common-tasks.md#multi-platform-adaptation).



### 基础概念

# Basic Concepts

This guide introduces the core concepts of ErisPulse, helping you understand the framework's design philosophy and basic architecture.

## Event-Driven Architecture

ErisPulse adopts an event-driven architecture, where all interactions are passed and processed through events.

### Event Flow

```
User sends message
      │
      ▼
Platform receives
      │
      ▼
Adapter receives platform native event
      │
      ▼
Convert to OneBot12 standard event
      │
      ▼
Submit to event system
      │
      ▼
Dispatch to registered handlers
      │
      ▼
Module processes event
      │
      ▼
Send response through adapter
      │
      ▼
Platform displays to user
```

### OneBot12 Standard

ErisPulse uses OneBot12 as the core event standard. OneBot12 is a generic chatbot application interface standard that defines a unified event format.

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
sdk.client     # HTTP client
sdk.lifecycle  # Lifecycle system
```

### 2. Event Object

Event objects encapsulate event data and provide convenient access methods.

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

### 3. Adapter

Adapters are the bridge between ErisPulse and external platforms.

**Responsibilities:**
- Receive platform native events
- Convert to OneBot12 standard format
- Send standard format events to the platform

**Example Adapters:**
- Yunhu Adapter: Communicate with Yunhu platform
- Telegram Adapter: Communicate with Telegram Bot API
- OneBot11 Adapter: Communicate with OneBot11 compatible applications
- Email Adapter: Handle email sending and receiving

### 4. Module

Modules are the basic unit for functional extensions and can:

- Register event handlers
- Implement business logic
- Call adapters to send messages
- Use services provided by core modules

#### Module Discovery Mechanism

ErisPulse discovers installed modules via Python's `importlib.metadata.entry_points`. Modules declare entry points in `pyproject.toml`:

```toml
[project.entry-points."erispulse.module"]
MyModule = "my_package:Main"
```

When the SDK initializes, it scans all entry points in the `erispulse.module` group, registers module classes to `ModuleManager`, and then initializes them sequentially after topological sorting by dependencies.

#### Minimum Viable Module

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

- **Registration**: SDK discovers module class and registers to manager
- **Loading**: Creates module instance, calls `on_load(event)` (`event = {"module_name": "MyModule"}`)
- **Unloading**: Calls `on_unload(event)`, cleans up resources

#### Load Strategy

Declare the module's loading behavior via `get_load_strategy()`:

```python
from ErisPulse.loaders import ModuleLoadStrategy

class Main(BaseModule):
    @staticmethod
    def get_load_strategy():
        return ModuleLoadStrategy(
            lazy_load=True,   # Whether to lazy load (default True)
            priority=0        # Load priority, larger numbers initialize earlier
        )
```

- **`lazy_load=True` (default)**: Module initializes only when first accessed (e.g., `sdk.MyModule`), reducing startup time
- **`lazy_load=False`**: Module initializes immediately when SDK starts, suitable for modules that need to listen to lifecycle events or execute scheduled tasks
- **`priority`**: Modules with the same priority load in registration order; larger numbers initialize earlier

> For a detailed explanation of the lazy loading mechanism, please refer to [Lazy Loading System](../advanced/lazy-loading.md).

## Event Types

ErisPulse supports 5 categories of events:

| Event Type | Decorator | Description |
|---------|--------|------|
| Message Event | `@message.on_message()` | Any message sent by the user (private chat, group chat) |
| Command Event | `@command("name")` | Messages starting with the command prefix (e.g., `/hello`) |
| Notice Event | `@notice.on_friend_add()` etc. | System notifications (friend added, group member changes, etc.) |
| Request Event | `@request.on_friend_request()` etc. | User requests (friend request, group invite) |
| Meta Event | `@meta.on_connect()` etc. | System-level events (connect, disconnect, heartbeat) |

> For detailed usage and code examples of each event type, please refer to [Getting Started with Event Handling](event-handling.md).

## Core Module Explanations

### Storage (Storage)

SQLite-based key-value storage system for persistent data.

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

### Config (Configuration)

TOML format configuration file management.

```python
# Get config
config = sdk.config.getConfig("MyModule", {})

# Set config
sdk.config.setConfig("MyModule", {"key": "value"})

# Read nested config
value = sdk.config.getConfig("MyModule.subkey", "default")
```

### Logger (Logging)

Modular logging system.

```python
# Log messages
sdk.logger.info("This is an info message")
sdk.logger.warning("This is a warning message")
sdk.logger.error("This is an error message")

# Get child logger
child_logger = sdk.logger.get_child("submodule")
child_logger.info("Submodule log")
```

**Property Access Syntax Sugar**

In addition to using the `get_child()` method, you can create child loggers via **property access**, which is a more concise **syntax sugar**:

```python
# Create child logger via property access
sdk.logger.mymodule.info("Module message")

# Support nested access
sdk.logger.mymodule.database.info("Database message")
```

### Router (Routing)

HTTP and WebSocket routing management, based on FastAPI + Uvicorn. Supports decorator routing, middleware, grouping, rate limiting, CORS.

```python
from ErisPulse.Core import HttpRequest

@sdk.router.get("MyModule", "/api")
async def handler(request: HttpRequest):
    data = await request.json()
    return {"status": "ok"}
```

> For the complete routing API (WebSocket, middleware, rate limiting, CORS, etc.), please refer to [Router Manager](../advanced/router.md).

### Client (Network Client)

Unified network client aggregating HTTP requests, WebSocket connections, connection pool management, automatic retry, timeout control, request statistics, and lifecycle event integration.

```python
from ErisPulse.Core import client

# HTTP request
resp = await client.get("https://api.example.com/users")
data = await resp.json()

# With retry and timeout
resp = await client.get(url, timeout=30, max_retries=3)

# WebSocket connection
ws = await client.ws_connect("wss://example.com/ws")
async for text in ws.iter_text():
    await ws.send_text(f"Echo: {text}")
```

> For the complete network client API, please refer to [Network Client](../advanced/http-client.md).

## SendDSL Message Sending

Adapters provide message sending interfaces with method chaining.

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

# Reply to message
await yunhu.Send.To("group", "G1001").Reply("msg123").Text("reply")

# @All
await yunhu.Send.To("group", "G1001").AtAll().Text("announcement")
```

### Event Reply Methods

Event objects provide convenient reply methods:

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

ErisPulse enables module lazy loading by default. Modules are initialized only when first accessed (e.g., `sdk.MyModule`), significantly improving startup speed.

```python
from ErisPulse.loaders import ModuleLoadStrategy

class Main(BaseModule):
    @staticmethod
    def get_load_strategy():
        return ModuleLoadStrategy(
            lazy_load=True,   # Enable lazy loading (default)
            priority=0        # Load priority, larger numbers initialize earlier
        )
```

**Scenarios where lazy loading needs to be disabled (`lazy_load=False`):**
- Modules listening to lifecycle events (e.g., `core.init.complete`)
- Modules starting scheduled tasks or background services
- Modules that need to complete initialization before other modules load

> For a detailed description of the lazy loading mechanism and precautions, please refer to [Lazy Loading System](../advanced/lazy-loading.md).



### 事件处理入门

# Getting Started with Event Handling

This guide introduces how to handle various events in ErisPulse.

## Event Type Overview

ErisPulse supports the following event types:

| Event Type | Description | Use Cases |
|------------|-------------|-----------|
| Message Event | Any message sent by a user | Chatbots, content filtering |
| Command Event | Messages starting with a command prefix | Command handling, feature entry points |
| Notification Event | System notifications (e.g., friend added, group member changes) | Welcome messages, status notifications |
| Request Event | User requests (e.g., friend requests, group invitations) | Automatic request handling |
| Meta Event | System-level events (e.g., connection, heartbeat) | Connection monitoring, status checks |

## Message Event Handling

> **Tip**: It is recommended to use the `Event` type annotation in event handlers to get IDE auto-completion and type checking support.

```python
from ErisPulse.Core.Event import Event  # Import Event type for type annotation
```

### Listening to All Messages

```python
from ErisPulse.Core.Event import message, Event

@message.on_message()
async def message_handler(event: Event):
    text = event.get_text()
    user_id = event.get_user_id()
    sdk.logger.info(f"Received message from {user_id}: {text}")
```

### Listening to Private Messages

```python
@message.on_private_message()
async def private_handler(event: Event):
    user_id = event.get_user_id()
    await event.reply(f"Hello, {user_id}! This is a private message.")
```

### Listening to Group Messages

```python
@message.on_group_message()
async def group_handler(event: Event):
    group_id = event.get_group_id()
    user_id = event.get_user_id()
    sdk.logger.info(f"Message sent by {user_id} in group {group_id}")
```

### Listening to @ Messages

```python
@message.on_at_message()
async def at_handler(event: Event):
    # Get list of mentioned users
    mentions = event.get_mentions()
    await event.reply(f"You mentioned these users: {mentions}")
```

### Wildcard and Regular Expression Matching

The four message decorators (`on_message`, `on_private_message`, `on_group_message`, and `on_at_message`) both support `pattern` (glob wildcard) and `regex` (regular expression). Messages that do not match will **not trigger** the handler:

```python
# Glob wildcard: * for any string, ? for single character, [seq] for character set
@message.on_message(pattern="Sign in*")
async def signin_handler(event: Event):
    await event.reply("Sign-in successful")

# Regular expression: match amount
@message.on_message(regex=r"\d+\s*Yuan")
async def price_handler(event: Event):
    await event.reply(f"Received amount: {event.get_text()}")

# Both pattern and regex provided → both must match
@message.on_message(pattern="*Yuan", regex=r"\d+\s*Yuan")
async def combined_handler(event: Event):
    pass
```

The `wait_reply` also supports these two parameters (see [Wait for Reply](../developer-guide/modules/event-wrapper.md#wait-for-reply-function)).

## Command Event Handling

### Basic Commands

```python
from ErisPulse.Core.Event import command

@command("help", help="Show help information")
async def help_handler(event):
    help_text = """
Available commands:
/help - Show help
/ping - Test connection
/info - View information
    """
    await event.reply(help_text)
```

### Command Aliases

```python
@command(["help", "h"], aliases=["帮助"], help="Show help information")
async def help_handler(event):
    await event.reply("Help information...")
```

Users can invoke the command using any of the following:
- `/help`
- `/h`
- `/帮助`

### Command Parameters

```python
@command("echo", help="Echo the message")
async def echo_handler(event):
    # Get command arguments
    args = event.get_command_args()
    
    if not args:
        await event.reply("Please enter the message to echo")
    else:
        await event.reply(f"You said: {' '.join(args)}")
```

### Command Groups

```python
@command("admin.reload", group="admin", help="Reload module")
async def reload_handler(event):
    await event.reply("Module has been reloaded")

@command("admin.stop", group="admin", help="Stop the bot")
async def stop_handler(event):
    await event.reply("Bot has been stopped")
```

### Command Permissions and Access Control

Command permissions are checked in three layers, from top to bottom (if upper layer denies, lower layers are not checked):

```python
# ① Command ACL (user-side configuration): per-command user allow/deny list, replies "Permission denied" on denial
# ② master=True —— Only the framework owner can execute (automatically checked by framework, replies "Permission denied" on denial)
@command("restart", master=True, help="Restart module")
async def restart_handler(event):
    await event.reply("Module has been restarted")

# ③ permission=callable —— Command-specific control logic (only executes if returns True)
def is_admin(event):
    return event.get_user_id() in {"user123", "user456"}

@command("panel", permission=is_admin, help="Admin panel")
async def panel_handler(event):
    await event.reply("Welcome to the admin panel")
```

**Command ACL** (Control Plane `ErisPulse.scope.commands`): Users can configure allow/deny lists for any command, command names support exact match and glob patterns (e.g., `"roll*"`), replies "Permission denied" on denial:

```toml
# config.toml —— Only allow user "onebot11:123456" to execute restart; deny user "onebot11:666" entirely
[ErisPulse.scope.commands.restart]
allow = ["onebot11:123456"]
deny = ["onebot11:666"]
```

Evaluation order: if `deny` matches → deny; if `allow` is non-empty and does not match → deny; otherwise, proceed to developer's default (via `master=True` / `permission`). Runtime API (command names support glob):

```python
from ErisPulse import sdk
sdk.scope.allow_user("restart", "onebot11", "123456")   # Allow list
sdk.scope.deny_user("restart", "onebot11", "666")       # Deny list
sdk.scope.remove_acl("restart")                          # Clear allow/deny lists
sdk.scope.get_acl("restart")                             # Query current lists
```

Cross-command / cross-user **event-level** access control (whether a message from a specific user / group / bot is received) is handled via the control plane's **identity dimension** (`scope.identity`); **module-level** availability (which modules are available) is handled via the control plane's **module dimension** (`scope.platforms / bots / sessions`). See [Unified Control Plane](../advanced/scope.md).

> Suggestion: Use `master=True` / `permission` for command logic that requires business-level coordination; use the control plane's identity dimension for access control based on user / group; use the control plane's module dimension for controlling module availability.

### Command Priority

```python
# Higher priority number executes earlier
@message.on_message(priority=10)
async def high_priority_handler(event):
    await event.reply("High priority handler")

@message.on_message(priority=1)
async def low_priority_handler(event):
    await event.reply("Low priority handler")
```

### Parallel Event Handling

ErisPulse's event system uses a **parallel execution for same priority, serial execution for different priorities** scheduling model:

```
Event arrives
    ↓
priority=10 group: [Handler C || Handler D] parallel → merge results
    ↓ (if not interrupted)
priority=0 group: [Handler A || Handler B] parallel → merge results
    ↓
...
```

- **Parallel within same priority**: Multiple handlers with the same priority execute simultaneously, improving throughput
- **Serial across priorities**: Groups with different priorities execute in order (higher priority numbers execute first), ensuring high-priority handlers run first
- **Copy-On-Write**: No copy is created if handlers do not modify the event, ensuring zero overhead
- **Conflict handling**: When multiple handlers at the same priority modify the same field, the last modification is used, and a warning log is recorded
- **Interruption mechanism**: After any handler calls `event.done()` (default) or `event.done(claim=False)`, subsequent lower-priority groups are skipped. The difference between claiming and blocking is explained in the following section [Link Control: Claiming and Blocking](#link-control-claiming-and-blocking)

```python
# Example: Parallel execution of handlers with same priority
@message.on_message(priority=0)
async def handler_a(event):
    # Process task A
    event['result_a'] = process_a()

@message.on_message(priority=0)
async def handler_b(event):
    # Executed in parallel with handler_a
    event['result_b'] = process_b()

# Sequential execution across priorities
@message.on_message(priority=10)
async def handler_c(event):
    # Highest priority, executes first
    pass
```

> **Concurrency limit**: All matching handlers' Tasks are **immediately created**, but a semaphore limits the **maximum number of concurrent executions**, defaulting to **64** (`ErisPulse.framework.handler_max_concurrency`, supports hot update). Tasks exceeding the limit are queued on the semaphore and proceed only after earlier ones complete. This acts as your "pressure relief valve" during event surges.
>
> **Slow logs**: If a single handler takes more than **1 second**, the framework logs a WARNING (`handler_slow`). The `wait_reply` waiting time is excluded from the duration, so waiting for a reply won't trigger a slow handler warning.

## Control Plane Filtering: Why Didn't My Module Receive the Message?

After an event arrives, there are two **silent** filters (neither replies nor errors):

1. **Identity Dimension** (`ErisPulse.scope.identity`): When an event enters the distribution entry point, it is determined whether to receive the event based on User > Group > Bot > Adapter.
   Events that are rejected are **entirely discarded**, and no handler (including the command dispatcher) will be triggered.
2. **Module Dimension** (`ErisPulse.scope`): When an event reaches a module's handler/command, it is determined whether the module is available based on Session > Bot > Platform.
   If it **fails the check, it is silently skipped**.

```toml
# Example 1: Do not propagate all messages from a specific group
[ErisPulse.scope.identity.sessions.onebot11."group_123"]
deny = true

# Example 2: Block MyModule from a specific Bot
[ErisPulse.scope.bots.onebot11."123456"]
blocked = ["MyModule"]
```

In this case, when messages arrive from that group, the `MyModule` command and event handlers **will not be scheduled**. This is not a bug, but a filtering mechanism—when troubleshooting "module not responding," prioritize checking the control plane's identity and module binding.

- Filter logs are only visible at the **TRACE** level (`core.scope.identity_denied` / `core.scope.denied`), and by default, nothing is visible at the INFO level.
- Framework-level handlers (such as the command dispatcher with `scope_exempt=True`) are not affected by the **module dimension**, but are affected by the **identity dimension** (the entire event has already been discarded).
- Before command execution, there is a third filter: command permission ACL (replies "insufficient permissions" on denial, see previous section).

> For five-dimensional configuration, matching syntax, and runtime API, see [Unified Control Plane](../../advanced/scope.md).

## Link Control: Claiming and Blocking

> [!NOTE]
> The `claim=` / `stop=` parameters for `event.done()` / `event.mark_processed()` require ErisPulse **2.7.1+**.

ErisPulse decouples the two orthogonal semantics of "claiming" and "blocking," controlling them uniformly via `event.done()`, which facilitates adding observation layers (such as logging, auditing, and permissions) around command handling.

**Precise definitions of the two concepts:**

- **Claiming (claim):** Marks the event as processed by this handler (writes to `_processed`). When the command dispatcher sees an already claimed event, it will **skip deduplication**—preventing the same message from being repeatedly processed by multiple command handlers. Typical scenario: Claim after a command match is successful, preventing the command dispatcher from intervening again.
- **Blocking (stop):** Prevents the event from propagating to **lower-priority** handlers (writes to `_propagation_stopped`). Lower-priority handlers (e.g., `on_message`) will no longer see the event. Typical scenario: A high-priority handler has fully processed the event and does not want lower-priority handlers to execute.

| `event.done(...)` | Claim | Block | Scenario |
|-------------------|-------|-------|----------|
| `event.done()` | ✔ | ✔ | Standard practice when a command/handler finishes processing |
| `event.done(stop=False)` | ✔ | ✘ | Only claim: lower-priority observers (logging / statistics) still see the event |
| `event.done(claim=False)` | ✘ | ✔ | Only block (e.g., firewall / rate limiting), but do not deduplicate commands |

`event.done(claim=, stop=)` is an alias for `event.mark_processed(claim=, stop=)`, and both have identical parameters and behavior.

```python
@command("help")
async def help_cmd(event):
    event.done()            # Claim + Block (standard practice when command processing is complete)

@message.on_message(priority=50)
async def observer(event):
    event.done(stop=False)  # Only claim: lower-priority handlers still execute (logging / statistics)

@message.on_message(priority=100)
async def firewall(event):
    if denied(event):
        event.done(claim=False)  # Only block: lower-priority handlers do not execute, but no deduplication is performed
```

### `block` Configuration for Commands and Replies

By default, after a command matches successfully or `wait_reply` matches a reply, propagation is blocked (for backward compatibility). You can configure this to allow propagation to lower-priority handlers (logging / auditing / permissions) to observe these messages:

```toml
[ErisPulse.event.command]
block = false   # Command messages continue to flow to lower-priority handlers

[ErisPulse.event.wait_reply]
block = false   # Replies consumed by wait_reply continue to flow to lower-priority handlers
```

## Notification Event Handling

### Friend Added

```python
from ErisPulse.Core.Event import notice

@notice.on_friend_add()
async def friend_add_handler(event):
    user_id = event.get_user_id()
    nickname = event.get_user_nickname() or "New Friend"
    await event.reply(f"Welcome to add me as a friend, {nickname}!")
```

### Group Member Added

```python
@notice.on_group_increase()
async def member_increase_handler(event):
    group_id = event.get_group_id()
    user_id = event.get_user_id()
    await event.reply(f"Welcome new member {user_id} to group {group_id}")
```

### Group Member Removed

```python
@notice.on_group_decrease()
async def member_decrease_handler(event):
    group_id = event.get_group_id()
    user_id = event.get_user_id()
    await event.reply(f"Member {user_id} has left group {group_id}")
```

## Request Event Handling

### Friend Request

```python
from ErisPulse.Core.Event import request

@request.on_friend_request()
async def friend_request_handler(event):
    user_id = event.get_user_id()
    comment = event.get_comment()
    
    sdk.logger.info(f"Received friend request: {user_id}, comment: {comment}")
    
    # You can handle the request through the adapter API
    # Refer to each adapter's documentation for specific implementation
```

### Group Invitation Request

```python
@request.on_group_request()
async def group_request_handler(event):
    group_id = event.get_group_id()
    user_id = event.get_user_id()
    
    await event.reply(f"Received group invitation {group_id}, from {user_id}")
```

## Meta Event Handling

### Connection Events

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

### Heartbeat Events

```python
@meta.on_heartbeat()
async def heartbeat_handler(event):
    platform = event.get_platform()
    sdk.logger.debug(f"{platform} heartbeat detected")
```

### Bot Status Queries

After an adapter sends a meta event, the framework automatically tracks the Bot status, and you can query it at any time:

```python
from ErisPulse import sdk

# Check if a specific Bot is online
if sdk.adapter.is_bot_online("telegram", "123456"):
    telegram = sdk.adapter.get("telegram")
    await telegram.Send.To("user", "123456").Text("Bot is online")

# List all currently online Bots
bots = sdk.adapter.list_bots()
for platform, bot_list in bots.items():
    for bot_id, info in bot_list.items():
        print(f"{platform}/{bot_id}: {info['status']}")

# Get a complete status summary
summary = sdk.adapter.get_status_summary()
```

## Interactive Handling

### Using the `reply` Method to Send Responses

The `event.reply()` method supports various modifiers, making it convenient to send messages with features like @ mentions and replies:

```python
# Simple reply
await event.reply("Hello")

# Send different types of messages
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

# Combine: @ user + reply to a message
await event.reply("Content", at_users=["user1"], reply_to="msg_id")
```

### Waiting for User Replies

```python
@command("ask", help="Ask user")
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
@command("age", help="Ask age")
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
        await event.reply(f"Your age is {age} years old")
    else:
        await event.reply("Invalid input or timeout")
```

### Waiting for Reply with Callback

```python
@command("confirm", help="Confirm operation")
async def confirm_handler(event):
    async def handle_confirmation(reply_event):
        text = reply_event.get_text().lower()
        
        if text in ["yes", "是", "y"]:
            await event.reply("Operation confirmed!")
        else:
            await event.reply("Operation canceled.")
    
    await event.reply("Confirm this operation? (Yes/No)")
    
    await event.wait_reply(
        timeout=30,
        callback=handle_confirmation
    )
```

### Confirmation Dialogue (`confirm`)

Wait for user confirmation or negation, automatically recognizing built-in Chinese and English confirmation words:

```python
@command("confirm", help="Confirm operation")
async def confirm_handler(event):
    if await event.confirm("Are you sure you want to execute this operation?"):
        await event.reply("Confirmed, executing...")
    else:
        await event.reply("Operation canceled")

# Custom confirmation words
if await event.confirm("Continue?", yes_words={"go", "continue"}, no_words={"stop", "stop"}):
    pass
```

### Selection Menu (`choose`)

Users can reply with option numbers or text:

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
        await event.reply("No selection made within the timeout")
```

**Merge Mode**: When `merge_prompt=True`, options are merged into the prompt message and sent as a single message using the specified `method`:

```python
# Send merged prompt + options using Markdown
choice = await event.choose(
    "## Please select a color\n{options}\nPlease reply with the number",
    ["Red", "Green", "Blue"],
    method="Markdown",
    merge_prompt=True,
)
```

> The `{options}` placeholder controls where options are inserted; if not specified, they are appended to the end of the prompt.
> You can customize the placeholder using the `placeholder` parameter (e.g., `placeholder="[choices]"`).
> `options_format="auto"` (default) automatically selects the style based on the method: unordered list for Markdown, ordered list for HTML, plain text list for others.
> For text-based methods (Text/Markdown/Html, etc.), options are merged by default at the end; for non-text methods (Image, etc.), options are sent as separate messages by default.

### Collecting Forms (`collect`)

Collect user input in multiple steps:

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
        await event.reply("Registration timed out or invalid input")
```

### Waiting for Any Event (`wait_for`)

Wait for any event that meets the condition, not limited to the same user:

```python
@command("wait_member", help="Wait for new member")
async def wait_member_handler(event):
    await event.reply("Waiting for new member to join...")
    
    evt = await event.wait_for(
        event_type="notice",
        condition=lambda e: e.get_detail_type() == "group_member_increase",
        timeout=120
    )
    
    if evt:
        await event.reply(f"Welcome new member: {evt.get_user_id()}")
    else:
        await event.reply("Timeout waiting")
```

### Multi-turn Dialogue (`conversation`)

Create an interactive multi-turn dialogue context:

```python
@command("survey", help="Questionnaire survey")
async def survey_handler(event):
    conv = event.conversation(timeout=60)
    
    await conv.say("Welcome to the questionnaire survey!")
    
    while conv.is_active:
        reply = await conv.wait()
        
        if reply is None:
            await conv.say("Dialogue timed out, goodbye!")
            break
        
        text = reply.get_text()
        
        if text == "Exit":
            await conv.say("Goodbye!")
            break
        
        await conv.say(f"You said: {text}, continue typing or reply 'Exit' to end")
```

### Built-in Confirmation Words

ErisPulse includes built-in sets of Chinese and English confirmation words:

- **Confirmation words** (`CONFIRM_YES_WORDS`): yes, 是, y, confirm, confirm, ok, true, 对, 嗯, 行, agree, no problem, ...
- **Negation words** (`CONFIRM_NO_WORDS`): no, 否, n, cancel, 不, 不要, 不行, cancel, false, 错, refuse,不可以...

## Event Data Access

### Common Event Object Methods

```python
@command("info")
async def info_handler(event):
    # Basic information
    event_id = event.get_id()
    event_time = event.get_time()
    event_type = event.get_type()
    detail_type = event.get_detail_type()
    
    # Sender information
    user_id = event.get_user_id()
    nickname = event.get_user_nickname()
    
    # Message content
    message_segments = event.get_message()
    alt_message = event.get_alt_message()
    text = event.get_text()
    
    # Group information
    group_id = event.get_group_id()
    
    # Bot information
    self_id = event.get_self_user_id()
    self_platform = event.get_self_platform()
    
    # Raw data
    raw_data = event.get_raw()
    raw_type = event.get_raw_type()
    
    # Platform information
    platform = event.get_platform()
    
    # Message type checking
    is_private = event.is_private_message()
    is_group = event.is_group_message()
    is_at = event.is_at_message()
    
    # Command information
    if event.is_command():
        cmd_name = event.get_command_name()
        cmd_args = event.get_command_args()
        cmd_raw = event.get_command_raw()
```

### Platform-Specific Methods

In addition to the built-in methods, each platform adapter registers platform-specific methods to allow access to platform-specific data.

```python
from ErisPulse.Core.Event import message

@message.on_message()
async def handle_message(event):
    platform = event.get_platform()

    # Call platform-specific methods based on the platform
    if platform == "telegram":
        chat_type = event.get_chat_type()      # Telegram-specific method
    elif platform == "email":
        subject = event.get_subject()           # Email-specific method
```

If you are unsure whether a platform has registered a specific method, you can query which methods have been registered for a particular platform:

```python
from ErisPulse.Core.Event import get_platform_event_methods

methods = get_platform_event_methods("telegram")
# ["get_chat_type", "is_bot_message", ...]
```

> For platform-specific methods, please refer to the corresponding [Platform Guide](../platform-guide/).

## Event Handling Best Practices

### 1. Exception Handling

```python
@command("process")
async def process_handler(event):
    try:
        # Business logic
        result = await do_some_work()
        await event.reply(f"Result: {result}")
    except ValueError as e:
        # Expected business error
        await event.reply(f"Parameter error: {e}")
    except Exception as e:
        # Unexpected error
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
    logger.debug(f"Detailed debug information")
```

### 3. Conditional Handling

```python
@message.on_message(priority=0)
async def conditional_handler(event):
    """Conditional handling - conditions checked inside the handler"""
    # Only process messages from specific users
    if event.get_user_id() in ["bot1", "bot2"]:
        return
    
    # Only process messages containing specific keywords
    if "keyword" not in event.get_text():
        return
    
    await event.reply("Condition met, processing message")
```



### IDE 补全

# Type Stub Generation (IDE Completion)

ErisPulse dynamically discovers modules/adapters via entry-points, and the exact types of user classes are not known at the static level. The `epsdk types` command scans installed modules/adapters and generates a type stub file, allowing users to use these types as variable annotations to obtain IDE completion.

## Core Design Principles

The stub file **only exports types**, without providing any runtime instances:

- All imports are under ``TYPE_CHECKING``, **zero runtime overhead, zero behavior change**
- Type names use the PascalCase form of the entry-point name (e.g., ``yunhu`` → ``Yunhu``), corresponding to the names passed into ``sdk.adapter.get()`` / ``sdk.module.get()``
- Users use ``sdk.module.get(...)`` / ``sdk.adapter.get(...)`` as usual to get instances, but use imported types for **variable annotations**

## Basic Usage

Run in the project root directory:

```bash
epsdk types
```

This generates `_ep_types.py` in the current directory, containing types for all installed modules/adapters.

## Using in Code

```python
from _ep_types import MyModule, Yunhu
from ErisPulse import sdk

# Using imported types as variable annotations enables IDE completion for the class methods
my_mod: MyModule = sdk.module.get("MyModule")
my_mod.hello()                  # ← IDE completes hello

my_adapter: Yunhu = sdk.adapter.get("yunhu")
await my_adapter.Send.To("group", "123").Board(...)   # ← Completes platform-specific methods
```

## How It Works

1. Scan `erispulse.adapter` / `erispulse.module` entry-points
2. Use a subprocess to introspect in the target Python environment, collecting actual class information for each adapter/module (including module path and qualified name)
3. Generate a `.py` file, where:
   - All ``from xxx import Yyy as Zzz`` are under ``TYPE_CHECKING``
   - ``Zzz`` is the PascalCase form of the entry-point name
4. The IDE reads the ``TYPE_CHECKING`` section to provide completion; no code is executed at runtime

Example of generated stub:

```python
# _ep_types.py (auto-generated)
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    # Adapters
    from MyAdapter.Core import MyAdapter as MyAdapter
    from YunhuAdapter.Core import YunhuAdapter as Yunhu

    # Modules
    from MyModule.Core import Main as MyModule

    __all__ = ['MyAdapter', 'Yunhu', 'MyModule']
```

## Command Options

| Option | Description |
|--------|-------------|
| `-o, --output PATH` | Specify the output file path (default `./_ep_types.py`) |
| `--force` | Overwrite existing stub file |
| `--adapters-only` | Only scan adapters |
| `--modules-only` | Only scan modules |

## When to Regenerate

- After installing/uninstalling new modules or adapters
- After modules/adapters update their public API
- When IDE completion fails or types are outdated

## Relationship with SendDSL Standard Methods

The `SendDSL` base class already includes standard send methods (Text/Image/Voice/Video/File), so any way of obtaining a `SendDSL` instance can complete these methods. The `types` command is mainly used to complete **platform-specific methods** (e.g., Yunhu's `Board`, Sandbox's `Dice`) and **module-specific methods**.



=====
适配器开发
=====


### 适配器开发入门

# Getting Started with Adapter Development

This guide helps you begin developing ErisPulse adapters to connect new messaging platforms.

## Adapter Introduction

### What is an Adapter

An adapter serves as the bridge between ErisPulse and various messaging platforms, responsible for:

1. **Forward Conversion**: Receiving platform events and converting them into OneBot12 standard format (Converter)
2. **Reverse Conversion**: Converting OneBot12 message segments into platform API calls (`Raw_ob12`)
3. Managing the connection with the platform (WebSocket/WebHook)
4. Providing a unified SendDSL message sending interface

### Adapter Architecture

```mermaid
flowchart LR
    subgraph receive["Forward Conversion (Receiving)"]
        direction TB
        P1["Platform Event"] --> C1["Converter.convert()"] --> O1["OneBot12 Standard Event"] --> S1["Event System"] --> M1["Module Processing"]
    end
    subgraph send["Reverse Conversion (Sending)"]
        direction TB
        M2["Module Builds Message"] --> R1["Send.Raw_ob12()"] --> N1["Platform Native API Call"] --> R2["Standard Response Format"]
    end
```

## Directory Structure

Standard adapter package structure:

```
MyAdapter/
├── pyproject.toml          # Project configuration
├── README.md               # Project description
├── LICENSE                 # License
└── MyAdapter/
    ├── __init__.py          # Package entry point
    ├── Core.py               # Main adapter class
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
    "ErisPulse>=2.4.0"  # ErisPulse has aiohttp built-in, usually no need to depend separately
]

[project.urls]
"homepage" = "https://github.com/yourname/MyAdapter"

[project.entry-points."erispulse.adapter"]
"MyAdapter" = "MyAdapter:MyAdapter"
```

### 3. Create Adapter Main Class

The framework provides `ConfigClass` / `AccountConfigClass` for declarative configuration management. The adapter only needs to declare the configuration class to automatically load, validate, and generate the configuration template.

```python
# MyAdapter/Core.py
from dataclasses import dataclass, field
from ErisPulse.Core import BaseAdapter
from ErisPulse.Core.Bases import BaseConfig

@dataclass
class MyAdapterConfig(BaseConfig):
    """MyAdapter Configuration"""
    api_endpoint: str = field(
        default="https://api.example.com",
        metadata={
            "description": {"i18n": "my_adapter.api_endpoint", "default": "API Address"},
            "required": False,
            "ui": {"widget": "text", "group": "connection", "order": 1},
        },
    )
    token: str = field(
        default="",
        metadata={
            "description": {"i18n": "my_adapter.token", "default": "Platform Token"},
            "required": True,
            "secret": True,
            "ui": {"widget": "password", "group": "basic", "order": 2},
        },
    )

class MyAdapter(BaseAdapter):
    ConfigClass = MyAdapterConfig  # Declare the configuration class, the framework manages it automatically
    
    # No need to override __init__! The framework handles it automatically:
    # - self.sdk / self.logger are set automatically
    # - self.cfg reads the configuration in real time
    # - self.Send / self.Request are initialized automatically
    
    def _setup_converter(self):
        from .Converter import MyPlatformConverter
        return MyPlatformConverter()
```

> ⚠️ **About `__init__`**: In the new version, `BaseAdapter.__init__(self, sdk=None)` automatically handles SDK references, log initialization, and configuration loading. Most adapters **do not need to override `__init__`**. See [__init__ Notes](#init-注意事项).

> ⚠️ **About `super().__init__()`**: `BaseAdapter.__init__()` is responsible for creating `Send` and `Request` factory instances. If you forget to call it, all message sending and request operations will report `AttributeError`. See [__init__ Notes](#init-注意事项).

### 4. Implement Required Methods

```python
class MyAdapter(BaseAdapter):
    # ... __init__ code ...
    
    async def start(self):
        """Start the adapter (must implement)"""
        # Register WebSocket or WebHook route
        router.register_websocket(
            module_name="myplatform",
            path="/ws",
            handler=self._ws_handler
        )
        self.logger.info("Adapter started")
    
    async def shutdown(self):
        """Shut down the adapter (must implement)"""
        router.unregister_websocket(
            module_name="myplatform",
            path="/ws"
        )
        # Clean up connections and resources
        self.logger.info("Adapter shut down")
    
    async def call_api(self, endpoint: str, **params):
        """Call platform API (must implement)"""
        raise NotImplementedError("call_api needs to be implemented")
```

#### Actively Send Meta Events

The adapter should actively send meta events to allow the framework to track the Bot's online status. Use `emit_meta()` to complete this in one line:

```python
class MyAdapter(BaseAdapter):
    async def _ws_handler(self, websocket):
        bot_id = self._get_bot_id()

        # Bot goes online
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
            # Bot goes offline
            await self.emit_meta("disconnect", bot_id)
```

> For detailed Bot status management and meta event explanations, see [Adapter Best Practices - Bot Status Management and Meta Events](best-practices.md#bot-状态管理与-meta-事件).

### 5. Implement Send Class

`At`/`AtAll`/`Reply` decorators are already implemented by the framework's SendDSL base class. The adapter only needs to implement `Raw_ob12` and specific send methods.

The framework provides two key helper methods:
- `self._apply_modifiers(message)` — automatically merges At/AtAll/Reply decorators into message segments
- `self.send_context` — gets the send context dictionary (`target_type`, `target_id`, `account_id`)

```python
import asyncio

class MyAdapter(BaseAdapter):
    # ... other code ...

    class Send(BaseAdapter.Send):

        def Raw_ob12(self, message, **kwargs):
            """
            Send OneBot12 format message (must implement)

            Use _apply_modifiers to automatically merge decorator states,
            use send_context to get send context.
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

        # Text/Image/Voice/Video/File are inherited from the SendDSL base class,
        # defaulting to delegation to Raw_ob12, no need to repeat implementation.
        # If platform-specific logic is needed, you can override individual methods:
        # def Text(self, text: str):
        #     return self.Raw_ob12([{"type": "text", "data": {"text": text}}])
```

**Media-type send method implementation points:**

- The default implementation of the base class will encapsulate the `file` parameter as a OneBot12 message segment and pass it to `Raw_ob12`. The adapter needs to handle downloading/uploading in `Raw_ob12`.
- The `file` parameter should support both `bytes` binary data and `str` URL types.
- When a URL is passed, the file must be downloaded before uploading to the platform.
- The platform usually requires first calling the upload interface to obtain a file identifier, then calling the send interface.

**`__getattr__` Magic Method:**

- Implement case-insensitive method names (`Text`, `text`, `TEXT` can all be called)
- Undefined methods should return a prompt message instead of raising an error

**`Raw_ob12` Method:**

- Convert OneBot12 standard message format to platform format for sending
- Use `self._apply_modifiers(message)` to automatically handle At/AtAll/Reply decorators
- Use `**self.send_context` to pass send target information and account information

### 6. Implement Converter

```python
# MyAdapter/Converter.py
import time
import uuid

class MyPlatformConverter:
    def convert(self, raw_event):
        """Convert platform-native events to OneBot12 standard format"""
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
        """Convert event types"""
        type_map = {
            "message": "message",
            "notice": "notice"
        }
        return type_map.get(event_type, "unknown")
    
    def _convert_detail_type(self, raw_event):
        """Convert detail types"""
        return "private"  # Simplified example
```

### 7. Implement Request Class (Request Operations)

If your platform supports friend requests, group invitations, or other requests requiring the Bot to make decisions, you can implement the `Request` inner class:

```python
from ErisPulse.Core import BaseAdapter, RequestDSL

class MyAdapter(BaseAdapter):
    # ... Send and other code ...

    class Request(RequestDSL):
        """Request operation implementation (friend requests, group invitations, etc.)"""

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

Module developers use it as follows:

```python
from ErisPulse.Core.Event import request

@request.on_friend_request()
async def handle_friend_request(event):
    # Use Event convenience methods
    await event.approve()
    # Or operate directly through the adapter
    await adapter.myplatform.Request("req_id").accept()
```

> If the platform does not support request operations, you can omit implementing the `Request` inner class. The base class defaults to returning `retcode=10002` (operation not supported). See [Request Action Specification](../../standards/request-action-spec.md).

### 8. Create Package Entry Point

```python
# MyAdapter/__init__.py
from .Core import MyAdapter
```

## Dependency Declaration (Optional, 2.8.0+)

Adapters can declare dependencies on other adapters or modules to enable adapter interconnection and optional features:

```python
from typing import ClassVar

class MyAdapter(BaseAdapter):
    # Hard dependency: Adapter startup is skipped if dependency is missing (warning + status=skipped-dependency event)
    depends: ClassVar[dict] = {
        "adapters": ["onebot11"],   # Dependent adapters (by platform name)
        "modules": ["TranslateEngine"],  # Dependent modules (by registration name)
    }
    # Soft dependency: Missing does not affect startup; callbacks are received when modules are loaded/unloaded (optional feature mode)
    optional_modules: ClassVar[list] = ["TranslateEngine"]
```

- **Startup Order**: Adapters that declare hard dependencies on modules will **start after the modules are initialized**
- **Soft Dependency Notification**: `on_dependency_ready(module_name)` is called when modules in `optional_modules` (or hard dependencies) are loaded; `on_dependency_lost(module_name)` is called when modules are unloaded (default is empty implementation, can be overridden) — covers late loading and hot reload scenarios:

```python
async def on_dependency_ready(self, module_name):
    """Soft dependency module is ready: Enable corresponding optional features"""
    if module_name == "TranslateEngine":
        self._translate = self.sdk.TranslateEngine

async def on_dependency_lost(self, module_name):
    """Soft dependency module is lost: Downgrade functionality"""
    if module_name == "TranslateEngine":
        self._translate = None
```

> [!NOTE]
> This feature requires ErisPulse **2.8.0+**.

## `__init__` Notes

There are three levels in adapter development that may involve `__init__` overwriting. Below are the correct practices for each level.

### 1. BaseAdapter Level (Most Cases Do Not Need to Overwrite)

`BaseAdapter.__init__(self, sdk=None)` is responsible for creating `Send` / `Request` factory instances and automatically performs the following tasks:

- Accepts the `sdk` parameter and sets `self.sdk`, `self.logger`
- If `ConfigClass` is declared, you can read global configurations in real time via `self.cfg`
- If `AccountConfigClass` is declared, you can read multi-account configurations in real time via `self.accounts`

**In most cases, you do not need to overwrite `__init__`**; simply declare `ConfigClass`:

```python
class MyAdapter(BaseAdapter):
    ConfigClass = MyAdapterConfig  # After declaration, the framework manages configurations automatically
    
    async def start(self):
        cfg = self.cfg  # Type-safe, reads in real time
        ...
```

If you really need to customize initialization, call `super().__init__(sdk)`:

```python
class MyAdapter(BaseAdapter):
    ConfigClass = MyAdapterConfig
    
    def __init__(self, sdk=None):
        super().__init__(sdk)  # Pass sdk
        self.converter = self._setup_converter()
        self.convert = self.converter.convert
```

### 2. Send Inner Class (Most Cases Do Not Need to Overwrite)

`SendDSL.__init__` is responsible for state passing in chained calls (target type, target ID, account, etc.). **In most cases, you only need to overwrite methods** (`Raw_ob12`, `Text`, etc.), not `__init__`.

If you do need to (for example, initializing platform-specific states), **you must pass through all parameters**:

```python
class MyAdapter(BaseAdapter):
    class Send(BaseAdapter.Send):
        # Parameters: adapter, target_type, target_id, account_id
        def __init__(self, adapter, target_type=None, target_id=None, account_id=None):
            super().__init__(adapter, target_type, target_id, account_id)  # ← Must pass through
            self._my_state = None  # Platform-specific initialization
```

**Why must it be passed through?** Each step of the chained call creates a new instance via `self.__class__(...)`:

```python
adapter.Send.To("user", "123")               # → Send(adapter, "user", "123", None)
adapter.Send.To("user", "123").Using("bot1")  # → Send(adapter, "user", "123", "bot1")
```

If the `__init__` signature does not match or `super()` is not called, the chained call will break.

### 3. Request Inner Class (Most Cases Do Not Need to Overwrite)

Same as Send. The parameters are `adapter`, `request_id`, `account_id`:

```python
class MyAdapter(BaseAdapter):
    class Request(RequestDSL):
        # Parameters: adapter, request_id, account_id
        def __init__(self, adapter, request_id=None, account_id=None):
            super().__init__(adapter, request_id, account_id)  # ← Must pass through
            self._my_state = None  # Platform-specific initialization
```

### Summary

| Level | When to overwrite | What must be done |
|------|------------|-----------|
| **BaseAdapter** | When custom initialization logic is needed | `super().__init__(sdk)` (pass sdk parameter) |
| **Send Inner Class** | When initializing send-related states is needed | `super().__init__(adapter, target_type, target_id, account_id)` |
| **Request Inner Class** | When initializing request-related states is needed | `super().__init__(adapter, request_id, account_id)` |
| All three levels | Most cases | **Just declare ConfigClass, do not touch `__init__`** |

### 9. Connection Information and Route Discovery

After registering routes, the framework records all route information. Users can use the following API to view the adapter's connection address:

```python
from ErisPulse import sdk

# Get complete connection information for the adapter
info = sdk.adapter.get_connection_info("myplatform")
# {
#   "platform": "myplatform",
#   "status": "started",
#   "connection": {
#     "base_url": "http://localhost:8080",
#     "http_routes": [
#       {"path": "/myplatform/webhook", "method": "POST",
#        "url": "http://localhost:8080/myplatform/webhook"}
#     ],
#     "websocket_routes": [
#       {"path": "/myplatform/ws",
#        "url": "ws://localhost:8080/myplatform/ws"}
#     ]
#   }
# }

# List all namespaces (adapters/modules) routes
namespaces = sdk.router.list_namespaces()
# {"myplatform": {"http": ["/myplatform/webhook"], "websocket": ["/myplatform/ws"]}}

# Get complete connection URLs for the namespace
urls = sdk.router.get_module_urls("myplatform")
# {"base_url": "http://localhost:8080", "http": [...], "websocket": [...]}

# Get detailed route information for the namespace
routes = sdk.router.get_module_routes("myplatform")
# {"http": [{"path": "/myplatform/webhook", "methods": ["POST"]}],
#  "websocket": [{"path": "/myplatform/ws", "auth": false}]}
```

> **Tip**: The information returned by `get_connection_info()` is suitable for displaying to users (such as in a WebUI), helping users configure the callback address or WebSocket connection address on the platform side. The `module_name` registered during route registration must exactly match the `platform` name registered by the adapter in ErisPulse; otherwise, route discovery will not be correctly associated.

### 10. SSE (Server-Sent Events) Support

ErisPulse has built-in, server-agnostic SSE support. Modules and adapters can register SSE endpoints using `@sdk.router.sse()`.

#### Basic Usage

```python
import asyncio
from ErisPulse import sdk

@sdk.router.sse("MyModule", "/events")
async def event_stream(sse):
    """Push SSE events"""
    count = 0
    while not sse.closed:
        await sse.send({"count": count}, event="update")
        count += 1
        await asyncio.sleep(1)
```

#### Using Request Parameters

The handler can declare a `request` parameter to access client request information:

```python
@sdk.router.sse("MyModule", "/events")
async def event_stream(request, sse):
    token = request.query_params.get("token")
    if not validate_token(token):
        await sse.close()
        return

    while not sse.closed:
        data = await fetch_data(token)
        await sse.send(data)
        await asyncio.sleep(5)
```

#### SseEmitter API

| Method | Description |
|------|------|
| `sse.send(data, event=None, id=None, retry=None)` | Send an SSE event. Non-str data is automatically serialized to JSON |
| `sse.close()` | Gracefully close the SSE connection (safe to call multiple times) |
| `sse.closed` | Whether the connection is closed |
| `sse.request` | The underlying request object (can be used to read query params, headers) |

#### Using in RouteGroup

```python
api = sdk.router.group("MyModule", "/api", version="1")

@api.sse("/events")
async def events(sse):
    await sse.send({"msg": "hello"})
```

#### Route Discovery

SSE routes are automatically included in route discovery APIs:

```python
# list_namespaces will include the "sse" key
sdk.router.list_namespaces()
# {"MyModule": {"http": [...], "websocket": [...], "sse": ["/MyModule/events"]}}

# get_module_routes will mark streaming: true
sdk.router.get_module_routes("MyModule")
# {"http": [...], "websocket": [...], "sse": [{"path": "/MyModule/events", "streaming": true}]}

# get_module_urls will generate full URLs
sdk.router.get_module_urls("MyModule")
# {"sse": [{"path": "/MyModule/events", "url": "http://localhost:8080/MyModule/events"}]}
```

> **Server-agnostic design**: `SseEmitter` is decoupled from the underlying HTTP framework through callbacks. The framework provides `register_sse()` and the `@sse` decorator as unified registration entry points, allowing adapters to implement SSE endpoints without directly depending on any underlying HTTP framework.



### 适配器核心概念

# Core Concepts of Adapters

Understanding the core concepts of ErisPulse adapters is the foundation for developing adapters.

## Adapter Architecture

### Component Relationships

```
Forward Conversion (Receiving Direction)         Reverse Conversion (Sending Direction)
─────────────────                           ─────────────────

┌──────────────────┐                        ┌──────────────────┐
│ Platform-native Event │                        │ Module-built Message │
└────────┬─────────┘                        └────────┬─────────┘
         │                                           │
         ↓                                           ↓
┌──────────────────┐   ┌──────────────────┐   ┌──────────────────┐
│                  │   │ Adapter (MyAdapter) │   │                  │
│  Converter       │   │ ┌──────────────┐ │   │ Send.Raw_ob12()  │
│  (Event Converter) │──→│ │              │ │   │ (Reverse Conversion Entry) │
│                  │   │ │              │ │   │                  │
└──────────────────┘   │ └──────────────┘ │   └────────┬─────────┘
                       └──────────────────┘            │
                                │                      ↓
                                ↓              ┌──────────────────┐
                       ┌──────────────────┐    │ Platform API Call │
                       │ OneBot12 Standard Event │    └────────┬─────────┘
                       └────────┬─────────┘             │
                                │                      ↓
                                ↓              ┌──────────────────┐
                       ┌──────────────────┐    │ Standard Response Format │
                       │ Event System     │    └──────────────────┘
                       └────────┬─────────┘
                                │
                                ↓
                       ┌──────────────────┐
                       │ Module (Event Handling) │
                       └──────────────────┘
```

**Core Symmetry**:
- **Forward Conversion** (Converter): Platform-native event → OneBot12 standard event, original data preserved in `{platform}_raw`
- **Reverse Conversion** (Raw_ob12): OneBot12 message segment → Platform API call, returns standard response format

## AdapterManager Adapter Manager

The `AdapterManager` is the core component of ErisPulse's adapter system, responsible for managing the registration, startup, shutdown, and event dispatch of all platform adapters.

### Core Features

- **Adapter Registration**: Register and manage multiple platform adapters
- **Lifecycle Management**: Control the startup and shutdown of adapters
- **Event Distribution**: Distribute OneBot12 standard events and platform-native events
- **Configuration Management**: Manage the enabled/disabled status of adapters
- **Middleware Support**: Support OneBot12 event middleware

### Basic Usage

```python
from ErisPulse import sdk

# Register adapter (typically done automatically by Loader)
sdk.adapter.register("myplatform", MyPlatformAdapter)

# Start all adapters
await sdk.adapter.startup()

# Start specified adapters
await sdk.adapter.startup(["myplatform"])
# Start all adapters
await sdk.adapter.startup()

# Get adapter instance
my_adapter = sdk.adapter.get("myplatform")
# Or access via attribute
my_adapter = sdk.adapter.myplatform

# Shutdown all adapters
await sdk.adapter.shutdown()
```

### Startup and Shutdown

#### Start Adapters

```python
# Start all registered adapters
await sdk.adapter.startup()

# Start specific platforms
await sdk.adapter.startup(["platform1", "platform2"])
```

**Startup Process:**

1. Submit the `adapter.start` lifecycle event
2. Submit the `adapter.status.change` event (starting)
3. Start each adapter in parallel
4. If startup fails, automatically retry (using exponential backoff)
5. After successful startup, submit the `adapter.status.change` event (started)

**Retry Mechanism:**

- First 4 retries: 60 seconds, 10 minutes, 30 minutes, 60 minutes
- 5th and subsequent retries: Fixed interval of 3 hours

#### Shutdown Adapters

```python
# Shutdown all adapters
await sdk.adapter.shutdown()
```

**Shutdown Process:**

1. Submit the `adapter.stop` lifecycle event
2. Call the `shutdown()` method of all adapters
3. Shutdown the routing server
4. Clear event handlers
5. Submit the `adapter.stopped` lifecycle event

### Configuration Management

#### Check Platform Status

```python
# Check if platform is registered
exists = sdk.adapter.exists("myplatform")

# Check if platform is enabled
enabled = sdk.adapter.is_enabled("myplatform")

# Use the 'in' operator
if "myplatform" in sdk.adapter:
    print("Platform exists and is enabled")
```

#### List Platforms

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
    print(f"Received message from myplatform: {data}")

# Listen to all events
@sdk.adapter.on("*")
async def handle_any_event(data):
    print(f"Received event: {data.get('type')}")
```

#### Platform-Native Events

```python
# Listen to a specific platform's native event
@sdk.adapter.on("raw_event_type", raw=True, platform="myplatform")
async def handle_raw_event(data):
    print(f"Received native event: {data}")

# Listen to native events from all platforms (wildcard)
@sdk.adapter.on("*", raw=True)
async def handle_all_raw_events(data):
    print(f"Received native event: {data}")
```

#### Event Distribution Mechanism

When calling `adapter.emit(event_data)`:

1. **Middleware Processing**: Execute all OneBot12 middlewares first
2. **Standard Event Distribution**: Distribute to matching OneBot12 event handlers
3. **Native Event Distribution**: If raw data exists, distribute to native event handlers

**Matching Rules:**

- Exact Match: `@sdk.adapter.on("message")` only matches `message` events
- Wildcard: `@sdk.adapter.on("*")` matches all events
- Platform Filtering: `platform="myplatform"` only distributes events from the specified platform

### Middleware

#### Add Middleware

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
        return None  # Returning None skips the middleware chain, preserving original data
    return data  # Must return data to continue passing
```

#### Middleware Execution Order

Middlewares are executed in the order they are registered, with the last registered middleware executed first.

> **Note**: If a middleware returns `None` (e.g., forgetting to `return data`), the framework will ignore the returned value and preserve the original data for continued propagation, while outputting a warning-level log. This ensures that a single middleware failure does not interrupt the entire event chain.

```python
# Registration order
sdk.adapter.middleware(middleware1)  # Last executed
sdk.adapter.middleware(middleware2)  # Middle executed
sdk.adapter.middleware(middleware3)  # First executed

# Execution order: middleware3 -> middleware2 -> middleware1
```

### Get Adapter Instance

#### get() Method

```python
adapter = sdk.adapter.get("myplatform")
if adapter:
    await adapter.Send.To("user", "123").Text("Hello")
```

#### Attribute Access

```python
# Access via attribute name (case-insensitive)
adapter = sdk.adapter.myplatform
await adapter.Send.To("user", "123").Text("Hello")
```

## BaseAdapter Base Class

### Basic Structure

```python
from dataclasses import dataclass, field
from ErisPulse.Core import BaseAdapter
from ErisPulse.Core.Bases import BaseConfig, BotAccountConfig

@dataclass
class MyConfig(BaseConfig):
    """Adapter configuration (automatically managed by the framework after declaration)"""
    token: str = field(
        default="",
        metadata={
            "description": {"i18n": "my_adapter.token", "default": "Bot Token"},
            "required": True,
            "secret": True,
            "ui": {"widget": "password", "group": "basic", "order": 1},
        },
    )

class MyAdapter(BaseAdapter):
    ConfigClass = MyConfig  # Declare configuration class
    
    # No need to override __init__, framework handles automatically:
    # - self.sdk, self.logger
    # - self.cfg (type-safe configuration instance, reads in real-time)
    # - self.Send, self.Request
    
    async def start(self):
        """Start the adapter (must be implemented)"""
        cfg = self.cfg  # Automatically loaded type-safe configuration
        pass
    
    async def shutdown(self):
        """Shutdown the adapter (must be implemented)"""
        pass
    
    async def call_api(self, endpoint: str, **params):
        """Call platform API (must be implemented)"""
        pass
```

### Configuration Management

The framework provides declarative configuration management, defining configuration structures using dataclass, with automatic handling of loading, validation, and template generation.

#### Single Account Configuration

```python
from dataclasses import dataclass, field
from ErisPulse.Core.Bases import BaseConfig

@dataclass
class TelegramConfig(BaseConfig):
    token: str = field(default="", metadata={
        "description": {"i18n": "telegram.token", "default": "Bot Token"},
        "required": True,
        "secret": True,
        "ui": {"widget": "password", "group": "basic", "order": 1},
    })
    proxy: str = field(default="", metadata={
        "description": {"i18n": "telegram.proxy", "default": "Proxy address"},
        "ui": {"widget": "text", "group": "advanced", "order": 10},
    })

class TelegramAdapter(BaseAdapter):
    ConfigClass = TelegramConfig
    
    async def start(self):
        cfg = self.cfg  # Type-safe, reads in real-time
        if not cfg.token:
            raise ValueError("Token not configured")
        await self._connect(cfg.token, proxy=cfg.proxy)
```

#### Multi-account Configuration

The `BotAccountConfig` base class provides `enabled` and `name` fields. Most adapters can automatically obtain `bot_id` from the platform protocol or login response, injecting it into account configurations during event transformation:

```python
from dataclasses import dataclass, field
from ErisPulse.Core.Bases import BotAccountConfig

# Most adapters: bot_id is automatically obtained at runtime, no need to configure
@dataclass
class MyBotConfig(BotAccountConfig):
    token: str = field(default="", metadata={
        "description": {"i18n": "my_adapter.bot_token", "default": "Token"},
        "required": True,
    })

# If bot_id cannot be obtained during login, allow users to fill it in the configuration
@dataclass
class YunhuBotConfig(BotAccountConfig):
    bot_id: str = field(default="", metadata={
        "description": {"i18n": "yunhu.bot_id", "default": "Bot ID"},
        "required": True,
    })
    token: str = field(default="", metadata={
        "description": {"i18n": "yunhu.token", "default": "Token"},
        "required": True,
    })

class MyAdapter(BaseAdapter):
    AccountConfigClass = MyBotConfig
    
    async def start(self):
        for name, account in self.enabled_accounts.items():
            user_id = await self._login(name, account)
            await self.emit_meta("connect", user_id)
```

#### metadata Convention

Field metadata serves both TOML comment generation and WebUI form rendering:

```python
metadata = {
    "description": str | dict,  # Field description (supports i18n)
    "required": bool,         # Whether required (validation + WebUI required indicator)
    "secret": bool,           # Whether sensitive (WebUI displays as ***; logs are masked)
    "ui": {                   # WebUI control configuration (old name "webui" still compatible)
        "widget": str,        # Control type: "text" | "switch" | "select" | "number" | "password"
        "group": str,         # Group: "basic" | "advanced" | "connection" etc.
        "order": int,         # Sort weight (smaller values appear earlier)
        "options": list,      # Select control options [{label, value}], label supports i18n
        "placeholder": str | dict,  # Input placeholder (supports i18n)
    },
    "extra": dict,            # Additional extended fields (passed through to schema)
}
```

All user-visible text fields support i18n, using the unified format `{"i18n": "key", "default": "text"}`; plain strings are passed through as-is (backward compatibility). Supported i18n fields:

| Field | Location | Description |
|------|------|------|
| `description` | Field metadata | Field description |
| `options[].label` | `ui.options` | Select control option label |
| `placeholder` | `ui.placeholder` | Input placeholder |
| `group_labels` | `_schema_meta` | Group display name (Dashboard section title) |

When using i18n, translate keys must be registered in the i18n system beforehand (see [i18n documentation](../../advanced/i18n.md#configuration-field-localization)).

**description / placeholder / options label** example:

```python
token: str = field(
    default="",
    metadata={
        "description": {"i18n": "my_adapter.token", "default": "Bot Token"},
        "ui": {
            "widget": "text",
            "placeholder": {"i18n": "my_adapter.token.ph", "default": "Enter Token"},
        },
    },
)
mode: str = field(
    default="a",
    metadata={
        "description": {"i18n": "my_adapter.mode", "default": "Mode"},
        "ui": {
            "widget": "select",
            "options": [
                {"label": {"i18n": "my_adapter.mode.a", "default": "Option A"}, "value": "a"},
                {"label": "Plain string label", "value": "b"},  # Plain strings are passed through
            ],
        },
    },
)
```

**group_labels** example (declare after configuration class definition):

```python
MyConfig._schema_meta = {
    "group_labels": {
        "basic": {"i18n": "my_adapter.group.basic", "default": "Basic Settings"},
        "advanced": {"i18n": "my_adapter.group.advanced", "default": "Advanced Settings"},
    }
}
```

The framework's `resolve_config_schema()` automatically resolves all i18n keys in the above fields based on the current language; `get_config_schema()` passes through the i18n dictionary as-is, letting the frontend handle the resolution.

### Declarative Translation Keys (v2.7.0+)

Adapters can declare translation keys centrally via the nested `I18nClass`, similar to declaring `ConfigClass`. The framework automatically registers all declared translation keys during `__init__` (before configuration template generation), ensuring that i18n keys referenced in configuration descriptions are available when generating templates.

```python
from ErisPulse.Core.Bases import BaseAdapter, BaseI18n, I18nKey

class MyAdapter(BaseAdapter):
    class I18nClass(BaseI18n):
        endpoint: I18nKey = I18nKey(
            default="API Endpoint",
            zh_CN="API 地址",
            zh_TW="API 位址",
            en="API Endpoint",
            ja="APIアドレス",
            ru="API адрес",
        )
        token: I18nKey = I18nKey(
            default="Platform Token",
            zh_CN="平台 Token",
            zh_TW="平台權杖",
            en="Platform Token",
            ja="プラットフォームトークン",
            ru="Токен платформы",
        )
```

> ``I18nKey.default`` is a **language-agnostic fallback text** and is not registered for any language.
> To make translations effective, at least one language parameter must be explicitly passed.

For detailed usage (key path rules, explicit key parameters, etc.), see [i18n documentation](../../advanced/i18n.md#recommended-usage-declaring-translation-keys-via-i18nclass-v270).

### Declarative Event Extension Methods (v2.7.0+)

Adapters can declare platform-specific event extension methods centrally via `EventMixin`, and the framework automatically registers them to the current platform.

```python
from ErisPulse.Core import BaseAdapter

class MyAdapter(BaseAdapter):
    class EventMixin:
        def get_chat_name(self):
            """Get chat name"""
            return self.get("myplatform_raw", {}).get("chat", {}).get("name", "")

        def is_official_message(self):
            """Check if it is an official message"""
            raw = self.get("myplatform_raw", {})
            return raw.get("sender", {}).get("is_official", False)
```

After registration, these methods can be directly called on event objects:

```python
@message.on_group_message()
async def handler(event):
    if event.is_official_message():
        chat_name = event.get_chat_name()
        await event.reply(f"[{chat_name}] Official message received")
```

> Adapter event extension methods are registered to the adapter's own platform (``self._platform``).
> For modules needing cross-platform event extensions, use the original ``register_event_mixin()`` API.

#### Account Resolution

Multi-account adapters can use `_resolve_account()` to automatically resolve the target account:

```python
async def call_api(self, endpoint: str, **params):
    account_id = params.pop("account_id", None)
    name, account = self._resolve_account(account_id)
    # name: account name, account: configuration instance
```

Resolution strategy: account name match → `bot_id` field match → other str field match → first enabled account.

#### Configuration Hot Reload

Subclasses can override `on_config_update()` to respond to configuration changes:

```python
class MyAdapter(BaseAdapter):
    ConfigClass = MyConfig
    
    def on_config_update(self, old_config, new_config):
        if old_config.token != new_config.token:
            self.logger.info("Token has been updated, reconnecting")
```

### Initialization Process

The framework automatically performs the following tasks in `BaseAdapter.__init__(self, sdk=None)`:

1. **SDK Reference**: Set `self.sdk`, `self.logger`
2. **Send/Request Factory**: Create `self.Send` and `self.Request`
3. **Configuration Template**: If `ConfigClass` is declared, generate a default configuration template (first time only)
4. **Account Template**: If `AccountConfigClass` is declared, generate a default account template (first time only)
5. **EventMixin Registration**: If `EventMixin` is declared, register it automatically in `AdapterManager` after injecting the platform name

Configuration is read in real-time via `self.cfg` / `self.accounts` (each access reads the latest value from the configuration store). `self.config` is a compatible alias for `self.cfg` and can still be used.

Most adapters do not need to override `__init__`. If custom initialization is required:

```python
class MyAdapter(BaseAdapter):
    ConfigClass = MyConfig
    
    def __init__(self, sdk=None):
        super().__init__(sdk)  # Pass sdk
        self.converter = self._setup_converter()
        self.convert = self.converter.convert
```

## Send Message DSL

### Inheritance Relationship

```python
class MyAdapter(BaseAdapter):
    class Send(BaseAdapter.Send):
        """Nested Send class, inherits from BaseAdapter.Send"""
        pass
```

### Available Properties

The `Send` class automatically sets the following properties when called:

| Property | Description | Setting Method |
|-----|------|---------|
| `_target_id` | Target ID | `To(id)` or `To(type, id)` |
| `_target_type` | Target Type | `To(type, id)` |
| `_target_to` | Simplified Target ID | `To(id)` |
| `_account_id` | Sender Account ID | `Using(account_id)` |
| `_adapter` | Adapter Instance | Automatically set |
| `_at_user_ids` | List of @ed Users | `At(user_id)` |
| `_reply_message_id` | ID of the message being replied to | `Reply(message_id)` |
| `_at_all` | Whether to @all | `AtAll()` |

> **Recommendation**: Use the `self.send_context` property to retrieve `target_type`, `target_id`, and `account_id` in one go. It is clearer than directly accessing instance variables.

### Framework Helper Methods

| Method/Property | Description |
|-----------|------|
| `self._apply_modifiers(message)` | Merges At/AtAll/Reply modifier states into the message segment list |
| `self.send_context` | Returns a dictionary containing `{target_type, target_id, account_id}` |

### Basic Methods

Adapters only need to implement `Raw_ob12`. Standard methods (Text/Image/Voice/Video/File) are inherited from the `SendDSL` base class and are delegated to it by default:

```python
class Send(BaseAdapter.Send):
    def Raw_ob12(self, message, **kwargs):
        """Must implement: OneBot12 message segment → platform API"""
        async def _do_send():
            segments = self._apply_modifiers(message)
            return await self._adapter.call_api(
                endpoint="/send_message",
                message=segments,
                **self.send_context,
                **kwargs
            )
        return asyncio.create_task(_do_send())

    # Text/Image/Voice/Video/File are inherited from the base class and automatically delegate to Raw_ob12, no need to implement them again
    # If platform-specific logic is needed, individual methods can be overridden:
    # def Text(self, text: str):
    #     return self.Raw_ob12([{"type": "text", "data": {"text": text}}])
```

### Chainable Modifier Methods

```python
class Send(BaseAdapter.Send):

    def __init__(self, adapter, target_type=None, target_id=None, account_id=None):
        super().__init__(adapter, target_type, target_id, account_id)
        self.buttons = []

    def Button(self, content: list) -> 'Send':
        self.buttons.append(content)
        return self
```

## Event Converters

### Conversion Flow

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
    "id": "Unique event identifier",
    "time": 1234567890,           # 10-digit Unix timestamp
    "type": "message/notice/request/meta",
    "detail_type": "Event detail type",
    "platform": "Platform name",
    "self": {
        "platform": "Platform name",
        "user_id": "Bot ID"     # Must match bot_id
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
class MyAdapter(BaseAdapter):
    async def start(self):
        """Register WebSocket route"""
        router.register_websocket(
            module_name="myplatform",
            path="/ws",
            handler=self._ws_handler,
            auth_handler=self._auth_handler
        )
    
    async def _ws_handler(self, websocket):
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
    
    async def _auth_handler(self, websocket) -> bool:
        """WebSocket authentication"""
        token = websocket.query_params.get("token")
        return token == "valid_token"
```

### WebHook Connection

```python
class MyAdapter(BaseAdapter):
    async def start(self):
        """Register WebHook route"""
        router.register_http_route(
            module_name="myplatform",
            path="/webhook",
            handler=self._webhook_handler,
            methods=["POST"]
        )
    
    async def _webhook_handler(self, request):
        """WebHook request handler"""
        data = await request.json()
        onebot_event = self.convert(data)
        if onebot_event:
            await self.adapter.emit(onebot_event)
        return {"status": "ok"}
```

> **Route Information Query**: The routes registered by the adapter (HTTP, WebSocket, SSE) can be queried using `sdk.adapter.get_connection_info(platform)` and `sdk.router.get_module_urls(module_name)` to retrieve the full connection address (including `base_url` + path). See [Getting Started - Adapter Development - Connection Information and Route Discovery](docs/en/getting-started.md#9-connection-information-and-route-discovery) and [SSE Support](docs/en/getting-started.md#10-sse-server-sent-events-support).

## API Response Standard

The framework provides `make_response()` and `make_error()` methods to construct standardized responses, eliminating the need to manually build response dictionaries.

### Success Response

```python
async def call_api(self, endpoint: str, **params):
    try:
        raw_response = await self._platform_api_call(endpoint, **params)
        
        return self.make_response(
            data=raw_response.get("data"),
            message_id=raw_response.get("data", {}).get("message_id", ""),
            raw=raw_response,
        )
    except Exception as e:
        return self.make_error(message=str(e), raw=None)
```

### Manually Constructing Responses (Legacy approach still compatible)

```python
async def call_api(self, endpoint: str, **params):
    return {
        "status": "ok",
        "retcode": 0,
        "data": {...},
        "message_id": "msg_id",
        "message": "",
        "myplatform_raw": raw_response
    }
```

## Multi-Account Support

### Declarative Configuration (Recommended)

After declaring the `AccountConfigClass`, the framework automatically manages multi-account loading, validation, and template generation:

```python
from dataclasses import dataclass, field
from ErisPulse.Core.Bases import BotAccountConfig

@dataclass
class MyBotConfig(BotAccountConfig):
    bot_id: str = field(default="", metadata={"description": "Bot ID", "required": True})
    token: str = field(default="", metadata={"description": "Token", "required": True, "secret": True})

class MyAdapter(BaseAdapter):
    AccountConfigClass = MyBotConfig
    
    async def start(self):
        for name, account in self.enabled_accounts.items():
            self.logger.info(f"Starting account {name}: {account.bot_id}")
            await self._connect(name, account)
    
    async def call_api(self, endpoint: str, **params):
        account_id = params.pop("account_id", None)
        name, account = self._resolve_account(account_id)
        # Use fields such as account.token, account.bot_id, etc.
```

### Account Configuration Files

```toml
[MyAdapter.accounts.account1]
bot_id = "bot_001"
token = "token1"
enabled = true

[MyAdapter.accounts.account2]
bot_id = "bot_002"
token = "token2"
enabled = true
```

### Specifying Accounts for Sending

```python
# Use the Using method to specify an account
my_adapter = adapter.get("myplatform")

# Using self.user_id from the event (recommended, most universal)
await my_adapter.Send.Using(event["self"]["user_id"]).To("user", "123").Text("Hello")

# Using the account name
await my_adapter.Send.Using("account1").To("user", "123").Text("Hello")
```

### Relationship Between self.user_id and Using

The framework's event reply mechanism automatically extracts `account_id` (preferred) or `user_id` from the event's `self` field and passes it as the `Using` parameter. Adapter developers need to ensure that `self.user_id` in the Converter correctly matches `_resolve_account()`.

**Framework Internal Behavior**:

```python
# Framework logic for extracting bot_id
bot_id = self.get("self", {}).get("account_id", "") or self.get("self", {}).get("user_id", "")

# Only call Using if bot_id is non-empty
if bot_id:
    send_chain = send_chain.Using(bot_id)
```

> **Key Point**: Even if an adapter uses only one Bot configuration, as long as the Converter correctly sets `self.user_id`, the framework will pass it as the `Using` parameter. The adapter must ensure that `self.user_id` matches the identifier field (such as `bot_id`) in `AccountConfigClass`, so that `_resolve_account()` can match the correct account. If `self.user_id` is empty, the framework will not call `Using`, and in this case `call_api` receives `account_id` as `None`, and `_resolve_account(None)` returns the first enabled account.

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
        # It is recommended to use the built-in client in the SDK
        from ErisPulse.Core import client
        from ErisPulse.Core.Bases.errors import ClientError, ClientTimeoutError
        resp = await client.post(
            f"https://api.platform.com/{endpoint}",
            json=params,
            max_retries=2,
        )
        response = await resp.json()
        return self._standardize_response(response)
    except ClientTimeoutError:
        self.logger.error(f"Request timed out: {endpoint}")
        return self._error_response("Request timed out", 32000)
    except ClientError as e:
        self.logger.error(f"Network error: {e}")
        return self._error_response("Network request failed", 33000)
    except Exception as e:
        self.logger.error(f"Unknown error: {e}")
        return self._error_response(str(e), 34000)
```

> **Backward Compatibility**: Old adapter code that directly uses `aiohttp.ClientSession` is unaffected and can still catch `aiohttp.ClientError`. Both approaches can coexist. It is recommended that new code use `sdk.client` with the ErisPulse exception system.

## Bot Status Management

AdapterManager includes a built-in Bot status tracking system, automatically maintaining the online status, active time, and metadata for all registered Bots.

### Automatic Discovery Mechanism

When an adapter sends an event via `adapter.emit()`, the framework automatically checks the `self` field in the event:

- **Meta Events**: Perform corresponding actions based on `detail_type` (register on connect / mark offline on disconnect / update active time on heartbeat)
- **Regular Events** (message/notice/request): Automatically discover Bots and update active time

```python
# All events containing the self field trigger automatic discovery
await self.adapter.emit({
    "type": "message",
    "platform": "myplatform",
    "self": {"platform": "myplatform", "user_id": "bot123"},
    # ...
})
# Bot "bot123" is automatically registered (if first appearance) and active time is updated
```

### Meta Event Types

| `detail_type` | Description | Framework Behavior |
|---|---|---|
| `connect` | Bot connects | Register Bot and trigger the `adapter.bot.online` lifecycle event |
| `disconnect` | Bot disconnects | Mark Bot as offline and trigger the `adapter.bot.offline` lifecycle event |
| `heartbeat` | Bot heartbeat | Update Bot active time and metadata |

### Adapter Sending Meta Events

Use `emit_meta()` to send meta events in one line:

```python
class MyAdapter(BaseAdapter):
    async def _on_bot_connect(self, bot_id: str):
        # Send connect event in one line
        await self.emit_meta("connect", bot_id, user_name="MyBot", nickname="MyBot")

    async def _on_bot_disconnect(self, bot_id: str):
        await self.emit_meta("disconnect", bot_id)
```

Manual construction is also supported (old method is still compatible):

```python
await self.adapter.emit({
    "type": "meta",
    "detail_type": "connect",
    "platform": "myplatform",
    "self": {"platform": "myplatform", "user_id": bot_id}
})
```

### Extended Information in the `self` Field

The `self` field supports the following optional fields in addition to the required `platform` and `user_id`:

| Field | Description |
|---|---|
| `user_name` | Bot username |
| `nickname` | Bot nickname |
| `avatar` | Bot avatar URL |
| `account_id` | Multi-account identifier |

### Bot Status Query

```python
from ErisPulse import sdk

# Get information for a single Bot
info = sdk.adapter.get_bot_info("myplatform", "bot123")
# {"status": "online", "last_active": 1712345678.0, "info": {"nickname": "MyBot"}}

# List all Bots
all_bots = sdk.adapter.list_bots()

# List Bots for a specific platform
platform_bots = sdk.adapter.list_bots("myplatform")

# Check if a Bot is online
is_online = sdk.adapter.is_bot_online("myplatform", "bot123")

# Get a complete status summary (suitable for WebUI display)
summary = sdk.adapter.get_status_summary()
# {"adapters": {"myplatform": {"status": "started", "bots": {...}}}}
```

### Listening to Bot Lifecycle Events

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



### SendDSL 详解

# SendDSL Explained

SendDSL is a fluent interface for message sending provided by the ErisPulse adapter.

## Basic Call Methods

### 1. Specify Type and ID

```python
await adapter.Send.To("group", "123").Text("Hello")
```

### 2. Specify Only ID

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

## Method Chaining

```mermaid
flowchart LR
    A["Using / Account<br/>（选发送账号，可选）"] --> B["To<br/>（选目标类型与 ID）"]
    B --> C["修饰方法<br/>At / Reply / Expire / ForMember 等"]
    C --> D["发送方法<br/>Text / Image / Voice / Raw_ob12"]
    D --> E["返回 asyncio.Task"]
```

## Sending Methods

All sending methods return an `asyncio.Task` object.

### Basic Methods (Built-in by Base Class)

The following standard methods are implemented by the `SendDSL` base class and are **defaulted to `Raw_ob12`**. Adapter subclasses do not need to re-implement them to use them directly, and IDE can complete them:

| Method Name | Description | Return Value |
|-------------|-------------|--------------|
| `Text(text: str)` | Send text message | `asyncio.Task` |
| `Image(file: bytes \| str)` | Send image | `asyncio.Task` |
| `Voice(file: bytes \| str)` | Send voice (OneBot12 `audio` segment) | `asyncio.Task` |
| `Video(file: bytes \| str)` | Send video | `asyncio.Task` |
| `File(file: bytes \| str, filename: str = None)` | Send file | `asyncio.Task` |

Adapters can override individual standard methods to provide platform-specific logic:

```python
class Send(SendDSL):
    def Raw_ob12(self, message, **kwargs):
        # Must implement
        ...

    # Optional: Override Text to provide platform-specific logic
    # def Text(self, text: str):
    #     return self.Raw_ob12([{"type": "text", "data": {"text": text}}])
```

### Protocol Methods

| Method Name | Description | Return Value | Required |
|-------------|-------------|--------------|----------|
| `Raw_ob12(message)` | Send OneBot12 formatted message | `asyncio.Task` | **Must implement** |

> **Important**: `Raw_ob12` is the core method of the adapter and **must be implemented**. It is the unified entry point for reverse conversion (OneBot12 → platform). If not implemented, the base class will log an error and return a standard error response (`status: "failed"`, `retcode: 10002`). Standard methods (`Text`, `Image`, etc.) default to `Raw_ob12`.

### Platform-Specific Methods

Adapters can add platform-specific sending methods in the `Send` subclass (will be recognized by `event.supports()` / `event.available_methods()`):

```python
class Send(SendDSL):
    def Raw_ob12(self, message, **kwargs): ...

    # Platform-specific method
    def Sticker(self, sticker_id: str):
        return self.Raw_ob12([{"type": "sticker", "data": {"id": sticker_id}}])
```

## Modifier Methods

Modifier methods return `self` to support method chaining.

### At Method

```python
# @single user
await adapter.Send.To("group", "123").At("456").Text("你好")

# @multiple users
await adapter.Send.To("group", "123").At("456").At("789").Text("你们好")
```

### AtAll Method

```python
# @all members
await adapter.Send.To("group", "123").AtAll().Text("大家好")
```

### Reply Method

```python
# Reply to message
await adapter.Send.To("group", "123").Reply("msg_id").Text("回复内容")
```

### Combined Modifiers

```python
await adapter.Send.To("group", "123").At("456").Reply("msg_id").Text("回复@的消息")
```

### Platform-Specific Modifier Methods

In addition to the built-in `At`/`AtAll`/`Reply`, adapters can define **platform-specific modifier methods**. These methods only need to return `self`—no decorators are required—the framework will automatically recognize them:

- Return `self` (SendDSL instance) → Modifier method, does not trigger sending wrapper/lifecycle events, continues chaining
- Return `Task`/`Awaitable` → Sending method

```python
class Send(SendDSL):
    def Raw_ob12(self, message, **kwargs): ...

    # Modifier method: return self, no sending
    def Expire(self, seconds: int):
        self._expire = seconds
        return self

    def ForMember(self, user_id: str):
        self._member = user_id
        return self

    # Sending method: return Task, depends on modifier method settings
    def Board(self, content: str, **kwargs):
        return self.Raw_ob12([{"type": "board", "data": {"text": content}}])
```

Usage:

```python
# Modifier methods can be chained continuously
await adapter.Send.To("group", "big").Expire(3600).ForMember("114").Board("看板内容")
```

## Using Modifier Methods in Event Wrapper Class

> [!NOTE]
> `reply(via=)` and `event.send_chain()` require ErisPulse **2.7.0+**.

`event.reply()` by default only exposes built-in modifier parameters like `at_sender`/`at_users`/`at_all`/`quote`. To use platform-specific modifier methods, there are two ways:

### Method 1: reply() via Parameter

Suitable for a small number of known modifier methods:

```python
await event.reply("看板内容", method="Board",
                  via=[("Expire", 3600), ("ForMember", "114514")])
```

`via` is a list, each element can be:

| Form | Equivalent Chain Call |
|------|-----------------------|
| `"Name"` | `.Name()` |
| `("Name", arg1, arg2)` | `.Name(arg1, arg2)` |
| `("Name", (arg1,), {kw: val})` | `.Name(arg1, kw=val)` |

### Method 2: event.send_chain()

Suitable for **multiple consecutive modifier methods** or **action-type methods without content parameters** (such as recall, delete). `send_chain()` returns a send chain configured with `To`/`Using`, which can freely append any modifier methods and sending methods:

```python
# Platform-specific modifier methods + board sending
await event.send_chain().Expire(3600).Board("一小时后过期")

# Multiple consecutive modifier methods
await (event.send_chain()
       .Expire(3600)
       .ForMember("114514")
       .Board("看板内容", content_type="markdown"))

# Built-in modifier methods are also available
await event.send_chain().At("123").Reply("msg_id").Text("hi")

# Action-type methods without content parameters
await event.send_chain().DismissBoard()
```

> `send_chain()` returns a complete SendDSL instance, so **all chaining features are available**—not just modifier methods, but also sending rules and batch building:

```python
# Sending rules: retry + timeout + success callback
await (event.send_chain()
       .Retry(3).Timeout(10)
       .Hook(lambda r: print("发送成功"))
       .Text("可靠发送"))

# Delayed sending + platform modifier + board
await event.send_chain().Defer(5).Expire(3600).Board("延迟看板")

# Batch building mode
results = await (event.send_chain()
                 .Build()
                 .Text("第一句").Image("pic.jpg").Text("第二句")
                 .send_all())
```

## Account Management

### Using Method

`Using()` is used to specify the account for sending messages. The identifier passed in will be matched through `_resolve_account()` in the following priority:

1. **Account name** — the key name in the configuration (e.g., `"default"`, `"bot1"`)
2. **Runtime injected bot_id** — the identifier automatically injected from the event conversion
3. **Any str field** — other string fields in the configuration
4. **Fallback** — the first enabled account

```python
# Using account name
await adapter.Send.Using("account1").To("user", "123").Text("Hello")

# Using bot_id (i.e., self.user_id in the event)
await adapter.Send.Using("bot_123").To("user", "123").Text("Hello")
```

### Account Method

`Account` method is equivalent to `Using`:

```python
await adapter.Send.Account("account1").To("user", "123").Text("Hello")
```

## Asynchronous Handling

### Do Not Wait for Result

```python
# Message is sent in the background
task = adapter.Send.To("user", "123").Text("Hello")

# Continue executing other operations
# ...
```

### Wait for Result

```python
# Directly await to get the result
result = await adapter.Send.To("user", "123").Text("Hello")
print(f"发送结果: {result}")

# Save Task first, then wait later
task = adapter.Send.To("user", "123").Text("Hello")
# ... other operations ...
result = await task
```

## Sending Rule System

SendDSL includes a built-in set of sending rule decorators, which are attached as rules through method chaining and applied uniformly at the final sending. The rules cover common production scenarios: timeout control, failure retry, success callback, delayed sending, priority dropping, and progress monitoring.

Rule methods **return self** (same as At/AtAll/Reply), and must be called before the sending method (Text/Image, etc.). Rules propagate with new instances created by `To`/`Using`/`Account`.

### Rule Methods Overview

| Method | Description |
|--------|-------------|
| `.Hook(callback)` | Callback executed after successful sending (can be called multiple times, executed in order) |
| `.Retry(times=1)` | Automatic retry N times on failure (including the first attempt, total N+1 attempts) |
| `.Timeout(seconds)` | Single sending timeout, cancel current attempt if timeout (can be stacked with Retry) |
| `.Defer(seconds=1.0)` | Delayed sending (in-process timing, not persistent) |
| `.Priority(level, drop_if_busy=False)` | Set priority; can drop on backlog |
| `.OnProgress(callback)` | Progress callback at each stage (passing `SendContext`) |
| `.OnError(callback)` | Error callback on final failure (only triggered once) |

### Execute Logic After Sending Success (Hook)

```python
# Synchronous callback
await (adapter.Send.To("user", "123")
       .Hook(lambda r: print(f"发送成功，消息ID: {r['message_id']}"))
       .Text("你好"))

# Asynchronous callback
async def deduct_points(result):
    await db.update(user_id="123", points=-1)

await adapter.Send.To("user", "123").Hook(deduct_points).Text("扣积分")
```

Hook is only triggered when sending is finally successful (including retry success); failure, timeout, and cancellation do not trigger it.

### Automatic Retry on Failure (Retry)

```python
# Retry 2 times after the first failure, for a total of 3 attempts
result = await adapter.Send.To("user", "123").Retry(2).Text("带重试")
```

Retry is triggered when sending throws an exception, times out, or returns a response with `status == "failed"`.

### Automatic Cancellation on Timeout (Timeout)

```python
# Cancel if a single sending exceeds 10 seconds
await adapter.Send.To("user", "123").Timeout(10).Text("带超时")

# Timeout + Retry: 10 seconds per attempt, up to 3 attempts
await adapter.Send.To("user", "123").Timeout(10).Retry(2).Text("超时重试")
```

### Progress Monitoring (OnProgress / OnError)

```python
def on_progress(ctx):
    print(f"阶段: {ctx.stage}, 尝试: {ctx.attempt + 1}/{ctx.max_attempts}, 耗时: {ctx.elapsed:.2f}s")
    if ctx.stage == "failed":
        print(f"  错误: {ctx.error!r}")

async def on_error(ctx):
    await notify_admin(f"发送给 {ctx.target_id} 失败: {ctx.error!r}")

await (adapter.Send.To("user", "123")
       .Retry(3).Timeout(10)
       .OnProgress(on_progress)
       .OnError(on_error)
       .Text("监控"))
```

`SendContext` includes the following fields: `task_id`, `platform`, `method`, `target_type`, `target_id`, `bot_id`, `stage`, `attempt`, `max_attempts`, `started_at`, `finished_at`, `elapsed`, `error`, `result`, `extra`.

`stage` possible values: `pending`, `sending`, `retrying`, `success`, `failed`, `timeout`, `cancelled`, `dropped`.

### Delayed Sending (Defer)

```python
# Send after 5 seconds
await adapter.Send.To("user", "123").Defer(5).Text("迟到消息")
```

> Note: Delay is in-process timing, and will be lost if the process restarts; no persistence is provided.

### Priority and Backlog Dropping (Priority)

```python
# Low priority message, automatically dropped if queue is backed up
result = await (adapter.Send.To("user", "123")
               .Priority(-1, drop_if_busy=True)
               .Text("可放弃的通知"))
# If dropped, result["status"] == "failed"
```

Enabling `drop_if_busy` will directly abandon the current sending if the number of in-flight sending tasks exceeds the threshold (default 64). The global threshold can be adjusted via `.PriorityThreshold(n)`.

### Rule Combination and Background Execution

```python
# Do not block the main process, rules still take effect
task = (adapter.Send.To("user", "123")
        .Hook(lambda r: print("发送成功！"))
        .Retry(3)
        .Timeout(10)
        .OnProgress(on_progress)
        .Text("你好"))

# Continue executing other operations
await handle_next_action()
```

### Rule Propagation

Rules propagate with new instances created by `To`/`Using`/`Account`, avoiding loss of rules in chained calls:

```python
# Rules set before To are also propagated to the instance created by To
builder = adapter.Send.Retry(3).Timeout(10)
send = builder.To("user", "123")  # send still carries Retry(3) and Timeout(10)
await send.Text("hi")
```

Multiple instances have independent rules (hooks list is deep-copied).

## Batch Build Mode (Build)

In addition to single-send mode, SendDSL also supports batch build mode: multiple sending methods are written in a single chain, and executed together at the end. This is suitable for scenarios where "a batch of messages is sent at once."

### Entering Build Mode

Call `.Build()` before the sending method, returning a `SendBuilder`. After this, sending methods (Text/Image, etc.) no longer execute immediately but accumulate as sending intentions:

```python
results = await (adapter.Send.To("user", "123")
                 .Build()                    # Enter build mode
                 .Text("第一句")
                 .Image("pic.jpg")
                 .Text("第二句")
                 .send_all())                 # Execute together
# results = [Text result, Image result, Text result]
```

`.send_all()` returns an `asyncio.Task`, and `await`ing it gives the result list (in the order of intentions).

### Parallel vs. Sequential

By default, it executes **in parallel** (concurrent sending, total time approximately equal to the slowest one). When the order of message arrival needs to be guaranteed, call `.Sequential()`:

```python
# Sequential: send in order
await (adapter.Send.To("group", "456")
       .Build()
       .Sequential()
       .Text("先发这个").Text("再发这个")
       .send_all())

# Parallel (default, can be explicitly called)
await (adapter.Send.To("group", "456")
       .Build()
       .Parallel()
       .Text("并发1").Text("并发2")
       .send_all())
```

### Continue on Failure and Retry

Batch execution uses a **continue on failure** strategy: if one fails, it does not interrupt the sending of others. When combined with `.Retry()`, failed items will automatically retry (retry applies to individual items, not the entire batch):

```python
await (adapter.Send.To("user", "123")
       .Build()
       .Retry(2)                       # Each item retries 2 times
       .Text("可能失败的").Image("也可能失败的")
       .send_all())
```

### Batch Rules and Callbacks

Rules uniformly apply to the entire batch:

| Method | Description |
|--------|-------------|
| `.Timeout(seconds)` | Single timeout for each sending |
| `.Retry(times)` | Each sending retries individually (continue on failure) |
| `.Defer(seconds)` | Delay the entire batch's sending |
| `.Hook(callback)` | Triggered after the entire batch succeeds, receives the `results` list |
| `.OnError(callback)` | Triggered if the batch has failures, receives the `BatchContext` |
| `.OnProgress(callback)` | Triggered for each completion, receives the `BatchContext` |

```python
def on_progress(ctx):
    print(f"进度: {ctx.completed}/{ctx.total}, 成功 {ctx.succeeded}, 失败 {ctx.failed}")

async def on_error(ctx):
    print(f"批次有 {ctx.failed} 条失败")

results = await (adapter.Send.To("user", "123")
               .Build()
               .Retry(2).Timeout(10)
               .OnProgress(on_progress)
               .OnError(on_error)
               .Hook(lambda rs: print("整批完成"))
               .Text("a").Text("b").Text("c")
               .send_all())
```

`BatchContext` includes: `task_id`, `total`, `completed`, `succeeded`, `failed`, `stage`, `results`, `errors`, `elapsed`, `extra`.

`stage` possible values: `pending`, `sending`, `success` (all succeeded), `partial` (partially succeeded), `failed` (all failed).

### Modifier and Rule Inheritance

Modifier methods and rules before `.Build()` are inherited to the entire batch, affecting each message:

```python
await (adapter.Send.To("group", "456")
       .At("789")                        # Inherited: each message @789
       .Build()
       .Retry(2)                         # Inherited + appended: each item retries
       .Text("@你的通知")
       .Image("公告图")
       .send_all())
```

After entering Build, you can still append modifiers (affecting the entire batch):

```python
await (adapter.Send.To("group", "456")
       .Build()
       .At("111").At("222")             # Append @, affects the entire batch
       .Text("@多人")
       .send_all())
```

### Background Execution

Like single-send, `.send_all()` returns a Task, which can be executed in the background without awaiting:

```python
task = (adapter.Send.To("user", "123")
        .Build()
        .Hook(lambda rs: print("批量发送完成"))
        .Text("a").Text("b")
        .send_all())

# Do not block the main process
await do_something_else()
```

## Naming Conventions

### PascalCase Naming

All sending methods use PascalCase naming:

```python
# ✅ Correct
def Text(self, text: str):
    pass

def Image(self, file: bytes):
    pass

# ❌ Incorrect
def text(self, text: str):
    pass

def send_image(self, file: bytes):
    pass
```

### Platform-Specific Methods

Platform prefix methods are not recommended:

```python
# ✅ Recommended
def Sticker(self, sticker_id: str):
    pass

# ❌ Not recommended
def TelegramSticker(self, sticker_id: str):
    pass
```

Use `Raw` methods instead:

```python
# ✅ Recommended
await adapter.Send.Raw_ob12([{"type": "sticker", ...}])

# ❌ Not recommended
def TelegramSticker(self, ...):
    pass
```

## Internal Breakdown of the Sending Chain

Behind a single `await adapter.Send.To("group", "123").Text("x")`, the framework helps you complete the following series of tasks:

```mermaid
flowchart TD
    A["adapter.Send.To(...).Text(...)"] --> B["To/Using chain methods<br/>Each returns an immutable new instance (order irrelevant)"]
    B --> C["__getattribute__ intercepts sending methods<br/>Wrap with a rule wrapper"]
    C --> D["Call the original method (e.g., Text)<br/>Internally delegates to Raw_ob12"]
    D --> E["Raw_ob12 returns asyncio.create_task(...)"]
    E --> F["Write [Send] log"]
    F --> G["emit message.sending (fire-and-forget)"]
    G --> H{"Declared sending rules?"}
    H -->|"No"| I["Task done_callback → emit message.sent"]
    H -->|"Yes"| J["apply_send_rules wraps into an outer Task<br/>Retry/timeout/delay/priority"]
    J --> I
    I --> K["await gets standard response dict"]
```

**What the framework does at each step:**

| Stage | What the framework does |
|------|-------------|
| Chain merging | `To`/`Using`/`Account` each call creates a new immutable instance and inherits set fields, so `To(...).Using(...)` and `Using(...).To(...)` are **equivalent**, order irrelevant |
| Method wrapping | Sending methods (`Text`, etc.) are intercepted by `__getattribute__` and wrapped; modifier methods (`To`/`Using`/`At`/`Retry`, etc.) are **not wrapped**. Nested `Raw_ob12` calls rely on `_in_rule_wrap` marking to prevent repeated wrapping |
| Task creation | `Raw_ob12` internally uses `asyncio.create_task()` to create the Task; `Text()` only synchronously returns this Task, **does not block** |
| Sending log | Write `[Send] platform/method -> target` event log (use `exclude_levels=["EVENT"]` to suppress) |
| `message.sending` | The sending method is called **immediately** to trigger (only if there are listeners, short-circuited by `has_handlers`) |
| `message.sent` | Bound to the Task's `done_callback`—**applies to the final result of the retry process when rules are present**, otherwise it is the original Task completion |

### Account Resolution Fallback Chain

When the adapter internally calls `_resolve_account(account_id)`, it resolves to a specific account in the following order:

1. Single-account adapter (no `AccountConfigClass`) → directly return
2. Account name exact match `account_id`
3. Each account's `bot_id` field matches
4. Each account's any `str` field value matches (excluding `enabled`/`name`)
5. Fallback to the first enabled account
6. All fail → raise `ValueError`

> The `account_id` you pass comes from: `Using()` explicitly specified > `event`'s `self` field (`account_id` takes precedence over `user_id`, automatically injected by `event.reply()`) > not specified (adapter defaults to the first enabled account).

### Sending Rule Engine (Retry/Timeout/Delay)

Rules are wrapped into a new outer Task after `Raw_ob12` returns the Task, without affecting the main process. Key facts:

| Rule | Description |
|------|------|
| `Retry(n)` | Total attempts `n+1`; **immediate retry on failure, no exponential backoff** |
| `Timeout(s)` | Single sending timeout cancels (using `asyncio.wait_for`), retries if not exhausted |
| `Defer(s)` | Delay sending before execution (in-process timing, not persistent) |
| `Priority(level, drop_if_busy)` | Returns `{status:"failed", retcode:10002, message:"dropped_low_priority"}` if backlog exceeds threshold |
| `Hook(fn)` | Only executed in order on final success |
| `on_progress` / `on_error` | Stage / final failure callbacks |

> **Note**: Retry is "immediate retry," with no backoff interval; if platform rate limiting requires backoff, manually sleep and retry within the `on_error` callback. Rule success is determined by the response dict's `status == "ok"` (retcode == 0).

> Standard response format and retcode semantic completeness can be found in [API Response Specification](../../standards/api-response.md).

## Return Values

### Task Object

All sending methods return an `asyncio.Task`. The adapter only needs to implement `Raw_ob12`, and standard methods (Text/Image, etc.) default to delegating to it:

```python
import asyncio

def Raw_ob12(self, message, **kwargs):
    async def _do_send():
        segments = self._apply_modifiers(message)
        return await self._adapter.call_api(
            endpoint="/send_message",
            message=segments,
            **self.send_context,
            **kwargs,
        )
    return asyncio.create_task(_do_send())

# Text/Image/Voice/Video/File are inherited from the base class, automatically delegated to Raw_ob12
# If you need to override standard methods, return asyncio.Task:
# def Text(self, text: str):
#     return self.Raw_ob12([{"type": "text", "data": {"text": text}}])
```

### Standardized Response

`call_api` should return a standardized response. It is recommended to use `make_response()` / `make_error()` methods:

```python
async def call_api(self, endpoint: str, **params):
    try:
        result = await self._do_api_call(endpoint, **params)
        return self.make_response(
            data=result.get("data"),
            message_id=result.get("message_id", ""),
            raw=result,
        )
    except Exception as e:
        return self.make_error(message=str(e))
```

Manual construction is also supported (old-style compatibility is still maintained):

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

## Complete Example

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

### Method Chaining

```python
# @user + reply
await my_adapter.Send.To("group", "456").At("789").Reply("msg123").Text("回复@的消息")

# @all + multiple modifiers
await my_adapter.Send.Using("bot1").To("group", "456").AtAll().Text("公告消息")
```

### Raw Message and Message Building

`Raw_ob12` is the core entry point for reverse conversion (OneBot12 message segments → platform API call), and `MessageBuilder` is a chainable message segment builder tool that works with it.

> For the complete `Raw_ob12` implementation specification and `MessageBuilder` usage and code examples, see:
> - [Sending Method Specification §6 Reverse Conversion Specification](../../standards/send-method-spec.md#6-反向转换规范onebot12--平台)
> - [Sending Method Specification §11 Message Builder](../../standards/send-method-spec.md#11-消息构建器-messagebuilder)



### 适配器开发最佳实践

# Adapter Development Best Practices

This document provides best practices for ErisPulse adapter development.

## Bot Status Management and Meta Events

Adapters should actively send meta events via `adapter.emit()` to allow the framework to automatically track the Bot's connection status, online/offline events, and heartbeat information.

### 1. When to Send Meta Events

| Event | `detail_type` | Trigger Timing | Framework Behavior |
|------|--------------|---------|---------|
| Connect | `"connect"` | When the Bot establishes a connection with the platform | Register the Bot, trigger the `adapter.bot.online` lifecycle event |
| Disconnect | `"disconnect"` | When the Bot disconnects from the platform | Mark the Bot as offline, trigger the `adapter.bot.offline` lifecycle event |
| Heartbeat | `"heartbeat"` | Regularly (recommended: 30-60 seconds) | Update the Bot's active time and metadata |

### 2. Sending Meta Events

The framework provides the `emit_meta()` method, allowing you to send meta events in a single line:

```python
class MyAdapter(BaseAdapter):
    async def _ws_handler(self, websocket):
        bot_id = self._get_bot_id()

        # Bot online: send connect event in one line
        await self.emit_meta("connect", bot_id, user_name="MyBot", nickname="MyBot")

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

### 3. Heartbeat Event

Adapters should regularly send heartbeat events during the connection's active period to update the Bot's active time:

```python
class MyAdapter(BaseAdapter):
    async def _heartbeat_loop(self, bot_id: str):
        while self._connected:
            # Send meta heartbeat to the framework (done in one line)
            await self.emit_meta("heartbeat", bot_id)
            await asyncio.sleep(30)
```

### 4. `self` Field Auto-detection

The framework's `adapter.emit()` automatically processes all events (not just meta events) containing the `self` field:

- **Regular events** (`message/notice/request`) with the `self` field will be automatically detected and register the Bot
- **Extended `self` field information**: Supports optional fields `user_name`, `nickname`, `avatar`, `account_id`

```python
# Converter with self field will auto-register the Bot
onebot_event = {
    "type": "message",
    "detail_type": "private",
    "platform": "myplatform",
    "self": {
        "platform": "myplatform",
        "user_id": "bot123",
        "user_name": "MyBot",
        "nickname": "MyBot",
    },
    # ... other fields
}
await self.adapter.emit(onebot_event)
# Bot "bot123" is automatically registered and active time is updated
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

# Check if a Bot is online
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
                    self.logger.error("Connection failed, maximum retry count reached")
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
            self.logger.info("Connection disconnected")
        finally:
            self.connection = None
            self._connected = False
```

### 3. Heartbeat Keepalive and Meta Heartbeat

Adapter heartbeats should simultaneously perform two tasks: sending a heartbeat to the platform for keepalive and sending a meta heartbeat event to the framework.

```python
class MyAdapter(BaseAdapter):
    async def start(self):
        self.connection = await self._connect_to_platform()
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())

    async def _heartbeat_loop(self):
        while self.connection:
            try:
                # 1. Send heartbeat to the platform for keepalive
                await self.connection.send_json({"type": "ping"})

                # 2. Send meta heartbeat to the framework (done in one line)
                await self.emit_meta("heartbeat", self._bot_id)

                await asyncio.sleep(30)
            except Exception as e:
                self.logger.error(f"Heartbeat failed: {e}")
                break
```

### 4. Connection Information Exposure

The routes registered by the adapter should be visible to users for configuring the platform-side callback address. It is recommended to actively output connection information in `start()`:

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
                self.logger.info(f"WebSocket address: "
                    f"{info.get('connection', {}).get('base_url', '')}"
                    f"{info.get('connection', {}).get('websocket_routes', [])}")
```

Users can query adapter routes and connection addresses through the following APIs:

```python
from ErisPulse import sdk

# Adapter-level connection information (recommended)
info = sdk.adapter.get_connection_info("myplatform")

# Query through the router manager
sdk.router.list_namespaces()              # List all namespaces
sdk.router.get_module_routes("myplatform")  # Detailed route information
sdk.router.get_module_urls("myplatform")    # Complete connection URL
```

> **Note**: The `module_name` used during route registration must exactly match the `platform` name registered by the adapter in ErisPulse, otherwise `get_connection_info()` will not associate the route. For multi-account adapters, sub-paths (such as `/account1/webhook`, `/account2/webhook`) should be registered for each account, not different `module_name`.

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
            "myplatform_raw": raw_event,  # Preserve original data (required)
            "myplatform_raw_type": raw_event.get("type", "")  # Original type (required)
        }
        return onebot_event
```

### 2. Standardize Timestamps

```python
def _convert_timestamp(self, timestamp):
    """Convert to 10-digit second-level timestamp"""
    if not timestamp:
        return int(time.time())
    
    # If it's a millisecond-level timestamp
    if timestamp > 10**12:
        return int(timestamp / 1000)
    
    # If it's a second-level timestamp
    return int(timestamp)
```

### 3. Generate Event ID

```python
import uuid

def _generate_event_id(self, raw_event):
    """Generate event ID"""
    event_id = raw_event.get("event_id")
    if event_id:
        return str(event_id)
    # If the platform does not provide an ID, generate a UUID
    return str(uuid.uuid4())
```

## SendDSL Implementation

The `At`/`AtAll`/`Reply` decorators are built into the framework's SendDSL base class. Adapters only need to implement `Raw_ob12` and specific send methods. Use `self._apply_modifiers(message)` and `self.send_context` to simplify development.

### 1. Must Return a Task Object

```python
class Send(BaseAdapter.Send):
    def Raw_ob12(self, message, **kwargs):
        """Recommended implementation: use framework helper method"""
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

### 2. Chainable Modifier Methods Return self

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
        """Send sticker message"""
        return asyncio.create_task(
            self._adapter.call_api(
                endpoint="/send_sticker",
                message=[{"type": "sticker", "data": {"id": sticker_id}}],
                **self.send_context
            )
        )
    
    def Card(self, card_data: dict):
        """Send card message"""
        return asyncio.create_task(
            self._adapter.call_api(
                endpoint="/send_card",
                message=[{"type": "card", "data": card_data}],
                **self.send_context
            )
        )
```

## API Response

### 1. Standardize Response Format

The framework provides `make_response()` and `make_error()` methods to construct standardized responses:

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

`make_response()` will automatically generate a response dictionary containing the `{platform}_raw` key. `make_error()` defaults to using `retcode=34000` (Platform Error).

### 2. Error Code Specification

Follow the OneBot12 standard error codes:

```python
# 1xxxx - Action Request Errors
10001: Bad Request
10002: Unsupported Action
10003: Bad Param

# 2xxxx - Action Handler Errors
20001: Bad Handler
20002: Internal Handler Error

# 3xxxx - Action Execution Errors
31000: Database Error
32000: Filesystem Error
33000: Network Error
34000: Platform Error
35000: Logic Error
```

## Multi-Account Support

### 1. Declarative Configuration (Recommended)

After declaring the configuration class using `AccountConfigClass`, the framework will automatically manage multi-account loading, validation, and template generation. The `BotAccountConfig` base class provides the `enabled` and `name` fields, which the adapter does not need to declare:

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
            # bot_id is automatically filled by the framework from the platform protocol/login response
    
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

### 2. Account Selection Mechanism

The framework provides the built-in `_resolve_account()` method, with matching priority:

1. **Account name** — Exact match with configuration key
2. **`bot_id` field** — Automatically obtained bot_id (i.e., `event["self"]["user_id"]`)
3. **Any str field** — Other string fields in the configuration
4. **Fallback** — The first enabled account

```python
# Match by account name
name, account = self._resolve_account("account1")

# Match by bot_id (most commonly used method, from event)
name, account = self._resolve_account("bot_123")

# Get the first enabled account (pass in None)
name, account = self._resolve_account(None)
```

## Error Handling

### 1. Categorized Exception Handling

Use `make_error()` to construct standardized error responses. When requesting through `sdk.client`, catch ErisPulse exceptions:

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
        self.logger.error(f"Request timeout: {endpoint}")
        return self.make_error(retcode=32000, message="Request timeout")
    except ClientError as e:
        self.logger.error(f"Network error: {e}")
        return self.make_error(retcode=33000, message="Network request failed")
    except json.JSONDecodeError:
        self.logger.error("JSON parsing failed")
        return self.make_error(retcode=10006, message="Response format error")
    except Exception as e:
        self.logger.error(f"Unknown error: {e}", exc_info=True)
        return self.make_error(message=str(e))
```

> **Backward Compatibility**: Old adapter code using `aiohttp` is unaffected and can still catch `aiohttp.ClientError`. Exception conversion only takes effect when requests are made through `sdk.client`.

### 2. Logging

The framework automatically creates a sub-logger for the adapter (`sdk.logger.get_child("MyAdapter")`), eliminating the need for manual initialization:

```python
class MyAdapter(BaseAdapter):
    # ConfigClass = ...  # After declaring the configuration class, self.logger is automatically available
    
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

`Raw_ob12` is a method that adapters **must implement**, serving as the unified entry point for reverse conversion (OneBot12 → platform). Standard methods (`Text`, `Image`, etc.) should delegate to `Raw_ob12`, and modifier state (`At`/`Reply`/`AtAll`) must be merged into message segments within `Raw_ob12`.

`MessageBuilder` is a message segment construction tool used in conjunction with `Raw_ob12`, supporting chainable calls and rapid construction.

> Complete implementation specifications, code examples, and usage methods can be found in:
> - [Send Method Specification §6 Reverse Conversion Specification](../../standards/send-method-spec.md#6-反向转换规范onebot12--平台)
> - [Send Method Specification §11 MessageBuilder](../../standards/send-method-spec.md#11-消息构建器-messagebuilder)

## Platform Event Method Extension

Adapters can register platform-specific methods for Event wrapper classes, allowing module developers to more easily access platform-specific data.

### 1. Use Mixin Class for Batch Registration (Recommended)

When the platform has multiple specific methods, it is recommended to use a Mixin class:

```python
# Register in start() or module level
from ErisPulse.Core.Event import register_event_mixin

class MyPlatformEventMixin:
    def get_chat_name(self):
        """Get chat name"""
        return self.get("myplatform_raw", {}).get("chat", {}).get("name", "")

    def is_official_message(self):
        """Check if it is an official message"""
        raw = self.get("myplatform_raw", {})
        return raw.get("sender", {}).get("is_official", False)

    def get_message_type(self):
        """Get platform message type"""
        return self.get("myplatform_raw", {}).get("msg_type", "text")

# Batch register
register_event_mixin("myplatform", MyPlatformEventMixin)
```

### 2. Use Decorator to Register Single Method

```python
from ErisPulse.Core.Event import register_event_method

@register_event_method("myplatform")
def get_chat_name(self):
    return self.get("myplatform_raw", {}).get("chat", {}).get("name", "")
```

### 3. Clean Up on Adapter Shutdown

```python
from ErisPulse.Core.Event import unregister_platform_event_methods

class MyAdapter(BaseAdapter):
    async def shutdown(self):
        # Clean up platform event method registration
        unregister_platform_event_methods("myplatform")
        # ... other cleanup
```

> For more detailed registration and deregistration instructions, see [Event System API - Register Platform Extension Methods](../../api-reference/event-system.md#适配器注册平台扩展方法).

## Documentation Maintenance

### 1. Maintain Platform Feature Documentation

Create a `{platform}.md` documentation under `docs/en/platform-guide/` (other language versions will be automatically generated):

```markdown
# Platform Name Adapter Documentation

## Basic Information
- Corresponding Module Version: 1.0.0
- Maintainer: Your Name

## Supported Message Sending Types
...

## Specific Event Types
...

## Configuration Options
...
```

### 2. Update Version Information

When releasing a new version, update the version information in the documentation:

```toml
[project]
version = "2.0.0"  # Update version number
```



### 事件转换器

# Event Converter Implementation Guide

The Event Converter is one of the core components of an adapter, responsible for converting platform-native events into the unified OneBot12 standard event format used by ErisPulse.

## Converter Responsibilities

```
Platform-native Event ──→ Converter.convert() ──→ OneBot12 Standard Event
```

The Converter is responsible only for **forward conversion** (receiving direction), transforming platform-native event data into the OneBot12 standard format. Reverse conversion (sending direction) is handled by the `Send.Raw_ob12()` method.

### Core Principles

1. **Lossless Conversion**: Original data must be fully retained in the `{platform}_raw` field
2. **Standard Compatibility**: The converted event must conform to the OneBot12 standard format
3. **Platform Extension**: Platform-specific data is stored using fields prefixed with `{platform}_`

## BaseConverter Base Class (Recommended)

Since version 2.7.0, the framework provides the `BaseConverter` base class (`ErisPulse.Core.Bases`), which encapsulates the **common field construction** and **common message segment helpers** for OneBot12 events, allowing converters to focus solely on type mapping:

```python
from ErisPulse.Core.Bases import BaseConverter


class MyConverter(BaseConverter):
    def __init__(self):
        super().__init__(platform="myplatform")

    def convert(self, raw_event: dict) -> dict | None:
        if not isinstance(raw_event, dict):
            return None
        event_type = raw_event.get("type", "")
        base = self.build_base_event(raw_event, event_type)  # id/time/platform/self/raw
        if event_type == "message":
            base["type"] = "message"
            base["detail_type"] = "group" if raw_event.get("group_id") else "private"
            base["user_id"] = str(raw_event.get("sender_id", ""))
            base["message"] = [self.text(raw_event.get("content", ""))]
            base["alt_message"] = raw_event.get("content", "")
            return base
        return None
```

`build_base_event()` already fills in the following common fields:

| Field | Source |
|------|------|
| `id` | `raw_event["event_id"]`, generated as UUID if missing |
| `time` | `raw_event["timestamp"]`, current time if missing |
| `platform` | `platform` passed during initialization |
| `self` | `{"platform": ..., "user_id": raw_event["bot_id"]}` |
| `{platform}_raw` | Original event (to satisfy "lossless conversion" principle) |
| `{platform}_raw_type` | Original event type |

Common message segment helper methods (all static methods, directly reusable):

```python
converter.text("hi")          # {"type": "text", "data": {"text": "hi"}}
converter.at("123456")        # {"type": "at", "data": {"user_id": "123456"}}
converter.image("file.png")   # {"type": "image", "data": {"file": "file.png"}}
```

> When implementing manually, the public field construction in `build_base_event` is boilerplate code that must be repeatedly written. Using `BaseConverter` eliminates this, and naturally ensures "lossless conversion" (original event always goes into `{platform}_raw`).

## convert() Method

### Method Signature

```python
def convert(self, raw_event: dict) -> dict:
    """
    Converts platform-native event data to OneBot12 standard format.

    :param raw_event: Platform-native event data
    :return: OneBot12 standard format event dictionary
    """
    pass
```

### Return Value Structure

The converted event dictionary should include the following standard fields:

```python
{
    "id": "Unique event ID",
    "time": 1234567890,           # Unix timestamp (seconds)
    "type": "message",             # Event type
    "detail_type": "private",      # Detailed type
    "platform": "myplatform",      # Platform name
    "self": {
        "platform": "myplatform",
        "user_id": "bot_user_id"
    },

    # Message event fields
    "user_id": "sender_id",
    "message": [...],              # List of OneBot12 message segments
    "alt_message": "Plain text content",

    # Original data must be preserved
    "myplatform_raw": { ... },     # Full platform-native event data
    "myplatform_raw_type": "Original event type name",
}
```

## Required Field Mapping

### Common Fields (All Event Types)

| OB12 Field | Type | Description |
|-----------|------|------|
| `id` | str | Unique event identifier |
| `time` | int | Unix timestamp (seconds) |
| `type` | str | Event type: `message` / `notice` / `request` / `meta` |
| `detail_type` | str | Detailed type: `private` / `group` / `friend` etc. |
| `platform` | str | Platform name, consistent with adapter registration name |
| `self` | dict | Bot information: `{"platform": "...", "user_id": "..."}` |

### Message Event Additional Fields

| OB12 Field | Type | Description |
|-----------|------|------|
| `user_id` | str | Sender ID |
| `message` | list[dict] | List of OneBot12 message segments |
| `alt_message` | str | Plain text fallback content |

### Notification Event Additional Fields

| OB12 Field | Type | Description |
|-----------|------|------|
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

# @Mention
{"type": "mention", "data": {"user_id": "123"}}

# @All
{"type": "mention_all", "data": {}}

# Reply
{"type": "reply", "data": {"message_id": "msg_123"}}
```

If the platform does not support certain message segment types, you may omit the segment or convert it to the closest standard type.

## Platform Extension Fields

Platform-specific data should be stored using fields prefixed with `{platform}_` to avoid conflicts with standard fields:

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
    "myplatform_group_name": "Group Name",
    "myplatform_sender_role": "admin",
}
```

> **Important**: The `{platform}_raw` field is required, as ErisPulse's event system and modules may depend on it to access platform-specific raw data.

## Complete Example

Here is a complete Converter implementation:

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

## Rich Media Message Conversion Example

Platform messages often contain rich media content such as images, @mentions, and replies. Here is an example of `_convert_message_segments` handling multiple message types:

```python
def _convert_message_segments(self, raw_content: list) -> list:
    """Converts platform-native message segment list into OneBot12 standard message segments"""
    segments = []

    for item in raw_content:
        item_type = item.get("type", "")

        if item_type == "text":
            segments.append({
                "type": "text",
                "data": {"text": item.get("content", "")}
            })

        elif item_type == "image":
            file_url = item.get("url") or item.get("file_id", "")
            segments.append({
                "type": "image",
                "data": {"file": file_url}
            })

        elif item_type == "at":
            segments.append({
                "type": "mention",
                "data": {"user_id": item.get("target_id", "")}
            })

        elif item_type == "reply":
            segments.append({
                "type": "reply",
                "data": {"message_id": item.get("reply_to_id", "")}
            })

        elif item_type == "at_all":
            segments.append({"type": "mention_all", "data": {}})

        else:
            segments.append({
                "type": "text",
                "data": {"text": f"[Unsupported message type: {item_type}]"}
            })

    return segments
```

## Common Pitfalls

### 1. Missing `{platform}_raw` Field

This is the most common error. Missing the original data field will prevent modules from accessing platform-specific information.

```python
base_event["myplatform_raw"] = raw_event        # Required!
base_event["myplatform_raw_type"] = event_type   # Required!
```

### 2. Incorrect Timestamp Format

OneBot12 requires the `time` field to be a Unix timestamp in seconds (integer). If your platform returns milliseconds or an ISO string, you must convert it:

```python
import time

# Milliseconds → seconds
"time": raw_event.get("timestamp", 0) // 1000

# ISO string → seconds
"time": int(time.mktime(time.strptime(raw_event["created_at"], "%Y-%m-%dT%H:%M:%S")))
```

### 3. Missing `self` Field

The `self` field contains bot information, with `user_id` being the bot's account ID. This field is crucial in multi-bot scenarios:

```python
"self": {
    "platform": self.platform,
    "user_id": raw_event.get("bot_id", ""),   # Bot's own ID
}
```

### 4. Using Non-Standard `detail_type` Values

`detail_type` must use OneBot12 standard values, such as `private`, `group`, `friend_increase`, `group_member_increase`, etc. Do not use platform-specific naming.

### 5. Round-Trip Consistency

Ensure that the message segment types generated by the Converter correspond to methods supported by the Send end. For example, if the Converter converts platform image messages into `{"type": "image", ...}`, then the `Image()` method on the Send end must be able to handle image sending.

## Best Practices

1. **Always preserve original data**: The `{platform}_raw` field must not be omitted
2. **Use standard message segments**: Try to convert platform messages into OneBot12 standard message segments
3. **Set `detail_type` appropriately**: Use standard types (`private`/`group`/`channel` etc.), do not define custom values
4. **Handle edge cases**: Original events may lack certain fields; use `.get()` and provide reasonable defaults
5. **Performance considerations**: `convert()` is called for every event, avoid performing time-consuming operations within it



=====
发布与工具
=====


### 发布模块到模块商店

# Publishing and Module Store Guide

Publish your developed module or adapter to the ErisPulse Module Store, allowing other users to easily discover and install it.

## Module Store Overview

The ErisPulse Module Store is a centralized module registry where users can browse, search, and install community-contributed modules and adapters through the CLI tool.

### Browsing and Discovery

```bash
# List all available packages remotely
epsdk list-remote

# Show only modules
epsdk list-remote -t modules

# Show only adapters
epsdk list-remote -t adapters

# Force refresh remote package list
epsdk list-remote -r
```

You can also browse the module store online at [ErisPulse official website](https://www.erisdev.com/#market).

### Supported Submission Types

| Type | Description | Entry-point Group |
|------|-------------|-------------------|
| Module | Extend bot functionality, implement business logic | `erispulse.module` |
| Adapter | Connect to new messaging platforms | `erispulse.adapter` |

## Quick Publishing

The entire process only requires three steps: configure the project → publish to PyPI → submit to the module store.

### 1. Configure pyproject.toml

Ensure the project directory contains `pyproject.toml` and `README.md`, and configure entry-points according to the type:

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

> **Note**: It is recommended that package names start with `ErisPulse-` for easy identification by users. The entry-point key (e.g., `"MyModule"`) will serve as the module's access name in the SDK.

### 2. Publish to PyPI

```bash
# Build + Publish (requires PyPI account)
pip install build twine
python -m build
python -m twine upload dist/*
```

After successful publication, verify installation:

```bash
pip install ErisPulse-MyModule
```

### 3. Submit to Module Store

Go to [ErisPulse Module Store](https://www.erisdev.com/#market), click "Submit Module", log in, and fill in the module information.

Supported login methods: **GitHub**, **Codeberg**, **Yunhu**, choose any one.

Key points to fill in:
- Module name, description, repository address
- Minimum SDK version: If unsure, fill in the version number of the latest [ErisPulse release](https://pypi.org/project/ErisPulse/)

After submission, it takes effect immediately, and users can install via the module source. The module will be marked as "unverified", and after the maintainer's review, it will be changed to "verified".

> **About verification status**:
> - "Unverified" only means it has not yet been officially reviewed, not that the module has problems
> - When users install unverified modules via `epsdk install`, they will receive a risk warning and must confirm before continuing installation

### 4. Manage Published Modules

After clicking "Submit Module" and logging in on the module store, switch to the "My Modules" tab to:

- **Edit** — Modify module description, repository address, tags, etc. The version number will automatically sync from PyPI
- **Delete** — Remove the module from the module store (irreversible)

> Newly submitted modules may take a few minutes to appear in the "My Modules" list.

## Update Published Modules

1. Update the `version` in `pyproject.toml`
2. Rebuild and upload: `python -m build && python -m twine upload dist/*`
3. The module store will automatically sync the latest version from PyPI

Users can upgrade via `epsdk upgrade MyModule`.

## Pre-release Checklist

Before pushing to PyPI, please confirm the following items one by one:

### Code Quality

- [ ] All public APIs have type annotations (function signatures and return values)
- [ ] All public methods have docstrings (`"""..."""` format, including `:param` / `:return` / `:raises`)
- [ ] Passed `ruff check` (no warnings)
- [ ] Test coverage ≥ 80%
- [ ] Passed all `pytest` cases

### Compatibility

- [ ] `pyproject.toml` declares the minimum SDK version: `dependencies = ["ErisPulse>=x.y.z"]`
- [ ] Tested on Python 3.10 / 3.11 / 3.12 / 3.13
- [ ] Tested on target operating systems (Windows / Linux / macOS, if applicable)
- [ ] No circular import dependencies

### Configuration

- [ ] If using declarative configuration (`ConfigClass` + `BaseConfig` / `BotAccountConfig`), configuration fields have `description` (recommended i18n format) and `ui` metadata
- [ ] If i18n translation keys are registered, all 5 languages (zh-CN / zh-TW / en / ja / ru) are covered
- [ ] Sensitive fields are marked with `secret=True`

### Documentation

- [ ] `README.md` has installation instructions and basic usage examples
- [ ] `README.md` explains configuration methods (configuration file examples + environment variables)
- [ ] `CHANGELOG.md` records all changes
- [ ] Adapter updates platform feature documentation (supported Send types, event types, etc.)

### Publishing

- [ ] `pyproject.toml` version number has been updated
- [ ] Build passed: `python -m build`
- [ ] Pushed to PyPI: `python -m twine upload dist/*`
- [ ] Installation verified: `pip install ErisPulse-xxx && epsdk run`

## Development Mode Testing

Before formal release, you can test locally using editable mode:

```bash
epsdk install -e /path/to/MyModule
# or
pip install -e /path/to/MyModule
```

## Frequently Asked Questions

### Must package names start with `ErisPulse-`?

Not mandatory, but strongly recommended. This helps users identify ErisPulse ecosystem packages on PyPI.

### Can a package register multiple modules?

Yes. Configure multiple key-value pairs in `entry-points`:

```toml
[project.entry-points."erispulse.module"]
"ModuleA" = "MyPackage:ModuleA"
"ModuleB" = "MyPackage:ModuleB"
```

### How long does the review take?

Typically completed within 1-3 working days. You can check the verification status in the "My Modules" section of the module store.

## Distributing Applications via Docker Images

If your application is not suitable for publishing to PyPI (e.g., contains private dependencies or requires pre-configured environments), you can publish Docker images via **GitHub Container Registry (GHCR)**, allowing other users to start with one click using `docker pull`.

### Applicable Scenarios

- You have a **complete robot application** (module + configuration + entry script) and want to distribute it with one click
- Modules/adapters depend on **private packages** or have special installation processes, making them unsuitable for PyPI
- You want to provide an **out-of-the-box deployment solution**, lowering the barrier to user adoption

### 1. Create Dockerfile

Build based on the ErisPulse official image, just add your module:

```dockerfile
FROM erispulse/erispulse:latest

LABEL org.opencontainers.image.title="ErisPulse-MyModule" \
      org.opencontainers.image.description="Module description" \
      org.opencontainers.image.url="https://github.com/yourname/ErisPulse-MyModule" \
      org.opencontainers.image.source="https://github.com/yourname/ErisPulse-MyModule"

COPY pyproject.toml README.md ./
COPY MyModule/ ./MyModule/

RUN uv pip install --system -e .
```

If the module requires additional system dependencies (e.g., SSH client, etc.), add them after `RUN uv pip install`:

```dockerfile
RUN apt-get update && apt-get install -y --no-install-recommends \
    openssh-client \
    && rm -rf /var/lib/apt/lists/*
```

> `erispulse/erispulse:latest` already includes ErisPulse, ErisPulse-Dashboard, Python runtime, and uv, no need to install repeatedly.

### 2. Create GitHub Actions Workflow

In `.github/workflows/docker-publish.yml`, create:

```yaml
name: Publish Docker Image

on:
  workflow_dispatch:
  push:
    branches:
      - main
    tags:
      - "v*"

permissions:
  contents: read
  packages: write

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository_owner }}/my-bot

jobs:
  docker-publish:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up QEMU (multi-architecture support)
        uses: docker/setup-qemu-action@v3

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Login to GitHub Container Registry
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Extract Docker metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
          tags: |
            type=semver,pattern={{version}}
            type=semver,pattern={{major}}.{{minor}}
            type=raw,value=latest

      - name: Build and push Docker image
        uses: docker/build-push-action@v6
        with:
          context: .
          file: ./Dockerfile
          platforms: linux/amd64,linux/arm64
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
```

> `GITHUB_TOKEN` is automatically provided by GitHub Actions, no need to manually create a key.

### 3. Trigger Build

Push code or tag to trigger automatic build:

```bash
# Push to main branch to trigger
git push origin main

# Or tag to trigger
git tag v1.0.0
git push origin v1.0.0
```

You can also manually trigger it on the GitHub repository's **Actions** page.

### 4. Set Image as Public

GHCR images are private by default, and need to be set to Public in GitHub settings before other users can pull without logging in:

1. Go to repository → **Packages** → Click the corresponding Package
2. **Package settings** → **Danger Zone** → **Change visibility** → **Public**

### 5. User Usage

After building, users can start with one line using `docker run`:

```bash
docker run -d \
  --name my-bot \
  -p 8000:8000 \
  -v $(pwd)/config:/app/config \
  -e TZ=Asia/Shanghai \
  -e ERISPULSE_DASHBOARD_TOKEN=your-token \
  --restart unless-stopped \
  ghcr.io/<your-username>/my-bot:latest
```

Or use `docker-compose.yml`:

```yaml
services:
  my-bot:
    image: ghcr.io/<your-username>/my-bot:latest
    container_name: my-bot
    ports:
      - "8000:8000"
    volumes:
      - ./config:/app/config
    environment:
      - TZ=Asia/Shanghai
      - ERISPULSE_DASHBOARD_TOKEN=${ERISPULSE_DASHBOARD_TOKEN:-}
    restart: unless-stopped
```

### Publish to Docker Hub Simultaneously

Extend the workflow, add Docker Hub login before the login step, and add the Docker Hub address in `images`:

```yaml
      - name: Login to Docker Hub
        uses: docker/login-action@v3
        with:
          registry: docker.io
          username: ${{ secrets.DOCKERHUB_USERNAME }}
          password: ${{ secrets.DOCKERHUB_TOKEN }}

      - name: Extract Docker metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: |
            docker.io/<your-dockerhub-username>/my-bot
            ghcr.io/${{ github.repository_owner }}/my-bot
```

> You need to add `DOCKERHUB_USERNAME` and `DOCKERHUB_TOKEN` in the repository **Settings → Secrets**.

### Docker Image vs PyPI Publishing

| Feature | Docker Image (GHCR) | PyPI Publishing |
|---------|---------------------|-----------------|
| Distribution Method | `docker pull` one-click run | `pip install` + manual configuration |
| Applicability | Complete applications/solutions | Individual modules/adapters |
| Private Dependencies | Native support | Requires private PyPI source |
| Module Store | Not applicable | Can be submitted to module store |
| Multi-architecture | Supports amd64/arm64 | Architecture-agnostic |

These two methods are not contradictory—you can simultaneously publish modules to the module store via PyPI and provide ready-to-use Docker images via GHCR.



### CLI 命令参考

# CLI Command Reference

The ErisPulse command-line tool (`epsdk`) provides project and package management functionality.

> **Tip**: You can view detailed parameter descriptions for any command using `epsdk <command> --help`.

---

## Package Management Commands

| Command | Aliases | Parameters | Description |
|---------|---------|------------|-------------|
| `install` | `i`, `add` | `[package]... [--upgrade/-U] [--pre] [-e PATH] [--user] [--no-deps] [-t DIR] [--index-url URL] [--extra-index-url URL] [--no-cache-dir] [-r FILE] [-c FILE] [--force-reinstall] [--ignore-installed] [--compile/--no-compile] [--prefix DIR] [--src DIR] [--config-settings SETTINGS] [--no-binary FORMAT] [--only-binary FORMAT] [--prefer-binary] [--build-isolation/--no-build-isolation] [--upgrade-strategy {eager,only-if-needed,to-satisfy-only}] [--break-system-packages] [--no-uv]` | Install modules/adapters |
| `uninstall` | `rm`, `remove` | `<package>... [--no-uv]` | Uninstall modules/adapters |
| `upgrade` | `up` | `[package]... [--force/-f] [--pre] [--no-uv]` | Upgrade specified modules or all |
| `self-update` | `su`, `update` | `[version] [--pre] [--force/-f] [--no-uv]` | Update the SDK itself |

## Diagnostic Commands

| Command | Alias | Parameters | Description |
|---------|-------|------------|-------------|
| `doctor` | `diag` | `[--verbose]` | Diagnose environment and output health report |

### install

Installs ErisPulse modules or adapter packages. If no package name is specified, enters interactive installation interface.

**Aliases:** `i`, `add`

**Parameters:**

| Parameter | Short | Description |
|-----------|-------|-------------|
| `[package]...` | | Package names to install, multiple can be specified |
| `--upgrade` | `-U` | Upgrade to latest version during installation |
| `--pre` | | Allow installation of pre-release versions |
| `--editable` | `-e` | Install in editable mode (requires path specification) |
| `--user` | | Install to user site-packages directory |
| `--no-deps` | | Do not install dependencies |
| `--target` | `-t` | Install to specified directory |
| `--index-url` | | Specify PyPI mirror source URL |
| `--extra-index-url` | | Additional PyPI mirror source URL (can be specified multiple times) |
| `--no-cache-dir` | | Disable cache |
| `--requirement` | `-r` | Install from requirements file |
| `--constraint` | `-c` | Install from constraint file |
| `--force-reinstall` | | Force reinstallation |
| `--ignore-installed` | | Ignore already installed packages |
| `--compile` | | Compile .pyc files after installation |
| `--no-compile` | | Do not compile .pyc files after installation |
| `--prefix` | | Install to specified prefix directory |
| `--src` | | Source code directory used for editable installation |
| `--config-settings` | | Pass configuration to build backend (can be specified multiple times) |
| `--no-binary` | | Restrict not to use binary packages (format like `:all:`) |
| `--only-binary` | | Restrict only to use binary packages (format like `:all:`) |
| `--prefer-binary` | | Prefer binary packages |
| `--build-isolation` | | Enable build isolation |
| `--no-build-isolation` | | Disable build isolation |
| `--upgrade-strategy` | | Upgrade strategy: `eager`, `only-if-needed`, `to-satisfy-only` |
| `--break-system-packages` | | Allow modification of Python packages managed by system package manager |
| `--no-uv` | | Use pip instead of uv |

**Examples:**

```bash
# Install single module
epsdk install Weather

# Install multiple modules
epsdk install Yunhu Weather

# Install from mirror source and upgrade
epsdk install Weather -U --index-url https://pypi.tuna.tsinghua.edu.cn/simple

# Editable mode installation (development mode)
epsdk install -e ./my-adapter
```

### uninstall

Uninstalls installed ErisPulse modules or adapter packages. If no package name is specified, enters interactive uninstallation interface.

**Aliases:** `rm`, `remove`

**Parameters:**

| Parameter | Description |
|-----------|-------------|
| `<package>...` | Package names to uninstall, multiple can be specified |
| `--no-uv` | Use pip instead of uv |

**Examples:**

```bash
# Uninstall single module
epsdk uninstall Weather

# Uninstall multiple modules
epsdk uninstall Yunhu Weather
```

### upgrade

Upgrades installed ErisPulse components. If no package name is specified, upgrades all interactively.

**Aliases:** `up`

**Parameters:**

| Parameter | Short | Description |
|-----------|-------|-------------|
| `[package]...` | | Package names to upgrade, multiple can be specified |
| `--force` | `-f` | Force upgrade, skip confirmation |
| `--pre` | | Allow upgrade to pre-release versions |
| `--no-uv` | | Use pip instead of uv |

**Examples:**

```bash
# Upgrade all packages
epsdk upgrade

# Upgrade specified package
epsdk upgrade Weather

# Force upgrade (skip confirmation)
epsdk upgrade -f
```

### self-update

Updates ErisPulse SDK itself to the latest version.

**Aliases:** `su`, `update`

**Parameters:**

| Parameter | Short | Description |
|-----------|-------|-------------|
| `[version]` | | Specify target version number to update to |
| `--pre` | | Allow update to pre-release version |
| `--force` | `-f` | Force update, skip confirmation |
| `--no-uv` | | Use pip instead of uv |

**Examples:**

```bash
# Update to latest stable version
epsdk self-update

# Update to specified version
epsdk self-update 1.2.3

# Allow pre-release version
epsdk self-update --pre

# Force update
epsdk self-update -f
```

## Information Query Commands

| Command | Alias | Parameters | Description |
|---------|-------|------------|-------------|
| `list` | `l`, `ls` | `[--type/-t {modules,adapters,all}] [--outdated/-o]` | List installed components |
| `list-remote` | `lsr` | `[--type/-t {modules,adapters,all}] [--refresh/-r]` | List remote available components |

### list

List installed ErisPulse modules and adapters.

**Aliases:** `l`, `ls`

**Parameters:**

| Parameter | Short Parameter | Description |
|-----------|-----------------|-------------|
| `--type` | `-t` | Specify type: `modules`, `adapters`, `all` (default) |
| `--outdated` | `-o` | Only show upgradable packages |

**Examples:**

```bash
# List all installed components
epsdk list

# Only list modules
epsdk list -t modules

# Only list adapters
epsdk list -t adapters

# Only show upgradable packages
epsdk list -o
```

### list-remote

List ErisPulse modules and adapters available in the remote repository.

**Aliases:** `lsr`

**Parameters:**

| Parameter | Short Parameter | Description |
|-----------|-----------------|-------------|
| `--type` | `-t` | Specify type: `modules`, `adapters`, `all` (default) |
| `--refresh` | `-r` | Force refresh remote package list cache |

**Examples:**

```bash
# List all remote available components
epsdk list-remote

# Only list remote modules
epsdk list-remote -t modules

# List after forcing cache refresh
epsdk list-remote -r
```

## Configuration Commands

| Command | Alias | Parameters | Description |
|---------|-------|------------|-------------|
| `config` | `cfg`, `conf` | `[name] [--list/-l]` | Interactively configure declarative configuration items of adapters/modules |

### config

Interactively fills out declarative configuration items of adapters/modules. The wizard is driven by the configuration class (`ConfigClass` / `AccountConfigClass`) declared by the adapter/module, automatically generating forms and validating them, eliminating the need to manually write `config.toml`.

Adapters additionally support multi-account (bot account) management: adding/editing/deleting accounts, as well as enabling/disabling switches.

**Aliases:** `cfg`, `conf`

**Parameters:**

| Parameter | Short Parameter | Description |
|-----------|-----------------|-------------|
| `[name]` | | Target name (adapter platform name or module name), leave empty to enter interactive selection |
| `--list` | `-l` | List configuration status of all targets only, do not enter the wizard |

**Examples:**

```bash
# View configuration status of all adapters/modules
epsdk config --list

# Enter interactive selection to configure
epsdk config

# Directly configure a specified adapter
epsdk config yunhu

# Directly configure a specified module
epsdk config MyModule
```

**Notes:**

- Configuration status is divided into four levels: `Ready` (validation passed), `Incomplete` (missing or validation failed required fields), `Not Configured` (never generated), `No Configuration` (target did not declare a configuration class)
- Field values are annotated with source information: existing configurations show ` (current:value)`, unconfigured fields show schema default values ` (default:value)`; pressing Enter retains the current value
- Secret-type fields (declared with `secret`) do not echo input, and pressing Enter retains the previously set value
- In interactive selection mode, after completing a single wizard, the selection menu is returned (status refreshed), allowing continuous configuration of multiple targets; press Enter to exit
- If global form validation fails and you choose not to re-enter, the current wizard is aborted and no configuration is written (to avoid creating a "enabled but incomplete configuration" state)
- After saving, configuration is immediately written to `config/config.toml`, and is visible in both the Dashboard and running SDK; for running adapters, restarting the process applies new account configurations
- After successful interactive installation via `epsdk install` or `epsdk init`, if configuration declaration is detected, it automatically guides you into this wizard; when installing a package directly from the command line, only a configuration prompt is printed

## Control Commands

| Command | Alias | Parameters | Description |
|---------|-------|------------|-------------|
| `run` | `r` | `[script] [--reload]` | Run a specified script or SDK |

### run

Run an ErisPulse project script or directly start the SDK. Hot reload mode is supported.

**Alias:** `r`

**Parameters:**

| Parameter | Description |
|-----------|-------------|
| `[script]` | The script file to run; if not specified, the SDK is run |
| `--reload` | Enable hot reload mode, monitoring file changes and automatically restarting |

**Examples:**

```bash
# Run SDK directly
epsdk run

# Run a specified script file
epsdk run main.py

# Run in hot reload mode (automatically restart on file changes)
epsdk run main.py --reload

# SDK in hot reload mode
epsdk run --reload
```

## Project Management Commands

| Command | Alias | Parameters | Description |
|---------|-------|------------|-------------|
| `init` | — | `[--project-name/-n <name>] [--quick/-q] [--force/-f] [--here] [--no-uv]` | Initialize an ErisPulse project |
| `create` | — | `{module,adapter} [--name/-n <name>] [--description/-d <desc>] [--author/-a <name>] [--email/-e <mail>] [--homepage <url>] [--output/-o <dir>] [--force/-f]` | Create a module/adapter scaffold |

### init

Initialize a new ErisPulse project. Supports both interactive and quick mode.

**Parameters:**

| Parameter | Short Parameter | Description |
|-----------|-----------------|-------------|
| `--project-name` | `-n` | Project name |
| `--quick` | `-q` | Quick mode, skip interactive wizard |
| `--force` | `-f` | Force overwrite existing configuration file |
| `--here` | | Initialize in the current directory, do not create a subdirectory |
| `--no-uv` | | Use pip instead of uv |

**Examples:**

```bash
# Interactive initialization
epsdk init

# Quick initialization
epsdk init -q -n my_bot

# Force overwrite existing configuration
epsdk init -f

# Initialize in current directory
epsdk init --here -n my_bot
```

### create

Create a scaffold project for an ErisPulse module or adapter.

**Parameters:**

| Parameter | Short Parameter | Description |
|-----------|-----------------|-------------|
| `{module,adapter}` | | Type to create: `module` or `adapter` |
| `--name` | `-n` | Project name (PascalCase) |
| `--description` | `-d` | Project description |
| `--author` | `-a` | Author name |
| `--email` | `-e` | Author email |
| `--homepage` | | Project homepage URL |
| `--output` | `-o` | Output directory (default: current directory) |
| `--force` | `-f` | Force overwrite existing directory |
| `--local` | | Create a local plugin (only available for `module`): generates `plugins/<name>/` package structure, eliminates the need for packaging and installation |

**Examples:**

```bash
# Interactive creation (guided selection of type and filling in information)
epsdk create

# Directly create a Module project
epsdk create module -n MyModule

# Create a local plugin (placed in the project's plugins/ directory, automatically discovered at startup, supports hot reload)
epsdk create module -n MyModule --local

# Directly create an Adapter project
epsdk create adapter -n MyAdapter

# Full parameters
epsdk create module -n MyModule -d "Module description" -a "Author" -e "mail@example.com"

# Specify output directory
epsdk create module -n MyModule -o ./projects

# Force overwrite existing directory
epsdk create module -n MyModule -f
```

---

## Language Commands

| Command | Aliases | Parameters | Description |
|---------|---------|------------|-------------|
| `i18n` | `language`, `lang` | `[lang] [--list/-l]` | View or switch the CLI display language |

### i18n

View the current CLI language, list supported languages, or switch the display language. If no parameter is specified, it enters an interactive selection interface.

**Aliases:** `language`, `lang`

**Parameters:**

| Parameter | Short Parameter | Description |
|-----------|-----------------|-------------|
| `[lang]` | | The language code to switch to (e.g., `zh-CN`, `en`, `ja`, `ru`) |
| `--list` | `-l` | List all supported languages |

**Examples:**

```bash
# Interactive language selection
epsdk i18n

# Switch to English
epsdk i18n en

# Switch to Japanese
epsdk i18n ja

# List all supported languages
epsdk i18n --list
```

## Type Stub Commands

| Command | Aliases | Parameters | Description |
|---------|---------|------------|-------------|
| `types` | `t`, `stub` | `[--output/-o <path>] [--force] [--adapters-only] [--modules-only]` | Generate type stub files to enable IDE completion |

### types

Scans installed ErisPulse modules and adapters, generating `.pyi` type stub files to provide accurate code completion and type checking support in IDEs.

**Aliases:** `t`, `stub`

**Parameters:**

| Parameter | Short | Description |
|-----------|-------|-------------|
| `--output` | `-o` | Output path (default: `ep-stubs/` in current directory) |
| `--force` | | Force overwrite existing stub files |
| `--adapters-only` | | Generate type stubs only for adapters |
| `--modules-only` | | Generate type stubs only for modules |

> **Note:** `--adapters-only` and `--modules-only` are mutually exclusive; when both are specified, `--modules-only` takes precedence.

**Examples:**

```bash
# Generate type stubs for all installed modules and adapters
epsdk types

# Generate stubs only for adapters
epsdk types --adapters-only

# Output to a specified directory
epsdk types -o ./typings

# Force overwrite existing files
epsdk types --force
```

---

## Global Parameters

The following parameters are available for all commands:

| Parameter | Short Parameter | Description |
|-----------|-----------------|-------------|
| `--help` | `-h` | Displays help information |
| `--version` | `-V` | Displays version information |
| `--verbose` | `-v` | Displays verbose output (can be stacked with `-vv`/`-vvv`) |
| `--no-color` | | Disables colored output (useful for CI / log collection) |
| `--yes` | `-y` | Automatically confirms all interactive prompts (non-interactive execution) |

---

## Environment Diagnosis

### doctor

> [!NOTE]
> This command requires ErisPulse **2.7.0+**.

Diagnose the current CLI runtime environment and output a health report. Used to troubleshoot issues like "why can't it be installed / connected".

| Parameter | Description |
|-----------|-------------|
| `--verbose` | Display detailed diagnostic information |

**Check Items**:
- **Python**: Interpreter version and path
- **Installation Backend**: Whether `uv` or `pip` is used
- **Target Interpreter**: The actual target Python environment where packages are installed
- **Configuration File**: Whether `config/config.toml` exists
- **PyPI Connectivity**: Whether PyPI can be accessed (and displays the number of discovered components)
- **System Proxy**: Whether a proxy is detected

```bash
# Run environment diagnosis
epsdk doctor

# Use alias
epsdk diag
```

---

## Interactive Installation

Running `epsdk install` without specifying a package name enters interactive installation mode:

```bash
epsdk install
```

The interactive interface provides:
1. Adapter selection
2. Module selection
3. Custom installation

## Common Usage

### Install Modules

```bash
# Install a single module
epsdk install Weather

# Install multiple modules
epsdk install Yunhu Weather

# Upgrade a module
epsdk install Weather -U
```

### List Components

```bash
# List all components
epsdk list

# List only adapters
epsdk list -t adapters

# List only upgradable components
epsdk list -o

# View remote available components
epsdk list-remote
```

### Uninstall Components

```bash
# Uninstall a single component
epsdk uninstall Weather

# Uninstall multiple components
epsdk uninstall Yunhu Weather
```

### Configure Components

```bash
# View configuration status
epsdk config --list

# Interactively select target configuration
epsdk config

# Configure a specific adapter
epsdk config yunhu
```

### Upgrade Components

```bash
# Upgrade all components
epsdk upgrade

# Upgrade specified components
epsdk upgrade Weather

# Force upgrade
epsdk upgrade -f
```

### Run Project

```bash
# Run normally
epsdk run main.py

# Hot reload mode
epsdk run main.py --reload
```

### Switch Language

```bash
# Interactively select language
epsdk i18n

# Directly switch to English
epsdk i18n en

# List supported languages
epsdk i18n --list
```

### Generate Type Stubs

```bash
# Generate all type stubs
epsdk types

# Generate only module type stubs
epsdk types --modules-only
```

### Initialize Project

```bash
# Interactive initialization
epsdk init

# Quick initialization
epsdk init -q -n my_bot
```

### Create Scaffolding

```bash
# Interactive creation (guided selection of type and filling in information)
epsdk create

# Directly create Module project
epsdk create module -n MyModule

# Directly create Adapter project
epsdk create adapter -n MyAdapter

# Full parameters
epsdk create module -n MyModule -d "Module description" -a "Author" -e "mail@example.com"

# Force overwrite existing directory
epsdk create module -n MyModule -f
```



======
API 参考
======


### 适配器系统 API

# Adapter System API

This document details the API for the ErisPulse adapter system.

## Adapter Manager

### Get Adapter

```python
from ErisPulse import sdk

# Get adapter by name
adapter = sdk.adapter.get("platform_name")

# Or access directly via attribute
adapter = sdk.adapter.platform_name
```

### Use Adapter Event Listeners
> Generally, it is recommended to use the `Event` module for event listening/processing;
>
> The `Event` module also provides powerful wrappers to bring more convenience to your module development

```python
# Listen to OneBot12 standard events
@sdk.adapter.on("message")
async def handle_message(event):
    pass

# Listen to specific platform standard events
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

# Start/Stop adapter
# The following methods only show the case where parameters are passed; when no parameters are passed, it represents starting/stopping all registered adapters
await sdk.adapter.startup(["platform1", "platform2"])
await sdk.adapter.shutdown(["platform1", "platform2"])

# Check if adapter is running
is_running = sdk.adapter.is_running("platform_name")

# List all running adapters
running = sdk.adapter.list_running()
```

## Middleware

Middleware executes before events are dispatched to handlers and can modify, filter, or log event data.

### Register Middleware

```python
@sdk.adapter.middleware
async def my_middleware(event):
    sdk.logger.info(f"Middleware processing: {event}")
    return event
```

### Middleware Execution Model

- **Execution Order**: Middleware executes in registration order (first registered, first executed).
- **Data Passing**: Each middleware receives the `event` data returned by the previous middleware; if a middleware returns `None`, the return value is ignored and the original data is passed along (while outputting a `warning` level log).
- **Modifying Data**: Middleware can modify event data and return the modified dictionary.

```python
@sdk.adapter.middleware
async def add_timestamp(event):
    event["processed_at"] = time.time()
    return event

@sdk.adapter.middleware
async def filter_spam(event):
    if event.get("detail_type") == "private":
        text = event.get("alt_message", "")
        if "junk ad" in text:  # 翻译了 '垃圾广告'
            return None   # Returning None does not block event propagation, only this return value is ignored
    return event
```

> **Note**: Middleware currently does not support blocking event propagation. If you need to filter specific events, please implement conditional judgment in the event handler.
> However, you can set high-priority processors in the Event module and then use `event.mark_processed()` inside the handler to block low-priority event handlers.

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

# Get detailed info for a specific method
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
# @ User
await adapter.Send.To("group", "456").At("789").Text("Hello")

# @ All Members
await adapter.Send.To("group", "456").AtAll().Text("Hello everyone")

# Reply to message
await adapter.Send.To("group", "456").Reply("msg_id").Text("Reply content")

# Combination usage
await adapter.Send.To("group", "456").At("789").Reply("msg_id").Text("Reply to @ message")
```

## API Calling

### call_api Method

> **Note**: `call_api` is a low-level method for directly calling platform native APIs. Parameters and return values may vary across platforms, please refer to the corresponding platform adapter documentation. **It is recommended to use the Send DSL for sending messages**, and only use `call_api` in scenarios where the Send DSL does not support (e.g., getting platform-specific data, calling platform management interfaces, etc.).

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
        # Initialize adapter
        pass
    
    async def start(self):
        """Start adapter (Must implement)"""
        pass
    
    async def shutdown(self):
        """Shutdown adapter (Must implement)"""
        pass
    
    async def call_api(self, endpoint: str, **params):
        """Call platform API (Must implement)"""
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

Adapters notify the framework of the Bot's connection status by sending OneBot12 standard **`meta` events**. The system automatically extracts Bot information from them for status tracking.

### meta Event Types

Adapters should send the following three types of `meta` events:

| `type` | `detail_type` | Description | Trigger Time |
|--------|--------------|-------------|--------------|
| `meta` | `connect` | Bot connected online | After the adapter successfully establishes a connection with the platform |
| `meta` | `heartbeat` | Bot heartbeat | Sent periodically (recommended 30-60 seconds) |
| `meta` | `disconnect` | Bot disconnected | When connection loss is detected |

### self Field Extensions

ErisPulse extends the following optional fields on the OneBot12 standard `self` field:

| Field | Type | Description |
|-------|------|-------------|
| `self.platform` | string | Platform name (OB12 standard) |
| `self.user_id` | string | Bot user ID (OB12 standard) |
| `self.user_name` | string | Bot nickname (ErisPulse extension) |
| `self.avatar` | string | Bot avatar URL (ErisPulse extension) |
| `self.account_id` | string | Multi-account identifier (ErisPulse extension) |

### meta Event Format

#### connect — Connect Online

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

System Processing: Register Bot, mark as `online`, trigger `adapter.bot.online` lifecycle event.

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

System Processing: Update `last_active` time (metadata update is also supported in heartbeat).

#### disconnect — Disconnect

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

System Processing: Mark Bot as `offline`, trigger `adapter.bot.offline` lifecycle event.

### Automatic Discovery of Normal Events

In addition to `meta` events, the `self` field in normal events (`message`/`notice`/`request`) is also automatically discovered to register Bots and update active times. This means that even if the adapter does not send a `connect` event, the framework can discover the Bot from the first normal event.

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
        # Disconnected, send disconnect event
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

### Query Bot Status

```python
# Get complete status of all adapters and bots (WebUI friendly)
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
|--------|-------------|
| `online` | Online (receiving events continuously or marked by adapter) |
| `offline` | Offline (marked by adapter or automatically set when system is shutting down) |
| `unknown` | Unknown (registered but status not confirmed) |

### Lifecycle Events

| Event Name | Trigger Time | Data |
|------------|--------------|------|
| `adapter.bot.online` | First automatic discovery of a new Bot | `{platform, bot_id, status}` |
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

> When the system shuts down (`shutdown`), all Bots will be automatically marked as `offline`.



### 核心模块 API

# Core Module API

This document provides a quick reference for the API of ErisPulse core modules, including method signatures and brief descriptions. Click the "Full Documentation" link for each module for detailed usage and examples.

## Storage Module

A key-value storage system based on SQLite, supporting general SQL chainable queries.

### Basic Operations

```python
from ErisPulse import sdk

sdk.storage.set("key", "value")
value = sdk.storage.get("key", default_value)
keys = sdk.storage.keys()
sdk.storage.delete("key")
```

### Batch Operations

```python
sdk.storage.set_multi({"key1": "val1", "key2": "val2"})
values = sdk.storage.get_multi(["key1", "key2"])
sdk.storage.delete_multi(["key1", "key2"])
```

### Transactional Operations

```python
with sdk.storage.transaction():
    sdk.storage.set("key1", "value1")
    sdk.storage.set("key2", "value2")
```

### Attribute Access

```python
sdk.storage.my_key          # Equivalent to sdk.storage.get("my_key")
sdk.storage.my_key = "val"  # Equivalent to sdk.storage.set("my_key", "val")
```

### SQL Chainable Queries

The Storage module provides a chainable-style generic SQL query builder, supporting CRUD operations for custom tables.

```python
sdk.storage.CreateTable("users", {
    "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
    "name": "TEXT NOT NULL",
})

sdk.storage.Table("users").Insert({"name": "Alice"}).Execute()
rows = sdk.storage.Table("users").Select("name").Where("id > ?", 0).Execute()
```

> For the complete chainable query API (Select/Insert/Update/Delete/Where/OrderBy/Limit, AlterTable, transactions, etc.), please refer to [SQL Query Builder](../advanced/sql-builder.md).

### Storage Backend Abstraction

`StorageManager` inherits from the `BaseStorage` abstract base class and supports extending other storage media (Redis, MySQL, etc.).

```python
from ErisPulse.Core.Bases.storage import BaseStorage, BaseQueryBuilder
```

### Asynchronous Interfaces

Both the Storage and Config modules provide asynchronous methods (prefixed with `a`), which can be safely called in asynchronous handlers. Synchronous methods are retained and do not require modification of existing code.

```python
# Asynchronous Storage
value = await sdk.storage.aget("key")
await sdk.storage.aset("key", "value")
await sdk.storage.adelete("key")
keys = await sdk.storage.aget_all_keys()
await sdk.storage.aclear()

# Asynchronous Batch Operations
values = await sdk.storage.aget_multi(["k1", "k2"])
await sdk.storage.aset_multi({"k1": "v1", "k2": "v2"})
await sdk.storage.adelete_multi(["k1", "k2"])

# Asynchronous Configuration
value = await sdk.config.agetConfig("MyModule.key")
await sdk.config.asetConfig("MyModule.key", "value")
await sdk.config.aforce_save()
await sdk.config.areload()
```

## Config Module

Configuration file management in TOML format, supporting key paths separated by dots.

### API Overview

| Method | Description |
|--------|-------------|
| `getConfig(key, default)` | Read configuration, supports dot-separated paths such as `"MyModule.subkey"` |
| `setConfig(key, value, immediate=False)` | Write configuration. If `immediate=True`, save immediately to file |
| `force_save()` | Force writing configuration from memory to file |
| `reload()` | Reload configuration from file |
| `agetConfig(key, default)` | Asynchronously read configuration |
| `asetConfig(key, value, immediate)` | Asynchronously write configuration |
| `aforce_save()` | Asynchronously force save |
| `areload()` | Asynchronously reload |

### Example

```python
config = sdk.config.getConfig("MyModule", {})
value = sdk.config.getConfig("MyModule.timeout", 30)

sdk.config.setConfig("MyModule", {"key": "value"})
sdk.config.setConfig("MyModule.timeout", 60, immediate=True)
```

> `setConfig` uses delayed writing by default (batched save every 5 seconds). Setting `immediate=True` persists changes immediately to the configuration file. Configuration changes trigger the `config.set` lifecycle event.

## Logger Module

A modular logging system based on Rich output, supporting child loggers and module-level control.

### Basic Usage

```python
sdk.logger.debug("Debug information")
sdk.logger.info("Runtime information")
sdk.logger.warning("Warning information")
sdk.logger.error("Error information")
sdk.logger.critical("Critical error")
```

### Child Loggers

```python
child_logger = sdk.logger.get_child("MyModule")
child_logger.info("Submodule log")

child_logger.get_child("utils")  # Supports nesting
```

### Log Level Control

```python
sdk.logger.set_level("DEBUG")                          # Global level
sdk.logger.set_module_level("MyModule", "DEBUG")       # Module level

# Supported levels (from low to high):
# TRACE, DEBUG, INFO, WARNING, ERROR, CRITICAL
# TRACE is the lowest level, outputting detailed internal framework debug information (event dispatching, routing registration, etc.)
sdk.logger.set_level("TRACE")                          # Enable all logs
```

### Log Subscription (Push Mode)

Allows real-time receipt of structured logs by modules such as Dashboard, supporting level filtering and historical log replay.

> **Explicitly subscribe to lower-level logs**: The `min_level` of a subscriber can be lower than the global log level. In this case, lower-level logs are **only pushed to matching subscribers**, not output to the console, nor written to memory, thus avoiding pollution of the main log stream.
>
> ```python
> # Global level is INFO, but DEBUG logs can still be individually subscribed
> @sdk.logger.handler("debug-tracer", min_level="DEBUG")
> def on_debug(log_data: dict): ...
> ```

```python
# Decorator approach
@sdk.logger.handler("my-handler", min_level="INFO")
def on_log(log_data: dict):
    # log_data = {
    #     "timestamp": "2026-06-29T22:00:00.123456",
    #     "level": "WARNING", "level_num": 30,
    #     "module": "ErisPulse.Core.adapter",
    #     "message": "Strict mode: ...",
    # }
    pass

# Direct call approach
sdk.logger.handler("my-handler", min_level="INFO")(on_log)
sdk.logger.remove_handler("my-handler")
```

| Method | Description |
|--------|-------------|
| `handler(id, *, min_level)(func)` | Decorator or direct call. If `id` is empty, it uses the function name. `min_level` can be lower than the global level (lower-level logs are only pushed to matching subscribers, not to console/memory). Registers and automatically replays historical logs |
| `remove_handler(id)` | Removes a subscriber |

### Output Control

```python
sdk.logger.set_output_file("app.log")
sdk.logger.save_logs("log.txt")
sdk.logger.get_logs("MyModule")
sdk.logger.set_memory_limit(1000)
```

## Adapter Module

The adapter manager, responsible for registering, starting, and shutting down adapters for multiple platforms.

### API Overview

| Method | Description |
|--------|-------------|
| `get(platform)` | Get the adapter instance |
| `exists(platform)` | Check if the adapter is registered |
| `enable(platform)` / `disable(platform)` | Enable/Disable the adapter |
| `is_enabled(platform)` | Check if the adapter is enabled |
| `startup(platforms)` / `shutdown(platforms)` | Start/Shutdown the adapter |
| `is_running(platform)` | Check if the adapter is running |
| `list_running()` | List all running adapters |
| `platforms` | Get a list of all platform names |

### Adapter Events

```python
@sdk.adapter.on("message")
async def handle_message(event):
    pass

@sdk.adapter.on("message", platform="yunhu")
async def handle_yunhu_message(event):
    pass
```

### Bot Status Query

```python
sdk.adapter.get_bot_info("telegram", "123456")
sdk.adapter.list_bots("telegram")
sdk.adapter.is_bot_online("telegram", "123456")
sdk.adapter.get_status_summary()
```

> For the complete adapter management API, see [Adapter System API](adapter-system.md).

## Module Module

The module manager, responsible for managing plugin registration, loading, and unloading.

### API Overview

| Method | Description |
|--------|-------------|
| `get(name)` | Get the module instance or a lazy-loaded proxy (returns a proxy when registered but not loaded) |
| `exists(name)` | Check if it is registered |
| `is_loaded(name)` | Check if it is loaded |
| `is_enabled(name)` | Check if it is enabled |
| `enable(name)` / `disable(name)` | Enable/disable the module |
| `load(name)` / `unload(name)` | Load/unload the module |
| `list_registered()` | List registered modules |
| `list_loaded()` | List loaded modules |
| `get_info(name)` | Get module information |
| `get_status_summary()` | Get a module status summary |

### Attribute Access

```python
module = sdk.module.get("ModuleName")
module = sdk.module.ModuleName
module = sdk.ModuleName  # Equivalent shortcut
```

## Lifecycle Module

An event-driven lifecycle manager that provides event submission and listening functionality.

### API Overview

| Method | Description |
|--------|-------------|
| `on(event, priority=0)` | Decorator to register event handlers, supports dot notation matching and wildcard `*` |
| `register(event, handler, priority=0)` | Function-style registration of handlers |
| `unregister(event, handler=None)` | Remove handlers |
| `emit(event, data)` | Asynchronously trigger an event |
| `emit_sync(event, data)` | Synchronously trigger an event |
| `submit_event(event_type, msg, data, source)` | Submit events in standard format (compatible with older versions) |
| `start_timer(id)` / `stop_timer(id)` | Performance timers |

### Example

```python
@sdk.lifecycle.on("module.init")
async def handle_module_init(event_data):
    print(f"Module initialized: {event_data}")

@sdk.lifecycle.on("module")
async def handle_any_module_event(event_data):
    print(f"Module event: {event_data}")

await sdk.lifecycle.emit("custom.event", {"key": "value"})
```

> For the complete list of standard events and detailed usage, please refer to [Lifecycle Management](../advanced/lifecycle.md).

## Router Module

HTTP/WebSocket routing manager, based on FastAPI + Uvicorn, supporting decorator-based routing, middleware, grouping, rate limiting, and CORS.

> For a complete routing API documentation (decorator-based routing, WebSocket, middleware, rate limiting, CORS, security headers, etc.), please refer to [Routing Manager](../advanced/router.md).

### Quick Reference

```python
# HTTP routing
@sdk.router.get("MyModule", "/api")
async def handler(request: HttpRequest):
    return {"status": "ok"}

# WebSocket routing
@sdk.router.ws("MyModule", "/ws")
async def ws_handler(ws: WebSocketConnection):
    async for text in ws.iter_text():
        await ws.send_text(f"Echo: {text}")

# Routing grouping
group = sdk.router.group("MyModule", prefix="/v1")
@group.get("/users")
async def list_users(request: HttpRequest):
    return {"users": []}
```

## HTTP Client Module

A unified network client that aggregates HTTP requests, WebSocket connections, connection pool management, automatic retries, request statistics, and lifecycle event integration.

> For the complete network client documentation (request methods, response objects, WebSocket client, exception hierarchy, etc.), please refer to [Network Client](../advanced/http-client.md).

### Quick Reference

```python
from ErisPulse.Core import client

# HTTP Request
resp = await client.get("https://api.example.com/users")
data = await resp.json()

# WebSocket
ws = await client.ws_connect("wss://example.com/ws")
async for text in ws.iter_text():
    await ws.send_text(f"Echo: {text}")
```

## SDK Debugging

### dump_state()

Exports a snapshot of the current runtime state of the framework, for debugging and diagnostics.

```python
import json
state = sdk.dump_state()
print(json.dumps(state, indent=2, ensure_ascii=False, default=str))
```

The returned structure includes the status of the following subsystems:

| Field | Description |
|-------|-------------|
| `sdk` | SDK initialization status, Python version, runtime platform, timestamp |
| `adapters` | List of registered/started adapters, online status of Bots on each platform |
| `modules` | List of registered/enabled/disabled/lazy-loaded modules |
| `events` | Number of event handlers for each event type (message/notice/request/meta/commands) |
| `router` | Server runtime status, number of HTTP/WebSocket routes |

> Added in 2.5.2



====
高级主题
====


### HTTP 客户端

# Network Client

ErisPulse provides a unified network client that aggregates HTTP requests, WebSocket connections, and connection pool management. Modules and adapters **must** use this client by default, rather than importing third-party libraries such as `aiohttp`, `httpx`, or `requests`.

## Overview

The main features of the network client:

- **Unified Interface**: Provides `get` / `post` / `put` / `delete` / `patch` / `request` methods
- **WebSocket Client**: Establishes a client WebSocket connection via `ws_connect`
- **Automatic Logging**: All requests are automatically logged and statistics are recorded
- **Lifecycle Integration**: Each request triggers the `client.request` lifecycle event, and WS connection triggers the `client.ws.connect` event
- **Retry Support**: Configurable automatic retry count and interval
- **Timeout Control**: Independent connection timeout and request timeout
- **Connection Pool Reuse**: Connection pool management based on aiohttp.ClientSession
- **Exception System**: aiohttp exceptions are automatically converted to ErisPulse exceptions (ClientError system)

## Quick Start

### HTTP Requests

```python
from ErisPulse.Core import client

# GET request
resp = await client.get("https://httpbin.org/get")
data = await resp.json()
print(resp.status)  # 200

# POST request
resp = await client.post(
    "https://httpbin.org/post",
    json={"key": "value"},
)
data = await resp.json()
```

### WebSocket Connection

```python
from ErisPulse.Core import client

ws = await client.ws_connect("wss://example.com/ws")

async for text in ws.iter_text():
    await ws.send_text(f"Echo: {text}")
```

## HttpResponse

All request methods return an `HttpResponse` object:

```python
from ErisPulse.Core import client

resp = await client.get("https://httpbin.org/get")

resp.status       # int - HTTP status code (e.g., 200, 404)
resp.reason       # str | None - status description (e.g., "OK")
resp.headers      # response headers (case-insensitive)
resp.content_type # str | None - Content-Type
resp.url          # final URL (may change due to redirects)
resp.raw          # underlying raw response object (currently aiohttp.ClientResponse)

# Read response body
body = await resp.read()       # bytes
text = await resp.text()       # str
data = await resp.json()       # parse JSON
text = await resp.text("gbk")  # specify encoding
```

## Request Methods

### GET

```python
from ErisPulse.Core import client

resp = await client.get(
    "https://api.example.com/users",
    params={"page": "1", "limit": "10"},
    headers={"Authorization": "Bearer token"},
)
```

### POST

```python
from ErisPulse.Core import client

# JSON request body
resp = await client.post(
    "https://api.example.com/users",
    json={"name": "Alice", "age": 30},
)

# Form request body
resp = await client.post(
    "https://api.example.com/login",
    data={"username": "admin", "password": "123"},
)

# Raw data
resp = await client.post(
    "https://api.example.com/upload",
    data=b"raw bytes",
    headers={"Content-Type": "application/octet-stream"},
)

# File upload (using files parameter, no need to import aiohttp)
# Format: {field_name: file_object/bytes/(filename, file)/(filename, file, content_type)}
resp = await client.post(
    "https://api.example.com/upload",
    data={"description": "Avatar"},            # Optional: include regular form fields
    files={
        "file": ("photo.png", open("photo.png", "rb"), "image/png"),
    },
)

# Simplified syntax: directly pass file object
resp = await client.post(
    "https://api.example.com/upload",
    files={"file": open("photo.png", "rb")},
)

# Upload in-memory data directly (no need to write to disk)
import io

resp = await client.post(
    "https://api.example.com/upload",
    files={"file": ("data.txt", io.BytesIO(b"file content"), "text/plain")},
)
```

### PUT / DELETE / PATCH

```python
from ErisPulse.Core import client

resp = await client.put("https://api.example.com/users/1", json={"name": "Bob"})
resp = await client.delete("https://api.example.com/users/1")
resp = await client.patch("https://api.example.com/users/1", json={"age": 31})
```

### Generic request

```python
from ErisPulse.Core import client

resp = await client.request(
    "OPTIONS",
    "https://api.example.com/resource",
    headers={"Origin": "https://example.com"},
)
```

## Parameters

### HTTP Request Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `url` | `str` | Request URL |
| `params` | `dict[str, str]` | Query parameters (optional) |
| `headers` | `dict[str, str]` | Additional request headers (optional) |
| `data` | `Any` | Request body (form or raw data) (optional) |
| `json` | `Any` | JSON request body (optional) |
| `files` | `dict[str, Any]` | File upload fields (optional, automatically constructs multipart/form-data) |
| `timeout` | `float` | Request timeout (in seconds) (optional, overrides the default value) |
| `max_retries` | `int` | Maximum number of retries for this request (optional, overrides the default value) |

### ws_connect Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `url` | `str` | WebSocket server URL |
| `headers` | `dict[str, str]` | Additional request headers (optional) |
| `heartbeat` | `float` | Heartbeat interval in seconds (optional) |

## Timeouts and Retries

```python
from ErisPulse.Core import Client

# Create a client with custom timeout settings
client = Client(
    timeout=60,           # Total request timeout of 60 seconds
    connect_timeout=5,    # Connection timeout of 5 seconds
    max_retries=3,        # Automatically retry failed requests 3 times
    retry_delay=2,        # Retry interval of 2 seconds
)

# Override timeout for a single request
resp = await client.get("https://slow-api.example.com/data", timeout=120)
```

> [!NOTE]
> The client class was renamed to `Client` starting from version 2.8.0 (`sdk.client` property name remains unchanged); the old name `HttpClient` is retained as a compatibility alias, so old code does not need modification.

## Custom Default Headers

```python
client = Client(
    headers={
        "Authorization": "Bearer token",
        "X-App-Id": "my-app",
    },
    user_agent="MyBot/1.0",
)
```

## Request Statistics

```python
from ErisPulse.Core import client

# View statistics
stats = client.stats
# {"total_requests": 42, "total_errors": 1, "total_bytes_sent": 0, "total_bytes_received": 0}

# Reset statistics
client.reset_stats()
```

## Lifecycle Events

### HTTP Request Events

The `client.request` event is triggered after each request completes and can be used for monitoring:

```python
from ErisPulse.Core import lifecycle

@lifecycle.on("client.request")
async def on_request(event_data):
    print(f"{event_data['method']} {event_data['url']} -> {event_data['status']} ({event_data['elapsed']}s)")
```

### WebSocket Connection Events

The `client.ws.connect` event is triggered after each WebSocket connection is established:

```python
from ErisPulse.Core import lifecycle

@lifecycle.on("client.ws.connect")
async def on_ws_connect(event_data):
    print(f"WS Connection: {event_data['url']}")
```

## Context Management

```python
# As a context manager, automatically closes the session
async with Client(timeout=30) as client:
    resp = await client.get("https://httpbin.org/get")
    data = await resp.json()
```

## WebSocket Client

Establish a WebSocket client connection using `client.ws_connect()`, which returns a `ClientWebSocket` object. The client and server WebSocket share the same base class `WebSocketConnectionBase`, and their send/receive/iter interfaces are completely consistent.

### Basic Usage

```python
from ErisPulse.Core import client

ws = await client.ws_connect("wss://example.com/ws", heartbeat=30)

await ws.send_text("Hello")
await ws.send_bytes(b"\x00\x01\x02")
await ws.send_json({"type": "ping"})
```

### Receiving Messages

#### High-Level Methods (Recommended)

Automatically filter message types, and raise `WebSocketDisconnect` on disconnection:

```python
from ErisPulse.Core import client
from ErisPulse.Core.Bases.errors import WebSocketDisconnect

ws = await client.ws_connect("wss://example.com/ws")

# Single message receive
text = await ws.receive_text()    # str
data = await ws.receive_bytes()   # bytes
obj = await ws.receive_json()     # dict / list

# Iterative receive (automatically stops on disconnection)
async for text in ws.iter_text():
    print(text)

async for data in ws.iter_bytes():
    print(data)

async for obj in ws.iter_json():
    print(obj)
```

#### Low-Level Methods

Use `receive()` and `iter_messages()` to handle raw message types, allowing distinction between TEXT / BINARY / CLOSE / ERROR:

```python
from ErisPulse.Core import client
from ErisPulse.Core.Bases.websocket import WSMessage

ws = await client.ws_connect("wss://example.com/ws")

# Single raw message receive
msg = await ws.receive()
# msg.type  -> WSMessage.TEXT / WSMessage.BINARY / WSMessage.CLOSE / WSMessage.ERROR
# msg.data  -> str | bytes | None

# Iterative raw message receive (automatically stops on CLOSE/ERROR)
async for msg in ws.iter_messages():
    if msg.type == WSMessage.TEXT:
        print(f"Text: {msg.data}")
    elif msg.type == WSMessage.BINARY:
        print(f"Binary: {len(msg.data)} bytes")
```

### WSMessage

`WSMessage` is a unified WebSocket message type independent of the underlying library:

| Property | Type | Description |
|----------|------|-------------|
| `type` | `str` | Message type: `WSMessage.TEXT` / `WSMessage.BINARY` / `WSMessage.CLOSE` / `WSMessage.ERROR` |
| `data` | `Any` | Message data |

### ClientWebSocket Properties

| Property | Type | Description |
|----------|------|-------------|
| `url` | `URL` | Connection URL |
| `headers` | `Headers` | Response headers |
| `closed` | `bool` | Whether the connection is closed |
| `raw` | `object` | Underlying native object (aiohttp.ClientWebSocketResponse) |

### Lifecycle Hooks

Consistent with `server-side WebSocketConnection`, supports `on_disconnect` and `on_error` callbacks:

```python
from ErisPulse.Core import client

ws = await client.ws_connect("wss://example.com/ws")

@ws.on_disconnect
async def handle_disconnect(ws, reason="unknown"):
    print(f"Connection disconnected: {reason}")

@ws.on_error
async def handle_error(ws, error=""):
    print(f"Connection error: {error}")
```

### Closing the Connection

```python
await ws.close(code=1000, reason="Normal closure")
```

## Error System

ErisPulse defines a unified error hierarchy. Requests initiated through `sdk.client` automatically convert underlying aiohttp errors into ErisPulse errors.

> **Backward Compatibility**: Modules/adapters that directly use `aiohttp.ClientSession` are completely unaffected. Error conversion only takes effect when requests are initiated through `sdk.client`. Code that directly uses aiohttp still catches native exceptions such as `aiohttp.ClientError`. Both approaches can coexist.

### Error Hierarchy

```
ErisPulseError
├── ClientError                  # Base class for all HTTP/WS client request errors
│   ├── ClientConnectionError    # Connection failure (DNS resolution failed, connection refused, network unreachable)
│   ├── ClientTimeoutError       # Connection or request timeout
│   └── HTTPStatusError          # HTTP 4xx/5xx status code errors
└── WebSocketError               # Base class for WebSocket errors
    └── WebSocketDisconnect      # WebSocket connection disconnected (applicable to both client and server)
```

### Error Handling

```python
from ErisPulse.Core import client
from ErisPulse.Core.Bases.errors import (
    ClientError,
    ClientConnectionError,
    ClientTimeoutError,
    HTTPStatusError,
    WebSocketDisconnect,
    WebSocketError,
)

# Handling HTTP request errors
try:
    resp = await client.get("https://api.example.com/data")
    data = await resp.json()
except ClientConnectionError:
    print("Cannot connect to the server")
except ClientTimeoutError:
    print("Request timed out")
except ClientError as e:
    print(f"Request failed: {e}")

# Handling WebSocket errors
try:
    ws = await client.ws_connect("wss://example.com/ws")
    async for text in ws.iter_text():
        await ws.send_text(f"Echo: {text}")
except WebSocketDisconnect as e:
    print(f"Connection disconnected: code={e.code}, reason={e.reason}")
except WebSocketError as e:
    print(f"WebSocket error: {e}")
```

### Unified Error Handling

Use `ClientError` to catch all HTTP/WS client request errors in a unified manner:

```python
from ErisPulse.Core.Bases.errors import ClientError

try:
    resp = await client.get("https://api.example.com/data")
except ClientError as e:
    print(f"Client error: {e}")
```

### HTTPStatusError

When you need to check the status code after a request and raise an exception, you can use it manually:

```python
from ErisPulse.Core.Bases.errors import HTTPStatusError

resp = await client.get("https://api.example.com/data")
if resp.status >= 400:
    raise HTTPStatusError(resp.status, await resp.text())
```

## Using in Adapters

Adapters can use the global client or create their own client instance to send requests to platform APIs:

```python
from ErisPulse.Core import client
from ErisPulse.Core.Bases import BaseAdapter
from ErisPulse.Core.Bases.errors import ClientError

class MyAdapter(BaseAdapter):
    async def call_api(self, endpoint, **params):
        try:
            resp = await client.post(
                f"https://api.platform.com/{endpoint}",
                json=params,
                headers={"Authorization": f"Bearer {self.token}"},
            )
            return await resp.json()
        except ClientError as e:
            self.logger.error(f"API call failed: {e}")
            raise
```

> You can also use `sdk.client` via `from ErisPulse import sdk`, which has the same effect.

## Best Practices

1. **Prefer using the global client**: Use `from ErisPulse.Core import client` to obtain the global singleton, which facilitates unified management and monitoring by the framework.
2. **Avoid directly importing aiohttp**: Use `client` instead of `aiohttp.ClientSession`, so that the underlying implementation can be changed in the future without modifying the code. Old code that directly uses aiohttp will continue to work normally, and both approaches can coexist.
3. **Use ErisPulse's exception system**: When making requests via `sdk.client`, catch `ClientError` rather than `aiohttp.ClientError` to ensure that the code does not depend on a specific HTTP library. Code that directly uses aiohttp remains unaffected.
4. **Set timeouts appropriately**: Set reasonable timeout values based on the API response speed to avoid long blocking periods.
5. **Use retry mechanisms**: Enable retries for unstable APIs to improve reliability.
6. **Monitor request statistics**: Monitor request status through `sdk.client.stats` or lifecycle events of `client.request`.
7. **Use advanced methods for WebSocket**: Prefer high-level methods such as `iter_text` / `iter_json`, and only use `iter_messages` when distinguishing between message types is necessary.



### SQL 查询构建器

# SQL Query Builder

The Storage module of ErisPulse provides a chain-style generic SQL query builder, supporting creation, querying, updating, and deletion operations for custom tables.

## Architecture Design

```
Bases/storage.py                    Core/storage.py
┌─────────────────────┐             ┌──────────────────────────┐
│  BaseStorage (ABC)  │◄────────────│  StorageManager          │
│  BaseQueryBuilder   │             │  (SQLite concrete impl)  │
│    (ABC)            │             │                          │
└─────────────────────┘             │  SQLiteQueryBuilder      │
                                    │  AlterTableBuilder       │
                                    └──────────────────────────┘
```

- `BaseStorage` / `BaseQueryBuilder` are abstract base classes that define unified interfaces, supporting future expansion to other storage media (Redis, MySQL, etc.)
- `StorageManager` is the current concrete implementation for SQLite, fully backward compatible

## Import

```python
from ErisPulse import sdk
# or
from ErisPulse.Core import storage

# ABC base classes (for type hinting or custom implementations)
from ErisPulse.Core.Bases.storage import BaseStorage, BaseQueryBuilder
```

## Table Management

### Create Table

```python
sdk.storage.CreateTable("users", {
    "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
    "name": "TEXT NOT NULL",
    "age": "INTEGER DEFAULT 0",
    "email": "TEXT"
})
```

### Check if Table Exists

```python
if sdk.storage.HasTable("users"):
    print("users table already exists")
```

### Drop Table

```python
sdk.storage.DropTable("users")
```

### Alter Table Structure

```python
# Add column
sdk.storage.AlterTable("users").AddColumn("email", "TEXT").Execute()

# Rename table
sdk.storage.AlterTable("users").RenameTo("members").Execute()

# Chain multiple operations
sdk.storage.AlterTable("users") \
    .AddColumn("phone", "TEXT") \
    .AddColumn("address", "TEXT") \
    .Execute()
```

## Chain-style Queries

### Insert Data

```python
# Single row insertion (pass dictionary)
sdk.storage.Table("users").Insert({"name": "Alice", "age": 30}).Execute()

# Batch insertion (pass list of dictionaries)
sdk.storage.Table("users").InsertMulti([
    {"name": "Bob", "age": 25},
    {"name": "Charlie", "age": 35},
    {"name": "Dave", "age": 40}
]).Execute()
```

### Query Data

> **Important**: `Select()` returns `list[tuple]` (list of tuples), not dictionaries. You need to access values by index following column order.

```python
# Query all columns
rows = sdk.storage.Table("users").Select().Execute()
# rows: [(1, "Alice", 30), (2, "Bob", 25), ...]

# Query specific columns
rows = sdk.storage.Table("users").Select("name", "age").Execute()
# rows: [("Alice", 30), ("Bob", 25), ...]

# Access by index
for row in rows:
    name = row[0]   # "Alice"
    age = row[1]    # 30
```

#### Convert tuples to dictionaries

```python
columns = ["id", "name", "age"]
rows = sdk.storage.Table("users").Select(*columns).Execute()

# Method 1: Using zip in loop
for row in rows:
    record = dict(zip(columns, row))
    print(record["name"], record["age"])

# Method 2: Convert to list of dictionaries in one go
records = [dict(zip(columns, row)) for row in rows]
```

#### Get single record

```python
row = sdk.storage.Table("users").Select("name", "age") \
    .Where("id = ?", 1) \
    .ExecuteOne()

# row is tuple or None
if row is not None:
    name = row[0]  # "Alice"
    age = row[1]   # 30
```

### Conditional Filtering

> `Where(condition, *params)` supports passing multiple parameters corresponding to multiple `?` placeholders.

```python
# Single condition (one placeholder, one parameter)
rows = sdk.storage.Table("users").Select("name") \
    .Where("age > ?", 18) \
    .Execute()

# Multiple placeholders in one Where
rows = sdk.storage.Table("users").Select("name") \
    .Where("age > ? AND age < ?", 20, 40) \
    .Execute()

# Multiple Where calls (AND connected)
rows = sdk.storage.Table("users").Select("name") \
    .Where("age > ?", 20) \
    .Where("age < ?", 40) \
    .Execute()
```

### Sorting, Pagination

```python
# Ascending order
rows = sdk.storage.Table("users").Select("name", "age") \
    .OrderBy("name") \
    .Execute()

# Descending order
rows = sdk.storage.Table("users").Select("name") \
    .OrderBy("age", desc=True) \
    .Execute()

# Pagination
rows = sdk.storage.Table("users").Select("name") \
    .OrderBy("id") \
    .Limit(10) \
    .Offset(20) \
    .Execute()
```

### Update Data

```python
# Conditional update
sdk.storage.Table("users") \
    .Update({"age": 31}) \
    .Where("name = ?", "Alice") \
    .Execute()

# Full update
sdk.storage.Table("users") \
    .Update({"status": "active"}) \
    .Execute()
```

### Delete Data

```python
# Conditional deletion
sdk.storage.Table("users") \
    .Delete() \
    .Where("name = ?", "Bob") \
    .Execute()

# Full deletion
sdk.storage.Table("users").Delete().Execute()
```

### Count and Existence Check

```python
# Count
count = sdk.storage.Table("users").Count()
count = sdk.storage.Table("users").Where("age > ?", 18).Count()

# Existence check
exists = sdk.storage.Table("users").Where("name = ?", "Alice").Exists()
```

## Reuse Query Conditions

Use `copy()` for deep copy of the builder to reuse base conditions:

```python
base = sdk.storage.Table("users").Where("age > ?", 20)

# Query based on same conditions
rows = base.copy().Select("name").OrderBy("name").Limit(5).Execute()

# Count based on same conditions
count = base.copy().Count()

# Check existence based on same conditions
exists = base.copy().Where("name = ?", "Alice").Exists()
```

## Reset Builder

```python
builder = sdk.storage.Table("users").Select("name").Where("age > ?", 18)
builder.clear()

# Rebuild query
builder.Select("name", "age").Where("name = ?", "Alice")
rows = builder.Execute()
```

## Using in Transactions

Chain-style operations fully support transactions:

```python
# Commit transaction
with sdk.storage.transaction():
    sdk.storage.Table("users").Insert({"name": "Eve", "age": 22}).Execute()
    sdk.storage.Table("users").Update({"age": 23}).Where("name = ?", "Eve").Execute()

# Rollback example
try:
    with sdk.storage.transaction():
        sdk.storage.Table("users").Delete().Where("name = ?", "Alice").Execute()
        raise Exception("force rollback")
except Exception:
    pass
# Alice's record still exists
```

## Return Value Explanation

| Operation | Return Type | Description |
|-----------|------------|-------------|
| `Select().Execute()` | `list[tuple]` | List of tuples, arranged in column order |
| `Select().ExecuteOne()` | `tuple \| None` | Single tuple or None |
| `Insert().Execute()` | `int` | Affected rows count |
| `InsertMulti().Execute()` | `int` | Inserted rows count |
| `Update().Execute()` | `int` | Affected rows count |
| `Delete().Execute()` | `int` | Affected rows count |
| `Count()` | `int` | Matching rows count |
| `Exists()` | `bool` | Whether it exists |

### Return Value Processing Examples

```python
# Select returns tuples, access by index
rows = sdk.storage.Table("users").Select("name", "age").Execute()
first_name = rows[0][0]  # First row, first column (name)
first_age = rows[0][1]   # First row, second column (age)

# Recommended: Use column names list + zip to convert to dictionary for better readability
cols = ["name", "age"]
rows = sdk.storage.Table("users").Select(*cols).Execute()
for row in rows:
    d = dict(zip(cols, row))
    print(d["name"], d["age"])

# ExecuteOne returns single tuple or None
row = sdk.storage.Table("users").Select("name").Where("id = ?", 1).ExecuteOne()
name = row[0] if row else None

# Insert/Update/Delete return affected rows count
affected = sdk.storage.Table("users").Delete().Where("age < ?", 18).Execute()
print(f"Deleted {affected} records")
```

## Parameterized Queries

All WHERE parameters use `?` placeholders, with parameters passed as subsequent arguments to `Where()` (**not** as tuples or lists):

```python
# Correct ✓ — Multiple parameters passed one by one
sdk.storage.Table("users").Where("age > ? AND name = ?", 18, "Alice").Execute()

# Correct ✓ — Multiple Where calls
sdk.storage.Table("users").Where("age > ?", 18).Where("name = ?", "Alice").Execute()

# Incorrect ✗ — Don't pass tuple
sdk.storage.Table("users").Where("age > ? AND name = ?", (18, "Alice")).Execute()
# This would treat the entire tuple as the value for the first placeholder

# Incorrect ✗ — Has SQL injection risk
sdk.storage.Table("users").Where(f"name = '{user_input}'").Execute()
```

### Where Parameter Passing Rules

```python
# Where(condition: str, *params: Any)
# params are variable arguments, pass them one by one

# Single parameter
.Where("name = ?", "Alice")

# Multiple parameters
.Where("age > ? AND age < ?", 18, 60)

# LIKE query
.Where("name LIKE ?", "A%")

# IN query (requires manually constructing placeholders)
.Where("name IN (?, ?, ?)", "Alice", "Bob", "Charlie")
```

## Custom Storage Backend

Inherit from `BaseStorage` and `BaseQueryBuilder` to implement custom storage backends:

```python
from ErisPulse.Core.Bases.storage import BaseStorage, BaseQueryBuilder

class MyQueryBuilder(BaseQueryBuilder):
    def Execute(self):
        # Implement specific execution logic
        ...

    def ExecuteOne(self):
        ...

    def Count(self):
        ...

    def Exists(self):
        ...


class MyStorage(BaseStorage):
    def get(self, key, default=None):
        ...

    def set(self, key, value):
        ...

    # Implement other abstract methods...
    def Table(self, table_name):
        return MyQueryBuilder(self, table_name)
```



### 生命周期管理

# Lifecycle Management

ErisPulse provides a unified hook/lifecycle system for monitoring the operational status of system components, as well as enabling extended functionalities such as auditing, statistics, and custom logic.

The system supports three trigger methods:
- `await lifecycle.emit("event", data)` — A concise version, which passes arbitrary data.
- `lifecycle.emit_sync("event", data)` — The synchronous version (for non-async contexts).
- `await lifecycle.submit_event("event", ...)` — Compatible with the legacy version, automatically constructs the standard event format.

## Event Handling Mechanism

### Registering Handlers

```python
from ErisPulse import sdk

# Decorator pattern
@sdk.lifecycle.on("module.load")
async def on_module_load(data):
    print(f"Module loaded: {data}")

# Programmatic registration
sdk.lifecycle.register("module.load", on_module_load, priority=10)

# Unregister
sdk.lifecycle.unregister("module.load", on_module_load)

# Batch unregister by owner (automatically called by framework when module/adapter is unloaded)
removed = sdk.lifecycle.unregister_by_owner("MyModule")
print(f"Cleaned up {removed} lifecycle hooks")
```

### Priority

Handlers support the `priority` parameter, where a higher value means earlier execution (consistent with the module loader):

```python
@sdk.lifecycle.on("adapter.event.receive", priority=10)  # Executes first
async def first_handler(data):
    pass

@sdk.lifecycle.on("adapter.event.receive", priority=0)  # Executes later
async def second_handler(data):
    pass
```

### Dot-Notation Events

When a specific event is triggered, its parent events are also triggered:
- Triggering `module.load` also triggers `module`
- Triggering `adapter.event.receive` also triggers `adapter.event` and `adapter`

### Wildcards

Register `*` to capture all events:

```python
@sdk.lifecycle.on("*")
async def on_anything(data):
    print(f"Received event: {data}")
```

### One-Time Registration (`once`)

Since version 2.7.0, handlers registered with `lifecycle.once()` are automatically unregistered after triggering **once**, suitable for one-time hooks like "first ready":

```python
@sdk.lifecycle.once("core.init.complete")
async def on_first_ready(data):
    print("First ready, will not trigger again")
```

- Same priority semantics as `on()` (higher `priority` values execute first)
- Automatically unregisters, no need for manual `unregister`
- Supports both synchronous and asynchronous handlers

### Listener Query (`has_handlers`)

In hot-path short-circuit scenarios, use `has_handlers()` to check if any listeners exist, avoiding unnecessary event traversal and task scheduling:

```python
if sdk.lifecycle.has_handlers("message.sending"):
    await sdk.lifecycle.emit("message.sending", send_ctx)
```

- Covers **exact event names, wildcards `*`, and parent events** for matching
- Returns `False` if there are no listeners, allowing safe skipping of `emit`

## Hook Breakpoint Overview

A typical sequence of lifecycle events for a message from the platform entering the framework to completion:

```mermaid
sequenceDiagram
    participant P as Platform
    participant A as Adapter
    participant F as Framework Core
    participant M as Module Processor

    P->>A: Native event arrives
    A->>F: adapter.event.receive (earliest)
    F->>F: event.pre_process (before handler execution)
    F->>M: Distribute to processor (commands/messages/notifications, etc.)
    M->>M: command.matched / command.executed
    M->>F: event.reply()
    F->>F: message.sending (before sending)
    F->>A: SendDSL send
    A->>P: Send to platform
    A->>F: message.sent (after sending complete)
    F->>F: adapter.event.dispatched (after dispatch complete)
```

The framework provides the following built-in hook breakpoints, allowing users to listen to any breakpoint using `@sdk.lifecycle.on()` to implement custom logic.

### Core Initialization

| Hook Name | Trigger Timing | Data |
|---------|---------|------|
| `core.init.start` | SDK initialization starts | `{}` |
| `core.init.complete` | SDK initialization completes | `{"duration": float, "success": bool, "adapters": {"enabled": [str], "disabled": [str]}, "modules": {"enabled": [str], "disabled": [str]}, "error": str (only on failure)}` |
| `core.uninit.complete` | SDK de-initialization completes | `{"duration": float, "success": bool, "adapters_closed": int, "modules_unloaded": int, "module_properties_cleared": int, "module_properties_to_clear": [str], "error": str (only on failure)}` |

### Configuration Changes

| Hook Name | Trigger Timing | Data |
|---------|---------|------|
| `config.set` | A configuration item is modified | `{"key": str, "old_value": Any, "new_value": Any}` |
| `config.updated` | The entire config tree is detected as changed after editing config.toml externally | `{"old_config": dict, "new_config": dict, "config_file": str}` |

**Example: Configuration Audit**

```python
@sdk.lifecycle.on("config.set")
def audit_config(data):
    print(f"[Audit] {data['key']}: {data['old_value']} -> {data['new_value']}")
```

### Module Lifecycle

| Hook Name | Trigger Timing | Data |
|---------|---------|------|
| `module.register` | Module class registered to manager | `{"module_name": str, "success": bool}` |
| `module.load` | Module loading completes (instance created successfully) | `{"module_name": str, "success": bool}` |
| `module.init` | Module initialization completes (including lazy loading) | `{"module_name": str, "success": bool}` |
| `module.unload` | Module unloaded | `{"module_name": str, "success": bool}` |

### Adapter Lifecycle

| Hook Name | Trigger Timing | Data |
|---------|---------|------|
| `adapter.load` | Adapter registration completes | `{"platform": str, "success": bool}` |
| `adapter.start` | Adapter starts | `{"platforms": [str]}` |
| `adapter.status.change` | Adapter status changes | `{"platform": str, "status": str, "retry_count": int, "error": str (only on failure)}` |
| `adapter.stop` | Adapter stops | `{"platforms": [str]}` |
| `adapter.stopped` | Adapter stop completes | `{"platforms": [str]}` |
| `adapter.bot.online` | Bot goes online | `{"platform": str, "bot_id": str, "info": dict, "status": str}` |
| `adapter.bot.offline` | Bot goes offline | `{"platform": str, "bot_id": str, "status": str}` |

### Event Reception and Processing

| Hook Name | Trigger Timing | Data |
|---------|---------|------|
| `adapter.event.receive` | External platform event received (earliest) | `{"platform": str, "event_type": str, "raw_event_type": str}` |
| `adapter.event.dispatched` | Event dispatch completes | `{"platform": str, "event_type": str, "raw_event_type": str, "onebot_handlers_count": int}` |
| `event.pre_process` | Before event handler execution starts | `{"event_type": str, "platform": str, "detail_type": str}` |

**Example: Event Counting**

```python
event_counter = {}

@sdk.lifecycle.on("adapter.event.receive")
def count_events(data):
    platform = data["platform"]
    event_counter[platform] = event_counter.get(platform, 0) + 1

@sdk.lifecycle.on("adapter.event.dispatched")
def log_unhandled(data):
    if data["onebot_handlers_count"] == 0:
        print(f"[Unhandled] {data['platform']}/{data['event_type']}")
```

### Message Sending

| Hook Name | Trigger Timing | Data |
|---------|---------|------|
| `message.sending` | Message about to send | `{"platform": str, "method": str, "detail_type": str, "target_id": str, "bot_id": str}` |
| `message.sent` | Message sending completes | `{"platform": str, "method": str, "detail_type": str, "target_id": str, "bot_id": str}` |

**Example: Message Sending Audit**

```python
@sdk.lifecycle.on("message.sending")
def log_sending(data):
    print(f"[Sending] -> {data['platform']}/{data['detail_type']}/{data['target_id']} via {data['method']}")
```

### Command System

| Hook Name | Trigger Timing | Data |
|---------|---------|------|
| `command.matched` | Command matched and about to execute | `{"command": str, "args": list[str], "platform": str, "user_id": str}` |
| `command.executed` | Command execution completes | `{"command": str, "args": list[str], "platform": str, "user_id": str, "success": bool, "error": str (only on failure)}` |

**Example: Command Counting**

```python
@sdk.lifecycle.on("command.matched")
def count_commands(data):
    print(f"[Command] /{data['command']} from {data['user_id']}@{data['platform']}")
```

### HTTP Routing

| Hook Name | Trigger Timing | Data |
|---------|---------|------|
| `server.request` | HTTP request received | `{"method": str, "path": str, "client_ip": str}` |
| `server.response` | HTTP response sent | `{"method": str, "path": str, "status_code": int, "client_ip": str}` |

**Example: HTTP Request Logging**

```python
@sdk.lifecycle.on("server.response")
def log_http(data):
    print(f"[HTTP] {data['method']} {data['path']} -> {data['status_code']}")
```

### WebSocket

| Hook Name | Trigger Timing | Data |
|---------|---------|------|
| `server.start` | Router server starts | `{"base_url": str, "host": str, "port": int}` |
| `server.stop` | Router server stops | `{}` |
| `server.websocket.connect` | WebSocket connection established | `{"path": str, "module_name": str, "client_ip": str}` |
| `server.websocket.disconnect` | WebSocket connection disconnected | `{"path": str, "module_name": str, "reason": str, "error": str (only on abnormal)}` |

**Example: WebSocket Connection Monitoring**

```python
@sdk.lifecycle.on("server.websocket.connect")
def on_ws_connect(data):
    print(f"[WS] Connection: {data['path']} from {data['client_ip']}")

@sdk.lifecycle.on("server.websocket.disconnect")
def on_ws_disconnect(data):
    print(f"[WS] Disconnection: {data['path']} ({data['reason']})")
```

## Standard Event Definitions

```python
STANDARD_EVENTS = {
    "core": ["init.start", "init.complete", "uninit.complete"],
    "module": ["load", "init", "unload", "register"],
    "adapter": [
        "load", "start", "status.change", "stop", "stopped",
        "event.receive", "event.dispatched",
        "bot.online", "bot.offline",
    ],
    "server": [
        "start", "stop",
        "request", "response",
        "websocket.connect", "websocket.disconnect",
    ],
    "event": ["pre_process"],
    "message": ["sending", "sent"],
    "command": ["matched", "executed"],
    "config": ["set"],
}
```

## Complete API Reference

### Registration and Unregistration

| Method | Description |
|--------|-------------|
| `@lifecycle.on(event, *, priority=0)` | Decorator to register a handler |
| `lifecycle.register(event, handler, *, priority=0)` | Programmatically register |
| `lifecycle.unregister(event, handler=None)` | Unregister (removes all handlers for the event if handler=None) |

### Triggering

| Method | Description |
|--------|-------------|
| `await lifecycle.emit(event, data=None)` | Asynchronously trigger, handlers that return non-None can modify data |
| `lifecycle.emit_sync(event, data=None)` | Synchronously trigger, asynchronous handlers are scheduled using create_task |
| `await lifecycle.submit_event(event_type, *, source, msg, data)` | Backward compatible, automatically constructs standard event format |

### Utilities

| Method | Description |
|--------|-------------|
| `lifecycle.start_timer(timer_id)` | Start timing |
| `lifecycle.get_duration(timer_id)` | Get elapsed time (in seconds) |
| `lifecycle.stop_timer(timer_id)` | Stop timing and return elapsed time |
| `lifecycle.list_hooks()` | List all registered hooks and their handler counts |
| `lifecycle.clear()` | Clear all handlers and timers |

## Example of Use in Module

```python
from ErisPulse.Core.Bases import BaseModule
from ErisPulse import sdk

class Main(BaseModule):
    async def on_load(self, event):
        # Implement simple message counting
        self.msg_count = 0
        
        @sdk.lifecycle.on("adapter.event.receive")
        async def count(data):
            if data["event_type"] == "message":
                self.msg_count += 1
        
        # Monitor all commands
        @sdk.lifecycle.on("command.matched")
        async def log_cmd(data):
            sdk.logger.info(f"Command executed: /{data['command']} by {data['user_id']}")
        
        # Audit configuration changes
        @sdk.lifecycle.on("config.set")
        def audit(data):
            sdk.logger.info(f"Configuration change: {data['key']} = {data['new_value']}")
```

## Background Task Ownership and Automatic Cancellation

> [!NOTE]  
> This feature requires ErisPulse **2.8.0+**.

If asyncio background tasks created by a module are not cancelled in `on_unload`, they will hold a reference to `self`, preventing the module instance from being garbage collected (leading to old instances lingering after hot reload). The framework provides the following safety mechanisms:

- **`self.spawn(coro)`** (recommended within modules): Tasks are automatically assigned to the module name, and when the module is unloaded, the framework **after** `on_unload` will automatically cancel unfinished tasks and log a warning.
- **`spawn_background(coro)`** (`ErisPulse.runtime`): Automatically captures the current `owner_scope` context; `cancel_owner_tasks(owner)` cancels tasks by owner, and `cancel_all_background_tasks()` is provided as a safety net for `sdk.uninit()`.
- **Adapters**: When closed, they also automatically cancel background tasks under the platform name.

```python
async def on_load(self, event):
    # Recommended: Use self.spawn() for background tasks, which are automatically cancelled by the framework when unloaded
    self.spawn(self._poll())

async def on_unload(self, event):
    # For scenarios requiring fine-grained control, it is still recommended to manually cancel and await cleanup
    if self._poll_task:
        self._poll_task.cancel()
        await asyncio.gather(self._poll_task, return_exceptions=True)

async def _poll(self):
    while True:
        await asyncio.sleep(60)
        ...
```

> [!IMPORTANT]  
> The framework's safety mechanism is a **forced cancellation** (`cancel_owner_tasks`), which occurs after `on_unload` returns. Therefore, tasks requiring graceful cleanup (flushing buffers, persisting state, closing connections) **must** be manually `cancel()` and `await`ed in `on_unload`—do not rely on the safety mechanism to preserve cleanup logic. The framework only guarantees that tasks holding a reference to `self` are not left hanging, not that the cleanup is graceful. For tasks that require awaiting results, directly `await` them instead of dropping them into background tasks.

## Notes

1. **Processors can be synchronous or asynchronous**: The system automatically detects and correctly invokes them.
2. **Data passing**: In `emit()` mode, if a processor returns a non-None value, it modifies the data passed to subsequent processors.
3. **Event naming convention**: It is recommended to use dot-notation for event names to facilitate listening on parent events.
4. **Error isolation**: An exception in a single processor does not affect the execution of other processors.
5. **Synchronous trigger limitation**: In `emit_sync()`, asynchronous processors are scheduled in a fire-and-forget manner, and their return values cannot be returned.
6. **Lifecycle cleanup**: When `sdk.uninit()` is called, all registered processors and timers are cleaned up.
7. **Loading priority**: If you need to listen for events during the framework initialization phase, it is recommended to set a high priority and disable lazy loading.



### 懶加载系统

# Lazy-Loaded Module System

The ErisPulse SDK provides a powerful lazy-loaded module system, allowing modules to be initialized only when they are actually needed, significantly improving application startup speed and memory efficiency.

## Overview

The lazy-loaded module system is one of the core features of ErisPulse. It works in the following ways:

- **Delayed Initialization**: Modules are only loaded and initialized when they are first accessed.
- **Transparent Usage**: For developers, lazy-loaded modules are almost indistinguishable from regular modules in usage.
- **Automatic Dependency Management**: Module dependencies are automatically initialized when they are used.
- **Lifecycle Support**: For modules that inherit from `BaseModule`, lifecycle methods are automatically called.

## How It Works

### The `LazyModule` Class

The core of the lazy-loading system is the `LazyModule` class, which is a wrapper that actually initializes the module only on the first access.

### Initialization Process

When a module is first accessed, `LazyModule` performs the following steps:

1. Retrieves the `__init__` parameter information of the module class.
2. Determines whether to pass a `sdk` reference based on the parameters.
3. Sets the `moduleInfo` property of the module.
4. For modules that inherit from `BaseModule`, calls the `on_load` method.
5. Triggers the `module.init` lifecycle event.

## Event-Driven Lazy Activation (`activate_on`)

> [!NOTE]
> This feature requires ErisPulse **2.8.0+**.

Modules with `lazy_load=True` are loaded only on the **first attribute access** by default. If a module registers command/event handlers, the traditional approach is to set `lazy_load=False` to load immediately. `activate_on` provides a third option: **declare triggers so that the module is automatically activated when the first matching event/command arrives**—the module is neither kept in memory nor loses its trigger entry.

```python
from ErisPulse.loaders import ModuleLoadStrategy

class MyModule(BaseModule):
    @staticmethod
    def get_load_strategy():
        return ModuleLoadStrategy(
            lazy_load=True,
            activate_on=[
                # ---- Event Triggers (passive arrival, no user awareness required)----
                "message",                                    # Type-level: any message event
                {"notice": "group_member_increase"},          # Type + single detail_type
                {"message": ["private", "group"]},            # Type + multiple detail_types

                # ---- Command Triggers (active input, placeholder commands visible in Help)----
                {"command": "roll"},                          # Shorthand: command name
                {"command": ["roll", "dice"]},                # List of command names
                {"command": {                                 # Dict declaration (name is required)
                    "name": "dice",
                    "help": "Roll a dice",
                    "usage": "/dice",
                    "group": "Entertainment",
                    "aliases": ["d"],
                    "hidden": False,
                }},
            ],
        )
```

### Command Dict Declaration Parameters

The dict form mirrors the user-level parameters of the `@command()` decorator, used to register placeholder commands before the module is loaded:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `name` | `str` | **Required** | Command name; must match the `@command(name)` in `on_load`, otherwise the placeholder is unregistered after activation, and the command will not exist |
| `help` | `str` | Fallback chain | Description shown in Help; if not declared, the value is taken from the fallback chain (see below) |
| `usage` | `str` | Auto-generated | Usage line, defaulting to `{prefix}{name}` |
| `group` | `str` | `None` | Command group |
| `aliases` | `list[str]` | `[]` | Aliases are also registered; **inputting an alias will also trigger activation** |
| `hidden` | `bool` | `False` | If `True`, the placeholder command is hidden (aligned with the hidden semantics of the real command after activation); users who know the command name can still trigger it by input |

**Not supported** `priority` / `permission` / `master`: The placeholder command's role is only to trigger activation; permission checks are performed by the real command after activation (blocking permissions at the placeholder stage would make "input command to activate" ineffective).

### Placeholder Command Help Fallback Chain

When the module is not loaded, the Help displays the command description according to the following priority (the first found is used):

1. The command-level `help` declared in the dict (most precise)
2. The `description` from the module's `get_meta()`
3. The `__description__` attribute of the module
4. The `Summary` from the package metadata (PyPI package summary)
5. A generic message: "This command comes from the lazy-loaded module X. The module will be automatically loaded on first use."

### Trigger Semantics

- **Event stub**: Registered to the corresponding event manager with very low priority (`ACTIVATION_STUB_PRIORITY`), acting as a fallback after all regular handlers; after activation, the current event is forwarded to the module's real handler
- **Command stub**: Registers a placeholder command; after activation, the placeholder is unregistered, and the real command takes over the current trigger
- **Reentrancy Prevention**: An `asyncio.Lock` ensures only one activation occurs in concurrent triggers
- **Scope Filtering**: The stub includes the module owner identity, and does not trigger if the module is not enabled for the Bot / session / platform
- **Failure Semantics**: If activation fails, it is not retried, and the stub is also unregistered
- **Deduplication**: When the same command is declared using both shorthand and dict forms, deduplication occurs (dict takes precedence); if the dict lacks `name` or the event `detail_type` is incorrectly written as a dict, a warning is issued and the entry is ignored

> For architecture diagrams and complete semantics, see [Architecture Overview](../architecture.md#event-driven-lazy-activationactivate_on-trigger-architecture).

## Configuring Lazy Loading

### Global Configuration

Enable or disable global lazy loading in the configuration file:

```toml
[ErisPulse.framework]
enable_lazy_loading = true  # true=enable lazy loading (default), false=disable lazy loading
```

### Module-Level Control

Modules can control their loading strategy by implementing the `get_load_strategy()` static method:

```python
from ErisPulse.Core.Bases import BaseModule
from ErisPulse.loaders import ModuleLoadStrategy

class MyModule(BaseModule):
    @staticmethod
    def get_load_strategy():
        """Returns the module loading strategy"""
        return ModuleLoadStrategy(
            lazy_load=False,  # Returning False means immediate loading
            priority=100      # Loading priority, higher values mean higher priority
        )
```

## Using Lazy-Loaded Modules

### Basic Usage

For developers, lazy-loaded modules are almost indistinguishable from regular modules in usage:

```python
# Accessing a lazy-loaded module through the SDK
from ErisPulse import sdk

# The following access will trigger module lazy loading
result = await sdk.my_module.my_method()
```

### Unified Module Access Entry

Whether accessed via SDK attributes, module manager attributes, or through `module.get()`, for "registered but not yet loaded" lazy-loaded modules, the same lazy-loaded proxy is returned. Accessing its attributes will actually trigger initialization:

```python
# All three methods return the same lazy-loaded proxy (when the module is not loaded), with consistent behavior and transparency to the user
sdk.my_module          # Entry point that triggers loading
sdk.module.my_module   # Also returns the lazy-loaded proxy
sdk.module.get("my_module")  # Also returns the lazy-loaded proxy, itself does not trigger loading

# Accessing any attribute of the proxy will actually initialize the module
result = await sdk.my_module.my_method()
```

`module.get()` is a **query** interface and does not trigger loading:
- If the module is loaded → returns the real instance
- If the module is registered but not loaded → returns the lazy-loaded proxy (initialization occurs on attribute access)
- If the module is not registered → returns `None`

To explicitly trigger loading, use `await sdk.load_module("my_module")`.

### Asynchronous Initialization

For modules requiring asynchronous initialization, it is recommended to load them explicitly first:

```python
# Load the module explicitly first
await sdk.load_module("my_module")

# Then use the module
result = await sdk.my_module.my_method()
```

### Synchronous Initialization

For modules that do not require asynchronous initialization, they can be accessed directly:

```python
# Direct access will automatically initialize synchronously
result = sdk.my_module.some_sync_method()
```

## Best Practices

When choosing a loading strategy, refer to the following decision flow:

```mermaid
flowchart TD
    A["Module declaration<br/>get_load_strategy()"] --> B{"Needs to be ready at startup<br/>or frequently triggered?"}
    B -->|"Yes"| C["lazy_load=False<br/>Immediate loading"]
    B -->|"No"| D{"Registered command / event handlers?"}
    D -->|"Yes"| E["lazy_load=True + activate_on<br/>Activate on event/command arrival"]
    D -->|"No"| F["lazy_load=True<br/>Load on first attribute access"]
    C --> G["on_load() called at startup"]
    E --> H["Register stub → instantiate on trigger"]
    F --> I["LazyModule proxy"]
```

### Recommended Scenarios for Lazy Loading (`lazy_load=True`)

- Passive utility modules (such as data query modules, format converters, etc., which are only needed when called by other modules)
- Modules that register command/event handlers but are not frequently used—combine with `activate_on` to declare triggers, so the module is automatically activated when the first matching event/command arrives, without sacrificing lazy loading

### Recommended Scenarios for Disabling Lazy Loading (`lazy_load=False`)

- Modules that need to be ready immediately at startup (such as core modules providing basic services to other modules)
- High-frequency listeners (each message needs to be processed)—`activate_on` forwarding has an activation overhead; immediate loading is more direct in high-frequency scenarios
- Scheduled task modules
- Modules that need to be initialized at application startup

> The `priority` parameter controls the initialization order of immediately loaded modules, with higher values meaning earlier initialization. Modules with the same priority are loaded in registration order.

## Notes

1. If your module uses lazy loading and other modules never call it within ErisPulse, your module will never be initialized.
2. If your module contains listeners for Events or similar active listeners, there are two options: declare `activate_on` triggers (keep lazy loading, activate automatically when events arrive), or declare that it needs to be loaded immediately (`lazy_load=False`), otherwise it may affect your module's normal operations.
3. We do not recommend disabling lazy loading unless there is a special need, as it may cause issues such as dependency management and lifecycle events.
4. In the command dict declaration of `activate_on`, `name` must match the real command name registered in `@command()` in the module's `on_load`—otherwise, after module activation, the placeholder command is unregistered, and the command with inconsistent declaration and implementation will not exist.



### 国际化（i18n）系统

# Internationalization (i18n) System

ErisPulse v2.5.0 introduces full internationalization support. The framework core and CLI interface can automatically switch display text based on your system language, and external modules can also register their own translations.

## Supported Languages

| Language | Code | Description |
|------|------|------|
| Simplified Chinese | `zh-CN` | Default language (framework's native language) |
| Traditional Chinese | `zh-TW` | Traditional Chinese (Hong Kong/Macau/Taiwan) |
| English | `en` | English (general fallback language) |
| 日本語 | `ja` | Japanese |
| Русский | `ru` | Russian |

## Quick Experience

### Switch via Environment Variable

```bash
# Windows PowerShell
$env:ERISPULSE_LANG = "en"
epsdk run

# macOS / Linux
ERISPULSE_LANG=ja epsdk run
```

### Switch via Configuration File

In `config/config.toml`, add:

```toml
[ErisPulse.i18n]
language = "zh-TW"
```

Set to `"auto"` (default) to automatically detect the system language.

### Switch Manually in Code

```python
from ErisPulse import i18n

# Manually set language
i18n.set_language("en")
print(i18n.get_language())  # "en"

# Reset to automatic detection
i18n.reset_language()
```

---

## Language Detection Mechanism

The framework detects the user's language in the following priority order:

1. **Environment variable `ERISPULSE_LANG`** — Highest priority, for testing and temporary switching
2. **Windows API** — `GetUserDefaultLocaleName` (only on Windows, unaffected by tools like Git Bash that override `LANG`)
3. **Environment variables** — `LANGUAGE` > `LC_ALL` > `LC_MESSAGES` > `LANG` (Unix/macOS standard)
4. **System Locale** — `locale.getlocale()` / `locale.getdefaultlocale()`
5. **Fallback** — en (English)

### Nearest Mapping Principle

When the detected language does not match exactly, it is mapped to the nearest supported language:

- `zh-TW`, `zh-HK`, `zh-MO`, `zh-Hant` → **Traditional Chinese**
- All other `zh-*` (e.g., `zh-CN`, `zh-SG`) → **Simplified Chinese**
- `en-US`, `en-GB`, `en-AU` etc. → **English**
- `ja-JP` → **Japanese**
- `ru-RU` → **Russian**
- Other unrecognized languages → **Simplified Chinese (fallback)**

---

## Using i18n in Modules

You can register translation text for your own modules to make them support multiple languages.

### Recommended Approach: Declare Translation Keys via I18nClass (v2.7.0+)

Starting from v2.7.0, modules/adapters can declare translation keys in a nested class `I18nClass`, similar to declaring `ConfigClass`. The framework will automatically register all declared translation keys during loading, without needing to manually call `i18n.register()`.

```python
from dataclasses import dataclass, field

from ErisPulse.Core.Bases import BaseConfig, BaseI18n, BaseModule, I18nKey


class MyModule(BaseModule):
    # Configuration class (optional)
    @dataclass
    class ConfigClass(BaseConfig):
        welcome_msg: str = field(
            default="Welcome",
            metadata={
                # Here we reference the i18n key mymodule.welcome_msg
                "description": {"i18n": "mymodule.welcome_msg", "default": "Welcome message"},
            },
        )

    # Translation key collection class (optional)
    # Declared keys are automatically registered by the framework, with higher priority than default config generated by ConfigClass
    class I18nClass(BaseI18n):
        # Property names are automatically concatenated to form the full key path: <module_name>.<property_name>
        welcome_msg: I18nKey = I18nKey(
            default="Welcome Message",   # Language-agnostic fallback, not registered to any language
            zh_CN="Welcome message",
            en="Welcome Message",
            ja="ウェルカムメッセージ",
            ru="Приветственное сообщение",
            zh_TW="Welcome message",
        )
        # Other translation keys used in business logic
        hello: I18nKey = I18nKey(
            default="Hello, {name}!",
            zh_CN="Hello, {name}!",
            zh_TW="Hello, {name}!",
            en="Hello, {name}!",
            ja="こんにちは、{name}！",
            ru="Привет, {name}!",
        )

        # You can also explicitly specify the full key path (not using property name concatenation)
        custom: I18nKey = I18nKey(
            key="mymodule.deep.nested.key",
            default="Default text",
            zh_CN="Default text",
            zh_TW="Default text",
            en="Default text",
            ja="Default text",
            ru="Default text",
        )
```

#### Why Recommend I18nClass?

| Scenario | Manual i18n.register() | I18nClass Declarative |
|------|-----------------------|------------------|
| i18n key referenced in configuration description | Manual registration required, must be done before configuration generation | Framework automatically registers before configuration generation |
| Multi-language translation declaration | Scattered across various on_load() methods | Centralized in class, clear at a glance |
| Key naming consistency | Prone to spelling errors | Property name as key suffix, IDE can auto-complete |
| Cleanup on unload | Manual unregister_domain() required | Framework uses unified domain registration |

#### I18nClass Key Path Rules

- **Default**: Use ``<module registration name>.<property name>`` as the full key path
  - Example: Module name is ``MyModule``, property is ``welcome`` → key path ``MyModule.welcome``
- **Explicit**: Specify any dot-separated path via the ``I18nKey(key="...")`` parameter
  - Suitable for deeply nested key names (e.g., ``mymodule.config.basic.token``)

#### Using in Adapters

Adapters also support `I18nClass`, with the same usage:

```python
from ErisPulse.Core import BaseAdapter
from ErisPulse.Core.Bases import BaseConfig, BaseI18n, I18nKey


class MyAdapter(BaseAdapter):
    @dataclass
    class ConfigClass(BaseConfig):
        endpoint: str = field(
            default="",
            metadata={
                # Configuration description references the adapter.MyAdapter.endpoint key
                "description": {"i18n": "MyAdapter.endpoint", "default": "API address"},
            },
        )

    class I18nClass(BaseI18n):
        # Central declaration of i18n keys referenced in configuration description and other business keys
        endpoint: I18nKey = I18nKey(
            default="API Endpoint",
            zh_CN="API address",
            zh_TW="API address",
            en="API Endpoint",
            ja="API address",
            ru="API address",
        )
```

The `I18nClass` of the adapter is automatically registered during the `__init__` phase (before configuration template generation), ensuring that i18n keys referenced in configuration descriptions are available.

### Manually Register Custom Translations (Old Approach)

If you do not use `I18nClass`, you can directly call `i18n.register()` to register translation text.

```python
from ErisPulse import i18n

# Register Chinese translations
i18n.register("zh-CN", {
    "my_module.welcome": "Welcome to my module!",
    "my_module.goodbye": "Goodbye!",
    "my_module.hello": "Hello, {name}!",
}, domain="my_module")

# Register English translations
i18n.register("en", {
    "my_module.welcome": "Welcome to my module!",
    "my_module.goodbye": "Goodbye!",
    "my_module.hello": "Hello, {name}!",
}, domain="my_module")
```

### Using Translations

```python
from ErisPulse import i18n

# Simple translation
i18n.t("my_module.welcome")  # Automatically uses current language

# With formatted parameters
i18n.t("my_module.hello", name="Alice")

# Specify default value (returns when translation key does not exist)
i18n.t("my_module.unknown_key", default="Default text")
```

### Using in Module Classes

```python
from dataclasses import dataclass, field
from ErisPulse import i18n
from ErisPulse.Core.Bases import BaseConfig, BaseModule

@dataclass
class MyModuleConfig(BaseConfig):
    welcome_msg: str = field(
        default="Welcome",
        metadata={
            "description": {"i18n": "my_module.welcome_msg", "default": "Welcome message"},
            "ui": {"widget": "text", "group": "basic", "order": 1},
        },
    )

class MyModule(BaseModule):
    ConfigClass = MyModuleConfig

    async def on_load(self, event):
        # Real-time access to configuration (reflects latest value on each access)
        self.logger.info(self.cfg.welcome_msg)
        self.logger.info(i18n.t("my_module.welcome"))

    @command("hello")
    async def hello_handler(self, event):
        name = event.get_user_nickname() or "friend"
        await event.reply(i18n.t("my_module.hello", name=name))

    async def on_unload(self, event):
        pass
```

### Unregistering Translations

```python
# Unregister all translations in a domain
i18n.unregister_domain("my_module")
```

---

## Multi-language Configuration Fields

Starting from v2.5.2, the configuration Schema fully supports i18n. All user-visible text fields can reference i18n keys, and WebUI and other consumers will automatically resolve them to corresponding text based on the current language.

### Supported i18n Fields

| Field | Location | Description |
|------|------|------|
| `description` | field metadata | Field description |
| `options[].label` | `ui.options` | Label for select control options |
| `placeholder` | `ui.placeholder` | Placeholder for input fields |
| `group_labels` | `_schema_meta` | Group display names (Dashboard section titles) |

All use the format `{"i18n": "key", "default": "text"}`. Pure strings are passed through as-is (for backward compatibility).

### Declaring i18n Fields

All user-visible text fields support i18n:

```python
from dataclasses import dataclass, field
from ErisPulse.Core.Bases import BaseConfig

@dataclass
class MyAdapterConfig(BaseConfig):
    # i18n for description
    token: str = field(
        default="",
        metadata={
            "description": {"i18n": "my_adapter.token", "default": "Platform Token"},
            "required": True,
            "secret": True,
            "ui": {
                "widget": "password",
                "group": "basic",
                "order": 1,
                # i18n for placeholder
                "placeholder": {"i18n": "my_adapter.token.ph", "default": "Please enter Token"},
            },
        },
    )
    # i18n for options label
    mode: str = field(
        default="a",
        metadata={
            "description": {"i18n": "my_adapter.mode", "default": "Operating mode"},
            "ui": {
                "widget": "select",
                "group": "basic",
                "order": 2,
                "options": [
                    {"label": {"i18n": "my_adapter.mode.a", "default": "Mode A"}, "value": "a"},
                    {"label": {"i18n": "my_adapter.mode.b", "default": "Mode B"}, "value": "b"},
                ],
            },
        },
    )

    # i18n for group_labels (group display names)
    _schema_meta = {
        "group_labels": {
            "basic": {"i18n": "my_adapter.group.basic", "default": "Basic settings"},
        }
    }
```

`default` is the fallback text — it is shown when the translation is not registered or lookup fails.

### Secret Masking and Configuration Validation

Fields marked as `"secret": True` will automatically receive **masking protection** (from v2.7.0 onwards):

- **Template generation masking**: When `dataclass_to_toml_with_comments()` generates the configuration template, the real value of secret fields is not written to the file (showing an empty placeholder), preventing sensitive information from being written to disk
- **General masking utility**: `redact_secret(value)` replaces non-empty values with `***`, and returns empty values as-is, suitable for use in log output, etc.

```python
from ErisPulse.Core.Bases.config_schema import redact_secret

redact_secret("sk-xxxxxx")  # '***'
redact_secret("")           # ''
```

**Configuration validation** (`validate_config()`) supports the following checks in addition to `required` non-empty checks (from v2.7.0 onwards):

| Validation | Metadata | Example |
|--------|--------|------|
| Type match | Field declared type | `int` field with a string input raises an error |
| Enum constraint | `ui.options` or top-level `options` | Value must be in allowed options |
| Numeric range | Top-level `min` / `max` | `metadata={"min": 1, "max": 65535}` |

```python
from ErisPulse.Core.Bases.config_schema import validate_config

@dataclass
class C(BaseConfig):
    mode: str = field(default="a", metadata={"ui": {"widget": "select", "options": ["a", "b"]}})
    port: int = field(default=80, metadata={"min": 1, "max": 65535})

errors = validate_config(C(mode="x", port=70000))  # Two errors: enum + range
```

### Registering Configuration Translations

The i18n keys for configuration fields are registered the same way as regular translation keys using `i18n.register()`:

```python
from ErisPulse import i18n

# Register Chinese (same as default, but can be different)
i18n.register("zh-CN", {
    "my_adapter.token": "Platform Token",
}, domain="my_adapter")

# Register English
i18n.register("en", {
    "my_adapter.token": "Platform Token",
}, domain="my_adapter")
```
> **Recommended approach**: Use `I18nClass` to declare translation keys; the framework automatically registers them (see the "Recommended Approach" section above),
> no need to manually call `i18n.register()` or `register_config_i18n()`.

A convenient function `register_config_i18n()` is also provided, which automatically extracts keys from the configuration class and registers them:

```python
from ErisPulse.Core.Bases.config_schema import register_config_i18n

# Automatically extract description.default as zh-CN translation
register_config_i18n(MyAdapterConfig, "zh-CN")

# Manually provide English translation
register_config_i18n(MyAdapterConfig, "en", {
    "my_adapter.token": "Platform Token",
})
```

### How WebUI Consumes

`get_config_schema()` returns a schema where the i18n dictionary is passed through as-is. The WebUI frontend can call `i18n.t()` to resolve it based on the current language.

If you need the server to directly resolve it into a string (e.g., for a frontend that doesn't support i18n), use `resolve_config_schema()`, which resolves all i18n fields (`description`, `options[].label`, `placeholder`, `group_labels`) into the current language's text:

```python
from ErisPulse.Core.Bases.config_schema import resolve_config_schema

# All i18n fields are resolved into the current language's text
schema = resolve_config_schema(MyAdapterConfig)
print(schema["fields"]["token"]["description"])    # "Platform Token" or "Platform Token"
print(schema["fields"]["token"]["placeholder"])   # "Please enter Token" or "Enter Token"
print(schema["fields"]["mode"]["options"][0]["label"])  # "Mode A" or "Mode A"
print(schema["group_labels"]["basic"])             # "Basic settings" or "Basic"
```

> `BaseConfig`, `BotAccountConfig`, `register_config_i18n()`, `resolve_config_schema()`
> and other types and utility functions are actually defined in `ErisPulse.Core.Bases.config_schema`.
> `ErisPulse.runtime.config_schema` is retained as a compatibility shim,
> **recommended to import uniformly from `ErisPulse.Core.Bases`** (except i18n translation key related types,
> which are located in `ErisPulse.Core.Bases.i18n_schema`).

## API Reference

### I18nManager

#### Core Methods

| Method | Description |
|------|------|
| `t(key, default=None, **kwargs)` | Get the translated text (`gettext()` is an alias) |
| `set_language(lang)` | Manually set the language |
| `get_language()` | Get the current language |
| `reset_language()` | Reset to automatic detection (and re-detect environment) |
| `get_supported_languages()` | Get the list of all supported languages |
| `has_translation(key, lang=None)` | Check if a translation key exists |
| `register(lang, translations, domain)` | Register custom translations |
| `unregister_domain(domain)` | Unload all translations for a specified domain |
| `reload()` | Reload built-in translations and re-detect language |

#### `t()` Method Details

```python
def t(self, key, /, default=None, **kwargs):
```

- `key` — Translation key (positional argument only, does not conflict with `**kwargs`'s `key=`)
- `default` — Default value returned if translation does not exist, default is `None` (returns the key name itself)
- `**kwargs` — Format parameters, used to fill placeholders in the translation value

Example:

```python
# Translation definition: "greeting": "Hello, {name}! Welcome to {place}."
i18n.t("greeting", name="Alice", place="ErisPulse")
# Returns: "Hello, Alice! Welcome to ErisPulse."
```

### BaseI18n / I18nKey (Declarative Translation Keys)

Starting from v2.7.0, `ErisPulse.Core.Bases` provides a class property-based translation key declaration tool (recommended to import uniformly from `ErisPulse.Core.Bases`):

> ``I18nKey.default`` is a **language-agnostic fallback text** and is not registered to any language.
> To make the translation effective, at least one language parameter must be explicitly passed (e.g., ``zh_CN=`` / ``en=`` / ``ja=`` etc.).
> This allows developers from different countries to freely use their native language to fill in the ``default``, and the framework does not make any assumptions.

| Name | Description |
|------|------|
| `I18nKey(default, *, key=None, zh_CN, zh_TW, en, ja, ru)` | Declaration of a single translation key, `default` is language-agnostic fallback |
| `BaseI18n` | Translation key collection base class (naming aligns with `BaseConfig`), child classes declare multiple `I18nKey` via class properties |
| `BaseI18n.register(prefix="", domain="app")` | Class method: register all declared keys into the i18n system |
| `key` | Alias for `I18nKey` (more concise writing) |

Example usage:

```python
from ErisPulse.Core.Bases import BaseI18n, key

class MyKeys(BaseI18n):
    # Concise alias writing
    hello = key(
        default="Hello",
        zh_CN="Hello",
        zh_TW="Hello",
        en="Hello",
        ja="こんにちは",
        ru="Привет",
    )
    bye = key(
        default="Bye",
        zh_CN="Bye",
        zh_TW="Bye",
        en="Bye",
        ja="さようなら",
        ru="До свидания",
    )

# Independent usage (manual registration)
MyKeys.register(prefix="myapp.", domain="myapp")
```

### Accessing from SDK Instance

```python
from ErisPulse import sdk

# sdk.i18n and directly imported i18n are the same object
sdk.i18n.set_language("en")
print(sdk.i18n.t("core.sdk.init.starting"))
```

---

## Runtime Configuration

### Reading i18n Configuration via API

```python
from ErisPulse.Core.Bases import I18nConfig
from ErisPulse.runtime import get_i18n_config

config = get_i18n_config()
print(config["language"])  # "auto" or specific language code

# I18nConfig is a dataclass, can be used to generate configuration templates
schema = I18nConfig.__dataclass_fields__
```

### Configuration Item Description

In the `[ErisPulse.i18n]` section of `config/config.toml`:

```toml
[ErisPulse.i18n]
# Display language, possible values:
# - "auto"      — Auto-detect system language (default)
# - "zh-CN"     — Simplified Chinese
# - "zh-TW"     — Traditional Chinese
# - "en"        — English
# - "ja"        — Japanese
# - "ru"        — Russian
language = "auto"
```

---

## Best Practices

### Translation Key Naming

It is recommended to use dot-separated namespace formatting:

```
<module_name>.<category>.<description>
```

For example: `my_module.command.hello_desc`, `core.adapter.start_failed`

### Multi-language Coverage

You don't need to provide translations for all languages at once; missing languages will automatically fall back to English, and if English is also missing, the key name itself will be displayed.

### Dynamic Content

For dynamically generated content (such as usernames, quantities, etc.), use `{placeholder}` formatting:

```python
# Translation definition
"user_count": "Current online users: {count} people"

# Usage
i18n.t("user_count", count=len(users))
```

### Log Messages

If your module uses the framework's Logger, these messages will also automatically use the current language:

```python
self.logger.info(i18n.t("my_module.startup"))
```

---

## Relationship with CLI i18n

The CLI has its own **independent** internationalization module (`ErisPulse.CLI.i18n`), completely decoupled from the framework core's internationalization module.

- **Core i18n** — Used by the framework core module, external modules can register translations
- **CLI i18n** — Used internally by the command-line interface, does not share translation data with Core

This design ensures that changes to CLI translations do not affect the stability of the framework core.



### 统一控制面（scope）

# Unified Control Plane (scope)

> [!NOTE]
> This feature requires ErisPulse **2.8.0+**.

The unified control plane answers six questions: **which modules are available, whether to receive events from whom, who can execute a certain command, what text a module processes, which implementation parameters are overridden, and which outbound calls a module is prohibited from initiating**. All control is given to the user: at the **upper level** of module/adapter/command/processor registration (configured via `ErisPulse.scope` or at runtime via `sdk.scope`), the control plane automatically reads and executes event pipelines at each level.

The control plane consolidates the original multiple permission systems and serves as the **only** entry point for permissions/access control in version 2.8.0:

| Dimension | Controls What | Rejection Behavior | Configuration Path |
|------|---------|---------|---------|
| **① Module** | Which modules are available (platform / Bot / session three levels) | Silently ignored (no reply, no claim) | `scope.platforms / bots / sessions` |
| **② Identity** | Whether to receive events (adapter / Bot / session / user four levels) | Completely discarded at the entry (silent) | `scope.identity.*` |
| **③ Command** | Who can execute a certain command (command names support glob) | Reply "insufficient permissions" (explicit) | `scope.commands` |
| **④ Handler** | What text a module's event handler processes | Not triggered (silent) | `scope.handlers` |
| **⑤ Override** | Override module/command implementation parameters (master/hidden/aliases/prefix) | —— (only changes parameters) | `scope.overrides` |
| **⑥ Outbound Action** | Prohibit modules from sending messages / calling standard APIs / handling requests | Failure response (`retcode=34601`) | `scope.actions` |

{!--< tips >!--}
1. Import the singleton via `from ErisPulse.Core import scope` (same object as `sdk.scope`)
2. `scope.is_allowed(platform, bot_id, module, session_id)` checks if a module is available
3. `scope.is_identity_allowed(platform, bot_id, session_id, user_id)` checks if an event is allowed
4. `scope.allow_user("roll*", platform, uid)` / `deny_user(...)` command ACL (supports glob)
5. `scope.override("MyModule", "restart", master=True)` overrides implementation parameters
6. `scope.set_action("MyModule", "send", False)` prohibits a module from replying/sending messages
7. `scope.get_stats()` checks filtering statistics; `scope.get_topology()` checks topology
{!--< /tips >!--}

## Matching Entry Syntax (Unified Across the System)

All "name lists" in the control plane (module names, identity keys, command names) share the same matching syntax (via `ErisPulse.Core.text_match`):

| Syntax | Example | Description |
|------|------|------|
| Exact Name | `"Chat"` | Full value comparison, **case-insensitive** |
| Glob | `"Tool*"`、`"spam_*"` | `*` for any string / `?` for single character / `[seq]` for character set, case-insensitive |
| Regex | `"re:^Danger.*"` | Prefix with `re:` to declare, matches via regex `search`, default case-insensitive |

- Invalid regex silently degrades to "no match" (no error thrown, no crash)
- Decorator parameters (`pattern=` / `regex=`) have fixed semantics: `pattern` is glob, `regex` is raw regex (no `re:` prefix); regex entries in control plane configurations **must** have the `re:` prefix

## Global Fallback: `default_allow`

`default_allow` is the **single global** fallback switch (default `true`), affecting three decision dimensions uniformly:

- **Module dimension**: If no binding is matched → `default_allow` determines allow/deny
- **Identity dimension**: If no strategy is matched → `default_allow` determines allow/deny
- **Command dimension**: If no ACL is configured → `default_allow=true` delegates to the developer's default permission chain; `false` (strict mode) denies commands without configured ACL

Setting it to `false` enables "implicit deny" strict mode: whitelisting management, **all unexplicitly allowed are denied**.

> **Exception**: The **outbound action** dimension is **not** affected by `default_allow`—it is an independent tightening switch, defaulting to allow all, only explicitly `false` disables (framework-level owner-empty calls are always allowed). This strict global mode will not accidentally cut off all module message replies.

## Configuration File

```toml
[ErisPulse.scope]
default_allow = true        # Global fallback (false = implicit deny strict mode)
cache_size = 1024           # LRU cache size

# ── ① Module dimension (priority: session > Bot > platform) ──
[ErisPulse.scope.platforms.onebot11]
modules = ["Chat", "Tool*"]   # Whitelist: exact names / glob / re: regex
blocked = ["re:^Danger"]
[ErisPulse.scope.bots.onebot11."123456"]
modules = ["Chat"]
[ErisPulse.scope.sessions.onebot11."789012345"]
modules = ["Chat"]

# ── ② Identity dimension (priority: user > session > Bot > adapter) ──
[ErisPulse.scope.identity.adapters.onebot11]
deny = true                   # Discard all events from the entire adapter
[ErisPulse.scope.identity.bots.onebot11."123456"]
deny = true
[ErisPulse.scope.identity.sessions.onebot11."g_blocked"]
deny = true
[ErisPulse.scope.identity.users.onebot11]
allow = ["u_admin"]           # User keys support glob / re: regex
deny = ["u_bad", "spam_*"]

# ── ③ Command dimension (command names support glob) ──
[ErisPulse.scope.commands."roll*"]
allow = ["onebot11:u_vip"]    # User identifier "platform:user_id"
deny = ["onebot11:u_bad"]

# ── ④ Handler/Text dimension ──
[ErisPulse.scope.handlers.MyModule]
pattern = "签到*"             # AND with code-side pattern/regex conditions
regex = "re:\\d+\\s*元"

# ── ⑤ Implementation Parameter Override ──
[ErisPulse.scope.overrides.MyModule.restart]
master = true                 # Only framework owner can use
hidden = true                 # Hide in help
aliases = ["rs"]              # Append alias
prefix = "!"                  # Append trigger prefix

# ── ⑥ Outbound Action Dimension (default allow all, only explicitly disable) ──
[ErisPulse.scope.actions.MyModule]
send = false                  # Prohibit MyModule from replying/actively sending messages
api = false                   # Prohibit MyModule from calling standard APIs (including call escape)
request = false               # Prohibit MyModule from handling request operations accept/reject
```

## ① Module Dimension

Answers "which modules are available in a certain context." By default, all are open; filtering starts only after binding is configured, and **modules and adapters require no changes**.

```mermaid
flowchart TD
    A["Event arrives at a module's handler/command"] --> B{"scope.is_allowed<br/>(platform, bot, module, session)"}
    B --> C{"Find effective binding<br/>Session level > Bot level > Platform level"}
    C -->|"Matched"| D["blocked matched → Deny<br/>modules non-empty → Only whitelist allowed<br/>Both empty → default_allow"]
    C -->|"Not matched"| E["default_allow (default true = allow)"]
    D -->|"Deny"| Z["Silently ignored<br/>(No reply, no claim, only TRACE log visible)"]
```

- **Resolution priority**: Session level > Bot level > Platform level, with higher priority bindings **completely overriding** lower ones
- **Silent semantics**: Commands and handlers of filtered modules do not trigger, reply, or claim (to prevent cross-command mis-matches), visible only in TRACE-level logs (`core.scope.denied`)
- **Framework-level handlers** (`scope_exempt=True` or owner is empty) are unaffected; module names that are empty (framework-level resources) are always allowed

## ② Identity Dimension (Event Admission)

Answers "whose events are received." Events denied are **completely discarded at the distribution entry**—they do not enter middleware or any handler (including framework-level), visible only in TRACE-level logs (`core.scope.identity_denied`).

- **Resolution priority**: User > Session > Bot > Adapter, taking the most specific configured strategy; deny takes precedence over allow
- Each binding level is a binary strategy: `{ allow = true }` or `{ deny = true }`
- User keys support glob / regex (e.g., `"spam_*"` to block a batch of spam users)
- Typical usage—上级 deny, individual allow for "exceptional allowance":

```toml
[ErisPulse.scope.identity.adapters.onebot11]
deny = true
[ErisPulse.scope.identity.users.onebot11]
allow = ["u_admin"]   # Even if adapter-level is denied, u_admin's events are still allowed
```

## ③ Command Dimension (Command ACL)

Answers "who can execute a certain command." The decision order is: **deny matched → deny; allow whitelist non-empty and not matched → deny; neither configured → follow `default_allow`** (true delegates to the developer's default permission chain). Denied commands will explicitly reply "insufficient permissions."

- Command names support glob: `"roll*"` covers a family of commands like `roll` and `roll_dice` with one rule
- Exact keys take precedence over glob keys (`commands.roll` matched, `commands."roll*"` not checked)
- User identifier format `"platform:user_id"` (consistent with the framework owner system)
- This dimension is **only an additional gate for user-side**, connected with the command's `master` / `permission` parameters: After passing ACL, the default permission chain declared by the developer is still followed (this default chain can be adjusted via ⑤ override)

## ④ Handler/Text Dimension

Filters "what text a module processes": After configuring `pattern` / `regex` for a module, all its event handlers only trigger when the text matches (AND with code-side conditions, both must be satisfied). This is suitable for narrowing the trigger range without changing module code.

```toml
[ErisPulse.scope.handlers.ChatModule]
pattern = "闲聊*"     # ChatModule's handlers only respond to messages starting with "闲聊"
```

## ⑤ Implementation Parameter Override

Overrides implementation parameters at the **upper level** of module/command registration, without modifying module code:

```toml
[ErisPulse.scope.overrides.MyModule.restart]
master = true      # Override to allow only framework owner (can also set false to loosen developer's owner restriction)
hidden = true      # Hide in help list
aliases = ["rs"]   #生效别名
```

> Override follows **user priority**: The developer's declared `master` / `hidden` etc. are only default values; after the user explicitly configures here, the user configuration takes precedence (can tighten or loosen). Override only changes **implementation parameters** (master / hidden / aliases / prefix / help / usage etc.). **Disabling a command is not done here**—use the command dimension deny (`scope.commands` or `scope.deny_user()`), to avoid conflicting "disable" semantics.

## ⑥ Outbound Action Dimension (Prohibit Modules from Initiating Outbound Calls)

Constraints on **outbound actions** initiated by modules: message sending / standard API actions / request operations. The three actions correspond to the underlying DSL: `Event.reply` and `Send` (send), `Api` / `call_api` (api), `Request`'s accept/reject (request). Outbound calls initiated by modules during event handler execution carry the module owner, and are uniformly judged by this dimension.

```toml
[ErisPulse.scope.actions.MyModule]
send = false      # Prohibit MyModule from replying/actively sending messages
api = false       # Prohibit MyModule from calling standard API actions (including call escape)
request = false   # Prohibit MyModule from executing accept/reject on request events
```

Judgment semantics: **Default allow all**—if not configured, or owner is empty (internal framework calls), all are allowed; only when explicitly set to `false` is it denied, and denied calls do not initiate any network request, directly returning the standard failure response (`retcode = 34601`, see [api-response §5.3](../standards/api-response.md#53-框架扩展返回码34xxx-平台错误段的低三位自定义)). The three actions are independent, and one can be disabled alone.

```python
# Runtime API
sdk.scope.set_action("MyModule", "send", False)   # Prohibit sending messages
sdk.scope.is_action_allowed("MyModule", "send")   # False
sdk.scope.unset_action("MyModule", "send")        # Restore allow
sdk.scope.get_action_rules("MyModule")            # {"send": False, "api": True, "request": True}
```

## Runtime API

### Module Dimension

```python
from ErisPulse import sdk

# Check
sdk.scope.is_allowed("onebot11", "123456", "Chat")
sdk.scope.is_allowed("onebot11", "123456", "Chat", "789012345")
sdk.scope.is_allowed("onebot11", "123456", None)      # Framework-level resources -> True

# Bind / Unbind
sdk.scope.bind_module("onebot11", "123456", modules=["Chat", "Tool*"])
sdk.scope.bind_module("onebot11", blocked=["Danger"])             # Platform level
sdk.scope.bind_module("onebot11", "123456", "789012345", modules=["Chat"])  # Session level
sdk.scope.bind_module("onebot11", "123456", modules=["Music"], merge=True)  # Merge
sdk.scope.bind_module("onebot11", "123456", modules=["Chat"], persist=False)  # Runtime only
sdk.scope.unbind_module("onebot11", "123456")

# Query
sdk.scope.get("onebot11", "123456")   # {"modules": ["Chat"], "blocked": []}
```

### Identity Dimension

```python
# Check if event is allowed
sdk.scope.is_identity_allowed("onebot11", "123456", "group_9", "u1")

# Bind strategy (hierarchy determined by parameters: user > session > bot > adapter)
sdk.scope.bind_identity("onebot11", user_id="u_bad", deny=True)
sdk.scope.bind_identity("onebot11", user_id="spam_*", deny=True)   # glob
sdk.scope.bind_identity("onebot11", "123456", "group_9", allow=True)
sdk.scope.unbind_identity("onebot11", user_id="u_bad")

# Convenient API for user blacklist
sdk.scope.block_user("onebot11", "u_bad")
sdk.scope.is_user_blocked("onebot11", "u_bad")
sdk.scope.get_blocked_users()        # {"onebot11": ["u_bad"]}
sdk.scope.unblock_user("onebot11", "u_bad")
```

### Command Dimension

```python
sdk.scope.is_command_allowed("roll", "onebot11", "u1")
sdk.scope.allow_user("roll*", "onebot11", "u_vip")   # Command names support glob
sdk.scope.deny_user("roll*", "onebot11", "u_bad")
sdk.scope.get_acl("roll*")
sdk.scope.remove_acl("roll*")

# Can also use command system facade (equivalent delegation)
from ErisPulse.Core.Event import command
command.allow_user("restart", "onebot11", "123456")
```

### Handler and Override Dimensions

```python
sdk.scope.bind_handler("MyModule", pattern="签到*", regex=r"\d+号")
sdk.scope.unbind_handler("MyModule")

sdk.scope.override("MyModule", "restart", master=True, hidden=True)
sdk.scope.get_override("MyModule", "restart")
sdk.scope.remove_override("MyModule", "restart")
```

### General

```python
sdk.scope.list_bindings()   # All bindings
sdk.scope.get_topology()    # Topology (for Dashboard)
sdk.scope.get_stats()
# {"module_calls": .., "module_filtered": .., "identity_checks": .., "identity_denied": ..,
#  "command_checks": .., "command_denied": .., "action_checks": .., "action_denied": ..,
#  "cache_hits": .., "cache_misses": ..}
sdk.scope.reset_stats()
sdk.scope.clear()           # Clear all bindings (in-memory only)
```

## Owner Identity and Custom Identity Source (provider)

The owner system answers "who is the framework owner": The `master=True` parameter of commands and the business layer's `master.is_master()` share the same identity determination, with the determination chain being **configured owner → runtime record → provider chain**.

Owner configuration (`ErisPulse.master.users`, supports global list and platform-specific dict) is detailed in the [configuration documentation](../user-guide/configuration.md#Owner System Configuration). This section focuses on identity determination API and extension points.

### Determination and Runtime Add/Remove

```python
from ErisPulse.Core import master

master.is_master(event)                      # Determine from event
master.is_master("yunhu", "123")             # Explicit determination
master.add("yunhu", "123")                   # Add at runtime (default persistent; persist=False only in-memory)
master.remove("yunhu", "123")                # Remove (default persistent)
master.list()                                # Aggregate: {"global": [...], "<platform>": [...]}
```

### Custom Identity Source (provider)

In addition to configuration, custom identity sources can be registered: `fn(platform, user_id) -> bool`, which are tried in sequence when built-in identity sources (configuration + runtime record) do not match; any provider allowing access is recognized as the owner. This is suitable for integrating with adapter administrator interfaces, database roles, and other external identity systems.

The registration entry `master.provider` supports both decorator and function-based writing styles; unregistration is done via the `unregister()` method on the registered function:

```python
from ErisPulse.Core import master

# Method 1: Decorator (persistent identity source, recommended)
@master.provider
def admin_provider(platform, user_id):
    return user_id in {"999"}     # Custom determination logic

master.is_master("yunhu", "999")   # True
admin_provider.unregister()        # Unregister when no longer needed

# Method 2: Function-based (register during module loading / unregister during unload)
fn = master.provider(admin_provider)
fn.unregister()
```

> Provider exceptions are caught and skipped, not blocking the identity determination chain. Binding instance methods cannot attach `unregister`, so for scenarios requiring paired registration/unregistration, use **module-level functions**.

### User Priority: Owner Scope is Finalized by the User

The command's `master=True` is only a **developer default**: The user can override it in the control plane via `ErisPulse.scope.overrides.<module>.<cmd>.master = true/false` (see above ⑤ Implementation Parameter Override, where user explicit configuration takes effect).

## Cache and Hot Updates

- `is_allowed` / `is_identity_allowed` results are cached with **LRU cache** (`scope.cache_size` is adjustable), and `bind_*` / `unbind_*` / configuration hot updates (`config.updated` / `config.set`) automatically invalidate it
- All dimension configurations take effect **immediately** without restart
- The control plane is "event-by-event" judgment, with no cross-event memory: If the configuration changes, the next event follows the new rule

## Common Issues and Notes

### 1. Configuration Hierarchy and Overriding

- Module dimension: Session level > Bot level > Platform level, with **complete override**. To "allow Chat at the platform level, and add Music at the Bot level," both must be listed at the Bot level
- Identity dimension: User > Session > Bot > Adapter, taking the **most specific** configured strategy (can do exceptional allowance)
- Command dimension: Exact command name takes precedence over glob key

### 2. Prefer Control Plane Over Module Code Changes

Module declarations are "developer default" (`master=True`, `permission=...`, `pattern=...`); control plane declarations are "user final decision." Implementation parameter overrides follow **user priority**: User explicit configuration of `master = true/false` takes effect directly (can tighten or loosen). Developers can tighten restrictions not set by them; control over disabling/allowing is done via command deny / identity allow.

### 3. Module/Command Not Responding

First suspect the control plane rather than the module itself:

```python
from ErisPulse import sdk

print(sdk.scope.is_allowed(event.get_platform(), bot_id, "MyModule", session_id))
print(sdk.scope.is_identity_allowed(event.get_platform(), bot_id, session_id, user_id))
print(sdk.scope.get_stats())   # module_filtered / identity_denied > 0 indicates silent filtering
```

Being filtered is **silent** (module and identity dimensions do not reply, preventing rule exposure), but statistics accumulate; command dimension ACL denial replies "insufficient permissions" explicitly.

### 4. Session Identifier Isolation Across Platforms

`(platform, session_id)` combination is the unique identifier. `scope.sessions.onebot11."789"` only applies to onebot11, not affecting the session with the same `789` on telegram. The same applies to identity dimension user keys.

## Topology Tree API

`ModuleManager.get_topology()` and `AdapterManager.get_topology()` provide module/adapter ownership relationship data, and `sdk.get_topology()` aggregates them (including the control plane's five dimensions):

```python
from ErisPulse import sdk

topology = sdk.get_topology()
# {
#   "modules": {                                   # Module → owned resources
#     "Chat": {
#       "loaded": True, "enabled": True,
#       "commands": ["chat", "translate"],
#       "handlers": {"message": 2, "notice": 1},
#       "routes": {"http": ["/Chat/api"], "ws": [], "sse": []},
#       "lifecycle_hooks": 3,
#     }
#   },
#   "adapters": {                                  # Adapter → Bot → scope
#     "onebot11": {
#       "status": "started", "enabled": True,
#       "bots": {"123456": {"status": "online", "scope": {...}}},
#       "scope": {"modules": [...], "blocked": [...]},
#     }
#   },
#   "scope": {                                     # Unified control plane (five dimensions)
#     "platforms": {...}, "bots": {...}, "sessions": {...},
#     "identity": {"adapters": {...}, "bots": {...}, "sessions": {...}, "users": {...}},
#     "commands": {...}, "handlers": {...}, "overrides": {...},
#   },
# }
```

- Module topology aggregates the commands, event handlers, HTTP/WS/SSE routes, and lifecycle hooks registered by the module, useful for drawing the module resource tree.
- Adapter topology aggregates the status of each adapter, the status of subordinate Bots, and platform-level/Bot-level scope bindings.



### 启动流程与手动控制

# Startup Process and Manual Control

The `await sdk.run()` / `await sdk.init()` methods of ErisPulse encapsulate the entire startup chain into a single line of code. However, when you need complete customization of the startup process (e.g., partial loading, dynamic registration, hot plugging, injecting custom loading strategies), you need to understand what happens inside this chain and how to manually drive each step.

This document breaks down the startup chain into independent components, explains their respective responsibilities and call order, and provides an example of manually performing the complete startup process.

> This document assumes you have already run through [the first bot](../getting-started/first-bot.md) and understand the two `keep_running` modes of `sdk.run()`. This document focuses on the internal breakdown of the `init()` chain, as well as lower-level entry points such as `init()`/`init_task()`/`init_sync()`.

## Overview of SDK Top-Level Entry Points

In addition to the two `keep_running` modes of `run()`, the SDK provides several lower-level initialization entry points, which differ in **asynchronicity, return values, and whether exceptions are wrapped**:

| Entry Point | Asynchronicity | Return Value | Exception Handling | Use Case |
|-------------|----------------|--------------|--------------------|----------|
| `await sdk.run(True)` | async, blocks to maintain | `None` (uninit automatically on shutdown) | Module/adapter errors are intercepted, not crashing the process | Pure bot application |
| `await sdk.run(False)` | async, does not block | `None` (no automatic unloading) | Same as above | Initialize and then execute custom logic |
| `await sdk.init()` | async, requires await | `bool` | Internal capture of component exceptions, returns `False` on failure | Manual control of lifecycle (paired with `uninit()`) |
| `sdk.init_task()` | async, returns Task without blocking | `asyncio.Task` | Same as `init()` | Concurrently execute other initializations, or when event loop is not running |
| `sdk.init_sync()` | **Synchronous**, blocks current thread | `bool` | Same as `init()` | Command-line scripts, synchronous entry without event loop |

> **Common Misconception**: `await sdk.init()` **is not equivalent to** `await sdk.run(keep_running=False)`. Two differences: ① `init()` returns `bool` (returns `False` on failure), `run()` returns `None`; ② `init()` only performs initialization, **does not automatically unload**, while `run()` automatically calls `uninit()` when the event loop ends. Therefore, when you need to manually pair unloading or customize the lifecycle, use `init()` + `uninit()`.

## Overview of the Startup Chain

`sdk.init()` (specifically its internal `Initializer.init()`) initiates the entire framework in the following order:

```mermaid
flowchart TD
    A[0. Prepare Environment<br/>Configuration loading / Exception handling] --> B
    B[1. Parallel Discovery and Loading<br/>AdapterLoader.load / ModuleLoader.load<br/>Internally calls Finder.find_all] --> C
    C[2. Register Adapters<br/>AdapterLoader.register_to_manager] --> D
    D[3. Start Adapters<br/>adapter.startup] --> E
    E[4. Register Modules<br/>ModuleLoader.register_to_manager] --> F
    F[5. Initialize Modules<br/>ModuleLoader.initialize_modules<br/>Instantiation and mounting to sdk] --> G
    G[6. Start Router Server<br/>router.start]
```

Corresponding core components:

| Layer | Component | Responsibility |
|-------|-----------|----------------|
| Discovery | `AdapterFinder` / `ModuleFinder` | **Discover** adapters/modules from entry-points of installed packages |
| Loading | `AdapterLoader` / `ModuleLoader` | Discovery + Import + Reading metadata + Determining enabled/disabled, returning object lists |
| Registration | `*Loader.register_to_manager` | Register objects to corresponding managers |
| Management | `sdk.adapter` / `sdk.module` | Maintain adapter/module instances, provide start/stop interfaces |
| Initialization | `ModuleLoader.initialize_modules` | Create module instances and mount to `sdk` (handling dependency topological sorting) |
| Routing | `sdk.router` | HTTP / WebSocket server |

> **Important**: `Finder` and `Loader` are two layers. The `Loader` internally **already holds** a `Finder` (e.g., `AdapterLoader` has its own `AdapterFinder`, `ModuleLoader` has its own `ModuleFinder`). In most scenarios, you only need to use `Loader`; `Finder` is only used when you need "list without importing."

## Detailed Explanation of Each Component

### 1. Discovery Layer: Finder

The `Finder` is responsible only for "finding which packages provide adapters/modules," without importing or instantiating.

```python
from ErisPulse.finders import AdapterFinder, ModuleFinder

adapter_finder = AdapterFinder()
module_finder = ModuleFinder()

# Find all installed adapters/modules entry-points
adapter_entries = adapter_finder.find_all()    # list[EntryPoint]
module_entries = module_finder.find_all()      # list[EntryPoint]

# Find a single by name
entry = module_finder.find_by_name("MyModule")  # EntryPoint | None
```

Each `EntryPoint` can be loaded via `.load()` to get the corresponding class, but usually you don't need to manually call it—`Loader` handles it.

### 2. Loading Layer: Loader

The `Loader` performs "importing + reading metadata + determining enabled/disabled" on top of the `Finder`.

```python
from ErisPulse.loaders import AdapterLoader, ModuleLoader
from ErisPulse import sdk

adapter_loader = AdapterLoader()
module_loader = ModuleLoader()

# load() internally: calls finder.find_all() → processes each entry-point → returns a triple
adapter_objs, enabled_adapters, disabled_adapters = await adapter_loader.load(sdk.adapter)
module_objs, enabled_modules, disabled_modules = await module_loader.load(sdk.module)
```

The three values returned by `load()`:

| Return Value | Meaning |
|--------------|---------|
| `objs` (`dict`) | Name → Object (adapter class / module wrapper object) |
| `enabled` (`list[str]`) | Names that are enabled (not disabled in configuration) |
| `disabled` (`list[str]`) | Names that are disabled |

#### Diagnostic Information on Loading Failures

When an exception is thrown during the loading or initialization phase of a module/adapter, the framework skips that component and continues loading others, while outputting a **summary of user code frames**, allowing you to locate the error position at the default INFO level without manually re-enabling DEBUG:

```
[ERROR] [ModuleLoader] Failed to load module MyModule from entry-point, skipped: 'NoneType' object has no attribute 'platform'
  → MyModule/Core.py:42 in on_load
      adapter = sdk.platform
  → AttributeError: 'NoneType' object has no attribute 'platform'
  → Note: Increase log level to DEBUG to view full stack trace; check implementation code of module MyModule
```

The diagnostic information is generated by the `ErisPulse.runtime.diagnostics` module, automatically filtering out internal framework frames and retaining only your code frames. If you need to reuse it in custom loading logic:

```python
from ErisPulse.runtime import log_diagnostic

try:
    risky_init()
except Exception as e:
    log_diagnostic(e)  # Automatically extract user code frames and write to ERROR log
```

This module also provides two low-level functions: `extract_user_frame()` (returns structured frame information) and `format_diagnostic_block()` (returns multi-line text).

### 3. Registration Layer: register_to_manager

Register the objects produced by the `Loader` to the manager, so that `sdk.adapter` / `sdk.module` can recognize them.

```python
# Register adapters (returns bool, indicating whether all succeeded)
await adapter_loader.register_to_manager(enabled_adapters, adapter_objs, sdk.adapter)

# Register modules
await module_loader.register_to_manager(enabled_modules, module_objs, sdk.module)
```

After registration, adapters are registered to the adapter manager, and modules are registered to the module manager, but **they are not started/instantiated yet**.

### 4. Start Adapters

```python
# Start all registered adapters
await sdk.adapter.startup()
# Or specify a platform
await sdk.adapter.startup("yunhu")
await sdk.adapter.startup(["yunhu", "telegram"])
```

> Registration ≠ Startup. `register_to_manager` only registers; `startup` calls the adapter's `start()`, establishing a connection with the platform.

### 5. Initialize Modules

Modules have one additional step—they need to be **instantiated** and mounted to `sdk` (so you can call `sdk.MyModule.xxx`). This step also handles module dependencies and topological sorting.

```python
success = await module_loader.initialize_modules(
    enabled_modules, module_objs, sdk.module, sdk
)
```

After successful instantiation, the module appears on `sdk.<ModuleName>`.

### 6. Start Router Server

```python
await sdk.router.start(
    host="0.0.0.0",
    port=8000,
    ssl_certfile=None,
    ssl_keyfile=None,
)
```

The router server is responsible for receiving webhook / WebSocket callbacks from adapters. Without starting it, server-mode adapters cannot receive messages.

## Complete Manual Startup Example

The following code **equivalent to** the core process of `await sdk.init()`, but exposes each step, allowing you to insert custom logic at any step:

```python
import asyncio
from ErisPulse import sdk
from ErisPulse.loaders import AdapterLoader, ModuleLoader

async def manual_startup():
    # 0. Prepare Environment (load configuration, register global exception handling)
    #    _prepare_environment is a pre-step inside init(); manual flow must call it first,
    #    otherwise Loader won't read configuration and will misjudge all adapters/modules as disabled.
    if not await sdk._prepare_environment():
        print("Environment preparation failed")
        return False

    # 1. Create Loaders (each internally holds a Finder)
    adapter_loader = AdapterLoader()
    module_loader = ModuleLoader()

    # 2. Parallel Discovery and Loading (consistent with init() internal gather)
    (adapter_objs, enabled_adapters, disabled_adapters), \
    (module_objs, enabled_modules, disabled_modules) = await asyncio.gather(
        adapter_loader.load(sdk.adapter),
        module_loader.load(sdk.module),
    )

    # 3. Register Adapters
    await adapter_loader.register_to_manager(
        enabled_adapters, adapter_objs, sdk.adapter
    )

    # 4. Start Adapters
    if enabled_adapters:
        await sdk.adapter.startup()

    # 5. Register Modules
    await module_loader.register_to_manager(
        enabled_modules, module_objs, sdk.module
    )

    # 6. Initialize Modules (instantiation + mounting to sdk)
    if enabled_modules:
        await module_loader.initialize_modules(
            enabled_modules, module_objs, sdk.module, sdk
        )

    # 7. Start Router Server
    await sdk.router.start(host="0.0.0.0", port=8000)

    print("Manual startup completed")
    return True

async def main():
    ok = await manual_startup()
    if ok:
        # Block to maintain running (manual flow does not automatically block)
        await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
```

### When to Use Manual Startup?

In most cases, **manual startup is not needed**—`await sdk.run()` already handles all the above steps. Manual startup is only valuable in these scenarios:

- **Partial loading**: Load only specified adapters/modules, skipping others
- **Dynamic registration**: Register new adapters/modules at runtime based on conditions
- **Custom order**: Need to disrupt the default loading order (e.g., start a module before an adapter)
- **Inject strategies**: Inject custom strict mode managers, loading strategies, etc., into Loader
- **Debugging/diagnosis**: Manually drive at a certain step to locate issues when failure occurs

## Runtime Fine-Grained Control

Even after using `sdk.run()` to complete startup, you can still individually control subsystems at runtime without restarting the entire SDK:

### Hot Restart/Stop of Adapters

```python
# Hot restart a specific adapter (repair connection, does not affect other platforms)
await sdk.adapter.shutdown("yunhu")
await sdk.adapter.startup("yunhu")

# Bring up a new platform at runtime
await sdk.adapter.startup("telegram")

# Temporarily take down a platform
await sdk.adapter.shutdown("telegram")
```

> `adapter.startup()` requires the adapter to be **registered** to the manager. Registration occurs inside `init()`/`run()`, so this is fine-grained control after startup.

### Router Server

```python
# Temporarily take down webhook server
await sdk.router.stop()

# Restart (e.g., after changing port)
await sdk.router.start(host="0.0.0.0", port=9000)
```

### Modules on Demand

```python
# Manually load a (possibly lazy-loaded) module
await sdk.load_module("MyModule")
```

## Graceful Shutdown

As of version 2.7.0, `sdk.shutdown()` provides **programmatic graceful shutdown**: set a shutdown event to allow the main loop hanging on `await sdk.run(keep_running=True)` to return, triggering `uninit()` to complete resource cleanup.

```python
# Call from any coroutine to trigger graceful exit (run() hangs and returns, then automatically uninit)
sdk.shutdown()
```

Typical use cases:

```python
async def shutdown_after_idle():
    await asyncio.sleep(3600)
    sdk.shutdown()  # Gracefully exit after 1 hour of idle
```

**Signal Handling**: `run()` internally registers `SIGTERM` / `SIGHUP` handlers, converting system signals into graceful shutdown—when container orchestration (Docker `docker stop`) or `systemd` stops the service, the process completes `uninit()` cleanup instead of being forcibly killed.

- Windows does not support `loop.add_signal_handler`, so the signal handler is automatically skipped (still use `sdk.shutdown()` or Ctrl+C to trigger shutdown)
- Repeatedly calling `sdk.shutdown()` is safe (no operation after the event is set)

## Unload Process

The reverse operation of startup is `await sdk.uninit()`, which cleans up in reverse order:

1. Close all adapters (`adapter.shutdown()`)
2. Unload all modules
3. Clean up all event handlers
4. Clean up managers and module attributes on SDK

In manual startup scenarios, remember to call `uninit()` before exiting to ensure graceful shutdown:

```python
try:
    await asyncio.Event().wait()   # Maintain running
finally:
    await sdk.uninit()
```

## Restart

The SDK provides two restart methods, both do not require you to manually unload first—the framework handles it itself:

| Method | Call | Behavior | Use Case |
|--------|------|----------|----------|
| Hot Restart | `await sdk.restart()` | Same process `uninit()` then `init()` again, reload adapters/modules | Reload configuration, hot update modules |
| Hard Restart | `await sdk.hard_restart()` | `uninit()` then exit process with **exit code 42**, restarted by external supervisor | Suspected memory/resource leaks, need thorough clean restart |

```python
# Hot Restart: Reload within the same process (most commonly used)
await sdk.restart()

# Hard Restart: Exit process, handed over to external supervisor for restarting (see below "Supervisor Guide")
await sdk.hard_restart()
```

> **Two Notes**:
> 1. Both methods execute the restart in a background task, **immediately returning `True` to indicate "restart task scheduled"**, not "restart completed." Actual restart happens in the background to avoid interrupting the current event chain.
> 2. The principle of `hard_restart()` is: uninit and flush configuration, then exit the process with **exit code 42** (`HARD_RESTART_EXIT_CODE`)—**it does not start a new process itself**. It must be restarted by an external supervisor detecting exit code 42. If you directly run `python main.py` without any supervisor, the process exits with code 42 and **does not automatically restart** (the framework will warn).

### When to Use Hard Restart?

Hard restart is not just "a more thorough restart," it is more suitable and even more efficient than hot restart in the following scenarios:

- **Binary library (C extension) side effects**: Hot restart occurs within the same process and cannot release C extensions, open file descriptors, threads, and other process-level resources; hard restart switches to a new process, thoroughly clearing these side effects.
- **Resource leak diagnosis**: Suspected memory or handle leaks, hard restart provides a clean environment.
- **Frequent restarts sensitive to performance**: Hard restart avoids the overhead of unloading and reloading within the same process, actually being more efficient than hot restart.

> The "Framework Restart" feature in the Dashboard management panel internally calls `hard_restart()`.

### Exit Code 42 Contract

Hard restart is cross-process collaboration: **SDK is responsible for exiting (code 42), supervisor is responsible for restarting**.

| Role | Behavior |
|------|----------|
| SDK (when hard restarted) | `uninit()` → flush configuration → `os._exit(42)` |
| Supervisor | Detect child process exit code 42 → restart the same command |

> `sdk.is_supervised()` can query whether the current process is started by a supervisor (detecting environment variable `ERISPULSE_SUPERVISED`). The CLI `run` command injects this marker automatically when starting a subprocess; external supervisors like systemd / Docker do not inject it, so `is_supervised()` returns `False`, and the framework will warn "supervisor not detected" after hard restart.

### Supervisor Guide

Choose a supervisor suitable for you to make hard restart truly effective:

#### 1. CLI run command (development/simple deployment, recommended)

`epsdk run main.py` includes an internal supervision loop: detects child process exit code, restarts immediately if 42; other abnormal exit codes retry with exponential backoff; `Ctrl+C` first gracefully terminates the child process (code 0 is considered normal exit, no restart).

```bash
epsdk run main.py
```

#### 2. systemd (Linux server)

`RestartForceExitStatus=42` makes exit code 42 trigger a restart (default `on-failure` only applies to non-zero codes):

```ini
[Service]
ExecStart=/usr/bin/python3 /opt/mybot/main.py
Restart=on-failure
RestartForceExitStatus=42
RestartSec=2
User=mybot
```

#### 3. Docker / docker-compose

Inside the container, PID 1 is the application process, and exit code 42 causes the container to exit—use the `restart` policy to automatically restart it:

```yaml
services:
  bot:
    build: .
    restart: unless-stopped   # Restart on any exit (including 42)
```

#### 4. PM2 (Node ecosystem operations)

```bash
pm2 start main.py --name mybot --interpreter python3
# 42 is treated as an exit code, PM2 defaults to restart; set restart_delay for debouncing
pm2 set mybot.restart_delay 2000
```

#### 5. supervisord

```ini
[program:mybot]
command=python3 /opt/mybot/main.py
autorestart=true
exitcodes=0,2,42    # 42 also considered "normal exit requiring restart"
```

#### 6. Pure Python Custom Supervisor

```python
import subprocess, sys, time

while True:
    p = subprocess.Popen([sys.executable, "main.py"])
    code = p.wait()
    if code == 42:          # Hard restart request
        time.sleep(0.5)
        continue
    if code == 0:           # Normal exit
        break
    time.sleep(3)           # Abnormal exit, backoff retry
```

> **Behavior without a supervisor**: Running directly with `python main.py`, calling `hard_restart()` exits the process with code 42 and does not restart. In this case, you should integrate any of the supervisors above.



====
技术标准
====


### 会话类型标准

# ErisPulse Session Type Standard

This document defines the session type standards supported by ErisPulse, including receive event types and send target types.

## 1. Core Concepts

### 1.1 Receive Type && Send Type

ErisPulse distinguishes two types of sessions:

- **Receive Type (Receive Type)**: The `detail_type` field for receiving events
- **Send Type (Send Type)**: The target type for the `Send.To()` method when sending messages

### 1.2 Type Mapping Relationship

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
- `private` is the receive type; `user` must be used for sending
- `group`, `channel`, `guild`, and `thread` have the same type for both receiving and sending
- The system automatically performs type conversion, so no manual handling is required (this means you can directly use the received type for sending), but in practice, you don't need to consider these conversions. The existence of the Event wrapper class allows you to directly use the `event.reply()` method without considering type conversion.

## 2. Standard Session Types

### 2.1 OneBot12 Standard Types

#### private
- **Receive Type**: `private`
- **Send Type**: `user`
- **Description**: One-to-one private chat messages
- **ID Field**: `user_id`
- **Applicable Platforms**: All platforms supporting private chats

#### group
- **Receive Type**: `group`
- **Send Type**: `group`
- **Description**: Group chat messages, including various forms of groups (e.g., Telegram supergroup)
- **ID Field**: `group_id`
- **Applicable Platforms**: All platforms supporting group chats

#### user
- **Receive Type**: `user`
- **Send Type**: `user`
- **Description**: User type; some platforms (e.g., Telegram) represent private chats as `user` rather than `private`
- **ID Field**: `user_id`
- **Applicable Platforms**: Telegram and other platforms

### 2.2 ErisPulse Extended Types

#### channel
- **Receive Type**: `channel`
- **Send Type**: `channel`
- **Description**: Channel messages, supporting broadcast-style messages to multiple users
- **ID Field**: `channel_id`
- **Applicable Platforms**: Discord, Telegram, Line, etc.

#### guild
- **Receive Type**: `guild`
- **Send Type**: `guild`
- **Description**: Server/community messages, typically used for Discord Guild-level events
- **ID Field**: `guild_id`
- **Applicable Platforms**: Discord and others

#### thread
- **Receive Type**: `thread`
- **Send Type**: `thread`
- **Description**: Thread/sub-channel messages, used for sub-discussion areas within communities
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

## 4. Custom Type Extension

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

After registration, the system automatically handles type conversion and inference:

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

When an event does not have an explicit `detail_type` field, the system automatically infers the type based on the available ID fields:

> [!NOTE]
> **Behavior change in 2.7.0+**: `detail_type` is only directly adopted if it is a **known session type** (standard or custom). For `notice`/`request` events, the `detail_type` (e.g., `group_member_increase`, `friend_increase`) is a **semantic subtype**, not a session type, and the correct session type will be inferred from the ID fields instead.

### 5.1 Inference Priority

```
Priority (from high to low):
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
# Returns: "group" (group_id is prioritized)

# Event only has user_id
event = {"user_id": "123"}
receive_type = infer_receive_type(event)
# Returns: "private"

# For notice events, detail_type is a semantic subtype; 2.7.0+ will infer from ID fields
event = {"type": "notice", "detail_type": "group_member_increase", "group_id": "123"}
receive_type = infer_receive_type(event)
# Returns: "group" (not "group_member_increase")
```

## 6. API Usage Examples

### 6.1 Sending Messages

```python
from ErisPulse import adapter

# Send to user
await adapter.myplatform.Send.To("user", "123").Text("Hello")

# Send to group
await adapter.myplatform.Send.To("group", "456").Text("Hello")

# Automatically convert private → user (not recommended, may have compatibility issues)
await adapter.myplatform.Send.To("private", "789").Text("Hello")
# Internally automatically converts to: Send.To("user", "789") # Using user as the session type directly is a better choice
```

### 6.2 Event Reply

```python
from ErisPulse.Core.Event import Event

# Event.reply() automatically handles type conversion
await event.reply("Reply content")
# Internally automatically uses the correct send type
```

### 6.3 Command Handling

```python
from ErisPulse.Core.Event import command

@command(name="test")
async def handle_test(event):
    # System automatically handles session types
    # No need to manually determine group_id or user_id
    await event.reply("Command executed successfully")
```

## 7. Core API Reference

### 7.1 Type Conversion

```python
from ErisPulse.Core.Event import convert_to_send_type, convert_to_receive_type

# Receive type → Send type
convert_to_send_type("private")  # → "user"
convert_to_send_type("group")    # → "group"

# Send type → Receive type
convert_to_receive_type("user")   # → "private"
convert_to_receive_type("group")  # → "group"
```

### 7.2 ID Field Query

```python
from ErisPulse.Core.Event import get_id_field, get_receive_type

get_id_field("group")    # → "group_id"
get_id_field("private")  # → "user_id"

get_receive_type("group_id")  # → "group"
get_receive_type("user_id")   # → "private"
```

### 7.3 Get Send Info in One Step

```python
from ErisPulse.Core.Event import get_send_type_and_target_id

event = {"detail_type": "private", "user_id": "123"}
send_type, target_id = get_send_type_and_target_id(event)
# send_type = "user", target_id = "123"

# Directly used with Send.To()
await adapter.Send.To(send_type, target_id).Text("Hello")
```

### 7.4 Get Target ID

```python
from ErisPulse.Core.Event import get_target_id

event = {"detail_type": "group", "group_id": "456"}
get_target_id(event)  # → "456"
```

## 8. Utility Methods

```python
from ErisPulse.Core.Event import (
    is_standard_type,
    is_valid_send_type,
    get_standard_types,
    get_send_types,
    clear_custom_types,
)

is_standard_type("private")     # True
is_standard_type("custom_type") # False

is_valid_send_type("user")      # True
is_valid_send_type("invalid")   # False

get_standard_types()  # {"private", "group", "channel", "guild", "thread", "user"}
get_send_types()      # {"user", "group", "channel", "guild", "thread"}

clear_custom_types()                # Clear all
clear_custom_types(platform="discord")  # Only clear types for the specified platform
```

## 9. Best Practices

### 7.1 Adapter Developers

1. **Use Standard Mapping**: Map to standard types as much as possible, rather than creating new types
2. **Correct Conversion**: Ensure correct mapping between receive and send types
3. **Retain Raw Data**: Keep raw event types in `{platform}_raw`
4. **Document Mapping**: Explain type mapping relationships in adapter documentation

### 7.2 Module Developers

1. **Use Utility Methods**: Use methods like `get_send_type_and_target_id()`
2. **Avoid Hardcoding**: Do not write code like `if group_id else "private"`
3. **Consider All Types**: Code should support all standard types, not just private/group
4. **Flexible Design**: Use event wrapper methods instead of directly accessing fields

### 7.3 Type Inference

- **Prefer detail_type**: Use it if available, do not infer
- **Use Inference Judiciously**: Only infer when no explicit type is available
- **Understand Priority**: Be aware of inference priority to avoid unexpected results

## 10. Common Questions

### Q1: Why must private be converted to user when sending?

A: This is a requirement of the OneBot12 standard. `private` is a receive concept; `user` is more semantically appropriate for sending.

### Q2: How to support new session types?

A: Register custom types using `register_custom_type()` or directly use standard types such as `channel`, `guild`, etc.

### Q3: What if an event has no detail_type?

A: The system automatically infers based on available ID fields. The priority is: group > channel > guild > thread > user.

### Q4: How should adapters map Telegram supergroup?

A: In the adapter's conversion logic, map `supergroup` to the standard `group` type.

### Q5: How to handle special or platform-specific types like email?

A: For non-generic or platform-specific types, use `{platform}_raw` and `{platform}_raw_type` to retain raw data, and let the adapter handle it.

## 11. Related Documentation

- [Event Conversion Standard](event-conversion.md) - Complete event conversion specification
- [Send Method Specification](send-method-spec.md) - Naming and parameter specification for Send methods
- [Adapter Development Guide](../developer-guide/adapters/) - Complete adapter development guide



### 事件转换标准

# Adapter Standardization Conversion Specification

## 1. Core Principles
1.  **Strict Compatibility**: All standard fields must strictly follow the OneBot12 specification.
2.  **Explicit Extension**: Platform-specific features must add the {platform}_ prefix (e.g., yunhu_form).
3.  **Data Integrity**: Original event data must be retained in the {platform}_raw field, and the original event type must be retained in the {platform}_raw_type field.
4.  **Time Consistency**: All timestamps must be converted to 10-digit Unix timestamps (seconds).
5.  **Platform Consistency**: The `platform` item name must match the name/alias registered in ErisPulse.

## 2. Standard Field Requirements

### 2.1 Required Fields
| Field | Type | Description |
|------|------|------|
| id | string | Unique event identifier |
| time | integer | Unix timestamp (seconds) |
| type | string | Event type |
| detail_type | string | Event detail type (see [Session Types Standard](session-types.md)) |
| platform | string | Platform name |
| self | object | Bot's own information |
| self.platform | string | Platform name |
| self.user_id | string | Bot user ID |

**detail_type Specification**:
- Must use ErisPulse standard session types (see [Session Types Standard](session-types.md))
- Supported types: `private`, `group`, `user`, `channel`, `guild`, `thread`
- The adapter is responsible for mapping platform native types to standard types

### 2.2 Message Event Fields
| Field | Type | Description |
|------|------|------|
| message | array | Message segment array |
| alt_message | string | Alternative text for message segments |
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
| request_id | string | Request identifier (**Strongly Recommended**, used for approve/reject operations) |

**`request_id` Field Description**:
- `request_id` is the unique operation identifier for the request event, used to execute approve/reject operations via the `HandleRequest` DSL
- When converting request events, the adapter should map the platform native request identifier to this field
- If the platform itself does not have a request ID, the adapter should generate a unique identifier (e.g., a hash based on timestamp + user_id)
- When `request_id` is missing, `event.approve()` / `event.reject()` will raise `ValueError`

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
  "request_id": "req_abc123",
  "onebot11_raw": {...},
  "onebot11_raw_type": "request"
}
```

## 4. Message Segment Standard

### 4.1 Standard Message Segment

Standard message segment types do **not** add platform prefixes:

| Type | Description | data Field |
|------|------|----------|
| `text` | Plain text | `text: str` |
| `image` | Image | `file: str/bytes`, `url: str` |
| `audio` | Audio | `file: str/bytes`, `url: str` |
| `video` | Video | `file: str/bytes`, `url: str` |
| `file` | File | `file: str/bytes`, `url: str`, `filename: str` |
| `mention` | @user | `user_id: str`, `user_name: str` |
| `reply` | Reply | `message_id: str` |
| `face` | Emoji | `id: str` |
| `location` | Location | `latitude: float`, `longitude: float` |

```json
{
  "type": "text",
  "data": {
    "text": "Hello World"
  }
}
```

### 4.2 Platform Extension Message Segment

Platform-specific message segments need to add platform prefixes:

```json
// Yunhu - Form
{"type": "yunhu_form", "data": {"form_id": "123456", "form_name": "报名表"}}

// Telegram - Sticker
{"type": "telegram_sticker", "data": {"file_id": "CAACAgIAAxkBAA...", "emoji": "😂"}}
```

**Extension Message Segment Requirements**:
1.  **No prefix for internal data fields**: `{"type": "yunhu_form", "data": {"form_id": "..."}}` and NOT `{"type": "yunhu_form", "data": {"yunhu_form_id": "..."}}`
2.  **Provide fallback**: Modules might not recognize extended message segments; the adapter should provide a text alternative in `alt_message`
3.  **Complete documentation**: Every extended message segment must describe the `type`, `data` structure, and use cases in the adapter documentation

## 5. Unknown Event Handling

For unrecognized event types, a warning event should be generated:
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

## 6. Extension Naming Convention

### 6.1 Field Naming

**Rule**: `{platform}_{field_name}`

```
Platform Prefix    Field Name            Full Field Name
────────            ────────              ────────────────
yunhu              command               yunhu_command
telegram            sticker_file_id       telegram_sticker_file_id
onebot11            anonymous             onebot11_anonymous
email               subject               email_subject
```

**Requirements**:
- `platform` must match the platform name exactly when registering the adapter (case sensitive)
- `field_name` uses `snake_case` naming
- Do not use double underscores `__` at the beginning (reserved for Python)
- Do not use the same name as standard fields (e.g., `type`, `time`, `message`, etc.)

### 6.2 Message Segment Type Naming

**Rule**: `{platform}_{segment_type}`

Standard message segment types (`text`, `image`, `audio`, `video`, `mention`, `reply`, etc.) must **not** add platform prefixes. Only platform-specific message segment types need the prefix.

### 6.3 Raw Data Field Naming

The following field names are **reserved fields** that all adapters must follow:

| Reserved Field | Type | Description |
|----------------|------|-------------|
| `{platform}_raw` | `any` | Complete copy of platform raw event data |
| `{platform}_raw_type` | `string` | Platform raw event type identifier |

**Requirements**:
- `{platform}_raw` must be a deep copy of the raw data, not a reference
- `{platform}_raw_type` must be a string, even if the platform uses numeric types, convert to string
- These two fields must exist in all events (as `null` and empty string `""` if unavailable)

### 6.4 Platform Specific Field Examples

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
- Top-level keys must have platform prefixes
- Internal nested fields must **not** add platform prefixes
- Recommended nesting depth should not exceed 3 levels

### 6.6 `self` Field Extension

Standard required fields for the `self` object (platform, user_id) see §2.1. Below are the optional fields extended by ErisPulse:

| Field | Type | Description |
|------|------|------|
| `self.user_name` | `string` | Bot nickname |
| `self.avatar` | `string` | Bot avatar URL |
| `self.account_id` | `string` | Account identifier in multi-account mode |

> **Bot Status Tracking**: Adapters inform the framework of the Bot's connection status by sending `type: "meta"` events. Supported `detail_type`: `connect` (online), `heartbeat` (heartbeat), `disconnect` (offline). The system automatically extracts the Bot metadata from the `self` field for status tracking. Additionally, the `self` field in normal events is automatically discovered. See [Adapter System API - Bot Status Management](../api-reference/adapter-system.md).

---

## 7. Session Type Extension

ErisPulse extends the following session types on top of the OneBot12 standard `private`, `group`:

| Type | OneBot12 Standard | ErisPulse Extension | Description |
|------|:-----------:|:------------:|------|
| `private` | ✅ | — | One-to-one private chat |
| `group` | ✅ | — | Group chat |
| `user` | — | ✅ | User type (Telegram, etc.) |
| `channel` | — | ✅ | Channel (broadcast style) |
| `guild` | — | ✅ | Server / Community |
| `thread` | — | ✅ | Topic / Sub-channel |

**Adapter Custom Type Extension**:

```python
from ErisPulse.Core.Event.session_type import register_custom_type

# Register at adapter startup
register_custom_type(
    receive_type="email",      # detail_type in the receive event
    send_type="email",         # target type when sending
    id_field="email_id",       # corresponding ID field name
    platform="email"           # platform identifier
)
```

**Custom Type Requirements**:
- Must be registered at adapter `start()` and unregistered at `shutdown()`
- `receive_type` should not duplicate standard type names
- `id_field` should follow the `{target}_id` naming pattern

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

    # Access platform extension fields - Method 2: Dot notation (Event wrapper class)
    # event.yunhu_command

    # Access raw data
    raw_data = event.get("yunhu_raw")
    raw_type = event.get_raw_type()

    # Determine platform
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

1.  **Prioritize Standard Fields**: Do not assume extension fields always exist
2.  **Platform Detection**: Determine platform via `event.get_platform()`, not by inferring from the existence of extension fields
3.  **Graceful Degradation**: If an extension message segment cannot be processed, use `alt_message` as a fallback
4.  **Do Not Hardcode Prefixes**: Dynamically concatenate using the `platform` variable

```python
# ✅ Recommended
platform = event.get_platform()
raw_data = event.get(f"{platform}_raw")

# ❌ Not Recommended
raw_data = event.get("yunhu_raw")
```

### 8.4 Request Event Handling

Module developers can operate on request events via `event.approve()` and `event.reject()`:

```python
from ErisPulse.Core.Event import request

# Friend Request: Auto-approve
@request.on_friend_request()
async def handle_friend_request(event):
    user_name = event.get_user_nickname() or event.get_user_id()
    comment = event.get_comment()
    
    # Approve request
    result = await event.approve()
    if result.get("status") == "ok":
        print(f"已同意 {user_name} 的好友请求")
    else:
        print(f"同意好友请求失败: {result.get('message')}")

# Group Invite: Decide based on conditions
@request.on_group_request()
async def handle_group_request(event):
    comment = event.get_comment()
    
    # Reject request
    result = await event.reject(comment="暂不加入新群")
```

**Direct Operation via Adapter** (Suitable for non-event handler scenarios):

```python
from ErisPulse import adapter

# Directly operate via request_id
await adapter.myplatform.Request("req_abc123").accept()
await adapter.myplatform.Request("req_abc123").reject()

# Specify Bot account for operation
await adapter.myplatform.Request("req_abc123").Using("bot1").accept()

# With remark/comment
await adapter.myplatform.Request("req_abc123").accept(comment="欢迎")
```

---

## 9. Session Type Inference for notice / request Events

### 9.1 Background

The `detail_type` of notice events and request events are **semantic subtypes** (e.g., `group_member_increase`, `friend_increase`), not session types (e.g., `group`, `private`).

```
type        detail_type                  Meaning          Session Type
────        ───────────                  ────            ────────
message     group                        Group message    group (detail_type is session type)
message     private                      Private message  private (detail_type is session type)
notice      group_member_increase        Member increase  group (inferred from group_id)
notice      friend_increase              Friend increase  private (inferred from user_id)
request     friend                       Friend request   private (inferred from user_id)
request     group                        Group request    group (detail_type is session type)
```

### 9.2 Inference Rules

The inference order of `infer_receive_type()`:

1. If `detail_type` is a known session type (`private`/`group`/`channel`/`guild`/`thread`/`user`), use directly
2. If `detail_type` is a custom session type, use directly
3. Otherwise (semantic subtypes of notice/request), infer based on ID fields:
   - Has `group_id` → `"group"`
   - Has `channel_id` → `"channel"`
   - Has `guild_id` → `"guild"`
   - Has `thread_id` → `"thread"`
   - Has `user_id` → `"private"`

### 9.3 `event.reply()` Target Inference

The target of `event.reply()` in notice/request events is determined by session type inference:

- Group notice events (containing `group_id`) → Reply to **Group**
- Friend notice events (containing only `user_id`) → Reply to **User Private Chat**

```python
from ErisPulse.Core.Event import notice

@notice.on_group_increase()
async def handle_welcome(event):
    group_id = event.get("group_id")    # "group_789"
    user_id = event.get("user_id")      # "user_456"

    # event.reply() sends to group (group/group_789)
    await event.reply("欢迎入群！")

    # To notify admin (private chat), explicitly specify target:
    await adapter.Send.To("user", "admin_id").Text(f"新成员 {user_id} 加入了 {group_id}")
```

### 9.4 Adapter Development Advice

Ensure notice/request events contain the correct ID fields:

| detail_type | Must contain ID fields | Inferred session type |
|-------------|------------------------|-----------------------|
| `group_member_increase` | `group_id` + `user_id` | `group` |
| `group_member_decrease` | `group_id` + `user_id` | `group` |
| `friend_increase` | `user_id` | `private` |
| `friend_decrease` | `user_id` | `private` |
| `friend` (request) | `user_id` | `private` |
| `group` (request) | `group_id` | `group` |

---

## 10. Related Documentation

- [Platform Features Guide](../platform-guide/README.md) - You can access this document to learn about platform features and known extended events and message segments.
- [Session Types Standard](session-types.md) - Session type definitions and mapping relationships
- [Send Method Specification](send-method-spec.md) - Naming, parameter specifications of Send class methods, and reverse conversion requirements
- [API Response Standard](api-response.md) - Adapter API response format standard
- [API Action Standard](api-action-spec.md) - Unified interface for OneBot12 standard API actions



### API 响应标准

# ErisPulse Adapter Standardized Return Specification

## 1. Description
Why does this specification exist?

To ensure the uniformity of interface responses across platforms and compatibility with OneBot12, the ErisPulse adapter adopts the message sending return structure standard defined by OneBot12 for API response formats.

However, ErisPulse's protocol includes some special definitions:
- 1. In the basic fields, `message_id` is required, but this field is not defined in the OneBot12 standard.
- 2. The return content needs to add a `{platform_name}_raw` field to store the raw response data.

## 2. Basic Return Structure
All action responses must include the following basic fields:

| Field Name | Data Type | Required | Description |
|------------|-----------|----------|-------------|
| status | string | Yes | Execution status, must be "ok" or "failed" |
| retcode | int64 | Yes | Return code, follows OneBot12 return code rules |
| data | any | Yes | Response data, contains the request result on success, null on failure |
| message_id | string | Yes | Message ID, used to identify the message; empty string if not available |
| message | string | Yes | Error message, empty string on success |
| {platform_name}_raw | any | No | Raw response data |

Optional field:
| Field Name | Data Type | Required | Description |
|------------|-----------|----------|-------------|
| echo | string | No | Returns the value of the echo field from the request, if present |

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

#### 1xxxx Request Error
| Error Code | Error Name | Description |
|-------|-------|------|
| 10001 | Bad Request | Invalid action request |
| 10002 | Unsupported Action | Unsupported action request |
| 10003 | Bad Param | Invalid action request parameter |
| 10004 | Unsupported Param | Unsupported action request parameter |
| 10005 | Unsupported Segment | Unsupported message segment type |
| 10006 | Bad Segment Data | Invalid message segment parameter |
| 10007 | Unsupported Segment Data | Unsupported message segment parameter |
| 10101 | Who Am I | Robot account not specified |
| 10102 | Unknown Self | Unknown robot account |

#### 2xxxx Handler Error
| Error Code | Error Name | Description |
|-------|-------|------|
| 20001 | Bad Handler | Action handler implementation error |
| 20002 | Internal Handler Error | Exception thrown during action handler runtime |

#### 3xxxx Execution Error
| Error Code Range | Error Type | Description |
|-----------|---------|------|
| 31xxx | Database Error | Database error |
| 32xxx | Filesystem Error | File system error |
| 33xxx | Network Error | Network error |
| 34xxx | Platform Error | Robot platform error |
| 35xxx | Logic Error | Action logic error |
| 36xxx | I Am Tired | Implementation decided to strike |

#### Reserved Error Ranges
- 4xxxx, 5xxxx: Reserved ranges, should not be used
- 6xxxx–9xxxx: Other error ranges, for custom implementation use

## 4. Implementation Requirements
1. All responses must include the status, retcode, data, and message fields.
2. When the request contains a non-empty echo field, the response must include an echo field with the same value.
3. Return codes must strictly follow the OneBot12 specification.
4. Error messages (message) should be human-readable descriptions.

## 5. Extension Specifications

ErisPulse extends the OneBot12 standard return structure as follows:

### 5.1 `message_id` Required Field

In the OneBot12 standard, `message_id` is located inside the `data` object and is not mandatory. ErisPulse elevates it to a **required** top-level field:

- If `message_id` cannot be obtained, it should be set to an empty string `""`
- Ensure `message_id` is always present, so modules do not need to perform null checks

### 5.2 `{platform}_raw` Raw Response Field

The return value should include the `{platform}_raw` field, which stores a complete deep copy of the raw response data from the platform:

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
- `{platform}_raw` must be a deep copy of the original response, not a reference
- `platform` must exactly match the platform name registered by the adapter (case-sensitive)
- Error information from the original response should also be retained for debugging purposes

### 5.3 Framework Extension Return Codes (Custom Low Three Digits in the 34xxx Platform Error Segment)

The OneBot12 specification allows implementations to define custom low three digits in `3xxxx`. The `34xxx` segment is semantically defined as **Platform Error** (robot platform errors, such as failures caused by platform restrictions). Within `34xxx`, the low three digits are used hierarchically based on responsibility:

| Low Three Digits Segment | Responsibility | Purpose |
|-------------------------|----------------|---------|
| `340xx` | Adapter Implementation | Request operation family (Request Not Found / Already Handled / Not Supported / Permission Denied, see request-action-spec §7) |
| `341xx`～`345xx` | Adapter Implementation | Platform-side permission / risk control / account restrictions (implement custom low three digits, original error in `{platform}_raw`) |
| `346xx` | **ErisPulse Framework (Reserved)** | Framework-level interception and generic failures; adapters/modules should not use these codes |
| `347xx`～`349xx` | Adapter Implementation | Other platform execution errors |

ErisPulse framework currently uses the `346xx` codes:

| Error Code | Error Name | Description |
|------------|------------|-------------|
| 34600 | SDK Failure | Framework-level generic failure (default return code for `make_error()`) |
| 34601 | Action Denied | Outbound action is disabled by the control plane (`scope.actions`), call not initiated, directly return this response |

> Responsibility distinction: `34601` is **framework-level interception before the call** (module does not have permission to initiate the action); `34004` / `34xxx` platform codes are **actions already sent but rejected by the platform** (e.g., Bot lacks permissions, blocked by risk control). When modules check for permission issues, they should check both types: first check `34601` (module itself is disabled by scope), then check `34xxx` (platform-side restrictions).

The return structure follows the standard failure response in §2:

```json
{
    "status": "failed",
    "retcode": 34601,
    "data": null,
    "message_id": "",
    "message": "action 'send' denied by scope.actions"
}
```

### 5.4 Adapter Implementation Checklist

- [ ] Include `status`, `retcode`, `data`, `message_id`, `message` fields
- [ ] Return codes follow the OneBot12 specification (see §3.2)
- [ ] `message_id` is always present (set to empty string if unavailable)
- [ ] `{platform}_raw` contains the raw response data from the platform

## 6. Notes
- For error codes in the 3xxxx range, the last three digits can be defined by the implementation.
- Avoid using reserved error ranges (4xxxx, 5xxxx).
- **`34600` / `34601` are reserved error codes for the ErisPulse framework** (see §5.3); adapters/modules should avoid using them.
- Error messages should be concise and clear for debugging purposes.



### 发送方法规范

# ErisPulse Send Method Specification

This document defines the naming conventions, parameter specifications, and reverse conversion requirements for the Send class methods in the ErisPulse adapter.

## 1. Standard Method Naming

All send methods use **PascalCase (PascalCase)**, with the first letter capitalized.

### 1.1 Standard Send Methods

| Method Name | Description | Parameter Type |
|-------------|-------------|----------------|
| `Text` | Send text message | `str` |
| `Image` | Send image | `bytes` \| `str` (URL/Path) |
| `Voice` | Send voice | `bytes` \| `str` (URL/Path) |
| `Video` | Send video | `bytes` \| `str` (URL/Path) |
| `File` | Send file | `bytes` \| `str` (URL/Path) |
| `At` | Mention user/group | `str` (user_id) |
| `Face` | Send emoji | `str` (emoji) |
| `Reply` | Reply to message | `str` (message_id) |
| `Forward` | Forward message | `str` (message_id) |
| `Markdown` | Send Markdown message | `str` |
| `HTML` | Send HTML message | `str` |
| `Card` | Send card message | `dict` |

### 1.2 Chained Modifier Methods

| Method Name | Description | Parameter Type |
|-------------|-------------|----------------|
| `At` | Mention user (can be called multiple times) | `str` (user_id) |
| `AtAll` | Mention all members | None |
| `Reply` | Reply to message | `str` (message_id) |

### 1.3 Protocol Methods

| Method Name | Description | Required |
|-------------|-------------|----------|
| `Raw_ob12` | Send OneBot12 format message segment | Required |

**`Raw_ob12` is a required method**. One of the core responsibilities of the adapter is to receive OneBot12 standard message segments and convert them into native platform API calls. `Raw_ob12` serves as the unified entry point for reverse conversion (OneBot12 → Platform), ensuring that modules can send messages directly using standard message segments without relying on platform-specific methods.

**Default behavior when `Raw_ob12` is not overridden**: The base class will log an **error-level** message and return a standard error response format (`status: "failed"`, `retcode: 10002`), indicating that the adapter developer must implement this method.

### 1.4 Recommended Extension Naming Convention

If an adapter needs to support sending non-OneBot12 format raw data (such as platform-specific JSON, XML, etc.), the following naming convention is recommended:

| Recommended Method Name | Description |
|-------------------------|-------------|
| `Raw_json` | Send arbitrary JSON data |
| `Raw_xml` | Send arbitrary XML data |

**Note**: These methods are **not** default methods provided by the base class, nor are they mandatory to implement. They are only naming conventions, and adapters can define them as needed. If an adapter does not support these formats, there is no need to define them.

**MessageBuilder**: ErisPulse provides the `MessageBuilder` utility class to easily construct OneBot12 message segment lists, which can be used in conjunction with `Raw_ob12`. See the [MessageBuilder](#11-messagebuilder) section.

## 2. Parameter Specification Details

### 2.1 Media Message Parameter Specification

Media messages (`Image`, `Voice`, `Video`, `File`) support two types of parameters:

#### 2.1.1 String Parameter (URL or File Path)

**Format:** `str`

**Supported Types:**
- **URL**: Network resource address (e.g., `https://example.com/image.jpg`)
- **File Path**: Local file path (e.g., `/path/to/file.jpg` or `C:\\path\\to\\file.jpg`)

**Use Cases:**
- The file is already online, send the URL directly
- The file is on the local disk, send the file path
- Want the adapter to handle file upload automatically

**Recommendation:** Prefer using URLs; if URLs are unavailable, use local file paths.

**Examples:**
```python
# Using URL
send.Image("https://example.com/image.jpg")

# Using local file path
send.Image("/path/to/local/image.jpg")
send.Image("C:\\path\\to\\local\\image.jpg")
```

#### 2.1.2 Binary Data Parameter

**Format:** `bytes`

**Use Cases:**
- The file is already in memory (e.g., downloaded from the network, read from another source)
- Need to process the file before sending (e.g., compress images, convert formats)
- Avoid repeated file reading

**Notes:**
- Uploading large files may consume significant memory
- It is recommended to set reasonable file size limits

**Example:**
```python
# Reading from the network and sending
import requests
image_data = requests.get("https://example.com/image.jpg").content
send.Image(image_data)

# Reading from a file and sending
with open("/path/to/local/image.jpg", "rb") as f:
    image_data = f.read()
send.Image(image_data)
```

#### 2.1.3 Parameter Processing Priority

When an adapter receives media message parameters, it should process them in the following order:

1. **URL Parameter**: Use the URL directly (some platform adapters may have operations to download URLs and then upload them)
2. **File Path**: Check if it is a local path; if so, upload the file
3. **Binary Data**: Upload the binary data directly

**Adapter Implementation Suggestion:**
```python
def Image(self, image: Union[bytes, str]):
    if isinstance(image, str):
        # Determine if it is a URL or a local path
        if image.startswith(("http://", "https://")):
            # Directly send URL
            return self._send_image_by_url(image)
        else:
            # Local path, read and upload
            with open(image, "rb") as f:
                return self._upload_image(f.read())
    elif isinstance(image, bytes):
        # Binary data, upload directly
        return self._upload_image(image)
```

### 2.2 @User Parameter Specification

**Method:** `At` (Modifier method)

**Parameter:** `user_id` (`str`)

**Requirements:**
- `user_id` should be a string type user identifier
- Different platforms may have different `user_id` formats (numbers, UUID, strings, etc.)
- The adapter is responsible for converting `user_id` into the platform-specific format
- Ensure the actual send method call is placed at the end

**Example:**
```python
# Single @ user
Send.To("group", "g123").At("123456").Text("Hello")

# Multiple @ users (chained call)
send.To("group", "g123").At("123456").At("789012").Text("Hello everyone")
```

### 2.3 Reply Message Parameter Specification

**Method:** `Reply` (Modifier method)

**Parameter:** `message_id` (`str`)

**Requirements:**
- `message_id` should be a string type message identifier
- Should be the ID of a previously received message
- Some platforms may not support reply functionality; the adapter should gracefully degrade

**Example:**
```python
send.To("group", "g123").Reply("msg_123456").Text("Received")
```

## 3. Platform-Specific Method Naming

**Do not** directly add platform-prefixed methods in the Send class. It is recommended to use generic method names or `Raw_{protocol}` methods.

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

**Extension Method Requirements**:
- Method names use PascalCase, without platform prefix
- Must return an `asyncio.Task` object
- Must provide complete type annotations and docstrings
- Parameter design should be as consistent as possible with standard method styles

## 4. Parameter Naming Specification

| Parameter Name | Description | Type |
|----------------|-------------|------|
| `text` | Text content | `str` |
| `url` / `file` | File URL or binary data | `str` / `bytes` |
| `user_id` | User ID | `str` / `int` |
| `group_id` | Group ID | `str` / `int` |
| `message_id` | Message ID | `str` |
| `data` | Data object (e.g., card data) | `dict` |

## 5. Return Value Specification

- **Send methods** (e.g., `Text`, `Image`): Must return an `asyncio.Task` object
- **Modifier methods** (e.g., `At`, `Reply`, `AtAll`): Must return `self` to support chained calls

---

## 6. Reverse Conversion Specification (OneBot12 → Platform)

The adapter must not only convert platform-native events into OneBot12 format (forward conversion), but also **must** provide the ability to convert OneBot12 message segments back into platform-native API calls (reverse conversion). The unified entry point for reverse conversion is the `Raw_ob12` method.

### 6.1 Conversion Model

```
Forward Conversion (Receiving Direction)                Reverse Conversion (Sending Direction)
─────────────────                ─────────────────
Platform-native Event                       OneBot12 Message Segment List
    │                                  │
    ▼                                  ▼
Converter.convert()               Send.Raw_ob12()
    │                                  │
    ▼                                  ▼
OneBot12 Standard Event                  Platform-native API Call
(Contains {platform}_raw)             (Returns Standard Response Format)
```

**Core Symmetry**: Forward conversion retains original data in `{platform}_raw`, and reverse conversion accepts OneBot12 standard format and restores it into platform calls.

### 6.2 `Raw_ob12` Implementation Specification

`Raw_ob12` receives OneBot12 standard message segment lists and must convert them into platform-native API calls.

**Method Signature**:

```python
def Raw_ob12(self, message_segments: List[Dict]) -> asyncio.Task:
    """
    Send OneBot12 standard message segments

    :param message_segments: List of OneBot12 message segments
        [
            {"type": "text", "data": {"text": "Hello"}},
            {"type": "image", "data": {"file": "https://..."}},
            {"type": "mention", "data": {"user_id": "123"}},
        ]
    :return: asyncio.Task, await returns standard response format
    """
```

**Implementation Requirements**:

1. **Must handle all standard message segment types**: At least support `text`, `image`, `audio`, `video`, `file`, `mention`, `reply`
2. **Must handle platform extension message segments**: For message segments of the type `{platform}_xxx`, convert them into corresponding platform-native calls
3. **Must return standard response format**: Follow [API Response Standard](api-response.md)
4. **Unsupported message segments should be skipped and warning logged**, should not throw exceptions causing the entire message to fail

### 6.3 Message Segment Conversion Rules

#### 6.3.1 Standard Message Segment Conversion

The adapter must implement the following standard message segment conversions:

| OneBot12 Message Segment | Conversion Requirements |
|--------------------------|-------------------------|
| `text` | Directly use `data.text` |
| `image` | Handle based on `data.file` type: Use URL directly, upload bytes, read and upload local path |
| `audio` | Same handling logic as image |
| `video` | Same handling logic as image |
| `file` | Same handling logic as image, pay attention to `data.filename` |
| `mention` | Convert to platform's @user mechanism (e.g., Telegram's `entities`, Yunhu's `at_uid`) |
| `reply` | Convert to platform's reply reference mechanism |
| `face` | Convert to platform's emoji sending mechanism, skip if not supported |
| `location` | Convert to platform's location sending mechanism, skip if not supported |

#### 6.3.2 Platform Extension Message Segment Conversion

For message segments with platform prefixes, the adapter should identify and convert them:

```python
def _convert_ob12_segments(self, segments: List[Dict]) -> Any:
    """Convert OneBot12 message segments to platform-native format"""
    platform_prefix = f"{self._platform_name}_"
    
    for segment in segments:
        seg_type = segment["type"]
        seg_data = segment["data"]
        
        if seg_type.startswith(platform_prefix):
            # Platform extension message segment → Platform-native call
            self._handle_platform_segment(seg_type, seg_data)
        elif seg_type in self._standard_segment_handlers:
            # Standard message segment → Platform equivalent operation
            self._standard_segment_handlers[seg_type](seg_data)
        else:
            # Unknown message segment → Log warning and skip
            logger.warning(f"Unsupported message segment type: {seg_type}")
```

#### 6.3.3 Handling Composite Message Segments

A message may contain multiple message segments, and the adapter needs to handle composite messages correctly:

```python
# Module sends a message containing text + image + @user
await send.Raw_ob12([
    {"type": "mention", "data": {"user_id": "123"}},
    {"type": "text", "data": {"text": "Hello"}},
    {"type": "image", "data": {"file": "https://example.com/img.jpg"}}
])
```

**Handling Strategy**:
- **Prioritize merging**: If the platform supports combining text, image, @, etc. in a single message, merge and send
- **Fallback to splitting**: If the platform does not support merging, send as multiple messages in sequence
- **Maintain order**: The sending order of message segments should be consistent with the list order

### 6.4 Relationship between `Raw_ob12` and Standard Methods

The adapter's standard send methods (`Text`, `Image`, etc.) **are already implemented by the `SendDSL` base class and default to delegating to `Raw_ob12`**, so the adapter subclass does not need to reimplement them:

```python
class Send(SendDSL):
    def Raw_ob12(self, message_segments: List[Dict]) -> asyncio.Task:
        """Core implementation: OneBot12 message segment → Platform API (must implement)"""
        return asyncio.create_task(self._send_ob12(message_segments))

    # Text/Image/Voice/Video/File are inherited from the base class and automatically delegate to Raw_ob12
    # If platform-specific logic is needed, individual methods can be overridden:
    # def Text(self, text: str) -> asyncio.Task:
    #     return self.Raw_ob12([{"type": "text", "data": {"text": text}}])
```

**Benefits**:
- Conversion logic is centralized in `Raw_ob12`, reducing redundant code
- Standard methods and `Raw_ob12` behavior are completely consistent
- Modules get the same result whether using `Text()` or `Raw_ob12()`
- The base class provides type signatures, and IDEs can complete standard methods

### 6.5 Implementation Example

```python
class YunhuSend(SendDSL):
    """Yunhu Platform Send Implementation"""
    
    def Raw_ob12(self, message_segments: list) -> asyncio.Task:
        """OneBot12 message segment → Yunhu API call"""
        return asyncio.create_task(self._do_send(message_segments))
    
    async def _do_send(self, segments: list) -> dict:
        """Actual sending logic"""
        # 1. Parse modifier status
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
                logger.warning(f"Yunhu does not support message segment: {seg_type}")
        
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

Module developers can query the adapter's supported send methods via API:

```python
from ErisPulse import adapter

# List all send methods
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

## 8. Registered Send Method Extensions

| Platform | Method Name | Description |
|----------|-------------|-------------|
| onebot12 | `Mention` | @User (OneBot12 style) |
| onebot12 | `Sticker` | Send sticker |
| onebot12 | `Location` | Send location |
| onebot12 | `Recall` | Recall message |
| onebot12 | `Edit` | Edit message |
| onebot12 | `Batch` | Batch send |

> **Note**: Send methods are not prefixed with the platform name; methods with the same name on different platforms can have different implementations.

---

## 9. Adapter Development Notes

For how to correctly override `BaseAdapter`, `Send`, `Request`'s `__init__`, see [Adapter Development Guide - `__init__` Notes](../developer-guide/adapters/getting-started.md#init-注意事项).

---

---

## 10. Adapter Implementation Checklist

### Send Methods
- [ ] Standard methods (`Text`, `Image`, etc.) are implemented
- [ ] Return values are all `asyncio.Task`
- [ ] Modifier methods (`At`, `Reply`, `AtAll`) return `self`
- [ ] Platform extension methods use PascalCase, no platform prefix
- [ ] All methods have complete type annotations and docstrings

### Reverse Conversion
- [ ] `Raw_ob12` **is implemented** (must, cannot skip)
- [ ] `Raw_ob12` can handle all standard message segments (`text`, `image`, `audio`, `video`, `file`, `mention`, `reply`)
- [ ] `Raw_ob12` can handle platform extension message segments (`{platform}_xxx` type)
- [ ] Standard send methods (`Text`, `Image`, etc.) internally delegate to `Raw_ob12`, not implement conversion logic independently
- [ ] Unsupported message segments are skipped and warnings are logged, no exceptions are thrown
- [ ] Composite message segments are handled correctly (merge or split in sequence)

---

## 11. MessageBuilder

`MessageBuilder` is a message segment builder tool provided by ErisPulse, used in conjunction with `Raw_ob12` to simplify the construction of OneBot12 message segments.

### 11.1 Import

```python
from ErisPulse.Core import MessageBuilder
# or
from ErisPulse.Core.Event import MessageBuilder
```

### 11.2 Chainable Building

```python
# Build a message containing text, image, and @user
segments = (
    MessageBuilder()
    .mention("123456")
    .text("Hello, look at this image")
    .image("https://example.com/img.jpg")
    .reply("msg_789")
    .build()
)

# Send
await adapter.Send.To("group", "456").Raw_ob12(segments)
```

### 11.3 Quick Single Segment Building

```python
# Quickly build a single message segment (returns list[dict], can be directly passed to Raw_ob12)
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
|--------|-------------|-------------|
| `text(text)` | Text | `text` |
| `image(file)` | Image | `file` |
| `audio(file)` | Audio | `file` |
| `video(file)` | Video | `file` |
| `file(file, filename=None)` | File | `file`, `filename` (optional) |
| `mention(user_id, user_name=None)` | @User | `user_id`, `user_name` (optional) |
| `at(user_id, user_name=None)` | @User (`mention` alias) | Same as `mention` |
| `reply(message_id)` | Reply | `message_id` |
| `at_all()` | @All members | `{}` |
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

## 12. Related Documentation

- [Event Conversion Standard](event-conversion.md) - Complete event conversion specification, extension naming, and message segment standards
- [API Response Standard](api-response.md) - Adapter API response format standard
- [Session Type Standard](session-types.md) - Session type definitions and mapping relationships
- [Request Operation Specification](request-action-spec.md) - Request event field requirements, HandleRequest DSL, and adapter implementation requirements



### 请求操作规范

# ErisPulse Request Operation Specification

This document defines the standardized specification for request event operations in the ErisPulse adapter, including field requirements for request events, usage of the Request DSL, and adapter implementation requirements.

## 1. Overview

The request event (`type: "request"`) is a special event type defined in the OneBot12 standard, representing requests that require the Bot to make a decision (such as friend requests or group invitations).

Unlike message events, request events require **bidirectional interaction**:
1. **Receiving**: The adapter converts the platform-native request into a standard request event
2. **Responding**: The module executes operations via the `Request` DSL or `Event.approve()`/`Event.reject()`

```
Platform-native request event
    │
    ▼
Converter.convert()        ← Adapter implementation (forward conversion)
    │
    ▼
Standard request event (with request_id)
    │
    ├─→ Module handler @request.on_friend_request()
    │       │
    │       ├─→ event.approve()     ← Approve the request
    │       └─→ event.reject()      ← Reject the request
    │               │
    │               ▼
    │       adapter.Request(request_id).accept()
    │               │
    │               ▼
    │       BaseAdapter.Request.accept()  ← Adapter override
    │               │
    │               ▼
    │       Platform API call
    │
    └─→ Or directly through adapter operations
            await adapter.Request("req_id").accept()
```

## 2. Request Event Field Requirements

### 2.1 Standard Fields

The request event must include OneBot12 standard fields and the following additional fields:

| Field | Type | Required | Description |
|------|------|------|------|
| `request_id` | string | **Strongly recommended** | Request identifier, used for approve/reject operations |
| `user_id` | string | Yes | ID of the request initiator |
| `user_nickname` | string | No | Nickname of the request initiator |
| `comment` | string | No | Request comment |

### 2.2 `request_id` Field

`request_id` is the core identifier for request operations:

- **Purpose**: Identifies an actionable request, used by the `Request` DSL
- **Generation Rules**:
  - Prefer using the platform-native request identifier (e.g., OneBot11's `flag` field, Telegram's `chat_invite_link`, etc.)
  - If the platform lacks a native request ID, the adapter should generate a unique identifier (recommended format: `{platform}_{timestamp}_{user_id}`)
- **Uniqueness**: Should be unique within the same platform
- **Missing Behavior**: When `request_id` is missing, `event.approve()` / `event.reject()` will raise a `ValueError`

### 2.3 Request Event Example

```json
{
  "id": "evt_123456",
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
  "comment": "Please add me as a friend",
  "request_id": "flag_abc123",
  "onebot11_raw": {...},
  "onebot11_raw_type": "request"
}
```

## 3. Request DSL

### 3.1 Chainable Calls

`Request` provides a chainable API similar to `Send`:

```python
# Basic usage
await adapter.Request("req_id").accept()
await adapter.Request("req_id").reject()

# Specify Bot account
await adapter.Request("req_id").Using("bot1").accept()

# Include comment (via kwargs)
await adapter.Request("req_id").accept(comment="Welcome")
await adapter.Request("req_id").reject(comment="Not adding for now")

# Combined usage
await adapter.Request("req_id").Using("bot1").accept(comment="Welcome")
```

### 3.2 Method List

| Method | Description | Return Value |
|------|------|--------|
| `Using(account_id)` | Specify the Bot account for the operation | `RequestDSL` (supports chainable calls) |
| `accept(**kwargs)` | Approve the request | `asyncio.Task` (await returns standard response) |
| `reject(**kwargs)` | Reject the request | `asyncio.Task` (await returns standard response) |

### 3.3 Return Value Format

The operation returns a standard API response format:

**Success**:
```json
{
    "status": "ok",
    "retcode": 0,
    "data": null,
    "message_id": "",
    "message": ""
}
```

**Failure**:
```json
{
    "status": "failed",
    "retcode": 34001,
    "data": null,
    "message_id": "",
    "message": "Request expired or does not exist"
}
```

**Not Implemented** (adapter did not override `accept`/`reject`):
```json
{
    "status": "failed",
    "retcode": 10002,
    "data": null,
    "message_id": "",
    "message": "Platform MyAdapter has not implemented request operation (accept)"
}
```

## 4. Event Convenience Methods

The `Event` wrapper class provides convenient methods suitable for use in request event handlers:

```python
from ErisPulse.Core.Event import request

@request.on_friend_request()
async def handle_friend_request(event):
    # Check request ID
    request_id = event.get_request_id()
    if not request_id:
        print("Warning: Request event missing request_id")
        return
    
    # Approve request
    result = await event.approve()
    
    # Or reject request
    # result = await event.reject(comment="Not adding as friend for now")
    
    # Check result
    if result.get("status") == "ok":
        print("Operation successful")
    else:
        print(f"Operation failed: {result.get('message')}")
```

### 4.1 Event Method List

| Method | Description | Return Value |
|------|------|--------|
| `get_request_id()` | Get request ID | `str` |
| `approve(comment=None)` | Approve current request event | Standard response format |
| `reject(comment=None)` | Reject current request event | Standard response format |

## 5. Adapter Implementation Requirements

### 5.1 Converter Requirements

The adapter's converter must correctly set the `request_id` field when converting request events:

```python
def convert_request_event(self, raw_event: dict) -> dict:
    """Convert platform-native request event"""
    return {
        "id": self._generate_event_id(raw_event),
        "time": int(time.time()),
        "type": "request",
        "detail_type": self._map_request_type(raw_event),  # "friend" or "group"
        "platform": self._platform_name,
        "self": {
            "platform": self._platform_name,
            "user_id": str(self._bot_id),
        },
        "user_id": str(raw_event.get("user_id", "")),
        "user_nickname": raw_event.get("nickname", ""),
        "comment": raw_event.get("message", ""),
        "request_id": self._extract_request_id(raw_event),  # ← Key field
        f"{self._platform_name}_raw": raw_event,
        f"{self._platform_name}_raw_type": raw_event.get("type", ""),
    }

def _extract_request_id(self, raw_event: dict) -> str:
    """
    Extract request ID from platform-native event
    
    Prefer using platform-native request identifier, or generate a unique ID if none exists
    """
    # Prefer using platform-native ID
    if flag := raw_event.get("flag"):
        return str(flag)
    if request_key := raw_event.get("request_key"):
        return str(request_key)
    
    # Fallback: Generate unique ID
    import hashlib
    raw = f"{self._platform_name}_{raw_event.get('user_id')}_{raw_event.get('timestamp')}"
    return hashlib.md5(raw.encode()).hexdigest()
```

### 5.2 Request Internal Class Implementation

The adapter implements `accept` and `reject` in the `Request` internal class:

```python
from ErisPulse.Core import BaseAdapter, RequestDSL

class MyAdapter(BaseAdapter):
    
    class Request(RequestDSL):
        """MyPlatform request operation implementation"""
        
        def accept(self, **kwargs):
            """
            Approve request
            
            :param kwargs: Additional parameters, e.g., comment="remark"
            :return: asyncio.Task
            """
            async def _do():
                try:
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
                except Exception as e:
                    return {
                        "status": "failed",
                        "retcode": 34001,
                        "data": None,
                        "message_id": "",
                        "message": f"Request operation failed: {e}",
                    }
            
            return self._create_task(_do())
        
        def reject(self, **kwargs):
            """Reject request"""
            async def _do():
                try:
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
                except Exception as e:
                    return {
                        "status": "failed",
                        "retcode": 34001,
                        "data": None,
                        "message_id": "",
                        "message": f"Request operation failed: {e}",
                    }
            
            return self._create_task(_do())
```

### 5.3 Platform Does Not Support Request Operations

If the platform does not support friend requests or group invitations (e.g., some platforms automatically handle requests), the adapter can:

1. **Do not override `Request` internal class**: Use the base class default implementation, calling `accept()`/`reject()` returns `retcode=10002`
2. **Skip `request_id` generation during conversion**: Do not generate `request_id`, let `event.approve()` raise `ValueError`
3. **Log warnings**: Record warnings in `accept`/`reject` and return appropriate error codes

### 5.4 Summary: Send and Request in Parallel

The adapter has two parallel DSL internal classes, each with its own responsibilities:

```
BaseAdapter
├── Send(SendDSL)     ← Message sending
│   ├── Raw_ob12()    ← Must be implemented
│   ├── Text()        ← Recommended implementation
│   └── Image()       ← Implemented as needed
│
└── Request(RequestDSL) ← Request operations
    ├── accept()        ← Implemented as needed
    └── reject()        ← Implemented as needed
```

### 5.5 Adapter `__init__` Considerations

When overriding the `Request` internal class's `__init__`, you must pass through parameters and call `super().__init__()`, see [Adapter Development Guide - `__init__` Considerations](../developer-guide/adapters/getting-started.md#init-注意事项) (`Request` is similar, parameters are `adapter, request_id, account_id`).

## 6. Adapter Implementation Checklist

### Basic Requirements
- [ ] If `__init__` is overridden, `super().__init__()` has been called (to ensure Send/Request factory initialization)

### Request Event Conversion
- [ ] Request event includes the `request_id` field (strongly recommended)
- [ ] `detail_type` correctly maps to `"friend"` or `"group"`
- [ ] Platform-native data is preserved in the `{platform}_raw` field
- [ ] `request_id` generation rules are documented

### Request Operations
- [ ] `Request` internal class is implemented (if the platform supports request operations)
- [ ] `accept()` method is implemented
- [ ] `reject()` method is implemented
- [ ] Operation returns standard API response format
- [ ] Operations not supported return `retcode=10002`
- [ ] Network errors return `retcode=33xxx` (following API response standards)

## 7. Error Code Extension

For **adapter implementation layer** related to request operations, the following recommended error codes are suggested (following [API Response Standard](api-response.md) §3.2, falling within the `34xxx` platform error segment's lower three digits for custom use):

| Error Code | Error Name | Description |
|-------|-------|------|
| 34001 | Request Not Found | Request does not exist or has expired |
| 34002 | Request Already Handled | Request has already been handled |
| 34003 | Request Not Supported | Platform does not support this type of request operation |
| 34004 | Permission Denied | Bot does not have permission to handle this request (returned by platform) |

> **Boundary with Framework Codes**: The above `340xx` are **platform/adapter**-returned request handling failures; when the ErisPulse framework disables a module's request action in `scope.actions`, it **directly returns `34601` (Action Denied)** before calling the adapter (see [API Response Standard §5.3](api-response.md#53-framework-extended-return-codes-34xxx-custom-use-in-the-lower-three-digits-of-the-platform-error-segment)), and the two are not substitutes: first pass the `34601` framework gate, then fall back to the platform layer `340xx` errors.

## 8. Related Documentation

- [Event Conversion Standard](event-conversion.md) - Complete event conversion specification
- [API Response Standard](api-response.md) - Standard format for adapter API responses
- [Send Method Specification](send-method-spec.md) - Naming and parameter conventions for Send class methods
- [Session Type Standard](session-types.md) - Definition and mapping of session types



### API 动作标准

# ErisPulse API Action Standard

This document defines the unified interface specification for **OneBot12 Standard API Actions** in ErisPulse adapters, enabling module developers to program against standard interfaces, with adapters responsible for mapping to platform-native APIs.

> **Scope**: In OneBot12 standard actions, `ApiDSL` provides strongly-typed methods for user/group/channel/message management/meta general interfaces (with `send_message` handled by `SendDSL.Raw_ob12`). File resource actions (`upload_file` / `get_file` / chunked) are retained only as degraded pass-through, see §3.5 for details. Platform extension actions are invoked via `Api.call("prefix.action", ...)` escape hatch. Action parameters and return structures follow the OneBot12 specification (located in `onebot/specs/interface/` in the repository).

## 1. Design Background

In ErisPulse, message segments (message send/receive) and event formats already fully conform to the OneBot12 standard, but **API action calls** (such as retrieving user information, group list, or deleting messages) were previously inconsistent—module developers had to write different `call_api` calls for each platform.

`ApiDSL` resolves this issue by providing strongly-typed standard action methods:

```
Module Code (Cross-Platform Consistency)       Adapter Implementation (Platform-Specific)
───────────────────────────────────────        ────────────────────────────────────────
adapter.Api.get_user_info("123")  →  Adapter call_api / Override
adapter.Api.get_group_list()      →  Adapter call_api / Override
adapter.Api.delete_message("id")  →  Adapter call_api / Override
```

## 2. Three Parallel DSL Structures

ErisPulse adapters have three parallel internal DSL classes, each with distinct responsibilities:

```
BaseAdapter
├── Send(SendDSL)       ← Message Sending (Text/Image/Raw_ob12)
├── Request(RequestDSL)  ← Request Handling (accept/reject)
└── Api(ApiDSL)          ← Standard API Actions (Users/Groups/Channels/Message Management/File/Meta) ★
```

| DSL | Responsibility | Method Style | Return Value |
|-----|----------------|--------------|--------------|
| `Send` | Sending Messages | Chained + `asyncio.Task` | Standard Response |
| `Request` | Handling Request Events | `asyncio.Task` | Standard Response |
| `Api` | Query/Management Operations | `async` Methods | Standard Response |

## 3. Standard Action List

### 3.1 User-Related

| Method | OB12 Action | Parameters | data Return |
|--------|-------------|------------|-------------|
| `get_self_info()` | `get_self_info` | None | `user_id`, `user_name`, `user_displayname` |
| `get_user_info(user_id)` | `get_user_info` | `user_id: str` | `user_id`, `user_name`, `user_displayname`, `user_remark` |
| `get_friend_list()` | `get_friend_list` | None | `list[get_user_info response]` |

### 3.2 Group-Related

| Method | OB12 Action | Parameters | data Return |
|--------|-------------|------------|-------------|
| `get_group_info(group_id)` | `get_group_info` | `group_id: str` | `group_id`, `group_name` |
| `get_group_list()` | `get_group_list` | None | `list[get_group_info response]` |
| `get_group_member_info(group_id, user_id)` | `get_group_member_info` | `group_id: str`, `user_id: str` | `user_id`, `user_name`, `user_displayname` |
| `get_group_member_list(group_id)` | `get_group_member_list` | `group_id: str` | `list[get_group_member_info response]` |
| `set_group_name(group_id, group_name)` | `set_group_name` | `group_id: str`, `group_name: str` | None |
| `leave_group(group_id)` | `leave_group` | `group_id: str` | None |

### 3.3 Message Management

| Method | OB12 Action | Parameters | Description |
|--------|-------------|------------|-------------|
| `delete_message(message_id)` | `delete_message` | `message_id: str` | Recall/Delete Message |

> **Sending Messages** (`send_message`) is handled by `SendDSL`'s `Raw_ob12`, and is not repeated in `ApiDSL`.

### 3.4 Channel (Guild) Related

OneBot12 channel system is hierarchical: **channel (guild)** and **sub-channel (channel)**.

| Method | OB12 Action | Parameters | data Return |
|--------|-------------|------------|-------------|
| `get_guild_info(guild_id)` | `get_guild_info` | `guild_id: str` | `guild_id`, `guild_name` |
| `get_guild_list()` | `get_guild_list` | None | `list[get_guild_info response]` |
| `set_guild_name(guild_id, guild_name)` | `set_guild_name` | `guild_id: str`, `guild_name: str` | None |
| `get_guild_member_info(guild_id, user_id)` | `get_guild_member_info` | `guild_id: str`, `user_id: str` | `user_id`, `user_name`, `user_displayname` |
| `get_guild_member_list(guild_id)` | `get_guild_member_list` | `guild_id: str` | `list[get_guild_member_info response]` |
| `leave_guild(guild_id)` | `leave_guild` | `guild_id: str` | None |
| `get_channel_info(guild_id, channel_id)` | `get_channel_info` | `guild_id: str`, `channel_id: str` | `channel_id`, `channel_name` |
| `get_channel_list(guild_id, *, joined_only)` | `get_channel_list` | `guild_id: str`, `joined_only: bool=false` | `list[get_channel_info response]` |
| `set_channel_name(guild_id, channel_id, channel_name)` | `set_channel_name` | `guild_id`, `channel_id`, `channel_name` | None |
| `get_channel_member_info(guild_id, channel_id, user_id)` | `get_channel_member_info` | `guild_id`, `channel_id`, `user_id` | `user_id`, `user_name`, `user_displayname` |
| `get_channel_member_list(guild_id, channel_id)` | `get_channel_member_list` | `guild_id`, `channel_id` | `list[get_channel_member_info response]` |
| `leave_channel(guild_id, channel_id)` | `leave_channel` | `guild_id`, `channel_id` | None |

> The channel system is independent from the group system: platforms such as Discord, QQ channels, and Kook implement channel interfaces, while traditional platforms like QQ and WeChat implement group interfaces. Both can coexist or exist independently.

### 3.5 File Resource Operations

> [!WARNING]
> **File resource model (two-segment file_id) is "degraded and available" in ErisPulse**: ErisPulse does not use the "upload first, then reference by file_id" model for file sending/receiving—modules send files using `SendDSL.File(file, filename)` (URL/path/bytes are directly transmitted at send time, see [Send Method Specification](send-method-spec.md)). This section's `upload_file` / `get_file` / chunked actions depend on platform-specific `file_id` file resource capabilities, which are **not universally applicable**; only when the adapter backend naturally supports this capability should it be passed through. Framework-built adapters **do not implement or recommend implementing** this, and calls typically return `retcode=10002`. When modules need to transfer files cross-platform, please use `SendDSL.File` instead of relying on file_id.
>
> **Outlook**: Standardizing the `file_id` resource model to the framework layer is a future direction, but is not provided in the current version.

**Whole-file transfer (small files):**

| Method | OB12 Action | Parameters | data Return |
|--------|-------------|------------|-------------|
| `upload_file(*, type, name, ...)` | `upload_file` | `type`, `name`, `url`/`path`/`data`, `headers?`, `sha256?` | `file_id` |
| `get_file(file_id, type)` | `get_file` | `file_id: str`, `type: str` | `name`, `url`/`path`/`data` |

The `type` parameter of `upload_file`:
- `"url"`: Upload via URL (must provide `url`)
- `"path"`: Upload via local path (must provide `path`)
- `"data"`: Upload via binary data (must provide `data`)

#### 3.5.1 Chunked Transfer (Large Files, Part of the Above Degraded Scope)

OneBot12 chunked actions distinguish stages by `stage`. `ApiDSL` splits the three/two stages of the same action into independent methods (`offset` is byte offset, `data` in JSON is Base64); the following table is for reference only—adapters do not need to or should not force implementation:

**Three-step chunked upload**: `prepare` → `transfer` (loop through chunks) → `finish`

| Method | Corresponding stage | Parameters | data Return |
|--------|---------------------|------------|-------------|
| `upload_file_fragmented_prepare(name, total_size)` | `prepare` | `name: str`, `total_size: int` | `file_id` (used during transfer) |
| `upload_file_fragmented_transfer(file_id, offset, data)` | `transfer` | `file_id`, `offset: int`, `data: bytes` | None |
| `upload_file_fragmented_finish(file_id, sha256)` | `finish` | `file_id`, `sha256: str` (full file checksum) | `file_id` |

```python
total = os.path.getsize(path)
r = await adapter.Api.upload_file_fragmented_prepare(os.path.basename(path), total)
fid = r["data"]["file_id"]
offset = 0
with open(path, "rb") as f:
    while chunk := f.read(65536):
        await adapter.Api.upload_file_fragmented_transfer(fid, offset, chunk)
        offset += len(chunk)
sha256 = hashlib.sha256(open(path, "rb").read()).hexdigest()
await adapter.Api.upload_file_fragmented_finish(fid, sha256)
```

**Two-step chunked download**: `prepare` → `transfer` (loop to fetch chunks)

| Method | Corresponding stage | Parameters | data Return |
|--------|---------------------|------------|-------------|
| `get_file_fragmented_prepare(file_id)` | `prepare` | `file_id` | `name`, `total_size`, `sha256` |
| `get_file_fragmented_transfer(file_id, offset, size)` | `transfer` | `file_id`, `offset: int`, `size: int` | `data` (this chunk's bytes) |

### 3.6 Meta Actions

Meta actions are not account-specific and do not require `Using()` to specify a Bot.

| Method | OB12 Action | Parameters | data Return |
|--------|-------------|------------|-------------|
| `get_latest_events(limit, timeout)` | `get_latest_events` | `limit: int=0`, `timeout: int=0` | Array of event objects (excluding meta events) |
| `get_supported_actions()` | `get_supported_actions` | None | `list[str]` supported action names |
| `get_status()` | `get_status` | None | `good: bool`, `bots: list[{self, online, ...}]` |
| `get_version()` | `get_version` | None | `impl`, `version`, `onebot_version` |

### 3.7 General Extension Actions

| Method | Description |
|--------|-------------|
| `call(action, **params)` | Escape hatch for platform extension actions, following OB12 extension naming rules `{prefix}.{action}` |

## 4. Usage

### 4.1 Basic Calls

```python
from ErisPulse import adapter

# Get user information (cross-platform consistency)
result = await adapter.myplatform.Api.get_user_info("123456")
if result["status"] == "ok":
    user_name = result["data"]["user_name"]
    print(f"Username: {user_name}")

# Get group list
result = await adapter.myplatform.Api.get_group_list()
groups = result["data"]

# Delete message
await adapter.myplatform.Api.delete_message("msg_123456")
```

### 4.2 Specifying Bot Account (Multi-account Mode)

```python
# Execute operation using a specific Bot account
info = await adapter.myplatform.Api.Using("bot1").get_self_info()
```

### 4.3 Platform Extension Actions

```python
# Call platform-specific extension actions (suggest using {prefix}.{action} naming)
result = await adapter.telegram.Api.call(
    "telegram.send_sticker",
    sticker_id="CAACAgIAAxkBAA...",
)
```

### 4.4 Use in Event Handlers

```python
from ErisPulse.Core.Event import message

@message()
async def handle(event):
    # Get sender's detailed information
    user_id = event.get_user_id()
    platform = event.get_platform()

    result = await getattr(adapter, platform).Api.get_user_info(user_id)
    if result["status"] == "ok":
        user_name = result["data"]["user_name"]
        await event.reply(f"Hello, {user_name}!")
```

## 5. Adapter Implementation

### 5.1 Default Behavior (Zero Configuration)

The default implementation of `ApiDSL` passes the standard action name as `endpoint` directly to `adapter.call_api()`:

```python
# ApiDSL default implementation is equivalent to:
async def get_user_info(self, user_id: str) -> dict:
    return await self._adapter.call_api("get_user_info", user_id=user_id, account_id=self._account_id)
```

**Applicable Scenarios**: When the adapter's underlying backend itself conforms to the OneBot12 standard action protocol, `call_api` naturally supports standard action names (e.g., directly interfacing with a service that follows this protocol).

### 5.2 Overriding Standard Methods (Mapping to Platform Native API)

Adapters can override individual standard methods to map them to platform-native APIs:

```python
class MyAdapter(BaseAdapter):

    class Api(BaseAdapter.Api):
        """MyPlatform standard API action implementation"""

        async def get_user_info(self, user_id: str) -> dict:
            # Map to platform-native API
            raw = await self._adapter._request("GET", f"/users/{user_id}")
            if raw.get("code") != 0:
                return self._adapter.make_error(retcode=34600, message="User does not exist")

            user = raw["data"]
            return self._adapter.make_response(
                data={
                    "user_id": str(user["id"]),
                    "user_name": user.get("nick", ""),
                    "user_displayname": user.get("display_name", ""),
                    "user_remark": user.get("remark", ""),
                },
                raw=raw,
            )

        async def get_friend_list(self) -> dict:
            raw = await self._adapter._request("GET", "/friends")
            friends = [
                {
                    "user_id": str(u["id"]),
                    "user_name": u.get("nick", ""),
                    "user_displayname": u.get("display_name", ""),
                    "user_remark": u.get("remark", ""),
                }
                for u in raw.get("data", [])
            ]
            return self._adapter.make_response(data=friends, raw=raw)
```

### 5.3 Unsupported Actions

Standard methods not overridden by the adapter use the default implementation (delegated to `call_api`). If `call_api` does not support the action, it should return a standard error response:

```python
async def call_api(self, endpoint: str, **params):
    if endpoint not in self._supported_endpoints:
        return self.make_error(retcode=10002, message=f"Unsupported action: {endpoint}")
    # ... platform API call
```

Module developers can determine support by checking the `retcode` in the return value:

```python
result = await adapter.myplatform.Api.get_friend_list()
if result["retcode"] == 10002:
    print("This platform does not support retrieving friend list")
```

## 6. Response Format

All `ApiDSL` methods return the standard API response format (see [API Response Standard](api-response.md)):

```json
{
    "status": "ok",
    "retcode": 0,
    "data": { ... },
    "message_id": "",
    "message": "",
    "myplatform_raw": { ... }
}
```

> **Note**: For information query actions, `message_id` is an empty string (only message sending actions have `message_id`).

## 7. Relationship with SendDSL / RequestDSL

| Scenario | Use DSL | Example |
|----------|---------|---------|
| Sending Messages | `Send` | `adapter.Send.To("group", "123").Text("hi")` |
| Accept/Reject Requests | `Request` | `adapter.Request("req_id").accept()` |
| Get User/Group Info | `Api` | `adapter.Api.get_user_info("123")` |
| Delete Message | `Api` | `adapter.Api.delete_message("msg_id")` |
| Leave Group | `Api` | `adapter.Api.leave_group("group_id")` |

## 8. Adapter Implementation Checklist

### Standard Actions
- [ ] `call_api` can handle standard action names (or override corresponding `ApiDSL` methods)
- [ ] Unsupported actions return `retcode=10002`
- [ ] Return values follow the standard API response format
- [ ] `data` field contains fields defined in the OB12 standard
- [ ] Channel platform must implement `get_guild_*` / `get_channel_*` / `leave_guild` / `leave_channel`
- [ ] Meta actions (`get_status` / `get_version` / `get_supported_actions`) are recommended to be implemented
- [ ] **File sending uses `SendDSL.File` (direct upload)**; file resource actions (`upload_file`/`get_file`/chunked) **are not mandatory**, only required when the backend has `file_id` resource capability

### Extension Actions
- [ ] Platform extension actions use `{prefix}.{action}` naming
- [ ] Extension action parameters and responses still follow the OB12 action request/response structure

## 9. Related Documents

- [API Response Standard](api-response.md) - Standard response format for adapter API
- [Send Method Specification](send-method-spec.md) - Naming and parameter conventions for Send class methods
- [Request Action Specification](request-action-spec.md) - Usage of Request DSL
- [Event Conversion Standard](event-conversion.md) - Event format and message segment standards



====
生态模块
====


### ErisPulse-App 安装与使用

# ErisPulse-App

[ErisPulse-App](https://github.com/ErisPulse/ErisPulse-App) is an **official cross-platform client** maintained directly by ErisDev (releases available for Android / Windows / Linux / macOS),
providing a fully native graphical management interface: create, run, and manage multiple bot instances on your phone or computer,
without the need for a terminal, or a separate Python environment.

> [!IMPORTANT]
> ErisPulse-App is a **standalone installed client application**, not a module installed via `epsdk install`.
> It comes with a built-in Python runtime and ErisPulse SDK, ready to use out of the box—**you can run it directly on your phone**.

## Feature Overview

- **Multi-instance Management**: Create / Start / Stop / Delete multiple instances, automatic port and access token allocation, support for new environments or cloning existing environments
- **Overview Dashboard**: Adapter / Module / Online Bots / Total Events statistics, CPU / Memory usage alerts with color changes
- **Module Store**: Search and tag filtering, one-click Install / Upgrade / Uninstall, specify version installation, pip mirror source and Git package support
- **Event Stream + Event Builder**: Real-time event viewing, visual construction and submission of test events to adapters
- **Monitoring**: Log / Lifecycle / Audit unified view
- **Command Management**: Global settings such as Prefix and Aliases, start/stop and platform allow/deny lists
- **Bot Overview / Config / File Management**: Native interface for direct instance operations
- **Background Persistence**: Android foreground service keep-alive; Windows minimized to system tray, closing the window does not interrupt the instance
- **Dynamic Module Windows**: Registered module pages automatically appear in the sidebar navigation (grouped with Dashboard), click to jump directly



## Supported Platforms

All platform installers can be downloaded from [GitHub Releases](https://github.com/ErisPulse/ErisPulse-App/releases). Simply select the appropriate package as needed:

| Platform | Package | Description |
|----------|--------|-------------|
| Android | `online-*.apk` / `offline-*.apk` | **Run directly on phone**, no computer required |
| Windows | `windows-x64-setup.exe` / `windows-x64.zip` | Installer / Portable version |
| Linux | `linux-x64.tar.gz` | Extract and run |
| macOS | `macos-arm64.zip` | Apple Silicon (arm64) |

A single Flutter codebase covers all platforms.

---

## Installation (Android / Mobile Direct Run)

Download and install the APK from [GitHub Releases](https://github.com/ErisPulse/ErisPulse-App/releases). There are two builds available:

| Build | Runtime Image | Use Case |
|------|-----------|---------|
| `erispulse-app-online-*.apk` | Downloaded on first launch | Smaller installer, suitable for good network connectivity |
| `erispulse-app-offline-*.apk` | Packaged into APK | Offline self-contained, no internet required after installation |

The installation steps for both builds are identical:

1. Download and install the APK, and grant notification permission at startup (required to keep background services alive)
2. Click "Run First Initialization" once the initialization banner appears on the home page (includes progress and log view)
3. Create an instance and start it
4. Configure adapters and Model API Keys in the built-in management interface

> The offline package is self-contained — no network is required after installation. If the download is slow or unstable during the first launch, you can switch the download source to a mirror (ghfast / gh-proxy) in the settings page.

### Installation (Desktop: Windows / Linux / macOS)

1. Download the corresponding platform installer from [GitHub Releases](https://github.com/ErisPulse/ErisPulse-App/releases)
   (Windows `setup.exe` or portable `zip`, Linux `tar.gz`, macOS `zip`)
2. Install and launch
3. On the welcome page, select the ErisPulse SDK version to install (default is the latest) and install it
4. Create an instance and launch it

---

## How It Works

```
┌────────────────────────────────────────────────────┐
│  ErisPulse-App (Flutter)                            │
│                                                    │
│  Native UI ── Dashboard REST / WS API              │
│       │                                            │
│       ├── Android: Foreground Service + proot + Ubuntu rootfs│
│       │        + Python + ErisPulse instance       │
│       └── Desktop: Built-in Python + Direct process management│
└────────────────────────────────────────────────────┘
```

- **Android**: The instance runs inside a foreground service (background isolate) managed `proot` (user-mode chroot). The bot continues to run after the UI closes, with automatic crash recovery.
- **Desktop**: The instance runs as a direct child process of the App; Windows supports minimizing to the system tray for background persistence (closing the window does not interrupt the instance). Upon App restart, management of still-running instances is automatically resumed; upon exit, all instances are stopped uniformly.
- Native UI across all platforms communicates with the instance via the REST / WebSocket API at `127.0.0.1:<port>/Dashboard/*`, sharing the same API as [ErisPulse-Dashboard](docs/en/dashboard.md)

---

## Relationship with SDK

- App comes with a built-in ErisPulse SDK: Android side is bundled in the Ubuntu image, desktop side is installed via PyPI (Welcome page optional versions, default is latest)
- The instance within the App is equivalent to the instance created by the CLI `epsdk`, and the same modules / adapters can be used
- Module developers can register custom pages via [Dashboard View API Registration](dashboard.md):
  The view will automatically appear in the App sidebar navigation (groups are consistent with Dashboard), click to jump to the corresponding page rendering

---



### Dashboard 使用与视窗注册

# ErisPulse-Dashboard

[ErisPulse-Dashboard](https://pypi.org/project/ErisPulse-Dashboard/) is a **Web Management Panel Module** directly maintained by ErisDev, providing ErisPulse with a visual runtime management interface: module control, configuration editing, log viewing, event stream monitoring, etc.

> [!IMPORTANT]
> Dashboard is **not** a built-in feature of the ErisPulse framework and requires separate installation:
>
> ```bash
> epsdk install Dashboard
> ```

Dashboard also supports other ErisPulse modules to register custom management pages to the sidebar. Once registered, users can directly switch to the module's dedicated view page in the Dashboard without the need for additional development of independent frontend interfaces.

> [!NOTE]
> View registration is an **optional feature**.
>
> - If the Dashboard module is **not installed** or **not loaded**, calling `sdk.Dashboard.register_view()` will throw an exception
> - Please be sure to wrap registration code with `try/except` to ensure other functionality of the module itself is not affected
> - It is recommended to check if the Dashboard is available before registering: `hasattr(sdk, 'Dashboard') and sdk.Dashboard`

---

## How it works

```
Module on_load()
  → Calls sdk.Dashboard.register_view(...)
  → Dashboard backend stores view info
  → WebSocket notifies frontend
  → Frontend dynamically creates sidebar nav item + page container
  → User clicks to view module view
```

---

## Register API

```python
sdk.Dashboard.register_view(
    id="MyModule",                    # Required, unique identifier
    title="My Module",                # Chinese display name
    title_en="My Module",             # English display name
    icon_svg='<svg>...</svg>',        # Sidebar icon SVG
    html_content='<div>...</div>',     # Page HTML content
    js_content='function xxx() {}',    # Page JavaScript logic
    css_content='.my-style {}',        # Optional custom CSS
    iframe_url='',                     # iframe mode URL (choose one between html_content and iframe_url)
    loader="loadMyModuleView",         # JS function name to call when switching to this page
    group="group_extensions",          # Sidebar group
    group_title="",                    # Custom group Chinese name
    group_title_en="",                 # Custom group English name
)
```

### Parameter Description

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `id` | `str` | Yes | Unique identifier for the view, recommended to use module name |
| `title` | `str` | No | Chinese display name, defaults to `id` |
| `title_en` | `str` | No | English display name, defaults to `title` |
| `icon_svg` | `str` | No | Full SVG string for the sidebar icon |
| `html_content` | `str` | No* | Page HTML content for injection mode |
| `js_content` | `str` | No | Page JavaScript code |
| `css_content` | `str` | No | Page custom CSS styles |
| `iframe_url` | `str` | No* | URL for iframe mode, will be ignored if `html_content` is set |
| `loader` | `str` | No | JS function name to automatically call when page is activated |
| `group` | `str` | No | Sidebar group identifier, default is `group_extensions` |
| `group_title` | `str` | No | Custom group Chinese title |
| `group_title_en` | `str` | No | Custom group English title |

> *At least one of `html_content` and `iframe_url` must be provided, otherwise the page will be blank.

---

## Two Injection Modes

### Mode 1: HTML/JS Injection (Recommended)

Provide HTML, JS, CSS strings directly, and Dashboard will inject the content into the page. This mode is fully consistent with Dashboard styles; it is recommended to use the CSS class names provided by Dashboard.

```python
sdk.Dashboard.register_view(
    id="HelloPage",
    title="Hello Page", title_en="Hello",
    icon_svg='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/></svg>',
    html_content='<h1 class="page-title">Hello World</h1><div class="card"><div class="card-body">This is an example page</div></div>',
    group="group_tools",
)
```

> For a complete weather module example (including API routes, JS interaction, etc.), see [Complete Module Example](#complete-module-example) below.

### Mode 2: iframe Embedding

Module provides its own HTML page URL (must register routes by itself), and Dashboard embeds it via iframe. Suitable for scenarios requiring completely independent UI or complex interactions.

```python
sdk.Dashboard.register_view(
    id="MyVisualizer",
    title="Data Visualizer", title_en="Data Visualizer",
    iframe_url="/MyVisualizer/view",
    group="group_tools",
)
```

> The iframe mode will automatically append a `token` parameter to the URL for authentication.

---

## Sidebar Groups

Modules can specify which sidebar group the view belongs to. Dashboard includes the following built-in groups:

| Group ID | Chinese Name | Position |
|----------|--------------|----------|
| `group_overview` | Overview | Group 1 |
| `group_events` | Events | Group 2 |
| `group_extensions` | Extensions | Group 3 (Default) |
| `group_system` | System | Group 4 |
| `group_tools` | Tools | Group 5 |

Specify a built-in group name, and the module view will be appended to the end of that group:

```python
group="group_tools"  # Appends to the "Tools" group
```

You can also use a custom group name (not starting with `group_`), and Dashboard will automatically create a new group:

```python
group="my_group",
group_title="My Group",
group_title_en="My Group",
```

---

## Common CSS Class Names

When using the HTML injection mode for module views, you can directly use the existing CSS class names provided by Dashboard to maintain visual consistency:

| Class Name | Usage |
|------------|-------|
| `page-title` | Page title, e.g., `<h1 class="page-title">Title</h1>` |
| `card` | Card container |
| `card-header` | Card title bar |
| `card-body` | Card content area |
| `grid-2` | Two-column grid layout |
| `grid-3` | Three-column grid layout |
| `btn` | Base button |
| `btn-primary` | Primary button (blue) |
| `btn-secondary` | Secondary button |
| `btn-icon` | Icon button |
| `btn-danger` | Dangerous action button |

Dashboard uses CSS variables to control theme colors, which you can reference directly in your module view:

| CSS Variable | Usage |
|--------------|-------|
| `var(--bg-p)` | Primary background color |
| `var(--bg-s)` | Secondary background color |
| `var(--bg-t)` | Tertiary background color (cards, etc.) |
| `var(--tx-p)` | Primary text color |
| `var(--tx-s)` | Secondary text color |
| `var(--tx-t)` | Tertiary text color |
| `var(--bd)` | Border color |
| `var(--accent)` | Accent color |
| `var(--ok-c)` | Success color |
| `var(--er-c)` | Error color |

These variables automatically switch according to Dashboard's light/dark theme; no extra processing is needed by the module.

---

## Authentication & API Calls

When calling a module's own API in the JS of a module view, you need to carry the Dashboard's Token for authentication:

```javascript
var token = localStorage.getItem('__ep_tk__');
var resp = await fetch('/YourModule/api/data', {
    headers: { 'Authorization': 'Bearer ' + token }
});
var data = await resp.json();
```

Module API endpoints can decide whether to verify the Token themselves. If verification is required, extract it from the request headers:

```python
async def _api_data(self, request):
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    if not token:
        return {"error": "Unauthorized"}, 401
    return {"data": "hello"}
```

---

## Complete Module Example

The following is a complete weather module example demonstrating how to register a view, provide API data, and clean up resources on unload:

```python
from ErisPulse import sdk
from ErisPulse.Core.Bases import BaseModule
from ErisPulse.Core.Event import command


class Main(BaseModule):
    def __init__(self):
        self.sdk = sdk
        self.logger = sdk.logger.get_child("Weather")
        self.config = self._load_config()

    @staticmethod
    def get_load_strategy():
        from ErisPulse.loaders import ModuleLoadStrategy
        return ModuleLoadStrategy(lazy_load=False, priority=50)

    async def on_load(self, event):
        self._register_routes()
        self._register_dashboard_view()
        self.logger.info("Weather module loaded")

    async def on_unload(self, event):
        self._unregister_routes()
        if hasattr(self.sdk, 'Dashboard') and self.sdk.Dashboard:
            self.sdk.Dashboard.unregister_view("Weather")
        self.logger.info("Weather module unloaded")

    def _load_config(self):
        config = self.sdk.config.getConfig("Weather")
        if not config:
            default = {"city": "Beijing", "api_key": ""}
            self.sdk.config.setConfig("Weather", default)
            return default
        return config

    def _register_routes(self):
        r = self.sdk.router
        r.register_http_route("Weather", "/api/current",
                              handler=self._api_current, methods=["GET"])

    def _unregister_routes(self):
        r = self.sdk.router
        try:
            r.unregister_http_route("Weather", "/api/current")
        except Exception:
            pass

    async def _api_current(self, request):
        return {
            "city": self.config.get("city", "Beijing"),
            "temp": 25,
            "humidity": 60,
        }

    def _register_dashboard_view(self):
        try:
            dashboard = self.sdk.Dashboard
            dashboard.register_view(
                id="Weather",
                title="Weather", title_en="Weather",
                icon_svg='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></svg>',
                html_content='''
                    <h1 class="page-title">Weather Query</h1>
                    <p style="color:var(--tx-s);margin-bottom:16px">View current weather information</p>
                    <div class="grid-2">
                        <div class="card">
                            <div class="card-header">Current Weather</div>
                            <div class="card-body">
                                <div id="weather-info" style="font-size:14px;color:var(--tx-s)">Click refresh to load</div>
                            </div>
                        </div>
                        <div class="card">
                            <div class="card-header">Actions</div>
                            <div class="card-body">
                                <button class="btn btn-primary" onclick="refreshWeather()">Refresh</button>
                            </div>
                        </div>
                    </div>
                ''',
                js_content='''
                    async function loadWeatherView() { await refreshWeather(); }
                    async function refreshWeather() {
                        var el = document.getElementById('weather-info');
                        if (!el) return;
                        el.textContent = 'Loading...';
                        try {
                            var resp = await fetch('/Weather/api/current', {
                                headers: { 'Authorization': 'Bearer ' + localStorage.getItem('__ep_tk__') }
                            });
                            var data = await resp.json();
                            el.innerHTML = '<p>City: ' + (data.city || '--') + '</p>' +
                                           '<p>Temp: ' + (data.temp || '--') + '°C</p>' +
                                           '<p>Humidity: ' + (data.humidity || '--') + '%</p>';
                        } catch (e) {
                            el.textContent = 'Load failed: ' + e.message;
                        }
                    }
                ''',
                loader="loadWeatherView",
                group="group_tools",
            )
        except Exception as e:
            self.logger.warning(f"Failed to register Dashboard view: {e}")
```

---

## Unregister View

When a module is unloaded, call `unregister_view()` to clean up the registered view:

```python
async def on_unload(self, event):
    if hasattr(self.sdk, 'Dashboard') and self.sdk.Dashboard:
        self.sdk.Dashboard.unregister_view("Weather")
```

After unregistration, the Dashboard frontend will remove sidebar navigation items and page content in real-time via WebSocket, without requiring a page refresh.

---

## Considerations

1. **Loading Order** — The loading priority of Dashboard is `99999` (high priority). Your module's priority should be lower than this value (e.g., `50`) to ensure Dashboard loads first
2. **Defensive Programming** — Wrap view registration with `try/except`, as the Dashboard module might not be installed or loaded
3. **Resource Cleanup** — Call `unregister_view()` in `on_unload` to remove registered views
4. **ID Uniqueness** — The `id` parameter must be unique across the entire Dashboard; it is recommended to use the module name directly
5. **SVG Icon** — `icon_svg` should be a complete `<svg>` tag; recommended size is `viewBox="0 0 24 24"` using `stroke="currentColor"` to inherit the Dashboard theme color
6. **JS Function Naming** — Function names in `js_content` should be unique (e.g., `loadWeatherView`) to avoid conflicts with other modules
7. **Dynamic Updates** — After a module registers/unregisters views, the Dashboard frontend will update the sidebar in real-time via WebSocket, without page refresh



### Takumi 图片渲染

# ErisPulse-Takumi

[ErisPulse-Takumi](https://pypi.org/project/ErisPulse-Takumi/) is a **third-party image rendering module** maintained by ccd2s, based on [takumi-py](https://github.com/BalconyJH/takumi-py), enabling bots to render HTML, node trees, Jinja templates, SVG, and animations into images. The module includes **built-in Chinese and English fonts** (Noto Sans SC / Roboto / Source Code Pro), requiring no additional configuration.

> [!IMPORTANT]
> Takumi is **not** a built-in feature of the ErisPulse framework and must be installed separately:
>
> ```bash
> epsdk install Takumi
> ```

Use Cases:

- Render data/statistics into card images
- Render Markdown / long text into images with stable layout, avoiding platform style differences
- Generate SVG / animations to achieve dynamic visual effects
- Mixed Chinese and English text and images (built-in fonts are ready to use out of the box)

---

## Installation and Enablement

```bash
epsdk install Takumi
```

After installation, the module is automatically loaded. Confirm its enablement in the configuration:

```toml
[Takumi]
enabled = true
```

---



## Quick Start

After modules are automatically loaded, retrieve them via the module manager, or use the `sdk` shortcut:

```python
from ErisPulse import sdk

takumi = sdk.module.get("Takumi")
# Equivalent: takumi = sdk.Takumi
```

### Render HTML

```python
png = takumi.render_html(
    """
    <div class="card">
      <h1>Hello, ErisPulse</h1>
      <p>Rendered by Takumi</p>
    </div>
    """,
    stylesheets=["""
    .card {
      width: 800px;
      padding: 48px;
      color: white;
      background: #111827;
      font-family: "Noto Sans SC";
    }
    """],
    width=800,
    height=None,   # Auto-expand based on content
    lang="zh-CN",
)
```

### Render Node Tree

```python
png = takumi.render_node(
    {
        "type": "text",
        "text": "中文和 English 都可直接渲染",
        "style": {"fontSize": 48, "color": "#111827"},
    },
    width=800,
    height=None,
    lang="zh-CN",
)
```

`png` is `bytes`, which can be sent via `event.reply(png, method="Image")` (see [Sending Rendered Results](#sending-rendered-results)).

---

## Rendering API

`sdk.Takumi` proxies all capabilities of the underlying `takumi_py.Renderer`: all rendering, measuring, SVG, animation, and templating methods can be called directly on `sdk.Takumi`. For these methods, the module automatically injects the **builtin font fallback stack** (`takumi.families`) when called, without requiring manual passing of `font_families`; if explicitly passed, the caller's settings are respected.

### Method Overview

| Category | Method | Return | Description |
|----------|--------|--------|-------------|
| Static Rendering | `render_html(html, ...)` | `bytes` | Render HTML string |
| | `render_node(node, ...)` | `bytes` | Render node tree (dict) |
| | `render_template(name, ctx, ...)` | `bytes` | Render Jinja template |
| | `render_compiled(node, ...)` | `bytes` | Render precompiled node |
| SVG Output | `render_svg_html(html, ...)` | `str` | Output SVG (HTML input) |
| | `render_svg_node(node, ...)` | `str` | Output SVG (node tree input) |
| | `render_svg_template(name, ctx, ...)` | `str` | Output SVG (template input) |
| | `render_svg_compiled(node, ...)` | `str` | Output SVG (precompiled input) |
| Animation | `render_animation(scenes, ...)` | `bytes` | Encode multi-frame animation |
| | `render_sequence_at_time(scenes, time_ms, ...)` | `bytes` | Capture frame at a sequence moment |
| Measuring | `measure_node(node, ...)` | `dict` | Measure node tree layout |
| | `measure_html(html, ...)` | `dict` | Measure HTML layout |
| | `measure_compiled(node, ...)` | `dict` | Measure precompiled node |
| Compiling | `compile_node(node)` | `CompiledNode` | Compile node tree |
| | `compile_html(html, ...)` | `CompiledNode` | Compile HTML |
| Fonts | `register_font(font)` | `list[str]` | Register custom font, returns list of families |
| | `register_fonts(fonts)` | `list[str]` | Batch register fonts |

> `CompiledNode` exposes a `resource_urls()` method, allowing pre-discovery of HTTP(S) image references to be loaded, facilitating preparation of resources in advance.

### Common Parameters

The following parameters apply to static rendering and SVG methods (animation methods have additional parameters like `fps`, see corresponding examples):

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `stylesheets` | `list[str]` | `None` | List of document-level CSS strings; inline `style` is still parsed together with HTML |
| `width` | `int \| None` | `1200` | Viewport width (pixels); `None` infers from layout |
| `height` | `int \| None` | `630` | Canvas height (pixels); `None` auto-stretches to content (see [Viewport and Output Format](#viewport-and-output-format)) |
| `lang` | `str \| None` | `None` | BCP-47 language tag (e.g., `zh-CN`), affecting text shaping and line breaking |
| `font_families` | `list[str]` | Auto-injected | Font fallback stack; convenience methods default to injecting builtin fonts |
| `format` | `str` | `"png"` | Output format (see [Viewport and Output Format](#viewport-and-output-format)) |
| `device_pixel_ratio` | `float` | `1.0` | Device pixel ratio, controlling output resolution |
| `time_ms` | `int` | `0` | Animation sampling moment (milliseconds) |
| `dithering` | `str` | `"none"` | Dithering algorithm: `none` / `ordered-bayer` / `floyd-steinberg` |
| `quality` | `int \| None` | `None` | Lossy encoding quality |
| `lossless` | `bool \| None` | `None` | Whether to encode losslessly |
| `images` | `list` | `None` | Image resources for this render (either `ImageResource` or a `(src, bytes)` tuple) |
| `keyframes` | `Mapping` | `None` | Structured keyframes, no need to write `@keyframes` |
| `options` | `RenderOptions` | — | Aggregate parameters via `RenderOptions(...)`, fields consistent with the table above |

For complete field definitions, see `takumi_py.RenderOptions`.

### Node Tree Example

```python
png = takumi.render_node(
    {
        "type": "container",
        "style": {"padding": "32px", "backgroundColor": "#111827"},
        "children": [
            {"type": "text", "text": "Title", "style": {"fontSize": 32, "color": "white"}},
            {"type": "text", "text": "Body", "style": {"fontSize": 18, "color": "#9ca3af"}},
        ],
    },
    width=800,
    height=None,
    lang="zh-CN",
)
```

### Jinja Template Example

```python
png = takumi.render_template(
    "card.html.jinja",
    {"title": "Takumi", "subtitle": "Jinja to image"},
    stylesheets=["""
    .card {
      width: 800px;
      padding: 48px;
      color: white;
      background: #111827;
    }
    """],
    width=800,
    height=None,
    lang="zh-CN",
)
```

> You can inject custom Jinja filters via `filters={...}` or pass a full `jinja2.Environment` via `environment=...`. See the [takumi-py template documentation](https://github.com/BalconyJH/takumi-py/blob/main/docs/guides/templates.md) for template directory and environment configuration.

### SVG Output Example

```python
svg = takumi.render_svg_html(
    '<div class="card">Hello</div>',
    stylesheets=[".card { width: 800px; color: black; }"],
    width=800,
    height=None,
)
```

### Animation Example

```python
from takumi_py import AnimationScene

webp = takumi.render_animation(
    [
        AnimationScene(
            {"type": "container", "style": {"width": "100%", "height": "100%", "backgroundColor": "black"}},
            duration_ms=100,
        ),
        AnimationScene(
            {"type": "container", "style": {"width": "100%", "height": "100%", "backgroundColor": "white"}},
            duration_ms=100,
        ),
    ],
    width=64,
    height=64,
    fps=20,
    format="webp",
)
```

> Each frame is composed by `AnimationScene(node, duration_ms=...)`, where `duration_ms` must be a positive number.

## Viewport and Output Formats

### Output Format

| Scenario | `format` Value |
|----------|---------------|
| Static Image | `png` (default) / `jpeg` / `jpg` / `webp` / `ico` / `raw` |
| Animation | `webp` (default) / `apng` / `gif` |

`format="raw"` returns row-major RGBA byte stream for custom pixel-level processing.

### About width and height

The roles of `width` and `height` are asymmetrical:

- `width` is the **viewport width**. Text and layout wrap/reflow based on it. **Should be set** to a specific value (e.g., `800`). Otherwise, the canvas stretches based on the natural width of the content and text will not wrap, making the size uncontrollable.
- `height` is the **canvas height**, which grows with the content. The default value of `height` is `630`; when `height=None` is passed, Takumi **automatically extends the canvas based on the content** (auto viewport).

> [!TIP]
> **Recommended combination: Fixed `width` + `height=None`.** Pass a specific `height` only when you need a fixed-size canvas or a cropping effect.

> [!NOTE]
> Either `width` / `height` can technically be passed as `None` to infer from the layout (e.g., when a node declares its own size); when both are provided, the output size is determined.

## Fonts

### Built-in Fonts

| Font | Family | Category |
|------|--------|----------|
| Noto Sans SC | `Noto Sans SC` | sans-serif |
| Roboto | `Roboto` | sans-serif |
| Roboto Italic | `Roboto` | sans-serif (italic) |
| Source Code Pro | `Source Code Pro` | monospace |
| Source Code Pro Italic | `Source Code Pro` | monospace (italic) |

Module attributes:

| Attribute | Description |
|-----------|-------------|
| `takumi.fonts` | List of built-in font filenames |
| `takumi.families` | List of registered font families |

### Automatic Injection

All rendering, measurement, SVG, animation, and template methods on `sdk.Takumi` automatically inject `takumi.families` as a font fallback stack. If calling `takumi.renderer` (native instance) or a standalone instance created via `create_renderer()`, you must manually pass `font_families=takumi.families`.

### Custom Fonts

```python
from takumi_py import FontResource

families = takumi.renderer.register_font(
    FontResource(
        font_bytes,
        name="MyFont",
        weight=400,
        style="normal",
        generic_family="sans-serif",
    )
)
```

`register_font` returns a list of registered family names, which can be passed as `font_families` in subsequent rendering.

## Renderer Instance

### Native Renderer

`takumi.renderer` is the original `takumi_py.Renderer` instance. When calling directly, `font_families` must be passed manually:

```python
png = takumi.renderer.render_html(
    "<div>Hello</div>",
    font_families=takumi.families,
    lang="zh-CN",
)
```

### Standalone Renderer

Create a standalone `Renderer` when isolation of fonts / images / resources is required (long-lived processes, multi-tenant scenarios). Built-in fonts are automatically registered:

```python
renderer = takumi.create_renderer(cache_max_bytes=64 * 1024 * 1024)

png = renderer.render_html(
    "<div>Standalone Renderer</div>",
    font_families=takumi.families,
    width=800,
    height=None,
    lang="zh-CN",
)
```

`create_renderer()` accepts the constructor parameters of `takumi_py.Renderer`:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `load_default_fonts` | `bool` | `False` | Whether to load takumi-py's built-in fonts (built-in fonts are always loaded) |
| `fonts` | `list[FontResource]` | `None` | Additional custom fonts to register |
| `cache_max_bytes` | `int \| None` | `None` | Upper limit for resource cache (bytes); `0` to disable |
| `persistent_images` | `list` | `None` | Persistent image resources |

> Standalone instances do not go through the module proxy. Therefore, to preserve a unified built-in font fallback stack, you must explicitly pass `font_families=takumi.families`. If `font_families` is explicitly passed, the module respects the caller's setting and no longer injects the default fallback stack; `RenderOptions(font_families=...)` is also valid.

## Sending Rendered Results

The rendered image is in `bytes`, which can be sent directly via event reply:

```python
from ErisPulse import sdk

takumi = sdk.Takumi
png = takumi.render_html("<div>hello</div>", lang="zh-CN")

# Method 1: Reply using Image method
await event.reply(png, method="Image")

# Method 2: Reply via OneBot12 message segment
from ErisPulse.Core.Event import MessageBuilder
await event.reply_ob12(
    MessageBuilder().image(png).build()
)
```

> Image handling across different platforms is unified by the adapter. See [MessageBuilder Details](../advanced/message-builder.md) and [Send Method Specifications](../standards/send-method-spec.md).

---

## Configuration

```toml
[Takumi]
enabled = true
```

---



======
平台特性指南
======


### 平台特性总览

# ErisPulse Platform Features Documentation

> Baseline Protocol: [OneBot12](https://12.onebot.dev/)  
> This document is a **platform-specific features guide**, including:  
> - Examples of chainable `Send` method calls supported by each adapter  
> - Platform-specific event/message format explanations  
>  
> General usage methods can be found at:  
> - [Basic Concepts](../getting-started/basic-concepts.md)  
> - [Event Conversion Standards](../standards/event-conversion.md)  
> - [API Response Specifications](../standards/api-response.md)  

---

## Platform-Specific Features

This section is maintained by each adapter developer to explain differences and extended features between the adapter and the OneBot12 standard. Please refer to the detailed documentation for each platform below:

- [Maintenance Notes](maintain-notes.md)  
- [Yunhu Platform Features](docs/en/yunhu.md)  
- [Yunhu User Platform Features](docs/en/yunhu_user.md)  
- [Telegram Platform Features](docs/en/telegram.md)  
- [OneBot11 Platform Features](docs/en/onebot11.md)  
- [OneBot12 Platform Features](docs/en/onebot12.md)  
- [Email Platform Features](docs/en/email.md)  
- [Kook (Let's Play Together) Platform Features](docs/en/kook.md)  
- [Matrix Platform Features](docs/en/matrix.md)  
- [Official QQ Bot Platform Features](docs/en/qqbot.md)  
- [Huafeng Café](docs/en/ideaura.md)  
- [Discord](docs/en/discord.md)  
- [Webhook Protocol Bridge](docs/en/webhook.md)  
- [WeChat Official Account](docs/en/wechatmp.md)  

> Additionally, there is a `sandbox` adapter, but this adapter does not require a platform-specific features document.

---

## General Interfaces

### Chainable `Send` Calls  
All adapters support the following standard calling methods:

> **Note:** `{AdapterName}` in the documentation must be replaced with the actual adapter name (e.g., `yunhu`, `telegram`, `onebot11`, `email`, etc.).

1. Specify type and ID: `To(type, id).Func()`  
   ```python
   # Get adapter instance
   my_adapter = adapter.get("{AdapterName}")
   
   # Send message
   await my_adapter.Send.To("user", "U1001").Text("Hello")
   
   # Example:
   yunhu = adapter.get("yunhu")
   await yunhu.Send.To("user", "U1001").Text("Hello")
   ```
2. Specify only ID: `To(id).Func()`  
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

#### Asynchronous Sending and Result Handling

The methods of the Send DSL return an `asyncio.Task` object, meaning you can choose whether to wait for the result immediately:

```python
# Get adapter instance
my_adapter = adapter.get("{AdapterName}")

# Send message in the background without waiting for result
task = my_adapter.Send.To("user", "123").Text("Hello")

# If you need to get the sending result, you can wait later
result = await task
```

#### Send Rule Decorators

In practical development, it is often necessary to: execute subsequent logic only after successful sending, automatically retry on failure, cancel on timeout, or monitor sending progress. The Send DSL includes a set of built-in send rule decorators that can be attached via chainable methods:

| Method | Description |
|--------|-------------|
| `.Hook(callback)` | Callback executed after successful sending (can be called multiple times) |
| `.Retry(times=1)` | Automatically retry N times on failure (total of N+1 attempts including the first) |
| `.Timeout(seconds)` | Single send timeout, cancel if exceeded (can be stacked with Retry) |
| `.Defer(seconds)` | Delay sending (in-process timing, not persisted) |
| `.OnProgress(callback)` | Progress callback at each stage, passing SendContext |
| `.OnError(callback)` | Error callback when final failure occurs (triggers only once) |

```python
yunhu = adapter.get("yunhu")

# Deduct points only after successful sending
await (yunhu.Send.To("user", "123")
       .Hook(lambda r: deduct_points("123"))
       .Text("Purchase successful"))

# Retry on failure + timeout cancellation + progress monitoring
def on_progress(ctx):
    print(f"Stage: {ctx.stage}, Attempt: {ctx.attempt + 1}/{ctx.max_attempts}")

task = (yunhu.Send.To("user", "123")
        .Retry(3)              # Retry up to 3 times
        .Timeout(10)           # 10-second timeout per attempt
        .OnProgress(on_progress)
        .OnError(lambda ctx: notify_admin(ctx.error))
        .Text("Important notification"))
```

Rule methods return `self`, so they must be called before the sending method (e.g., `Text`, `Image`, etc.). `SendContext` contains fields such as `stage` (pending/sending/retrying/success/failed/timeout), `attempt`, `elapsed`, `error`, `result`, etc., for monitoring purposes.

#### Batch Build Mode (Build)

Build multiple send methods in a single chain, then execute them all at once. This is suitable for scenarios where you need to send multiple messages at once:

```python
yunhu = adapter.get("yunhu")

# Build multiple messages and send them all at once
results = await (yunhu.Send.To("user", "123")
                .Build()                     # Enter build mode
                .Text("Notification 1")
                .Image("pic.jpg")
                .Text("Notification 2")
                .send_all())                 # Execute all at once
# results = [Text result, Image result, Text result]
```

`.send_all()` executes **in parallel** by default (high efficiency). To ensure message arrival order, call `.Sequential()` for sequential execution:

```python
# Sequential execution (ensures order) + retry on failure
await (yunhu.Send.To("group", "456")
       .Build()
       .Sequential()                # Send in order
       .Retry(2)                     # Retry failed items individually
       .Text("First message").Text("Second message")
       .send_all())
```

Batch execution uses a **fail-continue** strategy: if one message fails, it does not interrupt others, and failed items are automatically retried. The batch also supports batch-level `Hook` (triggered after all succeed), `OnError` (triggered when any fail), and `OnProgress` (progress callback).

> For more detailed rules and batch build instructions, see [SendDSL Detailed Explanation](../developer-guide/adapters/send-dsl.md).

### Event Listening  
There are three ways to listen for events:

1. Native platform event listening:
   ```python
   from ErisPulse.Core import adapter, logger
   
   @adapter.on("event_type", raw=True, platform="{AdapterName}")
   async def handler(data):
       logger.info(f"Received native {AdapterName} event: {data}")
   ```

2. OneBot12 standard event listening:
   ```python
   from ErisPulse.Core import adapter, logger

   # Listen for OneBot12 standard events
   @adapter.on("event_type")
   async def handler(data):
       logger.info(f"Received standard event: {data}")

   # Listen for standard events specific to a platform
   @adapter.on("event_type", platform="{AdapterName}")
   async def handler(data):
       logger.info(f"Received {AdapterName} standard event: {data}")
   ```

3. Event module listening:  
   Events based on the `Event` module use the `adapter.on()` function, so the event format provided by the `Event` module is a OneBot12 standard event.

   ```python
   from ErisPulse.Core.Event import message, notice, request, command

   message.on_message()(message_handler)
   notice.on_notice()(notice_handler)
   request.on_request()(request_handler)
   command("hello", help="Send a greeting message", usage="hello")(command_handler)

   async def message_handler(event):
       logger.info(f"Received message: {event}")
   async def notice_handler(event):
       logger.info(f"Received notice: {event}")
   async def request_handler(event):
       logger.info(f"Received request: {event}")
   async def command_handler(event):
       logger.info(f"Received command: {event}")
   ```

The most recommended approach is to use the `Event` module for event handling, as it provides a rich set of event types and various event handling methods.

---

## Standard Formats  
For easy reference, here are simple event formats. For detailed information, please refer to the links above.

> **Note:** The following formats are based on the OneBot12 standard. Each adapter may have extended fields based on this standard. For details, please refer to the specific features documentation for each adapter.

### Standard Event Format  
All adapters must implement the event conversion format:
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
#### Message Sent Successfully
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

#### Message Sent Failed
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
- [Yunhu Adapter Repository](https://github.com/ErisPulse/ErisPulse-YunhuAdapter)  
- [Telegram Adapter Repository](https://github.com/ErisPulse/ErisPulse-TelegramAdapter)  
- [OneBot Adapter Repository](https://github.com/ErisPulse/ErisPulse-OneBotAdapter)  

Related Official Documentation:  
- [OneBot V11 Protocol Documentation](https://github.com/botuniverse/onebot-11)  
- [Telegram Bot API Official Documentation](https://core.telegram.org/bots/api)  
- [Yunhu Official Documentation](https://www.yhchat.com/document/1-3)  

## Contributing  

We welcome more developers to contribute to writing and maintaining adapter documentation! Please follow these steps to submit contributions:  
1. Fork the [ErisPulse](https://github.com/ErisPulse/ErisPulse) repository.  
2. Create a Markdown file in the `docs/platform-features/` directory, naming it as `<Platform Name>.md`.  
3. Add a link to your contributed adapter and related official documentation in this `README.md` file.  
4. Submit a Pull Request.  

Thank you for your support!



### OneBot11 适配

# OneBot11 Platform Feature Documentation

OneBot11Adapter is an adapter built based on the OneBot V11 protocol.

---

## Documentation Information

- Corresponding Module Version: 4.0.0
- Maintainer: ErisPulse

## Basic Information

- Platform Introduction: OneBot is a chatbot application programming interface (API) standard.
- Adapter Name: OneBotAdapter
- Supported Protocol/API Version: OneBot V11
- Multi-account Support: Default multi-account architecture, supports configuring and running multiple OneBot accounts simultaneously.
- Configuration Key Name: `OneBotAdapter`

## Supported Message Sending Types

All sending methods are implemented using a fluent interface, for example:
```python
from ErisPulse.Core import adapter
onebot = adapter.get("onebot11")

# Send using the default account
await onebot.Send.To("group", group_id).Text("Hello World!")

# Specify a particular account for sending
await onebot.Send.Using("main").To("group", group_id).Text("Message from main account")

# Chaining modifiers: @user + reply
await onebot.Send.To("group", group_id).At(123456).Reply(msg_id).Text("Reply message")

# @all members
await onebot.Send.To("group", group_id).AtAll().Text("Announcement message")
```

### Basic Sending Methods

- `.Text(text: str)` : Send plain text message.
- `.Image(file: Union[str, bytes], filename: str = "image.png")` : Send image (supports URL, Base64, or bytes).
- `.Voice(file: Union[str, bytes], filename: str = "voice.amr")` : Send voice message.
- `.Video(file: Union[str, bytes], filename: str = "video.mp4")` : Send video message.
- `.Face(id: Union[str, int])` : Send QQ emoticon.
- `.File(file: Union[str, bytes], filename: str = "file.dat")` : Send file (type is automatically determined).
- `.Raw_ob12(message: List[Dict], **kwargs)` : Send OneBot12 formatted message (automatically converted to OB11).
- `.Recall(message_id: Union[str, int])` : Recall message.

### Group Operation Methods

The following methods must be used with `To("group", group_id)` to specify the target group and execute operations within the group context:

- `.Kick(user_id, reject_add_request=False)` : Kick out group member.
- `.Ban(user_id, duration=1800)` : Mute group member (duration in seconds), 0 means unmute.
- `.WholeBan(enable=True)` : Enable/disable all-mute for the group.
- `.SetAdmin(user_id, enable=True)` : Set/unset group admin.
- `.SetCard(user_id, card="")` : Set group nickname.
- `.SetGroupName(name)` : Change group name.
- `.Leave(is_dismiss=False)` : Leave group (group owner can dismiss).
- `.SetTitle(user_id, title="")` : Set group title.
- `.SetPortrait(file)` : Set group portrait.

### Query Methods

- `.GetMsg(message_id)` : Get message content.
- `.GetForwardMsg(id)` : Get merged forward message.
- `.GetLoginInfo()` : Get current login account information.
- `.GetFriendList()` : Get friend list.
- `.GetGroupInfo()` : Get group information (requires `To("group", group_id)`).
- `.GetGroupList()` : Get group list.
- `.GetGroupMemberInfo(user_id)` : Get group member information (requires `To("group", group_id)`).
- `.GetGroupMemberList()` : Get group member list (requires `To("group", group_id)`).

### Friend Operation Methods

- `.Like(user_id, times=1)` : Send friend like (maximum 10 times).

### Fluent Modifier Methods (Combinable)

Fluent modifier methods return `self`, allowing for chained calls, and must be called before the final sending method:

- `.At(user_id: Union[str, int], name: str = None)` : Mention a specific user (can be called multiple times).
- `.AtAll()` : Mention all members.
- `.Reply(message_id: Union[str, int])` : Reply to a specific message.

### Fluent Call Examples

```python
# Basic sending
await onebot.Send.To("group", 123456).Text("Hello")

# Mention a single user
await onebot.Send.To("group", 123456).At(789012).Text("你好")

# Mention multiple users
await onebot.Send.To("group", 123456).At(111).At(222).At(333).Text("大家好")

# Send OneBot12 formatted message
ob12_msg = [{"type": "text", "data": {"text": "Hello"}}]
await onebot.Send.To("group", 123456).Raw_ob12(ob12_msg)

# Send friend like
await onebot.Send.Like(123456, times=10)

# Mute group member
await onebot.Send.To("group", 123456).Ban(789012, duration=3600)

# Unmute
await onebot.Send.To("group", 123456).Ban(789012, duration=0)

# Kick user
await onebot.Send.To("group", 123456).Kick(789012)

# Set group admin
await onebot.Send.To("group", 123456).SetAdmin(789012)

# Change group name
await onebot.Send.To("group", 123456).SetGroupName("New Group Name")

# Get group info
result = await onebot.Send.To("group", 123456).GetGroupInfo()

# Specify account for operation
await onebot.Send.Using("main").To("group", 123456).Ban(789012)
```

### Handling Unsupported Types

If an undefined sending method is called, the adapter will return a text prompt:
```python
# Call an undefined method
await onebot.Send.To("group", 123456).SomeUnsupportedMethod(arg1, arg2)
# Actually sends: "[Unsupported sending type] Method name: SomeUnsupportedMethod, Parameters: [...]"
```

## Request Operations (Request DSL)

The adapter provides a Request Operations DSL for handling the approval/rejection of friend requests and group requests (group join/invitations).

### Event Shortcut Methods

Request events support `event.approve()` and `event.reject()` shortcut methods, which internally automatically invoke the Request DSL:

```python
from ErisPulse.Core.Event import request

@request.on_friend_request()
async def handle_friend_request(event):
    comment = event.get("comment", "")

    if comment == "passphrase":
        await event.approve()
    else:
        await event.reject()

@request.on_group_request()
async def handle_group_request(event):
    group_id = event.get("group_id")
    await event.approve()
```

### Manually Calling the Request DSL

```python
# Approve the request
await onebot.Request("flag_string").accept()

# Reject the request
await onebot.Request("flag_string").reject()

# Specify account for operation
await onebot.Request("flag_string").Using("main").accept()
```

### Complete Example

```python
from ErisPulse.Core.Event import request

@request.on_friend_request()
async def handle_friend_request(event):
    comment = event.get("comment", "")

    # Method 1: Use Event shortcut methods
    if comment == "passphrase":
        await event.approve()
    else:
        await event.reject()

    # Method 2: Use Request DSL
    flag = event.get("flag")
    if comment == "passphrase":
        await onebot.Request(flag).accept()
    else:
        await onebot.Request(flag).reject()
```

### Request Operation Return Values

```python
{
    "status": "ok",
    "retcode": 0,
    "data": {...},
    "message_id": "",
    "message": ""
}
```

## Event Type Mapping

### Standard OB12 Mapping

| OB11 Original Type | Converted detail_type | Description |
|--------------------|-----------------------|-------------|
| message_type: private | `private` | Private chat message |
| message_type: group | `group` | Group chat message |
| request_type: friend | `friend` | Friend request |
| request_type: group | `group` | Group request |
| meta_event_type: heartbeat | `heartbeat` | Heartbeat |
| notice_type: group_upload | `group_file_upload` | Group file upload |
| notice_type: group_admin | `group_admin_change` | Group admin change |
| notice_type: group_increase | `group_member_increase` | Group member increase |
| notice_type: group_decrease | `group_member_decrease` | Group member decrease |
| notice_type: group_ban | `group_ban` | Group mute |
| notice_type: friend_add | `friend_increase` | Friend added |
| notice_type: friend_delete | `friend_decrease` | Friend removed |
| notice_type: group_recall / friend_recall | `message_recall` | Message recall |

### Platform-specific Events (with `onebot11_` prefix)

| OB11 Original Type | Converted detail_type | Description |
|--------------------|-----------------------|-------------|
| meta_event_type: lifecycle | `onebot11_lifecycle` | OneBot implementation lifecycle |
| notify + sub_type: honor | `onebot11_honor` | Group honor change |
| notify + sub_type: poke | `onebot11_poke` | Poke |
| notify + sub_type: lucky_king | `onebot11_lucky_king` | Group red envelope lucky king |
| Unknown CQ code type | Message segment `onebot11_{type}` | Unrecognized CQ code |

### Event Examples

```python
// Friend request
{
  "type": "request",
  "detail_type": "friend",
  "user_id": "789012",
  "comment": "Please add me as a friend",
  "request_id": "flag_abc123",
  "flag": "flag_abc123"
}

// Heartbeat
{
  "type": "meta_event",
  "detail_type": "heartbeat",
  "interval": 5000,
  "status": {...}
}

// Lifecycle (platform-specific)
{
  "type": "meta_event",
  "detail_type": "onebot11_lifecycle",
  "sub_type": "enable"
}

// Poke (platform-specific)
{
  "type": "notice",
  "detail_type": "onebot11_poke",
  "group_id": "123456",
  "user_id": "789012",
  "target_id": "345678"
}

// Group red envelope lucky king (platform-specific)
{
  "type": "notice",
  "detail_type": "onebot11_lucky_king",
  "group_id": "123456",
  "user_id": "789012",
  "target_id": "345678"
}

// Honor change (platform-specific)
{
  "type": "notice",
  "detail_type": "onebot11_honor",
  "group_id": "123456",
  "user_id": "789012",
  "honor_type": "talkative"
}

// Extended CQ code message segment
{
  "type": "message",
  "message": [
    {"type": "onebot11_shake", "data": {}}
  ]
}
```

### Extended Field Description

- All special fields are prefixed with `onebot11_`
- Original event data is retained in the `onebot11_raw` field
- Original event type is retained in the `onebot11_raw_type` field
- CQ codes in message content are converted to corresponding message segments (standard types without prefix, unknown types with `onebot11_` prefix)
- Reply messages will add a message segment of type `reply`
- Mention messages will add a message segment of type `mention`

## Event Extension Methods

The OneBot11 adapter registers the following platform-specific methods for event objects, which can be directly called within event handlers:

```python
from ErisPulse.Core.Event import message

@message.on_message()
async def handle_message(event):
    raw_self_id = event.get_raw_self_id()
    sender_info = event.get_sender_info()
    sender_role = event.get_sender_role()
```

### Method List

| Method | Return Type | Description |
|--------|-------------|-------------|
| `get_raw_event()` | `dict` | Get the complete raw OneBot11 event data |
| `get_raw_self_id()` | `str` | Get the raw self_id (Bot's QQ number) |
| `get_sender_info()` | `dict` | Get complete sender information (including nickname, role, level, etc.) |
| `get_sender_role()` | `str` | Get the sender's role within the group (owner/admin/member) |
| `get_sender_level()` | `int` | Get the sender's level |
| `get_sender_title()` | `str` | Get the sender's group title |
| `is_system_message()` | `bool` | Determine if it is a system message (sub_type == "system") |

### Usage Examples

```python
from ErisPulse.Core.Event import message, command

@message.on_group_message()
async def handle_group(event):
    role = event.get_sender_role()
    if role == "admin" or role == "owner":
        await event.reply("Administrator, hello!")

    title = event.get_sender_title()
    if title:
        await event.reply(f"Your title is: {title}")

@command("whoami")
async def whoami(event):
    info = event.get_sender_info()
    nickname = info.get("nickname", "Unknown")
    level = event.get_sender_level()
    await event.reply(f"Nickname: {nickname}, Level: {level}")
```

## Configuration Options

The OneBot11 adapter uses a multi-account architecture, where each account is independently configured. The configuration key is `OneBotAdapter`.

### Account Configuration Fields

| Field | Type | Required | Default | Description |
|------|------|------|--------|------|
| `bot_id` | `str` | Yes | `""` | The robot's QQ number, used to identify the account |
| `mode` | `str` | No | `"server"` | Running mode: `"server"` (passive listening) or `"client"` (active connection) |
| `url` | `str` | No | `"ws://127.0.0.1:3001"` | WebSocket address for Client mode |
| `token` | `str` | No | `""` | Authentication Token (Client mode connection token / Server mode validation token) |
| `server_path` | `str` | No | `"/"` | WebSocket path for Server mode |
| `enabled` | `bool` | No | `true` | Whether to enable this account |
| `name` | `str` | No | `""` | Account comment name |

### Built-in Defaults

- Reconnection interval: 30 seconds
- API call timeout: 30 seconds

### Configuration Example

```toml
[OneBotAdapter.accounts.main]
bot_id = "123456789"
mode = "server"
server_path = "/onebot-main"
token = "main_token"
enabled = true

[OneBotAdapter.accounts.backup]
bot_id = "987654321"
mode = "client"
url = "ws://127.0.0.1:3002"
token = "backup_token"
enabled = true

[OneBotAdapter.accounts.test]
bot_id = "111222333"
mode = "client"
url = "ws://127.0.0.1:3003"
enabled = false
```

### Default Configuration

If no accounts are configured, the adapter will automatically create:
```toml
[OneBotAdapter.accounts.default]
bot_id = ""
mode = "server"
server_path = "/"
enabled = true
```

## Send Method Return Values

All send methods return a Task object, which can be awaited directly to obtain the send result. The returned result follows the ErisPulse adapter standardization return specification:

```python
{
    "status": "ok",
    "retcode": 0,
    "data": {...},
    "message_id": "123456",
    "message": "",
    "onebot11_raw": {...}
}
```

### Multi-Account Sending Syntax

```python
# Account selection method
await onebot.Send.Using("main").To("group", 123456).Text("Main account message")
await onebot.Send.Using("backup").To("group", 123456).Image("http://example.com/image.jpg")

# Select account via bot_id
await onebot.Send.Using("123456789").To("group", 123456).Text("Selected by QQ number")

# API call method
await onebot.call_api("send_msg", account_id="main", group_id=123456, message="Hello")
```

### Account Resolution Priority

The resolution priority of the `account_id` parameter in `call_api` and `Using()`:
1. Exact match of account name
2. Match `bot_id` field
3. Match any `str` type field of the account
4. Fall back to the first enabled account

## Asynchronous Processing Mechanism

The OneBot11 adapter adopts an asynchronous non-blocking design to ensure that:
1. Message sending does not block the event handling loop.
2. Multiple concurrent sending operations can be performed simultaneously.
3. API responses can be handled promptly.
4. WebSocket connections remain active.
5. Multiple accounts are processed concurrently, with each account running independently.

## Error Handling

Adapters provide a comprehensive error handling mechanism:
1. Automatic reconnection for network connection failures (supports independent reconnection for each account, with a 30-second interval)
2. API call timeout handling (fixed 30-second timeout)
3. Automatic retry with intervals when connection fails

## Event Handling Enhancement

In multi-account mode, all events automatically include account information:
```python
{
    "type": "message",
    "detail_type": "private",
    "self": {"user_id": "123456789", "platform": "onebot11"},
    "platform": "onebot11",
    // ... other event fields
}
```

The adapter automatically maintains the `self_id → account_name` mapping, so `event.reply()` does not require manually specifying the account and will correctly route back to the originating account.

## Management Interface

```python
# Get all account information
accounts = onebot.accounts

# Check account connection status
connection_status = {
    account_id: connection is not None and not connection.closed
    for account_id, connection in onebot.connections.items()
}

# Dynamically enable/disable accounts (requires adapter restart)
onebot.accounts["test"].enabled = False
```

## self_id Auto Mapping

The adapter will automatically establish a mapping between OneBot `self_id` (QQ number) and `account_name`, which is used for event routing:

```python
# Automatically completed internally by the adapter
# When an event is received, the self.user_id field is filled with bot_id
# The adapter automatically records: self_id("123456789") → account_name("main")

# Therefore, event.reply() can automatically find the correct account to send messages
@message.on_message()
async def handler(event):
    await event.reply("Automatically routed to the correct account")
```



### OneBot12 适配

# OneBot12 Platform Features Documentation

OneBot12Adapter is an adapter built based on the OneBot V12 protocol, serving as the baseline protocol adapter for the ErisPulse framework.

---

## Document Information

- Corresponding Module Version: 4.0.0
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

### Case-Insensitive Method Calls

All sending methods and chain modifiers support case-insensitive calls, and the adapter will automatically map them to the correct standard method names:

```python
# All the following calls are equivalent
await onebot12.Send.To("user", 123).Text("hello")
await onebot12.Send.To("user", 123).text("hello")
await onebot12.Send.To("user", 123).TEXT("hello")

# Chain modifier methods also support case-insensitivity
await onebot12.Send.To("group", 123).At(456).Text("hello")
await onebot12.Send.To("group", 123).at(456).TEXT("hello")
await onebot12.Send.To("group", 123).AT(456).text("hello")
```

### Unsupported Method Calls

When calling an unsupported method, the adapter will return a friendly text message instead of throwing an exception:

```python
# Call an unsupported method
result = await onebot12.Send.To("user", 123).UnsupportedMethod("test")

# The returned result is a text message
# Message content: [Unsupported sending type] Method name: UnsupportedMethod, arguments: [args[0]: 'test']
```

### Basic Message Types

- `.Text(text: str)`: Send a plain text message
- `.Image(file: Union[str, bytes], filename: str = "image.png")`: Send an image message (supports URL, Base64, or bytes)
- `.Audio(file: Union[str, bytes], filename: str = "audio.ogg")`: Send an audio message
- `.Voice(file: Union[str, bytes], filename: str = "voice.ogg")`: Send a voice message (alias for Audio, compatible with OneBot11)
- `.Video(file: Union[str, bytes], filename: str = "video.mp4")`: Send a video message

### Chain Modifier Methods (return self for chaining)

- `.At(user_id: Union[str, int])`: Mention a user (can be called multiple times)
- `.AtAll()`: Mention all members
- `.Reply(message_id: Union[str, int])`: Reply to a message

### Raw Message Sending

- `.Raw_ob12(message: Union[Dict, List[Dict]], **kwargs)`: Send OneBot12 raw format messages (follows naming conventions)

### Other Message Types

- `.Sticker(file_id: str)`: Send a sticker/E-mote
- `.Location(latitude: float, longitude: float, title: str = "", content: str = "")`: Send a location

### Management Functions

- `.Recall(message_id: Union[str, int])`: Recall a message
- `.Edit(message_id: Union[str, int], content: Union[str, List[Dict]])`: Edit a message
- `.Raw(message_segments: List[Dict])`: Send native OneBot12 message segments
- `.Batch(target_ids: List[str], message: Union[str, List[Dict]], target_type: str = "user")`: Send messages in batch

## OneBot12 Standard Events

The OneBot12 adapter fully adheres to the OneBot12 standard. The event format requires no conversion and is submitted directly to the framework.

### New Feature: Raw Event Type Field

Following the `standards/event-conversion.md` specification, all events will retain the raw event type field `onebot12_raw_type`:

```python
{
    "id": "event-id",
    "type": "message",              # Event type
    "onebot12_raw_type": "message", # Raw event type (same as type)
    "detail_type": "private",
    "self": {"user_id": "bot-id"},
    "user_id": "user-id",
    "message": [{"type": "text", "data": {"text": "Hello"}}],
    "alt_message": "Hello",
    "time": 1234567890
}
```

### Message Events (Message Events)

```python
# Private message
{
    "id": "event-id",
    "type": "message",
    "onebot12_raw_type": "message",
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
    "onebot12_raw_type": "message",
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
    "onebot12_raw_type": "notice",
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
    "onebot12_raw_type": "notice",
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
    "onebot12_raw_type": "request",
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
    "onebot12_raw_type": "request",
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
    "onebot12_raw_type": "meta_event",
    "detail_type": "lifecycle",
    "self": {"user_id": "bot-id"},
    "sub_type": "enable",
    "time": 1234567890
}

# Heartbeat event
{
    "id": "event-id",
    "type": "meta_event",
    "onebot12_raw_type": "meta_event",
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

### Message Sending Methods
All message sending methods (such as `.Text()`, `.Image()`, `.Raw_ob12()` etc.) return an `asyncio.Task` object, which can be directly awaited to obtain the sending result:

```python
task = await onebot12.Send.To("group", 123456).Text("Hello")
```

### Chain Modifier Methods
All chain modifier methods (such as `.At()`, `.AtAll()`, `.Reply()`) return `self`, supporting chain calls:

```python
# Combine multiple modifier methods
await onebot12.Send.To("group", 123456).Reply("msg123").At(789).At(790).Text("Text")
```

## API Response Standard

The adapter follows the ErisPulse standardized return specification (`standards/api-response.md`):

```python
# Success response
{
    "status": "ok",              // Required: execution status
    "retcode": 0,                // Required: return code (0 indicates success)
    "data": {                     // Required: response data
        "message_id": "123456",
        "time": 1632847927.599013
    },
    "message_id": "123456",       // Required: message ID (empty string if none)
    "message": "",                // Required: error message (empty if successful)
    "echo": "1234",               // Optional: echo returned from the original request
    "onebot12_raw": {...}        // Optional: raw response data
}

# Failure response
{
    "status": "failed",           // Required: execution status
    "retcode": 10003,            // Required: return code (non-zero indicates failure)
    "data": None,                // Required: null on failure
    "message_id": "",            // Required: empty string on failure
    "message": "Missing required parameter",    // Required: error description
    "echo": "1234",              // Optional: echo returned from the original request
    "onebot12_raw": {...}        // Optional: raw response data
}
```

### Error Code Specification

Follows OneBot12 standard error codes:

- **0**: Success
- **1xxxx**: Action request error
- **2xxxx**: Action handler error
- **3xxxx**: Action execution error (33001 for network timeout)

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

1. Message sending does not block the event handling loop
2. Multiple concurrent sending operations can proceed simultaneously
3. API responses can be processed in a timely manner
4. WebSocket connections remain active
5. Multi-account concurrency processing, with each account running independently

## Error Handling

The adapter provides comprehensive error handling mechanisms:

1. Automatic reconnection for network connection exceptions (supports independent reconnection for each account, interval of 30 seconds)
2. API call timeout handling (fixed 30-second timeout)
3. Automatic retry for failed message sending (maximum 3 retries)
4. Unsupported method calls will return a friendly text message

## Event Processing Enhancement

In multi-account mode, account information is automatically added to all events:

```python
{
    "type": "message",
    "onebot12_raw_type": "message",  // Raw event type
    "detail_type": "private",
    "self": {"user_id": "123456"},  // Account ID that sent the event (standard field)
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

1. **Configuration Management**: It is recommended to use multi-account configuration to manage bots of different purposes separately.
2. **Error Handling**: Always check the return status of API calls.
3. **Message Sending**: Use appropriate message types and avoid sending unsupported messages.
4. **Connection Monitoring**: Regularly check connection status to ensure service availability.
5. **Performance Optimization**: Use the Batch method for sending to reduce network overhead when sending in bulk.
6. **Method Calls**: It is recommended to use standard PascalCase naming (such as `.Text()`), but lowercase forms are also supported for compatibility with different coding styles (this approach may be incompatible with older versions)



### Telegram 适配

﻿# Telegram Platform Feature Documentation

TelegramAdapter is an adapter built on the Telegram Bot API, supporting various message types and event handling.

---

## Document Information

- Corresponding Module Version: 4.1.1
- Maintainer: ErisPulse

## Basic Information

- Platform Overview: Telegram is a cross-platform instant messaging software.
- Adapter Name: TelegramAdapter
- Supported Protocol/API Version: Telegram Bot API
- Session Type Mapping: `private` → use `user` when sending, `group`/`supergroup` → `group`, `channel` → `channel`

## Supported Message Sending Types

All sending methods use a fluent API syntax, for example:
```python
from ErisPulse.Core import adapter
telegram = adapter.get("telegram")

await telegram.Send.To("user", user_id).Text("Hello World!")
```

### Basic Sending Methods

| Method | Description | Parameters |
|------|------|------|
| `.Text(text)` | Send plain text message | `text: str` |
| `.Face(emoji)` | Send emoji dice | `emoji: str` (e.g., 🎲 🎯 🏀) |
| `.Markdown(text, content_type)` | Send Markdown formatted message | `content_type` defaults to `"MarkdownV2"` |
| `.HTML(text)` | Send HTML formatted message | `text: str` |
| `.Sticker(file)` | Send sticker | `file: str (file_id/URL) \| bytes` |
| `.Location(lat, lng)` | Send location | `latitude: float, longitude: float` |
| `.Venue(lat, lng, title, addr)` | Send venue | Includes title and address |
| `.Contact(phone, first, last)` | Send contact | Includes phone number and name |

### Media Sending Methods

All media methods support both `bytes` (upload) and `str` (file_id / URL) inputs:

| Method | Description |
|------|------|
| `.Image(file, caption, content_type)` | Send image |
| `.Video(file, caption, content_type)` | Send video |
| `.Voice(file, caption)` | Send voice |
| `.Audio(file, caption, content_type)` | Send audio |
| `.File(file, caption)` | Send file |
| `.Document(file, caption, content_type)` | Alias for File |

### Message Management Methods

| Method | Description |
|------|------|
| `.Edit(message_id, text, content_type)` | Edit existing message |
| `.Recall(message_id)` | Delete specified message |
| `.Forward(from_chat_id, message_id)` | Forward message (preserving source) |
| `.CopyMessage(from_chat_id, message_id)` | Copy message (without source) |
| `.AnswerCallback(callback_query_id, text, show_alert)` | Answer callback query |

### Raw Message Sending

- `.Raw_ob12(message: List[Dict])`: Send OneBot12 standard format message
- `.Raw_json(json_str: str)`: Send raw JSON format message

### Fluent Modifier Methods

| Method | Description |
|------|------|
| `.At(user_id)` | Mention a specified user (using Telegram entities, can be called multiple times) |
| `.AtAll()` | Mention all members (sends `@All` text) |
| `.Reply(message_id)` | Reply to a specified message |
| `.Keyboard(inline_keyboard)` | Set inline keyboard (`list[list[dict]]`) |
| `.ProtectContent(protect)` | Protect content (prevent forwarding and saving) |
| `.Silent(silent)` | Send silently (no user notification) |

### Sending Examples

```python
# Basic text sending
await telegram.Send.To("user", user_id).Text("Hello World!")

# Message with inline keyboard
from ErisPulse import sdk
telegram = sdk.adapter.get("telegram")
keyboard = [
    [{"text": "Button1", "callback_data": "btn1"}, {"text": "Button2", "callback_data": "btn2"}],
    [{"text": "Visit Website", "url": "https://example.com"}],
]
await telegram.Send.To("group", group_id).Keyboard(keyboard).Text("Please select:")

# Media sending (using URL)
await telegram.Send.To("group", group_id).Image("https://example.com/image.jpg", caption="Image")

# @ user
await telegram.Send.To("group", group_id).At("6117725680").Text("Hello!")

# Reply + protect content
await telegram.Send.To("group", group_id).Reply("12345").ProtectContent().Text("Secret message")

# Silent sending
await telegram.Send.To("group", group_id).Silent().Text("Silent notification")

# Answer callback query
await telegram.Send.AnswerCallback(callback_query_id, text="Processed", show_alert=False)

# OneBot12 composite message
ob12_message = [
    {"type": "text", "data": {"text": "Complex message: "}},
    {"type": "mention", "data": {"user_id": "6117725680", "user_name": "Username"}},
    {"type": "reply", "data": {"message_id": "12345"}},
    {"type": "image", "data": {"file": "https://http.cat/200"}}
]
await telegram.Send.To("group", group_id).Raw_ob12(ob12_message)

# Send sticker
await telegram.Send.To("user", user_id).Sticker("CAACAgIAAxkBAA...")  # file_id

# Send location
await telegram.Send.To("user", user_id).Location(39.9042, 116.4074)
```

## Unique Event Types

Telegram events are converted according to the OneBot12 standard, with platform extensions provided via the `telegram_` prefix.

### Message Event detail_type Mapping

| Telegram chat.type | OneBot12 detail_type | Target Type |
|---|---|---|
| `private` | `private` | `user` |
| `group` | `group` | `group` |
| `supergroup` | `group` | `group` |
| `channel` | `channel` | `channel` |

### Unique Event Types

| detail_type | Description |
|---|---|
| `telegram_callback_query` | Callback query (inline keyboard button click) |
| `telegram_inline_query` | Inline query |
| `telegram_chosen_inline_result` | Chosen inline result |
| `telegram_poll` | Poll event |
| `telegram_poll_answer` | Poll answer |
| `telegram_my_chat_member` | Bot member status change |
| `telegram_chat_member` | Chat member change |
| `telegram_chat_join_request` | Join chat request |
| `telegram_shipping_query` | Shipping query |
| `telegram_pre_checkout_query` | Pre-checkout query |

### Standard Message Segment Types

Converted message segments use the OneBot12 standard format:

| Message Segment Type | Description | data Fields |
|---|---|---|
| `text` | Plain text (without @username) | `text` |
| `mention` | @user (standard OB12) | `user_id`, `user_name` |
| `reply` | Reply reference | `message_id`, `user_id` |
| `image` | Image | `file_id`, `url` |
| `video` | Video | `file_id`, `url`, `duration`, `width`, `height` |
| `voice` | Voice | `file_id`, `url`, `duration` |
| `audio` | Audio | `file_id`, `url`, `duration`, `title`, `performer` |
| `file` | File | `file_id`, `url`, `file_name`, `file_size`, `mime_type` |
| `location` | Location | `latitude`, `longitude`, optional `title`, `address` |

### Platform Extension Message Segments

Message segments marked with the `telegram_` prefix:

| Message Segment Type | Description | data Fields |
|---|---|---|
| `telegram_sticker` | Sticker | `file_id`, `emoji`, `sticker_type`, `url` |
| `telegram_animation` | GIF animation | `file_id`, `url`, `duration`, `caption` |
| `telegram_contact` | Contact | `phone_number`, `first_name`, `last_name`, `user_id` |
| `telegram_inline_keyboard` | Inline keyboard | `inline_keyboard` |

### Event Examples

#### Group Message (with @mention)
```python
{
  "type": "message",
  "detail_type": "group",
  "platform": "telegram",
  "user_id": "6117725680",
  "user_nickname": "WSu2059",
  "group_id": "-1002850921906",
  "message_id": "172",
  "message": [
    {"type": "text", "data": {"text": "/it.echo "}},
    {"type": "mention", "data": {"user_id": "", "user_name": "@nm123_91178"}}
  ],
  "alt_message": "/it.echo @nm123_91178",
  "telegram_chat": {
    "id": -1002850921906,
    "title": "ErisPulse",
    "username": "erispulse",
    "type": "supergroup"
  }
}
```

#### Callback Query Event
```python
{
  "type": "notice",
  "detail_type": "telegram_callback_query",
  "user_id": "123456",
  "user_nickname": "YingXinche",
  "telegram_callback_id": "cb_123",
  "telegram_callback_data": "callback_data",
  "message_id": "msg_456"
}
```

#### Inline Query Event
```python
{
  "type": "request",
  "detail_type": "telegram_inline_query",
  "user_id": "789012",
  "user_nickname": "YingXinche",
  "telegram_query_id": "iq_789",
  "telegram_query_text": "search_text",
  "telegram_query_offset": "0"
}
```

#### Message with Inline Keyboard
```python
{
  "type": "message",
  "detail_type": "group",
  "message": [
    {"type": "text", "data": {"text": "Please select: "}},
    {
      "type": "telegram_inline_keyboard",
      "data": {
        "inline_keyboard": [
          [{"text": "Button1", "callback_data": "btn1"}],
          [{"text": "Visit", "url": "https://example.com"}]
        ]
      }
    }
  ]
}
```

## Event Mixin Extension Methods

The adapter registers the following platform-specific methods, available only when `platform == "telegram"`:

### Message Related

| Method | Return Type | Description |
|------|----------|------|
| `is_bot_message()` | `bool` | Check if message is from bot |
| `is_edited_message()` | `bool` | Check if message is edited |
| `is_topic_message()` | `bool` | Check if message is topic message |
| `get_update_id()` | `int` | Get Telegram update ID |
| `get_chat_title()` | `str` | Get chat title |
| `get_chat_username()` | `str` | Get chat username |
| `get_forward_from()` | `dict` | Get forwarding source info |
| `get_topic_id()` | `str` | Get topic ID |

### Callback Query Related

| Method | Return Type | Description |
|------|----------|------|
| `get_callback_data()` | `str` | Get callback query's callback_data |
| `get_callback_id()` | `str` | Get callback query ID (for answering) |

### Message Segment Data Extraction

| Method | Return Type | Description |
|------|----------|------|
| `get_inline_keyboard()` | `list` | Get inline keyboard from message |
| `get_sticker_info()` | `dict` | Get sticker info |
| `get_contact_info()` | `dict` | Get contact info |
| `get_location()` | `dict` | Get location info |

### Usage Examples

```python
from ErisPulse.Core.Event import message, notice

@message.on_message()
async def handle_message(event):
    if event.get("platform") != "telegram":
        return

    # Message properties
    if event.is_bot_message():
        return  # Ignore bot messages

    if event.is_edited_message():
        print("This is an edited message")

    # Chat information
    title = event.get_chat_title()
    username = event.get_chat_username()

    # Forward source
    forward = event.get_forward_from()

    # Message segment data
    sticker = event.get_sticker_info()
    contact = event.get_contact_info()
    location = event.get_location()
    keyboard = event.get_inline_keyboard()

    # Topic
    if event.is_topic_message():
        topic_id = event.get_topic_id()

@notice.on_notice()
async def handle_notice(event):
    if event.get("platform") != "telegram":
        return

    if event.get("detail_type") == "telegram_callback_query":
        callback_data = event.get_callback_data()
        callback_id = event.get_callback_id()

        # Answer callback query
        telegram = sdk.adapter.get("telegram")
        await telegram.Send.AnswerCallback(callback_id, text="Clicked")

        # Reply to message
        await event.reply(f"You clicked: {callback_data}")
```

## Extension Field Explanation

- All unique fields are prefixed with `telegram_`
- Original data is preserved in the `telegram_raw` field
- Original event type is preserved in the `telegram_raw_type` field
- Channel messages use `detail_type="channel"`
- Private chat messages use `detail_type="private"` (must be converted to `user` when sending)
- Topic messages include the `thread_id` field
- `@` mentions use the standard `mention` message segment type (`type: "mention"`), with no `@username` in the text

## Configuration Options

The Telegram adapter supports multi-account configuration:

### Configuration Example
```toml
[Telegram_Adapter.accounts.default]
token = "YOUR_BOT_TOKEN"
enabled = true

[Telegram_Adapter.accounts.bot2]
token = "ANOTHER_BOT_TOKEN"
enabled = true
```

### Running Mode

The Telegram adapter only supports **Polling** mode; Webhook mode has been removed.

### Proxy Configuration

If you need to connect to the Telegram API through a proxy, use system-level proxy settings (environment variables `ALL_PROXY` / `HTTPS_PROXY`).

### Migration from Old Configuration

Old single-token configurations are automatically compatible:
```toml
# Old format (still usable, but migration is recommended)
[Telegram_Adapter]
token = "YOUR_BOT_TOKEN"
```

Migration to the new format is recommended:
```toml
[Telegram_Adapter.accounts.default]
token = "YOUR_BOT_TOKEN"
enabled = true
```



### 云湖适配

# Yunhu Platform Feature Documentation

YunhuAdapter is an adapter built based on the Yunhu protocol, integrating all Yunhu functional modules and providing a unified interface for event handling and message operations.

---

## Documentation Information

- Corresponding Module Version: 4.3.0
- Maintainer: ErisPulse

## Basic Information

- Platform Introduction: Yunhu is an enterprise-level instant messaging platform.
- Adapter Name: YunhuAdapter
- Multi-account Support: Supports identifying and configuring multiple Yunhu robot accounts through bot_id.
- Chainable Modifier Support: Supports chainable modifier methods such as `.Reply()`.
- OneBot12 Compatibility: Supports sending messages in OneBot12 format.

## Supported Message Sending Types

All sending methods are implemented through a fluent interface syntax, for example:
```python
from ErisPulse.Core import adapter
yunhu = adapter.get("yunhu")

await yunhu.Send.To("user", user_id).Text("Hello World!")
```

The supported sending types include:
- `.Text(text: str)`: Sends a plain text message.
- `.Html(html: str)`: Sends an HTML formatted message.
- `.Markdown(markdown: str)`: Sends a Markdown formatted message.
- `.A2UI(text: str)`: Sends an A2UI formatted message.
- `.Image(file: bytes, stream: bool = False, filename: str = None)`: Sends an image message, supports streaming upload and custom filename.
- `.Video(file: bytes, stream: bool = False, filename: str = None)`: Sends a video message, supports streaming upload and custom filename.
- `.File(file: bytes, stream: bool = False, filename: str = None)`: Sends a file message, supports streaming upload and custom filename.
- `.Batch(target_ids: List[str], message: str, content_type: str = "text", **kwargs)`: Sends a batch message.
- `.Edit(msg_id: str, text: str, content_type: str = "text", buttons: List = None)`: Edits an existing message.
- `.Recall(msg_id: str)`: Recalls a message.
- `.Board(content: str, content_type: str = "text")`: Publishes a bulletin board message. The scope is inferred from `To()` (specifying target = local board, not specifying = global board). Chaining modifiers: `.Expire(duration)` for relative expiration (seconds), `.ExpireAt(timestamp)` for absolute expiration (second-level timestamp), `.ForMember(member_id)` for group member board; **automatically撤销 the board when content is empty**. Still compatible with the old-style `Board("local", "公告")` explicit scope syntax.
- `.DismissBoard()`: Dismisses a bulletin board message. The scope is similarly inferred from `To()`, supports `.ForMember(member_id)`; still compatible with the old-style `DismissBoard("local")` syntax.
- `.Stream(content_type: str, content_generator: AsyncGenerator, **kwargs)`: Sends a streaming message.

### Group Management Methods

All group management methods require specifying the group through a fluent interface syntax, for example:
```python
from ErisPulse.Core import adapter
yunhu = adapter.get("yunhu")

await yunhu.Send.To("group", group_id).Kick(user_id)
```

- `.Kick(user_id: str)`: Removes a group member. The bot needs the `allow remove group member` permission.
- `.Ban(user_id: str, duration: int = 600)`: Mutes a user. `duration` specifies the mute duration (seconds), 0 means unmute, -1 means permanent mute. The bot needs the `allow mute user` permission.
- `.CreateTag(tag: str, color: str = None, desc: str = None, sort: int = None)`: Creates a group tag. `color` is in the format #RRGGBB, `sort` determines the order (smaller values appear earlier). The bot needs the `allow control tag group` permission.
- `.EditTag(tag: str, new_tag: str = None, color: str = None, desc: str = None, sort: int = None)`: Edits a group tag. Each parameter is optional, and if not provided, it will not be modified. The bot needs the `allow control tag group` permission.
- `.DeleteTag(tag: str)`: Deletes a group tag. The bot needs the `allow control tag group` permission.
- `.GetTagList()`: Retrieves the group tag list. Returns a response containing a `list` array.
- `.AddUserTag(user_id: str, tag: str)`: Adds a tag to a user. The bot needs the `allow control tag group` permission.
- `.RemoveUserTag(user_id: str, tag: str)`: Removes a tag from a user. The bot needs the `allow control tag group` permission.
- `.SetMsgTypeLimit(types: str)`: Controls message types within the group. `types` is a comma-separated string of message type names (e.g., `"text,image,video"`), an empty string means no restriction. The bot needs the `allow modify group info` permission.

### Message Query Methods

To retrieve the history message list of a specified conversation (user/group), you need to specify the target through a fluent interface syntax, for example:
```python
from ErisPulse.Core import adapter
yunhu = adapter.get("yunhu")

result = await yunhu.Send.To("group", group_id).GetMessages(before=10)
```

- `.GetMessages(message_id: str = None, before: int = None, after: int = None)`: Retrieves the conversation history messages. Returns a response containing a `list` array and `total` count.
  - `message_id`: Message ID (optional). If not provided, combined with `before` returns the most recent N messages.
  - `before`: Returns the N messages before the specified message ID.
  - `after`: Returns the N messages after the specified message ID.
  - > **Note:** At least one of `before` and `after` must be specified and greater than 0, otherwise the server will not return any messages.

The board scope is automatically inferred by `To()`:
- Specifying `To(target_type, target_id)` → local board (specific user/group)
- Not specifying `To()` → global board

```python
# Local board (expires after 60 seconds)
await yunhu.Send.To("group", group_id).Expire(60).Board("公告", content_type="markdown")

# Group member board (visible only to the specified member)
await yunhu.Send.To("group", group_id).ForMember(user_id).Board("visible only to you")

# Absolute timestamp expiration
await yunhu.Send.To("group", group_id).ExpireAt(1785208268).Board("expires at specified time")

# Global board
await yunhu.Send.Board("global announcement")

# Clear local board (empty content → automatically撤销)
await yunhu.Send.To("group", group_id).Board("")
```

### Button Parameter Description

The `buttons` parameter is a nested list representing the layout and functionality of buttons. Each button object contains the following fields:

| Field         | Type   | Required | Description                                                                 |
|---------------|--------|----------|-----------------------------------------------------------------------------|
| `text`        | string | Yes      | The text on the button                                                      |
| `actionType`  | int    | Yes      | Action type:<br>`1`: Navigate to URL<br>`2`: Copy<br>`3`: Report on click    |
| `url`         | string | No       | Used when `actionType=1`, represents the target URL for navigation          |
| `value`       | string | No       | When `actionType=2`, this value will be copied to the clipboard<br>When `actionType=3`, this value will be sent to the subscriber |

Example:
```python
buttons = [
    [
        {"text": "Copy", "actionType": 2, "value": "xxxx"},
        {"text": "Click to Navigate", "actionType": 1, "url": "http://www.baidu.com"},
        {"text": "Report Event", "actionType": 3, "value": "xxxxx"}
    ]
]
await yunhu.Send.To("user", user_id).Buttons(buttons).Text("Message with buttons")
```
> **Note:**
> - Only clicking the **report event** button will trigger a push notification; **copy** and **navigate URL** actions will not trigger a push notification.

### Chaining Modifier Methods (can be combined)

Chaining modifier methods return `self`, support chaining, and must be called before the final sending method:

- `.Reply(message_id: str)`: Replies to a specified message.
- `.At(user_id: str)`: Mentions a specified user.
- `.AtAll()`: Mentions everyone.
- `.Buttons(buttons: List)`: Adds buttons.

### Chaining Call Examples

```python
# Basic sending
await yunhu.Send.To("user", user_id).Text("Hello")

# Reply to a message
await yunhu.Send.To("group", group_id).Reply(msg_id).Text("Reply message")

# Reply + buttons
await yunhu.Send.To("group", group_id).Reply(msg_id).Buttons(buttons).Text("Message with reply and buttons")
```

### Group Management Examples

```python
from ErisPulse.Core import adapter
yunhu = adapter.get("yunhu")

# Remove a group member
await yunhu.Send.To("group", group_id).Kick(user_id)

# Mute a user (10 minutes)
await yunhu.Send.To("group", group_id).Ban(user_id, duration=600)

# Unmute
await yunhu.Send.To("group", group_id).Ban(user_id, duration=0)

# Permanent mute
await yunhu.Send.To("group", group_id).Ban(user_id, duration=-1)

# Create a group tag
await yunhu.Send.To("group", group_id).CreateTag("VIP User", color="#FF5733", desc="VIP Member")

# Edit a group tag
await yunhu.Send.To("group", group_id).EditTag("VIP User", new_tag="SVIP User", color="#33C4FF")

# Delete a group tag
await yunhu.Send.To("group", group_id).DeleteTag("VIP User")

# Retrieve group tag list
result = await yunhu.Send.To("group", group_id).GetTagList()

# Add a tag to a user
await yunhu.Send.To("group", group_id).AddUserTag(user_id, "VIP User")

# Remove a tag from a user
await yunhu.Send.To("group", group_id).RemoveUserTag(user_id, "VIP User")

# Set message type restriction
await yunhu.Send.To("group", group_id).SetMsgTypeLimit("text,image,video")

# Remove message type restriction
await yunhu.Send.To("group", group_id).SetMsgTypeLimit("")
```

### Message Query Examples

```python
from ErisPulse.Core import adapter
yunhu = adapter.get("yunhu")

# Retrieve the last 10 messages in the group (returns 10 messages total)
result = await yunhu.Send.To("group", group_id).GetMessages(before=10)

# Retrieve the 10 messages before the specified message ID in the group (returns 11 messages total)
result = await yunhu.Send.To("group", group_id).GetMessages(message_id="msg_xxx", before=10)

# Retrieve 10 messages before and after the specified message ID in the group (returns 21 messages total)
result = await yunhu.Send.To("group", group_id).GetMessages(message_id="msg_xxx", before=10, after=10)

# Retrieve history messages in a user conversation
result = await yunhu.Send.To("user", user_id).GetMessages(message_id="msg_xxx", before=10)
```

### OneBot12 Message Support

The adapter supports sending OneBot12 formatted messages for cross-platform message compatibility:

- `.Raw_ob12(message: List[Dict], **kwargs)`: Sends a OneBot12 formatted message.

```python
# Send a OneBot12 formatted message
ob12_msg = [{"type": "text", "data": {"text": "Hello"}}]
await yunhu.Send.To("user", user_id).Raw_ob12(ob12_msg)

# Combined with chaining modifiers
ob12_msg = [{"type": "text", "data": {"text": "Reply message"}}]
await yunhu.Send.To("group", group_id).Reply(msg_id).Raw_ob12(ob12_msg)
```

## Standard API Actions (ApiDSL)

> [!NOTE]
> This feature requires ErisPulse **2.7.0+** and YunhuAdapter **4.3.0+**.

In addition to the `Send` fluent interface for sending messages, the adapter also provides the `Api` inner class, exposing standard OneBot12 API actions and platform extensions for Yunhu. All methods return a standard response format.

```python
from ErisPulse.Core import adapter
yunhu = adapter.get("yunhu")

# Information queries (via public Web API, no authentication required)
result = await yunhu.Api.get_self_info()              # Bot self information
result = await yunhu.Api.get_user_info("7058262")     # Any user information
result = await yunhu.Api.get_group_info("635409929")  # Group information

# File operations
result = await yunhu.Api.upload_file(type="path", name="a.png", path="./a.png")
result = await yunhu.Api.get_file("https://chat-file.jwznb.com/xxx")

# Message recall (requires additional chat_id + chat_type)
await yunhu.Api.delete_message("msg_id", chat_id="123", chat_type="group")

# Multi-account: specify Bot account
info = await yunhu.Api.Using("bot1").get_self_info()
```

### Supported Standard Actions

| Method | Description | Data Source |
|--------|-------------|-------------|
| `get_self_info()` | Bot self information | Public Web API (bot-info) |
| `get_user_info(user_id)` | User information (any user can be queried) | Public Web API (user/homepage) |
| `get_group_info(group_id)` | Group information | Public Web API (group-info) |
| `upload_file(*, type, name, ...)` | Upload file (automatically detects image/video/file) | Bot open API |
| `get_file(file_id)` | Get file (file_id is the URL) | — |
| `delete_message(message_id, *, chat_id, chat_type)` | Recall message | Bot open API (/bot/recall) |

> **Note**: `get_self_info` / `get_user_info` / `get_group_info` are implemented via **non-official public Web APIs** (chat-web-go.jwzhd.com). These interfaces require no authentication but are not officially documented and may change with platform updates; failures return standard error responses.

### Unsupported Standard Actions

The following standard actions do not have corresponding APIs on Yunhu, and calling them returns `retcode=10002` (unsupported operation):
- `get_friend_list` (the "bot user list" of the Bot open API is still pending launch)
- `get_group_list` / `get_group_member_info` / `get_group_member_list`
- `set_group_name` / `leave_group`

### Platform Extension Actions

Call Yunhu-specific actions using `Api.call("yunhu.xxx", **params)` (parameters use OB12-style naming, and the adapter automatically translates them to Yunhu fields):

| Extension Action | Description | Equivalent Send Method |
|------------------|-------------|------------------------|
| `yunhu.recall` | Recall message (msg_id, chat_id, chat_type) | `Send.To(...).Recall(msg_id)` |
| `yunhu.kick` | Remove group member (group_id, user_id) | `Send.To("group", g).Kick(uid)` |
| `yunhu.ban` | Mute (group_id, user_id, duration) | `Send.To("group", g).Ban(uid, duration)` |
| `yunhu.unban` | Unmute (group_id, user_id) | `Send.To("group", g).Ban(uid, duration=0)` |
| `yunhu.tag.create/edit/delete/list` | Group tag CRUD (group_id, ...) | `Send.To("group", g).CreateTag(...)` etc. |
| `yunhu.tag.relate` / `yunhu.tag.relate_cancel` | Add/remove tag to/from user | `Send.To("group", g).AddUserTag(...)` etc. |
| `yunhu.set_member_title` / `yunhu.unset_member_title` | **Member title semantic alias** (tag ≈ title, internally mapped to tag.relate) | — |
| `yunhu.msg_type_limit` | Group message type restriction (group_id, type) | `Send.To("group", g).SetMsgTypeLimit(...)` |
| `yunhu.get_messages` | Get historical messages (chat_id, chat_type, message_id?, before?, after?) | `Send.To(...).GetMessages(...)` |
| `yunhu.bot_info` | Public bot-info query (bot_id) | — |
| `yunhu.user_homepage` | Public user homepage query (user_id) | — |

```python
# Example of platform extensions
await yunhu.Api.call("yunhu.kick", group_id="123", user_id="456")
await yunhu.Api.call("yunhu.set_member_title", group_id="123", user_id="456", title="VIP")
result = await yunhu.Api.call("yunhu.get_messages", chat_id="123", chat_type="group", before=10)
```

> **Tags and Titles**: On Yunhu, the semantic meaning of "tags" is equivalent to OneBot12 group member `title`. `yunhu.set_member_title` is a native semantic alias for `yunhu.tag.relate`, and both internally map to the same endpoint. In group message events, the sender's role is mapped from `senderUserLevel` to the standard `role` field (owner/admin/member).

## Return Values of Send Methods

All send methods return a Task object, which can be directly awaited to obtain the send result. The returned result follows the ErisPulse adapter's standardized return specification:

```python
{
    "status": "ok",           // Execution status
    "retcode": 0,             // Return code
    "data": {...},            // Response data
    "self": {...},            // Self information (including bot_id)
    "message_id": "123456",   // Message ID
    "message": "",            // Error message
    "yunhu_raw": {...}        // Raw response data
}
```

## Unique Event Types

Platform-specific features should be used only after checking `platform=="yunhu"`

### Core Differences

1. Unique Event Types:
    - Form (e.g., form command): `yunhu_form`
    - Emoji/Sticker Message Segment: `yunhu_expression`
    - Button Click: `yunhu_button_click`
    - A2UI Button Click: `yunhu_a2ui_button`
    - Bot Setting: `yunhu_bot_setting`
    - Quick Menu: `yunhu_shortcut_menu`
2. Standard Field Extension (4.3.0+):
    - Standard `role` field added to message events (mapped from Yunhu's `senderUserLevel` to `owner`/`admin`/`member`)
    - New `user_avatar` field added (sender's avatar URL)
3. Extended Fields:
    - All extended fields are prefixed with `yunhu_`
    - Original data is preserved in the `yunhu_raw` field
    - In private chats, `self.user_id` represents the bot ID

### Special Field Examples

```python
# Form Command
{
  "type": "message",
  "detail_type": "private",
  "yunhu_command": {
    "name": "Form Command Name",
    "id": "Command ID",
    "form": {
      "Field ID1": {
        "id": "Field ID1",
        "type": "input/textarea/select/radio/checkbox/switch",
        "label": "Field Label",
        "value": "Field Value"
      }
    }
  }
}

# Button Click Event
{
  "type": "notice",
  "detail_type": "yunhu_button_click",
  "user_id": "User ID who clicked the button",
  "user_nickname": "User Nickname",
  "message_id": "Message ID",
  "yunhu_button": {
    "id": "Button ID (may be empty)",
    "value": "Button Value"
  }
}

# A2UI Button Click Event
{
  "type": "notice",
  "detail_type": "yunhu_a2ui_button",
  "user_id": "Operator User ID",
  "user_nickname": "User Nickname",
  "message_id": "Message ID",
  "yunhu_a2ui": {
    "recv_id": "Recipient ID",
    "recv_type": "Recipient Type",
    "action_name": "Action Name",
    "source_component_id": "Source Component ID",
    "form_context": {},
    "interaction_json": "JSON string of interaction data"
  }
}

### Button Click Event Handling Example

```python
from ErisPulse.Core.Event import notice

@notice.on_notice()
async def handle_yunhu_notice(event):
    """Handle Yunhu Notice Events

    Use the generic on_notice() decorator to handle all notification events,
    then distinguish different types of notifications via detail_type.
    event.reply() will automatically reply through the Yunhu platform.
    """

# Check if it is a button click event
    if event.get("detail_type") == "yunhu_button_click":
        user_id = event.get_user_id()
        user_nickname = event.get_user_nickname()
        button_value = event.get("yunhu_button", {}).get("value", "")

        print(f"User {user_nickname}({user_id}) clicked the button: {button_value}")

# Using event.reply() for Automatic Replies (会选择正确的发送方式以适应平台)
        if button_value == "confirm":
            await event.reply("You clicked the confirm button!")
        elif button_value == "cancel":
            await event.reply("Operation canceled")
        else:
            await event.reply(f"Received your selection: {button_value}")

# Handling Shortcut Menu Events
    elif event.get("detail_type") == "yunhu_shortcut_menu":
        menu_id = event.get("yunhu_menu", {}).get("id", "")
        await event.reply(f"Triggered shortcut menu: {menu_id}")

# Handling Robot Setting Changes
    elif event.get("detail_type") == "yunhu_bot_setting":
        settings = event.get("yunhu_setting", {})
        await event.reply(f"Settings have been updated: {settings}")

# Handling A2UI Button Events
    elif event.get("detail_type") == "yunhu_a2ui_button":
        a2ui = event.get("yunhu_a2ui", {})
        action_name = a2ui.get("action_name", "")
        form_context = a2ui.get("form_context", {})
        await event.reply(f"A2UI Action: {action_name}, Form Data: {form_context}")
```

### Sending a Message with Buttons Using a Chained Call

```python
from ErisPulse import sdk

yunhu = sdk.adapter.get("yunhu")

buttons = [
    [
        {"text": "Confirm", "actionType": 3, "value": "confirm"},
        {"text": "Cancel", "actionType": 3, "value": "cancel"},
        {"text": "View Details", "actionType": 1, "url": "http://example.com/detail"}
    ]
]

# Send a Message with Buttons to a Group  
await yunhu.Send.To("group", "123456").Buttons(buttons).Text("Please confirm the following action")

# Send a Message with Buttons to User's Private Chat
await yunhu.Send.To("user", "789").Buttons(buttons).Text("Please select your preferred settings")

### Send A2UI Message

```python
from ErisPulse import sdk

yunhu = sdk.adapter.get("yunhu")
```

# Send A2UI Message
await yunhu.Send.To("user", user_id).A2UI("A2UI interaction card content")

```
# Bot Settings
{
  "type": "notice",
  "detail_type": "yunhu_bot_setting",
  "group_id": "Group ID (may be empty)",
  "user_nickname": "User nickname",
  "yunhu_setting": {
    "Setting Item ID": {
      "id": "Setting Item ID",
      "type": "input/radio/checkbox/select/switch",
      "value": "Setting value"
    }
  }
}

# Quick Menu
{
  "type": "notice",
  "detail_type": "yunhu_shortcut_menu",
  "user_id": "User ID who triggered the menu",
  "user_nickname": "User nickname",
  "group_id": "Group ID (if it's a group chat)",
  "yunhu_menu": {
    "id": "Menu ID",
    "type": "Menu type (integer)",
    "action": "Menu action (integer)"
  }
}
```

## Event Mixin Extension Methods

The adapter registers the following platform-specific methods, available only when `platform == "yunhu"`:

| Method | Return Type | Description |
|--------|-------------|-------------|
| `get_raw_event()` | `dict` | Get raw Yunhu event data (`yunhu_raw`) |
| `get_sender_level()` | `str` | Sender's native Yunhu level (owner/administrator/member/unknown) |
| `get_sender_role()` | `str` | Sender's OneBot12 standard role (owner/admin/member) |
| `get_sender_title()` | `str` | Sender's title (standard `title` field accessor, reserved) |
| `get_sender_avatar()` | `str` | Sender's avatar URL |
| `get_command()` | `dict` | Command data (only for command message events, `yunhu_command`) |
| `get_button_value()` | `str` | The `value` of a button click event (`yunhu_button.value`) |
| `get_a2ui_action()` | `str` | The `actionName` of an A2UI button event |
| `get_a2ui_form_context()` | `dict` | The form context of an A2UI button event |
| `get_menu_id()` | `str` | Shortcut menu event ID (`yunhu_menu.id`) |
| `get_setting()` | `dict` | Setting data of a bot setting event (`yunhu_setting`) |
| `is_command_message()` | `bool` | Whether the event is a command message |
| `is_button_click()` | `bool` | Whether the event is a button click |
| `is_a2ui_button()` | `bool` | Whether the event is an A2UI button event |

```python
from ErisPulse.Core.Event import notice

@notice.on_notice()
async def handle_yunhu_notice(event):
    if event.get("platform") != "yunhu":
        return

    if event.is_button_click():
        value = event.get_button_value()
        await event.reply(f"You clicked the button: {value}")

    if event.get("detail_type") == "yunhu_shortcut_menu":
        menu_id = event.get_menu_id()
```

## Extension Field Description

- All custom fields are prefixed with `yunhu_` to avoid conflicts with standard fields.
- Raw data is preserved in the `yunhu_raw` field for easy access to the complete original data from the Yunhu platform.
- `self.user_id` represents the bot ID (obtained from the bot_id in the configuration).
- Form commands are provided as structured data through the `yunhu_command` field.
- Button click events are provided with button-related information through the `yunhu_button` field.
- A2UI button events are provided with A2UI interaction-related information through the `yunhu_a2ui` field.
- Bot setting changes are provided with setting item data through the `yunhu_setting` field.
- Quick menu operations are provided with menu-related information through the `yunhu_menu` field.
- Emoji/Sticker messages are provided as a message segment through `yunhu_expression`, containing sticker data (sticker_id, sticker pack ID, image dimensions, etc.).

### Emoji/Sticker Message Segment (yunhu_expression)

When a user sends an emoji or sticker, the message segment type is `yunhu_expression`:

```json
{
  "type": "yunhu_expression",
  "data": {
    "sticker_id": "35154",
    "sticker_pack_id": "1670",
    "expression_id": "0",
    "image_name": "sticker/fabb9077f2ba302402ea871cab3686ad7a3fc52c.gif",
    "width": 500,
    "height": 500
  }
}
```

| Field | Type | Description |
|-------|------|-------------|
| `sticker_id` | string | Sticker unique identifier |
| `sticker_pack_id` | string | Sticker pack ID |
| `expression_id` | string | Expression ID |
| `image_name` | string | Path to the expression image file |
| `width` | int | Image width (optional) |
| `height` | int | Image height (optional) |

Example usage:
```python
from ErisPulse.Core.Event import message

@message.on_message()
async def handle_message(event):
    if event.get_platform() == "yunhu":
        for segment in event.get("message", []):
            if segment.get("type") == "yunhu_expression":
                data = segment["data"]
                print(f"Received sticker: sticker_id={data['sticker_id']}, pack ID={data['sticker_pack_id']}")
```

## Multi-Bot Configuration

### Configuration Explanation

The Yunhu Adapter supports configuring and running multiple Yunhu bot accounts simultaneously.

```toml
# config.toml
[Yunhu_Adapter.accounts.bot1]
token = "your_bot1_token"  # Bot token (required)
mode = "ws"  # Receive mode (optional, default: "ws", options: "ws", "webhook")
webhook_path = "/webhook/bot1"  # Webhook path (optional, default: "/webhook")
enabled = true  # Whether to enable (optional, default: true)

[Yunhu_Adapter.accounts.bot2]
token = "your_bot2_token"  # Second bot's token
webhook_path = "/webhook/bot2"  # Independent webhook path
enabled = true
```

**Configuration Item Explanation:**
- `token`: API token provided by the Yunhu platform (required)
- `mode`: Receive mode (optional, default: `"ws"`, options: `"ws"`, `"webhook"`)
- `webhook_path`: HTTP path for receiving Yunhu events (optional, default: `"/webhook"`, only used in webhook mode)
- `enabled`: Whether to enable this account (optional, default: true)

**Important Notes:**
1. The Yunhu platform's bot ID is **automatically detected at runtime**, no need to specify it in the configuration
2. In webhook mode, each bot should have its own `webhook_path` to receive its own webhook events
3. When configuring webhooks in the Yunhu platform, please set up corresponding URLs for each bot, for example:
   - Bot1: `https://your-domain.com/webhook/bot1`
   - Bot2: `https://your-domain.com/webhook/bot2`

### Using Send DSL to Specify Bot

You can specify which bot to use for sending messages via the `Using()` method. This method supports two types of parameters:
- **Account name**: The bot name in the configuration (e.g., `bot1`, `bot2`)
- **bot_id**: The `bot_id` value in the configuration

```python
from ErisPulse.Core import adapter
yunhu = adapter.get("yunhu")

# Send message using account name
await yunhu.Send.Using("bot1").To("user", "user123").Text("Hello from bot1!")

# Send message using bot_id (automatically matches the corresponding account)
await yunhu.Send.Using("30535459").To("group", "group456").Text("Hello from bot!")

# Use the first enabled bot if not specified
await yunhu.Send.To("user", "user123").Text("Hello from default bot!")
```

> **Note:** When using `bot_id`, the system automatically finds the matching account in the configuration. This is especially useful when handling event replies, where you can directly use `event["self"]["user_id"]` to reply from the same account.

### Bot Identification in Events

Received events will automatically include the corresponding `bot_id` information:

```python
from ErisPulse.Core.Event import message

@message.on_message()
async def handle_message(event):
    if event["platform"] == "yunhu":
        # Get the bot ID that triggered the event
        bot_id = event["self"]["user_id"]
        print(f"Message from Bot: {bot_id}")
        
        # Reply using the same bot
        yunhu = adapter.get("yunhu")
        await yunhu.Send.Using(bot_id).To(
            event["detail_type"],
            event["user_id"] if event["detail_type"] == "private" else event["group_id"]
        ).Text("Reply message")
```

### Log Information

The adapter will automatically include `bot_id` information in logs, making debugging and tracking easier:

```
[INFO] [yunhu] [bot:30535459] Received private message from user user123
[INFO] [yunhu] [bot:12345678] Message sent successfully, message_id: abc123
```

### Management Interface

```python
# Get all account information
bots = yunhu.bots

# Check if an account is enabled
bot_status = {
    bot_name: bot_config.enabled
    for bot_name, bot_config in yunhu.bots.items()
}

# Dynamically enable/disable accounts (requires restarting the adapter)
yunhu.bots["bot1"].enabled = False
```

### Legacy Configuration Compatibility

Legacy `[Yunhu_Adapter.bots.*]` configuration (including the `bot_id` field) will be automatically migrated to the `accounts` format (`bot_id` is now automatically detected at runtime, and values in the configuration will be ignored); it is recommended to migrate to the new format as soon as possible.



### 邮件适配

# Email Platform Feature Documentation

EmailAdapter is a mail adapter based on the SMTP/IMAP protocols, supporting sending, receiving, and processing of emails.

---

## Document Information

- Corresponding Module Version: 4.1.0
- Maintainer: ErisPulse

## Basic Information

- Platform Overview: A general-purpose adapter for sending and receiving emails using standard SMTP/IMAP protocols
- Adapter Name: EmailAdapter
- Multi-account Support: Supports configuring multiple email accounts simultaneously
- Connection Method: IMAP long-polling for receiving + SMTP for sending
- Authentication Method: Email address + password/authorization code
- OneBot12 Compatibility: Supports sending OneBot12 format messages

## Configuration Guide

### Global Configuration (EmailAdapter)

| Configuration Item | Type | Default Value | Description |
|--------------------|------|---------------|-------------|
| `imap_server` | str | `imap.example.com` | Default IMAP server address |
| `imap_port` | int | `993` | Default IMAP port |
| `smtp_server` | str | `smtp.example.com` | Default SMTP server address |
| `smtp_port` | int | `465` | Default SMTP port |
| `ssl` | bool | `true` | Whether to enable SSL by default |
| `timeout` | int | `30` | Default connection timeout (seconds) |
| `poll_interval` | int | `60` | IMAP polling interval (seconds) |
| `max_retries` | int | `3` | Maximum number of retries on connection failure |

### Account Configuration (EmailAdapter.accounts)

Each account corresponds to a separate email. Account-level configurations take precedence over global configurations.

```toml
[EmailAdapter.accounts.default]
email = "user@example.com"
password = "your-password-or-auth-code"
imap_server = "imap.example.com"    # Optional, leave empty to use global default
imap_port = 993                      # Optional
smtp_server = "smtp.example.com"    # Optional
smtp_port = 465                      # Optional
ssl = true                           # Optional
timeout = 30                         # Optional
enabled = true

[EmailAdapter.accounts.backup]
email = "backup@example.com"
password = "another-password"
enabled = true
```

## Supported Message Sending Types

All sending methods are implemented using a fluent interface:

```python
from ErisPulse.Core import adapter
mail = adapter.get("email")

# Simple plain text email
await mail.Send.To("private", "to@example.com").Subject("Test").Text("Content")

# HTML email with attachments
await mail.Send.To("private", "to@example.com") \
    .Subject("HTML Email") \
    .Cc(["cc1@example.com", "cc2@example.com"]) \
    .Attachment("report.pdf") \
    .Html("<h1>HTML Content</h1>")

# Using Raw_ob12 to send standard OB12 messages
await mail.Send.To("private", "to@example.com").Raw_ob12([
    {"type": "text", "data": {"text": "Email body"}},
    {"type": "file", "data": {"file": "/path/to/attachment.pdf"}},
])

# Specify sending account (multi-account)
await mail.Send.Using("default").To("private", "to@example.com").Text("Content")
```

> Note: When using the fluent interface, parameter methods (Subject / Cc / Attachment, etc.) must be called before the sending method (Text / Html / Raw_ob12).

### Basic Sending Methods

| Method | Description |
|--------|-------------|
| `.Text(text: str)` | Send plain text email |
| `.Html(html: str)` | Send HTML formatted email |
| `.Raw_ob12(message, **kwargs)` | Send OneBot12 formatted message |

### Fluent Modifier Methods (return self, can be combined)

| Method | Description |
|--------|-------------|
| `.Subject(subject: str)` | Set email subject |
| `.Cc(emails: Union[str, List[str]])` | Set CC recipients |
| `.Bcc(emails: Union[str, List[str]])` | Set BCC recipients |
| `.ReplyTo(email: str)` | Set reply-to address |
| `.Attachment(file, filename: str = None)` | Add attachment |

### OB12 Message Segment Reverse Conversion (Raw_ob12)

| OB12 Message Segment | Converted to Email Content |
|----------------------|----------------------------|
| `text` | Plain text body |
| `image` | Image attachment |
| `video` | Video attachment |
| `file` | File attachment |
| `audio` | Audio attachment |
| `markdown` | Converted to HTML body |

## Unique Event Types

### Core Differences

1. All email events are of `message` type, with `detail_type` fixed as `private`
2. `user_id` is the sender's **raw email address**, `user_nickname` is the sender's display name
3. `message` message segments are standard OB12 format (text segment + file segment)
4. Email subject is obtained via the `email_subject` extension field
5. Complete raw data is preserved in the `email_raw` field

### New Email Event (email_new)

```json
{
  "id": "<message-id@example.com>",
  "time": 1751990446,
  "type": "message",
  "detail_type": "private",
  "platform": "email",
  "self": {
    "platform": "email",
    "user_id": "bot@example.com"
  },
  "message": [
    {
      "type": "text",
      "data": {
        "text": "Email body content"
      }
    }
  ],
  "alt_message": "Email subject",
  "user_id": "sender@example.com",
  "user_nickname": "Saber"
}
```

### Email with Attachments

```json
{
  "message": [
    {
      "type": "text",
      "data": {
        "text": "Please check the attachment"
      }
    },
    {
      "type": "file",
      "data": {
        "file_id": "document.pdf",
        "file_name": "document.pdf",
        "size": 102400
      }
    }
  ]
}
```

### Reply Email Event (email_reply)

When the email contains `References` or `In-Reply-To` headers, `email_raw_type` is `email_reply`:

```json
{
  "email_raw_type": "email_reply",
  "email_raw": {
    "references": "<original-msg-id@example.com>",
    "in_reply_to": "<original-msg-id@example.com>"
  }
}
```

## Extension Field Descriptions

| Field | Type | Description |
|-------|------|-------------|
| `email_raw` | dict | Complete raw email data (subject/from/to/date/cc/bcc/text_content/html_content/attachments, etc.) |
| `email_raw_type` | str | Raw event type: `email_new` (new email) or `email_reply` (reply email) |
| `email_subject` | str | Email subject (convenient access) |
| `email_from` | str | Sender's raw email address (convenient access) |
| `attachments` | list | List of attachment data (includes binary `data` field, backward compatible) |

## Standard Event Examples

### Complete Email Event

```json
{
  "id": "<abc123@example.com>",
  "time": 1751990446,
  "type": "message",
  "detail_type": "private",
  "platform": "email",
  "self": {
    "platform": "email",
    "user_id": "bot@example.com"
  },
  "message": [
    {
      "type": "text",
      "data": {
        "text": "Please check the attachment"
      }
    },
    {
      "type": "file",
      "data": {
        "file_id": "document.pdf",
        "file_name": "document.pdf",
        "size": 102400
      }
    }
  ],
  "alt_message": "Meeting Notice",
  "user_id": "sender@example.com",
  "user_nickname": "Sender",
  "email_subject": "Meeting Notice",
  "email_from": "sender@example.com",
  "email_raw": {
    "subject": "Meeting Notice",
    "from": "\"Sender\" <sender@example.com>",
    "to": "<bot@example.com>",
    "date": "Wed, 9 Jul 2026 02:00:46 +0800",
    "message_id": "<abc123@example.com>",
    "references": "",
    "in_reply_to": "",
    "cc": "",
    "bcc": "",
    "text_content": "Please check the attachment",
    "html_content": "<p>Please check the attachment</p>",
    "attachments": ["document.pdf"]
  },
  "email_raw_type": "email_new",
  "attachments": [
    {
      "filename": "document.pdf",
      "content_type": "application/pdf",
      "size": 102400,
      "data": "..."
    }
  ]
}
```

## Sending Method Return Values

```json
{
  "status": "ok",
  "retcode": 0,
  "data": {
    "message_id": "<sent-msg-id@example.com>",
    "time": 1751990446
  },
  "message_id": "<sent-msg-id@example.com>",
  "message": "",
  "email_raw": {
    "success": true,
    "message": "Email sent successfully"
  }
}
```

## Event Handling Example

```python
from ErisPulse.Core.Event import message

@message.on_message()
async def handle_email(event):
    if event.get("platform") != "email":
        return
    # Raw sender email address
    sender = event["user_id"]              # sender@example.com
    
    # Sender's display name
    nickname = event.get("user_nickname")  # Sender
    
    # Email subject
    subject = event.get("email_subject")   # Meeting Notice
    
    # Plain text body (first text segment)
    text = event.get_text()
    
    # Complete raw data
    raw = event.get("email_raw", {})
    html = raw.get("html_content", "")
    
    # Process attachments
    for seg in event.get("message", []):
        if seg["type"] == "file":
            filename = seg["data"]["file_name"]
            size = seg["data"]["size"]
    
    # Reply to email
    await event.reply(f"Received: {subject}")
```



### Kook 适配

# Kook Platform Feature Documentation

KookAdapter is an adapter built on the Kook (Kaihei La) Bot WebSocket protocol, integrating all Kook functional modules and providing unified event handling and message operation interfaces.

---

## Document Information

- Corresponding Module Version: 0.1.0
- Maintainer: ShanFish

## Basic Information

- Platform Introduction: Kook (formerly KaiHeiLa) is a community platform that supports text, voice, and video communication, and provides a complete Bot development interface.
- Adapter Name: KookAdapter
- Multi-account Support: Supports configuring multiple Kook Bots simultaneously.
- Connection Method: WebSocket long connection (via Kook Gateway).
- Authentication Method: Identity authentication based on Bot Token.
- Chainable Modifier Support: Supports chainable modifier methods such as `.Reply()`, `.At()`, and `.AtAll()`.
- OneBot12 Compatibility: Supports sending OneBot12 formatted messages.

## Configuration

KookAdapter supports multiple account configurations, with each account corresponding to an independent Kook bot.

```toml
# config.toml
# Account 1
[KookAdapter.accounts.default]
token = "YOUR_BOT_TOKEN"     # Kook Bot Token (required, format: Bot xxx/xxx)
bot_id = ""                   # Bot user ID (optional, if not filled, it will be parsed from token)
compress = true               # Whether to enable WebSocket compression (optional, default is true)
enabled = true                # Whether to enable the account (optional, default is true)

# Account 2
[KookAdapter.accounts.bot2]
token = "ANOTHER_BOT_TOKEN"
bot_id = ""
enabled = true
```

> Compatibility with old configuration: If the old single-account `[KookAdapter]` configuration (including token) is detected, it will be automatically migrated to `accounts.default`.

**Configuration Item Description (per account):**
- `token`: Kook Bot's token (required), obtainable from the [Kook Developer Center](https://developer.kookapp.cn), format: `Bot xxx/xxx`
- `bot_id`: Bot's user ID (optional), if not filled, the adapter will attempt to parse it from the token. It is recommended to manually fill it to ensure accuracy.
- `compress`: Whether to enable WebSocket data compression (optional, default is `true`), enabling it will use zlib to decompress data.
- `enabled`: Whether to enable this account (optional, default is `true`)

**API Environment:**
- Kook API base address: `https://www.kookapp.cn/api/v3`
- WebSocket gateway is dynamically obtained via API: `POST /gateway/index`

## Supported Message Sending Types

All sending methods are implemented using a fluent (chainable) syntax, for example:
```python
from ErisPulse.Core import adapter
kook = adapter.get("kook")

await kook.Send.To("group", channel_id).Text("Hello World!")
```

The supported sending types include:
- `.Text(text: str)`: Send a plain text message.
- `.Image(file: bytes | str)`: Send an image message, supporting file paths, URLs, and binary data.
- `.Video(file: bytes | str)`: Send a video message, supporting file paths, URLs, and binary data.
- `.File(file: bytes | str, filename: str = None)`: Send a file message, supporting file paths, URLs, and binary data.
- `.Voice(file: bytes | str)`: Send a voice message, supporting file paths, URLs, and binary data.
- `.Markdown(text: str)`: Send a KMarkdown-formatted message.
- `.Card(card_data: dict)`: Send a card message (CardMessage).
- `.Raw_ob12(message: List[Dict], **kwargs)`: Send a OneBot12-formatted message.

### Fluent Modifier Methods (can be combined)

Fluent modifier methods return `self`, enabling chainable calls, and must be called before the final sending method:

- `.Reply(message_id: str)`: Reply (quote) a specified message.
- `.At(user_id: str)`: Mention a specified user, can be called multiple times to mention multiple users.
- `.AtAll()`: Mention everyone.

### Fluent Call Examples

```python
# Basic sending
await kook.Send.To("group", channel_id).Text("Hello")

# Reply to a message
await kook.Send.To("group", channel_id).Reply(msg_id).Text("Reply message")

# Mention a user
await kook.Send.To("group", channel_id).At("user_id").Text("你好")

# Mention multiple users
await kook.Send.To("group", channel_id).At("user1").At("user2").Text("Multiple users @")

# Mention everyone
await kook.Send.To("group", channel_id).AtAll().Text("Announcement")

# Combine modifiers
await kook.Send.To("group", channel_id).Reply(msg_id).At("user_id").Text("Complex message")
```

### OneBot12 Message Support

The adapter supports sending OneBot12-formatted messages, facilitating cross-platform message compatibility:

```python
# Send a OneBot12-formatted message
ob12_msg = [{"type": "text", "data": {"text": "Hello"}}]
await kook.Send.To("group", channel_id).Raw_ob12(ob12_msg)

# Combine with fluent modifiers
ob12_msg = [{"type": "text", "data": {"text": "Reply message"}}]
await kook.Send.To("group", channel_id).Reply(msg_id).Raw_ob12(ob12_msg)

# Use mention and reply segments within Raw_ob12
ob12_msg = [
    {"type": "text", "data": {"text": "Hello "}},
    {"type": "mention", "data": {"user_id": "user_id"}},
    {"type": "reply", "data": {"message_id": "msg_id"}}
]
await kook.Send.To("group", channel_id).Raw_ob12(ob12_msg)
```

### Additional Operation Methods

In addition to sending messages, the Kook adapter supports the following operations:

```python
# Edit a message (only supports KMarkdown type=9 and CardMessage type=10)
await kook.Send.To("group", channel_id).Edit(msg_id, "**Updated content**")

# Recall a message
await kook.Send.To("group", channel_id).Recall(msg_id)

# Upload a file (get file URL)
result = await kook.Send.Upload("C:/path/to/file.jpg")
file_url = result["data"]["url"]
```

## Return Values of Send Methods

All send methods return a Task object, which can be directly awaited to obtain the send result. The returned result follows the ErisPulse adapter's standardized return specification:

```python
{
    "status": "ok",           // Execution status: "ok" or "failed"
    "retcode": 0,             // Return code (Kook API's code)
    "data": {...},            // Response data
    "message_id": "xxx",      // Message ID
    "message": "",            // Error message
    "kook_raw": {...}         // Original response data
}
```

### Error Code Descriptions

| retcode | Description |
|---------|-------------|
| 0 | Success |
| 40100 | Invalid or missing Token |
| 40101 | Token expired |
| 40102 | Token does not match Bot |
| 40103 | Missing permissions |
| 40000 | Parameter error |
| 40400 | Target does not exist |
| 40300 | No permission to perform operation |
| 50000 | Internal server error |
| -1 | Internal adapter error |

## Platform-Specific Event Types

Platform-specific features require `platform=="kook"` detection.

### Core Differences

1. **Channel System**: Kook uses a two-layer structure of servers (Guild) and channels (Channel), with channels being the basic targets for message sending.
2. **Message Types**: Kook supports various message types, including text (1), image (2), video (3), file (4), voice (8), KMarkdown (9), and card messages (10).
3. **Private Messaging System**: Kook distinguishes between channel messages and private messages, using different API endpoints.
4. **Message Sequence Numbers**: Kook's WebSocket uses `sn` sequence numbers to ensure message ordering, supporting message buffering and out-of-order reordering.
5. **Message Editing and Deletion**: Editing and deleting previously sent messages are supported (only for KMarkdown and CardMessage).

### Extended Fields

- All platform-specific fields are prefixed with `kook_`.
- Original data is preserved in the `kook_raw` field.
- `kook_raw_type` indicates the original Kook message type number (e.g., `1` for text, `255` for notification events).

### Special Field Examples

```python
# Channel text message
{
  "type": "message",
  "detail_type": "group",
  "user_id": "User ID",
  "group_id": "Channel ID",
  "channel_id": "Channel ID",
  "message_id": "Message ID",
  "kook_raw": {...},
  "kook_raw_type": "1",
  "message": [
    {"type": "text", "data": {"text": "Hello"}}
  ],
  "alt_message": "Hello"
}

# Message with image
{
  "type": "message",
  "detail_type": "group",
  "user_id": "User ID",
  "group_id": "Channel ID",
  "channel_id": "Channel ID",
  "message_id": "Message ID",
  "kook_raw": {...},
  "kook_raw_type": "2",
  "message": [
    {"type": "image", "data": {"file": "Image URL", "url": "Image URL"}}
  ],
  "alt_message": "Image content"
}

# KMarkdown message
{
  "type": "message",
  "detail_type": "group",
  "user_id": "User ID",
  "group_id": "Channel ID",
  "message_id": "Message ID",
  "kook_raw": {...},
  "kook_raw_type": "9",
  "message": [
    {"type": "text", "data": {"text": "Parsed plain text"}}
  ]
}

# Card message
{
  "type": "message",
  "detail_type": "group",
  "user_id": "User ID",
  "group_id": "Channel ID",
  "message_id": "Message ID",
  "kook_raw": {...},
  "kook_raw_type": "10",
  "message": [
    {"type": "json", "data": {"data": "Card JSON content"}}
  ]
}

# Private chat message
{
  "type": "message",
  "detail_type": "private",
  "user_id": "User ID",
  "message_id": "Message ID",
  "kook_raw": {...},
  "kook_raw_type": "1",
  "message": [
    {"type": "text", "data": {"text": "Private chat content"}}
  ]
}
```

### Message Segment Types

Kook's message types are automatically converted to corresponding message segments based on the `type` field:

| Kook type | Converted Type | Description |
|---|---|---|
| 1 | `text` | Text message |
| 2 | `image` | Image message |
| 3 | `video` | Video message |
| 4 | `file` | File message |
| 8 | `record` | Voice message |
| 9 | `text` | KMarkdown message (extracts plain text content) |
| 10 | `json` | Card message (original JSON) |

Example message segment structure:
```json
{
  "type": "image",
  "data": {
    "file": "Image URL",
    "url": "Image URL"
  }
}
```

### Mention Message Segment

When a message contains a mention (`@`), a `mention` message segment is inserted before the message segment:

```json
{
  "type": "mention",
  "data": {
    "user_id": "Mentioned user ID"
  }
}
```

### mention_all Message Segment

When a message is a mention to all (`@全体`), a `mention_all` message segment is inserted:

```json
{
  "type": "mention_all",
  "data": {}
}
```

## WebSocket Connection

### Connection Flow

1. Use Bot Token to call `POST /gateway/index` to obtain the WebSocket gateway address.
2. Connect to the WebSocket gateway.
3. Receive HELLO (s=1) message to verify connection status.
4. Begin heartbeat loop (PING, s=2, every 30 seconds).
5. Receive message events (s=0), using sn sequence number to ensure order.
6. Receive heartbeat response PONG (s=3).

### Message Types

| Message | s Value | Description |
|---------|---------|-------------|
| HELLO | 1 | Server welcome message, received after successful connection. |
| PING | 2 | Client heartbeat, sent every 30 seconds, carries current sn. |
| PONG | 3 | Heartbeat response. |
| RESUME | 4 | Resume connection message, carries sn to resume session. |
| RECONNECT | 5 | Server requests reconnection, requires re-obtaining gateway. |
| RESUME_ACK | 6 | RESUME success response. |

### Reconnection on Disconnection

- After abnormal disconnection, the adapter automatically retries connection.
- If there was a previous `sn > 0`, it first attempts RESUME (s=4) to restore connection.
- If RESUME fails, reset sn and message queue, and perform a new connection (HELLO flow).
- When RECONNECT (s=5) message is received, clear the status and reconnect.

### Message Sequence Number Mechanism

Kook WebSocket uses `sn` (incrementing sequence number) to ensure message order:

- For each received message event (s=0), sn is incremented.
- If a received message has a non-continuous sn, enter temporary storage mode.
- Messages in the temporary storage area are sorted by sn, waiting for missing messages to arrive before processing in order.
- After the temporary storage area is cleared, automatically exit temporary storage mode.

## Usage Examples

### Handling Channel Messages

```python
from ErisPulse.Core.Event import message
from ErisPulse import sdk

kook = sdk.adapter.get("kook")

@message.on_message()
async def handle_group_msg(event):
    if event.get("platform") != "kook":
        return
    if event.get("detail_type") != "group":
        return

    text = event.get_text()
    channel_id = event.get("group_id")

    if text == "hello":
        await kook.Send.To("group", channel_id).Text("Hello!")
```

### Handling Private Messages

```python
@message.on_message()
async def handle_private_msg(event):
    if event.get("platform") != "kook":
        return
    if event.get("detail_type") != "private":
        return

    text = event.get_text()
    user_id = event.get("user_id")

    await kook.Send.To("user", user_id).Text(f"You said: {text}")
```

### Handling Notification Events (Emoji Reactions, etc.)

```python
from ErisPulse.Core.Event import notice

@notice.on_notice()
async def handle_notice(event):
    if event.get("platform") != "kook":
        return

    sub_type = event.get("sub_type")

    if sub_type == "added_reaction":
        emoji = event.get("emoji", {})
        user_id = event.get("user_id")
        msg_id = event.get("message_id")
        print(f"User {user_id} added an emoji reaction to message {msg_id}")

    elif sub_type == "deleted_reaction":
        emoji = event.get("emoji", {})
        user_id = event.get("user_id")
        msg_id = event.get("message_id")
        print(f"User {user_id} removed an emoji reaction from message {msg_id}")
```

### Sending Media Messages

```python
# Sending an image (URL)
await kook.Send.To("group", channel_id).Image("https://example.com/image.png")

# Sending an image (binary)
with open("image.png", "rb") as f:
    image_bytes = f.read()
await kook.Send.To("group", channel_id).Image(image_bytes)

# Sending a video
await kook.Send.To("group", channel_id).Video("https://example.com/video.mp4")

# Sending a file
await kook.Send.To("group", channel_id).File("https://example.com/file.pdf", filename="document.pdf")

# Sending a voice message
await kook.Send.To("group", channel_id).Voice("https://example.com/voice.mp3")
```

### Sending KMarkdown and Card Messages

```python
# KMarkdown
await kook.Send.To("group", channel_id).Markdown("**Bold** *Italic* [Link](https://example.com)")

# Card message
card = {
    "type": "card",
    "theme": "primary",
    "size": "lg",
    "modules": [
        {"type": "header", "text": {"type": "plain-text", "content": "Title"}},
        {"type": "section", "text": {"type": "kmarkdown", "content": "Content"}}
    ]
}
await kook.Send.To("group", channel_id).Card(card)
```

### Editing and Deleting Messages

```python
# Sending a message
result = await kook.Send.To("group", channel_id).Markdown("**Original content**")
msg_id = result["data"]["msg_id"]

# Editing a message (supports only KMarkdown and CardMessage)
await kook.Send.To("group", channel_id).Edit(msg_id, "**Updated content**")

# Deleting a message
await kook.Send.To("group", channel_id).Recall(msg_id)
```

### Handling Edit and Delete Notifications for Private Messages

```python
@notice.on_notice()
async def handle_private_notice(event):
    if event.get("platform") != "kook":
        return

    sub_type = event.get("sub_type")

    if sub_type == "updated_private_message":
        msg_id = event.get("message_id")
        content = event.get("content")
        print(f"Private message updated: {msg_id}, new content: {content}")

    elif sub_type == "deleted_private_message":
        msg_id = event.get("message_id")
        print(f"Private message deleted: {msg_id}")
```



### Matrix 适配

# Matrix Platform Feature Documentation

MatrixAdapter is an adapter built based on the [Matrix protocol](https://spec.matrix.org/), integrating all core functional modules of the Matrix protocol and providing a unified interface for event handling and message operations.

---

## Document Information

- Corresponding Module Version: 4.1.0
- Maintainer: ErisPulse

## Basic Information

- Platform Overview: Matrix is an open, decentralized communication protocol that supports various scenarios such as private chats and group chats.
- Adapter Name: MatrixAdapter
- Multi-account Support: Supports configuring multiple Matrix accounts simultaneously.
- Connection Method: Long Polling (via Matrix Sync API `/sync`)
- Authentication Method: Login using access_token or user_id + password to obtain a token.
- Chained Modifier Support: Supports chained modifier methods such as `.Reply()`, `.At()`, and `.AtAll()`.
- OneBot12 Compatibility: Supports sending messages in OneBot12 format.

## Configuration Instructions

MatrixAdapter supports multi-account configuration, with each account having its own homeserver and authentication information.

```toml
# config.toml
# Account 1
[Matrix_Adapter.accounts.default]
homeserver = "https://matrix.org"          # Matrix server address (required)
access_token = "YOUR_ACCESS_TOKEN"          # Access token (either this or user_id+password is required)
user_id = ""                                # Matrix user ID (e.g. @bot:matrix.org)
password = ""                               # Matrix user password
auto_accept_invites = true                  # Whether to automatically accept room invites (optional, default is true)
enabled = true                              # Whether to enable this account (optional, default is true)

# Account 2
[Matrix_Adapter.accounts.bot2]
homeserver = "https://matrix.example.com"
access_token = "ANOTHER_TOKEN"
enabled = true
```

> **Backward Compatibility:** If an old single-account `[Matrix_Adapter]` configuration (including access_token) is detected, it will be automatically migrated to `accounts.default`.

**Configuration Item Descriptions (per account):**
- `homeserver`: Matrix server address (required), default is `https://matrix.org`
- `access_token`: Access token, can be obtained from a Matrix client. If you already have a token, simply fill it in
- `user_id`: Matrix user ID (e.g., `@bot:matrix.org`), used together with `password` for login
- `password`: Matrix user password, used for automatic login to obtain the access token
- `auto_accept_invites`: Whether to automatically accept room invites, default is `true`
- `enabled`: Whether to enable this account (optional, default is true)

**Authentication Methods:**
- Method 1 (Recommended): Provide `access_token` directly
- Method 2: Provide `user_id` and `password`, the adapter will automatically call the login API to obtain the token

## Supported Message Sending Types

All sending methods are implemented using a fluent interface, for example:
```python
from ErisPulse.Core import adapter
matrix = adapter.get("matrix")

await matrix.Send.To("group", room_id).Text("Hello World!")
```

The supported sending types include:
- `.Text(text: str)` : Sends a plain text message.
- `.Image(file: bytes | str)` : Sends an image message, supporting file paths, URLs, MXC URIs, and binary data.
- `.Voice(file: bytes | str)` : Sends a voice message, supporting file paths, URLs, MXC URIs, and binary data.
- `.Video(file: bytes | str)` : Sends a video message, supporting file paths, URLs, MXC URIs, and binary data.
- `.File(file: bytes | str, filename: str = "")` : Sends a file message, supporting file paths, URLs, MXC URIs, and binary data.
- `.Notice(text: str)` : Sends a notice message (Matrix's m.notice type).
- `.Html(html: str, fallback: str = "")` : Sends an HTML-formatted message, supporting rich text content.
- `.Raw_ob12(message: List[Dict], **kwargs)` : Sends a OneBot12 formatted message.

### Fluent Modifier Methods (Combinable)

Modifier methods return `self`, supporting fluent chaining, and must be called before the final sending method:

- `.Reply(message_id: str)` : Replies to a specified message (using Matrix `m.in_reply_to` relationship).
- `.At(user_id: str)` : Mentions a specified user (using Matrix `m.mentions` field).
- `.AtAll()` : Mentions everyone in the room (using Matrix `@room` mention).

### Fluent Chaining Examples

```python
# Basic sending
await matrix.Send.To("user", dm_room_id).Text("Hello")

# Reply to message
await matrix.Send.To("group", room_id).Reply("$event_id").Text("Reply message")

# Mention user
await matrix.Send.To("group", room_id).At("@user:matrix.org").Text("你好")

# Mention everyone
await matrix.Send.To("group", room_id).AtAll().Text("Announcement")

# Combinable: Reply + Mention
await matrix.Send.To("group", room_id).Reply("$event_id").At("@user:matrix.org").Text("Combined message")

# Send HTML message
await matrix.Send.To("group", room_id).Html("<h1>Title</h1><p>Content</p>", fallback="Title\nContent")

# Send notice message
await matrix.Send.To("group", room_id).Notice("System notification")
```

### OneBot12 Message Support

The adapter supports sending OneBot12 formatted messages, facilitating cross-platform message compatibility:

```python
# Send OneBot12 formatted message
ob12_msg = [{"type": "text", "data": {"text": "Hello"}}]
await matrix.Send.To("user", dm_room_id).Raw_ob12(ob12_msg)

# Combined with fluent modifiers
ob12_msg = [{"type": "text", "data": {"text": "Reply message"}}]
await matrix.Send.To("group", room_id).Reply("$event_id").Raw_ob12(ob12_msg)

# Complex message
ob12_msg = [
    {"type": "text", "data": {"text": "Look at this image: "}},
    {"type": "image", "data": {"file": "https://example.com/image.png"}},
    {"type": "text", "data": {"text": "Isn't it great? "}}
]
await matrix.Send.To("group", room_id).Raw_ob12(ob12_msg)
```

## Return values of send methods

All send methods return a Task object, which can be awaited directly to obtain the send result. The returned result follows the ErisPulse adapter's standardized return specification:

```python
{
    "status": "ok",           // Execution status: "ok" or "failed"
    "retcode": 0,             // Return code
    "data": {...},            // Response data
    "message_id": "$event_id", // Matrix event ID
    "message": "",            // Error message
    "matrix_raw": {...}       // Raw response data
}
```

### Error code description

| retcode | Description |
|---------|-------------|
| 0 | Success |
| 32000 | Request timeout or media upload failed |
| 33000 | API call exception |
| 34000 | API returned unexpected format or business error |

## Platform-Specific Event Types

Platform-specific features require `platform=="matrix"` detection.

### Core Differences

1. **Decentralized Architecture**: Matrix is a decentralized communication protocol, with user IDs formatted as `@user:server.domain` and room IDs as `!room_id:server.domain`.
2. **Room Concept**: Matrix does not distinguish between group chats and private chats; all conversations are "rooms". The adapter automatically identifies private chat rooms through DM (Direct Message) account data.
3. **Long Polling Synchronization**: Uses the `/sync` API for long-polling to fetch new events, rather than WebSocket.
4. **MXC URI**: Media files are referenced using the `mxc://server.domain/media_id` format.
5. **HTML Rich Text**: Supports sending HTML-formatted messages via `formatted_body`.
6. **Reaction Emojis**: Supports emoji reactions at the message level (Reaction), distinct from traditional reply messages.
7. **Message Editing**: Supports editing previously sent messages via the `m.replace` relationship.
8. **Message Deletion**: Supports deleting messages via `m.room.redaction`.

### Extended Fields

- All platform-specific fields are prefixed with `matrix_`.
- Original data is retained in the `matrix_raw` field.
- `matrix_raw_type` identifies the original Matrix event type (e.g., `m.room.message`, `m.room.member`).

### Special Field Examples

```python
# Group Message
{
  "type": "message",
  "detail_type": "group",
  "user_id": "@user:matrix.org",
  "group_id": "!room_id:matrix.org",
  "matrix_room_id": "!room_id:matrix.org"
}

# Private Message
{
  "type": "message",
  "detail_type": "private",
  "user_id": "@user:matrix.org",
  "matrix_room_id": "!dm_room_id:matrix.org"
}

# Reaction Emoji
{
  "type": "notice",
  "detail_type": "matrix_reaction",
  "matrix_reaction_event_id": "$reacted_msg_id",
  "matrix_reaction_key": "👍"
}

# Message Deletion
{
  "type": "notice",
  "detail_type": "matrix_redaction",
  "matrix_redacted_event_id": "$deleted_msg_id"
}

# Message Editing
{
  "type": "message",
  "detail_type": "group",
  "matrix_edit": True,
  "matrix_original_event_id": "$original_event_id"
}

# Thread Message
{
  "type": "message",
  "detail_type": "group",
  "thread_id": "$thread_root_id"
}
```

### Message Segment Types

Matrix messages are automatically converted into corresponding message segments based on `msgtype`:

| msgtype | Converted Type | Description |
|---|---|---|
| m.text | `text` | Text message |
| m.notice | `text` | Notice message |
| m.emote | `text` | Action message |
| m.image | `image` | Image message |
| m.audio | `voice` | Audio message |
| m.video | `video` | Video message |
| m.file | `file` | File message |
| m.location | `location` | Location message |

Example message segment structure:

```json
// Text Message (with HTML)
{
  "type": "text",
  "data": {
    "text": "Plain text content",
    "html": "<b>HTML content</b>"
  }
}

// Image Message
{
  "type": "image",
  "data": {
    "url": "mxc://matrix.org/abc123",
    "filename": "photo.png",
    "matrix_mxc": "mxc://matrix.org/abc123",
    "info": {
      "mimetype": "image/png",
      "w": 800,
      "h": 600,
      "size": 123456
    }
  }
}

// Location Message
{
  "type": "location",
  "data": {
    "latitude": 0.0,
    "longitude": 0.0,
    "matrix_geo_uri": "geo:39.9,116.4",
    "text": "Beijing, China"
  }
}
```

### Event Mixin Methods

The MatrixAdapter registers the following event mixin methods, which can be directly called in event handling:

| Method | Return Type | Description |
|------|----------|------|
| `get_room_id()` | `str` | Get the room ID |
| `get_matrix_event_type()` | `str` | Get the original Matrix event type |
| `get_matrix_sender()` | `str` | Get the original sender ID |
| `get_reaction_key()` | `str` | Get the reaction emoji |
| `is_edited()` | `bool` | Check if the message is edited |
| `is_notice()` | `bool` | Check if the message is of type m.notice |

```python
@message.on_message()
async def handle_message(event):
    if event.get("platform") != "matrix":
        return

    room_id = event.get_room_id()
    event_type = event.get_matrix_event_type()
    sender = event.get_matrix_sender()
    is_edited = event.is_edited()
    is_notice = event.is_notice()
```

## Sync API Connection

### Synchronization Flow

1. Authenticate using access_token or user_id + password
2. Call `/_matrix/client/v3/account/whoami` to get bot_user_id
3. Send a connect metadata event
4. Perform initial sync (`/_matrix/client/v3/sync?timeout=0`) to obtain the `next_batch` token
5. Discover DM rooms (`/_matrix/client/v3/user/{user_id}/account_data/m.direct`)
6. Begin Long Polling synchronization loop (`/_matrix/client/v3/sync?since={next_batch}&timeout=30000`)
7. Process new events returned from each sync and convert them for emission

### Heartbeat Mechanism

- The adapter sends a `heartbeat` metadata event every 30 seconds
- The adapter sends a `connect` metadata event upon successful connection
- The adapter sends a `disconnect` metadata event upon disconnection

### Room Invitations

- When a room invitation (room with `invite` state) is received, if the `auto_accept_invites` configuration is set to `true` (default), the adapter will automatically join the room
- To join the room, the adapter calls the `/_matrix/client/v3/join/{room_id}` endpoint

## Usage Examples

### Handling Group Messages

```python
from ErisPulse.Core.Event import message
from ErisPulse import sdk

matrix = sdk.adapter.get("matrix")

@message.on_message()
async def handle_group_msg(event):
    if event.get("platform") != "matrix":
        return
    if event.get("detail_type") != "group":
        return

    text = event.get_text()
    room_id = event.get("group_id")

    if text == "hello":
        await matrix.Send.To("group", room_id).Reply(
            event.get("message_id")
        ).Text("Hello!")
```

### Handling Reaction Events

```python
from ErisPulse.Core.Event import notice

@notice.on_notice()
async def handle_reaction(event):
    if event.get("platform") != "matrix":
        return

    if event.get("detail_type") == "matrix_reaction":
        reaction_key = event.get("matrix_reaction_key")
        reacted_event_id = event.get("matrix_reaction_event_id")
        room_id = event.get_room_id()
        # Handle reaction event...
```

### Sending Media Messages

```python
# Send image (URL)
await matrix.Send.To("group", room_id).Image("https://example.com/image.png")

# Send image (MXC URI)
await matrix.Send.To("group", room_id).Image("mxc://matrix.org/abc123")

# Send image (binary data)
with open("image.png", "rb") as f:
    image_bytes = f.read()
await matrix.Send.To("group", room_id).Image(image_bytes)

# Send image (local file path)
await matrix.Send.To("group", room_id).Image("/path/to/image.png")

# Send file (with filename)
await matrix.Send.To("group", room_id).File("/path/to/document.pdf", filename="Document.pdf")
```

### Handling Message Edits

```python
@message.on_message()
async def handle_edited_message(event):
    if event.get("platform") != "matrix":
        return

    if event.is_edited():
        original_id = event.get("matrix_original_event_id")
        # Handle edited message...
```

### Listening for Member Changes

```python
@notice.on_notice()
async def handle_member_change(event):
    if event.get("platform") != "matrix":
        return

    detail_type = event.get("detail_type")

    if detail_type == "group_member_increase":
        user_id = event.get("user_id")
        nickname = event.get("user_nickname")
        print(f"User {nickname} ({user_id}) joined the room")

    elif detail_type == "group_member_decrease":
        user_id = event.get("user_id")
        operator_id = event.get("operator_id")
        print(f"User {user_id} was removed, operator: {operator_id}")
```



### QQBot 适配

# QQBot Platform Features Documentation

QQBotAdapter is an adapter built based on the QQBot (QQ Bot Documentation) protocol, integrating all functional modules of QQBot and providing a unified interface for event handling and message operations.

---

## Document Information

- Corresponding Module Version: 1.0.0
- Maintainer: ErisPulse

## Basic Information

- Platform Overview: QQBot is the official bot development interface provided by QQ, supporting various scenarios such as group chats, private chats, and channels.
- Adapter Name: QQBotAdapter
- Connection Method: WebSocket long connection (via QQBot gateway)
- Authentication Method: Access token obtained based on appId + clientSecret
- Chained Modifier Support: Supports chained modifier methods such as `.Reply()`, `.At()`, `.AtAll()`, `.Keyboard()`, etc.
- OneBot12 Compatibility: Supports sending OneBot12 format messages

## Configuration Instructions

```toml
# config.toml
[QQBot_Adapter]
appid = "YOUR_APPID"          # QQ Bot Application ID (required)
secret = "YOUR_CLIENT_SECRET" # QQ Bot Client Secret (required)
sandbox = false               # Whether to use sandbox environment (optional, default is false)
intents = [1, 30, 25]        # Subscribed event intents bitmask (optional)
gateway_url = "wss://api.sgroup.qq.com/websocket/"  # Custom gateway URL (optional)
```

**Configuration Item Explanation:**
- `appid`: QQ Bot Application ID (required), obtained from the QQ Open Platform
- `secret`: QQ Bot Client Secret (required), obtained from the QQ Open Platform
- `sandbox`: Whether to use sandbox environment. The sandbox environment API address is `https://sandbox.api.sgroup.qq.com`
- `intents`: List of subscribed event intents. Each value is left-shifted and combined using bitwise OR operations.
  - `1`: Channel-related events
  - `25`: Channel message events
  - `30`: Group @ message events
- `gateway_url`: WebSocket gateway address, default is `wss://api.sgroup.qq.com/websocket/`

**API Environments:**
- Production environment: `https://api.sgroup.qq.com`
- Sandbox environment: `https://sandbox.api.sgroup.qq.com`

## Supported Message Sending Types

All sending methods are implemented using a fluent interface, for example:
```python
from ErisPulse.Core import adapter
qqbot = adapter.get("qqbot")

await qqbot.Send.To("user", user_openid).Text("Hello World!")
```

The supported sending types include:
- `.Text(text: str)`: Sends a plain text message.
- `.Image(file: bytes | str)`: Sends an image message, supporting file paths, URLs, and binary data.
- `.Markdown(content: str)`: Sends a message in Markdown format.
- `.Ark(template_id: int, kv: list)`: Sends an Ark template message.
- `.Embed(embed_data: dict)`: Sends an Embed message.
- `.Raw_ob12(message: List[Dict], **kwargs)`: Sends a OneBot12 formatted message.

### Fluent Modifier Methods (Can be Combined)

Fluent modifier methods return `self` and support fluent chaining, and must be called before the final sending method:

- `.Reply(message_id: str)`: Replies to a specified message.
- `.At(user_id: str)`: Mentions a specified user (inserts content in the format `<@user_id>`).
- `.AtAll()`: Mentions everyone (inserts the text `@所有人`).
- `.Keyboard(keyboard: dict)`: Adds keyboard buttons.

### Fluent Chaining Examples

```python
# Basic sending
await qqbot.Send.To("user", user_openid).Text("Hello")

# Reply to a message
await qqbot.Send.To("group", group_openid).Reply(msg_id).Text("Reply message")

# Reply + keyboard
await qqbot.Send.To("group", group_openid).Reply(msg_id).Keyboard(keyboard).Text("Message with reply and keyboard")

# Mention a user
await qqbot.Send.To("group", group_openid).At("member_openid").Text("Hello")

# Combining methods
await qqbot.Send.To("group", group_openid).Reply(msg_id).At("member_openid").Keyboard(keyboard).Text("Composite message")
```

### OneBot12 Message Support

The adapter supports sending OneBot12 formatted messages, facilitating cross-platform message compatibility:

```python
# Sending a OneBot12 formatted message
ob12_msg = [{"type": "text", "data": {"text": "Hello"}}]
await qqbot.Send.To("user", user_openid).Raw_ob12(ob12_msg)

# Combined with fluent modifiers
ob12_msg = [{"type": "text", "data": {"text": "Reply message"}}]
await qqbot.Send.To("group", group_openid).Reply(msg_id).Raw_ob12(ob12_msg)
```

## Return Values of Send Methods

All send methods return a Task object, which can be awaited directly to obtain the send result. The returned result follows the ErisPulse adapter's standardized return specification:

```python
{
    "status": "ok",           // Execution status: "ok" or "failed"
    "retcode": 0,             // Return code
    "data": {...},            // Response data
    "message_id": "123456",   // Message ID
    "message": "",            // Error message
    "qqbot_raw": {...}        // Raw response data
}
```

### Error Code Explanation

| retcode | Description |
|---------|-------------|
| 0 | Success |
| 10003 | Unable to determine the recipient |
| 32000 | Request timeout |
| 33000 | API call exception |
| 34000 | API returned unexpected format or business error |

## Platform-specific Event Types

Platform-specific features require `platform=="qqbot"` detection.

### Core Differences

1. **OpenID System**: QQBot uses OpenID instead of QQ numbers. User and group identifiers are both OpenID strings.
2. **Mention Requirement for Group Messages**: Group messages are only received when the user mentions the bot (`GROUP_AT_MESSAGE_CREATE`).
3. **Guild System**: QQBot supports messages and events for guilds (Guilds) and sub-channels (Channels).
4. **Message Moderation**: Sent messages may require moderation, with results notified through `qqbot_audit_pass`/`qqbot_audit_reject` events.
5. **Passive Reply**: Group and private messages support passive reply mechanisms, requiring `msg_id` to be included when sending replies.

### Extended Fields

- All platform-specific fields are prefixed with `qqbot_`.
- Original data is preserved in the `qqbot_raw` field.
- `qqbot_raw_type` indicates the original QQBot event type (e.g., `C2C_MESSAGE_CREATE`).
- Attachment data is stored in the `qqbot_attachment` field.

### Special Field Examples

```python
# Group @ Message
{
  "type": "message",
  "detail_type": "group",
  "user_id": "MEMBER_OPENID",
  "group_id": "GROUP_OPENID",
  "qqbot_group_openid": "GROUP_OPENID",
  "qqbot_member_openid": "MEMBER_OPENID",
  "qqbot_event_id": "Message Event ID",
  "qqbot_reply_token": "Reply Token"
}

# Private Message
{
  "type": "message",
  "detail_type": "private",
  "user_id": "USER_OPENID",
  "qqbot_openid": "USER_OPENID",
  "qqbot_event_id": "Message Event ID",
  "qqbot_reply_token": "Reply Token"
}

# Interaction Event
{
  "type": "notice",
  "detail_type": "qqbot_interaction",
  "qqbot_interaction_id": "Interaction ID",
  "qqbot_interaction_type": "Interaction Type",
  "qqbot_interaction_data": {
    "...": "Interaction Data"
  }
}

# Message Audit
{
  "type": "notice",
  "detail_type": "qqbot_audit_pass",
  "qqbot_audit_id": "Audit ID",
  "qqbot_message_id": "Message ID"
}

# Message Deletion
{
  "type": "notice",
  "detail_type": "qqbot_message_delete",
  "message_id": "Deleted Message ID",
  "operator_id": "Operator ID"
}

# Reaction Event
{
  "type": "notice",
  "detail_type": "qqbot_reaction_add",
  "qqbot_raw": {
    "...": "Raw Data"
  }
}
```

### Guild Message Segments

Guild messages support the `mentions` field, which is converted into `mention` message segments:

```json
{
  "type": "mention",
  "data": {
    "user_id": "Mentioned User ID",
    "user_name": "Mentioned User Nickname"
  }
}
```

### Attachment Message Segments

QQBot attachments are automatically converted into corresponding message segments based on `content_type`:

| content_type prefix | Conversion Type | Description |
|---|---|---|
| `image` | `image` | Image message |
| `video` | `video` | Video message |
| `audio` | `voice` | Voice message |
| Other | `file` | File message |

Attachment message segment structure:
```json
{
  "type": "image",
  "data": {
    "url": "Attachment URL",
    "qqbot_attachment": {
      "content_type": "image/png",
      "url": "Original Attachment URL"
    }
  }
}
```

## WebSocket Connection

### Connection Flow

1. Obtain `access_token` using `appId` + `clientSecret`
2. Connect to the WebSocket gateway
3. Receive OP_HELLO (op=10) message to get the heartbeat interval
4. Send OP_IDENTIFY (op=2) for authentication
5. Receive READY event to get `session_id` and `bot_id`
6. Start heartbeat loop (OP_HEARTBEAT, op=1)
7. Receive event dispatch (OP_DISPATCH, op=0)

### Disconnection and Reconnection

- Automatic reconnection is supported, with a maximum of 50 reconnection attempts
- Reconnection wait time uses exponential backoff algorithm: `min(5 * 2^min(count, 6), 300)` seconds
- Session resumption is supported (OP_RESUME, op=6), using `session_id` + `seq` to resume
- Automatic reconnection is triggered upon receiving OP_RECONNECT (op=7) or OP_INVALID_SESSION (op=9)

### Token Refresh

- The `access_token` validity is usually 7200 seconds
- The adapter automatically refreshes the token every 7080 seconds (7200-120)
- Refresh endpoint: `POST https://bots.qq.com/app/getAppAccessToken`

## Event Subscription (Intents)

The `intents` values are combined using bitwise operations:

```python
intents = [1, 30, 25]
value = 0
for intent in intents:
    value |= (1 << intent)
```

Common intent values:
| Intent Value | Description |
|--------------|-------------|
| 1 | Channel-related events (e.g., GUILD_CREATE) |
| 25 | Channel message events (e.g., AT_MESSAGE_CREATE) |
| 30 | Group mention message events (e.g., GROUP_AT_MESSAGE_CREATE) |

## Usage Examples

### Handling Group Messages

```python
from ErisPulse.Core.Event import message
from ErisPulse import sdk

qqbot = sdk.adapter.get("qqbot")

@message.on_message()
async def handle_group_msg(event):
    if event.get("platform") != "qqbot":
        return
    if event.get("detail_type") != "group":
        return

    text = event.get_text()
    group_id = event.get("group_id")

    if text == "hello":
        await qqbot.Send.To("group", group_id).Reply(
            event.get("message_id")
        ).Text("Hello!")
```

### Handling Interaction Events

```python
from ErisPulse.Core.Event import notice

@notice.on_notice()
async def handle_interaction(event):
    if event.get("platform") != "qqbot":
        return

    if event.get("detail_type") == "qqbot_interaction":
        interaction_id = event.get("qqbot_interaction_id", "")
        interaction_data = event.get("qqbot_interaction_data", {})
        # Handle interaction...
```

### Sending Media Messages

```python
# Send image (URL)
await qqbot.Send.To("group", group_openid).Image("https://example.com/image.png")

# Send image (binary)
with open("image.png", "rb") as f:
    image_bytes = f.read()
await qqbot.Send.To("user", user_openid).Image(image_bytes)
```

### Listening to Message Audit Results

```python
@notice.on_notice()
async def handle_audit(event):
    if event.get("platform") != "qqbot":
        return

    detail_type = event.get("detail_type")

    if detail_type == "qqbot_audit_pass":
        msg_id = event.get("qqbot_message_id")
        print(f"Message audit passed: {msg_id}")

    elif detail_type == "qqbot_audit_reject":
        reason = event.get("qqbot_audit_reject_reason", "")
        print(f"Message audit rejected: {reason}")
```



### 云湖用户端适配

# Yunhu User Platform Features Documentation

YunhuUserAdapter is an adapter based on the Yunhu user account protocol, allowing login through user email accounts, receiving events via WebSocket, and providing unified event processing and message operation interfaces.

---

## Document Information

- Corresponding Module Version: 1.4.0
- Maintainer: wsu2059

## Basic Information

- Platform Introduction: Yunhu is an enterprise-level instant messaging platform. This adapter interacts with it through **user accounts** (rather than bot accounts).
- Adapter Name: YunhuUserAdapter
- Multi-account Support: Supports identifying and configuring multiple user accounts through account names.
- Chain Decorator Support: Supports chained decorator methods like `.Reply()`.
- OneBot12 Compatibility: Supports sending OneBot12 format messages.
- Communication Method: Login via email to get token, use WebSocket to receive events, HTTP + Protobuf protocol to send messages.
- Session Types: Supports private chat (user), group chat (group), and bot chat (bot).

## Supported Message Sending Types

All sending methods are implemented through chained syntax, for example:
```python
from ErisPulse.Core import adapter
yunhu_user = adapter.get("yunhu_user")

await yunhu_user.Send.To("user", user_id).Text("Hello World!")
```

Supported sending types include:
- `.Text(text: str, buttons: Optional[List] = None)`: Send plain text messages.
- `.Html(html: str, buttons: Optional[List] = None)`: Send HTML format messages.
- `.Markdown(markdown: str, buttons: Optional[List] = None)`: Send Markdown format messages.
- `.Image(file: Union[str, bytes], buttons: Optional[List] = None)`: Send image messages, supporting URLs, local paths, or binary data.
- `.Video(file: Union[str, bytes], buttons: Optional[List] = None)`: Send video messages, supporting URLs, local paths, or binary data.
- `.Audio(file: Union[str, bytes], buttons: Optional[List] = None)`: Send voice messages, supporting URLs, local paths, or binary data, with automatic audio duration detection.
- `.Voice(file: Union[str, bytes], buttons: Optional[List] = None)`: Alias for `.Audio()`.
- `.File(file: Union[str, bytes], file_name: Optional[str] = None, buttons: Optional[List] = None)`: Send file messages, supporting URLs, local paths, or binary data.
- `.Face(file: Union[str, bytes], buttons: Optional[List] = None)`: Send emoji/sticker messages, supporting sticker IDs, sticker URLs, or binary image data.
- `.A2ui(a2ui_data: Union[str, Dict, List], buttons: Optional[List] = None)`: Send A2UI messages (message type 14), A2UI JSON data will be filled in the text field to send.
- `.Edit(msg_id: str, text: str, content_type: str = "text")`: Edit existing messages.
- `.Recall(msg_id: str)`: Recall messages.
- `.Raw_ob12(message: Union[List, Dict])`: Send OneBot12 format messages.

### Media File Processing

All media types (images, videos, audio, files) support the following input methods:
- **URL**: `"https://example.com/image.jpg"` — Automatically download and then upload
- **Local Path**: `"/path/to/file.jpg"` — Automatically read and then upload
- **Binary Data**: `open("file.jpg", "rb").read()` — Direct upload

Media files are automatically uploaded to Qiniu cloud storage, supporting the following features:
- Automatically detect file type and MIME using the `filetype` library
- Automatically calculate file size
- Automatically detect audio duration for audio files (supporting MP3, MP4/M4A formats)

### Button Parameter Description

The `buttons` parameter is a nested list representing the button layout and functionality. Each button object contains the following fields:

| Field         | Type   | Required | Description                                                                 |
|--------------|--------|----------|----------------------------------------------------------------------------|
| `text`       | string | Yes      | Text on the button                                                        |
| `actionType` | int    | Yes      | Action type:<br>`1`: Jump to URL<br>`2`: Copy<br>`3`: Click report           |
| `url`        | string | No       | Used when `actionType=1`, represents the target URL to jump to            |
| `value`      | string | No       | When `actionType=2`, this value will be copied to clipboard<br>When `actionType=3`, this value will be sent to the subscription end |

Example:
```python
buttons = [
    [
        {"text": "Copy", "actionType": 2, "value": "xxxx"},
        {"text": "Click to Jump", "actionType": 1, "url": "http://www.baidu.com"},
        {"text": "Report Event", "actionType": 3, "value": "xxxxx"}
    ]
]
await yunhu_user.Send.To("user", user_id).Buttons(buttons).Text("Message with buttons")
```

### Chained Decorator Methods (Combinable)

Chained decorator methods return `self`, supporting chained calls and must be called before the final sending method:

- `.Reply(message_id: str)`: Reply to a specific message.
- `.At(user_id: str)`: @mention a specific user (in text form @user_id).
- `.AtAll()`: @mention everyone (pseudo @all, sends @all text).
- `.Buttons(buttons: List)`: Add buttons.

> **Note:** Because user accounts are special, even non-admin users can @everyone, but `AtAll()` here only sends a @everyone text, which is a pseudo @everyone.

### Chained Call Examples

```python
# Basic sending
await yunhu_user.Send.To("user", user_id).Text("Hello")

# Reply to message
await yunhu_user.Send.To("group", group_id).Reply(msg_id).Text("Reply message")

# Reply + buttons
await yunhu_user.Send.To("group", group_id).Reply(msg_id).Buttons(buttons).Text("Message with reply and buttons")

# Specify account + reply + buttons
await yunhu_user.Send.Using("default").To("group", group_id).Reply(msg_id).Buttons(buttons).Text("Complete chained call")
```

### OneBot12 Message Support

The adapter supports sending OneBot12 format messages for cross-platform message compatibility:

- `.Raw_ob12(message: List[Dict], **kwargs)`: Send OneBot12 format messages.

```python
# Send OneBot12 format message
ob12_msg = [{"type": "text", "data": {"text": "Hello"}}]
await yunhu_user.Send.To("user", user_id).Raw_ob12(ob12_msg)

# With chained decorators
ob12_msg = [{"type": "text", "data": {"text": "Reply message"}}]
await yunhu_user.Send.To("group", group_id).Reply(msg_id).Raw_ob12(ob12_msg)
```

Raw_ob12 supports automatically grouping and processing mixed message segments:
- `text`, `mention` types can be merged into one group for sending
- `image`, `video`, `audio`, `file`, `face`, `markdown`, `html`, `a2ui` etc. types each form their own group
- `reply` type can be attached to any group

## Method Return Values

All sending methods return a Task object, which can be directly awaited to get the sending result. The return result follows the ErisPulse adapter standardized return specification:

```python
{
    "status": "ok",           // Execution status
    "retcode": 0,             // Return code
    "data": {...},            // Response data
    "message_id": "123456",   // Message ID
    "message": "",            // Error message
    "yunhu_user_raw": {...}   // Original response data
}
```

## Special Event Types

Requires checking `platform == "yunhu_user"` before using platform-specific features

### Core Differences

1. Special event types:
    - Super file sharing: `yunhu_user_file_send`
    - Bot announcement board: `yunhu_user_bot_board`
    - Message edit notification: `message_edit`
    - Message deletion notification: `message_delete` (recall)
2. Special message segment types:
    - Form message segment: `yunhu_user_form`
    - Article message segment: `yunhu_user_post`
    - Sticker message segment: `yunhu_user_sticker`
    - Button message segment: `yunhu_user_button`
    - A2UI message segment: `a2ui`
3. Extended fields:
    - All special fields are prefixed with `yunhu_user_`
    - Original data is retained in the `yunhu_user_raw` field
    - Original event type is recorded in the `yunhu_user_raw_type` field
    - In private chats, `self.user_id` represents the current logged-in user ID

### Supported Original Event Types

| Original Event Type | OneBot12 Type | Description |
|--------------------|--------------|-------------|
| `push_message` | `message` | Push message (private chat, group chat, bot chat) |
| `edit_message` | `notice` (`message_edit`) | Message edit event |
| `file_send_message` | `notice` (`yunhu_user_file_send`) | Super file sharing event |
| `bot_board_message` | `notice` (`yunhu_user_bot_board`) | Bot announcement board event |

> Other event types (such as `heartbeat_ack`, `draft_input`, `stream_message`, etc.) will be ignored.

### OneBot12 Supported detail_type

| OneBot12 detail_type | Yunhu chat_type | Description |
|---------------------|---------------|-------------|
| `private` | 1 | Private chat message |
| `group` | 2 | Group chat message |
| `bot` | 3 | Bot chat |

### Message Event Example

```python
{
    "id": "event_id",
    "time": 1234567890,
    "type": "message",
    "detail_type": "group",
    "platform": "yunhu_user",
    "self": {
        "platform": "yunhu_user",
        "user_id": "your_user_id"
    },
    "message": [
        {"type": "text", "data": {"text": "Message content"}}
    ],
    "alt_message": "Message content",
    "user_id": "sender_user_id",
    "user_nickname": "Sender nickname",
    "group_id": "group_id",
    "message_id": "msg_id",
    "yunhu_user_raw": {...},
    "yunhu_user_raw_type": "push_message"
}
```

### Message Edit Notification Example

```python
{
    "type": "notice",
    "detail_type": "message_edit",
    "platform": "yunhu_user",
    "self": {
        "platform": "yunhu_user",
        "user_id": "your_user_id"
    },
    "message_id": "msg_id",
    "user_id": "sender_user_id",
    "user_nickname": "Sender nickname",
    "edit_time": 1234567890,
    "group_id": "group_id",
    "yunhu_user_raw": {...},
    "yunhu_user_raw_type": "edit_message"
}
```

### Super File Sharing Event Example

```python
{
    "type": "notice",
    "detail_type": "yunhu_user_file_send",
    "platform": "yunhu_user",
    "self": {
        "platform": "yunhu_user",
        "user_id": "your_user_id"
    },
    "user_id": "send_user_id",
    "user_nickname": "",
    "yunhu_user_file_send": {
        "send_user_id": "Sender ID",
        "user_id": "Recipient user ID",
        "send_type": "Send type",
        "data": "File data"
    },
    "yunhu_user_raw": {...},
    "yunhu_user_raw_type": "file_send_message"
}
```

### Bot Announcement Board Event Example

```python
{
    "type": "notice",
    "detail_type": "yunhu_user_bot_board",
    "platform": "yunhu_user",
    "self": {
        "platform": "yunhu_user",
        "user_id": "your_user_id"
    },
    "bot_id": "bot_id",
    "bot_name": "Bot name",
    "yunhu_user_bot_board": {
        "bot_id": "bot_id",
        "chat_id": "chat_id",
        "chat_type": 1,
        "content": "Announcement content",
        "content_type": 1,
        "last_update_time": 1234567890
    },
    "yunhu_user_raw": {...},
    "yunhu_user_raw_type": "bot_board_message"
}
```

### Event Handling Example

```python
from ErisPulse.Core.Event import message, notice

@message.on_message()
async def handle_yunhu_user_message(event):
    """Handle Yunhu user messages"""
    if event.get("platform") != "yunhu_user":
        return
    
    user_id = event.get("user_id", "")
    user_nickname = event.get("user_nickname", "")
    alt_message = event.get("alt_message", "")
    
    print(f"User {user_nickname}({user_id}): {alt_message}")
    
    # Check for special types in message segments
    for segment in event.get("message", []):
        seg_type = segment.get("type", "")
        
        if seg_type == "yunhu_user_form":
            form_data = segment["data"]["form"]
            print(f"Received form message: {form_data}")
        
        elif seg_type == "yunhu_user_post":
            post_data = segment["data"]
            print(f"Received article message: {post_data.get('post_title', '')}")
        
        elif seg_type == "yunhu_user_sticker":
            sticker_url = segment["data"]["file_id"]
            print(f"Received sticker message: {sticker_url}")
        
        elif seg_type == "yunhu_user_button":
            buttons = segment["data"]["buttons"]
            print(f"Message contains buttons: {buttons}")
        
        elif seg_type == "a2ui":
            a2ui_data = segment["data"]["a2ui"]
            print(f"Received A2UI message: {a2ui_data}")
    
    # Use event.reply() to automatically reply
    await event.reply(f"Echo: {alt_message}")

@notice.on_notice()
async def handle_yunhu_user_notice(event):
    """Handle Yunhu user notification events"""
    if event.get("platform") != "yunhu_user":
        return
    
    detail_type = event.get("detail_type", "")
    
    if detail_type == "message_edit":
        message_id = event.get("message_id", "")
        user_nickname = event.get("user_nickname", "")
        edit_time = event.get("edit_time", 0)
        print(f"User {user_nickname} edited message {message_id}")
    
    elif detail_type == "yunhu_user_file_send":
        file_data = event.get("yunhu_user_file_send", {})
        print(f"Received super file sharing: {file_data}")
    
    elif detail_type == "yunhu_user_bot_board":
        board_data = event.get("yunhu_user_bot_board", {})
        bot_name = event.get("bot_name", "")
        print(f"Bot {bot_name} published announcement: {board_data.get('content', '')}")
```

## Extended Field Description

- All special fields are prefixed with `yunhu_user_` to avoid conflicts with standard fields
- Original data is retained in the `yunhu_user_raw` field for accessing complete original data from Yunhu platform
- Original event type is recorded in the `yunhu_user_raw_type` field (such as `push_message`, `edit_message`, etc.)
- `self.user_id` represents the current logged-in user ID (obtained from login response)
- Super file sharing provides file sharing data through the `yunhu_user_file_send` field
- Bot announcement board provides announcement data through the `yunhu_user_bot_board` field

### Special Message Segment Types

#### Form Message Segment (yunhu_user_form)

When content_type is 5, the message segment type is `yunhu_user_form`:

```json
{
    "type": "yunhu_user_form",
    "data": {
        "form": "Form data"
    }
}
```

#### Article Message Segment (yunhu_user_post)

When content_type is 6, the message segment type is `yunhu_user_post`:

```json
{
    "type": "yunhu_user_post",
    "data": {
        "post_id": "Article ID",
        "post_title": "Article title",
        "post_content": "Article content"
    }
}
```

| Field | Type | Description |
|------|------|-------------|
| `post_id` | string | Unique identifier for the article |
| `post_title` | string | Article title |
| `post_content` | string | Article content |

#### Sticker Message Segment (yunhu_user_sticker)

When content_type is 7, the message segment type is `yunhu_user_sticker`:

```json
{
    "type": "yunhu_user_sticker",
    "data": {
        "file_id": "Sticker image URL"
    }
}
```

| Field | Type | Description |
|------|------|-------------|
| `file_id` | string | Sticker image URL |

#### Button Message Segment (yunhu_user_button)

When the message contains buttons, a `yunhu_user_button` message segment is attached:

```json
{
    "type": "yunhu_user_button",
    "data": {
        "buttons": [[{"text": "Button text", "actionType": 3, "value": "Value"}]]
    }
}
```

#### A2UI Message Segment (a2ui)

When content_type is 14, the message segment type is `a2ui`:

```json
{
    "type": "a2ui",
    "data": {
        "a2ui": "A2UI JSON data"
    }
}
```

---

## Multi-Account Configuration

### Configuration Description

YunhuUserAdapter supports configuring and running multiple user accounts simultaneously.

```toml
# config.toml
[YunhuUserAdapter]
ws_reconnect_interval = 30  # WebSocket reconnect interval (seconds)
ws_timeout = 70             # WebSocket timeout (seconds)

[YunhuUserAdapter.accounts.default]
email = "user1@example.com"  # User email (required)
password = "password1"       # User password (required)
platform = "windows"         # Login platform (optional, default windows)
device_id = ""               # Device ID (optional, auto-generated if not specified)
enabled = true               # Whether to enable (optional, default true)

[YunhuUserAdapter.accounts.account2]
email = "user2@example.com"
password = "password2"
platform = "android"
device_id = "fixed_device_id_2"
enabled = true
```

**Configuration Item Description:**
- `email`: User email (required), used to login to Yunhu platform
- `password`: User password (required)
- `platform`: Login platform identifier (optional, default `windows`), optional values: `windows`, `macos`, `linux`, `ios`, `android`
- `device_id`: Device ID (optional, auto-generated if not specified), it is recommended to set a fixed value to maintain session consistency
- `enabled`: Whether to enable this account (optional, default `true`)

**Adapter Level Configuration:**
- `ws_reconnect_interval`: WebSocket reconnect interval (seconds, default 30)
- `ws_timeout`: WebSocket timeout (seconds, default 70)

**Important Notes:**
1. The adapter uses email login to get tokens, and receives events through WebSocket after login
2. WebSocket connection will automatically reconnect after disconnection, with a maximum of 3 retry attempts
3. It is recommended to set a fixed `device_id` for each account to maintain session consistency
4. Template accounts with unchanged default email and password will be automatically skipped

### Using Send DSL to Specify Accounts

You can specify which account to use for sending messages through the `Using()` method. This method supports two parameters:
- **Account name**: The account name in the configuration (such as `default`, `account2`)
- **user_id**: The user ID obtained after login

```python
from ErisPulse.Core import adapter
yunhu_user = adapter.get("yunhu_user")

# Send message using account name
await yunhu_user.Send.Using("default").To("user", "user123").Text("Hello from account1!")

# Send message using user_id (automatically matches corresponding account)
await yunhu_user.Send.Using("user_id_here").To("group", "group456").Text("Hello from user!")

# Use the first enabled account when not specified
await yunhu_user.Send.To("user", "user123").Text("Hello from default account!")
```

> **Tip:** When using `user_id`, the system will automatically find the matching account in the configuration. This is especially useful when handling event replies, where you can directly use `event["self"]["user_id"]` to reply to the same account.

### Account Identification in Events

Received events will automatically contain the corresponding user ID information:

```python
from ErisPulse.Core.Event import message

@message.on_message()
async def handle_message(event):
    if event["platform"] == "yunhu_user":
        # Get current logged-in user ID
        my_user_id = event["self"]["user_id"]
        print(f"Message from account: {my_user_id}")
        
        # Reply using the same account
        yunhu_user = adapter.get("yunhu_user")
        await yunhu_user.Send.Using(my_user_id).To(
            event["detail_type"],
            event["user_id"] if event["detail_type"] == "private" else event["group_id"]
        ).Text("Reply message")
```

### Log Information

The adapter will automatically include account information in logs for debugging and tracking:

```
[INFO] Account default (user1@example.com) login successful, user ID: 12345678
[INFO] Account default WebSocket listening task started
[INFO] Account account2 (user2@example.com) login successful, user ID: 87654321
```

### Management Interface

```python
# Get all account information
accounts = yunhu_user.accounts
# Return format: {"default": {"name": "default", "email": "...", "token": "...", "user_id": "...", ...}, ...}

# Check if account is enabled
for account_name, account_config in yunhu_user._account_configs.items():
    print(f"{account_name}: enabled={account_config.enabled}")

# Get HTTP client by account name
http_client = yunhu_user._get_http_client("default")

# Find account by user_id
account_name = yunhu_user._get_account_by_user_id("12345678")
```

## API Calls

The adapter provides a `call_api` method that supports direct platform API calls:

```python
# Send message
result = await yunhu_user.call_api("/send", 
    target_type="group", 
    target_id="group_id",
    account_id="default",
    message={"text": "Hello", "msg_type": 1}
)

# Edit message
result = await yunhu_user.call_api("/edit",
    target_type="group",
    target_id="group_id",
    msg_id="msg_id",
    text="New content",
    content_type="text"
)

# Recall message
result = await yunhu_user.call_api("/recall",
    target_type="group",
    target_id="group_id",
    msg_id="msg_id"
)

# Batch recall messages
result = await yunhu_user.call_api("/recall_batch",
    target_type="group",
    target_id="group_id",
    msg_id_list=["msg_id_1", "msg_id_2"]
)

# Get message list
result = await yunhu_user.call_api("/list",
    chat_id="group_id",
    chat_type=2,
    msg_count=10,
    msg_id=""
)

# Get message edit records
result = await yunhu_user.call_api("/list_edit_record",
    msg_id="msg_id",
    size=10,
    page=1
)

# Button event report
result = await yunhu_user.call_api("/button_report",
    chat_id="group_id",
    chat_type=2,
    msg_id="msg_id",
    user_id="user_id",
    button_value="button_value"
)
```

**Supported API Endpoints:**

| Endpoint | Description |
|----------|-------------|
| `/send` | Send message |
| `/edit` | Edit message |
| `/recall` | Recall message |
| `/recall_batch` | Batch recall messages |
| `/list` | Get message list |
| `/list_by_seq` | Get message by sequence |
| `/list_by_mid_seq` | Get message by message ID and sequence |
| `/list_edit_record` | Get message edit records |
| `/button_report` | Button event report |



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
- [ErisPulse Core Concepts](../getting-started/basic-concepts.md)
- [Event Conversion Standards](../standards/event-conversion.md)
- [API Response Specifications](../standards/api-response.md)
- [Other Platform Adapter Documentation](./)

## Contribution Flow

1. Fork [ErisPulse](https://github.com/ErisPulse/ErisPulse) repository
2. Modify the corresponding platform documentation under the `docs/platform-features/` directory
3. Ensure the documentation complies with the above requirements
4. Submit a Pull Request with a detailed description of the changes

If you have any questions, please contact the relevant adapter maintainer or ask in the project Issues.



### 花枫咖啡馆适配

# RockyChat (IdeauraAdapter) Platform Features Document

IdeauraAdapter is an adapter built on the RockyChat platform API, integrating all platform feature modules and providing a unified event handling and message operation interface.

---

## Document Information

- Corresponding Module: ErisPulse-Ideaura
- Corresponding Module Version: 4.0.1
- Maintainer: ErisPulse

## Basic Information

- Platform Introduction: RockyChat is an instant messaging platform.
- Adapter Name: IdeauraAdapter
- Multi-Account Support: Supports multiple accounts configured via Bot Token.
- Chained Modifier Support: Supports chained modifier methods such as `.At()`, `.AtAll()`, `.Reply()`, `.Command()`.
- OneBot12 Compatibility: Supports sending OneBot12 format messages.

## Supported Message Sending Types

All sending methods are implemented using chained syntax, for example:
```python
from ErisPulse.Core import adapter
ideaura = adapter.get("ideaura")

await ideaura.Send.To("group", "chatroom").Text("Hello World!")
```

The supported sending types include:
- `.Text(text: str)`: Send plain text messages.
- `.Image(file, filename: str = None)`: Send image messages, supporting bytes/URL/local path.
- `.Video(file, filename: str = None)`: Send video messages, supporting bytes/URL/local path.
- `.File(file, filename: str = None)`: Send file messages, supporting bytes/URL/local path.
- `.Voice(file, filename: str = None)`: Send voice messages (sent as files).
- `.Face(face_id: str)`: Send emoticons (sent as emoji in plain text).
- `.Markdown(text: str)`: Send messages in Markdown format.
- `.Html(html: str)`: Send messages in HTML format.
- `.Edit(message_id: str, text: str, content_type: str = "text")`: Edit existing messages.
- `.Recall(message_id: str)`: Recall messages.

### Chained Modifier Methods (can be combined)

Chained modifier methods return `self`, supporting chained calls, and must be called before the final sending method:

- `.At(user_id: str, name: str = None)`: Mention a specific user.
- `.AtAll()`: Mention everyone.
- `.Reply(message_id: str)`: Reply to a specific message.
- `.Command(command_id: str)`: Trigger a Bot command, used in combination with sending methods (sends the message as a specified command).

### Chained Call Examples

```python
# Basic sending
await ideaura.Send.To("user", user_id).Text("Hello")

# Trigger Bot command
await ideaura.Send.To("group", "chatroom").Command("550e8400-e29b-41d4-a716-446655440000").Text("/weather 北京")

# Mention a user
await ideaura.Send.To("group", "chatroom").At("456").Text("@李四 你好")

# Mention multiple users
await ideaura.Send.To("group", "chatroom").At("456").At("789").Text("@多人")

# Reply to a message
await ideaura.Send.To("group", "chatroom").Reply(msg_id).Text("回复消息")

# Reply + Mention
await ideaura.Send.To("group", "chatroom").Reply(msg_id).At("456").Text("回复并@")
```

### Sending to Different Targets

```python
# Send to a chatroom
await ideaura.Send.To("group", "chatroom").Text("聊天室消息")

# Send to a topic
await ideaura.Send.To("group", "topic_id").Text("话题消息")

# Send a private message
await ideaura.Send.To("user", "user_id").Text("私聊消息")
```

### OneBot12 Message Support

The adapter supports sending OneBot12 format messages, facilitating cross-platform message compatibility:

- `.Raw_ob12(message: List[Dict], **kwargs)`: Send OneBot12 format messages.

```python
# Send OneBot12 format message
ob12_msg = [{"type": "text", "data": {"text": "Hello"}}]
await ideaura.Send.To("user", user_id).Raw_ob12(ob12_msg)

# Combined with chained modifiers
ob12_msg = [{"type": "text", "data": {"text": "回复消息"}}]
await ideaura.Send.To("group", "chatroom").Reply(msg_id).Raw_ob12(ob12_msg)
```

## Sending Method Return Values

All sending methods return a Task object, which can be awaited to obtain the sending result. The returned result follows the standardized return specification of the ErisPulse adapter:

```python
{
    "status": "ok",           // Execution status
    "retcode": 0,             // Return code
    "data": {...},            // Response data
    "self": {...},            // Self information (including user_id)
    "message_id": "123456",   // Message ID
    "message": "",            // Error message
    "ideaura_raw": {...}      // Raw response data
}
```

## Unique Event Types

Use platform-specific features only after checking `platform=="ideaura"`

### Core Differences

1. Unique event types:
    - Message edit: ideaura_message_edit
    - Message recall: ideaura_message_recall
    - Message forward: ideaura_message_forward
    - Message read: ideaura_message_read
    - Friend rejected: ideaura_friend_rejected
    - Friend online: ideaura_friend_online
    - Friend offline: ideaura_friend_offline
    - User status change: ideaura_user_status_change
    - Forwarded message segment: ideaura_forwarded
    - Edited marker segment: ideaura_edited
    - Markdown message segment: ideaura_markdown
    - HTML message segment: ideaura_html
    - Bot command message segment: ideaura_command
2. Extended fields:
    - All unique fields are prefixed with `ideaura_`
    - Original data is retained in the `ideaura_raw` field
    - `self.user_id` indicates the current account's user ID

### Message Edit Event

```python
{
  "type": "notice",
  "detail_type": "ideaura_message_edit",
  "platform": "ideaura",
  "message_id": "Message ID",
  "user_id": "Editor ID",
  "ideaura_new_content": "Content after edit",
  "ideaura_updated_message": { ... },
  "ideaura_source_type": "chatroom/topic/private"
}
```

### Message Recall Event

```python
{
  "type": "notice",
  "detail_type": "ideaura_message_recall",
  "platform": "ideaura",
  "message_id": "Message ID to be recalled",
  "user_id": "Recaller ID",
  "group_id": "chatroom",
  "ideaura_source_type": "chatroom",
  "ideaura_recall_time": "Recall time",
  "ideaura_is_self": false
}
```

### Message Forward Event

```python
{
  "type": "notice",
  "detail_type": "ideaura_message_forward",
  "platform": "ideaura",
  "message_id": "Original message ID",
  "user_id": "Forwarder ID",
  "ideaura_forward_to": "Target topic ID",
  "ideaura_original_message_id": "Original message ID",
  "ideaura_forwarded_message_id": "New message ID after forwarding"
}
```

### Message Read Event

```python
{
  "type": "notice",
  "detail_type": "ideaura_message_read",
  "platform": "ideaura",
  "message_id": "Message ID",
  "ideaura_reader_id": "Reader ID",
  "ideaura_reader_name": "Reader nickname"
}
```

### Friend Online Event

```python
{
  "type": "notice",
  "detail_type": "ideaura_friend_online",
  "platform": "ideaura",
  "user_id": "Friend ID",
  "user_nickname": "Friend nickname",
  "ideaura_friend_avatar": "Avatar URL",
  "ideaura_presence_status": "online"
}
```

### Friend Offline Event

```python
{
  "type": "notice",
  "detail_type": "ideaura_friend_offline",
  "platform": "ideaura",
  "user_id": "Friend ID",
  "ideaura_presence_status": "offline"
}
```

### User Status Change Event

```python
{
  "type": "notice",
  "detail_type": "ideaura_user_status_change",
  "platform": "ideaura",
  "user_id": "User ID",
  "ideaura_status": "New status",
  "ideaura_previous_status": "Old status"
}
```

### Friend Request Event

```python
{
  "type": "request",
  "detail_type": "friend",
  "platform": "ideaura",
  "user_id": "Requester ID",
  "user_nickname": "Requester nickname",
  "ideaura_request_id": "Request ID",
  "ideaura_message": "Verification message"
}
```

### Friend Rejected Event

```python
{
  "type": "notice",
  "detail_type": "ideaura_friend_rejected",
  "platform": "ideaura",
  "user_id": "Rejector ID",
  "user_nickname": "Rejector nickname",
  "ideaura_request_id": "Request ID",
  "ideaura_requester_id": "Request initiator ID",
  "ideaura_requester_name": "Request initiator nickname"
}
```

### Forwarded Message Segment (ideaura_forwarded)

When receiving a forwarded message, the message segment type is `ideaura_forwarded`:

```json
{
  "type": "ideaura_forwarded",
  "data": {
    "forward_source_id": "1001",
    "original_message_id": "1001"
  }
}
```

| Field | Type | Description |
|------|------|------|
| `forward_source_id` | string | Forward source message ID |
| `original_message_id` | string | Original message ID |

### Bot Command Message Segment (ideaura_command)

When a user triggers a Bot command, the message segment type is `ideaura_command`:

```json
{
  "type": "ideaura_command",
  "data": {
    "command_id": "550e8400-e29b-41d4-a716-446655440000"
  }
}
```

| Field | Type | Description |
|------|------|------|
| `command_id` | string | Command UUID |

### Event Handling Example

```python
from ErisPulse.Core.Event import notice, message

@message.on_message()
async def handle_message(event):
    if event.get_platform() == "ideaura":
        # Handle message events
        for segment in event.get("message", []):
            if segment.get("type") == "ideaura_forwarded":
                data = segment["data"]
                print(f"Forwarded message, source ID: {data['forward_source_id']}")

@notice.on_notice()
async def handle_notice(event):
    if event.get_platform() != "ideaura":
        return

    detail_type = event.get("detail_type")

    if detail_type == "ideaura_message_edit":
        new_content = event.get("ideaura_new_content", "")
        print(f"Message edited: {new_content}")

    elif detail_type == "ideaura_message_recall":
        message_id = event.get("message_id")
        print(f"Message recalled: {message_id}")

    elif detail_type == "ideaura_friend_online":
        friend_name = event.get_user_nickname()
        print(f"Friend online: {friend_name}")

    elif detail_type == "ideaura_user_status_change":
        status = event.get("ideaura_status")
        print(f"User status changed: {status}")
```

## Event Mixin Extension Methods

The adapter registers the following platform-specific methods, available only when `platform == "ideaura"`:

| Method | Return Type | Description |
|------|----------|------|
| `get_source_type()` | `str` | Message source type (`chatroom`/`topic`/`private`) |
| `get_sender_name()` | `str` | Sender nickname |
| `get_sender_avatar()` | `str` | Sender avatar URL |
| `is_sender_bot()` | `bool` | Whether the sender is a bot |
| `is_receiver_bot()` | `bool` | Whether the receiver is a bot |
| `get_command_id()` | `str` | Triggered Bot command ID (if any, `ideaura_command_id`) |
| `get_command()` | `str` | Alias for `get_command_id()` |
| `get_topic_name()` | `str` | Topic name |
| `get_message_type()` | `str` | Message type (normal/edited/forwarded/quoted) |
| `get_message_subtype()` | `str` | Message sub-type (text/image/video/file/markdown/html) |
| `is_self_message()` | `bool` | Whether the message was sent by oneself |

```python
from ErisPulse.Core.Event import message

@message.on_message()
async def handle_message(event):
    if event.get_platform() != "ideaura":
        return

    # Get the triggered Bot command ID (if any)
    cmd_id = event.get_command_id()
    if cmd_id:
        print(f"Received command: {cmd_id}")
```

---

## Multi-Account Configuration

### Configuration Description

IdeauraAdapter supports configuring and running multiple accounts simultaneously, using **Bot Token** authentication.

> [!WARNING]
> As of version 4.0.1, **email/password login has been removed**, and only Bot Token is supported. Bot Token can be obtained from the [MSCPO Open Platform](https://open.mscpo.com/rockychat/bots) (must start with `bot-token-`).

```toml
# config.toml
# Account 1
[IdeauraAdapter.accounts.default]
token = "bot-token-xxxxxx1"      # Bot API Token (required)
enabled = true                   # Whether to enable (optional, default is true)

# Account 2
[IdeauraAdapter.accounts.bot2]
token = "bot-token-xxxxxx2"
enabled = true

# Optional: Custom server address
[IdeauraAdapter]
base_url = "https://api.mscpo.com/api/rockychat"
ws_url = "wss://api-cofe.allons-y.uk:3009/mqtt"
heartbeat_interval = 30
```

**Configuration Item Description:**
- `token`: Bot API Token (required, must start with `bot-token-`)
- `enabled`: Whether to enable this account (optional, default is true)

**Global Configuration Items:**
- `base_url`: API server address (optional, default is `https://api.mscpo.com/api/rockychat`)
- `ws_url`: WebSocket server address (optional, default is the official RockyChat address)
- `heartbeat_interval`: Heartbeat interval in seconds (optional, default is 30 seconds)

### Using Send DSL to Specify Account

You can specify which account to use for sending messages via the `Using()` method:

```python
from ErisPulse.Core import adapter
ideaura = adapter.get("ideaura")

# Send message using account name
await ideaura.Send.Using("default").To("user", "user123").Text("Hello from account 1!")

# Send message using user_id (automatically matches the corresponding account)
await ideaura.Send.Using("456").To("group", "chatroom").Text("Hello from account 2!")

# If not specified, use the first enabled account
await ideaura.Send.To("user", "user123").Text("Hello from default account!")
```

### Account Identifier in Events

Events received automatically include corresponding account information:

```python
from ErisPulse.Core.Event import message

@message.on_message()
async def handle_message(event):
    if event["platform"] == "ideaura":
        account_id = event["self"]["user_id"]
        print(f"Message from account: {account_id}")
```

---

## Extended Field Description

- All unique fields are prefixed with `ideaura_` to avoid conflicts with standard fields
- Original data is retained in the `ideaura_raw` field, facilitating access to the platform's complete raw data
- `self.user_id` indicates the user ID of the currently logged-in account
- `ideaura_source_type`: Message source type (`chatroom`/`topic`/`private`)
- `ideaura_sender_name`: Sender nickname
- `ideaura_sender_avatar`: Sender avatar URL
- `ideaura_sender_is_bot`: Whether the sender is a bot
- `ideaura_is_self`: Whether the message was sent by oneself (self-messages are filtered out)
- `ideaura_topic_name`: Topic name
- `ideaura_message_type`: Message type (normal/edited/forwarded/quoted)
- `ideaura_message_subtype`: Message sub-type (text/image/video/file/markdown/html)

### File Handling Features

- File size limit: 10MB (both download and local reading are limited)
- Automatic file type detection: Detects actual type via file header magic bytes
- Intelligent filename parsing: Automatically corrects meaningless extensions such as `.bin`/`.dat`/`.tmp`
- Supports three file input methods: bytes, URL, and local path
- Automatically downloads and uploads URL files to the server

### Supported File Types

Detected automatically via magic bytes:

| Type | Extension |
|------|--------|
| Image | png, jpg, gif, webp |
| Video | mp4, avi, flv |
| Audio | mp3, wav, ogg |
| Document | pdf, docx |

---

## Notes

1. The default API server address is `https://api.mscpo.com/api/rockychat` (can be customized via `base_url`); the WebSocket address `wss://api-cofe.allons-y.uk:3009/mqtt` is a platform-specific address and does not change with the adapter name.
2. The adapter uses a WebSocket long connection to receive events and supports automatic reconnection (fixed 5-second delay).
3. Messages sent by oneself (`isSelf: true`) are automatically filtered and do not generate events.
4. `AtAll()` requires administrator privileges.
5. File upload size limit is 10MB.
6. Audio files are sent as `file` sub-type (the platform does not distinguish independent audio types).
7. Emoticons (`Face()`) are sent as plain text emoji.
8. Call `shutdown()` before program exit to ensure resource release.



### Discord 适配

# Discord Platform Feature Documentation

DiscordAdapter is an adapter built on top of the Discord Gateway (WebSocket) and REST API v10 protocol, integrating the core functionalities of Discord Bots and providing a unified interface for event handling and message operations.

---

## Documentation Information

- Corresponding Module Version: 4.1.0
- Maintainer: ErisPulse
- Discord API Version: v10

## Basic Information

- Platform Introduction: Discord is a widely popular community communication platform that supports various conversation forms such as servers, channels, and private messages, and provides a comprehensive Bot development interface.
- Adapter Name: DiscordAdapter
- Multi-account Support: Supports configuring multiple Discord bots simultaneously.
- Connection Method: Gateway WebSocket (for receiving events) + REST API (for sending messages/calling APIs)
- Authentication Method: Bot Token (HTTP header `Authorization: Bot {token}`, token carried in the Gateway IDENTIFY payload)
- Chained Modifier Support: Supports chained modifier methods such as `.Reply()`, `.At()`, and `.AtAll()`
- OneBot12 Compatibility: Supports sending OneBot12 formatted messages.

## Configuration Guide

The DiscordAdapter supports multi-account configuration, where each account corresponds to a separate Discord Bot.

```toml
# config.toml

# Account 1
[DiscordAdapter.accounts.default]
token = "YOUR_BOT_TOKEN"       # Discord Bot Token (required)
intents = 33281                 # Gateway Intents (optional, default: 33281)
enabled = true                  # Whether to enable (optional, default: true)

# Account 2
[DiscordAdapter.accounts.bot2]
token = "ANOTHER_BOT_TOKEN"
intents = 33281
enabled = true
```

**Configuration Item Description (per account):**

- `token`: Discord Bot Token (required), obtained from [Discord Developer Portal](https://discord.com/developers/applications)
- `intents`: Gateway Intents bitmask (optional, default: `33281`), determines the types of events the Bot subscribes to
- `bot_id`: Bot's user ID (optional, automatically obtained at runtime from the READY event, no need to manually fill)
- `enabled`: Whether to enable this account (optional, default: `true`)

### Gateway Intents

Intents use bitmasks, calculated by bitwise OR (`|`) of each Intent value:

| Intent | Bit | Value | Description | Privileged |
|-------|------|------|------|------|
| GUILDS | `1 << 0` | 1 | Server creation/deletion/update, channels, role changes | No |
| GUILD_MEMBERS | `1 << 1` | 2 | Member join/leave/update | Yes |
| GUILD_MESSAGES | `1 << 9` | 512 | Server message sending/receiving | No |
| MESSAGE_CONTENT | `1 << 15` | 32768 | Message content (content is empty without this Intent) | Yes |

Default value `33281` = `GUILDS(1) | GUILD_MESSAGES(512) | MESSAGE_CONTENT(32768)`.

> **Note**: Privileged Intents must be enabled in Discord Developer Portal → Bot → Privileged Gateway Intents. If the Bot is in more than 100 servers, Discord review is also required.

**API Environment:**
- Discord REST API base URL: `https://discord.com/api/v10`
- Gateway WebSocket URL: Dynamically obtained via `GET /gateway/bot`, typically `wss://gateway.discord.gg/?v=10&encoding=json`

## Supported Message Sending Types

All sending methods are implemented using a fluent syntax, for example:
```python
from ErisPulse.Core import adapter
discord = adapter.get("discord")

await discord.Send.To("group", channel_id).Text("Hello World!")
```

The supported sending types include:
- `.Text(text: str)`: Sends a plain text message.
- `.Embed(embed: dict | list)`: Sends an Embed message, supporting single or multiple Embeds.
- `.Image(file: bytes | str, filename: str = "image.png")`: Sends an image, supporting binary data or URL.
- `.File(file: bytes | str, filename: str = None)`: Sends a file, supporting binary data or URL.
- `.Reply(content: str, message_id: str)`: Replies to a specified message (convenient terminal method).
- `.Raw_ob12(message: List[Dict], **kwargs)`: Sends a OneBot12 formatted message.
- `.Raw_json(json_str: str)`: Sends arbitrary Discord API request JSON.

### Fluent Modifier Methods (Combinable)

Fluent modifier methods return `self`, allowing for chained calls, which must be called before the final sending method:

- `.Reply(message_id: str)`: Replies (references) to a specified message, setting `message_reference`.
- `.At(user_id: str)`: Mentions a specified user, converting to `<@user_id>`, can be called multiple times.
- `.AtAll()`: Mentions everyone, converting to `@everyone`.

### Fluent Call Examples

```python
# Basic sending
await discord.Send.To("group", channel_id).Text("Hello")

# Reply to a message
await discord.Send.To("group", channel_id).Reply(msg_id).Text("Reply message")

# Convenient reply (one-step)
await discord.Send.To("group", channel_id).Reply("Reply content", msg_id)

# Mention a user
await discord.Send.To("group", channel_id).At("user_id").Text("Hello")

# Mention multiple users
await discord.Send.To("group", channel_id).At("user1").At("user2").Text("Multiple users @")

# Mention everyone
await discord.Send.To("group", channel_id).AtAll().Text("Announcement")

# Combinable usage
await discord.Send.To("group", channel_id).Reply(msg_id).At("user_id").Text("Composite message")

# Embed message
embed = {
    "title": "Notice",
    "description": "This is an embedded message",
    "color": 5814783,
    "fields": [{"name": "Field", "value": "Value", "inline": True}],
}
await discord.Send.To("group", channel_id).Embed(embed)

# Send an image
await discord.Send.To("group", channel_id).Image("https://example.com/image.png")
```

### Private Message Sending

When sending private messages, the adapter automatically creates a DM channel:

```python
# Send a private message
await discord.Send.To("user", user_id).Text("Private message content")
await discord.Send.To("user", user_id).Embed(embed)
```

### Message Operations

```python
# Recall a message
await discord.Send.To("group", channel_id).Recall(msg_id)

# OneBot12 format
ob12_msg = [
    {"type": "text", "data": {"text": "Hello "}},
    {"type": "mention", "data": {"user_id": "user_id"}},
]
await discord.Send.To("group", channel_id).Raw_ob12(ob12_msg)
```

## Return Values of Send Methods

All send methods return a Task object, which can be awaited directly to obtain the send result. The returned result follows the ErisPulse adapter's standardized return specification:

```python
{
    "status": "ok",           // Execution status: "ok" or "failed"
    "retcode": 0,             // Return code (0 means success)
    "data": {...},            // Original Discord API response
    "message_id": "xxx",      // Message ID (when sending a message)
    "message": "",            // Error message
    "discord_raw": {...}      // Raw response data
}
```

### Error Code Description

| retcode | Description |
|---------|-------------|
| 0 | Success |
| 33001 | Network error (connection failed, timeout, etc.) |
| 34000 | Discord API returned error (insufficient permissions, parameter error, etc.) |

## Unique Event Types

Use `platform == "discord"` to detect and use platform-specific features.

### Core Differences

1. **Server/Channel System**: Discord uses a two-layer structure of servers (Guilds) and channels (Channels), where channels are the basic targets for message sending.
2. **Gateway Events**: All events are received through the WebSocket Gateway using the Opcode + Dispatch mechanism.
3. **Intents Subscription**: Events are subscribed using bitmasks, and `MESSAGE_CONTENT` requires Privileged permissions.
4. **Message Segment Types**: Supports text, images, files, videos, audio, Embed, Sticker, and other message segments.
5. **Mention Format**: Discord uses the `<@user_id>` format to indicate user mentions.

### Extended Fields

All unique fields are prefixed with `discord_`:
- `discord_raw`: Raw Discord event data
- `discord_raw_type`: Raw event type name (e.g., `MESSAGE_CREATE`)
- `discord_guild_id`: Server ID
- `discord_channel_id`: Channel ID

### detail_type Mapping

| Discord Scenario | detail_type | Description |
|---|---|---|
| Channel Message | `channel` | ErisPulse extended type |
| Private Message (DM) | `private` | OneBot12 standard type |

### Event Type Mapping

| Discord Event | OneBot12 type | detail_type | Description |
|---|---|---|---|
| MESSAGE_CREATE | message | channel/private | Message creation |
| MESSAGE_UPDATE | message | channel/private | Message editing |
| MESSAGE_DELETE | notice | group_message_delete / private_message_delete | Message deletion |
| GUILD_MEMBER_ADD | notice | group_member_increase | Member joining |
| GUILD_MEMBER_REMOVE | notice | group_member_decrease | Member leaving |
| GUILD_MEMBER_UPDATE | notice | group_member_update | Member information update |
| GUILD_ROLE_CREATE | notice | group_role_create | Role creation |
| GUILD_ROLE_DELETE | notice | group_role_delete | Role deletion |
| CHANNEL_CREATE | notice | channel_create | Channel creation |
| CHANNEL_DELETE | notice | channel_delete | Channel deletion |
| INTERACTION_CREATE | request | interaction | Interaction (buttons, commands, etc.) |

### Special Field Examples

```python
# Channel text message
{
  "type": "message",
  "detail_type": "channel",
  "user_id": "sender ID",
  "user_nickname": "username",
  "group_id": "channel ID",
  "message_id": "message ID",
  "discord_raw": {...},
  "discord_raw_type": "MESSAGE_CREATE",
  "discord_guild_id": "server ID",
  "discord_channel_id": "channel ID",
  "message": [
    {"type": "text", "data": {"text": "Hello"}}
  ],
  "alt_message": "Hello"
}

# Private message
{
  "type": "message",
  "detail_type": "private",
  "user_id": "sender ID",
  "user_nickname": "username",
  "message_id": "message ID",
  "discord_raw": {...},
  "discord_raw_type": "MESSAGE_CREATE",
  "discord_channel_id": "DM channel ID",
  "message": [
    {"type": "text", "data": {"text": "private message content"}}
  ],
  "alt_message": "private message content"
}

# Message with Embed
{
  "type": "message",
  "detail_type": "channel",
  "message": [
    {"type": "discord_embed", "data": {"embed": {...}}}
  ],
  "alt_message": "[Embedded message]"
}

# Message with attachment
{
  "type": "message",
  "detail_type": "channel",
  "message": [
    {"type": "text", "data": {"text": "Look at this image"}},
    {"type": "image", "data": {"file": "image URL", "url": "image URL", "file_name": "image.png"}}
  ],
  "alt_message": "Look at this image[Image]"
}
```

### Message Segment Types

Discord message content is automatically converted into corresponding message segments based on the `content`, `attachments`, and `embeds` fields:

| Source | Conversion Type | Description |
|---|---|---|
| content text | `text` | Pure text content |
| content `<@id>` | `mention` | User mention |
| content `<@&id>` | `discord_role_mention` | Role mention |
| content `<#id>` | `discord_channel_mention` | Channel mention |
| attachments (image/*) | `image` | Image attachment |
| attachments (video/*) | `video` | Video attachment |
| attachments (audio/*) | `audio` | Audio attachment |
| attachments (other) | `file` | File attachment |
| embeds | `discord_embed` | Embedded message |
| sticker_items | `discord_sticker` | Sticker |

### discord_embed Message Segment

```json
{
  "type": "discord_embed",
  "data": {
    "embed": {
      "title": "Title",
      "description": "Description",
      "color": 12345,
      "fields": [...],
      "image": {"url": "..."},
      "thumbnail": {"url": "..."},
      "footer": {"text": "..."}
    }
  }
}
```

## Gateway Connection

### Connection Flow

1. Call `GET /gateway/bot` to get the WebSocket gateway URL
2. Connect to `wss://gateway.discord.gg/?v=10&encoding=json`
3. Receive opcode 10 HELLO: contains `heartbeat_interval`
4. Send opcode 2 IDENTIFY: includes token, intents, and properties
5. Begin heartbeat loop: send opcode 1 Heartbeat at intervals of `heartbeat_interval`
6. Receive opcode 0 Dispatch: event dispatch (`t`=event name, `s`=sequence number, `d`=data)
7. Receive opcode 11 Heartbeat ACK: heartbeat acknowledgment

### Opcode Description

| Opcode | Name | Direction | Description |
|--------|------|-----------|-------------|
| 0 | Dispatch | Receive | Event dispatch (includes `t`, `s`, `d` fields) |
| 1 | Heartbeat | Send/Receive | Heartbeat (includes last seq) |
| 2 | Identify | Send | Identity authentication |
| 6 | Resume | Send | Resume session |
| 7 | Reconnect | Receive | Server requests reconnection |
| 9 | Invalid Session | Receive | Invalid session |
| 10 | Hello | Receive | Connection handshake (includes heartbeat_interval) |
| 11 | Heartbeat ACK | Receive | Heartbeat acknowledgment |

### Disconnection Reconnection and RESUME

- After disconnection, the adapter automatically retries the connection
- If a `session_id` exists, attempt to RESUME (opcode 6) the session first
- RESUME includes `token`, `session_id`, and the last `seq`, restoring missed events after resumption
- When opcode 7 (Reconnect) is received, maintain session state and reconnect
- When opcode 9 (Invalid Session) is received with `d=false`, clear the session and re-IDENTIFY

### Heartbeat Mechanism

- After receiving HELLO, wait `heartbeat_interval * random()` milliseconds before sending the first heartbeat
- Subsequently, send a heartbeat every `heartbeat_interval` milliseconds
- Heartbeats include the last `seq` value (opcode 1, `d: seq`)
- If no ACK (opcode 11) is received within `heartbeat_interval` after sending a heartbeat, treat it as a connection failure and reconnect

## Usage Examples

### Handling Channel Messages

```python
from ErisPulse.Core.Event import message
from ErisPulse import sdk

discord = sdk.adapter.get("discord")

@message.on_message()
async def handle_group_msg(event):
    if event.get("platform") != "discord":
        return

    text = event.get_text()
    channel_id = event.get("group_id")

    if text == "hello":
        await discord.Send.To("group", channel_id).Text("Hello!")
```

### Handling Direct Messages

```python
@message.on_message()
async def handle_private_msg(event):
    if event.get("platform") != "discord":
        return
    if not event.is_dm():
        return

    text = event.get_text()
    user_id = event.get("user_id")

    await discord.Send.To("user", user_id).Text(f"You said: {text}")
```

### Sending Embed Messages

```python
embed = {
    "title": "Server Announcement",
    "description": "Welcome to use ErisPulse Discord adapter",
    "color": 3447003,
    "fields": [
        {"name": "Version", "value": "4.0.0", "inline": True},
        {"name": "Framework", "value": "ErisPulse", "inline": True},
    ],
    "footer": {"text": "Powered by ErisPulse"},
    "timestamp": "2025-01-01T00:00:00.000Z",
}
await discord.Send.To("group", channel_id).Embed(embed)
```

### Using Discord-Specific Methods

```python
@message.on_message()
async def handle(event):
    if event.get("platform") != "discord":
        return

    channel_id = event.get_channel_id()
    guild_id = event.get_guild_id()
    is_dm = event.is_dm()
    embeds = event.get_embeds()
    attachments = event.get_attachments()

    if embeds:
        await discord.Send.To("group", channel_id).Text(
            f"Received {len(embeds)} embeds"
        )
```

### Handling Interaction Events

```python
from ErisPulse.Core.Event import request

@request.on_request()
async def handle_interaction(event):
    if event.get("platform") != "discord":
        return

    interaction = event.get_interaction_data()
    if interaction.get("type") == 3:  # MESSAGE_COMPONENT
        await event.reply("Button clicked!")
```



### Webhook 适配

# Platform Feature Description — Webhook Generic Bridge Adapter

This document provides a detailed explanation of the bidirectional bridge protocol, field mapping, and implementation features of the Webhook adapter.

## Overview

The Webhook adapter is a **protocol-level bridge**, not bound to any specific platform. It exchanges messages via HTTP, enabling any system capable of initiating HTTP requests to connect to ErisPulse.

```
Inbound direction                             Outbound direction
────────                                ────────
External System                                ErisPulse Module
   │                                       │
   │ POST JSON                             │ Send.Text(...)
   ▼                                       ▼
┌──────────────────────────────────────────────────┐
│              WebhookAdapter                       │
│  ┌──────────────────┐   ┌──────────────────┐    │
│  │ Inbound Routes   │   │ Outbound Forward │    │
│  │ GET  (Health Check)│   │ client.post()    │    │
│  │ POST (Receive Event)│   │ → outgoing_url   │    │
│  └────────┬─────────┘   └────────▲─────────┘    │
│           │                      │               │
│           ▼                      │               │
│  ┌──────────────────┐   ┌──────────────────┐    │
│  │ WebhookConverter │   │ Send Class       │    │
│  │ JSON → OneBot12  │   │ Message Segment → JSON │    │
│  └────────┬─────────┘   └────────▲─────────┘    │
└───────────┼──────────────────────┼───────────────┘
            ▼                      │
     adapter.emit(event)    call_api("send_message")
            │                      │
            ▼                      │
       ErisPulse Event System ◄────────┘
```

## Multi-Account Model

Each account is an independent bridge configuration, isolated from others:

| Account | bot_id | callback_path | outgoing_url | secret |
|---------|--------|---------------|--------------|--------|
| `default` | `webhook_bot` | `/webhook/default` | `https://a.com/recv` | `key1` |
| `discord` | `discord_bot` | `/webhook/discord` | `https://b.com/send` | `key2` |

Each account registers routes independently and emits connect events separately upon startup.

## Inbound Protocol

### 1. Health Check (GET)

- **Path**: `{callback_path}`
- **Method**: `GET`
- **Authentication**: None
- **Response**:

```json
{"status": "ok", "account": "default"}
```

### 2. Receive Event (POST)

- **Path**: `{callback_path}`
- **Method**: `POST`
- **Content-Type**: `application/json`
- **Authentication** (when secret is configured): Header `X-Webhook-Secret` or Query `?secret=`

#### Request Body

```json
{
  "user_id": "u123",
  "user_nickname": "用户名",
  "group_id": "群组ID（仅群组会话）",
  "detail_type": "private",
  "message": [
    {"type": "text", "data": {"text": "消息内容"}}
  ],
  "raw": {}
}
```

| Field | Required | Description |
|-------|----------|-------------|
| `user_id` | Yes | Sender ID |
| `user_nickname` | No | Sender nickname |
| `group_id` | No | Group/channel ID (provided for group conversations) |
| `detail_type` | No | Conversation type (`private`/`group`), defaults to account default |
| `message` | Yes | Array of OneBot12 message segments |
| `raw` | No | Raw data, stored as `webhook_raw` |

#### Response

```json
{"status": "ok"}
```

Error responses include HTTP status codes:

| Status Code | Meaning |
|-------------|---------|
| 400 | Invalid JSON / body is not an object |
| 401 | Authentication failed |
| 404 | Unknown account |
| 500 | Event dispatch failed |

### 3. Field Mapping (Inbound JSON → OneBot12 Event)

| Inbound JSON | OneBot12 Event Field | Description |
|--------------|----------------------|-------------|
| — | `id` | Auto-generated |
| — | `time` | Current Unix timestamp (seconds) |
| — | `type` | Fixed as `message` |
| `detail_type` | `detail_type` | Defaults to account default value |
| — | `platform` | Fixed as `webhook` |
| — | `self.platform` | Fixed as `webhook` |
| — | `self.user_id` | Account `bot_id` |
| `user_id` | `user_id` | Passthrough |
| `user_nickname` | `user_nickname` | Passthrough (optional) |
| `group_id` | `group_id` | Passthrough (optional) |
| `message` | `message` | Passthrough |
| Full body | `webhook_raw` | Original request |
| Account name | `webhook_account` | Name of the account that generated the event |
| `type` or `message` | `webhook_raw_type` | Original event type |

## Outbound Protocol

### 1. Send Message

When a module calls methods like `Send.To(...).Text(...)`, the adapter sends a POST request to `outgoing_url`:

- **Method**: `POST`
- **Content-Type**: `application/json`
- **Authentication Header** (when secret is configured): `X-Webhook-Secret: {secret}`

#### Request Body

```json
{
  "target_type": "private",
  "target_id": "target_user_id",
  "account": "default",
  "message": [
    {"type": "text", "data": {"text": "消息内容"}}
  ],
  "timestamp": 1700000000
}
```

| Field | Description |
|-------|-------------|
| `target_type` | Target type (from `Send.To(type, id)`), defaults to account default |
| `target_id` | Target ID (from `Send.To`) |
| `account` | Sending account name |
| `message` | Array of OneBot12 message segments |
| `timestamp` | Send timestamp (seconds) |

### 2. Response Standardization

The adapter standardizes the response from the outbound target into ErisPulse's standard response format:

```json
{
  "status": "ok",
  "retcode": 0,
  "data": {"message_id": "...", ...},
  "message_id": "...",
  "message": "",
  "webhook_raw": {}
}
```

The message ID is extracted from the `message_id` field of the target's JSON response. If the target does not return `message_id`, it is set to an empty string.

On request failure, an error response is returned (`status: "failed"`, `retcode: 33001`).

## Send Methods

| Method | Description |
|--------|-------------|
| `Text(text)` | Send text, wrapped as `[{"type":"text","data":{"text":text}}]` |
| `Image(file)` | Send image, wrapped as `[{"type":"image","data":{"file":file}}]` |
| `Raw_ob12(message)` | Send raw OneBot12 message segments |
| `Json(data)` | Pass-through raw JSON, wrapped as `[{"type":"json","data":{"raw":data}}]` |

`At` / `AtAll` / `Reply` modifiers are provided by the framework base class and merged into message segments via `_apply_modifiers`.

## Event Extension Methods (WebhookEventMixin)

| Method | Description |
|--------|-------------|
| `get_raw_data()` | Get the original request body (`webhook_raw`) |
| `get_detail_type()` | Get the conversation type |
| `get_webhook_account()` | Get the account name that generated the event |

## Feature Matrix

| Feature | Support Status |
|---------|----------------|
| Multi-account | ✅ Each account bridges independently |
| Inbound Authentication | ✅ Header / Query dual mode |
| Health Check | ✅ GET returns status |
| Outbound Authentication | ✅ Header carries secret |
| OneBot12 Standard Event | ✅ Full standard fields |
| Meta Events | ✅ connect / disconnect |
| Route Discovery | ✅ Registered to `webhook` namespace |
| WebSocket | ❌ Only HTTP |
| Media Upload | ❌ Media is passed via URL, not binary data |

## Notes

1. **Unidirectional Outbound**: If `outgoing_url` is empty, the account only receives inbound messages, and send operations will return an error.
2. **Secret Security**: `secret` is stored in configuration as encrypted metadata (metadata secret), and HTTPS is recommended for transmission.
3. **Path Uniqueness**: `callback_path` for multiple accounts must be unique to avoid routing conflicts.
4. **Idempotency**: The adapter does not guarantee deduplication of inbound events; external systems should handle retries themselves.
5. **Timeout**: Outbound requests use ErisPulse's built-in `client` and inherit global timeout settings.



### 微信公众号适配

# WechatMp Adapter - Platform Features Documentation



## Basic Information
- Module Name: `ErisPulse-WechatMpAdapter`
- Platform Identifier: `mp` (alias: `wechat_mp`)
- Module Version: 4.1.0
- Maintainer: ErisPulse
- Dependencies: `cryptography`



## Supported Message Types

| Method | Description | WeChat API |
|--------|-------------|------------|
| `Text(text)` | Send text | Customer Service Message `message/custom/send` |
| `Image(file)` | Send image (automatically uploads and gets media_id) | Customer Service Message + `media/upload` |
| `Voice(file)` | Send voice (automatically uploads and gets media_id) | Customer Service Message + `media/upload` |
| `Video(file, title, description)` | Send video (automatically uploads and gets media_id) | Customer Service Message + `media/upload` |
| `Music(url, title, description, ...)` | Send music | Customer Service Message |
| `News(articles)` | Send news article message | Customer Service Message |
| `Template(template_id, data, url)` | Send template message | `message/template/send` |
| `Menu(head_content, list, tail_content)` | Send menu message | Customer Service Message `msgmenu` |
| `Raw_ob12(message)` | Send OneBot12 standard message segment | - |

### Media File Notes
- Supports three parameter types:
  - `str` URL (starts with `http://` or `https://`): automatically downloads and uploads
  - `str` local file path: automatically reads and uploads
  - `bytes` binary data: directly uploads
  - `str` media_id: with `media:` prefix, can directly reuse an already uploaded media_id
- After upload, a temporary material `media_id` is obtained, valid for 3 days

### Important Limitations
- Customer Service Messages can only be actively sent within **48 hours** after user interaction with the public account
- After 48 hours, use template messages (requires user-authorized scenarios)
- Unverified service accounts (`verified=false`) cannot send messages proactively; they can only respond passively (see "Verified Service Account and Passive Reply" above)

## Event Types

### Message Events (message)
All user messages have `detail_type: private` (WeChat Official Account 1v1 scenario).

| WeChat MsgType | Message Segment Type | Description |
|----------------|----------------------|-------------|
| `text` | `text` | Text message |
| `image` | `image` | Image message |
| `voice` | `voice` | Voice message (includes voice recognition result) |
| `video` | `video` | Video message |
| `shortvideo` | `video` | Short video (marked with `mp_shortvideo`) |
| `location` | `location` | Location message |
| `link` | `text` | Link message (converted to text) |

### Notification Events (notice)
Events are distinguished by the `mp_event` field.

| WeChat Event | `mp_event` | Description |
|--------------|------------|-------------|
| `subscribe` | `subscribe` | Subscribe to official account |
| `unsubscribe` | `unsubscribe` | Unsubscribe from official account |
| `SCAN` | `scan` | Scan a QR code with parameters |
| `LOCATION` | `location_report` | Report location |
| `CLICK` | `menu_click` | Click custom menu |
| `VIEW` | `menu_view` | Navigate menu link |
| `TEMPLATESENDJOBFINISH` | `template_send_finish` | Template message sending result |
| `MASSSENDJOBFINISH` | `mass_send_finish` | Mass message sending result |

## Platform Extension Fields

WeChat-specific fields (with `mp_` prefix) in the event object:

| Field | Type | Description |
|------|------|------|
| `mp_raw` | str | Original XML data |
| `mp_raw_type` | str | Original message/event type |
| `mp_msg_id` | str | WeChat message ID |
| `mp_event` | str | Event type (only for event notifications) |
| `mp_event_key` | str | Event Key (for menu clicks, scanning QR codes, etc.) |
| `mp_to_user` | str | Receiver's WeChat ID (official account original ID) |
| `mp_from_user` | str | Sender's OpenID |
| `mp_data` | dict | Parsed XML dictionary data |


## Event Extension Methods

Registered via `register_event_mixin("mp", ...)`, these methods can be directly called on event objects:

| Method | Return Value | Description |
|--------|--------------|-------------|
| `get_openid()` | str | Sender's OpenID |
| `get_msg_type()` | str | Original WeChat message type |
| `get_event()` | str | Event type (only for event notifications) |
| `get_content()` | str | Plain text content of the message |
| `get_raw_xml()` | str | Raw XML data |


## Configuration Options

### Multi-account Configuration

Each account corresponds to a WeChat Official Account:

```toml
[WechatMpAdapter.accounts.main]
appid = "wx1234567890abcdef"
appsecret = "your_app_secret_here"
token = "your_callback_token"
encoding_aes_key = ""                    # Required for secure/compatibility mode (43 characters)
callback_path = "/mp/main"               # Callback path
verified = true                          # Whether it is a verified service account (affects active sending capability)
enable = true

[WechatMpAdapter.accounts.secondary]
appid = "wx0987654321fedcba"
appsecret = "another_app_secret"
token = "another_callback_token"
callback_path = "/mp/secondary"
enable = true
```

### Configuration Field Descriptions

| Field | Required | Description |
|-------|----------|-------------|
| `appid` | Yes | Official Account AppID |
| `appsecret` | Yes | Official Account AppSecret (secret) |
| `token` | No | Callback verification Token (recommended to enable signature verification) |
| `encoding_aes_key` | No | Message encryption/decryption key (43 characters, required for secure mode) |
| `callback_path` | No | Callback path template, default `/mp/{account}`, where `{account}` will be replaced by the account name |
| `verified` | No | Whether it is a **verified service account**, default `true` (see below for details) |
| `enable` | No | Whether to enable, default true |

### Verified Service Account and Passive Response (`verified`)

- `verified = true` (default, verified service account): Can use **customer service messages** for active push (within a 48-hour window) and template messages at any time.
- `verified = false` (unverified subscription account):
  - Customer service messages / template messages **can only be sent within the webhook passive response context** (within 15 seconds after receiving a user message, one-time reply) — the adapter will automatically intercept and treat the sending as a passive response.
  - Active push (e.g., scheduled tasks) returns `retcode=34003` error.

## Encryption Mode Description

WeChat Official Accounts provide three message encryption and decryption modes:

| Mode | Description | encoding_aes_key | Validation Field |
|------|-------------|------------------|------------------|
| Plaintext Mode | XML transmitted in plaintext | Not required | `signature` |
| Compatible Mode | Both plaintext and ciphertext exist | Optional | `signature` / `msg_signature` |
| Secure Mode | Fully encrypted | Required | `msg_signature` |

This adapter automatically handles:
- Plaintext Mode: Validates `signature`, directly parses XML
- Secure/Compatible Mode: Detects the `Encrypt` field, validates `msg_signature`, and uses AES-256-CBC decryption
- Decryption depends on the `cryptography` library (declared in dependencies)

Please return the translated content directly, without any additional text.


## Callback Routes

The adapter registers two routes (GET + POST) for each enabled account:

- **GET**: WeChat server verification, returns `echostr` after signature verification
- **POST**: Receive user messages and events, verify signature → decrypt (if needed) → transform → emit

The actual access path automatically adds the module prefix. For example, if the registered path is `/mp/main`, the actual access paths are `/mp_{account}_verify/mp/main` and `/mp_{account}_message/mp/main`.



## API Response

All `call_api` calls return a standardized response:

- Success: `status: "ok"`, `retcode: 0`
- Failure: `status: "failed"`, `retcode: 34000+errcode`
- Always includes `mp_raw` (raw response), `message_id`



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

