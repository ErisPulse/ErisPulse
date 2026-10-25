---
name: erispulse-hot-reload
description: "适用于：改代码不重启（热重载）、闲置自动归眠（dormant_after）、运行时注册模块。覆盖场景：When using lazy-loaded modules or `activate_on` event-driven activation. Skip it if not needed; it does not affect the use of any other features.。By following this guide, you will create a runnable module that responds to the `/hello` command, and gain an understanding of the module's project structure, registration method, and load/unload hooks — all subsequent module documentation is built upon this foundation.。"
---

# ErisPulse 热重载与懒加载休眠

This skill is auto-built from the ErisPulse documentation.
Repository: https://github.com/ErisPulse/ErisPulse
Source paths are annotated per section; see docs/ in the repository for the latest content.

## 懒加载与休眠

> 来源: `docs/en/advanced/lazy-loading.md`（https://github.com/ErisPulse/ErisPulse/blob/main/docs/en/advanced/lazy-loading.md）

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

## 模块开发入门（加载策略）

> 来源: `docs/en/developer-guide/modules/getting-started.md`（https://github.com/ErisPulse/ErisPulse/blob/main/docs/en/developer-guide/modules/getting-started.md）

# Getting Started with Module Development

> [!NOTE]  
> **L1 Core Reading** — One of the five core documents in the "Reading Path" on the homepage, essential for module development.

By following this guide, you will create a runnable module that responds to the `/hello` command, and gain an understanding of the module's project structure, registration method, and load/unload hooks — all subsequent module documentation is built upon this foundation.

## Project Structure

A standard module structure:

```
MyModule/
├── pyproject.toml
├── README.md
├── LICENSE
└── MyModule/
    ├── __init__.py
    └── Core.py
```

## pyproject.toml Configuration

```toml
[project]
name = "ErisPulse-MyModule"
version = "1.0.0"
description = "Module function description"
readme = "README.md"
requires-python = ">=3.10"
license = { file = "LICENSE" }
authors = [ { name = "yourname", email = "your@mail.com" } ]
dependencies = []

[project.urls]
"homepage" = "https://github.com/yourname/MyModule"

[project.entry-points."erispulse.module"]
"MyModule" = "MyModule:Main"
```

## __init__.py

```python
from .Core import Main
```

## Core.py - Core Module

```python
from ErisPulse import sdk
# Recommended root import (2.10+): Common symbols are directly imported from the root package, deep paths are still compatible
from ErisPulse import BaseModule, command

class Main(BaseModule):
    def __init__(self, sdk):
        self.sdk = sdk
        self.logger = sdk.logger.get_child("MyModule")
        self.storage = sdk.storage
    
    @staticmethod
    def get_load_strategy():
        """Return the module loading strategy"""
        from ErisPulse.loaders import ModuleLoadStrategy
        return ModuleLoadStrategy(
            lazy_load=True,
            priority=0,
            depends=[],  # Optional: list of other modules this module depends on
            # Optional: event-driven lazy activation - declare triggers, module automatically loads when first matching event/command arrives
            # activate_on=[{"command": {"name": "hello", "help": "Send a greeting"}}],
        )
    
    async def on_load(self, event):
        """Called when the module is loaded"""
        @command("hello", help="Send a greeting")
        async def hello_command(event):
            name = event.get_user_nickname() or "friend"
            await event.reply(f"Hello, {name}!")
        
        self.logger.info("Module loaded")
    
    async def on_unload(self, event):
        """Called when the module is unloaded"""
        self.logger.info("Module unloaded")
```

> **Configuration Reading**: The basic example above does not use configuration. To read configuration, it is recommended to declare a nested `ConfigClass` and access it via `self.cfg` for real-time reading (see [Module Core Concepts](core-concepts.md#recommended-declarative-configuration)). The old method of manually calling `_load_config()` is deprecated.

## Testing Module

### Local Testing

```bash
# Install the module in the project directory
epsdk install ./MyModule

# Run the project
epsdk run main.py --reload
```

### Test Commands

Send a command to test:

```
/hello
```

## Core Concepts

### BaseModule Base Class

All modules must inherit from `BaseModule`, providing the following methods:

| Method | Description | Required |
|--------|-------------|----------|
| `__init__(self, sdk)` | Constructor (framework passes `sdk` instance) | No |
| `get_load_strategy()` | Returns the load strategy | No |
| `get_meta()` | Returns module metadata (optional) | No |
| `on_load(self, event)` | Called when the module is loaded | Yes |
| `on_unload(self, event)` | Called when the module is unloaded | Yes |

### Module Meta Information

> [!NOTE]
> This feature requires ErisPulse **2.8.0+**.

Declare module metadata (what the module does, its category, etc.) via `get_meta()`.  
Metadata is the **general introduction data** of a module, consumed by help modules, dashboard module lists, module stores, and other interfaces/ecosystem modules.

Similar to `get_load_strategy()` returning `ModuleLoadStrategy`, **it is recommended to return an instance of the `ModuleMeta` configuration class** (with type hints and IDE completion), but direct return of a dict is also supported:

```python
class MyModule(BaseModule):
    @staticmethod
    def get_meta() -> ModuleMeta:
        return ModuleMeta(
            name="Weather",               # Display name (default registration name)
            description="Query city weather",  # Module description
            version="1.0.0",
            author="ErisDev",
            group="Tools",               # Function group
            tags=["Weather", "Query"],
        )
```

Alternative dict-based approach:

```python
class MyModule(BaseModule):
    @staticmethod
    def get_meta() -> dict:
        return {
            "name": "Weather",
            "description": "Query city weather",
            "version": "1.0.0",
            "author": "ErisDev",
            "group": "Tools",
            "tags": ["Weather", "Query"],
        }
```

- `module.get_meta("MyModule")` retrieves the parsed metadata (class declaration > registered info, automatically completing the module's command name).
- `module.get_commands_overview()` aggregates "module meta + its registered commands (aliases/groups/help)" into a module-organized command overview.
- The module owner of a command can be obtained via `cmd_info["owner"]` (automatically injected by the context system during registration).

#### i18n Support for Meta Fields

The values of meta information fields can be plain strings or i18n dictionaries `{"i18n": "key.path", "default": "fallback text"}` (consistent with the `description` configuration convention).  
Translation keys are declared and registered via `I18nClass`. When reading with `module.get_meta()`, the values are automatically resolved into the current language text:

```python
class MyModule(BaseModule):
    class I18nClass(BaseI18n):
        meta_description: I18nKey = I18nKey(
            default="Weather lookup",
            zh_CN="查询城市天气",
            en="Weather lookup",
        )

    @staticmethod
    def get_meta() -> ModuleMeta:
        return ModuleMeta(
            name="Weather",
            description={"i18n": "MyModule.meta_description", "default": "Weather lookup"},
        )
```

### SDK Object

Access core features through the `sdk` object:

```python
from ErisPulse import sdk

sdk.storage    # Storage system
sdk.config     # Configuration system
sdk.logger     # Logging system
sdk.adapter    # Adapter system
sdk.router     # Routing system
sdk.lifecycle  # Lifecycle system
```

### Continue Your Learning Path

- [Module Core Concepts](core-concepts.md) - Deep dive into module architecture
- [Event Wrapper Class Explained](event-wrapper.md) - Learn about Event objects

### After Writing

- [Module Best Practices](best-practices.md) - Develop high-quality modules
