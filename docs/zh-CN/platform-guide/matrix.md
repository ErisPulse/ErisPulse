# Matrix平台特性文档

MatrixAdapter 是基于 [Matrix协议](https://spec.matrix.org/) 构建的适配器，整合了Matrix协议的所有核心功能模块，提供统一的事件处理和消息操作接口。

---

## 文档信息

- 对应模块版本: 1.0.0
- 维护者: ErisPulse

## 基本信息

- 平台简介：Matrix是一个开放的去中心化通信协议，支持私聊、群组等多种场景
- 适配器名称：MatrixAdapter
- 连接方式：Long Polling（通过 Matrix Sync API `/sync`）
- 认证方式：基于 access_token 或 user_id + password 登录获取 token
- 链式修饰支持：支持 `.Reply()`、`.At()`、`.AtAll()` 等链式修饰方法
- OneBot12兼容：支持发送 OneBot12 格式消息

## 配置说明

```toml
# config.toml
[Matrix_Adapter]
homeserver = "https://matrix.org"          # Matrix服务器地址（必填）
access_token = "YOUR_ACCESS_TOKEN"          # 访问令牌（与 user_id+password 二选一）
user_id = ""                                # Matrix用户ID（如 @bot:matrix.org）
password = ""                               # Matrix用户密码
auto_accept_invites = true                  # 是否自动接受房间邀请（可选，默认为true）
```

**配置项说明：**
- `homeserver`：Matrix服务器地址（必填），默认为 `https://matrix.org`
- `access_token`：访问令牌，可从Matrix客户端获取。如果已有 token，直接填写即可
- `user_id`：Matrix用户ID（如 `@bot:matrix.org`），与 `password` 配合使用进行登录
- `password`：Matrix用户密码，用于自动登录获取 access_token
- `auto_accept_invites`：是否自动接受房间邀请，默认为 `true`

**认证方式：**
- 方式一（推荐）：直接提供 `access_token`
- 方式二：提供 `user_id` 和 `password`，适配器会自动调用登录接口获取 token

## 支持的消息发送类型

所有发送方法均通过链式语法实现，例如：
```python
from ErisPulse.Core import adapter
matrix = adapter.get("matrix")

await matrix.Send.To("group", room_id).Text("Hello World!")
```

支持的发送类型包括：
- `.Text(text: str)`：发送纯文本消息。
- `.Image(file: bytes | str)`：发送图片消息，支持文件路径、URL、MXC URI、二进制数据。
- `.Voice(file: bytes | str)`：发送语音消息，支持文件路径、URL、MXC URI、二进制数据。
- `.Video(file: bytes | str)`：发送视频消息，支持文件路径、URL、MXC URI、二进制数据。
- `.File(file: bytes | str, filename: str = "")`：发送文件消息，支持文件路径、URL、MXC URI、二进制数据。
- `.Notice(text: str)`：发送通知消息（Matrix的 m.notice 类型）。
- `.Html(html: str, fallback: str = "")`：发送HTML格式消息，支持富文本内容。
- `.Raw_ob12(message: List[Dict], **kwargs)`：发送 OneBot12 格式消息。

### 链式修饰方法（可组合使用）

链式修饰方法返回 `self`，支持链式调用，必须在最终发送方法前调用：

- `.Reply(message_id: str)`：回复指定消息（通过 Matrix `m.in_reply_to` 关系）。
- `.At(user_id: str)`：@指定用户（通过 Matrix `m.mentions` 字段实现）。
- `.AtAll()`：@房间内所有人（通过 Matrix `@room` 提及实现）。

### 链式调用示例

```python
# 基础发送
await matrix.Send.To("user", dm_room_id).Text("Hello")

# 回复消息
await matrix.Send.To("group", room_id).Reply("$event_id").Text("回复消息")

# @用户
await matrix.Send.To("group", room_id).At("@user:matrix.org").Text("你好")

# @所有人
await matrix.Send.To("group", room_id).AtAll().Text("公告通知")

# 组合使用：回复 + @
await matrix.Send.To("group", room_id).Reply("$event_id").At("@user:matrix.org").Text("复合消息")

# 发送HTML消息
await matrix.Send.To("group", room_id).Html("<h1>标题</h1><p>内容</p>", fallback="标题\n内容")

# 发送通知消息
await matrix.Send.To("group", room_id).Notice("系统通知")
```

### OneBot12消息支持

适配器支持发送 OneBot12 格式的消息，便于跨平台消息兼容：

```python
# 发送 OneBot12 格式消息
ob12_msg = [{"type": "text", "data": {"text": "Hello"}}]
await matrix.Send.To("user", dm_room_id).Raw_ob12(ob12_msg)

# 配合链式修饰
ob12_msg = [{"type": "text", "data": {"text": "回复消息"}}]
await matrix.Send.To("group", room_id).Reply("$event_id").Raw_ob12(ob12_msg)

# 复杂消息
ob12_msg = [
    {"type": "text", "data": {"text": "看这张图片："}},
    {"type": "image", "data": {"file": "https://example.com/image.png"}},
    {"type": "text", "data": {"text": "不错吧？"}}
]
await matrix.Send.To("group", room_id).Raw_ob12(ob12_msg)
```

## 发送方法返回值

所有发送方法均返回一个 Task 对象，可以直接 await 获取发送结果。返回结果遵循 ErisPulse 适配器标准化返回规范：

```python
{
    "status": "ok",           // 执行状态: "ok" 或 "failed"
    "retcode": 0,             // 返回码
    "data": {...},            // 响应数据
    "message_id": "$event_id", // Matrix事件ID
    "message": "",            // 错误信息
    "matrix_raw": {...}       // 原始响应数据
}
```

### 错误码说明

| retcode | 说明 |
|---------|------|
| 0 | 成功 |
| 32000 | 请求超时或媒体上传失败 |
| 33000 | API调用异常 |
| 34000 | API返回了意外格式或业务错误 |

## 特有事件类型

需要 `platform=="matrix"` 检测再使用本平台特性

### 核心差异点

1. **去中心化架构**：Matrix 是一个去中心化的通信协议，用户ID格式为 `@user:server.domain`，房间ID格式为 `!room_id:server.domain`
2. **房间概念**：Matrix 不区分群聊和私聊，所有会话都是"房间"。适配器通过 DM（Direct Message）账户数据自动识别私聊房间
3. **Long Polling 同步**：使用 `/sync` API 进行长轮询获取新事件，而非 WebSocket
4. **MXC URI**：媒体文件通过 `mxc://server.domain/media_id` 格式引用
5. **HTML 富文本**：支持通过 `formatted_body` 发送 HTML 格式消息
6. **表情回应**：支持消息级别的表情回应（Reaction），区别于传统的回复消息
7. **消息编辑**：支持通过 `m.replace` 关系编辑已发送的消息
8. **消息撤回**：支持通过 `m.room.redaction` 撤回/删除消息

### 扩展字段

- 所有特有字段均以 `matrix_` 前缀标识
- 保留原始数据在 `matrix_raw` 字段
- `matrix_raw_type` 标识原始Matrix事件类型（如 `m.room.message`、`m.room.member`）

### 特殊字段示例

```python
# 群组消息
{
  "type": "message",
  "detail_type": "group",
  "user_id": "@user:matrix.org",
  "group_id": "!room_id:matrix.org",
  "matrix_room_id": "!room_id:matrix.org"
}

# 私聊消息
{
  "type": "message",
  "detail_type": "private",
  "user_id": "@user:matrix.org",
  "matrix_room_id": "!dm_room_id:matrix.org"
}

# 表情回应
{
  "type": "notice",
  "detail_type": "matrix_reaction",
  "matrix_reaction_event_id": "$reacted_msg_id",
  "matrix_reaction_key": "👍"
}

# 消息撤回
{
  "type": "notice",
  "detail_type": "matrix_redaction",
  "matrix_redacted_event_id": "$deleted_msg_id"
}

# 消息编辑
{
  "type": "message",
  "detail_type": "group",
  "matrix_edit": true,
  "matrix_original_event_id": "$original_event_id"
}

# 线程消息
{
  "type": "message",
  "detail_type": "group",
  "thread_id": "$thread_root_id"
}
```

### 消息段类型

Matrix消息根据 `msgtype` 自动转换为对应的消息段：

| msgtype | 转换类型 | 说明 |
|---|---|---|
| m.text | `text` | 文本消息 |
| m.notice | `text` | 通知消息 |
| m.emote | `text` | 动作消息 |
| m.image | `image` | 图片消息 |
| m.audio | `voice` | 音频消息 |
| m.video | `video` | 视频消息 |
| m.file | `file` | 文件消息 |
| m.location | `location` | 位置消息 |

消息段结构示例：

```json
// 文本消息（带HTML）
{
  "type": "text",
  "data": {
    "text": "纯文本内容",
    "html": "<b>HTML内容</b>"
  }
}

// 图片消息
{
  "type": "image",
  "data": {
    "url": "mxc://matrix.org/abc123",
    "filename": "photo.png",
    "matrix_mxc": "mxc://matrix.org/abc123",
    "info": {
      "mimetype": "image/png",
      "w": 800,
      "h": 600,
      "size": 123456
    }
  }
}

// 位置消息
{
  "type": "location",
  "data": {
    "latitude": 0.0,
    "longitude": 0.0,
    "matrix_geo_uri": "geo:39.9,116.4",
    "text": "北京市"
  }
}
```

### Event Mixin 方法

MatrixAdapter 注册了以下事件混入方法，可在事件处理中直接调用：

| 方法 | 返回类型 | 说明 |
|------|----------|------|
| `get_room_id()` | `str` | 获取房间ID |
| `get_matrix_event_type()` | `str` | 获取原始Matrix事件类型 |
| `get_matrix_sender()` | `str` | 获取原始发送者ID |
| `get_reaction_key()` | `str` | 获取回应表情 |
| `is_edited()` | `bool` | 判断消息是否为编辑消息 |
| `is_notice()` | `bool` | 判断消息是否为 m.notice 类型 |

```python
@message.on_message()
async def handle_message(event):
    if event.get("platform") != "matrix":
        return

    room_id = event.get_room_id()
    event_type = event.get_matrix_event_type()
    sender = event.get_matrix_sender()
    is_edited = event.is_edited()
    is_notice = event.is_notice()
```

## Sync API 连接

### 同步流程

1. 使用 access_token 或 user_id + password 进行认证
2. 调用 `/_matrix/client/v3/account/whoami` 获取 bot_user_id
3. 发出 connect 元事件
4. 执行初始同步（`/_matrix/client/v3/sync?timeout=0`）获取 `next_batch` token
5. 发现 DM 房间（`/_matrix/client/v3/user/{user_id}/account_data/m.direct`）
6. 开始 Long Polling 同步循环（`/_matrix/client/v3/sync?since={next_batch}&timeout=30000`）
7. 处理每次同步返回的新事件并转换发出

### 心跳机制

- 适配器每 30 秒发出一次 `heartbeat` 元事件
- 连接成功时发出 `connect` 元事件
- 关闭时发出 `disconnect` 元事件

### 房间邀请

- 收到房间邀请（`invite` 状态的房间）时，如果 `auto_accept_invites` 配置为 `true`（默认），适配器会自动加入房间
- 加入房间调用 `/_matrix/client/v3/join/{room_id}` 接口

## 使用示例

### 处理群组消息

```python
from ErisPulse.Core.Event import message
from ErisPulse import sdk

matrix = sdk.adapter.get("matrix")

@message.on_message()
async def handle_group_msg(event):
    if event.get("platform") != "matrix":
        return
    if event.get("detail_type") != "group":
        return

    text = event.get_text()
    room_id = event.get("group_id")

    if text == "hello":
        await matrix.Send.To("group", room_id).Reply(
            event.get("message_id")
        ).Text("Hello!")
```

### 处理表情回应

```python
from ErisPulse.Core.Event import notice

@notice.on_notice()
async def handle_reaction(event):
    if event.get("platform") != "matrix":
        return

    if event.get("detail_type") == "matrix_reaction":
        reaction_key = event.get("matrix_reaction_key")
        reacted_event_id = event.get("matrix_reaction_event_id")
        room_id = event.get_room_id()
        # 处理表情回应...
```

### 发送媒体消息

```python
# 发送图片（URL）
await matrix.Send.To("group", room_id).Image("https://example.com/image.png")

# 发送图片（MXC URI）
await matrix.Send.To("group", room_id).Image("mxc://matrix.org/abc123")

# 发送图片（二进制数据）
with open("image.png", "rb") as f:
    image_bytes = f.read()
await matrix.Send.To("group", room_id).Image(image_bytes)

# 发送图片（本地文件路径）
await matrix.Send.To("group", room_id).Image("/path/to/image.png")

# 发送文件（带文件名）
await matrix.Send.To("group", room_id).File("/path/to/document.pdf", filename="文档.pdf")
```

### 处理消息编辑

```python
@message.on_message()
async def handle_edited_message(event):
    if event.get("platform") != "matrix":
        return

    if event.is_edited():
        original_id = event.get("matrix_original_event_id")
        # 处理编辑消息...
```

### 监听成员变更

```python
@notice.on_notice()
async def handle_member_change(event):
    if event.get("platform") != "matrix":
        return

    detail_type = event.get("detail_type")

    if detail_type == "group_member_increase":
        user_id = event.get("user_id")
        nickname = event.get("user_nickname")
        print(f"用户 {nickname} ({user_id}) 加入了房间")

    elif detail_type == "group_member_decrease":
        user_id = event.get("user_id")
        operator_id = event.get("operator_id")
        print(f"用户 {user_id} 被移除，操作者: {operator_id}")