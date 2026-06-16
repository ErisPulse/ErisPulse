# OneBot11平台特性文档

OneBot11Adapter 是基于 OneBot V11 协议构建的适配器。

---

## 文档信息

- 对应模块版本: 4.0.0
- 维护者: ErisPulse

## 基本信息

- 平台简介：OneBot 是一个聊天机器人应用接口标准
- 适配器名称：OneBotAdapter
- 支持的协议/API版本：OneBot V11
- 多账户支持：默认多账户架构，支持同时配置和运行多个 OneBot 账户
- 配置键名：`OneBotAdapter`

## 支持的消息发送类型

所有发送方法均通过链式语法实现，例如：
```python
from ErisPulse.Core import adapter
onebot = adapter.get("onebot11")

# 使用默认账户发送
await onebot.Send.To("group", group_id).Text("Hello World!")

# 指定特定账户发送
await onebot.Send.Using("main").To("group", group_id).Text("来自主账户的消息")

# 链式修饰：@用户 + 回复
await onebot.Send.To("group", group_id).At(123456).Reply(msg_id).Text("回复消息")

# @全体成员
await onebot.Send.To("group", group_id).AtAll().Text("公告消息")
```

### 基础发送方法

- `.Text(text: str)`：发送纯文本消息。
- `.Image(file: Union[str, bytes], filename: str = "image.png")`：发送图片（支持 URL、Base64 或 bytes）。
- `.Voice(file: Union[str, bytes], filename: str = "voice.amr")`：发送语音消息。
- `.Video(file: Union[str, bytes], filename: str = "video.mp4")`：发送视频消息。
- `.Face(id: Union[str, int])`：发送 QQ 表情。
- `.File(file: Union[str, bytes], filename: str = "file.dat")`：发送文件（自动判断类型）。
- `.Raw_ob12(message: List[Dict], **kwargs)`：发送 OneBot12 格式消息（自动转换为 OB11）。
- `.Recall(message_id: Union[str, int])`：撤回消息。

### 群操作方法

以下方法需通过 `To("group", group_id)` 指定目标群，使用群上下文执行操作：

- `.Kick(user_id, reject_add_request=False)`：踢出群成员。
- `.Ban(user_id, duration=1800)`：禁言群成员（秒），0 表示解禁。
- `.WholeBan(enable=True)`：开启/关闭全员禁言。
- `.SetAdmin(user_id, enable=True)`：设置/取消群管理员。
- `.SetCard(user_id, card="")`：设置群名片。
- `.SetGroupName(name)`：修改群名称。
- `.Leave(is_dismiss=False)`：退群（群主可解散）。
- `.SetTitle(user_id, title="")`：设置群头衔。
- `.SetPortrait(file)`：设置群头像。

### 查询方法

- `.GetMsg(message_id)`：获取消息内容。
- `.GetForwardMsg(id)`：获取合并转发消息。
- `.GetLoginInfo()`：获取当前登录号信息。
- `.GetFriendList()`：获取好友列表。
- `.GetGroupInfo()`：获取群信息（需 `To("group", group_id)`）。
- `.GetGroupList()`：获取群列表。
- `.GetGroupMemberInfo(user_id)`：获取群成员信息（需 `To("group", group_id)`）。
- `.GetGroupMemberList()`：获取群成员列表（需 `To("group", group_id)`）。

### 好友操作方法

- `.Like(user_id, times=1)`：发送好友赞（最大 10 次）。

### 链式修饰方法（可组合使用）

链式修饰方法返回 `self`，支持链式调用，必须在最终发送方法前调用：

- `.At(user_id: Union[str, int], name: str = None)`：@指定用户（可多次调用）。
- `.AtAll()`：@全体成员。
- `.Reply(message_id: Union[str, int])`：回复指定消息。

### 链式调用示例

