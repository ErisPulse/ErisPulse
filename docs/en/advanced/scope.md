# Scope

> [!NOTE]
> This feature requires ErisPulse **2.8.0+**.

Scope answers four questions: **which modules are available, who receives events, what text does a module process, and what can a module do externally**.  
Control is entirely given to the user: at the **upper level** (configured via `ErisPulse.scope` or runtime `sdk.scope`) of module / adapter / processor / outbound call registration, event pipelines automatically read and execute at the entry, processor filtering, and outbound gate.

| Dimension | Controls what | Rejection behavior | Configuration path |
|------|---------|---------|---------|
| **① Module** | Which modules are available (platform / Bot / session three levels) | Silently ignore (no reply, no claim) | `scope.platforms / bots / sessions` |
| **② Identity** | Whether to receive events (adapter / Bot / session / user four levels) | Completely discard at entry (silent) | `scope.identity.*` |
| **③ Outbound** | What outbound calls a module can initiate (message / API / request, method-level white/blacklist) | Fail response (`retcode=34601`) | `scope.actions` |

> **Related systems**: Commands are special message event processors, their user whitelists/blacklists (ACL) and implementation parameter overrides are self-managed by the command system (`ErisPulse.event.command`), see [Event Handling Introduction](../getting-started/event-handling.md) and [Configuration Guide](../user-guide/configuration.md).

{!--< tips >!--}
1. Import the singleton via `from ErisPulse.Core import scope` (same object as `sdk.scope`)
2. Check: `scope.is_allowed(...)` / `scope.is_identity_allowed(...)` /
   `scope.is_action_allowed(...)` correspond to the three gates ①②③
3. Read/Write: dimension-specific parameter methods (IDE can complete) —
   `scope.set_module(...)` / `scope.set_identity(...)` / `scope.set_action(...)`；
   There is also a dictionary-style fallback `scope.get(path)` / `scope.set(path, v)` / `scope.delete(path)`
