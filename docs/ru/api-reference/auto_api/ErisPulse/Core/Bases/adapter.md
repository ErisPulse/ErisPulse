# `ErisPulse.Core.Bases.adapter` 模块

---

## 模块概述


ErisPulse 适配器基础模块

提供适配器和消息发送DSL的基类实现

> **提示**
> 1. 用于实现与不同平台的交互接口
> 2. 提供统一的消息发送DSL风格接口

---

## 函数列表


### `_has_rules(send_dsl: 'SendDSL')`

判断 SendDSL 实例是否附加了发送规则

- **send_dsl** (`SendDSL`): 实例
**返回值**: 是否存在任意已设置的规则

---


### `_copy_rules(rules: dict)`

复制规则字典（深拷贝可变值，如 hooks 列表）

用于 To/Using/Account 创建新实例时避免共享可变状态。
标量值（retry/timeout/defer 等）浅拷贝即可，
仅 hooks 列表需要创建新列表。

- **rules** (`原始规则字典`): **返回值**: 独立的规则字典副本

---


### `_wrap_to_task(result: Any)`

将任意返回值包装为 Task（用于重试路径的兼容处理）

- **result** (`原始方法返回值`): **返回值**: asyncio.Task

---


### `_wrap_send_method(method_name: str, original_method: Callable, send_dsl: 'SendDSL')`

为发送方法注入生命周期钩子

仅对返回 Task/Awaitable 的发送方法生效，链式修饰方法（返回 SendDSL）不受影响。
不改变原方法的返回值类型或执行行为，仅在 Task 上添加回调来触发钩子。

---


## 类列表


### `class SendDSL`

消息发送DSL基类

用于实现 Send.To(...).Func(...) 风格的链式调用接口

内置支持 At/AtAll/Reply 修饰器，适配器子类无需重复实现。
内置标准发送方法（Text/Image/Voice/Video/File），默认委托给 Raw_ob12，
适配器只需实现 Raw_ob12 即可获得全部标准发送能力，也可覆盖单个方法以提供平台特定逻辑。
通过 send_context 属性可显式获取发送上下文（目标类型、目标ID、发送账号）。
通过 _apply_modifiers() 方法可自动将修饰器状态合并到消息段。

> **提示**
> 1. 适配器必须实现 Raw_ob12（OneBot12 消息段 → 平台 API 的统一入口）
> 2. 标准发送方法（Text/Image/Voice/Video/File）已内置并委托给 Raw_ob12，无需子类重复实现
> 3. 子类可覆盖标准方法以提供平台特定逻辑，也可添加平台特有方法（如 Sticker）
> 4. At/AtAll/Reply 已内置实现，无需子类覆盖
> 5. 使用 self.send_context 获取发送上下文
> 6. 使用 self._apply_modifiers(message) 合并修饰器到消息段
> 7. 链式修饰方法（To/Using/At/Hook/Retry 等）返回 Self，使 IDE 能在链式调用中补全子类方法


#### 方法列表


##### `__init__(adapter: 'BaseAdapter', target_type: str | None = None, target_id: str | None = None, account_id: str | None = None, rules: dict | None = None)`

初始化DSL发送器

- **adapter** (`所属适配器实例`): - **target_type**: 目标类型(可选)
- **target_id** (`目标ID(可选)`): - **account_id**: 发送账号(可选)
- **rules** (`已附加的发送规则字典(可选，用于`): To/Using/Account 传播)

---


##### `__getattr__(name: str)`

动态属性访问处理，实现大小写不敏感调用

1. 如果找到匹配的方法（忽略大小写），返回该方法
2. 如果没找到，打印警告并抛出 AttributeError

- **name** (`属性名`): **返回值** (`匹配的方法或属性`): **异常**: `AttributeError` - 当属性不存在时抛出

---


##### `At(user_id: str)`

@指定用户（可链式多次调用）

- **user_id** (`要@的用户ID`): **返回值** (`SendDSL实例自身，支持链式调用`): 
**示例**:
```python
>>> await adapter.Send.To("group", "123").At("456").Text("Hello")
>>> await adapter.Send.To("group", "123").At("456").At("789").Text("@多人")
```

