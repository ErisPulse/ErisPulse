# Telegram平台特性文档

TelegramAdapter 是基于 Telegram Bot API 构建的适配器，支持多种消息类型和事件处理。

---

## 文档信息

- 对应模块版本: 3.6.5
- 维护者: ErisPulse

## 基本信息

- 平台简介：Telegram 是一个跨平台的即时通讯软件
- 适配器名称：TelegramAdapter
- 支持的协议/API版本：Telegram Bot API
- 会话类型映射：`private` → 发送时用 `user`，`group`/`supergroup` → `group`，`channel` → `channel`

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
| `.HTML(text)` | 发送 HTML 格式消息 | `text: str` |
| `.Sticker(file)` | 发送贴纸 | `file: str (file_id/URL) \| bytes` |
| `.Location(lat, lng)` | 发送位置 | `latitude: float, longitude: float` |
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
| `.AnswerCallback(callback_query_id, text, show_alert)` | 应答回调查询 |

### 原始消息发送

- `.Raw_ob12(message: List[Dict])`：发送 OneBot12 标准格式消息
- `.Raw_json(json_str: str)`：发送原始 JSON 格式消息

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

# 发送位置
await telegram.Send.To("user", user_id).Location(39.9042, 116.4074)
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
| `telegram_chat_join_request` | 加入聊天请求 |
| `telegram_shipping_query` | 运费查询 |
| `telegram_pre_checkout_query` | 预付款查询 |

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
  "telegram_chat": {
    "id": -1002850921906,
    "title": "ErisPulse",
    "username": "erispulse",
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

        # 回复消息
        await event.reply(f"你点击了：{callback_data}")
```

## 扩展字段说明

- 所有特有字段均以 `telegram_` 前缀标识
- 保留原始数据在 `telegram_raw` 字段
- 保留原始事件类型在 `telegram_raw_type` 字段
- 频道消息使用 `detail_type="channel"`
- 私聊消息使用 `detail_type="private"`（发送时需转换为 `user`）
- 话题消息包含 `thread_id` 字段
- `@` 提及使用标准 `mention` 消息段类型（`type: "mention"`），文本中不含 @用户名

## 配置选项

Telegram 适配器支持以下配置选项：

### 基本配置
- `token`: Telegram Bot Token
- `proxy_enabled`: 是否启用代理

### 代理配置
- `proxy.host`: 代理服务器地址
- `proxy.port`: 代理端口
- `proxy.type`: 代理类型 (`"socks4"` 或 `"socks5"`)

### 运行模式

Telegram 适配器仅支持 **Polling（轮询）** 模式，Webhook 模式已移除。

配置示例：
```toml
[Telegram_Adapter]
token = "YOUR_BOT_TOKEN"
proxy_enabled = false

[Telegram_Adapter.proxy]
host = "127.0.0.1"
port = 1080
type = "socks5"