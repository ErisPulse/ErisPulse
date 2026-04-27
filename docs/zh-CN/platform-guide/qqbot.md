# QQBot平台特性文档

QQBotAdapter 是基于QQBot（QQ机器人文档）协议构建的适配器，整合了QQBot所有功能模块，提供统一的事件处理和消息操作接口。

---

## 文档信息

- 对应模块版本: 1.0.0
- 维护者: ErisPulse

## 基本信息

- 平台简介：QQBot是QQ官方提供的机器人的开发接口，支持群聊、私聊、频道等多种场景
- 适配器名称：QQBotAdapter
- 连接方式：WebSocket 长连接（通过QQBot网关）
- 认证方式：基于 appId + clientSecret 获取 access_token
- 链式修饰支持：支持 `.Reply()`、`.At()`、`.AtAll()`、`.Keyboard()` 等链式修饰方法
- OneBot12兼容：支持发送 OneBot12 格式消息

## 配置说明

```toml
# config.toml
[QQBot_Adapter]
appid = "YOUR_APPID"          # QQ机器人应用ID（必填）
secret = "YOUR_CLIENT_SECRET"  # QQ机器人客户端密钥（必填）
sandbox = false                 # 是否使用沙盒环境（可选，默认为false）
intents = [1, 30, 25]          # 订阅的事件 intents 位（可选）
gateway_url = "wss://api.sgroup.qq.com/websocket/"  # 自定义网关地址（可选）
```

**配置项说明：**
- `appid`：QQ机器人的应用ID（必填），从QQ开放平台获取
- `secret`：QQ机器人的客户端密钥（必填），从QQ开放平台获取
- `sandbox`：是否使用沙盒环境，沙盒环境API地址为 `https://sandbox.api.sgroup.qq.com`
- `intents`：事件订阅 intents 列表，每个值会被左移位后按位或运算
  - `1`：频道相关事件
  - `25`：频道消息事件
  - `30`：群@消息事件
- `gateway_url`：WebSocket 网关地址，默认为 `wss://api.sgroup.qq.com/websocket/`

**API环境：**
- 正式环境：`https://api.sgroup.qq.com`
- 沙盒环境：`https://sandbox.api.sgroup.qq.com`

## 支持的消息发送类型

所有发送方法均通过链式语法实现，例如：
```python
from ErisPulse.Core import adapter
qqbot = adapter.get("qqbot")

await qqbot.Send.To("user", user_openid).Text("Hello World!")
```

支持的发送类型包括：
- `.Text(text: str)`：发送纯文本消息。
- `.Image(file: bytes | str)`：发送图片消息，支持文件路径、URL、二进制数据。
- `.Markdown(content: str)`：发送Markdown格式消息。
- `.Ark(template_id: int, kv: list)`：发送Ark模板消息。
- `.Embed(embed_data: dict)`：发送Embed消息。
- `.Raw_ob12(message: List[Dict], **kwargs)`：发送 OneBot12 格式消息。

### 链式修饰方法（可组合使用）

链式修饰方法返回 `self`，支持链式调用，必须在最终发送方法前调用：

- `.Reply(message_id: str)`：回复指定消息。
- `.At(user_id: str)`：@指定用户（以 `<@user_id>` 格式插入内容）。
- `.AtAll()`：@所有人（插入 `@所有人` 文本）。
- `.Keyboard(keyboard: dict)`：添加键盘按钮。

### 链式调用示例

```python
# 基础发送
await qqbot.Send.To("user", user_openid).Text("Hello")

# 回复消息
await qqbot.Send.To("group", group_openid).Reply(msg_id).Text("回复消息")

# 回复 + 按钮
await qqbot.Send.To("group", group_openid).Reply(msg_id).Keyboard(keyboard).Text("带回复和键盘的消息")

# @用户
await qqbot.Send.To("group", group_openid).At("member_openid").Text("你好")

# 组合使用
await qqbot.Send.To("group", group_openid).Reply(msg_id).At("member_openid").Keyboard(keyboard).Text("复合消息")
```

