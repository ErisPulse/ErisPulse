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

## Next Steps

- **Want to manually control startup/shutdown**: See [Startup Process and Manual Control](advanced/startup.md), which breaks down the initialization process step by step, allowing individual adapters and routers to be started or stopped independently.
- **Want to understand lazy loading and sleeping**: See [Lazy Loading System](advanced/lazy-loading.md), which includes the complete syntax for lazy activation driven by `activate_on` events.
- **Want to use lifecycle events effectively when writing modules**: See [Lifecycle Management](advanced/lifecycle.md), which covers all lifecycle events and listener methods.