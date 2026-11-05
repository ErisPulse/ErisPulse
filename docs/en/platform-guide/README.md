# ErisPulse PlatformFeatures Documentation

> Baseline protocol: [OneBot12](https://12.onebot.dev/) 
> 
> This document is a **platform-specific features guide**, including:
> - Chained Send method call examples supported by each adapter
> - Descriptions of platform-specific event/message formats
> 
> For general usage, please refer to:
> - [Basic Concepts](../getting-started/basic-concepts.md)
> - [Event Conversion Standard](../standards/event-conversion.md)  
> - [API Response Specification](../standards/api-response.md)

---

## Platform-Specific Features

This section is maintained by each adapter's developer, and is used to explain the adapter's differences from and extensions to the OneBot12 standard. Please refer to the detailed documentation for each platform below:

- [Maintenance Notes](maintain-notes.md)

- [Yunhu Platform Features](yunhu.md)
- [Yunhu User Platform Features](yunhu_user.md)
- [Telegram Platform Features](telegram.md)
- [OneBot11 Platform Features](onebot11.md)
- [OneBot12 Platform Features](onebot12.md)
- [SnowLuma Platform Features](snowluma.md)
- [Email Platform Features](email.md)
- [Kook Platform Features](kook.md)
- [Matrix Platform Features](matrix.md)
- [WeCom (Enterprise WeChat) Platform Features](wecom.md)
- [Bilibili Platform Features](bilibili.md)
- [Minecraft Platform Features](minecraft.md)
- [QQ Official Bot Platform Features](qqbot.md)
- [Kaede Café](ideaura.md)
- [Discord](discord.md)
- [Webhook Protocol Bridge](webhook.md)
- [WeChat Official Account](wechatmp.md)

> There is also a `sandbox` adapter, but this adapter does not require a platform features document to be maintained

---

## Common Interfaces

### Send Chained Calls
All adapters support the following standard calling methods:

> **Note:** `{AdapterName}` in the documentation should be replaced with the actual adapter name (e.g., `yunhu`, `telegram`, `onebot11`, `email`, etc.).

1. Specify type and ID: `To(type,id).Func()`
   ```python
   # Get adapter instance
   my_adapter = adapter.get("{AdapterName}")
   
   # Send message
   await my_adapter.Send.To("user", "U1001").Text("Hello")
   
   # Example:
   yunhu = adapter.get("yunhu")
   await yunhu.Send.To("user", "U1001").Text("Hello")
   ```
2. Specify ID only: `To(id).Func()`
   ```python
   my_adapter = adapter.get("{AdapterName}")
   await my_adapter.Send.To("U1001").Text("Hello")
   
   # Example:
   telegram = adapter.get("telegram")
   await telegram.Send.To("U1001").Text("Hello")
   ```
3. Specify the sending account: `Using(account_id)`
   ```python
   my_adapter = adapter.get("{AdapterName}")
   await my_adapter.Send.Using("bot1").To("U1001").Text("Hello")
   
   # Example:
   onebot11 = adapter.get("onebot11")
   await onebot11.Send.Using("bot1").To("U1001").Text("Hello")
   ```
4. Direct call: `Func()`
   ```python
   my_adapter = adapter.get("{AdapterName}")
   await my_adapter.Send.Text("Broadcast message")
   
   # Example:
   email = adapter.get("email")
   await email.Send.Text("Broadcast message")
   ```

#### Async Send and Result Handling

The Send DSL methods return `asyncio.Task` objects, which means you can choose whether to await the result immediately:

```python
# Get adapter instance
my_adapter = adapter.get("{AdapterName}")

# Without awaiting, the message is sent in the background
task = my_adapter.Send.To("user", "123").Text("Hello")

# If you need the send result, you can await it later
result = await task
```

#### Send Rule Decorators

In real-world development, you often need to: execute follow-up logic only after a successful send, retry automatically on failure, cancel on timeout, monitor send progress, etc. The Send DSL comes with a built-in set of send rule decorators; attach rules via chained methods:

| Method | Description |
|--------|------|
| `.Hook(callback)` | Callback executed after a successful send (can be called multiple times) |
| `.Retry(times=1)` | Automatically retry N times on failure (N+1 attempts in total including the first) |
| `.Timeout(seconds)` | Timeout for a single send; cancels on timeout (can be combined with Retry) |
| `.Defer(seconds)` | Delayed send (in-process scheduling, not persisted) |
| `.OnProgress(callback)` | Progress callback for each stage, receiving a SendContext |
| `.OnError(callback)` | Error callback on final failure (triggered only once) |

```python
yunhu = adapter.get("yunhu")

# Deduct points only after the send succeeds
await (yunhu.Send.To("user", "123")
       .Hook(lambda r: deduct_points("123"))
       .Text("Consumption successful"))

# Retry on failure + timeout cancellation + progress monitoring
def on_progress(ctx):
    print(f"Stage: {ctx.stage}, Attempt: {ctx.attempt + 1}/{ctx.max_attempts}")

task = (yunhu.Send.To("user", "123")
        .Retry(3)              # Retry up to 3 times
        .Timeout(10)           # 10-second timeout per attempt
        .OnProgress(on_progress)
        .OnError(lambda ctx: notify_admin(ctx.error))
        .Text("Important notice"))
```

Rule methods return `self` and must be called before the send method (Text/Image, etc.). `SendContext` contains fields such as `stage` (pending/sending/retrying/success/failed/timeout), `attempt`, `elapsed`, `error`, and `result`, making monitoring easy.

#### Batch Build Mode (Build)

Build multiple send methods in a single chain and execute them all together at the end. Suitable for scenarios where you want to "send multiple messages in one go":

```python
yunhu = adapter.get("yunhu")

# Build multiple messages and send them together
results = await (yunhu.Send.To("user", "123")
                .Build()                     # Enter build mode
                .Text("Notice one")
                .Image("pic.jpg")
                .Text("Notice two")
                .send_all())                 # Execute all together
# results = [Text result, Image result, Text result]
```

`.send_all()` executes **in parallel** by default (concurrent sending, more efficient). When message arrival order must be guaranteed, call `.Sequential()` to execute serially:

```python
# Serial execution (order guaranteed) + retry on failure
await (yunhu.Send.To("group", "456")
       .Build()
       .Sequential()                # Send one by one in order
       .Retry(2)                    # Each failed entry retries independently
       .Text("First message").Text("Second message")
       .send_all())
```

Batch execution adopts a **fail-and-continue** strategy: one failure does not interrupt the other entries, and failed entries are retried automatically. Batch mode also supports batch-level `Hook` (triggered after all succeed), `OnError` (triggered when any entry fails), and `OnProgress` (progress callback).

> For more detailed rules and batch build descriptions, please refer to [SendDSL in Detail](../developer-guide/adapters/send-dsl.md).

### Event Listening
There are three ways to listen for events:

1. Platform-native event listening:
   ```python
   from ErisPulse.Core import adapter, logger
   
   @adapter.on("event_type", raw=True, platform="{AdapterName}")
   async def handler(data):
       logger.info(f"Received {AdapterName} native event: {data}")
   ```

2. OneBot12 standard event listening:
   ```python
   from ErisPulse.Core import adapter, logger

   # Listen for OneBot12 standard events
   @adapter.on("event_type")
   async def handler(data):
       logger.info(f"Received standard event: {data}")

   # Listen for standard events from a specific platform
   @adapter.on("event_type", platform="{AdapterName}")
   async def handler(data):
       logger.info(f"Received {AdapterName} standard event: {data}")
   ```

3. Event module listening:
    The events of `Event` are based on the `adapter.on()` function, so the event format provided by `Event` is a OneBot12 standard event

    ```python
    from ErisPulse.Core.Event import message, notice, request, command

    message.on_message()(message_handler)
    notice.on_notice()(notice_handler)
    request.on_request()(request_handler)
    command("hello", help="Send a greeting message", usage="hello")(command_handler)

    async def message_handler(event):
        logger.info(f"Received message: {event}")
    async def notice_handler(event):
        logger.info(f"Received notice: {event}")
    async def request_handler(event):
        logger.info(f"Received request: {event}")
    async def command_handler(event):
        logger.info(f"Received command: {event}")
    ```

Among these, using the `Event` module for event handling is the most recommended option, because the `Event` module provides rich event types as well as rich event handling methods.

---

## Standard Formats
For convenience of reference, simple event formats are given here. If you need detailed information, please refer to the links above.

> **Note:** The formats below are the basic OneBot12 standard formats; each adapter may have extension fields on top of them. For specifics, please refer to each adapter's platform-specific feature descriptions.

### Standard Event Format
The event conversion format that all adapters must implement:
```json
{
  "id": "event_123",
  "time": 1752241220,
  "type": "message",
  "detail_type": "group",
  "platform": "example_platform",
  "self": {"platform": "example_platform", "user_id": "bot_123"},
  "message_id": "msg_abc",
  "message": [
    {"type": "text", "data": {"text": "Hello"}}
  ],
  "alt_message": "Hello",
  "user_id": "user_456",
  "user_nickname": "ExampleUser",
  "group_id": "group_789"
}
```

### Standard Response Format
#### Message Send Success
```json
{
  "status": "ok",
  "retcode": 0,
  "data": {
    "message_id": "1234",
    "time": 1632847927.599013
  },
  "message_id": "1234",
  "message": "",
  "echo": "1234",
  "{platform}_raw": {...}
}
```

#### Message Send Failure
```json
{
  "status": "failed",
  "retcode": 10003,
  "data": null,
  "message_id": "",
  "message": "Missing required parameter",
  "echo": "1234",
  "{platform}_raw": {...}
}
```

---

## Reference Links
ErisPulse projects:
- [Main Repository](https://github.com/ErisPulse/ErisPulse/)
- [Yunhu Adapter Repository](https://github.com/ErisPulse/ErisPulse-YunhuAdapter)
- [Telegram Adapter Repository](https://github.com/ErisPulse/ErisPulse-TelegramAdapter)
- [OneBot Adapter Repository](https://github.com/ErisPulse/ErisPulse-OneBotAdapter)

Related official documentation:
- [OneBot V11 Protocol Documentation](https://github.com/botuniverse/onebot-11)
- [Telegram Bot API Official Documentation](https://core.telegram.org/bots/api)
- [Yunhu Official Documentation](https://www.yhchat.com/document/1-3)

## Contributing

We welcome more developers to participate in writing and maintaining adapter documentation! Please follow these steps to submit your contributions:
1. Fork the [ErisPuls](https://github.com/ErisPulse/ErisPulse) repository.
2. Create a Markdown file under the `docs/platform-features/` directory, named in the format `<platform-name>.md`.
3. Add a link to your contributed adapter and its related official documentation in this `README.md` file.
4. Submit a Pull Request.

Thank you for your support!