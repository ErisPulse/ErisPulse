# `ErisPulse.Core.Event.wrapper` 模块

---

## 模块概述


ErisPulse 事件包装类

提供便捷的事件访问方法

> **提示**
> 1. 继承自dict，完全兼容字典访问
> 2. 提供便捷方法简化事件处理
> 3. 支持点式访问 event.platform
> 4. 支持适配器通过 register_event_mixin / register_event_method 注册平台专有方法
> 5. 建议在处理器参数中使用类型注解以获得 IDE 自动补全: async def handler(event: Event)

---

## 函数列表


### `register_event_mixin(platform: str, mixin_cls: type)`

注册一个类的所有公开方法到指定平台

适配器可以创建一个 Mixin 类集中定义平台专有方法，
然后通过此函数一次性注册。

注册的方法会通过 Event.__getattribute__ 优先于内置方法生效，
因此可以覆写 confirm / choose / collect / wait_reply 等内置交互式方法。

:param platform: 平台名称（需与适配器注册名一致）
:param mixin_cls: 包含平台方法的类
:return: 成功注册的方法数量

**示例**:
```python
>>> class EmailEventMixin:
...     def get_subject(self):
...         return self.get("email_raw", {}).get("subject", "")
...     def get_from(self):
...         return self.get("email_raw", {}).get("from", "")
>>> register_event_mixin("email", EmailEventMixin)
2
```

---


### `register_event_method(platform: str)`

装饰器：注册单个方法到指定平台

适合少量方法或动态注册的场景。

注册的方法会通过 Event.__getattribute__ 优先于内置方法生效，
因此可以覆写 confirm / choose / collect / wait_reply 等内置交互式方法。

:param platform: 平台名称（需与适配器注册名一致）

**示例**:
```python
>>> @register_event_method("email")
... def get_subject(self):
...     return self.get("email_raw", {}).get("subject", "")
```

---


### `unregister_event_method(platform: str, name: str)`

注销指定平台的单个扩展方法

:param platform: 平台名称
:param name: 方法名
:return: 是否成功注销

---


### `unregister_platform_event_methods(platform: str)`

注销指定平台的全部扩展方法

适配器关闭时应调用此方法清理注册的方法。

:param platform: 平台名称
:return: 被注销的方法数量

---


### `get_platform_event_methods(platform: str)`

查询指定平台已注册的扩展方法名列表

:param platform: 平台名称
:return: 方法名列表

---


### `async async _builtin_wait_reply(event: 'Event', prompt: str | None = None, timeout: float = DEFAULT_WAIT_TIMEOUT_SECS, callback: Callable[[dict[str, Any]], Awaitable[Any]] = None, validator: Callable[[dict[str, Any]], bool] = None, method: str = DEFAULT_SEND_METHOD)`

内置 wait_reply 实现

供覆写函数调用以复用内置等待逻辑。

---


### `async async _builtin_confirm(event: 'Event', prompt: str | None = None, timeout: float = DEFAULT_WAIT_TIMEOUT_SECS, yes_words: set[str] | frozenset[str] = None, no_words: set[str] | frozenset[str] = None, method: str = DEFAULT_SEND_METHOD)`

内置 confirm 实现

供覆写函数调用以复用内置确认逻辑。

---


### `async async _builtin_choose(event: 'Event', prompt: str, options: list[str], timeout: float = DEFAULT_WAIT_TIMEOUT_SECS, method: str = DEFAULT_SEND_METHOD)`

内置 choose 实现

供覆写函数调用以复用内置选择逻辑。
文本类方法 (Text/Markdown/Html) 会将选项拼接到 prompt 后一条消息发送；
富媒体类方法会先发富媒体内容，再单独发 Text 选项列表。

---


### `async async _builtin_collect(event: 'Event', fields: list[dict[str, Any]], timeout_per_field: float = 60.0)`

内置 collect 实现

供覆写函数调用以复用内置收集逻辑。
每个 field 支持 `method` 键来指定发送方法。

---


## 类列表


### `class EventData(TypedDict)`

OneBot12 标准事件数据结构

