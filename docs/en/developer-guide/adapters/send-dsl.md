# SendDSL Deep Dive

SendDSL is a message sending interface provided by the ErisPulse adapter, featuring a chain-call style.

## Basic Call Methods

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

## Method Chain

```
Using/Account() → To() → [Modifier Methods] → [Sending Methods]
```

## Sending Methods

All sending methods must return an `asyncio.Task` object.

### Basic Methods

| Method Name | Description | Return Value |
|--------|------|---------|
| `Text(text: str)` | Send text message | `asyncio.Task` |
| `Image(file: bytes \| str)` | Send image | `asyncio.Task` |
| `Voice(file: bytes \| str)` | Send voice | `asyncio.Task` |
| `Video(file: bytes \| str)` | Send video | `asyncio.Task` |
| `File(file: bytes \| str)` | Send file | `asyncio.Task` |

### Protocol Methods

| Method Name | Description | Return Value | Required |
|--------|------|---------|---------|
| `Raw_ob12(message)` | Send OneBot12 format message | `asyncio.Task` | **Must Implement** |

> **Important**: `Raw_ob12` is the core method of the adapter, **must implement**. It is the unified entry point for reverse conversion (OneBot12 → Platform). When not implemented, the base class will log an error and return a standard error response (`status: "failed"`, `retcode: 10002`). Standard methods (`Text`, `Image`, etc.) should delegate internally to `Raw_ob12`.

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
# reply message
await adapter.Send.To("group", "123").Reply("msg_id").Text("回复内容")
```

### Combined Modifiers

```python
await adapter.Send.To("group", "123").At("456").Reply("msg_id").Text("回复@的消息")
```

## Account Management

### Using Method

`Using()` is used to specify the account to send the message. The passed identifier will be matched by `_resolve_account()` with the following priority:

1. **Account Name** — The key name in the config (e.g., `"default"`, `"bot1"`)
2. **Runtime injected bot_id** — Identifier automatically injected when converting from the event
3. **Any str field** — Other string fields in the config
4. **Fallback** — The first enabled account

```python
# Use account name
await adapter.Send.Using("account1").To("user", "123").Text("Hello")

# Use bot_id (the self.user_id in the event)
await adapter.Send.Using("bot_123").To("user", "123").Text("Hello")
```

### Account Method

`Account` method is equivalent to `Using`:

```python
await adapter.Send.Account("account1").To("user", "123").Text("Hello")
```

## Async Processing

### Do Not Wait for Result

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
print(f"Send result: {result}")

# Save Task first, wait later
task = adapter.Send.To("user", "123").Text("Hello")
# ... other operations ...
result = await task
```

## Sending Rule System

SendDSL includes a built-in set of sending rule decorators. Rules are attached via chain methods and applied uniformly at the final send. Rules cover common production scenarios: timeout control, failure retry, success callback, delayed send, priority drop, and progress monitoring.

Rule methods **return self** (same as At/AtAll/Reply) and must be called before sending methods (Text/Image, etc.). Rules propagate with new instances created by `To`/`Using`/`Account`.

### Rule Methods Overview

| Method | Description |
|--------|------|
| `.Hook(callback)` | Callback executed after successful send (can be called multiple times, executes sequentially) |
| `.Retry(times=1)` | Automatically retry N times on failure (N+1 total attempts including the first) |
| `.Timeout(seconds)` | Single send timeout; cancels current attempt on timeout (can stack with Retry) |
| `.Defer(seconds=1.0)` | Delayed send (in-process timer, not persistent) |
| `.Priority(level, drop_if_busy=False)` | Set priority; discard when backlog occurs |
| `.OnProgress(callback)` | Progress callback for each stage (passes `SendContext`) |
| `.OnError(callback)` | Error callback on final failure (triggers only once) |

### Logic Executed After Send Success (Hook)

```python
# Sync callback
await (adapter.Send.To("user", "123")
       .Hook(lambda r: print(f"Send successful, message_id: {r['message_id']}"))
       .Text("你好"))

# Async callback
async def deduct_points(result):
    await db.update(user_id="123", points=-1)

await adapter.Send.To("user", "123").Hook(deduct_points).Text("扣积分")
```

Hook is executed only when the send eventually succeeds (including retries). Failure, timeout, and cancellation do not trigger.

### Failure Auto-Retry (Retry)

```python
# Retry 2 times after first failure, total 3 attempts
result = await adapter.Send.To("user", "123").Retry(2).Text("带重试")
```

