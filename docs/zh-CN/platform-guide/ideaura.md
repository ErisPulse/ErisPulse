# 花枫咖啡馆（Ideaura）平台特性文档

IdeauraAdapter 是基于花枫咖啡馆（Allons）平台 API 构建的适配器，整合了所有平台功能模块，提供统一的事件处理和消息操作接口。

---

## 文档信息

- 对应模块: ErisPulse-Ideaura
- 维护者: ErisPulse

## 基本信息

- 平台简介：花枫咖啡馆（Allons）是一个即时通讯平台
- 适配器名称：IdeauraAdapter
- 多账户支持：支持通过 token 或 email/password 配置多个账户
- 链式修饰支持：支持 `.At()`、`.AtAll()`、`.Reply()` 等链式修饰方法
- OneBot12兼容：支持发送 OneBot12 格式消息

## 支持的消息发送类型

所有发送方法均通过链式语法实现，例如：
```python
from ErisPulse.Core import adapter
ideaura = adapter.get("ideaura")

await ideaura.Send.To("group", "chatroom").Text("Hello World!")
```

支持的发送类型包括：
- `.Text(text: str)`：发送纯文本消息。
- `.Image(file, filename: str = None)`：发送图片消息，支持 bytes/URL/本地路径。
- `.Video(file, filename: str = None)`：发送视频消息，支持 bytes/URL/本地路径。
- `.File(file, filename: str = None)`：发送文件消息，支持 bytes/URL/本地路径。
- `.Voice(file, filename: str = None)`：发送语音消息（作为文件发送）。
- `.Face(face_id: str)`：发送表情（以纯文本形式发送 emoji）。
- `.Markdown(text: str)`：发送 Markdown 格式消息。
- `.Html(html: str)`：发送 HTML 格式消息。
- `.Edit(message_id: str, text: str, content_type: str = "text")`：编辑已有消息。
- `.Recall(message_id: str)`：撤回消息。

### 链式修饰方法（可组合使用）

链式修饰方法返回 `self`，支持链式调用，必须在最终发送方法前调用：

- `.At(user_id: str, name: str = None)`：@指定用户。
- `.AtAll()`：@所有人。
- `.Reply(message_id: str)`：回复指定消息。

### 链式调用示例

```python
# 基础发送
await ideaura.Send.To("user", user_id).Text("Hello")

# @用户
await ideaura.Send.To("group", "chatroom").At("456").Text("@李四 你好")

# @多人
await ideaura.Send.To("group", "chatroom").At("456").At("789").Text("@多人")

# 回复消息
await ideaura.Send.To("group", "chatroom").Reply(msg_id).Text("回复消息")

# 回复 + @
await ideaura.Send.To("group", "chatroom").Reply(msg_id).At("456").Text("回复并@")
```

### 发送到不同目标

```python
# 发送到聊天室
await ideaura.Send.To("group", "chatroom").Text("聊天室消息")

# 发送到话题
await ideaura.Send.To("group", "topic_id").Text("话题消息")

# 发送私聊消息
await ideaura.Send.To("user", "user_id").Text("私聊消息")
```

### OneBot12消息支持

适配器支持发送 OneBot12 格式的消息，便于跨平台消息兼容：

- `.Raw_ob12(message: List[Dict], **kwargs)`：发送 OneBot12 格式消息。

```python
# 发送 OneBot12 格式消息
ob12_msg = [{"type": "text", "data": {"text": "Hello"}}]
await ideaura.Send.To("user", user_id).Raw_ob12(ob12_msg)

# 配合链式修饰
ob12_msg = [{"type": "text", "data": {"text": "回复消息"}}]
await ideaura.Send.To("group", "chatroom").Reply(msg_id).Raw_ob12(ob12_msg)
```

## 发送方法返回值

所有发送方法均返回一个 Task 对象，可以直接 await 获取发送结果。返回结果遵循 ErisPulse 适配器标准化返回规范：

```python
{
    "status": "ok",           // 执行状态
    "retcode": 0,             // 返回码
    "data": {...},            // 响应数据
    "self": {...},            // 自身信息（包含 user_id）
    "message_id": "123456",   // 消息ID
    "message": "",            // 错误信息
    "ideaura_raw": {...}      // 原始响应数据
}
```

## 特有事件类型

需要 `platform=="ideaura"` 检测再使用本平台特性

### 核心差异点

1. 特有事件类型：
    - 消息编辑：ideaura_message_edit
    - 消息撤回：ideaura_message_recall
    - 消息转发：ideaura_message_forward
    - 消息已读：ideaura_message_read
    - 好友被拒：ideaura_friend_rejected
    - 好友上线：ideaura_friend_online
    - 好友下线：ideaura_friend_offline
    - 用户状态变更：ideaura_user_status_change
    - 转发消息段：ideaura_forwarded
    - 编辑标记段：ideaura_edited
    - Markdown消息段：ideaura_markdown
    - HTML消息段：ideaura_html
