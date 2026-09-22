# Getting Started with Event Handling

This guide introduces how to handle various event types in ErisPulse.

## Event Type Overview

ErisPulse supports the following event types:

| Event Type | Description | Applicable Scenarios |
|---------|------|---------|
| Message Event | Any message sent by a user | Chatbots, content filtering |
| Command Event | Messages starting with a command prefix | Command processing, entry points |
| Notice Event | System notifications (friend additions, group member changes, etc.) | Welcome messages, status notifications |
| Request Event | User requests (friend requests, group invitations) | Automatic handling of requests |
| Meta Event | System-level events (connection, heartbeat) | Connection monitoring, status checks |

## Handling Message Events

> **Note**: It is recommended to use the `Event` type annotation in event handlers to gain IDE auto-completion and type checking support.

```python
from ErisPulse.Core.Event import Event  # Import event types for annotation
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
    # Get the list of mentioned users
    mentions = event.get_mentions()
    await event.reply(f"You mentioned these users: {mentions}")
```

### Wildcards and Regular Expression Listening

The four message decorators (`on_message` / `on_private_message` / `on_group_message` /
`on_at_message`) support both `pattern` (glob wildcard) and `regex` (regular expression). Messages that do not match will **not trigger** the handler:

```python
# Glob wildcard: * matches any string, ? matches any single character, [seq] matches any character in the set
@message.on_message(pattern="Sign up*")
async def signin_handler(event: Event):
    await event.reply("Sign-in successful")

# Regular expression: match amounts
@message.on_message(regex=r"\d+\s*元")
async def price_handler(event: Event):
    await event.reply(f"Received amount: {event.get_text()}")

# Both pattern and regex given → both must match
@message.on_message(pattern="*元", regex=r"\d+\s*元")
async def combined_handler(event: Event):
    pass
```

