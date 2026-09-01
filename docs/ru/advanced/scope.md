# Unified Control Plane (scope)

> [!NOTE]
> This feature requires ErisPulse **2.8.0+**.

The unified control plane answers five questions: **which modules are available, whether events from whom are received, who can execute a certain command, which text a certain module processes, and which implementation parameters are overridden**. Control is entirely given to the user: at the **upper layer** of module / adapter / command / processor registration (configured via `ErisPulse.scope` or runtime `sdk.scope`), the event pipeline automatically reads and executes at each level.

The control plane consolidates the original multiple permission systems and serves as the **sole** entry point for permission/access control in version 2.8.0:

| Dimension | What is controlled | Rejection behavior | Configuration path |
|------|---------|---------|---------|
| **① Module** | Which modules are available (platform / Bot / session three levels) | Silent ignore (no reply, no claim) | `scope.platforms / bots / sessions` |
| **② Identity** | Whether events from whom are received (adapter / Bot / session / user four levels) | Complete discard at entry (silent) | `scope.identity.*` |
| **③ Command** | Who can execute a certain command (command name supports glob) | Reply with "insufficient permissions" (explicit) | `scope.commands` |
| **④ Handler** | Which text a certain module's event handler processes | Not triggered (silent) | `scope.handlers` |
| **⑤ Override** | Override module/command implementation parameters (master/hidden/aliases/prefix) | —— (only change parameters) | `scope.overrides` |

{!--< tips >!--}
1. Import the singleton via `from ErisPulse.Core import scope` (`sdk.scope` is the same object)
2. `scope.is_allowed(platform, bot_id, module, session_id)` determines if the module is available
3. `scope.is_identity_allowed(platform, bot_id, session_id, user_id)` determines if the event is allowed
4. `scope.allow_user("roll*", platform, uid)` / `deny_user(...)` command ACL (supports glob)
5. `scope.override("MyModule", "restart", master=True)` overrides implementation parameters
6. `scope.get_stats()` checks filtering statistics; `scope.get_topology()` checks the five-dimensional topology
{!--< /tips >!--}

## Matching Entry Syntax (Unified Across the System)

All "name lists" in the control plane (module names, identity keys, command names) share the same matching syntax (`ErisPulse.Core.text_match`):

| Syntax | Example | Description |
|------|------|------|
| Exact name | `"Chat"` | Full value comparison, **case-insensitive** |
| Glob | `"Tool*"`、`"spam_*"` | `*` matches any string / `?` matches a single character / `[seq]` matches a character set, case-insensitive |
| Regular Expression | `"re:^Danger.*"` | Declared with `re:` prefix, matches via regular expression `search`, default case-insensitive |

- Invalid regular expressions **silently degrade** to "no match" (no error thrown, no crash)
- Decorator parameters (`pattern=` / `regex=`) have fixed semantics: `pattern` is glob, `regex` is the raw regular expression (no `re:` prefix); regular expression entries in control plane configurations **must** have the `re:` prefix

## Global Fallback: `default_allow`

`default_allow` is the **global** fallback switch (default `true`), which uniformly affects three decision dimensions:

- **Module dimension**: If no binding is matched → `default_allow` determines allow / deny
- **Identity dimension**: If no strategy is matched → `default_allow` determines allow / deny
- **Command dimension**: If no ACL is configured → `default_allow=true` passes to the developer's default permission chain; `false` (strict mode) denies unconfigured commands

Setting it to `false` enables "implicit deny" strict mode: white-list management, **all unexplicitly allowed are denied**.

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

# ── ③ Command dimension (command names support glob) ──
[ErisPulse.scope.commands."roll*"]
allow = ["onebot11:u_vip"]    # User identifier "platform:user_id"
deny = ["onebot11:u_bad"]

# ── ④ Handler/Text dimension ──
[ErisPulse.scope.handlers.MyModule]
pattern = "签到*"             # AND with code-level pattern/regex conditions
regex = "re:\\d+\\s*元"

# ── ⑤ Implementation Parameter Override ──
[ErisPulse.scope.overrides.MyModule.restart]
master = true                 # Only framework owner can use
hidden = true                 # Hidden in help
aliases = ["rs"]              # Additional alias
prefix = "!"                  # Additional trigger prefix
```

## ① Module Dimension

Answers the question: "In a certain context, which modules are available." By default, all are open; filtering starts only after binding is configured. **No changes are needed for modules and adapters**.

```mermaid
flowchart TD
    A["Event arrives at a module's handler/command"] --> B{"scope.is_allowed<br/>(platform, bot, module, session)"}
    B --> C{"Find effective binding<br/>Session level > Bot level > Platform level"}
    C -->|"Matched"| D["blocked matched → deny<br/>modules non-empty → only whitelist allowed<br/>both empty → default_allow"]
    C -->|"Not matched"| E["default_allow (default true = allow)"]
    D -->|"Deny"| Z["Silent ignore<br/>(no reply, no claim, only TRACE log visible)"]
