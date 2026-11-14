# Telegram平台特性文档

TelegramAdapter 是基于 Telegram Bot API 构建的适配器，支持多种消息类型和事件处理。

---

## 文档信息

- 对应模块版本: 4.3.3
- 维护者: ErisPulse
- 最后更新: 2026-11-10

## 基本信息

- 平台简介：Telegram 是一个跨平台的即时通讯软件
- 适配器名称：TelegramAdapter
- 支持的协议/API版本：Telegram Bot API
- 会话类型映射：`private` → 发送时用 `user`，`group`/`supergroup` → `group`，`channel` → `channel`

## 标准化对齐（4.3.3）

本章节说明 4.3.3 版本完成的标准化对齐内容：事件变更、多账户约定、错误码规范与 Send 规范。

### 事件变更

1. **群加入申请事件标准化**：
   - `detail_type` 由 `telegram_chat_join_request` 改为标准 `"group"`，`sub_type="join"`
   - `@request.on_group_request()` 现在能直接命中该事件
   - `request_id` 合成规则不变：`tjr_{chat_id}_{user_id}_{date}`
   - 事件可用 `event.approve()` / `event.reject()` 审批（对应 `approveChatJoinRequest` / `declineChatJoinRequest`）
2. **事件 `self.account_id` 注入**：所有事件携带产生它的账户名，多账户下 `event.reply()` 自动按该账户受理发送
3. **unknown 事件**：`self.user_id` 填 bot_id（与消息事件行为一致）

请求事件接口约定遵循 SDK 标准：[请求与审批动作规范](../standards/request-action-spec.md)。

### 账户与多账户

`call_api` 支持双兼容账户字段：标准字段 `account_id`（ApiDSL.Using 传此名）/ 旧别名 `_account_id`；框架 ApiDSL 自动适配新旧适配器。

```python
from ErisPulse import sdk
telegram = sdk.adapter.get("telegram")

await telegram.Api.Using("main").get_self_info()        # 标准方式指定账户
await telegram.Api.get_self_info(account_id="main")     # 显式传标准字段 account_id
```

### 错误码规范

| retcode | 说明 |
|---------|------|
| 0 | 成功 |
| 33001 | 网络错误（连接失败、超时等） |
| 34100 | 平台拒绝（原始响应保留在 `telegram_raw` 字段） |
| 10002 | 不支持的动作（如 `get_friend_list` / `get_group_list`，Telegram Bot API 无对应接口） |

### Send 规范

- HTML 方法名为 `HTML`，`Html` 为保留别名
- `Location` 签名补全 `title` / `content` 可选参数
- `AnswerCallback` / `Raw_json` 走 send_context 账户：在事件处理链内调用发送 DSL 时自动使用当前事件所属账户发送

## 标准Api动作（Api DSL）

适配器将 OB12 标准动作映射到 Telegram Bot API 并标准化 data 字段：

| OB12 标准动作 | Telegram API | data 字段 |
|--------------|--------------|----------|
| get_self_info | getMe | user_id / user_name / user_displayname |
| get_user_info(user_id) | getChat | user_id / user_name / user_displayname |
| get_group_info(group_id) | getChat | group_id / group_name |
| get_group_member_info(group_id, user_id) | getChatMember | user_id / user_name / telegram_role |
| delete_message(message_id) | deleteMessage | 自动按消息登记表补全 chat_id |
| leave_group(group_id) | leaveChat | - |

扩展动作：get_group_admin_list(group_id)（管理员列表）、get_chat_member_count(chat_id)（成员数）。

```python
from ErisPulse import sdk
telegram = sdk.adapter.get("telegram")

result = await telegram.Api.get_self_info()
result = await telegram.Api.get_group_info(group_id=-100123)
result = await telegram.Api.get_group_admin_list(-100123)
await telegram.Api.delete_message(message_id=55)   # 自动补全 chat_id
result = await telegram.Api.Using("main").get_self_info()
```

