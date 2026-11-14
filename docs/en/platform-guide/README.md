# ErisPulse Platform Features Documentation

> Base Protocol: [OneBot12](https://12.onebot.dev/)  
> This document is a **platform-specific features guide**, including:  
> - Examples of chainable Send method calls supported by each adapter  
> - Explanations of platform-specific event/message formats  
>  
> For general usage methods, please refer to:  
> - [Basic Concepts](../getting-started/basic-concepts.md)  
> - [Event Conversion Standard](../standards/event-conversion.md)  
> - [API Response Specification](../standards/api-response.md)

---

## Platform-Specific Features

This section is maintained by each adapter developer and is used to explain the differences and extended features of the adapter compared to the OneBot12 standard. Please refer to the detailed documentation for each platform below:

- [Maintain Notes](maintain-notes.md)
- [Yunhu Platform Features](yunhu.md)
- [Yunhu User Platform Features](yunhu_user.md)
- [Oopz Platform Features](oopz.md)
- [Telegram Platform Features](telegram.md)
- [OneBot11 Platform Features](onebot11.md)
- [OneBot12 Platform Features](onebot12.md)
- [SnowLuma Platform Features](snowluma.md)
- [Email Platform Features](email.md)
- [Kook (Open Black) Platform Features](kook.md)
- [Matrix Platform Features](matrix.md)
- [Enterprise WeChat Platform Features](wecom.md)
- [Bilibili Platform Features](bilibili.md)
- [Minecraft Platform Features](minecraft.md)
- [QQ Official Bot Platform Features](qqbot.md)
- [Ideaura Coffee Shop](ideaura.md)
- [Discord](discord.md)
- [Webhook Protocol Bridge](webhook.md)
- [WeChat Official Account](wechatmp.md)

> Additionally, there is a `sandbox` adapter, but this adapter does not require a platform-specific features documentation.

---

## Common Interfaces

### Chainable Send Calls
All adapters support the following standard calling methods:

> **Note:** The placeholder `{AdapterName}` in the documentation must be replaced with the actual adapter name (such as `yunhu`, `telegram`, `onebot11`, `email`, etc.).

1. Specify type and ID: `To(type, id).Func()`
   ```python
   # Get adapter instance
   my_adapter = adapter.get("{AdapterName}")
   
   # Send message
   await my_adapter.Send.To("user", "U1001").Text("Hello")
   
   # For example:
   yunhu = adapter.get("yunhu")
   await yunhu.Send.To("user", "U1001").Text("Hello")
   ```

2. Specify only ID: `To(id).Func()`
   ```python
   my_adapter = adapter.get("{AdapterName}")
   await my_adapter.Send.To("U1001").Text("Hello")
   
   # For example:
   telegram = adapter.get("telegram")
   await telegram.Send.To("U1001").Text("Hello")
   ```

3. Specify sending account: `Using(account_id)`
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

#### Asynchronous Sending and Result Handling

The methods of the Send DSL return an `asyncio.Task` object, which means you can choose whether to wait for the result immediately:

```python
# Get adapter instance
my_adapter = adapter.get("{AdapterName}")

# Send message in the background without waiting for the result
task = my_adapter.Send.To("user", "123").Text("Hello")

# If you need to get the sending result, you can wait later
result = await task
```

#### Send Rule Decorators

In actual development, you often need: execute subsequent logic only after successful sending, automatic retry on failure, timeout cancellation, progress monitoring, etc. The Send DSL includes a set of built-in send rule decorators that can be attached via chainable methods:

| Method | Description |
|--------|-------------|
| `.Hook(callback)` | Callback executed after successful sending (can be called multiple times) |
| `.Retry(times=1)` | Automatically retry N times on failure (including the first attempt, total N+1 times) |
| `.Timeout(seconds)` | Single send timeout, cancel if timeout occurs (can be stacked with Retry) |
| `.Defer(seconds)` | Delay sending (in-process timing, not persisted) |
| `.OnProgress(callback)` | Progress callback at each stage, passing SendContext |
| `.OnError(callback)` | Error callback when final failure occurs (triggers only once) |

```python
yunhu = adapter.get("yunhu")

# Deduct points only after successful sending
await (yunhu.Send.To("user", "123")
       .Hook(lambda r: deduct_points("123"))
       .Text("Consumption successful"))

# Retry on failure + timeout cancellation + progress monitoring
def on_progress(ctx):
    print(f"Stage: {ctx.stage}, Attempt: {ctx.attempt + 1}/{ctx.max_attempts}")

task = (yunhu.Send.To("user", "123")
        .Retry(3)              # Retry up to 3 times
        .Timeout(10)           # Timeout each send at 10 seconds
        .OnProgress(on_progress)
        .OnError(lambda ctx: notify_admin(ctx.error))
        .Text("Important notice"))
```

Rule methods return `self`, so they must be called before the sending methods (e.g., Text/Image). The `SendContext` includes fields such as `stage` (pending/sending/retrying/success/failed/timeout), `attempt`, `elapsed`, `error`, `result`, which are useful for monitoring.

#### Batch Build Mode (Build)

Multiple sending methods can be built within a single chain, and then executed together. This is suitable for scenarios where multiple messages are sent at once:

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

`.send_all()` executes by default **in parallel** (concurrent sending, high efficiency). If the order of message arrival needs to be guaranteed, call `.Sequential()` for sequential execution:

```python
# Sequential execution (guarantee order) + retry on failure
await (yunhu.Send.To("group", "456")
       .Build()
       .Sequential()                # Send in order
       .Retry(2)                     # Retry failed items individually
       .Text("First message").Text("Second message")
       .send_all())
```

Batch execution adopts a **fail-continue** strategy: failure of one item does not interrupt others, and failed items are automatically retried. Batch also supports batch-level `Hook` (triggered after all succeed), `OnError` (triggered when there are failures), and `OnProgress` (progress callback).

> For more detailed rules and batch build instructions, please refer to [SendDSL Detailed Explanation](../developer-guide/adapters/send-dsl.md).

### Event Listening
There are three ways to listen for events:

1. Platform-native event listening:
   ```python
   from ErisPulse.Core import adapter, logger
   
   @adapter.on("event_type", raw=True, platform="{AdapterName}")
   async def handler(data):
       logger.info(f"Received native {AdapterName} event: {data}")
   ```

2. OneBot12 standard event listening:
   ```python
   from ErisPulse.Core import adapter, logger

   # Listen for OneBot12 standard events
   @adapter.on("event_type")
   async def handler(data):
       logger.info(f"Received standard event: {data}")

   # Listen for specific platform standard events
   @adapter.on("event_type", platform="{AdapterName}")
   async def handler(data):
       logger.info(f"Received {AdapterName} standard event: {data}")
   ```

3. Event module listening:  
   The events provided by the `Event` module are based on the `adapter.on()` function, so the event format provided by the `Event` module is a OneBot12 standard event.

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

The most recommended approach is to use the `Event` module for event handling, as the `Event` module provides rich event types and various event handling methods.

---

## Standard Formats
For convenience, basic event formats are provided here. For detailed information, please refer to the links above.

> **Note:** The following formats are based on the OneBot12 standard. Each adapter may have extended fields on top of this standard. Please refer to the specific features documentation of each adapter for details.

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
    {"type": "text", "data": {"text": "你好"}}
  ],
  "alt_message": "你好",
  "user_id": "user_456",
  "user_nickname": "ExampleUser",
  "group_id": "group_789"
}
```

### Standard Response Format
#### Message Sending Success
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

#### Message Sending Failure
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
ErisPulse Project:
- [Main Repository](https://github.com/ErisPulse/ErisPulse/)
- [Yunhu Adapter Repository](https://github.com/ErisPulse/ErisPulse-YunhuAdapter)
- [Telegram Adapter Repository](https://github.com/ErisPulse/ErisPulse-TelegramAdapter)
- [OneBot Adapter Repository](https://github.com/ErisPulse/ErisPulse-OneBotAdapter)

Related Official Documentation:
- [OneBot V11 Protocol Documentation](https://github.com/botuniverse/onebot-11)
- [Telegram Bot API Official Documentation](https://core.telegram.org/bots/api)
- [Yunhu Official Documentation](https://www.yhchat.com/document/1-3)

## Contributing

We welcome more developers to contribute and maintain adapter documentation! Please follow these steps to submit contributions:
1. Fork the [ErisPulse](https://github.com/ErisPulse/ErisPulse) repository.
2. Create a Markdown file in the `docs/platform-features/` directory, naming it in the format `<Platform Name>.md`.
3. Add a link to your contributed adapter and relevant official documentation in this `README.md` file.
4. Submit a Pull Request.

Thank you for your support!