# Best Practices for Module Development

> [!TIP]
> **When to read this**: Recommended after writing your first module (engineering best practices). Skip if not needed, it won't affect other features.

This document summarizes engineering conventions for module development: asynchronous operations should not block the event loop, configurations should be declarative, and resources managed by others must be released upon unloading. Following these practices avoids common pitfalls such as memory leaks, lingering background tasks, and failed hot reloads.

## Module Design

### 1. Single Responsibility Principle

Each module should be responsible for only one core feature:

```python
# Good design: each module handles only one function
class WeatherModule(BaseModule):
    """Module for weather queries"""
    pass

class NewsModule(BaseModule):
    """Module for news queries"""
    pass

# Bad design: one module handles multiple unrelated functions
class UtilityModule(BaseModule):
    """Contains weather, news, jokes, and other functions"""
    pass
```

### 2. Module Naming Convention

```toml
[project]
name = "ErisPulse-ModuleName"  # Use the ErisPulse- prefix
```

### 3. Clear Configuration Management

It is recommended to use declarative configuration (`ConfigClass` + `BaseConfig`) to gain type safety, automatic template generation, and WebUI form support:

```python
from dataclasses import dataclass, field
from ErisPulse.Core.Bases import BaseConfig

@dataclass
class MyModuleConfig(BaseConfig):
    api_url: str = field(default="https://api.example.com", metadata={
        "description": {"i18n": "my_module.api_url", "default": "API address"},
    })
    timeout: int = field(default=30, metadata={
        "description": {"i18n": "my_module.timeout", "default": "Timeout (seconds)"},
    })
    cache_ttl: int = field(default=3600, metadata={
        "description": {"i18n": "my_module.cache_ttl", "default": "Cache TTL (seconds)"},
    })

class MyModule(BaseModule):
    ConfigClass = MyModuleConfig

    async def do_something(self):
        cfg = self.cfg  # Type-safe, live reading
        await self._fetch(cfg.api_url, timeout=cfg.timeout)
```