```

- **Resolution priority: session level > Bot level > platform level**, with higher priority bindings **completely overriding** lower ones
- **Silent semantics**: Commands and handlers of filtered modules do not trigger, reply, or claim (prevents cross-command mis-matches), visible only in TRACE-level logs (`core.scope.denied`)
- **Framework-level handlers** (`scope_exempt=True` or owner is empty) are unaffected; modules with empty names (framework-level resources) are always allowed

## ② Identity Dimension (Event Admission)

Answers the question: "Whose events are received." Events denied at the **admission entry** are completely discarded—they do not enter middleware or any handler (including framework-level), visible only in TRACE-level logs (`core.scope.identity_denied`).

- **Resolution priority: user > session > Bot > adapter**, taking the most specific configured strategy; deny takes precedence over allow
- Each level binding is a binary strategy: `{ allow = true }` or `{ deny = true }`
- User keys support glob / regex (e.g., `"spam_*"` to block a group of spam users)
- Typical usage—上级 deny, personal allow for "exceptional allowance":

```toml
[ErisPulse.scope.identity.adapters.onebot11]
deny = true
[ErisPulse.scope.identity.users.onebot11]
allow = ["u_admin"]   # Even if adapter-level denied, u_admin's events are still allowed
```

## ③ Command Dimension (Command ACL)

Answers the question: "Who can execute a certain command." The decision order: **deny matched → deny; allow whitelist non-empty and not matched → deny; neither configured → follow `default_allow`** (`true` passes to the developer's default permission chain). Denied commands will explicitly reply with "insufficient permissions."

- Command names support glob: `"roll*"` covers a group of commands like `roll`, `roll_dice`, etc.
- Exact keys take precedence over glob keys (`commands.roll` matched does not check `commands."roll*"`)
- User identifier format `"platform:user_id"` (consistent with the framework owner system)
- This dimension is **only an additional gate on the user side**, connected with the command's `master` / `permission` parameters: After ACL passes, the default permission chain declared by the developer is still followed

## ④ Handler/Text Dimension

Filters "which text a module processes": After configuring `pattern` / `regex` for a module, all event handlers of that module only trigger when the text matches (AND with code-level conditions, both must be satisfied). Suitable for narrowing the trigger range without modifying module code.

```toml
[ErisPulse.scope.handlers.ChatModule]
pattern = "闲聊*"     # ChatModule's handlers only respond to messages starting with "闲聊"
```

## ⑤ Implementation Parameter Override

Overrides implementation parameters at the **upper level** of module/command registration, without modifying module code:

```toml
[ErisPulse.scope.overrides.MyModule.restart]
master = true      # Override to only framework owner
hidden = true      # Hidden in help list
aliases = ["rs"]   #生效别名
```

> Overriding only changes **implementation parameters** (master / hidden / aliases / prefix / help / usage, etc.). **Disabling a command is not done here**—use the command dimension deny (`scope.commands` or `scope.deny_user()`), to avoid conflicting semantics of "disable."

## Runtime API

### Module Dimension

```python
from ErisPulse import sdk

# Check
sdk.scope.is_allowed("onebot11", "123456", "Chat")
sdk.scope.is_allowed("onebot11", "123456", "Chat", "789012345")
sdk.scope.is_allowed("onebot11", "123456", None)      # Framework-level resource -> True

# Bind / Unbind
sdk.scope.bind_module("onebot11", "123456", modules=["Chat", "Tool*"])
sdk.scope.bind_module("onebot11", blocked=["Danger"])             # Platform-level
sdk.scope.bind_module("onebot11", "123456", "789012345", modules=["Chat"])  # Session-level
sdk.scope.bind_module("onebot11", "123456", modules=["Music"], merge=True)  # Merge
sdk.scope.bind_module("onebot11", "123456", modules=["Chat"], persist=False)  # Runtime only
sdk.scope.unbind_module("onebot11", "123456")

# Query
sdk.scope.get("onebot11", "123456")   # {"modules": ["Chat"], "blocked": []}
```

### Identity Dimension

```python
# Check if event is allowed
sdk.scope.is_identity_allowed("onebot11", "123456", "group_9", "u1")

# Bind strategy (hierarchy determined by parameters: user > session > bot > adapter)
sdk.scope.bind_identity("onebot11", user_id="u_bad", deny=True)
sdk.scope.bind_identity("onebot11", user_id="spam_*", deny=True)   # glob
sdk.scope.bind_identity("onebot11", "123456", "group_9", allow=True)
sdk.scope.unbind_identity("onebot11", user_id="u_bad")

