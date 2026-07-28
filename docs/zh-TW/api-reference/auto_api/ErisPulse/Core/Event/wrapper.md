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

- **platform** (`平台名称（需与适配器注册名一致），传`): "*" 表示对所有平台生效
- **mixin_cls** (`包含平台方法的类`): **返回值** (`成功注册的方法数量`): 
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

- **platform** (`平台名称（需与适配器注册名一致），传`): "*" 表示对所有平台生效

**示例**:
```python
>>> @register_event_method("email")
... def get_subject(self):
...     return self.get("email_raw", {}).get("subject", "")
>>>
>>> # 跨平台通配符
>>> @register_event_method("*")
... def ai_chat(self, prompt):
...     return await self.reply(f"AI: {prompt}")
```

---


### `unregister_event_method(platform: str, name: str)`

注销指定平台的单个扩展方法

- **platform** (`平台名称`): - **name**: 方法名
**返回值**: 是否成功注销

---


### `unregister_platform_event_methods(platform: str)`

注销指定平台的全部扩展方法

适配器关闭时应调用此方法清理注册的方法。

- **platform** (`平台名称`): **返回值**: 被注销的方法数量

---


### `get_platform_event_methods(platform: str)`

查询指定平台已注册的扩展方法名列表

- **platform** (`平台名称`): **返回值**: 方法名列表

---


### `async _builtin_wait_reply(event: 'Event', prompt: str | None = None, timeout: float = DEFAULT_WAIT_TIMEOUT_SECS, callback: Callable[[dict[str, Any]], Awaitable[Any]] | None = None, validator: Callable[[dict[str, Any]], bool] | None = None, method: str = DEFAULT_SEND_METHOD)`

内置 wait_reply 实现

供覆写函数调用以复用内置等待逻辑。

---


### `async _builtin_confirm(event: 'Event', prompt: str | None = None, timeout: float = DEFAULT_WAIT_TIMEOUT_SECS, yes_words: set[str] | frozenset[str] | None = None, no_words: set[str] | frozenset[str] | None = None, method: str = DEFAULT_SEND_METHOD, hint: bool = False)`

内置 confirm 实现

供覆写函数调用以复用内置确认逻辑。

---


### `_format_options(options: list[str], fmt: str | Callable[[list[str]], str], method: str = DEFAULT_SEND_METHOD)`

格式化选项列表为文本

- **options** (`选项列表`): - **fmt**: 格式类型，支持 "auto"（根据 method 自动选择）、"list"、"inline"、"md"、"html" 或自定义函数
- **method** (`发送方法名，fmt="auto"`): 时用于推断合适的格式
**返回值**: 格式化后的选项文本

---


### `_merge_prompt_options(prompt: str, options_text: str, placeholder: str = '{options}')`

将选项文本合并到提示消息中

如果 prompt 包含占位符（默认 ``{options}``），则替换占位符；
否则将选项追加到 prompt 末尾（用换行分隔）。

- **prompt** (`提示消息（可能包含占位符）`): - **options_text**: 已格式化的选项文本
- **placeholder** (`占位符标记，prompt`): 中出现该标记的位置将被替换为选项文本
**返回值**: 合并后的完整提示消息

---


### `_is_text_method(method: str)`

判断发送方法是否为文本类（内容可拼接选项文本）

通过大小写不敏感的子串匹配：方法名包含 text/md/markdown/html/h5 即视为文本类。
设计原则是“只要不是明确的富媒体就合并”，减少拆分消息的情况。

- **method** (`发送方法名`): **返回值** (`True`): 表示该方法是文本类，选项可直接拼接到末尾

---


### `async _builtin_choose(event: 'Event', prompt: str, options: list[str], timeout: float = DEFAULT_WAIT_TIMEOUT_SECS, method: str = DEFAULT_SEND_METHOD, options_format: str | Callable[[list[str]], str] = 'auto', merge_prompt: bool = False, placeholder: str = '{options}')`

内置 choose 实现

供覆写函数调用以复用内置选择逻辑。

