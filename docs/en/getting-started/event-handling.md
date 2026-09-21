# Event Handling Introduction

This guide introduces how to handle various events in ErisPulse.

## Event Type Overview

ErisPulse supports the following event types:

| Event Type | Description | Applicable Scenarios |
|---------|------|---------|
| Message Event | Any message sent by a user | Chatbots, content filtering |
| Command Event | Messages starting with a command prefix | Command processing, function entry points |
| Notice Event | System notifications (friend additions, group member changes, etc.) | Welcome messages, status notifications |
| Request Event | User requests (friend requests, group invitations) | Automatic request handling |
| Meta Event | System-level events (connection, heartbeat) | Connection monitoring, status checks |

## Handling Message Events

> **Tip**: It is recommended to use the `Event` type annotation in event handlers to benefit from IDE auto-completion and type checking support.

```python
from ErisPulse.Core.Event import Event  # Import event types for annotations
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

### Wildcard and Regular Expression Listening

The four message decorators (`on_message` / `on_private_message` / `on_group_message` / `on_at_message`) support `pattern` (glob wildcard) and `regex` (regular expression). Messages that do not match **will not trigger** the handler:

```python
# Glob wildcard: * for any string, ? for single character, [seq] for character set
@message.on_message(pattern="签到*")
async def signin_handler(event: Event):
    await event.reply("Sign-in successful")

# Regular expression: match amount
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

@command("help", help="Show help information")
async def help_handler(event):
    help_text = """
Available commands:
/help - Show help
/ping - Test connection
/info - View information
    """
    await event.reply(help_text)
```

### Command Aliases

```python
@command(["help", "h"], aliases=["帮助"], help="Show help information")
async def help_handler(event):
    await event.reply("Help information...")
```

Users can invoke the command using any of the following:
- `/help`
- `/h`
- `/帮助`

### Command Arguments

```python
@command("echo", help="Echo the message")
async def echo_handler(event):
    # Get command arguments
    args = event.get_command_args()
    
    if not args:
        await event.reply("Please enter the message to echo")
    else:
        await event.reply(f"You said: {' '.join(args)}")
```

Arguments preserve the original case of user input (even if configured to be case-insensitive, command name matching normalization does not affect argument content).

### Declarative Arguments and Options (`args=` / `options=`)

Manual argument parsing requires handling type conversion and error messages yourself. After declaring `args=` / `options=`, the framework automatically parses command arguments and injects them by name into the handler after permission checks pass; when users input incorrectly, it automatically replies with localized error messages and usage (without throwing an exception crash), and `/help <command>` automatically displays usage:

```python
@command(
    "roll",
    args="<count:int> [sides:int=6]",
    options={"verbose": "-v/--verbose", "label": "--label"},
    help="Roll dice",
)
async def roll_handler(event, count: int, sides: int = 6, verbose: bool = False, label: str = ""):
    total = sum(random.randint(1, sides) for _ in range(count))
    await event.reply(f"Rolled {count} dice with {sides} sides, total points: {total}")
