# Inter-Module Communication

> [!NOTE]  
> This chapter requires ErisPulse **2.8.0+**.

ErisPulse's modules have a **three-layer communication model**, ordered as "point-to-point → directed → broadcast":

| Layer | API | Semantics | Typical Scenario |
|---|---|---|---|
| **RPC** | `await sdk.module.call("Chat", "get_history", ...)` | Point-to-point request-response with contract / audit / timeout | Invoking capabilities of another module (e.g., fetching history, translation, refund) |
| **Directed Events** | `await lifecycle.emit("message_received", {...}, to="Chat")` | Distributed only to lifecycle hooks registered by the specified module | Notifying downstream modules of upstream state changes ("a new message was received") |
| **Broadcast** | `await lifecycle.emit("config.updated", {...})` | Framework-wide visible lifecycle events | Hot configuration updates, module up/down events |

{!--< tips >!--}
Selection rule: **Use `call` when you need a return value, use `emit(..., to=...)` when you only want to notify a specific module's hooks, and use `emit(...)` to notify everyone.**  
{!--< /tips >!--}

## RPC: module.call

```python
result = await sdk.module.call("Chat", "get_history", session_id, n=20)
```

Difference from direct attribute access `sdk.module.Chat.get_history(...)` (unchanged):

| | `module.call()` | Direct attribute access |
|---|---|---|
| Target not registered / disabled | Throws `ModuleNotAvailableError` | Throws `AttributeError` |
| Lazy-loaded modules | **Automatically wakes up** (event-driven modules go through activation lock) | Asynchronous initialization throws RuntimeError |
| `current_owner` | Attributed to the **target module** (its internal wait_reply / send / logs are correctly attributed) | Remains the caller |
| Timeout | Default 30 seconds (`timeout=` overrides, None means unlimited) | None |
| Scope audit | Caller goes through the outbound gate `actions.<caller>.call` | None |
| Contract validation | `meta.services` whitelist | None |

### Exception Hierarchy

```
ModuleError                      # Base class for module system exceptions
└── ModuleCallError              # Base class for cross-module calls (includes module / method attributes)
    ├── ModuleNotAvailableError  # Target not registered / disabled / activation failed
    ├── ServiceNotProvidedError  # Method not in services whitelist / private method / does not exist
    └── ModuleCallTimeoutError   # Coroutine method timeout
```

All exceptions are under the `ErisPulseError` hierarchy and can be caught using `from ErisPulse.Core import ModuleCallError`.

## Service Contract: meta.services

Service providers declare a whitelist of publicly available services in `get_meta()` (symmetrical to the `commands` field):

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
    def _internal_helper(self): ...   # Underscore-prefixed methods are always forbidden for external calls
```

**Default behavior is unnoticeable**:

- If `services` is not declared → All **public** methods are naturally callable via `module.call()` (consistent with direct attribute access),  
  no declaration is required
- After declaration → Restrict to the whitelist, calls beyond the list throw `ServiceNotProvidedError`—used to mark  
  "these methods are the ones promised externally"
- The main control authority lies with the user side: `scope.actions` configuration determines "who can call whom" (see audit below),  
  the module author's `services` is only a service declaration, and the two layers are not interchangeable

**Service Descriptions**: Provide human-readable / AI-readable descriptions for each service—no need to write anything if not required,  
the description is automatically taken from the **first line of the method's docstring** (the framework already requires docstring style):

```python
async def translate(self, text, target_lang):
    """Translate text into a specified language"""    # ← This line automatically becomes the service description
    ...
```

For fine-grained control (overriding docstring / multilingual), use dict form to declare `description` (supports i18n dictionary):

```python
services=[
    {"name": "translate", "description": "Translate text into a specified language"},
    {"name": "summarize", "description": {"i18n": "Chat.meta.svc.summarize", "default": "Summarize conversation"}},
]
```

## Service Directory: services()

```python
sdk.module.services()
# {'Chat': [{'name': 'get_history', 'signature': '(session_id, n=20)',
#            'description': 'Translate text into a specified language'}]}