```python
# 基础发送
await onebot.Send.To("group", 123456).Text("Hello")

# @单个用户
await onebot.Send.To("group", 123456).At(789012).Text("你好")

# @多个用户
await onebot.Send.To("group", 123456).At(111).At(222).At(333).Text("大家好")

# 发送 OneBot12 格式消息
ob12_msg = [{"type": "text", "data": {"text": "Hello"}}]
await onebot.Send.To("group", 123456).Raw_ob12(ob12_msg)

# 点赞
await onebot.Send.Like(123456, times=10)

# 禁言群成员
await onebot.Send.To("group", 123456).Ban(789012, duration=3600)

# 解禁
await onebot.Send.To("group", 123456).Ban(789012, duration=0)

# 踢人
await onebot.Send.To("group", 123456).Kick(789012)

# 设置群管理员
await onebot.Send.To("group", 123456).SetAdmin(789012)

# 修改群名
await onebot.Send.To("group", 123456).SetGroupName("新群名")

# 获取群信息
result = await onebot.Send.To("group", 123456).GetGroupInfo()

# 指定账户操作
await onebot.Send.Using("main").To("group", 123456).Ban(789012)
```

### 不支持的类型处理

如果调用未定义的发送方法，适配器会返回文本提示：
```python
# 调用不存在的方法
await onebot.Send.To("group", 123456).SomeUnsupportedMethod(arg1, arg2)
# 实际发送: "[不支持的发送类型] 方法名: SomeUnsupportedMethod, 参数: [...]"
```

## 请求操作（Request DSL）

适配器提供请求操作 DSL，用于处理好友请求和群请求（加群/邀请）的同意/拒绝操作。

### Event 快捷方法

请求事件支持 `event.approve()` 和 `event.reject()` 快捷方法，内部自动调用 Request DSL：

```python
from ErisPulse.Core.Event import request

@request.on_friend_request()
async def handle_friend_request(event):
    comment = event.get("comment", "")

    if comment == "passphrase":
        await event.approve()
    else:
        await event.reject()

@request.on_group_request()
async def handle_group_request(event):
    group_id = event.get("group_id")
    await event.approve()
```

### 手动调用 Request DSL

```python
# 同意请求
await onebot.Request("flag_string").accept()

# 拒绝请求
await onebot.Request("flag_string").reject()

# 指定账户操作
await onebot.Request("flag_string").Using("main").accept()
```

### 完整示例

```python
from ErisPulse.Core.Event import request

@request.on_friend_request()
async def handle_friend_request(event):
    comment = event.get("comment", "")

    # 方式一：使用 Event 快捷方法
    if comment == "passphrase":
        await event.approve()
    else:
        await event.reject()

    # 方式二：使用 Request DSL
    flag = event.get("flag")
    if comment == "passphrase":
        await onebot.Request(flag).accept()
    else:
        await onebot.Request(flag).reject()
```

### 请求操作返回值

```python
{
    "status": "ok",
    "retcode": 0,
    "data": {...},
    "message_id": "",
    "message": ""
}
```

## 事件类型映射

### 标准 OB12 映射

| OB11 原始类型 | 转换后 detail_type | 说明 |
|--------------|-------------------|------|
| message_type: private | `private` | 私聊消息 |
| message_type: group | `group` | 群聊消息 |
| request_type: friend | `friend` | 好友请求 |
| request_type: group | `group` | 群请求 |
| meta_event_type: heartbeat | `heartbeat` | 心跳 |
| notice_type: group_upload | `group_file_upload` | 群文件上传 |
| notice_type: group_admin | `group_admin_change` | 群管理员变动 |
| notice_type: group_increase | `group_member_increase` | 群成员增加 |
| notice_type: group_decrease | `group_member_decrease` | 群成员减少 |
| notice_type: group_ban | `group_ban` | 群禁言 |
| notice_type: friend_add | `friend_increase` | 好友添加 |
| notice_type: friend_delete | `friend_decrease` | 好友删除 |
| notice_type: group_recall / friend_recall | `message_recall` | 消息撤回 |

### 平台特有事件（onebot11_ 前缀）

