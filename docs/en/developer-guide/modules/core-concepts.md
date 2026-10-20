# Core Concepts of Modules

> [!NOTE]
> **L1 Core Reading** – One of the five core documents in the "Reading Path" on the homepage, essential for module development.

Understanding the core concepts of ErisPulse modules is the foundation for developing high-quality modules.

## Module Lifecycle

### Loading Strategy

```python
from ErisPulse.Core.Bases import BaseModule
from ErisPulse.loaders import ModuleLoadStrategy

class MyModule(BaseModule):
    @staticmethod
    def get_load_strategy():
        """Return the module loading strategy"""
        return ModuleLoadStrategy(
            lazy_load=True,   # Lazy load or immediate load
            priority=0,       # Loading priority (higher value loads earlier)
            depends=["OtherModule"]  # Optional: declare dependencies on other modules
        )
```

> If modules declared in `depends` are not registered, the current module will be skipped and a warning is logged. The loading order is determined by topological sorting, with modules at the same level sorted by `priority` in descending order.

> [!NOTE]
> **Cascading Unload / Cascading Reload** (ErisPulse **2.8.0+**): When unloading a module that is depended on by other modules, the dependent modules will be **first cascaded unloaded** (with logs explaining the cascade chain). When hot-reloading any module (local plugin / runtime registered / PyPI installed package), dependent modules are also **cascaded reloaded**, preventing dependent modules from holding invalid instance references and continuing to run. Circular dependencies are rejected at load time with a `RuntimeError`.
>
> **Reload means full reload** (ErisPulse **2.11.0+**): `reload()` by default clears the import cache by the top-level package name and re-imports dependent codes. Before unloading, a syntax pre-check is automatically performed (fails and refuses to unload, old instances continue to serve), and after success, code identity is verified (false reload warning / `stale` flag); load failures can be directly queried on-site via `sdk.module.last_error(name)` (including traceback).

### on_load Method

Called when the module is loaded, used for initializing resources and registering event handlers:

```python
async def on_load(self, event):
    # Register event handlers
    @command("hello", help="Greeting command")
    async def hello_handler(event):
        await event.reply("Hello!")
    
    # Use the SDK's built-in HTTP client (automatically manages connection pool, no need to manually create session)
    # Requests can be sent through sdk.client
```

### on_unload Method

Called when the module is unloaded, used for cleaning up resources:

```python
async def on_unload(self, event):
    # Clean up custom resources
    # sdk.client is managed by the framework, no need to manually close
    
    # Cancel event handlers (handled automatically by the framework)
    self.logger.info("Module has been unloaded")
```

