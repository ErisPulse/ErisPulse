# Getting Started with Event Handling

This guide introduces how to handle various types of events in ErisPulse.

## Overview of Event Types

ErisPulse supports the following event types:

| Event Type | Description | Use Cases |
|------------|-------------|-----------|
| Message Event | Any message sent by a user | Chatbots, content filtering |
| Command Event | Messages starting with a command prefix | Command processing, entry points |
| Notice Event | System notifications (friend addition, group member changes, etc.) | Welcome messages, status notifications |
| Request Event | User requests (friend requests, group invitations) | Automatic request handling |
| Meta Event | System-level events (connection, heartbeat) | Connection monitoring, status checks |

## Handling Message Events

> **Tip**: It is recommended to use the `Event` type annotation in event handlers for IDE auto-completion and type checking support.

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
    sdk.logger.info(f"Message sent in group {group_id} by {user_id}")
```

### Listening to @ Messages

```python
@message.on_at_message()
async def at_handler(event: Event):
    # Get list of mentioned users
    mentions = event.get_mentions()
    await event.reply(f"You mentioned these users: {mentions}")
```

### Wildcard and Regular Expression Matching

The four message decorators (`on_message` / `on_private_message` / `on_group_message` / `on_at_message`) support both `pattern` (glob wildcard) and `regex` (regular expression). Messages that do not match are **not triggered**:

```python
# Glob wildcard: * matches any string, ? matches a single character, [seq] matches a character set
@message.on_message(pattern="签到*")
async def signin_handler(event: Event):
    await event.reply("Sign-in successful")

# Regex: match amount
@message.on_message(regex=r"\d+\s*元")
async def price_handler(event: Event):
    await event.reply(f"Received amount: {event.get_text()}")

# Both pattern and regex given → both must match
@message.on_message(pattern="*元", regex=r"\d+\s*元")
async def combined_handler(event: Event):
    pass
```

`wait_reply` also supports these two parameters (see [Wait Reply Functionality](../developer-guide/modules/event-wrapper.md#wait-reply-functionality)).

## Handling Command Events

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

Users can invoke with any of the following:
- `/help`
- `/h`
- `/帮助`

### Command Arguments

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

Arguments preserve the original case as input (even if configured case-insensitive, command name matching normalization does not affect argument content).

### Declared Arguments and Options (`args=` / `options=`)

Manually parsing arguments requires handling type conversion and error messages yourself. After declaring `args=` / `options=`, the framework automatically parses command arguments and **injects them by name** after permission checks pass; when users input incorrectly, it automatically replies with localized prompts and usage (without throwing exceptions), and `/help <command>` will automatically show usage:

```python
@command(
    "roll",
    args="<count:int> [sides:int=6]",
    options={"verbose": "-v/--verbose", "label": "--label"},
    help="Roll dice",
)
async def roll_handler(event, count: int, sides: int = 6, verbose: bool = False, label: str = ""):
    total = sum(random.randint(1, sides) for _ in range(count))
    await event.reply(f"Rolled {count} {sides}-sided dice, total points: {total}")