发送行为取决于 method 和 merge_prompt：
- 文本类方法 (Text/Markdown/md/Html/h5 等): 选项默认拼接到 prompt 末尾，一条消息发送
- 非文本方法 (Image/Voice 等) + merge_prompt=False: 先发富媒体 prompt，再发 Text 选项
- 任意方法 + merge_prompt=True: 强制合并为一条消息发送（用用户指定的 method）
- prompt 含占位符（默认 ``{options}``，可通过 placeholder 自定义）时，替换该位置；否则追加到末尾
- options_format="auto" 时根据 method 自动选择内置样式（Markdown→无序列表，Html→有序列表）

---


### `async _builtin_collect(event: 'Event', fields: list[dict[str, Any]], timeout_per_field: float = 60.0)`

内置 collect 实现

供覆写函数调用以复用内置收集逻辑。
每个 field 支持 `method` 键来指定发送方法。

---


### `_normalize_modifier(mod)`

> **内部方法**
归一化修饰方法定义为 (name, args, kwargs)

支持以下形式：
- ``"Name"``                            → ``("Name", (), {})``
- ``("Name",)``                         → ``("Name", (), {})``
- ``("Name", arg1, arg2, ...)``         → ``("Name", (arg1, arg2, ...), {})``
- ``("Name", (arg1, arg2), kwargs_dict)`` → 显式位置参数 + 关键字参数

- **mod** (`str|tuple`): - 修饰方法定义（字符串或元组）
**返回值** (`tuple`): - ``(方法名, 位置参数元组, 关键字参数字典)``

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

- **event_data**: 原始事件数据

---


##### `get_id()`

获取事件ID

**返回值**: 事件ID

---


##### `get_time()`

获取事件时间戳

**返回值**: Unix时间戳（秒级）

---


##### `get_type()`

获取事件类型

**返回值**: 事件类型（message/notice/request/meta等）

---


##### `get_detail_type()`

获取事件详细类型

**返回值**: 事件详细类型（private/group/friend等）

---


##### `get_platform()`

获取平台名称

**返回值**: 平台名称

---


##### `get_self_platform()`

获取机器人平台

**返回值**: 机器人平台名称

---


##### `get_self_user_id()`

获取机器人用户ID

**返回值**: 机器人用户ID

---


##### `get_self_account_id()`

获取机器人账户标识（多Bot模式）

优先返回 account_id（ErisPulse扩展），若不存在则回退到 user_id（OB12标准）

**返回值**: 机器人账户标识，单Bot模式下返回空字符串

---


##### `get_self_info()`

获取机器人完整信息

**返回值**: 机器人信息字典

---


##### `get_message()`

获取消息段数组

**返回值**: 消息段数组

---


##### `get_alt_message()`

获取消息备用文本

**返回值**: 消息备用文本

---


##### `get_text()`

获取纯文本内容

**返回值**: 纯文本内容

---


##### `get_message_text()`

获取纯文本内容（别名）

**返回值**: 纯文本内容

---


##### `has_mention()`

是否包含@消息

**返回值**: 是否包含@消息

---


##### `get_mentions()`

获取所有被@的用户ID列表

**返回值**: 被@的用户ID列表

---


##### `get_user_id()`

获取发送者ID

**返回值**: 发送者用户ID

---


##### `is_master()`

检查事件发送者是否为框架主人

基于 ``ErisPulse.master.users`` 配置和运行时添加的主人列表判断。

**返回值** (`是否为框架主人`): 
**示例**:
```python
>>> if event.is_master():
...     await event.reply("主人你好")
```

---


##### `get_user_nickname()`

获取发送者昵称

**返回值**: 发送者昵称

---


##### `get_group_id()`

获取群组ID

**返回值**: 群组ID（群聊消息）

---


##### `get_channel_id()`

获取频道ID

**返回值**: 频道ID（频道消息）

---


##### `get_guild_id()`

获取服务器ID

**返回值**: 服务器ID（服务器消息）

---


##### `get_thread_id()`

获取话题/子频道ID

**返回值**: 话题ID（话题消息）

---


##### `get_target_id()`

获取当前会话的目标ID（统一接口）

根据事件类型自动返回对应的目标ID：
群聊 → group_id，频道 → channel_id，私聊 → user_id，以此类推。

