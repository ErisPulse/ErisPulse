# Introduction to Event Handling

This guide introduces how to handle various event types in ErisPulse.

## Event Type Overview

ErisPulse supports the following event types:

| Event Type | Description | Applicable Scenarios |
|---------|------|---------|
| Message Event | Any message sent by a user | Chatbots, content filtering |
| Command Event | Messages starting with a command prefix | Command processing, function entry points |
| Notice Event | System notifications (friend added, group member changes, etc.) | Welcome messages, status notifications |
| Request Event | User requests (friend requests, group invitations) | Automatic request handling |
| Meta Event | System-level events (connection, heartbeat) | Connection monitoring, status checks |

## Message Event Handling

> **Tip**: It is recommended to use `Event` type annotations in event handlers to gain IDE auto-completion and type checking support.

```python
from ErisPulse.Core.Event import Event  # Import Event type for annotation
```

### Listening to All Messages

```python
from ErisPulse.Core.Event import message, Event

@message.on_message()
async def message_handler(event: Event):
    text = event.get_text()
    user_id = event.get_user_id()
    sdk.logger.info(f"Received message from {user_id}: {text}")
```

### Listening to Private Messages

```python
@message.on_private_message()
async def private_handler(event: Event):
    user_id = event.get_user_id()
    await event.reply(f"Hello, {user_id}! This is a private message.")
```

### Listening to Group Messages

```python
@message.on_group_message()
async def group_handler(event: Event):
    group_id = event.get_group_id()
    user_id = event.get_user_id()
    sdk.logger.info(f"Message sent by {user_id} in group {group_id}")
```

### Listening to @ Messages

```python
@message.on_at_message()
async def at_handler(event: Event):
    # Get list of mentioned users
    mentions = event.get_mentions()
    await event.reply(f"You mentioned these users: {mentions}")
```

### Wildcard and Regular Expression Listening

The four message decorators (`on_message` / `on_private_message` / `on_group_message` / `on_at_message`) all support `pattern` (glob wildcard) and `regex` (regular expression). Messages that do not match **will not trigger** the handler:

```python
# Glob wildcard: * for any string, ? for single character, [seq] for character set
@message.on_message(pattern="sign*")
async def signin_handler(event: Event):
    await event.reply("Sign-in successful")

# Regular expression: matches amount
@message.on_message(regex=r"\d+\s*元")
async def price_handler(event: Event):
    await event.reply(f"Received amount: {event.get_text()}")

# Both pattern and regex given → both must match
@message.on_message(pattern="*元", regex=r"\d+\s*元")
async def combined_handler(event: Event):
    pass
```

