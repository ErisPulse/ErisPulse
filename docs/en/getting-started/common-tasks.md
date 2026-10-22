# Common Task Examples

> [!TIP]
> **When to read this**: When you want to add a specific feature to your bot, refer to each section—persistence, scheduled tasks, message filtering, permission control, batch sending. Each section is a complete example you can copy directly. If you want to learn event handling patterns systematically, start with [Introduction to Event Handling](event-handling.md); otherwise, skip it.

## Content List

1. Data Persistence  
2. Scheduled Tasks  
3. Message Filtering  
4. Multi-Platform Adaptation  
5. Advanced Message Sending (Retry/Timeout/Batch)  
6. Permission Control  
7. Message Statistics  
8. Search Functionality  
9. Image Processing

## Data Persistence

### Simple Counter

```python
from ErisPulse import sdk
from ErisPulse.Core.Event import command

@command("count", help="View command invocation count")
async def count_handler(event):
    # Get the count
    count = sdk.storage.get("command_count", 0)
    
    # Increment the count
    count += 1
    sdk.storage.set("command_count", count)
    
    await event.reply(f"This is the {count}th invocation of this command")
```

### User Data Storage

```python
@command("profile", help="View profile")
async def profile_handler(event):
    user_id = event.get_user_id()
    
    # Get user data
    user_data = sdk.storage.get(f"user:{user_id}", {
        "nickname": "",
        "join_date": None,
        "message_count": 0
    })
    
    profile_text = f"""
Nickname: {user_data['nickname']}
Join Date: {user_data['join_date']}
Message Count: {user_data['message_count']}
    """
    
    await event.reply(profile_text.strip())

@command("setnick", help="Set nickname")
async def setnick_handler(event):
    user_id = event.get_user_id()
    args = event.get_command_args()
    
    if not args:
        await event.reply("Please enter a nickname")
        return
    
    # Update user data
    user_data = sdk.storage.get(f"user:{user_id}", {})
    user_data["nickname"] = " ".join(args)
    sdk.storage.set(f"user:{user_id}", user_data)
    
    await event.reply(f"Nickname has been set to: {' '.join(args)}")
```

## Scheduled Tasks

### Simple Timer

```python
from ErisPulse import sdk
from ErisPulse.Core.Event import command
import asyncio

class TimerModule:
    def __init__(self):
        self.sdk = sdk
        self._tasks = []
    
    async def on_load(self, event):
        """Start scheduled tasks when the module is loaded"""
        self._start_timers()
        
        @command("timer", help="Timer management")
        async def timer_handler(event):
            await event.reply("The timer is running...")
    
    def _start_timers(self):
        """Start scheduled tasks"""
        # Execute every 60 seconds
        task = asyncio.create_task(self._every_minute())
        self._tasks.append(task)
        
        # Execute daily at midnight
        task = asyncio.create_task(self._daily_task())
        self._tasks.append(task)
    
    async def _every_minute(self):
        """Task executed every minute"""
        self.sdk.logger.info("Executing every minute task")
        # Your logic...
    
    async def _daily_task(self):
        """Task executed daily at midnight (Note: based on UTC time calculation, adjust for local time if needed)"""
        import time
        
        while True:
            # Calculate time until midnight
            now = time.time()
            midnight = now + (86400 - now % 86400)
            
            await asyncio.sleep(midnight - now)
            
            # Execute task
            self.sdk.logger.info("Executing daily task")
            # Your logic...
```

### Using Lifecycle Events

```python
@sdk.lifecycle.on("core.init.complete")
async def init_complete_handler(event_data):
    """Start scheduled tasks after SDK initialization completes"""
    import asyncio
    
    async def daily_reminder():
        """Daily reminder"""
        await asyncio.sleep(86400)  # 24 hours
        sdk.logger.info("Executing daily task")
    
    # Start background task
    asyncio.create_task(daily_reminder())
```

## Message Filtering

### Keyword Filtering

```python
from ErisPulse.Core.Event import message

blocked_words = ["垃圾", "广告", "钓鱼"]

@message.on_message()
async def filter_handler(event):
    text = event.get_text()
    
    # Check if the message contains any blocked words
    for word in blocked_words:
        if word in text:
            sdk.logger.warning(f"Blocked sensitive message: {word}")
            return  # Do not process this message
    
    # Process the message normally
    await event.reply(f"Received: {text}")
```

### Blacklist Filtering

```python
# Load blacklist from configuration or storage
blacklist = sdk.storage.get("user_blacklist", [])

@message.on_message()
async def blacklist_handler(event):
    user_id = event.get_user_id()
    
    if user_id in blacklist:
        sdk.logger.info(f"User on blacklist: {user_id}")
        return  # Do not process
    
    # Process normally
    await event.reply(f"Hello, {user_id}")
```