| OB11 原始类型 | 转换后 detail_type | 说明 |
|--------------|-------------------|------|
| meta_event_type: lifecycle | `onebot11_lifecycle` | OneBot 实现生命周期 |
| notify + sub_type: honor | `onebot11_honor` | 群荣誉变更 |
| notify + sub_type: poke | `onebot11_poke` | 戳一戳 |
| notify + sub_type: lucky_king | `onebot11_lucky_king` | 群红包运气王 |
| CQ 码未知类型 | 消息段 `onebot11_{type}` | 未识别的 CQ 码 |

### 事件示例

```python
// 好友请求
{
  "type": "request",
  "detail_type": "friend",
  "user_id": "789012",
  "comment": "请加好友",
  "request_id": "flag_abc123",
  "flag": "flag_abc123"
}

// 心跳
{
  "type": "meta_event",
  "detail_type": "heartbeat",
  "interval": 5000,
  "status": {...}
}

// 生命周期（平台特有）
{
  "type": "meta_event",
  "detail_type": "onebot11_lifecycle",
  "sub_type": "enable"
}

// 戳一戳（平台特有）
{
  "type": "notice",
  "detail_type": "onebot11_poke",
  "group_id": "123456",
  "user_id": "789012",
  "target_id": "345678"
}

// 群红包运气王（平台特有）
{
  "type": "notice",
  "detail_type": "onebot11_lucky_king",
  "group_id": "123456",
  "user_id": "789012",
  "target_id": "345678"
}

// 荣誉变更（平台特有）
{
  "type": "notice",
  "detail_type": "onebot11_honor",
  "group_id": "123456",
  "user_id": "789012",
  "honor_type": "talkative"
}

// CQ 码扩展消息段
{
  "type": "message",
  "message": [
    {"type": "onebot11_shake", "data": {}}
  ]
}
```

### 扩展字段说明

- 所有特有字段均以 `onebot11_` 前缀标识
- 保留原始事件数据在 `onebot11_raw` 字段
- 保留原始事件类型在 `onebot11_raw_type` 字段
- 消息内容中的 CQ 码会转换为相应的消息段（标准类型无前缀，未知类型加 `onebot11_` 前缀）
- 回复消息会添加 `reply` 类型的消息段
- @消息会添加 `mention` 类型的消息段

## 事件扩展方法

OneBot11 适配器为事件对象注册了以下平台专有方法，可在事件处理器中直接调用：

```python
from ErisPulse.Core.Event import message

@message.on_message()
async def handle_message(event):
    raw_self_id = event.get_raw_self_id()
    sender_info = event.get_sender_info()
    sender_role = event.get_sender_role()
```

### 方法列表

| 方法 | 返回类型 | 说明 |
|------|----------|------|
| `get_raw_self_id()` | `str` | 获取原始 self_id（Bot 的 QQ 号） |
| `get_sender_info()` | `dict` | 获取完整的发送者信息（包含 nickname、role、level 等） |
| `get_sender_role()` | `str` | 获取发送者在群内的角色（owner/admin/member） |
| `get_sender_level()` | `int` | 获取发送者等级 |
| `get_sender_title()` | `str` | 获取发送者群头衔 |
| `is_system_message()` | `bool` | 判断是否为系统消息（sub_type == "system"） |

### 使用示例

```python
from ErisPulse.Core.Event import message, command

@message.on_group_message()
async def handle_group(event):
    role = event.get_sender_role()
    if role == "admin" or role == "owner":
        await event.reply("管理员好！")

    title = event.get_sender_title()
    if title:
        await event.reply(f"你的头衔是: {title}")

@command("whoami")
async def whoami(event):
    info = event.get_sender_info()
    nickname = info.get("nickname", "未知")
    level = event.get_sender_level()
    await event.reply(f"昵称: {nickname}, 等级: {level}")
```

## 配置选项

OneBot11 适配器采用多账户架构，每个账户独立配置。配置键名为 `OneBotAdapter`。

### 账户配置字段