```

`args=` positional argument syntax: `<count:int>` required, `[sides:int=6]` optional (with default value). Supported types:

| Type | Example Input | Description |
|------|---------|------|
| `str` | `hello` | Text (default type) |
| `int` / `float` | `3` / `0.5` | Numeric |
| `bool` | `是` / `yes` / `はい` / `да` / `true` / `no` / `取消` | Boolean, reuses confirmation word list from `Event.confirm()` |
| `literal` | `<mode:literal=fast|slow>` | Enum, only accepts listed values; optional form defaults to first |
| `duration` | `90s`、`1h30m`、`1d` | Duration, converted to float in seconds |
| `rest` | `<text:rest>` | Remaining full text (must be last) |

`options=` options are declared as a dictionary: key is the handler parameter name, value is the flag form (multiple aliases separated by `/`). Parameters annotated as `bool` are boolean flags (set to `True` if present); others (defaulting to `str`) are value options, supporting both `--label hello` and `--label=hello` value forms, with type following the handler annotation. Options are first recognized and removed, remaining tokens are parsed according to `args=` (with `rest` covering the remaining text after option removal).

**Behavior Points**:

- Permission checks precede argument parsing—users without permission do not trigger parsing
- Parsing failure (type mismatch / missing parameters / too many parameters / unknown options) automatically replies with localized error + usage, the command is still claimed
- The declared parameter names must exist in the handler signature, otherwise a `ValueError` is thrown at registration
- Commands without `args=` / `options=` declaration behave unchanged (backward compatibility)

### Command Cooldown (`cooldown=`)

Manual cooldown timing can be replaced with the `cooldown=` declaration. Duration syntax is consistent with the `duration` type in `args=` (e.g., `"30s"`, `"1h30m"`, `"1d"`):

```python
@command("daily", cooldown="1d", cooldown_key="user", cooldown_reply="Already checked in today")
async def daily_handler(event):
    await event.reply("Check-in successful!")
```

`cooldown_key=` controls the granularity of the cooldown: `"user"` (default, shared by the same user), `"session"` (shared by the same session, e.g., the same group), `"global"` (shared by all users and all sessions).

**Behavior Points**:

- If cooldown is hit, it is **silently discarded** by default (symmetrical to silent scope); if `cooldown_reply=` is declared, it replies with the specified text when cooldown is hit
- The command is claimed immediately upon hitting cooldown—commands that hit cooldown are not missed by lower-priority message handlers
- Cooldown starts timing before all permission checks and argument parsing are passed, and before the command is actually executed: users without permission do not trigger cooldown, and parameter errors do not consume cooldown
- The status is in-process memory, automatically cleared when the module is unloaded; cross-process sharing / persistent storage across restarts is not in scope
- Declaration is validated at registration (fail-fast): invalid duration syntax, `cooldown_key=` not in whitelist, `cooldown_reply=` not paired with `cooldown=` all throw `ValueError`

### Dependency Injection (`Depends`)

Common dependencies (database sessions, configuration reading, etc.) can be extracted as dependency functions. Handlers declare dependencies as default values using `Depends(dependency function)`, and the framework automatically calls the dependency function with the context object and injects it by name before calling:

```python
from ErisPulse.Core import Depends

async def get_session(event):
    return await sdk.module.call("DB", "get_session")

@command("admin")
async def admin_handler(event, db=Depends(get_session)):
    ...
```

Request-level caching is enabled by default: within the same event dispatch, the same dependency function is parsed only once, and all injection points share the result (e.g., `get_db` only creates one database session within a single event); it is not reused across requests. You can disable caching for a single dependency using `Depends(get_db, use_cache=False)`.

Covers all framework injection points—command handlers, event handlers (`message.on_message()` etc.), lifecycle hooks (`sdk.lifecycle.on`), SSE route handlers. The first parameter of the dependency function is the context object of the injection point (event scene is `Event`, lifecycle is event `data`, route is `HttpRequest` / `SseEmitter`); both synchronous and asynchronous dependency functions can be declared.

**Declaring services from other modules** (syntactic sugar):

```python
@command("query")
async def query_handler(event, session=Depends.module("DB", "get_session")):
    ...
```

`Depends.module(module_name, method_name, *fixed_args)` is equivalent to calling `sdk.module.call(...)` within the dependency function. Module instantiation (`__init__`) is not covered—there is no context object during instantiation; for HTTP routes carried by FastAPI, use FastAPI's native `fastapi.Depends`.

**Behavior Points**:

- Declaration is validated at registration (fail-fast): dependency is not callable, or conflicts with `args=` / `options=` parameters throw `ValueError`
- Exceptions thrown by dependency functions and handler exceptions are handled at the same level (command automatically replies with errors)
- Handlers without `Depends` declaration have zero overhead (no reflection during dispatch)
- For HTTP routes carried by FastAPI, use FastAPI's native `fastapi.Depends`

### Command Groups

```python
@command("admin.reload", group="admin", help="Reload module")
async def reload_handler(event):
    await event.reply("Module reloaded")

