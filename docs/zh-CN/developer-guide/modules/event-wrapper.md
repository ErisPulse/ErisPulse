# Event 包装类详解

Event 模块提供了功能强大的 Event 包装类，简化事件处理。

## 核心特性

- **完全兼容字典**：Event 继承自 dict
- **便捷方法**：提供大量便捷方法
- **点式访问**：支持使用点号访问事件字段
- **向后兼容**：所有方法都是可选的

## 核心字段方法

```python
from ErisPulse.Core.Event import command

@command("info")
async def info_command(event):
    event_id = event.get_id()
    platform = event.get_platform()
    time = event.get_time()
    print(f"ID: {event_id}, 平台: {platform}, 时间: {time}")
```

## 消息事件方法

```python
from ErisPulse.Core.Event import message

@message.on_private_message()
async def private_handler(event):
    text = event.get_text()
    user_id = event.get_user_id()
    nickname = event.get_user_nickname()
    await event.reply(f"你好，{nickname}！")
```

## 消息类型判断

```python
from ErisPulse.Core.Event import message

@message.on_group_message()
async def group_handler(event):
    is_private = event.is_private_message()
    is_group = event.is_group_message()
    is_at = event.is_at_message()
    await event.reply(f"类型: {'私聊' if is_private else '群聊'}")
```

## 回复功能

```python
from ErisPulse.Core.Event import command

@command("ask")
async def ask_command(event):
    await event.reply("请输入你的名字:")
    reply = await event.wait_reply(timeout=30)
    if reply:
        name = reply.get_text()
        await event.reply(f"你好，{name}！")
```

## 命令信息获取

```python
from ErisPulse.Core.Event import command

@command("cmdinfo")
async def cmdinfo_command(event):
    cmd_name = event.get_command_name()
    cmd_args = event.get_command_args()
    await event.reply(f"命令: {cmd_name}, 参数: {cmd_args}")
```

## 通知事件方法

```python
from ErisPulse.Core.Event import notice

@notice.on_friend_add()
async def friend_add_handler(event):
    await event.reply("欢迎添加我为好友！")
```

## 方法速查表

### 核心方法

#### 事件基础信息
- `get_id()` - 获取事件ID
- `get_time()` - 获取事件时间戳（Unix秒级）
- `get_type()` - 获取事件类型（message/notice/request/meta）
- `get_detail_type()` - 获取事件详细类型（private/group/friend等）
- `get_platform()` - 获取平台名称

#### 机器人信息
- `get_self_platform()` - 获取机器人平台名称
- `get_self_user_id()` - 获取机器人用户ID
- `get_self_account_id()` - 获取机器人账户ID（多Bot模式）
- `get_self_info()` - 获取机器人完整信息字典

#### 会话标识
- `get_target_id()` - 获取统一目标 ID（群聊返回 `group_id`，频道返回 `channel_id`，私聊返回 `user_id`，按 group → channel → guild → thread → user 顺序取首个非空值）
- `get_session_id()` - 获取会话唯一标识，格式为 `{platform}:{detail_type}:{target_id}`

### 消息事件方法

#### 消息内容
- `get_message()` - 获取消息段数组（OneBot12格式）
- `get_alt_message()` - 获取消息备用文本
- `get_text()` - 获取纯文本内容（`get_alt_message()` 的别名）
- `get_message_text()` - 获取纯文本内容（`get_alt_message()` 的别名）

#### 发送者信息
- `get_user_id()` - 获取发送者用户ID
- `get_user_nickname()` - 获取发送者昵称
- `get_sender()` - 获取发送者完整信息字典

#### 群组/频道信息
- `get_group_id()` - 获取群组ID（群聊消息）
- `get_channel_id()` - 获取频道ID（频道消息）
- `get_guild_id()` - 获取服务器ID（服务器消息）
- `get_thread_id()` - 获取话题/子频道ID（话题消息）

#### @消息相关
- `has_mention()` - 是否包含@机器人
- `get_mentions()` - 获取所有被@的用户ID列表

### 消息类型判断

#### 基础判断
- `is_message()` - 是否为消息事件
- `is_private_message()` - 是否为私聊消息
- `is_group_message()` - 是否为群聊消息
- `is_at_message()` - 是否为@消息（`has_mention()` 的别名）

### 通知事件方法

#### 通知操作者
- `get_operator_id()` - 获取操作者ID
- `get_operator_nickname()` - 获取操作者昵称

#### 通知类型判断
- `is_notice()` - 是否为通知事件
- `is_group_member_increase()` - 群成员增加事件
- `is_group_member_decrease()` - 群成员减少事件
- `is_friend_add()` - 好友添加事件（匹配 `detail_type == "friend_increase"`）
- `is_friend_delete()` - 好友删除事件（匹配 `detail_type == "friend_decrease"`）

### 请求事件方法

#### 请求信息
- `get_comment()` - 获取请求附言