2. 扩展字段：
    - 所有特有字段均以 `ideaura_` 前缀标识
    - 保留原始数据在 `ideaura_raw` 字段
    - `self.user_id` 表示当前账户的用户ID

### 消息编辑事件

```python
{
  "type": "notice",
  "detail_type": "ideaura_message_edit",
  "platform": "ideaura",
  "message_id": "消息ID",
  "user_id": "编辑者ID",
  "ideaura_new_content": "编辑后的内容",
  "ideaura_updated_message": { ... },
  "ideaura_source_type": "chatroom/topic/private"
}
```

### 消息撤回事件

```python
{
  "type": "notice",
  "detail_type": "ideaura_message_recall",
  "platform": "ideaura",
  "message_id": "被撤回的消息ID",
  "user_id": "撤回者ID",
  "group_id": "chatroom",
  "ideaura_source_type": "chatroom",
  "ideaura_recall_time": "撤回时间",
  "ideaura_is_self": false
}
```

### 消息转发事件

```python
{
  "type": "notice",
  "detail_type": "ideaura_message_forward",
  "platform": "ideaura",
  "message_id": "原始消息ID",
  "user_id": "转发者ID",
  "ideaura_forward_to": "目标话题ID",
  "ideaura_original_message_id": "原始消息ID",
  "ideaura_forwarded_message_id": "转发后的新消息ID"
}
```

### 消息已读事件

```python
{
  "type": "notice",
  "detail_type": "ideaura_message_read",
  "platform": "ideaura",
  "message_id": "消息ID",
  "ideaura_reader_id": "已读者ID",
  "ideaura_reader_name": "已读者昵称"
}
```

### 好友上线事件

```python
{
  "type": "notice",
  "detail_type": "ideaura_friend_online",
  "platform": "ideaura",
  "user_id": "好友ID",
  "user_nickname": "好友昵称",
  "ideaura_friend_avatar": "头像URL",
  "ideaura_presence_status": "online"
}
```

### 好友下线事件

```python
{
  "type": "notice",
  "detail_type": "ideaura_friend_offline",
  "platform": "ideaura",
  "user_id": "好友ID",
  "ideaura_presence_status": "offline"
}
```

### 用户状态变更事件

```python
{
  "type": "notice",
  "detail_type": "ideaura_user_status_change",
  "platform": "ideaura",
  "user_id": "用户ID",
  "ideaura_status": "新状态",
  "ideaura_previous_status": "旧状态"
}
```

### 好友请求事件

```python
{
  "type": "request",
  "detail_type": "friend",
  "platform": "ideaura",
  "user_id": "请求者ID",
  "user_nickname": "请求者昵称",
  "ideaura_request_id": "请求ID",
  "ideaura_message": "验证消息"
}
```

### 好友被拒事件

```python
{
  "type": "notice",
  "detail_type": "ideaura_friend_rejected",
  "platform": "ideaura",
  "user_id": "拒绝者ID",
  "user_nickname": "拒绝者昵称",
  "ideaura_request_id": "请求ID",
  "ideaura_requester_id": "请求发起者ID",
  "ideaura_requester_name": "请求发起者昵称"
}
```

### 转发消息段 (ideaura_forwarded)

当收到转发消息时，消息段类型为 `ideaura_forwarded`：

```json
{
  "type": "ideaura_forwarded",
  "data": {
    "forward_source_id": "1001",
    "original_message_id": "1001"
  }
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `forward_source_id` | string | 转发源消息ID |
| `original_message_id` | string | 原始消息ID |

### 事件处理示例

```python
from ErisPulse.Core.Event import notice, message

@message.on_message()
async def handle_message(event):
    if event.get_platform() == "ideaura":
        # 处理消息事件
        for segment in event.get("message", []):
            if segment.get("type") == "ideaura_forwarded":
                data = segment["data"]
                print(f"转发消息，源ID: {data['forward_source_id']}")

@notice.on_notice()
async def handle_notice(event):
    if event.get_platform() != "ideaura":
        return

    detail_type = event.get("detail_type")

    if detail_type == "ideaura_message_edit":
        new_content = event.get("ideaura_new_content", "")
        print(f"消息被编辑: {new_content}")

    elif detail_type == "ideaura_message_recall":
        message_id = event.get("message_id")
        print(f"消息被撤回: {message_id}")

    elif detail_type == "ideaura_friend_online":
        friend_name = event.get_user_nickname()
        print(f"好友上线: {friend_name}")

    elif detail_type == "ideaura_user_status_change":
        status = event.get("ideaura_status")
        print(f"用户状态变更: {status}")
