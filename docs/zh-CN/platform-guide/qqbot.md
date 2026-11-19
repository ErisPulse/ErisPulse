# QQBot平台特性文档

QQBotAdapter 是基于QQ官方机器人（QQ OpenAPI）协议构建的适配器，整合群聊、私聊、频道等全场景功能，提供 OneBot12 标准事件、标准Api动作与请求操作接口。

---

## 文档信息

- 对应模块版本: 5.3.3
- 维护者: ErisPulse
- 最后更新: 2026-11-10

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
access_token_url = ""                # 自定义token接口（留空使用官方接口）
webhook_path = "/webhook"            # Webhook回调路径（mode=webhook 时生效）
enabled = true
```

**v5 破坏性变更：**
- `sandbox` 字段已废弃：官方统一使用 `api.bot.qq.com`，旧配置中的 sandbox 会自动迁移并忽略（打印警告）
- 旧版扁平配置（`[QQBot_Adapter]` 下直接写 appid/secret）会自动迁移到 `accounts.default`
- 框架为**软依赖**：安装适配器不会拉动框架版本；运行时检测 `ErisPulse>=2.7.1` 并提示

**intents 说明（支持位序号或事件名）：**

| 位 | 事件名 | 说明 |
|----|--------|------|
| 0 | GUILDS | 频道变更 |
| 1 | GUILD_MEMBERS | 频道成员变更 |
| 9 | GUILD_MESSAGES | 频道消息（私域需审核） |
| 10 | GUILD_MESSAGE_REACTIONS | 频道消息表态 |
| 12 | DIRECT_MESSAGE | 频道私信 |
| 24 | GROUP_MEMBER | 群成员变更（**v5新增**） |
| 25 | GROUP_AND_C2C_EVENT | 群@消息与私聊消息 |
| 26 | INTERACTION | 交互事件（按钮等） |
| 27 | MESSAGE_AUDIT | 消息审核事件 |
| 28 | FORUMS_EVENT | 论坛事件（仅私域） |
| 29 | AUDIO_ACTION | 音频操作 |
| 30 | PUBLIC_GUILD_MESSAGES | 频道消息（公域） |

```toml
# 两种写法等价
intents = "[0, 9, 12, 25, 26, 27]"
intents = '["GUILDS", "GUILD_MESSAGES", "DIRECT_MESSAGE", "GROUP_AND_C2C_EVENT", "INTERACTION", "MESSAGE_AUDIT"]'
```

## 标准化对齐

本节说明适配器与 ErisPulse 标准化规范对齐的行为。规范详情参见 SDK 文档《请求操作规范》（`docs/zh-CN/standards/request-action-spec.md`）与《API 响应规范》（`docs/zh-CN/standards/api-response.md`）。

### 错误码规范化（5.3.x）

- **平台错误统一 34100**：QQ官方 API 返回错误时返回 `retcode=34100`，原始响应（含官方 `code`/`message`）保留在 `qqbot_raw` 字段（媒体上传失败同样使用 34100）
- **超时 33001**：API 调用超时返回 `retcode=33001`（原 32000 不再使用）
- **撤回上下文缺失 10003**：`delete_message` 未找到消息归属上下文时返回 `retcode=10003`（参数错误）
- **请求族保留 34001/34003**：请求不存在或已过期返回 `34001`；请求上下文缺少路由参数返回 `34003`

| retcode | 说明 |
|---------|------|
| 0 | 成功 |
| 10001 | 参数缺失/端点为空 |
| 10002 | 不支持的动作 |
| 10003 | 无法确定发送目标/账户、撤回上下文缺失等参数错误 |
| 33000 | 网络/API调用异常 |
| 33001 | 请求超时 |
| 34001 | 请求不存在或已过期（Request DSL） |
| 34003 | 请求上下文缺少路由参数（Request DSL） |
| 34100 | 平台业务错误（原始响应与官方 code 保留在 `qqbot_raw`） |

### 通知事件命名（5.3.x）

好友增删通知事件统一为标准命名：

| 官方事件 | 转换后 detail_type | 说明 |
|----------|-------------------|------|
| FRIEND_ADD | `friend_increase` | 好友添加（原 `friend_add` 已废弃） |
| FRIEND_DEL | `friend_decrease` | 好友删除（原 `friend_del` 已废弃） |

### 请求上下文留存（5.3.2 起）

入群申请事件入口将 `request_id` 映射到申请上下文（群/申请人 openid）并缓存（TTL 3600 秒、上限 512 条，请求处理成功后清理），执行审批时路由到 `POST /v2/groups/{group_openid}/approval_join_request/{member_openid}`。

### 扩展动作路由（5.3.x）

频道成员权限查询通过带平台前缀的扩展动作提供：

```python
result = await qqbot.Api.call("qqbot.get_channel_member_permissions", channel_id="...", member_id="...")
```

### Stream 发送读 send_context

流式消息（`.Stream()`）读取 `send_context`：事件链内自动使用当前事件来源账户，显式 `Using()` 指定的账户优先。

## 消息发送

### 基础发送

```python
from ErisPulse import sdk
qqbot = sdk.adapter.get("qqbot")