Retry trigger conditions: send throws an exception, send times out, or send returns a response with `status == "failed"`.

### Timeout Auto-Cancellation (Timeout)

```python
# Cancel if single send exceeds 10 seconds
await adapter.Send.To("user", "123").Timeout(10).Text("带超时")

# Timeout + Retry: 10 seconds per attempt, max 3 times
await adapter.Send.To("user", "123").Timeout(10).Retry(2).Text("超时重试")
```

### Progress Monitoring (OnProgress / OnError)

```python
def on_progress(ctx):
    print(f"Stage: {ctx.stage}, Attempt: {ctx.attempt + 1}/{ctx.max_attempts}, Elapsed: {ctx.elapsed:.2f}s")
    if ctx.stage == "failed":
        print(f"  Error: {ctx.error!r}")

async def on_error(ctx):
    await notify_admin(f"Send to {ctx.target_id} failed: {ctx.error!r}")

await (adapter.Send.To("user", "123")
       .Retry(3).Timeout(10)
       .OnProgress(on_progress)
       .OnError(on_error)
       .Text("监控"))
```

Fields contained in `SendContext`: `task_id`, `platform`, `method`, `target_type`, `target_id`, `bot_id`, `stage`, `attempt`, `max_attempts`, `started_at`, `finished_at`, `elapsed`, `error`, `result`, `extra`.

Possible values for `stage`: `pending`, `sending`, `retrying`, `success`, `failed`, `timeout`, `cancelled`, `dropped`.

### Delayed Send (Defer)

```python
# Send after 5 seconds
await adapter.Send.To("user", "123").Defer(5).Text("迟到消息")
```

> Note: Delay is an in-process timer; process restarts will lose it. No persistence is provided.

### Priority and Backlog Drop (Priority)

```python
# Low priority message, discard automatically when backlog occurs
result = await (adapter.Send.To("user", "123")
               .Priority(-1, drop_if_busy=True)
               .Text("可放弃的通知"))
# If discarded, result["status"] == "failed"
```

When `drop_if_busy` is enabled, the current send is directly abandoned when the number of in-flight send tasks exceeds the threshold (default 64). The global threshold can be adjusted via `.PriorityThreshold(n)`.

### Rule Combination and Background Execution

```python
# Non-blocking main flow, rules still take effect
task = (adapter.Send.To("user", "123")
        .Hook(lambda r: print("Send successful!"))
        .Retry(3)
        .Timeout(10)
        .OnProgress(on_progress)
        .Text("你好"))

# Continue executing other operations
await handle_next_action()
```

### Rule Propagation

Rules propagate with new instances created by `To`/`Using`/`Account`, preventing rule loss in chain calls:

```python
# Rules set before To are also propagated to the instance created by To
builder = adapter.Send.Retry(3).Timeout(10)
send = builder.To("user", "123")  # send still carries Retry(3) and Timeout(10)
await send.Text("hi")
```

Rules of multiple instances are independent from each other (hooks list is deep copied).

## Bulk Build Mode (Build)

In addition to single send mode, SendDSL supports a bulk build mode: writing multiple sending methods in a single chain and executing them all at once. Suitable for scenarios like "sending multiple messages in one go".

### Enter Build Mode

Call `.Build()` before sending methods to return a `SendBuilder`. Subsequent sending methods (Text/Image, etc.) will not execute immediately but accumulate into send intents:

```python
results = await (adapter.Send.To("user", "123")
                 .Build()                    # Enter build mode
                 .Text("第一句")
                 .Image("pic.jpg")
                 .Text("第二句")
                 .send_all())                 # Execute all unified
# results = [TextResult, ImageResult, TextResult]
```

`.send_all()` returns an `asyncio.Task`. After await, a list of results is obtained (in the order of intents).

### Parallel and Serial

Default **parallel** execution (concurrent send, total time approx equal to the slowest one). Call `.Sequential()` to ensure message arrival order:

```python
# Sequential: send one by one in order
await (adapter.Send.To("group", "456")
       .Build()
       .Sequential()
       .Text("先发这个").Text("再发这个")
       .send_all())

# Parallel (default, can be explicit)
await (adapter.Send.To("group", "456")
       .Build()
       .Parallel()
       .Text("并发1").Text("并发2")
       .send_all())
```

### Failure Continue and Retry

Bulk execution adopts a **failure continue** strategy: failure of one item will not interrupt the sending of others. When combined with `.Retry()`, failed items will automatically retry (retry applies to individual items, not the whole batch):