**返回值** (`目标ID字符串，无法确定时返回空字符串`): 
**示例**:
```python
>>> target = event.get_target_id()
>>> # 群聊事件 → group_id
>>> # 私聊事件 → user_id
```

---


##### `get_session_id()`

生成会话唯一标识

格式: ``{platform}:{detail_type}:{target_id}``
如: ``telegram:private:12345``、``qq:group:67890``

用于存储、上下文管理等需要唯一标识会话的场景。

**返回值** (`会话标识字符串`): 
**示例**:
```python
>>> session_id = event.get_session_id()
>>> # "qq:group:123456"
```

---


##### `get_sender()`

获取发送者信息字典

**返回值**: 发送者信息字典

---


##### `is_message()`

是否为消息事件

**返回值**: 是否为消息事件

---


##### `is_private_message()`

是否为私聊消息

**返回值**: 是否为私聊消息

---


##### `is_group_message()`

是否为群聊消息

**返回值**: 是否为群聊消息

---


##### `is_at_message()`

是否为@消息

**返回值**: 是否为@消息

---


##### `get_operator_id()`

获取操作者ID

**返回值**: 操作者ID

---


##### `get_operator_nickname()`

获取操作者昵称

**返回值**: 操作者昵称

---


##### `is_notice()`

是否为通知事件

**返回值**: 是否为通知事件

---


##### `is_group_member_increase()`

群成员增加

**返回值**: 是否为群成员增加事件

---


##### `is_group_member_decrease()`

群成员减少

**返回值**: 是否为群成员减少事件

---


##### `is_friend_add()`

好友添加

**返回值**: 是否为好友添加事件

---


##### `is_friend_delete()`

好友删除

**返回值**: 是否为好友删除事件

---


##### `get_comment()`

获取请求附言

**返回值**: 请求附言

---


##### `get_request_id()`

获取请求ID

用于标识可操作的请求，配合 approve()/reject() 使用。

**返回值**: 请求ID，不存在时返回空字符串

---


##### `async approve(comment: str | None = None)`

同意当前请求事件

通过适配器的 Request DSL 执行同意操作。
仅对请求类型事件（type == "request"）有效。

- **comment** (`附带备注信息（可选，部分平台支持）`): **返回值** (`标准响应格式`): **异常**: `ValueError` - 当事件不是请求类型或缺少必要字段时

**示例**:
```python
>>> @request.on_friend_request()
... async def handle_friend_request(event):
...     await event.approve()
...     # 带备注
...     await event.approve(comment="欢迎添加好友")
```

---


##### `async reject(comment: str | None = None)`

拒绝当前请求事件

通过适配器的 Request DSL 执行拒绝操作。
仅对请求类型事件（type == "request"）有效。

- **comment** (`附带备注信息（可选，部分平台支持）`): **返回值** (`标准响应格式`): **异常**: `ValueError` - 当事件不是请求类型或缺少必要字段时

**示例**:
```python
>>> @request.on_group_request()
... async def handle_group_request(event):
...     await event.reject()
```

---


##### `async _handle_request_action(action: str, comment: str | None = None)`

执行请求操作的内部方法

- **action** (`操作类型`): ("accept" / "reject")
- **comment** (`附带备注`): **返回值** (`标准响应格式`): **异常**: `ValueError` - 当缺少必要字段时

---


##### `is_request()`

是否为请求事件

**返回值**: 是否为请求事件

---


##### `is_friend_request()`

是否为好友请求

**返回值**: 是否为好友请求

---


##### `is_group_request()`

是否为群组请求

**返回值**: 是否为群组请求

---


##### `_get_adapter_and_target()`

获取适配器实例和目标信息

使用会话类型管理模块自动处理类型转换和ID获取

**返回值** (`(适配器实例,`): 发送目标类型, 目标ID, 账户ID)

---


##### `async reply(content: str, method: str | None = None, at_sender: bool = False, quote: bool = False, at_users: list[str] | None = None, reply_to: str | None = None, at_all: bool = False, via: list | None = None)`

通用回复方法

基于适配器的Text方法，但可以通过method参数指定其他发送方法

- **content** (`发送内容（文本、URL等，取决于method参数）`): - **method**: str - 适配器发送方法（默认: "Text"）
               可选值: "Text", "Image", "Voice", "Video", "File" 等；
               使用 via 时必须显式指定
