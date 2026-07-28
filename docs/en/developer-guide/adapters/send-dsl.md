# SendDSL Deep Dive

SendDSL is the message sending interface provided by the ErisPulse adapter, featuring a chaining style.

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

### 4. Combined Usage

```python
await adapter.Send.Using("bot1").To("group", "123").Text("Hello")
```

## Method Chaining

```
Using/Account() → To() → [Modifier Methods] → [Sending Methods]
```

## Sending Methods

All sending methods return `asyncio.Task` objects.

### Basic Methods (Built-in in Base Class)

The following standard methods are built-in to the `SendDSL` base class, **delegating to `Raw_ob12` by default**. Adapter subclasses do not need to implement them repeatedly and can use them directly; IDEs can auto-complete them:

| Method Name | Description | Return Value |
|--------|------|---------|
| `Text(text: str)` | Send a text message | `asyncio.Task` |
| `Image(file: bytes \| str)` | Send an image | `asyncio.Task` |
| `Voice(file: bytes \| str)` | Send audio (OneBot12 `audio` segment) | `asyncio.Task` |
| `Video(file: bytes \| str)` | Send a video | `asyncio.Task` |
| `File(file: bytes \| str, filename: str = None)` | Send a file | `asyncio.Task` |

Adapters can override individual standard methods to provide platform-specific logic:

```python
class Send(SendDSL):
    def Raw_ob12(self, message, **kwargs):
        # Must implement
        ...

    # Optional: Override Text to provide platform-specific logic
    # def Text(self, text: str):
    #     return self.Raw_ob12([{"type": "text", "data": {"text": text}}])
```

### Protocol Methods

| Method Name | Description | Return Value | Must Implement |
|--------|------|---------|---------|
| `Raw_ob12(message)` | Send OneBot12 format message | `asyncio.Task` | **Must Implement** |

> **Important**: `Raw_ob12` is the core method of the adapter, **must be implemented**. It is the unified entry point for reverse conversion (OneBot12 → Platform). If not implemented, the base class will log an error and return a standard error response (`status: "failed"`, `retcode: 10002`). Standard methods (`Text`, `Image`, etc.) delegate to `Raw_ob12` by default.

### Platform-Specific Methods

Adapters can add platform-specific sending methods in `Send` subclasses (which will be recognized by `event.supports()` / `event.available_methods()`):

```python
class Send(SendDSL):
    def Raw_ob12(self, message, **kwargs): ...

    # Platform-specific method
    def Sticker(self, sticker_id: str):
        return self.Raw_ob12([{"type": "sticker", "data": {"id": sticker_id}}])
```

## Modifier Methods

Modifier methods return `self` to support chaining.

### At Method

```python
# @ single user
await adapter.Send.To("group", "123").At("456").Text("你好")

# @ multiple users
await adapter.Send.To("group", "123").At("456").At("789").Text("你们好")
```

### AtAll Method

```python
# @ everyone
await adapter.Send.To("group", "123").AtAll().Text("大家好")
```

### Reply Method

```python
# Reply to a message
await adapter.Send.To("group", "123").Reply("msg_id").Text("回复内容")
```

### Combined Modifiers

```python
await adapter.Send.To("group", "123").At("456").Reply("msg_id").Text("回复@的消息")
```

### Platform-Specific Modifier Methods

In addition to the built-in `At`/`AtAll`/`Reply`, adapters can define **platform-specific modifier methods**. These methods **only need to return `self`** without any decorators—the framework will automatically recognize them:

- Returns `self` (SendDSL instance) → Modifier method, does not trigger send wrapping/lifecycle events, chain continues
- Returns `Task`/`Awaitable` → Sending method

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

    # Sending method: returns Task, relies on state set by modifier methods
    def Board(self, content: str, **kwargs):
        return self.Raw_ob12([{"type": "board", "data": {"text": content}}])
```

Usage:

```python
# Modifier methods can be chained continuously
await adapter.Send.To("group", "big").Expire(3600).ForMember("114").Board("看板内容")
```

## Using Modifier Methods in Event Wrapper Classes

`event.reply()` only exposes built-in modifier parameters like `at_sender`/`at_users`/`at_all`/`quote` by default. To use platform-specific modifier methods, there are two ways:

### Method 1: `reply()` via parameter

Suitable for a small number of known modifier methods:

```python
await event.reply("看板内容", method="Board",
                  via=[("Expire", 3600), ("ForMember", "114514")])
```

`via` is a list, each element can be:

| Form | Equivalent Chained Call |
|------|-------------|
| `"Name"` | `.Name()` |
| `("Name", arg1, arg2)` | `.Name(arg1, arg2)` |
| `("Name", (arg1,), {kw: val})` | `.Name(arg1, kw=val)` |

### Method 2: `event.send_chain()`

Suitable for **multiple consecutive modifier methods** or **action-oriented methods without content parameters** (like recall, delete). `send_chain()` returns a send chain configured with `To`/`Using`, to which you can freely append any modifier and sending methods:

```python
# Platform-specific modifier methods + Board sending
await event.send_chain().Expire(3600).Board("一小时后过期")