```

`args=` positional parameter syntax: `<count:int>` is required, `[sides:int=6]` is optional (with default value). Supported types:

| Type | Example Input | Description |
|------|---------|------|
| `str` | `hello` | Text (default type) |
| `int` / `float` | `3` / `0.5` | Numerical |
| `bool` | `是` / `yes` / `はい` / `да` / `true` / `no` / `取消` | Boolean, reuses confirmation word list from `Event.confirm()` |
| `literal` | `<mode:literal=fast|slow>` | Enum, only accepts listed values; optional form defaults to first |
| `duration` | `90s`、`1h30m`、`1d` | Duration, converted to float in seconds |
| `rest` | `<text:rest>` | Remaining full text (must be last) |

`options=` option is declared in dictionary form: key is handler parameter name, value is flag form (multiple aliases separated by `/`). Parameters annotated as `bool` are boolean flags (appear as `True`); others (default as `str`) are value options, supporting both `--label hello` and `--label=hello` value forms, type follows handler annotation. Options are identified and removed first, remaining tokens are parsed according to `args=` (rest covers remaining text after removing options).

**Behavior Points**:

- Permission checks precede parameter parsing—users without permission will not trigger parsing
- Parsing fails (type mismatch / missing parameter / too many parameters / unknown option) automatically replies with localized error + usage, command is still claimed
- Declared parameter names must exist in handler signature, otherwise throw `ValueError` at registration
- Commands without declaring `args=` / `options=` behave exactly the same (backward compatibility)

### Command Governance (`cooldown=` / `rate_limit=` / `deprecated=`)

Manual cooldown timing, rate limiting window, and deprecation prompts can be replaced with declarations, which can be combined arbitrarily.

**Cooldown**—duration syntax is consistent with `args=`'s `duration` type (e.g., `"30s"`, `"1h30m"`, `"1d"`):

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

**Deprecated**—automatically replies with deprecation text when called; `deprecated_reject=True` rejects execution:

```python
@command("oldcmd", deprecated="Please use /newcmd", deprecated_reject=True)
async def old_handler(event): ...
```

Key granularity (`cooldown_key=` / `rate_limit_key=`): `"user"` (default, shared by same user), `"session"` (shared by same session, like same group), `"global"` (shared by all users and sessions).

**Behavior Points**:

- Cooldown / rate limit hit defaults to **silent discard** (symmetrical to scope silence); declare `cooldown_reply=` / `rate_limit_reply=` to reply with this text on hit
- Command hit counts as claimed—governed commands will not leak to lower priority message handlers
- Governance judgment occurs after all permission checks and parameter parsing pass, before actual execution: users without permission do not trigger, parameter errors do not consume
- When both cooldown and rate limit are declared, cooldown is judged first (cooldown hit does not occupy rate limit window)
- `deprecated=` defaults to replying with text and **continues execution**; `deprecated_reject=True` rejects execution (`command.executed` hook records `success=False, error="deprecated"`)
- `/help` list and single command help automatically display deprecation markers and text
- Status is in-process memory, automatically cleaned up when module unloads; cross-process sharing / persistent restart is not in scope
- Declaration is validated at registration (fail-fast): illegal syntax, key granularity not in whitelist value, reply not paired with main declaration all throw `ValueError`

### Handler Throttling (`throttle=`)

Message handler anti-spam declaration—same key events are processed at most once within an interval, others are silently discarded:

```python
from ErisPulse import sdk

@sdk.message.on_message(throttle="2s", throttle_key="user")
async def handler(event): ...
```

`on_message` / `on_private_message` / `on_group_message` / `on_at_message` all support throttling; `throttle_key=` shares the same key granularity as command governance (`user` / `session` / `global`), and the duration syntax is consistent with `duration`. Throttling and `pattern=` / `regex=` and other existing conditions are superimposed and effective (all must be satisfied to trigger); discarded within the interval only records TRACE log; declaration is validated at registration.

### Dependency Injection (`Depends`)

Common dependencies (database sessions, configuration reading, etc.) can be extracted into dependency functions, and handlers declare them as default values with `Depends(dependency function)`, and the framework automatically calls the dependency function with the context object and injects by name before calling:

```python
from ErisPulse.Core import Depends

async def get_session(event):
    return await sdk.module.call("DB", "get_session")

@command("admin")
async def admin_handler(event, db=Depends(get_session)):
    ...
```

Default **request-level caching** is enabled: within the same event distribution, the same dependency function is only parsed once, and all injection points share the result (e.g., `get_db` only builds one database session within one event); it is automatically not reused across requests. Use `Depends(get_db, use_cache=False)` to disable caching for a single dependency.

Covers all framework injection points—command handlers, event handlers (`message.on_message()` etc.), lifecycle hooks (`sdk.lifecycle.on`), SSE route handlers. The first parameter of the dependency function is the context object of the injection point (event scenario is `Event`, lifecycle is event `data`, route is `HttpRequest` / `SseEmitter`); both synchronous and asynchronous dependency functions can be declared.

**Syntax sugar for declaring other module services**:

```python
@command("query")
async def query_handler(event, session=Depends.module("DB", "get_session")):
    ...
