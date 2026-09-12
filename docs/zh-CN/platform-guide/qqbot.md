# QQBot平台特性文档

QQBotAdapter 是基于QQ官方机器人（QQ OpenAPI）协议构建的适配器，整合群聊、私聊、频道等全场景功能，提供 OneBot12 标准事件、标准Api动作与请求操作接口。

---

## 文档信息

- 对应模块版本: 5.0.0
- 维护者: ErisPulse

## 基本信息

- 平台简介：QQ官方机器人开发接口，支持群聊、私聊、频道等多种场景
- 适配器名称：QQBotAdapter
- 连接方式：**WebSocket 长连接**（默认）或 **Webhook HTTP 回调**（按账户配置，Ed25519 验签）
- 认证方式：appId + clientSecret 获取 access_token（7200s，提前45s自动刷新）
- API根地址：`https://api.bot.qq.com`（v5 起官方统一域名，sandbox 已废弃）
- OneBot12兼容：消息收发、事件、**标准Api动作**、**请求操作**全覆盖
- 多账户：支持，`accounts` 下任意账户并行（可混合 websocket/webhook 模式）

## 配置说明

```toml
# config.toml
[QQBot_Adapter]
intents = "[0, 9, 12, 25, 26, 27]"   # 全局：订阅的事件 intents（JSON数组，支持事件名）

[QQBot_Adapter.accounts.default]
appid = "YOUR_APPID"                 # QQ机器人应用ID（必填）
secret = "YOUR_CLIENT_SECRET"        # QQ机器人客户端密钥（必填）
mode = "websocket"                   # 事件接收方式：websocket / webhook
bot_id = ""                          # 机器人ID（留空自动获取；可手动填写用于 Using() 定位）
gateway_url = ""                     # WebSocket网关地址（留空通过 /gateway/bot 动态获取）
api_base_url = "https://api.bot.qq.com"  # API根地址（可自定义用于代理）
webhook_path = "/webhook"            # Webhook回调路径（mode=webhook 时生效）
enabled = true
```

**v5 破坏性变更：**
- 官方统一使用 `api.bot.qq.com`，`sandbox` 配置废弃（旧配置自动迁移并忽略）
- 旧版扁平配置（`[QQBot_Adapter]` 下直接写 appid/secret）自动迁移到 `accounts.default`
- 框架为**软依赖**：安装适配器不会拉动框架版本；运行时检测 `ErisPulse>=2.7.1` 并提示

**intents 说明（支持位序号或事件名）：**

| 位 | 事件名 | 说明 |
|----|--------|------|
| 0 | GUILDS | 频道变更 |
| 1 | GUILD_MEMBERS | 频道成员变更 |
| 9 | GUILD_MESSAGES | 频道消息（私域） |
| 12 | DIRECT_MESSAGE | 频道私信 |
| 24 | GROUP_MEMBER | 群成员变更（v5新增） |
| 25 | GROUP_AND_C2C_EVENT | 群@消息与私聊消息 |
| 26 | INTERACTION | 交互事件（按钮等） |
| 27 | MESSAGE_AUDIT | 消息审核事件 |
| 30 | PUBLIC_GUILD_MESSAGES | 频道消息（公域） |

## 消息发送

### 基础发送

```python
from ErisPulse import sdk
qqbot = sdk.adapter.get("qqbot")

await qqbot.Send.To("user", user_openid).Text("Hello World!")

# 群聊@消息（自动使用 <qqbot-at-user id="x" /> 格式）
await qqbot.Send.To("group", group_openid).At("member_openid").Text("@你")

# 频道消息（@ 自动使用 <@user_id> 格式）
await qqbot.Send.To("channel", channel_id).Text("频道消息")

# 被动回复（自动携带 msg_id，无需手动 Reply）
await qqbot.Send.To("group", group_openid).Reply(msg_id).Text("回复内容")

# 富媒体（URL / 本地路径 / 二进制；超过5MB自动分片上传）
await qqbot.Send.To("group", gid).Image("https://example.com/img.png")

# Markdown（原生 / 模板）
await qqbot.Send.To("group", gid).Markdown("# 标题\n- 列表")
await qqbot.Send.To("user", uid).Markdown(template_id=1, kv=[{"key": "title", "value": "通知"}])

# 键盘（自动置为 markdown 类型并附带 bot_appid）
await qqbot.Send.To("group", gid).Keyboard(keyboard).Text("请选择")

# 流式消息（单聊）
await qqbot.Send.To("user", openid).Stream("回答内容")

# 多账户
await qqbot.Send.Using("account2").To("group", gid).Text("来自第二个机器人")
```

## OneBot12 标准Api动作

```python
result = await qqbot.Api.get_self_info()                     # 机器人信息
result = await qqbot.Api.get_group_info(group_openid)        # 群信息
result = await qqbot.Api.get_group_member_list(group_openid) # 群成员列表（自动分页）
result = await qqbot.Api.get_guild_list()                    # 频道列表
result = await qqbot.Api.get_channel_list(guild_id)          # 子频道列表
await qqbot.Api.delete_message(message_id)                   # 撤回（自动按消息来源路由端点）
result = await qqbot.Api.get_status()                        # 多账户运行状态
result = await qqbot.Api.Using("account2").get_self_info()   # 指定账户
```

