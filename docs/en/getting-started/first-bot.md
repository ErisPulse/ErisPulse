# Create Your First Bot

This guide will take you from scratch to create a simple ErisPulse bot.

## Step 1: Create Project

Use the CLI tool to initialize the project:

```bash
# Interactive initialization
epsdk init

# Or quick initialization
epsdk init -q -n my_first_bot
```

Follow the prompts to complete the configuration. It is recommended to select:
- Project name: my_first_bot
- Log level: INFO
- Server: Default configuration
- Adapter: Choose your needed platform (e.g., Yunhu)

## Step 2: View Project Structure

The project structure after initialization:

```text
my_first_bot/
├── config/
│   └── config.toml
├── main.py
└── requirements.txt
```

## Step 3: Write Your First Command

Open `main.py` and write a simple command handler:

```python
from ErisPulse import sdk
from ErisPulse.Core.Event import command

@command("hello", help="Send a greeting message")
async def hello_handler(event):
    """Handle hello command"""
    user_name = event.get_user_nickname() or "Friend"
    await event.reply(f"Hello, {user_name}! I am the ErisPulse bot.")

@command("ping", help="Test if the bot is online")
async def ping_handler(event):
    """Handle ping command"""
    await event.reply("Pong! The bot is running normally.")

async def main():
    """Main entry function"""
    print("Initializing ErisPulse...")
    # Run SDK and keep it running
    await sdk.run(keep_running=True)
    print("ErisPulse initialization complete!")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

> In addition to using `sdk.run()` directly, you can also control the execution flow more granularly, such as:
```python
import asyncio
from ErisPulse import sdk

async def main():
    try:
        isInit = await sdk.init()
        
        if not isInit:
            sdk.logger.error("ErisPulse initialization failed, please check logs")
            return
        
        await sdk.adapter.startup()
        
        # Keep the program running; if you have other operations to execute, you can also not keep the event loop running, but you need to handle it yourself
        await asyncio.Event().wait()
    except Exception as e:
        sdk.logger.error(e)
    finally:
        await sdk.uninit()

if __name__ == "__main__":
    asyncio.run(main())
```

## Step 4: Run the Bot

```bash
# Run normally
epsdk run main.py

# Development mode (supports hot reload)
epsdk run main.py --reload
```

## Step 5: Test the Bot

Send the command in your chat platform:

```text
/hello
```

You should receive a response from the bot.

## Code Explanation

### Command Decorator

```python
@command("hello", help="Send a greeting message")
```

- `hello`: Command name, users call it via `/hello`
- `help`: Command help description, shown in the `/help` command

### Event Arguments

```python
async def hello_handler(event):
```

The `event` parameter is an Event object, containing:
- Message content
- Sender information
- Platform information
- etc...

### Sending a Reply

```python
await event.reply("Reply content")
```

`event.reply()` is a convenient method for sending a message to the sender.

## Extension: Adding More Features

### Add Message Listening

```python
from ErisPulse.Core.Event import message

@message.on_message()
async def message_handler(event):
    """Listen to all messages"""
    text = event.get_text()
    if "你好" in text:
        await event.reply("你好！")
```

### Add Notification Listening

```python
from ErisPulse.Core.Event import notice

@notice.on_friend_add()
async def friend_add_handler(event):
    """Listen to friend addition events"""
    user_id = event.get_user_id()
    await event.reply(f"欢迎添加我为好友！你的 ID 是 {user_id}")
```

### Use Storage System

```python
# Get counter
count = sdk.storage.get("hello_count", 0)

# Increment counter
count += 1
sdk.storage.set("hello_count", count)

await event.reply(f"这是第 {count} 次调用 hello 命令")
```

## Common Issues

### Bot does not respond?

1. Check if the adapter is configured correctly
2. View log output to confirm if there are errors
3. Confirm if the command prefix is correct (default is `/`)

### How to change the command prefix?

Add this to `config.toml`:

```toml
[ErisPulse.event.command]
prefix = "!"
case_sensitive = false
```

### How to support multiple platforms?

The code will automatically adapt to all loaded platform adapters. Just ensure your logic is compatible:

```python
@command("hello")
async def hello_handler(event):
    platform = event.get_platform()
    
    if platform == "yunhu":
        await event.reply("你好！来自云湖")
    elif platform == "telegram":
        await event.reply("Hello! From Telegram")
```

## Next Steps

- [Basic Concepts](basic-concepts.md) - Understand ErisPulse core concepts deeply
- [Event Handling Introduction](event-handling.md) - Learn how to handle various events
- [Common Task Examples](common-tasks.md) - Master more practical functions