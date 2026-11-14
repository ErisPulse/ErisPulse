# Core Adapter Concepts

> [!TIP]
> **When to read this**: Mandatory for adapter development path (complete explanation of core mechanisms: BaseAdapter / SendDSL / lifecycle). For quick start, read [Getting Started with Adapter Development](getting-started.md) first, and return to this document when encountering "why" related questions.

This document explains the adapter's runtime mechanism: how `AdapterManager` registers and dispatches events, what `BaseAdapter` does for you during initialization, how to declare configurations and multiple accounts—when you encounter "why should I write this way" during adapter development, refer to this document.

## Adapter Architecture

### Component Relationships

```
Forward Conversion (Receive Direction)                           Reverse Conversion (Send Direction)
─────────────────                           ─────────────────
                                             
┌──────────────────┐                        ┌──────────────────┐
│ Platform Native Event     │                        │ Module Constructed Message     │
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
                       │ Module (Event Handling)  │
                       └──────────────────┘
```

**Core Symmetry**:
- **Forward Conversion** (Converter): Platform native event → OneBot12 standard event, original data preserved in `{platform}_raw`
- **Reverse Conversion** (Raw_ob12): OneBot12 message segment → Platform API call, returns standard response format

## AdapterManager Adapter Manager

`AdapterManager` is the core component of the ErisPulse adapter system, responsible for managing all platform adapters' registration, startup, shutdown, and event dispatch.

### Core Functions

- **Adapter Registration**: Register and manage multiple platform adapters
- **Lifecycle Management**: Control adapter startup and shutdown
- **Event Dispatch**: Dispatch OneBot12 standard events and platform native events
- **Configuration Management**: Manage adapter enable/disable status
- **Middleware Support**: Support OneBot12 event middleware

### Basic Usage

```python
from ErisPulse import sdk

# Register adapter (usually handled automatically by Loader)
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

#### Startup Adapter

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

# Listen to all standard message events
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
# Listen to specific platform's native event
@sdk.adapter.on("raw_event_type", raw=True, platform="myplatform")
async def handle_raw_event(data):
    print(f"Received raw event: {data}")

# Listen to all platforms' native events (wildcard)
@sdk.adapter.on("*", raw=True)
async def handle_all_raw_events(data):
    print(f"Received raw event: {data}")
```

#### Event Dispatch Mechanism

When calling `adapter.emit(event_data)`:

1. **Middleware Handling**: Execute all OneBot12 middlewares first
2. **Standard Event Dispatch**: Dispatch to matching OneBot12 event handlers
3. **Native Event Dispatch**: If raw data exists, dispatch to native event handlers

**Matching Rules**:

- Exact match: `@sdk.adapter.on("message")` only matches `message` events
- Wildcard: `@sdk.adapter.on("*")` matches all events
- Platform filter: `platform="myplatform"` only dispatches events for the specified platform

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
        return None  # Return None to ignore the return value in the middleware chain, retaining the original data for further transmission
    return data  # Must return data to continue transmission
```

#### Middleware Return Contract

| Return Value | Behavior |
|--------|------|
| `dict` | Rewrite event payload (subsequent handlers receive the modified event) |
| `None` | Allow passage, payload unchanged (outputs WARNING message—recommended to explicitly return `data`) |
| `False` | **Reject**: Event is discarded, not entering any handler, no outbound side effects |

Rejection is suitable for scenarios like firewall, rate limiting, blacklist, where events are discarded at the event level (previously only achievable through high-priority event handlers). When rejection occurs, the framework outputs a TRACE log and triggers the `adapter.event.blocked` lifecycle hook (carrying `middleware` middleware name, complete `event`, `platform` / `event_type` / `detail_type`), facilitating troubleshooting for "why the event wasn't responded to":

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

> **Note**: If a middleware returns `None` (e.g., forgetting to `return data`), the framework ignores the return value and retains the original data for further transmission, while outputting a warning-level log. This ensures that a single middleware's mistake does not cause the entire event chain to interrupt.

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
    """Adapter configuration (automatically managed by the framework once declared)"""
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
    ConfigClass = MyConfig  # Declare the config class
    
    # No need to override __init__; the framework automatically handles:
    # - self.sdk, self.logger
    # - self.cfg (type-safe config instance, read in real time)
    # - self.Send, self.Request
    
    async def start(self):
        """Start the adapter (must be implemented)"""
        cfg = self.cfg  # Automatically loaded type-safe config
        pass
    
    async def shutdown(self):
        """Shut down the adapter (must be implemented)"""
        pass
    
    async def call_api(self, endpoint: str, **params):
        """Call the platform API (must be implemented)"""
        pass
```

