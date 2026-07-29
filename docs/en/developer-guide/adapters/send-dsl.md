# SendDSL Explained

SendDSL is the chained call style message sending interface provided by the ErisPulse adapter.

## Basic Usage

### 1. Specify Type and ID

```python
await adapter.Send.To("group", "123").Text("Hello")
```

### 2. Specify ID Only

```python
await adapter.Send.To("123").Text("Hello")
```

### 3. Specify Sending Account

```python
await adapter.Send.Using("bot1").Text("Hello")
```

### 4. Combination Usage

```python
await adapter.Send.Using("bot1").To("group", "123").Text("Hello")
```

## Method Chain

```
Using/Account() → To() → [Modifier Methods] → [Sending Methods]
```

## Sending Methods

All sending methods return `asyncio.Task` objects.

### Basic Methods (Built-in in Base Class)

The following standard methods are built-in to the `SendDSL` base class and **default to delegating to `Raw_ob12`**. Adapter subclasses do not need to implement them repeatedly and can use them directly, and IDE autocompletion works:

| Method Name | Description | Return Value |
|--------|------|---------|
| `Text(text: str)` | Send text message | `asyncio.Task` |
| `Image(file: bytes \| str)` | Send image | `asyncio.Task` |
| `Voice(file: bytes \| str)` | Send voice (OneBot12 `audio` segment) | `asyncio.Task` |
| `Video(file: bytes \| str)` | Send video | `asyncio.Task` |
| `File(file: bytes \| str, filename: str = None)` | Send file | `asyncio.Task` |

Adapters can override individual standard methods to provide platform-specific logic:

```python
class Send(SendDSL):
    def Raw_ob12(self, message, **kwargs):
        # Must be implemented
        ...

    # Optional: Override Text to provide platform-specific logic
    # def Text(self, text: str):
    #     return self.Raw_ob12([{"type": "text", "data": {"text": text}}])
```

### Protocol Methods

| Method Name | Description | Return Value | Required |
|--------|------|---------|---------|
| `Raw_ob12(message)` | Send OneBot12 format message | `asyncio.Task` | **Must be implemented** |

> **Important**: `Raw_ob12` is the core method of the adapter and **must be implemented**. It is the unified entry point for reverse conversion (OneBot12 → Platform). When not implemented, the base class logs an error and returns a standard error response (`status: "failed"`, `retcode: 10002`). Standard methods (`Text`, `Image`, etc.) default to delegating to `Raw_ob12`.

### Platform Specific Methods

Adapters can add platform-specific sending methods in `Send` subclasses (recognized by `event.supports()` / `event.available_methods()`):

```python
class Send(SendDSL):
    def Raw_ob12(self, message, **kwargs): ...

    # Platform-specific method
    def Sticker(self, sticker_id: str):
        return self.Raw_ob12([{"type": "sticker", "data": {"id": sticker_id}}])
```

## Modifier Methods

Modifier methods return `self` to support chaining.

### At Methods

```python
# @ single user
await adapter.Send.To("group", "123").At("456").Text("你好")

# @ multiple users
await adapter.Send.To("group", "123").At("456").At("789").Text("你们好")
```

### AtAll Method

```python
# @ all members
await adapter.Send.To("group", "123").AtAll().Text("大家好")
```

### Reply Method

```python
# reply to message
await adapter.Send.To("group", "123").Reply("msg_id").Text("回复内容")
```

### Combined Modifiers

```python
await adapter.Send.To("group", "123").At("456").Reply("msg_id").Text("回复@的消息")
```

### Platform Specific Modifier Methods

Besides the built-in `At`/`AtAll`/`Reply`, adapters can define **platform-specific modifier methods**. These methods only need to return `self`—no decorators required—the framework will automatically recognize them:

- Return `self` (SendDSL instance) → Modifier method, does not trigger send wrapper/lifecycle events, chain continues
- Return `Task`/`Awaitable` → Sending method

