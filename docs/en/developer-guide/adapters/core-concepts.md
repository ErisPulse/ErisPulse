# Core Concepts of Adapters

> [!TIP]
> **When to read this**: Mandatory for adapter development path (complete explanation of core mechanisms such as BaseAdapter, SendDSL, and lifecycle). For a quick start, read [Getting Started with Adapter Development](getting-started.md) first, and return here only if you have questions about "why" certain aspects are implemented this way.

This document explains the runtime mechanism of adapters: how `AdapterManager` registers and distributes events, what `BaseAdapter` does during initialization, how to declare configurations and multiple accounts—when you encounter questions like "why should I write this way," refer to this document.

## Adapter Architecture

### Component Relationships

```
Forward Conversion (Receiving Direction)                           Reverse Conversion (Sending Direction)
─────────────────                           ─────────────────
                                             
┌──────────────────┐                        ┌──────────────────┐
│ Platform Native Event     │                        │ Module Constructs Message     │
└────────┬─────────┘                        └────────┬─────────┘
         │                                           │
         ↓                                           ↓
┌──────────────────┐   ┌──────────────────┐   ┌──────────────────┐
│                  │   │  Adapter (MyAdapter) │   │                  │
│  Converter       │   │ ┌──────────────┐ │   │ Send.Raw_ob12()  │
│  (Event Converter)    │──→│ │              │ │   │ (Reverse Conversion Entry)   │
│                  │   │ │              │ │   │                  │
└──────────────────┘   │ └──────────────┘ │   └────────┬─────────┘
                       └──────────────────┘            │
                                │                      ↓
                                ↓              ┌──────────────────┐
                       ┌──────────────────┐    │ Platform API Call    │
                       │ OneBot12 Standard Event │    └────────┬─────────┘
                       └────────┬─────────┘             │
                                │                      ↓
                                ↓              ┌──────────────────┐
                       ┌──────────────────┐    │ Standard Response Format     │
                       │ Event System         │    └──────────────────┘
                       └────────┬─────────┘
                                │
                                ↓
                       ┌──────────────────┐
                       │ Module (Process Event)  │
                       └──────────────────┘
```

**Core Symmetry**:
- **Forward Conversion** (Converter): Platform native event → OneBot12 standard event, original data preserved in `{platform}_raw`
- **Reverse Conversion** (Raw_ob12): OneBot12 message segment → Platform API call, returns standard response format

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
3. Parallel startup of each adapter
4. If startup fails, automatically retry (exponential backoff strategy)
5. After successful startup, submit `adapter.status.change` event (started)

**Retry Mechanism**:

- First 4 retries: 60 seconds, 10 minutes, 30 minutes, 60 minutes
- Fifth and subsequent: Fixed interval of 3 hours

#### Shutdown Adapter

```python
# Shutdown all adapters
await sdk.adapter.shutdown()
```

**Shutdown Process**:

1. Submit `adapter.stop` lifecycle event
2. Call all adapters' `shutdown()` method
3. Close router server
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

# Listen to standard message events across all platforms
@sdk.adapter.on("message")
async def handle_message(data):
    print(f"Received OneBot12 message: {data}")

# Listen to standard message events for a specific platform
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
# Listen to native events for a specific platform
@sdk.adapter.on("raw_event_type", raw=True, platform="myplatform")
async def handle_raw_event(data):
    print(f"Received native event: {data}")

# Listen to native events for all platforms (wildcard)
@sdk.adapter.on("*", raw=True)
async def handle_all_raw_events(data):
    print(f"Received native event: {data}")