### Configuration Management

The framework provides declarative configuration management: the configuration structure is defined via dataclasses, and the framework automatically handles loading, validation, and template generation.

#### Single-Account Configuration

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
        cfg = self.cfg  # Type-safe, read in real time
        if not cfg.token:
            raise ValueError("Token not configured")
        await self._connect(cfg.token, proxy=cfg.proxy)
```

#### Multi-Account Configuration

The `BotAccountConfig` base class provides the `enabled` and `name` fields. The vast majority of adapters can automatically obtain the bot_id from the platform protocol or the login response, and inject it into the account configuration during event conversion:

```python
from dataclasses import dataclass, field
from ErisPulse.Core.Bases import BotAccountConfig

# Most adapters: bot_id is obtained automatically at runtime, no configuration needed
@dataclass
class MyBotConfig(BotAccountConfig):
    token: str = field(default="", metadata={
        "description": {"i18n": "my_adapter.bot_token", "default": "Token"},
        "required": True,
    })

# If bot_id cannot be obtained at login, you can have the user fill it in via configuration
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

#### metadata Conventions

Field metadata serves both TOML comment generation and WebUI form rendering:

```python
metadata = {
    "description": str | dict,  # Field description (supports i18n)
    "required": bool,         # Whether required (validation + WebUI required marker)
    "secret": bool,           # Whether sensitive (shown as *** in WebUI, masked in logs)
    "example": bool,          # No-persist flag: not written to config.toml (excluded from
                              # defaults/templates); only rendered into config.full.example; the
                              # schema carries an "example": true marker; the CLI config wizard
                              # skips it by default; persists normally once set manually by the user
    "min": number, "max": number,  # Numeric range validation
    "ui": {                   # WebUI control config (old name "webui" still compatible)
        "widget": str,        # Widget type: "text" | "switch" | "select" | "number" | "password"
        "group": str,         # Group: "basic" | "advanced" | "connection", etc.
        "order": int,         # Sort weight (smaller comes first)
        "options": list,      # Options for the select widget [{label, value}]; label supports i18n
        "placeholder": str | dict,  # Input placeholder (supports i18n)
    },
    "extra": dict,            # Extra extension fields (passed through to the schema)
}
```

All user-visible text fields support i18n, uniformly using the `{"i18n": "key", "default": "text"}` format; plain strings are passed through as-is (backward compatible). Supported i18n fields:

| Field | Location | Description |
|------|------|------|
| `description` | field metadata | Field description |
| `options[].label` | `ui.options` | Select widget option labels |
| `placeholder` | `ui.placeholder` | Input placeholder |
| `group_labels` | `_schema_meta` | Group display names (Dashboard section titles) |