> **提示**
> 所有字段均为可选（total=False），实际字段取决于事件类型。
> 详见 [适配器标准化转换规范](../../standards/event-conversion.md)

:ivar id: str 事件唯一标识符
:ivar time: int Unix时间戳（秒级）
:ivar type: str 事件类型（message/notice/request/meta）
:ivar detail_type: str 事件详细类型（详见会话类型标准）
:ivar sub_type: str 子类型
:ivar platform: str 平台名称
:ivar self: dict 机器人信息（含 platform, user_id）
:ivar message_id: str 消息ID
:ivar message: list 消息段数组
:ivar alt_message: str 纯文本消息
:ivar user_id: str 用户ID
:ivar user_nickname: str 用户昵称
:ivar group_id: str 群组ID
:ivar guild_id: str 频道ID
:ivar channel_id: str 子频道ID
:ivar thread_id: str 主题ID
:ivar operator_id: str 操作者ID
:ivar comment: str 请求附言
:ivar request_id: str 请求标识符


### `class Event(dict)`

事件包装类

提供便捷的事件访问方法

> **提示**
> 所有方法都是可选的，不影响原有字典访问方式


#### 方法列表


##### `__init__(event_data: dict[str, Any])`

初始化事件包装器

:param event_data: 原始事件数据

---


##### `get_id()`

获取事件ID

:return: 事件ID

---


##### `get_time()`

获取事件时间戳

:return: Unix时间戳（秒级）

---


##### `get_type()`

获取事件类型

:return: 事件类型（message/notice/request/meta等）

---


##### `get_detail_type()`

获取事件详细类型

:return: 事件详细类型（private/group/friend等）

---


##### `get_platform()`

获取平台名称

:return: 平台名称

---


##### `get_self_platform()`

获取机器人平台

:return: 机器人平台名称

---


##### `get_self_user_id()`

获取机器人用户ID

:return: 机器人用户ID

---


##### `get_self_account_id()`

获取机器人账户标识（多Bot模式）

优先返回 account_id（ErisPulse扩展），若不存在则回退到 user_id（OB12标准）

:return: 机器人账户标识，单Bot模式下返回空字符串

---


##### `get_self_info()`

获取机器人完整信息

:return: 机器人信息字典

---


##### `get_message()`

获取消息段数组

:return: 消息段数组

---


##### `get_alt_message()`

获取消息备用文本

:return: 消息备用文本

---


##### `get_text()`

获取纯文本内容

:return: 纯文本内容

---


##### `get_message_text()`

获取纯文本内容（别名）

:return: 纯文本内容

---


##### `has_mention()`

是否包含@消息

:return: 是否包含@消息

---


##### `get_mentions()`

获取所有被@的用户ID列表

:return: 被@的用户ID列表

---


##### `get_user_id()`

获取发送者ID

:return: 发送者用户ID

---


##### `get_user_nickname()`

获取发送者昵称

:return: 发送者昵称

---


##### `get_group_id()`

获取群组ID

:return: 群组ID（群聊消息）

---


##### `get_channel_id()`

获取频道ID

:return: 频道ID（频道消息）

---


##### `get_guild_id()`

获取服务器ID

:return: 服务器ID（服务器消息）

---


##### `get_thread_id()`

获取话题/子频道ID

:return: 话题ID（话题消息）

---


##### `get_sender()`

获取发送者信息字典

:return: 发送者信息字典

---


##### `is_message()`

是否为消息事件

:return: 是否为消息事件

---


##### `is_private_message()`

是否为私聊消息

:return: 是否为私聊消息

---


##### `is_group_message()`

是否为群聊消息

:return: 是否为群聊消息

---


##### `is_at_message()`

是否为@消息

:return: 是否为@消息

---


##### `get_operator_id()`

获取操作者ID

:return: 操作者ID

---


##### `get_operator_nickname()`

获取操作者昵称

:return: 操作者昵称

---


##### `is_notice()`

是否为通知事件

:return: 是否为通知事件

---


##### `is_group_member_increase()`

群成员增加

:return: 是否为群成员增加事件

---


##### `is_group_member_decrease()`

群成员减少

:return: 是否为群成员减少事件

---


##### `is_friend_add()`

好友添加

