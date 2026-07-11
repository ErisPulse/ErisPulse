# `ErisPulse.Core.Bases.send_builder` 模块

---

## 模块概述


SendDSL 批量构建系统

提供 :class:`SendBuilder`，支持在一条链路中构建多个发送方法，
最后统一执行。规则统一作用于整批（Plan C）：每条发送各自应用
Timeout/Retry（失败继续、重试失败的），整批层面统一 Hook/OnError/OnProgress。

进入方式：``adapter.Send.To("user", "123").Build().Text("...").Image("...")``
执行方式：``await builder.send_all()`` （默认并行，``.Sequential()`` 切换串行）

> **提示**
> 1. Build() 之前的 At/AtAll/Reply/规则会继承到整批
> 2. 默认并行执行，需要保证消息顺序时调用 .Sequential()
> 3. 失败的条目会自动重试（沿用 Retry 规则），其他条目继续发送

---

## 类列表


### `class BatchContext`

批量发送的实时执行上下文

在批量执行过程中持续更新，并传递给 OnProgress / OnError 回调。

:ivar task_id: 批次唯一标识
:ivar total: 批次总条数
:ivar completed: 已完成条数（成功 + 失败）
:ivar succeeded: 成功条数
:ivar failed: 失败条数
:ivar stage: 批次阶段：
    ``"pending"``（待执行）、``"sending"``（执行中）、
    ``"success"``（全部成功）、``"partial"``（部分成功）、
    ``"failed"``（全部失败）
:ivar results: 每条结果（按意图顺序），失败的为 None
:ivar errors: 每条错误（按意图顺序），成功的为 None
:ivar started_at: 开始时间戳
:ivar finished_at: 结束时间戳，未结束时为 None
:ivar extra: 预留扩展字段


#### 方法列表


##### `elapsed()`

已耗时（秒）

---


##### `to_dict()`

转为可序列化字典（用于日志/上报）

---


### `class SendBuilder`

批量发送构建器

通过 :meth:`SendDSL.Build` 进入构建模式。在此模式下，发送方法
（Text/Image 等）不再立即执行，而是累积为发送意图，最后通过
:meth:`send_all` 统一执行。

规则统一作用于整批：
- ``Timeout`` / ``Retry``：应用到每条发送（失败继续，重试失败的）
- ``Hook``：整批全部成功后触发一次，接收 ``results`` 列表
- ``OnError``：批次存在失败时触发一次，接收 :class:`BatchContext`
- ``OnProgress``：每条完成时触发，接收 :class:`BatchContext`

**示例**:
```python
>>> results = await (adapter.Send.To("user", "123")
...                  .Build()
...                  .Text("第一句")
...                  .Image("pic.jpg")
...                  .Retry(2)
...                  .send_all())
>>> # results = [Text结果, Image结果]
```


#### 方法列表


##### `__init__(send_dsl: 'SendDSL')`

从 SendDSL 实例构建批量发送器

:param send_dsl: 进入 Build 前的 SendDSL 实例（继承其上下文与规则）

---


##### `At(user_id: str)`

@指定用户（作用于整批所有消息）

:param user_id: 要@的用户ID
:return: SendBuilder实例自身

---


##### `AtAll()`

@全体成员（作用于整批所有消息）

---


##### `Reply(message_id: str)`

回复指定消息（作用于整批所有消息）

:param message_id: 要回复的消息ID

---


##### `Sequential()`

切换为串行执行（按意图顺序依次发送）

保证消息到达顺序，但总耗时为各条耗时之和。

:return: SendBuilder实例自身

---


##### `Parallel()`

切换为并行执行（默认）

并发发送所有意图，总耗时约等于最慢的一条。不保证消息到达顺序。

:return: SendBuilder实例自身

---


##### `Retry(times: int = 1)`

设置每条发送的失败重试次数（作用于每条，非整批重试）

:param times: 重试次数（不含首次），默认 1

---


##### `Timeout(seconds: float)`

设置每条发送的单次超时时间

:param seconds: 超时秒数

---


##### `Defer(seconds: float = 1.0)`

延迟执行整批发送

:param seconds: 延迟秒数

---


##### `Hook(callback: Callable)`

附加整批成功后的回调

仅当批次全部成功时触发一次，回调签名为 ``callback(results: list)``。

:param callback: 回调函数（同步或协程），接收结果列表

---


##### `OnError(callback: Callable)`

设置批次失败回调

批次存在任意失败条目时触发一次，回调签名为 ``callback(ctx: BatchContext)``。

:param callback: 回调函数（同步或协程）

---


##### `OnProgress(callback: Callable)`

设置批次进度回调

每条意图完成时触发，回调签名为 ``callback(ctx: BatchContext)``。

:param callback: 回调函数（同步或协程）

---


##### `__getattr__(name: str)`

捕获发送方法为意图

任何非下划线、非已定义方法的属性访问，都会被视为发送方法，
返回一个函数；调用后把 (方法名, 参数) 存入意图队列，返回 self 以继续链式。

---


##### `send_all()`

执行整批发送

根据执行模式（默认并行 / .Sequential() 串行）发送所有意图，
失败的条目自动重试（沿用 Retry 规则），其他条目继续发送。

:return: ``asyncio.Task``，await 后返回每条结果的列表（按意图顺序）

---


##### `_make_send_instance()`

创建一个带当前 modifiers/target 的 SendDSL 实例（用于调用原始发送方法）

直接使用适配器实例上当前的 Send 类构造，绕过 __getattribute__ 的包装，
由本构建器自行管理规则与生命周期。

---


##### `_resolve_method(send_inst, method_name: str)`

在 SendDSL 实例的类上解析发送方法（大小写不敏感）

:return: 未绑定的方法对象，或 None（未找到）

---


##### `async async _emit_lifecycle(event: str)`

触发整批的生命周期事件

---

