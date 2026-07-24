# Creating Your First Bot

This guide will walk you through creating a simple ErisPulse bot from scratch.

## Step 1: Create the Project

Initialize the project using the CLI tool:

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
- Adapter: Choose the platform you need (e.g., Yunhu)

## Step 2: View Project Structure

The structure of the initialized project:

```
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
    """Main entry point"""
    print("Starting ErisPulse...")
    
    # keep_running=True (default): The framework blocks and maintains execution until a close signal is received (e.g., Ctrl+C)
    await sdk.run(keep_running=True)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

### The `keep_running` Parameter

`sdk.run(keep_running)` controls whether the framework blocks to maintain execution:

- **`keep_running=True` (default)**: `run()` will block indefinitely until a close signal is received (e.g., Ctrl+C), suitable for pure bot applications.
- **`keep_running=False`**: `run()` returns immediately after initialization; **the framework does not unload**—started adapters/modules continue to process message events as background tasks. You can continue executing your own logic until the event loop ends and the framework closes. For example:

```python
async def main():
    await sdk.run(keep_running=False)   # Returns immediately after initialization
    # The framework is running in the background, here you can continue doing other things
    while True:
        await asyncio.sleep(3600)
        print("Check every hour")
```

> In addition to the two modes of `run()`, there are manual control methods for the lifecycle, starting and stopping adapters/routes individually, etc. See [Startup Process and Manual Control](../advanced/startup.md).

## Step 4: Run the Bot

```bash
# Normal run
epsdk run main.py

# Development mode (supports hot reload)
epsdk run main.py --reload
```

## Step 5: Test the Bot

Send the command in your chat platform:

```
/hello
```

You should receive a response from the bot.

## Code Explanation

### Command Decorator

```python
@command("hello", help="Send a greeting message")
```

- `hello`: Command name, called by users via `/hello`
- `help`: Command help text, displayed in the `/help` command

### Event Arguments

```python
async def hello_handler(event):
```

The `event` parameter is an Event object, containing:
- Message content: `event.get_text()`
- Sender information: `event.get_user_id()`, `event.get_user_nickname()`
- Platform information: `event.get_platform()`
- Group information: `event.get_group_id()`
- Raw data: `event.get_raw()`

> For a complete list of Event object methods, please refer to [Event Wrapper Class Details](../developer-guide/modules/event-wrapper.md).

### Sending a Reply

```python
await event.reply("Response content")
```

`event.reply()` is a convenient method for sending messages to the sender.

## Extension: Adding More Features

ErisPulse provides rich event handling and data processing capabilities:

- **Message Listening**: Use `@message.on_message()` to listen for various messages → [Event Handling Basics](event-handling.md)
- **Notification Listening**: Use `@notice.on_friend_add()` to listen for system notifications → [Event Handling Basics](event-handling.md)
- **Data Storage**: Use `sdk.storage.get/set` to persist data → [Common Task Examples](common-tasks.md)

## Common Issues

### The command is not responding?

1. Check if the adapter is configured correctly, confirm that the `status` of the adapter in `config/config.toml` is `true`
2. Check the terminal log output to see if there are error messages (especially `ERROR` level logs)
3. Confirm that the command prefix is correct (default is `/`), which can be viewed in the `[ErisPulse.event.command]` section of the configuration file
4. Confirm that the command name is spelled correctly, pay attention to case sensitivity settings

### How to change the command prefix?

Add the following in `config.toml`:

```toml
[ErisPulse.event.command]
prefix = "!"
case_sensitive = false
```

### How to support multiple platforms?

ErisPulse uses the OneBot12 standard to unify the event formats of different platforms. Handlers registered with `@command` and `@message` will automatically receive events from all platforms. You can distinguish the source platform using `event.get_platform()`:

```python
@command("hello")
async def hello_handler(event):
    platform = event.get_platform()
    
    if platform == "yunhu":
        await event.reply("Hello! From Yunhu")
    elif platform == "telegram":
        await event.reply("Hello! From Telegram")
    else:
        await event.reply("Hello!")
```

> For more multi-platform adaptation tips, please refer to [Common Task Examples](common-tasks.md#multi-platform-adaptation).

## Next Steps

- [Basic Concepts](basic-concepts.md) - Understand the core concepts of ErisPulse in depth
- [Event Handling Basics](event-handling.md) - Learn how to handle various events
- [Common Task Examples](common-tasks.md) - Master more practical features