# 发送文本
await qqbot.Send.To("user", user_openid).Text("Hello World!")

# 群聊@消息（自动使用 <qqbot-at-user id="x" /> 格式）
await qqbot.Send.To("group", group_openid).At("member_openid").Text("@你")
await qqbot.Send.To("group", group_openid).AtAll().Text("公告")

# 频道消息（@ 自动使用 <@user_id> 格式）
await qqbot.Send.To("channel", channel_id).Text("频道消息")

# 频道私信（先创建会话）
dms = await qqbot.create_dms(user_id, source_guild_id)
await qqbot.Send.To("dms", dms["data"]["guild_id"]).Text("私信")

# 回复消息（被动回复，自动携带 msg_id）
await qqbot.Send.To("group", group_openid).Reply(msg_id).Text("回复内容")

# 多账户（Using/Account 指定账户名或 bot_id）
await qqbot.Send.Using("account2").To("group", group_openid).Text("来自第二个机器人")
```

### 富媒体

```python
# URL / 本地路径 / 二进制三态支持；超过5MB自动分片上传
await qqbot.Send.To("group", gid).Image("https://example.com/img.png")
await qqbot.Send.To("user", uid).Image("/path/to/local.png")
await qqbot.Send.To("user", uid).Voice(open("audio.mp3", "rb").read())
await qqbot.Send.To("user", uid).Video("https://example.com/v.mp4")
await qqbot.Send.To("user", uid).File(b"...", filename="doc.pdf")

# 频道图片走 multipart 直传（file_image）
await qqbot.Send.To("channel", cid).Image(open("img.png", "rb").read())
```

`file_type` 映射：图片=1、视频=2、语音=3、文件=4（按消息段类型自动判定，`file` 段按扩展名推断）。

### Markdown / Ark / Embed / Keyboard

```python
# 原生 Markdown
await qqbot.Send.To("group", gid).Markdown("# 标题\n- 列表项")

# 模板 Markdown
await qqbot.Send.To("user", uid).Markdown(template_id=1, kv=[{"key": "title", "value": "通知"}])
await qqbot.Send.To("user", uid).Markdown(custom_template_id="23456", kv=[...])

# Ark 模板
await qqbot.Send.To("user", uid).Ark(23, [{"key": "a", "value": "b"}])

# Embed（仅频道/频道私信）
await qqbot.Send.To("channel", cid).Embed({"title": "标题", "content": "内容"})

# 键盘（自动置为 markdown 类型并附带 bot_appid）
keyboard = {"content": {"rows": [[{"label": "确认", "type": 2, "data": "ok"}]]}}
await qqbot.Send.To("group", gid).Keyboard(keyboard).Text("请选择")