When using i18n, translation keys must be registered with the i18n system in advance (see the [i18n documentation](../../advanced/i18n.md#配置字段多语言) for details).

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
                {"label": "Plain string label", "value": "b"},  # Plain strings are passed through as-is
            ],
        },
    },
)
```

**group_labels** example (declared after the config class is defined):

```python
MyConfig._schema_meta = {
    "group_labels": {
        "basic": {"i18n": "my_adapter.group.basic", "default": "Basic Settings"},
        "advanced": {"i18n": "my_adapter.group.advanced", "default": "Advanced Settings"},
    }
}
```

The framework's `resolve_config_schema()` automatically resolves the i18n keys of all the fields above according to the current language; `get_config_schema()` passes the i18n dictionaries through as-is, leaving resolution to the frontend.

#### Automatic Field Description Generation from docstring (v2.8.0+)

For fields without a `description` declared in metadata, the framework automatically extracts the field description from the config class docstring as a fallback. Two common styles are supported (and can be mixed):

```python
@dataclass
class MyConfig(BaseConfig):
    """
    MyAdapter configuration

    :ivar endpoint: Platform API address        # reST style
    :ivar timeout: Request timeout in seconds
    """

    endpoint: str = "https://api.example.com"   # No metadata description → comment/description taken from docstring
    timeout: int = 30

    # Google style is also supported (Attributes: section):
    # Attributes:
    #     endpoint: Platform API address
```

Priority: **metadata description > docstring field description > empty**. Descriptions in i18n dictionary form are unaffected (they always take precedence).

#### Nested Configuration (v2.8.0+)

When a field's type is a nested dataclass, the framework handles it recursively: the schema carries it via a `"type": "table"` + `"fields"` subtree (rendered by the WebUI as a collapsible nested group), the TOML template renders it as a `[subtable]` section, and defaults / population / validation / i18n resolution all apply recursively.

```python
@dataclass
class RetryConfig(BaseConfig):
    """Retry strategy

    :ivar max_retries: Maximum retry count
    """
    max_retries: int = 3
    backoff: float = 0.5

@dataclass
class MyConfig(BaseConfig):
    """MyAdapter configuration"""
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

> For nested types, direct type annotations are recommended. String annotations (e.g., in deferred-evaluation scenarios) must ensure that the type can be resolved by name from the config class's module globals, the enclosing-class namespaces referenced by `__qualname__`, or class attributes.

#### Non-Persistent `example` Fields (v2.8.0+)

```python
gc_interval: int = field(default=300, metadata={"example": True})
```

Fields with `example: True`:

- Are not written to config.toml (excluded from both adapter/module config templates and defaults; code defaults apply at runtime)
- Are only rendered into the project's `config.full.example` (for user reference; manually copy into config.toml as needed)
- Carry an `"example": true` marker in the schema (the panel can decide its own display strategy); skipped by default by the CLI config wizard
- Persist normally and hot-update normally once the user sets this key manually (explicit user intent takes precedence)

Suitable for advanced configuration items that are "cumbersome and rarely touched", keeping the user's config.toml minimal.

> ⚠️ `_schema_meta` is class-level metadata (not a configuration field). If declared inside the dataclass body, it must carry a `ClassVar` annotation (`_schema_meta: ClassVar[dict] = {...}`), otherwise it will be treated as a regular field by the dataclass. The framework already defensively excludes underscore-prefixed fields (they do not enter any schema / template / defaults / validation output), but a standards-compliant declaration is still recommended.

### Declarative Translation Keys (v2.7.0+)

Adapters can declare translation keys centrally via the nested `I18nClass`, just as they declare `ConfigClass`. During the `__init__` phase (before config template generation), the framework automatically registers all declared translation keys, ensuring that the i18n keys referenced in configuration descriptions are available when templates are generated.

```python
from ErisPulse.Core.Bases import BaseAdapter, BaseI18n, I18nKey

class MyAdapter(BaseAdapter):
    class I18nClass(BaseI18n):
        endpoint: I18nKey = I18nKey(
            default="API Endpoint",
            zh_CN="API address",
            zh_TW="API address",
            en="API Endpoint",
            ja="APIアドレス",
            ru="API адрес",
        )
        token: I18nKey = I18nKey(
            default="Platform Token",
            zh_CN="Platform Token",
            zh_TW="Platform Token",
            en="Platform Token",
            ja="プラットフォームトークン",
            ru="Токен платформы",
        )
```

