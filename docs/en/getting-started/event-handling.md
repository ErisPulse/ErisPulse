# Getting Started with Event Handling

This guide introduces how to handle various events in ErisPulse.

Please return the complete Markdown content directly without any other text.

## Event Type Overview

ErisPulse supports the following event types:

| Event Type | Description | Use Cases |
|---------|------|---------|
| Message Event | Any message sent by a user | Chatbots, Content Filtering |
| Command Event | Messages starting with a command prefix | Command Handling, Feature Entry Points |
| Notice Event | System notifications (friend addition, group member changes, etc.) | Welcome Messages, Status Notifications |
| Request Event | User requests (friend requests, group invitations) | Automatic Request Handling |
| Meta Event | System-level events (connection, heartbeat) | Connection Monitoring, Status Checks |

## Message Event Handling

> **Tip**: It is recommended to use the `Event` type annotation in event handlers to receive IDE auto-completion and type checking support.

```python
from ErisPulse.Core.Event import Event  # Import the event type for annotation
```

### Listen to all messages

```python
from ErisPulse.Core.Event import message, Event

@message.on_message()
async def message_handler(event: Event):
    text = event.get_text()
    user_id = event.get_user_id()
    sdk.logger.info(f"Received message from {user_id}: {text}")
```

### Listen to private messages

```python
@message.on_private_message()
async def private_handler(event: Event):
    user_id = event.get_user_id()
    await event.reply(f"Hello, {user_id}! This is a private message.")
```

### Listen to group messages

```python
@message.on_group_message()
async def group_handler(event: Event):
    group_id = event.get_group_id()
    user_id = event.get_user_id()
    sdk.logger.info(f"User {user_id} sent a message in group {group_id}")
```

### Listen to @mentions

```python
@message.on_at_message()
async def at_handler(event: Event):
    # Get the list of users mentioned
    mentions = event.get_mentions()
    await event.reply(f"You mentioned these users: {mentions}")

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

### Command Parameters

```python
@command("echo", help="Echo message")
async def echo_handler(event):
    # Get command arguments
    args = event.get_command_args()
    
    if not args:
        await event.reply("Please enter the message to echo")
    else:
        await event.reply(f"You said: {' '.join(args)}")
```

### Command Groups

```python
@command("admin.reload", group="admin", help="Reload module")
async def reload_handler(event):
    await event.reply("Module has been reloaded")

@command("admin.stop", group="admin", help="Stop bot")
async def stop_handler(event):
    await event.reply("Bot has been stopped")
```

### Command Permissions

```python
def is_master(event):
    """Check if user is framework master"""
    master_list = ["user123", "user456"]
    return event.get_user_id() in master_list

@command("master", permission=is_master, help="Master command")
async def master_handler(event):
    await event.reply("This is a master command")
```

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

### Parallel Event Processing

ErisPulse event system uses a **parallel within same priority, serial between different priorities** scheduling model:

```
Event arrives
    ↓
priority=10 group: [handler C || handler D] parallel → merge results
    ↓ (if not interrupted)
priority=0 group: [handler A || handler B] parallel → merge results
    ↓
...
```

- **Parallel within same priority**: Multiple handlers with the same priority execute simultaneously, increasing throughput
- **Serial between priorities**: Groups with different priorities execute in order (higher priority numbers execute first), ensuring high-priority handlers run first
- **Copy-On-Write**: No copy is created if handlers do not modify data, ensuring zero overhead
- **Conflict handling**: When multiple handlers at the same priority modify the same field, the last modification is used and a warning log is recorded
- **Interrupt mechanism**: After any handler calls `event.done()` (default) or `event.done(claim=False)`, subsequent lower priority groups are skipped. The difference between claiming and blocking is explained in the following section [**Link Control: Claiming and Blocking**](#link-control-claiming-and-blocking)

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

# Serial execution of handlers with different priorities
@message.on_message(priority=10)
async def handler_c(event):
    # Highest priority, executes first
    pass
```