# 合并转发（官方 md 无折叠语法，渲染为引用列表；需原生 Markdown 权限，失败自动回退纯文本）
await qqbot.Send.To("group", gid).MergeForward(nodes)
```

### 流式消息（v5 新增，单聊）

```python
# 一次性流式发送（input_state=10 直接完成）
await qqbot.Send.To("user", openid).Stream("回答内容")

# 多轮追加流式
r = await qqbot.stream_message(openid, "第一段", input_state=1, msg_id=被动msg_id)
stream_id = r["data"]["id"]
r = await qqbot.stream_message(openid, "第二段", stream_msg_id=stream_id, index=1, input_state=1)
r = await qqbot.stream_message(openid, "最后一段", stream_msg_id=stream_id, index=2, input_state=10)
```

### 撤回消息

```python
# 标准 Api 动作：自动按消息来源（群/私聊/频道/私信）路由到对应撤回端点
await qqbot.Api.delete_message(message_id)
```

适配器自动登记收发消息的归属目标，无需手工传入 group_id/channel_id；上下文缺失时返回 `retcode=10003`。

## OneBot12 标准Api动作（v5 新增）

```python
# 机器人信息
result = await qqbot.Api.get_self_info()

# 群管理
result = await qqbot.Api.get_group_info(group_openid)          # {group_id, group_name}
result = await qqbot.Api.get_group_member_list(group_openid)   # 自动分页聚合
result = await qqbot.Api.get_group_member_info(group_openid, member_openid)

# 频道
result = await qqbot.Api.get_guild_list()
result = await qqbot.Api.get_guild_info(guild_id)
result = await qqbot.Api.get_guild_member_list(guild_id)
result = await qqbot.Api.get_channel_list(guild_id)
result = await qqbot.Api.get_channel_info(guild_id, channel_id)
await qqbot.Api.set_channel_name(guild_id, channel_id, "新名称")
await qqbot.Api.leave_channel(guild_id, channel_id)            # 删除子频道

# 元动作
result = await qqbot.Api.get_status()   # {"good": bool, "bots": [...]}
result = await qqbot.Api.get_version()  # {"impl": "ErisPulse-QQBotAdapter", "onebot_version": "12"}

# 多账户
result = await qqbot.Api.Using("account2").get_self_info()
```

支持的标准动作：`get_self_info` / `get_group_info` / `get_group_member_info` / `get_group_member_list` / `get_guild_info` / `get_guild_list` / `get_guild_member_info` / `get_guild_member_list` / `get_channel_info` / `get_channel_list` / `set_channel_name` / `leave_channel` / `delete_message` / `get_status` / `get_version` / `get_supported_actions`。不支持的动作返回 `retcode=10002`（如 `get_friend_list`，QQ官方无对应接口）。

## 请求操作（Request DSL，v5 新增）

`GROUP_JOIN_REQUEST`（入群申请）事件转换为一对一交互的 `request` 事件，支持标准化审批：

```python
from ErisPulse.Core.Event import request as request_event

@request_event.on_request()
async def handle_join_request(event):
    if event.get("platform") != "qqbot":
        return
    # 自动审批通过
    result = await event.approve()
    # 或拒绝：await event.reject(comment="不符条件")
    # 或指定账户：await qqbot.Request(event["request_id"]).Using("account2").accept()