```

#### Event Distribution Mechanism

When calling `adapter.emit(event_data)`:

1. **Middleware Handling**: Execute all OneBot12 middlewares first
2. **Standard Event Distribution**: Distribute to matching OneBot12 event handlers
3. **Native Event Distribution**: If original data exists, distribute to native event handlers

**Matching Rules**:

- Exact match: `@sdk.adapter.on("message")` only matches `message` events
- Wildcard: `@sdk.adapter.on("*")` matches all events
- Platform filtering: `platform="myplatform"` only distributes events from the specified platform

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
        return None  # Returning None means the middleware chain ignores this return value, retaining original data for further propagation
    return data  # Must return data to continue propagation
```

#### Middleware Return Contract

| Return Value | Behavior |
|--------|------|
| `dict` | Rewrite event payload (subsequent handlers receive the modified event) |
| `None` | Allow passage, payload unchanged (outputs WARNING prompt—suggest explicit `return data`) |
| `False` | **Reject**: Event is discarded, no handlers are invoked, no outbound side effects |

Rejection is suitable for scenarios like firewalls, rate limiting, and blacklists that discard events at the event level (previously only possible using high-priority event handlers). When rejection occurs, the framework outputs a TRACE log and triggers the `adapter.event.blocked` lifecycle hook (carrying the `middleware` middleware name, complete `event`, `platform` / `event_type` / `detail_type`), facilitating troubleshooting of "why an event was not responded to":

```python
@sdk.adapter.middleware
async def rate_limit_middleware(data):
    """Rate limiting middleware"""
    if _is_rate_limited(data):
        return False  # Reject: Event is discarded
    data["rate_marked"] = True
    return data

@sdk.lifecycle.on("adapter.event.blocked")
async def on_event_blocked(data):
    print(f"Event rejected by {data['middleware']}: {data['event_type']}")
```

#### Middleware Execution Order

Middlewares execute in the order they are registered, with later registered middlewares executing first.

> **Note**: If a middleware returns `None` (e.g., forgetting to `return data`), the framework will ignore this return value and retain the original data for further propagation, while outputting a warning-level log. This ensures that a single middleware mistake does not cause the entire event chain to be interrupted.

```python
# Registration order
sdk.adapter.middleware(middleware1)  # Executes last
sdk.adapter.middleware(middleware2)  # Executes in the middle
sdk.adapter.middleware(middleware3)  # Executes first

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
    
    # No need to override __init__, the framework automatically handles:
    # - self.sdk, self.logger
    # - self.cfg (type-safe configuration instance, read in real-time)
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

The framework provides declarative configuration management, defining configuration structures via dataclass, with the framework automatically handling loading, validation, and template generation.

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
        cfg = self.cfg  # Type-safe, real-time reading
        if not cfg.token:
            raise ValueError("Token not configured")
        await self._connect(cfg.token, proxy=cfg.proxy)
```

#### Multi-Account Configuration

The `BotAccountConfig` base class provides `enabled` and `name` fields. Most adapters can automatically obtain `bot_id` from the platform protocol or login response, injecting it into the account configuration during event conversion.:

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

# If bot_id cannot be obtained during login, allow the user to fill it in the configuration
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
    "required": bool,         # Whether required (validation + WebUI required mark)
    "secret": bool,           # Whether sensitive (WebUI displays as ***, masked in logs)
    "example": bool,          # Not persisted flag: not written to config.toml (default value/template excluded),
                              # only rendered into config.full.example; schema with "example": true marked,
                              # CLI configuration wizard defaults skip; user manually sets then persists normally
    "min": number, "max": number,  # Numerical range validation
    "ui": {                   # WebUI control configuration (old name "webui" still compatible)
        "widget": str,        # Control type: "text" | "switch" | "select" | "number" | "password"
        "group": str,         # Group: "basic" | "advanced" | "connection" etc.
        "order": int,         # Sorting weight (smaller is earlier)
        "options": list,      # Select control options [{label, value}], label supports i18n
        "placeholder": str | dict,  # Input box placeholder (supports i18n)
    },
    "extra": dict,            # Additional extended field (passed through to schema)
}
```

All user-visible text fields support i18n, uniformly using the `{"i18n": "key", "default": "text"}` format,
pure strings are passed through as-is (backward compatibility). Supported i18n fields:

| Field | Location | Description |
|------|------|------|
| `description` | field metadata | Field description |
| `options[].label` | `ui.options` | Select control option label |
| `placeholder` | `ui.placeholder` | Input box placeholder |
| `group_labels` | `_schema_meta` | Group display name (Dashboard partition title) |

When using i18n, you must register the translation key to the i18n system in advance (see [i18n documentation](../../advanced/i18n.md#configuration-field-multilingual) for details).

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
                {"label": "Plain string label", "value": "b"},  # Plain string passed through as-is
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

The framework's `resolve_config_schema()` automatically resolves the above fields' i18n keys based on the current language;
`get_config_schema()` passes through the i18n dictionary as-is, letting the frontend parse it.

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

    endpoint: str = "https://api.example.com"   # No metadata description → comment/description from docstring
    timeout: int = 30

    # Google style also supported (Attributes: section):
    # Attributes:
    #     endpoint: Platform API address
```