@command("admin.stop", group="admin", help="Stop bot")
async def stop_handler(event):
    await event.reply("Bot stopped")
```

The `group` parameter is only used for categorizing help lists; in the above example, `admin.reload` is a **single command name** (the dot is just a naming style, users need to input `/admin.reload`).

### Subcommands

Command names support **multi-token forms separated by spaces**, enabling subcommands like `/admin add` and `/admin user ban`:

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

- `/admin add x` matches `admin add` first, `event.get_command_args()` returns `["x"]` (arguments after the subcommand name)
- When only `admin` is registered, `/admin add x` matches `admin`, `get_command_args()` returns `["add", "x"]` (unchanged historical behavior)
- Alias supports multi-token forms (e.g., `a remove`), single-token aliases (e.g., `a`) can also point to subcommands
- When parent and child commands are both registered, unregistered subcommands (e.g., `/admin list x`) fall back to the parent command

**Permission Inheritance**: When subcommands do not declare `permission`, they automatically inherit the nearest ancestor command on the parent chain that declared permission—protecting `/admin` automatically protects all its subcommands; permission declared in the subcommand itself takes precedence:

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

Note: `master=True` and `hidden` **do not** inherit; declare them separately on subcommands when needed; user ACL (whitelist/blacklist) matches full command name, glob rules like `"admin*"` can cover entire groups of subcommands.

In the `/help` command overview, subcommands are automatically displayed indented under visible parent commands (`admin` → `admin add` indented one level, `admin user` → `admin user ban` indented two levels).

### Command Permissions and Access Control

Command permissions are divided into three layers, determined from top to bottom (if the upper layer rejects, lower layers are not checked):

```python
# ① Command permission ACL (user-side configuration): user whitelist/blacklist for commands, replies "Permission denied" when denied
# ② master=True — only the framework owner can execute (framework automatically checks, replies "Permission denied" when denied)
@command("restart", master=True, help="Restart module")
async def restart_handler(event):
    await event.reply("Module restarted")

# ③ permission=callable function — command-specific control logic (executes only if returns True)
def is_admin(event):
    return event.get_user_id() in {"user123", "user456"}

@command("panel", permission=is_admin, help="Admin panel")
async def panel_handler(event):
    await event.reply("Welcome to the admin panel")
```

**Command User ACL** (`ErisPulse.event.command.acl`): Users can configure user whitelist/blacklist for any command, command names support exact and glob patterns (e.g., `"roll*"`), replies "Permission denied" when denied:

```toml
# config.toml — only allow 123456 to execute restart; 666 is always denied
[ErisPulse.event.command.acl.restart]
allow = ["onebot11:123456"]
deny = ["onebot11:666"]
```

Order of determination: `deny` hit → deny; `allow` non-empty and not hit → deny; when no ACL is configured, follow `event.command.default_allow` (false = strict mode, no ACL means deny; true means give developers default `master=True` / `permission`). Runtime API (command name supports glob):

```python
from ErisPulse.Core.Event import command

command.allow_user("restart", "onebot11", "123456")   # Allow list
command.deny_user("restart", "onebot11", "666")       # Deny list
command.remove_acl("restart")                          # Clear whitelist/blacklist
command.get_acl("restart")                             # Query current list
```

> Command handlers are imported from the event package: `from ErisPulse.Core.Event import command`; can also be accessed via the SDK event package: `sdk.Event.command` (both are the same singleton). Usually already imported within modules (via `from ErisPulse.Core.Event import command`).

Cross-command / cross-user **event-level** access control (whether messages from a certain person / group / Bot are received) is handled by the **identity dimension** of scope (`scope.identity`); **module-level** availability (which modules can be used) is handled by the **module dimension** of scope (`scope.platforms / bots / sessions`).
See [Scope (scope)](../advanced/scope.md).

> Recommendation: Use `master=True` / `permission` for business logic linkage within commands; use the identity dimension of scope for access control based on user / group; use the module dimension of scope for controlling module availability.

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

ErisPulse's event system uses a **parallel execution within the same priority, serial execution across different priorities** scheduling model:

```
Event arrives
    ↓
