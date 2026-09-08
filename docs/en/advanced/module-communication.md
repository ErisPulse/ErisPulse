# Inter-Module Communication

> [!NOTE]
> This chapter requires ErisPulse **2.8.0+**.

ErisPulse has a **three-layer communication model** between modules, ordered as "point-to-point → directed → broadcast":

| Layer | API | Semantics | Typical Scenarios |
|---|---|---|---|
| **RPC** | `await sdk.module.call("Chat", "get_history", ...)` | Point-to-point request-response, with contract / audit / timeout | Invoking another module's capability (e.g., check history, translate, refund) |
| **Directed Events** | `await sdk.module.emit_to("Chat", "message_received", {...})` | Notification sent to a specific module | Upstream state change notification to downstream (e.g., "new message received") |
| **Broadcast** | `await lifecycle.emit("config.updated", {...})` | Framework-wide lifecycle events | Hot configuration updates, module up/down events |

{!--< tips >!--}
Selection mnemonic: **Use `call` when you need a return value, `emit_to` to notify a single module, and `lifecycle` to notify everyone.** 
{!--< /tips >!--}

## RPC: module.call

```python
result = await sdk.module.call("Chat", "get_history", session_id, n=20)
```

Differences between `module.call()` and direct attribute access `sdk.module.Chat.get_history(...)` (which remains unchanged):

| | `module.call()` | Direct attribute access |
|---|---|---|
| Target not registered / disabled | Raises `ModuleNotAvailableError` | Raises `AttributeError` |
| Lazy-loaded module | **Automatically wakes up** (event-driven modules go through activation lock) | Asynchronous module initialization raises RuntimeError |
| `current_owner` | Attributed to the **target module** (its internal `wait_reply` / send / logging correctly attributed) | Remains the caller |
| Timeout | Default 30 seconds (`timeout=` overrides, None means no timeout) | None |
| Scope audit | Caller passes through outbound gate `actions.<caller>.call` | None |
| Contract validation | `meta.services` whitelist | None |

### Exception Hierarchy

```
ModuleError                      # Base class for module system exceptions
└── ModuleCallError              # Base class for cross-module calls (includes module / method attributes)
    ├── ModuleNotAvailableError  # Target not registered / disabled / activation failed
    ├── ServiceNotProvidedError  # Method not in services whitelist / private method / does not exist
    └── ModuleCallTimeoutError   # Coroutine method timeout
```

All exceptions are part of the `ErisPulseError` hierarchy and can be caught with `from ErisPulse.Core import ModuleCallError`.

## Service Contract: meta.services

The service provider declares the whitelisted services offered externally in `get_meta()` (symmetrical to the `commands` field):

```python
from ErisPulse.Core.Bases import BaseModule, ModuleMeta

class ChatModule(BaseModule):
    @staticmethod
    def get_meta() -> ModuleMeta:
        return ModuleMeta(
            name="聊天",
            services=[
                "get_history",                                       # Simple form
                {"name": "translate", "description": "把文本翻译成指定语言"},  # With description
            ],
        )

    async def get_history(self, session_id, n=20): ...
    async def translate(self, text, target_lang): ...
    def _internal_helper(self): ...   # Underscore-prefixed methods are always forbidden from external calls
```

**Default behavior is invisible to developers**:

- If `services` is not declared → all **public** methods are naturally callable via `module.call()` (consistent with raw attribute access),  
  requiring no declaration at all
- After declaration → restricted to the whitelist, out-of-bounds calls throw `ServiceNotProvidedError`—used to mark  
  "these methods are the ones externally committed"
- The main control authority lies with the user side: `scope.actions` configuration determines "who can call whom" (see auditing below),  
  the module author's `services` is only a service surface declaration; the two layers are independent and not interchangeable

**Service Descriptions**: Provide human-readable / AI-readable descriptions for each service—omit if unnecessary,  
descriptions automatically use the **first line of the method's docstring** (the framework already requires docstring style):

```python
async def translate(self, text, target_lang):
    """把文本翻译成指定语言"""    # ← This line automatically becomes the service description
    ...
```

For fine-grained control (overriding docstring / multi-language support), use dict form to declare `description` (supports i18n dictionary):

```python
services=[
    {"name": "translate", "description": "把文本翻译成指定语言"},
    {"name": "summarize", "description": {"i18n": "Chat.meta.svc.summarize", "default": "摘要对话"}},
]
```

## Service Directory: services()

```python
sdk.module.services()
# {'Chat': [{'name': 'get_history', 'signature': '(session_id, n=20)',
#            'description': 'Translate text into the specified language'}]}

sdk.module.services("Chat")   # Query only a specific module
```

- Only modules that explicitly declare `meta.services` are listed (modules without declaration do not appear in the directory)
- Each service includes a method signature string (extracted using `inspect.signature`) and a description text
- When entering the topology: each module entry in `sdk.module.get_topology()` includes a `services` field