#### 请求类型判断
- `is_request()` - 是否为请求事件
- `is_friend_request()` - 是否为好友请求
- `is_group_request()` - 是否为群组请求

### 回复功能

#### 基础回复
- `reply(content, method="Text", at_sender=False, reply_to_message=False, at_users=None, reply_to=None, at_all=False, **kwargs)` - 通用回复方法
  - `content`: 发送内容（文本、URL等）
  - `method`: 发送方法，默认 "Text"，可选 "Image"/"Voice"/"Video"/"File" 等
  - `at_sender`: 是否@发送者（自动提取 user_id）
  - `quote`: 是否引用回复当前消息（自动提取 message_id）
  - `at_users`: @用户列表，如 `["user1", "user2"]`
  - `reply_to`: 手动指定回复的消息 ID
  - `at_all`: 是否@全体成员
  - `**kwargs`: 额外参数（如 Mention 方法的 user_id）

- `reply_ob12(message)` - 使用 OneBot12 消息段回复
  - `message`: OneBot12 消息段列表或字典，可配合 MessageBuilder 构建

#### 平台能力查询
- `supports(method)` - 检查当前平台是否支持某发送方法（如 `"Image"`、`"Voice"`），返回 `bool`
- `available_methods()` - 列出当前平台所有可用发送方法，返回方法名列表

#### 转发功能

> **注意**：转发功能需要通过适配器的 Send DSL 实现，Event 包装类本身不提供直接的转发方法。

```python
# 转发消息到群组
adapter = sdk.adapter.get(event.get_platform())
target_id = event.get_group_id()  # 或指定其他群组ID
await adapter.Send.To("group", target_id).Text(event.get_text())
```

### 等待回复功能

- `wait_reply(prompt=None, timeout=60.0, callback=None, validator=None, method="Text")` - 等待用户回复
  - `prompt`: 提示消息，如果提供会发送给用户
  - `timeout`: 等待超时时间（秒），默认60秒
  - `callback`: 回调函数，当收到回复时执行
  - `validator`: 验证函数，用于验证回复是否有效
  - `method`: 发送提示消息的方法，默认 "Text"
  - 返回用户回复的 Event 对象，超时返回 None

#### 交互方法

- `confirm(prompt=None, timeout=60.0, yes_words=None, no_words=None, method="Text", hint=False)` - 确认对话
  - 返回 `True`（确认）/ `False`（否定）/ `None`（超时）
  - 内置中英文确认词自动识别，可自定义词集
  - `method`: 发送方法，默认 "Text"；支持 "Image"/"Markdown" 等非文本方式发送提示
  - `hint`: 是否在提示末尾自动追加确认词提示（如 "（是/否）"），默认 False

- `choose(prompt, options, timeout=60.0, method="Text", options_format="list", merge_prompt=False)` - 选择菜单
  - `options`: 选项文本列表
  - 返回选项索引（0-based），超时返回 `None`
  - `method`: 发送方法；文本类方法 (Text/Markdown/Html) 将选项拼接到 prompt 一条消息发送；富媒体方法先发富媒体内容再发 Text 选项列表
  - `options_format`: 选项格式，支持 `"list"`（默认，每行一个）、`"inline"`（单行 `1.A | 2.B`）或自定义函数 `(list[str]) -> str`
  - `merge_prompt`: 非文本方法时是否强制合并为一条 Text 消息，默认 False

- `collect(fields, timeout_per_field=60.0)` - 表单收集
  - `fields`: 字段列表，每项包含 `key`、`prompt`、可选 `validator`、可选 `method`
  - 返回 `{key: value}` 字典，任一字段超时返回 `None`
  - 每个 field 支持 `method` 键指定发送方法，例如收集图片时用 `{"key": "avatar", "prompt": "请发送头像", "method": "Image"}`
  - 每个 field 可选 `options` 键（列表），提供时该字段变为选择题（自动调用 choose 逻辑）
  - 每个 field 可选 `options_format` 和 `merge_prompt` 键，控制选项格式和消息合并行为`

- `wait_for(event_type="message", condition=None, timeout=60.0)` - 等待任意事件
  - `condition`: 过滤函数，返回 `True` 时匹配
  - 返回匹配的 Event 对象，超时返回 `None`

- `conversation(timeout=60.0)` - 创建多轮对话上下文
  - 返回 `Conversation` 对象，支持 `say()`/`wait()`/`confirm()`/`choose()`/`collect()`/`stop()`
  - `is_active` 属性表示对话是否活跃

#### 交互方法示例

**confirm() - 确认对话：**

```python
@command("delete", help="删除数据")
async def delete_handler(event):
    if await event.confirm("确定要删除所有数据吗？"):
        sdk.storage.delete("all_data")
        await event.reply("数据已删除")
    else:
        await event.reply("已取消")