priority=10 group: [HandlerC || HandlerD] parallel → merge results
    ↓ (if not interrupted)
priority=0 group: [HandlerA || HandlerB] parallel → merge results
    ↓
...
```

- **Parallel within same priority**: Multiple handlers with the same priority execute simultaneously, improving throughput
- **Serial across priorities**: Groups with different priorities execute in order (higher numerical values execute first), ensuring high-priority handlers run first
- **Copy-On-Write**: No copy is created if handlers do not modify, ensuring zero overhead
- **Conflict handling**: When multiple handlers at the same priority modify the same field, the last modification is used and a warning log is recorded
- **Interruption mechanism**: After any handler calls `event.done()` (default) or `event.done(claim=False)`, subsequent lower-priority groups are skipped. The difference between claiming and blocking is explained in the following section [Link Control: Claiming and Blocking](#link-control-claiming-and-blocking)

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

# Serial execution of different priorities
@message.on_message(priority=10)
async def handler_c(event):
    # Highest priority, executes first
    pass
```

> **Concurrency limit**: All matching handlers' tasks are **immediately created**, but a semaphore limits the **number of concurrently executing tasks**, with a default limit of **64** (`ErisPulse.framework.handler_max_concurrency`, supports hot updates). Tasks exceeding the limit queue on the semaphore, waiting for previous tasks to complete before proceeding. This acts as your "pressure relief valve" during event surges.
>
> **Slow logs**: If a single handler takes more than **1 second**, the framework logs a WARNING (`handler_slow`). The waiting time for `wait_reply` is excluded from the timing, so waiting for replies does not cause a false slow report.

## Scope Filtering: Why Didn't My Module Receive the Message

After an event arrives, there are two **silent** filters (neither replies nor reports errors):

1. **Identity dimension** (`ErisPulse.scope.identity`): When an event enters the distribution entry point, it is determined whether to receive based on User > Group > Bot > Adapter.  
   Events that are rejected are **entirely discarded**, and no handler (including the command dispatcher) will be triggered.
2. **Module dimension** (`ErisPulse.scope`): When an event reaches a module's handler/command, it is determined based on Session > Bot > Platform whether the module is available; if it does not pass, it is **silently skipped**.

```toml
# Example 1: Do not propagate all messages in a group
[ErisPulse.scope.identity.sessions.onebot11."group_123"]
deny = true

# Example 2: Block MyModule from a specific Bot
[ErisPulse.scope.bots.onebot11."123456"]
blocked = ["MyModule"]
```

In this case, when messages arrive from that group, the `MyModule` command and event handlers **will not be scheduled**. This is not a bug, but the filtering mechanism—when troubleshooting "module not responding," prioritize checking the identity and module binding of the scope.

- Filter logs are only visible at the **TRACE** level (`core.scope.identity_denied` / `core.scope.denied`), and no trace is visible by default at the INFO level.
- Framework-level handlers (such as the command dispatcher with `scope_exempt=True`) are not affected by the **module dimension**, but are affected by the **identity dimension** (the entire event has been discarded).
- Before command execution, there is a third filter: command user ACL (replies with "insufficient permissions" when denied, see previous section).
- The fourth filter is **event overwriting** (see next section).

> [!NOTE]
> **Relationship between scope filtering and event claiming (claim)**: Both silent filters occur before the handler is **scheduled**—handlers that are filtered out do not have the opportunity to execute and therefore do not participate in the claim status of `event.done()` / `mark_processed()`. Whether an event has been claimed is determined solely by the **actual executed** handlers (command matching claims, reply matching claims, explicit calls); scope rejection neither claims nor blocks (it silently skips, and the message continues through the remaining distribution chain).