---


##### `AtAll()`

@全体成员

**返回值** (`SendDSL实例自身，支持链式调用`): 
**示例**:
```python
>>> await adapter.Send.To("group", "123").AtAll().Text("公告")
```

---


##### `Reply(message_id: str)`

回复指定消息

- **message_id** (`要回复的消息ID`): **返回值** (`SendDSL实例自身，支持链式调用`): 
**示例**:
```python
>>> await adapter.Send.To("group", "123").Reply("msg_456").Text("回复内容")
```

---


##### `_apply_modifiers(message)`

将 At/AtAll/Reply 修饰器应用到消息段

修饰器按以下顺序添加到消息段前：
1. mention_all (@全体)
2. mention (@用户，按调用顺序)
3. reply (回复)

- **message** (`OneBot12`): 消息段（dict 或 list[dict]）
**返回值** (`合并后的消息段列表`): 
**示例**:
```python
>>> segments = self._apply_modifiers([
>>>     {"type": "text", "data": {"text": "Hello"}}
>>> ])
```

---


##### `send_context()`

获取当前发送上下文（目标信息 + 发送账号）

**返回值** (`包含`): target_type, target_id, account_id 的字典

**示例**:
```python
>>> ctx = self.send_context
>>> # {"target_type": "group", "target_id": "123", "account_id": "bot1"}
>>> await self._adapter.call_api(
>>>     endpoint="/send_message",
>>>     message=segments,
>>>     **self.send_context,
>>>     **kwargs
>>> )
```

---


##### `Raw_ob12(message)`

发送 OneBot12 格式消息段（必须由适配器子类重写）

- **message** (`OneBot12`): 消息段列表或单个消息段
- **kwargs** (`其他参数`): **返回值**: asyncio.Task

---


##### `Text(text: str)`

发送文本消息

默认实现委托给 :meth:`Raw_ob12`，适配器可覆盖以提供平台特定逻辑。

- **text** (`文本内容`): **返回值** (`asyncio.Task，await`): 后返回标准响应格式

**示例**:
```python
>>> await adapter.Send.To("user", "123").Text("Hello")
```

---


##### `Image(file: str | bytes)`

发送图片消息

默认实现委托给 :meth:`Raw_ob12`，适配器可覆盖以提供平台特定逻辑。

- **file** (`图片文件（URL、路径或二进制数据）`): **返回值** (`asyncio.Task，await`): 后返回标准响应格式

**示例**:
```python
>>> await adapter.Send.To("user", "123").Image("https://example.com/img.png")
```

---


##### `Voice(file: str | bytes)`

发送语音消息

默认实现委托给 :meth:`Raw_ob12`（OneBot12 ``audio`` 段），
适配器可覆盖以提供平台特定逻辑。

- **file** (`语音文件（URL、路径或二进制数据）`): **返回值** (`asyncio.Task，await`): 后返回标准响应格式

**示例**:
```python
>>> await adapter.Send.To("user", "123").Voice("https://example.com/voice.mp3")
```

---


##### `Video(file: str | bytes)`

发送视频消息

默认实现委托给 :meth:`Raw_ob12`，适配器可覆盖以提供平台特定逻辑。

- **file** (`视频文件（URL、路径或二进制数据）`): **返回值** (`asyncio.Task，await`): 后返回标准响应格式

**示例**:
```python
>>> await adapter.Send.To("user", "123").Video("https://example.com/video.mp4")
```

---


##### `File(file: str | bytes, filename: str | None = None)`

发送文件

默认实现委托给 :meth:`Raw_ob12`，适配器可覆盖以提供平台特定逻辑。

- **file** (`文件（URL、路径或二进制数据）`): - **filename**: 文件名（可选，部分平台需要）
**返回值** (`asyncio.Task，await`): 后返回标准响应格式

**示例**:
```python
>>> await adapter.Send.To("user", "123").File("https://example.com/doc.pdf")
```

---


##### `To(target_type: str | None = None, target_id: str | int | None = None)`

