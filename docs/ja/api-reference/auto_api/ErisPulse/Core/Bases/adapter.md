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

:param adapter: 所属适配器实例
:param request_id: 请求ID
:param account_id: 执行操作的 Bot 账号

---


##### `__call__(request_id: str)`

设置请求ID，返回新的 RequestDSL 实例

使得 ``adapter.Request("req_id")`` 可以直接调用

:param request_id: 请求ID
:return: 新的 RequestDSL 实例

---


##### `Using(account_id: str | int)`

指定执行操作的 Bot 账号

:param account_id: 账号标识
:return: 新的 RequestDSL 实例

**示例**:
```python
>>> adapter.Request("req_123").Using("bot1").accept()
```

---


##### `accept()`

同意请求

:param kwargs: 平台扩展参数（如 comment 备注）
:return: asyncio.Task，await 后返回标准响应格式

**示例**:
```python
>>> result = await adapter.Request("req_123").accept()
>>> result = await adapter.Request("req_123").accept(comment="欢迎")
```

---


##### `reject()`

拒绝请求

:param kwargs: 平台扩展参数（如 comment 拒绝理由）
:return: asyncio.Task，await 后返回标准响应格式

**示例**:
```python
>>> result = await adapter.Request("req_123").reject()
>>> result = await adapter.Request("req_123").reject(comment="暂不添加")
```

---


##### `async async _do_accept()`

同意请求的具体实现（适配器子类重写）

:param kwargs: 平台扩展参数
:return: 标准响应格式

---


##### `async async _do_reject()`

拒绝请求的具体实现（适配器子类重写）

:param kwargs: 平台扩展参数
:return: 标准响应格式

---


##### `_not_implemented_response(action: str)`

生成「未实现」的标准错误响应

:param action: 操作名称（accept/reject）
:return: 标准错误响应字典

---


##### `_create_task(coro)`

创建 asyncio.Task

---


##### `request_context()`

获取当前请求操作上下文

:return: 包含 request_id, account_id 的字典

---


### `class BaseAdapter(ABC)`

适配器基类

提供与外部平台交互的标准接口，子类必须实现必要方法

> **提示**
> 1. 必须实现call_api, start和shutdown方法
> 2. 可以自定义Send类实现平台特定的消息发送逻辑
> 3. 可以自定义Request类实现平台特定的请求操作逻辑
> 4. 通过on装饰器注册事件处理器
> 5. 支持OneBot12协议的事件处理
> 6. 通过 ConfigClass / AccountConfigClass 声明配置类，框架自动管理配置
> 7. 通过 self.config / self.accounts 访问类型安全的配置对象
> 8. 通过 self.emit_meta() 发送 meta 事件
> 9. 通过 self.make_response() / self.make_error() 构造标准化响应


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


##### `config()`

类型安全的配置对象

:return: AdapterConfig 实例
**异常**: `AttributeError` - 未声明 ConfigClass 时抛出

---


##### `accounts()`

类型安全的账户配置字典 {name: config_instance}

:return: 账户配置字典
**异常**: `AttributeError` - 未声明 AccountConfigClass 时抛出

---


##### `enabled_accounts()`

仅返回 enabled=True 的账户

:return: 启用的账户配置字典

---


##### `platform()`

获取平台名称

:return: 平台名称字符串

---


##### `_get_config_key()`

配置键名（默认用类名，可被子类覆写）

:return: 配置键名字符串

---


##### `_get_logger()`

获取 logger，兼容 sdk 未注入的场景

---


##### `_load_config()`

从 TOML 加载全局配置

1. 读取 {ConfigKey} 键
2. 如果不存在，用 dataclass 默认值生成模板并写入
3. 用 dict_to_dataclass() 转为类型安全的实例

:return: AdapterConfig 实例

---


##### `_load_accounts()`

从 TOML 加载多账户配置

1. 读取 {ConfigKey}.accounts 键
2. 如果不存在，创建包含一个 default 账户的模板
3. 对每个账户做 validate_config() 校验
4. 跳过校验失败的账户并记录错误

:return: 账户配置字典 {name: config_instance}

---


##### `_resolve_account(account_id: str | None = None)`

解析目标账户

- account_id 为 None → 返回第一个启用的账户
- account_id 匹配账户名 → 返回该账户
- account_id 匹配 bot_id 等字段 → 返回该账户
- 未找到 → 抛出 ValueError

匹配字段优先级：账户名 > dataclass 中名为 bot_id 的字段 > 任意 str 类型字段

:param account_id: 账户标识（账户名、bot_id 等）
:return: (账户名, 账户配置实例) 元组
**异常**: `ValueError` - 未找到可用账户时抛出

---


##### `async async emit_meta(detail_type: str, bot_id: str)`

发送 meta 事件的便捷方法

:param detail_type: "connect" | "disconnect" | "heartbeat"
:param bot_id: Bot 用户 ID
:param extra_info: 扩展字段（user_name, nickname, avatar 等）

---


##### `make_response()`

构造标准化响应

:param status: 状态码（"ok" | "failed"）
:param retcode: 返回码
:param data: 响应数据
:param message_id: 消息 ID
:param message: 响应消息
:param raw: 原始平台响应
:return: 标准响应字典

---


##### `make_error(retcode: int = 34000, message: str = '', raw = None)`

构造错误响应

:param retcode: 错误码
:param message: 错误消息
:param raw: 原始平台响应
:return: 标准错误响应字典

---


##### `on_config_update(old_config, new_config)`

配置变更回调（可选实现）

子类可覆写此方法以响应配置热更新。

:param old_config: 变更前的配置实例
:param new_config: 变更后的配置实例

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