> For scope configuration, matching syntax, and runtime API, see [Scope](../../advanced/scope.md).

## Event Override: Overwrite Behavior of Any Event Type Without Modifying Module Code

> [!NOTE]
> This feature requires ErisPulse **2.8.0+**.

Event handlers declare parameters (`pattern` / `regex` / `master` / `hidden`, etc.) at registration time as **default** for developers. The unified override system allows users to overwrite any module's behavior by **event type**—OneBot12 standard types (`meta` / `message` / `notice` / `request`) and ErisPulse extension types (`command`) each have their own set of overridable parameters:

| Event Type | Overridable Parameters | Purpose |
|---------|-----------|------|
| `message` | `pattern` / `regex` / `detail_types` | Text trigger conditions + message subtype whitelist |
| `notice` | `detail_types` / `pattern` / `regex` | Notification subtype whitelist + text conditions |
| `request` | `detail_types` / `pattern` / `regex` | Request subtype whitelist + text conditions |
| `meta` | `detail_types` | Meta-event subtype whitelist (e.g., connect / heartbeat) |
| `command` | `master` / `hidden` / `aliases` / `prefix` / `help` / `usage` | Command implementation parameters (user preference) |
| `acl` (command-specific) | `allow` / `deny` | Command user whitelist/blacklist (by command name glob) |

```toml
# message: Overwrite text trigger conditions (AND with code conditions)
[ErisPulse.event.overrides.message.ChatModule]
pattern = "闲聊*"

# notice: Only respond to specific notification subtypes
[ErisPulse.event.overrides.notice.MyModule]
detail_types = ["group_increase"]

# command: Overwrite implementation parameters (user preference—can tighten or loosen developer defaults)
[ErisPulse.event.overrides.command.MyModule.restart]
master = true
hidden = true

# acl: Command user whitelist/blacklist (across commands via glob)
[ErisPulse.event.overrides.acl."roll*"]
allow = ["onebot11:u_vip"]

# ACL fallback (false = strict mode: no ACL means deny)
acl_default_allow = true
```

Runtime API (`from ErisPulse.Core.Event import overrides` or `sdk.Event.overrides`, **type sub-namespace**—each type has symmetric `set` / `get` / `delete` trio):

```python
from ErisPulse.Core.Event import overrides

overrides.message.set("ChatModule", pattern="闲聊*")   # message text condition
overrides.notice.set("MyModule", detail_types=["group_increase"])
overrides.command.set("MyModule", "restart", master=True)  # command parameter
overrides.acl.set("roll*", deny=["onebot11:u_bad"])    # command user blacklist

overrides.message.get("ChatModule")     # {"pattern": "闲聊*"}
overrides.message.delete("ChatModule")  # Restore developer default
```

- Overwrite conditions and handler code conditions **both take effect** (AND semantics); `command` parameters and developer declarations are **deep merged** (overwrite takes precedence)
- `detail_types`: Events without `detail_type` are allowed (prevents accidental blocking of unknown events)
- `pattern` / `regex`: Events without text (e.g., connect / heartbeat) are not constrained and are directly allowed
- `command` overwrite key `master` synchronously maps to storage key `must_master`; disabled commands go through `acl` deny
- **Key mapping explanation**: In `overrides.command.set("My", "restart", master=True)`, the parameter name `master` is merely a configuration alias. The actual storage key and the key name in `get()` return value are unified as **`must_master`** (`get()` returns `{"must_master": true}`) — runtime checks read from the storage key, do not read by the `master` key name
- Configuration changes take effect immediately (hot update), format validation warnings (unknown parameters / bad entries are ignored)

## Link Control: Claiming and Blocking

> [!NOTE]
> The `event.done()` / `event.mark_processed()` `claim=` / `stop=` parameters for this feature require ErisPulse **2.7.1+**.