```

- `request_id` = 官方 `join_request_id`
- 适配器自动缓存申请上下文（群/申请人 openid），执行时路由到 `POST /v2/groups/{group_openid}/approval_join_request/{member_openid}`
- 拒绝可附 `reject_reason`；上下文过期返回 `retcode=34001`

也可以直接调用平台方法：

```python
await qqbot.approve_group_join(group_openid, member_openid, join_request_id, approve=True)
await qqbot.approve_group_join(group_openid, member_openid, approve=False, reject_reason="理由")
```

## 平台原生API方法族

适配器暴露完整QQ官方API（第一个参数多为目标ID，`account_id` 可选指定账户）：

### 机器人 / 交互
`get_me()`、`reply_interaction(interaction_id, code=0)`

### 频道（Guild）
`get_guilds()`、`get_guild(guild_id)`、`mute_guild_all(guild_id, mute_seconds)`、
`get_guild_roles` / `create_guild_role` / `update_guild_role` / `delete_guild_role`、
`get_guild_api_permission`、`demand_guild_api_permission(guild_id, channel_id, path, method, desc)`

### 子频道（Channel）
`get_channels`、`get_channel`、`create_channel(guild_id, name, type=0, ...)`、`update_channel(channel_id, name=..., ...)`、`delete_channel`、
`get_channel_pins`、`pin_message`、`unpin_message`

### 频道成员
`get_guild_members`、`get_guild_member`、`mute_guild_members`（批量/全频道）、`mute_guild_member`、
`add_guild_member_role` / `remove_guild_member_role`、`kick_guild_member`

### 权限 / 公告 / 表态
`get_channel_role_permissions`、`update_channel_role_permissions`、`get_channel_member_permissions`（扩展动作 `qqbot.get_channel_member_permissions`）、`update_channel_member_permissions`、`create_announce`、
`add_reaction`、`delete_reaction`、`get_reaction_users`

### 日程 / 帖子 / 音频
`get_schedules`、`get_schedule`、`create_schedule`、`update_schedule`、`delete_schedule`、
`get_threads`、`get_thread`、`publish_thread(channel_id, title, content, format=3)`、`delete_thread`、
`control_audio(channel_id, audio_url, text, status)`、`mic_online`、`mic_offline`

### 群管理（v2，**部分接口仅白名单机器人开放**）
```python
await qqbot.get_group_info_raw(group_openid)          # 群信息
await qqbot.get_group_bot_state(group_openid)         # 机器人在群状态
await qqbot.get_group_members(group_openid)           # 成员列表（含 next_cursor）
await qqbot.get_group_member(group_openid, member_openid)
await qqbot.batch_remove_group_members(group_openid, [member_openid], add_to_blacklist=False)
await qqbot.get_group_member_blacklist(group_openid)
await qqbot.update_group_member_blacklist(group_openid, "add", [member_openid])
await qqbot.get_group_join_requests(group_openid)     # 入群申请列表
await qqbot.approve_group_join(...)                   # 审批入群
await qqbot.get_group_restrict_setting(group_openid)  # 禁言设置
await qqbot.set_group_restrict(group_openid, [{"op": "add", "member_openid": "...", "mute_expire_at": 123}])
# 入群审批策略
await qqbot.get_join_approval_strategies()
await qqbot.create_join_approval_strategy(strategy_dict)
await qqbot.update_join_approval_strategy(strategy_id, **fields)
await qqbot.delete_join_approval_strategy(strategy_id)
await qqbot.execute_join_approval_strategy(strategy_id)
await qqbot.update_join_approval_strategy_whitelist(strategy_id, "add", [user_ids])
```

### 自定义菜单 / 指令面板（v5 新增）
```python
# 全局自定义菜单（仅 C2C 生效；子菜单最多5项不可嵌套）
menu_items = [
    {"type": "send_message", "content": {"label": "帮助", "content": "/help"}},
    {"type": "link", "content": {"label": "官网", "content": "https://example.com"}},
]
await qqbot.update_custom_menu(menu_items)
result = await qqbot.get_custom_menu()

