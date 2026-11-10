# Module Core Concepts

> [!NOTE]
> **L1 Core Must-Read** — one of the five core documents in the homepage's "Reading Path"; essential for module development.

This document explains the complete lifecycle of a module from loading to unloading, along with how to use declarative configuration and storage — what the framework automatically does for you and what you only need to write, so you'll know exactly where you stand after reading.

## Module Lifecycle

### Load Strategy

```python
from ErisPulse.Core.Bases import BaseModule
from ErisPulse.loaders import ModuleLoadStrategy

class MyModule(BaseModule):
    @staticmethod
    def get_load_strategy():
        """Return module load strategy"""
        return ModuleLoadStrategy(
            lazy_load=True,   # Lazy load or immediate load
            priority=0,       # Load priority (higher value loads earlier)
            depends=["OtherModule"]  # Optional: declare dependencies on other modules
        )
```

> If modules declared in `depends` are not registered, the current module will be skipped and a warning is logged. The loading order is determined by topological sorting, with modules at the same level sorted by `priority` in descending order.

> [!NOTE]
> **Cascading Unload / Cascading Reload** (ErisPulse **2.8.0+**): When unloading a module that is depended on by other modules, the dependent modules will be **cascaded unloaded first** (with logs indicating the cascade chain); during hot reload of any module (local plugin / runtime registered / PyPI installed package), dependent modules will also be **cascaded reloaded**, avoiding dependent modules holding invalid instance references and continuing to run. Circular dependencies will be rejected at load time with a `RuntimeError`.
>
> **Reload is Full Reload** (ErisPulse **2.11.0+**): `reload()` by default clears the import cache by top-level package name and re-imports dependent code, performs syntax pre-check before unloading (fails to reject unloading, old instances continue to serve), and verifies code identity after success (false reload warning / `stale` flag); load failure can be directly queried via `sdk.module.last_error(name)` on-site (including traceback).

### on_load Method

Called when the module is loaded, used for initializing resources and registering event handlers:

```python
async def on_load(self, event):
    # Register event handlers
    @command("hello", help="Greeting command")
    async def hello_handler(event):
        await event.reply("Hello!")
    
    # Use SDK built-in HTTP client (automatically manages connection pool, no need to manually create session)
    # Send requests via sdk.client
```

### on_unload Method

Called when the module is unloaded, used for cleaning up resources:

```python
async def on_unload(self, event):
    # Clean up custom resources
    # sdk.client is managed by the framework, no need to manually close
    
    # Cancel event handlers (handled automatically by the framework)
    self.logger.info("Module unloaded")
```

