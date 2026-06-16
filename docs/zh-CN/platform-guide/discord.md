# Discord 平台特性文档

DiscordAdapter 是基于 Discord Gateway (WebSocket) 和 REST API v10 协议构建的适配器，整合了 Discord Bot 的核心功能，提供统一的事件处理和消息操作接口。

---

## 文档信息

- 对应模块版本: 4.0.0
- 维护者: ErisPulse
- Discord API 版本: v10

## 基本信息

- 平台简介：Discord 是一款广受欢迎的社区通讯平台，支持服务器、频道、私信等多种会话形式，提供完善的 Bot 开发接口
- 适配器名称：DiscordAdapter
- 多账户支持：支持同时配置多个 Discord 机器人
- 连接方式：Gateway WebSocket（接收事件）+ REST API（发送消息/调用接口）
- 认证方式：Bot Token（HTTP 头 `Authorization: Bot {token}`，Gateway IDENTIFY payload 携带 token）
- 链式修饰支持：支持 `.Reply()`、`.At()`、`.AtAll()` 等链式修饰方法
- OneBot12 兼容：支持发送 OneBot12 格式消息

## 配置说明

DiscordAdapter 支持多账户配置，每个账户对应一个独立的 Discord Bot。

```toml
# config.toml

# 账户1
[DiscordAdapter.accounts.default]
token = "YOUR_BOT_TOKEN"       # Discord Bot Token（必填）
intents = 33281                 # Gateway Intents（可选，默认 33281）
enabled = true                  # 是否启用（可选，默认 true）

# 账户2
[DiscordAdapter.accounts.bot2]
token = "ANOTHER_BOT_TOKEN"
intents = 33281
enabled = true
```

**配置项说明（每个账户）：**