- **at_sender** (`是否@发送者（自动从事件中提取`): user_id）
- **quote** (`是否引用回复当前消息（自动从事件中提取`): message_id）
- **at_users** (`@用户列表（可选），如`): ["user1", "user2"]
- **reply_to** (`回复消息ID（可选，手动指定）`): - **at_all**: 是否@全体成员（可选），默认为 False
- **via** (`list`): - 经由的平台修饰方法链（可选，默认: None），按顺序在发送方法前应用。
            每个元素可为：
            - ``"Name"``（无参）
            - ``("Name", arg1, arg2, ...)``（位置参数）
            - ``("Name", (arg1, ...), {kw: val})``（位置+关键字参数）
            例如 ``[("Expire", 3600), ("ForMember", "uid")]`` 等价于
            ``.Expire(3600).ForMember("uid")``。
            当需要连续多个修饰方法、或 method 强依赖修饰方法时使用；
            更复杂的场景建议用 :meth:`send_chain`
- **kwargs** (`额外参数，例如Mention方法的user_id`): **返回值** (`Any`): - 适配器发送方法的返回值

**异常**: `ValueError` - 当适配器不支持指定的发送方法/修饰方法时

**示例**:
```python
>>> # 简单回复
>>> await event.reply("你好")
>>>
>>> # 回复并@发送者
>>> await event.reply("你好", at_sender=True)
>>>
>>> # 回复并引用当前消息
>>> await event.reply("收到", quote=True)
>>>
>>> # 发送图片
>>> await event.reply("http://example.com/image.jpg", method="Image")
>>>
>>> # @指定用户
>>> await event.reply("你好", at_users=["user123"])
>>>
>>> # @全体成员
>>> await event.reply("公告", at_all=True)
>>>
>>> # 平台专有修饰方法链 + 看板发送
>>> await event.reply("看板内容", method="Board",
...                   via=[("Expire", 3600), ("ForMember", "uid")])
```

---


##### `async reply_ob12(message: list[dict[str, Any]] | dict[str, Any])`

使用 OneBot12 消息段回复

通过适配器的 Raw_ob12 方法发送 OneBot12 标准消息段，
是 reply() 方法的 OB12 对应版本。

- **message** (`OneBot12`): 消息段列表或单个消息段
    [
        {"type": "text", "data": {"text": "Hello"}},
        {"type": "image", "data": {"file": "https://..." }},
    ]
**返回值** (`适配器`): Raw_ob12 的返回值（标准响应格式）

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


##### `send_chain()`

获取已配置好目标和发送账号的发送链

返回已设置 ``To``（目标）和 ``Using``（发送账号）的 SendDSL 实例，
可自由追加修饰方法（At/Reply/平台专有修饰）和发送方法。

适用于 :meth:`reply` 无法覆盖的场景：
- 平台专有修饰方法（如云虎的 Expire/ExpireAt/ForMember）
- 需要连续多个修饰方法
- 无内容参数的动作型发送方法（如 DismissBoard）

**返回值** (`SendDSL`): - 已设置目标和发送账号的发送链实例

**异常**: `ValueError` - 当事件缺少 platform 字段或找不到对应适配器时

**示例**:
```python
>>> # 平台专有修饰方法 + 看板发送
>>> await event.send_chain().Expire(3600).Board("一小时后过期")
>>>
>>> # 连续多个修饰方法
>>> await (event.send_chain()
...        .Expire(3600)
...        .ForMember("114514")
...        .Board("看板内容", content_type="markdown"))
>>>
>>> # 内置修饰方法同样可用
>>> await event.send_chain().At("123").Reply("msg_id").Text("hi")
>>>
>>> # 无内容参数的动作型方法
>>> await event.send_chain().DismissBoard()
```

---


##### `supports(method: str)`

检查当前事件所在平台是否支持某发送方法

- **method** (`发送方法名，如`): "Image"、"Voice"、"Video"
**返回值** (`是否支持`): 
**示例**:
```python
>>> if event.supports("Image"):
...     await event.reply(url, method="Image")
```

---


##### `available_methods()`

