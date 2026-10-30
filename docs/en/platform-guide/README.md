# ErisPulse PlatformFeatures Documentation

> Baseline protocol: [OneBot12](https://12.onebot.dev/) 
> 
> This document is a **platform-specific features guide**, including:
> - Chained `Send` method call examples supported by each adapter
> - Platform-specific event/message format descriptions
> 
> For general usage, please refer to:
> - [Basic Concepts](../getting-started/basic-concepts.md)
> - [Event Conversion Standards](../standards/event-conversion.md)  
> - [API Response Specifications](../standards/api-response.md)

---

## Platform-Specific Features

This section is maintained by each adapter developer to explain the differences and extended features of that adapter compared to the OneBot12 standard. Please refer to the detailed documentation for each platform below:

- [Maintenance Notes](maintain-notes.md)

- [Yunhu Platform Features](yunhu.md)
- [Yunhu User Platform Features](yunhu_user.md)
- [Telegram Platform Features](telegram.md)
- [OneBot11 Platform Features](onebot11.md)
- [OneBot12 Platform Features](onebot12.md)
- [SnowLuma Platform Features](snowluma.md)
- [Email Platform Features](email.md)
- [Kook (KaiHeiLa) Platform Features](kook.md)
- [Matrix Platform Features](matrix.md)
- [WeCom (Enterprise WeChat) Platform Features](wecom.md)
- [QQ Official Bot Platform Features](qqbot.md)
- [Ideaura (Huafeng Cafe)](ideaura.md)
- [Discord](discord.md)
- [Webhook Protocol Bridge](webhook.md)
- [WeChat Official Account](wechatmp.md)

> In addition, there is a `sandbox` adapter, but this adapter does not require a platform features document to be maintained.

---

## Common Interfaces

### Chained Send Calls
All adapters support the following standard calling patterns:

> **Note:** The `{AdapterName}` in this document must be replaced with the actual adapter name (e.g., `yunhu`, `telegram`, `onebot11`, `email`, etc.).

1. Specify type and ID: `To(type,id).Func()`
   ```python
   # Get the adapter instance
   my_adapter = adapter.get("{AdapterName}")
   
   # Send a message
   await my_adapter.Send.To("user", "U1001").Text("Hello")
   
   # For example:
   yunhu = adapter.get("yunhu")
   await yunhu.Send.To("user", "U1001").Text("Hello")
   ```
2. Specify ID only: `To(id).Func()`
   ```python
   my_adapter = adapter.get("{AdapterName}")
   await my_adapter.Send.To("U1001").Text("Hello")
   
   # For example:
   telegram = adapter.get("telegram")
   await telegram.Send.To("U1001").Text("Hello")
   ```
3. Specify the sending account: `Using(account_id)`
   ```python
   my_adapter = adapter.get("{AdapterName}")
   await my_adapter.Send.Using("bot1").To("U1001").Text("Hello")
   
   # For example:
   onebot11 = adapter.get("onebot11")
   await onebot11.Send.Using("bot1").To("U1001").Text("Hello")
   ```
4. Direct call: `Func()`
   ```python
   my_adapter = adapter.get("{AdapterName}")
   await my_adapter.Send.Text("Broadcast message")
   
   # For example:
   email = adapter.get("email")
   await email.Send.Text("Broadcast message")
   ```

#### Async Sending and Result Handling

The Send DSL methods return `asyncio.Task` objects, which means you can choose whether to await the result immediately:

```python
# Get the adapter instance
my_adapter = adapter.get("{AdapterName}")

# Do not await the result; the message is sent in the background
task = my_adapter.Send.To("user", "123").Text("Hello")

# If you need the send result, you can await it later
result = await task
```

#### Send Rule Decorators

In real-world development, it is often necessary to: execute follow-up logic only after a successful send, automatically retry on failure, cancel on timeout, monitor sending progress, etc. The Send DSL comes with a built-in set of send rule decorators, attached via chained methods:

| Method | Description |
|--------|------|
| `.Hook(callback)` | Callback executed after a successful send (can be called multiple times) |
| `.Retry(times=1)` | Automatically retry N times on failure (N+1 attempts in total including the first) |
| `.Timeout(seconds)` | Timeout for a single send; cancels on timeout (can be combined with Retry) |
| `.Defer(seconds)` | Delayed send (in-process timer, not persisted) |
| `.OnProgress(callback)` | Progress callback for each stage, receiving a SendContext |
| `.OnError(callback)` | Error callback on final failure (triggered only once) |

```python
yunhu = adapter.get("yunhu")

# Deduct points only after the message is sent successfully
await (yunhu.Send.To("user", "123")
       .Hook(lambda r: deduct_points("123"))
       .Text("Purchase successful"))

# Retry on failure + timeout cancellation + progress monitoring
def on_progress(ctx):
    print(f"Stage: {ctx.stage}, Attempt: {ctx.attempt + 1}/{ctx.max_attempts}")

task = (yunhu.Send.To("user", "123")
        .Retry(3)              # Retry up to 3 times
        .Timeout(10)           # 10-second timeout for each attempt
        .OnProgress(on_progress)
        .OnError(lambda ctx: notify_admin(ctx.error))
        .Text("Important notice"))
```

Rule methods return `self` and must be called before the send method (Text/Image, etc.). `SendContext` contains fields such as `stage` (pending/sending/retrying/success/failed/timeout), `attempt`, `elapsed`, `error`, and `result` for easy monitoring.

#### Batch Build Mode (Build)

Build multiple send methods in a single chain and execute them all at once at the end. Suitable for scenarios where you want to "send multiple messages in one go":

```python
yunhu = adapter.get("yunhu")

# Build multiple messages and send them together
results = await (yunhu.Send.To("user", "123")
                .Build()                     # Enter build mode
                .Text("Notice 1")
                .Image("pic.jpg")
                .Text("Notice 2")
                .send_all())                 # Execute all at once
# results = [Text result, Image result, Text result]
```

`.send_all()` executes **in parallel** by default (concurrent sending, highly efficient). To guarantee message arrival order, call `.Sequential()` for sequential execution:

```python
# Sequential execution (guaranteed order) + retry on failure
await (yunhu.Send.To("group", "456")
       .Build()
       .Sequential()                # Send one by one in order
       .Retry(2)                     # Each failed item is retried individually
       .Text("First message").Text("Second message")
       .send_all())
```

Batch execution adopts a **continue-on-failure** strategy: the failure of one item does not interrupt the others, and failed items are retried automatically. Batch execution also supports batch-level `Hook` (triggered after all succeed), `OnError` (triggered when any fails), and `OnProgress` (progress callback).

> For more detailed rules and batch build instructions, please refer to [SendDSL In Detail](../developer-guide/adapters/send-dsl.md).

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

   # Listen for standard events of a specific platform
   @adapter.on("event_type", platform="{AdapterName}")
   async def handler(data):
       logger.info(f"Received {AdapterName} standard event: {data}")
   ```

3. Event module listening:
    Events in `Event` are based on the `adapter.on()` function, so the event format provided by `Event` is a OneBot12 standard event.

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

Among these, using the `Event` module for event handling is the most recommended, because the `Event` module provides a rich set of event types as well as rich event handling methods.

---

## Standard Formats
For convenient reference, simple event formats are provided here. If you need detailed information, please refer to the links above.

> **Note:** The following formats are the basic OneBot12 standard formats, and each adapter may have extended fields on top of them. For details, please refer to each adapter's specific feature descriptions.

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
#### Message Sent Successfully
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

#### Message Send Failed
```json
{
  "status": "failed",
  "retcode": 10003,
  "data": null,
  "message_id": "",
  "message": "Missing required parameters",
  "echo": "1234",
  "{platform}_raw": {...}
}
```

---

## References
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

We welcome more developers to participate in writing and maintaining adapter documentation! Please follow these steps to submit your contribution:
1. Fork the [ErisPuls](https://github.com/ErisPulse/ErisPulse) repository.
2. Create a Markdown file in the `docs/platform-features/` directory, named in the format `<platform-name>.md`.
3. Add a link to the adapter you contributed, along with the related official documentation, in this `README.md` file.
4. Submit a Pull Request.

Thank you for your support!