```python
class Send(SendDSL):
    def Raw_ob12(self, message, **kwargs): ...

    # Modifier method: returns self, does not send
    def Expire(self, seconds: int):
        self._expire = seconds
        return self

    def ForMember(self, user_id: str):
        self._member = user_id
        return self

    # Sending method: returns Task, depends on state set by modifier methods
    def Board(self, content: str, **kwargs):
        return self.Raw_ob12([{"type": "board", "data": {"text": content}}])
```

Usage:

```python
# Modifier methods can be chained together
await adapter.Send.To("group", "big").Expire(3600).ForMember("114").Board("看板内容")
```

## Using Modifier Methods in Event Wrapper Class

`event.reply()` only exposes built-in modifier parameters like `at_sender`/`at_users`/`at_all`/`quote` by default. To use platform-specific modifier methods, there are two ways:

### Method 1: reply() via parameter

Suitable for a small number of known modifier methods:

```python
await event.reply("看板内容", method="Board",
                  via=[("Expire", 3600), ("ForMember", "114514")])
```

`via` is a list, each element can be:

| Form | Equivalent chained call |
|------|-------------|
| `"Name"` | `.Name()` |
| `("Name", arg1, arg2)` | `.Name(arg1, arg2)` |
| `("Name", (arg1,), {kw: val})` | `.Name(arg1, kw=val)` |

### Method 2: event.send_chain()

Suitable for **multiple modifier methods in sequence** or **action-type methods without content parameters** (such as revoke, delete). `send_chain()` returns a configured sending chain with `To`/`Using` set, allowing arbitrary modifier and sending methods to be appended:

```python
# Platform-specific modifier methods + board sending
await event.send_chain().Expire(3600).Board("一小时后过期")

# Multiple modifier methods in sequence
await (event.send_chain()
       .Expire(3600)
       .ForMember("114514")
       .Board("看板内容", content_type="markdown"))

# Built-in modifier methods also work
await event.send_chain().At("123").Reply("msg_id").Text("hi")

# Action-type methods without content parameters
await event.send_chain().DismissBoard()
```

> `send_chain()` returns a complete SendDSL instance, so **all chaining features are available**—not just modifier methods, but also sending rules and bulk building:

```python
# Sending rules: retry + timeout + success callback
await (event.send_chain()
       .Retry(3).Timeout(10)
       .Hook(lambda r: print("发送成功"))
       .Text("可靠发送"))

# Deferred sending + platform modifiers + board
await event.send_chain().Defer(5).Expire(3600).Board("延迟看板")

# Bulk build mode
results = await (event.send_chain()
                 .Build()
                 .Text("第一句").Image("pic.jpg").Text("第二句")
                 .send_all())
```

## Account Management

### Using Method

`Using()` is used to specify the account for sending messages. The passed identifier will be matched with the following priority via `_resolve_account()`:

1. **Account Name** — Key name in configuration (e.g., `"default"`, `"bot1"`)
2. **Runtime injected bot_id** — Identifier automatically injected during event conversion
3. **Any str field** — Other string fields in configuration
4. **Fallback** — First enabled account

```python
# Use account name
await adapter.Send.Using("account1").To("user", "123").Text("Hello")

# Use bot_id (i.e., self.user_id in event)
await adapter.Send.Using("bot_123").To("user", "123").Text("Hello")
```

### Account Method

`Account` method is equivalent to `Using`:

```python
await adapter.Send.Account("account1").To("user", "123").Text("Hello")
```

## Asynchronous Handling

### Don't Wait for Result

```python
# Message sent in background
task = adapter.Send.To("user", "123").Text("Hello")

# Continue executing other operations
# ...
```

### Wait for Result

```python
# Direct await to get result
result = await adapter.Send.To("user", "123").Text("Hello")
print(f"发送结果: {result}")

# Save Task first, wait later
task = adapter.Send.To("user", "123").Text("Hello")
# ... other operations ...
result = await task
```

## Sending Rules System

SendDSL builds a set of sending rule decorators. Rules are attached via chained methods and applied uniformly at final sending time. Rules cover common production scenarios: timeout control, failure retry, success callback, deferred sending, priority drop, progress monitoring.

Rule methods **return self** (same as At/AtAll/Reply) and must be called before sending methods (Text/Image, etc.). Rules propagate with new instances created by `To`/`Using`/`Account`.