列出当前平台所有可用发送方法

**返回值** (`发送方法名列表`): 
**示例**:
```python
>>> methods = event.available_methods()
>>> # ["Text", "Image", "Voice", ...]
```

---


##### `async wait_reply(prompt: str | None = None, timeout: float = DEFAULT_WAIT_TIMEOUT_SECS, callback: Callable[[dict[str, Any]], Awaitable[Any]] | None = None, validator: Callable[[dict[str, Any]], bool] | None = None, method: str = DEFAULT_SEND_METHOD)`

等待用户回复

- **prompt** (`提示消息，如果提供会发送给用户`): - **timeout**: 等待超时时间(秒)
- **callback** (`回调函数，当收到回复时执行`): - **validator**: 验证函数，用于验证回复是否有效
- **method** (`发送方法，默认为`): "Text"（可选: "Image", "Markdown", "Html" 等）
**返回值**: 用户回复的事件数据，如果超时则返回None

---


##### `async confirm(prompt: str | None = None, timeout: float = DEFAULT_WAIT_TIMEOUT_SECS, yes_words: set[str] | frozenset[str] | None = None, no_words: set[str] | frozenset[str] | None = None, method: str = DEFAULT_SEND_METHOD, hint: bool = False)`

等待用户确认 (是/否)

自动发送提示消息并等待用户回复，识别内置中英文确认词。
内置确认词: 是/yes/y/确认/确定/好/ok/true/对/嗯/行/同意/没问题... (否/no/n/取消/不/不要/cancel/false/错/拒绝...)

- **prompt** (`str`): - 提示消息（可选，发送后等待回复）
- **timeout** (`float`): - 超时时间(秒)（默认: 60.0）
- **yes_words** (`set[str]`): - 自定义确认词集合（默认: 内置 CONFIRM_YES_WORDS）
- **no_words** (`set[str]`): - 自定义否定词集合（默认: 内置 CONFIRM_NO_WORDS）
- **method** (`str`): - 发送方法（默认: "Text"，可选: "Image", "Markdown" 等）
- **hint** (`bool`): - 是否在提示消息末尾自动追加确认词提示，如 "（是/否）"（默认: False）
**返回值** (`bool|None`): - True=确认, False=否定, None=超时

**示例**:
```python
>>> if await event.confirm("确定要执行此操作吗？", hint=True):
...     await event.reply("已执行")
>>> # 发送图片作为确认提示
>>> if await event.confirm("https://example.com/image.jpg", method="Image"):
...     await event.reply("已确认")
```

---


##### `async choose(prompt: str, options: list[str], timeout: float = DEFAULT_WAIT_TIMEOUT_SECS, method: str = DEFAULT_SEND_METHOD, options_format: str | Callable[[list[str]], str] = 'auto', merge_prompt: bool = False, placeholder: str = '{options}')`

等待用户从选项中选择

        自动发送编号选项列表，用户可回复编号或选项文本。

        发送行为取决于 method 和 merge_prompt：
        - 文本类方法 (Text/Markdown/md/Html/h5 等): 选项默认拼接到 prompt 末尾，一条消息发送
        - 非文本方法 (Image/Voice 等) + merge_prompt=False (默认): 先发富媒体 prompt，再发 Text 选项
        - 任意方法 + merge_prompt=True: 强制合并为一条消息发送（用用户指定的 method）
        - prompt 含占位符（默认 ``{options}``，可通过 placeholder 自定义）时，替换该位置；否则追加到末尾

        - **prompt** (`str`): - 提示消息（必须）。可含占位符指定选项插入位置
        - **options** (`list[str]`): - 选项列表（不能为空）
        - **timeout** (`float`): - 超时时间(秒)（默认: 60.0）
        - **method** (`str`): - 发送方法（默认: "Text"）
        - **options_format** (`str|callable`): - 选项格式（默认: "auto"，根据 method 自动选择内置样式）
            - "auto": 根据 method 自动选择（Markdown→无序列表，Html→有序列表，其他→纯文本列表）
            - "list": 每行一个，如 ``1. 选项A
2. 选项B``
            - "inline": 单行展示，如 ``1.选项A | 2.选项B``
            - "md": Markdown 无序列表，如 ``- 1. 选项A
