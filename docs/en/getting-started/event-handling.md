# Event Handling Introduction

This guide introduces how to handle various events in ErisPulse.

## Event Type Overview

ErisPulse supports the following event types:

| Event Type | Description | Applicable Scenarios |
|---------|------|---------|
| Message Event | Any message sent by a user | Chatbot, content filtering |
| Command Event | Messages starting with a command prefix | Command handling, function entry |
| Notification Event | System notifications (friend added, group member changes, etc.) | Welcome messages, status notifications |
| Request Event | User requests (friend requests, group invitations) | Automatic request handling |
| Meta Event | System-level events (connection, heartbeat) | Connection monitoring, status checks |

## Handling Message Events

> **Note**: It is recommended to use the `Event` type annotation in event handlers for IDE auto-completion and type checking support.

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
    # Get the list of mentioned users
    mentions = event.get_mentions()
    await event.reply(f"You mentioned these users: {mentions}")
```

### Wildcard and Regex Matching

The four message decorators (`on_message`, `on_private_message`, `on_group_message`, `on_at_message`) support both `pattern` (glob wildcard) and `regex` (regular expression). Messages that do not match these conditions **will not trigger** the handler:

```python
# Glob wildcard: * for any string, ? for single character, [seq] for character set
@message.on_message(pattern="sign in*")
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