{!--< tips >!--}
**MCP Roadmap**: The service directory (name + signature + description) is essentially the shape of an MCP tool — each service naturally forms a ``{"name", "description", "parameters"}`` structure.
In the future, the framework can directly expose ``services()`` as an endpoint on the MCP server, allowing AI to discover and invoke module capabilities;
``scope.actions.call`` auditing naturally becomes a security gate for AI calls.
{!--< /tips >!--}

## Outbound Auditing: Who Can Call Whom

Every `module.call()` passes through the outbound gate as the **caller module**:

```toml
[ErisPulse.scope.actions.CallerModule.call]
deny = ["Chat.get_history"]        # Deny CallerModule from calling Chat.get_history
# allow = ["Chat.get_*"]           # Or whitelist: only allow calling Chat methods starting with "get_"
```

- The `name` format is `<target_module>.<method_name>`, supporting exact match, glob, or `re:` regular expressions
- Calls from the framework layer (without owner context, such as startup scripts) are not subject to auditing constraints
- Denied calls throw `ModuleCallError` (TRACE log `core.module.call_denied`)

For configuration details, see the outbound dimension in [Scope](scope.md).

## Directed Event: emit_to

```python
# Emitter side: After validating that the target is enabled, the event enters the module.<name>.<event> namespace
await sdk.module.emit_to("Chat", "message_received", {"text": "hi", "from": "u1"})

# Subscriber side (within the Chat module): Register hooks by namespace
from ErisPulse.Core.lifecycle import lifecycle

@lifecycle.on("module.Chat.message_received")
async def on_message_received(data): ...

@lifecycle.on("module.Chat")          # Or receive all directed events from this module
async def on_any(data): ...
```

Semantic details:

- If the target is not registered / not enabled → `ModuleNotAvailableError` (**do not send to non-existent locations**)
- If the target is a lazy-loaded module → **wake up first, then deliver** (directed events serve as activation sources, aligning with the semantics of `activate_on`)
- When `data` is a dict, it automatically carries `_trace_id` (without overwriting existing values), integrating with full-chain tracing

## Lazy Loading and Invocation

`module.call()` and `emit_to()` transparently awaken lazy-loaded modules:

- Event-driven lazy modules (`activate_on` declaration) → Use activation lock `_activate()`, and the trigger stub is automatically unregistered after activation.
- Regular lazy modules → Synchronize initialization or follow the regular loading path (idempotent).
- Wakeup failure → `ModuleNotAvailableError` (for `call`) / Activation failure (for `emit_to`).

That is: **the caller does not need to care whether the target module is loaded, nor wait for any event to awaken it.**

## Cold Start Replay

When a module is newly installed or restarted, it may miss some chat messages. The `get_load_strategy(replay=...)` method allows the framework to replay the most recent messages from the session inbox to the module itself after it becomes ready:

```python
from ErisPulse.loaders import ModuleLoadStrategy

class MyAIModule(BaseModule):
    @staticmethod
    def get_load_strategy():
        return ModuleLoadStrategy(
            lazy_load=False,
            priority=100,
            replay="5m",        # Replay the most recent 5 minutes ("1h" or "300" seconds are also valid)
        )

    async def on_load(self, event):
        @message.on_message()
        async def handle(e):
            if e.get("replayed"):
                # Synthetic event: only restore context, do not trigger side effects such as sending
                ...
```

Semantic details:

- The data source is the [session inbox](interaction.md#session-inbox-eventhistory) (`sdk.transcript.recent()`), and the replay is executed in the background after the module finishes loading, without blocking the startup process.
- Synthetic events are marked with `replayed: True` and include complete fields such as `platform`, `detail_type`, `user_id`, and `alt_message`, and are **only distributed to this module's handlers**—other modules are unaffected by the replay.
- If the inbox is not enabled, there are no records, or the duration declaration is invalid (`replay_invalid` warning), the replay is silently skipped.

## Event Idempotency Deduplication

After the platform's WebSocket reconnects, it often resends the same event (with the same `event["id"]`) — the distribution entry uses LRU deduplication by ID (capacity 4096), ensuring each event with the same ID is only distributed once.

```toml
[ErisPulse.framework]
event_dedupe = true   # Enabled by default; can be disabled in test environments where fixed ID synthetic events are used
```

The deduplication cache is automatically reset when the adapter registers (the starting point of a new connection lifecycle).

## Related Documentation

- [Interactive Session System](interaction.md) - wait_reply / timer / multi-path waiting / session mutual exclusion
- [Scope (scope)](scope.md) - Complete configuration for outbound dimension auditing
- [Ownership (owner) System](ownership.md) - How the owner context propagates across module calls
- [Lazy Loading System](lazy-loading.md) - Lazy loading and event-driven lazy activation (activate_on)
- [Lifecycle Management](lifecycle.md) - Mechanism of the broadcast layer event bus