支持的标准动作：`get_self_info` / `get_group_info` / `get_group_member_info` / `get_group_member_list` / `get_guild_info` / `get_guild_list` / `get_guild_member_info` / `get_guild_member_list` / `get_channel_info` / `get_channel_list` / `set_channel_name` / `leave_channel` / `delete_message` / `get_status` / `get_version` / `get_supported_actions`。不支持的动作返回 `retcode=10002`。

## 请求操作（入群申请审批）

`GROUP_JOIN_REQUEST` 事件转换为 OneBot12 `request` 事件，支持标准化审批：

```python
from ErisPulse.Core.Event import request as request_event

@request_event.on_request()
async def handle_join(event):
    if event.get("platform") == "qqbot":
        await event.approve()                  # 同意
        # await event.reject(comment="理由")   # 拒绝
```

`request_id` = 官方 `join_request_id`，适配器自动缓存申请上下文并路由到 `POST /v2/groups/{group_openid}/approval_join_request/{member_openid}`。

## @机器人检测机制（重要）

QQ官方的"被@"事实由事件名承载，且群消息 @ 标记为 `<@{群空间openid}>`（与 READY 返回的 bot_id **不在同一 id 体系**）。适配器自动处理：

1. **标记解析**：`<@openid>` 与 `<qqbot-at-user>` 两种风格均解析为 mention 段（文本中无残留）
2. **名称归一化**：`/users/@me` 返回的机器人名与 mentions 数组昵称一致时，认定为@机器人，mention 段归一化为 bot_id（原始 openid 保留在 `data.qqbot_openid`）
3. **openid 学习**：自动学习机器人在各群的 openid，用于"接收全部群消息"模式下的@识别
4. **注入保证**：`GROUP_AT_MESSAGE_CREATE` / `AT_MESSAGE_CREATE` 保证存在机器人 mention 段

因此 `on_at_message()` / `event.is_at_message()` 在 qqbot 平台可直接使用。开启"接收全部群消息"权限后，@消息以 `GROUP_MESSAGE_CREATE` 推送（`GROUP_AT_MESSAGE_CREATE` 不再到达），适配器同样能识别。

## 平台原生API方法族

适配器暴露完整QQ官方API（详情见适配器仓库 platform-features.md）：

- **机器人**：`get_me()`、`reply_interaction()`
- **频道**：`get_guilds/get_guild/mute_guild_all/roles管理/api_permission`
- **子频道**：`get_channels/get_channel/create_channel/update_channel/delete_channel/pins`
- **频道成员**：`get_guild_members/get_guild_member/mute/roles/kick`
- **权限/表态/日程/帖子/音频**：全套方法
- **群管理**（部分接口仅白名单机器人）：`get_group_members/get_group_bot_state/黑名单/入群审批/禁言/审批策略`
- **菜单面板**：`get_custom_menu/update_custom_menu/指令面板CRUD`
- **富媒体**：`_upload_media`（URL/路径/二进制，超5MB自动分片）、`stream_message`（流式消息）

## WebSocket / Webhook 连接

### WebSocket 流程

1. appId + clientSecret 获取 access_token（提前45s自动刷新，失败重试3次）
2. 通过 `GET /gateway/bot` 动态获取网关地址（配置 `gateway_url` 时直接使用）
3. OP_HELLO → Identify/Resume → READY（获取 session_id 与 bot_id）→ 心跳循环
4. 断线重连：最大50次，指数退避 `min(5 * 2^n, 300)` 秒；OP_RECONNECT 保留会话

### Webhook 模式

账户 `mode = "webhook"` 后通过 ErisPulse router 注册 HTTP 路由：

- Ed25519 验签（种子 = secret 循环填充至32字节），验证 `X-Signature-Ed25519` 对 `X-Signature-Timestamp + body`
- 自动处理 op=13 签名验证握手与 op=0 事件分发
- 依赖 `cryptography` 库（随适配器安装）

## 错误码说明

| retcode | 说明 |
|---------|------|
| 0 | 成功 |
| 10001 | 参数缺失 |
| 10002 | 不支持的动作 |
| 10003 | 无法确定目标/账户 |
| 32000 | 请求超时 |
| 33000 | 网络/API调用异常 |
| 34001 | 请求不存在或已过期（Request DSL） |
| 34100 | 媒体上传失败 |
| 34000+ | 平台业务错误（透传官方 code） |

## 使用示例

### 处理群消息（@检测）

```python
from ErisPulse.Core.Event import message

@message.on_at_message()
async def handle_at(event):
    if event.get("platform") != "qqbot":
        return
    text = event.get_text()
    if text == "签到":
        await event.reply("已签到")
```

### 处理交互事件

```python
from ErisPulse.Core.Event import notice

@notice.on_notice()
async def handle_interaction(event):
    if event.get("platform") != "qqbot":
        return
    if event.get("detail_type") == "qqbot_interaction":
        await qqbot.reply_interaction(event.get("qqbot_interaction_id"), code=0)
        button_id = event.get("qqbot_button_id", "")
        # 处理按钮...
```

### 多账户启动

```toml
[QQBot_Adapter.accounts.bot_a]
appid = "A_APPID"
secret = "..."
enabled = true

[QQBot_Adapter.accounts.bot_b]
appid = "B_APPID"
secret = "..."
mode = "webhook"
enabled = true
```

两个账户并行启动：bot_a 走 WebSocket，bot_b 走 Webhook，互不影响。