- 2. 选项B``
            - "html": Html 有序列表，如 ``<ol><li>1. 选项A</li>...</ol>``
            - callable: 自定义函数，接收 ``list[str]`` 返回 ``str``
        - **merge_prompt** (`bool`): - 是否合并为一条消息（默认: False）
            合并时使用用户指定的 method（如 Markdown/Html/Image 等），尊重用户选择
        - **placeholder** (`str`): - 选项插入占位符（默认: ``{options}``），
            prompt 中出现该标记的位置将被替换为选项文本；设为空字符串则始终追加到末尾
        **返回值** (`int|None`): - 选中选项的索引(0-based), 超时返回 None

        **异常**: `ValueError` - 当 options 为空时

        :example:
        >>> # 基本用法（prompt 和选项分两条消息）
        >>> choice = await event.choose("请选择颜色:", ["红", "绿", "蓝"])
        >>> # 合并模式：用 Markdown 一条消息发送
        >>> choice = await event.choose("请选择:", ["A", "B"],
        ...     method="Markdown", merge_prompt=True)
        >>> # 占位符：控制选项插入位置
        >>> choice = await event.choose(
        ...     "## 任务选择
{options}
请回复编号",
        ...     ["下载", "上传"], method="Markdown", merge_prompt=True)
        >>> # 自定义占位符
        >>> choice = await event.choose(
        ...     "请选择: [choices]",
        ...     ["A", "B"], placeholder="[choices]")

---


##### `async collect(fields: list[dict[str, Any]], timeout_per_field: float = 60.0)`

多步骤收集信息 (表单式)

依次向用户发送提示消息并收集回复，每个字段可配置验证器和重试逻辑

- **fields** (`list[dict]`): - 字段列表，每个字段为字典:
    - key: str - 字段键名（必须）
    - prompt: str - 提示消息（默认: "请输入 {key}"）
    - validator: callable - 验证函数，接收 Event 对象，返回 bool（可选）
    - retry_prompt: str - 验证失败时的重试提示（默认: "输入无效，请重新输入"）
    - max_retries: int - 最大重试次数（默认: 3）
    - method: str - 发送方法（默认: "Text"，可选: "Image", "Markdown" 等）
    - options: list[str] - 可选值列表，提供时该字段变为选择题（可选）
    - options_format: str|callable - 选项格式（默认: "auto"，详见 choose()）
    - merge_prompt: bool - 是否合并为一条消息（默认: False）
    - placeholder: str - 选项插入占位符（默认: "{options}"，详见 choose()）
- **timeout_per_field** (`float`): - 每个字段的超时时间(秒)（默认: 60.0）
**返回值** (`dict|None`): - 收集到的数据字典, 任何步骤超时或重试耗尽返回 None

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


##### `async wait_for(event_type: str = 'message', condition: Callable[['Event'], bool] | None = None, timeout: float = DEFAULT_WAIT_TIMEOUT_SECS)`

等待满足条件的任意事件

不限于同一用户/会话，可监听任意类型事件

- **event_type** (`str`): - 事件类型 (message/notice/request/meta 等，默认: message)
- **condition** (`callable`): - 条件函数，接收 Event 对象，返回 bool（可选）
- **timeout** (`float`): - 超时时间(秒)（默认: 60.0）
**返回值** (`Event|None`): - 匹配的事件, 超时返回 None

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

- **timeout** (`默认超时时间(秒)`): **返回值** (`Conversation`): 对象

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

**返回值** (`dict`): - 原始事件数据字典

---


##### `get_raw_type()`

获取原始事件类型

**返回值** (`str`): - 原始事件类型

---


##### `get_command_name()`

获取命令名称

**返回值** (`str`): - 命令名称

---


##### `get_command_args()`

获取命令参数

**返回值**: 命令参数列表

---


##### `get_command_raw()`

获取命令原始文本

**返回值**: 命令原始文本

---


##### `get_command_info()`

获取完整命令信息

**返回值**: 命令信息字典

---


##### `is_command()`

是否为命令

**返回值**: 是否为命令

---


##### `to_dict()`

转换为字典

**返回值**: 事件数据字典