ErisPulse decouples the two orthogonal semantics of "claiming" and "blocking" through `event.done()`, making it easier to add observation layers (logging, auditing, permissions) around command processing.

**Precise definitions of the two concepts:**

- **Claiming (claim)**: Mark the event as processed by this handler (write to `_processed`). The command dispatcher, seeing a claimed event, will **skip duplicate processing**—preventing the same message from being processed by multiple command handlers. Typical scenario: Claim after a command matches, preventing the command dispatcher from intervening again.
- **Blocking (stop)**: Prevent the event from propagating to **lower-priority** handlers (write to `_propagation_stopped`). Lower-priority handlers (e.g., `on_message`) will no longer see the event. Typical scenario: High-priority handlers have fully processed the event and do not want lower-priority handlers to execute.

| `event.done(...)` | Claim | Block | Scenario |
|-------------------|------|------|------|
| `event.done()` | ✔ | ✔ | Standard practice for command/handler completion |
| `event.done(stop=False)` | ✔ | ✘ | Claim only: lower-priority observers (logging / statistics) still see it |
| `event.done(claim=False)` | ✘ | ✔ | Block only (e.g., firewall / rate limiting), but do not perform command deduplication |

`event.done(claim=, stop=)` is an alias for `event.mark_processed(claim=, stop=)`; both have identical parameters and behavior.

```python
@command("help")
async def help_cmd(event):
    event.done()            # Claim + Block (standard practice for command completion)

@message.on_message(priority=50)
async def observer(event):
    event.done(stop=False)  # Claim only: lower-priority handlers still execute (logging / statistics)

@message.on_message(priority=100)
async def firewall(event):
    if denied(event):
        event.done(claim=False)  # Block only: lower-priority handlers do not execute, but no deduplication
```

### Block Configuration for Commands and Replies

**Command match equals claim**: Once a message matches a registered command name (including subcommands/aliases), regardless of subsequent scope or permission checks, it will be claimed and default block propagation—commands denied by permission will not leak to low-priority message handlers (eliminating "command denied then on_message responds again" double response).

Block propagation can be configured to allow low-priority observers (logging / audit / permission) to still see these messages:

```toml
[ErisPulse.event.command]
block = false   # Command messages continue to flow to low-priority handlers (claim is unaffected, no repeated consumption)

[ErisPulse.event.wait_reply]
block = false   # Replies consumed by wait_reply continue to flow to low-priority handlers
```

> Note: `block` only controls **blocking** (stop), not **claiming** (claim)—matched commands will never be repeatedly consumed by message handlers; unmatched messages flow as usual to message handlers.

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

### Group Member Addition

```python
@notice.on_group_increase()
async def member_increase_handler(event):
    group_id = event.get_group_id()
    user_id = event.get_user_id()
    await event.reply(f"Welcome new member {user_id} to group {group_id}")
```

### Group Member Removal

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
    
    sdk.logger.info(f"Friend request received: {user_id}, comment: {comment}")
    
    # You can handle the request via the adapter API
    # Specific implementation please refer to each adapter documentation
```

### Group Invitation Request

```python
@request.on_group_request()
async def group_request_handler(event):
    group_id = event.get_group_id()
    user_id = event.get_user_id()
    
    await event.reply(f"Received group {group_id} invitation from {user_id}")
```

## Handling Meta Events

### Connection Events

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

### Heartbeat Events

```python
@meta.on_heartbeat()
async def heartbeat_handler(event):
    platform = event.get_platform()
    sdk.logger.debug(f"{platform} heartbeat detected")
```

### Bot Status Query

After the adapter sends a meta event, the framework automatically tracks the bot status, and you can check it at any time:

```python
from ErisPulse import sdk

# Check if a bot is online
if sdk.adapter.is_bot_online("telegram", "123456"):
    telegram = sdk.adapter.get("telegram")
    await telegram.Send.To("user", "123456").Text("Bot is online")

