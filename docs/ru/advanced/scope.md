# Scope

> [!NOTE]
> This feature requires ErisPulse **2.8.0+**.

Scope answers four questions: **which modules are available, whether events from whom are received, what text is processed by a module, and what a module can do externally**. Control is fully handed over to the user: the **upper layer** (configured via `ErisPulse.scope` or runtime `sdk.scope`) where modules / adapters / processors / outbound calls are registered, declares these uniformly. The event pipeline automatically reads and executes these at entry, processor filtering, and outbound gateways.

| Dimension | What is controlled | Rejection behavior | Configuration path |
|------|---------|---------|---------|
| **① Module** | Which modules are available (platform / Bot / session three levels) | Silently ignored (no reply, no claim) | `scope.platforms / bots / sessions` |
| **② Identity** | Whether to receive events (adapter / Bot / session / user four levels) | Completely discarded at entry (silent) | `scope.identity.*` |
| **③ Outbound** | Which outbound calls a module can initiate (messages / API / requests, method-level whitelists and blacklists) | Failed response (`retcode=34601`) | `scope.actions` |

> **Related system**: Commands are special message event processors, their user allow/deny lists (ACL) and implementation parameter overrides are self-contained by the command system (`ErisPulse.event.command`), see [Introduction to Event Handling](../getting-started/event-handling.md) and [Configuration Guide](../user-guide/configuration.md).

{!--< tips >!--}
1. Import the singleton via `from ErisPulse.Core import scope` (same object as `sdk.scope`)
2. Check: `scope.is_allowed(...)` / `scope.is_identity_allowed(...)` /
   `scope.is_action_allowed(...)` correspond to the three gates ①②③
3. Read/write: dimension-specific parameter methods (IDE can auto-complete) —
   `scope.set_module(...)` / `scope.set_identity(...)` / `scope.set_action(...)`;
   There are also dictionary-style fallback methods `scope.get(path)` / `scope.set(path, v)` / `scope.delete(path)`