```

`Depends.module(module name, method name, *fixed arguments)` is equivalent to calling `sdk.module.call(...)` inside the dependency function. Module instantiation (`__init__`) is not covered—no context object at instantiation; for FastAPI hosted HTTP routes, use FastAPI's native `fastapi.Depends`.

**Behavior Points**:

- Declaration is validated at registration (fail-fast): dependency is not callable, or conflicts with `args=` / `options=` parameters, throw `ValueError`
- Exceptions thrown by the dependency function are handled in the same way as the handler's own exceptions (command automatically replies with error)
- Handlers without declaring `Depends` have zero overhead (no reflection at distribution)
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

The `group` parameter is only used for help list categorization; the above example's `admin.reload` is a **single command name** (dot notation is just naming style, users need to input `/admin.reload`).

### Subcommands

Command names support **multi-token forms separated by spaces**, achieving subcommands like `/admin add`, `/admin user ban`:

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

Matching rules (**longest prefix match**):

- `/admin add x` prioritizes matching `admin add`, `event.get_command_args()` returns `["x"]` (parameters after subcommand name)
- Only `admin` registered, `/admin add x` matches `admin`, `get_command_args()` returns `["add", "x"]` (legacy behavior unchanged)
- Alias supports multi-token forms (e.g., `a remove`), can also use single-token alias (e.g., `a`) pointing to subcommand
- When parent and child commands are both registered, unregistered subcommand input (e.g., `/admin list x`) falls back to parent command

**Permission Inheritance**: When subcommands do not declare `permission`, they automatically inherit the nearest ancestor command that declared permission on the parent chain—protecting `/admin` automatically protects all its subcommands; subcommands' own declared permissions take precedence:

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

Note: `master=True` and `hidden` **do not** inherit, please declare them separately when needed; user ACL (whitelist/blacklist) matches by full command name, glob rules like `"admin*"` can cover entire subcommand groups.

In `/help` command overview, subcommands will automatically be displayed indented under visible parent commands (e.g., `admin` → `admin add` indented one level, `admin user` → `admin user ban` indented two levels).

### Command Permissions and Access Control

Command permissions are divided into three layers, judged from top to bottom (if the upper layer rejects, the lower layer is not checked):

```python
# ① Command Permission ACL (user-side configuration): By user whitelist/blacklist of commands, reject with "Permission denied"
# ② master=True — Only the framework owner can execute (framework automatically checks, reject with "Permission denied")
@command("restart", master=True, help="Restart module")
async def restart_handler(event):
    await event.reply("Module restarted")

# ③ permission=call function — Command's own control logic (returns True to execute)
def is_admin(event):
    return event.get_user_id() in {"user123", "user456"}

@command("panel", permission=is_admin, help="Management panel")
async def panel_handler(event):
    await event.reply("Welcome to the management panel")
```

**Command User ACL** (`ErisPulse.event.command.acl`): Users can configure user whitelist/blacklist for any command, command name supports exact and glob patterns (e.g., `"roll*"`), reject with "Permission denied":

```toml
# config.toml — Allow only 123456 to execute restart; 666 is always rejected
[ErisPulse.event.command.acl.restart]
allow = ["onebot11:123456"]
deny = ["onebot11:666"]
```

Judgment order: `deny` hit → reject; `allow` non-empty and not hit → reject; no ACL configuration follows `event.command.default_allow` (false = strict mode, no ACL means reject; true means leave to developer default `master=True` / `permission`). Runtime API (command name supports glob):

```python
from ErisPulse.Core.Event import command

command.allow_user("restart", "onebot11", "123456")   # Allow list
command.deny_user("restart", "onebot11", "666")       # Deny list
command.remove_acl("restart")                          # Clear whitelist/blacklist
command.get_acl("restart")                             # Query current list
```

> Command handlers are imported from event package: `from ErisPulse.Core.Event import command`; can also access via SDK event package: `sdk.Event.command` (both are the same singleton). Usually imported within modules (from ErisPulse.Core.Event import command).

Cross-command / cross-user **event-level** access control (whether a person / group / bot's message is received) goes through **identity dimension** of scope (scope.identity); **module-level** availability (which modules can be used) goes through **module dimension** of scope (scope.platforms / bots / sessions).  
See [Scope](../advanced/scope.md).

> Suggestion: Use `master=True` / `permission` for command internal logic linkage; use scope identity dimension for access control by user / group; use scope module dimension for controlling module availability.

### Command Priority

```python
# Higher priority number, earlier execution
@message.on_message(priority=10)
async def high_priority_handler(event):
    await event.reply("High priority handler")