> **Concurrency limit**: All matching handlers' Tasks are **immediately created**, but a semaphore limits the **number of concurrent executions** by default to **64** (`ErisPulse.framework.handler_max_concurrency`, supports hot update). Tasks exceeding the limit queue on the semaphore and enter only after previous ones complete. This acts as your "pressure relief valve" during event surges.
>
> **Slow logs**: If a single handler takes more than **1 second**, the framework logs a WARNING (`handler_slow`). The `wait_reply` waiting time is excluded from the timing, so delays caused by "waiting for replies" won't trigger a false slow log.

## Scope Filtering: Why Didn't My Module Receive Messages

Event distribution performs scope filtering **before creating the handler Task**—determining `scope.is_allowed` based on the module owner (session level > Bot level > platform level). If it fails, the event is silently skipped without error or response.

```python
# Assuming config.toml blocks MyModule in a specific group:
[ErisPulse.scope]
block = { yunhu = { group_123 = ["MyModule"] } }
```

When messages arrive in this group, neither commands nor event handlers of `MyModule` will be scheduled. This is not a bug, but the scope mechanism—when troubleshooting "module not responding," check scope binding first.

- Three filtering points: adapter bus level (before Task creation), Event module level (within each priority group), command level (before permission check)
- Filtering logs are only visible at **TRACE** level (`core.scope.denied`); default INFO level shows no trace
- Framework-level handlers (e.g., command dispatcher with `scope_exempt=True`) are not affected by scope

> For details on three-level scope binding, whitelist/blacklist, priority overrides, and the implicit "default_allow" rejection semantics, see [Scope System](../../advanced/scope.md).

## Link Control: Claim and Stop

> [!NOTE]
> The `claim=` / `stop=` parameters of `event.done()` / `event.mark_processed()` require ErisPulse **2.7.1+**.

ErisPulse decouples the orthogonal semantics of "Claim" and "Stop", unified through `event.done()`, making it easy to overlay log, audit, permission, and other observation layers around command processing.

**Precise definitions of the two concepts:**

- **Claim (认领)**: Marks the event as handled by this processor (writes to `_processed`). The command dispatcher will **skip claiming events**—avoiding multiple command processors processing the same message. Typical scenario: Claim after successful command matching, preventing the command dispatcher from intervening again.
- **Stop (阻断)**: Prevents the event from propagating to **lower priority** processors (writes to `_propagation_stopped`). Lower priority processors (e.g., `on_message`) will no longer see the event. Typical scenario: High priority processors have fully processed the event, and no lower priority execution is desired.

| `event.done(...)` | Claim | Stop | Scenario |
|-------------------|-------|------|----------|
| `event.done()` | ✔ | ✔ | Standard practice for commands / processors |
| `event.done(stop=False)` | ✔ | ✘ | Only claim, allowing low priority observers (logs / stats) to continue seeing the event |
| `event.done(claim=False)` | ✘ | ✔ | Only stop (e.g., firewall / rate limiting), but do not deduplicate commands |

`event.done(claim=, stop=)` is an alias for `event.mark_processed(claim=, stop=)`, with completely equivalent parameters and behavior.

```python
@command("help")
async def help_cmd(event):
    event.done()            # Claim + Stop (standard practice for command processing)

@message.on_message(priority=50)
async def observer(event):
    event.done(stop=False)  # Only claim: low priority processors still execute (logs / stats)

@message.on_message(priority=100)
async def firewall(event):
    if denied(event):
        event.done(claim=False)  # Only stop: low priority processors do not execute, but no deduplication
```

### Block Configuration for Commands and Replies

After successful command matching / matching a reply via `wait_reply`, propagation is blocked by default (backwards compatible). You can allow the flow by configuring it so that lower priority processors (logs / audit / permission) can also observe these messages:

```toml
[ErisPulse.event.command]
block = false   # Command messages continue to flow to low priority processors

[ErisPulse.event.wait_reply]
block = false   # Replies consumed by wait_reply continue to flow to low priority processors

## Notification Event Handling

### Friend Add

```python
from ErisPulse.Core.Event import notice

@notice.on_friend_add()
async def friend_add_handler(event):
    user_id = event.get_user_id()
    nickname = event.get_user_nickname() or "New Friend"
    await event.reply(f"Welcome to add me as a friend, {nickname}!")