## Multi-Platform Adaptation

### Platform-Specific Responses

```python
@command("help", help="Show help")
async def help_handler(event):
    platform = event.get_platform()
    
    if platform == "yunhu":
        await event.reply("Yunhu platform help...")
    elif platform == "telegram":
        await event.reply("Telegram platform help...")
    elif platform == "onebot11":
        await event.reply("OneBot11 help...")
    else:
        await event.reply("General help information")
```

### Platform Feature Detection

```python
@command("rich", help="Send rich text message")
async def rich_handler(event):
    platform = event.get_platform()
    
    if platform == "yunhu":
        # Yunhu supports HTML
        yunhu = sdk.adapter.get("yunhu")
        await yunhu.Send.To("user", event.get_user_id()).Html(
            "<b>Bold text</b><i>Italic text</i>"
        )
    elif platform == "telegram":
        # Telegram supports Markdown
        telegram = sdk.adapter.get("telegram")
        await telegram.Send.To("user", event.get_user_id()).Markdown(
            "**Bold text** *Italic text*"
        )
    else:
        # Other platforms use plain text
        await event.reply("Bold text Italic text")
```

## Advanced Message Sending (Retry/Timeout/Batch)

In addition to the simple `event.reply()`, you can use the adapter's Send DSL to implement more complex sending scenarios: automatic retry on failure, timeout cancellation, executing logic after success, and batch sending of multiple messages.

> The following examples use `event.get_detail_type()` and `event.get_target_id()` to retrieve the target type and ID from the event (automatically getting `group_id` for group chats and `user_id` for private chats), avoiding hardcoding.

### Execute Logic After Successful Sending

```python
@command("pay", help="Simulate payment")
async def pay_handler(event):
    yunhu = sdk.adapter.get(event.get_platform())
    user_id = event.get_user_id()
    # Deduct points only after successful sending
    await (yunhu.Send.To(event.get_detail_type(), event.get_target_id())
           .Hook(lambda r: sdk.storage.set(f"points:{user_id}", -10))
           .Text("Payment successful, 10 points deducted"))
```

### Retry on Failure + Timeout Cancellation

```python
@command("notice", help="Send important notification")
async def notice_handler(event):
    adapter_inst = sdk.adapter.get(event.get_platform())
    # Retry up to 3 times, with each attempt timed out after 10 seconds
    task = (adapter_inst.Send.To(event.get_detail_type(), event.get_target_id())
            .Retry(3)
            .Timeout(10)
            .OnError(lambda ctx: sdk.logger.error(f"Notification sending failed: {ctx.error}"))
            .Text("This is an important notification"))
    # Send in the background without waiting
```

### Batch Send Multiple Messages

Send multiple messages in a single chain, with unified execution:

```python
@command("announce", help="Send announcement")
async def announce_handler(event):
    adapter_inst = sdk.adapter.get(event.get_platform())
    # Build multiple messages and send them together (default is parallel)
    results = await (adapter_inst.Send.To(event.get_detail_type(), event.get_target_id())
                    .Build()
                    .Text("📋 Today's announcement")
                    .Image("https://example.com/banner.jpg")
                    .Text("See the image above for details")
                    .Retry(2)            # Each failed item retries individually
                    .send_all())
    sdk.logger.info(f"Batch sending completed, {len(results)} messages in total")
```