> Creation and cleanup of background tasks (`self.spawn()` / framework's default cancellation) are detailed in [Lifecycle Management](../../advanced/lifecycle.md#background-task-ownership-and-automatic-cancellation).

### on_before_unload Method

> [!NOTE]
> This hook requires ErisPulse **2.11.0+**.

An optional hook triggered in the **first step** of the unload pipeline (before `on_unload` and resource cleanup) — at this point, all module resources are still intact, suitable for saving state to `sdk.storage` before unloading / sleeping / reloading, which can be restored next time in `on_load` (lazy-loaded sleep state continuation is based on this):

```python
async def on_before_unload(self, event):
    # event["reason"] indicates the reason: unload / reload / disable / cascade / dormant
    if event["reason"] in ("reload", "dormant"):
        await self.sdk.storage.aset(f"{self._module_name}:state", self.collect_state())
```

A failed hook only logs a warning and does not block the unload process; modules without this hook behave as before. The semantics of sleep / wake are detailed in [Lazy Loading Sleep](../../advanced/lazy-loading.md#lazy-loading-sleep-dormant_after).

### Unload vs. Purge Unload

> [!NOTE]
> This feature requires ErisPulse **2.8.0+**.

`unload()` by default only **unloads** (unloads the instance and resources), but retains the registration stub (module class and metadata) — the module can be rediscovered and reloaded via `load()` without needing to `register()` again.

When you need to **completely unload** (release module class references, clean up `sys.modules`, allowing plugins and their exclusive dependencies to be garbage collected), pass `purge=True`:

```python
# Only unloads: retains registration stub, can be reloaded anytime
await sdk.module.unload("MyModule")

# Completely unloads: deletes registration stub + cleans sys.modules (only for plugin folder sources)
await sdk.module.unload("MyModule", purge=True)
```

| Semantics | `unload()` default | `unload(purge=True)` |
|-----------|--------------------|----------------------|
| Unload instance and resources (events/task/route/lifecycle/i18n) | ✅ | ✅ |
| Retain registration stub (module class and metadata) | ✅ | ❌ Deleted |
| Clean up `sys.modules` (only for plugin folder sources) | ❌ | ✅ |
| Module class can be garbage collected | ❌ | ✅ |
| Reload | `load()` directly usable | Must `register()` + `load()` first |

> When `purge=True`, cascading unloaded dependents are also purged; after unloading, the framework will `gc.collect()` and check if module class/instance is collectible, residual references will be warned in logs (including reference source, DEBUG level).

### Lifecycle Overview

Putting the above methods together, here is **everything the framework does behind the scenes** when loading and unloading a module:

```mermaid
flowchart TD
    subgraph Load["Load (register → load)"]
        L1["register: Register module class and metadata"] --> L2["Dependency validation<br/>Skips if missing"]
        L2 --> L3["Topological sorting (Kahn + priority)"]
        L3 --> L4["Inject owner into current_owner"]
        L4 --> L5["Generate configuration template + register i18n translation keys"]
        L5 --> L6["Instantiate module (inject sdk)"]
        L6 --> L7["Call on_load()"]
        L7 --> L8["Mount to sdk attribute + emit module.load"]
    end

    subgraph Unload["Unload (unload)"]
        U1["Call on_unload()"] --> U2["Default cancel background tasks (self.spawn ownership)"]
        U2 --> U3["Clean up i18n translation keys"]
        U3 --> U4["Remove routes / commands / event handlers (by owner)"]
        U4 --> U5["Clean up lifecycle hooks (by owner)"]
        U5 --> U6["Remove SDK attribute + lazy-load proxy"]
        U6 --> U7["emit module.unload"]
    end

    Load --> Unload
```

**What the framework does for you during loading** (you only need to write `on_load`, the rest is automatic):

| Step | What the framework does automatically |
|------|---------------------------------------|
| Owner injection | Wrap the module name with `owner_scope` during instantiation — all commands/events/hooks/background tasks you register in `on_load` are **automatically assigned to this module**, and are cleaned up in one click during unload by owner |
| Configuration template | Modules declaring `ConfigClass` automatically generate/populate the `ErisPulse.<ModuleName>` configuration section |
| i18n translation keys | Modules declaring `I18nClass` automatically register translation keys (automatically unregistered during unload) |
| Dependency topology | Sort by `depends` declaration, ensuring dependent modules are loaded first; circular dependencies are rejected with a `RuntimeError` |
| SDK mounting | After instantiation, mount to `sdk.<ModuleName>`, allowing you to access via `sdk.MyModule.xxx` |

**What the framework cleans up during unload** (corresponding to U1→U7 above): After `on_unload` runs, it performs a default cleanup — background tasks are forcibly canceled (created via `self.spawn`, please handle gracefully in `on_unload`), i18n keys, routes, commands/event handlers, lifecycle hooks, and finally removes SDK attributes. `purge=True` additionally deletes the registration stub and cleans up `sys.modules`.

> This automatic cleanup is the foundation for the principle of "you only need to write `on_load`/`on_unload`, no need to manually unregister" — the framework uses owner assignment to make "who registers, who cleans up" into a one-click operation.

## SDK Objects

### Accessing Core Modules

```python
from ErisPulse import sdk

# Access all core modules through the sdk object
sdk.logger.info("Log")
sdk.storage.set("key", "value")
config = sdk.config.getConfig("MyModule")
```

### Inter-Module Communication

```python
# Access other modules
other_module = sdk.OtherModule
result = await other_module.some_method()
```

## Adapter Send Method Query

Due to the new standard specification requiring the use of the rewritten `__getattr__` method to implement the fallback sending mechanism, it is no longer possible to use the `hasattr` method to check if a method exists. Starting from `2.3.5`, a new feature has been added to query send methods.

### List Supported Send Methods

```python
# List all send methods supported by the platform
methods = sdk.adapter.list_sends("onebot11")
# Returns: ["Text", "Image", "Voice", "Markdown", ...]
```

### Get Detailed Method Information

```python
# Get detailed information about a specific method
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

Starting from v2.5.2, modules can declare configuration classes using `ConfigClass`, which shares the same configuration Schema system with adapters. Configuration is read in real-time via `self.cfg`, and changes take effect immediately:

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
        cfg = self.cfg  # Real-time reading, type-safe
        api_key = cfg.api_key
        timeout = cfg.timeout
```

`BaseConfig` is a generic configuration base class suitable for adapters, modules, external projects, and any scenario. Configuration fields support i18n multilingual descriptions (see [i18n documentation](../../advanced/i18n.md#multi-language-configuration-fields)).

> [!NOTE]
> The lifecycle of modules (including adapters) such as loading, unloading, starting, and stopping is managed uniformly by the framework (`module manager` / `scope` provides query and control APIs). `ConfigClass` should only carry business parameters; modules should not embed logic inside to determine whether they should start.

The configuration Schema system also supports (v2.8.0+, see [Adapter core-concepts](../adapters/core-concepts.md#metadata-conventions)):

- **Automatic docstring-based field description generation**: When `metadata.description` is not declared, the system automatically extracts fallback descriptions from the docstring's `:ivar field: description` or `Attributes:` section.
- **Nested dataclass configuration**: When a field type is a nested dataclass, schema/template/validation is recursively processed, and the WebUI renders it as nested groups.
- **`example` non-persistent field**: Fields with `metadata={"example": True}` are not written to `config.toml`, but recorded in `config.full.example` (suitable for complex and rarely touched advanced configuration items). After manual user settings, these fields are persisted normally.

### Declarative Translation Keys (v2.7.0+)

Starting from v2.7.0, modules can also declare translation keys centrally using a nested class `I18nClass`, just like declaring `ConfigClass`. The framework automatically registers all declared translation keys during loading, without requiring manual calls to `i18n.register()`, and the registration occurs before the configuration template is generated, ensuring that i18n keys referenced in configuration descriptions are available.

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
        # Property names are automatically concatenated into full key paths: <module_name>.<property_name>
        welcome_msg: I18nKey = I18nKey(
            default="Welcome Message",   # Language-agnostic fallback
            zh_CN="欢迎消息",
            zh_TW="歡迎訊息",
            en="Welcome Message",
            ja="ウェルカムメッセージ",
            ru="Приветственное сообщение",
        )
        hello: I18nKey = I18nKey(
            default="Hello, {name}!",
            zh_CN="你好，{name}！",
            zh_TW="你好，{name}！",
            en="Hello, {name}!",
            ja="こんにちは、{name}！",
            ru="Привет, {name}!",
        )
```

See [Recommended i18n Writing Style](../../advanced/i18n.md#recommended-approach-declaring-translation-keys-via-i18nclass).

### Manual Configuration Reading (Deprecated)

> **Deprecated**: Please switch to [Declarative Configuration](#declarative-configuration-recommended) + real-time reading via `self.cfg`.

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

# Retrieve data
user = sdk.storage.get("user:123", {})

# Delete data
sdk.storage.delete("user:123")
```

### Transaction Usage

```python
# Use transactions to ensure data consistency
with sdk.storage.transaction():
    sdk.storage.set("key1", "value1")
    sdk.storage.set("key2", "value2")
    # If any operation fails, all changes will be rolled back
```

## Event Handling

### Event Handler Registration

```python
from ErisPulse.Core.Event import command, message

# Register command
@command("info", help="Get information")
async def info_handler(event):
    await event.reply("This is information")

# Register message handler
@message.on_group_message()
async def group_handler(event):
    sdk.logger.info(f"Received group message: {event.get_text()}")
```

### Event Handler Lifecycle

The framework automatically manages the registration and unregistration of event handlers. You only need to register them in `on_load`.

## Lazy Loading Mechanism

### How It Works

```python
# The module is initialized only when first accessed
result = await sdk.my_module.some_method()
# ↑ This triggers module initialization
```

### Immediate Loading

For modules that need to be initialized immediately (such as listeners or timers):

```python
@staticmethod
def get_load_strategy():
    return ModuleLoadStrategy(
        lazy_load=False,  # Immediate loading
        priority=100
    )
```

## Error Handling

### Exception Handling

```python
async def handle_event(self, event):
    try:
        # Business logic
        await self.process_event(event)
    except ValueError as e:
        self.logger.warning(f"Parameter error: {e}")
        await event.reply(f"Parameter error: {e}")
    except Exception as e:
        self.logger.error(f"Processing failed: {e}")
        raise
```

### Logging

```python
# Use different logging levels
self.logger.debug("Debug information")    # Detailed debug information
self.logger.info("Running status")        # Normal running information
self.logger.warning("Warning information") # Warning information
self.logger.error("Error information")    # Error information
self.logger.critical("Critical error")    # Critical error
```

## Related Documentation

- [Getting Started with Module Development](getting-started.md) - Create your first module
- [Event Wrapper Class](event-wrapper.md) - Detailed explanation of event handling
- [Best Practices](best-practices.md) - Develop high-quality modules