### OneBot12消息支持

适配器支持发送 OneBot12 格式的消息，便于跨平台消息兼容：

```python
# 发送 OneBot12 格式消息
ob12_msg = [{"type": "text", "data": {"text": "Hello"}}]
await qqbot.Send.To("user", user_openid).Raw_ob12(ob12_msg)

# 配合链式修饰
ob12_msg = [{"type": "text", "data": {"text": "回复消息"}}]
await qqbot.Send.To("group", group_openid).Reply(msg_id).Raw_ob12(ob12_msg)
```

## 发送方法返回值

所有发送方法均返回一个 Task 对象，可以直接 await 获取发送结果。返回结果遵循 ErisPulse 适配器标准化返回规范：

```python
{
    "status": "ok",           // 执行状态: "ok" 或 "failed"
    "retcode": 0,             // 返回码
    "data": {...},            // 响应数据
    "message_id": "123456",   // 消息ID
    "message": "",            // 错误信息
    "qqbot_raw": {...}        // 原始响应数据
}
```

### 错误码说明

| retcode | 说明 |
|---------|------|
| 0 | 成功 |
| 10003 | 无法确定发送目标 |
| 32000 | 请求超时 |
| 33000 | API调用异常 |
| 34000 | API返回了意外格式或业务错误 |

## 特有事件类型

需要 `platform=="qqbot"` 检测再使用本平台特性

### 核心差异点

1. **openid体系**：QQBot使用 openid 而非 QQ号，用户和群的标识均为 openid 字符串
2. **群消息必须@**：群内消息仅在用户@机器人时才会收到（`GROUP_AT_MESSAGE_CREATE`）
3. **频道系统**：QQBot支持频道（Guild）和子频道（Channel）的消息和事件
4. **消息审核**：发送的消息可能需要经过审核，通过 `qqbot_audit_pass`/`qqbot_audit_reject` 事件通知结果
5. **被动回复**：群消息和私聊消息支持被动回复机制，需要在发送时携带 `msg_id`

### 扩展字段

- 所有特有字段均以 `qqbot_` 前缀标识
- 保留原始数据在 `qqbot_raw` 字段
- `qqbot_raw_type` 标识原始QQBot事件类型（如 `C2C_MESSAGE_CREATE`）
- 附件数据通过 `qqbot_attachment` 字段保存原始附件信息

### 特殊字段示例

```python
# 群@消息
{
  "type": "message",
  "detail_type": "group",
  "user_id": "MEMBER_OPENID",
  "group_id": "GROUP_OPENID",
  "qqbot_group_openid": "GROUP_OPENID",
  "qqbot_member_openid": "MEMBER_OPENID",
  "qqbot_event_id": "消息事件ID",
  "qqbot_reply_token": "回复token"
}

# 私聊消息
{
  "type": "message",
  "detail_type": "private",
  "user_id": "USER_OPENID",
  "qqbot_openid": "USER_OPENID",
  "qqbot_event_id": "消息事件ID",
  "qqbot_reply_token": "回复token"
}

# 交互事件
{
  "type": "notice",
  "detail_type": "qqbot_interaction",
  "qqbot_interaction_id": "交互ID",
  "qqbot_interaction_type": "交互类型",
  "qqbot_interaction_data": {
    "...": "交互数据"
  }
}

# 消息审核
{
  "type": "notice",
  "detail_type": "qqbot_audit_pass",
  "qqbot_audit_id": "审核ID",
  "qqbot_message_id": "消息ID"
}

# 消息删除
{
  "type": "notice",
  "detail_type": "qqbot_message_delete",
  "message_id": "被删除的消息ID",
  "operator_id": "操作者ID"
}

# 表情回应
{
  "type": "notice",
  "detail_type": "qqbot_reaction_add",
  "qqbot_raw": {
    "...": "原始数据"
  }
}
```

### 频道消息段

频道消息支持 `mentions` 字段，转换后以 `mention` 消息段表示：

