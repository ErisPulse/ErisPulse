# Core Adapter Concepts

> [!TIP]
> **When to read this**: Mandatory for adapter development path (complete explanation of BaseAdapter/SendDSL/lifecycle core mechanisms). For quick start, read [Adapter Development Introduction](getting-started.md) first, and return here when encountering "why" level questions.

This document explains the adapter's runtime mechanism: how AdapterManager registers and distributes events, what `BaseAdapter` does for you during initialization, how to declare configurations and multiple accounts—when you encounter "why should it be written this way" questions while writing adapters, refer here.

## Adapter Architecture

### Component Relationships

```
Forward Conversion (Receiving Direction)                           Reverse Conversion (Sending Direction)
─────────────────                           ─────────────────
                                             
┌──────────────────┐                        ┌──────────────────┐
│ Platform Native Event     │                        │ Module Message     │
└────────┬─────────┘                        └────────┬─────────┘
         │                                           │
         ↓                                           ↓
┌──────────────────┐   ┌──────────────────┐   ┌──────────────────┐
│                  │   │  Adapter (MyAdapter) │   │ Send.Raw_ob12()  │
│  Converter       │   │ ┌──────────────┐ │   │ (Reverse Conversion Entry)   │
│  (Event Converter)    │──→│ │              │ │   │                  │
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
                       │ Module (Event Handler)  │
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

# Register adapter (usually automatically done by Loader)
sdk.adapter.register("myplatform", MyPlatformAdapter)

# Startup all adapters
await sdk.adapter.startup()

# Startup specified adapter
await sdk.adapter.startup(["myplatform"])
# Startup all adapters
await sdk.adapter.startup()

# Get adapter instance
my_adapter = sdk.adapter.get("myplatform")
# Or access via attribute
my_adapter = sdk.adapter.myplatform

# Shutdown all adapters
await sdk.adapter.shutdown()
```

### Startup and Shutdown

#### Startup Adapter

```python
# Startup all registered adapters
await sdk.adapter.startup()

# Startup specified platform
await sdk.adapter.startup(["platform1", "platform2"])
```

**Startup Process**:

1. Submit `adapter.start` lifecycle event
2. Submit `adapter.status.change` event (starting)
3. Parallel startup of each adapter
4. If startup fails, automatic retry (exponential backoff strategy)
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
3. Shutdown router server
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

# Listen to all platforms' standard message events
@sdk.adapter.on("message")
async def handle_message(data):
    print(f"Received OneBot12 message: {data}")

# Listen to standard message events from a specific platform
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
# Listen to native events from a specific platform
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
        return None  # Returning None means the middleware chain will ignore this return value, retaining the original data for further passing
    return data  # Must return data to continue passing
```

#### Middleware Return Contract

| Return Value | Behavior |
|--------|------|
| `dict` | Rewrite event payload (subsequent handlers receive the rewritten event) |
| `None` | Allow passage, payload unchanged (outputs WARNING prompt—recommended to explicitly `return data`) |
| `False` | **Reject**: Event is discarded, not entering any handler, no outbound side effects |

Rejection is suitable for firewall, rate limiting, blacklist scenarios that "discard at the event level" (previously only achievable via high-priority event handlers). When rejected, the framework outputs TRACE log and triggers the `adapter.event.blocked` lifecycle hook (carrying `middleware` middleware name, complete `event`, `platform` / `event_type` / `detail_type`), facilitating troubleshooting for "why an event didn't respond":

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

Middlewares execute in registration order, with later registered middlewares executing first.

> **Note**: If a middleware returns `None` (e.g., forgetting `return data`), the framework will ignore this return value and retain the original data for further passing, while outputting a warning-level log. This ensures that a single middleware mistake does not interrupt the entire event chain.

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
    """Adapter Configuration (declared, framework automatically manages)"""
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
    
    # No need to override __init__, framework automatically handles:
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

The framework provides declarative configuration management, defining configuration structures through dataclasses, and the framework automatically handles loading, validation, and template generation.

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

# If bot_id cannot be obtained during login, let the user fill it in the configuration
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
    "secret": bool,           # Whether sensitive (WebUI displays as ***, logs are masked)
    "example": bool,          # Not persisted flag: not written to config.toml (default values/templates excluded),
                              # only rendered into config.full.example; schema with "example": true marked,
                              # CLI configuration wizard defaults skip; after user manually sets, normal persistence
    "min": number, "max": number,  # Numeric range validation
    "ui": {                   # WebUI control configuration (old name "webui" still compatible)
        "widget": str,        # Control type: "text" | "switch" | "select" | "number" | "password"
        "group": str,         # Group: "basic" | "advanced" | "connection" etc.
        "order": int,         # Sorting weight (smaller values appear earlier)
        "options": list,      # Options for select control [{label, value}], label supports i18n
        "placeholder": str | dict,  # Input box placeholder (supports i18n)
    },
    "extra": dict,            # Additional extended fields (passed through to schema)
}
```