> Creation and cleanup of background tasks (`self.spawn()` / framework's default cancellation) are detailed in [Lifecycle Management](../../advanced/lifecycle.md#background-task-ownership-and-automatic-cancellation).

### on_before_unload Method

> [!NOTE]
> This hook requires ErisPulse **2.11.0+**.

An optional hook triggered in the **first step** of the unload pipeline (before `on_unload` and resource cleanup) — at this point, all module resources are still intact, suitable for saving state to `sdk.storage` before unloading / sleeping / reloading, which can be restored in the next `on_load` (lazy loading resumes based on this): 

```python
async def on_before_unload(self, event):
    # event["reason"] indicates the reason: unload / reload / disable / cascade / dormant
    if event["reason"] in ("reload", "dormant"):
        await self.state.aset("snapshot", self.collect_state())
```

Failure of the hook only logs a warning and does not block the unload process; modules without this hook behave unchanged. The semantics of sleeping / waking are detailed in [Lazy Loading Dormancy](../../advanced/lazy-loading.md#lazy-loading-dormancy-dormant_after).

### Unload vs. Purge Unload

> [!NOTE]
> This feature requires ErisPulse **2.8.0+**.

`unload()` by default only **unloads** (unloads instance and resources), but retains registration stubs (module class and metadata) — the module can be rediscovered by `discover` and re-instantiated with `load()`, no need to re-register.

When you need to **completely unload** (release module class references, clean up `sys.modules`, allowing plugins and their exclusive dependencies to be collected by GC), pass `purge=True`:

```python
# Only unloads: retains registration stubs, can be reloaded anytime
await sdk.module.unload("MyModule")

# Completely unloads: deletes registration stubs + cleans up sys.modules (plugin source)
await sdk.module.unload("MyModule", purge=True)
```

| Semantics | `unload()` default | `unload(purge=True)` |
|-----------|--------------------|----------------------|
| Unloads instance and resources (events/task/routes/lifecycle/i18n) | ✅ | ✅ |
| Retains registration stubs (module class and metadata) | ✅ | ❌ deleted |
| Cleans up `sys.modules` (only plugin folder sources) | ❌ | ✅ |
| Module class can be collected by GC | ❌ | ✅ |
| Reload | `load()` is directly available | Requires `register()` + `load()` first |

> When `purge=True`, cascaded unloaded dependents are also purged; after unloading, the framework performs `gc.collect()` and checks if module class/instance is collectible, residual references are warned in logs (including reference source, DEBUG level).

### Lifecycle Overview

Putting the above methods together, the framework does **all the behind-the-scenes work** when loading and unloading a module:

```mermaid
flowchart TD
    subgraph Load["Load (register → load)"]
        L1["register: register module class and metadata"] --> L2["Dependency validation<br/>Skips if missing"]
        L2 --> L3["Topological sorting (Kahn + priority)"]
        L3 --> L4["Inject owner: current_owner"]
        L4 --> L5["Generate configuration template + register i18n translation keys"]
        L5 --> L6["Instantiate module (inject sdk)"]
        L6 --> L7["Call on_load()"]
        L7 --> L8["Mount to sdk attribute + emit module.load"]
    end

    subgraph Unload["Unload (unload)"]
        U1["Call on_unload()"] --> U2["Default cancellation of background tasks (self.spawn ownership)"]
        U2 --> U3["Clean up i18n translation keys"]
        U3 --> U4["Remove routes / commands / event handlers (by owner)"]
        U4 --> U5["Clean up lifecycle hooks (by owner)"]
        U5 --> U6["Remove SDK attribute + lazy load proxy"]
        U6 --> U7["emit module.unload"]
    end

    Load --> Unload
```

**What the framework does for you during loading** (you only need to write `on_load`, the rest is automatic):

| Step | What the framework automatically does |
|------|---------------------------------------|
| Owner injection | Wrap the module name with `owner_scope` during instantiation — commands/events/hooks/background tasks registered in `on_load` are **automatically assigned to this module**, and cleaned up in one click during unload by owner |
| Configuration template | Modules declaring `ConfigClass` have configuration segments `ErisPulse.<ModuleName>` automatically generated/loaded by the framework |
| i18n translation keys | Modules declaring `I18nClass` have translation keys automatically registered (unregistered automatically during unload) |
| Dependency topology | Sort by `depends` declaration, ensuring dependent modules are loaded first; circular dependencies are rejected with a `RuntimeError` |
| SDK mounting | After instantiation, mount to `sdk.<ModuleName>`, allowing you to access via `sdk.MyModule.xxx` |

**What the framework cleans up during unload** (corresponding to U1→U7 above): After `on_unload` completes, it performs a default cleanup — background tasks are forcibly cancelled (created via `self.spawn`, graceful shutdown should be handled manually in `on_unload`), i18n keys, routes, commands/event handlers, lifecycle hooks, finally removing SDK attributes. `purge=True` additionally deletes registration stubs + cleans up `sys.modules`.

> This automatic cleanup is the foundation for the principle that "you only need to write `on_load`/`on_unload`, without manually unregistering" — the framework uses owner assignment to make "who registers cleans up" a one-click operation.

## SDK Objects

### Accessing Core Modules

```python
from ErisPulse import sdk

# Access all core modules through the sdk object
sdk.logger.info("Log message")
sdk.storage.set("key", "value")

# Module-specific small states (counters/switches/last run time) should be accessed via self.state —
# Keys are automatically prefixed with module.state.<module name>. and persist after module unload/reload:
count = self.state.get("runs", 0) + 1
self.state.set("runs", count)            # Synchronous (any context)
await self.state.aset("runs", count)     # Asynchronous path
await self.state.aget("runs", 0)
config = sdk.config.getConfig("MyModule")
```

### Inter-Module Communication

```python
# Access other modules
other_module = sdk.OtherModule
result = await other_module.some_method()
```

## Adapter Send Method Query

Because the new standard specification requires overriding the `__getattr__` method to implement the fallback send mechanism, the `hasattr` method can no longer be used to check whether a method exists. Starting from `2.3.5`, the ability to query send methods has been added.

### Listing Supported Send Methods

```python
# List all send methods supported by the platform
methods = sdk.adapter.list_sends("onebot11")
# Returns: ["Text", "Image", "Voice", "Markdown", ...]
```

### Getting Method Details

```python
# Get the details of a method
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

## Configuration Management

### Declarative Configuration (Recommended)

Since v2.5.2, modules can declare a configuration class via `ConfigClass`, sharing the same configuration Schema system as adapters. Configuration is read in real time through `self.cfg`, so changes take effect immediately:

```python
from dataclasses import dataclass, field
from ErisPulse.Core.Bases import BaseModule
from ErisPulse.Core.Bases import BaseConfig

@dataclass
class MyModuleConfig(BaseConfig):
    api_key: str = field(
        default="",
        metadata={
            "description": {"i18n": "my_module.api_key", "default": "API Key"},
            "required": True,
            "secret": True,
            "ui": {"widget": "password", "group": "basic", "order": 1},
        },
    )
    timeout: int = field(
        default=30,
        metadata={
            "description": {"i18n": "my_module.timeout", "default": "Timeout (seconds)"},
            "ui": {"widget": "number", "group": "advanced", "order": 2},
        },
    )

class MyModule(BaseModule):
    ConfigClass = MyModuleConfig

    def __init__(self, sdk):
        self.sdk = sdk
        self.logger = sdk.logger.get_child("MyModule")

    async def on_load(self, event):
        self.logger.info("Module loaded")

    async def on_unload(self, event):
        pass

    async def do_something(self):
        cfg = self.cfg  # Read in real time, type-safe
        api_key = cfg.api_key
        timeout = cfg.timeout
```

`BaseConfig` is a general-purpose configuration base class suitable for adapters, modules, external projects, and any other scenario. Configuration fields support i18n multilingual descriptions (see the [i18n documentation](../../advanced/i18n.md#multilingual-configuration-fields) for details).

> [!NOTE]
> The lifecycle of modules (including adapters) — loading, unloading, enabling/disabling, and so on — is managed uniformly by the framework (the `module manager` / `scope` provide query and control APIs). `ConfigClass` should only carry business parameters; modules do not need to nest logic inside themselves that decides "whether they should start".

The configuration Schema system also supports the following (v2.8.0+, see [adapter core-concepts](../adapters/core-concepts.md#metadata-conventions) for details):

- **Automatic field descriptions from docstrings**: when metadata `description` is not declared, a fallback is automatically extracted from the docstring's `:ivar field: description` or `Attributes:` section
- **Nested dataclass configuration**: when a field's type is a nested dataclass, schema/template/validation are handled recursively, and the WebUI renders it as nested groups
- **`example` non-persisted fields**: fields with `metadata={"example": True}` are not written to config.toml and are only recorded in `config.full.example` (suitable for verbose, rarely touched advanced configuration items); once users set them manually, they persist normally

### Declarative Translation Keys (v2.7.0+)

Since v2.7.0, modules can also declare translation keys centrally through a nested class `I18nClass`, just like declaring `ConfigClass`. The framework **automatically registers** all declared translation keys at load time — no need to call `i18n.register()` manually — and registration happens before config template generation, ensuring that i18n keys referenced in configuration descriptions are already available.

```python
from ErisPulse.Core.Bases import BaseConfig, BaseI18n, I18nKey

class MyModule(BaseModule):
    # Configuration class (optional)
    @dataclass
    class ConfigClass(BaseConfig):
        welcome_msg: str = field(
            default="Welcome",
            metadata={
                "description": {"i18n": "mymodule.welcome_msg", "default": "Welcome message"},
            },
        )

    # Translation key collection class (optional)
    class I18nClass(BaseI18n):
        # Attribute names are automatically joined into the full key path: <module name>.<attribute name>
        welcome_msg: I18nKey = I18nKey(
            default="Welcome Message",   # Language-independent fallback
            zh_CN="Welcome message",
            zh_TW="歡迎訊息",
            en="Welcome Message",
            ja="ウェルカムメッセージ",
            ru="Приветственное сообщение",
        )
        hello: I18nKey = I18nKey(
            default="Hello, {name}!",
            zh_CN="Hello, {name}!",
            zh_TW="你好，{name}！",
            en="Hello, {name}!",
            ja="こんにちは、{name}！",
            ru="Привет, {name}!",
        )
```

For details, see [i18n Recommended Approach](../../advanced/i18n.md#recommended-approach-declaring-translation-keys-via-i18nclass-v270).

### Reading Configuration Manually (Deprecated)

> **Deprecated**: Please use [Declarative Configuration](#declarative-configuration-recommended) + real-time reading via `self.cfg` instead.

```python
class MyModule(BaseModule):
    def __init__(self, sdk):
        self.sdk = sdk

    def _load_config(self):
        config = self.sdk.config.getConfig("MyModule")
        if not config:
            self.sdk.config.setConfig("MyModule", {"api_key": "", "timeout": 30})
            return {"api_key": "", "timeout": 30}
        return config
```

## Storage System

### Basic Usage

```python
# Store data
sdk.storage.set("user:123", {"name": "Zhang San"})

# Get data
user = sdk.storage.get("user:123", {})

# Delete data
sdk.storage.delete("user:123")
```

### Using Transactions

```python
# Use a transaction to ensure data consistency
with sdk.storage.transaction():
    sdk.storage.set("key1", "value1")
    sdk.storage.set("key2", "value2")
    # If any operation fails, all changes are rolled back
```

## Event Handling

### Registering Event Handlers

```python
from ErisPulse.Core.Event import command, message

# Register a command
@command("info", help="Get information")
async def info_handler(event):
    await event.reply("Here is the information")

# Register a message handler
@message.on_group_message()
async def group_handler(event):
    sdk.logger.info(f"Received group message: {event.get_text()}")
```

### Event Handler Lifecycle

The framework automatically manages the registration and unregistration of event handlers; you only need to register them in `on_load`.

## Lazy Loading Mechanism

### How It Works

```python
# The module is only initialized on first access
result = await sdk.my_module.some_method()
# ↑ This triggers module initialization
```

### Immediate Loading

For modules that need to be initialized immediately (such as listeners, timers):

```python
@staticmethod
def get_load_strategy():
    return ModuleLoadStrategy(
        lazy_load=False,  # Load immediately
        priority=100
    )
```

## Error Handling

### Catching Exceptions

```python
async def handle_event(self, event):
    try:
        # Business logic
        await self.process_event(event)
    except ValueError as e:
        self.logger.warning(f"Invalid parameter: {e}")
        await event.reply(f"Invalid parameter: {e}")
    except Exception as e:
        self.logger.error(f"Processing failed: {e}")
        raise
```

### Logging

```python
# Use different log levels
self.logger.debug("Debug info")    # Detailed debug information
self.logger.info("Running status")      # Normal operation information
self.logger.warning("Warning message")  # Warning message
self.logger.error("Error message")    # Error message
self.logger.critical("Fatal error") # Fatal error
```

## Related Documentation

### Continuing the Learning Path

- [Event Wrapper Class](event-wrapper.md) - Event handling in depth

### Going Deeper and Troubleshooting

- [Module Best Practices](best-practices.md) - Developing high-quality modules
- [Module Development Getting Started](getting-started.md) - Review the steps for building your first module