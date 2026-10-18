# Scope

> [!TIP]
> **When to read this**: When you need to control module availability, event acceptance, or outbound action restrictions. Skip if not needed, it does not affect the use of other features.

> [!NOTE]
> This feature requires ErisPulse **2.8.0+**.

Scope answers four questions: **which modules are available, whether to accept events, what text a module processes, and what outbound actions a module can perform**. Control is entirely user-driven: at the upper level of module / adapter / processor / outbound call registration (configuration `ErisPulse.scope` or runtime `sdk.scope`), it is declared uniformly. The event pipeline automatically reads and executes at the entry, processor filtering, and outbound gate.

| Dimension | Controls what | Rejection behavior | Configuration path |
|------|---------|---------|---------|
| **① Module** | Which modules are available (platform / Bot / session three levels) | Filtered modules do not trigger or reply (intercept broadcast `scope.blocked` event; matched commands are still claimed and blocked) | `scope.platforms / bots / sessions` |
| **② Identity** | Whether to accept events (adapter / Bot / session / user four levels) | Completely discard at entry (intercept broadcast `scope.blocked` event) | `scope.identity.*` |
| **③ Outbound** | Which outbound calls a module can initiate (message / API / request, method-level white/black lists) | Fail response (`retcode=34601`) | `scope.actions` |

> **Related system**: Commands are special message event handlers, their user white/black lists (ACL) and implementation parameter overwrites are maintained by the command system (`ErisPulse.event.command`), see [Event Handling Introduction](../getting-started/event-handling.md) and [Configuration Guide](../user-guide/configuration.md).

{!--< tips >!--}
1. Import the singleton via `from ErisPulse.Core import scope` (same object as `sdk.scope`)
2. Check: `scope.is_allowed(...)` / `scope.is_identity_allowed(...)` /
   `scope.is_action_allowed(...)` corresponding to the three gates ①②③
3. Read/write: dimension-specific parameter methods (IDE can auto-complete) —
   `scope.set_module(...)` / `scope.set_identity(...)` / `scope.set_action(...)`;
   Additionally, there is a dictionary-style fallback `scope.get(path)` / `scope.set(path, v)` / `scope.delete(path)`