@message.on_message(priority=1)
async def low_priority_handler(event):
    await event.reply("Low priority handler")
```

### Parallel Event Handling

The ErisPulse event system adopts a **parallel within same priority, serial across different priorities** scheduling model:

```
Event arrives
    ↓
priority=10 group: [Handler C || Handler D] parallel → merge results
    ↓ (if not interrupted)
priority=0 group: [Handler A || Handler B] parallel → merge results
    ↓
...
```

- **Parallel within same priority**: Multiple handlers with the same priority execute simultaneously, improving throughput
- **Serial across different priorities**: Groups with different priorities execute in order (higher priority number executes first), ensuring high-priority handlers run first
- **Copy-On-Write**: Handlers do not create copies unless modified, ensuring zero overhead
- **Conflict handling**: When multiple handlers with the same priority modify the same field, the last modification is used and a warning log is recorded
- **Interruption mechanism**: After any handler calls `event.done()` (default) or `event.done(claim=False)`, subsequent lower-priority groups are skipped. The difference between claiming and blocking is described in the following section [Link Control: Claiming and Blocking](#link-control-claiming-and-blocking)

```python
# Example: Multiple handlers with the same priority execute in parallel
@message.on_message(priority=0)
async def handler_a(event):
    # Process task A
    event['result_a'] = process_a()

@message.on_message(priority=0)
async def handler_b(event):
    # Executes in parallel with handler_a
    event['result_b'] = process_b()

# Execute in serial across different priorities
@message.on_message(priority=10)
async def handler_c(event):
    # Highest priority, executes first
    pass
```

> **Concurrency Limit**: All matching handlers' Tasks are **immediately created**, but a semaphore limits the **maximum number of concurrent executions**, defaulting to **64** (`ErisPulse.framework.handler_max_concurrency`, supports hot updates). Tasks exceeding the limit wait in the semaphore queue until previous tasks complete. This is your "pressure relief valve" during event bursts.
>
> **Slow Logs**: If a single handler takes more than **1 second**, the framework logs a WARNING (`handler_slow`). The waiting time of `wait_reply` is deducted from the duration, preventing "waiting for reply" from mistakenly triggering slow logs.

## Scope Filtering: Why My Module Didn't Receive Messages

After an event arrives, there are two **silent** filters (neither replies nor errors):

1. **Identity Dimension** (`ErisPulse.scope.identity`): When an event enters the distribution entrance, it is determined whether to receive it by user > group > bot > adapter. Events rejected at this stage are **completely discarded**, and no processor (including the command dispatcher) will be triggered.
2. **Module Dimension** (`ErisPulse.scope`): When an event reaches a module's processor/command, it is determined whether the module is available by session > bot > platform. If it does not pass, it is **silently skipped**.

```toml
# Example 1: Messages from a specific group are not propagated
[ErisPulse.scope.identity.sessions.onebot11."group_123"]
deny = true

