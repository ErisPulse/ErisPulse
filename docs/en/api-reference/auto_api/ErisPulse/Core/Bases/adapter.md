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

> **提示**
> 1. 子类应实现具体的消息发送方法(如Text, Image等)
> 2. 通过__getattr__实现动态方法调用


#### 方法列表


##### `__init__(adapter: 'BaseAdapter', target_type: Optional[str] = None, target_id: Optional[str] = None, account_id: Optional[str] = None)`

初始化DSL发送器

:param adapter: 所属适配器实例
:param target_type: 目标类型(可选)
:param target_id: 目标ID(可选)
:param _account_id: 发送账号(可选)

---


##### `__getattr__(name: str)`

动态属性访问处理，实现大小写不敏感调用

1. 如果找到匹配的方法（忽略大小写），返回该方法
2. 如果没找到，打印警告并抛出 AttributeError

:param name: 属性名
:return: 匹配的方法或属性
**异常**: `AttributeError` - 当属性不存在时抛出

---


##### `_unimplemented_modifier(method_name: str)`

处理未实现的修饰方法，记录警告并返回自身以保持链式调用

---


##### `Raw_ob12(message)`

发送 OneBot12 格式消息段（必须由适配器子类重写）

:param message: OneBot12 消息段列表或单个消息段
:param kwargs: 其他参数
:return: asyncio.Task

---


##### `To(target_type: str = None, target_id: Union[str, int] = None)`

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


##### `Using(account_id: Union[str, int])`

设置发送账号

:param _account_id: 发送账号
:return: SendDSL实例

**示例**:
```python
>>> adapter.Send.Using("bot1").To("123").Text("Hello")
>>> adapter.Send.To("123").Using("bot1").Text("Hello")  # 支持乱序
```

---


##### `Account(account_id: Union[str, int])`

设置发送账号

:param _account_id: 发送账号
:return: SendDSL实例

**示例**:
```python
>>> adapter.Send.Account("bot1").To("123").Text("Hello")
>>> adapter.Send.To("123").Account("bot1").Text("Hello")  # 支持乱序
```

---


### `class BaseAdapter`

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

>>> # 适配器子类重写示例（必须）
>>> def Raw_ob12(self, message, **kwargs):
>>>     return asyncio.create_task(
>>>         self._adapter.call_api(
>>>             "send_message",
>>>             message=message,
>>>             target_type=self._target_type,
>>>             target_id=self._target_id,
>>>             account_id=self._account_id,
>>>             **kwargs
>>>         )
>>>     )
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