### Overview of Rule Methods

| Method | Description |
|--------|------|
| `.Hook(callback)` | Callback executed after send success (can be called multiple times, executed in order) |
| `.Retry(times=1)` | Automatically retry N times on failure (N+1 attempts including the first) |
| `.Timeout(seconds)` | Single send timeout, cancels current attempt if exceeded (can be stacked with Retry) |
| `.Defer(seconds=1.0)` | Deferred send (process timer, not persisted) |
| `.Priority(level, drop_if_busy=False)` | Set priority; can drop when backlog exists |
| `.OnProgress(callback)` | Progress callback for each stage (passing `SendContext`) |
| `.OnError(callback)` | Error callback on final failure (triggered only once) |

### Sending Success Logic (Hook)

```python
# Synchronous callback
await (adapter.Send.To("user", "123")
       .Hook(lambda r: print(f"发送成功，消息ID: {r['message_id']}"))
       .Text("你好"))

# Async callback
async def deduct_points(result):
    await db.update(user_id="123", points=-1)

await adapter.Send.To("user", "123").Hook(deduct_points).Text("扣积分")
```

Hook only executes when the send is ultimately successful (including retry success); failure, timeout, or cancellation does not trigger.

### Automatic Failure Retry (Retry)

```python
# Retry 2 times after first failure, total 3 attempts
result = await adapter.Send.To("user", "123").Retry(2).Text("带重试")
```

Retry triggers when sending throws an exception, sending times out, or sending returns a response with `status == "failed"`.

### Automatic Timeout Cancellation (Timeout)

```python
# Cancel if single send exceeds 10 seconds
await adapter.Send.To("user", "123").Timeout(10).Text("带超时")

# Timeout + Retry: 10 seconds per attempt, max 3 times
await adapter.Send.To("user", "123").Timeout(10).Retry(2).Text("超时重试")
```

### Progress Monitoring (OnProgress / OnError)

```python
def on_progress(ctx):
    print(f"阶段: {ctx.stage}, 尝试: {ctx.attempt + 1}/{ctx.max_attempts}, 耗时: {ctx.elapsed:.2f}s")
    if ctx.stage == "failed":
        print(f"  错误: {ctx.error!r}")

async def on_error(ctx):
    await notify_admin(f"发送给 {ctx.target_id} 失败: {ctx.error!r}")

await (adapter.Send.To("user", "123")
       .Retry(3).Timeout(10)
       .OnProgress(on_progress)
       .OnError(on_error)
       .Text("监控"))
```

Fields in `SendContext`: `task_id`, `platform`, `method`, `target_type`, `target_id`, `bot_id`, `stage`, `attempt`, `max_attempts`, `started_at`, `finished_at`, `elapsed`, `error`, `result`, `extra`.

Possible values of `stage`: `pending`, `sending`, `retrying`, `success`, `failed`, `timeout`, `cancelled`, `dropped`.

### Deferred Sending (Defer)

```python
# Send after 5 seconds
await adapter.Send.To("user", "123").Defer(5).Text("迟到消息")
```

> Note: Delay is a process timer; process restarts will lose it, no persistence provided.

### Priority and Backlog Drop (Priority)

```python
# Low priority message, dropped when queue is backed up
result = await (adapter.Send.To("user", "123")
               .Priority(-1, drop_if_busy=True)
               .Text("可放弃的通知"))
# If dropped, result["status"] == "failed"
```

When `drop_if_busy` is enabled, the current send is abandoned directly when the number of in-flight sending tasks exceeds the threshold (default 64). Global threshold can be adjusted via `.PriorityThreshold(n)`.

### Rule Combination and Background Execution

```python
# Don't block main flow, rules still work
task = (adapter.Send.To("user", "123")
        .Hook(lambda r: print("发送成功！"))
        .Retry(3)
        .Timeout(10)
        .OnProgress(on_progress)
        .Text("你好"))

# Continue executing other operations
await handle_next_action()
```

### Rule Propagation

Rules propagate with new instances created by `To`/`Using`/`Account`, preventing rules from being lost in the chain:

```python
# Rules set before To also propagate to instances created by To
builder = adapter.Send.Retry(3).Timeout(10)
send = builder.To("user", "123")  # send still carries Retry(3) and Timeout(10)
await send.Text("hi")
```

Rules of multiple instances are independent from each other (hooks list deep copied).

## Bulk Build Mode (Build)

Besides single-send mode, SendDSL also supports bulk build mode: writing multiple sending methods in one chain, executed uniformly at the end. Suitable for "send multiple messages at once" scenarios.

### Entering Build Mode

Call `.Build()` before sending methods to return a `SendBuilder`. Subsequent sending methods (Text/Image, etc.) will no longer execute immediately but accumulate as send intents:

```python
results = await (adapter.Send.To("user", "123")
                 .Build()                    # Enter build mode
                 .Text("第一句")
                 .Image("pic.jpg")
                 .Text("第二句")
                 .send_all())                 # Execute uniformly
# results = [Text result, Image result, Text result]
```

`.send_all()` returns `asyncio.Task`; await to get the list of results (in intent order).

### Parallel vs Sequential

Default **parallel** execution (concurrent sending, total time approx equal to the slowest one). Call `.Sequential()` when message arrival order must be guaranteed:

```python
# Sequential: send in order
await (adapter.Send.To("group", "456")
       .Build()
       .Sequential()
       .Text("先发这个").Text("再发这个")
       .send_all())

# Parallel (default, can be called explicitly)
await (adapter.Send.To("group", "456")
       .Build()
       .Parallel()
       .Text("并发1").Text("并发2")
       .send_all())
```

### Fail Continue and Retry

Bulk execution uses **fail-continue** strategy: failure of one item does not interrupt sending of others. Combined with `.Retry()`, failed items will retry automatically (retry applies to individual items, not the whole batch):

```python
await (adapter.Send.To("user", "123")
       .Build()
       .Retry(2)                       # Retry 2 times for each item
       .Text("可能失败的").Image("也可能失败的")
       .send_all())
```

### Batch Rules and Callbacks

Rules apply uniformly to the whole batch:

| Method | Description |
|--------|------|
| `.Timeout(seconds)` | Single send timeout per item |
| `.Retry(times)` | Retry each item individually (fail continue) |
| `.Defer(seconds)` | Defer the entire batch |
| `.Hook(callback)` | Triggered after all items in batch succeed, receiving `results` list |
| `.OnError(callback)` | Triggered when there is a failure in the batch, receiving `BatchContext` |
| `.OnProgress(callback)` | Triggered when each item completes, receiving `BatchContext` |

```python
def on_progress(ctx):
    print(f"进度: {ctx.completed}/{ctx.total}, 成功 {ctx.succeeded}, 失败 {ctx.failed}")

async def on_error(ctx):
    print(f"批次有 {ctx.failed} 条失败")

results = await (adapter.Send.To("user", "123")
               .Build()
               .Retry(2).Timeout(10)
               .OnProgress(on_progress)
               .OnError(on_error)
               .Hook(lambda rs: print("整批完成"))
               .Text("a").Text("b").Text("c")
               .send_all())
```

`BatchContext` contains: `task_id`, `total`, `completed`, `succeeded`, `failed`, `stage`, `results`, `errors`, `elapsed`, `extra`.

Possible values of `stage`: `pending`, `sending`, `success` (all succeeded), `partial` (some succeeded), `failed` (all failed).

### Inheritance of Modifiers and Rules

`At`/`AtAll`/`Reply` modifiers and rules set before `.Build()` are inherited to the whole batch, applied to each message:

```python
await (adapter.Send.To("group", "456")
       .At("789")                        # Inherited: every message @789
       .Build()
       .Retry(2)                         # Inherited + Appended: each retries individually
       .Text("@你的通知")
       .Image("公告图")
       .send_all())
```

Modifiers can still be appended after entering Build (applied to whole batch):

```python
await (adapter.Send.To("group", "456")
       .Build()
       .At("111").At("222")             # Append @, applied to whole batch
       .Text("@多人")
       .send_all())
```

### Background Execution

Like single-send, `.send_all()` returns Task and can be awaited to let it run in background:

```python
task = (adapter.Send.To("user", "123")
        .Build()
        .Hook(lambda rs: print("批量发送完成"))
        .Text("a").Text("b")
        .send_all())

# Don't block main flow
await do_something_else()
```

## Naming Conventions

### PascalCase Naming

All sending methods use PascalCase:

```python
# ✅ Correct
def Text(self, text: str):
    pass

def Image(self, file: bytes):
    pass

# ❌ Incorrect
def text(self, text: str):
    pass

def send_image(self, file: bytes):
    pass
```

### Platform Specific Methods

It is not recommended to add platform prefix methods:

```python
# ✅ Recommended
def Sticker(self, sticker_id: str):
    pass

# ❌ Not recommended
def TelegramSticker(self, sticker_id: str):
    pass
```

Use `Raw` methods instead:

```python
# ✅ Recommended
await adapter.Send.Raw_ob12([{"type": "sticker", ...}])

# ❌ Not recommended
def TelegramSticker(self, ...):
    pass
```

## Return Values

### Task Objects

All sending methods return `asyncio.Task`. Adapters only need to implement `Raw_ob12`, standard methods (Text/Image, etc.) default to delegating to it:

```python
import asyncio

def Raw_ob12(self, message, **kwargs):
    async def _do_send():
        segments = self._apply_modifiers(message)
        return await self._adapter.call_api(
            endpoint="/send_message",
            message=segments,
            **self.send_context,
            **kwargs,
        )
    return asyncio.create_task(_do_send())

# Text/Image/Voice/Video/File inherited from base class, automatically delegating to Raw_ob12
# To override standard methods, simply return asyncio.Task:
# def Text(self, text: str):
#     return self.Raw_ob12([{"type": "text", "data": {"text": text}}])
```

### Standardized Response

`call_api` should return a standardized response. It is recommended to use `make_response()` / `make_error()` methods:

```python
async def call_api(self, endpoint: str, **params):
    try:
        result = await self._do_api_call(endpoint, **params)
        return self.make_response(
            data=result.get("data"),
            message_id=result.get("message_id", ""),
            raw=result,
        )
    except Exception as e:
        return self.make_error(message=str(e))
```

Manually constructing is also supported (old style still compatible):

```python
async def call_api(self, endpoint: str, **params):
    return {
        "status": "ok" or "failed",
        "retcode": 0 or error_code,
        "data": {...},
        "message_id": "msg_id" or "",
        "message": "",
        "{platform}_raw": raw_response
    }
```

## Complete Example

### Basic Usage

```python
from ErisPulse.Core import adapter

my_adapter = adapter.get("myplatform")

# Send text
await my_adapter.Send.To("user", "123").Text("Hello World!")

# Send image
await my_adapter.Send.To("group", "456").Image("https://example.com/image.jpg")

# Send file
with open("document.pdf", "rb") as f:
    await my_adapter.Send.To("user", "123").File(f.read())
```

### Chained Calls

```python
# @ user + reply
await my_adapter.Send.To("group", "456").At("789").Reply("msg123").Text("回复@的消息")

# @ all + multiple modifiers
await my_adapter.Send.Using("bot1").To("group", "456").AtAll().Text("公告消息")
```

### Raw Messages and Message Building

`Raw_ob12` is the core entry point for reverse conversion (receives OB12 message segments → Platform API call), and `MessageBuilder` is the chained message segment building tool used in conjunction with it.

> For complete `Raw_ob12` implementation specs, `MessageBuilder` usage and code examples, see:
> - [Send Method Specification §6 Reverse Conversion Spec](../../standards/send-method-spec.md#6-反向转换规范onebot12--平台)
> - [Send Method Specification §11 Message Builder](../../standards/send-method-spec.md#11-消息构建器-messagebuilder)

## Related Documents

- [Getting Started with Adapters](getting-started.md) - Create adapters
- [Core Concepts of Adapters](core-concepts.md) - Understand adapter architecture
- [Best Practices for Adapters](best-practices.md) - Develop high-quality adapters
- [Send Method Specification](../../standards/send-method-spec.md) - Complete specification for sending methods