# 指令面板（scope: c2c/group/channel/dm；每机器人最多20个）
await qqbot.create_command_panel("c2c", [
    {"type": "command", "content": {"label": "查询天气", "content": "/weather"}},
    {"type": "link", "content": {"label": "更多", "content": "https://example.com"}},
], remark="面板备注", target_type="all")
await qqbot.get_command_panels("c2c")
await qqbot.get_command_panel(panel_id)
await qqbot.update_command_panel(panel_id, items)
await qqbot.delete_command_panel(panel_id)
await qqbot.update_command_panel_targets(panel_id, "add", user_openids=[...])
```

## WebSocket 连接

### 连接流程

1. appId + clientSecret 获取 access_token（`POST https://bots.qq.com/app/getAppAccessToken`）
2. 通过 `GET /gateway/bot` 动态获取网关地址（配置 `gateway_url` 时直接使用）
3. 收到 OP_HELLO（op=10），获取心跳间隔
4. 发送 OP_IDENTIFY（op=2）鉴权（intents 支持位运算组合）
5. 收到 READY，获取 session_id 与 bot_id，发送 connect meta 事件
6. 心跳循环（op=1）与事件分发（op=0）

### 断线重连

- 最大重连 50 次，指数退避 `min(5 * 2^n, 300)` 秒
- 收到 OP_RECONNECT（op=7）保留会话（Resume）；OP_INVALID_SESSION（op=9）重新 Identify
- 收发正常时自动重置重连计数

### Token 管理

- access_token 有效期 7200 秒，**提前 45 秒自动刷新**（请求时惰性检查）
- 刷新失败自动重试 3 次（递增延迟）
- 请求头：`Authorization: QQBot {token}` + **`X-Union-Appid: {appid}`**（v5 新增）

## Webhook 接入（v5 新增）

将账户 `mode` 设为 `webhook` 即可改用 HTTP 回调接收事件：

```toml
[QQBot_Adapter.accounts.mybot]
appid = "..."
secret = "..."
mode = "webhook"
webhook_path = "/webhook"    # 多 webhook 账户自动追加账户名避免冲突
```

- 适配器通过 ErisPulse router 注册 HTTP 路由，启动日志会输出完整回调 URL
- **Ed25519 验签**：种子 = secret 循环填充至 32 字节；验证 `X-Signature-Ed25519` 对 `X-Signature-Timestamp + body` 的签名
- 自动处理 op=13 签名验证握手（回调地址配置校验）与 op=0 事件分发
- 依赖 `cryptography` 库（已随适配器安装）

## 事件订阅与 openid 体系

1. QQBot 使用 openid 体系而非QQ号，用户/群标识均为 openid 字符串
2. 群消息默认仅在用户@机器人时收到（`GROUP_AT_MESSAGE_CREATE`）
3. **接收全部群消息**：需在 [QQ开放平台](https://q.qq.com/) 机器人管理后台开启相应权限（无API可设置）；开通后非@群消息以 `GROUP_MESSAGE_CREATE` 推送，适配器已完整支持转换（标记 `qqbot_is_at_message=false`；若消息中含@机器人标记则自动识别为@消息）
4. **@检测**：QQ 的"被@"由事件名承载，且群消息 @ 标记为 `<@{群空间openid}>`（与 READY bot_id 不同 id 体系）。适配器自动解析两种标记风格并注入/归一化机器人 mention 段，保证 `on_at_message()`/`is_at_message()` 可用；同时自动学习机器人在各群的 openid，使"接收全部群消息"模式下的 `GROUP_MESSAGE_CREATE` 中@消息也能被识别（原始 openid 保留在 mention 段 `data.qqbot_openid`）
5. 被动回复：群/私聊消息需携带 `msg_id` 或 `event_id`，适配器自动缓存并附加
6. `event_id` 不能与富媒体混发（官方限制），适配器自动降级处理
7. 发送可能触发审核，结果通过 `qqbot_audit_pass` / `qqbot_audit_reject` 事件通知
8. 程序退出调用 `shutdown()` 释放资源

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

### 处理按钮交互

```python
from ErisPulse.Core.Event import notice

@notice.on_notice()
async def handle_interaction(event):
    if event.get("detail_type") != "qqbot_interaction":
        return
    button_id = event.get("qqbot_button_id")
    await qqbot.reply_interaction(event.get("qqbot_interaction_id"), code=0)
    if button_id == "confirm":
        await qqbot.Send.To("group", event.get("group_id")).Text("已确认")
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