- `token`：Discord Bot Token（必填），从 [Discord Developer Portal](https://discord.com/developers/applications) 获取
- `intents`：Gateway Intents 位掩码（可选，默认 `33281`），决定 Bot 订阅的事件类型
- `bot_id`：Bot 的用户 ID（可选，运行时从 READY 事件自动获取，无需手动填写）
- `enabled`：是否启用该账户（可选，默认 `true`）

### Gateway Intents

Intents 使用位掩码，计算方式为各 Intent 值按位或（`|`）：

| Intent | 位 | 值 | 说明 | Privileged |
|-------|------|------|------|------|
| GUILDS | `1 << 0` | 1 | 服务器创建/删除/更新、频道、角色变更 | 否 |
| GUILD_MEMBERS | `1 << 1` | 2 | 成员加入/离开/更新 | 是 |
| GUILD_MESSAGES | `1 << 9` | 512 | 服务器消息收发 | 否 |
| MESSAGE_CONTENT | `1 << 15` | 32768 | 消息内容（无此 Intent 时 content 为空） | 是 |

默认值 `33281` = `GUILDS(1) | GUILD_MESSAGES(512) | MESSAGE_CONTENT(32768)`。

> **注意**：Privileged Intents 需在 Discord Developer Portal → Bot → Privileged Gateway Intents 中开启。如果 Bot 在超过 100 个服务器中，还需通过 Discord 审核。

**API 环境：**
- Discord REST API 基础地址：`https://discord.com/api/v10`
- Gateway WebSocket 地址：通过 `GET /gateway/bot` 动态获取，通常为 `wss://gateway.discord.gg/?v=10&encoding=json`

## 支持的消息发送类型

所有发送方法均通过链式语法实现，例如：
```python
from ErisPulse.Core import adapter
discord = adapter.get("discord")

await discord.Send.To("group", channel_id).Text("Hello World!")
```

支持的发送类型包括：
- `.Text(text: str)`：发送纯文本消息。
- `.Embed(embed: dict | list)`：发送 Embed 嵌入消息，支持单个或多个 Embed。
- `.Image(file: bytes | str, filename: str = "image.png")`：发送图片，支持二进制数据或 URL。
- `.File(file: bytes | str, filename: str = None)`：发送文件，支持二进制数据或 URL。
- `.Reply(content: str, message_id: str)`：回复指定消息（便捷终端方法）。
- `.Raw_ob12(message: List[Dict], **kwargs)`：发送 OneBot12 格式消息。
- `.Raw_json(json_str: str)`：发送任意 Discord API 请求 JSON。

### 链式修饰方法（可组合使用）

链式修饰方法返回 `self`，支持链式调用，必须在最终发送方法前调用：

- `.Reply(message_id: str)`：回复（引用）指定消息，设置 `message_reference`。
- `.At(user_id: str)`：@指定用户，转换为 `<@user_id>`，可多次调用。
- `.AtAll()`：@所有人，转换为 `@everyone`。

### 链式调用示例

```python
# 基础发送
await discord.Send.To("group", channel_id).Text("Hello")

# 回复消息
await discord.Send.To("group", channel_id).Reply(msg_id).Text("回复消息")

# 便捷回复（一步到位）
await discord.Send.To("group", channel_id).Reply("回复内容", msg_id)

# @用户
await discord.Send.To("group", channel_id).At("user_id").Text("你好")

# @多个用户
await discord.Send.To("group", channel_id).At("user1").At("user2").Text("多用户@")

# @全体
await discord.Send.To("group", channel_id).AtAll().Text("公告")

# 组合使用
await discord.Send.To("group", channel_id).Reply(msg_id).At("user_id").Text("复合消息")

# Embed 嵌入消息
embed = {
    "title": "通知",
    "description": "这是一条嵌入消息",
    "color": 5814783,
    "fields": [{"name": "字段", "value": "值", "inline": True}],
}
await discord.Send.To("group", channel_id).Embed(embed)

# 发送图片
await discord.Send.To("group", channel_id).Image("https://example.com/image.png")
```

### 私信发送

私信发送时，适配器会自动创建 DM 频道：

```python
# 发送私信
await discord.Send.To("user", user_id).Text("私信内容")
await discord.Send.To("user", user_id).Embed(embed)
```

### 消息操作

```python
# 撤回消息
await discord.Send.To("group", channel_id).Recall(msg_id)

# OneBot12 格式
ob12_msg = [
    {"type": "text", "data": {"text": "Hello "}},
    {"type": "mention", "data": {"user_id": "user_id"}},
]
await discord.Send.To("group", channel_id).Raw_ob12(ob12_msg)
```

## 发送方法返回值

所有发送方法均返回一个 Task 对象，可以直接 await 获取发送结果。返回结果遵循 ErisPulse 适配器标准化返回规范：

```python
{
    "status": "ok",           // 执行状态: "ok" 或 "failed"
    "retcode": 0,             // 返回码（0 为成功）
    "data": {...},            // Discord API 原始响应
    "message_id": "xxx",      // 消息ID（发送消息时）
    "message": "",            // 错误信息
    "discord_raw": {...}      // 原始响应数据
}
```

### 错误码说明

| retcode | 说明 |
|---------|------|
| 0 | 成功 |
| 33001 | 网络错误（连接失败、超时等） |
| 34000 | Discord API 返回错误（权限不足、参数错误等） |

## 特有事件类型

需要 `platform == "discord"` 检测再使用本平台特性。

### 核心差异点

1. **服务器/频道系统**：Discord 使用服务器（Guild）和频道（Channel）两层结构，频道是消息的基本发送目标
2. **Gateway 事件**：所有事件通过 WebSocket Gateway 接收，使用 Opcode + Dispatch 机制
3. **Intents 订阅**：通过位掩码订阅事件类型，`MESSAGE_CONTENT` 需 Privileged 权限
4. **消息段类型**：支持文本、图片、文件、视频、音频、Embed、Sticker 等消息段
5. **Mention 格式**：Discord 使用 `<@user_id>` 格式表示用户提及

### 扩展字段

所有特有字段均以 `discord_` 前缀标识：
- `discord_raw`：原始 Discord 事件数据
- `discord_raw_type`：原始事件类型名（如 `MESSAGE_CREATE`）
- `discord_guild_id`：服务器 ID
- `discord_channel_id`：频道 ID

### detail_type 映射

| Discord 场景 | detail_type | 说明 |
|---|---|---|
| 频道消息 | `channel` | ErisPulse 扩展类型 |
| 私信（DM） | `private` | OneBot12 标准类型 |

### 事件类型映射

| Discord 事件 | OneBot12 type | detail_type | 说明 |
|---|---|---|---|
| MESSAGE_CREATE | message | channel/private | 消息创建 |
| MESSAGE_UPDATE | message | channel/private | 消息编辑 |
| MESSAGE_DELETE | notice | group_message_delete / private_message_delete | 消息删除 |
| GUILD_MEMBER_ADD | notice | group_member_increase | 成员加入 |
| GUILD_MEMBER_REMOVE | notice | group_member_decrease | 成员离开 |
| GUILD_MEMBER_UPDATE | notice | group_member_update | 成员信息更新 |
| GUILD_ROLE_CREATE | notice | group_role_create | 角色创建 |
| GUILD_ROLE_DELETE | notice | group_role_delete | 角色删除 |
| CHANNEL_CREATE | notice | channel_create | 频道创建 |
| CHANNEL_DELETE | notice | channel_delete | 频道删除 |
| INTERACTION_CREATE | request | interaction | 交互（按钮、命令等） |

### 特殊字段示例

```python
# 频道文本消息
{
  "type": "message",
  "detail_type": "channel",
  "user_id": "发送者ID",
  "user_nickname": "用户名",
  "group_id": "频道ID",
  "message_id": "消息ID",
  "discord_raw": {...},
  "discord_raw_type": "MESSAGE_CREATE",
  "discord_guild_id": "服务器ID",
  "discord_channel_id": "频道ID",
  "message": [
    {"type": "text", "data": {"text": "Hello"}}
  ],
  "alt_message": "Hello"
}

# 私信消息
{
  "type": "message",
  "detail_type": "private",
  "user_id": "发送者ID",
  "user_nickname": "用户名",
  "message_id": "消息ID",
  "discord_raw": {...},
  "discord_raw_type": "MESSAGE_CREATE",
  "discord_channel_id": "DM频道ID",
  "message": [
    {"type": "text", "data": {"text": "私信内容"}}
  ],
  "alt_message": "私信内容"
}

# 带 Embed 的消息
{
  "type": "message",
  "detail_type": "channel",
  "message": [
    {"type": "discord_embed", "data": {"embed": {...}}}
  ],
  "alt_message": "[嵌入消息]"
}

# 带附件的消息
{
  "type": "message",
  "detail_type": "channel",
  "message": [
    {"type": "text", "data": {"text": "看这张图"}},
    {"type": "image", "data": {"file": "图片URL", "url": "图片URL", "file_name": "image.png"}}
  ],
  "alt_message": "看这张图[图片]"
}
```

### 消息段类型

Discord 消息内容根据 `content`、`attachments`、`embeds` 字段自动转换为对应消息段：

| 来源 | 转换类型 | 说明 |
|---|---|---|
| content 文本 | `text` | 纯文本内容 |
| content `<@id>` | `mention` | 用户提及 |
| content `<@&id>` | `discord_role_mention` | 角色提及 |
| content `<#id>` | `discord_channel_mention` | 频道提及 |
| attachments (image/*) | `image` | 图片附件 |
| attachments (video/*) | `video` | 视频附件 |
| attachments (audio/*) | `audio` | 音频附件 |
| attachments (其他) | `file` | 文件附件 |
| embeds | `discord_embed` | 嵌入消息 |
| sticker_items | `discord_sticker` | 贴纸 |

### discord_embed 消息段

```json
{
  "type": "discord_embed",
  "data": {
    "embed": {
      "title": "标题",
      "description": "描述",
      "color": 12345,
      "fields": [...],
      "image": {"url": "..."},
      "thumbnail": {"url": "..."},
      "footer": {"text": "..."}
    }
  }
}
```

## Gateway 连接

### 连接流程

1. 调用 `GET /gateway/bot` 获取 WebSocket 网关 URL
2. 连接到 `wss://gateway.discord.gg/?v=10&encoding=json`
3. 收到 opcode 10 HELLO：包含 `heartbeat_interval`
4. 发送 opcode 2 IDENTIFY：携带 token、intents、properties
5. 开始心跳循环：按 `heartbeat_interval` 定时发送 opcode 1 Heartbeat
6. 收到 opcode 0 Dispatch：事件分发（`t`=事件名, `s`=序号, `d`=数据）
7. 收到 opcode 11 Heartbeat ACK：心跳确认

### Opcode 说明

| Opcode | 名称 | 方向 | 说明 |
|--------|------|------|------|
| 0 | Dispatch | 接收 | 事件分发（含 `t`、`s`、`d` 字段） |
| 1 | Heartbeat | 发送/接收 | 心跳（携带最后 seq） |
| 2 | Identify | 发送 | 身份认证 |
| 6 | Resume | 发送 | 恢复会话 |
| 7 | Reconnect | 接收 | 服务器要求重连 |
| 9 | Invalid Session | 接收 | 无效会话 |
| 10 | Hello | 接收 | 连接握手（含 heartbeat_interval） |
| 11 | Heartbeat ACK | 接收 | 心跳确认 |

### 断线重连与 RESUME

- 连接断开后，适配器自动重试连接
- 如果之前有 `session_id`，优先尝试 RESUME（opcode 6）恢复会话
- RESUME 携带 `token`、`session_id`、最后 `seq`，恢复后补发遗漏事件
- 收到 opcode 7（Reconnect）时，保持会话状态并重连
- 收到 opcode 9（Invalid Session）且 `d=false` 时，清除会话并重新 IDENTIFY

### 心跳机制

- 收到 HELLO 后，等待 `heartbeat_interval * random()` 毫秒发送首次心跳
- 此后每隔 `heartbeat_interval` 毫秒发送一次心跳
- 心跳携带最后的 `seq` 值（opcode 1，`d: seq`）
- 若发送心跳后 `heartbeat_interval` 内未收到 ACK（opcode 11），视为连接异常并重连

## 使用示例

### 处理频道消息

```python
from ErisPulse.Core.Event import message
from ErisPulse import sdk

discord = sdk.adapter.get("discord")

@message.on_message()
async def handle_group_msg(event):
    if event.get("platform") != "discord":
        return

    text = event.get_text()
    channel_id = event.get("group_id")

    if text == "hello":
        await discord.Send.To("group", channel_id).Text("Hello!")
```

### 处理私信

```python
@message.on_message()
async def handle_private_msg(event):
    if event.get("platform") != "discord":
        return
    if not event.is_dm():
        return

    text = event.get_text()
    user_id = event.get("user_id")

    await discord.Send.To("user", user_id).Text(f"你说了: {text}")
```

### 发送 Embed 消息

```python
embed = {
    "title": "服务器公告",
    "description": "欢迎使用 ErisPulse Discord 适配器",
    "color": 3447003,
    "fields": [
        {"name": "版本", "value": "4.0.0", "inline": True},
        {"name": "框架", "value": "ErisPulse", "inline": True},
    ],
    "footer": {"text": "Powered by ErisPulse"},
    "timestamp": "2025-01-01T00:00:00.000Z",
}
await discord.Send.To("group", channel_id).Embed(embed)
```

### 使用 Discord 特有方法

```python
@message.on_message()
async def handle(event):
    if event.get("platform") != "discord":
        return

    channel_id = event.get_channel_id()
    guild_id = event.get_guild_id()
    is_dm = event.is_dm()
    embeds = event.get_embeds()
    attachments = event.get_attachments()

    if embeds:
        await discord.Send.To("group", channel_id).Text(
            f"收到 {len(embeds)} 个 Embed"
        )
```

### 处理交互事件

```python
from ErisPulse.Core.Event import request

@request.on_request()
async def handle_interaction(event):
    if event.get("platform") != "discord":
        return

    interaction = event.get_interaction_data()
    if interaction.get("type") == 3:  # MESSAGE_COMPONENT
        await event.reply("按钮已点击！")
```
