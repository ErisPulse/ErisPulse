# Module Development Best Practices

> [!TIP]
> **When to read this**: Recommended reading after you complete your first module (engineering best practices). Feel free to skip it if you don't need it — doing so won't affect your use of any other features.

This page summarizes the engineering conventions for module development: async operations must not block the event loop, configuration should be declarative, and resources hosted on behalf of other modules must be released on unload — following these conventions helps you avoid the most common module-development pitfalls, such as memory leaks, leftover background tasks, and broken hot reloading.

## Module Design

### 1. Single Responsibility Principle

Each module should be responsible for only one core feature:

```python
# Good design: each module handles a single feature
class WeatherModule(BaseModule):
    """Weather query module"""
    pass

class NewsModule(BaseModule):
    """News query module"""
    pass

# Bad design: one module handling multiple unrelated features
class UtilityModule(BaseModule):
    """Contains weather, news, jokes, and other features"""
    pass
```

### 2. Module Naming Conventions

```toml
[project]
name = "ErisPulse-ModuleName"  # Use the ErisPulse- prefix
```

### 3. Clean Configuration Management

Declarative configuration (`ConfigClass` + `BaseConfig`) is recommended, giving you type safety, automatic template generation, WebUI form support, and more:

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
        cfg = self.cfg  # Type-safe, read in real time
        await self._fetch(cfg.api_url, timeout=cfg.timeout)
```

You can also continue to read and write the configuration store manually (see [Module Core Concepts](core-concepts.md#configuration-management)).

### Declarative Translation Keys (v2.7.0+)

Modules can declare translation keys centrally via `I18nClass`; the framework registers them with the i18n system automatically, with no need to call `i18n.register()` manually.

```python
from ErisPulse.Core.Bases import BaseI18n, I18nKey

class MyModule(BaseModule):
    class I18nClass(BaseI18n):
        # Business translation key with placeholders
        welcome: I18nKey = I18nKey(
            default="Welcome, {name}!",
            zh_CN="Welcome, {name}!",
            zh_TW="Welcome, {name}!",
            en="Welcome, {name}!",
            ja="Welcome, {name}!",
            ru="Welcome, {name}!",
        )
        # Translation for config field descriptions
        api_url: I18nKey = I18nKey(
            default="API URL",
            zh_CN="API URL",
            zh_TW="API URL",
            en="API URL",
            ja="API URL",
            ru="API URL",
        )
```

See the [i18n documentation](../../advanced/i18n.md#recommended-approach-declare-translation-keys-via-i18nclass-v270) for detailed usage.

## Async Programming

### 1. Use Async Libraries

```python
# Recommended: use the SDK's built-in HTTP client (async, with automatic logging and statistics)
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

# Do not import aiohttp directly (harder for the framework to manage uniformly)
import aiohttp

class MyModule(BaseModule):
    async def fetch_data(self, url):
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                return await response.json()

# Do not use requests (synchronous; it blocks the event loop)
import requests

class MyModule(BaseModule):
    def fetch_data(self, url):
        return requests.get(url).json()  # Blocks the event loop
```

### 2. Correct Async Operations

```python
from ErisPulse.Core.Event import Event  # The event: Event annotation gives you IDE completion

async def handle_command(self, event: Event):
    # Long-running operations whose results you need: await directly (clear lifecycle)
    result = await self._long_operation()

async def on_load(self, event: dict):
    # Background tasks (polling / timers / fire-and-forget): use self.spawn().
    # On module unload the framework cancels them as a fallback after on_unload,
    # avoiding leaks caused by holding a reference to self
    self.spawn(self._poll())
```

> [!NOTE]
> `self.spawn()` is recommended for background tasks (ErisPulse **2.8.0+**). From **2.8.3 on**, bare
> `asyncio.create_task` calls are also automatically and implicitly attributed to the module (the Task Factory
> registers them automatically and cancels them on unload as a fallback, so the `self` reference no longer leaks);
> `self.spawn()` remains the recommended style — it supports scheduling back to the main loop from non-main-loop
> threads and explicit `owner=` assignment. In versions **before 2.8.3**, bare tasks were not attributed and
> would hold a `self` reference, preventing the module instance from being reclaimed (a hot-reload leak);
> you must use `self.spawn()`. See [Lifecycle Management](../../advanced/lifecycle.md#background-task-ownership-and-automatic-cancellation) for details.

### 3. Resource Management

```python
async def on_load(self, event):
    # The SDK client manages the connection pool automatically; no need to create sessions manually
    pass
    