`wait_reply` also supports these two parameters (see [Wait Reply Function](../developer-guide/modules/event-wrapper.md#wait-reply-function)).

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

Users can invoke it in any of the following ways:
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

### Command Groups

```python
@command("admin.reload", group="admin", help="Reload module")
async def reload_handler(event):
    await event.reply("Module reloaded")

@command("admin.stop", group="admin", help="Stop bot")
async def stop_handler(event):
    await event.reply("Bot stopped")
```

### Command Permissions and Access Control

Command permissions are divided into three layers, checked from top to bottom (if upper layer denies, lower layers are not checked):

```python
# ① Command ACL (user-side configuration): user whitelist/blacklist for commands, denies with "Permission denied" reply
# ② master=True — only framework owner can execute (framework automatically checks, denies with "Permission denied" reply)
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

**Command User ACL** (`ErisPulse.event.command.acl`): Users can configure user whitelist/blacklist for any command, command names support exact and glob patterns (e.g., `"roll*"`), denies with "Permission denied" reply:

```toml
# config.toml — allow only 123456 to execute restart; 666 is always denied
[ErisPulse.event.command.acl.restart]
allow = ["onebot11:123456"]
deny = ["onebot11:666"]
```

Check order: `deny` hits → deny; `allow` non-empty and not hit → deny; if no ACL configured, follow `event.command.default_allow` (`false` = strict mode, no ACL means deny; `true` means delegate to developer's default `master=True` / `permission`). Runtime API (command name supports glob):

```python
from ErisPulse.Core.Event import command

command.allow_user("restart", "onebot11", "123456")   # Allow list
command.deny_user("restart", "onebot11", "666")       # Deny list
command.remove_acl("restart")                          # Clear whitelist/blacklist
command.get_acl("restart")                             # Query current list
```

> Command handlers are imported from the event package: `from ErisPulse.Core.Event import command`; can also be accessed via SDK event package: `sdk.Event.command` (both are the same singleton). Usually already imported with command decorator in module (`from ErisPulse.Core.Event import command`).

Cross-command / cross-user **event-level** access control (whether to receive messages from someone / a group / a bot) goes through **identity scope** (`scope.identity`); **module-level** availability (which modules can be used) goes through **module scope** (`scope.platforms / bots / sessions`). See [Scope](../advanced/scope.md).

> Suggestion: Use `master=True` / `permission` for business logic linkage within commands; use identity scope for user / group access control; use module scope for module availability control.

### Command Priority

```python
# Higher priority number means earlier execution
@message.on_message(priority=10)
async def high_priority_handler(event):
    await event.reply("High priority handler")

@message.on_message(priority=1)
async def low_priority_handler(event):
    await event.reply("Low priority handler")
```

### Parallel Event Handling

ErisPulse's event system adopts a **parallel within same priority, serial across different priorities** scheduling model:

```
Event arrives
    ↓
priority=10 group: [handler C || handler D] parallel → merge results
    ↓ (if not interrupted)
priority=0 group: [handler A || handler B] parallel → merge results
    ↓
...
```

- **Parallel within same priority**: Multiple handlers with the same priority execute simultaneously, improving throughput
- **Serial across priorities**: Groups with different priorities execute in order (higher priority number executes first), ensuring high priority handlers run first
- **Copy-On-Write**: No copy is created if no modifications are made, ensuring zero overhead
- **Conflict handling**: When multiple handlers modify the same field within the same priority, the last modification is used, and a warning log is recorded
- **Interruption mechanism**: After any handler calls `event.done()` (default) or `event.done(claim=False)`, subsequent lower priority groups are skipped. The difference between claiming and blocking is discussed in the following section [Link Control: Claiming and Blocking](#link-control-claiming-and-blocking)

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

# Serial execution across different priorities
@message.on_message(priority=10)
async def handler_c(event):
    # Highest priority, executes first
    pass
```

> **Concurrency limit**: All matching handlers' tasks are **immediately created**, but a semaphore limits the **maximum number of concurrent executions**, defaulting to **64** (`ErisPulse.framework.handler_max_concurrency`, supports hot updates). Tasks exceeding the limit queue on the semaphore, waiting for previous tasks to complete before entering. This acts as your "pressure relief valve" during event spikes.
>
> **Slow logs**: If a single handler takes longer than **1 second**, the framework logs a WARNING (`handler_slow`). The waiting time in `wait_reply` is excluded from the duration, preventing misreporting due to "waiting for reply."

## Scope Filtering: Why My Module Didn't Receive Messages

After an event arrives, there are two **silent** filters (neither reply nor error):

1. **Identity scope** (`ErisPulse.scope.identity`): When an event enters the distribution entry, it is judged as to whether to receive it based on user > group > bot > adapter. Events rejected are **entirely discarded**, and no handler (including the command dispatcher) will trigger.
2. **Module scope** (`ErisPulse.scope`): When an event arrives at a module's handler/command, it is judged based on session > bot > platform as to whether the module is available, and **skips silently** if not passed.

```toml
# Example 1: All messages from a group are not propagated
[ErisPulse.scope.identity.sessions.onebot11."group_123"]
deny = true

# Example 2: Block MyModule from a specific bot
[ErisPulse.scope.bots.onebot11."123456"]
blocked = ["MyModule"]
```

In this case, when a message from this group arrives, the `MyModule`'s command and event handlers **will not be scheduled**. This is not a bug, but a filtering mechanism—when troubleshooting "module not responding," prioritize checking the identity and module binding in the scope.

- Filter logs are only visible at **TRACE** level (`core.scope.identity_denied` / `core.scope.denied`), and are not visible at default INFO level
- Framework-level handlers (such as the command dispatcher `scope_exempt=True`) are not affected by the **module scope**, but are affected by the **identity scope** (the entire event has been discarded)
- Before command execution, there is a third filter: command user ACL (denies with "Permission denied" reply, see previous section)
- The fourth filter is **event overwriting** (see next section)

> For scope configuration, matching syntax, and runtime API, see [Scope](../../advanced/scope.md).

## Event Overwriting: Overwrite Any Event Behavior Without Modifying Module Code

> [!NOTE]
> This feature requires ErisPulse **2.8.0+**.

Event handlers register parameters (such as `pattern`, `regex`, `master`, `hidden`, etc.) as **default values** for developers. The unified overwriting system allows users to overwrite any module's behavior by **event type**—OneBot12 standard types (meta / message / notice / request) and ErisPulse extended types (command) each have their own set of overwritable parameters:

| Event Type | Overwritable Parameters | Purpose |
|---------|-----------|------|
| `message` | `pattern` / `regex` / `detail_types` | Text trigger conditions + message subtype whitelist |
| `notice` | `detail_types` / `pattern` / `regex` | Notice subtype whitelist + text conditions |
| `request` | `detail_types` / `pattern` / `regex` | Request subtype whitelist + text conditions |
| `meta` | `detail_types` | Meta-event subtype whitelist (connect / heartbeat, etc.) |
| `command` | `master` / `hidden` / `aliases` / `prefix` / `help` / `usage` | Command implementation parameters (user priority) |
| `acl` (command-specific) | `allow` / `deny` | Command user whitelist/blacklist (by command name glob) |

```toml
# message: Overwrite text trigger conditions (AND with code conditions)
[ErisPulse.event.overrides.message.ChatModule]
pattern = "闲聊*"

# notice: Only respond to specific notice subtypes
[ErisPulse.event.overrides.notice.MyModule]
detail_types = ["group_increase"]

# command: Overwrite implementation parameters (user priority—can tighten or loosen developer defaults)
[ErisPulse.event.overrides.command.MyModule.restart]
master = true
hidden = true

# acl: Command user whitelist/blacklist (glob across commands)
[ErisPulse.event.overrides.acl."roll*"]
allow = ["onebot11:u_vip"]

# ACL fallback (false = strict mode: no ACL means deny)
acl_default_allow = true
```

Runtime API (`from ErisPulse.Core.Event import overrides` or `sdk.Event.overrides`, **type sub-namespace**—symmetrical `set` / `get` / `delete` trio for each type):

```python
from ErisPulse.Core.Event import overrides

overrides.message.set("ChatModule", pattern="闲聊*")   # message text condition
overrides.notice.set("MyModule", detail_types=["group_increase"])
overrides.command.set("MyModule", "restart", master=True)  # command parameter
overrides.acl.set("roll*", deny=["onebot11:u_bad"])    # command user blacklist

overrides.message.get("ChatModule")     # {"pattern": "闲聊*"}
overrides.message.delete("ChatModule")  # Restore developer defaults
```

- Overwrite conditions and handler code conditions **both take effect** (AND semantics); `command` parameters and developer declarations **deep merge** (overwrite takes precedence)
- `detail_types`: Events without `detail_type` are allowed (do not mistakenly kill unknown events)
- `pattern` / `regex`: Events without text (connect / heartbeat, etc.) are not constrained and are allowed directly
- `command` overwrite key `master` synchronously maps to storage key `must_master`; disabling commands uniformly uses `acl` deny
- Configuration changes take effect immediately (hot update), format validation warnings (unknown parameters / bad entries are ignored)

## Link Control: Claiming and Blocking

> [!NOTE]
> The `event.done()` / `event.mark_processed()` `claim=` / `stop=` parameters require ErisPulse **2.7.1+**.

ErisPulse decouples the two orthogonal semantics of "claiming" and "blocking" through `event.done()`, making it easier to overlay observation layers (logging, auditing, permissions) around command processing.

**Precise definitions of the two concepts:**

- **Claiming (claim)**: Marks the event as processed by this handler (writes to `_processed`). The command dispatcher skips already claimed events to **avoid duplicate processing** of the same message by multiple command handlers. Typical scenario: Claim after a command matches, preventing the command dispatcher from intervening again.
- **Blocking (stop)**: Prevents the event from propagating to **lower priority** handlers (writes to `_propagation_stopped`). Lower priority handlers (such as `on_message`) will no longer see the event. Typical scenario: High priority handlers have fully processed the event, and lower priority handlers should not execute again.

| `event.done(...)` | Claim | Block | Scenario |
|-------------------|------|------|------|
| `event.done()` | ✔ | ✔ | Standard practice for command / handler completion |
| `event.done(stop=False)` | ✔ | ✘ | Claim only: lower priority observers (logging / statistics) still see it |
| `event.done(claim=False)` | ✘ | ✔ | Block only (e.g., firewall / rate limiting), but no command deduplication |

`event.done(claim=, stop=)` is an alias for `event.mark_processed(claim=, stop=)`, with identical parameters and behavior.

```python
@command("help")
async def help_cmd(event):
    event.done()            # Claim + Block (standard practice for command completion)

@message.on_message(priority=50)
async def observer(event):
    event.done(stop=False)  # Claim only: lower priority still executes (logging / statistics)

@message.on_message(priority=100)
async def firewall(event):
    if denied(event):
        event.done(claim=False)  # Block only: lower priority does not execute, but no deduplication
```

### Command and Reply Block Configuration

After a command matches or `wait_reply` matches a reply, blocking propagation is enabled by default (backward compatibility). Configuration can be used to allow lower priority handlers (logging / auditing / permissions) to observe these messages:

```toml
[ErisPulse.event.command]
block = false   # Command messages continue to flow to lower priority handlers

[ErisPulse.event.wait_reply]
block = false   # Replies consumed by wait_reply continue to flow to lower priority handlers
```

## Handling Notification Events

### Friend Added

```python
from ErisPulse.Core.Event import notice

@notice.on_friend_add()
async def friend_add_handler(event):
    user_id = event.get_user_id()
    nickname = event.get_user_nickname() or "New friend"
    await event.reply(f"Welcome to add me as a friend, {nickname}!")
```

### Group Member Added

```python
@notice.on_group_increase()
async def member_increase_handler(event):
    group_id = event.get_group_id()
    user_id = event.get_user_id()
    await event.reply(f"Welcome new member {user_id} to group {group_id}")
```

### Group Member Removed

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
    
    # Handle the request via adapter API
    # Specific implementation refer to adapter documentation
```

### Group Invitation Request

```python
@request.on_group_request()
async def group_request_handler(event):
    group_id = event.get_group_id()
    user_id = event.get_user_id()
    
    await event.reply(f"Received invite to group {group_id} from {user_id}")
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

After the adapter sends a meta event, the framework automatically tracks the Bot status, and you can query it anytime:

```python
from ErisPulse import sdk

# Check if a Bot is online
if sdk.adapter.is_bot_online("telegram", "123456"):
    telegram = sdk.adapter.get("telegram")
    await telegram.Send.To("user", "123456").Text("Bot is online")

# List all online Bots
bots = sdk.adapter.list_bots()
for platform, bot_list in bots.items():
    for bot_id, info in bot_list.items():
        print(f"{platform}/{bot_id}: {info['status']}")

# Get complete status summary
summary = sdk.adapter.get_status_summary()
```

## Interactive Handling

### Using reply method to send replies

The `event.reply()` method supports various modifier parameters, making it convenient to send messages with @, reply, etc.:

```python
# Simple reply
await event.reply("Hello")

# Send messages of different types
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

# Combine: @ user + reply to message
await event.reply("Content", at_users=["user1"], reply_to="msg_id")
```

### Waiting for User Reply

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
        await event.reply("Timeout, please try again.")
```

### Wait Reply with Validation

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

### Wait Reply with Callback

```python
@command("confirm", help="Confirm operation")
async def confirm_handler(event):
    async def handle_confirmation(reply_event):
        text = reply_event.get_text().lower()
        
        if text in ["yes", "是", "y", "确认"]:
            await event.reply("Operation confirmed!")
        else:
            await event.reply("Operation canceled.")
    
    await event.reply("Confirm this operation? (Yes/No)")
    
    await event.wait_reply(
        timeout=30,
        callback=handle_confirmation
    )
```

### Confirmation Dialogue (confirm)

Wait for user confirmation or denial, automatically recognize built-in Chinese and English confirmation words:

```python
@command("confirm", help="Confirm operation")
async def confirm_handler(event):
    if await event.confirm("Are you sure to execute this operation?"):
        await event.reply("Confirmed, executing...")
    else:
        await event.reply("Cancelled")

# Custom confirmation words
if await event.confirm("Continue?", yes_words={"go", "继续"}, no_words={"stop", "停止"}):
    pass
```

### Choice Menu (choose)

User can reply with option number or option text:

```python
@command("choose", help="Choose")
async def choose_handler(event):
    choice = await event.choose(
        "Please select a color:",
        ["Red", "Green", "Blue"]
    )
    
    if choice is not None:
        colors = ["Red", "Green", "Blue"]
        await event.reply(f"You selected: {colors[choice]}")
    else:
        await event.reply("Timed out, no choice made")
```

**Merge mode**: `merge_prompt=True` will merge options into the prompt message, sending them in a single message using the specified `method`:

```python
# Send merged prompt + options using Markdown
choice = await event.choose(
    "## Please select a color\n{options}\nPlease reply with the number",
    ["Red", "Green", "Blue"],
    method="Markdown",
    merge_prompt=True,
)
```

> The `{options}` placeholder controls where options are inserted; if not written, they are appended to the end of the prompt. You can customize the placeholder using the `placeholder` parameter (e.g., `placeholder="[choices]"`). `options_format="auto"` (default) automatically selects the style based on the method: unordered list for Markdown, ordered list for Html, plain text list for others. Text-based methods (Text/Markdown/Html, etc.) default to merging options at the end; non-text methods (Image, etc.) default to splitting into two messages.

### Form Collection (collect)

Collect user input in multiple steps:

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

### Wait for Any Event (wait_for)

Wait for any event that meets the condition, not limited to the same user:

```python
@command("wait_member", help="Wait for new member")
async def wait_member_handler(event):
    await event.reply("Waiting for new group member...")
    
    evt = await event.wait_for(
        event_type="notice",
        condition=lambda e: e.get_detail_type() == "group_member_increase",
        timeout=120
    )
    
    if evt:
        await event.reply(f"Welcome new member: {evt.get_user_id()}")
    else:
        await event.reply("Timeout waiting")
```

### Multi-turn Dialogue (conversation)

Create an interactive multi-turn dialogue context:

```python
@command("survey", help="Survey")
async def survey_handler(event):
    conv = event.conversation(timeout=60)
    
    await conv.say("Welcome to the survey!")
    
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

### Built-in Confirmation Words

ErisPulse includes built-in sets of Chinese and English confirmation words:

- **Confirmation words** (`CONFIRM_YES_WORDS`): 是, yes, y, confirm, sure, ok, right, agree, fine,没问题, ...
- **Denial words** (`CONFIRM_NO_WORDS`): 否, no, n, cancel, don't, not, no way, false, wrong, refuse, 不可以, ...

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
    
    # Message type checking
    is_private = event.is_private_message()
    is_group = event.is_group_message()
    is_at = event.is_at_message()
    
    # Command information
    if event.is_command():
        cmd_name = event.get_command_name()
        cmd_args = event.get_command_args()
        cmd_raw = event.get_command_raw()
```

### Platform-specific Methods

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

If unsure whether a platform has registered a particular method, you can query which methods a platform has registered:

```python
from ErisPulse.Core.Event import get_platform_event_methods

methods = get_platform_event_methods("telegram")
# ["get_chat_type", "is_bot_message", ...]
```

> Platform-specific registered methods can be found in the respective [platform documentation](../platform-guide/).

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
    
    # Use module-specific logger
    from ErisPulse import sdk
    logger = sdk.logger.get_child("MyHandler")
    logger.debug(f"Debug information")
```

### 3. Conditional Handling

```python
@message.on_message(priority=0)
async def conditional_handler(event):
    """Conditional handling - check conditions within the handler"""
    # Only handle messages from specific users
    if event.get_user_id() in ["bot1", "bot2"]:
        return
    
    # Only handle messages containing specific keywords
    if "keyword" not in event.get_text():
        return
    
    await event.reply("Condition met, processing message")
```

## Next Steps

- [Common Tasks Examples](common-tasks.md) - Learn the implementation of common features (including advanced message sending: retry/timeout/batch)
- [Platform Features Guide](../platform-guide/README.md) - Complete explanation of Send DSL chaining, sending rules, and batch construction
- [Event Wrapper Class Details](../developer-guide/modules/event-wrapper.md) - Deep dive into Event objects
- [User Guide](../user-guide/) - Learn about configuration and module management