:return: 是否为好友添加事件

---


##### `is_friend_delete()`

好友删除

:return: 是否为好友删除事件

---


##### `get_comment()`

获取请求附言

:return: 请求附言

---


##### `get_request_id()`

获取请求ID

用于标识可操作的请求，配合 approve()/reject() 使用。

:return: 请求ID，不存在时返回空字符串

---


##### `async async approve(comment: str | None = None)`

同意当前请求事件

通过适配器的 Request DSL 执行同意操作。
仅对请求类型事件（type == "request"）有效。

:param comment: 附带备注信息（可选，部分平台支持）
:return: 标准响应格式

**异常**: `ValueError` - 当事件不是请求类型或缺少必要字段时

**示例**:
```python
>>> @request.on_friend_request()
... async def handle_friend_request(event):
...     await event.approve()
...     # 带备注
...     await event.approve(comment="欢迎添加好友")
```

---


##### `async async reject(comment: str | None = None)`

拒绝当前请求事件

通过适配器的 Request DSL 执行拒绝操作。
仅对请求类型事件（type == "request"）有效。

:param comment: 附带备注信息（可选，部分平台支持）
:return: 标准响应格式

**异常**: `ValueError` - 当事件不是请求类型或缺少必要字段时

**示例**:
```python
>>> @request.on_group_request()
... async def handle_group_request(event):
...     await event.reject()
```

---


##### `async async _handle_request_action(action: str, comment: str | None = None)`

执行请求操作的内部方法

:param action: 操作类型 ("accept" / "reject")
:param comment: 附带备注
:return: 标准响应格式
**异常**: `ValueError` - 当缺少必要字段时

---


##### `is_request()`

是否为请求事件

:return: 是否为请求事件

---


##### `is_friend_request()`

是否为好友请求

:return: 是否为好友请求

---


##### `is_group_request()`

是否为群组请求

:return: 是否为群组请求

---


##### `_get_adapter_and_target()`

获取适配器实例和目标信息

使用会话类型管理模块自动处理类型转换和ID获取

:return: (适配器实例, 发送目标类型, 目标ID, 账户ID)

---


##### `async async reply(content: str, method: str = DEFAULT_SEND_METHOD, at_users: list[str] = None, reply_to: str | None = None, at_all: bool = False)`

通用回复方法

基于适配器的Text方法，但可以通过method参数指定其他发送方法

:param content: 发送内容（文本、URL等，取决于method参数）
:param method: 适配器发送方法，默认为"Text"
               可选值: "Text", "Image", "Voice", "Video", "File" 等
:param at_users: @用户列表（可选），如 ["user1", "user2"]
:param reply_to: 回复消息ID（可选）
:param at_all: 是否@全体成员（可选），默认为 False
:param kwargs: 额外参数，例如Mention方法的user_id
:return: 适配器发送方法的返回值

**示例**:
```python
>>> # 简单回复
>>> await event.reply("你好")
>>>
>>> # 发送图片
>>> await event.reply("http://example.com/image.jpg", method="Image")
>>>
>>> # @用户
>>> await event.reply("你好", at_users=["user123"])
>>>
>>> # 回复消息
>>> await event.reply("回复内容", reply_to="msg_id")
>>>
>>> # @全体成员
>>> await event.reply("公告", at_all=True)
>>>
>>> # 组合使用：@用户 + 回复消息
>>> await event.reply("内容", at_users=["user1"], reply_to="msg_id")
```

---


##### `async async reply_ob12(message: list[dict[str, Any]] | dict[str, Any])`

使用 OneBot12 消息段回复

通过适配器的 Raw_ob12 方法发送 OneBot12 标准消息段，
是 reply() 方法的 OB12 对应版本。

:param message: OneBot12 消息段列表或单个消息段
    [
        {"type": "text", "data": {"text": "Hello"}},
        {"type": "image", "data": {"file": "https://..." }},
    ]
:return: 适配器 Raw_ob12 的返回值（标准响应格式）