async def on_unload(self, event):
    # If you use a custom client, remember to clean up its resources
    pass
```

## Event Handling

### 1. Use the Event Wrapper Class

```python
# Use the convenience methods of the Event wrapper class
@command("info")
async def info_command(event: Event):
    user_id = event.get_user_id()
    nickname = event.get_user_nickname()
    await event.reply(f"Hello, {nickname}!")

# Rather than accessing the dict directly
@command("info")
async def info_command(event: Event):
    user_id = event["user_id"]  # Not clear enough and error-prone
```

### 2. Use Lazy Loading Appropriately

```python
# Low-frequency command module: declare activate_on triggers; the module activates automatically
# when the first matching command arrives (stays lazily loaded)
class CommandModule(BaseModule):
    @staticmethod
    def get_load_strategy():
        return ModuleLoadStrategy(lazy_load=True, activate_on=[
            {"command": {"name": "dice", "help": "Roll a die", "aliases": ["d"]}},
        ])

# Low-frequency listener module: declare event triggers; the module activates automatically when events arrive
class ListenerModule(BaseModule):
    @staticmethod
    def get_load_strategy():
        return ModuleLoadStrategy(lazy_load=True, activate_on=[
            {"notice": "group_member_increase"},
        ])

# High-frequency triggers (every message must be handled) or modules that must be ready at startup: load immediately
class HotListenerModule(BaseModule):
    @staticmethod
    def get_load_strategy():
        return ModuleLoadStrategy(lazy_load=False)

# Utility modules are a good fit for lazy loading
class UtilityModule(BaseModule):
    @staticmethod
    def get_load_strategy():
        return ModuleLoadStrategy(lazy_load=True)
```

> For the complete syntax of `activate_on` (the three event forms / command shorthand and dict declaration / help fallback chain), see
> [Lazy-Loading Module System](../../advanced/lazy-loading.md#event-driven-lazy-activation-activate_on).

### 3. Event Handler Registration

```python
async def on_load(self, event):
    # Register event handlers inside on_load
    @command("hello")
    async def hello_handler(event: Event):
        await event.reply("Hello!")
    
    @message.on_group_message()
    async def group_handler(event: Event):
        self.logger.info("Received group message")
    
    # No need to unregister manually; the framework handles it automatically
```

## Tool Modules: Catch "Unload Notifications" When Hosting Things for Others

**When you need this**: your module keeps things on behalf of other modules (timed callbacks, subscribers, connections, cache entries, ...). If those references are never dropped after the other module unloads, its instance can never be reclaimed — this is the most common source of memory leaks in tool modules.

```python
from ErisPulse.Core.Bases import BaseModule
from ErisPulse.runtime import off_cleanup, on_cleanup

class MyToolModule(BaseModule):
    def __init__(self):
        self._entries = {}  # {module name: hosted items}

    def register(self, entry):
        owner = on_cleanup(self._drop)   # ① Hook into the cleanup chain on registration; the caller is identified automatically
        self._entries.setdefault(owner, []).append(entry)

    def _drop(self, owner: str):
        self._entries.pop(owner, None)   # ② Called automatically by the framework when the other side unloads: drop its items

    async def on_unload(self, event):
        off_cleanup(self._drop)          # ③ Unregister the hook before your own unload
```

That's all there is to it. The framework guarantees:

- When the other module is **unloaded / disabled** (or its adapter shuts down), `_drop("OtherModuleName")` is guaranteed to be called
- **Caller identification is fully automatic**: whether the other side calls `sdk.MyToolModule.register(...)` directly in `on_load`, or through `sdk.module.call("MyToolModule", "register", ...)`, the caller is identified correctly
- No need to worry about timing — the hook fires within the framework's cleanup chain, before leak diagnostics, so it won't produce false positives

Consequences of not adopting this: when the other side is completely removed with `purge`, its instance cannot be reclaimed (leak diagnostics report it as "unreclaimable"); if the other side also never unregisters from you in its own `on_unload`, the leak becomes permanent.

**Ordinary modules (those that don't host things for others) don't need to care about this** — cleanup of framework resources (commands / handlers / routes / background tasks, ...) on unload is fully automatic.

> For details such as trigger timing, caller identification rules, timeouts, and fault tolerance, see
> [Ownership System · Tool Module Guide](../../advanced/ownership.md#tool-module-guide-hosting-handles-of-other-modules).

## Error Handling

### 1. Categorized Exception Handling

```python
from ErisPulse.Core.Bases.errors import ClientError