# List all currently online bots
bots = sdk.adapter.list_bots()
for platform, bot_list in bots.items():
    for bot_id, info in bot_list.items():
        print(f"{platform}/{bot_id}: {info['status']}")

# Get complete status summary
summary = sdk.adapter.get_status_summary()
```

## Interactive Processing

### Sending Replies Using the `reply` Method

The `event.reply()` method supports various modifiers, making it convenient to send messages with features like @ mentions and replies:

```python
# Simple reply
await event.reply("Hello")

# Send messages of different types
await event.reply("http://example.com/image.jpg", method="Image")  # Image
await event.reply("http://example.com/voice.mp3", method="Voice")  # Voice

# @ a single user
await event.reply("Hello", at_users=["user123"])

# @ multiple users
await event.reply("Hello everyone", at_users=["user1", "user2", "user3"])

# Reply to a message
await event.reply("Reply content", reply_to="msg_id")

# @全体成员 (Mention all members)
await event.reply("Announcement", at_all=True)

# Combine: @ users + reply to a message
await event.reply("Content", at_users=["user1"], reply_to="msg_id")
```

### Waiting for User Replies

```python
@command("ask", help="Ask the user")
async def ask_handler(event):
    await event.reply("Please enter your name:")
    
    # Wait for user reply, timeout after 30 seconds
    reply = await event.wait_reply(timeout=30)
    
    if reply:
        name = reply.get_text()
        await event.reply(f"Hello, {name}!")
    else:
        await event.reply("Timeout, please try again.")
```

> [!TIP]
> **Commands remain available during waiting** (2.8.3+): Messages starting with the command prefix and matching registered commands (e.g., `/cancel`) will **execute the command** instead of being treated as reply content, suspending the wait—users can cancel or switch at any time, and after command execution, replies can continue. For the old behavior of "waiting to swallow all text": set `ErisPulse.event.wait_reply.cmdpass = true`, or use `wait_reply(cmdpass=True)` once.

### Waiting for Replies with Validation

```python
@command("age", help="Ask for age")
async def age_handler(event):
    def validate_age(event_data):
        """Validate if the age is valid"""
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

### Waiting for Replies with Callback

```python
@command("confirm", help="Confirm operation")
async def confirm_handler(event):
    async def handle_confirmation(reply_event):
        text = reply_event.get_text().lower()
        
        if text in ["是", "yes", "y"]:
            await event.reply("Operation confirmed!")
        else:
            await event.reply("Operation canceled.")
    
    await event.reply("Confirm this operation? (Yes/No)")
    
    await event.wait_reply(
        timeout=30,
        callback=handle_confirmation
    )
```

### Confirmation Dialogue (`confirm`)

Wait for user confirmation or negation, automatically recognizing built-in Chinese and English confirmation words:

```python
@command("confirm", help="Confirm operation")
async def confirm_handler(event):
    if await event.confirm("Are you sure you want to execute this operation?"):
        await event.reply("Confirmed, executing...")
    else:
        await event.reply("Canceled")

# Custom confirmation words
if await event.confirm("Continue?", yes_words={"go", "continue"}, no_words={"stop", "stop"}):
    pass
```

### Selection Menu (`choose`)

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
        await event.reply("Timeout, no selection made")
```

**Merge mode**: When `merge_prompt=True`, options are merged into the prompt message and sent in a single message using the specified `method`:

```python
# Send merged prompt + options using Markdown
choice = await event.choose(
    "## Please select a color\n{options}\nPlease reply with the number",
    ["red", "green", "blue"],
    method="Markdown",
    merge_prompt=True,
)
```

> The `{options}` placeholder controls the insertion position of options; if not specified, options are appended to the end of the prompt. You can customize the placeholder using the `placeholder` parameter (e.g., `placeholder="[choices]"`). `options_format="auto"` (default) automatically selects the style based on the method: unordered list for Markdown, ordered list for Html, and plain text list otherwise. For text-based methods (Text/Markdown/Html, etc.), options are merged by default; for non-text methods (Image, etc.), options are sent as separate messages by default.

### Collecting Forms (`collect`)

Collect user input across multiple steps:

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

### Waiting for Any Event (`wait_for`)

Wait for any event that meets a specified condition, not limited to the same user:

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
        await event.reply("Timeout")
```