| 字段 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `bot_id` | `str` | 是 | `""` | 机器人 QQ 号，用于标识账户 |
| `mode` | `str` | 否 | `"server"` | 运行模式：`"server"`（被动监听）或 `"client"`（主动连接） |
| `url` | `str` | 否 | `"ws://127.0.0.1:3001"` | Client 模式的 WebSocket 地址 |
| `token` | `str` | 否 | `""` | 认证 Token（Client 模式连接 Token / Server 模式验证 Token） |
| `server_path` | `str` | 否 | `"/"` | Server 模式的 WebSocket 路径 |
| `enabled` | `bool` | 否 | `true` | 是否启用该账户 |
| `name` | `str` | 否 | `""` | 账户备注名称 |

### 内置默认值

- 重连间隔：30秒
- API调用超时：30秒

### 配置示例

```toml
[OneBotAdapter.accounts.main]
bot_id = "123456789"
mode = "server"
server_path = "/onebot-main"
token = "main_token"
enabled = true

[OneBotAdapter.accounts.backup]
bot_id = "987654321"
mode = "client"
url = "ws://127.0.0.1:3002"
token = "backup_token"
enabled = true

[OneBotAdapter.accounts.test]
bot_id = "111222333"
mode = "client"
url = "ws://127.0.0.1:3003"
enabled = false
```

### 默认配置

如果未配置任何账户，适配器会自动创建：
```toml
[OneBotAdapter.accounts.default]
bot_id = ""
mode = "server"
server_path = "/"
enabled = true
```

## 发送方法返回值

所有发送方法均返回一个 Task 对象，可以直接 await 获取发送结果。返回结果遵循 ErisPulse 适配器标准化返回规范：

```python
{
    "status": "ok",
    "retcode": 0,
    "data": {...},
    "message_id": "123456",
    "message": "",
    "onebot11_raw": {...}
}
```

### 多账户发送语法

```python
# 账户选择方法
await onebot.Send.Using("main").To("group", 123456).Text("主账户消息")
await onebot.Send.Using("backup").To("group", 123456).Image("http://example.com/image.jpg")

# 通过 bot_id 选择账户
await onebot.Send.Using("123456789").To("group", 123456).Text("通过QQ号选择")

# API调用方式
await onebot.call_api("send_msg", account_id="main", group_id=123456, message="Hello")
```

### 账户解析优先级

`call_api` 和 `Using()` 中 `account_id` 参数的解析优先级：
1. 精确匹配账户名称
2. 匹配 `bot_id` 字段
3. 匹配账户的任意 `str` 类型字段
4. 回退到第一个已启用的账户

## 异步处理机制

OneBot11 适配器采用异步非阻塞设计，确保：
1. 消息发送不会阻塞事件处理循环
2. 多个并发发送操作可以同时进行
3. API 响应能够及时处理
4. WebSocket 连接保持活跃状态
5. 多账户并发处理，每个账户独立运行

## 错误处理

适配器提供完善的错误处理机制：
1. 网络连接异常自动重连（支持每个账户独立重连，间隔30秒）
2. API 调用超时处理（固定30秒超时）
3. 连接失败时自动按间隔重试

## 事件处理增强

多账户模式下，所有事件都会自动添加账户信息：
```python
{
    "type": "message",
    "detail_type": "private",
    "self": {"user_id": "123456789", "platform": "onebot11"},
    "platform": "onebot11",
    // ... 其他事件字段
}
```

适配器自动维护 `self_id → account_name` 映射，`event.reply()` 无需手动指定账户即可正确路由到来源账户。

## 管理接口

```python
# 获取所有账户信息
accounts = onebot.accounts

# 检查账户连接状态
connection_status = {
    account_id: connection is not None and not connection.closed
    for account_id, connection in onebot.connections.items()
}

# 动态启用/禁用账户（需要重启适配器）
onebot.accounts["test"].enabled = False
```

## self_id 自动映射

适配器会自动建立 OneBot `self_id`（QQ号）到 `account_name` 的映射关系，用于事件回路由：

```python
# 适配器内部自动完成
# 当收到事件时，self.user_id 字段填充为 bot_id
# 适配器自动记录: self_id("123456789") → account_name("main")

# 因此 event.reply() 可以自动找到正确的账户发送消息
@message.on_message()
async def handler(event):
    await event.reply("自动路由到正确的账户")
```