async def handle_event(self, event: Event):
    try:
        result = await self._process(event)
    except ValueError as e:
        # Expected business error
        self.logger.warning(f"Business warning: {e}")
        await event.reply(f"Invalid argument: {e}")
    except ClientError as e:
        # Network error (underlying aiohttp exceptions from sdk.client are converted automatically)
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
# Recommended: use the SDK's built-in client (timeout and retry included)
from ErisPulse.Core import client
from ErisPulse.Core.Bases.errors import ClientTimeoutError

async def fetch_with_timeout(self, url, timeout=30):
    try:
        resp = await client.get(url, timeout=timeout)
        return await resp.json()
    except ClientTimeoutError:
        self.logger.warning(f"Request timed out: {url}")
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

# ❌ Not using transactions may lead to data inconsistency
async def update_user(self, user_id, data):
    self.sdk.storage.set(f"user:{user_id}:profile", data["profile"])
    # If an error occurs here, the setting above cannot be rolled back
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
# DEBUG: detailed debugging information (development only)
self.logger.debug(f"Input parameters: {params}")

# INFO: normal operation information
self.logger.info("Module loaded")
self.logger.info(f"Processing request: {request_id}")

# WARNING: warnings that don't affect core functionality
self.logger.warning(f"Config item {key} not set, using default value")
self.logger.warning("API response is slow, may need optimization")

# ERROR: error information
self.logger.error(f"API request failed: {e}")
self.logger.error(f"Failed to process event: {e}", exc_info=True)

# CRITICAL: fatal error, requires immediate attention
self.logger.critical("Database connection failed, the bot cannot run properly")
```

### 2. Structured Logging

```python
# Use structured logging for easier parsing
self.logger.info(f"Processing request: request_id={request_id}, user_id={user_id}, duration={duration}ms")

# ❌ Unstructured logging
self.logger.info(f"Processed a request from user {user_id}, took {duration} ms")
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
            
            # Fetch from the database
            data = await self._fetch_from_db(key)
            
            # Cache the data
            self._cache[key] = data
            return data
```

### 2. Avoid Blocking Operations

```python
# Use async operations
async def process_message(self, event: Event):
    # Async processing
    await self._async_process(event)

# ❌ Blocking operation
async def process_message(self, event: Event):
    # Synchronous operation; blocks the event loop
    result = self._sync_process(event)
```

## Security

### 1. Sensitive Data Protection

```python
# Sensitive data lives in configuration (declarative ConfigClass; secret fields are excluded from logs/exports)
from dataclasses import dataclass, field
from ErisPulse.Core.Bases import BaseModule, BaseConfig

@dataclass
class MyModuleConfig(BaseConfig):
    api_key: str = field(
        default="",
        metadata={"description": "API key", "secret": True},
    )

class MyModule(BaseModule):
    ConfigClass = MyModuleConfig

    def check_api_key(self):
        if not self.cfg.api_key or self.cfg.api_key == "YOUR_API_KEY_HERE":
            raise ValueError("Please configure a valid API key in config.toml")

# ❌ Hardcoded sensitive data
class MyModule(BaseModule):
    API_KEY = "sk-1234567890"  # Never do this!
```

### 2. Input Validation

```python
# Validate user input
async def process_command(self, event: Event):
    user_input = event.get_text()
    
    # Validate input length
    if len(user_input) > 1000:
        await event.reply("Input is too long, please try again")
        return
    
    # Validate input format
    if not re.match(r'^[a-zA-Z0-9]+$', user_input):
        await event.reply("Invalid input format")
        return
```

## Testing

### 1. Unit Testing

```python
import pytest
from ErisPulse.Core.Bases import BaseModule

class TestMyModule:
    def test_config_defaults(self):
        """Test configuration default values"""
        config = MyModule.ConfigClass()
        assert config.timeout == 30