# Blacklist convenience API
sdk.scope.block_user("onebot11", "u_bad")
sdk.scope.is_user_blocked("onebot11", "u_bad")
sdk.scope.get_blocked_users()        # {"onebot11": ["u_bad"]}
sdk.scope.unblock_user("onebot11", "u_bad")
```

### Command Dimension

```python
sdk.scope.is_command_allowed("roll", "onebot11", "u1")
sdk.scope.allow_user("roll*", "onebot11", "u_vip")   # Command name supports glob
sdk.scope.deny_user("roll*", "onebot11", "u_bad")
sdk.scope.get_acl("roll*")
sdk.scope.remove_acl("roll*")

# Can also use command system facade (equivalent delegation)
from ErisPulse.Core.Event import command
command.allow_user("restart", "onebot11", "123456")
```

### Handler and Override Dimensions

```python
sdk.scope.bind_handler("MyModule", pattern="签到*", regex=r"\d+号")
sdk.scope.unbind_handler("MyModule")

sdk.scope.override("MyModule", "restart", master=True, hidden=True)
sdk.scope.get_override("MyModule", "restart")
sdk.scope.remove_override("MyModule", "restart")
```

### General

```python
sdk.scope.list_bindings()   # Full five-dimensional bindings
sdk.scope.get_topology()    # Five-dimensional topology (for Dashboard)
sdk.scope.get_stats()
# {"module_calls": .., "module_filtered": .., "identity_checks": .., "identity_denied": ..,
#  "command_checks": .., "command_denied": .., "cache_hits": .., "cache_misses": ..}
sdk.scope.reset_stats()
sdk.scope.clear()           # Clear all bindings (in-memory only)
```

## Cache and Hot Update

- `is_allowed` / `is_identity_allowed` results are cached with **LRU cache** (`scope.cache_size` is adjustable), invalidated automatically by `bind_*` / `unbind_*` / configuration hot update (`config.updated` / `config.set`)
- All dimension configurations take effect **immediately**, no restart needed
- The control plane makes **event-by-event** decisions, without cross-event memory: configuration changes take effect on the next event

## Common Issues and Notes

### 1. Configuration Hierarchy and Overriding

- Module dimension: session level > Bot level > platform level, **completely overrides**. To "allow Chat at platform level, and add Music at Bot level," both must be listed at the Bot level
- Identity dimension: user > session > Bot > adapter, taking the **most specific** configured strategy (can be used for exceptional allowance)
- Command dimension: exact command name takes precedence over glob key

### 2. Prefer Control Plane Over Module Code Changes

Module declarations are "developer defaults" (`master=True`, `permission=...`, `pattern=...`); control plane declarations are "user final decisions." When conflicts occur, the **more restrictive control plane takes precedence** (e.g., if the developer did not set master, the user can override `master = true` to tighten; the user cannot loosen the developer's explicit restrictions via override—control over enable/disable goes through command deny / identity allow).

### 3. Module/Command Not Responding

First suspect the control plane rather than the module itself:

```python
from ErisPulse import sdk

print(sdk.scope.is_allowed(event.get_platform(), bot_id, "MyModule", session_id))
print(sdk.scope.is_identity_allowed(event.get_platform(), bot_id, session_id, user_id))
print(sdk.scope.get_stats())   # module_filtered / identity_denied > 0 indicates silent filtering
```

Filtered results are **silent** (no reply for module and identity dimensions, to avoid exposing rules), but statistics are accumulated; command dimension denied by ACL will explicitly reply with "insufficient permissions."

### 4. Session Identifier Isolation Across Platforms

The combination of `(platform, session_id)` is the unique identifier. `scope.sessions.onebot11."789"` only applies to onebot11, not affecting the session with the same `789` on telegram. The same applies to identity dimension user keys.

## Topology Tree API

`ModuleManager.get_topology()` and `AdapterManager.get_topology()` provide module/adapter ownership relationship data, and `sdk.get_topology()` aggregates all (including control plane `scope` five dimensions):

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
#   "scope": {                                     # Unified control plane (five dimensions)
#     "platforms": {...}, "bots": {...}, "sessions": {...},
#     "identity": {"adapters": {...}, "bots": {...}, "sessions": {...}, "users": {...}},
#     "commands": {...}, "handlers": {...}, "overrides": {...},
#   },
# }
```

- Module topology aggregates commands, event handlers, HTTP/WS/SSE routes, and lifecycle hooks registered by the module, useful for drawing module resource trees.
- Adapter topology aggregates the status of each adapter, the status of subordinate Bots, and platform-level/Bot-level scope bindings.