以下是 ErisPulse SDK 适配器开发文档（知识库）。请基于文档内容回答；
文档未覆盖的 API 以 SDK 源码 docstring 为准，不要编造不存在的接口或行为。


---



=================
ErisPulse 适配器开发指南
=================




====
框架理解
====


### 架构概览

# Architecture Overview

> [!TIP]
> **When to read this**: When you want to understand what the framework is doing behind the scenes—how a message flows, the order in which modules are initialized, what happens during hot reload, or when troubleshooting "why the framework behaves this way." If you only want to write handlers, see [Getting Started with Event Handling](getting-started/event-handling.md); otherwise, skip this.

A message from a user to a bot reply goes through several stages: adapter transformation, middleware, scope filtering, and priority-based scheduling. Modules are not all loaded at startup. This article uses diagrams to clearly illustrate this chain and explain what you can intervene at each stage.

## SDK Core Architecture

The following diagram shows the core modules of the SDK and their relationships:

```mermaid
graph TB
    SDK["sdk<br/>Unified Entry Point"]

    SDK --> Event["Event<br/>Event System"]
    SDK --> Lifecycle["Lifecycle<br/>Lifecycle Management"]
    SDK --> Logger["Logger<br/>Logging Management"]
    SDK --> Storage["Storage / env<br/>Storage Management"]
    SDK --> Config["Config<br/>Configuration Management"]
    SDK --> AdapterMgr["Adapter<br/>Adapter Management"]
    SDK --> ModuleMgr["Module<br/>Module Management"]
    SDK --> Router["Router<br/>Routing Management"]
    SDK --> Client["Client<br/>HTTP Client"]
    Event --> Command["command"]
    Event --> Message["message"]
    Event --> Notice["notice"]
    Event --> Request["request"]
    Event --> Meta["meta"]
    Event --> Conversation["Conversation<br/>Branch + Persistence"]

    AdapterMgr --> BaseAdapter["BaseAdapter"]
    BaseAdapter --> P1["Yunhu"]
    BaseAdapter --> P2["Telegram"]
    BaseAdapter --> P3["OneBot11/12"]
    BaseAdapter --> PN["..."]

    ModuleMgr --> BaseModule["BaseModule"]
    BaseModule --> CM["Custom Module"]

    BaseAdapter -.-> SendDSL["SendDSL<br/>Message Sending"]
```

### Core Module Description

| Module | Description |
|--------|-------------|
| **Event** | Event system, providing five types of event handling: command / message / notice / request / meta, and Conversation for multi-turn dialogue |
| **Adapter** | Adapter manager, managing registration, startup, and shutdown of multi-platform adapters |
| **Module** | Module manager, managing plugin registration, loading, and unloading, supporting dependency declaration and topological sorting |
| **Lifecycle** | Lifecycle manager, providing event-driven lifecycle hooks |
| **Storage** | SQLite-based key-value storage system, supporting generic SQL chain query |
| **Config** | TOML-formatted configuration file management |
| **Logger** | Modular logging system, supporting sub-loggers |
| **Router** | HTTP/WebSocket routing management, encapsulating underlying backends (currently FastAPI + Uvicorn) through an abstraction layer, supporting decorator routing, middleware, grouping, rate limiting, CORS |
| **Client** | Unified HTTP/WS client (previously `HttpClient` before 2.8.0, retains compatibility alias), encapsulating underlying request libraries (currently aiohttp) through an abstraction layer, providing request statistics, retry, logging, WebSocket client, ErisPulse exception system, etc. The client and server-side WebSocket share the `WebSocketConnectionBase` base class |

## Initialization Process

The following diagram shows the complete initialization process of `sdk.init()`:

```mermaid
flowchart TD
    A["sdk.init()"] --> B["Prepare Runtime Environment"]
    B --> B1["Load Configuration File"]
    B1 --> B2["Set Global Exception Handler"]
    B2 --> C["Adapter & Module Discovery"]
    C --> D{"Parallel Loading"}
    D --> D1["Load Adapter from PyPI"]
    D --> D2["Load Module from PyPI"]
    D1 & D2 --> E["Register Adapter"]
    E --> E1["Start Adapter"]
    E1 --> F["Register Module"]
    F --> F1{"Dependency Validation"}
    F1 -->|"Missing Dependency"| F2["Skip Module and Log Warning"]
    F1 -->|"Dependency Satisfied"| F3["Topological Sorting<br/>(Kahn Algorithm + Priority)"]
    F3 --> G["Initialize Modules in Order<br/>(Instantiation + on_load)"]
    F2 --> G
    G --> H["Start Router Server"]
    H --> K["Ready to Run"]
```

### Detailed Initialization Stages

> The complete initialization chain breakdown (Finder / Loader / Manager / Router), underlying entry points (`init()` / `init_task()` / `init_sync()`), and manual full startup are detailed in [Startup Process and Manual Control](advanced/startup.md).

## Event Handling Process

The following diagram shows the complete flow of messages from the platform to the handler:

```mermaid
flowchart LR
    A["Platform Raw Message"] --> B["Adapter Receives"]
    B --> C["Convert to OneBot12 Standard"]
    C --> D["adapter.emit()"]
    D --> E["Execute Middleware Chain"]
    E --> F{"Event Dispatching"}
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

The above diagram shows the result; below, we break down what the framework does behind `adapter.emit()`—this is a three-layer dispatch chain:

```mermaid
sequenceDiagram
    participant P as Platform
    participant A as Adapter Bus Layer<br/>AdapterManager.emit
    participant T as Handler Task Layer<br/>_dispatch_handler_task
    participant E as Event Module Layer<br/>_process_event

    P->>A: Raw Event
    A->>A: Extract platform/type/detail_type + raw fields
    A->>A: [Recv] Receive Log
    A->>A: lifecycle.adapter.event.receive (earliest hook)
    A->>A: Process self field (meta branch / Bot auto-registration)
    A->>A: Middleware Chain (serial, event data can be rewritten)
    A->>A: Collect Handlers (specific type + wildcard *)
    A->>A: Identity Access + Scope Filtering (before Task creation, silently discard/skip)
    A->>T: asyncio.create_task (fire-and-forget)
    A->>A: lifecycle.adapter.event.dispatched (latest hook)
    T->>T: Get Concurrent Semaphore (default limit 64)
    T->>E: Call Event Module-registered Handlers
    E->>E: lifecycle.event.pre_process
    E->>E: ignore_self (message events default ignore self)
    E->>E: Group by Priority: High→Low, serial between groups, concurrent within groups
    E->>E: Execute within group + field merge (conflict warning)
    E->>E: Post-group check stop() to block lower priority
    T->>T: Slow Log (warning if > 1s, wait_reply time whitelist)
```

**What the framework does at each step and what you can intervene:**

| Stage | What the framework does | What you can intervene |
|-------|-------------------------|------------------------|
| Receive | Extract standard fields, preserve `{platform}_raw` raw data; write `[Recv]` log | Listen to `adapter.event.receive` to get earliest event |
| self field | Meta event goes through connect/disconnect/heartbeat branch; normal event auto-registers Bot and triggers `adapter.bot.online` | Listen to `adapter.bot.online` / `bot.offline` |
| Middleware | **Serial** execution, if returned value is not None, replace event data | Register middleware to rewrite/intercept event |
| Dispatch Collection | First get specific type handler, then get `*` wildcard handler | — |
| Identity Dimension | At dispatch entry, decide whether to receive event by User>Session>Bot>Adapter (`scope.is_identity_allowed`), **discard entire event if denied** | `ErisPulse.scope.identity` binding |
| Scope Filtering | Determine `scope.is_allowed` by module owner (session level > Bot level > platform level), **silently skip if not passed** | Configure scope whitelist/blacklist |
| Scheduling | Each matching handler gets independent `asyncio.Task`, `emit()` **returns immediately without waiting for handler completion** | — |
| Priority | High priority group executes first; **serial between groups, concurrent within groups** (each group holds event copy, changes merged back, conflicts warn) | `@command(..., priority=N)` / specify priority during registration |
| Blocking | After each group, check `event.is_stopped()`, if triggered, **do not execute lower priority** | `event.mark_processed(stop=True)` / `event.done()` |

> **Common Misunderstandings**:
> 1. **Scope filtering is silent**—filtered handlers do not report errors or respond, only visible in TRACE-level logs (`core.scope.denied`). If "my module didn't receive a message," first check scope binding.
> 2. **Handlers are inherently concurrent**—the framework already creates independent Tasks for each handler, you **do not need** to wrap them in `asyncio.create_task` again.
> 3. **No blocking within the same priority group**—`mark_processed(stop=True)` only blocks lower priority groups, not already concurrent handlers within the same group.
> 4. **Slow log threshold is fixed at 1 second**—handlers taking over 1s will be warned in logs (`wait_reply` time is excluded from duration), but execution is not interrupted.

> Details on scope's module-level three-tier binding, identity-level access and outbound action restrictions are in [Scope (scope)](advanced/scope.md); event scope text filtering and command user ACL are in [Event Handling Introduction](getting-started/event-handling.md); concurrency limit configuration is in [Configuration Guide](user-guide/configuration.md#Framework Configuration).

## Lifecycle Events

The following diagram shows the order in which lifecycle events are triggered by the framework components:

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

> The complete event listening methods (`lifecycle.on()` / `once()` / `has_handlers()`), all lifecycle event lists and data formats are detailed in [Lifecycle Management](advanced/lifecycle.md).

## Module Loading Strategy

ErisPulse supports three module loading strategies, declared by `get_load_strategy()` returning a `ModuleLoadStrategy`:

```mermaid
flowchart TD
    A["Module Registered to ModuleManager"] --> B{"Load Strategy"}
    B -->|"lazy_load = true<br/>+ activate_on declared"| C["Create ModuleActivator Proxy"]
    B -->|"lazy_load = true<br/>No activate_on"| D["Create LazyModule Proxy"]
    B -->|"lazy_load = false"| E["Create Instance Immediately"]
    C --> F["Register Event/Command stub to Dispatcher"]
    F --> G["Mount to sdk Attribute"]
    G --> H["Event Arrival Triggers Activation"]
    H --> I["Instantiate + on_load() + Unregister stub"]
    D --> J["Mount to sdk Attribute"]
    J --> K["Initialize on First Attribute Access"]
    E --> L["Call on_load()"]
    L --> M["Mount to sdk Attribute"]
```

> For more details, see [Lazy Loading System](advanced/lazy-loading.md), [Lifecycle Management](advanced/lifecycle.md), and module documentation.

### Event-Driven Lazy Activation (`activate_on`) Trigger Architecture

> [!NOTE]
> This feature requires ErisPulse **2.8.0+**.

`activate_on` allows modules to load only when the **first matching event/command arrives**, avoiding constant memory usage while ensuring no events are lost:

```mermaid
flowchart LR
    subgraph Declare["Module Declaration"]
        S1["get_load_strategy() returns<br/>ModuleLoadStrategy(activate_on=...)"] --> S2["activate_on Syntax:<br/>str / dict / list freely mixed"]
        S2 --> S2a["'message' → Event Type Level"]
        S2 --> S2b["{'notice': 'group_member_increase'}<br/>→ Type + detail_type"]
        S2 --> S2c["{'command': 'roll'}<br/>→ Command Trigger (short/long list)"]
        S2 --> S2d["{'command': {'name': 'dice', 'help': ...,<br/>'aliases': [...], 'hidden': ...}}<br/>→ Command Trigger (dict declaration)"]
    end

    subgraph Runtime["Runtime"]
        R1["ModuleActivator Registers stub"] --> R1a["Event stub → message/notice/request/meta manager<br/>priority ACTIVATION_STUB_PRIORITY (very low)"]
        R1 --> R1b["Command stub → Command Manager<br/>Placeholder command (mirrors help/usage/group/aliases/hidden in dict declaration)"]
        R1a --> R2{"Trigger Event Arrives"}
        R1b --> R2
        R2 --> R3["Filter by owner scope"]
        R3 --> R4["asyncio.Lock to prevent duplicate activation"]
        R4 --> R5["Instantiate module + call on_load()"]
        R5 --> R6["Unregister all stubs"]
        R6 --> R7["Event Forwarded to Real Handler"]
    end

    Declare --> Runtime
```

**Trigger Semantics Key Points:**

> The complete `activate_on` syntax (str / dict / list), command dict declaration, placeholder command help fallback chain, scope filtering, and failure semantics are in [Lazy Loading System](advanced/lazy-loading.md#Event-Driven-Lazy-Activation-activate_on).

## Local Plugin Folder Architecture

> [!NOTE]
> This feature requires ErisPulse **2.8.0+**.

Local plugins (`plugins/` directory) do not require packaging for release; the framework automatically discovers and loads them at startup:

```mermaid
flowchart TD
    A["Project plugins/ Directory<br/>(ErisPulse.framework.plugins_dir, supports multiple directories)"] --> B{"PluginFolderLoader.discover()"}
    B --> C["Single File: dice.py → Plugin Name = Filename"]
    B --> D["Package Form: weather/ (with __init__.py) → Plugin Name = Directory Name"]
    B --> E["Ignore: __pycache__ / _-prefixed / non-.py / directories without __init__.py"]
    C --> F["Import Module (spec_from_file_location)"]
    D --> G["Import Module (sys.path + import_module)"]
    F --> H["Identify Module Class: Main (BaseModule subclass) first, fallback to first subclass"]
    G --> H
    H --> I["Construct moduleInfo with entry-point consistent"]
    I --> J["ModuleLoader.load() merges<br/>Local takes precedence over PyPI same-named package"]
    J --> K["Shared with installed package:<br/>Enabled status / scope / meta / i18n / context"]
```

**Conventions and Features:**

- Plugin name source: filename for single file, directory name for package form
- Local plugin `moduleInfo.meta.source == "plugin_folder"`, seamlessly coexists with PyPI installed package modules
- Same name takes local precedence (for local override debugging), disabled entries are removed simultaneously

## Module Hot Reload Architecture

Hot reload is consistent for **all module sources**: local plugins (`plugins/` directory), runtime registration (`sdk.module.register()`), and PyPI installed package modules can all be hot reloaded via `sdk.reload_module()` / `sdk.module.reload()`—**default is full reload** (clear import cache by top-level package name and re-import dependent code, `full=False` is a lightweight escape route); `sdk.reload_all_modules()` / `sdk.module.reload_all()` can fully reload all registered modules at once (call after pip batch upgrade to make all effective):

```mermaid
flowchart TD
    A["sdk.enable_plugin_hot_reload()<br/>（Auto Monitor, Only Local Plugin Directory）"] --> B["PluginReloadWatcher Start"]
    B --> C["PollingObserver (Background Daemon Thread)<br/>Regularly Compare .py File mtime"]
    C --> D{"Plugin File Change"}
    D --> E["Change Debounce (Default 1 Second)"]
    E --> F["_handle_change Parse Plugin Name<br/>(Single File / Package Form)"]
    F --> G["asyncio.run_coroutine_threadsafe<br/>Schedule Back to Main Event Loop"]
    G --> H["sdk.reload_module(name, full=True Default)<br/>（Can Also Manually Call for Any Module）"]
    H --> I["Syntax Pre-check (File-by-file Parsing)<br/>Failure Rejects Reload, Old Instance Continues Serving"]
    I --> J["Unload Old Instance (on_before_unload → on_unload)<br/>Collect Dependent Modules for Cascading Reload"]
    J --> K{"Module Source?"}
    K -->|"plugin_folder"| L["Clear Registration and Plugin sys.modules<br/>Re-scan plugins/ Directory"]
    K -->|"runtime Runtime Registration"| M["Clear Cache and Re-import by Defined Module<br/>Re-fetch by Class Name (__main__ Guard)"]
    K -->|"PyPI Installed Package"| N["Clear Registration + Clear Package by top_level<br/>sys.modules subtree + __pycache__ Bytecode<br/>(When Metadata Missing, Fall Back to Old Module Object Top Segment)<br/>Refresh Import Cache and Re-query entry-point"]
    L --> O["Re-register + Load"]
    M --> O
    N --> O
    O --> P["Mount New Instance to sdk Attribute<br/>Verify New and Old Class Identity (Fake Reload Warning)"]
    P --> Q["Cascading Reload Dependent Modules<br/>(Plugins/Runtime Full Reload; PyPI Dependent Modules Default Re-import Code)"]
    L -.->|"File Deleted"| R["Remove from Load Result"]
    M -.->|"Definition Not Safe for Re-import"| R
    N -.->|"entry-point Disappeared (Uninstalled)"| R
```

**Differences Only in Discovery Phase for Three Sources**, Pre-check, Unload, and Cascading Reload are Fully Consistent:

- **Local Plugin** (`moduleInfo.meta.source == "plugin_folder"`): Clear sys.modules corresponding to plugin name and re-scan plugins/ directory; if file is deleted, remove from load result
- **Runtime Registration** (`source == "runtime"`): Re-import by defined module, re-fetch by class name and re-register; classes defined in `__main__` / without source file are rejected for re-import (guard warning, avoid re-executing entry script)
- **PyPI Installed Package**: Clear package's sys.modules subtree by `meta.top_level`, refresh import cache (break entry-point 60-second cache) and re-query and re-import; if entry-point disappears (pip uninstalled), remove from load result

**Default Semantics and Reliability Guarantees (2.11):**

- **Reload = Full Reload**: By default, clear sys.modules by top-level package name and re-import dependent code; `full=False` only clears metadata, PyPI dependent modules directly re-instantiate (performance escape for large dependency trees)
- **Syntax Pre-check Gate**: Before entering the unload process, parse each file for syntax, failure rejects reload—old instance is not unloaded, continues serving, syntax errors never put the module into a "half-dead state" (exceeds file count limit for large packages skips pre-check)
- **Cache Fallback**: When `top_level` metadata is missing, clear range by "old module object `__name__` prefix → module class `__module__` prefix" two-tier deduction; clear source file bytecode cache (pycache) during reload, small changes in the same second and length take effect
- **Identity Verification**: After successful reload, assert the change of new and old class identity, if unchanged (C extension cache not cleared), explicitly warn and carry `identity_changed: false` with `module.reload` event; `module.get_info()` exposes "registered version ≠ running version" via `running_identity` / `stale` fields
- **Failure Traceability**: Load failure scene (exception + traceback) can be directly queried via `module.last_error(name)` / `get_info()["last_error"]`, failure path also clears import cache of this module—"after modifying code, reload once again" will definitely read new code
- Reload will force activate modules that were previously lazy-loaded (explicit log); `reload_all_modules()` keeps lazy-loading strategy, only re-activates modules that were loaded before reload, dormant modules remain dormant
- `reload_all_modules()` reloads in dependency topological order, single module failure only records diagnostics and skips (no overall rollback—on_unload side effects are irreversible, consistent with the best-effort semantics of single module hot reload); scenarios where reload failure has been rolled back are similarly indicated in logs, old instances are in a terminated state

## Adapter Hot Reload Architecture

Adapter code-level hot reload (2.11) is structurally identical to the module pipeline: `sdk.adapter.reload(adapter_name)` / `sdk.reload_adapter(adapter_name)` executes for both **local plugin** and **PyPI installed package** sources—

```mermaid
flowchart TD
    A["sdk.adapter.reload(Platform Name)"] --> B["Syntax Pre-check (File-by-file Parsing)<br/>Failure Rejects Reload, Old Adapter Continues Serving"]
    B --> C["Snapshot: adapterInfo / Instance / Startup State /<br/>Startup Task / Bots / sys.modules Entries"]
    C --> D["Unload (shutdown means cleanup:<br/>Routing/Event/Command/Task/Connection/bot offline + unregistration)"]
    D --> E["Clear Cache: __pycache__ Bytecode →<br/>sys.modules Subtree → invalidate_caches<br/>→ Finder Cache → Plugin Path Record"]
    E --> F{"Source?"}
    F -->|"Plugin Directory"| G["Re-scan plugins/ (discover_adapters)"]
    F -->|"PyPI Installed Package"| H["Re-query entry-point and re-import<br/>(top_level cleanup + class __module__ fallback)"]
    G --> I["Re-register + startup (Original Running State)<br/>Verify Class Identity (Fake Reload Warning)"]
    H --> I
    I --> J["adapter.reload Event<br/>identity_changed / version_old→new / was_started"]
    G -.->|"Plugin Deleted"| K["Remove from Load Result"]
    H -.->|"entry-point Disappeared"| K
    I -.->|"Failure"| L["Rollback: Restore sys.modules /<br/>Registration Stub / Instance / Startup State"]
```

**Differences from Module Pipeline:**

- Adapter has no lazy loading or dependency cascading: Reload **does not cascade** dependent other adapters (only warnings—dependent parties indirectly consume through the registry, no instance-level cascading semantics)
- Startup is an asynchronous chain (`startup` dispatched via `_run_adapter`, including dependency skipping and exponential backoff retry): Startup temporarily failing **does not judge reload failure** (code has been replaced), results are broadcast via `adapter.status.change`
- The instance reuse trap of `register()` (same class object reuses old instance) is covered by the "pyc cleanup + sys.modules clear + identity verification" three-piece set
- Lifecycle events: `adapter.reload` (payload carries `adapter_name` / `success` / `full` / `duration_ms` / `identity_changed` / `version_old→new` / `was_started` / `source`)

> [!NOTE]
> This feature requires ErisPulse **2.8.0+**.



====
快速上手
====


### 快速开始

# Quick Start

> **This is your first step.** Run an ErisPulse robot from scratch in 5 minutes—see the result first, then expand each step.

## 60-Second Demo: Let the Bot Reply to You First

**1. Install** (Python >= 3.10):

```bash
pip install ErisPulse
```

**2. Initialize the project.** The wizard will prompt you to set the project name, select the platform adapter to connect, and complete the configuration, then generate `main.py` and `config/config.toml`:

```bash
epsdk init
```

**3. Open `main.py`, and replace it with these 9 lines of code:**

```python
from ErisPulse import sdk
from ErisPulse.Core.Event import command

@command("ping", help="Test if the bot is online")
async def ping_handler(event):
    await event.reply("Pong! The bot is running normally.")

if __name__ == "__main__":
    import asyncio
    asyncio.run(sdk.run(keep_running=True))
```

**4. Run**:

```bash
epsdk run main.py
```

The terminal will output framework startup logs and adapter connection information. At this point, send `/ping` to the bot in your connected platform; it will reply:

> Pong! The bot is running normally.

Seeing this reply confirms that the framework, adapter, and event handling chain are all working. If it doesn't work, go directly to the [Troubleshooting section](#troubleshooting) at the end of the document; if it works, continue reading to see what other options are available at each step.

## Install ErisPulse: Three Ways

The above uses the most direct pip method. Choose according to your environment:

### Install with pip

Ensure your Python version is >= 3.10, then install using pip:

```bash
pip install ErisPulse
```

If you have already installed [uv](https://github.com/astral-sh/uv), you can also use `uv pip install ErisPulse` for faster installation.

When you only want to install the `epsdk` command-line tool globally without polluting the project environment, it is recommended to use `uv tool install`:

```bash
uv tool install ErisPulse
```

After installation, `epsdk` will be globally available: when running within a project directory, it will automatically detect the project's `.venv` (installing `epsdk install` into the project environment, and running `epsdk run` using the project environment), while the framework itself is provided by the tool environment. See [Installation Reference](user-guide/installation.md) for details.

### One-Click Installation Script (Recommended for New Environments)

The installation script will automatically detect your environment (Docker, Python, uv), and guide you to select the most suitable installation method, supporting multiple languages (Chinese/English/Japanese/Russian/Traditional Chinese).

Windows (PowerShell):
```powershell
irm https://get.erisdev.com/install.ps1 -OutFile install.ps1; powershell -ExecutionPolicy Bypass -File install.ps1
```

macOS / Linux:
```bash
curl -fsSL https://get.erisdev.com/install.sh -o install.sh && chmod +x install.sh && ./install.sh
```

The script will guide you through:

- **Docker Installation** (recommended if Docker is detected): Choose image source (Docker Hub / GHCR), version channel (stable / pre-release), Dashboard management panel configuration, and port settings
- **Global CLI Installation (uv tool, recommended)**: Install `epsdk` as a global command, without virtual environments; uv automatically manages Python (even if the system version is too low); when running within a project directory, it automatically detects the project's `.venv`
- **Traditional Installation**: Automatically create a virtual environment, select the ErisPulse version, and optionally install the Dashboard management panel module

### Using Docker

The Docker image comes with the ErisPulse framework and the Dashboard management panel, supporting `linux/amd64` and `linux/arm64` architectures.

```bash
# Download docker-compose.yml
curl -O https://raw.githubusercontent.com/ErisPulse/ErisPulse/main/docker-compose.yml

# Set the Dashboard token and start
ERISPULSE_DASHBOARD_TOKEN=your-token docker compose up -d
```

<details>
<summary>Is Docker Hub unavailable?</summary>

Use the GitHub Container Registry image, and modify the `image` in `docker-compose.yml`:

```yaml
image: ghcr.io/erispulse/erispulse:latest
```

</details>

After starting, access `http://<host>:8000/Dashboard` and log in using the set token.

## Initialize Project

### Interactive Initialization (Recommended)

```bash
epsdk init
```

This will start an interactive wizard that guides you through:
- Project name setting
- Log level configuration
- Server configuration (host and port)
- Adapter selection and configuration
- Project structure creation

### Quick Initialization

```bash
# Quick mode with a specified project name
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

## Installing Modules

### Installing via CLI

```bash
epsdk install Yunhu AIChat
```

### Viewing Available Modules

```bash
epsdk list-remote
```

### Interactive Installation

Without specifying a package name, enter the interactive installation interface:

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

ErisPulse dynamically discovers modules/adapters, and IDEs cannot complete platform-specific methods by default.  
Run the following command to generate type stubs:

```bash
epsdk types
```

After generation, use the imported types as variable annotations to obtain precise completion (see [IDE Completion Guide](./getting-started/ide-completion.md)):

```python
from _ep_types import Yunhu
from ErisPulse import sdk

adapter: Yunhu = sdk.adapter.get("yunhu")
await adapter.Send.To("group", "123").Board(...)  # Completion for platform-specific methods
```

## Project Structure

After initialization, the project structure is as follows:

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

# Create Your First Bot

> [!TIP]
> **When to read this**: Your bot is already running, and you want to write your first `/hello` command handler and understand what `sdk.run` and command decorators do. If you haven't installed ErisPulse, initialized a project, or run the project yet, complete the "Install", "Initialize Project", and "Run Project" steps in [5-Minute Quick Start](../quick-start.md) first; otherwise, skip this section.

Running through the quick start is just the first step—this guide walks you through writing your first command handler and explains what each line of code does within the framework.

## Step 1: Write Your First Command

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
    
    # keep_running=True (default): The framework blocks and stays running until a shutdown signal is received (e.g., Ctrl+C)
    await sdk.run(keep_running=True)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

### `keep_running` Parameter

`sdk.run(keep_running)` controls whether the framework blocks and remains running:

- **`keep_running=True` (default)**: `run()` will block indefinitely until a shutdown signal (e.g., Ctrl+C) is received, suitable for pure bot applications.
- **`keep_running=False`**: `run()` returns immediately after initialization. **The framework is not unloaded**—active adapters/modules continue processing message events as background tasks. You can then proceed with your own logic until the event loop ends and the framework shuts down. For example:

```python
async def main():
    await sdk.run(keep_running=False)   # Returns immediately after initialization
    # The framework is running in the background, here you can continue doing other things
    while True:
        await asyncio.sleep(3600)
        print("Check every hour")
```

> Besides the two modes of `run()`, there are also more granular ways to manually control the lifecycle, such as `init()`/`uninit()` and individually starting/stopping adapters/routes. See [Startup Process and Manual Control](../advanced/startup.md).

## Step 2: Run the Robot

```bash
# Run normally
epsdk run main.py

# Development mode (supports hot reload)
epsdk run main.py --reload
```

## Step 3: Test the Bot

Send the following command in your chat platform:

```
/hello
```

You should receive a reply from the bot.

## Code Explanation

### Command Decorator

```python
@command("hello", help="Send a greeting message")
```

- `hello`: The command name, which users invoke via `/hello`
- `help`: The help description, displayed in the `/help` command

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

> For a complete list of Event object methods, refer to [Event Wrapper Class Details](../developer-guide/modules/event-wrapper.md).

### Sending a Reply

```python
await event.reply("Reply content")
```

`event.reply()` is a convenient method for sending messages back to the sender.

## Extensions: Adding More Features

ErisPulse provides rich event handling and data processing capabilities:

- **Message Listening**: Use `@message.on_message()` to listen to various types of messages → [Event Handling Introduction](event-handling.md)
- **Notification Listening**: Use `@notice.on_friend_add()` and others to listen to system notifications → [Event Handling Introduction](event-handling.md)
- **Data Storage**: Use `sdk.storage.get/set` to persist data → [Common Tasks Examples](common-tasks.md)

## FAQ

### No response from command?

1. Check if the adapter is correctly configured, and confirm that the `status` of the adapter in `config/config.toml` is set to `true`.
2. Check the terminal log output to confirm if there are any error messages (especially those with `ERROR` level).
3. Confirm that the command prefix is correct (the default is `/`), and check the `[ErisPulse.event.command]` section in the configuration file.
4. Confirm that the command name is spelled correctly, and pay attention to case sensitivity settings.

### How to change the command prefix?

Add the following to `config.toml`:

```toml
[ErisPulse.event.command]
prefix = "!"
case_sensitive = false
```

### How to support multiple platforms?

ErisPulse uses the OneBot12 standard to unify the event formats of different platforms. Handlers registered with `@command` and `@message` will automatically receive events from all platforms. You can distinguish the source platform using `event.get_platform()`:

```python
@command("hello")
async def hello_handler(event):
    platform = event.get_platform()
    
    if platform == "yunhu":
        await event.reply("你好！来自云湖")
    elif platform == "telegram":
        await event.reply("Hello! From Telegram")
    else:
        await event.reply("你好！")
```

> For more multi-platform adaptation techniques, please refer to [Common Tasks Examples](common-tasks.md#multi-platform-adaptation).

## What's Next

- **Continue along the learning path**: Read [Basic Concepts](basic-concepts.md) to understand what the framework behind command handlers does.
- **Want to handle more message types**: [Event Handling Introduction](event-handling.md), how to write handlers for messages / notifications / requests / meta-events.
- **Want to add practical features**: [Common Tasks Examples](common-tasks.md), ready-to-use code for persistence, scheduled tasks, and permission control.



### 基础概念

# Core Concepts

> [!NOTE]
> **L1 Core Must-Read** — The second article in the "L1 Core Five Articles" on the documentation homepage (Module Development Introduction → **Core Concepts** → Event Wrapper → Configuration File Explanation → Exception Handling).

What components does a message pass through from the user's message to the bot's reply? What are the responsibilities of adapters and modules? After reading this, you will be able to answer design questions that arise when writing processors yourself, rather than just copying examples.

## Event-Driven Architecture

ErisPulse adopts an event-driven architecture, where all interactions are passed and handled through events.

### Event Flow

```
User sends message
      │
      ▼
Platform receives
      │
      ▼
Adapter receives native platform event
      │
      ▼
Converts to OneBot12 standard event
      │
      ▼
Submits to event system
      │
      ▼
Distributes to registered handlers
      │
      ▼
Module processes event
      │
      ▼
Sends response via adapter
      │
      ▼
Platform displays to user
```

### OneBot12 Standard

ErisPulse uses OneBot12 as the core event standard. OneBot12 is a universal chatbot application interface standard that defines a unified event format.

All adapters convert platform-specific events into OneBot12 format, ensuring code consistency.

## Core Components

### 1. SDK Object

The SDK is the unified entry point for all features, providing access to core components.

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
> **Import from root** — `from ErisPulse.Core import adapter` / `import ErisPulse.Core.adapter`
> This binds to the **manager instance** (`AdapterManager` singleton), not the sub-module — `ErisPulse.Core`
> package re-exports will mask the same-named sub-modules. When writing tests, patches, or needing the module object itself, always use
> `from ErisPulse import sdk` root import (where `sdk.adapter` is the manager instance).

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
    
    # Send reply
    await event.reply(f"User: {user_id}, Platform: {platform}")
```

### 3. Adapters

Adapters serve as bridges between ErisPulse and external platforms.

**Responsibilities:**
- Receive native platform events
- Convert them into OneBot12 standard format
- Send standard-format events back to the platform

**Example Adapters:**
- Yunhu Adapter: Communicates with the Yunhu platform
- Telegram Adapter: Communicates with the Telegram Bot API
- OneBot11 Adapter: Communicates with OneBot11-compatible applications
- Email Adapter: Handles email sending and receiving

### 4. Modules

Modules are the basic units of functional extension and can:

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

When the SDK initializes, it scans all entry points in the `erispulse.module` group, registers the module class with `ModuleManager`, then initializes them in topological order based on dependencies.

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
- **Loading**: The module instance is created, and `on_load(event)` is called (`event = {"module_name": "MyModule"}`)
- **Unloading**: `on_unload(event)` is called, and resources are cleaned up

#### Loading Strategy

Declare the module's loading behavior via `get_load_strategy()`:

```python
from ErisPulse.loaders import ModuleLoadStrategy

class Main(BaseModule):
    @staticmethod
    def get_load_strategy():
        return ModuleLoadStrategy(
            lazy_load=True,   # Whether to load lazily (default True)
            priority=0        # Loading priority, higher values initialize earlier
        )
```

- **`lazy_load=True` (default)**: The module initializes only when first accessed via `sdk.MyModule`, reducing startup time
- **`lazy_load=False`**: The module initializes immediately when the SDK starts, suitable for modules that need to listen to lifecycle events or execute scheduled tasks
- **`priority`**: Modules with the same priority load in registration order; higher values initialize earlier

> For detailed explanations of the lazy-loading mechanism, refer to [Lazy Loading System](../advanced/lazy-loading.md).

## Event Types

ErisPulse supports five types of events:

| Event Type | Decorator | Description |
|---------|--------|------|
| Message Event | `@message.on_message()` | Any message sent by the user (private chat, group chat) |
| Command Event | `@command("name")` | Messages starting with a command prefix (e.g., `/hello`) |
| Notice Event | `@notice.on_friend_add()` etc. | System notifications (friend added, group member changes, etc.) |
| Request Event | `@request.on_friend_request()` etc. | User requests (friend requests, group invitations) |
| Meta Event | `@meta.on_connect()` etc. | System-level events (connection, disconnection, heartbeat) |

> For detailed usage and code examples of each event type, refer to [Event Handling Introduction](event-handling.md).

## Core Module Descriptions

### Storage (Storage)

A key-value storage system based on SQLite, used for persistent data.

```python
# Set value
sdk.storage.set("key", "value")

# Get value
value = sdk.storage.get("key", "default_value")

# Bulk operations
sdk.storage.set_multi({
    "key1": "value1",
    "key2": "value2"
})

# Transactions
with sdk.storage.transaction():
    sdk.storage.set("key1", "value1")
    sdk.storage.set("key2", "value2")
```

### Config (Configuration)

TOML-based configuration file management.

```python
# Get configuration
config = sdk.config.getConfig("MyModule", {})

# Set configuration
sdk.config.setConfig("MyModule", {"key": "value"})

# Read nested configuration
value = sdk.config.getConfig("MyModule.subkey", "default")
```

### Logger (Logging)

A modular logging system.

```python
# Log messages
sdk.logger.info("This is an info message")
sdk.logger.warning("This is a warning message")
sdk.logger.error("This is an error message")

# Get child logger
child_logger = sdk.logger.get_child("submodule")
child_logger.info("Submodule log message")
```

**Attribute Access Syntactic Sugar**

In addition to using the `get_child()` method, you can also create child loggers using **attribute access**, which is a more concise **syntactic sugar**:

```python
# Create child logger using attribute access
sdk.logger.mymodule.info("Module message")

# Supports nested access
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

> For the complete routing API (WebSocket, middleware, rate limiting, CORS, etc.), refer to [Router Manager](../advanced/router.md).

### Client (Network Client)

A unified network client that aggregates HTTP requests, WebSocket connections, connection pooling, automatic retries, timeout control, request statistics, and lifecycle event integration.

```python
from ErisPulse.Core import client

# HTTP request
resp = await client.get("https://api.example.com/users")
data = await resp.json()

# Request with retries and timeout
resp = await client.get(url, timeout=30, max_retries=3)

# WebSocket connection
ws = await client.ws_connect("wss://example.com/ws")
async for text in ws.iter_text():
    await ws.send_text(f"Echo: {text}")
```

> For the complete network client API, refer to [Network Client](../advanced/http-client.md).

## SendDSL Message Sending

Adapters provide a chainable message sending interface.

### Basic Sending

```python
# Get adapter instance
yunhu = sdk.adapter.get("yunhu")

# Send message
await yunhu.Send.To("user", "U1001").Text("Hello")

# Specify sender account
await yunhu.Send.Using("bot1").To("group", "G1001").Text("Group message")
```

### Chainable Modifiers

```python
# @user
await yunhu.Send.To("group", "G1001").At("U2001").Text("@message")

# Reply to message
await yunhu.Send.To("group", "G1001").Reply("msg123").Text("Reply")

# @all
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

ErisPulse enables module lazy loading by default. Modules only initialize when first accessed (e.g., `sdk.MyModule`), significantly improving startup speed.

```python
from ErisPulse.loaders import ModuleLoadStrategy

class Main(BaseModule):
    @staticmethod
    def get_load_strategy():
        return ModuleLoadStrategy(
            lazy_load=True,   # Enable lazy loading (default)
            priority=0        # Loading priority, higher values initialize earlier
        )
```

**Scenarios where lazy loading should be disabled (`lazy_load=False`):**
- Modules that listen to lifecycle events (e.g., `core.init.complete`)
- Modules that start scheduled tasks or background services
- Modules that need to complete initialization before other modules are loaded

> For detailed explanations of the lazy loading mechanism and considerations, refer to [Lazy Loading System](../advanced/lazy-loading.md).



### 事件处理入门

# Getting Started with Event Handling

> [!TIP]
> **When to read this**: Read this if you want your bot to respond to messages, commands, notifications, or requests, or if you need to implement reply waiting / multi-turn conversations, or troubleshoot "why isn't my command triggering". If you only want to understand the framework design, [Basic Concepts](basic-concepts.md) is all you need; otherwise, feel free to skip this.

Event handlers are where the bot "understands" users and reacts to them. This guide provides copy-paste-ready code patterns for the five event types, covering practical scenarios such as argument parsing, permissions, throttling, and multi-turn interaction.

## Overview of Event Types

ErisPulse supports the following event types:

| Event Type | Description | Applicable Scenarios |
|---------|------|---------|
| Message Event | Any message sent by a user | Chatbot, content filtering |
| Command Event | Message starting with a command prefix | Command processing, function entry |
| Notice Event | System notifications (friend addition, group member changes, etc.) | Welcome messages, status notifications |
| Request Event | User requests (friend requests, group invitations) | Automatic request handling |
| Meta Event | System-level events (connection, heartbeat) | Connection monitoring, status checks |

## Message Event Handling

> **Tip**: It is recommended to use the `Event` type annotation in event handlers to get IDE auto-completion and type checking support.

```python
from ErisPulse.Core.Event import Event  # Import Event type for annotation
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
    sdk.logger.info(f"Message sent in group {group_id} by {user_id}")
```

### Listening to @ Messages

```python
@message.on_at_message()
async def at_handler(event: Event):
    # Get list of mentioned users
    mentions = event.get_mentions()
    await event.reply(f"You mentioned these users: {mentions}")
```

### Wildcard and Regex Listening

All four message decorators (`on_message` / `on_private_message` / `on_group_message` /
`on_at_message`) support `pattern` (glob wildcard) and `regex` (regex), and messages that do not match will **not trigger** the handler:

```python
# Glob wildcard: * any string, ? single character, [seq] character set
@message.on_message(pattern="签到*")
async def signin_handler(event: Event):
    await event.reply("Sign-in successful")

# Regex: match amount
@message.on_message(regex=r"\d+\s*元")
async def price_handler(event: Event):
    await event.reply(f"Received amount: {event.get_text()}")

# Both pattern and regex given → both must match
@message.on_message(pattern="*元", regex=r"\d+\s*元")
async def combined_handler(event: Event):
    pass
```

`wait_reply` also supports these two parameters (see [Wait Reply Functionality](../developer-guide/modules/event-wrapper.md#wait-reply-functionality)).

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
/info - View information
    """
    await event.reply(help_text)
```

### Command Aliases

```python
@command(["help", "h"], aliases=["帮助"], help="Display help information")
async def help_handler(event):
    await event.reply("Help information...")
```

Users can call using any of the following:
- `/help`
- `/h`
- `/帮助`

### Command Arguments

```python
@command("echo", help="Echo message")
async def echo_handler(event):
    # Get command arguments
    args = event.get_command_args()
    
    if not args:
        await event.reply("Please enter a message to echo")
    else:
        await event.reply(f"You said: {' '.join(args)}")
```

Arguments preserve the original case entered by the user (even if case-insensitive is configured, case normalization for command matching does not affect argument content).

### Declared Parameters and Options (args= / options=)

Manually parsing arguments requires handling type conversion and error messages yourself. After declaring `args=` / `options=`, the framework automatically parses command arguments and **injects them by name** after permission checks pass; when user input is incorrect, it automatically replies with localized error messages and usage (without throwing an exception crash); `/help <command>` will also automatically display usage:

```python
@command(
    "roll",
    args="<count:int> [sides:int=6]",
    options={"verbose": "-v/--verbose", "label": "--label"},
    help="Roll dice",
)
async def roll_handler(event, count: int, sides: int = 6, verbose: bool = False, label: str = ""):
    total = sum(random.randint(1, sides) for _ in range(count))
    await event.reply(f"Rolled {count} {sides}-sided dice, total points: {total}")
```

`args=` positional parameter syntax: `<count:int>` is required, `[sides:int=6]` is optional (with default value). Supported types:

| Type | Example Input | Description |
|------|---------|------|
| `str` | `hello` | Text (default type) |
| `int` / `float` | `3` / `0.5` | Number |
| `bool` | `是` / `yes` / `はい` / `да` / `true` / `no` / `取消` | Boolean, reuses confirmation words from `Event.confirm()` |
| `literal` | `<mode:literal=fast|slow>` | Enum, accepts only listed values; optional form defaults to first |
| `duration` | `90s`、`1h30m`、`1d` | Duration, converted to float in seconds |
| `rest` | `<text:rest>` | Remaining full text (must be at the end) |

`options=` is declared as a dictionary: key is the handler parameter name, value is the flag form (multiple aliases separated by `/`). Parameters annotated as `bool` are boolean flags (appear as `True`); others (default as `str`) are options with values, supporting `--label hello` and `--label=hello` value formats, with type following the handler annotation. Options are recognized and removed first, remaining tokens are parsed according to `args=` (the `rest` covers the remaining text after option removal).

**Behavior Points**:

- Permission checks precede parameter parsing—users without permission will not trigger parsing
- Parsing fails (type mismatch / missing parameter / too many parameters / unknown option) automatically replies with localized error + usage, command is still claimed
- Declared parameter names must exist in the handler signature, otherwise a `ValueError` is thrown during registration
- Commands without declaring `args=` / `options=` behave exactly the same (backward compatibility)

### Command Governance (cooldown= / rate_limit= / usage_limit= / deprecated=)

Handwritten cooldown timing, rate limiting window, usage quota, deprecation prompts can be replaced with declarations, all four can be combined.

**Cooldown**—duration syntax is consistent with the `duration` type in `args=` (e.g., `"30s"`, `"1h30m"`, `"1d"`):

```python
@command("daily", cooldown="1d", cooldown_key="user", cooldown_reply="Signed in today")
async def daily_handler(event):
    await event.reply("Sign-in successful!")
```

**Rate Limit**—sliding window declaration `"count/window"` (e.g., `"5/minute"`, `"10/s"`, `"3/2m"`):

```python
@command("search", rate_limit="5/minute", rate_limit_key="user")
async def search_handler(event):
    await event.reply("Search results")
```

**Usage Limit**—total usage limit within a period (e.g., `"100/day"`, `"10/hour"`, `"500/30d"`), exceeding the limit rejects execution:

```python
@command("translate", usage_limit="100/day", usage_limit_key="user",
         usage_limit_reply="Daily translation count exhausted")
async def translate_handler(event):
    ...
```

Unlike cooldown/limiting, usage counting is **persisted in storage** (KV key `erispulse.usage.<key>`, not lost on restart): if storage is unreachable, it automatically degrades to pure in-memory counting and logs a warning (count resets on restart in this case). Counting automatically resets with the usage period switch, and cleanup occurs when the module is unloaded.

**Deprecated**—automatically replies with deprecation text upon call; `deprecated_reject=True` rejects execution:

```python
@command("oldcmd", deprecated="Please use /newcmd", deprecated_reject=True)
async def old_handler(event): ...
```

Key granularity (`cooldown_key=` / `rate_limit_key=`): `"user"` (default, shared by the same user), `"session"` (shared by the same session, like the same group), `"global"` (shared by all users and sessions).

**Behavior Points**:

- Cooldown / rate limiting / usage limit hits default to **silent discard** (symmetrical to scope silence); if `cooldown_reply=` / `rate_limit_reply=` / `usage_limit_reply=` is declared, reply with the text when hit
- Command hits claim the command—governed commands won't leak to lower priority message handlers
- Governance checks occur after all permission checks and parameter parsing pass, before actual execution: users without permission don't trigger, parameter errors don't consume
- When cooldown and rate limiting are declared simultaneously, cooldown is checked first (cooldown hits don't occupy the rate limiting window); usage limits are checked after cooldown/limiting
- `deprecated=` defaults to replying with the text and **continues execution**; `deprecated_reject=True` rejects execution (`command.executed` hook records `success=False, error="deprecated"`)
- `/help` list and single command help automatically display deprecation markers and text
- Cooldown and rate limiting status are in-process memory, automatically cleaned up when the module is unloaded; cross-process sharing / persistence on restart is out of scope (**usage quota counting excepted**—persisted via storage, see above)
- Declaration is validated at registration (fail-fast): illegal syntax, key granularity not in whitelist, reply not paired with main declaration all throw `ValueError`

### Handler Throttling (throttle=) and Debouncing (debounce=)

Message handler anti-spam declaration—same key events are processed at most once within the interval, others are silently discarded:

```python
from ErisPulse import sdk

@sdk.message.on_message(throttle="2s", throttle_key="user")
async def handler(event): ...
```

Debounce and throttling are complementary: **only the last one within the window is executed**, previous pending tasks are automatically canceled (suitable for search suggestion scenarios where processing happens after the user stops typing):

```python
@sdk.message.on_message(debounce="2s", debounce_key="user")
async def search(event): ...
```

`on_message` / `on_private_message` / `on_group_message` / `on_at_message` all support it; `throttle_key=` / `debounce_key=` use the same key granularity as command governance (`user` / `session` / `global`), duration syntax is consistent with `duration`. Throttling and `pattern=` / `regex=` conditions are overlapped and effective (all must match to trigger); discarded within the interval only logs TRACE; declaration is validated at registration; `throttle=` and `debounce=` semantics are mutually exclusive (throw `ValueError` if both are declared).

> **Debounce does not interrupt midway**: Only pending tasks that have not crossed the waiting window are canceled; tasks already past the window and currently executing are not canceled by new events (avoid partial side effects if stopped at any await point).

### Dependency Injection (Depends)

Common dependencies (database sessions, configuration reading, etc.) can be extracted into dependency functions. Handlers declare them as `Depends(dependency function)` with a default value, and the framework automatically calls the dependency function with the context object before calling and injects it by name:

```python
from ErisPulse.Core import Depends

async def get_session(event):
    return await sdk.module.call("DB", "get_session")

@command("admin")
async def admin_handler(event, db=Depends(get_session)):
    ...
```

Request-level caching is enabled by default: within the same event distribution, the same dependency function is parsed only once, and all injection points share the result (e.g., `get_db` only creates a database session once per event); it is not reused across requests. Use `Depends(get_db, use_cache=False)` to disable caching for a single dependency.

Covers all framework injection points—command handlers, event handlers (`message.on_message()` etc.), lifecycle hooks (`sdk.lifecycle.on`), SSE route handlers. The first parameter of the dependency function is the context object of the injection point (event scenario is `Event`, lifecycle is event `data`, route is `HttpRequest` / `SseEmitter`); both synchronous and asynchronous dependency functions can be declared.

**Syntax sugar for declaring other module services**:

```python
@command("query")
async def query_handler(event, session=Depends.module("DB", "get_session")):
    ...
```

`Depends.module(module name, method name, *fixed arguments)` is equivalent to calling `sdk.module.call(...)` inside the dependency function. Module instantiation (`__init__`) is not covered—there is no context object during instantiation; for FastAPI hosted HTTP routes, use FastAPI's native `fastapi.Depends`.

**Behavior Points**:

- Declaration is validated at registration (fail-fast): throws `ValueError` if the dependency is not callable, or if it conflicts with `args=` / `options=` parameters
- Exceptions thrown by the dependency function are handled in the same way as the handler's own exceptions (command automatically replies with errors)
- Handlers without declaring `Depends` have zero overhead (no reflection during distribution)
- For FastAPI hosted HTTP routes, use FastAPI's native `fastapi.Depends`

### Command Groups

```python
@command("admin.reload", group="admin", help="Reload module")
async def reload_handler(event):
    await event.reply("Module reloaded")

@command("admin.stop", group="admin", help="Stop bot")
async def stop_handler(event):
    await event.reply("Bot stopped")
```

The `group` parameter is only used for help list categorization; the above example's `admin.reload` is a **single command name** (the dot is just a naming style, users need to input `/admin.reload`).

### Subcommands

Command names support **multi-token** forms separated by spaces, enabling subcommands like `/admin add`, `/admin user ban`:

```python
@command("admin", help="Admin commands")
async def admin_handler(event):
    await event.reply("Usage: /admin add | /admin remove")

@command("admin add", help="Add admin")
async def admin_add_handler(event):
    target = event.get_command_args()[0]
    await event.reply(f"Added {target}")

@command("admin remove", aliases=["a remove"], help="Remove admin")
async def admin_remove_handler(event):
    await event.reply("Removed")
```

Matching rules (**longest prefix match**):

- `/admin add x` prioritizes matching `admin add`, `event.get_command_args()` returns `["x"]` (arguments after the subcommand name)
- Only `admin` is registered, `/admin add x` matches `admin`, `get_command_args()` returns `["add", "x"]` (historical behavior unchanged)
- Aliases support multi-token forms (e.g., `a remove`), single-token aliases (e.g., `a`) can also point to subcommands
- When parent and child commands are registered simultaneously, unregistered subcommands (e.g., `/admin list x`) fall back to the parent command

**Permission Inheritance**: When subcommands do not declare `permission`, they automatically inherit the permission of the nearest ancestor command that declared it on the parent chain—protecting `/admin` automatically protects all its subcommands; the permission declared by the subcommand itself takes precedence:

```python
def is_admin(event):
    return event.get_user_id() in {"user123"}

@command("admin", permission=is_admin, help="Admin commands")
async def admin_handler(event):
    ...

# No need to repeat permission declaration, automatically inherits is_admin
@command("admin add", help="Add admin")
async def admin_add_handler(event):
    ...
```

Note: `master=True` and `hidden` **do not** inherit, they need to be declared separately on the subcommand; user ACL (whitelist/blacklist) matches by full command name, glob rules like `"admin*"` can cover entire subcommand groups.

In the `/help` command overview, subcommands are automatically indented under visible parent commands (e.g., `admin` → `admin add` indented one level, `admin user` → `admin user ban` indented two levels).

### Command Permissions and Access Control

Command permissions are divided into three layers, checked from top to bottom (if the upper layer rejects, the lower layer is not checked):

```python
# ① Command Permission ACL (user-side configuration): By user whitelist/blacklist of the command, rejects with "permission denied"
# ② master=True — Only the framework owner can execute (framework automatically checks, rejects with "permission denied")
@command("restart", master=True, help="Restart module")
async def restart_handler(event):
    await event.reply("Module restarted")

# ③ permission=call function — The command's own control logic (returns True to execute)
def is_admin(event):
    return event.get_user_id() in {"user123", "user456"}

@command("panel", permission=is_admin, help="Admin panel")
async def panel_handler(event):
    await event.reply("Welcome to the admin panel")
```

**Command User ACL** (`ErisPulse.event.command.acl`): Users can configure user whitelist/blacklist for any command, command names support exact and glob patterns (e.g., `"roll*"`), rejects with "permission denied":

```toml
# config.toml — Allow only 123456 to execute restart; 666 is always rejected
[ErisPulse.event.command.acl.restart]
allow = ["onebot11:123456"]
deny = ["onebot11:666"]
```

Order of judgment: `deny` hits → reject; `allow` is non-empty and does not hit → reject; if ACL is not configured, follow `event.command.default_allow` (false = strict mode, no ACL means reject; true means leave to developer default `master=True` / `permission`). Runtime API (command names support glob):

```python
from ErisPulse.Core.Event import command

command.allow_user("restart", "onebot11", "123456")   # Allow list
command.deny_user("restart", "onebot11", "666")       # Deny list
command.remove_acl("restart")                          # Clear whitelist/blacklist
command.get_acl("restart")                             # Query current list
```

> Command handlers are imported from event package: `from ErisPulse.Core.Event import command`; can also access via SDK event package: `sdk.Event.command` (both are the same singleton). In modules, they are usually imported with the command decorator (`from ErisPulse.Core.Event import command`).

Cross-command / cross-user **event-level** access control (whether to receive messages from a person / group / Bot) goes through the **identity dimension** of the scope ( `scope.identity` ); **module-level** availability (which modules can be used) goes through the **module dimension** of the scope ( `scope.platforms / bots / sessions` ).
See [Scope](../advanced/scope.md).

> Suggestion: Use `master=True` / `permission` for command internal logic that needs to be linked with business logic; use the identity dimension of the scope for access control based on users / groups; use the module dimension of the scope for controlling module availability.

### Command Priority

```python
# The higher the priority value, the earlier it executes
@message.on_message(priority=10)
async def high_priority_handler(event):
    await event.reply("High-priority handler")

@message.on_message(priority=1)
async def low_priority_handler(event):
    await event.reply("Low-priority handler")
```

### Parallel Event Handling

ErisPulse's event system uses a scheduling model where handlers of the same priority run in parallel, and handlers of different priorities run serially:

```
Event arrives
    ↓
priority=10 group: [handler C || handler D] parallel → merge results
    ↓ (if not interrupted)
priority=0 group: [handler A || handler B] parallel → merge results
    ↓
...
```

- **Parallel within the same priority**: Handlers of the same priority run simultaneously, improving throughput
- **Serial across different priorities**: Groups of different priorities run in order (the higher the value, the earlier it runs), ensuring that high-priority handlers run first
- **Copy-On-Write**: Handlers do not create a copy unless they make modifications, ensuring zero overhead
- **Conflict handling**: When multiple handlers of the same priority modify the same field, the last modification is used, and a warning log is recorded
- **Interruption mechanism**: After any handler calls `event.done()` (default) or `event.done(claim=False)`, subsequent lower-priority groups are skipped. The difference between claiming and blocking is explained in the next section [Link Control: Claiming and Blocking](#link-control-claiming-and-blocking)

```python
# Example: Parallel execution of handlers with the same priority
@message.on_message(priority=0)
async def handler_a(event):
    # Process task A
    event['result_a'] = process_a()

@message.on_message(priority=0)
async def handler_b(event):
    # Executes in parallel with handler_a
    event['result_b'] = process_b()

# Serial execution of different priorities
@message.on_message(priority=10)
async def handler_c(event):
    # Highest priority, executed first
    pass
```

> **Concurrency limit**: All matching handlers' tasks are created immediately, but a semaphore limits the number of concurrent executions, with a default upper limit of **64** (`ErisPulse.framework.handler_max_concurrency`, supports hot updates). Tasks exceeding the limit queue on the semaphore, waiting for previous tasks to complete before entering. This is your "pressure relief valve" during event peaks.
>
> **Slow logs**: If a single handler takes more than **1 second**, the framework logs a WARNING (`handler_slow`). The waiting time for `wait_reply` is excluded from the timing, so it won't misreport slow due to "waiting for a reply."

## Middleware: Rewrite or Reject Before Distribution

Middleware executes in order before event distribution, serving as the proper implementation point for scenarios such as firewalls, rate limiting, and event desensitization:

```python
from ErisPulse.Core import adapter

@adapter.middleware
async def firewall(data):
    if _is_banned(data.get("user_id")):
        return False          # Reject: Event is discarded, not entering any handler, no outbound side effects
    data["checked"] = True    # Return dict: Rewrite event payload (consistent with historical behavior)
    # Return None: Allow, payload unchanged (historical behavior)
    return data
```

| Return Value | Behavior |
|--------|------|
| `False` | **Reject**: Event is immediately discarded, not entering any handler |
| `dict` | Rewrite event payload and continue distribution |
| `None` | Allow, payload unchanged |

When rejected, the framework outputs a TRACE log and triggers the `adapter.event.blocked` lifecycle hook (carrying the middleware name and full event), providing audit for "why the event was not responded to."

## Command Dispatch Decision Chain: Why a Command Didn't Trigger

A command message sequentially passes through: **command text judgment → command name/alias match (suggests spelling if not matched) → match claims → scope → user ACL → owner → permission → cooldown/limit → usage limit (deprecated, notice/rejected) → parameter parsing → execution** (middleware can reject at the event level, see the previous section). If any step is not met, it terminates; governance hits are silently discarded by default (symmetrical to scope silence); permission rejections reply to the user, and deprecation replies or rejects according to the declaration.

In testing, `ErisPulse-Testing`'s `dispatch()` directly returns this decision chain (`DispatchTrace`, `trace.explain()` outputs step-by-step causality), and in production, `ErisPulse.Core.Event.start_dispatch_trace()` can collect the same record.

Additionally, `ErisPulse.runtime` provides two sets of diagnostic APIs: `explain_module(module name)` answers "why the module didn't load" (not registered / lazy loaded / disabled by configuration / missing dependencies / SDK version not satisfied, each item gives a reason), `explain_event(event)` answers "why the event didn't respond" (adapter not registered / identity blacklisted / module session blocked / command not matched); with `format_report()` renders human-readable conclusions.

## Scope Filtering: Why My Module Didn't Receive the Message

After an event arrives, there are two **silent** filters (neither reply nor error):

1. **Identity dimension** (`ErisPulse.scope.identity`): When the event enters the distribution entry point, it is judged by user > group > Bot > adapter whether to receive or not.
   Events rejected by this dimension are **completely discarded**, and no handler (including the command dispatcher) will be triggered.
2. **Module dimension** (`ErisPulse.scope`): When the event reaches a module's handler/command, it is judged by session > Bot > platform whether the module is available; if it does not pass, it is **silently skipped**.

```toml
# Example 1: All messages in a group are not propagated
[ErisPulse.scope.identity.sessions.onebot11."group_123"]
deny = true

# Example 2: Blocking MyModule in a certain Bot
[ErisPulse.scope.bots.onebot11."123456"]
blocked = ["MyModule"]
```

At this point, when a message from this group arrives, the commands and event handlers of `MyModule` **will not be scheduled**. This is not a bug, but a filtering mechanism—when troubleshooting "module response," first check the scope's identity and module binding.

- Filter logs are only visible at **TRACE** level ( `core.scope.identity_denied` / `core.scope.denied` ), and default INFO does not show any trace
- Framework-level handlers (such as the command dispatcher `scope_exempt=True`) are not affected by the **module dimension** but are affected by the **identity dimension** (the entire event has been discarded)
- There is a third filter before command execution: command user ACL (rejects with "permission denied," see above)
- The fourth filter is **event overwriting** (see next section)

> [!NOTE]
> **Relationship between scope filtering and event claiming (claim)**: Both silent filters occur before handler **scheduling**—handlers that are filtered out do not have the opportunity to execute, and naturally do not participate in the `event.done()` / `mark_processed()` claiming status. Whether an event has been claimed is determined only by **actual executed** handlers (command match claims, reply match claims, explicit calls); event rejection itself neither claims nor blocks (silently skips, the message continues through the remaining distribution chain).

> Scope configuration, matching syntax, and runtime API are described in [Scope](../advanced/scope.md).

## Event Overwriting: Overwrite Any Event Type Behavior Without Modifying Module Code

> [!NOTE]
> This feature requires ErisPulse **2.8.0+**.

Event handlers, when registered, declare parameters ( `pattern` / `regex` / `master` / `hidden` etc.) only as **developer defaults**.
A unified overwriting system allows users to overwrite any module's behavior by **event type**—OneBot12 standard types ( meta / message / notice / request ) and ErisPulse extended types ( command ) each have their own set of overwritable parameters:

| Event Type | Overwritable Parameters | Purpose |
|---------|-----------|------|
| `message` | `pattern` / `regex` / `detail_types` | Text trigger conditions + message subtype whitelist |
| `notice` | `detail_types` / `pattern` / `regex` | Notice subtype whitelist + text conditions |
| `request` | `detail_types` / `pattern` / `regex` | Request subtype whitelist + text conditions |
| `meta` | `detail_types` | Meta event subtype whitelist (connect / heartbeat etc.) |
| `command` | `master` / `hidden` / `aliases` / `prefix` / `help` / `usage` | Command implementation parameters (user priority) |
| `acl` (command-specific) | `allow` / `deny` | Command user whitelist/blacklist (by command name glob) |

```toml
# message: Overwrite text trigger condition (AND with code-level condition)
[ErisPulse.event.overrides.message.ChatModule]
pattern = "闲聊*"

# notice: Only respond to specific notice subtypes
[ErisPulse.event.overrides.notice.MyModule]
detail_types = ["group_increase"]

# command: Overwrite implementation parameters (user priority—can tighten or loosen developer default)
[ErisPulse.event.overrides.command.MyModule.restart]
master = true
hidden = true

# acl: Command user whitelist/blacklist (cross-command glob)
[ErisPulse.event.overrides.acl."roll*"]
allow = ["onebot11:u_vip"]

# ACL fallback (false = strict mode: no ACL means reject)
acl_default_allow = true
```

Runtime API (`from ErisPulse.Core.Event import overrides` or `sdk.Event.overrides`, **type sub-namespace**—each type has symmetric `set` / `get` / `delete` three-piece sets):

```python
from ErisPulse.Core.Event import overrides

overrides.message.set("ChatModule", pattern="闲聊*")   # message text condition
overrides.notice.set("MyModule", detail_types=["group_increase"])
overrides.command.set("MyModule", "restart", master=True)  # command parameter
overrides.acl.set("roll*", deny=["onebot11:u_bad"])    # command user blacklist

overrides.message.get("ChatModule")     # {"pattern": "闲聊*"}
overrides.message.delete("ChatModule")  # Restore developer default
```

- Overwrite conditions and handler code-level conditions **both take effect** (AND semantics); `command` parameter overwrite and developer declaration **deep merge** (overwrite priority)
- `detail_types`: Events without `detail_type` are allowed (not mistakenly kill unknown events)
- `pattern` / `regex`: Events without text (connect / heartbeat etc.) are not constrained, directly allowed
- `command` overwrite key `master` synchronously maps to storage key `must_master`; disabling commands uniformly goes through `acl` deny
- **Key name mapping explanation**: The parameter name `master` for `overrides.command.set("My", "restart", master=True)` is only a configuration alias; the actual storage key and the key name in the `get()` return value are unified as **`must_master`** ( `get()` returns `{"must_master": true}` )—runtime judgment reads the storage key, please do not read by the `master` key name
- Configuration changes take effect immediately (hot update), format validation warnings (unknown parameters / bad entries are ignored)

## Link Control: Claiming and Blocking

> [!NOTE]
> `event.done()` / `event.mark_processed()` `claim=` / `stop=` parameters for this feature require ErisPulse **2.7.1+**.

ErisPulse decouples the two orthogonal semantics of "claiming" and "blocking," unifying control through `event.done()`, which is convenient for stacking logging, auditing, permission, and other observation layers around command processing.

**Accurate definitions of the two concepts:**

- **Claiming (claim)**: Mark the event as processed by this handler (write to `_processed`). The command dispatcher sees claimed events and **skips duplicates**—preventing the same message from being processed by multiple command handlers. Typical scenario: After a command matches, claim it, preventing the command dispatcher from intervening again.
- **Blocking (stop)**: Prevent the event from propagating to **lower-priority** handlers (write to `_propagation_stopped`). Lower-priority handlers will no longer see the event. Typical scenario: A high-priority handler has fully processed the event and does not want lower-priority handlers to execute.

| `event.done(...)` | Claim | Block | Scenario |
|-------------------|------|------|------|
| `event.done()` | ✔ | ✔ | Standard practice for command / handler completion |
| `event.done(stop=False)` | ✔ | ✘ | Only claim: lower-priority observers (logging / statistics) still see it |
| `event.done(claim=False)` | ✘ | ✔ | Only block (e.g., firewall / rate limiting), but do not do command deduplication |

`event.done(claim=, stop=)` is an alias for `event.mark_processed(claim=, stop=)`, with identical parameters and behavior.

```python
@command("help")
async def help_cmd(event):
    event.done()            # Claim + Block (standard practice for command completion)

@message.on_message(priority=50)
async def observer(event):
    event.done(stop=False)  # Only claim: lower-priority still executes (logging / statistics)

@message.on_message(priority=100)
async def firewall(event):
    if denied(event):
        event.done(claim=False)  # Only block: lower-priority does not execute, but no deduplication
```

### Command and Reply Block Configuration

**Command match claims immediately**: Once a message matches a registered command name (including subcommands/aliases), regardless of subsequent scope or permission checks, it is claimed and defaults to blocking propagation—commands rejected by permissions will no longer leak to lower-priority message handlers (eliminating "double response" of commands being rejected and then responding again in `on_message`).

Blocking can be configured to allow lower-priority observers (logging / auditing / permissions) to still see these messages:

```toml
[ErisPulse.event.command]
block = false   # Command messages continue to flow to lower-priority handlers (claim is unaffected, will not be re-consumed)

[ErisPulse.event.wait_reply]
block = false   # Reply messages consumed by wait_reply continue to flow to lower-priority handlers
```

> Note: `block` only controls **blocking** (stop), not **claiming** (claim)—commands that match will never be re-consumed by message handlers; messages that do not match any command flow as usual to message handlers.

## Notice Event Handling

### Friend Addition

```python
from ErisPulse.Core.Event import notice

@notice.on_friend_add()
async def friend_add_handler(event):
    user_id = event.get_user_id()
    nickname = event.get_user_nickname() or "New friend"
    await event.reply(f"Welcome to add me as a friend, {nickname}!")
```

### Group Member Increase

```python
@notice.on_group_increase()
async def member_increase_handler(event):
    group_id = event.get_group_id()
    user_id = event.get_user_id()
    await event.reply(f"Welcome new member {user_id} to group {group_id}")
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
    
    await event.reply(f"Received invitation to group {group_id} from {user_id}")
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

After the adapter sends a meta event, the framework automatically tracks the bot status, and you can query it at any time:

```python
from ErisPulse import sdk

# Check if a bot is online
if sdk.adapter.is_bot_online("telegram", "123456"):
    telegram = sdk.adapter.get("telegram")
    await telegram.Send.To("user", "123456").Text("Bot is online")

# List all online bots
bots = sdk.adapter.list_bots()
for platform, bot_list in bots.items():
    for bot_id, info in bot_list.items():
        print(f"{platform}/{bot_id}: {info['status']}")

# Get full status summary
summary = sdk.adapter.get_status_summary()
```

## Interactive Handling

### Using the reply method to send replies

The `event.reply()` method supports various modifier parameters, making it convenient to send messages with features like @, reply, etc.:

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

# Combination usage: @ user + reply to message
await event.reply("Content", at_users=["user1"], reply_to="msg_id")
```

### Waiting for user reply

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
        await event.reply("Timeout, please re-enter.")
```

> [!TIP]
> **Commands remain available during waiting** (2.8.3+): Messages starting with a command prefix and matching a registered command (e.g., `/cancel`) will **execute the command** rather than serve as a reply, keeping the wait suspended—users can cancel/switch at any time, and the command executes while continuing the reply. For the old behavior of "waiting swallowing all text," configure `ErisPulse.event.wait_reply.cmdpass = true`, or use `wait_reply(cmdpass=True)` once.

### Waiting reply with validation

```python
@command("age", help="Ask age")
async def age_handler(event):
    def validate_age(event_data):
        """Validate age is valid"""
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

### Waiting reply with callback

```python
@command("confirm", help="Confirm action")
async def confirm_handler(event):
    async def handle_confirmation(reply_event):
        text = reply_event.get_text().lower()
        
        if text in ["是", "yes", "y"]:
            await event.reply("Action confirmed!")
        else:
            await event.reply("Action canceled.")
    
    await event.reply("Confirm to execute this action? (Yes/No)")
    
    await event.wait_reply(
        timeout=30,
        callback=handle_confirmation
    )
```

### Confirmation dialog (confirm)

Wait for user confirmation or negation, automatically recognize built-in Chinese and English confirmation words:

```python
@command("confirm", help="Confirm action")
async def confirm_handler(event):
    if await event.confirm("Are you sure to execute this action?"):
        await event.reply("Confirmed, executing...")
    else:
        await event.reply("Canceled")

# Custom confirmation words
if await event.confirm("Continue?", yes_words={"go", "continue"}, no_words={"stop", "stop"}):
    pass
```

### Selection menu (choose)

Users can reply with option number or option text:

```python
@command("choose", help="Choose")
async def choose_handler(event):
    choice = await event.choose(
        "Please select a color:",
        ["red", "green", "blue"]
    )
    
    if choice is not None:
        colors = ["red", "green", "blue"]
        await event.reply(f"You selected: {colors[choice]}")
    else:
        await event.reply("Timeout, no selection made")
```

**Merge mode**: `merge_prompt=True` combines options into the prompt message, sending in a single message using the specified `method`:

```python
# Send merged prompt + options using Markdown
choice = await event.choose(
    "## Please select a color\n{options}\nPlease reply with the number",
    ["red", "green", "blue"],
    method="Markdown",
    merge_prompt=True,
)
```

> The `{options}` placeholder controls the insertion position of options; if not written, it appends to the end of the prompt. You can customize the placeholder using the `placeholder` parameter (e.g., `placeholder="[choices]"`). `options_format="auto"` (default) automatically chooses the style based on method: unordered list for Markdown, ordered list for Html, plain text list for others. For text methods (Text/Markdown/Html, etc.), options are merged by default to the end; for non-text methods (Image, etc.), options are split by default into two messages.

### Form collection (collect)

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

### Wait for any event (wait_for)

Wait for an event that meets certain conditions, not limited to the same user:

```python
@command("wait_member", help="Wait for new member")
async def wait_member_handler(event):
    await event.reply("Waiting for group member join...")
    
    evt = await event.wait_for(
        event_type="notice",
        condition=lambda e: e.get_detail_type() == "group_member_increase",
        timeout=120
    )
    
    if evt:
        await event.reply(f"Welcome new member: {evt.get_user_id()}")
    else:
        await event.reply("Timeout")
```

### Multi-turn conversation (conversation)

Create an interactive multi-turn conversation context:

```python
@command("survey", help="Questionnaire survey")
async def survey_handler(event):
    conv = event.conversation(timeout=60)
    
    await conv.say("Welcome to the survey!")
    
    while conv.is_active:
        reply = await conv.wait()
        
        if reply is None:
            await conv.say("Conversation timeout, goodbye!")
            break
        
        text = reply.get_text()
        
        if text == "Exit":
            await conv.say("Goodbye!")
            break
        
        await conv.say(f"You said: {text}, continue entering or reply 'Exit' to end")
```

### Built-in confirmation words

ErisPulse includes built-in confirmation word sets:

- **Confirmation words** (`CONFIRM_YES_WORDS`): 是, yes, y, confirm, sure, ok, true, yes, agree, no problem, ...
- **Negation words** (`CONFIRM_NO_WORDS`): no, n, cancel, no, don't, no way, cancel, false, wrong, reject, not allowed, ...

## Event Data Access

### Common methods of Event object

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
    
    # Message type judgment
    is_private = event.is_private_message()
    is_group = event.is_group_message()
    is_at = event.is_at_message()
    
    # Command information
    if event.is_command():
        cmd_name = event.get_command_name()
        cmd_args = event.get_command_args()
        cmd_raw = event.get_command_raw()
```

### Platform-specific methods

In addition to built-in methods, each platform adapter registers platform-specific methods, making it convenient to access platform-specific data.

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

If you are unsure whether a platform has registered a particular method, you can query which methods are registered for a specific platform:

```python
from ErisPulse.Core.Event import get_platform_event_methods

methods = get_platform_event_methods("telegram")
# ["get_chat_type", "is_bot_message", ...]
```

> For platform-specific methods registered by each platform, please refer to the corresponding [platform documentation](../platform-guide/).

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
    """Conditional handling - judge within the handler"""
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

> [!TIP]
> **When to read this**: If IDE completion doesn't surface an adapter's platform-specific methods (such as Yunhu's `Board`) or a module's custom methods, simply run the `epsdk types` command to generate type stubs; otherwise, skip this.

ErisPulse dynamically discovers modules/adapters via entry-points, so the concrete types of user classes cannot be known statically from entry points.
The `epsdk types` command scans installed modules/adapters and generates a type stub file, allowing users to use these types as variable annotations and thereby get IDE completion.

## Core Design Principles

Stub files **export only types** and provide no runtime instances:

- All imports are under ``TYPE_CHECKING``, **zero runtime overhead, no behavior changes**
- Type names use PascalCase form of entry-point names (e.g., ``yunhu`` → ``Yunhu``), matching the names passed to ``sdk.adapter.get()`` / ``sdk.module.get()``
- Users use ``sdk.module.get(...)`` / ``sdk.adapter.get(...)`` as usual to get instances in their code, only using imported types for **variable annotations**

## Basic Usage

Run the following command in the project root directory:

```bash
epsdk types
```

This will generate `_ep_types.py` in the current directory, containing types for all installed modules/adapters.

## Using in Code

```python
from _ep_types import MyModule, Yunhu
from ErisPulse import sdk

# By using the imported types as variable annotations, IDE will provide completion for the class's methods
my_mod: MyModule = sdk.module.get("MyModule")
my_mod.hello()                  # ← IDE completes hello

my_adapter: Yunhu = sdk.adapter.get("yunhu")
await my_adapter.Send.To("group", "123").Board(...)   # ← Completes platform-specific methods
```

## How It Works

1. Scan `erispulse.adapter` / `erispulse.module` entry-points
2. Inspect each adapter/module's actual class information (including module path and qualified name) within the target Python environment via a subprocess
3. Generate a `.py` file, where:
   - All `from xxx import Yyy as Zzz` statements are included under `TYPE_CHECKING`
   - `Zzz` is the PascalCase form of the entry-point name
4. The IDE reads the `TYPE_CHECKING` section to provide code completion; no code is executed at runtime

Example of generated stubs:

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
| `-o, --output PATH` | Specify the output file path (default: `./_ep_types.py`) |
| `--force` | Overwrite existing stub files |
| `--adapters-only` | Scan only adapters |
| `--modules-only` | Scan only modules |

## When to Regenerate

- After installing/uninstalling new modules or adapters
- After modules/adapters update their public APIs
- When IDE auto-completion fails or types are outdated

## Relationship with SendDSL Standard Methods

The `SendDSL` base class already has built-in standard sending methods (Text/Image/Voice/Video/File), and any instance of `SendDSL` obtained through any method can complete these methods.  
The `types` command is mainly used to complete **platform-specific methods** (such as `Board` for Yunhu, `Dice` for Sandbox) and **module-specific methods**.



=====
适配器开发
=====


### 适配器开发入门

# Getting Started with Adapter Development

> [!TIP]
> **When to read this**: This is the entry-point article (required reading) of the adapter development path. Everything about writing an adapter from scratch and understanding the adapter's responsibility boundaries and project structure is covered here; after finishing, move on to the [Event Converter](converter.md) and [SendDSL in Detail](send-dsl.md) as needed.

By following this guide to the end, you will have a minimal working adapter capable of receiving events and sending messages (main class + converter + Send), with a clear understanding of each component's responsibilities — all the work of integrating a new platform starts from here.

## Adapter Overview

### What Is an Adapter

An adapter is the bridge between ErisPulse and various messaging platforms, responsible for:

1. **Forward conversion**: receiving platform events and converting them into the OneBot12 standard format (Converter)
2. **Reverse conversion**: converting OneBot12 message segments into platform API calls (`Raw_ob12`)
3. Managing the connection with the platform (WebSocket/WebHook)
4. Providing a unified SendDSL message-sending interface

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
    ├── Core.py               # Adapter main class
    └── Converter.py          # Event converter
```

## Quick Start

### 1. Create Project

It is recommended to use the scaffold to generate a complete skeleton (including pyproject, main class, and converter):

```bash
# Standard project (for packaging and release)
epsdk create adapter -n MyAdapter

# Local adapter plugin (no packaging required, placed in the plugins/ directory to be automatically loaded, see "Local Development" below)
epsdk create adapter -n MyAdapter --local
```

The scaffold generates a WebSocket server skeleton by default. If the platform connection method differs, you can select a communication mode template via `--template` (generating a semi-finished base class corresponding to the mode, `start`/`shutdown` do not need to be written manually):

```bash
epsdk create adapter -n MyAdapter --template polling   # HTTP polling type (pull updates via getUpdates)
epsdk create adapter -n MyAdapter --template webhook   # HTTP callback type (platform pushes)
```

> The differences among the three connection modes and the minimum implementation of semi-finished base classes can be found at
> [Adapter Core Concepts - Semi-finished Base Classes for Connection Modes](core-concepts.md#Semi-finished Base Classes for Connection Modes).
> Complete runnable examples can be referenced in the repository `examples/example-adapter-polling/` and `examples/example-adapter-webhook/`.

Alternatively, you can create manually:

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
    "ErisPulse>=2.4.0"  # ErisPulse already includes aiohttp, usually no separate dependency required
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
# Recommended root import (2.10+): commonly used symbols are directly imported from the root package, deep paths are still compatible
from ErisPulse import BaseAdapter, BaseConfig

@dataclass
class MyAdapterConfig(BaseConfig):
    """MyAdapter Configuration"""
    api_endpoint: str = field(
        default="https://api.example.com",
        metadata={
            "description": {"i18n": "my_adapter.api_endpoint", "default": "API address"},
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
    ConfigClass = MyAdapterConfig  # Declare the configuration class, framework automatically manages it
    
    # No need to override __init__! Framework automatically handles:
    # - self.sdk / self.logger are automatically set
    # - self.cfg reads configuration in real-time
    # - self.Send / self.Request are automatically initialized
    
    def _setup_converter(self):
        from .Converter import MyPlatformConverter
        return MyPlatformConverter()
```

> ⚠️ **Regarding `__init__`**: In the new version, `BaseAdapter.__init__(self, sdk=None)` automatically handles SDK references, log initialization, and configuration loading. Most adapters **do not need to override `__init__`**. See [__init__ Notes](#init-注意事项).

> ⚠️ **Regarding `super().__init__()`**: `BaseAdapter.__init__()` is responsible for creating `Send` and `Request` factory instances. If you forget to call it, all message sending and request operations will report `AttributeError`. See [__init__ Notes](#init-注意事项).

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
        self.logger.info("Adapter has started")
    
    async def shutdown(self):
        """Shutdown the adapter (must implement)"""
        router.unregister_websocket(
            module_name="myplatform",
            path="/ws"
        )
        # Clean up connections and resources
        self.logger.info("Adapter has shutdown")
    
    async def call_api(self, endpoint: str, **params):
        """Call platform API (must implement)"""
        raise NotImplementedError("call_api needs to be implemented")
```

#### Actively Send Meta Events

The adapter should actively send meta events to let the framework track the Bot's online status. Use `emit_meta()` to complete this in one line:

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

> For detailed Bot status management and meta event explanations, see [Adapter Best Practices - Bot Status Management and Meta Events](best-practices.md#Bot-Status-Management-and-Meta-Events).

### 5. Implement Send Class

The `At`/`AtAll`/`Reply` decorators are already implemented by the framework's SendDSL base class. The adapter only needs to implement `Raw_ob12` and specific send methods.

The framework provides two key helper methods:
- `self._apply_modifiers(message)` — Automatically merges At/AtAll/Reply decorators into message segments
- `self.send_context` — Gets the send context dictionary (`target_type`, `target_id`, `account_id`)

```python
import asyncio

class MyAdapter(BaseAdapter):
    # ... other code ...

    class Send(BaseAdapter.Send):

        def Raw_ob12(self, message, **kwargs):
            """
            Send OneBot12 formatted message (must implement)

            Use _apply_modifiers to automatically merge modifier states,
            Use send_context to get send context.
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

        # Text/Image/Voice/Video/File are inherited from SendDSL base class,
        # defaulting to delegate to Raw_ob12, no need to re-implement.
        # If platform-specific logic is needed, override individual methods:
        # def Text(self, text: str):
        #     return self.Raw_ob12([{"type": "text", "data": {"text": text}}])
```

**Media Send Method Implementation Points (Image/Video/File):**

- The default implementation of the base class will encapsulate the `file` parameter as a OneBot12 message segment and pass it to `Raw_ob12`. The adapter needs to handle downloading/uploading in `Raw_ob12`
- The `file` parameter should support both `bytes` binary data and `str` URL types
- When a URL is passed, the file should be downloaded first and then uploaded to the platform
- The platform usually requires first calling the upload interface to get the file identifier, then calling the send interface

**`__getattr__` Magic Method:**

- Implement case-insensitive method names (`Text`, `text`, `TEXT` all work)
- Undefined methods should return a prompt message instead of raising an error

**`Raw_ob12` Method:**

- Convert OneBot12 standard message format to platform format for sending
- Use `self._apply_modifiers(message)` to automatically handle At/AtAll/Reply modifiers
- Use `**self.send_context` to pass send target information and account information

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

### 7. Implement Request Class (Request Operations)

If your platform supports friend requests, group invitations, and other requests that require the Bot to make decisions, you can implement the `Request` inner class:

```python
from ErisPulse import BaseAdapter, RequestDSL

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

Module developer usage:

```python
from ErisPulse import request

@request.on_friend_request()
async def handle_friend_request(event):
    # Through Event convenient method
    await event.approve()
    # Or through adapter directly
    await adapter.myplatform.Request("req_id").accept()
```

> If the platform does not support request operations, you can omit implementing the `Request` inner class. The base class defaults to returning `retcode=10002` (unsupported operation). See [Request Operation Specification](../../standards/request-action-spec.md).

### 8. Create Package Entry

```python
# MyAdapter/__init__.py
from .Core import MyAdapter
```

## Local Development (No Packaging Required)

Like modules, adapters can also be developed directly in the project's local plugin directory (default `plugins/`, configurable via `ErisPulse.framework.plugins_dir`) — **no `pip install -e .` required**:

```bash
# Generate a local adapter plugin
epsdk create adapter -n MyAdapter --local
# Generated structure:
# plugins/
# └── MyAdapter/
#     ├── __init__.py
#     ├── Core.py
#     └── Converter.py
```

At startup, the framework automatically scans the plugin directory and loads the modules and adapters within it (treated identically to entry-point installed packages: enablement state, config declarations, hot updates, and uninstall cleanup are all the same):

- **Recognition rules**: both package directories (containing `__init__.py`) and single `.py` files are accepted; a class named `Main` is recognized first, otherwise the first `BaseAdapter` / `BaseModule` subclass in the plugin is used
- **Name conflict override**: when a local plugin has the same name as an adapter installed from PyPI, the local plugin takes precedence (handy for overriding and debugging)
- **Hot reload**: plugin directory monitoring enabled via `sdk.enable_plugin_hot_reload()` also covers adapters; adapter code-level hot reload is available since 2.11 — `await sdk.adapter.reload("<platform-name>")` or `await sdk.reload_adapter("<platform-name>")` (syntax pre-check → unload and clean up → clear cache and re-import → re-register and start, with automatic rollback on failure; see the [Architecture Overview](../../architecture.md) for details)

### From Local Plugin to Release

After local verification, use the `pack` subcommand to convert the plugin into a publishable standard project in one step (interactively select the plugin, fill in the metadata, and generate a pyproject with an entry point):

```bash
epsdk create pack
# Select the plugin from the plugin directory → enter project name/description/author → the MyAdapter/ project directory is generated
cd MyAdapter
pip install -e .   # Switch to a standard installation; then follow the publishing process to upload to PyPI
```

> **Tip**: After conversion, it is recommended to remove the original from `plugins/` to avoid the local plugin and the installed package being loaded twice (when both share the same name, the local one takes precedence, which may mislead you into thinking the installed package is in effect).

## Dependency Declaration (Optional, 2.8.0+)


Adapters can declare dependencies on other adapters or modules, enabling inter-adapter coordination and optional features:

```python
from typing import ClassVar

class MyAdapter(BaseAdapter):
    # Hard dependencies: startup is skipped if missing (warning + status=skipped-dependency event)
    depends: ClassVar[dict] = {
        "adapters": ["onebot11"],   # Adapters depended on (by platform name)
        "modules": ["TranslateEngine"],  # Modules depended on (by registered name)
    }
    # Soft dependencies: missing ones do not affect startup; callbacks are received when modules load/unload (optional feature mode)
    optional_modules: ClassVar[list] = ["TranslateEngine"]
```

- **Startup order**: adapters that declare hard dependencies on modules will **defer startup until the modules finish initializing**
- **Soft dependency notifications**: when a module in `optional_modules` (or a hard module dependency) is loaded, `on_dependency_ready(module_name)` is called; when it is unloaded, `on_dependency_lost(module_name)` is called (default no-op implementations, overridable) — covering late loading and hot reload scenarios:

```python
async def on_dependency_ready(self, module_name):
    """Soft-dependency module ready: enable the corresponding optional feature"""
    if module_name == "TranslateEngine":
        self._translate = self.sdk.TranslateEngine

async def on_dependency_lost(self, module_name):
    """Soft-dependency module lost: degrade the feature"""
    if module_name == "TranslateEngine":
        self._translate = None
```

> [!NOTE]
> This feature requires ErisPulse **2.8.0+**.

## `__init__` Notes

There are three levels in adapter development where `__init__` overriding may be involved. Below is the correct approach for each level.

### 1. The BaseAdapter Level (No Override Needed in Most Cases)

`BaseAdapter.__init__(self, sdk=None)` is responsible for creating the `Send` / `Request` factory instances and automatically does the following:

- Accepts the `sdk` parameter and sets `self.sdk`, `self.logger`
- If `ConfigClass` is declared, the global configuration can be read in real time via `self.cfg`
- If `AccountConfigClass` is declared, the multi-account configuration can be read in real time via `self.accounts`

**In most cases there is no need to override `__init__`**; simply declaring `ConfigClass` is enough:

```python
class MyAdapter(BaseAdapter):
    ConfigClass = MyAdapterConfig  # Once declared, the framework manages the configuration automatically
    
    async def start(self):
        cfg = self.cfg  # Type-safe, read in real time
        ...
```

If custom initialization is truly needed, just call `super().__init__(sdk)`:

```python
class MyAdapter(BaseAdapter):
    ConfigClass = MyAdapterConfig
    
    def __init__(self, sdk=None):
        super().__init__(sdk)  # Pass in sdk
        self.converter = self._setup_converter()
        self.convert = self.converter.convert
```

### 2. The Send Inner Class (No Override Needed in Most Cases)

`SendDSL.__init__` is responsible for passing state through chained calls (target type, target ID, account, etc.). **In most cases you only need to override methods** (`Raw_ob12`, `Text`, etc.), not `__init__`.

If it is truly needed (e.g., to initialize platform-specific state), **you must pass through all parameters**:

```python
class MyAdapter(BaseAdapter):
    class Send(BaseAdapter.Send):
        # Parameters: adapter, target_type, target_id, account_id
        def __init__(self, adapter, target_type=None, target_id=None, account_id=None):
            super().__init__(adapter, target_type, target_id, account_id)  # ← must pass through
            self._my_state = None  # platform-specific initialization
```

**Why must parameters be passed through?** Every step of the chained call creates a new instance via `self.__class__(...)`:

```python
adapter.Send.To("user", "123")               # → Send(adapter, "user", "123", None)
adapter.Send.To("user", "123").Using("bot1")  # → Send(adapter, "user", "123", "bot1")
```

If the `__init__` signature does not match or `super()` is not called, the chained call will break.

### 3. The Request Inner Class (No Override Needed in Most Cases)

Same idea as Send. The parameters are `adapter`, `request_id`, `account_id`:

```python
class MyAdapter(BaseAdapter):
    class Request(RequestDSL):
        # Parameters: adapter, request_id, account_id
        def __init__(self, adapter, request_id=None, account_id=None):
            super().__init__(adapter, request_id, account_id)  # ← must pass through
            self._my_state = None  # platform-specific initialization
```

### Summary

| Level | When to Override | What Must Be Done |
|-------|------------------|-------------------|
| **BaseAdapter** | When custom initialization logic is needed | `super().__init__(sdk)` (pass in the sdk parameter) |
| **Send inner class** | When send-related state needs initialization | `super().__init__(adapter, target_type, target_id, account_id)` |
| **Request inner class** | When request-related state needs initialization | `super().__init__(adapter, request_id, account_id)` |
| All three levels | Most cases | **Just declare ConfigClass; don't touch `__init__`** |

### 9. Connection Info and Route Discovery

After the adapter registers its routes, the framework records all route information. Users can view the adapter's connection addresses through the following APIs:

```python
from ErisPulse import sdk

# Get the adapter's full connection info
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

# List routes for all namespaces (adapters/modules)
namespaces = sdk.router.list_namespaces()
# {"myplatform": {"http": ["/myplatform/webhook"], "websocket": ["/myplatform/ws"]}}

# Get the full connection URLs of a namespace
urls = sdk.router.get_module_urls("myplatform")
# {"base_url": "http://localhost:8080", "http": [...], "websocket": [...]}

# Get detailed route information of a namespace
routes = sdk.router.get_module_routes("myplatform")
# {"http": [{"path": "/myplatform/webhook", "methods": ["POST"]}],
#  "websocket": [{"path": "/myplatform/ws", "auth": false}]}
```

> **Tip**: The information returned by `get_connection_info()` is suitable for displaying to users (e.g., in a WebUI), helping them configure the platform-side callback address or WebSocket connection address. The `module_name` used at route registration must exactly match the `platform` name under which the adapter is registered in ErisPulse; otherwise route discovery will not be able to associate them correctly.

### 10. SSE (Server-Sent Events) Support

ErisPulse has built-in server-agnostic SSE support; modules and adapters can register SSE endpoints via `@sdk.router.sse()`.

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

Handlers can declare a `request` parameter to access client request information:

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
|--------|-------------|
| `sse.send(data, event=None, id=None, retry=None)` | Send an SSE event. Non-str data is automatically JSON-serialized |
| `sse.close()` | Gracefully close the SSE connection (safe to call, multiple times) |
| `sse.closed` | Whether the connection has been closed |
| `sse.request` | The underlying request object (can be used to read query params, headers) |

#### Using in RouteGroup

```python
api = sdk.router.group("MyModule", "/api", version="1")

@api.sse("/events")
async def events(sse):
    await sse.send({"msg": "hello"})
```

#### Route Discovery

SSE routes automatically appear in the route discovery APIs:

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

> **Server-agnostic design**: `SseEmitter` is decoupled from the underlying HTTP framework through callbacks. The framework provides `register_sse()` and the `@sse` decorator as a unified registration entry point, so adapters can implement SSE endpoints without directly depending on any underlying HTTP framework.



### 适配器核心概念

# Core Adapter Concepts

> [!TIP]
> **When to read this**: Mandatory for adapter development path (complete explanation of BaseAdapter / SendDSL / lifecycle mechanisms). For quick start, read [Getting Started with Adapter Development](getting-started.md) first, and return here for "why" questions.

This document explains the adapter's runtime mechanism: how AdapterManager registers and distributes events, what `BaseAdapter` does during initialization, how configuration and multiple accounts are declared—when you encounter "why should I write this way" questions while writing adapters, refer here.

## Adapter Architecture

### Component Relationships

```
Forward Conversion (Receiving Direction)                    Reverse Conversion (Sending Direction)
─────────────────                                        ─────────────────
                                                         
┌──────────────────┐                                     ┌──────────────────┐
│ Platform Native Events │                                     │ Module Constructed Message │
└────────┬─────────┘                                     └────────┬─────────┘
         │                                                          │
         ↓                                                          ↓
┌──────────────────┐   ┌──────────────────┐   ┌──────────────────┐
│                  │   │ Adapter (MyAdapter) │   │ Send.Raw_ob12()  │
│  Converter       │──→│ ┌──────────────┐ │   │ (Reverse Conversion Entry) │
│  (Event Converter) │   │ │              │ │   │                  │
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
- **Forward Conversion** (Converter): Platform native events → OneBot12 standard events, original data preserved in `{platform}_raw`
- **Reverse Conversion** (Raw_ob12): OneBot12 message segments → Platform API call, returns standard response format

## AdapterManager Adapter Manager

`AdapterManager` is the core component of ErisPulse's adapter system, responsible for managing all platform adapters' registration, startup, shutdown, and event distribution.

### Core Functions

- **Adapter Registration**: Register and manage multiple platform adapters
- **Lifecycle Management**: Control adapter startup and shutdown
- **Event Distribution**: Distribute OneBot12 standard events and platform native events
- **Configuration Management**: Manage adapter enable/disable status
- **Middleware Support**: Support OneBot12 event middleware

### Basic Usage

```python
from ErisPulse import sdk

# Register adapter (usually done automatically by Loader)
sdk.adapter.register("myplatform", MyPlatformAdapter)

# Start all adapters
await sdk.adapter.startup()

# Start specified adapter
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

#### Start Adapter

```python
# Start all registered adapters
await sdk.adapter.startup()

# Start specified platform
await sdk.adapter.startup(["platform1", "platform2"])
```

**Startup Process**:

1. Submit `adapter.start` lifecycle event
2. Submit `adapter.status.change` event (starting)
3. Parallel start each adapter
4. If startup fails, automatically retry (exponential backoff strategy)
5. After successful startup, submit `adapter.status.change` event (started)

**Retry Mechanism**:

- First 4 retries: 60 seconds, 10 minutes, 30 minutes, 60 minutes
- 5th and subsequent: Fixed interval of 3 hours

#### Shutdown Adapter

```python
# Shutdown all adapters
await sdk.adapter.shutdown()
```

**Shutdown Process**:

1. Submit `adapter.stop` lifecycle event
2. Call all adapters' `shutdown()` method
3. Shutdown routing server
4. Clear event handlers
5. Submit `adapter.stopped` lifecycle event

### Configuration Management

#### Check Platform Status

```python
# Check if platform is registered
exists = sdk.adapter.exists("myplatform")

# Check if platform is enabled
enabled = sdk.adapter.is_enabled("myplatform")

# Use in operator
if "myplatform" in sdk.adapter:
    print("Platform exists and enabled")
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

# Listen to all platforms' standard message events
@sdk.adapter.on("message")
async def handle_message(data):
    print(f"Received OneBot12 message: {data}")

# Listen to standard message events for specific platform
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
# Listen to specific platform's native events
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

**Matching Rules**:

- Exact match: `@sdk.adapter.on("message")` only matches `message` events
- Wildcard: `@sdk.adapter.on("*")` matches all events
- Platform filtering: `platform="myplatform"` only distributes events for the specified platform

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
        return None  # Returning None ignores the return value, preserving original data for further processing
    return data  # Must return data to continue passing
```

#### Middleware Return Contract

| Return Value | Behavior |
|--------|------|
| `dict` | Overwrite event payload (subsequent processors receive the modified event) |
| `None` | Pass through, payload unchanged (outputs WARNING message—recommended to explicitly `return data`) |
| `False` | **Reject**: Event is discarded, no processor is entered, no outbound side effects |

Reject is suitable for scenarios like firewall, rate limiting, blacklist, where events are discarded at the event level (previously could only be achieved using high-priority event handlers). When rejected, the framework outputs a TRACE log and triggers the `adapter.event.blocked` lifecycle hook (carrying `middleware` middleware name, full `event`, `platform` / `event_type` / `detail_type`), facilitating troubleshooting for why an event was not responded to:

```python
@sdk.adapter.middleware
async def rate_limit_middleware(data):
    """Rate limiting middleware"""
    if _is_rate_limited(data):
        return False  # Reject: event is discarded
    data["rate_marked"] = True
    return data

@sdk.lifecycle.on("adapter.event.blocked")
async def on_event_blocked(data):
    print(f"Event rejected by {data['middleware']}: {data['event_type']}")
```

#### Middleware Execution Order

Middlewares execute in the order they are registered, with later registered middlewares executing first.

> **Note**: If a middleware returns `None` (e.g., forgetting `return data`), the framework ignores the return value and preserves the original data for further processing, while outputting a warning-level log. This ensures that a single middleware's mistake does not interrupt the entire event chain.

```python
# Registration order
sdk.adapter.middleware(middleware1)  # Last to execute
sdk.adapter.middleware(middleware2)  # Middle execution
sdk.adapter.middleware(middleware3)  # First to execute

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
    # - self.cfg (type-safe configuration instance, real-time reading)
    # - self.Send, self.Request
    
    async def start(self):
        """Start adapter (must implement)"""
        cfg = self.cfg  # Automatically loaded type-safe configuration
        pass
    
    async def shutdown(self):
        """Shutdown adapter (must implement)"""
        pass
    
    async def call_api(self, endpoint: str, **params):
        """Call platform API (must implement)"""
        pass
```

### Configuration Management

The framework provides declarative configuration management, defining the configuration structure through dataclass, and automatically handling loading, validation, and template generation.

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
        "description": {"i18n": "telegram.proxy", "default": "Proxy Address"},
        "ui": {"widget": "text", "group": "advanced", "order": 10},
    })

class TelegramAdapter(BaseAdapter):
    ConfigClass = TelegramConfig
    
    async def start(self):
        cfg = self.cfg  # Type-safe, real-time reading
        if not cfg.token:
            raise ValueError("Token not configured")
        await self._connect(cfg.token, proxy=cfg.proxy)
```

#### Multi-Account Configuration

The `BotAccountConfig` base class provides `enabled` and `name` fields. Most adapters can automatically obtain `bot_id` from the platform protocol or login response, injecting it into the account configuration during event conversion:

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
    "required": bool,         # Whether it is required (validation + WebUI required mark)
    "secret": bool,           # Whether it is sensitive (WebUI displays as ***, de-sensitized in logs)
    "example": bool,          # Non-persistent flag: not written to config.toml (default values/examples excluded), only rendered into config.full.example; schema with "example": true marked, CLI configuration wizard skips by default; user manually sets then persists normally
    "min": number, "max": number,  # Numerical range validation
    "ui": {                   # WebUI control configuration (old name "webui" still compatible)
        "widget": str,        # Control type: "text" | "switch" | "select" | "number" | "password"
        "group": str,         # Group: "basic" | "advanced" | "connection" etc.
        "order": int,         # Sorting weight (smaller values appear earlier)
        "options": list,      # Options for select control [{label, value}], label supports i18n
        "placeholder": str | dict,  # Input placeholder (supports i18n)
    },
    "extra": dict,            # Additional extension fields (passed through to schema)
}
```

All user-visible text fields support i18n, uniformly using the `{"i18n": "key", "default": "text"}` format; pure strings are passed through as-is (backward compatibility). Supported i18n fields:

| Field | Location | Description |
|------|------|------|
| `description` | field metadata | Field description |
| `options[].label` | `ui.options` | Select control option labels |
| `placeholder` | `ui.placeholder` | Input placeholder |
| `group_labels` | `_schema_meta` | Group display name (Dashboard partition title) |

When using i18n, you must register the translation keys in the i18n system beforehand (see [i18n documentation](../../advanced/i18n.md#configuration-field-multilingual) for details).

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
                {"label": "Pure string label", "value": "b"},  # Pure strings passed through as-is
            ],
        },
    },
)
```

**group_labels** example (declared after configuration class definition):

```python
MyConfig._schema_meta = {
    "group_labels": {
        "basic": {"i18n": "my_adapter.group.basic", "default": "Basic Settings"},
        "advanced": {"i18n": "my_adapter.group.advanced", "default": "Advanced Settings"},
    }
}
```

The framework's `resolve_config_schema()` automatically resolves all the above fields' i18n keys based on the current language; `get_config_schema()` passes through the i18n dictionary as-is, for the frontend to parse.

#### docstring automatically generates field descriptions (v2.8.0+)

Fields without `description` declared in metadata, the framework automatically extracts field descriptions from the configuration class docstring as a fallback, supporting two common styles (can be mixed):

```python
@dataclass
class MyConfig(BaseConfig):
    """
    MyAdapter Configuration

    :ivar endpoint: Platform API address        # reST style
    :ivar timeout: Request timeout in seconds
    """

    endpoint: str = "https://api.example.com"   # No metadata description → Description taken from docstring
    timeout: int = 30

    # Google style is also supported (Attributes: section):
    # Attributes:
    #     endpoint: Platform API address
```

Priority: **metadata description > docstring field description > empty**. i18n dictionary form of description is unaffected (always prioritized).

#### Nested Configuration (v2.8.0+)

When the field type is a nested dataclass, the framework recursively processes it: the schema uses `"type": "table"` + `"fields"` subtree (WebUI renders as collapsible nested groups), TOML template renders as `[sub-table]` sections, default values / filling / validation / i18n parsing all recursively take effect.

```python
@dataclass
class RetryConfig(BaseConfig):
    """Retry Strategy

    :ivar max_retries: Maximum number of retries
    """
    max_retries: int = 3
    backoff: float = 0.5

@dataclass
class MyConfig(BaseConfig):
    """MyAdapter Configuration"""
    endpoint: str = "https://api.example.com"
    retry: RetryConfig = field(default_factory=RetryConfig)   # Nested configuration section
```

Generated TOML template:

```toml
endpoint = "https://api.example.com"

[retry]
# Maximum number of retries
max_retries = 3
backoff = 0.5
```

> For nested types, it is recommended to use direct type annotations; string annotations (e.g., for delayed evaluation scenarios) must ensure the type is globally resolvable from the configuration class's module, `__qualname__` outer class namespace, or class attributes by name.

#### Non-persistent example fields (v2.8.0+)

```python
gc_interval: int = field(default=300, metadata={"example": True})
```

Fields with `example: True`:

- Not written to config.toml (adapter/module configuration template and default values excluded, runtime uses code default values)
- Only rendered into project's `config.full.example` (for user reference, manually copy to config.toml as needed)
- Schema marked with `"example": true` (panel can decide display strategy), CLI configuration wizard skips by default
- After user manually sets this key, it persists normally, updates normally (user's explicit intent takes precedence)

Suitable for "complex but infrequently touched" advanced configuration items, keeping the user's config.toml minimal.

> ⚠️ `_schema_meta` is class-level metadata (not a configuration field). If declared within the dataclass body, it must be annotated with `ClassVar` (`_schema_meta: ClassVar[dict] = {...}`), otherwise it will be treated as a regular field by dataclass. The framework defensively excludes fields with leading underscores from any schema/template/default value/validation output, but it is still recommended to declare them properly.

### Declarative Translation Keys (v2.7.0+)

Adapters can centrally declare translation keys by nesting the `I18nClass` class, similar to declaring `ConfigClass`. The framework automatically registers all declared translation keys during `__init__` (before configuration template generation), ensuring that i18n keys referenced in configuration descriptions are available when generating the template.

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

> ``I18nKey.default`` is a language-agnostic fallback text and is not registered in any language. To make the translation effective, at least one language parameter must be explicitly passed.

For detailed usage (key path rules, explicit key parameters, etc.), see [i18n documentation](../../advanced/i18n.md#recommended-usage-declaring-translation-keys-via-i18nclass-v270).

### Declarative Event Extension Methods (v2.7.0+)

Adapters can centrally declare platform-specific event extension methods through `EventMixin`, which the framework automatically registers to the current platform.

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

After registration, event objects can directly call these methods:

```python
@message.on_group_message()
async def handler(event):
    if event.is_official_message():
        chat_name = event.get_chat_name()
        await event.reply(f"[{chat_name}] Official message received")
```

> The adapter's event extension methods are registered to its own platform (``self._platform``). Modules that need cross-platform event extensions should use the original ``register_event_mixin()`` API.

#### Account Resolution

Multi-account adapters can use `_resolve_account()` to automatically resolve the target account:

```python
async def call_api(self, endpoint: str, **params):
    account_id = params.pop("account_id", None)
    name, account = self._resolve_account(account_id)
    # name: account name, account: configuration instance
```

Resolution strategy: account name match → `bot_id` field match → other str field match → first enabled account.

#### Configuration Hot Update

Subclasses can override `on_config_update()` to respond to configuration changes:

```python
class MyAdapter(BaseAdapter):
    ConfigClass = MyConfig
    
    def on_config_update(self, old_config, new_config):
        if old_config.token != new_config.token:
            self.logger.info("Token updated, reconnecting")
```

### Initialization Process

The framework automatically performs the following tasks in `BaseAdapter.__init__(self, sdk=None)`:

1. **SDK Reference**: Set `self.sdk`, `self.logger`
2. **Send/Request Factory**: Create `self.Send` and `self.Request`
3. **Configuration Template**: If `ConfigClass` is declared, automatically generate a default configuration template (first time)
4. **Account Template**: If `AccountConfigClass` is declared, automatically generate a default account template (first time)
5. **EventMixin Registration**: If `EventMixin` is declared, automatically register to `AdapterManager` after injecting platform name

Configuration is read in real-time via `self.cfg` / `self.accounts` (each access reads the latest value from the configuration store). `self.config` as a compatibility alias for `self.cfg` is still available.

Most adapters do not need to override `__init__`. If custom initialization is required:

```python
class MyAdapter(BaseAdapter):
    ConfigClass = MyConfig
    
    def __init__(self, sdk=None):
        super().__init__(sdk)  # Pass sdk
        self.converter = self._setup_converter()
        self.convert = self.converter.convert
```

## Send Message Sending DSL

### Inheritance Relationship

```python
class MyAdapter(BaseAdapter):
    class Send(BaseAdapter.Send):
        """Send nested class, inherits from BaseAdapter.Send"""
        pass
```

### Available Attributes

The `Send` class automatically sets the following attributes when called:

| Attribute | Description | Setting Method |
|-----|------|---------|
| `_target_id` | Target ID | `To(id)` or `To(type, id)` |
| `_target_type` | Target Type | `To(type, id)` |
| `_target_to` | Simplified Target ID | `To(id)` |
| `_account_id` | Sending Account ID | `Using(account_id)` |
| `_adapter` | Adapter Instance | Automatically set |
| `_at_user_ids` | @ User List | `At(user_id)` |
| `_reply_message_id` | Reply Message ID | `Reply(message_id)` |
| `_at_all` | Whether to @ All | `AtAll()` |

> **Recommendation**: Use the `self.send_context` property to get `target_type`, `target_id`, `account_id` in one go, which is clearer than directly accessing instance variables.

### Framework Helper Methods

| Method/Attribute | Description |
|-----------|------|
| `self._apply_modifiers(message)` | Merge At/AtAll/Reply modifier states into the message segment list |
| `self.send_context` | Return a dictionary `{target_type, target_id, account_id}` |

### Basic Methods

Adapters only need to implement `Raw_ob12`, standard methods (Text/Image/Voice/Video/File) are inherited from the `SendDSL` base class and default to delegating to it:

```python
class Send(BaseAdapter.Send):
    def Raw_ob12(self, message, **kwargs):
        """Must implement: OneBot12 message segments → Platform API"""
        async def _do_send():
            segments = self._apply_modifiers(message)
            return await self._adapter.call_api(
                endpoint="/send_message",
                message=segments,
                **self.send_context,
                **kwargs
            )
        return asyncio.create_task(_do_send())

    # Text/Image/Voice/Video/File are inherited from base class, automatically delegate Raw_ob12, no need to implement repeatedly
    # If platform-specific logic is needed, override individual methods:
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
    "id": "Unique Event Identifier",
    "time": 1234567890,           # 10-digit Unix timestamp
    "type": "message/notice/request/meta",
    "detail_type": "Detailed Event Type",
    "platform": "Platform Name",
    "self": {
        "platform": "Platform Name",
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
        
        # Construct standard event
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

### Two Correct Ways to Write start()

Adapters that are client-mode (WebSocket client, HTTP polling, etc.) need to initiate a constant connection loop in `start()`. The framework supports two ways, **both are correct, but only one should be chosen**:

**Way 1: spawn-return style (recommended)**—use `spawn_client_loop()` to schedule the loop as a background task belonging to the current platform, `start()` returns immediately:

```python
class MyAdapter(BaseAdapter):
    async def start(self):
        # The loop task belongs to self._platform: automatically canceled by the framework when shutdown
        self.spawn_client_loop(self._connect_loop())
        # start ends here—“startup is successful”, connection failure handled within the loop

    async def _connect_loop(self):
        while True:
            try:
                await self._connect_and_receive()   # Disconnect throws exception → below backoff
            except asyncio.CancelledError:
                raise
            except Exception:
                await asyncio.sleep(5)              # Backoff and reconnect within the loop
```

**Way 2: Persistent style**—`start()` directly awaits the connection loop, never returns:

```python
class MyAdapter(BaseAdapter):
    async def start(self):
        await self._connect_loop()   # Persistent and never returns; loop throws exception = start failure
```

Differences and common points between the two writing styles:

| | spawn-return style | Persistent style |
|---|---|---|
| `start()` return timing | Immediately returns after launching the loop | Returns when the connection loop exits/fails (framework retries according to the backoff strategy) |
| Connection failure handling | Exception caught and backoff within the loop | Exception thrown up, handed over to the framework's retry chain |
| Suitable scenarios | Need to quickly return startup confirmation (multiple connections, register routes and then launch other tasks) | "Connection is startup" semantic simple implementation |

`spawn_client_loop(coro, *, name="client_loop")` is the entry point for way 1: the task is registered according to `self._platform`, when the adapter `shutdown()` the framework automatically cancels it, no need to manage task handles yourself; uncaught exceptions within the loop are automatically logged (for expected disconnects and reconnects, please catch them within the loop).

> **The only incorrect writing style is mixing**: spawning and then awaiting the same loop—this causes `start()` to lose its immediate return semantics, and the task cancellation path becomes unpredictable.

### Semi-finished Base Classes for Connection Patterns

In addition to the two writing styles mentioned above, the most common two connection patterns are directly provided by the framework as "semi-finished" base classes (`ErisPulse.Core.Bases.adapter_patterns`, the root package can be directly imported): `start`/`shutdown` lifecycle orchestration is fully handled by the base class, and the subclass only implements business hooks.

#### PollingAdapter (HTTP Polling Type)

Applicable to platforms that "periodically pull events from the client" (like Telegram's getUpdates type). The base class uses the spawn-return style to launch a constant polling loop, automatically logs failures and backoffs exponentially (base 1 second, upper limit 60 seconds, resets to zero on success; constants `POLLING_ADAPTER_BACKOFF_BASE_SECS` / `POLLING_ADAPTER_BACKOFF_MAX_SECS` can be adjusted in `Core/constants.py`):

```python
from ErisPulse import PollingAdapter

class MyAdapter(PollingAdapter):
    # Polling interval defaults to 5 seconds; if ConfigClass declares a poll_interval field, use the configured value (hot updates take effect)
    poll_interval = 5.0

    async def fetch_events(self):
        """Pull a batch of platform native events (exceptions handled by the base class, no need for try/except)"""
        resp = await self.sdk.client.get(f"{self.cfg.endpoint}/getUpdates")
        data = await resp.json()
        return data.get("result", [])

    def convert_one(self, raw):
        """Convert a single native event to OneBot12; return None to skip"""
        return self.converter.convert(raw)

    async def call_api(self, endpoint: str, **params):
        ...  # Same as ordinary adapters
```

Minimum implementation surface: `fetch_events` / `convert_one` / `call_api`. `start()` launches the loop and returns immediately; `shutdown()` does not require subclass handling (the polling loop is automatically canceled according to owner affiliation).

#### WebhookAdapter (HTTP Callback Type)

Applicable to platforms that "push callbacks from the platform." The base class's `start()` registers the receiving route on the framework router (final path `/{platform name}/webhook`, POST method), registered in `owner_scope`—the adapter unloads automatically clean up according to owner, no need to manually deregister:

```python
from ErisPulse import WebhookAdapter

class MyAdapter(WebhookAdapter):
    def verify_request(self, request) -> bool:
        """Optional hook: callback verification (default allows; return False to reject by base class with 403)"""
        cfg = self.cfg
        if not cfg.token:
            return True
        auth = request.headers.get("authorization", "")
        return auth == f"Bearer {cfg.token}"

    def convert(self, payload):
        """Convert callback payload to OneBot12; return None to skip"""
        return self.converter.convert(payload)

    async def call_api(self, endpoint: str, **params):
        ...  # Same as ordinary adapters
```

Minimum implementation surface: `convert` / `call_api` (`verify_request` is optional). The callback address is queried via `sdk.adapter.get_connection_info(platform)` and filled into the platform backend; requests with failed verification return 403, payload parsing failures return 400, normal returns return `{"status": "ok"}`.

#### How to Choose Three Modes

| Platform Protocol | Inherit | Scaffold |
|---|---|---|
| Platform connects (WebSocket server) | `BaseAdapter` | `epsdk create adapter` (default ws-server) |
| We pull (HTTP polling) | `PollingAdapter` | `epsdk create adapter --template polling` |
| Platform pushes (HTTP callback) | `WebhookAdapter` | `epsdk create adapter --template webhook` |

Complete runnable examples are available in the repository `examples/example-adapter/` (ws-server), `examples/example-adapter-polling/`, `examples/example-adapter-webhook/`.

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

> Pure callback-type platforms don't need to manually write this registration/verification/cleanup orchestration—simply inherit the [`WebhookAdapter` semi-finished base class](#connection-pattern-semi-finished-base-class) and only implement `convert` (optionally override `verify_request`).

> **Route information query**: The routes registered by adapters (HTTP, WebSocket, SSE) can be queried via `sdk.adapter.get_connection_info(platform)` and `sdk.router.get_module_urls(module_name)`, including `base_url` + path. See [Getting Started with Adapter Development - Connection Information and Route Discovery](getting-started.md#9-connection-information-and-route-discovery) and [SSE Support](getting-started.md#10-sse-server-sent-events-support).

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

### Manually Construct Response (Old Method Still Compatible)

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

After declaring `AccountConfigClass`, the framework automatically manages multi-account loading, validation, and template generation:

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
        # Use account.token, account.bot_id, etc.
```

### Account Configuration File

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

### Specify Account for Sending

```python
# Use Using method to specify account
my_adapter = adapter.get("myplatform")

# Use self.user_id from event (recommended, most universal)
await my_adapter.Send.Using(event["self"]["user_id"]).To("user", "123").Text("Hello")

# Use account name
await my_adapter.Send.Using("account1").To("user", "123").Text("Hello")
```

### Relationship between self.user_id and Using

The framework's event reply mechanism automatically extracts `account_id` (prioritized) or `user_id` from the event's `self` field as the `Using` parameter. Adapter developers need to ensure that the Converter correctly sets `self.user_id` to match `_resolve_account`.

**Framework Internal Behavior**:

```python
# Framework extraction logic for bot_id
bot_id = self.get("self", {}).get("account_id", "") or self.get("self", {}).get("user_id", "")

# Only call Using if bot_id is non-empty
if bot_id:
    send_chain = send_chain.Using(bot_id)
```

> **Key Point**: Even if the adapter only uses a single Bot configuration, as long as the Converter correctly sets `self.user_id`, the framework will pass it as the `Using` parameter. The adapter needs to ensure that `self.user_id` matches the identifier field (such as `bot_id`) in `AccountConfigClass`, so that `_resolve_account()` can match the correct account. If `self.user_id` is empty, the framework will not call `Using`, and `call_api` will receive `account_id` as `None`, with `_resolve_account(None)` returning the first enabled account.

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
        # Recommended to use SDK built-in client
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
        self.logger.error(f"Request timeout: {endpoint}")
        return self._error_response("Request timeout", 32000)
    except ClientError as e:
        self.logger.error(f"Network error: {e}")
        return self._error_response("Network request failed", 33000)
    except Exception as e:
        self.logger.error(f"Unknown error: {e}")
        return self._error_response(str(e), 34000)
```

> **Backward Compatibility**: Code for old adapters using `aiohttp.ClientSession` is unaffected and can still catch `aiohttp.ClientError`. Both methods can coexist. New code is recommended to use `sdk.client` + ErisPulse exception system.

## Bot Status Management

AdapterManager includes a built-in Bot status tracking system that automatically maintains the online status, active time, and metadata of all registered Bots.

### Automatic Discovery Mechanism

When the adapter emits an event via `adapter.emit()`, the framework automatically checks the `self` field in the event:

- **Meta Events**: Perform corresponding operations based on `detail_type` (register on connect, mark as offline on disconnect, update active time on heartbeat)
- **Regular Events** (message/notice/request): Automatically discover Bot and update active time

```python
# All events with self field trigger automatic discovery
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
| `connect` | Bot connects | Register Bot and trigger `adapter.bot.online` lifecycle event |
| `disconnect` | Bot disconnects | Mark Bot as offline and trigger `adapter.bot.offline` lifecycle event |
| `heartbeat` | Bot heartbeat | Update Bot active time and metadata |

### Adapter Sending Meta Events

Sending methods (one-line `emit_meta()`, heartbeat events, and manually constructed format) are detailed in [Adapter Best Practices - Bot Status Management and Meta Events](best-practices.md#bot-status-management-and-meta-events).

### `self` Field Extended Information

In addition to the required `platform` and `user_id`, the `self` field supports the following optional fields:

| Field | Description |
|---|---|
| `user_name` | Bot username |
| `nickname` | Bot nickname |
| `avatar` | Bot avatar URL |
| `account_id` | Multi-account identifier |

### Bot Status Query

Query APIs (`get_bot_info()` / `list_bots()` / `is_bot_online()` / `get_status_summary()`) are detailed in [Adapter System API - Bot Status Management](../../api-reference/adapter-system.md#bot-status-management).

### Listening to Bot Lifecycle

Event tables and listening examples for `adapter.bot.online` / `adapter.bot.offline` lifecycle events are detailed in [Adapter System API - Bot Status Management](../../api-reference/adapter-system.md#bot-status-management).



### SendDSL 详解

# SendDSL Detailed Explanation

> [!TIP]
> **When to read this**: This is a must-read for adapter development paths (Send DSL). If not needed, you can skip it without affecting the use of other features.

SendDSL allows message sending to be completed as a chain: specify the target, @ / reply, retry / timeout / delay, batch sending, all accomplished with a single chained call. This article covers the sending methods, modifier methods, sending rules, and the internal mechanism of the sending chain.

## Basic Calling Methods

### 1. Specify Type and ID

```python
await adapter.Send.To("group", "123").Text("Hello")
```

### 2. Specify ID Only

```python
await adapter.Send.To("123").Text("Hello")
```

### 3. Specify Sender Account

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
    A["Using / Account<br/>（Optional sender account, optional）"] --> B["To<br/>（Optional target type and ID）"]
    B --> C["Modifier Methods<br/>At / Reply / Expire / ForMember, etc."]
    C --> D["Sending Methods<br/>Text / Image / Voice / Raw_ob12"]
    D --> E["Returns asyncio.Task"]
```

## Sending Methods

All sending methods return an `asyncio.Task` object.

### Basic Methods (Built-in in Base Class)

The following standard methods are implemented by the `SendDSL` base class. By default, they are delegated to `Raw_ob12`, so adapter subclasses do not need to re-implement them and can use them directly, with IDE auto-completion available:

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
        # Must be implemented
        ...

    # Optional: Override Text to provide platform-specific logic
    # def Text(self, text: str):
    #     return self.Raw_ob12([{"type": "text", "data": {"text": text}}])
```

### Protocol Methods

| Method Name | Description | Return Value | Required |
|-------------|-------------|--------------|----------|
| `Raw_ob12(message)` | Send OneBot12 formatted message | `asyncio.Task` | **Must be implemented** |

> **Important**: `Raw_ob12` is the core method of the adapter and **must be implemented**. It serves as the unified entry point for reverse transformation (OneBot12 → platform). If not implemented, the base class will log an error and return a standard error response (`status: "failed"`, `retcode: 10002`). Standard methods (`Text`, `Image`, etc.) are delegated to `Raw_ob12` by default.

### Platform-Specific Methods

Adapters can add platform-specific sending methods in the `Send` subclass (these will be recognized by `event.supports()` / `event.available_methods()`):

```python
class Send(SendDSL):
    def Raw_ob12(self, message, **kwargs): ...

    # Platform-specific method
    def Sticker(self, sticker_id: str):
        return self.Raw_ob12([{"type": "sticker", "data": {"id": sticker_id}}])
```

## Modifiers

Modifiers return `self` to support method chaining.

### At Method

```python
# @single user
await adapter.Send.To("group", "123").At("456").Text("Hello")

# @multiple users
await adapter.Send.To("group", "123").At("456").At("789").Text("Hello everyone")
```

### AtAll Method

```python
# @all group members
await adapter.Send.To("group", "123").AtAll().Text("Hello everyone")
```

### Reply Method

```python
# Reply to a message
await adapter.Send.To("group", "123").Reply("msg_id").Text("Reply content")
```

### Combined Modifiers

```python
await adapter.Send.To("group", "123").At("456").Reply("msg_id").Text("Reply to the @ message")
```

### Platform-Specific Modifier Methods

In addition to the built-in `At`/`AtAll`/`Reply`, adapters can define **platform-specific modifier methods**. These methods **only need to return `self`** and do not require any decorators — the framework automatically recognizes them:

- Return `self` (an instance of `SendDSL`) → Modifier method, does not trigger send wrapping/lifecycle events, continues method chaining
- Return `Task`/`Awaitable` → Send method

```python
class Send(SendDSL):
    def Raw_ob12(self, message, **kwargs): ...

    # Modifier method: returns self, does not send
    def Expire(self, seconds: int):
        self._expire = seconds
        return self

    def ForMember(self, user_id: str):
        self._member = user_id
        return self

    # Send method: returns Task, depends on states set by modifier methods
    def Board(self, content: str, **kwargs):
        return self.Raw_ob12([{"type": "board", "data": {"text": content}}])
```

Usage:

```python
# Modifier methods can be chained continuously
await adapter.Send.To("group", "big").Expire(3600).ForMember("114").Board("Board content")
```

## Using Modifier Methods in Event Wrapper Classes

> [!NOTE]  
> The `reply(via=)` and `event.send_chain()` features require ErisPulse **2.7.0+**.

By default, `event.reply()` exposes only built-in modifier parameters such as `at_sender`/`at_users`/`at_all`/`quote`. To use platform-specific modifier methods, there are two approaches:

### Method 1: The `via` Parameter in `reply()`

Suitable for a small number of known modifier methods:

```python
await event.reply("Board content", method="Board",
                  via=[("Expire", 3600), ("ForMember", "114514")])
```

The `via` parameter is a list, where each element can take one of the following forms:

| Format | Equivalent Chain Call |
|--------|------------------------|
| `"Name"` | `.Name()` |
| `("Name", arg1, arg2)` | `.Name(arg1, arg2)` |
| `("Name", (arg1,), {kw: val})` | `.Name(arg1, kw=val)` |

### Method 2: `event.send_chain()`

Suitable for **multiple consecutive modifier methods** or **action-type methods without content parameters** (such as recall or delete). The `send_chain()` method returns a send chain already configured with `To`/`Using`, allowing you to freely append arbitrary modifier methods and send methods:

```python
# Platform-specific modifier methods + board message
await event.send_chain().Expire(3600).Board("Expires in one hour")

# Multiple consecutive modifier methods
await (event.send_chain()
       .Expire(3600)
       .ForMember("114514")
       .Board("Board content", content_type="markdown"))

# Built-in modifier methods are also available
await event.send_chain().At("123").Reply("msg_id").Text("hi")

# Action-type methods without content parameters
await event.send_chain().DismissBoard()
```

> The `send_chain()` method returns a complete SendDSL instance, so **all chainable features are available**—not just modifier methods, but also send rules and batch building:

```python
# Send rules: retry + timeout + success callback
await (event.send_chain()
       .Retry(3).Timeout(10)
       .Hook(lambda r: print("Message sent successfully"))
       .Text("Reliable message"))

# Delayed message + platform modifier + board
await event.send_chain().Defer(5).Expire(3600).Board("Delayed board")

# Batch building mode
results = await (event.send_chain()
                 .Build()
                 .Text("First sentence").Image("pic.jpg").Text("Second sentence")
                 .send_all())
```

## Account Management

### Using Method

The `Using()` method is used to specify the account for sending messages. The identifier passed in will be matched through `_resolve_account()` in the following priority order:

1. **Account Name** — The key name in the configuration (e.g., `"default"`, `"bot1"`)
2. **Runtime Injected bot_id** — The identifier automatically injected during event conversion
3. **Any str Field** — Any other string field in the configuration
4. **Fallback** — The first enabled account

```python
# Using account name
await adapter.Send.Using("account1").To("user", "123").Text("Hello")

# Using bot_id (i.e., self.user_id from the event)
await adapter.Send.Using("bot_123").To("user", "123").Text("Hello")
```

### Account Method

The `Account` method is equivalent to `Using`:

```python
await adapter.Send.Account("account1").To("user", "123").Text("Hello")
```

## Asynchronous Processing

### Not Waiting for Results

```python
# Message is sent in the background
task = adapter.Send.To("user", "123").Text("Hello")

# Continue executing other operations
# ...
```

### Waiting for Results

```python
# Await directly to get the result
result = await adapter.Send.To("user", "123").Text("Hello")
print(f"Send result: {result}")

# Save the Task first, then wait later
task = adapter.Send.To("user", "123").Text("Hello")
# ... other operations ...
result = await task
```

## Send Rule System

SendDSL includes a built-in set of send rule decorators. Rules are attached via chainable methods and applied collectively when the final send operation is executed. These rules cover common production scenarios: timeout control, retry on failure, success callbacks, delayed sending, priority-based dropping, and progress monitoring.

Rule methods **return self** (like `At`/`AtAll`/`Reply`), and must be called before the send method (`Text`/`Image`, etc.). Rules propagate along with new instances created by `To`/`Using`/`Account`.

### List of Rule Methods

| Method | Description |
|--------|-------------|
| `.Hook(callback)` | Callback executed on successful send (can be called multiple times, executed in order) |
| `.Retry(times=1)` | Automatically retry N times on failure (total N+1 attempts, including the first) |
| `.Timeout(seconds)` | Single send timeout; cancels current attempt if exceeded (can be combined with Retry) |
| `.Defer(seconds=1.0)` | Delayed send (in-process timer, not persisted) |
| `.Priority(level, drop_if_busy=False)` | Set priority; messages may be dropped during congestion |
| `.OnProgress(callback)` | Progress callback at each stage (receives `SendContext`) |
| `.OnError(callback)` | Error callback triggered only once on final failure |

### Executing Logic After Successful Send (Hook)

```python
# Synchronous callback
await (adapter.Send.To("user", "123")
       .Hook(lambda r: print(f"Send successful, message ID: {r['message_id']}"))
       .Text("Hello"))

# Asynchronous callback
async def deduct_points(result):
    await db.update(user_id="123", points=-1)

await adapter.Send.To("user", "123").Hook(deduct_points).Text("Deduct points")
```

The `Hook` is only executed when the send operation is ultimately successful (including after retries); it is not triggered on failure, timeout, or cancellation.

### Automatic Retry on Failure (Retry)

```python
# Retry 2 times after the first failure, for a total of 3 attempts
result = await adapter.Send.To("user", "123").Retry(2).Text("With retry")
```

Retry is triggered when an exception is thrown during send, when the send times out, or when the send returns a response with `status == "failed"`.

### Automatic Cancellation on Timeout (Timeout)

```python
# Cancel if a single send exceeds 10 seconds
await adapter.Send.To("user", "123").Timeout(10).Text("With timeout")

# Timeout + Retry: Each attempt lasts up to 10 seconds, with a maximum of 3 attempts
await adapter.Send.To("user", "123").Timeout(10).Retry(2).Text("Timeout retry")
```

### Progress Monitoring (OnProgress / OnError)

```python
def on_progress(ctx):
    print(f"Stage: {ctx.stage}, Attempt: {ctx.attempt + 1}/{ctx.max_attempts}, Elapsed: {ctx.elapsed:.2f}s")
    if ctx.stage == "failed":
        print(f"  Error: {ctx.error!r}")

async def on_error(ctx):
    await notify_admin(f"Failed to send to {ctx.target_id}: {ctx.error!r}")

await (adapter.Send.To("user", "123")
       .Retry(3).Timeout(10)
       .OnProgress(on_progress)
       .OnError(on_error)
       .Text("Monitored"))
```

`SendContext` includes the following fields: `task_id`, `platform`, `method`, `target_type`, `target_id`, `bot_id`, `stage`, `attempt`, `max_attempts`, `started_at`, `finished_at`, `elapsed`, `error`, `result`, `extra`.

Possible values for `stage`: `pending`, `sending`, `retrying`, `success`, `failed`, `timeout`, `cancelled`, `dropped`.

### Delayed Sending (Defer)

```python
# Send after a 5-second delay
await adapter.Send.To("user", "123").Defer(5).Text("Delayed message")
```

> Note: The delay is an in-process timer; it is not persisted and will be lost if the process restarts.

### Priority and Congestion Dropping (Priority)

```python
# Low-priority message, automatically dropped during queue congestion
result = await (adapter.Send.To("user", "123")
               .Priority(-1, drop_if_busy=True)
               .Text("Droppable notification"))
# If dropped, result["status"] == "failed"
```

When `drop_if_busy` is enabled, if the number of in-flight send tasks exceeds the threshold (default 64), the current send is immediately abandoned. The global threshold can be adjusted using `.PriorityThreshold(n)`.

### Rule Composition and Background Execution

```python
# Execute without blocking the main flow; rules still apply
task = (adapter.Send.To("user", "123")
        .Hook(lambda r: print("Send successful!"))
        .Retry(3)
        .Timeout(10)
        .OnProgress(on_progress)
        .Text("Hello"))

# Continue executing other operations
await handle_next_action()
```

### Rule Propagation

Rules propagate with new instances created by `To`/`Using`/`Account`, preventing loss of rules during chained calls:

```python
# Rules set before To are also propagated to the instance created by To
builder = adapter.Send.Retry(3).Timeout(10)
send = builder.To("user", "123")  # send still carries Retry(3) and Timeout(10)
await send.Text("hi")
```

Rule sets for multiple instances are independent (the hooks list is deeply copied).

## Batch Build Mode (Build)

In addition to the single-send mode, SendDSL also supports batch build mode: multiple send methods are written in a single chain, and executed at once. This is suitable for scenarios where you want to send multiple messages in one go.

### Entering Build Mode

Before calling a send method, call `.Build()`, which returns a `SendBuilder`. After this, send methods (such as Text/Image) will not be executed immediately, but will accumulate as send intents:

```python
results = await (adapter.Send.To("user", "123")
                 .Build()                    # Enter build mode
                 .Text("First sentence")
                 .Image("pic.jpg")
                 .Text("Second sentence")
                 .send_all())                 # Execute all at once
# results = [Text result, Image result, Text result]
```

`.send_all()` returns an `asyncio.Task`, and awaiting it yields a list of results (in the order of the intents).

### Parallel vs Sequential

By default, execution is **parallel** (concurrent sending, total time is approximately equal to the slowest message). To ensure the order of message arrival, call `.Sequential()`:

```python
# Sequential: Send in order
await (adapter.Send.To("group", "456")
       .Build()
       .Sequential()
       .Text("Send this first").Text("Then send this")
       .send_all())

# Parallel (default, can be explicitly called)
await (adapter.Send.To("group", "456")
       .Build()
       .Parallel()
       .Text("Parallel 1").Text("Parallel 2")
       .send_all())
```

### Continue on Failure and Retry

Batch execution uses a **continue on failure** strategy: if one message fails, it does not interrupt the sending of other messages. When combined with `.Retry()`, failed messages will automatically retry (retry applies to individual messages, not the entire batch):

```python
await (adapter.Send.To("user", "123")
       .Build()
       .Retry(2)                       # Each message retries 2 times
       .Text("May fail").Image("May also fail")
       .send_all())
```

### Batch-wide Rules and Callbacks

Rules apply uniformly to the entire batch:

| Method | Description |
|--------|-------------|
| `.Timeout(seconds)` | Timeout for each individual send |
| `.Retry(times)` | Each send retries individually (continue on failure) |
| `.Defer(seconds)` | Delay the entire batch |
| `.Hook(callback)` | Triggered after the entire batch succeeds, receives `results` list |
| `.OnError(callback)` | Triggered when the batch has failures, receives `BatchContext` |
| `.OnProgress(callback)` | Triggered when each message completes, receives `BatchContext` |

```python
def on_progress(ctx):
    print(f"Progress: {ctx.completed}/{ctx.total}, succeeded {ctx.succeeded}, failed {ctx.failed}")

async def on_error(ctx):
    print(f"There are {ctx.failed} failed messages in the batch")

results = await (adapter.Send.To("user", "123")
               .Build()
               .Retry(2).Timeout(10)
               .OnProgress(on_progress)
               .OnError(on_error)
               .Hook(lambda rs: print("Batch completed"))
               .Text("a").Text("b").Text("c")
               .send_all())
```

`BatchContext` contains: `task_id`, `total`, `completed`, `succeeded`, `failed`, `stage`, `results`, `errors`, `elapsed`, `extra`.

`stage` possible values: `pending`, `sending`, `success` (all succeeded), `partial` (partially succeeded), `failed` (all failed).

### Decorators and Rule Inheritance

Decorators and rules before `.Build()` are inherited by the entire batch and apply to each message:

```python
await (adapter.Send.To("group", "456")
       .At("789")                        # Inherited: each message @789
       .Build()
       .Retry(2)                         # Inherited + appended: each message retries individually
       .Text("@Your notification")
       .Image("Announcement image")
       .send_all())
```

After entering Build mode, you can still append decorators (applying to the entire batch):

```python
await (adapter.Send.To("group", "456")
       .Build()
       .At("111").At("222")             # Appended @, applies to entire batch
       .Text("@Multiple people")
       .send_all())
```

### Background Execution

As with single-send, `.send_all()` returns a Task, which can be executed in the background without awaiting:

```python
task = (adapter.Send.To("user", "123")
        .Build()
        .Hook(lambda rs: print("Batch send completed"))
        .Text("a").Text("b")
        .send_all())

# Non-blocking main flow
await do_something_else()
```

## Naming Convention

### PascalCase Naming

All send methods should use the PascalCase naming convention:

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

### Platform-specific Methods

Avoid adding platform prefixes to methods:

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

## Internal Decomposition of the Send Chain

Behind a single `await adapter.Send.To("group", "123").Text("x")`, the framework performs the following sequence of operations for you:

```mermaid
flowchart TD
    A["adapter.Send.To(...).Text(...)"] --> B["Chain methods To/Using<br/>Each returns a new immutable instance (order doesn't matter)"]
    B --> C["__getattribute__ intercepts send methods<br/>Wraps with a rule wrapper"]
    C --> D["Calls the original method (e.g. Text)<br/>Internally delegates to Raw_ob12"]
    D --> E["Raw_ob12 returns asyncio.create_task(...)"]
    E --> F["Write [Send] log"]
    F --> G["emit message.sending (fire-and-forget)"]
    G --> H{"Is a send rule declared?"}
    H -->|"No"| I["Task done_callback → emit message.sent"]
    H -->|"Yes"| J["apply_send_rules wraps into an outer Task<br/>Retry/timeout/delay/priority"]
    J --> I
    I --> K["await receives a standard response dict"]
```

**What the framework does at each step:**

| Phase | What the framework does |
|------|-------------|
| Chain merging | `To`/`Using`/`Account` each call **creates a new immutable instance** and inherits previously set fields, so `To(...).Using(...)` and `Using(...).To(...)` are **equivalent** and order doesn't matter |
| Method wrapping | Send methods (`Text`, etc.) are intercepted and wrapped by `__getattribute__`; modifier methods (`To`/`Using`/`At`/`Retry`, etc.) are **not wrapped**. Nested `Raw_ob12` calls are prevented from repeated wrapping using the `_in_rule_wrap` marker |
| Task creation | `Raw_ob12` internally uses `asyncio.create_task()` to create the Task; `Text()` only synchronously returns this Task, **without blocking** |
| Send logging | Writes `[Send] platform/method -> target` event log (can be suppressed with `exclude_levels=["EVENT"]`) |
| `message.sending` | Triggered immediately in a fire-and-forget manner when the send method is called (only if listeners exist, short-circuited by `has_handlers`) |
| `message.sent` | Bound to the Task's `done_callback` — **when rules are present, it covers the final result of the entire retry process**; without rules, it is simply the completion of the original Task |

### Account Resolution Fallback Chain

When the adapter internally calls `_resolve_account(account_id)`, it resolves to a specific account in the following order:

1. Single-account adapter (no `AccountConfigClass`) → directly returns
2. Exact match of account name `account_id`
3. Match of each account's `bot_id` field
4. Match of any `str` field value in each account (excluding `enabled`/`name`)
5. Fallback to the first enabled account
6. If all fail → raises `ValueError`

> The `account_id` you provide comes from: `Using()` explicitly specified > event `self` field (where `account_id` takes precedence over `user_id`, automatically injected by `event.reply()`) > unspecified (adapter falls back to the first enabled account).

### Send Rule Engine (Retry/Timeout/Delay)

Rules are wrapped into a new outer Task **after** `Raw_ob12` returns the Task, without affecting the main flow. Key facts:

| Rule | Description |
|------|------|
| `Retry(n)` | Total attempts: `n+1`; **immediate re-send after failure, no exponential backoff** |
| `Timeout(s)` | Single send times out and is cancelled (`asyncio.wait_for`), retries if not exhausted |
| `Defer(s)` | Delays sleep before sending |
| `Priority(level, drop_if_busy)` | If backlog exceeds threshold, directly returns `{status:"failed", retcode:10002, message:"dropped_low_priority"}` |
| `Hook(fn)` | Only executed in order when the final send is successful |
| `on_progress` / `on_error` | Callbacks at each stage / final failure |

> **Note**: Retries are "immediate re-sends" without any backoff interval; if platform rate limiting requires backoff, please manually sleep and re-send in the `on_error` callback. Rule success is determined by `status == "ok"` in the returned dict (where `retcode == 0`).

> For the complete semantics of the standard response format and `retcode`, see [API Response Specification](../../standards/api-response.md).

## Return Values

### Task Object

All send methods return an `asyncio.Task`. The adapter only needs to implement `Raw_ob12`, and the standard methods (Text/Image, etc.) are delegated by default:

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

# Text/Image/Voice/Video/File are inherited from the base class and automatically delegated to Raw_ob12
# If you need to override standard methods, just return an asyncio.Task:
# def Text(self, text: str):
#     return self.Raw_ob12([{"type": "text", "data": {"text": text}}])
```

### Standardized Response

`call_api` should return a standardized response. It is recommended to use the `make_response()` / `make_error()` methods:

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

Manual construction is also supported (the old way is still compatible):

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

# Send text message
await my_adapter.Send.To("user", "123").Text("Hello World!")

# Send image
await my_adapter.Send.To("group", "456").Image("https://example.com/image.jpg")

# Send file
with open("document.pdf", "rb") as f:
    await my_adapter.Send.To("user", "123").File(f.read())
```

### Chained Calls

```python
# @user + reply
await my_adapter.Send.To("group", "456").At("789").Reply("msg123").Text("Reply to @ message")

# @all + multiple modifiers
await my_adapter.Send.Using("bot1").To("group", "456").AtAll().Text("Announcement message")
```

### Raw Messages and Message Building

`Raw_ob12` is the core entry point for reverse conversion (OneBot 12 message segments → platform API calls), and `MessageBuilder` is a chainable message segment builder designed to work with it.

> For the complete `Raw_ob12` implementation specification, `MessageBuilder` usage, and code examples, please refer to:
> - [Send Method Specification §6 Reverse Conversion Specification (OneBot 12 → Platform)](../../standards/send-method-spec.md#6-反向转换规范onebot12--平台)
> - [Send Method Specification §11 MessageBuilder](../../standards/send-method-spec.md#11-消息构建器-messagebuilder)



### 适配器开发最佳实践

# Adapter Development Best Practices

> [!TIP]
> **When to read this**: After the adapter skeleton is working, it is recommended to read this section (engineering best practices). Skip if not needed, as it does not affect the use of other features.

This document summarizes engineering conventions for adapter development: Bot status reporting, connection retry and heartbeat, multi-account parsing, and standardized error responses. Following these practices can help avoid common platform integration issues such as undetected disconnections, sending messages to the wrong account, and difficult-to-locate errors.

## Bot Status Management and Meta Events

The adapter should actively send meta events using `adapter.emit()` to allow the framework to automatically track the Bot's connection status, online/offline events, and heartbeat information.

### 1. When to Send Meta Events

| Event | `detail_type` | Trigger Timing | Framework Behavior |
|-------|---------------|----------------|--------------------|
| Connect | `"connect"` | When the Bot establishes a connection with the platform | Register the Bot, trigger the `adapter.bot.online` lifecycle event |
| Disconnect | `"disconnect"` | When the Bot disconnects from the platform | Mark the Bot as offline, trigger the `adapter.bot.offline` lifecycle event |
| Heartbeat | `"heartbeat"` | Regularly (recommended 30-60 seconds) | Update the Bot's active time and metadata |

### 2. Sending Meta Events

The framework provides the `emit_meta()` method to send meta events in a single line:

```python
class MyAdapter(BaseAdapter):
    async def _ws_handler(self, websocket):
        bot_id = self._get_bot_id()

        # Bot online: send connect event in one line
        await self.emit_meta("connect", bot_id, user_name="MyBot", nickname="我的机器人")

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

You can also manually construct a standard meta event (the old method is still compatible):

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

The adapter should regularly send heartbeat events during the connection's active period to update the Bot's active time:

```python
class MyAdapter(BaseAdapter):
    async def _heartbeat_loop(self, bot_id: str):
        while self._connected:
            # Send meta heartbeat to the framework (one line)
            await self.emit_meta("heartbeat", bot_id)
            await asyncio.sleep(30)
```

### 4. Automatic Discovery of `self` Field

The framework's `adapter.emit()` automatically processes the `self` field in all events (not just meta events):

- **Normal events** (`message/notice/request`) with a `self` field will be automatically discovered and registered as a Bot
- **Extended `self` field information**: Supports optional fields such as `user_name`, `nickname`, `avatar`, and `account_id`

```python
# Including the `self` field in the converter will automatically register the Bot
onebot_event = {
    "type": "message",
    "detail_type": "private",
    "platform": "myplatform",
    "self": {
        "platform": "myplatform",
        "user_id": "bot123",
        "user_name": "MyBot",
        "nickname": "我的机器人",
    },
    # ... other fields
}
await self.adapter.emit(onebot_event)
# Bot "bot123" is automatically registered and its active time is updated
```

### 5. Bot Status Query

The query APIs (`get_bot_info()` / `list_bots()` / `is_bot_online()` / `get_status_summary()`) and the Bot lifecycle event table are available at [Adapter System API - Bot Status Management](../../api-reference/adapter-system.md#bot-状态管理).

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
                        f"Connection failed, retrying in {wait_time} seconds ({retry_count}/{max_retries}): {e}"
                    )
                    await asyncio.sleep(wait_time)
                else:
                    self.logger.error("Connection failed, maximum retry attempts reached")
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

The adapter's heartbeat should perform two tasks simultaneously: sending a heartbeat keepalive to the platform and sending a meta heartbeat event to the framework.

```python
class MyAdapter(BaseAdapter):
    async def start(self):
        self.connection = await self._connect_to_platform()
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())

    async def _heartbeat_loop(self):
        while self.connection:
            try:
                # 1. Send heartbeat keepalive to the platform
                await self.connection.send_json({"type": "ping"})

                # 2. Send meta heartbeat to the framework (one line)
                await self.emit_meta("heartbeat", self._bot_id)

                await asyncio.sleep(30)
            except Exception as e:
                self.logger.error(f"Failed to heartbeat: {e}")
                break
```

### 4. Connection Information Exposure

The routes registered by the adapter should be visible to users, facilitating the configuration of callback addresses on the platform side. It is recommended to actively output connection information in `start()`:

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

Users can query all routes and connection addresses of the adapter using the following APIs:

```python
from ErisPulse import sdk

# Adapter-level connection information (recommended)
info = sdk.adapter.get_connection_info("myplatform")

# Query at the router manager level
sdk.router.list_namespaces()              # List all namespaces
sdk.router.get_module_routes("myplatform")  # Detailed route information
sdk.router.get_module_urls("myplatform")    # Full connection URL
```

> **Note**: The `module_name` used during route registration must exactly match the `platform` name registered by the adapter in ErisPulse, otherwise `get_connection_info()` will not be able to associate the route. For multi-account adapters, sub-paths (e.g., `/account1/webhook`, `/account2/webhook`) should be registered for each account instead of using different `module_name`.

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
            "myplatform_raw": raw_event,  # Preserve raw data (required)
            "myplatform_raw_type": raw_event.get("type", "")  # Raw type (required)
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

### 3. Event ID Generation

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

The `At`/`AtAll`/`Reply` decorators are already built into the framework's SendDSL base class; the adapter only needs to implement `Raw_ob12` and specific send methods. Use `self._apply_modifiers(message)` and `self.send_context` to simplify development.

### 1. Must Return a Task Object

```python
class Send(BaseAdapter.Send):
    def Raw_ob12(self, message, **kwargs):
        """Recommended implementation: Use framework helper methods"""
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

### 2. Chainable Modifier Methods Return `self`

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
        """Send sticker"""
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

### 1. Standardized Response Format

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

`make_response()` automatically generates a response dictionary containing the `{platform}_raw` key. `make_error()` defaults to using `retcode=34000` (Platform Error).

### 2. Error Code Specification

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

After declaring a configuration class using `AccountConfigClass`, the framework automatically manages multi-account loading, validation, and template generation. The `BotAccountConfig` base class provides the `enabled` and `name` fields, which the adapter does not need to declare:

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
            # bot_id is automatically obtained from the platform protocol/login response and backfilled by the framework
    
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

The framework provides the built-in `_resolve_account()` method, which matches accounts in the following priority:

1. **Account name** — exact match with the configuration key
2. **`bot_id` field** — automatically obtained bot_id (i.e., `event["self"]["user_id"]`)
3. **Any str field** — other string fields in the configuration
4. **Fallback** — the first enabled account

```python
# Match by account name
name, account = self._resolve_account("account1")

# Match by bot_id (most commonly used method, from event)
name, account = self._resolve_account("bot_123")

# Get the first enabled account (pass None)
name, account = self._resolve_account(None)
```

## Error Handling

### 1. Categorized Exception Handling

Use `make_error()` to construct standardized error responses. When using `sdk.client` to request, catch ErisPulse exceptions:

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
        return self.make_error(retcode=10006, message="Response format error")
    except Exception as e:
        self.logger.error(f"Unknown error: {e}", exc_info=True)
        return self.make_error(message=str(e))
```

> **Backward Compatibility**: Old adapter code using `aiohttp` is unaffected and can still catch `aiohttp.ClientError`. Exception conversion only takes effect when requests are made via `sdk.client`.

### 2. Logging

The framework automatically creates a sub-logger for the adapter (`sdk.logger.get_child("MyAdapter")`), so manual initialization is not required:

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

## Reverse Conversion and Message Building

`Raw_ob12` is the method that adapters **must implement**, serving as the unified entry point for reverse conversion (OneBot12 → platform). Standard methods (`Text`, `Image`, etc.) should delegate to `Raw_ob12`, and modifier states (`At`/`Reply`/`AtAll`) must be merged into message segments within `Raw_ob12`.

`MessageBuilder` is a message segment builder tool that works in conjunction with `Raw_ob12`, supporting chainable calls and rapid message construction.

> For complete implementation specifications, code examples, and usage methods, please refer to:
> - [Send Method Specification §6 Reverse Conversion Specification](../../standards/send-method-spec.md#6-反向转换规范onebot12--平台)
> - [Send Method Specification §11 MessageBuilder](../../standards/send-method-spec.md#11-消息构建器-messagebuilder)

## Platform Event Method Extension

Adapters can register platform-specific methods for Event wrapper classes, allowing module developers to more easily access platform-specific data.

### 1. Use Mixin Class to Register Multiple Methods (Recommended)

When the platform has multiple specific methods, it is recommended to use a Mixin class:

```python
# Register at the start() or module level
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

# Register in bulk
register_event_mixin("myplatform", MyPlatformEventMixin)
```

### 2. Use Decorator to Register a Single Method

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

> For more detailed registration and deregistration instructions, please refer to [Event System API - Register Platform Extension Methods](../../api-reference/event-system.md#适配器注册平台扩展方法).

## Documentation Maintenance

### 1. Maintain Platform Feature Documentation

Create a `{platform}.md` documentation file under `docs/en/platform-guide/` (other language versions will be automatically generated):

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

> [!TIP]
> **When to read this**: Required reading within the adapter development path (Event Converter). Skip it if not needed; this won't affect the use of other features.

After the adapter receives a platform-native event, the Event Converter transforms it into ErisPulse's unified OneBot12 standard format—how platform events enter the framework is determined by this single class.

## Converter Responsibilities

```
Platform-native event ──→ Converter.convert() ──→ OneBot12 standard event
```

The Converter is only responsible for **forward conversion** (receiving direction), i.e., converting the platform's native event data into the OneBot12 standard format. Reverse conversion (sending direction) is handled by the `Send.Raw_ob12()` method.

### Core Principles

1. **Lossless conversion**: The raw data must be fully preserved in the `{platform}_raw` field
2. **Standard compatibility**: Converted events must conform to the OneBot12 standard format
3. **Platform extensions**: Platform-specific data is stored in fields with the `{platform}_` prefix

## BaseConverter Base Class (Recommended)

Since 2.7.0, the framework provides a `BaseConverter` base class (`ErisPulse.Core.Bases`) that encapsulates **common field construction** for OneBot12 events along with **common message segment helpers**, so converters only need to focus on type mapping:

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

Common fields populated by `build_base_event()`:

| Field | Source |
|------|--------|
| `id` | `raw_event["event_id"]`, auto-generated UUID by default |
| `time` | `raw_event["timestamp"]`, current time by default |
| `platform` | The `platform` passed in at construction |
| `self` | `{"platform": ..., "user_id": raw_event["bot_id"]}` |
| `{platform}_raw` | Raw event (satisfying the "lossless conversion" principle) |
| `{platform}_raw_type` | Raw event type |

Common message segment helper methods (all static methods, ready to reuse):

```python
converter.text("hi")          # {"type": "text", "data": {"text": "hi"}}
converter.at("123456")        # {"type": "at", "data": {"user_id": "123456"}}
converter.image("file.png")   # {"type": "image", "data": {"file": "file.png"}}
```

> When implementing manually, the common field construction in `build_base_event` is boilerplate code that must be written repeatedly. Using `BaseConverter` eliminates this part and naturally satisfies "lossless conversion" (the raw event always goes into `{platform}_raw`).

## The convert() Method

### Method Signature

```python
def convert(self, raw_event: dict) -> dict:
    """
    Convert a platform-native event to the OneBot12 standard format

    :param raw_event: Platform-native event data
    :return: OneBot12 standard format event dictionary
    """
    pass
```

### Return Value Structure

The converted event dictionary should contain the following standard fields:

```python
{
    "id": "Unique event ID",
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

    # Raw data must be preserved
    "myplatform_raw": { ... },     # Complete platform-native event data
    "myplatform_raw_type": "Native event type name",
}
```

## Required Field Mapping

### Common Fields (All Event Types)

| OB12 Field | Type | Description |
|-----------|------|-------------|
| `id` | str | Unique event identifier |
| `time` | int | Unix timestamp (seconds) |
| `type` | str | Event type: `message` / `notice` / `request` / `meta` |
| `detail_type` | str | Detail type: `private` / `group` / `friend`, etc. |
| `platform` | str | Platform name, matching the adapter registration name |
| `self` | dict | Bot info: `{"platform": "...", "user_id": "..."}` |

### Additional Fields for Message Events

| OB12 Field | Type | Description |
|-----------|------|-------------|
| `user_id` | str | Sender ID |
| `message` | list[dict] | OneBot12 message segment list |
| `alt_message` | str | Plain text fallback content |

### Additional Fields for Notice Events

| OB12 Field | Type | Description |
|-----------|------|-------------|
| `user_id` | str | Related user ID |
| `operator_id` | str | Operator ID (e.g., group member changes) |

## Message Segment Conversion

The OneBot12 standard defines the following message segment types:

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

# Mention all
{"type": "mention_all", "data": {}}

# Reply
{"type": "reply", "data": {"message_id": "msg_123"}}
```

If the platform has message segment types that are not supported, you can omit that segment or convert it to the closest standard type.

## Platform Extension Fields

Platform-specific data should be stored with the `{platform}_` prefix to avoid conflicts with standard fields:

```python
{
    # Standard fields
    "type": "message",
    "detail_type": "group",
    # ...

    # Platform extension fields
    "myplatform_raw": { ... },          # Raw event data (required)
    "myplatform_raw_type": "chat",      # Raw event type (required)

    # Other platform-specific fields
    "myplatform_group_name": "Group name",
    "myplatform_sender_role": "admin",
}
```

> **Important**: The `{platform}_raw` field is required. ErisPulse's event system and modules may rely on it to access the platform's raw data.

## Complete Example

The following is a complete Converter implementation:

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

Messages on real platforms usually contain rich media content such as images, mentions, and replies. The following is an example of `_convert_message_segments` handling multiple message types:

```python
def _convert_message_segments(self, raw_content: list) -> list:
    """Convert a list of platform-native message segments to OneBot12 standard message segments"""
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

### 1. Missing the `{platform}_raw` Field

This is the most common mistake. A missing raw data field prevents modules from accessing platform-specific information.

```python
base_event["myplatform_raw"] = raw_event        # Required!
base_event["myplatform_raw_type"] = event_type   # Required!
```

### 2. Incorrect Timestamp Format

The OneBot12 standard requires the `time` field to be a Unix timestamp in seconds (integer). If your platform returns millisecond timestamps or ISO format strings, you need to convert them:

```python
import time

# Milliseconds → seconds
"time": raw_event.get("timestamp", 0) // 1000

# ISO string → seconds
"time": int(time.mktime(time.strptime(raw_event["created_at"], "%Y-%m-%dT%H:%M:%S")))
```

### 3. Missing the `self` Field

The `self` field contains the bot's own information, where `user_id` is the bot's account ID. This field is crucial in multi-bot scenarios:

```python
"self": {
    "platform": self.platform,
    "user_id": raw_event.get("bot_id", ""),   # The bot's own ID
}
```

### 4. Using Non-Standard Values for detail_type

`detail_type` must use values defined by the OneBot12 standard, such as `private`, `group`, `friend_increase`, `group_member_increase`, etc. Do not use platform-specific naming.

### 5. Round-Trip Consistency

Ensure that the message segment types generated by the Converter correspond to the methods supported by the Send side. For example, if the Converter converts the platform's image messages to `{"type": "image", ...}`, then the `Image()` method on the Send side must be able to handle image sending.

## Best Practices

1. **Always preserve raw data**: The `{platform}_raw` field must not be omitted
2. **Use standard message segments**: Convert platform messages to OneBot12 standard message segments as much as possible
3. **Set detail_type properly**: Use standard types (`private`/`group`/`channel`, etc.), do not invent custom ones
4. **Handle edge cases**: Raw events may be missing certain fields; use `.get()` and provide sensible defaults
5. **Performance considerations**: `convert()` is called for every event; avoid performing time-consuming operations inside it



=====
发布与工具
=====


### 发布模块到模块商店

# Publishing and Module Store Guide

> [!TIP]
> **When to read this**: When publishing your work to PyPI / the Module Store. Skip it otherwise; it does not affect the use of other features.

Publish the modules or adapters you develop to the ErisPulse Module Store, so that other users can easily discover and install them.

## Module Store Overview

The ErisPulse Module Store is a centralized module registry where users can browse, search, and install community-contributed modules and adapters via CLI tools.

### Browsing and Discovery

```bash
# List all packages available remotely
epsdk list-remote

# View modules only
epsdk list-remote -t modules

# View adapters only
epsdk list-remote -t adapters

# Force refresh the remote package list
epsdk list-remote -r
```

You can also visit the [ErisPulse official website](https://www.erisdev.com/#market) to browse the Module Store online.

### Supported Submission Types

| Type | Description | Entry-point Group |
|------|------|----------------|
| Module | Extends bot functionality and implements business logic | `erispulse.module` |
| Adapter | Connects to new messaging platforms | `erispulse.adapter` |

## Quick Publish

The whole process takes just three steps: configure the project → publish to PyPI → submit to the Module Store.

### 1. Configure pyproject.toml

Make sure your project directory contains `pyproject.toml` and `README.md`, and configure entry-points according to the type:

#### Module

```toml
[project]
name = "ErisPulse-MyModule"
version = "1.0.0"
description = "Module description"
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
description = "Adapter description"
requires-python = ">=3.10"

[project.entry-points."erispulse.adapter"]
"myplatform" = "MyAdapter:MyAdapter"
```

> **Note**: It is recommended that package names start with `ErisPulse-` so users can easily identify them. The entry-point key (e.g., `"MyModule"`) will serve as the module's access name in the SDK.

### 2. Publish to PyPI

```bash
# Build + publish (requires a PyPI account)
pip install build twine
python -m build
python -m twine upload dist/*
```

Verify the installation after a successful publish:

```bash
pip install ErisPulse-MyModule
```

### 3. Submit to the Module Store

Go to the [ErisPulse Module Store](https://www.erisdev.com/#market), click "Submit Module", log in, and fill in the module information.

Supported login methods: **GitHub**, **Codeberg**, and **Yunhu** — choose any one of them.

Key information to fill in:
- Module name, description, and repository URL
- Minimum SDK version: if unsure, simply enter the version number of the [latest ErisPulse release](https://pypi.org/project/ErisPulse/)

Submissions take effect immediately, and users can install via the module source. The module will be marked as "Unverified" and changed to "Verified" once it passes review by maintainers.

> **About verification status**:
> - "Unverified" only means the module has not yet been officially reviewed; it does not indicate any problem with the module
> - When installing an unverified module via `epsdk install`, users will receive a risk warning and must confirm before the installation can continue

### 4. Manage Published Modules

After clicking "Submit Module" on the Module Store and logging in, switch to the "My Modules" tab, where you can:

- **Edit** — Modify the module description, repository URL, tags, and other information; the version number is automatically synced from PyPI
- **Delete** — Remove the module from the Module Store (irreversible)

> Modules that were just submitted may take a few minutes to appear in the "My Modules" list.

## Updating Published Modules

1. Update `version` in `pyproject.toml`
2. Rebuild and upload: `python -m build && python -m twine upload dist/*`
3. The Module Store will automatically sync the latest version from PyPI

Users can upgrade with `epsdk upgrade MyModule`.

## Pre-Publish Checklist

Before pushing to PyPI, please confirm the following items one by one:

### Code Quality

- [ ] All public APIs have type annotations (function signatures and return values)
- [ ] All public methods have docstrings (`"""..."""` format, including `:param` / `:return` / `:raises`)
- [ ] Passes `ruff check` (no warnings)
- [ ] Test coverage ≥ 80%
- [ ] All `pytest` test cases pass

### Compatibility

- [ ] `pyproject.toml` declares the minimum SDK version: `dependencies = ["ErisPulse>=x.y.z"]`
- [ ] The module declares the runtime minimum SDK version in `get_meta()` via `ModuleMeta(min_sdk_version="x.y.z")` (adapters use the class attribute `min_sdk_version`) — when the SDK in the user's environment is too old, the framework clearly reports an error and skips loading it, instead of throwing hard-to-diagnose runtime exceptions
- [ ] Tested on Python 3.10 / 3.11 / 3.12 / 3.13
- [ ] Tested on target operating systems (Windows / Linux / macOS, as applicable)
- [ ] No circular import dependencies

### Configuration

- [ ] If using declarative configuration (`ConfigClass` + `BaseConfig` / `BotAccountConfig`), configuration fields have `description` (i18n format recommended) and `ui` metadata
- [ ] If i18n translation keys are registered, all 5 languages are covered (zh-CN / zh-TW / en / ja / ru)
- [ ] Sensitive fields are marked with `secret=True`

### Documentation

- [ ] `README.md` includes installation instructions and basic usage examples
- [ ] `README.md` explains how to configure it (config file example + environment variables)
- [ ] `CHANGELOG.md` records all changes
- [ ] Adapters have updated platform feature documentation (supported Send types, event types, etc.)

### Publishing

- [ ] The version number in `pyproject.toml` has been updated
- [ ] Build passes: `python -m build`
- [ ] Pushed to PyPI: `python -m twine upload dist/*`
- [ ] Installation verified: `pip install ErisPulse-xxx && epsdk run`

## Development Mode Testing

Before the official release, you can test locally using editable mode:

```bash
epsdk install -e /path/to/MyModule
# or
pip install -e /path/to/MyModule
```

## FAQ

### Must package names start with `ErisPulse-`?

It is not mandatory, but strongly recommended. It helps users identify ErisPulse ecosystem packages on PyPI.

### Can a single package register multiple modules?

Yes. Simply configure multiple key-value pairs in `entry-points`:

```toml
[project.entry-points."erispulse.module"]
"ModuleA" = "MyPackage:ModuleA"
"ModuleB" = "MyPackage:ModuleB"
```

### How long does the review take?

Usually completed within 1-3 business days. You can check the verification status under "My Modules" on the Module Store.

## Distributing Applications via Docker Images

If your application is not suitable for publishing to PyPI (e.g., it contains private dependencies or requires a pre-configured environment), you can publish a Docker image via **GitHub Container Registry (GHCR)**, allowing other users to start it with a single `docker pull`.

### Use Cases

- You have a **complete bot application** (module + configuration + entry script) and want one-click distribution
- The module/adapter depends on **private packages** or has a special installation process, making it unsuitable for PyPI
- You want to provide an **out-of-the-box** deployment solution to lower the barrier for users

### 1. Create a Dockerfile

Build on top of the official ErisPulse image; you only need to add your module:

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

If the module requires additional system dependencies (such as an SSH client), add the following after `RUN uv pip install`:

```dockerfile
RUN apt-get update && apt-get install -y --no-install-recommends \
    openssh-client \
    && rm -rf /var/lib/apt/lists/*
```

> `erispulse/erispulse:latest` already includes ErisPulse, ErisPulse-Dashboard, the Python runtime, and uv, so there is no need to install them again.

### 2. Create a GitHub Actions Workflow

Create `.github/workflows/docker-publish.yml`:

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

      - name: Log in to GitHub Container Registry
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

> `GITHUB_TOKEN` is automatically provided by GitHub Actions; there is no need to create the secret manually.

### 3. Trigger the Build

Pushing code or creating a tag will trigger an automatic build:

```bash
# Trigger by pushing to the main branch
git push origin main

# Or trigger by creating a tag
git tag v1.0.0
git push origin v1.0.0
```

You can also trigger it manually from the **Actions** page of the GitHub repository.

### 4. Set the Image to Public

GHCR images are **private** by default; you need to set them to Public on GitHub so other users can pull them without logging in:

1. Go to the repository → **Packages** → click the corresponding Package
2. **Package settings** → **Danger Zone** → **Change visibility** → **Public**

### 5. User Usage

After the build completes, users can start it with a single `docker run` command:

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

### Publishing to Docker Hub as Well

Extend the workflow by adding a Docker Hub login step before the login step, and add the Docker Hub address to `images`:

```yaml
      - name: Log in to Docker Hub
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

> You need to add `DOCKERHUB_USERNAME` and `DOCKERHUB_TOKEN` under the repository **Settings → Secrets**.

### Docker Image vs PyPI Publishing

| Feature | Docker Image (GHCR) | PyPI Publishing |
|------|---------------------|-----------|
| Distribution method | Run with a single `docker pull` | `pip install` + manual configuration |
| Scope | Complete applications/solutions | Individual modules/adapters |
| Private dependencies | Natively supported | Requires a private PyPI source |
| Module Store | Not applicable | Can be submitted to the Module Store |
| Multi-architecture | Supports amd64/arm64 | Architecture-independent |

The two approaches are not mutually exclusive — you can publish modules to the Module Store via PyPI while also providing an out-of-the-box Docker image via GHCR.



### 模块测试（ErisPulse-Testing）

# Module Testing (ErisPulse-Testing)

> [!TIP]
> **When to read this**: When writing automated tests for your own modules. If not needed, feel free to skip — this won't affect the use of any other features.

[ErisPulse-Testing](https://github.com/ErisPulse/ErisPulse-Testing) is the official testing toolkit:
providing `TestBot`, test event factories, outbound message capture, and assertion interfaces, making module testing as easy as writing ordinary pytest tests.

```bash
pip install ErisPulse-Testing
```

> A development-time tool with a one-way dependency on the framework and zero runtime intervention. For smoke tests that actually connect to adapter platforms, use `tests/devs/test_adapter.py` from the framework repository.

## Quick Start

```python
import pytest
from ErisPulse.Core.Event.command import command
from ErisPulse_Testing import TestBot, create_command_event

async def test_daily(make_testbot):
    async with make_testbot(prefix="/") as bot:
        @command("daily", cooldown="1d", cooldown_reply="Already checked in today")
        async def daily(event):
            await event.reply("Check-in successful!")

        await bot.dispatch(create_command_event("daily", user_id="123"))
        assert bot.last_reply.text == "Check-in successful!"

        await bot.dispatch(create_command_event("daily", user_id="123"))
        bot.assert_reply_contains("Already checked in today")   # Second attempt hits the cooldown
```

`TestBot` is recommended to be used with `async with`: on startup it registers the MockAdapter (capturing all outbound messages), disables event deduplication, and applies config overrides; on exit it automatically cleans up the framework's global state, so test cases do not pollute one another.

Accompanying pytest fixtures (automatically available after installation):

- `testbot`: function-scoped standard TestBot (platform=`test`, prefix `/`)
- `make_testbot(**kwargs)`: factory with customizable parameters (`prefix` / `config` / `platform` / `bot_id` ...)

It is recommended to set `asyncio_mode = "auto"` (`[tool.pytest.ini_options]`) in your test project's configuration, or add `@pytest.mark.asyncio` to your test cases.

## Event Factories

| Function | Description |
|------|------|
| `create_message_event(text, user_id=..., group_id=None, ...)` | Message event; an empty `group_id` means a private chat |
| `create_command_event("roll 3", prefix="/")` | Command message (prefix added automatically; not duplicated if already present) |
| `create_notice_event(type, ...)` | Notice event (e.g., `friend_add`) |
| `create_request_event(type, ...)` | Request event (e.g., friend request) |
| `create_meta_event("connect", ...)` | Meta event (connect brings the Bot online) |

All events use a unique uuid `id`, naturally bypassing the framework's event deduplication.

Note: Synthetic events **do not contain the platform's raw payloads** (`event.get_raw()` returns an empty dict). To determine scenarios such as group chat / private chat, use accessors like `event.is_group_message()` / `event.get_detail_type()` / `event.get_group_id()`, instead of reading raw data.

## TestBot API

### Dispatch

```python
trace = await bot.dispatch(event)          # Dispatch and wait for handlers to settle; returns the decision chain
await bot.dispatch(event, drain=False)     # First message of an interaction: don't wait (wait_reply handlers stay resident)
await bot.send_message("Hello")            # Shortcut for message dispatch
await bot.reply_as("18", user_id="u1")     # Simulate a user reply to wait_reply (automatically waits for the waiter to be ready)
```

`dispatch()` gathers all in-flight handler Tasks after emit; by the time it returns, processing is complete — **no need for sleep in tests**.

### Outbound Assertions

```python
bot.replies                # All outbound messages (list of SentMessage)
bot.last_reply.text        # Text of the most recent reply
bot.replies_to("123")      # Filter by target
bot.clear_replies()        # Isolate assertions between phases
bot.assert_replied()                       # Outbound messages exist
bot.assert_replied(contains="check-in", to="123")
bot.assert_not_replied()                   # No outbound messages at all
bot.assert_reply_contains("Check-in successful")       # An outbound message containing the specified text exists
await bot.wait_for_reply(timeout=2)        # Wait for an asynchronous reply to appear
```

`SentMessage` fields: `text` (the first text segment), `segments` (full message segments), `target_type` / `target_id` / `bot_id` (sending context), `has_modifier("at")`, and more.

### Module Loading

```python
await bot.load_module("MyModule")   # Registered module name (requires the framework's sdk.init() to complete entry-point discovery)
await bot.load_module(MyModule)     # Or a BaseModule subclass (automatic register + load, recommended)
await bot.unload_module("MyModule")
```

Commands / event handlers registered inside `on_load` belong to the module and are automatically cleaned up on unload, so you can directly assert that "commands stop working after unloading".
Note: The string form **does not perform entry-point scanning** (TestBot does not initialize the framework's discovery process); to test modules that are soft dependencies, pass the class object directly (or call `module.register` yourself and then pass the name).

### Dependency Replacement (requires EP>=2.9.0-dev)

```python
with bot.patch_dependency(get_session, fake_session) as mock:
    await bot.dispatch(create_command_event("query"))
    assert mock.called
```

What is replaced is the function referenced by the `Depends(get_session)` declaration in the command registry; upon exiting the with block, everything is automatically restored.

### Config Overrides

```python
bot = TestBot(prefix="//", config={
    "ErisPulse.event.command.case_sensitive": False,
    "MyModule.api_key": "test-key",     # Module config (readable via self.cfg)
})
```

Injected through the config memory layer; command prefixes and the like take effect immediately via hot reload. Two caveats:

1. **Persistence to disk**: Overrides will be written to `config/config.toml` under the cwd according to the framework's deferred disk-write policy (about 5 seconds by default) — please add `config/` to `.gitignore` in the repository of the project under test;
2. **Conflict with module runtime write-backs (known limitation)**: When a module under test writes back entire config sections (`self.cfg = ...`, e.g., subscription lists) alongside the dotted overrides here, there is a read/write consistency issue in ConfigManager — a module reading an entire section may not see the overridden values, and overrides may be overwritten by whole-section write-backs when persisted (fixed in ErisPulse 2.9.0-dev.2; 2.8.x is still affected). For test cases involving "runtime config write-backs" on 2.8.x, it is recommended to reset the relevant config sections in a fixture using whole-section write-backs.

## Dispatch Decision Chain (troubleshooting "why didn't the command trigger"; requires EP>=2.9.0-dev)

`dispatch()` returns a `DispatchTrace` — the causal chain of every decision point traversed during this dispatch:

```python
trace = await bot.dispatch(create_command_event("dailyx", user_id="123"))

trace.verdict        # executed / rejected / dropped / failed / no_match / passed
trace.explain()      # Line-by-line causal explanation (in the current language)
trace.command        # Name of the matched command (None if not matched)
trace.steps("cooldown")  # Filter decision records by phase

trace.assert_executed("daily")  # Assert execution (attaches the full causal chain on failure)
trace.assert_rejected()         # Assert rejection by a permission-related verdict
trace.assert_dropped()          # Assert silent dropping (cooldown, etc.)
trace.assert_no_match()         # Assert no command was matched
```

Verdict coverage: command text validation, command matching (with spelling suggestions when unmatched), scopes, user ACLs, owner checks, permission functions, silent cooldown drops, argument parsing, execution results, and middleware vetoes.

In production environments, you can likewise use the framework's built-in `ErisPulse.Core.Event.trace` (`start_dispatch_trace()` / `format_dispatch_trace()`) to collect and render decision chains.



### CLI 命令参考

# CLI Command Reference

> [!TIP]
> **When to read this**: Consult it when you forget the arguments of an `epsdk` command, want to script component management, or need to control run / stop / restart behavior. If your daily usage is limited to `init` / `install` / `run`, remembering one thing is enough: `epsdk <command> --help` shows argument descriptions anytime—no need to read this document end to end.

`epsdk` is the command-line tool for ErisPulse: initializing projects, installing / upgrading modules and adapters, interactively configuring components, running and stopping bots, and diagnosing the environment—all under this single command.

> **Tip**: The main help of `epsdk` (without a command) is grouped by category: **Project** (init / create / run), **Component Management** (install / uninstall / upgrade / list / list-remote / types), **Configuration & Diagnostics** (config / doctor / i18n), **Other** (self-update / version).

---

## Package Management Commands

| Command | Alias | Arguments | Description |
|------|------|------|------|
| `install` | `i`, `add` | `[package]... [--upgrade/-U] [--pre] [-e PATH] [--user] [--no-deps] [-t DIR] [--index-url URL] [--extra-index-url URL] [--no-cache-dir] [-r FILE] [-c FILE] [--force-reinstall] [--ignore-installed] [--compile/--no-compile] [--prefix DIR] [--src DIR] [--config-settings SETTINGS] [--no-binary FORMAT] [--only-binary FORMAT] [--prefer-binary] [--build-isolation/--no-build-isolation] [--upgrade-strategy {eager,only-if-needed,to-satisfy-only}] [--break-system-packages] [--no-uv]` | Install modules/adapters |
| `uninstall` | `rm`, `remove` | `<package>... [--no-uv]` | Uninstall modules/adapters |
| `upgrade` | `up` | `[package]... [--force/-f] [--pre] [--no-uv]` | Upgrade specified modules or all |
| `self-update` | `su`, `update` | `[version] [--pre] [--force/-f] [--no-uv]` | Update the SDK itself |

## Diagnostic Commands

| Command | Alias | Arguments | Description |
|------|------|------|------|
| `doctor` | `diag` | `[--verbose] [--fix]` | Diagnose the environment and output a health report; `--fix` attempts automatic repair |

### install

Install ErisPulse module or adapter packages. If no package name is specified, an interactive installation interface is launched.

**Aliases:** `i`, `add`

> **uv project integration** (2.11.1+): Inside a uv-managed project (where `uv.lock` or `[tool.uv]` exists),
> `install` / `upgrade` / `uninstall` automatically switch to `uv add` / `uv remove`—dependencies are written to both
> `pyproject.toml` and `uv.lock`, so `uv sync` no longer wipes out components installed by epsdk; on failure it automatically
> falls back to the uv pip / pip channel. Arguments unsupported by uv, such as `--user`, go directly through pip. Target environment resolution order:
> `ERISPULSE_PYTHON` → `UV_PROJECT_ENVIRONMENT` → project `.venv` → `UV_PYTHON` →
> `VIRTUAL_ENV` → current interpreter (`epsdk doctor` shows the full decision chain).

**Arguments:**

| Argument | Short | Description |
|------|--------|------|
| `[package]...` | | Package names to install; multiple can be specified |
| `--upgrade` | `-U` | Upgrade to the latest version during installation |
| `--pre` | | Allow installing pre-release versions |
| `--editable` | `-e` | Install in editable mode (path required) |
| `--user` | | Install to the user site-packages directory |
| `--no-deps` | | Do not install dependencies |
| `--target` | `-t` | Install to the specified directory |
| `--index-url` | | Specify the PyPI mirror URL |
| `--extra-index-url` | | Additional PyPI mirror URLs (can be specified multiple times) |
| `--no-cache-dir` | | Disable the cache |
| `--requirement` | `-r` | Install from a requirements file |
| `--constraint` | `-c` | Install from a constraints file |
| `--force-reinstall` | | Force reinstall |
| `--ignore-installed` | | Ignore installed packages |
| `--compile` | | Compile .pyc files after installation |
| `--no-compile` | | Do not compile .pyc files after installation |
| `--prefix` | | Install to the specified prefix directory |
| `--src` | | Source directory used for editable installs |
| `--config-settings` | | Configuration passed to the build backend (can be specified multiple times) |
| `--no-binary` | | Restrict use of binary packages (format such as `:all:`) |
| `--only-binary` | | Restrict to binary packages only (format such as `:all:`) |
| `--prefer-binary` | | Prefer binary packages |
| `--build-isolation` | | Enable build isolation |
| `--no-build-isolation` | | Disable build isolation |
| `--upgrade-strategy` | | Upgrade strategy: `eager`, `only-if-needed`, `to-satisfy-only` |
| `--break-system-packages` | | Allow modifying Python packages managed by the system package manager |
| `--no-uv` | | Use pip instead of uv |

**Examples:**

```bash
# Install a single module
epsdk install Weather

# Install multiple modules
epsdk install Yunhu Weather

# Install and upgrade from a mirror
epsdk install Weather -U --index-url https://pypi.tuna.tsinghua.edu.cn/simple

# Install in editable mode (development mode)
epsdk install -e ./my-adapter
```

### uninstall

Uninstall installed ErisPulse module or adapter packages. If no package name is specified, an interactive uninstall interface is launched.

**Aliases:** `rm`, `remove`

**Arguments:**

| Argument | Description |
|------|------|
| `<package>...` | Package names to uninstall; multiple can be specified |
| `--no-uv` | Use pip instead of uv |

**Examples:**

```bash
# Uninstall a single module
epsdk uninstall Weather

# Uninstall multiple modules
epsdk uninstall Yunhu Weather
```

### upgrade

Upgrade installed ErisPulse components. If no package name is specified, upgrade all interactively.

**Aliases:** `up`

**Arguments:**

| Argument | Short | Description |
|------|--------|------|
| `[package]...` | | Package names to upgrade; multiple can be specified |
| `--force` | `-f` | Force upgrade, skip confirmation |
| `--pre` | | Allow upgrading to pre-release versions |
| `--no-uv` | | Use pip instead of uv |

**Examples:**

```bash
# Upgrade all packages
epsdk upgrade

# Upgrade a specific package
epsdk upgrade Weather

# Force upgrade (skip confirmation)
epsdk upgrade -f
```

### self-update

Update the ErisPulse SDK itself to the latest version.

**Aliases:** `su`, `update`

**Arguments:**

| Argument | Short | Description |
|------|--------|------|
| `[version]` | | Specify the target version to update to |
| `--pre` | | Allow updating to pre-release versions |
| `--force` | `-f` | Force update, skip confirmation |
| `--no-uv` | | Use pip instead of uv |

**Examples:**

```bash
# Update to the latest stable version
epsdk self-update

# Update to a specific version
epsdk self-update 1.2.3

# Allow pre-release versions
epsdk self-update --pre

# Force update
epsdk self-update -f
```

> [!NOTE]
> When installed via `uv tool install ErisPulse`, this command automatically switches to `uv tool upgrade ErisPulse` (or `uv tool install ErisPulse==<version> --force` when a version is specified), since a direct pip upgrade of the tool environment would be wiped out by uv's manifest restoration.
> On Windows, the update runs in a new console window: the current CLI must exit first to release the tool environment files; after the window indicates completion, simply reopen the terminal.

---

## Information Query Commands

| Command | Alias | Arguments | Description |
|------|------|------|------|
| `list` | `l`, `ls` | `[--type/-t {modules,adapters,all}] [--outdated/-o]` | List installed components |
| `list-remote` | `lsr` | `[--type/-t {modules,adapters,all}] [--refresh/-r]` | List remotely available components |
| `version` | `ver` | | Show SDK and Python version information (equivalent to `-V`) |

### list

List installed ErisPulse modules and adapters.

**Aliases:** `l`, `ls`

**Arguments:**

| Argument | Short | Description |
|------|--------|------|
| `--type` | `-t` | Specify type: `modules`, `adapters`, `all` (default) |
| `--outdated` | `-o` | Show only upgradable packages |

**Examples:**

```bash
# List all installed components
epsdk list

# List modules only
epsdk list -t modules

# List adapters only
epsdk list -t adapters

# Show only upgradable packages
epsdk list -o
```

### list-remote

List ErisPulse modules and adapters available in remote repositories.

**Aliases:** `lsr`

**Arguments:**

| Argument | Short | Description |
|------|--------|------|
| `--type` | `-t` | Specify type: `modules`, `adapters`, `all` (default) |
| `--refresh` | `-r` | Force refresh of the remote package list cache |

**Examples:**

```bash
# List all remotely available components
epsdk list-remote

# List remote modules only
epsdk list-remote -t modules

# Force refresh the cache before listing
epsdk list-remote -r
```

---

## Configuration Commands

| Command | Alias | Arguments | Description |
|------|------|------|------|
| `config` | `cfg`, `conf` | `[name] [--list/-l] [--json]` | Interactively configure declarative config entries of adapters/modules |

### config

Interactively fill in the declarative config entries of adapters/modules. The wizard is driven by the config classes declared by the adapter/module (`ConfigClass` / `AccountConfigClass`), automatically generating and validating forms—no need to hand-write config.toml.

Adapters additionally support multi-account (bot account) management: adding/editing/deleting accounts, and enable/disable switches.

**Aliases:** `cfg`, `conf`

**Arguments:**

| Argument | Short | Description |
|------|--------|------|
| `[name]` | | Target name (adapter platform name or module name); leave empty to enter interactive selection |
| `--list` | `-l` | Only list the configuration status of all targets without entering the wizard |
| `--json` | | Output all targets and their configuration status as JSON (for CI / script consumption) without entering the wizard |

**Examples:**

```bash
# View the configuration status of all adapters/modules
epsdk config --list

# Output configuration status as JSON (for CI / script consumption)
epsdk config --json

# Interactively select a target to configure
epsdk config

# Directly configure a specific adapter
epsdk config yunhu

# Directly configure a specific module
epsdk config MyModule
```

**Notes:**

- Configuration status has four levels: `Ready` (validation passed), `Incomplete` (required fields missing or validation failed), `Not Configured` (never generated), `No Configuration` (target declares no config class)
- Field values carry a source annotation: existing configuration shows `(current: value)`, and when unconfigured the schema default is shown as `(default: value)`; pressing Enter directly keeps that value
- Secret-type fields (declared with `secret`) are not echoed during input; pressing Enter keeps the already-set value
- In interactive selection mode, after a single wizard finishes it returns to the selection menu (with refreshed status), allowing you to configure multiple targets consecutively; leave empty to exit
- If global form validation fails and you abandon re-filling, the wizard aborts without writing any configuration (avoiding a half-finished state of "enabled but incomplete configuration")
- After saving, it is immediately written to `config/config.toml`, visible to both the Dashboard and the running SDK; running adapters that need to apply new account configuration can pick it up by restarting the process
- After `epsdk install` (interactive installation) and `epsdk init` successfully install an adapter, if a configuration declaration is detected, this wizard is automatically invoked; when installing by directly specifying package names on the command line, only a configuration hint is printed

---

## Run Control Commands

> [!TIP]
> `epsdk run` automatically detects and uses the `.venv` virtual environment in the project directory to run the bot
> (you can also explicitly specify an interpreter via the `ERISPULSE_PYTHON` environment variable). `epsdk install` /
> `uninstall` / `upgrade` / `list` likewise operate on the project virtual environment.

| Command | Alias | Arguments | Description |
|------|------|------|------|
| `run` | `r` | `[script] [--reload] [--strict/--no-strict]` | Run the specified script or the SDK |
| `stop` | — | `[--force] [--pid PID]` | Stop the running instance (started by `epsdk run`) |
| `restart` | — | `[--force] [--pid PID]` | Restart the running instance (stop, then relaunch with the original arguments) |

### run

Run an ErisPulse project script or start the SDK directly. Hot reload mode is supported.

**Aliases:** `r`

**Arguments:**

| Argument | Description |
|------|------|
| `[script]` | Script file to run; if not specified, runs the SDK |
| `--reload` | Enable hot reload mode: monitoring file changes automatically triggers component-level code hot reload (no full process restart needed); by default directories like `.venv`/`.git` are ignored (configurable via `ErisPulse.framework.watch_ignore_dirs`), and the plugins directory is handled precisely by the plugin hot-reload watcher |
| `--strict` / `--no-strict` | Temporarily enable / disable strict mode (effective for this run only, not written to config); by default follows `ErisPulse.framework.strict_mode` |

**Examples:**

```bash
# Run the SDK directly
epsdk run

# Run a specific script file
epsdk run main.py

# Run in hot reload mode (file changes automatically trigger code-level hot reload)
epsdk run main.py --reload

# SDK hot reload mode
epsdk run --reload

# Temporary strict mode: exit if the pre-start self-check fails, framework strictness raised to at least 1 for this run
epsdk run main.py --strict

# Temporary relaxed mode (strict_mode is on in config but you just want to get running this time)
epsdk run main.py --no-strict
```

**Pre-start self-check:** Before starting, `run` quickly checks the parseability of `config/config.toml` and the completeness of required configuration for installed components; strictness defaults to `ErisPulse.framework.strict_mode` (when non-zero, a failed check exits immediately; when 0, it only warns and continues). A missing config file is treated as a normal first launch—only a hint is shown, not judged as a failure. `--strict` temporarily enables it: exit immediately if the pre-check fails, and raise the framework strictness level to at least 1 for this run (non-compliant components are skipped, propagated to the running process via the `ERISPULSE_FRAMEWORK_STRICT_MODE` environment variable, not written to the config file); `--no-strict` conversely temporarily relaxes it. The self-check skips itself automatically when it encounters its own errors, involves no network probing, and never blocks startup.

> **Supervision structure of `--reload`** (since 2.11.1): `epsdk run --reload` runs as a "supervisor process + reload worker subprocess". Hot reloads triggered by saving `.py` files all happen inside the worker (mutually exclusive serialization, burst coalescing); syntax errors on the module side are rejected by an upfront pre-check, and the old instance keeps serving. When `sdk.hard_restart()` is called, the worker exits with code 42, and after the supervisor displays the reason it automatically pulls up a brand-new worker—after upgrading the framework itself, the new code takes effect immediately.

### stop

Stop a running ErisPulse instance (started by `epsdk run` and executed in the same project directory).
When `run` starts, it writes the supervisor process PID, the current framework subprocess PID, and the original launch command into
`.erispulse/runtime.json`, which `stop` uses to locate the instance.

**Stop sequence:** On POSIX, SIGINT is first sent to the supervisor process (the same graceful shutdown path as Ctrl+C—the
finally chain automatically terminates the framework subprocess), escalating step by step to SIGTERM / SIGKILL on timeout; Windows has no
process signal semantics, so the framework subprocess is terminated first and then the supervisor process (to prevent the supervisor from misjudging the force kill as a crash
and respawning).

**Arguments:**

| Argument | Description |
|------|------|
| `--force` | Skip graceful stop, terminate forcibly |
| `--pid PID` | Directly specify the target process PID (overrides the runtime state file, for non-standard launch methods) |

**Examples:**

```bash
# Stop the running instance of the current project
epsdk stop

# Force terminate
epsdk stop --force
```

### restart

Restart the running ErisPulse instance: after stopping with `stop` semantics, relaunch with the
**original launch command** recorded in the state file (taking over the current terminal in the foreground; the new instance writes a new runtime state file).

**Arguments:** Same as `stop` (`--force` / `--pid PID`).

**Examples:**

```bash
# Graceful restart (make pip-upgraded adapters/modules take effect; running modules can also use
# sdk.reload_module / sdk.adapter.reload code-level hot reload, no restart needed)
epsdk restart
```

> [!NOTE]
> Launch methods such as `python main.py` that bypass `epsdk run` do not write the runtime state file—manage such
> processes with system tools, or specify the PID with `epsdk stop --pid <PID>`.

---

## Project Management Commands

| Command | Alias | Arguments | Description |
|------|------|------|------|
| `init` | — | `[path] [--project-name/-n <name>] [--path <dir>] [--adapter/-a <name>] [--quick/-q] [--force/-f] [--here] [--no-uv] [--no-venv]` | Initialize an ErisPulse project |
| `create` | — | `{module,adapter,pack} [--name/-n <name>] [--description/-d <desc>] [--author/-a <name>] [--email/-e <mail>] [--homepage <url>] [--output/-o <dir>] [--force/-f] [--local]` | Create module/adapter scaffolding; `pack` converts a local plugin into a publishable project |

### init

Initialize a new ErisPulse project. Supports interactive and quick modes; since 2.8.4 it generates `pyproject.toml` (dependency manifest), optionally creates a project `.venv` virtual environment and installs the framework and adapters, and supports **specifying any directory**.

**Arguments:**

| Argument | Short | Description |
|------|--------|------|
| `[path]` | | Target path (may include a parent directory, e.g. `../apps/mybot`; a bare name is equivalent to `--project-name`) |
| `--project-name` | `-n` | Project name |
| `--path` | | Project parent directory (combined with `-n` to specify the creation location) |
| `--adapter` | `-a` | Preselect adapters to install (repeatable or comma-separated); when provided, skips adapter prompting and selection |
| `--quick` | `-q` | Quick mode, skip the interactive wizard (creates `.venv` and installs dependencies by default) |
| `--force` | `-f` | Force overwrite of existing config files |
| `--here` | | Initialize in the current directory without creating a subdirectory |
| `--no-uv` | | Use pip instead of uv |
| `--no-venv` | | Skip virtual environment creation and dependency installation |

**Examples:**

```bash
# Interactive initialization
epsdk init

# Quick initialization (creates my_bot/ in the current directory, with pyproject.toml + .venv)
epsdk init -q -n my_bot

# Quick initialization with pre-installed adapters (non-interactive, for scripts / CI)
epsdk init -q -n my_bot --adapter yunhu,telegram

# Initialize in any specified directory (../apps/mybot)
epsdk init ../apps/mybot

# Combine parent directory and project name
epsdk init -n my_bot --path ../apps

# Force overwrite existing configuration
epsdk init -f

# Initialize in the current directory
epsdk init --here -n my_bot

# Generate project structure only, without creating a virtual environment
epsdk init --no-venv -n my_bot
```

init artifacts: `main.py`, `pyproject.toml` (dependency manifest), `config/config.toml` + `config.full.example`, `config/ssl/`, `logs/`, `.gitignore`, `README.md`; when creating a virtual environment is chosen, a `.venv` is additionally generated with `erispulse` and the selected adapters installed into it.

> [!NOTE]
> The `.gitignore` is a grouped template: Python bytecode and build artifacts, virtual environments and `.env`, tool caches, editor and system files, and it **excludes the `config/` and `logs/` runtime directories entirely**—`config.toml` contains sensitive information such as adapter tokens and is not recommended for version control; use `config.full.example` to share the configuration skeleton.

> [!WARNING]
> **Do not use `uv run epsdk run` to run the bot**. When executed in a directory without `pyproject.toml`, `uv run` creates a **disposable isolated environment**—adapters installed via `epsdk install` inside it will not persist. Use `epsdk run` inside the project directory (which automatically uses the project `.venv`), or activate the virtual environment first and then run.

### create

Create scaffolding projects for ErisPulse modules or adapters; the `pack` subcommand converts local plugins (the `plugins/` directory) into publishable standard projects.

**Arguments:**

| Argument | Short | Description |
|------|--------|------|
| `{module,adapter,pack}` | | Type to create: `module` / `adapter` / `pack` (plugin to project) |
| `--name` | `-n` | Project name (PascalCase) |
| `--description` | `-d` | Project description |
| `--author` | `-a` | Author name |
| `--email` | `-e` | Author email |
| `--homepage` | | Project homepage URL |
| `--output` | `-o` | Output directory (defaults to current directory) |
| `--force` | `-f` | Force overwrite of an existing directory |
| `--local` | | Create a local plugin (available for `module` / `adapter`): generates a `plugins/<name>/` package structure, installable without packaging |

**Examples:**

```bash
# Interactive creation (guided type selection and info filling)
epsdk create

# Create a Module project directly
epsdk create module -n MyModule

# Create a local plugin (placed in the project's plugins/ directory, auto-discovered at startup)
epsdk create module -n MyModule --local

# Create a local adapter plugin (same as above, package-free development)
epsdk create adapter -n MyAdapter --local

# Create an Adapter project directly
epsdk create adapter -n MyAdapter

# Convert a local plugin into a publishable project (interactively select plugin → complete metadata → generate standard project)
epsdk create pack

# Full arguments
epsdk create module -n MyModule -d "Module description" -a "Author" -e "mail@example.com"

# Specify output directory
epsdk create module -n MyModule -o ./projects

# Force overwrite existing directory
epsdk create module -n MyModule -f
```

---

## Language Commands

| Command | Alias | Arguments | Description |
|------|------|------|------|
| `i18n` | `language`, `lang` | `[lang] [--list/-l]` | View or switch the CLI display language |

### i18n

View the current CLI language, list supported languages, or switch the display language. If no argument is specified, an interactive selection interface is launched.

**Aliases:** `language`, `lang`

**Arguments:**

| Argument | Short | Description |
|------|--------|------|
| `[lang]` | | Language code to switch to (e.g. `zh-CN`, `en`, `ja`, `ru`) |
| `--list` | `-l` | List all supported languages |

**Examples:**

```bash
# Interactively select a language
epsdk i18n

# Switch to English
epsdk i18n en

# Switch to Japanese
epsdk i18n ja

# List all supported languages
epsdk i18n --list
```

---

## Type Stub Commands

| Command | Alias | Arguments | Description |
|------|------|------|------|
| `types` | `t`, `stub` | `[--output/-o <path>] [--force] [--adapters-only] [--modules-only]` | Generate type stub files to enable IDE completion |

### types

Scan installed ErisPulse modules and adapters and generate `.pyi` type stub files for them, enabling accurate code completion and type checking support in your IDE.

**Aliases:** `t`, `stub`

**Arguments:**

| Argument | Short | Description |
|------|--------|------|
| `--output` | `-o` | Output path (defaults to `ep-stubs/` in the current directory) |
| `--force` | | Force overwrite of existing stub files |
| `--adapters-only` | | Generate type stubs for adapters only |
| `--modules-only` | | Generate type stubs for modules only |

> **Note:** `--adapters-only` and `--modules-only` are mutually exclusive; when both are specified, the latter takes effect.

**Examples:**

```bash
# Generate type stubs for all installed modules and adapters
epsdk types

# Generate adapter stubs only
epsdk types --adapters-only

# Output to a specified directory
epsdk types -o ./typings

# Force overwrite existing files
epsdk types --force
```

---

## Global Parameters

The following parameters apply to all commands:

| Argument | Short | Description |
|------|--------|------|
| `--help` | `-h` | Show help information |
| `--version` | `-V` | Show version information |
| `--verbose` | `-v` | Show verbose output (stackable `-vv`/`-vvv`) |
| `--no-color` | | Disable colored output (suitable for CI / log collection) |
| `--no-banner` | | Skip the startup banner (for scripted calls / CI scenarios; automatically silent on non-interactive terminals and when `ERISPULSE_NO_BANNER=1`) |
| `--yes` | `-y` | Automatically confirm all interactive prompts (non-interactive run) |

---

## Environment Diagnostics

### doctor

> [!NOTE]
> This command requires ErisPulse **2.7.0+**.

Diagnose the current CLI runtime environment and output a health report. Used to troubleshoot "why won't it install / connect" type issues.

| Argument | Description |
|------|------|
| `--verbose` | Show detailed diagnostic information |
| `--fix` | After diagnosis, attempt automatic repair of fixable issues |

**Check items**:
- **Python**: interpreter version and path
- **Install backend**: whether `uv` or `pip` is used
- **Target interpreter**: the target Python environment where packages are actually installed
- **Config file**: whether `config/config.toml` exists
- **Component configuration**: declarative configuration completeness of installed components ("installed but won't run" is often due to missing required fields)
- **Configuration pollution** (2.11.1+): scans for residual keys left over from historical upgrades (shadow state keys bound by older runtime versions, orphaned config sections) and reports upon detection
- **PyPI connectivity**: whether PyPI is reachable (and shows the number of components discovered)
- **System proxy**: whether a proxy is detected

**Automatic repair (`--fix`)**:
- Missing `config.toml` → generates an initial config file in the current language (same source as `init` project creation)
- Component configuration "Incomplete" → launches the interactive configuration wizard one by one to complete required fields (in non-interactive environments, prompts to use `epsdk config <name>` instead)
- Configuration pollution residual keys → lists their sources and deletes them after confirmation (tomlclass lossless path, comments and order preserved)
- Issues requiring manual intervention such as a too-low Python version or unreachable PyPI → outputs action recommendations only

```bash
# Run environment diagnostics
epsdk doctor

# Use the alias
epsdk diag

# Diagnose and attempt automatic repair
epsdk doctor --fix
```

---

## Interactive Installation

Running `epsdk install` without a package name enters interactive installation:

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

# Upgrade a module
epsdk install Weather -U
```

### Listing Components

```bash
# List all components
epsdk list

# List adapters only
epsdk list -t adapters

# List upgradable components only
epsdk list -o

# View remotely available components
epsdk list-remote
```

### Uninstalling Components

```bash
# Uninstall a single component
epsdk uninstall Weather

# Uninstall multiple components
epsdk uninstall Yunhu Weather
```

### Configuring Components

```bash
# View configuration status
epsdk config --list

# Interactively select a target to configure
epsdk config

# Configure a specific adapter
epsdk config yunhu
```

### Upgrading Components

```bash
# Upgrade all components
epsdk upgrade

# Upgrade a specific component
epsdk upgrade Weather

# Force upgrade
epsdk upgrade -f
```

### Running the Project

```bash
# Normal run
epsdk run main.py

# Hot reload mode
epsdk run main.py --reload
```

### Switching Language

```bash
# Interactively select a language
epsdk i18n

# Switch directly to English
epsdk i18n en

# List supported languages
epsdk i18n --list
```

### Generating Type Stubs

```bash
# Generate all type stubs
epsdk types

# Generate module type stubs only
epsdk types --modules-only
```

### Initializing a Project

```bash
# Interactive initialization
epsdk init

# Quick initialization
epsdk init -q -n my_bot
```

### Creating Scaffolding

```bash
# Interactive creation (guided type selection and info filling)
epsdk create

# Create a Module project directly
epsdk create module -n MyModule

# Create an Adapter project directly
epsdk create adapter -n MyAdapter

# Full arguments
epsdk create module -n MyModule -d "Module description" -a "Author" -e "mail@example.com"

# Force overwrite existing directory
epsdk create module -n MyModule -f
```



======
API 参考
======


### 适配器系统 API

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



### 核心模块 API

# Core Module API

> [!TIP]
> **When to read this**: When you need to use core capabilities like storage, configuration, logging, module management, routing, or HTTP client, but can't remember the exact method signatures, quickly refer to this document. Skip if not needed.

This document provides a quick reference for ErisPulse core module APIs, including method signatures and brief descriptions. For detailed usage and examples, please click the "Full Documentation" links for each module.

## Storage Module

A key-value storage system based on configurable backends (SQLite/MySQL/PostgreSQL), supporting generic SQL chain query, with backend switching via configuration, see [Storage Backends](../advanced/storage-backends.md).

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

### Transaction Operations

```python
with sdk.storage.transaction():
    sdk.storage.set("key1", "value1")
    sdk.storage.set("key2", "value2")
```

### Attribute Access

```python
sdk.storage.my_key          # equivalent to sdk.storage.get("my_key")
sdk.storage.my_key = "val"  # equivalent to sdk.storage.set("my_key", "val")
```

### SQL Chain Query

The Storage module provides a chain-call style generic SQL query builder, supporting CRUD operations for custom tables.

```python
sdk.storage.CreateTable("users", {
    "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
    "name": "TEXT NOT NULL",
})

sdk.storage.Table("users").Insert({"name": "Alice"}).Execute()
rows = sdk.storage.Table("users").Select("name").Where("id > ?", 0).Execute()
```

> For the complete chain query API (Select/Insert/Update/Delete/Where/OrderBy/Limit, AlterTable, transactions, etc.), see [SQL Query Builder](../advanced/sql-builder.md).

### Storage Backend Abstraction

`StorageManager` inherits from `BaseStorage` abstract base class, supporting extension to other storage media (Redis, MySQL, etc.).

```python
from ErisPulse.Core.Bases.storage import BaseStorage, BaseQueryBuilder
```

### Asynchronous Interfaces

The Storage and Config modules both provide asynchronous methods (prefixed with `a`): **Asynchronous is the native main interface, synchronous methods are compatibility layers** (internal bridge to background event loop execution). Existing synchronous code does not need modification; in new code within asynchronous handlers, prefer asynchronous methods.

```python
# Asynchronous storage
value = await sdk.storage.aget("key")
await sdk.storage.aset("key", "value")
await sdk.storage.adelete("key")
keys = await sdk.storage.aget_all_keys()
await sdk.storage.aclear()

# Asynchronous batch operations
values = await sdk.storage.aget_multi(["k1", "k2"])
await sdk.storage.aset_multi({"k1": "v1", "k2": "v2"})
await sdk.storage.adelete_multi(["k1", "k2"])

# Asynchronous configuration
value = await sdk.config.agetConfig("MyModule.key")
await sdk.config.asetConfig("MyModule.key", "value")
await sdk.config.aforce_save()
await sdk.config.areload()
```

## Config Module

TOML-based configuration file management, supporting dot-separated key paths.

### API Overview

| Method | Description |
|------|------|
| `getConfig(key, default)` | Read configuration, supports dot paths like `"MyModule.subkey"` |
| `getAllConfig()` | Full configuration snapshot (deep copy, including uncommitted pending values) |
| `setConfig(key, value, immediate=False)` | Write configuration. If `immediate=True`, immediately save to file |
| `delConfig(key, immediate=False)` | Delete configuration key (distinct from setting to empty), remove from file; triggers `config.set` event (`new_value=None`) |
| `force_save()` | Forcefully write in-memory configuration to file |
| `reload()` | Reload configuration from file |
| `agetConfig(key, default)` | Asynchronously read configuration |
| `agetAllConfig()` | Asynchronously get full configuration snapshot |
| `asetConfig(key, value, immediate)` | Asynchronously write configuration |
| `adelConfig(key, immediate)` | Asynchronously delete configuration key (behavior same as `delConfig`) |
| `aforce_save()` | Asynchronously force save |
| `areload()` | Asynchronously reload |

### Examples

```python
config = sdk.config.getConfig("MyModule", {})
value = sdk.config.getConfig("MyModule.timeout", 30)

snapshot = sdk.config.getAllConfig()          # Full snapshot (deep copy)
sdk.config.delConfig("MyModule.deprecated")  # Delete key (delayed write)

sdk.config.setConfig("MyModule", {"key": "value"})
sdk.config.setConfig("MyModule.timeout", 60, immediate=True)

# Asynchronous interface (prefer in asynchronous handlers)
snapshot = await sdk.config.agetAllConfig()
await sdk.config.adelConfig("MyModule.deprecated")  # Asynchronously delete key
```

> `setConfig` defaults to delayed write (batch save every 5 seconds), setting `immediate=True` immediately persists to the configuration file. Configuration changes trigger the `config.set` lifecycle event.
> `delete` also supports delayed write and `config.set` event (`new_value=None`), existing `on_config_update` listeners require zero changes to detect deletion.

## Logger Module

Modular logging system, based on Rich output, supports child loggers and module-level control.

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
# TRACE is the lowest level, outputs detailed framework internal debug information (event dispatch, routing registration, etc.)
sdk.logger.set_level("TRACE")                          # Enable all logs
```

### Log Subscription (Push Mode)

For modules like Dashboard to receive structured logs in real-time, supports level filtering and historical replay.

> **Explicitly subscribe to lower-level logs**: The `min_level` of a subscriber can be lower than the global log level. In this case, low-level logs are **only pushed to matching subscribers**, not output to console, nor written to memory, thus avoiding pollution of the main log stream.
>
> ```python
> # Global is INFO, still can individually subscribe to DEBUG logs
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
    #     "message": "Strict mode:...",
    # }
    pass

# Direct call approach
sdk.logger.handler("my-handler", min_level="INFO")(on_log)
sdk.logger.remove_handler("my-handler")
```

| Method | Description |
|------|------|
| `handler(id, *, min_level)(func)` | Decorator/inline call dual-use. If `id` is empty, use function name. `min_level` can be lower than global level (low-level logs only push to matching subscribers, not to console/memory). Registering automatically replays historical logs |
| `remove_handler(id)` | Remove subscriber |

### Output Control

```python
sdk.logger.set_output_file("app.log")
sdk.logger.save_logs("log.txt")
sdk.logger.get_logs("MyModule")
sdk.logger.set_memory_limit(1000)
```

## Adapter Module

Adapter manager, managing registration, startup, and shutdown of multi-platform adapters.

### API Overview

| Method | Description |
|------|------|
| `get(platform)` | Get adapter instance |
| `exists(platform)` | Check if adapter is registered |
| `enable(platform)` / `disable(platform)` | Enable/disable adapter |
| `is_enabled(platform)` | Check if enabled |
| `startup(platforms)` / `shutdown(platforms)` | Start/stop adapters |
| `is_running(platform)` | Check if adapter is running |
| `list_running()` | List all running adapters |
| `platforms` | Get list of all platform names |
| `get_info(platform)` | Adapter registration information (json-safe: meta + class name) |
| `get_meta(platform, resolve_i18n=True)` | Adapter introduction metadata (aligned with `module.get_meta`, supports i18n resolution) |

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

Module manager, managing plugin registration, loading, and unloading.

### API Overview

| Method | Description |
|------|------|
| `get(name)` | Get module instance or lazy-loaded proxy (returns proxy if registered but not loaded) |
| `exists(name)` | Check if registered |
| `is_loaded(name)` | Check if loaded |
| `is_enabled(name)` | Check if enabled |
| `enable(name)` / `disable(name)` | Enable/disable module |
| `load(name)` / `unload(name)` | Load/unload module |
| `call(module, method, *args, timeout=None, **kwargs)` | Cross-module call to target module's service method (protocolized RPC) |
| `list_registered()` | List registered modules |
| `list_loaded()` | List loaded modules |
| `get_info(name)` | Get module information |
| `get_status_summary()` | Get module status summary |

### Attribute Access

```python
module = sdk.module.get("ModuleName")
module = sdk.module.ModuleName
module = sdk.ModuleName  # Equivalent shortcut
```

### Inter-Module Calls (RPC)

```python
# Protocolized call: typed errors / lazy module auto-wake-up / owner attribution / timeout semantics
result = await sdk.module.call("Chat", "get_history", session_id, n=20)
```

Difference between `module.call()` and direct service access `sdk.module.Chat.get_history(...)`:

| | `module.call()` | Direct attribute access |
|---|---|---|
| Target not registered/enabled | Throws `ModuleNotAvailableError` | Throws `AttributeError` |
| Lazy-loaded module | Auto-wake-up | Async module initialization throws RuntimeError |
| `current_owner` | Attributed to target module | Retains caller |
| Timeout | Default 30s, can be overridden | None |
| Scope audit | `actions.<caller>.call` | None |

### Service Contract (`meta.services`)

Service provider declares a white-listed external API in `get_meta()`'s `services` field (symmetrical with `commands`), tightening the call surface after declaration:

```python
class ChatModule(BaseModule):
    @staticmethod
    def get_meta() -> ModuleMeta:
        return ModuleMeta(services=["get_history", "translate"])

    async def get_history(self, session_id, n=20): ...
```

- **Default = Developer-agnostic**: If `services` is not declared, any **public** method can be called (backward compatibility), private methods with underscore are always forbidden; the main control for restrictions is on the user-side scope configuration
- After declaration: Only methods in the white-list are allowed, calling beyond the list throws `ServiceNotProvidedError`
- Caller restriction: `scope.set_action("CallerModule", "call", deny="Chat.get_history")`

**Service Description (`description`)**: `services` supports dict form to declare description for each service (supports plain string or i18n dict), for service directory / AI call point description consumption:

```python
return ModuleMeta(
    services=[
        "get_history",                              # Simple form: description automatically takes the first line of method docstring
        {"name": "translate", "description": "Translate text into specified language"},
        {"name": "summarize", "description": {"i18n": "Chat.meta.svc.summarize", "default": "Summarize conversation"}},
    ],
)
```

Description resolution priority: **Explicit description (i18n resolved to current language) > First line of method docstring > Empty string**.

### Service Directory (`services`)

```python
sdk.module.services()
# {'Chat': [{'name': 'get_history', 'signature': '(session_id, n=20)',
#            'description': 'Get conversation history'}]}

sdk.module.services("Chat")  # Query only specific module
```

Only lists modules that explicitly declare `meta.services`; each service includes method signature string and description text, providing data foundation for MCP (exposing call points to AI).

> Directed event delivery belongs to the lifecycle layer: `lifecycle.emit(event, data, to="ModuleName")`, see [Inter-Module Communication](../advanced/module-communication.md).

## Lifecycle Module

Event-driven lifecycle manager, providing event submission and listening functionality.

### API Overview

| Method | Description |
|------|------|
| `on(event, priority=0)` | Decorator to register event handler, supports dot matching and wildcard `*` |
| `register(event, handler, priority=0)` | Function-style registration of handler |
| `unregister(event, handler=None)` | Remove handler |
| `emit(event, data, to=None)` | Asynchronously trigger event; if `to` specifies owner, deliver only to that module |
| `emit_sync(event, data, to=None)` | Synchronously trigger event (in asynchronous handlers, scheduled via create_task) |
| `submit_event(event_type, msg, data, source, to=None)` | Submit standard format event (compatible with old version) |
| `start_timer(id)` / `stop_timer(id)` | Performance timer |

### Examples

```python
@sdk.lifecycle.on("module.init")
async def handle_module_init(event_data):
    print(f"Module initialized: {event_data}")

@sdk.lifecycle.on("module")
async def handle_any_module_event(event_data):
    print(f"Module event: {event_data}")

await sdk.lifecycle.emit("custom.event", {"key": "value"})

# Directed delivery: only deliver to hooks registered by Chat module
await sdk.lifecycle.emit("message_received", {"text": "hi"}, to="Chat")
```

> For the complete list of standard events and detailed usage, see [Lifecycle Management](../advanced/lifecycle.md).

## Router Module

HTTP/WebSocket routing manager, based on FastAPI + Uvicorn, supports decorator routing, middleware, grouping, rate limiting, CORS.

> For the complete routing API documentation (decorator routing, WebSocket, middleware, rate limiting, CORS, security headers, etc.), see [Router Manager](../advanced/router.md).

### Quick Reference

```python
# HTTP route
@sdk.router.get("MyModule", "/api")
async def handler(request: HttpRequest):
    return {"status": "ok"}

# WebSocket route
@sdk.router.ws("MyModule", "/ws")
async def ws_handler(ws: WebSocketConnection):
    async for text in ws.iter_text():
        await ws.send_text(f"Echo: {text}")

# Route grouping
group = sdk.router.group("MyModule", prefix="/v1")
@group.get("/users")
async def list_users(request: HttpRequest):
    return {"users": []}
```

## HTTP Client Module

Unified network client, aggregating HTTP requests, WebSocket connections, connection pool management, automatic retries, request statistics, and lifecycle event integration.

> For the complete network client documentation (request methods, response objects, WebSocket client, exception hierarchy, etc.), see [Network Client](../advanced/http-client.md).

### Quick Reference

```python
from ErisPulse.Core import client

# HTTP request
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
|------|------|
| `sdk` | SDK initialization status, Python version, runtime platform, timestamp |
| `adapters` | List of registered/started adapters, online status of Bots per platform |
| `modules` | List of registered/enabled/disabled/lazy-loaded modules |
| `events` | Number of handlers for various event types (message/notice/request/meta/commands) |
| `router` | Server running status, number of HTTP/WebSocket routes |

> [!NOTE]
> Added in ErisPulse **2.5.2+**

## Interaction Sessions

Manages wait_reply suspension and session mutual exclusion leases (`sdk.interaction`).

### Common Methods

```python
# Session timeout reminder: 5 minutes without reply will remind, user reply cancels automatically
reminder = event.remind(300, "Still there?")
reminder.cancel()  # Manually cancel

# Timeout escalation: guaranteed delivery at the deadline (not cancelled by reply)
event.escalate(1800, lambda e: notify_master("30 minutes unhandled"))

# Multi-path waiting: first come, first served
which, reply = await event.select(
    event.expect(pattern="agree*", user="A"),
    event.expect(pattern="reject*", user="B"),
    timeout=60,
)

# Session-level waiting: reply from anyone in the same group can match
reply = await event.wait_reply(session=True, prompt="Can someone help answer?")

# Query current session ownership (who is interacting with this user)
owner = sdk.interaction.get_owner_of(event)

# Declare session mutual exclusion lease (returns None if occupied)
lease = sdk.interaction.acquire(event)
if lease:
    try:
        ...  # Exclusive interaction
    finally:
        lease.release()

# Context manager form (throws SessionOccupiedError if occupied)
with sdk.interaction.hold(event) as lease:
    ...

# Suspend session count
sdk.interaction.counts()  # {'waits': 2, 'leases': 1, 'timers': 3, 'owners': {'Chat': 3}}
```

When modules are unloaded or adapters are shut down, their suspended waits and timers are automatically canceled (waits immediately return `None`), and reply matches automatically recheck scope permissions (if user is blacklisted/module is unbound, wait is terminated).

> [!NOTE]
> This section's capabilities were added in ErisPulse **2.8.0+**

## Transcript Session Inbox

Automatic recording and querying of recent message flows per session (`sdk.transcript`), serving as a public foundation for AI conversation, anti-repetition, and other context-memory modules.

### Common Methods

```python
# Convenient query (recommended): recent 20 messages of current session (including user and bot, in ascending time order)
messages = await event.history(20)
for m in messages:
    print(m["role"], ":", m["text"])

# Manager API
sdk.transcript.append(event, "user", "text")
sdk.transcript.get(event, n=20)
sdk.transcript.clear(event)
```

Configuration (`ErisPulse.transcript`): `enabled` (default enabled), `max_per_session` (per-session limit, default 50), `ttl_hours` (global expiration time, default 168 hours). Data is stored in a separate SQLite table, with lazy cleanup for over-limit/expired entries.

> [!NOTE]
> This section's capabilities were added in ErisPulse **2.8.0+**



====
高级主题
====


### HTTP 客户端

# Network Client

> [!TIP]
> **When to read this**: When you need to make outbound HTTP / WebSocket requests. Skip if not needed, it doesn't affect the use of other features.

ErisPulse provides a unified network client that aggregates HTTP requests, WebSocket connections, and connection pool management. Modules and adapters **must** use this client instead of directly importing third-party libraries such as `aiohttp`, `httpx`, or `requests`.

## Overview

The main functions of the network client are:

- **Unified interface**: Provides `get` / `post` / `put` / `delete` / `patch` / `request` methods
- **WebSocket client**: Establishes a client-side WebSocket connection via `ws_connect`
- **Automatic logging**: All requests are automatically logged and their statistics recorded
- **Lifecycle integration**: Each request triggers the `client.request` lifecycle event, and WS connections trigger the `client.ws.connect` event
- **Retry support**: Configurable automatic retry counts and intervals
- **Timeout control**: Independent connection and request timeouts
- **Connection pool reuse**: Connection pool management based on `aiohttp.ClientSession`
- **Exception system**: aiohttp exceptions are automatically converted to ErisPulse exceptions (ClientError system)

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
from ErisPulse import client   # 2.10+ root import (ErisPulse.Core.client deep path is still compatible)

ws = await client.ws_connect("wss://example.com/ws")

async for text in ws.iter_text():
    await ws.send_text(f"Echo: {text}")
```

#### Outbound connections automatically join the pool (2.10+)

Connections established via `ws_connect` are **automatically registered** into the framework's connection pool (set `track=False` to disable):
They can be viewed via `connections.list(owner=...)` and broadcasted to; connections are automatically unregistered when closed or disconnected remotely;
**When modules are unloaded or adapters are stopped, the framework closes all outbound connections under their names**, preventing leaks.

```python
from ErisPulse import client, connections

ws = await client.ws_connect("wss://example.com/ws")
print(ws.id, ws.owner)   # Already registered: connection id and owner

# When the owner context is unavailable (e.g., tool thread callback), explicitly specify the owner so it can be automatically recycled on unload:
ws2 = await client.ws_connect("wss://example.com/ws2", owner="MyAdapter")
```

See [Connection Pool and Broadcasting](connections.md).

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
resp.raw          # underlying native response object (currently aiohttp.ClientResponse)

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
# Format: {field name: file object/bytes/(filename, file)/(filename, file, content_type)}
resp = await client.post(
    "https://api.example.com/upload",
    data={"description": "avatar"},            # Optional: can carry regular form fields
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

## Parameter Explanation

### HTTP Request Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `url` | `str` | Request URL |
| `params` | `dict[str, str]` | Query parameters (optional) |
| `headers` | `dict[str, str]` | Additional request headers (optional) |
| `data` | `Any` | Request body (form or raw data) (optional) |
| `json` | `Any` | JSON request body (optional) |
| `files` | `dict[str, Any]` | File upload fields (optional, automatically builds multipart/form-data) |
| `timeout` | `float` | Timeout for this request (seconds) (optional, overrides default value) |
| `max_retries` | `int` | Maximum retry attempts for this request (optional, overrides default value) |

### ws_connect Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `url` | `str` | WebSocket server URL |
| `headers` | `dict[str, str]` | Additional request headers (optional) |
| `heartbeat` | `float` | Heartbeat interval in seconds (optional) |

## Timeout and Retries

```python
from ErisPulse.Core import Client

# Create a client with custom timeouts
client = Client(
    timeout=60,           # Total request timeout 60s
    connect_timeout=5,    # Connection timeout 5s
    max_retries=3,        # Failures automatically retry 3 times
    retry_delay=2,        # Retry interval 2s
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

The `client.request` event is triggered after each request completes, which can be used for monitoring:

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
# As a context manager, automatically close the session
async with Client(timeout=30) as client:
    resp = await client.get("https://httpbin.org/get")
    data = await resp.json()
```

## WebSocket Client

Establish a WebSocket client connection via `client.ws_connect()`, returning a `ClientWebSocket` object. The client and server-side WebSocket share the same `WebSocketConnectionBase` base class, with identical send/receive/iter interfaces.

### Basic Usage

```python
from ErisPulse.Core import client

ws = await client.ws_connect("wss://example.com/ws", heartbeat=30)

await ws.send_text("Hello")
await ws.send_bytes(b"\x00\x01\x02")
await ws.send_json({"type": "ping"})
```

### Receiving Messages

#### Advanced Methods (Recommended)

Automatically filter message types, and throw `WebSocketDisconnect` on disconnection:

```python
from ErisPulse.Core import client
from ErisPulse.Core.Bases.errors import WebSocketDisconnect

ws = await client.ws_connect("wss://example.com/ws")

# Single message receive
text = await ws.receive_text()    # str
data = await ws.receive_bytes()   # bytes
obj = await ws.receive_json()     # dict / list

# Iterate receive (automatically stops on disconnection)
async for text in ws.iter_text():
    print(text)

async for data in ws.iter_bytes():
    print(data)

async for obj in ws.iter_json():
    print(obj)
```

#### Low-Level Methods

Use `receive()` and `iter_messages()` to handle raw message types, which allows distinguishing TEXT / BINARY / CLOSE / ERROR:

```python
from ErisPulse.Core import client
from ErisPulse.Core.Bases.websocket import WSMessage

ws = await client.ws_connect("wss://example.com/ws")

# Single message receive raw message
msg = await ws.receive()
# msg.type  -> WSMessage.TEXT / WSMessage.BINARY / WSMessage.CLOSE / WSMessage.ERROR
# msg.data  -> str | bytes | None

# Iterate raw messages (automatically stops on CLOSE/ERROR)
async for msg in ws.iter_messages():
    if msg.type == WSMessage.TEXT:
        print(f"Text: {msg.data}")
    elif msg.type == WSMessage.BINARY:
        print(f"Binary: {len(msg.data)} bytes")
```

### WSMessage

`WSMessage` is a unified WebSocket message type, independent of the underlying library:

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

### Closing Connection

```python
await ws.close(code=1000, reason="Normal closure")
```

## Exception System

ErisPulse defines a unified exception hierarchy. Requests initiated via `sdk.client` will automatically convert underlying aiohttp exceptions into ErisPulse exceptions.

> **Backward Compatibility**: Old modules/adapters that directly use `aiohttp.ClientSession` are completely unaffected. Exception conversion only occurs when requests are initiated via `sdk.client`. Code that directly uses aiohttp still catches `aiohttp.ClientError` and other native exceptions. Both approaches can coexist.

### Exception Hierarchy

```
ErisPulseError
├── ClientError                  # Base class for all HTTP/WS client request exceptions
│   ├── ClientConnectionError    # Connection failed (DNS resolution failed, connection refused, network unreachable)
│   ├── ClientTimeoutError       # Connection timeout or request timeout
│   └── HTTPStatusError          # HTTP 4xx/5xx status code error
└── WebSocketError               # WebSocket exception base class
    └── WebSocketDisconnect      # WebSocket connection disconnected (common for both client and server)
```

### Exception Handling

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

# HTTP request exception handling
try:
    resp = await client.get("https://api.example.com/data")
    data = await resp.json()
except ClientConnectionError:
    print("Unable to connect to the server")
except ClientTimeoutError:
    print("Request timeout")
except ClientError as e:
    print(f"Request failed: {e}")

# WebSocket exception handling
try:
    ws = await client.ws_connect("wss://example.com/ws")
    async for text in ws.iter_text():
        await ws.send_text(f"Echo: {text}")
except WebSocketDisconnect as e:
    print(f"Connection disconnected: code={e.code}, reason={e.reason}")
except WebSocketError as e:
    print(f"WebSocket error: {e}")
```

### Unified Exception Handling

Use `ClientError` to catch all HTTP/WS client request exceptions:

```python
from ErisPulse.Core.Bases.errors import ClientError

try:
    resp = await client.get("https://api.example.com/data")
except ClientError as e:
    print(f"Client error: {e}")
```

### HTTPStatusError

When you need to check the status code after a request and throw an exception, you can manually use:

```python
from ErisPulse.Core.Bases.errors import HTTPStatusError

resp = await client.get("https://api.example.com/data")
if resp.status >= 400:
    raise HTTPStatusError(resp.status, await resp.text())
```

## Using in Adapters

Adapters can use the global client or create their own client instance to send platform API requests:

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

> You can also use `from ErisPulse import sdk` to access `sdk.client`, with the same effect.

## Best Practices

1. **Prefer the global client**: Use `from ErisPulse.Core import client` to get the global singleton for easier framework management and monitoring
2. **Avoid directly importing aiohttp**: Use `client` instead of `aiohttp.ClientSession` to allow future changes to the underlying implementation without code modification. Old code directly using aiohttp still works normally, and both approaches can coexist
3. **Use the ErisPulse exception system**: When using `sdk.client` for requests, catch `ClientError` instead of `aiohttp.ClientError` to ensure code independence from specific HTTP libraries. Old code using aiohttp directly is unaffected
4. **Set timeouts reasonably**: Set appropriate timeout values based on API response speed to avoid long blocking
5. **Use retry mechanisms**: Enable retries for unstable APIs to improve reliability
6. **Monitor request statistics**: Use `sdk.client.stats` or the `client.request` lifecycle event to monitor request situations
7. **Use advanced WebSocket methods**: Prefer advanced methods like `iter_text` / `iter_json`, and only use `iter_messages` when distinguishing message types is needed



### SQL 查询构建器

# SQL Query Builder

> [!TIP]
> **When to read this**: When you need chain-style SQL queries or custom storage backends. If not needed, you can skip it without affecting the use of other features.

The Storage module of ErisPulse provides a general-purpose SQL query builder with a chain-call style, supporting creation, querying, updating, and deletion operations for custom tables.

## Architecture Design

```
Bases/storage.py                    Core/storage.py
┌─────────────────────┐             ┌──────────────────────────┐
│  BaseStorage (ABC)  │◄────────────│  StorageManager          │
│  BaseQueryBuilder   │             │  (backend dispatch:      │
│    (ABC)            │             │   sqlite/mysql/postgres) │
└─────────────────────┘             │  SQLiteQueryBuilder      │
                                    │  AlterTableBuilder       │
                                    └──────────────────────────┘
```

- `BaseStorage` / `BaseQueryBuilder` are abstract base classes that define unified interfaces; the framework includes three built-in implementations: SQLite / MySQL / PostgreSQL (custom backends can also be extended following this pattern, see [Storage Backends](storage-backends.md))
- `StorageManager` dispatches the specific backend according to the `ErisPulse.storage.backend` configuration, with SQLite as the default, ensuring full backward compatibility

## Importing

```python
from ErisPulse import sdk
# or
from ErisPulse.Core import storage

# ABC base classes (for type annotation or custom implementation)
from ErisPulse.Core.Bases.storage import BaseStorage, BaseQueryBuilder
```

## Table Management

### Creating a Table

```python
sdk.storage.CreateTable("users", {
    "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
    "name": "TEXT NOT NULL",
    "age": "INTEGER DEFAULT 0",
    "email": "TEXT"
})
```

### Checking if a Table Exists

```python
if sdk.storage.HasTable("users"):
    print("users table exists")
```

### Dropping a Table

```python
sdk.storage.DropTable("users")
```

### Modifying Table Structure

```python
# Adding a column
sdk.storage.AlterTable("users").AddColumn("email", "TEXT").Execute()

# Renaming a table
sdk.storage.AlterTable("users").RenameTo("members").Execute()

# Chaining multiple operations
sdk.storage.AlterTable("users") \
    .AddColumn("phone", "TEXT") \
    .AddColumn("address", "TEXT") \
    .Execute()
```

## Chainable Queries

### Inserting Data

```python
# Single row insertion (passing a dictionary)
sdk.storage.Table("users").Insert({"name": "Alice", "age": 30}).Execute()

# Batch insertion (passing a list of dictionaries)
sdk.storage.Table("users").InsertMulti([
    {"name": "Bob", "age": 25},
    {"name": "Charlie", "age": 35},
    {"name": "Dave", "age": 40}
]).Execute()
```

### Querying Data

> **Important**: `Select()` returns a `list[tuple]` (list of tuples), not a dictionary. You need to access values by column index.

```python
# Select all columns
rows = sdk.storage.Table("users").Select().Execute()
# rows: [(1, "Alice", 30), (2, "Bob", 25), ...]

# Select specific columns
rows = sdk.storage.Table("users").Select("name", "age").Execute()
# rows: [("Alice", 30), ("Bob", 25), ...]

# Access values by index
for row in rows:
    name = row[0]   # "Alice"
    age = row[1]    # 30
```

#### Converting Tuples to Dictionaries

It is recommended to call `ToDict()` directly on the chain; the SELECT result will automatically be returned as a dictionary (column name → value):

```python
# ToDict chain: result is list[dict], column names are automatically taken from query metadata (SELECT * is also supported)
rows = sdk.storage.Table("users").Select("name", "age").ToDict().Execute()
# rows: [{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}, ...]

for row in rows:
    print(row["name"], row["age"])

# ExecuteOne also works
row = sdk.storage.Table("users").Select("name", "age") \
    .Where("id = ?", 1) \
    .ToDict() \
    .ExecuteOne()
# row: {"name": "Alice", "age": 30} or None
```

> `ToDict()` is a chainable marker (returns self): chains without calling it retain the original `list[tuple]` behavior, fully backward compatible; `copy()` will preserve this flag.

Manual zip method (equivalent to ToDict, suitable for scenarios where the chain cannot be modified):

```python
columns = ["id", "name", "age"]
rows = sdk.storage.Table("users").Select(*columns).Execute()

# Method 1: zip in loop
for row in rows:
    record = dict(zip(columns, row))
    print(record["name"], record["age"])

# Method 2: convert to list of dictionaries at once
records = [dict(zip(columns, row)) for row in rows]
```

#### Getting a Single Record

```python
row = sdk.storage.Table("users").Select("name", "age") \
    .Where("id = ?", 1) \
    .ExecuteOne()

# row is a tuple or None
if row is not None:
    name = row[0]  # "Alice"
    age = row[1]   # 30
```

### Filtering Conditions

> `Where(condition, *params)` supports passing multiple parameters, corresponding to multiple `?` placeholders.

```python
# Single condition (one placeholder, one parameter)
rows = sdk.storage.Table("users").Select("name") \
    .Where("age > ?", 18) \
    .Execute()

# Using multiple placeholders in one Where
rows = sdk.storage.Table("users").Select("name") \
    .Where("age > ? AND age < ?", 20, 40) \
    .Execute()

# Multiple Where calls (AND connected)
rows = sdk.storage.Table("users").Select("name") \
    .Where("age > ?", 20) \
    .Where("age < ?", 40) \
    .Execute()
```

### Sorting and Pagination

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

### Updating Data

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

### Deleting Data

```python
# Conditional delete
sdk.storage.Table("users") \
    .Delete() \
    .Where("name = ?", "Bob") \
    .Execute()

# Full delete
sdk.storage.Table("users").Delete().Execute()
```

### Counting and Existence Check

```python
# Count
count = sdk.storage.Table("users").Count()
count = sdk.storage.Table("users").Where("age > ?", 18).Count()

# Existence check
exists = sdk.storage.Table("users").Where("name = ?", "Alice").Exists()
```

## Reusing Query Conditions

Use `copy()` to deep copy the builder and reuse base conditions:

```python
base = sdk.storage.Table("users").Where("age > ?", 20)

# Query based on the same condition
rows = base.copy().Select("name").OrderBy("name").Limit(5).Execute()

# Count based on the same condition
count = base.copy().Count()

# Existence check based on the same condition
exists = base.copy().Where("name = ?", "Alice").Exists()
```

## Resetting the Builder

```python
builder = sdk.storage.Table("users").Select("name").Where("age > ?", 18)
builder.clear()

# Rebuild the query
builder.Select("name", "age").Where("name = ?", "Alice")
rows = builder.Execute()
```

## Using in Transactions

Chainable operations fully support transactions:

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

## Asynchronous Native API

Starting from version 2.8.0, the storage layer uses asynchronous operations as the native primary interface. All terminating methods have corresponding asynchronous versions with an `a` prefix. It is recommended to use these in asynchronous handlers (to avoid temporary blocking of the event loop due to synchronous compatibility layers):

```python
# Asynchronous transaction
async with sdk.storage.atransaction():
    await sdk.storage.aset("key1", "value1")
    await sdk.storage.aset("key2", {"nested": True})

# Asynchronous chainable query
rows = await sdk.storage.Table("users").Select("name", "age").ToDict().aExecute()
row = await sdk.storage.Table("users").Select("*").Where("id = ?", 1).aExecuteOne()
total = await sdk.storage.Table("users").Where("age > ?", 18).aCount()
exists = await sdk.storage.Table("users").Where("name = ?", "Alice").aExists()

# Asynchronous KV operations
await sdk.storage.aset("app.name", "MyApp")
value = await sdk.storage.aget("app.name")
keys = await sdk.storage.aget_all_keys()
```

| Synchronous (Compatibility Layer) | Asynchronous Native |
|------|------|
| `get` / `set` / `delete` | `aget` / `aset` / `adelete` |
| `get_all_keys` / `clear` | `aget_all_keys` / `aclear` |
| `get_multi` / `set_multi` / `delete_multi` | `aget_multi` / `aset_multi` / `adelete_multi` |
| `transaction()` | `atransaction()` |
| `CreateTable` / `DropTable` / `HasTable` | `aCreateTable` / `aDropTable` / `aHasTable` |
| `Execute` / `ExecuteOne` / `Count` / `Exists` | `aExecute` / `aExecuteOne` / `aCount` / `aExists` |

## Return Value Description

| Operation | Return Type | Description |
|------|---------|------|
| `Select().Execute()` | `list[tuple]` | List of tuples, ordered by column |
| `Select().ExecuteOne()` | `tuple \| None` | Single tuple or None |
| `Insert().Execute()` | `int` | Number of affected rows |
| `InsertMulti().Execute()` | `int` | Number of inserted rows |
| `Update().Execute()` | `int` | Number of affected rows |
| `Delete().Execute()` | `int` | Number of affected rows |
| `Count()` | `int` | Number of matching rows |
| `Exists()` | `bool` | Whether exists |

### Example of Return Value Handling

```python
# Select returns tuples, access by index
rows = sdk.storage.Table("users").Select("name", "age").Execute()
first_name = rows[0][0]  # First row, first column (name)
first_age = rows[0][1]   # First row, second column (age)

# Recommended: Use column name list + zip to convert to dictionary, code is more readable
cols = ["name", "age"]
rows = sdk.storage.Table("users").Select(*cols).Execute()
for row in rows:
    d = dict(zip(cols, row))
    print(d["name"], d["age"])

# ExecuteOne returns a single tuple or None
row = sdk.storage.Table("users").Select("name").Where("id = ?", 1).ExecuteOne()
name = row[0] if row else None

# Insert/Update/Delete returns number of affected rows
affected = sdk.storage.Table("users").Delete().Where("age < ?", 18).Execute()
print(f"Deleted {affected} records")
```

## Parameterized Queries

All WHERE parameters use `?` placeholders, and parameters are passed as subsequent arguments to `Where()` (not as a tuple or list):

```python
# Correct ✓ — multiple parameters passed individually
sdk.storage.Table("users").Where("age > ? AND name = ?", 18, "Alice").Execute()

# Correct ✓ — multiple Where calls
sdk.storage.Table("users").Where("age > ?", 18).Where("name = ?", "Alice").Execute()

# Incorrect ✗ — do not pass a tuple
sdk.storage.Table("users").Where("age > ? AND name = ?", (18, "Alice")).Execute()
# This will treat the entire tuple as the value for the first placeholder

# Incorrect ✗ — SQL injection risk exists
sdk.storage.Table("users").Where(f"name = '{user_input}'").Execute()
```

### Where Parameter Passing Rules

```python
# Where(condition: str, *params: Any)
# params are variable arguments, passed one by one

# Single parameter
.Where("name = ?", "Alice")

# Multiple parameters
.Where("age > ? AND age < ?", 18, 60)

# LIKE query
.Where("name LIKE ?", "A%")

# IN query (need to manually construct placeholders)
.Where("name IN (?, ?, ?)", "Alice", "Bob", "Charlie")
```

## Custom Storage Backend

Starting from version 2.8.0, the abstract layer uses **asynchronous methods as the native contract**: inherit `BaseStorage` and implement asynchronous abstract methods. Synchronous `get/set/Execute` and others are provided automatically by the base class bridge:

```python
from ErisPulse.Core.Bases.storage import BaseStorage, BaseQueryBuilder

class MyQueryBuilder(BaseQueryBuilder):
    async def aExecute(self):
        # Implement specific execution logic
        ...

    async def aExecuteOne(self):
        ...

    async def aCount(self):
        ...

    async def aExists(self):
        ...


class MyStorage(BaseStorage):
    async def aget(self, key, default=None):
        ...

    async def aset(self, key, value):
        ...

    # Implement other asynchronous abstract methods and transaction connection hook ...
    def Table(self, table_name):
        return MyQueryBuilder(self, table_name)
```

> [!TIP]
> If you do not want to implement transaction connection routing (`conn` keyword argument), keep the class attribute
> `_SUPPORTS_CONN_ROUTING = False` (default), and transaction functionality is still available (with limited isolation).
> Pure SQL backends can directly inherit `Core/Bases/sql_base.py`'s `SQLStorageBase` +
> `SQLQueryBuilder`, requiring only connection management and dialect execution funnel implementation, see
> [Storage Backends](docs/en/storage-backends.md).



### 生命周期管理

# Lifecycle Management

> [!TIP]
> **When to read this**: When you need to subscribe to framework lifecycle events (startup / loading / state change). Skip if not needed, as it won't affect the use of other features.

> **What you'll learn**: The registration / triggering / targeted propagation mechanism of lifecycle events, the differences and selection among the four sets of triggering APIs, and the complete list of pre-buried hook breakpoints in the framework (core / module / adapter / server / message) along with their respective data formats.
>
> **This section does not cover**: Lifecycle methods that modules themselves need to implement (`on_load` / `on_unload`, see [Module Development Guide](../developer-guide/modules/getting-started.md)); the detailed flow of startup stages (see [Startup Flow and Manual Control](startup.md)).

To receive notifications and execute your own logic at key points such as module loading failure, configuration modification, message sending, or command execution (for auditing, statistics, alerting, or interoperation), simply subscribe to the framework's lifecycle events. The framework pre-buried hook breakpoints at each critical node, and you can integrate with `@sdk.lifecycle.on("event name")` in a single line. The complete list of breakpoints is provided at the end of this document.

The system supports three triggering methods:
- `await lifecycle.emit("event", data)` — A concise version, passing arbitrary data (targeted delivery when `to="Owner"`)
- `lifecycle.emit_sync("event", data)` — The synchronous version (used in non-async contexts)
- `await lifecycle.submit_event("event", ...)` — Compatible with the old version, automatically constructs the standard event format

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

# Batch unregister by owner (automatically called by framework during module/adapter unload)
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

### Dot-Structure Events

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

### Directed Propagation (`emit to=`)

> [!NOTE]
> This feature requires ErisPulse **2.8.0+**.

When `emit()` specifies the `to` parameter, it enters directed propagation: the event is only distributed to handlers registered under the specified owner (hooks registered in a module's `on_load` automatically belong to the module), while other modules and wildcard `*` handlers are not notified.

```python
# Emitter: Event only delivered to hooks registered by the Chat module
await sdk.lifecycle.emit("message_received", {"text": "hi"}, to="Chat")

# Subscriber (within Chat module): Register a hook with the same name; owner is automatically recorded during registration
@sdk.lifecycle.on("message_received")
async def on_message_received(data): ...

@sdk.lifecycle.on("message")   # Dot-structure parent prefixes also apply (filtered by owner)
async def on_any(data): ...
```

- If the target owner has no registered hooks → the event is **not consumed** (use `has_handlers()` to detect beforehand)
- If `data` is a dict, `_trace_id` is automatically included (does not overwrite existing values)
- `emit_sync` / `submit_event` also support the `to=` parameter
- Three-layer module communication model (RPC / directed / broadcast) is described in [Module Communication](module-communication.md)

### One-time Registration (`once`)

Since 2.7.0, handlers registered via `lifecycle.once()` are automatically unregistered after one trigger, suitable for one-time hooks such as "first ready":

```python
@sdk.lifecycle.once("core.init.complete")
async def on_first_ready(data):
    print("First ready, will not trigger again")
```

- Same priority semantics as `on()` (`priority` value higher means earlier execution)
- Automatic unregistration, no need for manual `unregister`
- Supports both synchronous and asynchronous handlers

### Listener Query (`has_handlers`)

In hot-path short-circuit scenarios, use `has_handlers()` to check if there are listeners beforehand, avoiding unnecessary event traversal and task scheduling:

```python
if sdk.lifecycle.has_handlers("message.sending"):
    await sdk.lifecycle.emit("message.sending", send_ctx)
```

- Covers **exact event name**, **wildcard `*`**, and **parent event** matching
- Returns `False` if there are no listeners, allowing safe skipping of `emit`

## Overview of Hook Breakpoints

A typical lifecycle event sequence diagram of a message from platform entry to framework processing completion:

```mermaid
sequenceDiagram
    participant P as Platform
    participant A as Adapter
    participant F as Framework Core
    participant M as Module Processor

    P->>A: Native event arrives
    A->>F: adapter.event.receive (earliest)
    F->>F: event.pre_process (before processor execution)
    F->>M: Dispatch to processor (commands/messages/notifications, etc.)
    M->>M: command.matched / command.executed
    M->>F: event.reply()
    F->>F: message.sending (before sending)
    F->>A: SendDSL send
    A->>P: Send to platform
    A->>F: message.sent (after sending)
    F->>F: adapter.event.dispatched (after dispatching)
```

The framework provides the following built-in hook breakpoints, and users can listen to any breakpoint to implement custom logic via `@sdk.lifecycle.on()`.

### Core Initialization

| Hook Name | Trigger Timing | Data |
|---------|---------|------|
| `core.init.start` | SDK initialization starts | `{}` |
| `core.init.stage` | Each initialization stage begins (emitted in background) | `{"stage": str}`; values: `discovery` / `adapter_register` / `adapter_start` / `module_register` / `module_init` / `adapter_start_deferred` / `router_start` |
| `core.init.complete` | SDK initialization completes | `{"duration": float, "success": bool, "stages": {stage: float}, "adapters": {"enabled": [str], "disabled": [str]}, "modules": {"enabled": [str], "disabled": [str]}, "error": str (only on failure)}` |
| `core.uninit.complete` | SDK de-initialization completes | `{"duration": float, "success": bool, "adapters_closed": int, "modules_unloaded": int, "module_properties_cleared": int, "module_properties_to_clear": [str], "error": str (only on failure)}` |

**Example: Displaying Startup Progress**

```python
@sdk.lifecycle.on("core.init.stage")
def show_stage(data):
    print(f"[Startup] Entering stage: {data['stage']}")
```

### Configuration Changes

| Hook Name | Trigger Timing | Data |
|---------|---------|------|
| `config.set` | A configuration item is modified | `{"key": str, "old_value": Any, "new_value": Any}` |
| `config.updated` | Entire configuration tree is detected changed after editing config.toml externally | `{"old_config": dict, "new_config": dict, "config_file": str}` |

**Example: Configuration Audit**

```python
@sdk.lifecycle.on("config.set")
def audit_config(data):
    print(f"[Audit] {data['key']}: {data['old_value']} -> {data['new_value']}")
```

### Module Lifecycle

| Hook Name | Trigger Timing | Data |
|---------|---------|------|
| `module.register` | A module class is registered to the manager | `{"module_name": str, "success": bool}` |
| `module.load` | Module loading completes (instance successfully created); on failure, payload additionally carries `"error": str, "traceback": str` (failure context can also be queried via `module.last_error(name)`) | `{"module_name": str, "success": bool}` |
| `module.init` | Module initialization completes (including lazy loading) | `{"module_name": str, "success": bool}` |
| `module.before_unload` | First step in the unload pipeline (before `on_unload` and resource release; module instance hook `on_before_unload` is triggered synchronously) | `{"module_name": str, "reason": str}`; `reason` values: `unload` / `reload` / `disable` / `cascade` / `dormant` |
| `module.sleep` | Module hibernation completes (lazy loading sleep: resources are released, automatically awakened on access) | `{"module_name": str, "success": bool}` |
| `module.unload` | Module is unloaded or disabled (`disable` and `unload` provide equivalent notifications to dependents; `on_dependency_lost` contract includes "disabled") | `{"module_name": str, "success": bool}` |
| `module.reload` | Module hot reload completes (including cascading reload of dependencies) | `{"module_name": str, "success": bool, "full": bool, "duration_ms": int}`; single module additionally carries `"identity_changed": bool` (False = old code may still be running in the process, e.g., C extension cache) and `"version_old": str, "version_new": str`; during full reload (`reload_all`), `module_name` is `"All"`, payload additionally carries `"results": dict[str, bool]` |

> **Module instance hook `on_before_unload`**: The optional lifecycle method corresponding to the `module.before_unload` event—`event["reason"]` indicates the reason, suitable for saving state to `sdk.storage` before resource release, and restoring it in `on_load` after awakening/reload (lazy loading hibernation state continuation is based on this). Hook failure only alerts, does not block the unload process.

### Adapter Lifecycle

| Hook Name | Trigger Timing | Data |
|---------|---------|------|
| `adapter.load` | Adapter registration completes | `{"platform": str, "success": bool}` |
| `adapter.reload` | Adapter code-level hot reload completes | `{"adapter_name": str, "success": bool, "full": bool, "duration_ms": int, "identity_changed": bool, "version_old": str, "version_new": str, "was_started": bool, "source": str}`; `identity_changed=False` = old code may still be running in the process |
| `adapter.start` | Adapter starts | `{"platforms": [str]}` |
| `adapter.status.change` | Adapter status changes | `{"platform": str, "status": str, "retry_count": int, "error": str (only on failure)}`; complete status values: `starting` / `started` / `start_failed` / `stopping` / `stopped` / `stop_failed` / `skipped-dependency` / `disabled` |
| `adapter.stop` | Adapter stops | `{"platforms": [str]}` |
| `adapter.stopped` | Adapter stop completes | `{"platforms": [str]}` |
| `adapter.bot.online` | Bot goes online | `{"platform": str, "bot_id": str, "info": dict, "status": str}` |
| `adapter.bot.offline` | Bot goes offline | `{"platform": str, "bot_id": str, "status": str}` |

### Event Reception and Processing

| Hook Name | Trigger Timing | Data |
|---------|---------|------|
| `adapter.event.receive` | External platform event is received (earliest) | `{"platform": str, "event_type": str, "raw_event_type": str}` |
| `adapter.event.blocked` | Middleware blocks the event (returns `False`, event is discarded and does not enter any processor) | `{"middleware": str, "platform": str, "event_type": str, "detail_type": str, "event": dict, "_trace_id": str}` |
| `adapter.event.dispatched` | Event dispatch completes | `{"platform": str, "event_type": str, "raw_event_type": str, "onebot_handlers_count": int}` |
| `event.pre_process` | Event processor begins execution | `{"event_type": str, "platform": str, "detail_type": str}` |

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
| `message.sending` | Message is about to be sent | `{"platform": str, "method": str, "detail_type": str, "target_id": str, "bot_id": str}` |
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
| `command.matched` | Command is matched and about to execute | `{"command": str, "args": list[str], "platform": str, "user_id": str}` |
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
| `server.request` | HTTP request is received | `{"method": str, "path": str, "client_ip": str, "request_id": str}` |
| `server.response` | HTTP response is sent | `{"method": str, "path": str, "status_code": int, "client_ip": str, "request_id": str}` |

> `request_id` is the [X-Request-ID request correlation ID](router.md#request-correlation-idx-request-id): it is prioritized from the client request header, otherwise a UUID is generated automatically. It can be used to link the request and response events.

**Example: Request Logging**

```python
@sdk.lifecycle.on("server.response")
def log_http(data):
    print(f"[HTTP] {data['method']} {data['path']} -> {data['status_code']}")
```

### WebSocket

| Hook Name | Trigger Timing | Data |
|---------|---------|------|
| `server.start` | Router server starts | `{"base_url": str, "host": str, "port": int, "success": bool, "error": str (only on failure)}` |
| `server.stop` | Router server stops | `{}` |
| `server.websocket.connect` | WebSocket connection is established | `{"path": str, "module_name": str, "client_ip": str}` |
| `server.websocket.disconnect` | WebSocket connection is disconnected | `{"path": str, "module_name": str, "reason": str, "error": str (only on abnormal disconnection)}` |

**Example: WebSocket Connection Monitoring**

```python
@sdk.lifecycle.on("server.websocket.connect")
def on_ws_connect(data):
    print(f"[WS] Connection: {data['path']} from {data['client_ip']}")

@sdk.lifecycle.on("server.websocket.disconnect")
def on_ws_disconnect(data):
    print(f"[WS] Disconnection: {data['path']} ({data['reason']})")
```

### Storage Connection Status

Establishment, failure, and recovery of the storage backend connection pool (all emitted in background, do not block storage operations):

| Hook Name | Trigger Timing | Data |
|---------|---------|------|
| `storage.ready` | Storage backend connection pool is ready (first successful pool creation per event loop) | `{"backend": str}` |
| `storage.unreachable` | Connection retry exhaustion enters cooldown period (during which operations fail quickly) | `{"backend": str, "error": str, "cooldown": float}` |
| `storage.recovered` | Cooldown ends, reconnection succeeds, storage is restored | `{"backend": str}` |

**Example: Storage Failure Alert**

```python
@sdk.lifecycle.on("storage.unreachable")
def alert_storage_down(data):
    print(f"[Alert] Storage backend {data['backend']} is unreachable: {data['error']}, automatic reconnection in {data['cooldown']}s")

@sdk.lifecycle.on("storage.recovered")
def notify_storage_back(data):
    print(f"[Recovery] Storage backend {data['backend']} is restored and available")
```

### HTTP Client

Request and connection events of `sdk.client` (all emitted in background):

| Hook Name | Trigger Timing | Data |
|---------|---------|------|
| `client.request.success` | HTTP request succeeds | `{"method": str, "url": str, "status": int, "elapsed": float}` |
| `client.request.failed` | HTTP request finally fails after exhausting retries | `{"method": str, "url": str, "error": str, "attempts": int, "elapsed": float}` |
| `client.ws.connect` | WebSocket connection is established | `{"url": str}` |

### Internationalization

| Hook Name | Trigger Timing | Data |
|---------|---------|------|
| `i18n.language.changed` | Framework language switch (`i18n.set_language`) | `{"language": str, "previous": str}` |

## Standard Event Definitions

```python
STANDARD_EVENTS = {
    "core": ["init.start", "init.stage", "init.complete", "uninit.complete"],
    "module": ["load", "before_unload", "init", "sleep", "unload", "register", "reload"],
    "adapter": [
        "load", "start", "status.change", "reload", "stop", "stopped",
        "event.receive", "event.blocked", "event.dispatched",
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
    "config": ["set", "updated"],
    "storage": ["ready", "unreachable", "recovered"],
    "client": ["request.success", "request.failed", "ws.connect"],
    "i18n": ["language.changed"],
}
```

## Complete API Reference

### Registration and Unregistration

| Method | Description |
|--------|-------------|
| `@lifecycle.on(event, *, priority=0)` | Decorator to register a handler |
| `lifecycle.register(event, handler, *, priority=0)` | Programmatic registration |
| `lifecycle.unregister(event, handler=None)` | Unregister (removes all handlers for the event if handler=None) |

### Triggering

| Method | Description |
|--------|-------------|
| `await lifecycle.emit(event, data=None, *, to=None)` | Asynchronously trigger; handlers execute **in parallel** (non-blocking, returns when all complete), and non-None return values are replayed in priority order to chain and replace data; `to` specifies owner for directed delivery |
| `lifecycle.fire(event, data=None, *, to=None)` | **Fire and forget (fire-and-forget)**: Handlers execute in background tasks in parallel, no waiting, no return value; zero overhead if no listeners; suitable for high-frequency hot paths and pure observation events; use `emit` for shutdown sequences and order-sensitive consumption (e.g. `config.set`) |
| `lifecycle.emit_sync(event, data=None, *, to=None)` | Synchronously trigger; asynchronous handlers are scheduled with create_task |
| `await lifecycle.submit_event(event_type, *, source, msg, data, to=None, background=False)` | Backward compatibility, automatically builds standard event format; `background=True` uses `fire` for background firing |

**Comparison of the four trigger APIs**:

| Method | Invocation Style | Wait for Handlers to Complete | Typical Scenarios |
|--------|------------------|-------------------------------|-------------------|
| `emit` | `await` (asynchronous) | **Wait**—handlers execute in parallel, return when all complete, return values replayed in priority order | Regular triggering; order-sensitive consumption (`config.set`) and shutdown sequences must use it |
| `fire` | Direct call (synchronous return) | **Do not wait**—handlers execute in background tasks in parallel, no return value; zero overhead if no listeners | High-frequency hot paths and pure observation events (`server.request` / `storage.ready`) |
| `emit_sync` | Direct call (synchronous) | Synchronous handlers complete immediately; asynchronous handlers are scheduled with `create_task` (return values cannot be returned) | Triggering events in non-async contexts (synchronous code) |
| `submit_event` | `await` (asynchronous) | Wait (same as `fire` if `background=True`) | Backward compatibility: automatically builds standard event format (`source` / `msg` / `timestamp`) |

### Utilities

| Method | Description |
|--------|-------------|
| `lifecycle.start_timer(timer_id)` | Start timing |
| `lifecycle.get_duration(timer_id)` | Get elapsed time (in seconds) |
| `lifecycle.stop_timer(timer_id)` | Stop timing and return elapsed time |
| `lifecycle.list_hooks()` | List all registered hooks and the number of handlers |
| `lifecycle.clear()` | Clear all handlers and timers |

## Example Usage in Module

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
        
        # Configuration change audit
        @sdk.lifecycle.on("config.set")
        def audit(data):
            sdk.logger.info(f"Configuration change: {data['key']} = {data['new_value']}")
```

## Background Task Ownership and Automatic Cancellation

> [!NOTE]
> This feature requires ErisPulse **2.8.0+**.

Background asyncio tasks created by a module that are not canceled in `on_unload` will hold a reference to `self`, preventing the module instance from being collected (old instances remain after hot reload). The framework provides the following fallback mechanism:

- **`self.spawn(coro)`** (recommended within module): Task automatically belongs to module name; framework automatically cancels unfinished tasks and logs warnings after `on_unload` when the module is unloaded
- **`spawn_background(coro)`** (from `ErisPulse.runtime`): Automatically captures current `owner_scope` context; `cancel_owner_tasks(owner)` cancels by ownership, `cancel_all_background_tasks()` is provided for `sdk.uninit()` fallback
- **Adapters**: Background tasks under platform name are also automatically canceled when adapter stops

```python
async def on_load(self, event):
    # Recommended: Use self.spawn() for background tasks, framework automatically cancels them after unload
    self.spawn(self._poll())

async def on_unload(self, event):
    # For fine control, still recommend manually canceling and waiting for cleanup
    if self._poll_task:
        self._poll_task.cancel()
        await asyncio.gather(self._poll_task, return_exceptions=True)

async def _poll(self):
    while True:
        await asyncio.sleep(60)
        ...
```

> [!IMPORTANT]
> Framework fallback is **forced cancellation** (`cancel_owner_tasks`), which occurs after `on_unload` returns. Therefore, tasks requiring graceful cleanup (flush buffers, persist state, close connections) **must** manually `cancel()` and `await` completion in `on_unload` — do not rely on fallback to preserve cleanup logic. Framework only guarantees "no lingering tasks holding `self`", not "graceful". For tasks requiring `await` results, directly `await`, do not throw them into background tasks.

## Notes

1. **Handlers can be synchronous or asynchronous**: The system automatically identifies and correctly calls them
2. **Data passing**: In `emit()` mode, non-None values returned by handlers modify the data passed to subsequent handlers
3. **Event naming convention**: Use dot-structure naming for events, making parent listening easier
4. **Error isolation**: Exception in a single handler does not affect execution of other handlers
5. **Synchronous trigger limitation**: In `emit_sync()`, asynchronous handlers are scheduled fire-and-forget, return values cannot be returned
6. **Lifecycle cleanup**: When `sdk.uninit()` is called, all registered handlers and timers are cleared
7. **Loading priority**: If you need to listen to events during the framework initialization phase, it is recommended to set a high priority and disable lazy loading



### 懶加载系统

# Lazy-Loading Module System

> [!TIP]
> **When to read this**: When using lazy-loaded modules or `activate_on` event-driven activation. Skip it if not needed; it does not affect the use of any other features.


The lazy-loading module system of the ErisPulse SDK allows modules to defer initialization until they are **actually accessed** — during startup, only placeholder proxies are registered, and modules that are never used consume no startup time or memory.

## Overview

The lazy-loading module system is one of ErisPulse's core features. It works in the following ways:

- **Deferred initialization**: A module is only actually loaded and initialized the first time it is accessed
- **Transparent usage**: For developers, lazy-loaded modules are almost indistinguishable from regular modules in usage
- **Automatic dependency management**: Module dependencies are automatically initialized when used
- **Lifecycle support**: For modules inheriting from `BaseModule`, lifecycle methods are called automatically

## How It Works

### The LazyModule Class

The core of the lazy-loading system is the `LazyModule` class, a wrapper that only actually initializes the module on first access.

### Initialization Process

When a module is first accessed, `LazyModule` performs the following operations:

1. Retrieves the `__init__` parameter information of the module class
2. Decides whether to pass in the `sdk` reference based on the parameters
3. Sets the module's `moduleInfo` attribute
4. For modules inheriting from `BaseModule`, calls the `on_load` method
5. Triggers the `module.init` lifecycle event

## Event-Driven Lazy Activation (activate_on)

> [!NOTE]
> This feature requires ErisPulse **2.8.0+**.

Modules with `lazy_load=True` are by default only loaded on **first attribute access**. If a module registers command/event handlers,
the traditional approach is to set `lazy_load=False` for immediate loading. `activate_on` provides a third option: **declare triggers,
and the module is automatically activated when the first matching event/command arrives** — it neither stays resident in memory nor loses its trigger entry points.

```python
from ErisPulse.loaders import ModuleLoadStrategy

class MyModule(BaseModule):
    @staticmethod
    def get_load_strategy():
        return ModuleLoadStrategy(
            lazy_load=True,
            activate_on=[
                # ---- Event triggers (passively arriving; no user awareness required) ----
                "message",                                    # Type-level: any message event
                {"notice": "group_member_increase"},          # Type + a single detail_type
                {"message": ["private", "group"]},            # Type + multiple detail_types

                # ---- Command triggers (active input; placeholder commands visible to Help) ----
                {"command": "roll"},                          # Shorthand: command name
                {"command": ["roll", "dice"]},                # List of command names
                {"command": {                                 # dict declaration (name is required)
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

### Command dict Declaration Parameters

The dict form mirrors the user-level parameters of the `@command()` decorator, used to register placeholder commands before the module is loaded:

| Parameter | Type | Default | Description |
|------|------|------|------|
| `name` | `str` | **Required** | Command name; must match `@command(name)` in `on_load`, otherwise after activation the placeholder is unregistered and the command no longer exists |
| `help` | `str` | Fallback chain | Description shown in Help; if not declared, values are taken via the fallback chain (see below) |
| `usage` | `str` | Auto-generated | Usage line, default `{prefix}{name}` |
| `group` | `str` | `None` | Command group |
| `aliases` | `list[str]` | `[]` | Aliases registered at the same time; **typing an alias also triggers activation** |
| `hidden` | `bool` | `False` | When `True`, the placeholder command is likewise hidden (aligned with the hidden semantics of the real command after activation); users who know the command name can still trigger it by typing it |

`priority` / `permission` / `master` are **not supported**: the placeholder command's sole mission is to trigger activation;
permission checks are performed by the real command after activation (intercepting permissions at the placeholder stage would instead break "activation by typing the command").

### Placeholder Command help Fallback Chain

The command description shown by Help before the module is loaded is taken in the following order (stopping at the first hit):

1. Command-level `help` in the dict declaration (most precise)
2. `description` from the module's `get_meta()`
3. The module's `__description__` attribute
4. The package metadata's `Summary` (PyPI package brief)
5. Generic hint: "This command comes from lazy-loaded module X; first use will automatically load that module"

### Trigger Semantics

- **Event stubs**: Registered with the corresponding event manager at an extremely low priority (`ACTIVATION_STUB_PRIORITY`),
  firing as a fallback after all regular handlers; after activation, the current event is forwarded to the module's real handlers
- **Command stubs**: Placeholder commands are registered; after activation, the placeholder is unregistered and the real command takes over the current trigger
- **Re-entrancy prevention**: `asyncio.Lock` guarantees that the module is activated only once under concurrent triggers
- **Scope filtering**: Stubs carry the module's owner identity and do not trigger when the module is not enabled for that Bot / session / platform
- **Failure semantics**: Failed activation enters a cooldown period (`ACTIVATE_RETRY_COOLDOWN_SECS`, 30 seconds);
  events are short-circuited during the cooldown to avoid repeated attempts; after the cooldown ends, the next trigger retries automatically, with the stub retained throughout
- **Deduplication**: When commands with the same name are declared as a mix of shorthand + dict, they are deduplicated (dict takes precedence); a dict missing `name`,
  or an event `detail_type` mistakenly written as a dict, produces a warning and is ignored

> For the architecture diagram and complete semantics, see [Architecture Overview](../architecture.md#event-driven-lazy-activation-activate_on-trigger-architecture).

## Lazy-Load Dormancy (dormant_after)

> [!NOTE]
> This feature requires ErisPulse **2.11.0+**.

After a lazily-activated module has been idle for a long time, the framework can put it into **dormancy**: runtime resources are released (owned tasks / connections / event registrations),
while the lazy-load proxy and registration stubs are kept — the module returns to the "registered but not loaded" state, and the next attribute access /
`module.call` / `activate_on` event **transparently wakes it up** (re-instantiating it and running `on_load`),
with no wake-up API needed. The system state after dormancy is exactly the same as "never activated".

### Declaration

```python
@staticmethod
def get_load_strategy():
    return ModuleLoadStrategy(
        lazy_load=True,
        dormant_after="30m",   # Auto-dormant after 30 minutes idle; not declared = never dormant (default)
    )
```

The duration syntax is exactly the same as the `cooldown` of command governance (`90s` / `1h30m` / `1d`). The sweeper scans at fixed intervals
(60 seconds), so the actual dormancy time = threshold + at most one scan interval; you can also put a module to sleep manually at any time:
`await sdk.module.sleep("module_name")`. Explicit `unload` still performs a full unload (the lazy proxy is removed as well).

### State Continuation

Before dormancy, the framework triggers `on_before_unload(reason="dormant")` (the first step of the unload pipeline, with resources still intact);
the module saves its state to `sdk.storage` and restores it in `on_load` after wake-up:

```python
async def on_before_unload(self, event):
    if event["reason"] in ("dormant", "reload", "disable"):
        await self.sdk.storage.aset(f"{self._module_name}:counter", self._count)

async def on_load(self, event):
    self._count = await self.sdk.storage.aget(f"{self._module_name}:counter") or 0
```

### Semantics and Boundaries

- **Dependency safety**: Dependents of a lazy module access it via the persistent proxy (`sdk.<Name>`) or `module.call`,
  and behavior is consistent before and after dormancy; directly holding references to real instances is an anti-pattern (visible to the leak auditor)
- **Events not delivered**: A dormant module no longer receives events — modules that need event-based wake-up should also declare `activate_on`
  (the event wakes the module first, then is forwarded); when troubleshooting "commands not responding", check whether the module is in a dormant state
- **Wake-up failures are self-healing**: A failed wake-up (re-initialization) enters a 30-second cooldown; after the cooldown, the next access retries automatically,
  without permanent failure

## Configuring Lazy Loading

### Global Configuration

Enable/disable global lazy loading in the configuration file:

```toml
[ErisPulse.framework]
enable_lazy_loading = true  # true = enable lazy loading (default), false = disable lazy loading
```

### Module-Level Control

Modules can control the loading strategy by implementing the `get_load_strategy()` static method:

```python
from ErisPulse.Core.Bases import BaseModule
from ErisPulse.loaders import ModuleLoadStrategy

class MyModule(BaseModule):
    @staticmethod
    def get_load_strategy():
        """Returns the module loading strategy"""
        return ModuleLoadStrategy(
            lazy_load=False,  # Returning False means immediate loading
            priority=100      # Loading priority; higher values mean higher priority
        )
```

## Using Lazy-Loaded Modules

### Basic Usage

For developers, lazy-loaded modules are almost indistinguishable from regular modules in usage:

```python
# Access a lazy-loaded module via the SDK
from ErisPulse import sdk

# The following access triggers the module's lazy loading
result = await sdk.my_module.my_method()
```

### Unified Module Access Entry Point

Whether accessed via SDK attributes, module manager attributes, or queried via `module.get()`,
for lazy-loaded modules that are "registered but not yet loaded", the same lazy-loading proxy is returned; accessing its attributes is what actually triggers initialization:

```python
# All three approaches return the lazy-loading proxy (when the module is not loaded), with consistent, transparent behavior
sdk.my_module          # Entry point that triggers loading
sdk.module.my_module   # Also returns the lazy-loading proxy
sdk.module.get("my_module")  # Also returns the lazy-loading proxy; it does not itself trigger loading

# Only accessing any attribute of the proxy actually initializes the module
result = await sdk.my_module.my_method()
```

`module.get()` is a **query** interface and does not itself trigger loading:
- Module loaded → returns the real instance
- Module registered but not loaded → returns the lazy-loading proxy (initialization occurs on attribute access)
- Module not registered → returns `None`

To explicitly trigger loading, use `await sdk.load_module("my_module")`.

### Asynchronous Initialization

For modules that require asynchronous initialization, explicit loading is recommended first:

```python
# Explicitly load the module first
await sdk.load_module("my_module")

# Then use the module
result = await sdk.my_module.my_method()
```

### Synchronous Initialization

For modules that do not require asynchronous initialization, direct access works:

```python
# Direct access automatically initializes synchronously
result = sdk.my_module.some_sync_method()
```

## Best Practices

When choosing a loading strategy, refer to the following decision flow:

```mermaid
flowchart TD
    A["Module declaration<br/>get_load_strategy()"] --> B{"Must be ready at startup<br/>or high-frequency triggers?"}
    B -->|"Yes"| C["lazy_load=False<br/>immediate loading"]
    B -->|"No"| D{"Registers command / event handlers?"}
    D -->|"Yes"| E["lazy_load=True + activate_on<br/>activates when an event/command arrives"]
    D -->|"No"| F["lazy_load=True<br/>loads on first attribute access"]
    C --> G["Calls on_load() at startup"]
    E --> H["Registers stub → instantiates on trigger"]
    F --> I["LazyModule proxy"]
```

### Scenarios Where Lazy Loading Is Recommended (lazy_load=True)

- Passively invoked utility modules (e.g., data query modules, format converters, etc. — only needed when called by other modules)
- Modules that register command/event handlers but are not used frequently — declare triggers with `activate_on`; the module is automatically activated when the first matching event/command arrives, without giving up lazy loading

### Scenarios Where Disabling Lazy Loading Is Recommended (lazy_load=False)

- Modules that need to be ready immediately at startup (e.g., core modules that provide foundational services for other modules)
- Frequently triggered listeners (need to process every message) — `activate_on` forwarding incurs a one-time activation overhead; immediate loading is more direct in high-frequency scenarios
- Scheduled task modules
- Modules that must be initialized at application startup

> The `priority` parameter controls the initialization order among immediately-loaded modules; higher values are initialized first. Modules with the same priority are loaded in registration order.

## Notes

1. If your module uses lazy loading and no other module ever calls it within ErisPulse, your module will never be initialized.
2. If your module contains components such as Event listeners or other actively listening components, you have two options: declare `activate_on` triggers (keeping lazy loading, automatically activating when events arrive), or declare that it needs to be loaded immediately (`lazy_load=False`); otherwise your module's normal operation will be affected.
3. We do not recommend disabling lazy loading unless you have special needs; otherwise it may cause problems such as dependency management and lifecycle event issues.
4. In the `activate_on` command dict declaration, `name` must match the real command name registered by `@command()` in the module's `on_load` — otherwise, after the module is activated, the placeholder command is unregistered and a command whose declaration does not match its implementation will not exist.



### 国际化（i18n）系统

# Internationalization (i18n) System

> [!TIP]
> **When to read this**: When you need multi-language content, translation registration, or language detection. Skip if not needed, as it does not affect the use of other features.

ErisPulse v2.5.0 includes full internationalization support. The framework core and CLI interface can automatically switch display text based on your system language, and external modules can register their own translations.

## Supported Languages

| Language | Code | Description |
|----------|------|-------------|
| Simplified Chinese | `zh-CN` | Default language (native framework language) |
| Traditional Chinese | `zh-TW` | Traditional Chinese (Hong Kong / Macau / Taiwan) |
| English | `en` | English (fallback language) |
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

Add the following to `config/config.toml`:

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

The framework detects user language in the following priority order:

1. **Environment Variable `ERISPULSE_LANG`** — Highest priority, used for testing and temporary switching
2. **Windows API** — `GetUserDefaultLocaleName` (Windows only, unaffected by tools like Git Bash that override `LANG`)
3. **Environment Variables** — `LANGUAGE` > `LC_ALL` > `LC_MESSAGES` > `LANG` (Unix/macOS standard)
4. **System Locale** — `locale.getlocale()` / `locale.getdefaultlocale()`
5. **Fallback** — en (English)

### Nearest Mapping Principle

When the detected language is not an exact match, it is mapped to the closest supported language:

- `zh-TW`, `zh-HK`, `zh-MO`, `zh-Hant` → **Traditional Chinese**
- All other `zh-*` (e.g., `zh-CN`, `zh-SG`) → **Simplified Chinese**
- `en-US`, `en-GB`, `en-AU`, etc. → **English**
- `ja-JP` → **Japanese**
- `ru-RU` → **Russian**
- Other unrecognized languages → **Simplified Chinese (fallback)**

---

## Using i18n in Modules

You can register translation text for your own modules, allowing your modules to support multiple languages.

### Recommended Approach: Declare Translation Keys via I18nClass (v2.7.0+)

Starting from v2.7.0, modules/adapters can declare translation keys by embedding a nested class `I18nClass`, similar to declaring `ConfigClass`. The framework will automatically register all declared translation keys during loading, eliminating the need to manually call `i18n.register()`.

```python
from dataclasses import dataclass, field

from ErisPulse.Core.Bases import BaseConfig, BaseI18n, BaseModule, I18nKey


class MyModule(BaseModule):
    # Configuration class (optional)
    @dataclass
    class ConfigClass(BaseConfig):
        welcome_msg: str = field(
            default="欢迎",
            metadata={
                # This references the i18n key mymodule.welcome_msg
                "description": {"i18n": "mymodule.welcome_msg", "default": "Welcome message"},
            },
        )

    # Translation key collection class (optional)
    # Declared keys will be automatically registered by the framework, taking precedence over ConfigClass-generated defaults
    class I18nClass(BaseI18n):
        # Property names are automatically concatenated to form the full key path: <module name>.<property name>
        welcome_msg: I18nKey = I18nKey(
            default="Welcome Message",   # Language-agnostic fallback, not registered to any language
            zh_CN="欢迎消息",
            en="Welcome Message",
            ja="ウェルカムメッセージ",
            ru="Приветственное сообщение",
            zh_TW="歡迎訊息",
        )
        # Other translation keys used in business logic
        hello: I18nKey = I18nKey(
            default="Hello, {name}!",
            zh_CN="你好，{name}！",
            zh_TW="你好，{name}！",
            en="Hello, {name}!",
            ja="こんにちは、{name}！",
            ru="Привет, {name}!",
        )

        # You can also explicitly specify the full key path (not using property name concatenation)
        custom: I18nKey = I18nKey(
            key="mymodule.deep.nested.key",
            default="Default text",
            zh_CN="默认文本",
            zh_TW="預設文本",
            en="Default text",
            ja="デフォルトテキスト",
            ru="Текст по умолчанию",
        )
```

#### Why is I18nClass Recommended?

| Scenario | Manual i18n.register() | I18nClass Declarative |
|----------|------------------------|-----------------------|
| i18n keys referenced in configuration descriptions | Must be manually registered, and must be done before configuration generation | Framework automatically registers before configuration generation |
| Multi-language translation declarations | Scattered across various on_load() methods |集中 in a class, clearly visible |
| Key naming consistency | Prone to typos | Property names as key suffixes, IDE can auto-complete |
| Cleanup on unload | Must manually unregister_domain() | Framework uses unified domain registration |

#### I18nClass Key Path Rules

- **Default**: Use ``<module registration name>.<property name>`` as the full key path
  - Example: Module name is ``MyModule``, property ``welcome`` → key path ``MyModule.welcome``
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
        # Central declaration of configuration description references and other business keys' multi-language translations
        endpoint: I18nKey = I18nKey(
            default="API Endpoint",
            zh_CN="API 地址",
            zh_TW="API 位址",
            en="API Endpoint",
            ja="APIアドレス",
            ru="API адрес",
        )
```

The `I18nClass` of an adapter is automatically registered during the `__init__` phase (before configuration template generation), ensuring that i18n keys referenced in configuration descriptions are available.

### Manual Registration of Custom Translations (Old Approach)

If you do not use `I18nClass`, you can directly call `i18n.register()` to register translation text.

```python
from ErisPulse import i18n

# Register Chinese translation
i18n.register("zh-CN", {
    "my_module.welcome": "欢迎使用我的模块！",
    "my_module.goodbye": "再见！",
    "my_module.hello": "你好，{name}！",
}, domain="my_module")

# Register English translation
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

# Specify default value (returned if translation key does not exist)
i18n.t("my_module.unknown_key", default="Default text")
```

### Using in Module Class

```python
from dataclasses import dataclass, field
from ErisPulse import i18n
from ErisPulse.Core.Bases import BaseConfig, BaseModule

@dataclass
class MyModuleConfig(BaseConfig):
    welcome_msg: str = field(
        default="欢迎",
        metadata={
            "description": {"i18n": "my_module.welcome_msg", "default": "Welcome message"},
            "ui": {"widget": "text", "group": "basic", "order": 1},
        },
    )

class MyModule(BaseModule):
    ConfigClass = MyModuleConfig

    async def on_load(self, event):
        # Dynamically read configuration (reflects latest value on each access)
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

Starting from v2.5.2, configuration Schema fully supports i18n. All user-visible text fields can reference i18n keys, and WebUI and other consumers will automatically resolve them to corresponding text based on the current language.

### Supported i18n Fields

| Field | Location | Description |
|-------|----------|-------------|
| `description` | field metadata | Field description |
| `options[].label` | `ui.options` | Select control option labels |
| `placeholder` | `ui.placeholder` | Input field placeholder |
| `group_labels` | `_schema_meta` | Group display name (Dashboard section title) |

All use the `{"i18n": "key", "default": "text"}` format. Pure strings are passed through as-is (for backward compatibility).

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
                "placeholder": {"i18n": "my_adapter.token.ph", "default": "Enter Token"},
            },
        },
    )
    # i18n for options label
    mode: str = field(
        default="a",
        metadata={
            "description": {"i18n": "my_adapter.mode", "default": "Operation mode"},
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

    # i18n for group_labels (group display name)
    _schema_meta = {
        "group_labels": {
            "basic": {"i18n": "my_adapter.group.basic", "default": "Basic Settings"},
        }
    }
```

`default` is the fallback text — displayed when translation is not registered or lookup fails.

### Secret Masking and Configuration Validation

Fields marked as `"secret": True` will automatically receive **masking protection** (from v2.7.0 onwards):

- **Template generation masking**: When `dataclass_to_toml_with_comments()` generates configuration templates, secret field values are not written to the file (empty placeholders are used), preventing sensitive information from being written to disk
- **General masking utility**: `redact_secret(value)` replaces non-empty values with `***`, returns empty values as-is, and can be used in scenarios such as logging output

```python
from ErisPulse.Core.Bases.config_schema import redact_secret

redact_secret("sk-xxxxxx")  # '***'
redact_secret("")           # ''
```

**Configuration validation** (`validate_config()`) includes non-empty checks for `required` fields, and from v2.7.0 onwards supports:

| Validation | Metadata | Example |
|------------|----------|---------|
| Type match | Field declaration type | `int` field with string input raises an error |
| Enum constraint | `ui.options` or top-level `options` | Value must be one of the allowed options |
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

Configuration field i18n keys are registered the same way as regular translation keys using `i18n.register()`:

```python
from ErisPulse import i18n

# Register Chinese (same as default, can be different)
i18n.register("zh-CN", {
    "my_adapter.token": "平台 Token",
}, domain="my_adapter")

# Register English
i18n.register("en", {
    "my_adapter.token": "Platform Token",
}, domain="my_adapter")
```
> **Recommended approach**: Use `I18nClass` to declare translation keys, as the framework will automatically register them (see the "Recommended Approach" section above),
> eliminating the need to manually call `i18n.register()` or `register_config_i18n()`.

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

The schema returned by `get_config_schema()` passes through the i18n dictionary as-is. The WebUI frontend can resolve it using `i18n.t()` based on the current language.

If the server needs to directly resolve to a string (e.g., for a frontend that does not support i18n), use `resolve_config_schema()`, which resolves `description`, `options[].label`, `placeholder`, and `group_labels` to the current language's text:

```python
from ErisPulse.Core.Bases.config_schema import resolve_config_schema

# All i18n fields are resolved to the current language's string
schema = resolve_config_schema(MyAdapterConfig)
print(schema["fields"]["token"]["description"])    # "平台 Token" or "Platform Token"
print(schema["fields"]["token"]["placeholder"])   # "请输入 Token" or "Enter Token"
print(schema["fields"]["mode"]["options"][0]["label"])  # "模式A" or "Mode A"
print(schema["group_labels"]["basic"])             # "基本设置" or "Basic"
```

> `BaseConfig`, `BotAccountConfig`, `register_config_i18n()`, `resolve_config_schema()`
> and other types and utility functions are actually defined in `ErisPulse.Core.Bases.config_schema`.
> `ErisPulse.runtime.config_schema` is retained as a compatibility shim,
> **recommended to import uniformly from `ErisPulse.Core.Bases`** (except i18n translation key-related types,
> which are located in `ErisPulse.Core.Bases.i18n_schema`).

## API Reference

### I18nManager

#### Core Methods

| Method | Description |
|--------|-------------|
| `t(key, default=None, **kwargs)` | Get translated text (`gettext()` is an alias) |
| `set_language(lang)` | Manually set language |
| `get_language()` | Get current language |
| `reset_language()` | Reset to automatic detection (and re-detect environment) |
| `get_supported_languages()` | Get list of all supported languages |
| `has_translation(key, lang=None)` | Check if translation key exists |
| `register(lang, translations, domain)` | Register custom translation |
| `unregister_domain(domain)` | Unload all translations in specified domain |
| `reload()` | Reload built-in translations and re-detect language |

#### `t()` Method Details

```python
def t(self, key, /, default=None, **kwargs):
```

- `key` — Translation key (positional argument only, does not conflict with `key=` in `**kwargs`)
- `default` — Default value returned if translation does not exist, defaults to `None` (returns key name itself)
- `**kwargs` — Formatting arguments to fill placeholders in translation values

Example:

```python
# Translation definition: "greeting": "你好，{name}！欢迎来到{place}。"
i18n.t("greeting", name="Alice", place="ErisPulse")
# Returns: "你好，Alice！欢迎来到ErisPulse。"
```

### BaseI18n / I18nKey (Declarative Translation Keys)

Starting from v2.7.0, `ErisPulse.Core.Bases` provides a class attribute-based translation key declaration tool (recommended to import uniformly from `ErisPulse.Core.Bases`):

> ``I18nKey.default`` is a **language-agnostic fallback text**, not registered to any language.
> To make translations effective, at least one language parameter must be explicitly provided (``zh_CN=`` / ``en=`` / ``ja=`` etc.).
> This allows developers from different countries to freely use their native language to fill in ``default``, and the framework does not make any assumptions.

| Name | Description |
|------|-------------|
| `I18nKey(default, *, key=None, zh_CN, zh_TW, en, ja, ru)` | Single translation key declaration, `default` is language-agnostic fallback |
| `BaseI18n` | Translation key collection base class (naming aligned with `BaseConfig`), sub-classes declare multiple `I18nKey` as class attributes |
| `BaseI18n.register(prefix="", domain="app")` | Class method: register all declared keys to the i18n system |
| `key` | Alias for `I18nKey` (more concise writing) |

Example usage:

```python
from ErisPulse.Core.Bases import BaseI18n, key

class MyKeys(BaseI18n):
    # Concise alias writing
    hello = key(
        default="Hello",
        zh_CN="你好",
        zh_TW="你好",
        en="Hello",
        ja="こんにちは",
        ru="Привет",
    )
    bye = key(
        default="Bye",
        zh_CN="再见",
        zh_TW="再見",
        en="Bye",
        ja="さようなら",
        ru="До свидания",
    )

# Standalone usage (manual registration)
MyKeys.register(prefix="myapp.", domain="myapp")
```

### Accessing via SDK Instance

```python
from ErisPulse import sdk

# sdk.i18n and directly imported i18n are the same object
sdk.i18n.set_language("en")
print(sdk.i18n.t("core.sdk.init.starting"))
```

---

## Runtime Configuration

### Reading i18n Configuration via Configuration API

```python
from ErisPulse.Core.Bases import I18nConfig
from ErisPulse.runtime import get_i18n_config

config = get_i18n_config()
print(config["language"])  # "auto" or specific language code

# I18nConfig is a dataclass, can be used to generate configuration templates
schema = I18nConfig.__dataclass_fields__
```

### Configuration Item Explanation

In the `[ErisPulse.i18n]` section of `config/config.toml`:

```toml
[ErisPulse.i18n]
# Display language, possible values:
# - "auto"      — Automatically detect system language (default)
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

It is recommended to use a dot-separated namespace format:

```
<module name>.<category>.<description>
```

For example: `my_module.command.hello_desc`, `core.adapter.start_failed`

### Multi-language Coverage

You do not need to provide translations for all languages at once. Missing languages will automatically fall back to English, and if English is also missing, the key name itself will be displayed.

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

The CLI has an **independent** internationalization module (`ErisPulse.CLI.i18n`), which is completely decoupled from the framework core's internationalization module.

- **Core i18n** — Used by framework core modules, external modules can register translations
- **CLI i18n** — Used internally by the command-line interface, does not share translation data with Core

This design ensures that changes to CLI translations do not affect the stability of the framework core.



### 统一控制面（scope）

# Scope

> [!TIP]
> **When to read this**: When you need to control module availability, event admission, or outbound action restrictions. Skip if not needed, it does not affect the use of other features.

> **After reading you will know**: The configuration paths, priority and rejection behaviors for the three scope dimensions (module availability / event admission / outbound actions), the usage of runtime API, and how interception is observable (via the `scope.blocked` event).
>
> **This section does not cover**: Resource ownership and unloading (see [Ownership (owner) system](ownership.md)); command ACL and event overrides (see [Event Handling Introduction](../getting-started/event-handling.md)).

> [!NOTE]
> This feature requires ErisPulse **2.8.0+**.

Scope answers four questions: **Which modules are available, which events are received, what text a module processes, and what actions a module can perform outwardly**. Control is entirely user-driven: at the top level during module / adapter / processor / outbound call registration (via `ErisPulse.scope` or runtime `sdk.scope`), the event pipeline automatically reads and executes the configuration at entry, processor filtering, and outbound gate.

| Dimension | Controls what | Rejection behavior | Configuration path |
|------|---------|---------|---------|
| **① Module** | Which modules are available (platform / Bot / session three levels) | Filtered modules do not trigger or reply (broadcast `scope.blocked` event; matched commands are still claimed and blocked) | `scope.platforms / bots / sessions` |
| **② Identity** | Whether to receive events (adapter / Bot / session / user four levels) | Completely discard at entry (broadcast `scope.blocked` event) | `scope.identity.*` |
| **③ Outbound** | What outbound calls a module can initiate (messages / API / requests, method-level white/blacklists) | Fail response (`retcode=34601`) | `scope.actions` |

> **Related systems**: Commands are special message event handlers, their user white/blacklists (ACL) and implementation parameter overrides are managed by the command system (`ErisPulse.event.command`), see [Event Handling Introduction](../getting-started/event-handling.md) and [Configuration Guide](../user-guide/configuration.md).

{!--< tips >!--}
1. Import the singleton via `from ErisPulse.Core import scope` (`sdk.scope` is the same object)
2. Check: `scope.is_allowed(...)` / `scope.is_identity_allowed(...)` /
   `scope.is_action_allowed(...)` correspond to the three gates ①②③
3. Read/write: Dimensional parameter methods (IDE can auto-complete) —
   `scope.set_module(...)` / `scope.set_identity(...)` / `scope.set_action(...)`;
   There are also dictionary-style fallback methods `scope.get(path)` / `scope.set(path, v)` / `scope.delete(path)`
4. Event handler text condition overrides are covered in
   [Event Handling Introduction · Event Override](../getting-started/event-handling.md#event-override-overwrite-any-event-type-behavior-without-modifying-module-code);
   Command ACL / parameter overrides are covered in [Event Handling Introduction](../getting-started/event-handling.md)
{!--< /tips >!--}

## Matching Entry Syntax (Unified Across the System)

All "name lists" in scope (module names, identity keys, outbound entries) use the same matching syntax (`ErisPulse.Core.text_match`):

| Syntax | Example | Description |
|------|------|------|
| Exact name | `"Chat"` | Full value comparison, **case-insensitive** |
| Glob | `"Tool*"`、`"spam_*"` | `*` for any string / `?` for single character / `[seq]` for character set, case-insensitive |
| Regular Expression | `"re:^Danger.*"` | Declared with `re:` prefix, regular expression `search` match, default case-insensitive |

- Invalid regular expressions **silently degrade** to "no match" (no error, no crash)
- Decorator parameters (`pattern=` / `regex=`) have fixed semantics: `pattern` is glob, `regex` is the regular expression source (without `re:` prefix); regular expression entries in scope configuration **must** have the `re:` prefix

## Global Fallback: `default_allow`

`default_allow` is the **single global fallback switch** (default `true`),
affecting two decision dimensions:

- **Module dimension**: If no binding is matched → `default_allow` decides allow / deny
- **Identity dimension**: If no strategy is matched → `default_allow` decides allow / deny

Setting it to `false` enables "implicit deny" strict mode: whitelist-style management,
**all unexplicitly allowed are denied**.

> **Exception**: The ③ outbound dimension is **not** affected by `default_allow` — it is an independent tightening switch,
> defaulting to full allow, only explicit rules restrict (framework-layer owner-empty calls are always allowed).
> This strict global mode won't accidentally cut off all module message replies.
> Command ACL has its own `ErisPulse.event.command.default_allow` fallback, independent of this.

## Configuration File

```toml
[ErisPulse.scope]
default_allow = true        # Global fallback (false = implicit deny strict mode)
cache_size = 1024           # LRU cache size

# ── ① Module Dimension (Priority: session > Bot > platform) ──
[ErisPulse.scope.platforms.onebot11]
modules = ["Chat", "Tool*"]   # Whitelist: exact name / glob / re: regex
blocked = ["re:^Danger"]
[ErisPulse.scope.bots.onebot11."123456"]
modules = ["Chat"]
merge = true                  # Append on top of platform-level binding (default is full override)
[ErisPulse.scope.sessions.onebot11."789012345"]
modules = ["Chat"]

# ── ② Identity Dimension (Priority: user > session > Bot > adapter) ──
[ErisPulse.scope.identity.adapters.onebot11]
deny = true                   # Discard all events from this adapter
[ErisPulse.scope.identity.bots.onebot11."123456"]
deny = true
[ErisPulse.scope.identity.sessions.onebot11."g_blocked"]
deny = true
[ErisPulse.scope.identity.users.onebot11]
allow = ["u_admin"]           # User keys support glob / re: regex
deny = ["u_bad", "spam_*"]

# ── ③ Outbound Dimension (Default: full allow, only explicit rules restrict) ──
[ErisPulse.scope.actions.MyModule]
send = { deny = true }                                    # Disable all sending
api = { allow = ["get_*"] }                               # Only allow standard query APIs
request = { deny = true }                                 # Disable request handling
```

## ① Module Dimension

**In one sentence**: Control "which modules are available in this context" via platform / Bot / session three-level binding; filtered modules do not trigger or reply (matched commands are still claimed and blocked).

Answer "which modules are available in a certain context". Default is fully open; filtering starts only after configuration binding,
**modules and adapters require no changes**.

```mermaid
flowchart TD
    A["Event arrives at a module's handler/command"] --> B{"scope.is_allowed<br/>(platform, bot, module, session)"}
    B --> C{"Parse chain: session-level > Bot-level > platform-level<br/>(if sub-level merge = true, merge entries individually)"}
    C -->|"Matched"| D["Blocked matched → Deny<br/>modules non-empty → Only whitelist allowed<br/>Both empty → default_allow"]
    C -->|"Not matched"| E["default_allow (default true = allow)"]
    D -->|"Deny"| Z["No reply<br/>(broadcast `scope.blocked` lifecycle event; matched commands are still claimed and blocked)"]
```

- **Parse priority**: session-level > Bot-level > platform-level, higher priority bindings **fully override** lower priority; if sub-level binding sets `merge = true`, it changes to **entry-by-entry union** with lower priority (each of modules / blocked is merged individually, `merge` itself is a control key, not an entry)
- **Default semantics**: Filtered modules' commands and handlers do not trigger or reply, visible in TRACE-level logs (core.scope.denied); interception also broadcasts the `scope.blocked` lifecycle event (subscribe to observe who was blocked and why); matched **commands** are still claimed and blocked — command text is no longer passed to lower-level message handlers, eliminating the ambiguity of "command rejected then message handler responds again"
- **Framework-level handlers** (scope_exempt=True or owner is empty) are unaffected; module names that are empty (framework-layer resources) are always allowed
- **Session-aware help and command queries**: Command query APIs (command.help /
  get_command / get_commands / get_group_commands / get_visible_commands,
  and module.get_commands_overview) all support optional event= or explicit
  platform= / bot_id= / session_id= keywords — commands from modules unavailable in the current session
  no longer appear in the results (get_command returns None, single-command help is treated as "unregistered",
  consistent with default semantics); if no context is provided, behavior remains full

### Binding Inheritance (merge)

The default semantics of full override are clear and predictable; when you need to **append** to the upper level, write `merge = true` in the sub-level:

```toml
[ErisPulse.scope.platforms.onebot11]
modules = ["Chat", "Tool"]      # Platform-level: allow Chat, Tool

[ErisPulse.scope.bots.onebot11."123456"]
modules = ["Music"]
merge = true                    # The actual effective modules for this Bot = ["Chat", "Tool", "Music"]
```

- **Merge rules**: `modules` and `blocked` each take the **union**; `blocked` inside the binding still takes precedence over `modules`
- **Chain merge**: Platform → Bot → Session, each level independently decides `merge` or override

## ② Identity Dimension (Event Admission)

**In one sentence**: Use user / session / Bot / adapter four-level strategies to completely discard "events that should not be received" at the distribution entry, with deny taking precedence over allow.

Answer "whose events are received or not". Events that are rejected are **completely discarded at the distribution entry** —
they do not enter middleware or any handler (including framework-level), visible only in TRACE-level logs (core.scope.identity_denied).

- **Parse priority**: user > session > Bot > adapter, take the most specific configured strategy; deny takes precedence over allow
- Each level binding is a binary strategy: `{ allow = true }` or `{ deny = true }`
- User keys support glob / regex (e.g. `"spam_*"` to block a batch of spam users)
- Typical use case — upper-level deny, individual allow for "exceptional allow":

```toml
[ErisPulse.scope.identity.adapters.onebot11]
deny = true
[ErisPulse.scope.identity.users.onebot11]
allow = ["u_admin"]   # Even if adapter-level denied, u_admin's events are still allowed
```

## ③ Outbound Dimension (Restricting Module Outbound Calls)

**In one sentence**: Restrict module-initiated outbound calls (messages / API / requests) with method-level white/blacklists, and rejected calls do not initiate any network request, directly returning `retcode=34601`.

Restrict module-initiated **outbound actions**: message sending / standard API actions / request operations.
The three actions correspond to the underlying DSL: `Event.reply` and `Send` (send), `Api` / `call_api` (api), and `Request`'s accept/reject (request). Outbound calls initiated by the module during event handler execution carry the module owner, which is uniformly judged by this dimension.

### Rule Form (Inline Table)

Each action's rule is an inline table: `{ allow = [...], deny = true|[...] }`.
Only one rule per action is allowed (TOML keys are not repeatable, choose between full deny or fine-grained):

```toml
[ErisPulse.scope.actions.MyModule]
send = { deny = true }                                  # Disable all message sending (Event.reply / Send DSL)
# Or fine-grained method-level: send = { allow = ["Text", "Image*"], deny = ["File"] }
api = { allow = ["get_*"] }                             # Only allow query-type standard APIs
# Or action-level blacklist: api = { deny = ["set_*", "leave_*"] }
request = { deny = true }                               # Disable request handling accept/reject
```

- `send` entries match **send method names** (`Text` / `Image` / `File` ...),
  `api` entries match **standard action names** (`get_group_info` / `set_group_name` ...)
- Entries support exact names / glob / `re:` regex (consistent with the unified system syntax, case-insensitive)
- Writing `allow` as a single string is equivalent to a single-entry list: `send = { allow = "Text" }`

### Decision Semantics

**Default: fully allow** — Unconfigured, or owner is empty (internal framework calls) are allowed.
After configuration, the following order is used for judgment:

1. `deny = true` → Reject
2. `deny` list matches the call name → Reject
3. `allow` list is non-empty and the call name is not matched (or the call has no name) → Reject
4. Otherwise, allow

Rejected calls do not initiate any network request, directly returning the standard failure response
(`retcode = 34601`, see [api-response §5.3](../standards/api-response.md#53-framework-extended-return-code-34xxx-customized-low-three-digits-in-the-platform-error-segment)).

The three actions are independent, and only one can be limited.

```python
# Runtime API
sdk.scope.set_action("MyModule", "send", deny=True)              # Disable all message sending
sdk.scope.set_action("MyModule", "send", allow=["Text"])         # Allow only text messages
sdk.scope.is_action_allowed("MyModule", "send", name="Image")    # False
sdk.scope.is_action_allowed("MyModule", "api", name="get_user_info")  # Judged by rules
sdk.scope.delete_action("MyModule", "send")                      # Restore allow
sdk.scope.get_action("MyModule", "send")                         # Current rule for this action
```

## Runtime API

The scope runtime API is layered into three parts: **decision** (three questions), **dimensional read/write** (each dimension has `set` / `get` / `delete` parameterized methods, fully typed signatures, IDE auto-complete), and **dictionary-style fallback** (dot-separated paths directly access any section).

```python
from ErisPulse import sdk

scope = sdk.scope
```

### Decision (Three Questions)

```python
scope.is_allowed("onebot11", "123456", "Chat")                 # ① Module dimension
scope.is_allowed("onebot11", "123456", "Chat", "789012345")    # With session level
scope.is_allowed("onebot11", "123456", None)                   # Framework-layer resource -> True

scope.is_identity_allowed("onebot11", "123456", "group_9", "u1")   # ② Identity dimension

scope.is_action_allowed("MyModule", "send")                    # ④ Outbound dimension
scope.is_action_allowed("MyModule", "send", name="Image")      # Fine-grained method-level
```

### ① Module Dimension

```python
# Binding (level determined by parameters: session_id > bot_id > platform-level)
scope.set_module("onebot11", bot_id="123456", modules=["Chat", "Tool*"])
scope.set_module("onebot11", blocked=["re:^Danger"])                       # Platform-level
scope.set_module("onebot11", bot_id="123456", session_id="g9", modules=["Chat"])  # Session-level
scope.set_module("onebot11", bot_id="123456", modules=["Music"], merge=True)      # Union with existing entries
scope.set_module("onebot11", bot_id="123456", modules=["Chat"], persist=False)    # Runtime only

# Read / Delete
scope.get_module("onebot11", bot_id="123456")   # {"modules": ["Chat"], "blocked": []}
scope.delete_module("onebot11", bot_id="123456")
```

> `merge=True` is **write-time union** (merge entries with existing bindings at this level); the `merge = true` configuration key at parse time across levels is covered in the above [Binding Inheritance](#binding inheritance merge) — these are independent mechanisms.

> **Runtime Binding (persist=False) Semantics**: Runtime bindings are saved in a separate overlay layer,
> **any subsequent configuration writes / hot reloads will not overwrite them** (the configuration tree is rebuilt and automatically reapplied in write order, including runtime deletions). They are not persisted to disk, and are lost after process restart; runtime bindings written by a module are cleaned up when the module is unloaded. Subsequent `persist=True` writes (user-persistent semantics) to the same path will replace the runtime rules.

### ② Identity Dimension

```python
# Binding strategies (level determined by parameters: user > session > bot > adapter; allow / deny chosen)
scope.set_identity("onebot11", user_id="u_bad", deny=True)
scope.set_identity("onebot11", user_id="spam_*", deny=True)    # Key supports glob / re: regex
scope.set_identity("onebot11", bot_id="123456", session_id="g9", allow=True)

# Read / Delete
scope.get_identity("onebot11", user_id="u_bad")   # {"deny": True}
scope.delete_identity("onebot11", user_id="u_bad")
```

### ③ Outbound Dimension

```python
# Set restriction rules (allow: str|list; deny: bool|str|list; whole rule replacement semantics)
scope.set_action("MyModule", "send", deny=True)                    # Disable all sending
scope.set_action("MyModule", "send", allow=["Text"])               # Allow only text messages
scope.set_action("MyModule", "api", deny=["set_*", "leave_*"])     # Disable management APIs

# Read / Delete
scope.get_action("MyModule", "send")       # {"allow": ["Text"]} original rule
scope.delete_action("MyModule", "send")    # Remove single action
scope.delete_action("MyModule")            # Remove all action restrictions for this module
```

### General

```python
scope.get("platforms")   # Dictionary-style fallback: dot-separated path to read any section
scope.topology()         # Full configuration tree (for Dashboard)
scope.stats()
# {"module_calls": .., "module_filtered": .., "identity_checks": .., "identity_denied": ..,
#  "action_checks": .., "action_denied": .., "cache_hits": .., "cache_misses": ..}
scope.reset_stats()
scope.clear()           # Clear all configuration (only in-memory effect)
```

### Advanced: Dictionary-style Dot-separated Path Fallback

Dimensional methods cover daily scenarios; when you need to directly access any node (or future added dimensions), use the dictionary-style API — `get` / `set` / `delete` accept dot-separated paths (deep dict merge, immediate read after write),
and provide `scope[path]` / `scope[path] = v` / `del scope[path]` / `path in scope` protocols:

```python
scope.set("bots.onebot11.123456", {"modules": ["Chat"], "blocked": []})
scope.set("identity.users.onebot11.u_bad", {"deny": True})
scope.get("actions.MyModule.send")

scope["platforms.onebot11"]        # Read (throws KeyError if not exists)
scope["platforms.onebot11"] = {...}  # Write
del scope["platforms.onebot11"]      # Delete
"actions.MyModule" in scope          # Existence check
```

## Interception Observability: `scope.blocked` Event

When scope interception (module filtering / identity rejection) occurs, it broadcasts the lifecycle event **`scope.blocked`**,
making "who was blocked, at which level" subscribable, countable, and presentable in the Dashboard — interception does not reply by default, but is no longer an opaque black box.

| Field | Description |
|------|------|
| `dimension` | `"module"` (module dimension filtering) / `"identity"` (identity admission rejection) |
| `module` | The filtered module name (only module dimension) |
| `platform` / `bot_id` / `session_id` / `user_id` | The context where the interception occurred |

```python
from ErisPulse.Core.lifecycle import lifecycle

@lifecycle.on("scope.blocked")
def on_blocked(data):
    print(f"Blocked: {data['dimension']} {data.get('module') or data.get('user_id')}")
```

- The event is broadcast via `fire` background (zero overhead if no listeners, does not slow hot paths)
- Repeated interception with cache hits **does not** broadcast repeatedly — each combination is broadcast only once when the cache expires
- Distinct from `adapter.event.blocked` (event-level discard): that is event-level discard, this
  event is scope admission gate module / identity filtering

## Cache and Hot Reload

- `is_allowed` / `is_identity_allowed` / `is_action_allowed` results are cached with **LRU** (configurable via `scope.cache_size`), invalidated automatically by `set` / `delete` /
  configuration hot reload (`config.updated` / `config.set`)
- All dimension configurations take effect **immediately**, no restart required
- Scope is "event-by-event" judgment, does not remember across events: configuration changes, next event follows new rules

## Configuration Format Validation

Configuration format is validated section by section during loading / hot reload: invalid sections (e.g., `platforms` written as a string), invalid outbound rules (e.g., `allow` written as a number), unknown action names, unknown top-level keys (e.g., `alow` with a typo) will output **WARNING** and ignore the corresponding section / entry, while other valid configurations remain effective — errors no longer silently fail.

## Common Issues and Considerations

### 1. Configuration Hierarchy and Overriding

- Module dimension: session-level > Bot-level > platform-level, **full override** (if sub-level `merge = true`, entries are unioned individually). To "platform allows Chat, Bot adds Music", you can write `merge = true` in the Bot-level, or list both
- Identity dimension: user > session > Bot > adapter, take the **most specific** configured strategy (can do exception allow)
- Command user white/blacklists: exact command names take precedence over glob keys (see `event.command.acl`)

### 2. Module/Command Not Responding

First suspect scope rather than the module itself:

```python
from ErisPulse import sdk

print(sdk.scope.is_allowed(event.get_platform(), bot_id, "MyModule", session_id))
print(sdk.scope.is_identity_allowed(event.get_platform(), bot_id, session_id, user_id))
print(sdk.scope.stats())   # module_filtered / identity_denied > 0 indicates interception records
```

Filtered modules default to no reply (module dimension and identity dimension, avoiding rule exposure), but broadcast the `scope.blocked` lifecycle event and statistics continue to accumulate;
commands rejected by ACL will reply "insufficient permissions" explicitly.

### 3. Outbound Action Rejected When Troubleshooting

```python
from ErisPulse import sdk

print(sdk.scope.get("actions.MyModule"))
print(sdk.scope.stats())   # action_denied > 0 indicates intercepted calls
```

Interception is **explicit**: rejected calls return the standard failure response (`retcode = 34601`) without initiating a network request.

### 4. Session Identifier Isolation Across Platforms

The `(platform, session_id)` combination is the unique identifier. `scope.sessions.onebot11."789"` only applies to onebot11, not affecting a session with the same `789` on telegram. The same applies to identity dimension user keys.

## Topology Tree API

`ModuleManager.get_topology()` and `AdapterManager.get_topology()` provide module/adapter ownership relationship data,
`sdk.get_topology()` aggregates them (including scope):

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
#   "adapters": {                                  # Adapter → Bot → Scope
#     "onebot11": {
#       "status": "started", "enabled": True,
#       "bots": {"123456": {"status": "online", "scope": {...}}},
#       "scope": {"modules": [...], "blocked": [...]},
#     }
#   },
#   "scope": {                                     # Scope (module / identity / outbound actions)
#     "platforms": {...}, "bots": {...}, "sessions": {...},
#     "identity": {"adapters": {...}, "bots": {...}, "sessions": {...}, "users": {...}},
#     "actions": {...},
#   },
# }
```

- Module topology aggregates commands registered by the module, event handlers, HTTP/WS/SSE routes, and lifecycle hooks, facilitating the drawing of module resource trees.
- Adapter topology aggregates status of each adapter, status of subordinate Bots, and platform-level/Bot-level scope bindings (module dimension).
- **JSON-safe output**: `get_topology(json_safe=...)` defaults to `True`, returning structures directly serializable via `json.dumps` — module `info` retains only pure data's `meta` sub-table (discarding `module_class` / `strategy` runtime objects), and other nodes (including arbitrary objects inserted by adapter authors into Bot `info`) are sanitized (class objects take `__name__`, unserializable objects fall back to `str()`). Dashboards / WebUI can directly serialize the return; for original objects, pass `json_safe=False`.



### 归属权（owner）系统

# Ownership (owner) System

> [!TIP]
> **When to read this**: When troubleshooting resource leaks, understanding the cleanup chain during unload/disable, or declaring owned resources. Skip if not needed, as it does not affect the use of other features.

> **After reading, you will know**: How the owner context automatically assigns resources, the complete overview of owned resources, the full sequence of cleanup chains during unload/disable, and which resources are not cleaned up during unload (design boundaries).
>
> **This section does not cover**: Permission checks for "when resources become effective" (see [Scope (scope)](scope.md)); recommended practices and forced cancellation boundaries for background tasks (see [Lifecycle Management · Background Task Ownership and Automatic Cancellation](lifecycle.md#background-task-ownership-and-automatic-cancellation)).

Ownership is the foundation for modules' "plug-and-play" functionality: all framework resources registered during module loading are automatically named, and are recycled with a single click during unload/disable—module authors only need to declare resources, without manually writing cleanup logic.

> **Related systems**: Scope determines "whether resources are effective" during event dispatching, while ownership determines "who owns the resources and who is recycled during unload" during the lifecycle. Scope is detailed in [Unified Control Plane (scope)](scope.md), and background tasks are covered in [Lifecycle Management](lifecycle.md#background-task-ownership-and-automatic-cancellation).

{!--< tips >!--}
1. Ownership is automatically recorded at the **moment of registration** based on `current_owner`, requiring zero changes to module code.
2. Unload and disable share the same cleanup chain (`_cleanup_module_registrations`), where failures at each step only trigger warnings and do not interrupt the process.
3. Resources with user configuration semantics (persistent overrides / scope rules / command ACL) are **not** cleaned up during module unload.
4. External handles hosted by utility modules can be attached to the cleanup chain using `on_cleanup(cb)`, which are automatically called back when the corresponding module is unloaded (see [Guide to Utility Modules: Hosting Handles of Other Modules](#guide-to-utility-modules-hosting-handles-of-other-modules)).
{!--< /tips >!--}

## Owner Context Mechanism

The `owner` is passed through the context variable `current_owner` (`ErisPulse.runtime.context`):

```python
from ErisPulse.runtime import owner_scope, get_current_owner

with owner_scope("MyModule"):
    # All resources registered within this context are automatically attributed to MyModule
    assert get_current_owner() == "MyModule"
```

The framework automatically injects the `owner` at the following points (module/adapter code does not need to manually wrap these):

| Timing | Owner Value | Location |
|--------|-------------|----------|
| Module `load()` | Module name | Throughout instantiation + `on_load` |
| Adapter `start()` / `restart()` | Platform name | Throughout adapter startup |
| `activate_on` lazy-load stub registration | Module name | During placeholder command/handler registration |
| Event handler execution | Module name of handler's owner | Re-injected at handler/command entry |

Re-injection during execution means that command handlers declared in `on_load` will still be automatically attributed to the module if they call registration APIs (such as `sdk.adapter.on()` or `overrides.*.set(persist=False)`) during runtime.

## Resource Ownership Overview

All resources registered by a module within its loading context are recorded for ownership and automatically reclaimed upon unloading/disabling:

| Resource | Registration Method | Cleanup Call |
|----------|---------------------|--------------|
| Command | `@command()` / Command dict declaration | `command.unregister_by_owner()` |
| Event Handler | `@message` / `@notice` / `@request` / `@meta` | `handler.unregister_by_owner()` |
| Adapter Event Listener | `sdk.adapter.on()` / `raw=True` | `adapter.unregister_handlers_by_owner()` |
| Adapter Middleware | `@sdk.adapter.middleware` | Same as above |
| Routes (HTTP/WS/SSE) | `router.http()` / `websocket()` / `sse()` | Double fallback by namespace + by owner |
| Route Middleware | `@router.middleware()` / `add_middleware()` | `router.unregister_all_by_owner()` |
| Dashboard Home Entry | `router.register_home_entry()` | `unregister_home_entries_by_owner()` |
| Custom Session Type | `register_custom_type()` | `unregister_custom_types_by_owner()` |
| Platform Event Method Injection | `register_event_method()` / `register_event_mixin()` | `unregister_event_methods_by_owner()` (module unloading automatically reclaims, old closures no longer leak) |
| Background Tasks | `self.spawn()` | `cancel_owner_tasks()` |
| External Cleanup Hook (Tool Module Managed) | `runtime.on_cleanup(cb)` | `run_owner_cleanups()` (triggered during unload/disable/adapter shutdown chain) |
| Lifecycle Hook | `lifecycle.register()` | `lifecycle.unregister_by_owner()` |
| Master Source Provider | `master.provider` | `master.unregister_by_owner()` |
| i18n Translation Keys | `I18nClass` declaration (domain=module name) | `i18n.unregister_domain()` |
| Event Override (Runtime) | `overrides.*.set(persist=False)` | `overrides.unregister_by_owner()` |
| Interactive Sessions (wait_reply waiting / lease) | `event.wait_reply()` / `sdk.interaction.acquire()` | `interaction.cancel_by_owner()` (waiter immediately receives cancellation) |
| Context Data | `runtime/context` recorded by owner | Precise cleanup by module |

On the adapter side, corresponding resources (with platform name as owner) are reclaimed by `_cleanup_adapter_resources` during the adapter's `shutdown()` / `restart()`, including:

| Resource | Cleanup Call |
|----------|--------------|
| Adapter's own `on()` handlers and middleware | `adapter.unregister_handlers_by_owner(platform)` |
| Platform Event Method Extension (`EventMixin`) | `unregister_platform_event_methods(platform)` |
| Custom Session Type | `unregister_custom_types_by_owner(platform)` |
| Interactive Sessions (wait_reply / lease pending on this platform) | `interaction.cancel_by_platform(platform)` |
| i18n Translation Domain (domain=configuration key) | `i18n.unregister_domain(configuration key)` |
| Fine-grained Namespaced Routes | `router.unregister_all_by_owner(platform)` |

## Unload/Disable Cleanup Sequence

`unload()` and `disable()` share the same cleanup chain (each step is independently wrapped in try/except, failures are only logged, **not interrupting subsequent cleanup**):

```mermaid
flowchart TD
    A["unload / disable"] --> B["on_unload()（timeout protection）"]
    B --> C["Fallback: cancel background tasks (cancel_owner_tasks）"]
    C --> C1["External ownership cleanup hooks<br/>（registered by tool modules via on_cleanup, triggered by run_owner_cleanups）"]
    C1 --> D["_cleanup_module_registrations<br/>＝ ownership.reclaim_sync()"]
    D --> D1["i18n translation domains"]
    D1 --> D2["Routes: namespace + owner fallback<br/>（exact deletion by route object identity,<br/>including middleware / home entry）"]
    D2 --> D3["Adapter event handlers / middleware"]
    D3 --> D4["Commands + event handlers"]
    D4 --> D5["Custom session types"]
    D5 --> D5b["Platform event method injection"]
    D5b --> D6["Runtime event overwrites (persist=False）"]
    D6 --> D7["Owner source provider"]
    D7 --> D8["Lifecycle hooks"]
    D8 --> E["Remove SDK attributes + lazy-loaded proxies"]
    E --> F["Auto-light audit: orphan owner warnings"]
```

`sdk.uninit()` performs additional global fallback on exit: all adapters shutdown → all modules unload → `router.stop()` (clear routes/middleware/home entry) → `cancel_all_background_tasks()` → clear event handlers and hooks.

## Ownership Facade (ownership)

The sixteen steps of chain cleanup converge under the ownership facade `ErisPulse.Core.ownership`, with four verbs covering "reclaim, count, scan, audit"—the subsystem-specific `*_by_owner` reclaim functions remain unchanged, serving as internal implementations of the facade:

| Verb | Purpose |
|------|---------|
| `ownership.reclaim(owner)` | Unified reclaim of all resources owned by owner (task cancellation → cleanup hooks → registered resource types; asynchronous full version) |
| `ownership.reclaim_sync(owner)` | Registered resource type reclaim (synchronous version, for synchronous unload paths) |
| `ownership.counts(owner=None)` | Read-only count of resources registered under owner (None for all owners) |
| `ownership.orphans()` | Orphan scan: resources registered but owner has been unregistered (concrete leak report) |
| `ownership.audit(owner, deep=)` | Leak audit report (counts + orphans + optional gc instance survey) |

```python
from ErisPulse.Core import ownership

ownership.reclaim_sync("MyModule")       # {'commands': 1, 'routes_http': 2, ...}
ownership.counts("MyModule")             # Count of registered resources
ownership.orphans()                      # [{"owner": "ghost", "total": 2, ...}]
```

**Audit entry points**:

- **Automatic light audit** after unload/reload: issues WARNING alert when orphaned owner resources are found (zero-cost counting scan)
- `sdk.module.audit(name, deep=True)`: Module instance gc survey—when an instance is unreclaimable, it reports the referencing type (identifying "who is holding the old instance"); involves global pause overhead, used only for explicit troubleshooting
- Deep survey is an explicit operation, not configurable, and does not perform automatic repair

## Hot Reload Failure Rollback

Hot reload has been changed to "**Snapshot before Unload → Automatic Rollback on Failure**": When a new version encounters syntax errors, missing dependencies, or fails to load, the old instance and its registration status (registry entries, sdk attributes, sys.modules entries) are automatically restored, ensuring uninterrupted service. The log will indicate "Rolled back to old instance to continue service."

Best-effort semantics (documented boundaries):

- Side effects already executed in `on_unload` (such as disconnected connections, canceled tasks) are irreversible—after rollback, the old instance is in a "cleaned-up" state and must be reloaded to become fully available again.
- Manual references to the old instance cached by third-party libraries during runtime are not restored.
- If the target package has been unloaded (entry-point disappeared), it is considered a successful unload and no rollback will occur.

## Design Boundaries: Resources Not Cleaned on Unload

Ownership only recovers **runtime resources registered by module code**. The following resources are **user-configured semantics** (controlled by the user, possibly intentionally configured), and persist after module unload:

| Resource | Semantics | Description |
|----------|-----------|-------------|
| `overrides.*.set(persist=True)` | Persistent overrides | Written to configuration file, effective across restarts; not deleted on module unload (user explicitly configured) |
| `scope.set_action()` and other scope rules | Permission control plane | Managed by user/Dashboard; rules are not reclaimed when the module is unloaded |
| `overrides.acl.set(persist=True)` | Command ACLs | Same as above |
| `Conversation.save()` persistence | Multi-turn conversation archives | Data assets are not cleaned up |

Runtime temporary writes (`persist=False`) are reclaimed by owner—**persistence is the boundary between "user assets" and "module runtime state."**

## Internal Implementation: How Ownership Works

**In one sentence**: The attribution chain (contextvar propagation) determines "whose responsibility it is," while the cancellation chain (task registry) determines "whether it can be canceled upon unloading." — These two chains operate independently, and proper resource cleanup requires both.

The ownership system consists of **two independent chains**. Understanding their division of labor is essential for troubleshooting ownership issues.

### Attribution Chain (Contextvar Propagation)

The `ContextVar`s such as `current_owner` in `runtime/context.py` are responsible for **attribution** — "Whose responsibility is this resource registration or call initiated by the code at this moment?" The propagation follows the semantics of Python's `contextvars`:

| Execution Path | Context Propagated | Attribution Result |
|----------------|--------------------|--------------------|
| Synchronous call chain / `await` chain | ✅ Propagated | Correct attribution |
| `asyncio.create_task` within `owner_scope` | ✅ Propagated (task copies the context at creation) | Correct attribution for framework calls within the task |
| `run_in_executor` / bare thread | ❌ Not propagated | Attribution lost |
| Custom event loop | ❌ Not propagated | Attribution lost |

> Attribution ≠ Registration: Context propagation only affects "whose responsibility it is." Whether a resource can be cleaned up depends on whether it enters the subsequent cancellation chain.

### Cancellation Chain (Task Registry)

The `_owner_tasks` registry in `runtime/tasks.py` manages **lifecycle** — "Which unfinished tasks belong to the owner, and should be canceled together during unloading." Tasks enter the registry through:

1. **Explicit Scheduling**: `spawn_background()` / `self.spawn()` → captures `current_owner` at creation (or explicitly via `owner=` parameter) → registers into the table;
2. **Task Factory Automatic Registration** (2.8.3): `install_owner_task_factory()` is installed at the main event loop during framework startup — **any** task creation (including `create_task` inside third-party libraries) passing through the factory reads `current_owner`, and registers if it is not None.

The registry self-cleans: Each task has a `done_callback`, and is removed from the table upon completion, with no leaks.

### Cancellation Timing (Module Unload)

```
module.unload()
  → on_unload(event)                    # Module-specific cleanup (fallback timeout protection)
  → Framework unregisters commands/events/hooks/routes for this owner
  → cancel_owner_tasks(owner)           # Registry fallback cancellation
      → cancel each task individually   # Excludes the task itself executing the cancellation logic
      → await gather(pending, timeout)  # Wait for cleanup (no blocking after timeout)
```

### Troubleshooting Approach

- **Resources not cleaned up** → Check the registry: Does `get_owner_tasks("MyModule")` contain the task? If not, the registration path did not pass through the attribution chain (import phase / thread / independent loop), refer to the table above to locate the issue.
- **Incorrect attribution** → Check the value of `get_current_owner()` at the time of error; for asynchronously delayed execution (callbacks/tasks), attribution is taken from the context at creation, not at execution time.

## Module Author Guide

### Recommended Practices

```python
from ErisPulse import sdk
from ErisPulse.Core.Event import command
from ErisPulse.runtime import owner_scope, spawn_background

class MyModule(BaseModule):
    async def on_load(self, event):
        # Framework resources: automatically owned, no manual cleanup required
        self.task = self.spawn(self.polling())      # Background task
        sdk.router.register_home_entry("My Module", "/my")  # Home entry

        # Module-specific resources: include in owner_scope to integrate into ownership system
        with owner_scope("MyModule"):
            self.client.on_event(self._handle)      # Hypothetical custom registration

    async def on_unload(self, event):
        # Framework resources have been automatically cleaned up, only clean up non-owner_scope covered resources
        await self.client.close()
```

### Notes

- **Registration during import has no ownership**: Hooks/handlers registered at the module's top level (during import) occur before `owner_scope`, and are considered framework-level resources (owner=None) and **will not be cleaned up**. Always register inside `on_load()`.
- **Custom domain i18n registration**: When `i18n.register(domain=...)` uses a domain different from the module name, it won't be automatically cleaned up. Please ensure domain=module name.
- **Background tasks recommended via `self.spawn()`**: As of 2.8.3, raw `asyncio.create_task` will also **automatically register ownership** (Task Factory automatically registers, cancels on unload as a fallback). However, `self.spawn()` remains the recommended approach—supporting non-main loop thread scheduling back to the main loop, explicit `owner=` assignment, and fire-and-forget to prevent GC. **For versions before 2.8.3**, raw tasks are not owned, and `self.spawn()` must be used.
- **Cleanup chain "failure only logs warning"**: Single-step cleanup exceptions will not block other resource releases, visible in DEBUG/WARNING log levels; enable TRACE for troubleshooting.

### Registration Timing → Ownership Result Comparison Table

| Registration Scenario | Ownership Result | Explanation |
|-----------------------|------------------|-------------|
| Registered inside `on_load()` via framework APIs (commands/events/lifecycle/routing decorators) | Owned by module | Automatically unregistered on unload |
| Registered at module top level (during import) | **No ownership** (owner=None) | Not cleaned up, do not use |
| Background tasks created via `self.spawn()` | Owned by module | Automatically cancelled on unload |
| Registered inside `owner_scope("Name")` via third-party APIs | Owned by module | Depends on third-party callbacks executing synchronously within scope |
| Raw `asyncio.create_task` (including `loop.create_task` / `ensure_future`) | **Automatic ownership** (Task Factory, 2.8.3+) | Instantly reads `current_owner` on creation, automatically registers within owner context, cancels on unload as a fallback; see [Internal Implementation](#internal-implementation-how-ownership-works) below |
| Tasks created internally within third-party library asynchronous callbacks (e.g., aiohttp / APScheduler) | **Automatic ownership** (Task Factory, 2.8.3+) | If `current_owner` is injected (e.g., during framework handler execution), the task automatically registers |
| `run_in_executor` (thread pool) | **No ownership** (not asyncio.Task) | Threads are not managed by Task Factory, lifecycle must be managed manually |
| Registration within an independent event loop (self-created loop) | **No ownership** | Task Factory is only installed in the main loop; contextvars do not propagate across event loops |

> Principle: **Ownership follows the `current_owner` context at the moment of registration**; any asynchronous delay, thread pools, or independent loops will detach from this context—explicitly enter `owner_scope` when ownership is required.

## Tool Module Guide: Handling References to Other Modules

**Scenario**: Tool modules such as scheduled tasks, registries, and connection pools hold references to other modules—when a module calls `sdk.Cron.on_trigger(handler)` in its `on_load`, your container stores a callback pointing to the instance of the calling module. The framework automatically cleans up all framework-level resources registered by the module, but it cannot clean up references stored in your **private container**: after the module is unloaded, your container still holds its instance, preventing it from being garbage collected (memory leak, `purge` leak diagnostics report "un回收able").

**Solution**: In the same function where you register the other module's resources, call `on_cleanup()`. The framework will automatically invoke your cleanup function when the module is unloaded or disabled:

```python
from ErisPulse.Core.Bases import BaseModule
from ErisPulse.runtime import off_cleanup, on_cleanup

class CronModule(BaseModule):
    def __init__(self):
        self._entries = {}  # {module_name: list of callbacks registered by the module}

    def on_trigger(self, handler):
        # Automatically identifies the caller module name (whether called directly in on_load or via module.call),
        # returns the resolved owner, which can be used directly as a named key
        owner = on_cleanup(self._drop)
        self._entries.setdefault(owner, []).append(handler)

    def _drop(self, owner: str):
        """Called automatically by the framework when the module is unloaded/disabled: simply discard its handle"""
        self._entries.pop(owner, None)

    async def on_unload(self, event):
        off_cleanup(self._drop)  # ③ Unregister the hook before self-unloading to avoid the hook table holding a reference to self
```

Guaranteed framework behavior:

| Concern | Behavior |
|---------|----------|
| Trigger Timing | Triggered when the module is unloaded / disabled, or when the adapter shuts down—always within the framework's cleanup chain, before `purge` leak diagnostics |
| Caller Identification | Direct call uses `current_owner`; called via `module.call()` uses `current_caller`; can also explicitly specify via `on_cleanup(cb, owner="module_name")`. **Mandatory validation**: if `owner` cannot be resolved (missing from all three sources), a `ValueError` is raised—private tool modules should register hooks within their own loading context |
| Callback Signature | `cb(owner: str)`, synchronous or asynchronous; asynchronous callbacks have timeout protection (`CLEANUP_CALLBACK_TIMEOUT_SECS`, default 10 seconds) |
| Fault Tolerance | If a single callback fails or times out, only logs are recorded, without affecting other hooks or the cleanup chain |
| Duplicate Registration | Identical `(owner, callback)` pairs are idempotently deduplicated |

**When Not Needed**: If the module registers framework-level resources (commands, event handlers, routes, background tasks, etc.), the framework automatically cleans them up (see [Resource Ownership Overview](#resource-ownership-overview) above). Only references held in your private container require `on_cleanup`. A quick-reference version from a module developer's perspective is available at [Best Practices · Tool Modules](../developer-guide/modules/best-practices.md#tool-modules-handling-references-to-other-modules-should-catch-unload-notifications).



### 影子模块与灰度转正

# Shadow Modules and Gradual Promotion

> [!TIP]
> **When to read this**: When you need gradual release—running a new version in parallel, comparing behaviors, and promoting or rolling back. Skip if not needed; it won't affect other features.

> **After reading, you will know**: The five isolation gates of shadow modules, alignment methods for behavior diff, the `promote` promotion and rollback flow when promotion fails, and the honest boundaries that the framework cannot block.
>
> **This section does not cover**: The general hot reload and ownership cleanup mechanism for ordinary modules (see [Ownership (owner) System](ownership.md)).

A shadow module is a **new version** of the same module, running in parallel with the live version under an independent owner (e.g., `roll_shadow`). It receives **copies** of real events, and its outbound messages are **intercepted and recorded** rather than actually sent. By comparing behaviors in `shadow_diff`, you can confirm the new version is harmless before promoting it with one click via `promote`, or discarding it at any time with `dismiss`. **No code changes are required**; the entire process is driven by runtime APIs: similar to `load / unload / reload`, these operations can be directly invoked by the Dashboard or custom management modules, with no configuration needed.

{!--< tips >!--}
1. Start: ``await sdk.module.shadow_start("roll", source="path/to/v2")``
   ——The new version runs in parallel with the old version under an independent owner (default is the path name).
2. The shadow does not participate in real distribution or dependency graphs: commands with the same name go into the shadow directory, routes are registered but not mounted, lifecycle broadcasts are silent, and `module.call` and dependency resolution still point to v1.
3. Promotion is always confirmed by a human: ``await sdk.module.promote_shadow("roll")``; if it fails, the old instance automatically rolls back and continues serving; ``dismiss_shadow`` discards the shadow at any time.
{!--< /tips >!--}

## Quick Start

```python
# v2 code: Standard module format, shadow-agnostic (any directory, e.g. downloads/roll_v2/)
```

```python
# In production bot (Dashboard / Management module call), start shadow with one line:
await sdk.module.shadow_start("roll", source="downloads/roll_v2")
# → Shadow runs independently as owner "roll_v2", coexisting with v1, with outbound traffic intercepted and tracked

# During trial period, compare behaviors:
report = sdk.module.shadow_diff("roll")
# {"shadow_owner": "roll_v2", "count": 3, "aligned": [...]}
```

- **v1 actual send**: Bot timeline from inbox (transcript)
- **v2 intended send**: Shadow ledger ("what was intended to be sent" recorded in outbound gate)
- Both aligned by `trace_id` — for the same message, both versions' triggers/missed triggers and intended vs. actual sends are clearly visible

After confirming correctness, promote:

```python
await sdk.module.promote_shadow("roll")   # Promote, rollback to v1 on failure
await sdk.module.dismiss_shadow("roll")   # Or: discard shadow
```

## Five Isolation Gates

| Gate | Mechanism |
|------|-----------|
| Event Copy | The shadow handler receives an **independent copy** of the event (marked with `shadow`) — modifications, claims, or stopping propagation by the shadow only affect the copy, not the original event chain |
| Outbound Gate | All `Send` DSL and `Api` calls from the shadow are intercepted and recorded (with a fake success response), without actually being sent — the shadow will not send duplicate replies |
| Storage Overlay | KV writes from the shadow go into an in-memory overlay and are discarded from the persistent store; reads first check the overlay, and if not found, transparently read from the real store (gray-scale runs against real data); deletes are recorded as tombstones |
| Routing Shield | HTTP/WS/SSE routes from the shadow are only registered but not mounted; commands with the same name are registered in the shadow command directory, and platform event method injection is prohibited |
| Lifecycle Silence | The shadow does not broadcast its own lifecycle events, nor does it participate in the ecosystem dependency graph (`module.call` and dependency resolution still point to v1, preventing half-finished components from being depended upon) |

Configuration Inheritance: The shadow **inherits the configuration section from the original module by default** (otherwise gray-scale would be distorted), and the configuration takes effect in place after promotion.

## Honest Boundaries (Can't Be Blocked)

- The framework can intercept all sending / API / KV storage / unified HTTP client operations;
  However, modules bypassing the framework by directly starting `aiohttp`, spawning threads, or writing to external systems cannot be intercepted by the framework.
- **ORM read/write operations are not within the coverage semantics** (clean implementation at the SQL layer is not possible with line-by-line overlay) — during shadow periods, it is recommended to avoid relying on ORM for isolation.
- **Shadow source is a local path**: New code is imported via path and loaded by an independent owner; the same PyPI package cannot exist in both old and new versions within the same interpreter due to the `sys.modules` single-key limitation.
- The leak auditor (`sdk.module.audit`) can see the ownership of shadow resources; side effects bypassing the framework will at least not go unnoticed.

## Promote and Rollback

The `promote` process: take a snapshot of the current version (including cascading dependents) → completely uninstall → register the shadow instance with the real name and load it. If any step fails, automatic rollback occurs and the old instance continues to serve (best-effort semantics: side effects executed by `on_unload` cannot be undone, and the old instance is in a cleaned-up state after rollback). Promoted shadow resources are reclaimed and bindings are released; the original module configuration section takes effect in place.

**Persistence Reminder**: `promote` is a runtime switch—after a restart, v2 will still be used. You need to **persistently install** the new version (`pip install -U` the new version / replace the plugin file). The runtime switch will not automatically handle package management for you.



### 模块间通信

# Inter-Module Communication

> [!TIP]
> **When to read this**: When you need cross-module calls (RPC), service contracts, directed events, or cold-start replay. Skip if not needed, as it won't affect the usage of other features.

> **After reading, you will know**: The selection mnemonic for the three-layer communication model (RPC / directed events / broadcast), `meta.services` service contracts and service directory, outbound audit configuration, lazy wake-up, and cold-start replay.
>
> **This section does not cover**: The registration / triggering / priority mechanism of the lifecycle event system itself (see [Lifecycle Management](lifecycle.md)); lazy loading configuration and `activate_on` declaration (see [Lazy Loading System](lazy-loading.md)).

> [!NOTE]
> This chapter requires ErisPulse **2.8.0+**.

ErisPulse's modules have a **three-layer communication model**, arranged from "point-to-point → directed → broadcast":

| Layer | API | Semantics | Typical Scenarios |
|---|---|---|---|
| **RPC** | `await sdk.module.call("Chat", "get_history", ...)` | Point-to-point request-response with contract / audit / timeout | Invoking capabilities of another module (e.g., fetching history, translation, refund) |
| **Directed Events** | `await lifecycle.emit("message_received", {...}, to="Chat")` | Distributed only to lifecycle hooks registered by the specified module | Upstream state change notification to downstream (e.g., "a new message was received") |
| **Broadcast** | `await lifecycle.emit("config.updated", {...})` | Framework-wide lifecycle events | Hot configuration updates, module up/down events |

{!--< tips >!--}
Selection Mnemonic: **Use `call` when you need a return value, use `emit(..., to=...)` to notify a specific module's hooks, and use `emit(...)` to notify everyone.**
{!--< /tips >!--}

## RPC: module.call

```python
result = await sdk.module.call("Chat", "get_history", session_id, n=20)
```

Difference from direct attribute access `sdk.module.Chat.get_history(...)` (unchanged):

| | `module.call()` | Direct attribute access |
|---|---|---|
| Target not registered / enabled | Throws `ModuleNotAvailableError` | Throws `AttributeError` |
| Lazy-loaded module | **Automatically wakes up** (event-driven modules use activation lock) | Async initialization throws RuntimeError |
| `current_owner` | Attributed to the **target module** (its internal wait_reply / send / logs are correctly attributed) | Maintains caller |
| Timeout | Default 30 seconds (`timeout=` overrides, None means no timeout) | None |
| Scope audit | Caller passes through outbound gate `actions.<caller>.call` | None |
| Contract validation | `meta.services` whitelist | None |

### Exception Hierarchy

```
ModuleError                      # Base class for module system exceptions
└── ModuleCallError              # Base class for cross-module calls (includes module / method attributes)
    ├── ModuleNotAvailableError  # Target not registered / enabled / activation failed
    ├── ServiceNotProvidedError  # Method not in services whitelist / private method / does not exist
    └── ModuleCallTimeoutError   # Coroutine method timeout
```

All are part of the `ErisPulseError` hierarchy, and can be caught via `from ErisPulse.Core import ModuleCallError`.

## Service Contract: meta.services

The service provider declares the whitelist of services offered externally in `get_meta()` (symmetrical to the `commands` field):

```python
from ErisPulse.Core.Bases import BaseModule, ModuleMeta

class ChatModule(BaseModule):
    @staticmethod
    def get_meta() -> ModuleMeta:
        return ModuleMeta(
            name="Chat",
            services=[
                "get_history",                                       # Simple form
                {"name": "translate", "description": "Translate text into a specified language"},  # With description
            ],
        )

    async def get_history(self, session_id, n=20): ...
    async def translate(self, text, target_lang): ...
    def _internal_helper(self): ...   # Methods with leading underscore are always prohibited from external calls
```

**By default, services are invisible to developers**:

- If `services` is not declared → all **public** methods are naturally callable via `module.call()` (consistent with direct attribute access),
  no declaration is required
- After declaration → the scope is restricted to the whitelist, calling outside the whitelist raises `ServiceNotProvidedError`—used to mark
  "these methods are the ones promised externally"
- The main control authority lies with the user: `scope.actions` configuration determines "who can call whom" (see audit below),
  the module author's `services` is only a service declaration, and the two layers are independent

**Service Descriptions**: Provide human- or AI-readable descriptions for each service—leave empty if not needed,
the description is automatically taken from the **first line of the method's docstring** (the framework already requires docstring style):

```python
async def translate(self, text, target_lang):
    """Translate text into a specified language"""    # ← This line automatically becomes the service description
    ...
```

**Parameter Hints**: The caller (especially AI agents) needs to know the meaning of each parameter. Leave empty if not needed,
hints are automatically taken from the **`:param:` lines** in the method's docstring:

```python
async def render_card(self, html, width=800, height=0):
    """Render HTML into an image file

    :param html: HTML text to render          ← Automatically becomes the parameter hint
    :param width: Canvas width in pixels, 0 for adaptive to content
    :param height: Canvas height in pixels, 0 for adaptive to content
    """
```

For fine-grained control (overriding docstring or multi-language support), use the dict form to declare `description` and `parameters`
(both support i18n dictionaries; `parameters` are merged with the docstring **by parameter**, explicit declaration within a single parameter takes precedence,
parameters declared that do not exist in the signature are filtered):

```python
services=[
    {"name": "translate", "description": "Translate text into a specified language"},
    {"name": "summarize", "description": {"i18n": "Chat.meta.svc.summarize", "default": "Summarize conversation"}},
    {
        "name": "render_card",
        "description": "Render HTML into an image file",
        "parameters": {"html": "HTML text", "width": "Width in pixels, 0 for adaptive"},
    },
]
```

## Service Directory: services()

```python
sdk.module.services()
# {'Chat': [{'name': 'get_history', 'signature': '(session_id, n=20)',
#            'description': 'Translate text into the specified language',
#            'parameters': {'session_id': 'Session ID', 'n': 'Number of entries to return'}}]}

sdk.module.services("Chat")   # Query only a specific module
```

- Only modules that explicitly declare `meta.services` are listed (modules without declaration do not appear in the directory)
- Each service includes a method signature string (extracted via `inspect.signature`), description text, and parameter hints
- **Lazily loaded modules are also included in the directory** (service discovery occurs before loading) — the caller can decide whether to `call()` to activate the target module
- Modules are also included in the topology: each entry in `sdk.module.get_topology()` contains a `services` field

{!--< tips >!--}
**MCP Roadmap**: The service directory (name + signature + description + parameter hints) naturally forms the shape of an MCP tool — each service becomes ``{"name", "description", "parameters"}``. In the future, the framework could directly expose ``services()`` as an MCP server endpoint, allowing AI to discover and invoke module capabilities; ``scope.actions.call`` auditing naturally becomes a security gate for AI calls.
{!--< /tips >!--}

## Outbound Audit: Who Can Call Whom

Each `module.call()` passes through the scope outbound gate as the **caller module**:

```toml
[ErisPulse.scope.actions.CallerModule.call]
deny = ["Chat.get_history"]        # Deny CallerModule from calling Chat's get_history
# allow = ["Chat.get_*"]           # Or whitelist: only allow calling Chat's get-* services
```

- `name` format is `<target module>.<method name>`, supporting exact / glob / `re:` regex
- Framework-level calls (without owner context, e.g., startup scripts) are not subject to audit constraints
- Denied calls throw `ModuleCallError` (TRACE log `core.module.call_denied`)

See [Scope (scope)](scope.md) for configuration details on the outbound dimension.

## Directed Events: lifecycle.emit with to parameter

Lifecycle events support directed propagation: when `to` specifies the target owner (owner), the event is only delivered to hooks registered by that owner (modules automatically register hooks in `on_load` and record the owner). Other modules and wildcard `*` handlers do not receive the event.

```python
from ErisPulse.Core.lifecycle import lifecycle

# Emitter: event is only delivered to hooks registered by Chat module
await lifecycle.emit("message_received", {"text": "hi", "from": "u1"}, to="Chat")

# Subscriber (inside Chat module): register same-name hook, owner is automatically recorded during registration
@lifecycle.on("message_received")
async def on_message_received(data): ...

@lifecycle.on("message")          # Point prefix also works (filtered by owner)
async def on_any(data): ...
```

Semantic details:

- If the target owner has no registered hooks → the event is **silently discarded** (does not send to non-existent places), use `lifecycle.has_handlers("message_received")` to probe in advance
- When `data` is a dict, it automatically carries `_trace_id` (without overriding existing values), integrating with full-chain tracing
- Broadcast and directed events share the same hook registration: `emit(...)` without `to` broadcasts to the entire framework, while with `to` the same event is only visible to the target module
- `emit_sync` / `submit_event` (compatibility API) also support `to=` parameter

> [!NOTE]
> Directed events are lightweight notifications, **do not perform target validation or lazy activation**; for target existence validation, contract audit, or return values, switch to [RPC: module.call](#rpcmodulecall).

## Lazy Loading and Invocation

`module.call()` transparently activates lazy-loaded modules:

- Event-driven lazy modules (`activate_on` declared) → Use activation lock `_activate()`, stub automatically unregisters after activation
- Regular lazy modules → Synchronous initialization or standard loading path (idempotent)
- Activation failure → `ModuleNotAvailableError`

That is: **the caller does not need to care whether the target module is loaded** and does not need to wait for it to be activated.

Directed events (`lifecycle.emit(..., to=...)`) do not perform lazy activation—target not loaded means no hooks, event silently discarded; use `module.call()` if you need to ensure delivery.

## Cold Start Replay

A newly installed / restarted module missed some chat messages—`get_load_strategy(replay=...)` allows the framework to replay the most recent messages from the session inbox to the module itself after it is ready:

```python
from ErisPulse.loaders import ModuleLoadStrategy

class MyAIModule(BaseModule):
    @staticmethod
    def get_load_strategy():
        return ModuleLoadStrategy(
            lazy_load=False,
            priority=100,
            replay="5m",        # Replay the last 5 minutes ("1h" / "300" seconds are also valid)
        )

    async def on_load(self, event):
        @message.on_message()
        async def handle(e):
            if e.get("replayed"):
                # Synthetic event: only supplement context, do not trigger side effects like sending
                ...
```

Semantic details:

- The data source is the [session inbox](interaction.md#session-inbox-eventhistory) (`sdk.transcript.recent()`), executed in the background after module loading, without blocking startup
- Synthetic events carry the `replayed: True` flag, along with complete `platform / detail_type / user_id / alt_message`, and are **only distributed to the module's own handlers**—other modules are unaffected by the replay
- If the inbox is not enabled / no records exist / the replay duration is invalid (`replay_invalid` warning), it is silently skipped

## Event Idempotency Deduplication

After platform websocket reconnection, the same event (with the same `event["id"]`) is often re-sent—event distribution entry deduplicates by id (capacity 4096), so the same id event is only distributed once.

```toml
[ErisPulse.framework]
event_dedupe = true   # Default on; turn off for test environments with fixed id synthetic events
```

The deduplication cache is automatically reset when adapters **register** (start of new connection lifecycle).



### 启动流程与手动控制

# Startup Flow and Manual Control

> [!TIP]
> **When to read this** : When you need to manually drive the startup chain, customize the startup sequence, or troubleshoot startup failures. Skip if not needed; it won't affect the use of other features.

ErisPulse's `await sdk.run()` / `await sdk.init()` encapsulates the entire startup chain into a single line of code. However, when you need to fully customize the startup process (e.g., partial loading, dynamic registration, hot-plug, injecting custom loading strategies), you need to understand what happens inside this chain and how to manually drive each step.

This article breaks down the startup chain into independent components, explains their respective responsibilities, call order, and provides an example of manual full startup.

> This article assumes you have run through [the first bot](../getting-started/first-bot.md) and understand the two `keep_running` modes of `sdk.run()`. This article focuses on the internal breakdown of the `init()` chain, as well as lower-level entry points such as `init()` / `init_task()` / `init_sync()`.

## Overview of SDK Top-Level Entry Points

In addition to the two `keep_running` modes of `run()`, the SDK also provides several lower-level initialization entry points, differing in **asynchronicity, return values, and exception handling**:

| Entry | Asynchronicity | Return Value | Exception Handling | Use Case |
|------|--------|--------|----------|----------|
| `await sdk.run(True)` | async, blocking to maintain | `None` (automatically `uninit` on shutdown) | Module/adapter errors are intercepted, not crashing the process | Pure bot application |
| `await sdk.run(False)` | async, non-blocking | `None` (no automatic unloading) | Same as above | Execute custom logic after initialization |
| `await sdk.init()` | async, requires await | `bool` | Internal capture of component exceptions, returns `False` on failure | Manual lifecycle control (paired with `uninit()`) |
| `sdk.init_task()` | async, returns Task without blocking | `asyncio.Task` | Same as `init()` | Concurrent initialization or when event loop is not running |
| `sdk.init_sync()` | **Synchronous**, blocking current thread | `bool` | Same as `init()` | Command-line scripts, synchronous entry without event loop |

> **Common Misconception**: `await sdk.init()` **is not equivalent to** `await sdk.run(keep_running=False)`. Two differences: ① `init()` returns `bool` (returns `False` on failure), `run()` returns `None`; ② `init()` only performs initialization, **does not automatically unload**, whereas `run()` automatically calls `uninit()` when the event loop ends. Therefore, when you need to manually pair unloading or customize the lifecycle, use `init()` + `uninit()`.

## Overview of the Startup Chain

`sdk.init()` (specifically its internal `Initializer.init()`) starts the entire framework in the following order:

```mermaid
flowchart TD
    A[0. Prepare Environment<br/>Configuration loading / Exception handling] --> B
    B[1. Parallel Discovery and Loading<br/>AdapterLoader.load / ModuleLoader.load<br/>Internal call to Finder.find_all] --> C
    C[2. Register Adapters<br/>AdapterLoader.register_to_manager] --> D
    D[3. Start Adapters<br/>adapter.startup] --> E
    E[4. Register Modules<br/>ModuleLoader.register_to_manager] --> F
    F[5. Initialize Modules<br/>ModuleLoader.initialize_modules<br/>Instantiate and mount to sdk] --> G
    G[6. Start Router Server<br/>router.start]
```

Corresponding core components:

| Layer | Component | Responsibility |
|----|------|------|
| Discovery | `AdapterFinder` / `ModuleFinder` | **Discover** adapters/modules from entry-points of installed packages |
| Loading | `AdapterLoader` / `ModuleLoader` | Discovery + import + metadata reading + enable/disable judgment, return object lists |
| Registration | `*Loader.register_to_manager` | Register objects to corresponding managers |
| Management | `sdk.adapter` / `sdk.module` | Maintain adapter/module instances, provide start/stop interfaces |
| Initialization | `ModuleLoader.initialize_modules` | Create module instances and mount to `sdk` (handle dependency topological sorting) |
| Routing | `sdk.router` | HTTP / WebSocket server |

> **Important**: `Finder` and `Loader` are two layers. `Loader` internally **already holds** a `Finder` (e.g., `AdapterLoader` has its own `AdapterFinder`, `ModuleLoader` has its own `ModuleFinder`). In most scenarios, you only need to use `Loader`; only when you need "list without importing" will you use `Finder` alone.

## Detailed Explanation of Each Component

### 1. Discovery Layer: Finder

Finder only finds out which packages provide adapters/modules, without importing or instantiating.

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

Each `EntryPoint` can be `.load()` to get the corresponding class, but usually you don't need to call it manually—`Loader` will do it.

### 2. Loading Layer: Loader

Loader performs "import + metadata reading + enable/disable judgment" on top of Finder.

```python
from ErisPulse.loaders import AdapterLoader, ModuleLoader
from ErisPulse import sdk

adapter_loader = AdapterLoader()
module_loader = ModuleLoader()

# load() internally: calls finder.find_all() → processes each entry-point → returns triplets
adapter_objs, enabled_adapters, disabled_adapters = await adapter_loader.load(sdk.adapter)
module_objs, enabled_modules, disabled_modules = await module_loader.load(sdk.module)
```

The three-tuple returned by `load()`:

| Return Value | Meaning |
|--------|------|
| `objs` (`dict`) | Name → Object (adapter class / module wrapper object) |
| `enabled` (`list[str]`) | Enabled names (not disabled in configuration) |
| `disabled` (`list[str]`) | Disabled names |

#### Diagnostic Information on Loading Failures

When a module/adapter throws an exception during loading or initialization, the framework skips that component and continues loading other components, while outputting a **summary of user code frames**, allowing you to locate the error position at the default INFO level without manually enabling DEBUG:

```
[ERROR] [ModuleLoader] Failed to load module MyModule from entry-point, skipped: 'NoneType' object has no attribute 'platform'
  → MyModule/Core.py:42 in on_load
      adapter = sdk.platform
  → AttributeError: 'NoneType' object has no attribute 'platform'
  → Hint: Increase log level to DEBUG to view full stack trace; check the implementation code of module MyModule
```

The diagnostic information is generated by the `ErisPulse.runtime.diagnostics` module and automatically filters out internal framework frames, keeping only your code frames. If you need to reuse it in custom loading logic:

```python
from ErisPulse.runtime import log_diagnostic

try:
    risky_init()
except Exception as e:
    log_diagnostic(e)  # Automatically extract user code frames and write to ERROR log
```

This module also provides two low-level functions: `extract_user_frame()` (returns structured frame information) and `format_diagnostic_block()` (returns multi-line text).

### 3. Registration Layer: register_to_manager

Register the objects produced by Loader to the manager, so that `sdk.adapter` / `sdk.module` can recognize them.

```python
# Register adapters (returns bool, indicating if all succeeded)
await adapter_loader.register_to_manager(enabled_adapters, adapter_objs, sdk.adapter)

# Register modules
await module_loader.register_to_manager(enabled_modules, module_objs, sdk.module)
```

After registration, adapters are registered to the adapter manager and modules to the module manager, but they are **not yet started/initialized**.

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

Modules require an extra step—**instantiation** and mounting to `sdk` (so you can call `sdk.MyModule.xxx`). This step also handles module dependencies and topological sorting.

```python
success = await module_loader.initialize_modules(
    enabled_modules, module_objs, sdk.module, sdk
)
```

After successful instantiation, modules appear on `sdk.<ModuleName>`.

### 6. Start Router Server

```python
await sdk.router.start(
    host="0.0.0.0",
    port=8000,
    ssl_certfile=None,
    ssl_keyfile=None,
)
```

The router server is responsible for receiving webhooks/websocket callbacks from adapters. Without starting it, server-mode adapters cannot receive messages.

## Complete Manual Startup Example

The following code is **equivalent to** the core flow of `await sdk.init()`, but each step is exposed, allowing you to insert custom logic at any step:

```python
import asyncio
from ErisPulse import sdk
from ErisPulse.loaders import AdapterLoader, ModuleLoader

async def manual_startup():
    # 0. Prepare Environment (load configuration, register global exception handler)
    #    _prepare_environment is a pre-step inside init(); manual flow must call it first,
    #    otherwise Loader won't read configuration, and all adapters/modules will be misjudged as disabled.
    if not await sdk._prepare_environment():
        print("Environment preparation failed")
        return False

    # 1. Create loaders (each internally holds a Finder)
    adapter_loader = AdapterLoader()
    module_loader = ModuleLoader()

    # 2. Parallel discovery and loading (consistent with internal use in init())
    (adapter_objs, enabled_adapters, disabled_adapters), \
    (module_objs, enabled_modules, disabled_modules) = await asyncio.gather(
        adapter_loader.load(sdk.adapter),
        module_loader.load(sdk.module),
    )

    # 3. Register adapters
    await adapter_loader.register_to_manager(
        enabled_adapters, adapter_objs, sdk.adapter
    )

    # 4. Start adapters
    if enabled_adapters:
        await sdk.adapter.startup()

    # 5. Register modules
    await module_loader.register_to_manager(
        enabled_modules, module_objs, sdk.module
    )

    # 6. Initialize modules (instantiation + mount to sdk)
    if enabled_modules:
        await module_loader.initialize_modules(
            enabled_modules, module_objs, sdk.module, sdk
        )

    # 7. Start router server
    await sdk.router.start(host="0.0.0.0", port=8000)

    print("Manual startup complete")
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

In most cases, **manual startup is not needed**; `await sdk.run()` already handles all of the above. Manual startup is only valuable in these scenarios:

- **Partial Loading**: Load only specified adapters/modules, skipping others
- **Dynamic Registration**: Register new adapters/modules at runtime based on conditions
- **Custom Order**: Need to reorder the default loading sequence (e.g., start a module before an adapter)
- **Inject Strategies**: Inject custom strict mode managers, loading strategies, etc., into Loader
- **Debugging/Diagnosis**: Manually drive at a certain step to locate issues when a failure occurs

## Runtime Fine-Grained Control

Even when using `sdk.run()` to complete the startup, you can still control subsystems individually at runtime without restarting the entire SDK:

### Hot Restart of Adapters

```python
# Hot restart an adapter (repair connection, does not affect other platforms)
await sdk.adapter.shutdown("yunhu")
await sdk.adapter.startup("yunhu")

# Bring up a new platform during runtime
await sdk.adapter.startup("telegram")

# Temporarily take down a platform
await sdk.adapter.shutdown("telegram")
```

> `adapter.startup()` requires the adapter to be **registered** to the manager. Registration happens inside `init()`/`run()`, so this is fine-grained control after startup.

### Router Server

```python
# Temporarily take down webhook server
await sdk.router.stop()

# Restart (e.g., after changing port)
await sdk.router.start(host="0.0.0.0", port=9000)
```

### Lazy Module Loading

```python
# Manually load a module (possibly lazy-loaded)
await sdk.load_module("MyModule")
```

## Graceful Shutdown

Since version 2.7.0, `sdk.shutdown()` provides **programmatic graceful shutdown**: set a shutdown event to make the main loop hanging in `await sdk.run(keep_running=True)` return, triggering `uninit()` to complete resource cleanup.

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

**Signal Handling**: `run()` internally registers `SIGTERM` / `SIGHUP` handlers, converting system signals into graceful shutdown—when container orchestration (Docker `docker stop`) or `systemd` stops the service, the process will go through `uninit()` cleanup instead of being forcefully killed.

- Windows does not support `loop.add_signal_handler`, so the signal handler is automatically skipped (still use `sdk.shutdown()` or Ctrl+C to trigger shutdown)
- Repeatedly calling `sdk.shutdown()` is safe (no operation after the event is set)

## Unload Process

The reverse operation of startup is `await sdk.uninit()`, which cleans up in the reverse order:

1. Shut down all adapters (`adapter.shutdown()`)
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

The SDK provides two restart methods, neither requiring you to manually unload first—the framework handles it:

| Method | Call | Behavior | Use Case |
|------|------|------|----------|
| Hot Restart | `await sdk.restart()` | **Code-level hot reload at the component level** within the same process: all modules go through a unified reload pipeline (global syntax pre-check / snapshot rollback / identity verification), adapters first **re-discover entry-points** (newly installed/uninstalled adapters during runtime take effect immediately) then reload code-level one by one | Hot reload after pip upgrades or installing components, hot update module code |
| Hard Restart | `await sdk.hard_restart()` | `uninit()` followed by **exit with code 42**, letting an external supervisor restart a new process | Framework self-upgrade (new framework code only takes effect in a new process), C extension side effects, suspected resource leaks |

```python
# Hot Restart: Component-level code hot reload (most common; newly installed adapters during runtime are also pulled in)
await sdk.restart()

# Hard Restart: Exit process, let external supervisor restart (see below "Supervisor Guide")
await sdk.hard_restart("sdk self-update")  # Optional reason for supervisor display
```

> **Two Notes**:
> 1. These methods execute restart in the background and **immediately return `True` to indicate "restart task scheduled"**, not "restart completed". Actual restart happens in the background, avoiding interruption of the current event chain.
> 2. The principle of `hard_restart()` is: after unloading and flushing configuration, exit the process with **exit code 42** (`HARD_RESTART_EXIT_CODE`)—**it does not start a new process itself**. It must be restarted by an external supervisor detecting exit code 42. If running directly with `python main.py` and no supervisor, the process exits with code 42 and **does not automatically restart** (the framework will warn).

> **Hot Restart Mutual Exclusion and Merging** (since 2.11.1): All hot reload operations (single module reload, full reload, adapter reload, hibernation) are mutually exclusive throughout—during a save storm, consecutive triggers will not be concurrently interleaved, and if a new request is received during an ongoing restart, it will be automatically merged, with at most one round completed afterward. When saving a file with syntax errors, the entire reload will be **rejected by a pre-check** before unloading (listing all error files and line numbers at once), and all old instances continue serving.

### When to Use Hard Restart?

Hot restart covers most scenarios (pip upgrades/installing components, hot updating module code, **including newly installed adapters during runtime**). The following scenarios require hard restart:

- **Framework Self-Upgrades**: After upgrading ErisPulse itself, the new framework code only takes effect in a new process (Python does not re-import loaded framework code).
- **Binary Library (C Extension) Side Effects**: Hot restart occurs within the same process, unable to release C extensions, open file descriptors, threads, and other process-level resources; hard restart switches to a new process, thoroughly clearing these side effects.
- **Resource Leak Diagnosis**: When suspected memory or handle leaks exist, hard restart provides a clean environment.

> The "Framework Restart" feature in the Dashboard management panel calls `hard_restart()` underneath.

### Exit Code 42 Contract

Hard restart is cross-process collaboration: **SDK handles the exit (code 42), supervisor handles the restart**.

| Role | Behavior |
|------|------|
| SDK (when hard restarted) | `uninit()` → flush configuration → write hard restart marker (reason / PID, for supervisor display) → `os._exit(42)` |
| Supervisor | Detect sub-process exit code 42 → display hard restart reason → restart the same command |

> `sdk.is_supervised()` can query whether the current process was started by a supervisor (detects environment variable `ERISPULSE_SUPERVISED`). The CLI `run` command automatically injects this marker when starting a subprocess; external supervisors like systemd / Docker do not inject it, so `is_supervised()` returns `False`, and the framework will warn "no supervisor detected" after hard restart.

### Supervisor Guide

Choose the supervisor that suits you to make hard restart truly effective:

#### 1. CLI run command (development/simple deployment, recommended)

`epsdk run main.py` includes an internal supervision loop: detects sub-process exit codes, restarts immediately if code 42 is detected (and displays the hard restart reason); other abnormal exit codes retry automatically with exponential backoff; `Ctrl+C` first gracefully terminates the sub-process (code 0 is considered normal exit, no restart).

```bash
epsdk run main.py
```

`epsdk run --reload` (development hot reload mode, since 2.11.1) also follows the "supervisor process + reload worker sub-process" structure: worker saves `.py` files to trigger **component-level hot reload** (no full framework restart); hard restart is performed by the supervisor process restarting a new worker, making the new code effective after framework upgrades.

#### 2. systemd (Linux server)

`RestartForceExitStatus=42` makes exit code 42 trigger restart (default `on-failure` only works for non-zero codes):

```ini
[Service]
ExecStart=/usr/bin/python3 /opt/mybot/main.py
Restart=on-failure
RestartForceExitStatus=42
RestartSec=2
User=mybot
```

#### 3. Docker / docker-compose

Inside the container, PID 1 is the application process; exit code 42 causes the container to exit—use `restart` policy to automatically restart it:

```yaml
services:
  bot:
    build: .
    restart: unless-stopped   # Restart on any exit (including 42)
```

#### 4. PM2 (Node ecosystem operations)

```bash
pm2 start main.py --name mybot --interpreter python3
# 42 is treated as an exit code, PM2 defaults to restart; set restart_delay to debounce
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
    time.sleep(3)           # Abnormal exit, retry with backoff
```

> **Behavior without a supervisor**: Running directly with `python main.py`, calling `hard_restart()` exits the process with code 42 and does not restart. In this case, you should integrate one of the above supervisors.



====
技术标准
====


### 会话类型标准

# ErisPulse Session Type Standard

> [!TIP]
> **When to read this**: When mapping platform-native session types to standard types (private/group/channel/guild/thread) in an adapter, or when unsure what target type to pass to `Send.To()` in a module, or to understand the automatic conversion of `event.reply()` — refer to this document. Skip it otherwise.

This document defines the session type standard supported by ErisPulse, covering receive event types and send target types.

## 1. Core Concepts

### 1.1 Receive Types && Send Types

ErisPulse distinguishes between two session types:

- **Receive Type**: The `detail_type` field of received events
- **Send Type**: The target type of the `Send.To()` method when sending messages

### 1.2 Type Mapping Relationships

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
- `private` is the receive-time type; the standard send type is `user`
- `group`, `channel`, `guild`, and `thread` use the same type for both receiving and sending
- **Recommended path**: Use `event.reply()` directly — it automatically completes type conversion and target inference, with no manual handling needed (the `private` → `user` automatic conversion happens here)
- **For manual sending**: Pass the send type directly (e.g., `Send.To("user", ...)`); manually passing a receive type such as `Send.To("private", ...)` can still be auto-converted, but is not recommended (see §6.1)

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
- **Description**: User type; some platforms (e.g., Telegram) represent private chats as user instead of private
- **ID Field**: `user_id`
- **Applicable Platforms**: Telegram and similar platforms

### 2.2 ErisPulse Extension Types

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
- **Applicable Platforms**: Discord, etc.

#### thread
- **Receive Type**: `thread`
- **Send Type**: `thread`
- **Description**: Thread/sub-channel messages, used for sub-discussion areas within a community
- **ID Field**: `thread_id`
- **Applicable Platforms**: Discord Threads, Telegram Topics, etc.

## 3. Platform Type Mapping

### 3.1 Mapping Principles

Adapters are responsible for mapping platform-native types to ErisPulse standard types:

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

# Register a custom type
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

# Get the corresponding ID
target_id = get_target_id(event, platform="MyPlatform")
# Returns: event["custom_id"]
```

### 4.3 Unregistering Custom Types

```python
from ErisPulse.Core.Event import unregister_custom_type

unregister_custom_type("my_custom_type", platform="MyPlatform")
```

## 5. Automatic Type Inference

When an event has no explicit `detail_type` field, the system automatically infers the type based on existing ID fields:

> [!NOTE]
> **2.7.0+ Behavior Change**: `detail_type` is adopted directly only when it is a **known session type** (standard or custom). The `detail_type` of notice/request events (such as `group_member_increase` and `friend_increase`) are **semantic subtypes** rather than session types, so the correct session type is instead inferred from ID fields.

### 5.1 Inference Priority

```
Priority (high to low):
1. group_id     → group
2. channel_id   → channel
3. guild_id     → guild
4. thread_id    → thread
5. user_id      → private
```

### 5.2 Usage Examples

```python
# Event has only group_id
event = {"group_id": "123", "user_id": "456"}
receive_type = infer_receive_type(event)
# Returns: "group" (group_id takes priority)

# Event has only user_id
event = {"user_id": "123"}
receive_type = infer_receive_type(event)
# Returns: "private"

# A notice event's detail_type is a semantic subtype; 2.7.0+ infers from ID fields
event = {"type": "notice", "detail_type": "group_member_increase", "group_id": "123"}
receive_type = infer_receive_type(event)
# Returns: "group" (not "group_member_increase")
```

## 6. API Usage Examples

### 6.1 Sending Messages

```python
from ErisPulse import adapter

# Send to a user
await adapter.myplatform.Send.To("user", "123").Text("Hello")

# Send to a group
await adapter.myplatform.Send.To("group", "456").Text("Hello")

# Automatic private → user conversion: manually passing a receive type is not recommended (may cause compatibility issues)
await adapter.myplatform.Send.To("private", "789").Text("Hello")
# Internally auto-converted to: Send.To("user", "789")
# Recommended practice: use the send type user directly for manual sending, or use event.reply() to complete the conversion automatically (see 6.2)
```

### 6.2 Event Reply

```python
from ErisPulse.Core.Event import Event

# Event.reply() automatically handles type conversion (recommended path)
await event.reply("Reply content")
# Internally uses the correct send type automatically (conversions like private → user happen here)
```

### 6.3 Command Handling

```python
from ErisPulse.Core.Event import command

@command(name="test")
async def handle_test(event):
    # The system automatically handles session types
    # No need to manually check whether it is group_id or user_id
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

### 7.3 One-Step Send Information Retrieval

```python
from ErisPulse.Core.Event import get_send_type_and_target_id

event = {"detail_type": "private", "user_id": "123"}
send_type, target_id = get_send_type_and_target_id(event)
# send_type = "user", target_id = "123"

# Use directly with Send.To()
await adapter.Send.To(send_type, target_id).Text("Hello")
```

### 7.4 Getting the Target ID

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
clear_custom_types(platform="discord")  # Clear only those for the specified platform
```

## 9. Best Practices

### 7.1 Adapter Developers

1. **Use standard mappings**: Map to standard types whenever possible, rather than creating new types
2. **Convert correctly**: Ensure the mapping relationship between receive and send types is correct
3. **Preserve original data**: Keep original event types in `{platform}_raw`
4. **Document it**: Describe the type mapping relationships in the adapter documentation

### 7.2 Module Developers

1. **Use utility methods**: Use utility methods such as `get_send_type_and_target_id()`
2. **Avoid hardcoding**: Do not write code like `if group_id else "private"`
3. **Consider all types**: Code should support all standard types, not just private/group
4. **Design flexibly**: Use event wrapper methods instead of accessing fields directly

### 7.3 Type Inference

- **Prefer detail_type**: If an explicit field exists, do not perform inference
- **Use inference sensibly**: Only use it when there is no explicit type
- **Mind the priority**: Understand the inference priority to avoid unexpected results

## 10. FAQ

### Q1: Why is private converted to user when sending?

A: This is required by the OneBot12 standard. `private` is a receive-time concept; `user` is more semantically appropriate when sending.

### Q2: How do I support new session types?

A: Register custom types via `register_custom_type()`, or directly use standard types such as `channel` and `guild`.

### Q3: What if an event has no detail_type?

A: The system automatically infers it based on existing ID fields. Priority: group > channel > guild > thread > user.

### Q4: How should adapters map Telegram supergroup?

A: In the adapter's conversion logic, map `supergroup` to the standard `group` type.

### Q5: How are special platforms like email handled?

A: For non-universal or platform-specific types, use `{platform}_raw` and `{platform}_raw_type` to preserve the original data, and let the adapter handle them itself.

## 11. Related Documentation

**Adapter side (mapping and conversion)**:
- [Event Conversion Standard](event-conversion.md) - Complete event conversion specification
- [Send Method Specification](send-method-spec.md) - Send class method naming and parameter specifications
- [Adapter Development Guide](../developer-guide/adapters/) - Complete guide to adapter development

**Module side (avoiding manual type conversion)**:
- Use `event.reply()` to automatically complete type conversion and target inference; see [Event Wrapper Class Explained](../developer-guide/modules/event-wrapper.md) for details



### 事件转换标准

# Adapter Standardization Conversion Specification

> [!TIP]
> **When to read this**: When you are converting platform-native events to OneBot12 standard events in an adapter—use this document as a reference for verifying required fields, message segment structure, extension field naming (the `{platform}_` prefix), and session type inference. Otherwise, skip it.

## 1. Core Principles

1. Strict Compatibility: All standard fields must fully comply with the OneBot12 specification.
2. Explicit Extension: Platform-specific features must be prefixed with `{platform}_` (e.g., `yunhu_form`).
3. Data Integrity: Original event data must be preserved in the `{platform}_raw` field, and the original event type must be preserved in the `{platform}_raw_type` field.
4. Time Standardization: All timestamps must be converted to 10-digit Unix timestamps (seconds precision).
5. Platform Consistency: The `platform` field name must match the name/alias you registered for in ErisPulse.

## 2. Standard Field Requirements

### 2.1 Mandatory Fields

| Field | Type | Description |
|-------|------|-------------|
| id | string | Unique event identifier |
| time | integer | Unix timestamp (seconds precision) |
| type | string | Event type |
| detail_type | string | Event detail type (see [Session Type Standard](session-types.md)) |
| platform | string | Platform name |
| self | object | Bot self information |
| self.platform | string | Platform name |
| self.user_id | string | Bot user ID |

**detail_type Specification**:
- Must use ErisPulse standard session types (see [Session Type Standard](session-types.md)).
- Supported types: `private`, `group`, `user`, `channel`, `guild`, `thread`.
- The adapter is responsible for mapping native platform types to standard types.

### 2.2 Message Event Fields

| Field | Type | Description |
|-------|------|-------------|
| message | array | Message segment array |
| alt_message | string | Alternate message text |
| user_id | string | User ID |
| user_nickname | string | User nickname (optional) |

### 2.3 Notice Event Fields

| Field | Type | Description |
|-------|------|-------------|
| user_id | string | User ID |
| user_nickname | string | User nickname (optional) |
| operator_id | string | Operator ID (optional) |

### 2.4 Request Event Fields

| Field | Type | Description |
|-------|------|-------------|
| user_id | string | User ID |
| user_nickname | string | User nickname (optional) |
| comment | string | Request comment (optional) |
| request_id | string | Request identifier (strongly recommended, used for approve/reject request operations) |

**`request_id` Field Explanation**:
- `request_id` is the unique operation identifier for request events, used to execute approve/reject operations via the `HandleRequest` DSL.
- The adapter, when converting request events, should map the native platform request identifier to this field.
- If the platform does not have a request ID, the adapter should generate a unique identifier (e.g., based on a hash of timestamp + user ID).
- When `request_id` is missing, `event.approve()` / `event.reject()` will raise a `ValueError`.

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

### 4.1 Standard Message Segments

Standard message segments **do not** require a platform prefix.

| Type | Description | data fields |
|------|-------------|-------------|
| `text` | Plain text | `text: str` |
| `image` | Image | `file`, `url: str` |
| `audio` | Audio | `file`, `url: str` |
| `video` | Video | `file`, `url: str` |
| `file` | File | `file`, `url: str`, `filename: str` |
| `mention` | @User | `user_id: str`, `user_name: str` |
| `reply` | Reply | `message_id: str` |
| `face` | Emoji | `id: str` |
| `location` | Location | `latitude: float`, `longitude: float` |
| `keyboard` | Button/Inline Keyboard | `rows: list[list[button]]` (see 4.1.1) |

**Media Segment `file` Field Format** (send direction, `image` / `audio` / `video` / `file` generic):

| Form | Example | Adapter Requirement |
|------|---------|---------------------|
| HTTP(S) URL | `https://example.com/a.png` | **Must** accept |
| Local File Path | `/tmp/a.png`, `C:\tmp\a.png` | **Must** accept |
| Binary Data | `bytes` | **Must** accept |
| `file://` URI / Base64 / Data URI | `file:///tmp/a.png`, `data:image/png;base64,...` | **Should** accept |

> Complete media sending protocol (form determination order, filename derivation, capability degradation ladder) see
> [Sending Method Specification §2.1](send-method-spec.md#21-media-message-sending-protocolimage--voice--video--file).

**Field Direction Semantics**:

- `file`: **Send direction** content source (above forms); **Receive direction** filled by adapter with platform retrievable forms
  (usually downloadable URL, or resource identifiers usable by `get_file`-type actions)
- `url`: **Receive direction** platform backlink (adapter should fill as much as possible when converting platform events, for modules to directly use); **Send direction** can be left blank
- `filename`: `file` segment filename (send direction optional, default to adapter generating by
  [Sending Method Specification §2.1.3](send-method-spec.md) derivation order; receive direction **should** fill platform original filename)

```json
{
  "type": "text",
  "data": {
    "text": "Hello World"
  }
}
```

### 4.1.1 keyboard Button/Inline Keyboard Segment (Cross-Platform Universal)

Buttons/inline keyboards exist in multiple platforms (Telegram / Yunhu / QQBot / Kook / Discord), and are a **cross-platform universal concept**, thus as a standard message segment (no platform prefix). Adapters should convert standard segments to platform-native structures; platform-native extension segments (e.g., `telegram_inline_keyboard`) continue to be retained and passed through.

```json
{
  "type": "keyboard",
  "data": {
    "rows": [
      [
        {"label": "Option A", "type": "callback", "data": "vote:A"},
        {"label": "Official Site", "type": "link", "data": "https://example.com"}
      ]
    ]
  }
}
```

**Field Explanation**:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `rows` | 2D array | Yes | Each sub-array is a row of buttons |
| `rows[][].label` | str | Yes | Button display text |
| `rows[][].type` | str | Yes | `callback` (click back data) / `link` (jump to URL) |
| `rows[][].data` | str | Yes | Callback data (type=callback) or jump address (type=link) |
| `rows[][].*` | Any | No | Platform-specific optional fields (e.g., `web_app`, `menus`), adapter maps or ignores as capability allows |

**Adapter Conversion Reference** (full mapping and interaction callback event standard see [Cross-Platform Interaction Component Standard](standardization-guide.md)):

| Platform | Standard Segment → Platform Native |
|----------|------------------------------------|
| Telegram | `inline_keyboard`: `[{text, callback_data \| url}]` |
| Yunhu | `buttons`: `[{label, action_type: 2=callback \| 1=jump, ...}]` |
| QQBot | `keyboard.content.rows`: `[{label, type: 2=callback \| 0=jump, data}]` (requires markdown-type message) |
| Kook | Card action-group module |
| Discord | components: `action_row` + `buttons` (custom_id/url) |

### 4.2 Platform Extension Message Segments

Platform-specific message segments must be prefixed with the platform name:

```json
// Yunhu - Form
{"type": "yunhu_form", "data": {"form_id": "123456", "form_name": "Registration Form"}}

// Telegram - Sticker
{"type": "telegram_sticker", "data": {"file_id": "CAACAgIAAxkBAA...", "emoji": "😂"}}
```

**Extension Message Segment Requirements**:
1. **No prefix in `data` internal fields**: `{"type": "yunhu_form", "data": {"form_id": "..."}}` instead of `{"type": "yunhu_form", "data": {"yunhu_form_id": "..."}}`
2. **Provide fallback solutions**: Modules may not recognize extension message segments, adapters should provide text alternatives in `alt_message`
3. **Complete documentation**: Each extension message segment must be documented in the adapter documentation, specifying `type`, `data` structure, and usage scenarios

## 5. Handling Unknown Events

For events that cannot be recognized, a warning event should be generated:
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
────────────────── ───────────────────── ─────────────────────
yunhu              command               yunhu_command
telegram           sticker_file_id       telegram_sticker_file_id
onebot11           anonymous             onebot11_anonymous
email              subject               email_subject
```

**Requirements**:
- `platform` must exactly match the platform name registered in the adapter (case-sensitive)
- `field_name` uses `snake_case` naming
- Double underscores `__` are prohibited (reserved for Python)
- No field name should conflict with standard fields (e.g., `type`, `time`, `message`, etc.)

### 6.2 Message Segment Type Naming

**Rule**: `{platform}_{segment_type}`

Standard message segment types (`text`, `image`, `audio`, `video`, `mention`, `reply`, etc.) **must not** have a platform prefix. Only platform-specific message segment types require a prefix.

### 6.3 Raw Data Field Naming

The following field names are **reserved fields** that all adapters must follow:

| Reserved Field | Type | Description |
|----------------|------|-------------|
| `{platform}_raw` | `any` | A deep copy of the raw event data from the platform |
| `{platform}_raw_type` | `string` | The raw event type identifier from the platform |

**Requirements**:
- `{platform}_raw` must be a deep copy of the raw data, not a reference
- `{platform}_raw_type` must be a string, even if the platform uses a numeric type, it must be converted to a string
- These two fields must be present in all events (if unavailable, use `null` and empty string `""`)

### 6.4 Examples of Platform-Specific Fields

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
- The top-level key must have a platform prefix
- Nested internal fields **do not** have platform prefixes
- Nesting depth should not exceed 3 levels

### 6.6 Extension of `self` Field

The standard required fields of the `self` object (`platform`, `user_id`) are listed in §2.1. The following are ErisPulse extensions for optional fields:

| Field | Type | Description |
|-------|------|-------------|
| `self.user_name` | `string` | Bot nickname |
| `self.avatar` | `string` | Bot avatar URL |
| `self.account_id` | `string` | Account identifier in multi-account mode |

> **Bot Status Tracking**: Adapters inform the framework of the bot's connection status by sending `type: "meta"` events. Supported `detail_type`: `connect` (online), `heartbeat` (heartbeat), `disconnect` (offline). The system automatically extracts bot metadata from the `self` field in these events for status tracking. Additionally, the `self` field in regular events is also automatically detected as the bot. See [Adapter System API - Bot Status Management](../api-reference/adapter-system.md).

---

## 7. Session Type Extension

ErisPulse extends the OneBot12 standard `private`, `group` with the following session types:

| Type | OneBot12 Standard | ErisPulse Extension | Description |
|------|:-----------------:|:-------------------:|-------------|
| `private` | ✅ | — | One-on-one private chat |
| `group` | ✅ | — | Group chat |
| `user` | — | ✅ | User type (Telegram, etc.) |
| `channel` | — | ✅ | Channel (broadcast-style) |
| `guild` | — | ✅ | Server/community |
| `thread` | — | ✅ | Topic/sub-channel |

**Adapter Custom Type Extension**:

```python
from ErisPulse.Core.Event.session_type import register_custom_type

# Register in adapter startup
register_custom_type(
    receive_type="email",      # detail_type in receive events
    send_type="email",         # target type when sending
    id_field="email_id",       # corresponding ID field name
    platform="email"           # platform identifier
)
```

**Custom Type Requirements**:
- Must be registered in the adapter `start()` and unregistered in `shutdown()`
- `receive_type` should not conflict with standard types
- `id_field` should follow the `{target}_id` naming pattern

> Full session type definition and mapping relationship see [Session Type Standard](session-types.md).

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

    # Access platform extension fields - Method 2: Dot-style access (Event wrapper class)
    # event.yunhu_command

    # Access raw data
    raw_data = event.get("yunhu_raw")
    raw_type = event.get_raw_type()

    # Platform judgment
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

1. **Prefer standard fields**: Do not assume extension fields will always exist
2. **Platform judgment**: Use `event.get_platform()` to determine the platform, not by checking the existence of extension fields
3. **Graceful degradation**: Use `alt_message` as a fallback when unable to handle extension message segments
4. **Do not hardcode prefixes**: Use `platform` variable to dynamically construct

```python
# ✅ Recommended
platform = event.get_platform()
raw_data = event.get(f"{platform}_raw")

# ❌ Not recommended
raw_data = event.get("yunhu_raw")
```

### 8.4 Request Event Handling

Module developers can use `event.approve()` and `event.reject()` to handle request events:

```python
from ErisPulse.Core.Event import request

# Friend request: Automatically approve
@request.on_friend_request()
async def handle_friend_request(event):
    user_name = event.get_user_nickname() or event.get_user_id()
    comment = event.get_comment()
    
    # Approve request
    result = await event.approve()
    if result.get("status") == "ok":
        print(f"Approved friend request from {user_name}")
    else:
        print(f"Failed to approve friend request: {result.get('message')}")

# Group request: Decide based on conditions
@request.on_group_request()
async def handle_group_request(event):
    comment = event.get_comment()
    
    # Reject request
    result = await event.reject(comment="Not joining new group for now")
```

**Direct operation via adapter** (for non-event handler scenarios):

```python
from ErisPulse import adapter

# Directly operate via request_id
await adapter.myplatform.Request("req_abc123").accept()
await adapter.myplatform.Request("req_abc123").reject()

# Specify bot account for operation
await adapter.myplatform.Request("req_abc123").Using("bot1").accept()

# With comment
await adapter.myplatform.Request("req_abc123").accept(comment="Welcome")
```

---

## 9. Session Type Inference for notice / request Events

### 9.1 Problem Background

The `detail_type` of `notice` events and `request` events are **semantic subtypes** (e.g., `group_member_increase`, `friend_increase`), not session types (e.g., `group`, `private`).

```
type        detail_type                  Meaning            Session Type
────        ───────────                  ────            ────────
message     group                        Group message         group (detail_type is session type)
message     private                      Private message       private (detail_type is session type)
notice      group_member_increase        Group member increase group (inferred from group_id)
notice      friend_increase              Friend increase       private (inferred from user_id)
request     friend                       Friend request        private (inferred from user_id)
request     group                        Group request         group (detail_type is session type)
```

### 9.2 Inference Rules

The inference order of `infer_receive_type()`:

1. If `detail_type` is a known session type (`private`/`group`/`channel`/`guild`/`thread`/`user`), use it directly.
2. If `detail_type` is a custom session type, use it directly.
3. Otherwise (for semantic subtypes of notice/request), infer from ID fields:
   - If `group_id` exists → `"group"`
   - If `channel_id` exists → `"channel"`
   - If `guild_id` exists → `"guild"`
   - If `thread_id` exists → `"thread"`
   - If `user_id` exists → `"private"`

### 9.3 `event.reply()` Target Inference

The sending target of `event.reply()` in notice/request events is determined by the inferred session type:

- Group notice events (with `group_id`) → reply to the **group**
- Friend notice events (with only `user_id`) → reply to the **private user**

```python
from ErisPulse.Core.Event import notice

@notice.on_group_increase()
async def handle_welcome(event):
    group_id = event.get("group_id")    # "group_789"
    user_id = event.get("user_id")      # "user_456"

    # event.reply() sends to group (group/group_789)
    await event.reply("Welcome to the group!")

    # To notify admin (private chat), specify target explicitly:
    await adapter.Send.To("user", "admin_id").Text(f"New member {user_id} joined {group_id}")
```

### 9.4 Adapter Development Recommendations

Ensure `notice`/`request` events contain correct ID fields:

| detail_type | Required ID Fields | Inferred Session Type |
|-------------|-------------------|-----------------------|
| `group_member_increase` | `group_id` + `user_id` | `group` |
| `group_member_decrease` | `group_id` + `user_id` | `group` |
| `friend_increase` | `user_id` | `private` |
| `friend_decrease` | `user_id` | `private` |
| `friend` (request) | `user_id` | `private` |
| `group` (request) | `group_id` | `group` |

---

## 10. Related Documentation

**Companion reference when implementing converters**:
- [Session Types Standard](session-types.md) - Session type definitions and mapping relationships
- [API Response Standard](api-response.md) - Adapter API response format standard

**Sending side of the same adapter**:
- [Send Method Specification](send-method-spec.md) - Method naming, parameter specifications for Send-type methods, and reverse conversion requirements
- [API Action Standard](api-action-spec.md) - Unified interface for OneBot12 standard API actions

**Look up known extended events and message segments for each platform**:
- [Platform Features Documentation](../platform-guide/README.md) - You can visit this documentation to learn about the features of each platform, as well as known extended events and message segments.



### API 响应标准

# ErisPulse Adapter Standardized Return Specification

> [!TIP]
> **When to read this**: When you are implementing the return values of `call_api` / Send / Request in an adapter and need to confirm that the response structure and return codes conform to the ErisPulse standard, or when troubleshooting the meaning of a particular `retcode`, refer to this document. Skip if not needed.

## 1. Description

Why does this specification exist?

To ensure the uniformity of API response formats across different platforms and maintain compatibility with OneBot12, the ErisPulse adapter adopts the message sending return structure standard defined by OneBot12.

However, the ErisPulse protocol has some special definitions:
- 1. In the base fields, `message_id` is required, but this field does not exist in the OneBot12 standard.
- 2. The response content needs to include a `{platform_name}_raw` field to store the raw response data.

## 2. Basic Return Structure

All action responses must include the following basic fields:

| Field Name | Data Type | Required | Description |
|-----------|-----------|----------|-------------|
| status | string | Yes | Execution status, must be "ok" or "failed" |
| retcode | int64 | Yes | Return code, follows OneBot12 return code rules |
| data | any | Yes | Response data, contains the request result on success, null on failure |
| message_id | string | Yes | Message ID, used to identify the message, empty string if not available |
| message | string | Yes | Error message, empty string on success |
| {platform_name}_raw | any | No | Raw response data |

Optional fields:
| Field Name | Data Type | Required | Description |
|-----------|-----------|----------|-------------|
| echo | string | No | Returned verbatim when the request contains an echo field |

## 3. Full Field Specification

### 3.1 Common Fields

#### Successful Response Example
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

#### Failed Response Example
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
|------------|------------|-------------|
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
|------------|------------|-------------|
| 20001 | Bad Handler | Action handler implementation error |
| 20002 | Internal Handler Error | Exception thrown during action handler execution |

#### 3xxxx Execution Error
| Error Code Range | Error Type | Description |
|------------------|------------|-------------|
| 31xxx | Database Error | Database error |
| 32xxx | Filesystem Error | Filesystem error |
| 33xxx | Network Error | Network error |
| 34xxx | Platform Error | Robot platform error |
| 35xxx | Logic Error | Action logic error |
| 36xxx | I Am Tired | Implementation decided to strike |

#### Reserved Error Ranges
- 4xxxx, 5xxxx: Reserved ranges, should not be used
- 6xxxx–9xxxx: Other error ranges, for custom implementation use

## 4. Implementation Requirements
1. All responses must contain the fields: `status`, `retcode`, `data`, and `message`.
2. When the request contains a non-empty `echo` field, the response must include an `echo` field with the same value.
3. Return codes must strictly follow the OneBot12 specification.
4. Error messages (`message`) should be human-readable descriptions.

## 5. Extension Specifications

ErisPulse extends the OneBot12 standard return structure as follows:

### 5.1 `message_id` Required Field

In the OneBot12 standard, `message_id` is located within the `data` object and is not mandatory. ErisPulse elevates it to a **required** top-level field:

- When `message_id` cannot be obtained, it should be set as an empty string `""`
- Ensure `message_id` always exists, so modules do not need to perform null checks

### 5.2 `{platform}_raw` Raw Response Field

The return value should include the `{platform}_raw` field, which stores a complete copy of the raw response data from the platform:

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

The OneBot12 specification allows implementations to define custom low three digits of `3xxxx`. The `34xxx` segment semantics are **Platform Error** (robot platform error, such as failures caused by platform restrictions). The `34xxx` segment is used hierarchically according to responsibilities:

| Low Three Digits Segment | Ownership | Purpose |
|---------|------|------|
| `340xx` | Adapter Implementation | Request operation group (Request Not Found / Already Handled / Not Supported / Permission Denied, see request-action-spec §7) |
| `341xx`～`345xx` | Adapter Implementation | Platform-side permission / risk control / account restriction errors (implement custom low three digits, original error placed in `{platform}_raw`) |
| `346xx` | **ErisPulse Framework (reserved)** | Framework-level interception and general failures; adapters/modules should not occupy these codes |
| `347xx`～`349xx` | Adapter Implementation | Other platform execution errors |

ErisPulse framework currently uses the `346xx` codes:

| Error Code | Error Name | Description |
|-------|-------|------|
| 34600 | SDK Failure | General failure in the framework (`make_error()` default return code) |
| 34601 | Action Denied | Outbound action denied by scope (`scope.actions`), call not initiated, directly return this response |

> Responsibility distinction: `34601` is **framework-level interception before the call** (the module has no right to initiate the action); `34004` / `34xxx` platform codes are **actions already sent but rejected by the platform** (e.g., Bot lacks permission, is restricted). When modules check for permission issues, they should check both types: first check `34601` (the module's own scope is disabled), then check `34xxx` (platform-side restrictions).

The return structure is the standard failure response as defined in §2:

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
- [ ] `message_id` always exists (set as empty string if unavailable)
- [ ] `{platform}_raw` contains the raw response data from the platform

## 6. Notes
- For error codes starting with 3xxxx, the last three digits can be defined by the implementation.
- Avoid using reserved error ranges (4xxxx, 5xxxx).
- **`34600` / `34601` are reserved error codes for the ErisPulse framework** (see §5.3); adapters/modules should avoid using them.
- Error messages should be concise and clear for easier debugging.



### 发送方法规范

# ErisPulse Send Method Specification

> [!TIP]
> **When to read this**: When implementing the `Send` class in your adapter—refer to this document for method naming, media parameter (URL/path/bytes) support, `Raw_ob12` reverse conversion, and merge forwarding capabilities. Skip if not needed.

This document defines the naming, parameter, and reverse conversion requirements for send methods in ErisPulse adapters.

## 0. Keyword Definitions

The terms **must (MUST)**, **should (SHOULD)**, and **may (MAY)** in this document are interpreted as follows (referencing RFC 2119):

| Keyword | Meaning | Consequence of Violation |
|--------|------|---------|
| **Must** | Mandatory requirement; framework behavior/cross-platform consistency depends on it | Adapter is considered non-compliant; module code may not work |
| **Should** | Strongly recommended; follow unless there is a compelling reason | If deviated, the adapter documentation must explain the reason and alternative behavior |
| **May** | Optional; decide based on platform capability | None |

## 1. Standard Method Naming

All send methods use **PascalCase** (capitalized first letter).

### 1.1 Standard Send Methods

| Method Name | Description | Parameter Type | Implementation Requirement |
|-------|------|---------|---------|
| `Text` | Send text message | `str` | Must |
| `Image` | Send image | `str` \| `bytes` | Must (built-in in base class; see §6.4) |
| `Voice` | Send voice | `str` \| `bytes` | Must (built-in in base class; if platform does not support voice, follow §2.1.5) |
| `Video` | Send video | `str` \| `bytes` | Must (built-in in base class; if platform does not support video, follow §2.1.5) |
| `File` | Send file | `str` \| `bytes`, `filename: str \| None = None` | Must (built-in in base class) |
| `At` | @ user/group | `str` (user_id) | Modifier method, optional |
| `Face` | Send emoji | `str` (emoji) | May |
| `Reply` | Reply to message | `str` (message_id) | Modifier method, optional |
| `Forward` | Forward message | `str` (message_id) | May |
| `Markdown` | Send Markdown message | `str` | May |
| `HTML` | Send HTML message | `str` | May |
| `Card` | Send card message | `dict` | May |

> Standard methods (`Text`/`Image`/`Voice`/`Video`/`File`) are built into the base class `SendDSL` and default to delegating to `Raw_ob12`. Adapters **do not need to re-implement** these methods to obtain type signatures; only override individual methods when the platform requires special logic (see §6.4).

### 1.2 Chained Modifier Methods

| Method Name | Description | Parameter Type |
|-------|------|---------|
| `At` | @ user (can be called multiple times) | `str` (user_id) |
| `AtAll` | @ all members | None |
| `Reply` | Reply to message | `str` (message_id) |

### 1.3 Protocol Methods

| Method Name | Description | Required? |
|-------|------|---------|
| `Raw_ob12` | Send OneBot12 format message segment | Must |

**`Raw_ob12` is a required method**. This is one of the adapter's core responsibilities: receiving OneBot12 standard message segments and converting them into native platform API calls. `Raw_ob12` serves as the unified entry point for reverse conversion (OneBot12 → platform), ensuring modules can send messages using standard message segments without relying on platform-specific methods.

**Behavior when `Raw_ob12` is not overridden**: The default base class implementation will log an **error-level** message and return a standard error response format (`status: "failed"`, `retcode: 10002`), indicating that the adapter developer must implement this method.

### 1.4 Recommended Extension Naming Convention

If adapters need to support sending non-OneBot12 format raw data (such as platform-specific JSON, XML, etc.), the following naming convention is recommended:

| Recommended Method Name | Description |
|-----------|------|
| `Raw_json` | Send arbitrary JSON data |
| `Raw_xml` | Send arbitrary XML data |

**Note**: These methods are **not** default methods provided by the base class, nor are they mandatory to implement. They are only naming conventions, and adapters can define them as needed. If an adapter does not support these formats, it does not need to define them.

**MessageBuilder**: ErisPulse provides the `MessageBuilder` utility class for easily constructing OneBot12 message segment lists, which can be used in conjunction with `Raw_ob12`. See [MessageBuilder Detailed Explanation](../advanced/message-builder.md).

## 2. Parameter Specification Details

### 2.1 Media Message Sending Protocol (`Image` / `Voice` / `Video` / `File`)

This section is the **unified protocol standard** for media sending: modules can use the same code to call the four media methods, and adapters are responsible for converting the various forms of the `file` parameter into native platform upload/send behavior.

#### 2.1.1 Valid Forms of the `file` Parameter

| Form | Example | Adapter Requirement |
|------|------|-----------|
| HTTP(S) URL | `https://example.com/image.jpg` | **Must** accept |
| Local file path | `/path/to/file.jpg`, `C:\path\to\file.jpg` | **Must** accept |
| Binary data | `b"\x89PNG..."` | **Must** accept |
| `file://` URI | `file:///path/to/file.jpg` | **Should** accept (can be forwarded as a local path) |
| Base64 string / Data URI | `iVBORw0KGgo=...`, `data:image/png;base64,...` | **Should** accept (compatible with OneBot12 ecosystem conventions) |

> Adapters **must** behave consistently across the three required forms—modules receive the same message regardless of whether they pass a URL, path, or bytes. If the platform cannot directly use a certain form (e.g., the platform API does not support referencing external URLs), the adapter should download/read and then upload, **not** require the module to retry with a different form.

#### 2.1.2 Form Determination Order

When implementing media parameter handling, adapters **should** determine the form in the following order:

1. `bytes` type → upload directly
2. String starting with `http://` / `https://` → handle as URL (direct reference or download and upload, depending on platform capability)
3. String starting with `file://` → strip prefix and handle as local path
4. Other strings → handle as local path (read and upload if exists; return standard error response if does not exist)

```python
def _resolve_media(self, file: "str | bytes") -> bytes:
    """Form determination and normalization (example)"""
    if isinstance(file, (bytes, bytearray)):
        return bytes(file)
    if file.startswith(("http://", "https://")):
        return self._download(file)          # download if platform cannot reference URL
    if file.startswith("file://"):
        file = file[len("file://"):]
    with open(file, "rb") as f:              # local path
        return f.read()
```

#### 2.1.3 File Name Semantics for `File`

`File` method signature: `File(file, filename=None)` (where `filename` is optional; built-in in base class).

File name **derivation order** (when adapter generates file name without explicit `filename`):

1. Explicit `filename` parameter (highest priority)
2. URL's basename (e.g., `https://host/a/b/report.pdf` → `report.pdf`, query string stripped)
3. Local path's basename (e.g., `/tmp/data/backup.zip` → `backup.zip`)
4. Platform default generation (e.g., `file_{timestamp}`; **should** retain real extension—extension affects platform-side type recognition and preview behavior)

> `Image` / `Voice` / `Video` can also accept `filename` (passed via message segment `data.filename`), but only `File`'s file name has cross-platform semantic guarantees.

#### 2.1.4 Declaration Obligation for Platform Restrictions

Platforms have different constraints on media size, format (MIME), duration (audio/video), etc. Adapters **should**:

- Declare supported media types and limits in the adapter documentation
- Return **standard error response** for over-limit or unsupported input (`status: "failed"`; `retcode` uses `10002` or platform-specific error code, `message` explains the reason), **not** throw an exception to interrupt module logic

#### 2.1.5 Capability Degradation Steps

When a platform does not support a certain media **type**, follow the following degradation steps (in line with the "capability degradation without error" principle):

| Scenario | Degradation Behavior |
|------|---------|
| `Voice` does not support voice messages | **Should** send as `File` (or platform-adjacent form); if cannot express, return `retcode=10002` |
| `Video` does not support video messages | Same as above |
| Media type completely unsupported (no file capability) | Return `retcode=10002`, `message` indicates unsupported data type |
| Form not supported (e.g., cannot handle base64) | Return `retcode=10002`, **can** in `message` prompt module to use URL/bytes |

**Prohibited actions**: Silent discard (no return), throw an exception, or require module to write platform-specific handling.

### 2.2 @ User Parameter Specification

**Method:** `At` (modifier method)

**Parameter:** `user_id` (`str`)

**Requirements:**
- `user_id` should be a string-type user identifier
- The `user_id` format may differ across platforms (numbers, UUIDs, strings, etc.)
- The adapter is responsible for converting `user_id` into the platform-specific format
- Note that the actual send method call should be placed at the last position.

**Example:**
```python
# Single @ user
Send.To("group", "g123").At("123456").Text("Hello")

# Multiple @ users (chained call)
send.To("group", "g123").At("123456").At("789012").Text("Hello everyone")
```

### 2.3 Reply Message Parameter Specification

**Method:** `Reply` (modifier method)

**Parameter:** `message_id` (`str`)

**Requirements:**
- `message_id` should be a string-type message identifier
- Should be the ID of a previously received message
- Some platforms may not support the reply function; adapters should degrade gracefully

**Example:**
```python
send.To("group", "g123").Reply("msg_123456").Text("Received")
```

### 2.4 Merge Forward Capability (`MergeForward`, Optional)

`MergeForward(nodes)` is an **optional capability method**: it packages multiple contents into a "merged forward / rich text collapse" form for sending, with the adapter deciding the best presentation based on platform capability. This differs semantically from `Forward(from_chat_id, message_id)` (forwarding **existing** messages) in §1.1; both coexist.

> **Standard Background**: The OneBot12 core standard does not have a node message segment or a merged forward API—"message node" is a concept implemented at the OneBot v11 ecosystem level (go-cqhttp extension), and v12 has delegated such platform-specific capabilities to the extension mechanism. ErisPulse's landing approach is equivalent to the extension mechanism: **no new standard message segments are added, but optional capability methods + `list_sends` runtime detection**—adapters that implement `MergeForward` automatically gain capability, and those that do not implement it automatically fall back to plain text, with zero module modifications.

**Method Signature:**

```python
def MergeForward(self, nodes: List[Dict]) -> asyncio.Task:
    """
    Send merged forward / rich text collapse message

    :param nodes: List of merged forward nodes (go-cqhttp extension's OneBot v11 node format):
        [
            {
                "type": "node",
                "data": {
                    "user_id": "10000",     # Displayed sender ID
                    "nickname": "MyBot",     # Displayed sender nickname
                    "content": [            # List of message segments, currently text segments
                        {"type": "text", "data": {"text": "【1/3】Title\nBody…"}}
                    ],
                },
            },
        ]
    :return: asyncio.Task, await to return standard response format
    """
```

**Implementation Requirements:**

1. **Platform has native merged forward** (OneBot11 system): **Must** call the dedicated protocol endpoint (`send_group_forward_msg` / `send_private_forward_msg`)—NapCat implementations will reject `send_msg` carrying node segments (retcode 1400); if the dedicated endpoint fails, **can** fall back to `send_msg` sending node segments directly
2. **Platform has no native forward but has rich text** (Yunhu / Telegram / Kook / Discord / Matrix, etc.): **Should** render nodes into the platform's rich text collapse form (HTML collapse card / Card / Embed / blockquote list), refer to style and adapter-specific task list in `SDK/Adapter/ADAPTER_FORWARD_GUIDE.md`
3. **Neither exists**: **Should not** implement this method (and must not return success while sending node dictionaries as plain text)—if not implemented, `list_sends` does not contain `MergeForward`, and the caller automatically falls back to plain text
4. **Failure semantics**: Return standard error response (`status: "failed"`) or throw an exception is acceptable; the caller will fall back to plain text sending, and content is not lost
5. **Should not** call `Raw_ob12` to send the same nodes inside `MergeForward` (OneBot11's `Raw_ob12` has built-in automatic routing of pure node segments, which would cause a loop)
6. **Outbound node segment parsing** (universal adapter convention): Each adapter's `Raw_ob12` segment distribution should register `node` segments—pure node lists are automatically routed to the adapter's merged forward presentation (platforms with `MergeForward` are equivalent to direct calls; platforms without this method extract each node's text to output "nickname: body" line by line in original form); text from node segments in mixed lists is merged into the body.
   Any adapter receiving a node segment must not silently discard it.

**Platform Implementation Forms** (see `SDK/Adapter/ADAPTER_FORWARD_GUIDE.md`):

- Native endpoint: OneBot11, SnowLuma (three-tiered fallback: `send_group/private_forward_msg` dedicated endpoint → `upload_forward_msg` to get resid and send forward segment → send node segments directly; SnowLuma API aligns fully with NapCat, adapters can directly connect to NapCat backend)
- Folded HTML `<details>` card: Yunhu (bot/user protocol), Email, Sandbox, Allons(Ideaura)
- Whitelisted HTML / quote block: Telegram (`<b>`+`<blockquote>`), Matrix (blockquote variant, whitelisted stripping of details/internal styles)
- Platform card: Kook (Card header+section), Discord (Embed fields)
- Official Markdown quote list: QQBot (official md has no collapse syntax, server-side validation rejects invalid tags 40034011)
- Not implemented (node segments output as original text for degradation): OneBot12 (standard has no node segments), WeCom, Terminal, Webhook, WechatMp

**Caller Detection Example:**

```python
sends = adapter.list_sends(platform)
if "MergeForward" in sends:
    await adapter.Send.To("group", "123").MergeForward(nodes)
else:
    await adapter.Send.To("group", "123").Text(plain_text)
```

> Reference Implementation: `ErisPulse-OneBot11Adapter` (dedicated endpoint → `send_msg` fallback); rendering templates and adapter-specific task lists are in `SDK/Adapter/ADAPTER_FORWARD_GUIDE.md`.

## 3. Platform-Specific Method Naming

**Not recommended** to directly add platform-prefixed methods in the `Send` class. Use generic method names or `Raw_{protocol}` methods.

**Not recommended:**
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
- Method names use PascalCase, no platform prefix
- Must return an `asyncio.Task` object
- Must provide complete type annotations and docstrings
- Parameter design should be as consistent as possible with standard method styles

## 4. Parameter Naming Convention

| Parameter Name | Description | Type |
|-------|------|------|
| `text` | Text content | `str` |
| `file` | Media content (URL/path/bytes, see §2.1.1) | `str` / `bytes` |
| `filename` | File name (`File` optional, see §2.1.3) | `str` / `None` |
| `user_id` | User ID | `str` / `int` |
| `group_id` | Group ID | `str` / `int` |
| `message_id` | Message ID | `str` |
| `data` | Data object (e.g., card data) | `dict` |

## 5. Return Value Convention

- **Send methods** (e.g., `Text`, `Image`): Must return an `asyncio.Task` object
- **Modifier methods** (e.g., `At`, `Reply`, `AtAll`): Must return `self` to support chained calls

---

## 6. Reverse Conversion Convention (OneBot12 → Platform)

Adapters must not only convert platform-native events into OneBot12 format (forward conversion), but also **must** provide the ability to convert OneBot12 message segments back into platform-native API calls (reverse conversion). The unified entry point for reverse conversion is the `Raw_ob12` method.

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
(Containing {platform}_raw)             (Return Standard Response Format)
```

**Core Symmetry**: Forward conversion retains original data in `{platform}_raw`, and reverse conversion accepts OneBot12 standard format and restores it into a platform call.

### 6.2 `Raw_ob12` Implementation Convention

`Raw_ob12` receives OneBot12 standard message segment lists and must convert them into platform-native API calls.

**Method Signature**:

```python
def Raw_ob12(self, message_segments: List[Dict]) -> asyncio.Task:
    """
    Send OneBot12 Standard Message Segments

    :param message_segments: List of OneBot12 message segments
        [
            {"type": "text", "data": {"text": "Hello"}},
            {"type": "image", "data": {"file": "https://..."}},
            {"type": "mention", "data": {"user_id": "123"}},
        ]
    :return: asyncio.Task, await to return standard response format
    """
```

**Implementation Requirements**:

1. **Must handle all standard message segment types**: At least support `text`, `image`, `audio`, `video`, `file`, `mention`, `reply`
2. **Must handle platform extension message segments**: For `{platform}_xxx` type message segments, convert them into corresponding platform-native calls
3. **Must return standard response format**: Follow [API Response Standard](api-response.md)
4. **Unsupported message segments should be skipped and warning logged**, not throw an exception causing the entire message to fail

### 6.3 Message Segment Conversion Rules

#### 6.3.1 Standard Message Segment Conversion

Adapters must implement the following standard message segment conversions:

| OneBot12 Message Segment | Conversion Requirement |
|----------------|---------|
| `text` | Directly use `data.text` |
| `image` | `data.file` handled according to §2.1 media protocol (three must forms + determination order) |
| `audio` | Same handling logic as image |
| `video` | Same handling logic as image |
| `file` | Same handling logic as image; filename handled according to §2.1.3 derivation order for `data.filename` |
| `mention` | Convert to platform's @ user mechanism (e.g., Telegram's `entities`, Yunhu's `at_uid`) |
| `reply` | Convert to platform's reply reference mechanism |
| `face` | Convert to platform's emoji sending mechanism, skip if not supported |
| `location` | Convert to platform's location sending mechanism, skip if not supported |

#### 6.3.2 Platform Extension Message Segment Conversion

For message segments with platform prefixes, adapters should recognize and convert them:

```python
def _convert_ob12_segments(self, segments: List[Dict]) -> Any:
    """Convert OneBot12 message segments to platform-native format"""
    platform_prefix = f"{self._platform_name}_"
    
    for segment in segments:
        seg_type = segment["type"]
        seg_data = segment["data"]
        
        if seg_type.startswith(platform_prefix):
            # Platform extension message segment → platform-native call
            self._handle_platform_segment(seg_type, seg_data)
        elif seg_type in self._standard_segment_handlers:
            # Standard message segment → platform equivalent operation
            self._standard_segment_handlers[seg_type](seg_data)
        else:
            # Unknown message segment → log warning and skip
            logger.warning(f"Unsupported message segment type: {seg_type}")
```

#### 6.3.3 Handling of Composite Message Segments

A message may contain multiple message segments, and adapters need to handle composite messages correctly:

```python
# Module sends a message containing text+image+@ user
await send.Raw_ob12([
    {"type": "mention", "data": {"user_id": "123"}},
    {"type": "text", "data": {"text": "Hello"}},
    {"type": "image", "data": {"file": "https://example.com/img.jpg"}}
])
```

**Handling Strategy**:
- **Prioritize merging**: If the platform supports combining text, image, @, etc., in a single message, merge and send
- **Fallback to splitting**: If the platform does not support merging, send as multiple messages in sequence
- **Maintain order**: The sending order of message segments should match the list order

### 6.4 Relationship Between `Raw_ob12` and Standard Methods

The adapter's standard send methods (`Text`, `Image`, etc.) are **already implemented and default-delegated to `Raw_ob12` by the `SendDSL` base class**; adapter subclasses do not need to re-implement them:

```python
class Send(SendDSL):
    def Raw_ob12(self, message_segments: List[Dict]) -> asyncio.Task:
        """Core implementation: OneBot12 message segments → platform API (must implement)"""
        return asyncio.create_task(self._send_ob12(message_segments))

    # Text/Image/Voice/Video/File inherited from base class, automatically delegated to Raw_ob12
    # If platform-specific logic is needed, override individual methods:
    # def Text(self, text: str) -> asyncio.Task:
    #     return self.Raw_ob12([{"type": "text", "data": {"text": text}}])
```

**Benefits**:
- Conversion logic is centralized in `Raw_ob12`, reducing duplicate code
- Standard methods and `Raw_ob12` have identical behavior
- Modules get the same result whether using `Text()` or `Raw_ob12()`
- The base class provides type signatures, allowing IDE to complete standard methods

### 6.5 Implementation Example

```python
class YunhuSend(SendDSL):
    """Yunhu platform Send implementation"""
    
    def Raw_ob12(self, message_segments: list) -> asyncio.Task:
        """OneBot12 message segments → Yunhu API call"""
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

Module developers can query the adapter's supported send methods (don't hardcode the platform's method list in the module—each adapter's extension methods evolve with version changes, so runtime discovery is the standard):

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

## 9. Adapter Development Notes

For how to correctly override `BaseAdapter`, `Send`, `Request`'s `__init__`, see [Adapter Development Guide - `__init__` Notes](../developer-guide/adapters/getting-started.md#init-注意事项).

---

---

## 10. Adapter Implementation Checklist

### Send Methods
- [ ] Standard methods (`Text`, `Image`, etc.) implemented
- [ ] Return values are all `asyncio.Task`
- [ ] Modifier methods (`At`, `Reply`, `AtAll`) return `self`
- [ ] Platform extension methods use PascalCase, no platform prefix
- [ ] All methods have complete type annotations and docstrings

### Media Sending Protocol
- [ ] `file` parameter **must forms** all supported: HTTP(S) URL / local path / `bytes` (see §2.1.1)
- [ ] Form determination order follows §2.1.2 (bytes → URL → `file://` → path)
- [ ] `File`'s filename derivation order follows §2.1.3 (explicit `filename` > URL basename > path basename > platform default)
- [ ] Platform's media restrictions (size / MIME / duration) are declared in adapter documentation (§2.1.4)
- [ ] Unsupported media types handled by the degradation ladder in §2.1.5: degraded to similar type or return `retcode=10002`, no exception thrown, no silent discard

### Merge Forward (Optional, see §2.4)
- [ ] Platform has native merged forward: `MergeForward` uses protocol dedicated endpoint, fails back to `send_msg` (OneBot11 system)
- [ ] Platform has no native forward but has rich text: `MergeForward` renders into platform's folded form (HTML card / Card / Embed / blockquote)
- [ ] Neither exists: **do not implement** `MergeForward`, do not return success while sending node dictionary as plain text
- [ ] `MergeForward` does not call `Raw_ob12` to forward the same nodes internally

### Reverse Conversion
- [ ] `Raw_ob12` **implemented** (required, cannot skip)
- [ ] `Raw_ob12` can handle all standard message segments (`text`, `image`, `audio`, `video`, `file`, `mention`, `reply`)
- [ ] `Raw_ob12` can handle platform extension message segments (`{platform}_xxx` type)
- [ ] Standard send methods (`Text`, `Image`, etc.) internally delegate to `Raw_ob12`, not implement separate conversion logic
- [ ] Unsupported message segments are skipped and warning logged, not thrown as an exception
- [ ] Composite message segments are correctly handled (merged or sent sequentially)

---

## 11. MessageBuilder - Adapter-Side Notes

`MessageBuilder` is a OneBot12 message segment builder tool provided by ErisPulse, for **module-side** message construction:
Chained calls (or static quick construction) ultimately produce a standard message segment list `[{"type": ..., "data": ...}]`,
which is directly passed to `Raw_ob12` by the caller.

**Adapter-side only needs to know this**: `Raw_ob12` receives exactly this product—structurally identical to a hand-written message segment list,
and processed according to the segment distribution logic in §6.2, without needing to perceive whether it comes from `MessageBuilder` or a literal list.

> Full usage (dual-mode mechanism, all message segment methods, `copy()` / `clear()` utility methods, and examples) is in [MessageBuilder Detailed Explanation](../advanced/message-builder.md), not repeated here.

---

## 12. Related Documents

**For implementing send return values, refer to:**
- [API Response Standard](api-response.md) - Standard format for adapter API responses

**For other sides of the same adapter:**
- [Event Conversion Standard](event-conversion.md) - Complete event conversion specification, extension naming, and message segment standard
- [Session Type Standard](session-types.md) - Definition and mapping of session types
- [Request Operation Specification](request-action-spec.md) - Field requirements for request events, HandleRequest DSL, and adapter implementation requirements



### 请求操作规范

# ErisPulse Request Operation Specification

> [!TIP]
> **When to read this**: When your adapter needs to handle friend requests/group invitations (converting request events, implementing `accept`/`reject`), or when your module needs to use `event.approve()` / `event.reject()` to approve requests, refer to this document. Otherwise, skip it.

This document defines the standardized specification for request event operations in ErisPulse adapters, including field requirements for request events, usage of the Request DSL, and adapter implementation requirements.

## 1. Overview

Request events (`type: "request"`) are a special event type defined in the OneBot12 standard, representing requests that require the Bot to make a decision (such as friend requests, group invitations, etc.).

Unlike message events, request events require **two-way interaction**:
1. **Receiving**: The adapter converts platform-native requests into standard request events
2. **Responding**: Modules perform operations via the `Request` DSL or `Event.approve()`/`Event.reject()`

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
    │       ├─→ event.approve()     ← Approve request
    │       └─→ event.reject()      ← Reject request
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
    └─→ Or operate directly through the adapter
            await adapter.Request("req_id").accept()
```

## 2. Request Event Field Requirements

### 2.1 Standard Fields

In addition to the required OneBot12 standard fields, request events must include the following fields:

| Field | Type | Required | Description |
|------|------|------|------|
| `request_id` | string | **Strongly recommended** | Request identifier, used for accept/reject operations |
| `user_id` | string | Yes | ID of the requester |
| `user_nickname` | string | No | Nickname of the requester |
| `comment` | string | No | Message attached to the request |

### 2.2 The `request_id` Field

`request_id` is the core identifier for request operations:

- **Purpose**: Identifies an operable request, used by the `Request` DSL
- **Generation rules**:
  - Prefer the platform's native request identifier (e.g., OneBot11's `flag` field, Telegram's `chat_invite_link`, etc.)
  - If the platform has no native request ID, the adapter should generate a unique identifier (suggested format: `{platform}_{timestamp}_{user_id}`)
- **Uniqueness**: Should remain unique within the same platform scope
- **Missing behavior**: When `request_id` is missing, `event.approve()` / `event.reject()` will raise `ValueError`

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

### 3.1 Chained Calls

`Request` provides a chained call interface consistent with the `Send` style:

```python
# Basic usage
await adapter.Request("req_id").accept()
await adapter.Request("req_id").reject()

# Specify a Bot account
await adapter.Request("req_id").Using("bot1").accept()

# With a note (via kwargs)
await adapter.Request("req_id").accept(comment="Welcome")
await adapter.Request("req_id").reject(comment="Not adding for now")

# Combined usage
await adapter.Request("req_id").Using("bot1").accept(comment="Welcome")
```

### 3.2 Method List

| Method | Description | Return Value |
|------|------|--------|
| `Using(account_id)` | Specify the Bot account to perform the operation | `RequestDSL` (supports chaining) |
| `accept(**kwargs)` | Approve the request | `asyncio.Task` (returns the standard response after await) |
| `reject(**kwargs)` | Reject the request | `asyncio.Task` (returns the standard response after await) |

### 3.3 Return Value Format

Operations return the standard API response format:

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
    "message": "The request has expired or does not exist"
}
```

**Not implemented** (adapter does not override `accept`/`reject`):
```json
{
    "status": "failed",
    "retcode": 10002,
    "data": null,
    "message_id": "",
    "message": "Platform MyAdapter has not implemented request operations (accept)"
}
```

## 4. Event Convenience Methods

The `Event` wrapper class provides convenience methods suitable for use in request event handlers:

```python
from ErisPulse.Core.Event import request

@request.on_friend_request()
async def handle_friend_request(event):
    # Check the request ID
    request_id = event.get_request_id()
    if not request_id:
        print("Warning: request event is missing request_id")
        return
    
    # Approve the request
    result = await event.approve()
    
    # Or reject the request
    # result = await event.reject(comment="Not adding friends for now")
    
    # Check the result
    if result.get("status") == "ok":
        print("Operation succeeded")
    else:
        print(f"Operation failed: {result.get('message')}")
```

### 4.1 Event Method List

| Method | Description | Return Value |
|------|------|--------|
| `get_request_id()` | Get the request ID | `str` |
| `approve(comment=None)` | Approve the current request event | Standard response format |
| `reject(comment=None)` | Reject the current request event | Standard response format |

## 5. Adapter Implementation Requirements

### 5.1 Converter Requirements

When converting request events, the adapter's converter **must** correctly set the `request_id` field:

```python
def convert_request_event(self, raw_event: dict) -> dict:
    """Convert a platform-native request event"""
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
    Extract the request ID from a platform-native event
    
    Prefer the platform's native request identifier; generate a unique ID if unavailable
    """
    # Prefer the platform's native ID
    if flag := raw_event.get("flag"):
        return str(flag)
    if request_key := raw_event.get("request_key"):
        return str(request_key)
    
    # Fallback: generate a unique ID
    import hashlib
    raw = f"{self._platform_name}_{raw_event.get('user_id')}_{raw_event.get('timestamp')}"
    return hashlib.md5(raw.encode()).hexdigest()
```

### 5.2 Request Inner Class Implementation

The adapter only needs to override `accept` and `reject` in the `Request` inner class:

```python
from ErisPulse.Core import BaseAdapter, RequestDSL

class MyAdapter(BaseAdapter):
    
    class Request(RequestDSL):
        """MyPlatform request operation implementation"""
        
        def accept(self, **kwargs):
            """
            Approve the request
            
            :param kwargs: Extended parameters, e.g., comment="a note"
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
            """Reject the request"""
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

### 5.3 Platforms That Do Not Support Request Operations

If the platform itself does not support friend request/group invitation operations (e.g., some platforms handle requests automatically), the adapter can:

1. **Not override the `Request` inner class**: Use the base class's default implementation; calling `accept()`/`reject()` returns `retcode=10002`
2. **Skip `request_id` during conversion**: Do not generate `request_id`, letting `event.approve()` raise `ValueError`
3. **Log warnings**: Log a warning in `accept`/`reject` and return an appropriate error code

### 5.4 Summary: Send and Request in Parallel

The adapter has two parallel DSL inner classes, each with its own responsibility:

```
BaseAdapter
├── Send(SendDSL)     ← Message sending
│   ├── Raw_ob12()    ← Must be implemented
│   ├── Text()        ← Recommended to implement
│   └── Image()       ← Implement as needed
│
└── Request(RequestDSL) ← Request operations
    ├── accept()        ← Implement as needed
    └── reject()        ← Implement as needed
```

### 5.5 Adapter `__init__` Notes

When overriding the `__init__` of the `Request` inner class, you must pass through the parameters and call `super().__init__()`. See [Adapter Development Getting Started - `__init__` Notes](../developer-guide/adapters/getting-started.md#init-notes) (`Request` works the same way, with parameters `adapter, request_id, account_id`).

## 6. Adapter Implementation Checklist

### Basic Requirements
- [ ] If `__init__` is overridden, `super().__init__()` has been called (ensures Send / Request factory initialization)

### Request Event Conversion
- [ ] Request events include the `request_id` field (strongly recommended)
- [ ] `detail_type` is correctly mapped to `"friend"` or `"group"`
- [ ] Platform raw data is preserved in the `{platform}_raw` field
- [ ] The `request_id` generation rules are documented

### Request Operations
- [ ] The `Request` inner class is implemented (if the platform supports request operations)
- [ ] The `accept()` method is implemented
- [ ] The `reject()` method is implemented
- [ ] Operations return the standard API response format
- [ ] Unsupported operations return `retcode=10002`
- [ ] Network errors return `retcode=33xxx` (following the API response standard)

## 7. Error Code Extensions

Recommended error codes for the **adapter implementation layer** related to request operations (following the [API Response Standard](api-response.md) §3.2,
customized in the last three digits of the `34xxx` platform error range):

| Error Code | Error Name | Description |
|-------|-------|------|
| 34001 | Request Not Found | The request does not exist or has expired |
| 34002 | Request Already Handled | The request has already been handled |
| 34003 | Request Not Supported | The platform does not support this type of request operation |
| 34004 | Permission Denied | The Bot has no permission to handle this request (returned by the platform) |

> **Boundary with framework codes**: The `340xx` codes above are request handling failures returned by the **platform/adapter**;
> when the ErisPulse framework disables a module's request action via `scope.actions`, it **returns `34601` directly before calling the adapter**
> (Action Denied, see [API Response Standard §5.3](api-response.md#53-framework-extension-return-codes-last-three-digits-of-the-34xxx-platform-error-range)).
> The two do not replace each other: first pass the `34601` framework gate, then fall to the platform-layer `340xx` errors.

## 8. Related Documents

**Reference alongside when implementing request operations**:
- [Event Conversion Standard](event-conversion.md) - Complete event conversion specification (including `request_id` field requirements)
- [API Response Standard](api-response.md) - Adapter API response format standard (operation return values and error codes)

**Other DSLs of the same adapter**:
- [Send Method Specification](send-method-spec.md) - Method naming and parameter specifications for the Send class
- [Session Types Standard](session-types.md) - Session type definitions and mapping relationships



### API 动作标准

# ErisPulse API Action Standard

> [!TIP]
> **When to read this**: When implementing Api DSL standard actions in an adapter (get_user_info / delete_message, etc.), or calling these standard actions cross-platform in a module and needing to confirm parameters and data fields. Skip it if you don't need it.

This document defines the unified interface specification for **OneBot12 standard API actions** in ErisPulse adapters, allowing module developers to program against a standard interface while adapters are responsible for mapping to platform-native APIs.

> **Scope**: Among the OneBot12 standard actions, `ApiDSL` provides strongly typed methods for user /
> group / guild / message management / Meta regular interfaces (`send_message` is
> handled by `SendDSL.Raw_ob12`). File resource actions (`upload_file` / `get_file` / fragmented) are
> retained only as degraded pass-through, see §3.5. Platform extension actions are invoked through
> the `Api.call("prefix.action", ...)` escape hatch. Action parameters and return structures follow
> the OneBot12 specification (`onebot/specs/interface/` in the repository).

## 1. Design Background

In ErisPulse, message segments (message send/receive) and event formats already fully follow the OneBot12 standard, but **API action calls** (such as getting user info, getting group lists, recalling messages, etc.) were previously not unified—module developers had to write different `call_api` calls for each platform.

`ApiDSL` solves this problem by providing strongly typed standard action methods:

```
Module code (cross-platform unified)       Adapter implementation (platform-specific)
─────────────────              ──────────────────
adapter.Api.get_user_info("123")  →  adapter call_api / override
adapter.Api.get_group_list()      →  adapter call_api / override
adapter.Api.delete_message("id")  →  adapter call_api / override
```

## 2. Three Parallel DSL Classes

ErisPulse adapters have three parallel DSL inner classes, each with its own responsibility:

```
BaseAdapter
├── Send(SendDSL)       ← Message sending (Text/Image/Raw_ob12)
├── Request(RequestDSL)  ← Request operations (accept/reject)
└── Api(ApiDSL)          ← Standard API actions (user/group/guild/message management/file/meta) ★
```

| DSL | Responsibility | Method Style | Return Value |
|-----|------|---------|--------|
| `Send` | Send messages | Chained + `asyncio.Task` | Standard response |
| `Request` | Handle request events | `asyncio.Task` | Standard response |
| `Api` | Query/management operations | `async` methods | Standard response |

## 3. Standard Action List

### 3.1 User-Related

| Method | OB12 Action | Parameters | data Return |
|------|----------|------|----------|
| `get_self_info()` | `get_self_info` | None | `user_id`, `user_name`, `user_displayname` |
| `get_user_info(user_id)` | `get_user_info` | `user_id: str` | `user_id`, `user_name`, `user_displayname`, `user_remark` |
| `get_friend_list()` | `get_friend_list` | None | `list[get_user_info response]` |

### 3.2 Group-Related

| Method | OB12 Action | Parameters | data Return |
|------|----------|------|----------|
| `get_group_info(group_id)` | `get_group_info` | `group_id: str` | `group_id`, `group_name` |
| `get_group_list()` | `get_group_list` | None | `list[get_group_info response]` |
| `get_group_member_info(group_id, user_id)` | `get_group_member_info` | `group_id: str`, `user_id: str` | `user_id`, `user_name`, `user_displayname` |
| `get_group_member_list(group_id)` | `get_group_member_list` | `group_id: str` | `list[get_group_member_info response]` |
| `set_group_name(group_id, group_name)` | `set_group_name` | `group_id: str`, `group_name: str` | None |
| `leave_group(group_id)` | `leave_group` | `group_id: str` | None |

### 3.3 Message Management

| Method | OB12 Action | Parameters | Description |
|------|----------|------|------|
| `delete_message(message_id)` | `delete_message` | `message_id: str` | Recall/delete a message |

> **Message sending** (`send_message`) is handled by `SendDSL`'s `Raw_ob12` and is not duplicated in `ApiDSL`.

### 3.4 Guild-Related

The OneBot12 guild system has two levels: **guild** and **channel**.

| Method | OB12 Action | Parameters | data Return |
|------|----------|------|----------|
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

> The guild system and groups are independent of each other: platforms such as Discord / QQ Guild / Kook implement the guild interfaces, while traditional QQ / WeChat implement the group interfaces; both may exist simultaneously or only one of them.

### 3.5 File Resource Operations

> [!WARNING]
> **The file resource model (two-stage file_id) is "degraded availability" in ErisPulse**:
> File send/receive in ErisPulse does not follow the "upload first to get a file_id, then reference it" model—modules send files with
> `SendDSL.File(file, filename)` (URL / path / bytes are **transmitted directly at send time**, see the
> [Send Method Specification](send-method-spec.md)).
> The `upload_file` / `get_file` / fragmented actions in this section depend on platform-specific `file_id` file resource
> capabilities, which are **not general-purpose**; pass-through is only possible when the adapter backend natively has this capability. The framework's built-in
> adapters **neither implement nor recommend implementing** them; calls typically return `retcode=10002`.
> When a module needs to transfer files cross-platform, use `SendDSL.File` and do not rely on file_id.
>
> **Outlook**: Standardizing the `file_id` resource model at the framework layer is a future direction; the current version does not provide it.

Whole-file transfer (small files):

| Method | OB12 Action | Parameters | data Return |
|------|----------|------|----------|
| `upload_file(*, type, name, ...)` | `upload_file` | `type`, `name`, `url`/`path`/`data`, `headers?`, `sha256?` | `file_id` |
| `get_file(file_id, type)` | `get_file` | `file_id: str`, `type: str` | `name`, `url`/`path`/`data` |

The `type` parameter of `upload_file`:
- `"url"`: Upload via URL (requires `url`)
- `"path"`: Upload via local path (requires `path`)
- `"data"`: Upload via binary data (requires `data`)

#### 3.5.1 Fragmented Transfer (Large Files, Within the Above Degraded Scope)

OneBot12 fragmented actions distinguish phases by `stage`. `ApiDSL` splits the three/two phases of the same action into independent methods
(`offset` is a byte offset, and `data` is Base64 in JSON); the tables below are retained for reference only, and adapters need not and should not be forced to implement them:

**Three-step fragmented upload**: `prepare` → `transfer` (loop chunk by chunk) → `finish`

| Method | Corresponding stage | Parameters | data Return |
|------|-----------|------|----------|
| `upload_file_fragmented_prepare(name, total_size)` | `prepare` | `name: str`, `total_size: int` | `file_id` (used during transfer) |
| `upload_file_fragmented_transfer(file_id, offset, data)` | `transfer` | `file_id`, `offset: int`, `data: bytes` | None |
| `upload_file_fragmented_finish(file_id, sha256)` | `finish` | `file_id`, `sha256: str` (whole-file checksum) | `file_id` |

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

**Two-step fragmented download**: `prepare` → `transfer` (loop fetching chunks)

| Method | Corresponding stage | Parameters | data Return |
|------|-----------|------|----------|
| `get_file_fragmented_prepare(file_id)` | `prepare` | `file_id` | `name`, `total_size`, `sha256` |
| `get_file_fragmented_transfer(file_id, offset, size)` | `transfer` | `file_id`, `offset: int`, `size: int` | `data` (bytes of the current chunk) |

### 3.6 Meta Actions

Meta actions do not target a specific account and do not require `Using()` to specify a Bot.

| Method | OB12 Action | Parameters | data Return |
|------|----------|------|----------|
| `get_latest_events(limit, timeout)` | `get_latest_events` | `limit: int=0`, `timeout: int=0` | Array of event objects (excluding meta events) |
| `get_supported_actions()` | `get_supported_actions` | None | `list[str]` of supported action names |
| `get_status()` | `get_status` | None | `good: bool`, `bots: list[{self, online, ...}]` |
| `get_version()` | `get_version` | None | `impl`, `version`, `onebot_version` |

### 3.7 Generic Extension Actions

| Method | Description |
|------|------|
| `call(action, **params)` | Escape hatch for platform extension actions, following the OB12 extension naming rule `{prefix}.{action}` |

## 4. Usage

### 4.1 Basic Calls

```python
from ErisPulse import adapter

# Get user info (cross-platform unified)
result = await adapter.myplatform.Api.get_user_info("123456")
if result["status"] == "ok":
    user_name = result["data"]["user_name"]
    print(f"Username: {user_name}")

# Get group list
result = await adapter.myplatform.Api.get_group_list()
groups = result["data"]

# Recall a message
await adapter.myplatform.Api.delete_message("msg_123456")
```

### 4.2 Specifying a Bot Account (Multi-Account Mode)

```python
# Execute operations with a specified Bot account
info = await adapter.myplatform.Api.Using("bot1").get_self_info()
```

### 4.3 Platform Extension Actions

```python
# Call a platform-specific extension action (use the {prefix}.{action} naming convention)
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
    # Get detailed sender info
    user_id = event.get_user_id()
    platform = event.get_platform()

    result = await getattr(adapter, platform).Api.get_user_info(user_id)
    if result["status"] == "ok":
        user_name = result["data"]["user_name"]
        await event.reply(f"Hello, {user_name}!")
```

## 5. Adapter Implementation

### 5.1 Default Behavior (Zero Configuration)

The default implementation of `ApiDSL` passes the standard action name directly to `adapter.call_api()` as the `endpoint`:

```python
# The ApiDSL default implementation is equivalent to:
async def get_user_info(self, user_id: str) -> dict:
    return await self._adapter.call_api("get_user_info", user_id=user_id, account_id=self._account_id)
```

**Applicable scenario**: When the adapter's underlying backend itself follows the OneBot12 standard action protocol, `call_api` naturally supports standard action names (e.g., when directly connecting to a server that follows this protocol).

### 5.2 Overriding Standard Methods (Mapping to Platform-Native APIs)

An adapter can override individual standard methods, mapping them to platform-native APIs:

```python
class MyAdapter(BaseAdapter):

    class Api(BaseAdapter.Api):
        """MyPlatform standard API action implementation"""

        async def get_user_info(self, user_id: str) -> dict:
            # Map to platform-native API
            raw = await self._adapter._request("GET", f"/users/{user_id}")
            if raw.get("code") != 0:
                # Platform-side error: use the 341xx–345xx range for the custom low three digits (346xx is reserved by the framework, do not use)
                return self._adapter.make_error(retcode=34400, message="User not found")

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

Standard methods not overridden by the adapter use the default implementation (delegating to `call_api`). If `call_api` also does not support the action, it should return a standard error response:

```python
async def call_api(self, endpoint: str, **params):
    if endpoint not in self._supported_endpoints:
        return self.make_error(retcode=10002, message=f"Unsupported action: {endpoint}")
    # ... platform API call
```

Module developers can check the `retcode` in the return value to determine whether an action is supported:

```python
result = await adapter.myplatform.Api.get_friend_list()
if result["retcode"] == 10002:
    print("This platform does not support getting the friend list")
```

## 6. Response Format

All `ApiDSL` methods return the standard API response format (see the [API Response Standard](api-response.md) for details):

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

> **Note**: For information-query actions, `message_id` is an empty string (only message-sending actions have a `message_id`).

## 7. Relationship with SendDSL / RequestDSL

| Scenario | DSL to Use | Example |
|------|---------|------|
| Send a message | `Send` | `adapter.Send.To("group", "123").Text("hi")` |
| Accept/reject a request | `Request` | `adapter.Request("req_id").accept()` |
| Get user/group info | `Api` | `adapter.Api.get_user_info("123")` |
| Recall a message | `Api` | `adapter.Api.delete_message("msg_id")` |
| Leave a group | `Api` | `adapter.Api.leave_group("group_id")` |

## 8. Adapter Implementation Checklist

### Standard Actions
- [ ] `call_api` can handle standard action names (or override the corresponding `ApiDSL` methods)
- [ ] Unsupported actions return `retcode=10002`
- [ ] Return values follow the standard API response format
- [ ] The `data` field contains the fields defined by the OB12 standard
- [ ] Guild platforms must implement `get_guild_*` / `get_channel_*` / `leave_guild` / `leave_channel`
- [ ] Meta actions (`get_status` / `get_version` / `get_supported_actions`) are recommended to be implemented
- [ ] **File send/receive uses `SendDSL.File` (direct transmission)**; file resource actions (upload_file/get_file/fragmented) are **not mandatory to implement**; pass-through is only needed when the backend has `file_id` resource capability

### Extension Actions
- [ ] Platform extension actions use the `{prefix}.{action}` naming convention
- [ ] Extension action parameters and responses still follow the OB12 action request/response structure

## 9. Related Documents

**Companion reference when implementing Api DSL return values**:
- [API Response Standard](api-response.md) - Adapter API response format standard

**Other DSLs of the same adapter**:
- [Send Method Specification](send-method-spec.md) - Method naming and parameter specification for the Send class
- [Request Action Specification](request-action-spec.md) - How to use the Request DSL

**Event-side companion**:
- [Event Conversion Standard](event-conversion.md) - Event format and message segment standard



====
生态模块
====


### ErisPulse-App 安装与使用

# ErisPulse-App

> [!TIP]
> **When to read this**: Read this when you want to create, run, and manage bot instances with a graphical interface on your phone or computer—without touching a terminal or installing a separate Python environment. Skip it if you don't need that.

[ErisPulse-App](https://github.com/ErisPulse/ErisPulse-App) is the **official multi-platform client** maintained directly by ErisDev (already released for Android / Windows / Linux / macOS).
It provides a fully native graphical management interface: create, run, and manage multiple bot instances on your phone or computer,
with no terminal required and no separate Python environment installation needed.

> [!IMPORTANT]
> ErisPulse-App is an **independently installed client application**, not a module installed via `epsdk install`.
> It comes with a built-in Python runtime and the ErisPulse SDK, ready to use right after installation—**it even runs directly on mobile phones**.

## Feature Overview

- **Multiple Instance Management**: Create / Start / Stop / Delete multiple instances, with ports and access tokens automatically assigned. Supports new environments or cloning existing environments.
- **Overview Dashboard**: Adapter / Module / Online Robot / Total Event Count statistics, CPU / Memory usage alerts with color changes.
- **Module Store**: Search and tag filtering, one-click install / upgrade / uninstall, install specific versions, support for pip mirror sources and Git packages.
- **Event Stream + Event Builder**: Real-time event viewing, visual construction of test events and submission to adapters.
- **Monitoring**: Unified view of logs / lifecycle / audit.
- **Command Management**: Global settings such as prefixes and aliases, enable/disable and platform whitelists/blacklists.
- **Robot Overview / Configuration / File Management**: Direct native interface operations on instances.
- **Background Persistence**: Android foreground service for survival; Windows minimize to system tray, closing the window does not interrupt instances.
- **Dynamic Module Windows**: Automatically appear in the sidebar navigation (same group as Dashboard) for pages registered by modules, click to navigate directly.

## Supported Platforms

All platform installers can be downloaded from [GitHub Releases](https://github.com/ErisPulse/ErisPulse-App/releases); simply choose the one that suits your needs:

| Platform | Installer | Description |
|----------|-----------|-------------|
| Android | `online-*.apk` / `offline-*.apk` | **Run directly on your phone**, no computer required |
| Windows | `windows-x64-setup.exe` / `windows-x64.zip` | Installer version / portable version |
| Linux | `linux-x64.tar.gz` | Extract and use |
| macOS | `macos-arm64.zip` | Apple Silicon (arm64) |

A single Flutter codebase covers all platforms.

## Installation Method (Android / Direct Phone Execution)

Download the APK from [GitHub Releases](https://github.com/ErisPulse/ErisPulse-App/releases) and install it. There are two builds available:

| Build | Runtime Image | Use Case |
|-------|---------------|----------|
| `erispulse-app-online-*.apk` | Downloaded on first launch | Smaller installation package, suitable for good network conditions |
| `erispulse-app-offline-*.apk` | Embedded in the APK | Offline self-contained, no internet required after installation |

Both builds follow the same installation steps:

1. Download and install the APK, and allow notification permissions when prompted (to keep the background service alive).
2. After the initialization banner appears on the home screen, click to run the first initialization (including progress and log views).
3. Create an instance and start it.
4. Configure adapters and model API keys in the App's built-in management interface.

> The offline package is self-contained—no internet connection is required after installation. If the download is slow or unstable on first launch, you can switch the download source to a mirror (ghfast / gh-proxy) in the settings page.

### Installation Method (Desktop: Windows / Linux / macOS)

1. Download the installation package for your platform from [GitHub Releases](https://github.com/ErisPulse/ErisPulse-App/releases)  
   (Windows: `setup.exe` or portable `zip`, Linux: `tar.gz`, macOS: `zip`)
2. Install and launch the application.
3. On the welcome page, select the ErisPulse SDK version to install (default is the latest).
4. Create an instance and start it.

---

## How It Works

```
┌────────────────────────────────────────────────────┐
│  ErisPulse-App (Flutter)                            │
│                                                    │
│  Native UI ── Dashboard REST / WS API              │
│       │                                            │
│       ├── Android: Foreground Service + proot + Ubuntu rootfs │
│       │        + Python + ErisPulse Instance       │
│       └── Desktop: Built-in Python + Direct Process Management │
└────────────────────────────────────────────────────┘
```

- **Android**: The instance runs within a proot (userspace chroot) hosted by a foreground service (background isolate). Even after the UI is closed, the bot continues to run and automatically restarts on crash.
- **Desktop**: The instance runs as a direct child process of the App. On Windows, it supports minimizing to the system tray to stay in the background (closing the window does not interrupt the instance). When the App restarts, it automatically resumes management of any still-running instances, and all instances are stopped together when exiting.
- On all platforms, the native UI communicates with the instance through the REST / WebSocket API at `127.0.0.1:<port>/Dashboard/*`, sharing the same API as [ErisPulse-Dashboard](dashboard.md).

## Relationship with SDK

- ErisPulse SDK is embedded in the App: Android is bundled in the Ubuntu image, desktop is installed from PyPI (optional version on welcome page, default latest)
- Instances in the App are equivalent to those created by the command line `epsdk`, and can use the same modules/adapters
- Module developers can register custom pages via the [Dashboard window registration API](dashboard.md): the window will automatically appear in the App's side navigation (grouped the same as Dashboard), and clicking will navigate to the corresponding page for rendering

---



### Dashboard 使用与视窗注册

# ErisPulse-Dashboard

> [!TIP]
> **When to read this**: Read this when you want to manage your bot through a web-based visual interface (start/stop modules, edit configurations, view logs, monitor event streams), or when you want to register a Dashboard management page for your own module. Skip it if you don't need these.

[ErisPulse-Dashboard](https://pypi.org/project/ErisPulse-Dashboard/) is a **Web management panel module** maintained directly by ErisDev, providing ErisPulse with a visual runtime management interface: module start/stop, configuration editing, log viewing, event stream monitoring, and more.

> [!IMPORTANT]
> Dashboard is **not** a built-in feature of the ErisPulse framework and requires separate installation:
>
> ```bash
> epsdk install Dashboard
> ```

Dashboard also supports other ErisPulse modules registering custom management pages to the sidebar. Once registered, users can switch directly to the module's dedicated view page within the Dashboard, without needing to develop a standalone frontend interface.

> [!NOTE]
> View registration is an **optional feature**.
>
> - If the Dashboard module is **not installed** or **not loaded**, calling `sdk.Dashboard.register_view()` will raise an exception
> - Be sure to wrap the registration code in `try/except` to ensure that other functionality of the module itself is not affected
> - It is recommended to check whether Dashboard is available before registering: `hasattr(sdk, 'Dashboard') and sdk.Dashboard`

---

## How It Works

```
Module on_load()
  → Calls sdk.Dashboard.register_view(...)
  → Dashboard backend stores view information
  → WebSocket notifies the frontend
  → Frontend dynamically creates sidebar navigation item + page container
  → User clicks to view the module view
```

---

## Registration API

```python
sdk.Dashboard.register_view(
    id="MyModule",                    # Required, unique identifier
    title="My Module",                # Chinese name
    title_en="My Module",             # English name
    icon_svg='<svg>...</svg>',        # Sidebar icon SVG
    html_content='<div>...</div>',     # Page HTML content
    js_content='function xxx() {}',    # Page JavaScript logic
    css_content='.my-style {}',        # Optional custom CSS
    iframe_url='',                     # iframe mode URL (choose either this or html_content)
    loader="loadMyModuleView",         # JS function name called when switching to this page
    group="group_extensions",          # Sidebar group
    group_title="",                    # Custom group name in Chinese
    group_title_en="",                 # Custom group name in English
)
```

### Parameter Descriptions

| Parameter | Type | Required | Description |
|------|------|------|------|
| `id` | `str` | Yes | Unique identifier of the view; module name recommended |
| `title` | `str` | No | Chinese display name, defaults to `id` |
| `title_en` | `str` | No | English display name, defaults to `title` |
| `icon_svg` | `str` | No | Complete SVG string for the sidebar icon |
| `html_content` | `str` | No* | Page HTML content in injection mode |
| `js_content` | `str` | No | Page JavaScript code |
| `css_content` | `str` | No | Page custom CSS styles |
| `iframe_url` | `str` | No* | URL in iframe mode; `html_content` is ignored when set |
| `loader` | `str` | No | JS function name automatically called when the page is activated |
| `group` | `str` | No | Sidebar group identifier, defaults to `group_extensions` |
| `group_title` | `str` | No | Chinese title of the custom group |
| `group_title_en` | `str` | No | English title of the custom group |

> *At least one of `html_content` and `iframe_url` must be provided; otherwise the page will be blank.

---

## Two Injection Modes

### Mode 1: HTML/JS Injection (Recommended)

Provide HTML, JS, and CSS strings directly, and Dashboard will inject the content into the page. This mode is fully consistent with the Dashboard's styling; it is recommended to use the CSS class names provided by Dashboard.

```python
sdk.Dashboard.register_view(
    id="HelloPage",
    title="Hello Page", title_en="Hello",
    icon_svg='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/></svg>',
    html_content='<h1 class="page-title">Hello World</h1><div class="card"><div class="card-body">This is a sample page</div></div>',
    group="group_tools",
)
```

> For a complete weather module example (including API routes, JS interactions, etc.), see [Complete Module Example](#complete-module-example) below.

### Mode 2: iframe Embedding

The module provides its own HTML page URL (routes must be registered by the module itself), and Dashboard embeds it via an iframe. Suitable for scenarios that require a completely independent UI or complex interactions.

```python
sdk.Dashboard.register_view(
    id="MyVisualizer",
    title="Data Visualization", title_en="Data Visualizer",
    iframe_url="/MyVisualizer/view",
    group="group_tools",
)
```

> In iframe mode, a `token` parameter is automatically appended to the URL for authentication.

---

## Sidebar Groups

Modules can specify the sidebar group in which the view is placed. Dashboard includes the following built-in groups:

| Group Identifier | Chinese Name | Position |
|---------|--------|------|
| `group_overview` | Overview | Group 1 |
| `group_events` | Events | Group 2 |
| `group_extensions` | Extensions | Group 3 (Default) |
| `group_system` | System | Group 4 |
| `group_tools` | Tools | Group 5 |

Specifying a built-in group name will append the module view to the end of that group:

```python
group="group_tools"  # Appended to the "Tools" group
```

You can also use a custom group name (not starting with `group_`), and Dashboard will automatically create a new group:

```python
group="my_group",
group_title="My Group",
group_title_en="My Group",
```

---

## Common CSS Class Names

When the module view uses HTML injection mode, you can directly use Dashboard's existing CSS class names to maintain visual consistency:

| Class Name | Purpose |
|------|------|
| `page-title` | Page title, e.g., `<h1 class="page-title">Title</h1>` |
| `card` | Card container |
| `card-header` | Card header bar |
| `card-body` | Card content area |
| `grid-2` | Two-column grid layout |
| `grid-3` | Three-column grid layout |
| `btn` | Basic button |
| `btn-primary` | Primary button (blue) |
| `btn-secondary` | Secondary button |
| `btn-icon` | Icon button |
| `btn-danger` | Danger action button |

Dashboard uses CSS variables to control theme colors, which you can reference directly in your module view:

| CSS Variable | Purpose |
|----------|------|
| `var(--bg-p)` | Primary background color |
| `var(--bg-s)` | Secondary background color |
| `var(--bg-t)` | Tertiary background color (cards, etc.) |
| `var(--tx-p)` | Primary text color |
| `var(--tx-s)` | Secondary text color |
| `var(--tx-t)` | Auxiliary text color |
| `var(--bd)` | Border color |
| `var(--accent)` | Accent color |
| `var(--ok-c)` | Success color |
| `var(--er-c)` | Error color |

These variables switch automatically according to Dashboard's light/dark theme, so modules do not require additional handling.

---

## Authentication and API Calls

When calling your module's own API from the JS in a module view, you need to carry the Dashboard Token for authentication:

```javascript
var token = localStorage.getItem('__ep_tk__');
var resp = await fetch('/YourModule/api/data', {
    headers: { 'Authorization': 'Bearer ' + token }
});
var data = await resp.json();
```

The module's API endpoint can decide on its own whether to verify the Token. If verification is needed, it can be extracted from the request headers:

```python
async def _api_data(self, request):
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    if not token:
        return {"error": "Unauthorized"}, 401
    return {"data": "hello"}
```

---

## Complete Module Example

Below is a complete weather module example demonstrating how to register a view, provide API data, and clean up resources on unload:

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
                                           '<p>Temperature: ' + (data.temp || '--') + '°C</p>' +
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

## Unregistering a View

When a module is unloaded, it should call `unregister_view()` to clean up registered views:

```python
async def on_unload(self, event):
    if hasattr(self.sdk, 'Dashboard') and self.sdk.Dashboard:
        self.sdk.Dashboard.unregister_view("Weather")
```

After unregistration, the Dashboard frontend will remove the sidebar navigation item and page content in real time via WebSocket, with no user refresh required.

---

## Notes

1. **Loading Order** — Dashboard's load priority is `99999` (high priority); your module's priority should be lower than this value (e.g., `50`) to ensure Dashboard is fully loaded first
2. **Defensive Programming** — Wrap view registration in `try/except`, since the Dashboard module may not be installed or loaded
3. **Resource Cleanup** — Call `unregister_view()` in `on_unload` to remove registered views
4. **ID Uniqueness** — The `id` parameter must be unique across the entire Dashboard; using the module name directly is recommended
5. **SVG Icons** — `icon_svg` should be a complete `<svg>` tag, with a recommended size of `viewBox="0 0 24 24"`; use `stroke="currentColor"` to inherit the Dashboard theme color
6. **JS Function Naming** — Function names in `js_content` should be unique (e.g., `loadWeatherView`) to avoid conflicts with other modules
7. **Dynamic Updates** — After a module registers/unregisters a view, the Dashboard frontend updates the sidebar in real time via WebSocket, with no page refresh needed

---



### Cron 定时任务

# ErisPulse-Cron

> [!TIP]
> **When to read this**: Read this when your module needs to trigger logic at a scheduled or delayed time (such as reminders, periodic monitoring, or scheduling with Cron expressions), and you want the tasks to persist after a framework restart. Skip this if you don't need it.

[ErisPulse-Cron](https://github.com/wsu2059q/ErisPulse-Cron) is the **scheduling module** in the ErisPulse ecosystem, providing a unified API for other modules to schedule timed tasks: it supports one-time timers, interval loops, and Cron expressions, with callback parameters and SQLite persistence (tasks are not lost after a restart).

> [!IMPORTANT]
> Cron is **not** a built-in feature of the ErisPulse framework and must be installed separately:
>
> ```bash
> epsdk install Cron
> ```

After installation, access all interfaces through `sdk.Cron`.

---

## Feature Overview

- **Three Scheduling Types**: One-time (`once`), interval loop (`interval`), and Cron expression (`cron`)
- **Callback Data**: Pass `callback_data` when creating a task, and it will be returned unchanged during execution, making it easy to identify the task source
- **Persistence**: Tasks are stored in SQLite (via `sdk.storage`), and are automatically restored after framework restart
- **Missed Trigger Strategy**: Immediate execution, skip, or rescheduling, selectable per task
- **Task Management**: Pause, resume, cancel, manually trigger, and clean up expired tasks
- **Dashboard Integration**: Automatically registers management windows when [ErisPulse-Dashboard](dashboard.md) is installed

## Quick Start

```python
from ErisPulse import sdk

# 1. Register a callback handler
@sdk.Cron.on_trigger
async def handle_trigger(info):
    data = info["callback_data"]
    print(f"Task triggered: {info['task_id']}, Data: {data}")

# 2. Create a scheduled task
task_id = sdk.Cron.once(
    delay=60,
    callback_data={"type": "reminder", "msg": "It's time to drink water"},
)
```

---

## API Overview

### Create Tasks

```python
# One-time: trigger after a delay of 600 seconds
sdk.Cron.once(delay=600, callback_data={"order_id": "123"}, label="Order timeout reminder")

# Interval loop: trigger every 300 seconds, up to 100 times
sdk.Cron.interval(interval_seconds=300, callback_data={"monitor": "server-1"}, max_runs=100)

# Cron expression: trigger daily at 9:30 AM on weekdays
sdk.Cron.cron(expression="30 9 * * 1-5", callback_data={"type": "daily_report"})

# General optional parameters: trigger_at (absolute timestamp), delay (first delay), timezone,
# max_runs (0 = unlimited), label, source (module name of creator), missed_policy (missed trigger policy)
```

Common Cron expressions: `*/5 * * * *` (every 5 minutes), `0 8 * * *` (every day at 8 AM), `30 9 * * 1-5` (every weekday at 9:30 AM), `0 0 1 * *` (every 1st day of the month).

### Callback

```python
@sdk.Cron.on_trigger
async def my_handler(info):
    # info contains task_id / task_type / callback_data / label / source /
    # run_count / max_runs / created_at / last_run / trigger_time
    ...
```

Multiple handlers can be registered and will be called in sequence. An exception in one handler does not affect others.

### Manage Tasks

```python
sdk.Cron.cancel(task_id)                  # Cancel
sdk.Cron.pause(task_id)                   # Pause
sdk.Cron.resume(task_id)                  # Resume (reschedule=True recalculates next trigger time)
await sdk.Cron.trigger_now(task_id)       # Manually trigger immediately (does not affect original schedule)
sdk.Cron.get_task(task_id)                # View a single task
sdk.Cron.list_tasks(source="MyModule")    # List tasks (supports filtering by source/status/task_type)
sdk.Cron.delete_task(task_id)             # Delete task record
sdk.Cron.cleanup()                        # Clean up completed/canceled tasks older than 7 days
```

### Missed Policy (`missed_policy`)

When the framework restarts, for tasks that missed their trigger time:

| Policy | Behavior |
|--------|----------|
| `fire_immediately` | Trigger immediately (default) |
| `skip` | Skip this trigger, wait for the next one |
| `reschedule` | Recalculate the next trigger time from the current time |

## Behavior on Module Unload

Cron's task data is a **persistent asset**: unloading or disabling the module that created the task does not delete the created task. However, the callback handles registered by the module will be cleaned up. Based on the ownership system's [external cleanup hooks](../advanced/ownership.md#Tool_Module_Guide_Handling_Handles_of_Other_Modules), Cron automatically names callbacks it manages on behalf of other modules. When the corresponding module is unloaded or disabled, its callback handles are automatically discarded, ensuring that the module instance can be properly reclaimed.

- After the task creator module is **reloaded**, re-registering `on_trigger` resumes receiving triggers.
- Tasks that are no longer needed can be cleaned up using `sdk.Cron.cancel(task_id)` / `delete_task(task_id)`.



### Takumi 图片渲染

# ErisPulse-Takumi

> [!TIP]
> **When to read this**: Read this when you need to render HTML / node trees / Jinja templates into images for sending to chat platforms (e.g., statistics cards, leaderboards,图文长文). Skip if not needed.

[ErisPulse-Takumi](https://pypi.org/project/ErisPulse-Takumi/) is a **third-party image rendering module** maintained by ccd2s, based on [takumi-py](https://github.com/BalconyJH/takumi-py), allowing Bots to render HTML, node trees, Jinja templates, SVG, and animations into images. The module **includes built-in Chinese and English fonts** (Noto Sans SC / Roboto / Source Code Pro), requiring no additional configuration.

> [!IMPORTANT]
> Takumi is **not** a built-in feature of the ErisPulse framework and must be installed separately:
>
> ```bash
> epsdk install Takumi
> ```

Applicable scenarios:

- Rendering data/statistics into card images
- Rendering Markdown / long text into well-formatted images to avoid platform style differences
- Generating SVG / animations for dynamic visual effects
- Mixed Chinese and English text images (built-in fonts work out-of-the-box)

## Installation and Activation

```bash
epsdk install Takumi
```

After installation, the module is automatically loaded. Confirm activation in the configuration:

```toml
[Takumi]
enabled = true
```

## Quick Start

After the module is automatically loaded, it can be obtained through the module manager or using the `sdk` shortcut:

```python
from ErisPulse import sdk

takumi = sdk.module.get("Takumi")
# Equivalent syntax: takumi = sdk.Takumi
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
    height=None,   # Auto height based on content
    lang="en",
)
```

### Render Node Tree

```python
png = takumi.render_node(
    {
        "type": "text",
        "text": "Both Chinese and English can be rendered directly",
        "style": {"fontSize": 48, "color": "#111827"},
    },
    width=800,
    height=None,
    lang="en",
)
```

`png` is a `bytes` object, which can be sent using `event.reply(png, method="Image")` (see [Sending Rendered Results](#sending-rendered-results)).

---

## Rendering API

`sdk.Takumi` proxies all capabilities of the underlying `takumi_py.Renderer`: all rendering, measurement, SVG, animation, and template methods are directly callable on `sdk.Takumi`. For these methods, the module automatically injects the built-in font fallback stack (`takumi.families`) at the time of invocation, eliminating the need to manually pass `font_families`; however, explicit input is respected if provided.

### Method Overview

| Category | Method | Return | Description |
|------|------|------|------|
| Static Rendering | `render_html(html, ...)` | `bytes` | Render HTML string |
| | `render_node(node, ...)` | `bytes` | Render node tree (dict) |
| | `render_template(name, ctx, ...)` | `bytes` | Render Jinja template |
| | `render_compiled(node, ...)` | `bytes` | Render pre-compiled node |
| SVG Output | `render_svg_html(html, ...)` | `str` | Output SVG (HTML input) |
| | `render_svg_node(node, ...)` | `str` | Output SVG (node tree input) |
| | `render_svg_template(name, ctx, ...)` | `str` | Output SVG (template input) |
| | `render_svg_compiled(node, ...)` | `str` | Output SVG (pre-compiled input) |
| Animation | `render_animation(scenes, ...)` | `bytes` | Encode multi-frame animation |
| | `render_sequence_at_time(scenes, time_ms, ...)` | `bytes` | Extract frame at a specific time from sequence |
| Measurement | `measure_node(node, ...)` | `dict` | Measure node tree layout |
| | `measure_html(html, ...)` | `dict` | Measure HTML layout |
| | `measure_compiled(node, ...)` | `dict` | Measure pre-compiled node |
| Compilation | `compile_node(node)` | `CompiledNode` | Compile node tree |
| | `compile_html(html, ...)` | `CompiledNode` | Compile HTML |
| Font | `register_font(font)` | `list[str]` | Register custom font, return family list |
| | `register_fonts(fonts)` | `list[str]` | Batch register fonts |

> `CompiledNode` exposes a `resource_urls()` method, allowing pre-discovery of HTTP(S) image references, facilitating resource preparation in advance.

### Common Parameters

The following parameters apply to static rendering and SVG methods (animation methods have additional parameters such as `fps`, see corresponding examples):

| Parameter | Type | Default | Description |
|------|------|--------|------|
| `stylesheets` | `list[str]` | `None` | List of document-level CSS strings; inline `style` is still parsed with HTML |
| `width` | `int \| None` | `1200` | Viewport width (in pixels); `None` infers width from layout |
| `height` | `int \| None` | `630` | Canvas height (in pixels); `None` auto-sizes content (see [Viewport and Output Format](#viewport-and-output-format)) |
| `lang` | `str \| None` | `None` | BCP-47 language tag (e.g., `zh-CN`), affects text shaping and line breaking |
| `font_families` | `list[str]` | Auto-injected | Font fallback stack; convenience methods auto-inject built-in fonts |
| `format` | `str` | `"png"` | Output format (see [Viewport and Output Format](#viewport-and-output-format)) |
| `device_pixel_ratio` | `float` | `1.0` | Device pixel ratio, controls output resolution |
| `time_ms` | `int` | `0` | Animation sampling time (in milliseconds) |
| `dithering` | `str` | `"none"` | Dithering algorithm: `none` / `ordered-bayer` / `floyd-steinberg` |
| `quality` | `int \| None` | `None` | Lossy encoding quality |
| `lossless` | `bool \| None` | `None` | Whether to use lossless encoding |
| `images` | `list` | `None` | Image resources for this render (`ImageResource` or `(src, bytes)` tuple) |
| `keyframes` | `Mapping` | `None` | Structured keyframes, no need to write `@keyframes` |
| `options` | `RenderOptions` | — | Aggregate parameters via `RenderOptions(...)`, fields match the above table |

Full field definitions are available in `takumi_py.RenderOptions`.

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

> Custom Jinja filters can be injected via `filters={...}`, or a full `jinja2.Environment` can be passed via `environment=...`. Template directory and environment configuration are detailed in [takumi-py template documentation](https://github.com/BalconyJH/takumi-py/blob/main/docs/guides/templates.md).

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

> Each frame is constructed using `AnimationScene(node, duration_ms=...)`, where `duration_ms` must be a positive number.

## Viewport and Output Format

### Output Format

| Scenario | `format` value |
|----------|----------------|
| Static image | `png` (default) / `jpeg` / `jpg` / `webp` / `ico` / `raw` |
| Animation | `webp` (default) / `apng` / `gif` |

`format="raw"` returns a row-major RGBA byte stream, for custom pixel-level processing.

### About width and height

The roles of `width` and `height` are asymmetrical:

- `width` is the **viewport width**, text and layout wrap and reflow according to it. **Should be fixed** to a specific value (e.g. `800`), otherwise the canvas will stretch to the natural width of the content, text will not wrap, and the size will be out of control.
- `height` is the **canvas height**, which grows with the content. The default value of `height` is `630`; when `height=None` is passed, Takumi will **automatically expand the canvas height** based on the content (auto viewport).

> [!TIP]
> **Recommended combination: fixed `width` + `height=None`.** Only when a fixed canvas size or clipping effect is needed, should a specific `height` be passed.

> [!NOTE]
> Either `width` or `height` can technically be passed as `None` to let it be inferred by the layout (e.g. when node itself has already declared its size); when both are provided, the output size is determined.

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
| `takumi.fonts` | List of built-in font file names |
| `takumi.families` | List of registered font families |

### Automatic Injection

All rendering, measurement, SVG, animation, and template methods on `sdk.Takumi` automatically inject `takumi.families` as the font fallback stack. If you directly call `takumi.renderer` (native instance) or create an independent instance via `create_renderer()`, you must manually pass `font_families=takumi.families`.

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

## Renderer Instances

### Native Renderer

`takumi.renderer` is the raw `takumi_py.Renderer` instance. When called directly, `font_families` must be passed manually:

```python
png = takumi.renderer.render_html(
    "<div>Hello</div>",
    font_families=takumi.families,
    lang="zh-CN",
)
```

### Standalone Renderer

For scenarios requiring isolated font/image/resource caching (long-lifecycle processes, multi-tenant scenarios), you can create a standalone `Renderer`, which automatically registers built-in fonts:

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

`create_renderer()` accepts constructor parameters from `takumi_py.Renderer`:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `load_default_fonts` | `bool` | `False` | Whether to load fonts bundled with takumi-py (built-in fonts are always loaded) |
| `fonts` | `list[FontResource]` | `None` | Additional custom fonts to register |
| `cache_max_bytes` | `int \| None` | `None` | Maximum resource cache size (in bytes); `0` disables caching |
| `persistent_images` | `list` | `None` | Persistent image resources |

> Standalone instances bypass the module proxy, so if you want to retain a unified built-in font fallback stack, you must explicitly pass `font_families=takumi.families`. If `font_families` is explicitly passed, the module respects the caller's setting and does not inject the default fallback stack; `RenderOptions(font_families=...)` is also valid.

## Sending Rendered Results

The rendered image is in `bytes` format and can be sent directly via event reply:

```python
from ErisPulse import sdk

takumi = sdk.Takumi
png = takumi.render_html("<div>hello</div>", lang="en")

# Method 1: Reply using Image method
await event.reply(png, method="Image")

# Method 2: Reply using OneBot12 message segment
from ErisPulse.Core.Event import MessageBuilder
await event.reply_ob12(
    MessageBuilder().image(png).build()
)
```

> The adapter handles the image encapsulation for different platforms. See [MessageBuilder Detailed Explanation](../advanced/message-builder.md) and [Send Method Specification](../standards/send-method-spec.md) for more information.

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

# ErisPulse PlatformFeatures Documentation

> Base Protocol: [OneBot12](https://12.onebot.dev/)  
> This document is a **platform-specific feature guide**, including:
> - Examples of chainable Send method calls supported by each adapter
> - Explanations of platform-specific event/message formats
> 
> For general usage, please refer to:
> - [Basic Concepts](../getting-started/basic-concepts.md)
> - [Event Conversion Standard](../standards/event-conversion.md)
> - [API Response Specification](../standards/api-response.md)

---

## Platform-Specific Features

This section is maintained by each adapter developer and describes the differences and extended features of the adapter compared to the OneBot12 standard. Please refer to the detailed documentation for each platform below:

- [Maintain Notes](maintain-notes.md)
- [Yunhu Platform Features](yunhu.md)
- [Yunhu User Platform Features](yunhu_user.md)
- [Telegram Platform Features](telegram.md)
- [OneBot11 Platform Features](onebot11.md)
- [OneBot12 Platform Features](onebot12.md)
- [SnowLuma Platform Features](snowluma.md)
- [Email Platform Features](email.md)
- [Kook (Open Black) Platform Features](kook.md)
- [Matrix Platform Features](matrix.md)
- [Official QQ Bot Platform Features](qqbot.md)
- [Ideaura Coffee Shop](ideaura.md)
- [Discord](discord.md)
- [Webhook Protocol Bridge](webhook.md)
- [WeChat Official Account](wechatmp.md)

> Additionally, there is a `sandbox` adapter, but this adapter does not require a platform-specific feature documentation.

---

## General Interfaces

### Chainable Send Calls
All adapters support the following standard calling methods:

> **Note:** `{AdapterName}` in the documentation must be replaced with the actual adapter name (such as `yunhu`, `telegram`, `onebot11`, `email`, etc.).

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

The methods of the Send DSL return an `asyncio.Task` object, which means you can choose whether to wait for the result immediately:

```python
# Get adapter instance
my_adapter = adapter.get("{AdapterName}")

# Do not wait for the result, the message is sent in the background
task = my_adapter.Send.To("user", "123").Text("Hello")

# If you need to get the sending result, you can wait later
result = await task
```

#### Sending Rule Decorators

In actual development, it is often necessary to: execute subsequent logic only after successful sending, automatically retry on failure, cancel on timeout, and monitor sending progress. The Send DSL includes a set of built-in sending rule decorators, which can be added via chained methods:

| Method | Description |
|--------|-------------|
| `.Hook(callback)` | Callback executed after successful sending (can be called multiple times) |
| `.Retry(times=1)` | Automatic retry on failure N times (total of N+1 attempts, including the first) |
| `.Timeout(seconds)` | Single sending timeout, cancellation on timeout (can be stacked with Retry) |
| `.Defer(seconds)` | Delay sending (in-process timing, not persisted) |
| `.OnProgress(callback)` | Progress callback at each stage, passing SendContext |
| `.OnError(callback)` | Error callback on final failure (triggers only once) |

```python
yunhu = adapter.get("yunhu")

# Deduct points only after successful sending
await (yunhu.Send.To("user", "123")
       .Hook(lambda r: deduct_points("123"))
       .Text("Consumption successful"))

# Retry on failure + timeout cancellation + progress monitoring
def on_progress(ctx):
    print(f"Stage: {ctx.stage}, Attempt: {ctx.attempt + 1}/{ctx.max_attempts}")

task = (yunhu.Send.To("user", "123")
        .Retry(3)              # Retry up to 3 times
        .Timeout(10)           # Timeout of 10 seconds per attempt
        .OnProgress(on_progress)
        .OnError(lambda ctx: notify_admin(ctx.error))
        .Text("Important notice"))
```

Rule methods return `self`, so they must be called before the sending methods (such as Text/Image). `SendContext` contains fields such as `stage` (pending/sending/retrying/success/failed/timeout), `attempt`, `elapsed`, `error`, `result`, which are useful for monitoring.

#### Batch Build Mode (Build)

Multiple sending methods can be built within a single chain, and executed together at the end. This is suitable for scenarios where multiple messages are sent at once:

```python
yunhu = adapter.get("yunhu")

# Build multiple messages and send them together
results = await (yunhu.Send.To("user", "123")
                .Build()                     # Enter build mode
                .Text("Notification 1")
                .Image("pic.jpg")
                .Text("Notification 2")
                .send_all())                 # Execute all at once
# results = [Text result, Image result, Text result]
```

`.send_all()` executes by default **in parallel** (concurrent sending, high efficiency). If the order of message arrival needs to be guaranteed, call `.Sequential()` to execute serially:

```python
# Sequential execution (guarantee order) + retry on failure
await (yunhu.Send.To("group", "456")
       .Build()
       .Sequential()                # Send in order
       .Retry(2)                     # Retry failed entries individually
       .Text("First message").Text("Second message")
       .send_all())
```

Batch execution adopts a **fail-continue** strategy: failure of one message does not interrupt others, and failed entries are automatically retried. Batch also supports `Hook` for the entire batch (triggered after all succeed), `OnError` (triggered when there are failures), and `OnProgress` (progress callback).

> For more detailed information on rules and batch building, please refer to [SendDSL Detailed Explanation](../developer-guide/adapters/send-dsl.md).

### Event Listening
There are three ways to listen to events:

1. Platform-native event listening:
   ```python
   from ErisPulse.Core import adapter, logger
   
   @adapter.on("event_type", raw=True, platform="{AdapterName}")
   async def handler(data):
       logger.info(f"Received raw {AdapterName} event: {data}")
   ```

2. OneBot12 standard event listening:
   ```python
   from ErisPulse.Core import adapter, logger

   # Listen to OneBot12 standard events
   @adapter.on("event_type")
   async def handler(data):
       logger.info(f"Received standard event: {data}")

   # Listen to specific platform's standard events
   @adapter.on("event_type", platform="{AdapterName}")
   async def handler(data):
       logger.info(f"Received {AdapterName} standard event: {data}")
   ```

3. Event module listening:
    Events in the `Event` module are based on the `adapter.on()` function, so the event format provided by `Event` is a OneBot12 standard event.

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

Among these, it is most recommended to use the `Event` module for event handling, because the `Event` module provides rich event types and event handling methods.

---

## Standard Formats
For easy reference, the following are basic event formats. For detailed information, please refer to the links above.

> **Note:** The following formats are basic OneBot12 standard formats. Each adapter may have extended fields based on this. Please refer to the specific feature descriptions of each adapter for details.

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

#### Message Sending Failure
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

We welcome more developers to contribute and maintain adapter documentation! Please follow these steps to submit your contribution:
1. Fork the [ErisPulse](https://github.com/ErisPulse/ErisPulse) repository.
2. Create a Markdown file in the `docs/platform-features/` directory, naming it in the format `<Platform Name>.md`.
3. Add a link to your contributed adapter and related official documentation in this `README.md` file.
4. Submit a Pull Request.

Thank you for your support!



### OneBot11 适配

# OneBot11 Platform Feature Documentation

OneBot11Adapter is an adapter built based on the OneBot V11 protocol.

---

## Document Information

- Corresponding Module Version: 4.4.0
- Maintainer: ErisPulse

## Basic Information

- Platform Introduction: OneBot is a chatbot application interface standard
- Adapter Name: OneBotAdapter
- Supported Protocol/API Version: OneBot V11
- Multi-account Support: Default multi-account architecture, supports configuring and running multiple OneBot accounts simultaneously
- Configuration Key Name: `OneBotAdapter`

## v5 Paradigm Update (4.3.0)

The adapter has completed alignment with the v5 paradigm (incremental upgrade, API compatible):

- **BaseConverter Inheritance**: Common fields of converters (id/time/platform/self/raw) are built by the framework's build_base_event, and are overridden according to OB11 field names (echo/time/self_id).
- **spawn_background Task Ownership**: For Client mode connections, the task now uses runtime.spawn_background (owner assignment, automatic shutdown cleanup).
- **Framework Soft Dependency**: Installing the adapter no longer declares a hard dependency on ErisPulse, avoiding pip resolution issues when adjusting framework versions; at runtime, it checks for ErisPulse>=2.7.1 and logs a warning if the version is too low.
- **Startup Version Log**: Outputs "OneBotAdapter v4.3.0 loaded" during initialization.

Existing capabilities (supported since 4.2.0): Multi-account support, standard action mapping for Api DSL (e.g., get_self_info → get_login_info), Request DSL (friend/group request approval: event.approve() / event.reject()), EventMixin, and i18n.

## Standard API Actions (API DSL)

The adapter automatically maps OneBot12 standard action names to OB11 action names, allowing modules to uniformly invoke actions across platforms:

| OB12 Standard Action | OB11 Action | Description |
|----------------------|-------------|-------------|
| get_self_info | get_login_info | Standardized fields: user_id/user_name/user_displayname |
| get_user_info | get_stranger_info | Standardized fields |
| delete_message | delete_msg | Recall message |
| leave_group | set_group_leave | Leave group |
| get_friend_list | get_friend_list | Action names are consistent, default pass-through |
| get_group_info | get_group_info | Action names are consistent, default pass-through |
| upload_file | upload_group_file / upload_private_file | Optional group_id/user_id parameters, filetype automatically detected and routed to appropriate function |

### Basic Usage

```python
from ErisPulse import sdk
onebot = sdk.adapter.get("onebot11")

# Get bot information
result = await onebot.Api.get_self_info()
print(result["data"]["user_id"], result["data"]["user_name"])

# Recall message
await onebot.Api.delete_message(message_id=123456)

# Upload group file (filetype automatically detected and routed to upload_group_file)
result = await onebot.Api.upload_file(group_id=123456, file="/path/to/file.zip")

# Specify account (multi-account)
result = await onebot.Api.Using("main").get_self_info()

# Unmapped OB11 actions can be called via the call() escape hatch (works with extensions like NapCat/Lagrange)
result = await onebot.Api.call("send_poke", group_id=123, user_id=456)
```

---

## Supported Message Sending Types

All sending methods are implemented using a fluent interface, for example:
```python
from ErisPulse.Core import adapter
onebot = adapter.get("onebot11")

# Send using the default account
await onebot.Send.To("group", group_id).Text("Hello World!")

# Send using a specific account
await onebot.Send.Using("main").To("group", group_id).Text("Message from main account")

# Chained modifiers: @user + reply
await onebot.Send.To("group", group_id).At(123456).Reply(msg_id).Text("Reply message")

# @all members
await onebot.Send.To("group", group_id).AtAll().Text("Announcement message")
```

### Basic Sending Methods

- `.Text(text: str)` : Sends plain text messages.
- `.Image(file: Union[str, bytes], filename: str = "image.png")` : Sends images (supports URL, Base64, or bytes).
- `.Voice(file: Union[str, bytes], filename: str = "voice.amr")` : Sends voice messages.
- `.Video(file: Union[str, bytes], filename: str = "video.mp4")` : Sends video messages.
- `.Face(id: Union[str, int])` : Sends QQ emoticons.
- `.File(file: Union[str, bytes], filename: str = "file.dat")` : Sends files (automatically detects type).
- `.Raw_ob12(message: List[Dict], **kwargs)` : Sends OneBot12 format messages (automatically converts to OB11).
- `.Recall(message_id: Union[str, int])` : Recalls a message.

### Group Operation Methods

The following methods must be used with `To("group", group_id)` to specify the target group, and are executed within the group context:

- `.Kick(user_id, reject_add_request=False)` : Kicks a group member.
- `.Ban(user_id, duration=1800)` : Mutes a group member (duration in seconds; 0 means unmute).
- `.WholeBan(enable=True)` : Enables/Disables global mute for the group.
- `.SetAdmin(user_id, enable=True)` : Sets/unsets a group admin.
- `.SetCard(user_id, card="")` : Sets a group member's nickname.
- `.SetGroupName(name)` : Changes the group name.
- `.Leave(is_dismiss=False)` : Leaves the group (group owner can dismiss).
- `.SetTitle(user_id, title="")` : Sets a group title for a member.
- `.SetPortrait(file)` : Sets the group portrait.

### Query Methods

- `.GetMsg(message_id)` : Retrieves the content of a message.
- `.GetForwardMsg(id)` : Retrieves a forwarded message.
- `.GetLoginInfo()` : Retrieves information about the current logged-in account.
- `.GetFriendList()` : Retrieves the friend list.
- `.GetGroupInfo()` : Retrieves group information (requires `To("group", group_id)`).
- `.GetGroupList()` : Retrieves the list of groups.
- `.GetGroupMemberInfo(user_id)` : Retrieves group member information (requires `To("group", group_id)`).
- `.GetGroupMemberList()` : Retrieves the list of group members (requires `To("group", group_id)`).

### Friend Operation Methods

- `.Like(user_id, times=1)` : Sends a like to a friend (maximum 10 times).

### Chained Modifier Methods (Combinable)

Chained modifier methods return `self`, enabling fluent chaining, and must be called before the final sending method:

- `.At(user_id: Union[str, int], name: str = None)` : Mentions a specific user (can be called multiple times).
- `.AtAll()` : Mentions all group members.
- `.Reply(message_id: Union[str, int])` : Replies to a specific message.

### Chained Call Examples

```python
# Basic sending
await onebot.Send.To("group", 123456).Text("Hello")

# Mention a single user
await onebot.Send.To("group", 123456).At(789012).Text("你好")

# Mention multiple users
await onebot.Send.To("group", 123456).At(111).At(222).At(333).Text("大家好")

# Send a OneBot12 format message
ob12_msg = [{"type": "text", "data": {"text": "Hello"}}]
await onebot.Send.To("group", 123456).Raw_ob12(ob12_msg)

# Send a like
await onebot.Send.Like(123456, times=10)

# Mute a group member
await onebot.Send.To("group", 123456).Ban(789012, duration=3600)

# Unmute
await onebot.Send.To("group", 123456).Ban(789012, duration=0)

# Kick a member
await onebot.Send.To("group", 123456).Kick(789012)

# Set a group admin
await onebot.Send.To("group", 123456).SetAdmin(789012)

# Change group name
await onebot.Send.To("group", 123456).SetGroupName("New Group Name")

# Retrieve group information
result = await onebot.Send.To("group", 123456).GetGroupInfo()

# Specify account for operation
await onebot.Send.Using("main").To("group", 123456).Ban(789012)
```

### Handling Unsupported Types

If an undefined sending method is called, the adapter will return a text prompt:
```python
# Call an unsupported method
await onebot.Send.To("group", 123456).SomeUnsupportedMethod(arg1, arg2)
# Actually sends: "[Unsupported sending type] Method name: SomeUnsupportedMethod, Parameters: [...]"
```

## Request Operations (Request DSL)

The adapter provides a Request Operations DSL for handling approval/rejection of friend requests and group requests (group join/invite).

### Event Shortcut Methods

Request events support `event.approve()` and `event.reject()` shortcut methods, which internally automatically call the Request DSL:

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

### Manual Call to Request DSL

```python
# Approve request
await onebot.Request("flag_string").accept()

# Reject request
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

    # Method 1: Using Event shortcut methods
    if comment == "passphrase":
        await event.approve()
    else:
        await event.reject()

    # Method 2: Using Request DSL
    flag = event.get("flag")
    if comment == "passphrase":
        await onebot.Request(flag).accept()
    else:
        await onebot.Request(flag).reject()
```

### Request Operation Return Value

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
| notice_type: group_ban | `group_ban` | Group ban |
| notice_type: friend_add | `friend_increase` | Friend added |
| notice_type: friend_delete | `friend_decrease` | Friend removed |
| notice_type: group_recall / friend_recall | `message_recall` | Message recall |

### Platform-Specific Events (onebot11_ prefix)

| OB11 Original Type | Converted detail_type | Description |
|--------------------|-----------------------|-------------|
| meta_event_type: lifecycle | `onebot11_lifecycle` | OneBot implementation lifecycle |
| notify + sub_type: honor | `onebot11_honor` | Group honor change |
| notify + sub_type: poke | `onebot11_poke` | Poke |
| notify + sub_type: lucky_king | `onebot11_lucky_king` | Group red packet lucky king |
| Unknown CQ Code Type | Message Segment `onebot11_{type}` | Unrecognized CQ Code |

### Event Examples

```python
// Friend Request
{
  "type": "request",
  "detail_type": "friend",
  "user_id": "789012",
  "comment": "Please add as friend",
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

// Lifecycle (Platform-specific)
{
  "type": "meta_event",
  "detail_type": "onebot11_lifecycle",
  "sub_type": "enable"
}

// Poke (Platform-specific)
{
  "type": "notice",
  "detail_type": "onebot11_poke",
  "group_id": "123456",
  "user_id": "789012",
  "target_id": "345678"
}

// Group Red Packet Lucky King (Platform-specific)
{
  "type": "notice",
  "detail_type": "onebot11_lucky_king",
  "group_id": "123456",
  "user_id": "789012",
  "target_id": "345678"
}

// Honor Change (Platform-specific)
{
  "type": "notice",
  "detail_type": "onebot11_honor",
  "group_id": "123456",
  "user_id": "789012",
  "honor_type": "talkative"
}

// CQ Code Extended Message Segment
{
  "type": "message",
  "message": [
    {"type": "onebot11_shake", "data": {}}
  ]
}
```

### Extension Field Description

- All specific fields are prefixed with `onebot11_`
- Original event data is retained in the `onebot11_raw` field
- Original event type is retained in the `onebot11_raw_type` field
- CQ codes within message content are converted into corresponding message segments (standard types without prefix, unknown types with `onebot11_` prefix)
- Reply messages add a `reply` type message segment
- @ messages add a `mention` type message segment

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
| `is_system_message()` | `bool` | Check if it is a system message (sub_type == "system") |

### Usage Examples

```python
from ErisPulse.Core.Event import message, command

@message.on_group_message()
async def handle_group(event):
    role = event.get_sender_role()
    if role == "admin" or role == "owner":
        await event.reply("Hello, admin!")

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

The OneBot11 adapter adopts a multi-account architecture, where each account is independently configured. The configuration key name is `OneBotAdapter`.

### Account Configuration Fields

| Field | Type | Required | Default | Description |
|------|------|------|--------|------|
| `bot_id` | `str` | Yes | `""` | The robot's QQ number, used to identify the account |
| `mode` | `str` | No | `"server"` | Running mode: `"server"` (passive listening) or `"client"` (active connection) |
| `url` | `str` | No | `"ws://127.0.0.1:3001"` | WebSocket address for Client mode |
| `token` | `str` | No | `""` | Authentication Token (Token for Client mode connection / Token for Server mode verification) |
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

If no account is configured, the adapter will automatically create:
```toml
[OneBotAdapter.accounts.default]
bot_id = ""
mode = "server"
server_path = "/"
enabled = true
```

## Send Method Return Values

All send methods return a Task object, which can be directly awaited to obtain the sending result. The returned result follows the ErisPulse adapter's standardized return specification:

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

The resolution priority for the `account_id` parameter in `call_api` and `Using()`:
1. Exact match with account name
2. Match `bot_id` field
3. Match any `str` type field of the account
4. Fall back to the first enabled account

## Asynchronous Processing Mechanism

The OneBot11 adapter adopts an asynchronous non-blocking design, ensuring that:
1. Message sending does not block the event handling loop.
2. Multiple concurrent sending operations can proceed simultaneously.
3. API responses can be handled promptly.
4. WebSocket connections remain active.
5. Concurrent processing of multiple accounts, with each account running independently.

## Error Handling

The adapter provides a comprehensive error handling mechanism:
1. Automatic reconnection for network connection exceptions (supports independent reconnection for each account, with a 30-second interval)
2. Handling of API call timeouts (fixed 30-second timeout)
3. Automatic retry at intervals when connection fails

## Event Handling Enhancements

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

The adapter automatically maintains the `self_id → account_name` mapping, allowing `event.reply()` to correctly route back to the originating account without manually specifying the account.

## Management Interface

```python
# Get all account information
accounts = onebot.accounts

# Check account connection status
connection_status = {
    account_id: connection is not None and not connection.closed
    for account_id, connection in onebot.connections.items()
}

# Dynamically enable/disable accounts (adapter needs to be restarted)
onebot.accounts["test"].enabled = False
```

## self_id Auto Mapping

The adapter automatically establishes a mapping between OneBot `self_id` (QQ number) and `account_name`, which is used for event routing:

```python
# Automatically completed by the adapter internally
# When an event is received, the self.user_id field is filled with bot_id
# The adapter automatically records: self_id("123456789") → account_name("main")

# Therefore, event.reply() can automatically find the correct account to send messages
@message.on_message()
async def handler(event):
    await event.reply("Automatically routed to the correct account")
```



### OneBot12 适配

# OneBot12 Platform Feature Documentation

OneBot12Adapter is an adapter built based on the OneBot V12 protocol, serving as the baseline protocol adapter for the ErisPulse framework.

---

## Document Information

- Corresponding Module Version: 4.4.0
- Maintainer: ErisPulse
- Protocol Version: OneBot V12

## Basic Information

- Platform Introduction: OneBot V12 is a general chatbot application interface standard and serves as the baseline protocol for the ErisPulse framework.
- Adapter Name: OneBot12Adapter
- Supported Protocol/API Version: OneBot V12
- Multi-Account Support: Fully multi-account architecture, supporting simultaneous configuration and operation of multiple OneBot12 accounts.

## v5 Paradigm Update (4.3.0)

This adapter has completed the alignment with the v5 paradigm (incremental upgrade, API compatible):

- **BaseConverter Inheritance**: Common fields of the converter (id/time/platform/self/raw) are built by the framework build_base_event, and are overwritten by the OB11 field names (echo/time/self_id).
- **spawn_background Task Ownership**: Client mode connection tasks are changed to use runtime.spawn_background (owner ownership, automatic shutdown recovery).
- **Framework Soft Dependency**: Installing the adapter no longer declares a hard dependency on ErisPulse, avoiding pip resolution adjustments for the framework version; ErisPulse>=2.7.1 is detected at runtime and a log warning is issued if the version is too low.
- **Startup Version Log**: Outputs "OneBotAdapter v4.3.0 has been loaded" during initialization.

Existing capabilities (supported since 4.2.0): multi-account, standard action mapping for Api DSL (get_self_info→get_login_info, etc.), Request DSL (friend/group request approval: event.approve() / event.reject()), EventMixin, i18n.

---

## Standard API Actions (Api DSL)

The OneBot12 backend natively supports all OB12 standard action names. The Api DSL defaults to directly delegating call_api for transparent transmission (no mapping required):

```python
from ErisPulse import sdk
ob12 = sdk.adapter.get("onebot12")

result = await ob12.Api.get_self_info()
result = await ob12.Api.get_friend_list()
await ob12.Api.delete_message(message_id="MSG_ID")

# Specify account (multi-account)
result = await ob12.Api.Using("main").get_self_info()

# Platform extension actions
result = await ob12.Api.call("extend_action", param=1)
```

> Supported actions are based on the backend implementation (e.g., NapCat/Lagrange/LLOneBot); unsupported actions return errors from the backend and are transparently passed through.

---

## Request Operations (Request DSL)

Based on the OneBot12 standard handle_quick_request action, handles approval/rejection of friend requests and group invitation requests:

### Event Convenience Methods

```python
from ErisPulse.Core.Event import request

@request.on_friend_request()
async def handle_friend_request(event):
    if event.get("platform") != "onebot12":
        return
    comment = event.get("comment", "")
    if comment == "passphrase":
        await event.approve()      # Approve
    else:
        await event.reject()       # Reject
```

### Manual Request DSL Calls

```python
await ob12.Request("request_flag").accept()
await ob12.Request("request_flag").reject()
await ob12.Request("request_flag").Using("main").accept()
```

---

## Supported Message Sending Types

All sending methods are implemented through chain syntax, for example:

```python
from ErisPulse.Core import adapter
onebot12 = adapter.get("onebot12")

# Send using the default account
await onebot12.Send.To("group", group_id).Text("Hello World!")

# Send using a specific account
await onebot12.Send.To("group", group_id).Account("main").Text("Message from main account")
```

### Case-Insensitive Method Calls

All sending methods and chain modifiers support case-insensitive calls, and the adapter automatically maps them to the correct standard method names:

```python
# All the following calls are equivalent
await onebot12.Send.To("user", 123).Text("hello")
await onebot12.Send.To("user", 123).text("hello")
await onebot12.Send.To("user", 123).TEXT("hello")

# Chain modifiers are also supported
await onebot12.Send.To("group", 123).At(456).Text("hello")
await onebot12.Send.To("group", 123).at(456).TEXT("hello")
await onebot12.Send.To("group", 123).AT(456).text("hello")
```

### Unsupported Method Calls

When calling an unsupported method, the adapter returns a friendly text message instead of throwing an exception:

```python
# Call an unsupported method
result = await onebot12.Send.To("user", 123).UnsupportedMethod("test")

# The returned result is a sent text message
# Message content: [Unsupported send type] Method name: UnsupportedMethod, Parameter: [args[0]: 'test']
```

### Basic Message Types

- `.Text(text: str)`: Send plain text message
- `.Image(file: Union[str, bytes], filename: str = "image.png")`: Send image message (supports URL, Base64, or bytes)
- `.Audio(file: Union[str, bytes], filename: str = "audio.ogg")`: Send audio message
- `.Voice(file: Union[str, bytes], filename: str = "voice.ogg")`: Send voice message (alias for Audio, compatible with OneBot11)
- `.Video(file: Union[str, bytes], filename: str = "video.mp4")`: Send video message

### Chain Modifier Methods (Return self to support chain calls)

- `.At(user_id: Union[str, int])`: @ user (can be called multiple times)
- `.AtAll()`: @ all members
- `.Reply(message_id: Union[str, int])`: Reply to message

### Raw Message Sending

- `.Raw_ob12(message: Union[Dict, List[Dict]], **kwargs)`: Send OneBot12 raw format message (conforms to naming conventions)

### Other Message Types

- `.Sticker(file_id: str)`: Send sticker/emoticon
- `.Location(latitude: float, longitude: float, title: str = "", content: str = "")`: Send location

### Management Functions

- `.Recall(message_id: Union[str, int])`: Recall message
- `.Edit(message_id: Union[str, int], content: Union[str, List[Dict]])`: Edit message
- `.Raw(message_segments: List[Dict])`: Send native OneBot12 message segments
- `.Batch(target_ids: List[str], message: Union[str, List[Dict]], target_type: str = "user")`: Batch send messages

## OneBot12 Standard Events

The OneBot12 adapter fully complies with the OneBot12 standard, and event formats do not require conversion, being directly submitted to the framework.

### New Feature: Raw Event Type Field

Conforms to the `standards/event-conversion.md` specification, all events will retain the raw event type field `onebot12_raw_type`:

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
    "comment": "application message",
    "flag": "request-flag",
    "time": 1234567890
}

# Group invitation request
{
    "id": "event-id",
    "type": "request",
    "onebot12_raw_type": "request",
    "detail_type": "group",
    "self": {"user_id": "bot-id"},
    "group_id": "group-id",
    "user_id": "user-id",
    "comment": "application message",
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

Each account independently configures the following options:

- `mode`: The running mode of this account ("server" or "client")
- `server_path`: WebSocket path in Server mode
- `server_token`: Authentication token in Server mode (optional)
- `client_url`: WebSocket address to connect in Client mode
- `client_token`: Authentication token in Client mode (optional)
- `enabled`: Whether to enable this account
- `platform`: Platform identifier, default is "onebot12"
- `implementation`: Implementation identifier, such as "go-cqhttp" (optional)

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

If no account is configured, the adapter will automatically create:

```toml
[OneBotv12_Adapter.accounts.default]
mode = "server"
server_path = "/onebot12"
enabled = true
platform = "onebot12"
```

## Send Method Return Values

### Message Sending Methods
All message sending methods (such as `.Text()`, `.Image()`, `.Raw_ob12()`, etc.) return an `asyncio.Task` object, which can be directly awaited to get the sending result:

```python
task = await onebot12.Send.To("group", 123456).Text("Hello")
```

### Chain Modifier Methods
All chain modifier methods (such as `.At()`, `.AtAll()`, `.Reply()`) return `self`, supporting chain calls:

```python
# Combine multiple modifier methods
await onebot12.Send.To("group", 123456).Reply("msg123").At(789).At(790).Text("text")
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
    "echo": "1234",               // Optional: echo returned as-is from the request
    "onebot12_raw": {...}        // Optional: raw response data
}

# Failure response
{
    "status": "failed",           // Required: execution status
    "retcode": 10003,            // Required: return code (non-zero indicates failure)
    "data": None,                // Required: null on failure
    "message_id": "",            // Required: empty string on failure
    "message": "Missing required parameter",    // Required: error description
    "echo": "1234",              // Optional: echo returned as-is from the request
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
# Account selection methods
await onebot12.Send.Using("main").To("group", 123456).Text("Main account message")
await onebot12.Send.Using("backup").To("group", 123456).Image("http://example.com/image.jpg")

# API call method
await onebot12.call_api("send_message", account_id="main", 
    detail_type="group", group_id=123456, 
    content=[{"type": "text", "data": {"text": "Hello"}}])
```

## Asynchronous Processing Mechanism

The OneBot12 adapter uses an asynchronous non-blocking design:

1. Message sending does not block the event handling loop.
2. Multiple concurrent sending operations can be performed simultaneously.
3. API responses are handled promptly.
4. WebSocket connections remain active.
5. Multi-account concurrent processing, with each account running independently.

## Error Handling

The adapter provides a comprehensive error handling mechanism:

1. Network connection exceptions are automatically reconnected (supports independent reconnection for each account, with a 30-second interval).
2. API call timeout handling (fixed 30-second timeout).
3. Message sending failures are automatically retried (up to 3 retries).
4. Calls to unsupported methods return friendly text prompts.

## Event Handling Enhancement

In multi-account mode, all events are automatically appended with account information:

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
# Get all account information
accounts = onebot12.accounts

# Check account connection status
connection_status = {
    account_id: connection is not None and not connection.closed
    for account_id, connection in onebot12.connections.items()
}

# Dynamically enable/disable accounts (requires adapter restart)
onebot12.accounts["test"].enabled = False
```

## OneBot12 Standard Features

### Message Segment Standard

OneBot12 uses standardized message segment formats:

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

Follows OneBot12 standard API specifications:

- `send_message`: Send message
- `delete_message`: Recall message
- `edit_message`: Edit message
- `get_message`: Get message
- `get_self_info`: Get self information
- `get_user_info`: Get user information
- `get_group_info`: Get group information

## Best Practices

1. **Configuration Management**: It is recommended to use multi-account configuration to separate management of robots with different purposes.
2. **Error Handling**: Always check the return status of API calls.
3. **Message Sending**: Use appropriate message types and avoid sending unsupported messages.
4. **Connection Monitoring**: Regularly check connection status to ensure service availability.
5. **Performance Optimization**: Use the Batch method for batch sending to reduce network overhead.
6. **Method Calls**: Standard camelCase naming (e.g., `.Text()`) is recommended, but lowercase forms are also supported for compatibility with different programming styles (this may be incompatible with older versions).



### Telegram 适配

# Telegram Platform Feature Documentation

TelegramAdapter is an adapter built on top of the Telegram Bot API, supporting multiple message types and event handling.

---

## Document Information

- Corresponding Module Version: 4.3.0
- Maintainer: ErisPulse

## Basic Information

- Platform Overview: Telegram is a cross-platform instant messaging application
- Adapter Name: TelegramAdapter
- Supported Protocol/API Version: Telegram Bot API
- Session Type Mapping: `private` → use `user` when sending, `group`/`supergroup` → `group`, `channel` → `channel`

## Standard API Actions (API DSL)

The adapter maps OB12 standard actions to the Telegram Bot API and standardizes the data field:

| OB12 Standard Action | Telegram API | Data Field |
|----------------------|--------------|------------|
| get_self_info | getMe | user_id / user_name / user_displayname |
| get_user_info(user_id) | getChat | user_id / user_name / user_displayname |
| get_group_info(group_id) | getChat | group_id / group_name |
| get_group_member_info(group_id, user_id) | getChatMember | user_id / user_name / telegram_role |
| delete_message(message_id) | deleteMessage | chat_id automatically completed via message registry |
| leave_group(group_id) | leaveChat | - |

Extended actions: get_group_admin_list(group_id) (admin list), get_chat_member_count(chat_id) (member count).

```python
from ErisPulse import sdk
telegram = sdk.adapter.get("telegram")

result = await telegram.Api.get_self_info()
result = await telegram.Api.get_group_info(group_id=-100123)
result = await telegram.Api.get_group_admin_list(-100123)
await telegram.Api.delete_message(message_id=55)   # chat_id automatically completed
result = await telegram.Api.Using("main").get_self_info()
```

> Telegram Bot API does not provide an interface to retrieve friend or group lists; get_friend_list/get_group_list returns code=10002.

---

## Request Operations (Request DSL)

Handles group join requests (chat_join_request event), based on approveChatJoinRequest / declineChatJoinRequest:

```python
from ErisPulse.Core.Event import request

@request.on_request()
async def handle_join_request(event):
    if event.get("platform") != "telegram":
        return
    # event["request_id"] is a synthesized identifier (tjr_{chat_id}_{user_id}_{date})
    if event.get("user_nickname"):
        await event.approve()          # Approve
    # await event.reject()             # Reject

# Manual invocation (must have received corresponding request event to register context)
await telegram.Request(event["request_id"]).accept()
await telegram.Request(event["request_id"]).reject()
await telegram.Request(event["request_id"]).Using("main").accept()
```

---

## Supported Message Sending Types

All sending methods use a fluent interface, for example:
```python
from ErisPulse.Core import adapter
telegram = adapter.get("telegram")

await telegram.Send.To("user", user_id).Text("Hello World!")
```

### Basic Sending Methods

| Method | Description | Parameters |
|--------|-------------|------------|
| `.Text(text)` | Send plain text message | `text: str` |
| `.Face(emoji)` | Send emoji dice | `emoji: str` (e.g. 🎲 🎯 🏀) |
| `.Markdown(text, content_type)` | Send Markdown formatted message | `content_type` defaults to `"MarkdownV2"` |
| `.HTML(text)` | Send HTML formatted message | `text: str` |
| `.MergeForward(nodes, title)` | Send merged forward message (title + each blockquote block, truncated at 4096) | `nodes: List[Dict]`, `title: str` |
| `.Sticker(file)` | Send sticker | `file: str (file_id/URL) \| bytes` |
| `.Location(lat, lng)` | Send location | `latitude: float, longitude: float` |
| `.Venue(lat, lng, title, addr)` | Send venue | Includes title and address |
| `.Contact(phone, first, last)` | Send contact | Includes phone number and name |

### Media Sending Methods

All media methods support both `bytes` (upload) and `str` (file_id / URL) inputs:

| Method | Description |
|--------|-------------|
| `.Image(file, caption, content_type)` | Send image |
| `.Video(file, caption, content_type)` | Send video |
| `.Voice(file, caption)` | Send voice |
| `.Audio(file, caption, content_type)` | Send audio |
| `.File(file, caption)` | Send file |
| `.Document(file, caption, content_type)` | Alias for File |

### Message Management Methods

| Method | Description |
|--------|-------------|
| `.Edit(message_id, text, content_type)` | Edit existing message |
| `.Recall(message_id)` | Delete specified message |
| `.Forward(from_chat_id, message_id)` | Forward message (retaining source) |
| `.CopyMessage(from_chat_id, message_id)` | Copy message (without source) |
| `.AnswerCallback(callback_query_id, text, show_alert)` | Respond to callback query |

### Raw Message Sending

- `.Raw_ob12(message: List[Dict])`: Send OneBot12 standard format message
- `.Raw_json(json_str: str)`: Send raw JSON format message

### Fluent Modifier Methods

| Method | Description |
|--------|-------------|
| `.At(user_id)` | @ specified user (implemented via Telegram entities, can be called multiple times) |
| `.AtAll()` | @ all members (send `@All` text) |
| `.Reply(message_id)` | Reply to specified message |
| `.Keyboard(inline_keyboard)` | Set inline keyboard (`list[list[dict]]`) |
| `.ProtectContent(protect)` | Protect content (prevent forwarding and saving) |
| `.Silent(silent)` | Silent send (no notification to user) |

### Sending Examples

```python
# Basic text sending
await telegram.Send.To("user", user_id).Text("Hello World!")

# Message with inline keyboard
from ErisPulse import sdk
telegram = sdk.adapter.get("telegram")
keyboard = [
    [{"text": "Button 1", "callback_data": "btn1"}, {"text": "Button 2", "callback_data": "btn2"}],
    [{"text": "Visit Website", "url": "https://example.com"}],
]
await telegram.Send.To("group", group_id).Keyboard(keyboard).Text("Please select:")

# Media sending (URL method)
await telegram.Send.To("group", group_id).Image("https://example.com/image.jpg", caption="Image")

# @ user
await telegram.Send.To("group", group_id).At("6117725680").Text("Hello!")

# Reply + protect content
await telegram.Send.To("group", group_id).Reply("12345").ProtectContent().Text("Confidential message")

# Silent send
await telegram.Send.To("group", group_id).Silent().Text("Silent notification")

# Respond to callback query
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

## Platform-Specific Event Types

Telegram events are converted following the OneBot12 standard, with platform extensions provided via the `telegram_` prefix.

### Message Event detail_type Mapping

| Telegram chat.type | OneBot12 detail_type | Sending Target Type |
|---|---|---|
| `private` | `private` | `user` |
| `group` | `group` | `group` |
| `supergroup` | `group` | `group` |
| `channel` | `channel` | `channel` |

### Platform-Specific Event Types

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

Converted message segments use OneBot12 standard format:

| Message Segment Type | Description | Data Field |
|---|---|---|
| `text` | Plain text (without @username) | `text` |
| `mention` | @ user (standard OB12) | `user_id`, `user_name` |
| `reply` | Reply reference | `message_id`, `user_id` |
| `image` | Image | `file_id`, `url` |
| `video` | Video | `file_id`, `url`, `duration`, `width`, `height` |
| `voice` | Voice | `file_id`, `url`, `duration` |
| `audio` | Audio | `file_id`, `url`, `duration`, `title`, `performer` |
| `file` | File | `file_id`, `url`, `file_name`, `file_size`, `mime_type` |
| `location` | Location | `latitude`, `longitude`, optional `title`, `address` |

### Platform Extension Message Segments

Message segments with `telegram_` prefix:

| Message Segment Type | Description | Data Field |
|---|---|---|
| `telegram_sticker` | Sticker | `file_id`, `emoji`, `sticker_type`, `url` |
| `telegram_animation` | GIF animation | `file_id`, `url`, `duration`, `caption` |
| `telegram_contact` | Contact | `phone_number`, `first_name`, `last_name`, `user_id` |
| `telegram_inline_keyboard` | Inline keyboard | `inline_keyboard` |

### Event Examples

#### Group Message (with @ mention)
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
    {"type": "text", "data": {"text": "Please select:"}},
    {
      "type": "telegram_inline_keyboard",
      "data": {
        "inline_keyboard": [
          [{"text": "Button 1", "callback_data": "btn1"}],
          [{"text": "Visit", "url": "https://example.com"}]
        ]
      }
    }
  ]
}
```

## Event Mixin Extension Methods

The adapter registers the following platform-specific methods, available only when `platform == "telegram"`:

### Message-related

| Method | Return Type | Description |
|--------|-------------|-------------|
| `is_bot_message()` | `bool` | Check if message is from bot |
| `is_edited_message()` | `bool` | Check if message is edited |
| `is_topic_message()` | `bool` | Check if message is topic/Topic message |
| `get_update_id()` | `int` | Get Telegram update ID |
| `get_chat_title()` | `str` | Get chat title |
| `get_chat_username()` | `str` | Get chat username |
| `get_forward_from()` | `dict` | Get forwarding source info |
| `get_topic_id()` | `str` | Get topic ID |

### Callback Query-related

| Method | Return Type | Description |
|--------|-------------|-------------|
| `get_callback_data()` | `str` | Get callback query's callback_data |
| `get_callback_id()` | `str` | Get callback query ID (used for response) |

### Message Segment Data Extraction

| Method | Return Type | Description |
|--------|-------------|-------------|
| `get_inline_keyboard()` | `list` | Get inline keyboard from message |
| `get_sticker_info()` | `dict` | Get sticker info |
| `get_contact_info()` | `dict` | Get contact info |
| `get_location()` | `dict` | Get location info |

### Usage Example

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

    # Chat info
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

        # Respond to callback query
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
- Private messages use `detail_type="private"` (must be converted to `user` when sending)
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

The Telegram adapter only supports **Polling (polling)** mode; Webhook mode has been removed.

### Proxy Configuration

If you need to connect to the Telegram API through a proxy, use system-level proxy (environment variables `ALL_PROXY` / `HTTPS_PROXY`).

### Migration from Old Configuration

Old single-token configuration is automatically compatible:
```toml
# Old format (still usable, but migration is recommended)
[Telegram_Adapter]
token = "YOUR_BOT_TOKEN"
```

Migration is recommended to the new format:
```toml
[Telegram_Adapter.accounts.default]
token = "YOUR_BOT_TOKEN"
enabled = true
```



### 云湖适配

# Yunhu Platform Features Documentation

YunhuAdapter is an adapter built on the Yunhu protocol, integrating all Yunhu functional modules and providing a unified interface for event handling and message operations.

---

## Document Information

- Corresponding Module Version: 4.5.0
- Maintainer: ErisPulse

## Basic Information

- Platform Overview: Yunhu is an enterprise-level instant messaging platform
- Adapter Name: YunhuAdapter
- Multi-account Support: Supports multiple Yunhu robot accounts identified and configured via bot_id
- Chainable Modifiers: Supports chainable modifier methods such as `.Reply()`
- OneBot12 Compatibility: Supports sending OneBot12 format messages

## v5 Paradigm Update (4.4.0)

This adapter has completed alignment with the v5 paradigm (incremental upgrade, API compatible):

- **Official Server-side API Set** (Api DSL extension methods): Edit messages, batch sending, message lists, user/global dashboards, group member mute, remove group members, group message type control, group tag CRUD, user tagging
- **Standard keyboard segment** (cross-platform interaction component standard): {"type": "keyboard", "data": {"rows": [[{"label", "type": "callback|link", "data"}]]}} segment automatically converted to Yunhu buttons; .Buttons(rows) / .Keyboard(rows) modifiers accept generic structure (native structure backward compatibility)
- **Interaction callback standard fields**: Button click/A2UI events include standard fields interaction_id / button_data
- **spawn_background task ownership**: WS connection tasks use runtime.spawn_background
- **Framework soft dependency**: Runtime detection of ErisPulse>=2.7.1 and prompt; version logs output on startup

### Platform Extension Actions (call / Api methods)

```python
from ErisPulse import sdk
yunhu = sdk.adapter.get("yunhu")

# Api methods (official server-side API)
await yunhu.Api.edit_message(msg_id, recv_id, "group", "text", {"text": "New Content"})
await yunhu.Api.batch_send(["userId1", "userId2"], "text", {"text": "Announcement"})
await yunhu.Api.get_message_list(group_id, "group", before=10)
await yunhu.Api.set_user_board(chat_id, "group", "Dashboard Content", expire_time=3600)
await yunhu.Api.dismiss_global_board()
await yunhu.Api.gag_group_member(group_id, user_id, 600)      # Mute for 600 seconds, 0=unmute
await yunhu.Api.remove_group_member(group_id, user_id)
await yunhu.Api.set_group_msg_type_limit(group_id, "text,image")
await yunhu.Api.create_group_tag(group_id, "VIP", color="#FF5733")
await yunhu.Api.add_user_tag(group_id, user_id, "VIP")

# Button click callback (standard fields)
from ErisPulse.Core.Event import notice

@notice.on_notice()
async def handle_button(event):
    if event.get("platform") == "yunhu" and event.get("button_data"):
        data = event["button_data"]     # Cross-platform unified value retrieval
        interaction_id = event["interaction_id"]
```

> Complete standard documentation is available at [Cross-platform Interaction Component Standard](../standards/standardization-guide.md).

---

## Supported Message Sending Types

All sending methods are implemented through chainable syntax, for example:
```python
from ErisPulse.Core import adapter
yunhu = adapter.get("yunhu")

await yunhu.Send.To("user", user_id).Text("Hello World!")
```

Supported sending types include:
- `.Text(text: str)`: Send plain text messages.
- `.Html(html: str)`: Send HTML formatted messages.
- `.Markdown(markdown: str)`: Send Markdown formatted messages.
- `.MergeForward(nodes, title="Merged Chat Record")`: Send merged forward messages (rendered as `<details>` collapsible HTML cards, sent via html channel).
- `.A2UI(text: str)`: Send A2UI formatted messages.
- `.Image(file: bytes, stream: bool = False, filename: str = None)`: Send image messages, supporting stream upload and custom filename.
- `.Video(file: bytes, stream: bool = False, filename: str = None)`: Send video messages, supporting stream upload and custom filename.
- `.File(file: bytes, stream: bool = False, filename: str = None)`: Send file messages, supporting stream upload and custom filename.
- `.Batch(target_ids: List[str], message: str, content_type: str = "text", **kwargs)`: Batch send messages.
- `.Edit(msg_id: str, text: str, content_type: str = "text", buttons: List = None)`: Edit existing messages.
- `.Recall(msg_id: str)`: Recall messages.
- `.Board(content: str, content_type: str = "text")`: Publish dashboard announcements. Scope inferred by `To()` (specified target=local dashboard, unspecified=global dashboard). Chainable modifiers: `.Expire(duration)` relative expiration (seconds), `.ExpireAt(timestamp)` absolute expiration (second-level timestamp), `.ForMember(member_id)` group member dashboard; **automatically撤销 dashboard when content is empty**. Still compatible with old-style `Board("local", "announcement")` explicit scope writing.
- `.DismissBoard()`: Recall dashboard announcements. Scope inferred by `To()`, supports `.ForMember(member_id)`; still compatible with old-style `DismissBoard("local")` writing.
- `.Stream(content_type: str, content_generator: AsyncGenerator, **kwargs)`: Send streaming messages.

### Group Management Methods

All group management methods require chainable syntax to specify the group, for example:
```python
from ErisPulse.Core import adapter
yunhu = adapter.get("yunhu")

await yunhu.Send.To("group", group_id).Kick(user_id)
```

- `.Kick(user_id: str)`: Remove group member. The bot needs `Allow removing group members` permission.
- `.Ban(user_id: str, duration: int = 600)`: Mute user. `duration` is mute duration (seconds), 0 is unmute, -1 is permanent mute. The bot needs `Allow muting users` permission.
- `.CreateTag(tag: str, color: str = None, desc: str = None, sort: int = None)`: Create group tag. `color` format is #RRGGBB, `sort` smaller is more front. The bot needs `Allow controlling tag group` permission.
- `.EditTag(tag: str, new_tag: str = None, color: str = None, desc: str = None, sort: int = None)`: Modify group tag. Optional parameters, not passed means no modification. The bot needs `Allow controlling tag group` permission.
- `.DeleteTag(tag: str)`: Delete group tag. The bot needs `Allow controlling tag group` permission.
- `.GetTagList()`: Get group tag list. Returns response data containing `list` array.
- `.AddUserTag(user_id: str, tag: str)`: Add tag to user. The bot needs `Allow controlling tag group` permission.
- `.RemoveUserTag(user_id: str, tag: str)`: Remove tag from user. The bot needs `Allow controlling tag group` permission.
- `.SetMsgTypeLimit(types: str)`: Control group message types. `types` is message type name, multiple separated by commas (e.g. "text,image,video"), empty string means no restriction. The bot needs `Allow modifying group information` permission.

### Message Query Methods

Get historical messages of specified session (user/group), need chainable syntax to specify target, for example:
```python
from ErisPulse.Core import adapter
yunhu = adapter.get("yunhu")

result = await yunhu.Send.To("group", group_id).GetMessages(before=10)
```

- `.GetMessages(message_id: str = None, before: int = None, after: int = None)`: Get session history messages. Returns response data containing `list` array and `total` count.
  - `message_id`: Message ID (optional). Not filled in with `before` returns the latest N messages.
  - `before`: Returns N messages before the specified message ID.
  - `after`: Returns N messages after the specified message ID.
  - > **Note:** At least one of `before` and `after` must be specified and greater than 0, otherwise the server will not return any message.

Board scope inferred by `To()` automatically:
- Specified `To(target_type, target_id)` → Local dashboard (specified user/group)
- Unspecified `To()` → Global dashboard

```python
# Local dashboard (expires in 60 seconds relatively)
await yunhu.Send.To("group", group_id).Expire(60).Board("Announcement", content_type="markdown")

# Group member dashboard (visible only to specified member)
await yunhu.Send.To("group", group_id).ForMember(user_id).Board("Visible only to you")

# Absolute timestamp expiration
await yunhu.Send.To("group", group_id).ExpireAt(1785208268).Board("Expires at specified time")

# Global dashboard
await yunhu.Send.Board("Global Announcement")

# Clear local dashboard (empty content → automatically recall)
await yunhu.Send.To("group", group_id).Board("")
```

### Button Parameter Description

The `buttons` parameter is a nested list representing button layout and functionality. Each button object contains the following fields:

| Field        | Type   | Required | Description                                                                 |
|--------------|--------|----------|-----------------------------------------------------------------------------|
| `text`       | string | Yes      | Text on the button                                                          |
| `actionType` | int    | Yes      | Action type:<br>`1`: Navigate URL<br>`2`: Copy<br>`3`: Report click         |
| `url`        | string | No       | Used when `actionType=1`, represents the target URL for navigation          |
| `value`      | string | No       | When `actionType=2`, this value is copied to clipboard<br>When `actionType=3`, this value is sent to the subscriber |

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
> - Only events reported by clicking the **Report Event** button will receive a push notification; neither **Copy** nor **Navigate URL** will trigger a push notification.

### Chainable Modifier Methods (can be combined)

Chainable modifier methods return `self`, supporting chained calls, must be called before the final sending method:

- `.Reply(message_id: str)`: Reply to a specific message.
- `.At(user_id: str)`: @ a specific user.
- `.AtAll()`: @ all users.
- `.Buttons(buttons: List)`: Add buttons.

### Chained Call Example

```python
# Basic sending
await yunhu.Send.To("user", user_id).Text("Hello")

# Reply to message
await yunhu.Send.To("group", group_id).Reply(msg_id).Text("Reply message")

# Reply + buttons
await yunhu.Send.To("group", group_id).Reply(msg_id).Buttons(buttons).Text("Message with reply and buttons")
```

### Group Management Examples

```python
from ErisPulse.Core import adapter
yunhu = adapter.get("yunhu")

# Remove group member
await yunhu.Send.To("group", group_id).Kick(user_id)

# Mute user (10 minutes)
await yunhu.Send.To("group", group_id).Ban(user_id, duration=600)

# Unmute
await yunhu.Send.To("group", group_id).Ban(user_id, duration=0)

# Permanent mute
await yunhu.Send.To("group", group_id).Ban(user_id, duration=-1)

# Create group tag
await yunhu.Send.To("group", group_id).CreateTag("VIP User", color="#FF5733", desc="VIP Member")

# Modify group tag
await yunhu.Send.To("group", group_id).EditTag("VIP User", new_tag="SVIP User", color="#33C4FF")

# Delete group tag
await yunhu.Send.To("group", group_id).DeleteTag("VIP User")

# Get group tag list
result = await yunhu.Send.To("group", group_id).GetTagList()

# Add tag to user
await yunhu.Send.To("group", group_id).AddUserTag(user_id, "VIP User")

# Remove tag from user
await yunhu.Send.To("group", group_id).RemoveUserTag(user_id, "VIP User")

# Set message type limit
await yunhu.Send.To("group", group_id).SetMsgTypeLimit("text,image,video")

# Clear message type limit
await yunhu.Send.To("group", group_id).SetMsgTypeLimit("")
```

### Message Query Examples

```python
from ErisPulse.Core import adapter
yunhu = adapter.get("yunhu")

# Get 10 recent messages from the group (returns 10 in total)
result = await yunhu.Send.To("group", group_id).GetMessages(before=10)

# Get 10 messages before the specified message ID from the group (returns 11 in total)
result = await yunhu.Send.To("group", group_id).GetMessages(message_id="msg_xxx", before=10)

# Get 10 messages before and after the specified message ID from the group (returns 21 in total)
result = await yunhu.Send.To("group", group_id).GetMessages(message_id="msg_xxx", before=10, after=10)

# Get history messages from user session
result = await yunhu.Send.To("user", user_id).GetMessages(message_id="msg_xxx", before=10)
```

### OneBot12 Message Support

The adapter supports sending OneBot12 formatted messages, facilitating cross-platform message compatibility:

- `.Raw_ob12(message: List[Dict], **kwargs)`: Send OneBot12 formatted messages.

```python
# Send OneBot12 formatted message
ob12_msg = [{"type": "text", "data": {"text": "Hello"}}]
await yunhu.Send.To("user", user_id).Raw_ob12(ob12_msg)

# Combined with chainable modifiers
ob12_msg = [{"type": "text", "data": {"text": "Reply message"}}]
await yunhu.Send.To("group", group_id).Reply(msg_id).Raw_ob12(ob12_msg)
```

## Standard API Actions (ApiDSL)

> [!NOTE]
> This feature requires ErisPulse **2.7.0+** and YunhuAdapter **4.3.0+**.

In addition to `Send` chainable sending, the adapter provides an `Api` internal class, exposing OneBot12 standard API actions and Yunhu platform extension actions. All methods return standard response format.

```python
from ErisPulse.Core import adapter
yunhu = adapter.get("yunhu")

# Information query (via public Web API, no authentication required)
result = await yunhu.Api.get_self_info()              # Robot self information
result = await yunhu.Api.get_user_info("7058262")     # Any user information
result = await yunhu.Api.get_group_info("635409929")  # Group information

# File operations
result = await yunhu.Api.upload_file(type="path", name="a.png", path="./a.png")
result = await yunhu.Api.get_file("https://chat-file.jwznb.com/xxx")

# Recall message (requires additional chat_id + chat_type)
await yunhu.Api.delete_message("msg_id", chat_id="123", chat_type="group")

# Multi-account: specify Bot account
info = await yunhu.Api.Using("bot1").get_self_info()
```

### Supported Standard Actions

| Method | Description | Data Source |
|--------|-------------|-------------|
| `get_self_info()` | Robot self information | Public Web API (bot-info) |
| `get_user_info(user_id)` | User information (any user can query) | Public Web API (user/homepage) |
| `get_group_info(group_id)` | Group information | Public Web API (group-info) |
| `upload_file(*, type, name, ...)` | Upload file (automatically determine image/video/file) | Bot Open API |
| `get_file(file_id)` | Get file (file_id is URL) | — |
| `delete_message(message_id, *, chat_id, chat_type)` | Recall message | Bot Open API (/bot/recall) |

> **Note:** `get_self_info` / `get_user_info` / `get_group_info` are implemented through **non-official public Web API** (chat-web-go.jwzhd.com). These interfaces do not require authentication but are not official documentation and may change with platform updates; failures return standard error responses.

### Unsupported Standard Actions

The following standard actions have no corresponding API in Yunhu, and calling them returns `retcode=10002` (unsupported operation):
- `get_friend_list` (Bot Open API's "robot user list" is still in pending launch status)
- `get_group_list` / `get_group_member_info` / `get_group_member_list`
- `set_group_name` / `leave_group`

### Platform Extension Actions

Call Yunhu-specific actions through `Api.call("yunhu.xxx", **params)` (parameters use OB12-style naming, adapter automatically translates to Yunhu fields):

| Extension Action | Description | Equivalent Send Method |
|------------------|-------------|------------------------|
| `yunhu.recall` | Recall message (msg_id, chat_id, chat_type) | `Send.To(...).Recall(msg_id)` |
| `yunhu.kick` | Remove group member (group_id, user_id) | `Send.To("group", g).Kick(uid)` |
| `yunhu.ban` | Mute (group_id, user_id, duration) | `Send.To("group", g).Ban(uid, duration)` |
| `yunhu.unban` | Unmute (group_id, user_id) | `Send.To("group", g).Ban(uid, duration=0)` |
| `yunhu.tag.create/edit/delete/list` | Group tag CRUD (group_id, ...) | `Send.To("group", g).CreateTag(...)` etc. |
| `yunhu.tag.relate` / `yunhu.tag.relate_cancel` | Add/remove tag from user | `Send.To("group", g).AddUserTag(...)` etc. |
| `yunhu.set_member_title` / `yunhu.unset_member_title` | **Member title semantic alias** (tag ≈ title, internally mapped to tag.relate) | — |
| `yunhu.msg_type_limit` | Group message type limit (group_id, type) | `Send.To("group", g).SetMsgTypeLimit(...)` |
| `yunhu.get_messages` | Get history messages (chat_id, chat_type, message_id?, before?, after?) | `Send.To(...).GetMessages(...)` |
| `yunhu.bot_info` | Public bot-info query (bot_id) | — |
| `yunhu.user_homepage` | Public user homepage query (user_id) | — |

```python
# Platform extension example
await yunhu.Api.call("yunhu.kick", group_id="123", user_id="456")
await yunhu.Api.call("yunhu.set_member_title", group_id="123", user_id="456", title="VIP")
result = await yunhu.Api.call("yunhu.get_messages", chat_id="123", chat_type="group", before=10)
```

> **Tags and Titles:** Yunhu's "tag" semantics are equivalent to OneBot12 group member `title`. `yunhu.set_member_title` is a native semantic alias for `yunhu.tag.relate`, both internally mapped to the same endpoint. In group message events, the sender's role is mapped to the standard `role` field (`owner/admin/member`) from Yunhu's `senderUserLevel`.

## Send Method Return Values

All send methods return a Task object, which can be awaited directly to get the send result. The returned result follows ErisPulse adapter standardized return specifications:

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

## Platform-Specific Event Types

Platform-specific features should be used only after checking platform=="yunhu"

### Core Differences

1. Platform-specific event types:
    - Forms (e.g., form commands): yunhu_form
    - Emoji/pack messages: yunhu_expression
    - Button clicks: yunhu_button_click
    - A2UI button clicks: yunhu_a2ui_button
    - Bot settings: yunhu_bot_setting
    - Quick menus: yunhu_shortcut_menu
2. Standard field extensions (4.3.0+):
    - Message events add standard `role` field (mapped from Yunhu `senderUserLevel` to `owner`/`admin`/`member`)
    - New `user_avatar` field (sender's avatar URL)
3. Extension fields:
    - All platform-specific fields are prefixed with yunhu_
    - Original data is preserved in the yunhu_raw field
    - In private chats, self.user_id represents the bot ID

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
      "Field ID1": {
        "id": "Field ID1",
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

# A2UI button event
{
  "type": "notice",
  "detail_type": "yunhu_a2ui_button",
  "user_id": "User ID who operated",
  "user_nickname": "User nickname",
  "message_id": "Message ID",
  "yunhu_a2ui": {
    "recv_id": "Recipient ID",
    "recv_type": "Recipient type",
    "action_name": "Action name",
    "source_component_id": "Source component ID",
    "form_context": {},
    "interaction_json": "JSON string of interaction data"
  }
}

### Button Click Event Handling Example

```python
from ErisPulse.Core.Event import notice

@notice.on_notice()
async def handle_yunhu_notice(event):
    """Handle Yunhu notification events

    Use the generic on_notice() decorator to handle all notification events,
    then distinguish different types of notifications by detail_type
    event.reply() will automatically reply via the Yunhu platform
    """

# Check if it is a button click event
    if event.get("detail_type") == "yunhu_button_click":
        user_id = event.get_user_id()
        user_nickname = event.get_user_nickname()
        button_value = event.get("yunhu_button", {}).get("value", "")

        print(f"User {user_nickname}({user_id}) clicked the button: {button_value}")

# Use event.reply() to automatically reply (will automatically select the correct sending method based on the platform)
        if button_value == "confirm":
            await event.reply("You clicked the confirm button!")
        elif button_value == "cancel":
            await event.reply("Operation canceled")
        else:
            await event.reply(f"Received your selection: {button_value}")

# Handle quick menu event
    elif event.get("detail_type") == "yunhu_shortcut_menu":
        menu_id = event.get("yunhu_menu", {}).get("id", "")
        await event.reply(f"Triggered quick menu: {menu_id}")

# Handle bot setting changes
    elif event.get("detail_type") == "yunhu_bot_setting":
        settings = event.get("yunhu_setting", {})
        await event.reply(f"Settings updated: {settings}")

# Handle A2UI button event
    elif event.get("detail_type") == "yunhu_a2ui_button":
        a2ui = event.get("yunhu_a2ui", {})
        action_name = a2ui.get("action_name", "")
        form_context = a2ui.get("form_context", {})
        await event.reply(f"A2UI operation: {action_name}, form data: {form_context}")
```

### Sending Message with Buttons Using Chained Calls

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

# Send a message with buttons to a group
await yunhu.Send.To("group", "123456").Buttons(buttons).Text("Please confirm the following operation")

# Send a message with buttons to a private chat
await yunhu.Send.To("user", "789").Buttons(buttons).Text("Please select your preference settings")
```

### Sending A2UI Messages

```python
from ErisPulse import sdk

yunhu = sdk.adapter.get("yunhu")

# Send A2UI message
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
      "value": "Setting Value"
    }
  }
}

# Quick Menu
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

## Event Mixin Extension Methods

The adapter registers the following platform-specific methods, available only when `platform == "yunhu"`:

| Method | Return Type | Description |
|--------|-------------|-------------|
| `get_raw_event()` | `dict` | Get raw Yunhu event data (yunhu_raw) |
| `get_sender_level()` | `str` | Sender's original Yunhu level (owner/administrator/member/unknown) |
| `get_sender_role()` | `str` | Sender's OneBot12 standard role (owner/admin/member) |
| `get_sender_title()` | `str` | Sender's title (standard `title` field accessor, reserved) |
| `get_sender_avatar()` | `str` | Sender's avatar URL |
| `get_command()` | `dict` | Command data (only for command message events, yunhu_command) |
| `get_button_value()` | `str` | Button click event's value (yunhu_button.value) |
| `get_a2ui_action()` | `str` | A2UI button event's actionName |
| `get_a2ui_form_context()` | `dict` | A2UI button event's form context |
| `get_menu_id()` | `str` | Quick menu event ID (yunhu_menu.id) |
| `get_setting()` | `dict` | Bot setting event's setting data (yunhu_setting) |
| `is_command_message()` | `bool` | Whether it is a command message |
| `is_button_click()` | `bool` | Whether it is a button click event |
| `is_a2ui_button()` | `bool` | Whether it is an A2UI button event |

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

## Extension Field Descriptions

- All platform-specific fields are prefixed with `yunhu_` to avoid conflicts with standard fields
- Original data is preserved in the `yunhu_raw` field, facilitating access to complete original Yunhu platform data
- `self.user_id` represents the bot ID (obtained from the bot_id in configuration)
- Form commands are provided through the `yunhu_command` field as structured data
- Button click events are provided through the `yunhu_button` field with button-related information
- A2UI button events are provided through the `yunhu_a2ui` field with A2UI interaction-related information
- Bot setting changes are provided through the `yunhu_setting` field with setting item data
- Quick menu operations are provided through the `yunhu_menu` field with menu-related information
- Emoji/pack message segments are provided through the `yunhu_expression` message segment with sticker data (sticker_id, pack ID, image size, etc.)

### Emoji/Pack Message Segment (yunhu_expression)

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
|------|------|------|
| `sticker_id` | string | Unique sticker identifier |
| `sticker_pack_id` | string | Sticker pack ID |
| `expression_id` | string | Expression ID |
| `image_name` | string | Expression image file path |
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

---

## Multi-Bot Configuration

### Configuration Description

The Yunhu adapter supports configuring and running multiple Yunhu robot accounts simultaneously.

```toml
# config.toml
[Yunhu_Adapter.accounts.bot1]
token = "your_bot1_token"  # Robot token (required)
mode = "ws"  # Receive mode (optional, default "ws", options: "ws", "webhook")
webhook_path = "/webhook/bot1"  # Webhook path (optional, default "/webhook", used in webhook mode)
enabled = true  # Whether to enable (optional, default true)

[Yunhu_Adapter.accounts.bot2]
token = "your_bot2_token"  # Second robot's token
webhook_path = "/webhook/bot2"  # Independent webhook path
enabled = true
```

**Configuration Item Description:**
- `token`: Yunhu platform-provided API token (required)
- `mode`: Receive mode (optional, default "ws", options "ws", "webhook")
- `webhook_path`: HTTP path for receiving Yunhu events (optional, default "/webhook", used in webhook mode)
- `enabled`: Whether to enable this account (optional, default true)

**Important Notes:**
1. The robot ID in the Yunhu platform is automatically detected at runtime, no need to specify in the configuration
2. In webhook mode, each bot should have an independent `webhook_path` to receive its own webhook events
3. When configuring webhook in the Yunhu platform, please set corresponding URLs for each bot, for example:
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

> **Note:** When using `bot_id`, the system will automatically find the matching account in the configuration. This is especially useful when handling event replies, where you can directly use `event["self"]["user_id"]` to reply with the same bot.

### Bot Identifier in Events

Events received will automatically include the corresponding `bot_id` information:

```python
from ErisPulse.Core.Event import message

@message.on_message()
async def handle_message(event):
    if event["platform"] == "yunhu":
        # Get the bot ID that triggered the event
        bot_id = event["self"]["user_id"]
        print(f"Message from Bot: {bot_id}")
        
        # Reply with the same bot
        yunhu = adapter.get("yunhu")
        await yunhu.Send.Using(bot_id).To(
            event["detail_type"],
            event["user_id"] if event["detail_type"] == "private" else event["group_id"]
        ).Text("Reply message")
```

### Log Information

The adapter will automatically include `bot_id` information in logs, facilitating debugging and tracking:

```
[INFO] [yunhu] [bot:30535459] Received private message from user user123
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

# Dynamically enable/disable accounts (requires adapter restart)
yunhu.bots["bot1"].enabled = False
```

### Old Configuration Compatibility

Old configuration format `[Yunhu_Adapter.bots.*]` (with `bot_id` field) will be automatically migrated to the `accounts` format (`bot_id` is now automatically detected at runtime, the value in the configuration will be ignored); it is recommended to migrate to the new format as soon as possible.



### 邮件适配

# Email Platform Feature Documentation

EmailAdapter is an email adapter based on the SMTP/IMAP protocol, supporting email sending, receiving, and processing.

---

## Documentation Information

- Corresponding Module Version: 4.3.0  
- Maintainer: ErisPulse

## Basic Information

- Platform Overview: A general-purpose adapter for sending and receiving emails via standard SMTP/IMAP protocols
- Adapter Name: EmailAdapter
- Multi-account Support: Supports configuring multiple email accounts simultaneously
- Connection Method: IMAP long-polling for receiving + SMTP for sending
- Authentication Method: Email address + password/authorization code
- OneBot12 Compatibility: Supports sending OneBot12 formatted messages

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
| `max_retries` | int | `3` | Maximum number of retry attempts on connection failure |

### Account Configuration (EmailAdapter.accounts)

Each account corresponds to an independent email. Account-level configurations take precedence over global configurations.

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

## v5 Paradigm Update (4.2.0)

- **Api DSL Minimal Set**: get_self_info (email address) / get_status / get_version / get_supported_actions
- **spawn_background Task Ownership**: IMAP polling tasks now use runtime.spawn_background
- **Framework Soft Dependency**: Runtime checks for ErisPulse>=2.7.1 and prompts; version logs are output on startup
- Import paths updated to Core.Bases; _load_accounts retained (global default values merged into adapter-specific logic)

---

### Platform Capabilities Already Integrated

- **Receiving**: IMAP polling for receiving messages (body/HTML/attachments parsed into message segments), incremental unread detection
- **Sending**: SMTP sending (Subject/Text/Html/Cc/Bcc/ReplyTo/Attachment), supports multiple accounts
- **API**: Account information and runtime status (minimal set); concepts like email recall/group are not applicable

---

## Supported Message Sending Types

All sending methods are implemented through a fluent API syntax:

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

# Use Raw_ob12 to send standard OB12 messages
await mail.Send.To("private", "to@example.com").Raw_ob12([
    {"type": "text", "data": {"text": "Email body"}},
    {"type": "file", "data": {"file": "/path/to/attachment.pdf"}},
])

# Specify the sending account (for multiple accounts)
await mail.Send.Using("default").To("private", "to@example.com").Text("Content")
```

> Note: When using the fluent API syntax, parameter methods (Subject / Cc / Attachment, etc.) must be called before the sending method (Text / Html / Raw_ob12).

### Basic Sending Methods

| Method | Description |
|--------|-------------|
| `.Text(text: str)` | Send plain text email |
| `.Html(html: str)` | Send HTML formatted email |
| `.MergeForward(nodes, title)` | Send merged forward email (body is a `<details>` collapsed HTML card, subject defaults to the title) |
| `.Raw_ob12(message, **kwargs)` | Send OneBot12 formatted message |

### Fluent Modifier Methods (return self, can be chained)

| Method | Description |
|--------|-------------|
| `.Subject(subject: str)` | Set the email subject |
| `.Cc(emails: Union[str, List[str]])` | Set the CC recipients |
| `.Bcc(emails: Union[str, List[str]])` | Set the BCC recipients |
| `.ReplyTo(email: str)` | Set the reply-to address |
| `.Attachment(file, filename: str = None)` | Add an attachment |

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
2. `user_id` is the sender's **pure email address**, `user_nickname` is the sender's display name
3. `message` message segments are in standard OB12 format (text segment + file segment)
4. The email subject is obtained via the `email_subject` extension field
5. The complete original data is preserved in the `email_raw` field

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
  "alt_message": "Email Subject",
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
| `email_raw` | dict | Complete original email data (subject/from/to/date/cc/bcc/text_content/html_content/attachments, etc.) |
| `email_raw_type` | str | Original event type: `email_new` (new email) or `email_reply` (reply email) |
| `email_subject` | str | Email subject (convenient access) |
| `email_from` | str | Sender's pure email address (convenient access) |
| `attachments` | list | List of attachment data (including binary `data` field, backward compatible) |

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
    # Pure email address of sender
    sender = event["user_id"]              # sender@example.com
    
    # Sender's display name
    nickname = event.get("user_nickname")  # Sender
    
    # Email subject
    subject = event.get("email_subject")   # Meeting Notice
    
    # Plain text body (first text segment)
    text = event.get_text()
    
    # Complete original data
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

- Corresponding Module Version: 4.2.0
- Maintainer: ShanFish

## Basic Information

- Platform Overview: Kook (formerly Kaihei La) is a community platform supporting text, voice, and video communication, providing a complete Bot development interface.
- Adapter Name: KookAdapter
- Multi-account Support: Supports configuring multiple Kook robots simultaneously.
- Connection Method: WebSocket long connection (via Kook gateway).
- Authentication Method: Identity authentication based on Bot Token.
- Chained Modifier Support: Supports chained modifier methods such as `.Reply()`, `.At()`, `.AtAll()`.
- OneBot12 Compatibility: Supports sending OneBot12 format messages.

## Configuration Instructions

KookAdapter supports multi-account configuration, with each account corresponding to a distinct Kook robot.

```toml
# config.toml
# Account 1
[KookAdapter.accounts.default]
token = "YOUR_BOT_TOKEN"     # Kook Bot Token (required, format: Bot xxx/xxx)
bot_id = ""                   # Bot user ID (optional, if not filled, parsed from token)
compress = true               # Whether to enable WebSocket compression (optional, default: true)
enabled = true                # Whether to enable (optional, default: true)

# Account 2
[KookAdapter.accounts.bot2]
token = "ANOTHER_BOT_TOKEN"
bot_id = ""
enabled = true
```

> Backward Compatibility: If an old single-account `[KookAdapter]` configuration (including token) is detected, it will be automatically migrated to `accounts.default`.

**Configuration Item Description (per account):**
- `token`: Kook Bot's Token (required), obtained from [Kook Developer Center](https://developer.kookapp.cn), format: `Bot xxx/xxx`
- `bot_id`: Bot's user ID (optional), if not filled, the adapter will attempt to automatically parse from the token. It is recommended to manually fill to ensure accuracy.
- `compress`: Whether to enable WebSocket data compression (optional, default: `true`), zlib is used to decompress data when enabled.
- `enabled`: Whether to enable this account (optional, default: true)

**API Environment:**
- Kook API base address: `https://www.kookapp.cn/api/v3`
- WebSocket gateway is dynamically obtained via API: `POST /gateway/index`

## v5 Paradigm Update (4.1.0)

This adapter has completed v5 paradigm alignment (incremental upgrade, API compatible):

- **BaseConverter Inheritance**: Common fields of converters are built by framework `build_base_event`
- **Api DSL**: Standard API action mapping (see below)
- **Standard keyboard segment**: `{"type": "keyboard", "data": {"rows": [[{"label", "type": "callback|link", "data"}]]}}` text+keyboard automatically combined into Kook card message (section + action-group); .Keyboard(rows) modifier accepts generic structure
- **spawn_background task assignment**: Connection tasks use runtime.spawn_background
- **Framework Soft Dependency**: Runtime detects ErisPulse>=2.7.1 and prompts; startup outputs version logs

### Standard API Actions

```python
from ErisPulse import sdk
kook = sdk.adapter.get("kook")

result = await kook.Api.get_self_info()              # GET /users/@me
result = await kook.Api.get_user_info(user_id)       # POST /user/view
result = await kook.Api.get_guild_info(guild_id)     # POST /guild/view
result = await kook.Api.get_guild_list()             # POST /guild/list
result = await kook.Api.get_channel_info(channel_id) # POST /channel/view
result = await kook.Api.get_channel_list(guild_id)   # POST /channel/list
await kook.Api.delete_message(msg_id)                # POST /message/delete
result = await kook.Api.Using("main").get_self_info()
```

### Buttons (keyboard)

```python
rows = [[{"label": "Option A", "type": "callback", "data": "vote:A"},
         {"label": "Official Site",  "type": "link",     "data": "https://example.com"}]]
await kook.Send.To("channel", channel_id).Keyboard(rows).Text("Please select")
# Text and buttons automatically combined into Kook card message (section + action-group)

# Button click callback (standard fields)
from ErisPulse.Core.Event import notice

@notice.on_notice()
async def handle_button(event):
    if event.get("platform") == "kook" and event.get("button_data"):
        data = event["button_data"]
```

---

## Supported Message Sending Types

All sending methods use chained syntax, for example:
```python
from ErisPulse.Core import adapter
kook = adapter.get("kook")

await kook.Send.To("group", channel_id).Text("Hello World!")
```

Supported sending types include:
- `.Text(text: str)`: Send plain text message.
- `.Image(file: bytes | str)`: Send image message, supports file path, URL, binary data.
- `.Video(file: bytes | str)`: Send video message, supports file path, URL, binary data.
- `.File(file: bytes | str, filename: str = None)`: Send file message, supports file path, URL, binary data.
- `.Voice(file: bytes | str)`: Send voice message, supports file path, URL, binary data.
- `.Markdown(text: str)`: Send KMarkdown format message.
- `.Card(card_data: dict)`: Send card message (CardMessage).
- `.MergeForward(nodes, title="Merged Chat Record")`: Send merged forward message (rendered as card: title header + each message as a section, KMD escaped, ≤40 nodes).
- `.Raw_ob12(message: List[Dict], **kwargs)`: Send OneBot12 format message.

### Chained Modifier Methods (can be combined)

Chained modifier methods return `self`, supporting chained calls, must be called before the final sending method:

- `.Reply(message_id: str)`: Reply (quote) to a specified message.
- `.At(user_id: str)`: At a specified user, can be called multiple times to mention multiple users.
- `.AtAll()`: At all users.

### Chained Call Examples

```python
# Basic sending
await kook.Send.To("group", channel_id).Text("Hello")

# Reply to message
await kook.Send.To("group", channel_id).Reply(msg_id).Text("Reply message")

# At user
await kook.Send.To("group", channel_id).At("user_id").Text("Hello")

# At multiple users
await kook.Send.To("group", channel_id).At("user1").At("user2").Text("Multiple users @")

# At all
await kook.Send.To("group", channel_id).AtAll().Text("Announcement")

# Combined usage
await kook.Send.To("group", channel_id).Reply(msg_id).At("user_id").Text("Composite message")
```

### OneBot12 Message Support

The adapter supports sending OneBot12 format messages, facilitating cross-platform message compatibility:

```python
# Send OneBot12 format message
ob12_msg = [{"type": "text", "data": {"text": "Hello"}}]
await kook.Send.To("group", channel_id).Raw_ob12(ob12_msg)

# Combined with chained modifiers
ob12_msg = [{"type": "text", "data": {"text": "Reply message"}}]
await kook.Send.To("group", channel_id).Reply(msg_id).Raw_ob12(ob12_msg)

# Use mention and reply message segments in Raw_ob12
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
# Edit message (only supports KMarkdown type=9 and CardMessage type=10)
await kook.Send.To("group", channel_id).Edit(msg_id, "**Updated content**")

# Recall message
await kook.Send.To("group", channel_id).Recall(msg_id)

# Upload file (get file URL)
result = await kook.Send.Upload("C:/path/to/file.jpg")
file_url = result["data"]["url"]
```

## Send Method Return Values

All send methods return a Task object, which can be directly awaited to get the send result. The return result follows the ErisPulse adapter standardized return specification:

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

### Error Code Description

| retcode | Description |
|---------|-------------|
| 0 | Success |
| 40100 | Token invalid or not provided |
| 40101 | Token expired |
| 40102 | Token does not match Bot |
| 40103 | Missing permission |
| 40000 | Parameter error |
| 40400 | Target does not exist |
| 40300 | No permission to operate |
| 50000 | Server internal error |
| -1 | Adapter internal error |

## Platform-Specific Event Types

Use platform=="kook" check before using platform-specific features

### Core Differences

1. **Channel System**: Kook uses a two-layer structure of server (Guild) and channel (Channel), with channels being the basic message sending target.
2. **Message Types**: Kook supports multiple message types including text (1), image (2), video (3), file (4), voice (8), KMarkdown (9), and card messages (10).
3. **Private Messaging System**: Kook distinguishes between channel messages and private messages, using different API endpoints.
4. **Message Sequence Numbers**: Kook WebSocket uses `sn` sequence numbers to ensure message order, supporting message buffering and out-of-order reordering.
5. **Message Editing and Recall**: Supports editing sent messages (only KMarkdown and CardMessage) and recalling messages.

### Extended Fields

- All unique fields are prefixed with `kook_`
- Original data is preserved in the `kook_raw` field
- `kook_raw_type` indicates the original Kook message type number (e.g., `1` for text, `255` for notification events)

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
| 9 | `text` | KMarkdown message (extract plain text content) |
| 10 | `json` | Card message (original JSON) |

Message segment structure example:
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

When a message contains @ information, a `mention` message segment is inserted before the message segment:

```json
{
  "type": "mention",
  "data": {
    "user_id": "Mentioned user ID"
  }
}
```

### mention_all Message Segment

When the message is a @all, a `mention_all` message segment is inserted:

```json
{
  "type": "mention_all",
  "data": {}
}
```

## WebSocket Connection

### Connection Process

1. Use Bot Token to call `POST /gateway/index` to obtain the WebSocket gateway address.
2. Connect to the WebSocket gateway.
3. Receive HELLO (s=1) signal, verify connection status.
4. Start heartbeat loop (PING, s=2, every 30 seconds).
5. Receive message events (s=0), use sn sequence number to ensure order.
6. Receive heartbeat response PONG (s=3).

### Signal Types

| Signal | s value | Description |
|--------|---------|-------------|
| HELLO | 1 | Server welcome signal, received after successful connection |
| PING | 2 | Client heartbeat, sent every 30 seconds, carries current sn |
| PONG | 3 | Heartbeat response |
| RESUME | 4 | Resume connection signal, carries sn to resume session |
| RECONNECT | 5 | Server requests reconnection, need to re-obtain gateway |
| RESUME_ACK | 6 | RESUME success response |

### Disconnection Reconnection

- After an abnormal disconnection, the adapter automatically retries the connection.
- If there was a previous `sn > 0`, it first attempts RESUME (s=4) to restore the connection.
- After RESUME failure, reset sn and message queue, and reconnect from scratch (HELLO process).
- Upon receiving RECONNECT (s=5) signal, clear status and reconnect.

### Message Sequence Number Mechanism

Kook WebSocket uses `sn` (incrementing sequence number) to ensure message order:

- Each received message event (s=0) increments sn.
- If a message with a non-continuous sn is received, it enters buffering mode.
- Messages in the buffer are sorted by sn, waiting for missing messages to arrive before processing in order.
- After the buffer is cleared, it automatically exits buffering mode.

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
        print(f"User {user_id} added emoji reaction to message {msg_id}")

    elif sub_type == "deleted_reaction":
        emoji = event.get("emoji", {})
        user_id = event.get("user_id")
        msg_id = event.get("message_id")
        print(f"User {user_id} removed emoji reaction from message {msg_id}")
```

### Sending Media Messages

```python
# Send image (URL)
await kook.Send.To("group", channel_id).Image("https://example.com/image.png")

# Send image (binary)
with open("image.png", "rb") as f:
    image_bytes = f.read()
await kook.Send.To("group", channel_id).Image(image_bytes)

# Send video
await kook.Send.To("group", channel_id).Video("https://example.com/video.mp4")

# Send file
await kook.Send.To("group", channel_id).File("https://example.com/file.pdf", filename="document.pdf")

# Send voice
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

### Message Editing and Recall

```python
# Send message
result = await kook.Send.To("group", channel_id).Markdown("**Original content**")
msg_id = result["data"]["msg_id"]

# Edit message (only supports KMarkdown and CardMessage)
await kook.Send.To("group", channel_id).Edit(msg_id, "**Updated content**")

# Recall message
await kook.Send.To("group", channel_id).Recall(msg_id)
```

### Handling Private Message Edit and Delete Notifications

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

MatrixAdapter is an adapter built on the [Matrix protocol](https://spec.matrix.org/), integrating all core functional modules of the Matrix protocol and providing unified event handling and message operation interfaces.

---

## Document Information

- Corresponding module version: 4.4.0
- Maintainer: ErisPulse

## Basic Information

- Platform Overview: Matrix is an open, decentralized communication protocol supporting various scenarios such as private chats and group chats.
- Adapter Name: MatrixAdapter
- Multi-account Support: Supports simultaneous configuration of multiple Matrix accounts
- Connection Method: Long Polling (via Matrix Sync API `/sync`)
- Authentication Method: Based on access_token or user_id + password to obtain token
- Chainable Modifier Support: Supports chainable modifier methods such as `.Reply()`, `.At()`, and `.AtAll()`
- OneBot12 Compatibility: Supports sending OneBot12 formatted messages

## Configuration Explanation

MatrixAdapter supports multi-account configuration, with each account having independent homeserver and authentication information.

```toml
# config.toml
# Account 1
[Matrix_Adapter.accounts.default]
homeserver = "https://matrix.org"          # Matrix server address (required)
access_token = "YOUR_ACCESS_TOKEN"          # Access token (either this or user_id+password)
user_id = ""                                # Matrix user ID (e.g. @bot:matrix.org)
password = ""                               # Matrix user password
auto_accept_invites = true                  # Whether to automatically accept room invites (optional, default is true)
enabled = true                              # Whether to enable (optional, default is true)

# Account 2
[Matrix_Adapter.accounts.bot2]
homeserver = "https://matrix.example.com"
access_token = "ANOTHER_TOKEN"
enabled = true
```

> Compatibility with old configuration: If an old single-account `[Matrix_Adapter]` configuration (including access_token) is detected, it will be automatically migrated to `accounts.default`.

**Configuration Item Explanation (per account):**
- `homeserver`: Matrix server address (required), default is `https://matrix.org`
- `access_token`: Access token, obtainable from a Matrix client. If you already have a token, simply fill it in
- `user_id`: Matrix user ID (e.g. `@bot:matrix.org`), used in conjunction with `password` for login
- `password`: Matrix user password, used for automatic login to obtain access_token
- `auto_accept_invites`: Whether to automatically accept room invites, default is `true`
- `enabled`: Whether to enable this account (optional, default is true)

**Authentication Method:**
- Method 1 (Recommended): Directly provide `access_token`
- Method 2: Provide `user_id` and `password`, the adapter will automatically call the login interface to obtain the token

## v5 Paradigm Update (4.2.0)

- **BaseConverter Inheritance**: Common fields of converters are built by framework build_base_event
- **Api DSL**: get_self_info/get_user_info/get_group_info/get_group_list/get_group_member_list/leave_group/delete_message(redact) + meta actions
- **Message Event Supplement message_id** (event_id); Message registration table supports delete_message
- **spawn_background Task Assignment**: Synchronous/heartbeat tasks use runtime.spawn_background
- **Framework Soft Dependency**: Runtime detects ErisPulse>=2.7.1 and prompts; Version logs output on startup
- Matrix has no native button capability, standard keyboard segment is gracefully ignored (no error)

## End-to-End Encryption (4.3.0)

Starting from 4.3.0, the adapter natively supports end-to-end encryption for encrypted rooms (based on matrix-nio[e2e] / vodozemac):

```toml
[Matrix_Adapter.accounts.default]
user_id = "@bot:matrix.org"
password = "YOUR_PASSWORD"
encryption_enabled = true       # Enable (default false, existing deployments unaffected)
trust_all_devices = true        # Automatically trust unverified devices (default; false for strict mode)
```

- Automatic decryption/encryption for encrypted room message sending/receiving, media end-to-end encryption (`m.file.encrypted`)
- `device_id` is automatically parsed and persisted; sessions are stored in `store_path` (default `data/matrix/<account name>`, **do not delete**, otherwise historical messages cannot be decrypted)
- Event Mixin adds `event.is_encrypted()`; media segment carries `matrix_encrypted_file` (JWK), which can be decrypted using `MatrixAdapter.decrypt_media()`
- Cross-signing and server-side key backup are not supported; requires Python >= 3.10
- If not enabled or matrix-nio is not installed, it automatically falls back to plaintext mode

See the [adapter README](https://github.com/ErisPulse/ErisPulse-MatrixAdapter) for detailed explanation.

### Standard API Action Examples

```python
from ErisPulse import sdk
matrix = sdk.adapter.get("matrix")
result = await matrix.Api.get_self_info()            # /account/whoami
result = await matrix.Api.get_group_info(room_id)    # m.room.name
result = await matrix.Api.get_group_list()           # /joined_rooms
await matrix.Api.delete_message(event_id)            # redact (room_id completed in registration table)
```

---

### Supported Platform Capabilities

- **Events**: Message events (m.room.message: text/image/file/audio/video/reply/edit), member changes (m.room.member), room name changes, and other status events
- **Sessions**: Private chat (DM rooms are automatically discovered) / group (room); Supports sending Text/Image/File/Voice/Video/Markdown/Raw_ob12
- **API**: whoami/profile/joined_rooms/room status/member list/leave/redact (see above Api DSL)

---

## Supported Message Sending Types

All sending methods use chainable syntax, for example:
```python
from ErisPulse.Core import adapter
matrix = adapter.get("matrix")

await matrix.Send.To("group", room_id).Text("Hello World!")
```

Supported sending types include:
- `.Text(text: str)`: Send plain text messages.
- `.Image(file: bytes | str)`: Send image messages, supporting file paths, URLs, MXC URIs, and binary data.
- `.Voice(file: bytes | str)`: Send voice messages, supporting file paths, URLs, MXC URIs, and binary data.
- `.Video(file: bytes | str)`: Send video messages, supporting file paths, URLs, MXC URIs, and binary data.
- `.File(file: bytes | str, filename: str = "")`: Send file messages, supporting file paths, URLs, MXC URIs, and binary data.
- `.Notice(text: str)`: Send notification messages (m.notice type in Matrix).
- `.Html(html: str, fallback: str = "")`: Send HTML formatted messages, supporting rich text content.
- `.MergeForward(nodes, title="Merged Chat Record")`: Send merged forward messages (formatted_body blockquote form; whitelist will strip details/inline styles).
- `.Raw_ob12(message: List[Dict], **kwargs)`: Send OneBot12 formatted messages.

### Chainable Modifier Methods (can be combined)

Chainable modifier methods return `self`, supporting chained calls, and must be called before the final sending method:

- `.Reply(message_id: str)`: Reply to a specific message (via Matrix `m.in_reply_to` relationship).
- `.At(user_id: str)`: Mention a specific user (via Matrix `m.mentions` field).
- `.AtAll()`: Mention everyone in the room (via Matrix `@room` mention).

### Chained Call Examples

```python
# Basic sending
await matrix.Send.To("user", dm_room_id).Text("Hello")

# Reply to a message
await matrix.Send.To("group", room_id).Reply("$event_id").Text("Reply message")

# Mention a user
await matrix.Send.To("group", room_id).At("@user:matrix.org").Text("Hello")

# Mention everyone
await matrix.Send.To("group", room_id).AtAll().Text("Announcement")

# Combination: Reply + Mention
await matrix.Send.To("group", room_id).Reply("$event_id").At("@user:matrix.org").Text("Composite message")

# Send HTML message
await matrix.Send.To("group", room_id).Html("<h1>Title</h1><p>Content</p>", fallback="Title\nContent")

# Send notification message
await matrix.Send.To("group", room_id).Notice("System notification")
```

### OneBot12 Message Support

The adapter supports sending OneBot12 formatted messages, facilitating cross-platform message compatibility:

```python
# Send OneBot12 formatted message
ob12_msg = [{"type": "text", "data": {"text": "Hello"}}]
await matrix.Send.To("user", dm_room_id).Raw_ob12(ob12_msg)

# Combined with chainable modifiers
ob12_msg = [{"type": "text", "data": {"text": "Reply message"}}]
await matrix.Send.To("group", room_id).Reply("$event_id").Raw_ob12(ob12_msg)

# Complex message
ob12_msg = [
    {"type": "text", "data": {"text": "Look at this picture: "}},
    {"type": "image", "data": {"file": "https://example.com/image.png"}},
    {"type": "text", "data": {"text": "Isn't it nice? "}}
]
await matrix.Send.To("group", room_id).Raw_ob12(ob12_msg)
```

## Send Method Return Values

All sending methods return a Task object, which can be awaited to obtain the sending result. The returned result follows the ErisPulse adapter standard return specification:

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

### Error Code Explanation

| retcode | Description |
|---------|-------------|
| 0 | Success |
| 32000 | Request timeout or media upload failed |
| 33000 | API call exception |
| 34000 | API returned unexpected format or business error |

## Unique Event Types

Use `platform=="matrix"` to detect and use this platform-specific feature

### Core Differences

1. **Decentralized Architecture**: Matrix is a decentralized communication protocol, with user IDs in the format `@user:server.domain` and room IDs in the format `!room_id:server.domain`
2. **Room Concept**: Matrix does not distinguish between group chats and private chats; all conversations are "rooms." The adapter automatically identifies private chat rooms through DM (Direct Message) account data
3. **Long Polling Synchronization**: Uses the `/sync` API for long polling to fetch new events, rather than WebSocket
4. **MXC URI**: Media files are referenced using the `mxc://server.domain/media_id` format
5. **HTML Rich Text**: Supports sending HTML formatted messages through `formatted_body`
6. **Reaction Emojis**: Supports emoji reactions at the message level (Reaction), distinct from traditional reply messages
7. **Message Editing**: Supports editing previously sent messages via `m.replace` relationship
8. **Message Recall**: Supports recalling/deleting messages via `m.room.redaction`

### Extended Fields

- All unique fields are prefixed with `matrix_`
- Original data is retained in the `matrix_raw` field
- `matrix_raw_type` indicates the original Matrix event type (such as `m.room.message`, `m.room.member`)

### Special Field Examples

```python
# Group message
{
  "type": "message",
  "detail_type": "group",
  "user_id": "@user:matrix.org",
  "group_id": "!room_id:matrix.org",
  "matrix_room_id": "!room_id:matrix.org"
}

# Private chat message
{
  "type": "message",
  "detail_type": "private",
  "user_id": "@user:matrix.org",
  "matrix_room_id": "!dm_room_id:matrix.org"
}

# Reaction emoji
{
  "type": "notice",
  "detail_type": "matrix_reaction",
  "matrix_reaction_event_id": "$reacted_msg_id",
  "matrix_reaction_key": "👍"
}

# Message recall
{
  "type": "notice",
  "detail_type": "matrix_redaction",
  "matrix_redacted_event_id": "$deleted_msg_id"
}

# Message editing
{
  "type": "message",
  "detail_type": "group",
  "matrix_edit": true,
  "matrix_original_event_id": "$original_event_id"
}

# Thread message
{
  "type": "message",
  "detail_type": "group",
  "thread_id": "$thread_root_id"
}
```

### Message Segment Types

Matrix messages are automatically converted to corresponding message segments based on `msgtype`:

| msgtype | Converted Type | Description |
|---|---|---|
| m.text | `text` | Text message |
| m.notice | `text` | Notification message |
| m.emote | `text` | Action message |
| m.image | `image` | Image message |
| m.audio | `voice` | Audio message |
| m.video | `video` | Video message |
| m.file | `file` | File message |
| m.location | `location` | Location message |

Message segment structure example:

```json
// Text message (with HTML)
{
  "type": "text",
  "data": {
    "text": "Plain text content",
    "html": "<b>HTML content</b>"
  }
}

// Image message
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

// Location message
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

MatrixAdapter registers the following event mixin methods, which can be directly called in event handling:

| Method | Return Type | Description |
|------|----------|------|
| `get_room_id()` | `str` | Get room ID |
| `get_matrix_event_type()` | `str` | Get original Matrix event type |
| `get_matrix_sender()` | `str` | Get original sender ID |
| `get_reaction_key()` | `str` | Get reaction emoji |
| `is_edited()` | `bool` | Determine if the message is an edited message |
| `is_notice()` | `bool` | Determine if the message is of m.notice type |

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

### Synchronization Process

1. Authenticate using access_token or user_id + password
2. Call `/_matrix/client/v3/account/whoami` to get bot_user_id
3. Emit connect meta event
4. Perform initial synchronization (`/_matrix/client/v3/sync?timeout=0`) to obtain `next_batch` token
5. Discover DM rooms (`/_matrix/client/v3/user/{user_id}/account_data/m.direct`)
6. Begin Long Polling synchronization loop (`/_matrix/client/v3/sync?since={next_batch}&timeout=30000`)
7. Process new events returned from each synchronization and convert and emit them

### Heartbeat Mechanism

- The adapter emits a `heartbeat` meta event every 30 seconds
- Emits a `connect` meta event upon successful connection
- Emits a `disconnect` meta event upon disconnection

### Room Invitations

- When receiving a room invitation (room with `invite` status), if the `auto_accept_invites` configuration is `true` (default), the adapter will automatically join the room
- Joining the room calls the `/_matrix/client/v3/join/{room_id}` interface

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

### Handling Reaction Emojis

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
        # Handle reaction emoji...
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
await matrix.Send.To("group", room_id).File("/path/to/document.pdf", filename="document.pdf")
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

### Listening to Member Changes

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

QQBotAdapter is an adapter built based on the official QQ Bot (QQ OpenAPI) protocol, integrating full-scene functionalities such as group chats, private chats, and channels. It provides OneBot12 standard events, standard API actions, and request operation interfaces.

---

## Document Information

- Corresponding Module Version: 5.1.0
- Maintainer: ErisPulse

## Basic Information

- Platform Overview: Official QQ Bot Development Interface, supports various scenarios including group chats, private chats, and channels
- Adapter Name: QQBotAdapter
- Connection Method: **WebSocket long connection** (default) or **Webhook HTTP callback** (configured per account, Ed25519 signature verification)
- Authentication Method: appId + clientSecret to obtain access_token (7200s, automatically refreshed 45s in advance)
- API Root Address: `https://api.bot.qq.com` (official unified domain since v5, sandbox is deprecated)
- OneBot12 Compatibility: Full coverage of message sending/receiving, events, **standard API actions**, and **request operations**
- Multi-Account Support: Supported, any account under `accounts` can run in parallel (can mix websocket/webhook modes)

## Configuration Instructions

```toml
# config.toml
[QQBot_Adapter]
intents = "[0, 9, 12, 25, 26, 27]"   # Global: Subscribed event intents (JSON array, supports event names)

[QQBot_Adapter.accounts.default]
appid = "YOUR_APPID"                 # QQ Bot Application ID (required)
secret = "YOUR_CLIENT_SECRET"        # QQ Bot Client Secret (required)
mode = "websocket"                   # Event reception method: websocket / webhook
bot_id = ""                          # Bot ID (left empty to auto-fetch; can be manually filled for Using() location)
gateway_url = ""                     # WebSocket Gateway URL (left empty to dynamically fetch via /gateway/bot)
api_base_url = "https://api.bot.qq.com"  # API root URL (customizable for proxy use)
webhook_path = "/webhook"            # Webhook callback path (生效于 mode=webhook)
enabled = true
```

**Breaking Changes in v5:**
- The official unified use of `api.bot.qq.com`, `sandbox` configuration is deprecated (old configurations are automatically migrated and ignored)
- Old flat configuration (directly writing appid/secret under `[QQBot_Adapter]`) is automatically migrated to `accounts.default`
- Framework is a **soft dependency**: Installing the adapter does not pull the framework version; runtime checks for `ErisPulse>=2.7.1` and prompts accordingly

**Intents Explanation (supports bit positions or event names):**

| Bit | Event Name | Description |
|----|------------|-------------|
| 0 | GUILDS | Channel changes |
| 1 | GUILD_MEMBERS | Channel member changes |
| 9 | GUILD_MESSAGES | Channel messages (private domain) |
| 12 | DIRECT_MESSAGE | Channel direct messages |
| 24 | GROUP_MEMBER | Group member changes (v5 addition) |
| 25 | GROUP_AND_C2C_EVENT | Group @ messages and private chat messages |
| 26 | INTERACTION | Interaction events (buttons, etc.) |
| 27 | MESSAGE_AUDIT | Message audit events |
| 30 | PUBLIC_GUILD_MESSAGES | Channel messages (public domain) |

## Message Sending

### Basic Sending

```python
from ErisPulse import sdk
qqbot = sdk.adapter.get("qqbot")

await qqbot.Send.To("user", user_openid).Text("Hello World!")

# Group chat @ message (automatically uses <qqbot-at-user id="x" /> format)
await qqbot.Send.To("group", group_openid).At("member_openid").Text("@You")

# Channel message (@ automatically uses <@user_id> format)
await qqbot.Send.To("channel", channel_id).Text("Channel message")

# Passive reply (automatically includes msg_id, no need to manually Reply)
await qqbot.Send.To("group", group_openid).Reply(msg_id).Text("Reply content")

# Rich media (URL / local path / binary; automatically splits and uploads if over 5MB)
await qqbot.Send.To("group", gid).Image("https://example.com/img.png")

# Markdown (native / template)
await qqbot.Send.To("group", gid).Markdown("# Title\n- List")
await qqbot.Send.To("user", uid).Markdown(template_id=1, kv=[{"key": "title", "value": "Notification"}])

# Merge Forward (official md has no collapse syntax, renders as a quoted list; requires native Markdown permission, falls back to plain text on failure)
await qqbot.Send.To("group", gid).MergeForward(nodes)

# Keyboard (automatically set to markdown type and includes bot_appid)
await qqbot.Send.To("group", gid).Keyboard(keyboard).Text("Please select")

# Streaming message (1-on-1 chat)
await qqbot.Send.To("user", openid).Stream("Answer content")

# Multiple accounts
await qqbot.Send.Using("account2").To("group", gid).Text("Sent from second bot")
```

## OneBot12 Standard API Actions

```python
result = await qqbot.Api.get_self_info()                     # Bot information
result = await qqbot.Api.get_group_info(group_openid)        # Group information
result = await qqbot.Api.get_group_member_list(group_openid) # List of group members (auto-paginated)
result = await qqbot.Api.get_guild_list()                    # List of guilds/channels
result = await qqbot.Api.get_channel_list(guild_id)          # List of sub-channels
await qqbot.Api.delete_message(message_id)                   # Delete message (auto-routed endpoint based on message source)
result = await qqbot.Api.get_status()                        # Multi-account running status
result = await qqbot.Api.Using("account2").get_self_info()   # Specify account
```

Supported standard actions: `get_self_info` / `get_group_info` / `get_group_member_info` / `get_group_member_list` / `get_guild_info` / `get_guild_list` / `get_guild_member_info` / `get_guild_member_list` / `get_channel_info` / `get_channel_list` / `set_channel_name` / `leave_channel` / `delete_message` / `get_status` / `get_version` / `get_supported_actions`. Unsupported actions return `retcode=10002`.

## Request Operations (Group Join Approval)

The `GROUP_JOIN_REQUEST` event is converted into the OneBot12 `request` event, supporting standardized approval:

```python
from ErisPulse.Core.Event import request as request_event

@request_event.on_request()
async def handle_join(event):
    if event.get("platform") == "qqbot":
        await event.approve()                  # Approve
        # await event.reject(comment="Reason") # Reject
```

`request_id` = Official `join_request_id`, the adapter automatically caches the request context and routes it to `POST /v2/groups/{group_openid}/approval_join_request/{member_openid}`.

## @Robot Detection Mechanism (Important)

On QQ, the fact that a user is mentioned ("@") is carried by an event name. In group messages, the @ marker is represented as `<@{group space openid}>` (which is **not in the same ID system** as the bot_id returned by READY). The adapter automatically handles the following:

1. **Marker Parsing**: Both `<@openid>` and `<qqbot-at-user>` styles are parsed into mention segments (no remnants remain in the text).
2. **Name Normalization**: When the bot name returned by `/users/@me` matches the nickname in the mentions array, it is recognized as an @-to-robot mention. The mention segment is normalized to bot_id (the original openid is preserved in `data.qqbot_openid`).
3. **OpenID Learning**: Automatically learns the bot's openid in each group, used for @ recognition in "receive all group messages" mode.
4. **Injection Guarantee**: `GROUP_AT_MESSAGE_CREATE` / `AT_MESSAGE_CREATE` guarantee the presence of a robot mention segment.

Therefore, `on_at_message()` / `event.is_at_message()` can be directly used on the qqbot platform. After enabling the "receive all group messages" permission, @ messages are pushed via `GROUP_MESSAGE_CREATE` (`GROUP_AT_MESSAGE_CREATE` no longer arrives), and the adapter can still recognize them.

## Platform Native API Method Family

The adapter exposes the complete QQ official API (see platform-features.md in the adapter repository):

- **Bot**: `get_me()`, `reply_interaction()`
- **Guild**: `get_guilds/get_guild/mute_guild_all/roles management/api_permission`
- **Subchannel**: `get_channels/get_channel/create_channel/update_channel/delete_channel/pins`
- **Guild Members**: `get_guild_members/get_guild_member/mute/roles/kick`
- **Permissions/Reactions/Schedules/Posts/Audio**: Full set of methods
- **Group Management** (some interfaces are only available to whitelisted bots): `get_group_members/get_group_bot_state/banlist/join_approval/mute/approval policy`
- **Menu Panels**: `get_custom_menu/update_custom_menu/command panel CRUD`
- **Rich Media**: `_upload_media` (URL/path/binary, automatically chunks if over 5MB), `stream_message` (streaming messages)

## WebSocket / Webhook Connection

### WebSocket Flow

1. Obtain `access_token` using `appId` + `clientSecret` (automatically refreshed 45 seconds in advance, with 3 retry attempts on failure)
2. Dynamically obtain the gateway address via `GET /gateway/bot` (use `gateway_url` directly when configuring)
3. OP_HELLO → Identify/Resume → READY (obtain `session_id` and `bot_id`) → Heartbeat loop
4. Reconnection on disconnection: up to 50 attempts, exponential backoff `min(5 * 2^n, 300)` seconds; OP_RECONNECT preserves session

### Webhook Mode

After setting account `mode = "webhook"`, register HTTP routes via ErisPulse router:

- Ed25519 signature verification (seed = secret filled cyclically to 32 bytes), verify `X-Signature-Ed25519` against `X-Signature-Timestamp + body`
- Automatic handling of op=13 signature verification handshake and op=0 event distribution
- Depends on `cryptography` library (installed with adapter)

## Error Code Description

| retcode | Description |
|---------|-------------|
| 0 | Success |
| 10001 | Missing parameter |
| 10002 | Unsupported action |
| 10003 | Unable to determine target/account |
| 32000 | Request timeout |
| 33000 | Network/API call exception |
| 34001 | Request does not exist or has expired (Request DSL) |
| 34100 | Media upload failed |
| 34000+ | Platform business error (passed through official code) |

## Usage Examples

### Handling Group Messages (Mention Detection)

```python
from ErisPulse.Core.Event import message

@message.on_at_message()
async def handle_at(event):
    if event.get("platform") != "qqbot":
        return
    text = event.get_text()
    if text == "签到":
        await event.reply("已签到")
```

### Handling Interaction Events

```python
from ErisPulse.Core.Event import notice

@notice.on_notice()
async def handle_interaction(event):
    if event.get("platform") != "qqbot":
        return
    if event.get("detail_type") == "qqbot_interaction":
        await qqbot.reply_interaction(event.get("qqbot_interaction_id"), code=0)
        button_id = event.get("qqbot_button_id", "")
        # Handle button...
```

### Multi-Account Startup

```toml
[QQBot_Adapter.accounts.bot_a]
appid = "A_APPID"
secret = "..."
enabled = true

[QQBot_Adapter.accounts.bot_b]
appid = "B_APPID"
secret = "..."
mode = "webhook"
enabled = true
```

Two accounts start in parallel: bot_a uses WebSocket, bot_b uses Webhook, and they do not interfere with each other.



### 云湖用户端适配

# Yunhu User Adapter Feature Documentation

YunhuUserAdapter is an adapter built based on the Yunhu User Account Protocol. It allows login via user email accounts, uses WebSocket to receive events, and provides a unified interface for event handling and message operations.

---

## Document Information

- Corresponding Module Version: 4.4.0
- Maintainer: wsu2059

## Basic Information

- Platform Overview: Yunhu is an enterprise-level instant messaging platform. This adapter interacts with it using **user accounts** (not bot accounts).
- Adapter Name: YunhuUserAdapter
- Multi-account Support: Supports identification and configuration of multiple user accounts via account names.
- Chainable Modifier Support: Supports chainable modifier methods such as `.Reply()`.
- OneBot12 Compatibility: Supports sending OneBot12 format messages.
- Communication Method: Uses email login to obtain a token, receives events via WebSocket, and sends messages using HTTP + Protobuf protocol.
- Session Types: Supports private chats (user), group chats (group), and bot sessions (bot).

## v5 Paradigm Update (4.2.0)

- **BaseConverter Inheritance**; **spawn_background Task Assignment** (WS listening task)
- **Full User API** (based on yhchatAPI full.proto / v1 endpoint, protobuf over HTTP):
  - User: get_user / edit_nickname / edit_avatar
  - Friends: Address book / request list / apply / agree / ignore / delete
  - Groups: Group info / member list / create / dismiss / invite / remove / mute / bot list
  - Conversations: Conversation list; Messages: list / recall / button report
- **Framework Soft Dependency**: Runtime detection of ErisPulse>=2.7.1 with prompts; Version logs output on startup

## Connected Platform Functionality List

### Event Reception (WebSocket, protobuf encoding)

| WS cmd | Event | Description |
|--------|-------|-------------|
| `push_message` | `message` | Private chat/group chat/Bot session messages (text/HTML/Markdown/image/video/audio/file/emoji/article/sticker/button/A2UI) |
| `edit_message` | `notice` (`message_edit`) | Message edit notification |
| `file_send_message` | `notice` (`yunhu_user_file_send`) | Super file sharing |
| `bot_board_message` | `notice` (`yunhu_user_bot_board`) | Bot bulletin board |

### Api DSL Method Mapping ( YunhuHTTPClient → User API v1 endpoint )

| Category | Api Method | Endpoint | Description |
|----------|------------|----------|-------------|
| Account | `get_self_info()` | `/user/info` | Logged-in user information (nickname/avatar/user_id) |
| User | `get_user(user_id)` | `/user/get-user` | User details |
| User | `edit_nickname(nickname)` | `/user/edit-nickname` | Modify own nickname |
| User | `edit_avatar(url)` | `/user/edit-avatar` | Modify own avatar |
| Friends | `get_friend_address_book(md5)` | `/friend/address-book-list` | Address book (cursor pagination) |
| Friends | `get_friend_requests()` | `/friend/request-list` | Friend/group join application list |
| Friends | `friend_apply(user_id, desc)` | `/friend/apply` | Apply to add friend |
| Friends | `friend_agree_apply(user_id)` | `/friend/agree-apply` | Agree to friend application |
| Friends | `friend_ignore_apply(user_id)` | `/friend/ignore-apply` | Ignore friend application |
| Friends | `friend_delete(user_id)` | `/friend/delete-friend` | Delete friend |
| Groups | `get_group_info(group_id)` | `/group/info` | Group information |
| Groups | `get_group_member_list(group_id)` | `/group/list-member` | Group member list (supports keyword search) |
| Groups | `create_group(name, ...)` | `/group/create-group` | Create group |
| Groups | `dismiss_group(group_id)` | `/group/dismiss-group` | Dissolve group |
| Groups | `group_invite(group_id, user_ids)` | `/group/invite` | Invite to group |
| Groups | `group_remove_member(group_id, user_id)` | `/group/remove-member` | Remove group member |
| Groups | `group_gag_member(group_id, user_id, seconds)` | `/group/gag-member` | Mute group member (0=unmute) |
| Groups | `get_group_bot_list(group_id)` | `/group/bot-list` | List of bots in group |
| Conversations | `get_conversation_list(md5)` | `/conversation/list` | Conversation list (cursor pagination) |
| Messages | `get_message_list(chat_id, chat_type, ...)` | `/msg/list-message` | Message list (multiple pagination variants see HTTP client) |
| Messages | `delete_message(msg_id, chat_id, chat_type)` | `/msg/recall-msg` | Recall message (batch recall see HTTP client) |
| Messages | `button_report(...)` | `/msg/button-report` | Button click report |
| Meta Actions | `get_status` / `get_version` / `get_supported_actions` | - | Runtime status/version/supported actions |

### Not Yet Connected (Endpoint Known, full.proto Messages Complete, Extendable as Needed)

- User: Verification code login, badges, gold bean records, bind phone/email, notification settings, user data storage
- Friends: Do not disturb (no-notify), delete application records
- Groups: Command list, categories, recommendations, live room, edit group info/group nickname/keywords, auto-approval on group join, group file limits, event SSE
- Conversations: Pin/sort/delete, do not disturb
- Messages: Forward, A2UI submission, message list image retrieval, file download records
- Group Tags: list / relate / relate-cancel / create / edit / delete / members (endpoint `/group-tag/*`)

> Extension Method: Add methods in `YunhuHTTPClient` following the existing pattern (`_proto_request` / `_json_request` general encapsulation), then expose them in the `Api` class. Endpoint and message definition reference `yhchatAPI/src/api/v1/*.md` and `yhchatAPI/src/full.proto`.

### User API Example

```python
from ErisPulse import sdk
yunhu_user = sdk.adapter.get("yunhu_user")

result = await yunhu_user.Api.get_self_info()
result = await yunhu_user.Api.get_friend_requests()          # Friend application list
await yunhu_user.Api.friend_agree_apply(user_id)             # Agree to friend application
result = await yunhu_user.Api.get_group_member_list(group_id)
result = await yunhu_user.Api.get_conversation_list()        # Conversation list
await yunhu_user.Api.delete_message(msg_id, chat_id, chat_type)  # Recall
```

---

## Supported Message Sending Types

All send methods are implemented through chainable syntax, for example:
```python
from ErisPulse.Core import adapter
yunhu_user = adapter.get("yunhu_user")

await yunhu_user.Send.To("user", user_id).Text("Hello World!")
```

Supported send types include:
- `.Text(text: str, buttons: Optional[List] = None)`: Send plain text message.
- `.Html(html: str, buttons: Optional[List] = None)`: Send HTML formatted message.
- `.Markdown(markdown: str, buttons: Optional[List] = None)`: Send Markdown formatted message.
- `.MergeForward(nodes, title="Merged Chat Record")`: Send merged forwarded message (rendered as `<details>` collapsed HTML card, sent via msg_type=8 HTML channel).
- `.Image(file: Union[str, bytes], buttons: Optional[List] = None)`: Send image message, supports URL, local path, or binary data.
- `.Video(file: Union[str, bytes], buttons: Optional[List] = None)`: Send video message, supports URL, local path, or binary data.
- `.Audio(file: Union[str, bytes], buttons: Optional[List] = None)`: Send audio message, supports URL, local path, or binary data, automatically detects audio duration.
- `.Voice(file: Union[str, bytes], buttons: Optional[List] = None)`: Alias for `.Audio()`.
- `.File(file: Union[str, bytes], file_name: Optional[str] = None, buttons: Optional[List] = None)`: Send file message, supports URL, local path, or binary data.
- `.Face(file: Union[str, bytes], buttons: Optional[List] = None)`: Send emoji/sticker message, supports sticker ID, sticker URL, or binary image data.
- `.A2ui(a2ui_data: Union[str, Dict, List], buttons: Optional[List] = None)`: Send A2UI message (message type 14), A2UI JSON data will be filled into the text field for sending.
- `.Edit(msg_id: str, text: str, content_type: str = "text")`: Edit existing message.
- `.Recall(msg_id: str)`: Recall message.
- `.Raw_ob12(message: Union[List, Dict])`: Send OneBot12 formatted message.

### Media File Handling

All media types (image, video, audio, file) support the following input methods:
- **URL**: `"https://example.com/image.jpg"` — automatically downloads and uploads
- **Local Path**: `"/path/to/file.jpg"` — automatically reads and uploads
- **Binary Data**: `open("file.jpg", "rb").read()` — directly uploads

Media files are automatically uploaded to Qiniu Cloud storage, supporting the following features:
- Automatically detects file type and MIME using the `filetype` library
- Automatically calculates file size
- Automatically detects audio duration (supports MP3, MP4/M4A formats)

### Button Parameter Description

The `buttons` parameter is a nested list, representing the layout and functionality of buttons. Each button object contains the following fields:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `text` | string | Yes | Text on the button |
| `actionType` | int | Yes | Action type:<br>`1`: Navigate to URL<br>`2`: Copy<br>`3`: Click report |
| `url` | string | No | When `actionType=1`, this is the target URL for navigation |
| `value` | string | No | When `actionType=2`, this value is copied to the clipboard<br>When `actionType=3`, this value is sent to the subscriber |

Example:
```python
buttons = [
    [
        {"text": "Copy", "actionType": 2, "value": "xxxx"},
        {"text": "Click to Navigate", "actionType": 1, "url": "http://www.baidu.com"},
        {"text": "Report Event", "actionType": 3, "value": "xxxxx"}
    ]
]
await yunhu_user.Send.To("user", user_id).Buttons(buttons).Text("Message with buttons")
```

### Chainable Modifier Methods (Can be Combined)

Chainable modifier methods return `self`, supporting chained calls, must be called before the final send method:

- `.Reply(message_id: str)`: Reply to a specific message.
- `.At(user_id: str)`: Mention a specific user (text format @user_id).
- `.AtAll()`: Mention everyone (pseudo @all, sends @all text).
- `.Buttons(buttons: List)`: Add buttons.

> **Note:** Because user accounts are special, even non-admin users can @all, but here `AtAll()` only sends a text that mentions everyone, which is a pseudo @all.

### Chained Call Example

```python
# Basic send
await yunhu_user.Send.To("user", user_id).Text("Hello")

# Reply to message
await yunhu_user.Send.To("group", group_id).Reply(msg_id).Text("Reply message")

# Reply + buttons
await yunhu_user.Send.To("group", group_id).Reply(msg_id).Buttons(buttons).Text("Message with reply and buttons")

# Specify account + reply + buttons
await yunhu_user.Send.Using("default").To("group", group_id).Reply(msg_id).Buttons(buttons).Text("Complete chained call")
```

### OneBot12 Message Support

The adapter supports sending OneBot12 formatted messages, facilitating cross-platform message compatibility:

- `.Raw_ob12(message: List[Dict], **kwargs)`: Send OneBot12 formatted message.

```python
# Send OneBot12 formatted message
ob12_msg = [{"type": "text", "data": {"text": "Hello"}}]
await yunhu_user.Send.To("user", user_id).Raw_ob12(ob12_msg)

# Combine with chained modifiers
ob12_msg = [{"type": "text", "data": {"text": "Reply message"}}]
await yunhu_user.Send.To("group", group_id).Reply(msg_id).Raw_ob12(ob12_msg)
```

Raw_ob12 supports automatic grouping of mixed message segments:
- `text`, `mention` types can be merged into one group
- `image`, `video`, `audio`, `file`, `face`, `markdown`, `html`, `a2ui` types are each sent as separate groups
- `reply` type can be attached to any group

## Send Method Return Values

All send methods return a Task object, which can be awaited to get the send result. The return result follows the ErisPulse adapter standardized return specification:

```python
{
    "status": "ok",           // Execution status
    "retcode": 0,             // Return code
    "data": {...},            // Response data
    "message_id": "123456",   // Message ID
    "message": "",            // Error message
    "yunhu_user_raw": {...}   // Raw response data
}
```

## Platform-Specific Event Types

Use `platform == "yunhu_user"` to detect and use platform-specific features.

### Core Differences

1. Platform-specific event types:
    - Super file sharing: `yunhu_user_file_send`
    - Bot bulletin board: `yunhu_user_bot_board`
    - Message edit notification: `message_edit`
    - Message delete notification: `message_delete` (recall)
2. Platform-specific message segment types:
    - Form message segment: `yunhu_user_form`
    - Article message segment: `yunhu_user_post`
    - Sticker message segment: `yunhu_user_sticker`
    - Button message segment: `yunhu_user_button`
    - A2UI message segment: `a2ui`
3. Extended fields:
    - All platform-specific fields are prefixed with `yunhu_user_`
    - Original data is preserved in the `yunhu_user_raw` field
    - Original event type is recorded in the `yunhu_user_raw_type` field
    - In private chats, `self.user_id` indicates the current logged-in user ID

### Supported Original Event Types

| Original Event Type | OneBot12 Type | Description |
|---------------------|---------------|-------------|
| `push_message` | `message` | Pushed message (private chat, group chat, Bot session) |
| `edit_message` | `notice` (`message_edit`) | Message edit event |
| `file_send_message` | `notice` (`yunhu_user_file_send`) | Super file sharing event |
| `bot_board_message` | `notice` (`yunhu_user_bot_board`) | Bot bulletin board event |

> Other event types (such as `heartbeat_ack`, `draft_input`, `stream_message`, etc.) are ignored.

### OneBot12 Supported detail_type

| OneBot12 detail_type | Yunhu chat_type | Description |
|----------------------|-----------------|-------------|
| `private` | 1 | Private chat message |
| `group` | 2 | Group chat message |
| `bot` | 3 | Bot session |

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
    "user_nickname": "Sender's nickname",
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
    "user_nickname": "Sender's nickname",
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

### Bot Bulletin Board Event Example

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
    """Handle Yunhu user message"""
    if event.get("platform") != "yunhu_user":
        return
    
    user_id = event.get("user_id", "")
    user_nickname = event.get("user_nickname", "")
    alt_message = event.get("alt_message", "")
    
    print(f"User {user_nickname}({user_id}): {alt_message}")
    
    # Check for specific message segment types
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

- All platform-specific fields are prefixed with `yunhu_user_` to avoid conflicts with standard fields
- Original data is preserved in the `yunhu_user_raw` field, facilitating access to the complete raw data from the Yunhu platform
- Original event type is recorded in the `yunhu_user_raw_type` field (e.g., `push_message`, `edit_message`, etc.)
- `self.user_id` indicates the current logged-in user ID (obtained from the login response)
- Super file sharing is provided through the `yunhu_user_file_send` field for file sharing data
- Bot bulletin board is provided through the `yunhu_user_bot_board` field for announcement data

### Platform-Specific Message Segment Types

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
        "post_title": "Article Title",
        "post_content": "Article Content"
    }
}
```

| Field | Type | Description |
|-------|------|-------------|
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
|-------|------|-------------|
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
ws_reconnect_interval = 30  # WebSocket reconnection interval (seconds)
ws_timeout = 70             # WebSocket timeout time (seconds)

[YunhuUserAdapter.accounts.default]
email = "user1@example.com"  # User email (required)
password = "password1"       # User password (required)
platform = "windows"         # Login platform (optional, default windows)
device_id = ""               # Device ID (optional, auto-generated if not provided)
enabled = true               # Whether to enable (optional, default true)

[YunhuUserAdapter.accounts.account2]
email = "user2@example.com"
password = "password2"
platform = "android"
device_id = "fixed_device_id_2"
enabled = true
```

**Configuration Item Description:**
- `email`: User email (required), used to log in to the Yunhu platform
- `password`: User password (required)
- `platform`: Login platform identifier (optional, default `windows`), available values: `windows`, `macos`, `linux`, `ios`, `android`
- `device_id`: Device ID (optional, auto-generated if not provided), it is recommended to fill in a fixed value to maintain session consistency
- `enabled`: Whether to enable this account (optional, default `true`)

**Adapter-Level Configuration:**
- `ws_reconnect_interval`: WebSocket reconnection interval (seconds, default 30)
- `ws_timeout`: WebSocket timeout time (seconds, default 70)

**Important Notes:**
1. The adapter uses email login to obtain a token, and receives events via WebSocket after logging in
2. WebSocket connection will automatically reconnect after disconnection, with a maximum of 3 retries
3. It is recommended to set a fixed `device_id` for each account to maintain session consistency
4. Unmodified template accounts (default email and password) will be automatically skipped

### Using Send DSL to Specify Account

You can specify which account to use for sending messages through the `Using()` method. This method supports two types of parameters:
- **Account Name**: The account name in the configuration (e.g., `default`, `account2`)
- **user_id**: The user ID obtained after logging in

```python
from ErisPulse.Core import adapter
yunhu_user = adapter.get("yunhu_user")

# Send message using account name
await yunhu_user.Send.Using("default").To("user", "user123").Text("Hello from account1!")

# Send message using user_id (automatically matches the corresponding account)
await yunhu_user.Send.Using("user_id_here").To("group", "group456").Text("Hello from user!")

# Use the first enabled account if not specified
await yunhu_user.Send.To("user", "user123").Text("Hello from default account!")
```

> **Tip:** When using `user_id`, the system will automatically find the matching account in the configuration. This is especially useful when handling event replies, where you can directly use `event["self"]["user_id"]` to reply from the same account.

### Account Identification in Events

Events received will automatically include the corresponding user ID information:

```python
from ErisPulse.Core.Event import message

@message.on_message()
async def handle_message(event):
    if event["platform"] == "yunhu_user":
        # Get the current logged-in user ID
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

The adapter will automatically include account information in the logs, which is useful for debugging and tracking:

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

The adapter provides a `call_api` method, supporting direct calls to the platform API:

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

# Batch recall message
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

# Get message edit record
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
| `/recall_batch` | Batch recall message |
| `/list` | Get message list |
| `/list_by_seq` | Get message by sequence |
| `/list_by_mid_seq` | Get message by message ID and sequence |
| `/list_edit_record` | Get message edit record |
| `/button_report` | Button event report |



### 平台文档维护说明

# Documentation Maintenance Instructions

This document is maintained by each adapter developer to document the differences and extended features of the adapter in relation to the OneBot12 standard.  
Adapter developers should update this document when releasing new versions.

## Update Requirements

1. Accurately describe the platform-specific send methods and parameters.
2. Provide detailed explanations of the differences from the OneBot12 standard.
3. Offer clear code examples and parameter descriptions.
4. Maintain uniform document formatting for easy user access.
5. Keep version information and maintainer contact details up to date.

## Documentation Structure Guidelines

### 1. Basic Information Section
Each platform feature documentation should include the following basic information:
```markdown
# Platform Name Adapter Documentation

Adapter Name: [Adapter class name]
Platform Overview: [Brief platform introduction]
Supported Protocol/API Version: [Specific protocol or API version]
Maintainer: [Maintainer name/team]
Corresponding Module Version: [Version number]
```

### 2. Supported Message Sending Types
List all supported sending methods and their parameters in detail:
```markdown
## Supported Message Sending Types

All sending methods are implemented using a fluent syntax, for example:
[Code Example]

The supported sending types include:
- Method 1: Description
- Method 2: Description
- ...

### Parameter Description
| Parameter | Type | Description |
|-----------|------|-------------|
| Parameter Name | Type | Description |
```

### 3. Platform-Specific Event Types
Describe the platform-specific event types and their formats in detail:
```markdown
## Platform-Specific Event Types

[Platform Name] events are converted to the OneBot12 protocol, where standard fields fully comply with the OneBot12 protocol, but there are the following differences:

### Core Differences
1. Platform-Specific Event Types:
   - Event Type 1: Description
   - Event Type 2: Description
2. Extended Fields:
   - Field Description

### Special Field Example
[JSON Example]
```

### 4. Extended Field Description
```markdown
## Extended Field Description

- All platform-specific fields are prefixed with `[platform]_`
- Original data is preserved in the `[platform]_raw` field
- [Other special field descriptions]
```

### 5. Configuration Options (if applicable)
```markdown
## Configuration Options

The [Platform Name] adapter supports the following configuration options:

### Basic Configuration
- Configuration Item 1: Description
- Configuration Item 2: Description

### Special Configuration
- Special Configuration Item 1: Description
```

## Content Writing Guidelines

### Code Example Guidelines
1. All code examples must be complete and runnable examples.
2. Use standard import methods:
```python
from ErisPulse.Core import adapter
[Adapter Instance] = adapter.get("[Adapter Name]")
```
3. Provide examples for various usage scenarios.

### Documentation Format Guidelines
1. Use standard Markdown syntax.
2. Use clear heading levels, with a maximum of 4 levels.
3. Use standard Markdown table format for tables.
4. Use appropriate language identifiers for code blocks.

### Version Update Notes
When updating the documentation, update the version information at the top of the document:
```markdown
## Document Information

- Corresponding Module Version: [New Version Number]
- Maintainer: [Maintainer Information]
- Last Updated: [Date]
```

## Quality Checklist

Before submitting documentation updates, please check the following:

- [ ] The document structure meets the specification requirements
- [ ] All code examples can run successfully
- [ ] Parameter descriptions are complete and accurate
- [ ] Event format examples match actual outputs
- [ ] Links and references are correct
- [ ] No grammar or spelling errors
- [ ] Version information has been updated
- [ ] Maintainer information is accurate

## Reference Documents

When writing, please refer to the following documents to ensure consistency:
- [OneBot12 Specification](https://12.onebot.dev/)
- [ErisPulse Core Concepts](../getting-started/basic-concepts.md)
- [Event Conversion Standard](../standards/event-conversion.md)
- [API Response Specification](../standards/api-response.md)
- [Other Platform Adapter Documentation](./)

## Contributing Process

1. Fork the [ErisPulse](https://github.com/ErisPulse/ErisPulse) repository
2. Modify the corresponding platform documentation under the `docs/platform-features/` directory
3. Ensure the documentation complies with the above specification requirements
4. Submit a Pull Request and provide a detailed explanation of the changes

If you have any questions, please contact the relevant adapter maintainer or ask in the project Issues.



### 花枫咖啡馆适配

# Platform Features Document for Huafeng Coffeehouse (RockyChat)

IdeauraAdapter is an adapter built on the RockyChat platform API, integrating all platform functionality modules and providing a unified interface for event handling and message operations.

---

## Documentation Information

- Corresponding Module: ErisPulse-Ideaura  
- Corresponding Module Version: 4.2.0  
- Maintainer: ErisPulse

## Basic Information

- Platform Introduction: Huafeng Coffee Shop (RockyChat) is an instant messaging platform.
- Adapter Name: IdeauraAdapter
- Multi-account Support: Supports configuring multiple accounts via Bot Token.
- Chainable Modifier Support: Supports chainable modifier methods such as `.At()`, `.AtAll()`, `.Reply()`, `.Command()`, etc.
- OneBot12 Compatibility: Supports sending OneBot12 formatted messages.

## v5 Paradigm Update (4.1.0)

- **BaseConverter Inheritance**: Common fields of converters are built by the framework's build_base_event
- **spawn_background Task Ownership**: Account connection tasks are now using runtime.spawn_background
- **Framework Soft Dependencies**: Runtime checks for ErisPulse>=2.7.1 and provides a warning; version logs are output on startup
- Request DSL Postponed (Friend Request Approval API is pending platform support)

---

### Platforms Supported

- **Events**: Message edit/withdraw/forward/read (ideaura_message_*), friend request, friend increase/decrease, online status (friend_online/offline)
- **Sending**: Text / Image / Markdown / Raw_ob12 (with chainable Reply/At/AtAll modifiers)
- **Not Supported**: Friend Request Approval API (not yet provided by the platform), Api DSL (REST API pending platform availability)

## Supported Message Sending Types

All sending methods are implemented using a fluent (chainable) syntax. For example:

```python
from ErisPulse.Core import adapter
ideaura = adapter.get("ideaura")

await ideaura.Send.To("group", "chatroom").Text("Hello World!")
```

The supported sending types include:
- `.Text(text: str)`: Send a plain text message.
- `.Image(file, filename: str = None)`: Send an image message, supporting bytes/URL/local path.
- `.Video(file, filename: str = None)`: Send a video message, supporting bytes/URL/local path.
- `.File(file, filename: str = None)`: Send a file message, supporting bytes/URL/local path.
- `.Voice(file, filename: str = None)`: Send a voice message (sent as a file).
- `.Face(face_id: str)`: Send an emoji (sent as a plain text emoji).
- `.Markdown(text: str)`: Send a message in Markdown format.
- `.Html(html: str)`: Send a message in HTML format.
- `.MergeForward(nodes, title="Merged Chat Record")`: Send a merged-forward message (rendered as a `<details>` collapsed HTML card).
- `.Edit(message_id: str, text: str, content_type: str = "text")`: Edit an existing message.
- `.Recall(message_id: str)`: Recall a message.

### Fluent Modifier Methods (Combination Supported)

Fluent modifier methods return `self`, supporting chainable calls, and must be called before the final sending method:

- `.At(user_id: str, name: str = None)`: @ a specific user.
- `.AtAll()`: @ everyone.
- `.Reply(message_id: str)`: Reply to a specific message.
- `.Command(command_id: str)`: Trigger a Bot command, used in combination with sending methods (sends the message as a specific command).

### Fluent Call Examples

```python
# Basic sending
await ideaura.Send.To("user", user_id).Text("Hello")

# Trigger Bot command
await ideaura.Send.To("group", "chatroom").Command("550e8400-e29b-41d4-a716-446655440000").Text("/weather 北京")

# @ user
await ideaura.Send.To("group", "chatroom").At("456").Text("@李四 你好")

# @ multiple users
await ideaura.Send.To("group", "chatroom").At("456").At("789").Text("@多人")

# Reply to message
await ideaura.Send.To("group", "chatroom").Reply(msg_id).Text("回复消息")

# Reply + @
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

The adapter supports sending OneBot12 formatted messages, facilitating cross-platform message compatibility:

- `.Raw_ob12(message: List[Dict], **kwargs)`: Send a OneBot12 formatted message.

```python
# Send a OneBot12 formatted message
ob12_msg = [{"type": "text", "data": {"text": "Hello"}}]
await ideaura.Send.To("user", user_id).Raw_ob12(ob12_msg)

# Combined with fluent modifiers
ob12_msg = [{"type": "text", "data": {"text": "回复消息"}}]
await ideaura.Send.To("group", "chatroom").Reply(msg_id).Raw_ob12(ob12_msg)
```

## Send Method Return Values

All send methods return a Task object, which can be directly awaited to obtain the send result. The returned result follows the ErisPulse adapter standardization return specification:

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

The `platform=="ideaura"` check is required before using platform-specific features.

### Core Differences

1. Unique Event Types:
    - Message Edit: ideaura_message_edit
    - Message Recall: ideaura_message_recall
    - Message Forward: ideaura_message_forward
    - Message Read: ideaura_message_read
    - Friend Rejected: ideaura_friend_rejected
    - Friend Online: ideaura_friend_online
    - Friend Offline: ideaura_friend_offline
    - User Status Change: ideaura_user_status_change
    - Forwarded Message Segment: ideaura_forwarded
    - Edited Mark Segment: ideaura_edited
    - Markdown Message Segment: ideaura_markdown
    - HTML Message Segment: ideaura_html
    - Bot Command Message Segment: ideaura_command
2. Extended Fields:
    - All unique fields are prefixed with `ideaura_`
    - Original data is preserved in the `ideaura_raw` field
    - `self.user_id` represents the current account's user ID

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
  "ideaura_previous_status": "Previous status"
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

When receiving a forwarded message, the segment type is `ideaura_forwarded`:

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

When a user triggers a Bot command, the segment type is `ideaura_command`:

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
|--------|-------------|-------------|
| `get_source_type()` | `str` | Message source type (`chatroom`/`topic`/`private`) |
| `get_sender_name()` | `str` | Sender's nickname |
| `get_sender_avatar()` | `str` | Sender's avatar URL |
| `is_sender_bot()` | `bool` | Whether the sender is a bot |
| `is_receiver_bot()` | `bool` | Whether the receiver is a bot |
| `get_command_id()` | `str` | The ID of the triggered Bot command (if any, `ideaura_command_id`) |
| `get_command()` | `str` | Alias for `get_command_id()` |
| `get_topic_name()` | `str` | Topic name |
| `get_message_type()` | `str` | Message type (`normal`/`edited`/`forwarded`/`quoted`) |
| `get_message_subtype()` | `str` | Message subtype (`text`/`image`/`video`/`file`/`markdown`/`html`) |
| `is_self_message()` | `bool` | Whether the message was sent by oneself |

```python
from ErisPulse.Core.Event import message

@message.on_message()
async def handle_message(event):
    if event.get_platform() != "ideaura":
        return

    # Get the ID of the triggered Bot command (if any)
    cmd_id = event.get_command_id()
    if cmd_id:
        print(f"Received command: {cmd_id}")
```

## Multi-Account Configuration

### Configuration Instructions

IdeauraAdapter supports configuring and running multiple accounts simultaneously, using **Bot Token** authentication.

> [!WARNING]
> Starting from version 4.0.1, **email and password login has been removed**, and only Bot Token is supported. Bot Token can be obtained from [MSCPO Open Platform](https://open.mscpo.com/rockychat/bots) (must start with `bot-token-`).

```toml
# config.toml
# Account 1
[IdeauraAdapter.accounts.default]
token = "bot-token-xxxxxx1"      # API Token for the bot (required)
enabled = true                   # Whether to enable this account (optional, default is true)

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
- `token`: API Token for the bot (required, must start with `bot-token-`)
- `enabled`: Whether to enable this account (optional, default is true)

**Global Configuration Items:**
- `base_url`: API server address (optional, default is `https://api.mscpo.com/api/rockychat`)
- `ws_url`: WebSocket server address (optional, default is the official address of Huafeng Coffee House)
- `heartbeat_interval`: Heartbeat interval in seconds (optional, default is 30 seconds)

### Using Send DSL to Specify Account

You can specify which account to use for sending messages via the `Using()` method:

```python
from ErisPulse.Core import adapter
ideaura = adapter.get("ideaura")

# Send message using account name
await ideaura.Send.Using("default").To("user", "user123").Text("Hello from account 1!")

# Send message using user_id (automatically matches corresponding account)
await ideaura.Send.Using("456").To("group", "chatroom").Text("Hello from account 2!")

# If not specified, the first enabled account is used
await ideaura.Send.To("user", "user123").Text("Hello from default account!")
```

### Account Identification in Events

Received events automatically include corresponding account information:

```python
from ErisPulse.Core.Event import message

@message.on_message()
async def handle_message(event):
    if event["platform"] == "ideaura":
        account_id = event["self"]["user_id"]
        print(f"Message received from account: {account_id}")
```

## Extension Field Description

- All special fields are prefixed with `ideaura_` to avoid conflicts with standard fields.
- The original data is retained in the `ideaura_raw` field, allowing access to the platform's complete raw data.
- `self.user_id` represents the user ID of the currently logged-in account.
- `ideaura_source_type`: Message source type (`chatroom`/`topic`/`private`)
- `ideaura_sender_name`: Sender's nickname
- `ideaura_sender_avatar`: Sender's avatar URL
- `ideaura_sender_is_bot`: Whether the sender is a bot
- `ideaura_is_self`: Whether the message was sent by oneself (self-messages have been filtered out)
- `ideaura_topic_name`: Topic name
- `ideaura_message_type`: Message type (normal/edited/forwarded/quoted)
- `ideaura_message_subtype`: Message subtype (text/image/video/file/markdown/html)

### File Handling Features

- File size limit: 10MB (both download and local read are limited)
- Automatic file type detection: Detects actual type via file header magic bytes
- Intelligent filename parsing: Automatically corrects meaningless extensions such as `.bin`/`.dat`/`.tmp`
- Supports three file input methods: bytes, URL, and local path
- Automatically downloads and uploads URL files to the server

### Supported File Types

Detected automatically via magic bytes:

| Type | Extensions |
|------|------------|
| Image | png, jpg, gif, webp |
| Video | mp4, avi, flv |
| Audio | mp3, wav, ogg |
| Document | pdf, docx |

## Notes

1. The default API server address is `https://api.mscpo.com/api/rockychat` (customizable via `base_url`); the WebSocket address `wss://api-cofe.allons-y.uk:3009/mqtt` is a platform-specific address and does not change with the adapter name.
2. The adapter uses a WebSocket long connection to receive events and supports automatic reconnection (with a fixed 5-second delay).
3. Messages sent by itself (`isSelf: true`) are automatically filtered and do not generate events.
4. @all (using `AtAll()`) requires administrator privileges.
5. File upload size is limited to 10MB.
6. Audio files are sent as a `file` subtype (the platform does not distinguish independent audio types).
7. Emojis (using `Face()`) are sent as plain text emoji.
8. Call `shutdown()` when exiting the program to ensure proper resource release.



### Discord 适配

# Discord Platform Feature Documentation

DiscordAdapter is an adapter built on the Discord Gateway (WebSocket) and REST API v10 protocol, integrating the core functionalities of Discord Bots and providing unified event handling and message operation interfaces.

---

## Document Information

- Corresponding Module Version: 4.3.0
- Maintainer: ErisPulse
- Discord API Version: v10

## Basic Information

- **Platform Overview**: Discord is a widely popular community communication platform that supports various conversation formats such as servers, channels, and direct messages, and provides a comprehensive Bot development interface.
- **Adapter Name**: DiscordAdapter
- **Multi-account Support**: Supports configuring multiple Discord bots simultaneously.
- **Connection Method**: Gateway WebSocket (for receiving events) + REST API (for sending messages / invoking APIs)
- **Authentication Method**: Bot Token (HTTP header `Authorization: Bot {token}`, token included in the Gateway IDENTIFY payload)
- **Chained Modifiers Support**: Supports chained modifier methods such as `.Reply()`, `.At()`, and `.AtAll()`
- **OneBot12 Compatibility**: Supports sending OneBot12 formatted messages

## Configuration

DiscordAdapter supports multi-account configuration, with each account corresponding to an independent Discord Bot.

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
- `bot_id`: Bot's user ID (optional, automatically retrieved at runtime from the READY event, no need to manually fill)
- `enabled`: Whether to enable this account (optional, default: `true`)

### Gateway Intents

Intents use a bitmask, calculated as the bitwise OR (`|`) of each Intent value:

| Intent | Bit | Value | Description | Privileged |
|-------|------|------|------|------|
| GUILDS | `1 << 0` | 1 | Server creation/deletion/update, channel, role changes | No |
| GUILD_MEMBERS | `1 << 1` | 2 | Member join/leave/update | Yes |
| GUILD_MESSAGES | `1 << 9` | 512 | Server message sending/receiving | No |
| MESSAGE_CONTENT | `1 << 15` | 32768 | Message content (empty if this Intent is not present) | Yes |

Default value `33281` = `GUILDS(1) | GUILD_MESSAGES(512) | MESSAGE_CONTENT(32768)`.

> **Note**: Privileged Intents must be enabled in Discord Developer Portal → Bot → Privileged Gateway Intents. If the Bot is in more than 100 servers, Discord approval is also required.

**API Environment:**
- Discord REST API base URL: `https://discord.com/api/v10`
- Gateway WebSocket URL: Dynamically retrieved via `GET /gateway/bot`, typically `wss://gateway.discord.gg/?v=10&encoding=json`

## v5 Paradigm Update (4.2.0)

This adapter has completed alignment with the v5 paradigm (incremental upgrade, API compatible):

- **BaseConverter Inheritance**: Common fields of the converter are built by the framework `build_base_event`
- **Api DSL**: Standard API action mapping (see below)
- **Standard keyboard segment**: Converted to Discord components (action row + buttons); .Keyboard(rows) decorator accepts a generic structure
- **Standard interaction callback fields**: The INTERACTION_CREATE event includes interaction_id / button_data
- **spawn_background task ownership**: Connection tasks now use runtime.spawn_background
- **Framework soft dependency**: Runtime detection of ErisPulse>=2.7.1 with prompts; version logs output on startup

### Standard API Actions

```python
from ErisPulse import sdk
discord = sdk.adapter.get("discord")

result = await discord.Api.get_self_info()                # GET /users/@me
result = await discord.Api.get_user_info(user_id)         # GET /users/{id}
result = await discord.Api.get_guild_info(guild_id)       # GET /guilds/{id}
result = await discord.Api.get_guild_list()               # GET /users/@me/guilds
result = await discord.Api.get_channel_list(guild_id)     # GET /guilds/{id}/channels
result = await discord.Api.get_guild_member_info(gid, uid)
await discord.Api.delete_message(message_id)              # channel_id auto-completed in the registration table
await discord.Api.leave_guild(guild_id)
result = await discord.Api.Using("main").get_self_info()
```

### Buttons (keyboard / components)

```python
rows = [[{"label": "Click", "type": "callback", "data": "btn:1"},
         {"label": "Website", "type": "link", "data": "https://example.com"}]]
await discord.Send.To("channel", channel_id).Keyboard(rows).Text("Please Select")
# Automatically converts components: callback → custom_id / link → url
```

---

## Supported Message Sending Types

All sending methods are implemented using a fluent interface syntax, for example:
```python
from ErisPulse.Core import adapter
discord = adapter.get("discord")

await discord.Send.To("group", channel_id).Text("Hello World!")
```

The supported sending types include:
- `.Text(text: str)`: Sends a plain text message.
- `.Embed(embed: dict | list)`: Sends an Embed message, supporting single or multiple Embeds.
- `.MergeForward(nodes, title="Merged Chat Records")`: Sends a merged forward message (Embed: title + one field per message, ≤25 fields, value ≤1024).
- `.Image(file: bytes | str, filename: str = "image.png")`: Sends an image, supporting binary data or URL.
- `.File(file: bytes | str, filename: str = None)`: Sends a file, supporting binary data or URL.
- `.Reply(content: str, message_id: str)`: Replies to a specified message (convenient terminal method).
- `.Raw_ob12(message: List[Dict], **kwargs)`: Sends a OneBot12 formatted message.
- `.Raw_json(json_str: str)`: Sends any Discord API request JSON.

### Fluent Modifier Methods (Combinable)

Fluent modifier methods return `self`, supporting chained calls, and must be called before the final sending method:

- `.Reply(message_id: str)`: Replies (references) a specified message, setting `message_reference`.
- `.At(user_id: str)`: Mentions a specified user, converting to `<@user_id>`, can be called multiple times.
- `.AtAll()`: Mentions everyone, converting to `@everyone`.

### Chained Call Examples

```python
# Basic sending
await discord.Send.To("group", channel_id).Text("Hello")

# Reply to message
await discord.Send.To("group", channel_id).Reply(msg_id).Text("Reply message")

# Convenient reply (one step)
await discord.Send.To("group", channel_id).Reply("Reply content", msg_id)

# Mention user
await discord.Send.To("group", channel_id).At("user_id").Text("Hello")

# Mention multiple users
await discord.Send.To("group", channel_id).At("user1").At("user2").Text("Multiple users @")

# Mention all
await discord.Send.To("group", channel_id).AtAll().Text("Announcement")

# Combine methods
await discord.Send.To("group", channel_id).Reply(msg_id).At("user_id").Text("Composite message")

# Embed message
embed = {
    "title": "Notice",
    "description": "This is an embedded message",
    "color": 5814783,
    "fields": [{"name": "Field", "value": "Value", "inline": True}],
}
await discord.Send.To("group", channel_id).Embed(embed)

# Send image
await discord.Send.To("group", channel_id).Image("https://example.com/image.png")
```

### Private Message Sending

When sending private messages, the adapter will automatically create a DM channel:

```python
# Send private message
await discord.Send.To("user", user_id).Text("Private message content")
await discord.Send.To("user", user_id).Embed(embed)
```

### Message Operations

```python
# Recall message
await discord.Send.To("group", channel_id).Recall(msg_id)

# OneBot12 format
ob12_msg = [
    {"type": "text", "data": {"text": "Hello "}},
    {"type": "mention", "data": {"user_id": "user_id"}},
]
await discord.Send.To("group", channel_id).Raw_ob12(ob12_msg)
```

## Send Method Return Values

All send methods return a Task object, which can be awaited directly to obtain the send result. The returned result follows the ErisPulse adapter's standardized return specification:

```python
{
    "status": "ok",           // Execution status: "ok" or "failed"
    "retcode": 0,             // Return code (0 indicates success)
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
| 34000 | Discord API returned error (insufficient permissions, invalid parameters, etc.) |

## Unique Event Types

The platform-specific features require `platform == "discord"` detection before use.

### Core Differences

1. **Server/Channel System**: Discord uses a two-tier structure of servers (Guild) and channels (Channel), with channels being the basic targets for message sending.
2. **Gateway Events**: All events are received via the WebSocket Gateway using the Opcode + Dispatch mechanism.
3. **Intents Subscription**: Event types are subscribed via bitmask, and `MESSAGE_CONTENT` requires Privileged permissions.
4. **Message Segment Types**: Supports text, images, files, videos, audio, Embed, Sticker, and other message segments.
5. **Mention Format**: Discord uses the `<@user_id>` format for user mentions.

### Extended Fields

All unique fields are prefixed with `discord_`:
- `discord_raw`: The raw Discord event data.
- `discord_raw_type`: The raw event type name (e.g., `MESSAGE_CREATE`).
- `discord_guild_id`: The server ID.
- `discord_channel_id`: The channel ID.

### detail_type Mapping

| Discord Scenario | detail_type | Description |
|---|---|---|
| Channel Message | `channel` | ErisPulse extension type |
| Direct Message (DM) | `private` | OneBot12 standard type |

### Event Type Mapping

| Discord Event | OneBot12 type | detail_type | Description |
|---|---|---|---|
| MESSAGE_CREATE | message | channel/private | Message creation |
| MESSAGE_UPDATE | message | channel/private | Message edit |
| MESSAGE_DELETE | notice | group_message_delete / private_message_delete | Message deletion |
| GUILD_MEMBER_ADD | notice | group_member_increase | Member join |
| GUILD_MEMBER_REMOVE | notice | group_member_decrease | Member leave |
| GUILD_MEMBER_UPDATE | notice | group_member_update | Member information update |
| GUILD_ROLE_CREATE | notice | group_role_create | Role creation |
| GUILD_ROLE_DELETE | notice | group_role_delete | Role deletion |
| CHANNEL_CREATE | notice | channel_create | Channel creation |
| CHANNEL_DELETE | notice | channel_delete | Channel deletion |
| INTERACTION_CREATE | request | interaction | Interaction (button, command, etc.) |

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

# Direct message
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
  "alt_message": "[embedded message]"
}

# Message with attachment
{
  "type": "message",
  "detail_type": "channel",
  "message": [
    {"type": "text", "data": {"text": "Look at this image"}},
    {"type": "image", "data": {"file": "image URL", "url": "image URL", "file_name": "image.png"}}
  ],
  "alt_message": "Look at this image[image]"
}
```

### Message Segment Types

Discord message content is automatically converted into corresponding message segments based on the `content`, `attachments`, and `embeds` fields:

| Source | Conversion Type | Description |
|---|---|---|
| content text | `text` | Plain text content |
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
5. Start heartbeat loop: send opcode 1 Heartbeat at intervals of `heartbeat_interval`
6. Receive opcode 0 Dispatch: event dispatch (`t`=event name, `s`=sequence number, `d`=data)
7. Receive opcode 11 Heartbeat ACK: heartbeat acknowledgment

### Opcode Reference

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

### Reconnection and RESUME

- After a connection is disconnected, the adapter automatically retries the connection
- If a previous `session_id` exists, attempt to RESUME (opcode 6) the session first
- RESUME includes `token`, `session_id`, and the last `seq`, restoring missed events after resumption
- When opcode 7 (Reconnect) is received, maintain session state and reconnect
- When opcode 9 (Invalid Session) is received and `d=false`, clear the session and re-authenticate with IDENTIFY

### Heartbeat Mechanism

- After receiving HELLO, wait `heartbeat_interval * random()` milliseconds before sending the first heartbeat
- Subsequently, send a heartbeat every `heartbeat_interval` milliseconds
- The heartbeat includes the last `seq` value (opcode 1, `d: seq`)
- If an ACK (opcode 11) is not received within `heartbeat_interval` milliseconds after sending a heartbeat, consider the connection abnormal and reconnect

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

### Handling Private Messages

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

### Supported Platform Capabilities

- **Inbound**: External systems POST to `callback_path` → converted to OneBot12 events (json/text segments are transparently passed through)
- **Outbound**: Module `Send` → POST to `outgoing_url` (dual bridging)
- **API**: Bridging identity information and runtime status (minimal set)

## v5 Paradigm Update (4.2.0)

- **Minimal API DSL**: `get_self_info`, `get_status`, `get_version`, `get_supported_actions`
- **Framework Soft Dependency**: Runtime detection of ErisPulse>=2.7.1 with prompt; version log output on startup
- Import path updated to Core.Bases

# Platform Feature Description — Webhook Universal Bridge Adapter

This document provides a detailed explanation of the bidirectional bridge protocol, field mapping, and implementation features of the Webhook adapter.

## Overview

The Webhook Adapter is a **protocol-level bridge**, not tied to any specific platform. It exchanges messages via HTTP, enabling any system capable of initiating HTTP requests to integrate with ErisPulse.

```
Inbound Direction                          Outbound Direction
────────────────                          ────────────────
External System                            ErisPulse Module
   │                                         │
   │ POST JSON                               │ Send.Text(...)
   ▼                                         ▼
┌──────────────────────────────────────────────────────┐
│                WebhookAdapter                          │
│  ┌──────────────────┐    ┌──────────────────┐     │
│  │ Inbound Routes    │    │ Outbound Forward │     │
│  │ GET  (Health Check)│    │ client.post()    │     │
│  │ POST (Receive Event)│   │ → outgoing_url   │     │
│  └────────┬─────────┘    └────────▲─────────┘     │
│           │                      │                 │
│           ▼                      │                 │
│  ┌──────────────────┐    ┌──────────────────┐     │
│  │ WebhookConverter │    │ Send Class       │     │
│  │ JSON → OneBot12  │    │ Message Segment → JSON │
│  └────────┬─────────┘    └────────▲─────────┘     │
└───────────┼──────────────────────┼─────────────────┘
            ▼                      │
     adapter.emit(event)    call_api("send_message")
            │                      │
            ▼                      │
       ErisPulse Event System ◄────────┘
```

## Multi-Account Model

Each account is an independent bridge configuration, isolated from each other:

| Account | bot_id | callback_path | outgoing_url | secret |
|---------|--------|---------------|--------------|--------|
| `default` | `webhook_bot` | `/webhook/default` | `https://a.com/recv` | `key1` |
| `discord` | `discord_bot` | `/webhook/discord` | `https://b.com/send` | `key2` |

Each account registers routes independently and emits connect independently upon startup.

## Inbound Protocols

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
|------|------|------|
| `user_id` | Yes | Sender ID |
| `user_nickname` | No | Sender nickname |
| `group_id` | No | Group/channel ID (provided for group sessions) |
| `detail_type` | No | Session type (`private`/`group`), defaults to account default if missing |
| `message` | Yes | Array of OneBot12 message segments |
| `raw` | No | Raw data, stored as-is in `webhook_raw` |

#### Response

```json
{"status": "ok"}
```

Error responses include HTTP status codes:

| Status Code | Meaning |
|--------|------|
| 400 | Invalid JSON / body is not an object |
| 401 | Authentication failed |
| 404 | Unknown account |
| 500 | Event dispatch failed |

### 3. Field Mapping (Inbound JSON → OneBot12 Event)

| Inbound JSON | OneBot12 Event Field | Description |
|-----------|-------------------|------|
| — | `id` | Auto-generated |
| — | `time` | Current Unix timestamp (seconds) |
| — | `type` | Fixed as `message` |
| `detail_type` | `detail_type` | Defaults to account default value if missing |
| — | `platform` | Fixed as `webhook` |
| — | `self.platform` | Fixed as `webhook` |
| — | `self.user_id` | Account `bot_id` |
| `user_id` | `user_id` | Passed through |
| `user_nickname` | `user_nickname` | Passed through (optional) |
| `group_id` | `group_id` | Passed through (optional) |
| `message` | `message` | Passed through |
| Full body | `webhook_raw` | Original request |
| Account name | `webhook_account` | Name of the account that generated the event |
| `type` or `message` | `webhook_raw_type` | Original event type |

## Outbound Protocols

### 1. Sending Messages

When the module calls methods such as `Send.To(...).Text(...)`, the adapter sends a POST request to `outgoing_url`:

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
    {"type": "text", "data": {"text": "Message content"}}
  ],
  "timestamp": 1700000000
}
```

| Field | Description |
|-------|-------------|
| `target_type` | Target type (from `Send.To(type, id)`), defaults to the account's default if not provided |
| `target_id` | Target ID (from `Send.To`) |
| `account` | Sender account name |
| `message` | Array of OneBot12 message segments |
| `timestamp` | Timestamp of sending (in seconds) |

### 2. Response Standardization

The adapter standardizes the response from the outbound target into the ErisPulse standard response format:

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

The message ID is extracted from the `message_id` field of the target's response JSON. If the target does not return a `message_id`, it will be an empty string.

If the request fails, an error response is returned (with `status: "failed"`, `retcode: 33001`).

## Send Method

| Method | Description |
|--------|-------------|
| `Text(text)` | Sends text, encapsulated as `[{"type":"text","data":{"text":text}}]` |
| `Image(file)` | Sends an image, encapsulated as `[{"type":"image","data":{"file":file}}]` |
| `Raw_ob12(message)` | Sends a raw OneBot12 message segment |
| `Json(data)` | Passes raw JSON data, encapsulated as `[{"type":"json","data":{"raw":data}}]` |

`At` / `AtAll` / `Reply` decorators are provided by the framework base class and merged into message segments via `_apply_modifiers`.

## Event Extension Methods (WebhookEventMixin)

| Method | Description |
|--------|-------------|
| `get_raw_data()` | Get the raw request body (`webhook_raw`) |
| `get_detail_type()` | Get the session type |
| `get_webhook_account()` | Get the account name that generated the event |

## Feature Matrix

| Feature | Support Status |
|---------|----------------|
| Multi-account | ✅ Each account has an independent bridge |
| Inbound Authentication | ✅ Header / Query dual mode |
| Health Check | ✅ GET returns status |
| Outbound Authentication | ✅ Secret carried in Header |
| OneBot12 Standard Events | ✅ Complete standard fields |
| Meta Events | ✅ connect / disconnect |
| Route Discovery | ✅ Registered to `webhook` namespace |
| WebSocket | ❌ Only HTTP |
| Media Upload | ❌ Pass-through via URL, no binary relay |

## Notes

1. **One-way Outbound**: If `outgoing_url` is left empty, the account will only receive inbound messages, and sending operations will return an error.
2. **Secret Security**: `secret` is stored as an encrypted value in the configuration (metadata secret), and HTTPS is recommended for transmission.
3. **Unique Path**: The `callback_path` for multiple accounts must be unique to avoid routing conflicts.
4. **Idempotency**: The adapter does not guarantee deduplication of inbound events; external systems should handle retries themselves.
5. **Timeout**: Outbound requests use ErisPulse's built-in `client` and inherit the global timeout configuration.



### 微信公众号适配

# WeChat MP Adapter - Platform Features Documentation

## Basic Information
- Module Name: `ErisPulse-WechatMpAdapter`
- Platform Identifier: `mp` (Alias: `wechat_mp`)
- Module Version: 4.3.0
- Maintainer: ErisPulse
- Dependencies: `cryptography`

## v5 Paradigm Update (4.2.0)

- **BaseConverter Inheritance**: Common fields of converters are built by the framework's build_base_event
- **Api DSL Minimal Set**: get_self_info (appid) / get_status / get_version / get_supported_actions
- **Framework Soft Dependency**: Runtime detection of ErisPulse>=2.7.1 with prompt; version logs output on startup

---

### Platform Capabilities Already Integrated

- **Receiving**: Official account callback messages and events such as follow/unfollow (plaintext/secure mode), signature verification
- **Sending**: Customer service messages (Text/Image, etc., via Send DSL)
- **API**: Account information (appid) and runtime status (minimal set)

---

## Supported Message Sending Types

| Method | Description | WeChat API |
|--------|-------------|------------|
| `Text(text)` | Send text message | Customer Service Message `message/custom/send` |
| `Image(file)` | Send image (automatically uploads and retrieves media_id) | Customer Service Message + `media/upload` |
| `Voice(file)` | Send voice (automatically uploads and retrieves media_id) | Customer Service Message + `media/upload` |
| `Video(file, title, description)` | Send video (automatically uploads and retrieves media_id) | Customer Service Message + `media/upload` |
| `Music(url, title, description, ...)` | Send music | Customer Service Message |
| `News(articles)` | Send news message | Customer Service Message |
| `Template(template_id, data, url)` | Send template message | `message/template/send` |
| `Menu(head_content, list, tail_content)` | Send menu message | Customer Service Message `msgmenu` |
| `Raw_ob12(message)` | Send OneBot12 standard message segment | - |

### Media File Notes
- Three parameter types are supported:
  - `str` URL (starting with `http://` or `https://`): automatically downloads and uploads
  - `str` local file path: automatically reads and uploads
  - `bytes` binary data: uploads directly
  - `str` media_id: prefixed with `media:` to reuse an already uploaded media_id
- After upload, a temporary material `media_id` is obtained, valid for 3 days

### Important Restrictions
- Customer service messages can only be sent **within 48 hours** after user interaction with the official account
- After 48 hours, template messages must be used (requires user-authorized scenarios)
- Unverified service accounts (`verified=false`) cannot send messages proactively, only respond passively (see "Verified Service Account and Passive Reply" above)

## Event Types

### Message Events (message)
All user messages have `detail_type: private` (1v1 scenario for official accounts).

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
| `CLICK` | `menu_click` | Click on a custom menu |
| `VIEW` | `menu_view` | Navigate to a menu link |
| `TEMPLATESENDJOBFINISH` | `template_send_finish` | Template message send result |
| `MASSSENDJOBFINISH` | `mass_send_finish` | Mass message send result |

## Platform Extension Fields

WeChat-specific fields (with `mp_` prefix) in the event object:

| Field | Type | Description |
|------|------|------|
| `mp_raw` | str | Raw XML data |
| `mp_raw_type` | str | Original message/event type |
| `mp_msg_id` | str | WeChat message ID |
| `mp_event` | str | Event type (only for event notifications) |
| `mp_event_key` | str | Event Key (menu click/scan, etc.) |
| `mp_to_user` | str | Receiver's WeChat ID (official account original ID) |
| `mp_from_user` | str | Sender's OpenID |
| `mp_data` | dict | Parsed XML dictionary data |

## Event Extension Methods

Registered via `register_event_mixin("mp", ...)`, allowing direct calls on event objects:

| Method | Return Value | Description |
|--------|--------------|-------------|
| `get_openid()` | str | Sender's OpenID |
| `get_msg_type()` | str | Original WeChat message type |
| `get_event()` | str | Event type (only for event notifications) |
| `get_content()` | str | Pure text content of the message |
| `get_raw_xml()` | str | Raw XML data |

## Configuration Options

### Multi-Account Configuration

Each account corresponds to a public account:

```toml
[WechatMpAdapter.accounts.main]
appid = "wx1234567890abcdef"
appsecret = "your_app_secret_here"
token = "your_callback_token"
encoding_aes_key = ""                    # Required for secure mode/compatibility mode (43 characters)
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
| `appid` | Yes | Public account AppID |
| `appsecret` | Yes | Public account AppSecret (secret) |
| `token` | No | Callback verification Token (recommended to enable signature verification) |
| `encoding_aes_key` | No | Message encryption/decryption key (43 characters, required for secure mode) |
| `callback_path` | No | Callback path template, default `/mp/{account}`, `{account}` will be replaced by the account name |
| `verified` | No | Whether it is a **verified service account**, default `true` (see below for details) |
| `enable` | No | Whether to enable, default true |

### Verified Service Account and Passive Reply (`verified`)

- `verified = true` (default, verified service account): Can use **customer service messages** for active push (within a 48-hour window) and template messages at any time.
- `verified = false` (unverified subscription account):
  - Customer service messages / template messages can **only be sent within the passive reply context of a webhook** (within 15 seconds after receiving a user message, one reply only) — the adapter will automatically intercept and convert the sending into a passive reply.
  - Active push (e.g., scheduled tasks) returns `retcode=34003` error.

## Encryption Mode Explanation

WeChat Official Accounts provide three message encryption and decryption modes:

| Mode | Description | encoding_aes_key | Verification Field |
|------|-------------|------------------|--------------------|
| Plaintext Mode | XML transmitted in plaintext | Not required | `signature` |
| Compatible Mode | Both plaintext and encrypted messages exist | Optional | `signature` / `msg_signature` |
| Secure Mode | Entire message encrypted | Required | `msg_signature` |

This adapter automatically handles:
- Plaintext Mode: Validates `signature` and directly parses XML
- Secure/Compatible Mode: Detects the `Encrypt` field, validates `msg_signature`, and uses AES-256-CBC decryption
- Decryption depends on the `cryptography` library (declared in dependencies)

## Callback Routes

The adapter registers two routes (GET + POST) for each enabled account:

- **GET**: WeChat server access verification. After verifying the signature, it returns the `echostr`.
- **POST**: Receives user messages and events. Verifies the signature → decrypts (if required) → converts → emits.

The actual access paths automatically include the module prefix. For example, if the registered path is `/mp/main`, the actual access paths will be `/mp_{account}_verify/mp/main` and `/mp_{account}_message/mp/main`.

## API Response

All `call_api` calls return a standardized response:

- Success: `status: "ok"`, `retcode: 0`
- Failure: `status: "failed"`, `retcode: 34000+errcode`
- Always includes `mp_raw` (raw response), `message_id`