`wait_reply` also supports these two parameters (see [Wait for Reply Functionality](../developer-guide/modules/event-wrapper.md#wait-for-reply-functionality)).

## Command Event Handling

### Basic Commands

```python
from ErisPulse.Core.Event import command

@command("help", help="Display help information")
async def help_handler(event):
    help_text = """
Available commands:
/help - Display help
/ping - Test connection
/info - View information
    """
    await event.reply(help_text)
```

### Command Aliases

```python
@command(["help", "h"], aliases=["帮助"], help="Display help information")
async def help_handler(event):
    await event.reply("Help information...")
```

Users can call it in any of the following ways:
- `/help`
- `/h`
- `/帮助`

### Command Parameters

```python
@command("echo", help="Echo message")
async def echo_handler(event):
    # Get command arguments
    args = event.get_command_args()
    
    if not args:
        await event.reply("Please enter a message to echo")
    else:
        await event.reply(f"You said: {' '.join(args)}")
```

Parameters retain the original case as entered by the user (even if configured to be case-insensitive, command name matching normalization does not affect parameter content).

### Declarative Parameters and Options (args= / options=)

Manually parsing parameters requires handling type conversion and error messages yourself. After declaring `args=` / `options=`, the framework automatically parses command parameters and **injects them by name** after permission checks pass; when the user input is incorrect, it automatically replies with localized error messages and usage (without throwing an exception crash), and `/help <command>` will automatically display usage:

```python
@command(
    "roll",
    args="<count:int> [sides:int=6]",
    options={"verbose": "-v/--verbose", "label": "--label"},
    help="Roll dice",
)
async def roll_handler(event, count: int, sides: int = 6, verbose: bool = False, label: str = ""):
    total = sum(random.randint(1, sides) for _ in range(count))
    await event.reply(f"Rolled {count} dice with {sides} faces, total points: {total}")
```

`args=` positional parameter syntax: `<count:int>` is required, `[sides:int=6]` is optional (with default value). Supported types:

| Type | Example Input | Description |
|------|---------|------|
| `str` | `hello` | Text (default type) |
| `int` / `float` | `3` / `0.5` | Numeric |
| `bool` | `是` / `yes` / `はい` / `да` / `true` / `no` / `取消` | Boolean value, reuses confirmation word list from `Event.confirm()` |
| `literal` | `<mode:literal=fast|slow>` | Enum, accepts only listed values; optional form defaults to first |
| `duration` | `90s`、`1h30m`、`1d` | Duration, converted to float in seconds |
| `rest` | `<text:rest>` | Remaining text (must be at the end) |

`options=` options are declared in dictionary form: the key is the handler parameter name, the value is the flag form (multiple aliases separated by `/`). Parameters annotated as `bool` are boolean flags (appear as `True`); others (default as `str`) are value options, supporting both `--label hello` and `--label=hello` value formats, with type following the handler annotation. Options are first identified and removed, and the remaining tokens are parsed according to `args=` (the `rest` covers the remaining text after removing options).

**Behavior Points**:

- Permission checks occur before parameter parsing—users without permission will not trigger parsing
- Parsing fails (type mismatch / missing parameters / too many parameters / unknown options) automatically replies with localized error + usage, and the command is still claimed
- The declared parameter names must exist in the handler signature, otherwise a `ValueError` is thrown during registration
- Commands without declaring `args=` / `options=` behave exactly the same (backward compatibility)

### Command Governance (cooldown= / rate_limit= / deprecated=)

Manual cooldown timing, rate limiting window, and deprecation prompts can be replaced by declarations, and the three can be combined arbitrarily.

**Cooldown**—duration syntax is consistent with the `duration` type in `args=` (e.g., `"30s"`, `"1h30m"`, `"1d"`):

```python
@command("daily", cooldown="1d", cooldown_key="user", cooldown_reply="Already signed in today")
async def daily_handler(event):
    await event.reply("Sign-in successful!")
```

**Rate Limit**—sliding window declaration `"count/window"` (e.g., `"5/minute"`, `"10/s"`, `"3/2m"`):

```python
@command("search", rate_limit="5/minute", rate_limit_key="user")
async def search_handler(event):
    await event.reply("Search results")
```

**Deprecated**—automatically replies with deprecation text upon call; `deprecated_reject=True` rejects execution:

```python
@command("oldcmd", deprecated="Please use /newcmd", deprecated_reject=True)
async def old_handler(event): ...
```

Key granularity (`cooldown_key=` / `rate_limit_key=`): `"user"` (default, shared by the same user), `"session"` (shared by the same session, like the same group), `"global"` (shared by all users and sessions).

**Behavior Points**:

- Cooldown / rate limit hit defaults to **silent discard** (symmetrical to scope silence); after declaring `cooldown_reply=` / `rate_limit_reply=`, replying with this text upon hit
- Command hit is claimed immediately—commands hit by governance will not leak to lower priority message handlers
- Governance judgment occurs after all permission checks and parameter parsing pass, before actual execution: users without permission do not trigger, parameter errors do not consume
- When both cooldown and rate limit are declared, cooldown is judged first (cooldown hit does not occupy rate limit window)
- `deprecated=` defaults to replying with the text and **continuing execution**; `deprecated_reject=True` rejects execution (`command.executed` hook records `success=False, error="deprecated"`)
- `/help` list and single command help automatically display deprecation markers and text
- Status is in-process memory, automatically cleaned up when the module is unloaded; cross-process sharing / persistent restart is out of scope
- Declaration is validated at registration (fail-fast): illegal syntax, non-whitelist key granularity value, reply not paired with main declaration all throw `ValueError`

### Handler Throttling (throttle=)

Message handler anti-spam declaration—same key events are processed at most once within the interval, others are silently discarded:

```python
from ErisPulse import sdk

@sdk.message.on_message(throttle="2s", throttle_key="user")
async def handler(event): ...
```

`on_message` / `on_private_message` / `on_group_message` / `on_at_message` all support it; `throttle_key=` uses the same key granularity as command governance (`user` / `session` / `global`), and the duration syntax is consistent with `duration`. Throttling and `pattern=` / `regex=` and other existing conditions are overlapped and effective (all conditions must be satisfied to trigger); discarded within the interval only records TRACE logs; declaration is validated at registration.

### Dependency Injection (Depends)

Common dependencies (database sessions, configuration reading, etc.) can be extracted as dependency functions, and handlers can declare them as default values with `Depends(dependency function)`, and the framework automatically calls the dependency function with the context object and injects it by name before calling:

```python
from ErisPulse.Core import Depends

async def get_session(event):
    return await sdk.module.call("DB", "get_session")

@command("admin")
async def admin_handler(event, db=Depends(get_session)):
    ...
```

Default **request-level caching** is enabled: within the same event distribution, the same dependency function is parsed only once, and all injection points share the result (e.g., `get_db` only creates one database session within one event); it is not reused across requests. You can use `Depends(get_db, use_cache=False)` to disable caching for a single dependency.

Covers all framework injection points—command handlers, event handlers (`message.on_message()` etc.), lifecycle hooks (`sdk.lifecycle.on`), SSE route handlers. The first parameter of the dependency function is the context object of the injection point (event scenario is `Event`, lifecycle is event `data`, route is `HttpRequest` / `SseEmitter`); both synchronous and asynchronous dependency functions can be declared.

**Declaration of other module services** (syntactic sugar):

```python
@command("query")
async def query_handler(event, session=Depends.module("DB", "get_session")):
    ...
```

`Depends.module(module name, method name, *fixed arguments)` is equivalent to calling `sdk.module.call(...)` within the dependency function. Module instantiation (`__init__`) is not covered—the context object is not available during instantiation; for FastAPI hosted HTTP routes, use FastAPI's native `fastapi.Depends`.

**Behavior Points**:

- Declaration is validated at registration (fail-fast): dependency is not callable, or conflicts with `args=` / `options=` parameters throws `ValueError`
- Exceptions thrown by dependency functions are handled in the same way as exceptions thrown by the handler itself (command automatically replies with errors)
- Handlers without declaring `Depends` have zero overhead (no reflection during distribution)
- For HTTP routes hosted by FastAPI, use FastAPI's native `fastapi.Depends`

### Command Groups

```python
@command("admin.reload", group="admin", help="Reload module")
async def reload_handler(event):
    await event.reply("Module reloaded")

@command("admin.stop", group="admin", help="Stop bot")
async def stop_handler(event):
    await event.reply("Bot stopped")
```

The `group` parameter is only used for help list classification; the example above `admin.reload` is a **single command name** (the dot is just a naming style, users need to input `/admin.reload`).

### Subcommands

Command names support **multi-token forms separated by spaces**, implementing subcommands like `/admin add`, `/admin user ban`:

```python
@command("admin", help="Admin commands")
async def admin_handler(event):
    await event.reply("Usage: /admin add | /admin remove")

@command("admin add", help="Add admin")
async def admin_add_handler(event):
    target = event.get_command_args()[0]
    await event.reply(f"Added {target}")

@command("admin remove", aliases=["a remove"], help="Remove admin")
async def admin_remove_handler(event):
    await event.reply("Removed")
```

Matching rules (longest prefix match):

- `/admin add x` takes precedence over `admin add`, `event.get_command_args()` returns `["x"]` (arguments after the subcommand name)
- Only `admin` is registered, `/admin add x` matches `admin`, `get_command_args()` returns `["add", "x"]` (legacy behavior unchanged)
- Alias supports multi-token form (e.g., `a remove`), can also use single-token alias (e.g., `a`) pointing to subcommand
- When parent and child commands are both registered, unregistered subcommands input (e.g., `/admin list x`) fall back to parent command

**Permission Inheritance**: When subcommands do not declare `permission`, they automatically inherit the nearest ancestor command that declared permission on the parent chain—protecting `/admin` automatically protects all its subcommands; the subcommand's own declared permission takes precedence:

```python
def is_admin(event):
    return event.get_user_id() in {"user123"}

@command("admin", permission=is_admin, help="Admin commands")
async def admin_handler(event):
    ...

# No need to repeat permission declaration, automatically inherits is_admin
@command("admin add", help="Add admin")
async def admin_add_handler(event):
    ...
```

Note: `master=True` and `hidden` **do not** inherit, please declare them individually when needed; user ACL (whitelist/blacklist) matches by full command name, glob rules like `"admin*"` can cover entire subcommand groups.

In the `/help` command overview, subcommands will automatically be displayed indented under visible parent commands (e.g., `admin` → `admin add` indented one level, `admin user` → `admin user ban` indented two levels).

### Command Permissions and Access Control

Command permissions are divided into three layers, judged sequentially from top to bottom (if the upper layer rejects, the lower layer is not checked):

```python
# ① Command permission ACL (user-side configuration): user whitelist/blacklist for commands, replies "permission denied" on rejection
# ② master=True — only the framework owner can execute (framework automatically checks, replies "permission denied" on rejection)
@command("restart", master=True, help="Restart module")
async def restart_handler(event):
    await event.reply("Module restarted")

# ③ permission=call function — command's own control logic (returns True to execute)
def is_admin(event):
    return event.get_user_id() in {"user123", "user456"}

@command("panel", permission=is_admin, help="Admin panel")
async def panel_handler(event):
    await event.reply("Welcome to the admin panel")
```

**Command User ACL** (`ErisPulse.event.command.acl`): Users can configure user whitelist/blacklist for any command, command names support exact and glob patterns (e.g., `"roll*"`), replies "permission denied" on rejection:

```toml
# config.toml — only allow 123456 to execute restart; 666 is always rejected
[ErisPulse.event.command.acl.restart]
allow = ["onebot11:123456"]
deny = ["onebot11:666"]
```

Judgment order: `deny` hits → reject; `allow` is non-empty but not hit → reject; when ACL is not configured, follow `event.command.default_allow` (`false` = strict mode, no ACL means reject; `true` means give developers default `master=True` / `permission`). Runtime API (command name supports glob):

```python
from ErisPulse.Core.Event import command

command.allow_user("restart", "onebot11", "123456")   # Allow list
command.deny_user("restart", "onebot11", "666")       # Deny list
command.remove_acl("restart")                          # Clear whitelist/blacklist
command.get_acl("restart")                             # Query current list
```

> Command handlers are imported from event package: `from ErisPulse.Core.Event import command`; can also be accessed via SDK event package: `sdk.Event.command` (both are the same singleton). In modules, they are usually already imported with command decorators (`from ErisPulse.Core.Event import command`).

Cross-command / cross-user **event-level** access control (whether to receive messages from someone / a group / a Bot) goes through **identity dimension** of scope (`.scope.identity`); **module-level** availability (which modules can be used) goes through **module dimension** of scope (`.scope.platforms / bots / sessions`).
See [Scope](../advanced/scope.md).

> Recommendation: Use `master=True` / `permission` for command internal logic linkage; use identity dimension for access control based on users / groups; use module dimension for controlling module availability.

### Command Priority

```python
# Higher numerical value means higher priority
@message.on_message(priority=10)
async def high_priority_handler(event):
    await event.reply("High priority handler")

@message.on_message(priority=1)
async def low_priority_handler(event):
    await event.reply("Low priority handler")
```

### Parallel Event Handling

ErisPulse's event system adopts a **parallel within the same priority, serial across different priorities** scheduling model:

```
Event arrives
    ↓
priority=10 group: [handler C || handler D] parallel → merge results
    ↓ (if not interrupted)
priority=0 group: [handler A || handler B] parallel → merge results
    ↓
...
```

- **Parallel within the same priority**: Multiple handlers with the same priority execute simultaneously, improving throughput
- **Serial across priorities**: Groups with different priorities execute in order (higher numerical values execute first), ensuring high-priority handlers run first
- **Copy-On-Write**: Handlers do not create copies if they do not modify, ensuring zero overhead
- **Conflict handling**: When multiple handlers at the same priority modify the same field, the last modification is used and a warning log is recorded
- **Interruption mechanism**: After any handler calls `event.done()` (default) or `event.done(claim=False)`, subsequent lower-priority groups are skipped. The difference between claim and block is detailed in the following section [Link Control: Claim and Block](#link-control-claim-and-block)

```python
# Example: Parallel execution of handlers with the same priority
@message.on_message(priority=0)
async def handler_a(event):
    # Process task A
    event['result_a'] = process_a()

@message.on_message(priority=0)
async def handler_b(event):
    # Executes in parallel with handler_a
    event['result_b'] = process_b()

# Sequential execution across different priorities
@message.on_message(priority=10)
async def handler_c(event):
    # Highest priority, executes first
    pass
```

> **Concurrency limit**: All matching handlers' tasks are **immediately created**, but a semaphore limits the **maximum number of concurrent executions**, defaulting to **64** (`ErisPulse.framework.handler_max_concurrency`, supports hot updates). Tasks exceeding the limit queue on the semaphore, waiting for previous tasks to complete before entering. This is your "pressure relief valve" during event surges.
>
> **Slow logs**: If a single handler takes over **1 second**, the framework logs a WARNING (`handler_slow`). The waiting time for `wait_reply` is excluded from the duration, so it won't cause a slow log due to "waiting for a reply."

## Middleware: Rewrite or Reject Before Distribution

Middleware executes in order before event distribution, serving as the legitimate implementation point for scenarios like firewalls, rate limiting, and event desensitization:

```python
from ErisPulse.Core import adapter

@adapter.middleware
async def firewall(data):
    if _is_banned(data.get("user_id")):
        return False          # Reject: event is discarded, does not enter any handler, no outbound side effects
    data["checked"] = True    # Return dict: rewrite event payload (consistent with historical behavior)
    # Return None: allow, payload unchanged (historical behavior)
    return data
```

| Return value | Behavior |
|--------|------|
| `False` | **Reject**: event is immediately discarded, does not enter any handler |
| `dict` | Rewrite event payload and continue distribution |
| `None` | Allow, payload unchanged |

When rejected, the framework outputs a TRACE log and triggers the `adapter.event.blocked` lifecycle hook (carrying the middleware name and complete event), providing audit for "why the event did not respond."

## Command Dispatch Decision Chain: Why a Command Didn't Trigger

A command message sequentially passes through: **command text determination → command name/alias match (with spelling suggestions if not matched) → match immediately claims → scope → user ACL → owner → permission → cooldown/rate limit → parameter parsing → execution**. If any step is not satisfied, it terminates; governance hits (cooldown/rate limit) default to silent discard, permission rejections reply to the user.

In testing, `ErisPulse-Testing`'s `dispatch()` directly returns this decision chain (`DispatchTrace`, `trace.explain()` outputs causal lines), and in production, `ErisPulse.Core.Event.start_dispatch_trace()` can collect the same records.

## Scope Filtering: Why My Module Didn't Receive Messages

After an event arrives, there are two **silent** filters (neither reply nor error):

1. **Identity dimension** (`ErisPulse.scope.identity`): When an event enters the distribution entry point, it is judged whether to receive based on user > group > Bot > adapter.
   Events rejected by **the entire event** are directly discarded, and no handler (including the command dispatcher) is triggered.
2. **Module dimension** (`ErisPulse.scope`): When an event arrives at a module's handler/command, it is judged based on session > Bot > platform whether the module is available, and **skips silently** if not passed.

```toml
# Example 1: All messages in a group are not propagated
[ErisPulse.scope.identity.sessions.onebot11."group_123"]
deny = true

# Example 2: Blocking MyModule in a certain Bot
[ErisPulse.scope.bots.onebot11."123456"]
blocked = ["MyModule"]
```

At this point, when messages from this group arrive, the `MyModule` command and event handlers **will not be scheduled**. This is not a bug, but a filtering mechanism—when troubleshooting "module not responding," prioritize checking the identity and module binding of the scope.

- Filter logs are only visible at **TRACE** level (`core.scope.identity_denied` / `core.scope.denied`), and default INFO does not show any traces
- Framework-level handlers (such as the command dispatcher `scope_exempt=True`) are not affected by the **module dimension**, but are affected by the **identity dimension** (the entire event has been discarded)
- Before command execution, there is a third filter: command user ACL (replies "permission denied" on rejection, see the previous section)
- The fourth filter is **event overwriting** (see the next section).

> [!NOTE]
> **Relationship between scope filtering and event claim (claim)**: Both silent filters occur before the handler **scheduling**—handlers that are filtered out do not have the opportunity to execute, and naturally do not participate in the claim status of `event.done()` / `mark_processed()`. Whether an event has been claimed is only determined by **actual execution** handlers (command match claims, reply match claims, explicit calls); event rejection itself neither claims nor blocks (silently skips, the message continues through the remaining distribution chain).

> Scope configuration, matching syntax, and runtime API are described in [Scope](../../advanced/scope.md).

## Event Overwriting: Overwrite Behavior of Any Event Type Without Modifying Module Code

> [!NOTE]
> This feature requires ErisPulse **2.8.0+**.

Event handlers declare parameters (such as `pattern` / `regex` / `master` / `hidden`) at registration, which are only **default** for developers.
A unified overwriting system allows users to overwrite behavior for any module based on **event type**—OneBot12 standard types (meta / message / notice / request) and ErisPulse extended types (command) each have their own set of overwritable parameters:

| Event Type | Overwritable Parameters | Function |
|---------|-----------|------|
| `message` | `pattern` / `regex` / `detail_types` | Text trigger conditions + message subtype whitelist |
| `notice` | `detail_types` / `pattern` / `regex` | Notice subtype whitelist + text conditions |
| `request` | `detail_types` / `pattern` / `regex` | Request subtype whitelist + text conditions |
| `meta` | `detail_types` | Meta-event subtype whitelist (connect / heartbeat, etc.) |
| `command` | `master` / `hidden` / `aliases` / `prefix` / `help` / `usage` | Command implementation parameters (user priority) |
| `acl` (command-specific) | `allow` / `deny` | Command user whitelist/blacklist (by command name glob) |

```toml
# message: Overwrite text trigger conditions (AND with code-side conditions)
[ErisPulse.event.overrides.message.ChatModule]
pattern = "闲聊*"

# notice: Only respond to specific notice subtypes
[ErisPulse.event.overrides.notice.MyModule]
detail_types = ["group_increase"]

# command: Overwrite implementation parameters (user priority—can tighten or loosen developer defaults)
[ErisPulse.event.overrides.command.MyModule.restart]
master = true
hidden = true

# acl: Command user whitelist/blacklist (across commands glob)
[ErisPulse.event.overrides.acl."roll*"]
allow = ["onebot11:u_vip"]

# ACL fallback (false = strict mode: no ACL means reject)
acl_default_allow = true
```

Runtime API (via `from ErisPulse.Core.Event import overrides` or `sdk.Event.overrides`, **type sub-namespace**—each type symmetrically has `set` / `get` / `delete` three methods):

```python
from ErisPulse.Core.Event import overrides

overrides.message.set("ChatModule", pattern="闲聊*")   # message text condition
overrides.notice.set("MyModule", detail_types=["group_increase"])
overrides.command.set("MyModule", "restart", master=True)  # command parameter
overrides.acl.set("roll*", deny=["onebot11:u_bad"])    # command user blacklist

overrides.message.get("ChatModule")     # {"pattern": "闲聊*"}
overrides.message.delete("ChatModule")  # Restore developer default
```

- Overwrite conditions and handler code-side conditions **both take effect** (AND semantics); `command` parameter overwrite and developer declaration **deep merge** (overwrite takes precedence)
- `detail_types`: Events without `detail_type` are allowed (not mistakenly kill unknown events)
- `pattern` / `regex`: Events without text (connect / heartbeat, etc.) are not constrained and are allowed directly
- `command` overwrite key `master` synchronously maps to storage key `must_master`; disabling commands uses `acl` deny
- **Key name mapping explanation**: `overrides.command.set("My", "restart", master=True)`'s parameter name `master` is only an alias for configuration, the actual storage key and the key name returned by `get()` are unified as **`must_master`** (e.g., `get()` returns `{"must_master": true}`) — the runtime judgment reads the storage key, so do not read by the `master` key name
- Configuration changes take effect immediately (hot update), format validation warnings (unknown parameters / bad entries are ignored)

## Link Control: Claim and Block

> [!NOTE]
> The `event.done()` / `event.mark_processed()` `claim=` / `stop=` parameters for this feature require ErisPulse **2.7.1+**.

ErisPulse decouples the two orthogonal semantics of "claim" and "block," unifying control through `event.done()`, which is convenient for adding observation layers such as logging, auditing, and permission around command processing.

**Two concepts are defined precisely:**

- **Claim (claim)**: Mark the event as processed by this handler (write to `_processed`). The command dispatcher sees the claimed event and **skips duplicate processing**—preventing the same message from being processed by multiple command handlers. Typical scenario: After a command matches, claim it to prevent the command dispatcher from intervening again.
- **Block (block)**: Prevent the event from propagating to **lower-priority** handlers (write to `_propagation_stopped`). Lower-priority handlers will no longer see the event. Typical scenario: The high-priority handler has fully processed the event, and lower-priority handlers should not execute.

| `event.done(...)` | Claim | Block | Scenario |
|-------------------|------|------|------|
| `event.done()` | ✔ | ✔ | Standard practice for command / handler completion |
| `event.done(stop=False)` | ✔ | ✘ | Only claim, let lower-priority observers (logging / statistics) still see |
| `event.done(claim=False)` | ✘ | ✔ | Only block (e.g., firewall / rate limit), but do not do command deduplication |

`event.done(claim=, stop=)` is an alias for `event.mark_processed(claim=, stop=)`, with identical parameters and behavior.

```python
@command("help")
async def help_cmd(event):
    event.done()            # Claim + Block (standard practice for command completion)

@message.on_message(priority=50)
async def observer(event):
    event.done(stop=False)  # Only claim: lower-priority still executes (logging / statistics)

@message.on_message(priority=100)
async def firewall(event):
    if denied(event):
        event.done(claim=False)  # Only block: lower-priority does not execute, but no deduplication
```

### Command and Reply Block Configuration

**Command matches claim immediately**: As soon as a message matches a registered command name (including subcommands/aliases), regardless of subsequent scope or permission checks, it is claimed and defaults to blocking propagation—commands rejected by permission will no longer leak to lower-priority message handlers (eliminating "double response" where the command is rejected and then `on_message` responds again).

Blocking propagation can be configured to allow lower-priority observers (logging / audit / permission) to still see these messages:

```toml
[ErisPulse.event.command]
block = false   # Command messages continue to flow to lower-priority handlers (claim is unaffected, will not be re-consumed)

[ErisPulse.event.wait_reply]
block = false   # Reply consumed by wait_reply continues to flow to lower-priority handlers
```

> Note: `block` only controls **blocking** (stop), not **claiming** (claim) — matched commands will never be re-consumed by message handlers; messages that do not match any command flow normally to message handlers.

## Notice Event Handling

### Friend Added

```python
from ErisPulse.Core.Event import notice

@notice.on_friend_add()
async def friend_add_handler(event):
    user_id = event.get_user_id()
    nickname = event.get_user_nickname() or "new friend"
    await event.reply(f"Welcome to add me as a friend, {nickname}!")
```

### Group Member Increase

```python
@notice.on_group_increase()
async def member_increase_handler(event):
    group_id = event.get_group_id()
    user_id = event.get_user_id()
    await event.reply(f"Welcome new member {user_id} to group {group_id}")
```

### Group Member Decrease

```python
@notice.on_group_decrease()
async def member_decrease_handler(event):
    group_id = event.get_group_id()
    user_id = event.get_user_id()
    await event.reply(f"Member {user_id} left group {group_id}")
```

## Request Event Handling

### Friend Request

```python
from ErisPulse.Core.Event import request

@request.on_friend_request()
async def friend_request_handler(event):
    user_id = event.get_user_id()
    comment = event.get_comment()
    
    sdk.logger.info(f"Received friend request: {user_id}, comment: {comment}")
    
    # You can handle the request through the adapter API
    # See the adapter documentation for specific implementation
```

### Group Invitation Request

```python
@request.on_group_request()
async def group_request_handler(event):
    group_id = event.get_group_id()
    user_id = event.get_user_id()
    
    await event.reply(f"Received invitation to group {group_id} from {user_id}")
```

## Meta Event Handling

### Connection Event

```python
from ErisPulse.Core.Event import meta

@meta.on_connect()
async def connect_handler(event):
    platform = event.get_platform()
    sdk.logger.info(f"{platform} platform connected")

@meta.on_disconnect()
async def disconnect_handler(event):
    platform = event.get_platform()
    sdk.logger.warning(f"{platform} platform disconnected")
```

### Heartbeat Event

```python
@meta.on_heartbeat()
async def heartbeat_handler(event):
    platform = event.get_platform()
    sdk.logger.debug(f"{platform} heartbeat check")
```

### Bot Status Query

After the adapter sends a meta event, the framework automatically tracks the Bot status, and you can query it at any time:

```python
from ErisPulse import sdk

# Check if a Bot is online
if sdk.adapter.is_bot_online("telegram", "123456"):
    telegram = sdk.adapter.get("telegram")
    await telegram.Send.To("user", "123456").Text("Bot is online")

# List all currently online Bots
bots = sdk.adapter.list_bots()
for platform, bot_list in bots.items():
    for bot_id, info in bot_list.items():
        print(f"{platform}/{bot_id}: {info['status']}")

# Get complete status summary
summary = sdk.adapter.get_status_summary()
```

## Interactive Handling

### Using the reply method to send replies

The `event.reply()` method supports various modifier parameters, making it convenient to send messages with @, reply, etc.:

```python
# Simple reply
await event.reply("Hello")

# Send different types of messages
await event.reply("http://example.com/image.jpg", method="Image")  # Image
await event.reply("http://example.com/voice.mp3", method="Voice")  # Voice

# @ single user
await event.reply("Hello", at_users=["user123"])

# @ multiple users
await event.reply("Hello everyone", at_users=["user1", "user2", "user3"])

# Reply to message
await event.reply("Reply content", reply_to="msg_id")

# @ all members
await event.reply("Announcement", at_all=True)

# Combinations: @ user + reply to message
await event.reply("Content", at_users=["user1"], reply_to="msg_id")
```

### Waiting for user reply

```python
@command("ask", help="Ask user")
async def ask_handler(event):
    await event.reply("Please enter your name:")
    
    # Wait for user reply, timeout 30 seconds
    reply = await event.wait_reply(timeout=30)
    
    if reply:
        name = reply.get_text()
        await event.reply(f"Hello, {name}!")
    else:
        await event.reply("Timeout, please re-enter.")
```

> [!TIP]
> **Commands remain available during waiting** (2.8.3+): Messages starting with a command prefix and matching a registered command (e.g., `/cancel`) will **execute the command** rather than serve as reply content, and waiting continues suspended—users can cancel/switch at any time, and the command executes and continues to reply. For the old behavior of "waiting swallowing all text," configure `ErisPulse.event.wait_reply.cmdpass = true`, or single-time `wait_reply(cmdpass=True)`.

### Waiting reply with validation

```python
@command("age", help="Ask age")
async def age_handler(event):
    def validate_age(event_data):
        """Validate if age is valid"""
        try:
            age = int(event_data.get_text())
            return 0 <= age <= 150
        except ValueError:
            return False
    
    await event.reply("Please enter your age (0-150):")
    
    reply = await event.wait_reply(
        timeout=60,
        validator=validate_age
    )
    
    if reply:
        age = int(reply.get_text())
        await event.reply(f"Your age is {age} years old")
    else:
        await event.reply("Invalid input or timeout")
```

### Waiting reply with callback

```python
@command("confirm", help="Confirm operation")
async def confirm_handler(event):
    async def handle_confirmation(reply_event):
        text = reply_event.get_text().lower()
        
        if text in ["是", "yes", "y"]:
            await event.reply("Operation confirmed!")
        else:
            await event.reply("Operation canceled.")
    
    await event.reply("Confirm executing this operation? (Yes/No)")
    
    await event.wait_reply(
        timeout=30,
        callback=handle_confirmation
    )
```

### Confirmation dialog (confirm)

Wait for user confirmation or negation, automatically recognizing built-in Chinese and English confirmation words:

```python
@command("confirm", help="Confirm operation")
async def confirm_handler(event):
    if await event.confirm("Are you sure to execute this operation?"):
        await event.reply("Confirmed, executing...")
    else:
        await event.reply("Canceled")

# Custom confirmation words
if await event.confirm("Continue?", yes_words={"go", "continue"}, no_words={"stop", "stop"}):
    pass
```

### Selection menu (choose)

Users can reply with option numbers or option text:

```python
@command("choose", help="Choose")
async def choose_handler(event):
    choice = await event.choose(
        "Please select a color:",
        ["red", "green", "blue"]
    )
    
    if choice is not None:
        colors = ["red", "green", "blue"]
        await event.reply(f"You selected: {colors[choice]}")
    else:
        await event.reply("Timed out without selection")
```

**Merge mode**: With `merge_prompt=True`, options are merged into the prompt message and sent in a single message using the specified `method`:

```python
# Send merged prompt + options using Markdown
choice = await event.choose(
    "## Please select a color\n{options}\nPlease reply with the number",
    ["red", "green", "blue"],
    method="Markdown",
    merge_prompt=True,
)
```

> The `{options}` placeholder controls the insertion position of options; if not written, it appends to the end of the prompt. You can customize the placeholder with the `placeholder` parameter (e.g., `placeholder="[choices]"`). `options_format="auto"` (default) automatically chooses the style based on method: unordered list for Markdown, ordered list for Html, plain text list for others. For text methods (Text/Markdown/Html, etc.), options are merged by default to the end; for non-text methods (Image, etc.), options are split into two messages by default.

### Collect form (collect)

Multi-step collection of user input:

```python
@command("register", help="Register")
async def register_handler(event):
    data = await event.collect([
        {"key": "name", "prompt": "Please enter your name:"},
        {"key": "age", "prompt": "Please enter your age:", 
         "validator": lambda e: e.get_text().isdigit()},
        {"key": "email", "prompt": "Please enter your email:"}
    ])
    
    if data:
        await event.reply(f"Registration successful!\nName: {data['name']}\nAge: {data['age']}\nEmail: {data['email']}")
    else:
        await event.reply("Registration timed out or invalid input")
```

### Wait for any event (wait_for)

Wait for an event that meets the condition, not limited to the same user:

```python
@command("wait_member", help="Wait for new member")
async def wait_member_handler(event):
    await event.reply("Waiting for new member to join...")
    
    evt = await event.wait_for(
        event_type="notice",
        condition=lambda e: e.get_detail_type() == "group_member_increase",
        timeout=120
    )
    
    if evt:
        await event.reply(f"Welcome new member: {evt.get_user_id()}")
    else:
        await event.reply("Timed out")
```

### Multi-turn conversation (conversation)

Create an interactive multi-turn conversation context:

```python
@command("survey", help="Questionnaire survey")
async def survey_handler(event):
    conv = event.conversation(timeout=60)
    
    await conv.say("Welcome to the survey!")
    
    while conv.is_active:
        reply = await conv.wait()
        
        if reply is None:
            await conv.say("Conversation timed out, goodbye!")
            break
        
        text = reply.get_text()
        
        if text == "exit":
            await conv.say("Goodbye!")
            break
        
        await conv.say(f"You said: {text}, continue typing or reply 'exit' to end")
```

### Built-in confirmation words

ErisPulse has built-in sets of Chinese and English confirmation words:

- **Confirmation words** (`CONFIRM_YES_WORDS`): 是、yes、y、confirm、sure、ok、true、right、mm、okay、agree、no problem...
- **Negation words** (`CONFIRM_NO_WORDS`): 否、no、n、cancel、don't、refuse、false、wrong、reject、cannot...

## Event Data Access

### Common Methods of Event Object

```python
@command("info")
async def info_handler(event):
    # Basic information
    event_id = event.get_id()
    event_time = event.get_time()
    event_type = event.get_type()
    detail_type = event.get_detail_type()
    
    # Sender information
    user_id = event.get_user_id()
    nickname = event.get_user_nickname()
    
    # Message content
    message_segments = event.get_message()
    alt_message = event.get_alt_message()
    text = event.get_text()
    
    # Group information
    group_id = event.get_group_id()
    
    # Bot information
    self_id = event.get_self_user_id()
    self_platform = event.get_self_platform()
    
    # Raw data
    raw_data = event.get_raw()
    raw_type = event.get_raw_type()
    
    # Platform information
    platform = event.get_platform()
    
    # Message type judgment
    is_private = event.is_private_message()
    is_group = event.is_group_message()
    is_at = event.is_at_message()
    
    # Command information
    if event.is_command():
        cmd_name = event.get_command_name()
        cmd_args = event.get_command_args()
        cmd_raw = event.get_command_raw()
```

### Platform Extension Methods

In addition to built-in methods, each platform adapter will also register platform-specific methods, making it convenient for you to access platform-specific data.

```python
from ErisPulse.Core.Event import message

@message.on_message()
async def handle_message(event):
    platform = event.get_platform()

    # Call platform-specific methods based on platform
    if platform == "telegram":
        chat_type = event.get_chat_type()      # Telegram-specific method
    elif platform == "email":
        subject = event.get_subject()           # Email-specific method
```

If you are unsure whether a platform has registered a particular method, you can query which methods a platform has registered:

```python
from ErisPulse.Core.Event import get_platform_event_methods

methods = get_platform_event_methods("telegram")
# ["get_chat_type", "is_bot_message", ...]
```

> For platform-specific methods registered by each platform, please refer to the corresponding [Platform Documentation](../platform-guide/).

## Event Handling Best Practices

### 1. Exception Handling

```python
@command("process")
async def process_handler(event):
    try:
        # Business logic
        result = await do_some_work()
        await event.reply(f"Result: {result}")
    except ValueError as e:
        # Expected business error
        await event.reply(f"Parameter error: {e}")
    except Exception as e:
        # Unexpected error
        sdk.logger.error(f"Processing failed: {e}")
        await event.reply("Processing failed, please try again later")
```

### 2. Logging

```python
@message.on_message()
async def message_handler(event):
    user_id = event.get_user_id()
    text = event.get_text()
    
    sdk.logger.info(f"Processing message: {user_id} - {text}")
    
    # Use the module's own logger
    from ErisPulse import sdk
    logger = sdk.logger.get_child("MyHandler")
    logger.debug(f"Detailed debug information")
```

### 3. Conditional Processing

```python
@message.on_message(priority=0)
async def conditional_handler(event):
    """Conditional processing - judge within the handler"""
    # Only process messages from specific users
    if event.get_user_id() in ["bot1", "bot2"]:
        return
    
    # Only process messages containing specific keywords
    if "keyword" not in event.get_text():
        return
    
    await event.reply("Condition satisfied, processing message")
```

## Next Steps

- [Common Task Examples](common-tasks.md) - Learn implementations of common features (including advanced message sending: retry/timeout/batch)
- [Platform Features Guide](../platform-guide/README.md) - Complete explanation of Send DSL chain sending, sending rules, and batch construction
- [Event Wrapper Class Details](../developer-guide/modules/event-wrapper.md) - Deep dive into Event objects
- [User Guide](../user-guide/) - Learn about configuration and module management