**示例**:
```python
>>> # 简单文本回复
>>> await event.reply_ob12([{"type": "text", "data": {"text": "收到"}}])
>>>
>>> # 配合 MessageBuilder 使用
>>> from ErisPulse.Core import MessageBuilder
>>> await event.reply_ob12(
>>>     MessageBuilder()
>>>         .reply(event.get_id())
>>>         .text("收到你的消息")
>>>         .build()
>>> )
>>>
>>> # 发送复杂消息
>>> await event.reply_ob12(
>>>     MessageBuilder()
>>>         .mention(event.get_user_id())
>>>         .text("你好")
>>>         .image("https://example.com/img.jpg")
>>>         .build()
>>> )
```

---


##### `async async wait_reply(prompt: str | None = None, timeout: float = DEFAULT_WAIT_TIMEOUT_SECS, callback: Callable[[dict[str, Any]], Awaitable[Any]] = None, validator: Callable[[dict[str, Any]], bool] = None, method: str = DEFAULT_SEND_METHOD)`

等待用户回复

:param prompt: 提示消息，如果提供会发送给用户
:param timeout: 等待超时时间(秒)
:param callback: 回调函数，当收到回复时执行
:param validator: 验证函数，用于验证回复是否有效
:param method: 发送方法，默认为 "Text"（可选: "Image", "Markdown", "Html" 等）
:return: 用户回复的事件数据，如果超时则返回None

---


##### `async async confirm(prompt: str | None = None, timeout: float = DEFAULT_WAIT_TIMEOUT_SECS, yes_words: set[str] | frozenset[str] = None, no_words: set[str] | frozenset[str] = None, method: str = DEFAULT_SEND_METHOD)`

等待用户确认 (是/否)

自动发送提示消息并等待用户回复，识别内置中英文确认词。
内置确认词: 是/yes/y/确认/确定/好/ok/true/对/嗯/行/同意/没问题... (否/no/n/取消/不/不要/cancel/false/错/拒绝...)

:param prompt: str - 提示消息（可选，发送后等待回复）
:param timeout: float - 超时时间(秒)（默认: 60.0）
:param yes_words: set[str] - 自定义确认词集合（默认: 内置 CONFIRM_YES_WORDS）
:param no_words: set[str] - 自定义否定词集合（默认: 内置 CONFIRM_NO_WORDS）
:param method: str - 发送方法（默认: "Text"，可选: "Image", "Markdown" 等）
:return: bool|None - True=确认, False=否定, None=超时

**示例**:
```python
>>> if await event.confirm("确定要执行此操作吗？"):
...     await event.reply("已执行")
>>> # 发送图片作为确认提示
>>> if await event.confirm("https://example.com/image.jpg", method="Image"):
...     await event.reply("已确认")
```

---


##### `async async choose(prompt: str, options: list[str], timeout: float = DEFAULT_WAIT_TIMEOUT_SECS, method: str = DEFAULT_SEND_METHOD)`

等待用户从选项中选择

自动发送编号选项列表 (1.选项1 2.选项2 ...)，用户可回复编号或选项文本。
文本类方法 (Text/Markdown/Html) 将选项拼接到 prompt 后一条消息发送；
富媒体类方法 (Image/Voice 等) 先发富媒体内容，再单独发 Text 选项列表。

:param prompt: str - 提示消息（必须）
:param options: list[str] - 选项列表（不能为空）
:param timeout: float - 超时时间(秒)（默认: 60.0）
:param method: str - 发送方法（默认: "Text"，可选: "Image", "Markdown" 等）
:return: int|None - 选中选项的索引(0-based), 超时返回 None

**异常**: `ValueError` - 当 options 为空时

**示例**:
```python
>>> choice = await event.choose("请选择颜色:", ["红", "绿", "蓝"])
>>> if choice is not None:
...     await event.reply(f"你选择了: {['红','绿','蓝'][choice]}")
```

---


##### `async async collect(fields: list[dict[str, Any]], timeout_per_field: float = 60.0)`

多步骤收集信息 (表单式)

依次向用户发送提示消息并收集回复，每个字段可配置验证器和重试逻辑