```

---

## 多账户配置

### 配置说明

IdeauraAdapter 支持同时配置和运行多个账户，每个账户可选择 Token 登录或邮箱密码登录（二选一）。

```toml
# config.toml
# 账户1：Token 登录（推荐，无需邮箱密码）
[IdeauraAdapter.accounts.default]
token = "your-token-here"        # 登录Token（与 email+password 二选一）
enabled = true                   # 是否启用（可选，默认为true）

# 账户2：邮箱密码登录
[IdeauraAdapter.accounts.bot2]
email = "user2@example.com"      # 登录邮箱
password = "password2"           # 登录密码
enabled = true

# 可选：自定义服务器地址
[IdeauraAdapter]
base_url = "https://api-cofe.allons-y.uk:3009"
ws_url = "wss://api-cofe.allons-y.uk:3009/mqtt"
heartbeat_interval = 30
```

**配置项说明：**
- `token`：登录Token（选填，填写后优先使用Token登录，无需邮箱密码）
- `email`：登录邮箱（Token登录时可不填，邮箱密码登录时必填）
- `password`：登录密码（Token登录时可不填，邮箱密码登录时必填）
- `enabled`：是否启用该账户（可选，默认为true）

**全局配置项：**
- `base_url`：API 服务器地址（可选，默认为花枫咖啡馆官方地址）
- `ws_url`：WebSocket 服务器地址（可选，默认为花枫咖啡馆官方地址）
- `heartbeat_interval`：心跳间隔秒数（可选，默认30秒）

### 使用 Send DSL 指定账户

可以通过 `Using()` 方法指定使用哪个账户发送消息：

```python
from ErisPulse.Core import adapter
ideaura = adapter.get("ideaura")

# 使用账户名发送消息
await ideaura.Send.Using("default").To("user", "user123").Text("Hello from account 1!")

# 使用 user_id 发送消息（自动匹配对应账户）
await ideaura.Send.Using("456").To("group", "chatroom").Text("Hello from account 2!")

# 不指定时使用第一个启用的账户
await ideaura.Send.To("user", "user123").Text("Hello from default account!")
```

### 事件中的账户标识

接收到的事件会自动包含对应的账户信息：

```python
from ErisPulse.Core.Event import message

@message.on_message()
async def handle_message(event):
    if event["platform"] == "ideaura":
        account_id = event["self"]["user_id"]
        print(f"消息来自账户: {account_id}")
```

---

## 扩展字段说明

- 所有特有字段均以 `ideaura_` 前缀标识，避免与标准字段冲突
- 保留原始数据在 `ideaura_raw` 字段，便于访问平台的完整原始数据
- `self.user_id` 表示当前登录账户的用户ID
- `ideaura_source_type`：消息来源类型（`chatroom`/`topic`/`private`）
- `ideaura_sender_name`：发送者昵称
- `ideaura_sender_avatar`：发送者头像URL
- `ideaura_sender_is_bot`：发送者是否为机器人
- `ideaura_is_self`：是否为自己发送的消息（自消息已被过滤）
- `ideaura_topic_name`：话题名称
- `ideaura_message_type`：消息类型（normal/edited/forwarded/quoted）
- `ideaura_message_subtype`：消息子类型（text/image/video/file/markdown/html）

### 文件处理特性

- 文件大小限制：10MB（下载和本地读取均有限制）
- 自动文件类型检测：通过文件头魔法字节检测实际类型
- 智能文件名解析：对 `.bin`/`.dat`/`.tmp` 等无意义扩展名自动修正
- 支持 bytes、URL、本地路径三种文件输入方式
- URL 文件自动下载并上传到服务器

### 支持的文件类型

通过魔法字节自动检测：

| 类型 | 扩展名 |
|------|--------|
| 图片 | png, jpg, gif, webp |
| 视频 | mp4, avi, flv |
| 音频 | mp3, wav, ogg |
| 文档 | pdf, docx |

---

## 注意事项

1. 服务器地址 `api-cofe.allons-y.uk` 是平台固有地址，不随适配器名称变化
2. 适配器使用 WebSocket 长连接接收事件，支持自动重连（固定5秒延迟）
3. 自身发送的消息（`isSelf: true`）会被自动过滤，不会产生事件
4. @全体（`AtAll()`）需要管理员权限
5. 文件上传大小限制为 10MB
6. 音频文件作为 `file` 子类型发送（平台不区分独立音频类型）
7. 表情（`Face()`）以纯文本形式发送 emoji
8. 程序退出时请调用 `shutdown()` 确保资源释放