sdk.module.services("Chat")   # Only query a specific module
```

- Only lists modules that explicitly declare `meta.services` (modules not declared do not appear in the directory)
- Each service includes method signature string (extracted via `inspect.signature`) and description text
- Also included in topology: `sdk.module.get_topology()` entries for each module include a `services` field

{!--< tips >!--}
**MCP Roadmap**: The service directory (name + signature + description) is the shape of an MCP tool—  
each service naturally becomes ``{"name", "description", "parameters"}``.  
In the future, the framework can expose ``services()`` directly as an MCP server endpoint, allowing AI to discover and invoke module capabilities;  
``scope.actions.call`` audit naturally becomes the security gate for AI calls.
{!--< /tips >!--}

## Outbound Audit: Who Can Call Whom

Each `module.call()` passes through the scope outbound gate as the **caller module**'s identity:

```toml
[ErisPulse.scope.actions.CallerModule.call]
deny = ["Chat.get_history"]        # Prohibit CallerModule from calling Chat's get_history
# allow = ["Chat.get_*"]           # Or whitelist: only allow calling Chat's get-* services
```

- `name` format is `<target module>.<method name>`, supports exact / glob / `re:` regex
- Framework-level calls (without owner context, e.g., startup scripts) are not subject to audit constraints
- Denied calls throw `ModuleCallError` (TRACE log `core.module.call_denied`)

See [Scope (scope)](scope.md) for configuration details on the outbound dimension.

## Directed Events: lifecycle.emit's to parameter

Lifecycle events support directed propagation: `to` specifies the target owner (owner), and the event is only distributed to hooks registered by that owner (hooks automatically registered by the module in `on_load` are assigned to the module itself),  
other modules and wildcard `*` handlers are not notified.

```python
from ErisPulse.Core.lifecycle import lifecycle

# Emitter: Event is only sent to hooks registered by the Chat module
await lifecycle.emit("message_received", {"text": "hi", "from": "u1"}, to="Chat")

# Subscriber (inside Chat module): Register same-name hook, owner is automatically recorded at registration
@lifecycle.on("message_received")
async def on_message_received(data): ...

@lifecycle.on("message")          # Dot-prefixed parent prefix also works (filtered by owner)
async def on_any(data): ...
```

Semantic details:

- If the target owner has no registered hooks → The event is **silently discarded** (events are not sent to non-existent places),  
  use `lifecycle.has_handlers("message_received")` to probe in advance
- When `data` is a dict, `_trace_id` is automatically added (without overwriting existing values), connecting to full-chain tracing
- Broadcast and directed events share the same hook registration: `emit(...)` without `to` broadcasts to the entire framework,  
  with `to` the same event is only visible to the target module
- `emit_sync` / `submit_event` (compatible API) also support the `to=` parameter

> [!NOTE]  
> Directed events are lightweight notifications, **do not perform target validation or lazy wake-up**;  
> if target existence validation, contract audit, or return values are needed, switch to [RPC: module.call](#rpcmodulecall).

## Lazy Loading and Calls

`module.call()` transparently wakes up lazy-loaded modules:

- Event-driven lazy modules (`activate_on` declared) → Go through the activation lock `_activate()`, stubs are automatically unregistered after activation
- Ordinary lazy modules → Synchronous initialization or regular loading path (idempotent)
- Activation failure → `ModuleNotAvailableError`

That is: **the caller does not need to care if the target module is loaded**, nor does it need to wait for the target module to be awakened.

Directed events (`lifecycle.emit(..., to=...)`) do not perform lazy wake-up—no hooks are present if the target is not loaded,  
the event is silently discarded; use `module.call()` if delivery must be ensured.

## Cold Start Replay

A newly installed / restarted module misses some chat history—`get_load_strategy(replay=...)` allows the framework to replay the module's inbox messages **after the module is ready**:

```python
from ErisPulse.loaders import ModuleLoadStrategy

class MyAIModule(BaseModule):
    @staticmethod
    def get_load_strategy():
        return ModuleLoadStrategy(
            lazy_load=False,
            priority=100,
            replay="5m",        # Replay the last 5 minutes (can also use "1h" / "300" seconds)
        )

    async def on_load(self, event):
        @message.on_message()
        async def handle(e):
            if e.get("replayed"):
                # Synthetic event: only supplement context, do not trigger side effects like sending
                ...
```

Semantic details:

- The data source is the [session inbox](interaction.md#session-inbox-eventhistory) (`sdk.transcript.recent()`),  
  executed in the background after module loading, not blocking startup
- Synthetic events include the `replayed: True` flag, complete `platform / detail_type / user_id / alt_message`,  
  **only distributed to the module's own handlers**—other modules are unaffected by replay
- If the inbox is not enabled / no records exist / the replay duration is invalid (`replay_invalid` warning), it is silently skipped

## Event Idempotency Deduplication

After platform websocket reconnection, the same event (same `event["id"]`) is often resent—distribution entry performs LRU deduplication (capacity 4096),  
so the same id event is only distributed once.

```toml
[ErisPulse.framework]
event_dedupe = true   # Default is enabled; disable for test environments with fixed id synthetic events
```

The deduplication cache is automatically reset when adapters register (start of new connection lifecycle).

## Related Documentation

- [Interaction Session System](interaction.md) - wait_reply / timers / multiplexed waiting / session mutual exclusion
- [Scope (scope)](scope.md) - Complete configuration for outbound dimension audit
- [Ownership (owner) System](ownership.md) - How owner context permeates across module calls
- [Lazy Loading System](lazy-loading.md) - Lazy loading and event-driven lazy activation (`activate_on`)
- [Lifecycle Management](lifecycle.md) - Mechanism of the broadcast layer event bus