设置消息目标

支持自动类型转换（遵循 :ref:`session-type` 规范）：
- 如果 ``target_type`` 是接收类型（如 ``"private"``），自动转换为对应的发送类型（``"user"``）
- 如果只提供 ``target_id``（字符串或数字）但未指定类型，默认推断为 ``"user"``
- 发送类型（``"user"``/``"group"``/``"channel"``/``"guild"``/``"thread"``）保持原样

- **target_type** (`目标类型（接收类型或发送类型均可，None`): 时自动推断）
- **target_id** (`目标ID（可选）`): **返回值** (`SendDSL`): 实例

**示例**:
```python
>>> # 标准用法（直接指定发送类型）
>>> adapter.Send.To("user", "123").Text("Hello")
>>> # 自动转换 private → user
>>> adapter.Send.To("private", "123").Text("Hello")
>>> # 简化形式（默认推断为 user）
>>> adapter.Send.To("123").Text("Hello")
```

---


##### `Using(account_id: str | int)`

设置发送账号

- **_account_id** (`发送账号`): **返回值** (`SendDSL实例`): 
**示例**:
```python
>>> adapter.Send.Using("bot1").To("123").Text("Hello")
>>> adapter.Send.To("123").Using("bot1").Text("Hello")  # 支持乱序
```

---


##### `Account(account_id: str | int)`

设置发送账号

- **_account_id** (`发送账号`): **返回值** (`SendDSL实例`): 
**示例**:
```python
>>> adapter.Send.Account("bot1").To("123").Text("Hello")
>>> adapter.Send.To("123").Account("bot1").Text("Hello")  # 支持乱序
```

---


##### `Hook(callback: Callable)`

附加发送成功后的回调钩子

仅当发送最终成功（包括重试成功）时执行，失败/超时/取消不触发。
可链式多次调用以添加多个 Hook，按添加顺序依次执行。

- **callback** (`回调函数，签名为`): ``callback(result)``，可为同步或协程函数
**返回值** (`SendDSL实例自身，支持链式调用`): 
**示例**:
```python
>>> await adapter.Send.To("user", "123").Hook(
...     lambda r: print("发送成功！")
... ).Text("你好")
>>>
>>> async def on_success(result):
...     print(f"消息ID: {result.get('message_id')}")
>>> await adapter.Send.To("user", "123").Hook(on_success).Text("异步回调")
```

---


##### `Retry(times: int = 1)`

设置失败自动重试次数

含首次发送共尝试 ``times + 1`` 次。重试触发条件：
- 发送抛出异常
- 发送超时（配合 :meth:`Timeout` 使用）
- 发送返回 ``status == "failed"`` 的响应

- **times** (`重试次数（不含首次发送），默认`): 1
**返回值** (`SendDSL实例自身，支持链式调用`): 
**示例**:
```python
>>> # 首次失败后重试2次，共3次尝试
>>> await adapter.Send.To("user", "123").Retry(2).Text("带重试")
```

---


##### `Timeout(seconds: float)`

设置单次发送超时时间

超时后取消当前尝试。若同时设置了 :meth:`Retry`，超时也会触发重试。

- **seconds** (`超时秒数`): **返回值** (`SendDSL实例自身，支持链式调用`): 
**示例**:
```python
>>> await adapter.Send.To("user", "123").Timeout(10).Text("带超时")
```

---


##### `Defer(seconds: float = 1.0)`

延迟发送

在实际发起发送前等待 ``seconds`` 秒。用于延迟提醒、定时消息等场景。
注意：此延迟为进程内定时，重启进程会丢失，不提供持久化。

- **seconds** (`延迟秒数，默认`): 1.0
**返回值** (`SendDSL实例自身，支持链式调用`): 
**示例**:
```python
>>> # 5秒后发送
>>> await adapter.Send.To("user", "123").Defer(5).Text("迟到消息")
```

---


##### `Priority(level: int = 0)`

设置消息优先级

优先级会被记录到 :class:`SendContext` 的 ``extra["priority"]``，
供业务层监控或自定义调度使用。