:param fields: list[dict] - 字段列表，每个字段为字典:
    - key: str - 字段键名（必须）
    - prompt: str - 提示消息（默认: "请输入 {key}"）
    - validator: callable - 验证函数，接收 Event 对象，返回 bool（可选）
    - retry_prompt: str - 验证失败时的重试提示（默认: "输入无效，请重新输入"）
    - max_retries: int - 最大重试次数（默认: 3）
    - method: str - 发送方法（默认: "Text"，可选: "Image", "Markdown" 等）
:param timeout_per_field: float - 每个字段的超时时间(秒)（默认: 60.0）
:return: dict|None - 收集到的数据字典, 任何步骤超时或重试耗尽返回 None

**示例**:
```python
>>> data = await event.collect([
...     {"key": "name", "prompt": "请输入姓名"},
...     {"key": "age", "prompt": "请输入年龄",
...      "validator": lambda e: e.get("alt_message", "").strip().isdigit()},
...     {"key": "avatar", "prompt": "请发送头像图片", "method": "Image"},
... ])
>>> if data:
...     await event.reply(f"姓名: {data['name']}, 年龄: {data['age']}")
```

---


##### `async async wait_for(event_type: str = 'message', condition: Callable[['Event'], bool] = None, timeout: float = DEFAULT_WAIT_TIMEOUT_SECS)`

等待满足条件的任意事件

不限于同一用户/会话，可监听任意类型事件

:param event_type: str - 事件类型 (message/notice/request/meta 等，默认: message)
:param condition: callable - 条件函数，接收 Event 对象，返回 bool（可选）
:param timeout: float - 超时时间(秒)（默认: 60.0）
:return: Event|None - 匹配的事件, 超时返回 None

**示例**:
```python
>>> # 等待群成员加入通知
>>> evt = await event.wait_for(
...     "notice",
...     condition=lambda e: e.get_detail_type() == "group_member_increase",
...     timeout=120,
... )
>>>
>>> # 等待任意消息包含特定关键词
>>> evt = await event.wait_for(
...     condition=lambda e: "hello" in e.get_text(),
... )
```

---


##### `conversation(timeout: float = DEFAULT_WAIT_TIMEOUT_SECS)`

创建多轮对话上下文

:param timeout: 默认超时时间(秒)
:return: Conversation 对象

**示例**:
```python
>>> conv = event.conversation(timeout=30)
>>> await conv.say("欢迎！请问有什么需要帮助的？")
>>> while conv.is_active:
...     resp = await conv.wait()
...     if resp is None:
...         await conv.say("会话超时，再见！")
...         break
...     if resp.get_text() == "退出":
...         await conv.say("再见！")
...         break
```

---


##### `get_raw()`

获取原始事件数据

:return: dict - 原始事件数据字典

---


##### `get_raw_type()`

获取原始事件类型

:return: str - 原始事件类型

---


##### `get_command_name()`

获取命令名称

:return: str - 命令名称

---


##### `get_command_args()`

获取命令参数

:return: 命令参数列表

---


##### `get_command_raw()`

获取命令原始文本

:return: 命令原始文本

---


##### `get_command_info()`

获取完整命令信息

:return: 命令信息字典

---


##### `is_command()`

是否为命令

:return: 是否为命令

---


##### `to_dict()`

转换为字典

:return: 事件数据字典

---


##### `is_processed()`

是否已被处理

:return: 是否已被处理

---


##### `mark_processed()`

标记为已处理

---


##### `__getattribute__(name: str)`

属性查找优先级:
1. 平台注册的方法覆写（仅当前平台，优先于内置方法）
2. 内置方法/属性（正常解析）

:param name: str - 属性名
:return: Any - 属性值

---


##### `__getattr__(name: str)`

属性查找优先级:
1. 平台注册的扩展方法（仅当前平台）
2. 字典键访问（点式访问 event.platform 等）

:param name: str - 属性名
:return: Any - 属性值
**异常**: `AttributeError` - 属性不存在

---


##### `__dir__()`

让 dir(event) 包含当前平台注册的扩展方法名

---


##### `__repr__()`

字符串表示

:return: 字符串表示

---


### `class Conversation`

多轮对话上下文

提供在同一会话中进行多轮交互的便捷方法，支持分支跳转、上下文持久化