```

### Group Member Increase

```python
@notice.on_group_increase()
async def member_increase_handler(event):
    group_id = event.get_group_id()
    user_id = event.get_user_id()
    await event.reply(f"Welcome new member {user_id} to join group {group_id}")
```

### Group Member Decrease

```python
@notice.on_group_decrease()
async def member_decrease_handler(event):
    group_id = event.get_group_id()
    user_id = event.get_user_id()
    await event.reply(f"Member {user_id} has left group {group_id}")

## Request Event Handling

### Friend Request

```python
from ErisPulse.Core.Event import request

@request.on_friend_request()
async def friend_request_handler(event):
    user_id = event.get_user_id()
    comment = event.get_comment()
    
    sdk.logger.info(f"Received friend request: {user_id}, comment: {comment}")
    
    # Requests can be handled via adapter API
    # Please refer to the documentation of each adapter for specific implementations
```

### Group Invitation Request

```python
@request.on_group_request()
async def group_request_handler(event):
    group_id = event.get_group_id()
    user_id = event.get_user_id()
    
    await event.reply(f"Received group {group_id} invitation from {user_id}")

## Meta Events Handling

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
    sdk.logger.debug(f"{platform} heartbeat check")
```

### Bot Status Query

After the adapter sends a meta event, the framework automatically tracks the Bot's status. You can query it at any time:

```python
from ErisPulse import sdk

# Check if a specific Bot is online
if sdk.adapter.is_bot_online("telegram", "123456"):
    telegram = sdk.adapter.get("telegram")
    await telegram.Send.To("user", "123456").Text("Bot is online")

# List all currently online Bots
bots = sdk.adapter.list_bots()
for platform, bot_list in bots.items():
    for bot_id, info in bot_list.items():
        print(f"{platform}/{bot_id}: {info['status']}")

# Get a full status summary
summary = sdk.adapter.get_status_summary()

## Interactive Processing

### Sending Replies Using the `reply` Method

The `event.reply()` method supports various modifiers to facilitate sending messages with @, reply, and other features:

```python
# Simple reply
await event.reply("Hello")

# Sending different types of messages
await event.reply("http://example.com/image.jpg", method="Image")  # Image
await event.reply("http://example.com/voice.mp3", method="Voice")  # Voice

# @ single user
await event.reply("Hello", at_users=["user123"])

# @ multiple users
await event.reply("Hello everyone", at_users=["user1", "user2", "user3"])

# Reply to a message
await event.reply("Reply content", reply_to="msg_id")

# @ all members
await event.reply("Notice", at_all=True)

# Combination: @ user + reply to message
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

### Waiting for Reply with Validation

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

### Waiting for Reply with Callback

```python
@command("confirm", help="Confirm operation")
async def confirm_handler(event):
    async def handle_confirmation(reply_event):
        text = reply_event.get_text().lower()
        
        if text in ["是", "yes", "y"]:
            await event.reply("Operation confirmed!")
        else:
            await event.reply("Operation cancelled.")
    
    await event.reply("Confirm to execute this operation? (Yes/No)")
    
    await event.wait_reply(
        timeout=30,
        callback=handle_confirmation
    )
```

### Confirming Dialogue (confirm)

Waits for user confirmation or negation, automatically recognizing built-in Chinese and English confirmation words:

```python
@command("confirm", help="Confirm operation")
async def confirm_handler(event):
    if await event.confirm("Are you sure you want to execute this operation?"):
        await event.reply("Confirmed, executing...")
    else:
        await event.reply("Cancelled")

# Custom confirmation words
if await event.confirm("Continue?", yes_words={"go", "继续"}, no_words={"stop", "停止"}):
    pass
```

### Choice Menu (choose)

Users can reply with the option number or option text:

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
        await event.reply("Timeout: No choice made")