```json
{
  "type": "mention",
  "data": {
    "user_id": "被@用户ID",
    "user_name": "被@用户昵称"
  }
}
```

### 附件消息段

QQBot的附件根据 `content_type` 自动转换为对应消息段：

| content_type 前缀 | 转换类型 | 说明 |
|---|---|---|
| `image` | `image` | 图片消息 |
| `video` | `video` | 视频消息 |
| `audio` | `voice` | 语音消息 |
| 其他 | `file` | 文件消息 |

附件消息段结构：
```json
{
  "type": "image",
  "data": {
    "url": "附件URL",
    "qqbot_attachment": {
      "content_type": "image/png",
      "url": "原始附件URL"
    }
  }
}
```

## WebSocket连接

### 连接流程

1. 使用 appId + clientSecret 获取 access_token
2. 连接到 WebSocket 网关
3. 收到 OP_HELLO（op=10）消息，获取心跳间隔
4. 发送 OP_IDENTIFY（op=2）进行身份验证
5. 收到 READY 事件，获取 session_id 和 bot_id
6. 开始心跳循环（OP_HEARTBEAT，op=1）
7. 接收事件分发（OP_DISPATCH，op=0）

### 断线重连

- 支持自动重连，最大重连次数为50次
- 重连等待时间采用指数退避算法：`min(5 * 2^min(count, 6), 300)` 秒
- 支持会话恢复（OP_RESUME，op=6），使用 session_id + seq 恢复
- 收到 OP_RECONNECT（op=7）或 OP_INVALID_SESSION（op=9）时自动触发重连

### Token刷新

- access_token 有效期通常为7200秒
- 适配器自动每 7080 秒（7200-120）刷新一次 token
- 刷新接口：`POST https://bots.qq.com/app/getAppAccessToken`

## 事件订阅（Intents）

intents 值通过位运算组合：

```python
intents = [1, 30, 25]
value = 0
for intent in intents:
    value |= (1 << intent)
```

常用的 intent 位：
| intent值 | 说明 |
|----------|------|
| 1 | 频道相关事件（GUILD_CREATE等） |
| 25 | 频道消息事件（AT_MESSAGE_CREATE等） |
| 30 | 群@消息事件（GROUP_AT_MESSAGE_CREATE等） |

## 使用示例

### 处理群消息

```python
from ErisPulse.Core.Event import message
from ErisPulse import sdk

qqbot = sdk.adapter.get("qqbot")

@message.on_message()
async def handle_group_msg(event):
    if event.get("platform") != "qqbot":
        return
    if event.get("detail_type") != "group":
        return

    text = event.get_text()
    group_id = event.get("group_id")

    if text == "hello":
        await qqbot.Send.To("group", group_id).Reply(
            event.get("message_id")
        ).Text("Hello!")
```

### 处理交互事件

```python
from ErisPulse.Core.Event import notice

@notice.on_notice()
async def handle_interaction(event):
    if event.get("platform") != "qqbot":
        return

    if event.get("detail_type") == "qqbot_interaction":
        interaction_id = event.get("qqbot_interaction_id", "")
        interaction_data = event.get("qqbot_interaction_data", {})
        # 处理交互...
```

### 发送媒体消息

```python
# 发送图片（URL）
await qqbot.Send.To("group", group_openid).Image("https://example.com/image.png")

# 发送图片（二进制）
with open("image.png", "rb") as f:
    image_bytes = f.read()
await qqbot.Send.To("user", user_openid).Image(image_bytes)
```

### 监听消息审核结果

```python
@notice.on_notice()
async def handle_audit(event):
    if event.get("platform") != "qqbot":
        return

    detail_type = event.get("detail_type")

    if detail_type == "qqbot_audit_pass":
        msg_id = event.get("qqbot_message_id")
        print(f"消息审核通过: {msg_id}")

    elif detail_type == "qqbot_audit_reject":
        reason = event.get("qqbot_audit_reject_reason", "")
        print(f"消息审核拒绝: {reason}")
```