> For a more complete explanation of rules and batch operations, see the [Platform Features Guide](../platform-guide/README.md#sending-rules-decorators).

## Permission Control

### Administrator Check

```python
# Configure the list of owners
MASTERS = ["user123", "user456"]

def is_master(user_id):
    """Check if the user is the framework owner"""
    return user_id in MASTERS

@command("master", help="Framework owner command")
async def master_handler(event):
    user_id = event.get_user_id()
    
    if not is_master(user_id):
        await event.reply("Insufficient permissions, this command is only available to the framework owner")
        return
    
    await event.reply("Framework owner command executed successfully")

@command("addmaster", help="Add framework owner")
async def addmaster_handler(event):
    if not is_master(event.get_user_id()):
        return
    
    args = event.get("text", "").split()
    if len(args) < 2:
        await event.reply("Usage: /addmaster <user ID>")
        return
    
    new_master = args[0]
    MASTERS.append(new_master)
    await event.reply(f"Framework owner added: {new_master}")
```

### Group Permissions

```python
@command("groupinfo", help="View group information")
async def groupinfo_handler(event):
    if not event.is_group_message():
        await event.reply("This command is only available in group chats")
        return
    
    group_id = event.get_group_id()
    user_id = event.get_user_id()
    
    await event.reply(f"Group ID: {group_id}, Your ID: {user_id}")
```

## Message Statistics

### Message Counting

> **Note**: The following example uses `sdk.storage.get/set` for simple counting. In high-concurrency scenarios, it is recommended to use `sdk.storage.transaction()` to ensure atomicity.

```python
@message.on_message()
async def count_handler(event):
    # Get statistics
    stats = sdk.storage.get("message_stats", {
        "total": 0,
        "by_user": {},
        "by_day": {}
    })
    
    # Update statistics
    stats["total"] += 1
    
    user_id = event.get_user_id()
    stats["by_user"][user_id] = stats["by_user"].get(user_id, 0) + 1
    
    # Save
    sdk.storage.set("message_stats", stats)

@command("stats", help="View message statistics")
async def stats_handler(event):
    stats = sdk.storage.get("message_stats", {
        "total": 0,
        "by_user": {},
        "by_day": {}
    })
    
    top_users = sorted(
        stats["by_user"].items(),
        key=lambda x: x[1],
        reverse=True
    )[:5]
    
    top_text = "\n".join(
        f"{uid}: {count} messages" for uid, count in top_users
    )
    
    await event.reply(f"Total messages: {stats['total']}\n\nActive users:\n{top_text}")
```

## Search Functionality

### Simple Search

> **Note**: The following example uses an in-memory list to store message history; **data will be lost after program restart**. For production environments, it is recommended to use `sdk.storage` or SQLite tables for persistent storage.

```python
from ErisPulse.Core.Event import command, message

# Store message history
message_history = []

@message.on_message()
async def store_handler(event):
    """Store messages for searching"""
    user_id = event.get_user_id()
    text = event.get_text()
    
    message_history.append({
        "user_id": user_id,
        "text": text,
        "time": event.get_time()
    })
    
    # Limit the number of history records
    if len(message_history) > 1000:
        message_history.pop(0)

@command("search", help="Search messages")
async def search_handler(event):
    args = event.get_command_args()
    
    if not args:
        await event.reply("Please enter a search keyword")
        return
    
    keyword = " ".join(args)
    results = []
    
    # Search through history
    for msg in message_history:
        if keyword in msg["text"]:
            results.append(msg)
    
    if not results:
        await event.reply("No matching messages found")
        return
    
    # Display results
    result_text = f"Found {len(results)} matching messages:\n\n"
    for i, msg in enumerate(results[:10], 1):  # Show at most 10 results
        result_text += f"{i}. {msg['text']}\n"
    
    await event.reply(result_text)
```

## Image Processing

### Image Download and Storage

```python
from ErisPulse.Core import client

@message.on_message()
async def image_handler(event):
    """Handle image messages"""
    message_segments = event.get_message()
    
    for segment in message_segments:
        if segment.get("type") == "image":
            file_url = segment.get("data", {}).get("file")
            
            if file_url:
                # Recommended to use the SDK built-in client to download images
                resp = await client.get(file_url)
                if resp.status == 200:
                    image_data = await resp.read()
                    
                    # Save to file
                    filename = f"images/{event.get_time()}.jpg"
                    with open(filename, "wb") as f:
                        f.write(image_data)
                    
                    sdk.logger.info(f"Image saved: {filename}")
                    await event.reply("Image saved")
```

### Image Recognition Example

> **Note**: The following example uses a placeholder API address. Please replace it with your own image recognition service when using it.

```python
from ErisPulse.Core import client

@command("identify", help="Identify image")
async def identify_handler(event):
    """Identify images in the message"""
    message_segments = event.get_message()
    
    for segment in message_segments:
        if segment.get("type") == "image":
            file_url = segment.get("data", {}).get("file")
            
            # Call the image recognition API
            result = await _identify_image(file_url)
            
            await event.reply(f"Recognition result: {result}")
            return
    
    await event.reply("No image found")

async def _identify_image(url):
    """Call the image recognition API (example) - Use the SDK built-in client"""
    resp = await client.post(
        "https://api.example.com/identify",
        json={"url": url}
    )
    data = await resp.json()
    return data.get("description", "Recognition failed")
```

## What's Next

- **Function is ready, want to run it long-term**: See [Deployment Guide](../user-guide/deployment.md), Docker / systemd daemon and backup & upgrade
- **Want to distribute your own function to others**: Start from [Module Development Introduction](../developer-guide/modules/getting-started.md), upgrade your script to an installable module
- **Need to adjust configuration or troubleshoot "module not responding"**: Check [Configuration File Description](../user-guide/configuration.md) and [Scope](../advanced/scope.md)