> ``I18nKey.default`` is **language-independent fallback text** and is not registered to any language.
> To make a translation take effect, you must explicitly pass at least one language parameter.

For detailed usage (key path rules, explicit key parameters, etc.), see the [i18n documentation](../../advanced/i18n.md#推荐写法通过-i18nclass-声明翻译键-v270).

### Declarative Event Extension Methods (v2.7.0+)

Adapters can use `EventMixin` to centrally declare platform-specific event extension methods, which the framework automatically registers to the current platform.

```python
from ErisPulse.Core import BaseAdapter

class MyAdapter(BaseAdapter):
    class EventMixin:
        def get_chat_name(self):
            """Get the chat name"""
            return self.get("myplatform_raw", {}).get("chat", {}).get("name", "")

        def is_official_message(self):
            """Check whether the message is official"""
            raw = self.get("myplatform_raw", {})
            return raw.get("sender", {}).get("is_official", False)
```

After registration, event objects can call these methods directly:

```python
@message.on_group_message()
async def handler(event):
    if event.is_official_message():
        chat_name = event.get_chat_name()
        await event.reply(f"[{chat_name}] Official message received")
```

> An adapter's event extension methods are registered to its own platform (``self._platform``).
> If a module needs cross-platform event extensions, use the original ``register_event_mixin()`` API.

#### Account Resolution

When implementing `call_api`, the adapter needs to resolve the account identifier into a concrete account configuration. The framework passes the account binding (the result of `Using()` or automatic binding along the event chain) into `call_api` via the standard field `account_id`, and automatically adapts to how the adapter actually consumes it—choose any of the three consumption forms; the framework detects them by signature parameter names and in-body constants, regardless of parameter position:

```python
# Form 1 (recommended): declare the standard name in the signature
async def call_api(self, endpoint: str, account_id: str | None = None, **params):
    name, account = self._resolve_account(account_id)
    # name: account name, account: config instance

# Form 2 (legacy compatibility): old name _account_id; the framework automatically rewrites account_id to the old name when dispatching
async def call_api(self, endpoint: str, _account_id: str | None = None, **params):
    name, account = self._resolve_account(_account_id)

# Form 3: extracted from params inside the function body (recognized via constant detection)
async def call_api(self, endpoint: str, **params):
    account_id = params.pop("account_id", None)
    name, account = self._resolve_account(account_id)
```

> When the adapter does not consume the account field, the framework strips that field (to prevent it from leaking into platform parameters) and emits a WARNING once; single-account adapters may skip consuming it (resolution falls back to the first enabled account).

Resolution strategy: account name match → `bot_id` field match → other str field match → first enabled account.

**Runtime identification and persistence** (2.12+): the adapter calls `self.update_bot_id(account_name, bot_id)` when a connection is established / an event arrives — the framework maintains a bot_id → account registry (first priority in the resolution chain) and, when the value changes, writes `accounts.<account name>.bot_id` into the config storage: after a restart, the rebuilt account instance already carries its bot_id, and resolution for scenarios such as the second account no longer depends on backfilling from account activity (eliminating the restart window).

#### Configuration Hot Reload

Subclasses can override `on_config_update()` to respond to configuration changes:

```python
class MyAdapter(BaseAdapter):
    ConfigClass = MyConfig
    
    def on_config_update(self, old_config, new_config):
        if old_config.token != new_config.token:
            self.logger.info("Token updated, will reconnect")
```

### Initialization Process

The framework automatically completes the following within `BaseAdapter.__init__(self, sdk=None)`:

1. **SDK reference**: sets `self.sdk`, `self.logger`
2. **Send/Request factories**: creates `self.Send` and `self.Request`
3. **Config template**: if `ConfigClass` is declared, a default config template is generated automatically (first time only)
4. **Account template**: if `AccountConfigClass` is declared, a default account template is generated automatically (first time only)
5. **EventMixin registration**: if `EventMixin` is declared, it is registered automatically after `AdapterManager` injects the platform name

Configuration is read in real time through `self.cfg` / `self.accounts` (each access reads the latest value from the config storage). `self.config` remains available as a compatibility alias for `self.cfg`.

Most adapters do not need to override `__init__`. If custom initialization is needed:

```python
class MyAdapter(BaseAdapter):
    ConfigClass = MyConfig
    
    def __init__(self, sdk=None):
        super().__init__(sdk)  # Pass in the sdk
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

`Send` class automatically sets the following attributes when called:

| Attribute | Description | Setting Method |
|-----|------|---------|
| `_target_id` | Target ID | `To(id)` or `To(type, id)` |
| `_target_type` | Target Type | `To(type, id)` |
| `_target_to` | Simplified Target ID | `To(id)` |
| `_account_id` | Sending Account ID | `Using(account_id)` |
| `_adapter` | Adapter Instance | Automatically set |
| `_at_user_ids` | @ User List | `At(user_id)` |
| `_reply_message_id` | ID of the replied message | `Reply(message_id)` |
| `_at_all` | Whether to @ all | `AtAll()` |

> **Recommended**: Use `self.send_context` property to get `target_type`, `target_id`, `account_id` at once, which is clearer than directly accessing instance variables.

### Framework Helper Methods

| Method/Property | Description |
|-----------|------|
| `self._apply_modifiers(message)` | Merge At/AtAll/Reply modifier states into the message segment list |
| `self.send_context` | Return `{target_type, target_id, account_id}` dictionary; `account_id` defaults to the account that triggered the event distribution chain if not explicitly specified |

### Basic Methods

Adapters only need to implement `Raw_ob12`, standard methods (Text/Image/Voice/Video/File) are inherited from the `SendDSL` base class and default to delegating to it:

```python
class Send(BaseAdapter.Send):
    def Raw_ob12(self, message, **kwargs):
        """Must implement: OneBot12 message segment → platform API"""
        async def _do_send():
            segments = self._apply_modifiers(message)
            return await self._adapter.call_api(
                endpoint="/send_message",
                message=segments,
                **self.send_context,
                **kwargs
            )
        return asyncio.create_task(_do_send())

    # Text/Image/Voice/Video/File are inherited from the base class and automatically delegate to Raw_ob12, no need to reimplement
    # If platform-specific logic is needed, override individual methods:
    # def Text(self, text: str):
    #     return self.Raw_ob12([{"type": "text", "data": {"text": text}}])
```

### Chained Modifier Methods

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
    "id": "Unique Event Identifier",          # Same event must have the same id for the same account (framework uses this for deduplication)
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

> Event `id` must include account dimension: the same event must have the same `id` for the same account, and for different accounts receiving the same group message, the `id` must be different (e.g., `f"{self.user_id}:{post_type}:{message_id}"`).

### Cross-Account Duplicate Handling (Framework Injected Fields)

For multi-account adapters, the same physical message arrives through multiple accounts in the same group/session. The framework automatically performs content-level association (same platform + same session + same sender + same `alt_message` within a short window) when `ErisPulse.framework.cross_account_policy != "off"`, and adapters do not need to participate:

- `mark`: Subsequent copies inject the top-level field `"multi_receipt": {"event_id": first accepted event id, "self_id": first accepted account}` and proceed with distribution as usual, allowing modules to decide based on this field
- `drop`: Subsequent copies are dropped directly at the distribution entry

`multi_receipt` is an optional field injected by the framework; adapters do not produce or consume it; the policy defaults to `off`, and the event structure is consistent with the existing contract.

#### Three-tier Deduplication Mechanism Division of Labor

| Mechanism | Configuration | What to Intercept | Determination Basis |
|------|------|----------|----------|
| Event Idempotency Deduplication | `ErisPulse.framework.event_dedupe` (default on) | Repeated events from the same connection (same event id) | Event `id` |
| Self-echo Filtering | `ErisPulse.event.message.ignore_self` (default on) | Messages received from the account itself (sender == receiving account) | `self.user_id` vs `user_id` |
| Cross-Account Duplicate Handling | `ErisPulse.framework.cross_account_policy` (default `off`, `drop` enabled) | **Physical message received by other accounts**—when multiple accounts are in the same group, bot A speaks, bot B also receives a copy, resulting in duplicate messages | Content-level association (same platform + same session + same sender + same content, short window), key does not include self_id |

**Typical Scenario - Multi-Account Group Repetition**: bot A speaks, and other accounts (bot B) in the same group also receive a copy, causing repetition modules to see the same content twice. Enabling `cross_account_policy = "drop"` causes subsequent account copies to be dropped at the distribution entry, ensuring that any module sees it at most once.

The semantics of `ignore_self` are orthogonal, and the combination of both determines the number of visible times:

| Combination | Repetition module sees bot A's message |
|------|--------------------------|
| `drop` + `ignore_self = true` (default) | 0 or 1 times (the first copy, if received from A's own connection, is blocked by `ignore_self`) — **never 2 times** |
| `drop` + `ignore_self = false` | Exactly 1 time |

> It is not recommended to extend the semantics of `ignore_self` to "exclude all local accounts": this determination depends on the `self.user_id` of the event being received (the binding is invalid during the window before establishment), and cross-account association is content-level determination, independent of self information; and "receiving by account" is an existing dependency of cross-account logging/synchronization modules, narrowing the semantics is an implicit destruction. Cross-account deduplication is left to `cross_account_policy`.

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

Adapters with client mode (WebSocket client, HTTP polling, etc.) need to start a persistent connection loop in `start()`. The framework supports two ways, **both correct, but only one can be chosen**:

**Approach 1: spawn-return style (Recommended)**—use `spawn_client_loop()` to schedule the loop as a background task belonging to the platform, and `start()` returns immediately:

```python
class MyAdapter(BaseAdapter):
    async def start(self):
        # The loop task belongs to self._platform: framework automatically cancels it during shutdown
        self.spawn_client_loop(self._connect_loop())
        # start ends here — "startup is successful", connection failures are handled within the loop

    async def _connect_loop(self):
        while True:
            try:
                await self._connect_and_receive()   # Disconnect throws exception → below backoff
            except asyncio.CancelledError:
                raise
            except Exception:
                await asyncio.sleep(5)              # Loop handles backoff and reconnect internally
```

**Approach 2: Persistent style**—`start()` directly `await` the connection loop, which never returns:

```python
class MyAdapter(BaseAdapter):
    async def start(self):
        await self._connect_loop()   # Persistent and never returns; loop throws exception = start fails
```

Differences and common points between the two approaches:

| | spawn-return style | Persistent style |
|---|---|---|
| `start()` return timing | Returns immediately after launching the loop | Returns when the connection loop exits/fails (framework retries according to backoff strategy) |
| Connection failure handling | Loop handles failures internally | Exception thrown is passed to the framework's retry chain |
| Applicable scenarios | Need to return startup confirmation quickly (multiple connections, registering routes and then launching other tasks) | "Connection is startup" semantics for simple implementation |

`spawn_client_loop(coro, *, name="client_loop")` is the dispatch entry for approach one: the task is registered according to `self._platform`, and the adapter's `shutdown()` automatically cancels it according to the owner, without needing to manage task handles itself; exceptions not caught in the loop are automatically logged (expected disconnection and reconnection should be caught within the loop).

> **The only incorrect way is to mix them**: spawning and then awaiting the same loop—this causes `start()` to lose its immediate return semantics, and the task cancellation path becomes unpredictable.

### Semi-finished Base Classes for Connection Modes

In addition to the two approaches in the previous section, the most common connection modes have direct "semi-finished" base classes provided by the framework (`ErisPulse.Core.Bases.adapter_patterns`, root package can be directly imported): the lifecycle orchestration of `start` / `shutdown` is fully handled by the base class, and the subclass only implements business hooks.

#### PollingAdapter (HTTP Polling Type)

Suitable for platforms that "periodically pull events from the client" (Telegram getUpdates type). The base class uses the spawn-return style to launch a persistent polling loop, automatically logs failures and backoffs exponentially (base 1 second, maximum 60 seconds, resets to zero on success; constants `POLLING_ADAPTER_BACKOFF_BASE_SECS` / `POLLING_ADAPTER_BACKOFF_MAX_SECS` can be adjusted in `Core/constants.py`):

```python
from ErisPulse import PollingAdapter

class MyAdapter(PollingAdapter):
    # Polling interval defaults to 5 seconds; if ConfigClass declares poll_interval field, use configuration value (hot update takes effect)
    poll_interval = 5.0

    async def fetch_events(self):
        """Pull a batch of platform native events (exceptions handled by base class, no need for try/except)"""
        resp = await self.sdk.client.get(f"{self.cfg.endpoint}/getUpdates")
        data = await resp.json()
        return data.get("result", [])

    def convert_one(self, raw):
        """Convert a single native event to OneBot12; return None to skip"""
        return self.converter.convert(raw)

    async def call_api(self, endpoint: str, **params):
        ...  # Same as ordinary adapter
```

Minimum implementation: `fetch_events` / `convert_one` / `call_api`. `start()` launches the loop and returns immediately; `shutdown()` does not require subclass handling (the polling loop is automatically canceled according to owner).

#### WebhookAdapter (HTTP Callback Type)

Suitable for platforms that "platform actively pushes callbacks". The base class's `start()` registers the receiving route on the framework router (final path `/{platform}/webhook`, POST method), registered in `owner_scope`—the adapter automatically cleans up when unloaded, no need to manually deregister:

```python
from ErisPulse import WebhookAdapter

class MyAdapter(WebhookAdapter):
    def verify_request(self, request) -> bool:
        """Optional hook: callback verification (default allows, return False to deny by base class)"""
        cfg = self.cfg
        if not cfg.token:
            return True
        auth = request.headers.get("authorization", "")
        return auth == f"Bearer {cfg.token}"

    def convert(self, payload):
        """Convert callback payload to OneBot12; return None to skip"""
        return self.converter.convert(payload)

    async def call_api(self, endpoint: str, **params):
        ...  # Same as ordinary adapter
```

Minimum implementation: `convert` / `call_api` (`verify_request` optional). The callback address is queried via `sdk.adapter.get_connection_info(platform)` and filled into the platform backend; requests with failed verification return 403, payload parsing failures return 400, normal returns `{"status": "ok"}`.

#### How to Choose the Three Modes

| Platform Protocol | Inherit | Scaffolding |
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

> Pure callback-type platforms do not need to write the above registration/validation/cleanup orchestration—simply inherit the [`WebhookAdapter` semi-finished base class](#connection-mode-semi-finished-base-classes) and implement only `convert` (optionally override `verify_request`).

> **Route information query**: The routes registered by adapters (HTTP, WebSocket, SSE) can be queried via `sdk.adapter.get_connection_info(platform)` and `sdk.router.get_module_urls(module_name)`, which include `base_url` + path. See [Getting Started with Adapter Development - Connection Information and Route Discovery](getting-started.md#9-connection-information-and-route-discovery) and [SSE Support](getting-started.md#10-sse-server-sent-events-support).

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

### Manually Constructed Response (Old Style Still Compatible)

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
    
    async def call_api(self, endpoint: str, account_id: str | None = None, **params):
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

# Via event's self.user_id (recommended, most universal)
await my_adapter.Send.Using(event["self"]["user_id"]).To("user", "123").Text("Hello")

# Via account name
await my_adapter.Send.Using("account1").To("user", "123").Text("Hello")
```

### Relationship Between Event Account Identifier and Using

The framework's event reply mechanism automatically extracts the account identifier from the event's `self` field (account_id takes precedence, otherwise user_id), injecting it into `Using`. Adapter developers must ensure that the Converter produces account identifiers that match the account configuration (account name or `bot_id` fields).

**Framework Injection Behavior**:

```python
# Framework extracts account identifier logic (account_id precedence, user_id fallback)
account = self.get("self", {}).get("account_id", "") or self.get("self", {}).get("user_id", "")

# Inject Using only if identifier is non-empty
if account:
    send_chain = send_chain.Using(account)
```

> **Key Point**: Even if the adapter only uses a single Bot configuration, as long as the Converter correctly sets the account identifier, the framework will inject it into `Using`. The adapter must ensure that this identifier matches the account name or `bot_id` fields in the `AccountConfigClass` to resolve to the correct account. If the identifier is empty, the framework does not inject `Using`, and sending proceeds without specifying an account—falling back to the first enabled account.

If the explicitly passed `account_id` cannot be resolved, the framework logs a WARNING and falls back to the first enabled account; the WARNING includes `platform` / `account_id` / `account` to locate the source of events not belonging to any account.

**Automatic Binding in Event Dispatch Chain**: When calling send methods within the event processing chain, **no explicit `Using()` is needed**—the framework injects the account identifier from the triggering event into the call context at the event dispatch entry, and `Send` / `Api` / `Request` chains use this as a fallback binding if no account is explicitly specified (explicit `Using()` always takes precedence; scenarios like timers / startup tasks without event context maintain default account semantics). Automatic binding in the event chain requires ErisPulse **2.12+**.

> The `self.user_id` / `self.account_id` substitution output contract for events is detailed in [Event Conversion Standard](../../standards/event-conversion.md); the constant presence of this field is the premise for account resolution fallback semantics—missing it falls back to the first enabled account, and in multi-account scenarios, it means "sent from the default account."

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

> **Backward Compatibility**: Old adapter code using `aiohttp.ClientSession` is unaffected and can still catch `aiohttp.ClientError`. Both approaches can coexist. New code is recommended to use `sdk.client` with the ErisPulse exception system.

## Bot Status Management

The `AdapterManager` includes a built-in Bot status tracking system, automatically maintaining online status, active time, and metadata for all registered Bots.

### Automatic Discovery Mechanism

When an adapter emits an event via `adapter.emit()`, the framework automatically checks for the `self` field in the event:

- **Meta Events**: Perform corresponding operations based on `detail_type` (register on connect, mark offline on disconnect, update active time on heartbeat)
- **Regular Events** (message/notice/request): Automatically discover Bots and update active time

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

Sending methods (`emit_meta()` for single-line sending, heartbeat events and manually constructed formats) are detailed in [Adapter Best Practices - Bot Status Management and Meta Events](best-practices.md#bot-status-management-and-meta-events).

### `self` Field Extended Information

Besides the required `platform` and `user_id` fields, `self` can also include the following optional fields:

| Field | Description |
|---|---|
| `user_name` | Bot username |
| `nickname` | Bot nickname |
| `avatar` | Bot avatar URL |
| `account_id` | Multi-account identifier |

### Bot Status Query

Query APIs (`get_bot_info()` / `list_bots()` / `is_bot_online()` / `get_status_summary()`) are detailed in [Adapter System API - Bot Status Management](../../api-reference/adapter-system.md#bot-status-management).

### Listening to Bot Lifecycle

The `adapter.bot.online` / `adapter.bot.offline` lifecycle event tables and listening examples are detailed in [Adapter System API - Bot Status Management](../../api-reference/adapter-system.md#bot-status-management).

## Related Documentation

### Implementation-Level Details

- [SendDSL Detailed Explanation](send-dsl.md) - Learn message sending
- [Adapter Best Practices](best-practices.md) - Develop high-quality adapters

### Reviewing the Initial Steps

- [Getting Started with Adapter Development](getting-started.md) - Create your first adapter