> Telegram Bot API 无获取好友列表/群列表接口，get_friend_list/get_group_list 显式返回
> retcode=10002（不支持的动作）。

---

## 请求操作（Request DSL）

处理加群申请，基于 approveChatJoinRequest / declineChatJoinRequest。4.3.3 起 `chat_join_request` 映射为标准 `group` 请求事件（`sub_type="join"`），`@request.on_group_request()` 现在能直接命中：

```python
from ErisPulse.Core.Event import request

@request.on_group_request()
async def handle_join_request(event):
    if event.get("platform") != "telegram":
        return
    # event["request_id"] 为合成标识（tjr_{chat_id}_{user_id}_{date}，规则不变）
    if event.get("sub_type") == "join":
        await event.approve()          # 同意（approveChatJoinRequest）
    # await event.reject()             # 拒绝（declineChatJoinRequest）

# 手动调用（需先收到过对应请求事件以登记上下文）
await telegram.Request(event["request_id"]).accept()
await telegram.Request(event["request_id"]).reject()
await telegram.Request(event["request_id"]).Using("main").accept()
```

---
## 支持的消息发送类型

所有发送方法均通过链式语法实现，例如：
```python
from ErisPulse.Core import adapter
telegram = adapter.get("telegram")

await telegram.Send.To("user", user_id).Text("Hello World!")
```

### 基本发送方法

| 方法 | 说明 | 参数 |
|------|------|------|
| `.Text(text)` | 发送纯文本消息 | `text: str` |
| `.Face(emoji)` | 发送表情骰子 | `emoji: str`（如 🎲 🎯 🏀） |
| `.Markdown(text, content_type)` | 发送 Markdown 格式消息 | `content_type` 默认 `"MarkdownV2"` |
| `.HTML(text)` | 发送 HTML 格式消息（`Html` 为保留别名） | `text: str` |
| `.MergeForward(nodes, title)` | 发送合并转发消息（标题 + 每条 blockquote 引用块，4096 截断） | `nodes: List[Dict]`, `title: str` |
| `.Sticker(file)` | 发送贴纸 | `file: str (file_id/URL) \| bytes` |
| `.Location(lat, lng, title="", content="")` | 发送位置（可选标题与内容） | `latitude: float, longitude: float, title: str, content: str` |
| `.Venue(lat, lng, title, addr)` | 发送地点 | 含标题和地址 |
| `.Contact(phone, first, last)` | 发送联系人 | 含电话号码和姓名 |

### 媒体发送方法

所有媒体方法支持 `bytes`（上传）和 `str`（file_id / URL）两种输入：

| 方法 | 说明 |
|------|------|
| `.Image(file, caption, content_type)` | 发送图片 |
| `.Video(file, caption, content_type)` | 发送视频 |
| `.Voice(file, caption)` | 发送语音 |
| `.Audio(file, caption, content_type)` | 发送音频 |
| `.File(file, caption)` | 发送文件 |
| `.Document(file, caption, content_type)` | File 的别名 |

### 消息管理方法

| 方法 | 说明 |
|------|------|
| `.Edit(message_id, text, content_type)` | 编辑已有消息 |
| `.Recall(message_id)` | 删除指定消息 |
| `.Forward(from_chat_id, message_id)` | 转发消息（保留来源） |
| `.CopyMessage(from_chat_id, message_id)` | 复制消息（不带来源） |
| `.AnswerCallback(callback_query_id, text, show_alert)` | 应答回调查询（走 send_context 账户） |

### 原始消息发送

- `.Raw_ob12(message: List[Dict])`：发送 OneBot12 标准格式消息
- `.Raw_json(json_str: str)`：发送原始 JSON 格式消息（走 send_context 账户）

### 链式修饰方法