```python
await (adapter.Send.To("user", "123")
       .Build()
       .Retry(2)                       # Each item retries 2 times individually
       .Text("可能失败的").Image("也可能失败的")
       .send_all())
```

### Batch Rules and Callbacks

Rules uniformly apply to the whole batch:

| Method | Description |
|--------|------|
| `.Timeout(seconds)` | Single send timeout for each item |
| `.Retry(times)` | Each individual item retry on failure (failure continue) |
| `.Defer(seconds)` | Delay sending the entire batch |
| `.Hook(callback)` | Triggered after all batch items succeed, receives `results` list |
| `.OnError(callback)` | Triggered when the batch contains failures, receives `BatchContext` |
| `.OnProgress(callback)` | Triggered when each item completes, receives `BatchContext` |

```python
def on_progress(ctx):
    print(f"Progress: {ctx.completed}/{ctx.total}, Success {ctx.succeeded}, Failed {ctx.failed}")

async def on_error(ctx):
    print(f"Batch has {ctx.failed} items failed")

results = await (adapter.Send.To("user", "123")
               .Build()
               .Retry(2).Timeout(10)
               .OnProgress(on_progress)
               .OnError(on_error)
               .Hook(lambda rs: print("Whole batch done"))
               .Text("a").Text("b").Text("c")
               .send_all())
```

`BatchContext` contains: `task_id`, `total`, `completed`, `succeeded`, `failed`, `stage`, `results`, `errors`, `elapsed`, `extra`.

Possible values for `stage`: `pending`, `sending`, `success` (all succeed), `partial` (some succeed), `failed` (all fail).

### Inheritance of Modifiers and Rules

At/AtAll/Reply modifiers and rules set before `.Build()` are inherited to the whole batch and applied to each message:

```python
await (adapter.Send.To("group", "456")
       .At("789")                        # Inherited: every message @789
       .Build()
       .Retry(2)                         # Inherited + Appended: each item retries individually
       .Text("@你的通知")
       .Image("公告图")
       .send_all())
```

Modifiers can still be appended after entering Build (applies to the whole batch):

```python
await (adapter.Send.To("group", "456")
       .Build()
       .At("111").At("222")             # Append @, applies to whole batch
       .Text("@多人")
       .send_all())
```

### Background Execution

Same as single send, `.send_all()` returns Task, and you can choose not to await to let it execute in the background:

```python
task = (adapter.Send.To("user", "123")
        .Build()
        .Hook(lambda rs: print("Bulk send done"))
        .Text("a").Text("b")
        .send_all())

# Non-blocking main flow
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

Adding platform prefix methods is not recommended:

```python
# ✅ Recommended
def Sticker(self, sticker_id: str):
    pass

# ❌ Not recommended
def TelegramSticker(self, sticker_id: str):
    pass
```

Use `Raw` method instead:

```python
# ✅ Recommended
await adapter.Send.Raw_ob12([{"type": "sticker", ...}])

# ❌ Not recommended
def TelegramSticker(self, ...):
    pass
```

## Return Values

### Task Object

All sending methods return `asyncio.Task`:

```python
import asyncio

def Text(self, text: str):
    return asyncio.create_task(
        self._adapter.call_api(
            endpoint="/send",
            content=text,
            recvId=self._target_id,
            recvType=self._target_type
        )
    )
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

Manual construction is also supported (old style still compatible):

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

### Chain Call

```python
# @ user + reply
await my_adapter.Send.To("group", "456").At("789").Reply("msg123").Text("回复@的消息")

# @ all + multiple modifiers
await my_adapter.Send.Using("bot1").To("group", "456").AtAll().Text("公告消息")
```

### Raw Message and Message Building

`Raw_ob12` is the core entry point for reverse conversion (receives OB12 message segments → Platform API calls), and `MessageBuilder` is a chain message segment builder tool used with it.

> For complete `Raw_ob12` implementation specifications, `MessageBuilder` usage, and code examples, please refer to:
> - [Sending Method Specification §6 Reverse Conversion Specification](../../standards/send-method-spec.md#6-reverse-conversion-specification-onebot12--platform)
> - [Sending Method Specification §11 Message Builder](../../standards/send-method-spec.md#11-message-builder-messagebuilder)

## Related Documentation

- [Adapter Development Getting Started](getting-started.md) - Creating adapters
- [Adapter Core Concepts](core-concepts.md) - Understanding adapter architecture
- [Adapter Best Practices](best-practices.md) - Developing high-quality adapters
- [Sending Method Specification](../../standards/send-method-spec.md) - Complete specification for sending methods