`wait_reply` also supports these two parameters (see [Wait for Reply Functionality](../developer-guide/modules/event-wrapper.md#wait-for-reply-functionality)).

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

Users can call it using any of the following:
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

Arguments retain the original case input by the user (even if configured to be case-insensitive, case normalization of the command name does not affect the argument content).

### Declared Arguments and Options (`args=` / `options=`)

Manually parsing arguments requires handling type conversion and error messages yourself. After declaring `args=` / `options=`, the framework automatically parses command arguments and **injects them by name** after passing permission checks; when user input is incorrect, it automatically replies with localized error messages and usage (without throwing an exception crash), and `/help <command>` will automatically show usage:

```python
@command(
    "roll",
    args="<count:int> [sides:int=6]",
    options={"verbose": "-v/--verbose", "label": "--label"},
    help="Roll dice",
)
async def roll_handler(event, count: int, sides: int = 6, verbose: bool = False, label: str = ""):
    total = sum(random.randint(1, sides) for _ in range(count))
    await event.reply(f"Rolled {count} times {sides}-sided dice, total points: {total}")
```

`args=` positional parameter syntax: `<count:int>` is required, `[sides:int=6]` is optional (with a default value). Supported types:

| Type | Example Input | Description |
|------|---------|------|
| `str` | `hello` | Text (default type) |
| `int` / `float` | `3` / `0.5` | Numeric |
| `bool` | `是` / `yes` / `はい` / `да` / `true` / `no` / `取消` | Boolean, reuses the confirmation word list from `Event.confirm()` |
| `literal` | `<mode:literal=fast|slow>` | Enum, accepts only listed values; optional form defaults to the first |
| `duration` | `90s`、`1h30m`、`1d` | Duration, converted to float in seconds |
| `rest` | `<text:rest>` | Remaining full text (must be at the end) |

`options=` options are declared as a dictionary: the key is the handler parameter name, the value is the flag form (multiple aliases separated by `/`). Parameters annotated as `bool` are boolean flags (appear as `True`); others (default as `str`) are value options, supporting both `--label hello` and `--label=hello` value forms, with the type following the handler annotation. Options are first identified and removed, then the remaining tokens are parsed according to `args=` (the `rest` overrides the remaining text after option removal).

**Behavior Points**:

- Permission checks precede argument parsing—users without permission will not trigger parsing
- Parsing failures (type mismatch / missing parameters / too many parameters / unknown options) automatically reply with localized errors + usage, and the command is still claimed
- The declared parameter names must exist in the handler signature, otherwise a `ValueError` is thrown during registration
- Commands without `args=` / `options=` have completely unchanged behavior (backward compatibility)

### Command Governance (`cooldown=` / `rate_limit=` / `deprecated=`)

Manual cooldown timing, rate limiting windows, and deprecation prompts can be replaced with declarations, all three can be combined.

**Cooldown**—the duration syntax is consistent with the `duration` type in `args=` (e.g., `"30s"`, `"1h30m"`, `"1d"`):

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

Key granularity (`cooldown_key=` / `rate_limit_key=`): `"user"` (default, shared by the same user), `"session"` (shared by the same session, like the same group), `"global"` (shared by all users and all sessions).

**Behavior Points**:

- Cooldown / rate limit hits default to **silent discard** (symmetrical to scope silence); declare `cooldown_reply=` / `rate_limit_reply=` to reply with this text on hit
- The command is claimed as soon as it hits—governed commands do not leak to lower-priority message handlers
- Governance checks are performed after all permission checks and argument parsing pass, before actual execution: users without permission do not trigger, argument errors do not consume
- When both cooldown and rate limit are declared, cooldown is checked first (cooldown hit does not occupy the rate limit window)
- `deprecated=` defaults to replying with the deprecation text and **continues execution**; `deprecated_reject=True` rejects execution (the `command.executed` hook records `success=False, error="deprecated"`)
- `/help` list and single command help automatically display deprecation markers and text
- Status is in-process memory, automatically cleared when the module is unloaded; cross-process sharing / persistent restart is not included
- Declaration is validated at registration time (fail-fast): illegal syntax, key granularity not in whitelist value, reply not paired with main declaration all throw `ValueError`

### Handler Throttling (`throttle=`) and Debouncing (`debounce=`)

Message handler anti-spam declaration—events with the same key are processed at most once within the interval, others are silently discarded:

```python
from ErisPulse import sdk

@sdk.message.on_message(throttle="2s", throttle_key="user")
async def handler(event): ...
```

Debounce and throttling are complementary: **only the last one is executed within the window**, previous pending tasks are automatically canceled (suitable for "process after stopping input" search suggestion scenarios):

```python
@sdk.message.on_message(debounce="2s", debounce_key="user")
async def search(event): ...
```

`on_message` / `on_private_message` / `on_group_message` / `on_at_message` all support it; `throttle_key=` / `debounce_key=` use the same key granularity as command governance (`user` / `session` / `global`), and the duration syntax is consistent with `duration`. Throttling and `pattern=` / `regex=` conditions are overlapped and effective (all must match to trigger); discarded within the interval only logs TRACE; declaration is validated at registration time; `throttle=` and `debounce=` have mutually exclusive semantics (throwing `ValueError` if both are declared simultaneously).

### Dependency Injection (`Depends`)

Common dependencies (database sessions, configuration reading, etc.) can be extracted as dependency functions. Handlers declare them as `Depends(dependency function)` with a default value, and the framework automatically calls the dependency function with the context object before calling and injects it by name:

```python
from ErisPulse.Core import Depends

async def get_session(event):
    return await sdk.module.call("DB", "get_session")

@command("admin")
async def admin_handler(event, db=Depends(get_session)):
    ...
```

Default **request-level caching** is enabled: within the same event dispatch, the same dependency function is only resolved once, and all injection points share the result (e.g., `get_db` only creates one database session in one event); it is automatically not reused across requests. You can disable caching for a single dependency with `Depends(get_db, use_cache=False)`.

Covers all framework injection points—command handlers, event handlers (`message.on_message()` etc.), lifecycle hooks (`sdk.lifecycle.on`), SSE route handlers. The first parameter of the dependency function is the context object of the injection point (event scenario is `Event`, lifecycle is event `data`, route is `HttpRequest` / `SseEmitter`); both synchronous and asynchronous dependency functions can be declared.

**Syntax sugar for declaring other module services**:

```python
@command("query")
async def query_handler(event, session=Depends.module("DB", "get_session")):
    ...
```

`Depends.module(module name, method name, *fixed arguments)` is equivalent to calling `sdk.module.call(...)` inside the dependency function. Module instantiation (`__init__`) is not covered—the context object is not available during instantiation; for FastAPI hosted HTTP routes, use FastAPI's native `fastapi.Depends`.

**Behavior Points**:

- Declaration is validated at registration time (fail-fast): if the dependency is not callable, or conflicts with `args=` / `options=` parameters, a `ValueError` is thrown
- Exceptions thrown by the dependency function are handled in the same way as exceptions in the handler itself (command automatically replies with errors)
- Handlers without `Depends` have zero overhead (no reflection during dispatch)
- For FastAPI hosted HTTP routes, use FastAPI's native `fastapi.Depends`

### Command Groups

```python
@command("admin.reload", group="admin", help="Reload module")
async def reload_handler(event):
    await event.reply("Module reloaded")

@command("admin.stop", group="admin", help="Stop bot")
async def stop_handler(event):
    await event.reply("Bot stopped")
```

The `group` parameter is only used for grouping in help lists; the example above's `admin.reload` is a **single command name** (the dot is just a naming style, users need to input `/admin.reload`).

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

- `/admin add x` prioritizes matching `admin add`, `event.get_command_args()` returns `["x"]` (arguments after the subcommand name)
- Only `admin` is registered, `/admin add x` matches `admin`, `get_command_args()` returns `["add", "x"]` (legacy behavior unchanged)
- Alias supports multi-token form (e.g., `a remove`), single-token alias (e.g., `a`) can also point to subcommands
- When parent and child commands are registered simultaneously, unregistered subcommands (e.g., `/admin list x`) fall back to the parent command

**Permission Inheritance**: If a subcommand does not declare `permission`, it automatically inherits the nearest ancestor command that declared permission on the parent chain—protecting `/admin` automatically protects all its subcommands; the subcommand's own permission declaration takes precedence:

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

Note: `master=True` and `hidden` **do not** inherit, they need to be declared separately on the subcommand; user ACL (whitelist/blacklist) matches by full command name, glob rules like `"admin*"` can cover entire subcommand groups.

In the `/help` command overview, subcommands are automatically displayed indented under visible parent commands (e.g., `admin` → `admin add` indented one level, `admin user` → `admin user ban` indented two levels).

### Command Permissions and Access Control

Command permissions are divided into three layers, checked from top to bottom (if the upper layer rejects, the lower layer is not checked):

```python
# ① Command Permission ACL (user-side configuration): by user whitelist/blacklist of commands, reply "insufficient permission" on rejection
# ② master=True — only the framework owner can execute (framework automatically checks, reply "insufficient permission" on rejection)
@command("restart", master=True, help="Restart module")
async def restart_handler(event):
    await event.reply("Module restarted")

# ③ permission=call function — command's own control logic (returns True to execute)
def is_admin(event):
    return event.get_user_id() in {"user123", "user456"}

@command("panel", permission=is_admin, help="Management panel")
async def panel_handler(event):
    await event.reply("Welcome to the management panel")
```

**Command User ACL** (`ErisPulse.event.command.acl`): Users can configure user whitelist/blacklist for any command, command names support exact and glob patterns (e.g., `"roll*"`), reply "insufficient permission" on rejection:

```toml
# config.toml — allow only 123456 to execute restart; 666 is rejected
[ErisPulse.event.command.acl.restart]
allow = ["onebot11:123456"]
deny = ["onebot11:666"]
```

Check order: `deny` hit → reject; `allow` non-empty and not hit → reject; if ACL is not configured, follow `event.command.default_allow` (false = strict mode, no ACL means reject; true means leave to developer default `master=True` / `permission`). Runtime API (command name supports glob):

```python
from ErisPulse.Core.Event import command

command.allow_user("restart", "onebot11", "123456")   # allow list
command.deny_user("restart", "onebot11", "666")       # deny list
command.remove_acl("restart")                          # clear whitelist/blacklist
command.get_acl("restart")                             # query current list
```

> Command handler imported from event package: `from ErisPulse.Core.Event import command`;
> can also be accessed via SDK event package: `sdk.Event.command` (both are the same singleton).
> Usually imported within modules (via `from ErisPulse.Core.Event import command`).

Cross-command / cross-user **event-level** access control (whether a person / group / bot's message is received or not)
goes through **identity dimension** of scope ( `scope.identity` ); **module-level** availability (which modules can be used)
goes through **module dimension** of scope ( `scope.platforms / bots / sessions` ).
See [Scope](../advanced/scope.md).

> Recommendation: Use `master=True` / `permission` for command internal business logic linkage; for access control based on user / group, use scope identity dimension; for module availability control, use scope module dimension.

### Command Priority

```python
# Higher priority number executes earlier
@message.on_message(priority=10)
async def high_priority_handler(event):
    await event.reply("High priority handler")

@message.on_message(priority=1)
async def low_priority_handler(event):
    await event.reply("Low priority handler")
```

### Parallel Event Handling

ErisPulse's event system adopts a scheduling model of **parallel within the same priority, serial across different priorities**:

```
Event arrival
    ↓
priority=10 group: [Handler C || Handler D] parallel → merge results
    ↓ (if not interrupted)
priority=0 group: [Handler A || Handler B] parallel → merge results
    ↓
...
```

- **Parallel within the same priority**: Multiple handlers with the same priority execute simultaneously, improving throughput
- **Serial across priorities**: Groups with different priorities execute in order (the higher the number, the earlier it executes), ensuring high-priority handlers run first
- **Copy-On-Write**: Handlers do not create a copy if no modifications are made, ensuring zero overhead
- **Conflict handling**: When multiple handlers with the same priority modify the same field, the last modification is used, and a warning log is recorded
- **Interrupt mechanism**: After any handler calls `event.done()` (default) or `event.done(claim=False)`, subsequent lower-priority groups are skipped. The difference between claiming and blocking is described in the following section [Link Control: Claiming and Blocking](#link-control-claiming-and-blocking)

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

# Different priorities execute in serial
@message.on_message(priority=10)
async def handler_c(event):
    # Highest priority, executes first
    pass
```

> **Concurrency Limit**: All matching handlers' tasks are **immediately created**, but a semaphore limits the **number of concurrent executions**, with a default upper limit of **64** (`ErisPulse.framework.handler_max_concurrency`, supports hot updates). Tasks exceeding the limit queue up on the semaphore and proceed only after previous tasks complete. This is your "pressure relief valve" during event spikes.
>
> **Slow Logs**: If a single handler takes more than **1 second**, the framework logs a WARNING (`handler_slow`). The waiting time for `wait_reply` is excluded from the timing, so it won't falsely report slow due to "waiting for a reply."

## Middleware: Rewrite or Reject Before Distribution

Middleware executes in sequence before event distribution, serving as the proper implementation point for scenarios like firewalls, rate limiting, and event desensitization:

```python
from ErisPulse.Core import adapter

@adapter.middleware
async def firewall(data):
    if _is_banned(data.get("user_id")):
        return False          # Reject: Event is discarded, not entering any handler, no outbound side effects
    data["checked"] = True    # Return dict: Rewrite the payload (consistent with historical behavior)
    # Return None: Proceed, payload unchanged (historical behavior)
    return data
```

| Return Value | Behavior |
|--------|------|
| `False` | **Reject**: Event is immediately discarded, not entering any handler |
| `dict` | Rewrite the event payload and continue distribution |
| `None` | Proceed, payload unchanged |

When rejected, the framework outputs a TRACE log and triggers the `adapter.event.blocked` lifecycle hook (carrying the middleware name and complete event), for auditing "why the event was not responded to."

## Command Dispatch Decision Chain: Why a Command Didn't Trigger

A command message sequentially goes through: **command text determination → command name/alias match (with spelling suggestions if not matched) → claim on match → scope → user ACL → owner → permission → cooldown/rate limit → argument parsing → execution**. If any step is not satisfied, it terminates; governance hits (cooldown/limit) default to silent discard, permission rejections reply to the user.

In testing, `ErisPulse-Testing`'s `dispatch()` directly returns this decision chain (`DispatchTrace`, `trace.explain()` outputs step-by-step causal explanations), and in production, `ErisPulse.Core.Event.start_dispatch_trace()` can collect the same records.

Additionally, `ErisPulse.runtime` provides two sets of diagnostic APIs: `explain_module(module name)` answers "why the module wasn't loaded" (not registered / lazy-loaded / disabled by configuration / missing dependencies / SDK version not met, each item provides a reason), `explain_event(event)` answers "why the event wasn't responded to" (adapter not registered / identity blacklisted / module session blocked / command not matched); combined with `format_report()` to render human-readable conclusions.

## Scope Filtering: Why My Module Didn't Receive Messages

After an event arrives, there are two **silent** filters (neither replies nor errors):

1. **Identity Dimension** (`ErisPulse.scope.identity`): When an event enters the distribution entry point, it is judged whether to receive it based on user > group > bot > adapter.
   Events rejected by this dimension are **entirely discarded**, and no handler (including the command dispatcher) is triggered.
2. **Module Dimension** (`ErisPulse.scope`): When an event reaches a module's handler/command, it is judged based on session > bot > platform whether the module is available, and **skips silently** if it does not pass.

```toml
# Example 1: All messages in a certain group are not propagated
[ErisPulse.scope.identity.sessions.onebot11."group_123"]
deny = true

# Example 2: Blocking MyModule in a certain bot
[ErisPulse.scope.bots.onebot11."123456"]
blocked = ["MyModule"]
```

At this point, when messages from that group arrive, `MyModule`'s command and event handlers **will not be scheduled**. This is not a bug, but a filtering mechanism—when troubleshooting "module not responding," first check the identity and module binding of the scope.

- Filter logs are only visible at the **TRACE** level (`core.scope.identity_denied` / `core.scope.denied`), and are not visible at the default INFO level
- Framework-level handlers (such as the command dispatcher `scope_exempt=True`) are not affected by the **module dimension**, but are affected by the **identity dimension** (the entire event has been discarded)
- Before command execution, there is a third filter: command user ACL (rejects with "insufficient permission," see the previous section)
- The fourth filter is **event overwriting** (see the next section)

> [!NOTE]
> **Relationship between scope filtering and event claiming (claim)**: The two silent filters occur before the handler is **scheduled**—handlers that are filtered out do not have a chance to execute, and naturally do not participate in the `event.done()` / `mark_processed()` claiming status. Whether an event has been claimed is determined only by **actual execution** of the handler (command match claims, reply match claims, explicit calls); event rejection itself neither claims nor blocks (silently skips, the message continues through the rest of the dispatch chain).

> Scope configuration, matching syntax, and runtime API are detailed in [Scope](../../advanced/scope.md).

## Event Overwriting: Overwrite Any Event Type Behavior Without Modifying Module Code

> [!NOTE]
> This feature requires ErisPulse **2.8.0+**.

The parameters declared by event handlers at registration (such as `pattern` / `regex` / `master` / `hidden`) are only **defaults for developers**.
The unified overwriting system allows users to overwrite the behavior of any module based on **event type**—OneBot12 standard types (meta / message / notice / request) and ErisPulse extended types (command) each have their own set of overwritable parameters:

| Event Type | Overwritable Parameters | Function |
|---------|-----------|------|
| `message` | `pattern` / `regex` / `detail_types` | Text trigger conditions + message sub-type whitelist |
| `notice` | `detail_types` / `pattern` / `regex` | Notification sub-type whitelist + text conditions |
| `request` | `detail_types` / `pattern` / `regex` | Request sub-type whitelist + text conditions |
| `meta` | `detail_types` | Meta-event sub-type whitelist (connect / heartbeat, etc.) |
| `command` | `master` / `hidden` / `aliases` / `prefix` / `help` / `usage` | Command implementation parameters (user priority) |
| `acl` (command-specific) | `allow` / `deny` | Command user whitelist/blacklist (by command name glob) |

```toml
# message: Overwrite text trigger conditions (AND with code-side conditions)
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

# ACL fallback (false = strict mode: no ACL means reject)
acl_default_allow = true
```

Runtime API (via `from ErisPulse.Core.Event import overrides` or `sdk.Event.overrides`, **type sub-namespace**—each type has a symmetric trio of `set` / `get` / `delete`):

```python
from ErisPulse.Core.Event import overrides

overrides.message.set("ChatModule", pattern="闲聊*")   # message text condition
overrides.notice.set("MyModule", detail_types=["group_increase"])
overrides.command.set("MyModule", "restart", master=True)  # command parameter
overrides.acl.set("roll*", deny=["onebot11:u_bad"])    # command user blacklist

overrides.message.get("ChatModule")     # {"pattern": "闲聊*"}
overrides.message.delete("ChatModule")  # Restore developer default
```

- Overwrite conditions and handler code-side conditions **both take effect** (AND semantics); `command` parameter overwrite and developer declaration **deep merge** (overwrite priority)
- `detail_types`: Events without `detail_type` are allowed (no accidental killing of unknown events)
- `pattern` / `regex`: Events without text (connect / heartbeat, etc.) are not constrained and are allowed directly
- `command` overwrite key `master` synchronously maps to storage key `must_master`; disabling commands uniformly goes through `acl` deny
- **Key name mapping explanation**: The parameter name `master` for `overrides.command.set("My", "restart", master=True)` is only an alias for configuration; the actual storage key and the key name returned by `get()` are unified as **`must_master`** (the returned value of `get()` is `{"must_master": true}`)—the runtime judgment reads the storage key, so do not read by the `master` key name
- Configuration changes take effect immediately (hot update), format validation warnings (unknown parameters / bad entries are ignored)

## Link Control: Claiming and Blocking

> [!NOTE]
> The `event.done()` / `event.mark_processed()` `claim=` / `stop=` parameters for this feature require ErisPulse **2.7.1+**.

ErisPulse decouples the two orthogonal semantics of "claiming" and "blocking" and unifies control through `event.done()`, facilitating the addition of logging, auditing, permission, and other observation layers around command processing.

**Accurate definitions of the two concepts**:

- **Claiming (claim)**: Mark the event as processed by this handler (write to `_processed`). The command dispatcher sees the claimed event and **skips it to prevent** duplicate processing of the same message by multiple command handlers. Typical scenario: After a command matches, claim it to prevent the command dispatcher from intervening again.
- **Blocking (stop)**: Prevent the event from propagating to **lower-priority** handlers (write to `_propagation_stopped`). Lower-priority handlers will no longer see the event. Typical scenario: The high-priority handler has fully processed the event and does not want lower-priority handlers to execute.

| `event.done(...)` | Claim | Block | Scenario |
|-------------------|------|------|------|
| `event.done()` | ✔ | ✔ | Standard practice for command / handler completion |
| `event.done(stop=False)` | ✔ | ✘ | Only claim, allowing low-priority observers (logging / statistics) to continue seeing |
| `event.done(claim=False)` | ✘ | ✔ | Only block (e.g., firewall / rate limit), but do not perform command deduplication |

`event.done(claim=, stop=)` is an alias for `event.mark_processed(claim=, stop=)`, with identical parameters and behavior.

```python
@command("help")
async def help_cmd(event):
    event.done()            # Claim + Block (standard practice for command completion)

@message.on_message(priority=50)
async def observer(event):
    event.done(stop=False)  # Only claim: Low-priority still executes (logging / statistics)

@message.on_message(priority=100)
async def firewall(event):
    if denied(event):
        event.done(claim=False)  # Only block: Low-priority does not execute, but no deduplication
```

### Command and Reply Block Configuration

**Command matches claim immediately**: As soon as a message matches a registered command name (including subcommands/aliases), regardless of subsequent scope or permission checks, it will be claimed and default to blocking propagation—commands denied by permission will not leak to lower-priority message handlers (eliminating "double response" when a command is denied and then the `on_message` responds again).

Blocking propagation can be configured to allow lower-priority observers (logging / audit / permission) to still see these messages:

```toml
[ErisPulse.event.command]
block = false   # Command messages continue to flow to lower-priority handlers (claim is unaffected, will not be repeatedly consumed)

[ErisPulse.event.wait_reply]
block = false   # Messages consumed by wait_reply continue to flow to lower-priority handlers
```

> Note: `block` only controls **blocking** (stop), not **claiming** (claim)—matched commands will never be repeatedly consumed by message handlers; messages that do not match any command flow as usual to message handlers.

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
    
    # You can handle the request via the adapter API
    # Refer to each adapter's documentation for specific implementation
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

## Interactive Processing

### Using the reply method to send responses

The `event.reply()` method supports various modifier parameters, making it convenient to send messages with @, reply, and other functions:

```python
# Simple reply
await event.reply("Hello")

# Send different types of messages
await event.reply("http://example.com/image.jpg", method="Image")  # Image
await event.reply("http://example.com/voice.mp3", method="Voice")  # Voice

# @ a single user
await event.reply("Hello", at_users=["user123"])

# @ multiple users
await event.reply("Hello", at_users=["user1", "user2", "user3"])

# Reply to a message
await event.reply("Reply content", reply_to="msg_id")

# @ all members
await event.reply("Announcement", at_all=True)

# Combined usage: @ user + reply to message
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
        await event.reply("Timeout, please enter again.")
```

> [!TIP]
> **Commands are still available during waiting** (2.8.3+): Messages starting with a command prefix and matching a registered command (e.g., `/cancel`) will **execute the command** rather than being treated as reply content, and the waiting continues suspended—users can cancel/switch at any time, and the command execution continues after completion. If you need the old behavior of "waiting consumes all text," configure `ErisPulse.event.wait_reply.cmdpass = true`, or use `wait_reply(cmdpass=True)` for a single instance.

### Waiting reply with validation

```python
@command("age", help="Ask age")
async def age_handler(event):
    def validate_age(event_data):
        """Validate age is valid"""
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
    
    await event.reply("Confirm this operation? (Yes/No)")
    
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
        await event.reply(f"You chose: {colors[choice]}")
    else:
        await event.reply("Timed out, no choice made")
```

**Merge mode**: `merge_prompt=True` combines options into the prompt message and sends them in a single message using the specified `method`:

```python
# Send combined prompt + options in Markdown
choice = await event.choose(
    "## Please select a color\n{options}\nPlease reply with the number",
    ["red", "green", "blue"],
    method="Markdown",
    merge_prompt=True,
)
```

> The `{options}` placeholder controls the insertion position of options; if not specified, it appends to the end of the prompt. You can customize the placeholder with the `placeholder` parameter (e.g., `placeholder="[choices]"`). `options_format="auto"` (default) automatically selects the style based on the method: unordered list for Markdown, ordered list for Html, plain text list for other methods. For text-based methods (Text/Markdown/Html, etc.), options are merged to the end by default; for non-text methods (Image, etc.), they are split into two messages by default.

### Form collection (collect)

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

### Waiting for any event (wait_for)

Wait for an event that meets certain conditions, not limited to the same user:

```python
@command("wait_member", help="Wait for new member")
async def wait_member_handler(event):
    await event.reply("Waiting for a new member to join...")
    
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
    
    await conv.say("Welcome to the questionnaire survey!")
    
    while conv.is_active:
        reply = await conv.wait()
        
        if reply is None:
            await conv.say("Conversation timed out, goodbye!")
            break
        
        text = reply.get_text()
        
        if text == "Exit":
            await conv.say("Goodbye!")
            break
        
        await conv.say(f"You said: {text}, continue entering or reply 'Exit' to end")
```

### Built-in confirmation words

ErisPulse includes built-in sets of confirmation words:

- **Confirmation words** (`CONFIRM_YES_WORDS`): 是、yes、y、确认、确定、好、好的、ok、true、对、嗯、行、同意、没问题...
- **Negation words** (`CONFIRM_NO_WORDS`): 否、no、n、取消、不、不要、不行、cancel、false、错、拒绝、不可以...

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

### Platform-specific Extension Methods

In addition to built-in methods, each platform adapter registers platform-specific methods, making it convenient to access platform-specific data.

```python
from ErisPulse.Core.Event import message

@message.on_message()
async def handle_message(event):
    platform = event.get_platform()

    # Call platform-specific methods based on the platform
    if platform == "telegram":
        chat_type = event.get_chat_type()      # Telegram-specific method
    elif platform == "email":
        subject = event.get_subject()           # Email-specific method
```

If you are unsure whether a platform has registered a particular method, you can query which methods are registered for a platform:

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
    
    # Use module-specific logging
    from ErisPulse import sdk
    logger = sdk.logger.get_child("MyHandler")
    logger.debug(f"Detailed debug information")
```

### 3. Conditional Handling

```python
@message.on_message(priority=0)
async def conditional_handler(event):
    """Conditional handling - judge within the handler"""
    # Only process messages from specific users
    if event.get_user_id() in ["bot1", "bot2"]:
        return
    
    # Only process messages containing specific keywords
    if "keyword" not in event.get_text():
        return
    
    await event.reply("Condition met, processing message")
```

## Next Steps

- [Common Tasks Examples](common-tasks.md) - Learn implementations of common features (including advanced message sending: retry/timeout/batch)
- [Platform Features Guide](../platform-guide/README.md) - Complete explanation of Send DSL chained sending, sending rules, and batch building
- [Event Wrapper Class Detailed Explanation](../developer-guide/modules/event-wrapper.md) - Deep dive into the Event object
- [User Guide](../user-guide/) - Learn about configuration and module management