4. Event processor text condition overrides are found in
   [Introduction to Event Handling · Event Overriding](../getting-started/event-handling.md#event-overriding-overwrite-the-behavior-of-any-event-type-without-modifying-the-module-code);
   Command ACL / parameter overrides are found in [Introduction to Event Handling](../getting-started/event-handling.md)
{!--< /tips >!--}

## Matching Entry Syntax (Unified Across the System)

All "name lists" in scope (module names, identity keys, outbound entries) share the same matching syntax (via `ErisPulse.Core.text_match`):

| Syntax | Example | Description |
|------|------|------|
| Exact name | `"Chat"` | Full value comparison, **case-insensitive** |
| glob | `"Tool*"`、`"spam_*"` | `*` for any string / `?` for a single character / `[seq]` for character set, case-insensitive |
| Regular expression | `"re:^Danger.*"` | Declared with `re:` prefix, matches using regular expression `search`, default case-insensitive |

- Invalid regular expressions **silently degrade** to "no match" (no error thrown, no crash)
- Decorator parameters (`pattern=` / `regex=`) have fixed semantics: `pattern` is glob, `regex` is the raw regular expression (without `re:` prefix); regular expression entries in scope configuration **must** have the `re:` prefix

## Global Fallback: `default_allow`

`default_allow` is the **single global** fallback switch (default `true`), affecting two decision dimensions:

- **Module dimension**: If no binding is matched → `default_allow` decides allow/deny
- **Identity dimension**: If no policy is matched → `default_allow` decides allow/deny

Setting it to `false` enables "implicit deny" strict mode: whitelist-style management,
**everything not explicitly allowed is denied**.

> **Exception**: The outbound dimension is **not affected** by `default_allow`—it is an independent tightening switch,
> defaulting to full allow, with restrictions only via explicit rules (framework-level owner-empty calls are always allowed).
> This strict global mode won't accidentally cut off all module message replies.
> Command ACL has a separate `ErisPulse.event.command.default_allow` fallback, independent of others.

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

# ── ③ Outbound dimension (default allow all, restrict only via explicit rules) ──
[ErisPulse.scope.actions.MyModule]
send = { deny = true }                                    # Disable all sending
api = { allow = ["get_*"] }                               # Allow only query-type standard APIs
request = { deny = true }                                 # Disable request handling
```

## ① Module Dimension

Answers "which modules are available in a given context." By default, all are open; filtering starts only after configuration binding,
**no changes are needed for modules or adapters**.

```mermaid
flowchart TD
    A["Event arrives at a module's handler/command"] --> B{"scope.is_allowed<br/>(platform, bot, module, session)"}
    B --> C{"Parse chain: session-level > Bot-level > platform-level<br/> (if sub-level merge = true, merge entries step by step)"}
    C -->|"Matched"| D["blocked matched → deny<br/>modules non-empty → only whitelist allowed<br/>both empty → default_allow"]
    C -->|"Not matched"| E["default_allow (default true = allow)"]
    D -->|"Denied"| Z["Silently ignored<br/> (no reply, no claim, only TRACE log visible)"]
```

- **Parse priority: session-level > Bot-level > platform-level**, higher priority bindings **fully override** lower ones;
  if a sub-level binding sets `merge = true`, it instead performs a **per-entry union** with lower levels (both `modules` and `blocked` are merged separately,
  `merge` itself is a control key and not counted as an entry)
- **Silent semantics**: Commands and processors of filtered modules do not trigger, reply, or claim (to prevent cross-command mis-matches),
  only TRACE-level logs are visible (`core.scope.denied`)
- **Framework-level processors** (`scope_exempt=True` or owner is empty) are unaffected; modules with empty names (framework-level resources) are always allowed
- **Session-aware help and command queries**: Command query APIs (`command.help` /
  `get_command` / `get_commands` / `get_group_commands` / `get_visible_commands`,
  and `module.get_commands_overview`) all support optional `event=` or explicit
  `platform=` / `bot_id=` / `session_id=` keywords—commands from modules unavailable in the current session
  no longer appear in the results (`get_command` returns None, single command help is treated as "not registered",
  consistent with silent semantics); if no context is provided, full behavior is maintained

### Binding Inheritance (merge)

The default full override semantics are clear and predictable; when you need to **append** to an upper-level binding, set `merge = true` in the sub-level:

```toml
[ErisPulse.scope.platforms.onebot11]
modules = ["Chat", "Tool"]      # Platform-level: allow Chat, Tool

[ErisPulse.scope.bots.onebot11."123456"]
modules = ["Music"]
merge = true                    # The actual effect for this Bot = ["Chat", "Tool", "Music"]
```

- **Merge rules**: `modules` and `blocked` each take a **union**; within a binding, `blocked` still takes precedence over `modules`
- **Chained merging**: Platform → Bot → Session are layered step by step, each level independently decides `merge` or override

## ② Identity Dimension (Event Admission)

Answers "whose events are received." Events that are denied are **completely discarded at the distribution entry**—
they do not enter middleware or any processor (including framework-level), with only TRACE-level logs visible (`core.scope.identity_denied`).

- **Parse priority: user > session > Bot > adapter**, take the most specific configured policy; deny takes precedence over allow
- Each level of binding is a binary policy: `{ allow = true }` or `{ deny = true }`
- User keys support glob / regular expressions (e.g. `"spam_*"` to block a batch of spam users)
- Typical use case—上级 deny, individual allow for "exception allow":

```toml
[ErisPulse.scope.identity.adapters.onebot11]
deny = true
[ErisPulse.scope.identity.users.onebot11]
allow = ["u_admin"]   # Even if adapter-level denied, events from u_admin are still allowed
```

## ③ Outbound Dimension (Limiting Module Outbound Calls)

Constraints on modules **initiating outbound actions**: message sending / standard API actions / request operations.
Three types of actions correspond to the underlying DSL: `Event.reply` and `Send` (send), `Api` / `call_api` (api), and
`Request`'s accept/reject (request). Outbound calls initiated by modules during event handler execution
carry the module owner, and are uniformly judged by this dimension.

### Rule Forms (Inline Tables)

Each action's rule is an inline table: `{ allow = [...], deny = true|[...] }`.
Only one rule per action is allowed (TOML keys cannot repeat, choose between full deny and fine-grained):

```toml
[ErisPulse.scope.actions.MyModule]
send = { deny = true }                                  # Disable all sending (Event.reply / Send DSL)
# Or fine-grained method-level: send = { allow = ["Text", "Image*"], deny = ["File"] }
api = { allow = ["get_*"] }                             # Allow only query-type standard APIs
# Or action-level blacklist: api = { deny = ["set_*", "leave_*"] }
request = { deny = true }                               # Disable request handling accept/reject
```

- `send` entries match **send method names** (`Text` / `Image` / `File` ...),
  `api` entries match **standard action names** (`get_group_info` / `set_group_name` ...)
- Entries support exact names / glob / `re:` regex (consistent with the unified system syntax, case-insensitive)
- Writing a single string in `allow` is equivalent to a single-item list: `send = { allow = "Text" }`

### Decision Semantics

**Default is full allow**—unconfigured, or owner is empty (internal framework calls) are allowed.
After configuration, rules are evaluated in the following order:

1. `deny = true` → deny
2. `deny` list matches call name → deny
3. `allow` list is non-empty and call name is not matched (or call has no name) → deny
4. Otherwise, allow

Denied calls do not initiate any network requests, directly returning a standard failure response
(`retcode = 34601`, see [api-response §5.3](../standards/api-response.md#53-framework-extended-return-codes-34xxx-custom-platform-error-segment-lower-three-digits)).

```python
# Runtime API
sdk.scope.set_action("MyModule", "send", deny=True)              # Disable all message sending
sdk.scope.set_action("MyModule", "send", allow=["Text"])         # Allow only text sending
sdk.scope.is_action_allowed("MyModule", "send", name="Image")    # False
sdk.scope.is_action_allowed("MyModule", "api", name="get_user_info")  # Evaluate by rules
sdk.scope.delete_action("MyModule", "send")                      # Re-enable
sdk.scope.get_action("MyModule", "send")                         # Current rule for this action
```

## Runtime API

The runtime API for scope is divided into three layers: **decision** (three questions), **dimension-specific read/write** (per dimension `set` / `get` / `delete` parameterized methods, fully type-annotated, IDE can auto-complete), and **dictionary-style fallback** (dot-separated path to reach any section).

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
scope.is_action_allowed("MyModule", "send", name="Image")      # Fine-grained method-level
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

> `merge=True` is **write-time union** (merges entries with existing bindings at this level); `merge = true` configuration keys at parse time across levels are described above in [Binding Inheritance](#binding inheritance-merge)—these are independent mechanisms.

> **Runtime binding (persist=False) semantics**: Runtime bindings are saved in a separate overlay layer,
> **any subsequent configuration writes / hot reloads of configuration files will not overwrite them** (the configuration tree is rebuilt and automatically reapplied in order, including runtime deletions). They are not persisted, and are lost after process restart; when a module is unloaded, runtime bindings written by that module are cleaned up. Subsequent `persist=True` writes (user-persistent semantics) to the same path will replace runtime rules.

### ② Identity Dimension

```python
# Binding policies (hierarchy determined by parameters: user > session > bot > adapter; allow / deny are mutually exclusive)
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
scope.set_action("MyModule", "api", deny=["set_*", "leave_*"])     # Disable management-type APIs

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

### Advanced: Dictionary-style Dot-Path Fallback

Dimension-specific methods cover daily scenarios; when you need to directly access any node (or future added dimensions),
use the dictionary-style API—`get` / `set` / `delete` accepts dot-separated paths (deep dict merge, immediate read after write),
and provides `scope[path]` / `scope[path] = v` / `del scope[path]` / `path in scope` protocols:

```python
scope.set("bots.onebot11.123456", {"modules": ["Chat"], "blocked": []})
scope.set("identity.users.onebot11.u_bad", {"deny": True})
scope.get("actions.MyModule.send")

scope["platforms.onebot11"]        # Read (raises KeyError if not exists)
scope["platforms.onebot11"] = {...}  # Write
del scope["platforms.onebot11"]      # Delete
"actions.MyModule" in scope          # Existence check
```

## Cache and Hot Reload

- `is_allowed` / `is_identity_allowed` / `is_action_allowed` results are cached with **LRU** (configurable via `scope.cache_size`),
  invalidated automatically by `set` / `delete` /
  configuration hot reload (`config.updated` / `config.set`)
- All dimension configurations take effect **immediately** without restart
- Scope is evaluated **per event**, with no cross-event memory: configuration changes take effect on the next event

## Configuration Format Validation

During loading / hot reload, configuration format is validated per section: type errors (e.g. `platforms` written as a string), invalid outbound rules (e.g. `allow` written as a number), unknown action names, unknown top-level keys (e.g. `alow` with a typo) will output **WARNING** and ignore the corresponding section / entry, while other valid configurations remain effective—incorrect writing no longer silently fails.

## Common Issues and Notes

### 1. Configuration Hierarchy and Overriding

- Module dimension: session-level > Bot-level > platform-level, **full override** (sub-level `merge = true` means per-entry union).
  If you want "platform allows Chat, Bot adds Music," you can set `merge = true` in the Bot-level binding, or list both
- Identity dimension: user > session > Bot > adapter, take the **most specific** configured policy (can be used for exception allow)
- Command user allow/deny lists: exact command names take precedence over glob keys (see `event.command.acl`)

### 2. Module/Command Not Responding

First suspect scope rather than the module itself:

```python
from ErisPulse import sdk

print(sdk.scope.is_allowed(event.get_platform(), bot_id, "MyModule", session_id))
print(sdk.scope.is_identity_allowed(event.get_platform(), bot_id, session_id, user_id))
print(sdk.scope.stats())   # module_filtered / identity_denied > 0 indicates silent filtering
```

Filtered is **silent** (module and identity dimensions do not reply, to avoid exposing rules), but statistics are accumulated;
commands denied by ACL reply "insufficient permissions."

### 3. Outbound Action Denied When Troubleshooting

```python
from ErisPulse import sdk

print(sdk.scope.get("actions.MyModule"))
print(sdk.scope.stats())   # action_denied > 0 indicates some calls were blocked
```

Blocking is **explicit**: denied calls return a standard failure response (`retcode = 34601`, no network request initiated).

### 4. Session Identifier Isolation Across Platforms

The `(platform, session_id)` combination is the unique identifier. `scope.sessions.onebot11."789"` only applies to onebot11, not affecting the session with `789` on Telegram. The same applies to identity dimension user keys.

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
#   "scope": {                                     # Scope (module / identity / outbound actions)
#     "platforms": {...}, "bots": {...}, "sessions": {...},
#     "identity": {"adapters": {...}, "bots": {...}, "sessions": {...}, "users": {...}},
#     "actions": {...},
#   },
# }
```

- Module topology aggregates commands, event handlers, HTTP/WS/SSE routes, and lifecycle hooks registered by the module, useful for drawing module resource trees.
- Adapter topology aggregates status of each adapter, status of subordinate Bots, and platform-level/Bot-level scope bindings (module dimension).

commands