当 ``drop_if_busy=True`` 时，启用积压丢弃：若当前在途发送任务数
超过阈值（默认 64，可通过 :meth:`PriorityThreshold` 调整），
直接放弃本次发送（返回 ``stage="dropped"``），避免队列堆积。

- **level** (`优先级数值，越大越优先（默认`): 0）
- **drop_if_busy** (`是否在队列积压时丢弃本消息（默认`): False）
**返回值** (`SendDSL实例自身，支持链式调用`): 
**示例**:
```python
>>> # 低优先级消息，积压时自动丢弃
>>> await (adapter.Send.To("user", "123")
...       .Priority(-1, drop_if_busy=True)
...       .Text("可放弃的通知"))
```

---


##### `PriorityThreshold(threshold: int)`

设置优先级丢弃的积压阈值（全局生效）

配合 :meth:`Priority` 的 ``drop_if_busy=True`` 使用。

- **threshold** (`在途发送任务数阈值，超过则丢弃新消息`): **返回值**: SendDSL实例自身，支持链式调用

---


##### `OnProgress(callback: Callable)`

设置进度回调

在发送的各个阶段（pending/sending/retrying/success/failed/timeout/cancelled/dropped）
调用，传入实时更新的 :class:`SendContext`。可据此实现监控、日志、介入决策。

- **callback** (`回调函数，签名为`): ``callback(ctx: SendContext)``，
    可为同步或协程函数
**返回值** (`SendDSL实例自身，支持链式调用`): 
**示例**:
```python
>>> def on_progress(ctx):
...     print(f"阶段: {ctx.stage}, 尝试: {ctx.attempt + 1}/{ctx.max_attempts}")
...     if ctx.stage == "failed":
...         print(f"错误: {ctx.error!r}")
>>> task = (adapter.Send.To("user", "123")
...        .Retry(3).Timeout(10).OnProgress(on_progress).Text("监控"))
```

---


##### `OnError(callback: Callable)`

设置错误回调

当发送最终失败（重试耗尽仍失败、超时、取消）时调用一次，
传入最终的 :class:`SendContext`（``ctx.error`` 为异常对象，超时时为
:class:`asyncio.TimeoutError`）。

与 :meth:`OnProgress` 的区别：OnProgress 在每个阶段都触发，
OnError 仅在最终失败时触发一次。

- **callback** (`回调函数，签名为`): ``callback(ctx: SendContext)``，
    可为同步或协程函数
**返回值** (`SendDSL实例自身，支持链式调用`): 
**示例**:
```python
>>> async def on_error(ctx):
...     await admin_notify(f"发送失败: {ctx.target_id} {ctx.error!r}")
>>> await (adapter.Send.To("user", "123")
...       .Retry(2).OnError(on_error).Text("带错误处理"))
```

---


##### `Build()`

进入批量构建模式，返回 :class:`SendBuilder`

在构建模式下，发送方法（Text/Image 等）不再立即执行，而是累积为发送意图，
最后通过 ``send_all()`` 统一执行。规则统一作用于整批。

进入 Build 之前的 At/AtAll/Reply 修饰器和已设置的规则会继承到整批。

**返回值** (`:class:`SendBuilder``): 实例

**示例**:
```python
>>> # 构建多条消息，统一发送
>>> results = await (adapter.Send.To("user", "123")
...                  .Build()
...                  .Text("第一句")
...                  .Image("pic.jpg")
...                  .Text("第二句")
...                  .send_all())
>>> # results = [Text结果, Image结果, Text结果]
>>>
>>> # 串行执行 + 重试失败的
>>> await (adapter.Send.To("group", "456")
...        .Build()
...        .Sequential()
...        .Retry(2)
...        .Text("保证顺序1").Text("保证顺序2")
...        .send_all())
```

---


### `class RequestDSL`

请求操作 DSL 基类

用于对请求事件（好友请求、群邀请等）执行同意/拒绝操作。
采用与 Send 一致的工厂实例模式：``adapter.Request("req_id").accept()``