| 方法 | 说明 |
|------|------|
| `.At(user_id)` | @指定用户（通过 Telegram entities 实现，可多次调用） |
| `.AtAll()` | @全体成员（发送 `@All` 文本） |
| `.Reply(message_id)` | 回复指定消息 |
| `.Keyboard(inline_keyboard)` | 设置内联键盘（`list[list[dict]]`） |
| `.ProtectContent(protect)` | 保护内容（防止转发和保存） |
| `.Silent(silent)` | 静默发送（不通知用户） |

### 发送示例

```python
# 基本文本发送
await telegram.Send.To("user", user_id).Text("Hello World!")

# 带内联键盘的消息
from ErisPulse import sdk
telegram = sdk.adapter.get("telegram")
keyboard = [
    [{"text": "按钮1", "callback_data": "btn1"}, {"text": "按钮2", "callback_data": "btn2"}],
    [{"text": "访问官网", "url": "https://example.com"}],
]
await telegram.Send.To("group", group_id).Keyboard(keyboard).Text("请选择：")

# 媒体发送（URL 方式）
await telegram.Send.To("group", group_id).Image("https://example.com/image.jpg", caption="图片")

# @用户
await telegram.Send.To("group", group_id).At("6117725680").Text("你好！")

# 回复 + 保护内容
await telegram.Send.To("group", group_id).Reply("12345").ProtectContent().Text("机密消息")

# 静默发送
await telegram.Send.To("group", group_id).Silent().Text("静默通知")

# HTML 格式消息（Html 为旧名别名）
await telegram.Send.To("user", user_id).HTML("<b>加粗</b> <i>斜体</i>")

# 发送位置（带标题）
await telegram.Send.To("user", user_id).Location(39.9042, 116.4074, title="天安门", content="北京市中心")

# 应答回调查询
await telegram.Send.AnswerCallback(callback_query_id, text="已处理", show_alert=False)

# OneBot12 组合消息
ob12_message = [
    {"type": "text", "data": {"text": "复杂消息："}},
    {"type": "mention", "data": {"user_id": "6117725680", "user_name": "用户名"}},
    {"type": "reply", "data": {"message_id": "12345"}},
    {"type": "image", "data": {"file": "https://http.cat/200"}}
]
await telegram.Send.To("group", group_id).Raw_ob12(ob12_message)

# 发送贴纸
await telegram.Send.To("user", user_id).Sticker("CAACAgIAAxkBAA...")  # file_id
```

## 特有事件类型

Telegram 事件转换遵循 OneBot12 标准，同时通过 `telegram_` 前缀提供平台扩展。

### 消息事件 detail_type 映射

| Telegram chat.type | OneBot12 detail_type | 发送目标类型 |
|---|---|---|
| `private` | `private` | `user` |
| `group` | `group` | `group` |
| `supergroup` | `group` | `group` |
| `channel` | `channel` | `channel` |

### 特有事件类型

| detail_type | 说明 |
|---|---|
| `telegram_callback_query` | 回调查询（内联键盘按钮点击） |
| `telegram_inline_query` | 内联查询 |
| `telegram_chosen_inline_result` | 选择的内联结果 |
| `telegram_poll` | 投票事件 |
| `telegram_poll_answer` | 投票答案 |
| `telegram_my_chat_member` | Bot 自身成员状态变更 |
| `telegram_chat_member` | 聊天成员变更 |
| `telegram_shipping_query` | 运费查询 |
| `telegram_pre_checkout_query` | 预付款查询 |

> 加入聊天请求（chat_join_request）已标准化为 `group` 请求事件（`sub_type="join"`），
> 不再使用 `telegram_chat_join_request` 作为 detail_type；相关平台字段
> （`telegram_chat_join_request_id`、`telegram_chat` 等）仍保留。

### 标准消息段类型

转换后的消息段使用 OneBot12 标准格式：

