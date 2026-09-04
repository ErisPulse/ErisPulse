# Unified Control Plane (scope)

> [!NOTE]
> This feature requires ErisPulse **2.8.0+**.

The unified control plane answers six questions: **which modules are available, whether events from whom are accepted, who can execute a certain command, what text a module processes, which implementation parameters are overridden, and which outbound calls modules are prohibited from initiating**. Control is entirely given to the user: at the **upper level** of module / adapter / command / processor registration (configuration `ErisPulse.scope` or runtime `sdk.scope`), events are automatically read and executed at each level.

The control plane consolidates the original multiple permission systems and serves as the **only** entry point for permissions/access control in version 2.8.0:

| Dimension | What to control | Rejection behavior | Configuration path |
|------|---------|---------|---------|
| **① Module** | Which modules are available (platform / Bot / session three levels) | Silent ignore (no reply, no claim) | `scope.platforms / bots / sessions` |
| **② Identity** | Whether to accept events (adapter / Bot / session / user four levels) | Complete discard at the entry (silent) | `scope.identity.*` |
| **③ Command** | Who can execute a certain command (command names support glob) | Reply with "insufficient permissions" (explicit) | `scope.commands` |
| **④ Handler** | Which text a module's event handler processes | Do not trigger (silent) | `scope.handlers` |
| **⑤ Override** | Override module/command implementation parameters (master/hidden/aliases/prefix) | —— (only change parameters) | `scope.overrides` |
| **⑥ Outbound Actions** | Prohibit modules from sending messages / calling standard APIs / handling requests | Fail response (`retcode=34601`) | `scope.actions` |

{!--< tips >!--}
1. Import the singleton via `from ErisPulse.Core import scope` (`sdk.scope` refers to the same object)
2. `scope.is_allowed(platform, bot_id, module, session_id)` checks if a module is available
3. `scope.is_identity_allowed(platform, bot_id, session_id, user_id)` checks if an event is allowed
4. `scope.allow_user("roll*", platform, uid)` / `deny_user(...)` command ACL (supports glob)
5. `scope.override("MyModule", "restart", master=True)` overrides implementation parameters
6. `scope.set_action("MyModule", "send", False)` prohibits a module from replying/sending messages
7. `scope.get_stats()` checks filtering statistics; `scope.get_topology()` checks topology
{!--< /tips >!--}

## Matching Entry Syntax (Unified Across the System)

All "name lists" in the control plane (module names, identity keys, command names) share the same matching syntax (via `ErisPulse.Core.text_match`):

| Syntax | Example | Description |
|------|------|------|
| Exact name | `"Chat"` | Full value comparison, **case-insensitive** |
| Glob | `"Tool*"`、`"spam_*"` | `*` for arbitrary string / `?` for single character / `[seq]` for character set, case-insensitive |
| Regular Expression | `"re:^Danger.*"` | Declare with `re:` prefix, match using `re.search`, default case-insensitive |

- Invalid regular expressions **silently degrade** to "no match" (no error thrown, no crash)
- Decorator parameters (`pattern=` / `regex=`) have fixed semantics: `pattern` is glob, `regex` is the regular expression source (no `re:` prefix); regular expression entries in control plane configurations **must** have the `re:` prefix

## Global Default: `default_allow`

`default_allow` is the **single global** default switch (default `true`), affecting three decision dimensions uniformly:

- **Module dimension**: If no binding is matched → `default_allow` decides allow/deny
- **Identity dimension**: If no policy is matched → `default_allow` decides allow/deny
- **Command dimension**: If no ACL is configured → `default_allow=true` delegates to the developer's default permission chain; `false` (strict mode) denies commands with no configured ACL

Setting it to `false` enables "implicit deny" strict mode: whitelist-style management, **all unexplicitly allowed are denied**.

> **Exception**: The **outbound actions** dimension is **not** affected by `default_allow`—it is an independent tightening switch, defaulting to full allow, only explicitly `false` disables (framework-layer owner-empty calls are always allowed). This strict global mode does not accidentally cut off all module message replies.

## Configuration File

