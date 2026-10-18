# Inter-Module Communication

> [!TIP]
> **When to read this**: When you need cross-module calls (RPC), service contracts, directed events, or cold-start replay. Skip if not needed, as it does not affect other features.

> [!NOTE]
> This chapter requires ErisPulse **2.8.0+**.

ErisPulse has a **three-layer communication model** between modules, arranged as "point-to-point → directed → broadcast":

| Layer | API | Semantics | Typical Scenario |
|---|---|---|---|
| **RPC** | `await sdk.module.call("Chat", "get_history", ...)` | Point-to-point request-response with contract / audit / timeout | Invoking another module's capability (e.g., check history, translate, refund) |
| **Directed Events** | `await lifecycle.emit("message_received", {...}, to="Chat")` | Only delivered to lifecycle hooks registered by the specified module | Upstream state change notification to downstream ("new message received") |
| **Broadcast** | `await lifecycle.emit("config.updated", {...})` | Framework-wide visible lifecycle event | Hot configuration updates, module up/down |

{!--< tips >!--}
Selection mnemonic: **Use `call` for return values, `emit(..., to=...)` for notifying a specific module's hooks, and `emit(...)` for notifying everyone.** 
{!--< /tips >!--}

## RPC: module.call

```python
result = await sdk.module.call("Chat", "get_history", session_id, n=20)
```

Difference from direct attribute access `sdk.module.Chat.get_history(...)` (unchanged):

| | `module.call()` | Direct attribute access |
|---|---|---|
| Target not registered / enabled | Throws `ModuleNotAvailableError` | Throws `AttributeError` |
| Lazy-loaded module | **Automatically wakes up** (event-driven modules use activation lock) | Async initialization throws RuntimeError |
| `current_owner` | Attributed to the **target module** (its internal wait_reply / send / logs are correctly attributed) | Maintains caller |
| Timeout | Default 30 seconds (`timeout=` overrides, None means no timeout) | None |
| Scope audit | Caller passes through outbound gate `actions.<caller>.call` | None |
| Contract validation | `meta.services` whitelist | None |

### Exception Hierarchy

```
ModuleError                      # Base class for module system exceptions
└── ModuleCallError              # Base class for cross-module calls (includes module / method attributes)
    ├── ModuleNotAvailableError  # Target not registered / enabled / activation failed
    ├── ServiceNotProvidedError  # Method not in services whitelist / private method / does not exist
    └── ModuleCallTimeoutError   # Coroutine method timeout
```

All are part of the `ErisPulseError` hierarchy, and can be caught via `from ErisPulse.Core import ModuleCallError`.

## Service Contract: meta.services

The service provider declares the whitelist of services offered externally in `get_meta()` (symmetrical to the `commands` field):

```python
from ErisPulse.Core.Bases import BaseModule, ModuleMeta

class ChatModule(BaseModule):
    @staticmethod
    def get_meta() -> ModuleMeta:
        return ModuleMeta(
            name="Chat",
            services=[
                "get_history",                                       # Simple form
                {"name": "translate", "description": "Translate text into a specified language"},  # With description
            ],
        )

    async def get_history(self, session_id, n=20): ...
    async def translate(self, text, target_lang): ...
    def _internal_helper(self): ...   # Methods with leading underscore are always prohibited from external calls
```

**By default, services are invisible to developers**:

- If `services` is not declared → all **public** methods are naturally callable via `module.call()` (consistent with direct attribute access),
  no declaration is required
- After declaration → the scope is restricted to the whitelist, calling outside the whitelist raises `ServiceNotProvidedError`—used to mark
  "these methods are the ones promised externally"
- The main control authority lies with the user: `scope.actions` configuration determines "who can call whom" (see audit below),
  the module author's `services` is only a service declaration, and the two layers are independent

**Service Descriptions**: Provide human- or AI-readable descriptions for each service—leave empty if not needed,
the description is automatically taken from the **first line of the method's docstring** (the framework already requires docstring style):

```python
async def translate(self, text, target_lang):
    """Translate text into a specified language"""    # ← This line automatically becomes the service description
    ...
```

**Parameter Hints**: The caller (especially AI agents) needs to know the meaning of each parameter. Leave empty if not needed,
hints are automatically taken from the **`:param:` lines** in the method's docstring:

```python
async def render_card(self, html, width=800, height=0):
    """Render HTML into an image file

    :param html: HTML text to render          ← Automatically becomes the parameter hint
    :param width: Canvas width in pixels, 0 for adaptive to content
    :param height: Canvas height in pixels, 0 for adaptive to content
    """
```

For fine-grained control (overriding docstring or multi-language support), use the dict form to declare `description` and `parameters`
(both support i18n dictionaries; `parameters` are merged with the docstring **by parameter**, explicit declaration within a single parameter takes precedence,
parameters declared that do not exist in the signature are filtered):

```python
services=[
    {"name": "translate", "description": "Translate text into a specified language"},
    {"name": "summarize", "description": {"i18n": "Chat.meta.svc.summarize", "default": "Summarize conversation"}},
    {
        "name": "render_card",
        "description": "Render HTML into an image file",
        "parameters": {"html": "HTML text", "width": "Width in pixels, 0 for adaptive"},
    },
]
```

## Service Directory: services()

```python
sdk.module.services()
# {'Chat': [{'name': 'get_history', 'signature': '(session_id, n=20)',
#            'description': 'Translate text into the specified language',
#            'parameters': {'session_id': 'Session ID', 'n': 'Number of entries to return'}}]}

sdk.module.services("Chat")   # Query only a specific module
```