---


##### `is_processed()`

是否已被处理

**返回值**: 是否已被处理

---


##### `mark_processed()`

标记为已处理

---


##### `__getattribute__(name: str)`

属性查找优先级:
1. 当前平台的注册方法覆写（优先于内置方法）
2. 通配符 "*" 平台的注册方法
3. 内置方法/属性（正常解析）

- **name** (`str`): - 属性名
**返回值** (`Any`): - 属性值

---


##### `__getattr__(name: str)`

属性查找优先级:
1. 当前平台的扩展方法
2. 通配符 "*" 平台的扩展方法
3. 字典键访问（点式访问 event.platform 等）

- **name** (`str`): - 属性名
**返回值** (`Any`): - 属性值
**异常**: `AttributeError` - 属性不存在

---


##### `__dir__()`

让 dir(event) 包含当前平台和通配符注册的扩展方法名

---


##### `__repr__()`

字符串表示

**返回值**: 字符串表示

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

- **event** (`Event`): - 事件对象
- **timeout** (`float`): - 默认超时时间(秒)（默认: 60.0）

---


##### `is_active()`

对话是否处于活跃状态

**返回值** (`bool`): - 是否活跃

---


##### `async say(content: str)`

发送消息

- **content** (`str`): - 消息内容
**返回值** (`Conversation`): - self（支持链式调用）

---


##### `async wait(prompt: str | None = None, timeout: float | None = None, method: str = DEFAULT_SEND_METHOD)`

等待用户回复

- **prompt** (`str`): - 提示消息（可选）
- **timeout** (`float`): - 超时时间(秒)，默认使用对话的超时设置
- **method** (`str`): - 发送方法（默认: "Text"）
**返回值** (`Event|None`): - 用户回复的事件, 超时返回 None

---


##### `async confirm(prompt: str | None = None)`

等待用户确认

- **prompt** (`str`): - 提示消息
**返回值** (`bool|None`): - True/False/None

---


##### `async choose(prompt: str, options: list[str])`

等待用户选择

- **prompt** (`str`): - 提示消息
- **options** (`list[str]`): - 选项列表
**返回值** (`int|None`): - 选中索引或 None

---


##### `async collect(fields: list[dict])`

多步骤收集信息

- **fields** (`list[dict]`): - 字段列表，支持 condition 字段:
    - condition: callable - 接收已收集数据 dict, 返回 bool 决定是否收集此字段
**返回值** (`dict|None`): - 收集到的数据字典或 None

---


##### `stop()`

结束对话

---


##### `branch(name: str)`

注册分支处理器

- **name** (`str`): 分支名称
**返回值** (`Callable`): 装饰器

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


##### `goto(branch_name: str, event: 'Event | None' = None)`

跳转到指定分支

- **branch_name** (`str`): 目标分支名称
- **event** (`Event`): 传递给分支的事件对象 (可选)

**异常**: `ValueError` - 当目标分支不存在时

**示例**:
```python
>>> conv.goto("drink")
```

---


##### `start(branch_name: str, event: 'Event | None' = None)`

启动对话，从指定分支开始

- **branch_name** (`str`): 起始分支名称
- **event** (`Event`): 初始事件对象 (可选)

**异常**: `ValueError` - 当起始分支不存在时

**示例**:
```python
>>> conv.start("menu")
```

---


##### `get_current_branch()`

获取当前分支名称

**返回值** (`str|None`): 当前分支名, 未在分支中时返回 None

---


##### `has_branch(name: str)`

检查分支是否存在

- **name** (`str`): 分支名称
**返回值** (`bool`): 是否存在

---


##### `async save()`

保存对话状态到 storage

**示例**:
```python
>>> await conv.save()

> **提示**
> 保存内容包括: 当前分支、上下文数据、活跃状态
> 可用于重启后恢复对话
```

---


##### `async resume(event: 'Event | None' = None)`

从 storage 恢复对话状态

- **event** (`Event`): 新的事件对象 (可选, 不传则使用原事件)
**返回值** (`bool`): 是否恢复成功

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


##### `async clear_saved()`

清除保存的对话状态

**示例**:
```python
>>> await conv.clear_saved()
```

---