All user-visible text fields support i18n, uniformly using the `{"i18n": "key", "default": "text"}` format,
pure strings are passed through as is (backward compatibility). Supported i18n fields:

| Field | Location | Description |
|------|------|------|
| `description` | field metadata | Field description |
| `options[].label` | `ui.options` | Select control option label |
| `placeholder` | `ui.placeholder` | Input box placeholder |
| `group_labels` | `_schema_meta` | Group display name (Dashboard partition title) |

When using i18n, you need to register the translation key in the i18n system in advance (see [i18n documentation](../../advanced/i18n.md#configuration-field-multilingual) for details).

**description / placeholder / options label** Example:

```python
token: str = field(
    default="",
    metadata={
        "description": {"i18n": "my_adapter.token", "default": "Bot Token"},
        "ui": {
            "widget": "text",
            "placeholder": {"i18n": "my_adapter.token.ph", "default": "Please enter Token"},
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
                {"label": "Plain string label", "value": "b"},  # Plain string passed through as is
            ],
        },
    },
)
```

**group_labels** Example (declared after configuration class definition):

```python
MyConfig._schema_meta = {
    "group_labels": {
        "basic": {"i18n": "my_adapter.group.basic", "default": "Basic Settings"},
        "advanced": {"i18n": "my_adapter.group.advanced", "default": "Advanced Settings"},
    }
}
```

The framework's `resolve_config_schema()` automatically resolves the above fields' i18n keys according to the current language;
`get_config_schema()` passes the i18n dictionary as is, and the frontend parses it itself.

#### docstring Auto-generates Field Descriptions (v2.8.0+)

Fields without `description` declared in metadata, the framework automatically extracts field descriptions from the configuration class docstring as a fallback, supporting two common styles (can be mixed):

```python
@dataclass
class MyConfig(BaseConfig):
    """
    MyAdapter Configuration

    :ivar endpoint: Platform API Address        # reST style
    :ivar timeout: Request timeout in seconds
    """

    endpoint: str = "https://api.example.com"   # No metadata description → comment/description from docstring
    timeout: int = 30

    # Google style also supported (Attributes: section):
    # Attributes:
    #     endpoint: Platform API Address
```

Priority: **metadata description > docstring field description > empty**.
i18n dictionary form of description is unaffected (always prioritized).

#### Nested Configuration (v2.8.0+)

When the field type is a nested dataclass, the framework recursively processes it: schema uses `"type": "table"` +
`"fields"` subtree (WebUI renders as collapsible nested groups), TOML template renders as `[sub-table]` section,
default values / filling / validation / i18n parsing all recursively take effect.

```python
@dataclass
class RetryConfig(BaseConfig):
    """Retry Strategy

    :ivar max_retries: Maximum retry attempts
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
# Maximum retry attempts
max_retries = 3
backoff = 0.5
```

> For nested types, it is recommended to use direct type annotations; string annotations (e.g., for delayed evaluation scenarios) must ensure
> the type is globally resolvable from the configuration class's module, `__qualname__` outer class namespace, or class attribute by name.

#### Non-persisted example fields (v2.8.0+)

```python
gc_interval: int = field(default=300, metadata={"example": True})
```

Fields with `example: True`:

- Not written to config.toml (adapter/module configuration template and default values excluded, runtime uses code default values)
- Only rendered into project's `config.full.example` (for user reference, manually copy to config.toml as needed)
- Schema includes `"example": true` marker (panel can decide display strategy), CLI configuration wizard defaults skip
- After user manually sets this key, it persists normally, hot-updates normally (user's explicit intent takes precedence)

Suitable for "complex and rarely touched" advanced configuration items, keeping the user's config.toml minimal.

> ⚠️ `_schema_meta` is class-level metadata (not a configuration field). If declared inside the dataclass class body,
> it must be annotated with `ClassVar` (`_schema_meta: ClassVar[dict] = {...}`), otherwise it will be
> treated as a regular field by dataclass. The framework defensively excludes fields with leading underscores from any
> schema/template/default/valid output, but it is still recommended to declare them properly.

### Declarative Translation Keys (v2.7.0+)

Adapters can declare translation keys like `ConfigClass` by nesting the `I18nClass` class, and the framework automatically registers all declared translation keys during `__init__` (before configuration template generation), ensuring that referenced i18n keys in configuration descriptions are available when generating templates.

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

> ``I18nKey.default`` is a language-agnostic fallback text and will not be registered in any language.
> To make the translation effective, at least one language parameter must be explicitly passed.

For detailed usage (key path rules, explicit key parameter, etc.), see [i18n documentation](../../advanced/i18n.md#recommended-usage-declaring-translation-keys-via-i18nclass-v270).

### Declarative Event Extension Methods (v2.7.0+)

Adapters can declare platform-specific event extension methods through `EventMixin` to centrally declare, and the framework automatically registers them to the current platform.

```python
from ErisPulse.Core import BaseAdapter

class MyAdapter(BaseAdapter):
    class EventMixin:
        def get_chat_name(self):
            """Get chat name"""
            return self.get("myplatform_raw", {}).get("chat", {}).get("name", "")

        def is_official_message(self):
            """Check if it's an official message"""
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

> Adapter's event extension methods are registered to its own platform (``self._platform``).
> Modules needing cross-platform event extensions should use the original ``register_event_mixin()`` API.

#### Account Resolution

When adapters implement `call_api`, they need to resolve the account identifier into a specific account configuration. The framework passes the account binding (result of `Using()` or automatic binding result from the event chain) to `call_api` as a standard field `account_id`, and automatically adapts it according to the adapter's actual consumption method—three consumption forms are available, and the framework detects them via signature parameter names and function body constants, independent of parameter position:

```python
# Form 1 (Recommended): Declare standard names in signature
async def call_api(self, endpoint: str, account_id: str | None = None, **params):
    name, account = self._resolve_account(account_id)
    # name: account name, account: configuration instance

# Form 2 (Legacy Compatibility): Old name _account_id, framework automatically rewrites account_id to old name for dispatch
async def call_api(self, endpoint: str, _account_id: str | None = None, **params):
    name, account = self._resolve_account(_account_id)

# Form 3: Function body retrieves from params (recognized by constant detection)
async def call_api(self, endpoint: str, **params):
    account_id = params.pop("account_id", None)
    name, account = self._resolve_account(account_id)
```

> When the adapter does not consume the account field, the framework removes the field (to avoid leaking into platform parameters) and issues a single WARNING; single-account adapters can omit consumption (resolution falls back to the first enabled account).

Resolution strategy: account name match → `bot_id` field match → other str field match → first enabled account.

**Runtime Identification and Persistence** (2.12+): When the adapter establishes a connection / event arrival, it calls `self.update_bot_id(account_name, bot_id)`—the framework maintains a bot_id → account registration table (first priority in resolution chain), and writes `accounts.<account name>.bot_id` to the configuration store when the value changes: after restart, the account instance is reconstructed with its own bot_id, and for second accounts, etc., the resolution no longer depends on account activity backfilling (eliminating the restart window).

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
5. **EventMixin Registration**: If `EventMixin` is declared, automatically register it in `AdapterManager` after injecting the platform name

Configuration is read in real-time via `self.cfg` / `self.accounts` (each access reads the latest value from the configuration store). `self.config` as a compatibility alias for `self.cfg` is still usable.

Most adapters do not need to override `__init__`. If custom initialization is required:

```python
class MyAdapter(BaseAdapter):
    ConfigClass = MyConfig
    
    def __init__(self, sdk=None):
        super().__init__(sdk)  # Pass in sdk
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

`Send` class automatically sets the following properties when called:

| Property | Description | Setting Method |
|-----|------|---------|
| `_target_id` | Target ID | `To(id)` or `To(type, id)` |
| `_target_type` | Target Type | `To(type, id)` |
| `_target_to` | Simplified Target ID | `To(id)` |
| `_account_id` | Sending Account ID | `Using(account_id)` |
| `_adapter` | Adapter Instance | Automatically set |
| `_at_user_ids` | @ User List | `At(user_id)` |
| `_reply_message_id` | Reply Message ID | `Reply(message_id)` |
| `_at_all` | Whether @ All | `AtAll()` |

> **Recommended**: Use `self.send_context` property to get `target_type`, `target_id`, `account_id` at once, which is clearer than directly accessing instance variables.

### Framework Helper Methods

| Method/Property | Description |
|-----------|------|
| `self._apply_modifiers(message)` | Merge At/AtAll/Reply modifier states into message segment list |
| `self.send_context` | Returns `{target_type, target_id, account_id}` dictionary; `account_id` falls back to the triggering account of the event distribution chain if not explicitly specified |

### Basic Methods

Adapters only need to implement `Raw_ob12`, standard methods (Text/Image/Voice/Video/File) are inherited from the `SendDSL` base class and default to delegating it:

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

    # Text/Image/Voice/Video/File are inherited from base class, automatically delegate Raw_ob12, no need to reimplement
    # If platform-specific logic is needed, override individual methods:
    # def Text(self, text: str):
    #     return self.Raw_ob12([{"type": "text", "data": {"text": text}}])
```

### Chaining Modifier Methods

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
    "id": "Unique Event ID",          # Same event must have the same ID for the same account (framework uses this for deduplication)
    "time": 1234567890,           # 10-digit Unix timestamp
    "type": "message/notice/request/meta",
    "detail_type": "Detailed Event Type",
    "platform": "Platform Name",
    "message_id": "Message ID",        # Required for message-type events
    "self": {
        "platform": "Platform Name",
        "user_id": "Bot ID"     # Must match bot_id
    },
    "{platform}_raw": {...},       # Raw data (must)
    "{platform}_raw_type": "..."    # Raw type (must)
}
```

> Event `id` must be account-scoped: Same event must have the same `id` for the same account, different accounts receiving the same group message must have different `id` (e.g., `f"{self.user_id}:{post_type}:{message_id}"`).

### Cross-Account Duplicate Handling (Framework Injected Fields)

For multi-account adapters, the same physical message arrives at different accounts in the same group/session. The framework automatically performs content-level association when `ErisPulse.framework.cross_account_policy != "off"` (adapters do not participate):

- `mark`: Subsequent copies inject the top-level field `"multi_receipt": {"event_id": first-handled event id, "self_id": first-handled account}` and distribute normally, modules read this field to decide
- `drop`: Subsequent copies are directly discarded at the distribution entrance
- **Mention Point Exception**: If the `message` segment's mention target matches the receiving account's own identity (`self.user_id` / `self.account_id`), the copy is exempt from association (`mark` / `drop` both exempt) — the mentioned account must receive its own event, `drop` does not mistakenly discard @-driven multi-account modules; @ messages may be distributed once per account, @-driven modules naturally only respond once via `on_at_message` condition

#### Session Account Binding (Precise Assignment Declaration)

Content-level association relies on heuristic judgment ("who arrives first wins"); when **precise assignment of session ownership** is needed, use `ErisPulse.framework.session_accounts` configuration to bind the session to a single account:

```toml
[ErisPulse.framework.session_accounts.snowluma]
"group:643319481" = "1325859446"   # Recommended prefix key: session type:session ID → assigned account
"643319481" = "1325859446"         # Bare key compatible write: binds all sessions of this session ID
```

> Prefix keys isolate same-numbered different-type sessions (group `group:123` and private chat `user:123` do not interfere); bare keys are compatible writes, binding means the session is exclusively assigned.

- Binding **takes effect independently of `cross_account_policy`** (configuration binding equals enabling deduplication for this session): The assigned account's events are distributed normally, other account copies are discarded at the distribution entrance
- **Mention point exception still applies**: Non-assigned account copies that are mentioned are still allowed
- Binding reads configuration in real-time, hot updates take effect; sessions not configured with binding are unaffected
- Suitable for "single session, multiple accounts, only one account responds" deployment: More precise than content-level association, no 3-second window and content comparison heuristic errors

`multi_receipt` is an optional field injected by the framework, the adapter Converter does not produce or consume it; the policy is `off` by default, the event structure is consistent with the existing contract.

#### Three-tier Deduplication Mechanism Division of Labor

| Mechanism | Configuration | What to Intercept | Determination Basis |
|------|------|----------|----------|
| Event Idempotency Deduplication | `ErisPulse.framework.event_dedupe` (default on) | Same event id's reconnection/repush (same connection) | Event `id` |
| Self-message Echo Filtering | `ErisPulse.event.message.ignore_self` (default on) | Receiving the account's own message (sender == receiving account) | `self.user_id` vs `user_id` |
| Cross-account Duplicate Handling | `ErisPulse.framework.cross_account_policy` (default `off`, `drop` enabled) | **Physical message received by other accounts**—when multiple accounts are in the same group, bot A speaks, bot B also receives a copy (mention-targeted copies exempt) | Content-level association (same platform + same session + same sender + same content, short window), key does not contain self_id |

**Typical Scenario—Multiple Accounts Repeating in Same Group**: Bot A speaks, other accounts (bot B) in the same group also receive a copy, causing repeat modules to see the same content twice. Enabling `cross_account_policy = "drop"` discards subsequent account copies at the distribution entrance, ensuring any module sees it at most once. **Exception: At-mention Messages**—The account copy that is mentioned is always allowed (modules driven by @ depend on it for response), other account copies are deduplicated as usual.

The semantics of `ignore_self` are orthogonal, and the combination of the two determines the visibility count:

| Combination | Repeat Module Sees Bot A's Message |
|------|--------------------------|
| `drop` + `ignore_self = true` (default) | 0 or 1 times (if the first copy from A's own connection is intercepted by `ignore_self`) — **Never 2 times** |
| `drop` + `ignore_self = false` | Exactly 1 time |

> It is not recommended to extend the semantics of `ignore_self` to "exclude all local accounts": This determination depends on the `self.user_id` of the event being received (the binding is ineffective during the unestablished window, see above "Runtime Identification and Persistence"), and cross-account association is content-level determination, independent of self information; and "receiving one account at a time" is an existing dependency of cross-account logging/synchronization modules, narrowing the semantics is an implicit destruction. Cross-account deduplication is left to `cross_account_policy`.

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

### Two Correct Ways to Write start()

Adapters that are client-mode (WebSocket client, HTTP polling, etc.) need to start a persistent connection loop in `start()`. The framework supports two ways, **both are correct, but only one can be chosen**:

**Way 1: spawn-return style (Recommended)**—Use `spawn_client_loop()` to schedule the loop as a background task belonging to the current platform, `start()` returns immediately:

```python
class MyAdapter(BaseAdapter):
    async def start(self):
        # The loop task belongs to self._platform: automatically cancelled by framework when shutdown
        self.spawn_client_loop(self._connect_loop())
        # start ends here — "startup is successful", connection failure handled within the loop

    async def _connect_loop(self):
        while True:
            try:
                await self._connect_and_receive()   # Disconnect throws exception → below backoff
            except asyncio.CancelledError:
                raise
            except Exception:
                await asyncio.sleep(5)              # Loop handles backoff and reconnection itself
```

**Way 2: Persistent Style**—`start()` directly `await` the connection loop, which never returns:

```python
class MyAdapter(BaseAdapter):
    async def start(self):
        await self._connect_loop()   # Persistent and never returns; loop throws exception = start failure
```

Differences and common points between the two ways:

| | spawn-return style | Persistent style |
|---|---|---|
| `start()` return timing | Immediately returns after launching the loop | When the loop exits/fails (framework retries according to backoff strategy) |
| Connection failure handling | Handled within the loop, with self-backoff | Exception thrown, handed over to the framework's retry chain |
| Applicable scenarios | Need to return startup confirmation quickly (multiple connections, register routes and then launch other tasks) | "Connection is startup" semantic simple implementation |

`spawn_client_loop(coro, *, name="client_loop")` is the dispatch entry for way one: the task is registered under `self._platform`, and the framework automatically cancels it when the adapter `shutdown()` is called, without needing to manage task handles yourself; unhandled exceptions in the loop are automatically logged (expected disconnects and reconnects should be caught within the loop).

> **The only incorrect way is mixing**—spawning and then awaiting the same loop—this causes `start()` to lose its immediate return semantics, and the task cancellation path becomes unpredictable.

### Connection Mode Semi-finished Base Classes

In addition to the two ways above, the most common connection modes have direct "semi-finished" base classes provided by the framework (`ErisPulse.Core.Bases.adapter_patterns`, root package can be directly imported): `start` / `shutdown` lifecycle orchestration is fully handled by the base class, and subclasses only implement business hooks.

#### PollingAdapter (HTTP Polling Type)

适用于「客户端定时拉取事件」的平台（Telegram getUpdates型）。基类以
spawn-返回式拉起常驻轮询循环，拉取失败自动留痕并指数退避（基数 1 秒、上限
60 秒，成功后归零；常量 `POLLING_ADAPTER_BACKOFF_BASE_SECS` /
`POLLING_ADAPTER_BACKOFF_MAX_SECS` 可在 `Core/constants.py` 调整）：

```python
from ErisPulse import PollingAdapter

class MyAdapter(PollingAdapter):
    # 轮询间隔默认 5 秒；ConfigClass 声明 poll_interval 字段后以配置值为准（热更新生效）
    poll_interval = 5.0

    async def fetch_events(self):
        """拉一批平台原生事件（异常由基类统一退避，无需 try/except）"""
        resp = await self.sdk.client.get(f"{self.cfg.endpoint}/getUpdates")
        data = await resp.json()
        return data.get("result", [])

    def convert_one(self, raw):
        """单条原生事件转 OneBot12；返回 None 跳过"""
        return self.converter.convert(raw)

    async def call_api(self, endpoint: str, **params):
        ...  # 与普通适配器相同
```

最小实现面：`fetch_events` / `convert_one` / `call_api`。`start()` 拉起循环后立即
返回；`shutdown()` 无需子类处理（轮询循环按 owner 归属自动取消）。

#### WebhookAdapter (HTTP Callback Type)

适用于「平台主动推送回调」的平台。基类的 `start()` 在 framework router 上注册接收路由
（最终路径 `/{平台名}/webhook`，POST 方法），注册包在 `owner_scope` 中——适配器
卸载时按 owner 自动清理，无需手动注销：

```python
from ErisPulse import WebhookAdapter

class MyAdapter(WebhookAdapter):
    def verify_request(self, request) -> bool:
        """可选钩子：回调校验（默认放行；返回 False 时基类以 403 回绝）"""
        cfg = self.cfg
        if not cfg.token:
            return True
        auth = request.headers.get("authorization", "")
        return auth == f"Bearer {cfg.token}"

    def convert(self, payload):
        """回调载荷转 OneBot12；返回 None 跳过"""
        return self.converter.convert(payload)

    async def call_api(self, endpoint: str, **params):
        ...  # 与普通适配器相同
```

最小实现面：`convert` / `call_api`（`verify_request` 可选）。回调地址经
`sdk.adapter.get_connection_info(platform)` 查询后填到平台后台；校验失败的请求
返回 403、载荷解析失败返回 400、正常返回 `{"status": "ok"}`。

#### 三种模式怎么选

| 平台协议 | 继承 | 脚手架 |
|---|---|---|
| 平台连过来（WebSocket 服务端） | `BaseAdapter` | `epsdk create adapter`（默认 ws-server） |
| 我们去拉（HTTP 轮询） | `PollingAdapter` | `epsdk create adapter --template polling` |
| 平台推过来（HTTP 回调） | `WebhookAdapter` | `epsdk create adapter --template webhook` |

完整可运行示例见仓库 `examples/example-adapter/`（ws-server）、
`examples/example-adapter-polling/`、`examples/example-adapter-webhook/`。

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

> 纯回调型平台不必手写上面这套注册/校验/清理编排——直接继承
> [`WebhookAdapter` 半成品基类](#连接模式半成品基类)，只实现 `convert`
> （可选覆写 `verify_request`）即可。

> **路由信息查询**：适配器注册的路由（HTTP、WebSocket、SSE）可以通过 `sdk.adapter.get_connection_info(platform)` 和 `sdk.router.get_module_urls(module_name)` 查询完整连接地址（包含 `base_url` + 路径）。详见 [适配器开发入门 - 连接信息与路由发现](getting-started.md#9-连接信息与路由发现) 和 [SSE 支持](getting-started.md#10-sse-server-sent-events-支持)。

## API Response Standard

The framework provides `make_response()` and `make_error()` methods to construct standardized responses, without manually building response dictionaries.

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

### Manual Response Construction (Old Style Still Compatible)

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

## Multi-account Support

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
    
    async def call_api(self, endpoint: str, account_id: str | None = None, **params):
        name, account = self._resolve_account(account_id)
        # Use account.token, account.bot_id, etc. fields
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

### Event Account Identifier and Its Relationship with Using

The framework's event reply mechanism automatically extracts account identifiers (prioritizing `account_id`, otherwise `user_id`) from the event's `self` field and injects them into `Using`. Adapter developers must ensure that the Converter produces account identifiers that match the account configurations (account name or `bot_id` fields).

**Framework Injection Behavior**:

```python
# Framework extracts account identifier logic (account_id prioritized, otherwise user_id as fallback)
account = self.get("self", {}).get("account_id", "") or self.get("self", {}).get("user_id", "")

# Only inject Using if identifier is non-empty
if account:
    send_chain = send_chain.Using(account)
```

> **Key Point**: Even if the adapter only uses a single Bot configuration, as long as the Converter correctly sets the account identifier, the framework will inject it into `Using`. The adapter must ensure that this identifier matches the account name or `bot_id` fields in the `AccountConfigClass` to resolve to the correct account. If the identifier is empty, the framework does not inject `Using`, and sending proceeds without specifying an account—falling back to the first enabled account.

If the explicitly passed `account_id` cannot be resolved, the framework logs a WARNING and falls back to the first enabled account; the WARNING includes `platform` / `account_id` / `account` to locate the source of events not belonging to an account.

**Automatic Binding in Event Dispatch Chain**: When calling send methods within the event handling chain, **explicit `Using()` is not required**—the framework injects the account identifier from the triggering event into the call context at the event dispatch entrance, and `Send` / `Api` / `Request` chains use this as a fallback binding if no account is explicitly specified (explicit `Using()` always takes precedence; timers / startup tasks without event context maintain default account semantics). Automatic binding in the event chain requires ErisPulse **2.12+**.

> The `self.user_id` / `self.account_id` field in events is part of the output contract for automatic discovery; this field must always exist as the basis for fallback account resolution—if missing, it falls back to the first enabled account, and in multi-account scenarios, it means "sent from the default account."

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
        self.logger.error(f"Request timed out: {endpoint}")
        return self._error_response("Request timed out", 32000)
    except ClientError as e:
        self.logger.error(f"Network error: {e}")
        return self._error_response("Network request failed", 33000)
    except Exception as e:
        self.logger.error(f"Unknown error: {e}")
        return self._error_response(str(e), 34000)
```

> **Backward Compatibility**: Code using `aiohttp.ClientSession` from old adapters is unaffected and can still catch `aiohttp.ClientError`. Both approaches can coexist. New code is recommended to use `sdk.client` + ErisPulse exception system.

## Bot Status Management

AdapterManager includes a built-in Bot status tracking system that automatically maintains the online status, active time, and metadata of all registered Bots.

### Automatic Discovery Mechanism

When the adapter emits an event via `adapter.emit()`, the framework automatically checks the event's `self` field:

- **meta events**: Perform corresponding operations based on `detail_type` (register on connect, mark as offline on disconnect, update active time on heartbeat)
- **regular events** (message/notice/request): Automatically discover Bots and update active time

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
| `connect` | Bot connects | Register Bot and trigger `adapter.bot.online` lifecycle event |
| `disconnect` | Bot disconnects | Mark Bot as offline and trigger `adapter.bot.offline` lifecycle event |
| `heartbeat` | Bot heartbeat | Update Bot active time and metadata |

### Adapter Sending Meta Events

Sending method (`emit_meta()` one-line send, heartbeat event and manual construction format) see [Adapter Best Practices - Bot Status Management and Meta Events](best-practices.md#bot-状态管理与-meta-事件).

### `self` Field Extended Information

Besides the required `platform` and `user_id`, the `self` field supports the following optional fields:

| Field | Description |
|---|---|
| `user_name` | Bot username |
| `nickname` | Bot nickname |
| `avatar` | Bot avatar URL |
| `account_id` | Multi-account identifier |

### Bot Status Query

Query APIs (`get_bot_info()` / `list_bots()` / `is_bot_online()` / `get_status_summary()`) see [Adapter System API - Bot Status Management](../../api-reference/adapter-system.md#bot-状态管理).

### Listening to Bot Lifecycle

`adapter.bot.online` / `adapter.bot.offline` lifecycle event table and listening examples see [Adapter System API - Bot Status Management](../../api-reference/adapter-system.md#bot-状态管理).

## Related Documentation

### Implementation Level Deep Dive

- [SendDSL Detailed Explanation](send-dsl.md) - Learn message sending
- [Adapter Best Practices](best-practices.md) - Develop high-quality adapters

### Revisit Getting Started Steps

- [Adapter Development Introduction](getting-started.md) - Create your first adapter