Priority: **metadata description > docstring field description > empty**.
i18n dictionary form of description is unaffected (always prioritized).

#### Nested Configuration (v2.8.0+)

When the field type is a nested dataclass, the framework recursively processes: schema uses `"type": "table"` +
`"fields"` subtree carries (WebUI renders as collapsible nested group), TOML template renders as `[subtable]` section,
default value / filling / validation / i18n resolution all recursively take effect.

```python
@dataclass
class RetryConfig(BaseConfig):
    """Retry Strategy

    :ivar max_retries: Maximum retry count
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
# Maximum retry count
max_retries = 3
backoff = 0.5
```

> For nested types, it is recommended to use direct type annotations; string annotations (e.g., for delayed evaluation scenarios) must ensure
> the type can be globally resolved from the configuration class module, `__qualname__` outer class namespace, or class attributes by name.

#### Non-persisted example field (v2.8.0+)

```python
gc_interval: int = field(default=300, metadata={"example": True})
```

Fields with `example: True`:

- Not written to config.toml (adapter/module configuration template and default values excluded, runtime uses code default value)
- Only rendered into project's `config.full.example` (for user reference, copy to config.toml as needed)
- Schema with `"example": true` marked (panel can decide display strategy), CLI configuration wizard defaults skip
- After user manually sets this key, it persists normally, updates normally (user's explicit intent takes precedence)

Suitable for "complex but rarely touched" advanced configuration items, keeping the user's config.toml minimal.

> ⚠️ `_schema_meta` is class-level metadata (not a configuration field). If declared inside the dataclass class body,
> it must be annotated with `ClassVar` (`_schema_meta: ClassVar[dict] = {...}`), otherwise it will be treated
> as a regular field by dataclass. The framework defensively excludes fields with leading underscores from any
> schema / template / default value / validation output, but it is still recommended to declare them properly.

### Declarative Translation Keys (v2.7.0+)

Adapters can declare translation keys in a nested class `I18nClass`, similar to declaring `ConfigClass`. The framework automatically registers all declared translation keys during `__init__` (before configuration template generation), ensuring that i18n keys referenced in configuration descriptions are available when generating templates.

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

> ``I18nKey.default`` is a language-agnostic fallback text, not registered to any language.
> To make the translation effective, at least one language parameter must be explicitly passed.
> See [i18n documentation](../../advanced/i18n.md#recommended-usage-declaring-translation-keys-via-i18nclass-v270) for detailed usage (key path rules, explicit key parameter, etc.).

### Declarative Event Extension Methods (v2.7.0+)

Adapters can declare platform-specific event extension methods via `EventMixin`, and the framework automatically registers them to the current platform.

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

> Event extension methods of the adapter are registered to its own platform (``self._platform``).
> Modules need to use the original ``register_event_mixin()`` API for cross-platform event extensions.

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
            self.logger.info("Token has been updated, reconnecting")
```

### Initialization Process

The framework automatically completes the following tasks in `BaseAdapter.__init__(self, sdk=None)`:

1. **SDK Reference**: Set `self.sdk`, `self.logger`
2. **Send/Request Factory**: Create `self.Send` and `self.Request`
3. **Configuration Template**: If `ConfigClass` is declared, automatically generate the default configuration template (first time)
4. **Account Template**: If `AccountConfigClass` is declared, automatically generate the default account template (first time)
5. **EventMixin Registration**: If `EventMixin` is declared, automatically register it to `AdapterManager` after injecting the platform name

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

### Available Properties

The `Send` class automatically sets the following properties when called:

| Property | Description | Setting Method |
|-----|------|---------|
| `_target_id` | Target ID | `To(id)` or `To(type, id)` |
| `_target_type` | Target Type | `To(type, id)` |
| `_target_to` | Simplified Target ID | `To(id)` |
| `_account_id` | Sending Account ID | `Using(account_id)` |
| `_adapter` | Adapter Instance | Automatically set |
| `_at_user_ids` | @ User List | `At(user_id)` |
| `_reply_message_id` | ID of the replied message | `Reply(message_id)` |
| `_at_all` | Whether to @ all | `AtAll()` |

> **Recommendation**: Use the `self.send_context` property to get `target_type`, `target_id`, `account_id` in one go, which is clearer than directly accessing instance variables.

### Framework Helper Methods

| Method/Property | Description |
|-----------|------|
| `self._apply_modifiers(message)` | Merge At/AtAll/Reply modifier states into the message segment list |
| `self.send_context` | Return `{target_type, target_id, account_id}` dictionary |

### Basic Methods

Adapters only need to implement `Raw_ob12`, standard methods (Text/Image/Voice/Video/File) are inherited from `SendDSL` base class and default delegate to it:

```python
class Send(BaseAdapter.Send):
    def Raw_ob12(self, message, **kwargs):
        """Must implement: OneBot12 message segment → Platform API"""
        async def _do_send():
            segments = self._apply_modifiers(message)
            return await self._adapter.call_api(
                endpoint="/send_message",
                message=segments,
                **self.send_context,
                **kwargs
            )
        return asyncio.create_task(_do_send())

    # Text/Image/Voice/Video/File are inherited from base class, automatically delegate Raw_ob12, no need to repeat implementation
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
    "id": "Unique event identifier",
    "time": 1234567890,           # 10-digit Unix timestamp
    "type": "message/notice/request/meta",
    "detail_type": "Event detail type",
    "platform": "Platform name",
    "self": {
        "platform": "Platform name",
        "user_id": "Bot ID"     # Must match bot_id
    },
    "{platform}_raw": {...},       # Original data (must)
    "{platform}_raw_type": "..."    # Original type (must)
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

Adapters in client mode (WebSocket client, HTTP polling, etc.) need to start a persistent connection loop in `start()`. The framework supports two ways, **both correct, but only one can be chosen**:

**Way 1: spawn-return style (Recommended)**—Use `spawn_client_loop()` to schedule the loop as a background task belonging to this platform, `start()` returns immediately:

```python
class MyAdapter(BaseAdapter):
    async def start(self):
        # The loop task belongs to self._platform: framework automatically cancels when shutdown
        self.spawn_client_loop(self._connect_loop())
        # start ends here—“startup is successful”, connection failure handled within loop

    async def _connect_loop(self):
        while True:
            try:
                await self._connect_and_receive()   # Disconnect throws exception → below backoff
            except asyncio.CancelledError:
                raise
            except Exception:
                await asyncio.sleep(5)              # Loop handles backoff and reconnects
```

**Way 2: Persistent style**—`start()` directly `await` the connection loop, never returns:

```python
class MyAdapter(BaseAdapter):
    async def start(self):
        await self._connect_loop()   # Persistent, never returns; loop throws exception = start fails
```

Differences and common points between the two writing styles:

| | spawn-return style | Persistent style |
|---|---|---|
| `start()` return timing | Immediately returns after launching the loop | Returns when the connection loop exits/fails (framework retries according to backoff strategy) |
| Connection failure handling | Exception caught within loop, handled internally | Exception thrown, handed over to the framework's retry chain |
| Suitable scenarios | Need to return startup confirmation quickly (multiple connections, register routes and then launch other tasks) | "Connection is startup" semantics simple implementation |

`spawn_client_loop(coro, *, name="client_loop")` is the scheduling entry for way one: the task is registered by `self._platform`, the framework automatically cancels it when the adapter `shutdown()` without needing to manage task handles yourself; uncaught exceptions within the loop are automatically logged (for expected disconnection and reconnection, please catch them within the loop).

> **The only incorrect way is mixing**: spawning and then `await`ing the same loop—this makes `start()` lose the immediate return semantics, and the task cancellation path becomes unpredictable.

### Connection Mode Semi-Complete Base Classes

In addition to the two writing styles above, the most common connection modes have direct "semi-complete" base classes provided by the framework (`ErisPulse.Core.Bases.adapter_patterns`, importable directly from the root package): `start`/`shutdown` lifecycle orchestration is fully handled by the base class, and the subclass only implements business hooks.

#### PollingAdapter (HTTP Polling Type)

Suitable for platforms that "periodically pull events from the client" (Telegram getUpdates type). The base class starts a persistent polling loop using the spawn-return style, automatically logs failed pulls and applies exponential backoff (base 1 second, upper limit 60 seconds, success resets to zero; constants `POLLING_ADAPTER_BACKOFF_BASE_SECS`/`POLLING_ADAPTER_BACKOFF_MAX_SECS` can be adjusted in `Core/constants.py`):

```python
from ErisPulse import PollingAdapter

class MyAdapter(PollingAdapter):
    # Polling interval defaults to 5 seconds; ConfigClass declares poll_interval field, uses configuration value (hot update takes effect)
    poll_interval = 5.0

    async def fetch_events(self):
        """Pull a batch of platform native events (exceptions handled by base class backoff, no try/except needed)"""
        resp = await self.sdk.client.get(f"{self.cfg.endpoint}/getUpdates")
        data = await resp.json()
        return data.get("result", [])

    def convert_one(self, raw):
        """Convert a single native event to OneBot12; return None to skip"""
        return self.converter.convert(raw)

    async def call_api(self, endpoint: str, **params):
        ...  # Same as regular adapter
```

Minimum implementation surface: `fetch_events`/`convert_one`/`call_api`. `start()` starts the loop and returns immediately; `shutdown()` does not need subclass handling (polling loop is automatically canceled by owner).

#### WebhookAdapter (HTTP Callback Type)

Suitable for platforms that "push callbacks from the platform." The base class's `start()` registers the receiving route on the framework router (final path `/{platform name}/webhook`, POST method), registered in `owner_scope`—the adapter unloads automatically clean up by owner, no need to manually deregister:

```python
from ErisPulse import WebhookAdapter

class MyAdapter(WebhookAdapter):
    def verify_request(self, request) -> bool:
        """Optional hook: callback verification (default allows, return False to deny by base class with 403)"""
        cfg = self.cfg
        if not cfg.token:
            return True
        auth = request.headers.get("authorization", "")
        return auth == f"Bearer {cfg.token}"

    def convert(self, payload):
        """Convert callback payload to OneBot12; return None to skip"""
        return self.converter.convert(payload)

    async def call_api(self, endpoint: str, **params):
        ...  # Same as regular adapter
```

Minimum implementation surface: `convert`/`call_api` (`verify_request` optional). The callback address is queried via `sdk.adapter.get_connection_info(platform)` and filled into the platform backend; requests with failed verification return 403, payload parsing failures return 400, normal returns `{"status": "ok"}`.

#### How to Choose the Three Modes

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

> Pure callback-type platforms do not need to manually write the above registration/verification/cleanup orchestration—simply inherit the [`WebhookAdapter` semi-complete base class](#connection-mode-semi-complete-base-classes) and implement `convert` (optionally override `verify_request`).

> **Route information query**: The routes registered by the adapter (HTTP, WebSocket, SSE) can be queried via `sdk.adapter.get_connection_info(platform)` and `sdk.router.get_module_urls(module_name)` to get the complete connection address (including `base_url` + path). See [Getting Started with Adapter Development - Connection Information and Route Discovery](getting-started.md#9-connection-information-and-route-discovery) and [SSE Support](getting-started.md#10-sse-server-sent-events-support).

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

### Manually Constructed Response (Old Method Still Compatible)

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

# Through event's self.user_id (recommended, most universal)
await my_adapter.Send.Using(event["self"]["user_id"]).To("user", "123").Text("Hello")

# Through account name
await my_adapter.Send.Using("account1").To("user", "123").Text("Hello")
```

### Relationship Between self.user_id and Using

The framework's event reply mechanism automatically extracts `account_id` (prioritized) or `user_id` from the event's `self` field as the `Using` parameter. Adapter developers need to ensure that the Converter correctly sets `self.user_id` to match `_resolve_account`.

**Framework Internal Behavior**:

```python
# Framework extraction of bot_id logic
bot_id = self.get("self", {}).get("account_id", "") or self.get("self", {}).get("user_id", "")

# Only call Using if bot_id is non-empty
if bot_id:
    send_chain = send_chain.Using(bot_id)
```

> **Key Point**: Even if the adapter uses only one Bot configuration, as long as the Converter correctly sets `self.user_id`, the framework will use it as the `Using` parameter. The adapter needs to ensure that `self.user_id` matches the identifier field (such as `bot_id`) in `AccountConfigClass` so that `_resolve_account()` can match the correct account. If `self.user_id` is empty, the framework will not call `Using`, and `call_api` will receive `account_id` as `None`, and `_resolve_account(None)` returns the first enabled account.

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

> **Backward Compatibility**: Code for old adapters using `aiohttp.ClientSession` is unaffected and can still capture `aiohttp.ClientError`. Both methods can coexist. New code is recommended to use `sdk.client` + ErisPulse exception system.

## Bot Status Management

The `AdapterManager` has a built-in bot status tracking system that automatically maintains the online status, active time, and metadata of all registered bots.

### Automatic Discovery Mechanism

When the adapter emits an event via `adapter.emit()`, the framework automatically checks the `self` field in the event:

- **meta events**: Perform corresponding operations based on `detail_type` (register on connect, mark offline on disconnect, update active time on heartbeat)
- **ordinary events** (message/notice/request): Automatically discover bot and update active time

```python
# All events containing self field trigger automatic discovery
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
| `connect` | Bot connects | Register bot and trigger `adapter.bot.online` lifecycle event |
| `disconnect` | Bot disconnects | Mark bot as offline and trigger `adapter.bot.offline` lifecycle event |
| `heartbeat` | Bot heartbeat | Update bot active time and metadata |

### Adapter Sending Meta Events

Sending methods (one-line `emit_meta`, heartbeat events and manual construction format) are detailed in [Adapter Best Practices - Bot Status Management and Meta Events](best-practices.md#bot-status-management-and-meta-events).

### `self` Field Extended Information

Besides the required `platform` and `user_id`, the `self` field supports the following optional fields:

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

## Related Documents

### Implementation-Level Deep Dive

- [SendDSL Detailed Explanation](send-dsl.md) - Learn message sending
- [Adapter Best Practices](best-practices.md) - Develop high-quality adapters

### Reviewing the Starting Steps

- [Getting Started with Adapter Development](getting-started.md) - Create your first adapter