- Only modules that explicitly declare `meta.services` are listed (modules without declaration do not appear in the directory)
- Each service includes a method signature string (extracted via `inspect.signature`), description text, and parameter hints
- **Lazily loaded modules are also included in the directory** (service discovery occurs before loading) — the caller can decide whether to `call()` to activate the target module
- Modules are also included in the topology: each entry in `sdk.module.get_topology()` contains a `services` field

{!--< tips >!--}
**MCP Roadmap**: The service directory (name + signature + description + parameter hints) naturally forms the shape of an MCP tool — each service becomes ``{"name", "description", "parameters"}``. In the future, the framework could directly expose ``services()`` as an MCP server endpoint, allowing AI to discover and invoke module capabilities; ``scope.actions.call`` auditing naturally becomes a security gate for AI calls.
{!--< /tips >!--}

## Outbound Audit: Who Can Call Whom

Each `module.call()` passes through the scope outbound gate as the **caller module**:

```toml
[ErisPulse.scope.actions.CallerModule.call]
deny = ["Chat.get_history"]        # Deny CallerModule from calling Chat's get_history
# allow = ["Chat.get_*"]           # Or whitelist: only allow calling Chat's get-* services
```

- `name` format is `<target module>.<method name>`, supporting exact / glob / `re:` regex
- Framework-level calls (without owner context, e.g., startup scripts) are not subject to audit constraints
- Denied calls throw `ModuleCallError` (TRACE log `core.module.call_denied`)

See [Scope (scope)](scope.md) for configuration details on the outbound dimension.

## Directed Events: lifecycle.emit with to parameter

Lifecycle events support directed propagation: when `to` specifies the target owner (owner), the event is only delivered to hooks registered by that owner (modules automatically register hooks in `on_load` and record the owner). Other modules and wildcard `*` handlers do not receive the event.

```python
from ErisPulse.Core.lifecycle import lifecycle

# Emitter: event is only delivered to hooks registered by Chat module
await lifecycle.emit("message_received", {"text": "hi", "from": "u1"}, to="Chat")

# Subscriber (inside Chat module): register same-name hook, owner is automatically recorded during registration
@lifecycle.on("message_received")
async def on_message_received(data): ...

@lifecycle.on("message")          # Point prefix also works (filtered by owner)
async def on_any(data): ...
```

Semantic details:

- If the target owner has no registered hooks → the event is **silently discarded** (does not send to non-existent places), use `lifecycle.has_handlers("message_received")` to probe in advance
- When `data` is a dict, it automatically carries `_trace_id` (without overriding existing values), integrating with full-chain tracing
- Broadcast and directed events share the same hook registration: `emit(...)` without `to` broadcasts to the entire framework, while with `to` the same event is only visible to the target module
- `emit_sync` / `submit_event` (compatibility API) also support `to=` parameter

> [!NOTE]
> Directed events are lightweight notifications, **do not perform target validation or lazy activation**; for target existence validation, contract audit, or return values, switch to [RPC: module.call](#rpcmodulecall).

## Lazy Loading and Invocation

`module.call()` transparently activates lazy-loaded modules:

- Event-driven lazy modules (`activate_on` declared) → Use activation lock `_activate()`, stub automatically unregisters after activation
- Regular lazy modules → Synchronous initialization or standard loading path (idempotent)
- Activation failure → `ModuleNotAvailableError`

That is: **the caller does not need to care whether the target module is loaded** and does not need to wait for it to be activated.

Directed events (`lifecycle.emit(..., to=...)`) do not perform lazy activation—target not loaded means no hooks, event silently discarded; use `module.call()` if you need to ensure delivery.

## Cold Start Replay

A newly installed / restarted module missed some chat messages—`get_load_strategy(replay=...)` allows the framework to replay the most recent messages from the session inbox to the module itself after it is ready:

```python
from ErisPulse.loaders import ModuleLoadStrategy

class MyAIModule(BaseModule):
    @staticmethod
    def get_load_strategy():
        return ModuleLoadStrategy(
            lazy_load=False,
            priority=100,
            replay="5m",        # Replay the last 5 minutes ("1h" / "300" seconds are also valid)
        )

    async def on_load(self, event):
        @message.on_message()
        async def handle(e):
            if e.get("replayed"):
                # Synthetic event: only supplement context, do not trigger side effects like sending
                ...
```

Semantic details:

- The data source is the [session inbox](interaction.md#session-inbox-eventhistory) (`sdk.transcript.recent()`), executed in the background after module loading, without blocking startup
- Synthetic events carry the `replayed: True` flag, along with complete `platform / detail_type / user_id / alt_message`, and are **only distributed to the module's own handlers**—other modules are unaffected by the replay
- If the inbox is not enabled / no records exist / the replay duration is invalid (`replay_invalid` warning), it is silently skipped

## Event Idempotency Deduplication

After platform websocket reconnection, the same event (with the same `event["id"]`) is often re-sent—event distribution entry deduplicates by id (capacity 4096), so the same id event is only distributed once.

```toml
[ErisPulse.framework]
event_dedupe = true   # Default on; turn off for test environments with fixed id synthetic events
```

The deduplication cache is automatically reset when adapters **register** (start of new connection lifecycle).

## Related Documentation

- [Interaction Session System](interaction.md) - wait_reply / timers / multi-wait / session mutual exclusion
- [Scope (scope)](scope.md) - complete configuration for outbound dimension audit
- [Ownership (owner) System](ownership.md) - how owner context traverses cross-module calls
- [Lazy Loading System](lazy-loading.md) - lazy loading and event-driven lazy activation (`activate_on`)
- [Lifecycle Management](lifecycle.md) - mechanism of the broadcast layer event bus