```

**Merged Mode**: When `merge_prompt=True`, options are merged into the prompt message and sent in a single message using the user-specified `method`:

```python
# Send merged prompt + options using Markdown
choice = await event.choose(
    "## Please select a color\n{options}\nPlease reply with the number",
    ["Red", "Green", "Blue"],
    method="Markdown",
    merge_prompt=True,
)
```

> The `{options}` placeholder controls the insertion position of options; if omitted, they are appended to the end of the prompt.
> The `placeholder` parameter can be used to customize the placeholder (e.g., `placeholder="[choices]"`).
> `options_format="auto"` (default) selects the style automatically based on method: Markdown → unordered list, Html → ordered list, others → plain text list.
> For text-based methods (Text/Markdown/Html, etc.), options are merged by default; for non-text methods (Image, etc.), they are split into two messages by default.

### Collecting Forms (collect)

Collects user input in multiple steps:

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

### Waiting for Any Event (wait_for)

Waits for any event meeting the conditions, not limited to the same user:

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
        await event.reply("Timeout waiting")
```

### Multi-turn Dialogue (conversation)

Creates an interactive multi-turn dialogue context:

```python
@command("survey", help="Survey")
async def survey_handler(event):
    conv = event.conversation(timeout=60)
    
    await conv.say("Welcome to the survey!")
    
    while conv.is_active:
        reply = await conv.wait()
        
        if reply is None:
            await conv.say("Conversation timeout, goodbye!")
            break
        
        text = reply.get_text()
        
        if text == "退出":
            await conv.say("Goodbye!")
            break
        
        await conv.say(f"You said: {text}, continue typing or reply '退出' to end")
```

### Built-in Confirmation Words

ErisPulse includes built-in sets of Chinese and English confirmation words:

- **Confirmation Words** (`CONFIRM_YES_WORDS`): 是, yes, y, 确认, 确定, 好, 好的, ok, true, 对, 嗯, 行, 同意, 没问题...
- **Negation Words** (`CONFIRM_NO_WORDS`): 否, no, n, 取消, 不, 不要, 不行, cancel, false, 错, 拒绝, 不可以...

## Event Data Access

### Common Methods of the Event Object

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
    
    # Message type judgment
    is_private = event.is_private_message()
    is_group = event.is_group_message()
    is_at = event.is_at_message()
    
    # Command info
    if event.is_command():
        cmd_name = event.get_command_name()
        cmd_args = event.get_command_args()
        cmd_raw = event.get_command_raw()
```

### Platform Extension Methods

In addition to built-in methods, platform adapters also register platform-specific methods to facilitate access to platform-specific data.

```python
from ErisPulse.Core.Event import message

@message.on_message()
async def handle_message(event):
    platform = event.get_platform()

    # Call specific methods according to the platform
    if platform == "telegram":
        chat_type = event.get_chat_type()      # Telegram specific method
    elif platform == "email":
        subject = event.get_subject()           # Email specific method
```

If you are unsure whether a platform has registered a specific method, you can query which methods a platform has registered:

```python
from ErisPulse.Core.Event import get_platform_event_methods

methods = get_platform_event_methods("telegram")
# ["get_chat_type", "is_bot_message", ...]
```

> For the platform-specific methods registered on each platform, please refer to the corresponding [Platform Documentation](../platform-guide/).

## Best Practices for Event Handling

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
    logger.debug(f"Detailed debug info")
```

### 3. Conditional Handling

```python
@message.on_message(priority=0)
async def conditional_handler(event):
    """Conditional handling - Logic inside the handler"""
    # Only process messages from specific users
    if event.get_user_id() in ["bot1", "bot2"]:
        return
    
    # Only process messages containing specific keywords
    if "keyword" not in event.get_text():
        return
    
    await event.reply("Conditions met, processing message")

## Next Steps

- [Common Task Examples](common-tasks.md) - Learn the implementation of common features (including advanced message sending: retry/timeout/batch)
- [Platform Features Guide](../platform-guide/README.md) - Complete description of Send DSL chaining, sending rules, and batch building
- [Event Wrapper Class Details](../developer-guide/modules/event-wrapper.md) - Deep dive into the Event object
- [User Guide](../user-guide/) - Learn about configuration and module management

Please return the translated complete Markdown content directly, without any other text.