| 消息段类型 | 说明 | data 字段 |
|---|---|---|
| `text` | 纯文本（不含 @用户名） | `text` |
| `mention` | @用户（标准 OB12） | `user_id`, `user_name` |
| `reply` | 回复引用 | `message_id`, `user_id` |
| `image` | 图片 | `file_id`, `url` |
| `video` | 视频 | `file_id`, `url`, `duration`, `width`, `height` |
| `voice` | 语音 | `file_id`, `url`, `duration` |
| `audio` | 音频 | `file_id`, `url`, `duration`, `title`, `performer` |
| `file` | 文件 | `file_id`, `url`, `file_name`, `file_size`, `mime_type` |
| `location` | 位置 | `latitude`, `longitude`, 可选 `title`, `address` |

### 平台扩展消息段

以 `telegram_` 前缀标识的扩展消息段：

| 消息段类型 | 说明 | data 字段 |
|---|---|---|
| `telegram_sticker` | 贴纸 | `file_id`, `emoji`, `sticker_type`, `url` |
| `telegram_animation` | GIF 动画 | `file_id`, `url`, `duration`, `caption` |
| `telegram_contact` | 联系人 | `phone_number`, `first_name`, `last_name`, `user_id` |
| `telegram_inline_keyboard` | 内联键盘 | `inline_keyboard` |

### 事件示例

#### 群聊消息（含 @提及）
```python
{
  "type": "message",
  "detail_type": "group",
  "platform": "telegram",
  "user_id": "6117725680",
  "user_nickname": "WSu2059",
  "group_id": "-1002850921906",
  "message_id": "172",
  "message": [
    {"type": "text", "data": {"text": "/it.echo "}},
    {"type": "mention", "data": {"user_id": "", "user_name": "@nm123_91178"}}
  ],
  "alt_message": "/it.echo @nm123_91178",
  "self": {
    "platform": "telegram",
    "user_id": "6117725680",
    "account_id": "default"
  },
  "telegram_chat": {
    "id": -1002850921906,
    "title": "ErisPulse",
    "username": "erispulse",
    "type": "supergroup"
  }
}
```

#### 群加入申请事件（标准化后）
```python
{
  "type": "request",
  "detail_type": "group",
  "sub_type": "join",
  "platform": "telegram",
  "user_id": "6117725680",
  "user_nickname": "申请者昵称",
  "request_id": "tjr_-1002850921906_6117725680_1731212345",
  "group_id": "-1002850921906",
  "comment": "邀请链接名称",
  "self": {
    "platform": "telegram",
    "user_id": "6117725680",
    "account_id": "default"
  },
  "telegram_chat_join_request_id": "",
  "telegram_chat": {
    "id": -1002850921906,
    "title": "ErisPulse",
    "type": "supergroup"
  }
}
```

#### 回调查询事件
```python
{
  "type": "notice",
  "detail_type": "telegram_callback_query",
  "user_id": "123456",
  "user_nickname": "YingXinche",
  "telegram_callback_id": "cb_123",
  "telegram_callback_data": "callback_data",
  "message_id": "msg_456"
}
```

#### 内联查询事件
```python
{
  "type": "request",
  "detail_type": "telegram_inline_query",
  "user_id": "789012",
  "user_nickname": "YingXinche",
  "telegram_query_id": "iq_789",
  "telegram_query_text": "search_text",
  "telegram_query_offset": "0"
}
```

#### 带内联键盘的消息
```python
{
  "type": "message",
  "detail_type": "group",
  "message": [
    {"type": "text", "data": {"text": "请选择："}},
    {
      "type": "telegram_inline_keyboard",
      "data": {
        "inline_keyboard": [
          [{"text": "按钮1", "callback_data": "btn1"}],
          [{"text": "访问", "url": "https://example.com"}]
        ]
      }
    }
  ]
}
```

## Event Mixin 扩展方法

适配器注册了以下平台专有方法，仅在 `platform == "telegram"` 时可用：

### 消息相关