```toml
[ErisPulse.scope]
default_allow = true        # Global default (false = implicit deny strict mode)
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
hidden = true                 # Hide in help
aliases = ["rs"]              # Append alias
prefix = "!"                  # Append trigger prefix

# ── ⑥ Outbound Actions Dimension (default allow all, only explicitly disable) ──
[ErisPulse.scope.actions.MyModule]
send = false                  # Prohibit MyModule from replying/sending messages
api = false                   # Prohibit MyModule from calling standard APIs (including call escape hatch)
request = false               # Prohibit MyModule from handling request operations accept/reject
```

## ① Module Dimension

Answers "which modules are available in a certain context." By default, all are open; filtering starts only after configuration binding, and **modules and adapters require no changes**.

```mermaid
flowchart TD
    A["Event arrives at a module's handler/command"] --> B{"scope.is_allowed<br/>(platform, bot, module, session)"}
    B --> C{"Find effective binding<br/>Session level > Bot level > Platform level"}
    C -->|"Matched"| D["blocked matched → deny<br/>modules non-empty → only whitelist allowed<br/>both empty → default_allow"]
    C -->|"Not matched"| E["default_allow (default true = allow)"]
    D -->|"Denied"| Z["Silently ignore<br/>No reply, no claim (only TRACE logs visible, core.scope.denied)"]
```

- **Resolution priority: session level > bot level > platform level**, higher priority bindings **fully override** lower priority ones
- **Silent semantics**: Commands and handlers of filtered modules do not trigger, reply, or claim (prevent cross-command mis-matching), only TRACE-level logs are visible (core.scope.denied)
- **Framework-level handlers** (scope_exempt=True or owner is empty) are unaffected; modules with empty names (framework-level resources) are always allowed
- **Session-aware help and command query**: Command query APIs (command.help / get_command / get_commands / get_group_commands / get_visible_commands, and module.get_commands_overview) support optional event= or explicit platform= / bot_id= / session_id= keywords—commands from modules not available in the current session no longer appear in results (get_command returns None, single command help is treated as "unregistered", consistent with silent semantics); if no context is provided, full behavior is maintained. The help/hidden fields returned by command queries are merged and overridden effective values (user priority)

## ② Identity Dimension (Event Admission)

Answers "whose events are accepted." Events rejected at the **distribution entry are completely discarded**—they do not enter middleware or any handler (including framework-level), only TRACE-level logs are visible (core.scope.identity_denied).

- **Resolution priority: user > session > bot > adapter**, take the most specific configured policy; deny takes precedence over allow
- Each level binding is a binary policy: `{ allow = true }` or `{ deny = true }`
- User keys support glob / regex (e.g. `"spam_*"` to block a batch of spam users)
- Typical usage—上级 deny, individual allow for "exceptional allowance":

```toml
[ErisPulse.scope.identity.adapters.onebot11]
deny = true
[ErisPulse.scope.identity.users.onebot11]
allow = ["u_admin"]   # Even if adapter-level denied, events from u_admin are allowed
```

## ③ Command Dimension (Command ACL)