# Example 2: Blocking MyModule from a specific bot
[ErisPulse.scope.bots.onebot11."123456"]
blocked = ["MyModule"]
```

At this point, the `MyModule` command and event processors **will not be scheduled** when messages arrive in this group. This is not a bug, but a filtering mechanism—when troubleshooting "module not responding," prioritize checking the identity and module binding of the scope.

- Filter logs are only visible at **TRACE** level (`core.scope.identity_denied` / `core.scope.denied`), default INFO does not show any traces
- Framework-level processors (such as the command dispatcher `scope_exempt=True`) are not affected by the **module dimension**, but are affected by the **identity dimension** (the entire event has been discarded)
- There is a third layer of command user ACL before command execution (rejects with "Permission denied," see the previous section)
- The fourth layer is **event overwriting** (see the next section)

> [!NOTE]
> **Scope filtering and event claiming (claim)**: Both silent filters occur **before** processor **scheduling**—processors that are filtered out have no chance to execute, and naturally do not participate in `event.done()` / `mark_processed()` claiming status. Whether an event has been claimed is determined only by **actual executed** processors (command hit claiming, reply hit claiming, explicit call); scope rejection itself neither claims nor blocks (silently skips, message continues through the remaining distribution chain).

> Scope configuration, matching syntax, runtime API see [Scope (scope)](../../advanced/scope.md).

## Event Overwriting: Overwrite Any Event Type Behavior Without Modifying Module Code

> [!NOTE]
> This feature requires ErisPulse **2.8.0+**.

Event processors, when registered, declare parameters (`pattern` / `regex` / `master` / `hidden` etc.) as **developer defaults**. The unified overwriting system allows users to overwrite any module's behavior by **event type**—OneBot12 standard types (meta / message / notice / request) and ErisPulse extended types (command) each have their own set of overwritable parameters:

| Event Type | Overwritable Parameters | Function |
|---------|-----------|------|
| `message` | `pattern` / `regex` / `detail_types` | Text trigger conditions + message sub-type whitelist |
| `notice` | `detail_types` / `pattern` / `regex` | Notification sub-type whitelist + text conditions |
| `request` | `detail_types` / `pattern` / `regex` | Request sub-type whitelist + text conditions |
| `meta` | `detail_types` | Meta-event sub-type whitelist (connect / heartbeat etc.) |
| `command` | `master` / `hidden` / `aliases` / `prefix` / `help` / `usage` | Command implementation parameters (user priority) |
| `acl` (command-specific) | `allow` / `deny` | Command user whitelist/blacklist (by command name glob) |

```toml
# message: Overwrite text trigger conditions (AND with code conditions)
[ErisPulse.event.overrides.message.ChatModule]
pattern = "闲聊*"

# notice: Only respond to specific notification sub-types
[ErisPulse.event.overrides.notice.MyModule]
detail_types = ["group_increase"]

# command: Overwrite implementation parameters (user priority—can tighten or loosen developer defaults)
[ErisPulse.event.overrides.command.MyModule.restart]
master = true
hidden = true

# acl: Command user whitelist/blacklist (cross-command glob)
[ErisPulse.event.overrides.acl."roll*"]
allow = ["onebot11:u_vip"]

# ACL default (false = strict mode: no ACL means reject)
acl_default_allow = true
```

Runtime API (`from ErisPulse.Core.Event import overrides` or `sdk.Event.overrides`, **type sub-namespace**—each type has symmetric `set` / `get` / `delete` three-piece sets):

```python
from ErisPulse.Core.Event import overrides

overrides.message.set("ChatModule", pattern="闲聊*")   # message text condition
overrides.notice.set("MyModule", detail_types=["group_increase"])
overrides.command.set("MyModule", "restart", master=True)  # command parameter
overrides.acl.set("roll*", deny=["onebot11:u_bad"])    # command user blacklist

overrides.message.get("ChatModule")     # {"pattern": "闲聊*"}
overrides.message.delete("ChatModule")  # Restore developer default
```

- Overwrite conditions and processor code conditions **both take effect** (AND semantics); `command` parameter overwrite and developer declaration **deep merge** (overwrite priority)
- `detail_types`: Events without `detail_type` are allowed (no accidental killing of unknown events)
- `pattern` / `regex`: Events without text (connect / heartbeat, etc.) are not constrained and are allowed directly
- `command` overwrite key `master` synchronously maps to storage key `must_master`; disabling commands uniformly uses `acl` deny
- **Key name mapping explanation**: `overrides.command.set("My", "restart", master=True)`'s parameter name `master` is only a configuration alias, the actual storage key and the key name returned by `get()` are unified as **`must_master`** (e.g., `get()` returns `{"must_master": true}`) — runtime judgment reads the storage key, do not read by `master` key name
- Configuration changes take effect immediately (hot update), format validation warnings (unknown parameters / bad entries ignored)

## Link Control: Claiming and Blocking

> [!NOTE]
> `event.done()` / `event.mark_processed()`'s `claim=` / `stop=` parameters require ErisPulse **2.7.1+**.

ErisPulse decouples the two orthogonal semantics of "claiming" and "blocking" and unifies control through `event.done`, facilitating the addition of observation layers such as logging, auditing, and permission around command processing.

**Accurate definitions of the two concepts:**

- **Claiming (claim)**: Mark the event as processed by this handler (write to `_processed`). The command dispatcher sees the claimed event and **skips deduplication**—preventing the same message from being processed multiple times by multiple command handlers. Typical scenario: After a command matches, claim it to prevent the command dispatcher from intervening again.
- **Blocking (stop)**: Prevent the event from propagating to **lower-priority** handlers (write to `_propagation_stopped`). Lower-priority handlers will no longer see the event. Typical scenario: A high-priority handler has fully processed the event and does not want lower-priority handlers to execute.

| `event.done(...)` | Claim | Block | Scenario |
|-------------------|------|------|------|
| `event.done()` | ✔ | ✔ | Standard practice after command/processor completion |
| `event.done(stop=False)` | ✔ | ✘ | Only claim: lower-priority observers (logging/statistics) still see it |
| `event.done(claim=False)` | ✘ | ✔ | Only block (e.g., firewall/limiting), but do not perform deduplication |

`event.done(claim=, stop=)` is an alias for `event.mark_processed(claim=, stop=)`, with identical parameters and behavior.

```python
@command("help")
async def help_cmd(event):
    event.done()            # Claim + Block (standard practice after command completion)