| 方法 | 返回类型 | 说明 |
|------|----------|------|
| `is_bot_message()` | `bool` | 判断消息是否来自机器人 |
| `is_edited_message()` | `bool` | 判断是否为编辑过的消息 |
| `is_topic_message()` | `bool` | 判断是否为话题/Topic 消息 |
| `get_update_id()` | `int` | 获取 Telegram update ID |
| `get_chat_title()` | `str` | 获取聊天标题 |
| `get_chat_username()` | `str` | 获取聊天用户名 |
| `get_forward_from()` | `dict` | 获取转发来源信息 |
| `get_topic_id()` | `str` | 获取话题 ID |

### 回调查询相关

| 方法 | 返回类型 | 说明 |
|------|----------|------|
| `get_callback_data()` | `str` | 获取回调查询的 callback_data |
| `get_callback_id()` | `str` | 获取回调查询 ID（用于应答） |

### 消息段数据提取

| 方法 | 返回类型 | 说明 |
|------|----------|------|
| `get_inline_keyboard()` | `list` | 获取消息中的内联键盘 |
| `get_sticker_info()` | `dict` | 获取贴纸信息 |
| `get_contact_info()` | `dict` | 获取联系人信息 |
| `get_location()` | `dict` | 获取位置信息 |

### 使用示例

```python
from ErisPulse.Core.Event import message, notice

@message.on_message()
async def handle_message(event):
    if event.get("platform") != "telegram":
        return

    # 消息属性
    if event.is_bot_message():
        return  # 忽略机器人消息

    if event.is_edited_message():
        print("这是编辑过的消息")

    # 聊天信息
    title = event.get_chat_title()
    username = event.get_chat_username()

    # 转发来源
    forward = event.get_forward_from()

    # 消息段数据
    sticker = event.get_sticker_info()
    contact = event.get_contact_info()
    location = event.get_location()
    keyboard = event.get_inline_keyboard()

    # 话题
    if event.is_topic_message():
        topic_id = event.get_topic_id()

@notice.on_notice()
async def handle_notice(event):
    if event.get("platform") != "telegram":
        return

    if event.get("detail_type") == "telegram_callback_query":
        callback_data = event.get_callback_data()
        callback_id = event.get_callback_id()

        # 应答回调查询
        telegram = sdk.adapter.get("telegram")
        await telegram.Send.AnswerCallback(callback_id, text="已点击")

        # 回复消息（多账户下自动按事件所属账户受理）
        await event.reply(f"你点击了：{callback_data}")
```

## 扩展字段说明

- 所有特有字段均以 `telegram_` 前缀标识
- 保留原始数据在 `telegram_raw` 字段
- 保留原始事件类型在 `telegram_raw_type` 字段
- 事件 `self.account_id` 为产生事件的账户名（多账户下 `event.reply()` 自动按该账户受理）
- 频道消息使用 `detail_type="channel"`
- 私聊消息使用 `detail_type="private"`（发送时需转换为 `user`）
- 话题消息包含 `thread_id` 字段
- `@` 提及使用标准 `mention` 消息段类型（`type: "mention"`），文本中不含 @用户名

## 配置选项

Telegram 适配器支持多账号配置：

### 配置示例
```toml
[Telegram_Adapter.accounts.default]
token = "YOUR_BOT_TOKEN"
enabled = true

[Telegram_Adapter.accounts.bot2]
token = "ANOTHER_BOT_TOKEN"
enabled = true
```

### 运行模式

Telegram 适配器仅支持 **Polling（轮询）** 模式，Webhook 模式已移除。

### 代理配置

如需通过代理连接 Telegram API，请使用系统级代理（环境变量 `ALL_PROXY` / `HTTPS_PROXY`）。

### 旧版配置迁移

旧版单 token 配置会自动兼容：
```toml
# 旧版格式（仍可使用，但建议迁移）
[Telegram_Adapter]
token = "YOUR_BOT_TOKEN"
```

建议迁移到新格式：
```toml
[Telegram_Adapter.accounts.default]
token = "YOUR_BOT_TOKEN"
enabled = true
```