Alternatively, you can continue to use manual configuration storage (see [Module Core Concepts](core-concepts.md#configuration-management)).

### Declarative Translation Keys (v2.7.0+)

Modules can declare translation keys via `I18nClass`, which the framework automatically registers into the i18n system, eliminating the need for manual `i18n.register()` calls.

```python
from ErisPulse.Core.Bases import BaseI18n, I18nKey

class MyModule(BaseModule):
    class I18nClass(BaseI18n):
        # Business translation keys with placeholders
        welcome: I18nKey = I18nKey(
            default="Welcome, {name}!",
            zh_CN="欢迎你，{name}！",
            zh_TW="歡迎你，{name}！",
            en="Welcome, {name}!",
            ja="ようこそ、{name}！",
            ru="Добро пожаловать, {name}!",
        )
        # Configuration field descriptions
        api_url: I18nKey = I18nKey(
            default="API URL",
            zh_CN="API 地址",
            zh_TW="API 位址",
            en="API URL",
            ja="API URL",
            ru="API URL",
        )
```

See [i18n documentation](../../advanced/i18n.md#recommended-approach-declaring-translation-keys-via-i18nclass-v270) for detailed usage.

## Asynchronous Programming

### 1. Use Asynchronous Libraries

```python
# Recommended: Use SDK's built-in HTTP client (async, with automatic logging and metrics)
from ErisPulse.Core import client

class MyModule(BaseModule):
    async def fetch_data(self, url):
        resp = await client.get(url)
        return await resp.json()

# Also available via sdk.client (same effect)
from ErisPulse import sdk

class MyModule(BaseModule):
    async def fetch_data(self, url):
        resp = await sdk.client.get(url)
        return await resp.json()

# Do not use aiohttp directly (not convenient for framework management)
import aiohttp

class MyModule(BaseModule):
    async def fetch_data(self, url):
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                return await response.json()

# Do not use requests (sync, blocks event loop)
import requests

class MyModule(BaseModule):
    def fetch_data(self, url):
        return requests.get(url).json()  # Blocks event loop
```

### 2. Correct Asynchronous Operations

```python
from ErisPulse.Core.Event import Event  # Strongly recommend using Event annotation; see epsdk types for custom method completion

async def handle_command(self, event: Event):
    # Time-consuming operations requiring result: directly await (clear lifecycle)
    result = await self._long_operation()

async def on_load(self, event: dict):
    # Background tasks (polling/timer/fire-and-forget): use self.spawn(),
    # when the module unloads, the framework cancels them after on_unload, avoiding self reference leaks
    self.spawn(self._poll())
```

> [!NOTE]
> Background tasks are recommended to use `self.spawn()` (ErisPulse **2.8.0+**). **Since 2.8.3**, bare `asyncio.create_task`
> will also be automatically registered to the module (Task Factory automatically registers, and cancels them on unload, no longer leaking `self` references);
> `self.spawn()` is still the recommended approach—supports non-main loop thread scheduling back to the main loop, and explicitly specifies `owner=`. 
> **Before 2.8.3**, bare tasks are not registered, and they hold `self` references, causing module instances to be unrecoverable
> (hot reload leaks), so `self.spawn()` must be used. See [Lifecycle Management](../../advanced/lifecycle.md#background-task-ownership-and-automatic-cancellation).

### 3. Resource Management

```python
async def on_load(self, event):
    # SDK client manages connection pools automatically, no need to manually create session
    pass
    
async def on_unload(self, event):
    # If you need a custom client, remember to clean up resources
    pass
```

## Event Handling

### 1. Use Event Wrapper Class

```python
from ErisPulse.Core.Event import Event
# Use Event wrapper class's convenient methods
@command("info")
async def info_command(event: Event):
    user_id = event.get_user_id()
    nickname = event.get_user_nickname()
    await event.reply(f"你好，{nickname}！")

# Rather than directly accessing the dictionary
@command("info")
async def info_command(event: Event):
    user_id = event["user_id"]  # Less clear, prone to errors
```

### 2. Reasonable Use of Lazy Loading

```python
# Low-frequency command module: declare activate_on trigger, automatically activate on first matching command arrival (maintain lazy loading)
class CommandModule(BaseModule):
    @staticmethod
    def get_load_strategy():
        return ModuleLoadStrategy(lazy_load=True, activate_on=[
            {"command": {"name": "dice", "help": "Roll a dice", "aliases": ["d"]}},
        ])

# Low-frequency listener module: declare event trigger, activate when event arrives
class ListenerModule(BaseModule):
    @staticmethod
    def get_load_strategy():
        return ModuleLoadStrategy(lazy_load=True, activate_on=[
            {"notice": "group_member_increase"},
        ])

# High-frequency triggers (process every message) or modules that must be ready at startup: load immediately
class HotListenerModule(BaseModule):
    @staticmethod
    def get_load_strategy():
        return ModuleLoadStrategy(lazy_load=False)

# Utility modules are suitable for lazy loading
class UtilityModule(BaseModule):
    @staticmethod
    def get_load_strategy():
        return ModuleLoadStrategy(lazy_load=True)
```

> The full syntax for `activate_on` (event three forms / command shorthand and dict declaration / help fallback chain) is detailed in
> [Lazy-Loading Module System](../../advanced/lazy-loading.md#event-driven-lazy-activation-activate_on).

### 3. Event Handler Registration

```python
from ErisPulse.Core.Event import Event
async def on_load(self, event):
    # Register event handlers in on_load
    @command("hello")
    async def hello_handler(event: Event):
        await event.reply("你好！")
    
    @message.on_group_message()
    async def group_handler(event: Event):
        self.logger.info("Received group message")
    
    # No need to manually unregister; the framework handles it automatically
```

## Utility Modules: Handle "Unload Notifications" When Managing Other Modules' Resources

**When needed**: Your module manages resources for other modules (timers, subscribers, connections, cache entries...). If these references are not discarded after the other module unloads, the other module instance cannot be recycled—this is the most common source of memory leaks in utility modules.

```python
from ErisPulse.Core.Bases import BaseModule
from ErisPulse.runtime import off_cleanup, on_cleanup

class MyToolModule(BaseModule):
    def __init__(self):
        self._entries = {}  # {module name: managed resource}

    def register(self, entry):
        owner = on_cleanup(self._drop)   # ① Register cleanup chain when registering, automatically identifies caller
        self._entries.setdefault(owner, []).append(entry)

    def _drop(self, owner: str):
        self._entries.pop(owner, None)   # ② When the other module unloads, the framework automatically calls: discard its resources

    async def on_unload(self, event):
        off_cleanup(self._drop)          # ③ Unregister hook before unloading
```

That's all, the framework guarantees:

- When the other module is **unloaded / disabled** (or adapter closed), `_drop("other module name")` will definitely be called
- **Automatic caller identification**: Whether the caller directly calls `sdk.MyToolModule.register(...)` in `on_load`, or calls via `sdk.module.call("MyToolModule", "register", ...)`), the caller is correctly identified
- No need to worry about timing—the hook is triggered within the framework's cleanup chain, earlier than leak detection, and will not cause false alarms

Consequences of not integrating: When the other module `purge` is completely unloaded, the instance cannot be recovered (leak detection reports "unrecoverable"); if the other module does not also unregister from you in `on_unload`, the leak is permanent.

**Regular modules (not managing other modules' resources) do not need to care about this**—the framework automatically cleans up resources (commands / handlers / routes / background tasks...) during unloading.

> For details on trigger timing, caller identification rules, timeouts, and fault tolerance, see
> [Ownership System · Utility Module Guide](../../advanced/ownership.md#utility-module-guide-managing-other-modules-handles).

## Error Handling

### 1. Categorized Exception Handling

```python
from ErisPulse.Core.Event import Event
from ErisPulse.Core.Bases.errors import ClientError

async def handle_event(self, event: Event):
    try:
        result = await self._process(event)
    except ValueError as e:
        # Expected business error
        self.logger.warning(f"Business warning: {e}")
        await event.reply(f"Parameter error: {e}")
    except ClientError as e:
        # Network error (sdk.client's underlying aiohttp exceptions are automatically converted)
        self.logger.error(f"Network error {e.method} {e.url}: {e}")
        await event.reply("Network request failed, please try again later")
    except Exception as e:
        # Unexpected error
        self.logger.error(f"Unknown error: {e}", exc_info=True)
        await event.reply("Processing failed, please contact the administrator")
        raise
```

### 2. Timeout Handling

```python
# Recommended: Use SDK's built-in client (with built-in timeout and retry)
from ErisPulse.Core import client
from ErisPulse.Core.Bases.errors import ClientTimeoutError

async def fetch_with_timeout(self, url, timeout=30):
    try:
        resp = await client.get(url, timeout=timeout)
        return await resp.json()
    except ClientTimeoutError:
        self.logger.warning(f"Request timeout: {url}")
        raise
```

## Storage System

### 1. Use Transactions

```python
# Use transactions to ensure data consistency
async def update_user(self, user_id, data):
    with self.sdk.storage.transaction():
        self.sdk.storage.set(f"user:{user_id}:profile", data["profile"])
        self.sdk.storage.set(f"user:{user_id}:settings", data["settings"])

# ❌ Not using transactions may cause data inconsistency
async def update_user(self, user_id, data):
    self.sdk.storage.set(f"user:{user_id}:profile", data["profile"])
    # If an error occurs here, the previous setting cannot be rolled back
    self.sdk.storage.set(f"user:{user_id}:settings", data["settings"])
```

### 2. Batch Operations

```python
# Use batch operations to improve performance
def cache_multiple_items(self, items):
    self.sdk.storage.set_multi({
        f"item:{k}": v for k, v in items.items()
    })

# ❌ Multiple calls are inefficient
def cache_multiple_items(self, items):
    for k, v in items.items():
        self.sdk.storage.set(f"item:{k}", v)
```

## Logging

### 1. Use Log Levels Appropriately

```python
# DEBUG: Detailed debugging information (only during development)
self.logger.debug(f"Input parameters: {params}")

# INFO: Normal runtime information
self.logger.info("Module loaded")
self.logger.info(f"Processing request: {request_id}")

# WARNING: Warning information, does not affect main functionality
self.logger.warning(f"Configuration item {key} not set, using default value")
self.logger.warning("API response is slow, may need optimization")

# ERROR: Error information
self.logger.error(f"API request failed: {e}")
self.logger.error(f"Failed to process event: {e}", exc_info=True)

# CRITICAL: Fatal error, requires immediate attention
self.logger.critical("Database connection failed, bot cannot run normally")
```

### 2. Structured Logging

```python
# Use structured logging for easier parsing
self.logger.info(f"Processing request: request_id={request_id}, user_id={user_id}, duration={duration}ms")

# ❌ Use unstructured logging
self.logger.info(f"Processing request, from user {user_id}, took {duration} milliseconds")
```

## Performance Optimization

### 1. Use Caching

```python
class MyModule(BaseModule):
    def __init__(self):
        self._cache = {}
        self._cache_lock = asyncio.Lock()
    
    async def get_data(self, key):
        async with self._cache_lock:
            if key in self._cache:
                return self._cache[key]
            
            # Fetch from database
            data = await self._fetch_from_db(key)
            
            # Cache data
            self._cache[key] = data
            return data
```

### 2. Avoid Blocking Operations

```python
from ErisPulse.Core.Event import Event
# Use asynchronous operations
async def process_message(self, event: Event):
    # Asynchronous processing
    await self._async_process(event)

# ❌ Blocking operation
async def process_message(self, event: Event):
    # Synchronous operation, blocks event loop
    result = self._sync_process(event)
```

## Security

### 1. Protect Sensitive Data

```python
# Store sensitive data in configuration (declarative ConfigClass, secret fields do not enter logs/exports)
from dataclasses import dataclass, field
from ErisPulse.Core.Bases import BaseModule, BaseConfig

@dataclass
class MyModuleConfig(BaseConfig):
    api_key: str = field(
        default="",
        metadata={"description": "API Key", "secret": True},
    )

class MyModule(BaseModule):
    ConfigClass = MyModuleConfig

    def check_api_key(self):
        if not self.cfg.api_key or self.cfg.api_key == "YOUR_API_KEY_HERE":
            raise ValueError("Please configure a valid API key in config.toml")

# ❌ Hardcoded sensitive data
class MyModule(BaseModule):
    API_KEY = "sk-1234567890"  # Do not do this!
```

### 2. Input Validation

```python
from ErisPulse.Core.Event import Event
# Validate user input
async def process_command(self, event: Event):
    user_input = event.get_text()
    
    # Validate input length
    if len(user_input) > 1000:
        await event.reply("Input too long, please re-enter")
        return
    
    # Validate input format
    if not re.match(r'^[a-zA-Z0-9]+$', user_input):
        await event.reply("Invalid input format")
        return
```

## Testing

### 1. Unit Tests

```python
import pytest
from ErisPulse.Core.Bases import BaseModule

class TestMyModule:
    def test_config_defaults(self):
        """Test configuration default values"""
        config = MyModule.ConfigClass()
        assert config.timeout == 30
```

### 2. Integration Tests

```python
@pytest.mark.asyncio
async def test_command_handling():
    """Test command handling"""
    module = MyModule()
    await module.on_load({})
    
    # Simulate command event
    event = create_test_command_event("hello")
    await module.handle_command(event)
```

## HTTP Route Lifecycle

HTTP/WebSocket routes registered by a module via `router` are managed by the framework according to the **ownership principle**:

- The namespace at registration serves as the ownership identifier; **during reload/unload, the framework automatically cleans up all routes and connection resources under this ownership**, no need for manual unregistration
- Therefore, **`on_load` must unconditionally re-register routes**. Do not use instance-level boolean flags for "register only once" optimization: configuration hot reload triggers stop/start and **reuses the same instance**, flag remnants will cause routes to be cleaned up and **permanently lost**, resulting in 404 interface errors until the process is restarted

```python
class MyModule(BaseModule):
    async def on_load(self):
        # Re-register unconditionally every time
        router.register_http_route("MyModule", "/api/panel", self._panel, methods=["GET"])
```

When you need to manually unload routes earlier (e.g., dynamically disable an entry), you can unregister them:

```python
from ErisPulse.Core import router

router.unregister_http_route("MyModule", "/api/panel")
```

- Frontend/callers may temporarily receive route 404 errors during the hot reload window, which is a transient phenomenon; for browser-facing interactive pages, consider limited automatic retries for 404 errors

## Deployment

### 1. Version Management

```toml
[project]
name = "ErisPulse-MyModule"
version = "1.0.0"
```

Follow semantic versioning:
- MAJOR.MINOR.PATCH
- Major version: Incompatible API changes
- Minor version: Backward-compatible feature additions
- Patch version: Backward-compatible bug fixes

### 2. README Header

The README generated by `epsdk create` already includes the ErisPulse header (logo + badge line). Two recommended modes:

**Mode A — ErisPulse Logo Only (Default):**

```markdown
<div align="center">

<img src="https://raw.githubusercontent.com/ErisPulse/ErisPulse/main/.github/assets/ErisPulseLogo.png" width="180" alt="MyModule" />

# MyModule

**One-sentence description**

<p>
  <a href="https://pypi.org/project/ErisPulse-MyModule/"><img src="https://img.shields.io/pypi/v/ErisPulse-MyModule?style=for-the-badge&logo=pypi&logoColor=white" alt="PyPI"></a>
  <a href="https://pypi.org/project/ErisPulse-MyModule/"><img src="https://img.shields.io/badge/Python-3.10+-FFD43B?style=for-the-badge&logo=python&logoColor=blue" alt="Python"></a>
  <a href="./LICENSE"><img src="https://img.shields.io/badge/License-MIT-blue?style=for-the-badge" alt="License"></a>
  <a href="https://github.com/ErisPulse/ErisPulse"><img src="https://img.shields.io/badge/Powered_by-ErisPulse-FF6B9D?style=for-the-badge&logo=bookstack&logoColor=white" alt="ErisPulse"></a>
</p>

</div>
```

**Mode B — Module Icon × ErisPulse Logo (with custom icon):**

```markdown
<div align="center">

<img src=".github/assets/MyModuleIcon.svg" width="120" alt="MyModule" />
<span style="font-size:44px;color:#c8c8c8;margin:0 18px;vertical-align:middle;">×</span>
<img src="https://raw.githubusercontent.com/ErisPulse/ErisPulse/main/.github/assets/ErisPulseLogo.png" height="120" alt="ErisPulse" />

# MyModule
(With the same badge line as above)
</div>
```

You can add GitHub Stars, Downloads, and other badges as needed. The logo can also be downloaded locally (`.github/assets/ErisPulseLogo.png`) and referenced with a relative path.

## Related Documentation

### Back to Learning Path

- [Getting Started with Module Development](getting-started.md) - Create your first module
- [Module Core Concepts](core-concepts.md) - Understand module architecture

### Deep Dive by Scenario

- [Event Wrapper Class](event-wrapper.md) - Detailed event handling
- [Publishing and Module Store Guide](../publishing.md) - Publish your module to PyPI and the module store