# Multiple consecutive modifier methods
await (event.send_chain()
       .Expire(3600)
       .ForMember("114514")
       .Board("看板内容", content_type="markdown"))

# Built-in modifier methods are also available
await event.send_chain().At("123").Reply("msg_id").Text("hi")

# Action-oriented methods without content parameters
await event.send_chain().DismissBoard()
```

## Account Management

### Using Method

`Using()` is used to specify the account sending the message. The passed identifier will be matched by `_resolve_account()` with the following priority:

1. **Account Name** — The key name in the configuration (e.g., `"default"`, `"bot1"`)
2. **Runtime-injected bot_id** — The identifier automatically injected during event conversion
3. **Any str field** — Other string fields in the configuration
4. **Fallback** — The first enabled account

```python
# Use account name
await adapter.Send.Using("account1").To("user", "123").Text("Hello")

# Use bot_id (i.e., self.user_id in the event)
await adapter.Send.Using("bot_123").To("user", "123").Text("Hello")
```

### Account Method

`Account` method is equivalent to `Using`:

```python
await adapter.Send.Account("account1").To("user", "123").Text("Hello")
```

## Async Processing

### Don't Wait for Result

```python
# Send message in the background
task = adapter.Send.To("user", "123").Text("Hello")

# Continue executing other operations
# ...
```

### Wait for Result

```python
# Await directly to get result
result = await adapter.Send.To("user", "123").Text("Hello")
print(f"Send result: {result}")

# Save Task first, wait later
task = adapter.Send.To("user", "123").Text("Hello")
# ... other operations ...
result = await task
```

## Sending Rules System

SendDSL is built with a set of sending rule decorators. By attaching rules via chaining methods, they are uniformly applied when sending. Rules cover common production scenarios: timeout control, failure retry, success callback, delayed sending, priority dropping, progress monitoring.

Rule methods **return self** (same as At/AtAll/Reply) and must be called before sending methods (Text/Image, etc.). Rules propagate with new instances created by `To`/`Using`/`Account`.

### Overview of Rule Methods

| Method | Description |
|--------|------|
| `.Hook(callback)` | Callback to execute after sending success (can be called multiple times, executes in order) |
| `.Retry(times=1)` | Auto retry N times on failure (N+1 attempts total including the first) |
| `.Timeout(seconds)` | Timeout for a single send, cancels current attempt on timeout (can be stacked with Retry) |
| `.Defer(seconds=1.0)` | Delay sending (in-process timer, not persistent) |
| `.Priority(level, drop_if_busy=False)` | Set priority; can drop if backlog |
| `.OnProgress(callback)` | Progress callback at each stage (receives `SendContext`) |
| `.OnError(callback)` | Error callback on final failure (triggered only once) |

### Sending Success Logic (Hook)

```python
# Synchronous callback
await (adapter.Send.To("user", "123")
       .Hook(lambda r: print(f"发送成功，消息ID: {r['message_id']}"))
       .Text("你好"))

# Asynchronous callback
async def deduct_points(result):
    await db.update(user_id="123", points=-1)

await adapter.Send.To("user", "123").Hook(deduct_points).Text("扣积分")
```

Hook only executes when sending finally succeeds (including retry success); failures, timeouts, and cancellation do not trigger.

### Failure Auto-Retry (Retry)

```python
# Retry 2 times after first failure, total 3 attempts
result = await adapter.Send.To("user", "123").Retry(2).Text("带重试")
```

Retry trigger conditions: sending throws an exception, sending times out, or sending returns a response with `status == "failed"`.

### Timeout Auto-Cancel (Timeout)

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

Fields contained in `SendContext`: `task_id`, `platform`, `method`, `target_type`, `target_id`, `bot_id`, `stage`, `attempt`, `max_attempts`, `started_at`, `finished_at`, `elapsed`, `error`, `result`, `extra`.

Possible values for `stage`: `pending`, `sending`, `retrying`, `success`, `failed`, `timeout`, `cancelled`, `dropped`.

### Delayed Sending (Defer)

```python
# Send after 5 seconds
await adapter.Send.To("user", "123").Defer(5).Text("迟到消息")
```

> Note: Delay is in-process timer, will be lost on process restart, no persistence provided.

### Priority and Backlog Dropping (Priority)

```python
# Low priority message, automatically dropped when queue backlog
result = await (adapter.Send.To("user", "123")
               .Priority(-1, drop_if_busy=True)
               .Text("可放弃的通知"))
# If dropped, result["status"] == "failed"
```

When `drop_if_busy` is enabled, if the number of in-flight sending tasks exceeds the threshold (default 64), the current send is directly abandoned. The global threshold can be adjusted via `.PriorityThreshold(n)`.

### Rule Combination and Background Execution

```python
# Don't block main flow, rules still take effect
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

Rules propagate with new instances created by `To`/`Using`/`Account`, avoiding rule loss in chaining:

```python
# Rules set before To will also propagate to the instance created by To
builder = adapter.Send.Retry(3).Timeout(10)
send = builder.To("user", "123")  # send still carries Retry(3) and Timeout(10)
await send.Text("hi")
```

Rules from multiple instances are independent of each other (hooks list deep copy).

## Batch Build Mode (Build)

In addition to the single-send mode, SendDSL also supports a batch build mode: writing multiple sending methods in one chain and executing them uniformly. Suitable for scenarios like "sending multiple messages at once".

### Entering Build Mode

Call `.Build()` before sending methods, returning `SendBuilder`. From then on, sending methods (Text/Image, etc.) will no longer execute immediately, but accumulate into send intents:

```python
results = await (adapter.Send.To("user", "123")
                 .Build()                    # Enter build mode
                 .Text("第一句")
                 .Image("pic.jpg")
                 .Text("第二句")
                 .send_all())                 # Execute uniformly
# results = [TextResult, ImageResult, TextResult]
```

`.send_all()` returns `asyncio.Task`, which returns a list of results (in order of intents) after awaited.

### Parallel and Sequential

Default is **parallel** execution (concurrent sending, total time approx equals the slowest one). Call `.Sequential()` when you need to guarantee message arrival order:

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

### Failure Continue and Retry

Batch execution uses a **failure continue** strategy: failure of one item will not interrupt the sending of others. When combined with `.Retry()`, failed items will be retried automatically (retry applies to individual items, not the whole batch):

```python
await (adapter.Send.To("user", "123")
       .Build()
       .Retry(2)                       # Retry 2 times for each item
       .Text("可能失败的").Image("也可能失败的")
       .send_all())
```

### Batch Rules and Callbacks

Rules act on the whole batch uniformly:

| Method | Description |
|--------|------|
| `.Timeout(seconds)` | Timeout for each send |
| `.Retry(times)` | Retry each send individually (failure continue) |
| `.Defer(seconds)` | Delay the whole batch |
| `.Hook(callback)` | Triggered after the whole batch succeeds, receives `results` list |
| `.OnError(callback)` | Triggered if the batch has failures, receives `BatchContext` |
| `.OnProgress(callback)` | Triggered when each item is completed, receives `BatchContext` |

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

Possible values for `stage`: `pending`, `sending`, `success` (all succeeded), `partial` (some succeeded), `failed` (all failed).

### Inheritance of Modifiers and Rules

Modifiers and rules for At/AtAll/Reply before `.Build()` are inherited to the whole batch, acting on each message:

```python
await (adapter.Send.To("group", "456")
       .At("789")                        # Inherited: every message @789
       .Build()
       .Retry(2)                         # Inherited + Append: each retries individually
       .Text("@你的通知")
       .Image("公告图")
       .send_all())
```

After entering Build, modifiers can still be appended (acting on the whole batch):

```python
await (adapter.Send.To("group", "456")
       .Build()
       .At("111").At("222")             # Append @, acting on the whole batch
       .Text("@多人")
       .send_all())
```

### Background Execution

Like single-send, `.send_all()` returns Task, and can be awaited to let it execute in background:

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

### Platform-Specific Methods

It is not recommended to add platform prefix methods:

```python
# ✅ Recommended
def Sticker(self, sticker_id: str):
    pass

# ❌ Not Recommended
def TelegramSticker(self, sticker_id: str):
    pass
```

Use `Raw` methods instead:

```python
# ✅ Recommended
await adapter.Send.Raw_ob12([{"type": "sticker", ...}])

# ❌ Not Recommended
def TelegramSticker(self, ...):
    pass
```

## Return Values

### Task Objects

All sending methods return `asyncio.Task`. Adapters only need to implement `Raw_ob12`; standard methods (Text/Image, etc.) delegate to it by default:

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

# Text/Image/Voice/Video/File inherited from base class, auto-delegated to Raw_ob12
# If you need to override standard methods, simply return asyncio.Task:
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

Manually constructing (old style) is also supported:

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

### Chaining

```python
# @ user + reply
await my_adapter.Send.To("group", "456").At("789").Reply("msg123").Text("回复@的消息")

# @ all + multiple modifiers
await my_adapter.Send.Using("bot1").To("group", "456").AtAll().Text("公告消息")
```

### Raw Messages and Message Building

`Raw_ob12` is the core entry point for reverse conversion (receives OB12 message segments → Platform API call), and `MessageBuilder` is the chaining message segment building tool used with it.

> For complete `Raw_ob12` implementation specs, `MessageBuilder` usage, and code examples, please refer to:
> - [Send Method Specification §6 Reverse Conversion Specification](../../standards/send-method-spec.md#6-反向转换规范onebot12--平台)
> - [Send Method Specification §11 Message Builder](../../standards/send-method-spec.md#11-消息构建器-messagebuilder)

## Related Documents

- [Getting Started with Adapter Development](getting-started.md) - Creating adapters
- [Core Adapter Concepts](core-concepts.md) - Understanding adapter architecture
- [Adapter Best Practices](best-practices.md) - Developing high-quality adapters
- [Send Method Specification](../../standards/send-method-spec.md) - Complete specification of send methods