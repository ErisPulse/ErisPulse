# Getting Started with Module Development

This guide walks you through creating an ErisPulse module from scratch.

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

## pyproject.toml Configuration

```toml
[project]
name = "ErisPulse-MyModule"
version = "1.0.0"
description = "Module description"
readme = "README.md"
requires-python = ">=3.10"
license = { file = "LICENSE" }
authors = [ { name = "yourname", email = "your@mail.com" } ]
dependencies = []

[project.urls]
"homepage" = "https://github.com/yourname/MyModule"

[project.entry-points."erispulse.module"]
"MyModule" = "MyModule:Main"

## __init__.py

```python
from .Core import Main

## Core.py - Basic Module

```python
from ErisPulse import sdk
from ErisPulse.Core.Bases import BaseModule
from ErisPulse.Core.Event import command

class Main(BaseModule):
    def __init__(self):
        self.sdk = sdk
        self.logger = sdk.logger.get_child("MyModule")
        self.storage = sdk.storage
        self.config = self._load_config()
    
    @staticmethod
    def get_load_strategy():
        """Returns the module load strategy"""
        from ErisPulse.loaders import ModuleLoadStrategy
        return ModuleLoadStrategy(
            lazy_load=True,
            priority=0,
            depends=[]  # Optional: list of other modules to depend on
        )
    
    async def on_load(self, event):
        """Called when the module is loaded"""
        @command("hello", help="Send a greeting")
        async def hello_command(event):
            name = event.get_user_nickname() or "Friend"
            await event.reply(f"Hello, {name}!")
        
        self.logger.info("Module loaded")
    
    async def on_unload(self, event):
        """Called when the module is unloaded"""
        self.logger.info("Module unloaded")
    
    def _load_config(self):
        """Load module configuration"""
        config = self.sdk.config.getConfig("MyModule")
        if not config:
            default_config = {
                "api_url": "https://api.example.com",
                "timeout": 30
            }
            self.sdk.config.setConfig("MyModule", default_config)
            return default_config
        return config

## Test Module

### Local Testing

```bash
# Install module in the project directory
epsdk install ./MyModule

# Run the project
epsdk run main.py --reload
```

### Test Commands

Send a command test:

```
/hello

## Core Concepts

### BaseModule Base Class

All modules must inherit from `BaseModule` and provide the following methods:

| Method | Description | Required |
|--------|-------------|----------|
| `__init__(self)` | Constructor | No |
| `get_load_strategy()` | Return load strategy | No |
| `get_meta()` | Return module description metadata (optional) | No |
| `on_load(self, event)` | Called when module is loaded | Yes |
| `on_unload(self, event)` | Called when module is unloaded | Yes |

### Module Description meta

Declare the module's description metadata via `get_meta()` (what this module does, which category it belongs to, etc.).
Metadata is the **general introduction data** of the module, consumed by the help module, Dashboard module list, module store, and various other interfaces/ecosystem modules.

Consistent with `get_load_strategy()` returning a `ModuleLoadStrategy`, it is **recommended to return a `ModuleMeta` configuration class instance** (for attribute typing and IDE autocomplete), and it is also compatible with returning a dict directly:

```python
class MyModule(BaseModule):
    @staticmethod
    def get_meta() -> ModuleMeta:
        return ModuleMeta(
            name="Weather",               # Display name (defaults to the registered name)
            description="Query city weather",  # Module brief introduction
            version="1.0.0",
            author="ErisDev",
            group="Tool",                 # Functional grouping
            tags=["Weather", "Query"],
        )
```

Compatible writing style (dict):

```python
class MyModule(BaseModule):
    @staticmethod
    def get_meta() -> dict:
        return {
            "name": "Weather",
            "description": "Query city weather",
            "version": "1.0.0",
            "author": "ErisDev",
            "group": "Tool",
            "tags": ["Weather", "Query"],
        }
```

- `module.get_meta("MyModule")` reads the parsed metadata (class declaration > registered info, automatically completes the module's command name).
- `module.get_commands_overview()` aggregates the "module meta + its registered commands (aliases/grouping/help)" to provide a command overview organized by module.
- The module a command belongs to can be obtained via `cmd_info["owner"]` (automatically injected by the context system upon registration).

#### meta fields i18n support

Metadata field values can be plain strings or an i18n dictionary `{"i18n": "key.path", "default": "fallback text"}` (consistent with the `description` configuration convention).
Translation keys are declared and registered via `I18nClass`, and when `module.get_meta()` reads them, they are automatically resolved into the current language text:

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

### SDK Objects

Access core functionality via the `sdk` object:

```python
from ErisPulse import sdk

sdk.storage    # Storage system
sdk.config     # Configuration system
sdk.logger     # Logging system
sdk.adapter    # Adapter system
sdk.router     # Routing system
sdk.lifecycle  # Lifecycle system

## Next Steps

- [Module Core Concepts](core-concepts.md) - Deep dive into module architecture
- [Event Wrapper Class Details](event-wrapper.md) - Learn about Event objects
- [Module Best Practices](best-practices.md) - Develop high-quality modules