4. Event processor text condition overrides are described in
   [Event Handling Introduction · Event Overriding](../getting-started/event-handling.md#event-overriding-does-not-modify-module-code-overrides-behavior-of-any-event-type);
   Command ACL / parameter overrides are described in [Event Handling Introduction](../getting-started/event-handling.md)
{!--< /tips >!--}

## Matching Entry Syntax (Unified Across the System)

All "name lists" in scope (module names, identity keys, outbound entries) share the same matching syntax
(`ErisPulse.Core.text_match`):

| Syntax | Example | Description |
|------|------|------|
| Exact name | `"Chat"` | Full value comparison, **case-insensitive** |
| Glob | `"Tool*"`、`"spam_*"` | `*` matches any string / `?` matches single character / `[seq]` matches character set, case-insensitive |
| Regex | `"re:^Danger.*"` | Declared with `re:` prefix, matches via regex `search`, default case-insensitive |

- Invalid regex **silently degrades** to "no match" (no error, no crash)
- Decorator parameters (`pattern=` / `regex=`) have fixed semantics: `pattern` is glob, `regex` is the regex source code
  (without `re:` prefix); regex entries in scope configuration **must** have the `re:` prefix

## Global Fallback: `default_allow`

`default_allow` is the **global unique** fallback switch (default `true`),
affecting two decision dimensions uniformly:

- **Module dimension**: No binding matched → `default_allow` determines allow / deny
- **Identity dimension**: No strategy matched → `default_allow` determines allow / deny

Setting it to `false` enables "implicit deny" strict mode: whitelist-style management,
**everything not explicitly allowed is denied**.

> **Exception**: The outbound dimension is **not affected** by `default_allow` — it is an independent tightening switch,
> defaulting to full allow, only explicit rules restrict (framework-level owner is empty calls are always allowed).
> This strict global mode won't accidentally cut off all module message replies.
> Command ACL has an independent `ErisPulse.event.command.default_allow` fallback, unaffected.

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

# ── ③ Outbound dimension (default allow all, only explicit rules restrict) ──
[ErisPulse.scope.actions.MyModule]
send = { deny = true }                                    # Disable all sending
api = { allow = ["get_*"] }                               # Only allow standard query APIs
request = { deny = true }                                 # Disable request handling
```

## ① Module Dimension

Answers "which modules are available in a given context." Default is fully open; filtering starts only after configuration binding,
**modules and adapters require no changes**.

```mermaid
flowchart TD
    A["Event arrives at a module's handler/command"] --> B{"scope.is_allowed<br/>(platform, bot, module, session)"}
    B --> C{"Parse chain: session-level > Bot-level > platform-level<br/>(if sub-level merge = true, merge entries level by level)"}
    C -->|"Matched"| D["blocked matched → deny<br/>modules non-empty → only whitelist allowed<br/>both empty → default_allow"]
    C -->|"Not matched"| E["default_allow (default true = allow)"]
    D -->|"Denied"| Z["Silently ignore<br/>(no reply, no claim, only TRACE log visible)"]
```

- **Parse priority: session-level > Bot-level > platform-level**, higher priority bindings **fully override** lower levels;
  if a sub-level binding writes `merge = true`, it changes to **per-entry merge** with lower levels (merge `modules` / `blocked` individually,
  `merge` itself is a control key, not counted as an entry)
- **Silent semantics**: Commands and processors of filtered modules do not trigger, reply, or claim (prevent cross-command mis-matching),
  only TRACE-level logs are visible (`core.scope.denied`)
- **Framework-level processors** (`scope_exempt=True` or owner is empty) are unaffected; modules with empty names (framework-level resources) are always allowed
- **Session-aware help and command queries**: Command query APIs (`command.help` /
  `get_command` / `get_commands` / `get_group_commands` / `get_visible_commands`,
  and `module.get_commands_overview`) all support optional `event=` or explicit
  `platform=` / `bot_id=` / `session_id=` keywords — commands from modules unavailable in the current session
  no longer appear in the results (single command help is treated as "unregistered" if `get_command` returns None,
  consistent with silent semantics); if no context is provided, full behavior is maintained

### Binding Inheritance (merge)

Default full override semantics are clear and predictable; when you need to **append** to an upper-level binding, write `merge = true` in the sub-level:

```toml
[ErisPulse.scope.platforms.onebot11]
modules = ["Chat", "Tool"]      # Platform-level: allow Chat, Tool

[ErisPulse.scope.bots.onebot11."123456"]
modules = ["Music"]
merge = true                    # The actual effective for this Bot = ["Chat", "Tool", "Music"]
```

- **Merge rules**: `modules` and `blocked` each take **union**; `blocked` still takes precedence over `modules` within the binding
- **Chain merging**: Platform → Bot → session level by level, each level independently decides `merge` or override

## ② Identity Dimension (Event Admission)

Answers "whose events are received." Events rejected at the **distribution entry are completely discarded** —
they do not enter middleware or any processor (including framework-level), only TRACE-level logs are visible (`core.scope.identity_denied`).

- **Parse priority: user > session > Bot > adapter**, take the most specific configured strategy; deny takes precedence over allow
- Each level binding is a binary strategy: `{ allow = true }` or `{ deny = true }`
- User keys support glob / regex (e.g. `"spam_*"` to block a batch of spam users)
- Typical use case — upper-level deny, individual allow for "exception allow":

```toml
[ErisPulse.scope.identity.adapters.onebot11]
deny = true
[ErisPulse.scope.identity.users.onebot11]
allow = ["u_admin"]   # Even if adapter-level is denied, events from u_admin are still allowed
```

## ③ Outbound Dimension (Limit Module Outbound Calls)

Constraints on modules **initiating outbound actions**: message sending / standard API actions / request operations.
Three action types correspond to underlying DSL: `Event.reply` and `Send` (send), `Api` / `call_api` (api), and `Request`'s accept/reject (request). Outbound calls initiated by modules during event handler execution
carry the module owner, and are uniformly judged by this dimension.

### Rule Form (Inline Table)

Each action's rule is an inline table: `{ allow = [...], deny = true|[...] }`.
Only one rule is allowed per action (TOML keys are not repeatable, choose between full deny and fine-grained):

```toml
[ErisPulse.scope.actions.MyModule]
send = { deny = true }                                  # Disable all sending (Event.reply / Send DSL)
# Or method-level fine-grained: send = { allow = ["Text", "Image*"], deny = ["File"] }
api = { allow = ["get_*"] }                             # Only allow standard query APIs
# Or action-level blacklist: api = { deny = ["set_*", "leave_*"] }
request = { deny = true }                               # Disable request handling accept/reject
```

- `send` entries match **send method names** (`Text` / `Image` / `File` ...),
  `api` entries match **standard action names** (`get_group_info` / `set_group_name` ...)
- Entries support exact name / glob / `re:` regex (consistent with unified system syntax, case-insensitive)
- Writing a single string in `allow` is equivalent to a single-entry list: `send = { allow = "Text" }`

### Decision Semantics

**Default is fully allowed** — unconfigured, or owner is empty (internal framework calls) are always allowed.
After configuring rules, the following order is used for judgment:

1. `deny = true` → deny
2. `deny` list matches the call name → deny
3. `allow` list is non-empty and the call name is not matched (or the call has no name) → deny
4. Otherwise, allow

Denied calls do not initiate any network requests, directly returning a standard failure response
(`retcode = 34601`, see [api-response §5.3](../standards/api-response.md#53-framework-extension-return-code-34xxx-customization-in-low-three-digits-of-platform-error-segment)).

The three actions are independent, allowing restriction of only one.

```python
# Runtime API
sdk.scope.set_action("MyModule", "send", deny=True)              # Disable all message sending
sdk.scope.set_action("MyModule", "send", allow=["Text"])         # Allow only text sending
sdk.scope.is_action_allowed("MyModule", "send", name="Image")    # False
sdk.scope.is_action_allowed("MyModule", "api", name="get_user_info")  # Judged by rules
sdk.scope.delete_action("MyModule", "send")                      # Restore allow
sdk.scope.get_action("MyModule", "send")                         # Current rule for this action
```

## Runtime API

The runtime API for scope is divided into three layers: **decision** (three questions), **dimension-specific read/write** (each dimension has `set` / `get` / `delete` parameterized methods, all signatures are type-annotated, IDE can complete), and **dictionary-style fallback** (dot-separated path to any section).

```python
from ErisPulse import sdk

scope = sdk.scope
```

### Decision (Three Questions)

```python
scope.is_allowed("onebot11", "123456", "Chat")                 # ① Module dimension
scope.is_allowed("onebot11", "123456", "Chat", "789012345")    # With session-level
scope.is_allowed("onebot11", "123456", None)                   # Framework-level resource -> True

scope.is_identity_allowed("onebot11", "123456", "group_9", "u1")   # ② Identity dimension

scope.is_action_allowed("MyModule", "send")                    # ④ Outbound dimension
scope.is_action_allowed("MyModule", "send", name="Image")      # Method-level fine-grained
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

> `merge=True` is **write-time union** (merge entries with existing bindings at this level); `merge = true` configuration during cross-level parsing is described above in [Binding Inheritance](#binding-inheritance-merge) — these are independent mechanisms.

### ② Identity Dimension

```python
# Binding strategy (hierarchy determined by parameters: user > session > bot > adapter; allow / deny chosen)
scope.set_identity("onebot11", user_id="u_bad", deny=True)
scope.set_identity("onebot11", user_id="spam_*", deny=True)    # Key supports glob / re: regex
scope.set_identity("onebot11", bot_id="123456", session_id="g9", allow=True)

# Read / Delete
scope.get_identity("onebot11", user_id="u_bad")   # {"deny": True}
scope.delete_identity("onebot11", user_id="u_bad")
```

### ③ Outbound Dimension

```python
# Set restriction rules (allow: str|list; deny: bool|str|list; whole rule replacement semantics)
scope.set_action("MyModule", "send", deny=True)                    # Disable all sending
scope.set_action("MyModule", "send", allow=["Text"])               # Allow only text sending
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
scope.clear()           # Clear all configurations (memory only)
```

### Advanced: Dictionary-style Dot-separated Path Fallback

Dimension-specific methods cover everyday scenarios; when you need to directly access any node (or future added dimensions),
use the dictionary-style API — `get` / `set` / `delete` accepts dot-separated paths (deep dict merge, write and read immediately),
and provides `scope[path]` / `scope[path] = v` / `del scope[path]` / `path in scope` protocols:

```python
scope.set("bots.onebot11.123456", {"modules": ["Chat"], "blocked": []})
scope.set("identity.users.onebot11.u_bad", {"deny": True})
scope.get("actions.MyModule.send")

scope["platforms.onebot11"]        # Read (throws KeyError if not found)
scope["platforms.onebot11"] = {...}  # Write
del scope["platforms.onebot11"]      # Delete
"actions.MyModule" in scope          # Existence check
```

## Cache and Hot Update

- `is_allowed` / `is_identity_allowed` / `is_action_allowed` results include **LRU cache**
  (`scope.cache_size` is adjustable), `set` / `delete` /
  configuration hot update (`config.updated` / `config.set`) automatically invalidate
- All dimension configurations are effective **immediately**, no restart required
- Scope is "per-event" judgment, not cross-event memory: configuration changes, next event is judged by new rules

## Configuration Format Validation

Configuration format is validated section by section during load / hot update: invalid sections (e.g. `platforms` written as a string), invalid outbound rules (e.g. `allow` written as a number), unknown action names, unknown top-level keys (e.g. `alow` typo)
output **WARNING** and ignore the corresponding section / entry, other valid configurations are still effective — errors no longer silently fail.

## Common Issues and Notes

### 1. Configuration Hierarchy and Overriding

- Module dimension: session-level > Bot-level > platform-level, **full override** (if sub-level `merge = true`, entries are merged level by level).
  To "platform allows Chat, Bot adds Music", write `merge = true` in the Bot-level, or list both
- Identity dimension: user > session > Bot > adapter, take the **most specific** configured strategy (can do exception allow)
- Command user whitelists/blacklists: exact command names take precedence over glob keys (see `event.command.acl`)

### 2. Module/Command No Response

First suspect scope rather than the module itself:

```python
from ErisPulse import sdk

print(sdk.scope.is_allowed(event.get_platform(), bot_id, "MyModule", session_id))
print(sdk.scope.is_identity_allowed(event.get_platform(), bot_id, session_id, user_id))
print(sdk.scope.stats())   # module_filtered / identity_denied > 0 indicates silent filtering
```

Filtered is **silent** (module and identity dimensions do not reply, preventing rule exposure), but statistics accumulate;
ACL-denied command dimensions reply "permission denied" explicitly.

### 3. Outbound Action Denied When Troubleshooting

```python
from ErisPulse import sdk

print(sdk.scope.get("actions.MyModule"))
print(sdk.scope.stats())   # action_denied > 0 indicates some calls were blocked
```

Blocking is **explicit**: denied calls return a standard failure response (`retcode = 34601`) without initiating network requests.

### 4. Session Identifier Isolation Across Platforms

`(platform, session_id)` combination is the unique identifier. `scope.sessions.onebot11."789"`
only applies to onebot11, not affecting a session with `789` on telegram. Identity dimension user keys are the same.

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
#   "adapters": {                                  # Adapter → Bot → scope
#     "onebot11": {
#       "status": "started", "enabled": True,
#       "bots": {"123456": {"status": "online", "scope": {...}}},
#       "scope": {"modules": [...], "blocked": [...]},
#     }
#   },
#   "scope": {                                     # Scope (modules / identity / outbound actions)
#     "platforms": {...}, "bots": {...}, "sessions": {...},
#     "identity": {"adapters": {...}, "bots": {...}, "sessions": {...}, "users": {...}},
#     "actions": {...},
#   },
# }
```

- Module topology aggregates resources registered by the module, including commands, event handlers, HTTP/WS/SSE routes, and lifecycle hooks, useful for drawing a module resource tree.
- Adapter topology aggregates status of each adapter, status of subordinate bots, and platform-level/Bot-level scope bindings (module dimension).