```

**confirm() - 带提示词：**

```python
# hint=True 会在提示末尾追加 "（是/否）"
if await event.confirm("确定继续？", hint=True):
    await event.reply("已继续")
# 用户看到：确定继续？（是/否）
```

**choose() - 选择菜单：**

```python
@command("color", help="选择颜色")
async def color_handler(event):
    choice = await event.choose("请选择颜色：", ["红色", "绿色", "蓝色"])
    if choice is not None:
        colors = ["红色", "绿色", "蓝色"]
        await event.reply(f"你选择了：{colors[choice]}")
```

**choose() - 选项格式化与消息合并：**

```python
# inline 格式：选项显示在同一行
choice = await event.choose("请选择：", ["A", "B", "C"], options_format="inline")
# 输出：1.A | 2.B | 3.C

# 自定义格式
choice = await event.choose("请选择：", ["猫", "狗"],
    options_format=lambda opts: " / ".join(opts))
# 输出：猫 / 狗

# 非文本方法 + 合并选项到文本
choice = await event.choose("看图选择：", ["猫", "狗"],
    method="Image", merge_prompt=True)
```

**collect() - 表单收集：**

```python
@command("register", help="注册")
async def register_handler(event):
    data = await event.collect([
        {"key": "name", "prompt": "请输入姓名："},
        {"key": "age", "prompt": "请输入年龄：",
         "validator": lambda e: e.get_text().isdigit()},
    ])
    if data:
        await event.reply(f"注册成功！{data['name']}，{data['age']}岁")
```

**非 Text 方法的 reply：**

```python
await event.reply("http://example.com/img.jpg", method="Image")
await event.reply("http://example.com/audio.mp3", method="Voice")

from ErisPulse.Core.Event import MessageBuilder
segments = MessageBuilder.text("看这张图：").image("http://example.com/img.jpg").build()
await event.reply_ob12(segments)
```

> 完整的 Conversation 多轮对话用法请参考 [Conversation 多轮对话](../../advanced/conversation.md)。

### 命令信息

#### 命令基础
- `get_command_name()` - 获取命令名称
- `get_command_args()` - 获取命令参数列表
- `get_command_raw()` - 获取命令原始文本
- `get_command_info()` - 获取完整命令信息字典
- `is_command()` - 是否为命令

### 原始数据

- `get_raw()` - 获取平台原始事件数据
- `get_raw_type()` - 获取平台原始事件类型

### 平台扩展方法

适配器可以为 Event 包装类注册平台专有方法。方法仅在对应平台的 Event 实例上可用，其他平台访问时抛出 `AttributeError`。

平台方法通过 `Event.__getattribute__` 优先于内置方法生效，因此可以覆写 `confirm`、`choose`、`collect`、`wait_reply` 等内置交互方法，提供平台特色实现（如按钮、卡片等）。内置实现作为 `_builtin_*` 函数导出供覆写方调用。

```python
# 邮件事件 - 只有邮件方法
event = Event({"platform": "email", "email_raw": {"subject": "Hello"}})
event.get_subject()      # ✅ 返回 "Hello"
event.get_chat_type()    # ❌ AttributeError

# Telegram 事件 - 只有 Telegram 方法
event = Event({"platform": "telegram", "telegram_raw": {"chat": {"type": "private"}}})
event.get_chat_type()    # ✅ 返回 "private"
event.get_subject()      # ❌ AttributeError

# 内置方法始终可用
event.get_text()         # ✅ 任何平台
event.reply("hi")        # ✅ 任何平台
```

### 查询已注册方法

```python
from ErisPulse.Core.Event import get_platform_event_methods

methods = get_platform_event_methods("email")
# ["get_subject", "get_from", ...]
```

### `hasattr` 和 `dir` 支持

```python
hasattr(event, "get_subject")   # 仅当 platform="email" 时返回 True
"get_subject" in dir(event)     # 同上
```

### 跨平台扩展（通配符）

`register_event_method` 和 `register_event_mixin` 支持传 `"*"` 作为平台名，注册的方法在**所有平台**的 Event 实例上都可用。适合 AI 对话、上下文管理等需要跨平台复用的功能。

```python
from ErisPulse.Core.Event.wrapper import register_event_method

@register_event_method("*")
async def ai_chat(self, prompt: str):
    # self 为 Event 实例，可访问事件数据和内置方法
    await self.reply(f"AI: {prompt}")
```

注册后，任何平台的事件处理器都能调用 `event.ai_chat(...)`。

方法解析优先级（从高到低）：平台特定方法 → 通配符方法 → 内置方法 → 字典键访问。

> 适配器开发者注册扩展方法的方式请参阅 [事件系统 API - 跨平台扩展](../../api-reference/event-system.md#跨平台扩展通配符)。

## 相关文档

- [模块开发入门](getting-started.md) - 创建第一个模块
- [最佳实践](best-practices.md) - 开发高质量模块