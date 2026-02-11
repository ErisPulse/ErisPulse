# Telegram平台特性文档

TelegramAdapter 是基于 Telegram Bot API 构建的适配器，支持多种消息类型和事件处理。

---

## 文档信息

- 对应模块版本: 3.5.0
- 维护者: ErisPulse

## 基本信息

- 平台简介：Telegram 是一个跨平台的即时通讯软件
- 适配器名称：TelegramAdapter
- 支持的协议/API版本：Telegram Bot API

## 支持的消息发送类型

所有发送方法均通过链式语法实现，例如：
```python
from ErisPulse.Core import adapter
telegram = adapter.get("telegram")

await telegram.Send.To("user", user_id).Text("Hello World!")
```

### 基本发送方法

- `.Text(text: str)`：发送纯文本消息。
- `.Face(emoji: str)`：发送表情消息。
- `.Markdown(text: str, content_type: str = "MarkdownV2")`：发送Markdown格式消息。
- `.HTML(text: str)`：发送HTML格式消息。

### 媒体发送方法

所有媒体方法支持两种输入方式：
- **URL 方式**：直接传入字符串 URL
- **文件上传**：传入 bytes 类型数据

- `.Image(file: bytes | str, caption: str = "", content_type: str = None)`：发送图片消息
- `.Video(file: bytes | str, caption: str = "", content_type: str = None)`：发送视频消息
- `.Voice(file: bytes | str, caption: str = "")`：发送语音消息
- `.Audio(file: bytes | str, caption: str = "", content_type: str = None)`：发送音频消息
- `.File(file: bytes | str, caption: str = "")`：发送文件消息
- `.Document(file: bytes | str, caption: str = "", content_type: str = None)`：发送文档消息（File 的别名）

### 消息管理方法

- `.Edit(message_id: int, text: str, content_type: str = None)`：编辑已有消息。
- `.Recall(message_id: int)`：删除指定消息。

### 原始消息发送

- `.Raw_ob12(message: List[Dict])`：发送 OneBot12 标准格式消息
  - 支持复杂组合消息（文本 + @用户 + 回复 + 媒体）
  - 自动将文本作为媒体消息的 caption
- `.Raw_json(json_str: str)`：发送原始 JSON 格式消息

### 链式修饰方法

- `.At(user_id: str)`：@指定用户（可多次调用）
- `.AtAll()`：@全体成员
- `.Reply(message_id: str)`：回复指定消息

### 方法名映射

发送方法支持大小写不敏感调用，通过映射表自动转换为标准方法名：
```python
# 以下写法等效
telegram.Send.To("group", 123).Text("hello")
telegram.Send.To("group", 123).text("hello")
telegram.Send.To("group", 123).TEXT("hello")
```

### 发送示例

```python
# 基本文本发送
await telegram.Send.To("group", group_id).Text("Hello World!")

# 媒体发送（URL 方式）
await telegram.Send.To("group", group_id).Image("https://example.com/image.jpg", caption="这是一张图片")

# 媒体发送（文件上传）
with open("image.jpg", "rb") as f:
    await telegram.Send.To("group", group_id).Image(f.read())

# @用户
await telegram.Send.To("group", group_id).At("6117725680").Text("你好！")

# 回复消息
await telegram.Send.To("group", group_id).Reply("12345").Text("回复内容")

# 组合使用
await telegram.Send.To("group", group_id).Reply("12345").At("6117725680").Image("https://example.com/image.jpg", caption="看这张图")

# OneBot12 组合消息
ob12_message = [
    {"type": "text", "data": {"text": "复杂组合消息："}},
    {"type": "mention", "data": {"user_id": "6117725680", "name": "用户名"}},
    {"type": "reply", "data": {"message_id": "12345"}},
    {"type": "image", "data": {"file": "https://http.cat/200"}}
]
await telegram.Send.To("group", group_id).Raw_ob12(ob12_message)
```

### 不支持的方法提示

调用不支持的发送方法时，会自动发送文本提示：
```python
# 不支持的发送类型
await telegram.Send.To("group", group_id).UnknownMethod("data")
# 将发送：[不支持的发送类型] 方法名: UnknownMethod, 参数: [...]
```

## 特有事件类型

Telegram事件转换到OneBot12协议，其中标准字段完全遵守OneBot12协议，但存在以下差异：

### 核心差异点

1. 特有事件类型：
   - 内联查询：telegram_inline_query
   - 回调查询：telegram_callback_query
   - 投票事件：telegram_poll
   - 投票答案：telegram_poll_answer

2. 扩展字段：
   - 所有特有字段均以telegram_前缀标识
   - 保留原始数据在telegram_raw字段
   - 频道消息使用detail_type="channel"

### 事件监听方式

Telegram适配器支持两种方式监听事件：

```python
# 使用原始事件名
@sdk.adapter.Telegram.on("message")
async def handle_message(event):
    pass

# 使用映射后的事件名
@sdk.adapter.Telegram.on("message")
async def handle_message(event):
    pass
```

### 特殊字段示例

```python
# 回调查询事件
{
  "type": "notice",
  "detail_type": "telegram_callback_query",
  "user_id": "123456",
  "user_nickname": "YingXinche",
  "telegram_callback_data": {
    "id": "cb_123",
    "data": "callback_data",
    "message_id": "msg_456"
  }
}

# 内联查询事件
{
  "type": "notice",
  "detail_type": "telegram_inline_query",
  "user_id": "789012",
  "user_nickname": "YingXinche",
  "telegram_inline_query": {
    "id": "iq_789",
    "query": "search_text",
    "offset": "0"
  }
}

# 频道消息
{
  "type": "message",
  "detail_type": "channel",
  "message_id": "msg_345",
  "channel_id": "channel_123",
  "telegram_chat": {
    "title": "News Channel",
    "username": "news_official"
  }
}
```

## 扩展字段说明

- 所有特有字段均以 `telegram_` 前缀标识
- 保留原始数据在 `telegram_raw` 字段
- 频道消息使用 `detail_type="channel"`
- 消息内容中的实体（如粗体、链接等）会转换为相应的消息段
- 回复消息会添加 `telegram_reply` 类型的消息段

## 配置选项

Telegram 适配器支持以下配置选项：

### 基本配置
- `token`: Telegram Bot Token
- `proxy_enabled`: 是否启用代理

### 代理配置
- `proxy.host`: 代理服务器地址
- `proxy.port`: 代理端口
- `proxy.type`: 代理类型 ("socks4" 或 "socks5")

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
```