@message.on_message(priority=50)
async def observer(event):
    event.done(stop=False)  # Only claim: lower-priority still executes (logging/statistics)

@message.on_message(priority=100)
async def firewall(event):
    if denied(event):
        event.done(claim=False)  # Only block: lower-priority does not execute, but no deduplication
```

### block Configuration for Commands and Replies

**Commands are claimed immediately upon match**: Once a message matches a registered command name (including subcommands/aliases), regardless of subsequent scope or permission judgment results, it will be claimed and default to blocking propagation—commands rejected by permission will not leak to lower-priority message handlers (eliminating "double response" where a command is rejected and then the on_message responds again).

Blocking propagation can be configured to allow lower-priority observers (logging/auditing/permission) to still see these messages:

```toml
[ErisPulse.event.command]
block = false   # Command messages continue to flow to lower-priority handlers (claim is unaffected, will not be re-consumed)

[ErisPulse.event.wait_reply]
block = false   # Replies consumed by wait_reply continue to flow to lower-priority handlers
```

> Note: `block` only controls **blocking** (stop), does not affect **claiming** (claim)—matched commands will never be re-consumed by message handlers; messages that do not match any command flow as usual to message handlers.

## Handling Notice Events

### Friend Addition

```python
from ErisPulse.Core.Event import notice

@notice.on_friend_add()
async def friend_add_handler(event):
    user_id = event.get_user_id()
    nickname = event.get_user_nickname() or "New friend"
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

## Handling Request Events

### Friend Request

```python
from ErisPulse.Core.Event import request

@request.on_friend_request()
async def friend_request_handler(event):
    user_id = event.get_user_id()
    comment = event.get_comment()
    
    sdk.logger.info(f"Received friend request: {user_id}, comment: {comment}")
    
    # You can handle the request through the adapter API
    # Refer to the adapter documentation for specific implementation
```

### Group Invitation Request

```python
@request.on_group_request()
async def group_request_handler(event):
    group_id = event.get_group_id()
    user_id = event.get_user_id()
    
    await event.reply(f"Received invitation to group {group_id} from {user_id}")
```

## Handling Meta Events

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
    sdk.logger.debug(f"{platform} heartbeat detected")
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

# @ a single user
await event.reply("Hello", at_users=["user123"])

# @ multiple users
await event.reply("Hello everyone", at_users=["user1", "user2", "user3"])

# Reply to a message
await event.reply("Reply content", reply_to="msg_id")

# @ all members
await event.reply("Announcement", at_all=True)

# Combination usage: @ user + reply to message
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
> **Commands remain available during waiting** (2.8.3+): Messages starting with a command prefix and matching a registered command (e.g., `/cancel`) will **execute the command** rather than serve as reply content, keeping the wait suspended—users can cancel/switch at any time, and the command executes and continues to reply. For the old behavior of "waiting to swallow all text," configure `ErisPulse.event.wait_reply.cmdpass = true`, or use `wait_reply(cmdpass=True)` for a single instance.

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
    
    await event.reply("Confirm this operation? (yes/no)")
    
    await event.wait_reply(
        timeout=30,
        callback=handle_confirmation
    )