> **提示**
> 1. 通过 event.conversation() 方法创建
> 2. 超时后自动标记为非活跃状态
> 3. 支持链式调用 say() 方法
> 4. 支持 branch() 定义分支和 goto() 跳转
> 5. 支持 context 字典存储对话状态
> 6. 支持 save()/resume() 持久化到 storage


#### 方法列表


##### `__init__(event: 'Event', timeout: float = DEFAULT_WAIT_TIMEOUT_SECS)`

初始化对话上下文

:param event: Event - 事件对象
:param timeout: float - 默认超时时间(秒)（默认: 60.0）

---


##### `is_active()`

对话是否处于活跃状态

:return: bool - 是否活跃

---


##### `async async say(content: str)`

发送消息

:param content: str - 消息内容
:return: Conversation - self（支持链式调用）

---


##### `async async wait(prompt: str | None = None, timeout: float = None, method: str = DEFAULT_SEND_METHOD)`

等待用户回复

:param prompt: str - 提示消息（可选）
:param timeout: float - 超时时间(秒)，默认使用对话的超时设置
:param method: str - 发送方法（默认: "Text"）
:return: Event|None - 用户回复的事件, 超时返回 None

---


##### `async async confirm(prompt: str | None = None)`

等待用户确认

:param prompt: str - 提示消息
:return: bool|None - True/False/None

---


##### `async async choose(prompt: str, options: list[str])`

等待用户选择

:param prompt: str - 提示消息
:param options: list[str] - 选项列表
:return: int|None - 选中索引或 None

---


##### `async async collect(fields: list[dict])`

多步骤收集信息

:param fields: list[dict] - 字段列表，支持 condition 字段:
    - condition: callable - 接收已收集数据 dict, 返回 bool 决定是否收集此字段
:return: dict|None - 收集到的数据字典或 None

---


##### `stop()`

结束对话

---


##### `branch(name: str)`

注册分支处理器

:param name: str 分支名称
:return: Callable 装饰器

**示例**:
```python
>>> conv = event.conversation()
>>>
>>> @conv.branch("menu")
... async def menu_branch(conv, event):
...     await conv.say("1.饮品 2.主食")
...     resp = await conv.wait()
...     if resp and resp.get_text() == "1":
...         conv.goto("drink")
...
>>> @conv.branch("drink")
... async def drink_branch(conv, event):
...     await conv.say("请选择饮品")
...     resp = await conv.wait()
...     conv.context["drink"] = resp.get_text()
...     conv.goto("confirm")
...
>>> conv.start("menu")
```

---


##### `goto(branch_name: str, event: 'Event' = None)`

跳转到指定分支

:param branch_name: str 目标分支名称
:param event: Event 传递给分支的事件对象 (可选)

**异常**: `ValueError` - 当目标分支不存在时

**示例**:
```python
>>> conv.goto("drink")
```

---


##### `start(branch_name: str, event: 'Event' = None)`

启动对话，从指定分支开始

:param branch_name: str 起始分支名称
:param event: Event 初始事件对象 (可选)

**异常**: `ValueError` - 当起始分支不存在时

**示例**:
```python
>>> conv.start("menu")
```

---


##### `get_current_branch()`

获取当前分支名称

:return: str|None 当前分支名, 未在分支中时返回 None

---


##### `has_branch(name: str)`

检查分支是否存在

:param name: str 分支名称
:return: bool 是否存在

---


##### `async async save()`

保存对话状态到 storage

**示例**:
```python
>>> await conv.save()

> **提示**
> 保存内容包括: 当前分支、上下文数据、活跃状态
> 可用于重启后恢复对话
```

---


##### `async async resume(event: 'Event' = None)`

从 storage 恢复对话状态

:param event: Event 新的事件对象 (可选, 不传则使用原事件)
:return: bool 是否恢复成功

**示例**:
```python
>>> conv = event.conversation()
>>> # ... 注册分支 ...
>>> if await conv.resume():
...     conv.goto(conv.get_current_branch())

> **提示**
> 需要在 resume() 之前先注册好所有分支
```

---


##### `async async clear_saved()`

清除保存的对话状态

**示例**:
```python
>>> await conv.clear_saved()
```

---