适配器只需在内部类中重写 ``accept`` / ``reject`` 即可。

> **提示**
> 1. 使用 ``adapter.Request(request_id).accept()`` 同意请求
> 2. 使用 ``adapter.Request(request_id).reject()`` 拒绝请求
> 3. 适配器重写 ``accept`` / ``reject`` 实现平台逻辑
> 4. 基类默认返回 ``retcode=10002``（不支持的操作）


#### 方法列表


##### `__init__(adapter: 'BaseAdapter', request_id: str | None = None, account_id: str | None = None)`

初始化请求操作 DSL

- **adapter** (`所属适配器实例`): - **request_id**: 请求ID
- **account_id** (`执行操作的`): Bot 账号

---


##### `__call__(request_id: str)`

设置请求ID，返回新的 RequestDSL 实例

使得 ``adapter.Request("req_id")`` 可以直接调用

- **request_id** (`请求ID`): **返回值** (`新的`): RequestDSL 实例

---


##### `Using(account_id: str | int)`

指定执行操作的 Bot 账号

- **account_id** (`账号标识`): **返回值** (`新的`): RequestDSL 实例

**示例**:
```python
>>> adapter.Request("req_123").Using("bot1").accept()
```

---


##### `accept()`

同意请求

- **kwargs** (`平台扩展参数（如`): comment 备注）
**返回值** (`asyncio.Task，await`): 后返回标准响应格式

**示例**:
```python
>>> result = await adapter.Request("req_123").accept()
>>> result = await adapter.Request("req_123").accept(comment="欢迎")
```

---


##### `reject()`

拒绝请求

- **kwargs** (`平台扩展参数（如`): comment 拒绝理由）
**返回值** (`asyncio.Task，await`): 后返回标准响应格式

**示例**:
```python
>>> result = await adapter.Request("req_123").reject()
>>> result = await adapter.Request("req_123").reject(comment="暂不添加")
```

---


##### `async _do_accept()`

同意请求的具体实现（适配器子类重写）

- **kwargs** (`平台扩展参数`): **返回值**: 标准响应格式

---


##### `async _do_reject()`

拒绝请求的具体实现（适配器子类重写）

- **kwargs** (`平台扩展参数`): **返回值**: 标准响应格式

---


##### `_not_implemented_response(action: str)`

生成「未实现」的标准错误响应

- **action** (`操作名称（accept/reject）`): **返回值**: 标准错误响应字典

---


##### `_create_task(coro)`

创建 asyncio.Task

---


##### `request_context()`

获取当前请求操作上下文

**返回值** (`包含`): request_id, account_id 的字典

---


### `class BaseAdapter(ABC)`

适配器基类

提供与外部平台交互的标准接口，子类必须实现必要方法

> **提示**
> 1. 必须实现call_api, start和shutdown方法
> 2. Send 子类只需实现 Raw_ob12，即可获得全部标准发送方法（Text/Image/Voice/Video/File）
> 3. 可以自定义Request类实现平台特定的请求操作逻辑
> 4. 通过on装饰器注册事件处理器
> 5. 支持OneBot12协议的事件处理
> 6. 通过 ConfigClass / AccountConfigClass 声明配置类，框架自动管理配置
> 7. 通过 self.cfg / self.accounts 访问类型安全的配置对象（实时读取）
> 8. 通过 self.emit_meta() 发送 meta 事件
> 9. 通过 self.make_response() / self.make_error() 构造标准化响应
> 10. 通过 I18nClass 声明翻译键集合，框架自动注册到 i18n 系统


#### 嵌套类


##### `class Request(RequestDSL)`

请求操作 DSL 实现

适配器子类重写 ``accept`` / ``reject`` 以实现平台特定逻辑。

> **提示**
> 1. 默认实现返回 ``retcode=10002``（不支持的操作）
> 2. 适配器应重写 ``accept`` / ``reject`` 方法
> 3. 通过 ``self._adapter.call_api()`` 调用平台 API
> 4. 通过 ``self._request_id`` 获取请求标识
> 5. 通过 ``self._account_id`` 获取 Bot 账号