```

### Confirmation dialog (confirm)

Wait for user confirmation or negation, automatically recognize built-in Chinese and English confirmation words:

```python
@command("confirm", help="Confirm operation")
async def confirm_handler(event):
    if await event.confirm("Are you sure to execute this operation?"):
        await event.reply("Confirmed, executing...")
    else:
        await event.reply("Cancelled")

# Custom confirmation words
if await event.confirm("Continue?", yes_words={"go", "continue"}, no_words={"stop", "stop"}):
    pass
```

### Selection menu (choose)

Users can reply with option number or option text:

```python
@command("choose", help="Choose")
async def choose_handler(event):
    choice = await event.choose(
        "Please select color:",
        ["red", "green", "blue"]
    )
    
    if choice is not None:
        colors = ["red", "green", "blue"]
        await event.reply(f"You selected: {colors[choice]}")
    else:
        await event.reply("Timeout, no choice made")
```

**Merge mode**: `merge_prompt=True` combines options into the prompt message, sending them as a single message using the specified `method`:

```python
# Send merged prompt + options as Markdown
choice = await event.choose(
    "## Please select color\n{options}\nPlease reply with number",
    ["red", "green", "blue"],
    method="Markdown",
    merge_prompt=True,
)
```

> The `{options}` placeholder controls the insertion position of options; if not written, it appends to the end of the prompt. You can customize the placeholder with the `placeholder` parameter (e.g., `placeholder="[choices]"`). `options_format="auto"` (default) automatically selects the style based on method: unordered list for Markdown, ordered list for Html, plain text list for others. Text-based methods (Text/Markdown/Html, etc.) default to merging options to the end; non-text methods (Image, etc.) default to splitting into two messages.

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
        await event.reply("Registration timeout or invalid input")
```

### Wait for any event (wait_for)

Wait for an event satisfying conditions, not limited to the same user:

```python
@command("wait_member", help="Wait for new member")
async def wait_member_handler(event):
    await event.reply("Waiting for group member to join...")
    
    evt = await event.wait_for(
        event_type="notice",
        condition=lambda e: e.get_detail_type() == "group_member_increase",
        timeout=120
    )
    
    if evt:
        await event.reply(f"Welcome new member: {evt.get_user_id()}")
    else:
        await event.reply("Timeout")
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
            await conv.say("Conversation timeout, goodbye!")
            break
        
        text = reply.get_text()
        
        if text == "exit":
            await conv.say("Goodbye!")
            break
        
        await conv.say(f"You said: {text}, continue or reply 'exit' to end")
```

### Built-in confirmation words

ErisPulse includes built-in sets of Chinese and English confirmation words:

- **Confirmation words** (`CONFIRM_YES_WORDS`): 是、yes、y、确认、确定、好、好的、ok、true、对、嗯、行、同意、没问题...
- **Negation words** (`CONFIRM_NO_WORDS`): 否、no、n、取消、不、不要、不行、cancel、false、错、拒绝、不可以...

## Event Data Access

### Common Event Object Methods

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

### Platform-specific Extension Methods

In addition to built-in methods, each platform adapter registers platform-specific methods, allowing you to access platform-specific data.

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

If unsure whether a platform has registered a particular method, you can query which methods a platform has registered:

```python
from ErisPulse.Core.Event import get_platform_event_methods

methods = get_platform_event_methods("telegram")
# ["get_chat_type", "is_bot_message", ...]
```

> For platform-specific methods registered by each platform, refer to the corresponding [Platform Documentation](../platform-guide/).

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
    
    # Use module-specific logging
    from ErisPulse import sdk
    logger = sdk.logger.get_child("MyHandler")
    logger.debug(f"Detailed debug information")
```

### 3. Conditional Handling

```python
@message.on_message(priority=0)
async def conditional_handler(event):
    """Conditional handling - judge within handler"""
    # Only handle messages from specific users
    if event.get_user_id() in ["bot1", "bot2"]:
        return
    
    # Only handle messages containing specific keywords
    if "keyword" not in event.get_text():
        return
    
    await event.reply("Condition met, processing message")
```