Answers "who can execute a certain command." Decision order: **deny matched → deny; allow whitelist non-empty and not matched → deny; neither configured → follow default_allow** (true delegates to developer's default permission chain). Denied commands will explicitly reply with "insufficient permissions."

- Command names support glob: `"roll*"` one rule covers a family of commands such as `roll` and `roll_dice`
- Exact keys take precedence over glob keys (`commands.roll` matched, no need to check `commands."roll*"`)
- User identifier format `"platform:user_id"` (consistent with framework owner system)
- This dimension is **only an additional gate on the user side**, and is chained with the command's `master` / `permission` parameters: ACL passes, then the default permission chain declared by the developer is still followed (this default chain can be adjusted via ⑤ override)

## ④ Handler/Text Dimension

Filters "which text a module processes": after configuring `pattern` / `regex` for a module, all its event handlers only trigger when the text matches (AND with code-level conditions, both must be satisfied). Suitable for narrowing the trigger range of a module without changing its code.

```toml
[ErisPulse.scope.handlers.ChatModule]
pattern = "闲聊*"     # ChatModule's handlers only respond to messages starting with "闲聊"
```

## ⑤ Implementation Parameter Override

Overrides implementation parameters at the **upper level** of module/command registration, without modifying module code:

```toml
[ErisPulse.scope.overrides.MyModule.restart]
master = true      # Override to only framework owner (can also set false to open developer's owner restriction)
hidden = true      # Hide in help list
aliases = ["rs"]   #生效别名
```

> Override follows **user priority**: The developer's declared `master` / `hidden` etc. are just default values; after the user configures explicitly here, the user's configuration takes precedence (can tighten or loosen). Override only changes **implementation parameters** (master / hidden / aliases / prefix / help / usage etc.), command execution decision and help rendering share the same merged result: `hidden` override immediately changes help list visibility, `help` / `usage` override immediately changes `/help` display. **Disabling a command is not here**—unify through command dimension deny (`scope.commands` or `scope.deny_user()`), avoiding two sets of "disable" semantics clashing.

## ⑥ Outbound Actions Dimension (Prohibit Modules from Initiating Outbound Calls)

Constraints on modules **initiating outbound actions**: message sending / standard API actions / request operations. The three types of actions correspond to the underlying DSL: `Event.reply` and `Send` (send), `Api` / `call_api` (api), `Request`'s accept/reject (request). Outbound calls initiated by modules during the event handler execution period carry the module owner, which is uniformly judged by this dimension.

```toml
[ErisPulse.scope.actions.MyModule]
send = false      # Prohibit MyModule from replying/sending messages
api = false       # Prohibit MyModule from calling standard API actions (including call escape hatch)
request = false   # Prohibit Myodule from executing accept/reject on request events
```

Judgment semantics: **Default is full allow**—not configured, or owner is empty (internal framework calls) are all allowed; only when explicitly set to `false` is it denied, and denied calls do not initiate any network requests, directly returning a standard failure response (`retcode = 34601`, see [api-response §5.3](../standards/api-response.md#53-框架扩展返回码34xxx-平台错误段的低三位自定义)) Three actions are independent, any one can be prohibited.

```python
# Runtime API
sdk.scope.set_action("MyModule", "send", False)   # Prohibit sending messages
sdk.scope.is_action_allowed("MyModule", "send")   # False
sdk.scope.unset_action("MyModule", "send")        # Restore allow
sdk.scope.get_action_rules("MyModule")            # {"send": False, "api": True, "request": True}
```

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
sdk.scope.bind_module("onebot11", blocked=["Danger"])             # Platform level
sdk.scope.bind_module("onebot11", "123456", "789012345", modules=["Chat"])  # Session level
sdk.scope.bind_module("onebot11", "123456", modules=["Music"], merge=True)  # Merge
sdk.scope.bind_module("onebot11", "123456", modules=["Chat"], persist=False)  # Only runtime
sdk.scope.unbind_module("onebot11", "123456")

# Query
sdk.scope.get("onebot11", "123456")   # {"modules": ["Chat"], "blocked": []}
```

### Identity Dimension

```python
# Check if event is allowed
sdk.scope.is_identity_allowed("onebot11", "123456", "group_9", "u1")

# Bind policy (hierarchy determined by parameters: user > session > bot > adapter)
sdk.scope.bind_identity("onebot11", user_id="u_bad", deny=True)
sdk.scope.bind_identity("onebot11", user_id="spam_*", deny=True)   # glob
sdk.scope.bind_identity("onebot11", "123456", "group_9", allow=True)
sdk.scope.unbind_identity("onebot11", user_id="u_bad")

# Convenient API for user blacklist
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

# Can also be delegated via command system facade (equivalent)
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
sdk.scope.list_bindings()   # All bindings
sdk.scope.get_topology()    # Topology (for Dashboard)
sdk.scope.get_stats()
# {"module_calls": .., "module_filtered": .., "identity_checks": .., "identity_denied": ..,
#  "command_checks": .., "command_denied": .., "action_checks": .., "action_denied": ..,
#  "cache_hits": .., "cache_misses": ..}
sdk.scope.reset_stats()
sdk.scope.clear()           # Clear all bindings (memory-only)
```

## Owner Identity and Custom Identity Source (provider)

The owner system answers "who is the framework owner": The `master=True` parameter of commands and the business layer's `master.is_master()` share the same identity determination, with the determination chain being **configured owner → runtime record → provider chain**.

Owner configuration (`ErisPulse.master.users`, supports global list and per-platform dict) is detailed in the [configuration document](../user-guide/configuration.md#Owner System Configuration); this section focuses on identity determination APIs and extension points.

### Determination and Runtime Addition/Removal

```python
from ErisPulse.Core import master

master.is_master(event)                      # Determine from event
master.is_master("yunhu", "123")             # Explicit determination
master.add("yunhu", "123")                   # Add at runtime (default persistent; persist=False only memory)
master.remove("yunhu", "123")                # Remove (default persistent)
master.list()                                # Aggregate: {"global": [...], "<platform>": [...]}
```

### Custom Identity Source (provider)

In addition to configuration, custom identity sources can be registered: `fn(platform, user_id) -> bool`, which are tried in sequence when built-in identity sources (configuration + runtime records) do not match, and any provider allowing access is considered an owner. Suitable for integrating with adapter administrator interfaces, database roles, and other external identity systems.

Registration entry `master.provider` supports both decorator and function-based writing, and unregistration is uniformly handled by the unregistered function:

```python
from ErisPulse.Core import master

# Method 1: Decorator (persistent identity source, recommended)
@master.provider
def admin_provider(platform, user_id):
    return user_id in {"999"}     # Custom determination logic

master.is_master("yunhu", "999")   # True
admin_provider.unregister()        # Unregister when no longer needed

# Method 2: Function-based (register during module loading / unregister during unloading)
fn = master.provider(admin_provider)
fn.unregister()
```

> Exceptions from provider are caught and skipped, not blocking the identity determination chain. Binding instance methods cannot mount `unregister`, and scenarios requiring registration/unregistration pairing should use **module-level functions**.

### User Priority: Owner Scope is Ultimately Decided by the User

The `master=True` of a command is only a **developer default**: the user can override it in the control plane via `ErisPulse.scope.overrides.<module>.<cmd>.master = true/false` (see above ⑤ Implementation Parameter Override, where explicit user configuration takes effect).

## Cache and Hot Update

- Results of `is_allowed` / `is_identity_allowed` are cached with **LRU** (adjustable via `scope.cache_size`), `bind_*` / `unbind_*` / configuration hot update (`config.updated` / `config.set`) automatically invalidate
- Changes to all dimensions take effect **immediately**, no restart required
- The control plane makes "event-by-event" judgments, not cross-event memory: if the configuration changes, the next event follows the new rule

## Common Issues and Precautions

### 1. Configuration Hierarchy and Overriding

- Module dimension: session level > bot level > platform level, **full override**. To "platform allows Chat, bot adds Music," both must be listed at the bot level
- Identity dimension: user > session > bot > adapter, take the **most specific** configured policy (can do exceptional allowance)
- Command dimension: exact command name takes precedence over glob key

### 2. Prefer the Control Plane over Modifying Module Code

Module declarations are "developer default" (`master=True`, `permission=...`, `pattern=...`); control plane declarations are "user final decision." Implementation parameter overrides follow **user priority**: user's explicit `master = true/false` configuration takes effect directly (can tighten or loosen). Developers' unconfigured restrictions can be tightened by the user; disable/allow control goes through command deny / identity allow.

### 3. Module/Command Not Responding

First suspect the control plane rather than the module itself:

```python
from ErisPulse import sdk

print(sdk.scope.is_allowed(event.get_platform(), bot_id, "MyModule", session_id))
print(sdk.scope.is_identity_allowed(event.get_platform(), bot_id, session_id, user_id))
print(sdk.scope.get_stats())   # module_filtered / identity_denied > 0 indicates silent filtering
```

Filtered is **silent** (module dimension and identity dimension do not reply, avoiding rule exposure), but statistics accumulate; command dimension denied by ACL replies "insufficient permissions" explicitly.

### 4. Session Identifier Isolation Across Platforms

The `(platform, session_id)` combination is the unique identifier. `scope.sessions.onebot11."789"` only affects onebot11, not affecting a session with the same `789` on telegram. The same applies to identity dimension user keys.

## Topology Tree API

`ModuleManager.get_topology()` and `AdapterManager.get_topology()` provide module/adapter ownership relationship data, and `sdk.get_topology()` aggregates them (including the control plane's five dimensions):

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

- Module topology aggregates commands, event handlers, HTTP/WS/SSE routes, and lifecycle hooks registered by the module, facilitating the drawing of module resource trees.
- Adapter topology aggregates the status of each adapter, the status of subordinate bots, and platform-level/Bot-level scope bindings.