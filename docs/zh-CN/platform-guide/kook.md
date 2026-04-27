# Kook平台特性文档

KookAdapter 是基于Kook（开黑啦）Bot WebSocket 协议构建的适配器，整合了Kook所有功能模块，提供统一的事件处理和消息操作接口。

---

## 文档信息

- 对应模块版本: 0.1.0
- 维护者: ShanFish

## 基本信息

- 平台简介：Kook（原开黑啦）是一款支持文字、语音、视频通信的社区平台，提供完整的 Bot 开发接口
- 适配器名称：KookAdapter
- 连接方式：WebSocket 长连接（通过Kook网关）
- 认证方式：基于 Bot Token 进行身份认证
- 链式修饰支持：支持 `.Reply()`、`.At()`、`.AtAll()` 等链式修饰方法
- OneBot12兼容：支持发送 OneBot12 格式消息

## 配置说明

```toml
# config.toml
[KookAdapter]
token = "YOUR_BOT_TOKEN"     # Kook Bot Token（必填，格式: Bot xxx/xxx）
bot_id = ""                   # Bot 用户ID（可选，不填则从 token 中解析）
compress = true               # 是否启用 WebSocket 压缩（可选，默认为 true）
```

**配置项说明：**
- `token`：Kook Bot 的 Token（必填），从 [Kook开发者中心](https://developer.kookapp.cn) 获取，格式为 `Bot xxx/xxx`
- `bot_id`：Bot 的用户ID（可选），如果不填写，适配器会尝试从 token 中自动解析。建议手动填写以确保准确性
- `compress`：是否启用 WebSocket 数据压缩（可选，默认为 `true`），启用后使用 zlib 解压数据

**API环境：**
- Kook API 基础地址：`https://www.kookapp.cn/api/v3`
- WebSocket 网关通过 API 动态获取：`POST /gateway/index`

## 支持的消息发送类型

所有发送方法均通过链式语法实现，例如：
```python
from ErisPulse.Core import adapter
kook = adapter.get("kook")

await kook.Send.To("group", channel_id).Text("Hello World!")
```

支持的发送类型包括：
- `.Text(text: str)`：发送纯文本消息。
- `.Image(file: bytes | str)`：发送图片消息，支持文件路径、URL、二进制数据。
- `.Video(file: bytes | str)`：发送视频消息，支持文件路径、URL、二进制数据。
- `.File(file: bytes | str, filename: str = None)`：发送文件消息，支持文件路径、URL、二进制数据。
- `.Voice(file: bytes | str)`：发送语音消息，支持文件路径、URL、二进制数据。
- `.Markdown(text: str)`：发送KMarkdown格式消息。
- `.Card(card_data: dict)`：发送卡片消息（CardMessage）。
- `.Raw_ob12(message: List[Dict], **kwargs)`：发送 OneBot12 格式消息。

### 链式修饰方法（可组合使用）

链式修饰方法返回 `self`，支持链式调用，必须在最终发送方法前调用：

- `.Reply(message_id: str)`：回复（引用）指定消息。
- `.At(user_id: str)`：@指定用户，可多次调用以@多个用户。
- `.AtAll()`：@所有人。

### 链式调用示例

```python
# 基础发送
await kook.Send.To("group", channel_id).Text("Hello")

# 回复消息
await kook.Send.To("group", channel_id).Reply(msg_id).Text("回复消息")

# @用户
await kook.Send.To("group", channel_id).At("user_id").Text("你好")

# @多个用户
await kook.Send.To("group", channel_id).At("user1").At("user2").Text("多用户@")

# @全体
await kook.Send.To("group", channel_id).AtAll().Text("公告")

# 组合使用
await kook.Send.To("group", channel_id).Reply(msg_id).At("user_id").Text("复合消息")
```

### OneBot12消息支持

适配器支持发送 OneBot12 格式的消息，便于跨平台消息兼容：

```python
# 发送 OneBot12 格式消息
ob12_msg = [{"type": "text", "data": {"text": "Hello"}}]
await kook.Send.To("group", channel_id).Raw_ob12(ob12_msg)

# 配合链式修饰
ob12_msg = [{"type": "text", "data": {"text": "回复消息"}}]
await kook.Send.To("group", channel_id).Reply(msg_id).Raw_ob12(ob12_msg)

# 在 Raw_ob12 中使用 mention 和 reply 消息段
ob12_msg = [
    {"type": "text", "data": {"text": "Hello "}},
    {"type": "mention", "data": {"user_id": "user_id"}},
    {"type": "reply", "data": {"message_id": "msg_id"}}
]
await kook.Send.To("group", channel_id).Raw_ob12(ob12_msg)
```

### 额外操作方法

除发送消息外，Kook适配器还支持以下操作：

```python
# 编辑消息（仅支持 KMarkdown type=9 和 CardMessage type=10）
await kook.Send.To("group", channel_id).Edit(msg_id, "**更新后的内容**")

# 撤回消息
await kook.Send.To("group", channel_id).Recall(msg_id)

# 上传文件（获取文件URL）
result = await kook.Send.Upload("C:/path/to/file.jpg")
file_url = result["data"]["url"]
```

## 发送方法返回值

所有发送方法均返回一个 Task 对象，可以直接 await 获取发送结果。返回结果遵循 ErisPulse 适配器标准化返回规范：

```python
{
    "status": "ok",           // 执行状态: "ok" 或 "failed"
    "retcode": 0,             // 返回码（Kook API 的 code）
    "data": {...},            // 响应数据
    "message_id": "xxx",      // 消息ID
    "message": "",            // 错误信息
    "kook_raw": {...}         // 原始响应数据
}
```

### 错误码说明

| retcode | 说明 |
|---------|------|
| 0 | 成功 |
| 40100 | Token 无效或未提供 |
| 40101 | Token 过期 |
| 40102 | Token 与 Bot 不匹配 |
| 40103 | 缺少权限 |
| 40000 | 参数错误 |
| 40400 | 目标不存在 |
| 40300 | 无权限操作 |
| 50000 | 服务器内部错误 |
| -1 | 适配器内部错误 |

## 特有事件类型

需要 `platform=="kook"` 检测再使用本平台特性

### 核心差异点

1. **频道系统**：Kook 使用服务器（Guild）和频道（Channel）两层结构，频道是消息的基本发送目标
2. **消息类型**：Kook 支持文本(1)、图片(2)、视频(3)、文件(4)、语音(8)、KMarkdown(9)、卡片消息(10)等多种消息类型
3. **私信系统**：Kook 区分频道消息和私信消息，使用不同的 API 端点
4. **消息序号**：Kook WebSocket 使用 `sn` 序号保证消息有序性，支持消息暂存和乱序重排
5. **消息编辑与撤回**：支持编辑已发送的消息（仅 KMarkdown 和 CardMessage）和撤回消息

### 扩展字段

- 所有特有字段均以 `kook_` 前缀标识
- 保留原始数据在 `kook_raw` 字段
- `kook_raw_type` 标识原始Kook消息类型编号（如 `1` 为文本、`255` 为通知事件）

### 特殊字段示例

```python
# 频道文本消息
{
  "type": "message",
  "detail_type": "group",
  "user_id": "用户ID",
  "group_id": "频道ID",
  "channel_id": "频道ID",
  "message_id": "消息ID",
  "kook_raw": {...},
  "kook_raw_type": "1",
  "message": [
    {"type": "text", "data": {"text": "Hello"}}
  ],
  "alt_message": "Hello"
}

# 带图片的消息
{
  "type": "message",
  "detail_type": "group",
  "user_id": "用户ID",
  "group_id": "频道ID",
  "channel_id": "频道ID",
  "message_id": "消息ID",
  "kook_raw": {...},
  "kook_raw_type": "2",
  "message": [
    {"type": "image", "data": {"file": "图片URL", "url": "图片URL"}}
  ],
  "alt_message": "图片内容"
}

# KMarkdown消息
{
  "type": "message",
  "detail_type": "group",
  "user_id": "用户ID",
  "group_id": "频道ID",
  "message_id": "消息ID",
  "kook_raw": {...},
  "kook_raw_type": "9",
  "message": [
    {"type": "text", "data": {"text": "解析后的纯文本"}}
  ]
}

# 卡片消息
{
  "type": "message",
  "detail_type": "group",
  "user_id": "用户ID",
  "group_id": "频道ID",
  "message_id": "消息ID",
  "kook_raw": {...},
  "kook_raw_type": "10",
  "message": [
    {"type": "json", "data": {"data": "卡片JSON内容"}}
  ]
}

# 私聊消息
{
  "type": "message",
  "detail_type": "private",
  "user_id": "用户ID",
  "message_id": "消息ID",
  "kook_raw": {...},
  "kook_raw_type": "1",
  "message": [
    {"type": "text", "data": {"text": "私聊内容"}}
  ]
}
```

### 消息段类型

Kook 的消息类型根据 `type` 字段自动转换为对应消息段：

| Kook type | 转换类型 | 说明 |
|---|---|---|
| 1 | `text` | 文本消息 |
| 2 | `image` | 图片消息 |
| 3 | `video` | 视频消息 |
| 4 | `file` | 文件消息 |
| 8 | `record` | 语音消息 |
| 9 | `text` | KMarkdown消息（提取纯文本内容） |
| 10 | `json` | 卡片消息（原始JSON） |

消息段结构示例：
```json
{
  "type": "image",
  "data": {
    "file": "图片URL",
    "url": "图片URL"
  }
}
```

### Mention消息段

当消息中包含@信息时，会在消息段前插入 `mention` 消息段：

```json
{
  "type": "mention",
  "data": {
    "user_id": "被@用户ID"
  }
}
```

### mention_all消息段

当消息为@全体时，会插入 `mention_all` 消息段：

```json
{
  "type": "mention_all",
  "data": {}
}
```

## WebSocket连接

### 连接流程

1. 使用 Bot Token 调用 `POST /gateway/index` 获取 WebSocket 网关地址
2. 连接到 WebSocket 网关
3. 收到 HELLO（s=1）信令，验证连接状态
4. 开始心跳循环（PING，s=2，每30秒一次）
5. 接收消息事件（s=0），使用 sn 序号保证有序性
6. 收到心跳响应 PONG（s=3）

### 信令类型

| 信令 | s值 | 说明 |
|------|-----|------|
| HELLO | 1 | 服务器欢迎信令，连接成功后收到 |
| PING | 2 | 客户端心跳，每30秒发送一次，携带当前 sn |
| PONG | 3 | 心跳响应 |
| RESUME | 4 | 恢复连接信令，携带 sn 恢复会话 |
| RECONNECT | 5 | 服务器要求重连，需要重新获取网关 |
| RESUME_ACK | 6 | RESUME 成功响应 |

### 断线重连

- 连接异常断开后，适配器自动重试连接
- 如果之前有 `sn > 0`，会首先尝试 RESUME（s=4）恢复连接
- RESUME 失败后，重置 sn 和消息队列，重新进行全新连接（HELLO 流程）
- 收到 RECONNECT（s=5）信令时，清空状态并重新连接

### 消息序号机制

Kook WebSocket 使用 `sn`（递增序号）保证消息有序性：

- 每收到一条消息事件（s=0），sn 递增
- 如果收到的消息 sn 不连续，进入暂存模式
- 暂存区中的消息按 sn 排序，等待缺失消息到达后按序处理
- 暂存区清空后自动退出暂存模式

## 使用示例

### 处理频道消息

```python
from ErisPulse.Core.Event import message
from ErisPulse import sdk

kook = sdk.adapter.get("kook")

@message.on_message()
async def handle_group_msg(event):
    if event.get("platform") != "kook":
        return
    if event.get("detail_type") != "group":
        return

    text = event.get_text()
    channel_id = event.get("group_id")

    if text == "hello":
        await kook.Send.To("group", channel_id).Text("Hello!")
```

### 处理私聊消息

```python
@message.on_message()
async def handle_private_msg(event):
    if event.get("platform") != "kook":
        return
    if event.get("detail_type") != "private":
        return

    text = event.get_text()
    user_id = event.get("user_id")

    await kook.Send.To("user", user_id).Text(f"你说了: {text}")
```

### 处理通知事件（表情回应等）

```python
from ErisPulse.Core.Event import notice

@notice.on_notice()
async def handle_notice(event):
    if event.get("platform") != "kook":
        return

    sub_type = event.get("sub_type")

    if sub_type == "added_reaction":
        emoji = event.get("emoji", {})
        user_id = event.get("user_id")
        msg_id = event.get("message_id")
        print(f"用户 {user_id} 对消息 {msg_id} 添加了表情回应")

    elif sub_type == "deleted_reaction":
        emoji = event.get("emoji", {})
        user_id = event.get("user_id")
        msg_id = event.get("message_id")
        print(f"用户 {user_id} 移除了消息 {msg_id} 的表情回应")
```

### 发送媒体消息

```python
# 发送图片（URL）
await kook.Send.To("group", channel_id).Image("https://example.com/image.png")

# 发送图片（二进制）
with open("image.png", "rb") as f:
    image_bytes = f.read()
await kook.Send.To("group", channel_id).Image(image_bytes)

# 发送视频
await kook.Send.To("group", channel_id).Video("https://example.com/video.mp4")

# 发送文件
await kook.Send.To("group", channel_id).File("https://example.com/file.pdf", filename="document.pdf")

# 发送语音
await kook.Send.To("group", channel_id).Voice("https://example.com/voice.mp3")
```

### 发送KMarkdown和卡片消息

```python
# KMarkdown
await kook.Send.To("group", channel_id).Markdown("**粗体** *斜体* [链接](https://example.com)")

# 卡片消息
card = {
    "type": "card",
    "theme": "primary",
    "size": "lg",
    "modules": [
        {"type": "header", "text": {"type": "plain-text", "content": "标题"}},
        {"type": "section", "text": {"type": "kmarkdown", "content": "内容"}}
    ]
}
await kook.Send.To("group", channel_id).Card(card)
```

### 消息编辑与撤回

```python
# 发送消息
result = await kook.Send.To("group", channel_id).Markdown("**原始内容**")
msg_id = result["data"]["msg_id"]

# 编辑消息（仅支持 KMarkdown 和 CardMessage）
await kook.Send.To("group", channel_id).Edit(msg_id, "**更新后的内容**")

# 撤回消息
await kook.Send.To("group", channel_id).Recall(msg_id)
```

### 处理私信消息的编辑和删除通知

```python
@notice.on_notice()
async def handle_private_notice(event):
    if event.get("platform") != "kook":
        return

    sub_type = event.get("sub_type")

    if sub_type == "updated_private_message":
        msg_id = event.get("message_id")
        content = event.get("content")
        print(f"私信消息已更新: {msg_id}, 新内容: {content}")

    elif sub_type == "deleted_private_message":
        msg_id = event.get("message_id")
        print(f"私信消息已删除: {msg_id}")
```