##### `class Send(SendDSL)`

消息发送DSL实现

> **提示**
> 1. 必须重写 Raw_ob12 方法（OneBot12 消息段 → 平台 API）
> 2. 标准方法（Text/Image/Voice/Video/File）已从 SendDSL 基类继承，默认委托 Raw_ob12
> 3. 如需平台特定逻辑，可覆盖单个标准方法（如 Text）
> 4. 可添加平台特有的发送方法（如 Sticker）


###### 方法列表


####### `Example(text: str)`

示例消息发送方法

- **text** (`文本内容`): **返回值** (`异步任务`): 
**示例**:
```python
>>> await adapter.Send.To("123").Example("Hello")
```

---


####### `Raw_ob12(message)`

发送 OneBot12 格式消息段（必须由适配器子类重写）

此方法是反向转换（OneBot12 → 平台）的统一入口，适配器必须重写此方法。
未重写时，基类默认实现会记录错误日志并返回标准错误响应。

推荐使用框架提供的辅助方法：
- self._apply_modifiers(message) - 合并 At/AtAll/Reply 修饰器到消息段
- self.send_context - 获取发送上下文 (target_type, target_id, account_id)

- **message** (`OneBot12`): 格式的消息段数组或单个消息段
    [
        {"type": "text", "data": {"text": "Hello"}},
        {"type": "image", "data": {"file": "https://..."}},
    ]
- **kwargs** (`其他参数`): **返回值** (`asyncio.Task，await`): 后返回标准响应格式

**示例**:
```python
>>> # 用户调用
>>> await adapter.Send.To("user", "123").Raw_ob12([
>>>     {"type": "text", "data": {"text": "Hello"}},
>>>     {"type": "image", "data": {"file": "https://..."}}
>>> ])
>>>
>>> # 适配器子类重写示例（推荐：使用框架辅助方法）
>>> def Raw_ob12(self, message, **kwargs):
>>>     async def _do_send():
>>>         segments = self._apply_modifiers(message)
>>>         return await self._adapter.call_api(
>>>             endpoint="/send_message",
>>>             message=segments,
>>>             **self.send_context,
>>>             **kwargs
>>>         )
>>>     return asyncio.create_task(_do_send())
```

---


#### 方法列表


##### `_load_accounts()`

> **内部方法**
加载账户配置（可被子类覆写）

子类可覆写此方法实现自定义账户加载逻辑（如全局配置合并、旧格式迁移等）。
返回 None 时使用默认配置存储读取逻辑。

**返回值** (`账户配置字典，或`): None 表示使用默认逻辑

---


##### `_load_config()`

> **内部方法**
加载适配器配置（可被子类覆写）

子类可覆写此方法实现自定义配置加载逻辑（如旧格式迁移等）。
返回 None 时使用默认配置存储读取逻辑。

**返回值** (`配置实例，或`): None 表示使用默认逻辑

---


##### `async call_api(endpoint: str)`

调用平台API的抽象方法

- **endpoint** (`API端点`): - **params**: API参数
**返回值** (`API调用结果`): **异常**: `NotImplementedError` - 必须由子类实现

---


##### `async start()`

启动适配器的抽象方法

**异常**: `NotImplementedError` - 必须由子类实现

---


##### `async shutdown()`

关闭适配器的抽象方法

**异常**: `NotImplementedError` - 必须由子类实现

---


##### `cfg()`

类型安全的配置对象（实时读取）

每次访问都从配置存储读取最新值，确保用户修改配置后立即生效。
返回的 dataclass 实例是只读快照，修改它不会回写存储。

**返回值** (`AdapterConfig`): / BaseConfig 实例
**异常**: `AttributeError` - 未声明 ConfigClass 时抛出

> **提示**
> 推荐使用 ``self.cfg`` 而非 ``self.config``，
> 后者已弃用且可能被子类属性覆盖产生冲突。

---


##### `cfg(value)`

设置配置实例，同时同步写入配置存储（保证实时性）

---


##### `config()`

``self.cfg`` 的兼容别名