4. Event handler text condition overwrite see
   [Event Handling Introduction · Event Overwrite](../getting-started/event-handling.md#event-overwrite-overwrite-any-event-type-behavior-without-modifying-module-code);
   Command ACL / parameter overwrite see [Event Handling Introduction](../getting-started/event-handling.md)
{!--< /tips >!--}

## Matching Entry Syntax (Unified Across the System)

All "name lists" in scope (module names, identity keys, outbound entries) share the same matching syntax (`ErisPulse.Core.text_match`):

| Syntax | Example | Description |
|------|------|------|
| Exact name | `"Chat"` | Full value comparison, **case-insensitive** |
| Glob | `"Tool*"`、`"spam_*"` | `*` for any string / `?` for single character / `[seq]` for character set, case-insensitive |
| Regex | `"re:^Danger.*"` | Prefix with `re:` for regex `search` matching, default case-insensitive |

- Invalid regex silently degrades to "no match" (no error thrown, no crash)
- Decorator parameters (`pattern=` / `regex=`) have fixed semantics: `pattern` is glob, `regex` is regex source (no `re:` prefix); regex entries in scope configuration **must** have the `re:` prefix

## Global Fallback: `default_allow`

`default_allow` is the **single global fallback switch** (default `true`), affecting two decision dimensions:

- **Module dimension**: If no binding is matched → `default_allow` determines allow or deny
- **Identity dimension**: If no policy is matched → `default_allow` determines allow or deny

Setting it to `false` enables "implicit deny" strict mode: whitelist-based management,
**everything not explicitly allowed is denied**.

> **Exception**: The ③ outbound dimension is **not** affected by `default_allow`—it is an independent tightening switch, defaulting to full allow, only explicitly rules restrict (framework-level owner-empty calls always allow). This strict global mode won't accidentally cut off all module message replies. Command ACL has a separate `ErisPulse.event.command.default_allow` fallback, independent of each other.

## Configuration File

```toml
[ErisPulse.scope]
default_allow = true        # Global fallback (false = implicit deny strict mode)
cache_size = 1024           # LRU cache size

# ── ① Module dimension (priority: session > Bot > platform) ──
[ErisPulse.scope.platforms.onebot11]
modules = ["Chat", "Tool*"]   # Whitelist: exact name / glob / re: regex
blocked = ["re:^Danger"]
[ErisPulse.scope.bots.onebot11."123456"]
modules = ["Chat"]
merge = true                  # Append on top of platform-level binding (default is full override)
[ErisPulse.scope.sessions.onebot11."789012345"]
modules = ["Chat"]

# ── ② Identity dimension (priority: user > session > Bot > adapter) ──
[ErisPulse.scope.identity.adapters.onebot11]
deny = true                   # Discard all events from this adapter
[ErisPulse.scope.identity.bots.onebot11."123456"]
deny = true
[ErisPulse.scope.identity.sessions.onebot11."g_blocked"]
deny = true
[ErisPulse.scope.identity.users.onebot11]
allow = ["u_admin"]           # User keys support glob / re: regex
deny = ["u_bad", "spam_*"]

# ── ③ Outbound dimension (default allow all, restrict only with explicit rules) ──
[ErisPulse.scope.actions.MyModule]
send = { deny = true }                                    # Disable all sending
api = { allow = ["get_*"] }                               # Only allow standard query APIs
request = { deny = true }                                 # Disable request handling
```

## ① Module Dimension

Answers "which modules are available in a certain context." By default, all are open; filtering starts only after configuration binding.
**Modules and adapters require no changes**.

```mermaid
flowchart TD
    A["Event arrives at a module's handler/command"] --> B{"scope.is_allowed<br/>(platform, bot, module, session)"}
    B --> C{"Parse chain: session-level > Bot-level > platform-level<br/>(if sub-level merge = true, merge entries individually)"}
    C -->|"Matched"| D["blocked matched → deny<br/>modules non-empty → only whitelist allowed<br/>both empty → default_allow"]
    C -->|"Not matched"| E["default_allow (default true = allow)"]
    D -->|"Deny"| Z["No reply<br/>(intercept broadcast `scope.blocked` event; matched commands are still claimed and blocked)"]
```

- **Parse priority: session-level > Bot-level > platform-level**, higher priority bindings **fully override** lower priority; if sub-level binding writes `merge = true`, it becomes **entry-by-entry union** with lower priority (both `modules` and `blocked` are merged individually, `merge` itself is a control key, not counted as an entry)
- **Default semantics**: Filtered module commands and handlers do not trigger or reply, visible in TRACE-level logs (`core.scope.denied`); interception also broadcasts the `scope.blocked` lifecycle event (subscribing makes it observable who is blocked and why); **matched commands** are still claimed and blocked—command text is no longer leaked to lower-priority message handlers, eliminating the ambiguity of "double response" where a command is rejected and then the message handler responds again
- **Framework-level handlers** (`scope_exempt=True` or owner is empty) are unaffected; module name is empty (framework-level resources) always allowed
- **Session-aware help and command query**: Command query APIs (`command.help` /
  `get_command` / `get_commands` / `get_group_commands` / `get_visible_commands`,
  and `module.get_commands_overview`) all support optional `event=` or explicit
  `platform=` / `bot_id=` / `session_id=` keyword—commands from modules unavailable in the current session
  no longer appear in results (`get_command` returns None, single command help is treated as "unregistered",
  consistent with default semantics); if no context is provided, full behavior is maintained

### Binding Inheritance (merge)

The default semantics of full override are clear and predictable; when you need to **append** on top of an upper-level binding, write `merge = true` in the sub-level:

```toml
[ErisPulse.scope.platforms.onebot11]
modules = ["Chat", "Tool"]      # Platform-level: allow Chat, Tool

[ErisPulse.scope.bots.onebot11."123456"]
modules = ["Music"]
merge = true                    # The actual effective modules for this Bot = ["Chat", "Tool", "Music"]
```

- **Merge rules**: `modules` and `blocked` each take **union**; `blocked` still takes precedence over `modules` within the binding
- **Chained merge**: Platform → Bot → Session is layered step-by-step, each level independently decides `merge` or full override

## ② Identity Dimension (Event Acceptance)

Answers "whose events are accepted or rejected." Events that are rejected are **completely discarded at the distribution entry**—they do not enter middlewares or any processor (including framework-level), visible only in TRACE-level logs (`core.scope.identity_denied`).

- **Parse priority: user > session > Bot > adapter**, taking the most specific configured policy; deny takes precedence over allow
- Each level of binding is a binary policy: `{ allow = true }` or `{ deny = true }`
- User keys support glob / regex (e.g., `"spam_*"` to block a batch of spam users)
- Typical usage—deny at upper level, allow individual for "exceptional pass-through":

```toml
[ErisPulse.scope.identity.adapters.onebot11]
deny = true
[ErisPulse.scope.identity.users.onebot11]
allow = ["u_admin"]   # Even if adapter-level is denied, events from u_admin are still allowed
```

## ③ Outbound Dimension (Restricting Module Outbound Calls)

Restricts the **outbound actions** a module can initiate: message sending / standard API actions / request operations. The three action types correspond to the underlying DSL: `Event.reply` and `Send` (send), `Api` / `call_api` (api), `Request`'s accept/reject (request). Outbound calls initiated by modules during event handler execution carry the module owner, and are uniformly judged by this dimension.

### Rule Form (Inline Table)

The rule for each action is an inline table: `{ allow = [...], deny = true|[...] }`.
Only one rule can exist for the same action (TOML keys are not repeatable, choose between full deny and fine-grained):

```toml
[ErisPulse.scope.actions.MyModule]
send = { deny = true }                                  # Disable all sending (Event.reply / Send DSL)
# Or fine-grained by method: send = { allow = ["Text", "Image*"], deny = ["File"] }
api = { allow = ["get_*"] }                             # Only allow standard query APIs
# Or blacklist by action: api = { deny = ["set_*", "leave_*"] }
request = { deny = true }                               # Disable request handling accept/reject
```

- `send` entries match **send method names** (`Text` / `Image` / `File` ...),
  `api` entries match **standard action names** (`get_group_info` / `set_group_name` ...)
- Entries support exact names / glob / `re:` regex (consistent with the unified system syntax, case-insensitive)
- Writing a single string in `allow` is equivalent to a single-entry list: `send = { allow = "Text" }`

### Decision Semantics

**Default is full allow**—if not configured, or owner is empty (internal framework calls), it is allowed.
After configuring rules, the following order is used for determination:

1. `deny = true` → reject
2. `deny` list matches the call name → reject
3. `allow` list is non-empty and the call name is not matched (or the call has no name) → reject
4. Otherwise, allow

Rejected calls do not initiate any network requests, directly returning the standard failure response
(`retcode = 34601`, see [api-response §5.3](../standards/api-response.md#53-framework-extended-return-code-34xxx-custom-defined-low-three-digits-in-the-platform-error-segment)).

The three actions are independent, and only one can be restricted.

```python
# Runtime API
sdk.scope.set_action("MyModule", "send", deny=True)              # Disable all message sending
sdk.scope.set_action("MyModule", "send", allow=["Text"])         # Allow only text messages
sdk.scope.is_action_allowed("MyModule", "send", name="Image")    # False
sdk.scope.is_action_allowed("MyModule", "api", name="get_user_info")  # Determine by rule
sdk.scope.delete_action("MyModule", "send")                      # Restore allow
sdk.scope.get_action("MyModule", "send")                         # Current rule for this action
```

## Runtime API

The runtime API for scope is layered in three tiers: **determination** (three questions), **dimension-specific read/write** (each dimension has `set` / `get` / `delete` parameterized methods, fully type-annotated, IDE can auto-complete), and **dictionary-style fallback** (dot-separated path to reach any section).

```python
from ErisPulse import sdk

scope = sdk.scope
```

### Determination (Three Questions)

```python
scope.is_allowed("onebot11", "123456", "Chat")                 # ① Module dimension
scope.is_allowed("onebot11", "123456", "Chat", "789012345")    # With session-level
scope.is_allowed("onebot11", "123456", None)                   # Framework-level resource -> True

scope.is_identity_allowed("onebot11", "123456", "group_9", "u1")   # ② Identity dimension

scope.is_action_allowed("MyModule", "send")                    # ④ Outbound dimension
scope.is_action_allowed("MyModule", "send", name="Image")      # Fine-grained by method
```

### ① Module Dimension

```python
# Binding (hierarchy determined by parameters: session_id > bot_id > platform-level)
scope.set_module("onebot11", bot_id="123456", modules=["Chat", "Tool*"])
scope.set_module("onebot11", blocked=["re:^Danger"])                       # Platform-level
scope.set_module("onebot11", bot_id="123456", session_id="g9", modules=["Chat"])  # Session-level
scope.set_module("onebot11", bot_id="123456", modules=["Music"], merge=True)      # Union with existing entries
scope.set_module("onebot11", bot_id="123456", modules=["Chat"], persist=False)    # Runtime only

# Read / Delete
scope.get_module("onebot11", bot_id="123456")   # {"modules": ["Chat"], "blocked": []}
scope.delete_module("onebot11", bot_id="123456")
```

> `merge=True` is **merge on write** (merge entries with existing binding at this level); the `merge = true` configuration key during cross-level parsing is described above in [Binding Inheritance](#binding-inheritancemerge)—these are independent mechanisms.

> **Runtime binding (`persist=False` semantics)**: Runtime bindings are saved in a separate overlay layer,
> **any subsequent configuration writes / hot reloads of the configuration file will not overwrite them** (the configuration tree is rebuilt and automatically replayed in the order of writes, including runtime deletions). They are not persisted, and are lost upon process restart; runtime bindings written by a module are cleaned up when the module is unloaded. Subsequent `persist=True` writes (user-persistent semantics) to the same path will replace the runtime rules.

### ② Identity Dimension

```python
# Binding policies (hierarchy determined by parameters: user > session > bot > adapter; allow / deny are mutually exclusive)
scope.set_identity("onebot11", user_id="u_bad", deny=True)
scope.set_identity("onebot11", user_id="spam_*", deny=True)    # Keys support glob / re: regex
scope.set_identity("onebot11", bot_id="123456", session_id="g9", allow=True)

# Read / Delete
scope.get_identity("onebot11", user_id="u_bad")   # {"deny": True}
scope.delete_identity("onebot11", user_id="u_bad")
```

### ③ Outbound Dimension

```python
# Set restriction rules (allow: str|list; deny: bool|str|list; whole rule replacement semantics)
scope.set_action("MyModule", "send", deny=True)                    # Disable all sending
scope.set_action("MyModule", "send", allow=["Text"])               # Allow only text messages
scope.set_action("MyModule", "api", deny=["set_*", "leave_*"])     # Disable management APIs

# Read / Delete
scope.get_action("MyModule", "send")       # {"allow": ["Text"]} original rule
scope.delete_action("MyModule", "send")    # Remove single action
scope.delete_action("MyModule")            # Remove all action restrictions for this module
```

### General

```python
scope.get("platforms")   # Dictionary-style fallback: dot-separated path to read any section
scope.topology()         # Full configuration tree (for Dashboard)
scope.stats()
# {"module_calls": .., "module_filtered": .., "identity_checks": .., "identity_denied": ..,
#  "action_checks": .., "action_denied": .., "cache_hits": .., "cache_misses": ..}
scope.reset_stats()
scope.clear()           # Clear all configurations (only effective in memory)
```

### Advanced: Dictionary-style Dot-separated Path Fallback

Dimension-specific methods cover daily scenarios; when you need to directly access any node (or future added dimensions), use the dictionary-style API—`get` / `set` / `delete` accepts dot-separated paths (deep merge for dict, read immediately after write), and provides `scope[path]` / `scope[path] = v` / `del scope[path]` / `path in scope` protocol:

```python
scope.set("bots.onebot11.123456", {"modules": ["Chat"], "blocked": []})
scope.set("identity.users.onebot11.u_bad", {"deny": True})
scope.get("actions.MyModule.send")

scope["platforms.onebot11"]        # Read (raises KeyError if not exists)
scope["platforms.onebot11"] = {...}  # Write
del scope["platforms.onebot11"]      # Delete
"actions.MyModule" in scope          # Check existence
```

## Interception Observability: `scope.blocked` Event

When scope interception (module filtering / identity rejection) occurs, the lifecycle event **`scope.blocked`** is broadcast,
making "who is blocked, at which level" subscribable, statable, and presentable in the Dashboard—interception defaults
to no reply, but is no longer an unknowable black box.

| Field | Description |
|------|------|
| `dimension` | `"module"` (module dimension filtering) / `"identity"` (identity acceptance rejection) |
| `module` | The filtered module name (only module dimension) |
| `platform` / `bot_id` / `session_id` / `user_id` | The context where the interception occurred |

```python
from ErisPulse.Core.lifecycle import lifecycle

@lifecycle.on("scope.blocked")
def on_blocked(data):
    print(f"Blocked: {data['dimension']} {data.get('module') or data.get('user_id')}")
```

- The event is broadcast via `fire` in the background (zero overhead if no listeners, does not slow hot paths)
- Repeated interception hits in the cache **do not** broadcast again—each unique combination is broadcast only once when the cache expires
- Distinct from `adapter.event.blocked` (event-level discard): this
  event is the module/identity filtering at the scope acceptance gate

## Cache and Hot Reload

- `is_allowed` / `is_identity_allowed` / `is_action_allowed` results are cached with **LRU cache**
  (`scope.cache_size` is adjustable), `set` / `delete` /
  configuration hot reload (`config.updated` / `config.set`) automatically invalidate
- All dimension configurations take effect **immediately**, no restart required
- Scope is "event-by-event" judgment, not cross-event memory: if configuration changes, the next event follows the new rules

## Configuration Format Validation

When loading / hot reloading, each section is validated for configuration format: type errors in sections (e.g., `platforms` written as a string), invalid outbound rules (e.g., `allow` written as a number), unknown action names, unknown top-level keys (e.g., `alow` spelling error)
will output **WARNING** and ignore the corresponding section / entry, while other valid configurations take effect as usual—writing errors no longer silently fail.

## Common Issues and Precautions

### 1. Configuration Hierarchy and Overriding

- Module dimension: session-level > Bot-level > platform-level, **full override** (if sub-level `merge = true`, each entry is unioned). To "platform allows Chat, Bot adds Music", write `merge = true` in the Bot-level, or list both simultaneously
- Identity dimension: user > session > Bot > adapter, take the **most specific** configured policy (can do exceptional pass-through)
- Command user white/black lists: exact command names take precedence over glob keys (see `event.command.acl`)

### 2. Module/Command Not Responding

First suspect scope rather than the module itself:

```python
from ErisPulse import sdk

print(sdk.scope.is_allowed(event.get_platform(), bot_id, "MyModule", session_id))
print(sdk.scope.is_identity_allowed(event.get_platform(), bot_id, session_id, user_id))
print(sdk.scope.stats())   # module_filtered / identity_denied > 0 indicates there are interception records
```

Filtered modules default to no reply (module dimension and identity dimension, avoiding rule exposure), but broadcast the `scope.blocked` lifecycle event and continuously accumulate statistics;
ACL-rejected commands return an explicit "insufficient permissions" response.

### 3. Troubleshooting Outbound Actions Rejected

```python
from ErisPulse import sdk

print(sdk.scope.get("actions.MyModule"))
print(sdk.scope.stats())   # action_denied > 0 indicates there are intercepted calls
```

Interception is **explicit**: rejected calls return the standard failure response (`retcode = 34601`) without initiating network requests.

### 4. Session Identifier Cross-Platform Isolation

The `(platform, session_id)` combination is the unique identifier. `scope.sessions.onebot11."789"` only affects onebot11, not telegram sessions with the same `789`. The same applies to identity dimension user keys.

## Topology Tree API

`ModuleManager.get_topology()` and `AdapterManager.get_topology()` provide module/adapter ownership relationship data,
`sdk.get_topology()` aggregates them (including scope):

```python
from ErisPulse import sdk

topology = sdk.get_topology()
# {
#   "modules": {                                   # Module → owned resources
#     "Chat": {
#       "loaded": True, "enabled": True,
#       "commands": ["chat", "translate"],
#       "handlers": {"message": 2, "notice": 1},
#       "routes": {"http": ["/Chat/api"], "ws": [], "sse": []},
#       "lifecycle_hooks": 3,
#     }
#   },
#   "adapters": {                                  # Adapter → Bot → Scope
#     "onebot11": {
#       "status": "started", "enabled": True,
#       "bots": {"123456": {"status": "online", "scope": {...}}},
#       "scope": {"modules": [...], "blocked": [...]},
#     }
#   },
#   "scope": {                                     # Scope (module / identity / outbound actions)
#     "platforms": {...}, "bots": {...}, "sessions": {...},
#     "identity": {"adapters": {...}, "bots": {...}, "sessions": {...}, "users": {...}},
#     "actions": {...},
#   },
# }
```

- Module topology aggregates commands registered by the module, event handlers, HTTP/WS/SSE routes, and lifecycle hooks, facilitating the drawing of module resource trees.
- Adapter topology aggregates status of each adapter, status of subordinate Bots, and platform-level/Bot-level scope bindings (module dimension).
- **JSON-safe output**: `get_topology(json_safe=...)` defaults to `True`, returning a structure that can be directly `json.dumps`—module `info` retains only the pure data `meta` sub-table (discarding `module_class` / `strategy` runtime objects), and other nodes (including arbitrary objects inserted by adapter authors into Bot `info`) are purged (class objects take `__name__`, unserializable objects degrade to `str()`). Dashboards/WebUI can directly serialize and return; for original objects, pass `json_safe=False`.