```

### 2. Integration Testing

```python
@pytest.mark.asyncio
async def test_command_handling():
    """Test command handling"""
    module = MyModule()
    await module.on_load({})
    
    # Simulate a command event
    event = create_test_command_event("hello")
    await module.handle_command(event)
```

## HTTP Route Lifecycle

The lifecycle of HTTP/WebSocket routes registered by a module through `router` is managed automatically by the framework according to the **ownership principle**:

- The namespace used at registration is the ownership identifier; **on reload / unload the framework automatically cleans up all routes and connection resources under that ownership**, with no manual unregistration required
- Therefore **routes must be re-registered unconditionally in `on_load`**. Do not use an instance-level boolean flag as a "register only once" optimization: configuration hot reloads trigger stop/start and **reuse the same instance**, so a leftover flag causes routes to be **permanently lost** after cleanup — manifesting as 404s on the endpoint that only recover after restarting the process

```python
class MyModule(BaseModule):
    async def on_load(self):
        # Re-register unconditionally on every load
        router.register_http_route("MyModule", "/api/panel", self._panel, methods=["GET"])
```

If you need to unload routes manually ahead of time (e.g., taking an endpoint offline dynamically), you can unregister proactively:

```python
from ErisPulse.Core import router

router.unregister_http_route("MyModule", "/api/panel")
```

- Frontends/callers may receive route 404s during the hot-reload window; this is transient. For browser-facing interactive pages, a limited number of automatic retries on 404 are recommended

## Deployment

### 1. Version Management

```toml
[project]
name = "ErisPulse-MyModule"
version = "1.0.0"
```

Follow semantic versioning:
- MAJOR.MINOR.PATCH
- Major version: incompatible API changes
- Minor version: backward-compatible feature additions
- Patch version: backward-compatible bug fixes

### 2. README Header

The README generated by `epsdk create` already includes the ErisPulse header identity (logo + badge row). Two recommended patterns:

**Pattern A — ErisPulse logo only (default):**

```markdown
<div align="center">

<img src="https://raw.githubusercontent.com/ErisPulse/ErisPulse/main/.github/assets/ErisPulseLogo.png" width="180" alt="MyModule" />

# MyModule

**One-line description**

<p>
  <a href="https://pypi.org/project/ErisPulse-MyModule/"><img src="https://img.shields.io/pypi/v/ErisPulse-MyModule?style=for-the-badge&logo=pypi&logoColor=white" alt="PyPI"></a>
  <a href="https://pypi.org/project/ErisPulse-MyModule/"><img src="https://img.shields.io/badge/Python-3.10+-FFD43B?style=for-the-badge&logo=python&logoColor=blue" alt="Python"></a>
  <a href="./LICENSE"><img src="https://img.shields.io/badge/License-MIT-blue?style=for-the-badge" alt="License"></a>
  <a href="https://github.com/ErisPulse/ErisPulse"><img src="https://img.shields.io/badge/Powered_by-ErisPulse-FF6B9D?style=for-the-badge&logo=bookstack&logoColor=white" alt="ErisPulse"></a>
</p>

</div>
```

**Pattern B — Module icon × ErisPulse logo (when a custom icon is available):**

```markdown
<div align="center">

<img src=".github/assets/MyModuleIcon.svg" width="120" alt="MyModule" />
<span style="font-size:44px;color:#c8c8c8;margin:0 18px;vertical-align:middle;">×</span>
<img src="https://raw.githubusercontent.com/ErisPulse/ErisPulse/main/.github/assets/ErisPulseLogo.png" height="120" alt="ErisPulse" />

# MyModule
(Badge row same as above)
</div>
```

You can add badges such as GitHub Stars or Downloads as needed. The logo can also be downloaded into the project locally (`.github/assets/ErisPulseLogo.png`) and referenced via a relative path.

## Related Documentation

### Back to the Learning Path

- [Module Development Getting Started](getting-started.md) - Create your first module
- [Module Core Concepts](core-concepts.md) - Understand the module architecture

### Deep Dives by Scenario

- [Event Wrapper Class](event-wrapper.md) - Event handling in depth
- [Publishing and Module Store Guide](../publishing.md) - Publish your module to PyPI and the Module Store once it's written