### Multi-turn Dialogue (`conversation`)

Create an interactive multi-turn dialogue context:

```python
@command("survey", help="Survey")
async def survey_handler(event):
    conv = event.conversation(timeout=60)
    
    await conv.say("Welcome to the survey!")
    
    while conv.is_active:
        reply = await conv.wait()
        
        if reply is None:
            await conv.say("Dialogue timeout, goodbye!")
            break
        
        text = reply.get_text()
        
        if text == "Exit":
            await conv.say("Goodbye!")
            break
        
        await conv.say(f"You said: {text}, continue typing or reply 'Exit' to end")
```

### Built-in Confirmation Words

ErisPulse includes built-in Chinese and English confirmation word sets:

- **Confirmation words** (`CONFIRM_YES_WORDS`): 是、yes、y、确认、确定、好、好的、ok、true、对、嗯、行、同意、没问题...
- **Negation words** (`CONFIRM_NO_WORDS`): 否、no、n、取消、不、不要、不行、cancel、false、错、拒绝、不可以...

## Event Data Access

### Common Event Object Methods

```python
@command("info")
async def info_handler(event):
    # Basic info
    event_id = event.get_id()
    event_time = event.get_time()
    event_type = event.get_type()
    detail_type = event.get_detail_type()
    
    # Sender info
    user_id = event.get_user_id()
    nickname = event.get_user_nickname()
    
    # Message content
    message_segments = event.get_message()
    alt_message = event.get_alt_message()
    text = event.get_text()
    
    # Group info
    group_id = event.get_group_id()
    
    # Bot info
    self_id = event.get_self_user_id()
    self_platform = event.get_self_platform()
    
    # Raw data
    raw_data = event.get_raw()
    raw_type = event.get_raw_type()
    
    # Platform info
    platform = event.get_platform()
    
    # Message type check
    is_private = event.is_private_message()
    is_group = event.is_group_message()
    is_at = event.is_at_message()
    
    # Command info
    if event.is_command():
        cmd_name = event.get_command_name()
        cmd_args = event.get_command_args()
        cmd_raw = event.get_command_raw()
```

### Platform-Specific Methods

In addition to built-in methods, each platform adapter registers platform-specific methods, making it easier for you to access platform-specific data.

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

If unsure whether a platform has registered a specific method, you can query which methods a platform has registered:

```python
from ErisPulse.Core.Event import get_platform_event_methods

methods = get_platform_event_methods("telegram")
# ["get_chat_type", "is_bot_message", ...]
```

> Platform-specific registered methods are detailed in the corresponding [Platform Documentation](../platform-guide/).

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
    logger.debug(f"Debug information")
```

### 3. Conditional Handling

```python
@message.on_message(priority=0)
async def conditional_handler(event):
    """Conditional handling - check conditions within handler"""
    # Only process messages from specific users
    if event.get_user_id() in ["bot1", "bot2"]:
        return
    
    # Only process messages containing specific keywords
    if "keyword" not in event.get_text():
        return
    
    await event.reply("Condition met, processing message")
```

## Next Steps

- [Common Tasks Examples](common-tasks.md) - Learn to implement common features (including advanced message sending: retry/timeout/batch)
- [Platform Features Guide](../platform-guide/README.md) - Complete explanation of Send DSL chain sending, sending rules, and batch building
- [Event Wrapper Class Details](../developer-guide/modules/event-wrapper.md) - Deep dive into the Event object
- [User Guide](../user-guide/) - Learn about configuration and module management