功能与 ``self.cfg`` 完全一致，推荐新代码使用 ``self.cfg``。

---


##### `accounts()`

类型安全的账户配置字典（实时读取）

每次访问都从配置存储读取最新值，确保用户修改账户配置后立即生效。

**返回值** (`账户配置字典`): {name: config_instance}
**异常**: `AttributeError` - 未声明 AccountConfigClass 时抛出

---


##### `accounts(value)`

设置账户配置字典，同时同步写入配置存储

---


##### `enabled_accounts()`

仅返回 enabled=True 的账户

**返回值**: 启用的账户配置字典

---


##### `platform()`

获取平台名称

**返回值**: 平台名称字符串

---


##### `_get_config_key()`

配置键名（默认用类名，可被子类覆写）

**返回值**: 配置键名字符串

---


##### `_get_logger()`

获取 logger，兼容 sdk 未注入的场景

---


##### `_ensure_config_exists()`

确保全局配置模板存在，不存在则生成默认配置

> **内部方法**
会先行调用 _ensure_i18n_registered() 注册声明的翻译键，
确保配置描述引用的 i18n 键在生成模板时已可用。

---


##### `_ensure_i18n_registered()`

注册 I18nClass 中声明的翻译键到 i18n 系统

使用适配器配置键名（默认为类名）作为键名前缀和 domain，便于统一卸载。
方法是幂等的，多次调用不会产生副作用（重复注册会覆盖旧值）。

> **内部方法**
由 __init__() 在生成配置之前隐式调用。

---


##### `_ensure_accounts_exist()`

确保多账户配置模板存在，不存在则生成默认账户配置

> **内部方法**

---


##### `_resolve_account(account_id: str | None = None)`

解析目标账户

- account_id 为 None → 返回第一个启用的账户
- account_id 匹配账户名 → 返回该账户
- account_id 匹配 bot_id 等字段 → 返回该账户
- 未找到 → 抛出 ValueError

匹配字段优先级：账户名 > dataclass 中名为 bot_id 的字段 > 任意 str 类型字段

- **account_id** (`账户标识（账户名、bot_id`): 等）
**返回值** (`(账户名,`): 账户配置实例) 元组
**异常**: `ValueError` - 未找到可用账户时抛出

---


##### `async emit_meta(detail_type: str, bot_id: str)`

发送 meta 事件的便捷方法

- **detail_type** (`"connect"`): | "disconnect" | "heartbeat"
- **bot_id** (`Bot`): 用户 ID
- **extra_info** (`扩展字段（user_name,`): nickname, avatar 等）

---


##### `make_response()`

构造标准化响应

- **status** (`状态码（"ok"`): | "failed"）
- **retcode** (`返回码`): - **data**: 响应数据
- **message_id** (`消息`): ID
- **message** (`响应消息`): - **raw**: 原始平台响应
**返回值**: 标准响应字典

---


##### `make_error(retcode: int = 34000, message: str = '', raw = None)`

构造错误响应

- **retcode** (`错误码`): - **message**: 错误消息
- **raw** (`原始平台响应`): **返回值**: 标准错误响应字典

---


##### `on_config_update(old_config, new_config)`

配置变更回调（可选实现）

子类可覆写此方法以响应配置热更新。默认实现为空操作。

- **old_config** (`变更前的配置实例`): - **new_config**: 变更后的配置实例

---


##### `send(target_type: str, target_id: str, message: Any)`

发送消息的便捷方法，返回一个 asyncio Task

- **target_type** (`目标类型`): - **target_id**: 目标ID
- **message** (`消息内容`): - **kwargs**: 其他参数
    - method: 发送方法名(默认为"Text")
**返回值** (`asyncio.Task`): 对象，用户可以自主决定是否等待

**异常**: `AttributeError` - 当发送方法不存在时抛出

**示例**:
```python
>>> task = adapter.send("user", "123", "Hello")
>>> # 用户可以选择等待: result = await task
>>> # 或者不等待让其在后台执行
>>> await adapter.send("group", "456", "Hello", method="Markdown")  # 直接等待
```

---

