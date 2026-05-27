# `ErisPulse.Core.Bases.adapter` 模块

---

## 模块概述


ErisPulse 适配器基础模块

提供适配器和消息发送DSL的基类实现

> **提示**
> 1. 用于实现与不同平台的交互接口
> 2. 提供统一的消息发送DSL风格接口

---

## 类列表


### `class SendDSL`

消息发送DSL基类

用于实现 Send.To(...).Func(...) 风格的链式调用接口

内置支持 At/AtAll/Reply 修饰器，适配器子类无需重复实现。
通过 send_context 属性可显式获取发送上下文（目标类型、目标ID、发送账号）。
通过 _apply_modifiers() 方法可自动将修饰器状态合并到消息段。

> **提示**
> 1. 子类应实现具体的消息发送方法(如Text, Image等)
> 2. 通过__getattr__实现动态方法调用
> 3. At/AtAll/Reply 已内置实现，无需子类覆盖
> 4. 使用 self.send_context 获取发送上下文
> 5. 使用 self._apply_modifiers(message) 合并修饰器到消息段


#### 方法列表


##### `__init__(adapter: 'BaseAdapter', target_type: str | None = None, target_id: str | None = None, account_id: str | None = None)`

初始化DSL发送器

:param adapter: 所属适配器实例
:param target_type: 目标类型(可选)
:param target_id: 目标ID(可选)
:param account_id: 发送账号(可选)

---


##### `__getattr__(name: str)`

动态属性访问处理，实现大小写不敏感调用

1. 如果找到匹配的方法（忽略大小写），返回该方法
2. 如果没找到，打印警告并抛出 AttributeError

:param name: 属性名
:return: 匹配的方法或属性
**异常**: `AttributeError` - 当属性不存在时抛出

---


##### `At(user_id: str)`

@指定用户（可链式多次调用）

:param user_id: 要@的用户ID
:return: SendDSL实例自身，支持链式调用

**示例**:
```python
>>> await adapter.Send.To("group", "123").At("456").Text("Hello")
>>> await adapter.Send.To("group", "123").At("456").At("789").Text("@多人")
```

---


##### `AtAll()`

@全体成员

:return: SendDSL实例自身，支持链式调用

**示例**:
```python
>>> await adapter.Send.To("group", "123").AtAll().Text("公告")
```

---


##### `Reply(message_id: str)`

回复指定消息

:param message_id: 要回复的消息ID
:return: SendDSL实例自身，支持链式调用

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

:param message: OneBot12 消息段（dict 或 list[dict]）
:return: 合并后的消息段列表

**示例**:
```python
>>> segments = self._apply_modifiers([
>>>     {"type": "text", "data": {"text": "Hello"}}
>>> ])
```

---


##### `send_context()`

获取当前发送上下文（目标信息 + 发送账号）

:return: 包含 target_type, target_id, account_id 的字典

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

:param message: OneBot12 消息段列表或单个消息段
:param kwargs: 其他参数
:return: asyncio.Task

---


##### `To(target_type: str = None, target_id: str | int = None)`

设置消息目标

支持自动类型转换：
- 当 target_type 为 "private" 时，自动转换为 "user"
- 当只提供 target_id（字符串或数字）时，默认推断为 "user"

:param target_type: 目标类型(可选)
:param target_id: 目标ID(可选)
:return: SendDSL实例

**示例**:
```python
>>> # 标准用法
>>> adapter.Send.To("user", "123").Text("Hello")
>>> # 自动转换 private → user
>>> adapter.Send.To("private", "123").Text("Hello")
>>> # 简化形式（默认推断为 user）
>>> adapter.Send.To("123").Text("Hello")
```

---


##### `Using(account_id: str | int)`

设置发送账号

:param _account_id: 发送账号
:return: SendDSL实例

**示例**:
```python
>>> adapter.Send.Using("bot1").To("123").Text("Hello")
>>> adapter.Send.To("123").Using("bot1").Text("Hello")  # 支持乱序
```

---


##### `Account(account_id: str | int)`

设置发送账号

:param _account_id: 发送账号
:return: SendDSL实例

**示例**:
```python
>>> adapter.Send.Account("bot1").To("123").Text("Hello")
>>> adapter.Send.To("123").Account("bot1").Text("Hello")  # 支持乱序
```

---


### `class BaseAdapter(ABC)`

适配器基类

提供与外部平台交互的标准接口，子类必须实现必要方法

> **提示**
> 1. 必须实现call_api, start和shutdown方法
> 2. 可以自定义Send类实现平台特定的消息发送逻辑
> 3. 通过on装饰器注册事件处理器
> 4. 支持OneBot12协议的事件处理


#### 嵌套类


##### `class Send(SendDSL)`

消息发送DSL实现

> **提示**
> 1. 子类可以重写Text方法提供平台特定实现
> 2. 可以添加新的消息类型(如Image, Voice等)


###### 方法列表


####### `Example(text: str)`

示例消息发送方法

:param text: 文本内容
:return: 异步任务

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

:param message: OneBot12 格式的消息段数组或单个消息段
    [
        {"type": "text", "data": {"text": "Hello"}},
        {"type": "image", "data": {"file": "https://..."}},
    ]
:param kwargs: 其他参数
:return: asyncio.Task，await 后返回标准响应格式

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


##### `async async call_api(endpoint: str)`

调用平台API的抽象方法

:param endpoint: API端点
:param params: API参数
:return: API调用结果
**异常**: `NotImplementedError` - 必须由子类实现

---


##### `async async start()`

启动适配器的抽象方法

**异常**: `NotImplementedError` - 必须由子类实现

---


##### `async async shutdown()`

关闭适配器的抽象方法

**异常**: `NotImplementedError` - 必须由子类实现

---


##### `send(target_type: str, target_id: str, message: Any)`

发送消息的便捷方法，返回一个 asyncio Task

:param target_type: 目标类型
:param target_id: 目标ID
:param message: 消息内容
:param kwargs: 其他参数
    - method: 发送方法名(默认为"Text")
:return: asyncio.Task 对象，用户可以自主决定是否等待

**异常**: `AttributeError` - 当发送方法不存在时抛出

**示例**:
```python
>>> task = adapter.send("user", "123", "Hello")
>>> # 用户可以选择等待: result = await task
>>> # 或者不等待让其在后台执行
>>> await adapter.send("group", "456", "Hello", method="Markdown")  # 直接等待
```

---

